# Block F2 Tests

Status: PASS
Date: 2026-05-05

Zero-cost local validation:

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_block_f2.py -q
```

Result: `20 passed`.

Log: `compact_v5/_status/v5_completion_audit/logs/block-f2-tests.log`

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m py_compile compact_v5/MAIN/agent/core/budget_continuation.py compact_v5/MAIN/agent/core/query_engine.py compact_v5/MAIN/agent/runtime/config.py compact_v5/MAIN/agent/tests/integration/test_block_f2.py
```

Result: `PASS`.

Log: `compact_v5/_status/v5_completion_audit/logs/block-f2-py-compile.log`

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
python -m pytest compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py compact_v5/MAIN/agent/tests/r_tier/test_software_project_workflow_contracts.py -q
```

Result: failed before collection because bare `python` resolved to `C:\Users\winst\AppData\Local\Programs\Swift\Python-3.10.1\usr\bin\python.exe`, which has no pytest installed.

Valid rerun:

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py compact_v5/MAIN/agent/tests/r_tier/test_software_project_workflow_contracts.py -q
```

Result: `114 passed`.

Log: `compact_v5/_status/v5_completion_audit/logs/block-f2-software-readiness.log`

```powershell
py -3.11 compact_v5/_status/scripts/scope_audit.py --block F2
```

Result: `READY_TO_REVIEW_CLOSE`, 1 shipped, 0 ship-blocking rows.

Log: `compact_v5/_status/v5_completion_audit/logs/block-f2-scope-audit.log`

Coverage target:

- F2-1 pure decision behavior under 90 percent.
- Stop at or above 90 percent.
- Cost-cap halt priority.
- Default-off opt-in behavior.
- Parent-only continuation; no subagent continuation.
- Diminishing-return halt.
- StopDecision telemetry/audit logging.
- Best-effort warning when the F2 path raises.
- Fresh `BudgetTracker` per `QueryEngine.run()`.
- Software-project readiness remains command-consolidated and zero-cost before AWS.
