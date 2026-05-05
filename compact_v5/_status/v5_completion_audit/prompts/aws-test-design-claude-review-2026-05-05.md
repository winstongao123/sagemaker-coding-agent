# AWS/R-Tier Test Design Review Prompt

You are Claude Code acting as an independent reviewer for the v5.0.1
software-builder AWS/R-tier validation design.

Repository:

`D:\Github\sagemaker-coding-agent`

Do not trust this prompt as evidence. Use it only as navigation. Read the
repository files from disk with read-only tools before deciding.

## Required Context To Read

Read these files first:

1. `compact_v5/_status/v5_completion_audit/PS_AWS_TEST_EXECUTION_LOOP.md`
2. `compact_v5/_status/v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md`
3. `compact_v5/_status/v5_completion_audit/TEST_CASE_PREP.md`
4. `compact_v5/_status/v5_completion_audit/PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md`
5. `compact_v5/_status/v5_completion_audit/THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`
6. `compact_v5/_status/R_TIER_EVIDENCE_CONTRACT.md`
7. `compact_v5/_status/r_tier_test_matrix.json`
8. `compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py`
9. `compact_v5/MAIN/agent/tests/r_tier/test_software_project_workflow_contracts.py`

## Review Goal

Review whether the AWS/R-tier test design is ready to validate v5 as a
long-running software engineering agent.

Focus on:

- whether the selected AWS scenarios are optimized and non-overlapping;
- whether each expensive test proves multiple production qualities;
- whether local zero-cost tests cover cheap/simple checks before AWS spend;
- whether each test has clear acceptance criteria, telemetry, metadata,
  traceability, and stop rules;
- whether the loop requires worker preflight, Claude Phase A review, explicit
  spend approval, AWS execution, metadata capture, worker post-run review,
  Claude Phase C review, fix/retry, and escalation after 3 failed meaningful
  attempts;
- whether the plan can produce hard evidence for production readiness in
  software engineering use, including subagents/reviewers, memory, status,
  todos, compaction, cache, costs, tool use, and no-drift gates.

## Required Per-Test Review

Review these scenarios individually:

- R13
- R14
- R15
- R16
- R19-U1
- R19-U2
- R19-U3
- R19-U6
- R19-U7
- R19-U10

For each scenario, state:

- purpose;
- whether it is non-overlapping or redundant;
- bundled capabilities measured;
- required evidence;
- missing design/test/telemetry risks;
- whether it is approved for later Phase A execution design.

Do not approve from aggregate statements alone.

## Required Output

Return exactly these sections:

1. `REVIEWED FILES`
2. `PER-TEST REVIEW`
3. `OVERLAP / OPTIMIZATION ASSESSMENT`
4. `EVIDENCE AND TRACEABILITY ASSESSMENT`
5. `BLOCKING FINDINGS`
6. `NON-BLOCKING FINDINGS`
7. `VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT`
8. `TEST DESIGN DECISION: READY_FOR_PHASE_A_PER_TEST_REVIEW | NOT_READY`

Use `REJECT` if any selected AWS scenario is clearly redundant, lacks evidence
requirements, lacks stop rules, or cannot validate the software-builder goal.

