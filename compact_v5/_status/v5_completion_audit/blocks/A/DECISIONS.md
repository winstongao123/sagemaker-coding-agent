# Block A Audit Decisions

## Decision A-AUDIT-001: Do Not Treat Prior Block A APPROVE As Full Scope Closure

The historical Block A Codex prompt at `compact_v5/_status/codex_reviews/block-a-iter1.md:13-26` asked for review of a narrowed scope: Compactor, auto-compact circuit breaker, cache_edits, B-2, and B+5. It did not ask the reviewer to regenerate A-1 through A-43 from `SYNTHESIS_MASTER.md`.

Therefore, the ledger treats historical Codex APPROVE as evidence for the narrowed submitted implementation only, not as evidence of full Block A completeness.

## Decision A-AUDIT-002: A-16 And A-25 Are First Implementation Batch

The worker prompt explicitly says that after the ledger, if Block A has missing/partial rows, implement A-16 and A-25 first unless the user redirects. The ledger keeps both rows ship-blocking:

- A-16: no cold-cache/microcompact/time-elapsed runtime path exists.
- A-25: generic stub helper exists in Block N, but compactor still returns summary plus recent messages without repairing orphaned post-compact tool_use blocks.

## Linked Existing ADRs

- ADR-012: prompt/cache boundary foundation.
- ADR-026: narrowed Block A compactor/circuit/cache_edits/B-2/B+5 implementation.
- ADR-037: generic Block N synthetic tool_result helper.
- ADR-040: A-16/A-25 cold-cache microcompact and post-compact stub injection.
- ADR-041: broad Block A helper slice and remaining blockers.
- ADR-042: remaining Block A blockers A-13/A-27/A-33/A-34/A-38.

New implementation work for A-16/A-25 is recorded in ADR-040.

## Decision A-IMPL-001: A-16 Uses v4 30-Minute Default With Runnable Time-Based Shape

Runnable's `timeBasedMCConfig.ts` defaults to a disabled 60-minute feature flag. v4 has an active 30-minute `COLD_CACHE_THRESHOLD_SECONDS` path that directly matches PS#3 and the R4 scenario. v5 adopts the Runnable pre-call shape and keep-recent clearing behavior, but uses the v4/SageMaker 30-minute default so the existing PS/R4 contract remains testable without waiting an hour.

## Decision A-IMPL-002: A-25 Repairs Compactor Output, Not Just Dispatcher Failures

Block N already provided the generic `synthetic_tool_result_stub()` helper. A-25 requires compactor-path wiring, so `Compactor.compact()` now calls `inject_missing_tool_result_stubs()` on its summary-plus-recent output. This keeps the Bedrock tool_use/tool_result pair invariant even when compaction cuts away the original tool result.

## Decision A-IMPL-003: Broad Helper Rows Can Ship Without Claiming Full Block A Closure

The broad helper slice closes rows that are implementable inside the current v5 Bedrock-only compact/query/runtime architecture. The ledger marks those rows SHIPPED only where code, tests, PORT_LOG #109, and ADR-041 all exist.

ADR-042 later implements the five rows left ship-blocking by this decision. Scope audit and Claude review still need to verify the row mapping.

## Decision A-IMPL-004: Remaining Rows Use Synchronous v5 Adaptations

Block A remaining rows cross systems that are asynchronous or streaming in Runnable. v5.0.1 is Bedrock-only and streaming-disabled, so the implementation uses synchronous equivalents:

- A-13 uses G2 fork replay after compaction, without streaming fallback.
- A-27 exposes a forced memory extraction hook before compaction rather than hard-coding a real model call.
- A-33 freezes prompt-cache-sensitive state across continued sessions and allows immediate changes only through `prompt_cache_now=True`.
- A-34 records transition reasons and returns immediately on API errors.
- A-38 dedupes preservedSegment metadata before turn construction while keeping the recent tail intact.

These rows are now marked SHIPPED in the ledger pending scope audit and Claude review.

## Decision A-IMPL-005: Iter10 LOW Findings Fixed In-Block

Per user policy update, local LOW Claude findings inside the current block are fixed automatically rather than requiring a stop. The iter10 findings were resolved as follows:

- A-22: strengthened the ordering-invariant lock test so it asserts summary first, recent tail in the middle, and todo restoration last.
- A-30: made `reset_retry_counters()` clear the `AUTO_COMPACT` failure state via `record_success()` and strengthened the lock test.
- A-37: wired `CONFIG.cache_ttl` into emitted Bedrock `cache_control` payloads, with supported values `5m` and `1h` and fallback to `5m` for invalid values.

These fixes are recorded in ADR-043 and PORT_LOG #111.
