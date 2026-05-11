# Future Software Development Lessons From compact_v5

Date: 2026-05-11
Scope: Higher-level lessons from the compact_v5 build, v4/Runnable/Hermes/Learning
Factory comparisons, notes_cli acceptance run, and S3 real-use failure.

This document is intentionally not just technical. It records reusable product
and engineering lessons for future software-development work.

## Executive Summary

compact_v5 did many hard things correctly: long-task supervision, status files,
subagent evidence, cost/cache metrics, zip verification, and independent review.
But the S3 real-use transcript showed a deeper lesson: **a system can pass a
benchmark and still fail the user's lived workflow**.

The future rule is simple:

> Do not only test whether the machinery works. Test whether the user can see,
> trust, and steer the machinery while it works.

## Core Lessons

| Lesson | What happened | Future rule | Concrete reference |
|---|---|---|---|
| 1. Passing acceptance is not the same as being ready | PS/PS v3 passed, but the user later saw drift, high cost, wrong S3 diagnosis, and confusing UI. | Every benchmark needs a paired real-use transcript test. | `PS_PS_FINAL_TEST_v3_RESULT.md`; `PS_PS_FINAL_TEST_v3_REAL_USE_ISSUES.md` |
| 2. UI is not decoration; it is supervision | The notes_cli run felt stuck because live work, subagents, tools, and thinking were not visible in the right way. | For agents, UI must show progress, tool use, cost, blockers, and reviewer work as first-class state. | `PS_PS_FINAL_TEST_v3_UI_ISSUES.md` |
| 3. Tool truth must match executor truth | UI/docs said S3 read/list could work when Bedrock-only was OFF, but `aws s3` was blocked and boto3 failed on `linecache`. | A tool/policy promise is invalid until an executable smoke test proves the exact path. | S3 transcript; `compact_v5/tools/python_exec.py`; `compact_v5/security/dangerous_patterns.py` |
| 4. Drift is often a product failure, not just a model failure | After S3 failed, the agent switched to summarizing the compact_v5 source tree and presented it as useful progress. | Fallbacks must stay anchored to the original user intent and say clearly what remains unanswered. | `PS_PS_FINAL_TEST_v3_REAL_USE_ISSUES.md`, Problem 3 |
| 5. Cost is a behavioral signal | The simple S3 request used 7 calls and 2,636 output tokens. The cost was not random; it revealed retry loops, verbosity, and tool mismatch. | Treat cost spikes as bug reports. Attach them to exact behaviors. | S3 transcript cost line; `S3_REAL_USE_FIX_WORKER_PROMPT_20260511.md`, Block 6 |
| 6. Independent review must be operationally tested | A worker tried Claude review through the wrong auth route and got `Credit balance is too low`. | Review process is part of the system; test the reviewer command, auth mode, and saved artifacts. | `PS_PS_FINAL_TEST_v3_UI_ISSUES.md`, Claude review correction |
| 7. Architecture drift can happen through paths and packaging | Workers repeatedly referenced old `compact_v5/compact_v5/` paths after the active tree became flattened `compact_v5/`. | Every worker prompt must state the active tree, zip root, and no-touch paths. | `AGENT_STATUS.md`; `S3_REAL_USE_FIX_WORKER_PROMPT_20260511.md` |
| 8. "Better than v4/Runnable" means adapted, not copied | Runnable's tool deferral saves schema tokens, but the S3 run showed deferred common tools can add a first-use tax. | Port ideas with measurement and local constraints, not ideology. | `PS_V5_LEARNINGS_FROM_REPOS.md`; S3 real-use cost findings |
| 9. Evidence should teach the next builder | Docs originally captured technical fixes, but future workers also need why the miss happened and what principle to reuse. | Every major incident should end with: symptom, cause, missed test, future rule, and example. | This document |

## Actual Examples

### Example A - The S3 failure is not just an AWS bug

User asked:

```text
list file and bucket structure of my s3
```

Observed chain:

1. Agent tried `aws s3 ls`.
2. Bash security blocked `aws`.
3. Agent tried `boto3`.
4. Python sandbox blocked transitive import `linecache`.
5. Agent said the environment appeared to be in Bedrock-only mode.
6. Status bar said `Bedrock-only: OFF`.
7. User chose local fallback.
8. Agent summarized the compact_v5 source tree instead of re-anchoring to S3.

What future builders should learn:

- The bug is not one line. It is a contract mismatch across UI, prompt,
  security policy, Python sandbox, fallback behavior, and final-answer
  validation.
- Fixing only the import does not fix the drift.
- Fixing only the drift does not make S3 work.
- Fixing only the UI does not reduce cost.

Future test pattern:

```text
Given a user asks for an external resource,
when the preferred access path is blocked,
the agent must name the true blocker,
avoid repeating the same blocked action,
offer only relevant fallbacks,
and keep the final answer anchored to the original request.
```

### Example B - The notes_cli run shows why "in progress" must be visible

The notes_cli acceptance task involved project creation, tests, docs, status,
and a reviewer. The agent was working, but the UI made the user feel stuck.

What future builders should learn:

- Long-running agents need live operational visibility.
- The user should see tools, tests, subagents, and blockers as they happen.
- Metrics should be readable at a glance, not stacked into a confusing wall.
- Thinking/reasoning should never visually compete with the final answer.

Future test pattern:

```text
During a multi-minute task, the UI must update before completion:
- tool started,
- tool result summarized,
- subagent started/finished,
- cost/context changed,
- stop requested state,
- final evidence paths.
```

### Example C - Claude review failed because the process was not tested

The worker attempted independent Claude review, but the CLI used the wrong auth
route and returned `Credit balance is too low`.

What future builders should learn:

- A review requirement is only real if the command is known to work.
- "Use Claude review" is not enough; specify executable command, auth mode,
  output path, and verdict format.
- Independent review should receive architecture context, not only a diff.

Future test pattern:

```powershell
$env:ANTHROPIC_API_KEY = $null
$env:CLAUDE_CODE_USE_BEDROCK = $null
& C:\Users\winst\AppData\Roaming\npm\claude.cmd --setting-sources user --permission-mode dontAsk -p "@review_prompt.md"
```

## Lessons From Reference Systems

| Reference | What it taught v5 | What the S3 incident adds |
|---|---|---|
| v4 | Notebook UI parity matters; simple live feedback can be more trustworthy than richer hidden machinery. | Preserve v4's visible supervision contract when adding v5 complexity. |
| Runnable Claude Code | Tool deferral, structured tools, and rich agent patterns are powerful. | Deferral must be measured against first-use cost and common-task UX. |
| Hermes | Shared budgets and iteration controls matter for preventing runaway work. | Cost controls must be tied to behavior, not only session totals. |
| Learning Factory | ADRs, status files, and review logs make long builds recoverable. | Add intent-drift and real-use transcript reviews to the governance loop. |

## Future Development Checklist

Use this checklist before calling a future agent/tooling release ready:

| Question | Why it matters | Evidence required |
|---|---|---|
| Does the UI promise match an executable path? | Prevents "S3 allowed" while all paths fail. | Smoke test for the exact UI/prompt promise. |
| Does the fallback still answer the original user goal? | Prevents silent task drift. | Transcript replay with fallback choice. |
| Can the user see long-running progress live? | Prevents "it feels stuck." | UI screenshot or live-render fixture. |
| Are tool results summarized before they hit UI/history? | Prevents cost and cognitive overload. | Collapsed card test and token/call measurement. |
| Is the reviewer truly independent and runnable? | Prevents fake review gates. | Saved Claude CLI prompt/output with subscription auth. |
| Is the zip built from the active source tree? | Prevents source/ship drift. | Zip hash/member verification. |
| Did the test include a realistic user mistake or follow-up? | Real failures often happen after the first turn. | Multi-turn transcript test. |
| Did we document the principle, not only the patch? | Helps future builders avoid repeating the class of bug. | Learning note with example and reference. |

## Recommended Documentation Pattern For Future Incidents

Every serious miss should produce one technical issue doc and one learning note.

Technical issue doc:

```text
Symptom
Transcript / reproduction
Code location
Root cause
Patch shape
Tests
Open questions
```

Learning note:

```text
What this teaches us
Why prior tests missed it
What future builders should do differently
Actual example
Reference docs / files
```

## Current Gap Status

As of 2026-05-11, the higher-level lessons are now documented here. The actual
S3 real-use blockers remain open and are assigned to the persistent worker
handoff:

`compact_v5_test_evidence/final_results/S3_REAL_USE_FIX_WORKER_PROMPT_20260511.md`

Do not confuse "lesson documented" with "runtime fixed."
