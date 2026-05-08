# Block A Prompts

## Worker Prompt

Saved copy:

- `compact_v5/_status/v5_completion_audit/prompts/block-a-worker-ledger-2026-05-04.md`

The current active worker instruction is `compact_v5/_status/v5_completion_audit/06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md`. The original 2026-05-04 kickoff required starting with Block A and not running nested Codex or Codex review.

## Reviewer Handoff Prompt

Saved copy:

- `compact_v5/_status/v5_completion_audit/prompts/block-a-claude-review-2026-05-04.md`

Reviewer command was not run by this worker.
Additional compliant reviewer prompt:

- `compact_v5/_status/v5_completion_audit/prompts/block-a-claude-review-iter7.md`

## Closure Review Prompt

Saved copy:

- `compact_v5/_status/v5_completion_audit/prompts/block-a-claude-review-iter8.md`

This prompt was reused for iter8, iter9, and iter10 attempts:

- Iter8: `NO_VERDICT / HANDOFF_FAILED_AUTH_ROUTING`; review output saved at
  `reviews/block-a-claude-review-iter8.md`, log at
  `logs/block-a-claude-review-iter8.log`.
- Iter9: `NO_VERDICT / HANDOFF_FAILED_AUTH_COMMAND`; review output saved at
  `reviews/block-a-claude-review-iter9.md`, log at
  `logs/block-a-claude-review-iter9.log`.
- Iter10: usable closure-scope review; review output saved at
  `reviews/block-a-claude-review-iter10.md`, log at
  `logs/block-a-claude-review-iter10.log`.

Iter10 returned `VERDICT: APPROVE_WITH_FIXES` and
`SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW`.

## LOW-Fix Re-Review Prompt

Saved copy:

- `compact_v5/_status/v5_completion_audit/prompts/block-a-claude-review-iter11.md`

Iter11 reviewed the A-22/A-30/A-37 LOW-finding fixes after iter10:

- Review output: `compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter11.md`
- Stderr log: `compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter11.log`

Iter11 returned `VERDICT: APPROVE` and
`SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW`.
