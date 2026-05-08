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

## Pre-AWS Coding-Ability Hardening

The R-tier gate proves the 42-scenario matrix and zero-cost readiness contracts
are materialized. It does not by itself prove that every software-writing
scenario is already an executable real-AWS task.

The third deep scan for long-running software-builder readiness is now a
pre-AWS input:

- `compact_v5/_status/v5_completion_audit/THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`

Accepted implement-now gaps from that scan must be implemented, locally tested,
documented, and independently reviewed before using AWS results to claim
production readiness.

Required zero-cost local tests from the Claude third-scan review:

- `todo_write` state survives `/save` + `/resume` in a fresh process/session.
- `/done` refuses with explicit reason when status is stale, required tests are
  missing, required review evidence is missing, or last verification failed.
- shell timeout kills a real sleeping child process tree; sentinel-file tests
  must prove no orphan process survives.
- an actual auto-compact or microcompact run emits typed audit actions consumed
  by `build_telemetry.py`.

The optimized pre-spend validation plan is:

- `compact_v5/_status/v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md`
- `compact_v5/_status/v5_completion_audit/SOFTWARE_BUILDER_BLOCK_REVISIT_PLAN.md`
- `compact_v5/_status/v5_completion_audit/PS_AWS_TEST_EXECUTION_LOOP.md`

That plan is the review target for the 98% confidence claim. It bundles
software-writing capabilities into high-signal AWS runs instead of creating
many overlapping calls.

The revisit plan prevents churn: completed blocks stay closed unless local
tests, strict audit, optimized AWS evidence, telemetry, or Claude final review
identify a concrete block-level gap.

Before using AWS to judge v5's real coding ability, explicitly harden and
Claude-review the software-project scenarios:

- R13: coding accuracy tasks with assertions.
- R14: multi-file refactor with hidden/cross-file dependency discovery.
- R15: planted-bug debugging with no unrelated edits.
- R16: long-session app build with tests and compaction/cache evidence.
- R19-U1/U2/U3/U6/U7/U10: UX coding edge cases for ambiguity,
  contradiction, hidden dependencies, tool-output recovery, repeated-tool
  circuit breaker, and long-session coherence.

Current readiness caveat: the AWS test design itself must have a clean Claude
design review before any per-test Phase A spend. The first full design review
found the framework sound but required plan/contract tightening around R16
typed sub-checks, R16/R19-U10 token-budget caps, `SOFTWARE-*` preconditions,
R13 pass threshold, bundle-vs-cap policy, and determinism/retry rules.
Those items are now captured in:

- `compact_v5/_status/R_TIER_EVIDENCE_CONTRACT.md`
- `compact_v5/_status/v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md`
- `compact_v5/_status/v5_completion_audit/PS_AWS_TEST_EXECUTION_LOOP.md`

These tests are crucial because the core product goal is an independent
long-running software-writing agent. The AWS/real-model test plan must verify
not only final artifacts but also the process quality:

- optimized prompt/context behavior;
- efficient token/cache usage;
- purposeful tool use with low repeated-call waste;
- auto-compaction without losing active work;
- status and memory integrity after compaction/resume;
- subagent/reviewer use when useful, without blind delegation;
- clear telemetry and quality-review evidence.

Each scenario must have:

- executable pytest or runner code, not only a marker/spec row;
- fixture files that resemble a real software project;
- acceptance assertions over produced code/tests/artifacts;
- telemetry and quality-review expectations;
- reviewer/subagent token, cost, cache, and usefulness evidence when a
  scenario uses `task` or reviewer-style subagents;
- Phase A Claude approval before any Bedrock spend;
- `r_tier_gate.py --test <TEST>` pass after execution.

Each real AWS test must follow the per-test loop in
`PS_AWS_TEST_EXECUTION_LOOP.md`: worker preflight, Claude Phase A design
review, explicit spend approval, AWS execution, metadata capture, worker
post-run review, Claude Phase C genuine-pass review, fix/retry loop, and
escalation after 3 unsuccessful meaningful fix/retry attempts on the same test.

Zero-cost contract coverage has been added at:

- `compact_v5/MAIN/agent/tests/r_tier/test_software_project_workflow_contracts.py`

Latest local verification:

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
C:\Users\winst\AppData\Local\Programs\Python\Python310\Scripts\pytest.exe compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py compact_v5/MAIN/agent/tests/r_tier/test_software_project_workflow_contracts.py -q
```

Result: `114 passed`.

This hardening can run after all v5 completion-audit blocks close and before
AWS/R-tier execution. It is not a reason to interrupt the current block redo,
but it is a blocker for claiming that AWS tests are ready to fully judge v5 as
a software-writing agent.

## Command Consolidation Rule For Software-Project Work

Do not add new `/project-*` slash commands for v5.0.1 unless explicitly
approved. v5 already has overlapping long-project primitives:

- `/status`
- `/save`
- `/resume`
- `/checkpoint`
- `/verify`
- `/done`
- `/phase`
- `/cost`
- `/context`
- `/dream`

If software-project governance needs to improve, enhance these existing
commands or their backing status/session/checkpoint behavior instead of adding
parallel command names. Preferred consolidation:

| Need | Existing command to enhance |
|---|---|
| project plan/current milestone | `/status`, `/phase` |
| persistent task state | `/save`, `/resume`, AGENT_STATUS.md |
| rollback point | `/checkpoint` |
| test/lint/security review | `/verify` |
| close gate / ready claim | `/done` |
| token/cost/context health | `/cost`, `/context` |
| memory consolidation | `/dream` |

Pre-AWS coding-ability tests should verify the consolidated command behavior,
not a new command surface. In particular, R16 and R19-U10 should cover long
software tasks using the existing commands for status, save/resume,
checkpoint, verification, and close discipline.
