# PS CLI Worker Design

Status: ACTIVE
Created: 2026-05-04

This folder explains the reusable CLI worker/reviewer pattern for the v5.0.1
completion redo. The current primary design is worker-led, not full-auto
supervisor-led.

The repo-level Codex instruction file is `../../../AGENTS.md`. It points future
Codex sessions back to this active v5 audit folder.

It exists because the live process has several moving parts:

- Codex CLI worker implements and documents block work.
- Codex CLI worker coordinates Claude review handoffs directly.
- Claude Code Opus reviewer independently checks scope and evidence.
- Audit files persist state so compaction or chat memory loss does not erase
  the goal.

## Do Not Move Active Files

The active scripts/prompts remain in their original paths because the running
worker references those paths:

- `../06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md`
- `../CLAUDE_REVIEWER_BASE_PROMPT.md`
- `../claude-reviewer-settings.json`
- `../prompts/`
- `../reviews/`
- `../blocks/`
- `../ledger/CLAUDE_REVIEW_MATRIX.md`

This folder is the design and memory index. It links to active files instead of
moving them.

## Core Pattern

```text
Codex worker reads canonical scope
-> worker updates per-block ledger/docs/code/tests
-> worker writes fresh Claude prompt including CLAUDE_REVIEWER_BASE_PROMPT.md
-> worker runs Claude directly with read-only settings
-> Claude review is saved under reviews/
-> worker reads review and updates verdict/matrix/status
-> worker fixes findings
-> repeat until block has zero ship-blocking rows
-> closure review
-> final scope/self-reflection checks
-> specific-file commit and push for rollback/traceability
-> continue to next block
```

## Hard Rules

- Trust artifacts, not agent claims.
- `SYNTHESIS_MASTER.md` is canonical scope.
- No Codex CLI review.
- No nested `codex exec`.
- Claude reviewer is independent.
- Every Claude review prompt must include `CLAUDE_REVIEWER_BASE_PROMPT.md`.
- No AWS/R-tier spend until all blocks and test cases are reviewed and the user
  approves.
- Do not mark a block done while the ledger has blocking rows.
- After a clean block close, commit and push a specific-file checkpoint to
  `sageagent/v5-build` for rollback/traceability.
- Do not tag, run AWS/R-tier, or mark final-ready unless explicitly approved.

## Start Here

Read in this order:

1. `FLOW.md`
2. `STATE_FILES.md`
3. `COMMANDS.md`
4. `FAILURE_MODES.md`
5. `FOLDER_MAP.md`
6. `WORKER_LED_LOOP.md`
7. `../PS_COMPACTION_RESUME_CHECKLIST.md`
8. `LEARNING_FACTORY_ADAPTATION.md`
9. `PROGRESS_VISIBILITY.md`
10. `CLAUDE_REVIEWER_AUTH.md`
11. `WORKER_REVIEWER_TRANSCRIPT_RULE.md`
12. `GIT_CHECKPOINT_POLICY.md`
13. `WORKER_HANDOFF_TEMPLATE.md`

## Resume Safety

After compaction, interruption, or a new worker session, the worker must use
`../PS_COMPACTION_RESUME_CHECKLIST.md`. The worker may not rely on chat memory
or terminal scrollback. It must rerun `scope_audit.py --block <BLOCK>`, compare
the result to the block heartbeat, inspect latest Claude review artifacts, and
write `blocks/<BLOCK>/RESUME_CONFLICT.md` if those sources disagree.

## Learning Factory

`LEARNING_FACTORY_ADAPTATION.md` records the Learning Factory rules that apply
to this redo. The important translation is: Codex remains the single writer,
Claude remains read-only reviewer, and durable repo files replace chat memory
or Claude-specific hooks as the state mechanism.
