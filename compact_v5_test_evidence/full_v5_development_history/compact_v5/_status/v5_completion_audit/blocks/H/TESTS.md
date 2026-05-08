# Block H Tests

Date: 2026-05-05

## Focused Block H

Command:

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_block_h.py -q
```

Result:

```text
29 passed
```

Log:

- `compact_v5/_status/v5_completion_audit/logs/block-h-tests.log`

## Software-Builder Zero-Cost Readiness

Command:

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py compact_v5/MAIN/agent/tests/r_tier/test_software_project_workflow_contracts.py -q
```

Result:

```text
115 passed
```

This is zero-cost local readiness/spec coverage only. It does not approve or
run AWS/R-tier spend.

Log:

- `compact_v5/_status/v5_completion_audit/logs/block-h-software-builder-readiness.log`

## Compile

Command:

```powershell
py -3.11 -m py_compile compact_v5/MAIN/agent/memory/extract.py compact_v5/MAIN/agent/memory/session_memory.py compact_v5/MAIN/agent/memory/compact.py compact_v5/MAIN/agent/memory/context.py compact_v5/MAIN/agent/memory/__init__.py compact_v5/MAIN/agent/prompt/__init__.py compact_v5/MAIN/agent/agent.py
```

Result: PASS

Log:

- `compact_v5/_status/v5_completion_audit/logs/block-h-py-compile.log`

## Scope Audit

Command:

```powershell
py -3.11 compact_v5/_status/scripts/scope_audit.py --block H --strict
```

Result:

```text
Expected rows: 20
Ledger rows: 20
SHIPPED: 20
Ship-blocking rows: NONE
Verdict: READY_TO_REVIEW_CLOSE
```

Log:

- `compact_v5/_status/v5_completion_audit/logs/block-h-scope-audit.log`
