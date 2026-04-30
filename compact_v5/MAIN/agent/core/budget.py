"""V5 core/budget.py — IterationBudget (Hermes pattern via v4).

Per ADR-014: verbatim port of v4's IterationBudget at
`compact_v4/MAIN/agent/sagemaker_agent.py:8190`. v4 itself adopted this
from `D:/Github/hermes-agent/run_agent.py:170` in v4.9.4.

PORT_LOG: #016.

Why this exists (PS Issue #2):
A parent agent could otherwise spawn N sub-agents that each loop
max_turns times, blowing the cost ceiling. Insurance/audit values
predictable cost ceilings per user request. Counter is shared across
parent + sub-agents (the parent creates one budget at the start of
`run()`; sub-agents inherit the same instance).

Phase 11 (notebook UX) will wire the budget's `consume() / remaining()
/ used() / total()` methods into an ipywidgets progress bar so the
user can SEE the budget burning down — addressing PS Issue #2's
"budget is invisible until exhausted" complaint.
"""
from __future__ import annotations

import threading


class IterationBudget:
    """Thread-safe counter shared across a parent agent and its spawned sub-agents.

    A parent agent creates one budget at the start of run(); sub-agents inherit
    the same instance. Each LLM turn (success or failure) increments the counter.
    When `consume()` returns False, the agent surfaces a "budget exhausted"
    message and stops cleanly, preserving partial work.
    """

    DEFAULT_MAX = 600  # v4.10.10 in-place: 90 -> 600 (Hermes default 90 too tight for SageMaker dev)

    def __init__(self, max_iterations: int = DEFAULT_MAX):
        self._max = max(1, int(max_iterations))
        self._used = 0
        self._lock = threading.Lock()

    def consume(self) -> bool:
        """Atomically reserve one iteration. Returns False if budget is exhausted."""
        with self._lock:
            if self._used >= self._max:
                return False
            self._used += 1
            return True

    def remaining(self) -> int:
        with self._lock:
            return max(0, self._max - self._used)

    def used(self) -> int:
        with self._lock:
            return self._used

    def total(self) -> int:
        return self._max

    def reset(self) -> None:
        """Reset counter to 0. Tests + manual /reset only — not a normal flow."""
        with self._lock:
            self._used = 0
