# Optimized AWS Validation Plan

Date: 2026-05-05

Purpose: define the minimum high-signal AWS validation set needed before any
98% confidence production-readiness claim for v5 as a single-person
SageMaker software-building agent.

This plan does not approve AWS spend. It is the review target before spend.
Every AWS run still needs Phase A Claude approval, explicit user approval,
budget headroom, raw logs, telemetry, quality review, metrics, and
`r_tier_gate.py --test <TEST>` pass.

## Confidence Rule

Do not claim 98% confidence or production readiness unless all of these are
true:

1. All completion-audit blocks are closed, pushed, and Claude row-reviewed.
2. Full strict scope audit is clean.
3. Local and mock tests are green.
4. This optimized AWS plan is Claude-reviewed and approved before spend.
5. Each selected AWS software-writing scenario passes with required evidence.
6. Telemetry shows acceptable tool, token, cache, compaction, and recovery
   behavior.
7. Final independent review approves the complete code, docs, test, telemetry,
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
| 5 | R19-U3 + R19-U6 + R19-U7 recovery gate | handles hidden deps, bad output, repeated-call traps | alternative path, retry discipline, repeated-call counters, checkpoint/verify | bundles recovery failures instead of one AWS call per trap |
| 6 | R16 long app build | completes a small real app across a long session | app tests, `/status`, `/phase`, `/save`, `/resume`, `/checkpoint`, `/verify`, `/done`, `/cost`, `/context`, compaction/cache telemetry | broadest end-to-end software-builder proof |
| 7 | R19-U10 long coherence | preserves final task intent after compactions | final-task coherence, memory/status integrity, compaction events, cache trend, quality review | isolates long-coherence risk after R16 proves app build |

## Required Evidence Per AWS Run

Every selected AWS run must write:

- Phase A Claude review approving `APPROVE_FOR_AWS_CALL`;
- raw Bedrock log;
- telemetry with `tool_call_summary`, token counts, cache read/write counts,
  model id, cost, retries, and repeated-call signals;
- compaction/cache evidence when the scenario exercises long context;
- quality review with pass/fail reasoning;
- metrics JSONL row;
- review-log row;
- `r_tier_gate.py --test <TEST>` pass result.

## Stop Rules

Stop AWS execution and return to implementation/review if:

- local zero-cost tests fail;
- Claude Phase A rejects the scenario;
- budget headroom is not confirmed;
- a scenario needs more than the approved call budget;
- telemetry is missing or cannot be trusted;
- the model passes final artifacts but shows unsafe process behavior such as
  uncontrolled repeated calls, lost status, lost memory, or unexplained
  unrelated edits.

## Expected Confidence

Passing local gates alone is not enough for 98% confidence. Passing all gates
above, including the optimized AWS matrix and final independent review, is the
target evidence package for 98% confidence for the intended personal
SageMaker software-building use case.
