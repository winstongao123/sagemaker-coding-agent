# PS_PS v3 Comparison Report

Date: 2026-05-07

Purpose: compare v4 and v5 on the same bounded Haiku software-engineering
benchmark, then use the result to prepare the human `PS_PS_FINAL_TEST_v3.md`.

## Benchmark

Model: `au.anthropic.claude-haiku-4-5-20251001-v1:0`

Region: `ap-southeast-2`

Cap: `$5.00` per agent run

Task: build `mini_release_auditor`, a small standard-library Python package with
dataclass models, atomic JSON storage, search/filter/sort, CLI, markdown report,
tests, docs, logs/reviews, current status, and a validated zip.

Prompt:

- `compact_v5/_status/ps_ps_v3_compare/benchmark_task_prompt.md`

Harness:

- `compact_v5/_status/ps_ps_v3_compare/run_agent_compare.py`

Workspaces:

- v5: `D:/Github/sageagent_psps_v3_compare_workspaces/v5`
- v4: `D:/Github/sageagent_psps_v3_compare_workspaces/v4`

## Final Results After v5 Fixes

| Dimension | v5 Haiku | v4 Haiku | What it means |
|---|---:|---:|---|
| Latest local cost recorded | `$0.7146 / $5.00` | `$0.3934 / $5.00` | Both stayed under cap. v5 spent more because it actually built/tested the package and ran a real subagent. |
| API calls | `55` | `62` | v5 completed the task with fewer calls than the original v4 comparison run. |
| Final stop reason | `end_turn` | incomplete/wrong workspace | The stricter v5 harness now rejects `fatal_error`; latest v5 ended cleanly. |
| Required live files present | `18 / 18` | `0 / 18` in intended workspace | v5 produced the project in the right workspace. v4 wrote into the repo root instead of the requested workspace. |
| Tests | `76 passed` | no tests dir in intended workspace | v5 produced runnable code and tests. v4 did not finish in the correct workspace. |
| Zip | valid, `58` members, `124,043` bytes | no zip in intended workspace | v5 fixed the v1 zip failure class and validated the output package. |
| Subagent/reviewer telemetry | plan subagent used; `$0.0500`, cache R/W tracked; artifact saved in `docs/reviews/` | no saved comparable reviewer artifact in intended workspace | v5 records subagent cost/cache attribution and leaves review evidence. |
| Cache telemetry | read `1,967,864`, write `159,492` tokens | cache lines appear in log, but less structured | v5 has structured cache/read/write stats usable by UI and logs. |
| Workspace safety | wrote under intended external workspace | wrote `mini_release_auditor/`, `tests/`, `pyproject.toml`, and modified repo `README.md` | v4 reproduced a serious PS problem: workspace drift and repo pollution. |
| Remaining gap | none in latest strict v5 run | large failure | The earlier v5 missing-review-artifact and Bedrock pairing failures were fixed and rerun. |

## Evidence Files

| Evidence | Path |
|---|---|
| v5 summary JSON | `compact_v5/_status/ps_ps_v3_compare/logs/v5-summary.json` |
| v5 agent output | `compact_v5/_status/ps_ps_v3_compare/logs/v5-agent-output.log` |
| v5 final answer | `compact_v5/_status/ps_ps_v3_compare/logs/v5-agent-final.txt` |
| v5 pytest log | `compact_v5/_status/ps_ps_v3_compare/logs/v5-pytest.log` |
| v5 result zip | `D:/Github/sageagent_psps_v3_compare_workspaces/v5/mini_release_auditor_result.zip` |
| v4 summary JSON | `compact_v5/_status/ps_ps_v3_compare/logs/v4-summary.json` |
| v4 agent output | `compact_v5/_status/ps_ps_v3_compare/logs/v4-agent-output.log` |
| v4 final answer | `compact_v5/_status/ps_ps_v3_compare/logs/v4-agent-final.txt` |

## What The Test Caught

1. The original benchmark workspace under `compact_v5/_status` was unsafe/noisy.
   The harness now uses `D:/Github/sageagent_psps_v3_compare_workspaces`.
2. The prompt must forbid shell `cd`, because both agents initially tried it and
   the bash policy blocks it.
3. v5 originally completed the code but missed saved `docs/reviews/` evidence.
   The `task` tool now persists review receipts automatically under both
   `.sageagent_state/subagents/` and `docs/reviews/`, and logs paths in
   `docs/logs/subagent_artifacts.log`.
4. v5 then exposed real long-session Bedrock pairing bugs after compaction:
   dangling, orphaned, and duplicate tool_result blocks. Runtime now repairs
   tool_use/tool_result pairs before compaction-summary calls and before every
   Bedrock chat call.
5. The harness was too lenient because it could pass a run that ended with
   `fatal_error` after artifacts were created. The harness now requires
   `stop_reason == "end_turn"`.
6. Latest v5 can complete the long coding task on Haiku when the workspace is safe:
   76 tests passed, `18/18` required files exist, the zip validates, a subagent was
   used, and final stop reason is `end_turn`.
7. v4 is not safe enough for this acceptance style: it wrote to the repo root
   instead of the requested workspace and modified `README.md`. That pollution was
   removed after the run.

## Explain It Like You Are 9

v5 built the little software project in the right sandbox, tested it, made a real
zip, saved the helper note, and showed how much the main agent and helper agent cost.

v4 got confused about which desk it was working on. It started putting homework
on the wrong desk, then said it was fixed. That is exactly why v5 needed stronger
workspace/status/review gates.

During fixing, v5 also showed us a backpack-packing bug: after compaction, one
tool receipt could be separated from the matching tool request. Bedrock refused
that. v5 now checks the backpack right before every model call and repairs the
tool receipts so the model sees a valid history.
