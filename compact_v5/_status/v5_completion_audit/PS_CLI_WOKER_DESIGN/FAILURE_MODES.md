# Failure Modes And Recovery

## Empty Claude Review File

Symptom:

- `reviews/block-*-claude-review-iterN.md` exists but length is `0`.

Meaning:

- Claude may still be running, hung, or exited without output.

Recovery:

1. Check whether a matching Claude process is still active.
2. If stale, stop only that stale Claude process.
3. Save a new prompt with the next iter number.
4. Run Claude directly using the command pattern in `COMMANDS.md`.
5. Record the failed iter as `NO_VERDICT` in the matrix/status instead of
   pretending it reviewed anything.

## Claude Handoff Retry Policy

Failed handoffs are not usable review verdicts, but they are still audit
artifacts. Save prompt, stdout/review, stderr/log, matrix row, block verdict
note, and block heartbeat for every attempt.

- `ConnectionRefused`, timeout, or transient network failure: retry up to 3
  times with the same intended prompt content, a new iteration number, and
  saved artifacts for each attempt.
- API credit, balance, or billing-route error: clear `ANTHROPIC_API_KEY` for
  the Claude subprocess and retry through the Claude Code subscription-auth
  path in `CLAUDE_REVIEWER_AUTH.md`.
- Malformed command, bad `--setting-sources`, or PowerShell argument issue:
  fix the command shape and retry with a new iteration number.
- Empty output, missing `VERDICT:`, missing `SHIP DECISION:`, or plan-mode
  output: record `NO_VERDICT`, fix prompt/stdin/permission mode, and retry.
- Failed or timed-out pre-review Claude smoke: do not run the full review yet.
  Record the smoke failure under the current block logs/status. If the smoke
  output includes hook errors such as `SessionEnd hook`, `EPERM`, or
  `uv_spawn`, retry with the documented smoke command that passes
  `claude-reviewer-settings.json` so `disableAllHooks: true` applies. Then
  retry the smoke using the documented non-escalated command shape, and
  continue only local implementation/scope work until the reviewer path is
  proven live.
- Policy denial: do not bypass silently. If the user has already authorized
  read-only Claude review for this audit, retry using the approved
  non-escalated subscription-auth/read-only path. Do not request
  sandbox/approval escalation for the Claude reviewer command; escalation can
  be denied before Claude executes as private-repo egress. If the
  non-escalated path is still policy-denied, stop with
  `REVIEW_LOOP_BLOCKED.md`.

## Claude Writes A Plan Instead Of A Verdict

Symptom:

- Review file contains plan text, sandbox permission complaints, or no
  `VERDICT:`.

Meaning:

- The reviewer prompt/CLI mode allowed planning behavior or did not deliver the
  full prompt.

Recovery:

1. Ensure the prompt includes `CLAUDE_REVIEWER_BASE_PROMPT.md`.
2. Add: return review text directly to stdout; do not create plan files; do not
   edit/write files; do not call ExitPlanMode.
3. Use `--permission-mode dontAsk` with read-only settings.
4. Pipe the full prompt by stdin with `Get-Content -Raw $prompt | claude ...`.
5. Save a new review iter.

## Stale Prompt Scope

Symptom:

- Claude says the prompt is stale, or the review omits newly implemented rows.

Meaning:

- The worker reused a previous prompt or forgot to include new row/file
  evidence.

Recovery:

- Treat the review as failed/no-verdict for implementation approval.
- Create a fresh prompt with current rows, changed files, expected counts, test
  evidence, PORT_LOG/ADR evidence, and the static base prompt.
- Run a new Claude iter.

## Worker Claims Done With Blocking Rows

Symptom:

- `STATUS.md` says `DONE`, but `LEDGER.md` has `PARTIAL`, `MISSING`, or
  `SHIP_BLOCKING_ROWS`.

Meaning:

- False closure.

Recovery:

- Treat as blocked.
- Do not commit/push/tag.
- Run `py -3.11 compact_v5\_status\scripts\scope_audit.py --block <BLOCK>`.
- Continue implementation or request explicit user defer/drop approval.

## Matrix Not Updated

Symptom:

- New review file exists, but `ledger/CLAUDE_REVIEW_MATRIX.md` lacks the row.

Recovery:

- Worker must read the review and update matrix plus `REVIEWER_VERDICT.md`.
- Do not proceed to the next block until the review evidence is recorded.

## Worker Disagrees With Claude Finding

Symptom:

- Claude reports a finding, but Codex believes the finding is incorrect.

Recovery:

- Do not mark the row or block done.
- Record the finding as unresolved in `REVIEWER_VERDICT.md` and
  `CLAUDE_REVIEW_MATRIX.md`.
- Write a `DISPUTED_FINDING` note with exact file:line/test evidence.
- Create a fresh Claude dispute-review prompt that includes the full
  `CLAUDE_REVIEWER_BASE_PROMPT.md`.
- Claude must reread canonical context from disk before responding.
- The finding remains ship-blocking unless Claude withdraws it, Codex fixes it,
  or the user explicitly decides.

## Review/Fix Loop Is Stuck

Symptom:

- A block repeats the same failure without meaningful progress, or Claude
  handoff fails repeatedly.

Meaning:

- The process is stuck. There is no fixed cap on useful reviews, but repeated
  no-progress loops must not continue unattended.

Recovery:

- Stop the worker loop.
- Write `blocks/<BLOCK>/REVIEW_LOOP_BLOCKED.md`.
- Include every iter number, prompt path, review path, verdict, and remaining
  blockers.
- Ask the user whether to continue, split the block, change strategy, or switch
  worker/reviewer mode.

Stuck guards:

- 3 consecutive reviewer handoff failures.
- 3 attempts on the same row/finding/test failure without meaningful change.

## AWS Test Confusion

Symptom:

- Local R-tier gate passes and someone claims AWS readiness.

Correction:

- Local marker gate is not AWS proof.
- AWS test requires Claude Phase A approval, raw log, telemetry, quality review,
  metrics row, review log row, and per-test gate pass.
