# Block N Reviewer Verdict

Status: APPROVED_READY_FOR_CLOSE
Date: 2026-05-04

## Iter1

Review: `compact_v5/_status/v5_completion_audit/reviews/block-n-claude-review-iter1.md`

Latest usable Claude verdict: `APPROVE_WITH_FIXES`

Ship decision: `READY_FOR_BLOCK_CLOSE_REVIEW`

Expected rows: 19
Ledger rows: 19
Remaining ship-blocking rows: 0

Findings:

- LOW `parallel_dispatch.py` module docstring said QueryEngine integration had
  not landed. Fixed in iter2 local changes.
- LOW `scope_audit.py` summary reports `N/A: 0` while per-row dispositions show
  five `N/A_CONSTRAINT` rows. This is a cosmetic global audit-summary display
  issue, not a Block N ship blocker.
- LOW PORT_LOG #114 historical-review field was `(pending)`. Updated to cite
  Claude iter1 and mark iter2 pending.

## Iter2

Review: `compact_v5/_status/v5_completion_audit/reviews/block-n-claude-review-iter2.md`

Latest usable Claude verdict: `APPROVE`

Ship decision: `READY_FOR_BLOCK_CLOSE_REVIEW`

Expected rows: 19
Ledger rows: 19
Remaining ship-blocking rows: 0

Claude explicitly verified that the user-raised parallel fast-path risk is
resolved in code: both the ThreadPoolExecutor worker path and sequential
fallback call `_dispatch_single_tool_call`, and the new lock tests exercise
parallel-path audit, JSON repair, and repetition/error behavior.

Iter2 LOW findings:

- Missing `block-n-py-compile-iter2.log` artifact. Fixed by rerunning
  `py_compile` and writing the explicit PASS log.
- Existing broad Block B count-token tests require local `boto3`; accepted by
  Claude as environment-only and not a Block N regression because the
  dispatch-relevant subset passed.
- Pre-existing cosmetic `scope_audit.py` N/A summary display issue; not a
  Block N ship blocker.

## User Pre-Review Risk

Before iter2, the user identified a substantive risk that QueryEngine's
parallel dispatch fast path could bypass sequential dispatch bookkeeping:
audit logging, repeat-call tracking, JSON argument repair, and tool
error/forensics.

Resolution:

- Added `_dispatch_single_tool_call` in `core/query_engine.py`.
- Both parallel-safe ThreadPoolExecutor workers and sequential fallback now call
  this same single-tool pipeline.
- Added lock tests proving parallel-path audit success/error logging, JSON
  repair, and repeat-call/error forensics are preserved.

Validation:

- `block-n-py-compile-iter2.log`: PASS.
- `block-n-pytest-iter2.log`: 28 passed.
- `block-n-regression-iter2.log`: 53 passed.
- `block-n-dispatch-relevant-regression-iter2.log`: 5 passed.
- `block-n-scope-audit-iter2.log`: 0 ship-blocking rows.
- `block-n-scope-audit-strict-iter2.log`: 0 ship-blocking rows.

Final mechanical audit after iter2: `block-n-scope-audit-final.log` and
`block-n-scope-audit-strict-final.log` both report 0 ship-blocking rows and
`READY_TO_REVIEW_CLOSE`.
