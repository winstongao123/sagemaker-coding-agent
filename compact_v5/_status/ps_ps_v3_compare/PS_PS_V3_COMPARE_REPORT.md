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

## Results

| Dimension | v5 Haiku | v4 Haiku | What it means |
|---|---:|---:|---|
| Local cost recorded | `$0.9378 / $5.00` | `$0.3934 / $5.00` | Both stayed under cap. v5 spent more because it actually built/tested the package and ran a verify subagent. |
| API calls | `85` | `62` | v5 did a complete long task. v4 spent many turns but lost workspace control. |
| Required live files present | `17 / 18` | `0 / 18` in intended workspace | v5 produced the project in the right workspace. v4 wrote into the repo root instead of the requested workspace. |
| Tests | `62 passed` | no tests dir in intended workspace | v5 produced runnable code and tests. v4 did not finish in the correct workspace. |
| Zip | valid, `27` members, `45,501` bytes | no zip in intended workspace | v5 fixed the v1 zip failure class. v4 did not package correctly. |
| Subagent/reviewer telemetry | verify subagent used; `$0.1809`, cache R/W tracked | no saved comparable reviewer artifact in intended workspace | v5 records subagent cost/cache attribution. |
| Cache telemetry | read `2,850,417`, write `273,670` tokens | cache lines appear in log, but less structured | v5 has structured cache/read/write stats usable by UI and logs. |
| Workspace safety | wrote under intended external workspace | wrote `mini_release_auditor/`, `tests/`, `pyproject.toml`, and modified repo `README.md` | v4 reproduced a serious PS problem: workspace drift and repo pollution. |
| Remaining gap | `docs/reviews/` missing despite verify subagent | large failure | v5 is much better, but v3 prompt must hard-require saving each subagent result immediately. |

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
3. v5 can complete the long coding task on Haiku when the workspace is safe:
   62 tests passed and the zip validated.
4. v5 still needs stricter acceptance wording around saved subagent review
   artifacts. The verify subagent ran and was costed, but `docs/reviews/` was not
   created. v3 now makes this a hard no-done condition.
5. v4 is not safe enough for this acceptance style: it wrote to the repo root
   instead of the requested workspace and modified `README.md`. That pollution was
   removed after the run.

## Explain It Like You Are 9

v5 built the little software project in the right sandbox, tested it, made a real
zip, and showed how much the main agent and helper agent cost.

v4 got confused about which desk it was working on. It started putting homework
on the wrong desk, then said it was fixed. That is exactly why v5 needed stronger
workspace/status/review gates.

v5 still forgot to put the helper's written review into the `docs/reviews/`
folder, so the v3 test says: "after a helper talks, save what it said right away,
or you are not done."
