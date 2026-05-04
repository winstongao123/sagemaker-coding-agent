# Block E+F Claude Review Iter2 Prompt

You are re-reviewing Block E+F after worker fixes for Claude iter1 LOW findings.

Repository root: `D:\Github\sagemaker-coding-agent`

Do not write or edit files. Do not run Codex. Do not run AWS/R-tier spend. Do
not run git commit/push/tag/reset/checkout. Use read-only inspection and local
non-AWS tests/audits only.

First read the canonical control files from disk and reconstruct Block E+F
scope from `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` before
trusting any worker summary below.

Additional required reads for this handoff:

1. `AGENTS.md`
2. `compact_v5/_status/v5_completion_audit/06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md`
3. `compact_v5/_status/v5_completion_audit/PS_COMPACTION_RESUME_CHECKLIST.md`
4. `compact_v5/_status/v5_completion_audit/BLOCK_ORDER_AND_COVERAGE.md`
5. `compact_v5/_status/v5_completion_audit/CLAUDE_REVIEWER_BASE_PROMPT.md`
6. `compact_v5/_status/v5_completion_audit/reviews/block-e-f-claude-review-iter1.md`

## Base Prompt

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

## Iter2 Review Target

Target block: `E+F`

This is a re-review after Claude iter1:

- Iter1 review path: `compact_v5/_status/v5_completion_audit/reviews/block-e-f-claude-review-iter1.md`
- Iter1 verdict: `APPROVE`
- Iter1 ship decision: `READY_FOR_BLOCK_CLOSE_REVIEW`
- Iter1 LOW EF-3: signature stripping breadth.
- Iter1 LOW EF-5: first-call-only `tool_gen_callback`.
- Iter1 tooling note: `scope_audit.py` prints `N/A: 0` because of a count-key
  display bug; row-level classification and ship-blocking verdict were still
  correct. This is outside Block E+F ownership unless you determine otherwise.

Worker claims the two local EF findings are now fixed:

- EF-3: `strip_signature_blocks` now removes any top-level thinking-block key
  whose normalized name contains `signature`, plus encrypted-content variants,
  and removes `redacted_thinking` blocks.
- EF-5: `_notify_tool_generation` now emits an event for every visible tool
  call before dispatch, rather than only the first call.

Do not trust these claims until you inspect code, tests, and logs.

## Worker Evidence Navigation

Changed files to inspect:

- `compact_v5/MAIN/agent/core/query_engine.py`
- `compact_v5/MAIN/agent/core/formatting.py`
- `compact_v5/MAIN/agent/core/__init__.py`
- `compact_v5/MAIN/agent/runtime/config.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_e_f.py`
- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md`
- `compact_v5/_status/V5_DESIGN_DECISIONS.md`
- `compact_v5/_status/v5_completion_audit/blocks/E+F/LEDGER.md`
- `compact_v5/_status/v5_completion_audit/blocks/E+F/TESTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/E+F/CHANGELOG.md`
- `compact_v5/_status/v5_completion_audit/blocks/E+F/DECISIONS.md`
- `compact_v5/_status/v5_completion_audit/blocks/E+F/WORKER_SELF_REVIEW.md`
- `compact_v5/_status/v5_completion_audit/blocks/E+F/REVIEWER_VERDICT.md`
- `compact_v5/_status/v5_completion_audit/blocks/E+F/STATUS.md`

Saved iter2 logs to inspect:

- `compact_v5/_status/v5_completion_audit/logs/block-e-f-py-compile-iter2.log`
- `compact_v5/_status/v5_completion_audit/logs/block-e-f-pytest-iter2.log`
- `compact_v5/_status/v5_completion_audit/logs/block-e-f-query-f2-regression-iter2.log`
- `compact_v5/_status/v5_completion_audit/logs/block-e-f-scope-audit-iter2.log`
- `compact_v5/_status/v5_completion_audit/logs/block-e-f-scope-audit-strict-iter2.log`

Review questions:

1. Did the worker preserve all eight canonical Block E+F rows while applying
   the LOW fixes?
2. Are EF-3 and EF-5 LOW findings fixed without new regressions?
3. Do tests and scope-audit logs support the updated ledger?
4. Are there any remaining ship-blocking rows or fresh LOW findings that should
   be fixed before the specific-file git checkpoint?
