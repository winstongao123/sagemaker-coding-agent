# Block N Prompts

Status: ITER2_PROMPT_SAVED

## Iter1

- Purpose: closure review.
- Prompt: `compact_v5/_status/v5_completion_audit/prompts/block-n-claude-review-iter1.md`
- Required base prompt: full `CLAUDE_REVIEWER_BASE_PROMPT.md` embedded.
- Canonical reconstruction requirement: yes; prompt instructs Claude to read
  context files from disk and reconstruct Block N from `SYNTHESIS_MASTER.md`
  before trusting worker context.
- Review status: completed with `APPROVE_WITH_FIXES` /
  `READY_FOR_BLOCK_CLOSE_REVIEW`; 0 ship-blocking rows and LOW doc/process
  findings.

## Iter2

- Purpose: closure re-review after iter1 LOW fixes and user-requested
  parallel fast-path risk resolution.
- Prompt: `compact_v5/_status/v5_completion_audit/prompts/block-n-claude-review-iter2.md`
- Required base prompt: full `CLAUDE_REVIEWER_BASE_PROMPT.md` embedded.
- Canonical reconstruction requirement: yes; prompt instructs Claude to read
  context files from disk and reconstruct Block N from `SYNTHESIS_MASTER.md`
  before trusting worker context.
- Explicit risk included: QueryEngine parallel dispatch fast path must preserve
  audit logging, repeat-call tracking, JSON argument repair, and
  error/forensic behavior by reusing `_dispatch_single_tool_call`.
- Review status: completed with `APPROVE` /
  `READY_FOR_BLOCK_CLOSE_REVIEW`; 0 ship-blocking rows.
