"""Block A — Compactor + auto-compact circuit breaker + Runnable cache_edits.

v5 port of v4's `Compactor` class (compact_v4/MAIN/agent/sagemaker_agent.py
lines 186-635, ~449 LOC). Adapted for v5's nested-package layout. Plus:
  - Auto-compact circuit breaker (Hermes-style cooldown)
  - Runnable cache_edits adaptation (cache_control on prompt sections —
    Bedrock equivalent of the Anthropic-direct cache_edits param)
  - B-2 countTokensViaHaikuFallback (deferred from Block B per ADR-021)
  - B+5 recursive advisor sub-cost accounting (deferred from Block B+
    per ADR-022 — auxiliary compaction-summary model)

The Compactor is the load-bearing piece for context-window management.
At 80% of max context, `should_compact()` returns True; the chat loop
calls `Compactor.run(messages, client)` which prunes oversized tool
results, asks Bedrock for an LLM summary, and replaces old messages
with the summary + last N messages.

PORT_LOG: see #066-#070.
"""
from __future__ import annotations

import copy
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# ============================================================
# CompactionResult
# ============================================================

@dataclass
class CompactionResult:
    """Outcome of a compact() call."""

    success: bool
    summary: str = ""
    messages_after: List[Dict[str, Any]] = field(default_factory=list)
    tokens_before: int = 0
    tokens_after: int = 0
    error: str = ""


# ============================================================
# AutoCompactCircuitBreaker (Hermes-style cooldown)
# ============================================================

class AutoCompactCircuitBreaker:
    """Prevents auto-compact runaway by enforcing a cooldown window.

    Pattern: when auto-compact fires, mark the timestamp. If
    `should_attempt()` is called again within `cooldown_seconds`, return
    False — caller must continue without re-compacting. Hermes
    run_agent.py uses this to prevent compact-after-compact loops where
    a freshly-compacted context still trips the 80% trigger because
    the summary itself is large.

    Per Wave-5-DEEP H5 (auto-compact circuit breaker; A28 cache-invariant).
    """

    def __init__(self, cooldown_seconds: int = 30, max_per_session: int = 10):
        # cooldown_seconds=0 is a valid setting (test scenarios + caller
        # who only wants the session cap as a gate). We clamp at >= 0.
        self.cooldown_seconds = max(0, int(cooldown_seconds))
        self.max_per_session = max(1, int(max_per_session))
        self._lock = threading.Lock()
        self._last_attempt: float = 0.0
        self._session_count = 0

    def should_attempt(self) -> Tuple[bool, str]:
        """True iff a compact attempt is allowed right now.

        Returns (allowed, reason). When False, the reason explains why
        (session cap hit / cooldown active) so the caller can surface
        a clear log message. Session cap checked FIRST — once exhausted,
        no further attempts make sense regardless of cooldown.
        """
        with self._lock:
            if self._session_count >= self.max_per_session:
                return False, (
                    f"auto-compact session cap reached "
                    f"({self._session_count}/{self.max_per_session})"
                )
            now = time.time()
            since = now - self._last_attempt
            if self._last_attempt > 0 and since < self.cooldown_seconds:
                return False, (
                    f"auto-compact cooldown active "
                    f"({since:.0f}s elapsed, "
                    f"{self.cooldown_seconds}s required)"
                )
            return True, ""

    def record_attempt(self) -> None:
        """Mark a compact attempt — caller calls this after a successful
        OR failed compact so cooldown applies either way (a failed
        compact still consumed time + tokens)."""
        with self._lock:
            self._last_attempt = time.time()
            self._session_count += 1

    def reset(self) -> None:
        with self._lock:
            self._last_attempt = 0.0
            self._session_count = 0

    def try_attempt(self) -> Tuple[bool, str]:
        """Atomic check+record: if allowed, record the attempt and
        return (True, ""). If not allowed, return (False, reason)
        without recording. Concurrent callers cannot both pass the
        check before either records — this closes the TOCTOU window
        in should_attempt() + record_attempt() that Codex iter-1
        finding #3 (MEDIUM) flagged.
        """
        with self._lock:
            if self._session_count >= self.max_per_session:
                return False, (
                    f"auto-compact session cap reached "
                    f"({self._session_count}/{self.max_per_session})"
                )
            now = time.time()
            since = now - self._last_attempt
            if self._last_attempt > 0 and since < self.cooldown_seconds:
                return False, (
                    f"auto-compact cooldown active "
                    f"({since:.0f}s elapsed, "
                    f"{self.cooldown_seconds}s required)"
                )
            # Atomic record.
            self._last_attempt = now
            self._session_count += 1
            return True, ""


# ============================================================
# Compactor (v4 port)
# ============================================================

class Compactor:
    """Smart context compaction: prune oversized tool results, then
    LLM-summarize old messages, replace with summary + last N.

    Verbatim port of v4 sagemaker_agent.py:186-635 with adaptations:
    - estimate_tokens delegates to runtime/tokens.estimate_message_tokens
      (drops tiktoken dependency for SageMaker-native deployment).
    - create_llm_summary uses v5 BedrockClient.chat() shape.
    - Auxiliary-model routing (v4.9.4 compaction_model) preserved with
      per-agent attribution via TokenTracker.add(agent_kind="advisor")
      — this is the B+5 recursive advisor sub-cost accounting that
      ADR-022 deferred from Block B+ to Block A.
    """

    PRUNE_PROTECT_TOKENS = 40_000
    PRUNE_MIN_SAVINGS = 10_000
    SUMMARY_TRIGGER_PERCENT = 0.80
    KEEP_LAST_MESSAGES = 3
    MAX_PTL_RETRIES = 3

    SUMMARY_TOOL_RESULT_THRESHOLD = 8_000
    SUMMARY_TOOL_RESULT_HEAD = 2_000
    SUMMARY_TOOL_RESULT_TAIL = 1_000

    PROTECTED_TOOLS = {"todo_write", "todo_read", "semantic_search"}

    FIXED_OVERHEAD_TOKENS = 6_000

    # Aux client cache (per-process); built lazily.
    _aux_client_cache: Dict[str, Any] = {}

    # --------------------------------------------------------
    # Token estimation
    # --------------------------------------------------------

    @classmethod
    def estimate_tokens(cls, text_or_messages: Any) -> int:
        """Estimate token count for a string OR list of messages.

        Delegates to `runtime.tokens.estimate_message_tokens` for strings
        and `rough_token_count_for_message` for message dicts.
        """
        from runtime.tokens import (
            estimate_message_tokens,
            rough_token_count_for_message,
        )
        if isinstance(text_or_messages, str):
            return estimate_message_tokens(text_or_messages)
        if isinstance(text_or_messages, list):
            return sum(rough_token_count_for_message(m) for m in text_or_messages)
        if isinstance(text_or_messages, dict):
            return rough_token_count_for_message(text_or_messages)
        return 0

    # --------------------------------------------------------
    # Prune oversized tool results
    # --------------------------------------------------------

    @classmethod
    def prune_tool_outputs(
        cls,
        messages: List[Dict[str, Any]],
        max_context: int,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Truncate tool results that are far past PRUNE_PROTECT_TOKENS.

        Keeps the head + tail of each oversized result so the model
        retains some signal but the bulk is removed. Returns
        (pruned_messages, tokens_saved).
        """
        if not messages:
            return messages, 0

        pruned = copy.deepcopy(messages)
        tool_name_map: Dict[str, str] = {}
        # Build tool_use_id → tool_name map so we can skip protected tools.
        for msg in pruned:
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        tool_name_map[item.get("id", "")] = item.get("name", "")

        # Walk most-recent → oldest; protect the last PROTECT_TOKENS worth.
        running_tokens = 0
        tokens_saved = 0
        for msg in reversed(pruned):
            content = msg.get("content")
            if not isinstance(content, list):
                running_tokens += cls.estimate_tokens(msg)
                continue
            for block in content:
                if not (isinstance(block, dict) and block.get("type") == "tool_result"):
                    continue
                tool_name = tool_name_map.get(block.get("tool_use_id", ""), "")
                if tool_name in cls.PROTECTED_TOOLS:
                    continue
                inner = block.get("content")
                if isinstance(inner, str):
                    block_tokens = cls.estimate_tokens(inner)
                    running_tokens += block_tokens
                    if running_tokens > cls.PRUNE_PROTECT_TOKENS \
                       and len(inner) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
                        head = inner[: cls.SUMMARY_TOOL_RESULT_HEAD]
                        tail = inner[-cls.SUMMARY_TOOL_RESULT_TAIL :]
                        new_text = (
                            f"{head}\n... [pruned "
                            f"{len(inner) - len(head) - len(tail):,} chars] ...\n{tail}"
                        )
                        block["content"] = new_text
                        tokens_saved += cls.estimate_tokens(inner) - cls.estimate_tokens(new_text)
                elif isinstance(inner, list):
                    for sub in inner:
                        if isinstance(sub, dict) and sub.get("type") == "text":
                            txt = sub.get("text", "")
                            running_tokens += cls.estimate_tokens(txt)
                            if running_tokens > cls.PRUNE_PROTECT_TOKENS \
                               and len(txt) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
                                head = txt[: cls.SUMMARY_TOOL_RESULT_HEAD]
                                tail = txt[-cls.SUMMARY_TOOL_RESULT_TAIL :]
                                new_text = (
                                    f"{head}\n... [pruned "
                                    f"{len(txt) - len(head) - len(tail):,} chars] ...\n{tail}"
                                )
                                sub["text"] = new_text
                                tokens_saved += cls.estimate_tokens(txt) - cls.estimate_tokens(new_text)
        # Codex Block-A iter-1 finding #2 (MEDIUM) lock: v4 invariant —
        # if savings are too small, return ORIGINAL messages (don't
        # accept the fidelity loss for marginal token wins). Per v4
        # PRUNE_MIN_SAVINGS = 10,000 tokens (constant kept above).
        if tokens_saved < cls.PRUNE_MIN_SAVINGS:
            return messages, 0
        return pruned, tokens_saved

    # --------------------------------------------------------
    # Should compact?
    # --------------------------------------------------------

    @classmethod
    def should_compact(cls, messages: List[Dict[str, Any]], max_tokens: int) -> bool:
        """True iff token estimate > 80% of max_tokens (with overhead)."""
        try:
            from runtime.tokens import TOKENS
            overhead = TOKENS.final_context_tokens_from_last_response()
            if overhead == 0:
                overhead = cls.FIXED_OVERHEAD_TOKENS
        except Exception:
            overhead = cls.FIXED_OVERHEAD_TOKENS
        total = cls.estimate_tokens(messages) + overhead
        return total > max_tokens * cls.SUMMARY_TRIGGER_PERCENT

    # --------------------------------------------------------
    # Auxiliary-model routing (B+5 — recursive advisor sub-cost)
    # --------------------------------------------------------

    @classmethod
    def _summary_client(cls, main_client) -> Any:
        """Return the client to use for summary generation.

        Per v4.9.4: when CONFIG.compaction_model is set, build a
        Bedrock client for that cheaper auxiliary model so summaries
        don't pay main-model rates. Per ADR-022 / B+5: TOKENS.add()
        with `agent_kind="advisor"` so the auxiliary cost is attributed
        separately in /cost output.
        """
        from runtime.config import CONFIG
        aux_model = (getattr(CONFIG, "compaction_model", "") or "").strip()
        if not aux_model or aux_model == getattr(main_client, "model_id", ""):
            return main_client
        cached = cls._aux_client_cache.get(aux_model)
        if cached is not None:
            return cached
        try:
            from runtime.bedrock_client import BedrockClient
            aux = BedrockClient(
                aux_model,
                getattr(main_client, "region", "ap-southeast-2"),
                getattr(main_client, "mock_mode", False),
            )
            cls._aux_client_cache[aux_model] = aux
            logging.info(f"[COMPACT] Using auxiliary compaction model: {aux_model}")
            return aux
        except Exception as exc:  # noqa: BLE001
            logging.warning(
                f"[COMPACT] Auxiliary model '{aux_model}' init failed; "
                f"using main client: {exc}"
            )
            return main_client

    # --------------------------------------------------------
    # LLM summary
    # --------------------------------------------------------

    @classmethod
    def create_llm_summary(
        cls,
        client: Any,
        messages: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Ask Bedrock to summarize the conversation. Returns None on
        failure. Per v4 verbatim with v5 adaptations:
        - Pre-prune oversized tool results for the summary input.
        - Optionally route through CONFIG.compaction_model (advisor).
        - Attribute advisor tokens via TOKENS.add(agent_kind='advisor').
        """
        from runtime.tokens import TOKENS

        pruned_messages = cls._prune_tool_results_for_summary(messages)
        summary_client = cls._summary_client(client)

        SUMMARY_SYSTEM_PROMPT = (
            "You are summarizing a coding conversation. You have ZERO tools "
            "available — do NOT attempt any tool calls. Be concise but "
            "preserve:\n"
            "1. Current task and goal\n"
            "2. Key files modified or read\n"
            "3. Important decisions made\n"
            "4. Where we left off\n"
            "5. What needs to happen next\n"
            "6. Resolved questions\n"
            "7. Pending questions"
        )

        summary_input = list(pruned_messages)
        # Bedrock requires user/assistant alternation.
        if summary_input and summary_input[-1].get("role") == "user":
            summary_input.append({
                "role": "assistant",
                "content": "[Preparing summary...]",
            })
        summary_input.append({
            "role": "user",
            "content": (
                "Summarize the conversation above per the rubric. Be concise."
            ),
        })

        attempts = 0
        while attempts <= cls.MAX_PTL_RETRIES:
            try:
                response = summary_client.chat(
                    messages=summary_input,
                    system=SUMMARY_SYSTEM_PROMPT,
                    tools=None,
                    max_tokens=2000,
                    temperature=0.0,
                )
                if response and response.usage:
                    # B+5 (ADR-022 remap): attribute advisor cost separately.
                    agent_kind = (
                        "advisor"
                        if summary_client is not client
                        else "parent"
                    )
                    TOKENS.add(
                        response.usage,
                        model_id=getattr(summary_client, "model_id", None),
                        agent_kind=agent_kind,
                    )
                if response and response.text:
                    return response.text
                return None
            except Exception as exc:  # noqa: BLE001
                err = str(exc).lower()
                is_ptl = ("prompt" in err and "long" in err) \
                    or "too many tokens" in err
                if not is_ptl:
                    logging.warning(f"[COMPACT] LLM summary failed: {exc}")
                    return None
                attempts += 1
                summary_input = cls._truncate_head_for_ptl_retry(summary_input)
                if not summary_input:
                    logging.warning("[COMPACT] PTL retries exhausted")
                    return None
        return None

    @classmethod
    def _prune_tool_results_for_summary(
        cls,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Cheap pre-LLM pass: drop oversized tool_result bodies."""
        out: List[Dict[str, Any]] = []
        for msg in messages:
            content = msg.get("content")
            if not isinstance(content, list):
                out.append(msg)
                continue
            new_blocks: List[Any] = []
            mutated = False
            for block in content:
                if not (isinstance(block, dict) and block.get("type") == "tool_result"):
                    new_blocks.append(block)
                    continue
                inner = block.get("content")
                if isinstance(inner, str) and len(inner) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
                    head = inner[: cls.SUMMARY_TOOL_RESULT_HEAD]
                    tail = inner[-cls.SUMMARY_TOOL_RESULT_TAIL :]
                    new_block = dict(block)
                    new_block["content"] = (
                        f"{head}\n... [pruned for summary] ...\n{tail}"
                    )
                    new_blocks.append(new_block)
                    mutated = True
                else:
                    new_blocks.append(block)
            if mutated:
                new_msg = dict(msg)
                new_msg["content"] = new_blocks
                out.append(new_msg)
            else:
                out.append(msg)
        return out

    @classmethod
    def _truncate_head_for_ptl_retry(
        cls,
        messages: List[Dict[str, Any]],
    ) -> Optional[List[Dict[str, Any]]]:
        """Drop the first 25% of messages so PTL retry has a smaller
        input. Returns None when input is already minimal.

        Codex Block-A iter-1 finding #1 (HIGH) lock: Bedrock requires
        message lists to start with role=user. If the head-slice
        produces a list starting with role=assistant, prepend a
        user-marker so the retry doesn't fail Bedrock validation
        (which would early-abort the PTL recovery loop).
        Per v4_compactor_section.txt:189.
        """
        if len(messages) < 4:
            return None
        drop_n = max(1, len(messages) // 4)
        truncated = messages[drop_n:]
        if not truncated:
            return None
        # Guarantee user-first ordering for Bedrock.
        if truncated[0].get("role") != "user":
            truncated = [{
                "role": "user",
                "content": "[continuing from earlier in the conversation]",
            }] + truncated
        return truncated

    # --------------------------------------------------------
    # Compact: replace old messages with summary
    # --------------------------------------------------------

    @classmethod
    def compact(
        cls,
        messages: List[Dict[str, Any]],
        summary: str,
    ) -> List[Dict[str, Any]]:
        """Replace old messages with a summary + last N messages."""
        if not summary:
            return messages
        keep_last = cls.KEEP_LAST_MESSAGES
        recent = messages[-keep_last:] if len(messages) > keep_last else []
        summary_msg = {
            "role": "user",
            "content": (
                f"[CONVERSATION SUMMARY]\n{summary}\n"
                "[END SUMMARY — Continuing from here]"
            ),
        }
        return [summary_msg] + recent

    @classmethod
    def run(
        cls,
        client: Any,
        messages: List[Dict[str, Any]],
        max_tokens: int = 200_000,
    ) -> CompactionResult:
        """End-to-end: prune → summarize → compact. Single entry point."""
        before_tokens = cls.estimate_tokens(messages)
        if not cls.should_compact(messages, max_tokens):
            return CompactionResult(
                success=False,
                error="compact not needed (under 80% trigger)",
                tokens_before=before_tokens,
                tokens_after=before_tokens,
                messages_after=list(messages),
            )
        pruned, _saved = cls.prune_tool_outputs(messages, max_tokens)
        summary = cls.create_llm_summary(client, pruned)
        if not summary:
            return CompactionResult(
                success=False,
                error="LLM summary returned empty",
                tokens_before=before_tokens,
                tokens_after=cls.estimate_tokens(pruned),
                messages_after=pruned,
            )
        new_messages = cls.compact(pruned, summary)
        after_tokens = cls.estimate_tokens(new_messages)
        return CompactionResult(
            success=True,
            summary=summary,
            messages_after=new_messages,
            tokens_before=before_tokens,
            tokens_after=after_tokens,
        )


# ============================================================
# Runnable cache_edits — Bedrock cache_control adaptation
# ============================================================

def apply_cache_control_to_blocks(
    blocks: List[Dict[str, Any]],
    cache_break_at: int = -1,
) -> List[Dict[str, Any]]:
    """Apply Bedrock-style `cache_control` to message blocks.

    Bedrock equivalent of Anthropic-direct `cache_edits` (Runnable's
    name): mark the block at `cache_break_at` (default -1 = last) with
    `{"cache_control": {"type": "ephemeral"}}` so prefix-replay works
    on subsequent turns. Block A's compaction output is the natural
    place to set this — the summary block becomes the new cache prefix.

    Per Runnable cache_edits.ts (reference) + Hermes A28 cache-invariant
    (no mid-turn cache flips).
    """
    if not blocks:
        return blocks
    if cache_break_at == -1:
        cache_break_at = len(blocks) - 1
    if cache_break_at < 0 or cache_break_at >= len(blocks):
        return blocks
    out = list(blocks)
    target = dict(out[cache_break_at])
    target["cache_control"] = {"type": "ephemeral"}
    out[cache_break_at] = target
    return out


# ============================================================
# B-2 — countTokensViaHaikuFallback (deferred from Block B per ADR-021)
# ============================================================

def count_tokens_via_haiku_fallback(
    messages: List[Dict[str, Any]],
    main_client: Any,
) -> Optional[int]:
    """Fallback token counter when BedrockClient.count_tokens is
    unavailable: use Haiku (cheaper) to count tokens via a
    1-token-budget chat call. Returns the input_tokens reported.

    Per Runnable services/tokenEstimation.ts:251-325 (R4 #42).
    Block A consumer: uses this when Compactor needs an accurate
    count and the live client doesn't expose count_tokens (older boto3).
    """
    if main_client is None:
        return None
    if getattr(main_client, "mock_mode", False):
        # In mock mode, use the rough estimator from runtime/tokens.
        from runtime.tokens import rough_token_count_for_message
        return sum(rough_token_count_for_message(m) for m in messages)
    try:
        from runtime.bedrock_client import BedrockClient
        haiku_client = BedrockClient(
            "anthropic.claude-haiku-4-5-20251001-v1:0",
            getattr(main_client, "region", "ap-southeast-2"),
            mock_mode=False,
        )
        # Send a max_tokens=1 call so we get the input usage cheaply.
        response = haiku_client.chat(
            messages=messages,
            system="Token-count fallback. Reply with a single dot.",
            tools=None,
            max_tokens=1,
            temperature=0.0,
        )
        if response and response.usage:
            return int(response.usage.get("input_tokens", 0))
    except Exception as exc:  # noqa: BLE001
        logging.warning(f"haiku-fallback token count failed: {exc}")
    return None


# ============================================================
# Module-level singleton circuit breaker
# ============================================================

AUTO_COMPACT = AutoCompactCircuitBreaker()


__all__ = [
    "Compactor",
    "CompactionResult",
    "AutoCompactCircuitBreaker",
    "AUTO_COMPACT",
    "apply_cache_control_to_blocks",
    "count_tokens_via_haiku_fallback",
]
