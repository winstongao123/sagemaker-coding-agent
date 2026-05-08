# CODEX AFK WORKER PROMPT — v5.0.1 R-tier

Copy this prompt into a fresh worker session when the user is AFK.

---

You are continuing `sagemaker-coding-agent` v5.0.1 R-tier validation.

Repository: `D:/Github/sagemaker-coding-agent`
Branch: `v5-build`
Remote to push: `sageagent v5-build`
AWS account: `903039434627`
AWS region: `ap-southeast-2`
AWS budget: `Bedrock-Monthly-50`

## Mission

Make v5.0.1 production-release ready with minimum necessary real-AWS spend and
maximum hard evidence.

Run v5 only. Do not run v4 or Runnable. The comparison claim remains
architectural through PORT_LOG and PS problem fixes. Do not spend AWS on v4 or
Runnable.

Target R-tier cap: `$14.25 USD`.
AWS hard budget: `$50.00 USD`.

## First actions

```bash
cd D:/Github/sagemaker-coding-agent
git pull sageagent v5-build
git status --short --branch
py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root .
aws budgets describe-budget --account-id 903039434627 --budget-name Bedrock-Monthly-50
```

Read these before editing:

1. `compact_v5/_status/R_TIER_GATE_STATUS.md`
2. `compact_v5/_status/r_tier_test_matrix.json`
3. `compact_v5/_status/R_TIER_PENDING_TESTS.md`
4. `compact_v5/_status/R_TIER_EVIDENCE_CONTRACT.md`
5. `compact_v5/_status/R_TIER_WORKER_BEHAVIOR_CONTRACT.md`
6. `compact_v5/docs/CODEX_CONTEXT_v5_R_TIER.md`
7. `compact_v5/docs/PS_V5_TEST_PLAYBOOK.md`
8. `compact_v5/docs/PS_V5_TEST_SET.md`
9. `compact_v5/_status/R_TIER_REVIEW_TEMPLATE.md`
10. `compact_v5/_status/V5_BUILD_STATUS.md`
11. `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md`

## Current truth at prompt creation

- R1 and R17 are executable.
- R2-R16, R18-E1..E15, and R19-U1..U10 still need executable tests.
- R1 call #1 found a Unicode stdout crash after useful work completed.
- Fixes already pushed:
  - `7eeaa1e v5/r-tier: harden telemetry and evidence gate`
  - `b80d3ce v5/r-tier: record AWS budget snapshot`
- Ledgers are initialized:
  - `compact_v5/_status/r_tier_metrics.jsonl`
  - `compact_v5/_status/r_tier_review_log.md`
- `r_tier_gate.py` is the local fail-closed guard.
- `r_tier_test_matrix.json` is the canonical list of all 42 required scenarios,
  cost caps, benefits, and ready criteria. Do not silently add/drop tests.
- `R_TIER_EVIDENCE_CONTRACT.md` defines the required files and content.
- `R_TIER_WORKER_BEHAVIOR_CONTRACT.md` defines status, git, cost, and stop rules.

## Autonomy contract

You may work autonomously while the user is AFK if and only if all rules below
are followed.

You MUST stop and wait for the user if any escalation trigger fires.
Otherwise, keep going test by test.

## Escalation triggers — stop immediately

1. 3 AWS calls used for one test and still failing.
2. Any `SEMANTIC_BUG_DETECTED`.
3. AWS Budget actual or forecast reaches or exceeds `$40`.
4. Local total R-tier spend reaches or exceeds `$14.25`.
5. Bedrock auth, quota, account, or region error.
6. Two consecutive R-tests fail on AWS call #1.
7. Worker and Codex cannot agree after 3 review rounds.
8. A fix would require changing the product scope or dropping a test.
9. `r_tier_gate.py --test <TEST>` fails after a test was marked passed.

When stopping, write `compact_v5/_status/codex_reviews/ESCALATION-<TEST>.md`,
commit it, push it, then stop.

## Required status updates every step

Update and commit/push after each meaningful step:

- `_status/R_TIER_GATE_STATUS.md`
- `_status/R_TIER_PENDING_TESTS.md` if a test status changes
- `_status/r_tier_test_matrix.json` if a test status changes
- `_status/r_tier_metrics.jsonl`
- `_status/r_tier_review_log.md`
- `_status/V5_BUILD_STATUS.md` when high-level state changes
- `_status/codex_reviews/r-tier-<TEST>-...` prompt/review/log files
- telemetry and quality files for the test

Every commit must be pushed:

```bash
git push sageagent v5-build
```

## Cost monitoring before every AWS call

Run:

```bash
aws budgets describe-budget --account-id 903039434627 --budget-name Bedrock-Monthly-50
```

Proceed only if:

- `ActualSpend.Amount < 40`
- `ForecastedSpend.Amount < 40`
- local `r_tier_metrics.jsonl` total + next test cap <= `$14.25`

Use AU pricing assumptions:

- Haiku 4.5 AU: `$1.10/MTok` input, `$5.50/MTok` output
- Sonnet 4.5 AU: `$3.30/MTok` input, `$16.50/MTok` output
- cache reads are 10% of input price
- cache writes are 1.25x or 2x input price depending duration

## Per-test loop

For each scenario, do this in order.

### A. Materialize executable test if missing

Write the smallest test that actually falsifies the claim.
Prefer Haiku and low max turns. Use Sonnet only for R11/R17/R7 switch.
Use mock only where the playbook explicitly says mock is valid.

Run collect-only:

```bash
cd compact_v5/MAIN/agent
py -3.11 -m pytest tests/r_tier --collect-only -q
```

### B. Phase A review before AWS

Fill TEMPLATE A from `R_TIER_REVIEW_TEMPLATE.md`.
Save:

- `_status/codex_reviews/r-tier-<TEST>-phaseA-iter<N>-prompt.txt`
- `_status/codex_reviews/r-tier-<TEST>-phaseA-iter<N>.md`

Do not spend AWS unless Phase A says `APPROVE_FOR_AWS_CALL`.

### C. AWS call

Before call, kill Codex zombies if using Codex CLI review:

```bash
taskkill //F //IM codex.exe 2>$null
```

Run exactly one test and tee output:

```bash
cd compact_v5/MAIN/agent
$env:RUN_REAL_BEDROCK='1'
py -3.11 -m pytest tests/r_tier/<test_file>.py::<test_name> -q -s 2>&1 |
  Tee-Object -FilePath ../../_status/codex_reviews/r-tier-<TEST>-aws-call<N>.log
```

### D. After AWS call

Immediately generate telemetry:

```bash
py -3.11 compact_v5/_status/scripts/build_telemetry.py `
  --test <TEST> `
  --call <N> `
  --audit-log compact_v5/MAIN/agent/audit_logs `
  --raw-log compact_v5/_status/codex_reviews/r-tier-<TEST>-aws-call<N>.log `
  --output compact_v5/_status/r-tier-<TEST>-aws-call<N>-telemetry.json
```

Append one JSON row to `_status/r_tier_metrics.jsonl`.

If PASS:

- write worker quality review
- run Codex post-pass / quality review
- save `_status/codex_reviews/r-tier-<TEST>-phaseC-iter<N>.md`
- save `_status/r-tier-<TEST>-aws-call<N>-quality.md`
- append READY row to `_status/r_tier_review_log.md`
- run `py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root . --test <TEST>`

If FAIL:

- write diagnosis prompt and Codex review
- save `_status/codex_reviews/r-tier-<TEST>-phaseB-iter<N>.md`
- fix only after diagnosis approval
- add a mock lock test for any product bug found
- commit/push the fix
- re-run Phase A before the next AWS call

## Execution order

1. Finish R1 from current state.
2. R2 through R17.
3. R18-E1 through R18-E15.
4. R19-U1 through R19-U10.
5. Final full-codebase Codex review.
6. Generate `_status/FINAL_v5.0.1_PRODUCT_SUMMARY.md`.
7. Commit and push.
8. Stop for user F5 signoff. Do not tag final or ship without user.

## Production-ready definition

Do not say production-ready until all are true:

- all 42 scenarios have READY rows
- total local spend <= `$14.25`
- AWS Budget remains healthy
- zero unresolved semantic bugs
- final full-codebase review approves
- final summary exists
- every change and evidence file is pushed to `sageagent/v5-build`
- user gives F5 signoff

If all rules are clear, begin by updating `R_TIER_GATE_STATUS.md` with the
current step, then finish R1 Phase A and continue.
