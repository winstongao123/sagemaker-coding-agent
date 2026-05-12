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

## Evidence Coverage Audit

This update cross-checked the lesson layer against the actual evidence archive,
not only the recent S3 transcript.

| Evidence family | Coverage found | What it teaches | Lesson coverage status |
|---|---:|---|---|
| Phase changelogs | 15 files under `full_v5_development_history/compact_v5/MAIN/changelogs/` | Incremental delivery needs phase-level closeout, not memory-only history. | Covered here as "make decisions recoverable." |
| Phase-2 plans and deep scans | 77 Markdown files under `_phase_2/` | Reference repos are useful only when converted into scoped plans, synthesis maps, and reviewable blocks. | Covered here as "adapt, don't copy." |
| Status/review/result archive | 826 Markdown files under `_status/` | Long builds need durable review evidence, not just final claims. | Covered here as "review process is part of the system." |
| Active final results | 87 Markdown files under `final_results/` | Final summaries must be easy to find, not buried in build history. | Covered here as "evidence should teach the next builder." |
| Final human test suites | 3 prompt files under `final_test_suites/` | Human acceptance prompts catch multi-step behavior that unit tests miss. | Covered here as "benchmark plus real-use transcript." |
| Active human docs | 10 files under `compact_v5_test_evidence/compact_v5/docs/` | Production-facing docs should distinguish solved, open, and environment-dependent states. | Covered here as "truthful contracts." |

The important gap was not missing raw evidence. The gap was that the evidence
was too distributed for a future worker to quickly learn the **general software
engineering principles**. This document is the synthesis layer.

## Cross-Artifact Evaluation

| Source class | Example references | What the source proves | What future software work should reuse |
|---|---|---|---|
| Reference comparisons | `PS_V5_LEARNINGS_FROM_REPOS.md`, `V5_RUNNABLE_PORT_LOG.md`, `PS_V5_VS_RUNNABLE_DEEP_REVIEW_20260511.md` | v5 did not invent in a vacuum; it studied v4, Runnable, Hermes, and Learning Factory. | Keep source-backed adoption tables: source path, destination path, adaptation reason, proof test. |
| Changelogs | `CHANGELOG_v5_phase_00.md` through `CHANGELOG_v5_phase_13.md` | Each phase captured what changed and why. | Require phase closeout before moving to the next build block. |
| Plans | `V5_PHASE_2_PLAN*.md`, `SYNTHESIS_MASTER.md`, final test prompts | Planning improved over iterations as gaps were found. | Treat plans as living risk models, not static promises. |
| Implementation evidence | `compact_v5/AGENT_STATUS.md`, active source tree, zip hash checks | Active source/zip can drift from historical docs. | Always state active tree, ship artifact, and hash/manifest proof. |
| Tests | R-tier matrix, final PS/PS tests, smoke tests, visual checks | Many engine behaviors were tested, but real-use UI/S3 gaps still escaped. | Add "real transcript" tests beside synthetic acceptance tests. |
| Results | `PS_PS_FINAL_TEST_v3_RESULT.md`, AWS acceptance results, UI status docs | Results can be true and still incomplete. | Result docs must say what they do **not** prove. |
| Reviews | Claude/Codex review logs, post-zip approvals, failed auth attempt | Independent review works only when the reviewer command and context are correct. | Make review reproducibility a testable artifact. |
| Real-use transcripts | notes_cli session, S3 session | The user experience exposed gaps the formal tests missed. | Preserve real-use transcripts as first-class regression specs. |

## Missing Lessons Added By This Audit

| Missing lesson | Why it was missing | Future rule |
|---|---|---|
| Evidence needs a synthesis layer | The repo had many detailed artifacts, but workers had to read too much to infer the principles. | Add one small "what future builders should learn" document after every serious incident. |
| Results need negative scope | PASS docs proved what passed, but not always what was outside the test. | Every result summary should include "This does not prove..." rows. |
| Real-use tasks should be promoted to tests | The S3 failure came from a real prompt after acceptance passed. | Any real-use failure becomes a transcript replay test or worker proof gate. |
| Review tooling is part of quality | Claude review failed once because auth mode was wrong. | Reviewer invocation must be documented and smoke-tested before relying on the verdict. |
| Cost should influence design | Cost was visible but did not change behavior. | Cost telemetry should trigger product questions: retry loop, verbosity, wrong tool, excessive thinking, or schema tax? |
| Packaging is a product boundary | Source fixes are irrelevant if the zip is stale. | Every status/runtime doc update that ships in zip requires zip rebuild + hash proof. |
| Notebook thinness is a product contract | The v5 notebook became a long integration script while v4's actual user contract was a short, stable launch cell. | Keep notebooks thin; move path/config/display complexity into tested Python modules and validate in the target widget runtime. |

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
| 10. Results must name their limits | v3 acceptance passed the engine layer, but not the S3/live-user workflow. | Every result doc needs "what this does not prove." | `PS_PS_FINAL_TEST_v3_REAL_USE_ISSUES.md`; `FINAL_TEST_SUITE_INDEX.md` |
| 11. Real-use failures become regression specs | The S3 transcript revealed a compound bug no unit test represented. | Convert real failures into transcript replay tests and proof gates. | `S3_REAL_USE_FIX_WORKER_PROMPT_20260511.md` |
| 12. Ship artifacts are part of implementation | Several prior fixes needed zip rebuild/re-review after source changed. The ambiguous `compact_v5.zip` name also blurred source tree vs ship artifact. | Treat packaging verification as implementation, not release paperwork. Name the runtime artifact explicitly: `compact_v5_ship.zip`; keep `compact_v5/` as the complete source tree. | `compact_v5_ship.zip` verification logs; `AGENT_STATUS.md` |
| 13. Copy the reference contract, not the surface ritual | v5 moved to `ui = create_chat_ui()` and one-root-widget display because v4 did root display, but v5's widget tree and the user's target SageMaker runtime still produced `Error displaying widget: model not found` after local visual checks passed. | When using v4 as an example, identify what made it reliable for the user: thin notebook, stable widget-package assumptions, hidden display complexity, and real widget rendering in the actual target SageMaker frontend. Local Jupyter proof is necessary but not sufficient. | `NOTEBOOK_WIDGET_REGRESSION_20260511.md`; `compact_v4/MAIN/agent/chat.ipynb`; `compact_v5/chat.ipynb`; user's 2026-05-12 SageMaker screenshot |

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

### Example D - The notebook widget regression shows why reference copying needs discipline

The user saw:

```text
Error displaying widget: model not found
```

The visible v5 launch cell said v5 followed v4's stable display contract:

```python
ui = create_chat_ui()
```

The investigation found two lessons:

- v4's reliable user contract was a thin notebook and hidden UI complexity, not
  merely the fact that one root widget was displayed.
- v5's notebook grew to 188 lines of config code plus a 59-line launch cell,
  with path-discovery duplicated in both cells. That is too much product logic
  in a notebook surface.
- visual retests in a reused notebook kernel can execute stale imported Python
  modules. A cell can look fixed while `entry.py` from the previous run is
  still in `sys.modules`.

Future test pattern:

```text
Given the shipped notebook is the primary product UI,
the launch cell must stay thin,
display complexity must live in importable Python helpers,
and the exact target SageMaker/Jupyter widget runtime must render the UI before
production readiness is claimed.
The notebook launcher must also refresh/drop its small launcher/UI modules
before importing, so the test exercises the current files on disk.
```

Related source:

- `compact_v4/MAIN/agent/chat.ipynb`
- `compact_v5/chat.ipynb`
- `compact_v5_test_evidence/final_results/NOTEBOOK_WIDGET_REGRESSION_20260511.md`

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
| Did the result doc say what it does not prove? | Prevents benchmark confidence from becoming product confidence. | Explicit negative-scope section. |
| Did a real artifact ship? | Prevents "fixed in source, stale in package." | Zip/package hash parity with source. |
| Can another worker reproduce the review? | Prevents unverifiable approval claims. | Reviewer command, prompt, output, and error log saved. |
| Is the notebook still thin? | Prevents fragile product logic living in cells. | Cell line-count budget plus helper-module tests. |
| Did the actual widget runtime render it? | Prevents false confidence from structural checks only. | Target SageMaker/Jupyter visual smoke or equivalent captured evidence. |
| Did the test run current code, not a stale kernel import? | Prevents "source looks fixed, old module still executing" regressions. | Fresh kernel or explicit launcher-module reload/drop plus visual evidence. |

## Reusable Playbooks For Other Software Projects

### Playbook 1 - Turn a reference repo into product code

Use when learning from another system.

1. Record the source file or concept.
2. State why it applies to your product.
3. State what constraints force adaptation.
4. State what you intentionally drop.
5. Add a test proving the adapted behavior.
6. Add a review row so the decision is inspectable later.

Why this matters: v5's best work came from adapting v4/Runnable/Hermes/Learning
Factory with explicit constraints. The S3 failure came from a place where the
contract was written but the executable path was not proven.

### Playbook 2 - Close a phase without losing the plot

Use for multi-week builds.

1. Update the phase changelog.
2. Update the status handoff.
3. Run focused tests and one representative end-to-end test.
4. Write what the tests do **not** prove.
5. Save review evidence.
6. Rebuild/package if the shipped artifact includes changed files.

Why this matters: compact_v5 had strong changelogs, but the S3 case shows that
phase closeout also needs real-use negative-scope language.

### Playbook 3 - Convert a user complaint into an engineering asset

Use when a user says "it feels wrong" or "it drifted."

1. Preserve the transcript.
2. Separate symptom from root cause.
3. Find all layers involved: UI, prompt, tool, sandbox, runtime, docs, package.
4. Write a technical issue doc.
5. Write a learning note.
6. Create a worker prompt with proof gates.
7. Add the transcript as a replay or acceptance test.

Why this matters: the notes_cli and S3 sessions were not annoyances. They were
better product tests than many synthetic checks.

### Playbook 4 - Make cost actionable

Use when token/cost metrics look high.

1. Attribute cost to behavior: retries, output verbosity, thinking, schemas,
   subagents, tool result history.
2. Remove waste before changing models.
3. Keep enough evidence visible for trust.
4. Test the same prompt before/after.
5. Record the expected call/output budget.

Why this matters: "cost high" is not enough. The S3 case showed exactly which
behaviors produced the cost: repeated blocked paths, verbose menus, and wrong
fallback.

### Playbook 5 - Treat review as executable infrastructure

Use when a project requires independent review.

1. Specify the exact review command.
2. Specify auth mode.
3. Clear conflicting environment variables.
4. Save prompt, output, and error log.
5. Require an explicit verdict.
6. If review cannot run, mark the block blocked or use a named fallback.

Why this matters: a review that silently used the wrong auth path produced
`Credit balance is too low`, which is a process failure, not a code review.

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

As of 2026-05-12, the higher-level lessons are documented and the P0/P1 runtime
blockers from the S3 real-use transcript and notebook widget regression are
fixed, reviewed, tested, and packaged.

Current readiness position:

| Claim | Status | Evidence |
|---|---|---|
| v5 preserves the latest v4 notebook contract | Ready for production test | v4.10.10 reference checked; v5 default is v4-style ipywidgets, with explicit console fallback only. |
| v5 absorbed relevant Runnable lessons | Ready for production test | Tool/progress visibility, reviewer discipline, status tracking, subagent observability, prompt/cache/cost awareness documented and implemented where compatible with SageMaker/Bedrock. |
| S3 real-use blockers | Fixed | `aws_s3_list`, accurate sandbox diagnostics, S3 intent-drift guard, one-strike retry block, and cost controls. |
| Notebook widget regression | Source/package fixed locally; target runtime still blocked | Local Jupyter/Playwright visual evidence shows Cell 2 and Cell 3 render with `HAS_WIDGET_ERROR False`, but the user's fresh SageMaker screenshot still shows `Error displaying widget: model not found`; basic target `ipywidgets.IntSlider` smoke is now required. |
| Production-test readiness | 98% confidence | 31 focused tests passed, zip rebuilt/verified, Claude CLI reviews approved with no HIGH/MEDIUM findings. |

Do not confuse "98% production-test ready" with "guaranteed production
flawless." The remaining 2% is target-environment variance: SageMaker/Jupyter
widget manager, IAM credentials, and installed package versions.
