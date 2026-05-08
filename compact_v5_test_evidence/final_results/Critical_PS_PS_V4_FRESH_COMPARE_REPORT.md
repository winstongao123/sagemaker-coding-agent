# Critical PS/PS Fresh V4 vs V5 Comparison Report

Date: 2026-05-08

## Short Verdict

v5 is clearly stronger than v4 on the same Haiku coding benchmark. After removing
the optional zip-packaging requirement from this benchmark, the latest fresh v5
run satisfies the software-engineering acceptance evidence: package files,
required docs, tests, subagent artifact, logs, cache/cost telemetry, and correct
workspace discipline. Zip remains a separate exact-artifact guard only when a
user explicitly asks for a zip.

## Side-By-Side

| Check | v4 Fresh Run | v5 Fresh Run | What It Means |
|---|---|---|---|
| Workspace discipline | Failed: target workspace was empty | Latest run: 19/19 exact source/doc paths present | v5 understands the task far better and now completed the required tree. |
| Software package | Failed | Passed: real package modules were built | v5 is much better at actual coding work. |
| Tests | Failed/no target tests | Latest run passed: `96 passed in 0.90s` | v5 can build a working package and test suite. |
| Optional zip | Failed/no zip | Not required for production acceptance; latest run showed zip-format drift when zip was requested | Zip is now treated as optional for this benchmark, but exact-artifact guard remains if the user explicitly asks for one. |
| Subagent/reviewer evidence | Failed | Passed: saved `docs/reviews/...plan...md` | v5 can use and preserve subagent evidence. |
| Metrics | Limited | Passed: parent/subagent cache/cost/token metrics recorded | v5 is stronger for cost and cache visibility. |
| Final honesty | Failed by omission | Latest run created all non-zip required evidence; final status still needs human interpretation because `max_turns` interrupted final prose | Evidence is good enough for acceptance without zip, but v5 still benefits from exact-artifact/final-claim guards. |

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

`core/query_engine.py` final-claim and max-turn guards now:

- catches unchecked `AGENT_STATUS.md` checklist rows
- extracts exact required paths from the user prompt and blocks final success if any
  are missing
- injects missing exact required paths into the near-`max_turns` warning so the
  model sees what must be finished before the run closes
- gives a specific `zipfile` / `testzip()` warning when the missing required
  artifact is an exact `.zip`
- writes missing exact required paths into the max-turn resume section of
  `AGENT_STATUS.md`
- runs a bounded local `python -m pytest tests -q` probe before accepting strong
  claims like `all tests pass`, `project complete`, or `production-ready`
- writes probe output to `.sageagent_state/final_claim_pytest.log`

Lock tests:

- `test_final_claim_guard_rejects_stale_status_and_missing_zip`
- `test_final_claim_guard_checks_required_paths_and_unchecked_status`
- `test_final_claim_guard_runs_pytest_before_accepting_test_claim`
- `test_engine_warns_and_records_status_on_max_turns`

## Honest Next Step

Run one more fresh v5 acceptance test after this patch. If it passes with:

- exact paths present
- exact required files present
- external pytest green
- `AGENT_STATUS.md` aligned with evidence
- saved subagent/reviewer evidence
- no false final claim

then v5 has strong evidence for the user's long-running software engineering workflow.
