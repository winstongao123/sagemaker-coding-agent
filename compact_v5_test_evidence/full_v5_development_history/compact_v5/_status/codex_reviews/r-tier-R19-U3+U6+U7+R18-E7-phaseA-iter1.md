APPROVE_FOR_AWS_CALL

Summary: bundle design, fixtures, prompts, runners, caps, evidence routes, and the implementation hooks (typed `tool_failure_loop_blocked` audit event in `query_engine.py`; `breaker_fired` propagation in `build_telemetry.py`) all verify against the OPTIMIZED_AWS_VALIDATION_PLAN, PS_AWS_TEST_EXECUTION_LOOP, and R_TIER_EVIDENCE_CONTRACT.

Verified directly from disk:
- `compact_v5/MAIN/agent/core/query_engine.py:1280-1290` emits `tool_failure_loop_blocked` on the 3rd identical dispatch (recent-calls path) and again at `:1318-1327` on the failure-count path. Both write `tool_name`, `args_hash`, `previous_failures`, `result_summary`. Telemetry-durable as required by R19-U7.
- `compact_v5/_status/scripts/build_telemetry.py:525-526` propagates `side_channel.breaker_fired` to top-level `telemetry["breaker_fired"]` only when non-null, so non-U7 members will not get a stray field.
- `compact_v5/MAIN/agent/tests/r_tier/test_r19_u3_u6_u7_r18_e7_recovery_bundle.py:339, 363, 405-410, 477-479` asserts `breaker_fired=True`, `custom_tool_calls==2` (exactly two real loop_bait dispatches, third blocked), and report content `safe-fallback-77`. Aligns with R19-U7 contract (Evidence Contract §"Selected-Test Evidence Additions").
- Per-member caps `0.50/0.20/0.20/0.10` sum to `$1.00`, matching plan §"Cost-Cap And Bundle Policy" Stage 5 line.
- Per-test side-metrics path `_status/r-tier-<TEST>-aws-call<N>-side-metrics.json` and per-test audit dirs are created with `R_TIER_CALL` honored, so post-run `build_telemetry.py` can produce per-test `telemetry.json`, metrics-jsonl rows, quality, and review-log rows as required for a bundled run.

Findings:

HIGH: none.

MEDIUM
- M1. R18-E7 depends on SOFTWARE-RESULTS shipping `sageagent-result://` refs and the `result_replay` tool dispatch path. Local skip-mode preflight does not exercise it. Phase C must validate the result_replay dispatch shows up in audit events and the report contains both `kiwi-1842` and a `result_replay` mention; otherwise treat as fail and do not retry without fixing SOFTWARE-RESULTS.
- M2. Side metrics hard-codes `cache_hit_pct=0.0`. Real cache evidence must come from post-run `build_telemetry.py` per-turn `chat_response.usage` aggregation or an explicit `MODEL_LIMITATION` row. Phase C must not accept the side-metrics zero as evidence of "no cache" — it is unfilled, not measured.
- M3. Audit dir is reused on rerun if `R_TIER_CALL` is not bumped (`mkdir(..., exist_ok=True)` does not clear). Operationally fine because the loop bumps `call` on retries, but document: retry must increment `R_TIER_CALL` to 2 before re-invocation, or the prior run's audit JSONL will leak into `breaker_fired`/`failure_loop_event_count`.

LOW
- L1. R19-U7 test side-metrics `tool_calls` adds blocked events to dispatches; consistent but Phase C must use audit events for the canonical dispatch count when checking R14-style repeat patterns on non-loop_bait tools.
- L2. Two `tool_failure_loop_blocked` paths (`_args_hash` vs `_failure_key`) use slightly different key construction. Either path satisfies R19-U7; cosmetic only.
- L3. Bundle shares one raw Bedrock log per evidence contract §"Bundle And Retry Policy". Reminder: per-test telemetry/metrics/quality/review-log rows must still be emitted; the bundle test only writes per-test audit + side-metrics — the rest is post-run.

R14 repeated-tool-loop follow-up coverage
- Adequately covered by R19-U7 preflight for THIS AWS call. The bundle:
  - asserts `breaker_fired=True` and exactly 2 real `loop_bait` dispatches before the block (matches R_TIER_PROCESS_QUALITY_FOLLOWUPS §R14 step 4);
  - emits a typed `tool_failure_loop_blocked` audit event with `previous_failures`, `args_hash`, `tool_name` so failure-loop telemetry is durable, not prose;
  - records `failure_loop_event_count` in side metrics so Phase C can detect loops outside the intentional bait window.
- The bundle does NOT have a hard assertion that non-`loop_bait` tools never enter a loop (e.g., R14-style `edit_file`/`write_file` retries after read-before-edit guards). Per R_TIER_PROCESS_QUALITY_FOLLOWUPS §R14, that judgment lives in the Phase C quality review. This is acceptable because the audit data needed to make that judgment is captured. It does NOT block this AWS call.
- Binding requirement on Phase C: the post-run quality review for R19-U7 must explicitly inspect (a) per-tool repeat counts in `tool_call_summary` outside the loop_bait window, (b) any `tool_failure_loop_warning`/`tool_failure_loop_blocked` events not attributed to `loop_bait`, and (c) classify any such recurrence as `PROCESS_BLOCKER` per the R14 follow-up. If Phase C does not perform this check, the R14 follow-up remains OPEN and final readiness is still blocked even if the artifact passes.

Bottom line: bundle is ready for one real Bedrock pytest invocation under the documented per-test caps and stop conditions. R14 follow-up is covered by R19-U7 within this call as long as Phase C enforces the explicit non-loop_bait-loop check above.
