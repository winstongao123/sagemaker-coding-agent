I've read all 10 required files. Now I'll write the review.

# REVIEWED FILES

Read from disk:

1. `compact_v5/_status/v5_completion_audit/reviews/aws-test-design-claude-review-2026-05-05.md` (prior review)
2. `compact_v5/_status/v5_completion_audit/PS_AWS_TEST_EXECUTION_LOOP.md`
3. `compact_v5/_status/v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md`
4. `compact_v5/_status/v5_completion_audit/TEST_CASE_PREP.md`
5. `compact_v5/_status/v5_completion_audit/PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md`
6. `compact_v5/_status/R_TIER_EVIDENCE_CONTRACT.md`
7. `compact_v5/_status/r_tier_test_matrix.json`
8. `compact_v5/_status/scripts/r_tier_gate.py`
9. `compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py`
10. `compact_v5/MAIN/agent/tests/r_tier/test_software_project_workflow_contracts.py`

# PRIOR BLOCKER RESOLUTION

| # | Prior Blocker | Status | Evidence |
|---|---|---|---|
| 1 | R16 sub-check enforcement is soft | **RESOLVED** | `R_TIER_EVIDENCE_CONTRACT.md:32,40-53` defines `software_builder_subchecks` keys; `r_tier_gate.py:321-345` enforces presence of dict + each required subcheck = `True`, with explicit failure message naming missing/false subchecks. Test `test_r_tier_evidence_contract_has_typed_software_builder_fields` locks the contract text. |
| 2 | R16/R19-U10 cost caps not justified | **RESOLVED** | `OPTIMIZED_AWS_VALIDATION_PLAN.md:74-82` adds explicit Phase A budget model table: R13 (5 tasks + verification), R16 ("max 8 primary model turns", "If Phase A estimates exceed cap, do not spend"), R19-U10 ("If true 150 Bedrock calls are required, this cap is not valid and Phase A must stop for user approval"). Stop-on-overrun is named, not aspirational. |
| 3 | `SOFTWARE-*` block closure precondition | **RESOLVED** | `OPTIMIZED_AWS_VALIDATION_PLAN.md:58-72` adds dedicated "Precondition Gate For Long-Run Tests" listing all seven `SOFTWARE-*` blocks (`-STATE`, `-CHECKPOINT`, `-SHELL`, `-RESULTS`, `-SUBAGENT`, `-COMPACT-TELEMETRY`, `-GATE`) as gating R16/R19-U10 spend. |
| 4 | R13 minimum pass threshold | **RESOLVED** | `R_TIER_EVIDENCE_CONTRACT.md:29` requires `score_total=5` and `score_passed>=4`; `r_tier_gate.py:283-293` enforces both at gate time with explicit error string. Matrix `ready_criteria` updated to "At least 4/5...target 5/5". |
| 5 | Bundle-vs-cap policy unresolved | **RESOLVED** | `OPTIMIZED_AWS_VALIDATION_PLAN.md:84-89` and `R_TIER_EVIDENCE_CONTRACT.md:146-156` define: U1+U2 bundle cap = $0.40 (sum), U3+U6+U7 bundle cap = $0.90 (sum); raw log may be shared but per-test telemetry, metrics, quality, review-log rows still mandatory. Bundle log-file naming (`r-tier-R19-U1+U2-aws-call1.log`) is shown. |
| 6 | Re-run/determinism/cost-cap-hit attempt policy | **RESOLVED** | `OPTIMIZED_AWS_VALIDATION_PLAN.md:91-97` and `R_TIER_EVIDENCE_CONTRACT.md:158-168` codify: one `GENUINE_PASS` is sufficient only if quality is clean; rerun once on flakiness/marginal pass; cost-cap-hit counts as one failed attempt unless preflight refused before any model call; 3-attempt cap then `ESCALATION-<TEST>.md`. |

All six prior blockers are resolved at the plan and contract layer, and four (R13 score, R13/R14/R15 changed-files, R16 subchecks, R19-U7 breaker_fired) are now enforced in code by `r_tier_gate.py`. Local zero-cost tests (`117 passed` per worker note; specs file confirms structure) lock the contract text against silent drift.

# PER-TEST READINESS

| Test | Status | Notes |
|---|---|---|
| R13 | **READY** | Cap $0.50; gate enforces `score_total=5`, `score_passed>=4`, `changed_files_within_fixture=true`; Phase A budget model documented; acceptance row in readiness specs aligned ("at least 4/5...target 5/5"). |
| R14 | **READY** | Cap $0.75; gate enforces `changed_files_within_fixture=true`; contract requires stale-symbol grep evidence and visible-call-site fixture note. Search-before-edit ordering is contract-required but verified by Phase C reviewer rather than gate code — acceptable since reviewer has raw `tool_call_summary` access. |
| R15 | **READY** | Cap $0.50; gate enforces `changed_files_within_fixture=true`; contract requires pre-fix failing run + post-fix passing run + `false_positive_area_unchanged=true` + diagnosis trace. Diagnosis-trace shape is reviewer-judged, which is appropriate for a free-form trace. |
| R16 | **READY** | Cap $1.00 with token-budget model; gate enforces full `software_builder_subchecks` dict; precondition gate on all seven `SOFTWARE-*` blocks; cache-limitation row template provided. Background-shell subcheck conditional on `SOFTWARE-SHELL` shipping is correctly conditional. |
| R19-U1 | **READY** | Cap $0.20; bundled with U2 at $0.40 sum; contract requires `clarification_request_count>=1` and `changed_files_count=0`. Typed fields documented in contract but not enforced at gate level — Phase C reviewer must verify, which is acceptable for a small UX gate. |
| R19-U2 | **READY** | Cap $0.20; bundled with U1; contract requires `conflict_detected=true`, `clarification_request_count>=1`, no speculative edit. Same gate-vs-reviewer split as U1; acceptable. |
| R19-U3 | **READY** | Cap $0.50; bundled with U6+U7 at $0.90 sum; contract requires "search-before-edit ordering and fixture orthogonality from R14." Fixture-orthogonality is described in evidence contract; reviewer must confirm at Phase A. |
| R19-U6 | **READY** | Cap $0.20; bundled; contract requires "fixture-controlled malformed-output injection and recovery path" be named in evidence. Determinism handled by fixture-injection requirement. |
| R19-U7 | **READY** | Cap $0.20; gate enforces `breaker_fired=true` (`r_tier_gate.py:346-350`); contract allows escalated "model recovered before breaker could be tested" alternative path. Strong typed enforcement. |
| R19-U10 | **READY** | Cap $0.50 with explicit Phase A stop-rule if 150 real Bedrock calls actually required; precondition gate on `SOFTWARE-COMPACT-TELEMETRY`; contract requires "deterministic final-task anchor that depends on information inserted before compaction/churn." Phase A reviewer must confirm anchor is locked into the fixture. |

# REMAINING BLOCKING FINDINGS

None. All six prior blockers are resolved at plan/contract/gate level and the changes are locked by zero-cost tests.

# REMAINING NON-BLOCKING FINDINGS

1. **Typed-field gate coverage asymmetry.** The gate enforces `score_passed`, `changed_files_within_fixture`, `software_builder_subchecks`, and `breaker_fired` in code, but R19-U1/U2 (`clarification_request_count`, `conflict_detected`), R19-U3 (search-before-edit ordering), R19-U6 (named injection mechanism), and R19-U10 (final-task anchor) are documented in `R_TIER_EVIDENCE_CONTRACT.md` and verified by Phase C reviewer rather than gate code. This is acceptable for a single-reviewer process but adding optional gate checks would harden them against reviewer drift in future re-runs.

2. **Fixture-orthogonality contract for R14 vs R19-U3** is described in prose in the evidence contract; consider adding a one-line zero-cost test asserting that R14 fixture has visible call sites and R19-U3 fixture requires inheritance walk, to prevent future fixture authors from collapsing them.

3. **Bundle log-file naming** is shown by example in the evidence contract but is not asserted by `r_tier_gate.py`; if a bundled run uses a non-standard log name the gate will still pass per-test if individual telemetry/metrics/quality files exist. Low risk because Phase A review will see the proposed log path.

4. **Cache-limitation row template** is provided in `R_TIER_EVIDENCE_CONTRACT.md:65-75` but the gate does not detect missing cache evidence vs. an explicit `cache_evidence_status: MODEL_LIMITATION` row. Phase C reviewer must distinguish "silently blank" from "explicitly limited." Acceptable.

5. **Reviewer/subagent attribution applicability per selected test** is required in the contract whenever the scenario uses `task` or reviewer-style subagents, but the plan does not enumerate per-test which of R13-R19 is expected to dispatch reviewers and which may legitimately have zero. Minor; Phase A review covers this implicitly.

# VERDICT: APPROVE_WITH_FIXES

The plan, evidence contract, and gate are now mutually consistent. All six prior blocking findings are addressed at the layer where they matter: cost-cap discipline and `SOFTWARE-*` precondition are in the plan; R13 threshold, R16 sub-checks, R19-U7 breaker, R13/R14/R15 changed-files, and bundle/determinism rules are in the contract; the gate enforces the most at-risk typed evidence in code; and zero-cost tests lock the contract strings so they cannot silently regress.

The remaining non-blocking findings are tightenings (more gate-side enforcement of typed evidence, a fixture-orthogonality test, log-naming assertions). They can be addressed during or after Phase A per-test review without holding up spend.

# TEST DESIGN DECISION: READY_FOR_PHASE_A_PER_TEST_REVIEW

The framework, optimization principle, evidence contract, gate enforcement, and execution loop are sufficient to begin per-test Phase A reviews for R13, R14, R15, R19-U1, R19-U2, R19-U3, R19-U6, R19-U7. R16 and R19-U10 may enter Phase A only after the seven `SOFTWARE-*` blocks are closed, pushed, locally tested, and Claude-reviewed per `OPTIMIZED_AWS_VALIDATION_PLAN.md:58-72`.

