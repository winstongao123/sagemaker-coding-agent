# REVIEWED FILES

Read from disk:

1. `compact_v5/_status/v5_completion_audit/PS_AWS_TEST_EXECUTION_LOOP.md`
2. `compact_v5/_status/v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md`
3. `compact_v5/_status/v5_completion_audit/TEST_CASE_PREP.md`
4. `compact_v5/_status/v5_completion_audit/PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md`
5. `compact_v5/_status/v5_completion_audit/THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`
6. `compact_v5/_status/R_TIER_EVIDENCE_CONTRACT.md`
7. `compact_v5/_status/r_tier_test_matrix.json`
8. `compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py`
9. `compact_v5/MAIN/agent/tests/r_tier/test_software_project_workflow_contracts.py`

# PER-TEST REVIEW

## R13 — HumanEval-mini coding accuracy ($0.50, Haiku 4.5 AU)

- **Purpose**: prove v5 generates correct code for bounded tasks (5 small Python functions with deterministic unit tests).
- **Non-overlap**: distinct from R14 (refactor) and R15 (debug). It is the cheapest correctness baseline; cannot be replaced by local mock.
- **Bundled capabilities**: code generation quality, tool sequencing, "no unrelated edits" discipline, score recording, basic tool_call_summary.
- **Required evidence**: full evidence contract + per-task pass/fail with score, changed-files set bounded to fixture.
- **Missing risks**:
  - acceptance allows "all five pass **or** scored failure logged" — there is no **minimum pass threshold**, so 0/5 + logged failure technically satisfies the acceptance text.
  - "no unrelated file edits" is asserted in prose but not tied to a typed telemetry field that `r_tier_gate.py` can verify.
  - no stop-rule entry for "score below threshold" or "false-positive edit detected".
- **Approval**: **CONDITIONAL** — set explicit pass threshold (e.g., ≥4/5) and a typed `changed_files_within_fixture` evidence row before Phase A.

## R14 — Multi-file refactor ($0.75, Haiku 4.5 AU)

- **Purpose**: prove cross-file navigation, symbol rename, import update, and post-edit verification.
- **Non-overlap**: distinct from R13 (single-file generation) and R19-U3 (hidden inheritance discovery). R14 is "given visible call sites, rename safely"; R19-U3 is "find non-obvious dependency before editing". Distinction holds if fixtures are intentionally orthogonal.
- **Bundled capabilities**: project search/grep, dependency walk, pytest run, repeated-call telemetry, `/checkpoint`/`/verify`/`/done` exercise.
- **Required evidence**: pytest pass, grep for stale symbol names, repeated-call counters, contract-required telemetry/metrics rows.
- **Missing risks**:
  - acceptance does not require **search-before-edit** to appear in `tool_call_summary` ordering (only the outcome is checked).
  - `/checkpoint` round-trip is listed in the workflow contract but not asserted as a separable sub-check (no checkpoint preview/restore evidence row).
  - no explicit cap on number of edited files vs fixture size; a noisy refactor that touches more files than necessary could still pass.
- **Approval**: **CONDITIONAL** — require search-before-edit ordering evidence and a checkpoint round-trip sub-check before Phase A.

## R15 — Find and fix planted bugs ($0.50, Haiku 4.5 AU)

- **Purpose**: prove debug quality with explicit false-positive trap.
- **Non-overlap**: distinct from R13 (generation) and R14 (refactor); the false-positive trap is unique to R15.
- **Bundled capabilities**: failing-to-passing tests, diagnosis ordering, no unrelated edits, `/checkpoint`/`/verify`/`/done`.
- **Required evidence**: both planted bugs fixed, both originally failing tests pass, false-positive area byte-identical, "test-driven diagnosis" in trace.
- **Missing risks**:
  - "debug evidence shows test-driven diagnosis" is loose — no schema for what "diagnosis trace" must contain.
  - no requirement that the failing tests are run **before** the fix (i.e., reproduce-the-bug-first discipline).
  - no telemetry assertion that `/verify` was actually invoked, only that `/done` was reachable.
- **Approval**: **CONDITIONAL** — define diagnosis-trace schema (must include a pre-fix failing run + post-fix passing run) before Phase A.

## R16 — Long-session Flask CRUD build ($1.00, Haiku 4.5 AU)

- **Purpose**: broadest end-to-end software-builder proof.
- **Non-overlap**: this is the only test exercising `/status`, `/phase`, `/save`, `/resume`, `/checkpoint`, `/verify`, `/done`, `/cost`, `/context` together with compaction and cache evidence.
- **Bundled capabilities**: app tests, command surface, compaction event emission, cache trend, status/todo/checkpoint round-trip, optional shell background lifecycle, final artifact quality.
- **Required evidence (per plan)**: separable sub-checks for status round-trip, todo round-trip, named-checkpoint round-trip, verify/done stale-evidence block, compaction event emitted, shell background start/poll/kill if shipped, final artifact quality.
- **Missing risks** (BLOCKING):
  - the plan describes separable sub-checks but `test_software_project_workflow_contracts.py` only enforces presence of the words "compaction", "cache", "app tests" in acceptance — there is no enforced contract that the run produces N typed sub-check evidence rows. At AWS time this can degrade to "app tests pass = R16 done".
  - $1.00 cap is plausibly tight if the fixture must deliberately trigger auto-compact; no model of expected token/turn budget is shown.
  - the plan depends on `SOFTWARE-STATE`, `SOFTWARE-CHECKPOINT`, `SOFTWARE-SHELL`, `SOFTWARE-COMPACT-TELEMETRY`, `SOFTWARE-GATE` being implemented locally first (per PS3 requirements). Optimized plan does **not** state R16 spend is blocked until those blocks close.
  - cache-hit evidence is contingent on Bedrock exposing the field; the explicit "limitation row" template is referenced but not provided.
- **Approval**: **NOT YET** — fix sub-check contract enforcement, validate cost cap with a token budget model, and gate R16 spend on `SOFTWARE-*` block closure.

## R19-U1 — Ambiguous request asks clarification ($0.20)

- **Purpose**: prove the agent does not blindly edit when intent is vague.
- **Non-overlap**: bundled with R19-U2 in Stage 4 ambiguity gate; distinct because the trap is *ambiguity* (multiple plausible targets), not *contradiction*.
- **Bundled capabilities**: ask-user/clarification path, no speculative edit, status note.
- **Required evidence**: clarification call observed, zero edits in fixture.
- **Missing risks**: no telemetry field requiring `clarification_request_count > 0`; relies on prose acceptance.
- **Approval**: **APPROVED** — minor: add a typed clarification-event telemetry field.

## R19-U2 — Contradictory specs flagged ($0.20)

- **Purpose**: prove conflicting requirements are explicitly reported.
- **Non-overlap**: paired with R19-U1 but trap differs (contradiction, not ambiguity); both must remain because each maps to a distinct prompt-time failure mode.
- **Bundled capabilities**: conflict reporting, clarification request, no paper-over edit.
- **Required evidence**: conflict statement in output, clarification request, zero edits.
- **Missing risks**: same as U1 — no typed conflict-detection telemetry; assertion is on free-text only.
- **Approval**: **APPROVED** — minor: typed conflict-event field.

## R19-U3 — Hidden cross-file dependency ($0.50)

- **Purpose**: prove grep/explore-before-edit when dependency is non-obvious (e.g., inheritance).
- **Non-overlap**: distinct from R14 if and only if the R19-U3 fixture has no surface-level call site discoverable by grep on the symbol name. The plan asserts this but the readiness spec does not lock it.
- **Bundled capabilities**: search ordering, repeated-call counters, edit-after-search behavior.
- **Required evidence**: tool_call_summary shows search before edit, final tests pass.
- **Missing risks**: overlap with R14 if R14 fixture also requires inheritance walk; needs explicit fixture-orthogonality contract.
- **Approval**: **CONDITIONAL** — fixture must be orthogonal to R14 (no shared dependency-discovery mechanism), and search-before-edit ordering must be a typed assertion.

## R19-U6 — Malformed tool output recovery ($0.20)

- **Purpose**: prove the model can detect and recover from garbage tool output.
- **Non-overlap**: bundled in Stage 5 recovery gate with U7. Distinct from U7 because the trap is *bad output*, not *repeated identical call*.
- **Bundled capabilities**: bad-output detection, retry or alternative-tool path.
- **Required evidence**: tool_call_summary shows retry/alternative; outcome is correct or escalates.
- **Missing risks**: no requirement that the malformed output is **delivered** (rather than naturally absent) — needs a deterministic injection or fixture-controlled tool that returns garbage.
- **Approval**: **CONDITIONAL** — confirm the malformed-output injection mechanism is deterministic.

## R19-U7 — Repeated-call circuit breaker ($0.20)

- **Purpose**: prove the stuck-loop detector fires and the model changes approach.
- **Non-overlap**: bundled in Stage 5; distinct from U6 because the trap is *the agent's own repetition*, not external garbage.
- **Bundled capabilities**: repeated-call counter, circuit-breaker fire, alternative-path success.
- **Required evidence**: third repeated call blocked or redirected; alternative path succeeds or asks user.
- **Missing risks**:
  - real-model behavior may avoid the third repeat on its own, masking whether the breaker fires; the test must assert the breaker actually triggered, not just that the outcome is correct.
  - no stop-rule for "breaker did not fire because model recovered first" (which is technically a pass for outcome but does not validate the breaker).
- **Approval**: **CONDITIONAL** — require explicit "breaker_fired = true" telemetry and a fixture engineered to force the third call.

## R19-U10 — 150-turn session with switches/compactions ($0.50, Haiku 4.5 AU + Sonnet 4.5 AU)

- **Purpose**: long-coherence proof under model switches and multiple compactions.
- **Non-overlap**: distinct from R16 — R16 proves app build, R19-U10 isolates *coherence after churn*. Final-task fixture must be answerable only with information injected pre-compaction to be meaningful.
- **Bundled capabilities**: model-switch behavior, multi-compaction survival, file-backed status/memory continuity, cache trend, final-task coherence.
- **Required evidence**: final task succeeds, compactions/switches logged, no coherence loss in quality review.
- **Missing risks** (BLOCKING):
  - $0.50 cap for 150 turns mixing Haiku and Sonnet is implausibly tight given expected compaction overhead; cost-cap-hit will likely show up as outcome failure rather than coherence signal. No token-budget model is shown.
  - "no coherence loss" is judged by quality review — needs a deterministic anchor (e.g., a final task whose answer requires recalling a fact placed at turn 5).
  - depends on `SOFTWARE-COMPACT-TELEMETRY` typed audit events; if substring-based detection is still in place, compactions may be invisible to evidence.
- **Approval**: **NOT YET** — re-validate cost cap with a token budget, lock the final-task anchor, and gate spend on `SOFTWARE-COMPACT-TELEMETRY` closure.

# OVERLAP / OPTIMIZATION ASSESSMENT

- **Stage bundling is correct in principle**: R19-U1+U2 (ambiguity gate), R19-U3+U6+U7 (recovery gate), R16+R19-U10 split (app-build vs coherence) are sensible groupings. The matrix and contracts list them as separate IDs, but the plan groups them — this is acceptable as long as a single AWS call exercises each bundle.
- **Genuine overlap risks**:
  - R14 vs R19-U3: both involve cross-file work and grep. Distinct only if R14 fixture has visible call sites and R19-U3 fixture has hidden inheritance. **The fixture orthogonality is described in prose but not locked in code.**
  - R13 vs R15 vs R14: all assert "no unrelated edits". This is fine per-test but should be a shared typed evidence field, not three independent prose checks.
- **Local-coverage check**: R8, R18-E2, R18-E5, R18-E9, R18-E12 are correctly mock_local with `cost_cap_usd == 0`. The selected AWS subset (R13-R16, R19-U1/U2/U3/U6/U7/U10) does not duplicate any cheap mock case. Optimization principle is honored.
- **Bundle vs cap mismatch**: stages 4 and 5 in the plan describe bundled execution (one AWS run covering U1+U2 or U3+U6+U7), but the matrix preserves separate cost caps per ID. The execution loop does not reconcile this — is one bundled run charged against the lowest cap, the sum, or run separately? **Unresolved.**

# EVIDENCE AND TRACEABILITY ASSESSMENT

- **Evidence contract**: `R_TIER_EVIDENCE_CONTRACT.md` is well-defined — required metrics keys, telemetry keys, quality-review axes, file paths per call. This is strong.
- **Phase A / Phase C loop**: `PS_AWS_TEST_EXECUTION_LOOP.md` mandates worker preflight → Claude Phase A → user spend approval → AWS exec → metadata capture → worker post-run → Claude Phase C → fix/retry → escalation after 3 attempts. Loop is correct and sufficient for traceability.
- **Per-test traceability**: every test has Phase A prompt, Phase A review, raw call log, telemetry JSON, quality MD, metrics JSONL row, review-log row, Phase C review. This is reproducible.
- **Gaps**:
  - R16 separable sub-check evidence is described in plan text but not pinned to a JSON schema or `r_tier_gate.py --test R16` checklist; risk of being "soft" at AWS time.
  - Reviewer/subagent attribution is required by contract but not all selected tests exercise reviewer/subagent — the plan should state which of R13-R19 must include subagent dispatches and which may legitimately have zero.
  - No re-run / determinism policy: real Bedrock is non-deterministic. Is one Phase C `GENUINE_PASS` enough, or do flaky behaviors need a second run? Currently silent.
  - Cache-evidence "model-side limitation row" template is referenced but not provided in the contract.
  - Cost-cap-hit is a stop trigger, but no rule states whether a cost-cap-hit run counts as one of the 3 fix/retry attempts.

# BLOCKING FINDINGS

1. **R16 sub-check enforcement is soft.** Plan text lists separable sub-checks; readiness/contract code does not enforce them as typed evidence rows. Without enforcement, R16 will degrade to "app tests pass" at AWS time and bypass the broader proof.
2. **R16 and R19-U10 cost caps are not justified by a token budget model.** $1.00 for a long-session app build that must trigger compaction, and $0.50 for a 150-turn dual-model session, may force cost-cap-hit before the coherence signal is observable. A documented turn/token estimate must back each cap.
3. **`SOFTWARE-*` block closure is a precondition not surfaced in the plan.** PS3 requirements state `SOFTWARE-STATE`, `-CHECKPOINT`, `-SHELL`, `-RESULTS`, `-SUBAGENT`, `-COMPACT-TELEMETRY`, `-GATE` must be implemented before AWS spend. The optimized plan does not gate R16/R19-U10 spend on those blocks, so a Phase A approval could be granted while compaction telemetry is still substring-based.
4. **R13 has no minimum pass threshold.** "All five pass **or** scored failure logged" admits a 0/5 result with logged failure as acceptance-passing. Set an explicit threshold.
5. **Bundle-vs-cap policy unresolved.** Plan bundles R19-U1+U2 and R19-U3+U6+U7 into single runs, but the matrix carries per-ID caps. The loop must specify whether bundled runs charge against summed caps and how per-ID evidence files are written.
6. **Re-run / determinism policy is silent.** Real-model flakiness is not addressed. Define whether one Phase C `GENUINE_PASS` is sufficient, and whether a cost-cap-hit run counts as a fix/retry attempt.

# NON-BLOCKING FINDINGS

1. **"No unrelated edits" should be a shared typed evidence field** (`changed_files_within_fixture`) instead of three independent prose checks across R13/R14/R15.
2. **R14 vs R19-U3 fixture orthogonality** is described in prose; lock it as a fixture invariant test (R14 fixture has visible call sites; R19-U3 fixture requires inheritance walk).
3. **R15 diagnosis-trace schema** is unspecified. Require pre-fix failing-test run + post-fix passing-test run as the minimum evidence shape.
4. **R19-U6 malformed-output injection** mechanism is not documented; ensure the garbage output is fixture-controlled, not opportunistic.
5. **R19-U7 must assert breaker fired**, not only that the alternative path succeeded; otherwise a self-correcting model masks the breaker behavior.
6. **Reviewer/subagent attribution applicability** should be enumerated per selected test (R13-R19) — which runs are expected to dispatch subagents/reviewers, and which may legitimately have zero — to avoid blanket "zero is fine" interpretations.
7. **Cache-limitation row template** referenced in the plan should be added to `R_TIER_EVIDENCE_CONTRACT.md`.
8. **Stage 4/5 bundle naming**: when bundled runs occur, name the call file (e.g., `r-tier-R19-U1+U2-aws-call1.log`) explicitly so per-ID evidence files are predictable.

# VERDICT: APPROVE_WITH_FIXES

The framework — execution loop, evidence contract, optimization principle, bundle structure — is sound. Each selected scenario has a defensible non-overlap story and a plausible bundled-evidence story. The blocking findings are plan/contract tightenings, not redundant scenarios or missing infrastructure. None of R13/R14/R15/R16/R19-U1/U2/U3/U6/U7/U10 should be removed; each maps to a distinct production behavior the project goal requires.

Required fixes before per-test Phase A spend:

- enforce R16 separable sub-checks as typed evidence rows (not prose);
- back R16 and R19-U10 cost caps with a token-budget estimate;
- gate R16 and R19-U10 spend on `SOFTWARE-*` block closure;
- set R13 minimum pass threshold;
- resolve bundle-vs-cap charging policy;
- add re-run / determinism / cost-cap-hit-counts-as-attempt rules.

# TEST DESIGN DECISION: NOT_READY

Six blocking items (R16 sub-check enforcement, R16/R19-U10 cost-cap justification, `SOFTWARE-*` precondition gating, R13 threshold, bundle-vs-cap policy, determinism policy) must be resolved at the plan/contract layer before per-test Phase A reviews can usefully run. Once those land, this design moves to `READY_FOR_PHASE_A_PER_TEST_REVIEW`.

