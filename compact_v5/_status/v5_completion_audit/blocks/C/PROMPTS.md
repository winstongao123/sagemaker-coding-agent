# Block C Prompts

Status: ITER1_PROMPT_SAVED
Date: 2026-05-04

## Saved Prompts

| Iter | Purpose | Prompt path | Status |
|---:|---|---|---|
| 1 | closure review | `compact_v5/_status/v5_completion_audit/prompts/block-c-claude-review-iter1.md` | saved and run; review body produced but subprocess timed out |
| 2 | closure re-review after iter1 LOW fixes | `compact_v5/_status/v5_completion_audit/prompts/block-c-claude-review-iter2.md` | saved, pending Claude execution |
| 3 | closure re-review retry after iter2 capture timeout | `compact_v5/_status/v5_completion_audit/prompts/block-c-claude-review-iter3.md` | saved, pending Claude execution |

Every future Block C Claude prompt must include the full
`CLAUDE_REVIEWER_BASE_PROMPT.md` and instruct Claude to read canonical context
from disk first and reconstruct Block C scope from `SYNTHESIS_MASTER.md`.
