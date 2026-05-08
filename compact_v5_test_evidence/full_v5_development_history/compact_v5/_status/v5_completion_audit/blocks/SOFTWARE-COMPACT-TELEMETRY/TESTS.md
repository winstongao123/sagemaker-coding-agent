# SOFTWARE-COMPACT-TELEMETRY Tests

Status: READY_FOR_BLOCK_CLOSE_REVIEW
Date: 2026-05-05

Focused tests:

- `py -3.11 -m pytest tests/integration/test_software_compact_telemetry.py -q` -> `3 passed`
- Log: `compact_v5/_status/v5_completion_audit/logs/software-compact-telemetry-tests.log`

Telemetry-builder tests:

- `py -3.11 -m pytest tests/integration/test_build_telemetry.py -q` -> `8 passed`
- Log: `compact_v5/_status/v5_completion_audit/logs/software-compact-telemetry-build-telemetry-tests.log`

Regression tests:

- `py -3.11 -m pytest tests/integration/test_block_a.py::test_cold_cache_30min_idle_triggers_microcompact tests/integration/test_block_a.py::test_auto_compact_wired_into_query_engine_run tests/integration/test_block_a.py::test_a18_a30_auto_compact_failure_counter_and_success_reset tests/integration/test_block_n.py::test_query_engine_parallel_dispatch_keeps_repetition_guard -q` -> passed
- Log: `compact_v5/_status/v5_completion_audit/logs/software-compact-telemetry-regression-tests.log`

Compile gate:

- `py -3.11 -m py_compile compact_v5/MAIN/agent/core/query_engine.py compact_v5/_status/scripts/build_telemetry.py compact_v5/MAIN/agent/tests/integration/test_software_compact_telemetry.py compact_v5/MAIN/agent/tests/integration/test_build_telemetry.py` -> PASS
- Log: `compact_v5/_status/v5_completion_audit/logs/software-compact-telemetry-py-compile.log`

Original-block scope gates:

- `scope_audit.py --all --summary` -> `TOTAL_SHIP_BLOCKING_ROWS: 0`
- `scope_audit.py --all --strict` -> `TOTAL_SHIP_BLOCKING_ROWS: 0`

No AWS/R-tier tests were run.
