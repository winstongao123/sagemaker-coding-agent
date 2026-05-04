# Block N Decisions

Date: 2026-05-04

## Decisions

- Treat N-10, N-11, N-13, and N-19 as `N/A_CONSTRAINT` rows because v5.0.1
  forbids streaming and does not ship the async TaskV2 swarm surface.
- Treat N-12 as `N/A_CONSTRAINT` because v5.0.1 has no local-provider runtime;
  Bedrock stale-call handling is covered in Block L.
- Implement the concurrent state-machine lesson as local ThreadPoolExecutor
  dispatch for safe non-streaming tool calls.
- Keep QueryEngine's sequential behavior as the fallback for unsafe,
  destructive, approval-gated, or path-conflicting batches.
- Use one canonical QueryEngine `_dispatch_single_tool_call` pipeline for both
  sequential calls and parallel-safe worker calls. This directly resolves the
  pre-review risk that the parallel fast path could bypass audit logging,
  repeat-call tracking, JSON argument repair, tool_search discovery, approval
  checks, or error/forensic audit behavior.
- Keep all validation local/no-AWS until the later reviewed AWS/R-tier phase.

## Evidence

- PORT_LOG: #114.
- ADR: ADR-046.
- Tests: `logs/block-n-py-compile-iter2.log`,
  `logs/block-n-pytest-iter2.log`,
  `logs/block-n-regression-iter2.log`, and
  `logs/block-n-dispatch-relevant-regression-iter2.log`.

No human decision is currently needed for Block N.
