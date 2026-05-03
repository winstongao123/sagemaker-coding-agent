Reading additional input from stdin...
OpenAI Codex v0.128.0 (research preview)
--------
workdir: D:\Github\sagemaker-coding-agent
model: gpt-5.5
provider: openai
approval: never
sandbox: read-only
reasoning effort: high
reasoning summaries: none
session id: 019df02e-6fc5-7b53-8d99-f04efdfd9983
--------
user
# Codex CLI version: codex-cli 0.128.0
# Model used: gpt-5.5
# Reasoning effort: high
# Date: 2026-05-04

R2 PHASE A iter-3 — fixes for iter-2 REJECT (3 remaining issues).

iter-2 REJECT findings — closure status:

1. **Fix 3 partial — compact-occurred too weak (api_calls heuristic
   alone)**: FIXED. Replaced with STRONG signal:
   `compact_proven = compact_log_seen OR summary_marker_seen` where
   `summary_marker_seen` walks `agent.messages` looking for
   `"[CONVERSATION SUMMARY]"`, `"[Conversation Summary]"`,
   `"## Summary of prior conversation"`, or `"summary of the prior"` in
   any role's content (str or list-of-blocks).
   Plus: T2 input MUST drop materially vs T1 (`t2_input_estimate <
   tokens_in_t1 * 0.5`) — proves the buffer was actually compacted, not
   just that `api_calls` increased.

2. **Fix 4 partial — T2 recall accepted "5"**: FIXED. Removed "5" from
   accepted recall tokens. Now requires "2 + 3" / "2+3" / "what is 2"
   in t2_text. A weak summary that dropped the question CANNOT pass.

3. **Compaction success now mandatory**: FIXED. Two assertions now
   both must hold:
   - `assert compact_proven, ...` (strong signal)
   - `assert t2_dropped_materially, ...` (input shrank)

Updated assertions block (verbatim):
```python
# T1: tight regex for "5"/"five".
assert re.match(r"^\s*=?\s*(5|five)\b\.?\s*$", t1_text, re.IGNORECASE), ...

# T2: must mention the SPECIFIC prior question (2+3) — no "5" fallback.
assert ("2 + 3" in t2_text or "2+3" in t2_text or "what is 2" in t2_text), ...

# Compaction PROVEN, not heuristic.
assert compact_proven, ...
assert t2_dropped_materially, ...

assert tokens_in_t1 > 50_000, ...   # large preamble was sent
assert cost_used <= 0.50, ...
```

Cost recompute (iter-2 caveat noted):
- Turn 1: 78K input × $1.10/MTok + 64 output × $5.50/MTok ≈ $0.086
- Auto-compact summary: ~78K input × $1.10/MTok + summary output × $5.50
  ≈ $0.086 + $0.005 = $0.091 (worst case with no caching of user msg)
- Turn 2: small input (~5K post-compact summary) + small output ≈ $0.006
- TOTAL ≈ $0.18-$0.20 worst case. Still WELL under $0.50 cap.

PRODUCE THREE INDEPENDENT VERDICTS.

=== AXIS A — Test design soundness ===
- Are the 3 iter-2 issues now closed?
  - compact_proven uses STRONG signals only (log line or messages
    marker)?
  - t2_dropped_materially asserts T2 input < 50% of T1 input?
  - T2 recall no longer accepts "5"?
- Are there edge cases the new assertions could still miss?
  - Could a v5 implementation produce a successful compact without
    writing `[CONVERSATION SUMMARY]` to messages? (Cite the actual
    summary block format in compactor.py.)
  - Could `t2_input_estimate = tokens_in - tokens_in_t1` be wrong if
    auto-compact summary call also adds to TOKENS.session_input? (Then
    "T2 estimate" includes the summary call's input too.)

=== AXIS B — Cost-control soundness ===
- Recompute total worst case: ~$0.18-$0.20 incl summary call. Headroom
  for $0.50 cap is 2.5×. Acceptable.
- on_stop_check still bounded loop boundaries.

=== AXIS C — Coverage of v5 EMPIRICAL evidence ===
- After iter-3 fixes, R2 provides MANDATORY proof of:
  - Compactor.run produced [CONVERSATION SUMMARY] (or didn't, and test
    fails loud)
  - Buffer materially shrunk between T1 and T2
  - Post-compact recall preserved the original question
- Strong empirical evidence for Block A end-to-end.

=== FINAL ===
PRE-FLIGHT VERDICT: APPROVE_FOR_AWS_CALL | REJECT (do not run AWS)

Goal: APPROVE so we can run R2 AWS call #1.

Files:
- compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py (~280 LOC)
- compact_v5/MAIN/agent/core/compactor.py (Compactor.run + summary
  block format)
- compact_v5/_status/codex_reviews/r-tier-R2-phaseA-iter2.md (prior
  REJECT findings)
codex
I’ll inspect the R2 test, the compactor summary format, and the prior iter-2 review so the verdict is grounded in the actual code rather than the change summary.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/_status/codex_reviews/r-tier-R2-phaseA-iter2.md' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/core/compactor.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py' in D:\Github\sagemaker-coding-agent
 succeeded in 2034ms:
"""Block A ƒ?" Compactor + auto-compact circuit breaker + Runnable cache_edits.

v5 port of v4's `Compactor` class (compact_v4/MAIN/agent/sagemaker_agent.py
lines 186-635, ~449 LOC). Adapted for v5's nested-package layout. Plus:
  - Auto-compact circuit breaker (Hermes-style cooldown)
  - Runnable cache_edits adaptation (cache_control on prompt sections ƒ?"
    Bedrock equivalent of the Anthropic-direct cache_edits param)
  - B-2 countTokensViaHaikuFallback (deferred from Block B per ADR-021)
  - B+5 recursive advisor sub-cost accounting (deferred from Block B+
    per ADR-022 ƒ?" auxiliary compaction-summary model)

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
    False ƒ?" caller must continue without re-compacting. Hermes
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
        a clear log message. Session cap checked FIRST ƒ?" once exhausted,
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
        """Mark a compact attempt ƒ?" caller calls this after a successful
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
        check before either records ƒ?" this closes the TOCTOU window
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
      ƒ?" this is the B+5 recursive advisor sub-cost accounting that
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
        # Build tool_use_id ƒ+' tool_name map so we can skip protected tools.
        for msg in pruned:
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        tool_name_map[item.get("id", "")] = item.get("name", "")

        # Walk most-recent ƒ+' oldest; protect the last PROTECT_TOKENS worth.
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
        # Codex Block-A iter-1 finding #2 (MEDIUM) lock: v4 invariant ƒ?"
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
    # Auxiliary-model routing (B+5 ƒ?" recursive advisor sub-cost)
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
            "available ƒ?" do NOT attempt any tool calls. Be concise but "
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
                "[END SUMMARY ƒ?" Continuing from here]"
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
        """End-to-end: prune ƒ+' summarize ƒ+' compact. Single entry point."""
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
# Runnable cache_edits ƒ?" Bedrock cache_control adaptation
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
    place to set this ƒ?" the summary block becomes the new cache prefix.

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
# B-2 ƒ?" countTokensViaHaikuFallback (deferred from Block B per ADR-021)
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
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 2885ms:
"""R-tier R2 ƒ?" large preamble crosses Compactor threshold, follow-up
turn succeeds against the COMPACTED buffer.

Per PS_V5_TEST_PLAYBOOK / PS_V5_TEST_SET ATier 1 R2:
  Validates Block A (Compactor + auto-compact + cache invariants) on
  real Bedrock end-to-end:
    - Turn 1: large preamble + simple question ƒ+' assistant answer.
      Crosses Compactor.should_compact threshold (80% of
      context_max_tokens).
    - Auto-compact fires after the response ƒ?" summarises history into
      one [CONVERSATION SUMMARY] system block, freeing tokens.
    - Turn 2: follow-up question. Bedrock must accept the post-compact
      message buffer (no 400 from cut-mid-pair) and answer correctly
      using only the compact summary.

Codex R2 PHASE A iter-1 fixes applied (REJECT ƒ+' re-pre-flight):
  1. Default CONFIG.context_max_tokens=200_000 means real trigger is
     ~160K. We monkey-patch CONFIG.context_max_tokens=100_000 for this
     test so the existing 78K preamble crosses the 80% gate (80K).
     Cheaper than pushing to 165K real tokens AND tests same code path.
  2. Tightened final answer regex (single-token "5" or "five" reply
     expected from max_tokens=64; pattern in code below).
  3. Compaction-occurred assertion: TOKENS.api_calls accounts for
     initial turn + compaction summary call + follow-up turn ƒ% 3 if
     compact fired; OR captured "[auto-compact]" line in stdout.
  4. Follow-up turn against the compacted buffer (asks recall question
     answerable from system summary).
  5. AUTO_COMPACT.reset() + TOKENS.reset() in finally for hermetic test.

Cost cap: $0.50. Model: Haiku 4.5 AU.
Real-AWS gated: skipped without RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_R2_COST_CAP_USD = 0.50

# 2700 lines of lorem ƒ%^ 60K words ƒ%^ 78K tokens. With CONFIG.context_max_tokens
# = 100_000 (test override), this crosses the 80%-of-100K = 80K threshold.
_LOREM_LINE = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
    "eiusmod tempor incididunt ut labore et dolore magna aliqua. "
)
_LOREM_LINES = 2700

_R2_PROMPT_T1 = """You are reviewing a long conversation history. Below is a recap of
prior context ƒ?" most of it is filler. After the recap, please answer
ONE SHORT question.

=== RECAP (do not summarize back; just keep in mind) ===
{recap}
=== END RECAP ===

QUESTION: What is 2 + 3? Answer with a single number, no explanation.
"""

# Follow-up ƒ?" forces a 2nd Bedrock call against the post-compact buffer.
_R2_PROMPT_T2 = (
    "What was the previous question I asked? Reply with the question only "
    "(one short sentence)."
)


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R2 is real-AWS gated.",
)
def test_r2_compaction_under_load(tmp_path, monkeypatch):
    """R-tier R2 ƒ?" large preamble + follow-up succeed across compaction.

    PASS criteria:
      - Turn 1 produces a tight "5"/"Five" answer.
      - Turn 2 is answered against the compacted buffer (recalls the
        previous question or a paraphrase).
      - Auto-compact fired (TOKENS.api_calls >= 2 ƒ?" model+compact-summary
        on turn 1 alone ƒ?" OR "[auto-compact]" appears in captured stdout).
      - cost ƒ% $0.50.
    """
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    from core.compactor import AUTO_COMPACT
    import security.manager as sec_mgr
    from agent import Agent

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    saved_ctx_max = getattr(CONFIG, "context_max_tokens", None)
    cwd_before = os.getcwd()

    # Codex iter-1 fix #5: clean state in finally + at start.
    AUTO_COMPACT.reset() if hasattr(AUTO_COMPACT, "reset") else None

    captured_stdout: list = []

    def _stdout_capture(text: str) -> None:
        captured_stdout.append(text)
        # Also forward to print so pytest -s shows it.
        try:
            print(text)
        except Exception:
            pass

    try:
        CONFIG.workspace = str(tmp_path)
        CONFIG.session_cost_limit = _R2_COST_CAP_USD
        CONFIG.model_id = _HAIKU_45_AU
        CONFIG.max_tokens = 64
        CONFIG.require_tool_approval = False
        # Codex iter-1 fix #1: lower threshold so 78K crosses the 80% gate.
        CONFIG.context_max_tokens = 100_000
        sec_mgr.rebuild_singleton_for_tests()
        os.chdir(str(tmp_path))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt():
            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= _R2_COST_CAP_USD
            )

        agent = Agent(
            client=client,
            max_turns=4,
            on_stop_check=_hard_cost_halt,
        )

        recap = (_LOREM_LINE + "\n") * _LOREM_LINES
        prompt_t1 = _R2_PROMPT_T1.format(recap=recap)
        approx_tokens_in = len(prompt_t1) // 4

        t0 = time.time()
        # Turn 1 ƒ?" large preamble.
        result_t1 = agent.run(prompt_t1, tools=[], output_fn=_stdout_capture)
        wall_t1 = time.time() - t0
        tokens_in_t1 = TOKENS.session_input
        api_calls_after_t1 = TOKENS.api_calls
        # Turn 2 ƒ?" follow-up against (likely-compacted) buffer.
        t1 = time.time()
        result_t2 = agent.run(_R2_PROMPT_T2, tools=[], output_fn=_stdout_capture)
        wall_t2 = time.time() - t1
        cost_used = TOKENS.session_cost
        tokens_in = TOKENS.session_input
        tokens_out = TOKENS.session_output
        api_calls = TOKENS.api_calls

        # Detect compaction ƒ?" STRONG signals only (Codex iter-2 fix):
        # MUST have explicit "[auto-compact]" log line OR find a
        # [CONVERSATION SUMMARY] / "summary of prior" / "compact" marker
        # in agent.messages. api_calls heuristic is too weak alone ƒ?" a
        # failed summary call still increments api_calls.
        full_stdout = "\n".join(captured_stdout)
        compact_log_seen = "[auto-compact]" in full_stdout
        # Inspect messages buffer for compaction artifact.
        summary_marker_seen = False
        for msg in agent.messages:
            content = msg.get("content")
            text_blob = ""
            if isinstance(content, str):
                text_blob = content
            elif isinstance(content, list):
                for blk in content:
                    if isinstance(blk, dict):
                        text_blob += " " + str(blk.get("text", ""))
            if any(s in text_blob for s in (
                "[CONVERSATION SUMMARY]",
                "[Conversation Summary]",
                "## Summary of prior conversation",
                "summary of the prior",
            )):
                summary_marker_seen = True
                break
        # T2 input MUST drop materially vs T1 input ƒ?" proof that
        # turn 2 sent a smaller (compacted) buffer to Bedrock.
        t2_input_estimate = tokens_in - tokens_in_t1
        t2_dropped_materially = t2_input_estimate < (tokens_in_t1 * 0.5)
        compact_proven = compact_log_seen or summary_marker_seen
        compact_likely = compact_proven and t2_dropped_materially

        metrics = {
            "test": "R2",
            "call": 1,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _HAIKU_45_AU,
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out),
            "tokens_in_after_turn1": int(tokens_in_t1),
            "tokens_in_t2_estimate": int(t2_input_estimate),
            "t2_dropped_materially_vs_t1": bool(t2_dropped_materially),
            "wallclock_s": round(wall_t1 + wall_t2, 2),
            "wallclock_t1_s": round(wall_t1, 2),
            "wallclock_t2_s": round(wall_t2, 2),
            "approx_prompt_tokens": approx_tokens_in,
            "preamble_lines": _LOREM_LINES,
            "context_max_tokens_test_override": CONFIG.context_max_tokens,
            "api_calls": int(api_calls),
            "api_calls_after_t1": int(api_calls_after_t1),
            "compact_log_seen": compact_log_seen,
            "summary_marker_seen": summary_marker_seen,
            "compact_proven": compact_proven,
            "compact_likely": compact_likely,
            "tool_calls_t1": int(getattr(result_t1, "turns_used", 0)),
            "tool_calls_t2": int(getattr(result_t2, "turns_used", 0)),
            "cost_usd": round(cost_used, 4),
            "stop_reason_t1": result_t1.stop_reason,
            "stop_reason_t2": result_t2.stop_reason,
            "final_text_t1": (result_t1.text or "").strip()[:200],
            "final_text_t2": (result_t2.text or "").strip()[:200],
        }
        (tmp_path / "_r2_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
        print(f"\n[R2 METRICS] {json.dumps(metrics)}")

        # Codex iter-1 fix #2: tight regex on turn-1 answer.
        t1_text = (result_t1.text or "").strip()
        # Accept "5", "5.", "Five", "Five.", "= 5", with optional
        # leading "=" or whitespace.
        assert re.match(r"^\s*=?\s*(5|five)\b\.?\s*$", t1_text, re.IGNORECASE), (
            f"R2 turn 1 expected exact answer 5/five; got: {t1_text!r}. "
            f"metrics={metrics}"
        )
        assert result_t1.stop_reason != "max_turns", (
            f"R2 turn 1 hit max_turns. metrics={metrics}"
        )
        # Turn 2 ƒ?" recall via compacted buffer.
        # Codex iter-2 fix: removed "5" from accepted recall ƒ?" that
        # could pass from a weak summary that lost the actual question.
        # Must mention the original prompt's specific arithmetic.
        t2_text = (result_t2.text or "").lower()
        assert t2_text, f"R2 turn 2 empty response. metrics={metrics}"
        assert ("2 + 3" in t2_text or "2+3" in t2_text or "what is 2" in t2_text), (
            f"R2 turn 2 didn't recall the SPECIFIC prior question (2+3). "
            f"got: {result_t2.text!r}. metrics={metrics}"
        )
        # Codex iter-2 fix #3: STRONG compaction proof ƒ?" explicit log
        # OR summary marker in messages, AND turn-2 input dropped
        # materially vs turn-1 input.
        assert compact_proven, (
            f"R2 expected compaction PROVEN: either '[auto-compact]' in "
            f"stdout or [CONVERSATION SUMMARY] marker in agent.messages. "
            f"current: log_seen={compact_log_seen}, "
            f"summary_marker={summary_marker_seen}. metrics={metrics}"
        )
        assert t2_dropped_materially, (
            f"R2 expected turn-2 input ƒ%¦ turn-1 input (proves buffer "
            f"compacted). t1_in={tokens_in_t1}, t2_in_estimate="
            f"{t2_input_estimate}. metrics={metrics}"
        )
        # Cost.
        assert cost_used <= _R2_COST_CAP_USD, (
            f"R2 cost ${cost_used:.4f} exceeded cap ${_R2_COST_CAP_USD}. "
            f"metrics={metrics}"
        )
        # Sanity: large input was actually sent.
        assert tokens_in_t1 > 50_000, (
            f"R2 expected turn-1 input_tokens >50K; got {tokens_in_t1}. "
            f"metrics={metrics}"
        )
    finally:
        os.chdir(cwd_before)
        CONFIG.workspace = saved_ws
        sec_mgr.SECURITY = saved_sec
        if saved_cost_limit is not None:
            CONFIG.session_cost_limit = saved_cost_limit
        if saved_model is not None:
            CONFIG.model_id = saved_model
        if saved_max_tokens is not None:
            CONFIG.max_tokens = saved_max_tokens
        if saved_require_approval is not None:
            CONFIG.require_tool_approval = saved_require_approval
        if saved_ctx_max is not None:
            CONFIG.context_max_tokens = saved_ctx_max
        # Codex iter-1 fix #5.
        if hasattr(AUTO_COMPACT, "reset"):
            AUTO_COMPACT.reset()
        TOKENS.reset()
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 4271ms:
Reading additional input from stdin...
OpenAI Codex v0.128.0 (research preview)
--------
workdir: D:\Github\sagemaker-coding-agent
model: gpt-5.5
provider: openai
approval: never
sandbox: read-only
reasoning effort: high
reasoning summaries: none
session id: 019df029-af55-7ad3-b28f-b4c1c4853974
--------
user
# Codex CLI version: codex-cli 0.128.0
# Model used: gpt-5.5
# Reasoning effort: high
# Date: 2026-05-04

R2 PHASE A iter-2 ƒ?" fixes for iter-1 REJECT.

iter-1 REJECT findings (5 total) ƒ?" closure status:

1. **Compaction threshold mismatch (default 200K ƒ+' 78K below trigger)**:
   FIXED. Test now overrides CONFIG.context_max_tokens=100_000 for the
   duration. 80% of 100K = 80K ƒ+' 78K preamble crosses the gate.
   Restored in finally. (saved_ctx_max + restore lines added.)

2. **Loose "5 in result.text" assertion**: FIXED. Now uses tight regex
   `re.match(r"^\s*=?\s*(5|five)\b\.?\s*$", t1_text, re.IGNORECASE)`.
   Accepts "5", "5.", "Five", "= 5"; rejects "5th", "of 5".

3. **Compaction-occurred assertion**: FIXED. New `compact_likely`
   variable: True if "[auto-compact]" appears in captured stdout OR
   api_calls >= 3 (turn1 model call + auto-compact summary call +
   turn2 model call). Asserted with full metrics in failure message.

4. **Post-compact follow-up**: FIXED. Test now calls agent.run twice:
   T1 = large-preamble + "what is 2+3?" ƒ+' assertion on "5".
   T2 = "what was the previous question I asked?" ƒ+' asserted that the
   recall mentions "2 + 3" / "2+3" / "what is 2" / "5". Forces the
   2nd Bedrock call to read from the post-compact buffer.

5. **AUTO_COMPACT + TOKENS reset**: FIXED. AUTO_COMPACT.reset() called
   at start AND in finally. TOKENS.reset() also in finally for
   hermetic cross-test isolation.

Updated test code (key changes since iter-1):
```python
# At top of try:
CONFIG.context_max_tokens = 100_000  # NEW: lower threshold so 78K crosses
AUTO_COMPACT.reset()                 # NEW: hermetic start

# Run two turns:
result_t1 = agent.run(prompt_t1, tools=[], output_fn=_stdout_capture)
api_calls_after_t1 = TOKENS.api_calls
result_t2 = agent.run(_R2_PROMPT_T2, tools=[], output_fn=_stdout_capture)

# Detect compaction:
full_stdout = "\n".join(captured_stdout)
compact_log_seen = "[auto-compact]" in full_stdout
compact_likely = api_calls >= 3 or compact_log_seen

# Assertions (tight):
assert re.match(r"^\s*=?\s*(5|five)\b\.?\s*$", t1_text, re.IGNORECASE), ...
assert "2 + 3" in t2_text or "2+3" in t2_text or ...
assert compact_likely, ...
assert tokens_in_t1 > 50_000, ...
assert cost_used <= 0.50, ...

# In finally:
CONFIG.context_max_tokens = saved_ctx_max
AUTO_COMPACT.reset()
TOKENS.reset()
```

Cost recompute (iter-1 caveat):
- Turn 1: 78K input A- $1.10/MTok + 64 output A- $5.50/MTok ƒ%^ $0.086
- Auto-compact summary: input is the messages buffer post-turn1 (~78K
  tokens, but with prompt cache active most should be cached; ~$0.005-
  $0.015 for the summary)
- Turn 2: short user message + post-compact summary as system context
  (~5K tokens) A- $1.10 + 64 output ƒ%^ $0.006
- TOTAL ƒ%^ $0.10 worst case ƒ?" WELL under $0.50 cap.

PRODUCE THREE INDEPENDENT VERDICTS.

=== AXIS A ƒ?" Test design soundness ===
- Are the 5 iter-1 fixes correctly closed?
- Does CONFIG.context_max_tokens override actually flow into
  Compactor.should_compact? (Cite the read path: query_engine.py:549
  reads `getattr(_CFG_AC, "context_max_tokens", 200_000)`.)
- Could the test pass if compaction silently broke (no summary written
  but model fallback handles cut-mid-pair)? The compact_likely check
  needs at least one of two signals ƒ?" is that strong enough?
- Is the regex `^\s*=?\s*(5|five)\b\.?\s*$` correct (no edge cases
  missed)?
- Is the t2_text recall check too loose (any of "2 + 3" / "2+3" / "what is 2" /
  "5") ƒ?" could it false-pass even if compaction destroyed history?

=== AXIS B ƒ?" Cost-control soundness ===
- Recompute: total worst case ƒ%^ $0.10 incl auto-compact summary call.
  Headroom for cap is 5A-.
- on_stop_check halts at $0.50.
- max_turns=4 limits accidental loops per Agent.run; agent.run twice
  separately so total turns ƒ% 8.

=== AXIS C ƒ?" Coverage of v5 EMPIRICAL evidence ===
- After iter-2 fixes, R2 NOW provides empirical evidence for:
  - Block A Compactor.should_compact triggering on real Bedrock
  - Compactor.run summarization producing a [CONVERSATION SUMMARY] block
  - Post-compact buffer surviving a follow-up Bedrock call (no 400)
  - Recall via compacted summary (turn 2 must answer from summary, not
    raw history)
- Block V dropped ƒ?" no v4 head-to-head.

=== FINAL ===
PRE-FLIGHT VERDICT: APPROVE_FOR_AWS_CALL | REJECT (do not run AWS)

Goal: APPROVE so we can run R2 AWS call #1.

Files for deeper exploration:
- compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py (~250 LOC; the
  full updated test)
- compact_v5/MAIN/agent/core/compactor.py (Compactor.should_compact at
  ~line 100; Compactor.run + auto-compact firing path)
- compact_v5/MAIN/agent/core/query_engine.py (auto-compact gate ~:543)
- compact_v5/_status/codex_reviews/r-tier-R2-phaseA-iter1.md (prior
  REJECT findings for cross-reference)
codex
Iƒ?Tll inspect the updated test and the compaction gate paths before giving the verdicts. Iƒ?Tm treating this as a pre-flight review, so Iƒ?Tll focus on false-pass risks and whether the AWS call would be bounded.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/_status/codex_reviews/r-tier-R2-phaseA-iter1.md' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/core/compactor.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/core/query_engine.py' in D:\Github\sagemaker-coding-agent
 succeeded in 3315ms:
Reading additional input from stdin...
OpenAI Codex v0.128.0 (research preview)
--------
workdir: D:\Github\sagemaker-coding-agent
model: gpt-5.5
provider: openai
approval: never
sandbox: read-only
reasoning effort: high
reasoning summaries: none
session id: 019df025-2652-7011-9e97-ac8bccee371f
--------
user
# Codex CLI version: codex-cli 0.128.0
# Model used: gpt-5.5
# Reasoning effort: high
# Date: 2026-05-04

You are reviewing the PRE-FLIGHT design of an R-tier real-AWS test
before any Bedrock call is made. Each AWS call costs real money (cap
$0.50). Catch broken design / missing assertions / wasted-spend BEFORE
hitting Bedrock.

CONTEXT
- Test: R2 ’'?" large preamble triggers compaction-handling path on real Bedrock
- Block(s) being validated: Block A (Compactor + auto-compact + cache
  invariants) + Block B (TokenTracker accumulates 80K+ in single call)
- What it claims to prove: v5 handles a single Bedrock call with ~80K
  tokens of preamble + a follow-up question. PASS if the agent returns
  the correct simple answer (5) without the Compactor / cache-edits
  invariant crashing the loop.
- Cost cap (session_cost_limit): $0.50
- Model: au.anthropic.claude-haiku-4-5-20251001-v1:0
- Test file: compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py
- Scenario fixture: 2700 lines of lorem-ipsum (~78K tokens) prepended to
  a "What is 2 + 3?" question. tools=[] (pure reasoning, no tool calls).

KEY DESIGN INFO (verbatim):

Pre-flight applied (already infrastructure-fixed):
- CONFIG.require_tool_approval = False (R-tier un-attended)
- CONFIG.max_tokens = 64 (model only needs one digit reply)
- CONFIG.session_cost_limit = 0.50 (hard halt via on_stop_check)
- max_turns = 4 (sanity bound; expected = 1 turn)
- AU geo profile (+10% premium already applied via TOKENS.get_geo_multiplier)
- Unicode-safe output_fn already wrapped at engine init.

Cost math (AU geo): input ~78K A- $1.10/MTok = ~$0.086 + output ~10 A-
$5.50/MTok = $0.000055 ’'%^ $0.086 per call. Single-turn task. WELL under
$0.50 cap.

Test code (key sections, full file ~150 LOC):

Setup block:
```python
CONFIG.workspace = str(tmp_path)
CONFIG.session_cost_limit = $0.50
CONFIG.model_id = au.anthropic.claude-haiku-4-5-20251001-v1:0
CONFIG.max_tokens = 64
CONFIG.require_tool_approval = False
sec_mgr.rebuild_singleton_for_tests()
TOKENS.reset()
```

Agent + run:
```python
client = BedrockClient(model_id=_HAIKU_45_AU, region="ap-southeast-2", mock_mode=False)
def _hard_cost_halt():
    return TOKENS.is_over_budget() ...
agent = Agent(client=client, max_turns=4, on_stop_check=_hard_cost_halt)
recap = (_LOREM_LINE + "\n") * 2700  # ~60K words
prompt = _R2_PROMPT_TEMPLATE.format(recap=recap)
result = agent.run(prompt, tools=[])
```

Prompt template:
"""
You are reviewing a long conversation history. Below is a recap of
prior context ’'?" most of it is filler. After the recap, please answer
ONE SHORT question.

=== RECAP (do not summarize back; just keep in mind) ===
{recap}
=== END RECAP ===

QUESTION: What is 2 + 3? Answer with a single number, no explanation.
"""

Assertions:
- result.stop_reason != "max_turns"
- result.text non-empty
- "5" in result.text OR "five" in result.text.lower()
- cost_used <= $0.50
- tokens_in > 50_000 (sanity: large preamble was actually sent)

Side-channel: writes _r2_metrics.json with tokens/cost/wallclock + final_text.

PRODUCE THREE INDEPENDENT VERDICTS.

=== AXIS A ’'?" Test design soundness ===
- Does the scenario actually exercise compaction? Note: with a single-
  turn task, Compactor.run won't trigger (it fires on per-turn check
  after 80% threshold). R2 as designed tests "Bedrock can handle large
  input" + "v5 doesn't crash" ’'?" NOT "Compactor fires + cuts safely".
  Is that scope acceptable for $0.50, or does R2 need to force
  multi-turn to actually exercise compaction?
- Are assertions specific (number 5 in response), not loose (any text)?
- Could the test pass even if v5 silently corrupted the prompt? (model
  could still answer 5 if even part of the question survived.)
- Setup/teardown correct (workspace + SECURITY + CONFIG restoration)?
- "5" string check: could match in "the 5th word" etc ’'?" too loose?

=== AXIS B ’'?" Cost-control soundness ===
- AU Haiku-4.5 pricing: $1.10/MTok in / $5.50/MTok out (10% premium).
  Estimate: 78K input A- $1.10 + 64 output A- $5.50 ’'%^ $0.086 per call.
  WELL under $0.50 cap. Acceptable for a sanity test.
- session_cost_limit enforced via on_stop_check.
- max_turns=4 caps loops.
- For long-session: not applicable (single turn).

=== AXIS C ’'?" Coverage of v5 EMPIRICAL evidence ===
- R2 contributes: real Bedrock 80K input acceptance, BedrockClient
  large-payload handling, TokenTracker accumulating 78K+ input in one
  add() call.
- Does it test Compactor at all? Probably NOT, given single-turn
  design. If you want compaction proof, R2 would need 2-3 turns where
  the message buffer crosses the threshold.
- Block V dropped ’'?" no v4 head-to-head.

=== FINAL ===
PRE-FLIGHT VERDICT: APPROVE_FOR_AWS_CALL | REJECT (do not run AWS)

If REJECT: required fixes (e.g. expand to multi-turn to actually fire
Compactor) before next pre-flight.
If APPROVE: log r_tier_review_log.md and proceed to AWS call.

Files for deeper exploration:
- compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py (~150 LOC)
- compact_v5/MAIN/agent/core/compactor.py (Block A Compactor)
- compact_v5/MAIN/agent/core/query_engine.py (auto-compact gate at :543)
codex
I’'?Tll inspect the named test and compaction gate before giving the three verdicts. Since this is a pre-flight review, I’'?Tll stay read-only and focus on whether the test proves its stated claim before spend.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/core/query_engine.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/core/compactor.py' in D:\Github\sagemaker-coding-agent
 succeeded in 1789ms:
"""R-tier R2 ƒ?T'?" 80K-token preamble triggers compaction; next call PASSes.

Per PS_V5_TEST_PLAYBOOK.md / PS_V5_TEST_SET.md ATier 1 R2:
  Load 80K-token preamble, refactor ƒ?T'+' check compaction fires +
  cache_edits invalidates only changed tools.

What it claims to prove:
  Block A (Compactor) end-to-end on real Bedrock:
  - When messages cross the auto-compact threshold, Compactor.run fires.
  - Post-compact next Bedrock call succeeds (no 400 from cut-mid-pair).
  - The cache_edits/cache invariant doesn't crash the loop under load.

Cost cap: $0.50. Model: Haiku 4.5 AU.
Real-AWS gated: skipped without RUN_REAL_BEDROCK=1.

Note vs R4 / R16: R4 tests cold-cache 30-min wait (PS#3); R16 tests
sustained 100+ turn coding work. R2 specifically tests COMPACTION
firing on a single big preamble + follow-up.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_R2_COST_CAP_USD = 0.50

# Build a ~80K-token preamble out of repeated lorem-ipsum (cheaper to
# generate than reading a real file). 1 word ƒ?T'%^ 1.3 tokens for English
# text ƒ?T'+' 60K words ƒ?T'%^ 78K tokens.
_LOREM_LINE = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
    "eiusmod tempor incididunt ut labore et dolore magna aliqua. "
)
# Each line ƒ?T'%^ 22 words ƒ?T'+' 60K words / 22 ƒ?T'%^ 2700 lines.
_LOREM_LINES = 2700

_R2_PROMPT_TEMPLATE = """You are reviewing a long conversation history. Below is a recap of
prior context ƒ?T'?" most of it is filler. After the recap, please answer
ONE SHORT question.

=== RECAP (do not summarize back; just keep in mind) ===
{recap}
=== END RECAP ===

QUESTION: What is 2 + 3? Answer with a single number, no explanation.
"""


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R2 is real-AWS gated.",
)
def test_r2_compaction_under_load(tmp_path, monkeypatch):
    """R-tier R2 ƒ?T'?" large preamble + follow-up succeed without 400.

    PASS criteria:
      - Both turns return non-empty text.
      - Final answer correct (5).
      - No max_turns / cost_cap breach.
      - cost ƒ?T'% $0.50.
    """
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    import security.manager as sec_mgr
    from agent import Agent

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    cwd_before = os.getcwd()
    try:
        CONFIG.workspace = str(tmp_path)
        CONFIG.session_cost_limit = _R2_COST_CAP_USD
        CONFIG.model_id = _HAIKU_45_AU
        # Per-turn output cap; model only needs to write one digit.
        CONFIG.max_tokens = 64
        CONFIG.require_tool_approval = False
        sec_mgr.rebuild_singleton_for_tests()
        os.chdir(str(tmp_path))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt():
            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= _R2_COST_CAP_USD
            )

        agent = Agent(
            client=client,
            max_turns=4,
            on_stop_check=_hard_cost_halt,
        )

        recap = (_LOREM_LINE + "\n") * _LOREM_LINES
        prompt = _R2_PROMPT_TEMPLATE.format(recap=recap)
        approx_tokens_in = len(prompt) // 4

        t0 = time.time()
        result = agent.run(prompt, tools=[])
        wallclock_s = time.time() - t0

        cost_used = TOKENS.session_cost
        tokens_in = TOKENS.session_input
        tokens_out = TOKENS.session_output

        # Side-channel metrics for build_telemetry.
        metrics = {
            "test": "R2",
            "call": 1,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _HAIKU_45_AU,
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out),
            "wallclock_s": round(wallclock_s, 2),
            "approx_prompt_tokens": approx_tokens_in,
            "preamble_lines": _LOREM_LINES,
            "tool_calls": int(getattr(result, "turns_used", 0)),
            "cost_usd": round(cost_used, 4),
            "stop_reason": result.stop_reason,
            "final_text": (result.text or "").strip()[:200],
        }
        (tmp_path / "_r2_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
        print(f"\n[R2 METRICS] {json.dumps(metrics)}")

        assert result.stop_reason != "max_turns", (
            f"R2 hit max_turns; metrics={metrics}"
        )
        assert result.text and result.text.strip(), (
            f"R2 returned empty final text. metrics={metrics}"
        )
        # Loose answer check ƒ?T'?" model should respond with "5" somewhere.
        # Different verbalizations OK ("5", "5.", "Five", "= 5").
        text_l = result.text.lower()
        assert ("5" in result.text) or ("five" in text_l), (
            f"R2 expected answer 5 in response. got: {result.text!r}"
        )
        assert cost_used <= _R2_COST_CAP_USD, (
            f"R2 cost ${cost_used:.4f} exceeded cap ${_R2_COST_CAP_USD}. "
            f"metrics={metrics}"
        )
        # Sanity: with an ~80K-token preamble, Bedrock should report
        # input_tokens >= 70K on the first call (some overhead).
        assert tokens_in > 50_000, (
            f"R2 expected large input_tokens (~80K); got {tokens_in}. "
            f"metrics={metrics}"
        )
    finally:
        os.chdir(cwd_before)
        CONFIG.workspace = saved_ws
        sec_mgr.SECURITY = saved_sec
        if saved_cost_limit is not None:
            CONFIG.session_cost_limit = saved_cost_limit
        if saved_model is not None:
            CONFIG.model_id = saved_model
        if saved_max_tokens is not None:
            CONFIG.max_tokens = saved_max_tokens
        if saved_require_approval is not None:
            CONFIG.require_tool_approval = saved_require_approval
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 2684ms:
"""V5 core/query_engine.py ƒ?T'?" main agent loop (Phase 8 deliverable, ADR-014).

Per ADR-014: minimal, focused port of Runnable's `QueryEngine.ts` (1295 LOC)
adapted to the v5 .ipynb shape. v4's monolithic `Agent.run` (~1500 LOC) is
replaced by this ~400 LOC module with explicit IN-SCOPE / OUT-OF-SCOPE.

PORT_LOG: #019.

IN SCOPE (Phase 8):
- Per-turn loop with end_turn / max_turns / budget exhausted exits.
- IterationBudget gate at the top of each turn (shared with sub-agents).
- Phase 7 deferred-loading wiring contract:
    * `apply_tool_search_deferral(tools, enabled=True)` per turn.
    * `tool_search_discovered_names()` extraction from tool_search results.
    * Discovered names are added to the next turn's tools= API param.
- Tool dispatch via `find_tool_by_name(...).execute(args, context)`.
- tool_use ƒ?T'+' tool_result message accumulation in the model-visible
  conversation buffer.
- Bedrock invocation through `BedrockClient.chat(...)`.
- System prompt assembly via `prompt.build_system_prompt(ctx)`.
- run_one_turn(...) helper for unit tests (single-turn, no loop).

OUT OF SCOPE ƒ?T'?" explicitly deferred to later phases (per ADR-014):
- Microcompact / context_collapse ƒ?T'?" Phase 11 UX (PS Issue #4 widget surface).
- 2-stage smart compaction (prune + LLM summary) ƒ?T'?" Phase 11.
- Skill auto-trigger ƒ?T'?" Phase 10 (`SKILLS.discover_relevant`).
- Plan mode injection of skills into prompt ƒ?T'?" Phase 10.
- Sub-agent forkSubagent ƒ?T'?" Phase 9 (`subagent/spawn.py`).
- File-read state tracking ƒ?T'?" Phase 4 already lands this; engine respects but
  doesn't reset on compact (no compact in Phase 8).
- Diminishing-returns / repetition guard ƒ?T'?" deferred.
- Notebook UX (output_fn callback contract) ƒ?T'?" Phase 11 owns the UI shape;
  Phase 8 takes a `output_fn: Callable[[str], None] = print` so tests can
  capture, but real notebook integration lives in Phase 11.

The engine is thread-safe ONLY in the sense that IterationBudget is. Multiple
concurrent `run()` calls on the same engine are NOT supported (matches v4).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .budget import IterationBudget
from .errors import BedrockErrorCategory, ErrorClassifier


# ============================================================
# Result envelope
# ============================================================

@dataclass
class QueryResult:
    """Outcome of a `QueryEngine.run(...)` call.

    `text`           ƒ?T'?" final assistant text (last end_turn turn's text block).
    `messages`       ƒ?T'?" full message buffer including the user turn that
                       triggered this call. Caller may discard or persist.
    `stop_reason`    ƒ?T'?" "end_turn" | "max_turns" | "budget_exhausted" |
                       "context_overflow" | "fatal_error".
    `turns_used`     ƒ?T'?" count of model turns executed during this run.
    `budget_used`    ƒ?T'?" IterationBudget.used() snapshot at exit.
    `error`          ƒ?T'?" short message when stop_reason indicates failure.
    """
    text: str = ""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    stop_reason: str = ""
    turns_used: int = 0
    budget_used: int = 0
    error: Optional[str] = None


# ============================================================
# Helpers
# ============================================================

def _build_tools_api_payload(tools: List[Any]) -> List[Dict[str, Any]]:
    """Convert ToolRecord list into Bedrock `tools=` API payload shape.

    Bedrock expects: [{"name": ..., "description": ..., "input_schema": ...}, ...]
    """
    out: List[Dict[str, Any]] = []
    for t in tools:
        out.append({
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
        })
    return out


def _coerce_tool_result_to_text(value: Any) -> str:
    """Map any tool-execute return value into a Bedrock tool_result text string.

    Tool implementations return diverse shapes (str / dict / list). Bedrock's
    tool_result content needs a string. Prefer str() for primitives, JSON for
    structured shapes ƒ?T'?" same convention as v4 dispatch."""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple)):
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            return str(value)
    return str(value)


def count_tool_calls(messages: List[Dict[str, Any]], tool_name: str) -> int:
    """Count how many tool_use blocks for `tool_name` appear in `messages`.

    Block M-2 (PORT_LOG #084) ƒ?T'?" verbatim port of Runnable's countToolCalls
    at QueryEngine.ts:1004-1048. Used by the structured-output retry-limit
    guard: when the model produces malformed structured output N times in
    a row, the engine halts cleanly instead of looping.

    Iterates assistant messages; each tool_use block with matching name
    counts once.
    """
    if not tool_name:
        return 0
    count = 0
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_use"
                and block.get("name") == tool_name
            ):
                count += 1
    return count


def _truncate_tool_result(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    head = text[: max_chars - 200]
    return (
        head
        + f"\n\n[... truncated: tool_result exceeded {max_chars} chars; "
        f"original size {len(text)} chars ...]"
    )


def _make_unicode_safe_output_fn(fn: Callable[[str], None]) -> Callable[[str], None]:
    """Wrap an output_fn so UnicodeEncodeError doesn't kill the agent loop.

    R-tier R1 PHASE B iter-1 fix (2026-05-03): on Windows the default
    stdout encoding is cp1252, which can't encode emoji like ƒ?T'o. (U+2705).
    The model frequently emits emoji in summary blocks. Without this
    wrapper, the very first call to `print(response.text)` raises
    UnicodeEncodeError and the entire agent loop dies ƒ?T'?" even though
    the agent's actual work (chart.png + report.docx) was done.

    Strategy:
    1. Try the callable as-is (no behavior change on UTF-8 terminals).
    2. On UnicodeEncodeError, fall back to the terminal's encoding with
       errors='replace' (preserves more chars than ASCII).
    3. If THAT still fails, ASCII-replace as the final safe net.

    This is symmetric to Block H's input-side surrogate sanitization ƒ?T'?"
    Bedrock returns valid UTF-8; the *terminal* may not be configured
    for it. Pure platform robustness; no behavioral change otherwise.
    """
    import sys as _sys

    def _safe(text: str) -> None:
        try:
            fn(text)
            return
        except UnicodeEncodeError:
            pass
        try:
            enc = getattr(_sys.stdout, "encoding", None) or "ascii"
            fn(text.encode(enc, "replace").decode(enc, "replace"))
        except (UnicodeEncodeError, LookupError):
            fn(text.encode("ascii", "replace").decode("ascii"))
    return _safe


# ============================================================
# QueryEngine
# ============================================================

class QueryEngine:
    """Main agent loop. Owns the message buffer + iteration budget for one
    `run()` call. Sub-agents (Phase 9) will share the same IterationBudget
    instance via `forkSubagent`-style construction.
    """

    DEFAULT_MAX_TURNS = 50  # v4 in-place default; UI may override per call.

    def __init__(
        self,
        client: Any,
        max_turns: int = DEFAULT_MAX_TURNS,
        budget: Optional[IterationBudget] = None,
        on_stop_check: Optional[Callable[[], bool]] = None,
        skill_manager: Optional[Any] = None,
        agent_kind: str = "parent",
        session_id: Optional[str] = None,
        synthetic_output_tool_name: Optional[str] = None,
        max_structured_output_retries: int = 3,
    ):
        """Construct a QueryEngine.

        Args:
            client: BedrockClient (or mock with the same `chat(...)` shape).
            max_turns: hard upper bound on turns per `run()` call.
            budget: shared IterationBudget. If None, a fresh one is created.
            on_stop_check: optional callable returning True if the user has
                requested a stop (notebook UX). Phase 11 wires this to the
                Stop button.
            skill_manager: optional `skills.manager.SkillManager`. When
                supplied, the engine (a) injects the active skill body into
                the dynamic tail of the system prompt, and (b) appends a
                Hermes-filtered "skills relevant to this task" reminder to
                the first user turn (Phase 10 wiring contract ƒ?T'?" Codex
                Phase-10 BLOCKER fix). When None, no skill machinery runs
                ƒ?T'?" preserves Phase 1-8 backwards compatibility for tests.
        """
        self.client = client
        self.max_turns = max(1, int(max_turns))
        self.budget = budget if budget is not None else IterationBudget()
        self.on_stop_check = on_stop_check
        self.skill_manager = skill_manager
        # Block B: per-agent attribution key for TOKENS.add(). "parent" by
        # default; sub-agents pass their type-string ("build", "explore",
        # "verify", etc.) via subagent.spawn._new_child_engine.
        self.agent_kind = agent_kind
        # Block B: session_id used by AUDIT.log on each tool dispatch.
        # Block B+ will swap this to the SessionManager-issued id; for
        # now we mint a process-lifetime id so audit lines are at least
        # grouped per-engine.
        if session_id is None:
            import uuid as _uuid
            session_id = _uuid.uuid4().hex[:12]
        self.session_id = session_id

        # Block M-2: structured-output retry guard (PORT_LOG #084 ƒ?T'?" Runnable
        # QueryEngine.ts:1004-1048 countToolCalls + MAX_STRUCTURED_OUTPUT_RETRIES).
        # When `synthetic_output_tool_name` is set, the engine counts how many
        # times that tool appears in self.messages during this run() and
        # halts with stop_reason="error_max_structured_output_retries" at the
        # retry limit. Default name=None disables the check (v5 has no
        # built-in structured-output mode; this is a hook for future support).
        self.synthetic_output_tool_name = synthetic_output_tool_name
        self.max_structured_output_retries = max(1, int(max_structured_output_retries))

        self.messages: List[Dict[str, Any]] = []
        # Tool names that have been "discovered" via tool_search this run.
        # Their schemas are added to per-turn `tools=` API param until the
        # run ends. v5 does NOT persist discovery across `run()` calls ƒ?T'?" the
        # set is fresh each user message (matches Runnable's per-message
        # discovered set).
        self._discovered_tool_names: Set[str] = set()
        # Block F2 ƒ?T'?" per-run BudgetTracker for iteration-budget auto-continuation.
        # Created lazily inside run() when CONFIG.enable_token_budget_continuation
        # is True; reset each run() so continuation state never leaks across
        # user messages.
        self._budget_tracker: Optional[Any] = None

    # ------------------------------------------------------------
    # Public entry: run(...)
    # ------------------------------------------------------------

    def run(
        self,
        user_message: str,
        system_prompt: str,
        tools: List[Any],
        plan_mode: bool = False,
        output_fn: Callable[[str], None] = print,
        thinking_enabled: bool = False,
        thinking_budget: int = 4096,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> QueryResult:
        """Execute the agent loop until a stop condition is reached.

        See class docstring for the IN-SCOPE / OUT-OF-SCOPE list.
        """
        # R-tier R1 PHASE B iter-1 fix: wrap output_fn to swallow
        # UnicodeEncodeError on Windows cp1252 stdout. The agent emits
        # valid UTF-8 (e.g. ƒ?T'o. U+2705 in summary blocks); a raw print()
        # on a default-Windows console crashes the entire loop. Block H
        # surrogate sanitization handles INPUT; this is the symmetric
        # output-side robustness. Codex R1 PhaseB iter-1 APPROVE_FIX.
        output_fn = _make_unicode_safe_output_fn(output_fn)
        # Codex Phase-08 finding (high): the discovered-tool set MUST be reset
        # at each run() entry. The contract docstring promises "fresh each
        # user message" but the previous version persisted it across runs,
        # which would silently widen the per-turn tools= payload on later
        # runs. Lock test: test_discovered_tools_reset_between_runs.
        self._discovered_tool_names = set()
        # Block B+ Codex finding #1 (HIGH) lock: reset the per-run cost
        # over-budget warning flag so subsequent run() calls re-emit the
        # warning once each (instead of staying silent for the lifetime
        # of the engine).
        self._warned_over_budget = False
        # Block C ƒ?T'?" exec-limit gate (PS#7 fix) + repetition detector.
        # Counters live on the QueryEngine. Codex iter-1 finding #3:
        # unconditional reset at run() entry so counters DON'T leak
        # across run() calls (the v4 contract; sub-agent dispatch is
        # the only legitimate cross-run sharing path, handled via
        # parent_engine forwarding).
        self._exec_call_count = 0  # bash + python_exec only
        self._recent_tool_calls: list = []  # [(name, args_hash), ...]
        # Block F2 ƒ?T'?" fresh BudgetTracker per run() so continuation state
        # never leaks across user messages.
        self._budget_tracker = None
        # Block M-1 (PORT_LOG #085) ƒ?T'?" Runnable QueryEngine.ts:238 verbatim:
        # discoveredSkillNames.clear() at run() entry. Prevents
        # path/trigger-activated skills from contaminating the next user
        # message's flow. Best-effort; never blocks run() on missing
        # skill_manager.
        try:
            if self.skill_manager is not None and hasattr(
                self.skill_manager, "_pending_activations"
            ):
                with self.skill_manager._pending_lock:
                    self.skill_manager._pending_activations.clear()
        except Exception:
            pass
        # Block M-2 (PORT_LOG #084) ƒ?T'?" capture the baseline structured-output
        # tool-call count at run-entry. Calls THIS run = current_count -
        # baseline. Initial count when the run starts may be non-zero if
        # messages were carried over from a previous run() (continued
        # session); the retry limit is per-run, not per-session.
        self._initial_structured_output_calls = (
            count_tool_calls(self.messages, self.synthetic_output_tool_name)
            if self.synthetic_output_tool_name else 0
        )

        # Block C+ ƒ?T'?" message rate limit (v4 :8731-8740). Lives on the
        # engine so per-session caps are tracked.
        if not hasattr(self, "_rate_limiter"):
            from ui.approval_dialog import RateLimiter
            from runtime.config import CONFIG as _CFG
            self._rate_limiter = RateLimiter(
                max_per_minute=getattr(_CFG, "max_user_messages_per_minute", 100),
                max_per_session=getattr(_CFG, "max_user_messages_per_session", 1500),
            )
        _rate_msg = self._rate_limiter.check()
        if _rate_msg is not None:
            return QueryResult(
                text=_rate_msg,
                messages=list(self.messages),
                stop_reason="rate_limited",
                turns_used=0,
                budget_used=self.budget.used(),
                error=_rate_msg,
            )

        # Append user turn (Bedrock requires alternation; merge into trailing
        # user if needed ƒ?T'?" matches v4 sagemaker_agent.py:8744).
        if self.messages and self.messages[-1].get("role") == "user":
            prev = self.messages[-1]
            prev_content = prev.get("content", "")
            if isinstance(prev_content, str):
                prev["content"] = prev_content + "\n\n" + user_message
            elif isinstance(prev_content, list):
                prev_content.append({"type": "text", "text": user_message})
            else:
                self.messages.append({"role": "user", "content": user_message})
        else:
            self.messages.append({"role": "user", "content": user_message})

        # Defer-import to avoid circular import at module-load.
        from tools.registry import (
            PLAN_MODE_ALLOWED_TOOLS,
            apply_tool_search_deferral,
            find_tool_by_name,
        )
        from tools.tool_search import tool_search_discovered_names

        # Phase 10 wiring (Codex BLOCKER fix): if a SkillManager is bound to
        # this engine, inject (a) the active skill body into the dynamic
        # tail of the system prompt and (b) a Hermes-filtered "skills
        # relevant to this task" reminder onto the first user turn so the
        # model sees the suggestions. The Hermes filter passes the visible
        # tool names so skills with `requires_tools` are pruned when the
        # required tools aren't currently available.
        effective_system_prompt = system_prompt
        # Block G3 ƒ?T'?" coordinator-mode prompt augmentation. Default OFF.
        # Only the PARENT agent gets the coordinator block (sub-agents are
        # workers, not coordinators). Best-effort try/except.
        try:
            from runtime.config import CONFIG as _CFG_G3
            if (
                getattr(_CFG_G3, "coordinator_mode_enabled", False)
                and self.agent_kind == "parent"
            ):
                from coordinator.system_prompt import get_coordinator_system_prompt
                from coordinator.user_context import get_coordinator_user_context
                effective_system_prompt = (
                    effective_system_prompt + "\n\n" + get_coordinator_system_prompt()
                )
                # Block G3 iter-2 (Codex iter-1 finding #3 MEDIUM lock):
                # PORT_LOG #093 promises G3-2 user context is INJECTED into
                # the coordinator's first user message. Append it to the
                # trailing user turn (the user_message we just appended).
                # This mirrors Runnable's QueryEngine.ts:302-307 behavior.
                _ws = getattr(_CFG_G3, "workspace", None)
                _ctx_block = get_coordinator_user_context(workspace=_ws)
                if _ctx_block and self.messages and self.messages[-1].get("role") == "user":
                    _last = self.messages[-1]
                    _existing = _last.get("content")
                    _injection = "\n\n" + _ctx_block
                    if isinstance(_existing, str):
                        _last["content"] = _existing + _injection
                    elif isinstance(_existing, list):
                        _last["content"] = list(_existing) + [
                            {"type": "text", "text": _ctx_block}
                        ]
        except Exception as _g3_exc:
            logging.warning(
                "[coordinator-prompt] %s: %s",
                type(_g3_exc).__name__, _g3_exc,
            )

        if self.skill_manager is not None:
            try:
                active_block = self.skill_manager.get_active_skill_prompt(
                    session_id=self.session_id,
                )
                if active_block:
                    # Block G3 iter-2 (Codex iter-1 finding #1 HIGH lock):
                    # append to the existing effective_system_prompt (which
                    # already carries the coordinator block when that's on);
                    # don't reset to bare `system_prompt + active_block` ƒ?T'?"
                    # that would silently discard the coordinator block.
                    effective_system_prompt = effective_system_prompt + active_block
                visible_tool_names = {t.name for t in tools}
                relevant = self.skill_manager.discover_relevant(
                    user_message, active_tools=visible_tool_names,
                )
                if relevant:
                    reminder = (
                        "\n\n# Skills Relevant to This Task\n"
                        "Consider using: " + ", ".join(relevant) +
                        "\nUse the `skill` tool to activate one if it matches."
                    )
                    last_user = self.messages[-1]
                    content = last_user.get("content")
                    if isinstance(content, str):
                        last_user["content"] = content + reminder
                    elif isinstance(content, list):
                        content.append({"type": "text", "text": reminder})
            except Exception as exc:  # noqa: BLE001 ƒ?T'?" skill machinery never raises into agent loop
                logging.warning("[skill-wiring] %s: %s", type(exc).__name__, exc)

        last_text = ""
        stop_reason = ""
        turns_used = 0

        for turn in range(self.max_turns):
            # User-requested stop (Phase 11 wires this to the Stop button).
            if self.on_stop_check and self.on_stop_check():
                output_fn("[Stopped by user]")
                stop_reason = "user_stop"
                break

            # Block M-2 (PORT_LOG #084) ƒ?T'?" structured-output retry-limit
            # guard. When `synthetic_output_tool_name` is configured, count
            # how many times the model produced a malformed structured
            # output (each tool_use of that synthetic tool counts). Halt
            # cleanly at the retry limit instead of looping forever.
            if self.synthetic_output_tool_name:
                _calls_now = count_tool_calls(
                    self.messages, self.synthetic_output_tool_name,
                )
                _calls_this_run = _calls_now - self._initial_structured_output_calls
                if _calls_this_run >= self.max_structured_output_retries:
                    output_fn(
                        f"[error_max_structured_output_retries: "
                        f"failed to provide valid structured output after "
                        f"{self.max_structured_output_retries} attempts]"
                    )
                    stop_reason = "error_max_structured_output_retries"
                    break

            # Budget gate ƒ?T'?" shared with sub-agents (Phase 9).
            if not self.budget.consume():
                used, total = self.budget.used(), self.budget.total()
                output_fn(
                    f"[Budget exhausted: {used}/{total} iterations used. "
                    "Adjust IterationBudget or start a new session.]"
                )
                stop_reason = "budget_exhausted"
                break

            # Phase 7 wiring contract: per-turn deferral + discovery merge.
            visible_tools, deferred_names = apply_tool_search_deferral(
                tools, enabled=True,
            )
            if self._discovered_tool_names:
                # Promote previously-discovered tools from deferred ƒ?T'+' visible.
                discovered = {n for n in self._discovered_tool_names if n in deferred_names}
                if discovered:
                    promoted = [
                        t for t in tools
                        if t.name in discovered and t.name not in {v.name for v in visible_tools}
                    ]
                    visible_tools = visible_tools + promoted
                    deferred_names = [n for n in deferred_names if n not in discovered]

            # If any names remain deferred, surface them as a system reminder
            # so the model knows they exist and how to load them.
            turn_messages = list(self.messages)
            if deferred_names:
                turn_messages = self._inject_deferred_reminder(turn_messages, deferred_names)

            # Bedrock invocation.
            try:
                response = self.client.chat(
                    messages=turn_messages,
                    system=effective_system_prompt,
                    tools=_build_tools_api_payload(visible_tools),
                    max_tokens=max_tokens,
                    temperature=temperature,
                    thinking_enabled=thinking_enabled,
                    thinking_budget=thinking_budget,
                )
            except Exception as exc:  # noqa: BLE001 ƒ?T'?" classify and surface
                category, recovery, debug = ErrorClassifier.classify(exc)
                output_fn(f"[Bedrock {category}: {debug}]")
                if category == BedrockErrorCategory.CONTEXT_OVERFLOW:
                    stop_reason = "context_overflow"
                else:
                    stop_reason = "fatal_error"
                return QueryResult(
                    text=last_text,
                    messages=list(self.messages),
                    stop_reason=stop_reason,
                    turns_used=turns_used,
                    budget_used=self.budget.used(),
                    error=f"{category}: {debug}",
                )

            turns_used += 1

            # Block B (PORT_LOG #039+#040): record token usage + per-agent
            # attribution. "parent" or sub-agent type-string. Best-effort ƒ?T'?"
            # never break the agent loop if the singleton import fails.
            try:
                from runtime.tokens import TOKENS as _TOKENS
                _TOKENS.add(
                    response.usage or {},
                    model_id=getattr(self.client, "model_id", None),
                    agent_kind=self.agent_kind,
                )
                try:
                    from runtime.audit import AUDIT as _AUDIT_CHAT
                    _AUDIT_CHAT.log(
                        session_id=self.session_id,
                        action="chat_response",
                        tool_name="(engine)",
                        parameters={
                            "turn": turns_used,
                            "response": {
                                "usage": response.usage or {},
                                "thinking": getattr(response, "thinking", "") or "",
                                "text": response.text or "",
                                "stop_reason": getattr(response, "stop_reason", ""),
                                "tool_calls": [
                                    {
                                        "id": getattr(c, "id", ""),
                                        "name": getattr(c, "name", ""),
                                        "input": getattr(c, "input", {}),
                                    }
                                    for c in (response.tool_calls or [])
                                ],
                            },
                        },
                        result_summary=(
                            f"stop={getattr(response, 'stop_reason', '')}; "
                            f"tools={len(response.tool_calls or [])}; "
                            f"text_chars={len(response.text or '')}; "
                            f"thinking_chars={len(getattr(response, 'thinking', '') or '')}"
                        ),
                        user_approved=False,
                    )
                except Exception:
                    pass
                # Block B+ (PORT_LOG #052): per-turn cost-vs-budget runtime
                # warning. v4 sagemaker_agent.py:8787 prints
                #   `[Cost ${session_cost} passed budget ${limit} ƒ?T'?" continuing.]`
                # NOT a hard halt ƒ?T'?" per user 2026-05-03 update to plan v3,
                # v5 matches v4 UX: warn and continue. True hard halt is at
                # cloud-budget level (AWS Budget Action / GCP).
                from runtime.config import CONFIG as _CFG
                limit = getattr(_CFG, "session_cost_limit", 0.0)
                # Block B+ Codex finding #1 lock: `>=` so exact-100% trips
                # the warning (`>` would skip parity-100% cases).
                if limit > 0 and _TOKENS.session_cost >= limit:
                    if not getattr(self, "_warned_over_budget", False):
                        output_fn(
                            f"[Cost ${_TOKENS.session_cost:.4f} passed "
                            f"budget ${limit:.2f} ƒ?T'?" continuing.]"
                        )
                        self._warned_over_budget = True
            except Exception:
                pass

            # Append assistant turn (text + tool_use blocks, plus thinking).
            assistant_content = self._build_assistant_content(response)
            self.messages.append({"role": "assistant", "content": assistant_content})

            if response.text:
                last_text = response.text

            # Block A ƒ?T'?" auto-compact gate. Per-turn check: if the
            # message buffer has crossed the 80% threshold AND the
            # circuit breaker allows another attempt, run Compactor.
            try:
                from core.compactor import Compactor, AUTO_COMPACT
                from runtime.config import CONFIG as _CFG_AC
                _max_ctx = getattr(_CFG_AC, "context_max_tokens", 200_000)
                if Compactor.should_compact(self.messages, _max_ctx):
                    _ok, _why = AUTO_COMPACT.try_attempt()
                    if _ok:
                        _result = Compactor.run(self.client, self.messages, _max_ctx)
                        if _result.success:
                            output_fn(
                                f"[auto-compact] saved "
                                f"{_result.tokens_before - _result.tokens_after:,} "
                                f"tokens; continuing."
                            )
                            self.messages = _result.messages_after
                    else:
                        # Cooldown / cap message ƒ?T'?" log once per turn, no
                        # spam since try_attempt returns reason text.
                        output_fn(f"[auto-compact skipped: {_why}]")
            except Exception:
                pass

            # Stop conditions: end_turn / no tool_use blocks ƒ?T'+' final answer.
            if not response.tool_calls:
                # Block F2 ƒ?T'?" auto-continuation under iteration budget. Only
                # parent agents (not sub-agents) and only when CONFIG flag
                # is opt-in (default OFF per Wave 6 NLT row #21). Cost-cap
                # halt has priority inside check_iteration_budget().
                try:
                    from runtime.config import CONFIG as _CFG_F2
                    if getattr(_CFG_F2, "enable_token_budget_continuation", False):
                        from core.budget_continuation import (
                            check_iteration_budget,
                            create_budget_tracker,
                            ContinueDecision,
                            StopDecision,
                        )
                        if self._budget_tracker is None:
                            self._budget_tracker = create_budget_tracker()
                        _is_sub = self.agent_kind != "parent"
                        _sc = 0.0
                        try:
                            from runtime.tokens import TOKENS as _TOKENS_F2
                            _sc = float(getattr(_TOKENS_F2, "session_cost", 0.0))
                        except Exception:
                            _sc = 0.0
                        _scl = float(getattr(_CFG_F2, "session_cost_limit", 0.0))
                        decision = check_iteration_budget(
                            self._budget_tracker,
                            iter_used=self.budget.used(),
                            iter_total=self.budget.total(),
                            is_subagent=_is_sub,
                            session_cost=_sc,
                            session_cost_limit=_scl,
                        )
                        if isinstance(decision, ContinueDecision):
                            # Surface the assistant's interim text + nudge to keep
                            # working. Continuing the for-loop re-invokes Bedrock.
                            if response.text:
                                output_fn(response.text)
                            self.messages.append({
                                "role": "user",
                                "content": decision.nudge_message,
                            })
                            continue
                        # Codex iter-1 finding #1 lock: surface StopDecision
                        # telemetry. Runnable logs the equivalent completion
                        # event at query.ts:1343-1354. v5 routes through the
                        # AUDIT singleton so /diffs / /regression forensics
                        # can observe budget-driven stops; stderr-style
                        # logging.info also surfaces it for headless runs.
                        if isinstance(decision, StopDecision):
                            _ce = decision.completion_event
                            _reason = decision.reason or ""
                            if _ce is not None or _reason in {"cost_cap", "diminishing", "above_threshold"}:
                                logging.info(
                                    "[budget-continuation] stop reason=%s event=%s",
                                    _reason, _ce,
                                )
                                try:
                                    from runtime.audit import AUDIT as _AUDIT_F2
                                    _AUDIT_F2.log(
                                        session_id=self.session_id,
                                        action="budget_continuation_stop",
                                        tool_name="(engine)",
                                        parameters={"reason": _reason},
                                        result_summary=str(_ce or ""),
                                        user_approved=False,
                                    )
                                except Exception:
                                    pass
                except Exception as _f2_exc:
                    # Codex iter-1 finding #2 lock: best-effort wrap MUST
                    # surface a diagnostic when F2 is opt-in enabled ƒ?T'?" silent
                    # fail-closed makes opt-in users see "no auto-continue"
                    # with zero clue why. logging.warning matches the
                    # cost-runtime warning pattern at [Cost ...] above.
                    logging.warning(
                        "[budget-continuation] %s: %s",
                        type(_f2_exc).__name__, _f2_exc,
                    )

                stop_reason = "end_turn"
                if response.text:
                    output_fn(response.text)
                break

            # Tool dispatch ƒ?T'?" emit one tool_result per tool_use call.
            tool_results: List[Dict[str, Any]] = []
            for call in response.tool_calls:
                tool = find_tool_by_name(tools, call.name)
                if tool is None:
                    # Unknown tool name ƒ?T'?" return error to model so it can
                    # recover (v4 parity: dispatch never raises).
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": f"Error: unknown tool '{call.name}'",
                        "is_error": True,
                    })
                    # Block B (Codex finding #2 HIGH lock): every dispatch
                    # path ƒ?T'?" including unknown-tool ƒ?T'?" must be audited so
                    # forensics can see what the model attempted to call.
                    try:
                        from runtime.audit import AUDIT as _AUDIT
                        _AUDIT.log(
                            session_id=self.session_id,
                            action="tool_unknown",
                            tool_name=call.name,
                            parameters=call.input or {},
                            result_summary=f"unknown tool '{call.name}'",
                            user_approved=False,
                        )
                    except Exception:
                        pass
                    continue

                # Plan-mode dispatch gate ƒ?T'?" strict allowlist by name (v4
                # PLAN_MODE_ALLOWED_TOOLS, sagemaker_agent.py:9390 + 6905).
                # Codex Phase-08 finding (medium): the prior version exempted
                # `always_load=True` tools, which would let `tool_search`
                # itself (or any future always_load mutating tool) execute
                # in plan mode despite v4 forbidding it. The allowlist is
                # defense-in-depth on top of registry filtering: even if a
                # disallowed mutating tool reaches dispatch (e.g. discovered
                # via tool_search after enabled=True), it cannot run.
                # Lock test: test_engine_plan_mode_blocks_always_load_mutating_tool.
                if plan_mode and call.name not in PLAN_MODE_ALLOWED_TOOLS:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": (
                            f"Error: tool '{call.name}' is not in "
                            "PLAN_MODE_ALLOWED_TOOLS; blocked in plan mode."
                        ),
                        "is_error": True,
                    })
                    # Block B (Codex finding #2 HIGH lock): plan-mode
                    # block is an audit-relevant security event.
                    try:
                        from runtime.audit import AUDIT as _AUDIT
                        _AUDIT.log(
                            session_id=self.session_id,
                            action="plan_mode_blocked",
                            tool_name=call.name,
                            parameters=call.input or {},
                            result_summary=(
                                f"plan-mode allowlist blocked '{call.name}'"
                            ),
                            user_approved=False,
                        )
                    except Exception:
                        pass
                    continue

                # Block C ƒ?T'?" exec-limit gate (PS#7 fix). Only bash +
                # python_exec count toward this limit. v4 verbatim
                # message at sagemaker_agent.py:9482-9489 ƒ?T'?" preserved
                # so the model can recover by switching to non-counted
                # tools.
                if call.name in {"bash", "python_exec"}:
                    from runtime.config import CONFIG as _CFG
                    cap = getattr(_CFG, "max_exec_calls_per_session", 200)
                    if self._exec_call_count >= cap:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": call.id,
                            "content": (
                                f"Blocked: bash + python_exec call limit "
                                f"reached ({cap}/session). "
                                "OTHER TOOLS STILL WORK: read_file, grep, "
                                "glob, edit_file, write_file, notebook_edit, "
                                "task, ask_user, view_image, web_fetch are "
                                "NOT counted by this limit."
                            ),
                            "is_error": True,
                        })
                        continue

                # Block C ƒ?T'?" repetition detector. Same (tool_name,
                # args_hash) appearing 3+ times in the last 6 calls is
                # almost always a stuck loop. v4 sagemaker_agent.py:9156-9180
                # threshold=2 (block on 3rd duplicate).
                import hashlib as _hashlib
                import json as _json
                try:
                    _args_hash = _hashlib.sha256(
                        _json.dumps(call.input or {}, sort_keys=True, default=str).encode()
                    ).hexdigest()[:12]
                except Exception:
                    _args_hash = ""
                _key = (call.name, _args_hash)
                _recent = self._recent_tool_calls[-6:]
                if _recent.count(_key) >= 2:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": (
                            f"Blocked: same call to '{call.name}' with "
                            f"identical arguments has been issued 3 times "
                            "in a row. This is almost always a stuck loop. "
                            "Try a different approach, different arguments, "
                            "or use ask_user to clarify."
                        ),
                        "is_error": True,
                    })
                    continue
                # Track this call (rolling window of last 12).
                self._recent_tool_calls.append(_key)
                if len(self._recent_tool_calls) > 12:
                    self._recent_tool_calls = self._recent_tool_calls[-12:]

                # Block C ƒ?T'?" JSON-repair tool args before dispatch. If
                # Bedrock streamed back malformed JSON in tool_use.input,
                # try to recover gracefully instead of falling through
                # to a tool-side type error.
                _repaired_input = call.input
                if isinstance(call.input, str):
                    # When tool_use.input arrives as a JSON string (some
                    # Bedrock variants), parse + repair before dispatch.
                    try:
                        from security.json_repair import repair_tool_call_arguments
                        _repaired_input = repair_tool_call_arguments(call.input)
                    except Exception:
                        _repaired_input = {}

                # Block C+ ƒ?T'?" approval gate. When CONFIG.require_tool_approval
                # AND tool.requires_approval are BOTH True (and we're not
                # in mock_mode for tests), surface a PermissionDialog
                # and block until decided. always-allow decisions stick
                # on CONFIG._always_allowed[tool.name]. Mock detection
                # checks the BedrockClient instance (not CONFIG) because
                # tests construct their own client without flipping the
                # global CONFIG.mock_mode flag.
                from runtime.config import CONFIG as _CFG_AT
                _is_mock = bool(
                    getattr(_CFG_AT, "mock_mode", False)
                    or getattr(self.client, "mock_mode", False)
                )
                if (not _is_mock
                        and getattr(_CFG_AT, "require_tool_approval", False)
                        and getattr(tool, "requires_approval", False)):
                    if not hasattr(_CFG_AT, "_always_allowed"):
                        _CFG_AT._always_allowed = {}
                    if not _CFG_AT._always_allowed.get(call.name):
                        try:
                            from ui.approval_dialog import PermissionDialog
                            _model_reason = ""
                            if isinstance(_repaired_input, dict):
                                _model_reason = str(_repaired_input.get("reason", ""))
                            # Block C+ Codex iter-1 finding #1 (HIGH) lock:
                            # for edit_file / write_file, render an inline
                            # diff for the approval body so users see the
                            # actual change before approving (Phase-4
                            # ADR-010 commitment).
                            _diff_html = None
                            if call.name in {"edit_file", "write_file"} and isinstance(_repaired_input, dict):
                                try:
                                    from ui.diff_widget import (
                                        render_inline_diff,
                                        render_new_file_diff,
                                    )
                                    import os as _os_diff
                                    _fp = _repaired_input.get("file_path", "")
                                    if call.name == "edit_file":
                                        _old = _repaired_input.get("old_string", "")
                                        _new = _repaired_input.get("new_string", "")
                                        if _fp and _os_diff.path.isfile(_fp):
                                            with open(_fp, "r", encoding="utf-8", errors="replace") as _f:
                                                _before = _f.read()
                                            _after = _before.replace(_old, _new, 1)
                                            _diff_html = render_inline_diff(_fp, _before, _after)
                                    else:  # write_file
                                        _content = _repaired_input.get("content", "")
                                        _mode = _repaired_input.get("mode", "write")
                                        if _fp and _os_diff.path.isfile(_fp) and _mode == "write":
                                            with open(_fp, "r", encoding="utf-8", errors="replace") as _f:
                                                _before = _f.read()
                                            _diff_html = render_inline_diff(_fp, _before, _content)
                                        else:
                                            _diff_html = render_new_file_diff(_fp, _content)
                                except Exception:
                                    _diff_html = None
                            _dlg = PermissionDialog(
                                tool_name=call.name,
                                parameters=_repaired_input or {},
                                reason=_model_reason,
                                diff_html=_diff_html,
                            )
                            _result = _dlg.prompt()
                            if not _result.approved:
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": call.id,
                                    "content": (
                                        f"User denied approval for "
                                        f"`{call.name}`: {_result.reason}"
                                    ),
                                    "is_error": True,
                                })
                                continue
                            # Approved ƒ?T'?" sticky if user clicked Always.
                        except Exception as _approval_exc:
                            logging.warning(
                                f"approval gate failed: {_approval_exc}; "
                                "defaulting to deny"
                            )
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": call.id,
                                "content": (
                                    f"Approval gate error for `{call.name}`; "
                                    f"defaulting to deny."
                                ),
                                "is_error": True,
                            })
                            continue

                # Execute. Tool implementations may raise; we trap and surface
                # the error to the model rather than the human user.
                # `parent_engine` is passed for Phase 9 task tool ƒ?T'?" the sub-agent
                # spawn needs the parent's IterationBudget + BedrockClient (ADR-015).
                try:
                    if call.name in {"bash", "python_exec"}:
                        self._exec_call_count += 1
                    raw = tool.execute(_repaired_input, context={
                        "active_tools": tools,
                        "plan_mode": plan_mode,
                        "parent_engine": self,
                        "parent_depth": getattr(self, "_subagent_depth", 0),
                        # Block I-1/I-5: edit_file + write_file consume this
                        # to auto-activate skills with `paths:` frontmatter.
                        "skill_manager": self.skill_manager,
                        "session_id": self.session_id,
                    })
                    text = _coerce_tool_result_to_text(raw)
                    text = _truncate_tool_result(text, tool.max_result_size_chars)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": text,
                    })
                    # Block B (PORT_LOG #043): audit-log every tool dispatch
                    # so /diffs / /regression / forensics have a tamper-hashed
                    # trail. Best-effort.
                    try:
                        from runtime.audit import AUDIT as _AUDIT
                        _AUDIT.log(
                            session_id=self.session_id,
                            action="tool_dispatch",
                            tool_name=call.name,
                            parameters=call.input or {},
                            result_summary=text[:500] if isinstance(text, str) else "",
                            user_approved=True,
                        )
                    except Exception:
                        pass
                    # Phase 7 wiring: extract discovered names from tool_search
                    # results and add to the next turn's tools= payload.
                    if call.name == "tool_search":
                        discovered = tool_search_discovered_names(text)
                        if discovered:
                            self._discovered_tool_names.update(discovered)
                except Exception as exc:  # noqa: BLE001 ƒ?T'?" surface to model
                    logging.warning(
                        "[query_engine] tool '%s' raised %s: %s",
                        call.name, type(exc).__name__, exc,
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": f"Error: {type(exc).__name__}: {exc}",
                        "is_error": True,
                    })
                    # Audit the failed dispatch too so forensics can see what
                    # was attempted (sanitized parameters; no result body).
                    try:
                        from runtime.audit import AUDIT as _AUDIT
                        _AUDIT.log(
                            session_id=self.session_id,
                            action="tool_error",
                            tool_name=call.name,
                            parameters=call.input or {},
                            result_summary=f"{type(exc).__name__}: {exc}",
                            user_approved=False,
                        )
                    except Exception:
                        pass

            # Append the tool_results as a user turn (Bedrock convention).
            self.messages.append({"role": "user", "content": tool_results})

        else:  # for-loop fell through without break
            stop_reason = "max_turns"
            output_fn(f"[Max turns reached: {self.max_turns}]")

        return QueryResult(
            text=last_text,
            messages=list(self.messages),
            stop_reason=stop_reason or "end_turn",
            turns_used=turns_used,
            budget_used=self.budget.used(),
        )

    # ------------------------------------------------------------
    # Internal: assemble assistant turn content from a Bedrock Response
    # ------------------------------------------------------------

    @staticmethod
    def _build_assistant_content(response: Any) -> List[Dict[str, Any]]:
        """Construct a Bedrock-shaped assistant content list from a Response.

        Order: thinking blocks (if any) ƒ?T'+' text ƒ?T'+' tool_use. The thinking
        block is preserved so the next turn's API call carries it back to
        the model (Bedrock requires this for extended thinking continuity).
        """
        blocks: List[Dict[str, Any]] = []
        thinking = getattr(response, "thinking", "") or ""
        if thinking:
            blocks.append({"type": "thinking", "thinking": thinking})
        if response.text:
            blocks.append({"type": "text", "text": response.text})
        for call in response.tool_calls:
            blocks.append({
                "type": "tool_use",
                "id": call.id,
                "name": call.name,
                "input": call.input,
            })
        return blocks

    # ------------------------------------------------------------
    # Internal: deferred-tools system reminder injection
    # ------------------------------------------------------------

    @staticmethod
    def _inject_deferred_reminder(
        messages: List[Dict[str, Any]],
        deferred_names: List[str],
    ) -> List[Dict[str, Any]]:
        """Append a `<system-reminder>` block listing deferred tool names so
        the model knows what's available via tool_search.

        The reminder is injected as a transient text block on the trailing
        user turn ƒ?T'?" it does not mutate `self.messages`, so it does not leak
        into subsequent turns once the model has loaded the schemas it needs.
        """
        if not deferred_names:
            return messages
        reminder = (
            "<system-reminder>\n"
            "The following deferred tools are available via tool_search. Their schemas "
            "are NOT loaded ƒ?T'?" calling them directly will fail. Use tool_search with "
            "query \"select:<name>[,<name>...]\" to load tool schemas before calling them:\n"
            + "\n".join(sorted(deferred_names))
            + "\n</system-reminder>"
        )
        # Transient append: copy the trailing user message and add the reminder
        # as an extra text block. If the trailing turn is not user-role, we
        # append a fresh user message ƒ?T'?" but this should never happen because
        # the loop only invokes Bedrock right after a user turn or tool_results.
        out = list(messages)
        if not out or out[-1].get("role") != "user":
            out.append({"role": "user", "content": [{"type": "text", "text": reminder}]})
            return out
        last = dict(out[-1])
        content = last.get("content")
        if isinstance(content, str):
            last["content"] = [
                {"type": "text", "text": content},
                {"type": "text", "text": reminder},
            ]
        elif isinstance(content, list):
            last["content"] = list(content) + [{"type": "text", "text": reminder}]
        else:
            last["content"] = [{"type": "text", "text": reminder}]
        out[-1] = last
        return out


# ============================================================
# Single-turn helper for unit tests
# ============================================================

def run_one_turn(
    client: Any,
    messages: List[Dict[str, Any]],
    system_prompt: str,
    tools: List[Any],
    max_tokens: int = 4096,
    temperature: float = 0.0,
    thinking_enabled: bool = False,
    thinking_budget: int = 4096,
) -> Any:
    """Run a single Bedrock invocation with Phase 7 deferral applied.

    Returns the raw `Response` object. Tests use this to assert wiring without
    spinning up the full multi-turn loop.
    """
    from tools.registry import apply_tool_search_deferral

    visible_tools, _deferred = apply_tool_search_deferral(tools, enabled=True)
    return client.chat(
        messages=messages,
        system=system_prompt,
        tools=_build_tools_api_payload(visible_tools),
        max_tokens=max_tokens,
        temperature=temperature,
        thinking_enabled=thinking_enabled,
        thinking_budget=thinking_budget,
    )
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 3370ms:
"""Block A ƒ?T'?" Compactor + auto-compact circuit breaker + Runnable cache_edits.

v5 port of v4's `Compactor` class (compact_v4/MAIN/agent/sagemaker_agent.py
lines 186-635, ~449 LOC). Adapted for v5's nested-package layout. Plus:
  - Auto-compact circuit breaker (Hermes-style cooldown)
  - Runnable cache_edits adaptation (cache_control on prompt sections ƒ?T'?"
    Bedrock equivalent of the Anthropic-direct cache_edits param)
  - B-2 countTokensViaHaikuFallback (deferred from Block B per ADR-021)
  - B+5 recursive advisor sub-cost accounting (deferred from Block B+
    per ADR-022 ƒ?T'?" auxiliary compaction-summary model)

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
    False ƒ?T'?" caller must continue without re-compacting. Hermes
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
        a clear log message. Session cap checked FIRST ƒ?T'?" once exhausted,
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
        """Mark a compact attempt ƒ?T'?" caller calls this after a successful
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
        check before either records ƒ?T'?" this closes the TOCTOU window
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
      ƒ?T'?" this is the B+5 recursive advisor sub-cost accounting that
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
        # Build tool_use_id ƒ?T'+' tool_name map so we can skip protected tools.
        for msg in pruned:
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        tool_name_map[item.get("id", "")] = item.get("name", "")

        # Walk most-recent ƒ?T'+' oldest; protect the last PROTECT_TOKENS worth.
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
        # Codex Block-A iter-1 finding #2 (MEDIUM) lock: v4 invariant ƒ?T'?"
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
    # Auxiliary-model routing (B+5 ƒ?T'?" recursive advisor sub-cost)
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
            "available ƒ?T'?" do NOT attempt any tool calls. Be concise but "
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
                "[END SUMMARY ƒ?T'?" Continuing from here]"
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
        """End-to-end: prune ƒ?T'+' summarize ƒ?T'+' compact. Single entry point."""
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
# Runnable cache_edits ƒ?T'?" Bedrock cache_control adaptation
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
    place to set this ƒ?T'?" the summary block becomes the new cache prefix.

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
# B-2 ƒ?T'?" countTokensViaHaikuFallback (deferred from Block B per ADR-021)
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
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

codex
The test file confirms a mismatch between the docstring and the actual run: the implementation is one `agent.run(...)` call with no tools, not the two-turn compaction scenario the header describes. I’'?Tm narrowing the engine path now to see exactly when auto-compact is evaluated.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "Compactor|AUTO_COMPACT|should_compact|compact" compact_v5/MAIN/agent/core/query_engine.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"TOKENS\\.add|session_input|session_cost|is_over_budget|cost\" compact_v5/MAIN/agent -g \"*.py\"" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"class Agent|def run\\(\" compact_v5/MAIN/agent/agent.py compact_v5/MAIN/agent -g \"agent.py\"" in D:\Github\sagemaker-coding-agent
 succeeded in 2839ms:
24:- Microcompact / context_collapse ’'?" Phase 11 UX (PS Issue #4 widget surface).
25:- 2-stage smart compaction (prune + LLM summary) ’'?" Phase 11.
30:  doesn't reset on compact (no compact in Phase 8).
619:            # Block A ’'?" auto-compact gate. Per-turn check: if the
621:            # circuit breaker allows another attempt, run Compactor.
623:                from core.compactor import Compactor, AUTO_COMPACT
626:                if Compactor.should_compact(self.messages, _max_ctx):
627:                    _ok, _why = AUTO_COMPACT.try_attempt()
629:                        _result = Compactor.run(self.client, self.messages, _max_ctx)
632:                                f"[auto-compact] saved "
640:                        output_fn(f"[auto-compact skipped: {_why}]")
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 2860ms:
compact_v5/MAIN/agent\agent.py:166:        # per-turn output cost) would have no effect because QueryEngine.run
compact_v5/MAIN/agent\agent.py:192:        wants a fresh conversation but still respects the cost ceiling
compact_v5/MAIN/agent\commands.py:11:    /skill apply, /skill reject, /revert, /cost, /context, /status,
compact_v5/MAIN/agent\commands.py:43:  /cost              ’'?" session cost summary
compact_v5/MAIN/agent\commands.py:282:# /cost ’'?" session cost summary
compact_v5/MAIN/agent\commands.py:285:def cmd_cost(args: str, ctx: Optional[Dict[str, Any]] = None) -> CommandResult:
compact_v5/MAIN/agent\commands.py:288:    cost = TOKENS.get_cost()
compact_v5/MAIN/agent\commands.py:291:    limit = getattr(CONFIG, "session_cost_limit", 0.0)
compact_v5/MAIN/agent\commands.py:297:        f"Session cost: {cost}",
compact_v5/MAIN/agent\commands.py:318:            f"(based on last response usage). Use /cost for full session view."
compact_v5/MAIN/agent\commands.py:600:    ("/cost", cmd_cost),
compact_v5/MAIN/agent\core\budget_continuation.py:14:  session_cost >= session_cost_limit, halt. Runnable's tokenBudget had no
compact_v5/MAIN/agent\core\budget_continuation.py:15:  cost-cap interaction; v5 adds it because TOKENS.session_cost is a 1st-class
compact_v5/MAIN/agent\core\budget_continuation.py:25:diminishing returns kick in OR cost-cap is hit.
compact_v5/MAIN/agent\core\budget_continuation.py:72:    reason: str = ""  # "complete" | "diminishing" | "above_threshold" | "cost_cap" | "no_budget" | "subagent"
compact_v5/MAIN/agent\core\budget_continuation.py:87:    session_cost: float = 0.0,
compact_v5/MAIN/agent\core\budget_continuation.py:88:    session_cost_limit: float = 0.0,
compact_v5/MAIN/agent\core\budget_continuation.py:92:    Cost-cap halts BEFORE the under-90% check so a near-budget cost can't be
compact_v5/MAIN/agent\core\budget_continuation.py:104:    if session_cost_limit > 0 and session_cost >= session_cost_limit:
compact_v5/MAIN/agent\core\budget_continuation.py:111:                "cost": session_cost,
compact_v5/MAIN/agent\core\budget_continuation.py:112:                "cost_limit": session_cost_limit,
compact_v5/MAIN/agent\core\budget_continuation.py:115:            reason="cost_cap",
compact_v5/MAIN/agent\core\budget.py:11:max_turns times, blowing the cost ceiling. Insurance/audit values
compact_v5/MAIN/agent\core\budget.py:12:predictable cost ceilings per user request. Counter is shared across
compact_v5/MAIN/agent\core\cache.py:168:    invalidated. This is the single most-debugged class of cost-spike
compact_v5/MAIN/agent\core\compactor.py:9:  - B+5 recursive advisor sub-cost accounting (deferred from Block B+
compact_v5/MAIN/agent\core\compactor.py:151:      ’'?" this is the B+5 recursive advisor sub-cost accounting that
compact_v5/MAIN/agent\core\compactor.py:293:    # Auxiliary-model routing (B+5 ’'?" recursive advisor sub-cost)
compact_v5/MAIN/agent\core\compactor.py:302:        don't pay main-model rates. Per ADR-022 / B+5: TOKENS.add()
compact_v5/MAIN/agent\core\compactor.py:303:        with `agent_kind="advisor"` so the auxiliary cost is attributed
compact_v5/MAIN/agent\core\compactor.py:304:        separately in /cost output.
compact_v5/MAIN/agent\core\compactor.py:344:        - Attribute advisor tokens via TOKENS.add(agent_kind='advisor').
compact_v5/MAIN/agent\core\compactor.py:389:                    # B+5 (ADR-022 remap): attribute advisor cost separately.
compact_v5/MAIN/agent\core\compactor.py:395:                    TOKENS.add(
compact_v5/MAIN/agent\runtime\config.py:34:    # Cost note: Sonnet 4.5 is ~10x the per-token cost of Haiku 4.5, but the
compact_v5/MAIN/agent\runtime\config.py:36:    # (Sonnet), so caching activates earlier and offsets some of the cost on
compact_v5/MAIN/agent\runtime\config.py:37:    # multi-turn sessions. To switch back to Haiku for cost-sensitive runs,
compact_v5/MAIN/agent\runtime\config.py:90:    session_cost_limit: float = 0.0  # 0 = no limit. Warns at 80%, stops at 100%.
compact_v5/MAIN/agent\runtime\config.py:135:    # budget AND not diminishing-returns AND session_cost < session_cost_limit
compact_v5/MAIN/agent\runtime\config.py:228:        "aws_bedrock_only": bool, "disable_local_traces": bool, "session_cost_limit": float,
compact_v5/MAIN/agent\runtime\cleanup_registry.py:10:Uses: TokenTracker cost-flush at exit (B+7); SnapshotManager log flush
compact_v5/MAIN/agent\core\query_engine.py:233:        # Block B: per-agent attribution key for TOKENS.add(). "parent" by
compact_v5/MAIN/agent\core\query_engine.py:302:        # Block B+ Codex finding #1 (HIGH) lock: reset the per-run cost
compact_v5/MAIN/agent\core\query_engine.py:554:                _TOKENS.add(
compact_v5/MAIN/agent\core\query_engine.py:592:                # Block B+ (PORT_LOG #052): per-turn cost-vs-budget runtime
compact_v5/MAIN/agent\core\query_engine.py:594:                #   `[Cost ${session_cost} passed budget ${limit} ’'?" continuing.]`
compact_v5/MAIN/agent\core\query_engine.py:599:                limit = getattr(_CFG, "session_cost_limit", 0.0)
compact_v5/MAIN/agent\core\query_engine.py:602:                if limit > 0 and _TOKENS.session_cost >= limit:
compact_v5/MAIN/agent\core\query_engine.py:605:                            f"[Cost ${_TOKENS.session_cost:.4f} passed "
compact_v5/MAIN/agent\core\query_engine.py:665:                            _sc = float(getattr(_TOKENS_F2, "session_cost", 0.0))
compact_v5/MAIN/agent\core\query_engine.py:668:                        _scl = float(getattr(_CFG_F2, "session_cost_limit", 0.0))
compact_v5/MAIN/agent\core\query_engine.py:674:                            session_cost=_sc,
compact_v5/MAIN/agent\core\query_engine.py:675:                            session_cost_limit=_scl,
compact_v5/MAIN/agent\core\query_engine.py:696:                            if _ce is not None or _reason in {"cost_cap", "diminishing", "above_threshold"}:
compact_v5/MAIN/agent\core\query_engine.py:718:                    # cost-runtime warning pattern at [Cost ...] above.
compact_v5/MAIN/agent\runtime\env_validation.py:5:cost_limit, retention_days, etc.) so config loaders never crash on
compact_v5/MAIN/agent\runtime\tokens.py:5:- per-agent input/output/cost attribution (B-11 + Plan v3 ABlock B)
compact_v5/MAIN/agent\runtime\tokens.py:74:# list price for Haiku 4.5 and Sonnet 4.5. The local cost tracker MUST
compact_v5/MAIN/agent\runtime\tokens.py:306:    """Thread-safe tracker for API token usage, cost, and cache hits per session.
compact_v5/MAIN/agent\runtime\tokens.py:309:    sub-agent token costs can be reported separately while still rolling
compact_v5/MAIN/agent\runtime\tokens.py:310:    up to the same `session_cost` total. Per Plan v3 ABlock B + B-11.
compact_v5/MAIN/agent\runtime\tokens.py:346:        self.session_input = 0
compact_v5/MAIN/agent\runtime\tokens.py:354:        self.session_cost = 0.0
compact_v5/MAIN/agent\runtime\tokens.py:355:        self.last_cost = 0.0
compact_v5/MAIN/agent\runtime\tokens.py:363:        self.parent_cost = 0.0
compact_v5/MAIN/agent\runtime\tokens.py:366:        self.subagent_cost: Dict[str, float] = {}
compact_v5/MAIN/agent\runtime\tokens.py:395:            self.session_input += input_tokens
compact_v5/MAIN/agent\runtime\tokens.py:397:            self.session_total = self.session_input + self.session_output
compact_v5/MAIN/agent\runtime\tokens.py:409:            cost = 0.0
compact_v5/MAIN/agent\runtime\tokens.py:413:                # this, local cost tracker undercounts AWS billing by 10%.
compact_v5/MAIN/agent\runtime\tokens.py:418:                cost = (
compact_v5/MAIN/agent\runtime\tokens.py:424:                self.session_cost += cost
compact_v5/MAIN/agent\runtime\tokens.py:425:                self.last_cost = cost
compact_v5/MAIN/agent\runtime\tokens.py:432:                        f"TokenTracker: no pricing for model '{mid}' ’'?" cost will show as $0. "
compact_v5/MAIN/agent\runtime\tokens.py:435:                self.last_cost = 0.0
compact_v5/MAIN/agent\runtime\tokens.py:441:                self.parent_cost += cost
compact_v5/MAIN/agent\runtime\tokens.py:449:                self.subagent_cost[agent_kind] = (
compact_v5/MAIN/agent\runtime\tokens.py:450:                    self.subagent_cost.get(agent_kind, 0.0) + cost
compact_v5/MAIN/agent\runtime\tokens.py:454:            limit = self._config.session_cost_limit
compact_v5/MAIN/agent\runtime\tokens.py:455:            if limit > 0 and self.session_cost > 0:
compact_v5/MAIN/agent\runtime\tokens.py:456:                pct = self.session_cost / limit
compact_v5/MAIN/agent\runtime\tokens.py:460:                        f"Session cost ${self.session_cost:.4f} reached limit ${limit:.2f}."
compact_v5/MAIN/agent\runtime\tokens.py:465:                        f"Session cost ${self.session_cost:.4f} is {pct:.0%} of ${limit:.2f} limit."
compact_v5/MAIN/agent\runtime\tokens.py:472:    def is_over_budget(self) -> bool:
compact_v5/MAIN/agent\runtime\tokens.py:473:        limit = self._config.session_cost_limit
compact_v5/MAIN/agent\runtime\tokens.py:474:        return limit > 0 and self.session_cost >= limit
compact_v5/MAIN/agent\runtime\tokens.py:481:            f"In:{self.session_input:,} Out:{self.session_output:,} "
compact_v5/MAIN/agent\runtime\tokens.py:493:    def get_cost(self) -> str:
compact_v5/MAIN/agent\runtime\tokens.py:494:        cost_str = (
compact_v5/MAIN/agent\runtime\tokens.py:495:            f"${self.session_cost:.4f}"
compact_v5/MAIN/agent\runtime\tokens.py:496:            if self.session_cost < 0.01
compact_v5/MAIN/agent\runtime\tokens.py:497:            else f"${self.session_cost:.2f}"
compact_v5/MAIN/agent\runtime\tokens.py:499:        if self.session_cache_read > 0 and self.session_input > 0:
compact_v5/MAIN/agent\runtime\tokens.py:500:            cache_pct = min(100, (self.session_cache_read / self.session_input) * 100)
compact_v5/MAIN/agent\runtime\tokens.py:502:            cost_str += f" (cache {cache_pct:.0f}% | saved ~${savings:.4f})"
compact_v5/MAIN/agent\runtime\tokens.py:503:        return cost_str
compact_v5/MAIN/agent\runtime\tokens.py:507:            "session_input": self.session_input,
compact_v5/MAIN/agent\runtime\tokens.py:515:            "session_cost_usd": round(self.session_cost, 6),
compact_v5/MAIN/agent\runtime\tokens.py:516:            "last_cost_usd": round(self.last_cost, 6),
compact_v5/MAIN/agent\runtime\tokens.py:519:            "parent_cost_usd": round(self.parent_cost, 6),
compact_v5/MAIN/agent\runtime\tokens.py:522:            "subagent_cost_usd": {k: round(v, 6) for k, v in self.subagent_cost.items()},
compact_v5/MAIN/agent\runtime\tokens.py:528:        Used by Block B+ SessionManager `/resume` to rehydrate cost
compact_v5/MAIN/agent\runtime\tokens.py:529:        across sessions (Runnable cost-tracker.ts:87-175 / R11 N8).
compact_v5/MAIN/agent\runtime\tokens.py:532:            self.session_input = int(stats.get("session_input", 0))
compact_v5/MAIN/agent\runtime\tokens.py:534:            self.session_total = self.session_input + self.session_output
compact_v5/MAIN/agent\runtime\tokens.py:540:            self.session_cost = float(stats.get("session_cost_usd", 0.0))
compact_v5/MAIN/agent\runtime\tokens.py:541:            self.last_cost = float(stats.get("last_cost_usd", 0.0))
compact_v5/MAIN/agent\runtime\tokens.py:544:            self.parent_cost = float(stats.get("parent_cost_usd", 0.0))
compact_v5/MAIN/agent\runtime\tokens.py:547:            self.subagent_cost = {
compact_v5/MAIN/agent\runtime\tokens.py:548:                k: float(v) for k, v in stats.get("subagent_cost_usd", {}).items()
compact_v5/MAIN/agent\runtime\tokens.py:565:            return self.session_input  # cold start fallback
compact_v5/MAIN/agent\runtime\tokens.py:593:# Block B+ (PORT_LOG #054): atexit cost-flush via cleanup_registry.
compact_v5/MAIN/agent\runtime\tokens.py:594:# Per Runnable costHook.ts:6-22 (R11 N14). On normal exit / SIGINT /
compact_v5/MAIN/agent\runtime\tokens.py:595:# SIGTERM, log the final session cost so operators can audit
compact_v5/MAIN/agent\runtime\tokens.py:597:def _flush_cost_on_exit() -> None:
compact_v5/MAIN/agent\runtime\tokens.py:598:    if TOKENS.session_cost > 0:
compact_v5/MAIN/agent\runtime\tokens.py:600:            f"session-final cost: {TOKENS.get_cost()} "
compact_v5/MAIN/agent\runtime\tokens.py:602:            f"in={TOKENS.session_input:,} out={TOKENS.session_output:,})"
compact_v5/MAIN/agent\runtime\tokens.py:608:    _register_cleanup(_flush_cost_on_exit)
compact_v5/MAIN/agent\ui\widgets.py:81:                # Color cue for cost ceiling ’'?" red when ’'%A? 90% consumed.
compact_v5/MAIN/agent\ui\chat_ui.py:307:        # runtime turn ceiling / cost-ceiling guards.
compact_v5/MAIN/agent\skills\manager.py:733:            cost = _estimate_tokens(name + ", ")
compact_v5/MAIN/agent\skills\manager.py:734:            if used + cost + hint_reserve > budget_tokens:
compact_v5/MAIN/agent\skills\manager.py:738:            used += cost
compact_v5/MAIN/agent\subagent\agent_types.py:14:  shared IterationBudget, which is the cost-cap; max_turns is the
compact_v5/MAIN/agent\subagent\agent_types.py:36:# only needs the answer, not surrounding cleanup. Keeps token cost
compact_v5/MAIN/agent\subagent\spawn.py:75:    Block B: `agent_type` is forwarded as `agent_kind` so TOKENS.add()
compact_v5/MAIN/agent\subagent\spawn.py:76:    attributes the child's input/output/cost to the right per-agent
compact_v5/MAIN/agent\tests\integration\test_block_b.py:53:    TOKENS.add({"input_tokens": 100, "output_tokens": 50}, model_id="test-model")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:54:    TOKENS.add({"input_tokens": 200, "output_tokens": 75}, model_id="test-model")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:56:    assert TOKENS.session_input == 300
compact_v5/MAIN/agent\tests\integration\test_block_b.py:150:    TOKENS.add({"input_tokens": 100, "output_tokens": 50}, model_id="test-model", agent_kind="parent")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:151:    TOKENS.add({"input_tokens": 80, "output_tokens": 40}, model_id="test-model", agent_kind="build")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:152:    TOKENS.add({"input_tokens": 60, "output_tokens": 30}, model_id="test-model", agent_kind="explore")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:153:    TOKENS.add({"input_tokens": 50, "output_tokens": 25}, model_id="test-model", agent_kind="parent")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:163:    assert TOKENS.session_input == 290
compact_v5/MAIN/agent\tests\integration\test_block_b.py:165:    # Parent + sum of sub-agent costs == session total.
compact_v5/MAIN/agent\tests\integration\test_block_b.py:166:    parent_cost = TOKENS.parent_cost
compact_v5/MAIN/agent\tests\integration\test_block_b.py:167:    sub_cost_total = sum(TOKENS.subagent_cost.values())
compact_v5/MAIN/agent\tests\integration\test_block_b.py:168:    assert abs(TOKENS.session_cost - (parent_cost + sub_cost_total)) < 1e-6
compact_v5/MAIN/agent\tests\integration\test_block_b.py:206:    TOKENS.add({"input_tokens": 100, "output_tokens": 30}, model_id="test-model")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:207:    TOKENS.add({"input_tokens": 120, "output_tokens": 35}, model_id="test-model")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:208:    TOKENS.add({"input_tokens": 140, "output_tokens": 40}, model_id="test-model")
compact_v5/MAIN/agent\tests\integration\test_block_b.py:211:    assert TOKENS.session_input == 360
compact_v5/MAIN/agent\tests\integration\test_block_b.py:240:    This test costs ~$0.005 worth of Bedrock CountTokens API calls when
compact_v5/MAIN/agent\tests\integration\test_block_b.py:399:    TOKENS.add({
compact_v5/MAIN/agent\tests\integration\test_block_b.py:410:# Wiring lock ’'?" TOKENS.add fires on QueryEngine response (mock client)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:415:    user can see /cost reflect work done. Wired in core/query_engine.py
compact_v5/MAIN/agent\tests\integration\test_block_b.py:427:    assert TOKENS.session_input + TOKENS.session_output > 0
compact_v5/MAIN/agent\tests\integration\test_block_b.py:438:    default-config prefix; without stripping, default-path TOKENS.add
compact_v5/MAIN/agent\tests\integration\test_block_b.py:460:def test_au_prefixed_model_records_real_cost():
compact_v5/MAIN/agent\tests\integration\test_block_b.py:461:    """Lock test for Codex iter-1 finding #1 (HIGH): TOKENS.add against
compact_v5/MAIN/agent\tests\integration\test_block_b.py:462:    `au.`-prefixed model id must record a non-zero cost (was $0 before fix).
compact_v5/MAIN/agent\tests\integration\test_block_b.py:466:    `get_geo_multiplier(raw_mid) = 1.10` so the recorded cost is now
compact_v5/MAIN/agent\tests\integration\test_block_b.py:473:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b.py:482:    assert TOKENS.session_cost > 0
compact_v5/MAIN/agent\tests\integration\test_block_b.py:483:    assert abs(TOKENS.session_cost - 0.01155) < 1e-6
compact_v5/MAIN/agent\tests\integration\test_block_b.py:598:    audit event so real-AWS runs can be reviewed per-turn for cost, cache,
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:1:"""Block B+ ’'?" SessionManager + cost-limit + AGENT_STATUS auto-load + FileCache.
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:7:  T1 test_session_save_load_preserves_cost         save at $2.09 ’'+' load ’'+' TOKENS.session_cost == 2.09 (PS#5)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:8:  T1 test_session_cost_limit_warns_at_100pct       v5 = warn-and-continue (per user 2026-05-03 Plan v3 update)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:11:  T2 test_subagent_token_attribution               TOKENS.parent_input_tokens > 0 AND subagent["build"] > 0 AND session_cost == sum
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:88:# T1 ’'?" Save / load preserves session cost (PS#5)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:91:def test_session_save_load_preserves_cost(tmp_path):
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:92:    """PS#5: session cost must persist across /save ’'+' /resume.
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:97:    and asserting the singleton ends up at the recorded cost.
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:103:    s = sm.create(title="cost-restore")
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:105:    # Simulate a session of work that accumulates cost.
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:106:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:110:    expected_cost = TOKENS.session_cost
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:111:    assert expected_cost > 0
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:119:    assert TOKENS.session_cost == 0.0
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:124:    assert abs(TOKENS.session_cost - expected_cost) < 1e-6
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:128:# T1 ’'?" session_cost_limit warn-and-continue (per user 2026-05-03)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:131:def test_session_cost_limit_warns_at_100pct(monkeypatch, caplog):
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:142:    monkeypatch.setattr(CONFIG, "session_cost_limit", 0.005)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:146:        # Push session_cost above the limit.
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:147:        TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:152:    # is_over_budget reports True, but the tracker did NOT raise; the
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:154:    assert TOKENS.is_over_budget()
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:156:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:161:        "v5 contract: TOKENS.add must NOT raise / refuse after over-budget; "
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:301:    each goes to its own bucket. session_cost == sum of buckets."""
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:305:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:311:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:321:    assert TOKENS.parent_cost > 0
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:322:    assert TOKENS.subagent_cost["build"] > 0
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:325:        TOKENS.session_cost
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:326:        - (TOKENS.parent_cost + sum(TOKENS.subagent_cost.values()))
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:337:    share one cost view."""
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:348:    cost_after_a1 = TOKENS.session_cost
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:350:    cost_after_a2 = TOKENS.session_cost
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:353:    assert cost_after_a2 >= cost_after_a1
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:437:def test_cost_warning_resets_each_run(monkeypatch):
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:442:    the session even when costs keep growing."""
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:448:    monkeypatch.setattr(CONFIG, "session_cost_limit", 0.0001)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:454:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:474:def test_cost_warning_fires_on_exact_100_percent(monkeypatch):
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:481:    # Force session_cost == session_cost_limit exactly.
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:482:    monkeypatch.setattr(CONFIG, "session_cost_limit", 0.001)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:487:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:491:    assert abs(TOKENS.session_cost - 0.001) < 1e-9
compact_v5/MAIN/agent\tests\integration\test_agent_max_tokens_propagation.py:6:output cost) would have no effect because QueryEngine.run defaults to
compact_v5/MAIN/agent\tests\integration\test_block_d.py:11:  - Chat-UI integration: ConsoleChatUI.send("/cost") routes to dispatcher.
compact_v5/MAIN/agent\tests\integration\test_block_d.py:50:        "/revert", "/cost", "/context", "/status",
compact_v5/MAIN/agent\tests\integration\test_block_d.py:77:    assert is_command("/cost")
compact_v5/MAIN/agent\tests\integration\test_block_d.py:135:# T1 ’'?" /cost dispatches to TokenTracker
compact_v5/MAIN/agent\tests\integration\test_block_d.py:138:def test_cost_command_includes_session_summary():
compact_v5/MAIN/agent\tests\integration\test_block_d.py:143:    TOKENS.add(
compact_v5/MAIN/agent\tests\integration\test_block_d.py:147:    cr = dispatch_command("/cost")
compact_v5/MAIN/agent\tests\integration\test_block_d.py:149:    assert "Session cost:" in cr.text
compact_v5/MAIN/agent\tests\integration\test_block_d.py:316:    """ConsoleChatUI.send('/cost') must hit the dispatcher and NOT
compact_v5/MAIN/agent\tests\integration\test_block_d.py:334:    out = ui.send("/cost")
compact_v5/MAIN/agent\tests\integration\test_block_d.py:335:    assert "Session cost:" in out
compact_v5/MAIN/agent\tests\integration\test_block_d.py:336:    assert not invoked["agent_run"], "/cost must NOT invoke agent.run()"
compact_v5/MAIN/agent\tests\integration\test_block_a.py:13:  - B+5 advisor sub-cost attribution via TOKENS.add(agent_kind="advisor").
compact_v5/MAIN/agent\tests\integration\test_block_a.py:289:# B+5 ’'?" advisor sub-cost attribution
compact_v5/MAIN/agent\tests\integration\test_block_a.py:292:def test_advisor_cost_attributed_when_aux_model_set(monkeypatch):
compact_v5/MAIN/agent\tests\integration\test_block_a.py:294:    used, summary tokens go into TOKENS.subagent_cost['advisor'].
compact_v5/MAIN/agent\tests\integration\test_block_a.py:323:    # Add some pricing so cost is non-zero (hitchk test pricing fallback)
compact_v5/MAIN/agent\tests\integration\test_block_a.py:328:    # Advisor bucket present (cost may be 0 if aux-model has no pricing,
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:9:- test_f2_respects_cost_cap
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:12:  ("F2 auto-continuation respects cost cap + opt-in"):
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:73:def test_check_respects_cost_cap_even_under_90pct():
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:74:    """session_cost >= session_cost_limit ’'+' halt even if iter_used < 90%."""
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:86:        session_cost=2.50,
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:87:        session_cost_limit=2.00,  # already over cap
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:90:    assert decision.reason == "cost_cap"
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:91:    assert decision.completion_event["cost"] == 2.50
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:92:    assert decision.completion_event["cost_limit"] == 2.00
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:93:    # Tracker NOT advanced when cost-capped
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:201:    """F2 reads TOKENS.session_cost; reset before each test for determinism."""
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:282:def test_f2_respects_cost_cap(reset_tokens):
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:283:    """TEST_DESIGN row 3: even if iter_used < 90%, if session_cost >=
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:284:    session_cost_limit ’'+' halt without nudge."""
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:292:    _prev_limit = CONFIG.session_cost_limit
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:294:    CONFIG.session_cost_limit = 1.00
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:296:        # Inflate session_cost above the limit BEFORE the run.
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:297:        TOKENS.session_cost = 1.50
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:316:        CONFIG.session_cost_limit = _prev_limit
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:425:    cost-cap, diminishing, above-threshold), the engine must surface its
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:438:    _prev_limit = CONFIG.session_cost_limit
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:440:    CONFIG.session_cost_limit = 1.00
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:443:        TOKENS.session_cost = 1.50  # over cap ’'+' StopDecision reason="cost_cap"
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:446:            ("text", "Should halt on cost-cap before completion."),
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:457:        # session_id, with reason=cost_cap.
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:466:        assert f2_stops[0]["parameters"]["reason"] == "cost_cap"
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:468:        assert "1.5" in f2_stops[0]["result_summary"] or "cost_cap" in f2_stops[0]["result_summary"]
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:471:        CONFIG.session_cost_limit = _prev_limit
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:569:def test_f2_completion_event_includes_pct_for_cost_cap(reset_tokens):
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:570:    """Codex iter-2 finding #2 lock: cost-cap StopDecision.completion_event
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:586:        session_cost=2.50,
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:587:        session_cost_limit=2.00,
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:590:    assert decision.reason == "cost_cap"
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:593:    assert "pct" in ce, "cost-cap completion_event must include pct"
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:595:    assert ce["cost"] == 2.50
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:72:      - No max_turns / cost_cap breach.
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:73:      - cost ’'% $0.50.
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:83:    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:90:        CONFIG.session_cost_limit = _R2_COST_CAP_USD
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:102:        def _hard_cost_halt():
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:103:            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:104:                TOKENS.session_cost >= _R2_COST_CAP_USD
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:110:            on_stop_check=_hard_cost_halt,
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:121:        cost_used = TOKENS.session_cost
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:122:        tokens_in = TOKENS.session_input
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:137:            "cost_usd": round(cost_used, 4),
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:158:        assert cost_used <= _R2_COST_CAP_USD, (
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:159:            f"R2 cost ${cost_used:.4f} exceeded cap ${_R2_COST_CAP_USD}. "
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:172:        if saved_cost_limit is not None:
compact_v5/MAIN/agent\tests\r_tier\test_r2_compact.py:173:            CONFIG.session_cost_limit = saved_cost_limit
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:13:  - session_cost_limit enforcement
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:89:      - Total cost <= R1 cap ($1.00).
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:107:    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:114:        CONFIG.session_cost_limit = _R1_COST_CAP_USD
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:116:        # Codex Phase A iter-1 cost-risk fix: cap per-turn output.
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:124:        # (Workspace + python AST + bash allowlist + cost cap still enforce
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:134:        # Agent + run with HARD cost halt
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:143:        # Codex Phase A iter-1 cost-risk fix: v5's session_cost_limit is a
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:148:        def _hard_cost_halt():
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:149:            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:150:                TOKENS.session_cost >= _R1_COST_CAP_USD
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:158:            on_stop_check=_hard_cost_halt,
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:170:        cost_used = TOKENS.session_cost
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:171:        tokens_in = TOKENS.session_input
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:186:            "cost_usd": round(cost_used, 4),
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:248:        # Assert: cost within R1 cap.
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:249:        assert cost_used <= _R1_COST_CAP_USD, (
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:250:            f"R1 cost ${cost_used:.4f} exceeded cap ${_R1_COST_CAP_USD}. "
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:257:        if saved_cost_limit is not None:
compact_v5/MAIN/agent\tests\r_tier\test_r1_dashboard.py:258:            CONFIG.session_cost_limit = saved_cost_limit
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:68:    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:77:        CONFIG.session_cost_limit = _R17_COST_CAP_USD
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:91:        def _hard_cost_halt():
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:92:            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:93:                TOKENS.session_cost >= _R17_COST_CAP_USD
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:101:            on_stop_check=_hard_cost_halt,
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:125:        cost_used = TOKENS.session_cost
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:126:        tokens_in = TOKENS.session_input
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:140:            "cost_usd": round(cost_used, 4),
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:162:        assert cost_used <= _R17_COST_CAP_USD, (
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:163:            f"R17 cost ${cost_used:.4f} exceeded cap ${_R17_COST_CAP_USD}."
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:169:        if saved_cost_limit is not None:
compact_v5/MAIN/agent\tests\r_tier\test_r17_thinking_visibility.py:170:            CONFIG.session_cost_limit = saved_cost_limit
compact_v5/MAIN/agent\tests\unit\test_tool_search.py:268:    cost. The full ’'%A?3000-token target lands as Phases 9-10 add more tools."""
compact_v5/MAIN/agent\tests\unit\test_tool_search.py:276:    def schemas_token_cost(tools_list):
compact_v5/MAIN/agent\tests\unit\test_tool_search.py:282:    full_cost = schemas_token_cost(full)
compact_v5/MAIN/agent\tests\unit\test_tool_search.py:283:    visible_cost = schemas_token_cost(visible)
compact_v5/MAIN/agent\tests\unit\test_tool_search.py:284:    savings = full_cost - visible_cost
compact_v5/MAIN/agent\tests\integration\test_block_j_ship_gate.py:20:Total Block J AWS cost when RUN_REAL_BEDROCK=1: ~$0.02.
compact_v5/MAIN/agent\tests\integration\test_block_j_ship_gate.py:50:# T4 ’'?" Zip rebuild + extract + import (no AWS cost)
compact_v5/MAIN/agent\tests\integration\test_block_j_ship_gate.py:309:    cost more than Block J's $0.02 cap, AND auto-compaction is wired in
compact_v5/MAIN/agent\tests\integration\test_block_j_ship_gate.py:316:      - costs ~$0.01.
compact_v5/MAIN/agent\tools\skill.py:34:Skill auto-trigger is OFF by default. Skills only load when a user runs `/skill activate <name>` (Phase 11 UX) or you call `skill activate <name>` explicitly. v4 made auto-trigger opt-in (`CONFIG.enable_skill_auto_trigger=True`) because silent skill injection bloated cost.
compact_v5/MAIN/agent\tools\task.py:35:Sub-agents run with a FRESH conversation but share the parent agent's iteration budget ’'?" they cannot collectively exceed the cost ceiling. Use a sub-agent when:
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:1:"""Lock test for R-tier R1 PHASE A iter-3 fix: cost tracker applies
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:5:path for Haiku 4.5) would undercount billed cost by 10% locally ’'?" letting
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:49:def test_token_cost_applies_geo_premium_for_au_profile():
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:65:        cost_global = t_global.session_cost
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:67:        # Geo tracker ’'?" same usage; should be 1.10x cost.
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:71:        cost_geo = t_geo.session_cost
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:73:        assert cost_global > 0, "global cost must be non-zero"
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:74:        assert cost_geo > 0, "geo cost must be non-zero"
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:75:        # Geo cost must be 1.10x global cost (+/- floating-point tolerance).
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:76:        ratio = cost_geo / cost_global
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:78:            f"expected ratio ~1.10; got {ratio:.6f} (global={cost_global}, geo={cost_geo})"
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:84:def test_token_cost_no_premium_for_global_profile():
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:91:    expected_input_cost = (1000 / 1000) * MODEL_COSTS[global_id]["input"]
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:92:    expected_output_cost = (1000 / 1000) * MODEL_COSTS[global_id]["output"]
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:93:    expected_total = expected_input_cost + expected_output_cost
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:101:        assert abs(t.session_cost - expected_total) < 1e-9, (
compact_v5/MAIN/agent\tests\integration\test_geo_inference_premium.py:102:            f"global cost expected {expected_total}, got {t.session_cost}"
compact_v5/MAIN/agent\tests\integration\test_block_n.py:138:        "Changing this affects Bedrock concurrency cost ’'?" review with care."
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:232:    """Side-channel _<test>_metrics.json populates outcome.cost_usd etc."""
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:240:            "cost_usd": 0.04, "wallclock_s": 12.3,
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:249:        "tokens_in": 5000, "tokens_out": 2000, "cost_usd": 0.04,
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:259:    assert out["cost_usd"] == 0.04
compact_v5/MAIN/agent\tests\integration\test_block_t.py:128:            {"month": "Jan", "sales": 100, "cost": 60},
compact_v5/MAIN/agent\tests\integration\test_block_t.py:129:            {"month": "Feb", "sales": 120, "cost": 70},
compact_v5/MAIN/agent\tests\integration\test_block_t.py:135:        "y_columns": ["sales", "cost"],
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:4:coverage, missing evidence files, and cost-cap drift before another AWS call
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:33:def test_r_tier_gate_matrix_is_complete_and_costed():
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:51:def test_r_tier_gate_detects_cost_cap_excess(tmp_path):
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:56:        json.dumps({"test": "R1", "call": 1, "cost_usd": 2.0}) + "\n",
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:60:    errors = gate.check_costs(tmp_path)
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:61:    assert any("R1 cost" in e for e in errors)
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:70:    assert gate.check_costs(tmp_path) == []
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:117:            "cost_usd": 0.01,
compact_v5/MAIN/agent\tests\integration\test_r_tier_gate.py:163:            "completed": True, "cost_usd": 0.01, "verdict": "GENUINE_PASS",
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 3167ms:
compact_v5/MAIN/agent/agent.py:60:class Agent:
compact_v5/MAIN/agent/agent.py:122:    def run(
compact_v5/MAIN/agent\agent.py:60:class Agent:
compact_v5/MAIN/agent\agent.py:122:    def run(
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/core/query_engine.py | Select-Object -Skip 530 -First 140' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/agent.py | Select-Object -Skip 100 -First 120' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/runtime/tokens.py | Select-Object -Skip 60 -First 110; Get-Content -Path compact_v5/MAIN/agent/runtime/tokens.py | Select-Object -Skip 380 -First 105' in D:\Github\sagemaker-coding-agent
 succeeded in 1938ms:
            except Exception as exc:  # noqa: BLE001 ƒ?T'?" classify and surface
                category, recovery, debug = ErrorClassifier.classify(exc)
                output_fn(f"[Bedrock {category}: {debug}]")
                if category == BedrockErrorCategory.CONTEXT_OVERFLOW:
                    stop_reason = "context_overflow"
                else:
                    stop_reason = "fatal_error"
                return QueryResult(
                    text=last_text,
                    messages=list(self.messages),
                    stop_reason=stop_reason,
                    turns_used=turns_used,
                    budget_used=self.budget.used(),
                    error=f"{category}: {debug}",
                )

            turns_used += 1

            # Block B (PORT_LOG #039+#040): record token usage + per-agent
            # attribution. "parent" or sub-agent type-string. Best-effort ƒ?T'?"
            # never break the agent loop if the singleton import fails.
            try:
                from runtime.tokens import TOKENS as _TOKENS
                _TOKENS.add(
                    response.usage or {},
                    model_id=getattr(self.client, "model_id", None),
                    agent_kind=self.agent_kind,
                )
                try:
                    from runtime.audit import AUDIT as _AUDIT_CHAT
                    _AUDIT_CHAT.log(
                        session_id=self.session_id,
                        action="chat_response",
                        tool_name="(engine)",
                        parameters={
                            "turn": turns_used,
                            "response": {
                                "usage": response.usage or {},
                                "thinking": getattr(response, "thinking", "") or "",
                                "text": response.text or "",
                                "stop_reason": getattr(response, "stop_reason", ""),
                                "tool_calls": [
                                    {
                                        "id": getattr(c, "id", ""),
                                        "name": getattr(c, "name", ""),
                                        "input": getattr(c, "input", {}),
                                    }
                                    for c in (response.tool_calls or [])
                                ],
                            },
                        },
                        result_summary=(
                            f"stop={getattr(response, 'stop_reason', '')}; "
                            f"tools={len(response.tool_calls or [])}; "
                            f"text_chars={len(response.text or '')}; "
                            f"thinking_chars={len(getattr(response, 'thinking', '') or '')}"
                        ),
                        user_approved=False,
                    )
                except Exception:
                    pass
                # Block B+ (PORT_LOG #052): per-turn cost-vs-budget runtime
                # warning. v4 sagemaker_agent.py:8787 prints
                #   `[Cost ${session_cost} passed budget ${limit} ƒ?T'?" continuing.]`
                # NOT a hard halt ƒ?T'?" per user 2026-05-03 update to plan v3,
                # v5 matches v4 UX: warn and continue. True hard halt is at
                # cloud-budget level (AWS Budget Action / GCP).
                from runtime.config import CONFIG as _CFG
                limit = getattr(_CFG, "session_cost_limit", 0.0)
                # Block B+ Codex finding #1 lock: `>=` so exact-100% trips
                # the warning (`>` would skip parity-100% cases).
                if limit > 0 and _TOKENS.session_cost >= limit:
                    if not getattr(self, "_warned_over_budget", False):
                        output_fn(
                            f"[Cost ${_TOKENS.session_cost:.4f} passed "
                            f"budget ${limit:.2f} ƒ?T'?" continuing.]"
                        )
                        self._warned_over_budget = True
            except Exception:
                pass

            # Append assistant turn (text + tool_use blocks, plus thinking).
            assistant_content = self._build_assistant_content(response)
            self.messages.append({"role": "assistant", "content": assistant_content})

            if response.text:
                last_text = response.text

            # Block A ƒ?T'?" auto-compact gate. Per-turn check: if the
            # message buffer has crossed the 80% threshold AND the
            # circuit breaker allows another attempt, run Compactor.
            try:
                from core.compactor import Compactor, AUTO_COMPACT
                from runtime.config import CONFIG as _CFG_AC
                _max_ctx = getattr(_CFG_AC, "context_max_tokens", 200_000)
                if Compactor.should_compact(self.messages, _max_ctx):
                    _ok, _why = AUTO_COMPACT.try_attempt()
                    if _ok:
                        _result = Compactor.run(self.client, self.messages, _max_ctx)
                        if _result.success:
                            output_fn(
                                f"[auto-compact] saved "
                                f"{_result.tokens_before - _result.tokens_after:,} "
                                f"tokens; continuing."
                            )
                            self.messages = _result.messages_after
                    else:
                        # Cooldown / cap message ƒ?T'?" log once per turn, no
                        # spam since try_attempt returns reason text.
                        output_fn(f"[auto-compact skipped: {_why}]")
            except Exception:
                pass

            # Stop conditions: end_turn / no tool_use blocks ƒ?T'+' final answer.
            if not response.tool_calls:
                # Block F2 ƒ?T'?" auto-continuation under iteration budget. Only
                # parent agents (not sub-agents) and only when CONFIG flag
                # is opt-in (default OFF per Wave 6 NLT row #21). Cost-cap
                # halt has priority inside check_iteration_budget().
                try:
                    from runtime.config import CONFIG as _CFG_F2
                    if getattr(_CFG_F2, "enable_token_budget_continuation", False):
                        from core.budget_continuation import (
                            check_iteration_budget,
                            create_budget_tracker,
                            ContinueDecision,
                            StopDecision,
                        )
                        if self._budget_tracker is None:
                            self._budget_tracker = create_budget_tracker()
                        _is_sub = self.agent_kind != "parent"
                        _sc = 0.0
                        try:
                            from runtime.tokens import TOKENS as _TOKENS_F2
                            _sc = float(getattr(_TOKENS_F2, "session_cost", 0.0))
                        except Exception:
                            _sc = 0.0
                        _scl = float(getattr(_CFG_F2, "session_cost_limit", 0.0))
                        decision = check_iteration_budget(
                            self._budget_tracker,
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 2760ms:
            return False

        self._engine = QueryEngine(
            client=client,
            max_turns=max_turns,
            budget=self.budget,
            on_stop_check=_combined_stop,
            skill_manager=skill_manager,
        )
        self._system_prompt = system_prompt
        self._plan_mode = bool(plan_mode)
        self._thinking_enabled = bool(thinking_enabled)
        self._thinking_budget = int(thinking_budget)
        # Block B+: AGENT_STATUS auto-load runs once on the first run() call.
        self._agent_status_loaded = False
        self._agent_status_text: Optional[str] = None

    # ------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------

    def run(
        self,
        message: str,
        tools: Optional[List[Any]] = None,
        output_fn: Callable[[str], None] = print,
    ) -> QueryResult:
        """Execute a single user turn. Returns the `QueryResult`."""
        # Lazy-import to avoid circular import on package init
        from prompt import build_system_prompt, CACHE_BOUNDARY
        from tools import all_registered

        # Block B+: AGENT_STATUS auto-load on first run() call. Reads
        # `<workspace>/AGENT_STATUS.md` (or CONFIG.status_doc) and
        # appends it to the dynamic tail of the system prompt so the
        # agent picks up handoff context from a previous session.
        # Reads file ONCE per Agent instance (idempotent).
        if not self._agent_status_loaded and self._system_prompt is None:
            try:
                self._agent_status_text = _load_agent_status_text()
            except Exception:
                self._agent_status_text = None
            self._agent_status_loaded = True

        system_prompt = self._system_prompt or build_system_prompt(ctx={})
        if self._agent_status_text:
            # Append to the dynamic tail (after CACHE_BOUNDARY) so the
            # cache-aware prefix replay (Block G2 territory) still works.
            if CACHE_BOUNDARY in system_prompt:
                system_prompt = (
                    system_prompt + "\n\n## Handoff: AGENT_STATUS\n\n"
                    + self._agent_status_text
                )
            else:
                system_prompt = (
                    system_prompt + CACHE_BOUNDARY
                    + "\n\n## Handoff: AGENT_STATUS\n\n"
                    + self._agent_status_text
                )
        active_tools = list(tools) if tools is not None else all_registered()

        self._stop_requested = False  # reset between runs
        # R-tier R1 PHASE A iter-2 fix: propagate CONFIG.max_tokens +
        # CONFIG.temperature into the per-call Bedrock kwargs. Without
        # this, R-tier tests that override CONFIG.max_tokens (to cap
        # per-turn output cost) would have no effect because QueryEngine.run
        # defaults to max_tokens=4096 / temperature=0.0.
        from runtime.config import CONFIG as _CFG
        _max_tokens = getattr(_CFG, "max_tokens", 4096)
        _temperature = getattr(_CFG, "temperature", 0.0)
        result = self._engine.run(
            user_message=message,
            system_prompt=system_prompt,
            tools=active_tools,
            plan_mode=self._plan_mode,
            output_fn=output_fn,
            thinking_enabled=self._thinking_enabled,
            thinking_budget=self._thinking_budget,
            max_tokens=_max_tokens,
            temperature=_temperature,
        )
        return result

    def stop(self) -> None:
        """Request the next-turn checkpoint to break out of the loop."""
        self._stop_requested = True

    def clear(self, reset_budget: bool = False) -> None:
        """Reset the conversation buffer. Optionally also reset the budget.

        By default the budget is preserved across `clear()` so a user who
        wants a fresh conversation but still respects the cost ceiling
        doesn't have to pass anything special. Pass `reset_budget=True`
        for the more aggressive reset.
        """
        self._engine.messages = []
        self._engine._discovered_tool_names = set()
        if reset_budget:
            self.budget.reset()

    # ------------------------------------------------------------
    # Read-only views (used by Phase 11 widgets)
    # ------------------------------------------------------------

    @property
    def messages(self) -> list:
        """Snapshot of the conversation buffer (for the chat UI to render)."""
        return list(self._engine.messages)

    @property
    def thinking_enabled(self) -> bool:
        return self._thinking_enabled

    @property
    def thinking_budget(self) -> int:
        return self._thinking_budget

    def set_thinking(self, enabled: bool, budget: Optional[int] = None) -> None:
        """Update thinking-mode settings (PS Issue #4 UI hook)."""
        self._thinking_enabled = bool(enabled)
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 3483ms:
MODEL_COSTS: Dict[str, Dict[str, float]] = {
    "anthropic.claude-haiku-4-5-20251001-v1:0": {"input": 0.001, "output": 0.005},
    "anthropic.claude-sonnet-4-5-20250929-v1:0": {"input": 0.003, "output": 0.015},
    # Phase-1 baseline kept for parity tests
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {"input": 0.003, "output": 0.015},
}

# Backwards-compat alias (v4 internal name used inside TokenTracker.add).
_MODEL_PRICING = MODEL_COSTS


# R-tier R1 PHASE A iter-3 fix: AWS Bedrock geo inference profiles
# (au. / us. / eu. / apac.) carry a 10% premium over the global Anthropic
# list price for Haiku 4.5 and Sonnet 4.5. The local cost tracker MUST
# apply this multiplier to avoid undercounting actual AWS spend (which
# would let R-tier tests "pass cap locally" while exceeding it in real
# AWS billing).
#
# Sources (verified 2026-05-03):
#   - AWS Bedrock model card for Haiku 4.5 documents au./us./eu./apac.
#     as Geo Inference IDs.
#   - Anthropic pricing docs
#     (https://platform.claude.com/docs/en/about-claude/pricing) state
#     regional/multi-region endpoints carry a 10% premium over global.
#   - v5 internal corroboration: clara/prompts/HOW_TO_USE.md:31 prices
#     Haiku (AU) at $1.10 confirming the premium.
#
# Global / standard prefix `anthropic.` = 1.0x.
# Geo prefixes `au.` / `us.` / `eu.` / `apac.` = 1.10x.
GEO_INFERENCE_PREMIUM = 1.10
_GEO_PREFIXES = ("au.", "apac.", "us.", "eu.")


def get_geo_multiplier(model_id: str) -> float:
    """Return the price multiplier for a Bedrock model id.

    1.0  = global (`anthropic.<...>`)
    1.10 = geo inference profile (`au.<...>`, `us.<...>`, `eu.<...>`, `apac.<...>`)

    Source: AWS Bedrock model card for Haiku 4.5 documents au./us./eu./apac.
    as Geo Inference IDs. Anthropic pricing
    (https://platform.claude.com/docs/en/about-claude/pricing) states
    regional/multi-region endpoints carry a 10% premium over global.
    v5 internal: clara/prompts/HOW_TO_USE.md:31 prices Haiku (AU) at $1.10
    confirming the premium.
    """
    if not model_id:
        return 1.0
    if any(model_id.startswith(p) for p in _GEO_PREFIXES):
        return GEO_INFERENCE_PREMIUM
    return 1.0


def canonicalize_model_id(model_id: str) -> str:
    """Strip Bedrock cross-region inference prefixes for pricing lookup.

    Bedrock inference-profile prefixes covered:
        au.   ƒ?T'?" Australia (Sydney; ap-southeast-2 default)
        apac. ƒ?T'?" Asia-Pacific
        us.   ƒ?T'?" United States (legacy us-east-1 / us-west-2)
        eu.   ƒ?T'?" Europe (legacy eu-west-1 / eu-central-1)

    Source: AWS Bedrock model card for Haiku 4.5 documents au./us./eu./apac.
    as Geo Inference IDs. Anthropic pricing
    (https://platform.claude.com/docs/en/about-claude/pricing) states
    regional/multi-region endpoints carry a 10% premium over global.
    v5 internal: clara/prompts/HOW_TO_USE.md:31 prices Haiku (AU) at $1.10
    confirming the premium.

    Codex Block-B finding #1 (HIGH) lock: `au.` was missing originally,
    causing CONFIG.model_id="au.anthropic.claude-sonnet-4-5-..." to
    miss MODEL_COSTS entirely and TOKENS to record $0.

    NOTE: stripping the prefix gets the BASE rate from MODEL_COSTS;
    callers must additionally apply `get_geo_multiplier()` to charge the
    +10% premium on geo-inference profiles. R-tier R1 iter-3 fix.
    """
    if not model_id:
        return model_id
    for prefix in _GEO_PREFIXES:
        if model_id.startswith(prefix):
            return model_id[len(prefix):]
    return model_id


# ============================================================
# R4 #14 ƒ?T'?" EXCLUDED_MODELS_FOR_CACHE_BREAK (MUST)
# ============================================================
#
# Haiku-4.5 cache hashing in Bedrock is non-deterministic in a way that
# the prompt-cache-break detector misreads as a "section flipped". Add
# Haiku to the exclusion set so cache-break warnings don't fire on Haiku
# sessions. This is a MUST per Wave-5-DEEP R4 #14.

EXCLUDED_MODELS_FOR_CACHE_BREAK: set = {
    "anthropic.claude-haiku-4-5-20251001-v1:0",
}


# ============================================================
# B-5 ƒ?T'?" IMAGE_MAX_TOKEN_SIZE (R4 #38)
# ============================================================
#
# Per Anthropic billing: each image consumed by Bedrock counts for at
# most 2000 tokens regardless of resolution. Used by the rough estimator
# below.

IMAGE_MAX_TOKEN_SIZE: int = 2000



        agent_kind: attribution bucket. "parent" (default) for the main
        agent loop; sub-agent type-strings ("build", "explore", "verify",
        "plan", "review", "general") for spawned children. The session
        rollup totals always include both.
        """
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        cache_read = int(usage.get("cache_read_input_tokens", 0) or 0)
        cache_write = int(usage.get("cache_creation_input_tokens", 0) or 0)

        with self._lock:
            self.last_input = input_tokens
            self.last_output = output_tokens
            self.session_input += input_tokens
            self.session_output += output_tokens
            self.session_total = self.session_input + self.session_output
            self.session_cache_read += cache_read
            self.session_cache_write += cache_write
            self.api_calls += 1
            # B-8 ƒ?T'?" record last usage so estimators can walk back.
            self._last_usage_record = dict(usage)

            raw_mid = model_id or self._config.model_id
            mid = canonicalize_model_id(raw_mid)
            if model_id:
                self._model_id = model_id
            pricing = MODEL_COSTS.get(mid)
            cost = 0.0
            if pricing:
                # R-tier R1 PHASE A iter-3 fix: apply geo-inference
                # premium (1.10x) for au./us./eu./apac. profiles. Without
                # this, local cost tracker undercounts AWS billing by 10%.
                geo_mult = get_geo_multiplier(raw_mid)
                base_input = pricing["input"] * geo_mult
                base_output = pricing["output"] * geo_mult
                regular_input = max(0, input_tokens - cache_read - cache_write)
                cost = (
                    (regular_input / 1000) * base_input
                    + (cache_read / 1000) * base_input * 0.1
                    + (cache_write / 1000) * base_input * 1.25
                    + (output_tokens / 1000) * base_output
                )
                self.session_cost += cost
                self.last_cost = cost
            else:
                if not hasattr(self, "_warned_models"):
                    self._warned_models = set()
                if mid not in self._warned_models:
                    self._warned_models.add(mid)
                    logging.warning(
                        f"TokenTracker: no pricing for model '{mid}' ƒ?T'?" cost will show as $0. "
                        f"Add to MODEL_COSTS dict in runtime/tokens.py."
                    )
                self.last_cost = 0.0

            # Per-agent attribution (additive ƒ?T'?" same singleton, separate buckets).
            if agent_kind == "parent":
                self.parent_input_tokens += input_tokens
                self.parent_output_tokens += output_tokens
                self.parent_cost += cost
            else:
                self.subagent_input_tokens[agent_kind] = (
                    self.subagent_input_tokens.get(agent_kind, 0) + input_tokens
                )
                self.subagent_output_tokens[agent_kind] = (
                    self.subagent_output_tokens.get(agent_kind, 0) + output_tokens
                )
                self.subagent_cost[agent_kind] = (
                    self.subagent_cost.get(agent_kind, 0.0) + cost
                )

            # Budget gate (verbatim from v4).
            limit = self._config.session_cost_limit
            if limit > 0 and self.session_cost > 0:
                pct = self.session_cost / limit
                if pct >= 1.0 and not self._budget_stopped:
                    self._budget_stopped = True
                    logging.warning(
                        f"Session cost ${self.session_cost:.4f} reached limit ${limit:.2f}."
                    )
                elif pct >= 0.8 and not self._budget_warned:
                    self._budget_warned = True
                    logging.warning(
                        f"Session cost ${self.session_cost:.4f} is {pct:.0%} of ${limit:.2f} limit."
                    )

    # --------------------------------------------------------
    # Read-only views (v4 verbatim)
    # --------------------------------------------------------

    def is_over_budget(self) -> bool:
        limit = self._config.session_cost_limit
        return limit > 0 and self.session_cost >= limit

    def get_last(self) -> str:
        return f"In:{self.last_input:,} Out:{self.last_output:,}"

    def get_session(self) -> str:
        return (
            f"In:{self.session_input:,} Out:{self.session_output:,} "
            f"Total:{self.session_total:,}"
        )

    def get_cache_savings_usd(self) -> float:
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "context_max_tokens|max_tokens" compact_v5/MAIN/agent/runtime/config.py compact_v5/MAIN/agent/tests/integration/test_block_a.py compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/runtime/config.py | Select-Object -First 130' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path compact_v5/MAIN/agent/tests/integration/test_block_a.py | Select-Object -Skip 200 -First 120' in D:\Github\sagemaker-coding-agent
 succeeded in 2712ms:
"""V5 Config ƒ?T'?" verbatim port from compact_v4/MAIN/agent/sagemaker_agent.py:1018-1287.

Per ADR-006: Config + JSONC loader is a pure v4 reuse, no Runnable adoption.
Behavior unchanged from v4.10.10 final state. Only structural change: lives in
its own module instead of inline in the monolith.

Source: compact_v4/MAIN/agent/sagemaker_agent.py:1018 (Config dataclass),
        :1152 (_strip_jsonc_comments), :1190 (_load_config_file),
        :1205 (_apply_config_file), :1285 (CONFIG = Config()).

The flat-zip ship surface (Phase 13) collapses this back to root-level
`config.py` next to chat.ipynb; v5 source-tree namespacing is dev-time only.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Dict


# ============================================================
# CONFIG (verbatim port from v4)
# ============================================================

@dataclass
class Config:
    """Agent configuration."""
    # AWS Settings
    region: str = "ap-southeast-2"  # Sydney
    # Default runtime model: Sonnet 4.5 inference profile.
    # V4.10.1: default switched from Haiku 4.5 to Sonnet 4.5 (user-set, 2026-04-28).
    # Cost note: Sonnet 4.5 is ~10x the per-token cost of Haiku 4.5, but the
    # prompt-cache checkpoint threshold drops from 4096 (Haiku) to 1024 tokens
    # (Sonnet), so caching activates earlier and offsets some of the cost on
    # multi-turn sessions. To switch back to Haiku for cost-sensitive runs,
    # set model_id to "au.anthropic.claude-haiku-4-5-20251001-v1:0" in agent_config.json.
    model_id: str = "au.anthropic.claude-sonnet-4-5-20250929-v1:0"

    # Workspace - use absolute paths to avoid confusion
    workspace: str = os.getcwd()
    sessions_dir: str = os.path.join(os.getcwd(), "sessions")
    audit_dir: str = os.path.join(os.getcwd(), "audit_logs")

    # Limits
    max_turns: int = 60
    max_tokens: int = 16384  # Must be > thinking_budget when thinking enabled
    max_history: int = 20
    max_output_chars: int = 50000  # Matches Runnable's DEFAULT_MAX_RESULT_SIZE_CHARS (50K)
    max_file_size: int = 10 * 1024 * 1024  # 10MB

    # Context limits (Claude 3.5 = 200K tokens)
    context_max_tokens: int = 200000

    # Model parameters
    temperature: float = 0.0
    thinking_enabled: bool = False  # Extended thinking OFF by default
    thinking_budget: int = 8192  # Tokens for thinking (1024-16000)

    # Testing
    mock_mode: bool = False  # Set True to test without Bedrock API

    # Security policy
    allowed_paths: list = None  # Additional directories accessible outside workspace
    bash_allow_interpreters: bool = False  # Block python/node via bash (use python_exec)
    bash_allow_docker: bool = False        # If True, allow docker/docker-compose via bash

    # Runtime isolation / execution limits
    execution_mode: str = "local"  # local | docker
    exec_docker_image: str = "python:3.11-slim"
    exec_docker_network_disabled: bool = True
    exec_docker_readonly_rootfs: bool = True
    exec_docker_cpus: float = 1.0
    exec_docker_memory: str = "1g"
    exec_docker_pids_limit: int = 128

    # Operational controls
    require_auth: bool = False
    require_tool_approval: bool = True
    auth_token_env: str = "SAGEMAKER_AGENT_AUTH_TOKEN"
    max_user_messages_per_minute: int = 10
    max_user_messages_per_session: int = 150
    # V4.10.10: 40 -> 200. Old 40-call ceiling was hit mid-task in real SageMaker
    # sessions (real log: agent finished call 40 at 06:29 then spent 5 minutes
    # confused about which tools were still available). Only bash + python_exec
    # are counted; read_file/grep/glob/edit_file/etc are unaffected.
    max_exec_calls_per_session: int = 200
    max_exec_seconds_per_session: int = 900
    session_cost_limit: float = 0.0  # 0 = no limit. Warns at 80%, stops at 100%.
    audit_retention_days: int = 30

    # AWS scope
    aws_bedrock_only: bool = False  # Set True to block all boto3 except bedrock-runtime
    disable_local_traces: bool = False  # Set True for zero local footprint

    # V4.7.1 local-git baseline maintenance
    auto_commit_every: int = 0

    # V4 capabilities
    load_claude_md: bool = True
    enable_prompt_cache: bool = True
    enable_memory_extraction: bool = False
    enable_status_doc: bool = True
    status_doc: str = "AGENT_STATUS.md"
    enable_skills: bool = True
    enable_skill_auto_trigger: bool = False  # V4.9.6: global opt-in; no skill auto-loads by default
    skills_dir: str = "./skills"
    enable_mcp: bool = False
    mcp_servers: Dict = field(default_factory=dict)
    mcp_timeout_seconds: int = 30
    subagent_max_depth: int = 2
    enable_worktree: bool = True

    # V4.9.4: shared iteration budget across parent + sub-agents (hermes pattern).
    # V4.10.10: default bumped 90 -> 600 for normal SageMaker development.
    max_iteration_budget: int = 600

    # V4.9.4: optional auxiliary model for compaction summaries
    compaction_model: str = ""

    # V4.9.5: opt-in self-patching skills
    enable_skill_patching: bool = False

    # V4.10.2: control whether the verify-after-3-edits Verification Contract is
    # MANDATORY or merely SUGGESTED. Default False = suggest-and-let-user-confirm.
    enforce_verify_contract: bool = False

    # V4.10.4: control sub-agent handoff block
    enable_subagent_handoff: bool = True
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 2855ms:
compact_v5/MAIN/agent/tests/integration/test_block_a.py:61:    assert Compactor.should_compact(msgs, max_tokens=100_000)
compact_v5/MAIN/agent/tests/integration/test_block_a.py:63:    assert not Compactor.should_compact(msgs, max_tokens=400_000)
compact_v5/MAIN/agent/tests/integration/test_block_a.py:70:    assert not Compactor.should_compact(msgs, max_tokens=200_000)
compact_v5/MAIN/agent/tests/integration/test_block_a.py:184:    result = Compactor.run(client, msgs, max_tokens=100_000)
compact_v5/MAIN/agent/tests/integration/test_block_a.py:197:    result = Compactor.run(client, msgs, max_tokens=200_000)
compact_v5/MAIN/agent/tests/integration/test_block_a.py:459:    def fake_run(client_arg, messages, max_tokens=200_000):
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:85:    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:93:        CONFIG.max_tokens = 64
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:176:        if saved_max_tokens is not None:
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:177:            CONFIG.max_tokens = saved_max_tokens
compact_v5/MAIN/agent/runtime/config.py:48:    max_tokens: int = 16384  # Must be > thinking_budget when thinking enabled
compact_v5/MAIN/agent/runtime/config.py:54:    context_max_tokens: int = 200000
compact_v5/MAIN/agent/runtime/config.py:221:        "region": str, "model_id": str, "max_turns": int, "max_tokens": int,
compact_v5/MAIN/agent/runtime/config.py:240:        "context_max_tokens": int,
compact_v5/MAIN/agent/runtime/config.py:267:        if key in ("max_turns", "max_tokens", "max_history", "subagent_max_depth") and val < 1:
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 3439ms:

# ============================================================
# T1 ƒ?T'?" AutoCompactCircuitBreaker
# ============================================================

def test_circuit_breaker_cooldown_blocks_repeated_attempts():
    from core.compactor import AutoCompactCircuitBreaker

    cb = AutoCompactCircuitBreaker(cooldown_seconds=10, max_per_session=100)
    ok, _ = cb.should_attempt()
    assert ok
    cb.record_attempt()
    ok2, reason = cb.should_attempt()
    assert not ok2
    assert "cooldown" in reason.lower()


def test_circuit_breaker_session_cap():
    from core.compactor import AutoCompactCircuitBreaker

    cb = AutoCompactCircuitBreaker(cooldown_seconds=0, max_per_session=2)
    cb.record_attempt()
    cb.record_attempt()
    ok, reason = cb.should_attempt()
    assert not ok
    assert "session cap" in reason.lower()


def test_circuit_breaker_reset():
    from core.compactor import AutoCompactCircuitBreaker

    cb = AutoCompactCircuitBreaker(cooldown_seconds=10, max_per_session=2)
    cb.record_attempt()
    cb.record_attempt()
    assert not cb.should_attempt()[0]
    cb.reset()
    assert cb.should_attempt()[0]


# ============================================================
# T1 ƒ?T'?" apply_cache_control_to_blocks
# ============================================================

def test_apply_cache_control_marks_last_ephemeral():
    from core.compactor import apply_cache_control_to_blocks

    blocks = [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]
    out = apply_cache_control_to_blocks(blocks)
    assert "cache_control" not in out[0]
    assert out[1]["cache_control"] == {"type": "ephemeral"}


def test_apply_cache_control_at_specific_index():
    from core.compactor import apply_cache_control_to_blocks

    blocks = [{"type": "text", "text": str(i)} for i in range(3)]
    out = apply_cache_control_to_blocks(blocks, cache_break_at=0)
    assert out[0]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in out[1]
    assert "cache_control" not in out[2]


def test_apply_cache_control_empty_list():
    from core.compactor import apply_cache_control_to_blocks
    assert apply_cache_control_to_blocks([]) == []


# ============================================================
# B-2 ƒ?T'?" count_tokens_via_haiku_fallback
# ============================================================

def test_count_tokens_haiku_fallback_in_mock_mode():
    from core.compactor import count_tokens_via_haiku_fallback
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    msgs = [{"role": "user", "content": "hello world"}]
    n = count_tokens_via_haiku_fallback(msgs, client)
    assert isinstance(n, int)
    assert n > 0


def test_count_tokens_haiku_fallback_handles_none_client():
    from core.compactor import count_tokens_via_haiku_fallback
    assert count_tokens_via_haiku_fallback([], None) is None


# ============================================================
# B+5 ƒ?T'?" advisor sub-cost attribution
# ============================================================

def test_advisor_cost_attributed_when_aux_model_set(monkeypatch):
    """When CONFIG.compaction_model is set AND a different aux client is
    used, summary tokens go into TOKENS.subagent_cost['advisor'].
    Closes the B+5 deferral from ADR-022."""
    from core.compactor import Compactor
    from runtime.bedrock_client import BedrockClient, Response
    from runtime.tokens import TOKENS
    from runtime.config import CONFIG

    # Set up: main client + auxiliary client (we mock the aux build).
    main_client = BedrockClient(model_id="main-model", region="us-east-1", mock_mode=True)
    aux_client = BedrockClient(model_id="aux-model", region="us-east-1", mock_mode=True)

    monkeypatch.setattr(CONFIG, "compaction_model", "aux-model")
    Compactor._aux_client_cache = {}  # reset cache

    # Spy on _summary_client to verify aux is selected.
    monkeypatch.setattr(
        Compactor, "_summary_client",
        classmethod(lambda cls, mc: aux_client),
    )

    def fake_aux_chat(*args, **kwargs):
        return Response(
            text="advisor-built summary",
            usage={"input_tokens": 500, "output_tokens": 100},
        )

    monkeypatch.setattr(aux_client, "chat", fake_aux_chat)
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Select-String -Path compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py -Pattern \"result = agent.run|assert \\(\\\"5\\\"|tokens_in >|CONFIG.context_max|_LOREM_LINES|def test_r2|CONFIG.session_cost_limit|require_tool_approval|max_turns=4\"" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Select-String -Path compact_v5/MAIN/agent/core/query_engine.py -Pattern "auto-compact gate|should_compact|Compactor.run|if not response.tool_calls|TOKENS.add|session_cost_limit"' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Select-String -Path compact_v5/MAIN/agent/runtime/config.py -Pattern "context_max_tokens|max_tokens|session_cost_limit|require_tool_approval"' in D:\Github\sagemaker-coding-agent
2026-05-03T23:21:56.926744Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 1.9 seconds
Output:
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 
Select-String : A positional parameter cannot be found that accepts argument '5\|tokens_in 
>|CONFIG.context_max|_LOREM_LINES|def test_r2|CONFIG.session_cost_limit|require_tool_approval|max_turns=4'.
At line:2 char:1
+ Select-String -Path compact_v5/MAIN/agent/tests/r_tier/test_r2_compac ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (:) [Select-String], ParameterBindingException
    + FullyQualifiedErrorId : PositionalParameterNotFound,Microsoft.PowerShell.Commands.SelectStringCommand
 

 exited 1 in 1855ms:
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 
Select-String : A positional parameter cannot be found that accepts argument '5\|tokens_in 
>|CONFIG.context_max|_LOREM_LINES|def test_r2|CONFIG.session_cost_limit|require_tool_approval|max_turns=4'.
At line:2 char:1
+ Select-String -Path compact_v5/MAIN/agent/tests/r_tier/test_r2_compac ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (:) [Select-String], ParameterBindingException
    + FullyQualifiedErrorId : PositionalParameterNotFound,Microsoft.PowerShell.Commands.SelectStringCommand
 

 succeeded in 2646ms:

compact_v5\MAIN\agent\core\query_engine.py:233:        # Block B: per-agent attribution key for TOKENS.add(). "parent" 
by
compact_v5\MAIN\agent\core\query_engine.py:554:                _TOKENS.add(
compact_v5\MAIN\agent\core\query_engine.py:599:                limit = getattr(_CFG, "session_cost_limit", 0.0)
compact_v5\MAIN\agent\core\query_engine.py:619:            # Block A - auto-compact gate. Per-turn check: if the
compact_v5\MAIN\agent\core\query_engine.py:626:                if Compactor.should_compact(self.messages, _max_ctx):
compact_v5\MAIN\agent\core\query_engine.py:629:                        _result = Compactor.run(self.client, 
self.messages, _max_ctx)
compact_v5\MAIN\agent\core\query_engine.py:645:            if not response.tool_calls:
compact_v5\MAIN\agent\core\query_engine.py:668:                        _scl = float(getattr(_CFG_F2, 
"session_cost_limit", 0.0))
compact_v5\MAIN\agent\core\query_engine.py:675:                            session_cost_limit=_scl,


Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 3356ms:

compact_v5\MAIN\agent\runtime\config.py:48:    max_tokens: int = 16384  # Must be > thinking_budget when thinking 
enabled
compact_v5\MAIN\agent\runtime\config.py:54:    context_max_tokens: int = 200000
compact_v5\MAIN\agent\runtime\config.py:80:    require_tool_approval: bool = True
compact_v5\MAIN\agent\runtime\config.py:90:    session_cost_limit: float = 0.0  # 0 = no limit. Warns at 80%, stops at 
100%.
compact_v5\MAIN\agent\runtime\config.py:135:    # budget AND not diminishing-returns AND session_cost < 
session_cost_limit
compact_v5\MAIN\agent\runtime\config.py:221:        "region": str, "model_id": str, "max_turns": int, "max_tokens": 
int,
compact_v5\MAIN\agent\runtime\config.py:227:        "require_auth": bool, "require_tool_approval": bool,
compact_v5\MAIN\agent\runtime\config.py:228:        "aws_bedrock_only": bool, "disable_local_traces": bool, 
"session_cost_limit": float,
compact_v5\MAIN\agent\runtime\config.py:240:        "context_max_tokens": int,
compact_v5\MAIN\agent\runtime\config.py:267:        if key in ("max_turns", "max_tokens", "max_history", 
"subagent_max_depth") and val < 1:


Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Select-String -Path compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py -Pattern "_LOREM_LINES|def test_r2|CONFIG.session_cost_limit|CONFIG.max_tokens|require_tool_approval|max_turns=4|result = agent.run|tokens_in > 50_000|five"' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Select-String -Path compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py -Pattern '\"5\" in result.text'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Select-String -Path compact_v5/MAIN/agent/core/compactor.py -Pattern "SUMMARY_TRIGGER_PERCENT|KEEP_LAST_MESSAGES|def should_compact|def run"' in D:\Github\sagemaker-coding-agent
 succeeded in 1901ms:

compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:48:_LOREM_LINES = 2700
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:66:def test_r2_compaction_under_load(tmp_path, monkeypatch):
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:86:    saved_require_approval = getattr(CONFIG, 
"require_tool_approval", None)
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:90:        CONFIG.session_cost_limit = _R2_COST_CAP_USD
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:93:        CONFIG.max_tokens = 64
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:94:        CONFIG.require_tool_approval = False
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:109:            max_turns=4,
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:113:        recap = (_LOREM_LINE + "\n") * _LOREM_LINES
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:118:        result = agent.run(prompt, tools=[])
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:135:            "preamble_lines": _LOREM_LINES,
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:153:        # Different verbalizations OK ("5", "5.", "Five", "= 
5").
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:155:        assert ("5" in result.text) or ("five" in text_l), (
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:164:        assert tokens_in > 50_000, (
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:173:            CONFIG.session_cost_limit = saved_cost_limit
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:177:            CONFIG.max_tokens = saved_max_tokens
compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:179:            CONFIG.require_tool_approval = 
saved_require_approval


Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 2632ms:

compact_v5\MAIN\agent\tests\r_tier\test_r2_compact.py:155:        assert ("5" in result.text) or ("five" in text_l), (


Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 3348ms:

compact_v5\MAIN\agent\core\compactor.py:157:    SUMMARY_TRIGGER_PERCENT = 0.80
compact_v5\MAIN\agent\core\compactor.py:158:    KEEP_LAST_MESSAGES = 3
compact_v5\MAIN\agent\core\compactor.py:280:    def should_compact(cls, messages: List[Dict[str, Any]], max_tokens: 
int) -> bool:
compact_v5\MAIN\agent\core\compactor.py:290:        return total > max_tokens * cls.SUMMARY_TRIGGER_PERCENT
compact_v5\MAIN\agent\core\compactor.py:497:        keep_last = cls.KEEP_LAST_MESSAGES
compact_v5\MAIN\agent\core\compactor.py:509:    def run(


Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

codex
One more important detail emerged: `CONFIG.context_max_tokens` defaults to `200_000`, so the auto-compact threshold is about `160_000` estimated tokens, not `80_000`. The current ~78K input is below the actual gate, so even the post-response compaction check will not fire.
codex
**Axis A: REJECT**
The design does not exercise compaction. In [test_r2_compact.py](</mnt/data?>) the test sends one ~78K-token prompt, but auto-compact checks `Compactor.should_compact(...)` against `CONFIG.context_max_tokens=200_000`, so the real trigger is ~160K estimated tokens. Current R2 is below that and ends after the first model response.

The assertion that `"5" in result.text` is also loose. Use an exact-ish regex such as `^\s*(5|five)[\.\s]*$`. This test could also pass if most of the preamble were dropped, as long as the final question survived.

Setup is mostly fine, but if this becomes a real compaction test it should reset `AUTO_COMPACT` and probably reset `TOKENS` in `finally` to avoid cross-test leakage.

**Axis B: APPROVE WITH CAVEAT**
For the current single-call design, cost control is acceptable: ~78K input on AU Haiku 4.5 is about `$0.086`, `max_tokens=64` bounds output, `max_turns=4` bounds accidental loops, and `session_cost_limit=$0.50` is wired through `on_stop_check`.

Caveat: if R2 is changed to force compaction, the compaction summary is an additional Bedrock call. Recompute the cap before running; a two-large-turn design plus summary could approach `$0.40-$0.50`.

**Axis C: REJECT**
Current R2 provides empirical evidence for large Bedrock input handling and `TokenTracker` accumulation of 50K+ input tokens. It does not provide empirical evidence for Block A compaction, cache-edits invariants, safe message cutting, or ’'?opost-compact next Bedrock call succeeds.’'??

**PRE-FLIGHT VERDICT: REJECT**

Do not run AWS for this as ’'?oR2 compaction.’'?? Required fixes:

1. Either rename/scope it to ’'?olarge input sanity + TokenTracker’'?? and remove Block A claims, or make it actually cross the compaction threshold.
2. Add an assertion that compaction occurred, for example captured `[auto-compact]`, `Compactor.run` call count, `TOKENS.api_calls >= 2`, or final `agent.messages` containing `[CONVERSATION SUMMARY]`.
3. Add a post-compaction follow-up call that must answer correctly from the compacted buffer.
4. Tighten the final answer assertion to exact `5` / `five`.
5. Reset `AUTO_COMPACT` and token/config state cleanly around the test.
tokens used
54,431
**Axis A: REJECT**
The design does not exercise compaction. In [test_r2_compact.py](</mnt/data?>) the test sends one ~78K-token prompt, but auto-compact checks `Compactor.should_compact(...)` against `CONFIG.context_max_tokens=200_000`, so the real trigger is ~160K estimated tokens. Current R2 is below that and ends after the first model response.

The assertion that `"5" in result.text` is also loose. Use an exact-ish regex such as `^\s*(5|five)[\.\s]*$`. This test could also pass if most of the preamble were dropped, as long as the final question survived.

Setup is mostly fine, but if this becomes a real compaction test it should reset `AUTO_COMPACT` and probably reset `TOKENS` in `finally` to avoid cross-test leakage.

**Axis B: APPROVE WITH CAVEAT**
For the current single-call design, cost control is acceptable: ~78K input on AU Haiku 4.5 is about `$0.086`, `max_tokens=64` bounds output, `max_turns=4` bounds accidental loops, and `session_cost_limit=$0.50` is wired through `on_stop_check`.

Caveat: if R2 is changed to force compaction, the compaction summary is an additional Bedrock call. Recompute the cap before running; a two-large-turn design plus summary could approach `$0.40-$0.50`.

**Axis C: REJECT**
Current R2 provides empirical evidence for large Bedrock input handling and `TokenTracker` accumulation of 50K+ input tokens. It does not provide empirical evidence for Block A compaction, cache-edits invariants, safe message cutting, or ’'?opost-compact next Bedrock call succeeds.’'??

**PRE-FLIGHT VERDICT: REJECT**

Do not run AWS for this as ’'?oR2 compaction.’'?? Required fixes:

1. Either rename/scope it to ’'?olarge input sanity + TokenTracker’'?? and remove Block A claims, or make it actually cross the compaction threshold.
2. Add an assertion that compaction occurred, for example captured `[auto-compact]`, `Compactor.run` call count, `TOKENS.api_calls >= 2`, or final `agent.messages` containing `[CONVERSATION SUMMARY]`.
3. Add a post-compaction follow-up call that must answer correctly from the compacted buffer.
4. Tighten the final answer assertion to exact `5` / `five`.
5. Reset `AUTO_COMPACT` and token/config state cleanly around the test.
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 4385ms:
"""Block A ’'?" Compactor + auto-compact circuit breaker + Runnable cache_edits.

v5 port of v4's `Compactor` class (compact_v4/MAIN/agent/sagemaker_agent.py
lines 186-635, ~449 LOC). Adapted for v5's nested-package layout. Plus:
  - Auto-compact circuit breaker (Hermes-style cooldown)
  - Runnable cache_edits adaptation (cache_control on prompt sections ’'?"
    Bedrock equivalent of the Anthropic-direct cache_edits param)
  - B-2 countTokensViaHaikuFallback (deferred from Block B per ADR-021)
  - B+5 recursive advisor sub-cost accounting (deferred from Block B+
    per ADR-022 ’'?" auxiliary compaction-summary model)

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
    False ’'?" caller must continue without re-compacting. Hermes
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
        a clear log message. Session cap checked FIRST ’'?" once exhausted,
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
        """Mark a compact attempt ’'?" caller calls this after a successful
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
        check before either records ’'?" this closes the TOCTOU window
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
      ’'?" this is the B+5 recursive advisor sub-cost accounting that
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
        # Build tool_use_id ’'+' tool_name map so we can skip protected tools.
        for msg in pruned:
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        tool_name_map[item.get("id", "")] = item.get("name", "")

        # Walk most-recent ’'+' oldest; protect the last PROTECT_TOKENS worth.
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
        # Codex Block-A iter-1 finding #2 (MEDIUM) lock: v4 invariant ’'?"
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
    # Auxiliary-model routing (B+5 ’'?" recursive advisor sub-cost)
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
            "available ’'?" do NOT attempt any tool calls. Be concise but "
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
                "[END SUMMARY ’'?" Continuing from here]"
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
        """End-to-end: prune ’'+' summarize ’'+' compact. Single entry point."""
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
# Runnable cache_edits ’'?" Bedrock cache_control adaptation
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
    place to set this ’'?" the summary block becomes the new cache prefix.

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
# B-2 ’'?" countTokensViaHaikuFallback (deferred from Block B per ADR-021)
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
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 5597ms:
"""R-tier R2 ’'?" large preamble crosses Compactor threshold, follow-up
turn succeeds against the COMPACTED buffer.

Per PS_V5_TEST_PLAYBOOK / PS_V5_TEST_SET ATier 1 R2:
  Validates Block A (Compactor + auto-compact + cache invariants) on
  real Bedrock end-to-end:
    - Turn 1: large preamble + simple question ’'+' assistant answer.
      Crosses Compactor.should_compact threshold (80% of
      context_max_tokens).
    - Auto-compact fires after the response ’'?" summarises history into
      one [CONVERSATION SUMMARY] system block, freeing tokens.
    - Turn 2: follow-up question. Bedrock must accept the post-compact
      message buffer (no 400 from cut-mid-pair) and answer correctly
      using only the compact summary.

Codex R2 PHASE A iter-1 fixes applied (REJECT ’'+' re-pre-flight):
  1. Default CONFIG.context_max_tokens=200_000 means real trigger is
     ~160K. We monkey-patch CONFIG.context_max_tokens=100_000 for this
     test so the existing 78K preamble crosses the 80% gate (80K).
     Cheaper than pushing to 165K real tokens AND tests same code path.
  2. Tightened final answer regex (single-token "5" or "five" reply
     expected from max_tokens=64; pattern in code below).
  3. Compaction-occurred assertion: TOKENS.api_calls accounts for
     initial turn + compaction summary call + follow-up turn ’'%A? 3 if
     compact fired; OR captured "[auto-compact]" line in stdout.
  4. Follow-up turn against the compacted buffer (asks recall question
     answerable from system summary).
  5. AUTO_COMPACT.reset() + TOKENS.reset() in finally for hermetic test.

Cost cap: $0.50. Model: Haiku 4.5 AU.
Real-AWS gated: skipped without RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_R2_COST_CAP_USD = 0.50

# 2700 lines of lorem ’'%^ 60K words ’'%^ 78K tokens. With CONFIG.context_max_tokens
# = 100_000 (test override), this crosses the 80%-of-100K = 80K threshold.
_LOREM_LINE = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
    "eiusmod tempor incididunt ut labore et dolore magna aliqua. "
)
_LOREM_LINES = 2700

_R2_PROMPT_T1 = """You are reviewing a long conversation history. Below is a recap of
prior context ’'?" most of it is filler. After the recap, please answer
ONE SHORT question.

=== RECAP (do not summarize back; just keep in mind) ===
{recap}
=== END RECAP ===

QUESTION: What is 2 + 3? Answer with a single number, no explanation.
"""

# Follow-up ’'?" forces a 2nd Bedrock call against the post-compact buffer.
_R2_PROMPT_T2 = (
    "What was the previous question I asked? Reply with the question only "
    "(one short sentence)."
)


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R2 is real-AWS gated.",
)
def test_r2_compaction_under_load(tmp_path, monkeypatch):
    """R-tier R2 ’'?" large preamble + follow-up succeed across compaction.

    PASS criteria:
      - Turn 1 produces a tight "5"/"Five" answer.
      - Turn 2 is answered against the compacted buffer (recalls the
        previous question or a paraphrase).
      - Auto-compact fired (TOKENS.api_calls >= 2 ’'?" model+compact-summary
        on turn 1 alone ’'?" OR "[auto-compact]" appears in captured stdout).
      - cost ’'% $0.50.
    """
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    from core.compactor import AUTO_COMPACT
    import security.manager as sec_mgr
    from agent import Agent

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    saved_ctx_max = getattr(CONFIG, "context_max_tokens", None)
    cwd_before = os.getcwd()

    # Codex iter-1 fix #5: clean state in finally + at start.
    AUTO_COMPACT.reset() if hasattr(AUTO_COMPACT, "reset") else None

    captured_stdout: list = []

    def _stdout_capture(text: str) -> None:
        captured_stdout.append(text)
        # Also forward to print so pytest -s shows it.
        try:
            print(text)
        except Exception:
            pass

    try:
        CONFIG.workspace = str(tmp_path)
        CONFIG.session_cost_limit = _R2_COST_CAP_USD
        CONFIG.model_id = _HAIKU_45_AU
        CONFIG.max_tokens = 64
        CONFIG.require_tool_approval = False
        # Codex iter-1 fix #1: lower threshold so 78K crosses the 80% gate.
        CONFIG.context_max_tokens = 100_000
        sec_mgr.rebuild_singleton_for_tests()
        os.chdir(str(tmp_path))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt():
            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= _R2_COST_CAP_USD
            )

        agent = Agent(
            client=client,
            max_turns=4,
            on_stop_check=_hard_cost_halt,
        )

        recap = (_LOREM_LINE + "\n") * _LOREM_LINES
        prompt_t1 = _R2_PROMPT_T1.format(recap=recap)
        approx_tokens_in = len(prompt_t1) // 4

        t0 = time.time()
        # Turn 1 ’'?" large preamble.
        result_t1 = agent.run(prompt_t1, tools=[], output_fn=_stdout_capture)
        wall_t1 = time.time() - t0
        tokens_in_t1 = TOKENS.session_input
        api_calls_after_t1 = TOKENS.api_calls
        # Turn 2 ’'?" follow-up against (likely-compacted) buffer.
        t1 = time.time()
        result_t2 = agent.run(_R2_PROMPT_T2, tools=[], output_fn=_stdout_capture)
        wall_t2 = time.time() - t1
        cost_used = TOKENS.session_cost
        tokens_in = TOKENS.session_input
        tokens_out = TOKENS.session_output
        api_calls = TOKENS.api_calls

        # Detect compaction ’'?" either explicit log line or implicit from
        # api_calls (each Agent.run does ’'%A?1 call; auto-compact between
        # turns adds another for the summary).
        full_stdout = "\n".join(captured_stdout)
        compact_log_seen = "[auto-compact]" in full_stdout
        # Heuristic: 2 user turns alone = ’'%A?2 api_calls. With auto-compact
        # firing between t1 and t2, api_calls should be ’'%A?3.
        compact_likely = api_calls >= 3 or compact_log_seen

        metrics = {
            "test": "R2",
            "call": 1,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _HAIKU_45_AU,
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out),
            "tokens_in_after_turn1": int(tokens_in_t1),
            "wallclock_s": round(wall_t1 + wall_t2, 2),
            "wallclock_t1_s": round(wall_t1, 2),
            "wallclock_t2_s": round(wall_t2, 2),
            "approx_prompt_tokens": approx_tokens_in,
            "preamble_lines": _LOREM_LINES,
            "context_max_tokens_test_override": CONFIG.context_max_tokens,
            "api_calls": int(api_calls),
            "api_calls_after_t1": int(api_calls_after_t1),
            "compact_log_seen": compact_log_seen,
            "compact_likely": compact_likely,
            "tool_calls_t1": int(getattr(result_t1, "turns_used", 0)),
            "tool_calls_t2": int(getattr(result_t2, "turns_used", 0)),
            "cost_usd": round(cost_used, 4),
            "stop_reason_t1": result_t1.stop_reason,
            "stop_reason_t2": result_t2.stop_reason,
            "final_text_t1": (result_t1.text or "").strip()[:200],
            "final_text_t2": (result_t2.text or "").strip()[:200],
        }
        (tmp_path / "_r2_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
        print(f"\n[R2 METRICS] {json.dumps(metrics)}")

        # Codex iter-1 fix #2: tight regex on turn-1 answer.
        t1_text = (result_t1.text or "").strip()
        # Accept "5", "5.", "Five", "Five.", "= 5", with optional
        # leading "=" or whitespace.
        assert re.match(r"^\s*=?\s*(5|five)\b\.?\s*$", t1_text, re.IGNORECASE), (
            f"R2 turn 1 expected exact answer 5/five; got: {t1_text!r}. "
            f"metrics={metrics}"
        )
        assert result_t1.stop_reason != "max_turns", (
            f"R2 turn 1 hit max_turns. metrics={metrics}"
        )
        # Turn 2 ’'?" recall via compacted buffer.
        t2_text = (result_t2.text or "").lower()
        assert t2_text, f"R2 turn 2 empty response. metrics={metrics}"
        assert ("2 + 3" in t2_text or "2+3" in t2_text or
                "what is 2" in t2_text or "5" in t2_text), (
            f"R2 turn 2 didn't recall the prior question. "
            f"got: {result_t2.text!r}. metrics={metrics}"
        )
        # Codex iter-1 fix #3: assert compaction or 2-turn evidence.
        assert compact_likely, (
            f"R2 expected compaction OR ’'%A?3 api_calls (current: "
            f"api_calls={api_calls}, log_seen={compact_log_seen}). "
            f"metrics={metrics}"
        )
        # Cost.
        assert cost_used <= _R2_COST_CAP_USD, (
            f"R2 cost ${cost_used:.4f} exceeded cap ${_R2_COST_CAP_USD}. "
            f"metrics={metrics}"
        )
        # Sanity: large input was actually sent.
        assert tokens_in_t1 > 50_000, (
            f"R2 expected turn-1 input_tokens >50K; got {tokens_in_t1}. "
            f"metrics={metrics}"
        )
    finally:
        os.chdir(cwd_before)
        CONFIG.workspace = saved_ws
        sec_mgr.SECURITY = saved_sec
        if saved_cost_limit is not None:
            CONFIG.session_cost_limit = saved_cost_limit
        if saved_model is not None:
            CONFIG.model_id = saved_model
        if saved_max_tokens is not None:
            CONFIG.max_tokens = saved_max_tokens
        if saved_require_approval is not None:
            CONFIG.require_tool_approval = saved_require_approval
        if saved_ctx_max is not None:
            CONFIG.context_max_tokens = saved_ctx_max
        # Codex iter-1 fix #5.
        if hasattr(AUTO_COMPACT, "reset"):
            AUTO_COMPACT.reset()
        TOKENS.reset()
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 6566ms:
"""V5 core/query_engine.py ’'?" main agent loop (Phase 8 deliverable, ADR-014).

Per ADR-014: minimal, focused port of Runnable's `QueryEngine.ts` (1295 LOC)
adapted to the v5 .ipynb shape. v4's monolithic `Agent.run` (~1500 LOC) is
replaced by this ~400 LOC module with explicit IN-SCOPE / OUT-OF-SCOPE.

PORT_LOG: #019.

IN SCOPE (Phase 8):
- Per-turn loop with end_turn / max_turns / budget exhausted exits.
- IterationBudget gate at the top of each turn (shared with sub-agents).
- Phase 7 deferred-loading wiring contract:
    * `apply_tool_search_deferral(tools, enabled=True)` per turn.
    * `tool_search_discovered_names()` extraction from tool_search results.
    * Discovered names are added to the next turn's tools= API param.
- Tool dispatch via `find_tool_by_name(...).execute(args, context)`.
- tool_use ’'+' tool_result message accumulation in the model-visible
  conversation buffer.
- Bedrock invocation through `BedrockClient.chat(...)`.
- System prompt assembly via `prompt.build_system_prompt(ctx)`.
- run_one_turn(...) helper for unit tests (single-turn, no loop).

OUT OF SCOPE ’'?" explicitly deferred to later phases (per ADR-014):
- Microcompact / context_collapse ’'?" Phase 11 UX (PS Issue #4 widget surface).
- 2-stage smart compaction (prune + LLM summary) ’'?" Phase 11.
- Skill auto-trigger ’'?" Phase 10 (`SKILLS.discover_relevant`).
- Plan mode injection of skills into prompt ’'?" Phase 10.
- Sub-agent forkSubagent ’'?" Phase 9 (`subagent/spawn.py`).
- File-read state tracking ’'?" Phase 4 already lands this; engine respects but
  doesn't reset on compact (no compact in Phase 8).
- Diminishing-returns / repetition guard ’'?" deferred.
- Notebook UX (output_fn callback contract) ’'?" Phase 11 owns the UI shape;
  Phase 8 takes a `output_fn: Callable[[str], None] = print` so tests can
  capture, but real notebook integration lives in Phase 11.

The engine is thread-safe ONLY in the sense that IterationBudget is. Multiple
concurrent `run()` calls on the same engine are NOT supported (matches v4).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .budget import IterationBudget
from .errors import BedrockErrorCategory, ErrorClassifier


# ============================================================
# Result envelope
# ============================================================

@dataclass
class QueryResult:
    """Outcome of a `QueryEngine.run(...)` call.

    `text`           ’'?" final assistant text (last end_turn turn's text block).
    `messages`       ’'?" full message buffer including the user turn that
                       triggered this call. Caller may discard or persist.
    `stop_reason`    ’'?" "end_turn" | "max_turns" | "budget_exhausted" |
                       "context_overflow" | "fatal_error".
    `turns_used`     ’'?" count of model turns executed during this run.
    `budget_used`    ’'?" IterationBudget.used() snapshot at exit.
    `error`          ’'?" short message when stop_reason indicates failure.
    """
    text: str = ""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    stop_reason: str = ""
    turns_used: int = 0
    budget_used: int = 0
    error: Optional[str] = None


# ============================================================
# Helpers
# ============================================================

def _build_tools_api_payload(tools: List[Any]) -> List[Dict[str, Any]]:
    """Convert ToolRecord list into Bedrock `tools=` API payload shape.

    Bedrock expects: [{"name": ..., "description": ..., "input_schema": ...}, ...]
    """
    out: List[Dict[str, Any]] = []
    for t in tools:
        out.append({
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
        })
    return out


def _coerce_tool_result_to_text(value: Any) -> str:
    """Map any tool-execute return value into a Bedrock tool_result text string.

    Tool implementations return diverse shapes (str / dict / list). Bedrock's
    tool_result content needs a string. Prefer str() for primitives, JSON for
    structured shapes ’'?" same convention as v4 dispatch."""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple)):
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            return str(value)
    return str(value)


def count_tool_calls(messages: List[Dict[str, Any]], tool_name: str) -> int:
    """Count how many tool_use blocks for `tool_name` appear in `messages`.

    Block M-2 (PORT_LOG #084) ’'?" verbatim port of Runnable's countToolCalls
    at QueryEngine.ts:1004-1048. Used by the structured-output retry-limit
    guard: when the model produces malformed structured output N times in
    a row, the engine halts cleanly instead of looping.

    Iterates assistant messages; each tool_use block with matching name
    counts once.
    """
    if not tool_name:
        return 0
    count = 0
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_use"
                and block.get("name") == tool_name
            ):
                count += 1
    return count


def _truncate_tool_result(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    head = text[: max_chars - 200]
    return (
        head
        + f"\n\n[... truncated: tool_result exceeded {max_chars} chars; "
        f"original size {len(text)} chars ...]"
    )


def _make_unicode_safe_output_fn(fn: Callable[[str], None]) -> Callable[[str], None]:
    """Wrap an output_fn so UnicodeEncodeError doesn't kill the agent loop.

    R-tier R1 PHASE B iter-1 fix (2026-05-03): on Windows the default
    stdout encoding is cp1252, which can't encode emoji like ’'o. (U+2705).
    The model frequently emits emoji in summary blocks. Without this
    wrapper, the very first call to `print(response.text)` raises
    UnicodeEncodeError and the entire agent loop dies ’'?" even though
    the agent's actual work (chart.png + report.docx) was done.

    Strategy:
    1. Try the callable as-is (no behavior change on UTF-8 terminals).
    2. On UnicodeEncodeError, fall back to the terminal's encoding with
       errors='replace' (preserves more chars than ASCII).
    3. If THAT still fails, ASCII-replace as the final safe net.

    This is symmetric to Block H's input-side surrogate sanitization ’'?"
    Bedrock returns valid UTF-8; the *terminal* may not be configured
    for it. Pure platform robustness; no behavioral change otherwise.
    """
    import sys as _sys

    def _safe(text: str) -> None:
        try:
            fn(text)
            return
        except UnicodeEncodeError:
            pass
        try:
            enc = getattr(_sys.stdout, "encoding", None) or "ascii"
            fn(text.encode(enc, "replace").decode(enc, "replace"))
        except (UnicodeEncodeError, LookupError):
            fn(text.encode("ascii", "replace").decode("ascii"))
    return _safe


# ============================================================
# QueryEngine
# ============================================================

class QueryEngine:
    """Main agent loop. Owns the message buffer + iteration budget for one
    `run()` call. Sub-agents (Phase 9) will share the same IterationBudget
    instance via `forkSubagent`-style construction.
    """

    DEFAULT_MAX_TURNS = 50  # v4 in-place default; UI may override per call.

    def __init__(
        self,
        client: Any,
        max_turns: int = DEFAULT_MAX_TURNS,
        budget: Optional[IterationBudget] = None,
        on_stop_check: Optional[Callable[[], bool]] = None,
        skill_manager: Optional[Any] = None,
        agent_kind: str = "parent",
        session_id: Optional[str] = None,
        synthetic_output_tool_name: Optional[str] = None,
        max_structured_output_retries: int = 3,
    ):
        """Construct a QueryEngine.

        Args:
            client: BedrockClient (or mock with the same `chat(...)` shape).
            max_turns: hard upper bound on turns per `run()` call.
            budget: shared IterationBudget. If None, a fresh one is created.
            on_stop_check: optional callable returning True if the user has
                requested a stop (notebook UX). Phase 11 wires this to the
                Stop button.
            skill_manager: optional `skills.manager.SkillManager`. When
                supplied, the engine (a) injects the active skill body into
                the dynamic tail of the system prompt, and (b) appends a
                Hermes-filtered "skills relevant to this task" reminder to
                the first user turn (Phase 10 wiring contract ’'?" Codex
                Phase-10 BLOCKER fix). When None, no skill machinery runs
                ’'?" preserves Phase 1-8 backwards compatibility for tests.
        """
        self.client = client
        self.max_turns = max(1, int(max_turns))
        self.budget = budget if budget is not None else IterationBudget()
        self.on_stop_check = on_stop_check
        self.skill_manager = skill_manager
        # Block B: per-agent attribution key for TOKENS.add(). "parent" by
        # default; sub-agents pass their type-string ("build", "explore",
        # "verify", etc.) via subagent.spawn._new_child_engine.
        self.agent_kind = agent_kind
        # Block B: session_id used by AUDIT.log on each tool dispatch.
        # Block B+ will swap this to the SessionManager-issued id; for
        # now we mint a process-lifetime id so audit lines are at least
        # grouped per-engine.
        if session_id is None:
            import uuid as _uuid
            session_id = _uuid.uuid4().hex[:12]
        self.session_id = session_id

        # Block M-2: structured-output retry guard (PORT_LOG #084 ’'?" Runnable
        # QueryEngine.ts:1004-1048 countToolCalls + MAX_STRUCTURED_OUTPUT_RETRIES).
        # When `synthetic_output_tool_name` is set, the engine counts how many
        # times that tool appears in self.messages during this run() and
        # halts with stop_reason="error_max_structured_output_retries" at the
        # retry limit. Default name=None disables the check (v5 has no
        # built-in structured-output mode; this is a hook for future support).
        self.synthetic_output_tool_name = synthetic_output_tool_name
        self.max_structured_output_retries = max(1, int(max_structured_output_retries))

        self.messages: List[Dict[str, Any]] = []
        # Tool names that have been "discovered" via tool_search this run.
        # Their schemas are added to per-turn `tools=` API param until the
        # run ends. v5 does NOT persist discovery across `run()` calls ’'?" the
        # set is fresh each user message (matches Runnable's per-message
        # discovered set).
        self._discovered_tool_names: Set[str] = set()
        # Block F2 ’'?" per-run BudgetTracker for iteration-budget auto-continuation.
        # Created lazily inside run() when CONFIG.enable_token_budget_continuation
        # is True; reset each run() so continuation state never leaks across
        # user messages.
        self._budget_tracker: Optional[Any] = None

    # ------------------------------------------------------------
    # Public entry: run(...)
    # ------------------------------------------------------------

    def run(
        self,
        user_message: str,
        system_prompt: str,
        tools: List[Any],
        plan_mode: bool = False,
        output_fn: Callable[[str], None] = print,
        thinking_enabled: bool = False,
        thinking_budget: int = 4096,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> QueryResult:
        """Execute the agent loop until a stop condition is reached.

        See class docstring for the IN-SCOPE / OUT-OF-SCOPE list.
        """
        # R-tier R1 PHASE B iter-1 fix: wrap output_fn to swallow
        # UnicodeEncodeError on Windows cp1252 stdout. The agent emits
        # valid UTF-8 (e.g. ’'o. U+2705 in summary blocks); a raw print()
        # on a default-Windows console crashes the entire loop. Block H
        # surrogate sanitization handles INPUT; this is the symmetric
        # output-side robustness. Codex R1 PhaseB iter-1 APPROVE_FIX.
        output_fn = _make_unicode_safe_output_fn(output_fn)
        # Codex Phase-08 finding (high): the discovered-tool set MUST be reset
        # at each run() entry. The contract docstring promises "fresh each
        # user message" but the previous version persisted it across runs,
        # which would silently widen the per-turn tools= payload on later
        # runs. Lock test: test_discovered_tools_reset_between_runs.
        self._discovered_tool_names = set()
        # Block B+ Codex finding #1 (HIGH) lock: reset the per-run cost
        # over-budget warning flag so subsequent run() calls re-emit the
        # warning once each (instead of staying silent for the lifetime
        # of the engine).
        self._warned_over_budget = False
        # Block C ’'?" exec-limit gate (PS#7 fix) + repetition detector.
        # Counters live on the QueryEngine. Codex iter-1 finding #3:
        # unconditional reset at run() entry so counters DON'T leak
        # across run() calls (the v4 contract; sub-agent dispatch is
        # the only legitimate cross-run sharing path, handled via
        # parent_engine forwarding).
        self._exec_call_count = 0  # bash + python_exec only
        self._recent_tool_calls: list = []  # [(name, args_hash), ...]
        # Block F2 ’'?" fresh BudgetTracker per run() so continuation state
        # never leaks across user messages.
        self._budget_tracker = None
        # Block M-1 (PORT_LOG #085) ’'?" Runnable QueryEngine.ts:238 verbatim:
        # discoveredSkillNames.clear() at run() entry. Prevents
        # path/trigger-activated skills from contaminating the next user
        # message's flow. Best-effort; never blocks run() on missing
        # skill_manager.
        try:
            if self.skill_manager is not None and hasattr(
                self.skill_manager, "_pending_activations"
            ):
                with self.skill_manager._pending_lock:
                    self.skill_manager._pending_activations.clear()
        except Exception:
            pass
        # Block M-2 (PORT_LOG #084) ’'?" capture the baseline structured-output
        # tool-call count at run-entry. Calls THIS run = current_count -
        # baseline. Initial count when the run starts may be non-zero if
        # messages were carried over from a previous run() (continued
        # session); the retry limit is per-run, not per-session.
        self._initial_structured_output_calls = (
            count_tool_calls(self.messages, self.synthetic_output_tool_name)
            if self.synthetic_output_tool_name else 0
        )

        # Block C+ ’'?" message rate limit (v4 :8731-8740). Lives on the
        # engine so per-session caps are tracked.
        if not hasattr(self, "_rate_limiter"):
            from ui.approval_dialog import RateLimiter
            from runtime.config import CONFIG as _CFG
            self._rate_limiter = RateLimiter(
                max_per_minute=getattr(_CFG, "max_user_messages_per_minute", 100),
                max_per_session=getattr(_CFG, "max_user_messages_per_session", 1500),
            )
        _rate_msg = self._rate_limiter.check()
        if _rate_msg is not None:
            return QueryResult(
                text=_rate_msg,
                messages=list(self.messages),
                stop_reason="rate_limited",
                turns_used=0,
                budget_used=self.budget.used(),
                error=_rate_msg,
            )

        # Append user turn (Bedrock requires alternation; merge into trailing
        # user if needed ’'?" matches v4 sagemaker_agent.py:8744).
        if self.messages and self.messages[-1].get("role") == "user":
            prev = self.messages[-1]
            prev_content = prev.get("content", "")
            if isinstance(prev_content, str):
                prev["content"] = prev_content + "\n\n" + user_message
            elif isinstance(prev_content, list):
                prev_content.append({"type": "text", "text": user_message})
            else:
                self.messages.append({"role": "user", "content": user_message})
        else:
            self.messages.append({"role": "user", "content": user_message})

        # Defer-import to avoid circular import at module-load.
        from tools.registry import (
            PLAN_MODE_ALLOWED_TOOLS,
            apply_tool_search_deferral,
            find_tool_by_name,
        )
        from tools.tool_search import tool_search_discovered_names

        # Phase 10 wiring (Codex BLOCKER fix): if a SkillManager is bound to
        # this engine, inject (a) the active skill body into the dynamic
        # tail of the system prompt and (b) a Hermes-filtered "skills
        # relevant to this task" reminder onto the first user turn so the
        # model sees the suggestions. The Hermes filter passes the visible
        # tool names so skills with `requires_tools` are pruned when the
        # required tools aren't currently available.
        effective_system_prompt = system_prompt
        # Block G3 ’'?" coordinator-mode prompt augmentation. Default OFF.
        # Only the PARENT agent gets the coordinator block (sub-agents are
        # workers, not coordinators). Best-effort try/except.
        try:
            from runtime.config import CONFIG as _CFG_G3
            if (
                getattr(_CFG_G3, "coordinator_mode_enabled", False)
                and self.agent_kind == "parent"
            ):
                from coordinator.system_prompt import get_coordinator_system_prompt
                from coordinator.user_context import get_coordinator_user_context
                effective_system_prompt = (
                    effective_system_prompt + "\n\n" + get_coordinator_system_prompt()
                )
                # Block G3 iter-2 (Codex iter-1 finding #3 MEDIUM lock):
                # PORT_LOG #093 promises G3-2 user context is INJECTED into
                # the coordinator's first user message. Append it to the
                # trailing user turn (the user_message we just appended).
                # This mirrors Runnable's QueryEngine.ts:302-307 behavior.
                _ws = getattr(_CFG_G3, "workspace", None)
                _ctx_block = get_coordinator_user_context(workspace=_ws)
                if _ctx_block and self.messages and self.messages[-1].get("role") == "user":
                    _last = self.messages[-1]
                    _existing = _last.get("content")
                    _injection = "\n\n" + _ctx_block
                    if isinstance(_existing, str):
                        _last["content"] = _existing + _injection
                    elif isinstance(_existing, list):
                        _last["content"] = list(_existing) + [
                            {"type": "text", "text": _ctx_block}
                        ]
        except Exception as _g3_exc:
            logging.warning(
                "[coordinator-prompt] %s: %s",
                type(_g3_exc).__name__, _g3_exc,
            )

        if self.skill_manager is not None:
            try:
                active_block = self.skill_manager.get_active_skill_prompt(
                    session_id=self.session_id,
                )
                if active_block:
                    # Block G3 iter-2 (Codex iter-1 finding #1 HIGH lock):
                    # append to the existing effective_system_prompt (which
                    # already carries the coordinator block when that's on);
                    # don't reset to bare `system_prompt + active_block` ’'?"
                    # that would silently discard the coordinator block.
                    effective_system_prompt = effective_system_prompt + active_block
                visible_tool_names = {t.name for t in tools}
                relevant = self.skill_manager.discover_relevant(
                    user_message, active_tools=visible_tool_names,
                )
                if relevant:
                    reminder = (
                        "\n\n# Skills Relevant to This Task\n"
                        "Consider using: " + ", ".join(relevant) +
                        "\nUse the `skill` tool to activate one if it matches."
                    )
                    last_user = self.messages[-1]
                    content = last_user.get("content")
                    if isinstance(content, str):
                        last_user["content"] = content + reminder
                    elif isinstance(content, list):
                        content.append({"type": "text", "text": reminder})
            except Exception as exc:  # noqa: BLE001 ’'?" skill machinery never raises into agent loop
                logging.warning("[skill-wiring] %s: %s", type(exc).__name__, exc)

        last_text = ""
        stop_reason = ""
        turns_used = 0

        for turn in range(self.max_turns):
            # User-requested stop (Phase 11 wires this to the Stop button).
            if self.on_stop_check and self.on_stop_check():
                output_fn("[Stopped by user]")
                stop_reason = "user_stop"
                break

            # Block M-2 (PORT_LOG #084) ’'?" structured-output retry-limit
            # guard. When `synthetic_output_tool_name` is configured, count
            # how many times the model produced a malformed structured
            # output (each tool_use of that synthetic tool counts). Halt
            # cleanly at the retry limit instead of looping forever.
            if self.synthetic_output_tool_name:
                _calls_now = count_tool_calls(
                    self.messages, self.synthetic_output_tool_name,
                )
                _calls_this_run = _calls_now - self._initial_structured_output_calls
                if _calls_this_run >= self.max_structured_output_retries:
                    output_fn(
                        f"[error_max_structured_output_retries: "
                        f"failed to provide valid structured output after "
                        f"{self.max_structured_output_retries} attempts]"
                    )
                    stop_reason = "error_max_structured_output_retries"
                    break

            # Budget gate ’'?" shared with sub-agents (Phase 9).
            if not self.budget.consume():
                used, total = self.budget.used(), self.budget.total()
                output_fn(
                    f"[Budget exhausted: {used}/{total} iterations used. "
                    "Adjust IterationBudget or start a new session.]"
                )
                stop_reason = "budget_exhausted"
                break

            # Phase 7 wiring contract: per-turn deferral + discovery merge.
            visible_tools, deferred_names = apply_tool_search_deferral(
                tools, enabled=True,
            )
            if self._discovered_tool_names:
                # Promote previously-discovered tools from deferred ’'+' visible.
                discovered = {n for n in self._discovered_tool_names if n in deferred_names}
                if discovered:
                    promoted = [
                        t for t in tools
                        if t.name in discovered and t.name not in {v.name for v in visible_tools}
                    ]
                    visible_tools = visible_tools + promoted
                    deferred_names = [n for n in deferred_names if n not in discovered]

            # If any names remain deferred, surface them as a system reminder
            # so the model knows they exist and how to load them.
            turn_messages = list(self.messages)
            if deferred_names:
                turn_messages = self._inject_deferred_reminder(turn_messages, deferred_names)

            # Bedrock invocation.
            try:
                response = self.client.chat(
                    messages=turn_messages,
                    system=effective_system_prompt,
                    tools=_build_tools_api_payload(visible_tools),
                    max_tokens=max_tokens,
                    temperature=temperature,
                    thinking_enabled=thinking_enabled,
                    thinking_budget=thinking_budget,
                )
            except Exception as exc:  # noqa: BLE001 ’'?" classify and surface
                category, recovery, debug = ErrorClassifier.classify(exc)
                output_fn(f"[Bedrock {category}: {debug}]")
                if category == BedrockErrorCategory.CONTEXT_OVERFLOW:
                    stop_reason = "context_overflow"
                else:
                    stop_reason = "fatal_error"
                return QueryResult(
                    text=last_text,
                    messages=list(self.messages),
                    stop_reason=stop_reason,
                    turns_used=turns_used,
                    budget_used=self.budget.used(),
                    error=f"{category}: {debug}",
                )

            turns_used += 1

            # Block B (PORT_LOG #039+#040): record token usage + per-agent
            # attribution. "parent" or sub-agent type-string. Best-effort ’'?"
            # never break the agent loop if the singleton import fails.
            try:
                from runtime.tokens import TOKENS as _TOKENS
                _TOKENS.add(
                    response.usage or {},
                    model_id=getattr(self.client, "model_id", None),
                    agent_kind=self.agent_kind,
                )
                try:
                    from runtime.audit import AUDIT as _AUDIT_CHAT
                    _AUDIT_CHAT.log(
                        session_id=self.session_id,
                        action="chat_response",
                        tool_name="(engine)",
                        parameters={
                            "turn": turns_used,
                            "response": {
                                "usage": response.usage or {},
                                "thinking": getattr(response, "thinking", "") or "",
                                "text": response.text or "",
                                "stop_reason": getattr(response, "stop_reason", ""),
                                "tool_calls": [
                                    {
                                        "id": getattr(c, "id", ""),
                                        "name": getattr(c, "name", ""),
                                        "input": getattr(c, "input", {}),
                                    }
                                    for c in (response.tool_calls or [])
                                ],
                            },
                        },
                        result_summary=(
                            f"stop={getattr(response, 'stop_reason', '')}; "
                            f"tools={len(response.tool_calls or [])}; "
                            f"text_chars={len(response.text or '')}; "
                            f"thinking_chars={len(getattr(response, 'thinking', '') or '')}"
                        ),
                        user_approved=False,
                    )
                except Exception:
                    pass
                # Block B+ (PORT_LOG #052): per-turn cost-vs-budget runtime
                # warning. v4 sagemaker_agent.py:8787 prints
                #   `[Cost ${session_cost} passed budget ${limit} ’'?" continuing.]`
                # NOT a hard halt ’'?" per user 2026-05-03 update to plan v3,
                # v5 matches v4 UX: warn and continue. True hard halt is at
                # cloud-budget level (AWS Budget Action / GCP).
                from runtime.config import CONFIG as _CFG
                limit = getattr(_CFG, "session_cost_limit", 0.0)
                # Block B+ Codex finding #1 lock: `>=` so exact-100% trips
                # the warning (`>` would skip parity-100% cases).
                if limit > 0 and _TOKENS.session_cost >= limit:
                    if not getattr(self, "_warned_over_budget", False):
                        output_fn(
                            f"[Cost ${_TOKENS.session_cost:.4f} passed "
                            f"budget ${limit:.2f} ’'?" continuing.]"
                        )
                        self._warned_over_budget = True
            except Exception:
                pass

            # Append assistant turn (text + tool_use blocks, plus thinking).
            assistant_content = self._build_assistant_content(response)
            self.messages.append({"role": "assistant", "content": assistant_content})

            if response.text:
                last_text = response.text

            # Block A ’'?" auto-compact gate. Per-turn check: if the
            # message buffer has crossed the 80% threshold AND the
            # circuit breaker allows another attempt, run Compactor.
            try:
                from core.compactor import Compactor, AUTO_COMPACT
                from runtime.config import CONFIG as _CFG_AC
                _max_ctx = getattr(_CFG_AC, "context_max_tokens", 200_000)
                if Compactor.should_compact(self.messages, _max_ctx):
                    _ok, _why = AUTO_COMPACT.try_attempt()
                    if _ok:
                        _result = Compactor.run(self.client, self.messages, _max_ctx)
                        if _result.success:
                            output_fn(
                                f"[auto-compact] saved "
                                f"{_result.tokens_before - _result.tokens_after:,} "
                                f"tokens; continuing."
                            )
                            self.messages = _result.messages_after
                    else:
                        # Cooldown / cap message ’'?" log once per turn, no
                        # spam since try_attempt returns reason text.
                        output_fn(f"[auto-compact skipped: {_why}]")
            except Exception:
                pass

            # Stop conditions: end_turn / no tool_use blocks ’'+' final answer.
            if not response.tool_calls:
                # Block F2 ’'?" auto-continuation under iteration budget. Only
                # parent agents (not sub-agents) and only when CONFIG flag
                # is opt-in (default OFF per Wave 6 NLT row #21). Cost-cap
                # halt has priority inside check_iteration_budget().
                try:
                    from runtime.config import CONFIG as _CFG_F2
                    if getattr(_CFG_F2, "enable_token_budget_continuation", False):
                        from core.budget_continuation import (
                            check_iteration_budget,
                            create_budget_tracker,
                            ContinueDecision,
                            StopDecision,
                        )
                        if self._budget_tracker is None:
                            self._budget_tracker = create_budget_tracker()
                        _is_sub = self.agent_kind != "parent"
                        _sc = 0.0
                        try:
                            from runtime.tokens import TOKENS as _TOKENS_F2
                            _sc = float(getattr(_TOKENS_F2, "session_cost", 0.0))
                        except Exception:
                            _sc = 0.0
                        _scl = float(getattr(_CFG_F2, "session_cost_limit", 0.0))
                        decision = check_iteration_budget(
                            self._budget_tracker,
                            iter_used=self.budget.used(),
                            iter_total=self.budget.total(),
                            is_subagent=_is_sub,
                            session_cost=_sc,
                            session_cost_limit=_scl,
                        )
                        if isinstance(decision, ContinueDecision):
                            # Surface the assistant's interim text + nudge to keep
                            # working. Continuing the for-loop re-invokes Bedrock.
                            if response.text:
                                output_fn(response.text)
                            self.messages.append({
                                "role": "user",
                                "content": decision.nudge_message,
                            })
                            continue
                        # Codex iter-1 finding #1 lock: surface StopDecision
                        # telemetry. Runnable logs the equivalent completion
                        # event at query.ts:1343-1354. v5 routes through the
                        # AUDIT singleton so /diffs / /regression forensics
                        # can observe budget-driven stops; stderr-style
                        # logging.info also surfaces it for headless runs.
                        if isinstance(decision, StopDecision):
                            _ce = decision.completion_event
                            _reason = decision.reason or ""
                            if _ce is not None or _reason in {"cost_cap", "diminishing", "above_threshold"}:
                                logging.info(
                                    "[budget-continuation] stop reason=%s event=%s",
                                    _reason, _ce,
                                )
                                try:
                                    from runtime.audit import AUDIT as _AUDIT_F2
                                    _AUDIT_F2.log(
                                        session_id=self.session_id,
                                        action="budget_continuation_stop",
                                        tool_name="(engine)",
                                        parameters={"reason": _reason},
                                        result_summary=str(_ce or ""),
                                        user_approved=False,
                                    )
                                except Exception:
                                    pass
                except Exception as _f2_exc:
                    # Codex iter-1 finding #2 lock: best-effort wrap MUST
                    # surface a diagnostic when F2 is opt-in enabled ’'?" silent
                    # fail-closed makes opt-in users see "no auto-continue"
                    # with zero clue why. logging.warning matches the
                    # cost-runtime warning pattern at [Cost ...] above.
                    logging.warning(
                        "[budget-continuation] %s: %s",
                        type(_f2_exc).__name__, _f2_exc,
                    )

                stop_reason = "end_turn"
                if response.text:
                    output_fn(response.text)
                break

            # Tool dispatch ’'?" emit one tool_result per tool_use call.
            tool_results: List[Dict[str, Any]] = []
            for call in response.tool_calls:
                tool = find_tool_by_name(tools, call.name)
                if tool is None:
                    # Unknown tool name ’'?" return error to model so it can
                    # recover (v4 parity: dispatch never raises).
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": f"Error: unknown tool '{call.name}'",
                        "is_error": True,
                    })
                    # Block B (Codex finding #2 HIGH lock): every dispatch
                    # path ’'?" including unknown-tool ’'?" must be audited so
                    # forensics can see what the model attempted to call.
                    try:
                        from runtime.audit import AUDIT as _AUDIT
                        _AUDIT.log(
                            session_id=self.session_id,
                            action="tool_unknown",
                            tool_name=call.name,
                            parameters=call.input or {},
                            result_summary=f"unknown tool '{call.name}'",
                            user_approved=False,
                        )
                    except Exception:
                        pass
                    continue

                # Plan-mode dispatch gate ’'?" strict allowlist by name (v4
                # PLAN_MODE_ALLOWED_TOOLS, sagemaker_agent.py:9390 + 6905).
                # Codex Phase-08 finding (medium): the prior version exempted
                # `always_load=True` tools, which would let `tool_search`
                # itself (or any future always_load mutating tool) execute
                # in plan mode despite v4 forbidding it. The allowlist is
                # defense-in-depth on top of registry filtering: even if a
                # disallowed mutating tool reaches dispatch (e.g. discovered
                # via tool_search after enabled=True), it cannot run.
                # Lock test: test_engine_plan_mode_blocks_always_load_mutating_tool.
                if plan_mode and call.name not in PLAN_MODE_ALLOWED_TOOLS:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": (
                            f"Error: tool '{call.name}' is not in "
                            "PLAN_MODE_ALLOWED_TOOLS; blocked in plan mode."
                        ),
                        "is_error": True,
                    })
                    # Block B (Codex finding #2 HIGH lock): plan-mode
                    # block is an audit-relevant security event.
                    try:
                        from runtime.audit import AUDIT as _AUDIT
                        _AUDIT.log(
                            session_id=self.session_id,
                            action="plan_mode_blocked",
                            tool_name=call.name,
                            parameters=call.input or {},
                            result_summary=(
                                f"plan-mode allowlist blocked '{call.name}'"
                            ),
                            user_approved=False,
                        )
                    except Exception:
                        pass
                    continue

                # Block C ’'?" exec-limit gate (PS#7 fix). Only bash +
                # python_exec count toward this limit. v4 verbatim
                # message at sagemaker_agent.py:9482-9489 ’'?" preserved
                # so the model can recover by switching to non-counted
                # tools.
                if call.name in {"bash", "python_exec"}:
                    from runtime.config import CONFIG as _CFG
                    cap = getattr(_CFG, "max_exec_calls_per_session", 200)
                    if self._exec_call_count >= cap:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": call.id,
                            "content": (
                                f"Blocked: bash + python_exec call limit "
                                f"reached ({cap}/session). "
                                "OTHER TOOLS STILL WORK: read_file, grep, "
                                "glob, edit_file, write_file, notebook_edit, "
                                "task, ask_user, view_image, web_fetch are "
                                "NOT counted by this limit."
                            ),
                            "is_error": True,
                        })
                        continue

                # Block C ’'?" repetition detector. Same (tool_name,
                # args_hash) appearing 3+ times in the last 6 calls is
                # almost always a stuck loop. v4 sagemaker_agent.py:9156-9180
                # threshold=2 (block on 3rd duplicate).
                import hashlib as _hashlib
                import json as _json
                try:
                    _args_hash = _hashlib.sha256(
                        _json.dumps(call.input or {}, sort_keys=True, default=str).encode()
                    ).hexdigest()[:12]
                except Exception:
                    _args_hash = ""
                _key = (call.name, _args_hash)
                _recent = self._recent_tool_calls[-6:]
                if _recent.count(_key) >= 2:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": (
                            f"Blocked: same call to '{call.name}' with "
                            f"identical arguments has been issued 3 times "
                            "in a row. This is almost always a stuck loop. "
                            "Try a different approach, different arguments, "
                            "or use ask_user to clarify."
                        ),
                        "is_error": True,
                    })
                    continue
                # Track this call (rolling window of last 12).
                self._recent_tool_calls.append(_key)
                if len(self._recent_tool_calls) > 12:
                    self._recent_tool_calls = self._recent_tool_calls[-12:]

                # Block C ’'?" JSON-repair tool args before dispatch. If
                # Bedrock streamed back malformed JSON in tool_use.input,
                # try to recover gracefully instead of falling through
                # to a tool-side type error.
                _repaired_input = call.input
                if isinstance(call.input, str):
                    # When tool_use.input arrives as a JSON string (some
                    # Bedrock variants), parse + repair before dispatch.
                    try:
                        from security.json_repair import repair_tool_call_arguments
                        _repaired_input = repair_tool_call_arguments(call.input)
                    except Exception:
                        _repaired_input = {}

                # Block C+ ’'?" approval gate. When CONFIG.require_tool_approval
                # AND tool.requires_approval are BOTH True (and we're not
                # in mock_mode for tests), surface a PermissionDialog
                # and block until decided. always-allow decisions stick
                # on CONFIG._always_allowed[tool.name]. Mock detection
                # checks the BedrockClient instance (not CONFIG) because
                # tests construct their own client without flipping the
                # global CONFIG.mock_mode flag.
                from runtime.config import CONFIG as _CFG_AT
                _is_mock = bool(
                    getattr(_CFG_AT, "mock_mode", False)
                    or getattr(self.client, "mock_mode", False)
                )
                if (not _is_mock
                        and getattr(_CFG_AT, "require_tool_approval", False)
                        and getattr(tool, "requires_approval", False)):
                    if not hasattr(_CFG_AT, "_always_allowed"):
                        _CFG_AT._always_allowed = {}
                    if not _CFG_AT._always_allowed.get(call.name):
                        try:
                            from ui.approval_dialog import PermissionDialog
                            _model_reason = ""
                            if isinstance(_repaired_input, dict):
                                _model_reason = str(_repaired_input.get("reason", ""))
                            # Block C+ Codex iter-1 finding #1 (HIGH) lock:
                            # for edit_file / write_file, render an inline
                            # diff for the approval body so users see the
                            # actual change before approving (Phase-4
                            # ADR-010 commitment).
                            _diff_html = None
                            if call.name in {"edit_file", "write_file"} and isinstance(_repaired_input, dict):
                                try:
                                    from ui.diff_widget import (
                                        render_inline_diff,
                                        render_new_file_diff,
                                    )
                                    import os as _os_diff
                                    _fp = _repaired_input.get("file_path", "")
                                    if call.name == "edit_file":
                                        _old = _repaired_input.get("old_string", "")
                                        _new = _repaired_input.get("new_string", "")
                                        if _fp and _os_diff.path.isfile(_fp):
                                            with open(_fp, "r", encoding="utf-8", errors="replace") as _f:
                                                _before = _f.read()
                                            _after = _before.replace(_old, _new, 1)
                                            _diff_html = render_inline_diff(_fp, _before, _after)
                                    else:  # write_file
                                        _content = _repaired_input.get("content", "")
                                        _mode = _repaired_input.get("mode", "write")
                                        if _fp and _os_diff.path.isfile(_fp) and _mode == "write":
                                            with open(_fp, "r", encoding="utf-8", errors="replace") as _f:
                                                _before = _f.read()
                                            _diff_html = render_inline_diff(_fp, _before, _content)
                                        else:
                                            _diff_html = render_new_file_diff(_fp, _content)
                                except Exception:
                                    _diff_html = None
                            _dlg = PermissionDialog(
                                tool_name=call.name,
                                parameters=_repaired_input or {},
                                reason=_model_reason,
                                diff_html=_diff_html,
                            )
                            _result = _dlg.prompt()
                            if not _result.approved:
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": call.id,
                                    "content": (
                                        f"User denied approval for "
                                        f"`{call.name}`: {_result.reason}"
                                    ),
                                    "is_error": True,
                                })
                                continue
                            # Approved ’'?" sticky if user clicked Always.
                        except Exception as _approval_exc:
                            logging.warning(
                                f"approval gate failed: {_approval_exc}; "
                                "defaulting to deny"
                            )
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": call.id,
                                "content": (
                                    f"Approval gate error for `{call.name}`; "
                                    f"defaulting to deny."
                                ),
                                "is_error": True,
                            })
                            continue

                # Execute. Tool implementations may raise; we trap and surface
                # the error to the model rather than the human user.
                # `parent_engine` is passed for Phase 9 task tool ’'?" the sub-agent
                # spawn needs the parent's IterationBudget + BedrockClient (ADR-015).
                try:
                    if call.name in {"bash", "python_exec"}:
                        self._exec_call_count += 1
                    raw = tool.execute(_repaired_input, context={
                        "active_tools": tools,
                        "plan_mode": plan_mode,
                        "parent_engine": self,
                        "parent_depth": getattr(self, "_subagent_depth", 0),
                        # Block I-1/I-5: edit_file + write_file consume this
                        # to auto-activate skills with `paths:` frontmatter.
                        "skill_manager": self.skill_manager,
                        "session_id": self.session_id,
                    })
                    text = _coerce_tool_result_to_text(raw)
                    text = _truncate_tool_result(text, tool.max_result_size_chars)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": text,
                    })
                    # Block B (PORT_LOG #043): audit-log every tool dispatch
                    # so /diffs / /regression / forensics have a tamper-hashed
                    # trail. Best-effort.
                    try:
                        from runtime.audit import AUDIT as _AUDIT
                        _AUDIT.log(
                            session_id=self.session_id,
                            action="tool_dispatch",
                            tool_name=call.name,
                            parameters=call.input or {},
                            result_summary=text[:500] if isinstance(text, str) else "",
                            user_approved=True,
                        )
                    except Exception:
                        pass
                    # Phase 7 wiring: extract discovered names from tool_search
                    # results and add to the next turn's tools= payload.
                    if call.name == "tool_search":
                        discovered = tool_search_discovered_names(text)
                        if discovered:
                            self._discovered_tool_names.update(discovered)
                except Exception as exc:  # noqa: BLE001 ’'?" surface to model
                    logging.warning(
                        "[query_engine] tool '%s' raised %s: %s",
                        call.name, type(exc).__name__, exc,
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": f"Error: {type(exc).__name__}: {exc}",
                        "is_error": True,
                    })
                    # Audit the failed dispatch too so forensics can see what
                    # was attempted (sanitized parameters; no result body).
                    try:
                        from runtime.audit import AUDIT as _AUDIT
                        _AUDIT.log(
                            session_id=self.session_id,
                            action="tool_error",
                            tool_name=call.name,
                            parameters=call.input or {},
                            result_summary=f"{type(exc).__name__}: {exc}",
                            user_approved=False,
                        )
                    except Exception:
                        pass

            # Append the tool_results as a user turn (Bedrock convention).
            self.messages.append({"role": "user", "content": tool_results})

        else:  # for-loop fell through without break
            stop_reason = "max_turns"
            output_fn(f"[Max turns reached: {self.max_turns}]")

        return QueryResult(
            text=last_text,
            messages=list(self.messages),
            stop_reason=stop_reason or "end_turn",
            turns_used=turns_used,
            budget_used=self.budget.used(),
        )

    # ------------------------------------------------------------
    # Internal: assemble assistant turn content from a Bedrock Response
    # ------------------------------------------------------------

    @staticmethod
    def _build_assistant_content(response: Any) -> List[Dict[str, Any]]:
        """Construct a Bedrock-shaped assistant content list from a Response.

        Order: thinking blocks (if any) ’'+' text ’'+' tool_use. The thinking
        block is preserved so the next turn's API call carries it back to
        the model (Bedrock requires this for extended thinking continuity).
        """
        blocks: List[Dict[str, Any]] = []
        thinking = getattr(response, "thinking", "") or ""
        if thinking:
            blocks.append({"type": "thinking", "thinking": thinking})
        if response.text:
            blocks.append({"type": "text", "text": response.text})
        for call in response.tool_calls:
            blocks.append({
                "type": "tool_use",
                "id": call.id,
                "name": call.name,
                "input": call.input,
            })
        return blocks

    # ------------------------------------------------------------
    # Internal: deferred-tools system reminder injection
    # ------------------------------------------------------------

    @staticmethod
    def _inject_deferred_reminder(
        messages: List[Dict[str, Any]],
        deferred_names: List[str],
    ) -> List[Dict[str, Any]]:
        """Append a `<system-reminder>` block listing deferred tool names so
        the model knows what's available via tool_search.

        The reminder is injected as a transient text block on the trailing
        user turn ’'?" it does not mutate `self.messages`, so it does not leak
        into subsequent turns once the model has loaded the schemas it needs.
        """
        if not deferred_names:
            return messages
        reminder = (
            "<system-reminder>\n"
            "The following deferred tools are available via tool_search. Their schemas "
            "are NOT loaded ’'?" calling them directly will fail. Use tool_search with "
            "query \"select:<name>[,<name>...]\" to load tool schemas before calling them:\n"
            + "\n".join(sorted(deferred_names))
            + "\n</system-reminder>"
        )
        # Transient append: copy the trailing user message and add the reminder
        # as an extra text block. If the trailing turn is not user-role, we
        # append a fresh user message ’'?" but this should never happen because
        # the loop only invokes Bedrock right after a user turn or tool_results.
        out = list(messages)
        if not out or out[-1].get("role") != "user":
            out.append({"role": "user", "content": [{"type": "text", "text": reminder}]})
            return out
        last = dict(out[-1])
        content = last.get("content")
        if isinstance(content, str):
            last["content"] = [
                {"type": "text", "text": content},
                {"type": "text", "text": reminder},
            ]
        elif isinstance(content, list):
            last["content"] = list(content) + [{"type": "text", "text": reminder}]
        else:
            last["content"] = [{"type": "text", "text": reminder}]
        out[-1] = last
        return out


# ============================================================
# Single-turn helper for unit tests
# ============================================================

def run_one_turn(
    client: Any,
    messages: List[Dict[str, Any]],
    system_prompt: str,
    tools: List[Any],
    max_tokens: int = 4096,
    temperature: float = 0.0,
    thinking_enabled: bool = False,
    thinking_budget: int = 4096,
) -> Any:
    """Run a single Bedrock invocation with Phase 7 deferral applied.

    Returns the raw `Response` object. Tests use this to assert wiring without
    spinning up the full multi-turn loop.
    """
    from tools.registry import apply_tool_search_deferral

    visible_tools, _deferred = apply_tool_search_deferral(tools, enabled=True)
    return client.chat(
        messages=messages,
        system=system_prompt,
        tools=_build_tools_api_payload(visible_tools),
        max_tokens=max_tokens,
        temperature=temperature,
        thinking_enabled=thinking_enabled,
        thinking_budget=thinking_budget,
    )
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

codex
The updated test is materially different from iter-1: it now lowers the threshold and runs a second turn. Iƒ?Tm checking the exact engine flow now, especially whether `Agent.run` reuses the same `QueryEngine` message buffer and whether the auto-compact signal is strong enough.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=0; Get-Content compact_v5/MAIN/agent/core/query_engine.py | ForEach-Object { $i++; if ($i -ge 520 -and $i -le 660) { '"'{0,5}: {1}' -f "'$i, $_ } }' in D:\Github\sagemaker-coding-agent
2026-05-03T23:26:33.364303Z ERROR codex_core::tools::router: error=`"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=0; Get-Content compact_v5/MAIN/agent/core/query_engine.py | ForEach-Object { $i++; if ($i -ge 520 -and $i -le 660) { '"'{0,5}: {1}' -f "'$i, $_ } }'` rejected: blocked by policy
2026-05-03T23:26:33.368387Z ERROR codex_core::tools::router: error=`"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=0; Get-Content compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py | ForEach-Object { $i++; if ($i -ge 70 -and $i -le 230) { '"'{0,5}: {1}' -f "'$i, $_ } }'` rejected: blocked by policy
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=0; Get-Content compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py | ForEach-Object { $i++; if ($i -ge 70 -and $i -le 230) { '"'{0,5}: {1}' -f "'$i, $_ } }' in D:\Github\sagemaker-coding-agent
 declined in 0ms:
`"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=0; Get-Content compact_v5/MAIN/agent/core/query_engine.py | ForEach-Object { $i++; if ($i -ge 520 -and $i -le 660) { '"'{0,5}: {1}' -f "'$i, $_ } }'` rejected: blocked by policy
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content compact_v5/MAIN/agent/agent.py' in D:\Github\sagemaker-coding-agent
 declined in 0ms:
`"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=0; Get-Content compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py | ForEach-Object { $i++; if ($i -ge 70 -and $i -le 230) { '"'{0,5}: {1}' -f "'$i, $_ } }'` rejected: blocked by policy
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"class Agent|QueryEngine|def run\\(\" compact_v5/MAIN/agent -g \"*.py\"" in D:\Github\sagemaker-coding-agent
 succeeded in 1715ms:
"""V5 agent.py ’'?" public Agent class (Phase 11, ADR-017).

Thin wrapper that composes the Phase 1-10 surfaces:
  - `runtime.bedrock_client.BedrockClient` (Phase 1)
  - `core.budget.IterationBudget` (Phase 8)
  - `core.query_engine.QueryEngine` (Phase 8)
  - optional `skills.manager.SkillManager` (Phase 10)

Public methods:
  - `run(message)` ’'?" execute a single user turn, return a `QueryResult`.
  - `stop()` ’'?" request the next turn to halt cleanly.
  - `clear()` ’'?" reset conversation buffer (does NOT reset budget by default;
                callers can pass `reset_budget=True` to also reset the budget).

This is the surface chat.ipynb (Phase 11) drives. It does NOT re-implement
agent logic ’'?" every behavior lives in its own module (Phase 8-10).

PORT_LOG: #031.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, List, Optional

from core import IterationBudget, QueryEngine
from core.query_engine import QueryResult


# ============================================================
# Block B+ helper ’'?" load AGENT_STATUS.md if present
# ============================================================

def _load_agent_status_text() -> Optional[str]:
    """Return the contents of `<workspace>/AGENT_STATUS.md`, or None.

    Honors CONFIG.enable_status_doc + CONFIG.status_doc + CONFIG.workspace.
    Returns None silently when the file is missing or disabled ’'?" the
    handoff path is a v4 capability that gracefully degrades.
    """
    import os
    from runtime.config import CONFIG
    if not getattr(CONFIG, "enable_status_doc", True):
        return None
    status_path = os.path.join(CONFIG.workspace, CONFIG.status_doc)
    if not os.path.isfile(status_path):
        return None
    try:
        with open(status_path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    text = text.strip()
    if not text:
        return None
    # Cap at ~8 KB so a runaway status doc can't blow out the prompt.
    if len(text) > 8000:
        text = text[:8000] + "\n\n’'?Žø[truncated; AGENT_STATUS.md exceeds 8 KB]"
    return text


class Agent:
    """Minimal public Agent wrapping the Phase 8-10 surfaces."""

    def __init__(
        self,
        client: Any,
        max_turns: int = 50,
        budget: Optional[IterationBudget] = None,
        skill_manager: Optional[Any] = None,
        on_stop_check: Optional[Callable[[], bool]] = None,
        system_prompt: Optional[str] = None,
        plan_mode: bool = False,
        thinking_enabled: bool = False,
        thinking_budget: int = 4096,
    ):
        """Construct the Agent.

        Args:
            client: BedrockClient (or mock with the same `chat(...)` shape).
            max_turns: hard upper bound on turns per `run()` call.
            budget: shared IterationBudget. If None, a fresh one is created.
            skill_manager: optional SkillManager for active-skill prompt
                injection + auto-trigger reminder (Phase 10 wiring).
            on_stop_check: callable returning True if user pressed Stop.
            system_prompt: override the default `prompt.build_system_prompt`.
                If None, the static v5 prompt is used.
            plan_mode: when True, the dispatch gate enforces the v4
                PLAN_MODE_ALLOWED_TOOLS read-only allowlist.
            thinking_enabled: send thinking config on every Bedrock call.
            thinking_budget: max tokens for thinking (PS Issue #4 surfaces this).
        """
        self.client = client
        self.budget = budget if budget is not None else IterationBudget()
        self.skill_manager = skill_manager
        self._stop_requested = False

        def _combined_stop():
            if self._stop_requested:
                return True
            if on_stop_check is not None and on_stop_check():
                return True
            return False

        self._engine = QueryEngine(
            client=client,
            max_turns=max_turns,
            budget=self.budget,
            on_stop_check=_combined_stop,
            skill_manager=skill_manager,
        )
        self._system_prompt = system_prompt
        self._plan_mode = bool(plan_mode)
        self._thinking_enabled = bool(thinking_enabled)
        self._thinking_budget = int(thinking_budget)
        # Block B+: AGENT_STATUS auto-load runs once on the first run() call.
        self._agent_status_loaded = False
        self._agent_status_text: Optional[str] = None

    # ------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------

    def run(
        self,
        message: str,
        tools: Optional[List[Any]] = None,
        output_fn: Callable[[str], None] = print,
    ) -> QueryResult:
        """Execute a single user turn. Returns the `QueryResult`."""
        # Lazy-import to avoid circular import on package init
        from prompt import build_system_prompt, CACHE_BOUNDARY
        from tools import all_registered

        # Block B+: AGENT_STATUS auto-load on first run() call. Reads
        # `<workspace>/AGENT_STATUS.md` (or CONFIG.status_doc) and
        # appends it to the dynamic tail of the system prompt so the
        # agent picks up handoff context from a previous session.
        # Reads file ONCE per Agent instance (idempotent).
        if not self._agent_status_loaded and self._system_prompt is None:
            try:
                self._agent_status_text = _load_agent_status_text()
            except Exception:
                self._agent_status_text = None
            self._agent_status_loaded = True

        system_prompt = self._system_prompt or build_system_prompt(ctx={})
        if self._agent_status_text:
            # Append to the dynamic tail (after CACHE_BOUNDARY) so the
            # cache-aware prefix replay (Block G2 territory) still works.
            if CACHE_BOUNDARY in system_prompt:
                system_prompt = (
                    system_prompt + "\n\n## Handoff: AGENT_STATUS\n\n"
                    + self._agent_status_text
                )
            else:
                system_prompt = (
                    system_prompt + CACHE_BOUNDARY
                    + "\n\n## Handoff: AGENT_STATUS\n\n"
                    + self._agent_status_text
                )
        active_tools = list(tools) if tools is not None else all_registered()

        self._stop_requested = False  # reset between runs
        # R-tier R1 PHASE A iter-2 fix: propagate CONFIG.max_tokens +
        # CONFIG.temperature into the per-call Bedrock kwargs. Without
        # this, R-tier tests that override CONFIG.max_tokens (to cap
        # per-turn output cost) would have no effect because QueryEngine.run
        # defaults to max_tokens=4096 / temperature=0.0.
        from runtime.config import CONFIG as _CFG
        _max_tokens = getattr(_CFG, "max_tokens", 4096)
        _temperature = getattr(_CFG, "temperature", 0.0)
        result = self._engine.run(
            user_message=message,
            system_prompt=system_prompt,
            tools=active_tools,
            plan_mode=self._plan_mode,
            output_fn=output_fn,
            thinking_enabled=self._thinking_enabled,
            thinking_budget=self._thinking_budget,
            max_tokens=_max_tokens,
            temperature=_temperature,
        )
        return result

    def stop(self) -> None:
        """Request the next-turn checkpoint to break out of the loop."""
        self._stop_requested = True

    def clear(self, reset_budget: bool = False) -> None:
        """Reset the conversation buffer. Optionally also reset the budget.

        By default the budget is preserved across `clear()` so a user who
        wants a fresh conversation but still respects the cost ceiling
        doesn't have to pass anything special. Pass `reset_budget=True`
        for the more aggressive reset.
        """
        self._engine.messages = []
        self._engine._discovered_tool_names = set()
        if reset_budget:
            self.budget.reset()

    # ------------------------------------------------------------
    # Read-only views (used by Phase 11 widgets)
    # ------------------------------------------------------------

    @property
    def messages(self) -> list:
        """Snapshot of the conversation buffer (for the chat UI to render)."""
        return list(self._engine.messages)

    @property
    def thinking_enabled(self) -> bool:
        return self._thinking_enabled

    @property
    def thinking_budget(self) -> int:
        return self._thinking_budget

    def set_thinking(self, enabled: bool, budget: Optional[int] = None) -> None:
        """Update thinking-mode settings (PS Issue #4 UI hook)."""
        self._thinking_enabled = bool(enabled)
        if budget is not None:
            self._thinking_budget = int(budget)
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 2444ms:
compact_v5/MAIN/agent\agent.py:6:  - `core.query_engine.QueryEngine` (Phase 8)
compact_v5/MAIN/agent\agent.py:24:from core import IterationBudget, QueryEngine
compact_v5/MAIN/agent\agent.py:60:class Agent:
compact_v5/MAIN/agent\agent.py:103:        self._engine = QueryEngine(
compact_v5/MAIN/agent\agent.py:122:    def run(
compact_v5/MAIN/agent\agent.py:166:        # per-turn output cost) would have no effect because QueryEngine.run
compact_v5/MAIN/agent\prompt\sections.py:227:    Phase 8 will wire this into the QueryEngine's compaction handler.
compact_v5/MAIN/agent\core\__init__.py:4:  - core/query_engine.py : main agent loop (Runnable QueryEngine.ts adaptation)
compact_v5/MAIN/agent\core\__init__.py:44:from .query_engine import QueryEngine, run_one_turn, count_tool_calls  # noqa: F401
compact_v5/MAIN/agent\core\query_engine.py:3:Per ADR-014: minimal, focused port of Runnable's `QueryEngine.ts` (1295 LOC)
compact_v5/MAIN/agent\core\query_engine.py:56:    """Outcome of a `QueryEngine.run(...)` call.
compact_v5/MAIN/agent\core\query_engine.py:114:    at QueryEngine.ts:1004-1048. Used by the structured-output retry-limit
compact_v5/MAIN/agent\core\query_engine.py:188:# QueryEngine
compact_v5/MAIN/agent\core\query_engine.py:191:class QueryEngine:
compact_v5/MAIN/agent\core\query_engine.py:211:        """Construct a QueryEngine.
compact_v5/MAIN/agent\core\query_engine.py:247:        # QueryEngine.ts:1004-1048 countToolCalls + MAX_STRUCTURED_OUTPUT_RETRIES).
compact_v5/MAIN/agent\core\query_engine.py:273:    def run(
compact_v5/MAIN/agent\core\query_engine.py:308:        # Counters live on the QueryEngine. Codex iter-1 finding #3:
compact_v5/MAIN/agent\core\query_engine.py:318:        # Block M-1 (PORT_LOG #085) ƒ?" Runnable QueryEngine.ts:238 verbatim:
compact_v5/MAIN/agent\core\query_engine.py:409:                # This mirrors Runnable's QueryEngine.ts:302-307 behavior.
compact_v5/MAIN/agent\subagent\spawn.py:23:    parent = QueryEngine(client=..., budget=IterationBudget())
compact_v5/MAIN/agent\subagent\spawn.py:69:    """Construct a fresh QueryEngine that shares the parent's IterationBudget.
compact_v5/MAIN/agent\subagent\spawn.py:80:    from core.query_engine import QueryEngine
compact_v5/MAIN/agent\subagent\spawn.py:81:    return QueryEngine(
compact_v5/MAIN/agent\subagent\spawn.py:230:    # IF the child itself dispatches `task`, the QueryEngine's tool-dispatch
compact_v5/MAIN/agent\core\errors.py:12:  - QueryEngine can import without pulling boto3 transitively
compact_v5/MAIN/agent\core\compactor.py:509:    def run(
compact_v5/MAIN/agent\subagent\agent_types.py:60:class AgentType:
compact_v5/MAIN/agent\core\budget_continuation.py:46:    One instance per QueryEngine.run() call. Sub-agents do NOT get one ƒ?" F2
compact_v5/MAIN/agent\tools\task.py:22:the parent QueryEngine via `context["parent_engine"]` so the child can share
compact_v5/MAIN/agent\tools\task.py:86:      - context["parent_engine"]: the parent QueryEngine. Used to (a) share
compact_v5/MAIN/agent\ui\approval_dialog.py:311:    Used at QueryEngine.run() entry. When rate exceeded, run() returns
compact_v5/MAIN/agent\tools\_file_read_tracking.py:14:into the QueryEngine session state. The 4 tool modules will switch
compact_v5/MAIN/agent\tests\integration\test_agent_max_tokens_propagation.py:2:CONFIG.max_tokens + CONFIG.temperature into the QueryEngine.run call,
compact_v5/MAIN/agent\tests\integration\test_agent_max_tokens_propagation.py:6:output cost) would have no effect because QueryEngine.run defaults to
compact_v5/MAIN/agent\tests\integration\test_agent_max_tokens_propagation.py:42:            # Return a minimal end_turn response shape so QueryEngine
compact_v5/MAIN/agent\tests\integration\test_agent_max_tokens_propagation.py:71:    """If CONFIG.max_tokens is missing/falsy, fall back to QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_a.py:439:    invoked from QueryEngine.run() per turn ƒ?" not just helper-only.
compact_v5/MAIN/agent\tests\integration\test_block_a.py:443:    from core.query_engine import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_a.py:448:    engine = QueryEngine(client=client, max_turns=2)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:410:# Wiring lock ƒ?" TOKENS.add fires on QueryEngine response (mock client)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:497:    # Dispatch an unknown tool via QueryEngine.
compact_v5/MAIN/agent\tests\integration\test_block_b.py:499:    from core.query_engine import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_b.py:518:    engine = QueryEngine(client=client, max_turns=3)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:545:    from core.query_engine import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_b.py:575:    engine = QueryEngine(client=client, max_turns=3)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:607:    from core.query_engine import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_b.py:625:    engine = QueryEngine(client=client, max_turns=1)
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:169:    """`Agent.stop()` mid-loop sets a flag; QueryEngine respects it
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:278:# Sanity: rate limiter wired into QueryEngine.run() entry
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:285:    from core.query_engine import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:289:    engine = QueryEngine(client=client, max_turns=2)
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:314:    from core.query_engine import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:370:    engine = QueryEngine(client=client, max_turns=3)
compact_v5/MAIN/agent\tests\integration\test_block_c.py:30:    from core.query_engine import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_c.py:61:    engine = QueryEngine(client=client, max_turns=10)
compact_v5/MAIN/agent\tests\integration\test_block_c.py:93:    from core.query_engine import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_c.py:120:    engine = QueryEngine(client=client, max_turns=10)
compact_v5/MAIN/agent\tests\integration\test_block_c.py:467:    from core.query_engine import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_c.py:470:    engine = QueryEngine(client=client, max_turns=2)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:215:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:228:        engine = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:252:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:267:        engine = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:285:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:303:        engine = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:326:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:338:    engine = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:353:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:373:        engine = QueryEngine(client=client, max_turns=10, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:390:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:402:        engine = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:430:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:449:        engine = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:485:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:507:        engine = QueryEngine(client=client, max_turns=2, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:653:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_f2.py:667:        engine = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_block_g.py:103:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g.py:112:    parent = QueryEngine(client=client, max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:145:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g.py:164:    parent = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_block_g.py:237:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g.py:242:    parent = QueryEngine(client=client, max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:269:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g.py:274:    parent = QueryEngine(client=_ScriptedClient([]), max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:288:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g.py:296:    parent = QueryEngine(client=client, max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:326:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g.py:330:    parent = QueryEngine(client=_ScriptedClient([]), max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:372:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g.py:401:        parent = QueryEngine(client=client, max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:431:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g.py:449:    parent = QueryEngine(client=_SnoopClient(), max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:467:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g.py:485:    parent = QueryEngine(client=_SnoopClient(), max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:496:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g.py:520:        parent = QueryEngine(client=_SnoopClient(), max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:548:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g.py:567:    parent = QueryEngine(client=_SnoopClient(), max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:630:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g.py:648:    parent = QueryEngine(client=_SnoopClient(), max_turns=5,
compact_v5/MAIN/agent\tests\integration\test_block_g.py:682:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g.py:689:    parent = QueryEngine(client=client, max_turns=200,
compact_v5/MAIN/agent\tests\parity\test_parity_non_critical.py:145:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\parity\test_parity_non_critical.py:148:    parent = QueryEngine(client=None, max_turns=1, budget=IterationBudget())
compact_v5/MAIN/agent\tests\parity\test_parity_non_critical.py:162:    from core import QueryEngine
compact_v5/MAIN/agent\tests\parity\test_parity_non_critical.py:175:    eng = QueryEngine(client=_C(), max_turns=3)
compact_v5/MAIN/agent\tests\parity\test_thin_slice.py:20:  09. Phase 8 ƒ?" End-to-end QueryEngine: user ƒ+' tool_use ƒ+' tool_result ƒ+' final.
compact_v5/MAIN/agent\tests\parity\test_thin_slice.py:227:# Scenario 09 ƒ?" Phase 8 end-to-end QueryEngine
compact_v5/MAIN/agent\tests\parity\test_thin_slice.py:231:    from core import QueryEngine
compact_v5/MAIN/agent\tests\parity\test_thin_slice.py:238:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\parity\test_thin_slice.py:256:    from core import QueryEngine
compact_v5/MAIN/agent\tests\parity\test_thin_slice.py:264:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:159:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:181:        parent = QueryEngine(client=_SnoopClient(), max_turns=2,
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:194:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:216:        parent = QueryEngine(client=_SnoopClient(), max_turns=2,
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:236:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:273:        parent = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:349:    #093 promises this ƒ?" Runnable wires it the same way at QueryEngine.ts:302-307.
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:351:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:373:        parent = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:412:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:435:        child = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:474:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_g3.py:497:        child = QueryEngine(
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:121:    from core import QueryEngine
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:128:    eng = QueryEngine(client=client, max_turns=3)
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:141:    from core import QueryEngine
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:156:    eng = QueryEngine(client=client, max_turns=3)
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:221:    from core import QueryEngine
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:229:    eng = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:300:    from core import QueryEngine
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:307:    eng = QueryEngine(client=_OverflowClient(), max_turns=3)
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:318:    from core import QueryEngine
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:333:    eng = QueryEngine(client=client, max_turns=3)
compact_v5/MAIN/agent\tests\integration\test_block_h_plus.py:290:        def run(self, *a, **kw):
compact_v5/MAIN/agent\tests\integration\test_block_h_plus.py:291:            from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_j_ship_gate.py:224:    and the assistant content must mirror QueryEngine's _build_assistant_content
compact_v5/MAIN/agent\tests\integration\test_block_j_ship_gate.py:267:    # Build assistant content like QueryEngine._build_assistant_content:
compact_v5/MAIN/agent\tests\integration\test_block_j_ship_gate.py:301:    HIGH #2): drive QueryEngine end-to-end across TWO turns, verify the
compact_v5/MAIN/agent\tests\integration\test_block_j_ship_gate.py:310:    QueryEngine ƒ?" calling BedrockClient.chat() directly skips that path.
compact_v5/MAIN/agent\tests\integration\test_block_j_ship_gate.py:314:      - using Agent.run() (QueryEngine) which exercises the SAME compaction
compact_v5/MAIN/agent\tests\integration\test_block_m.py:4:Source: Runnable QueryEngine.ts:197 (discoveredSkillNames Set) + :238
compact_v5/MAIN/agent\tests\integration\test_block_m.py:147:    discoveredSkillNames Set at QueryEngine.ts:197). The list is cleared
compact_v5/MAIN/agent\tests\integration\test_block_m.py:148:    at run() entry per Runnable QueryEngine.ts:238 verbatim ƒ?" prevents
compact_v5/MAIN/agent\tests\integration\test_block_m.py:152:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_m.py:173:    engine = QueryEngine(client=client, max_turns=2, skill_manager=sm)
compact_v5/MAIN/agent\tests\integration\test_block_m.py:179:        "(Block M-1, Runnable QueryEngine.ts:238 parity)"
compact_v5/MAIN/agent\tests\integration\test_block_m.py:193:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_m.py:204:    engine = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_block_m.py:231:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_m.py:244:    engine = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_block_m.py:269:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_m.py:276:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_block_m.py:291:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_m.py:293:    e1 = QueryEngine(client=_ScriptedClient([]), max_structured_output_retries=0)
compact_v5/MAIN/agent\tests\integration\test_block_m.py:295:    e2 = QueryEngine(client=_ScriptedClient([]), max_structured_output_retries=-5)
compact_v5/MAIN/agent\tests\integration\test_block_m.py:297:    e3 = QueryEngine(client=_ScriptedClient([]), max_structured_output_retries=10)
compact_v5/MAIN/agent\tests\integration\test_block_m.py:306:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_block_m.py:322:    engine = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_build_telemetry.py:155:    """R-tier telemetry lock: QueryEngine writes chat_response payloads under
compact_v5/MAIN/agent\tests\integration\test_skills.py:212:# Codex Phase-10 BLOCKER lock: SkillManager wired into QueryEngine.run()
compact_v5/MAIN/agent\tests\integration\test_skills.py:217:    QueryEngine and a skill is active, the active skill body MUST be
compact_v5/MAIN/agent\tests\integration\test_skills.py:219:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_skills.py:246:    engine = QueryEngine(client=client, max_turns=2, budget=IterationBudget(),
compact_v5/MAIN/agent\tests\integration\test_skills.py:259:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_skills.py:291:    engine = QueryEngine(client=client, max_turns=2, budget=IterationBudget(),
compact_v5/MAIN/agent\tests\integration\test_subagent.py:63:    """Phase 9 acceptance criterion: the child QueryEngine's `budget`
compact_v5/MAIN/agent\tests\integration\test_subagent.py:66:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:70:    parent = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_subagent.py:89:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:92:    parent = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_subagent.py:121:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:125:    parent = QueryEngine(client=client, max_turns=5, budget=IterationBudget())
compact_v5/MAIN/agent\tests\integration\test_subagent.py:146:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:149:    parent = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_subagent.py:165:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:174:    parent = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_subagent.py:224:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:227:    parent = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_subagent.py:245:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:251:    parent = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_subagent.py:265:# Test 10 ƒ?" end-to-end via QueryEngine: model calls task tool
compact_v5/MAIN/agent\tests\integration\test_subagent.py:269:    """Model in turn 1 calls `task`. The QueryEngine dispatches it; the task
compact_v5/MAIN/agent\tests\integration\test_subagent.py:272:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:288:    parent = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_subagent.py:316:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:319:    parent = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_subagent.py:334:    # to run the full QueryEngine.run ƒ?" just verify that _new_child_engine
compact_v5/MAIN/agent\tests\integration\test_subagent.py:343:    # The QueryEngine dispatch context picks it up via getattr(self, "_subagent_depth", 0):
compact_v5/MAIN/agent\tests\integration\test_subagent.py:350:    so the QueryEngine dispatch context carries `parent_depth=child_depth`.
compact_v5/MAIN/agent\tests\integration\test_subagent.py:357:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:360:    parent = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_subagent.py:405:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:408:    parent = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_subagent.py:440:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:443:    parent = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_subagent.py:458:        def run(self, **kwargs):
compact_v5/MAIN/agent\tests\integration\test_subagent.py:482:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:485:    parent = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_subagent.py:502:    mutation. We simulate corruption by patching the underlying QueryEngine.run
compact_v5/MAIN/agent\tests\integration\test_subagent.py:504:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_subagent.py:507:    parent = QueryEngine(
compact_v5/MAIN/agent\tests\integration\test_subagent.py:522:        def run(self, **kwargs):
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:7:Locks PORT_LOG #019: Runnable QueryEngine.ts adapted to v5 .ipynb shape.
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:83:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:87:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:103:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:111:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:136:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:140:    engine = QueryEngine(client=client, max_turns=2)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:173:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:184:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:212:    from core import QueryEngine, IterationBudget
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:220:    engine = QueryEngine(client=client, max_turns=5, budget=budget)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:237:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:246:    engine = QueryEngine(client=client, max_turns=3)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:261:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:268:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:286:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:304:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:322:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:326:    engine = QueryEngine(client=client, max_turns=2)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:355:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:362:    engine = QueryEngine(client=OverflowClient(), max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:398:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:405:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:427:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:444:    engine = QueryEngine(client=client, max_turns=5)
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:471:    from core import QueryEngine
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:479:    engine = QueryEngine(client=client_run1, max_turns=5)
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n -C 6 \"context_max_tokens|Compactor\\.should_compact|Compactor\\.run|\\[auto-compact\\]|TOKENS\\.add|session_cost_limit|not response\\.tool_calls\" compact_v5/MAIN/agent/core/query_engine.py" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n -C 3 \"CONFIG\\.context_max_tokens|AUTO_COMPACT\\.reset|agent\\.run|compact_likely|re\\.match|t2_text|tokens_in_t1|cost_used|max_turns=4|TOKENS\\.reset\" compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n -C 4 \"def should_compact|SUMMARY_TRIGGER_PERCENT|FIXED_OVERHEAD_TOKENS|def compact|\\[CONVERSATION SUMMARY\\]|def run\\(\" compact_v5/MAIN/agent/core/compactor.py" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n -C 3 "session_cost_limit|def is_over_budget|session_cost|api_calls|def add" compact_v5/MAIN/agent/runtime/tokens.py' in D:\Github\sagemaker-coding-agent
 succeeded in 3826ms:
227-        """
228-        self.client = client
229-        self.max_turns = max(1, int(max_turns))
230-        self.budget = budget if budget is not None else IterationBudget()
231-        self.on_stop_check = on_stop_check
232-        self.skill_manager = skill_manager
233:        # Block B: per-agent attribution key for TOKENS.add(). "parent" by
234-        # default; sub-agents pass their type-string ("build", "explore",
235-        # "verify", etc.) via subagent.spawn._new_child_engine.
236-        self.agent_kind = agent_kind
237-        # Block B: session_id used by AUDIT.log on each tool dispatch.
238-        # Block B+ will swap this to the SessionManager-issued id; for
239-        # now we mint a process-lifetime id so audit lines are at least
--
548-
549-            # Block B (PORT_LOG #039+#040): record token usage + per-agent
550-            # attribution. "parent" or sub-agent type-string. Best-effort ƒ?"
551-            # never break the agent loop if the singleton import fails.
552-            try:
553-                from runtime.tokens import TOKENS as _TOKENS
554:                _TOKENS.add(
555-                    response.usage or {},
556-                    model_id=getattr(self.client, "model_id", None),
557-                    agent_kind=self.agent_kind,
558-                )
559-                try:
560-                    from runtime.audit import AUDIT as _AUDIT_CHAT
--
593-                # warning. v4 sagemaker_agent.py:8787 prints
594-                #   `[Cost ${session_cost} passed budget ${limit} ƒ?" continuing.]`
595-                # NOT a hard halt ƒ?" per user 2026-05-03 update to plan v3,
596-                # v5 matches v4 UX: warn and continue. True hard halt is at
597-                # cloud-budget level (AWS Budget Action / GCP).
598-                from runtime.config import CONFIG as _CFG
599:                limit = getattr(_CFG, "session_cost_limit", 0.0)
600-                # Block B+ Codex finding #1 lock: `>=` so exact-100% trips
601-                # the warning (`>` would skip parity-100% cases).
602-                if limit > 0 and _TOKENS.session_cost >= limit:
603-                    if not getattr(self, "_warned_over_budget", False):
604-                        output_fn(
605-                            f"[Cost ${_TOKENS.session_cost:.4f} passed "
--
619-            # Block A ƒ?" auto-compact gate. Per-turn check: if the
620-            # message buffer has crossed the 80% threshold AND the
621-            # circuit breaker allows another attempt, run Compactor.
622-            try:
623-                from core.compactor import Compactor, AUTO_COMPACT
624-                from runtime.config import CONFIG as _CFG_AC
625:                _max_ctx = getattr(_CFG_AC, "context_max_tokens", 200_000)
626:                if Compactor.should_compact(self.messages, _max_ctx):
627-                    _ok, _why = AUTO_COMPACT.try_attempt()
628-                    if _ok:
629:                        _result = Compactor.run(self.client, self.messages, _max_ctx)
630-                        if _result.success:
631-                            output_fn(
632:                                f"[auto-compact] saved "
633-                                f"{_result.tokens_before - _result.tokens_after:,} "
634-                                f"tokens; continuing."
635-                            )
636-                            self.messages = _result.messages_after
637-                    else:
638-                        # Cooldown / cap message ƒ?" log once per turn, no
639-                        # spam since try_attempt returns reason text.
640-                        output_fn(f"[auto-compact skipped: {_why}]")
641-            except Exception:
642-                pass
643-
644-            # Stop conditions: end_turn / no tool_use blocks ƒ+' final answer.
645:            if not response.tool_calls:
646-                # Block F2 ƒ?" auto-continuation under iteration budget. Only
647-                # parent agents (not sub-agents) and only when CONFIG flag
648-                # is opt-in (default OFF per Wave 6 NLT row #21). Cost-cap
649-                # halt has priority inside check_iteration_budget().
650-                try:
651-                    from runtime.config import CONFIG as _CFG_F2
--
662-                        _sc = 0.0
663-                        try:
664-                            from runtime.tokens import TOKENS as _TOKENS_F2
665-                            _sc = float(getattr(_TOKENS_F2, "session_cost", 0.0))
666-                        except Exception:
667-                            _sc = 0.0
668:                        _scl = float(getattr(_CFG_F2, "session_cost_limit", 0.0))
669-                        decision = check_iteration_budget(
670-                            self._budget_tracker,
671-                            iter_used=self.budget.used(),
672-                            iter_total=self.budget.total(),
673-                            is_subagent=_is_sub,
674-                            session_cost=_sc,
675:                            session_cost_limit=_scl,
676-                        )
677-                        if isinstance(decision, ContinueDecision):
678-                            # Surface the assistant's interim text + nudge to keep
679-                            # working. Continuing the for-loop re-invokes Bedrock.
680-                            if response.text:
681-                                output_fn(response.text)
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 4867ms:
153-    """
154-
155-    PRUNE_PROTECT_TOKENS = 40_000
156-    PRUNE_MIN_SAVINGS = 10_000
157:    SUMMARY_TRIGGER_PERCENT = 0.80
158-    KEEP_LAST_MESSAGES = 3
159-    MAX_PTL_RETRIES = 3
160-
161-    SUMMARY_TOOL_RESULT_THRESHOLD = 8_000
--
163-    SUMMARY_TOOL_RESULT_TAIL = 1_000
164-
165-    PROTECTED_TOOLS = {"todo_write", "todo_read", "semantic_search"}
166-
167:    FIXED_OVERHEAD_TOKENS = 6_000
168-
169-    # Aux client cache (per-process); built lazily.
170-    _aux_client_cache: Dict[str, Any] = {}
171-
--
276-    # Should compact?
277-    # --------------------------------------------------------
278-
279-    @classmethod
280:    def should_compact(cls, messages: List[Dict[str, Any]], max_tokens: int) -> bool:
281-        """True iff token estimate > 80% of max_tokens (with overhead)."""
282-        try:
283-            from runtime.tokens import TOKENS
284-            overhead = TOKENS.final_context_tokens_from_last_response()
285-            if overhead == 0:
286:                overhead = cls.FIXED_OVERHEAD_TOKENS
287-        except Exception:
288:            overhead = cls.FIXED_OVERHEAD_TOKENS
289-        total = cls.estimate_tokens(messages) + overhead
290:        return total > max_tokens * cls.SUMMARY_TRIGGER_PERCENT
291-
292-    # --------------------------------------------------------
293-    # Auxiliary-model routing (B+5 ƒ?" recursive advisor sub-cost)
294-    # --------------------------------------------------------
--
485-    # Compact: replace old messages with summary
486-    # --------------------------------------------------------
487-
488-    @classmethod
489:    def compact(
490-        cls,
491-        messages: List[Dict[str, Any]],
492-        summary: str,
493-    ) -> List[Dict[str, Any]]:
--
498-        recent = messages[-keep_last:] if len(messages) > keep_last else []
499-        summary_msg = {
500-            "role": "user",
501-            "content": (
502:                f"[CONVERSATION SUMMARY]\n{summary}\n"
503-                "[END SUMMARY ƒ?" Continuing from here]"
504-            ),
505-        }
506-        return [summary_msg] + recent
507-
508-    @classmethod
509:    def run(
510-        cls,
511-        client: Any,
512-        messages: List[Dict[str, Any]],
513-        max_tokens: int = 200_000,
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 4998ms:
14-      using only the compact summary.
15-
16-Codex R2 PHASE A iter-1 fixes applied (REJECT ƒ+' re-pre-flight):
17:  1. Default CONFIG.context_max_tokens=200_000 means real trigger is
18:     ~160K. We monkey-patch CONFIG.context_max_tokens=100_000 for this
19-     test so the existing 78K preamble crosses the 80% gate (80K).
20-     Cheaper than pushing to 165K real tokens AND tests same code path.
21-  2. Tightened final answer regex (single-token "5" or "five" reply
--
25-     compact fired; OR captured "[auto-compact]" line in stdout.
26-  4. Follow-up turn against the compacted buffer (asks recall question
27-     answerable from system summary).
28:  5. AUTO_COMPACT.reset() + TOKENS.reset() in finally for hermetic test.
29-
30-Cost cap: $0.50. Model: Haiku 4.5 AU.
31-Real-AWS gated: skipped without RUN_REAL_BEDROCK=1.
--
50-_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
51-_R2_COST_CAP_USD = 0.50
52-
53:# 2700 lines of lorem ƒ%^ 60K words ƒ%^ 78K tokens. With CONFIG.context_max_tokens
54-# = 100_000 (test override), this crosses the 80%-of-100K = 80K threshold.
55-_LOREM_LINE = (
56-    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
--
108-    cwd_before = os.getcwd()
109-
110-    # Codex iter-1 fix #5: clean state in finally + at start.
111:    AUTO_COMPACT.reset() if hasattr(AUTO_COMPACT, "reset") else None
112-
113-    captured_stdout: list = []
114-
--
127-        CONFIG.max_tokens = 64
128-        CONFIG.require_tool_approval = False
129-        # Codex iter-1 fix #1: lower threshold so 78K crosses the 80% gate.
130:        CONFIG.context_max_tokens = 100_000
131-        sec_mgr.rebuild_singleton_for_tests()
132-        os.chdir(str(tmp_path))
133:        TOKENS.reset()
134-
135-        region = os.getenv("AWS_REGION", "ap-southeast-2")
136-        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)
--
142-
143-        agent = Agent(
144-            client=client,
145:            max_turns=4,
146-            on_stop_check=_hard_cost_halt,
147-        )
148-
--
152-
153-        t0 = time.time()
154-        # Turn 1 ƒ?" large preamble.
155:        result_t1 = agent.run(prompt_t1, tools=[], output_fn=_stdout_capture)
156-        wall_t1 = time.time() - t0
157:        tokens_in_t1 = TOKENS.session_input
158-        api_calls_after_t1 = TOKENS.api_calls
159-        # Turn 2 ƒ?" follow-up against (likely-compacted) buffer.
160-        t1 = time.time()
161:        result_t2 = agent.run(_R2_PROMPT_T2, tools=[], output_fn=_stdout_capture)
162-        wall_t2 = time.time() - t1
163:        cost_used = TOKENS.session_cost
164-        tokens_in = TOKENS.session_input
165-        tokens_out = TOKENS.session_output
166-        api_calls = TOKENS.api_calls
--
172-        compact_log_seen = "[auto-compact]" in full_stdout
173-        # Heuristic: 2 user turns alone = ƒ%2 api_calls. With auto-compact
174-        # firing between t1 and t2, api_calls should be ƒ%3.
175:        compact_likely = api_calls >= 3 or compact_log_seen
176-
177-        metrics = {
178-            "test": "R2",
--
181-            "model": _HAIKU_45_AU,
182-            "tokens_in": int(tokens_in),
183-            "tokens_out": int(tokens_out),
184:            "tokens_in_after_turn1": int(tokens_in_t1),
185-            "wallclock_s": round(wall_t1 + wall_t2, 2),
186-            "wallclock_t1_s": round(wall_t1, 2),
187-            "wallclock_t2_s": round(wall_t2, 2),
188-            "approx_prompt_tokens": approx_tokens_in,
189-            "preamble_lines": _LOREM_LINES,
190:            "context_max_tokens_test_override": CONFIG.context_max_tokens,
191-            "api_calls": int(api_calls),
192-            "api_calls_after_t1": int(api_calls_after_t1),
193-            "compact_log_seen": compact_log_seen,
194:            "compact_likely": compact_likely,
195-            "tool_calls_t1": int(getattr(result_t1, "turns_used", 0)),
196-            "tool_calls_t2": int(getattr(result_t2, "turns_used", 0)),
197:            "cost_usd": round(cost_used, 4),
198-            "stop_reason_t1": result_t1.stop_reason,
199-            "stop_reason_t2": result_t2.stop_reason,
200-            "final_text_t1": (result_t1.text or "").strip()[:200],
--
209-        t1_text = (result_t1.text or "").strip()
210-        # Accept "5", "5.", "Five", "Five.", "= 5", with optional
211-        # leading "=" or whitespace.
212:        assert re.match(r"^\s*=?\s*(5|five)\b\.?\s*$", t1_text, re.IGNORECASE), (
213-            f"R2 turn 1 expected exact answer 5/five; got: {t1_text!r}. "
214-            f"metrics={metrics}"
215-        )
--
217-            f"R2 turn 1 hit max_turns. metrics={metrics}"
218-        )
219-        # Turn 2 ƒ?" recall via compacted buffer.
220:        t2_text = (result_t2.text or "").lower()
221:        assert t2_text, f"R2 turn 2 empty response. metrics={metrics}"
222:        assert ("2 + 3" in t2_text or "2+3" in t2_text or
223:                "what is 2" in t2_text or "5" in t2_text), (
224-            f"R2 turn 2 didn't recall the prior question. "
225-            f"got: {result_t2.text!r}. metrics={metrics}"
226-        )
227-        # Codex iter-1 fix #3: assert compaction or 2-turn evidence.
228:        assert compact_likely, (
229-            f"R2 expected compaction OR ƒ%3 api_calls (current: "
230-            f"api_calls={api_calls}, log_seen={compact_log_seen}). "
231-            f"metrics={metrics}"
232-        )
233-        # Cost.
234:        assert cost_used <= _R2_COST_CAP_USD, (
235:            f"R2 cost ${cost_used:.4f} exceeded cap ${_R2_COST_CAP_USD}. "
236-            f"metrics={metrics}"
237-        )
238-        # Sanity: large input was actually sent.
239:        assert tokens_in_t1 > 50_000, (
240:            f"R2 expected turn-1 input_tokens >50K; got {tokens_in_t1}. "
241-            f"metrics={metrics}"
242-        )
243-    finally:
--
253-        if saved_require_approval is not None:
254-            CONFIG.require_tool_approval = saved_require_approval
255-        if saved_ctx_max is not None:
256:            CONFIG.context_max_tokens = saved_ctx_max
257-        # Codex iter-1 fix #5.
258-        if hasattr(AUTO_COMPACT, "reset"):
259:            AUTO_COMPACT.reset()
260:        TOKENS.reset()
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 5735ms:
307-
308-    v5 extension over v4: per-agent attribution dict so parent and
309-    sub-agent token costs can be reported separately while still rolling
310:    up to the same `session_cost` total. Per Plan v3 ABlock B + B-11.
311-
312-    The agent_kind argument to `add()` is the attribution bucket key
313-    (default "parent"; sub-agents pass "build", "explore", "verify",
--
350-        self.session_cache_write = 0
351-        self.last_input = 0
352-        self.last_output = 0
353:        self.api_calls = 0
354:        self.session_cost = 0.0
355-        self.last_cost = 0.0
356-        self._model_id = self._config.model_id
357-        self._budget_warned = False
--
371-    # Add usage (the singleton write path)
372-    # --------------------------------------------------------
373-
374:    def add(
375-        self,
376-        usage: Dict[str, int],
377-        model_id: Optional[str] = None,
--
397-            self.session_total = self.session_input + self.session_output
398-            self.session_cache_read += cache_read
399-            self.session_cache_write += cache_write
400:            self.api_calls += 1
401-            # B-8 ƒ?" record last usage so estimators can walk back.
402-            self._last_usage_record = dict(usage)
403-
--
421-                    + (cache_write / 1000) * base_input * 1.25
422-                    + (output_tokens / 1000) * base_output
423-                )
424:                self.session_cost += cost
425-                self.last_cost = cost
426-            else:
427-                if not hasattr(self, "_warned_models"):
--
451-                )
452-
453-            # Budget gate (verbatim from v4).
454:            limit = self._config.session_cost_limit
455:            if limit > 0 and self.session_cost > 0:
456:                pct = self.session_cost / limit
457-                if pct >= 1.0 and not self._budget_stopped:
458-                    self._budget_stopped = True
459-                    logging.warning(
460:                        f"Session cost ${self.session_cost:.4f} reached limit ${limit:.2f}."
461-                    )
462-                elif pct >= 0.8 and not self._budget_warned:
463-                    self._budget_warned = True
464-                    logging.warning(
465:                        f"Session cost ${self.session_cost:.4f} is {pct:.0%} of ${limit:.2f} limit."
466-                    )
467-
468-    # --------------------------------------------------------
469-    # Read-only views (v4 verbatim)
470-    # --------------------------------------------------------
471-
472:    def is_over_budget(self) -> bool:
473:        limit = self._config.session_cost_limit
474:        return limit > 0 and self.session_cost >= limit
475-
476-    def get_last(self) -> str:
477-        return f"In:{self.last_input:,} Out:{self.last_output:,}"
--
492-
493-    def get_cost(self) -> str:
494-        cost_str = (
495:            f"${self.session_cost:.4f}"
496:            if self.session_cost < 0.01
497:            else f"${self.session_cost:.2f}"
498-        )
499-        if self.session_cache_read > 0 and self.session_input > 0:
500-            cache_pct = min(100, (self.session_cache_read / self.session_input) * 100)
--
511-            "session_cache_write": self.session_cache_write,
512-            "last_input": self.last_input,
513-            "last_output": self.last_output,
514:            "api_calls": self.api_calls,
515:            "session_cost_usd": round(self.session_cost, 6),
516-            "last_cost_usd": round(self.last_cost, 6),
517-            "parent_input_tokens": self.parent_input_tokens,
518-            "parent_output_tokens": self.parent_output_tokens,
--
536-            self.session_cache_write = int(stats.get("session_cache_write", 0))
537-            self.last_input = int(stats.get("last_input", 0))
538-            self.last_output = int(stats.get("last_output", 0))
539:            self.api_calls = int(stats.get("api_calls", 0))
540:            self.session_cost = float(stats.get("session_cost_usd", 0.0))
541-            self.last_cost = float(stats.get("last_cost_usd", 0.0))
542-            self.parent_input_tokens = int(stats.get("parent_input_tokens", 0))
543-            self.parent_output_tokens = int(stats.get("parent_output_tokens", 0))
--
595-# SIGTERM, log the final session cost so operators can audit
596-# post-hoc even if the user closes the notebook abruptly.
597-def _flush_cost_on_exit() -> None:
598:    if TOKENS.session_cost > 0:
599-        logging.warning(
600-            f"session-final cost: {TOKENS.get_cost()} "
601:            f"({TOKENS.api_calls} API calls, "
602-            f"in={TOKENS.session_input:,} out={TOKENS.session_output:,})"
603-        )
604-
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n -C 5 \"on_stop_check|for .*range|turns_used|turns_used|budget\\.consume|client\\.chat|messages_for_model\" compact_v5/MAIN/agent/core/query_engine.py" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n -C 4 "def final_context_tokens_from_last_response|last_response|cache_read|input_tokens" compact_v5/MAIN/agent/runtime/tokens.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n -C 4 "class Response|usage=|count_tokens|cache_control|cache_read" compact_v5/MAIN/agent/runtime/bedrock_client.py' in D:\Github\sagemaker-coding-agent
 succeeded in 3544ms:
58-    `text`           ƒ?" final assistant text (last end_turn turn's text block).
59-    `messages`       ƒ?" full message buffer including the user turn that
60-                       triggered this call. Caller may discard or persist.
61-    `stop_reason`    ƒ?" "end_turn" | "max_turns" | "budget_exhausted" |
62-                       "context_overflow" | "fatal_error".
63:    `turns_used`     ƒ?" count of model turns executed during this run.
64-    `budget_used`    ƒ?" IterationBudget.used() snapshot at exit.
65-    `error`          ƒ?" short message when stop_reason indicates failure.
66-    """
67-    text: str = ""
68-    messages: List[Dict[str, Any]] = field(default_factory=list)
69-    stop_reason: str = ""
70:    turns_used: int = 0
71-    budget_used: int = 0
72-    error: Optional[str] = None
73-
74-
75-# ============================================================
--
199-    def __init__(
200-        self,
201-        client: Any,
202-        max_turns: int = DEFAULT_MAX_TURNS,
203-        budget: Optional[IterationBudget] = None,
204:        on_stop_check: Optional[Callable[[], bool]] = None,
205-        skill_manager: Optional[Any] = None,
206-        agent_kind: str = "parent",
207-        session_id: Optional[str] = None,
208-        synthetic_output_tool_name: Optional[str] = None,
209-        max_structured_output_retries: int = 3,
--
212-
213-        Args:
214-            client: BedrockClient (or mock with the same `chat(...)` shape).
215-            max_turns: hard upper bound on turns per `run()` call.
216-            budget: shared IterationBudget. If None, a fresh one is created.
217:            on_stop_check: optional callable returning True if the user has
218-                requested a stop (notebook UX). Phase 11 wires this to the
219-                Stop button.
220-            skill_manager: optional `skills.manager.SkillManager`. When
221-                supplied, the engine (a) injects the active skill body into
222-                the dynamic tail of the system prompt, and (b) appends a
--
226-                ƒ?" preserves Phase 1-8 backwards compatibility for tests.
227-        """
228-        self.client = client
229-        self.max_turns = max(1, int(max_turns))
230-        self.budget = budget if budget is not None else IterationBudget()
231:        self.on_stop_check = on_stop_check
232-        self.skill_manager = skill_manager
233-        # Block B: per-agent attribution key for TOKENS.add(). "parent" by
234-        # default; sub-agents pass their type-string ("build", "explore",
235-        # "verify", etc.) via subagent.spawn._new_child_engine.
236-        self.agent_kind = agent_kind
--
351-        if _rate_msg is not None:
352-            return QueryResult(
353-                text=_rate_msg,
354-                messages=list(self.messages),
355-                stop_reason="rate_limited",
356:                turns_used=0,
357-                budget_used=self.budget.used(),
358-                error=_rate_msg,
359-            )
360-
361-        # Append user turn (Bedrock requires alternation; merge into trailing
--
456-            except Exception as exc:  # noqa: BLE001 ƒ?" skill machinery never raises into agent loop
457-                logging.warning("[skill-wiring] %s: %s", type(exc).__name__, exc)
458-
459-        last_text = ""
460-        stop_reason = ""
461:        turns_used = 0
462-
463:        for turn in range(self.max_turns):
464-            # User-requested stop (Phase 11 wires this to the Stop button).
465:            if self.on_stop_check and self.on_stop_check():
466-                output_fn("[Stopped by user]")
467-                stop_reason = "user_stop"
468-                break
469-
470-            # Block M-2 (PORT_LOG #084) ƒ?" structured-output retry-limit
--
485-                    )
486-                    stop_reason = "error_max_structured_output_retries"
487-                    break
488-
489-            # Budget gate ƒ?" shared with sub-agents (Phase 9).
490:            if not self.budget.consume():
491-                used, total = self.budget.used(), self.budget.total()
492-                output_fn(
493-                    f"[Budget exhausted: {used}/{total} iterations used. "
494-                    "Adjust IterationBudget or start a new session.]"
495-                )
--
517-            if deferred_names:
518-                turn_messages = self._inject_deferred_reminder(turn_messages, deferred_names)
519-
520-            # Bedrock invocation.
521-            try:
522:                response = self.client.chat(
523-                    messages=turn_messages,
524-                    system=effective_system_prompt,
525-                    tools=_build_tools_api_payload(visible_tools),
526-                    max_tokens=max_tokens,
527-                    temperature=temperature,
--
537-                    stop_reason = "fatal_error"
538-                return QueryResult(
539-                    text=last_text,
540-                    messages=list(self.messages),
541-                    stop_reason=stop_reason,
542:                    turns_used=turns_used,
543-                    budget_used=self.budget.used(),
544-                    error=f"{category}: {debug}",
545-                )
546-
547:            turns_used += 1
548-
549-            # Block B (PORT_LOG #039+#040): record token usage + per-agent
550-            # attribution. "parent" or sub-agent type-string. Best-effort ƒ?"
551-            # never break the agent loop if the singleton import fails.
552-            try:
--
561-                    _AUDIT_CHAT.log(
562-                        session_id=self.session_id,
563-                        action="chat_response",
564-                        tool_name="(engine)",
565-                        parameters={
566:                            "turn": turns_used,
567-                            "response": {
568-                                "usage": response.usage or {},
569-                                "thinking": getattr(response, "thinking", "") or "",
570-                                "text": response.text or "",
571-                                "stop_reason": getattr(response, "stop_reason", ""),
--
1037-
1038-        return QueryResult(
1039-            text=last_text,
1040-            messages=list(self.messages),
1041-            stop_reason=stop_reason or "end_turn",
1042:            turns_used=turns_used,
1043-            budget_used=self.budget.used(),
1044-        )
1045-
1046-    # ------------------------------------------------------------
1047-    # Internal: assemble assistant turn content from a Bedrock Response
--
1139-    spinning up the full multi-turn loop.
1140-    """
1141-    from tools.registry import apply_tool_search_deferral
1142-
1143-    visible_tools, _deferred = apply_tool_search_deferral(tools, enabled=True)
1144:    return client.chat(
1145-        messages=messages,
1146-        system=system_prompt,
1147-        tools=_build_tools_api_payload(visible_tools),
1148-        max_tokens=max_tokens,
1149-        temperature=temperature,
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 3573ms:
50-# B-10 ƒ?" MODEL_COSTS (R8 #34, #68; Bedrock-only subset)
51-# ============================================================
52-#
53-# 2-row Bedrock pricing table per the user's deployment (Haiku 4.5 +
54:# Sonnet 4.5). Cache pricing math: cache_read = 10% of base input,
55-# cache_write = 125% of base input. Output = full price. All values are
56-# USD per 1K tokens, current as of 2026-04 Bedrock list pricing.
57-#
58-# Cross-region inference profile prefixes (`apac.`, `us.`, `eu.`) collapse
--
267-    if btype == "tool_use":
268-        # Tool name + input as JSON (dense, 2 bytes/token).
269-        name_tokens = estimate_message_tokens(block.get("name", ""))
270-        import json as _json
271:        input_tokens = int(len(_json.dumps(block.get("input", {}))) / 2.0 + 0.5)
272:        return name_tokens + input_tokens
273-    if btype == "tool_result":
274-        content = block.get("content", "")
275-        if isinstance(content, list):
276-            return sum(rough_token_count_for_block(c) for c in content)
--
345-    def _reset_unlocked(self):
346-        self.session_input = 0
347-        self.session_output = 0
348-        self.session_total = 0
349:        self.session_cache_read = 0
350-        self.session_cache_write = 0
351-        self.last_input = 0
352-        self.last_output = 0
353-        self.api_calls = 0
--
357-        self._budget_warned = False
358-        self._budget_stopped = False
359-        # Per-agent attribution (Plan v3 ABlock B). Parent always tracked
360-        # by default; sub-agents accumulate under their type-string key.
361:        self.parent_input_tokens = 0
362-        self.parent_output_tokens = 0
363-        self.parent_cost = 0.0
364:        self.subagent_input_tokens: Dict[str, int] = {}
365-        self.subagent_output_tokens: Dict[str, int] = {}
366-        self.subagent_cost: Dict[str, float] = {}
367-        # Last-usage record for tokenCountWithEstimation walks (B-8).
368-        self._last_usage_record: Optional[Dict[str, int]] = None
--
383-        agent loop; sub-agent type-strings ("build", "explore", "verify",
384-        "plan", "review", "general") for spawned children. The session
385-        rollup totals always include both.
386-        """
387:        input_tokens = int(usage.get("input_tokens", 0) or 0)
388-        output_tokens = int(usage.get("output_tokens", 0) or 0)
389:        cache_read = int(usage.get("cache_read_input_tokens", 0) or 0)
390:        cache_write = int(usage.get("cache_creation_input_tokens", 0) or 0)
391-
392-        with self._lock:
393:            self.last_input = input_tokens
394-            self.last_output = output_tokens
395:            self.session_input += input_tokens
396-            self.session_output += output_tokens
397-            self.session_total = self.session_input + self.session_output
398:            self.session_cache_read += cache_read
399-            self.session_cache_write += cache_write
400-            self.api_calls += 1
401-            # B-8 ƒ?" record last usage so estimators can walk back.
402-            self._last_usage_record = dict(usage)
--
413-                # this, local cost tracker undercounts AWS billing by 10%.
414-                geo_mult = get_geo_multiplier(raw_mid)
415-                base_input = pricing["input"] * geo_mult
416-                base_output = pricing["output"] * geo_mult
417:                regular_input = max(0, input_tokens - cache_read - cache_write)
418-                cost = (
419-                    (regular_input / 1000) * base_input
420:                    + (cache_read / 1000) * base_input * 0.1
421-                    + (cache_write / 1000) * base_input * 1.25
422-                    + (output_tokens / 1000) * base_output
423-                )
424-                self.session_cost += cost
--
435-                self.last_cost = 0.0
436-
437-            # Per-agent attribution (additive ƒ?" same singleton, separate buckets).
438-            if agent_kind == "parent":
439:                self.parent_input_tokens += input_tokens
440-                self.parent_output_tokens += output_tokens
441-                self.parent_cost += cost
442-            else:
443:                self.subagent_input_tokens[agent_kind] = (
444:                    self.subagent_input_tokens.get(agent_kind, 0) + input_tokens
445-                )
446-                self.subagent_output_tokens[agent_kind] = (
447-                    self.subagent_output_tokens.get(agent_kind, 0) + output_tokens
448-                )
--
484-
485-    def get_cache_savings_usd(self) -> float:
486-        mid = canonicalize_model_id(self._model_id or self._config.model_id)
487-        pricing = MODEL_COSTS.get(mid)
488:        if not pricing or self.session_cache_read == 0:
489-            return 0.0
490-        full_price_per_1k = pricing["input"]
491:        return (self.session_cache_read / 1000) * full_price_per_1k * 0.90
492-
493-    def get_cost(self) -> str:
494-        cost_str = (
495-            f"${self.session_cost:.4f}"
496-            if self.session_cost < 0.01
497-            else f"${self.session_cost:.2f}"
498-        )
499:        if self.session_cache_read > 0 and self.session_input > 0:
500:            cache_pct = min(100, (self.session_cache_read / self.session_input) * 100)
501-            savings = self.get_cache_savings_usd()
502-            cost_str += f" (cache {cache_pct:.0f}% | saved ~${savings:.4f})"
503-        return cost_str
504-
--
506-        return {
507-            "session_input": self.session_input,
508-            "session_output": self.session_output,
509-            "session_total": self.session_total,
510:            "session_cache_read": self.session_cache_read,
511-            "session_cache_write": self.session_cache_write,
512-            "last_input": self.last_input,
513-            "last_output": self.last_output,
514-            "api_calls": self.api_calls,
515-            "session_cost_usd": round(self.session_cost, 6),
516-            "last_cost_usd": round(self.last_cost, 6),
517:            "parent_input_tokens": self.parent_input_tokens,
518-            "parent_output_tokens": self.parent_output_tokens,
519-            "parent_cost_usd": round(self.parent_cost, 6),
520:            "subagent_input_tokens": dict(self.subagent_input_tokens),
521-            "subagent_output_tokens": dict(self.subagent_output_tokens),
522-            "subagent_cost_usd": {k: round(v, 6) for k, v in self.subagent_cost.items()},
523-        }
524-
--
531-        with self._lock:
532-            self.session_input = int(stats.get("session_input", 0))
533-            self.session_output = int(stats.get("session_output", 0))
534-            self.session_total = self.session_input + self.session_output
535:            self.session_cache_read = int(stats.get("session_cache_read", 0))
536-            self.session_cache_write = int(stats.get("session_cache_write", 0))
537-            self.last_input = int(stats.get("last_input", 0))
538-            self.last_output = int(stats.get("last_output", 0))
539-            self.api_calls = int(stats.get("api_calls", 0))
540-            self.session_cost = float(stats.get("session_cost_usd", 0.0))
541-            self.last_cost = float(stats.get("last_cost_usd", 0.0))
542:            self.parent_input_tokens = int(stats.get("parent_input_tokens", 0))
543-            self.parent_output_tokens = int(stats.get("parent_output_tokens", 0))
544-            self.parent_cost = float(stats.get("parent_cost_usd", 0.0))
545:            self.subagent_input_tokens = dict(stats.get("subagent_input_tokens", {}))
546-            self.subagent_output_tokens = dict(stats.get("subagent_output_tokens", {}))
547-            self.subagent_cost = {
548-                k: float(v) for k, v in stats.get("subagent_cost_usd", {}).items()
549-            }
--
551-    # --------------------------------------------------------
552-    # B-8 / B-9 ƒ?" context-token math derived from last response
553-    # --------------------------------------------------------
554-
555:    def final_context_tokens_from_last_response(self) -> int:
556-        """Best-available estimate of the current context window size.
557-
558-        Per R8 #16: Bedrock returns top-level `usage` only (no per-block
559:        `cache_creation_input_tokens` breakdown). We use:
560:          context = last_input + cache_read + cache_write
561-        as a conservative upper bound for the next turn's prompt.
562-        """
563-        rec = self._last_usage_record
564-        if not rec:
565-            return self.session_input  # cold start fallback
566-        return (
567:            int(rec.get("input_tokens", 0))
568:            + int(rec.get("cache_read_input_tokens", 0))
569:            + int(rec.get("cache_creation_input_tokens", 0))
570-        )
571-
572-    def token_count_with_estimation(self, messages: List[Dict[str, Any]]) -> int:
573-        """Estimate token count for a message list.
--
579-        """
580-        if not messages:
581-            return 0
582-        if self._last_usage_record is not None:
583:            recorded = self._last_usage_record.get("input_tokens", 0)
584-            if recorded > 0:
585-                return int(recorded)
586-        return sum(rough_token_count_for_message(m) for m in messages)
587-
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 4197ms:
48-    input: Dict[str, Any] = field(default_factory=dict)
49-
50-
51-@dataclass
52:class Response:
53-    """Parsed Bedrock response."""
54-    text: str
55-    tool_calls: List[ToolCall] = field(default_factory=list)
56-    stop_reason: str = ""
--
188-
189-    def chat(
190-        self,
191-        messages: List[Dict],
192:        system: Any,  # str OR list-of-blocks (with cache_control)
193-        tools: Optional[List[Dict]] = None,
194-        max_tokens: int = 4096,
195-        temperature: float = 0.0,
196-        thinking_enabled: bool = False,
--
199-        """Send chat request to Bedrock.
200-
201-        Args:
202-            messages: Conversation messages
203:            system: System prompt (str or pre-formatted multi-block list with cache_control)
204-            tools: Tool definitions
205-            max_tokens: Maximum response tokens
206-            temperature: Sampling temperature (0.0-1.0)
207-            thinking_enabled: Enable extended thinking mode
--
215-
216-        # V4.1 #14: Prompt cache boundary.
217-        # If cache enabled and supported, split system string into static (cached)
218-        # + dynamic (uncached) blocks. Bedrock supports prompt caching natively
219:        # via cache_control blocks in content. No anthropic_beta header needed.
220-        # Haiku 4.5: min 4096 tokens/checkpoint. Sonnet 4.5: min 1024.
221-        cache_active = CONFIG.enable_prompt_cache and self.prompt_cache_supported
222-        if cache_active and isinstance(system, list):
223-            # Already formatted as cache blocks by caller ƒ?" pass as-is
--
233-                    system_field = [
234-                        {
235-                            "type": "text",
236-                            "text": static_part,
237:                            "cache_control": {"type": "ephemeral"},
238-                        },
239-                        {"type": "text", "text": dynamic_part},
240-                    ]
241-                else:
242-                    system_field = [
243-                        {
244-                            "type": "text",
245-                            "text": static_part,
246:                            "cache_control": {"type": "ephemeral"},
247-                        },
248-                    ]
249-            else:
250-                # No boundary ƒ?" cache the whole prompt as static
251-                system_field = [
252-                    {
253-                        "type": "text",
254-                        "text": system,
255:                        "cache_control": {"type": "ephemeral"},
256-                    },
257-                ]
258-            use_cache = True
259-        else:
--
265-            "max_tokens": max_tokens,
266-            "system": system_field,
267-            "messages": messages,
268-        }
269:        # Note: Bedrock prompt caching is activated by cache_control blocks in
270-        # content. No anthropic_beta header needed (that header is for the direct
271-        # Anthropic API only).
272-
273-        # Extended thinking mode (requires temperature=1).
--
363-        return Response(
364-            text=text,
365-            tool_calls=tool_calls,
366-            stop_reason=result.get("stop_reason", ""),
367:            usage=result.get("usage", {}),
368-            thinking=thinking,
369-        )
370-
371-    # ============================================================
372-    # B-1 ƒ?" countTokensWithBedrock (R4 #41, MUST)
373-    # ============================================================
374-
375:    def count_tokens(
376-        self,
377-        messages: List[Dict[str, Any]],
378-        system: Optional[str] = None,
379-        tools: Optional[List[Dict[str, Any]]] = None,
--
387-        Compactor (Block A) cannot make safe context-budget decisions.
388-
389-        Falls through to None when:
390-          - mock_mode is True (no Bedrock contact)
391:          - the bedrock-runtime client doesn't expose count_tokens
392-            (older boto3 versions; retry by upgrading boto3 ƒ% 1.35)
393-          - the API returns a malformed response
394-        """
395-        if self.mock_mode:
--
428-                "input": {
429-                    "invokeModel": {"body": json.dumps(body).encode("utf-8")},
430-                },
431-            }
432:            resp = self.client.count_tokens(**kwargs)
433-            count = resp.get("inputTokens")
434-            if isinstance(count, int):
435-                return count
436-            return None
437-        except (AttributeError,) as exc:
438-            logging.warning(
439:                "BedrockClient.count_tokens: client missing count_tokens method "
440-                "(boto3 < 1.35?): %s", exc,
441-            )
442-            return None
443-        except Exception as exc:  # noqa: BLE001 ƒ?" best-effort; no raise
444:            logging.warning("BedrockClient.count_tokens failed: %s", exc)
445-            return None
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n -C 8 \"self\\.messages\\.append\\(\\{\\\"role\\\": \\\"assistant\\\"|last_text|_build_assistant_content|response\\.text|response\\.tool_calls\" compact_v5/MAIN/agent/core/query_engine.py" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n -C 5 \"def create_llm_summary|SUMMARY_SYSTEM_PROMPT|summary_input|response = summary_client\\.chat|TOKENS\\.add|return response\\.text\" compact_v5/MAIN/agent/core/compactor.py" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n -C 6 \"def run\\(|before_tokens|pruned|summary =|CompactionResult\" compact_v5/MAIN/agent/core/compactor.py" in D:\Github\sagemaker-coding-agent
2026-05-03T23:27:12.835889Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 3.6 seconds
Output:
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 
rg: regex parse error:
    (?:self\.messages\.append\(\{\)
    ^
error: unclosed group

 exited 1 in 3634ms:
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 
rg: regex parse error:
    (?:self\.messages\.append\(\{\)
    ^
error: unclosed group

 succeeded in 3672ms:
297-    def _summary_client(cls, main_client) -> Any:
298-        """Return the client to use for summary generation.
299-
300-        Per v4.9.4: when CONFIG.compaction_model is set, build a
301-        Bedrock client for that cheaper auxiliary model so summaries
302:        don't pay main-model rates. Per ADR-022 / B+5: TOKENS.add()
303-        with `agent_kind="advisor"` so the auxiliary cost is attributed
304-        separately in /cost output.
305-        """
306-        from runtime.config import CONFIG
307-        aux_model = (getattr(CONFIG, "compaction_model", "") or "").strip()
--
330-    # --------------------------------------------------------
331-    # LLM summary
332-    # --------------------------------------------------------
333-
334-    @classmethod
335:    def create_llm_summary(
336-        cls,
337-        client: Any,
338-        messages: List[Dict[str, Any]],
339-    ) -> Optional[str]:
340-        """Ask Bedrock to summarize the conversation. Returns None on
341-        failure. Per v4 verbatim with v5 adaptations:
342-        - Pre-prune oversized tool results for the summary input.
343-        - Optionally route through CONFIG.compaction_model (advisor).
344:        - Attribute advisor tokens via TOKENS.add(agent_kind='advisor').
345-        """
346-        from runtime.tokens import TOKENS
347-
348-        pruned_messages = cls._prune_tool_results_for_summary(messages)
349-        summary_client = cls._summary_client(client)
350-
351:        SUMMARY_SYSTEM_PROMPT = (
352-            "You are summarizing a coding conversation. You have ZERO tools "
353-            "available ƒ?" do NOT attempt any tool calls. Be concise but "
354-            "preserve:\n"
355-            "1. Current task and goal\n"
356-            "2. Key files modified or read\n"
--
359-            "5. What needs to happen next\n"
360-            "6. Resolved questions\n"
361-            "7. Pending questions"
362-        )
363-
364:        summary_input = list(pruned_messages)
365-        # Bedrock requires user/assistant alternation.
366:        if summary_input and summary_input[-1].get("role") == "user":
367:            summary_input.append({
368-                "role": "assistant",
369-                "content": "[Preparing summary...]",
370-            })
371:        summary_input.append({
372-            "role": "user",
373-            "content": (
374-                "Summarize the conversation above per the rubric. Be concise."
375-            ),
376-        })
377-
378-        attempts = 0
379-        while attempts <= cls.MAX_PTL_RETRIES:
380-            try:
381:                response = summary_client.chat(
382:                    messages=summary_input,
383:                    system=SUMMARY_SYSTEM_PROMPT,
384-                    tools=None,
385-                    max_tokens=2000,
386-                    temperature=0.0,
387-                )
388-                if response and response.usage:
--
390-                    agent_kind = (
391-                        "advisor"
392-                        if summary_client is not client
393-                        else "parent"
394-                    )
395:                    TOKENS.add(
396-                        response.usage,
397-                        model_id=getattr(summary_client, "model_id", None),
398-                        agent_kind=agent_kind,
399-                    )
400-                if response and response.text:
401:                    return response.text
402-                return None
403-            except Exception as exc:  # noqa: BLE001
404-                err = str(exc).lower()
405-                is_ptl = ("prompt" in err and "long" in err) \
406-                    or "too many tokens" in err
407-                if not is_ptl:
408-                    logging.warning(f"[COMPACT] LLM summary failed: {exc}")
409-                    return None
410-                attempts += 1
411:                summary_input = cls._truncate_head_for_ptl_retry(summary_input)
412:                if not summary_input:
413-                    logging.warning("[COMPACT] PTL retries exhausted")
414-                    return None
415-        return None
416-
417-    @classmethod
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 4329ms:
25-import time
26-from dataclasses import dataclass, field
27-from typing import Any, Callable, Dict, List, Optional, Tuple
28-
29-
30-# ============================================================
31:# CompactionResult
32-# ============================================================
33-
34-@dataclass
35:class CompactionResult:
36-    """Outcome of a compact() call."""
37-
38-    success: bool
39-    summary: str = ""
40-    messages_after: List[Dict[str, Any]] = field(default_factory=list)
41-    tokens_before: int = 0
--
203-        max_context: int,
204-    ) -> Tuple[List[Dict[str, Any]], int]:
205-        """Truncate tool results that are far past PRUNE_PROTECT_TOKENS.
206-
207-        Keeps the head + tail of each oversized result so the model
208-        retains some signal but the bulk is removed. Returns
209:        (pruned_messages, tokens_saved).
210-        """
211-        if not messages:
212-            return messages, 0
213-
214:        pruned = copy.deepcopy(messages)
215-        tool_name_map: Dict[str, str] = {}
216-        # Build tool_use_id ƒ+' tool_name map so we can skip protected tools.
217:        for msg in pruned:
218-            content = msg.get("content")
219-            if isinstance(content, list):
220-                for item in content:
221-                    if isinstance(item, dict) and item.get("type") == "tool_use":
222-                        tool_name_map[item.get("id", "")] = item.get("name", "")
223-
224-        # Walk most-recent ƒ+' oldest; protect the last PROTECT_TOKENS worth.
225-        running_tokens = 0
226-        tokens_saved = 0
227:        for msg in reversed(pruned):
228-            content = msg.get("content")
229-            if not isinstance(content, list):
230-                running_tokens += cls.estimate_tokens(msg)
231-                continue
232-            for block in content:
233-                if not (isinstance(block, dict) and block.get("type") == "tool_result"):
--
241-                    running_tokens += block_tokens
242-                    if running_tokens > cls.PRUNE_PROTECT_TOKENS \
243-                       and len(inner) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
244-                        head = inner[: cls.SUMMARY_TOOL_RESULT_HEAD]
245-                        tail = inner[-cls.SUMMARY_TOOL_RESULT_TAIL :]
246-                        new_text = (
247:                            f"{head}\n... [pruned "
248-                            f"{len(inner) - len(head) - len(tail):,} chars] ...\n{tail}"
249-                        )
250-                        block["content"] = new_text
251-                        tokens_saved += cls.estimate_tokens(inner) - cls.estimate_tokens(new_text)
252-                elif isinstance(inner, list):
253-                    for sub in inner:
--
256-                            running_tokens += cls.estimate_tokens(txt)
257-                            if running_tokens > cls.PRUNE_PROTECT_TOKENS \
258-                               and len(txt) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
259-                                head = txt[: cls.SUMMARY_TOOL_RESULT_HEAD]
260-                                tail = txt[-cls.SUMMARY_TOOL_RESULT_TAIL :]
261-                                new_text = (
262:                                    f"{head}\n... [pruned "
263-                                    f"{len(txt) - len(head) - len(tail):,} chars] ...\n{tail}"
264-                                )
265-                                sub["text"] = new_text
266-                                tokens_saved += cls.estimate_tokens(txt) - cls.estimate_tokens(new_text)
267-        # Codex Block-A iter-1 finding #2 (MEDIUM) lock: v4 invariant ƒ?"
268-        # if savings are too small, return ORIGINAL messages (don't
269-        # accept the fidelity loss for marginal token wins). Per v4
270-        # PRUNE_MIN_SAVINGS = 10,000 tokens (constant kept above).
271-        if tokens_saved < cls.PRUNE_MIN_SAVINGS:
272-            return messages, 0
273:        return pruned, tokens_saved
274-
275-    # --------------------------------------------------------
276-    # Should compact?
277-    # --------------------------------------------------------
278-
279-    @classmethod
--
342-        - Pre-prune oversized tool results for the summary input.
343-        - Optionally route through CONFIG.compaction_model (advisor).
344-        - Attribute advisor tokens via TOKENS.add(agent_kind='advisor').
345-        """
346-        from runtime.tokens import TOKENS
347-
348:        pruned_messages = cls._prune_tool_results_for_summary(messages)
349-        summary_client = cls._summary_client(client)
350-
351-        SUMMARY_SYSTEM_PROMPT = (
352-            "You are summarizing a coding conversation. You have ZERO tools "
353-            "available ƒ?" do NOT attempt any tool calls. Be concise but "
354-            "preserve:\n"
--
358-            "4. Where we left off\n"
359-            "5. What needs to happen next\n"
360-            "6. Resolved questions\n"
361-            "7. Pending questions"
362-        )
363-
364:        summary_input = list(pruned_messages)
365-        # Bedrock requires user/assistant alternation.
366-        if summary_input and summary_input[-1].get("role") == "user":
367-            summary_input.append({
368-                "role": "assistant",
369-                "content": "[Preparing summary...]",
370-            })
--
435-                inner = block.get("content")
436-                if isinstance(inner, str) and len(inner) > cls.SUMMARY_TOOL_RESULT_THRESHOLD:
437-                    head = inner[: cls.SUMMARY_TOOL_RESULT_HEAD]
438-                    tail = inner[-cls.SUMMARY_TOOL_RESULT_TAIL :]
439-                    new_block = dict(block)
440-                    new_block["content"] = (
441:                        f"{head}\n... [pruned for summary] ...\n{tail}"
442-                    )
443-                    new_blocks.append(new_block)
444-                    mutated = True
445-                else:
446-                    new_blocks.append(block)
447-            if mutated:
--
503-                "[END SUMMARY ƒ?" Continuing from here]"
504-            ),
505-        }
506-        return [summary_msg] + recent
507-
508-    @classmethod
509:    def run(
510-        cls,
511-        client: Any,
512-        messages: List[Dict[str, Any]],
513-        max_tokens: int = 200_000,
514:    ) -> CompactionResult:
515-        """End-to-end: prune ƒ+' summarize ƒ+' compact. Single entry point."""
516:        before_tokens = cls.estimate_tokens(messages)
517-        if not cls.should_compact(messages, max_tokens):
518:            return CompactionResult(
519-                success=False,
520-                error="compact not needed (under 80% trigger)",
521:                tokens_before=before_tokens,
522:                tokens_after=before_tokens,
523-                messages_after=list(messages),
524-            )
525:        pruned, _saved = cls.prune_tool_outputs(messages, max_tokens)
526:        summary = cls.create_llm_summary(client, pruned)
527-        if not summary:
528:            return CompactionResult(
529-                success=False,
530-                error="LLM summary returned empty",
531:                tokens_before=before_tokens,
532:                tokens_after=cls.estimate_tokens(pruned),
533:                messages_after=pruned,
534-            )
535:        new_messages = cls.compact(pruned, summary)
536-        after_tokens = cls.estimate_tokens(new_messages)
537:        return CompactionResult(
538-            success=True,
539-            summary=summary,
540-            messages_after=new_messages,
541:            tokens_before=before_tokens,
542-            tokens_after=after_tokens,
543-        )
544-
545-
546-# ============================================================
547-# Runnable cache_edits ƒ?" Bedrock cache_control adaptation
--
625-
626-AUTO_COMPACT = AutoCompactCircuitBreaker()
627-
628-
629-__all__ = [
630-    "Compactor",
631:    "CompactionResult",
632-    "AutoCompactCircuitBreaker",
633-    "AUTO_COMPACT",
634-    "apply_cache_control_to_blocks",
635-    "count_tokens_via_haiku_fallback",
636-]
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n -C 12 "self.messages.append|last_text =|_build_assistant_content|if not response.tool_calls" compact_v5/MAIN/agent/core/query_engine.py' in D:\Github\sagemaker-coding-agent
 succeeded in 1902ms:
359-            )
360-
361-        # Append user turn (Bedrock requires alternation; merge into trailing
362-        # user if needed ƒ?" matches v4 sagemaker_agent.py:8744).
363-        if self.messages and self.messages[-1].get("role") == "user":
364-            prev = self.messages[-1]
365-            prev_content = prev.get("content", "")
366-            if isinstance(prev_content, str):
367-                prev["content"] = prev_content + "\n\n" + user_message
368-            elif isinstance(prev_content, list):
369-                prev_content.append({"type": "text", "text": user_message})
370-            else:
371:                self.messages.append({"role": "user", "content": user_message})
372-        else:
373:            self.messages.append({"role": "user", "content": user_message})
374-
375-        # Defer-import to avoid circular import at module-load.
376-        from tools.registry import (
377-            PLAN_MODE_ALLOWED_TOOLS,
378-            apply_tool_search_deferral,
379-            find_tool_by_name,
380-        )
381-        from tools.tool_search import tool_search_discovered_names
382-
383-        # Phase 10 wiring (Codex BLOCKER fix): if a SkillManager is bound to
384-        # this engine, inject (a) the active skill body into the dynamic
385-        # tail of the system prompt and (b) a Hermes-filtered "skills
--
447-                        "Consider using: " + ", ".join(relevant) +
448-                        "\nUse the `skill` tool to activate one if it matches."
449-                    )
450-                    last_user = self.messages[-1]
451-                    content = last_user.get("content")
452-                    if isinstance(content, str):
453-                        last_user["content"] = content + reminder
454-                    elif isinstance(content, list):
455-                        content.append({"type": "text", "text": reminder})
456-            except Exception as exc:  # noqa: BLE001 ƒ?" skill machinery never raises into agent loop
457-                logging.warning("[skill-wiring] %s: %s", type(exc).__name__, exc)
458-
459:        last_text = ""
460-        stop_reason = ""
461-        turns_used = 0
462-
463-        for turn in range(self.max_turns):
464-            # User-requested stop (Phase 11 wires this to the Stop button).
465-            if self.on_stop_check and self.on_stop_check():
466-                output_fn("[Stopped by user]")
467-                stop_reason = "user_stop"
468-                break
469-
470-            # Block M-2 (PORT_LOG #084) ƒ?" structured-output retry-limit
471-            # guard. When `synthetic_output_tool_name` is configured, count
--
601-                # the warning (`>` would skip parity-100% cases).
602-                if limit > 0 and _TOKENS.session_cost >= limit:
603-                    if not getattr(self, "_warned_over_budget", False):
604-                        output_fn(
605-                            f"[Cost ${_TOKENS.session_cost:.4f} passed "
606-                            f"budget ${limit:.2f} ƒ?" continuing.]"
607-                        )
608-                        self._warned_over_budget = True
609-            except Exception:
610-                pass
611-
612-            # Append assistant turn (text + tool_use blocks, plus thinking).
613:            assistant_content = self._build_assistant_content(response)
614:            self.messages.append({"role": "assistant", "content": assistant_content})
615-
616-            if response.text:
617:                last_text = response.text
618-
619-            # Block A ƒ?" auto-compact gate. Per-turn check: if the
620-            # message buffer has crossed the 80% threshold AND the
621-            # circuit breaker allows another attempt, run Compactor.
622-            try:
623-                from core.compactor import Compactor, AUTO_COMPACT
624-                from runtime.config import CONFIG as _CFG_AC
625-                _max_ctx = getattr(_CFG_AC, "context_max_tokens", 200_000)
626-                if Compactor.should_compact(self.messages, _max_ctx):
627-                    _ok, _why = AUTO_COMPACT.try_attempt()
628-                    if _ok:
629-                        _result = Compactor.run(self.client, self.messages, _max_ctx)
--
633-                                f"{_result.tokens_before - _result.tokens_after:,} "
634-                                f"tokens; continuing."
635-                            )
636-                            self.messages = _result.messages_after
637-                    else:
638-                        # Cooldown / cap message ƒ?" log once per turn, no
639-                        # spam since try_attempt returns reason text.
640-                        output_fn(f"[auto-compact skipped: {_why}]")
641-            except Exception:
642-                pass
643-
644-            # Stop conditions: end_turn / no tool_use blocks ƒ+' final answer.
645:            if not response.tool_calls:
646-                # Block F2 ƒ?" auto-continuation under iteration budget. Only
647-                # parent agents (not sub-agents) and only when CONFIG flag
648-                # is opt-in (default OFF per Wave 6 NLT row #21). Cost-cap
649-                # halt has priority inside check_iteration_budget().
650-                try:
651-                    from runtime.config import CONFIG as _CFG_F2
652-                    if getattr(_CFG_F2, "enable_token_budget_continuation", False):
653-                        from core.budget_continuation import (
654-                            check_iteration_budget,
655-                            create_budget_tracker,
656-                            ContinueDecision,
657-                            StopDecision,
--
670-                            self._budget_tracker,
671-                            iter_used=self.budget.used(),
672-                            iter_total=self.budget.total(),
673-                            is_subagent=_is_sub,
674-                            session_cost=_sc,
675-                            session_cost_limit=_scl,
676-                        )
677-                        if isinstance(decision, ContinueDecision):
678-                            # Surface the assistant's interim text + nudge to keep
679-                            # working. Continuing the for-loop re-invokes Bedrock.
680-                            if response.text:
681-                                output_fn(response.text)
682:                            self.messages.append({
683-                                "role": "user",
684-                                "content": decision.nudge_message,
685-                            })
686-                            continue
687-                        # Codex iter-1 finding #1 lock: surface StopDecision
688-                        # telemetry. Runnable logs the equivalent completion
689-                        # event at query.ts:1343-1354. v5 routes through the
690-                        # AUDIT singleton so /diffs / /regression forensics
691-                        # can observe budget-driven stops; stderr-style
692-                        # logging.info also surfaces it for headless runs.
693-                        if isinstance(decision, StopDecision):
694-                            _ce = decision.completion_event
--
1020-                        _AUDIT.log(
1021-                            session_id=self.session_id,
1022-                            action="tool_error",
1023-                            tool_name=call.name,
1024-                            parameters=call.input or {},
1025-                            result_summary=f"{type(exc).__name__}: {exc}",
1026-                            user_approved=False,
1027-                        )
1028-                    except Exception:
1029-                        pass
1030-
1031-            # Append the tool_results as a user turn (Bedrock convention).
1032:            self.messages.append({"role": "user", "content": tool_results})
1033-
1034-        else:  # for-loop fell through without break
1035-            stop_reason = "max_turns"
1036-            output_fn(f"[Max turns reached: {self.max_turns}]")
1037-
1038-        return QueryResult(
1039-            text=last_text,
1040-            messages=list(self.messages),
1041-            stop_reason=stop_reason or "end_turn",
1042-            turns_used=turns_used,
1043-            budget_used=self.budget.used(),
1044-        )
1045-
1046-    # ------------------------------------------------------------
1047-    # Internal: assemble assistant turn content from a Bedrock Response
1048-    # ------------------------------------------------------------
1049-
1050-    @staticmethod
1051:    def _build_assistant_content(response: Any) -> List[Dict[str, Any]]:
1052-        """Construct a Bedrock-shaped assistant content list from a Response.
1053-
1054-        Order: thinking blocks (if any) ƒ+' text ƒ+' tool_use. The thinking
1055-        block is preserved so the next turn's API call carries it back to
1056-        the model (Bedrock requires this for extended thinking continuity).
1057-        """
1058-        blocks: List[Dict[str, Any]] = []
1059-        thinking = getattr(response, "thinking", "") or ""
1060-        if thinking:
1061-            blocks.append({"type": "thinking", "thinking": thinking})
1062-        if response.text:
1063-            blocks.append({"type": "text", "text": response.text})
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

codex
The key read path is present: `query_engine.py` reads `CONFIG.context_max_tokens` immediately before `Compactor.should_compact`, and `Agent` keeps one engine instance across both `run` calls. Iƒ?Tm doing one local token-estimator sanity check because the threshold is estimator-driven, not based solely on Bedrockƒ?Ts reported tokens.
2026-05-03T23:27:31.510506Z ERROR codex_core::tools::router: error=`"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$env:PYTHONPATH='"'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent'; python -c \"from runtime.tokens import rough_token_count_for_message; from core.compactor import Compactor; line='Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. '; prompt='''You are reviewing a long conversation history. Below is a recap of\\nprior context - most of it is filler. After the recap, please answer\\nONE SHORT question.\\n\\n=== RECAP (do not summarize back; just keep in mind) ===\\n{}=== END RECAP ===\\n\\nQUESTION: What is 2 + 3? Answer with a single number, no explanation.\\n'''.format((line+'\\n')*2700); msgs=[{'role':'user','content':prompt},{'role':'assistant','content':[{'type':'text','text':'5'}]}]; print(len(prompt)); print(rough_token_count_for_message(msgs[0])); print(Compactor.estimate_tokens(msgs)); print(Compactor.should_compact(msgs,100000))\""` rejected: blocked by policy
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$env:PYTHONPATH='"'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent'; python -c \"from runtime.tokens import rough_token_count_for_message; from core.compactor import Compactor; line='Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. '; prompt='''You are reviewing a long conversation history. Below is a recap of\\nprior context - most of it is filler. After the recap, please answer\\nONE SHORT question.\\n\\n=== RECAP (do not summarize back; just keep in mind) ===\\n{}=== END RECAP ===\\n\\nQUESTION: What is 2 + 3? Answer with a single number, no explanation.\\n'''.format((line+'\\n')*2700); msgs=[{'role':'user','content':prompt},{'role':'assistant','content':[{'type':'text','text':'5'}]}]; print(len(prompt)); print(rough_token_count_for_message(msgs[0])); print(Compactor.estimate_tokens(msgs)); print(Compactor.should_compact(msgs,100000))\"" in D:\Github\sagemaker-coding-agent
 declined in 0ms:
`"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$env:PYTHONPATH='"'D:\\Github\\sagemaker-coding-agent\\compact_v5\\MAIN\\agent'; python -c \"from runtime.tokens import rough_token_count_for_message; from core.compactor import Compactor; line='Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. '; prompt='''You are reviewing a long conversation history. Below is a recap of\\nprior context - most of it is filler. After the recap, please answer\\nONE SHORT question.\\n\\n=== RECAP (do not summarize back; just keep in mind) ===\\n{}=== END RECAP ===\\n\\nQUESTION: What is 2 + 3? Answer with a single number, no explanation.\\n'''.format((line+'\\n')*2700); msgs=[{'role':'user','content':prompt},{'role':'assistant','content':[{'type':'text','text':'5'}]}]; print(len(prompt)); print(rough_token_count_for_message(msgs[0])); print(Compactor.estimate_tokens(msgs)); print(Compactor.should_compact(msgs,100000))\""` rejected: blocked by policy
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "def estimate_message_tokens|def rough_token_count_for_message|def rough_token_count_for_block" compact_v5/MAIN/agent/runtime/tokens.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "MODEL_COSTS|haiku-4-5|claude-haiku" compact_v5/MAIN/agent/runtime/tokens.py' in D:\Github\sagemaker-coding-agent
 succeeded in 2513ms:
6:- MODEL_COSTS for Haiku 4.5 + Sonnet 4.5 (B-10, R8 #34/#68)
17:PORT_LOG: see #039 (TokenTracker), #040 (MODEL_COSTS+per-agent),
50:# B-10 ƒ?" MODEL_COSTS (R8 #34, #68; Bedrock-only subset)
61:MODEL_COSTS: Dict[str, Dict[str, float]] = {
62:    "anthropic.claude-haiku-4-5-20251001-v1:0": {"input": 0.001, "output": 0.005},
69:_MODEL_PRICING = MODEL_COSTS
132:    miss MODEL_COSTS entirely and TOKENS to record $0.
134:    NOTE: stripping the prefix gets the BASE rate from MODEL_COSTS;
156:    "anthropic.claude-haiku-4-5-20251001-v1:0",
408:            pricing = MODEL_COSTS.get(mid)
433:                        f"Add to MODEL_COSTS dict in runtime/tokens.py."
487:        pricing = MODEL_COSTS.get(mid)
615:    "MODEL_COSTS",
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 3213ms:
215:def estimate_message_tokens(text: str, padding_factor: float = 4.0 / 3.0) -> int:
254:def rough_token_count_for_block(block: Any) -> int:
285:def rough_token_count_for_message(msg: Dict[str, Any]) -> int:
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

2026-05-03T23:27:41.971605Z ERROR codex_core::tools::router: error=`"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "python -c \"from runtime.tokens import rough_token_count_for_message; from core.compactor import Compactor; line='Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. '; recap=(line+'\\n')*2700; prompt='QUESTION: What is 2 + 3?\\n'+recap; msgs=[{'role':'user','content':prompt},{'role':'assistant','content':[{'type':'text','text':'5'}]}]; print(len(prompt)); print(rough_token_count_for_message(msgs[0])); print(Compactor.estimate_tokens(msgs)); print(Compactor.should_compact(msgs,100000))\""` rejected: blocked by policy
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "python -c \"from runtime.tokens import rough_token_count_for_message; from core.compactor import Compactor; line='Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. '; recap=(line+'\\n')*2700; prompt='QUESTION: What is 2 + 3?\\n'+recap; msgs=[{'role':'user','content':prompt},{'role':'assistant','content':[{'type':'text','text':'5'}]}]; print(len(prompt)); print(rough_token_count_for_message(msgs[0])); print(Compactor.estimate_tokens(msgs)); print(Compactor.should_compact(msgs,100000))\"" in D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent
 declined in 0ms:
`"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "python -c \"from runtime.tokens import rough_token_count_for_message; from core.compactor import Compactor; line='Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. '; recap=(line+'\\n')*2700; prompt='QUESTION: What is 2 + 3?\\n'+recap; msgs=[{'role':'user','content':prompt},{'role':'assistant','content':[{'type':'text','text':'5'}]}]; print(len(prompt)); print(rough_token_count_for_message(msgs[0])); print(Compactor.estimate_tokens(msgs)); print(Compactor.should_compact(msgs,100000))\""` rejected: blocked by policy
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n -C 20 "def estimate_message_tokens|def rough_token_count_for_message" compact_v5/MAIN/agent/runtime/tokens.py' in D:\Github\sagemaker-coding-agent
 succeeded in 1857ms:
195-
196-def bytes_per_token_for_file_type(filename: str) -> float:
197-    """Return the bytes-per-token ratio for a filename's extension.
198-
199-    Falls back to 4.0 (plain-text) for unknown extensions. Used by the
200-    rough estimator to budget tool output sizes.
201-    """
202-    if not filename:
203-        return 4.0
204-    lower = filename.lower()
205-    for ext, ratio in _BYTES_PER_TOKEN_BY_EXT.items():
206-        if lower.endswith(ext):
207-            return ratio
208-    return 4.0
209-
210-
211-# ============================================================
212-# B-6 ƒ?" estimateMessageTokens with 4/3 padding (R4 #39)
213-# ============================================================
214-
215:def estimate_message_tokens(text: str, padding_factor: float = 4.0 / 3.0) -> int:
216-    """Rough token estimator with 4/3 padding (Bedrock-side overhead).
217-
218-    v4 used `len(text) // 3`. Runnable's microCompact.ts:164-205 adds a
219-    4/3 multiplier so the estimate accounts for Bedrock framing tokens
220-    (turn boundaries, role markers). Returns ceil(len/3 * 4/3) = len*4/9
221-    rounded up.
222-    """
223-    if not text:
224-        return 0
225-    base = len(text) / 3.0
226-    return int(base * padding_factor + 0.5)
227-
228-
229-# ============================================================
230-# B-7 ƒ?" hasThinkingBlocks (R4 #43)
231-# ============================================================
232-
233-def has_thinking_blocks(message: Dict[str, Any]) -> bool:
234-    """True if a message contains an Anthropic-format `thinking` block.
235-
--
265-    if btype == "text":
266-        return estimate_message_tokens(block.get("text", ""))
267-    if btype == "tool_use":
268-        # Tool name + input as JSON (dense, 2 bytes/token).
269-        name_tokens = estimate_message_tokens(block.get("name", ""))
270-        import json as _json
271-        input_tokens = int(len(_json.dumps(block.get("input", {}))) / 2.0 + 0.5)
272-        return name_tokens + input_tokens
273-    if btype == "tool_result":
274-        content = block.get("content", "")
275-        if isinstance(content, list):
276-            return sum(rough_token_count_for_block(c) for c in content)
277-        return estimate_message_tokens(str(content))
278-    if btype in {"image", "input_image"}:
279-        return IMAGE_MAX_TOKEN_SIZE
280-    if btype in {"thinking", "redacted_thinking"}:
281-        return estimate_message_tokens(block.get("thinking", "") or block.get("data", ""))
282-    return 0
283-
284-
285:def rough_token_count_for_message(msg: Dict[str, Any]) -> int:
286-    """Sum of `rough_token_count_for_block` for each block in a message."""
287-    if not isinstance(msg, dict):
288-        return 0
289-    content = msg.get("content")
290-    if isinstance(content, str):
291-        return estimate_message_tokens(content)
292-    if isinstance(content, list):
293-        return sum(rough_token_count_for_block(b) for b in content)
294-    return 0
295-
296-
297-# ============================================================
298-# TokenTracker ƒ?" verbatim port of v4 + per-agent attribution
299-# ============================================================
300-
301-# Sentinel for distinguishing "not yet recorded" from "recorded as 0".
302-_NO_USAGE_RECORD: Optional[Dict[str, int]] = None
303-
304-
305-class TokenTracker:
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

codex
**Axis A: REJECT**

Fixes 1, 2, and 5 are closed. `CONFIG.context_max_tokens = 100_000` flows into the real gate: [test_r2_compact.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:130) sets it, [query_engine.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/query_engine.py:625) reads `getattr(_CFG_AC, "context_max_tokens", 200_000)`, then calls `Compactor.should_compact(...)` at line 626. `should_compact` uses the passed max at [compactor.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/compactor.py:280).

But fixes 3 and 4 are only partially closed. `api_calls >= 3` proves an extra model call likely happened, but not that compaction succeeded or that `[CONVERSATION SUMMARY]` was written. A failed summary call still increments `TOKENS.api_calls`, leaves raw history intact, and can let T2 pass. Require `compact_log_seen`, `api_calls_after_t1 >= 2`, and preferably inspect `agent.messages` for `[CONVERSATION SUMMARY]`.

The T1 regex is good. The T2 recall assertion is too loose because accepting `"5"` can pass from the prior assistant answer or a weak summary that omitted the actual question.

**Axis B: APPROVE WITH CAVEAT**

Cost is bounded enough for a pre-flight AWS run. Worst case is probably closer to `$0.18-$0.30` than `$0.10`, because the auto-compact summary call appears to resend the large user message; prompt caching here mainly applies to system prompt blocks, not that huge user recap. Still under `$0.50`.

`on_stop_check` and `max_turns=4` are reasonable, but note the cost halt is checked at loop boundaries, not before the internal compaction-summary call.

**Axis C: REJECT**

Iter-2 provides empirical evidence for real Bedrock large-input handling, token accumulation, and likely `should_compact` entry.

It does not yet prove successful `Compactor.run` replacement, existence of the `[CONVERSATION SUMMARY]` block, post-compact buffer survival, or recall from compacted summary rather than raw history. Also, implementation creates the summary as a `role: "user"` message, not a system-role block.

**FINAL: REJECT**

Do not run AWS yet. Minimal fix: make compaction success mandatory with `compact_log_seen` or direct `agent.messages` summary-block assertion, assert T2 input dropped materially versus T1, and remove `"5"` from the T2 recall acceptance.
tokens used
69,427
**Axis A: REJECT**

Fixes 1, 2, and 5 are closed. `CONFIG.context_max_tokens = 100_000` flows into the real gate: [test_r2_compact.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:130) sets it, [query_engine.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/query_engine.py:625) reads `getattr(_CFG_AC, "context_max_tokens", 200_000)`, then calls `Compactor.should_compact(...)` at line 626. `should_compact` uses the passed max at [compactor.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/compactor.py:280).

But fixes 3 and 4 are only partially closed. `api_calls >= 3` proves an extra model call likely happened, but not that compaction succeeded or that `[CONVERSATION SUMMARY]` was written. A failed summary call still increments `TOKENS.api_calls`, leaves raw history intact, and can let T2 pass. Require `compact_log_seen`, `api_calls_after_t1 >= 2`, and preferably inspect `agent.messages` for `[CONVERSATION SUMMARY]`.

The T1 regex is good. The T2 recall assertion is too loose because accepting `"5"` can pass from the prior assistant answer or a weak summary that omitted the actual question.

**Axis B: APPROVE WITH CAVEAT**

Cost is bounded enough for a pre-flight AWS run. Worst case is probably closer to `$0.18-$0.30` than `$0.10`, because the auto-compact summary call appears to resend the large user message; prompt caching here mainly applies to system prompt blocks, not that huge user recap. Still under `$0.50`.

`on_stop_check` and `max_turns=4` are reasonable, but note the cost halt is checked at loop boundaries, not before the internal compaction-summary call.

**Axis C: REJECT**

Iter-2 provides empirical evidence for real Bedrock large-input handling, token accumulation, and likely `should_compact` entry.

It does not yet prove successful `Compactor.run` replacement, existence of the `[CONVERSATION SUMMARY]` block, post-compact buffer survival, or recall from compacted summary rather than raw history. Also, implementation creates the summary as a `role: "user"` message, not a system-role block.

**FINAL: REJECT**

Do not run AWS yet. Minimal fix: make compaction success mandatory with `compact_log_seen` or direct `agent.messages` summary-block assertion, assert T2 input dropped materially versus T1, and remove `"5"` from the T2 recall acceptance.
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

codex
The iter-3 test has the stronger assertions in place. I’m checking the auto-compact call site and token accounting now, because the remaining design risk is whether the “T2 estimate” is actually measuring only T2 or is polluted by the summary call.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n -C 35 \"auto-compact|Compactor\\.run|should_compact|context_max_tokens|messages = compact|messages_after\" compact_v5/MAIN/agent/core/query_engine.py" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n -C 20 "def add|session_input|api_calls|input_tokens" compact_v5/MAIN/agent/runtime/tokens.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"compact_proven|summary_marker_seen|t2_dropped_materially|t2_input_estimate|what is 2|2 \\+ 3|\\[CONVERSATION SUMMARY\\]|Turn 2\" compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py compact_v5/MAIN/agent/core/compactor.py" in D:\Github\sagemaker-coding-agent
 succeeded in 2753ms:
584-                            f"tools={len(response.tool_calls or [])}; "
585-                            f"text_chars={len(response.text or '')}; "
586-                            f"thinking_chars={len(getattr(response, 'thinking', '') or '')}"
587-                        ),
588-                        user_approved=False,
589-                    )
590-                except Exception:
591-                    pass
592-                # Block B+ (PORT_LOG #052): per-turn cost-vs-budget runtime
593-                # warning. v4 sagemaker_agent.py:8787 prints
594-                #   `[Cost ${session_cost} passed budget ${limit} — continuing.]`
595-                # NOT a hard halt — per user 2026-05-03 update to plan v3,
596-                # v5 matches v4 UX: warn and continue. True hard halt is at
597-                # cloud-budget level (AWS Budget Action / GCP).
598-                from runtime.config import CONFIG as _CFG
599-                limit = getattr(_CFG, "session_cost_limit", 0.0)
600-                # Block B+ Codex finding #1 lock: `>=` so exact-100% trips
601-                # the warning (`>` would skip parity-100% cases).
602-                if limit > 0 and _TOKENS.session_cost >= limit:
603-                    if not getattr(self, "_warned_over_budget", False):
604-                        output_fn(
605-                            f"[Cost ${_TOKENS.session_cost:.4f} passed "
606-                            f"budget ${limit:.2f} — continuing.]"
607-                        )
608-                        self._warned_over_budget = True
609-            except Exception:
610-                pass
611-
612-            # Append assistant turn (text + tool_use blocks, plus thinking).
613-            assistant_content = self._build_assistant_content(response)
614-            self.messages.append({"role": "assistant", "content": assistant_content})
615-
616-            if response.text:
617-                last_text = response.text
618-
619:            # Block A — auto-compact gate. Per-turn check: if the
620-            # message buffer has crossed the 80% threshold AND the
621-            # circuit breaker allows another attempt, run Compactor.
622-            try:
623-                from core.compactor import Compactor, AUTO_COMPACT
624-                from runtime.config import CONFIG as _CFG_AC
625:                _max_ctx = getattr(_CFG_AC, "context_max_tokens", 200_000)
626:                if Compactor.should_compact(self.messages, _max_ctx):
627-                    _ok, _why = AUTO_COMPACT.try_attempt()
628-                    if _ok:
629:                        _result = Compactor.run(self.client, self.messages, _max_ctx)
630-                        if _result.success:
631-                            output_fn(
632:                                f"[auto-compact] saved "
633-                                f"{_result.tokens_before - _result.tokens_after:,} "
634-                                f"tokens; continuing."
635-                            )
636:                            self.messages = _result.messages_after
637-                    else:
638-                        # Cooldown / cap message — log once per turn, no
639-                        # spam since try_attempt returns reason text.
640:                        output_fn(f"[auto-compact skipped: {_why}]")
641-            except Exception:
642-                pass
643-
644-            # Stop conditions: end_turn / no tool_use blocks → final answer.
645-            if not response.tool_calls:
646-                # Block F2 — auto-continuation under iteration budget. Only
647-                # parent agents (not sub-agents) and only when CONFIG flag
648-                # is opt-in (default OFF per Wave 6 NLT row #21). Cost-cap
649-                # halt has priority inside check_iteration_budget().
650-                try:
651-                    from runtime.config import CONFIG as _CFG_F2
652-                    if getattr(_CFG_F2, "enable_token_budget_continuation", False):
653-                        from core.budget_continuation import (
654-                            check_iteration_budget,
655-                            create_budget_tracker,
656-                            ContinueDecision,
657-                            StopDecision,
658-                        )
659-                        if self._budget_tracker is None:
660-                            self._budget_tracker = create_budget_tracker()
661-                        _is_sub = self.agent_kind != "parent"
662-                        _sc = 0.0
663-                        try:
664-                            from runtime.tokens import TOKENS as _TOKENS_F2
665-                            _sc = float(getattr(_TOKENS_F2, "session_cost", 0.0))
666-                        except Exception:
667-                            _sc = 0.0
668-                        _scl = float(getattr(_CFG_F2, "session_cost_limit", 0.0))
669-                        decision = check_iteration_budget(
670-                            self._budget_tracker,
671-                            iter_used=self.budget.used(),
672-                            iter_total=self.budget.total(),
673-                            is_subagent=_is_sub,
674-                            session_cost=_sc,
675-                            session_cost_limit=_scl,
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 2767ms:
251-# B-4 — roughTokenCountEstimationForBlock (R4 #44)
252-# ============================================================
253-
254-def rough_token_count_for_block(block: Any) -> int:
255-    """Per-block-type token estimator.
256-
257-    text/tool_use/tool_result/image — each has different size math.
258-    Images are capped at IMAGE_MAX_TOKEN_SIZE per Anthropic billing.
259-    """
260-    if isinstance(block, str):
261-        return estimate_message_tokens(block)
262-    if not isinstance(block, dict):
263-        return 0
264-    btype = block.get("type")
265-    if btype == "text":
266-        return estimate_message_tokens(block.get("text", ""))
267-    if btype == "tool_use":
268-        # Tool name + input as JSON (dense, 2 bytes/token).
269-        name_tokens = estimate_message_tokens(block.get("name", ""))
270-        import json as _json
271:        input_tokens = int(len(_json.dumps(block.get("input", {}))) / 2.0 + 0.5)
272:        return name_tokens + input_tokens
273-    if btype == "tool_result":
274-        content = block.get("content", "")
275-        if isinstance(content, list):
276-            return sum(rough_token_count_for_block(c) for c in content)
277-        return estimate_message_tokens(str(content))
278-    if btype in {"image", "input_image"}:
279-        return IMAGE_MAX_TOKEN_SIZE
280-    if btype in {"thinking", "redacted_thinking"}:
281-        return estimate_message_tokens(block.get("thinking", "") or block.get("data", ""))
282-    return 0
283-
284-
285-def rough_token_count_for_message(msg: Dict[str, Any]) -> int:
286-    """Sum of `rough_token_count_for_block` for each block in a message."""
287-    if not isinstance(msg, dict):
288-        return 0
289-    content = msg.get("content")
290-    if isinstance(content, str):
291-        return estimate_message_tokens(content)
292-    if isinstance(content, list):
--
326-        self.reset()
327-
328-    @property
329-    def _config(self):
330-        """Resolve CONFIG lazily so reloads in tests don't strand us."""
331-        if self._config_override is not None:
332-            return self._config_override
333-        from runtime.config import CONFIG as _CFG  # noqa: F401 — late import
334-        return _CFG
335-
336-    # --------------------------------------------------------
337-    # Reset / state
338-    # --------------------------------------------------------
339-
340-    def reset(self):
341-        """Reset all counters."""
342-        with self._lock:
343-            self._reset_unlocked()
344-
345-    def _reset_unlocked(self):
346:        self.session_input = 0
347-        self.session_output = 0
348-        self.session_total = 0
349-        self.session_cache_read = 0
350-        self.session_cache_write = 0
351-        self.last_input = 0
352-        self.last_output = 0
353:        self.api_calls = 0
354-        self.session_cost = 0.0
355-        self.last_cost = 0.0
356-        self._model_id = self._config.model_id
357-        self._budget_warned = False
358-        self._budget_stopped = False
359-        # Per-agent attribution (Plan v3 §Block B). Parent always tracked
360-        # by default; sub-agents accumulate under their type-string key.
361:        self.parent_input_tokens = 0
362-        self.parent_output_tokens = 0
363-        self.parent_cost = 0.0
364:        self.subagent_input_tokens: Dict[str, int] = {}
365-        self.subagent_output_tokens: Dict[str, int] = {}
366-        self.subagent_cost: Dict[str, float] = {}
367-        # Last-usage record for tokenCountWithEstimation walks (B-8).
368-        self._last_usage_record: Optional[Dict[str, int]] = None
369-
370-    # --------------------------------------------------------
371-    # Add usage (the singleton write path)
372-    # --------------------------------------------------------
373-
374:    def add(
375-        self,
376-        usage: Dict[str, int],
377-        model_id: Optional[str] = None,
378-        agent_kind: str = "parent",
379-    ):
380-        """Add usage from API response (thread-safe).
381-
382-        agent_kind: attribution bucket. "parent" (default) for the main
383-        agent loop; sub-agent type-strings ("build", "explore", "verify",
384-        "plan", "review", "general") for spawned children. The session
385-        rollup totals always include both.
386-        """
387:        input_tokens = int(usage.get("input_tokens", 0) or 0)
388-        output_tokens = int(usage.get("output_tokens", 0) or 0)
389:        cache_read = int(usage.get("cache_read_input_tokens", 0) or 0)
390:        cache_write = int(usage.get("cache_creation_input_tokens", 0) or 0)
391-
392-        with self._lock:
393:            self.last_input = input_tokens
394-            self.last_output = output_tokens
395:            self.session_input += input_tokens
396-            self.session_output += output_tokens
397:            self.session_total = self.session_input + self.session_output
398-            self.session_cache_read += cache_read
399-            self.session_cache_write += cache_write
400:            self.api_calls += 1
401-            # B-8 — record last usage so estimators can walk back.
402-            self._last_usage_record = dict(usage)
403-
404-            raw_mid = model_id or self._config.model_id
405-            mid = canonicalize_model_id(raw_mid)
406-            if model_id:
407-                self._model_id = model_id
408-            pricing = MODEL_COSTS.get(mid)
409-            cost = 0.0
410-            if pricing:
411-                # R-tier R1 PHASE A iter-3 fix: apply geo-inference
412-                # premium (1.10x) for au./us./eu./apac. profiles. Without
413-                # this, local cost tracker undercounts AWS billing by 10%.
414-                geo_mult = get_geo_multiplier(raw_mid)
415-                base_input = pricing["input"] * geo_mult
416-                base_output = pricing["output"] * geo_mult
417:                regular_input = max(0, input_tokens - cache_read - cache_write)
418-                cost = (
419-                    (regular_input / 1000) * base_input
420-                    + (cache_read / 1000) * base_input * 0.1
421-                    + (cache_write / 1000) * base_input * 1.25
422-                    + (output_tokens / 1000) * base_output
423-                )
424-                self.session_cost += cost
425-                self.last_cost = cost
426-            else:
427-                if not hasattr(self, "_warned_models"):
428-                    self._warned_models = set()
429-                if mid not in self._warned_models:
430-                    self._warned_models.add(mid)
431-                    logging.warning(
432-                        f"TokenTracker: no pricing for model '{mid}' — cost will show as $0. "
433-                        f"Add to MODEL_COSTS dict in runtime/tokens.py."
434-                    )
435-                self.last_cost = 0.0
436-
437-            # Per-agent attribution (additive — same singleton, separate buckets).
438-            if agent_kind == "parent":
439:                self.parent_input_tokens += input_tokens
440-                self.parent_output_tokens += output_tokens
441-                self.parent_cost += cost
442-            else:
443:                self.subagent_input_tokens[agent_kind] = (
444:                    self.subagent_input_tokens.get(agent_kind, 0) + input_tokens
445-                )
446-                self.subagent_output_tokens[agent_kind] = (
447-                    self.subagent_output_tokens.get(agent_kind, 0) + output_tokens
448-                )
449-                self.subagent_cost[agent_kind] = (
450-                    self.subagent_cost.get(agent_kind, 0.0) + cost
451-                )
452-
453-            # Budget gate (verbatim from v4).
454-            limit = self._config.session_cost_limit
455-            if limit > 0 and self.session_cost > 0:
456-                pct = self.session_cost / limit
457-                if pct >= 1.0 and not self._budget_stopped:
458-                    self._budget_stopped = True
459-                    logging.warning(
460-                        f"Session cost ${self.session_cost:.4f} reached limit ${limit:.2f}."
461-                    )
462-                elif pct >= 0.8 and not self._budget_warned:
463-                    self._budget_warned = True
464-                    logging.warning(
465-                        f"Session cost ${self.session_cost:.4f} is {pct:.0%} of ${limit:.2f} limit."
466-                    )
467-
468-    # --------------------------------------------------------
469-    # Read-only views (v4 verbatim)
470-    # --------------------------------------------------------
471-
472-    def is_over_budget(self) -> bool:
473-        limit = self._config.session_cost_limit
474-        return limit > 0 and self.session_cost >= limit
475-
476-    def get_last(self) -> str:
477-        return f"In:{self.last_input:,} Out:{self.last_output:,}"
478-
479-    def get_session(self) -> str:
480-        return (
481:            f"In:{self.session_input:,} Out:{self.session_output:,} "
482-            f"Total:{self.session_total:,}"
483-        )
484-
485-    def get_cache_savings_usd(self) -> float:
486-        mid = canonicalize_model_id(self._model_id or self._config.model_id)
487-        pricing = MODEL_COSTS.get(mid)
488-        if not pricing or self.session_cache_read == 0:
489-            return 0.0
490-        full_price_per_1k = pricing["input"]
491-        return (self.session_cache_read / 1000) * full_price_per_1k * 0.90
492-
493-    def get_cost(self) -> str:
494-        cost_str = (
495-            f"${self.session_cost:.4f}"
496-            if self.session_cost < 0.01
497-            else f"${self.session_cost:.2f}"
498-        )
499:        if self.session_cache_read > 0 and self.session_input > 0:
500:            cache_pct = min(100, (self.session_cache_read / self.session_input) * 100)
501-            savings = self.get_cache_savings_usd()
502-            cost_str += f" (cache {cache_pct:.0f}% | saved ~${savings:.4f})"
503-        return cost_str
504-
505-    def get_stats(self) -> Dict[str, Any]:
506-        return {
507:            "session_input": self.session_input,
508-            "session_output": self.session_output,
509-            "session_total": self.session_total,
510-            "session_cache_read": self.session_cache_read,
511-            "session_cache_write": self.session_cache_write,
512-            "last_input": self.last_input,
513-            "last_output": self.last_output,
514:            "api_calls": self.api_calls,
515-            "session_cost_usd": round(self.session_cost, 6),
516-            "last_cost_usd": round(self.last_cost, 6),
517:            "parent_input_tokens": self.parent_input_tokens,
518-            "parent_output_tokens": self.parent_output_tokens,
519-            "parent_cost_usd": round(self.parent_cost, 6),
520:            "subagent_input_tokens": dict(self.subagent_input_tokens),
521-            "subagent_output_tokens": dict(self.subagent_output_tokens),
522-            "subagent_cost_usd": {k: round(v, 6) for k, v in self.subagent_cost.items()},
523-        }
524-
525-    def restore(self, stats: Dict[str, Any]):
526-        """Restore counters from saved session metadata.
527-
528-        Used by Block B+ SessionManager `/resume` to rehydrate cost
529-        across sessions (Runnable cost-tracker.ts:87-175 / R11 N8).
530-        """
531-        with self._lock:
532:            self.session_input = int(stats.get("session_input", 0))
533-            self.session_output = int(stats.get("session_output", 0))
534:            self.session_total = self.session_input + self.session_output
535-            self.session_cache_read = int(stats.get("session_cache_read", 0))
536-            self.session_cache_write = int(stats.get("session_cache_write", 0))
537-            self.last_input = int(stats.get("last_input", 0))
538-            self.last_output = int(stats.get("last_output", 0))
539:            self.api_calls = int(stats.get("api_calls", 0))
540-            self.session_cost = float(stats.get("session_cost_usd", 0.0))
541-            self.last_cost = float(stats.get("last_cost_usd", 0.0))
542:            self.parent_input_tokens = int(stats.get("parent_input_tokens", 0))
543-            self.parent_output_tokens = int(stats.get("parent_output_tokens", 0))
544-            self.parent_cost = float(stats.get("parent_cost_usd", 0.0))
545:            self.subagent_input_tokens = dict(stats.get("subagent_input_tokens", {}))
546-            self.subagent_output_tokens = dict(stats.get("subagent_output_tokens", {}))
547-            self.subagent_cost = {
548-                k: float(v) for k, v in stats.get("subagent_cost_usd", {}).items()
549-            }
550-
551-    # --------------------------------------------------------
552-    # B-8 / B-9 — context-token math derived from last response
553-    # --------------------------------------------------------
554-
555-    def final_context_tokens_from_last_response(self) -> int:
556-        """Best-available estimate of the current context window size.
557-
558-        Per R8 #16: Bedrock returns top-level `usage` only (no per-block
559:        `cache_creation_input_tokens` breakdown). We use:
560-          context = last_input + cache_read + cache_write
561-        as a conservative upper bound for the next turn's prompt.
562-        """
563-        rec = self._last_usage_record
564-        if not rec:
565:            return self.session_input  # cold start fallback
566-        return (
567:            int(rec.get("input_tokens", 0))
568:            + int(rec.get("cache_read_input_tokens", 0))
569:            + int(rec.get("cache_creation_input_tokens", 0))
570-        )
571-
572-    def token_count_with_estimation(self, messages: List[Dict[str, Any]]) -> int:
573-        """Estimate token count for a message list.
574-
575-        Per R8 #15. Walks back to the last usage record; if it covers
576-        the same prefix-length as `messages`, reuse the recorded value
577-        (correct under prompt caching). Otherwise fall back to the
578-        block-level rough estimator.
579-        """
580-        if not messages:
581-            return 0
582-        if self._last_usage_record is not None:
583:            recorded = self._last_usage_record.get("input_tokens", 0)
584-            if recorded > 0:
585-                return int(recorded)
586-        return sum(rough_token_count_for_message(m) for m in messages)
587-
588-
589-# Module-level singleton (parity with v4 `TOKENS = TokenTracker()`).
590-TOKENS = TokenTracker()
591-
592-
593-# Block B+ (PORT_LOG #054): atexit cost-flush via cleanup_registry.
594-# Per Runnable costHook.ts:6-22 (R11 N14). On normal exit / SIGINT /
595-# SIGTERM, log the final session cost so operators can audit
596-# post-hoc even if the user closes the notebook abruptly.
597-def _flush_cost_on_exit() -> None:
598-    if TOKENS.session_cost > 0:
599-        logging.warning(
600-            f"session-final cost: {TOKENS.get_cost()} "
601:            f"({TOKENS.api_calls} API calls, "
602:            f"in={TOKENS.session_input:,} out={TOKENS.session_output:,})"
603-        )
604-
605-
606-try:  # pragma: no cover — registration-time best-effort
607-    from runtime.cleanup_registry import register as _register_cleanup
608-    _register_cleanup(_flush_cost_on_exit)
609-except Exception:
610-    pass
611-
612-
613-__all__ = [
614-    "ToolResult",
615-    "MODEL_COSTS",
616-    "EXCLUDED_MODELS_FOR_CACHE_BREAK",
617-    "IMAGE_MAX_TOKEN_SIZE",
618-    "TokenTracker",
619-    "TOKENS",
620-    "bytes_per_token_for_file_type",
621-    "estimate_message_tokens",
622-    "has_thinking_blocks",
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

 succeeded in 3104ms:
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:11:      one [CONVERSATION SUMMARY] system block, freeing tokens.
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:12:    - Turn 2: follow-up question. Bedrock must accept the post-compact
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:69:QUESTION: What is 2 + 3? Answer with a single number, no explanation.
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:88:      - Turn 2 is answered against the compacted buffer (recalls the
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:159:        # Turn 2 — follow-up against (likely-compacted) buffer.
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:170:        # [CONVERSATION SUMMARY] / "summary of prior" / "compact" marker
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:176:        summary_marker_seen = False
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:187:                "[CONVERSATION SUMMARY]",
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:192:                summary_marker_seen = True
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:196:        t2_input_estimate = tokens_in - tokens_in_t1
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:197:        t2_dropped_materially = t2_input_estimate < (tokens_in_t1 * 0.5)
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:198:        compact_proven = compact_log_seen or summary_marker_seen
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:199:        compact_likely = compact_proven and t2_dropped_materially
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:209:            "tokens_in_t2_estimate": int(t2_input_estimate),
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:210:            "t2_dropped_materially_vs_t1": bool(t2_dropped_materially),
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:220:            "summary_marker_seen": summary_marker_seen,
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:221:            "compact_proven": compact_proven,
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:247:        # Turn 2 — recall via compacted buffer.
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:253:        assert ("2 + 3" in t2_text or "2+3" in t2_text or "what is 2" in t2_text), (
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:260:        assert compact_proven, (
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:262:            f"stdout or [CONVERSATION SUMMARY] marker in agent.messages. "
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:264:            f"summary_marker={summary_marker_seen}. metrics={metrics}"
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:266:        assert t2_dropped_materially, (
compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py:269:            f"{t2_input_estimate}. metrics={metrics}"
compact_v5/MAIN/agent/core/compactor.py:502:                f"[CONVERSATION SUMMARY]\n{summary}\n"
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

codex
The summary marker format is direct: `Compactor.compact()` writes a user-role message starting with `[CONVERSATION SUMMARY]`, then `[END SUMMARY ...]`. The test comment says “system block,” but the executable marker assertion matches the actual user-message format.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n -C 25 "cache_read_input_tokens|cache_creation_input_tokens|input_tokens|usage" compact_v5/MAIN/agent/runtime/bedrock_client.py compact_v5/MAIN/agent/runtime/*.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n -C 8 \"summary_msg|\\[CONVERSATION SUMMARY\\]|\\[END SUMMARY\" compact_v5/MAIN/agent/core/compactor.py" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n -C 8 "result_t1|tokens_in_t1|result_t2|t2_input_estimate|t2_dropped_materially" compact_v5/MAIN/agent/tests/r_tier/test_r2_compact.py' in D:\Github\sagemaker-coding-agent
 succeeded in 2905ms:
491-        messages: List[Dict[str, Any]],
492-        summary: str,
493-    ) -> List[Dict[str, Any]]:
494-        """Replace old messages with a summary + last N messages."""
495-        if not summary:
496-            return messages
497-        keep_last = cls.KEEP_LAST_MESSAGES
498-        recent = messages[-keep_last:] if len(messages) > keep_last else []
499:        summary_msg = {
500-            "role": "user",
501-            "content": (
502:                f"[CONVERSATION SUMMARY]\n{summary}\n"
503:                "[END SUMMARY — Continuing from here]"
504-            ),
505-        }
506:        return [summary_msg] + recent
507-
508-    @classmethod
509-    def run(
510-        cls,
511-        client: Any,
512-        messages: List[Dict[str, Any]],
513-        max_tokens: int = 200_000,
514-    ) -> CompactionResult:
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

2026-05-03T23:32:05.340047Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 2.9 seconds
Output:
compact_v5/MAIN/agent/runtime/bedrock_client.py-32-
compact_v5/MAIN/agent/runtime/bedrock_client.py-33-# botocore.config import is local-deferred so unit tests with mock_mode=True
compact_v5/MAIN/agent/runtime/bedrock_client.py-34-# can import this module without boto3 installed. Real flows will import on demand.
compact_v5/MAIN/agent/runtime/bedrock_client.py-35-
compact_v5/MAIN/agent/runtime/bedrock_client.py-36-# CONFIG is imported lazily within methods to avoid circular import during Phase 1.
compact_v5/MAIN/agent/runtime/bedrock_client.py-37-
compact_v5/MAIN/agent/runtime/bedrock_client.py-38-
compact_v5/MAIN/agent/runtime/bedrock_client.py-39-# ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-40-# Response / ToolCall (lightweight value types — verbatim from v4)
compact_v5/MAIN/agent/runtime/bedrock_client.py-41-# ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-42-
compact_v5/MAIN/agent/runtime/bedrock_client.py-43-@dataclass
compact_v5/MAIN/agent/runtime/bedrock_client.py-44-class ToolCall:
compact_v5/MAIN/agent/runtime/bedrock_client.py-45-    """A tool invocation request from the model."""
compact_v5/MAIN/agent/runtime/bedrock_client.py-46-    id: str
compact_v5/MAIN/agent/runtime/bedrock_client.py-47-    name: str
compact_v5/MAIN/agent/runtime/bedrock_client.py-48-    input: Dict[str, Any] = field(default_factory=dict)
compact_v5/MAIN/agent/runtime/bedrock_client.py-49-
compact_v5/MAIN/agent/runtime/bedrock_client.py-50-
compact_v5/MAIN/agent/runtime/bedrock_client.py-51-@dataclass
compact_v5/MAIN/agent/runtime/bedrock_client.py-52-class Response:
compact_v5/MAIN/agent/runtime/bedrock_client.py-53-    """Parsed Bedrock response."""
compact_v5/MAIN/agent/runtime/bedrock_client.py-54-    text: str
compact_v5/MAIN/agent/runtime/bedrock_client.py-55-    tool_calls: List[ToolCall] = field(default_factory=list)
compact_v5/MAIN/agent/runtime/bedrock_client.py-56-    stop_reason: str = ""
compact_v5/MAIN/agent/runtime/bedrock_client.py:57:    usage: Dict[str, Any] = field(default_factory=dict)
compact_v5/MAIN/agent/runtime/bedrock_client.py-58-    thinking: str = ""
compact_v5/MAIN/agent/runtime/bedrock_client.py-59-
compact_v5/MAIN/agent/runtime/bedrock_client.py-60-
compact_v5/MAIN/agent/runtime/bedrock_client.py-61-# ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-62-# Error categories + classifier + retry policy
compact_v5/MAIN/agent/runtime/bedrock_client.py-63-# Phase 8: extracted to core/errors.py + core/retry.py (ADR-014).
compact_v5/MAIN/agent/runtime/bedrock_client.py-64-# Re-imported here so existing call-sites (and tests) continue to work
compact_v5/MAIN/agent/runtime/bedrock_client.py-65-# byte-equivalent with Phase 1.
compact_v5/MAIN/agent/runtime/bedrock_client.py-66-# ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-67-
compact_v5/MAIN/agent/runtime/bedrock_client.py-68-from core.errors import BedrockErrorCategory, ErrorClassifier  # noqa: F401
compact_v5/MAIN/agent/runtime/bedrock_client.py-69-from core.retry import RetryPolicy  # noqa: F401
compact_v5/MAIN/agent/runtime/bedrock_client.py-70-
compact_v5/MAIN/agent/runtime/bedrock_client.py-71-
compact_v5/MAIN/agent/runtime/bedrock_client.py-72-# ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-73-# BEDROCK_EXTRA_PARAMS_HEADERS (Block 0 item 0-3 → Block B per ADR-020)
compact_v5/MAIN/agent/runtime/bedrock_client.py-74-# ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-75-#
compact_v5/MAIN/agent/runtime/bedrock_client.py-76-# Anthropic-API-direct features (interleaved-thinking beta, 1m-context
compact_v5/MAIN/agent/runtime/bedrock_client.py-77-# beta) ride on `anthropic-beta` HTTP headers. Bedrock does NOT accept
compact_v5/MAIN/agent/runtime/bedrock_client.py-78-# those headers; the equivalent goes in `additionalModelRequestFields`
compact_v5/MAIN/agent/runtime/bedrock_client.py-79-# in the request body. This Set documents which beta names we know need
compact_v5/MAIN/agent/runtime/bedrock_client.py-80-# the body-not-header treatment, so any future code that wants to opt
compact_v5/MAIN/agent/runtime/bedrock_client.py-81-# in to a beta has a single source of truth and can't accidentally pass
compact_v5/MAIN/agent/runtime/bedrock_client.py-82-# them as headers (which Bedrock would silently drop).
--
compact_v5/MAIN/agent/runtime/bedrock_client.py-159-    # ---------- mock-mode helpers ----------
compact_v5/MAIN/agent/runtime/bedrock_client.py-160-
compact_v5/MAIN/agent/runtime/bedrock_client.py-161-    def _mock_response(self, messages, tools) -> Response:
compact_v5/MAIN/agent/runtime/bedrock_client.py-162-        """Generate mock response for testing (v4 verbatim, simplified)."""
compact_v5/MAIN/agent/runtime/bedrock_client.py-163-        last = messages[-1]["content"] if messages else ""
compact_v5/MAIN/agent/runtime/bedrock_client.py-164-        if isinstance(last, str):
compact_v5/MAIN/agent/runtime/bedrock_client.py-165-            low = last.lower()
compact_v5/MAIN/agent/runtime/bedrock_client.py-166-            if "list" in low and ("file" in low or "dir" in low):
compact_v5/MAIN/agent/runtime/bedrock_client.py-167-                return Response(
compact_v5/MAIN/agent/runtime/bedrock_client.py-168-                    "I'll list the files.",
compact_v5/MAIN/agent/runtime/bedrock_client.py-169-                    [ToolCall("m1", "list_dir", {"path": "."})],
compact_v5/MAIN/agent/runtime/bedrock_client.py-170-                    "tool_use",
compact_v5/MAIN/agent/runtime/bedrock_client.py-171-                    {},
compact_v5/MAIN/agent/runtime/bedrock_client.py-172-                )
compact_v5/MAIN/agent/runtime/bedrock_client.py-173-            if "read" in low:
compact_v5/MAIN/agent/runtime/bedrock_client.py-174-                return Response(
compact_v5/MAIN/agent/runtime/bedrock_client.py-175-                    "I'll read that file.",
compact_v5/MAIN/agent/runtime/bedrock_client.py-176-                    [ToolCall("m2", "read_file", {"file_path": "README.md"})],
compact_v5/MAIN/agent/runtime/bedrock_client.py-177-                    "tool_use",
compact_v5/MAIN/agent/runtime/bedrock_client.py-178-                    {},
compact_v5/MAIN/agent/runtime/bedrock_client.py-179-                )
compact_v5/MAIN/agent/runtime/bedrock_client.py-180-        return Response(
compact_v5/MAIN/agent/runtime/bedrock_client.py-181-            f"[MOCK] Received: {str(last)[:100]}...",
compact_v5/MAIN/agent/runtime/bedrock_client.py-182-            [],
compact_v5/MAIN/agent/runtime/bedrock_client.py-183-            "end_turn",
compact_v5/MAIN/agent/runtime/bedrock_client.py:184:            {"input_tokens": 100, "output_tokens": 50},
compact_v5/MAIN/agent/runtime/bedrock_client.py-185-        )
compact_v5/MAIN/agent/runtime/bedrock_client.py-186-
compact_v5/MAIN/agent/runtime/bedrock_client.py-187-    # ---------- main chat entry ----------
compact_v5/MAIN/agent/runtime/bedrock_client.py-188-
compact_v5/MAIN/agent/runtime/bedrock_client.py-189-    def chat(
compact_v5/MAIN/agent/runtime/bedrock_client.py-190-        self,
compact_v5/MAIN/agent/runtime/bedrock_client.py-191-        messages: List[Dict],
compact_v5/MAIN/agent/runtime/bedrock_client.py-192-        system: Any,  # str OR list-of-blocks (with cache_control)
compact_v5/MAIN/agent/runtime/bedrock_client.py-193-        tools: Optional[List[Dict]] = None,
compact_v5/MAIN/agent/runtime/bedrock_client.py-194-        max_tokens: int = 4096,
compact_v5/MAIN/agent/runtime/bedrock_client.py-195-        temperature: float = 0.0,
compact_v5/MAIN/agent/runtime/bedrock_client.py-196-        thinking_enabled: bool = False,
compact_v5/MAIN/agent/runtime/bedrock_client.py-197-        thinking_budget: int = 4096,
compact_v5/MAIN/agent/runtime/bedrock_client.py-198-    ) -> Response:
compact_v5/MAIN/agent/runtime/bedrock_client.py-199-        """Send chat request to Bedrock.
compact_v5/MAIN/agent/runtime/bedrock_client.py-200-
compact_v5/MAIN/agent/runtime/bedrock_client.py-201-        Args:
compact_v5/MAIN/agent/runtime/bedrock_client.py-202-            messages: Conversation messages
compact_v5/MAIN/agent/runtime/bedrock_client.py-203-            system: System prompt (str or pre-formatted multi-block list with cache_control)
compact_v5/MAIN/agent/runtime/bedrock_client.py-204-            tools: Tool definitions
compact_v5/MAIN/agent/runtime/bedrock_client.py-205-            max_tokens: Maximum response tokens
compact_v5/MAIN/agent/runtime/bedrock_client.py-206-            temperature: Sampling temperature (0.0-1.0)
compact_v5/MAIN/agent/runtime/bedrock_client.py-207-            thinking_enabled: Enable extended thinking mode
compact_v5/MAIN/agent/runtime/bedrock_client.py-208-            thinking_budget: Max tokens for thinking (1024-16000)
compact_v5/MAIN/agent/runtime/bedrock_client.py-209-        """
--
compact_v5/MAIN/agent/runtime/bedrock_client.py-342-    # ---------- response parsing ----------
compact_v5/MAIN/agent/runtime/bedrock_client.py-343-
compact_v5/MAIN/agent/runtime/bedrock_client.py-344-    def _parse(self, result: dict) -> Response:
compact_v5/MAIN/agent/runtime/bedrock_client.py-345-        """Parse Bedrock response into Response value type (v4 verbatim)."""
compact_v5/MAIN/agent/runtime/bedrock_client.py-346-        text = ""
compact_v5/MAIN/agent/runtime/bedrock_client.py-347-        thinking = ""
compact_v5/MAIN/agent/runtime/bedrock_client.py-348-        tool_calls: List[ToolCall] = []
compact_v5/MAIN/agent/runtime/bedrock_client.py-349-        for block in result.get("content", []):
compact_v5/MAIN/agent/runtime/bedrock_client.py-350-            block_type = block.get("type")
compact_v5/MAIN/agent/runtime/bedrock_client.py-351-            if block_type == "text":
compact_v5/MAIN/agent/runtime/bedrock_client.py-352-                text += block.get("text", "")
compact_v5/MAIN/agent/runtime/bedrock_client.py-353-            elif block_type == "thinking":
compact_v5/MAIN/agent/runtime/bedrock_client.py-354-                thinking += block.get("thinking", "")
compact_v5/MAIN/agent/runtime/bedrock_client.py-355-            elif block_type == "tool_use":
compact_v5/MAIN/agent/runtime/bedrock_client.py-356-                tool_calls.append(
compact_v5/MAIN/agent/runtime/bedrock_client.py-357-                    ToolCall(
compact_v5/MAIN/agent/runtime/bedrock_client.py-358-                        id=block.get("id", ""),
compact_v5/MAIN/agent/runtime/bedrock_client.py-359-                        name=block.get("name", ""),
compact_v5/MAIN/agent/runtime/bedrock_client.py-360-                        input=block.get("input", {}),
compact_v5/MAIN/agent/runtime/bedrock_client.py-361-                    )
compact_v5/MAIN/agent/runtime/bedrock_client.py-362-                )
compact_v5/MAIN/agent/runtime/bedrock_client.py-363-        return Response(
compact_v5/MAIN/agent/runtime/bedrock_client.py-364-            text=text,
compact_v5/MAIN/agent/runtime/bedrock_client.py-365-            tool_calls=tool_calls,
compact_v5/MAIN/agent/runtime/bedrock_client.py-366-            stop_reason=result.get("stop_reason", ""),
compact_v5/MAIN/agent/runtime/bedrock_client.py:367:            usage=result.get("usage", {}),
compact_v5/MAIN/agent/runtime/bedrock_client.py-368-            thinking=thinking,
compact_v5/MAIN/agent/runtime/bedrock_client.py-369-        )
compact_v5/MAIN/agent/runtime/bedrock_client.py-370-
compact_v5/MAIN/agent/runtime/bedrock_client.py-371-    # ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-372-    # B-1 — countTokensWithBedrock (R4 #41, MUST)
compact_v5/MAIN/agent/runtime/bedrock_client.py-373-    # ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-374-
compact_v5/MAIN/agent/runtime/bedrock_client.py-375-    def count_tokens(
compact_v5/MAIN/agent/runtime/bedrock_client.py-376-        self,
compact_v5/MAIN/agent/runtime/bedrock_client.py-377-        messages: List[Dict[str, Any]],
compact_v5/MAIN/agent/runtime/bedrock_client.py-378-        system: Optional[str] = None,
compact_v5/MAIN/agent/runtime/bedrock_client.py-379-        tools: Optional[List[Dict[str, Any]]] = None,
compact_v5/MAIN/agent/runtime/bedrock_client.py-380-        model_id: Optional[str] = None,
compact_v5/MAIN/agent/runtime/bedrock_client.py-381-    ) -> Optional[int]:
compact_v5/MAIN/agent/runtime/bedrock_client.py-382-        """Real Bedrock token count via the bedrock-runtime CountTokens API.
compact_v5/MAIN/agent/runtime/bedrock_client.py-383-
compact_v5/MAIN/agent/runtime/bedrock_client.py-384-        Returns the token count as int, or None on failure / mock mode.
compact_v5/MAIN/agent/runtime/bedrock_client.py-385-        Per Runnable services/tokenEstimation.ts:437-495 (R4 #41 MUST):
compact_v5/MAIN/agent/runtime/bedrock_client.py-386-        without this, v5 has no real Bedrock token count and the
compact_v5/MAIN/agent/runtime/bedrock_client.py-387-        Compactor (Block A) cannot make safe context-budget decisions.
compact_v5/MAIN/agent/runtime/bedrock_client.py-388-
compact_v5/MAIN/agent/runtime/bedrock_client.py-389-        Falls through to None when:
compact_v5/MAIN/agent/runtime/bedrock_client.py-390-          - mock_mode is True (no Bedrock contact)
compact_v5/MAIN/agent/runtime/bedrock_client.py-391-          - the bedrock-runtime client doesn't expose count_tokens
compact_v5/MAIN/agent/runtime/bedrock_client.py-392-            (older boto3 versions; retry by upgrading boto3 ≥ 1.35)
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 
rg: compact_v5/MAIN/agent/runtime/*.py: The filename, directory name, or volume label syntax is incorrect. (os error 123)

 exited 1 in 2944ms:
compact_v5/MAIN/agent/runtime/bedrock_client.py-32-
compact_v5/MAIN/agent/runtime/bedrock_client.py-33-# botocore.config import is local-deferred so unit tests with mock_mode=True
compact_v5/MAIN/agent/runtime/bedrock_client.py-34-# can import this module without boto3 installed. Real flows will import on demand.
compact_v5/MAIN/agent/runtime/bedrock_client.py-35-
compact_v5/MAIN/agent/runtime/bedrock_client.py-36-# CONFIG is imported lazily within methods to avoid circular import during Phase 1.
compact_v5/MAIN/agent/runtime/bedrock_client.py-37-
compact_v5/MAIN/agent/runtime/bedrock_client.py-38-
compact_v5/MAIN/agent/runtime/bedrock_client.py-39-# ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-40-# Response / ToolCall (lightweight value types — verbatim from v4)
compact_v5/MAIN/agent/runtime/bedrock_client.py-41-# ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-42-
compact_v5/MAIN/agent/runtime/bedrock_client.py-43-@dataclass
compact_v5/MAIN/agent/runtime/bedrock_client.py-44-class ToolCall:
compact_v5/MAIN/agent/runtime/bedrock_client.py-45-    """A tool invocation request from the model."""
compact_v5/MAIN/agent/runtime/bedrock_client.py-46-    id: str
compact_v5/MAIN/agent/runtime/bedrock_client.py-47-    name: str
compact_v5/MAIN/agent/runtime/bedrock_client.py-48-    input: Dict[str, Any] = field(default_factory=dict)
compact_v5/MAIN/agent/runtime/bedrock_client.py-49-
compact_v5/MAIN/agent/runtime/bedrock_client.py-50-
compact_v5/MAIN/agent/runtime/bedrock_client.py-51-@dataclass
compact_v5/MAIN/agent/runtime/bedrock_client.py-52-class Response:
compact_v5/MAIN/agent/runtime/bedrock_client.py-53-    """Parsed Bedrock response."""
compact_v5/MAIN/agent/runtime/bedrock_client.py-54-    text: str
compact_v5/MAIN/agent/runtime/bedrock_client.py-55-    tool_calls: List[ToolCall] = field(default_factory=list)
compact_v5/MAIN/agent/runtime/bedrock_client.py-56-    stop_reason: str = ""
compact_v5/MAIN/agent/runtime/bedrock_client.py:57:    usage: Dict[str, Any] = field(default_factory=dict)
compact_v5/MAIN/agent/runtime/bedrock_client.py-58-    thinking: str = ""
compact_v5/MAIN/agent/runtime/bedrock_client.py-59-
compact_v5/MAIN/agent/runtime/bedrock_client.py-60-
compact_v5/MAIN/agent/runtime/bedrock_client.py-61-# ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-62-# Error categories + classifier + retry policy
compact_v5/MAIN/agent/runtime/bedrock_client.py-63-# Phase 8: extracted to core/errors.py + core/retry.py (ADR-014).
compact_v5/MAIN/agent/runtime/bedrock_client.py-64-# Re-imported here so existing call-sites (and tests) continue to work
compact_v5/MAIN/agent/runtime/bedrock_client.py-65-# byte-equivalent with Phase 1.
compact_v5/MAIN/agent/runtime/bedrock_client.py-66-# ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-67-
compact_v5/MAIN/agent/runtime/bedrock_client.py-68-from core.errors import BedrockErrorCategory, ErrorClassifier  # noqa: F401
compact_v5/MAIN/agent/runtime/bedrock_client.py-69-from core.retry import RetryPolicy  # noqa: F401
compact_v5/MAIN/agent/runtime/bedrock_client.py-70-
compact_v5/MAIN/agent/runtime/bedrock_client.py-71-
compact_v5/MAIN/agent/runtime/bedrock_client.py-72-# ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-73-# BEDROCK_EXTRA_PARAMS_HEADERS (Block 0 item 0-3 → Block B per ADR-020)
compact_v5/MAIN/agent/runtime/bedrock_client.py-74-# ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-75-#
compact_v5/MAIN/agent/runtime/bedrock_client.py-76-# Anthropic-API-direct features (interleaved-thinking beta, 1m-context
compact_v5/MAIN/agent/runtime/bedrock_client.py-77-# beta) ride on `anthropic-beta` HTTP headers. Bedrock does NOT accept
compact_v5/MAIN/agent/runtime/bedrock_client.py-78-# those headers; the equivalent goes in `additionalModelRequestFields`
compact_v5/MAIN/agent/runtime/bedrock_client.py-79-# in the request body. This Set documents which beta names we know need
compact_v5/MAIN/agent/runtime/bedrock_client.py-80-# the body-not-header treatment, so any future code that wants to opt
compact_v5/MAIN/agent/runtime/bedrock_client.py-81-# in to a beta has a single source of truth and can't accidentally pass
compact_v5/MAIN/agent/runtime/bedrock_client.py-82-# them as headers (which Bedrock would silently drop).
--
compact_v5/MAIN/agent/runtime/bedrock_client.py-159-    # ---------- mock-mode helpers ----------
compact_v5/MAIN/agent/runtime/bedrock_client.py-160-
compact_v5/MAIN/agent/runtime/bedrock_client.py-161-    def _mock_response(self, messages, tools) -> Response:
compact_v5/MAIN/agent/runtime/bedrock_client.py-162-        """Generate mock response for testing (v4 verbatim, simplified)."""
compact_v5/MAIN/agent/runtime/bedrock_client.py-163-        last = messages[-1]["content"] if messages else ""
compact_v5/MAIN/agent/runtime/bedrock_client.py-164-        if isinstance(last, str):
compact_v5/MAIN/agent/runtime/bedrock_client.py-165-            low = last.lower()
compact_v5/MAIN/agent/runtime/bedrock_client.py-166-            if "list" in low and ("file" in low or "dir" in low):
compact_v5/MAIN/agent/runtime/bedrock_client.py-167-                return Response(
compact_v5/MAIN/agent/runtime/bedrock_client.py-168-                    "I'll list the files.",
compact_v5/MAIN/agent/runtime/bedrock_client.py-169-                    [ToolCall("m1", "list_dir", {"path": "."})],
compact_v5/MAIN/agent/runtime/bedrock_client.py-170-                    "tool_use",
compact_v5/MAIN/agent/runtime/bedrock_client.py-171-                    {},
compact_v5/MAIN/agent/runtime/bedrock_client.py-172-                )
compact_v5/MAIN/agent/runtime/bedrock_client.py-173-            if "read" in low:
compact_v5/MAIN/agent/runtime/bedrock_client.py-174-                return Response(
compact_v5/MAIN/agent/runtime/bedrock_client.py-175-                    "I'll read that file.",
compact_v5/MAIN/agent/runtime/bedrock_client.py-176-                    [ToolCall("m2", "read_file", {"file_path": "README.md"})],
compact_v5/MAIN/agent/runtime/bedrock_client.py-177-                    "tool_use",
compact_v5/MAIN/agent/runtime/bedrock_client.py-178-                    {},
compact_v5/MAIN/agent/runtime/bedrock_client.py-179-                )
compact_v5/MAIN/agent/runtime/bedrock_client.py-180-        return Response(
compact_v5/MAIN/agent/runtime/bedrock_client.py-181-            f"[MOCK] Received: {str(last)[:100]}...",
compact_v5/MAIN/agent/runtime/bedrock_client.py-182-            [],
compact_v5/MAIN/agent/runtime/bedrock_client.py-183-            "end_turn",
compact_v5/MAIN/agent/runtime/bedrock_client.py:184:            {"input_tokens": 100, "output_tokens": 50},
compact_v5/MAIN/agent/runtime/bedrock_client.py-185-        )
compact_v5/MAIN/agent/runtime/bedrock_client.py-186-
compact_v5/MAIN/agent/runtime/bedrock_client.py-187-    # ---------- main chat entry ----------
compact_v5/MAIN/agent/runtime/bedrock_client.py-188-
compact_v5/MAIN/agent/runtime/bedrock_client.py-189-    def chat(
compact_v5/MAIN/agent/runtime/bedrock_client.py-190-        self,
compact_v5/MAIN/agent/runtime/bedrock_client.py-191-        messages: List[Dict],
compact_v5/MAIN/agent/runtime/bedrock_client.py-192-        system: Any,  # str OR list-of-blocks (with cache_control)
compact_v5/MAIN/agent/runtime/bedrock_client.py-193-        tools: Optional[List[Dict]] = None,
compact_v5/MAIN/agent/runtime/bedrock_client.py-194-        max_tokens: int = 4096,
compact_v5/MAIN/agent/runtime/bedrock_client.py-195-        temperature: float = 0.0,
compact_v5/MAIN/agent/runtime/bedrock_client.py-196-        thinking_enabled: bool = False,
compact_v5/MAIN/agent/runtime/bedrock_client.py-197-        thinking_budget: int = 4096,
compact_v5/MAIN/agent/runtime/bedrock_client.py-198-    ) -> Response:
compact_v5/MAIN/agent/runtime/bedrock_client.py-199-        """Send chat request to Bedrock.
compact_v5/MAIN/agent/runtime/bedrock_client.py-200-
compact_v5/MAIN/agent/runtime/bedrock_client.py-201-        Args:
compact_v5/MAIN/agent/runtime/bedrock_client.py-202-            messages: Conversation messages
compact_v5/MAIN/agent/runtime/bedrock_client.py-203-            system: System prompt (str or pre-formatted multi-block list with cache_control)
compact_v5/MAIN/agent/runtime/bedrock_client.py-204-            tools: Tool definitions
compact_v5/MAIN/agent/runtime/bedrock_client.py-205-            max_tokens: Maximum response tokens
compact_v5/MAIN/agent/runtime/bedrock_client.py-206-            temperature: Sampling temperature (0.0-1.0)
compact_v5/MAIN/agent/runtime/bedrock_client.py-207-            thinking_enabled: Enable extended thinking mode
compact_v5/MAIN/agent/runtime/bedrock_client.py-208-            thinking_budget: Max tokens for thinking (1024-16000)
compact_v5/MAIN/agent/runtime/bedrock_client.py-209-        """
--
compact_v5/MAIN/agent/runtime/bedrock_client.py-342-    # ---------- response parsing ----------
compact_v5/MAIN/agent/runtime/bedrock_client.py-343-
compact_v5/MAIN/agent/runtime/bedrock_client.py-344-    def _parse(self, result: dict) -> Response:
compact_v5/MAIN/agent/runtime/bedrock_client.py-345-        """Parse Bedrock response into Response value type (v4 verbatim)."""
compact_v5/MAIN/agent/runtime/bedrock_client.py-346-        text = ""
compact_v5/MAIN/agent/runtime/bedrock_client.py-347-        thinking = ""
compact_v5/MAIN/agent/runtime/bedrock_client.py-348-        tool_calls: List[ToolCall] = []
compact_v5/MAIN/agent/runtime/bedrock_client.py-349-        for block in result.get("content", []):
compact_v5/MAIN/agent/runtime/bedrock_client.py-350-            block_type = block.get("type")
compact_v5/MAIN/agent/runtime/bedrock_client.py-351-            if block_type == "text":
compact_v5/MAIN/agent/runtime/bedrock_client.py-352-                text += block.get("text", "")
compact_v5/MAIN/agent/runtime/bedrock_client.py-353-            elif block_type == "thinking":
compact_v5/MAIN/agent/runtime/bedrock_client.py-354-                thinking += block.get("thinking", "")
compact_v5/MAIN/agent/runtime/bedrock_client.py-355-            elif block_type == "tool_use":
compact_v5/MAIN/agent/runtime/bedrock_client.py-356-                tool_calls.append(
compact_v5/MAIN/agent/runtime/bedrock_client.py-357-                    ToolCall(
compact_v5/MAIN/agent/runtime/bedrock_client.py-358-                        id=block.get("id", ""),
compact_v5/MAIN/agent/runtime/bedrock_client.py-359-                        name=block.get("name", ""),
compact_v5/MAIN/agent/runtime/bedrock_client.py-360-                        input=block.get("input", {}),
compact_v5/MAIN/agent/runtime/bedrock_client.py-361-                    )
compact_v5/MAIN/agent/runtime/bedrock_client.py-362-                )
compact_v5/MAIN/agent/runtime/bedrock_client.py-363-        return Response(
compact_v5/MAIN/agent/runtime/bedrock_client.py-364-            text=text,
compact_v5/MAIN/agent/runtime/bedrock_client.py-365-            tool_calls=tool_calls,
compact_v5/MAIN/agent/runtime/bedrock_client.py-366-            stop_reason=result.get("stop_reason", ""),
compact_v5/MAIN/agent/runtime/bedrock_client.py:367:            usage=result.get("usage", {}),
compact_v5/MAIN/agent/runtime/bedrock_client.py-368-            thinking=thinking,
compact_v5/MAIN/agent/runtime/bedrock_client.py-369-        )
compact_v5/MAIN/agent/runtime/bedrock_client.py-370-
compact_v5/MAIN/agent/runtime/bedrock_client.py-371-    # ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-372-    # B-1 — countTokensWithBedrock (R4 #41, MUST)
compact_v5/MAIN/agent/runtime/bedrock_client.py-373-    # ============================================================
compact_v5/MAIN/agent/runtime/bedrock_client.py-374-
compact_v5/MAIN/agent/runtime/bedrock_client.py-375-    def count_tokens(
compact_v5/MAIN/agent/runtime/bedrock_client.py-376-        self,
compact_v5/MAIN/agent/runtime/bedrock_client.py-377-        messages: List[Dict[str, Any]],
compact_v5/MAIN/agent/runtime/bedrock_client.py-378-        system: Optional[str] = None,
compact_v5/MAIN/agent/runtime/bedrock_client.py-379-        tools: Optional[List[Dict[str, Any]]] = None,
compact_v5/MAIN/agent/runtime/bedrock_client.py-380-        model_id: Optional[str] = None,
compact_v5/MAIN/agent/runtime/bedrock_client.py-381-    ) -> Optional[int]:
compact_v5/MAIN/agent/runtime/bedrock_client.py-382-        """Real Bedrock token count via the bedrock-runtime CountTokens API.
compact_v5/MAIN/agent/runtime/bedrock_client.py-383-
compact_v5/MAIN/agent/runtime/bedrock_client.py-384-        Returns the token count as int, or None on failure / mock mode.
compact_v5/MAIN/agent/runtime/bedrock_client.py-385-        Per Runnable services/tokenEstimation.ts:437-495 (R4 #41 MUST):
compact_v5/MAIN/agent/runtime/bedrock_client.py-386-        without this, v5 has no real Bedrock token count and the
compact_v5/MAIN/agent/runtime/bedrock_client.py-387-        Compactor (Block A) cannot make safe context-budget decisions.
compact_v5/MAIN/agent/runtime/bedrock_client.py-388-
compact_v5/MAIN/agent/runtime/bedrock_client.py-389-        Falls through to None when:
compact_v5/MAIN/agent/runtime/bedrock_client.py-390-          - mock_mode is True (no Bedrock contact)
compact_v5/MAIN/agent/runtime/bedrock_client.py-391-          - the bedrock-runtime client doesn't expose count_tokens
compact_v5/MAIN/agent/runtime/bedrock_client.py-392-            (older boto3 versions; retry by upgrading boto3 ≥ 1.35)
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 
rg: compact_v5/MAIN/agent/runtime/*.py: The filename, directory name, or volume label syntax is incorrect. (os error 123)

 succeeded in 3277ms:
147-        )
148-
149-        recap = (_LOREM_LINE + "\n") * _LOREM_LINES
150-        prompt_t1 = _R2_PROMPT_T1.format(recap=recap)
151-        approx_tokens_in = len(prompt_t1) // 4
152-
153-        t0 = time.time()
154-        # Turn 1 — large preamble.
155:        result_t1 = agent.run(prompt_t1, tools=[], output_fn=_stdout_capture)
156-        wall_t1 = time.time() - t0
157:        tokens_in_t1 = TOKENS.session_input
158-        api_calls_after_t1 = TOKENS.api_calls
159-        # Turn 2 — follow-up against (likely-compacted) buffer.
160-        t1 = time.time()
161:        result_t2 = agent.run(_R2_PROMPT_T2, tools=[], output_fn=_stdout_capture)
162-        wall_t2 = time.time() - t1
163-        cost_used = TOKENS.session_cost
164-        tokens_in = TOKENS.session_input
165-        tokens_out = TOKENS.session_output
166-        api_calls = TOKENS.api_calls
167-
168-        # Detect compaction — STRONG signals only (Codex iter-2 fix):
169-        # MUST have explicit "[auto-compact]" log line OR find a
--
188-                "[Conversation Summary]",
189-                "## Summary of prior conversation",
190-                "summary of the prior",
191-            )):
192-                summary_marker_seen = True
193-                break
194-        # T2 input MUST drop materially vs T1 input — proof that
195-        # turn 2 sent a smaller (compacted) buffer to Bedrock.
196:        t2_input_estimate = tokens_in - tokens_in_t1
197:        t2_dropped_materially = t2_input_estimate < (tokens_in_t1 * 0.5)
198-        compact_proven = compact_log_seen or summary_marker_seen
199:        compact_likely = compact_proven and t2_dropped_materially
200-
201-        metrics = {
202-            "test": "R2",
203-            "call": 1,
204-            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
205-            "model": _HAIKU_45_AU,
206-            "tokens_in": int(tokens_in),
207-            "tokens_out": int(tokens_out),
208:            "tokens_in_after_turn1": int(tokens_in_t1),
209:            "tokens_in_t2_estimate": int(t2_input_estimate),
210:            "t2_dropped_materially_vs_t1": bool(t2_dropped_materially),
211-            "wallclock_s": round(wall_t1 + wall_t2, 2),
212-            "wallclock_t1_s": round(wall_t1, 2),
213-            "wallclock_t2_s": round(wall_t2, 2),
214-            "approx_prompt_tokens": approx_tokens_in,
215-            "preamble_lines": _LOREM_LINES,
216-            "context_max_tokens_test_override": CONFIG.context_max_tokens,
217-            "api_calls": int(api_calls),
218-            "api_calls_after_t1": int(api_calls_after_t1),
219-            "compact_log_seen": compact_log_seen,
220-            "summary_marker_seen": summary_marker_seen,
221-            "compact_proven": compact_proven,
222-            "compact_likely": compact_likely,
223:            "tool_calls_t1": int(getattr(result_t1, "turns_used", 0)),
224:            "tool_calls_t2": int(getattr(result_t2, "turns_used", 0)),
225-            "cost_usd": round(cost_used, 4),
226:            "stop_reason_t1": result_t1.stop_reason,
227:            "stop_reason_t2": result_t2.stop_reason,
228:            "final_text_t1": (result_t1.text or "").strip()[:200],
229:            "final_text_t2": (result_t2.text or "").strip()[:200],
230-        }
231-        (tmp_path / "_r2_metrics.json").write_text(
232-            json.dumps(metrics, indent=2), encoding="utf-8"
233-        )
234-        print(f"\n[R2 METRICS] {json.dumps(metrics)}")
235-
236-        # Codex iter-1 fix #2: tight regex on turn-1 answer.
237:        t1_text = (result_t1.text or "").strip()
238-        # Accept "5", "5.", "Five", "Five.", "= 5", with optional
239-        # leading "=" or whitespace.
240-        assert re.match(r"^\s*=?\s*(5|five)\b\.?\s*$", t1_text, re.IGNORECASE), (
241-            f"R2 turn 1 expected exact answer 5/five; got: {t1_text!r}. "
242-            f"metrics={metrics}"
243-        )
244:        assert result_t1.stop_reason != "max_turns", (
245-            f"R2 turn 1 hit max_turns. metrics={metrics}"
246-        )
247-        # Turn 2 — recall via compacted buffer.
248-        # Codex iter-2 fix: removed "5" from accepted recall — that
249-        # could pass from a weak summary that lost the actual question.
250-        # Must mention the original prompt's specific arithmetic.
251:        t2_text = (result_t2.text or "").lower()
252-        assert t2_text, f"R2 turn 2 empty response. metrics={metrics}"
253-        assert ("2 + 3" in t2_text or "2+3" in t2_text or "what is 2" in t2_text), (
254-            f"R2 turn 2 didn't recall the SPECIFIC prior question (2+3). "
255:            f"got: {result_t2.text!r}. metrics={metrics}"
256-        )
257-        # Codex iter-2 fix #3: STRONG compaction proof — explicit log
258-        # OR summary marker in messages, AND turn-2 input dropped
259-        # materially vs turn-1 input.
260-        assert compact_proven, (
261-            f"R2 expected compaction PROVEN: either '[auto-compact]' in "
262-            f"stdout or [CONVERSATION SUMMARY] marker in agent.messages. "
263-            f"current: log_seen={compact_log_seen}, "
264-            f"summary_marker={summary_marker_seen}. metrics={metrics}"
265-        )
266:        assert t2_dropped_materially, (
267-            f"R2 expected turn-2 input ≪ turn-1 input (proves buffer "
268:            f"compacted). t1_in={tokens_in_t1}, t2_in_estimate="
269:            f"{t2_input_estimate}. metrics={metrics}"
270-        )
271-        # Cost.
272-        assert cost_used <= _R2_COST_CAP_USD, (
273-            f"R2 cost ${cost_used:.4f} exceeded cap ${_R2_COST_CAP_USD}. "
274-            f"metrics={metrics}"
275-        )
276-        # Sanity: large input was actually sent.
277:        assert tokens_in_t1 > 50_000, (
278:            f"R2 expected turn-1 input_tokens >50K; got {tokens_in_t1}. "
279-            f"metrics={metrics}"
280-        )
281-    finally:
282-        os.chdir(cwd_before)
283-        CONFIG.workspace = saved_ws
284-        sec_mgr.SECURITY = saved_sec
285-        if saved_cost_limit is not None:
286-            CONFIG.session_cost_limit = saved_cost_limit
Cannot set property. Property setting is supported only on core types in this language mode.
At line:1 char:1
+ [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : PropertySetterNotSupportedInConstrainedLanguage
 

codex
**Axis A: APPROVE**

The three iter-2 issues are closed.

`compact_proven` no longer relies on `api_calls`; it uses the `[auto-compact]` success log or a message-buffer summary marker. In current code that is strong: `query_engine.py` only emits `[auto-compact]` after `_result.success`, and `Compactor.compact()` always writes:

`role: "user"` with content:
`[CONVERSATION SUMMARY]\n{summary}\n[END SUMMARY — Continuing from here]`

See [compactor.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/compactor.py:499).

`t2_dropped_materially` is asserted separately, and T2 recall no longer accepts `"5"`; it requires the original `2 + 3` question shape.

Residual edge case: the test comment still says “system block,” but the actual compactor writes a user-role summary message. The assertion is compatible with the implementation.

`t2_input_estimate = tokens_in - tokens_in_t1` is acceptable in the current ordering: `tokens_in_t1` is captured after T1 returns, and the summary call happens inside T1 before return, so subtraction excludes the summary call. Caveat: `tokens_in_t1` is “T1 run including summary call,” not pure first-model-call input, so the 50% denominator is looser than the wording implies. Combined with `compact_proven`, this is not a blocker.

**Axis B: APPROVE**

Worst-case cost around `$0.18-$0.20` is plausible: T1 large input, summary call over the same large buffer, then small post-compact T2. Even allowing summary output up to 2K tokens, the `$0.50` cap has enough headroom.

`on_stop_check` is still loop-boundary based, not a preflight guard before the internal summary call, but max turns plus the cost math make the spend risk acceptable.

**Axis C: APPROVE**

Iter-3 now gives mandatory empirical evidence for Block A:

Compactor success is proven by success log or `[CONVERSATION SUMMARY]` in `agent.messages`; buffer shrink is asserted by T2 input delta; post-compact recall must preserve the original arithmetic question.

This is strong enough end-to-end evidence for the first real R2 AWS run.

**FINAL: APPROVE_FOR_AWS_CALL**
tokens used
47,516
**Axis A: APPROVE**

The three iter-2 issues are closed.

`compact_proven` no longer relies on `api_calls`; it uses the `[auto-compact]` success log or a message-buffer summary marker. In current code that is strong: `query_engine.py` only emits `[auto-compact]` after `_result.success`, and `Compactor.compact()` always writes:

`role: "user"` with content:
`[CONVERSATION SUMMARY]\n{summary}\n[END SUMMARY — Continuing from here]`

See [compactor.py](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/compactor.py:499).

`t2_dropped_materially` is asserted separately, and T2 recall no longer accepts `"5"`; it requires the original `2 + 3` question shape.

Residual edge case: the test comment still says “system block,” but the actual compactor writes a user-role summary message. The assertion is compatible with the implementation.

`t2_input_estimate = tokens_in - tokens_in_t1` is acceptable in the current ordering: `tokens_in_t1` is captured after T1 returns, and the summary call happens inside T1 before return, so subtraction excludes the summary call. Caveat: `tokens_in_t1` is “T1 run including summary call,” not pure first-model-call input, so the 50% denominator is looser than the wording implies. Combined with `compact_proven`, this is not a blocker.

**Axis B: APPROVE**

Worst-case cost around `$0.18-$0.20` is plausible: T1 large input, summary call over the same large buffer, then small post-compact T2. Even allowing summary output up to 2K tokens, the `$0.50` cap has enough headroom.

`on_stop_check` is still loop-boundary based, not a preflight guard before the internal summary call, but max turns plus the cost math make the spend risk acceptable.

**Axis C: APPROVE**

Iter-3 now gives mandatory empirical evidence for Block A:

Compactor success is proven by success log or `[CONVERSATION SUMMARY]` in `agent.messages`; buffer shrink is asserted by T2 input delta; post-compact recall must preserve the original arithmetic question.

This is strong enough end-to-end evidence for the first real R2 AWS run.

**FINAL: APPROVE_FOR_AWS_CALL**
