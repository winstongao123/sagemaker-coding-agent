# Block H+ Prompts

Date: 2026-05-05

Expected first Claude review prompt:

- `compact_v5/_status/v5_completion_audit/prompts/block-h-plus-claude-review-iter1.md`

Prompt rules:

- Include the full `CLAUDE_REVIEWER_BASE_PROMPT.md`.
- Include row id H+1.
- Include code/test/artifact/log paths only, not repository file contents.
- Require Claude to read files itself and return `REVIEWED ROWS`, `VERDICT`,
  and `SHIP DECISION`.
