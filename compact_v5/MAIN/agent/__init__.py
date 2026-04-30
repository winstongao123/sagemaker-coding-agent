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

from typing import Any, Callable, Iterable, List, Optional

from core import IterationBudget, QueryEngine
from core.query_engine import QueryResult


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
        from prompt import build_system_prompt
        from tools import all_registered

        system_prompt = self._system_prompt or build_system_prompt(ctx={})
        active_tools = list(tools) if tools is not None else all_registered()

        self._stop_requested = False  # reset between runs
        result = self._engine.run(
            user_message=message,
            system_prompt=system_prompt,
            tools=active_tools,
            plan_mode=self._plan_mode,
            output_fn=output_fn,
            thinking_enabled=self._thinking_enabled,
            thinking_budget=self._thinking_budget,
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
