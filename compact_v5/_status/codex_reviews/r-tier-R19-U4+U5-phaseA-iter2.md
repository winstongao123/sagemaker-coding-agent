`APPROVE_FOR_AWS_CALL`

## Stage 6 R3-rerun question

Existing R3 READY evidence remains sufficient. R3 must NOT be rerun in this AWS invocation. The iter1 rationale (ledger row 5 GENUINE_PASS, $0.0810 cumulative, telemetry confirms 3 explore dispatches with parent/child split, NEAR_IDEAL quality) is unchanged by this runner edit, and the optimized plan's non-overlap rule still applies — R19-U4 adds conflict reconciliation, R19-U5 adds failed-child recovery, neither overlaps R3.

## Effect of the iter1→iter2 change

Verified at `compact_v5/MAIN/agent/tests/r_tier/test_r19_u4_u5_subagent_recovery_bundle.py:244`:

```python
and task_dispatches == (2 if test_id == "R19-U4" else 3)
```

This resolves iter1 MEDIUM #2 directly. The runner now matches the Phase A spec ("exactly two" / "exactly three") and aligns with R3's `==3` falsifier pattern. A model that over-dispatches (e.g., 4 explore subagents) now fails-ready — that is the intended tightening, not a blocker. Prompt fidelity is strengthened, not weakened.

## Findings

### HIGH
- None.

### MEDIUM
1. **Carried from iter1 — canonical telemetry build is still implicit.** The runner only writes `r-tier-<TEST>-aws-call<N>-side-metrics.json`. After the AWS call the worker must run `compact_v5/_status/scripts/build_telemetry.py` twice (once per member) to produce `r-tier-R19-U{4,5}-aws-call1-telemetry.json` from the per-member audit dirs. `r_tier_gate.py:check_test_evidence` will fail without canonical telemetry. Unchanged by iter2.
2. **Carried from iter1 — `_u5_ready` substring "failure" is narrow** (line 168). Prompt explicitly says "record that child failure", so this should fire, but Phase C quality review should sanity-check `recovery_summary.md` content even if the assertion passes.

### LOW
1. Bundle `session_cost_limit = $0.48 + $0.36 = $0.84` (line 304). Plan-level Stage 6 is $1.20 (including R3 share). User-approval message must state $0.84 ceiling excludes R3 because R3 evidence is reused.
2. `cache_hit_pct = 0.0` is hardcoded in side metrics (line 254). `build_telemetry.py` will repopulate from `chat_response.usage` if Bedrock exposes cache fields; otherwise log `MODEL_LIMITATION` per evidence contract — do not silently leave 0.0.
3. Default `AWS_REGION = ap-southeast-2` (line 312) matches Haiku 4.5 AU geo and prior R3 call2.
4. `task_dispatches` falsifier is now exact (`==`), satisfying the iter1 ask. No new failure modes introduced; the only path that newly fails is over-dispatch, which violates the prompt anyway.

## Approval scope

Approved: ONE real Bedrock pytest invocation of `test_r19_u4_u5_subagent_recovery_bundle.py` on Haiku 4.5 AU (`au.anthropic.claude-haiku-4-5-20251001-v1:0`), planned cap $0.40 (R19-U4) + $0.30 (R19-U5) = $0.70 planned / $0.84 hard ceiling, R3 evidence reused. Required after the AWS call: bundled raw log, per-member side metrics (auto-produced), per-member canonical telemetry via `build_telemetry.py`, per-member `quality.md`, per-member metrics JSONL row, per-member review-log row, Phase C `GENUINE_PASS`, and `r_tier_gate.py --test R19-U4` and `--test R19-U5` both passing. Stop conditions from the iter1 prompt apply.
