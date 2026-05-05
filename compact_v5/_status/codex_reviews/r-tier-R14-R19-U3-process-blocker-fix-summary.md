# R14/R19-U3 Process Blocker Fix Summary

Date: 2026-05-06

Status: RESOLVED_BY_STAGE5_CALL2_PENDING_RECURRENCE_WATCH

Scope:

- R14 artifact pass remains valid and is not replaced.
- R19-U3 call1 remains diagnostic/non-ready spend.
- R18-E7 call1 cap exceed remains diagnostic/non-ready spend.
- No prior spend, failed call, raw log, telemetry, side metrics, or audit file
  was deleted or hidden.

## Root Cause

The shared R14/R19-U3 failure-loop pattern had one primary implementation root
cause and one runtime-control gap.

Primary root cause:

- `read_file` did not call `_file_read_tracking.mark_read()` after a successful
  read.
- `edit_file` and `write_file` enforce read-before-edit/read-before-overwrite
  using `_file_read_tracking.was_read()`.
- Therefore the model could correctly call `read_file`, then still receive
  "Must read file before editing/overwriting" guard failures on later
  `edit_file`/`write_file` calls.
- R14 amplified this into batched edit/write failures across many files.
- R19-U3 reproduced the same class on a smaller fixture.

Runtime-control gap:

- Existing repeated-call detection keyed by exact tool arguments, so it blocked
  only identical retries.
- R14/R19-U3 varied file paths and later varied strategy (`edit_file` ->
  `write_file` -> `python_exec`), so the exact-argument breaker did not stop
  the guard class early.
- `python_exec` nonzero exit output was not classified as a tool failure unless
  it started with a generic error prefix.

## Fix

Implementation:

- `tools/read_file.py`
  - Marks a successful read in `_file_read_tracking` for empty, normal, and
    large-file preview paths.
- `tools/_file_read_tracking.py`
  - Canonicalizes paths with `abspath` + `normcase` so read/write checks match
    on Windows path spelling.
  - Stores a last-read snapshot for existing edit staleness false-positive
    logic.
- `core/query_engine.py`
  - Adds `failure_class` telemetry for guard failures:
    - `read_before_edit`
    - `read_before_write`
    - `bash_cd_blocked`
    - `python_exec_error`
  - Blocks repeated guard-class failures after two actual failures, even when
    arguments differ.
  - For `python_exec_error`, requires the failures to also be consecutive
    before pre-blocking a later `python_exec`, so two historical script errors
    do not permanently disable later successful scripts after recovery.
  - Emits typed `tool_failure_loop_blocked` events for class-level blocking.
  - Treats nonzero `[exit code: N]` tool output as a tool failure.
  - R14 and Stage 5 runners keep R14/R19-U3 on Haiku 4.5 AU and now include
    process-quality checks in their executable READY condition. Metrics record
    tool order, tool count, edit/exec counts, failure-loop event count, guard
    failure class counts, and `process_quality_ok`.
- `compact_v5/_status/scripts/r_tier_gate.py`
  - Allows historical diagnostic/non-ready metrics rows to remain in the
    ledger before a later genuine pass while still requiring a completed
    pass/ready row for READY evidence.
  - Cost checks continue to include all diagnostic spend.

Harness hardening:

- Stage 5 R19-U3 prompt now requires ASCII-only `change_summary.md` content to
  avoid spending turns on Windows cp1252/Unicode summary-file detours.
- Stage 5 R18-E7 large-result fixture now gives a deterministic replay offset
  while still requiring `sageagent-result://` + `result_replay`; the planned
  cap remains $0.10 and the user-approved hard retry ceiling is $0.12.

## Lock Tests

New zero-cost tests in
`compact_v5/MAIN/agent/tests/integration/test_software_compact_telemetry.py`:

- `test_read_file_marks_file_read_for_edit_path`
- `test_guard_class_breaker_blocks_batched_unread_edit_loop`
- `test_guard_class_breaker_blocks_batched_unread_write_loop`
- `test_guard_class_breaker_blocks_repeated_python_exec_errors`
- `test_python_exec_error_class_allows_later_script_after_success`

These tests prove the agent path can edit after a real `read_file` and cannot
continue unbounded edit/write/exec loops after explicit guard failures.
They also prove two failed `python_exec` calls do not permanently block a later
valid script after an intervening successful tool call.

## Local Validation

Run on 2026-05-06:

```text
py -3.11 -m py_compile compact_v5/MAIN/agent/core/query_engine.py compact_v5/MAIN/agent/tools/_file_read_tracking.py compact_v5/MAIN/agent/tools/read_file.py compact_v5/MAIN/agent/tests/integration/test_software_compact_telemetry.py
PASS

$env:PYTHONPATH=(Resolve-Path compact_v5/MAIN/agent).Path
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_build_telemetry.py compact_v5/MAIN/agent/tests/integration/test_software_compact_telemetry.py compact_v5/MAIN/agent/tests/tools/test_phase4_mutating_tools.py -q
54 passed

$env:PYTHONPATH=(Resolve-Path compact_v5/MAIN/agent).Path
py -3.11 -m pytest compact_v5/MAIN/agent/tests/r_tier/test_r19_u3_u6_u7_r18_e7_recovery_bundle.py -q
1 skipped

py -3.11 -m py_compile compact_v5/MAIN/agent/core/query_engine.py compact_v5/MAIN/agent/tools/_file_read_tracking.py compact_v5/MAIN/agent/tools/read_file.py compact_v5/MAIN/agent/tests/integration/test_software_compact_telemetry.py compact_v5/MAIN/agent/tests/r_tier/test_r19_u3_u6_u7_r18_e7_recovery_bundle.py compact_v5/_status/scripts/build_telemetry.py
PASS

$env:PYTHONPATH=(Resolve-Path compact_v5/MAIN/agent).Path
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_build_telemetry.py compact_v5/MAIN/agent/tests/integration/test_software_compact_telemetry.py compact_v5/MAIN/agent/tests/tools/test_phase4_mutating_tools.py compact_v5/MAIN/agent/tests/r_tier/test_r19_u3_u6_u7_r18_e7_recovery_bundle.py -q
54 passed, 1 skipped

$env:PYTHONPATH=(Resolve-Path compact_v5/MAIN/agent).Path
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_build_telemetry.py compact_v5/MAIN/agent/tests/integration/test_software_compact_telemetry.py compact_v5/MAIN/agent/tests/tools/test_phase4_mutating_tools.py compact_v5/MAIN/agent/tests/r_tier/test_r14_multifile_refactor.py compact_v5/MAIN/agent/tests/r_tier/test_r19_u3_u6_u7_r18_e7_recovery_bundle.py -q
55 passed, 2 skipped

$env:PYTHONPATH=(Resolve-Path compact_v5/MAIN/agent).Path
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_r_tier_gate.py compact_v5/MAIN/agent/tests/integration/test_software_compact_telemetry.py compact_v5/MAIN/agent/tests/r_tier/test_r14_multifile_refactor.py compact_v5/MAIN/agent/tests/r_tier/test_r19_u3_u6_u7_r18_e7_recovery_bundle.py -q
16 passed, 2 skipped
```

Claude iter1 review returned `APPROVE_FIX_AND_RETRY_PATH` with one medium
finding: the initial `python_exec_error` class breaker could block future
`python_exec` calls based on two historical failures even after intervening
successful tools. The implementation was refined so `python_exec_error`
pre-blocking requires both two class failures and two consecutive tool failures.
This keeps the repeated-failure circuit breaker active for R14/R19-U3 style
loops without turning cumulative historical script errors into a permanent
session-level ban.

## Retry Conditions

Claude CLI independently read the fix from disk and approved the Haiku-only
retry path in iter3 and iter4. Stage 5 call2 then passed with Phase C
`GENUINE_PASS` and per-test gates.

If approved:

- Stage 5 used `R_TIER_CALL=2`;
- preserve all call1 evidence and costs;
- do not raise any planned per-test cap;
- keep R14/R19-U3 on Haiku 4.5 AU only; do not switch them to Sonnet;
- require acceptable process quality in addition to artifact correctness:
  visible search/read before edit where applicable, reviewed tool count and
  failure-loop telemetry, no repeated non-intentional read-before-edit/write
  guard loop, and no repeated failed exec recovery loop;
- R19-U3 call1 cost $0.1090 remains diagnostic/non-ready spend;
- R18-E7 call1 cost $0.1022 remains diagnostic/non-ready spend and cap exceed
  evidence;
- R19-U3, R19-U6, R19-U7, and R18-E7 call1 diagnostic costs are recorded in
  `r_tier_metrics.jsonl`; these rows are not READY evidence but remain part of
  cumulative spend accounting;
- R18-E7 retry targets the original $0.10 planned cap, may use only the
  user-approved $0.12 hard retry ceiling, and must stop if it exceeds $0.12;
- any recurrence of the R14/R19-U3 guard-loop pattern stops the matrix.

Stage 5 call2 result:

- R19-U3 passed on Haiku at $0.0501 with `search_before_edit=true`,
  `process_quality_ok=true`, 13 tool calls, one isolated `bash_cd_blocked`
  event, no repeated guard-class loop, no repeated failed exec recovery loop,
  and no `max_turns`.
- R19-U6 passed at $0.0175 with malformed-output recovery.
- R19-U7 passed at $0.0230 with `breaker_fired=true` and exactly two actual
  bait tool executions.
- R18-E7 passed at $0.0226 under the original $0.10 planned cap using
  `result_replay` and a persisted `sageagent-result://` reference.
- Claude Phase C returned `GENUINE_PASS` and stated that R14 does not need an
  immediate targeted rerun; the issue remains on recurrence watch for R16,
  R19-U10, and later software-builder tests.
