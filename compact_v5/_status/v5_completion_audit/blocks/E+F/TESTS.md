# Block E+F Tests

Date: 2026-05-04

## Commands

```text
py -3.11 -m py_compile compact_v5\MAIN\agent\core\query_engine.py compact_v5\MAIN\agent\runtime\config.py compact_v5\MAIN\agent\core\formatting.py compact_v5\MAIN\agent\tests\integration\test_block_e_f.py
```

Result: PASS.

Log: `compact_v5/_status/v5_completion_audit/logs/block-e-f-py-compile.log`

```text
py -3.11 -m pytest tests\integration\test_block_e_f.py -q
```

Run from: `compact_v5/MAIN/agent`

Result: 21 passed.

Log: `compact_v5/_status/v5_completion_audit/logs/block-e-f-pytest.log`

```text
py -3.11 -m pytest tests\integration\test_query_engine.py tests\integration\test_block_f2.py -q
```

Run from: `compact_v5/MAIN/agent`

Result: 34 passed.

Log: `compact_v5/_status/v5_completion_audit/logs/block-e-f-query-f2-regression.log`

```text
py -3.11 compact_v5\_status\scripts\scope_audit.py --block E+F
py -3.11 compact_v5\_status\scripts\scope_audit.py --block E+F --strict
```

Result: 8 expected rows, 8 ledger rows, no weak shipped evidence, no
ship-blocking rows, verdict `READY_TO_REVIEW_CLOSE`.

Logs:

- `compact_v5/_status/v5_completion_audit/logs/block-e-f-scope-audit.log`
- `compact_v5/_status/v5_completion_audit/logs/block-e-f-scope-audit-strict.log`

## Iter2 After Claude LOW-Finding Fixes

Claude iter1 approved Block E+F for close review but noted LOW robustness
findings for EF-3 signature-key breadth and EF-5 first-call-only callback
behavior. The worker fixed both and reran:

```text
py -3.11 -m py_compile compact_v5\MAIN\agent\core\query_engine.py compact_v5\MAIN\agent\runtime\config.py compact_v5\MAIN\agent\core\formatting.py compact_v5\MAIN\agent\tests\integration\test_block_e_f.py
```

Result: PASS.
Log: `compact_v5/_status/v5_completion_audit/logs/block-e-f-py-compile-iter2.log`

```text
py -3.11 -m pytest tests\integration\test_block_e_f.py -q
```

Result: 21 passed.
Log: `compact_v5/_status/v5_completion_audit/logs/block-e-f-pytest-iter2.log`

```text
py -3.11 -m pytest tests\integration\test_query_engine.py tests\integration\test_block_f2.py -q
```

Result: 34 passed.
Log: `compact_v5/_status/v5_completion_audit/logs/block-e-f-query-f2-regression-iter2.log`

```text
py -3.11 compact_v5\_status\scripts\scope_audit.py --block E+F
py -3.11 compact_v5\_status\scripts\scope_audit.py --block E+F --strict
```

Result: no ship-blocking rows, verdict `READY_TO_REVIEW_CLOSE`.
Logs:

- `compact_v5/_status/v5_completion_audit/logs/block-e-f-scope-audit-iter2.log`
- `compact_v5/_status/v5_completion_audit/logs/block-e-f-scope-audit-strict-iter2.log`

No AWS/R-tier test was run.

## Notes

The repo-root pytest invocation for `compact_v5\MAIN\agent\tests\integration\test_block_e_f.py`
failed during collection before Block E+F tests ran because package import
`compact_v5.MAIN.agent.__init__` imports top-level `core` before the test path
bootstrap executes. The passing invocation from `compact_v5/MAIN/agent` matches
the existing test suite import layout.
