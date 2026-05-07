You are running a fresh side-by-side software-engineering benchmark.

Workspace: D:\Github\sageagent_psps_v4_fresh_workspaces\v4

Use the Haiku model already configured by the harness. Do not spend more than
$5.00. If cost approaches the cap, stop after saving status and evidence.

Goal: build a small but real Python package named `mini_research_worklog`.

This is not only a coding task. It must prove research, review, long-task state,
tool discipline, packaging, and evidence capture.

Required tree:

- `mini_research_worklog/__init__.py`
- `mini_research_worklog/models.py`
- `mini_research_worklog/store.py`
- `mini_research_worklog/search.py`
- `mini_research_worklog/report.py`
- `mini_research_worklog/cli.py`
- `tests/test_models.py`
- `tests/test_store.py`
- `tests/test_search.py`
- `tests/test_cli.py`
- `docs/DESIGN.md`
- `docs/RESEARCH.md`
- `docs/TEST_REPORT.md`
- `docs/REVIEW.md`
- `docs/logs/`
- `docs/reviews/`
- `AGENT_STATUS.md`
- `README.md`
- `pyproject.toml`

Research requirement:

Before implementation, inspect these v5 files if present:

- `D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tools/task.py`
- `D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/query_engine.py`
- `D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/core/compactor.py`
- `D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/runtime/tokens.py`

Write `docs/RESEARCH.md` explaining, in your own words:

- what you learned about subagent evidence,
- what you learned about tool/cost/cache metrics,
- how you will avoid repeated failed commands,
- how you will keep state resumable.

Process requirements:

0. Your first tool-based phase MUST try to use a real `task` tool call with
   `subagent_type` set to `plan`, `explore`, `review`, or `verify`.
   If available, save the returned subagent artifact/envelope path under
   `docs/reviews/`. If unavailable, write `docs/reviews/subagent_unavailable.md`
   with the exact error. A self-written review is not a substitute when the tool
   is available.
1. Keep `AGENT_STATUS.md` current with goal, plan, completed work, next 3 todos,
   blockers, cost checkpoints, and review state.
2. Use todo state if available and keep it consistent with `AGENT_STATUS.md`.
3. Save worker/reviewer/subagent output under `docs/reviews/`.
4. Save command/test/zip summaries under `docs/logs/` and summarize them in
   `docs/TEST_REPORT.md`.
5. Run targeted tests first, then full tests.
6. Do not repeat the same failed command more than twice without changing
   approach. If one failure repeats 3 times, stop and write `ESCALATION.md`.
7. Before final answer, verify every required live file exists in `D:\Github\sageagent_psps_v4_fresh_workspaces\v4`.
8. Create `mini_research_worklog_result.zip` with Python `zipfile`, then validate
   it with `ZipFile(...).testzip()` and save the validation output.
9. Before final answer, update `AGENT_STATUS.md` so nothing says packaging,
   review, cost, context, verify, or done is pending.
10. Final answer must include a SPEC vs SHIPPED table and exact evidence paths.

Implementation requirements:

- Python standard library only.
- Use dataclasses.
- JSON writes must be atomic: write a temp file next to the target, flush it,
  then replace the target.
- Worklog items include id, title, researcher, status, topic, tags, created,
  updated, confidence, and notes.
- CLI commands: `add`, `list`, `show`, `update`, `close`, `reopen`, `search`,
  `report`.
- Search/filter/sort must support status, researcher, topic, tag, confidence,
  free text, and updated-desc ordering.
- Markdown report must include counts by status/researcher/topic, high-confidence
  open items, and stale open items.
- Tests must cover empty store, invalid JSON, duplicate id prevention, status
  transitions, atomic write temp cleanup, search filters, CLI happy path, CLI
  error path, report generation, and zip validation helper behavior.

Do not claim done until saved evidence proves the package works.
