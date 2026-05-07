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
import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


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


@dataclass
class TokenWarningState:
    """A-4 token warning state for compact UI/status surfaces."""

    tokens_used: int
    context_window: int
    percent_used: float
    should_microcompact: bool
    should_auto_compact: bool
    warning: bool
    error: bool


@dataclass
class ContentReplacementEntry:
    """A-42 persisted replacement metadata for compacted content."""

    original_ref: str
    replacement_ref: str
    original_tokens: int
    replacement_tokens: int
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_ref": self.original_ref,
            "replacement_ref": self.replacement_ref,
            "original_tokens": self.original_tokens,
            "replacement_tokens": self.replacement_tokens,
            "reason": self.reason,
        }


class TransitionReason(str, Enum):
    """A-34 transition reasons shared by compact/query state."""

    COMPACT_SUCCESS = "compact_success"
    COMPACT_SKIPPED = "compact_skipped"
    CONTEXT_OVERFLOW_PRE_API = "context_overflow_pre_api"
    API_ERROR = "api_error"
    USER_ABORT = "user_abort"
    END_TURN = "end_turn"


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
        self._consecutive_failures = 0
        self._disabled = False

    def should_attempt(self) -> Tuple[bool, str]:
        """True iff a compact attempt is allowed right now.

        Returns (allowed, reason). When False, the reason explains why
        (session cap hit / cooldown active) so the caller can surface
        a clear log message. Session cap checked FIRST — once exhausted,
        no further attempts make sense regardless of cooldown.
        """
        with self._lock:
            if self._disabled:
                return False, (
                    "auto-compact disabled after "
                    f"{self._consecutive_failures} consecutive failures"
                )
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

    def record_success(self) -> None:
        """Reset consecutive-failure state after a successful compact."""
        with self._lock:
            self._consecutive_failures = 0
            self._disabled = False

    def record_failure(self) -> Tuple[bool, str]:
        """Record a failed compact attempt.

        Returns (disabled, reason). A-3 disables auto-compact after three
        consecutive failures so the agent does not spin on an expensive
        compact path.
        """
        with self._lock:
            self._consecutive_failures += 1
            if self._consecutive_failures >= Compactor.MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES:
                self._disabled = True
                return True, (
                    "auto-compact disabled after "
                    f"{self._consecutive_failures} consecutive failures"
                )
            return False, ""

    def reset(self) -> None:
        with self._lock:
            self._last_attempt = 0.0
            self._session_count = 0
            self._consecutive_failures = 0
            self._disabled = False

    def try_attempt(self) -> Tuple[bool, str]:
        """Atomic check+record: if allowed, record the attempt and
        return (True, ""). If not allowed, return (False, reason)
        without recording. Concurrent callers cannot both pass the
        check before either records — this closes the TOCTOU window
        in should_attempt() + record_attempt() that Codex iter-1
        finding #3 (MEDIUM) flagged.
        """
        with self._lock:
            if self._disabled:
                return False, (
                    "auto-compact disabled after "
                    f"{self._consecutive_failures} consecutive failures"
                )
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
    MAX_OUTPUT_TOKENS_FOR_SUMMARY = 20_000
    AUTOCOMPACT_BUFFER = 13_000
    AUTOCOMPACT_WARNING_TOKENS = 20_000
    AUTOCOMPACT_ERROR_TOKENS = 20_000
    MANUAL_COMPACT_BUFFER = 3_000
    MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3
    MICROCOMPACT_TRIGGER_PERCENT = 0.70
    MICROCOMPACT_MIN_SAVINGS = 5_000
    COLD_CACHE_THRESHOLD_SECONDS = 30 * 60
    MICROCOMPACT_MARKER = "[Tool output cleared to save context - re-run if needed]"
    KEEP_LAST_N_PER_TOOL = 3
    KEEP_LAST_N_COLD_CACHE = 1
    COMPACTABLE_TOOLS = {
        "read_file",
        "bash",
        "grep",
        "glob",
        "list_dir",
        "python_exec",
        "create_chart",
        "semantic_search",
    }
    MICROCOMPACT_TOOLS = COMPACTABLE_TOOLS
    SUMMARY_TRIGGER_PERCENT = 0.80
    CONTEXT_COLLAPSE_TRIGGER_PERCENT = 0.85
    KEEP_LAST_MESSAGES = 3
    MAX_PTL_RETRIES = 3
    PTL_RETRY_BACKOFF_SECONDS = 0.0

    SUMMARY_TOOL_RESULT_THRESHOLD = 8_000
    SUMMARY_TOOL_RESULT_HEAD = 2_000
    SUMMARY_TOOL_RESULT_TAIL = 1_000
    POST_COMPACT_FILE_TOKEN_BUDGET = 12_000
    POST_COMPACT_SKILL_TOKEN_BUDGET = 4_000
    POST_COMPACT_EXCLUDED_BASENAMES = {
        "claude.md",
        "memory.md",
        "agent_status.md",
    }

    PROTECTED_TOOLS = {"todo_write", "todo_read", "semantic_search"}

    FIXED_OVERHEAD_TOKENS = 6_000

    # Aux client cache (per-process); built lazily.
    _aux_client_cache: Dict[str, Any] = {}
    _transition_reason: str = ""
    _last_session_activity: float = 0.0
    _compact_warning_suppressed_until: float = 0.0
    _last_content_replacements: List[ContentReplacementEntry] = []

    # --------------------------------------------------------
    # Microcompact
    # --------------------------------------------------------

    @classmethod
    def get_effective_context_window_size(
        cls,
        model_id: str = "",
        configured_max: int = 200_000,
    ) -> int:
        """A-1 context window after reserving summary output tokens."""
        model = (model_id or "").lower()
        base = int(configured_max or 200_000)
        if "haiku" in model or "sonnet" in model or "opus" in model:
            base = max(base, 200_000)
        return max(1, base - cls.MAX_OUTPUT_TOKENS_FOR_SUMMARY)

    @classmethod
    def _context_usage(cls, messages: List[Dict[str, Any]], max_tokens: int) -> int:
        try:
            from runtime.tokens import TOKENS
            overhead = TOKENS.final_context_tokens_from_last_response()
            if overhead == 0:
                overhead = cls.FIXED_OVERHEAD_TOKENS
        except Exception:
            overhead = cls.FIXED_OVERHEAD_TOKENS
        return cls.estimate_tokens(messages) + overhead

    @classmethod
    def calculate_token_warning_state(
        cls,
        messages: List[Dict[str, Any]],
        max_tokens: int,
    ) -> TokenWarningState:
        """A-4 five-flag token warning state used by UI/status code."""
        window = max(1, int(max_tokens))
        used = cls._context_usage(messages, window)
        percent = used / window
        return TokenWarningState(
            tokens_used=used,
            context_window=window,
            percent_used=percent,
            should_microcompact=percent >= cls.MICROCOMPACT_TRIGGER_PERCENT,
            should_auto_compact=percent >= cls.SUMMARY_TRIGGER_PERCENT,
            warning=used >= window - cls.AUTOCOMPACT_WARNING_TOKENS,
            error=used >= window - cls.AUTOCOMPACT_ERROR_TOKENS,
        )

    @staticmethod
    def should_auto_compact(query_source: str = "user") -> bool:
        """A-5/A-19 recursion guard for compact/session-memory turns."""
        return (query_source or "user") not in {"compact", "session_memory"}

    @staticmethod
    def has_exact_error_message(exc: Exception, text: str) -> bool:
        """A-23 exact abort/error matching helper."""
        return str(exc) == text

    @staticmethod
    def is_user_abort_error(exc: Exception) -> bool:
        """A-23 compact aborts should not be logged as model/API errors."""
        return str(exc).strip().lower() in {
            "user aborted",
            "user abort",
            "aborted by user",
            "operation cancelled",
            "operation canceled",
        }

    @staticmethod
    def _is_stale_round_trip(messages: List[Dict[str, Any]]) -> bool:
        """A-24 detect a dangling assistant tool_use without tool_result."""
        pending: set[str] = set()
        for msg in messages:
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use" and block.get("id"):
                    pending.add(str(block["id"]))
                elif block.get("type") == "tool_result" and block.get("tool_use_id"):
                    pending.discard(str(block["tool_use_id"]))
        return bool(pending)

    @classmethod
    def _sleep_between_ptl_retries(cls, should_abort: Optional[Callable[[], bool]] = None) -> bool:
        """A-20 abortable retry sleep. Returns False when aborted."""
        if should_abort and should_abort():
            return False
        if cls.PTL_RETRY_BACKOFF_SECONDS > 0:
            end = time.time() + cls.PTL_RETRY_BACKOFF_SECONDS
            while time.time() < end:
                if should_abort and should_abort():
                    return False
                time.sleep(min(0.05, end - time.time()))
        return True

    @classmethod
    def set_transition_reason(cls, reason: str) -> None:
        """A-34 transition.reason equivalent for compact state changes."""
        cls._transition_reason = reason

    @classmethod
    def transition_reason(cls) -> str:
        return cls._transition_reason

    @classmethod
    def reset_retry_counters(cls) -> None:
        """A-30 reset post-compression retry counters tracked by compactor."""
        try:
            auto_compact = globals().get("AUTO_COMPACT")
            if auto_compact is not None:
                auto_compact.record_success()
        except Exception:
            pass
        cls._transition_reason = "post_compact_retry_counters_reset"

    @classmethod
    def touch_session_activity(cls) -> float:
        """A-18 keep a live activity heartbeat during compaction."""
        cls._last_session_activity = time.time()
        return cls._last_session_activity

    @classmethod
    def last_session_activity(cls) -> float:
        return cls._last_session_activity

    @classmethod
    def suppress_compact_warning_state(cls, seconds: float = 30.0) -> None:
        """A-15 suppress bogus warning immediately after compaction."""
        cls._compact_warning_suppressed_until = time.time() + max(0.0, float(seconds))

    @classmethod
    def compact_warning_suppressed(cls) -> bool:
        return time.time() < cls._compact_warning_suppressed_until

    @classmethod
    def gc_compact_boundary_preserved_segments(
        cls,
        messages: List[Dict[str, Any]],
        tail_keep: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """A-38 compact-boundary GC for repeated preservedSegment metadata.

        Keep normal messages unchanged, keep the tail untouched, and dedupe
        older preserved segments by id so long sessions do not accumulate
        stale compact-boundary metadata.
        """
        if not messages:
            return []
        keep = cls.KEEP_LAST_MESSAGES if tail_keep is None else max(0, int(tail_keep))
        if keep <= 0 or len(messages) <= keep:
            head = list(messages)
            tail: List[Dict[str, Any]] = []
        else:
            head = list(messages[:-keep])
            tail = list(messages[-keep:])

        latest_by_id: Dict[str, int] = {}
        for idx, msg in enumerate(head):
            seg_id = cls._preserved_segment_id(msg)
            if seg_id:
                latest_by_id[seg_id] = idx

        out: List[Dict[str, Any]] = []
        for idx, msg in enumerate(head):
            seg_id = cls._preserved_segment_id(msg)
            if seg_id and latest_by_id.get(seg_id) != idx:
                continue
            out.append(msg)
        return out + tail

    @staticmethod
    def _preserved_segment_id(msg: Dict[str, Any]) -> str:
        raw = (
            msg.get("preservedSegment")
            or msg.get("preserved_segment")
            or msg.get("preserved_segment_id")
        )
        if raw is True:
            return "default"
        if isinstance(raw, dict):
            return str(raw.get("id") or raw.get("name") or "default")
        if raw:
            return str(raw)
        if msg.get("compact_boundary") and msg.get("is_meta"):
            return str(msg.get("id") or "compact_boundary")
        return ""

    @classmethod
    def _find_tool_name(cls, messages: List[Dict[str, Any]], tool_use_id: str) -> str:
        """Return the tool name that created a given tool_use id."""
        if not tool_use_id:
            return ""
        for msg in messages:
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if (
                    isinstance(block, dict)
                    and block.get("type") == "tool_use"
                    and block.get("id") == tool_use_id
                ):
                    return str(block.get("name", ""))
        return ""

    @classmethod
    def microcompact(
        cls,
        messages: List[Dict[str, Any]],
        keep_n_override: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Clear old compactable tool_result bodies without changing turns."""
        keep_n = (
            int(keep_n_override)
            if keep_n_override is not None
            else cls.KEEP_LAST_N_PER_TOOL
        )
        keep_n = max(1, keep_n)
        tokens_before = cls.estimate_tokens(messages)
        keep_counts: Dict[str, int] = {}
        any_read_file_cleared = False
        result_msgs: List[Dict[str, Any]] = []

        for msg in reversed(messages):
            content = msg.get("content")
            if not isinstance(content, list):
                result_msgs.append(msg)
                continue
            changed = False
            new_content_reversed: List[Any] = []
            for block in reversed(content):
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    tool_use_id = str(block.get("tool_use_id", ""))
                    tool_name = cls._find_tool_name(messages, tool_use_id)
                    if tool_name in cls.MICROCOMPACT_TOOLS:
                        keep_counts[tool_name] = keep_counts.get(tool_name, 0) + 1
                        already_cleared = block.get("content") == cls.MICROCOMPACT_MARKER
                        if keep_counts[tool_name] > keep_n and not already_cleared:
                            block = dict(block)
                            block["content"] = cls.MICROCOMPACT_MARKER
                            changed = True
                            if tool_name == "read_file":
                                any_read_file_cleared = True
                new_content_reversed.append(block)
            if changed:
                msg = dict(msg)
                msg["content"] = list(reversed(new_content_reversed))
            result_msgs.append(msg)

        result_msgs = list(reversed(result_msgs))
        tokens_saved = max(0, tokens_before - cls.estimate_tokens(result_msgs))
        if tokens_saved < cls.MICROCOMPACT_MIN_SAVINGS:
            return messages, 0

        if any_read_file_cleared:
            try:
                from runtime.file_cache import FILE_CACHE
                FILE_CACHE.clear_context()
            except Exception:
                pass
        return result_msgs, tokens_saved

    @classmethod
    def should_microcompact(cls, messages: List[Dict[str, Any]], max_tokens: int) -> bool:
        """True iff token estimate crosses the 70% microcompact threshold."""
        total = cls._context_usage(messages, max_tokens)
        return total > max_tokens * cls.MICROCOMPACT_TRIGGER_PERCENT

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
        total = cls._context_usage(messages, max_tokens)
        return total > max_tokens * cls.SUMMARY_TRIGGER_PERCENT

    @classmethod
    def would_exceed_context_limit(
        cls,
        messages: List[Dict[str, Any]],
        max_tokens: int,
        tool_schema_tokens: int = 0,
    ) -> bool:
        """A-35 pre-API context guard, including A-29 tool schema tokens."""
        total = cls._context_usage(messages, max_tokens) + max(0, int(tool_schema_tokens))
        return total >= max_tokens - cls.AUTOCOMPACT_ERROR_TOKENS

    @classmethod
    def estimate_tool_schema_tokens(cls, tools: Iterable[Dict[str, Any]]) -> int:
        """A-29 include tool schemas in pre-compression estimates."""
        total = 0
        for tool in tools or []:
            try:
                payload = json.dumps(tool, sort_keys=True, separators=(",", ":"))
            except Exception:
                payload = str(tool)
            total += cls.estimate_tokens(payload)
        return total

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
    def strip_images_from_messages(
        cls,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """A-6 remove image blocks from compact-summary input."""
        out: List[Dict[str, Any]] = []
        for msg in messages:
            content = msg.get("content")
            if not isinstance(content, list):
                out.append(msg)
                continue
            new_content = [
                block for block in content
                if not (
                    isinstance(block, dict)
                    and (
                        block.get("type") == "image"
                        or block.get("source", {}).get("type") == "base64"
                    )
                )
            ]
            if len(new_content) == len(content):
                out.append(msg)
            else:
                clone = dict(msg)
                clone["content"] = new_content
                out.append(clone)
        return out

    @classmethod
    def strip_reinjected_attachments(
        cls,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """A-7 remove post-compact reinjected attachment blocks before summary."""
        out: List[Dict[str, Any]] = []
        for msg in messages:
            content = msg.get("content")
            if not isinstance(content, list):
                out.append(msg)
                continue
            new_content = [
                block for block in content
                if not (
                    isinstance(block, dict)
                    and (
                        block.get("is_reinjected_attachment")
                        or block.get("name") in {"skill_discovery", "skill_listing"}
                    )
                )
            ]
            if len(new_content) == len(content):
                out.append(msg)
            else:
                clone = dict(msg)
                clone["content"] = new_content
                out.append(clone)
        return out

    @classmethod
    def group_messages_by_api_round(
        cls,
        messages: List[Dict[str, Any]],
    ) -> List[List[Dict[str, Any]]]:
        """A-9 group conversation messages into Bedrock API rounds."""
        rounds: List[List[Dict[str, Any]]] = []
        current: List[Dict[str, Any]] = []
        for msg in messages:
            if msg.get("role") == "user" and current:
                rounds.append(current)
                current = [msg]
            else:
                current.append(msg)
        if current:
            rounds.append(current)
        return rounds

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
        cls.touch_session_activity()
        from runtime.tokens import TOKENS

        summary_messages = cls.strip_reinjected_attachments(
            cls.strip_images_from_messages(messages)
        )
        pruned_messages = cls._prune_tool_results_for_summary(summary_messages)
        pruned_messages, _, _ = cls.repair_tool_result_pairs_for_bedrock(
            pruned_messages,
            reason="pre-summary orphaned tool_use repaired",
        )
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
                cls.touch_session_activity()
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
                    cls.touch_session_activity()
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
                if not cls._sleep_between_ptl_retries():
                    logging.info("[COMPACT] PTL retry aborted by user")
                    return None
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
        replacement_id = cls.generate_temp_file_path(
            summary,
            prefix="compact-summary",
            suffix=".txt",
        )
        cls._last_content_replacements = [
            ContentReplacementEntry(
                original_ref="conversation-prefix",
                replacement_ref=replacement_id,
                original_tokens=cls.estimate_tokens(messages[:-keep_last]),
                replacement_tokens=cls.estimate_tokens(summary),
                reason="compact",
            )
        ]
        summary_msg = {
            "role": "user",
            "content": (
                f"[CONVERSATION SUMMARY]\n{summary}\n"
                "[END SUMMARY — Continuing from here]"
            ),
        }
        summary_msg["content"] = (
            f"{summary_msg['content']}\n"
            f"[marble-origami-commit: {replacement_id}]"
        )
        summary_msg["is_meta"] = True
        summary_msg["compact_metadata"] = {
            "marble-origami-commit": replacement_id,
            "content_replacements": [
                entry.to_dict() for entry in cls._last_content_replacements
            ],
        }
        post_messages = [summary_msg] + recent
        todo_msg = cls.build_todo_restoration_message()
        if todo_msg:
            post_messages.append(todo_msg)
        return cls.repair_tool_result_pairs_for_bedrock(post_messages)[0]

    @classmethod
    def build_cache_sharing_fork_after_compact(
        cls,
        parent_messages: List[Dict[str, Any]],
        parent_assistant_message: Dict[str, Any],
        directive: str,
        summary: str,
    ) -> List[Dict[str, Any]]:
        """A-13 compacted parent history plus G2 cache-sharing fork replay."""
        from subagent.fork import build_forked_messages, is_in_fork_child

        if is_in_fork_child(parent_messages):
            raise ValueError("fork children cannot create nested cache-sharing forks")
        compacted_parent = cls.compact(parent_messages, summary) if summary else list(parent_messages)
        return build_forked_messages(compacted_parent, parent_assistant_message, directive)

    @classmethod
    def flush_memories_before_compact(
        cls,
        messages: List[Dict[str, Any]],
        extractor: Optional[Any] = None,
        extract_fn: Optional[Callable[[List[Dict], str], List[str]]] = None,
        workspace: Optional[str] = None,
    ) -> List[str]:
        """A-27 force a memory-only extraction turn before compression."""
        if extractor is None:
            if extract_fn is None:
                return []
            try:
                from memory import create_memory_extractor
                from runtime.config import CONFIG
                extractor = create_memory_extractor(
                    workspace=workspace or getattr(CONFIG, "workspace", ".")
                )
            except Exception:
                return []
        try:
            return list(extractor.extract_memories(
                messages,
                extract_fn=extract_fn,
                force=True,
            ))
        except Exception as exc:
            logging.warning("[COMPACT] pre-compact memory flush failed: %s", exc)
            return []

    @classmethod
    def build_todo_restoration_message(cls) -> Optional[Dict[str, Any]]:
        """A-28 re-inject current todos after compaction."""
        try:
            from tools.todo import _todo_read_executor
            todos = _todo_read_executor({}, context={})
        except Exception:
            return None
        if not todos or "no todos" in todos.lower():
            return None
        return {
            "role": "user",
            "content": "[TODO RESTORATION]\n" + todos,
            "is_meta": True,
        }

    @classmethod
    def create_post_compact_file_attachments(
        cls,
        paths: Optional[Iterable[str]] = None,
    ) -> List[Dict[str, Any]]:
        """A-11 rebuild bounded file attachments after compaction."""
        if paths is None:
            try:
                from runtime.file_cache import FILE_CACHE
                paths = list(getattr(FILE_CACHE, "_in_context", set()))
            except Exception:
                paths = []
        attachments: List[Dict[str, Any]] = []
        used = 0
        for path in paths or []:
            base = os.path.basename(str(path)).lower()
            if base in cls.POST_COMPACT_EXCLUDED_BASENAMES:
                continue
            try:
                text = open(path, "r", encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            tokens = cls.estimate_tokens(text)
            if used + tokens > cls.POST_COMPACT_FILE_TOKEN_BUDGET:
                remaining = max(0, cls.POST_COMPACT_FILE_TOKEN_BUDGET - used)
                text = text[: remaining * 3]
                tokens = cls.estimate_tokens(text)
            if tokens <= 0:
                continue
            used += tokens
            attachments.append({
                "type": "text",
                "text": f"[POST-COMPACT FILE: {path}]\n{text}",
                "is_reinjected_attachment": True,
            })
            if used >= cls.POST_COMPACT_FILE_TOKEN_BUDGET:
                break
        return attachments

    @classmethod
    def create_skill_attachment_if_needed(
        cls,
        skill_manager: Optional[Any],
    ) -> Optional[Dict[str, Any]]:
        """A-12 re-inject the active skill body after compaction."""
        if skill_manager is None:
            return None
        try:
            if not getattr(skill_manager, "active_skill", None):
                return None
            body = skill_manager.get_active_skill_prompt(session_id="post-compact")
        except Exception:
            return None
        if not body:
            return None
        return {
            "type": "text",
            "text": "[POST-COMPACT ACTIVE SKILL]\n"
            + body[: cls.POST_COMPACT_SKILL_TOKEN_BUDGET * 3],
            "is_reinjected_attachment": True,
        }

    @classmethod
    def last_content_replacements(cls) -> List[ContentReplacementEntry]:
        return list(cls._last_content_replacements)

    @staticmethod
    def generate_temp_file_path(
        content: str,
        prefix: str = "tmp",
        suffix: str = "",
        root: Optional[str] = None,
    ) -> str:
        """A-43 content-hash temp path helper."""
        digest = hashlib.sha256((content or "").encode("utf-8")).hexdigest()[:16]
        safe_prefix = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in prefix)
        root_dir = root or ".agent_tmp"
        return os.path.join(root_dir, f"{safe_prefix}-{digest}{suffix}")

    @classmethod
    def normalize_for_prefix_cache(cls, value: Any) -> str:
        """A-32 stable JSON/string normalization for cache-prefix reuse."""
        if isinstance(value, str):
            return "\n".join(line.rstrip() for line in value.strip().splitlines())
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def sanitize_messages_surrogates(cls, value: Any) -> Any:
        """A-26 recursively replace lone surrogate codepoints before Bedrock."""
        if isinstance(value, str):
            return value.encode("utf-8", "replace").decode("utf-8")
        if isinstance(value, list):
            return [cls.sanitize_messages_surrogates(item) for item in value]
        if isinstance(value, tuple):
            return tuple(cls.sanitize_messages_surrogates(item) for item in value)
        if isinstance(value, dict):
            return {
                cls.sanitize_messages_surrogates(k): cls.sanitize_messages_surrogates(v)
                for k, v in value.items()
            }
        return value

    @classmethod
    def run_post_compact_cleanup(cls, skill_manager: Optional[Any] = None) -> Dict[str, bool]:
        """Invalidate context-sensitive caches after successful compaction."""
        cleared = {
            "file_read_tracking": False,
            "file_cache": False,
            "skill_listing_cache": False,
            "prompt_section_cache": False,
        }

        try:
            from tools import _file_read_tracking
            _file_read_tracking.clear_tracked_reads()
            cleared["file_read_tracking"] = True
        except Exception:
            pass

        try:
            from runtime.file_cache import FILE_CACHE
            FILE_CACHE.clear_all()
            cleared["file_cache"] = True
        except Exception:
            pass

        if skill_manager is not None:
            try:
                if hasattr(skill_manager, "invalidate_cache"):
                    skill_manager.invalidate_cache("all")
                elif hasattr(skill_manager, "clear_listing_cache"):
                    skill_manager.clear_listing_cache()
                elif hasattr(skill_manager, "_cache"):
                    skill_manager._cache.clear()
                cleared["skill_listing_cache"] = True
            except Exception:
                pass

        try:
            from prompt.sections import clear_section_cache
            clear_section_cache()
            cleared["prompt_section_cache"] = True
        except Exception:
            pass

        return cleared

    @classmethod
    def inject_missing_tool_result_stubs(
        cls,
        messages: List[Dict[str, Any]],
        reason: str = "post-compact orphaned tool_use repaired",
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Insert synthetic tool_result stubs for orphaned tool_use blocks."""
        try:
            from core.parallel_dispatch import synthetic_tool_result_stub
        except Exception:
            def synthetic_tool_result_stub(tool_use_id: str, reason: str = "") -> Dict[str, Any]:
                return {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": f"[synthetic stub: {reason}]",
                    "is_error": False,
                }

        repaired: List[Dict[str, Any]] = []
        inserted = 0
        idx = 0
        while idx < len(messages):
            msg = messages[idx]
            repaired.append(msg)
            content = msg.get("content")
            if msg.get("role") != "assistant" or not isinstance(content, list):
                idx += 1
                continue

            tool_ids = [
                str(block.get("id", ""))
                for block in content
                if isinstance(block, dict)
                and block.get("type") == "tool_use"
                and block.get("id")
            ]
            if not tool_ids:
                idx += 1
                continue

            next_msg = messages[idx + 1] if idx + 1 < len(messages) else None
            next_content = next_msg.get("content") if isinstance(next_msg, dict) else None
            present: set[str] = set()
            if isinstance(next_content, list):
                present = {
                    str(block.get("tool_use_id", ""))
                    for block in next_content
                    if isinstance(block, dict) and block.get("type") == "tool_result"
                }
            missing = [tool_id for tool_id in tool_ids if tool_id not in present]
            if missing:
                stubs = [
                    synthetic_tool_result_stub(tool_id, reason=reason)
                    for tool_id in missing
                ]
                if isinstance(next_msg, dict) and next_msg.get("role") == "user":
                    patched_next = dict(next_msg)
                    if isinstance(next_content, list):
                        patched_next["content"] = stubs + list(next_content)
                    elif isinstance(next_content, str):
                        patched_next["content"] = stubs + [
                            {"type": "text", "text": next_content}
                        ]
                    else:
                        patched_next["content"] = stubs
                    repaired.append(patched_next)
                    idx += 2
                else:
                    repaired.append({"role": "user", "content": stubs})
                    idx += 1
                inserted += len(stubs)
            else:
                idx += 1

        return repaired, inserted

    @classmethod
    def repair_tool_result_pairs_for_bedrock(
        cls,
        messages: List[Dict[str, Any]],
        reason: str = "orphaned tool_use repaired",
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """Make tool_use/tool_result pairs valid for Bedrock.

        Bedrock requires any assistant tool_use blocks to be followed
        immediately by user tool_result blocks with matching IDs, and rejects
        tool_result IDs that do not match the immediately preceding assistant.
        Compaction may summarize away one side of that pair, so repair both
        directions before sending a compacted or summary-input history back to
        the model.
        """
        repaired, inserted = cls.inject_missing_tool_result_stubs(
            messages,
            reason=reason,
        )
        out: List[Dict[str, Any]] = []
        expected: set[str] = set()
        converted = 0

        for msg in repaired:
            role = msg.get("role")
            content = msg.get("content")

            if role == "user" and isinstance(content, list):
                new_blocks: List[Any] = []
                mutated = False
                seen_results: set[str] = set()
                for block in content:
                    if not (
                        isinstance(block, dict)
                        and block.get("type") == "tool_result"
                    ):
                        new_blocks.append(block)
                        continue

                    tool_use_id = str(block.get("tool_use_id", ""))
                    if tool_use_id in expected and tool_use_id not in seen_results:
                        seen_results.add(tool_use_id)
                        new_blocks.append(block)
                        continue

                    converted += 1
                    mutated = True
                    raw_content = block.get("content", "")
                    if isinstance(raw_content, list):
                        raw_content = json.dumps(raw_content, ensure_ascii=False)
                    elif not isinstance(raw_content, str):
                        raw_content = str(raw_content)
                    if len(raw_content) > cls.SUMMARY_TOOL_RESULT_HEAD:
                        raw_content = (
                            raw_content[: cls.SUMMARY_TOOL_RESULT_HEAD]
                            + "\n... [orphaned tool_result truncated] ..."
                        )
                    new_blocks.append({
                        "type": "text",
                        "text": (
                            "[orphaned tool_result converted to text for "
                            f"Bedrock validation; tool_use_id={tool_use_id}]\n"
                            f"{raw_content}"
                        ),
                    })

                if mutated:
                    patched = dict(msg)
                    patched["content"] = new_blocks
                    out.append(patched)
                else:
                    out.append(msg)
                expected = set()
                continue

            out.append(msg)
            if role == "assistant" and isinstance(content, list):
                expected = {
                    str(block.get("id", ""))
                    for block in content
                    if isinstance(block, dict)
                    and block.get("type") == "tool_use"
                    and block.get("id")
                }
            else:
                expected = set()

        return out, inserted, converted

    @classmethod
    def run(
        cls,
        client: Any,
        messages: List[Dict[str, Any]],
        max_tokens: int = 200_000,
        skill_manager: Optional[Any] = None,
        memory_extractor: Optional[Any] = None,
        memory_extract_fn: Optional[Callable[[List[Dict], str], List[str]]] = None,
    ) -> CompactionResult:
        """End-to-end: prune → summarize → compact. Single entry point."""
        cls.touch_session_activity()
        before_tokens = cls.estimate_tokens(messages)
        if not cls.should_compact(messages, max_tokens):
            cls.set_transition_reason(TransitionReason.COMPACT_SKIPPED.value)
            return CompactionResult(
                success=False,
                error="compact not needed (under 80% trigger)",
                tokens_before=before_tokens,
                tokens_after=before_tokens,
                messages_after=list(messages),
            )
        cls.flush_memories_before_compact(
            messages,
            extractor=memory_extractor,
            extract_fn=memory_extract_fn,
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
        post_blocks: List[Dict[str, Any]] = []
        post_blocks.extend(cls.create_post_compact_file_attachments())
        skill_block = cls.create_skill_attachment_if_needed(skill_manager)
        if skill_block is not None:
            post_blocks.append(skill_block)
        if post_blocks:
            new_messages.append({
                "role": "user",
                "content": post_blocks,
                "is_meta": True,
            })
        cls.reset_retry_counters()
        cls.set_transition_reason(TransitionReason.COMPACT_SUCCESS.value)
        cls.suppress_compact_warning_state()
        cls.run_post_compact_cleanup(skill_manager=skill_manager)
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
    "TokenWarningState",
    "ContentReplacementEntry",
    "TransitionReason",
    "AutoCompactCircuitBreaker",
    "AUTO_COMPACT",
    "apply_cache_control_to_blocks",
    "count_tokens_via_haiku_fallback",
]
