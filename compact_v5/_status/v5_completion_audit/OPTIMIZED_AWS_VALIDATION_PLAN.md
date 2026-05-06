# Optimized AWS Validation Plan

Date: 2026-05-05

Purpose: define the minimum high-signal AWS validation set needed before any
98% confidence production-readiness claim for v5 as a single-person
SageMaker software-building agent.

This plan does not approve AWS spend. It is the review target before spend.
Every AWS run still needs Phase A Claude approval, explicit user approval,
budget headroom, raw logs, telemetry, quality review, metrics, and
`r_tier_gate.py --test <TEST>` pass.

Execution loop: `compact_v5/_status/v5_completion_audit/PS_AWS_TEST_EXECUTION_LOOP.md`.
Every test must pass worker preflight, Claude Phase A design review, explicit
spend approval, AWS execution, metadata capture, worker post-run review, Claude
Phase C review, and the fix/retry/escalation loop before it can count toward
production readiness. Passing means more than a correct final artifact: the
test must also provide acceptable evidence for process quality, including
efficient tool use, coding discipline, context/memory continuity, useful
subagent/reviewer coordination, compaction/cache behavior, and cost control.

## Confidence Rule

Do not claim 98% confidence or production readiness unless all of these are
true:

1. All completion-audit blocks are closed, pushed, and Claude row-reviewed.
2. Accepted implement-now gaps from
   `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` are implemented, documented,
   locally tested, and independently reviewed.
3. Full strict scope audit is clean.
4. Local and mock tests are green.
5. This optimized AWS plan is Claude-reviewed and approved before spend.
6. Each selected AWS software-writing scenario passes with required evidence.
7. Telemetry shows acceptable tool, token, cache, compaction, subagent/reviewer,
   memory/status/checkpoint, and recovery behavior.
8. Any functional pass with weak process quality is tracked in
   `_status/R_TIER_PROCESS_QUALITY_FOLLOWUPS.md` and is resolved, explicitly
   accepted, or promoted to a blocker before the final readiness claim.
9. Final independent review approves the complete code, docs, test, telemetry,
   process-quality, and AWS evidence package.

## Optimization Principle

Use small zero-cost tests to catch simple breakage first.
Use AWS only for tests that reveal multiple production qualities in one run.
Do not duplicate a simple local assertion in a separate AWS test unless the
real model behavior is the point being evaluated.

An optimized run must not hide process defects behind a correct output. If a
test passes functionally but shows repeated failed tool calls, poor coding
discipline, lost status/memory, missing subagent/reviewer attribution, or
uncontrolled token/cache/cost behavior, the pass may be genuine for the narrow
artifact but it is not enough for final production readiness until the process
issue is closed or explicitly accepted.

## AWS Software-Builder Matrix

| Stage | Scenario | Primary Proof | Bundled Evidence | Why Not Overlap |
|---|---|---|---|---|
| 1 | R13 coding accuracy | implements correct code from a bounded task | tests/assertions, no unrelated edits, quality review, tool summary | catches basic code-generation quality before larger tasks |
| 2 | R15 debugging | finds planted bugs without false positives | failing-to-passing tests, diagnosis trace, no unrelated edits, checkpoint/verify/done flow | covers repair behavior, distinct from R13 generation |
| 3 | R14 multi-file refactor | changes a realistic cross-file project safely | grep/search evidence, pytest, stale-reference cleanup, repeated-call telemetry | covers project navigation and dependency discovery |
| 4 | R19-U1 + R19-U2 ambiguity gate | asks clarification on ambiguity/contradiction | no speculative edit, conflict reporting, status note | cheap UX/safety gate before long app work |
| 5 | R19-U3 + R19-U6 + R19-U7 + R18-E7 recovery/results gate | handles hidden deps, bad output, repeated-call traps, and large-output replay | alternative path, retry discipline, repeated-call counters, stable `sageagent-result://` refs, `result_replay`, checkpoint/verify | bundles recovery/result-inspection failures instead of one AWS call per trap |
| 6 | R3 + R19-U4 + R19-U5 subagent/reviewer gate | coordinates child agents, reconciles conflicting findings, and recovers from a failed child | subagent dispatch telemetry, parent synthesis, conflict evidence, failed-child recovery, token/cost/cache attribution | covers pure orchestration risk not proven by app-build success alone |
| 7 | R16 long app build | completes a small real app across a long session | app tests, `/status`, `/phase`, `/save`, `/resume`, `/checkpoint`, `/verify`, `/done`, `/cost`, `/context`, compaction/cache telemetry | broadest end-to-end software-builder proof |
| 8 | R19-U10 long coherence | preserves final task intent after compactions | final-task coherence, memory/status integrity, compaction events, cache trend, quality review | isolates long-coherence risk after R16 proves app build |

## Precondition Gate For Long-Run Tests

R16 and R19-U10 must not receive per-test Phase A approval until these
software-builder blocks are closed, pushed, locally tested, and Claude-reviewed:

- `SOFTWARE-STATE`
- `SOFTWARE-CHECKPOINT`
- `SOFTWARE-SHELL` if background shell lifecycle is accepted for v5.0.1
- `SOFTWARE-RESULTS`
- `SOFTWARE-SUBAGENT`
- `SOFTWARE-COMPACT-TELEMETRY`
- `SOFTWARE-GATE`

This prevents AWS from testing missing infrastructure and then producing a
misleading failure.

## Cost-Cap And Bundle Policy

Current caps remain intentionally small, but they are interpreted through a
token-budget model at Phase A:

The listed cap is the planned budget. The hard retry ceiling is the listed cap
plus the user-approved 20% buffer (`cap * 1.20`). The buffer is active in the
local R-tier gate and must preserve cumulative spend history; it must not be
used to hide failed diagnostic calls or bypass a process-quality blocker.

| Test | Cap | Phase A budget model |
|---|---:|---|
| R13 | $0.50 | 5 bounded tasks, max 1 model attempt per task plus one verification/synthesis turn. READY requires at least 4/5 passing tasks and no unrelated edits; 5/5 is the target. |
| R16 | $1.00 | Bounded small Flask CRUD fixture, max 8 primary model turns, local tests after edits, forced/local compaction evidence where possible. If Phase A estimates exceed cap, do not spend; ask user to approve cap change or shrink fixture. |
| R19-U10 | $0.50 | 150 logical turns may be represented by a prebuilt transcript/churn fixture plus a small number of real model turns that must use pre-compaction facts. If true 150 Bedrock calls are required, this cap is not valid and Phase A must stop for user approval. |

Bundle policy:

- Stage 4 can bundle R19-U1+R19-U2. Cap is the sum: $0.40.
- Stage 5 can bundle R19-U3+R19-U6+R19-U7+R18-E7. Cap is the sum: $1.00,
  buffered hard ceiling $1.20.
- Stage 6 can bundle R3+R19-U4+R19-U5. Cap is the sum: $1.20.
- Bundled runs may share one raw log, but must write per-test telemetry,
  metrics, quality rows, and review-log rows.
- R1 is already `IN_PROGRESS` from a prior Unicode-stdout failure. It must be
  rerun under the same Phase A -> AWS -> Phase C loop before any READY claim.

Determinism policy:

- one `GENUINE_PASS` is enough only when quality review finds no flakiness,
  missing evidence, or suspicious process behavior;
- rerun once if the pass is marginal or telemetry is incomplete;
- cost-cap-hit counts as one failed attempt unless no model call occurred;
- after 3 failed meaningful attempts, stop and escalate.

## Required Evidence Per AWS Run

Every selected AWS run must write:

- Phase A Claude review approving `APPROVE_FOR_AWS_CALL`;
- raw Bedrock log;
- telemetry with `tool_call_summary`, token counts, cache read/write counts,
  model id, cost, retries, repeated-call signals, and parent/subagent/reviewer
  attribution when delegation or review agents are used;
- process-quality evidence that separately grades artifact correctness, coding
  quality, tool/path efficiency, wasted calls, context/memory continuity,
  subagent/reviewer usefulness, and recovery discipline;
- compaction/cache evidence when the scenario exercises long context;
- large-output evidence when a scenario exercises R18-E7, including
  `sageagent-result://` refs, replayed content checks, artifact metadata, and
  proof the model did not rely on a marker-only truncation;
- reviewer/subagent breakdown when the scenario uses reviewer, verify, explore,
  build, fork, or other `task` roles. The evidence must include tokens, cost,
  cache read/write, dispatch count, and whether the delegation was useful;
- quality review with pass/fail reasoning;
- metrics JSONL row;
- review-log row;
- `r_tier_gate.py --test <TEST>` pass result.

R16 must also report separable sub-checks so a failure is actionable without
rerunning the whole matrix:

- status round-trip;
- todo round-trip;
- named-checkpoint round-trip;
- verify/done stale-evidence block;
- compaction event emitted;
- shell background start/poll/kill if `SOFTWARE-SHELL` ships background
  lifecycle;
- final artifact quality.

These sub-checks must be typed evidence in telemetry as
`software_builder_subchecks`, not only prose in a quality review.
The compaction sub-check may be satisfied by forced/local compaction when the
Phase A budget model proves the fixture is too small to naturally trigger
auto-compact under the approved cap. The evidence must say which path was used.

For cache evidence, if Bedrock/model output does not expose cache-hit/read/write
fields for a run, the evidence package must record an explicit model-side
limitation row instead of leaving the metric silently blank.

## Stop Rules

Stop AWS execution and return to implementation/review if:

- local zero-cost tests fail;
- Claude Phase A rejects the scenario;
- budget headroom is not confirmed;
- a scenario needs more than the approved call budget;
- telemetry is missing or cannot be trusted;
- the model passes final artifacts but shows unsafe process behavior such as
  uncontrolled repeated calls, lost status, lost memory, wasteful subagent or
  reviewer use, missing reviewer/subagent token attribution, or unexplained
  unrelated edits.
- a pattern like the R14 tool-failure loop recurs in R19-U7, R16, R19-U10, or
  any later software-builder run without a clear fix or user-accepted
  disposition.

2026-05-06 Stage 5 stop:

- Stage 5 call1 correctly stopped after R19-U3 reproduced the R14 repeated
  failed tool-loop class and R18-E7 exceeded its $0.10 cap.
- Before any additional AWS call, the R14/R19-U3 process blocker must be fixed
  locally and Claude CLI must approve the fix/retry path from disk.
- R14/R19-U3 retries must remain on Haiku 4.5 AU. Do not switch them to Sonnet
  to bypass the process-quality blocker.
- The retry must prove acceptable Haiku tool use: visible search/read before
  edit where applicable, reviewed tool count and failure-loop telemetry, no
  repeated non-intentional read-before-edit/write guard loop, and no repeated
  failed exec recovery loop. Final artifact correctness is insufficient by
  itself.
- Prior failed/non-ready costs remain diagnostic spend. Do not delete, hide, or
  reset them. Any retry allowance must be explicit to the affected item and
  preserve cumulative history.

2026-05-06 Stage 5 call2 resolution:

- Claude approved the Haiku-only fix/retry path and Phase A call2.
- Stage 5 call2 passed on Haiku:
  - R19-U3: $0.0501, `search_before_edit=true`, `process_quality_ok=true`,
    no repeated guard/exec loop.
  - R19-U6: $0.0175, malformed-output recovery.
  - R19-U7: $0.0230, `breaker_fired=true`, exactly two actual bait calls.
  - R18-E7: $0.0226, `result_replay_used=true`, under the original $0.10
    planned cap.
- Claude Phase C returned `GENUINE_PASS` and per-test gates passed.
- R14 immediate rerun is not required; keep recurrence watch active for R16,
  R19-U10, and later software-builder runs.
- Next optimized stage is Stage 6: R3 + R19-U4 + R19-U5 subagent/reviewer
  bundle, subject to fresh Phase A approval and AWS Budget/headroom check.

2026-05-06 Stage 6 call1 stop:

- Claude Phase A approved R19-U4+R19-U5 on Haiku 4.5 AU with R3 evidence
  reused and not rerun.
- AWS budget was healthy before spend. Call1 used `$0.0529` for R19-U4 and
  `$0.0366` for R19-U5, both under their buffered per-test ceilings.
- R19-U4 produced a genuine functional/process pass, but remains
  bundle-blocked pending clean Phase C/gate.
- R19-U5 produced the intended recovery artifact and acceptable process
  quality, but pytest failed because `_u5_ready` required the exact substring
  `failure`; the artifact used "Failed Probes" and `FILE NOT FOUND`.
- The runner predicate was fixed locally and zero-cost lock tests passed.
- Claude Phase B could not run: both default and `--model haiku` CLI attempts
  returned `Credit balance is too low`.
- The subscription-auth Claude reviewer command later returned
  `APPROVE_RETRY` from
  `r-tier-R19-U4+U5-phaseB-iter2-subscription.md`.

2026-05-06 Stage 6 call2 resolution:

- Stage 6 call2 retried only R19-U4+R19-U5 on Haiku 4.5 AU. R3 was not rerun.
- R19-U4 passed at `$0.0537`, under the `$0.40` planned cap and `$0.48` hard
  ceiling, with exactly two subagents, source-of-truth reconciliation, and no
  failure-loop events.
- R19-U5 passed at `$0.0309`, under the `$0.30` planned cap and `$0.36` hard
  ceiling, with exactly three subagents, one expected missing-child
  file-not-found event, and no repeated guard/exec loop.
- Claude Phase C returned `GENUINE_PASS` for both members.
- `r_tier_gate.py --test R19-U4` and `--test R19-U5` passed.
- Call1 diagnostic/non-ready spend remains preserved in the metrics ledger and
  evidence files.
- Next optimized stage is Stage 7: R16 long app build, subject to fresh Phase A
  approval, budget/headroom check, and recurrence watch for R14/R19-U3-style
  tool loops.

2026-05-06 Stage 7 R16 resolution:

- Claude Phase A iter2 approved R16 after the runner was tightened to hash
  `tests/test_app.py` before and after the model run.
- AWS budget was healthy before spend. Local R-tier ledger before R16 was
  `$1.4653`; R16 had no prior spend.
- R16 call1 ran on Haiku 4.5 AU and passed at `$0.0205`, under the `$1.00`
  planned cap and `$1.20` hard retry ceiling.
- The model read `tests/test_app.py` before writing `app.py`, completed the
  Flask CRUD fixture, and pytest reported `3 passed`.
- All required `software_builder_subchecks` were true. Cache evidence was
  numeric (`cache_read_tokens=7597`, `cache_write_tokens=10154`,
  `cache_hit_pct=0.4279`), so no `MODEL_LIMITATION` row was needed.
- Compaction evidence was explicitly forced/local, not natural long-context
  pressure, per the approved R16 bounded-fixture allowance.
- The R14/R19-U3 repeated guard/edit/write/exec loop did not recur:
  two tool calls, zero repeated calls, zero failure-loop events, and empty
  guard failure class counts.
- R16 surfaced a local telemetry aggregation bug: when an audit directory
  contained both the session JSONL and forced/local compaction JSONL, the
  builder read only one file. `build_telemetry.py` now reads all JSONL files in
  an audit directory, a zero-cost lock test covers this, and R16 telemetry was
  rebuilt from the preserved AWS evidence.
- Claude Phase C returned `GENUINE_PASS`, and
  `r_tier_gate.py --test R16` passed.
- Next optimized stage is Stage 8: R19-U10 long coherence, subject to fresh
  Phase A approval and AWS Budget/headroom check.

2026-05-06 Stage 8 R19-U10 resolution:

- Claude Phase A approved the optimized prebuilt transcript/churn substitution
  for R19-U10. The design explicitly avoided 150 live Bedrock calls because
  true 150-call execution is not valid under the `$0.50` cap without user
  approval.
- AWS budget was healthy before spend. Local R-tier ledger before R19-U10 was
  `$1.4858`; R19-U10 had no prior spend.
- R19-U10 call1 ran on Haiku 4.5 AU and passed at `$0.0134`, under the `$0.50`
  planned cap and `$0.60` hard retry ceiling.
- The model wrote `final_coherence_report.md` with the early codename
  `HYDRA-LIME`, checksum `kiwi-1842`, latest runtime `Python 3.12`, latest
  owner `Priya`, and final task marker `create_coherence_report`.
- The stale `Python 3.10` preference did not win.
- Evidence includes a 150-logical-turn prebuilt transcript fixture, three typed
  prebuilt `compact_auto_end` events, two prebuilt `model_switch` events,
  numeric cache fields, and one real `write_file` tool call.
- This pass proves the approved optimized substitution only. It does not claim
  150 live Bedrock calls, live model switching, or natural threshold-triggered
  compaction.
- The R14/R19-U3 repeated guard/edit/write/exec loop did not recur:
  one tool call, zero repeated calls, zero failure-loop events, and empty guard
  failure class counts. Claude Phase C noted the recurrence watch had limited
  surface area because the run completed in one turn.
- `build_telemetry.py` now extracts `model_switch_events` and a zero-cost lock
  test covers that canonical telemetry field.
- Claude Phase C returned `GENUINE_PASS`, and
  `r_tier_gate.py --test R19-U10` passed.
- Optimized stages 4 through 8 are now complete. Continue any remaining
  required R-tier rows according to the final readiness docs before any final
  production-readiness claim.

2026-05-06 remaining cleanup verification:

- R1 was refreshed from disk after the optimized sequence. Existing call2
  evidence remains valid: Phase C `GENUINE_PASS`, `r_tier_gate.py --test R1`
  passed, and call1 Unicode-crash spend remains preserved as diagnostic.
  No redundant AWS rerun was performed.
- R2 was refreshed from disk. Existing call1 evidence remains valid:
  Phase C `GENUINE_PASS`, `r_tier_gate.py --test R2` passed, and it remains
  the real compaction/recall proof.
- R4 is a real stop/defer gate, not an AWS candidate to run blindly.
  `ESCALATION-R4.md` documents that v5.0.1 did not yet ship the A-16
  time-based cold-cache microcompact path that original R4 claims to measure.
  Running R4 as written before A-16 exists would spend money to confirm a known
  missing feature.

2026-05-06 user production-scope decision:

- R4 deferment is not accepted for the final production-readiness package.
- Implement A-16 time-based cold-cache microcompact before production.
- Reshape R4 only as needed to test the same production code path without a
  30-minute wallclock wait, for example by using an injectable clock or test
  threshold. The test claim must remain cold-cache/time-based microcompact, not
  a weaker idle-resume-only substitute.
- After A-16, R4 must go through normal Phase A, AWS execution,
  telemetry/quality/metrics, Phase C, and `r_tier_gate.py --test R4`.
- The remaining matrix rows that failed per-test gates
  (`R6`, `R7`, `R8`, `R9`, `R10`, `R11`, `R12`, `R17`,
  `R18-E1`, `R18-E2`, `R18-E3`, `R18-E4`, `R18-E5`,
  `R18-E6`, `R18-E8`, `R18-E9`, `R18-E10`, `R18-E11`,
  `R18-E12`, `R18-E13`, `R18-E14`, `R18-E15`, `R19-U8`,
  and `R19-U9`) must each receive concrete per-test evidence, an optimized
  bundle mapping with artifacts strong enough to pass `r_tier_gate.py --test`,
  or an explicit reviewed/user-approved disposition.

2026-05-06 R4/A-16 resolution:

- A-16 time-based cold-cache microcompact is present in `QueryEngine.run()` and
  is now covered by local lock tests plus R4 real-AWS evidence.
- R4 Phase A iter1 returned `APPROVE_FOR_AWS_CALL`.
- AWS Budget was healthy before spend. Local R-tier ledger before R4 was
  `$1.4992`; R4 prior spend was `$0.0000`.
- R4 call1 ran on Haiku 4.5 AU and passed at `$0.0230`, under the `$0.20`
  planned cap and `$0.24` hard retry ceiling.
- The R4 runner used the supported injectable threshold
  `CONFIG.cold_cache_threshold_seconds=1` and a seeded idle gap to exercise the
  same production cold-cache branch without a 30-minute wall-clock wait.
- Evidence includes typed `compact_micro_start` and `compact_micro_end` events
  with `trigger=cold_cache`, `microcompact_applied=true`,
  `microcompact_saved_tokens=50360`, two cleared old tool-result markers,
  numeric cache fields, and no repeated tool/failure loop.
- Claude Phase C returned `GENUINE_PASS`, and
  `r_tier_gate.py --test R4` passed.
- The older `ESCALATION-R4.md` remains preserved as superseded historical
  deferment evidence. Final readiness must describe R4 as "A-16 cold-cache code
  path validated on real Bedrock with supported injectable threshold," not as a
  literal 30-minute wall-clock production wait.

## Expected Confidence

Passing local gates alone is not enough for 98% confidence. Passing all gates
above, including the optimized AWS matrix and final independent review, is the
target evidence package for 98% confidence for the intended personal
SageMaker software-building use case.
