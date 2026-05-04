# Claude Reviewer Prompt - Block A Post-Implementation Review

You are the independent Claude Code reviewer for the v5.0.1 completion redo.

This is not the original ledger-only review. Review the current Block A
post-implementation batch after Codex implemented A-16, A-17, A-21, and A-25.

Return the review text directly to stdout. Do not create a plan file, do not
call ExitPlanMode, and do not write or edit any repository file. The supervisor
will save stdout under `compact_v5/_status/v5_completion_audit/reviews/`.

Do not trust the worker's row list. Independently read:

1. `compact_v5/_status/v5_completion_audit/00_MASTER_PROTOCOL.md`
2. `compact_v5/_status/v5_completion_audit/03_LEDGER_SCHEMA.md`
3. `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md`
4. `compact_v5/_status/PS_CRITICAL_WORKER_PROBLEM.md`

Then review Block A artifacts:

- `compact_v5/_status/v5_completion_audit/blocks/A/LEDGER.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/TESTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/CHANGELOG.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/DECISIONS.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/STATUS.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/WORKER_SELF_REVIEW.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/MEMORY_UPDATE.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/GIT_CLOSE_PLAN.md`

Review implementation evidence for:

- A-16 cold-cache time-based microcompact
- A-17 compactable-tool allowlist
- A-21 post-compact cleanup/cache invalidation
- A-25 post-compact synthetic `tool_result` stub injection
- R4 zero-AWS executable marker and the explicit no-AWS skip gate
- R-tier readiness marker update only as local gate evidence, not AWS pass evidence

Read the relevant changed files:

- `compact_v5/MAIN/agent/core/compactor.py`
- `compact_v5/MAIN/agent/core/query_engine.py`
- `compact_v5/MAIN/agent/skills/manager.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_a.py`
- `compact_v5/MAIN/agent/tests/r_tier/test_r4_cold_cache.py`
- `compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py`
- `compact_v5/MAIN/agent/tools/_file_read_tracking.py`
- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md`
- `compact_v5/_status/V5_DESIGN_DECISIONS.md`
- `compact_v5/_status/R_TIER_GATE_STATUS.md`
- `compact_v5/_status/R_TIER_PENDING_TESTS.md`
- `compact_v5/_status/r_tier_test_matrix.json`
- `compact_v5/_status/v5_completion_audit/TEST_CASE_PREP.md`

Required review:

1. Regenerate the expected Block A row list directly from `SYNTHESIS_MASTER.md`.
2. Confirm the Block A ledger still has 43/43 canonical rows.
3. Confirm whether A-16, A-17, A-21, and A-25 are correctly marked `SHIPPED`.
4. Reject if any of A-16/A-17/A-21/A-25 lacks code evidence, test evidence,
   PORT_LOG evidence, or ADR evidence.
5. Reject if the R-tier gate pass is overstated as AWS evidence.
6. Confirm remaining Block A blocking-row count and that Block A is not marked
   done.
7. Confirm the worker did not run AWS/R-tier spend, Codex review, or nested
   Codex.

Implementation evidence anchors to verify:

- A-16: `core/compactor.py` microcompact constants and clearing path;
  `core/query_engine.py` pre-call cold-cache idle trigger; tests
  `test_microcompact_cold_cache_keep_last_1` and
  `test_cold_cache_30min_idle_triggers_microcompact`; PORT_LOG #105; ADR-040.
- A-17: `core/compactor.py` `COMPACTABLE_TOOLS` allowlist and
  `test_compactable_tools_allowlist_excludes_document_creators`; PORT_LOG #107;
  ADR-040.
- A-21: `core/compactor.py:618-655` `run_post_compact_cleanup`;
  `core/compactor.py:765` cleanup invocation after successful compaction;
  `core/query_engine.py:676-681` active skill-manager pass-through;
  `tools/_file_read_tracking.py:84-97` production read-tracking clear;
  `skills/manager.py:371-373` skill-listing cache clear;
  `tests/integration/test_block_a.py:243-281`
  `test_run_post_compact_cleanup_invalidates_context_caches`;
  PORT_LOG #108; ADR-040.
- A-25: `core/compactor.py` `inject_missing_tool_result_stubs` call from
  `compact()` and `test_h2_stub_injection_for_orphan_tool_use`; PORT_LOG #106;
  ADR-040.

Expected current counts:

- Expected rows: 43.
- Ledger rows: 43.
- SHIPPED: 6 (`A-16`, `A-17`, `A-21`, `A-22`, `A-25`, `A-40`).
- PARTIAL: 9.
- MISSING: 28.
- Remaining ship-blocking rows: 37.
- `blocks/A/STATUS.md` must remain `LEDGER_COMPLETE_IMPLEMENTATION_REQUIRED`;
  Block A is not done.

Return exactly:

- Expected row count.
- Ledger row count.
- Disposition counts.
- Findings, if any.
- Remaining ship-blocking rows.
- `VERDICT: APPROVE`, `VERDICT: APPROVE_WITH_FIXES`, or `VERDICT: REJECT`.

Do not run Codex CLI. Do not spend AWS/R-tier. Do not edit files.
