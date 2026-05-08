# APPROVE_FOR_AWS_CALL

## Stage 6 R3-rerun question

**Existing R3 READY evidence is sufficient for Stage 6. R3 must NOT be rerun in this AWS invocation.**

R3 is already fully tagged READY in the ledger:

- `r_tier_review_log.md` row 5: `GENUINE_PASS / READY (NEAR_IDEAL 5.00/5 worker; 4.83/5 Codex)`, $0.0810 cumulative ($0.0406 call1 diagnostic + $0.0404 call2 PASS), $0.50 cap, gate-passable.
- `r_tier_metrics.jsonl` row 3: `R3 call=2, completed=true, cost_usd=0.0404, verdict=GENUINE_PASS`.
- Phase A approve + Phase C `GENUINE_PASS` (`r-tier-R3-phaseC-iter1.md`).
- Telemetry (`r-tier-R3-aws-call2-telemetry.json`) shows 3 `task` dispatches all `subagent_type=explore`, parent_session/child_session split confirmed, one-to-one task→file mapping, `findings.md` synthesis with all function names + TODO bodies, REPEATED_calls=0.
- Quality review (`r-tier-R3-aws-call2-quality.md`) NEAR_IDEAL.

The OPTIMIZED_AWS_VALIDATION_PLAN.md "Optimization Principle" explicitly warns against re-running an AWS test that already proved the targeted production quality. Stage 6's "R3+R19-U4+R19-U5" naming describes the orchestration risk surface, not a mandate to re-burn each member every time the bundle gains a new pending row. R3 already proved basic three-subagent dispatch + parent synthesis on real Bedrock; R19-U4 adds conflict reconciliation; R19-U5 adds failed-child recovery. These are non-overlapping capabilities, satisfying the bundle/non-overlap rule in `R_TIER_EVIDENCE_CONTRACT.md` §Bundle And Retry Policy.

Therefore the proposed single-AWS-call Phase A targeting only R19-U4 + R19-U5 is consistent with the optimized plan.

## Findings

### HIGH
- None.

### MEDIUM
1. **Bundle telemetry build step is implicit, not in-test.** `test_r19_u4_u5_subagent_recovery_bundle.py` writes only `r-tier-<TEST>-aws-call<N>-side-metrics.json`. Per `R_TIER_EVIDENCE_CONTRACT.md` and `r_tier_gate.py:check_test_evidence`, each member needs `r-tier-<TEST>-aws-call<N>-telemetry.json` (with non-empty `per_turn`, `tool_call_summary`, `compaction_events`, `subagent_dispatches`, `cache_efficiency_trend`, `outcome`) and `r-tier-<TEST>-aws-call<N>-quality.md`. After the AWS call the worker MUST run `compact_v5/_status/scripts/build_telemetry.py` twice (one per member id) pointing `--audit-log` at `compact_v5/_status/r_tier_runtime/R19-U{4,5}-call1-audit/`, `--raw-log` at the bundled log, `--metrics-side-channel` at the per-member side metrics, and `--output` at the canonical `r-tier-<TEST>-aws-call1-telemetry.json`. Phase A summary should call this out so the gate doesn't fail on missing canonical telemetry.

2. **Bundle pytest assertion uses `>=` instead of "exactly".** Line 244 enforces `task_dispatches >= 2` for R19-U4 and `>= 3` for R19-U5. Phase A spec says "exactly two" / "exactly three". A model that dispatches 4 explore subagents would still pass, weakening prompt-fidelity falsifiability vs. R3's `==3` rule. Acceptable on first call (Stage 5 R19-U7 used the same `>=` pattern with breaker_fired evidence as the falsifier), but quality review must flag if dispatch count materially exceeds the prompt.

3. **R19-U5 ready-check substring is narrow.** `_u5_ready` requires literal `"failure"` (lowercased). A model that writes "missing probe could not be read" or "child errored" without the word "failure" would fail-ready even if the artifact is functionally correct. Prompt explicitly says "record that child failure", so this should usually appear, but the quality reviewer should sanity-check the recovery_summary content even if the assertion fires.

### LOW
1. Bundle `session_cost_limit` is `sum(_hard_ceiling)` = $0.48 + $0.36 = $0.84. Plan-level Stage 6 sum is $1.20 (including R3 share). State explicitly in the user-approval message that the $0.84 ceiling excludes R3 because R3 evidence is reused. The cumulative R-tier ledger remains preserved.
2. `cache_hit_pct=0.0` is hardcoded in side metrics (line 254). After `build_telemetry.py` runs, telemetry will populate cache_hit_pct from `chat_response.usage` if present (R3 call2 captured 0.4943 fine). If Bedrock for this run doesn't expose cache fields, write the explicit `MODEL_LIMITATION` row per the evidence contract — do not silently leave 0.0.
3. Default `AWS_REGION=ap-southeast-2` matches Haiku 4.5 AU geo profile and prior R3 call2.
4. Per-member workspaces use `tmp_path / "r19_u4"` and `tmp_path / "r19_u5"`, but `audit_dir` lives under `compact_v5/_status/r_tier_runtime/<TEST>-call<N>-audit/` so audit JSONLs survive pytest teardown. Good.
5. Local preflight `py -3.11 -m pytest ... -q` correctly skips without `RUN_REAL_BEDROCK`. Verified by user. Phase A budget headroom and explicit user approval still required before spend.

## Approval scope

Approved: ONE real Bedrock pytest invocation of `test_r19_u4_u5_subagent_recovery_bundle.py` on Haiku 4.5 AU, planned cap $0.40 (R19-U4) + $0.30 (R19-U5) = $0.70 planned / $0.84 hard ceiling, R3 evidence reused.

Required after the AWS call: bundled raw log, per-member side metrics (already produced by the test), per-member canonical telemetry via `build_telemetry.py`, per-member quality.md, per-member metrics JSONL row, per-member review-log row, Phase C `GENUINE_PASS` review, and `r_tier_gate.py --test R19-U4` and `--test R19-U5` both passing. Stop conditions in the prompt apply.
