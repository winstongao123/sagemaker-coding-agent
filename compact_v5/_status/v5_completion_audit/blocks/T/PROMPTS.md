# Block T Prompts

Status: ITER1_PROMPT_SAVED
Date: 2026-05-04

| Iter | Prompt path | Purpose | Notes |
|---:|---|---|---|
| 1 | `compact_v5/_status/v5_completion_audit/prompts/block-t-claude-review-iter1.md` | closure review | Includes full `CLAUDE_REVIEWER_BASE_PROMPT.md`, instructs Claude to read canonical context from disk first and reconstruct scope from `SYNTHESIS_MASTER.md`, lists all 12 Block T rows, includes changed files/logs, and explicitly calls out the user-highlighted QueryEngine parallel-dispatch bookkeeping risk plus regression evidence. |
| 2 | `compact_v5/_status/v5_completion_audit/prompts/block-t-claude-review-iter2.md` | closure re-review after LOW fix | Includes full base prompt, requires canonical scope reconstruction, and asks Claude to verify the iter1 LOW `scope_audit.py` N/A counter fix plus refreshed strict audit evidence. |
| 3 | `compact_v5/_status/v5_completion_audit/prompts/block-t-claude-review-iter3.md` | artifact re-review after LOW missing-log fix | Includes full base prompt, requires canonical scope reconstruction, and asks Claude to verify the regenerated `block-t-low-fix-py-compile.log` artifact plus unchanged zero-blocker Block T state. |
