# Master Protocol

Status: MANDATORY
Applies to: every v5 completion audit, implementation, review, and test.

## Non-Negotiable Rule

The reviewer must independently reconstruct the expected scope from
`SYNTHESIS_MASTER.md`. The worker's prompt, changelog, code diff, and test
list are not allowed to define the scope.

This directly fixes the prior failure mode:

> Codex approved the scope presented to it, not the full canonical scope.

## Reviewer Policy

Do not run Codex CLI as reviewer in this redo. The reviewer is Claude Code CLI
only. This avoids recursive Codex-worker -> Codex-reviewer crashes and prevents
the old narrowed-prompt review path from reappearing.

## Workflow

### Phase 0 - Baseline

Before any code changes:

1. Record `git status --short`.
2. Record `git rev-parse HEAD`.
3. Record the latest `v5.0.1-block-*` tags.
4. Run zero-cost gates that are relevant:
   - `py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root .`
   - `cd compact_v5/MAIN/agent && py -3.11 -m pytest tests/integration/test_block_<block>.py -q`
5. Save outputs in `blocks/<block>/BASELINE.md`.

### Phase 1 - Row Ledger Audit

For the target block:

1. Parse every row in `SYNTHESIS_MASTER.md` for that block.
2. For each row, search:
   - production code
   - unit/integration/r_tier tests
   - `V5_RUNNABLE_PORT_LOG.md`
   - `V5_DESIGN_DECISIONS.md`
   - `CHANGELOG.md`
   - `V5_BUILD_STATUS.md`
   - historical Codex review prompts/results
   - git log/tag/blame evidence
3. Fill `blocks/<block>/LEDGER.md`.
4. Do not implement until the row ledger is complete enough to identify
   shipped vs missing vs partial rows.

### Phase 2 - Implementation

For every row marked `MISSING` or `PARTIAL`:

1. Decide whether it is required for v5.0.1 ship.
2. If required, implement it.
3. If not required, stop and ask the user for explicit drop/defer approval.
4. Add or update tests.
5. Update PORT_LOG and ADR as needed.
6. Update block changelog.

### Phase 3 - Worker Self-Review

The worker must write `blocks/<block>/WORKER_SELF_REVIEW.md` with:

| Required section | Contents |
|---|---|
| Scope regenerated | List all expected row IDs from `SYNTHESIS_MASTER`. |
| Evidence summary | Row counts by disposition. |
| Tests run | Exact commands and outcomes. |
| Git evidence | Commits/tags/file-line refs. |
| Open risk | Anything not fully proven. |

### Phase 4 - Independent Reviewer

Claude reviewer must:

1. Read `SYNTHESIS_MASTER.md` directly.
2. Regenerate the expected row list independently.
3. Compare regenerated rows to `blocks/<block>/LEDGER.md`.
4. Reject if any canonical row is absent.
5. Reject if any shipped row lacks code evidence.
6. Reject if any shipped runtime row lacks test evidence unless the
   `NO_TEST_JUSTIFICATION` is convincing.
7. Reject if any defer/drop lacks explicit user approval.
8. Reject if review prompt scope is narrower than `SYNTHESIS_MASTER`.

### Phase 5 - Close

A block closes only when:

1. Worker final status is `READY_FOR_REVIEW`.
2. Claude reviewer verdict is `APPROVE`.
3. Worker ledger and Claude reviewer row counts match.
4. Tests pass.
5. PORT_LOG/ADR/changelog/status docs are updated.
6. User approves.

### Resume / Compaction Rule

After context compaction, terminal interruption, or a new worker session, the
worker must not continue from memory. It must follow
`PS_COMPACTION_RESUME_CHECKLIST.md`:

1. Reread the worker prompt, master protocol, ledger schema, reviewer base
   prompt, global status, block status, block ledger, worker self-review, latest
   reviewer verdict, and review matrix.
2. Rerun `py -3.11 compact_v5/_status/scripts/scope_audit.py --block <BLOCK>`.
3. Compare expected row count, ledger row count, shipped/partial/missing counts,
   ship-blocking rows, latest usable Claude verdict, and the block heartbeat.
4. Inspect `git status --short` and continue with existing uncommitted changes
   without reverting them.
5. If the sources disagree, stop and write
   `blocks/<BLOCK>/RESUME_CONFLICT.md`. Do not code, review, or close until the
   conflict is reconciled.

## Required Artifacts Per Block

Each block folder must contain:

| File | Required |
|---|---|
| `BASELINE.md` | yes |
| `LEDGER.md` | yes |
| `CHANGELOG.md` | yes |
| `DECISIONS.md` | yes, may link ADRs |
| `TESTS.md` | yes |
| `PROMPTS.md` | yes |
| `WORKER_SELF_REVIEW.md` | yes |
| `REVIEWER_VERDICT.md` | yes |
| `STATUS.md` | yes |

## Disposition Meanings

| Disposition | Meaning |
|---|---|
| `SHIPPED` | Implemented, tested or justified, logged, reviewed. |
| `PARTIAL` | Some code exists but row is not fully satisfied. Ship-blocking unless explicitly accepted. |
| `MISSING` | No implementation evidence. Ship-blocking unless explicitly dropped/deferred by user. |
| `DEFERRED_USER_APPROVED` | User explicitly approved defer. Must cite exact approval. |
| `DROPPED_USER_APPROVED` | User explicitly approved drop. Must cite exact approval. |
| `N/A_CONSTRAINT` | Inapplicable due hard constraint, with source citation. |
