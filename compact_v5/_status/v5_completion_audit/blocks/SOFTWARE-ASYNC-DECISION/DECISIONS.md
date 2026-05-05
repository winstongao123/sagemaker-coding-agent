# SOFTWARE-ASYNC-DECISION Decisions

Date: 2026-05-05

## Decision SAD-001: Defer True Async Subagents For v5.0.1

v5.0.1 will not implement true pollable/background subagents.

Rationale:

- DS3-S6 classifies true async/background subagents as
  `NEW_BLOCK_DECISION_REQUIRED`, not unconditional implementation.
- The target runtime is a personal SageMaker notebook environment where
  background worker lifetime, UI stop handling, orphan cleanup, cost attribution,
  and restart recovery would add substantial risk.
- The third deep scan already recommends deferring true async while validating
  strengthened synchronous supervision honestly.

Accepted v5.0.1 contract:

- `task` remains a synchronous, one-shot subagent call.
- The parent receives only the final child result for this release.
- No `job_id`, poll, wait, kill, or background task API is exposed.
- Later blocks must strengthen the synchronous path:
  `SOFTWARE-SUBAGENT` owns structured child/reviewer result envelopes, and
  `SOFTWARE-GATE` owns consumption of that evidence before `/done`.

This is not a product-ready async implementation. It is an explicit scope
decision that prevents false claims and keeps the remaining software-builder
work focused.
