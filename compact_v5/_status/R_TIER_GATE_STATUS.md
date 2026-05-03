# R-tier Gate Status

Date: 2026-05-03

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

## Current status

The gate currently fails, intentionally:

- executable R-tier coverage exists for R1 and R17 only
- R2-R16, R18-E1..E15, and R19-U1..U10 are not yet materialized as test code
- `_status/r_tier_metrics.jsonl` is initialized at `$0.00` local recorded spend
- `_status/r_tier_review_log.md` is initialized with its table header

Do not claim all 42 tests are ready until this gate passes.

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

## AWS spend rule

No additional AWS call should run unless:

1. the relevant test has passed phase A review,
2. the expected remaining local cap is enough for the test,
3. AWS Budget headroom is confirmed,
4. raw output is teed to `_status/codex_reviews/r-tier-<TEST>-aws-call<N>.log`,
5. telemetry and quality files are generated immediately after the call,
6. `r_tier_gate.py --test <TEST>` passes before moving on.

## AWS Budget snapshot

Checked on 2026-05-03 with:

```bash
aws budgets describe-budget --account-id 903039434627 --budget-name Bedrock-Monthly-50
```

Result:

- budget limit: `$50.00`
- actual spend: `$0.00`
- forecasted spend: `$0.051`
- health status: `HEALTHY`
