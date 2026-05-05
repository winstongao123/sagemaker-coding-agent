I've read all required files and verified the design from disk. The delta since iter1 (test file hash check) is correctly wired in three places:

- `test_r16_long_app_build.py:320` — `initial_test_hash` computed immediately after fixture write.
- `test_r16_long_app_build.py:397` — post-run hash recomputed; `test_file_unchanged` boolean recorded.
- `test_r16_long_app_build.py:401, 442` — `test_file_unchanged=True` is now a hard component of `artifact_ok` AND is exposed in side metrics.

This closes the iter1 concern: a model that edits `tests/test_app.py` to make pytest pass will fail `artifact_ok`, fail the test, and leave `test_file_unchanged=false` visible in side metrics for Phase C.

---

## Phase A iter2 Review — R16 Long App Build

### Cap / budget math
- Planned $1.00, hard ceiling $1.20 (`CONFIG.session_cost_limit = _R16_HARD_CEILING_USD` = 1.00 × 1.20).
- `max_turns=8`, `IterationBudget(max_iterations=14)`, `max_tokens=2048` on Haiku 4.5 AU → expected spend ~$0.15–0.30; deep headroom.
- `_hard_cost_halt` returns true on `is_over_budget()` OR `_app_ready(tmp_path)`. Both early-exit paths sound.

### Evidence pipeline (closed)
- Runner emits `software_builder_subchecks` into side metrics → `build_telemetry.py:527-528` propagates them into canonical telemetry → `r_tier_gate.py:385-409` enforces the exact same 8-key set the runner produces. End-to-end shape matches `R_TIER_EVIDENCE_CONTRACT.md` exactly.
- Forced/local compaction explicit: typed `compact_auto_end` event with `path="forced_local"` + `forced_local_compaction_used=True`. Within OPTIMIZED_AWS_VALIDATION_PLAN allowance for R16's bounded fixture.
- Test file hash check now present (delta verified).

### R14/R19-U3 recurrence watch
- `_GUARD_FAILURE_CLASSES` covers all four required classes.
- `repeated_guard_loop = any(count >= 2 ...)` + `result.stop_reason != "max_turns"` + `len(order) <= 24` — appropriate process-quality gate.

### Local zero-cost validation
- py_compile PASS; R16 runner correctly skipped (RUN_REAL_BEDROCK gated); 9/9 build_telemetry lock tests green; imports resolve.

### Non-blocking weaknesses (must be addressed in Phase C / quality.md)
1. `cache_evidence_recorded = TOKENS.session_cache_read >= 0 and TOKENS.session_cache_write >= 0` is tautological. Phase C MUST verify numeric cache fields in canonical telemetry's `cache_efficiency_trend`/`per_turn`, OR write the explicit `MODEL_LIMITATION` row from `R_TIER_EVIDENCE_CONTRACT.md`. Runner does not auto-emit that row.
2. `cost_context_reported` is substring-based on `/cost` and `/context` output — passes trivially. Acceptable as typed-evidence indicator only.
3. `background_shell_start_poll_kill` exercises `subprocess.Popen` directly, NOT the agent's shell tool. Phase C quality.md must NOT overclaim this as proof the agent's shell tool supports background lifecycle. (Extra evidence, not in the 8 required subchecks.)
4. `_app_ready` runs pytest on every `on_stop_check` once `app.py` exists; with `timeout=45` and small Flask app, worst-case ~8 pytest spawns — tolerable.

### Stop-condition coverage
- ✓ Cap exceed → `_hard_cost_halt`.
- ✓ Max turns → `process_quality_ok=False`.
- ✓ Missing app.py / failing tests → `final_artifact_quality_passed=False`, `artifact_ok=False`.
- ✓ Repeated guard loop → `process_quality_ok=False`.
- ✓ Subchecks missing/false → `subchecks_ok=False`.
- ✓ Edit to `tests/test_app.py` → now caught by `test_file_unchanged` in `artifact_ok` (DELTA).

### Decision

`APPROVE_FOR_AWS_CALL`

Conditional on, before spend:
- Fresh AWS Budget/headroom check.
- Phase C must (a) verify cache fields are numeric in canonical telemetry OR write `MODEL_LIMITATION` row, (b) re-confirm `tests/test_app.py` hash equals fixture template (now also asserted in runner — Phase C should verify the side-metrics field independently).


