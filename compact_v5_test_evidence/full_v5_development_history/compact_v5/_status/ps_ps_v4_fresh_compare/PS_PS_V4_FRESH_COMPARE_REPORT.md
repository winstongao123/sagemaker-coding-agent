# PS/PS Fresh V4 vs V5 Comparison Report

Date: 2026-05-08

## Purpose

Compare v4 and v5 on the same Haiku, same `$5.00` cap benchmark for the user
priority areas:

- software coding ability
- tool discipline
- workspace/context/status management
- subagent coordination
- test/log/review evidence capture
- packaging accuracy

## Benchmark

Prompt: `benchmark_task_prompt.md`

Task: build `mini_research_worklog`, a small but real Python package that must
research v5 internals, use at least one subagent/reviewer artifact, keep
`AGENT_STATUS.md`, run tests, and save logs/reviews.

Model/region/cap:

- Model: `au.anthropic.claude-haiku-4-5-20251001-v1:0`
- Region: `ap-southeast-2`
- Per-run cap: `$5.00`

## Results

| Area | v4 fresh run | latest v5 fresh run after guard fixes |
|---|---:|---:|
| Target workspace respected | FAIL: 0/19 required paths in target workspace | PASS: 19/19 exact source/doc paths present |
| Software package built | FAIL | PASS |
| Tests | FAIL: no tests dir in target workspace | PASS: `96 passed in 0.90s` |
| Optional `.zip` artifact | FAIL: none | Not required for benchmark acceptance; latest zip attempt exposed artifact-format drift |
| Subagent evidence | FAIL: none | PASS: `docs/reviews/20260507T152935Z-plan-429d3b6faf16.md` |
| Logs | FAIL: none | PASS: `docs/logs/subagent_artifacts.log` |
| Status file | FAIL in target workspace | PASS for non-zip evidence; final prose was interrupted by `max_turns` |
| Stop reason | Incomplete/wrong workspace | PARTIAL: `max_turns` |
| API calls | 93 | 104 |
| Cost | `$0.7796` | `$1.1935` |
| Cache telemetry | limited v4 session stats | PASS: cache read/write and subagent cost recorded |
| Acceptance verdict | FAIL | FAIL, but much closer and with evidence |

## What This Proves

v5 is clearly stronger than v4 on the same task:

- v4 drifted out of the requested workspace and left the target workspace empty.
- v5 built the requested software package in the correct workspace.
- v5 used a subagent and saved the subagent artifact.
- v5 recorded cache, cost, parent/subagent metrics.
- v5 produced a fully passing local test suite and complete required source/doc
  tree with subagent evidence, logs, and metrics.

## What Still Failed

The latest v5 run is not a clean acceptance pass:

1. It passed its generated tests: `96 passed`.
2. It completed all exact required source/doc files.
3. It saved subagent evidence and logs.
4. It stopped by `max_turns`, so final prose was interrupted even though the
   non-zip evidence was complete.

These are important because the user's goal is not just "can write code"; the goal
is a long-running software engineering agent that does not drift from evidence.

## Fixes Applied During This Comparison

Runtime:

- `core/query_engine.py` now injects a model-visible turn-budget warning near
  `max_turns`.
- `core/query_engine.py` now appends a resume-safe section to `AGENT_STATUS.md`
  if `max_turns` interrupts a run.
- `core/query_engine.py` now has a final-claim guard: if the model tries to
  claim completion while local evidence still shows failing/partial tests,
  pending status, or a requested `.zip` artifact is missing, the engine feeds
  that contradiction back as a correction turn instead of ending.
- `core/query_engine.py` now includes missing exact requested paths in the
  near-`max_turns` warning and in the max-turn resume section of
  `AGENT_STATUS.md`.
- `core/query_engine.py` now gives a specific `zipfile` / `testzip()` instruction
  when the exact missing path is a `.zip`.

Prompt rules:

- `prompt/doing_tasks.md` now requires exact requested artifact paths and file
  types.
- `prompt/doing_tasks.md` now requires a required-file checklist before final
  answers.
- `prompt/doing_tasks.md` now forbids claiming completion while `AGENT_STATUS.md`
  still says tests, review, packaging, or status are pending.

Lock test:

- `tests/integration/test_query_engine.py::test_engine_warns_and_records_status_on_max_turns`
  covers the new max-turn warning and status-resume behavior.
- `tests/integration/test_query_engine.py::test_final_claim_guard_rejects_stale_status_and_missing_zip`
  covers the new final-claim guard.

## Current Honest Verdict

v5 is materially better than v4 for the user's target workflow, but the fresh
comparison found one remaining production-quality issue:

> v5 could still run out of turns after substituting `.tar.gz` for an exact
> requested `.zip`. The turn-budget warning and resume guard now list exact
> missing paths and add a concrete zipfile/testzip instruction for `.zip`
> artifacts.

After the Runnable source scan, the final-claim guard was strengthened again:

- exact required path extraction from the user prompt
- unchecked `AGENT_STATUS.md` checklist detection
- bounded final `python -m pytest tests -q` probe before accepting strong
  `all tests pass` / `production-ready` claims

Detailed source-level comparison:

- `Critical_RUNNABLE_LESSONS_FOR_FINAL_GUARD.md`

For the software-engineering benchmark without zip as a required deliverable, the
latest v5 run has the required evidence:

- exact required paths all present
- external pytest pass
- saved subagent/reviewer artifact
- logs and cache/cost/subagent metrics

## Evidence Files

- `logs/v4-summary.json`
- `logs/v4-agent-output.log`
- `logs/v4-pytest.log`
- `logs/v5-summary.json`
- `logs/v5-agent-output.log`
- `logs/v5-pytest.log`
- v5 workspace: `D:\Github\sageagent_psps_v4_fresh_workspaces\v5`
- v4 target workspace: `D:\Github\sageagent_psps_v4_fresh_workspaces\v4`
