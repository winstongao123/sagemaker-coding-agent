# Block J Tests

Date: 2026-05-05

## Zero-Cost Ship-Gate Tests

Command:

```powershell
Remove-Item Env:RUN_REAL_BEDROCK -ErrorAction SilentlyContinue
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_block_j_ship_gate.py -q
```

Result:

```text
5 passed, 3 skipped
```

The skipped tests are the real Bedrock smoke tests gated by
`RUN_REAL_BEDROCK=1`. They were intentionally not run under the no-AWS-spend
rule.

Log:

- `compact_v5/_status/v5_completion_audit/logs/block-j-tests.log`

## Compile

Command:

```powershell
py -3.11 -m py_compile compact_v5/MAIN/agent/tests/integration/test_block_j_ship_gate.py compact_v5/_rebuild_zip.py compact_v5/verify_ship_zip.py
```

Result: PASS

Log:

- `compact_v5/_status/v5_completion_audit/logs/block-j-py-compile.log`

## Scope Audit

Command:

```powershell
py -3.11 compact_v5/_status/scripts/scope_audit.py --block J --strict
```

Result:

```text
Expected rows: 0
Ledger rows: 0
Ship-blocking rows: NONE
Verdict: NO_SPEC_ROWS_FOUND
```

Log:

- `compact_v5/_status/v5_completion_audit/logs/block-j-scope-audit.log`
