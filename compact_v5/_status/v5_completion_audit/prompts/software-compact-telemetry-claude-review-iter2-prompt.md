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

# SOFTWARE-COMPACT-TELEMETRY Cleanup Re-Review Prompt Iter2

You are re-reviewing only the two LOW cleanup findings from:

- `compact_v5/_status/v5_completion_audit/reviews/software-compact-telemetry-claude-review-iter1.md`

Canonical SOFTWARE-COMPACT-TELEMETRY scope is still:

- `compact_v5/_status/v5_completion_audit/THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`
- `compact_v5/_status/v5_completion_audit/PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md`
- `compact_v5/_status/v5_completion_audit/BLOCK_ORDER_AND_COVERAGE.md`

Read files from disk. Do not trust this prompt except as navigation.

Cleanup fixes to verify:

1. `compact_v5/MAIN/agent/core/query_engine.py`
   - iter1 finding: `compact_auto_start.max_context_tokens` would be redacted by `runtime/audit.py`.
   - worker fix: renamed the parameter to `max_context_count`.

2. `compact_v5/_status/v5_completion_audit/blocks/SOFTWARE-COMPACT-TELEMETRY/LEDGER.md`
   - iter1 finding: row 4 used `N/A_CONSTRAINT` for the DS3-S9 TEST_HARDENING_ONLY/no-goal branch.
   - worker fix: row 4 is now `SHIPPED`, with rationale citing the third-scan TEST_HARDENING_ONLY branch and local forced micro/auto compaction tests.

Updated logs to inspect:

- `compact_v5/_status/v5_completion_audit/logs/software-compact-telemetry-tests.log`
- `compact_v5/_status/v5_completion_audit/logs/software-compact-telemetry-build-telemetry-tests.log`
- `compact_v5/_status/v5_completion_audit/logs/software-compact-telemetry-regression-tests.log`
- `compact_v5/_status/v5_completion_audit/logs/software-compact-telemetry-py-compile.log`

Return the standard required sections from the base prompt. Focus findings on whether the two iter1 LOW findings are withdrawn or still apply. If both are fixed and no new blocker appears, return:

- `VERDICT: APPROVE`
- `SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW`