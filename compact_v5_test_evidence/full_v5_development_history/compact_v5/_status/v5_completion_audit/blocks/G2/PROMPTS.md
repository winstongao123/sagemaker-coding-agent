# Block G2 Prompts

Claude review prompts:

- Pending: `compact_v5/_status/v5_completion_audit/prompts/block-g2-claude-review-iter1.md`

Prompt requirements:

- Include full `CLAUDE_REVIEWER_BASE_PROMPT.md`.
- Target block: G2.
- Canonical row ids: G2.
- Do not paste repository file contents.
- Provide only changed-file paths, block artifact paths, logs, and concise
  navigation notes.
- Require Claude to read canonical context and relevant files from disk before
  producing `REVIEWED ROWS`, `VERDICT`, and `SHIP DECISION`.
