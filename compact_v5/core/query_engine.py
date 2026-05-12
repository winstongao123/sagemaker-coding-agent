"""V5 core/query_engine.py â€” main agent loop (Phase 8 deliverable, ADR-014).

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
- tool_use â†’ tool_result message accumulation in the model-visible
  conversation buffer.
- Bedrock invocation through `BedrockClient.chat(...)`.
- System prompt assembly via `prompt.build_system_prompt(ctx)`.
- run_one_turn(...) helper for unit tests (single-turn, no loop).

OUT OF SCOPE â€” explicitly deferred to later phases (per ADR-014):
- Microcompact / context_collapse â€” Phase 11 UX (PS Issue #4 widget surface).
- 2-stage smart compaction (prune + LLM summary) â€” Phase 11.
- Skill auto-trigger â€” Phase 10 (`SKILLS.discover_relevant`).
- Plan mode injection of skills into prompt â€” Phase 10.
- Sub-agent forkSubagent â€” Phase 9 (`subagent/spawn.py`).
- File-read state tracking â€” Phase 4 already lands this; engine respects but
  doesn't reset on compact (no compact in Phase 8).
- Diminishing-returns / repetition guard â€” deferred.
- Notebook UX (output_fn callback contract) â€” Phase 11 owns the UI shape;
  Phase 8 takes a `output_fn: Callable[[str], None] = print` so tests can
  capture, but real notebook integration lives in Phase 11.

The engine is thread-safe ONLY in the sense that IterationBudget is. Multiple
concurrent `run()` calls on the same engine are NOT supported (matches v4).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .budget import IterationBudget
from .errors import BedrockErrorCategory, ErrorClassifier
from runtime.tool_surface import (
    MAX_TOOL_RESULT_MESSAGE_CHARS,
    XML_SYSTEM_REMINDER_TAG,
    enforce_tool_result_message_budget,
    xml_tag,
)


# ============================================================
# Result envelope
# ============================================================

@dataclass
class QueryResult:
    """Outcome of a `QueryEngine.run(...)` call.

    `text`           â€” final assistant text (last end_turn turn's text block).
    `messages`       â€” full message buffer including the user turn that
                       triggered this call. Caller may discard or persist.
    `stop_reason`    â€” "end_turn" | "max_turns" | "budget_exhausted" |
                       "context_overflow" | "fatal_error".
    `turns_used`     â€” count of model turns executed during this run.
    `budget_used`    â€” IterationBudget.used() snapshot at exit.
    `thinking`       â€” display-only extended-thinking text captured during
                       this run. Signed thinking blocks stay in `messages`;
                       this field is for UI/log visibility only.
    `error`          â€” short message when stop_reason indicates failure.
    """
    text: str = ""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    stop_reason: str = ""
    turns_used: int = 0
    budget_used: int = 0
    thinking: str = ""
    error: Optional[str] = None


@dataclass
class PromptCacheInvariantState:
    """A-33 frozen prompt-cache boundary state for an active conversation."""

    model_id: str
    system_prompt_hash: str
    tool_names: Tuple[str, ...]


class FallbackTriggeredError(Exception):
    """Signal that the current model should be swapped and retried once.

    Block E+F EF-3: thinking signatures are model-bound, so the retry path
    strips signature material before resubmitting the same turn to the
    fallback model.
    """

    def __init__(self, target_model_id: str, reason: str = ""):
        self.target_model_id = target_model_id
        self.reason = reason
        super().__init__(reason or f"fallback requested: {target_model_id}")


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


def _repair_messages_for_bedrock(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Best-effort final validation repair before any Bedrock call."""
    try:
        from core.compactor import Compactor
        repaired, _, _ = Compactor.repair_tool_result_pairs_for_bedrock(
            messages,
            reason="pre-api tool pair repair",
        )
        return repaired
    except Exception:
        return messages


def _coerce_tool_result_to_text(value: Any) -> str:
    """Map any tool-execute return value into a Bedrock tool_result text string.

    Tool implementations return diverse shapes (str / dict / list). Bedrock's
    tool_result content needs a string. Prefer str() for primitives, JSON for
    structured shapes â€” same convention as v4 dispatch."""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple)):
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            return str(value)
    return str(value)


def _strip_signature_from_content(content: Any) -> Any:
    if isinstance(content, list):
        stripped = []
        for block in content:
            if not isinstance(block, dict):
                stripped.append(block)
                continue
            if block.get("type") in {"thinking", "redacted_thinking"}:
                continue
            item = dict(block)
            for key in list(item):
                normalized = key.replace("_", "").lower()
                if "signature" in normalized or normalized in {
                    "encryptedcontent",
                }:
                    item.pop(key, None)
            stripped.append(item)
        return stripped
    return content


def strip_signature_blocks(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return messages safe to replay after a model fallback.

        Bedrock extended-thinking signatures are tied to the model that created
        them. Replaying those signatures to a different model can fail; thinking
        without its signature is also invalid, so fallback replay preserves
        text/tool context while dropping thinking blocks.
    """
    sanitized: List[Dict[str, Any]] = []
    for msg in messages:
        item = dict(msg)
        item["content"] = _strip_signature_from_content(item.get("content"))
        sanitized.append(item)
    return sanitized


def count_tool_calls(messages: List[Dict[str, Any]], tool_name: str) -> int:
    """Count how many tool_use blocks for `tool_name` appear in `messages`.

    Block M-2 (PORT_LOG #084) â€” verbatim port of Runnable's countToolCalls
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


def _persist_large_tool_results_for_message(
    blocks: List[Dict[str, Any]],
    *,
    session_id: str,
    per_tool_limit: int,
) -> List[Dict[str, Any]]:
    """Persist large result bodies before any model-visible truncation.

    Best-effort: a storage failure must not break tool dispatch, but successful
    storage gives long-running sessions a stable replay reference instead of
    silent loss from per-tool or aggregate message budgets.
    """
    try:
        from runtime.results import persist_large_tool_results
        return persist_large_tool_results(
            blocks,
            session_id=session_id,
            per_tool_limit=per_tool_limit,
            message_budget=MAX_TOOL_RESULT_MESSAGE_CHARS,
        )
    except Exception as exc:  # noqa: BLE001
        logging.warning(
            "[tool-results] failed to persist large tool results: %s: %s",
            type(exc).__name__, exc,
        )
        return [
            {
                k: v for k, v in block.items()
                if k not in {"_sageagent_tool_name", "_sageagent_max_result_chars"}
            }
            if isinstance(block, dict)
            else block
            for block in blocks
        ]


def _make_unicode_safe_output_fn(fn: Callable[[str], None]) -> Callable[[str], None]:
    """Wrap an output_fn so UnicodeEncodeError doesn't kill the agent loop.

    R-tier R1 PHASE B iter-1 fix (2026-05-03): on Windows the default
    stdout encoding is cp1252, which can't encode emoji like âœ… (U+2705).
    The model frequently emits emoji in summary blocks. Without this
    wrapper, the very first call to `print(response.text)` raises
    UnicodeEncodeError and the entire agent loop dies â€” even though
    the agent's actual work (chart.png + report.docx) was done.

    Strategy:
    1. Try the callable as-is (no behavior change on UTF-8 terminals).
    2. On UnicodeEncodeError, fall back to the terminal's encoding with
       errors='replace' (preserves more chars than ASCII).
    3. If THAT still fails, ASCII-replace as the final safe net.

    This is symmetric to Block H's input-side surrogate sanitization â€”
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
        status_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        tool_gen_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        abort_events: Optional[Any] = None,
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
                the first user turn (Phase 10 wiring contract â€” Codex
                Phase-10 BLOCKER fix). When None, no skill machinery runs
                â€” preserves Phase 1-8 backwards compatibility for tests.
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

        # Block M-2: structured-output retry guard (PORT_LOG #084 â€” Runnable
        # QueryEngine.ts:1004-1048 countToolCalls + MAX_STRUCTURED_OUTPUT_RETRIES).
        # When `synthetic_output_tool_name` is set, the engine counts how many
        # times that tool appears in self.messages during this run() and
        # halts with stop_reason="error_max_structured_output_retries" at the
        # retry limit. Default name=None disables the check (v5 has no
        # built-in structured-output mode; this is a hook for future support).
        self.synthetic_output_tool_name = synthetic_output_tool_name
        self.max_structured_output_retries = max(1, int(max_structured_output_retries))
        # Block E+F EF-8/EF-5: optional read-only event callbacks for
        # notebook/runtime UI surfaces. Defaults preserve the historical
        # output_fn-only behavior.
        self.status_callback = status_callback
        self.tool_gen_callback = tool_gen_callback
        self.abort_events = tuple(abort_events or ())

        self.messages: List[Dict[str, Any]] = []
        # Tool names that have been "discovered" via tool_search this run.
        # Their schemas are added to per-turn `tools=` API param until the
        # run ends. v5 does NOT persist discovery across `run()` calls â€” the
        # set is fresh each user message (matches Runnable's per-message
        # discovered set).
        self._discovered_tool_names: Set[str] = set()
        # Block F2 â€” per-run BudgetTracker for iteration-budget auto-continuation.
        # Created lazily inside run() when CONFIG.enable_token_budget_continuation
        # is True; reset each run() so continuation state never leaks across
        # user messages.
        self._budget_tracker: Optional[Any] = None
        # Block A A-16: timestamp of the last main Bedrock call. A long idle
        # gap means prompt cache is cold, so the next request can microcompact
        # old tool_result bodies before paying to re-upload them.
        self._last_api_call_time: float = 0.0
        self._prompt_cache_state: Optional[PromptCacheInvariantState] = None
        self._frozen_system_prompt: Optional[str] = None
        self._frozen_tool_names: Tuple[str, ...] = ()
        self._tool_denials_this_turn = 0
        self._partial_tool_names: Set[str] = set()
        self._tool_dispatch_checkpoints: List[Any] = []
        # SOFTWARE-COMPACT-TELEMETRY: keep failure signatures across top-level
        # run() calls for this engine so repeated tool failures leave durable
        # audit evidence instead of being only an in-turn repetition guard.
        self._tool_failure_counts: Dict[Tuple[str, str], int] = {}
        self._tool_failure_class_counts: Dict[Tuple[str, str], int] = {}
        self._consecutive_tool_failures = 0
        # Long software tasks need a model-visible closure nudge before the
        # hard max_turns cap, otherwise the last state file can stay stale.
        self._turn_budget_warning_sent = False
        self._final_claim_guard_sent = False
        self._intent_drift_guard_sent = False
        self._s3_truncation_guard_sent = False
        self._s3_list_calls_this_run = 0
        # Preserve the original user request outside `self.messages` so exact
        # deliverables survive compaction/truncation and remain available to
        # max-turn/final-claim guards.
        self._run_requested_text = ""

    # ------------------------------------------------------------
    # Public entry: run(...)
    # ------------------------------------------------------------

    def run(
        self,
        user_message: str,
        system_prompt: str,
        tools: List[Any],
        plan_mode: bool = False,
        auto_compact_enabled: bool = True,
        output_fn: Callable[[str], None] = print,
        thinking_enabled: bool = False,
        thinking_budget: int = 4096,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        query_source: str = "user",
        prompt_cache_now: bool = False,
        ask_user_response_provider: Optional[Callable[[str], str]] = None,
    ) -> QueryResult:
        """Execute the agent loop until a stop condition is reached.

        See class docstring for the IN-SCOPE / OUT-OF-SCOPE list.
        """
        # R-tier R1 PHASE B iter-1 fix: wrap output_fn to swallow
        # UnicodeEncodeError on Windows cp1252 stdout. The agent emits
        # valid UTF-8 (e.g. âœ… U+2705 in summary blocks); a raw print()
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
        self._tool_denials_this_turn = 0
        # Block C â€” exec-limit gate (PS#7 fix) + repetition detector.
        # Counters live on the QueryEngine. Codex iter-1 finding #3:
        # unconditional reset at run() entry so counters DON'T leak
        # across run() calls (the v4 contract; sub-agent dispatch is
        # the only legitimate cross-run sharing path, handled via
        # parent_engine forwarding).
        self._exec_call_count = 0  # bash + python_exec only
        self._recent_tool_calls: list = []  # [(name, args_hash), ...]
        self._s3_list_calls_this_run = 0
        # Block F2 â€” fresh BudgetTracker per run() so continuation state
        # never leaks across user messages.
        self._budget_tracker = None
        self._run_requested_text = str(user_message or "")
        # Block M-1 (PORT_LOG #085) â€” Runnable QueryEngine.ts:238 verbatim:
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
        # Block M-2 (PORT_LOG #084) â€” capture the baseline structured-output
        # tool-call count at run-entry. Calls THIS run = current_count -
        # baseline. Initial count when the run starts may be non-zero if
        # messages were carried over from a previous run() (continued
        # session); the retry limit is per-run, not per-session.
        self._initial_structured_output_calls = (
            count_tool_calls(self.messages, self.synthetic_output_tool_name)
            if self.synthetic_output_tool_name else 0
        )

        # Block C+ â€” message rate limit (v4 :8731-8740). Lives on the
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

        had_prior_messages = bool(self.messages)

        # Append user turn (Bedrock requires alternation; merge into trailing
        # user if needed â€” matches v4 sagemaker_agent.py:8744).
        if self.messages and self.messages[-1].get("role") == "user":
            prev = self.messages[-1]
            prev_content = prev.get("content", "")
            if isinstance(prev_content, str):
                prev["content"] = prev_content + "\n\n" + user_message
            elif isinstance(prev_content, list):
                prev_content.append({"type": "text", "text": user_message})
            else:
                self.messages.append({"role": "user", "content": user_message, "is_meta": False})
        else:
            self.messages.append({"role": "user", "content": user_message, "is_meta": False})

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
        # Block G3 â€” coordinator-mode prompt augmentation. Default OFF.
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
                    # don't reset to bare `system_prompt + active_block` â€”
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
            except Exception as exc:  # noqa: BLE001 â€” skill machinery never raises into agent loop
                logging.warning("[skill-wiring] %s: %s", type(exc).__name__, exc)

        effective_system_prompt, tools, _cache_policy_warnings = (
            self._enforce_prompt_cache_invariants(
                effective_system_prompt,
                tools,
                allow_now=prompt_cache_now or not had_prior_messages,
            )
        )
        for _warning in _cache_policy_warnings:
            output_fn(f"[prompt-cache invariant] {_warning}")

        last_text = ""
        thinking_trace: List[str] = []
        stop_reason = ""
        turns_used = 0

        for turn in range(self.max_turns):
            hard_cap = self._max_budget_halt(output_fn)
            if hard_cap is not None:
                return hard_cap
            self._tool_denials_this_turn = 0
            # User-requested stop (Phase 11 wires this to the Stop button).
            if self.on_stop_check and self.on_stop_check():
                output_fn("[Stopped by user]")
                stop_reason = "user_stop"
                try:
                    from core.compactor import Compactor, TransitionReason
                    Compactor.set_transition_reason(TransitionReason.USER_ABORT.value)
                except Exception:
                    pass
                break

            # Block M-2 (PORT_LOG #084) â€” structured-output retry-limit
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

            # Budget gate â€” shared with sub-agents (Phase 9).
            if not self.budget.consume():
                used, total = self.budget.used(), self.budget.total()
                output_fn(
                    f"[Budget exhausted: {used}/{total} iterations used. "
                    "Adjust IterationBudget or start a new session.]"
                )
                stop_reason = "budget_exhausted"
                break

            # A-38: compact-boundary preservedSegment GC before building the
            # model-visible turn, while keeping the recent tail untouched.
            try:
                from core.compactor import Compactor, TransitionReason
                self.messages = Compactor.gc_compact_boundary_preserved_segments(
                    self.messages
                )
            except Exception:
                pass

            # Phase 7 wiring contract: per-turn deferral + discovery merge.
            visible_tools, deferred_names = apply_tool_search_deferral(
                tools, enabled=True,
            )
            if self._discovered_tool_names:
                # Promote previously-discovered tools from deferred â†’ visible.
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
            turn_messages = self._inject_s3_followup_reminder_if_needed(turn_messages)
            turn_messages = self._inject_artifact_reminder_if_needed(turn_messages)

            # Block A A-16: time-based microcompact BEFORE the next API call.
            # If the main loop has been idle long enough for the server-side
            # prompt cache to be cold, clear old compactable tool_result
            # bodies so the miss re-uploads less context.
            try:
                import time as _time
                from core.compactor import Compactor
                from runtime.config import CONFIG as _CFG_MC
                if (
                    auto_compact_enabled
                    and
                    self.agent_kind == "parent"
                    and self._last_api_call_time > 0
                    and Compactor.should_auto_compact(query_source)
                ):
                    threshold = float(
                        getattr(
                            _CFG_MC,
                            "cold_cache_threshold_seconds",
                            Compactor.COLD_CACHE_THRESHOLD_SECONDS,
                        )
                    )
                    now = _time.time()
                    if now - self._last_api_call_time > threshold:
                        gap_min = (now - self._last_api_call_time) / 60.0
                        self._audit_engine_event(
                            "compact_micro_start",
                            parameters={
                                "trigger": "cold_cache",
                                "gap_seconds": round(now - self._last_api_call_time, 3),
                                "threshold_seconds": threshold,
                                "keep_n": Compactor.KEEP_LAST_N_COLD_CACHE,
                            },
                            result_summary="microcompact started",
                        )
                        mc_messages, mc_saved = Compactor.microcompact(
                            self.messages,
                            keep_n_override=Compactor.KEEP_LAST_N_COLD_CACHE,
                        )
                        if mc_saved >= Compactor.MICROCOMPACT_MIN_SAVINGS:
                            self.messages = mc_messages
                            turn_messages = mc_messages
                            if deferred_names:
                                turn_messages = self._inject_deferred_reminder(
                                    turn_messages,
                                    deferred_names,
                                )
                            turn_messages = self._inject_s3_followup_reminder_if_needed(turn_messages)
                            turn_messages = self._inject_artifact_reminder_if_needed(turn_messages)
                            self._audit_engine_event(
                                "compact_micro_end",
                                parameters={
                                    "trigger": "cold_cache",
                                    "saved_count": mc_saved,
                                    "applied": True,
                                },
                                result_summary=f"microcompact freed {mc_saved} tokens",
                            )
                            output_fn(
                                f"[i] Cold cache detected ({gap_min:.0f}min gap) - "
                                f"proactive microcompact freed ~{mc_saved:,} tokens"
                            )
                        else:
                            self._audit_engine_event(
                                "compact_micro_end",
                                parameters={
                                    "trigger": "cold_cache",
                                    "saved_count": mc_saved,
                                    "applied": False,
                                },
                                result_summary=f"microcompact skipped; saved {mc_saved} tokens below threshold",
                            )
            except Exception:
                self._audit_engine_event(
                    "compact_micro_failed",
                    result_summary="microcompact raised before API call",
                )
                pass

            try:
                from core.compactor import Compactor
                tool_schema_tokens = Compactor.estimate_tool_schema_tokens(
                    _build_tools_api_payload(visible_tools)
                )
                if Compactor.would_exceed_context_limit(
                    turn_messages,
                    getattr(__import__("runtime.config", fromlist=["CONFIG"]).CONFIG, "context_max_tokens", 200_000),
                    tool_schema_tokens=tool_schema_tokens,
                ):
                    stop_reason = "context_overflow"
                    Compactor.set_transition_reason(
                        TransitionReason.CONTEXT_OVERFLOW_PRE_API.value
                    )
                    output_fn("[context_overflow: estimated prompt would exceed context limit before API call]")
                    return QueryResult(
                        text=last_text,
                        messages=list(self.messages),
                        stop_reason=stop_reason,
                        turns_used=turns_used,
                        budget_used=self.budget.used(),
                        thinking="\n\n".join(thinking_trace),
                        error="context_overflow: pre-api guard",
                    )
                turn_messages = Compactor.sanitize_messages_surrogates(turn_messages)
            except Exception:
                pass

            turn_messages = self._inject_turn_budget_warning_if_needed(
                turn_messages,
                turn_index=turn,
                output_fn=output_fn,
            )

            # Bedrock invocation.
            try:
                response = self._chat_with_fallback(
                    messages=turn_messages,
                    system=effective_system_prompt,
                    tools=_build_tools_api_payload(visible_tools),
                    max_tokens=max_tokens,
                    temperature=temperature,
                    thinking_enabled=thinking_enabled,
                    thinking_budget=thinking_budget,
                )
            except Exception as exc:  # noqa: BLE001 â€” classify and surface
                category, recovery, debug = ErrorClassifier.classify(exc)
                try:
                    from core.compactor import Compactor, TransitionReason
                    Compactor.set_transition_reason(TransitionReason.API_ERROR.value)
                except Exception:
                    pass
                output_fn(f"[error_during_execution][Bedrock {category}: {debug}]")
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
                    thinking="\n\n".join(thinking_trace),
                    error=f"{category}: {debug}",
                )

            try:
                import time as _time
                self._last_api_call_time = _time.time()
            except Exception:
                pass
            turns_used += 1
            response_thinking = getattr(response, "thinking", "") or ""
            if response_thinking:
                thinking_trace.append(response_thinking)
                try:
                    output_fn("[thinking]\n" + response_thinking)
                except Exception:
                    pass

            # Block B (PORT_LOG #039+#040): record token usage + per-agent
            # attribution. "parent" or sub-agent type-string. Best-effort â€”
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
                #   `[Cost ${session_cost} passed budget ${limit} â€” continuing.]`
                # NOT a hard halt â€” per user 2026-05-03 update to plan v3,
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
                            f"budget ${limit:.2f} â€” continuing.]"
                        )
                        self._warned_over_budget = True
            except Exception:
                pass

            # Append assistant turn (text + tool_use blocks, plus thinking).
            assistant_content = self._build_assistant_content(response)
            self.messages.append({
                "role": "assistant",
                "content": assistant_content,
                "is_meta": False,
            })
            self._notify_tool_generation(response)

            if response.text:
                last_text = response.text

            # Block A â€” auto-compact gate. Per-turn check: if the
            # message buffer has crossed the 80% threshold AND the
            # circuit breaker allows another attempt, run Compactor.
            try:
                from core.compactor import Compactor, AUTO_COMPACT
                from runtime.config import CONFIG as _CFG_AC
                _max_ctx = getattr(_CFG_AC, "context_max_tokens", 200_000)
                if (
                    auto_compact_enabled
                    and
                    Compactor.should_auto_compact(query_source)
                    and Compactor.should_compact(self.messages, _max_ctx)
                ):
                    _ok, _why = AUTO_COMPACT.try_attempt()
                    if _ok:
                        self._audit_engine_event(
                            "compact_auto_start",
                            parameters={
                                "trigger": "context_threshold",
                                "max_context_count": _max_ctx,
                                "messages": len(self.messages),
                            },
                            result_summary="auto compact started",
                        )
                        _result = Compactor.run(
                            self.client,
                            self.messages,
                            _max_ctx,
                            skill_manager=self.skill_manager,
                        )
                        if _result.success:
                            AUTO_COMPACT.record_success()
                            self._audit_engine_event(
                                "compact_auto_end",
                                parameters={
                                    "success": True,
                                    "before_count": _result.tokens_before,
                                    "after_count": _result.tokens_after,
                                    "saved_count": _result.tokens_before - _result.tokens_after,
                                },
                                result_summary=(
                                    f"auto compact saved "
                                    f"{_result.tokens_before - _result.tokens_after} tokens"
                                ),
                            )
                            output_fn(
                                f"[auto-compact] saved "
                                f"{_result.tokens_before - _result.tokens_after:,} "
                                f"tokens; continuing."
                            )
                            self.messages = _result.messages_after
                        else:
                            self._audit_engine_event(
                                "compact_failed",
                                parameters={
                                    "trigger": "context_threshold",
                                    "before_count": _result.tokens_before,
                                    "after_count": _result.tokens_after,
                                },
                                result_summary=_result.error or "auto compact failed",
                            )
                            _disabled, _reason = AUTO_COMPACT.record_failure()
                            if _disabled:
                                output_fn(f"[{_reason}]")
                    else:
                        self._audit_engine_event(
                            "compact_auto_skipped",
                            parameters={"trigger": "context_threshold", "reason": _why},
                            result_summary=_why,
                        )
                        # Cooldown / cap message - log once per turn, no
                        # spam since try_attempt returns reason text.
                        output_fn(f"[auto-compact skipped: {_why}]")
            except Exception:
                self._audit_engine_event("compact_failed", result_summary="auto compact raised")
                pass

            # Stop conditions: end_turn / no tool_use blocks â†’ final answer.
            if not response.tool_calls:
                # Block F2 â€” auto-continuation under iteration budget. Only
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
                    # surface a diagnostic when F2 is opt-in enabled â€” silent
                    # fail-closed makes opt-in users see "no auto-continue"
                    # with zero clue why. logging.warning matches the
                    # cost-runtime warning pattern at [Cost ...] above.
                    logging.warning(
                        "[budget-continuation] %s: %s",
                        type(_f2_exc).__name__, _f2_exc,
                    )

                stop_reason = "end_turn"
                try:
                    from core.compactor import Compactor, TransitionReason
                    Compactor.set_transition_reason(TransitionReason.END_TURN.value)
                except Exception:
                    pass
                guard = self._final_claim_guard_message(response.text or "")
                if guard:
                    output_fn("[final-claim guard: evidence is not ready; continuing]")
                    self.messages.append({
                        "role": "user",
                        "content": [{"type": "text", "text": guard}],
                        "is_meta": True,
                    })
                    continue
                guard = self._s3_truncation_guard_message(response.text or "")
                if guard:
                    output_fn("[truncation guard: S3 evidence is partial; continuing]")
                    self.messages.append({
                        "role": "user",
                        "content": [{"type": "text", "text": guard}],
                        "is_meta": True,
                    })
                    continue
                if response.text:
                    guard = self._intent_drift_guard_message(response.text)
                    if guard:
                        output_fn("[intent-drift guard: S3 inventory evidence is not ready; continuing]")
                        self.messages.append({
                            "role": "user",
                            "content": [{"type": "text", "text": guard}],
                            "is_meta": True,
                        })
                        continue
                    output_fn(response.text)
                break

            # Tool dispatch â€” emit one tool_result per tool_use call.
            tool_results: List[Dict[str, Any]] = []
            _dispatch_calls = list(response.tool_calls)
            try:
                from core.parallel_dispatch import (
                    execute_parallel_tool_calls,
                    partial_tool_call_warning,
                    pending_tool_use_ids,
                    plan_tool_dispatch,
                    synthetic_tool_result_stub,
                )
                self._partial_tool_names = set(pending_tool_use_ids(_dispatch_calls))
                _tools_by_name = {getattr(t, "name", ""): t for t in tools}
                _plan = plan_tool_dispatch(_dispatch_calls, _tools_by_name)
                for _dropped in _plan.get("dropped", []):
                    _tid = getattr(_dropped, "id", "") or (
                        _dropped.get("id") if isinstance(_dropped, dict) else ""
                    )
                    tool_results.append(
                        synthetic_tool_result_stub(str(_tid), reason="duplicate tool call")
                    )
                    self._partial_tool_names.discard(str(_tid))
                if (
                    len(_plan.get("parallel", [])) > 1
                    and not _plan.get("sequential")
                    and not plan_mode
                ):
                    import threading as _threading
                    _parallel_bookkeeping_lock = _threading.Lock()

                    def _execute_parallel_one(_call: Any) -> Dict[str, Any]:
                        return self._dispatch_single_tool_call(
                            _call,
                            tools=tools,
                            plan_mode=plan_mode,
                            output_fn=output_fn,
                            ask_user_response_provider=ask_user_response_provider,
                            bookkeeping_lock=_parallel_bookkeeping_lock,
                        )

                    _parallel_results = execute_parallel_tool_calls(
                        _plan["parallel"],
                        _execute_parallel_one,
                        checkpoint_callback=self._tool_dispatch_checkpoints.append,
                    )
                    tool_results.extend(_parallel_results)
                    for _block in _parallel_results:
                        self._partial_tool_names.discard(str(_block.get("tool_use_id", "")))
                    if self._partial_tool_names:
                        tool_results.extend(
                            partial_tool_call_warning(
                                sorted(self._partial_tool_names),
                                output_fn=output_fn,
                            )
                        )
                    self._partial_tool_names.clear()
                    tool_results = _persist_large_tool_results_for_message(
                        tool_results,
                        session_id=self.session_id,
                        per_tool_limit=max(
                            [getattr(t, "max_result_size_chars", 0) for t in tools]
                            or [0]
                        ),
                    )
                    tool_results = enforce_tool_result_message_budget(tool_results)
                    self.messages.append({"role": "user", "content": tool_results, "is_meta": False})
                    continue
                _dispatch_calls = _plan.get("parallel", []) + _plan.get("sequential", [])
            except Exception:
                _dispatch_calls = list(response.tool_calls)

            for call in _dispatch_calls:
                self._partial_tool_names.discard(str(call.id))
                tool_results.append(self._dispatch_single_tool_call(
                    call,
                    tools=tools,
                    plan_mode=plan_mode,
                    output_fn=output_fn,
                    ask_user_response_provider=ask_user_response_provider,
                ))

            # Append the tool_results as a user turn (Bedrock convention).
            if self._partial_tool_names:
                try:
                    from core.parallel_dispatch import partial_tool_call_warning
                    tool_results.extend(
                        partial_tool_call_warning(
                            sorted(self._partial_tool_names),
                            output_fn=output_fn,
                        )
                    )
                finally:
                    self._partial_tool_names.clear()
            tool_results = _persist_large_tool_results_for_message(
                tool_results,
                session_id=self.session_id,
                per_tool_limit=max(
                    [getattr(t, "max_result_size_chars", 0) for t in tools]
                    or [0]
                ),
            )
            tool_results = enforce_tool_result_message_budget(tool_results)
            self.messages.append({"role": "user", "content": tool_results, "is_meta": False})

        else:  # for-loop fell through without break
            stop_reason = "max_turns"
            output_fn(f"[Max turns reached: {self.max_turns}]")
            self._record_max_turn_resume_state(output_fn, turns_used=turns_used)

        return QueryResult(
            text=last_text,
            messages=list(self.messages),
            stop_reason=stop_reason or "end_turn",
            turns_used=turns_used,
            budget_used=self.budget.used(),
            thinking="\n\n".join(thinking_trace),
        )

    def _dispatch_single_tool_call(
        self,
        call: Any,
        *,
        tools: List[Any],
        plan_mode: bool,
        output_fn: Callable[[str], None],
        ask_user_response_provider: Optional[Callable[[str], str]] = None,
        bookkeeping_lock: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Dispatch one tool call through the canonical QueryEngine pipeline.

        Block N uses this same function for sequential dispatch and parallel
        safe calls so audit logging, repetition tracking, JSON repair, approval
        checks, tool_search discovery, and error forensics cannot drift between
        paths. `bookkeeping_lock` serializes shared engine counters when this
        function runs inside ThreadPoolExecutor workers.
        """
        from contextlib import nullcontext
        from tools.registry import PLAN_MODE_ALLOWED_TOOLS, find_tool_by_name
        from tools.tool_search import tool_search_discovered_names

        def _guard():
            return bookkeeping_lock if bookkeeping_lock is not None else nullcontext()

        def _audit_parameters(value: Any) -> Dict[str, Any]:
            return value if isinstance(value, dict) else {}

        tool = find_tool_by_name(tools, call.name)
        if tool is None:
            result = {
                "type": "tool_result",
                "tool_use_id": call.id,
                "content": f"error_during_execution: unknown tool '{call.name}'",
                "is_error": True,
            }
            try:
                from runtime.audit import AUDIT as _AUDIT
                _AUDIT.log(
                    session_id=self.session_id,
                    action="tool_unknown",
                    tool_name=call.name,
                    parameters=_audit_parameters(call.input),
                    result_summary=f"unknown tool '{call.name}'",
                    user_approved=False,
                )
            except Exception:
                pass
            return result

        if plan_mode and call.name not in PLAN_MODE_ALLOWED_TOOLS:
            result = {
                "type": "tool_result",
                "tool_use_id": call.id,
                "content": (
                    f"Error: tool '{call.name}' is not in "
                    "PLAN_MODE_ALLOWED_TOOLS; blocked in plan mode."
                ),
                "is_error": True,
            }
            try:
                from runtime.audit import AUDIT as _AUDIT
                _AUDIT.log(
                    session_id=self.session_id,
                    action="plan_mode_blocked",
                    tool_name=call.name,
                    parameters=_audit_parameters(call.input),
                    result_summary=f"plan-mode allowlist blocked '{call.name}'",
                    user_approved=False,
                )
            except Exception:
                pass
            return result

        _repaired_input = call.input
        if isinstance(call.input, str):
            try:
                from security.json_repair import repair_tool_call_arguments
                _repaired_input = repair_tool_call_arguments(call.input)
            except Exception:
                _repaired_input = {}

        if call.name == "aws_s3_list" and self._is_s3_followup_request(self._run_requested_text):
            with _guard():
                self._s3_list_calls_this_run += 1
                if self._s3_list_calls_this_run > 2:
                    return {
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": (
                            "Blocked: too many aws_s3_list calls this turn. "
                            "Reuse prior S3 results or ask for a narrower prefix."
                        ),
                        "is_error": True,
                    }

        if call.name in {"edit_file", "write_file"} and self._is_blocked_status_doc_update(call.name, _repaired_input):
            return {
                "type": "tool_result",
                "tool_use_id": call.id,
                "content": (
                    "Blocked: AGENT_STATUS.md updates are reserved for explicit "
                    "status/progress/handoff requests, long-running coding tasks, "
                    "or large project edits. This looks like a small read-only/report task."
                ),
                "is_error": True,
            }

        if call.name in {"bash", "python_exec"}:
            from runtime.config import CONFIG as _CFG
            cap = getattr(_CFG, "max_exec_calls_per_session", 200)
            with _guard():
                if self._exec_call_count >= cap:
                    return {
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
                    }

        import hashlib as _hashlib
        import json as _json
        try:
            _args_hash = _hashlib.sha256(
                _json.dumps(call.input or {}, sort_keys=True, default=str).encode()
            ).hexdigest()[:12]
        except Exception:
            _args_hash = ""
        _key = (call.name, _args_hash)
        with _guard():
            _recent = self._recent_tool_calls[-6:]
            if _recent.count(_key) >= 2:
                self._audit_engine_event(
                    "tool_failure_loop_blocked",
                    tool_name=call.name,
                    parameters={
                        "tool_name": call.name,
                        "args_hash": _args_hash,
                        "previous_failures": self._tool_failure_counts.get(_key, 0),
                        "repeated_recent_calls": _recent.count(_key),
                    },
                    result_summary="blocked third identical tool call",
                )
                return {
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
                }
            self._recent_tool_calls.append(_key)
            if len(self._recent_tool_calls) > 12:
                self._recent_tool_calls = self._recent_tool_calls[-12:]

        _failure_key = self._tool_failure_key(call.name, _repaired_input)
        _failure_count = self._tool_failure_counts.get(_failure_key, 0)
        if _failure_count >= 2:
            self._audit_engine_event(
                "tool_failure_loop_blocked",
                tool_name=call.name,
                parameters={
                    "tool_name": call.name,
                    "args_hash": _failure_key[1],
                    "previous_failures": _failure_count,
                },
                result_summary="blocked repeated failed tool call",
            )
            return {
                "type": "tool_result",
                "tool_use_id": call.id,
                "content": (
                    f"Blocked: previous identical call to '{call.name}' failed "
                    f"{_failure_count} times. Change approach, change arguments, "
                    "or ask the user before retrying."
                ),
                "is_error": True,
            }

        _predicted_failure_class = self._predict_guard_failure_class(call.name, _repaired_input)
        if _predicted_failure_class is not None:
            _class_key = (call.name, _predicted_failure_class)
            _class_count = self._tool_failure_class_counts.get(_class_key, 0)
            _should_block_class = _class_count >= 2
            if _predicted_failure_class == "bash_aws_s3_cli_blocked":
                _should_block_class = _class_count >= 1
            if _predicted_failure_class == "python_exec_error":
                _should_block_class = (
                    _should_block_class
                    and self._consecutive_tool_failures >= 2
                )
            if _should_block_class:
                self._audit_engine_event(
                    "tool_failure_loop_blocked",
                    tool_name=call.name,
                    parameters={
                        "tool_name": call.name,
                        "failure_class": _predicted_failure_class,
                        "previous_failures": _class_count,
                    },
                    result_summary="blocked repeated guard-class tool call",
                )
                return {
                    "type": "tool_result",
                    "tool_use_id": call.id,
                    "content": self._failure_class_block_message(
                        call.name,
                        _predicted_failure_class,
                        _class_count,
                    ),
                    "is_error": True,
                }

        from runtime.config import CONFIG as _CFG_AT
        _is_mock = bool(
            getattr(_CFG_AT, "mock_mode", False)
            or getattr(self.client, "mock_mode", False)
        )
        if (
            not _is_mock
            and getattr(_CFG_AT, "require_tool_approval", False)
            and getattr(tool, "requires_approval", False)
        ):
            if not hasattr(_CFG_AT, "_always_allowed"):
                _CFG_AT._always_allowed = {}
            if not _CFG_AT._always_allowed.get(call.name):
                try:
                    from ui.approval_dialog import PermissionDialog
                    _model_reason = ""
                    if isinstance(_repaired_input, dict):
                        _model_reason = str(_repaired_input.get("reason", ""))
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
                            else:
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
                        self._record_tool_denial(
                            call.name,
                            _result.reason,
                            output_fn,
                        )
                        return {
                            "type": "tool_result",
                            "tool_use_id": call.id,
                            "content": (
                                f"User denied approval for "
                                f"`{call.name}`: {_result.reason}"
                            ),
                            "is_error": True,
                        }
                except Exception as _approval_exc:
                    logging.warning(
                        f"approval gate failed: {_approval_exc}; defaulting to deny"
                    )
                    self._record_tool_denial(
                        call.name,
                        f"approval gate error: {_approval_exc}",
                        output_fn,
                    )
                    return {
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": (
                            f"Approval gate error for `{call.name}`; "
                            f"defaulting to deny."
                        ),
                        "is_error": True,
                    }

        try:
            if call.name in {"bash", "python_exec"}:
                with _guard():
                    self._exec_call_count += 1
            raw = tool.execute(_repaired_input, context={
                "active_tools": tools,
                "plan_mode": plan_mode,
                "parent_engine": self,
                "parent_depth": getattr(self, "_subagent_depth", 0),
                "skill_manager": self.skill_manager,
                "session_id": self.session_id,
                "abort_events": self.abort_events,
                "output_fn": output_fn,
                "ask_user_response_provider": ask_user_response_provider,
                "ascii_only": self._requests_ascii_only(self._run_requested_text),
                "tool_name": call.name,
            })
            text = _coerce_tool_result_to_text(raw)
            self._notify_tool_result(call, text, is_error=False)
            try:
                from runtime.audit import AUDIT as _AUDIT
                _AUDIT.log(
                    session_id=self.session_id,
                    action="tool_dispatch",
                    tool_name=call.name,
                    parameters=_audit_parameters(_repaired_input),
                    result_summary=text[:500] if isinstance(text, str) else "",
                    user_approved=True,
                )
            except Exception:
                pass
            if self._looks_like_tool_failure(text):
                self._record_tool_failure(call.name, _failure_key, text)
            else:
                self._record_tool_success()
            if call.name == "tool_search":
                discovered = tool_search_discovered_names(text)
                if discovered:
                    with _guard():
                        self._discovered_tool_names.update(discovered)
            return {
                "type": "tool_result",
                "tool_use_id": call.id,
                "_sageagent_tool_name": call.name,
                "_sageagent_max_result_chars": tool.max_result_size_chars,
                "content": text,
            }
        except Exception as exc:  # noqa: BLE001 - surface to model
            logging.warning(
                "[query_engine] tool '%s' raised %s: %s",
                call.name, type(exc).__name__, exc,
            )
            try:
                from runtime.audit import AUDIT as _AUDIT
                _AUDIT.log(
                    session_id=self.session_id,
                    action="tool_error",
                    tool_name=call.name,
                    parameters=_audit_parameters(_repaired_input),
                    result_summary=f"{type(exc).__name__}: {exc}",
                    user_approved=False,
                )
            except Exception:
                pass
            self._record_tool_failure(
                call.name,
                _failure_key,
                f"{type(exc).__name__}: {exc}",
            )
            self._notify_tool_result(
                call,
                f"error_during_execution: {type(exc).__name__}: {exc}",
                is_error=True,
            )
            return {
                "type": "tool_result",
                "tool_use_id": call.id,
                "content": f"error_during_execution: {type(exc).__name__}: {exc}",
                "is_error": True,
            }

    # ------------------------------------------------------------
    # Internal: E+F runtime event surfaces
    # ------------------------------------------------------------

    def _emit_status(
        self,
        event_type: str,
        message: str,
        *,
        output_fn: Optional[Callable[[str], None]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        event = {
            "type": event_type,
            "message": message,
            "session_id": self.session_id,
            "agent_kind": self.agent_kind,
            "metadata": metadata or {},
        }
        if self.status_callback is not None:
            try:
                self.status_callback(event)
            except Exception as exc:  # noqa: BLE001 - callbacks are best-effort UI hooks
                logging.warning(
                    "[status-callback] %s: %s",
                    type(exc).__name__, exc,
                )
        if output_fn is not None and event_type == "warning":
            output_fn(f"[warning] {message}")

    def _audit_engine_event(
        self,
        action: str,
        *,
        tool_name: str = "(engine)",
        parameters: Optional[Dict[str, Any]] = None,
        result_summary: str = "",
        user_approved: bool = False,
    ) -> None:
        """Best-effort typed audit helper used by telemetry hardening."""
        try:
            from runtime.audit import AUDIT as _AUDIT
            _AUDIT.log(
                session_id=self.session_id,
                action=action,
                tool_name=tool_name,
                parameters=parameters or {},
                result_summary=result_summary,
                user_approved=user_approved,
            )
        except Exception:
            pass

    @staticmethod
    def _tool_failure_key(tool_name: str, args: Any) -> Tuple[str, str]:
        try:
            canonical = json.dumps(args or {}, sort_keys=True, default=str)
        except Exception:
            canonical = repr(args)
        return (
            str(tool_name or "unknown"),
            hashlib.sha256(canonical.encode("utf-8", errors="replace")).hexdigest()[:12],
        )

    @staticmethod
    def _looks_like_tool_failure(text: str) -> bool:
        t = (text or "").strip().lower()
        return t.startswith((
            "error:",
            "error_during_execution:",
            "blocked:",
            "approval gate error",
            "user denied approval",
        )) or " timed out after " in t or (
            "[exit code:" in t and "[exit code: 0]" not in t
        )

    @staticmethod
    def _failure_class(tool_name: str, text: str) -> Optional[str]:
        t = (text or "").lower()
        if tool_name == "edit_file" and "must read file before editing" in t:
            return "read_before_edit"
        if tool_name == "write_file" and "must read file before overwriting" in t:
            return "read_before_write"
        if tool_name == "bash" and "command not allowed: 'cd'" in t:
            return "bash_cd_blocked"
        if tool_name == "bash" and "aws s3 cli is blocked by the bash allowlist" in t:
            return "bash_aws_s3_cli_blocked"
        if tool_name == "python_exec" and (
            "syntaxerror" in t
            or "unicodeencodeerror" in t
            or "error_during_execution" in t
        ):
            return "python_exec_error"
        return None

    @staticmethod
    def _failure_class_block_message(
        tool_name: str,
        failure_class: str,
        previous_failures: int,
    ) -> str:
        hints = {
            "read_before_edit": (
                "read_file has not established a readable current-state marker "
                "for this target. Stop retrying edit_file; call read_file on the "
                "exact target path and then retry one edit, or use a different "
                "documented strategy."
            ),
            "read_before_write": (
                "write_file is trying to overwrite an existing file without a "
                "current read marker. Stop retrying write_file; call read_file "
                "on the exact target path, use append for append-only work, or "
                "switch strategy."
            ),
            "bash_cd_blocked": (
                "cd is not allowed in bash. Stop retrying cd variants; run the "
                "allowed command directly from the current workspace or use the "
                "dedicated file tools."
            ),
            "bash_aws_s3_cli_blocked": (
                "aws s3/aws s3api is blocked in bash. Stop retrying the CLI; "
                "use the read-only aws_s3_list tool for S3 bucket/prefix "
                "inventory, or report the exact AWS credential/permission blocker."
            ),
            "python_exec_error": (
                "python_exec has failed repeatedly. Stop retrying near-identical "
                "scripts; simplify the script, remove non-ASCII/path escaping "
                "hazards, or use file tools instead."
            ),
        }
        return (
            f"Blocked: '{tool_name}' has already hit {previous_failures} "
            f"{failure_class} failures. {hints.get(failure_class, 'Change strategy before retrying.')}"
        )

    @staticmethod
    def _predict_guard_failure_class(tool_name: str, args: Any) -> Optional[str]:
        if not isinstance(args, dict):
            return None
        if tool_name == "python_exec":
            return "python_exec_error"
        if tool_name == "bash":
            command = str(args.get("command", "")).strip().lower()
            if re.search(r"\baws\s+s3(?:api)?\b", command):
                return "bash_aws_s3_cli_blocked"
            if command == "cd" or command.startswith("cd ") or "&& cd " in command or command.startswith("cd\t"):
                return "bash_cd_blocked"
            return None
        if tool_name not in {"edit_file", "write_file"}:
            return None
        if tool_name == "write_file" and args.get("mode", "write") != "write":
            return None
        file_path = args.get("file_path")
        if not isinstance(file_path, str) or not file_path:
            return None
        try:
            import os as _os
            from tools import _file_read_tracking as _read_tracking
            from tools import _path_validation as _path_security
            ok, _msg = _path_security.validate_path(file_path)
            if not ok:
                return None
            abs_path = _os.path.abspath(_path_security.resolve_path(file_path))
            if tool_name == "edit_file":
                if _os.path.isfile(abs_path) and not _read_tracking.was_read(abs_path):
                    return "read_before_edit"
            elif _os.path.exists(abs_path) and not _read_tracking.was_read(abs_path):
                return "read_before_write"
        except Exception:
            return None
        return None

    def _record_tool_success(self) -> None:
        self._consecutive_tool_failures = 0

    def _record_tool_failure(
        self,
        tool_name: str,
        failure_key: Tuple[str, str],
        result_summary: str,
    ) -> None:
        count = self._tool_failure_counts.get(failure_key, 0) + 1
        self._tool_failure_counts[failure_key] = count
        failure_class = self._failure_class(tool_name, result_summary)
        class_count = None
        if failure_class is not None:
            class_key = (tool_name, failure_class)
            class_count = self._tool_failure_class_counts.get(class_key, 0) + 1
            self._tool_failure_class_counts[class_key] = class_count
        self._consecutive_tool_failures += 1
        self._audit_engine_event(
            "tool_failure_recorded",
            tool_name=tool_name,
            parameters={
                "tool_name": tool_name,
                "args_hash": failure_key[1],
                "failure_count": count,
                "failure_class": failure_class,
                "failure_class_count": class_count,
                "consecutive_failures": self._consecutive_tool_failures,
            },
            result_summary=str(result_summary)[:500],
        )
        if self._consecutive_tool_failures >= 5:
            self._audit_engine_event(
                "tool_failure_loop_warning",
                tool_name=tool_name,
                parameters={"consecutive_failures": self._consecutive_tool_failures},
                result_summary="five consecutive tool failures observed",
            )

    def _emit_warning(
        self,
        message: str,
        *,
        output_fn: Optional[Callable[[str], None]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._emit_status(
            "warning",
            message,
            output_fn=output_fn,
            metadata=metadata,
        )

    def _record_tool_denial(
        self,
        tool_name: str,
        reason: str,
        output_fn: Callable[[str], None],
    ) -> None:
        self._tool_denials_this_turn += 1
        count = self._tool_denials_this_turn
        if count >= 3:
            self._emit_warning(
                f"{count} tool denials this turn",
                output_fn=output_fn,
                metadata={"tool_name": tool_name, "reason": reason, "count": count},
            )
        else:
            self._emit_status(
                "tool_denial",
                f"{count} tool denial{'s' if count != 1 else ''} this turn",
                metadata={"tool_name": tool_name, "reason": reason, "count": count},
            )

    def _max_budget_halt(
        self,
        output_fn: Callable[[str], None],
    ) -> Optional[QueryResult]:
        try:
            from runtime.config import CONFIG as _CFG
            from runtime.tokens import TOKENS as _TOKENS
            limit = float(
                getattr(_CFG, "max_budget_usd", 0.0)
                or getattr(_CFG, "maxBudgetUsd", 0.0)
                or 0.0
            )
            cost = float(getattr(_TOKENS, "session_cost", 0.0) or 0.0)
        except Exception:
            return None
        if limit <= 0 or cost < limit:
            return None
        message = f"maxBudgetUsd hard cap reached: ${cost:.4f} >= ${limit:.4f}"
        self._emit_warning(
            message,
            output_fn=output_fn,
            metadata={"session_cost": cost, "max_budget_usd": limit},
        )
        return QueryResult(
            text=message,
            messages=list(self.messages),
            stop_reason="cost_cap",
            turns_used=0,
            budget_used=self.budget.used(),
            error=message,
        )

    def _chat_with_fallback(self, **kwargs: Any) -> Any:
        if isinstance(kwargs.get("messages"), list):
            kwargs = dict(kwargs)
            kwargs["messages"] = _repair_messages_for_bedrock(kwargs["messages"])
        try:
            return self.client.chat(**kwargs)
        except FallbackTriggeredError as exc:
            if getattr(self.client, "model_id", None) is not None:
                try:
                    self.client.model_id = exc.target_model_id
                except Exception:
                    pass
            retry_kwargs = dict(kwargs)
            retry_kwargs["messages"] = strip_signature_blocks(
                retry_kwargs.get("messages", [])
            )
            retry_kwargs["messages"] = _repair_messages_for_bedrock(
                retry_kwargs["messages"]
            )
            return self.client.chat(**retry_kwargs)

    def _notify_tool_generation(self, response: Any) -> None:
        if self.tool_gen_callback is None:
            return
        calls = getattr(response, "tool_calls", None) or []
        if not calls:
            return
        for call in calls:
            event = {
                "type": "tool_generation",
                "tool_use_id": getattr(call, "id", ""),
                "name": getattr(call, "name", ""),
                "input": getattr(call, "input", {}) or {},
            }
            try:
                self.tool_gen_callback(event)
            except Exception as exc:  # noqa: BLE001 - callbacks are best-effort UI hooks
                logging.warning(
                    "[tool-gen-callback] %s: %s",
                    type(exc).__name__, exc,
                )

    def _notify_tool_result(self, call: Any, text: str, *, is_error: bool) -> None:
        if self.tool_gen_callback is None:
            return
        event = {
            "type": "tool_result",
            "tool_use_id": getattr(call, "id", ""),
            "name": getattr(call, "name", ""),
            "content": text,
            "is_error": bool(is_error),
        }
        try:
            self.tool_gen_callback(event)
        except Exception as exc:  # noqa: BLE001 - callbacks are best-effort UI hooks
            logging.warning(
                "[tool-result-callback] %s: %s",
                type(exc).__name__, exc,
            )

    # ------------------------------------------------------------
    # Internal: A-33 prompt-cache invariant policy
    # ------------------------------------------------------------

    def _enforce_prompt_cache_invariants(
        self,
        system_prompt: str,
        tools: List[Any],
        allow_now: bool = False,
    ) -> Tuple[str, List[Any], List[str]]:
        """Freeze model/system/toolset for an active prompt-cache session.

        Tool/model/system changes are deferred unless `allow_now` is explicit.
        This preserves the cache-prefix invariant across continued sessions.
        """
        model_id = str(getattr(self.client, "model_id", ""))
        prompt_hash = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()
        tool_names = tuple(t.name for t in tools)
        current = PromptCacheInvariantState(
            model_id=model_id,
            system_prompt_hash=prompt_hash,
            tool_names=tool_names,
        )
        if self._prompt_cache_state is None or allow_now:
            self._prompt_cache_state = current
            self._frozen_system_prompt = system_prompt
            self._frozen_tool_names = tool_names
            return system_prompt, tools, []

        warnings: List[str] = []
        frozen_prompt = self._frozen_system_prompt or system_prompt
        frozen_tools = list(tools)
        if current.model_id != self._prompt_cache_state.model_id:
            warnings.append("model change deferred until next session")
        if current.system_prompt_hash != self._prompt_cache_state.system_prompt_hash:
            warnings.append("system prompt change deferred until next session")
            frozen_prompt = self._frozen_system_prompt or system_prompt
        if current.tool_names != self._prompt_cache_state.tool_names:
            warnings.append("toolset change deferred until next session")
            frozen = set(self._frozen_tool_names)
            frozen_tools = [t for t in tools if t.name in frozen]
        return frozen_prompt, frozen_tools, warnings

    # ------------------------------------------------------------
    # Internal: assemble assistant turn content from a Bedrock Response
    # ------------------------------------------------------------

    @staticmethod
    def _build_assistant_content(response: Any) -> List[Dict[str, Any]]:
        """Construct a Bedrock-shaped assistant content list from a Response.

        Order: signed thinking blocks (if any) â†’ text â†’ tool_use. Bedrock
        requires model-supplied signatures for replayed thinking blocks, so v5
        never synthesizes a thinking block from display-only thinking text.
        """
        blocks: List[Dict[str, Any]] = []
        for thinking_block in getattr(response, "thinking_blocks", []) or []:
            if isinstance(thinking_block, dict) and thinking_block.get("signature"):
                blocks.append(dict(thinking_block))
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
        user turn â€” it does not mutate `self.messages`, so it does not leak
        into subsequent turns once the model has loaded the schemas it needs.
        """
        if not deferred_names:
            return messages
        reminder_body = (
            "The following deferred tools are available via tool_search. Their schemas "
            "are NOT loaded â€” calling them directly will fail. Use tool_search with "
            "query \"select:<name>[,<name>...]\" to load tool schemas before calling them:\n"
            + "\n".join(sorted(deferred_names))
        )
        reminder = xml_tag(XML_SYSTEM_REMINDER_TAG, reminder_body)
        # Transient append: copy the trailing user message and add the reminder
        # as an extra text block. If the trailing turn is not user-role, we
        # append a fresh user message â€” but this should never happen because
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

    def _inject_turn_budget_warning_if_needed(
        self,
        messages: List[Dict[str, Any]],
        *,
        turn_index: int,
        output_fn: Callable[[str], None],
    ) -> List[Dict[str, Any]]:
        """Transiently nudge long-running parent tasks to close or checkpoint.

        This does not mutate `self.messages`. It only affects the next model
        request once the run is near the hard max_turns cap.
        """
        if self._turn_budget_warning_sent:
            return messages
        if self.agent_kind != "parent":
            return messages
        warning_window = max(1, min(15, max(5, self.max_turns // 6)))
        turns_remaining = self.max_turns - turn_index
        if turns_remaining > warning_window:
            return messages

        self._turn_budget_warning_sent = True
        missing_paths = self._missing_requested_paths(
            self._requested_user_text(),
            self._current_workspace(),
        )
        body = (
            f"Turn budget warning: {turns_remaining} of {self.max_turns} turns remain. "
            "Prioritize closure over optional work. If deliverables are complete, "
            "update AGENT_STATUS.md, run the smallest useful verification, and give "
            "the final SPEC vs SHIPPED/evidence summary now. If deliverables are not "
            "complete, update AGENT_STATUS.md with exact remaining work and say "
            "NOT_DONE instead of continuing broad implementation."
        )
        if missing_paths:
            shown = ", ".join(missing_paths[:12])
            if len(missing_paths) > 12:
                shown += f", ... ({len(missing_paths)} total)"
            body += (
                "\nExact required paths still missing from the current workspace: "
                f"{shown}. Create or explicitly escalate these before any final claim."
            )
        zip_problems = self._requested_zip_artifact_problems(
            self._requested_user_text(),
            self._current_workspace(),
        )
        if zip_problems:
            body += (
                "\nExact ZIP artifact is not ready: "
                + "; ".join(zip_problems[:3])
                + ". Stop optional work and create/recreate it now with Python "
                "`zipfile`; then validate it with "
                "`ZipFile(...).testzip()` and save the validation log."
            )
        try:
            output_fn(f"[Turn budget warning: {turns_remaining} turns remaining]")
        except Exception:
            pass
        return self._append_transient_text_reminder(messages, body)

    @staticmethod
    def _append_transient_text_reminder(
        messages: List[Dict[str, Any]],
        body: str,
    ) -> List[Dict[str, Any]]:
        reminder = xml_tag(XML_SYSTEM_REMINDER_TAG, body)
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

    def _record_max_turn_resume_state(
        self,
        output_fn: Callable[[str], None],
        *,
        turns_used: int,
    ) -> None:
        """Best-effort AGENT_STATUS.md append when max_turns interrupts a run."""
        try:
            from runtime.config import CONFIG
            enable_status = getattr(CONFIG, "enable_status_doc", True)
            status_name = getattr(CONFIG, "status_doc", "AGENT_STATUS.md") or "AGENT_STATUS.md"
        except Exception:
            return
        if not enable_status:
            return
        workspace = self._current_workspace()
        status_path = os.path.join(workspace, status_name)
        try:
            os.makedirs(os.path.dirname(status_path) or ".", exist_ok=True)
            existing = ""
            if os.path.exists(status_path):
                with open(status_path, "r", encoding="utf-8") as handle:
                    existing = handle.read()
            marker = "<!-- SAGEAGENT_MAX_TURNS_RESUME_STATE -->"
            prior = existing.split(marker, 1)[0].rstrip()
            stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            missing_paths = self._missing_requested_paths(
                self._requested_user_text(),
                workspace,
            )
            missing_line = ""
            if missing_paths:
                shown = ", ".join(missing_paths[:20])
                if len(missing_paths) > 20:
                    shown += f", ... ({len(missing_paths)} total)"
                missing_line = f"- Missing exact required paths at interruption: {shown}\n"
            section = (
                f"\n\n{marker}\n"
                "## SageAgent Resume State\n\n"
                f"- Updated: {stamp}\n"
                "- Stop reason: max_turns\n"
                f"- Turns used in interrupted run: {turns_used} / {self.max_turns}\n"
                "- Completion claim: NOT_DONE until the next run verifies deliverables.\n"
                f"{missing_line}"
                "- Next action: read this file, inspect recent artifacts/logs, run the "
                "smallest relevant verification, then either finish or update this "
                "section with remaining work.\n"
            )
            with open(status_path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write((prior + section).lstrip())
            try:
                output_fn(f"[AGENT_STATUS.md updated for max_turns resume: {status_path}]")
            except Exception:
                pass
        except Exception as exc:
            try:
                output_fn(f"[AGENT_STATUS.md max_turns resume update failed: {exc}]")
            except Exception:
                pass

    def _final_claim_guard_message(self, text: str) -> str:
        """Return a correction reminder when a final success claim contradicts files."""
        if self._final_claim_guard_sent:
            return ""
        lower = (text or "").lower()
        claim_words = (
            "complete", "production-ready", "ready for production",
            "successfully built", "all tests pass", "all tests passing",
            "project complete",
        )
        if not any(word in lower for word in claim_words):
            return ""
        problems: List[str] = []
        try:
            from runtime.config import CONFIG
            status_name = getattr(CONFIG, "status_doc", "AGENT_STATUS.md") or "AGENT_STATUS.md"
        except Exception:
            status_name = "AGENT_STATUS.md"
        workspace = self._current_workspace()

        def _read_rel(rel: str) -> str:
            try:
                path = os.path.join(workspace, rel)
                if os.path.isfile(path):
                    with open(path, "r", encoding="utf-8", errors="replace") as handle:
                        return handle.read(120_000)
            except Exception:
                return ""
            return ""

        status_text = _read_rel(status_name)
        status_lower = status_text.lower()
        stale_markers = (
            "in_progress", "pending", "not_done", "failed", "1 failed",
            "tests failed", "packaging (pending)", "review (pending)",
        )
        if status_lower and any(marker in status_lower for marker in stale_markers):
            problems.append(f"{status_name} still contains pending/failed/not_done state")
        if status_lower and re.search(r"(?m)^\s*[-*]\s+\[\s\]", status_text):
            problems.append(f"{status_name} still contains unchecked checklist items")

        for rel in ("docs/TEST_REPORT.md", "TEST_REPORT.md"):
            report = _read_rel(rel)
            report_lower = report.lower()
            if report_lower and (
                re.search(r"\b[1-9]\d*\s+failed\b", report_lower)
                or re.search(r"\bfailed:\s*[1-9]\d*\b", report_lower)
                or "98.75%" in report_lower
                or "79/80" in report_lower
            ):
                problems.append(f"{rel} reports failing or partial tests")

        requested = self._requested_user_text()
        for missing in self._missing_requested_paths(requested, workspace):
            problems.append(f"required path missing: {missing}")
        for match in sorted(set(re.findall(r"([A-Za-z0-9_.\\/\-+]+\.zip)\b", requested))):
            candidate = match.replace("\\", os.sep).replace("/", os.sep)
            if os.path.isabs(candidate):
                exists = os.path.isfile(candidate)
                shown = candidate
            else:
                exists = os.path.isfile(os.path.join(workspace, candidate))
                shown = match
            if not exists:
                problems.append(f"required zip missing: {shown}")
        for zip_problem in self._requested_zip_artifact_problems(requested, workspace):
            problems.append(zip_problem)

        pytest_problem = self._final_claim_pytest_problem(lower, workspace)
        if pytest_problem:
            problems.append(pytest_problem)

        if not problems:
            return ""
        self._final_claim_guard_sent = True
        body = (
            "Final-claim guard: do not claim completion yet. Evidence conflicts with "
            "your final answer:\n- " + "\n- ".join(problems) +
            "\nFix the issue, rerun the smallest relevant verification, update "
            "AGENT_STATUS.md/docs, and only then provide the final SPEC vs SHIPPED "
            "summary. If you cannot fix it, answer NOT_DONE with exact blockers."
        )
        return xml_tag(XML_SYSTEM_REMINDER_TAG, body)

    def _intent_drift_guard_message(self, text: str) -> str:
        """Keep S3 inventory answers from drifting into local workspace inventory."""
        if self._intent_drift_guard_sent:
            return ""
        requested = self._requested_user_text()
        if not self._is_s3_inventory_request(requested):
            return ""

        final_lower = (text or "").lower()
        if not final_lower:
            return ""
        if self._final_text_has_s3_answer_or_blocker(final_lower):
            return ""

        local_signals = (
            "compact_v5",
            "agent.py",
            "core/",
            "tools/",
            "ui/",
            "repository",
            "source tree",
            "workspace",
            "local file",
        )
        if not any(signal in final_lower for signal in local_signals):
            return ""

        self._intent_drift_guard_sent = True
        body = (
            "Intent-drift guard: the user asked for S3 bucket/file structure, "
            "but the draft answer appears to describe the local workspace or "
            "compact_v5 source tree instead. Do not substitute repository "
            "inventory for S3 inventory. Use the read-only `aws_s3_list` tool "
            "for bucket/prefix inventory when allowed, or clearly report the "
            "actual blocker (for example Bedrock-only, bash allowlist, approval, "
            "AWS credentials, or AWS permissions) and stop."
        )
        return xml_tag(XML_SYSTEM_REMINDER_TAG, body)

    def _inject_s3_followup_reminder_if_needed(
        self,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Anchor S3 follow-ups to prior results instead of re-scanning buckets."""
        requested = getattr(self, "_run_requested_text", "") or ""
        if not self._is_s3_followup_request(requested):
            return messages
        paths = self._recent_s3_object_paths(limit=24)
        if not paths:
            return messages
        shown = "\n".join(f"- {p}" for p in paths[:12])
        more = "" if len(paths) <= 12 else f"\n- ... {len(paths) - 12} more recent object paths"
        body = (
            "S3 follow-up guard: the user is referring to recently listed S3 "
            "files. Reuse the known object paths below before calling "
            "`aws_s3_list` again. For inspecting file contents, pick at most the "
            "requested number of files and use `aws_s3_preview`. Do not refresh "
            "all buckets unless the user explicitly asks for a fresh full scan.\n"
            f"{shown}{more}"
        )
        return self._append_transient_text_reminder(messages, body)

    def _inject_artifact_reminder_if_needed(
        self,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Answer artifact-location follow-ups from durable artifact state."""
        requested = (getattr(self, "_run_requested_text", "") or "").lower()
        if not any(
            phrase in requested
            for phrase in (
                "where is the file",
                "where is file",
                "cannot find",
                "can't find",
                "file location",
                "saved where",
                "where did you save",
            )
        ):
            return messages
        try:
            from tools.artifacts import recent_artifacts
            artifacts = recent_artifacts(limit=8)
        except Exception:
            artifacts = []
        if not artifacts:
            return messages
        lines = []
        for item in artifacts[:8]:
            path = item.get("path") if isinstance(item, dict) else ""
            source = item.get("source_tool", "") if isinstance(item, dict) else ""
            if path:
                suffix = f" ({source})" if source else ""
                lines.append(f"- {path}{suffix}")
        if not lines:
            return messages
        body = (
            "Artifact-location guard: answer file-location questions from these "
            "recorded artifacts first. Do not search the filesystem unless the "
            "artifact list is insufficient.\n" + "\n".join(lines)
        )
        return self._append_transient_text_reminder(messages, body)

    def _s3_truncation_guard_message(self, text: str) -> str:
        """Prevent complete/all claims when recent S3 evidence was truncated."""
        if self._s3_truncation_guard_sent:
            return ""
        if not self._recent_s3_truncation_seen():
            return ""
        lowered = (text or "").lower()
        complete_claims = (
            "complete",
            "fully mapped",
            "all files",
            "all buckets",
            "all s3",
            "entire",
            "everything",
        )
        partial_qualifiers = (
            "partial",
            "truncated",
            "first-level",
            "sample",
            "preview",
            "continuation_token",
            "narrower prefix",
        )
        if not any(term in lowered for term in complete_claims):
            return ""
        if any(term in lowered for term in partial_qualifiers):
            return ""
        self._s3_truncation_guard_sent = True
        body = (
            "S3 truncation guard: recent `aws_s3_list` output was truncated or "
            "included a continuation token. Do not claim a complete S3/file "
            "inventory. Either continue with a narrower prefix/continuation token "
            "or clearly label the answer as a partial first-level/sample view."
        )
        return xml_tag(XML_SYSTEM_REMINDER_TAG, body)

    def _recent_s3_truncation_seen(self) -> bool:
        for msg in reversed(self.messages[-16:]):
            content = msg.get("content") if isinstance(msg, dict) else None
            text_parts: List[str] = []
            if isinstance(content, str):
                text_parts.append(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        text_parts.append(str(block.get("content") or block.get("text") or ""))
            joined = "\n".join(text_parts).lower()
            if "aws_s3_list" in joined or "s3://" in joined or "s3 structure" in joined:
                if "output truncated" in joined or "continuation_token" in joined:
                    return True
        return False

    def _recent_s3_object_paths(self, limit: int = 20) -> List[str]:
        """Extract recent concrete S3 object paths from conversation history."""
        seen: Set[str] = set()
        paths: List[str] = []
        pattern = re.compile(r"s3://([A-Za-z0-9.\-_]+)/([^\s\]\)>,\"']+)")
        for msg in reversed(self.messages[-24:]):
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")
            chunks: List[str] = []
            if isinstance(content, str):
                chunks.append(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        chunks.append(str(block.get("content") or block.get("text") or ""))
            for text in chunks:
                for match in pattern.finditer(text):
                    bucket = match.group(1)
                    key = match.group(2).strip().rstrip(".,;:")
                    if not key or key.endswith("/"):
                        continue
                    uri = f"s3://{bucket}/{key}"
                    if uri not in seen:
                        seen.add(uri)
                        paths.append(uri)
                    if len(paths) >= limit:
                        return paths
        return paths

    @staticmethod
    def _is_s3_followup_request(text: str) -> bool:
        lowered = (text or "").lower()
        if not lowered:
            return False
        if "s3" in lowered and any(
            term in lowered
            for term in (
                "pick",
                "choose",
                "investigate",
                "inspect",
                "sample",
                "preview",
                "open",
                "read",
                "relationship",
                "where is the file",
            )
        ):
            return True
        return (
            any(phrase in lowered for phrase in ("pick two", "pick 2", "choose two", "choose 2"))
            and any(term in lowered for term in ("file", "files", "object", "objects", "investigate", "inspect"))
        )

    @staticmethod
    def _requests_ascii_only(text: str) -> bool:
        lowered = (text or "").lower()
        return "ascii" in lowered or "plain text diagram" in lowered

    def _is_blocked_status_doc_update(self, tool_name: str, args: Any) -> bool:
        if not isinstance(args, dict):
            return False
        path = str(args.get("file_path") or args.get("filepath") or "")
        if not path:
            return False
        if os.path.basename(path).lower() != "agent_status.md":
            return False
        requested = (getattr(self, "_run_requested_text", "") or "").lower()
        explicit_status = (
            "agent_status" in requested
            or "status doc" in requested
            or "update status" in requested
            or "keep status" in requested
            or "handoff" in requested
            or "document" in requested and "status" in requested
        )
        if explicit_status:
            return False
        return self._is_s3_inventory_request(requested) or self._is_s3_followup_request(requested)

    @staticmethod
    def _is_s3_inventory_request(text: str) -> bool:
        lowered = (text or "").lower()
        if "s3" not in lowered:
            return False
        inventory_terms = (
            "list",
            "inventory",
            "structure",
            "bucket",
            "buckets",
            "prefix",
            "prefixes",
            "files",
            "objects",
        )
        return any(term in lowered for term in inventory_terms)

    @staticmethod
    def _final_text_has_s3_answer_or_blocker(final_lower: str) -> bool:
        s3_answer_terms = (
            "s3 bucket",
            "s3 buckets",
            "bucket:",
            "buckets:",
            "prefixes:",
            "objects:",
            "s3://",
            "aws_s3_list",
        )
        if any(term in final_lower for term in s3_answer_terms):
            return True
        blocker_terms = (
            "aws_bedrock_only=true",
            "bedrock-only",
            "bash allowlist",
            "python sandbox",
            "approval",
            "credentials",
            "access denied",
            "permission",
            "not authorized",
            "unable to list s3",
            "could not list s3",
        )
        return "s3" in final_lower and any(term in final_lower for term in blocker_terms)

    def _current_workspace(self) -> str:
        try:
            from runtime.config import CONFIG
            return getattr(CONFIG, "workspace", "") or os.getcwd()
        except Exception:
            return os.getcwd()

    def _requested_user_text(self) -> str:
        user_text_parts: List[str] = []
        for msg in self.messages:
            if msg.get("role") != "user":
                continue
            content = msg.get("content", "")
            if isinstance(content, str):
                if XML_SYSTEM_REMINDER_TAG in content:
                    continue
                user_text_parts.append(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = str(block.get("text", ""))
                        if XML_SYSTEM_REMINDER_TAG in text:
                            continue
                        user_text_parts.append(text)
        original = getattr(self, "_run_requested_text", "")
        if original:
            user_text_parts.insert(0, original)
        return "\n".join(user_text_parts)

    @staticmethod
    def _missing_requested_paths(requested: str, workspace: str) -> List[str]:
        """Best-effort exact-path gate for user-provided deliverable lists."""
        if not requested:
            return []
        candidates: Set[str] = set()
        path_pattern = re.compile(
            r"(?<![A-Za-z0-9_./\\-])"
            r"([A-Za-z0-9_.+ -]+(?:[\\/][A-Za-z0-9_.+ -]+)+/?"
            r"|[A-Za-z0-9_.+-]+\.(?:py|md|txt|json|toml|yaml|yml|ipynb|zip))"
        )
        for raw in path_pattern.findall(requested):
            item = raw.strip().strip("`'\".,;:")
            item = re.sub(r"^\s*[-*]\s+", "", item).strip()
            if not item or item.startswith(("/", "\\")):
                continue
            lowered = item.lower()
            if lowered.startswith(("http://", "https://")):
                continue
            if not (
                "/" in item
                or "\\" in item
                or lowered.endswith((".zip", "readme.md", "agent_status.md", "pyproject.toml"))
            ):
                continue
            candidates.add(item)

        missing: List[str] = []
        for item in sorted(candidates):
            rel = item.replace("\\", os.sep).replace("/", os.sep)
            path = rel if os.path.isabs(rel) else os.path.join(workspace, rel)
            if item.endswith(("/", "\\")):
                exists = os.path.isdir(path)
            else:
                exists = os.path.exists(path)
            if not exists:
                missing.append(item)
        return missing

    @staticmethod
    def _requested_zip_artifact_problems(requested: str, workspace: str) -> List[str]:
        problems: List[str] = []
        if not requested:
            return problems
        for match in sorted(set(re.findall(r"([A-Za-z0-9_.\\/\-+]+\.zip)\b", requested))):
            candidate = match.replace("\\", os.sep).replace("/", os.sep)
            path = candidate if os.path.isabs(candidate) else os.path.join(workspace, candidate)
            if not os.path.isfile(path):
                problems.append(f"required zip missing: {match}")
                continue
            try:
                with zipfile.ZipFile(path, "r") as archive:
                    bad = archive.testzip()
                if bad is not None:
                    problems.append(f"required zip invalid: {match} has bad member {bad}")
            except Exception as exc:
                problems.append(
                    f"required zip invalid: {match} ({type(exc).__name__}: {exc})"
                )
        return problems

    @staticmethod
    def _final_claim_pytest_problem(final_text_lower: str, workspace: str) -> str:
        """Run a bounded local pytest probe before accepting strong test claims."""
        if os.environ.get("SAGEAGENT_DISABLE_FINAL_PYTEST_GUARD"):
            return ""
        if not os.path.isdir(os.path.join(workspace, "tests")):
            return ""
        if not any(
            phrase in final_text_lower
            for phrase in (
                "all tests pass",
                "all tests passing",
                "100% pass",
                "production-ready",
                "ready for production",
                "project complete",
            )
        ):
            return ""
        log_dir = os.path.join(workspace, ".sageagent_state")
        log_path = os.path.join(log_dir, "final_claim_pytest.log")
        try:
            os.makedirs(log_dir, exist_ok=True)
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests", "-q"],
                cwd=workspace,
                text=True,
                capture_output=True,
                timeout=120,
            )
            output = (result.stdout or "") + (
                "\n--- STDERR ---\n" + result.stderr if result.stderr else ""
            )
            with open(log_path, "w", encoding="utf-8", errors="replace") as handle:
                handle.write(output)
            if result.returncode != 0:
                summary = ""
                for line in reversed(output.splitlines()):
                    if "failed" in line.lower() or "passed" in line.lower():
                        summary = line.strip()
                        break
                if not summary:
                    summary = f"pytest exited {result.returncode}"
                return f"final pytest guard failed ({summary}); see {log_path}"
        except Exception as exc:
            return f"final pytest guard could not verify tests: {exc}"
        return ""


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
        messages=_repair_messages_for_bedrock(messages),
        system=system_prompt,
        tools=_build_tools_api_payload(visible_tools),
        max_tokens=max_tokens,
        temperature=temperature,
        thinking_enabled=thinking_enabled,
        thinking_budget=thinking_budget,
    )

