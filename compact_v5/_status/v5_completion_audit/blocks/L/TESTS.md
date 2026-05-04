# Block L Tests

Date: 2026-05-04

## Commands

```text
python -m py_compile compact_v5\MAIN\agent\core\errors.py compact_v5\MAIN\agent\core\retry.py compact_v5\MAIN\agent\core\cache_break_detection.py compact_v5\MAIN\agent\core\__init__.py compact_v5\MAIN\agent\runtime\bedrock_client.py compact_v5\MAIN\agent\runtime\config.py compact_v5\MAIN\agent\tests\integration\test_block_l.py
```

Result: PASS.

Log: `compact_v5/_status/v5_completion_audit/logs/block-l-py-compile.log`

Note: `py -3.11` failed before executing because the local Windows launcher
points at a broken Store Python app execution alias. The available local
interpreter is `C:\Users\winst\AppData\Local\Programs\Python\Python310\python.exe`;
it compiled all touched Python files successfully.

```text
python -m pytest compact_v5\MAIN\agent\tests\integration\test_block_l.py -q
```

Run from repo root with `PYTHONPATH=compact_v5/MAIN/agent`.

Result: 40 passed.

Log: `compact_v5/_status/v5_completion_audit/logs/block-l-pytest.log`

No AWS/R-tier test was run.

```text
python compact_v5\_status\scripts\scope_audit.py --block L
python compact_v5\_status\scripts\scope_audit.py --block L --strict
```

Result: 28 expected rows, 28 ledger rows, 0 weak shipped evidence, 0
ship-blocking rows, verdict `READY_TO_REVIEW_CLOSE`.

Logs:

- `compact_v5/_status/v5_completion_audit/logs/block-l-scope-audit-final.log`
- `compact_v5/_status/v5_completion_audit/logs/block-l-scope-audit-strict-final.log`
