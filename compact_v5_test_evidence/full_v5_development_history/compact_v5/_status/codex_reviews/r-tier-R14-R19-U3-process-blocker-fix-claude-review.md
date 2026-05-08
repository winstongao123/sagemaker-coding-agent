Reviewed all the requested files. Here is my independent review.

---

# Independent Review — R14/R19-U3 Process Blocker Local Fix

**Verdict: `APPROVE_FIX_AND_RETRY_PATH`**

AWS may proceed to a fresh Stage 5 Phase A review (not directly to spend). Phase A approval and budget headroom must still be re-confirmed before the call.

## Acceptance criteria check

### 1. Root cause fixed at right architectural layer — PASS

The two-part diagnosis is convincing and the fix addresses both:

**Primary cause (read tracking gap)**: `read_file.py:174,182,210` now calls `read_tracking.mark_read(abs_path, content)` on the empty, large-file-preview, and normal-content return paths. `_file_read_tracking.py:43` canonicalizes paths via `os.path.normcase(os.path.abspath(...))`, so Windows path-spelling differences between the read and the later edit/write resolve to the same key. This cleanly removes the false-guard cause of the R14 batched edit/write loop.

**Runtime-control gap (varied-argument breaker)**: `query_engine.py:1340-1364` adds a class-level pre-call breaker keyed by `(tool_name, failure_class)` rather than argument hash; `query_engine.py:1602-1616` defines the four classes (`read_before_edit`, `read_before_write`, `bash_cd_blocked`, `python_exec_error`); `query_engine.py:1654-1686` predicts the class from the upcoming call so the third call is blocked even if it targets a new file path. `query_engine.py:1598` makes nonzero `[exit code: N]` count as a tool failure, which closes the python_exec-error blind spot.

The fix sits in the right places: tool-side tracking (root cause) plus engine-side guard (defense-in-depth). It does not paper over the symptom in test code.

### 2. Lock tests cover the model/agent path — PASS

The four new tests in `test_software_compact_telemetry.py:180-317` go through `QueryEngine` with `_ScriptedClient` and the real `all_registered()` tool surface, not unit-stubbed internals. They lock:

- `read_file → edit_file` succeeds with zero `tool_failure_recorded` events (proves the primary cause is fixed).
- 3-call batched unread `edit_file` produces exactly 2 failures plus a `tool_failure_loop_blocked` with `failure_class="read_before_edit"` (proves varied-arg class breaker works).
- Same shape for `write_file` (`read_before_write`).
- 3 syntax-broken `python_exec` calls produce 2 failures and 1 class block (`python_exec_error`).

This is the exact agent path that R14/R19-U3 exercised (class loops across varied paths). Combined with `54 passed, 1 skipped` across the broader suite, the gate is justifiable for a Phase A retry review. Tests cover the model/agent path, not just internal helpers.

### 3. Prior failed/non-ready spend preserved — PASS

The fix summary at `r-tier-R14-R19-U3-process-blocker-fix-summary.md:9-13` and `r_tier_review_log.md:13,16` keep:
- R14 call1 $0.0900 as READY (unchanged)
- R19-U3 call1 $0.1090 as diagnostic/non-ready
- R18-E7 call1 $0.1022 as diagnostic/non-ready cap exceed

`R_TIER_PROCESS_QUALITY_FOLLOWUPS.md` still flags both R19-U3 and R18-E7 as `PROCESS_BLOCKER_LOCAL_FIX_PENDING_CLAUDE_REVIEW` and `PROCESS_BLOCKER`. No raw log, telemetry, side metrics, or audit file was hidden. Retry path is `R_TIER_CALL=2` with new audit dirs, preserving call1 artifacts.

### 4. R18-E7 retry stays under $0.10 by design — PASS

`test_r19_u3_u6_u7_r18_e7_recovery_bundle.py:32` keeps `"R18-E7": 0.10`; line 378 still asserts `cost_used <= cap`; line 480 asserts `metrics["cost_usd"] <= _PER_TEST_CAPS[metrics["test"]]`. The harness redesign at lines 72-81 narrows the search to "near offset 2600" while still requiring `sageagent-result://` + `result_replay` (line 344-345 in side metrics, line 372 in completion check). The fixture (lines 263-268) places `STAGE5-CHECKSUM: kiwi-1842` at roughly byte offset 2656, so a deterministic small-slice replay near 2600 reaches it without scanning the whole artifact. The cap is not silently raised.

### 5. Next AWS step requires fresh Phase A — PASS

Fix summary explicitly says "No AWS retry is allowed until Claude CLI independently reads this fix from disk and approves the retry path." `PS_AWS_TEST_EXECUTION_LOOP.md:42` still enforces "No Phase A approval means no AWS call." The gate ordering is intact.

## Findings

### MEDIUM

- **MED-1**: `_predict_guard_failure_class` for `python_exec` returns `"python_exec_error"` unconditionally on any python_exec call (`query_engine.py:1657-1658`). Combined with monotonic class counters that never reset on success, this means after 2 cumulative python_exec-error failures in a session, **every** subsequent `python_exec` call is blocked for the rest of the session — even if the third script is correct and even if many successful python_exec calls happened in between. This is heavier than the fix summary describes ("blocks repeated guard-class failures after two actual failures even if arguments differ"). For R16 long-app runs this could unintentionally cut off a legitimate later use of python_exec. Not a blocker for Stage 5 retry (R19-U3 used edit/write guards, not python_exec class loops), but worth a follow-up note before R16. Recommend either (a) reset the class counter on a python_exec success, or (b) gate the python_exec predictor on a recent-failure window rather than session totals.

### LOW

- **LOW-1**: Same monotonic-counter concern applies to the other three classes, but is much less likely to bite because their predictors actually inspect arguments (file path, cd token), so once the model adapts, the predictor returns `None` for valid calls and the count is irrelevant.
- **LOW-2**: `_failure_class` for python_exec keys on substring `"error_during_execution"` (`query_engine.py:1613`) while `_looks_like_tool_failure` uses `"error_during_execution:"` (`:1593`). Drift between these two classifiers is tolerable today but worth aligning before R19-U7 quality review treats unrelated python_exec loops as blockers.
- **LOW-3**: The R19-U3 prompt change is narrow ("ASCII-only `change_summary.md`"). It is preventive against cp1252/Unicode detours, not the actual call1 failure cause. That is fine, but means the harness change does not directly close the call1 loop — the engine fix does.

### INFO

- The R18-E7 fixture's checksum offset is approximately 2656 bytes from the start; the prompt's "near offset 2600" guidance is correct without being a give-away. The model still has to perform a real replay slice.
- `r_tier_review_log.md:13-16` correctly records the four members' dispositions (R19-U3/R18-E7 = `PROCESS_BLOCKER_LOCAL_FIX_PENDING_CLAUDE_REVIEW`; R19-U6/R19-U7 = `CALL1_FUNCTIONAL_PASS_BUNDLE_BLOCKED`).

## AWS proceed disposition

**AWS may proceed to a fresh Stage 5 Phase A design review** with `R_TIER_CALL=2`. It may **not** proceed directly to spend. Before any spend:

1. New Phase A prompt + Claude approval over the redesigned harness and the engine fix.
2. Explicit user spend approval and AWS Budget headroom check.
3. R18-E7 retry must enforce the original $0.10 cap with no buffer.
4. Any recurrence of the guard-class loop pattern in the retry stops the matrix immediately, per the contract at `R_TIER_EVIDENCE_CONTRACT.md:233-235`.
5. Note MED-1 in the Phase A prompt so the R16 plan can decide whether to soften the python_exec class breaker before a long-app run.

No call1 evidence may be deleted, hidden, or reclassified during the retry.
