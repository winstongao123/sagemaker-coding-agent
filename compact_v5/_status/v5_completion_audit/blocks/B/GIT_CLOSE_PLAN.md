# Block B Git Close Plan

Status: READY_FOR_CLOSE_COMMIT
Date: 2026-05-05

Close preconditions:

1. 16/16 canonical rows are in `LEDGER.md`.
2. 0 ship-blocking rows remain from `scope_audit.py --block B`.
3. Relevant local tests pass.
4. Usable Claude approval has `SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW`.
5. Documentation consistency pass from `PS_CLI_WOKER_DESIGN/GIT_CHECKPOINT_POLICY.md` passes.
6. Close artifacts are updated.

No tag will be created without explicit user approval.

## Preconditions

- Ledger rows: 16/16.
- Ship-blocking rows: 0.
- Latest usable Claude verdict: iter8 `APPROVE`.
- Latest usable ship decision: iter8 `READY_FOR_BLOCK_CLOSE_REVIEW`.
- Documentation consistency pass: PASS, `logs/block-b-doc-consistency-pass.log`.
- Final strict scope audit: PASS, `logs/block-b-pre-close-scope-audit-strict.log`.
- No AWS/R-tier spend, no tag, no force push, no Codex review, no nested `codex exec`.

## Planned Staged Files

Stage only this Block B-specific file list:

- `compact_v5/MAIN/agent/core/__init__.py`
- `compact_v5/MAIN/agent/core/budget.py`
- `compact_v5/MAIN/agent/runtime/bedrock_client.py`
- `compact_v5/MAIN/agent/runtime/tokens.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_b.py`
- `compact_v5/MAIN/agent/tests/utils/__init__.py`
- `compact_v5/MAIN/agent/tests/utils/lorem.py`
- `compact_v5/_status/V5_DESIGN_DECISIONS.md`
- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md`
- `compact_v5/_status/v5_completion_audit/STATUS.md`
- `compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md`
- `compact_v5/_status/v5_completion_audit/blocks/B/BASELINE.md`
- `compact_v5/_status/v5_completion_audit/blocks/B/CHANGELOG.md`
- `compact_v5/_status/v5_completion_audit/blocks/B/DECISIONS.md`
- `compact_v5/_status/v5_completion_audit/blocks/B/GIT_CLOSE_PLAN.md`
- `compact_v5/_status/v5_completion_audit/blocks/B/LEDGER.md`
- `compact_v5/_status/v5_completion_audit/blocks/B/PROMPTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/B/REVIEWER_VERDICT.md`
- `compact_v5/_status/v5_completion_audit/blocks/B/REVIEW_LOOP_BLOCKED.md`
- `compact_v5/_status/v5_completion_audit/blocks/B/STATUS.md`
- `compact_v5/_status/v5_completion_audit/blocks/B/TESTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/B/WORKER_SELF_REVIEW.md`
- `compact_v5/_status/v5_completion_audit/logs/block-b-baseline-scope-audit.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-bedrock-unit-iter1.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-claude-review-iter1.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-claude-review-iter2.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-claude-review-iter3.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-claude-review-iter4.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-claude-review-iter5.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-claude-review-iter6.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-claude-review-iter7.command.md`
- `compact_v5/_status/v5_completion_audit/logs/block-b-claude-review-iter7.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-claude-review-iter8.command.md`
- `compact_v5/_status/v5_completion_audit/logs/block-b-claude-review-iter8.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-doc-consistency-pass.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-geo-pricing-iter1.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-monitor-claude-fullprompt-test.err.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-monitor-claude-fullprompt-test.out.md`
- `compact_v5/_status/v5_completion_audit/logs/block-b-pre-close-scope-audit-strict.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-py-compile-iter1.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-pytest-after-hermetic-fix.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-pytest-existing.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-pytest-iter1.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-scope-audit-after-implementation.log`
- `compact_v5/_status/v5_completion_audit/logs/block-b-scope-audit-after-ledger-init.log`
- `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter1-prompt.md`
- `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter2-prompt.md`
- `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter3-prompt.md`
- `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter4-prompt.md`
- `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter5-prompt.md`
- `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter6-prompt.md`
- `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter7-prompt.md`
- `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter8-prompt.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-b-claude-review-iter1.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-b-claude-review-iter2.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-b-claude-review-iter3.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-b-claude-review-iter4.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-b-claude-review-iter5.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-b-claude-review-iter6.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-b-claude-review-iter7.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-b-claude-review-iter8.md`

## Close Commit

- Commit message: `v5/block-b: complete token accounting closure audit`
- Commit SHA: pending close commit.
- Push remote/branch: `sageagent v5-build`
- Push result: pending close push.
- Post-push git status: pending close push.

## Evidence Update Commit

- Commit message: `v5/block-b: record checkpoint evidence`
- Evidence commit SHA: pending evidence update.
- Push remote/branch: `sageagent v5-build`
- Push result: pending evidence push.
- Post-push git status: pending evidence push.
