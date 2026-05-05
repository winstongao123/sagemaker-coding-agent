# Block F2 Prompts

Status: SENT_ITER1
Date: 2026-05-05

Reviewer prompt:

- `compact_v5/_status/v5_completion_audit/prompts/block-f2-claude-review-iter1.md`

Prompt requirements:

- Include the full `CLAUDE_REVIEWER_BASE_PROMPT.md`.
- Target block: F2.
- Review purpose: closure review.
- Expected row ids: F2-1.
- List changed/code paths, artifact paths, and test/log paths only.
- Do not paste repository file contents.
- Require Claude to read `SYNTHESIS_MASTER.md`, implementation files, tests, and artifacts directly from disk with read-only tools.
- Require `REVIEWED ROWS`, `VERDICT:`, and `SHIP DECISION:`.

Claude smoke:

- `compact_v5/_status/v5_completion_audit/logs/block-f2-claude-smoke-before-review-iter1.out.txt`
- `compact_v5/_status/v5_completion_audit/logs/block-f2-claude-smoke-before-review-iter1.err.txt`

Claude review:

- `compact_v5/_status/v5_completion_audit/reviews/block-f2-claude-review-iter1.md`
- `compact_v5/_status/v5_completion_audit/logs/block-f2-claude-review-iter1.log`
