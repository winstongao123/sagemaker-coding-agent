# Critical PS/PS Fresh V4 vs V5 Comparison Report

Date: 2026-05-08

## Short Verdict

v5 is clearly stronger than v4 on the same Haiku coding benchmark, but the latest
fresh v5 run still exposed a critical false-finish risk. The runtime has now been
hardened again, and a fresh acceptance run is required before claiming final
production readiness.

## Side-By-Side

| Check | v4 Fresh Run | v5 Fresh Run | What It Means |
|---|---|---|---|
| Workspace discipline | Failed: target workspace was empty | Passed: 18/19 then 19/19 package files depending on run, but one exact doc was missed in latest run | v5 understands the task far better, but exact required paths still needed a stronger guard. |
| Software package | Failed | Passed: real package modules were built | v5 is much better at actual coding work. |
| Tests | Failed/no target tests | Failed latest external pytest: `4 failed, 123 passed` | v5 can create tests, but final truth must be checked mechanically. |
| Exact zip | Failed/no zip | Passed latest run: valid `.zip` was created | The earlier `.tar.gz` substitution class is fixed for this run. |
| Subagent/reviewer evidence | Failed | Passed: saved `docs/reviews/...plan...md` | v5 can use and preserve subagent evidence. |
| Metrics | Limited | Passed: parent/subagent cache/cost/token metrics recorded | v5 is stronger for cost and cache visibility. |
| Final honesty | Failed by omission | Failed latest run: final answer said production-ready despite failing tests | This is the remaining critical class fixed by the new final-claim guard. |

## Runnable Lessons Applied

The Runnable source scan found relevant hardening patterns:

- sidechain subagent transcripts are kept separate from main transcripts
- resume consistency is measured, not guessed
- max-turn is a visible error state
- background output has durable output-file paths and size watchdogs
- verification is nudged at task close, not left to prose
- ZIP creation uses a deterministic archive path and atomic write
- cost/cache/subagent metrics are first-class

Detailed source citations are in:

- `compact_v5/_status/ps_ps_v4_fresh_compare/Critical_RUNNABLE_LESSONS_FOR_FINAL_GUARD.md`

## v5 Fix Added After This Report

`core/query_engine.py` final-claim guard now:

- catches unchecked `AGENT_STATUS.md` checklist rows
- extracts exact required paths from the user prompt and blocks final success if any
  are missing
- runs a bounded local `python -m pytest tests -q` probe before accepting strong
  claims like `all tests pass`, `project complete`, or `production-ready`
- writes probe output to `.sageagent_state/final_claim_pytest.log`

Lock tests:

- `test_final_claim_guard_rejects_stale_status_and_missing_zip`
- `test_final_claim_guard_checks_required_paths_and_unchecked_status`
- `test_final_claim_guard_runs_pytest_before_accepting_test_claim`

## Honest Next Step

Run one more fresh v5 acceptance test after this patch. If it passes with:

- exact paths present
- exact zip valid
- external pytest green
- `AGENT_STATUS.md` aligned with evidence
- saved subagent/reviewer evidence
- no false final claim

then v5 has strong evidence for the user's long-running software engineering workflow.
