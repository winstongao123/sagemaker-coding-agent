I independently verified the Block A artifacts against `SYNTHESIS_MASTER.md:149-191` and the implementation evidence anchors in the prompt.

---

# Block A Post-Implementation Review (A-16 / A-17 / A-21 / A-25)

## Independently regenerated row list (from SYNTHESIS_MASTER.md:149-191)

A-1, A-2, A-3, A-4, A-5, A-6, A-7, A-8, A-9, A-10, A-11, A-12, A-13, A-14, A-15, A-16, A-17, A-18, A-19, A-20, A-21, A-22, A-23, A-24, A-25, A-26, A-27, A-28, A-29, A-30, A-31, A-32, A-33, A-34, A-35, A-36, A-37, A-38, A-39, A-40, A-41, A-42, A-43.

## Counts

- Expected row count: **43**
- Ledger row count: **43**
- SHIPPED: **6** (A-16, A-17, A-21, A-22, A-25, A-40) — matches expected
- PARTIAL: **9** (A-1, A-3, A-8, A-13, A-31, A-32, A-33, A-34, A-35)
- MISSING: **28** (A-2, A-4, A-5, A-6, A-7, A-9, A-10, A-11, A-12, A-14, A-15, A-18, A-19, A-20, A-23, A-24, A-26, A-27, A-28, A-29, A-30, A-36, A-37, A-38, A-39, A-41, A-42, A-43)
- DEFERRED_USER_APPROVED: 0
- DROPPED_USER_APPROVED: 0
- N/A_CONSTRAINT: 0
- Sums: 6 + 9 + 28 = 43 ✓

## Implementation evidence verification

- **A-16 (cold-cache time-based microcompact)**: VERIFIED.
  - Constants `COLD_CACHE_THRESHOLD_SECONDS = 30*60`, `KEEP_LAST_N_COLD_CACHE = 1`, `MICROCOMPACT_TRIGGER_PERCENT = 0.70` at `core/compactor.py:157-174`. `microcompact()` keep_n_override path at `core/compactor.py:211-266`.
  - Pre-call cold-cache idle trigger and `[i] Cold cache detected` output at `core/query_engine.py:524-560`.
  - Tests `test_microcompact_cold_cache_keep_last_1` at `tests/integration/test_block_a.py:99-120` and `test_cold_cache_30min_idle_triggers_microcompact` at `:133-168`.
  - PORT_LOG row #105 present; ADR-040 present.
- **A-17 (COMPACTABLE_TOOLS allowlist)**: VERIFIED.
  - `COMPACTABLE_TOOLS` set at `core/compactor.py:163-173`; `MICROCOMPACT_TOOLS = COMPACTABLE_TOOLS` at :173; allowlist used in `microcompact()` at `:240`.
  - Test `test_compactable_tools_allowlist_excludes_document_creators` at `tests/integration/test_block_a.py:123-130` (excludes `create_word`/`create_excel`/`create_pdf`).
  - PORT_LOG row #107 present; ADR-040 present.
- **A-21 (post-compact cleanup / cache invalidation)**: VERIFIED.
  - `run_post_compact_cleanup()` at `core/compactor.py:618-658` (file_read_tracking, FILE_CACHE.clear_all, skill listing cache, prompt section cache).
  - Invocation after successful compact at `core/compactor.py:765`.
  - Skill-manager pass-through at `core/query_engine.py:676-681`.
  - `clear_tracked_reads()` at `tools/_file_read_tracking.py:84-92`.
  - `clear_listing_cache()` at `skills/manager.py:371-373` (preserves `active_skill`).
  - Test `test_run_post_compact_cleanup_invalidates_context_caches` at `tests/integration/test_block_a.py:243-279`; verifies all four caches cleared and that `active_skill` is preserved.
  - PORT_LOG row #108 present; ADR-040 present.
- **A-25 (post-compact synthetic tool_result stub injection)**: VERIFIED.
  - `inject_missing_tool_result_stubs()` at `core/compactor.py:660-734`, invoked from `Compactor.compact()` at `:615` so summary-plus-recent output repairs orphaned `tool_use` blocks via the Block N helper (`core/parallel_dispatch.synthetic_tool_result_stub`).
  - Test `test_h2_stub_injection_for_orphan_tool_use` at `tests/integration/test_block_a.py:282-310`.
  - PORT_LOG row #106 present; ADR-040 present.

## R-tier evidence boundary

- R4 zero-AWS executable marker present at `tests/r_tier/test_r4_cold_cache.py` with explicit double-env-var skip gate (`RUN_REAL_BEDROCK` AND `RUN_R4_IDLE_WAIT`). It is correctly described as a marker, not AWS pass evidence.
- R-tier readiness specs at `tests/r_tier/test_r6_to_r19_readiness_specs.py` materialize R6-R16, R18-E1..E15, R19-U1..U10 markers without Bedrock calls.
- `R_TIER_GATE_STATUS.md:75-80` explicitly states the local gate pass is "zero-cost Phase A contracts, not AWS pass evidence." Block A artifacts (`TESTS.md:74-84`, `WORKER_SELF_REVIEW.md:43`) repeat the same caveat. **R-tier gate pass is not overstated as AWS evidence.**
- R4 `pytest` result was `1 skipped`, not pass. No AWS spend recorded.

## Process / non-spend confirmations

- Worker did not run AWS/R-tier real spend. Confirmed via `WORKER_SELF_REVIEW.md` (R4 `SKIPPED, 1 skipped because real-AWS env vars were not set`).
- Worker did not run Codex CLI review nor invoke nested Codex workers. Confirmed by `00_MASTER_PROTOCOL.md:17-20` requirement and the absence of Codex review artifacts under `_status/v5_completion_audit/blocks/A/`.
- `STATUS.md` remains `LEDGER_COMPLETE_IMPLEMENTATION_REQUIRED`; Block A is **not** marked DONE. ✓
- `GIT_CLOSE_PLAN.md` Status: `NOT_READY` (no premature close). ✓
- `MEMORY_UPDATE.md` Status: `DRAFT_NOT_APPLIED` (correctly gated on close). ✓

## Findings

1. **Minor (non-blocking) line-number drift in ledger/TESTS.md anchors.** The ledger cites `core/compactor.py:614-679` and the TESTS.md cites `test_block_a.py:233-260` for A-25, but the actual `inject_missing_tool_result_stubs()` definition is at `:660-734` (invocation at `:615`) and the test starts at `test_block_a.py:282`. The substantive evidence exists and matches the prompt's anchors at `core/compactor.py:614-679`/the prompt's cited anchors are correct; the discrepancy is in the worker's narrative line ranges, not the code or test. Recommend tightening anchors on next pass; not ship-blocking.
2. No other discrepancies. Counts in `LEDGER.md:52-60`, `STATUS.md:11-14`, and `WORKER_SELF_REVIEW.md:18-25` all agree (43 / 6 / 9 / 28 / 0 / 0 / 0; ship-blocking 37).

## Remaining ship-blocking rows

**37** rows: A-1, A-2, A-3, A-4, A-5, A-6, A-7, A-8, A-9, A-10, A-11, A-12, A-13, A-14, A-15, A-18, A-19, A-20, A-23, A-24, A-26, A-27, A-28, A-29, A-30, A-31, A-32, A-33, A-34, A-35, A-36, A-37, A-38, A-39, A-41, A-42, A-43.

Block A is not closeable. v5.0.1 is not ship-ready.

## VERDICT: APPROVE

The A-16 / A-17 / A-21 / A-25 batch is correctly marked `SHIPPED` with code, test, PORT_LOG (#105/#106/#107/#108), and ADR-040 evidence. The 43-row ledger is intact, dispositions and ship-blocking count are consistent, the R-tier gate pass is correctly scoped to local marker materialization (not AWS evidence), R4 carries an explicit double-env-var skip gate, no AWS/Codex spend occurred, and Block A status remains `LEDGER_COMPLETE_IMPLEMENTATION_REQUIRED`. The line-number drift on A-25 anchors is cosmetic and should be tightened, but does not invalidate the evidence.
