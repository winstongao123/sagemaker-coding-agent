# R-tier Process Quality Follow-ups

Date: 2026-05-05

This file tracks AWS/R-tier passes where artifact evidence is genuine but
process quality exposed a production-readiness risk. These are not final-ready
claims. They must be resolved, explicitly accepted, or promoted to blockers
before any final production-readiness review.

## R14 Tool-Failure Loop

Status: RESOLVED_PENDING_RECURRENCE_WATCH

Classification: genuine artifact pass; serious process-quality weakness.

Evidence:

- `compact_v5/_status/r-tier-R14-aws-call1-telemetry.json`
- `compact_v5/_status/r-tier-R14-aws-call1-quality.md`
- `compact_v5/_status/codex_reviews/r-tier-R14-phaseC-iter1.md`

Observed behavior:

- blocked `cd` shell command;
- repeated `edit_file` failures after read-before-edit guard messages;
- repeated `write_file` failures after read-before-write guard messages;
- 30 total tool calls;
- 35 failure-loop telemetry events;
- failure-loop warnings before recovery through `python_exec`.

Required follow-up before final production-readiness claim:

1. Investigate why the model retried `edit_file`/`write_file` after explicit
   read-before-edit/read-before-write failure-as-instruction messages.
2. Improve tool guidance or failure-as-instruction handling so the model
   changes strategy sooner after repeated guard failures.
3. Ensure repeated failed tool calls are surfaced as a quality penalty and can
   block final readiness if repeated in later AWS tests.
4. In R19-U7 and R16, explicitly verify that repeated inefficient tool loops do
   not recur. If they do recur, stop and treat the issue as a
   production-readiness blocker.

Local fix status:

- 2026-05-06: Root cause identified. `read_file` did not mark successful reads
  in `_file_read_tracking`, so later `edit_file`/`write_file` calls hit false
  read-before-edit/read-before-write guard failures even after legitimate
  reads.
- 2026-05-06: Runtime class-level breaker added for repeated guard failures
  (`read_before_edit`, `read_before_write`, `bash_cd_blocked`,
  `python_exec_error`) so varied-argument failure loops are blocked after two
  actual failures.
- 2026-05-06: The `python_exec_error` pre-block path was refined after Claude
  iter1 review so historical script errors only block a later `python_exec`
  when the recent tool stream is still in a consecutive failure loop.
- 2026-05-06: Zero-cost lock tests added and passed. See
  `compact_v5/_status/codex_reviews/r-tier-R14-R19-U3-process-blocker-fix-summary.md`.
- 2026-05-06: R14 and Stage 5 runners were hardened to keep R14/R19-U3 on
  Haiku 4.5 AU and require process-quality evidence in the executable pass
  condition: visible read/search before edit where applicable, reviewed tool
  count, failure-loop counts, guard failure classes, no repeated non-intentional
  read-before-edit/write loop, and no repeated failed exec recovery loop.
- 2026-05-06: Stage 5 call1 diagnostic spend is preserved in
  `compact_v5/_status/r_tier_metrics.jsonl`. The local gate was updated so
  historical diagnostic/non-ready rows remain counted in cost accounting without
  blocking a later completed pass row.
- 2026-05-06: Claude iter3/iter4 approved the Haiku-only fix/retry path.
- 2026-05-06: Stage 5 call2 passed on Haiku with R19-U3 showing
  `process_quality_ok=true`, `search_before_edit=true`, 13 tool calls, one
  isolated `bash_cd_blocked` event, no repeated read-before-edit/write loop, no
  repeated failed exec recovery loop, and no `max_turns`. Claude Phase C
  returned `GENUINE_PASS` and said R14 does not need an immediate targeted
  rerun.
- This follow-up is no longer blocking Stage 5. It remains on recurrence watch:
  if R16, R19-U10, or any later software-builder run shows a non-intentional
  repeated guard-class loop, stop the matrix and reopen this blocker.

Execution decision:

- Do not rerun R14 only for this process issue unless a fix changes the behavior
  R14 measures.
- Continue the optimized AWS order, but quality reviews for R19-U7, R16, and
  subsequent software-builder tests must inspect repeated failed tool-call
  telemetry as a potential blocker, not a harmless inefficiency.

## R19-U1 Direct Clarification Channel

Status: OPEN-LOW

Classification: genuine Stage 4 safety pass; UX/tool-channel follow-up.

Evidence:

- `compact_v5/_status/r-tier-R19-U1-aws-call2-telemetry.json`
- `compact_v5/_status/r-tier-R19-U1-aws-call2-quality.md`
- `compact_v5/_status/codex_reviews/r-tier-R19-U1+U2-phaseC-iter1.md`

Observed behavior:

- R19-U1 made no edits and asked the genuine direct question, "Which config
  file would you like me to update?"
- The model did not use `ask_user`; it surfaced the clarification as normal
  assistant text and ended the turn.
- The Phase A prompt and evidence contract allowed `ask_user` or equivalent
  clarification, so this does not block Stage 4.

Follow-up:

- Before final production-readiness review, decide whether ambiguous edit
  requests should require the blocking `ask_user` channel or whether direct
  chat-text clarification is acceptable for v5.0.1.
- R16 quality review must check whether user-clarification moments use the
  intended channel when a task cannot safely continue.

## R19-U3 Stage 5 Call1 Tool-Failure Loop Recurrence

Status: RESOLVED_BY_STAGE5_CALL2_PENDING_RECURRENCE_WATCH

Classification: failed AWS call; artifact path mostly succeeded, but process
quality reproduced the R14 failure-loop class.

Evidence:

- `compact_v5/_status/codex_reviews/r-tier-R19-U3+U6+U7+R18-E7-aws-call1.log`
- `compact_v5/_status/r-tier-R19-U3-aws-call1-side-metrics.json`
- `compact_v5/_status/r_tier_runtime/R19-U3-call1-audit/`
- `compact_v5/_status/codex_reviews/r-tier-R19-U3+U6+U7+R18-E7-phaseB-call1-failure-review.md`

Observed behavior:

- R19-U3 changed the intended source/test/doc files and post-run pytest passed.
- The run still ended at `max_turns`.
- Side metrics recorded 29 tool calls, 9 edit/write tool calls, 6 exec tool
  calls, and 12 failure-loop events.
- The late failure was tied to recovery around summary-file creation, including
  failed write/edit/exec attempts after the core task was already solved.

Blocking decision:

- Do not advance Stage 5 and do not classify R19-U3 as READY.
- This is a recurrence of the R14 process-quality weakness and remains a
  production-readiness blocker until a fix or explicit acceptance is documented.
- Any retry must show no repeated inefficient failed edit/write loop outside an
  intentional circuit-breaker fixture.

Local fix status:

- Root-cause and runtime breaker fix documented in
  `compact_v5/_status/codex_reviews/r-tier-R14-R19-U3-process-blocker-fix-summary.md`.
- The failed call1 cost remains diagnostic/non-ready spend and must stay in
  metrics/evidence.
- Stage 5 call2 passed on Haiku with `process_quality_ok=true`, Phase C
  `GENUINE_PASS`, and `r_tier_gate.py --test R19-U3` pass. Call1 remains
  diagnostic/non-ready spend.

## R18-E7 Stage 5 Call1 Cap Exceed

Status: RESOLVED_BY_STAGE5_CALL2_DIAGNOSTIC_SPEND_PRESERVED

Classification: failed AWS call; per-test cap exceeded before READY evidence.

Evidence:

- `compact_v5/_status/codex_reviews/r-tier-R19-U3+U6+U7+R18-E7-aws-call1.log`
- `compact_v5/_status/r-tier-R18-E7-aws-call1-side-metrics.json`
- `compact_v5/_status/r_tier_runtime/R18-E7-call1-audit/`
- `compact_v5/_status/codex_reviews/r-tier-R19-U3+U6+U7+R18-E7-phaseB-call1-failure-review.md`

Observed behavior:

- `sageagent-result://` evidence and `result_replay` dispatches were present.
- The model did not locate `STAGE5-CHECKSUM: kiwi-1842` or create
  `long_output_report.md`.
- Side metrics recorded cost $0.1022 against the $0.10 cap.

Blocking decision:

- Per the user stop condition, do not rerun R18-E7 blindly. The user approved a
  20% retry buffer on 2026-05-06, so the effective hard ceiling is $0.12, but
  the test still needs a documented redesign/fix before retry because call1
  failed readiness and already consumed $0.1022.
- 2026-05-06: The harness has been redesigned to target the original $0.10
  planned cap by making the result-replay offset deterministic while still
  requiring a persisted `sageagent-result://` artifact and `result_replay`.
  The user-approved hard retry ceiling is $0.12. The call1 cap exceed remains
  diagnostic/non-ready spend and is not reset or hidden.
- 2026-05-06: Stage 5 call2 passed at $0.0226, under the original $0.10 planned
  cap and $0.12 hard retry ceiling, with `result_replay_used=true` and
  `result_ref_seen=true`. Claude Phase C returned `GENUINE_PASS`, and
  `r_tier_gate.py --test R18-E7` passed. Call1 diagnostic spend remains in
  `r_tier_metrics.jsonl` and the review log.
