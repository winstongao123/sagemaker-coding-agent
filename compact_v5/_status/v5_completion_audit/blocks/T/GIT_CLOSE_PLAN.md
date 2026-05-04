# Block T Git Close Plan

Status: READY_TO_STAGE
Date: 2026-05-04

## Close Preconditions

- 12/12 canonical rows in `LEDGER.md`.
- 0 ship-blocking rows from final `scope_audit.py --block T`.
- Final strict scope audit passed.
- Local relevant tests passed; see `TESTS.md`.
- Claude iter3 returned `APPROVE` and `SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW`.
- No AWS/R-tier spend was run.
- No tag will be created without explicit user approval.

## Planned Staged Files

Specific-file staging only. Do not use `git add -A`.

- `compact_v5/CHANGELOG.md`
- `compact_v5/MAIN/agent/core/query_engine.py`
- `compact_v5/MAIN/agent/runtime/tool_surface.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_k_process.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_t.py`
- `compact_v5/MAIN/agent/tools/read_file.py`
- `compact_v5/MAIN/agent/tools/tool_search.py`
- `compact_v5/MAIN/agent/tools/view_image.py`
- `compact_v5/_status/V5_DESIGN_DECISIONS.md`
- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md`
- `compact_v5/_status/scripts/scope_audit.py`
- `compact_v5/_status/v5_completion_audit/blocks/T/CHANGELOG.md`
- `compact_v5/_status/v5_completion_audit/blocks/T/DECISIONS.md`
- `compact_v5/_status/v5_completion_audit/blocks/T/GIT_CLOSE_PLAN.md`
- `compact_v5/_status/v5_completion_audit/blocks/T/LEDGER.md`
- `compact_v5/_status/v5_completion_audit/blocks/T/PROMPTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/T/REVIEWER_VERDICT.md`
- `compact_v5/_status/v5_completion_audit/blocks/T/STATUS.md`
- `compact_v5/_status/v5_completion_audit/blocks/T/TESTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/T/WORKER_SELF_REVIEW.md`
- `compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md`
- `compact_v5/_status/v5_completion_audit/logs/block-t-block-n-parallel-risk-regression.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-claude-review-iter1.command.md`
- `compact_v5/_status/v5_completion_audit/logs/block-t-claude-review-iter1.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-claude-review-iter2.command.md`
- `compact_v5/_status/v5_completion_audit/logs/block-t-claude-review-iter2.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-claude-review-iter3.command.md`
- `compact_v5/_status/v5_completion_audit/logs/block-t-claude-review-iter3.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-doc-consistency-pass.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-final-scope-audit-strict.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-final-scope-audit.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-low-fix-block-k-process.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-low-fix-py-compile.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-phase4-tools-regression.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-pre-close-scope-audit-strict.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-post-ledger-field-scope-audit-strict.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-post-ledger-field-scope-audit.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-py-compile-iter1.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-pytest-iter1.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-scope-audit-iter1.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-scope-audit-iter2.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-scope-audit-strict-iter1.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-scope-audit-strict-iter2.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-skills-regression.log`
- `compact_v5/_status/v5_completion_audit/logs/block-t-tool-search-regression.log`
- `compact_v5/_status/v5_completion_audit/prompts/block-t-claude-review-iter1.md`
- `compact_v5/_status/v5_completion_audit/prompts/block-t-claude-review-iter2.md`
- `compact_v5/_status/v5_completion_audit/prompts/block-t-claude-review-iter3.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-t-claude-review-iter1.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-t-claude-review-iter2.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-t-claude-review-iter3.md`

## Commit

Planned commit message: `v5/block-t: complete tool surface closure audit`

Commit SHA: pending.

Push result: pending.

Post-push git status: pending.

Tag: no tag created; explicit user approval required for any tag.
