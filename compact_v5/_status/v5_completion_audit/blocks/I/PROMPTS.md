# Block I Prompts

Status: REVIEW_COMPLETE
Date: 2026-05-05

Reviewer prompt:

- `compact_v5/_status/v5_completion_audit/prompts/block-i-claude-review-iter1.md`

Reviewer stdout:

- `compact_v5/_status/v5_completion_audit/reviews/block-i-claude-review-iter1.md`

Reviewer stderr/log:

- `compact_v5/_status/v5_completion_audit/logs/block-i-claude-review-iter1.log`

Smoke:

- `compact_v5/_status/v5_completion_audit/logs/block-i-claude-smoke-before-review-iter1.out.txt`
- `compact_v5/_status/v5_completion_audit/logs/block-i-claude-smoke-before-review-iter1.err.txt`

Prompt requirements:

- Include the full `CLAUDE_REVIEWER_BASE_PROMPT.md`.
- Target block: I.
- Review purpose: closure review.
- Expected row ids: I-1 through I-13.
- List changed/code paths, artifact paths, and test/log paths only.
- Do not paste repository file contents.
- Require Claude to read `SYNTHESIS_MASTER.md`, implementation files, tests, and artifacts directly from disk with read-only tools.
- Require `REVIEWED ROWS`, `VERDICT:`, and `SHIP DECISION:`.

Result:

- Smoke returned exactly `CLAUDE_REVIEWER_READY block_i_pre_review_iter1`.
- Review iter1 returned `VERDICT: APPROVE`, `SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW`, and 0 remaining ship-blocking rows.
