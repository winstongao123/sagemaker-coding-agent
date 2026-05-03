"""V5 core/budget_continuation.py — Block F2: auto-continuation under iteration budget.

PORT_LOG: F2-1.

Source: Runnable `query/tokenBudget.ts:1-93` + `query.ts:1308-1355`.

Adaptation (NEEDS-ADAPTATION verdict per Wave 5-DEEP):
- Runnable's tokenBudget tracks turn-output-tokens vs a user-set token budget
  parsed from the message text ("+500k", "use 2M tokens"). v5 reuses its
  existing IterationBudget surface (counts turns) instead of introducing a
  parallel token-counted budget — same semantic, fewer surfaces, matches
  scenario #21 wording ("F2 auto-continuation under iteration budget").
- Cost-cap halt added (Wave 6 NLT row #21): even when iter_used < 90%, if
  session_cost >= session_cost_limit, halt. Runnable's tokenBudget had no
  cost-cap interaction; v5 adds it because TOKENS.session_cost is a 1st-class
  budget surface in Block B/B+.
- Opt-in (Wave 6 NLT row #21): default OFF via CONFIG.enable_token_budget_continuation.
  Runnable's `feature('TOKEN_BUDGET')` is the equivalent flag.

Why this exists (PS Issue #2 follow-up):
The Phase-11 IterationBudgetWidget made the budget VISIBLE, but a model that
emits end_turn at 30% used silently leaves 70% of the user's reserved budget
on the floor. F2 detects "model said done early" and (when opt-in flag is on)
nudges the model to keep working until ~90% of the budget is consumed OR
diminishing returns kick in OR cost-cap is hit.

Diminishing-returns guard:
3+ consecutive nudges with iteration-delta < 2 each time means the model is
saying "ok, I'm done" with no real work between nudges. Halt cleanly.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union


COMPLETION_THRESHOLD = 0.9
DIMINISHING_THRESHOLD = 2  # iterations (Runnable: 500 tokens; iteration-adapted)


@dataclass
class BudgetTracker:
    """Per-run tracker for budget-continuation decisions.

    One instance per QueryEngine.run() call. Sub-agents do NOT get one — F2
    auto-continuation is parent-only (matches Runnable's `agentId` early-out
    at tokenBudget.ts:51).
    """
    continuation_count: int = 0
    last_delta_iters: int = 0
    last_iter_used: int = 0
    started_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))


@dataclass
class ContinueDecision:
    """Auto-continue: inject `nudge_message` as a user turn and re-invoke."""
    action: str = "continue"
    nudge_message: str = ""
    continuation_count: int = 0
    pct: int = 0
    iter_used: int = 0
    iter_total: int = 0


@dataclass
class StopDecision:
    """Halt: surface completion_event for telemetry, then return to user."""
    action: str = "stop"
    completion_event: Optional[Dict[str, Any]] = None
    reason: str = ""  # "complete" | "diminishing" | "above_threshold" | "cost_cap" | "no_budget" | "subagent"


BudgetDecision = Union[ContinueDecision, StopDecision]


def create_budget_tracker() -> BudgetTracker:
    return BudgetTracker()


def check_iteration_budget(
    tracker: BudgetTracker,
    iter_used: int,
    iter_total: int,
    is_subagent: bool = False,
    session_cost: float = 0.0,
    session_cost_limit: float = 0.0,
) -> BudgetDecision:
    """Decide whether to auto-continue or halt.

    Cost-cap halts BEFORE the under-90% check so a near-budget cost can't be
    bypassed by a low iteration count. Sub-agents always halt (parent runs
    F2; children inherit the budget but not the auto-continuation logic).
    """
    if is_subagent or iter_total <= 0:
        return StopDecision(reason="subagent" if is_subagent else "no_budget")

    if session_cost_limit > 0 and session_cost >= session_cost_limit:
        return StopDecision(
            completion_event={
                "continuation_count": tracker.continuation_count,
                "iter_used": iter_used,
                "iter_total": iter_total,
                "cost": session_cost,
                "cost_limit": session_cost_limit,
                "duration_ms": int(time.time() * 1000) - tracker.started_at_ms,
            },
            reason="cost_cap",
        )

    pct = round((iter_used / iter_total) * 100)
    delta = iter_used - tracker.last_iter_used

    is_diminishing = (
        tracker.continuation_count >= 3
        and delta < DIMINISHING_THRESHOLD
        and tracker.last_delta_iters < DIMINISHING_THRESHOLD
    )

    if not is_diminishing and iter_used < iter_total * COMPLETION_THRESHOLD:
        tracker.continuation_count += 1
        tracker.last_delta_iters = delta
        tracker.last_iter_used = iter_used
        return ContinueDecision(
            nudge_message=get_budget_continuation_message(pct, iter_used, iter_total),
            continuation_count=tracker.continuation_count,
            pct=pct,
            iter_used=iter_used,
            iter_total=iter_total,
        )

    if is_diminishing or tracker.continuation_count > 0:
        return StopDecision(
            completion_event={
                "continuation_count": tracker.continuation_count,
                "iter_used": iter_used,
                "iter_total": iter_total,
                "diminishing": is_diminishing,
                "duration_ms": int(time.time() * 1000) - tracker.started_at_ms,
            },
            reason="diminishing" if is_diminishing else "above_threshold",
        )

    return StopDecision(reason="complete")


def get_budget_continuation_message(pct: int, iter_used: int, iter_total: int) -> str:
    """Verbatim port (adapted to iterations) of Runnable's
    `getBudgetContinuationMessage` at utils/tokenBudget.ts:66-73.
    """
    return (
        f"Stopped at {pct}% of iteration budget "
        f"({iter_used:,} / {iter_total:,}). Keep working — do not summarize."
    )
