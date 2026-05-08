# Block T Changelog

Date: 2026-05-04

## Implementation

- Rebuilt Block T from canonical `SYNTHESIS_MASTER.md:354-371`.
- Updated the Block T ledger to account for all 12 rows with row-specific code,
  test, PORT_LOG, and ADR evidence.
- Added `runtime/tool_surface.py` for Block T utility rows:
  semantic boolean/number coercion, `FileTooLargeError`, range reads,
  lazy lockfiles, API limits, tool-result message budget, and XML tag
  constants.
- Wired the new helper into runtime paths:
  `tools/read_file.py`, `tools/view_image.py`, `tools/tool_search.py`, and
  `core/query_engine.py`.
- Updated `view_image` from the historical 20 MB cap to the canonical Block T
  5 MB image cap.
- Added Block T lock tests for T-6, T-7, T-8, T-10, T-11, and T-12.
- Recorded T-4 as `DROPPED_USER_APPROVED` using the existing explicit
  2026-05-03 user decision for disabled `web_fetch`.
- Recorded T-9 as `N/A_CONSTRAINT`: v5 has no streaming UI placeholder layer,
  and QueryEngine emits Bedrock tool_result blocks with `tool_use_id` directly.

## Regression Evidence

- Block T suite: 17 passed, 14 skipped.
- Phase 4 tool suite: 39 passed.
- tool_search suite: 32 passed.
- skills suite: 12 passed.
- Block N parallel-dispatch risk subset: 3 passed, 25 deselected.
- Claude iter1 LOW audit-script finding fixed: `scope_audit.py` now normalizes
  `N/A_CONSTRAINT` to the `na_constraint` count key. Process lock test added;
  Block K process suite now reports 10 passed.
- Refreshed Block T scope audit and strict gate now report 10 shipped, 1
  dropped, 1 N/A, and 0 ship-blocking rows.

## Parallel Dispatch Risk

The user-highlighted risk was explicitly rechecked before Claude review.
`core/query_engine.py` routes parallel-safe calls through
`_dispatch_single_tool_call`, the same function used by sequential calls. The
regression subset proves audit/error logging, JSON repair, and repetition guard
behavior are preserved in the parallel path.

No AWS/R-tier test was run.
