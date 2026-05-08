# Block 0 Prompts

Date: 2026-05-05

Claude prompt artifact:

- `compact_v5/_status/v5_completion_audit/prompts/block-0-claude-review-iter1.md`

Prompt requirements:

- Include the full `CLAUDE_REVIEWER_BASE_PROMPT.md`.
- Require Claude to reconstruct Block 0 scope directly from
  `SYNTHESIS_MASTER.md`.
- Require row-by-row review for 0-1 through 0-10.
- Require Claude to verify the ADR-020 remap rule and no-AWS boundary.
