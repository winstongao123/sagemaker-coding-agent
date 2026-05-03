OpenAI Codex v0.125.0 (research preview)
--------
workdir: D:\Github\sagemaker-coding-agent
model: gpt-5.3-codex
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, C:\Users\winst\.codex\memories]
reasoning effort: high
reasoning summaries: none
session id: 019deb98-1f44-7252-9cb8-00013d841046
--------
user
Verify Block B+ (post-iter-1) fixes are clean. APPROVE or list new issues.

iter-1 (gpt-5.3-codex) APPROVE_WITH_FIXES findings (now fixed):
1. HIGH: cost-warning state leak across runs + > vs >= → both fixed in core/query_engine.py
2. MEDIUM: feature-flag import-boundary not wired → entry.py now actively probes for re-introduced `mcp/` package via importlib.util.find_spec
3. MEDIUM: cleanup_registry signal/lock re-entrancy → switched threading.Lock → threading.RLock
4. LOW: B+3..B+6 UNDECLARED_PATTERN + TEST_DESIGN drift "blocks at 100%" → both fixed in V5_DESIGN_DECISIONS.md (ADR-022 §Notes / known scope remaps Block B+ items B+3..B+6) + TEST_DESIGN.md updated to "warns at 100%"

Read ONLY these 5 files:
- compact_v5/MAIN/agent/core/query_engine.py (run() entry around line 211 + cost-warning around line 360)
- compact_v5/MAIN/agent/entry.py (import-boundary guard at top)
- compact_v5/MAIN/agent/runtime/cleanup_registry.py (RLock at module top)
- compact_v5/MAIN/agent/tests/integration/test_block_b_plus.py (6 new finding-lock tests at bottom)
- compact_v5/_status/V5_DESIGN_DECISIONS.md (ADR-022 §Notes / known scope remaps Block B+ items B+3..B+6 — bottom)

For each of the 4 findings: cleanly fixed? Yes/no, one sentence.
FINAL: APPROVE | APPROVE_WITH_FIXES | REJECT.

codex
Reviewing only the five specified files and validating each prior finding against the exact code/doc locations you called out. I’ll inspect the targeted sections plus the six new lock tests, then return a strict `Yes/No` per finding and a final verdict.
web search: 
web search: 
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/core/query_engine.py' | Select-Object -First 460" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/runtime/cleanup_registry.py' | Select-Object -First 220" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/entry.py' | Select-Object -First 220" in D:\Github\sagemaker-coding-agent
 succeeded in 745ms:
"""Block B+ â€” cleanup registry (Block 0 item 0-7 remap per ADR-020).

Adapter of Runnable's `cleanupRegistry` (utils/cleanupRegistry.ts:1-26 /
R8 #18). Provides a single registry of best-effort shutdown callables
that fire on:
  - Normal interpreter exit (atexit)
  - SIGINT (Ctrl+C in a shell-driven context)
  - SIGTERM where the OS supports it

Uses: TokenTracker cost-flush at exit (B+7); SnapshotManager log flush
(future); SessionManager final-save; scratchpad gc (Block C 0-5 remap).

PORT_LOG: see #050.
"""
from __future__ import annotations

import atexit
import logging
import signal
import threading
from typing import Callable, List


# Codex Block-B+ finding #3 (MEDIUM) lock: use RLock so a SIGINT
# arriving while register()/_run_all() holds the lock can re-enter
# without deadlocking. The signal handler calls _run_all() which
# acquires the same lock â€” non-reentrant Lock would deadlock.
_lock = threading.RLock()
_callbacks: List[Callable[[], None]] = []
_installed = False


def register(callback: Callable[[], None]) -> None:
    """Register a no-arg callable to fire on shutdown.

    The callable runs once per process; if it raises, the error is
    logged at WARNING and other callbacks still run.
    """
    with _lock:
        _callbacks.append(callback)
        _ensure_installed_locked()


def unregister(callback: Callable[[], None]) -> None:
    """Remove a previously registered callback (idempotent)."""
    with _lock:
        try:
            _callbacks.remove(callback)
        except ValueError:
            pass


def _run_all() -> None:
    """Fire all registered callbacks. Errors are logged, not re-raised."""
    with _lock:
        cbs = list(_callbacks)
        _callbacks.clear()
    for cb in cbs:
        try:
            cb()
        except Exception as exc:  # noqa: BLE001 â€” best-effort
            logging.warning(
                f"cleanup_registry: callback {cb!r} raised "
                f"{type(exc).__name__}: {exc}"
            )


def _signal_handler(_signum, _frame):
    _run_all()
    # Re-raise SIGINT semantics so the host (Jupyter / shell) sees the
    # interrupt and can take its normal path.
    raise KeyboardInterrupt


def _ensure_installed_locked() -> None:
    """Install atexit + signal handlers exactly once. Caller holds _lock."""
    global _installed
    if _installed:
        return
    atexit.register(_run_all)
    # Some hosts (Jupyter notebook kernels) override signal handlers;
    # tolerate the install failing â€” atexit still gives us best-effort.
    try:
        signal.signal(signal.SIGINT, _signal_handler)
    except (ValueError, OSError):
        pass
    try:
        signal.signal(signal.SIGTERM, _signal_handler)
    except (ValueError, OSError, AttributeError):
        pass
    _installed = True


def _reset_for_tests() -> None:
    """Test helper â€” drop registered callbacks without un-installing handlers."""
    with _lock:
        _callbacks.clear()


__all__ = ["register", "unregister"]

 succeeded in 756ms:
"""V5 entry.py â€” cell-0 import target for chat.ipynb (Phase 11, ADR-017).

Re-exports the public surface. Notebook cells should be able to:

    from entry import Agent, create_chat_ui, CONFIG, BEDROCK_MODELS

without knowing which subpackage owns each name.

Block B+ Codex finding #2 (MEDIUM) lock: import-boundary fail-closed
for v5.0.1 hard-constraint banned subsystems (#9 MCP, #10 streaming,
anthropic_api_direct). Any future code path that re-introduces them
will fail at import here.

PORT_LOG: see #031 + #032 (chat.ipynb wiring) + #056 (banned-subsystem guard).
"""
from __future__ import annotations

# ============================================================
# Banned-subsystem import-time guard (Block B+ â€” ADR-022 / PORT_LOG #056)
# ============================================================
#
# v5.0.1 hard constraints #9 + #10 forbid MCP and streaming. The guard
# below ACTIVELY checks whether a banned subsystem package has been
# re-introduced (e.g. someone added a `mcp/` package back). If so,
# importing entry.py â€” the v5 public surface â€” fails-closed at load.
# This is the import-boundary fail-closed contract from ADR-022 Â§
# Linked port-log row #051.
import importlib.util as _importlib_util

_BANNED_PACKAGE_NAMES = ("mcp",)
for _banned in _BANNED_PACKAGE_NAMES:
    if _importlib_util.find_spec(_banned) is not None:
        # Heuristic: filter out external packages that happen to share
        # the name (a v5 package would live under MAIN/agent/<name>/).
        # Only raise when the spec resolves to a path inside this agent
        # package, indicating an in-tree re-introduction.
        _spec = _importlib_util.find_spec(_banned)
        _origin = getattr(_spec, "origin", "") or ""
        if "MAIN/agent" in _origin.replace("\\", "/") or _origin.endswith(
            f"/{_banned}/__init__.py"
        ):
            raise ImportError(
                f"v5.0.1 hard constraint: banned subsystem '{_banned}' "
                f"has been re-introduced at {_origin!r}. See "
                f"runtime/feature_flags.py."
            )

# Public Agent class (Phase 11 â€” wraps Phase 1-10 modules)
from agent import Agent  # noqa: F401

# Config singleton + Bedrock model registry (Phase 1)
from runtime.config import CONFIG  # noqa: F401

# Optional Bedrock model list â€” kept as a module-level constant so the
# config widget in chat.ipynb cell 2 can populate a dropdown.
BEDROCK_MODELS = [
    ("Claude Sonnet 4.5 (anthropic.claude-sonnet-4-5-20250929-v1:0)",
     "anthropic.claude-sonnet-4-5-20250929-v1:0"),
    ("Claude Haiku 4.5 (au.anthropic.claude-haiku-4-5-20251001-v1:0)",
     "au.anthropic.claude-haiku-4-5-20251001-v1:0"),
    ("Claude Sonnet 3.5 (anthropic.claude-3-5-sonnet-20241022-v2:0)",
     "anthropic.claude-3-5-sonnet-20241022-v2:0"),
]

# Chat UI factory (Phase 11)
from ui.chat_ui import create_chat_ui  # noqa: F401

# Skill manager helper for power users who want to inspect / activate
# skills programmatically (Phase 10).
from skills.manager import SkillManager  # noqa: F401

# IterationBudget for power users + tests (Phase 8).
from core.budget import IterationBudget  # noqa: F401

 succeeded in 761ms:
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

    `text`           â€” final assistant text (last end_turn turn's text block).
    `messages`       â€” full message buffer including the user turn that
                       triggered this call. Caller may discard or persist.
    `stop_reason`    â€” "end_turn" | "max_turns" | "budget_exhausted" |
                       "context_overflow" | "fatal_error".
    `turns_used`     â€” count of model turns executed during this run.
    `budget_used`    â€” IterationBudget.used() snapshot at exit.
    `error`          â€” short message when stop_reason indicates failure.
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
    structured shapes â€” same convention as v4 dispatch."""
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

        self.messages: List[Dict[str, Any]] = []
        # Tool names that have been "discovered" via tool_search this run.
        # Their schemas are added to per-turn `tools=` API payload until the
        # run ends. v5 does NOT persist discovery across `run()` calls â€” the
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
            except Exception as exc:  # noqa: BLE001 â€” skill machinery never raises into agent loop
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

            # Budget gate â€” shared with sub-agents (Phase 9).
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
            except Exception as exc:  # noqa: BLE001 â€” classify and surface
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
            # attribution. "parent" or sub-agent type-string. Best-effort â€”
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
            self.messages.append({"role": "assistant", "content": assistant_content})

            if response.text:
                last_text = response.text

            # Stop conditions: end_turn / no tool_use blocks â†’ final answer.
            if not response.tool_calls:
                stop_reason = "end_turn"
                if response.text:
                    output_fn(response.text)
                break

            # Tool dispatch â€” emit one tool_result per tool_use call.
            tool_results: List[Dict[str, Any]] = []
            for call in response.tool_calls:
                tool = find_tool_by_name(tools, call.name)
                if tool is None:
                    # Unknown tool name â€” return error to model so it can
                    # recover (v4 parity: dispatch never raises).
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": f"Error: unknown tool '{call.name}'",
                        "is_error": True,
                    })
                    # Block B (Codex finding #2 HIGH lock): every dispatch
                    # path â€” including unknown-tool â€” must be audited so
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

                # Plan-mode dispatch gate â€” strict allowlist by name (v4
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

                # Execute. Tool implementations may raise; we trap and surface
                # the error to the model rather than the human user.
                # `parent_engine` is passed for Phase 9 task tool â€” the sub-agent
                # spawn needs the parent's IterationBudget + BedrockClient (ADR-015).
                try:
                    raw = tool.execute(call.input, context={

codex
I’ve confirmed the three code files include the intended fixes (run-scope warning reset, import-boundary probe, and `RLock`). Next I’m checking the new integration lock tests and ADR/doc wording to ensure behavior and scope claims are aligned.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/tests/integration/test_block_b_plus.py'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/_status/V5_DESIGN_DECISIONS.md' | Select-Object -Last 260" in D:\Github\sagemaker-coding-agent
 succeeded in 439ms:
"""Block B+ â€” SessionManager + cost-limit + AGENT_STATUS auto-load + FileCache.

Tests per TEST_DESIGN.md Â§Block B+ (7 tests) plus 2 ADR-020 remap lock
tests (0-7 cleanupRegistry, 0-9 feature_flags fail-closed):

  T1 test_session_manager_atomic_save              tmp + os.replace; partial-write doesn't corrupt
  T1 test_session_save_load_preserves_cost         save at $2.09 â†’ load â†’ TOKENS.session_cost == 2.09 (PS#5)
  T1 test_session_cost_limit_warns_at_100pct       v5 = warn-and-continue (per user 2026-05-03 Plan v3 update)
  T1 test_agent_status_auto_load                   first Agent.run() reads AGENT_STATUS.md and injects
  T2 test_filecache_thread_local_isolation         parent _FILES_READ not visible inside sub-agent thread
  T2 test_subagent_token_attribution               TOKENS.parent_input_tokens > 0 AND subagent["build"] > 0 AND session_cost == sum
  T1 test_tokens_singleton_is_budget_source        budget checks read TOKENS singleton (closes PS#6)

  + test_cleanup_registry_register_and_fire        ADR-020 remap 0-7 lock
  + test_feature_flag_fail_closed_for_banned       ADR-020 remap 0-9 lock
"""
from __future__ import annotations

import json
import os
import sys
import threading
from typing import Any, Dict

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch):
    """Reset TOKENS + FILE_CACHE between tests."""
    from runtime.tokens import TOKENS
    from runtime.file_cache import FILE_CACHE

    TOKENS.reset()
    FILE_CACHE.clear_all()
    FILE_CACHE.exit_thread_local_context()
    yield
    TOKENS.reset()
    FILE_CACHE.clear_all()
    FILE_CACHE.exit_thread_local_context()


# ============================================================
# T1 â€” SessionManager atomic save
# ============================================================

def test_session_manager_atomic_save(tmp_path):
    from runtime.session import SessionManager, Session

    sm = SessionManager(sessions_dir=str(tmp_path))
    s = sm.create(title="atomic-test")
    s.messages = [{"role": "user", "content": "hi"}]
    sm.save(s)

    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    with open(files[0], "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["id"] == s.id
    assert data["title"] == "atomic-test"
    assert data["messages"][0]["content"] == "hi"


def test_session_load_round_trip(tmp_path):
    from runtime.session import SessionManager, Session

    sm = SessionManager(sessions_dir=str(tmp_path))
    s = sm.create(title="round-trip")
    s.messages = [{"role": "user", "content": "x"}]
    s.metadata = {"foo": "bar"}
    sm.save(s)

    loaded = sm.load(s.id)
    assert loaded is not None
    assert loaded.id == s.id
    assert loaded.title == "round-trip"
    assert loaded.messages == [{"role": "user", "content": "x"}]
    assert loaded.metadata == {"foo": "bar"}


# ============================================================
# T1 â€” Save / load preserves session cost (PS#5)
# ============================================================

def test_session_save_load_preserves_cost(tmp_path):
    """PS#5: session cost must persist across /save â†’ /resume.

    Block B+'s SessionManager + Block B's TokenTracker.restore close
    this together. We simulate the saveâ†’quitâ†’reload cycle by storing
    TOKENS.get_stats() in the session metadata, restoring on load,
    and asserting the singleton ends up at the recorded cost.
    """
    from runtime.session import SessionManager
    from runtime.tokens import TOKENS

    sm = SessionManager(sessions_dir=str(tmp_path))
    s = sm.create(title="cost-restore")

    # Simulate a session of work that accumulates cost.
    TOKENS.add(
        {"input_tokens": 10_000, "output_tokens": 1_000},
        model_id="anthropic.claude-sonnet-4-5-20250929-v1:0",
    )
    expected_cost = TOKENS.session_cost
    assert expected_cost > 0

    # Snapshot stats into session metadata + persist.
    s.metadata["tokens_stats"] = TOKENS.get_stats()
    sm.save(s)

    # Simulate a fresh process: reset singleton, then reload.
    TOKENS.reset()
    assert TOKENS.session_cost == 0.0

    loaded = sm.load(s.id)
    assert loaded is not None
    TOKENS.restore(loaded.metadata["tokens_stats"])
    assert abs(TOKENS.session_cost - expected_cost) < 1e-6


# ============================================================
# T1 â€” session_cost_limit warn-and-continue (per user 2026-05-03)
# ============================================================

def test_session_cost_limit_warns_at_100pct(monkeypatch, caplog):
    """v5 default v4 behavior: warn at 80%, warn-and-continue at 100%.

    Per user 2026-05-03 Plan v3 Â§Block B+ update:
      "Behavior matches v4: warn at 80%, warn at 100% but agent
       CONTINUES. User decidesâ€¦ NO hard halt at application level."
    """
    import logging
    from runtime.tokens import TOKENS
    from runtime.config import CONFIG

    monkeypatch.setattr(CONFIG, "session_cost_limit", 0.005)

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        # Push session_cost above the limit.
        TOKENS.add(
            {"input_tokens": 100_000, "output_tokens": 5_000},
            model_id="anthropic.claude-sonnet-4-5-20250929-v1:0",
        )

    # is_over_budget reports True, but the tracker did NOT raise; the
    # next add() must still work (warn-and-continue contract).
    assert TOKENS.is_over_budget()
    pre_count = TOKENS.api_calls
    TOKENS.add(
        {"input_tokens": 1_000, "output_tokens": 100},
        model_id="anthropic.claude-sonnet-4-5-20250929-v1:0",
    )
    assert TOKENS.api_calls == pre_count + 1, (
        "v5 contract: TOKENS.add must NOT raise / refuse after over-budget; "
        "warn-and-continue per user 2026-05-03 Plan v3 update"
    )
    assert any(
        "limit" in r.getMessage().lower() or "budget" in r.getMessage().lower()
        for r in caplog.records
    ), "over-budget condition must log a WARNING"


# ============================================================
# T1 â€” AGENT_STATUS.md auto-load on first Agent.run()
# ============================================================

def test_agent_status_auto_load(tmp_path, monkeypatch):
    """First Agent.run() reads AGENT_STATUS.md from CONFIG.workspace and
    appends it to the dynamic tail of the system prompt."""
    from runtime.config import CONFIG
    from runtime.bedrock_client import BedrockClient
    from agent import Agent

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "status_doc", "AGENT_STATUS.md")
    monkeypatch.setattr(CONFIG, "enable_status_doc", True)

    status_path = tmp_path / "AGENT_STATUS.md"
    status_path.write_text(
        "# Phase 5 handoff\n\nResume from step 7.", encoding="utf-8",
    )

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    # Capture the system prompt the engine ends up with.
    captured = {}
    real_run = a._engine.run

    def spy_run(*args, **kwargs):
        captured["system_prompt"] = kwargs.get("system_prompt") or args[1]
        return real_run(*args, **kwargs)

    monkeypatch.setattr(a._engine, "run", spy_run)
    a.run("hi")

    sp = captured["system_prompt"]
    assert "Phase 5 handoff" in sp
    assert "Resume from step 7" in sp


def test_agent_status_auto_load_disabled(tmp_path, monkeypatch):
    """When enable_status_doc=False, AGENT_STATUS.md is ignored."""
    from runtime.config import CONFIG
    from runtime.bedrock_client import BedrockClient
    from agent import Agent

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "enable_status_doc", False)

    (tmp_path / "AGENT_STATUS.md").write_text("must be ignored", encoding="utf-8")

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    captured = {}
    real_run = a._engine.run

    def spy_run(*args, **kwargs):
        captured["system_prompt"] = kwargs.get("system_prompt") or args[1]
        return real_run(*args, **kwargs)

    monkeypatch.setattr(a._engine, "run", spy_run)
    a.run("hi")
    assert "must be ignored" not in captured["system_prompt"]


# ============================================================
# T2 â€” FileCache thread-local context isolation
# ============================================================

def test_filecache_thread_local_isolation(tmp_path):
    """A sub-agent thread that calls enter_thread_local_context() must
    not see the parent's `in_context` set (and vice versa)."""
    from runtime.file_cache import FILE_CACHE

    f1 = tmp_path / "parent.txt"
    f1.write_text("p", encoding="utf-8")
    f2 = tmp_path / "child.txt"
    f2.write_text("c", encoding="utf-8")

    # Parent (main thread) marks its file in context.
    FILE_CACHE.mark_in_context(str(f1))
    assert FILE_CACHE.is_in_context(str(f1))

    saw_parent_marker_inside_child = []

    def child_thread():
        FILE_CACHE.enter_thread_local_context()
        try:
            saw_parent_marker_inside_child.append(
                FILE_CACHE.is_in_context(str(f1))
            )
            FILE_CACHE.mark_in_context(str(f2))
            saw_parent_marker_inside_child.append(
                FILE_CACHE.is_in_context(str(f2))
            )
        finally:
            FILE_CACHE.exit_thread_local_context()

    t = threading.Thread(target=child_thread)
    t.start()
    t.join()

    # Sub-agent didn't see parent's context.
    assert saw_parent_marker_inside_child[0] is False
    # Sub-agent saw its own marker.
    assert saw_parent_marker_inside_child[1] is True
    # Parent's marker is preserved post-child.
    assert FILE_CACHE.is_in_context(str(f1))
    # Child's marker did NOT leak into parent.
    assert FILE_CACHE.is_in_context(str(f2)) is False


def test_filecache_save_and_restore_round_trip():
    from runtime.file_cache import FILE_CACHE

    FILE_CACHE.mark_in_context("/tmp/a")
    FILE_CACHE.mark_in_context("/tmp/b")
    saved = FILE_CACHE.save_and_clear_context()
    # Cleared.
    assert FILE_CACHE.is_in_context("/tmp/a") is False
    assert FILE_CACHE.is_in_context("/tmp/b") is False
    # Restored.
    FILE_CACHE.restore_context(saved)
    assert FILE_CACHE.is_in_context("/tmp/a")
    assert FILE_CACHE.is_in_context("/tmp/b")


# ============================================================
# T2 â€” Sub-agent token attribution acceptance test (Plan v3 Â§Block B+)
# ============================================================

def test_subagent_token_attribution():
    """Plan v3 acceptance: parent + sub-agent both update TOKENS, but
    each goes to its own bucket. session_cost == sum of buckets."""
    from runtime.tokens import TOKENS

    # Parent does some work.
    TOKENS.add(
        {"input_tokens": 1000, "output_tokens": 200},
        model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
        agent_kind="parent",
    )
    # Sub-agent type=build does some work.
    TOKENS.add(
        {"input_tokens": 500, "output_tokens": 100},
        model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
        agent_kind="build",
    )

    assert TOKENS.parent_input_tokens == 1000
    assert TOKENS.parent_output_tokens == 200
    assert TOKENS.subagent_input_tokens["build"] == 500
    assert TOKENS.subagent_output_tokens["build"] == 100
    assert TOKENS.parent_cost > 0
    assert TOKENS.subagent_cost["build"] > 0
    # Roll-up invariant within $0.0001.
    assert abs(
        TOKENS.session_cost
        - (TOKENS.parent_cost + sum(TOKENS.subagent_cost.values()))
    ) < 1e-4


# ============================================================
# T1 â€” TOKENS singleton is the budget source (PS#6 closure)
# ============================================================

def test_tokens_singleton_is_budget_source():
    """PS#6 was: budget read from wrong source (Agent attribute, not
    singleton). v5 must read budget from TOKENS singleton so all agents
    share one cost view."""
    from runtime.tokens import TOKENS
    from agent import Agent
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a1 = Agent(client=client)
    a2 = Agent(client=client)

    TOKENS.reset()
    a1.run("first")
    cost_after_a1 = TOKENS.session_cost
    a2.run("second")
    cost_after_a2 = TOKENS.session_cost

    # Both agents update the SAME singleton.
    assert cost_after_a2 >= cost_after_a1
    # The increment from a2 is non-trivial (mock returns non-zero usage).
    assert TOKENS.api_calls >= 2


# ============================================================
# ADR-020 remap 0-7 â€” cleanup_registry register-and-fire
# ============================================================

def test_cleanup_registry_register_and_fire():
    """register() + _run_all() fires callbacks once and clears the list."""
    from runtime import cleanup_registry as cr

    cr._reset_for_tests()
    fired = []
    cr.register(lambda: fired.append("a"))
    cr.register(lambda: fired.append("b"))
    cr._run_all()
    assert fired == ["a", "b"]
    # After _run_all, the registry is empty so a second fire is a no-op.
    cr._run_all()
    assert fired == ["a", "b"]


def test_cleanup_registry_callback_error_does_not_skip_others(caplog):
    import logging
    from runtime import cleanup_registry as cr

    cr._reset_for_tests()
    fired = []
    def bad():
        raise RuntimeError("intentional")
    cr.register(bad)
    cr.register(lambda: fired.append("ok"))

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        cr._run_all()
    assert fired == ["ok"]
    assert any("intentional" in r.getMessage() for r in caplog.records)


# ============================================================
# ADR-020 remap 0-9 â€” feature_flags fail-closed
# ============================================================

def test_feature_flag_fail_closed_for_banned():
    from runtime.feature_flags import feature_enabled, is_banned, assert_not_banned

    # Banned features always return False.
    assert feature_enabled("mcp") is False
    assert feature_enabled("streaming") is False
    assert feature_enabled("anthropic_api_direct") is False
    assert is_banned("mcp")
    # Unknown features fail-closed.
    assert feature_enabled("nonexistent_feature_xyz") is False
    # Soft features default OFF.
    assert feature_enabled("skill_patching") is False
    # assert_not_banned raises on banned.
    with pytest.raises(ImportError):
        assert_not_banned("mcp")
    # Non-banned name doesn't raise.
    assert_not_banned("not_in_banned_set")


def test_feature_flag_env_override_for_soft_features(monkeypatch):
    """Soft features can be flipped on/off via env. Banned features ignore env."""
    from runtime.feature_flags import feature_enabled

    monkeypatch.setenv("SAGEMAKER_AGENT_FEATURE_SKILL_PATCHING", "1")
    assert feature_enabled("skill_patching") is True

    monkeypatch.setenv("SAGEMAKER_AGENT_FEATURE_SKILL_PATCHING", "0")
    assert feature_enabled("skill_patching") is False

    # Banned ignores env.
    monkeypatch.setenv("SAGEMAKER_AGENT_FEATURE_MCP", "1")
    assert feature_enabled("mcp") is False


# ============================================================
# Codex Block-B+ iter-1 finding-lock tests (regression prevention)
# ============================================================

def test_cost_warning_resets_each_run(monkeypatch):
    """Codex iter-1 finding #1 (HIGH) lock: `_warned_over_budget` resets
    at every run() entry so subsequent runs re-emit the warning once
    each. Without the reset, a long-running Agent would emit the
    warning once on first run and then stay silent for the rest of
    the session even when costs keep growing."""
    from runtime.tokens import TOKENS
    from runtime.config import CONFIG
    from runtime.bedrock_client import BedrockClient
    from agent import Agent

    monkeypatch.setattr(CONFIG, "session_cost_limit", 0.0001)

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    TOKENS.reset()
    # Push above budget.
    TOKENS.add(
        {"input_tokens": 10_000, "output_tokens": 1_000},
        model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
    )

    captured: list = []
    def cap(s):
        captured.append(s)

    a.run("first", output_fn=cap)
    a.run("second", output_fn=cap)
    a.run("third", output_fn=cap)

    over_budget_messages = [s for s in captured if "passed budget" in s]
    assert len(over_budget_messages) >= 2, (
        f"warning must reset and re-fire each run; got "
        f"{len(over_budget_messages)} over-budget lines: {captured}"
    )


def test_cost_warning_fires_on_exact_100_percent(monkeypatch):
    """Codex iter-1 finding #1 lock: `>=` (not `>`) so exact-100% trips."""
    from runtime.tokens import TOKENS
    from runtime.config import CONFIG
    from runtime.bedrock_client import BedrockClient
    from agent import Agent

    # Force session_cost == session_cost_limit exactly.
    monkeypatch.setattr(CONFIG, "session_cost_limit", 0.001)
    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    TOKENS.reset()
    # 1000 input tokens at $0.001/1k = $0.001 exactly = the limit.
    TOKENS.add(
        {"input_tokens": 1_000, "output_tokens": 0},
        model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
    )
    assert abs(TOKENS.session_cost - 0.001) < 1e-9

    captured: list = []
    a.run("turn", output_fn=lambda s: captured.append(s))
    over_budget_messages = [s for s in captured if "passed budget" in s]
    assert over_budget_messages, (
        "exact 100% must fire the warning (>= not >); got: " + str(captured)
    )


def test_entry_import_succeeds_when_no_mcp_package_present():
    """Codex iter-1 finding #2 (MEDIUM) lock: entry.py's import-boundary
    guard must NOT raise when the v5 tree has no banned packages.
    (We just imported entry successfully if this test is even running.)"""
    import entry
    assert entry is not None
    assert hasattr(entry, "Agent")


def test_entry_guard_raises_if_banned_package_reintroduced(tmp_path, monkeypatch):
    """Lock for finding #2: simulate a re-introduced `mcp/` package by
    pointing importlib at a tmp directory that contains one. The guard
    in entry.py must reject this import path.

    We can't easily re-import entry.py against an alternate path, so we
    test the guard's logic by crafting a fake spec via importlib and
    verifying the heuristic catches an in-tree path."""
    import importlib.util as iu

    # Simulate the discovered spec.origin string the guard checks.
    fake_origin = str(tmp_path / "MAIN" / "agent" / "mcp" / "__init__.py")
    # The guard: `"MAIN/agent" in _origin.replace("\\", "/") or _origin.endswith("/mcp/__init__.py")`
    normalized = fake_origin.replace("\\", "/")
    assert "MAIN/agent" in normalized
    # And the explicit name-suffix branch:
    assert normalized.endswith("/mcp/__init__.py")


def test_cleanup_registry_uses_rlock_for_signal_safety():
    """Codex iter-1 finding #3 (MEDIUM) lock: cleanup_registry's _lock
    must be threading.RLock (not Lock) so the signal handler can re-enter
    without deadlocking. RLock supports the same thread re-acquiring."""
    import threading
    from runtime import cleanup_registry as cr

    # threading.RLock() returns a `_thread.RLock` object; threading.Lock()
    # returns `_thread.lock`. We verify by attempting re-acquisition.
    cr._lock.acquire()
    try:
        # Same-thread re-acquire would deadlock on a non-reentrant Lock.
        # Use blocking=False so a regression here is caught instead of hanging.
        acquired_twice = cr._lock.acquire(blocking=False)
        assert acquired_twice, (
            "cleanup_registry._lock must be RLock for signal-handler "
            "re-entrancy; got non-reentrant Lock"
        )
        cr._lock.release()
    finally:
        cr._lock.release()


def test_block_b_plus_remap_table_present_in_adr_022():
    """Codex iter-1 finding #4 (LOW) lock: ADR-022 declares the explicit
    remap for Block B+ items B+3..B+6 (was UNDECLARED_PATTERN before
    the fix-up commit). This test pins the contract so future Block I /
    Block A reviews can verify the matching landing site."""
    adr_path = os.path.join(
        _AGENT_ROOT, "..", "..",
        "_status", "V5_DESIGN_DECISIONS.md",
    )
    with open(adr_path, "r", encoding="utf-8") as f:
        text = f.read()
    # ADR-022 must contain the explicit Block-B+ remap header.
    assert "Notes / known scope remaps (Block B+ items B+3..B+6)" in text
    # And must declare landing sites for each of the 4 items.
    for item in ("B+3", "B+4", "B+5", "B+6"):
        # Each B+N row references its target Block (I or A).
        # Be tolerant of formatting; just look for the literal item id.
        assert item in text, f"ADR-022 missing landing-Block remap for {item}"

 succeeded in 689ms:
- MODIFIED: `compact_v5/MAIN/agent/runtime/snapshot.py` (lazy @property)
- MODIFIED: `compact_v5/MAIN/agent/__init__.py` (Agent.run AGENT_STATUS
  auto-load + first-call cache)
- MODIFIED: `compact_v5/MAIN/agent/core/query_engine.py` (cost runtime
  warning post-chat())
- MODIFIED: `compact_v5/MAIN/agent/subagent/spawn.py` (FILE_CACHE
  save/restore around child.run try/finally)

### Linked port-log rows
- #048 â€” SessionManager
- #049 â€” FileCache
- #050 â€” cleanup_registry (ADR-020 0-7 remap)
- #051 â€” feature_flags (ADR-020 0-9 remap)
- #052 â€” cost runtime warning
- #053 â€” sub-agent FILE_CACHE save/restore boundary
- #054 â€” atexit cost-flush
- #055 â€” AGENT_STATUS auto-load

### Validation
- 483 pass + 5 skipped (was 469 + 5 at end of Block B; +14 net new).
- verify_ship_zip.py: PASS (104 files / 272.4 KB / 38%).

### PS_problems closed/extended
- **PS#5** (session cost not persisted): SessionManager round-trip
  test confirms TOKENS.session_cost survives save â†’ load. Lock test:
  test_session_save_load_preserves_cost.
- **PS#6** (budget read from wrong source): test_tokens_singleton_is_budget_source
  asserts both Agents share TOKENS state. Lock test in this Block.

### Notes / known scope remaps (Block B+ items B+3..B+6)

Codex Block-B+ iter-1 finding #4 (LOW) flagged B+3..B+6 as
UNDECLARED_PATTERN until remap is concretely declared. Per
constraint #3 (no deferrals), this table records the explicit
landing Block + lock test for each:

| Item | Capability | LOC | Lands in Block | Implementation site (target file) | Lock test (Block where it runs) |
|---|---|---|---|---|---|
| B+3 | 4-line cost block format (R11 N10) | 15 | **Block I** (UI/widgets) | `ui/widgets.py:CostWidget.render_html` (4-line block: total / per-model / per-agent / cache) | `test_cost_widget_renders_4_line_block` (Block I) |
| B+4 | Local OTel-style counters (R11 N11) | 25 | **Block I** | `runtime/tokens.py:TokenTracker.get_otel_counters()` (local SQLite/JSON only â€” never external endpoint per Bedrock-only constraint) | `test_otel_counters_emitted_locally_only` (Block I) |
| B+5 | Recursive advisor sub-cost accounting (R11 N12) | 30 | **Block A** (Compactor) | `core/compactor.py` calls `TOKENS.add(usage, agent_kind="advisor")` for the auxiliary compaction-summary model | `test_advisor_sub_cost_attributed` (Block A) |
| B+6 | contextWindow refresh on every cost update (R11 N13) | 5 | **Block I** | hook `IterationBudgetWidget.update()` to fire on every TOKENS.add (per-update refresh) | `test_iteration_budget_widget_refreshes_on_token_add` (Block I) |

Each row's TARGET BLOCK must verify:
- (a) the row above is honored
- (b) the lock test exists and is green
- (c) PORT_LOG row references the implementing Block

This closes Codex iter-1 finding #4 (UNDECLARED_PATTERN) for B+3..B+6.

## ADR-021 â€” Block B (v5.0.1): TokenTracker + AuditLogger + SnapshotManager + tokenEstimation + ADR-020 0-3/0-8 remap

**Date**: 2026-05-03
**Phase ID**: v5.0.1 Block B
**Status**: ACCEPTED

### Context
v5.0.0 shipped without TokenTracker / AuditLogger / SnapshotManager â€” a
documented PS_problem (#5 cost not persisted, #6 budget read from wrong
source). Block B closes that gap with verbatim ports of v4's three
classes plus Runnable's tokenEstimation helpers (so Block A Compactor
has accurate context-budget math) plus per-agent attribution so parent
+ sub-agent costs roll up correctly. Block 0 items 0-3 (BEDROCK_EXTRA_
PARAMS_HEADERS) and 0-8 (validate_bounded_int_env_var) land here per
ADR-020's remap table â€” Block B owns runtime/bedrock_client + runtime/
config consumers.

### Options
1. **Verbatim ports + Runnable estimators** (chosen): port v4's
   TokenTracker / AuditLogger / SnapshotManager byte-for-byte (modulo
   constructor injection of `config`), add Runnable's tokenEstimation
   helpers, extend TokenTracker with per-agent attribution. Wire only
   in places that already exist (QueryEngine, edit_file, write_file).
   Skill apply_proposal wiring deferred to Block I (skill manager).
2. **Re-implement from Runnable's TokenTracker**: would lose v4's
   cache-aware pricing math (cache_read=10%, cache_write=125%) which
   v5 needs for Bedrock prompt caching cost reporting. Rejected.
3. **Skip per-agent attribution to Block B+**: Plan v3 Block B+
   acceptance test demands `TOKENS.parent_input_tokens > 0 AND
   TOKENS.subagent_input_tokens["build"] > 0` so the data model has
   to land here even if the wiring contract finalizes in B+. Done as
   chosen.

### Decision
Option 1. Block B ships:
- `runtime/tokens.py` (verbatim TokenTracker + MODEL_COSTS + per-agent
  attribution + EXCLUDED_MODELS_FOR_CACHE_BREAK + IMAGE_MAX_TOKEN_SIZE
  + bytes_per_token_for_file_type + estimate_message_tokens +
  has_thinking_blocks + rough_token_count_for_block + rough_token_
  count_for_message + final_context_tokens_from_last_response +
  token_count_with_estimation + ToolResult dataclass)
- `runtime/audit.py` (verbatim AuditLogger + AuditEntry)
- `runtime/snapshot.py` (verbatim SnapshotManager)
- `runtime/env_validation.py` (validate_bounded_int_env_var per
  ADR-020 0-8 remap)
- `runtime/bedrock_client.py` extended:
    - `BEDROCK_EXTRA_PARAMS_HEADERS` frozenset (per ADR-020 0-3 remap)
    - `BedrockClient.count_tokens()` method (B-1, R4 #41 MUST)
- Wiring:
    - `core/query_engine.py` â€” TOKENS.add(usage, model_id, agent_kind)
      after every chat() return; AUDIT.log on every tool dispatch
      (success + failure paths); `agent_kind` + `session_id` ctor params
    - `subagent/spawn.py` â€” `_new_child_engine` accepts `agent_type`
      and forwards to QueryEngine ctor as `agent_kind`
    - `tools/edit_file.py` + `tools/write_file.py` â€” SNAPSHOTS.save
      best-effort before write/edit
- Tests: 18 new (17 pass + 1 T5 skipped without RUN_REAL_BEDROCK).

### Rationale
- Verbatim ports preserve v4's battle-tested invariants (cache pricing
  math, LRU snapshot eviction, redaction sensitive-key set).
- Constructor `config` injection avoids the v4 import-time global
  dependency that Phase 1-13 already moved away from for `BedrockClient`.
- Per-agent attribution data model lives on the same singleton so
  `session_cost == parent_cost + sum(subagent_cost.values())` is
  enforceable (the test_token_tracker_per_agent_breakdown lock pins
  this within $0.0001).
- ADR-020 0-3 and 0-8 land here because runtime/bedrock_client.py and
  runtime/config.py consumers are the targets â€” Block 0 didn't touch
  either.
- The remaining ADR-020 remap rows (0-4 / 0-5 / 0-6 / 0-7 / 0-9 / 0-10)
  land in their declared Blocks (B+ / C / E+F) â€” none silently dropped.

### Runnable-fidelity impact
- MODEL_COSTS: dropped `fast-mode` tier (Anthropic-direct only); kept
  cache-aware math. FAITHFUL-WITH-JUSTIFIED-ADAPTATION.
- tokenEstimation: TS Promise-based async â†’ Python sync. Per-block-type
  math preserved. countTokensViaHaikuFallback (B-2) deferred-with-
  intent to Block A (where it's used) â€” no scope drop.
- EXCLUDED_MODELS_FOR_CACHE_BREAK: net-new (R4 #14 was a Wave-5-DEEP
  finding not in original Runnable code).

### Affected files
- NEW: `compact_v5/MAIN/agent/runtime/tokens.py`
- NEW: `compact_v5/MAIN/agent/runtime/audit.py`
- NEW: `compact_v5/MAIN/agent/runtime/snapshot.py`
- NEW: `compact_v5/MAIN/agent/runtime/env_validation.py`
- NEW: `compact_v5/MAIN/agent/tests/integration/test_block_b.py`
- MODIFIED: `compact_v5/MAIN/agent/runtime/bedrock_client.py`
- MODIFIED: `compact_v5/MAIN/agent/core/query_engine.py`
- MODIFIED: `compact_v5/MAIN/agent/subagent/spawn.py`
- MODIFIED: `compact_v5/MAIN/agent/tools/edit_file.py`
- MODIFIED: `compact_v5/MAIN/agent/tools/write_file.py`
- MODIFIED: `compact_v5/MAIN/agent/tests/integration/test_subagent.py`
  (mock signatures updated to accept new `agent_type` kwarg)

### Linked port-log rows
- #039 â€” TokenTracker
- #040 â€” MODEL_COSTS + EXCLUDED_MODELS_FOR_CACHE_BREAK + canonicalize_model_id
- #041 â€” Runnable tokenEstimation helpers
- #042 â€” ToolResult dataclass
- #043 â€” AuditLogger + AuditEntry
- #044 â€” SnapshotManager
- #045 â€” validate_bounded_int_env_var (Block 0 item 0-8 remap)
- #046 â€” BEDROCK_EXTRA_PARAMS_HEADERS (Block 0 item 0-3 remap)
- #047 â€” BedrockClient.count_tokens

### Validation
- 459 pass + 5 skipped (was 442 + 4 at end of Block 0; +17 pass + 1 skip).
- verify_ship_zip.py: PASS (100 files / 262.4 KB / 38%).
- 1 T5 test gated by `RUN_REAL_BEDROCK=1` (~$0.005); to be run as part
  of Block J real-Bedrock smoke gate so Block B doesn't burn API budget
  per local pytest.

### PS_problems addressed
- **PS#5 (session cost not persisted)**: TokenTracker has `restore()`
  reconstructor; Block B+ wires it to SessionManager `/resume`.
- **PS#6 (budget read from wrong source)**: `_TOKENS.add` always reads
  CONFIG.session_cost_limit; Block B+ acceptance test
  test_tokens_singleton_is_budget_source pins this.

## ADR-020 â€” Block 0 (v5.0.1): `sagemaker_agent.py` shim + notebook smoke gate

**Date**: 2026-05-02
**Phase ID**: v5.0.1 Block 0
**Status**: ACCEPTED

### Context
v5.0.0 reorganized the v4 monolith into nested packages (`runtime/`, `core/`,
`agent/`, `ui/`, `tools/`, `skills/`, `subagent/`, `security/`, `prompt/`).
The Phase-11 notebook (`chat.ipynb`) imports from `entry`. v4's notebook
imports from `sagemaker_agent`. v5.0.1 hard-constraint #2 requires that v4's
canonical `chat.ipynb` continues to work unchanged on v5 via a shim â€” the
notebook should not need to know about the v5 reorg.

### Options
1. **Drop-in shim** (chosen): tiny `sagemaker_agent.py` at the agent root that
   re-exports `entry`'s public surface. v4's `from sagemaker_agent import â€¦`
   line resolves; everything else stays in its v5 module.
2. **Replace v5 chat.ipynb with v4's verbatim**: most faithful to constraint
   #2 but pulls in v4 widgets that depend on Block-B+ (`session_cost_limit`)
   and Block-D (slash commands) features not yet present at Block 0. Defers
   to Block E+F.
3. **Move all v5 surface back to a top-level `sagemaker_agent` module**:
   undoes the Phase-2..11 file-per-section structure. Violates constraint
   #5 (minimum file count) and constraint #6 (architecture-first).

### Decision
Option 1. Block 0 ships a 30-LOC shim that re-exports `Agent`, `BEDROCK_MODELS`,
`CONFIG`, `IterationBudget`, `SkillManager`, and `create_chat_ui` from `entry`.
v5's existing `chat.ipynb` is left untouched at Block 0; full notebook-shape
restoration to v4 canonical is Block E+F territory (per Wave-3
COMBINED_ARCHITECTURE.md).

### Rationale
- Smallest possible surface that satisfies constraint #2 at Block 0 boundary.
- Zero impact on Phase 1-13 module structure.
- v4's `from sagemaker_agent import {BEDROCK_MODELS, CONFIG, create_chat_ui}`
  line works literally â€” verified by `test_smoke_imports` and
  `test_v4_import_compat`.
- The shim is implementation-free; it cannot drift from v5 internals because
  it re-binds, never re-implements.

### Runnable-fidelity impact
None. This shim is v4-compat, not Runnable-derived.

### Affected files
- NEW: `compact_v5/MAIN/agent/sagemaker_agent.py` (shim)
- NEW: `compact_v5/MAIN/agent/tests/integration/test_block0_shim.py` (5 tests)
- UPDATED: `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` (row #038)
- UPDATED: `compact_v5/_status/V5_BUILD_STATUS.md` (Block 0 done; next = smoke gate / Block B)

### Linked port-log rows
- #038 â€” Block 0 shim.

### Validation
- 5/5 Block 0 tests green (TEST_DESIGN Â§Block 0).
- Full pytest 442 passed + 4 skipped (was 437 + 4; +5 new from Block 0).
- `verify_ship_zip.py`: PASS.
- Codex AXIS A/B/C: APPROVE (review at `_status/codex_reviews/block-0.md`).

### Notes / known scope remaps (constraint #3 â€” no deferrals)

SYNTHESIS_MASTER.md Â§Block 0 (lines 32-47) tags 9 additional items
"Block 0" because that is where their PORT_LOG row originates. All 9 are
**ported, not dropped** â€” but their *implementation* lands in the Block
that architecturally owns the touched module. Each item below has an
explicit landing Block + a test gate where its lock test runs. This
table is the no-deferrals contract.

| Item | Capability | LOC | Lands in Block | Implementation site (target file) | Lock test (Block where it runs) |
|---|---|---|---|---|---|
| 0-1 | SYSTEM_PROMPT verbatim re-export | 0 (doc) | Block 0 | `prompt/*.md` (Phase 6, present) + this PORT_LOG row #038 | `test_v4_import_compat` (Block 0) |
| 0-2 | `getSessionStartDate()` + `getLocalMonthYear()` (cache-stable date) | 15 | **Block E+F** | `prompt/env_block.py` (formatter for `prompt/env_block.md`) | `test_env_block_uses_month_year_not_iso_date` (Block E+F) |
| 0-3 | `BEDROCK_EXTRA_PARAMS_HEADERS` Set | 5 | **Block B** | `runtime/bedrock_client.py` (constant + reference at invoke site) | `test_extra_params_in_body_not_headers` (Block B) |
| 0-4 | env block format (Windows-shell hint, OS version, Notes appendix) | 30 | **Block E+F** | `prompt/env_block.md` + `prompt/env_block.py` | `test_env_block_includes_shell_hint_and_notes` (Block E+F) |
| 0-5 | `getScratchpadInstructions()` per-session scratchpad dir | 30 | **Block C** | `security/scratchpad.py` + allowlist update + `prompt/scratchpad.md` | `test_scratchpad_dir_pre_allowlisted_and_gc` (Block C) |
| 0-6 | `getKnowledgeCutoff(modelId)` Sonnet 4.6 / Haiku 4.5 cutoffs | 5 | **Block E+F** | `prompt/env_block.py` (cutoff lookup table) | `test_env_block_emits_model_specific_knowledge_cutoff` (Block E+F) |
| 0-7 | `cleanupRegistry` graceful-shutdown for SIGINT / atexit | 15 | **Block B+** | `runtime/cleanup_registry.py` + `runtime/session.py` flush hook | `test_cleanup_registry_flushes_on_atexit_and_sigint` (Block B+) |
| 0-8 | `validateBoundedIntEnvVar` env-validation helper | 30 | **Block B** | `runtime/env_validation.py` (used by Config dataclass numeric loaders) | `test_env_validation_clamps_and_rejects_bad_input` (Block B) |
| 0-9 | Feature-flag fail-closed at import boundary | 30 | **Block B+** | `runtime/feature_flags.py` (returns False for banned modules) + `entry.py` import-time guard | `test_banned_module_imports_fail_closed` (Block B+) |
| 0-10 | `_scan_for_prompt_injection` + `_INJECTION_PATTERNS` (v4-native) | 40 | **Block C** | `security/injection_scanner.py` (v4 verbatim port from sagemaker_agent.py:7509-7541) | `test_injection_scanner_v4_native` (Block C; already in TEST_DESIGN Â§Block C) |

Codex AXIS C (Block 0 review #1) flagged this remap as UNDECLARED_PATTERN
when only stated in prose; the table above declares it concretely. Each
target Block's review (when it lands) must verify (a) the row above is
honored, (b) the lock test exists, and (c) the SYNTHESIS_MASTER Â§3 row
for that item references the implementing Block. Plan-level cross-link
added to `_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` Block 0 table head
note.

web search: 
web search: 
codex
I’ve found the six new regression tests and validated they target all four iter-1 findings. I’m now taking exact line references for each fix and checking for any new regressions before issuing the final `APPROVE` decision.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"_warned_over_budget|session_cost >=|def run\\(\" compact_v5/MAIN/agent/core/query_engine.py" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "find_spec|_BANNED_PACKAGE_NAMES|origin.endswith|ImportError" compact_v5/MAIN/agent/entry.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "RLock|_lock =|def _signal_handler|def register" compact_v5/MAIN/agent/runtime/cleanup_registry.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "test_cost_warning_resets_each_run|test_cost_warning_fires_on_exact_100_percent|test_entry_import_succeeds_when_no_mcp_package_present|test_entry_guard_raises_if_banned_package_reintroduced|test_cleanup_registry_uses_rlock_for_signal_safety|test_block_b_plus_remap_table_present_in_adr_022" compact_v5/MAIN/agent/tests/integration/test_block_b_plus.py' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"Notes / known scope remaps \\(Block B\\+ items B\\+3\\.\\.B\\+6\\)|\\| B\\+3 \\||\\| B\\+4 \\||\\| B\\+5 \\||\\| B\\+6 \\|\" compact_v5/_status/V5_DESIGN_DECISIONS.md" in D:\Github\sagemaker-coding-agent
 succeeded in 481ms:
30:_BANNED_PACKAGE_NAMES = ("mcp",)
31:for _banned in _BANNED_PACKAGE_NAMES:
32:    if _importlib_util.find_spec(_banned) is not None:
37:        _spec = _importlib_util.find_spec(_banned)
39:        if "MAIN/agent" in _origin.replace("\\", "/") or _origin.endswith(
42:            raise ImportError(

 succeeded in 536ms:
190:    def run(
216:        self._warned_over_budget = False
363:                if limit > 0 and _TOKENS.session_cost >= limit:
364:                    if not getattr(self, "_warned_over_budget", False):
369:                        self._warned_over_budget = True

 succeeded in 533ms:
24:# Codex Block-B+ finding #3 (MEDIUM) lock: use RLock so a SIGINT
28:_lock = threading.RLock()
33:def register(callback: Callable[[], None]) -> None:
68:def _signal_handler(_signum, _frame):

 succeeded in 548ms:
1229:### Notes / known scope remaps (Block B+ items B+3..B+6)
1238:| B+3 | 4-line cost block format (R11 N10) | 15 | **Block I** (UI/widgets) | `ui/widgets.py:CostWidget.render_html` (4-line block: total / per-model / per-agent / cache) | `test_cost_widget_renders_4_line_block` (Block I) |
1239:| B+4 | Local OTel-style counters (R11 N11) | 25 | **Block I** | `runtime/tokens.py:TokenTracker.get_otel_counters()` (local SQLite/JSON only — never external endpoint per Bedrock-only constraint) | `test_otel_counters_emitted_locally_only` (Block I) |
1240:| B+5 | Recursive advisor sub-cost accounting (R11 N12) | 30 | **Block A** (Compactor) | `core/compactor.py` calls `TOKENS.add(usage, agent_kind="advisor")` for the auxiliary compaction-summary model | `test_advisor_sub_cost_attributed` (Block A) |
1241:| B+6 | contextWindow refresh on every cost update (R11 N13) | 5 | **Block I** | hook `IterationBudgetWidget.update()` to fire on every TOKENS.add (per-update refresh) | `test_iteration_budget_widget_refreshes_on_token_add` (Block I) |

 succeeded in 557ms:
437:def test_cost_warning_resets_each_run(monkeypatch):
474:def test_cost_warning_fires_on_exact_100_percent(monkeypatch):
501:def test_entry_import_succeeds_when_no_mcp_package_present():
510:def test_entry_guard_raises_if_banned_package_reintroduced(tmp_path, monkeypatch):
529:def test_cleanup_registry_uses_rlock_for_signal_safety():
552:def test_block_b_plus_remap_table_present_in_adr_022():

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$p='"'compact_v5/MAIN/agent/entry.py'; "'$i=0; Get-Content $p | ForEach-Object { $i++; if($i -ge 28 -and $i -le 44){ '"'{0,4}: {1}' -f "'$i, $_ } }' in D:\Github\sagemaker-coding-agent
 succeeded in 394ms:
  28: import importlib.util as _importlib_util
  29: 
  30: _BANNED_PACKAGE_NAMES = ("mcp",)
  31: for _banned in _BANNED_PACKAGE_NAMES:
  32:     if _importlib_util.find_spec(_banned) is not None:
  33:         # Heuristic: filter out external packages that happen to share
  34:         # the name (a v5 package would live under MAIN/agent/<name>/).
  35:         # Only raise when the spec resolves to a path inside this agent
  36:         # package, indicating an in-tree re-introduction.
  37:         _spec = _importlib_util.find_spec(_banned)
  38:         _origin = getattr(_spec, "origin", "") or ""
  39:         if "MAIN/agent" in _origin.replace("\\", "/") or _origin.endswith(
  40:             f"/{_banned}/__init__.py"
  41:         ):
  42:             raise ImportError(
  43:                 f"v5.0.1 hard constraint: banned subsystem '{_banned}' "
  44:                 f"has been re-introduced at {_origin!r}. See "

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$p='"'compact_v5/MAIN/agent/tests/integration/test_block_b_plus.py'; "'$i=0; Get-Content $p | ForEach-Object { $i++; if($i -ge 501 -and $i -le 528){ '"'{0,4}: {1}' -f "'$i, $_ } }' in D:\Github\sagemaker-coding-agent
 succeeded in 408ms:
 501: def test_entry_import_succeeds_when_no_mcp_package_present():
 502:     """Codex iter-1 finding #2 (MEDIUM) lock: entry.py's import-boundary
 503:     guard must NOT raise when the v5 tree has no banned packages.
 504:     (We just imported entry successfully if this test is even running.)"""
 505:     import entry
 506:     assert entry is not None
 507:     assert hasattr(entry, "Agent")
 508: 
 509: 
 510: def test_entry_guard_raises_if_banned_package_reintroduced(tmp_path, monkeypatch):
 511:     """Lock for finding #2: simulate a re-introduced `mcp/` package by
 512:     pointing importlib at a tmp directory that contains one. The guard
 513:     in entry.py must reject this import path.
 514: 
 515:     We can't easily re-import entry.py against an alternate path, so we
 516:     test the guard's logic by crafting a fake spec via importlib and
 517:     verifying the heuristic catches an in-tree path."""
 518:     import importlib.util as iu
 519: 
 520:     # Simulate the discovered spec.origin string the guard checks.
 521:     fake_origin = str(tmp_path / "MAIN" / "agent" / "mcp" / "__init__.py")
 522:     # The guard: `"MAIN/agent" in _origin.replace("\\", "/") or _origin.endswith("/mcp/__init__.py")`
 523:     normalized = fake_origin.replace("\\", "/")
 524:     assert "MAIN/agent" in normalized
 525:     # And the explicit name-suffix branch:
 526:     assert normalized.endswith("/mcp/__init__.py")
 527: 
 528: 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$p='"'compact_v5/MAIN/agent/core/query_engine.py'; "'$i=0; Get-Content $p | ForEach-Object { $i++; if(($i -ge 206 -and $i -le 220) -or ($i -ge 356 -and $i -le 372)){ '"'{0,4}: {1}' -f "'$i, $_ } }' in D:\Github\sagemaker-coding-agent
 succeeded in 419ms:
 206:         # Codex Phase-08 finding (high): the discovered-tool set MUST be reset
 207:         # at each run() entry. The contract docstring promises "fresh each
 208:         # user message" but the previous version persisted it across runs,
 209:         # which would silently widen the per-turn tools= payload on later
 210:         # runs. Lock test: test_discovered_tools_reset_between_runs.
 211:         self._discovered_tool_names = set()
 212:         # Block B+ Codex finding #1 (HIGH) lock: reset the per-run cost
 213:         # over-budget warning flag so subsequent run() calls re-emit the
 214:         # warning once each (instead of staying silent for the lifetime
 215:         # of the engine).
 216:         self._warned_over_budget = False
 217: 
 218:         # Append user turn (Bedrock requires alternation; merge into trailing
 219:         # user if needed â€” matches v4 sagemaker_agent.py:8744).
 220:         if self.messages and self.messages[-1].get("role") == "user":
 356:                 # NOT a hard halt â€” per user 2026-05-03 update to plan v3,
 357:                 # v5 matches v4 UX: warn and continue. True hard halt is at
 358:                 # cloud-budget level (AWS Budget Action / GCP).
 359:                 from runtime.config import CONFIG as _CFG
 360:                 limit = getattr(_CFG, "session_cost_limit", 0.0)
 361:                 # Block B+ Codex finding #1 lock: `>=` so exact-100% trips
 362:                 # the warning (`>` would skip parity-100% cases).
 363:                 if limit > 0 and _TOKENS.session_cost >= limit:
 364:                     if not getattr(self, "_warned_over_budget", False):
 365:                         output_fn(
 366:                             f"[Cost ${_TOKENS.session_cost:.4f} passed "
 367:                             f"budget ${limit:.2f} â€” continuing.]"
 368:                         )
 369:                         self._warned_over_budget = True
 370:             except Exception:
 371:                 pass
 372: 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$p='"'compact_v5/MAIN/agent/runtime/cleanup_registry.py'; "'$i=0; Get-Content $p | ForEach-Object { $i++; if($i -ge 24 -and $i -le 31){ '"'{0,4}: {1}' -f "'$i, $_ } }' in D:\Github\sagemaker-coding-agent
 succeeded in 406ms:
  24: # Codex Block-B+ finding #3 (MEDIUM) lock: use RLock so a SIGINT
  25: # arriving while register()/_run_all() holds the lock can re-enter
  26: # without deadlocking. The signal handler calls _run_all() which
  27: # acquires the same lock â€” non-reentrant Lock would deadlock.
  28: _lock = threading.RLock()
  29: _callbacks: List[Callable[[], None]] = []
  30: _installed = False
  31: 

codex
1. Finding #1 (cost-warning state leak + `>` vs `>=`): **Yes** — `run()` now resets `self._warned_over_budget` at entry and the warning check uses `>=`, covering exact-100% and per-run re-emission ([query_engine.py:216](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/query_engine.py:216), [query_engine.py:363](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/query_engine.py:363)).

2. Finding #2 (import-boundary wiring): **No** — the guard is wired, but the condition `or _origin.endswith("/mcp/__init__.py")` can also match external `mcp` installs despite the comment claiming external packages are filtered, so this is not cleanly constrained to in-tree reintroduction ([entry.py:39](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/entry.py:39), [entry.py:40](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/entry.py:40)); the lock test also doesn’t execute the guard path ([test_block_b_plus.py:510](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_block_b_plus.py:510)).

3. Finding #3 (cleanup_registry signal/lock re-entrancy): **Yes** — module lock is now `threading.RLock`, which addresses same-thread re-entry from signal handler path ([cleanup_registry.py:28](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/runtime/cleanup_registry.py:28)).

4. Finding #4 (B+3..B+6 remap + 100% warn doc drift): **Yes** — ADR-022 now has explicit B+3..B+6 remap rows, and the integration suite includes lock coverage for that table and 100%-warning behavior ([V5_DESIGN_DECISIONS.md:1229](D:/Github/sagemaker-coding-agent/compact_v5/_status/V5_DESIGN_DECISIONS.md:1229), [test_block_b_plus.py:474](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_block_b_plus.py:474), [test_block_b_plus.py:552](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_block_b_plus.py:552)).

FINAL: **APPROVE_WITH_FIXES**.

New issue:
1. MEDIUM: Import-boundary guard can false-positive on external `mcp` packages due to overly broad suffix check; tighten to in-repo path detection only.
2026-05-03T02:09:48.690364Z ERROR codex_core::session: failed to record rollout items: thread 019deb98-1f44-7252-9cb8-00013d841046 not found
tokens used
26,067
1. Finding #1 (cost-warning state leak + `>` vs `>=`): **Yes** — `run()` now resets `self._warned_over_budget` at entry and the warning check uses `>=`, covering exact-100% and per-run re-emission ([query_engine.py:216](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/query_engine.py:216), [query_engine.py:363](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/query_engine.py:363)).

2. Finding #2 (import-boundary wiring): **No** — the guard is wired, but the condition `or _origin.endswith("/mcp/__init__.py")` can also match external `mcp` installs despite the comment claiming external packages are filtered, so this is not cleanly constrained to in-tree reintroduction ([entry.py:39](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/entry.py:39), [entry.py:40](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/entry.py:40)); the lock test also doesn’t execute the guard path ([test_block_b_plus.py:510](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_block_b_plus.py:510)).

3. Finding #3 (cleanup_registry signal/lock re-entrancy): **Yes** — module lock is now `threading.RLock`, which addresses same-thread re-entry from signal handler path ([cleanup_registry.py:28](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/runtime/cleanup_registry.py:28)).

4. Finding #4 (B+3..B+6 remap + 100% warn doc drift): **Yes** — ADR-022 now has explicit B+3..B+6 remap rows, and the integration suite includes lock coverage for that table and 100%-warning behavior ([V5_DESIGN_DECISIONS.md:1229](D:/Github/sagemaker-coding-agent/compact_v5/_status/V5_DESIGN_DECISIONS.md:1229), [test_block_b_plus.py:474](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_block_b_plus.py:474), [test_block_b_plus.py:552](D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_block_b_plus.py:552)).

FINAL: **APPROVE_WITH_FIXES**.

New issue:
1. MEDIUM: Import-boundary guard can false-positive on external `mcp` packages due to overly broad suffix check; tighten to in-repo path detection only.
