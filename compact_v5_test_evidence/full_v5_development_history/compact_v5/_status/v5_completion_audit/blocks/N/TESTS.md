# Block N Tests

Date: 2026-05-04

## Commands

```text
python -m py_compile compact_v5\MAIN\agent\core\parallel_dispatch.py compact_v5\MAIN\agent\core\query_engine.py compact_v5\MAIN\agent\core\__init__.py compact_v5\MAIN\agent\tools\registry.py compact_v5\MAIN\agent\tests\integration\test_block_n.py
```

Result: PASS.

Log: `compact_v5/_status/v5_completion_audit/logs/block-n-py-compile.log`

```text
python -m pytest compact_v5\MAIN\agent\tests\integration\test_block_n.py -q
```

Result: 25 passed.

Log: `compact_v5/_status/v5_completion_audit/logs/block-n-pytest.log`

```text
python -m pytest compact_v5\MAIN\agent\tests\integration\test_query_engine.py compact_v5\MAIN\agent\tests\integration\test_subagent.py compact_v5\MAIN\agent\tests\unit\test_registry.py -q
```

Result: 53 passed.

Log: `compact_v5/_status/v5_completion_audit/logs/block-n-regression.log`

No AWS/R-tier test was run.

```text
python compact_v5\_status\scripts\scope_audit.py --block N
python compact_v5\_status\scripts\scope_audit.py --block N --strict
```

Result: 19 expected rows, 19 ledger rows, 0 weak shipped evidence, 0
ship-blocking rows, verdict `READY_TO_REVIEW_CLOSE`.

Logs:

- `compact_v5/_status/v5_completion_audit/logs/block-n-scope-audit.log`
- `compact_v5/_status/v5_completion_audit/logs/block-n-scope-audit-strict.log`

## Iter2 Parallel Fast-Path Risk Resolution

User-requested risk: QueryEngine's new parallel dispatch path must not bypass
sequential dispatch bookkeeping for audit logging, repeat-call tracking, JSON
argument repair, or tool error/forensics.

Validation after refactor:

```text
python -m py_compile compact_v5\MAIN\agent\core\query_engine.py compact_v5\MAIN\agent\core\parallel_dispatch.py compact_v5\MAIN\agent\tests\integration\test_block_n.py
```

Result: PASS.

Log: `compact_v5/_status/v5_completion_audit/logs/block-n-py-compile-iter2.log`

```text
python -m pytest tests\integration\test_block_n.py -q
```

Result: 28 passed.

Log: `compact_v5/_status/v5_completion_audit/logs/block-n-pytest-iter2.log`

```text
python -m pytest tests\integration\test_query_engine.py tests\integration\test_subagent.py tests\unit\test_registry.py -q
```

Result: 53 passed.

Log: `compact_v5/_status/v5_completion_audit/logs/block-n-regression-iter2.log`

```text
python -m pytest tests\integration\test_query_engine.py tests\integration\test_block_c.py tests\integration\test_block_b.py -k "audit_log" -q
```

Result: 5 passed, 59 deselected.

Log:
`compact_v5/_status/v5_completion_audit/logs/block-n-dispatch-relevant-regression-iter2.log`

Additional broad dispatch-adjacent run:

```text
python -m pytest tests\integration\test_query_engine.py tests\integration\test_block_b.py tests\integration\test_block_c.py -q
```

Result: 61 passed, 1 skipped, 2 failed due absent local `boto3` dependency in
existing Block B non-mock count-token tests. No AWS/R-tier call was made.

Log:
`compact_v5/_status/v5_completion_audit/logs/block-n-dispatch-regression-iter2.log`

```text
python compact_v5\_status\scripts\scope_audit.py --block N
python compact_v5\_status\scripts\scope_audit.py --block N --strict
```

Result: 19 expected rows, 19 ledger rows, 0 weak shipped evidence, 0
ship-blocking rows, verdict `READY_TO_REVIEW_CLOSE`.

Logs:

- `compact_v5/_status/v5_completion_audit/logs/block-n-scope-audit-iter2.log`
- `compact_v5/_status/v5_completion_audit/logs/block-n-scope-audit-strict-iter2.log`
