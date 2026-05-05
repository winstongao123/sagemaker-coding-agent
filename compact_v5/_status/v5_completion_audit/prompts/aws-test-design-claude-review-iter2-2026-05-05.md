# AWS/R-Tier Test Design Re-Review Prompt Iter2

You are Claude Code acting as an independent reviewer for the v5.0.1
software-builder AWS/R-tier validation design.

Repository:

`D:\Github\sagemaker-coding-agent`

Do not trust this prompt as evidence. Use it only as navigation. Read the
repository files from disk with read-only tools before deciding.

## Required Context To Read

Read these files first:

1. `compact_v5/_status/v5_completion_audit/reviews/aws-test-design-claude-review-2026-05-05.md`
2. `compact_v5/_status/v5_completion_audit/PS_AWS_TEST_EXECUTION_LOOP.md`
3. `compact_v5/_status/v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md`
4. `compact_v5/_status/v5_completion_audit/TEST_CASE_PREP.md`
5. `compact_v5/_status/v5_completion_audit/PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md`
6. `compact_v5/_status/R_TIER_EVIDENCE_CONTRACT.md`
7. `compact_v5/_status/r_tier_test_matrix.json`
8. `compact_v5/_status/scripts/r_tier_gate.py`
9. `compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py`
10. `compact_v5/MAIN/agent/tests/r_tier/test_software_project_workflow_contracts.py`

## Worker Notes

After your prior `APPROVE_WITH_FIXES / NOT_READY` review, the worker made these
plan/contract changes:

- added `PS_AWS_TEST_EXECUTION_LOOP.md`;
- added R16 typed `software_builder_subchecks` to the evidence contract;
- added R13 `score_passed>=4` and `score_total=5` pass threshold;
- added bundle-vs-cap policy for R19-U1+U2 and R19-U3+U6+U7;
- added determinism/retry/cost-cap-hit attempt policy;
- added R16/R19-U10 cost-budget model and `SOFTWARE-*` precondition gate;
- updated `r_tier_gate.py` to enforce R13/R16/R19-U7 selected evidence;
- updated zero-cost contract tests, which passed locally:
  `117 passed`.

These notes are navigation only. Verify from files.

## Required Review

Check whether the six blocking findings from your prior review are now
resolved:

1. R16 sub-check enforcement.
2. R16/R19-U10 cost-cap justification.
3. `SOFTWARE-*` block closure precondition.
4. R13 minimum pass threshold.
5. Bundle-vs-cap charging policy.
6. Re-run/determinism/cost-cap-hit attempt policy.

Also re-check per-test design for:

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

## Required Output

Return exactly these sections:

1. `REVIEWED FILES`
2. `PRIOR BLOCKER RESOLUTION`
3. `PER-TEST READINESS`
4. `REMAINING BLOCKING FINDINGS`
5. `REMAINING NON-BLOCKING FINDINGS`
6. `VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT`
7. `TEST DESIGN DECISION: READY_FOR_PHASE_A_PER_TEST_REVIEW | NOT_READY`

