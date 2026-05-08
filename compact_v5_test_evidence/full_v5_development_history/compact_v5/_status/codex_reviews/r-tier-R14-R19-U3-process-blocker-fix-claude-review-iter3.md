# Independent Review — R14/R19-U3 Process Blocker Local Fix (iter3)

**Verdict: `APPROVE_FIX_AND_HAIKU_RETRY_PATH`**

AWS may proceed to a fresh Stage 5 **Phase A design review only** with `R_TIER_CALL=2`. It may **not** proceed directly to spend. Phase A approval, explicit user spend approval, and AWS Budget headroom must all be re-confirmed.

## Acceptance Criteria

### 1. Tool/runtime fix preserved — PASS
- `read_file.py:174,182,210` still calls `read_tracking.mark_read(abs_path, content)` on empty / large-file preview / normal paths.
- `_file_read_tracking.py:35-36` still canonicalizes via `os.path.normcase(os.path.abspath(...))`.
- `query_engine.py:1340-1370` keeps the class-level pre-call breaker for `read_before_edit`, `read_before_write`, `bash_cd_blocked`, `python_exec_error`.
- `query_engine.py:1604` still treats nonzero `[exit code: N]` as a tool failure.
- Identical-args breaker preserved at `:1316-1338`.

### 2. New regression test addresses iter2 LOW-1 — PASS
`test_software_compact_telemetry.py:320-358` (`test_python_exec_error_class_allows_later_script_after_success`) drives `QueryEngine` with a real script: `python_exec(syntax error) → python_exec(syntax error) → read_file(success) → python_exec(well-formed)`. It asserts exactly 2 `tool_failure_recorded` for `python_exec` and **`blocked == []`**. This locks the success-between-failures unblock property: `_record_tool_success()` zeroes `_consecutive_tool_failures` after `r1`, and the python_exec-specific extra condition at `query_engine.py:1345-1349` (`_class_count >= 2 AND _consecutive_tool_failures >= 2`) means p3 is no longer pre-blocked even though `_class_count` is still 2. Adequate coverage of iter2 LOW-1.

### 3. R14 and R19-U3 retry paths are Haiku-only — PASS
- `test_r14_multifile_refactor.py:26,257,267` pins `_HAIKU_45_AU = au.anthropic.claude-haiku-4-5-20251001-v1:0`, sets `CONFIG.model_id = _HAIKU_45_AU`, and constructs `BedrockClient(model_id=_HAIKU_45_AU,...)`.
- `test_r19_u3_u6_u7_r18_e7_recovery_bundle.py:27,487,495` does the same. No Sonnet fallback.
- Evidence docs (`PS_AWS_TEST_EXECUTION_LOOP.md:123-132`, `OPTIMIZED_AWS_VALIDATION_PLAN.md:191-197`, `R_TIER_EVIDENCE_CONTRACT.md:236-237`, `R_TIER_PROCESS_QUALITY_FOLLOWUPS.md:60-62`) all spell out Haiku-only.

### 4. Process quality mandatory in executable runners — PASS
- **R14** (`test_r14_multifile_refactor.py:319-324, 369-371, 388-389`): `process_quality_ok = read_or_search_before_edit AND not repeated_guard_loop AND stop_reason != "max_turns"`. `completed` and `verdict==GENUINE_PASS` both AND `artifact_ok` with `process_quality_ok`. Hard asserts on `read_or_search_before_edit` and `not repeated_guard_loop`.
- **Stage 5** (`test_r19_u3_u6_u7_r18_e7_recovery_bundle.py:375-383, 385-410`): `process_quality_ok = not repeated_guard_loop AND stop_reason != "max_turns"`. R19-U3 additionally requires `search_before_edit` (grep/glob, not `read_file`, matching the prompt). `completed_by_test` for every Stage 5 member ANDs `process_quality_ok`. Bundle-level assertion at `:517` requires `metrics["completed"] is True`.
- New telemetry recorded: `tool_order`, `tool_calls`, `edit_tool_count`, `exec_tool_count`, `failure_loop_event_count`, `guard_failure_class_counts`, `read_or_search_before_edit` / `search_before_edit`, `process_quality_ok`. Final-artifact correctness alone no longer satisfies the gate.

### 5. Prior failed/non-ready spend preserved — PASS
`r_tier_review_log.md` rows 10/13/14/15/16 keep R14 call1 READY $0.0900, R19-U3 call1 $0.1090 diagnostic/non-ready, R19-U6 / R19-U7 functional pass within blocked bundle ($0.0175 / $0.0221), R18-E7 call1 $0.1022 diagnostic/non-ready cap exceed. `R_TIER_PROCESS_QUALITY_FOLLOWUPS.md` keeps R19-U3 / R18-E7 in `PROCESS_BLOCKER_LOCAL_FIX_PENDING_CLAUDE_REVIEW`. Fix summary explicitly states "No prior spend, failed call, raw log, telemetry, side metrics, or audit file was deleted or hidden." Retry uses `R_TIER_CALL=2`, which writes new audit dirs without overwriting call1 artifacts.

### 6. R18-E7 retry stays at $0.10 planned cap with $0.12 ceiling — PASS
`test_r19_u3_u6_u7_r18_e7_recovery_bundle.py:32` pins `"R18-E7": 0.10`. `_USER_APPROVED_RETRY_BUFFER_MULTIPLIER = 1.20` (`:34`) yields hard ceiling $0.12. `_run_member` passes `cap=_hard_ceiling(test_id)` to halt at $0.12. Per-member assertion `:518` blocks `cost_usd > $0.12`. The `:88-91` prompt narrows replay near offset 2600 while still requiring `sageagent-result://` + `result_replay`, and `:404-409` completion requires `result_replay_used AND result_ref_seen AND` both `kiwi-1842` and `result_replay` substrings in `long_output_report.md`. Cap is not silently raised.

### 7. Next AWS step is fresh Phase A only — PASS
`PS_AWS_TEST_EXECUTION_LOOP.md:42` "No Phase A approval means no AWS call." `:119-132` 2026-05-06 Stage 5 stop and Haiku-only retry rule intact. `OPTIMIZED_AWS_VALIDATION_PLAN.md:185-200` 2026-05-06 stop note intact. Fix summary `:135-137` says "No AWS retry is allowed until Claude CLI independently reads this fix from disk and approves the retry path." Gate ordering preserved.

## Findings

### MEDIUM
None blocking.

### LOW (carry forward from iter2; non-blocking for Stage 5 retry)
- **LOW-2** (carry): `_predict_guard_failure_class` returns `python_exec_error` unconditionally for any `python_exec` (`query_engine.py:1663-1664`). The `_consecutive_tool_failures >= 2` gate prevents wrong outcomes, but the block-message wording could mislead the model on a genuinely new well-formed script. Cosmetic; consider gating the predictor on a recent-failure window before R16.
- **LOW-3** (carry): `_failure_class` keys on substring `"error_during_execution"` (`:1619`) while `_looks_like_tool_failure` uses `"error_during_execution:"` with the colon (`:1599`). Tolerable today but worth aligning before R19-U7/R16 quality reviews treat unrelated `python_exec` loops as blockers.

### INFO
- The new regression test uses single-call `("tool", ...)` script entries (one `chat_response` per tool), which is the realistic shape for the success-between-failures recovery property. Prior batched `("tools", [...])` tests cover the in-batch class-breaker shape. Both shapes locked.
- R14 runner permits `read_file` to satisfy "search before edit"; Stage 5 R19-U3 runner restricts to grep/glob, matching the U3 prompt requirement. Asymmetry is intentional and consistent with each test's spec.
- `test_r14_multifile_refactor.py:269-273` retains `_hard_cost_halt` which is `over_budget OR _r14_ready` — the harness still halts when artifact is correct, but `process_quality_ok` is now a separate gate evaluated post-halt, so an artifact-correct/process-bad run will halt early and then fail the assertion (correct behavior, no silent "halt = pass").

## AWS Disposition

**AWS may proceed to a fresh Stage 5 Phase A design review with `R_TIER_CALL=2`.** Required before any spend:

1. New Phase A prompt + Claude `APPROVE_FOR_AWS_CALL` over the iter3 fix and runners.
2. Explicit user spend approval and AWS Budget headroom check.
3. R18-E7 retry must keep planned $0.10 cap and may only use the user-approved $0.12 hard ceiling — stop if `cost_usd > $0.12`.
4. Any recurrence of the R14/R19-U3 guard-class loop in the retry stops the matrix immediately, per the `R_TIER_EVIDENCE_CONTRACT.md` guard-loop rule.
5. If Haiku still cannot pass after this fix and Claude-reviewed retry path, **stop and escalate** rather than switching R14/R19-U3 to Sonnet (per the user constraint).
6. LOW-2 / LOW-3 stay open; address the `_predict_guard_failure_class` recent-window gating and substring alignment before R16 long-app runs.

A targeted R14 process-only confirmation is **optional** and the lower-signal path: the fix is engine-side and locked by zero-cost tests, and the Stage 5 retry exercises the same engine fix on a smaller fixture for less spend. Do not delete, hide, or reclassify any call1 evidence during the retry.
