# Block G Prompts

Status: REVIEW_COMPLETE
Date: 2026-05-05

Planned reviewer prompt:

- `compact_v5/_status/v5_completion_audit/prompts/block-g-claude-review-iter1.md`

Reviewer stdout:

- `compact_v5/_status/v5_completion_audit/reviews/block-g-claude-review-iter1.md`

Reviewer stderr/log:

- `compact_v5/_status/v5_completion_audit/logs/block-g-claude-review-iter1.log`

Smoke:

- `compact_v5/_status/v5_completion_audit/logs/block-g-claude-smoke-before-review-iter1.out.txt`
- `compact_v5/_status/v5_completion_audit/logs/block-g-claude-smoke-before-review-iter1.err.txt`

Prompt requirements:

- Include the full `CLAUDE_REVIEWER_BASE_PROMPT.md`.
- Target block: G.
- Review purpose: closure review.
- Expected row ids: G-1 through G-8.
- List changed/code paths, artifact paths, and test/log paths only.
- Do not paste repository file contents.
- Require Claude to read `SYNTHESIS_MASTER.md`, implementation files, tests, and artifacts directly from disk with read-only tools.
- Require `REVIEWED ROWS`, `VERDICT:`, and `SHIP DECISION:`.

Prompt state:

- Created with the full `CLAUDE_REVIEWER_BASE_PROMPT.md`.
- Contains row ids, changed-file paths, artifact paths, test/log paths, and concise navigation only.
- Does not paste repository file contents.

Result:

- Smoke returned exactly `CLAUDE_REVIEWER_READY block_g_pre_review_iter1`.
- Review iter1 returned `VERDICT: APPROVE`, `SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW`, and 0 remaining ship-blocking rows.
