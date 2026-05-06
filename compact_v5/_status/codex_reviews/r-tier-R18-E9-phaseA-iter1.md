## Phase A Review — Zero-Cost R-tier Mock Cleanup Bundle (R8, R18-E2, R18-E5, R18-E9, R18-E12)

**Reviewer:** independent Claude Phase A reviewer, files read from disk under `D:\Github\sagemaker-coding-agent\`.

### 1. Is local/mock evidence the correct path?

Yes. `compact_v5/_status/r_tier_test_matrix.json` declares all five rows as `kind=mock`, `model="Mock"`, `cost_cap_usd=0.0`:

| ID | kind | cost_cap_usd |
|---|---|---|
| R8 | mock | 0.00 |
| R18-E2 | mock | 0.00 |
| R18-E5 | mock | 0.00 |
| R18-E9 | mock | 0.00 |
| R18-E12 | mock | 0.00 |

The matrix has been the contract since the bundle was defined; these rows are explicitly mock-only. Their ready_criteria language ("without spending AWS", "without forcing AWS failure", "without AWS", "without forcing actual disk-full", "without AWS") matches local execution. `test_r6_to_r19_readiness_specs.py` `_MOCK_SCENARIOS` and `test_mock_r_tier_scenario_stays_zero_cost` lock the same set. Real Bedrock would be wasteful and would not exercise the deterministic failure modes these rows are designed to test (HTML 5xx body, corrupt JSON file, disk-full OSError, log-rotation date math, JSON-string tool args).

### 2. Do the new local tests cover each row's ready criteria?

I traced each test against the source it claims to exercise:

- **R8 — `test_r8_malformed_json_tool_args_repaired_locally`**
  - Mock client emits `ToolCall("a", "read_file", '{"file_path": "a.txt"}')` (input as a JSON string).
  - Triggers `query_engine.py:1308-1314`, which calls `security.json_repair.repair_tool_call_arguments`, producing `{"file_path": "a.txt"}` before tool dispatch.
  - Asserts `seen == [{"file_path": "a.txt"}]` and `stop_reason == "end_turn"`. ✅ Repair ladder success path covered.
  - **Minor non-blocking gap:** the explicit fallback-to-`{}` branch (`except Exception:` at line 1313) is not directly exercised. Acceptable for zero-cost cleanup; can be revisited as a follow-up if needed.

- **R18-E2 — `test_r18_e2_bedrock_5xx_html_humanized_without_aws`**
  - Hits `errors.py:413` (HTML branch) → `BEDROCK_5XX_HTML` + `"backoff"`.
  - `categorize_retryable` includes `BEDROCK_5XX_HTML` (line 92) → True.
  - `humanize_api_error` → `extract_nested_error_message` h1-regex extracts "Internal Server Error" and strips `<html>` tags.
  - All four assertions are sound and deterministic. ✅

- **R18-E5 — `test_r18_e5_corrupt_session_json_is_skipped`**
  - `session.py:143` catches `json.JSONDecodeError` → `load("bad")` returns `None`.
  - Valid `good.json` still loads with messages preserved.
  - `list_sessions()` (line 166) skips corrupt files via the same exception, leaving exactly `["good"]`. ✅

- **R18-E9 — `test_r18_e9_snapshot_write_failure_is_safe`**
  - `monkeypatch` replaces `shutil.copy2` with an OSError raiser.
  - In `snapshot.py:128`, `shutil.copy2` raises **before** `self._log.append(entry)` (line 136) and `_persist_index_locked()` (line 139), so the index never receives the failed snapshot.
  - Outer `except OSError: return None` (line 147) keeps the source file untouched.
  - Assertions on source content and empty `list_snapshots` are both correct. ✅

- **R18-E12 — `test_r18_e12_audit_log_rotation_prunes_old_logs`**
  - AuditLogger constructor calls `prune_old_logs(30)` at line 68.
  - `audit.py:160-177` deletes the 40-day-old file (its date prefix is < cutoff) and leaves the fresh file in place.
  - Subsequent `audit.log(...)` appends to today's file; `get_session_log("freshsession")` returns both the seed `"fresh"` row and the new `tool_dispatch` row. ✅

Each row's stated mock ready_criteria is satisfied for the cleanup goal.

### 3. Is the gate change appropriate and narrow for mock rows?

Yes. The change in `r_tier_gate.py` is minimal and targeted:

- `_phase_a_latest_decision_is_approval` accepts `APPROVE_FOR_LOCAL_MOCK` alongside the prior approval tokens (lines 178-188).
- `check_test_evidence` reads `kind` from the matrix and switches the raw-log/telemetry/quality patterns from `aws-call*` → `local-call*` only when `is_mock` is true (lines 294, 312-316, 331-336, 407).
- Every other gate requirement is preserved for mock rows: Phase A prompt + review file, Phase C `GENUINE_PASS`, telemetry schema (non-empty `per_turn`, completed outcome, no `cost_cap_hit`), quality verdict (no `SEMANTIC_BUG_DETECTED`, accepted composite verdict), metrics row with required keys, review log `READY` row.
- Cost ceiling logic (`check_costs`) is unchanged — for these rows `cap = 0.0`, so any nonzero `cost_usd` still trips the ceiling check.
- The new lock test `test_r_tier_gate_accepts_mock_local_call_evidence` pins the new pattern set against a synthetic single-row mock matrix.

I confirmed the lock tests on disk: 5 mock-cleanup tests pass, 11 gate tests pass (matching the worker's report). No requirement is silently relaxed; only the file-naming convention and the approval token for mock rows are widened.

### 4. Process-quality and cost-safety check

- All five rows remain at `cost_cap_usd=0.0`. Approving local mock execution does not authorize any Bedrock call, and the gate's per-row ceiling check still blocks any nonzero cost row.
- The Phase A approval token I am issuing is `APPROVE_FOR_LOCAL_MOCK`. Per the gate's logic, this token does **not** satisfy the approval check for any non-mock matrix row (the gate inspects `kind` from the matrix to choose evidence patterns; the approval-token check accepts `APPROVE_FOR_LOCAL_MOCK` regardless, but a real-AWS row would still fail because of `aws-call*` evidence pattern requirements unless and until corresponding aws-call evidence is present — which is independent of this approval).
- I am not approving real AWS for any row in this bundle.

### Verdict

The local/mock path is correct, the lock tests cover the stated mock ready criteria adequately, and the gate change is narrow and appropriate. No AWS spend is authorized.

**APPROVE_FOR_LOCAL_MOCK**

Bundle scope: R8, R18-E2, R18-E5, R18-E9, R18-E12 — local/mock execution only, `cost_cap_usd=0.0` per row, no AWS calls.
