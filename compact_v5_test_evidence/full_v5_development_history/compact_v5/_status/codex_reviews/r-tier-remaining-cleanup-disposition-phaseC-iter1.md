# Phase C Reviewer Verdict — REJECT

The disposition rows **do not pass** the local gate as currently configured. Two blocking gaps reproduce on every one of the 14 rows under review.

## Findings against required checks

**Check 1 — matrix `status: DISPOSITION_OK` with original `kind`/model/cap preserved:** PASS. All 14 rows in `r_tier_test_matrix.json` carry `status: "DISPOSITION_OK"` while keeping `kind: "real"`, original model, and original `cost_cap_usd`.

**Check 2 — no fake `aws-call`/`local-call` evidence:** PASS. File listing for the 14 rows shows only `phaseA-iter1-prompt.txt`, `phaseA-iter1.md`, and `disposition-iter1.md`. No `*-aws-call*.log` or `*-local-call*.log` files were synthesized.

**Check 3 — per-test phaseA prompt/review alias, disposition note, zero-cost metrics row, review-log row:** **FAIL on two sub-items**.
- ✅ Phase A prompts present (UTF-8 readable).
- ❌ **Phase A review files are UTF-16 LE** (BOM `ff fe`, e.g. `r-tier-R9-phaseA-iter1.md`). The gate's `_read_text` opens them as UTF-8, yielding text with NUL bytes between every character, so `_phase_a_latest_decision_is_approval` cannot match the substring `APPROVE_DISPOSITION_PLAN`. Every row therefore fails: `latest phase A decision does not approve AWS call`.
- ✅ Disposition notes present and content-clean.
- ✅ Zero-cost metrics rows present with `verdict=DISPOSITION_OK`, `cost_usd=0` (lines 32–45 of `r_tier_metrics.jsonl`).
- ✅ Review-log rows present with `DISPOSITION_OK` final tag.
- ❌ **Phase C iter files do not exist on disk** for any of the 14 rows. The review log advertises `r-tier-{test_id}-phaseC-iter1.md` as evidence (rows 35–48), but `ls compact_v5/_status/codex_reviews/ | grep phaseC` for those IDs returns nothing. Gate raises `missing phase C post-pass review` for every row.

**Check 4 — three local locks present and passing:** PASS. `tests/integration/test_r_tier_disposition_locks.py` runs green:
- `test_r18_e4_skill_activation_is_canonical_name_not_alias` PASSED
- `test_r18_e11_subagent_timeout_survives_parent_compaction_and_resume` PASSED
- `test_r18_e13_unicode_rtl_memory_round_trips_through_dream` PASSED

**Check 5 — gate change is honest:** PASS in design (disposition keyed off matrix `status`, requires `disposition-iter*.md` in lieu of raw call log, skips telemetry/quality only when `is_disposition`, telemetry sanity loop returns early at line 418, cost ceiling unchanged because cap is keyed off `cost_usd`). The matrix-cap total is still enforced at $14.25, prior diagnostic spend is not reset, and disposition rows contribute $0 without erasing earlier rows.

**Check 6 — direct verification:** **All 14 rows fail `r_tier_gate.py --test <row>`** with the same two errors:
```
{test}: missing phase C post-pass review in ...\codex_reviews
{test}: latest phase A decision does not approve AWS call
```

## Why this is a REJECT, not a small nit

The prior reviewer's gate spec explicitly warned: *"Without this change, every DISPOSITION_OK row above would either (a) fail the default gate ... or (b) be forced through by writing fake files — exactly the failure mode the user is asking the reviewer to block."* The current state lands in (a): every disposition row fails the default gate. The matrix and review log advertise these rows as `DISPOSITION_OK`/`READY-equivalent`, but the gate disagrees. That is the same drift the user is asking the reviewer to block — paperwork claims completion while the mechanical gate says incomplete.

## Required fixes before re-review (no AWS spend needed)

1. Re-encode all 14 `r-tier-{R9,R10,R12,R18-E1,R18-E3,R18-E4,R18-E6,R18-E8,R18-E10,R18-E11,R18-E13,R18-E14,R18-E15,R19-U8}-phaseA-iter1.md` files as UTF-8 (or change `_read_text` to detect/handle UTF-16 BOM) so `APPROVE_DISPOSITION_PLAN` is detectable.
2. Create the 14 missing `r-tier-{test_id}-phaseC-iter1.md` files containing `POST-PASS VERDICT: DISPOSITION_OK` and the per-row rationale (matching the pattern the lock test `test_r_tier_gate_accepts_reviewed_disposition_without_fake_call` validates).
3. Re-run `python compact_v5/_status/scripts/r_tier_gate.py --repo-root . --test <row>` for each of the 14 IDs and confirm exit 0.

The local locks, matrix edits, disposition notes, metrics rows, review-log rows, and gate logic are all correct. Only the encoding of the phase A reviews and the missing phase C files block acceptance.

**REJECT**
