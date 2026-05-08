# PS_PS_FINAL_TEST - Human Long-Running Software Engineering Acceptance Test

Date: 2026-05-07

This is the simple final test you run yourself in v5.

You do **not** prepare the project files. v5 must create them.

Your job is only:

1. Open v5 in SageMaker.
2. Paste the prompt below.
3. Let v5 work.
4. Collect the result zip or key files.
5. Paste/send the evidence back to Codex for final validation.

## What This Test Checks

This test checks whether v5 can do a real, longer software engineering task:

- plan the work;
- create multiple files;
- use worker/reviewer subagents or reviewer-style passes;
- keep `AGENT_STATUS.md`;
- keep logs and review notes;
- run tests;
- show `/cost` and `/context`;
- avoid repeating bad tool calls;
- create a final zip with evidence.

Explain it like you are 9:

v5 must build a small software toy, test it, ask a helper to check it, write down
what happened, and pack the evidence into a zip.

## Before You Start

Use a fresh v5 folder from `compact_v5.zip`.

Open:

```text
chat.ipynb
```

Recommended settings:

```python
CONFIG.region = "ap-southeast-2"
CONFIG.mock_mode = False
CONFIG.bedrock_only = True
CONFIG.iteration_budget = 600
CONFIG.max_tokens = 4096
CONFIG.thinking_enabled = False
CONFIG.cost_budget_usd = 2.00
```

Use the normal default model:

```text
Claude 4.5 Sonnet (AU) - default
```

## Paste This Prompt Into v5

```text
You are the supervisor for my final v5 long-running software engineering acceptance test.

Workspace:
/home/sagemaker-user/v5_final_acceptance_workspace

Important:
I will not prepare any project files. You must create the project from scratch inside the workspace.

Goal:
Build a small but real Python package named mini_issue_tracker.

The package must:
- use only the Python standard library;
- provide issue models;
- store issues in JSON with atomic writes;
- support create, list, show, update, close, reopen, search, and report;
- provide an argparse CLI;
- generate a markdown report;
- include tests;
- include README, design notes, changelog, test report, review report, logs, and final status.

Required project files:
- issue_tracker/__init__.py
- issue_tracker/models.py
- issue_tracker/store.py
- issue_tracker/cli.py
- issue_tracker/search.py
- issue_tracker/report.py
- tests/test_models.py
- tests/test_store.py
- tests/test_cli.py
- tests/test_search.py
- docs/DESIGN.md
- docs/CHANGELOG.md
- docs/TEST_REPORT.md
- docs/REVIEW.md
- docs/logs/
- docs/reviews/
- AGENT_STATUS.md
- README.md
- pyproject.toml

Process rules:
1. Act as supervisor, not just code writer.
2. Keep AGENT_STATUS.md updated with goal, plan, completed work, next 3 todos, blockers, cost checkpoints, and review state.
3. Use a todo list and keep it aligned with AGENT_STATUS.md.
4. Use at least one worker/explorer subagent through the task tool, or clearly explain if the tool is unavailable.
5. Use at least one reviewer/verify subagent or reviewer-style pass before claiming done.
6. Save worker/reviewer notes under docs/reviews/.
7. Save test and command summaries under docs/logs/.
8. Run /cost near the start, after implementation, and before final done.
9. Run /context after planning and before final done.
10. Use /checkpoint create before broad or risky edits if available.
11. Run targeted tests first, then the full test suite.
12. Do not repeat the same failed command more than twice without changing approach.
13. If the same failure repeats 3 times, stop and write ESCALATION.md.
14. If Bedrock cost exceeds $2.00, stop and report.
15. Before final answer, run /verify full and /done full if available.

Final evidence:
The live workspace must include:
- the whole mini_issue_tracker project;
- AGENT_STATUS.md;
- docs/DESIGN.md;
- docs/CHANGELOG.md;
- docs/TEST_REPORT.md;
- docs/REVIEW.md;
- docs/logs/;
- docs/reviews/;
- FINAL_FILE_TREE.txt;
- FINAL_METRICS.md.

FINAL_METRICS.md must include:
- final /cost output;
- final /context output;
- final /verify full output or explanation;
- final /done full output or explanation;
- test command and result;
- any repeated failures;
- final SPEC vs SHIPPED table.

Do not claim done until tests pass, review evidence is saved, and all required
live files exist.
```

## What To Send Back To Codex

Paste or upload these files:

```text
AGENT_STATUS.md
docs/TEST_REPORT.md
docs/REVIEW.md
FINAL_METRICS.md
FINAL_FILE_TREE.txt
pytest output
any ESCALATION.md or failure log if created
```

Also tell Codex:

```text
main model used:
subagent model settings:
region:
final cost:
did compaction happen:
did reviewer pass:
did /verify pass:
did /done pass:
```

## Pass / Fail

Pass means:

- v5 created the project;
- tests passed;
- logs and reviews were saved;
- cost/context were captured;
- final answer has evidence paths and SPEC vs SHIPPED.

Fail means:

- no tests;
- no review evidence;
- no status file;
- repeated tool loop;
- cost went over budget without stopping;
- v5 says "done" without evidence.
