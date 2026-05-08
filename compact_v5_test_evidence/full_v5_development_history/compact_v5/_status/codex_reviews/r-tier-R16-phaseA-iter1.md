I've read all the required artifacts and verified critical assumptions (Flask 3.0.0 available in py-3.11, gate requires the exact 8 subchecks the runner produces, side-channel propagation wired in build_telemetry.py:527-528, all imports resolve). Here's my Phase A judgment.

---

## Phase A Independent Review — R16 Long App Build

### Cap math check
- Planned $1.00, hard ceiling $1.20 (1.00 × 1.20 buffer enforced via `CONFIG.session_cost_limit = 1.20` and `_hard_cost_halt`).
- 8 primary turns × `max_tokens=2048` × Haiku 4.5 AU pricing (~$1/$5 per Mtok) ≈ $0.15–0.25 expected; deep headroom under cap.
- `IterationBudget(max_iterations=14)` is appropriately bounded.
- Early-stop wired: `on_stop_check=_hard_cost_halt` returns true on `cost ≥ ceiling` OR `_app_ready(tmp_path)`.

### Required-evidence pipeline
- Runner directly emits `r-tier-R16-aws-call<N>-side-metrics.json` with `software_builder_subchecks`.
- `build_telemetry.py` line 527–528 propagates `software_builder_subchecks` into the canonical telemetry.json.
- `r_tier_gate.py` line 385–408 enforces the exact same 8-key set the runner produces. Pipeline closed.
- All 8 required keys present in `_exercise_command_subchecks` return dict; matches `R_TIER_EVIDENCE_CONTRACT.md` exactly.
- Forced/local `compact_auto_end` typed audit event explicit + `forced_local_compaction_used=true` recorded — within OPTIMIZED_AWS_VALIDATION_PLAN allowance for R16's bounded fixture.

### Recurrence watch (R14/R19-U3)
- `_guard_failure_class_counts` covers `read_before_edit`, `read_before_write`, `bash_cd_blocked`, `python_exec_error`.
- `repeated_guard_loop = any(count >= 2 ...)` plus `result.stop_reason != "max_turns"` plus `len(order) <= 24` is a reasonable process-quality blocker.

### Local validation
- `py_compile` PASS, R16 runner skipped (gated correctly on `RUN_REAL_BEDROCK`), 9/9 build_telemetry lock tests green, imports resolve.

### Non-blocking weaknesses (must be addressed in Phase C / quality.md, not Phase A)
1. `cache_evidence_recorded` is `>= 0` — tautological. Real cache numbers will land in `cache_efficiency_trend` from `chat_response` usage. Phase C must verify numeric values OR write the `MODEL_LIMITATION` row per evidence contract; the runner does not auto-emit that row.
2. `cost_context_reported` is substring-based (`"Session cost:"`, `"Context window estimate"`) — passes trivially. OK as a typed-evidence indicator.
3. `background_shell_start_poll_kill` exercises `subprocess.Popen` directly, not the agent's shell tool. This is **extra** evidence (not in the 8 required subchecks), so it doesn't gate Phase A, but quality.md should not represent it as proof that the agent's shell tool can do background lifecycle.
4. No before/after hash on `tests/test_app.py` — if Haiku violates the prompt and edits the test file, post-run pytest could pass spuriously. Mitigated by the prompt instruction; Phase C must spot-check `tests/test_app.py` content equals the fixture template.
5. `_app_ready` runs pytest on every `on_stop_check` once `app.py` exists; small Flask app + `timeout=45` means worst case ~8 pytest spawns — tolerable.

### Stop-condition coverage
- ✅ Cap exceed → `_hard_cost_halt`.
- ✅ Max turns → `process_quality_ok` rejects.
- ✅ Missing `app.py` / failing tests → `final_artifact_quality_passed = False` and `artifact_ok = False`.
- ✅ Repeated guard loop → `process_quality_ok = False`.
- ✅ Subchecks missing/false → `subchecks_ok = False`.
- ⚠ Edit to `tests/test_app.py` not directly asserted (see #4 above); manual Phase C spot-check required.

### Decision

`APPROVE_FOR_AWS_CALL`

Conditional on, before spend:
- Fresh AWS Budget/headroom check (the contract you already agreed to).
- Phase C must (a) verify cache fields are either numeric in canonical telemetry or accompanied by the `MODEL_LIMITATION` row, and (b) confirm `tests/test_app.py` content is byte-identical to the fixture template after the run.

