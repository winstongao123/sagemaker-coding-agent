# Software Project Workflow Target

Status: ACTIVE
Created: 2026-05-05

## Goal

v5 is primarily intended for long-running software-writing work in SageMaker,
not short one-off code snippets. The agent should be able to plan, edit,
verify, review, save, resume, and continue across compaction/restarts with
minimal user babysitting.

The critical product claim is not "can write a snippet." The critical claim is:

> v5 can run an independent, long software-coding task with good prompt
> discipline, efficient token/tool use, reliable auto-compaction, intact
> status/memory, and reviewable evidence.

## Design Direction

Do not add a parallel `/project-*` command family for v5.0.1. Consolidate
software-project behavior into the existing command surface:

| Need | Primary command | Notes |
|---|---|---|
| know current project state | `/status` | Should surface current phase, blockers, next steps, status doc |
| set current milestone | `/phase` | Supporting label only; not a second status command |
| persist conversation/task state | `/save` | Should save messages and token/cost state |
| resume after restart/compaction | `/resume` | Should restore messages and token/cost state |
| create rollback point | `/checkpoint` | File-level rollback/checkpoint, separate from session save |
| run verification | `/verify` | Project quality/test/security verification path |
| decide if ready | `/done` | Must depend on clean verification, not a bare claim |
| inspect resource health | `/cost`, `/context` | Cost and token/context diagnostics |
| consolidate memory | `/dream` | Memory cleanup/preservation, manual only |

## Autonomous Long-Task Behavior

The user should not need to be present for every step. During a long coding
task, v5 should naturally:

1. maintain status and phase;
2. search/read before editing;
3. use subagents when useful for exploration, verification, or review;
4. edit code safely;
5. run relevant tests;
6. run a reviewer-mode pass using available Bedrock models/subagents;
7. save/checkpoint state;
8. continue until done or a real decision is needed.

Human intervention should be reserved for ambiguous requirements, spend/AWS
approval, risky actions, final acceptance, or unrecoverable blockers.

The long-task path must preserve:

- AGENT_STATUS/project status across turns;
- memory and `/dream` output across compaction/resume;
- session messages and token/cost state across `/save` and `/resume`;
- task progress after auto-compaction;
- evidence that tool calls were purposeful, not repeated waste;
- telemetry for token use, cache behavior, compaction events, tool calls, and
  subagent dispatches.

## Block/Test Implications

Relevant remaining blocks should preserve this consolidation:

- Block D: slash-command behavior and command tests.
- Block I: skill prompts and command/skill activation behavior.
- Block G/G3: subagent/reviewer/coordinator behavior.
- Block H/H+: memory and `/dream`.
- Block F2/A: long-run continuation and compaction.
- R16 and R19-U10: final proof that long software tasks can run coherently.

Before AWS/R-tier, the coding-ability test hardening must verify this workflow
through existing commands rather than adding new command names.

Block revisit policy:

- `compact_v5/_status/v5_completion_audit/SOFTWARE_BUILDER_BLOCK_REVISIT_PLAN.md`

That file is authoritative for whether completed/pushed blocks must be reopened.
Completed blocks are not reopened automatically; they are reopened only when a
local test, optimized AWS scenario, strict audit, Claude final review, or
telemetry evidence points to a concrete block-level gap.

## Required Final Test Evidence

Before claiming v5 is ready for real software-coding use, the test suite must
include and execute scenarios that prove:

1. Long independent software task completion.
2. Multi-file search-before-edit behavior.
3. Debug/fix behavior with no unrelated changes.
4. App-build behavior with tests passing.
5. Auto-compaction does not lose current task, status, or memory.
6. `/save` and `/resume` restore messages, status-relevant state, and cost.
7. `/status` reflects the current phase/blocker/next step.
8. `/verify` and `/done` do not claim ready while checks fail.
9. Subagent/reviewer use is appropriate and not wasteful.
10. Telemetry/quality review shows efficient prompt, token, cache, and tool
    usage.

These requirements map primarily to R13, R14, R15, R16, and R19-U1 through
R19-U10. If those scenarios are only readiness specs, they must be hardened
into executable tests before AWS/R-tier execution.
