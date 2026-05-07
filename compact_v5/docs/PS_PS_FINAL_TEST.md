# PS_PS_FINAL_TEST - Human Long-Running Software Engineering Acceptance Test

Date: 2026-05-06

Purpose: final hands-on validation after the automated v5.0.1 build, review,
and AWS/R-tier evidence. This is the test the human operator runs in SageMaker
to prove v5 behaves like a practical long-running software engineering agent:
supervisor first, worker subagents when useful, reviewer evidence before done,
logs kept, cost visible, and no silent drift.

This does not replace `PS_TEST_REVIEW_FINAL.md`. It is the final user-facing
acceptance script to run on the production zip.

## What This Test Proves

Explain it like you are 9:

v5 already passed obstacle-course tests. This file is the "real desk" test.
You give v5 a small but real software project. It must plan, build, ask helper
agents, review itself, fix mistakes, write down what happened, show cost, and
only say done when tests and review evidence are saved.

The key question is not "can it write one code snippet?" The key question is:

Can v5 keep a long software task organized without losing the goal?

## Hard Test Rules

- Run this from a fresh extraction of the production `compact_v5.zip`, not from
  the source repo with `_status/` and tests.
- Use SageMaker notebook UI unless explicitly testing headless runtime.
- Use real Bedrock mode for the final run: `CONFIG.mock_mode = False`.
- Set a small explicit cost budget before starting. Suggested: `$2.00` for this
  acceptance task.
- Use Claude 4.5 Sonnet AU as the main model for the first final acceptance run.
- Keep subagent model overrides visible in the UI. Haiku is acceptable for
  worker/explorer subagents if you want to test cheaper helpers, but reviewer
  quality matters.
- Do not allow extra AWS services beyond Bedrock unless you explicitly approve
  them. The test project should write files locally only.
- Stop if the same failure repeats 3 times without a new hypothesis.
- Stop if cost exceeds the chosen budget.
- Stop if the agent skips saved status, logs, review, or final verification.

## Setup

1. Extract the production zip to a clean folder:

```text
~/compact_v5_final_acceptance
```

2. Open:

```text
chat.ipynb
```

3. In Cell 2, configure:

```python
CONFIG.region = "ap-southeast-2"
CONFIG.mock_mode = False
CONFIG.bedrock_only = True
CONFIG.iteration_budget = 600
CONFIG.max_tokens = 4096
CONFIG.thinking_enabled = False
CONFIG.cost_budget_usd = 2.00
```

4. Select the default main model:

```text
Claude 4.5 Sonnet (AU) - default
```

5. Confirm the UI shows:

- dark v4-style panel;
- main model dropdown;
- sub-agent model dropdown panel;
- Send, Stop, Compact, Clean, and mode/status text;
- `/cost`, `/context`, `/checkpoint`, `/verify`, and `/done` available.

6. Create a fresh project workspace outside the v5 runtime folder:

```text
~/v5_final_acceptance_workspace
```

## The Software Task

The task is intentionally medium-sized. It should be big enough to require
planning, multiple files, tests, and review, but small enough to finish under
budget.

Build a local Python package named:

```text
mini_issue_tracker
```

Required files:

```text
mini_issue_tracker/
  issue_tracker/
    __init__.py
    models.py
    store.py
    cli.py
    search.py
    report.py
  tests/
    test_models.py
    test_store.py
    test_cli.py
    test_search.py
  docs/
    DESIGN.md
    CHANGELOG.md
    TEST_REPORT.md
    REVIEW.md
    logs/
    reviews/
  AGENT_STATUS.md
  README.md
  pyproject.toml
```

Required behavior:

- Create, update, close, reopen, list, search, and report issues.
- Store issues in JSON.
- Use atomic writes for JSON save.
- Support tags, priority, status, title, description, and created/updated time.
- Provide a CLI using `argparse`.
- Generate a markdown report from current issues.
- Handle invalid JSON, missing files, empty projects, duplicate IDs, and bad CLI
  arguments gracefully.
- Include tests for core logic and CLI behavior.
- Include a README that a new user can follow.

## Prompt To Paste Into v5

Paste this into the v5 chat UI as the first real task:

```text
You are the supervisor for my final v5 long-running software engineering acceptance test.

Workspace:
~/v5_final_acceptance_workspace

Goal:
Build a small but real Python package named mini_issue_tracker. It must include models, JSON storage with atomic writes, search/filter/sort, argparse CLI, markdown report generation, tests, README, design notes, changelog, test report, review report, logs, and final status.

Required project tree:
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

Hard process rules:
1. Act as supervisor. Keep AGENT_STATUS.md current with goal, plan, completed work, next 3 todos, blockers, cost checkpoints, and review state.
2. Use a todo list internally and keep it synchronized with AGENT_STATUS.md.
3. Use at least one worker/explorer subagent through the task tool for design or codebase review before implementation becomes final.
4. Use at least one reviewer/verify subagent or reviewer-style pass before claiming done.
5. Save worker and reviewer outputs under docs/reviews/ with clear filenames.
6. Save command/test summaries under docs/logs/ and summarize them in docs/TEST_REPORT.md.
7. Use /cost near the start, after the main implementation, and before final done.
8. Use /context after the plan and before final done. If compaction happens, confirm AGENT_STATUS.md still contains enough state to resume.
9. Use /checkpoint create before risky edits or broad refactors.
10. Run targeted tests first, then the full test suite.
11. Do not repeat the same failed tool command more than twice without changing approach.
12. If the same failure repeats 3 times, stop and write ESCALATION.md instead of looping.
13. If Bedrock cost exceeds $2.00 for this test, stop and report.
14. Before final answer, run /verify full if available, then /done full if available.
15. Final answer must include a SPEC vs SHIPPED table and exact evidence paths.

Implementation requirements:
- Use only the Python standard library.
- Use dataclasses or simple classes, not external dependencies.
- JSON writes must be atomic by writing a temp file and replacing the target.
- The CLI must support create, list, show, update, close, reopen, search, and report.
- Tests must cover empty store, invalid JSON, duplicate ID prevention, status transitions, search filters, CLI happy path, and CLI error path.
- README must show install/test/use examples.

Final deliverables:
- Passing tests.
- docs/DESIGN.md
- docs/CHANGELOG.md
- docs/TEST_REPORT.md
- docs/REVIEW.md
- docs/reviews/worker_review.md or equivalent
- docs/reviews/final_reviewer_review.md or equivalent
- AGENT_STATUS.md final state
- final /cost output
- final /context output
- final /verify and /done outputs or a clear explanation if unavailable

Do not claim done until the saved evidence proves the project works and the reviewer pass has no ship-blocking findings.
```

## What The Human Should Watch During The Run

Use this table while v5 is working.

| Check | Good Behavior | Bad Behavior |
|---|---|---|
| Planning | Writes a concrete plan and status file before broad edits. | Starts coding with no visible plan or status. |
| Subagents | Uses `task` for focused worker/reviewer work and saves the result. | Claims review happened but saves no review output. |
| Tool use | Reads/searches targeted files, runs targeted tests, then full tests. | Repeats broad commands or failed commands without a new idea. |
| Cost | Runs `/cost` and stays under the chosen budget. | Keeps spending without cost checkpoints. |
| Context | Runs `/context` and uses `AGENT_STATUS.md` as resume anchor. | Relies only on chat memory for a long task. |
| Checkpoint | Uses `/checkpoint create` before risky changes. | Makes broad edits with no rollback point. |
| Tests | Runs targeted tests and full tests; records results. | Says tests pass without paths/logs. |
| Review | Reviewer checks spec vs shipped, not just style. | Reviewer gives generic praise or no row-by-row evidence. |
| Final answer | Gives evidence paths and SPEC vs SHIPPED table. | Gives a vague "done" claim. |

## Metrics To Collect And Paste Back

After the run, paste these into the validation chat:

```text
1. Main model:
2. Subagent model settings:
3. Region:
4. Start /cost:
5. Final /cost:
6. Final /context:
7. Did compaction happen? If yes, did AGENT_STATUS.md preserve state?
8. Number of files created:
9. Test command and result:
10. Final /verify output:
11. Final /done output:
12. Review artifact paths:
13. Worker/subagent artifact paths:
14. Any repeated failed commands:
15. Any cost or budget warnings:
16. Final file tree:
17. Contents of AGENT_STATUS.md:
18. Contents of docs/TEST_REPORT.md:
19. Contents of docs/REVIEW.md:
20. Any screenshots of the UI cost/context/status area:
```

## Acceptance Rubric

Score out of 100.

| Area | Points | Pass Signal |
|---|---:|---|
| Functional correctness | 25 | CLI and library work; tests pass. |
| Software architecture | 20 | Clean modules, simple APIs, atomic storage, good errors. |
| Test quality | 15 | Edge cases are tested, not only happy paths. |
| Tool/process discipline | 15 | Targeted reads/tests, no repeated tool loop, checkpoints used. |
| Status and memory | 10 | `AGENT_STATUS.md`, logs, and resume anchors are current. |
| Subagent/reviewer loop | 10 | Worker/reviewer evidence is saved and acted on. |
| Cost/context telemetry | 5 | `/cost` and `/context` are captured and reasonable. |

Interpretation:

- 90 to 100: strong acceptance. v5 behaves like a real software-building agent.
- 80 to 89: usable, but inspect weak areas before company use.
- below 80: do not call this final. Fix the weak area and rerun.

## Failure Rules

The test fails if any of these happen:

- v5 does not use any worker/reviewer subagent or equivalent reviewer pass.
- final code has no passing tests.
- no saved review evidence exists.
- no saved status/log/test report exists.
- v5 repeats the same failed tool pattern 3 times.
- cost exceeds the user-set limit without stopping.
- v5 says "done" without a SPEC vs SHIPPED table.
- v5 cannot explain what changed, what was tested, and where evidence is saved.

## What I Will Validate When Results Are Pasted Back

When the user pastes results, validate:

- final project quality;
- whether tests cover real edge cases;
- whether v5 used tools efficiently;
- whether subagent/reviewer outputs are real and saved;
- whether status/memory/checkpoint behavior would survive compaction or resume;
- whether cost/token/context behavior is acceptable;
- whether final claims match saved evidence;
- whether any failure points reveal a v5.0.2 blocker.

## Final Note

Do not judge v5 by one polished final paragraph. Judge it by the trail:
status, logs, tests, reviews, cost, context, checkpoints, and final artifact
quality. That is the behavior we designed v5 to make visible.
