# Block G2 Tests

Status: LOCAL_PASS

Commands run from repo root:

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_block_g2.py compact_v5/MAIN/agent/tests/integration/test_block_g.py compact_v5/MAIN/agent/tests/integration/test_subagent.py -q
```

Result:

```text
49 passed, 1 skipped
```

Saved log:

- `compact_v5/_status/v5_completion_audit/logs/block-g2-tests.log`

Software-builder zero-cost readiness suite:

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py compact_v5/MAIN/agent/tests/r_tier/test_software_project_workflow_contracts.py -q
```

Result:

```text
115 passed
```

Saved log:

- `compact_v5/_status/v5_completion_audit/logs/block-g2-software-builder-readiness.log`

Compile check:

```powershell
py -3.11 -m py_compile compact_v5/MAIN/agent/subagent/fork.py compact_v5/MAIN/agent/subagent/__init__.py
```

Result:

```text
py_compile PASS
```

Saved log:

- `compact_v5/_status/v5_completion_audit/logs/block-g2-py-compile.log`

Scope audit:

```powershell
py -3.11 compact_v5/_status/scripts/scope_audit.py --block G2
```

Result:

```text
READY_TO_REVIEW_CLOSE; ship-blocking rows: NONE
```

Saved log:

- `compact_v5/_status/v5_completion_audit/logs/block-g2-scope-audit.log`

Post-review close gates:

- Focused G/G2/subagent suite: `49 passed, 1 skipped`
  (`logs/block-g2-close-tests.log`)
- py_compile: `py_compile PASS`
  (`logs/block-g2-close-py-compile.log`)
- `scope_audit.py --block G2`: `READY_TO_REVIEW_CLOSE`, ship-blocking rows
  `NONE` (`logs/block-g2-close-scope-audit.log`)
- stale pending-review marker search: no matches.
