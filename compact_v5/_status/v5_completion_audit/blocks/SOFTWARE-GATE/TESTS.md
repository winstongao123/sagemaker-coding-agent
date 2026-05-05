# SOFTWARE-GATE Tests

Status: IMPLEMENTED_PENDING_CLAUDE_REVIEW
Date: 2026-05-05

Local zero-cost validation:

- `PYTHONPATH=compact_v5/MAIN/agent py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_software_gate.py -q` -> `4 passed`
- `PYTHONPATH=compact_v5/MAIN/agent py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_block_d.py -q` -> `31 passed`
- `py -3.11 -m py_compile compact_v5/MAIN/agent/runtime/gate.py compact_v5/MAIN/agent/commands.py compact_v5/MAIN/agent/tests/integration/test_software_gate.py` -> PASS
- `py -3.11 compact_v5/_status/scripts/scope_audit.py --all --summary` -> `TOTAL_SHIP_BLOCKING_ROWS: 0`
- `py -3.11 compact_v5/_status/scripts/scope_audit.py --all --strict` -> `TOTAL_SHIP_BLOCKING_ROWS: 0`

Log artifacts:

- `compact_v5/_status/v5_completion_audit/logs/software-gate-tests.log`
- `compact_v5/_status/v5_completion_audit/logs/software-gate-command-regression-tests.log`
- `compact_v5/_status/v5_completion_audit/logs/software-gate-py-compile.log`
- `compact_v5/_status/v5_completion_audit/logs/software-gate-scope-summary.log`
- `compact_v5/_status/v5_completion_audit/logs/software-gate-scope-strict.log`

Known non-blocking note:

- A first bare pytest invocation without `PYTHONPATH=compact_v5/MAIN/agent` failed during collection with the repo's known `ModuleNotFoundError: core` path issue. The focused suite passed when run with the established repo test path.
