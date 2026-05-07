You are running a bounded software-engineering acceptance benchmark.

Workspace: {{WORKSPACE}}

Use the Haiku model already configured by the harness. Do not spend more than
$5.00. If cost is close to the cap, stop and write the current status.

Command guidance:

- Do not use shell `cd`; the shell tool may block it. Use absolute paths or
  Python `os.chdir(r"{{WORKSPACE}}")` inside `python_exec`.
- Before claiming any file exists, verify it with a directory listing or Python
  `Path.exists()`.
- The final zip is not enough by itself; the live workspace must also contain
  the required source, tests, docs, logs, and review files.

Goal: build a small but real Python package named `mini_release_auditor`.

Required tree:

- `mini_release_auditor/__init__.py`
- `mini_release_auditor/models.py`
- `mini_release_auditor/store.py`
- `mini_release_auditor/search.py`
- `mini_release_auditor/report.py`
- `mini_release_auditor/cli.py`
- `tests/test_models.py`
- `tests/test_store.py`
- `tests/test_search.py`
- `tests/test_cli.py`
- `docs/DESIGN.md`
- `docs/TEST_REPORT.md`
- `docs/REVIEW.md`
- `docs/logs/`
- `docs/reviews/`
- `AGENT_STATUS.md`
- `README.md`
- `pyproject.toml`

Process requirements:

1. Keep `AGENT_STATUS.md` current with goal, plan, completed work, next 3 todos,
   blockers, cost checkpoints, and review state.
2. Use a todo list if available. Keep the todo state consistent with
   `AGENT_STATUS.md`.
3. Use at least one worker/explorer/reviewer subagent if the task tool is
   available. If not available, write `docs/reviews/subagent_unavailable.md`.
4. Save worker/reviewer outputs under `docs/reviews/`.
5. Save command summaries under `docs/logs/` and summarize them in
   `docs/TEST_REPORT.md`.
6. Run targeted tests first, then full tests.
7. Do not repeat the same failed command more than twice without changing
   approach. If one failure repeats 3 times, stop and write `ESCALATION.md`.
8. Before final answer, update `AGENT_STATUS.md` so nothing says packaging,
   review, cost, context, verify, or done is pending.
9. Create a valid zip archive `mini_release_auditor_result.zip` using Python
   `zipfile`, then validate it with `zipfile.ZipFile(...).testzip()`.
10. Before final answer, verify the live workspace still contains every required
    source/test/doc file, not only the zip.
11. Final answer must include a SPEC vs SHIPPED table and exact evidence paths.

Implementation requirements:

- Python standard library only.
- Use dataclasses.
- JSON writes must be atomic: write a temp file next to the target, flush it,
  then replace the target.
- CLI commands: `add`, `list`, `show`, `update`, `close`, `reopen`, `search`,
  `report`.
- Release items must include id, title, owner, status, priority, tags, created
  timestamp, updated timestamp, and notes.
- Search/filter/sort must support status, owner, priority, tag, free text, and
  updated-desc ordering.
- Markdown report must summarize counts by status/owner/priority and include
  open high-priority items.
- Tests must cover empty store, invalid JSON, duplicate id prevention, status
  transitions, atomic write temp cleanup, search filters, CLI happy path, CLI
  error path, and report generation.

Final deliverables:

- Passing tests.
- Valid zip archive.
- Saved logs and reviews.
- Final `AGENT_STATUS.md`.
- Final SPEC vs SHIPPED table.

Do not claim done until the saved evidence proves the package works.
