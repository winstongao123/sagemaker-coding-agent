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

Target block: T
Review purpose: closure review
Worker: Codex single writer
Reviewer: Claude Code read-only independent reviewer

Your first task remains the base-prompt task: read canonical context from disk and reconstruct Block T scope directly from `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` before trusting this worker context.

## Canonical Row List Claimed By Worker

Spec source: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:354-371`.
Expected rows: 12.

| Row | Worker disposition | Evidence summary |
|---|---|---|
| T-1 | SHIPPED | `notebook_edit` already-present v5 tool, now row-ledgered with Phase 4 executor/registry tests and PORT_LOG #123. |
| T-2 | SHIPPED | `view_image` already-present v5 tool, now row-ledgered with Phase 4 tests plus new 5 MB cap lock and PORT_LOG #124. |
| T-3 | SHIPPED | `semantic_search` TF-IDF index/search/status adaptation with Block T test and PORT_LOG #125. |
| T-4 | DROPPED_USER_APPROVED | Active `web_fetch` remains disabled per explicit 2026-05-03 user decision recorded in PORT_LOG #103-A and ADR-038; redo row #126. |
| T-5 | SHIPPED | `skill` and `skill_propose_patch` registry/executor behavior revalidated by skills suite; PORT_LOG #127. |
| T-6 | SHIPPED | `semantic_boolean` / `semantic_number` helpers added and `read_file` quoted offset/limit runtime path wired; PORT_LOG #128. |
| T-7 | SHIPPED | `FileTooLargeError` and `read_file_in_range` helper added and wired into `read_file`; PORT_LOG #129. |
| T-8 | SHIPPED | Lazy `lockfile` wrapper with portalocker/stdlib fallback added and tested; PORT_LOG #130. |
| T-9 | N/A_CONSTRAINT | v5 has no streaming UI placeholder layer for `tagMessagesWithToolUseID`; QueryEngine emits direct Bedrock `tool_result` blocks with `tool_use_id`; PORT_LOG #131. |
| T-10 | SHIPPED | API limits constants added: 5 MB image, 20 MB PDF, 100 PDF pages; `view_image` wired to 5 MB cap; PORT_LOG #132. |
| T-11 | SHIPPED | 200K aggregate per-message tool-result budget added before QueryEngine appends tool-result turns in both parallel and sequential paths; PORT_LOG #133. |
| T-12 | SHIPPED | XML tag constants added and used by `tool_search` and QueryEngine deferred-tool reminders; PORT_LOG #134. |

Worker ledger summary:

```text
EXPECTED_ROWS: 12
LEDGER_ROWS: 12
SHIPPED: 10
PARTIAL: 0
MISSING: 0
DEFERRED_USER_APPROVED: 0
DROPPED_USER_APPROVED: 1
N/A_CONSTRAINT: 1
SHIP_BLOCKING_ROWS: 0
```

## Changed Files To Inspect

Production/runtime:

- `compact_v5/MAIN/agent/runtime/tool_surface.py`
- `compact_v5/MAIN/agent/tools/read_file.py`
- `compact_v5/MAIN/agent/tools/view_image.py`
- `compact_v5/MAIN/agent/tools/tool_search.py`
- `compact_v5/MAIN/agent/core/query_engine.py`

Tests:

- `compact_v5/MAIN/agent/tests/integration/test_block_t.py`

Audit/status artifacts:

- `compact_v5/_status/v5_completion_audit/blocks/T/LEDGER.md`
- `compact_v5/_status/v5_completion_audit/blocks/T/STATUS.md`
- `compact_v5/_status/v5_completion_audit/blocks/T/TESTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/T/CHANGELOG.md`
- `compact_v5/_status/v5_completion_audit/blocks/T/DECISIONS.md`
- `compact_v5/_status/v5_completion_audit/blocks/T/WORKER_SELF_REVIEW.md`
- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md`
- `compact_v5/_status/V5_DESIGN_DECISIONS.md`
- `compact_v5/CHANGELOG.md`

Saved test/audit logs:

- `compact_v5/_status/v5_completion_audit/logs/block-t-py-compile-iter1.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-pytest-iter1.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-phase4-tools-regression.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-tool-search-regression.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-skills-regression.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-block-n-parallel-risk-regression.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-scope-audit-iter1.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-scope-audit-strict-iter1.log`

## Local Validation Claimed By Worker

- py_compile: PASS.
- `tests/integration/test_block_t.py -q`: 17 passed, 14 skipped.
- `tests/tools/test_phase4_mutating_tools.py -q`: 39 passed.
- `tests/unit/test_tool_search.py -q`: 32 passed.
- `tests/integration/test_skills.py -q`: 12 passed.
- Block N parallel-dispatch risk subset: 3 passed, 25 deselected.
- `scope_audit.py --block T`: zero ship-blocking rows, `READY_TO_REVIEW_CLOSE`.
- `scope_audit.py --block T --strict`: zero ship-blocking rows, `READY_TO_REVIEW_CLOSE`.

No AWS/R-tier test was run.

## User-Highlighted Parallel Dispatch Risk And Resolution

The user explicitly warned that the QueryEngine parallel dispatch fast path could bypass sequential dispatch bookkeeping: audit logging, repeat-call tracking, JSON argument repair, and per-tool forensics.

Resolution to verify independently:

- In `compact_v5/MAIN/agent/core/query_engine.py`, the parallel path calls `_dispatch_single_tool_call` for every parallel-safe call via `_execute_parallel_one`.
- The sequential path also calls `_dispatch_single_tool_call` for each call.
- `_dispatch_single_tool_call` owns unknown-tool/plan-mode audit logging, exec/repetition guard updates, JSON argument repair, approval checks, tool execution, success audit logging, tool_search discovery, and error audit/forensics.
- Existing Block N tests specifically lock the highlighted risk and were rerun as Block T evidence:
  - `test_query_engine_parallel_dispatch_audits_success_and_error`
  - `test_query_engine_parallel_dispatch_repairs_json_string_args`
  - `test_query_engine_parallel_dispatch_keeps_repetition_guard`
- Saved log: `compact_v5/_status/v5_completion_audit/logs/block-t-block-n-parallel-risk-regression.log` with result `3 passed, 25 deselected`.

Please explicitly include this risk in FINDINGS if you believe any checkpoint is still bypassed or insufficiently tested.

## Review Instructions

Independently verify the 12 expected rows from `SYNTHESIS_MASTER.md` against the ledger and evidence. Do not trust the worker table above except as navigation. Reject if any canonical row is missing, any shipped row lacks code/test/PORT_LOG evidence, any adaptation lacks ADR/decision evidence, or either T-4/T-9 disposition is not acceptable under the canonical rules.

Return text only to stdout with the exact sections required by the base prompt, including `VERDICT:` and `SHIP DECISION:`.
