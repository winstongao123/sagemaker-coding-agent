# v5 Completion Audit

Status: ACTIVE
Created: 2026-05-04
Purpose: finish v5.0.1 honestly against the post-Wave-5-DEEP plan.

This folder is the control center for the v5.0.1 completion redo.

## Reviewer Policy Override

**Do not use Codex CLI as reviewer for this redo.** Codex may be used as the
worker if the user chooses, but the worker must not spawn nested `codex exec`
reviews. All independent review gates in this redo are Claude Code CLI
reviewer gates, using Opus/high effort where available.

The problem being fixed:

> Codex did not approve full `SYNTHESIS_MASTER` completeness. Codex approved
> the narrower scope presented in per-block review prompts.

The new rule:

> No block is DONE unless every canonical `SYNTHESIS_MASTER` row for that
> block has a ledger disposition and independent reviewer verification.

## Source Of Truth

Read these in order before doing any work:

| Order | File | Why |
|---:|---|---|
| 1 | `_status/PS_CRITICAL_WORKER_PROBLEM.md` | Incident report and root cause. |
| 2 | `_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md` | Plan states v5 = v4 + Runnable + Hermes + LF combined. |
| 3 | `_phase_2/wave_6/BUILDER_PROMPT.md` | No-deferral build contract. |
| 4 | `_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` | Canonical row-level scope. |
| 5 | `_phase_2/wave_6/TEST_DESIGN.md` | Promised per-block tests. |
| 6 | `_phase_2/wave_6/PS_Plan_Edge_Cases_Thinking.md` | 111 user scenarios and edge cases. |
| 7 | `_status/V5_RUNNABLE_PORT_LOG.md` | Existing port evidence. |
| 8 | `_status/V5_DESIGN_DECISIONS.md` | Existing ADR/decision evidence. |
| 9 | `_status/codex_reviews/` | Historical Codex review prompts/results. |
| 10 | `_status/r_tier_review_log.md` | Real-AWS R-tier evidence so far. |

## Folder Contract

| Path | Purpose |
|---|---|
| `00_MASTER_PROTOCOL.md` | Mandatory workflow for every worker/reviewer iteration. |
| `03_LEDGER_SCHEMA.md` | Required ledger columns and disposition rules. |
| `04_COMMANDS.md` | Known-good local commands for Codex and Claude CLI. |
| `06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md` | Current recommended prompt for a new Codex worker session. |
| `CLAUDE_REVIEWER_BASE_PROMPT.md` | Static base that every Claude review prompt must include. |
| `PS_WORKER_REVIEWER_DECISION.md` | Current worker/reviewer pairing and alternate-mode rules. |
| `PS_COMPACTION_RESUME_CHECKLIST.md` | How a compacted/interrupted worker picks up remaining work from files. |
| `_status/PS_AGENT_SELF_REFLECTION.md` | Mandatory anti-scope-drift checklist before any DONE/ready claim. |
| `_status/scripts/scope_audit.py` | Mechanical expected-row vs ledger/evidence gate. |
| `_status/scripts/verify_scope_completeness.ps1` | Repo-local strict wrapper for the scope gate. |
| `STATUS.md` | Current audit status and next action. |
| `PS_CLI_WOKER_DESIGN/` | Reusable worker-led loop design and recovery docs. |
| `blocks/` | One folder per block. Each block gets ledger, changelog, tests, decisions, prompts, and reviews. |
| `prompts/` | Exact prompts sent to worker/reviewer, copied before execution. |
| `reviews/` | Exact reviewer outputs. |
| `logs/` | CLI stdout/stderr logs for worker/reviewer commands. |
| `ledger/` | Cross-block master ledger outputs. |

Do not move historical files into this folder. Many existing docs reference
their current paths. Copy exact excerpts or link to them when needed.

## Current Recommended Workflow

Use the worker-led loop:

`06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md`

The abandoned full-auto PowerShell supervisor files were removed from the
active control folder. The primary pattern is one Codex worker coordinating
implementation and Claude review directly, while
every Claude prompt includes `CLAUDE_REVIEWER_BASE_PROMPT.md` so Claude
reconstructs canonical scope independently.

## Definition Of Done

A block is complete only when all are true:

1. Every `SYNTHESIS_MASTER` row for the block appears in that block's ledger.
2. Every row has one disposition: `SHIPPED`, `PARTIAL`, `MISSING`,
   `DEFERRED_USER_APPROVED`, `DROPPED_USER_APPROVED`, or `N/A_CONSTRAINT`.
3. Every non-shipped row has explicit user approval or remains ship-blocking.
4. Every shipped row has code evidence with file:line.
5. Every shipped row has test evidence or an explicit `NO_TEST_JUSTIFICATION`.
6. Every shipped row has PORT_LOG evidence or a new PORT_LOG row.
7. Every non-trivial adaptation has ADR evidence.
8. The exact worker prompt is saved under `prompts/`.
9. The exact Claude reviewer prompt is saved under `prompts/`.
10. The Claude reviewer independently reconstructs expected scope from
    `SYNTHESIS_MASTER`; it must not trust the worker's row list.
11. Reviewer verdict is `APPROVE`.
12. Local tests and any required R-tier tests are recorded.

## Current High-Risk Blocks

| Block | Reason |
|---|---|
| A | A-16 cold-cache microcompact and A-25 post-compact stub injection missing. |
| E+F | Actual block narrowed to env_block remaps; promised UI/status scope not proven. |
| L | Large error/retry/cache-break scope only partially proven. |
| N | Helpers exist; runtime parallel dispatch/wiring not fully proven. |
| K | Process tests exist; PORT_LOG/ADR closure weak. |
| T | v4 tool surface mostly built; Wave fold-ins need row audit. |
