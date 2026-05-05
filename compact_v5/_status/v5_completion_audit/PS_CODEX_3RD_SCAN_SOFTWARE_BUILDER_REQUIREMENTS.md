# PS Codex Third Scan Software Builder Requirements

Date: 2026-05-05

Status: ACTIVE_PRE_AWS_REQUIREMENTS

## Purpose

This document captures the user-facing requirements added after the third deep
scan. These requirements are mandatory before v5 can be called production-ready
for long-running software engineering work.

The goal is not only to finish mapped v5 rows. The goal is that v5 can operate
like the current Codex-worker plus Claude-reviewer audit workflow, using
Bedrock models inside SageMaker:

- maintain durable task state across long runs;
- preserve status, memory, todos, checkpoints, and review evidence;
- coordinate subagents and reviewer-style subagents without silent drift;
- keep prompt/review/log/verdict artifacts;
- track token, cache, cost, duration, and result metadata;
- survive compaction, interruption, save/resume, and restart;
- enforce verify/done gates before claiming completion;
- run optimized local and AWS tests that prove real software-building ability.

## Non-Negotiable Product Requirements

| ID | Requirement | Must Be Proven By |
|---|---|---|
| PS3-1 | Long-running software work must survive compaction and resume. | Local save/resume tests, R16/R19 AWS evidence, final Claude review. |
| PS3-2 | Todos/work ledger must be durable, not only process memory. | Fresh-process restore test and software-builder block evidence. |
| PS3-3 | `AGENT_STATUS.md` and `memory.md` or equivalent status/memory context must be refreshed before important turns. | Local state tests and AWS resume/compaction evidence. |
| PS3-4 | Subagent and reviewer calls must produce structured evidence. | Result envelope containing role, stop reason, files, tests, tokens, cost, cache, duration, heartbeat/timeout, and summary. |
| PS3-5 | Reviewer outputs must be saved as prompts, stdout reviews, stderr logs, verdicts, matrix rows, and status updates. | Block artifacts and final review evidence. |
| PS3-6 | Token/cost/cache telemetry must include parent and child/subagent work where available. | `/cost`, telemetry builder, R-tier evidence. |
| PS3-7 | Large tool outputs must be persisted/replayable by stable reference. | Local result-replay tests and AWS large-output scenario. |
| PS3-8 | Long-running shell/dev-server/test processes must not orphan after timeout/stop. | Process-tree kill/no-orphan tests and logs. |
| PS3-9 | `/verify` and `/done` must be enforced gates, not only advice. | Tests where stale/missing status, test, or review evidence blocks done. |
| PS3-10 | Completed blocks may be revisited only with concrete evidence. | `SOFTWARE_BUILDER_BLOCK_REVISIT_PLAN.md` and final review traceability. |
| PS3-11 | No overlapping `/project-*` command family should be added. Existing commands must be enhanced instead. | Command docs/tests and Claude review. |
| PS3-12 | AWS tests must be optimized: one expensive scenario should prove multiple behaviors. | `OPTIMIZED_AWS_VALIDATION_PLAN.md` and test logs. |

## Required Software-Builder Blocks

These blocks are required after the original canonical blocks close and before
AWS/R-tier production-readiness testing:

| Block | Requirement Covered |
|---|---|
| `SOFTWARE-ASYNC-DECISION` | Decide true async/background subagent scope for v5.0.1; current recommendation is to defer true async and prove strengthened synchronous supervision. |
| `SOFTWARE-STATE` | Durable todos, save/resume, status/memory refresh, crash-safe journal, auto-restore, memory extraction path. |
| `SOFTWARE-CHECKPOINT` | Durable named checkpoints, safe preview/confirm restore/revert, restart-safe listing. |
| `SOFTWARE-SHELL` | Foreground timeout/stop process-tree kill, managed background jobs, durable logs, no-orphan proof. |
| `SOFTWARE-RESULTS` | Large output persistence/replay and stable content-replacement references. |
| `SOFTWARE-SUBAGENT` | Structured synchronous subagent/reviewer envelope with files/tokens/cost/cache/duration/heartbeat/recovery metadata. |
| `SOFTWARE-COMPACT-TELEMETRY` | Typed compaction/recovery/cache telemetry and broader repeated-failure loop evidence. |
| `SOFTWARE-GATE` | Enforced `/verify` and `/done` gate consuming fresh state, result, subagent, compaction, test, and review evidence. |

## Completed Block Revisit Policy

Do not reopen completed/pushed blocks casually. Revisit an old block only when
one of the following points to a concrete gap:

- a new local test fails;
- an optimized AWS test fails;
- Claude final review cites file/row evidence;
- strict scope audit finds weak or missing evidence;
- telemetry shows broken status, memory, compaction, save/resume, subagent, or
  tool-use behavior tied to that block.

When a `SOFTWARE-*` block modifies code originally covered by a completed block,
the worker must:

1. name the affected original block;
2. cite the changed files and tests;
3. update the software-builder block ledger and changelog;
4. request Claude review under the `SOFTWARE-*` block;
5. avoid rewriting old approved evidence unless it is explicitly stale or wrong.

## Test Requirements

Before AWS spend:

- add local zero-cost tests for every accepted `SOFTWARE-*` requirement;
- rerun relevant old block tests when shared code changes;
- run strict scope audit for original blocks;
- run documentation consistency checks;
- run Claude final review over code, docs, tests, logs, telemetry, and the
  software-builder evidence.

AWS/R-tier testing may start only after those local gates pass and the user
explicitly approves spend.

The AWS matrix must prove real software-building ability, not only isolated
unit behaviors. High-signal AWS runs should bundle:

- coding quality;
- tool selection and failure recovery;
- subagent/reviewer coordination;
- status/todo/memory continuity;
- compaction and resume behavior;
- token/cache/cost efficiency;
- checkpoint/revert behavior;
- final artifact quality and verification.

## Confidence Rule

The project may claim high production confidence only after:

1. all original and software-builder blocks are implemented or explicitly
   classified as future/non-goal;
2. each block has local tests and Claude review evidence;
3. all pushed artifacts are consistent and traceable;
4. optimized AWS tests pass with telemetry;
5. final independent Claude review approves production readiness.

Before that, the correct claim is: the plan is ready and the worker can
continue, but production readiness is not yet proven.

