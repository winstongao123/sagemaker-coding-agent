# Learning Factory Adaptation For v5 Redo

Status: ACTIVE
Created: 2026-05-04

This file records which Learning Factory rules apply to the v5.0.1 redo and
how they are translated from Claude Code defaults into the current Codex-worker
/ Claude-reviewer workflow.

## Source Files Read

- `D:/Github/Learning_Factory/CLAUDE.md`
- `D:/Github/Learning_Factory/docs/LF_LESSON_AGENT_SCOPE_DRIFT.md`
- `D:/Github/Learning_Factory/docs/SETTINGS_PROTOCOL.md`
- `D:/Github/Learning_Factory/docs/SMOKE_TEST_PROTOCOL.md`
- `D:/Github/Learning_Factory/memories/feedback_scope_clarity.md`

## Portable Rules Adopted

| Learning Factory rule | v5 redo adaptation |
|---|---|
| Goals live in files, not chat | `STATUS.md`, block `STATUS.md`, ledgers, review matrix, and `PS_COMPACTION_RESUME_CHECKLIST.md` are the source of truth. |
| One agent, one job, one output | Codex is the only writer/worker. Claude is read-only reviewer. No second writer edits the repo. |
| Always know done/not done | Every active block status must show current task, last completed action, next 3 todos, review count, and blocking row count. |
| Reviewer two-pass | Claude review must check canonical scope compliance first, then code quality. |
| Scope clarity | For broad operations, enumerate affected files/rows before acting. Do not interpret "all" or "done" without row counts. |
| Independent review | Reviewer reads canonical files from disk before trusting worker context. |
| Smoke tests complement unit tests | Real AWS/R-tier and real CLI integration tests are final gates only, not substitutes for row-scope audit. |
| Hook/settings automation should reduce friction, not safety | Do not bypass AWS spend, git push/tag, destructive commands, or reviewer gates for convenience. |

## Claude-Specific Parts Not Copied Directly

These Learning Factory mechanisms are Claude Code specific and are not imported
as-is into the Codex worker:

- `.claude/settings.json` project auto-approval as the primary control plane.
- Claude Code subagents or `/orchestrate` as writers.
- Claude pre-compact/session hooks as the only state mechanism.
- Codex review from inside Claude Code.

Instead, this redo uses explicit repo-local Markdown state, `scope_audit.py`,
worker-managed Claude review prompts, and saved raw review/log artifacts.

## Required v5 Behavior

1. Before any broad change, identify affected block rows and files.
2. Before any done/ready/close claim, run `scope_audit.py --block <BLOCK>` and
   the self-reflection checklist.
3. After compaction/interruption/new session, run
   `PS_COMPACTION_RESUME_CHECKLIST.md` and continue only from files.
4. Claude reviewer prompts must include `CLAUDE_REVIEWER_BASE_PROMPT.md` and
   require Claude to reconstruct scope from `SYNTHESIS_MASTER.md`.
5. Review/fix cycles continue while useful. Stop only on stuck-loop conditions
   and write the blocked report.
6. If Codex disputes Claude, record `DISPUTED_FINDING` and send a fresh Claude
   dispute review with canonical context.

## Test Implication

The v5 test plan must have two layers:

- Fast local tests and row-scope audit for every block.
- Real AWS/R-tier smoke/evidence tests only after all blocks have zero
  ship-blocking rows, Claude closure review, and user approval.

Passing tests alone is not enough. Passing tests plus complete row audit plus
reviewed evidence is the required trust bundle.
