# PS AWS Test Execution Loop

Date: 2026-05-05

Status: ACTIVE_PRE_SPEND_GATE

## Purpose

This document defines the mandatory loop for every real AWS/R-tier validation
test. It exists to prevent expensive tests from becoming one-off anecdotes.
Each test must produce traceable evidence that v5 is production-ready for
long-running software engineering, or it must produce a clear fix/escalation
path. A functional artifact pass is not enough by itself: the run must also
show acceptable process quality for tool use, coding discipline, status/memory
continuity, subagent/reviewer coordination, context/compaction behavior, and
token/cache/cost control.

## Test Design Review Before Spend

Before any AWS call for a test:

1. The worker preflight must read the test spec, fixture, acceptance criteria, cost cap,
   and required evidence files from disk.
2. The worker must write a Phase A preflight summary that names:
   - test id and purpose;
   - exact prompt/fixture/runner paths;
   - cost cap and expected model;
   - capabilities measured;
   - overlap analysis explaining why the test is not redundant with cheaper
     local or earlier AWS tests;
   - process-quality risks being measured, including tool loops, wasted calls,
     search-before-edit discipline, subagent/reviewer usefulness, context loss,
     and memory/status/checkpoint continuity where applicable;
   - required telemetry and traceability files;
   - stop conditions.
3. Claude CLI must independently review the Phase A design from disk and return
   either `APPROVE_FOR_AWS_CALL` or a blocking finding.
4. User approval and budget headroom must be confirmed after Claude approval
   and before spend.

No Phase A approval means no AWS call.

## Required Per-Test Loop

For each AWS test:

1. **Worker preflight**
   - confirm local gates still pass;
   - confirm the test is still needed and non-overlapping;
   - confirm cost cap and stop rules;
   - save the filled Phase A prompt.
2. **Claude Phase A review**
   - Claude reads test design and evidence requirements from disk;
   - Claude must approve `APPROVE_FOR_AWS_CALL`;
   - save prompt, stdout review, stderr log, and review-ledger row.
3. **explicit spend approval**
   - user approval is required for the AWS call;
   - no tag/final-ready claim is allowed at this stage.
4. **AWS execution**
   - run only the approved test;
   - capture full stdout/stderr raw log;
   - enforce cost cap and stop rules.
5. **Metadata capture**
   - write telemetry JSON;
   - append metrics JSONL row;
   - write quality review;
   - write review-log row;
   - record token, cache, cost, tool, compaction, subagent/reviewer, duration,
     retry, and outcome evidence where applicable.
6. **Worker post-run review**
   - inspect output, artifacts, telemetry, final code, and process quality;
   - classify functional result and process result separately;
   - identify fixes for semantic bugs, weak assertions, inefficient tool loops,
     context/memory loss, poor subagent coordination, missing attribution, or
     unacceptable token/cache/cost behavior;
   - run `r_tier_gate.py --test <TEST>`.
7. **Claude Phase C review**
   - Claude independently reviews raw logs, telemetry, quality review, metrics,
     produced artifacts, and gate result;
   - Claude must return `GENUINE_PASS` before the test can be called ready;
   - if Claude agrees the artifact is correct but process quality is weak, the
     weakness must be written to `_status/R_TIER_PROCESS_QUALITY_FOLLOWUPS.md`
     and explicitly resolved, accepted, or promoted to a blocker before final
     production-readiness review.
8. **Fix/retry loop**
   - if the test fails, fix code/test/design only with recorded rationale;
   - if the artifact passes but process quality is unacceptable for the user's
     goal of a strong long-running coding agent, fix the harness, prompt,
     tool guidance, or implementation and rerun the appropriate review/test
     loop;
   - if test design was wrong or overlapping, update the test case and rerun
     Phase A review before spending again;
   - if implementation was wrong, fix implementation and rerun local gates
     before retrying AWS.
9. **Escalation**
   - if the same test cannot be fixed after 3 meaningful fix/retry attempts,
     stop and write `ESCALATION-<TEST>.md`;
   - do not continue AWS testing until the user decides.

## Diagnostic Spend And Retry Allowance

Prior AWS calls that fail or stop on process quality remain part of the
evidence and spend ledger. Do not delete, rewrite, hide, or globally reset
failed/non-ready spend.

The matrix cap is the planned budget. The hard local retry ceiling is the
planned cap plus the user-approved 20% buffer (`cost_cap_usd * 1.20`). This
buffer exists to avoid false stops from small real-model variance; it is not a
permission to ignore process-quality blockers or rerun blindly.

A retry allowance may be documented only for the affected item, and only after
the fix summary explains:

- why the prior spend was diagnostic/non-ready;
- what implementation, harness, or process behavior changed;
- why the retry is expected to stay under the buffered hard ceiling;
- what exact per-test planned cap and buffered ceiling apply to the retry.

For the 2026-05-06 Stage 5 stop, no AWS retry is allowed until the R14/R19-U3
process blocker is fixed locally and Claude CLI approves the fix/retry path
from disk.

R14/R19-U3 retry model rule:

- Use Haiku 4.5 AU only for R14 and R19-U3. Do not switch these retries to
  Sonnet to bypass process-quality failure.
- Artifact correctness is not sufficient. Phase C and the worker quality review
  must inspect tool count, failure-loop telemetry, guard failure classes,
  visible search/read-before-edit ordering where applicable, and repeated failed
  exec recovery behavior.
- If Haiku cannot pass after the local fix and Claude-reviewed retry path, stop
  and escalate instead of changing models.

## Optimized-Test Requirement

Every AWS test must justify why it is high-signal. A good AWS test should prove
multiple production qualities at once, such as:

- software artifact correctness;
- coding quality, including minimal unrelated edits and meaningful tests;
- tool selection and search/edit efficiency;
- checkpoint/save/resume behavior;
- status/todo/memory continuity;
- compaction survival;
- token/cache/cost behavior;
- subagent/reviewer usefulness;
- failure recovery and no-drift close discipline.

For this project, "optimized" means one run should reveal several qualities at
once. It does not mean accepting a pass that only proves final output while
hiding poor tool use, lost context, weak memory/status behavior, or wasteful
subagent/reviewer coordination.

Do not create an AWS test for a simple behavior that is already fully covered
by a local zero-cost test unless real-model behavior is specifically the thing
being measured.

## Evidence Locations

Use the evidence contract in `compact_v5/_status/R_TIER_EVIDENCE_CONTRACT.md`.
At minimum, every AWS call must create or update:

- `_status/codex_reviews/r-tier-<TEST>-phaseA-iter<N>-prompt.txt`
- `_status/codex_reviews/r-tier-<TEST>-phaseA-iter<N>.md`
- `_status/codex_reviews/r-tier-<TEST>-aws-call<N>.log`
- `_status/r-tier-<TEST>-aws-call<N>-telemetry.json`
- `_status/r-tier-<TEST>-aws-call<N>-quality.md`
- `_status/r_tier_metrics.jsonl`
- `_status/r_tier_review_log.md`
- `_status/codex_reviews/r-tier-<TEST>-phaseC-iter<N>.md`

If a stop trigger fires, write:

- `_status/codex_reviews/ESCALATION-<TEST>.md`

## Final Readiness

The project is not production-ready merely because AWS tests ran. It is ready
for the final claim only when:

- every selected AWS test has Phase A approval, execution evidence, telemetry,
  worker post-run review, Phase C Claude `GENUINE_PASS`, and gate pass;
- all failed tests are fixed or escalated with user decision;
- all process-quality follow-ups are closed, explicitly accepted by the user,
  or promoted into blocking work;
- final worker self-review and final Claude production-readiness review both
  approve the complete evidence package.
