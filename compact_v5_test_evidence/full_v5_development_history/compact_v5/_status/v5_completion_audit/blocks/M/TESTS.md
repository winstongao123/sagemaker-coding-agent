# Block M Tests

Date: 2026-05-05

## Existing Block M Regression Tests

Command:

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_block_m.py -q
```

Result:

```text
11 passed
```

Log:

- `compact_v5/_status/v5_completion_audit/logs/block-m-tests.log`

## Compile

Command:

```powershell
py -3.11 -m py_compile compact_v5/MAIN/agent/core/query_engine.py compact_v5/MAIN/agent/skills/manager.py
```

Result: PASS

Log:

- `compact_v5/_status/v5_completion_audit/logs/block-m-py-compile.log`

## Scope Audit

Command:

```powershell
py -3.11 compact_v5/_status/scripts/scope_audit.py --block M --strict
```

Result:

```text
Expected rows: 0
Ledger rows: 0
Ship-blocking rows: NONE
Verdict: NO_SPEC_ROWS_FOUND
```

Log:

- `compact_v5/_status/v5_completion_audit/logs/block-m-scope-audit.log`
