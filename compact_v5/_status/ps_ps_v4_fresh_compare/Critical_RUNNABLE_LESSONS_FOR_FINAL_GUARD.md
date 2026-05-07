# Critical Runnable Lessons For Final Guard

Date: 2026-05-08

## Why This Exists

The fresh v4/v5 acceptance comparison found that v5 was much stronger than v4, but
still had one serious product-risk class: it could write a confident final summary
while external evidence still showed a missing exact file or failing tests.

Runnable Claude Code has several source-level patterns that are relevant to this
problem. The lesson is simple: for long-running coding work, trust durable evidence
and mechanical checks more than the model's final prose.

## Runnable Source Patterns Checked

| Area | Runnable Source Evidence | Lesson For v5 |
|---|---|---|
| Subagent transcript separation | `src/utils/sessionStorage.ts:1200-1207`, `1224-1260` writes sidechain agent messages to agent transcript paths and avoids deduping them against the main transcript. | v5 must keep subagent/reviewer artifacts separate and durable, then reference those paths in parent status/review docs. |
| Resume consistency telemetry | `src/utils/sessionStorage.ts:2208-2243` emits a resume consistency delta comparing expected vs reconstructed chain position. | v5 should treat resume/status drift as a measurable bug class, not as a narrative issue. |
| Compact resume safety | `src/utils/sessionStorage.ts:1888-1902`, `1920-1938` avoids pruning when compact relink is broken and zeros stale usage after compaction. | v5's compact/resume state must preserve enough truthful status and avoid stale usage causing immediate compact loops. |
| Large transcript loading | `src/utils/sessionStoragePortable.ts:699-784` handles compact boundaries and crash-truncated carry data while loading large transcripts. | v5 should favor bounded, resume-safe readers for long sessions rather than assuming small happy-path logs. |
| Background output durability | `src/utils/ShellCommand.ts:13-30`, `52-55`, `106-113`, `306-315` records large output paths, output task ids, and uses a size watchdog. | v5 should surface long command output paths and avoid losing evidence behind abbreviated inline text. |
| Verification nudge | `src/tools/TodoWriteTool/TodoWriteTool.ts:72-108` and `TaskUpdateTool.ts:396-398` add a model-visible reminder when work closes without verification. | v5 should inject final corrections at the loop-exit moment, not rely only on static prompt rules. |
| Exact ZIP handling | `src/utils/plugins/zipCache.ts:171-201`, `207-228`, `366-378` creates ZIP bytes and writes them atomically; `pluginLoader.ts:826-831` path-validates before moving plugin subdirs. | v5 should require exact requested artifact types and prefer deterministic archive helpers over model-chosen substitutes like `.tar.gz`. |
| Cost/cache visibility | `src/cost-tracker.ts:261-314`, `src/utils/forkedAgent.ts:607-669`, and `src/bootstrap/state.ts:769-779` record cache read/write, subagent/fork usage, and post-compaction state. | v5 UI and `/cost` should keep parent/subagent/cache attribution visible, especially after compaction. |

## v5 Hardening Added From This Scan

`compact_v5/MAIN/agent/core/query_engine.py` now has a stronger final-claim guard:

- Rejects final success claims when `AGENT_STATUS.md` still has unchecked checklist
  items.
- Extracts exact requested paths from the user's prompt and rejects final success
  if any are missing.
- Runs a bounded local `python -m pytest tests -q` probe when a Python project
  claims `all tests pass`, `project complete`, or `production-ready`.
- Saves that probe to `.sageagent_state/final_claim_pytest.log` if it runs.

Lock tests:

- `test_final_claim_guard_rejects_stale_status_and_missing_zip`
- `test_final_claim_guard_checks_required_paths_and_unchecked_status`
- `test_final_claim_guard_runs_pytest_before_accepting_test_claim`

## Current Honest Status

This closes the specific false-finish class found in the latest fresh v5 run:

- Missing `docs/DESIGN.md` would now be caught as a required path mismatch.
- Unchecked `AGENT_STATUS.md` plan rows would now be caught.
- External pytest failures would now be caught before accepting a strong final
  completion claim.

Production confidence still requires a fresh acceptance run after this patch, because
the previous v5 run was correctly recorded as `acceptance_pass: false`.
