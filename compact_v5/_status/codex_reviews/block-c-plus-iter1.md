OpenAI Codex v0.125.0 (research preview)
--------
workdir: D:\Github\sagemaker-coding-agent
model: gpt-5.3-codex
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, C:\Users\winst\.codex\memories]
reasoning effort: high
reasoning summaries: none
session id: 019debc2-e747-7a53-be10-0911d65c9105
--------
user
Review Block C+ of v5.0.1: approval/diff dispatch + rate limits + ipywidgets fallback + Block-C UI helper wiring.

Block C+ ships PermissionDialog (sticky always-allow, reason prompt, ipywidgets+text-fallback, 60s watchdog, non-TTY defaults-to-deny) + RateLimiter (sliding-window per-minute + per-session caps) + Block-C UI remaps (cd+git C-11 / multi-cd C-12 / pipe-segment C-13 / comment-label C-14 surfaced via render_warnings).

Read these 3 files:
- compact_v5/MAIN/agent/ui/approval_dialog.py (PermissionDialog + RateLimiter + ApprovalResult)
- compact_v5/MAIN/agent/core/query_engine.py (rate-limit at run() entry ~line 235; approval gate before dispatch ~line 510-560)
- compact_v5/MAIN/agent/tests/integration/test_block_c_plus.py (14 lock tests)

3-axis review:
AXIS A: errors / regressions / security (race in CONFIG._always_allowed; TOCTOU in rate limiter; non-TTY default-deny). Verdict: PASS / CHANGES_REQUESTED / BLOCKER.
AXIS B: v5 fit (Phase-4 ADR-010 commitment fulfilled; Block-C UI remap closure). Verdict: FAITHFUL / FAITHFUL-WITH-JUSTIFIED-ADAPTATION / DRIFTED.
AXIS C: covers TEST_DESIGN §Block C+ 7 items + Block-C UI remap (C-11/C-12/C-13/C-14)? Anything UNDECLARED_PATTERN?

Tests: 525 pass + 5 skip (was 511; +14 net new).

FINAL: APPROVE | APPROVE_WITH_FIXES | REJECT.

codex
I’ll inspect the three requested files and the 14 new integration tests, then I’ll give a strict 3-axis verdict with concrete findings (security/regression risks first) and a final approve decision.
web search: 
web search: 
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/ui/approval_dialog.py'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/tests/integration/test_block_c_plus.py'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/core/query_engine.py'" in D:\Github\sagemaker-coding-agent
 succeeded in 533ms:
"""Block C+ â€” PermissionDialog (approval flow + always-allow + reason prompt).

Renders a per-tool approval dialog when CONFIG.require_tool_approval=True
AND the tool's `requires_approval=True`. The dialog surfaces:
  - Tool name + sanitised parameters
  - Optional diff preview (edit_file / write_file via ui/diff_widget)
  - Optional reason string from tool_use args (Block C+ richer feature)
  - Block C UI-only helper warnings: cd+git compound bare-repo (C-11),
    multi-cd (C-12), per-pipe-segment destructive (C-13), bash comment-
    label (C-14) â€” all surfaced when bash is the dispatched tool
  - Three buttons: Approve / Deny / Always allow (per-tool sticky)

Block C+ headless contract: when ipywidgets is unavailable, the dialog
falls back to a synchronous text-mode `ask_user`-style prompt with a
60-second watchdog timeout.

PORT_LOG: see #064.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ApprovalResult:
    """The outcome of a single approval prompt."""

    approved: bool
    always_allow: bool = False  # if True, future calls to same tool skip the dialog
    reason: str = ""             # caller-supplied rationale for the decision
    timed_out: bool = False


@dataclass
class PermissionDialog:
    """Per-tool approval dialog. ipywidgets-aware with text fallback.

    Block C+ adds three features over the Phase-9 base:
      1. always_allow toggle â€” sticky per tool name, lives in
         CONFIG._always_allowed (initialized lazily).
      2. reason prompt â€” surfaces the tool_use input's `reason` field
         when present so the user understands intent before approving.
      3. Block-C bash safety annotations â€” cd+git, multi-cd,
         pipe-segment destructive warnings displayed inline.
    """

    tool_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    diff_html: Optional[str] = None
    reason: str = ""

    # Watchdog timeout for headless / text-mode fallback.
    timeout_seconds: int = 60

    # Optional callable used by tests to short-circuit the modal loop.
    _override_decision: Optional[Callable[[], ApprovalResult]] = None

    # --------------------------------------------------------
    # Decision driver
    # --------------------------------------------------------

    def prompt(self) -> ApprovalResult:
        """Show the dialog + block until decided (or timed out).

        Resolution order (sticky FIRST so always-allow short-circuits
        even when callers pass an `_override_decision`):
          1. CONFIG._always_allowed[tool_name] â€” auto-approve if sticky.
          2. `_override_decision` â€” used by unit tests to inject answers.
          3. ipywidgets dialog (Approve / Deny / Always allow buttons).
          4. Text-mode fallback (ask_user-style) with watchdog timeout.
        """
        # 1) sticky always-allow (Block-C+ Codex finding lock test)
        from runtime.config import CONFIG
        if not hasattr(CONFIG, "_always_allowed"):
            CONFIG._always_allowed = {}
        if CONFIG._always_allowed.get(self.tool_name):
            return ApprovalResult(approved=True, always_allow=True,
                                  reason="sticky: tool was previously Always-allowed")

        # 2) test override
        if self._override_decision is not None:
            return self._override_decision()

        # 3) ipywidgets path
        try:
            from ui.chat_ui import _IPYWIDGETS_OK
        except Exception:
            _IPYWIDGETS_OK = False
        if _IPYWIDGETS_OK:
            return self._prompt_widgets()

        # 4) text-mode fallback (ask_user style with watchdog)
        return self._prompt_text_mode()

    # --------------------------------------------------------
    # Annotation: Block-C bash safety hooks
    # --------------------------------------------------------

    def render_warnings(self) -> List[str]:
        """Return human-readable warnings to display alongside the dialog.

        Block C UI-only helpers (C-11/C-12/C-13/C-14) surface here when
        the dispatched tool is `bash`. Per ADR-023 Â§Notes / known scope
        remaps (Block C UI-only helpers â†’ Block C+).
        """
        warnings: List[str] = []
        if self.tool_name != "bash":
            return warnings
        cmd = self.parameters.get("command", "")
        if not cmd:
            return warnings
        try:
            from security.bash_safety import (
                destructive_command_warning,
                has_cd_git_compound_with_bare_repo,
                has_multiple_cd,
                pipe_segment_permission_check,
                extract_bash_comment_label,
            )
            d = destructive_command_warning(cmd)
            if d:
                warnings.append(f"âš  destructive: {d}")
            if has_cd_git_compound_with_bare_repo(cmd):
                warnings.append("âš  cd into bare git repo + git command (fsmonitor risk)")
            if has_multiple_cd(cmd):
                warnings.append("âš  multiple cd's â€” chained directory changes")
            for seg_warn in pipe_segment_permission_check(cmd):
                warnings.append(f"âš  pipe-segment destructive: {seg_warn}")
            label = extract_bash_comment_label(cmd)
            if label:
                warnings.append(f"label: {label}")
        except Exception:
            pass
        return warnings

    # --------------------------------------------------------
    # ipywidgets dialog
    # --------------------------------------------------------

    def _prompt_widgets(self) -> ApprovalResult:
        """Block on three-button ipywidgets dialog. Best-effort render."""
        try:
            import ipywidgets as widgets
            from IPython.display import display
        except Exception:
            return self._prompt_text_mode()

        decision: Dict[str, Any] = {"result": None}

        def on_approve(_btn):
            decision["result"] = ApprovalResult(approved=True)

        def on_deny(_btn):
            decision["result"] = ApprovalResult(approved=False, reason="user denied")

        def on_always(_btn):
            from runtime.config import CONFIG
            if not hasattr(CONFIG, "_always_allowed"):
                CONFIG._always_allowed = {}
            CONFIG._always_allowed[self.tool_name] = True
            decision["result"] = ApprovalResult(
                approved=True, always_allow=True,
                reason="user clicked Always-allow",
            )

        approve_btn = widgets.Button(description="Approve", button_style="success")
        deny_btn = widgets.Button(description="Deny", button_style="danger")
        always_btn = widgets.Button(description="Always allow this tool",
                                    button_style="warning")
        approve_btn.on_click(on_approve)
        deny_btn.on_click(on_deny)
        always_btn.on_click(on_always)

        header = f"<b>Approve `{self.tool_name}`?</b>"
        if self.reason:
            header += f"<br/><i>Reason from model:</i> {self.reason}"
        warning_lines = self.render_warnings()
        warning_html = "<br/>".join(warning_lines) if warning_lines else ""
        body_parts = [widgets.HTML(value=header)]
        if warning_html:
            body_parts.append(widgets.HTML(value=warning_html))
        if self.diff_html:
            body_parts.append(widgets.HTML(value=self.diff_html))
        body_parts.append(widgets.HBox([approve_btn, deny_btn, always_btn]))
        panel = widgets.VBox(body_parts)
        display(panel)

        # Spin until a button clicked or watchdog fires.
        deadline = time.time() + self.timeout_seconds
        while decision["result"] is None and time.time() < deadline:
            time.sleep(0.1)
        if decision["result"] is None:
            return ApprovalResult(approved=False, timed_out=True,
                                  reason="watchdog timeout")
        return decision["result"]

    # --------------------------------------------------------
    # Text-mode fallback (ask_user-style)
    # --------------------------------------------------------

    def _prompt_text_mode(self) -> ApprovalResult:
        """Headless fallback: print dialog + read stdin with watchdog."""
        import sys

        print(f"\n=== Approve tool `{self.tool_name}`? ===")
        if self.reason:
            print(f"Model reason: {self.reason}")
        for w in self.render_warnings():
            print(f"  {w}")
        if self.diff_html:
            print("[diff preview available â€” open in widget host to view]")
        print(f"Parameters (sanitised): {self._sanitised_params()}")
        print(f"Reply (a)pprove / (d)eny / (A)lways allow [60s timeout]:")

        # When stdin is not a TTY (notebook headless), default to deny so
        # we never silently auto-approve.
        if not sys.stdin.isatty():
            logging.warning(
                "PermissionDialog: stdin not a TTY; defaulting to DENY"
            )
            return ApprovalResult(approved=False, timed_out=True,
                                  reason="non-tty fallback")

        # Watchdog â€” readline doesn't natively support timeout; use a
        # signal-based timer where supported, else just block + record
        # the wall time.
        try:
            import select
            t_start = time.time()
            while True:
                if select.select([sys.stdin], [], [], 1)[0]:
                    line = sys.stdin.readline().strip()
                    if line in ("a", "approve", "y", "yes"):
                        return ApprovalResult(approved=True)
                    if line in ("A", "always"):
                        from runtime.config import CONFIG
                        if not hasattr(CONFIG, "_always_allowed"):
                            CONFIG._always_allowed = {}
                        CONFIG._always_allowed[self.tool_name] = True
                        return ApprovalResult(approved=True, always_allow=True,
                                              reason="text-mode Always-allow")
                    return ApprovalResult(approved=False, reason="user denied")
                if time.time() - t_start > self.timeout_seconds:
                    return ApprovalResult(approved=False, timed_out=True,
                                          reason="watchdog timeout")
        except (OSError, ValueError):
            # select.select unsupported (e.g. Windows non-socket).
            line = sys.stdin.readline().strip()
            if line in ("a", "approve", "y", "yes"):
                return ApprovalResult(approved=True)
            if line in ("A", "always"):
                from runtime.config import CONFIG
                if not hasattr(CONFIG, "_always_allowed"):
                    CONFIG._always_allowed = {}
                CONFIG._always_allowed[self.tool_name] = True
                return ApprovalResult(approved=True, always_allow=True)
            return ApprovalResult(approved=False, reason="user denied")

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    def _sanitised_params(self) -> Dict[str, Any]:
        """Truncate big strings; redact secret-looking keys."""
        out: Dict[str, Any] = {}
        for k, v in self.parameters.items():
            if any(s in k.lower() for s in (
                "password", "secret", "key", "token", "credential",
            )):
                out[k] = "[REDACTED]"
            elif isinstance(v, str) and len(v) > 200:
                out[k] = f"[{len(v)} chars]"
            else:
                out[k] = v
        return out


# ============================================================
# Rate limiter (Block C+ â€” port of v4 :8731-8740)
# ============================================================

class RateLimiter:
    """Sliding-window message rate limiter.

    100 user messages per 60s window per v4 default + per-session cap.
    Used at QueryEngine.run() entry. When rate exceeded, run() returns
    a clear error result without spending iteration budget.
    """

    def __init__(self, max_per_minute: int = 100, max_per_session: int = 1500):
        self.max_per_minute = max(1, int(max_per_minute))
        self.max_per_session = max(1, int(max_per_session))
        self._timestamps: List[float] = []
        self._session_count = 0

    def check(self) -> Optional[str]:
        """Return None if OK, or an error message if rate-limited.

        Caller must call this BEFORE any work that consumes budget.
        """
        now = time.time()
        # Drop stamps older than 60s.
        cutoff = now - 60.0
        self._timestamps = [t for t in self._timestamps if t >= cutoff]
        if len(self._timestamps) >= self.max_per_minute:
            wait = int(60 - (now - self._timestamps[0]))
            return (
                f"Rate limit hit: {self.max_per_minute} messages per minute. "
                f"Try again in ~{max(1, wait)}s."
            )
        if self._session_count >= self.max_per_session:
            return (
                f"Session message cap hit ({self.max_per_session}). "
                "Start a new session to continue."
            )
        self._timestamps.append(now)
        self._session_count += 1
        return None

    def reset(self) -> None:
        self._timestamps = []
        self._session_count = 0


__all__ = ["ApprovalResult", "PermissionDialog", "RateLimiter"]

 succeeded in 569ms:
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
        # Block C â€” exec-limit gate (PS#7 fix) + repetition detector.
        # Counters live on the QueryEngine. Codex iter-1 finding #3:
        # unconditional reset at run() entry so counters DON'T leak
        # across run() calls (the v4 contract; sub-agent dispatch is
        # the only legitimate cross-run sharing path, handled via
        # parent_engine forwarding).
        self._exec_call_count = 0  # bash + python_exec only
        self._recent_tool_calls: list = []  # [(name, args_hash), ...]

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

                # Block C â€” exec-limit gate (PS#7 fix). Only bash +
                # python_exec count toward this limit. v4 verbatim
                # message at sagemaker_agent.py:9482-9489 â€” preserved
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

                # Block C â€” repetition detector. Same (tool_name,
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

                # Block C â€” JSON-repair tool args before dispatch. If
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

                # Block C+ â€” approval gate. When CONFIG.require_tool_approval
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
                            _dlg = PermissionDialog(
                                tool_name=call.name,
                                parameters=_repaired_input or {},
                                reason=_model_reason,
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
                            # Approved â€” sticky if user clicked Always.
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
                # `parent_engine` is passed for Phase 9 task tool â€” the sub-agent
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
                except Exception as exc:  # noqa: BLE001 â€” surface to model
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

        Order: thinking blocks (if any) â†’ text â†’ tool_use. The thinking
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
        user turn â€” it does not mutate `self.messages`, so it does not leak
        into subsequent turns once the model has loaded the schemas it needs.
        """
        if not deferred_names:
            return messages
        reminder = (
            "<system-reminder>\n"
            "The following deferred tools are available via tool_search. Their schemas "
            "are NOT loaded â€” calling them directly will fail. Use tool_search with "
            "query \"select:<name>[,<name>...]\" to load tool schemas before calling them:\n"
            + "\n".join(sorted(deferred_names))
            + "\n</system-reminder>"
        )
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

 succeeded in 570ms:
"""Block C+ â€” Approval/diff dispatch + rate limits + ipywidgets fallback.

Tests per TEST_DESIGN.md Â§Block C+ (7 tests) plus 4 lock tests for the
Block C UI-only helpers (C-11/C-12/C-13/C-14) wired through the
approval flow per ADR-023 Â§Notes / known scope remaps.
"""
from __future__ import annotations

import os
import sys
import time

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


@pytest.fixture(autouse=True)
def reset_always_allowed():
    """Reset CONFIG._always_allowed between tests."""
    from runtime.config import CONFIG
    if hasattr(CONFIG, "_always_allowed"):
        CONFIG._always_allowed = {}
    yield
    if hasattr(CONFIG, "_always_allowed"):
        CONFIG._always_allowed = {}


# ============================================================
# T2 â€” Approval gate blocks until approve / unblocks on approve
# ============================================================

def test_approval_gate_blocks_until_approve():
    """Approval-required tool dispatched in non-mock mode triggers
    PermissionDialog. Approve â†’ tool runs. Deny â†’ tool blocked."""
    from ui.approval_dialog import ApprovalResult, PermissionDialog

    # Inject decision via test override; verify the dispatch path is wired.
    dlg_approve = PermissionDialog(
        tool_name="bash",
        parameters={"command": "echo hi"},
        _override_decision=lambda: ApprovalResult(approved=True),
    )
    res = dlg_approve.prompt()
    assert res.approved
    assert not res.timed_out

    dlg_deny = PermissionDialog(
        tool_name="bash",
        parameters={"command": "echo hi"},
        _override_decision=lambda: ApprovalResult(approved=False, reason="user denied"),
    )
    res = dlg_deny.prompt()
    assert not res.approved
    assert "denied" in res.reason


# ============================================================
# T2 â€” Approval dialog shows diff
# ============================================================

def test_approval_dialog_shows_diff():
    """When `diff_html` is provided, PermissionDialog includes it in
    the rendered body. We verify by exercising the headless path that
    the helper accepts + reports the diff string."""
    from ui.approval_dialog import ApprovalResult, PermissionDialog

    diff_sample = "<pre><span style='color:red'>- a</span>"
    dlg = PermissionDialog(
        tool_name="edit_file",
        parameters={"file_path": "/tmp/x.txt"},
        diff_html=diff_sample,
        _override_decision=lambda: ApprovalResult(approved=True),
    )
    # Sanity: the diff is preserved on the dialog object so the
    # widget/text-mode renderer can include it.
    assert dlg.diff_html == diff_sample
    res = dlg.prompt()
    assert res.approved


# ============================================================
# T2 â€” Per-tool always-allow (sticky)
# ============================================================

def test_approval_per_tool_always_allow():
    """Clicking Always-allow stores the tool in CONFIG._always_allowed
    and subsequent dialogs short-circuit with approved=True."""
    from runtime.config import CONFIG
    from ui.approval_dialog import ApprovalResult, PermissionDialog

    CONFIG._always_allowed = {}
    # First call: user clicks Always-allow.
    dlg1 = PermissionDialog(
        tool_name="write_file",
        parameters={"file_path": "/tmp/y"},
        _override_decision=lambda: ApprovalResult(
            approved=True, always_allow=True, reason="always",
        ),
    )
    r1 = dlg1.prompt()
    assert r1.approved and r1.always_allow

    # Manually flip the sticky flag (the override didn't go through the
    # ipywidgets handler that does this). Real flow: the widget click
    # handler sets CONFIG._always_allowed[name] = True before returning.
    CONFIG._always_allowed["write_file"] = True

    # Second call: dialog short-circuits via the sticky path.
    dlg2 = PermissionDialog(
        tool_name="write_file",
        parameters={"file_path": "/tmp/z"},
        _override_decision=lambda: pytest.fail("override should NOT fire"),
    )
    r2 = dlg2.prompt()
    assert r2.approved
    assert "sticky" in r2.reason


# ============================================================
# T2 â€” Rate limit triggers
# ============================================================

def test_rate_limit_100_per_min():
    """101st check() in 60s window returns a rate-limit error."""
    from ui.approval_dialog import RateLimiter

    rl = RateLimiter(max_per_minute=100, max_per_session=1500)
    for i in range(100):
        assert rl.check() is None, f"check {i} should pass"
    err = rl.check()
    assert err is not None
    assert "Rate limit" in err
    assert "messages per minute" in err


def test_rate_limit_session_cap():
    """Session-cap kicks in even if per-minute window allows."""
    from ui.approval_dialog import RateLimiter

    rl = RateLimiter(max_per_minute=10_000, max_per_session=5)
    for _ in range(5):
        assert rl.check() is None
    err = rl.check()
    assert err is not None
    assert "Session message cap" in err


def test_rate_limit_sliding_window():
    """Old timestamps drop out of the window after 60s."""
    from ui.approval_dialog import RateLimiter

    rl = RateLimiter(max_per_minute=2, max_per_session=100)
    rl._timestamps = [time.time() - 120, time.time() - 90]  # both > 60s old
    assert rl.check() is None
    assert rl.check() is None  # 2 in current window
    assert rl.check() is not None  # 3rd trips


# ============================================================
# T2 â€” Stop button halts run (already locked in Phase 11; sanity check)
# ============================================================

def test_stop_button_halts_run():
    """`Agent.stop()` mid-loop sets a flag; QueryEngine respects it
    on next per-turn checkpoint. Phase 11 lock; sanity check here."""
    from runtime.bedrock_client import BedrockClient
    from agent import Agent

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    a.stop()  # request stop before run() even starts
    assert a._stop_requested is True
    a.run("hi")
    # Stop request was honored; either the run exited via stop check
    # OR completed before the check (mock returns end_turn fast).


# ============================================================
# T2 â€” ipywidgets fallback when widgets unavailable
# ============================================================

def test_ipywidgets_fallback_text_mode(monkeypatch):
    """When ipywidgets is unavailable, PermissionDialog falls back to
    text mode. We force the fallback path via a monkeypatched flag."""
    from ui.approval_dialog import ApprovalResult, PermissionDialog

    # Without an override, the dialog would block on stdin. The
    # _override_decision parameter short-circuits before any rendering,
    # but we still verify the helper is callable in non-widget mode.
    dlg = PermissionDialog(
        tool_name="bash",
        parameters={"command": "ls"},
        _override_decision=lambda: ApprovalResult(approved=False, timed_out=True),
    )
    res = dlg.prompt()
    assert not res.approved
    assert res.timed_out


# ============================================================
# T2 â€” PermissionDialog reason prompt
# ============================================================

def test_permission_dialog_reason_prompt():
    """The dialog accepts a `reason` from the model's tool_use input
    and propagates it through to the rendered body."""
    from ui.approval_dialog import ApprovalResult, PermissionDialog

    dlg = PermissionDialog(
        tool_name="write_file",
        parameters={"file_path": "/tmp/q.txt", "reason": "Save config"},
        reason="Save config",
        _override_decision=lambda: ApprovalResult(approved=True),
    )
    assert dlg.reason == "Save config"
    res = dlg.prompt()
    assert res.approved


# ============================================================
# Block C remap locks: C-11/C-12/C-13/C-14 surfaced via approval
# ============================================================

def test_approval_renders_cd_git_warning():
    """C-11: cd into bare repo + git fsmonitor risk surfaced in dialog."""
    from ui.approval_dialog import PermissionDialog

    dlg = PermissionDialog(
        tool_name="bash",
        parameters={"command": "cd repo.git && git log"},
    )
    warnings = dlg.render_warnings()
    assert any("cd into bare git repo" in w for w in warnings)


def test_approval_renders_multi_cd_warning():
    """C-12: chained cd's flagged."""
    from ui.approval_dialog import PermissionDialog

    dlg = PermissionDialog(
        tool_name="bash",
        parameters={"command": "cd /tmp && cd subdir && rm file"},
    )
    warnings = dlg.render_warnings()
    assert any("multiple cd" in w for w in warnings)


def test_approval_renders_pipe_segment_warning():
    """C-13: destructive pipe segment surfaced."""
    from ui.approval_dialog import PermissionDialog

    dlg = PermissionDialog(
        tool_name="bash",
        parameters={"command": "ls -la | rm -rf /tmp/foo"},
    )
    warnings = dlg.render_warnings()
    assert any("pipe-segment" in w.lower() for w in warnings)


def test_approval_renders_bash_comment_label():
    """C-14: leading `# comment` surfaced as label."""
    from ui.approval_dialog import PermissionDialog

    dlg = PermissionDialog(
        tool_name="bash",
        parameters={"command": "# build the docs\nmake docs"},
    )
    warnings = dlg.render_warnings()
    assert any("label: build the docs" in w for w in warnings)


# ============================================================
# Sanity: rate limiter wired into QueryEngine.run() entry
# ============================================================

def test_rate_limiter_wired_into_query_engine_run(monkeypatch):
    """When the rate limit is hit, run() returns a rate_limited result
    immediately without consuming budget."""
    from runtime.bedrock_client import BedrockClient
    from core.query_engine import QueryEngine
    from ui.approval_dialog import RateLimiter

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    engine = QueryEngine(client=client, max_turns=2)
    # Force rate limit at run() entry by pre-filling the timestamps so
    # the next check() trips. max_per_minute=1, prefilled with one
    # current-time stamp -> next call fails.
    rl = RateLimiter(max_per_minute=1, max_per_session=1500)
    rl._timestamps = [time.time()]
    engine._rate_limiter = rl

    result = engine.run(
        user_message="hi", system_prompt="test", tools=[],
    )
    assert result.stop_reason == "rate_limited"
    assert "Rate limit" in (result.error or "")

codex
I’ve loaded the target files; next I’m checking surrounding runtime/config and call paths to validate the specific risks you called out (sticky-map race, limiter TOCTOU, and non-TTY deny behavior) against actual execution model.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "_always_allowed|require_tool_approval|max_user_messages_per_minute|max_user_messages_per_session|mock_mode" compact_v5/MAIN/agent/runtime compact_v5/MAIN/agent -g "*.py"' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/runtime/config.py'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "Multiple concurrent `run'"\\(\\)"'` calls|thread-safe|NOT supported" compact_v5/MAIN/agent/core/query_engine.py' in D:\Github\sagemaker-coding-agent
 succeeded in 499ms:
compact_v5/MAIN/agent\ui\approval_dialog.py:3:Renders a per-tool approval dialog when CONFIG.require_tool_approval=True
compact_v5/MAIN/agent\ui\approval_dialog.py:43:         CONFIG._always_allowed (initialized lazily).
compact_v5/MAIN/agent\ui\approval_dialog.py:70:          1. CONFIG._always_allowed[tool_name] — auto-approve if sticky.
compact_v5/MAIN/agent\ui\approval_dialog.py:77:        if not hasattr(CONFIG, "_always_allowed"):
compact_v5/MAIN/agent\ui\approval_dialog.py:78:            CONFIG._always_allowed = {}
compact_v5/MAIN/agent\ui\approval_dialog.py:79:        if CONFIG._always_allowed.get(self.tool_name):
compact_v5/MAIN/agent\ui\approval_dialog.py:161:            if not hasattr(CONFIG, "_always_allowed"):
compact_v5/MAIN/agent\ui\approval_dialog.py:162:                CONFIG._always_allowed = {}
compact_v5/MAIN/agent\ui\approval_dialog.py:163:            CONFIG._always_allowed[self.tool_name] = True
compact_v5/MAIN/agent\ui\approval_dialog.py:240:                        if not hasattr(CONFIG, "_always_allowed"):
compact_v5/MAIN/agent\ui\approval_dialog.py:241:                            CONFIG._always_allowed = {}
compact_v5/MAIN/agent\ui\approval_dialog.py:242:                        CONFIG._always_allowed[self.tool_name] = True
compact_v5/MAIN/agent\ui\approval_dialog.py:256:                if not hasattr(CONFIG, "_always_allowed"):
compact_v5/MAIN/agent\ui\approval_dialog.py:257:                    CONFIG._always_allowed = {}
compact_v5/MAIN/agent\ui\approval_dialog.py:258:                CONFIG._always_allowed[self.tool_name] = True
compact_v5/MAIN/agent\ui\chat_ui.py:174:    mock_mode: Optional[bool] = None,
compact_v5/MAIN/agent\ui\chat_ui.py:182:            `mock_mode` when supplied.
compact_v5/MAIN/agent\ui\chat_ui.py:183:        mock_mode: override CONFIG.mock_mode for the lazy path. Ignored
compact_v5/MAIN/agent\ui\chat_ui.py:196:        if mock_mode is not None:
compact_v5/MAIN/agent\ui\chat_ui.py:197:            CONFIG.mock_mode = bool(mock_mode)
compact_v5/MAIN/agent\ui\chat_ui.py:201:            mock_mode=CONFIG.mock_mode,
compact_v5/MAIN/agent/runtime\config.py:62:    mock_mode: bool = False  # Set True to test without Bedrock API
compact_v5/MAIN/agent/runtime\config.py:80:    require_tool_approval: bool = True
compact_v5/MAIN/agent/runtime\config.py:82:    max_user_messages_per_minute: int = 10
compact_v5/MAIN/agent/runtime\config.py:83:    max_user_messages_per_session: int = 150
compact_v5/MAIN/agent/runtime\config.py:209:        "thinking_budget": int, "mock_mode": bool,
compact_v5/MAIN/agent/runtime\config.py:213:        "require_auth": bool, "require_tool_approval": bool,
compact_v5/MAIN/agent/runtime\config.py:222:        "max_user_messages_per_minute": int, "max_user_messages_per_session": int,
compact_v5/MAIN/agent/runtime\bedrock_client.py:33:# botocore.config import is local-deferred so unit tests with mock_mode=True
compact_v5/MAIN/agent/runtime\bedrock_client.py:130:        mock_mode: bool = False,
compact_v5/MAIN/agent/runtime\bedrock_client.py:138:            mock_mode: if True, no real Bedrock calls; `_mock_response()` is used.
compact_v5/MAIN/agent/runtime\bedrock_client.py:146:        self.mock_mode = mock_mode
compact_v5/MAIN/agent/runtime\bedrock_client.py:149:        if mock_mode:
compact_v5/MAIN/agent/runtime\bedrock_client.py:210:        if self.mock_mode:
compact_v5/MAIN/agent/runtime\bedrock_client.py:390:          - mock_mode is True (no Bedrock contact)
compact_v5/MAIN/agent/runtime\bedrock_client.py:395:        if self.mock_mode:
compact_v5/MAIN/agent\core\query_engine.py:232:                max_per_minute=getattr(_CFG, "max_user_messages_per_minute", 100),
compact_v5/MAIN/agent\core\query_engine.py:233:                max_per_session=getattr(_CFG, "max_user_messages_per_session", 1500),
compact_v5/MAIN/agent\core\query_engine.py:554:                # Block C+ — approval gate. When CONFIG.require_tool_approval
compact_v5/MAIN/agent\core\query_engine.py:556:                # in mock_mode for tests), surface a PermissionDialog
compact_v5/MAIN/agent\core\query_engine.py:558:                # on CONFIG._always_allowed[tool.name]. Mock detection
compact_v5/MAIN/agent\core\query_engine.py:561:                # global CONFIG.mock_mode flag.
compact_v5/MAIN/agent\core\query_engine.py:564:                    getattr(_CFG_AT, "mock_mode", False)
compact_v5/MAIN/agent\core\query_engine.py:565:                    or getattr(self.client, "mock_mode", False)
compact_v5/MAIN/agent\core\query_engine.py:568:                        and getattr(_CFG_AT, "require_tool_approval", False)
compact_v5/MAIN/agent\core\query_engine.py:570:                    if not hasattr(_CFG_AT, "_always_allowed"):
compact_v5/MAIN/agent\core\query_engine.py:571:                        _CFG_AT._always_allowed = {}
compact_v5/MAIN/agent\core\query_engine.py:572:                    if not _CFG_AT._always_allowed.get(call.name):
compact_v5/MAIN/agent\runtime\bedrock_client.py:33:# botocore.config import is local-deferred so unit tests with mock_mode=True
compact_v5/MAIN/agent\runtime\bedrock_client.py:130:        mock_mode: bool = False,
compact_v5/MAIN/agent\runtime\bedrock_client.py:138:            mock_mode: if True, no real Bedrock calls; `_mock_response()` is used.
compact_v5/MAIN/agent\runtime\bedrock_client.py:146:        self.mock_mode = mock_mode
compact_v5/MAIN/agent\runtime\bedrock_client.py:149:        if mock_mode:
compact_v5/MAIN/agent\runtime\bedrock_client.py:210:        if self.mock_mode:
compact_v5/MAIN/agent\runtime\bedrock_client.py:390:          - mock_mode is True (no Bedrock contact)
compact_v5/MAIN/agent\runtime\bedrock_client.py:395:        if self.mock_mode:
compact_v5/MAIN/agent\runtime\config.py:62:    mock_mode: bool = False  # Set True to test without Bedrock API
compact_v5/MAIN/agent\runtime\config.py:80:    require_tool_approval: bool = True
compact_v5/MAIN/agent\runtime\config.py:82:    max_user_messages_per_minute: int = 10
compact_v5/MAIN/agent\runtime\config.py:83:    max_user_messages_per_session: int = 150
compact_v5/MAIN/agent\runtime\config.py:209:        "thinking_budget": int, "mock_mode": bool,
compact_v5/MAIN/agent\runtime\config.py:213:        "require_auth": bool, "require_tool_approval": bool,
compact_v5/MAIN/agent\runtime\config.py:222:        "max_user_messages_per_minute": int, "max_user_messages_per_session": int,
compact_v5/MAIN/agent\tests\integration\test_block0_shim.py:134:    mock_mode, etc.). We snapshot every CONFIG attribute before exec
compact_v5/MAIN/agent\tests\integration\test_block0_shim.py:162:    monkeypatch.setattr(CONFIG, "mock_mode", True)
compact_v5/MAIN/agent\tests\integration\test_block0_shim.py:200:    monkeypatch.setattr(CONFIG, "mock_mode", True)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:179:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:252:        mock_mode=False,
compact_v5/MAIN/agent\tests\integration\test_block_b.py:421:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:491:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:549:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:592:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=False)
compact_v5/MAIN/agent\tests\integration\test_block_b.py:620:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=False)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:190:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:219:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:342:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:450:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_block_b_plus.py:483:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:248:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\parity\test_parity_critical.py:350:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_block_c.py:35:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_block_c.py:95:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_block_c.py:469:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:23:def reset_always_allowed():
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:24:    """Reset CONFIG._always_allowed between tests."""
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:26:    if hasattr(CONFIG, "_always_allowed"):
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:27:        CONFIG._always_allowed = {}
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:29:    if hasattr(CONFIG, "_always_allowed"):
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:30:        CONFIG._always_allowed = {}
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:91:    """Clicking Always-allow stores the tool in CONFIG._always_allowed
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:96:    CONFIG._always_allowed = {}
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:110:    # handler sets CONFIG._always_allowed[name] = True before returning.
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:111:    CONFIG._always_allowed["write_file"] = True
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:174:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:288:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\parity\test_thin_slice.py:79:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:69:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:80:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:91:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:103:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:117:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:134:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:148:    monkeypatch.setattr(CONFIG, "mock_mode", True)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:166:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:213:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:264:    monkeypatch.setattr(CONFIG, "mock_mode", True)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:281:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:307:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\integration\test_notebook_smoke.py:337:    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:7:Tests are runnable without boto3 by using mock_mode=True throughout. Real
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:85:def test_bedrock_client_mock_mode_no_boto():
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:86:    """mock_mode=True allows BedrockClient instantiation without boto3 client."""
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:88:    c = BedrockClient(model_id="test", region="ap-southeast-2", mock_mode=True)
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:90:    assert c.mock_mode is True
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:96:    c = BedrockClient(model_id="test", region="ap-southeast-2", mock_mode=True)
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:108:    c = BedrockClient(model_id="test", region="ap-southeast-2", mock_mode=True)
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:158:        mock_mode=False,
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:204:        mock_mode=False,
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:245:        mock_mode=False,
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:291:        mock_mode=False,
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:356:        mock_mode=False,
compact_v5/MAIN/agent\tests\unit\test_bedrock.py:415:        ("bedrock_client_mock_mode_no_boto",            test_bedrock_client_mock_mode_no_boto),

 succeeded in 507ms:
36:The engine is thread-safe ONLY in the sense that IterationBudget is. Multiple
37:concurrent `run()` calls on the same engine are NOT supported (matches v4).

 succeeded in 514ms:
"""V5 Config â€” verbatim port from compact_v4/MAIN/agent/sagemaker_agent.py:1018-1287.

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

    # Custom commands
    custom_commands: Dict = field(default_factory=dict)

    # Permission overrides (from config file)
    permission_rules: Dict = field(default_factory=dict)

    # Agent type overrides (from config file)
    agent_overrides: Dict = field(default_factory=dict)


# ============================================================
# JSONC loader (v4 verbatim)
# ============================================================

def _strip_jsonc_comments(text: str) -> str:
    """Strip // comments from JSONC, preserving // inside quoted strings."""
    result = []
    i = 0
    in_string = False
    while i < len(text):
        ch = text[i]
        if in_string:
            result.append(ch)
            if ch == '\\' and i + 1 < len(text):
                result.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
        else:
            if ch == '"':
                in_string = True
                result.append(ch)
                i += 1
            elif ch == '/' and i + 1 < len(text) and text[i + 1] == '/':
                # Skip to end of line
                while i < len(text) and text[i] != '\n':
                    i += 1
            elif ch == '/' and i + 1 < len(text) and text[i + 1] == '*':
                # Block comment /* ... */
                i += 2
                while i + 1 < len(text) and not (text[i] == '*' and text[i + 1] == '/'):
                    i += 1
                if i + 1 < len(text):
                    i += 2  # skip */
            else:
                result.append(ch)
                i += 1
    return "".join(result)


def _load_config_file(workspace: str) -> Dict:
    """Load optional agent_config.json or agent_config.jsonc from workspace."""
    for name in ("agent_config.json", "agent_config.jsonc"):
        path = os.path.join(workspace, name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                text = _strip_jsonc_comments(text)
                return json.loads(text)
            except Exception:
                pass
    return {}


def _apply_config_file(config: Config) -> None:
    """Merge external config file into Config dataclass with type validation."""
    ext = _load_config_file(config.workspace)
    if not ext:
        return

    # Scalar fields with expected types for validation
    _SCALAR_FIELDS: Dict[str, type] = {
        "region": str, "model_id": str, "max_turns": int, "max_tokens": int,
        "max_history": int, "temperature": float, "thinking_enabled": bool,
        "thinking_budget": int, "mock_mode": bool,
        "bash_allow_interpreters": bool, "bash_allow_docker": bool,
        "execution_mode": str, "exec_docker_image": str,
        "exec_docker_network_disabled": bool, "exec_docker_readonly_rootfs": bool,
        "require_auth": bool, "require_tool_approval": bool,
        "aws_bedrock_only": bool, "disable_local_traces": bool, "session_cost_limit": float,
        "load_claude_md": bool,
        "enable_prompt_cache": bool,
        "enable_memory_extraction": bool,
        "enable_status_doc": bool, "status_doc": str,
        "enable_skills": bool, "enable_skill_auto_trigger": bool, "skills_dir": str,
        "enable_mcp": bool, "mcp_timeout_seconds": int, "subagent_max_depth": int,
        "enable_worktree": bool,
        "max_user_messages_per_minute": int, "max_user_messages_per_session": int,
        "max_exec_calls_per_session": int, "max_exec_seconds_per_session": int,
        "max_iteration_budget": int,
        "audit_retention_days": int,
        "context_max_tokens": int,
        "compaction_model": str,
        "enable_skill_patching": bool,
        "enforce_verify_contract": bool,
        "enable_subagent_handoff": bool,
    }
    for key, expected_type in _SCALAR_FIELDS.items():
        if key not in ext:
            continue
        val = ext[key]
        # Allow int where float expected
        if expected_type is float and isinstance(val, int):
            val = float(val)
        if not isinstance(val, expected_type):
            logging.warning(
                f"Config: '{key}' expected {expected_type.__name__}, got {type(val).__name__} â€” skipped"
            )
            continue
        # Range validation for numeric fields
        if key == "temperature" and not (0.0 <= val <= 1.0):
            logging.warning(f"Config: temperature={val} out of range [0.0, 1.0] â€” skipped")
            continue
        if key == "thinking_budget" and not (1024 <= val <= 64000):
            logging.warning(f"Config: thinking_budget={val} out of range [1024, 64000] â€” skipped")
            continue
        if key in ("max_turns", "max_tokens", "max_history", "subagent_max_depth") and val < 1:
            logging.warning(f"Config: {key}={val} must be positive â€” skipped")
            continue
        setattr(config, key, val)

    # Structured fields
    if "mcp" in ext and isinstance(ext["mcp"], dict):
        config.mcp_servers = ext["mcp"]
        if config.mcp_servers:
            config.enable_mcp = True

    if "commands" in ext and isinstance(ext["commands"], dict):
        config.custom_commands = ext["commands"]

    if "permissions" in ext and isinstance(ext["permissions"], dict):
        config.permission_rules = ext["permissions"]

    if "agents" in ext and isinstance(ext["agents"], dict):
        config.agent_overrides = ext["agents"]

    # Allowed paths â€” list of absolute directory paths the agent can read AND write outside workspace
    # Also accepts legacy key "allowed_read_paths" for backward compatibility
    _ap_key = (
        "allowed_paths" if "allowed_paths" in ext
        else ("allowed_read_paths" if "allowed_read_paths" in ext else None)
    )
    if _ap_key:
        val = ext[_ap_key]
        if isinstance(val, list) and all(isinstance(p, str) for p in val):
            config.allowed_paths = val
        else:
            logging.warning(f"Config: '{_ap_key}' must be a list of strings â€” skipped")


# ============================================================
# Module-level singleton (v4 pattern)
# ============================================================

CONFIG = Config()
_apply_config_file(CONFIG)

# Block B (Codex finding #5 MEDIUM lock): wire validate_bounded_int_env_var
# into the runtime numeric knobs so env-var overrides clamp safely + log
# WARNING on bad input. Per ADR-021 Â§Linked port-log rows #045.
try:
    from runtime.env_validation import validate_bounded_int_env_var as _vbiev
    CONFIG.max_turns = _vbiev(
        "SAGEMAKER_AGENT_MAX_TURNS",
        minimum=1, maximum=10_000, default=CONFIG.max_turns,
    )
    CONFIG.max_iteration_budget = _vbiev(
        "SAGEMAKER_AGENT_MAX_ITERATION_BUDGET",
        minimum=1, maximum=100_000, default=CONFIG.max_iteration_budget,
    )
    CONFIG.audit_retention_days = _vbiev(
        "SAGEMAKER_AGENT_AUDIT_RETENTION_DAYS",
        minimum=0, maximum=3650, default=CONFIG.audit_retention_days,
    )
    CONFIG.max_exec_calls_per_session = _vbiev(
        "SAGEMAKER_AGENT_MAX_EXEC_CALLS",
        minimum=1, maximum=100_000, default=CONFIG.max_exec_calls_per_session,
    )
    CONFIG.max_exec_seconds_per_session = _vbiev(
        "SAGEMAKER_AGENT_MAX_EXEC_SECONDS",
        minimum=0, maximum=86_400, default=CONFIG.max_exec_seconds_per_session,
    )
except Exception:  # pragma: no cover â€” env-validation is best-effort
    # If anything goes wrong, keep CONFIG defaults; never block import.
    pass

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"Block C\\+|TEST_DESIGN|C-11|C-12|C-13|C-14|UNDECLARED_PATTERN|approval|rate\" compact_v5/MAIN/agent/TEST_DESIGN.md compact_v5/MAIN/agent -g \"TEST_DESIGN.md\"" in D:\Github\sagemaker-coding-agent
2026-05-03T02:55:33.195904Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.4 seconds
Output:
rg: compact_v5/MAIN/agent/TEST_DESIGN.md: The system cannot find the file specified. (os error 2)

 exited 1 in 389ms:
rg: compact_v5/MAIN/agent/TEST_DESIGN.md: The system cannot find the file specified. (os error 2)

codex
I’m now mapping the 14 tests against `TEST_DESIGN` to verify declared coverage and check for any undeclared-pattern drift.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg --files compact_v5/MAIN | rg "TEST_DESIGN|test_design|ADR-010|ADR-023"' in D:\Github\sagemaker-coding-agent
2026-05-03T02:55:36.967040Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.7 seconds
Output:

 exited 1 in 658ms:
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg --files | rg "TEST_DESIGN|test_design|ADR-010|ADR-023"' in D:\Github\sagemaker-coding-agent
 succeeded in 687ms:
compact_v5\_phase_2\wave_6\TEST_DESIGN.md

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/_phase_2/wave_6/TEST_DESIGN.md'" in D:\Github\sagemaker-coding-agent
 succeeded in 464ms:
# v5.0.1 TEST DESIGN

**Date**: 2026-05-01
**Purpose**: define the per-Block test surface so the builder knows what to write, what proves "done", and what AWS cost each test incurs.
**Coverage**: all 21 Blocks + final ship gate.
**Constraint**: minimize AWS spend; max real-AWS cost across full build = ~$0.50.

---

## Test tier definitions

| Tier | Description | When | AWS cost |
|---|---|---|---|
| **T1 Unit** | pytest unit test, mocks all external (Bedrock, files only in tmpdir, no network) | every commit | $0 |
| **T2 Integration** | pytest integration test, mocked Bedrock with canned responses, real file IO + real subprocess | every Block close | $0 |
| **T3 Notebook smoke** | open `chat.ipynb` headlessly via `papermill` or `jupyter nbconvert --execute`, run cells 1-3, assert no error | every Block close | $0 |
| **T4 Zip extract+import** | `_rebuild_zip.py` then `verify_ship_zip.py` extracts in tmpdir + runs `python -c "import entry"` and `python -c "import sagemaker_agent"` | every Block close + before tag | $0 |
| **T5 Real-Bedrock single round-trip** | `RUN_REAL_BEDROCK=1 pytest tests/integration/test_real_bedrock_smoke.py::test_<name>` â€” one Haiku-4.5 round-trip per test | gated, only on 6 high-risk Blocks + Block J | ~$0.005-0.05 each |
| **T6 User acceptance** | YOU run a real task in SageMaker chat.ipynb with `session_cost_limit=$2.00` | per Block, after I commit | depends on session |

---

## Pass/fail criteria

A Block ships only when ALL of:
1. Every T1 + T2 test green
2. T3 smoke green (notebook cells 1-3 + open WidgetChatUI without error)
3. T4 zip extract+import green
4. T5 real-Bedrock smoke green (only for high-risk Blocks)
5. Codex 3-axis review APPROVE on the diff
6. T6 user acceptance â€” you say "go" to next Block

Any single failure = stop, fix, re-test, re-Codex, re-approve.

---

## Per-Block test plan

### Block 0 â€” `sagemaker_agent.py` shim + notebook smoke gate

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_smoke_imports` | T1 | `from sagemaker_agent import CONFIG, BEDROCK_MODELS, create_chat_ui` succeeds | $0 |
| `test_smoke_no_cso_warnings` | T1 | running shim with default LOG_LEVEL emits 0 WARNING-level CSO-CHECK lines (closes PS#1) | $0 |
| `test_chat_ipynb_cells_1_3` | T3 | chat.ipynb cells 1-3 parse + execute against mock Bedrock without exception (cell 1 = pip install, parse-only; cells 2-3 = exec under mock_mode=True). Equivalent to `papermill` for the smoke surface; chosen because papermill is not in the v5 ship-zip dep set and Bedrock smoke does not need a real kernel. | $0 |
| `test_widget_chat_ui_renders` | T2 | `create_chat_ui()` returns a chat-UI handle wired to a real Agent. Accepts `WidgetChatUI` (with non-empty `_panel`) when ipywidgets is installed; falls back to `ConsoleChatUI` (with non-empty `render()`) when ipywidgets is unavailable â€” matches Phase 11 ADR-017 fallback contract. | $0 |
| `test_v4_import_compat` | T1 | every name v4 chat.ipynb references (`CONFIG`, `BEDROCK_MODELS`, `create_chat_ui` per `compact_v4/MAIN/agent/chat.ipynb` cells 2+3) is re-exported through `sagemaker_agent` AND listed in `__all__` | $0 |

**Block 0 ships when**: 5/5 green. **Total AWS cost: $0.**

**Implementation notes (post-Block-0 â€” Codex AXIS A finding #2 lock)**:
- T3 is implemented with manual `exec()` of cell sources rather than papermill. Reason: papermill pulls in jupyter_client + ipykernel + nbclient as install-time deps (~50 MB), which the v5 ship zip does not carry, and the smoke surface (parse + exec under mock_mode) does not require a live kernel. The implementation pre-snapshots every CONFIG field via `monkeypatch` so cell 2's CONFIG mutations don't leak into other tests (this caught a real test-isolation bug at Block 0 build time).
- T2 accepts ConsoleChatUI fallback because the Phase 11 factory branches on ipywidgets availability (`_IPYWIDGETS_OK`). On a CI runner without ipywidgets, the WidgetChatUI branch is unreachable; the fallback is the production behavior and is what users with no widget host will see.

---

### Block B â€” TokenTracker + AuditLogger + SnapshotManager + Runnable tokenEstimation

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_token_tracker_singleton` | T1 | `TOKENS` is the singleton; `update()` accumulates correctly | $0 |
| `test_audit_logger_writes_jsonl` | T1 | every audit entry writes valid JSONL line to `audit_logs/<session>.jsonl` | $0 |
| `test_snapshot_manager_creates_backup` | T1 | edit_file creates `.snapshot/<file>_<ts>.bak` | $0 |
| `test_token_tracker_per_agent_breakdown` | T1 | `TOKENS.parent_input_tokens` + `TOKENS.subagent_input_tokens["build"]` accumulate independently | $0 |
| `test_count_tokens_with_bedrock_mocked` | T2 | mocked `bedrock-runtime.count_tokens` response parsed correctly | $0 |
| `test_token_accounting_input_cumulative` | T1 | per turn: input KEEPS-LATEST (not sum), output SUMS (R7 N8 fix) | $0 |
| `test_haiku_excluded_from_cache_break` | T1 | Haiku-4.5 model_id added to `EXCLUDED_MODELS_FOR_CACHE_BREAK` set; cache-break detector skips it (R4 #14 MUST) | $0 |
| `test_count_tokens_real_bedrock_haiku` | T5 | one real `count_tokens` call to Haiku-4.5 returns positive int matching mock contract | ~$0.005 |

**Block B ships when**: 8/8 green. **Total AWS cost: ~$0.005.**

---

### Block B+ â€” SessionManager + cost-limit + AGENT_STATUS + FileCache thread-local

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_session_manager_atomic_save` | T1 | save â†’ tmp file â†’ atomic rename; partial-write doesn't corrupt | $0 |
| `test_session_save_load_preserves_cost` | T1 | save at $2.09 â†’ load â†’ `TOKENS.session_cost == 2.09` (closes PS#5) | $0 |
| `test_session_cost_limit_warns_at_100pct` | T1 | when `session_cost >= session_cost_limit`, query_engine emits a `[Cost ${cost} passed budget ${limit} â€” continuing.]` line ONCE per run() call AND `TOKENS.add()` does NOT raise on subsequent calls (warn-and-continue per user 2026-05-03 Plan v3 update; matches v4 UX). Hard halt is at cloud-budget level (AWS Budget Action / GCP) â€” see `docs/CLOUD_COST_CAPS_SETUP.md`. | $0 |
| `test_agent_status_auto_load` | T1 | first `Agent.run()` call reads `AGENT_STATUS.md` and injects into system prompt | $0 |
| `test_filecache_thread_local_isolation` | T2 | parent `_FILES_READ` not visible inside sub-agent thread context (uses verified v4 APIs `save_and_clear_context` + `enter_thread_local_context`) | $0 |
| `test_subagent_token_attribution` | T2 | spawn parent + sub-agent â†’ assert `TOKENS.parent_input_tokens > 0` AND `TOKENS.subagent_input_tokens["build"] > 0` AND `session_cost == sum_of(per_agent_cost) Â± $0.0001` | $0 |
| `test_tokens_singleton_is_budget_source` | T1 | budget checks read TOKENS singleton, NOT Agent attribute (closes PS#6) | $0 |

**Block B+ ships when**: 7/7 green. **Total AWS cost: $0.**

---

### Block C â€” Runtime safety + secret scanner + JSON repair + injection scan + bash hardening

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_exec_limit_200_then_201_blocked` | T2 | run 200 mocked bash â†’ 201st returns exact error including `OTHER TOOLS STILL WORK: read_file, grep, glob, edit_file, write_file, notebook_edit, task, ask_user, view_image, web_fetch are NOT counted by this limit.` (closes PS#7) | $0 |
| `test_repetition_detector_blocks_3rd_dup` | T2 | same `read_file(path=X)` 3 times â†’ 3rd blocked with dedup message | $0 |
| `test_security_manager_blocks_dangerous_rm` | T1 | `bash("rm -rf /")` returns DANGER block message | $0 |
| `test_security_manager_blocks_etc_passwd` | T1 | `read_file("/etc/passwd")` returns PATH-VALIDATION block | $0 |
| `test_security_manager_blocks_aws_destroy` | T1 | `bash("aws s3 rm s3://prod --recursive")` blocked | $0 |
| `test_secret_scanner_38_patterns` | T1 | each of 38 secret patterns (13 v4 + 25 from Runnable) detects + redacts in test fixture | $0 |
| `test_json_repair_malformed_args` | T1 | `_repair_tool_call_arguments({"foo":"bar)` â†’ `{"foo":"bar"}` (Hermes :547-641); empty `{}` fallback if irrecoverable | $0 |
| `test_injection_scanner_v4_native` | T1 | `_scan_for_prompt_injection` detects v4's 12 patterns + invisible chars (v4:7509-7541) | $0 |
| `test_files_read_thread_local_save_restore` | T1 | `save_and_clear_context()` + `restore_context()` + `enter_thread_local_context()` all from v4:893-1017 verbatim | $0 |
| `test_quote_normalization_curly_to_straight` | T1 | edit_file with `"foo"` matches `"foo"` (curly quotes) (R1 #115) | $0 |
| `test_utf16_bom_detected` | T1 | edit_file on Notepad-saved file (UTF-16 LE BOM) handled correctly (R1 #121) | $0 |
| `test_unc_path_skip_windows` | T1 | `\\\\server\\share\\file.txt` rejected on Windows (NTLM credential leak prevention) (R1 #123) | $0 |

**Block C ships when**: 12/12 green. **Total AWS cost: $0.**

---

### Block C+ â€” Approval/diff + rate limits + ipywidgets fallback + PermissionDialog richer

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_approval_gate_blocks_until_approve` | T2 | write_file with `require_tool_approval=True` blocks; mock approve â†’ unblocks | $0 |
| `test_approval_dialog_shows_diff` | T2 | `pending_approval` UI renders colored diff (red/green/gray context) | $0 |
| `test_approval_per_tool_always_allow` | T2 | "Always allow" sets `_always_allowed[tool_name]=True`; subsequent calls skip dialog | $0 |
| `test_rate_limit_100_per_min` | T2 | 101st message in 60s window â†’ rate-limit error with countdown | $0 |
| `test_stop_button_halts_run` | T2 | `Agent.stop()` mid-tool-loop sets stop flag; QueryEngine respects it | $0 |
| `test_ipywidgets_fallback_text_mode` | T2 | when `ipywidgets` unavailable, `WidgetChatUI` falls back to `ConsoleChatUI` with `ask_user`-text-mode for approvals (60s watchdog timeout) | $0 |
| `test_permission_dialog_reason_prompt` | T2 | dialog shows model's "reason" string from tool_use args | $0 |

**Block C+ ships when**: 7/7 green. **Total AWS cost: $0.**

---

### Block D â€” Slash commands (19 advertised + /auth + /simplify expander + /init + /init-verifiers + /skillify + /dream + /promote-to-skill)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_slash_dispatch_/cost` | T2 | `/cost` returns formatted 4-line cost block | $0 |
| `test_slash_dispatch_/status` | T2 | `/status` returns status with model + active skills + phase | $0 |
| `test_slash_dispatch_/save_<name>` | T2 | `/save mywork` writes `sessions/mywork.json` with full state | $0 |
| `test_slash_dispatch_/load_<name>` | T2 | `/load mywork` restores state including `TOKENS.session_cost` | $0 |
| `test_slash_dispatch_/compact` | T2 | `/compact` invokes `Compactor.compact()` (Block A trigger) | $0 |
| `test_slash_dispatch_/clean` | T2 | `/clean` removes `audit_logs/` + `sessions/` + `.snapshots/` files | $0 |
| `test_slash_dispatch_/skills_list` | T2 | `/skills` lists all 10 skills | $0 |
| `test_slash_dispatch_/skill_use_clara` | T2 | `/skill use clara` resolves `clara` â†’ `clara-review` (fuzzy from Block I) | $0 |
| `test_slash_dispatch_/skill_apply_proposal` | T2 | `/skill apply <name>` shows diff + applies | $0 |
| `test_slash_dispatch_/revert_<file>` | T2 | `/revert path/to/file.py` rolls back to last snapshot | $0 |
| `test_slash_dispatch_/context` | T2 | `/context` shows token/context bloat diagnostic | $0 |
| `test_slash_dispatch_/verify_quick` | T2 | `/verify quick` invokes verify skill | $0 |
| `test_slash_dispatch_/checkpoint_create_v1` | T2 | `/checkpoint create v1` snapshots all touched files | $0 |
| `test_slash_dispatch_/checkpoint_restore_v1` | T2 | `/checkpoint restore v1` rolls back all to v1 state | $0 |
| `test_slash_dispatch_/phase_text` | T2 | `/phase Phase 2 build` sets work-phase tag in status bar | $0 |
| `test_slash_dispatch_/diffs_summary` | T2 | `/diffs summary` shows session edit history summary | $0 |
| `test_slash_dispatch_/regression` | T2 | `/regression` runs `git diff HEAD --stat` + suggests test cmd | $0 |
| `test_slash_dispatch_/done_quick` | T2 | `/done quick` runs simplify â†’ verify pipeline â†’ READY-TO-SHIP verdict | $0 |
| `test_slash_dispatch_/commands` | T2 | `/commands` lists custom commands from `agent_config.json` | $0 |
| `test_slash_dispatch_/auth_token` | T2 | `/auth <token>` validates against `os.getenv(CONFIG.auth_token_env)` (when `require_auth=True`) | $0 |
| `test_slash_dispatch_/simplify_falls_through_to_skill` | T2 | `/simplify` (no dedicated handler) hits expander at `:11330` â†’ resolves to `skills/simplify/SKILL.md` | $0 |
| `test_slash_dispatch_/dream_invokes_consolidation` | T2 | `/dream` invokes Block H+ memory consolidation (manual-only) | $0 |
| `test_slash_dispatch_/init_scaffolds_claude_md` | T2 | `/init` generates project CLAUDE.md from interactive prompt | $0 |
| `test_slash_dispatch_/skillify_captures_session` | T2 | `/skillify` runs 4-round AskUserQuestion â†’ saves new skill | $0 |
| `test_slash_dispatch_/promote_to_skill` | T2 | `/promote-to-skill` writes proposal to `state/skill-proposals/` | $0 |
| `test_dispatcher_unknown_slash_falls_through` | T2 | `/unknown_command` not in registry â†’ falls through to chat (not error) | $0 |

**Block D ships when**: 26/26 green. **Total AWS cost: $0.**

---

### Block A â€” Compactor + cold-cache + auto-compact (COMBINED v4 + Runnable)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_compactor_2stage_prune_plus_llm_summary` | T2 | mocked LLM summary; assert prune step removes tool outputs older than threshold; LLM step generates 13-section template | $0 |
| `test_microcompact_threshold_70pct` | T2 | when `total_tokens / context_window > 0.70` â†’ microcompact fires | $0 |
| `test_context_collapse_threshold_85pct` | T2 | when > 0.85 â†’ context_collapse fires | $0 |
| `test_cold_cache_30min_idle_triggers_microcompact` | T2 | mock `time.time()` to simulate 30min idle â†’ next msg â†’ microcompact fires + log line `[i] Cold cache detected` (closes PS#3) | $0 |
| `test_keep_last_n_cold_cache_1` | T2 | after cold-cache compact, only last 1 message retained | $0 |
| `test_post_compact_files_read_clear` | T2 | after compact, `_FILES_READ.clear()` runs (model can re-read files) | $0 |
| `test_post_compact_todo_restoration_message` | T2 | after compact, `build_todo_restoration_message` injected | $0 |
| `test_auto_compact_circuit_breaker_3_failures` | T2 | 3 consecutive `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES` â†’ autoCompact disabled with warning | $0 |
| `test_cache_edits_per_tool_invalidation` | T2 | per-tool schema hash change â†’ only that tool's cache invalidated | $0 |
| `test_a28_cache_invariant_no_mid_session_rebuild` | T2 | system prompt rebuild attempted mid-conversation â†’ blocked with warning (`/cmd --now` opt-in only) | $0 |
| `test_h2_stub_injection_for_orphan_tool_use` | T2 | post-compact, dangling `tool_use` block â†’ synthetic `tool_result` stub injected (prevents Bedrock 400) | $0 |
| `test_compact_fires_real_haiku_long_context` | T5 | real Haiku-4.5 round-trip with 80K+ token input â†’ triggers compact â†’ next call succeeds | ~$0.01 |

**Block A ships when**: 12/12 green. **Total AWS cost: ~$0.01.**

---

### Block E+F â€” HTML chat rendering + cell 2 widgets + complete session UI + IterationBudgetWidget + ThinkingBudgetWidget

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_render_chat_user_message` | T1 | `render_chat()` produces HTML with user message in correct color | $0 |
| `test_render_chat_assistant_markdown` | T1 | `_render_assistant_markdown()` converts markdown â†’ HTML (code blocks, tables, lists) | $0 |
| `test_render_todos_status_icons` | T1 | TODO list renders with âœ…/ðŸ”„/â¬œ icons | $0 |
| `test_update_tokens_display_shows_pct` | T1 | token display shows `X / Y (Z%)` and `cache hit %` | $0 |
| `test_update_mode_display_status_bar` | T1 | status bar shows model + active skills + phase + cost | $0 |
| `test_dark_mode_toggle_swaps_theme` | T2 | dark-mode toggle swaps theme dict; chat re-renders | $0 |
| `test_model_dropdown_lists_all_models` | T2 | dropdown contains Haiku-4.5 + Sonnet-4.6 + Opus options | $0 |
| `test_iteration_budget_widget_shows_used_total` | T1 | widget HTML shows `<progress>` + `used/total` + color cue (closes PS#2 visible UI) | $0 |
| `test_thinking_budget_widget_shows_on_off` | T1 | widget HTML shows `thinking=ON\|OFF, budget=N tokens` (closes PS#4 visible UI) | $0 |
| `test_session_dropdown_lists_saves` | T2 | session dropdown lists all `sessions/*.json` files | $0 |
| `test_session_load_button_restores` | T2 | clicking load â†’ `SessionManager.load()` â†’ state restored | $0 |
| `test_auto_save_on_send` | T2 | every send auto-saves to `last_session.json` | $0 |
| `test_long_text_details_collapse` | T1 | text > 5000 chars wrapped in `<details><summary>show more</summary>...</details>` (Wave 6 GAP fix) | $0 |
| `test_thinking_config_sent_every_call` | T1 | mocked BedrockClient.chat: thinking config in every payload (closes PS#4) | $0 |

**Block E+F ships when**: 14/14 green. **Total AWS cost: $0.**

---

### Block F2 â€” Auto-continuation under iteration budget

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_f2_auto_continue_at_under_90pct` | T2 | iteration_used < 90% AND not diminishing-returns â†’ auto-continue | $0 |
| `test_f2_blocks_at_90pct` | T2 | iteration_used >= 90% â†’ halts + asks user | $0 |
| `test_f2_respects_cost_cap` | T2 | even if iteration_used < 90%, if `session_cost > session_cost_limit` â†’ halt | $0 |

**Block F2 ships when**: 3/3 green. **Total AWS cost: $0.**

---

### Block I â€” Skill name resolution + Hermes fuzzy + paths frontmatter + scaffolders

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_skill_resolve_by_directory_name` | T1 | `/skill use clara-review` â†’ loads `skills/clara-review/SKILL.md` | $0 |
| `test_skill_resolve_by_metadata_name` | T1 | `/skill use Clara` (metadata `name: Clara`) â†’ loads `skills/clara-review/` | $0 |
| `test_skill_fuzzy_match_typo` | T1 | `/skill use verfy` â†’ fuzzy resolves to `verify` (Hermes :4689-4720) | $0 |
| `test_skill_paths_frontmatter_auto_activate` | T2 | skill with `paths: ["*.py"]` auto-activates when user edits .py file | $0 |
| `test_skill_disable_model_invocation` | T2 | skill with `disable_model_invocation: true` not visible to model but callable by user | $0 |
| `test_skill_enabled_when_config_flag` | T2 | skill with `enabled_when: CONFIG.advanced_mode` only loads when flag True | $0 |
| `test_skillify_4_round_interview` | T2 | `/skillify` runs 4 AskUserQuestion rounds â†’ writes `skills/<new>/SKILL.md` | $0 |
| `test_skill_manager_realpath_dedup` | T1 | symlink to same dir loaded once (R9 #23 bug fix) | $0 |

**Block I ships when**: 8/8 green. **Total AWS cost: $0.**

---

### Block M â€” Phase 8 critical fixes (per-turn discovery reset + structured-output retry counter)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_discovered_tool_names_reset_per_turn` | T1 | `self._discovered_tool_names` resets at start of each turn (not just run-start) | $0 |
| `test_structured_output_retry_limit_3` | T1 | `countToolCalls` blocks at retry limit 3 â†’ halts with explicit message | $0 |
| `test_infinite_loop_blocked_at_retry_limit` | T2 | model returns malformed structured output 3x â†’ halt | $0 |

**Block M ships when**: 3/3 green. **Total AWS cost: $0.**

---

### Block G â€” AGENT_TYPES + worktree + handoff/env

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_agent_types_dict_has_7` | T1 | `AGENT_TYPES.keys() == {build, plan, explore, verify, general, review, fork}` | $0 |
| `test_subagent_build_spawns_worktree` | T2 | `task(subagent_type="build")` creates `worktrees/<id>/` (mocked git) | $0 |
| `test_subagent_verify_loads_verify_skill` | T2 | `task(subagent_type="verify")` loads verify skill in sub-agent context | $0 |
| `test_subagent_handoff_block_built` | T1 | `_build_subagent_handoff_block()` produces v4-equivalent text | $0 |
| `test_subagent_env_details_built` | T1 | `_build_subagent_env_details()` includes cwd + git status + tool list | $0 |
| `test_max_subagent_depth_2_blocks_grandchild` | T2 | parent â†’ child OK; child â†’ grandchild blocked with `MAX_SUBAGENT_DEPTH=2` error (Wave 6 GAP fix) | $0 |
| `test_iteration_budget_shared_object_identity` | T2 | parent and sub-agent share SAME `IterationBudget` object (object identity check) | $0 |
| `test_worktree_cleanup_on_completion` | T2 | sub-agent completion removes worktree | $0 |

**Block G ships when**: 8/8 green. **Total AWS cost: $0.**

---

### Block G3 â€” Coordinator System Prompt (NEW)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_coordinator_prompt_contains_4_phases` | T1 | system prompt for `task` tool contains "Research â†’ Synthesis â†’ Implementation â†’ Verification" | $0 |
| `test_coordinator_prompt_synthesize_dont_delegate` | T1 | prompt contains "NEVER delegate understanding" | $0 |
| `test_coordinator_prompt_continue_vs_spawn_table` | T1 | prompt contains continue-vs-spawn decision table | $0 |
| `test_coordinator_prompt_research_parallel_write_serial` | T1 | prompt contains "Read-only tasks: run in parallel; Write tasks: one at a time" | $0 |
| `test_coordinator_prompt_real_haiku_orchestration` | T5 | real Haiku-4.5 round-trip: prompt agent to coordinate 3 sub-agents â†’ assert it spawns parallel reads, serial writes | ~$0.01 |

**Block G3 ships when**: 5/5 green. **Total AWS cost: ~$0.01.**

---

### Block G2 â€” forkSubagent cache-prefix replay

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_forkSubagent_byte_identical_prefix` | T1 | parent + child API requests have BYTE-identical prefix when `cache_prefix_share=True` | $0 |
| `test_forkSubagent_cache_aware_serialization` | T1 | message serialization deterministic (sorted keys, no random IDs in prefix) | $0 |
| `test_g2_cache_prefix_real_bedrock` | T5 | real Bedrock call: parent + child â†’ second call cache_read_input_tokens > 0 (cache hit verified) | ~$0.01 |

**Block G2 ships when**: 3/3 green. **Total AWS cost: ~$0.01.**

---

### Block H â€” Memory extraction (COMBINED v4 + Runnable extractMemories + sessionMemory)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_extract_and_append_memories_v4_session_end` | T1 | session-end trigger writes new entries to `memory.md` (v4 behavior) | $0 |
| `test_extract_memories_closure_scoped_state` | T1 | extractMemories has closure-scoped throttle state (Runnable pattern) | $0 |
| `test_session_memory_dedup_before_write` | T1 | `sessionMemoryUtils` deduplicates before writing memory.md | $0 |
| `test_adjust_index_preserves_api_invariants` | T1 | `adjustIndexToPreserveAPIInvariants` returned indices keep tool_use/tool_result paired (R4 #56 MUST) | $0 |
| `test_memory_extraction_handles_empty_session` | T1 | session with 0 user messages â†’ no extraction, no error | $0 |
| `test_session_memory_compact_no_400_sequence` | T2 | compact run on session with mixed tool_use/tool_result â†’ resulting messages valid for Bedrock | $0 |

**Block H ships when**: 6/6 green. **Total AWS cost: $0.**

---

### Block H+ â€” Memory consolidation engine (`/dream` MANUAL ONLY, no daemon)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_dream_4_phase_prompt_orient_gather_consolidate_prune` | T1 | dream prompt contains 4 phases in correct order | $0 |
| `test_dream_lock_file_prevents_concurrent_runs` | T1 | `dream.lock` file blocks 2nd `/dream` invocation | $0 |
| `test_dream_rollback_on_failure` | T2 | mid-run failure â†’ `memory.md.bak` restored; original `memory.md` untouched | $0 |
| `test_dream_no_daemon_no_auto_fire` | T1 | search v5 codebase: no `Thread`/`asyncio.create_task`/`atexit.register(dream)`/`SAGEMAKER_AUTO_DREAM` env var (verifies user decision 2026-05-01) | $0 |
| `test_dream_real_consolidation_haiku` | T5 | real `/dream` invocation on test memory.md â†’ outputs cleaner file (~$0.05) | ~$0.05 |

**Block H+ ships when**: 5/5 green. **Total AWS cost: ~$0.05.**

---

### Block L â€” Error/retry/cache-break + Bedrock guardrails + daemon-thread call

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_categorize_retryable_18_error_types` | T1 | each of 18 Runnable error categories â†’ correct retryable verdict (R4 18 categories) | $0 |
| `test_parse_max_tokens_overflow_recovers` | T1 | `parseMaxTokensContextOverflowError` triggers compact + retry (R4 #2 MUST) | $0 |
| `test_extract_nested_error_message_humanizes_5xx_html` | T1 | Bedrock 5xx with raw HTML â†’ user sees clean error message (R4 #9 MUST) | $0 |
| `test_retry_after_header_parsed` | T1 | `getRetryAfterMs` parses `Retry-After: 5` â†’ 5000ms wait | $0 |
| `test_per_tool_cache_break_detection` | T1 | per-tool schema hash change â†’ `notifyCacheDeletion` fires for that tool only | $0 |
| `test_haiku_excluded_from_cache_break_3loc` | T1 | Haiku-4.5 model_id in EXCLUDED set â†’ cache-break detector skips (R4 #14 MUST) | $0 |
| `test_daemon_thread_bedrock_call_responds_to_ctrl_c` | T2 | Bedrock call wrapped in daemon thread; main thread Ctrl-C raises KeyboardInterrupt cleanly | $0 |
| `test_30s_heartbeat_during_long_call` | T2 | heartbeat ping every 30s during long call â†’ status bar updates | $0 |

**Block L ships when**: 8/8 green. **Total AWS cost: $0.**

---

### Block N â€” Parallel tool execution + dynamic tool refs + dedup + fuzzy + ephemeral prompt

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_parallel_exec_3_independent_reads` | T2 | 3 read_file calls dispatched in parallel â†’ completion in MAX(call_time), not SUM | $0 |
| `test_parallel_exec_path_conflict_serializes_writes` | T2 | 2 write_file to same path â†’ serialized (not parallel) | $0 |
| `test_tool_call_dedup_blocks_redundant` | T2 | same `(tool_name, args)` 3x in one batch â†’ 2 calls deduped | $0 |
| `test_fuzzy_tool_name_typo_resolves` | T1 | `read_filee` â†’ fuzzy resolves to `read_file` | $0 |
| `test_ephemeral_system_prompt_not_persisted` | T1 | ephemeral prompt fragment not written to session log | $0 |
| `test_dynamic_tool_ref_injection_at_init` | T1 | tool schemas at init have cross-references injected (Hermes A36) | $0 |
| `test_max_tool_workers_4` | T1 | `_MAX_TOOL_WORKERS=4` constant; 5 parallel calls â†’ 4 in flight + 1 queued | $0 |
| `test_n7_partial_tool_names_warning_on_disconnect` | T2 | mid-call disconnect â†’ warning + synthetic tool_result stub | $0 |
| `test_n_real_3_parallel_reads_haiku` | T5 | real Bedrock 3 parallel read_file calls â†’ wallclock < SUM (validate ~40% gain) | ~$0.005 |

**Block N ships when**: 9/9 green. **Total AWS cost: ~$0.005.**

---

### Block T â€” v4 tool surface parity (11 missing tools)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_tool_create_word_writes_docx` | T1 | `create_word(filepath="x.docx", content="# h")` writes valid .docx | $0 |
| `test_tool_create_excel_with_chart` | T1 | `create_excel(...,chart_type="bar")` writes .xlsx with embedded chart | $0 |
| `test_tool_create_markdown` | T1 | `create_markdown` writes .md file | $0 |
| `test_tool_create_notebook_cells` | T1 | `create_notebook(cells=[...])` writes valid .ipynb | $0 |
| `test_tool_create_chart_png` | T1 | `create_chart(chart_type="bar")` writes valid PNG | $0 |
| `test_tool_create_pdf_sections` | T1 | `create_pdf(content=[heading,text,table,image])` writes valid .pdf | $0 |
| `test_tool_todo_write_round_trip` | T1 | `todo_write([{"content":"x","status":"pending","activeForm":"Doing x"}])` then `todo_read()` returns same | $0 |
| `test_tool_semantic_search_index_then_search` | T2 | `semantic_search(action="index", path=".")` then `action="search", query="..."` returns hits | $0 |
| `test_tool_web_fetch_html_to_markdown` | T2 | mocked HTTP response â†’ `web_fetch` returns markdown text | $0 |
| `test_tool_ask_user_blocks_then_unblocks` | T2 | `ask_user` blocks until user responds; mock response unblocks | $0 |
| `test_tool_create_html_via_write_file_documented` | T1 | docs note: `create_html` not a separate tool; use `write_file(*.html)` (Wave 6 design note) | $0 |

**Block T ships when**: 11/11 green. **Total AWS cost: $0.**

---

### Block J â€” Real-Bedrock smoke + zip extract+import (THE SHIP GATE)

This is THE final gate before tagging. **All real-AWS testing concentrates here.**

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_zip_rebuild_succeeds` | T4 | `python _rebuild_zip.py` produces `compact_v5.zip` | $0 |
| `test_zip_extract_in_tmpdir` | T4 | `verify_ship_zip.py` extracts zip in fresh tmpdir | $0 |
| `test_zip_python_c_import_entry` | T4 | `python -c "import entry"` succeeds in extracted dir | $0 |
| `test_zip_python_c_import_sagemaker_agent` | T4 | `python -c "import sagemaker_agent; sagemaker_agent.create_chat_ui()"` succeeds | $0 |
| `test_real_bedrock_hello_world` | T5 | real Haiku-4.5 round-trip: send "say hello", assert non-empty text response | ~$0.005 |
| `test_real_bedrock_tool_use_round_trip` | T5 | real Haiku-4.5: send "list files in /tmp", assert tool_use(name="list_dir") + tool_result + final text | ~$0.005 |
| `test_real_bedrock_compact_then_continue` | T5 | real call with 80K-token preamble â†’ compact fires â†’ next call succeeds with reduced prefix | ~$0.01 |

**Block J ships when**: 7/7 green. **Total AWS cost: ~$0.02.**

This block + the per-block T5 tests = total ~$0.10 across the entire build.

---

### Block K â€” Process discipline (LF AXIS C + per-block user gate + STATE/RESUME + 3-critic + A44 test refactor)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_axis_c_template_present` | T4 | `_status/CODEX_REVIEW_TEMPLATE.md` contains AXIS A + AXIS B + AXIS C sections | $0 |
| `test_state_resume_anchor_per_block` | T4 | every Block tag has corresponding `V5_BUILD_STATUS.md` "Last commit sha" matching | $0 |
| `test_per_block_user_approval_gate_documented` | T4 | `RESUME.md` Step 5 contains "Tag is FORBIDDEN if any open Codex finding has severity â‰¥ CHANGES_REQUESTED" | $0 |
| `test_a44_no_change_detector_tests_audit` | T4 | scan `tests/` for `assert "X" in MODELS` / `assert COUNT == N` â€” fail if found (rewrite as invariant) | $0 |
| `test_lint_phase_id` | T4 | `tests/lint_phase_id.py` validates tag name + status field + codex review filename match | $0 |

**Block K ships when**: 5/5 green. **Total AWS cost: $0.**

---

---

## R-tier â€” high-value real-AWS scenarios (added 2026-05-01 per user directive)

User directive: "AWS test allowed but must be carefully designed and optimized for v5 to collect MOST value to see if user using it without any semantic bugs."

These are end-to-end USER-SIMULATING scenarios run on real Bedrock. Each has a hard cost cap. Run after Block K (process discipline) lands but before tag.

| # | Scenario | What it catches | Model | Cost cap |
|---|---|---|---|---|
| **R1** | 50-turn dashboard build: read CSV â†’ python_exec to summarize â†’ create_chart â†’ create_word with embedded chart | Tool dispatch round-trips end-to-end, parallel exec wallclock gain on real Bedrock, security gate with real bash, .docx output integrity | Haiku-4.5 | $1.00 |
| **R2** | Long context: load 80K-token preamble â†’ ask "refactor this module" â†’ verify compaction fires + cache_edits invalidates only changed tools | Block A semantic correctness on Bedrock cache; A28 invariant on real cache hit | Haiku-4.5 | $0.50 |
| **R3** | Sub-agent dispatch: parent spawns 3 parallel research sub-agents â†’ synthesize â†’ write report. Verify cache-prefix replay shares cache | Block G + G2 + G3 cache-prefix bytes-stable on real Bedrock | Haiku-4.5 | $0.50 |
| **R4** | 30-min idle: send msg â†’ wait 30min real-time â†’ send next. Verify cold-cache compact fires + saves â‰¥5K tokens | PS#3 structural fix end-to-end | Haiku-4.5 | $0.20 |
| **R5** | 200-bash: agent loops python_exec 200x. 201st returns exact "OTHER TOOLS STILL WORK" message; agent continues with read_file/grep | PS#7 structural fix end-to-end | Haiku-4.5 | $0.50 |
| **R6** | Memory consolidation: build memory.md to 100 entries â†’ `/dream` â†’ verify deduplication + categorization works | Block H+ semantic correctness; rollback on fail; lock prevents concurrent | Haiku-4.5 | $0.30 |
| **R7** | Model switch mid-conversation: 10 turns on Haiku â†’ user changes dropdown â†’ next turn uses Sonnet. **A28 invariant**: prompt cache NOT rebuilt mid-conversation; switch applies next session | Hermes A28 critical policy on real Bedrock | Haikuâ†’Sonnet | $0.50 |
| **R8** | Error recovery: mock Bedrock return malformed JSON tool args â†’ multi-pass repair works â†’ if irrecoverable, `{}` fallback used + agent continues | Block C JSON repair end-to-end | Haiku-4.5 (mocked) | $0.20 |
| **R9** | Approval flow: write_file â†’ diff_widget renders â†’ user clicks Approve/Deny/Always â†’ decision propagates to TOKENS + AUDIT + SNAPSHOTS | Block C+ approval flow end-to-end | Haiku-4.5 | $0.30 |
| **R10** | Save/load: spend $1 in turns â†’ `/save mytest` â†’ restart kernel â†’ `/load mytest` â†’ verify `TOKENS.session_cost == $1.00` and chat history restored | PS#5 + PS#6 structural fix on real session | Haiku-4.5 | $1.00 |
| **R11** | Sonnet end-to-end: same as R1 but on Sonnet-4.6. Catches model-specific behavior differences | Sonnet-4.6 | $1.50 |
| **R12** | Multi-tool malformed args stress: model returns `{"path": "/tmp/", "content": "<UNCLOSED` â†’ JSON repair fires; model returns surrogate-pair Unicode â†’ sanitizer fires | Block L Bedrock error categories; H1 surrogate sanitize | Haiku-4.5 | $0.20 |

**R-tier total cost cap: ~$7.00** (worst case all hit cost cap; realistic ~$3-5).

Each R-test:
- Hard `session_cost_limit` set to its cap; agent halts if exceeded
- Test passes if scenario completes + assertions green
- Test fails (and is investigated) if Bedrock returns error, cost cap hit, or assertion fails
- Failed R-test = stop, fix, re-test before tag

---

## Per-Block close ritual (NOT a separate test, but a discipline the builder follows)

User directive 2026-05-01: status, git push, HTML, rezip must all be part of implementation plan.

These run at EVERY Block close per Block K + project CLAUDE.md rules:

| Action | When | Tool | Cost |
|---|---|---|---|
| Update `_status/V5_BUILD_STATUS.md` (Last updated, Last commit sha, State, Next session pickup) | end of every Block | manual edit | $0 |
| Append PORT_LOG rows to `_status/V5_RUNNABLE_PORT_LOG.md` for that Block (each row references one source file:line + Codex verdict) | end of every Block | manual append | $0 |
| Append ADR(s) to `_status/V5_DESIGN_DECISIONS.md` for any non-trivial choice in this Block | end of every Block | manual append | $0 |
| Save Codex AXIS A/B/C review to `_status/codex_reviews/block-<X>.md` | end of every Block | save Codex output | $0 (Codex run is per-Block) |
| Git commit (`git add <specific files>` then `git commit -m "..."`); NEVER `git add -A` (per user project rule, prevents .env / credentials) | end of every Block | git | $0 |
| Run pytest `tests/` (T1+T2) green | end of every Block | pytest | $0 |
| Run `python verify_ship_zip.py` (T4) green | end of every Block | python | $0 |
| **Rebuild `compact_v5.zip`** via `python _rebuild_zip.py`; verify size + manifest sane | end of every Block (catches packaging regressions early) | python | $0 |
| Tag `v5.0.1-block-<X>` ONLY after Codex APPROVE + user approval | end of every Block, after gates pass | git tag | $0 |
| **Push to `sageagent` remote** (per user project rule for sagemaker-coding-agent) | end of every Block, after tag | `git push sageagent v5-build && git push sageagent v5.0.1-block-<X>` | $0 |
| **Update HTML companion docs** if architecture changed (Block E+F changes UI; Block A changes compaction; Block B changes cost; Block H changes memory; Block N changes parallel exec). HTML is at `compact_v5/docs/` if exists OR `compact_v4/MAIN/agent/docs/` for v4-comparison HTML | per relevant Block | manual or scripted | $0 |
| Sync `chat.ipynb` companion `chat.md` (markdown render of cells) | per Block 0/E+F/F | jupytext or manual | $0 |
| Sync ship zip to OneDrive (per project rule) | end of every Block, after rezip | manual copy | $0 |

**Block K codifies this ritual; it's not a separate test or a separate Block â€” it runs at every Block close.**

The builder MUST NOT advance to next Block until ALL ritual items pass for current Block.

---

## Total cost summary

| Source | Tests | AWS cost |
|---|---|---|
| All T1 unit tests | ~150 | $0 |
| All T2 integration tests | ~100 | $0 |
| All T3 notebook smoke | ~21 | $0 |
| All T4 zip extract+import | ~21 | $0 |
| **T5 real-Bedrock single round-trips** (env-gated, only on 6 high-risk Blocks + Block J) | **~10 round-trips** | **~$0.10-0.15** |
| **R-tier high-value end-to-end real-AWS scenarios** (R1-R12, run after Block K, before tag) | 12 scenarios | **~$3-7** (caps total $7) |
| Total Phase 2 build validation (incl. R-tier) | ~312 tests | **~$3.10-7.15** |
| Your first 5 real coding sessions (Haiku-4.5, `session_cost_limit=$1`) | n/a | **~$1-3** |
| **GRAND TOTAL through real-world validation** | | **~$4-10** |

---

## How to run

### During each Block (mock-only, $0)
```bash
cd compact_v5/MAIN/agent
pytest tests/                                    # T1 + T2
papermill chat.ipynb out.ipynb                   # T3
cd .. && python verify_ship_zip.py               # T4
```

### High-risk Blocks (B, A, G3, G2, H+, N) end-of-Block
```bash
RUN_REAL_BEDROCK=1 AWS_REGION=ap-southeast-2 \
  pytest tests/integration/test_real_bedrock_smoke.py::test_<block>_real_haiku
# Expected cost per Block: $0.005-0.05
```

### Block J ship gate
```bash
cd compact_v5
python _rebuild_zip.py                           # build zip
python verify_ship_zip.py                        # extract + import gate

RUN_REAL_BEDROCK=1 AWS_REGION=ap-southeast-2 \
  pytest tests/integration/test_real_bedrock_smoke.py
# Expected cost: $0.02
```

### Your acceptance test (post-tag, in SageMaker)
1. Open `chat.ipynb` in SageMaker JupyterLab
2. Cell 2: set `iteration_budget_slider=200`, `session_cost_limit=$1.00`, model=Haiku-4.5
3. Cell 3: launch chat
4. Send: "list the files in /home/sagemaker-user/, then read the README if present, then summarize"
5. Verify: list_dir + read_file + assistant text response, total cost <$0.05
6. Try `/cost`, `/status`, `/save mytest`, `/load mytest` â€” all work
7. **If green**: v5.0.1 acceptance gate PASS

---

## Pass/fail rule (non-negotiable)

A Block tag is FORBIDDEN if ANY:
- T1/T2/T3/T4 test red
- T5 (when applicable) red
- Codex AXIS A/B/C verdict â‰  APPROVE
- You haven't approved the diff

After tag: STATE/RESUME anchor updated, PORT_LOG row materialized, V5_BUILD_STATUS bumped, next Block starts.

**Total estimated build time** (with you reviewing each Block): 2-4 weeks of focused work. **Total estimated cost**: under $5 in AWS. **Confidence after Block J + first 5 real sessions**: ~99%.

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg --files | rg "ADR-010|ADR_010|V5_DESIGN_DECISIONS|ADR-023"' in D:\Github\sagemaker-coding-agent
 succeeded in 660ms:
compact_v5\_status\V5_DESIGN_DECISIONS.md

codex
I found the design-decision log and will cross-check ADR-010/023 intent to score Axis B (faithfulness vs adaptation).
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"ADR-010|ADR-023|Phase-4|approval|rate limit|Block C\\+|PermissionDialog|render_warnings\" 'compact_v5/_status/V5_DESIGN_DECISIONS.md'" in D:\Github\sagemaker-coding-agent
 succeeded in 490ms:
255:- Source: Runnable `src/Tool.ts` (`Tool` interface + `buildTool` defaults) + v4 `compact_v4/MAIN/agent/sagemaker_agent.py:7105` (`TOOLS = {name: (callable, requires_approval, description, schema)}`)
258:- **REPLACEMENT.** Replaces v4's monolithic `TOOLS = {...}` 4-tuple dict (`(callable, requires_approval, description, schema)` per entry) with a typed `ToolDef` Protocol. Each tool becomes a small object with named attributes instead of a positional 4-tuple, which silently grew confusing as fields were added.
282:  - `is_destructive` (Runnable: `isDestructive()`) — surfaced in approval prompt
284:  - `requires_approval` (v4-native; Runnable splits this into `checkPermissions()`) — kept v4-style for Bedrock/SageMaker constraint where approval flow is ipywidgets-driven, not a TS permission context
343:- Justification: Runnable's permission context exists because the Anthropic-direct CLI has multi-source rules (user config, project config, settings, MCP server scopes). v5's Bedrock-only `.ipynb` has none of those sources — approval is a single ipywidgets prompt per call. Constraint = **`.ipynb`** (single approval source).
345:- Down-stream wiring: tools' `requires_approval` flag drives the ipywidgets approval prompt; v5 does NOT call Runnable's `checkPermissions()` (which returns a structured `PermissionResult`) because there's no permission context to check against. Instead, `requires_approval=True` triggers the user prompt directly. Documented as a v4-native ADAPT, not drift.
348:Auto-reject avoidance: constraint is **`.ipynb`** (not `none`), so this is a legitimate `FAITHFUL-WITH-JUSTIFIED-ADAPTATION` — the simpler permission-context tuple is forced by the .ipynb single-source approval flow.
394:- Each tool flagged: `is_read_only=True`, `is_concurrency_safe=True` (Runnable parity — read-only ops are safe in parallel), `requires_approval=False`.
430:## ADR-010 — Phase 4 mutating tools: REUSE v4 executors + ADAPT Runnable prompts + diff_widget UI
437:  - V5_PLAN.md Phase 4 acceptance criterion: edit_file, write_file, AND notebook_edit approval prompts each show colored before/after diff inline (red removed, green added, gray context) with file path header + line numbers + ±3 lines context + click-to-expand-full-file using `ui/diff_widget.py` BEFORE user clicks Approve.
441:- **ADDITION** for `ui/diff_widget.py` — the UX pattern is novel to v5 (v4 didn't show colored inline diffs in the approval prompt; user only saw a text summary). Adopted from Runnable's `EditTool/UI.tsx` Ink renderer pattern.
456:**Yes**. Misplaced-edit prevention is exactly the kind of user-visible improvement V5_PLAN.md's "addition gate" requires. The cost (~150 LOC + 0 tokens) is negligible vs the value (catches a documented v4 failure mode at approval time, before the bad edit lands).
460:  - `tools/write_file.py` — REUSE v4 executor + ADAPT Runnable prompt text. Requires `read_before_overwrite` (matches v4 contract). `requires_approval=True`.
461:  - `tools/edit_file.py` — REUSE v4 executor + ADAPT Runnable prompt text. Requires `read_first` (matches v4 contract). Exact match + `replace_all` flag. `requires_approval=True`.
462:  - `tools/notebook_edit.py` — REUSE v4 executor (insert/replace/delete cells). Atomic write (tmp file + rename) preserved. `requires_approval=True`.
464:  - `ui/diff_widget.py` — generates HTML diff strings (red removed, green added, gray context, file path header, ±3 lines context, `<details>`-wrapped full-file expansion). Phase 11 wires into the ipywidgets approval flow.
477:- compact_v5/MAIN/agent/tools/_file_read_tracking.py (new, Phase-4-only stub)
505:  - v4 `:10487` (`HIGH_RISK_TOOLS = {"bash", "python_exec", "task", "web_fetch"}` — used by approval-prompt UX)
552:- `.ipynb` constraint forces no Ink/JSX in the bash/python_exec UI — text output flows back through the existing approval prompt.
1127:## ADR-024 — Block C+ (v5.0.1): Approval/diff dispatch + rate limits + ipywidgets fallback + Block-C UI remaps
1130:**Phase ID**: v5.0.1 Block C+
1136:was explicitly deferred to Block C+ per ADR-023's "Notes / known
1137:scope remaps" table. Block C+ also adds the approval gate (Phase 4
1138:ADR-010 commitment) + rate limiter (v4 :8731-8740) + per-tool
1142:Single `ui/approval_dialog.py` module with three exports:
1143:  - `PermissionDialog` — per-tool dialog, ipywidgets + text-mode paths.
1145:  - `RateLimiter` — sliding-window message rate limit + per-session cap.
1165:4. **Block-C helper integration.** PermissionDialog.render_warnings()
1172:- NEW: `compact_v5/MAIN/agent/ui/approval_dialog.py` (~280 LOC)
1174:- MODIFIED: `compact_v5/MAIN/agent/core/query_engine.py` (gate + rate limiter wiring)
1177:- #064 — PermissionDialog + RateLimiter + Block-C UI remap wiring
1182:- Closes ADR-023 §Notes / known scope remaps for Block-C UI items
1183:  (C-11/C-12/C-13/C-14 lock-tested via test_approval_renders_*).
1185:## ADR-023 — Block C (v5.0.1): Runtime safety + JSON repair + injection scan + bash hardening + ADR-020 0-5 / 0-10 remap
1248:  --force / redis FLUSHALL. Approval flow (Block C+) consumes these.
1287:### Notes / known scope remaps (Block C UI-only helpers → Block C+)
1291:unwired helpers are all approval/UI surface — they feed Block C+'s
1292:approval flow + history display rather than the core dispatch path.
1297:| C-11 | cd+git compound bare-repo guard | 40 | **Block C+** (approval flow) | `ui/approval_dialog.py`: surface warning before bash exec | `test_approval_warns_on_cd_git_bare_repo` (Block C+) |
1298:| C-12 | Multiple-cd detection | 10 | **Block C+** (approval flow) | `ui/approval_dialog.py`: bump approval requirement for multi-cd | `test_approval_required_on_multi_cd` (Block C+) |
1299:| C-13 | Pipe-segment per-segment permission | 30 | **Block C+** (approval flow) | `ui/approval_dialog.py`: per-segment approval line | `test_approval_per_pipe_segment` (Block C+) |
1300:| C-14 | Bash comment-label extraction | 15 | **Block C+** (UI history) | `ui/widgets.py:HistoryRow`: render comment as label | `test_history_row_labels_with_bash_comment` (Block C+) |
1303:with 100% test coverage. Block C+ wiring is API-stable — no helper
1309:Block C+ adds the pre-exec approval surface). Lock coverage already

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/_status/V5_DESIGN_DECISIONS.md' -TotalCount 1220 | Select-Object -Last 120" in D:\Github\sagemaker-coding-agent
 succeeded in 662ms:
  - `compact_v5/_rebuild_zip.py` â€” adapted from v4. Walks `MAIN/agent/` in v5 layout. Preserves nested packages. Excludes tests/changelogs/_status/docs/_archive/__pycache__.
  - `compact_v5/verify_ship_zip.py` â€” adapts v4's verifier to v5's runtime file list (chat.ipynb, chat.md, entry.py, agent/__init__.py, core/, tools/, skills/, runtime/, prompt/, ui/, subagent/, security/, mcp/, memory.md, AGENT_STATUS.md).
  - `compact_v5/CHANGELOG.md` â€” top-level v5 release notes summarizing all phases.
  - `compact_v5/README.md` â€” minimal: how to extract + run chat.ipynb.
  - Final tag: `v5.0.0` after the zip extracts cleanly + verify_ship_zip passes.
- Phase 13 does NOT: merge to main (v4 stays on main; v5 lives on `v5-build` until user explicitly ships); upload zip to a release; auto-deploy.

### Budget reservation
- Static prompt: +0.
- Per-turn: +0.

### Reconciliation
After Phase 13 lands:
- `compact_v5.zip` extracts to a flat-ish layout and `chat.ipynb` opens cleanly.
- `verify_ship_zip.py` reports PASS.
- Tests still 437/4 (Phase 12 baseline).
- Final tag `v5.0.0` created.

### Linked port-log rows
- #036 â€” v4 _rebuild_zip.py â†’ compact_v5/_rebuild_zip.py (ADAPT â€” walks v5 nested-package layout).
- #037 â€” v4 verify_ship_zip.py â†’ compact_v5/verify_ship_zip.py (ADAPT â€” v5 runtime file list).

---

## (Append future ADRs below this line â€” keep numerical order 020, 021, ...)

## ADR-024 â€” Block C+ (v5.0.1): Approval/diff dispatch + rate limits + ipywidgets fallback + Block-C UI remaps

**Date**: 2026-05-03
**Phase ID**: v5.0.1 Block C+
**Status**: ACCEPTED

### Context
Block C shipped runtime safety helpers (destructive catalog, cd+git
guard, multi-cd, pipe-segment, comment-label) but their UI-flow wiring
was explicitly deferred to Block C+ per ADR-023's "Notes / known
scope remaps" table. Block C+ also adds the approval gate (Phase 4
ADR-010 commitment) + rate limiter (v4 :8731-8740) + per-tool
always-allow + reason prompt + ipywidgets-headless fallback.

### Decision
Single `ui/approval_dialog.py` module with three exports:
  - `PermissionDialog` â€” per-tool dialog, ipywidgets + text-mode paths.
  - `ApprovalResult` â€” dataclass (approved / always_allow / reason / timed_out).
  - `RateLimiter` â€” sliding-window message rate limit + per-session cap.

Wire-in QueryEngine.run():
  - Rate limit check at run() entry; on hit, return `stop_reason="rate_limited"`
    without consuming budget.
  - Approval gate before tool.execute(): when both flags set AND
    `client.mock_mode is False`, prompt + block on user decision.

### Key contracts (locked by tests)
1. **mock_mode bypass.** When `client.mock_mode=True` (test runs), the
   gate is silent â€” tests don't wedge on stdin. Verified via existing
   525-test suite which constructs all clients with `mock_mode=True`.
2. **Sticky always-allow.** First-time Always-allow stores
   `CONFIG._always_allowed[tool_name] = True`; subsequent dialogs
   short-circuit to ApprovalResult(approved=True, always_allow=True,
   reason="sticky: ..."). Sticky check runs FIRST (before
   `_override_decision`) so even tests with overrides honor it.
3. **Headless watchdog.** ipywidgets-unavailable â†’ text-mode prompt
   with 60s timeout; non-TTY stdin â†’ defaults to DENY (never silent
   auto-approve).
4. **Block-C helper integration.** PermissionDialog.render_warnings()
   pulls from `security.bash_safety` for the four Block-C UI-only
   helpers (C-11/C-12/C-13/C-14) and surfaces them in the dialog body.
5. **Rate limit sliding window.** Drops timestamps older than 60s
   before count; per-session cap separate from per-minute cap.

### Affected files
- NEW: `compact_v5/MAIN/agent/ui/approval_dialog.py` (~280 LOC)
- NEW: `compact_v5/MAIN/agent/tests/integration/test_block_c_plus.py` (14 tests)
- MODIFIED: `compact_v5/MAIN/agent/core/query_engine.py` (gate + rate limiter wiring)

### Linked port-log rows
- #064 â€” PermissionDialog + RateLimiter + Block-C UI remap wiring

### Validation
- 525 pass + 5 skipped (was 511 + 5 at end of Block C; +14 net new).
- verify_ship_zip.py: PASS (109 files / 292.8 KB / 37%).
- Closes ADR-023 Â§Notes / known scope remaps for Block-C UI items
  (C-11/C-12/C-13/C-14 lock-tested via test_approval_renders_*).

## ADR-023 â€” Block C (v5.0.1): Runtime safety + JSON repair + injection scan + bash hardening + ADR-020 0-5 / 0-10 remap

**Date**: 2026-05-03
**Phase ID**: v5.0.1 Block C
**Status**: ACCEPTED

### Context
v5.0.0 left several runtime-safety gaps that PS#7 + Wave-5-DEEP R1/R5
flagged: 40-call exec limit hit mid-task, no JSON repair on malformed
tool args, no injection scanner on skill bodies, secret-scanner light
on patterns (13 vs Runnable's 38), no Windows-edit safety (UTF-16 BOM,
UNC, CRLF, smart quotes, OneDrive mtime drift), no bash-side exit-code
semantics or destructive-command catalog. Block C closes all of these
plus ADR-020 remap rows 0-5 (scratchpad) and 0-10 (v4-native injection
scanner).

### Decision
Pure additive: 5 new helper modules + 2 tool extensions + query_engine
gate wiring. Zero changes to existing class APIs.

NEW modules (all under `runtime/` or `security/` for proximity to use):
- `security/json_repair.py` (~115 LOC) â€” Hermes-style malformed-JSON
  repair (5 strategies, fallback `{}`).
- `security/injection_scanner.py` (~100 LOC) â€” 12 v4 patterns +
  invisible/zero-width char class.
- `security/scratchpad.py` (~110 LOC) â€” per-process scratchpad dir
  under platform tempdir; cleanup_registry-registered GC.
- `security/edit_file_safety.py` (~190 LOC) â€” quote norm + UTF-16 BOM +
  UNC reject + CRLF round-trip + Windows staleness fallback.
- `security/bash_safety.py` (~225 LOC) â€” exit-code semantics + 13-pattern
  destructive catalog + cd+git compound + multi-cd + pipe-segment
  splitter + bash-comment-label extractor.

EXTENDED:
- `security/manager.py` â€” SECRET_PATTERNS expanded 13 â†’ 38 (R5 A1).
- `tools/edit_file.py` â€” wired UNC reject + UTF-16 BOM detection + quote

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"diff_html|PermissionDialog\\(|approval_dialog|pending_approval|render_diff|diff_widget|requires_approval\" compact_v5/MAIN/agent -g \"*.py\"" in D:\Github\sagemaker-coding-agent
 succeeded in 396ms:
compact_v5/MAIN/agent\core\query_engine.py:229:            from ui.approval_dialog import RateLimiter
compact_v5/MAIN/agent\core\query_engine.py:555:                # AND tool.requires_approval are BOTH True (and we're not
compact_v5/MAIN/agent\core\query_engine.py:569:                        and getattr(tool, "requires_approval", False)):
compact_v5/MAIN/agent\core\query_engine.py:574:                            from ui.approval_dialog import PermissionDialog
compact_v5/MAIN/agent\core\query_engine.py:578:                            _dlg = PermissionDialog(
compact_v5/MAIN/agent\ui\approval_dialog.py:4:AND the tool's `requires_approval=True`. The dialog surfaces:
compact_v5/MAIN/agent\ui\approval_dialog.py:6:  - Optional diff preview (edit_file / write_file via ui/diff_widget)
compact_v5/MAIN/agent\ui\approval_dialog.py:52:    diff_html: Optional[str] = None
compact_v5/MAIN/agent\ui\approval_dialog.py:185:        if self.diff_html:
compact_v5/MAIN/agent\ui\approval_dialog.py:186:            body_parts.append(widgets.HTML(value=self.diff_html))
compact_v5/MAIN/agent\ui\approval_dialog.py:213:        if self.diff_html:
compact_v5/MAIN/agent\ui\diff_widget.py:1:"""V5 ui/diff_widget.py — colored inline + expandable diff for the approval prompt.
compact_v5/MAIN/agent\ui\__init__.py:5:- `diff_widget.py` — Phase-4 diff renderer for write_file/edit_file/notebook_edit approval.
compact_v5/MAIN/agent\tools\bash.py:216:        requires_approval=True,      # HIGH_RISK_TOOLS membership
compact_v5/MAIN/agent\tools\edit_file.py:249:        requires_approval=True,         # ADR-010: approval prompt with diff
compact_v5/MAIN/agent\tools\glob.py:149:        requires_approval=False,
compact_v5/MAIN/agent\tools\grep.py:169:        requires_approval=False,
compact_v5/MAIN/agent\tools\list_dir.py:102:        requires_approval=False,
compact_v5/MAIN/agent\tools\notebook_edit.py:219:        requires_approval=True,
compact_v5/MAIN/agent\tools\python_exec.py:289:        requires_approval=True,      # HIGH_RISK_TOOLS membership
compact_v5/MAIN/agent\tools\read_file.py:226:        requires_approval=False,
compact_v5/MAIN/agent\tools\registry.py:5:  more (callable, requires_approval, description, schema) positional
compact_v5/MAIN/agent\tools\registry.py:76:    requires_approval: bool                  # v4-native; Runnable splits into checkPermissions()
compact_v5/MAIN/agent\tools\registry.py:114:    requires_approval: bool = False  # v4 split: defaults False, mutating tools set True
compact_v5/MAIN/agent\tools\registry.py:130:    need `is_read_only=True`; most mutating tools need `requires_approval=True`.
compact_v5/MAIN/agent\tools\skill.py:165:        requires_approval=False,
compact_v5/MAIN/agent\tools\skill_propose_patch.py:131:        requires_approval=False,    # NO approval needed — proposal is itself the approval gate
compact_v5/MAIN/agent\tools\task.py:150:        requires_approval=False,    # the *child* approval gates fire on its tool calls
compact_v5/MAIN/agent\tools\view_image.py:170:        requires_approval=False,    # Read-only image load
compact_v5/MAIN/agent\tools\tool_search.py:351:        requires_approval=False,
compact_v5/MAIN/agent\tools\write_file.py:140:        requires_approval=True,         # ADR-010: approval prompt with diff
compact_v5/MAIN/agent\tests\unit\test_diff_widget.py:1:"""Phase 04 unit tests: ui/diff_widget.py.
compact_v5/MAIN/agent\tests\unit\test_diff_widget.py:27:    from ui.diff_widget import render_inline_diff
compact_v5/MAIN/agent\tests\unit\test_diff_widget.py:42:    from ui.diff_widget import render_inline_diff
compact_v5/MAIN/agent\tests\unit\test_diff_widget.py:49:def test_inline_diff_html_escapes_special_chars():
compact_v5/MAIN/agent\tests\unit\test_diff_widget.py:51:    from ui.diff_widget import render_inline_diff
compact_v5/MAIN/agent\tests\unit\test_diff_widget.py:64:    from ui.diff_widget import render_expandable_diff
compact_v5/MAIN/agent\tests\unit\test_diff_widget.py:75:    from ui.diff_widget import render_new_file_diff
compact_v5/MAIN/agent\tests\unit\test_diff_widget.py:89:    from ui.diff_widget import render_new_file_diff
compact_v5/MAIN/agent\tests\unit\test_diff_widget.py:98:    from ui.diff_widget import render_inline_diff
compact_v5/MAIN/agent\tests\unit\test_diff_widget.py:111:    from ui.diff_widget import render_inline_diff
compact_v5/MAIN/agent\tests\unit\test_diff_widget.py:128:    from ui.diff_widget import render_inline_diff
compact_v5/MAIN/agent\tests\unit\test_diff_widget.py:146:    from ui.diff_widget import _render_unified
compact_v5/MAIN/agent\tests\tools\test_phase4_mutating_tools.py:5:   requires_approval / is_concurrency_safe per ADR-010).
compact_v5/MAIN/agent\tests\tools\test_phase4_mutating_tools.py:72:    requires_approval=True, is_concurrency_safe=False."""
compact_v5/MAIN/agent\tests\tools\test_phase4_mutating_tools.py:78:        assert t.requires_approval is True, f"{name} should require approval"
compact_v5/MAIN/agent\tests\tools\test_phase4_mutating_tools.py:87:    assert t.requires_approval is False
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:40:    from ui.approval_dialog import ApprovalResult, PermissionDialog
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:43:    dlg_approve = PermissionDialog(
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:52:    dlg_deny = PermissionDialog(
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:66:def test_approval_dialog_shows_diff():
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:67:    """When `diff_html` is provided, PermissionDialog includes it in
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:70:    from ui.approval_dialog import ApprovalResult, PermissionDialog
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:73:    dlg = PermissionDialog(
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:76:        diff_html=diff_sample,
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:81:    assert dlg.diff_html == diff_sample
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:94:    from ui.approval_dialog import ApprovalResult, PermissionDialog
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:98:    dlg1 = PermissionDialog(
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:114:    dlg2 = PermissionDialog(
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:130:    from ui.approval_dialog import RateLimiter
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:143:    from ui.approval_dialog import RateLimiter
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:155:    from ui.approval_dialog import RateLimiter
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:190:    from ui.approval_dialog import ApprovalResult, PermissionDialog
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:195:    dlg = PermissionDialog(
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:212:    from ui.approval_dialog import ApprovalResult, PermissionDialog
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:214:    dlg = PermissionDialog(
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:231:    from ui.approval_dialog import PermissionDialog
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:233:    dlg = PermissionDialog(
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:243:    from ui.approval_dialog import PermissionDialog
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:245:    dlg = PermissionDialog(
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:255:    from ui.approval_dialog import PermissionDialog
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:257:    dlg = PermissionDialog(
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:267:    from ui.approval_dialog import PermissionDialog
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:269:    dlg = PermissionDialog(
compact_v5/MAIN/agent\tests\integration\test_block_c_plus.py:286:    from ui.approval_dialog import RateLimiter
compact_v5/MAIN/agent\tests\tools\test_phase3_read_only_tools.py:7:   is_concurrency_safe, requires_approval).
compact_v5/MAIN/agent\tests\tools\test_phase3_read_only_tools.py:82:    is_concurrency_safe=True, requires_approval=False (ADR-009)."""
compact_v5/MAIN/agent\tests\tools\test_phase3_read_only_tools.py:89:    assert tool.requires_approval is False
compact_v5/MAIN/agent\tests\unit\test_registry.py:55:    assert t.requires_approval is False
compact_v5/MAIN/agent\tests\tools\test_phase5_bash_python.py:5:  is_destructive=True, requires_approval=True, is_concurrency_safe=False).
compact_v5/MAIN/agent\tests\tools\test_phase5_bash_python.py:53:    """bash + python_exec both: is_destructive, requires_approval,
compact_v5/MAIN/agent\tests\tools\test_phase5_bash_python.py:60:        assert t.requires_approval is True, f"{name} should require approval"
compact_v5/MAIN/agent\tests\integration\test_query_engine.py:437:        requires_approval=True,
compact_v5/MAIN/agent\tests\unit\test_tool_search.py:39:    assert t.requires_approval is False

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/tests/integration/test_query_engine.py'" in D:\Github\sagemaker-coding-agent
 succeeded in 471ms:
"""Phase 08 integration tests: core/query_engine.py â€” end-to-end agent loop.

Acceptance criterion (V5_PLAN.md Â§Phase 8):
- end-to-end mock test (tool_use â†’ tool runs â†’ final answer)
- tool_search deferred-loading round-trip works

Locks PORT_LOG #019: Runnable QueryEngine.ts adapted to v5 .ipynb shape.
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

import pytest

_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# Test fixtures
# ============================================================

class _ScriptedClient:
    """Mock Bedrock client that returns pre-scripted responses in order.

    Each entry is one of:
      - ("text", "final answer")              â†’ stop_reason=end_turn, no tools
      - ("tool", call_id, tool_name, args)    â†’ tool_use block
      - ("text+tool", text, call_id, name, args) â†’ both text and tool_use
    """

    def __init__(self, script):
        self.script = list(script)
        self.calls = []  # list of (messages, tools_payload)

    def chat(self, messages, system, tools, max_tokens, temperature,
             thinking_enabled, thinking_budget):
        from runtime.bedrock_client import Response, ToolCall
        self.calls.append({
            "messages": list(messages),
            "tools": list(tools or []),
        })
        if not self.script:
            return Response(text="(no more scripted responses)", tool_calls=[],
                            stop_reason="end_turn", usage={})
        kind, *rest = self.script.pop(0)
        if kind == "text":
            return Response(text=rest[0], tool_calls=[], stop_reason="end_turn", usage={})
        if kind == "tool":
            cid, name, args = rest
            return Response(
                text="", tool_calls=[ToolCall(cid, name, args)],
                stop_reason="tool_use", usage={},
            )
        if kind == "text+tool":
            txt, cid, name, args = rest
            return Response(
                text=txt,
                tool_calls=[ToolCall(cid, name, args)],
                stop_reason="tool_use", usage={},
            )
        raise AssertionError(f"unknown script kind: {kind}")


@pytest.fixture(autouse=True)
def fresh_registry():
    """Phase 7 / Phase 2 tests mutate the registry; force-reset for Phase 8."""
    from tools.registry import _reset_registry_for_tests
    from tools import bootstrap_built_ins
    _reset_registry_for_tests()
    bootstrap_built_ins()
    yield


# ============================================================
# Test 1 â€” basic single-turn end_turn
# ============================================================

def test_engine_returns_final_text_on_end_turn():
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([("text", "Hello world.")])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="say hi",
        system_prompt="you are an assistant",
        tools=all_registered(),
    )
    assert result.stop_reason == "end_turn"
    assert result.text == "Hello world."
    assert result.turns_used == 1


# ============================================================
# Test 2 â€” tool_use â†’ tool runs â†’ tool_result â†’ final answer
# ============================================================

def test_engine_dispatches_tool_then_finalizes():
    from core import QueryEngine
    from tools import all_registered

    # Turn 1: model asks for read_file. Turn 2: model gives final answer.
    client = _ScriptedClient([
        ("tool", "call_1", "read_file", {"file_path": "nonexistent_for_test.txt"}),
        ("text", "I read the file."),
    ])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="read a file",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "end_turn"
    assert result.text == "I read the file."
    assert result.turns_used == 2
    # Conversation must contain: user, assistant(tool_use), user(tool_result), assistant(text).
    roles = [m["role"] for m in result.messages]
    assert roles == ["user", "assistant", "user", "assistant"]
    # The tool_result block must have correct tool_use_id.
    tr_block = result.messages[2]["content"][0]
    assert tr_block["type"] == "tool_result"
    assert tr_block["tool_use_id"] == "call_1"


# ============================================================
# Test 3 â€” Phase 7 wiring contract: tools= payload excludes deferred tools by default
# ============================================================

def test_engine_excludes_deferred_tools_from_first_turn_payload():
    """First turn, no tool_search calls yet: per-turn `tools=` must NOT include
    view_image, list_dir, notebook_edit. tool_search itself MUST be included."""
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([("text", "ok")])
    engine = QueryEngine(client=client, max_turns=2)
    engine.run(
        user_message="hi",
        system_prompt="sys",
        tools=all_registered(),
    )
    sent_tools = client.calls[0]["tools"]
    sent_names = {t["name"] for t in sent_tools}
    assert "tool_search" in sent_names
    assert "view_image" not in sent_names
    assert "list_dir" not in sent_names
    assert "notebook_edit" not in sent_names
    # Phase 9 added `task` tool with should_defer=True â€” must also be excluded.
    assert "task" not in sent_names
    # Phase 10 added `skill` and `skill_propose_patch` with should_defer=True.
    assert "skill" not in sent_names
    assert "skill_propose_patch" not in sent_names
    # high-frequency tools must remain visible
    assert "read_file" in sent_names
    assert "edit_file" in sent_names


# ============================================================
# Test 4 â€” Phase 7 round-trip: tool_search promotes deferred tool into next turn
# ============================================================

def test_tool_search_round_trip_promotes_deferred_tool():
    """Phase 8 acceptance: model calls tool_search â†’ query_engine extracts the
    discovered names â†’ next turn's `tools=` payload includes those tools.

    The hidden marker `<!-- v5_discovered:NAME --> ` emitted by tool_search is
    extracted via `tool_search_discovered_names()` and the named tool's full
    schema is added to the next turn's payload."""
    from core import QueryEngine
    from tools import all_registered

    # Turn 1: model calls tool_search for view_image (a deferred tool).
    # Turn 2: model now calls view_image (its schema was promoted).
    # Turn 3: model gives final answer.
    client = _ScriptedClient([
        ("tool", "call_1", "tool_search", {"query": "select:view_image"}),
        ("tool", "call_2", "view_image", {"file_path": "nonexistent.png"}),
        ("text", "Done."),
    ])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="look at an image",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "end_turn"
    assert result.turns_used == 3

    # Turn 1 payload: view_image is NOT in tools=
    turn1_names = {t["name"] for t in client.calls[0]["tools"]}
    assert "view_image" not in turn1_names
    assert "tool_search" in turn1_names

    # Turn 2 payload: view_image IS in tools= (promoted by Phase 7 wiring)
    turn2_names = {t["name"] for t in client.calls[1]["tools"]}
    assert "view_image" in turn2_names, (
        "view_image must be promoted into per-turn payload after tool_search "
        "discovered it"
    )


# ============================================================
# Test 5 â€” IterationBudget gate stops the loop
# ============================================================

def test_engine_stops_on_budget_exhausted():
    """Pre-consume the budget so the first turn can't be entered."""
    from core import QueryEngine, IterationBudget
    from tools import all_registered

    budget = IterationBudget(max_iterations=2)
    budget.consume()
    budget.consume()  # exhausted

    client = _ScriptedClient([("text", "should not be reached")])
    engine = QueryEngine(client=client, max_turns=5, budget=budget)
    result = engine.run(
        user_message="hi",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "budget_exhausted"
    assert result.turns_used == 0
    assert client.calls == []  # client.chat() was never called


# ============================================================
# Test 6 â€” max_turns cap
# ============================================================

def test_engine_stops_at_max_turns():
    """If model never returns end_turn, the loop must exit cleanly at max_turns."""
    from core import QueryEngine
    from tools import all_registered

    # Always returns tool_use for read_file â†’ engine never reaches end_turn.
    looping_script = [
        ("tool", f"call_{i}", "read_file", {"file_path": f"x{i}.txt"})
        for i in range(20)
    ]
    client = _ScriptedClient(looping_script)
    engine = QueryEngine(client=client, max_turns=3)
    result = engine.run(
        user_message="loop",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "max_turns"
    assert result.turns_used == 3


# ============================================================
# Test 7 â€” unknown tool name surfaces error to model
# ============================================================

def test_engine_returns_error_tool_result_for_unknown_tool():
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([
        ("tool", "call_1", "definitely_not_a_tool", {}),
        ("text", "ok, sorry"),
    ])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="call a tool that doesn't exist",
        system_prompt="sys",
        tools=all_registered(),
    )
    # Loop continues â€” model gets an error tool_result and can recover
    assert result.stop_reason == "end_turn"
    tr_block = result.messages[2]["content"][0]
    assert tr_block["is_error"] is True
    assert "unknown tool" in tr_block["content"]


# ============================================================
# Test 8 â€” tool that raises is surfaced to model, not user
# ============================================================

def test_engine_traps_tool_exception():
    from core import QueryEngine
    from tools.registry import build_tool, register, all_registered

    def boom(args, context=None):
        raise RuntimeError("kaboom")

    register(build_tool(
        name="boom_tool",
        description="raises",
        input_schema={"type": "object", "properties": {}},
        execute=boom,
        is_read_only=True,
    ))

    client = _ScriptedClient([
        ("tool", "call_1", "boom_tool", {}),
        ("text", "recovered"),
    ])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="call boom",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "end_turn"
    tr = result.messages[2]["content"][0]
    assert tr["is_error"] is True
    assert "RuntimeError" in tr["content"]
    assert "kaboom" in tr["content"]


# ============================================================
# Test 9 â€” system reminder injected for deferred tools
# ============================================================

def test_engine_injects_deferred_tools_system_reminder_on_first_turn():
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([("text", "ok")])
    engine = QueryEngine(client=client, max_turns=2)
    engine.run(
        user_message="hi",
        system_prompt="sys",
        tools=all_registered(),
    )
    sent_messages = client.calls[0]["messages"]
    last_user = sent_messages[-1]
    assert last_user["role"] == "user"
    # The system reminder must be appended as a text block on the user turn
    if isinstance(last_user["content"], list):
        joined = "\n".join(
            blk.get("text", "") for blk in last_user["content"]
            if isinstance(blk, dict)
        )
    else:
        joined = last_user["content"]
    assert "<system-reminder>" in joined
    assert "view_image" in joined
    assert "tool_search" in joined  # mentioned as the loader


# ============================================================
# Test 10 â€” context_overflow stops cleanly
# ============================================================

def test_engine_stops_on_context_overflow():
    """Bedrock raising prompt-too-long must classify as context_overflow and
    return cleanly with stop_reason set."""
    from core import QueryEngine
    from tools import all_registered

    class OverflowClient:
        def chat(self, **_kw):
            raise Exception("ValidationException: prompt is too long")

    engine = QueryEngine(client=OverflowClient(), max_turns=5)
    result = engine.run(
        user_message="hi",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "context_overflow"
    assert "context_overflow" in (result.error or "")


# ============================================================
# Test 11 â€” run_one_turn helper
# ============================================================

def test_run_one_turn_helper_applies_deferral():
    from core import run_one_turn
    from tools import all_registered

    client = _ScriptedClient([("text", "single turn")])
    response = run_one_turn(
        client=client,
        messages=[{"role": "user", "content": "hi"}],
        system_prompt="sys",
        tools=all_registered(),
    )
    assert response.text == "single turn"
    sent_names = {t["name"] for t in client.calls[0]["tools"]}
    assert "view_image" not in sent_names
    assert "tool_search" in sent_names


# ============================================================
# Test 12 â€” plan mode blocks mutating tools at dispatch
# ============================================================

def test_engine_blocks_mutating_tool_in_plan_mode():
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([
        ("tool", "call_1", "edit_file", {"file_path": "x", "old_string": "a", "new_string": "b"}),
        ("text", "noted"),
    ])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="edit a file",
        system_prompt="sys",
        tools=all_registered(),
        plan_mode=True,
    )
    tr = result.messages[2]["content"][0]
    assert tr["is_error"] is True
    assert "plan mode" in tr["content"]


# ============================================================
# Test 13 â€” Codex Phase-08 finding 2 lock: plan-mode strict allowlist
# ============================================================

def test_engine_plan_mode_blocks_always_load_mutating_tool():
    """Codex Phase-08 finding (medium) lock: a mutating tool that has
    `always_load=True` MUST still be blocked in plan mode. The previous
    dispatch gate exempted always_load tools, which would let any future
    always_load mutating tool slip past plan mode. The fix enforces a
    strict v4-style allowlist (PLAN_MODE_ALLOWED_TOOLS) at dispatch."""
    from core import QueryEngine
    from tools.registry import build_tool, register, all_registered

    register(build_tool(
        name="bypass_attempt_tool",
        description="synthetic mutating + always_load tool â€” must still be blocked in plan mode",
        input_schema={"type": "object", "properties": {}},
        execute=lambda args, context=None: "should never execute in plan mode",
        is_read_only=False,         # MUTATING
        always_load=True,           # always-loaded â€” would have bypassed old gate
        requires_approval=True,
    ))

    client = _ScriptedClient([
        ("tool", "call_1", "bypass_attempt_tool", {}),
        ("text", "blocked, ok"),
    ])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="try to bypass",
        system_prompt="sys",
        tools=all_registered(),
        plan_mode=True,
    )
    tr = result.messages[2]["content"][0]
    assert tr["is_error"] is True, (
        "Mutating always_load=True tool must still be blocked in plan mode"
    )
    assert "PLAN_MODE_ALLOWED_TOOLS" in tr["content"] or "plan mode" in tr["content"]


# ============================================================
# Test 14 â€” Codex Phase-08 finding 1 lock: discovered tools reset between runs
# ============================================================

def test_discovered_tools_reset_between_runs():
    """Codex Phase-08 finding (high) lock: `_discovered_tool_names` MUST be
    cleared at each `run()` start. Otherwise a tool_search discovery in
    run #1 would silently widen the per-turn `tools=` payload on run #2.

    Run #1: model calls tool_search to discover view_image.
    Run #2: model just sends a final answer.
    The first turn of run #2 must NOT include view_image in `tools=`.
    """
    from core import QueryEngine
    from tools import all_registered

    # Run #1: discovers view_image via tool_search.
    client_run1 = _ScriptedClient([
        ("tool", "call_1", "tool_search", {"query": "select:view_image"}),
        ("text", "discovered"),
    ])
    engine = QueryEngine(client=client_run1, max_turns=5)
    engine.run(
        user_message="discover view_image",
        system_prompt="sys",
        tools=all_registered(),
    )
    # Sanity: after run #1, view_image was promoted at some turn.
    assert "view_image" in engine._discovered_tool_names

    # Run #2: same engine, fresh user message. view_image MUST NOT be in
    # the first turn's tools= payload because the discovered set is reset.
    engine.client = _ScriptedClient([("text", "ok")])
    engine.run(
        user_message="hi again",
        system_prompt="sys",
        tools=all_registered(),
    )
    run2_first_turn_names = {t["name"] for t in engine.client.calls[0]["tools"]}
    assert "view_image" not in run2_first_turn_names, (
        "Discovered tool names from run #1 leaked into run #2's first turn payload"
    )
    # And the discovered set itself is empty after the second run starts (only
    # populated if the second run also calls tool_search, which it doesn't).
    assert "view_image" not in engine._discovered_tool_names

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/security/bash_safety.py'" in D:\Github\sagemaker-coding-agent
 succeeded in 408ms:
"""Block C C-9..C-14 â€” bash safety helpers.

Adapters of Runnable's `BashTool/commandSemantics.ts` (R1 #49) +
`BashTool/destructiveCommandWarning.ts` (R1 #50) +
`BashTool/bashCommandHelpers.ts` (R1 #53/54/55) + `BashTool/commentLabel.ts`
(R1 #48). Each helper is small and self-contained so `tools/bash.py`
can call them without growing.

Helpers:
  C-9  interpret_command_result   exit-code semantics (grep 1=no-match, etc.)
  C-10 destructive_command_warning rm -rf / git push --force / DROP TABLE / kubectl delete / terraform destroy
  C-11 has_cd_git_compound_with_bare_repo  cd into a bare git repo + git fsmonitor risk
  C-12 has_multiple_cd            `cd a && cd b && X` requires approval
  C-13 pipe_segment_permission_check  per-segment approval check
  C-14 extract_bash_comment_label  `# comment` â†’ UI history label

PORT_LOG: see #061.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple


# ============================================================
# C-9 â€” Exit-code semantics
# ============================================================

# Commands whose non-zero exit-codes have well-known non-error meanings.
# Reporting them as "command failed" misleads the model.
_NONZERO_NON_ERROR_SEMANTICS: dict = {
    "grep": {1: "no match (not an error)"},
    "egrep": {1: "no match (not an error)"},
    "fgrep": {1: "no match (not an error)"},
    "rg": {1: "no match (not an error)"},
    "find": {1: "partial result (some paths inaccessible)"},
    "diff": {1: "files differ (not an error â€” diff worked)"},
    "cmp": {1: "files differ (not an error â€” cmp worked)"},
    "test": {1: "condition false (test worked)"},
}


def interpret_command_result(command: str, exit_code: int) -> Optional[str]:
    """Return a human-readable explanation for `command`'s exit code.

    None means "no special semantics â€” surface the raw exit code".
    Per Runnable BashTool/commandSemantics.ts:1-140 (R1 #49).
    """
    if exit_code == 0 or not command:
        return None
    # First token is the command name (after stripping env-vars / sudo).
    head = command.strip().split()
    if not head:
        return None
    # Skip env-var assignments: `FOO=bar grep ...`
    while head and "=" in head[0] and not head[0].startswith("="):
        head.pop(0)
    if not head:
        return None
    cmd_name = head[0].split("/")[-1]  # strip leading path
    semantics = _NONZERO_NON_ERROR_SEMANTICS.get(cmd_name)
    if semantics and exit_code in semantics:
        return semantics[exit_code]
    return None


# ============================================================
# C-10 â€” Destructive command warnings (catalog)
# ============================================================

_DESTRUCTIVE_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\brm\s+-[rRf]+\b", re.IGNORECASE),
     "rm -rf / -fR â€” recursive force-delete"),
    (re.compile(r"\bgit\s+push\s+--force(-with-lease)?\b", re.IGNORECASE),
     "git push --force â€” overwrites remote history"),
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),
     "git reset --hard â€” discards local changes"),
    (re.compile(r"\bgit\s+clean\s+-[fdx]+\b", re.IGNORECASE),
     "git clean -fd / -fdx â€” deletes untracked files"),
    (re.compile(r"\bdrop\s+(table|database|schema)\b", re.IGNORECASE),
     "DROP TABLE / DATABASE / SCHEMA â€” irreversible SQL drop"),
    (re.compile(r"\btruncate\s+table\b", re.IGNORECASE),
     "TRUNCATE TABLE â€” empties a SQL table"),
    (re.compile(r"\bkubectl\s+delete\b", re.IGNORECASE),
     "kubectl delete â€” removes Kubernetes resource"),
    (re.compile(r"\bterraform\s+destroy\b", re.IGNORECASE),
     "terraform destroy â€” tears down Terraform-managed infra"),
    (re.compile(r"\bdocker\s+(rm|rmi|system\s+prune)\b", re.IGNORECASE),
     "docker rm / rmi / system prune â€” destroys containers / images"),
    (re.compile(r"\bdd\s+if=.+\s+of=/dev/", re.IGNORECASE),
     "dd of=/dev/... â€” overwrites raw block device"),
    (re.compile(r":\s*\(\s*\)\s*\{\s*:\|:&\s*\}\s*;\s*:", re.IGNORECASE),
     "fork bomb"),
    (re.compile(r"\baws\s+s3\s+rb\s+.*--force\b", re.IGNORECASE),
     "aws s3 rb --force â€” deletes S3 bucket + contents"),
    (re.compile(r"\bredis-cli\s+(-[a-z]+\s+)*flushall\b", re.IGNORECASE),
     "redis-cli FLUSHALL â€” wipes every Redis db"),
]


def destructive_command_warning(command: str) -> Optional[str]:
    """Return the first destructive-pattern label, or None.

    Per Runnable BashTool/destructiveCommandWarning.ts (R1 #50).
    Used by the approval flow to surface a clear "this is dangerous"
    message before executing.
    """
    if not command:
        return None
    for pat, label in _DESTRUCTIVE_PATTERNS:
        if pat.search(command):
            return label
    return None


# ============================================================
# C-11 â€” cd into bare git repo + fsmonitor risk
# ============================================================

_CD_GIT_COMPOUND = re.compile(
    r"\bcd\s+([^\s&;|]+).*?\bgit\b", re.IGNORECASE
)


def has_cd_git_compound_with_bare_repo(command: str) -> bool:
    """True iff command does `cd <something> && git ...` AND the cd
    target is plausibly a bare repo (ends in .git).

    Bare repos with `core.fsmonitor` enabled launch a long-running
    helper that can survive shell exit + pin file handles. Per
    Runnable BashTool/bashCommandHelpers.ts:50-82 (R1 #53).
    """
    if not command:
        return False
    m = _CD_GIT_COMPOUND.search(command)
    if not m:
        return False
    target = m.group(1).strip().strip('"').strip("'")
    return target.endswith(".git") or target.endswith(".git/")


# ============================================================
# C-12 â€” Multiple cd detection
# ============================================================

_CD_TOKEN = re.compile(r"\bcd\s+", re.IGNORECASE)


def has_multiple_cd(command: str) -> bool:
    """True iff command contains 2+ `cd ` tokens (chained dir changes).

    Per Runnable BashTool/bashCommandHelpers.ts:32-47 (R1 #54). Multiple
    cd's confuse approval semantics â€” `cd a && cd b && rm X` looks like
    rm-relative-to-cwd but actually targets `b/X`.
    """
    if not command:
        return False
    return len(_CD_TOKEN.findall(command)) >= 2


# ============================================================
# C-13 â€” Pipe-segment permission check
# ============================================================

def split_pipe_segments(command: str) -> List[str]:
    """Split a command on top-level `|` (skipping `||`).

    Per Runnable BashTool/bashCommandHelpers.ts:84-156 (R1 #55). Each
    segment is then checked individually for destructive content so a
    pipeline like `harmless_cmd | rm -rf /` doesn't slip through.
    """
    if not command:
        return []
    out: List[str] = []
    cur: list = []
    i = 0
    n = len(command)
    in_single = False
    in_double = False
    while i < n:
        ch = command[i]
        if ch == "'" and not in_double:
            in_single = not in_single
            cur.append(ch)
        elif ch == '"' and not in_single:
            in_double = not in_double
            cur.append(ch)
        elif ch == "|" and not in_single and not in_double:
            # Skip `||` (logical OR).
            if i + 1 < n and command[i + 1] == "|":
                cur.append("||")
                i += 2
                continue
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    if cur:
        out.append("".join(cur).strip())
    return [s for s in out if s]


def pipe_segment_permission_check(command: str) -> List[str]:
    """Return destructive-warning labels for any pipe segment, or [].

    Joins per-segment results â€” useful when the approval flow wants to
    show "the second segment is destructive: <reason>".
    """
    warnings: List[str] = []
    for seg in split_pipe_segments(command):
        w = destructive_command_warning(seg)
        if w:
            warnings.append(w)
    return warnings


# ============================================================
# C-14 â€” Extract bash comment label
# ============================================================

_LEADING_COMMENT = re.compile(r"^\s*#\s*(.+?)\s*(?:$|\n)")


def extract_bash_comment_label(command: str) -> Optional[str]:
    """Return the leading `# comment` text, or None.

    Used by the UI history view to label long bash invocations with
    something the user wrote. Per Runnable BashTool/commentLabel.ts
    (R1 #48).
    """
    if not command:
        return None
    m = _LEADING_COMMENT.match(command)
    if not m:
        return None
    label = m.group(1).strip()
    return label if label else None


__all__ = [
    "interpret_command_result",
    "destructive_command_warning",
    "has_cd_git_compound_with_bare_repo",
    "has_multiple_cd",
    "split_pipe_segments",
    "pipe_segment_permission_check",
    "extract_bash_comment_label",
]

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content '"'compact_v5/MAIN/agent/ui/approval_dialog.py' | ForEach-Object { '{0,4}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content '"'compact_v5/MAIN/agent/core/query_engine.py' | ForEach-Object { '{0,4}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=1; Get-Content '"'compact_v5/MAIN/agent/tests/integration/test_block_c_plus.py' | ForEach-Object { '{0,4}: {1}' -f "'$i, $_; $i++ }' in D:\Github\sagemaker-coding-agent
 succeeded in 528ms:
   1: """Block C+ â€” Approval/diff dispatch + rate limits + ipywidgets fallback.
   2: 
   3: Tests per TEST_DESIGN.md Â§Block C+ (7 tests) plus 4 lock tests for the
   4: Block C UI-only helpers (C-11/C-12/C-13/C-14) wired through the
   5: approval flow per ADR-023 Â§Notes / known scope remaps.
   6: """
   7: from __future__ import annotations
   8: 
   9: import os
  10: import sys
  11: import time
  12: 
  13: import pytest
  14: 
  15: _AGENT_ROOT = os.path.dirname(
  16:     os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  17: )
  18: if _AGENT_ROOT not in sys.path:
  19:     sys.path.insert(0, _AGENT_ROOT)
  20: 
  21: 
  22: @pytest.fixture(autouse=True)
  23: def reset_always_allowed():
  24:     """Reset CONFIG._always_allowed between tests."""
  25:     from runtime.config import CONFIG
  26:     if hasattr(CONFIG, "_always_allowed"):
  27:         CONFIG._always_allowed = {}
  28:     yield
  29:     if hasattr(CONFIG, "_always_allowed"):
  30:         CONFIG._always_allowed = {}
  31: 
  32: 
  33: # ============================================================
  34: # T2 â€” Approval gate blocks until approve / unblocks on approve
  35: # ============================================================
  36: 
  37: def test_approval_gate_blocks_until_approve():
  38:     """Approval-required tool dispatched in non-mock mode triggers
  39:     PermissionDialog. Approve â†’ tool runs. Deny â†’ tool blocked."""
  40:     from ui.approval_dialog import ApprovalResult, PermissionDialog
  41: 
  42:     # Inject decision via test override; verify the dispatch path is wired.
  43:     dlg_approve = PermissionDialog(
  44:         tool_name="bash",
  45:         parameters={"command": "echo hi"},
  46:         _override_decision=lambda: ApprovalResult(approved=True),
  47:     )
  48:     res = dlg_approve.prompt()
  49:     assert res.approved
  50:     assert not res.timed_out
  51: 
  52:     dlg_deny = PermissionDialog(
  53:         tool_name="bash",
  54:         parameters={"command": "echo hi"},
  55:         _override_decision=lambda: ApprovalResult(approved=False, reason="user denied"),
  56:     )
  57:     res = dlg_deny.prompt()
  58:     assert not res.approved
  59:     assert "denied" in res.reason
  60: 
  61: 
  62: # ============================================================
  63: # T2 â€” Approval dialog shows diff
  64: # ============================================================
  65: 
  66: def test_approval_dialog_shows_diff():
  67:     """When `diff_html` is provided, PermissionDialog includes it in
  68:     the rendered body. We verify by exercising the headless path that
  69:     the helper accepts + reports the diff string."""
  70:     from ui.approval_dialog import ApprovalResult, PermissionDialog
  71: 
  72:     diff_sample = "<pre><span style='color:red'>- a</span>"
  73:     dlg = PermissionDialog(
  74:         tool_name="edit_file",
  75:         parameters={"file_path": "/tmp/x.txt"},
  76:         diff_html=diff_sample,
  77:         _override_decision=lambda: ApprovalResult(approved=True),
  78:     )
  79:     # Sanity: the diff is preserved on the dialog object so the
  80:     # widget/text-mode renderer can include it.
  81:     assert dlg.diff_html == diff_sample
  82:     res = dlg.prompt()
  83:     assert res.approved
  84: 
  85: 
  86: # ============================================================
  87: # T2 â€” Per-tool always-allow (sticky)
  88: # ============================================================
  89: 
  90: def test_approval_per_tool_always_allow():
  91:     """Clicking Always-allow stores the tool in CONFIG._always_allowed
  92:     and subsequent dialogs short-circuit with approved=True."""
  93:     from runtime.config import CONFIG
  94:     from ui.approval_dialog import ApprovalResult, PermissionDialog
  95: 
  96:     CONFIG._always_allowed = {}
  97:     # First call: user clicks Always-allow.
  98:     dlg1 = PermissionDialog(
  99:         tool_name="write_file",
 100:         parameters={"file_path": "/tmp/y"},
 101:         _override_decision=lambda: ApprovalResult(
 102:             approved=True, always_allow=True, reason="always",
 103:         ),
 104:     )
 105:     r1 = dlg1.prompt()
 106:     assert r1.approved and r1.always_allow
 107: 
 108:     # Manually flip the sticky flag (the override didn't go through the
 109:     # ipywidgets handler that does this). Real flow: the widget click
 110:     # handler sets CONFIG._always_allowed[name] = True before returning.
 111:     CONFIG._always_allowed["write_file"] = True
 112: 
 113:     # Second call: dialog short-circuits via the sticky path.
 114:     dlg2 = PermissionDialog(
 115:         tool_name="write_file",
 116:         parameters={"file_path": "/tmp/z"},
 117:         _override_decision=lambda: pytest.fail("override should NOT fire"),
 118:     )
 119:     r2 = dlg2.prompt()
 120:     assert r2.approved
 121:     assert "sticky" in r2.reason
 122: 
 123: 
 124: # ============================================================
 125: # T2 â€” Rate limit triggers
 126: # ============================================================
 127: 
 128: def test_rate_limit_100_per_min():
 129:     """101st check() in 60s window returns a rate-limit error."""
 130:     from ui.approval_dialog import RateLimiter
 131: 
 132:     rl = RateLimiter(max_per_minute=100, max_per_session=1500)
 133:     for i in range(100):
 134:         assert rl.check() is None, f"check {i} should pass"
 135:     err = rl.check()
 136:     assert err is not None
 137:     assert "Rate limit" in err
 138:     assert "messages per minute" in err
 139: 
 140: 
 141: def test_rate_limit_session_cap():
 142:     """Session-cap kicks in even if per-minute window allows."""
 143:     from ui.approval_dialog import RateLimiter
 144: 
 145:     rl = RateLimiter(max_per_minute=10_000, max_per_session=5)
 146:     for _ in range(5):
 147:         assert rl.check() is None
 148:     err = rl.check()
 149:     assert err is not None
 150:     assert "Session message cap" in err
 151: 
 152: 
 153: def test_rate_limit_sliding_window():
 154:     """Old timestamps drop out of the window after 60s."""
 155:     from ui.approval_dialog import RateLimiter
 156: 
 157:     rl = RateLimiter(max_per_minute=2, max_per_session=100)
 158:     rl._timestamps = [time.time() - 120, time.time() - 90]  # both > 60s old
 159:     assert rl.check() is None
 160:     assert rl.check() is None  # 2 in current window
 161:     assert rl.check() is not None  # 3rd trips
 162: 
 163: 
 164: # ============================================================
 165: # T2 â€” Stop button halts run (already locked in Phase 11; sanity check)
 166: # ============================================================
 167: 
 168: def test_stop_button_halts_run():
 169:     """`Agent.stop()` mid-loop sets a flag; QueryEngine respects it
 170:     on next per-turn checkpoint. Phase 11 lock; sanity check here."""
 171:     from runtime.bedrock_client import BedrockClient
 172:     from agent import Agent
 173: 
 174:     client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
 175:     a = Agent(client=client)
 176:     a.stop()  # request stop before run() even starts
 177:     assert a._stop_requested is True
 178:     a.run("hi")
 179:     # Stop request was honored; either the run exited via stop check
 180:     # OR completed before the check (mock returns end_turn fast).
 181: 
 182: 
 183: # ============================================================
 184: # T2 â€” ipywidgets fallback when widgets unavailable
 185: # ============================================================
 186: 
 187: def test_ipywidgets_fallback_text_mode(monkeypatch):
 188:     """When ipywidgets is unavailable, PermissionDialog falls back to
 189:     text mode. We force the fallback path via a monkeypatched flag."""
 190:     from ui.approval_dialog import ApprovalResult, PermissionDialog
 191: 
 192:     # Without an override, the dialog would block on stdin. The
 193:     # _override_decision parameter short-circuits before any rendering,
 194:     # but we still verify the helper is callable in non-widget mode.
 195:     dlg = PermissionDialog(
 196:         tool_name="bash",
 197:         parameters={"command": "ls"},
 198:         _override_decision=lambda: ApprovalResult(approved=False, timed_out=True),
 199:     )
 200:     res = dlg.prompt()
 201:     assert not res.approved
 202:     assert res.timed_out
 203: 
 204: 
 205: # ============================================================
 206: # T2 â€” PermissionDialog reason prompt
 207: # ============================================================
 208: 
 209: def test_permission_dialog_reason_prompt():
 210:     """The dialog accepts a `reason` from the model's tool_use input
 211:     and propagates it through to the rendered body."""
 212:     from ui.approval_dialog import ApprovalResult, PermissionDialog
 213: 
 214:     dlg = PermissionDialog(
 215:         tool_name="write_file",
 216:         parameters={"file_path": "/tmp/q.txt", "reason": "Save config"},
 217:         reason="Save config",
 218:         _override_decision=lambda: ApprovalResult(approved=True),
 219:     )
 220:     assert dlg.reason == "Save config"
 221:     res = dlg.prompt()
 222:     assert res.approved
 223: 
 224: 
 225: # ============================================================
 226: # Block C remap locks: C-11/C-12/C-13/C-14 surfaced via approval
 227: # ============================================================
 228: 
 229: def test_approval_renders_cd_git_warning():
 230:     """C-11: cd into bare repo + git fsmonitor risk surfaced in dialog."""
 231:     from ui.approval_dialog import PermissionDialog
 232: 
 233:     dlg = PermissionDialog(
 234:         tool_name="bash",
 235:         parameters={"command": "cd repo.git && git log"},
 236:     )
 237:     warnings = dlg.render_warnings()
 238:     assert any("cd into bare git repo" in w for w in warnings)
 239: 
 240: 
 241: def test_approval_renders_multi_cd_warning():
 242:     """C-12: chained cd's flagged."""
 243:     from ui.approval_dialog import PermissionDialog
 244: 
 245:     dlg = PermissionDialog(
 246:         tool_name="bash",
 247:         parameters={"command": "cd /tmp && cd subdir && rm file"},
 248:     )
 249:     warnings = dlg.render_warnings()
 250:     assert any("multiple cd" in w for w in warnings)
 251: 
 252: 
 253: def test_approval_renders_pipe_segment_warning():
 254:     """C-13: destructive pipe segment surfaced."""
 255:     from ui.approval_dialog import PermissionDialog
 256: 
 257:     dlg = PermissionDialog(
 258:         tool_name="bash",
 259:         parameters={"command": "ls -la | rm -rf /tmp/foo"},
 260:     )
 261:     warnings = dlg.render_warnings()
 262:     assert any("pipe-segment" in w.lower() for w in warnings)
 263: 
 264: 
 265: def test_approval_renders_bash_comment_label():
 266:     """C-14: leading `# comment` surfaced as label."""
 267:     from ui.approval_dialog import PermissionDialog
 268: 
 269:     dlg = PermissionDialog(
 270:         tool_name="bash",
 271:         parameters={"command": "# build the docs\nmake docs"},
 272:     )
 273:     warnings = dlg.render_warnings()
 274:     assert any("label: build the docs" in w for w in warnings)
 275: 
 276: 
 277: # ============================================================
 278: # Sanity: rate limiter wired into QueryEngine.run() entry
 279: # ============================================================
 280: 
 281: def test_rate_limiter_wired_into_query_engine_run(monkeypatch):
 282:     """When the rate limit is hit, run() returns a rate_limited result
 283:     immediately without consuming budget."""
 284:     from runtime.bedrock_client import BedrockClient
 285:     from core.query_engine import QueryEngine
 286:     from ui.approval_dialog import RateLimiter
 287: 
 288:     client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
 289:     engine = QueryEngine(client=client, max_turns=2)
 290:     # Force rate limit at run() entry by pre-filling the timestamps so
 291:     # the next check() trips. max_per_minute=1, prefilled with one
 292:     # current-time stamp -> next call fails.
 293:     rl = RateLimiter(max_per_minute=1, max_per_session=1500)
 294:     rl._timestamps = [time.time()]
 295:     engine._rate_limiter = rl
 296: 
 297:     result = engine.run(
 298:         user_message="hi", system_prompt="test", tools=[],
 299:     )
 300:     assert result.stop_reason == "rate_limited"
 301:     assert "Rate limit" in (result.error or "")

 succeeded in 571ms:
   1: """Block C+ â€” PermissionDialog (approval flow + always-allow + reason prompt).
   2: 
   3: Renders a per-tool approval dialog when CONFIG.require_tool_approval=True
   4: AND the tool's `requires_approval=True`. The dialog surfaces:
   5:   - Tool name + sanitised parameters
   6:   - Optional diff preview (edit_file / write_file via ui/diff_widget)
   7:   - Optional reason string from tool_use args (Block C+ richer feature)
   8:   - Block C UI-only helper warnings: cd+git compound bare-repo (C-11),
   9:     multi-cd (C-12), per-pipe-segment destructive (C-13), bash comment-
  10:     label (C-14) â€” all surfaced when bash is the dispatched tool
  11:   - Three buttons: Approve / Deny / Always allow (per-tool sticky)
  12: 
  13: Block C+ headless contract: when ipywidgets is unavailable, the dialog
  14: falls back to a synchronous text-mode `ask_user`-style prompt with a
  15: 60-second watchdog timeout.
  16: 
  17: PORT_LOG: see #064.
  18: """
  19: from __future__ import annotations
  20: 
  21: import logging
  22: import time
  23: from dataclasses import dataclass, field
  24: from typing import Any, Callable, Dict, List, Optional
  25: 
  26: 
  27: @dataclass
  28: class ApprovalResult:
  29:     """The outcome of a single approval prompt."""
  30: 
  31:     approved: bool
  32:     always_allow: bool = False  # if True, future calls to same tool skip the dialog
  33:     reason: str = ""             # caller-supplied rationale for the decision
  34:     timed_out: bool = False
  35: 
  36: 
  37: @dataclass
  38: class PermissionDialog:
  39:     """Per-tool approval dialog. ipywidgets-aware with text fallback.
  40: 
  41:     Block C+ adds three features over the Phase-9 base:
  42:       1. always_allow toggle â€” sticky per tool name, lives in
  43:          CONFIG._always_allowed (initialized lazily).
  44:       2. reason prompt â€” surfaces the tool_use input's `reason` field
  45:          when present so the user understands intent before approving.
  46:       3. Block-C bash safety annotations â€” cd+git, multi-cd,
  47:          pipe-segment destructive warnings displayed inline.
  48:     """
  49: 
  50:     tool_name: str
  51:     parameters: Dict[str, Any] = field(default_factory=dict)
  52:     diff_html: Optional[str] = None
  53:     reason: str = ""
  54: 
  55:     # Watchdog timeout for headless / text-mode fallback.
  56:     timeout_seconds: int = 60
  57: 
  58:     # Optional callable used by tests to short-circuit the modal loop.
  59:     _override_decision: Optional[Callable[[], ApprovalResult]] = None
  60: 
  61:     # --------------------------------------------------------
  62:     # Decision driver
  63:     # --------------------------------------------------------
  64: 
  65:     def prompt(self) -> ApprovalResult:
  66:         """Show the dialog + block until decided (or timed out).
  67: 
  68:         Resolution order (sticky FIRST so always-allow short-circuits
  69:         even when callers pass an `_override_decision`):
  70:           1. CONFIG._always_allowed[tool_name] â€” auto-approve if sticky.
  71:           2. `_override_decision` â€” used by unit tests to inject answers.
  72:           3. ipywidgets dialog (Approve / Deny / Always allow buttons).
  73:           4. Text-mode fallback (ask_user-style) with watchdog timeout.
  74:         """
  75:         # 1) sticky always-allow (Block-C+ Codex finding lock test)
  76:         from runtime.config import CONFIG
  77:         if not hasattr(CONFIG, "_always_allowed"):
  78:             CONFIG._always_allowed = {}
  79:         if CONFIG._always_allowed.get(self.tool_name):
  80:             return ApprovalResult(approved=True, always_allow=True,
  81:                                   reason="sticky: tool was previously Always-allowed")
  82: 
  83:         # 2) test override
  84:         if self._override_decision is not None:
  85:             return self._override_decision()
  86: 
  87:         # 3) ipywidgets path
  88:         try:
  89:             from ui.chat_ui import _IPYWIDGETS_OK
  90:         except Exception:
  91:             _IPYWIDGETS_OK = False
  92:         if _IPYWIDGETS_OK:
  93:             return self._prompt_widgets()
  94: 
  95:         # 4) text-mode fallback (ask_user style with watchdog)
  96:         return self._prompt_text_mode()
  97: 
  98:     # --------------------------------------------------------
  99:     # Annotation: Block-C bash safety hooks
 100:     # --------------------------------------------------------
 101: 
 102:     def render_warnings(self) -> List[str]:
 103:         """Return human-readable warnings to display alongside the dialog.
 104: 
 105:         Block C UI-only helpers (C-11/C-12/C-13/C-14) surface here when
 106:         the dispatched tool is `bash`. Per ADR-023 Â§Notes / known scope
 107:         remaps (Block C UI-only helpers â†’ Block C+).
 108:         """
 109:         warnings: List[str] = []
 110:         if self.tool_name != "bash":
 111:             return warnings
 112:         cmd = self.parameters.get("command", "")
 113:         if not cmd:
 114:             return warnings
 115:         try:
 116:             from security.bash_safety import (
 117:                 destructive_command_warning,
 118:                 has_cd_git_compound_with_bare_repo,
 119:                 has_multiple_cd,
 120:                 pipe_segment_permission_check,
 121:                 extract_bash_comment_label,
 122:             )
 123:             d = destructive_command_warning(cmd)
 124:             if d:
 125:                 warnings.append(f"âš  destructive: {d}")
 126:             if has_cd_git_compound_with_bare_repo(cmd):
 127:                 warnings.append("âš  cd into bare git repo + git command (fsmonitor risk)")
 128:             if has_multiple_cd(cmd):
 129:                 warnings.append("âš  multiple cd's â€” chained directory changes")
 130:             for seg_warn in pipe_segment_permission_check(cmd):
 131:                 warnings.append(f"âš  pipe-segment destructive: {seg_warn}")
 132:             label = extract_bash_comment_label(cmd)
 133:             if label:
 134:                 warnings.append(f"label: {label}")
 135:         except Exception:
 136:             pass
 137:         return warnings
 138: 
 139:     # --------------------------------------------------------
 140:     # ipywidgets dialog
 141:     # --------------------------------------------------------
 142: 
 143:     def _prompt_widgets(self) -> ApprovalResult:
 144:         """Block on three-button ipywidgets dialog. Best-effort render."""
 145:         try:
 146:             import ipywidgets as widgets
 147:             from IPython.display import display
 148:         except Exception:
 149:             return self._prompt_text_mode()
 150: 
 151:         decision: Dict[str, Any] = {"result": None}
 152: 
 153:         def on_approve(_btn):
 154:             decision["result"] = ApprovalResult(approved=True)
 155: 
 156:         def on_deny(_btn):
 157:             decision["result"] = ApprovalResult(approved=False, reason="user denied")
 158: 
 159:         def on_always(_btn):
 160:             from runtime.config import CONFIG
 161:             if not hasattr(CONFIG, "_always_allowed"):
 162:                 CONFIG._always_allowed = {}
 163:             CONFIG._always_allowed[self.tool_name] = True
 164:             decision["result"] = ApprovalResult(
 165:                 approved=True, always_allow=True,
 166:                 reason="user clicked Always-allow",
 167:             )
 168: 
 169:         approve_btn = widgets.Button(description="Approve", button_style="success")
 170:         deny_btn = widgets.Button(description="Deny", button_style="danger")
 171:         always_btn = widgets.Button(description="Always allow this tool",
 172:                                     button_style="warning")
 173:         approve_btn.on_click(on_approve)
 174:         deny_btn.on_click(on_deny)
 175:         always_btn.on_click(on_always)
 176: 
 177:         header = f"<b>Approve `{self.tool_name}`?</b>"
 178:         if self.reason:
 179:             header += f"<br/><i>Reason from model:</i> {self.reason}"
 180:         warning_lines = self.render_warnings()
 181:         warning_html = "<br/>".join(warning_lines) if warning_lines else ""
 182:         body_parts = [widgets.HTML(value=header)]
 183:         if warning_html:
 184:             body_parts.append(widgets.HTML(value=warning_html))
 185:         if self.diff_html:
 186:             body_parts.append(widgets.HTML(value=self.diff_html))
 187:         body_parts.append(widgets.HBox([approve_btn, deny_btn, always_btn]))
 188:         panel = widgets.VBox(body_parts)
 189:         display(panel)
 190: 
 191:         # Spin until a button clicked or watchdog fires.
 192:         deadline = time.time() + self.timeout_seconds
 193:         while decision["result"] is None and time.time() < deadline:
 194:             time.sleep(0.1)
 195:         if decision["result"] is None:
 196:             return ApprovalResult(approved=False, timed_out=True,
 197:                                   reason="watchdog timeout")
 198:         return decision["result"]
 199: 
 200:     # --------------------------------------------------------
 201:     # Text-mode fallback (ask_user-style)
 202:     # --------------------------------------------------------
 203: 
 204:     def _prompt_text_mode(self) -> ApprovalResult:
 205:         """Headless fallback: print dialog + read stdin with watchdog."""
 206:         import sys
 207: 
 208:         print(f"\n=== Approve tool `{self.tool_name}`? ===")
 209:         if self.reason:
 210:             print(f"Model reason: {self.reason}")
 211:         for w in self.render_warnings():
 212:             print(f"  {w}")
 213:         if self.diff_html:
 214:             print("[diff preview available â€” open in widget host to view]")
 215:         print(f"Parameters (sanitised): {self._sanitised_params()}")
 216:         print(f"Reply (a)pprove / (d)eny / (A)lways allow [60s timeout]:")
 217: 
 218:         # When stdin is not a TTY (notebook headless), default to deny so
 219:         # we never silently auto-approve.
 220:         if not sys.stdin.isatty():
 221:             logging.warning(
 222:                 "PermissionDialog: stdin not a TTY; defaulting to DENY"
 223:             )
 224:             return ApprovalResult(approved=False, timed_out=True,
 225:                                   reason="non-tty fallback")
 226: 
 227:         # Watchdog â€” readline doesn't natively support timeout; use a
 228:         # signal-based timer where supported, else just block + record
 229:         # the wall time.
 230:         try:
 231:             import select
 232:             t_start = time.time()
 233:             while True:
 234:                 if select.select([sys.stdin], [], [], 1)[0]:
 235:                     line = sys.stdin.readline().strip()
 236:                     if line in ("a", "approve", "y", "yes"):
 237:                         return ApprovalResult(approved=True)
 238:                     if line in ("A", "always"):
 239:                         from runtime.config import CONFIG
 240:                         if not hasattr(CONFIG, "_always_allowed"):
 241:                             CONFIG._always_allowed = {}
 242:                         CONFIG._always_allowed[self.tool_name] = True
 243:                         return ApprovalResult(approved=True, always_allow=True,
 244:                                               reason="text-mode Always-allow")
 245:                     return ApprovalResult(approved=False, reason="user denied")
 246:                 if time.time() - t_start > self.timeout_seconds:
 247:                     return ApprovalResult(approved=False, timed_out=True,
 248:                                           reason="watchdog timeout")
 249:         except (OSError, ValueError):
 250:             # select.select unsupported (e.g. Windows non-socket).
 251:             line = sys.stdin.readline().strip()
 252:             if line in ("a", "approve", "y", "yes"):
 253:                 return ApprovalResult(approved=True)
 254:             if line in ("A", "always"):
 255:                 from runtime.config import CONFIG
 256:                 if not hasattr(CONFIG, "_always_allowed"):
 257:                     CONFIG._always_allowed = {}
 258:                 CONFIG._always_allowed[self.tool_name] = True
 259:                 return ApprovalResult(approved=True, always_allow=True)
 260:             return ApprovalResult(approved=False, reason="user denied")
 261: 
 262:     # --------------------------------------------------------
 263:     # Helpers
 264:     # --------------------------------------------------------
 265: 
 266:     def _sanitised_params(self) -> Dict[str, Any]:
 267:         """Truncate big strings; redact secret-looking keys."""
 268:         out: Dict[str, Any] = {}
 269:         for k, v in self.parameters.items():
 270:             if any(s in k.lower() for s in (
 271:                 "password", "secret", "key", "token", "credential",
 272:             )):
 273:                 out[k] = "[REDACTED]"
 274:             elif isinstance(v, str) and len(v) > 200:
 275:                 out[k] = f"[{len(v)} chars]"
 276:             else:
 277:                 out[k] = v
 278:         return out
 279: 
 280: 
 281: # ============================================================
 282: # Rate limiter (Block C+ â€” port of v4 :8731-8740)
 283: # ============================================================
 284: 
 285: class RateLimiter:
 286:     """Sliding-window message rate limiter.
 287: 
 288:     100 user messages per 60s window per v4 default + per-session cap.
 289:     Used at QueryEngine.run() entry. When rate exceeded, run() returns
 290:     a clear error result without spending iteration budget.
 291:     """
 292: 
 293:     def __init__(self, max_per_minute: int = 100, max_per_session: int = 1500):
 294:         self.max_per_minute = max(1, int(max_per_minute))
 295:         self.max_per_session = max(1, int(max_per_session))
 296:         self._timestamps: List[float] = []
 297:         self._session_count = 0
 298: 
 299:     def check(self) -> Optional[str]:
 300:         """Return None if OK, or an error message if rate-limited.
 301: 
 302:         Caller must call this BEFORE any work that consumes budget.
 303:         """
 304:         now = time.time()
 305:         # Drop stamps older than 60s.
 306:         cutoff = now - 60.0
 307:         self._timestamps = [t for t in self._timestamps if t >= cutoff]
 308:         if len(self._timestamps) >= self.max_per_minute:
 309:             wait = int(60 - (now - self._timestamps[0]))
 310:             return (
 311:                 f"Rate limit hit: {self.max_per_minute} messages per minute. "
 312:                 f"Try again in ~{max(1, wait)}s."
 313:             )
 314:         if self._session_count >= self.max_per_session:
 315:             return (
 316:                 f"Session message cap hit ({self.max_per_session}). "
 317:                 "Start a new session to continue."
 318:             )
 319:         self._timestamps.append(now)
 320:         self._session_count += 1
 321:         return None
 322: 
 323:     def reset(self) -> None:
 324:         self._timestamps = []
 325:         self._session_count = 0
 326: 
 327: 
 328: __all__ = ["ApprovalResult", "PermissionDialog", "RateLimiter"]

 succeeded in 582ms:
   1: """V5 core/query_engine.py â€” main agent loop (Phase 8 deliverable, ADR-014).
   2: 
   3: Per ADR-014: minimal, focused port of Runnable's `QueryEngine.ts` (1295 LOC)
   4: adapted to the v5 .ipynb shape. v4's monolithic `Agent.run` (~1500 LOC) is
   5: replaced by this ~400 LOC module with explicit IN-SCOPE / OUT-OF-SCOPE.
   6: 
   7: PORT_LOG: #019.
   8: 
   9: IN SCOPE (Phase 8):
  10: - Per-turn loop with end_turn / max_turns / budget exhausted exits.
  11: - IterationBudget gate at the top of each turn (shared with sub-agents).
  12: - Phase 7 deferred-loading wiring contract:
  13:     * `apply_tool_search_deferral(tools, enabled=True)` per turn.
  14:     * `tool_search_discovered_names()` extraction from tool_search results.
  15:     * Discovered names are added to the next turn's tools= API param.
  16: - Tool dispatch via `find_tool_by_name(...).execute(args, context)`.
  17: - tool_use â†’ tool_result message accumulation in the model-visible
  18:   conversation buffer.
  19: - Bedrock invocation through `BedrockClient.chat(...)`.
  20: - System prompt assembly via `prompt.build_system_prompt(ctx)`.
  21: - run_one_turn(...) helper for unit tests (single-turn, no loop).
  22: 
  23: OUT OF SCOPE â€” explicitly deferred to later phases (per ADR-014):
  24: - Microcompact / context_collapse â€” Phase 11 UX (PS Issue #4 widget surface).
  25: - 2-stage smart compaction (prune + LLM summary) â€” Phase 11.
  26: - Skill auto-trigger â€” Phase 10 (`SKILLS.discover_relevant`).
  27: - Plan mode injection of skills into prompt â€” Phase 10.
  28: - Sub-agent forkSubagent â€” Phase 9 (`subagent/spawn.py`).
  29: - File-read state tracking â€” Phase 4 already lands this; engine respects but
  30:   doesn't reset on compact (no compact in Phase 8).
  31: - Diminishing-returns / repetition guard â€” deferred.
  32: - Notebook UX (output_fn callback contract) â€” Phase 11 owns the UI shape;
  33:   Phase 8 takes a `output_fn: Callable[[str], None] = print` so tests can
  34:   capture, but real notebook integration lives in Phase 11.
  35: 
  36: The engine is thread-safe ONLY in the sense that IterationBudget is. Multiple
  37: concurrent `run()` calls on the same engine are NOT supported (matches v4).
  38: """
  39: from __future__ import annotations
  40: 
  41: import json
  42: import logging
  43: from dataclasses import dataclass, field
  44: from typing import Any, Callable, Dict, List, Optional, Set, Tuple
  45: 
  46: from .budget import IterationBudget
  47: from .errors import BedrockErrorCategory, ErrorClassifier
  48: 
  49: 
  50: # ============================================================
  51: # Result envelope
  52: # ============================================================
  53: 
  54: @dataclass
  55: class QueryResult:
  56:     """Outcome of a `QueryEngine.run(...)` call.
  57: 
  58:     `text`           â€” final assistant text (last end_turn turn's text block).
  59:     `messages`       â€” full message buffer including the user turn that
  60:                        triggered this call. Caller may discard or persist.
  61:     `stop_reason`    â€” "end_turn" | "max_turns" | "budget_exhausted" |
  62:                        "context_overflow" | "fatal_error".
  63:     `turns_used`     â€” count of model turns executed during this run.
  64:     `budget_used`    â€” IterationBudget.used() snapshot at exit.
  65:     `error`          â€” short message when stop_reason indicates failure.
  66:     """
  67:     text: str = ""
  68:     messages: List[Dict[str, Any]] = field(default_factory=list)
  69:     stop_reason: str = ""
  70:     turns_used: int = 0
  71:     budget_used: int = 0
  72:     error: Optional[str] = None
  73: 
  74: 
  75: # ============================================================
  76: # Helpers
  77: # ============================================================
  78: 
  79: def _build_tools_api_payload(tools: List[Any]) -> List[Dict[str, Any]]:
  80:     """Convert ToolRecord list into Bedrock `tools=` API payload shape.
  81: 
  82:     Bedrock expects: [{"name": ..., "description": ..., "input_schema": ...}, ...]
  83:     """
  84:     out: List[Dict[str, Any]] = []
  85:     for t in tools:
  86:         out.append({
  87:             "name": t.name,
  88:             "description": t.description,
  89:             "input_schema": t.input_schema,
  90:         })
  91:     return out
  92: 
  93: 
  94: def _coerce_tool_result_to_text(value: Any) -> str:
  95:     """Map any tool-execute return value into a Bedrock tool_result text string.
  96: 
  97:     Tool implementations return diverse shapes (str / dict / list). Bedrock's
  98:     tool_result content needs a string. Prefer str() for primitives, JSON for
  99:     structured shapes â€” same convention as v4 dispatch."""
 100:     if isinstance(value, str):
 101:         return value
 102:     if isinstance(value, (dict, list, tuple)):
 103:         try:
 104:             return json.dumps(value, ensure_ascii=False, default=str)
 105:         except Exception:
 106:             return str(value)
 107:     return str(value)
 108: 
 109: 
 110: def _truncate_tool_result(text: str, max_chars: int) -> str:
 111:     if max_chars <= 0 or len(text) <= max_chars:
 112:         return text
 113:     head = text[: max_chars - 200]
 114:     return (
 115:         head
 116:         + f"\n\n[... truncated: tool_result exceeded {max_chars} chars; "
 117:         f"original size {len(text)} chars ...]"
 118:     )
 119: 
 120: 
 121: # ============================================================
 122: # QueryEngine
 123: # ============================================================
 124: 
 125: class QueryEngine:
 126:     """Main agent loop. Owns the message buffer + iteration budget for one
 127:     `run()` call. Sub-agents (Phase 9) will share the same IterationBudget
 128:     instance via `forkSubagent`-style construction.
 129:     """
 130: 
 131:     DEFAULT_MAX_TURNS = 50  # v4 in-place default; UI may override per call.
 132: 
 133:     def __init__(
 134:         self,
 135:         client: Any,
 136:         max_turns: int = DEFAULT_MAX_TURNS,
 137:         budget: Optional[IterationBudget] = None,
 138:         on_stop_check: Optional[Callable[[], bool]] = None,
 139:         skill_manager: Optional[Any] = None,
 140:         agent_kind: str = "parent",
 141:         session_id: Optional[str] = None,
 142:     ):
 143:         """Construct a QueryEngine.
 144: 
 145:         Args:
 146:             client: BedrockClient (or mock with the same `chat(...)` shape).
 147:             max_turns: hard upper bound on turns per `run()` call.
 148:             budget: shared IterationBudget. If None, a fresh one is created.
 149:             on_stop_check: optional callable returning True if the user has
 150:                 requested a stop (notebook UX). Phase 11 wires this to the
 151:                 Stop button.
 152:             skill_manager: optional `skills.manager.SkillManager`. When
 153:                 supplied, the engine (a) injects the active skill body into
 154:                 the dynamic tail of the system prompt, and (b) appends a
 155:                 Hermes-filtered "skills relevant to this task" reminder to
 156:                 the first user turn (Phase 10 wiring contract â€” Codex
 157:                 Phase-10 BLOCKER fix). When None, no skill machinery runs
 158:                 â€” preserves Phase 1-8 backwards compatibility for tests.
 159:         """
 160:         self.client = client
 161:         self.max_turns = max(1, int(max_turns))
 162:         self.budget = budget if budget is not None else IterationBudget()
 163:         self.on_stop_check = on_stop_check
 164:         self.skill_manager = skill_manager
 165:         # Block B: per-agent attribution key for TOKENS.add(). "parent" by
 166:         # default; sub-agents pass their type-string ("build", "explore",
 167:         # "verify", etc.) via subagent.spawn._new_child_engine.
 168:         self.agent_kind = agent_kind
 169:         # Block B: session_id used by AUDIT.log on each tool dispatch.
 170:         # Block B+ will swap this to the SessionManager-issued id; for
 171:         # now we mint a process-lifetime id so audit lines are at least
 172:         # grouped per-engine.
 173:         if session_id is None:
 174:             import uuid as _uuid
 175:             session_id = _uuid.uuid4().hex[:12]
 176:         self.session_id = session_id
 177: 
 178:         self.messages: List[Dict[str, Any]] = []
 179:         # Tool names that have been "discovered" via tool_search this run.
 180:         # Their schemas are added to per-turn `tools=` API payload until the
 181:         # run ends. v5 does NOT persist discovery across `run()` calls â€” the
 182:         # set is fresh each user message (matches Runnable's per-message
 183:         # discovered set).
 184:         self._discovered_tool_names: Set[str] = set()
 185: 
 186:     # ------------------------------------------------------------
 187:     # Public entry: run(...)
 188:     # ------------------------------------------------------------
 189: 
 190:     def run(
 191:         self,
 192:         user_message: str,
 193:         system_prompt: str,
 194:         tools: List[Any],
 195:         plan_mode: bool = False,
 196:         output_fn: Callable[[str], None] = print,
 197:         thinking_enabled: bool = False,
 198:         thinking_budget: int = 4096,
 199:         max_tokens: int = 4096,
 200:         temperature: float = 0.0,
 201:     ) -> QueryResult:
 202:         """Execute the agent loop until a stop condition is reached.
 203: 
 204:         See class docstring for the IN-SCOPE / OUT-OF-SCOPE list.
 205:         """
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
 217:         # Block C â€” exec-limit gate (PS#7 fix) + repetition detector.
 218:         # Counters live on the QueryEngine. Codex iter-1 finding #3:
 219:         # unconditional reset at run() entry so counters DON'T leak
 220:         # across run() calls (the v4 contract; sub-agent dispatch is
 221:         # the only legitimate cross-run sharing path, handled via
 222:         # parent_engine forwarding).
 223:         self._exec_call_count = 0  # bash + python_exec only
 224:         self._recent_tool_calls: list = []  # [(name, args_hash), ...]
 225: 
 226:         # Block C+ â€” message rate limit (v4 :8731-8740). Lives on the
 227:         # engine so per-session caps are tracked.
 228:         if not hasattr(self, "_rate_limiter"):
 229:             from ui.approval_dialog import RateLimiter
 230:             from runtime.config import CONFIG as _CFG
 231:             self._rate_limiter = RateLimiter(
 232:                 max_per_minute=getattr(_CFG, "max_user_messages_per_minute", 100),
 233:                 max_per_session=getattr(_CFG, "max_user_messages_per_session", 1500),
 234:             )
 235:         _rate_msg = self._rate_limiter.check()
 236:         if _rate_msg is not None:
 237:             return QueryResult(
 238:                 text=_rate_msg,
 239:                 messages=list(self.messages),
 240:                 stop_reason="rate_limited",
 241:                 turns_used=0,
 242:                 budget_used=self.budget.used(),
 243:                 error=_rate_msg,
 244:             )
 245: 
 246:         # Append user turn (Bedrock requires alternation; merge into trailing
 247:         # user if needed â€” matches v4 sagemaker_agent.py:8744).
 248:         if self.messages and self.messages[-1].get("role") == "user":
 249:             prev = self.messages[-1]
 250:             prev_content = prev.get("content", "")
 251:             if isinstance(prev_content, str):
 252:                 prev["content"] = prev_content + "\n\n" + user_message
 253:             elif isinstance(prev_content, list):
 254:                 prev_content.append({"type": "text", "text": user_message})
 255:             else:
 256:                 self.messages.append({"role": "user", "content": user_message})
 257:         else:
 258:             self.messages.append({"role": "user", "content": user_message})
 259: 
 260:         # Defer-import to avoid circular import at module-load.
 261:         from tools.registry import (
 262:             PLAN_MODE_ALLOWED_TOOLS,
 263:             apply_tool_search_deferral,
 264:             find_tool_by_name,
 265:         )
 266:         from tools.tool_search import tool_search_discovered_names
 267: 
 268:         # Phase 10 wiring (Codex BLOCKER fix): if a SkillManager is bound to
 269:         # this engine, inject (a) the active skill body into the dynamic
 270:         # tail of the system prompt and (b) a Hermes-filtered "skills
 271:         # relevant to this task" reminder onto the first user turn so the
 272:         # model sees the suggestions. The Hermes filter passes the visible
 273:         # tool names so skills with `requires_tools` are pruned when the
 274:         # required tools aren't currently available.
 275:         effective_system_prompt = system_prompt
 276:         if self.skill_manager is not None:
 277:             try:
 278:                 active_block = self.skill_manager.get_active_skill_prompt()
 279:                 if active_block:
 280:                     effective_system_prompt = system_prompt + active_block
 281:                 visible_tool_names = {t.name for t in tools}
 282:                 relevant = self.skill_manager.discover_relevant(
 283:                     user_message, active_tools=visible_tool_names,
 284:                 )
 285:                 if relevant:
 286:                     reminder = (
 287:                         "\n\n# Skills Relevant to This Task\n"
 288:                         "Consider using: " + ", ".join(relevant) +
 289:                         "\nUse the `skill` tool to activate one if it matches."
 290:                     )
 291:                     last_user = self.messages[-1]
 292:                     content = last_user.get("content")
 293:                     if isinstance(content, str):
 294:                         last_user["content"] = content + reminder
 295:                     elif isinstance(content, list):
 296:                         content.append({"type": "text", "text": reminder})
 297:             except Exception as exc:  # noqa: BLE001 â€” skill machinery never raises into agent loop
 298:                 logging.warning("[skill-wiring] %s: %s", type(exc).__name__, exc)
 299: 
 300:         last_text = ""
 301:         stop_reason = ""
 302:         turns_used = 0
 303: 
 304:         for turn in range(self.max_turns):
 305:             # User-requested stop (Phase 11 wires this to the Stop button).
 306:             if self.on_stop_check and self.on_stop_check():
 307:                 output_fn("[Stopped by user]")
 308:                 stop_reason = "user_stop"
 309:                 break
 310: 
 311:             # Budget gate â€” shared with sub-agents (Phase 9).
 312:             if not self.budget.consume():
 313:                 used, total = self.budget.used(), self.budget.total()
 314:                 output_fn(
 315:                     f"[Budget exhausted: {used}/{total} iterations used. "
 316:                     "Adjust IterationBudget or start a new session.]"
 317:                 )
 318:                 stop_reason = "budget_exhausted"
 319:                 break
 320: 
 321:             # Phase 7 wiring contract: per-turn deferral + discovery merge.
 322:             visible_tools, deferred_names = apply_tool_search_deferral(
 323:                 tools, enabled=True,
 324:             )
 325:             if self._discovered_tool_names:
 326:                 # Promote previously-discovered tools from deferred â†’ visible.
 327:                 discovered = {n for n in self._discovered_tool_names if n in deferred_names}
 328:                 if discovered:
 329:                     promoted = [
 330:                         t for t in tools
 331:                         if t.name in discovered and t.name not in {v.name for v in visible_tools}
 332:                     ]
 333:                     visible_tools = visible_tools + promoted
 334:                     deferred_names = [n for n in deferred_names if n not in discovered]
 335: 
 336:             # If any names remain deferred, surface them as a system reminder
 337:             # so the model knows they exist and how to load them.
 338:             turn_messages = list(self.messages)
 339:             if deferred_names:
 340:                 turn_messages = self._inject_deferred_reminder(turn_messages, deferred_names)
 341: 
 342:             # Bedrock invocation.
 343:             try:
 344:                 response = self.client.chat(
 345:                     messages=turn_messages,
 346:                     system=effective_system_prompt,
 347:                     tools=_build_tools_api_payload(visible_tools),
 348:                     max_tokens=max_tokens,
 349:                     temperature=temperature,
 350:                     thinking_enabled=thinking_enabled,
 351:                     thinking_budget=thinking_budget,
 352:                 )
 353:             except Exception as exc:  # noqa: BLE001 â€” classify and surface
 354:                 category, recovery, debug = ErrorClassifier.classify(exc)
 355:                 output_fn(f"[Bedrock {category}: {debug}]")
 356:                 if category == BedrockErrorCategory.CONTEXT_OVERFLOW:
 357:                     stop_reason = "context_overflow"
 358:                 else:
 359:                     stop_reason = "fatal_error"
 360:                 return QueryResult(
 361:                     text=last_text,
 362:                     messages=list(self.messages),
 363:                     stop_reason=stop_reason,
 364:                     turns_used=turns_used,
 365:                     budget_used=self.budget.used(),
 366:                     error=f"{category}: {debug}",
 367:                 )
 368: 
 369:             turns_used += 1
 370: 
 371:             # Block B (PORT_LOG #039+#040): record token usage + per-agent
 372:             # attribution. "parent" or sub-agent type-string. Best-effort â€”
 373:             # never break the agent loop if the singleton import fails.
 374:             try:
 375:                 from runtime.tokens import TOKENS as _TOKENS
 376:                 _TOKENS.add(
 377:                     response.usage or {},
 378:                     model_id=getattr(self.client, "model_id", None),
 379:                     agent_kind=self.agent_kind,
 380:                 )
 381:                 # Block B+ (PORT_LOG #052): per-turn cost-vs-budget runtime
 382:                 # warning. v4 sagemaker_agent.py:8787 prints
 383:                 #   `[Cost ${session_cost} passed budget ${limit} â€” continuing.]`
 384:                 # NOT a hard halt â€” per user 2026-05-03 update to plan v3,
 385:                 # v5 matches v4 UX: warn and continue. True hard halt is at
 386:                 # cloud-budget level (AWS Budget Action / GCP).
 387:                 from runtime.config import CONFIG as _CFG
 388:                 limit = getattr(_CFG, "session_cost_limit", 0.0)
 389:                 # Block B+ Codex finding #1 lock: `>=` so exact-100% trips
 390:                 # the warning (`>` would skip parity-100% cases).
 391:                 if limit > 0 and _TOKENS.session_cost >= limit:
 392:                     if not getattr(self, "_warned_over_budget", False):
 393:                         output_fn(
 394:                             f"[Cost ${_TOKENS.session_cost:.4f} passed "
 395:                             f"budget ${limit:.2f} â€” continuing.]"
 396:                         )
 397:                         self._warned_over_budget = True
 398:             except Exception:
 399:                 pass
 400: 
 401:             # Append assistant turn (text + tool_use blocks, plus thinking).
 402:             assistant_content = self._build_assistant_content(response)
 403:             self.messages.append({"role": "assistant", "content": assistant_content})
 404: 
 405:             if response.text:
 406:                 last_text = response.text
 407: 
 408:             # Stop conditions: end_turn / no tool_use blocks â†’ final answer.
 409:             if not response.tool_calls:
 410:                 stop_reason = "end_turn"
 411:                 if response.text:
 412:                     output_fn(response.text)
 413:                 break
 414: 
 415:             # Tool dispatch â€” emit one tool_result per tool_use call.
 416:             tool_results: List[Dict[str, Any]] = []
 417:             for call in response.tool_calls:
 418:                 tool = find_tool_by_name(tools, call.name)
 419:                 if tool is None:
 420:                     # Unknown tool name â€” return error to model so it can
 421:                     # recover (v4 parity: dispatch never raises).
 422:                     tool_results.append({
 423:                         "type": "tool_result",
 424:                         "tool_use_id": call.id,
 425:                         "content": f"Error: unknown tool '{call.name}'",
 426:                         "is_error": True,
 427:                     })
 428:                     # Block B (Codex finding #2 HIGH lock): every dispatch
 429:                     # path â€” including unknown-tool â€” must be audited so
 430:                     # forensics can see what the model attempted to call.
 431:                     try:
 432:                         from runtime.audit import AUDIT as _AUDIT
 433:                         _AUDIT.log(
 434:                             session_id=self.session_id,
 435:                             action="tool_unknown",
 436:                             tool_name=call.name,
 437:                             parameters=call.input or {},
 438:                             result_summary=f"unknown tool '{call.name}'",
 439:                             user_approved=False,
 440:                         )
 441:                     except Exception:
 442:                         pass
 443:                     continue
 444: 
 445:                 # Plan-mode dispatch gate â€” strict allowlist by name (v4
 446:                 # PLAN_MODE_ALLOWED_TOOLS, sagemaker_agent.py:9390 + 6905).
 447:                 # Codex Phase-08 finding (medium): the prior version exempted
 448:                 # `always_load=True` tools, which would let `tool_search`
 449:                 # itself (or any future always_load mutating tool) execute
 450:                 # in plan mode despite v4 forbidding it. The allowlist is
 451:                 # defense-in-depth on top of registry filtering: even if a
 452:                 # disallowed mutating tool reaches dispatch (e.g. discovered
 453:                 # via tool_search after enabled=True), it cannot run.
 454:                 # Lock test: test_engine_plan_mode_blocks_always_load_mutating_tool.
 455:                 if plan_mode and call.name not in PLAN_MODE_ALLOWED_TOOLS:
 456:                     tool_results.append({
 457:                         "type": "tool_result",
 458:                         "tool_use_id": call.id,
 459:                         "content": (
 460:                             f"Error: tool '{call.name}' is not in "
 461:                             "PLAN_MODE_ALLOWED_TOOLS; blocked in plan mode."
 462:                         ),
 463:                         "is_error": True,
 464:                     })
 465:                     # Block B (Codex finding #2 HIGH lock): plan-mode
 466:                     # block is an audit-relevant security event.
 467:                     try:
 468:                         from runtime.audit import AUDIT as _AUDIT
 469:                         _AUDIT.log(
 470:                             session_id=self.session_id,
 471:                             action="plan_mode_blocked",
 472:                             tool_name=call.name,
 473:                             parameters=call.input or {},
 474:                             result_summary=(
 475:                                 f"plan-mode allowlist blocked '{call.name}'"
 476:                             ),
 477:                             user_approved=False,
 478:                         )
 479:                     except Exception:
 480:                         pass
 481:                     continue
 482: 
 483:                 # Block C â€” exec-limit gate (PS#7 fix). Only bash +
 484:                 # python_exec count toward this limit. v4 verbatim
 485:                 # message at sagemaker_agent.py:9482-9489 â€” preserved
 486:                 # so the model can recover by switching to non-counted
 487:                 # tools.
 488:                 if call.name in {"bash", "python_exec"}:
 489:                     from runtime.config import CONFIG as _CFG
 490:                     cap = getattr(_CFG, "max_exec_calls_per_session", 200)
 491:                     if self._exec_call_count >= cap:
 492:                         tool_results.append({
 493:                             "type": "tool_result",
 494:                             "tool_use_id": call.id,
 495:                             "content": (
 496:                                 f"Blocked: bash + python_exec call limit "
 497:                                 f"reached ({cap}/session). "
 498:                                 "OTHER TOOLS STILL WORK: read_file, grep, "
 499:                                 "glob, edit_file, write_file, notebook_edit, "
 500:                                 "task, ask_user, view_image, web_fetch are "
 501:                                 "NOT counted by this limit."
 502:                             ),
 503:                             "is_error": True,
 504:                         })
 505:                         continue
 506: 
 507:                 # Block C â€” repetition detector. Same (tool_name,
 508:                 # args_hash) appearing 3+ times in the last 6 calls is
 509:                 # almost always a stuck loop. v4 sagemaker_agent.py:9156-9180
 510:                 # threshold=2 (block on 3rd duplicate).
 511:                 import hashlib as _hashlib
 512:                 import json as _json
 513:                 try:
 514:                     _args_hash = _hashlib.sha256(
 515:                         _json.dumps(call.input or {}, sort_keys=True, default=str).encode()
 516:                     ).hexdigest()[:12]
 517:                 except Exception:
 518:                     _args_hash = ""
 519:                 _key = (call.name, _args_hash)
 520:                 _recent = self._recent_tool_calls[-6:]
 521:                 if _recent.count(_key) >= 2:
 522:                     tool_results.append({
 523:                         "type": "tool_result",
 524:                         "tool_use_id": call.id,
 525:                         "content": (
 526:                             f"Blocked: same call to '{call.name}' with "
 527:                             f"identical arguments has been issued 3 times "
 528:                             "in a row. This is almost always a stuck loop. "
 529:                             "Try a different approach, different arguments, "
 530:                             "or use ask_user to clarify."
 531:                         ),
 532:                         "is_error": True,
 533:                     })
 534:                     continue
 535:                 # Track this call (rolling window of last 12).
 536:                 self._recent_tool_calls.append(_key)
 537:                 if len(self._recent_tool_calls) > 12:
 538:                     self._recent_tool_calls = self._recent_tool_calls[-12:]
 539: 
 540:                 # Block C â€” JSON-repair tool args before dispatch. If
 541:                 # Bedrock streamed back malformed JSON in tool_use.input,
 542:                 # try to recover gracefully instead of falling through
 543:                 # to a tool-side type error.
 544:                 _repaired_input = call.input
 545:                 if isinstance(call.input, str):
 546:                     # When tool_use.input arrives as a JSON string (some
 547:                     # Bedrock variants), parse + repair before dispatch.
 548:                     try:
 549:                         from security.json_repair import repair_tool_call_arguments
 550:                         _repaired_input = repair_tool_call_arguments(call.input)
 551:                     except Exception:
 552:                         _repaired_input = {}
 553: 
 554:                 # Block C+ â€” approval gate. When CONFIG.require_tool_approval
 555:                 # AND tool.requires_approval are BOTH True (and we're not
 556:                 # in mock_mode for tests), surface a PermissionDialog
 557:                 # and block until decided. always-allow decisions stick
 558:                 # on CONFIG._always_allowed[tool.name]. Mock detection
 559:                 # checks the BedrockClient instance (not CONFIG) because
 560:                 # tests construct their own client without flipping the
 561:                 # global CONFIG.mock_mode flag.
 562:                 from runtime.config import CONFIG as _CFG_AT
 563:                 _is_mock = bool(
 564:                     getattr(_CFG_AT, "mock_mode", False)
 565:                     or getattr(self.client, "mock_mode", False)
 566:                 )
 567:                 if (not _is_mock
 568:                         and getattr(_CFG_AT, "require_tool_approval", False)
 569:                         and getattr(tool, "requires_approval", False)):
 570:                     if not hasattr(_CFG_AT, "_always_allowed"):
 571:                         _CFG_AT._always_allowed = {}
 572:                     if not _CFG_AT._always_allowed.get(call.name):
 573:                         try:
 574:                             from ui.approval_dialog import PermissionDialog
 575:                             _model_reason = ""
 576:                             if isinstance(_repaired_input, dict):
 577:                                 _model_reason = str(_repaired_input.get("reason", ""))
 578:                             _dlg = PermissionDialog(
 579:                                 tool_name=call.name,
 580:                                 parameters=_repaired_input or {},
 581:                                 reason=_model_reason,
 582:                             )
 583:                             _result = _dlg.prompt()
 584:                             if not _result.approved:
 585:                                 tool_results.append({
 586:                                     "type": "tool_result",
 587:                                     "tool_use_id": call.id,
 588:                                     "content": (
 589:                                         f"User denied approval for "
 590:                                         f"`{call.name}`: {_result.reason}"
 591:                                     ),
 592:                                     "is_error": True,
 593:                                 })
 594:                                 continue
 595:                             # Approved â€” sticky if user clicked Always.
 596:                         except Exception as _approval_exc:
 597:                             logging.warning(
 598:                                 f"approval gate failed: {_approval_exc}; "
 599:                                 "defaulting to deny"
 600:                             )
 601:                             tool_results.append({
 602:                                 "type": "tool_result",
 603:                                 "tool_use_id": call.id,
 604:                                 "content": (
 605:                                     f"Approval gate error for `{call.name}`; "
 606:                                     f"defaulting to deny."
 607:                                 ),
 608:                                 "is_error": True,
 609:                             })
 610:                             continue
 611: 
 612:                 # Execute. Tool implementations may raise; we trap and surface
 613:                 # the error to the model rather than the human user.
 614:                 # `parent_engine` is passed for Phase 9 task tool â€” the sub-agent
 615:                 # spawn needs the parent's IterationBudget + BedrockClient (ADR-015).
 616:                 try:
 617:                     if call.name in {"bash", "python_exec"}:
 618:                         self._exec_call_count += 1
 619:                     raw = tool.execute(_repaired_input, context={
 620:                         "active_tools": tools,
 621:                         "plan_mode": plan_mode,
 622:                         "parent_engine": self,
 623:                         "parent_depth": getattr(self, "_subagent_depth", 0),
 624:                     })
 625:                     text = _coerce_tool_result_to_text(raw)
 626:                     text = _truncate_tool_result(text, tool.max_result_size_chars)
 627:                     tool_results.append({
 628:                         "type": "tool_result",
 629:                         "tool_use_id": call.id,
 630:                         "content": text,
 631:                     })
 632:                     # Block B (PORT_LOG #043): audit-log every tool dispatch
 633:                     # so /diffs / /regression / forensics have a tamper-hashed
 634:                     # trail. Best-effort.
 635:                     try:
 636:                         from runtime.audit import AUDIT as _AUDIT
 637:                         _AUDIT.log(
 638:                             session_id=self.session_id,
 639:                             action="tool_dispatch",
 640:                             tool_name=call.name,
 641:                             parameters=call.input or {},
 642:                             result_summary=text[:500] if isinstance(text, str) else "",
 643:                             user_approved=True,
 644:                         )
 645:                     except Exception:
 646:                         pass
 647:                     # Phase 7 wiring: extract discovered names from tool_search
 648:                     # results and add to the next turn's tools= payload.
 649:                     if call.name == "tool_search":
 650:                         discovered = tool_search_discovered_names(text)
 651:                         if discovered:
 652:                             self._discovered_tool_names.update(discovered)
 653:                 except Exception as exc:  # noqa: BLE001 â€” surface to model
 654:                     logging.warning(
 655:                         "[query_engine] tool '%s' raised %s: %s",
 656:                         call.name, type(exc).__name__, exc,
 657:                     )
 658:                     tool_results.append({
 659:                         "type": "tool_result",
 660:                         "tool_use_id": call.id,
 661:                         "content": f"Error: {type(exc).__name__}: {exc}",
 662:                         "is_error": True,
 663:                     })
 664:                     # Audit the failed dispatch too so forensics can see what
 665:                     # was attempted (sanitized parameters; no result body).
 666:                     try:
 667:                         from runtime.audit import AUDIT as _AUDIT
 668:                         _AUDIT.log(
 669:                             session_id=self.session_id,
 670:                             action="tool_error",
 671:                             tool_name=call.name,
 672:                             parameters=call.input or {},
 673:                             result_summary=f"{type(exc).__name__}: {exc}",
 674:                             user_approved=False,
 675:                         )
 676:                     except Exception:
 677:                         pass
 678: 
 679:             # Append the tool_results as a user turn (Bedrock convention).
 680:             self.messages.append({"role": "user", "content": tool_results})
 681: 
 682:         else:  # for-loop fell through without break
 683:             stop_reason = "max_turns"
 684:             output_fn(f"[Max turns reached: {self.max_turns}]")
 685: 
 686:         return QueryResult(
 687:             text=last_text,
 688:             messages=list(self.messages),
 689:             stop_reason=stop_reason or "end_turn",
 690:             turns_used=turns_used,
 691:             budget_used=self.budget.used(),
 692:         )
 693: 
 694:     # ------------------------------------------------------------
 695:     # Internal: assemble assistant turn content from a Bedrock Response
 696:     # ------------------------------------------------------------
 697: 
 698:     @staticmethod
 699:     def _build_assistant_content(response: Any) -> List[Dict[str, Any]]:
 700:         """Construct a Bedrock-shaped assistant content list from a Response.
 701: 
 702:         Order: thinking blocks (if any) â†’ text â†’ tool_use. The thinking
 703:         block is preserved so the next turn's API call carries it back to
 704:         the model (Bedrock requires this for extended thinking continuity).
 705:         """
 706:         blocks: List[Dict[str, Any]] = []
 707:         thinking = getattr(response, "thinking", "") or ""
 708:         if thinking:
 709:             blocks.append({"type": "thinking", "thinking": thinking})
 710:         if response.text:
 711:             blocks.append({"type": "text", "text": response.text})
 712:         for call in response.tool_calls:
 713:             blocks.append({
 714:                 "type": "tool_use",
 715:                 "id": call.id,
 716:                 "name": call.name,
 717:                 "input": call.input,
 718:             })
 719:         return blocks
 720: 
 721:     # ------------------------------------------------------------
 722:     # Internal: deferred-tools system reminder injection
 723:     # ------------------------------------------------------------
 724: 
 725:     @staticmethod
 726:     def _inject_deferred_reminder(
 727:         messages: List[Dict[str, Any]],
 728:         deferred_names: List[str],
 729:     ) -> List[Dict[str, Any]]:
 730:         """Append a `<system-reminder>` block listing deferred tool names so
 731:         the model knows what's available via tool_search.
 732: 
 733:         The reminder is injected as a transient text block on the trailing
 734:         user turn â€” it does not mutate `self.messages`, so it does not leak
 735:         into subsequent turns once the model has loaded the schemas it needs.
 736:         """
 737:         if not deferred_names:
 738:             return messages
 739:         reminder = (
 740:             "<system-reminder>\n"
 741:             "The following deferred tools are available via tool_search. Their schemas "
 742:             "are NOT loaded â€” calling them directly will fail. Use tool_search with "
 743:             "query \"select:<name>[,<name>...]\" to load tool schemas before calling them:\n"
 744:             + "\n".join(sorted(deferred_names))
 745:             + "\n</system-reminder>"
 746:         )
 747:         # Transient append: copy the trailing user message and add the reminder
 748:         # as an extra text block. If the trailing turn is not user-role, we
 749:         # append a fresh user message â€” but this should never happen because
 750:         # the loop only invokes Bedrock right after a user turn or tool_results.
 751:         out = list(messages)
 752:         if not out or out[-1].get("role") != "user":
 753:             out.append({"role": "user", "content": [{"type": "text", "text": reminder}]})
 754:             return out
 755:         last = dict(out[-1])
 756:         content = last.get("content")
 757:         if isinstance(content, str):
 758:             last["content"] = [
 759:                 {"type": "text", "text": content},
 760:                 {"type": "text", "text": reminder},
 761:             ]
 762:         elif isinstance(content, list):
 763:             last["content"] = list(content) + [{"type": "text", "text": reminder}]
 764:         else:
 765:             last["content"] = [{"type": "text", "text": reminder}]
 766:         out[-1] = last
 767:         return out
 768: 
 769: 
 770: # ============================================================
 771: # Single-turn helper for unit tests
 772: # ============================================================
 773: 
 774: def run_one_turn(
 775:     client: Any,
 776:     messages: List[Dict[str, Any]],
 777:     system_prompt: str,
 778:     tools: List[Any],
 779:     max_tokens: int = 4096,
 780:     temperature: float = 0.0,
 781:     thinking_enabled: bool = False,
 782:     thinking_budget: int = 4096,
 783: ) -> Any:
 784:     """Run a single Bedrock invocation with Phase 7 deferral applied.
 785: 
 786:     Returns the raw `Response` object. Tests use this to assert wiring without
 787:     spinning up the full multi-turn loop.
 788:     """
 789:     from tools.registry import apply_tool_search_deferral
 790: 
 791:     visible_tools, _deferred = apply_tool_search_deferral(tools, enabled=True)
 792:     return client.chat(
 793:         messages=messages,
 794:         system=system_prompt,
 795:         tools=_build_tools_api_payload(visible_tools),
 796:         max_tokens=max_tokens,
 797:         temperature=temperature,
 798:         thinking_enabled=thinking_enabled,
 799:         thinking_budget=thinking_budget,
 800:     )

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/tools/task.py'" in D:\Github\sagemaker-coding-agent
 succeeded in 446ms:
"""Phase 9 task tool â€” sub-agent dispatch (Phase 9, ADR-015).

ADAPT port of:
- gg-claude-code-runnable/src/tools/AgentTool/AgentTool.tsx (1397 LOC) â€” only the
  tool-shape contract (description + schema + executor signature). Runnable's
  React/Ink UI lives in UI.tsx and is not ported (constraint=.ipynb).
- v4 `_run_task_tool` at sagemaker_agent.py:8350 â€” the executor logic.

PORT_LOG: #024.

Phase 9 surface â€” minimal so the v5 .ipynb shape doesn't drag the full
AGENT_TYPES + worktree complexity across the gate:
- subagent_type values: "general" only. Future phases add build/plan/explore/verify.
- No worktree isolation (build agent's git-worktree dance lands in Phase 11).
- No parallel dispatch (Runnable's parallel sub-agent dispatch is async-only).

The tool is marked `should_defer=True` because spawn is low-frequency:
most turns don't need a sub-agent, so the schema is loaded only when the
model calls tool_search after seeing the deferred-tool reminder.

The Phase 7 wiring contract (ADR-013/014) requires the executor to receive
the parent QueryEngine via `context["parent_engine"]` so the child can share
the parent's IterationBudget â€” see acceptance test
`test_subagent_shares_iteration_budget`.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .registry import build_tool, register


_DESCRIPTION = """Launch a sub-agent for a specific, scoped task.

Sub-agents run with a FRESH conversation but share the parent agent's iteration budget â€” they cannot collectively exceed the cost ceiling. Use a sub-agent when:
- The task is well-scoped and self-contained (e.g., "summarize this codebase", "find every TODO comment").
- You want to keep the parent's main context clean (the sub-agent's full transcript is not loaded into the parent â€” only the final answer is returned).
- You need read-only exploration without polluting the parent's file-read history.

Do NOT use a sub-agent when:
- The task is small enough to do directly in the current turn.
- The result must be incrementally visible to the user (sub-agent runs to completion before returning).
- You need persistent state across multiple top-level requests (sub-agents are one-shot).

Inputs:
- description: 1-line summary shown to the user.
- prompt: the actual task description for the sub-agent. Be specific.
- subagent_type: "general" (default; full tool access). Other types are reserved for future phases.

Returns the sub-agent's final answer as a string. If the sub-agent hits its iteration budget or max_turns, the partial work + reason is returned."""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "description": {
            "type": "string",
            "description": "1-line summary of what the sub-agent will do (for display only).",
        },
        "prompt": {
            "type": "string",
            "description": "Full task description sent to the sub-agent. Be specific â€” the sub-agent has no parent context unless you brief it.",
        },
        "subagent_type": {
            "type": "string",
            "description": "Agent type. 'general' (default) for full tool access. Other types reserved for future phases.",
        },
    },
    "required": ["prompt"],
}


def _task_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    """Spawn a sub-agent and return its final answer.

    Required context (Phase 9 contract):
      - context["parent_engine"]: the parent QueryEngine. Used to (a) share
        IterationBudget, (b) reuse the BedrockClient, (c) inherit on_stop_check.
        If absent, the executor returns an Error: the model can read.
      - context["parent_depth"] (optional, default 0): the parent's depth.
        Used to enforce the recursion-depth limit.
    """
    description = str(args.get("description", "")).strip()
    prompt = str(args.get("prompt", "")).strip()
    if not prompt:
        return "Error: prompt is required and must be a non-empty string"
    subagent_type = str(args.get("subagent_type", "general")).strip() or "general"

    # Codex Phase-09 finding (medium): Phase-9 supports `general` only.
    # Silently falling back to general for unknown types hides caller/model
    # errors and diverges from v4's explicit-unknown-type contract
    # (compact_v4/MAIN/agent/sagemaker_agent.py:8366). Reject unknowns so
    # the model can self-correct via tool_search before retrying.
    from subagent.spawn import _AGENT_TYPE_SUFFIXES
    if subagent_type not in _AGENT_TYPE_SUFFIXES:
        available = ", ".join(sorted(_AGENT_TYPE_SUFFIXES.keys()))
        return (
            f"Error: unknown subagent_type '{subagent_type}'. "
            f"Phase-9 supports: {available}. "
            "(build/plan/explore/verify types reserved for later phases.)"
        )

    if not isinstance(context, dict) or "parent_engine" not in context:
        return (
            "Error: task tool requires `context['parent_engine']` to spawn a "
            "sub-agent (Phase 9 contract). The query_engine should pass this "
            "via the tool dispatch context."
        )
    parent_engine = context["parent_engine"]
    parent_depth = int(context.get("parent_depth", 0))

    # Lazy-import to avoid circular import: subagent.spawn imports
    # core.query_engine which (via tools/__init__.py:bootstrap_built_ins)
    # imports this module.
    from subagent.spawn import spawn_subagent

    result = spawn_subagent(
        parent_engine=parent_engine,
        prompt=prompt,
        agent_type=subagent_type,
        parent_depth=parent_depth,
        plan_mode=bool(context.get("plan_mode", False)),
    )

    if result.error and result.stop_reason in ("depth_exceeded", "invalid_args"):
        return result.error
    if result.stop_reason in ("budget_exhausted", "max_turns", "context_overflow"):
        # Surface partial work + reason so the parent can react.
        return (
            f"[Sub-agent stopped: {result.stop_reason}]\n"
            f"{result.text or '(no partial output)'}"
        )
    return result.text or "(sub-agent returned no text)"


def _register():
    """Idempotent registration. Called by tools/__init__.py:bootstrap_built_ins."""
    from .registry import find_tool_by_name, all_registered, unregister
    if find_tool_by_name(all_registered(), "task") is not None:
        return  # already registered

    register(build_tool(
        name="task",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_task_executor,
        is_read_only=False,         # children may write â€” fail-closed default
        is_destructive=False,
        is_concurrency_safe=False,  # parallel sub-agents land later
        requires_approval=False,    # the *child* approval gates fire on its tool calls
        should_defer=True,          # low-frequency; deferred via Phase 7
        always_load=False,
        search_hint="sub-agent fork delegate spawn task launch background",
    ))

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/subagent/spawn.py'" in D:\Github\sagemaker-coding-agent
 succeeded in 427ms:
"""V5 subagent/spawn.py â€” fork-style sub-agent spawn (Phase 9, ADR-015).

ADAPT port of Runnable's `forkSubagent.ts` (210 LOC). v5 adaptation:
- Synchronous (no Promise / async generator chain). Constraint=.ipynb.
- Drops Runnable's experimental fork branch (FORK_SUBAGENT feature gate),
  cache-prefix-identical message replay, and `<task-notification>`
  background dispatch model â€” those need streaming/async to be useful.
- Drops Runnable's coordinator-mode mutual exclusion (v5 has no coordinator).
- v5's spawn ALWAYS shares the parent's IterationBudget instance â€” that is
  Hermes's PS Issue #2 contract and the Phase-9 acceptance criterion.
- Drops AGENT_TYPES configuration registry â€” Phase 9 supports `general` only;
  build/plan/explore/verify agent types are deferred (their large prompts
  are reviewable as data later).
- Includes depth-limit enforcement (v4 sagemaker_agent.py:8354 parity).

PORT_LOG: #021.

Acceptance criteria (V5_PLAN.md Â§Phase 9):
- Parent context unchanged after sub-agent run.
- Child shares IterationBudget instance.

Usage:
    parent = QueryEngine(client=..., budget=IterationBudget())
    text, child = spawn_subagent(parent, "summarize this codebase", "general")
    # parent.messages is unchanged; child.budget is parent.budget.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple

from .env import build_env_details
from .handoff import build_handoff_block


# Default cap on sub-agent depth. Matches v4 CONFIG.subagent_max_depth=2.
DEFAULT_MAX_DEPTH: int = 2

# Per-agent-type prompt suffix table. Phase 9 ships `general` only; richer
# types (build/plan/explore/verify) land in later phases as their prompts
# become part of the deferred-loading content review surface.
_AGENT_TYPE_SUFFIXES = {
    "general": (
        "You are a sub-agent working on a focused task. Always use ABSOLUTE "
        "file paths (cwd may reset between bash calls). In your final "
        "response, share relevant file paths and key findings. Be concise â€” "
        "the parent will read your full reply."
    ),
}


@dataclass
class SubagentResult:
    """Outcome of `spawn_subagent`. Returned alongside the child engine so
    callers can inspect message buffer / budget / stop reason / turns_used.

    `text`            â€” final assistant text (the sub-agent's answer).
    `stop_reason`     â€” same as QueryResult.stop_reason.
    `turns_used`      â€” turns the child consumed.
    `child_messages`  â€” the child's full conversation buffer (for audit).
    `error`           â€” short message when stop_reason indicates failure.
    `agent_type`      â€” what type was requested.
    `depth`           â€” depth the child ran at.
    """
    text: str = ""
    stop_reason: str = ""
    turns_used: int = 0
    child_messages: List[Any] = field(default_factory=list)
    error: Optional[str] = None
    agent_type: str = "general"
    depth: int = 1


def _new_child_engine(parent_engine: Any, max_turns: int, agent_type: str = "general") -> Any:
    """Construct a fresh QueryEngine that shares the parent's IterationBudget.

    Lazy-imports to avoid a circular load at module-import time
    (core.query_engine imports tools/registry which may import
    tools/task.py which imports this module).

    Block B: `agent_type` is forwarded as `agent_kind` so TOKENS.add()
    attributes the child's input/output/cost to the right per-agent
    bucket. The child also gets a fresh session_id so AUDIT.log entries
    can be filtered to a single sub-agent run.
    """
    from core.query_engine import QueryEngine
    return QueryEngine(
        client=parent_engine.client,
        max_turns=max_turns,
        budget=parent_engine.budget,            # SHARED â€” the Phase-9 contract
        on_stop_check=parent_engine.on_stop_check,
        agent_kind=agent_type,
    )


def _resolve_agent_suffix(agent_type: str) -> Optional[str]:
    """Look up the prompt suffix for a known agent type.

    Returns None for unknown types so the caller (spawn_subagent / task tool)
    can surface an explicit error instead of silently falling back. Phase-9
    Codex finding: silent fallback masks contract bugs.
    """
    return _AGENT_TYPE_SUFFIXES.get(agent_type)


def spawn_subagent(
    parent_engine: Any,
    prompt: str,
    agent_type: str = "general",
    parent_depth: int = 0,
    max_turns: int = 25,
    max_depth: int = DEFAULT_MAX_DEPTH,
    base_system_prompt: Optional[str] = None,
    workspace: Optional[str] = None,
    status_path: Optional[str] = None,
    todos_text: Optional[str] = None,
    recent_files: Optional[List[str]] = None,
    plan_mode: bool = False,
    output_fn: Callable[[str], None] = print,
) -> SubagentResult:
    """Spawn a sub-agent with the parent's shared IterationBudget.

    The child gets:
      - A FRESH message buffer (no parent conversation leakage).
      - The parent's BedrockClient, IterationBudget, on_stop_check (shared).
      - A system prompt = base_system_prompt + env_details + handoff_block
        + agent-type suffix, with the cache boundary preserved.

    Returns a `SubagentResult` with the child's final answer + audit info.

    Phase 9 contract (V5_PLAN.md Â§Phase 9):
      - Parent's `messages` buffer is NOT mutated.
      - Child's `budget is parent_engine.budget` (object identity).
      - Depth-limit enforcement: depth >= max_depth â†’ blocked with error
        result, no Bedrock call made.
    """
    child_depth = parent_depth + 1

    # Depth-limit gate (v4 sagemaker_agent.py:8354 parity).
    if child_depth > max_depth:
        return SubagentResult(
            text="",
            stop_reason="depth_exceeded",
            error=(
                f"Blocked: sub-agent depth limit reached "
                f"({child_depth} > max {max_depth})"
            ),
            agent_type=agent_type,
            depth=child_depth,
        )

    # Validate prompt â€” empty prompt is a programming error in the caller.
    p = (prompt or "").strip()
    if not p:
        return SubagentResult(
            text="",
            stop_reason="invalid_args",
            error="Error: prompt is required",
            agent_type=agent_type,
            depth=child_depth,
        )

    # Validate agent type. The task tool already gates on this at the
    # dispatch layer, but spawn_subagent is also called directly by Phase
    # 11 UX wiring, so guard here too. Codex Phase-09 finding: don't
    # silently fall back to `general`.
    suffix = _resolve_agent_suffix(agent_type)
    if suffix is None:
        available = ", ".join(sorted(_AGENT_TYPE_SUFFIXES.keys()))
        return SubagentResult(
            text="",
            stop_reason="invalid_args",
            error=(
                f"Error: unknown agent_type '{agent_type}'. "
                f"Phase-9 supports: {available}."
            ),
            agent_type=agent_type,
            depth=child_depth,
        )

    # Assemble the child's system prompt:
    #   <static> [+ env_details + handoff_block + agent_type_suffix in dynamic tail]
    # If base_system_prompt has the boundary marker, inject our extras after it.
    # Otherwise append at the end.
    from prompt import build_system_prompt, CACHE_BOUNDARY

    base = base_system_prompt or build_system_prompt(ctx={})
    env_details = build_env_details(
        agent_type=agent_type,
        depth=child_depth,
        workspace=workspace,
        max_depth=max_depth,
    )
    handoff = build_handoff_block(
        status_path=status_path,
        todos_text=todos_text,
        recent_files=recent_files,
    )

    dynamic_extras = [env_details, handoff, suffix]
    dynamic_extras = [x for x in dynamic_extras if x]

    if dynamic_extras:
        addendum = "\n\n" + "\n\n".join(dynamic_extras)
        if CACHE_BOUNDARY in base:
            # Append after the existing dynamic tail (preserve cached prefix).
            child_prompt = base + addendum
        else:
            # No boundary â€” append at the end with our own boundary so future
            # cache-block builders see the static/dynamic split.
            child_prompt = base + CACHE_BOUNDARY + addendum
    else:
        child_prompt = base

    # Construct child engine. The shared-budget invariant is enforced by
    # _new_child_engine â€” verified by test_subagent_shares_iteration_budget.
    child = _new_child_engine(parent_engine, max_turns=max_turns, agent_type=agent_type)

    # Codex Phase-09 finding (BLOCKER): thread the child's depth so that
    # IF the child itself dispatches `task`, the QueryEngine's tool-dispatch
    # context picks up the correct `parent_depth` via
    # `getattr(self, "_subagent_depth", 0)`. Without this line, nested
    # `task` chains all see parent_depth=0 and the recursion guard never
    # fires. Lock test: test_nested_subagent_recursion_blocked_at_max_depth.
    child._subagent_depth = child_depth

    # Snapshot the parent's full message buffer for a defense-in-depth
    # mutation check. Codex Phase-09 finding (medium): the prior version
    # checked only length, so an in-place mutation that preserves length
    # (e.g. modifying messages[i]["content"] of an existing entry) would
    # evade detection. We deep-copy so post-hoc comparison is structural.
    import copy
    parent_msgs_snapshot = copy.deepcopy(parent_engine.messages)

    # Resolve the child's tool pool. Phase 9 keeps it simple: the child
    # gets the full registry (subject to plan-mode if requested). Future
    # phases may filter by AGENT_TYPES["tools"].
    from tools import all_registered
    child_tools = all_registered()

    # Block B+ (PORT_LOG #053): save+clear FILE_CACHE main context
    # before the child runs so the child sees a fresh in-context set;
    # restore the parent's set after the child returns. Best-effort â€”
    # if FILE_CACHE singleton is unavailable, dispatch still proceeds.
    _file_cache_saved = None
    try:
        from runtime.file_cache import FILE_CACHE as _FC
        _file_cache_saved = _FC.save_and_clear_context()
    except Exception:
        pass

    try:
        # The child runs synchronously to completion or budget exhaustion.
        result = child.run(
            user_message=p,
            system_prompt=child_prompt,
            tools=child_tools,
            plan_mode=plan_mode,
            output_fn=output_fn,
        )
    finally:
        # Always restore parent's in-context set, even if child raised.
        if _file_cache_saved is not None:
            try:
                from runtime.file_cache import FILE_CACHE as _FC
                _FC.restore_context(_file_cache_saved)
            except Exception:
                pass

    # Defense-in-depth: confirm the parent buffer wasn't mutated. Structural
    # comparison via the deep snapshot â€” catches in-place edits that preserve
    # length as well as length-changing mutations.
    if parent_engine.messages != parent_msgs_snapshot:
        # This should never happen if the contract holds. Surface a clear
        # error rather than silently corrupt parent state.
        return SubagentResult(
            text=result.text,
            stop_reason="parent_context_mutated",
            error=(
                "Internal error: parent_engine.messages was mutated by "
                "sub-agent dispatch. Phase-9 contract violated."
            ),
            child_messages=result.messages,
            agent_type=agent_type,
            depth=child_depth,
        )

    return SubagentResult(
        text=result.text,
        stop_reason=result.stop_reason,
        turns_used=result.turns_used,
        child_messages=result.messages,
        error=result.error,
        agent_type=agent_type,
        depth=child_depth,
    )

web search: 
web search: 
codex
I’ve identified a likely contract gap around “diff dispatch,” so I’m checking mutating tool implementations to confirm whether diff HTML is generated anywhere before approval.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/tools/edit_file.py'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/tools/write_file.py'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/ui/diff_widget.py'" in D:\Github\sagemaker-coding-agent
 succeeded in 526ms:
"""Phase 4 edit_file tool â€” REUSE v4 executor + ADAPT Runnable prompt.

Per ADR-010:
- Executor body is a Phase-4 minimal port of v4 `tool_edit_file` at
  `compact_v4/MAIN/agent/sagemaker_agent.py:4729`. Keeps: must-read-first
  enforcement, exact-match enforcement, replace_all flag, stale-check
  (file modified externally since last read).
- Phase-5+8 deferred: SnapshotManager.save (snapshot-before-edit), auto-
  lint-Python, auto-commit-checkpoint, post-edit `git diff` summary.
- Description text is adapted from
  `gg-claude-code-runnable/src/tools/FileEditTool/prompt.ts`.

PORT_LOG: row #007.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from .registry import build_tool, register
from . import _path_validation as path_security
from . import _file_read_tracking as read_tracking


_DESCRIPTION = """Performs exact string replacements in files.

Usage:
- You MUST use read_file at least once in the conversation before editing. This tool will error if you attempt an edit without reading the file (prevents blind misplaced edits).
- When editing text from read_file output, ensure you preserve the exact indentation (tabs/spaces) as it appears AFTER the line number prefix. The line number prefix format is: line number + `|` + space. Everything after that is the actual file content to match. Never include any part of the line number prefix in old_string or new_string.
- ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
- The edit will FAIL if `old_string` is not unique in the file. Either provide a larger string with more surrounding context to make it unique, or use `replace_all=true` to change every instance of `old_string`.
- Use `replace_all=true` for replacing and renaming strings across the file. This parameter is useful for renaming a variable.
- Use the smallest old_string that's clearly unique â€” usually 2-4 adjacent lines is sufficient. Avoid including 10+ lines of context when less uniquely identifies the target.
- Approval prompt shows colored before/after diff inline + click-to-expand-full-file (per V5_PLAN.md Phase 4).
- Approval is required before the edit happens.

WHEN to use:
- Modifying specific sections of existing code (bug fixes, feature additions, refactoring)
- Renaming variables, functions, or strings across a file (with replace_all=true)
- Any targeted change to an existing file

WHEN NOT to use:
- Creating brand-new files â†’ use write_file
- Complete file rewrites â†’ use write_file
- Editing notebook cells â†’ use notebook_edit
- Never use bash sed / awk to edit files â€” use this dedicated tool instead"""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Absolute path to the file to edit.",
        },
        "old_string": {
            "type": "string",
            "description": "Exact text to replace. Must match EXACTLY including indentation.",
        },
        "new_string": {
            "type": "string",
            "description": "Replacement text.",
        },
        "replace_all": {
            "type": "boolean",
            "description": "If true, replace every occurrence. Default false (must be unique).",
        },
    },
    "required": ["file_path", "old_string", "new_string"],
}


def _edit_file_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    file_path = args.get("file_path")
    old_string = args.get("old_string")
    new_string = args.get("new_string")
    replace_all = bool(args.get("replace_all", False))

    if not isinstance(file_path, str) or not file_path:
        return "Error: file_path is required and must be a non-empty string"
    if not isinstance(old_string, str):
        return "Error: old_string is required and must be a string"
    if not isinstance(new_string, str):
        return "Error: new_string is required and must be a string"
    if old_string == new_string:
        return "Error: old_string and new_string are identical â€” nothing to change"

    # Block C C-6 (R1 #123) â€” UNC path skip on Windows (NTLM credential leak).
    try:
        from security.edit_file_safety import is_unc_path_windows
        if is_unc_path_windows(file_path):
            return (
                "Error: UNC paths (\\\\server\\share\\...) are not allowed on "
                "Windows because reading them leaks NTLM credentials. Copy "
                "the file locally first (e.g. via robocopy) and edit the copy."
            )
    except Exception:
        pass

    ok, msg = path_security.validate_path(file_path)
    if not ok:
        return f"Error: {msg}"

    abs_path = os.path.abspath(path_security.resolve_path(file_path))
    if not os.path.isfile(abs_path):
        return f"Error: File not found or not a regular file: {abs_path}"

    if not read_tracking.was_read(abs_path):
        return (
            "Error: Must read file before editing. Use read_file first to load the "
            "current state of the file, then retry the edit."
        )

    is_stale, stale_msg = read_tracking.is_stale(abs_path)
    if is_stale:
        # Block C C-8 (R1 #111) â€” Windows OneDrive / AV touch can bump
        # mtime without changing content. If the read tracker has a
        # cached snapshot AND the file content is byte-identical to
        # that snapshot, treat the staleness as a false positive.
        try:
            from security.edit_file_safety import is_staleness_false_positive
            cached = read_tracking.get_last_read_snapshot(abs_path) \
                if hasattr(read_tracking, "get_last_read_snapshot") else None
            if cached is not None:
                last_mtime = cached.get("mtime", 0.0)
                last_text = cached.get("content")
                if is_staleness_false_positive(abs_path, last_mtime, last_text):
                    is_stale = False  # tolerate the touch
        except Exception:
            pass
        if is_stale:
            return f"Error: {stale_msg}"

    # Block C C-5 (R1 #121) â€” detect UTF-16 / UTF-8-sig BOMs (Notepad-saved).
    _file_encoding = "utf-8"
    _eol = "\n"
    try:
        from security.edit_file_safety import (
            detect_utf16_bom,
            normalize_line_endings,
            normalize_quotes,
        )
        _bom_enc = detect_utf16_bom(abs_path)
        if _bom_enc:
            _file_encoding = _bom_enc
    except Exception:
        pass

    try:
        with open(abs_path, "r", encoding=_file_encoding, errors="replace") as f:
            content = f.read()
    except OSError as e:
        return f"Error: cannot read file: {e}"

    # Block C C-7 (R1 #122) â€” round-trip line endings: match in LF space,
    # restore on write. Block C C-3 (R1 #115) â€” fold curlyâ†’straight quotes
    # on BOTH file and search needle so smart-quote files match.
    _content_lf = content
    try:
        _content_lf, _eol = normalize_line_endings(content)
        _norm_content = normalize_quotes(_content_lf)
        _norm_old = normalize_quotes(old_string)
    except NameError:
        _norm_content = _content_lf
        _norm_old = old_string

    count = _norm_content.count(_norm_old)
    if count == 0:
        return "Error: old_string not found in file. Must be EXACT match (check indentation, line endings, exact characters)."
    if count > 1 and not replace_all:
        return (
            f"Error: old_string appears {count} times in the file. "
            f"Either provide a larger old_string with more context to make it unique, "
            f"or pass replace_all=true to change every occurrence."
        )

    # Apply replacement on the normalized (LF + straight-quote) content
    # so the match works for smart-quote / CRLF files; then restore the
    # original line endings before writing.
    # Block C C-4 (R1 #116) lock: if the original content uses curly
    # quotes (we detect by comparing the un-normalized vs normalized
    # version), re-wrap new_string in the same curly variant so the
    # file remains stylistically consistent post-edit.
    if "_norm_old" in locals():
        _norm_new = normalize_quotes(new_string)
        try:
            from security.edit_file_safety import preserve_quote_style
            _norm_new = preserve_quote_style(content, _norm_new)
        except Exception:
            pass
    else:
        _norm_new = new_string
    new_content = (
        _norm_content.replace(_norm_old, _norm_new)
        if replace_all
        else _norm_content.replace(_norm_old, _norm_new, 1)
    )
    if _eol != "\n":
        try:
            from security.edit_file_safety import restore_line_endings
            new_content = restore_line_endings(new_content, _eol)
        except Exception:
            pass

    # Block B (PORT_LOG #044): SnapshotManager.save snapshots the
    # current file before edit so /revert restores it. Best-effort â€”
    # snapshot failure must not block the edit.
    try:
        from runtime.snapshot import SNAPSHOTS
        SNAPSHOTS.save(abs_path)
    except Exception:
        pass

    # Write back in the same encoding we read with (preserves BOM).
    try:
        with open(abs_path, "w", encoding=_file_encoding) as f:
            f.write(new_content)
    except OSError as e:
        return f"Error: cannot write file: {e}"

    # Re-mark read so the next edit doesn't falsely fail the staleness check.
    read_tracking.mark_read(abs_path)

    # Compute change summary
    old_lines = old_string.count("\n") + 1
    new_lines = new_string.count("\n") + 1
    pos = content.find(old_string)
    line_no = content[:pos].count("\n") + 1 if pos >= 0 else 1
    suffix = f" ({count} replacements)" if (count > 1 and replace_all) else ""
    return (
        f"Edited {os.path.basename(abs_path)} (line {line_no})\n"
        f"  -{old_lines} lines / +{new_lines} lines{suffix}"
    )


def _register():
    """Idempotent registration of edit_file. See read_file.py:_register."""
    from .registry import find_tool_by_name, all_registered
    if find_tool_by_name(all_registered(), "edit_file") is not None:
        return find_tool_by_name(all_registered(), "edit_file")
    return register(build_tool(
        name="edit_file",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_edit_file_executor,
        is_read_only=False,
        is_destructive=True,            # Modifies file content
        is_concurrency_safe=False,      # Two edits to same file race
        requires_approval=True,         # ADR-010: approval prompt with diff
        search_hint="exact string replace in file",
    ))

 succeeded in 539ms:
"""Phase 4 write_file tool â€” REUSE v4 executor + ADAPT Runnable prompt.

Per ADR-010:
- Executor body is a Phase-4 minimal port of v4 `tool_write_file` at
  `compact_v4/MAIN/agent/sagemaker_agent.py:4632`. The Phase-4 minimal port
  keeps the security check, the read-before-overwrite enforcement, and
  basic file write. Phase-5+8 additions (secrets scan, snapshot, auto-lint,
  auto-commit) are noted inline and added at the appropriate phase.
- Description text is adapted from
  `gg-claude-code-runnable/src/tools/FileWriteTool/prompt.ts`.

PORT_LOG: row #006.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from .registry import build_tool, register
from . import _path_validation as path_security
from . import _file_read_tracking as read_tracking


_DESCRIPTION = """Writes content to a file, creating it if it doesn't exist or overwriting if it does.

Usage:
- This tool will OVERWRITE the existing file if there is one at the provided path.
- If this is an existing file, you MUST use read_file first to read its contents. This tool will error if you haven't read the file (prevents blind clobber).
- Prefer edit_file for modifying existing files â€” it only sends the diff portion, saving tokens. Use write_file only for creating new files or complete rewrites.
- Supports `mode='write'` (default â€” overwrites entire file) and `mode='append'` (adds to end). Append mode does NOT require a prior read.
- The file_path parameter must be an absolute path, not a relative path. Parent directories are created automatically.
- Approval prompt shows colored before/after diff (green = added, red = removed) inline + click-to-expand-full-file (per V5_PLAN.md Phase 4).
- Approval is required before the write happens.

WHEN to use:
- Creating a brand-new file that doesn't exist yet
- Complete rewrite of an existing file (after reading it first)
- Appending content to the end of a file (mode='append')

WHEN NOT to use:
- Modifying specific sections of an existing file â†’ use edit_file (cheaper, safer, fewer tokens)
- Editing notebook cells â†’ use notebook_edit
- Never use bash echo / heredoc / cat to write files â€” use this dedicated tool instead"""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Absolute path to the file to write.",
        },
        "content": {
            "type": "string",
            "description": "Content to write.",
        },
        "mode": {
            "type": "string",
            "enum": ["write", "append"],
            "description": "'write' (default) overwrites the entire file. 'append' adds to the end without requiring a prior read.",
        },
    },
    "required": ["file_path", "content"],
}


def _write_file_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    file_path = args.get("file_path")
    content = args.get("content")
    mode = args.get("mode", "write")

    if not isinstance(file_path, str) or not file_path:
        return "Error: file_path is required and must be a non-empty string"
    if not isinstance(content, str):
        return "Error: content is required and must be a string"
    if mode not in ("write", "append"):
        return f"Error: mode must be 'write' or 'append'; got {mode!r}"

    ok, msg = path_security.validate_path(file_path)
    if not ok:
        return f"Error: {msg}"

    abs_path = os.path.abspath(path_security.resolve_path(file_path))

    # v4 parity: in 'write' mode, refuse to clobber an existing file unless
    # the agent has read it first. Phase-8 query_engine populates
    # `_file_read_tracking` whenever read_file is invoked.
    if mode == "write" and os.path.exists(abs_path) and not read_tracking.was_read(abs_path):
        return (
            "Error: Must read file before overwriting. Use read_file first, "
            "or use mode='append' to add content without prior read."
        )

    # Phase-5 deferred: secrets scan (v4 SECURITY.scan_secrets) â€” landing in
    # Phase 5 with the full security/ port. Phase 4 ships without it because
    # the secrets scanner depends on the Phase-5 SecurityManager state.
    # Phase-5 ADR will reconcile this gap.

    try:
        # Block B (PORT_LOG #044): SnapshotManager.save snapshots the
        # current file before overwrite/append so /revert restores it.
        # No-op on first write (file doesn't exist yet) and in stealth
        # mode (CONFIG.disable_local_traces=True).
        try:
            from runtime.snapshot import SNAPSHOTS
            SNAPSHOTS.save(abs_path)
        except Exception:
            # Snapshot is best-effort â€” never block the write on a
            # snapshot failure (insufficient disk space, perms, etc.).
            pass
        dir_path = os.path.dirname(abs_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        open_mode = "a" if mode == "append" else "w"
        with open(abs_path, open_mode, encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        return f"Error writing file: {e}"

    # After write, the file's "current state" is what we just wrote, so mark
    # it as read so a subsequent edit_file doesn't trip the read-first check.
    read_tracking.mark_read(abs_path)

    return f"Written {len(content):,} chars to {abs_path}"


def _register():
    """Idempotent registration of write_file. See read_file.py:_register."""
    from .registry import find_tool_by_name, all_registered
    if find_tool_by_name(all_registered(), "write_file") is not None:
        return find_tool_by_name(all_registered(), "write_file")
    return register(build_tool(
        name="write_file",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_write_file_executor,
        is_read_only=False,
        is_destructive=True,            # Overwrites existing files
        is_concurrency_safe=False,      # Two writes to same path race
        requires_approval=True,         # ADR-010: approval prompt with diff
        search_hint="write file create or overwrite",
    ))

 succeeded in 555ms:
"""V5 ui/diff_widget.py â€” colored inline + expandable diff for the approval prompt.

Per ADR-010, V5_PLAN.md Phase 4 acceptance criterion:
    edit_file, write_file, AND notebook_edit approval prompts each show
    colored before/after diff inline (red removed, green added, gray
    context) with file path header + line numbers + Â±3 lines context +
    click-to-expand-full-file BEFORE the user clicks Approve.

Adopted from Runnable's `gg-claude-code-runnable/src/tools/FileEditTool/UI.tsx`
React/Ink diff component (PORT_LOG row #009). v5 emits HTML strings instead
of Ink JSX (constraint = .ipynb). Phase 11 wires the HTML into an
ipywidgets `HTML` widget inside the approval prompt.

Phase 4 deliverable: HTML emission + tests. Phase 11 wires into UX.

The widget exposes two functions:
  - `render_inline_diff(file_path, before_text, after_text, context=3)`
    â†’ returns HTML string with the colored diff visible immediately.
  - `render_expandable_diff(file_path, before_text, after_text)`
    â†’ returns HTML wrapping inline diff in `<details>` so the full-file
       view is collapsible. Used in approval prompts.

Both use stdlib `difflib.unified_diff` for the diff content. No new
dependencies.
"""
from __future__ import annotations

import difflib
import html
import os
from typing import List


# ============================================================
# Color palette (matches Runnable's UI.tsx ANSI conventions adapted to web)
# ============================================================
# Inline-styles used so the HTML renders correctly inside a Jupyter notebook
# cell output where stylesheet inheritance is unreliable. Colors picked for
# readability on both light and dark notebook themes.
_COLOR_ADDED_BG = "#e6ffec"      # very light green
_COLOR_ADDED_FG = "#1a7f37"      # dark green
_COLOR_REMOVED_BG = "#ffebe9"    # very light red
_COLOR_REMOVED_FG = "#cf222e"    # dark red
_COLOR_CONTEXT_BG = "#f6f8fa"    # very light gray
_COLOR_CONTEXT_FG = "#57606a"    # mid gray
_COLOR_HUNK_BG = "#ddf4ff"       # light blue (hunk header)
_COLOR_HUNK_FG = "#0969da"       # GitHub blue


# ============================================================
# Public renderers
# ============================================================

def render_inline_diff(
    file_path: str,
    before_text: str,
    after_text: str,
    context: int = 3,
) -> str:
    """Render an inline colored diff as HTML.

    Args:
        file_path: file being edited (shown in header).
        before_text: original full-file content.
        after_text: post-edit full-file content.
        context: lines of context shown around each change. Default 3.

    Returns:
        An HTML fragment (no `<html>`/`<body>` wrapper) suitable for
        ipywidgets.HTML or `display(HTML(...))`. Includes its own
        inline styles, no external CSS needed.

    Note: empty diff (before == after) returns a header + "No changes"
    note rather than an empty string, so the approval prompt always shows
    something meaningful.
    """
    before_lines = before_text.splitlines()
    after_lines = after_text.splitlines()

    diff_lines = list(difflib.unified_diff(
        before_lines, after_lines,
        fromfile=f"a/{os.path.basename(file_path)}",
        tofile=f"b/{os.path.basename(file_path)}",
        n=context,
        lineterm="",
    ))

    if not diff_lines:
        # Codex Phase-04 review finding 3: `splitlines()` strips trailing
        # newlines so a file change that ONLY toggles the EOF newline
        # would silently render as "No changes". Surface it explicitly.
        before_eof_nl = before_text.endswith("\n")
        after_eof_nl = after_text.endswith("\n")
        if before_eof_nl != after_eof_nl:
            change = (
                "added trailing newline at EOF" if after_eof_nl
                else "removed trailing newline at EOF"
            )
            return _wrap(
                _header(file_path)
                + _row_note(f"No content changes â€” only the final newline differs ({change}).")
            )
        return _wrap(_header(file_path) + _row_note("No changes â€” file content is identical."))

    return _wrap(_header(file_path) + _render_unified(diff_lines))


def render_expandable_diff(
    file_path: str,
    before_text: str,
    after_text: str,
    context: int = 3,
) -> str:
    """Render the inline diff PLUS a click-to-expand `<details>` block
    containing the full-file view (no truncation).

    Used in the approval prompt so the user sees the focused diff
    immediately and can drill into the whole file if uncertain.
    """
    inline = render_inline_diff(file_path, before_text, after_text, context=context)

    full_diff_lines = list(difflib.unified_diff(
        before_text.splitlines(), after_text.splitlines(),
        fromfile=f"a/{os.path.basename(file_path)}",
        tofile=f"b/{os.path.basename(file_path)}",
        n=10_000,  # effectively whole-file context
        lineterm="",
    ))
    full = (
        '<details style="margin-top:6px;">'
        '<summary style="cursor:pointer;font-size:0.9em;color:#57606a;">'
        'Show full-file diff (click to expand)'
        '</summary>'
        + _wrap(_render_unified(full_diff_lines) if full_diff_lines else _row_note("No changes."))
        + '</details>'
    )
    return inline + full


def render_new_file_diff(file_path: str, content: str) -> str:
    """Specialised renderer for write_file when the file does not yet exist.
    All lines are shown as additions."""
    if not content:
        return _wrap(_header(file_path) + _row_note("(empty file will be created)"))
    rows = []
    for i, ln in enumerate(content.splitlines(), 1):
        rows.append(_row_added(i, ln))
    return _wrap(_header(file_path, badge="NEW FILE") + "".join(rows))


# ============================================================
# Internal helpers
# ============================================================

def _wrap(body: str) -> str:
    """Wrap body in an outer `<div>` with the v5 diff styling."""
    return (
        '<div style="font-family:ui-monospace,SFMono-Regular,Consolas,monospace;'
        'font-size:0.85em;line-height:1.45;border:1px solid #d0d7de;'
        'border-radius:6px;overflow:hidden;margin:4px 0;">'
        + body
        + '</div>'
    )


def _header(file_path: str, badge: str = "") -> str:
    safe = html.escape(file_path)
    badge_html = ""
    if badge:
        badge_html = (
            f'<span style="margin-left:8px;padding:1px 6px;border-radius:3px;'
            f'background:{_COLOR_HUNK_BG};color:{_COLOR_HUNK_FG};'
            f'font-size:0.85em;font-weight:600;">{html.escape(badge)}</span>'
        )
    return (
        f'<div style="padding:6px 10px;background:#f6f8fa;'
        f'border-bottom:1px solid #d0d7de;font-weight:600;color:#1f2328;">'
        f'{safe}{badge_html}</div>'
    )


def _row_note(text: str) -> str:
    return (
        f'<div style="padding:6px 10px;color:{_COLOR_CONTEXT_FG};'
        f'font-style:italic;">{html.escape(text)}</div>'
    )


def _row_added(line_no: int | str, text: str) -> str:
    return _row("+", line_no, text, _COLOR_ADDED_BG, _COLOR_ADDED_FG)


def _row_removed(line_no: int | str, text: str) -> str:
    return _row("-", line_no, text, _COLOR_REMOVED_BG, _COLOR_REMOVED_FG)


def _row_context(line_no: int | str, text: str) -> str:
    return _row(" ", line_no, text, _COLOR_CONTEXT_BG, _COLOR_CONTEXT_FG)


def _row_hunk(text: str) -> str:
    safe = html.escape(text)
    return (
        f'<div style="padding:2px 10px;background:{_COLOR_HUNK_BG};'
        f'color:{_COLOR_HUNK_FG};font-weight:600;">{safe}</div>'
    )


def _row(marker: str, line_no: int | str, text: str, bg: str, fg: str) -> str:
    safe_text = html.escape(text)
    safe_marker = html.escape(marker)
    return (
        f'<div style="display:flex;background:{bg};color:{fg};'
        f'padding:1px 0;">'
        f'<span style="display:inline-block;width:46px;text-align:right;'
        f'padding-right:8px;color:{_COLOR_CONTEXT_FG};opacity:0.85;'
        f'border-right:1px solid #eaeef2;flex-shrink:0;">{line_no}</span>'
        f'<span style="display:inline-block;width:18px;text-align:center;'
        f'flex-shrink:0;">{safe_marker}</span>'
        f'<span style="white-space:pre;">{safe_text}</span>'
        f'</div>'
    )


def _render_unified(diff_lines: List[str]) -> str:
    """Translate `difflib.unified_diff` output into colored HTML rows.

    `unified_diff` emits:
      - `--- a/path` and `+++ b/path` headers (skipped â€” we have our own header)
      - `@@ -L,N +L,N @@` hunk markers
      - `+line` / `-line` / ` line` content rows

    We track the running line numbers in the BEFORE and AFTER files so each
    row gets the correct line number annotation.
    """
    out: List[str] = []
    before_no = 0
    after_no = 0

    for raw in diff_lines:
        if raw.startswith("---") or raw.startswith("+++"):
            continue  # skip file-name headers; we render our own
        if raw.startswith("@@"):
            # Parse hunk header, e.g. "@@ -10,5 +10,7 @@"
            try:
                # Format: "@@ -<oldStart>,<oldCount> +<newStart>,<newCount> @@"
                inner = raw.strip().strip("@").strip()
                parts = inner.split()
                old_part = parts[0]  # "-10,5"
                new_part = parts[1]  # "+10,7"
                before_no = int(old_part.lstrip("-").split(",")[0])
                after_no = int(new_part.lstrip("+").split(",")[0])
            except (ValueError, IndexError):
                # Defensive: malformed hunk header â€” render verbatim and continue
                pass
            out.append(_row_hunk(raw))
            continue

        if raw.startswith("+"):
            out.append(_row_added(after_no, raw[1:]))
            after_no += 1
        elif raw.startswith("-"):
            out.append(_row_removed(before_no, raw[1:]))
            before_no += 1
        else:
            # context line (begins with " " or is empty after leading space)
            text = raw[1:] if raw.startswith(" ") else raw
            # Choose `before_no` to display because the line exists in both;
            # display "L/L" only when before_no != after_no.
            label = (
                str(before_no) if before_no == after_no
                else f"{before_no}/{after_no}"
            )
            out.append(_row_context(label, text))
            before_no += 1
            after_no += 1

    return "".join(out)

web search: 
web search: ipywidgets HTML widget sanitization script tags
codex
I’ve confirmed no dispatch path currently passes `diff_html` into `PermissionDialog`; I’ll run the Block C+ integration file to confirm the current tests still pass despite that gap.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'pytest -q compact_v5/MAIN/agent/tests/integration/test_block_c_plus.py' in D:\Github\sagemaker-coding-agent
2026-05-03T02:56:59.570667Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.5 seconds
Output:
pytest : The term 'pytest' is not recognized as the name of a cmdlet, function, script file, or operable program. 
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:2 char:1
+ pytest -q compact_v5/MAIN/agent/tests/integration/test_block_c_plus.p ...
+ ~~~~~~
    + CategoryInfo          : ObjectNotFound: (pytest:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

 exited 1 in 484ms:
pytest : The term 'pytest' is not recognized as the name of a cmdlet, function, script file, or operable program. 
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:2 char:1
+ pytest -q compact_v5/MAIN/agent/tests/integration/test_block_c_plus.p ...
+ ~~~~~~
    + CategoryInfo          : ObjectNotFound: (pytest:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

web search: 
web search: 
codex
1. **`diff dispatch` is not actually wired before approval (High).**  
`QueryEngine` creates `PermissionDialog` without `diff_html` and never calls `ui.diff_widget`, so mutating tools are approved without the promised inline diff.  
- [query_engine.py:578](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:578)  
- [approval_dialog.py:52](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\ui\approval_dialog.py:52)  
- No `diff_widget` usage in dispatch path.

2. **60s watchdog contract is broken on Windows `select` fallback (High).**  
If `select.select()` is unsupported, code falls back to blocking `readline()` with no timeout, which can hang indefinitely in TTY mode.  
- [approval_dialog.py:249](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\ui\approval_dialog.py:249)

3. **Test coverage claims are overstated; several tests bypass real paths (Medium).**  
Multiple “integration” tests use `_override_decision`, which short-circuits before widget/text fallback and before QueryEngine approval dispatch behavior.  
- [test_block_c_plus.py:37](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\integration\test_block_c_plus.py:37)  
- [test_block_c_plus.py:187](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\integration\test_block_c_plus.py:187)  
- [approval_dialog.py:83](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\ui\approval_dialog.py:83)

**Axis A (errors/regression/security):** `CHANGES_REQUESTED`  
- `CONFIG._always_allowed` race and RateLimiter TOCTOU are acceptable only under current non-concurrent `run()` contract ([query_engine.py:36](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:36)).  
- Non-TTY default-deny is correctly fail-closed ([approval_dialog.py:220](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\ui\approval_dialog.py:220)).  
- But the two High issues above block acceptance quality.

**Axis B (v5 fit / ADR-010 + Block-C remap):** `DRIFTED`  
- C-11/C-12/C-13/C-14 warning surfacing is present.  
- Phase-4 ADR-010 “diff-before-approve” commitment is not fulfilled in dispatch wiring.

**Axis C (TEST_DESIGN Block C+ 7 + remap + undeclared pattern):**  
- Declared items are only partially proven.  
- `UNDECLARED_PATTERN`: tests labeled as approval/fallback integration rely on `_override_decision` short-circuit and do not validate real UI/text watchdog behavior.

**FINAL:** `REJECT`

Couldn’t run pytest locally because `pytest` is not installed in this shell environment.
2026-05-03T02:57:35.774301Z ERROR codex_core::session: failed to record rollout items: thread 019debc2-e747-7a53-be10-0911d65c9105 not found
tokens used
95,130
1. **`diff dispatch` is not actually wired before approval (High).**  
`QueryEngine` creates `PermissionDialog` without `diff_html` and never calls `ui.diff_widget`, so mutating tools are approved without the promised inline diff.  
- [query_engine.py:578](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:578)  
- [approval_dialog.py:52](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\ui\approval_dialog.py:52)  
- No `diff_widget` usage in dispatch path.

2. **60s watchdog contract is broken on Windows `select` fallback (High).**  
If `select.select()` is unsupported, code falls back to blocking `readline()` with no timeout, which can hang indefinitely in TTY mode.  
- [approval_dialog.py:249](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\ui\approval_dialog.py:249)

3. **Test coverage claims are overstated; several tests bypass real paths (Medium).**  
Multiple “integration” tests use `_override_decision`, which short-circuits before widget/text fallback and before QueryEngine approval dispatch behavior.  
- [test_block_c_plus.py:37](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\integration\test_block_c_plus.py:37)  
- [test_block_c_plus.py:187](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\tests\integration\test_block_c_plus.py:187)  
- [approval_dialog.py:83](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\ui\approval_dialog.py:83)

**Axis A (errors/regression/security):** `CHANGES_REQUESTED`  
- `CONFIG._always_allowed` race and RateLimiter TOCTOU are acceptable only under current non-concurrent `run()` contract ([query_engine.py:36](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\core\query_engine.py:36)).  
- Non-TTY default-deny is correctly fail-closed ([approval_dialog.py:220](D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent\ui\approval_dialog.py:220)).  
- But the two High issues above block acceptance quality.

**Axis B (v5 fit / ADR-010 + Block-C remap):** `DRIFTED`  
- C-11/C-12/C-13/C-14 warning surfacing is present.  
- Phase-4 ADR-010 “diff-before-approve” commitment is not fulfilled in dispatch wiring.

**Axis C (TEST_DESIGN Block C+ 7 + remap + undeclared pattern):**  
- Declared items are only partially proven.  
- `UNDECLARED_PATTERN`: tests labeled as approval/fallback integration rely on `_override_decision` short-circuit and do not validate real UI/text watchdog behavior.

**FINAL:** `REJECT`

Couldn’t run pytest locally because `pytest` is not installed in this shell environment.
