# Block G3 Prompts

Claude review prompts:

- Pending: `compact_v5/_status/v5_completion_audit/prompts/block-g3-claude-review-iter1.md`

Prompt requirements:

- Include full `CLAUDE_REVIEWER_BASE_PROMPT.md`.
- Target block: G3.
- Canonical row ids: G3-1, G3-2.
- Do not paste repository file contents.
- Provide only changed-file paths, block artifact paths, logs, and concise
  navigation notes.
- Require Claude to read canonical context and relevant files from disk before
  producing `REVIEWED ROWS`, `VERDICT`, and `SHIP DECISION`.
