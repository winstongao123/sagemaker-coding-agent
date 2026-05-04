# Worker Reviewer Transcript Rule

Status: ACTIVE
Created: 2026-05-04

Every worker/reviewer exchange must be recoverable from files. Terminal output
and chat history are not sufficient evidence.

## Save Every Message

For every Claude reviewer attempt, including failed attempts, save:

| Artifact | Required path |
|---|---|
| Exact prompt sent to Claude | `compact_v5/_status/v5_completion_audit/prompts/block-<block>-claude-review-iter<N>.md` |
| Claude stdout / review text | `compact_v5/_status/v5_completion_audit/reviews/block-<block>-claude-review-iter<N>.md` |
| Claude stderr / CLI log | `compact_v5/_status/v5_completion_audit/logs/block-<block>-claude-review-iter<N>.log` |
| Command/auth notes when relevant | `compact_v5/_status/v5_completion_audit/logs/block-<block>-claude-review-iter<N>.command.md` |
| Matrix row | `compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md` |
| Latest block verdict | `compact_v5/_status/v5_completion_audit/blocks/<BLOCK>/REVIEWER_VERDICT.md` |
| Latest block heartbeat | `compact_v5/_status/v5_completion_audit/blocks/<BLOCK>/STATUS.md` |

## Failed Attempts Still Count As Artifacts

Save and record these too:

- empty output
- stale prompt complaint
- plan-mode output
- command-shape failure
- auth-routing failure
- low API credit / subscription-routing failure
- timeout / hang
- no `VERDICT:`
- no `SHIP DECISION:`

Failed attempts are not reviewer verdicts, but they are part of the process
history and must remain inspectable.

## Worker Reply To Reviewer

If Codex responds to a Claude finding, save the response as one of:

- `prompts/block-<block>-claude-dispute-iter<N>.md`
- `blocks/<BLOCK>/DISPUTED_FINDING_<id>.md`

The dispute prompt must include the full
`CLAUDE_REVIEWER_BASE_PROMPT.md` and must instruct Claude to reread canonical
context from disk before trusting the worker's evidence.

## No Silent Review State

Do not proceed to the next block, close a block, or ask for git/AWS approval
unless the latest worker/reviewer messages are saved and indexed in the block
status plus review matrix.
