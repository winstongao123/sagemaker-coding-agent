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
production readiness.

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
   and recovery behavior.
8. Final independent review approves the complete code, docs, test, telemetry,
   and AWS evidence package.

## Optimization Principle

Use small zero-cost tests to catch simple breakage first.
Use AWS only for tests that reveal multiple production qualities in one run.
Do not duplicate a simple local assertion in a separate AWS test unless the
real model behavior is the point being evaluated.

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

| Test | Cap | Phase A budget model |
|---|---:|---|
| R13 | $0.50 | 5 bounded tasks, max 1 model attempt per task plus one verification/synthesis turn. READY requires at least 4/5 passing tasks and no unrelated edits; 5/5 is the target. |
| R16 | $1.00 | Bounded small Flask CRUD fixture, max 8 primary model turns, local tests after edits, forced/local compaction evidence where possible. If Phase A estimates exceed cap, do not spend; ask user to approve cap change or shrink fixture. |
| R19-U10 | $0.50 | 150 logical turns may be represented by a prebuilt transcript/churn fixture plus a small number of real model turns that must use pre-compaction facts. If true 150 Bedrock calls are required, this cap is not valid and Phase A must stop for user approval. |

Bundle policy:

- Stage 4 can bundle R19-U1+R19-U2. Cap is the sum: $0.40.
- Stage 5 can bundle R19-U3+R19-U6+R19-U7+R18-E7. Cap is the sum: $1.00.
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

## Expected Confidence

Passing local gates alone is not enough for 98% confidence. Passing all gates
above, including the optimized AWS matrix and final independent review, is the
target evidence package for 98% confidence for the intended personal
SageMaker software-building use case.
