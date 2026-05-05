# Block B Prompts

Status: ITER8_IMPORTED_REVIEW_RECORDED
Date: 2026-05-05

## Claude Reviewer Prompts

| Iter | Purpose | Prompt path | Notes |
|---:|---|---|---|
| 1 | closure review | `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter1-prompt.md` | Includes full `CLAUDE_REVIEWER_BASE_PROMPT.md`, requires canonical context reads and scope reconstruction from `SYNTHESIS_MASTER.md`, and calls out B-10 Sonnet 4.6/current-runtime Sonnet 4.5 adaptation risk. |
| 2 | closure review retry | `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter2-prompt.md` | Same full prompt as iter1; retry after iter1 returned `API Error: Unable to connect to API (ConnectionRefused)`. |
| 3 | closure review retry | `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter3-prompt.md` | Fresh prompt after user confirmed Claude Code subscription-path smoke and explicitly authorized read-only private-repo review; same canonical scope requirements plus prior no-verdict attempt context. |
| 4 | closure review retry | `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter4-prompt.md` | Same saved prompt shape as iter3; retry after iter3 returned `ConnectionRefused`, using the approved subscription-auth/read-only path with escalation for network access. |
| 5 | closure review retry | `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter5-prompt.md` | Same saved prompt shape as iter3; retry per user instruction using the normal non-escalated subscription-auth/read-only command path. |
| 6 | closure review retry | `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter6-prompt.md` | Same saved prompt shape as iter5; normal non-escalated retry after iter5 returned `ConnectionRefused`. |
| 7 | closure review retry | `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter7-prompt.md` | Same saved prompt shape as iter5 with iter6 no-verdict context added; normal non-escalated retry after iter6 returned `ConnectionRefused`. |
| 8 | closure review import record | `compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter8-prompt.md` | Records that the official iter8 review was imported per user instruction from monitor-session output `logs/block-b-monitor-claude-fullprompt-test.out.md`; no new Claude subprocess was launched by this worker. |

No Codex review prompts were created.
