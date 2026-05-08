# R15 Phase A Iteration 2 Retry Review

## What I read (from disk, not worker summary)

- `compact_v5/_status/v5_completion_audit/PS_AWS_TEST_EXECUTION_LOOP.md` — per-test loop, fix/retry rules, evidence files
- `compact_v5/_status/v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md` — Stage 2 R15 placement, determinism policy ("cost-cap-hit counts as one failed attempt unless no model call occurred"), 3-attempt escalation
- `compact_v5/_status/R_TIER_EVIDENCE_CONTRACT.md` — R15-specific evidence: pre-fix failing output, post-fix passing output, `false_positive_area_unchanged`, diagnosis trace, plus telemetry/metrics/quality keys; cache-evidence policy
- `compact_v5/_status/r_tier_test_matrix.json` — R15 cap $0.50, kind=real, Haiku 4.5 AU
- `compact_v5/MAIN/agent/tests/r_tier/test_r15_debugging.py` — runner under retry (lines 218–232 show the new dir filter)
- `compact_v5/_status/codex_reviews/r-tier-R15-phaseA-iter1.md` — prior approval; flagged cache_hit_pct hardcode and tool_calls mislabel as MEDIUM/LOW
- `compact_v5/_status/codex_reviews/r-tier-R15-phaseB-iter1.md` — Phase B classification of call1 as harness false positive
- `compact_v5/_status/codex_reviews/r-tier-R15-aws-call1.log` — raw run; pre 2 failed/1 passed → post 3 passed; 28 API calls; cost $0.1668; failure was the assertion at line 296 against `unexpected_files`
- `compact_v5/_status/r-tier-R15-aws-call1-side-metrics.json` — confirms `post_fix_passed=true`, `false_positive_area_unchanged=true`, `test_file_unchanged=true`, `diagnosis_trace=true`, `stop_reason="user_stop"`
- `compact_v5/MAIN/agent/core/query_engine.py:602–619` — confirmed `user_stop` is the legitimate stop value when `on_stop_check` returns true (the runner uses `_hard_cost_halt` which returns true once the fixture is green)
- Cross-check: `compact_v5/MAIN/agent/runtime/state.py:75` — `.sageagent_state/` is the StateRecorder directory (`turn_journal.jsonl`, `last_turn.json`), written by the agent runtime when `disable_local_traces=False`. It is infrastructure, not a model file edit.

## Stop-condition verification

| Stop condition | Verified? | Evidence |
|---|---|---|
| Call1 was harness false positive, not model failure | YES | All model-controlled assertions in side-metrics passed (post_fix, false_positive intact, test_file SHA unchanged, diagnosis trace valid, stop_reason in allowed set). The only failure was `unexpected_files` containing `.pytest_cache/*` (created by pytest subprocess inside pre/post-fix runs, not by the model) and `.sageagent_state/last_turn.json` + `turn_journal.jsonl` (created by `runtime/state.py` recorder for any agent turn). Neither set is reachable by a model `write_file`-style action against project source. |
| Filter does not weaken code-preservation assertions | YES | `_false_positive_area_unchanged` (line 113) still does an exact-substring match of the full `_FALSE_POSITIVE_BLOCK` including docstring. `test_file_unchanged` (line 216) still SHA-256 compares to initial hash. `expected_agent_files` allowlist (line 218) still permits only `order_utils.py` and `diagnosis.md` as project files; any other model-created `.py` or non-runtime file still falls into `unexpected_files`. The new filter is dir-name-based on three known infrastructure dirs only. |
| Retry cannot pass without required model evidence | YES | Lines 289–299 still assert: `stop_reason ∈ {end_turn, user_stop}`, `post_code==0`, `false_positive_area_unchanged`, `test_file_unchanged`, `diagnosis_trace`, `not unexpected_files`, `cost_used <= cap`. Verdict is `GENUINE_PASS` only when all conditions hold (lines 273–280). |
| Remaining cap sufficient | YES | Call1 cost $0.1668 against $0.50 cap. Remaining $0.3332. Same prompt, same fixture, same model, same `max_turns=18`, same `max_tokens=2048`. ~2x headroom over expected call cost. |
| 3-attempt rule | OK | Per OPTIMIZED plan determinism policy, call1 counts as 1 meaningful attempt because a real model call occurred. Call2 will be attempt 2 of 3. Phase B retry rationale is recorded. |

## Local checks I re-ran

| Command | Expected | Observed |
|---|---|---|
| `py -3.11 -m py_compile compact_v5/MAIN/agent/tests/r_tier/test_r15_debugging.py` | exit 0 | exit 0 |
| `PYTHONPATH=compact_v5/MAIN/agent pytest compact_v5/MAIN/agent/tests/r_tier/test_r15_debugging.py -q` | 1 skipped | `1 skipped in 0.04s` |
| `PYTHONPATH=compact_v5/MAIN/agent pytest compact_v5/MAIN/agent/tests/r_tier/test_software_project_workflow_contracts.py -q` | 9 passed | `9 passed in 0.13s` |

## Findings

**HIGH** — none ship-blocking for AWS spend approval.

**MEDIUM (carryover from iter1, not closed in this retry; not blocking AWS spend, blocking Phase C close)**
1. `cache_hit_pct: 0.0` is still hardcoded in side-metrics (test file line ~242). The call1 raw log emitted `cache 100% | saved ~$0.2267`, so cache evidence exists but is not captured. Per `R_TIER_EVIDENCE_CONTRACT.md` the wrapper or runner must emit a numeric value or a `MODEL_LIMITATION` row before Phase C can accept the run. Worker should resolve this in the wrapper layer that promotes `side-metrics.json + audit JSONL` to contract-shaped telemetry; not a precondition for AWS call2.
2. Wrapper still must produce contract-shaped `r-tier-R15-aws-call2-telemetry.json` (with `per_turn`, `tool_call_summary`, `compaction_events`, `subagent_dispatches`, `cache_efficiency_trend`, `outcome`), `r_tier_metrics.jsonl` row, and `r_tier_review_log.md` row. The runner alone does not emit these. Carryover from iter1 M1; gate-blocking at Phase C.

**LOW**
3. `tool_calls` (line 244) still set from `result.turns_used` rather than a real tool-call counter; `api_calls` field is correct. Carryover from iter1.
4. `_hard_cost_halt` re-runs pytest each turn check; functionally fine, slightly noisy.

**DISPUTED FINDINGS:** None — I did not contradict the worker's harness-false-positive classification after independently inspecting `state.py:75` and the call1 log.

## Optimization vs R13/R14/R16

R15 remains non-redundant: diagnostic repair (find planted bugs without touching the false-positive helper or the test file) is not exercised by R13 (greenfield from spec), R14 (cross-file refactor + stale-symbol grep), or R16 (long-session app build with software_builder_subchecks). Call1 already produced model behavior consistent with the R15 capability claim.

## Section recap

EXPECTED ROW COUNT: N/A (Phase A retry preflight, not block ledger)
LEDGER ROW COUNT: N/A
DISPOSITION COUNTS: N/A

REMAINING SHIP-BLOCKING ROWS: 0 for AWS call2 spend approval. 2 wrapper preconditions (telemetry contract emission, cache-evidence row) carry into Phase C and must be closed before `GENUINE_PASS`.

3-attempt rule: this retry is attempt 2 of 3. Approved.

PHASE A VERDICT: APPROVE_FOR_AWS_CALL
