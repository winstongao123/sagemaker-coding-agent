# PS_PS_FINAL_TEST_v2 - Human Long-Running Software Engineering Acceptance Test

Date: 2026-05-07

This is the final hands-on test for v5. You paste one prompt into SageMaker and
let v5 act as the supervisor. v5 must plan, build, call a helper/reviewer, test,
save logs, show cost/context, and create a zip you can send back for validation.

Explain it like you are 9:

v5 must build a small software project, ask a helper to check it, write down what
happened, test the project, and pack all proof into a zip.

## Before You Start

Use a fresh copy from `compact_v5.zip`.

Open:

```text
chat.ipynb
```

Recommended SageMaker setup:

```python
CONFIG.region = "ap-southeast-2"
CONFIG.model_id = "au.anthropic.claude-sonnet-4-5-20250929-v1:0"
CONFIG.mock_mode = False
CONFIG.aws_bedrock_only = True
CONFIG.max_iteration_budget = 600
CONFIG.max_tokens = 4096
CONFIG.thinking_enabled = False
CONFIG.session_cost_limit = 2.00
CONFIG.auto_compact_enabled = True
CONFIG.subagents_enabled = True
```

Use the UI default model:

```text
Claude 4.5 Sonnet (AU) - default
```

Before the big prompt, do one tiny smoke message:

```text
Say READY and do not use tools.
```

Confirm the UI shows:

- `Cache R/W`;
- `Saved`;
- `Agents: parent ...`;
- `Sub-Agents`;
- todo/status area;
- `/cost` works;
- `/context` works.

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
1. Act as supervisor, not only as a code writer.
2. Keep AGENT_STATUS.md updated with goal, plan, completed work, next 3 todos, blockers, cost checkpoints, and review state.
3. Use a todo list and keep it aligned with AGENT_STATUS.md.
4. Use at least one worker/explorer subagent through the task tool before final implementation, or clearly explain if the task tool is unavailable.
5. Use at least one reviewer/verify subagent or reviewer-style pass before claiming done.
6. Save worker/reviewer notes under docs/reviews/ with clear filenames.
7. Save test and command summaries under docs/logs/.
8. Run /cost near the start, after implementation, and before final done.
9. Run /context after planning and before final done.
10. Use /checkpoint create before broad or risky edits if available.
11. Run targeted tests first, then the full test suite.
12. Do not repeat the same failed command more than twice without changing approach.
13. If the same failure repeats 3 times, stop and write ESCALATION.md.
14. If Bedrock cost exceeds $2.00, stop and report.
15. Before final answer, run /verify full and /done full if available.
16. If compaction happens, check AGENT_STATUS.md and confirm it has enough state to resume.

Quality rules:
- JSON writes must be atomic: write a temp file, then replace the target.
- Tests must cover empty store, invalid JSON, duplicate ID prevention, status transitions, search filters, CLI happy path, and CLI error path.
- Do not claim done until tests pass, review evidence is saved, and the zip is created.
- Final answer must include a SPEC vs SHIPPED table and exact evidence paths.

Final packaging:
Create this zip at the end:

/home/sagemaker-user/v5_final_acceptance_results.zip

Use Python standard library zipfile. Do not use external dependencies.

The zip must include:
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
```

## What To Watch In The UI

During the run, the UI should show:

- cost, last cost, context percent, budget percent;
- `Cache R/W` and `Saved`;
- `Agents: parent ...` plus any subagent type such as `review`;
- subagent start/finish messages in chat, for example `[subagent:review] started`;
- todo/status evidence, either via the todo panel or `AGENT_STATUS.md`;
- no repeated failing command loop.

There is not a separate live subagent window in v5.0.1. The main notebook is the
supervisor view. Subagent lifecycle, cost/cache attribution, and saved review
files are the traceability mechanism.

## What To Send Back To Codex

Best option:

```text
/home/sagemaker-user/v5_final_acceptance_results.zip
```

Also send these values:

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

If you cannot upload the zip, paste these files:

```text
AGENT_STATUS.md
docs/TEST_REPORT.md
docs/REVIEW.md
FINAL_METRICS.md
FINAL_FILE_TREE.txt
pytest output
any ESCALATION.md or failure log if created
```

## Pass / Fail

Pass means v5 created the project, tests passed, logs and reviews were saved,
cost/context were captured, subagent or reviewer evidence exists, the zip was
created, and the final answer cites exact evidence paths.

Fail means no tests, no review evidence, no status file, repeated tool loops,
cost went over budget without stopping, or v5 says done without evidence.

