"""V5 agent.py — public Agent class (Phase 11, ADR-017).

Thin wrapper that composes the Phase 1-10 surfaces:
  - `runtime.bedrock_client.BedrockClient` (Phase 1)
  - `core.budget.IterationBudget` (Phase 8)
  - `core.query_engine.QueryEngine` (Phase 8)
  - optional `skills.manager.SkillManager` (Phase 10)

Public methods:
  - `run(message)` — execute a single user turn, return a `QueryResult`.
  - `stop()` — request the next turn to halt cleanly.
  - `clear()` — reset conversation buffer (does NOT reset budget by default;
                callers can pass `reset_budget=True` to also reset the budget).

This is the surface chat.ipynb (Phase 11) drives. It does NOT re-implement
agent logic — every behavior lives in its own module (Phase 8-10).

PORT_LOG: #031.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional

from core import IterationBudget, QueryEngine
from core.query_engine import QueryResult


# ============================================================
# Block B+ helper — load AGENT_STATUS.md if present
# ============================================================

def _load_agent_status_text() -> Optional[str]:
    """Return the contents of `<workspace>/AGENT_STATUS.md`, or None.

    Honors CONFIG.enable_status_doc + CONFIG.status_doc + CONFIG.workspace.
    Returns None silently when the file is missing or disabled — the
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
        text = text[:8000] + "\n\n…[truncated; AGENT_STATUS.md exceeds 8 KB]"
    return text


def _load_agent_memory_text() -> Optional[str]:
    """Return the contents of `<workspace>/memory.md`, or None."""
    import os
    from runtime.config import CONFIG
    memory_path = os.path.join(CONFIG.workspace, "memory.md")
    if not os.path.isfile(memory_path):
        return None
    try:
        with open(memory_path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    text = text.strip()
    if not text:
        return None
    if len(text) > 8000:
        text = text[:8000] + "\n\n...[truncated; memory.md exceeds 8 KB]"
    return text


def _load_agent_state_context_blocks() -> List[str]:
    """Load fresh durable status/memory context for a top-level turn."""
    blocks: List[str] = []
    status_text = _load_agent_status_text()
    if status_text:
        blocks.append("## Handoff: AGENT_STATUS\n\n" + status_text)
    memory_text = _load_agent_memory_text()
    if memory_text:
        blocks.append("## Persistent Memory: memory.md\n\n" + memory_text)
    return blocks


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
        auto_compact_enabled: bool = True,
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
            auto_compact_enabled: when False, disables pre-call cold-cache
                microcompact and post-turn auto-compact. Manual compaction
                remains available from the notebook UI.
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
        self._auto_compact_enabled = bool(auto_compact_enabled)
        self._thinking_enabled = bool(thinking_enabled)
        self._thinking_budget = int(thinking_budget)
        self._ui_subagent_preferences: Dict[str, Any] = {}
        # Historical B+ state retained for compatibility with tests that
        # inspect the attribute; SOFTWARE-STATE refreshes context per run.
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

        state_blocks: List[str] = []
        if self._system_prompt is None:
            try:
                state_blocks = _load_agent_state_context_blocks()
                self._agent_status_text = (
                    state_blocks[0].split("\n\n", 1)[1]
                    if state_blocks and state_blocks[0].startswith("## Handoff")
                    else None
                )
            except Exception:
                state_blocks = []
                self._agent_status_text = None
            self._agent_status_loaded = True

        from runtime.config import CONFIG as _CFG_PROMPT
        system_prompt = self._system_prompt or build_system_prompt(
            ctx={"workspace": getattr(_CFG_PROMPT, "workspace", None)}
        )
        if state_blocks:
            state_text = "\n\n".join(state_blocks)
            # Append to the dynamic tail (after CACHE_BOUNDARY) so the
            # cache-aware prefix replay (Block G2 territory) still works.
            if CACHE_BOUNDARY in system_prompt:
                system_prompt = system_prompt + "\n\n" + state_text
            else:
                system_prompt = system_prompt + CACHE_BOUNDARY + "\n\n" + state_text
        if self._ui_subagent_preferences.get("enabled"):
            prefs = self._ui_subagent_preferences
            preference_block = (
                "## Notebook UI Sub-Agent Preferences\n\n"
                "The operator enabled the Sub-Agents panel in the notebook UI. "
                "Use these as coordination preferences, not as permission to spawn "
                "unnecessary workers. Only call the task tool when it materially "
                "helps the current user request.\n\n"
                f"- explorer: {prefs.get('explorer', 'explorer')}\n"
                f"- worker: {prefs.get('worker', 'worker')}\n"
                f"- reviewer: {prefs.get('reviewer', 'reviewer')}"
            )
            if CACHE_BOUNDARY in system_prompt:
                system_prompt = system_prompt + "\n\n" + preference_block
            else:
                system_prompt = system_prompt + CACHE_BOUNDARY + "\n\n" + preference_block
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
        status_memory: Dict[str, Any] = {}
        try:
            from runtime.state import STATE
            from tools.todo import get_current_todos

            status_memory = STATE.capture_status_memory()
            STATE.append_journal(
                "turn_start",
                {
                    "message_chars": len(message or ""),
                    "todos": len(get_current_todos(load_disk=True)),
                    "status_sha256": status_memory.get("status", {}).get("sha256", ""),
                    "memory_sha256": status_memory.get("memory", {}).get("sha256", ""),
                },
            )
        except Exception:
            pass
        result = self._engine.run(
            user_message=message,
            system_prompt=system_prompt,
            tools=active_tools,
            plan_mode=self._plan_mode,
            auto_compact_enabled=self._auto_compact_enabled,
            output_fn=output_fn,
            thinking_enabled=self._thinking_enabled,
            thinking_budget=self._thinking_budget,
            max_tokens=_max_tokens,
            temperature=_temperature,
            prompt_cache_now=bool(state_blocks),
        )
        try:
            from runtime.state import STATE
            from runtime.tokens import TOKENS
            from tools.todo import get_current_todos

            STATE.save_turn_recovery(
                messages=result.messages,
                todos=get_current_todos(load_disk=True),
                token_stats=TOKENS.get_stats(),
                status_memory=status_memory or STATE.capture_status_memory(),
                result={
                    "stop_reason": result.stop_reason,
                    "turns_used": result.turns_used,
                    "text_chars": len(result.text or ""),
                },
            )
            STATE.append_journal(
                "turn_finish",
                {
                    "stop_reason": result.stop_reason,
                    "turns_used": result.turns_used,
                    "messages": len(result.messages),
                },
            )
        except Exception:
            pass
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

    def replace_messages(self, messages: Iterable[Dict[str, Any]]) -> None:
        """Replace the conversation buffer after a trusted runtime transform.

        The notebook Compact button uses this instead of reaching into
        `Agent._engine.messages` directly. Keeping the mutation behind the
        public wrapper protects the UI from future QueryEngine internals.
        """
        self._engine.messages = list(messages)

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
    def plan_mode(self) -> bool:
        return self._plan_mode

    @property
    def auto_compact_enabled(self) -> bool:
        return self._auto_compact_enabled

    @property
    def thinking_budget(self) -> int:
        return self._thinking_budget

    def set_plan_mode(self, enabled: bool) -> None:
        """Update plan-mode dispatch filtering for subsequent runs."""
        self._plan_mode = bool(enabled)

    def set_auto_compact(self, enabled: bool) -> None:
        """Enable/disable automatic compaction for subsequent runs."""
        self._auto_compact_enabled = bool(enabled)

    def set_ui_subagent_preferences(
        self,
        *,
        enabled: bool,
        explorer: str = "explorer",
        worker: str = "worker",
        reviewer: str = "reviewer",
    ) -> None:
        """Store notebook sub-agent preferences for the dynamic prompt tail."""
        self._ui_subagent_preferences = {
            "enabled": bool(enabled),
            "explorer": explorer or "explorer",
            "worker": worker or "worker",
            "reviewer": reviewer or "reviewer",
        }

    def set_thinking(self, enabled: bool, budget: Optional[int] = None) -> None:
        """Update thinking-mode settings (PS Issue #4 UI hook)."""
        self._thinking_enabled = bool(enabled)
        if budget is not None:
            self._thinking_budget = int(budget)
