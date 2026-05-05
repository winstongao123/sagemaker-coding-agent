Confirmed: `max_context_tokens` triggers the sanitizer's `token` substring rule and is redacted, contradicting the stated goal in `DECISIONS.md`. Now writing the review.

---

# SOFTWARE-COMPACT-TELEMETRY Independent Claude Review

**Reviewer:** Claude (Opus 4.7, 1M context)
**Date:** 2026-05-05
**Iteration:** iter1

## Reconstructed Canonical Scope

Source files read directly from disk:
- `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` (DS3-S9, DS3-S10, DS3-S18 + Gap-To-Block traceability table)
- `PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md` (PS3-1, PS3-6)
- `BLOCK_ORDER_AND_COVERAGE.md` (block scope confirmation)

Independently-reconstructed canonical row set for SOFTWARE-COMPACT-TELEMETRY:

| Canonical id | Source | Required behavior | Decision class |
|---|---|---|---|
| DS3-S9 | THIRD_DEEP_SCAN §Consolidated Scan Findings | Manual `/compact` command OR explicit no-goal decision + tests for manual compaction trigger | TEST_HARDENING_ONLY |
| DS3-S10 | THIRD_DEEP_SCAN §Consolidated Scan Findings | Typed audit events (`compact_auto_start/end`, `compact_micro_start/end`, `compact_failed`) so telemetry no longer depends on substring matching; `build_telemetry.py` must consume them | NEW_BLOCK_IMPLEMENT_NOW |
| DS3-S18 | THIRD_DEEP_SCAN §Consolidated Scan Findings | Failure-signature tracking across tool errors and turns with status evidence and tests | NEW_BLOCK_IMPLEMENT_NOW |
| PS3-1 | PS_CODEX §Non-Negotiable Product Requirements | Long-running work must survive compaction (telemetry must prove typed compaction occurred) | Mandatory |
| PS3-6 | PS_CODEX §Non-Negotiable Product Requirements | Token/cost/cache telemetry must include parent + subagent attribution | Mandatory |

Worker mapping into 4 ledger rows (1↔DS3-S10/PS3-1, 2↔DS3-S10/PS3-6, 3↔DS3-S18, 4↔DS3-S9) is correct and exhaustive.

## Disposition Counts (verified)

```
EXPECTED ROW COUNT: 4
LEDGER ROW COUNT: 4
DISPOSITION COUNTS:
- SHIPPED: 3
- PARTIAL: 0
- MISSING: 0
- DEFERRED_USER_APPROVED: 0
- DROPPED_USER_APPROVED: 0
- N/A_CONSTRAINT: 1
```

## ROW REVIEW

| row_id | verdict | evidence judgment |
|---|---|---|
| SOFTWARE-COMPACT-TELEMETRY-1 | APPROVE | Code: `query_engine.py:705,727,741,751,911,928,948,961,969` emits typed start/end/skipped/failed events for both microcompact and auto-compact paths. Test: `test_software_compact_telemetry.py::test_microcompact_emits_typed_audit_events` and `::test_auto_compact_emits_typed_start_and_end` (3 passed). DECISIONS.md documents intent. PORT_LOG/DECISIONS evidence present. |
| SOFTWARE-COMPACT-TELEMETRY-2 | APPROVE | Code: `build_telemetry.py:49-54` adds `failure_loop_events` to required keys; `:233-263` typed-vs-legacy compaction extraction with `typed` flag; `:281-305` failure-loop extraction; `:315-322` cache trend; `:325-377` parent/subagent/reviewer attribution. Test: `test_build_telemetry.py` 8 passed including typed/legacy compaction, agent attribution split, cache trend math (0.3333 from `500/(500+0+1000)`). |
| SOFTWARE-COMPACT-TELEMETRY-3 | APPROVE | Code: `query_engine.py:1304-1326` blocks third identical failed call; `:1564-1590` records typed `tool_failure_recorded`/`tool_failure_loop_warning`. Test: `test_repeated_tool_failure_loop_is_audited_and_blocked` verifies third call blocked, `previous_failures==2`, two `tool_failure_recorded` events emitted. Persists across `engine.run()` calls on the same instance via `self._tool_failure_counts`. |
| SOFTWARE-COMPACT-TELEMETRY-4 | NEEDS_FIX (non-blocking) | DS3-S9 is classified `TEST_HARDENING_ONLY` in the canonical source, which explicitly authorizes "Add command OR explicit no-goal decision; at minimum add tests/docs for manual compaction trigger." Worker chose no-goal + test hardening. Decision is documented in `DECISIONS.md`. However the disposition `N/A_CONSTRAINT` is the wrong taxonomy slot — `03_LEDGER_SCHEMA.md` reserves `N/A_CONSTRAINT` for *hard* constraints (e.g., model/SageMaker incapability). The substantive evidence is satisfied; only the label is mislabeled. Non-blocking. |

## FINDINGS (severity ordered)

- **LOW SOFTWARE-COMPACT-TELEMETRY-4 disposition label**: row 4 is labeled `N/A_CONSTRAINT` but per master protocol the proper taxonomy is either `SHIPPED` (the test-hardening branch was satisfied with `test_software_compact_telemetry.py` covering forced micro/auto compaction) or `DROPPED_USER_APPROVED` (with explicit user approval citation for not adding `/compact`). The action_needed field already requests Claude confirmation; recommend re-disposition to `SHIPPED` with the test-hardening rationale, *or* leave as-is with an inline note that the third-deep-scan classification authorizes the no-goal/test-hardening branch. Not ship-blocking.
- **LOW `compact_auto_start.max_context_tokens` redaction**: `query_engine.py:914` sets `max_context_tokens` in the `compact_auto_start` parameters. The audit sanitizer (`runtime/audit.py:54-57,123-132`) redacts any key whose lowercased name contains `"token"`, so this value is written to disk as `"[REDACTED]"`. `DECISIONS.md` explicitly states the design goal of "neutral audit parameter names such as `saved_count`, `before_count`, `after_count` so the existing audit sanitizer does not redact token-count telemetry as a secret" — but the same renaming was not applied here. R-tier inspection of the actual context-window value (≈200000) is therefore lost. Tests do not assert on this field so they still pass. Recommend renaming to `max_context_count` (or similar) to match the documented decision. Not ship-blocking.
- **INFO failure-loop persistence is process-local**: `_tool_failure_counts` is per-`QueryEngine` instance only, so a fresh process or fresh engine instance starts with an empty counter. Worker self-review acknowledges this and defers full restart-persistence to SOFTWARE-GATE. Acceptable for this block.
- **INFO cache-hit denominator interpretation**: `build_telemetry._aggregate_per_turn` defines `denom = cache_read + cache_write + tokens_in`, treating Bedrock's `input_tokens` as the non-cached portion. This matches Bedrock's billing model (input_tokens excludes cache reads), so 500/(500+0+1000)=0.333 is correct. Confirmed by `test_build_telemetry_captures_thinking_when_audit_emits_chat_response`. Documented for R-tier evidence reviewers.

## DISPUTED FINDINGS

NONE: no worker dispute received in this iteration.

## REMAINING SHIP-BLOCKING ROWS

0

## VERDICT

```
VERDICT: APPROVE_WITH_FIXES
SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW
```

## Required Fixes Before Commit/Push

Both items are NON-BLOCKING (LOW). Worker may close on the existing artifacts. Recommended cleanup before the close commit:

1. **Re-disposition row 4** in `LEDGER.md` from `N/A_CONSTRAINT` to `SHIPPED` (with action_needed cleared and `disposition_rationale` referencing the third-deep-scan TEST_HARDENING_ONLY classification + the focused tests in `test_software_compact_telemetry.py`). This aligns the label with the master protocol's disposition taxonomy.
2. **Rename `max_context_tokens` → `max_context_count`** (or equivalent neutral name) in `query_engine.py:914` so the typed `compact_auto_start` event survives the audit sanitizer intact, matching the explicit goal in `DECISIONS.md`. Then rerun `test_software_compact_telemetry.py` and `test_build_telemetry.py` to confirm no regression and update the focused log.

After applying fixes (or accepting them as non-blocking), proceed with the specific-file close commit + push to `sageagent/v5-build` per the established checkpoint policy. Do not run AWS/R-tier spend without separate explicit user approval.

---

**End of review.** Block is substantively complete: typed compaction telemetry is in place, build_telemetry.py consumes it, repeated-failure looping is audited and blocked at the third identical fail, tests pass (3 + 8 + 4 regression), and both scope audits remain clean (`TOTAL_SHIP_BLOCKING_ROWS: 0`). Two LOW labeling/cleanup items remain.
