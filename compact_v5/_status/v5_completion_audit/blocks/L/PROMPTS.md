# Block L Prompts

Status: ITER1_PROMPT_SAVED

## Iter1

- Purpose: closure review.
- Prompt: `compact_v5/_status/v5_completion_audit/prompts/block-l-claude-review-iter1.md`
- Required base prompt: full `CLAUDE_REVIEWER_BASE_PROMPT.md` embedded.
- Canonical reconstruction requirement: yes; prompt instructs Claude to read
  context files from disk and reconstruct Block L from `SYNTHESIS_MASTER.md`
  before trusting worker context.
- Review status: not run yet.

Result: `NO_VERDICT / HANDOFF_FAILED_COMMAND_SHAPE`; PowerShell blocked
`claude.ps1` before Claude ran.

## Iter2

- Purpose: closure review retry with the same Block L scope.
- Prompt: `compact_v5/_status/v5_completion_audit/prompts/block-l-claude-review-iter2.md`
- Required base prompt: full `CLAUDE_REVIEWER_BASE_PROMPT.md` embedded.
- Canonical reconstruction requirement: yes.
- Command change: use `claude.cmd` instead of `claude.ps1` to avoid the local
  PowerShell execution-policy block.
- Review status: `NO_VERDICT / HANDOFF_FAILED_NETWORK`; Claude CLI returned
  `API Error: Unable to connect to API (ConnectionRefused)`.

## Iter3

- Purpose: closure review retry with the same Block L scope.
- Prompt: `compact_v5/_status/v5_completion_audit/prompts/block-l-claude-review-iter3.md`
- Required base prompt: full `CLAUDE_REVIEWER_BASE_PROMPT.md` embedded.
- Canonical reconstruction requirement: yes.
- Command change: same `claude.cmd` command as iter2, run with network
  escalation because iter2 could not connect to the API.
- Review status: usable review saved.
- Review path: `compact_v5/_status/v5_completion_audit/reviews/block-l-claude-review-iter3.md`
- Log path: `compact_v5/_status/v5_completion_audit/logs/block-l-claude-review-iter3.log`
- Verdict: `APPROVE_WITH_FIXES`
- Ship decision: `READY_FOR_BLOCK_CLOSE_REVIEW`
