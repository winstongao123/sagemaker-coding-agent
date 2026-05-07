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
`AGENT_STATUS.md`, run tests, save logs/reviews, and produce an exact
`mini_research_worklog_result.zip`.

Model/region/cap:

- Model: `au.anthropic.claude-haiku-4-5-20251001-v1:0`
- Region: `ap-southeast-2`
- Per-run cap: `$5.00`

## Results

| Area | v4 fresh run | v5 fresh run after first fixes |
|---|---:|---:|
| Target workspace respected | FAIL: 0/19 required paths in target workspace | PASS: 19/19 required paths present |
| Software package built | FAIL | PASS |
| Tests | FAIL: no tests dir in target workspace | PARTIAL: latest rerun had 123/127 passing |
| Exact `.zip` artifact | FAIL: none | PASS in latest rerun |
| Subagent evidence | FAIL: none | PASS: `docs/reviews/20260507T152935Z-plan-429d3b6faf16.md` |
| Logs | FAIL: none | PASS: `docs/logs/subagent_artifacts.log` |
| Status file | FAIL in target workspace | PARTIAL: present, but still claimed complete with failing tests and one missing required doc |
| Stop reason | Incomplete/wrong workspace | PASS: `end_turn` |
| API calls | 93 | 104 |
| Cost | `$0.7796` | `$1.5409` |
| Cache telemetry | limited v4 session stats | PASS: cache read/write and subagent cost recorded |
| Acceptance verdict | FAIL | FAIL, but much closer and with evidence |

## What This Proves

v5 is clearly stronger than v4 on the same task:

- v4 drifted out of the requested workspace and left the target workspace empty.
- v5 built the requested software package in the correct workspace.
- v5 used a subagent and saved the subagent artifact.
- v5 recorded cache, cost, parent/subagent metrics.
- v5 reached a clean `end_turn` after the max-turn/status guard and prompt-rule fixes.

## What Still Failed

The latest v5 run is not a clean acceptance pass:

1. It reported completion with four failing tests.
2. It produced the exact requested `.zip`, but missed `docs/DESIGN.md`.
3. `AGENT_STATUS.md` still used a completion tone despite failing tests and
   unchecked original plan rows.

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

> v5 could still claim done when the external harness saw a failing test or exact
> artifact mismatch. A deterministic final-claim guard has now been added and
> lock-tested to prevent that class of false finish.

After the Runnable source scan, the final-claim guard was strengthened again:

- exact required path extraction from the user prompt
- unchecked `AGENT_STATUS.md` checklist detection
- bounded final `python -m pytest tests -q` probe before accepting strong
  `all tests pass` / `production-ready` claims

Detailed source-level comparison:

- `Critical_RUNNABLE_LESSONS_FOR_FINAL_GUARD.md`

Before calling v5 "98% ready" for autonomous long-running coding, run one more
fresh acceptance pass after this strengthened final-claim guard. The next acceptance run should
require:

- exact required paths all present
- exact archive type present and valid
- external pytest pass
- `AGENT_STATUS.md` final state aligned with real evidence
- saved subagent/reviewer artifact
- no final answer claiming green while any gate is red

## Evidence Files

- `logs/v4-summary.json`
- `logs/v4-agent-output.log`
- `logs/v4-pytest.log`
- `logs/v5-summary.json`
- `logs/v5-agent-output.log`
- `logs/v5-pytest.log`
- v5 workspace: `D:\Github\sageagent_psps_v4_fresh_workspaces\v5`
- v4 target workspace: `D:\Github\sageagent_psps_v4_fresh_workspaces\v4`
