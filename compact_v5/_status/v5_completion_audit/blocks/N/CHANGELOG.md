# Block N Changelog

Date: 2026-05-04

## Changed

- Added v5-filtered parallel dispatch constants, path-scope helpers, dispatch
  planning, ThreadPoolExecutor execution, worker checkpoint snapshots, aggregate
  turn-budget enforcement, pending tool-use tracking, retry classification, and
  mid-call stub recovery to `core/parallel_dispatch.py`.
- Wired QueryEngine to use the parallel dispatcher for all-safe multi-tool
  batches while preserving sequential fallback for unsafe/path-conflicting
  batches.
- Refactored QueryEngine tool dispatch so parallel-safe calls and sequential
  calls share `_dispatch_single_tool_call`, preserving audit logging,
  repeat-call tracking, JSON argument repair, tool_search discovery, approval
  checks, and tool error/forensic behavior in both paths.
- Added `interrupt_behavior` metadata to `ToolRecord`/`ToolDef`.
- Expanded `tests/integration/test_block_n.py` to executable no-AWS coverage
  for the active Block N rows and removed older skipped local timing tests.
- Added lock tests proving the parallel fast path preserves audit logging,
  JSON argument repair, and error/repetition forensics.
- Added PORT_LOG #114 and ADR-046.

## Validation

- Compile: PASS (`logs/block-n-py-compile.log`).
- Targeted tests: 28 passed (`logs/block-n-pytest-iter2.log`).
- Regression tests: 53 passed (`logs/block-n-regression-iter2.log`).
- Dispatch-relevant audit/JSON/repetition subset: 5 passed
  (`logs/block-n-dispatch-relevant-regression-iter2.log`).
- No AWS/R-tier spend.
