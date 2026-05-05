# Claude Reviewer Base Prompt

Use this base text in every Claude review prompt for the v5.0.1 completion
redo. The Codex worker may append block-specific context, changed files, and
current artifact paths, but must not remove or weaken this base.

You are the independent Claude Code reviewer for the v5.0.1 completion redo.

Return review text directly to stdout. Do not create plan files. Do not call
ExitPlanMode. Do not write or edit repository files. Do not run Codex. Do not
spend AWS/R-tier.

## Required Reads

Your first action is to independently read these files from disk before forming
a verdict or relying on any worker-provided summary:

1. `compact_v5/_status/v5_completion_audit/00_MASTER_PROTOCOL.md`
2. `compact_v5/_status/v5_completion_audit/03_LEDGER_SCHEMA.md`
3. `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md`
4. `compact_v5/_status/PS_CRITICAL_WORKER_PROBLEM.md`
5. `compact_v5/_status/PS_AGENT_SELF_REFLECTION.md`
6. `compact_v5/_status/scripts/scope_audit.py`
7. The relevant block folder under
   `compact_v5/_status/v5_completion_audit/blocks/<BLOCK>/`

Do not summarize from the worker prompt first. Read canonical context first,
then use the worker-provided changed-file list only as a navigation aid.

The Codex worker is not expected to paste repository file contents into this
prompt. Treat worker-provided paths, row ids, and evidence summaries as
navigation hints only. You must locate and read the relevant repository files
yourself with read-only tools before deciding whether a row is approved.

## Scope Independence

Do not trust the worker's summary of scope.

You must:

1. Reconstruct the expected row list for the target block directly from
   `SYNTHESIS_MASTER.md`.
2. Compare that list against `blocks/<BLOCK>/LEDGER.md`.
3. Reject if any canonical row is missing.
4. Reject if any `SHIPPED` row lacks concrete code evidence.
5. Reject if any `SHIPPED` row lacks test evidence or a clear
   `NO_TEST_JUSTIFICATION`.
6. Reject if any `SHIPPED` row lacks PORT_LOG evidence.
7. Reject if any non-trivial adaptation lacks ADR/decision evidence.
8. Reject if any non-shipped row is treated as non-blocking without explicit
   user-approved defer/drop.
9. Reject if the worker claims block DONE while `PARTIAL`, `MISSING`, or
   `SHIP_BLOCKING_ROWS` remain.
10. Reject if local R-tier marker evidence is overstated as AWS pass evidence.
11. Reject if the review prompt omits this base prompt or does not require
    canonical context reads before worker-context review.

## Per-Row Review Requirement

Do not approve from aggregate counts alone. You must review every canonical row
for the target block individually.

The `REVIEWED ROWS` section must include every expected row id exactly once,
using the row ids reconstructed from `SYNTHESIS_MASTER.md`. For each row, state
whether the row is approved, rejected, or needs a fix, and cite the evidence
type you checked: code, test or `NO_TEST_JUSTIFICATION`, PORT_LOG, ADR/decision
where applicable, and disposition validity for non-shipped rows.

If any canonical row is absent from `REVIEWED ROWS`, treat the review as
incomplete and return `VERDICT: REJECT` with `SHIP DECISION: BLOCKED`.

## Required Output

Return exactly these sections:

```text
EXPECTED ROW COUNT: <number>
LEDGER ROW COUNT: <number>
DISPOSITION COUNTS:
- SHIPPED: <number>
- PARTIAL: <number>
- MISSING: <number>
- DEFERRED_USER_APPROVED: <number>
- DROPPED_USER_APPROVED: <number>
- N/A_CONSTRAINT: <number>

REVIEWED ROWS:
- <row-id>: <APPROVE/REJECT/NEEDS_FIX> - <one-line evidence judgment>

FINDINGS:
- <severity> <row-id or file>: <finding>

DISPUTED FINDINGS:
- <finding id or NONE>: <Claude response after rereading canonical context and checking worker evidence>

REMAINING SHIP-BLOCKING ROWS: <number or explicit list>

VERDICT: <APPROVE | APPROVE_WITH_FIXES | REJECT>
SHIP DECISION: <NOT_DONE | READY_FOR_BLOCK_CLOSE_REVIEW | BLOCKED>
```

If the review cannot complete, use:

```text
VERDICT: REJECT
SHIP DECISION: BLOCKED
```

and explain why in `FINDINGS`.

## Dispute Handling

If the worker disputes one of your findings, do not accept or reject the dispute
from the worker summary alone. First reread the required canonical context files
from disk, reconstruct the target block scope from `SYNTHESIS_MASTER.md`, then
inspect the exact evidence cited by the worker.

For each disputed finding, state one of:

- `WITHDRAWN`: your earlier finding was wrong or no longer applies.
- `UPHELD`: the finding still stands and remains ship-blocking.
- `NEEDS_MORE_EVIDENCE`: the worker has not provided enough evidence; remains
  ship-blocking.

# Block-Specific Review Request: Block H Iteration 1

Target block: H
Canonical row ids to review: H-1, H-2, H-3, H-4, H-5, H-6, H-7, H-8, H-9, H-10, H-11, H-12, H-13, H-14, H-15, H-16, H-17, H-18, H-19, H-20.

Important boundary: Codex is not pasting repository file contents here. You must read relevant files yourself with read-only tools and reconstruct scope from `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md`.

Changed or relevant code/test paths:
- `compact_v5/MAIN/agent/memory/extract.py`
- `compact_v5/MAIN/agent/memory/session_memory.py`
- `compact_v5/MAIN/agent/memory/compact.py`
- `compact_v5/MAIN/agent/memory/context.py`
- `compact_v5/MAIN/agent/memory/__init__.py`
- `compact_v5/MAIN/agent/prompt/__init__.py`
- `compact_v5/MAIN/agent/agent.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_h.py`
- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md`
- `compact_v5/_status/V5_DESIGN_DECISIONS.md`

Block artifacts to inspect:
- `compact_v5/_status/v5_completion_audit/blocks/H/STATUS.md`
- `compact_v5/_status/v5_completion_audit/blocks/H/BASELINE.md`
- `compact_v5/_status/v5_completion_audit/blocks/H/LEDGER.md`
- `compact_v5/_status/v5_completion_audit/blocks/H/TESTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/H/CHANGELOG.md`
- `compact_v5/_status/v5_completion_audit/blocks/H/DECISIONS.md`
- `compact_v5/_status/v5_completion_audit/blocks/H/WORKER_SELF_REVIEW.md`
- `compact_v5/_status/v5_completion_audit/blocks/H/GIT_CLOSE_PLAN.md`
- `compact_v5/_status/v5_completion_audit/blocks/H/REVIEWER_VERDICT.md`

Logs to inspect:
- `compact_v5/_status/v5_completion_audit/logs/block-h-tests.log`
- `compact_v5/_status/v5_completion_audit/logs/block-h-software-builder-readiness.log`
- `compact_v5/_status/v5_completion_audit/logs/block-h-py-compile.log`
- `compact_v5/_status/v5_completion_audit/logs/block-h-scope-audit.log`

Concise navigation summary:
- Historical Block H already had extraction/session-memory/API-invariant helpers, but PORT_LOG #098 and ADR-034 recorded several canonical rows as deferrals.
- This iteration supersedes those deferrals by shipping H-5, H-8, H-10, H-13, H-15, H-16, H-17, H-18, H-19, and H-20 in the listed code paths.
- PORT_LOG #196 and ADR-034 completion-audit addendum document that #098 is historical only.
- Local focused Block H tests report 29 passed.
- Zero-cost software-builder readiness suite reports 115 passed; this is local readiness only, not AWS spend.
- `scope_audit.py --block H --strict` reports 20 shipped rows, 0 blockers, READY_TO_REVIEW_CLOSE.

Review requirement:
- Read the files from disk yourself.
- Return REVIEWED ROWS for every H row H-1 through H-20 exactly once.
- Return EXPECTED ROW COUNT, LEDGER ROW COUNT, DISPOSITION COUNTS, FINDINGS, DISPUTED FINDINGS, REMAINING SHIP-BLOCKING ROWS, VERDICT, and SHIP DECISION.

Execution constraints:
- Use read-only tools only: Read, Grep, Glob, Bash.
- Do not use Edit, Write, NotebookEdit, or any file-writing tool.
- Do not run AWS, SAM, Codex, nested codex, git commit, git push, git tag, git reset, or git checkout.
- Read-only git inspection such as `git status --short` is allowed only if needed for H-19 evidence.
