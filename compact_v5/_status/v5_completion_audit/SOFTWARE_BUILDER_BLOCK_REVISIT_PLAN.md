# Software Builder Block Revisit Plan

Date: 2026-05-05

Purpose: prevent the software-builder goal from becoming a vague late-stage
requirement. This file tells the worker when completed blocks must be
revisited, and which remaining blocks must carry the long-running
software-engineering behavior.

## Revisit Rule

Do not reopen a completed/pushed block just because the software-builder goal
was clarified later. Reopen a completed block only if one of these happens:

1. a new local test or optimized AWS test fails against that block's behavior;
2. Claude final review finds a concrete gap with file/row evidence;
3. strict scope audit finds missing/partial/weak evidence;
4. the block introduced an overlapping `/project-*` command or conflicting
   workflow surface;
5. telemetry shows broken status, memory, compaction, save/resume, subagent, or
   tool-use behavior tied to that block.

If none of those triggers occur, keep the block closed and verify the
cross-cutting behavior through final local/AWS tests.

## Completed Blocks

| Block | Status For Software-Builder Goal | Revisit Now? | Reason |
|---|---|---:|---|
| A | Covered by compaction/context-management rows and closure tests | No | Reopen only if R16/R19-U10 compaction evidence fails |
| B | Covered by runtime/config/cost surfaces | No | Reopen only if AWS telemetry/cost evidence fails |
| B+ | Covered by `/save`, `/resume`, AGENT_STATUS, UI command context | No | This is the main completed block for long-task persistence |
| C | Covered by tool/runtime behavior from canonical scope | No | Reopen only on concrete final-review gap |
| C+ | Covered by snapshot/abort behavior | No | Reopen only if long-run interruption evidence fails |
| D | Covered by slash-command surface and command tests | No | This is the main completed block for command consolidation |
| E+F | Covered by runtime permission/status/cost helper surfaces | No | Reopen only on telemetry/status evidence failure |
| K/L/N/T | Covered by their canonical rows and reviewed evidence | No | Reopen only on strict audit, Claude, or AWS evidence failure |

## Remaining Blocks Carrying The Goal

| Block | Required Software-Builder Check |
|---|---|
| F2 | Auto-continuation must not lose task/status after token-budget continuation |
| I | Skill prompts/activation must support `/verify`, review, and coding workflow without overlapping commands |
| G | Subagent coordination must support useful explore/build/verify/review delegation and avoid blind/wasteful spawning |
| G2 | Fork/cache-prefix behavior must preserve long-task context |
| G3 | Permission/approval or execution coordination must preserve safe long-task flow |
| H | Memory extraction/session memory must preserve important coding-task facts |
| H+ | `/dream` memory consolidation must preserve durable project facts |
| M/J/0 | Closure/meta blocks must not weaken the final evidence gate or AWS stop rules |

## New Third-Deep-Scan Software-Builder Blocks

After canonical Block 0 closes, continue into these cross-cutting hardening
blocks. Do not reopen completed blocks unless a concrete test/review/audit
failure points back to them; instead implement the new behavior through the
existing command/tool/runtime surfaces.

| Block | Required Software-Builder Check |
|---|---|
| SOFTWARE-ASYNC-DECISION | Decide and document true async/background subagent scope; current recommendation is defer true async for v5.0.1. |
| SOFTWARE-STATE | Durable todos, `/save`, `/resume`, per-turn status/memory, crash-safe journal, auto-restore, memory extraction path. |
| SOFTWARE-CHECKPOINT | Durable named checkpoint index, safe preview/confirm restore/revert, restart-safe listing. |
| SOFTWARE-SHELL | Foreground process kill-on-timeout/stop, managed background shell lifecycle, durable logs, no-orphan proof. |
| SOFTWARE-RESULTS | Large output persistence/replay and stable content-replacement references. |
| SOFTWARE-SUBAGENT | Structured synchronous subagent/reviewer envelope with files/tokens/cost/cache/duration/heartbeat/recovery metadata. |
| SOFTWARE-COMPACT-TELEMETRY | Typed compaction/recovery/cache telemetry and broader tool-failure loop evidence. |
| SOFTWARE-GATE | Enforced `/verify` and `/done` gate using fresh state, result, subagent, compaction, test, and review evidence. |

## Final Verification

Before production-readiness or 98% confidence:

1. run strict all-block scope audit;
2. run local command/status/save/resume/compaction/subagent/memory tests;
3. run the optimized AWS validation plan;
4. require Claude final independent review over code, docs, tests, logs,
   telemetry, and all pushed block evidence;
5. revisit only the blocks implicated by failing evidence.
