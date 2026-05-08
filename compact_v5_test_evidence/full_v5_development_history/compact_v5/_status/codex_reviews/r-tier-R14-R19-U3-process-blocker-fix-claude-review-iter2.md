Reviewed all requested files from disk, including the iter2 implementation in `query_engine.py`, the four lock tests in `test_software_compact_telemetry.py`, the redesigned R18-E7 fixture in the recovery bundle, and the current process/follow-up/review-log evidence.

# Independent Review — R14/R19-U3 Process Blocker Local Fix (iter2)

**Verdict: `APPROVE_FIX_AND_RETRY_PATH`**

AWS may proceed to a fresh Stage 5 **Phase A design review** with `R_TIER_CALL=2`. It may **not** proceed directly to spend. Phase A approval, explicit user spend approval, and AWS Budget headroom must still be re-confirmed.

## Acceptance criteria check

### 1. Root cause fixed at the right architectural layer — PASS

Two-layer fix is well placed:

- **Tool-side root cause**: `read_file.py:174,182,210` now calls `read_tracking.mark_read(abs_path, content)` on the empty, large-file preview, and normal-content return paths. `_file_read_tracking.py:35-36` canonicalizes via `os.path.normcase(os.path.abspath(...))`, eliminating Windows path-spelling drift between read and later edit/write keys. This removes the false-guard cause of the R14 batched edit/write loop.
- **Engine-side defense-in-depth**: `query_engine.py:1340-1370` adds a class-level pre-call breaker keyed by `(tool_name, failure_class)`. `:1660-1692` predicts the four classes (`read_before_edit`, `read_before_write`, `bash_cd_blocked`, `python_exec_error`). `:1604` makes nonzero `[exit code: N]` count as a tool failure, closing the python_exec blind spot. Identical-args breaker at `:1316-1338` is preserved.

The fix does not paper over the symptom in test code.

### 2. Lock tests cover the model/agent path — PASS

The four new tests in `test_software_compact_telemetry.py:180-317` go through `QueryEngine` with `_ScriptedClient` and the real `all_registered()` tool surface (not stubbed internals). They lock:

- `read_file → edit_file` succeeds with zero `tool_failure_recorded` events (primary cause regression test).
- 3 batched unread `edit_file` calls produce exactly 2 `tool_failure_recorded` + 1 `tool_failure_loop_blocked` with `failure_class="read_before_edit"`.
- Same shape for `write_file` (`read_before_write`).
- 3 syntax-broken `python_exec` calls produce 2 failures + 1 class block (`python_exec_error`).

Combined with `54 passed, 1 skipped` across the broader suite, the gate is justifiable for a Phase A retry review. Tests exercise the agent path R14/R19-U3 actually used.

### 3. Iter1 MEDIUM (session-monotonic python_exec_error) adequately addressed — PASS (with one LOW)

`query_engine.py:1345-1349` adds a python_exec_specific extra condition: pre-blocking requires **both** `_class_count >= 2` **and** `_consecutive_tool_failures >= 2`. `_record_tool_success()` at `:1695` resets `_consecutive_tool_failures = 0` on any tool success, so after a single intervening successful tool call the python_exec class breaker re-opens even if the cumulative class count is still ≥2. This matches the fix-summary description and resolves iter1 MED-1.

LOW-1 (carry forward): the recovery property — "two python_exec failures, then a successful tool call, then a well-formed python_exec is NOT pre-blocked" — is correct in code but not directly locked by a test. The python_exec lock test only exercises the consecutive path. A regression that re-introduced session-monotonic blocking would not be caught by the existing suite. Recommend a regression test before R16, not a Stage 5 retry blocker.

### 4. Prior failed/non-ready spend preserved — PASS

`r_tier_review_log.md:13` keeps R19-U3 call1 at $0.1090 as `PROCESS_BLOCKER_LOCAL_FIX_PENDING_CLAUDE_REVIEW`; `:16` keeps R18-E7 call1 at $0.1022 diagnostic/non-ready cap exceed; `:10` keeps R14 call1 READY at $0.0900. `R_TIER_PROCESS_QUALITY_FOLLOWUPS.md` still flags R19-U3/R18-E7 with their blocking statuses. The fix summary explicitly states "No prior spend, failed call, raw log, telemetry, side metrics, or audit file was deleted or hidden." Retry path uses `R_TIER_CALL=2` with new audit dirs that do not overwrite call1 artifacts.

### 5. R18-E7 retry stays under $0.10 by design, only the $0.12 user-approved ceiling — PASS

- `test_r19_u3_u6_u7_r18_e7_recovery_bundle.py:32` keeps `"R18-E7": 0.10` in `_PER_TEST_CAPS`. Hard ceiling at `:37-38` = `0.10 * 1.20 = $0.12` (matches user-approved buffer). Per-test cap assertion at `:485` enforces `cost_usd <= _hard_ceiling`.
- Prompt at `:77-86` narrows search to "near offset 2600" while still requiring `sageagent-result://` + `result_replay`.
- Fixture at `:268-273`: head (1186 chars) + 105 middle filler lines (1470 chars) places `STAGE5-CHECKSUM: kiwi-1842` at ≈2656 bytes — a small slice replay near 2600 reaches it without scanning the whole artifact, but the model still has to do a real replay (preview cap is 2000 chars).
- Completion at `:374-378` requires `result_replay_used` AND `result_ref_seen` AND both `kiwi-1842` and `result_replay` substrings in `long_output_report.md`. The cap is not silently raised; planned cap stays $0.10, ceiling stays $0.12.

### 6. Next AWS step requires a fresh Phase A — PASS

Fix summary `:124-125` says "No AWS retry is allowed until Claude CLI independently reads this fix from disk and approves the retry path." `PS_AWS_TEST_EXECUTION_LOOP.md:42` still enforces "No Phase A approval means no AWS call." The 2026-05-06 Stage 5 stop note at `:119-121` is intact. Gate ordering is preserved.

## Findings

### MEDIUM
- None blocking.

### LOW
- **LOW-1**: Iter2 recovery property for `python_exec_error` (success-between-failures unblocks later python_exec) is correct but not regression-tested. Add a test before R16 long-app runs: `python_exec error → python_exec error → read_file success → python_exec well-formed` should pass without pre-block.
- **LOW-2**: `_predict_guard_failure_class` returns `python_exec_error` unconditionally for any `python_exec` call (`query_engine.py:1663-1664`). The block message says "stop retrying near-identical scripts" which can be misleading when the script is actually new and well-formed — the consecutive-failures gate prevents the wrong outcome but the wording could mislead the model into a strategy change it does not need. Cosmetic; consider gating the predictor on a recent-failure window.
- **LOW-3**: Classifier drift — `_failure_class` keys on substring `"error_during_execution"` (`:1619`) while `_looks_like_tool_failure` uses `"error_during_execution:"` with colon (`:1599`). Tolerable today but worth aligning before R19-U7/R16 quality reviews treat unrelated python_exec loops as blockers.

### INFO
- R18-E7 fixture checksum offset is ≈2656 bytes; "near offset 2600" guidance is correct without being a give-away. The model still must perform a real replay slice.
- `r_tier_review_log.md:13-16` correctly records all four Stage 5 member dispositions (`PROCESS_BLOCKER_LOCAL_FIX_PENDING_CLAUDE_REVIEW` for R19-U3/R18-E7; `CALL1_FUNCTIONAL_PASS_BUNDLE_BLOCKED` for R19-U6/R19-U7).
- The R19-U3 ASCII-only `change_summary.md` prompt change is preventive against cp1252/Unicode detours; the engine fix is what actually closes the call1 loop.

## AWS proceed disposition

**AWS may proceed to a fresh Stage 5 Phase A design review** with `R_TIER_CALL=2`. Before any spend:

1. New Phase A prompt + Claude approval over the redesigned harness and engine fix.
2. Explicit user spend approval and AWS Budget headroom check.
3. R18-E7 retry must keep the $0.10 planned cap and may use only the user-approved $0.12 hard retry ceiling — stop if cost crosses $0.12.
4. Any recurrence of the R14/R19-U3 guard-class loop pattern in the retry stops the matrix immediately, per `R_TIER_EVIDENCE_CONTRACT.md` guard-loop rule.
5. Carry LOW-1/LOW-2/LOW-3 forward; address the python_exec recovery regression test before R16.

A targeted R14 process confirmation is **optional** and not the higher-signal path: the fix is engine-side and is locked by zero-cost tests, and `R_TIER_PROCESS_QUALITY_FOLLOWUPS.md` already says "Do not rerun R14 only for this process issue unless a fix changes the behavior R14 measures." Stage 5 retry exercises the same fix on the smaller R19-U3/R18-E7 fixture for less spend.

No call1 evidence may be deleted, hidden, or reclassified during the retry.
