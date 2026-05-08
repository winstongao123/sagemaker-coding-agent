# Block K Prompts

Status: ITER1_PROMPT_SAVED
Date: 2026-05-04

Claude review prompts:

| Iter | Purpose | Prompt path | Status |
|---:|---|---|---|
| 1 | closure review | `compact_v5/_status/v5_completion_audit/prompts/block-k-claude-review-iter1.md` | Returned APPROVE |
| 2 | closure review cleanup re-review | `compact_v5/_status/v5_completion_audit/prompts/block-k-claude-review-iter2.md` | Returned APPROVE_WITH_FIXES |
| 3 | closure review ledger cleanup re-review | `compact_v5/_status/v5_completion_audit/prompts/block-k-claude-review-iter3.md` | Returned APPROVE |

Every prompt embeds `CLAUDE_REVIEWER_BASE_PROMPT.md` and instructs Claude to reconstruct Block K scope from `SYNTHESIS_MASTER.md` before trusting worker context.
