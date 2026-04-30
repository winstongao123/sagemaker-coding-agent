"""Phase 08 unit tests: core/budget.py — IterationBudget.

Locks PORT_LOG #016: verbatim port of v4's IterationBudget (Hermes pattern).
"""
from __future__ import annotations

import os
import sys
import threading

_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


def test_default_max_is_600():
    from core.budget import IterationBudget
    b = IterationBudget()
    assert b.total() == 600


def test_consume_decrements_remaining():
    from core.budget import IterationBudget
    b = IterationBudget(max_iterations=3)
    assert b.remaining() == 3
    assert b.consume() is True
    assert b.used() == 1
    assert b.remaining() == 2


def test_consume_returns_false_when_exhausted():
    from core.budget import IterationBudget
    b = IterationBudget(max_iterations=2)
    assert b.consume() is True
    assert b.consume() is True
    assert b.consume() is False
    # Subsequent calls also return False without incrementing
    assert b.consume() is False
    assert b.used() == 2


def test_min_clamp_to_one():
    """max_iterations <= 0 must clamp to 1 (defensive)."""
    from core.budget import IterationBudget
    b = IterationBudget(max_iterations=0)
    assert b.total() == 1
    assert b.consume() is True
    assert b.consume() is False


def test_reset_clears_used():
    from core.budget import IterationBudget
    b = IterationBudget(max_iterations=2)
    b.consume()
    b.consume()
    assert b.used() == 2
    b.reset()
    assert b.used() == 0
    assert b.consume() is True


def test_thread_safety_under_concurrent_consumers():
    """20 threads each calling consume() 100 times against a budget of 1000
    must end with exactly 1000 successful consumes and zero overshoot."""
    from core.budget import IterationBudget
    b = IterationBudget(max_iterations=1000)
    successes: list = []
    lock = threading.Lock()

    def worker():
        local = 0
        for _ in range(100):
            if b.consume():
                local += 1
        with lock:
            successes.append(local)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sum(successes) == 1000
    assert b.used() == 1000
    assert b.consume() is False


def test_shared_budget_across_pseudo_subagents():
    """The Hermes pattern: a parent + N "sub-agents" share one budget instance."""
    from core.budget import IterationBudget
    parent = IterationBudget(max_iterations=10)
    child_a = parent  # sub-agents inherit the same instance
    child_b = parent

    for _ in range(4):
        assert parent.consume() is True
    for _ in range(3):
        assert child_a.consume() is True
    for _ in range(3):
        assert child_b.consume() is True
    # All 10 used; next call returns False regardless of caller
    assert parent.consume() is False
    assert child_a.consume() is False
    assert child_b.consume() is False
