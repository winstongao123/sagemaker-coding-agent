# Block E+F Git Close Plan

Status: READY_TO_STAGE_SPECIFIC_FILES

No files have been staged, committed, or pushed for Block E+F yet.

Claude review:

- Iter1: `APPROVE`, `READY_FOR_BLOCK_CLOSE_REVIEW`, with LOW EF-3/EF-5 findings.
- Iter2: `APPROVE`, `READY_FOR_BLOCK_CLOSE_REVIEW`, after LOW fixes.

Final scope audit:

- `block-e-f-scope-audit-final.log`: no ship-blocking rows.
- `block-e-f-scope-audit-strict-final.log`: no ship-blocking rows.

Specific-file staging list:

```text
compact_v5/MAIN/agent/core/__init__.py
compact_v5/MAIN/agent/core/formatting.py
compact_v5/MAIN/agent/core/query_engine.py
compact_v5/MAIN/agent/runtime/config.py
compact_v5/MAIN/agent/tests/integration/test_block_e_f.py
compact_v5/_status/V5_DESIGN_DECISIONS.md
compact_v5/_status/V5_RUNNABLE_PORT_LOG.md
compact_v5/_status/v5_completion_audit/blocks/E+F/BASELINE.md
compact_v5/_status/v5_completion_audit/blocks/E+F/CHANGELOG.md
compact_v5/_status/v5_completion_audit/blocks/E+F/DECISIONS.md
compact_v5/_status/v5_completion_audit/blocks/E+F/GIT_CLOSE_PLAN.md
compact_v5/_status/v5_completion_audit/blocks/E+F/LEDGER.md
compact_v5/_status/v5_completion_audit/blocks/E+F/PROMPTS.md
compact_v5/_status/v5_completion_audit/blocks/E+F/REVIEWER_VERDICT.md
compact_v5/_status/v5_completion_audit/blocks/E+F/SELF_REFLECTION.md
compact_v5/_status/v5_completion_audit/blocks/E+F/STATUS.md
compact_v5/_status/v5_completion_audit/blocks/E+F/TESTS.md
compact_v5/_status/v5_completion_audit/blocks/E+F/WORKER_SELF_REVIEW.md
compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md
compact_v5/_status/v5_completion_audit/logs/block-e-f-claude-review-iter1.log
compact_v5/_status/v5_completion_audit/logs/block-e-f-claude-review-iter2.log
compact_v5/_status/v5_completion_audit/logs/block-e-f-py-compile.log
compact_v5/_status/v5_completion_audit/logs/block-e-f-py-compile-iter2.log
compact_v5/_status/v5_completion_audit/logs/block-e-f-pytest.log
compact_v5/_status/v5_completion_audit/logs/block-e-f-pytest-iter2.log
compact_v5/_status/v5_completion_audit/logs/block-e-f-query-f2-regression.log
compact_v5/_status/v5_completion_audit/logs/block-e-f-query-f2-regression-iter2.log
compact_v5/_status/v5_completion_audit/logs/block-e-f-scope-audit.log
compact_v5/_status/v5_completion_audit/logs/block-e-f-scope-audit-strict.log
compact_v5/_status/v5_completion_audit/logs/block-e-f-scope-audit-iter2.log
compact_v5/_status/v5_completion_audit/logs/block-e-f-scope-audit-strict-iter2.log
compact_v5/_status/v5_completion_audit/logs/block-e-f-scope-audit-final.log
compact_v5/_status/v5_completion_audit/logs/block-e-f-scope-audit-strict-final.log
compact_v5/_status/v5_completion_audit/prompts/block-e-f-claude-review-iter1.md
compact_v5/_status/v5_completion_audit/prompts/block-e-f-claude-review-iter2.md
compact_v5/_status/v5_completion_audit/reviews/block-e-f-claude-review-iter1.md
compact_v5/_status/v5_completion_audit/reviews/block-e-f-claude-review-iter2.md
```

Known unrelated/pre-existing dirty paths to leave unstaged include:

- `_archive/compare_code/gg-claude-code-runnable`
- `compact_v5.zip`
- `compact_v5/MAIN/agent/memory.md`
- `compact_v5/_phase_2/wave_6/BUILDER_PROMPT.md`
- existing `_status` and docs files outside the Block E+F staging list
- `compact_v5/_status/v5_completion_audit/BLOCK_ORDER_AND_COVERAGE.md`
  is an active control file read during this block, but it was already
  untracked in the working tree and is not a Block E+F implementation artifact.

Do not use `git add -A`. Do not tag. Do not force push.
