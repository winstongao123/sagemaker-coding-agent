# v5.0.1 Test Case Preparation

Date: 2026-05-04

Purpose: keep the final AWS/R-tier test set reviewable before any new spend.

## Current R-tier readiness

The local executable marker gate now passes without AWS:

```powershell
cd D:\Github\sagemaker-coding-agent
py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root .
```

Result:

```text
R-tier gate PASSED
```

New zero-cost readiness specs:

`compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py`

Coverage materialized:

- R6-R16
- R18-E1..E15
- R19-U1..U10

These are Phase A readiness contracts, not AWS pass claims. They require each
scenario to declare:

- matching `r_tier_test_matrix.json` cost cap
- real-vs-mock execution mode
- fixture/prompt/acceptance criteria
- required evidence files for `r_tier_gate.py --test <TEST>`
- explicit `RUN_REAL_BEDROCK` gating for real scenarios

## Verification

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py -q
```

Result:

```text
108 passed
```

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_r_tier_gate.py -q
```

Result:

```text
7 passed
```

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/r_tier -q
```

Result:

```text
108 passed, 6 skipped
```

## Before AWS

Before any actual AWS/R-tier call:

1. Claude must review the specific scenario Phase A prompt/spec.
2. The review must be saved under `_status/codex_reviews/`.
3. The review must explicitly approve `APPROVE_FOR_AWS_CALL`.
4. User approval and budget headroom must be confirmed.
5. Raw logs, telemetry, quality review, metrics, and review-log rows must be
   written immediately after execution.
6. `r_tier_gate.py --repo-root . --test <TEST>` must pass before advancing.
