# Block H Prompts

Date: 2026-05-05

Claude review prompt paths will be recorded here.

Expected first review prompt:

- `compact_v5/_status/v5_completion_audit/prompts/block-h-claude-review-iter1.md`

Prompt rules:

- Include the full `CLAUDE_REVIEWER_BASE_PROMPT.md`.
- Include Block H row ids H-1 through H-20.
- Include changed-file paths, block artifact paths, and test/log paths.
- Do not paste repository file contents.
- Require Claude to read files itself and return `REVIEWED ROWS`, `VERDICT`,
  and `SHIP DECISION`.
