# Block F2 Git Close Plan

Status: CLOSE_COMMIT_PUSHED_EVIDENCE_UPDATE_PENDING
Date: 2026-05-05

Target remote/branch:

- `sageagent/v5-build`

Specific files expected for close commit:

- `compact_v5/_status/v5_completion_audit/blocks/F2/STATUS.md`
- `compact_v5/_status/v5_completion_audit/blocks/F2/BASELINE.md`
- `compact_v5/_status/v5_completion_audit/blocks/F2/LEDGER.md`
- `compact_v5/_status/v5_completion_audit/blocks/F2/TESTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/F2/CHANGELOG.md`
- `compact_v5/_status/v5_completion_audit/blocks/F2/DECISIONS.md`
- `compact_v5/_status/v5_completion_audit/blocks/F2/PROMPTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/F2/REVIEWER_VERDICT.md`
- `compact_v5/_status/v5_completion_audit/blocks/F2/WORKER_SELF_REVIEW.md`
- `compact_v5/_status/v5_completion_audit/blocks/F2/GIT_CLOSE_PLAN.md`
- `compact_v5/_status/v5_completion_audit/prompts/block-f2-claude-review-iter1.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-f2-claude-review-iter1.md`
- `compact_v5/_status/v5_completion_audit/logs/block-f2-claude-smoke-before-review-iter1.out.txt`
- `compact_v5/_status/v5_completion_audit/logs/block-f2-claude-smoke-before-review-iter1.err.txt`
- `compact_v5/_status/v5_completion_audit/logs/block-f2-claude-review-iter1.log`
- `compact_v5/_status/v5_completion_audit/logs/block-f2-tests.log`
- `compact_v5/_status/v5_completion_audit/logs/block-f2-py-compile.log`
- `compact_v5/_status/v5_completion_audit/logs/block-f2-software-readiness.log`
- `compact_v5/_status/v5_completion_audit/logs/block-f2-scope-audit.log`
- `compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md`
- `compact_v5/_status/v5_completion_audit/STATUS.md`
- `compact_v5/_status/v5_completion_audit/TEST_CASE_PREP.md`
- `compact_v5/_status/v5_completion_audit/PS_SOFTWARE_PROJECT_WORKFLOW.md`
- `compact_v5/_status/v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md`
- `compact_v5/_status/v5_completion_audit/SOFTWARE_BUILDER_BLOCK_REVISIT_PLAN.md`
- `compact_v5/_status/v5_completion_audit/06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md`
- `compact_v5/MAIN/agent/tests/r_tier/test_software_project_workflow_contracts.py`
- `compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py`

Before commit:

1. Tests pass.
2. `scope_audit.py --block F2` reports zero ship-blocking rows.
3. Claude review contains `REVIEWED ROWS` with F2-1, `VERDICT:`, and `SHIP DECISION:`.
4. Status, reviewer verdict, matrix, and ledger are consistent.
5. Only the specific F2 file list is staged.

Close commit:

- Message: `Close block F2 budget continuation audit`
- Commit SHA: `6e3a0dd86ec49b869bf3b579d52daac79603af27`
- Push: `sageagent/v5-build`
- Remote verification: `git ls-remote sageagent refs/heads/v5-build` returned `6e3a0dd86ec49b869bf3b579d52daac79603af27`
- Tag: none created.

Evidence update scope:

- Records the close SHA in the F2 ledger/status.
- Refreshes the zero-cost software-project readiness result to `114 passed`.
- Includes the optimized AWS validation plan, software-builder block revisit plan, and command-consolidated software-project workflow docs/tests as pre-AWS hardening evidence.
