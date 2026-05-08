# Block F2 Decisions

Date: 2026-05-05

## D-001: Keep Runnable token budget as v5 iteration-budget continuation

Decision: Preserve the earlier ADR-028 adaptation. Runnable counted output tokens and parsed a token budget from user text; v5 uses the existing `IterationBudget` surface and only auto-continues when the explicit iteration budget is under 90 percent consumed.

Reason:

- Avoids adding a parallel budget surface for users.
- Matches the current v5 budget mechanics and tests.
- Supports long-running coding work by nudging continuation when the model stops early under a user-visible budget.

## D-002: Default off and parent-only

Decision: Keep `CONFIG.enable_token_budget_continuation` default `False`, and keep auto-continuation parent-only.

Reason:

- Prevents surprising loops unless the feature is explicitly enabled.
- Mirrors Runnable's child-agent early-out behavior.
- Protects subagent/reviewer bounded tasks from auto-continuing beyond their delegated scope.

## D-003: Broader long-coding proof is pre-AWS hardening

Decision: Do not expand F2 into new commands or R-tier execution. Record the product-level long-running software-writing target as pre-AWS hardening.

Reason:

- The current block row is F2-1 only.
- `PS_SOFTWARE_PROJECT_WORKFLOW.md` says to consolidate through existing commands.
- `TEST_CASE_PREP.md` requires zero-cost and later AWS-gated evidence for R13, R14, R15, R16, and R19-U1/U2/U3/U6/U7/U10 before final AWS spend claims.
