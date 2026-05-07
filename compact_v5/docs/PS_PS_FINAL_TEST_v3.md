# PS_PS_FINAL_TEST_v3 - Human Long-Running Software Engineering Acceptance Test

Use this after installing a fresh `compact_v5.zip` in SageMaker.

This test has two parts:

1. UI and metrics visibility.
2. A longer Haiku software-engineering run that must scan v5 files, use a helper,
   build software, test it, save evidence, and package a valid zip.

Budget: set the session cap to `$5.00`.

Model: use `Claude 4.5 Haiku (AU)`.

Region: `ap-southeast-2`.

## Part A - UI And Metrics Check

Run the notebook setup and display the UI with the v5 child-display path:

```python
import sys
sys.path.insert(0, "/home/sagemaker-user/compact_v5")

from entry import CONFIG, BEDROCK_MODELS, create_chat_ui

CONFIG.region = "ap-southeast-2"
CONFIG.model_id = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
CONFIG.mock_mode = False
CONFIG.session_cost_limit = 5.00
CONFIG.max_budget_usd = 5.00
CONFIG.max_iteration_budget = 600
CONFIG.max_tokens = 4096
CONFIG.thinking_enabled = False
CONFIG.thinking_budget = 4096
CONFIG.require_tool_approval = True
CONFIG.enable_status_doc = True
CONFIG.status_doc = "AGENT_STATUS.md"

ui = create_chat_ui()
for _part in ui.render_parts():
    display(_part)
```

Before sending the long prompt, visually confirm the UI shows:

- model dropdown with Haiku selected,
- sub-agent model panel,
- todo/status area,
- `Cache R/W`,
- `Saved`,
- `Without cache`,
- `Reasoning: Thinking ON/OFF`,
- `Agents: parent ...` after at least one turn,
- context and budget bars,
- Stop button.

Save a screenshot if anything looks wrong.

## Part B - Paste This Prompt Into v5

```text
You are the supervisor for my final v5 long-running software engineering
acceptance test v3.

Workspace: /home/sagemaker-user/v5_final_acceptance_workspace_v3

Use the configured Haiku model. Do not exceed $5.00 total session cost. If the
cost approaches the cap, stop, write AGENT_STATUS.md, and explain what remains.

Goal:
Build a small but real Python package named mini_release_auditor, while proving
you can maintain status, use helpers, scan code, test, review, package, and keep
evidence.

Important command guidance:
- Do not use shell cd. Use absolute paths or Python os.chdir inside python_exec.
- Do not claim a file exists until you verify it with Path.exists(), list_dir, or
  an equivalent check.
- After every task/subagent call, immediately save the helper output under
  docs/reviews/<clear-name>.md. If task/subagent is unavailable, create
  docs/reviews/subagent_unavailable.md and explain why.
- The live workspace must contain all required files. The final zip alone is not
  enough.

Required tree:
- mini_release_auditor/__init__.py
- mini_release_auditor/models.py
- mini_release_auditor/store.py
- mini_release_auditor/search.py
- mini_release_auditor/report.py
- mini_release_auditor/cli.py
- tests/test_models.py
- tests/test_store.py
- tests/test_search.py
- tests/test_cli.py
- docs/DESIGN.md
- docs/TEST_REPORT.md
- docs/REVIEW.md
- docs/logs/
- docs/reviews/
- docs/reviews/v5_code_scan.md
- docs/reviews/worker_or_explorer_review.md
- docs/reviews/final_reviewer_review.md
- AGENT_STATUS.md
- README.md
- pyproject.toml

Part 1 - v5 code scan:
Before implementation, inspect these v5 runtime files if present:
- /home/sagemaker-user/compact_v5/ui/chat_ui.py
- /home/sagemaker-user/compact_v5/runtime/tokens.py
- /home/sagemaker-user/compact_v5/tools/task.py
- /home/sagemaker-user/compact_v5/subagent/spawn.py
- /home/sagemaker-user/compact_v5/docs/PS_TEST_REVIEW_FINAL.md

Save a short scan to docs/reviews/v5_code_scan.md explaining:
- how cache/cost metrics should be visible,
- how subagent/reviewer evidence should be saved,
- how AGENT_STATUS.md should survive long work,
- what commands you will use to avoid repeated failure loops.

Part 2 - build mini_release_auditor:
Use Python standard library only.
Use dataclasses.
JSON writes must be atomic: write a temp file next to the target, flush it, then
replace the target.

Release items must include:
- id
- title
- owner
- status
- priority
- tags
- created timestamp
- updated timestamp
- notes

CLI commands:
- add
- list
- show
- update
- close
- reopen
- search
- report

Search/filter/sort must support:
- status
- owner
- priority
- tag
- free text
- updated-desc ordering

Markdown report must include:
- counts by status,
- counts by owner,
- counts by priority,
- open high-priority items.

Process rules:
0. Your first tool-based phase MUST include a real `task` tool call with
   `subagent_type` set to `plan`, `explore`, `review`, or `verify`. Save the
   returned subagent artifact/envelope path in `docs/reviews/`. If you do not
   call the `task` tool, you are not done. A self-written review file is not a
   substitute.
1. Act as supervisor.
2. Keep AGENT_STATUS.md current with goal, plan, completed work, next 3 todos,
   blockers, cost checkpoints, and review state.
3. Use todo_write if available and keep it synchronized with AGENT_STATUS.md.
4. Use at least one worker/explorer/reviewer subagent through the task tool.
   If the tool is truly unavailable, write `docs/reviews/subagent_unavailable.md`
   with the exact error.
5. Save every worker/reviewer/subagent output and returned `task` artifact path
   under docs/reviews/ immediately.
6. Save command/test summaries under docs/logs/.
7. Summarize all command/test logs in docs/TEST_REPORT.md.
8. Use /cost near the start, after implementation, and before final done if
   available. If not available, write the visible cost/metrics from the UI/logs
   into AGENT_STATUS.md and docs/TEST_REPORT.md.
9. Use /context after the plan and before final done if available. If not
   available, write "not available" and continue.
10. Run targeted tests first, then the full test suite.
11. Do not repeat the same failed command more than twice without changing
    approach.
12. If the same failure repeats 3 times, stop and write ESCALATION.md.
13. Before final answer, verify every required live file exists.
14. Before final answer, update AGENT_STATUS.md so nothing says review,
    packaging, cost, context, verify, or done is pending.
15. Before final answer, run /verify full and /done full if available. If not,
    explain clearly and save manual verification in docs/REVIEW.md.
16. Final answer must include a SPEC vs SHIPPED table and exact evidence paths.

Tests must cover:
- empty store,
- invalid JSON,
- duplicate id prevention,
- status transitions,
- atomic write temp cleanup,
- search filters,
- CLI happy path,
- CLI error path,
- report generation.

Do not claim done until:
- tests pass,
- docs/reviews/ has saved helper/reviewer evidence,
- docs/logs/ has saved command/test summaries,
- AGENT_STATUS.md is current,
- SPEC vs SHIPPED is complete.
```

## What To Give Back To Codex

After the run, provide:

- screenshot of the UI metrics footer after the run,
- `AGENT_STATUS.md`,
- `docs/TEST_REPORT.md`,
- `docs/REVIEW.md`,
- `docs/reviews/v5_code_scan.md`,
- `docs/reviews/worker_or_explorer_review.md`,
- `docs/reviews/final_reviewer_review.md`,
- final SPEC vs SHIPPED answer,
- final visible cost from UI or `/cost`.

## Pass Criteria

Clean pass requires:

- all required files present in the live workspace,
- tests pass,
- reviewer evidence is saved,
- status is current,
- UI shows cache/cost/context/agent metrics,
- total cost stays under `$5.00`,
- no repeated failure loop.
