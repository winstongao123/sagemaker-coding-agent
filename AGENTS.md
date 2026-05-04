# Codex Instructions For sagemaker-coding-agent

This file is the Codex-facing equivalent of `CLAUDE.md` for this repo.

## Current Priority

The active high-risk work is the v5.0.1 completion redo under:

`compact_v5/_status/v5_completion_audit/`

For v5.0.1 work, read and follow the persistent control files in that folder.
Do not rely on chat memory, terminal scrollback, or prior worker claims.

## v5.0.1 Redo Rules

- `SYNTHESIS_MASTER.md` is canonical scope.
- Codex is the single writer/worker.
- Claude Code is the independent read-only reviewer.
- Do not run Codex CLI review.
- Do not call nested `codex exec`.
- Do not run AWS/R-tier spend without explicit user approval.
- Git must be updated for rollback/traceability. After each clean block close,
  commit a specific file list and push to `sageagent` remote branch `v5-build`.
  Do not tag unless explicitly approved.
- Do not mark a block done while any ledger row is ship-blocking.
- Before any done/ready/close claim, run the relevant scope audit and
  self-reflection checklist.
- Keep progress visible in status files, not only terminal output.
- After compaction or a new session, resume from files plus `scope_audit.py`,
  not memory.
- There is no fixed hard limit on useful review iterations per block; stop only
  on documented stuck-loop conditions.
- Save every worker/reviewer exchange: prompt, review/stdout, stderr/log,
  matrix row, block verdict, and block heartbeat.

## Required v5 Entrypoints

Start v5.0.1 work by reading:

1. `compact_v5/_status/v5_completion_audit/06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md`
2. `compact_v5/_status/v5_completion_audit/00_MASTER_PROTOCOL.md`
3. `compact_v5/_status/v5_completion_audit/PS_COMPACTION_RESUME_CHECKLIST.md`
4. `compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/PROGRESS_VISIBILITY.md`
5. `compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/LEARNING_FACTORY_ADAPTATION.md`
6. `compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/CLAUDE_REVIEWER_AUTH.md`
7. `compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/WORKER_REVIEWER_TRANSCRIPT_RULE.md`
8. `compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/GIT_CHECKPOINT_POLICY.md`

## Persistent State

Use these files to understand current progress:

- `compact_v5/_status/v5_completion_audit/STATUS.md`
- `compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md`
- `compact_v5/_status/v5_completion_audit/blocks/<BLOCK>/STATUS.md`
- `compact_v5/_status/v5_completion_audit/blocks/<BLOCK>/LEDGER.md`
- latest files in `compact_v5/_status/v5_completion_audit/prompts/`
- latest files in `compact_v5/_status/v5_completion_audit/reviews/`
- latest files in `compact_v5/_status/v5_completion_audit/logs/`

## Legacy Context

`CLAUDE.md` remains useful project context, but it is Claude-oriented and partly
legacy v4 overview. For Codex behavior, follow this `AGENTS.md` plus the active
v5 audit control files.
