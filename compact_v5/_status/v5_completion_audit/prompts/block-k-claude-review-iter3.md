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

Target block: K
Review purpose: closure review cleanup re-review after Claude iter2 LOW ledger findings

Your first task is still to read the required canonical context files from disk and reconstruct Block K scope directly from `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` before trusting any worker context below.

Canonical Block K source: `SYNTHESIS_MASTER.md:377-390`.
Expected rows: K-1 through K-8.

Prior usable reviews:

- Iter1: `reviews/block-k-claude-review-iter1.md` -> `APPROVE`, `READY_FOR_BLOCK_CLOSE_REVIEW`, 0 blockers.
- Iter2: `reviews/block-k-claude-review-iter2.md` -> `APPROVE_WITH_FIXES`, `READY_FOR_BLOCK_CLOSE_REVIEW`, 0 blockers.

Iter2 LOW findings to verify fixed:

1. `blocks/K/LEDGER.md` had `git_evidence=APPROVE` instead of git evidence.
2. `blocks/K/LEDGER.md` had `reviewer_verdict=pending` instead of a review verdict.
3. `blocks/K/LEDGER.md` action_needed still said to await scope audit and Claude review.

Cleanup performed after iter2:

- `blocks/K/LEDGER.md` now has `git_evidence` set to `working tree implementation pending Block K commit` for all 8 rows.
- `blocks/K/LEDGER.md` now has `reviewer_verdict` set to `APPROVE_WITH_FIXES_ITER2` for all 8 rows pending this iter3 re-review.
- `blocks/K/LEDGER.md` action_needed now says `Await Claude iter3 cleanup re-review and close checkpoint.`
- `blocks/K/STATUS.md`, `TESTS.md`, `REVIEWER_VERDICT.md`, and `ledger/CLAUDE_REVIEW_MATRIX.md` were updated to record iter2 and the cleanup.

Post-cleanup local gates:

- `pytest tests/integration/test_block_k_process.py -q`: PASS, 9 passed; log `logs/block-k-pytest-iter4.log`
- `scope_audit.py --block K`: PASS, 8 shipped, 0 blocking; log `logs/block-k-scope-audit-iter3.log`
- `scope_audit.py --block K --strict`: PASS, 8 shipped, 0 blocking; log `logs/block-k-scope-audit-strict-iter3.log`

Changed files since iter2 review to inspect:

- `compact_v5/_status/v5_completion_audit/blocks/K/LEDGER.md`
- `compact_v5/_status/v5_completion_audit/blocks/K/STATUS.md`
- `compact_v5/_status/v5_completion_audit/blocks/K/TESTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/K/REVIEWER_VERDICT.md`
- `compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md`
- New logs listed above.

Please verify:

1. The three iter2 LOW ledger findings are resolved.
2. Block K still has 8 expected rows, 8 ledger rows, 8 shipped, 0 blockers.
3. The block remains ready for close checkpoint, with no AWS/R-tier spend or tag/final-ready approval implied.

Return text only to stdout using the exact required output sections, including `VERDICT:` and `SHIP DECISION:`.