# Block G Git Close Plan

Status: READY_FOR_SPECIFIC_FILE_COMMIT
Date: 2026-05-05

Target remote/branch:

- `sageagent/v5-build`

Specific files expected for close commit:

- `compact_v5/CHANGELOG.md`
- `compact_v5/MAIN/agent/subagent/agent_memory.py`
- `compact_v5/MAIN/agent/subagent/agent_types.py`
- `compact_v5/MAIN/agent/subagent/spawn.py`
- `compact_v5/MAIN/agent/subagent/__init__.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_g.py`
- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md`
- `compact_v5/_status/V5_DESIGN_DECISIONS.md`
- `compact_v5/_status/v5_completion_audit/blocks/G/`
- `compact_v5/_status/v5_completion_audit/prompts/block-g-claude-review-iter1.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-g-claude-review-iter1.md`
- `compact_v5/_status/v5_completion_audit/logs/block-g-*`
- `compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md`
- `compact_v5/_status/v5_completion_audit/STATUS.md`

Before commit:

1. Tests pass.
2. `scope_audit.py --block G` reports zero ship-blocking rows.
3. Claude review contains `REVIEWED ROWS` with G-1 through G-8, `VERDICT:`, and `SHIP DECISION:`.
4. Status, reviewer verdict, matrix, and ledger are consistent.
5. Only the specific Block G file list is staged.

Current gate state:

- Tests: PASS (`49 passed, 1 skipped`; py_compile PASS).
- Scope audit: PASS (`READY_TO_REVIEW_CLOSE`, 8 shipped, 0 blockers).
- Claude review: PASS (`VERDICT: APPROVE`, `SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW`).
- Git evidence: pending close commit SHA.
