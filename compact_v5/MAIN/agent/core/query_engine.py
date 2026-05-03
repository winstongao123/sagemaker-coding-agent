"""V5 core/query_engine.py — main agent loop (Phase 8 deliverable, ADR-014).

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
- tool_use → tool_result message accumulation in the model-visible
  conversation buffer.
- Bedrock invocation through `BedrockClient.chat(...)`.
- System prompt assembly via `prompt.build_system_prompt(ctx)`.
- run_one_turn(...) helper for unit tests (single-turn, no loop).

OUT OF SCOPE — explicitly deferred to later phases (per ADR-014):
- Microcompact / context_collapse — Phase 11 UX (PS Issue #4 widget surface).
- 2-stage smart compaction (prune + LLM summary) — Phase 11.
- Skill auto-trigger — Phase 10 (`SKILLS.discover_relevant`).
- Plan mode injection of skills into prompt — Phase 10.
- Sub-agent forkSubagent — Phase 9 (`subagent/spawn.py`).
- File-read state tracking — Phase 4 already lands this; engine respects but
  doesn't reset on compact (no compact in Phase 8).
- Diminishing-returns / repetition guard — deferred.
- Notebook UX (output_fn callback contract) — Phase 11 owns the UI shape;
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

    `text`           — final assistant text (last end_turn turn's text block).
    `messages`       — full message buffer including the user turn that
                       triggered this call. Caller may discard or persist.
    `stop_reason`    — "end_turn" | "max_turns" | "budget_exhausted" |
                       "context_overflow" | "fatal_error".
    `turns_used`     — count of model turns executed during this run.
    `budget_used`    — IterationBudget.used() snapshot at exit.
    `error`          — short message when stop_reason indicates failure.
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
    structured shapes — same convention as v4 dispatch."""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple)):
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            return str(value)
    return str(value)


def _truncate_tool_result(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    head = text[: max_chars - 200]
    return (
        head
        + f"\n\n[... truncated: tool_result exceeded {max_chars} chars; "
        f"original size {len(text)} chars ...]"
    )


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
                the first user turn (Phase 10 wiring contract — Codex
                Phase-10 BLOCKER fix). When None, no skill machinery runs
                — preserves Phase 1-8 backwards compatibility for tests.
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

        self.messages: List[Dict[str, Any]] = []
        # Tool names that have been "discovered" via tool_search this run.
        # Their schemas are added to per-turn `tools=` API payload until the
        # run ends. v5 does NOT persist discovery across `run()` calls — the
        # set is fresh each user message (matches Runnable's per-message
        # discovered set).
        self._discovered_tool_names: Set[str] = set()

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
        # Block C — exec-limit gate (PS#7 fix) + repetition detector.
        # Counters live on the QueryEngine. Codex iter-1 finding #3:
        # unconditional reset at run() entry so counters DON'T leak
        # across run() calls (the v4 contract; sub-agent dispatch is
        # the only legitimate cross-run sharing path, handled via
        # parent_engine forwarding).
        self._exec_call_count = 0  # bash + python_exec only
        self._recent_tool_calls: list = []  # [(name, args_hash), ...]

        # Append user turn (Bedrock requires alternation; merge into trailing
        # user if needed — matches v4 sagemaker_agent.py:8744).
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
        if self.skill_manager is not None:
            try:
                active_block = self.skill_manager.get_active_skill_prompt()
                if active_block:
                    effective_system_prompt = system_prompt + active_block
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
            except Exception as exc:  # noqa: BLE001 — skill machinery never raises into agent loop
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

            # Budget gate — shared with sub-agents (Phase 9).
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
                # Promote previously-discovered tools from deferred → visible.
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
            except Exception as exc:  # noqa: BLE001 — classify and surface
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
            # attribution. "parent" or sub-agent type-string. Best-effort —
            # never break the agent loop if the singleton import fails.
            try:
                from runtime.tokens import TOKENS as _TOKENS
                _TOKENS.add(
                    response.usage or {},
                    model_id=getattr(self.client, "model_id", None),
                    agent_kind=self.agent_kind,
                )
                # Block B+ (PORT_LOG #052): per-turn cost-vs-budget runtime
                # warning. v4 sagemaker_agent.py:8787 prints
                #   `[Cost ${session_cost} passed budget ${limit} — continuing.]`
                # NOT a hard halt — per user 2026-05-03 update to plan v3,
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
                            f"budget ${limit:.2f} — continuing.]"
                        )
                        self._warned_over_budget = True
            except Exception:
                pass

            # Append assistant turn (text + tool_use blocks, plus thinking).
            assistant_content = self._build_assistant_content(response)
            self.messages.append({"role": "assistant", "content": assistant_content})

            if response.text:
                last_text = response.text

            # Stop conditions: end_turn / no tool_use blocks → final answer.
            if not response.tool_calls:
                stop_reason = "end_turn"
                if response.text:
                    output_fn(response.text)
                break

            # Tool dispatch — emit one tool_result per tool_use call.
            tool_results: List[Dict[str, Any]] = []
            for call in response.tool_calls:
                tool = find_tool_by_name(tools, call.name)
                if tool is None:
                    # Unknown tool name — return error to model so it can
                    # recover (v4 parity: dispatch never raises).
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": f"Error: unknown tool '{call.name}'",
                        "is_error": True,
                    })
                    # Block B (Codex finding #2 HIGH lock): every dispatch
                    # path — including unknown-tool — must be audited so
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

                # Plan-mode dispatch gate — strict allowlist by name (v4
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

                # Block C — exec-limit gate (PS#7 fix). Only bash +
                # python_exec count toward this limit. v4 verbatim
                # message at sagemaker_agent.py:9482-9489 — preserved
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

                # Block C — repetition detector. Same (tool_name,
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

                # Block C — JSON-repair tool args before dispatch. If
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

                # Execute. Tool implementations may raise; we trap and surface
                # the error to the model rather than the human user.
                # `parent_engine` is passed for Phase 9 task tool — the sub-agent
                # spawn needs the parent's IterationBudget + BedrockClient (ADR-015).
                try:
                    if call.name in {"bash", "python_exec"}:
                        self._exec_call_count += 1
                    raw = tool.execute(_repaired_input, context={
                        "active_tools": tools,
                        "plan_mode": plan_mode,
                        "parent_engine": self,
                        "parent_depth": getattr(self, "_subagent_depth", 0),
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
                except Exception as exc:  # noqa: BLE001 — surface to model
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

        Order: thinking blocks (if any) → text → tool_use. The thinking
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
        user turn — it does not mutate `self.messages`, so it does not leak
        into subsequent turns once the model has loaded the schemas it needs.
        """
        if not deferred_names:
            return messages
        reminder = (
            "<system-reminder>\n"
            "The following deferred tools are available via tool_search. Their schemas "
            "are NOT loaded — calling them directly will fail. Use tool_search with "
            "query \"select:<name>[,<name>...]\" to load tool schemas before calling them:\n"
            + "\n".join(sorted(deferred_names))
            + "\n</system-reminder>"
        )
        # Transient append: copy the trailing user message and add the reminder
        # as an extra text block. If the trailing turn is not user-role, we
        # append a fresh user message — but this should never happen because
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
