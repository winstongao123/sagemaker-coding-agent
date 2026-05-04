# Block A Tests

Date: 2026-05-04

## Baseline Tests Run

### `py -3.11 -m pytest tests\integration\test_block_a.py -q`

Working directory: `compact_v5/MAIN/agent`

Result: PASS

```text
.........................                                                [100%]
25 passed in 0.59s
C:\Users\winst\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\requests\__init__.py:113: RequestsDependencyWarning: urllib3 (2.3.0) or chardet (7.4.0.post2)/charset_normalizer (3.4.1) doesn't match a supported version!
  warnings.warn(
```

## Gate Run

### `py -3.11 compact_v5\_status\scripts\r_tier_gate.py --repo-root .`

Result: FAIL

The gate fails for missing executable markers, including R4. Full output is recorded in `BASELINE.md`.

### `py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root .`

Result after A-16/A-25 batch: FAIL

```text
R-tier gate FAILED:
  - missing executable marker for R6
  - missing executable marker for R7
  - missing executable marker for R8
  - missing executable marker for R9
  - missing executable marker for R10
  - missing executable marker for R11
  - missing executable marker for R12
  - missing executable marker for R13
  - missing executable marker for R14
  - missing executable marker for R15
  - missing executable marker for R16
  - missing executable marker for R18-E1
  - missing executable marker for R18-E2
  - missing executable marker for R18-E3
  - missing executable marker for R18-E4
  - missing executable marker for R18-E5
  - missing executable marker for R18-E6
  - missing executable marker for R18-E7
  - missing executable marker for R18-E8
  - missing executable marker for R18-E9
  - missing executable marker for R18-E10
  - missing executable marker for R18-E11
  - missing executable marker for R18-E12
  - missing executable marker for R18-E13
  - missing executable marker for R18-E14
  - missing executable marker for R18-E15
  - missing executable marker for R19-U1
  - missing executable marker for R19-U2
  - missing executable marker for R19-U3
  - missing executable marker for R19-U4
  - missing executable marker for R19-U5
  - missing executable marker for R19-U6
  - missing executable marker for R19-U7
  - missing executable marker for R19-U8
  - missing executable marker for R19-U9
  - missing executable marker for R19-U10
```

R4 no longer appears in the missing-marker list because `tests/r_tier/test_r4_cold_cache.py` exists. The R4 test was not run; it remains real-AWS gated.

### `py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root .`

Result after R-tier readiness spec materialization: PASS

```text
R-tier gate PASSED
```

This pass is local and zero-AWS. It means all 42 executable markers are now
materialized and the cost ledger is within cap. It does not mean the R-tier
scenario evidence is complete.

## Test Gap

Existing `test_block_a.py` now covers the narrowed historical Block A implementation, the A-16/A-17/A-21/A-25 batch approved by Claude iter7, the broad Block A helper slice recorded in PORT_LOG #109 / ADR-041, and the remaining-row implementation recorded in PORT_LOG #110 / ADR-042. Scope audit and Claude review still need to verify the row mapping.

## A-16/A-25 Implementation Tests

### `py -3.11 -m pytest tests/integration/test_block_a.py -q`

Working directory: `compact_v5/MAIN/agent`

Result: PASS

```text
.............................                                            [100%]
29 passed in 0.58s
C:\Users\winst\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\requests\__init__.py:113: RequestsDependencyWarning: urllib3 (2.3.0) or chardet (7.4.0.post2)/charset_normalizer (3.4.1) doesn't match a supported version!
  warnings.warn(
```

Previous A-16/A-25-only run:

```text
............................                                             [100%]
28 passed in 0.54s
C:\Users\winst\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\requests\__init__.py:113: RequestsDependencyWarning: urllib3 (2.3.0) or chardet (7.4.0.post2)/charset_normalizer (3.4.1) doesn't match a supported version!
  warnings.warn(
```

New/changed assertions:

- `test_microcompact_cold_cache_keep_last_1` proves cold-cache mode keeps only the newest compactable tool result body.
- `test_compactable_tools_allowlist_excludes_document_creators` proves the A-17 allowlist excludes document/excel/pdf creators.
- `test_run_post_compact_cleanup_invalidates_context_caches` proves A-21 post-compact cleanup invalidates file-read tracking, file cache, skill-listing cache, and prompt-section cache.
- `test_cold_cache_30min_idle_triggers_microcompact` proves the QueryEngine pre-call idle trigger emits `[i] Cold cache detected` and sends a microcompacted prompt.
- `test_h2_stub_injection_for_orphan_tool_use` proves compaction inserts a synthetic `tool_result` for an orphaned post-compact `tool_use`.

## A-21 Implementation Tests

### `py -3.11 -m pytest tests/integration/test_block_a.py -q`

Working directory: `compact_v5/MAIN/agent`

Result: PASS

```text
..............................                                           [100%]
30 passed in 0.51s
C:\Users\winst\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\requests\__init__.py:113: RequestsDependencyWarning: urllib3 (2.3.0) or chardet (7.4.0.post2)/charset_normalizer (3.4.1) doesn't match a supported version!
  warnings.warn(
```

### `py -3.11 -m pytest tests/tools/test_phase4_mutating_tools.py -q`

Working directory: `compact_v5/MAIN/agent`

Result: PASS

```text
.......................................                                  [100%]
39 passed in 2.59s
C:\Users\winst\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\requests\__init__.py:113: RequestsDependencyWarning: urllib3 (2.3.0) or chardet (7.4.0.post2)/charset_normalizer (3.4.1) doesn't match a supported version!
  warnings.warn(
```

## Broad Block A Helper Slice Tests

### `py -3.11 -m pytest tests\integration\test_block_a.py -q`

Working directory: `compact_v5/MAIN/agent`

Result: PASS

```text
................................................                         [100%]
48 passed in 0.60s
C:\Users\winst\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\requests\__init__.py:113: RequestsDependencyWarning: urllib3 (2.3.0) or chardet (7.4.0.post2)/charset_normalizer (3.4.1) doesn't match a supported version!
  warnings.warn(
```

### `py -3.11 -m py_compile core\compactor.py core\query_engine.py runtime\bedrock_client.py runtime\config.py`

Working directory: `compact_v5/MAIN/agent`

Result: PASS

New broad-slice assertions:

- `test_a1_a2_a4_effective_context_budgets_and_warning_state`
- `test_a3_circuit_breaker_disables_after_three_failures`
- `test_a5_a19_auto_compact_query_source_guards`
- `test_a6_a7_summary_input_strips_images_and_reinjected_attachments`
- `test_a9_groups_messages_by_api_round`
- `test_a10_a11_a14_post_compact_file_attachments_exclude_memory_files`
- `test_a12_create_skill_attachment_if_active`
- `test_a15_a23_a24_warning_state_abort_and_stale_round_trip`
- `test_a20_abortable_retry_sleep_honors_abort`
- `test_a18_session_activity_heartbeat_updates`
- `test_a26_surrogate_sanitizer_recursive`
- `test_a28_a39_a41_a42_compact_metadata_and_todo_restoration`
- `test_a29_a35_tool_schema_tokens_pre_api_guard`
- `test_a30_a32_a37_a43_retry_reset_prefix_normalization_cache_ttl_temp_path`
- `test_a18_a30_auto_compact_failure_counter_and_success_reset`
- `test_a31_a34_a35_a36_query_engine_pre_guard_and_error_prefix`
- `test_a31_bedrock_cache_control_marks_last_three_messages`
- `test_a33_query_source_guard_skips_auto_compact`

## Remaining Block A Row Tests

### `py -3.11 -m py_compile core\compactor.py core\query_engine.py runtime\bedrock_client.py runtime\config.py`

Working directory: `compact_v5/MAIN/agent`

Result: PASS

### `py -3.11 -m pytest tests\integration\test_block_a.py -q`

Working directory: `compact_v5/MAIN/agent`

Result: PASS

```text
.....................................................                    [100%]
53 passed in 0.69s
C:\Users\winst\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\requests\__init__.py:113: RequestsDependencyWarning: urllib3 (2.3.0) or chardet (7.4.0.post2)/charset_normalizer (3.4.1) doesn't match a supported version!
  warnings.warn(
```

New remaining-row assertions:

- `test_a13_cache_sharing_fork_after_compact`
- `test_a27_flush_memories_before_compact_forces_memory_turn`
- `test_a33_prompt_cache_invariant_defers_tool_and_prompt_changes`
- `test_a34_transition_reason_enum_and_skip_api_error_hooks`
- `test_a38_preserved_segment_gc_keeps_latest_and_tail`

## Iter10 LOW-Finding Fix Tests

### `py -3.11 -m py_compile core\compactor.py core\query_engine.py runtime\bedrock_client.py runtime\config.py`

Working directory: `compact_v5/MAIN/agent`

Result: PASS

### `py -3.11 -m pytest tests\integration\test_block_a.py -q`

Working directory: `compact_v5/MAIN/agent`

Result: PASS

```text
.....................................................                    [100%]
53 passed in 0.94s
C:\Users\winst\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\requests\__init__.py:113: RequestsDependencyWarning: urllib3 (2.3.0) or chardet (7.4.0.post2)/charset_normalizer (3.4.1) doesn't match a supported version!
  warnings.warn(
```

Changed assertions:

- A-22: `test_a28_a39_a41_a42_compact_metadata_and_todo_restoration` now asserts summary -> recent tail -> todo restoration ordering.
- A-30: `test_a30_a32_a37_a43_retry_reset_prefix_normalization_cache_ttl_temp_path` now proves `reset_retry_counters()` re-enables `AUTO_COMPACT` after three failures.
- A-37: `test_a30_a32_a37_a43_retry_reset_prefix_normalization_cache_ttl_temp_path` checks TTL validation/fallback, and `test_a31_bedrock_cache_control_marks_last_three_messages` flips `CONFIG.cache_ttl` to `1h` and verifies emitted `cache_control` blocks include `ttl`.

## R4 Marker

Added `tests/r_tier/test_r4_cold_cache.py`. This is an executable marker for R4, but the test is skipped unless both `RUN_REAL_BEDROCK=1` and `RUN_R4_IDLE_WAIT=1` are set. It has not been run because AWS/R-tier spend requires explicit user approval.

### `py -3.11 -m pytest tests/r_tier/test_r4_cold_cache.py -q`

Working directory: `compact_v5/MAIN/agent`

Result: SKIPPED

```text
s                                                                        [100%]
1 skipped in 0.04s
C:\Users\winst\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\requests\__init__.py:113: RequestsDependencyWarning: urllib3 (2.3.0) or chardet (7.4.0.post2)/charset_normalizer (3.4.1) doesn't match a supported version!
  warnings.warn(
```

### `py -3.11 -m pytest tests/integration/test_r_tier_gate.py -q`

Working directory: `compact_v5/MAIN/agent`

Result: PASS

```text
.......                                                                  [100%]
7 passed in 0.10s
C:\Users\winst\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\requests\__init__.py:113: RequestsDependencyWarning: urllib3 (2.3.0) or chardet (7.4.0.post2)/charset_normalizer (3.4.1) doesn't match a supported version!
  warnings.warn(
```
