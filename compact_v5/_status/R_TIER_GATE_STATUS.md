# R-tier Gate Status

> **2026-05-04 OVERRIDE**: R-tier review approval for the v5 completion redo
> must come from Claude Code CLI reviewer prompts under
> `_status/v5_completion_audit/`, not Codex CLI review.

Date: 2026-05-05

Purpose: make the real-AWS validation fail closed until every test has enough
review, telemetry, cost accounting, and persisted evidence to support the
v5.0.1 production-readiness decision.

## Gate commands

Run these before any new AWS call:

```bash
cd D:/Github/sagemaker-coding-agent
py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root .
```

Run this after a specific test passes, before advancing:

```bash
py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root . --test R1
```

Run this before each AWS batch to inspect cloud budget headroom:

```bash
aws budgets describe-budget --account-id 903039434627 --budget-name Bedrock-Monthly-50
```

The local gate enforces:

- `r_tier_test_matrix.json` exists, contains all 42 required scenarios, and
  totals exactly `$14.25`
- the 42 v5-only scenarios are materialized as executable R-tier tests
- `_status/r_tier_metrics.jsonl` exists and total local recorded spend stays
  at or below `$14.25`
- per-scenario local spend stays at or below the scenario cap
- a completed test has phase A prompt/review, raw AWS log, phase C review,
  telemetry JSON, quality review, metrics row, and review-log row
- telemetry JSON has the required review schema and non-empty `per_turn`

## AFK worker prompt

Use `compact_v5/docs/CODEX_AFK_WORKER_PROMPT.md` for a fresh autonomous
worker session. It contains:

- exact first commands
- required docs to read
- per-test loop
- AWS Budget checks
- local cost cap rules
- mandatory files
- commit/push requirements
- escalation triggers where the worker must stop and wait for the user

AFK is allowed only under that prompt. The worker may continue test by test
while all gates pass, but must stop on any escalation trigger.

Canonical test queue:

- machine-readable: `compact_v5/_status/r_tier_test_matrix.json`
- human-readable: `compact_v5/_status/R_TIER_PENDING_TESTS.md`

Operating contracts:

- evidence: `compact_v5/_status/R_TIER_EVIDENCE_CONTRACT.md`
- worker behavior: `compact_v5/_status/R_TIER_WORKER_BEHAVIOR_CONTRACT.md`

## Current status

AWS/R-tier execution has started under
`v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md`. Do not use stale
queue order from `R_TIER_PENDING_TESTS.md`.

Completed and pushed:

- R13: Phase C `GENUINE_PASS`, `r_tier_gate.py --test R13` passed.
- R15: Phase C `GENUINE_PASS`, `r_tier_gate.py --test R15` passed.
- R14: Phase C `GENUINE_PASS`, `r_tier_gate.py --test R14` passed. Artifact
  pass only; serious process-quality follow-up is open in
  `R_TIER_PROCESS_QUALITY_FOLLOWUPS.md`.
- R19-U1: Stage 4 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R19-U1` passed. Low follow-up open for direct
  chat-text clarification instead of `ask_user`.
- R19-U2: Stage 4 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R19-U2` passed.
- R19-U3: Stage 5 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R19-U3` passed. R14/R19-U3 process blocker did not
  recur; one isolated `bash_cd_blocked` event remains a quality penalty, not a
  blocker.
- R19-U6: Stage 5 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R19-U6` passed.
- R19-U7: Stage 5 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R19-U7` passed with `breaker_fired=true`.
- R18-E7: Stage 5 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R18-E7` passed. Call1 diagnostic cap exceed remains
  preserved; call2 passed under the $0.10 planned cap.

- R19-U4: Stage 6 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R19-U4` passed. Call1 diagnostic bundle-blocked spend
  remains preserved.
- R19-U5: Stage 6 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R19-U5` passed. Call1 diagnostic predicate-failure
  spend remains preserved.

The local no-AWS gate still passes for suite materialization and cost guard:

- executable R-tier coverage exists for all 42 required scenario markers
- R6-R16, R18-E1..E15, and R19-U1..U10 are materialized in
  `MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py`
- those new specs are zero-cost Phase A contracts, not AWS pass evidence
- `_status/r_tier_metrics.jsonl` remains the spend ledger and must stay at or
  below `$14.25`
- `_status/r_tier_review_log.md` remains the review ledger for READY or
  ESCALATED rows
- `_status/r_tier_test_matrix.json` is initialized and totals `$14.25`
- `_status/R_TIER_PENDING_TESTS.md` lists every pending test, benefit, and
  ready criterion

Do not claim the R-tier suite is production-ready until each required scenario
has Claude-reviewed Phase A approval, allowed AWS/mock execution, phase C
review, telemetry, quality evidence, metrics, and `r_tier_gate.py --test
<TEST>` pass, and the open process-quality follow-ups are resolved or accepted
by final review.

## Stage 5 Call1 Diagnostic Stop And Call2 Resolution

Stage 5 call1 ran on 2026-05-06 and stopped correctly:

- R19-U3: diagnostic/non-ready spend `$0.1090`; artifact path mostly succeeded
  but the R14 repeated failed tool-loop class recurred. Status:
  `PROCESS_BLOCKER_LOCAL_FIX_PENDING_CLAUDE_REVIEW`.
- R18-E7: diagnostic/non-ready spend `$0.1022`; exceeded the `$0.10` cap before
  READY evidence. Status: `PROCESS_BLOCKER_LOCAL_FIX_PENDING_CLAUDE_REVIEW`.
- R19-U6: functional member pass inside blocked bundle.
- R19-U7: functional member pass inside blocked bundle with `breaker_fired=true`.

No prior failed/non-ready spend may be deleted, hidden, or globally reset.
The R14/R19-U3 process blocker was fixed locally, approved by Claude CLI, and
verified by Stage 5 call2 on Haiku. Continue recurrence watch in R16 and later
software-builder tests; any non-intentional repeated guard-class loop remains a
matrix stop condition.

Local blocker fix summary:

- `compact_v5/_status/codex_reviews/r-tier-R14-R19-U3-process-blocker-fix-summary.md`

## Fixes landed in this hardening pass

- `core/query_engine.py` now emits one `chat_response` audit event per Bedrock
  turn, containing usage, cache fields, thinking text, assistant text,
  stop reason, and tool-call summaries. This allows real per-turn telemetry
  instead of relying only on tool-dispatch timing heuristics.
- `build_telemetry.py` now reads both legacy top-level `response` payloads and
  the new `parameters.response` payload emitted by QueryEngine.
- `r_tier_gate.py` was added as a local evidence/cost guard.

## Mock verification

Zero-AWS tests run after the hardening pass:

```text
py -3.11 -m pytest tests/integration/test_build_telemetry.py tests/integration/test_unicode_safe_output.py tests/integration/test_r_tier_gate.py -q
15 passed

py -3.11 -m pytest tests/integration/test_block_b.py -q
28 passed, 1 skipped
```

Zero-AWS R-tier readiness verification on 2026-05-04:

```text
py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root .
R-tier gate PASSED

$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py -q
108 passed

$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_r_tier_gate.py -q
7 passed

$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/r_tier -q
108 passed, 6 skipped
```

## AWS spend rule

No additional AWS call should run unless:

1. the relevant test has passed phase A review,
2. the expected remaining local cap is enough for the test,
3. AWS Budget headroom is confirmed,
4. raw output is teed to `_status/codex_reviews/r-tier-<TEST>-aws-call<N>.log`,
5. telemetry and quality files are generated immediately after the call,
6. `r_tier_gate.py --test <TEST>` passes before moving on.

## AWS Budget snapshot

Latest checked during Stage 6 on 2026-05-06 with:

```bash
aws budgets describe-budget --account-id 903039434627 --budget-name Bedrock-Monthly-50
```

Result:

- budget limit: `$50.00`
- actual spend: `$0.00`
- forecasted spend: `$0.047`
- health status: `HEALTHY`
- local R-tier ledger before Stage 6 call1: `$1.2912`
- Stage 6 call1 diagnostic/non-ready spend added:
  - R19-U4: `$0.0529`
  - R19-U5: `$0.0366`
- Stage 6 call2 READY spend added:
  - R19-U4: `$0.0537`
  - R19-U5: `$0.0309`
