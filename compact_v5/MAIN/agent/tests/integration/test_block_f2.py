"""Block F2 — Auto-continuation under iteration budget.

Source: Runnable `query/tokenBudget.ts` + `query.ts:1308-1355`.
Adapted to v5's IterationBudget surface (NEEDS-ADAPTATION verdict).

Tests per TEST_DESIGN.md §Block F2 (3 T2 tests, $0):
- test_f2_auto_continue_at_under_90pct
- test_f2_blocks_at_90pct
- test_f2_respects_cost_cap

+ NLT lock test from PS_Plan_Edge_Cases scenario #21
  ("F2 auto-continuation respects cost cap + opt-in"):
- test_f2_default_off_no_continuation_when_disabled (opt-in contract)

+ behavioral lock tests:
- test_f2_diminishing_returns_halts_after_3_continuations
- test_f2_subagent_does_not_auto_continue
- test_f2_tracker_resets_between_runs
"""
from __future__ import annotations

import os
import sys
from typing import Any, List

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# Pure-function tests — check_iteration_budget logic
# ============================================================

def test_check_returns_continue_when_under_90pct():
    """iter_used < 90% AND not diminishing → ContinueDecision."""
    from core.budget_continuation import (
        check_iteration_budget,
        create_budget_tracker,
        ContinueDecision,
    )

    tracker = create_budget_tracker()
    decision = check_iteration_budget(tracker, iter_used=10, iter_total=100)
    assert isinstance(decision, ContinueDecision)
    assert decision.action == "continue"
    assert decision.pct == 10
    assert decision.continuation_count == 1
    # Tracker mutated for next call
    assert tracker.continuation_count == 1
    assert tracker.last_iter_used == 10


def test_check_returns_stop_at_90pct():
    """iter_used >= 90% → StopDecision (not above_threshold; no prior continues)."""
    from core.budget_continuation import (
        check_iteration_budget,
        create_budget_tracker,
        StopDecision,
    )

    tracker = create_budget_tracker()
    decision = check_iteration_budget(tracker, iter_used=90, iter_total=100)
    assert isinstance(decision, StopDecision)
    assert decision.action == "stop"
    assert decision.reason == "complete"  # never continued, just past threshold


def test_check_respects_cost_cap_even_under_90pct():
    """session_cost >= session_cost_limit → halt even if iter_used < 90%."""
    from core.budget_continuation import (
        check_iteration_budget,
        create_budget_tracker,
        StopDecision,
    )

    tracker = create_budget_tracker()
    decision = check_iteration_budget(
        tracker,
        iter_used=10,        # only 10% used
        iter_total=100,
        session_cost=2.50,
        session_cost_limit=2.00,  # already over cap
    )
    assert isinstance(decision, StopDecision)
    assert decision.reason == "cost_cap"
    assert decision.completion_event["cost"] == 2.50
    assert decision.completion_event["cost_limit"] == 2.00
    # Tracker NOT advanced when cost-capped
    assert tracker.continuation_count == 0


def test_check_subagent_never_auto_continues():
    """is_subagent=True → StopDecision regardless of usage."""
    from core.budget_continuation import (
        check_iteration_budget,
        create_budget_tracker,
        StopDecision,
    )

    tracker = create_budget_tracker()
    decision = check_iteration_budget(
        tracker, iter_used=10, iter_total=100, is_subagent=True,
    )
    assert isinstance(decision, StopDecision)
    assert decision.reason == "subagent"


def test_check_diminishing_returns_halts():
    """3+ consecutive continuations with delta<2 each → diminishing → halt."""
    from core.budget_continuation import (
        check_iteration_budget,
        create_budget_tracker,
        ContinueDecision,
        StopDecision,
    )

    tracker = create_budget_tracker()
    # Each call increments iter_used by 1 — definite "diminishing" pattern.
    d1 = check_iteration_budget(tracker, iter_used=1, iter_total=100)
    d2 = check_iteration_budget(tracker, iter_used=2, iter_total=100)
    d3 = check_iteration_budget(tracker, iter_used=3, iter_total=100)
    # First three are continues (count=1, 2, 3 with delta=1 each).
    assert isinstance(d1, ContinueDecision)
    assert isinstance(d2, ContinueDecision)
    assert isinstance(d3, ContinueDecision)
    # 4th call: count >= 3 AND delta=1 AND last_delta=1 → diminishing.
    d4 = check_iteration_budget(tracker, iter_used=4, iter_total=100)
    assert isinstance(d4, StopDecision)
    assert d4.reason == "diminishing"
    assert d4.completion_event["diminishing"] is True


def test_check_no_budget_total_zero():
    """iter_total <= 0 → StopDecision reason=no_budget."""
    from core.budget_continuation import (
        check_iteration_budget,
        create_budget_tracker,
        StopDecision,
    )

    tracker = create_budget_tracker()
    decision = check_iteration_budget(tracker, iter_used=0, iter_total=0)
    assert isinstance(decision, StopDecision)
    assert decision.reason == "no_budget"


def test_continuation_message_format():
    """Verbatim port of Runnable's getBudgetContinuationMessage shape."""
    from core.budget_continuation import get_budget_continuation_message

    msg = get_budget_continuation_message(pct=42, iter_used=100, iter_total=240)
    assert "42%" in msg
    assert "100" in msg and "240" in msg
    assert "Keep working" in msg
    assert "do not summarize" in msg.lower()


# ============================================================
# Wired-into-engine tests — TEST_DESIGN names
# ============================================================

class _ScriptedClient:
    """Same mock client shape as test_query_engine.py."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []
        self.model_id = "anthropic.claude-haiku-4-5-20251001-v1:0"
        self.mock_mode = True

    def chat(self, messages, system, tools, max_tokens, temperature,
             thinking_enabled, thinking_budget):
        from runtime.bedrock_client import Response
        self.calls.append({"messages": list(messages)})
        if not self.script:
            return Response(text="(no more scripted)", tool_calls=[],
                            stop_reason="end_turn", usage={})
        kind, *rest = self.script.pop(0)
        if kind == "text":
            return Response(text=rest[0], tool_calls=[],
                            stop_reason="end_turn", usage={})
        raise AssertionError(f"unknown kind {kind}")


@pytest.fixture(autouse=True)
def fresh_registry():
    from tools.registry import _reset_registry_for_tests
    from tools import bootstrap_built_ins
    _reset_registry_for_tests()
    bootstrap_built_ins()
    yield


@pytest.fixture
def reset_tokens():
    """F2 reads TOKENS.session_cost; reset before each test for determinism."""
    from runtime.tokens import TOKENS
    TOKENS.reset()
    yield
    TOKENS.reset()


def test_f2_auto_continue_at_under_90pct(reset_tokens):
    """TEST_DESIGN row 1: iteration_used < 90% AND not diminishing-returns →
    auto-continue. Engine emits one nudge between two end_turn responses.

    Budget=2: after turn 1 used=1/2=50% → continue. After turn 2 used=2/2=100%
    → above_threshold → stop. Net: 2 turns, 1 nudge in between.
    """
    from core import QueryEngine
    from core.budget import IterationBudget
    from runtime.config import CONFIG
    from tools import all_registered

    CONFIG.enable_token_budget_continuation = True
    try:
        client = _ScriptedClient([
            ("text", "First answer (premature)."),
            ("text", "Final answer after nudge."),
        ])
        budget = IterationBudget(max_iterations=2)
        engine = QueryEngine(client=client, max_turns=5, budget=budget)
        result = engine.run(
            user_message="do work",
            system_prompt="sys",
            tools=all_registered(),
        )
        assert result.turns_used == 2
        assert result.stop_reason == "end_turn"
        assert result.text == "Final answer after nudge."
        # 2nd Bedrock call's messages must include the nudge as a user turn.
        assert len(client.calls) == 2
        last_user = [m for m in client.calls[1]["messages"] if m["role"] == "user"][-1]
        content = last_user.get("content")
        if isinstance(content, list):
            content = " ".join(
                b.get("text", "") for b in content if isinstance(b, dict)
            )
        assert "Keep working" in content
    finally:
        CONFIG.enable_token_budget_continuation = False


def test_f2_blocks_at_90pct(reset_tokens):
    """TEST_DESIGN row 2: iter_used >= 90% → halts (no nudge injected)."""
    from core import QueryEngine
    from core.budget import IterationBudget
    from runtime.config import CONFIG
    from tools import all_registered

    CONFIG.enable_token_budget_continuation = True
    try:
        client = _ScriptedClient([
            ("text", "Final answer."),
        ])
        # Budget=2: after first turn used=1, ratio 50% (under 90%) — but to
        # exercise the 90% gate we use budget=1 so iter_used=1/1=100% on
        # first end_turn check → ContinueDecision is NOT emitted.
        budget = IterationBudget(max_iterations=1)
        engine = QueryEngine(client=client, max_turns=5, budget=budget)
        result = engine.run(
            user_message="do work",
            system_prompt="sys",
            tools=all_registered(),
        )
        # Only 1 turn — no nudge.
        assert result.turns_used == 1
        assert result.stop_reason == "end_turn"
        assert result.text == "Final answer."
        assert len(client.calls) == 1
    finally:
        CONFIG.enable_token_budget_continuation = False


def test_f2_respects_cost_cap(reset_tokens):
    """TEST_DESIGN row 3: even if iter_used < 90%, if session_cost >=
    session_cost_limit → halt without nudge."""
    from core import QueryEngine
    from core.budget import IterationBudget
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    from tools import all_registered

    CONFIG.enable_token_budget_continuation = True
    CONFIG.session_cost_limit = 1.00
    try:
        # Inflate session_cost above the limit BEFORE the run.
        TOKENS.session_cost = 1.50

        client = _ScriptedClient([
            ("text", "Stops short despite plenty of iterations."),
        ])
        budget = IterationBudget(max_iterations=100)
        engine = QueryEngine(client=client, max_turns=5, budget=budget)
        result = engine.run(
            user_message="do work",
            system_prompt="sys",
            tools=all_registered(),
        )
        # Cost-cap fired before continuation was emitted.
        assert result.turns_used == 1
        assert result.stop_reason == "end_turn"
        assert result.text == "Stops short despite plenty of iterations."
        assert len(client.calls) == 1
    finally:
        CONFIG.enable_token_budget_continuation = False
        CONFIG.session_cost_limit = 0.0


# ============================================================
# Behavioral lock tests
# ============================================================

def test_f2_default_off_no_continuation_when_disabled(reset_tokens):
    """Wave 6 NLT row #21 lock: opt-in. Default OFF means even when iter_used
    is well under 90%, the engine MUST NOT auto-continue."""
    from core import QueryEngine
    from core.budget import IterationBudget
    from runtime.config import CONFIG
    from tools import all_registered

    # Verify default is False
    assert CONFIG.enable_token_budget_continuation is False

    client = _ScriptedClient([
        ("text", "Premature answer that should NOT trigger continuation."),
    ])
    budget = IterationBudget(max_iterations=1000)  # 0.1% used after 1 turn
    engine = QueryEngine(client=client, max_turns=5, budget=budget)
    result = engine.run(
        user_message="do work",
        system_prompt="sys",
        tools=all_registered(),
    )
    # No nudge fired → exactly 1 turn.
    assert result.turns_used == 1
    assert result.stop_reason == "end_turn"
    assert len(client.calls) == 1


def test_f2_diminishing_returns_halts_after_3_continuations(reset_tokens):
    """End-to-end lock: after 3 nudges with no real iteration progress, the
    engine halts via diminishing-returns guard."""
    from core import QueryEngine
    from core.budget import IterationBudget
    from runtime.config import CONFIG
    from tools import all_registered

    CONFIG.enable_token_budget_continuation = True
    try:
        # 6 end_turn responses queued. After turn 4, diminishing kicks in.
        client = _ScriptedClient([
            ("text", "answer 1"),
            ("text", "answer 2"),
            ("text", "answer 3"),
            ("text", "answer 4"),
            ("text", "answer 5"),
            ("text", "answer 6"),
        ])
        # Budget total=100. After each turn iter_used grows by 1, so delta=1
        # each time → diminishing fires after the 3rd continuation.
        budget = IterationBudget(max_iterations=100)
        engine = QueryEngine(client=client, max_turns=10, budget=budget)
        result = engine.run(
            user_message="do work",
            system_prompt="sys",
            tools=all_registered(),
        )
        # Continues x3, then halts on the 4th end_turn → 4 total turns.
        assert result.turns_used == 4
        assert result.stop_reason == "end_turn"
        assert result.text == "answer 4"
    finally:
        CONFIG.enable_token_budget_continuation = False


def test_f2_subagent_does_not_auto_continue(reset_tokens):
    """Sub-agents inherit the IterationBudget but NOT the F2 auto-continue
    logic (matches Runnable's `agentId` early-out)."""
    from core import QueryEngine
    from core.budget import IterationBudget
    from runtime.config import CONFIG
    from tools import all_registered

    CONFIG.enable_token_budget_continuation = True
    try:
        client = _ScriptedClient([
            ("text", "child says done."),
        ])
        budget = IterationBudget(max_iterations=1000)
        engine = QueryEngine(
            client=client, max_turns=5, budget=budget,
            agent_kind="explore",  # any non-"parent" string flags subagent
        )
        result = engine.run(
            user_message="do work",
            system_prompt="sys",
            tools=all_registered(),
        )
        # Sub-agent must NOT emit a nudge despite iter_used < 90%.
        assert result.turns_used == 1
        assert result.stop_reason == "end_turn"
        assert len(client.calls) == 1
    finally:
        CONFIG.enable_token_budget_continuation = False


def test_f2_tracker_resets_between_runs(reset_tokens):
    """Each run() starts with a fresh BudgetTracker. The tracker created in
    run 1 must NOT be the same object as the tracker in run 2 — otherwise
    diminishing-returns state would leak across user messages.
    """
    from core import QueryEngine
    from core.budget import IterationBudget
    from runtime.config import CONFIG
    from tools import all_registered

    CONFIG.enable_token_budget_continuation = True
    try:
        # Run 1: triggers continuation, captures tracker object.
        client = _ScriptedClient([
            ("text", "r1 t1"),
            ("text", "r1 t2"),
        ])
        budget = IterationBudget(max_iterations=2)  # 2 turns then above_threshold
        engine = QueryEngine(client=client, max_turns=5, budget=budget)
        engine.run(
            user_message="do work 1",
            system_prompt="sys",
            tools=all_registered(),
        )
        tracker_run_1 = engine._budget_tracker
        assert tracker_run_1 is not None

        # Run 2: bump budget total via internals so the engine has headroom.
        # The reset hook in run() must replace the tracker object.
        budget._max = 4  # raise ceiling so run 2 has 2 more iterations
        client.script = [
            ("text", "r2 t1"),
            ("text", "r2 t2"),
        ]
        engine.run(
            user_message="do work 2",
            system_prompt="sys",
            tools=all_registered(),
        )
        tracker_run_2 = engine._budget_tracker
        assert tracker_run_2 is not None
        assert tracker_run_2 is not tracker_run_1, (
            "BudgetTracker must be a fresh object per run(); leaked state "
            "would silently reduce auto-continuation across user messages."
        )
    finally:
        CONFIG.enable_token_budget_continuation = False
