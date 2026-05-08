# State Files

Use these files instead of chat memory.

## Global Control Files

| File | Purpose |
|---|---|
| `../../../AGENTS.md` | Repo-level Codex instructions; Codex equivalent of `CLAUDE.md` |
| `../README.md` | Audit entrypoint |
| `../00_MASTER_PROTOCOL.md` | Rules for completion redo |
| `../03_LEDGER_SCHEMA.md` | Ledger schema |
| `../06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md` | Current worker-led prompt |
| `../CLAUDE_REVIEWER_BASE_PROMPT.md` | Static base included in every Claude review prompt |
| `../PS_COMPACTION_RESUME_CHECKLIST.md` | Required pickup procedure after compaction/interruption/new worker session |
| `../STATUS.md` | Current audit status |
| `../TEST_CASE_PREP.md` | AWS/R-tier test preparation status |
| `../../PS_AGENT_SELF_REFLECTION.md` | Mandatory anti-scope-drift checklist |
| `../../scripts/scope_audit.py` | Mechanical expected-row vs ledger/evidence audit |
| `../../scripts/verify_scope_completeness.ps1` | Strict repo-local wrapper for the scope gate |

## Review And Design Files

| File | Purpose |
|---|---|
| `../claude-reviewer-settings.json` | Read-only Claude permissions / Codex denied |
| `../PS_CLI_WOKER_DESIGN/` | This reusable design memory folder |
| `../PS_CLI_WOKER_DESIGN/LEARNING_FACTORY_ADAPTATION.md` | Learning Factory rules adapted for Codex worker / Claude reviewer |
| `../PS_CLI_WOKER_DESIGN/PROGRESS_VISIBILITY.md` | Required heartbeat cadence and fields |
| `../PS_CLI_WOKER_DESIGN/CLAUDE_REVIEWER_AUTH.md` | Claude reviewer auth routing rule |
| `../PS_CLI_WOKER_DESIGN/WORKER_REVIEWER_TRANSCRIPT_RULE.md` | Worker/reviewer message persistence rule |
| `../PS_CLI_WOKER_DESIGN/GIT_CHECKPOINT_POLICY.md` | Required per-block commit/push policy |

## Per-Block Files

For each block:

`../blocks/<BLOCK>/`

Required files:

- `BASELINE.md`
- `LEDGER.md`
- `STATUS.md`
- `PROMPTS.md`
- `TESTS.md`
- `CHANGELOG.md`
- `DECISIONS.md`
- `WORKER_SELF_REVIEW.md`
- `REVIEWER_VERDICT.md`
- `MEMORY_UPDATE.md`
- `GIT_CLOSE_PLAN.md`

## Review Evidence

| Directory/File | Purpose |
|---|---|
| `../prompts/` | Saved Claude prompts and Codex handoff prompts |
| `../reviews/` | Raw Claude outputs |
| `../logs/` | CLI stdout/stderr logs |
| `../ledger/CLAUDE_REVIEW_MATRIX.md` | Cross-block review table |

## What Proves A Block Is Healthy

- Ledger row count matches canonical expected count.
- Every shipped row has code/test/PORT_LOG/ADR evidence.
- Non-shipped rows are still blocking unless user approved defer/drop.
- Claude review output exists, is non-empty, and has a parseable `VERDICT:`.
- Matrix contains the review row.
- Block status does not overclaim done.
- After compaction or interruption, `scope_audit.py --block <BLOCK>` agrees
  with the block heartbeat and latest Claude verdict. If not, the block has a
  `RESUME_CONFLICT.md` instead of continued implementation.
