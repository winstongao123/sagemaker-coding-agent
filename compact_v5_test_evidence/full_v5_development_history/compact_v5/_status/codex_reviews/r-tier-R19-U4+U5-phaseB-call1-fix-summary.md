# Stage 6 R19-U4+U5 Phase B Call1 Fix Summary

Date: 2026-05-05T18:08:00Z

## Classification

`TEST_DESIGN_FIX_REQUIRED`

Call1 is preserved as diagnostic/non-ready spend. Do not delete, reset, or hide
its raw log, side metrics, telemetry, audit logs, or cost.

## Call1 Evidence

- Raw log:
  `compact_v5/_status/codex_reviews/r-tier-R19-U4+U5-aws-call1.log`
- U4 side metrics:
  `compact_v5/_status/r-tier-R19-U4-aws-call1-side-metrics.json`
- U5 side metrics:
  `compact_v5/_status/r-tier-R19-U5-aws-call1-side-metrics.json`
- U4 telemetry:
  `compact_v5/_status/r-tier-R19-U4-aws-call1-telemetry.json`
- U5 telemetry:
  `compact_v5/_status/r-tier-R19-U5-aws-call1-telemetry.json`
- U4 audit:
  `compact_v5/_status/r_tier_runtime/R19-U4-call1-audit`
- U5 audit:
  `compact_v5/_status/r_tier_runtime/R19-U5-call1-audit`

## What Happened

The Stage 6 AWS invocation ran the approved Haiku 4.5 AU bundle for R19-U4 and
R19-U5 only. R3 was not rerun; existing R3 READY evidence remains reused.

R19-U4 completed successfully:

- exactly two `task` dispatches;
- conflict between Alpha SHIP and Beta ROLLBACK was reconciled using
  `source_of_truth.json`;
- final decision was ROLLBACK because `12.0 > 2.0`;
- cost `$0.0529`, under the `$0.48` buffered ceiling;
- `process_quality_ok=true`;
- no guard failure loop.

R19-U5 produced a correct artifact but the bundle failed because `_u5_ready`
required the exact substring `failure`. The artifact used "Failed Probes",
`FILE NOT FOUND`, and "Single attempt made; no retry per instructions" to
record the missing child. It used both successful child findings and concluded
`CONTINUE_WITH_PARTIAL_EVIDENCE`.

R19-U5 call1 metrics:

- exactly three `task` dispatches;
- cost `$0.0366`, under the `$0.36` buffered ceiling;
- `process_quality_ok=true`;
- one expected missing-file read failure inside the missing child;
- no repeated guard failure loop;
- no repeated exec recovery loop;
- stop reason `end_turn`;
- runner verdict `FAIL` only because of the narrow artifact predicate.

## Fix

Updated `compact_v5/MAIN/agent/tests/r_tier/test_r19_u4_u5_subagent_recovery_bundle.py`:

- `_u5_ready` now accepts explicit missing-child failure evidence expressed as
  `failure`, `failed`, or `file not found`.
- It still requires `missing`, `checkout`, `inventory`, and
  `continue_with_partial_evidence`.
- Added zero-cost lock tests:
  - `test_u5_ready_accepts_failed_probe_artifact_wording`
  - `test_u5_ready_rejects_summary_without_missing_child_failure`

## Local Validation

Command:

```powershell
$env:PYTHONPATH=(Resolve-Path compact_v5/MAIN/agent).Path
py -3.11 -m pytest compact_v5/MAIN/agent/tests/r_tier/test_r19_u4_u5_subagent_recovery_bundle.py -q
```

Result:

```text
2 passed, 1 skipped
```

Also compiled:

```powershell
py -3.11 -m py_compile compact_v5/MAIN/agent/tests/r_tier/test_r19_u4_u5_subagent_recovery_bundle.py
```

## Retry Request

Request Claude Phase B approval for one retry of the same Stage 6 bundle:

- Runner:
  `compact_v5/MAIN/agent/tests/r_tier/test_r19_u4_u5_subagent_recovery_bundle.py`
- Model: Haiku 4.5 AU,
  `au.anthropic.claude-haiku-4-5-20251001-v1:0`
- Invocation: R19-U4 + R19-U5 only.
- R3: do not rerun; reuse existing READY evidence.
- Planned bundle target: `$0.70`.
- Buffered hard ceiling: `$0.84`, excluding R3.
- Call1 diagnostic spend to preserve:
  - R19-U4: `$0.0529`
  - R19-U5: `$0.0366`

The retry is expected to remain under cap because call1 used `$0.0895` total
for both members, far below the `$0.84` hard ceiling, and no prompt/model scope
was expanded.

Stop the retry if:

- Claude rejects this Phase B fix/retry plan;
- AWS budget headroom is unhealthy;
- either member exceeds its per-test buffered ceiling;
- telemetry is missing;
- R14/R19-U3-style repeated guard or exec loops recur;
- U5 still fails artifact readiness after the predicate fix.
