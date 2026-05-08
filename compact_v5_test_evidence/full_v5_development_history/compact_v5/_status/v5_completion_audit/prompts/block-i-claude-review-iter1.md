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

Target block: I
Review purpose: closure review

Important independence rule: Codex has not pasted repository implementation or test file contents here. Treat this appendix only as navigation. You must read repository files from disk yourself using read-only tools before deciding.

Expected canonical row ids reconstructed by worker from `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md`:

- I-1
- I-2
- I-3
- I-4
- I-5
- I-6
- I-7
- I-8
- I-9
- I-10
- I-11
- I-12
- I-13

Required row coverage in stdout:

- `REVIEWED ROWS` must include exactly one entry for each row I-1 through I-13.
- Output must include `VERDICT:` and `SHIP DECISION:`.

Primary files to inspect:

- `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md`
- `compact_v5/_status/v5_completion_audit/blocks/I/STATUS.md`
- `compact_v5/_status/v5_completion_audit/blocks/I/BASELINE.md`
- `compact_v5/_status/v5_completion_audit/blocks/I/LEDGER.md`
- `compact_v5/_status/v5_completion_audit/blocks/I/TESTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/I/CHANGELOG.md`
- `compact_v5/_status/v5_completion_audit/blocks/I/DECISIONS.md`
- `compact_v5/_status/v5_completion_audit/blocks/I/WORKER_SELF_REVIEW.md`
- `compact_v5/_status/v5_completion_audit/blocks/I/GIT_CLOSE_PLAN.md`
- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md`
- `compact_v5/_status/V5_DESIGN_DECISIONS.md`
- `compact_v5/CHANGELOG.md`
- `compact_v5/_status/v5_completion_audit/PS_SOFTWARE_PROJECT_WORKFLOW.md`

Implementation and test paths to inspect:

- `compact_v5/MAIN/agent/skills/manager.py`
- `compact_v5/MAIN/agent/tools/edit_file.py`
- `compact_v5/MAIN/agent/core/query_engine.py`
- `compact_v5/MAIN/agent/tools/skill.py`
- `compact_v5/MAIN/agent/tools/skill_propose_patch.py`
- `compact_v5/MAIN/agent/commands.py`
- `compact_v5/MAIN/agent/skills/init/SKILL.md`
- `compact_v5/MAIN/agent/skills/init-verifiers/SKILL.md`
- `compact_v5/MAIN/agent/skills/skillify/SKILL.md`
- `compact_v5/MAIN/agent/skills/debug/SKILL.md`
- `compact_v5/MAIN/agent/skills/remember/SKILL.md`
- `compact_v5/MAIN/agent/tests/integration/test_block_i.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_d.py`
- `compact_v5/MAIN/agent/tests/integration/test_skills.py`

Local test/log paths to inspect:

- `compact_v5/_status/v5_completion_audit/logs/block-i-tests.log`
- `compact_v5/_status/v5_completion_audit/logs/block-i-py-compile.log`
- `compact_v5/_status/v5_completion_audit/logs/block-i-scope-audit.log`

Concise worker navigation summary:

- Block I has 13 canonical rows: I-1 through I-13.
- Worker believes existing implementation evidence covers I-1 through I-11 and I-13 from the earlier Block I/D work.
- Worker patched I-12 during this redo so it is no longer treated as deferred. The patch is intentionally small: bracketed CSV-like scalars, simple quoted tokens, one-level brace expansion for path globs, and non-string description coercion. It does not execute shell commands from skill markdown.
- Worker updated PORT_LOG row #194 and ADR-029 notes for I-12.
- Worker ran combined Block I/D/skills tests with `PYTHONPATH=compact_v5/MAIN/agent`: 66 passed, 1 skipped.
- Worker ran py_compile for Block I implementation/test paths: PASS.
- Worker ran `scope_audit.py --block I`: READY_TO_REVIEW_CLOSE, 13 shipped, 0 ship-blocking rows.
- Worker claims no AWS/R-tier pass and no `/project-*` command was added.

Review focus:

- Reconstruct Block I directly from `SYNTHESIS_MASTER.md` and verify every row I-1 through I-13.
- Check that I-12 is now concrete enough for SHIPPED and is not relying on a historical deferral.
- Check that I-7/I-8/I-9/I-13 folded-Block-D evidence is valid for Block I rows.
- Check code/test/PORT_LOG/ADR evidence for every shipped row.
- Check no AWS/R-tier pass is claimed and no overlapping `/project-*` commands were added.
- Return text only to stdout.
