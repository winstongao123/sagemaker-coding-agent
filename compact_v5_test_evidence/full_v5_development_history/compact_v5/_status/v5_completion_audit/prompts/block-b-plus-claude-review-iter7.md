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

---

# Block-Specific Review Request

Target block: `B+`

Review purpose: `closure re-review after iter6 B+1 fix`

This prompt intentionally does not paste repository implementation, ledger,
status, test, PORT_LOG, ADR, changelog, or review file contents. Use the paths
below only as navigation hints. You must read the relevant files yourself from
disk using read-only tools before forming a verdict.

First, reconstruct Block B+ scope directly from:

- `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md`

Expected row ids to verify independently and include exactly once in
`REVIEWED ROWS`:

- B+1
- B+2
- B+3
- B+4
- B+5
- B+6
- B+7
- B+8

Changed implementation/test files to inspect:

- `compact_v5/MAIN/agent/runtime/tokens.py`
- `compact_v5/MAIN/agent/commands.py`
- `compact_v5/MAIN/agent/ui/chat_ui.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_b_plus.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_d.py`
- `compact_v5/MAIN/agent/core/compactor.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_a.py`
- `compact_v5/MAIN/agent/runtime/config.py`
- `compact_v5/MAIN/agent/runtime/session.py`

Block artifacts and audit docs to inspect:

- `compact_v5/_status/v5_completion_audit/blocks/B+/LEDGER.md`
- `compact_v5/_status/v5_completion_audit/blocks/B+/STATUS.md`
- `compact_v5/_status/v5_completion_audit/blocks/B+/TESTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/B+/CHANGELOG.md`
- `compact_v5/_status/v5_completion_audit/blocks/B+/DECISIONS.md`
- `compact_v5/_status/v5_completion_audit/blocks/B+/WORKER_SELF_REVIEW.md`
- `compact_v5/_status/v5_completion_audit/blocks/B+/REVIEWER_VERDICT.md`
- `compact_v5/_status/v5_completion_audit/blocks/B+/REVIEW_LOOP_BLOCKED.md`
- `compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md`
- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md`
- `compact_v5/_status/V5_DESIGN_DECISIONS.md`
- `compact_v5/CHANGELOG.md`

Test and log paths to inspect:

- `compact_v5/_status/v5_completion_audit/blocks/B+/TESTS.md`
- `compact_v5/_status/v5_completion_audit/logs/block-b-plus-scope-audit-post-ledger.md`
- `compact_v5/_status/v5_completion_audit/logs/block-b-plus-claude-review-iter6.command.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-b-plus-claude-review-iter6.md`
- `compact_v5/_status/v5_completion_audit/logs/block-b-plus-claude-review-iter6.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-plus-claude-smoke-before-review-iter6.command.md`

Concise worker navigation summary:

- Claude iter6 was the first usable B+ review. It reviewed B+1 through B+8,
  approved B+2 through B+8, and returned `APPROVE_WITH_FIXES` with
  `SHIP DECISION: BLOCKED` because B+1 had no production `/resume` call site.
- Worker reports the B+1 gap is now fixed through production `/save` and
  `/resume` commands, with Chat UI command dispatch passing Agent context and
  tests covering both context-message and Agent-message restore. Treat this as
  a navigation hint only; inspect the files yourself.
- Worker reports local validation after the fix: Block B+ suite 29 passed,
  Block D command suite 22 passed, targeted B+5 advisor tests 2 passed,
  py_compile passed, and `scope_audit.py --block B+` returned
  `READY_TO_REVIEW_CLOSE`. Confirm from files and evidence rather than trusting
  this summary.
- B+ is not closed and no B+ block-close commit/push has been made yet.

Do not run AWS/R-tier, Codex, git commit/push/tag/reset/checkout, or write/edit
files. Return text only to stdout. Your output must include `REVIEWED ROWS`
with B+1 through B+8 exactly once, `VERDICT:`, and `SHIP DECISION:`.
