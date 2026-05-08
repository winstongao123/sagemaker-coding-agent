# Claude Recheck Prompt - Worker Readiness Wiring

You are rechecking only the three worker-readiness fixes from your prior review.

Do not edit files. Do not run Codex. Do not run AWS/R-tier spend. Do not commit,
tag, push, reset, or checkout.

Read:

- `compact_v5/_status/v5_completion_audit/06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md`
- `compact_v5/_status/v5_completion_audit/BLOCK_ORDER_AND_COVERAGE.md`
- `compact_v5/_status/v5_completion_audit/STATUS.md`
- `compact_v5/_status/v5_completion_audit/SOFTWARE_BUILDER_BLOCK_REVISIT_PLAN.md`
- `compact_v5/_status/v5_completion_audit/THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`
- `compact_v5/_status/v5_completion_audit/reviews/third-deep-scan-final-worker-readiness-claude-review-2026-05-05.md`

Check whether these prior required fixes are now satisfied:

F1. `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` and relevant software-builder
review docs are in the worker Required Read Order.

F2. Block order includes:

`... -> M -> J -> 0 -> SOFTWARE-ASYNC-DECISION -> SOFTWARE-STATE -> SOFTWARE-CHECKPOINT -> SOFTWARE-SHELL -> SOFTWARE-RESULTS -> SOFTWARE-SUBAGENT -> SOFTWARE-COMPACT-TELEMETRY -> SOFTWARE-GATE`

and explains `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` as canonical scope for
`SOFTWARE-*` blocks.

F3. `STATUS.md` clearly tells a fresh worker to continue into the `SOFTWARE-*`
queue after M/J/0.

Return exactly:

F1:
F2:
F3:
REMAINING BLOCKERS:
VERDICT:

Use one of: APPROVE, APPROVE_WITH_FIXES, REQUEST_CHANGES.
