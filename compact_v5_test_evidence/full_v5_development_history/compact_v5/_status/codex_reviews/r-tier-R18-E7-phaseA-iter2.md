`APPROVE_FOR_AWS_CALL`

## Verdict summary

The Stage 5 call2 bundle (R19-U3 + R19-U6 + R19-U7 + R18-E7) is ready for one real-Bedrock invocation. The Haiku-only retry path is properly wired, per-test caps and the 20% buffer match the user-approved policy, the R14/R19-U3 process blocker has a real engine-layer fix locked by zero-cost tests, and call1 diagnostic spend is preserved.

The required Phase A gate ordering downstream of this approval still applies: explicit user spend approval and AWS Budget headroom check must be re-confirmed before `pytest` is invoked.

## Findings

### HIGH
None blocking.

### MEDIUM
None.

### LOW (carry-forward, non-blocking for Stage 5; resolve before R16)
- **LOW-A** `r_tier_gate.py:23-29` `DIAGNOSTIC_NON_READY_VERDICTS` includes the bare string `"FAIL"`. `test_r19_u3_u6_u7_r18_e7_recovery_bundle.py:454` writes `verdict="FAIL"` for any non-completed member, so a generic crash row would be auto-treated as diagnostic for telemetry-relaxation purposes. Cost still counts and READY still requires a separate pass row, so Stage 5 is not blocked, but tighten the set and migrate runners to a more specific diagnostic verdict before R16.
- **LOW-2** `query_engine.py:1663-1664` `_predict_guard_failure_class` returns `python_exec_error` unconditionally for any `python_exec`. The `_consecutive_tool_failures >= 2` extra gate prevents wrong outcomes today, but the block-message wording could mislead a future R16 run on a genuinely new well-formed script. Consider gating the predictor on a recent-failure window.
- **LOW-3** `query_engine.py:1619` `_failure_class` keys on substring `"error_during_execution"` while `query_engine.py:1599-1605` `_looks_like_tool_failure` uses `"error_during_execution:"` with the colon. Tolerable today; align before R19-U7/R16 quality reviews treat unrelated `python_exec` loops as blockers.

### INFO
- `tests/r_tier/test_r19_u3_u6_u7_r18_e7_recovery_bundle.py:486` correctly raises `CONFIG.session_cost_limit` to `sum(_hard_ceiling(...))` = $1.20 for the bundle, while `_run_member` resets `TOKENS` and halts each member at its own `_hard_ceiling(test_id)`, so per-test ceilings ($0.60/$0.24/$0.24/$0.12) are enforced independently of the bundle ceiling.
- `_run_member` halt uses the test's `ready()` short-circuit. R18-E7's halt-ready (`kiwi-1842` in `long_output_report.md`) is weaker than `completed_by_test` (which also requires `result_replay_used`, `result_ref_seen`, and "result_replay" in the report). Practically benign because the fixture hides the checksum past the 2000-char preview cap (head+middle filler ≈2.7 KB) so the model cannot get `kiwi-1842` without `result_replay`.
- `r_tier_gate.py:395-399` enforces `breaker_fired=true` in R19-U7 telemetry; the runner asserts `breaker_fired` and `custom_tool_calls == 2`, matching the deterministic identical-args breaker semantics in `query_engine.py:1316-1338`.

## Explicit answers to the required statements

**Haiku-only R14/R19-U3 process blocker — adequately fixed for Stage 5 retry.**
- `tools/read_file.py:174,182,210` mark successful reads in `_file_read_tracking` for empty/normal/large-file-preview paths.
- `tools/_file_read_tracking.py:35-36` canonicalizes paths via `normcase(abspath(...))`.
- `core/query_engine.py:1340-1370` adds a class-level pre-call breaker for `read_before_edit`, `read_before_write`, `bash_cd_blocked`, `python_exec_error`, with `python_exec_error` additionally requiring `_consecutive_tool_failures >= 2` so historical script errors do not permanently disable later valid scripts.
- `query_engine.py:1604` treats nonzero `[exit code: N]` as a tool failure.
- Zero-cost lock tests at `test_software_compact_telemetry.py:180,216,257,294,320` cover the read-mark, batched edit/write guard breakers, batched `python_exec_error` breaker, and the success-between-failures unblock property.
- Both R14 (`test_r14_multifile_refactor.py:319-389`) and Stage 5 (`test_r19_u3_u6_u7_r18_e7_recovery_bundle.py:375-410`) pin Haiku 4.5 AU and hard-assert `process_quality_ok = not repeated_guard_loop and stop_reason != max_turns`, with R19-U3 additionally requiring `search_before_edit` (grep/glob). No Sonnet fallback exists in either runner.
- Local preflight `55 passed, 2 skipped` and `16 passed, 2 skipped` are consistent with all locks. R14 call1 stays `READY $0.0900`; R19-U3 / R19-U6 / R19-U7 / R18-E7 call1 rows remain in `r_tier_metrics.jsonl` rows 11-14 with their original verdicts and costs intact.

**R18-E7 deterministic result-replay redesign — acceptable under the $0.10 planned cap and $0.12 hard ceiling.**
- Prompt at `test_r19_u3_u6_u7_r18_e7_recovery_bundle.py:88-91` directs replay "near offset 2600" instead of asking the model to scan the full artifact.
- Fixture `_large_result` at `:291-296` places `STAGE5-CHECKSUM: kiwi-1842` deterministically inside the body past the 2000-char preview cap so the model must use `result_replay`.
- Planned cap pinned at `:32` (`"R18-E7": 0.10`); hard ceiling computed at `:43-44` via `1.20` multiplier yields `$0.12`. `_run_member` passes `cap=_hard_ceiling(test_id)` to halt at $0.12, and the bundle assertion at `:518` blocks any member with `cost_usd > _hard_ceiling(test_id)`. Cap is not silently raised, and the call1 $0.1022 cap-exceed remains as diagnostic spend rather than being reset.
- `completed_by_test["R18-E7"]` requires `result_replay_used AND result_ref_seen AND` both `kiwi-1842` and `result_replay` substrings in `long_output_report.md`, so a marker-only or hallucinated-checksum pass is not possible.

If the Stage 5 call2 retry shows the R14/R19-U3 guard-class loop again, stop the matrix immediately per the user constraint — do not rerun, bypass, or switch to Sonnet.
