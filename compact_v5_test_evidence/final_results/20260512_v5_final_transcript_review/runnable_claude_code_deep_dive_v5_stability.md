# Runnable Claude Code Deep Dive For v5 Stability And Performance

Date: 2026-05-12

Scope:
- v5 target: `D:\Github\sagemaker-coding-agent\compact_v5`
- transcript under review: `D:\Github\sagemaker-coding-agent\compact_v5\tests\PS_Final_test\final_test_v5_responds.md`
- local Runnable reference: `D:\Github\gg_claude_code\gg-claude-code-runnable`

Goal:

Learn from Runnable Claude Code without drifting v5 away from its SageMaker
notebook/Bedrock/product constraints. The focus is stability, performance,
resume correctness, tool discipline, and auditable evidence for software tasks.

## Executive Summary

The last final-coding transcript showed that v5 can complete the software task:
it created the project, wrote code, ran tests, used todo/task/reviewer tools,
saved evidence, and produced the requested final report.

The weakness was operational noise. Runtime guards and tool behavior created
false doubt near the end: prose was over-parsed as paths, relative deliverables
were checked under the wrong root, and POSIX `*.py` verification commands did
not expand. Those issues caused unnecessary tool calls, extra reasoning, and
less trustworthy cost narration.

Runnable's strongest lesson is that stability is a control-plane design
problem, not only a model prompt problem. The runtime should give the model
small, truthful, structured signals: command output previews with persisted
paths, resume state that restores todos/cost/session identity, explicit context
and cost accounting, and structural verification nudges before final summary.

## Round 1 - Shell And Tool Output Stability

| Runnable reference | What it does | v5 lesson | v5 action |
|---|---|---|---|
| `src/tools/BashTool/BashTool.tsx:525`, `:530` | Blocks or redirects long/blocking shell patterns and tells the model how to run them safely. | A bad shell result should be diagnosed by the tool, not left for the model to guess. | Already fixed for final-task glob use: local commands containing `*` route through shell execution; the acceptance contract is POSIX/SageMaker glob expansion, while Windows shell behavior remains platform-specific. |
| `src/tools/BashTool/BashTool.tsx:547`, `:606-620` | Separates UI-facing display from model-facing metadata such as background output paths. | Keep user UI clean while preserving auditable paths for the model and logs. | v5 should keep current collapsed tool cards, and next add artifact-backed previews for large bash/test output. |
| `src/tools/BashTool/BashTool.tsx:608-614` | Background tasks report stable task IDs and output file paths. | Long operations should not stall the main loop or force repeated polling. | Backlog: add a v5 shell-job summary that exposes task id, output path, elapsed time, and exit state in one block. |
| `src/tools/BashTool/BashTool.tsx:1038-1054` | Handles races where a command completes as it is being backgrounded. | Tool state machines need explicit race handling, especially notebook UI refresh and long test commands. | Use this as a pattern for future notebook/session refresh tests. |
| `src/utils/task/diskOutput.ts` | Persists task output to disk with bounded retention. | Large evidence should travel as files, not as huge context. | Backlog: add bounded model-visible previews for bash/test artifacts already stored under the project WIP evidence layout. |

Key learning:

v5 should treat every noisy tool result as a product surface. A false negative
from a tool is more expensive than an ordinary failure because it pushes the
model into repeated verification loops.

## Round 2 - Session, Resume, And State Stability

| Runnable reference | What it does | v5 lesson | v5 action |
|---|---|---|---|
| `src/utils/sessionRestore.ts:96-146` | Restores file history, attribution, and todos from transcript state. | Resume is more than messages; it must restore active control state. | v5 now restores visible notebook transcript and has WIP state locations; add a restart audit checklist for todos/status/session. |
| `src/utils/sessionRestore.ts:318-360` | Restores worktree cwd after resume and clears stale path caches. | Workspace/cwd must be an explicit session attribute. | v5 project WIP layout now separates file workspace from evidence home. |
| `src/utils/sessionRestore.ts:426-482` | Reuses resumed session ID, restores metadata, and re-points transcript file. | Session identity should not split between the model, UI, and disk. | Backlog: add a post-resume self-check that reports workspace, WIP path, session id, and transcript path. |
| `src/commands/resume/resume.tsx:228-237` | Direct UUID fallback lets sessions resume even if enriched listing filtered them out. | Resume lookup should have a simple robust fallback. | Backlog: v5 session loader should provide a direct path/id fallback and explain why a session was hidden. |
| `src/utils/sessionStorage.ts:150-155`, `:3708-3744` | Progress messages do not become transcript leaves for resume anchoring. | Progress/UI ticks are not conversation turns. | v5 should keep UI progress visible but avoid feeding it into model-visible history unless it carries evidence. |
| `src/utils/sessionStorage.ts:5050-5053` | Sessions with missing prompt/title receive fallback titles instead of disappearing. | Debuggability beats perfect indexing. | Backlog: never drop v5 sessions only because title/first prompt extraction fails. |

Key learning:

Runnable is strict about separating model-visible history, UI progress, and
runtime metadata. v5 should keep the same separation: visible notebook rows are
for the user, transcript messages are for the model, and WIP files are for
durable audit.

## Round 3 - Cost, Context, Cache, Todo, And Delegation Performance

| Runnable reference | What it does | v5 lesson | v5 action |
|---|---|---|---|
| `src/cost-tracker.ts:177-238` | Formats total cost, API/wall duration, code changes, and usage by model. | Cost claims should come from runtime counters, not prose estimates. | v5 UI block metrics now expose time, tokens, cache, cost, and cache saved. Final answers should refer to those metrics instead of hand-calculating. |
| `src/cost-tracker.ts:266-300` | Accumulates input, output, cache read, cache write, web search, and cost per model. | Cache is first-class performance data. | Keep cache read/write and "without cache" delta visible in v5 blocks. |
| `src/commands/context/context-noninteractive.ts:19-58` | Applies compact boundary, project view, and microcompact before context analysis. | Context reports must measure what the model actually sees. | Backlog: v5 context diagnostics should run after the same prompt transforms as the actual API call. |
| `src/commands/context/context-noninteractive.ts:135` | Shows active context strategy and collapse health. | Compaction should be observable and not mysterious. | Add a v5 context/compaction health section to diagnostic reports. |
| `src/tools/TodoWriteTool/TodoWriteTool.ts:76-107` | Emits a verification nudge when 3+ tasks close with no verification step. | Verification should be structurally inserted before final summary. | Backlog: add a final-summary guard that nudges review/test evidence when a complex todo list closes. |
| `src/tools/TaskCreateTool/prompt.ts` | Encourages task tracking for complex work but not trivial work. | Todo/task usage should be scoped; over-planning wastes tokens. | v5 should avoid broad tool_search/task setup for simple S3/listing turns. |
| `src/tools/AgentTool/prompt.ts:112` | "Never delegate understanding"; subagent prompts need concrete files and changes. | Delegation should reduce work, not outsource synthesis. | Keep this as the v5 subagent rule: main agent frames exact scope, files, expected output, and review criteria. |
| `src/tools/AgentTool/runAgent.ts` cleanup block | Clears agent todo entries, prompt-cache tracking, cloned file state, transcript mappings, and background shell tasks. | Subagents need lifecycle cleanup to avoid memory/state leaks. | Backlog: add a v5 subagent cleanup test for WIP task state and shell jobs. |

Key learning:

The model can be strong but still waste tokens if the runtime does not expose a
clear accounting surface. Good performance is not just "think less"; it is
truthful cost/context/tool state at the right time.

## Why The Transcript Was Functionally Strong But Operationally Noisy

| Phrase | Meaning | Evidence from transcript review | Fix or follow-up |
|---|---|---|---|
| Functionally strong | v5 completed the requested software task. | Project was created, code/tests/review/evidence/final report were produced. | No broad coding-engine rewrite needed. |
| Operationally noisy | v5 spent extra turns proving things that were already true or recovering from tool/runtime false negatives. | False missing paths, failed `*.py` glob command, repeated late checks, manual cost narration. | Path guard and glob fixes are implemented; cost/context reports should become more automatic. |
| Root cause | Runtime control-plane signals were too ambiguous near finalization. | Guard warnings and tool failures arrived late and looked authoritative. | Prefer precise tool diagnostics, explicit project roots, and runtime metrics. |

## Architecture Non-Drift Rules For v5

| Rule | Reason |
|---|---|
| Keep v5 notebook-first. | Runnable is a terminal product; v5's primary delivery surface is SageMaker/Jupyter. Copy concepts, not terminal UI. |
| Keep project evidence under `<project>/compact_v5_wip/`. | User deliverables and audit evidence should travel with the project while v5 runtime internals stay in the runtime folder. |
| Keep source/runtime changes small and covered by tests. | Stability fixes should not trigger new broad behavior drift. |
| Treat UI progress, model transcript, and WIP audit as separate streams. | Mixing them causes resume bugs, context bloat, and misleading UI. |
| Runtime counters are the source of truth for cost/cache/tokens. | Manual final cost narration is not auditable. |
| Subagents receive concrete scoped prompts. | "Based on your findings" prompts create hidden synthesis and review drift. |

## Implemented From This Investigation

| Item | Status |
|---|---|
| Harden final-claim path detection to avoid prose false positives. | Done in `core/query_engine.py`. |
| Check relative deliverables under explicit user-requested project roots. | Done in `core/query_engine.py`. |
| Limit root expansion to explicit roots. | Done after Claude review. |
| Accept quoted relative directories as deliverables. | Done after Claude re-review. |
| Route local `*` glob commands through shell execution for the POSIX/SageMaker acceptance path. | Done in `tools/bash.py`; Windows shell behavior remains platform-specific. |
| Add regression tests for final-task path and glob behavior. | Done in `tests/test_final_task_regression_guards.py`. |
| Document Runnable lessons with correct local source references. | Done in this document. |

## Improvement Backlog

| Priority | Improvement | Acceptance evidence |
|---|---|---|
| High | Add a restart/resume audit command or report: workspace, WIP path, session id, transcript path, visible rows, todos, cost state. | Test that save/restart/load restores both model-visible context and notebook-visible transcript. |
| High | Make final reports pull token/cost/cache from runtime metrics. | Final report includes runtime usage table and avoids hand-authored cost splits. |
| High | Add bounded model-visible previews for large bash/test outputs stored as WIP log artifacts. | Verbose test run creates `compact_v5_wip/docs/logs/...` and the tool result gives a concise preview plus the artifact path. |
| Medium | Add context diagnostics after actual prompt transforms. | Diagnostic token count matches API-bound prompt view after compaction/project view. |
| Medium | Add structural verification nudge for complex todo completion. | Closing 3+ tasks without test/review evidence triggers a pre-final reminder. |
| Medium | Add direct session-id/path fallback for resume. | A session with missing title/large first prompt can still be loaded directly. |
| Medium | Add subagent cleanup regression test. | Completed subagent leaves no stale todo/shell-job/prompt-cache state. |
| Low | Add repeated-command/noise summarizer for transcript audits. | Report lists failed commands, repeated checks, broad scans, and final evidence paths. |

## Pickup Checklist

1. Read this document before making more v5 stability/performance changes.
2. Read `final_test_v5_responds_investigation.md` for the concrete transcript
   defects already fixed.
3. Preserve the v5 architecture boundary: notebook UI, project WIP evidence,
   Bedrock/SageMaker constraints.
4. For any new fix, capture:
   - focused tests;
   - full test suite;
   - `git diff --stat`;
   - updated `compact_v5_ship.zip` verification;
   - independent Claude CLI subscription review with API env vars cleared.
   Use the S3 follow-up review folder and the Claude prompts in this evidence
   folder as the current review-format examples.

## Claude Review Status

Claude CLI subscription review was run with API-token env vars cleared.

| Review | Result | Evidence |
|---|---|---|
| Architecture review | `APPROVE` with two medium doc-consistency polish items | `claude_runnable_deep_dive_arch_review.md` |
| Architecture re-review | `APPROVE`; prior medium issues closed; no HIGH/MEDIUM blockers | `claude_runnable_deep_dive_arch_rereview.md` |

The review question was:

"Do these Runnable-derived lessons improve v5 stability/performance without
copying terminal-only architecture or creating drift from the existing
SageMaker notebook design?"
