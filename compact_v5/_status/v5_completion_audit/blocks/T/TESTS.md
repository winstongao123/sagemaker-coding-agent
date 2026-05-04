# Block T Tests

Status: NOT_RUN_FOR_CURRENT_REDO
Date: 2026-05-04

Existing candidate suite:

`compact_v5/MAIN/agent/tests/integration/test_block_t.py`

Planned gates:

1. `python -m py_compile compact_v5/MAIN/agent/tests/integration/test_block_t.py`
2. `cd compact_v5/MAIN/agent && python -m pytest tests/integration/test_block_t.py -q`
3. Additional focused tests for new T-6/T-7/T-8/T-10/T-11/T-12 helpers as needed.
4. `python compact_v5/_status/scripts/scope_audit.py --block T`
5. `python compact_v5/_status/scripts/scope_audit.py --block T --strict`

Scope logs:

- Baseline before ledger init: `logs/block-t-baseline-scope-audit.log`.
- After ledger init: `logs/block-t-scope-audit-after-ledger-init.log` (12 ledger rows, 12 blocking).
