# Worker-Led Loop

Status: PRIMARY DESIGN
Created: 2026-05-04

This is the recommended workflow for the v5.0.1 redo.

## Why

The earlier full-auto PowerShell supervisor made Claude CLI handoffs brittle:

- plan mode caused plan-file behavior
- some review outputs were empty or lacked `VERDICT:`
- stale prompts could miss newly implemented rows
- prompt delivery differed between permission modes

The replacement is simpler: one Codex worker owns implementation and file
updates, while Claude remains an independent read-only reviewer.

## Primary Files

| File | Purpose |
|---|---|
| `../06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md` | Prompt for the Codex worker |
| `../CLAUDE_REVIEWER_BASE_PROMPT.md` | Static base every Claude review prompt must include |
| `../claude-reviewer-settings.json` | Read-only reviewer permissions |
| `../prompts/` | Saved prompts actually sent |
| `../reviews/` | Saved Claude outputs |
| `../logs/` | Saved stderr/logs |
| `../ledger/CLAUDE_REVIEW_MATRIX.md` | Review state table |

## Removed From Active Workflow

These abandoned files were removed to prevent accidental reuse:

- `../01_CODEX_WORKER_START_PROMPT.md`
- `../02_CLAUDE_REVIEWER_START_PROMPT.md`
- `../05_CODEX_AUTONOMOUS_REDO_PROMPT.md`
- `../RUN_SUPERVISOR.ps1`
- `../PS_Codex_Supervisor/`

Historical prompts/reviews that mention them are kept as audit history.

## Good Review Artifact

A usable Claude review must:

- be non-empty
- include `EXPECTED ROW COUNT`
- include `LEDGER ROW COUNT`
- include reviewed rows/findings
- include `VERDICT:`
- include `SHIP DECISION:`

If any of those are missing, record the review as failed/no-verdict and rerun
with a new iter number after fixing the prompt/command.

## Worker Independence Guardrail

The worker may write the review prompt only because every prompt must include
`CLAUDE_REVIEWER_BASE_PROMPT.md`, which forces Claude to reconstruct scope from
`SYNTHESIS_MASTER.md`.

The worker can add changed files and context. The worker cannot define the
review scope.
