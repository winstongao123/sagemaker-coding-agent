# PS AWS Test Execution Loop

Date: 2026-05-05

Status: ACTIVE_PRE_SPEND_GATE

## Purpose

This document defines the mandatory loop for every real AWS/R-tier validation
test. It exists to prevent expensive tests from becoming one-off anecdotes.
Each test must produce traceable evidence that v5 is production-ready for
long-running software engineering, or it must produce a clear fix/escalation
path.

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
   - inspect output, artifacts, telemetry, and final code;
   - classify pass/fail and identify fixes;
   - run `r_tier_gate.py --test <TEST>`.
7. **Claude Phase C review**
   - Claude independently reviews raw logs, telemetry, quality review, metrics,
     produced artifacts, and gate result;
   - Claude must return `GENUINE_PASS` before the test can be called ready.
8. **Fix/retry loop**
   - if the test fails, fix code/test/design only with recorded rationale;
   - if test design was wrong or overlapping, update the test case and rerun
     Phase A review before spending again;
   - if implementation was wrong, fix implementation and rerun local gates
     before retrying AWS.
9. **Escalation**
   - if the same test cannot be fixed after 3 meaningful fix/retry attempts,
     stop and write `ESCALATION-<TEST>.md`;
   - do not continue AWS testing until the user decides.

## Optimized-Test Requirement

Every AWS test must justify why it is high-signal. A good AWS test should prove
multiple production qualities at once, such as:

- software artifact correctness;
- tool selection and search/edit efficiency;
- checkpoint/save/resume behavior;
- status/todo/memory continuity;
- compaction survival;
- token/cache/cost behavior;
- subagent/reviewer usefulness;
- failure recovery and no-drift close discipline.

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
- final worker self-review and final Claude production-readiness review both
  approve the complete evidence package.
