I've read all required files. Now drafting the Phase A review.

## What I read

- `compact_v5/_status/v5_completion_audit/PS_AWS_TEST_EXECUTION_LOOP.md` — execution loop and per-test gating contract
- `compact_v5/_status/v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md` — Stage 2 R15 placement, cap policy, evidence requirements
- `compact_v5/_status/R_TIER_EVIDENCE_CONTRACT.md` — R15 specifically requires pre-fix failing output, post-fix passing output, `false_positive_area_unchanged=true`, diagnosis trace; metrics/telemetry/quality keys
- `compact_v5/_status/r_tier_test_matrix.json` — R15 cap $0.50, kind=real, model=Haiku 4.5 AU, ready criteria match
- `compact_v5/MAIN/agent/tests/r_tier/test_r15_debugging.py` — runner under review
- `compact_v5/MAIN/agent/tests/r_tier/test_software_project_workflow_contracts.py` — R15 contract row (debugging, must include `bugs`, `false-positive`, `diagnosis`)
- `compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py` — R15 spec row matches matrix
- `compact_v5/MAIN/agent/runtime/bedrock_client.py` — confirmed `mock_mode=False` routes through real Bedrock; mock branch only fires when `mock_mode=True`
- `compact_v5/MAIN/agent/core/query_engine.py` — confirmed `QueryResult.stop_reason` values are `end_turn`/`max_turns`/`budget_exhausted`/`context_overflow`/`fatal_error`; `user_stop` is added by Agent wrapper for `on_stop_check`

## Trap-door verification (per stop conditions)

| Stop condition | Verified? | Evidence |
|---|---|---|
| Cannot pass without real Bedrock when `RUN_REAL_BEDROCK=1` absent | YES | `pytest.mark.skipif` at line 141; `BedrockClient(... mock_mode=False)` at line 193; bedrock_client.py:313 only short-circuits when `mock_mode=True` |
| Fixture starts red | YES | `_BUGGY_MODULE`: `summarize_invoice` uses `qty + unit_price` (gives 10.5/11.34, not 11.0/11.88); `parse_due_date` uses `%m-%d-%Y` against `2026-05-06` → ValueError. Pre-run asserts `pre_code != 0` and `"2 failed, 1 passed"` substring |
| False-positive helper cannot change | YES | `_false_positive_area_unchanged` does exact-substring match of full block including docstring; even reformatting fails it |
| Diagnosis trace required | YES | `_diagnosis_trace_valid` requires `diagnosis.md` plus all of: both test names, `qty`, `unit_price`, `yyyy-mm-dd` (lowercased) |
| Test file cannot be edited | YES | `_sha256(tests) == initial_test_hash` |
| No unrelated files | YES | `unexpected_files = workspace_files − {order_utils.py, diagnosis.md, runner_files}` and asserted empty |
| Over-cap, fatal_error, max_turns not READY | YES | `stop_reason in {end_turn, user_stop}` asserted; `cost_used <= 0.50` asserted; verdict only `GENUINE_PASS` when all checks pass |
| Telemetry missing not READY | PARTIAL | runner writes `side-metrics.json` + audit JSONL dir, but does NOT itself write the contract-shaped `r-tier-R15-aws-call1-telemetry.json` (`per_turn`, `tool_call_summary`, `compaction_events`, `cache_efficiency_trend`, `outcome`), append `r_tier_metrics.jsonl`, or `r_tier_review_log.md` row. Wrapper/driver must do this — flagged below |

## Redundancy analysis vs R13/R14/R16

- **R13 (greenfield from spec)**: writes new functions to satisfy unit tests. R15 cannot be satisfied by R13 because R15 forbids editing tests, requires running tests *before* editing, requires diagnosis prose, and traps false-positive rewrites. Distinct capability: diagnostic repair vs. specification implementation.
- **R14 (multi-file refactor)**: cross-file rename + stale-symbol grep. R15 is single-file two-bug diagnosis with a third tempting helper. Distinct.
- **R16 (long Flask CRUD)**: long-session app build with status/checkpoint/compaction sub-checks. R15 has no software-builder long-session surface. Distinct.

R15 is **optimized**, not redundant.

## Findings

**HIGH — none ship-blocking**

**MEDIUM**
1. **Telemetry contract gap (wrapper precondition).** The runner alone does not emit `r-tier-R15-aws-call1-telemetry.json` with the contract's required keys (`per_turn`, `tool_call_summary`, `compaction_events`, `subagent_dispatches`, `cache_efficiency_trend`, `outcome`), nor append `r_tier_metrics.jsonl` / `r_tier_review_log.md`. These must be produced by an external driver/wrapper using `audit_dir/*.jsonl` and `side-metrics.json`. Before Phase A spend approval, the worker must show that wrapper exists or that side-metrics + audit JSONL will be promoted to the contract telemetry shape. Otherwise `r_tier_gate.py --test R15` will reject the run regardless of model behavior.
2. **`cache_hit_pct: 0.0` is hardcoded** in side-metrics (line 239). The evidence contract forbids silently-blank cache fields; either compute from `TOKENS.session_cache_read`/total input or emit a `MODEL_LIMITATION` row with cited missing-field evidence. The wrapper or runner must close this before the Phase C gate accepts the run.

**LOW**
3. **`tool_calls = result.turns_used`** (line 241) mislabels turns as tool calls. `api_calls` correctly uses `TOKENS.api_calls`; the `tool_calls` row should come from a real tool-call counter (e.g., audit JSONL grep) or be renamed `turns_used` in side-metrics to avoid corrupting the metrics ledger.
4. **`changed_files_within_fixture: True` is hardcoded** (line 251). It is true by construction (workspace = `tmp_path`), but the contract prefers evidence-derived values; consider asserting from `unexpected_files == []` plus the file allowlist used elsewhere in the runner.
5. **`_hard_cost_halt` runs pytest every check.** It calls `_r15_ready` which subprocesses pytest after every turn. Functionally fine, slightly noisy in the audit log; not blocking.

## Section recap

EXPECTED ROW COUNT: N/A (Phase A preflight, not block ledger)
LEDGER ROW COUNT: N/A
DISPOSITION COUNTS: N/A

REMAINING SHIP-BLOCKING ROWS: 0 for the runner itself; 1 wrapper-precondition (telemetry/metrics/review-log emission) must be confirmed in worker preflight before spend.

Test optimization status: **non-redundant with R13/R14/R16**; isolates diagnostic-repair behavior with hard trap-doors against false-positive rewrites and test-file tampering.

PHASE A VERDICT: APPROVE_FOR_AWS_CALL
