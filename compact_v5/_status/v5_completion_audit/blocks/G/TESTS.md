# Block G Tests

Status: PASS
Date: 2026-05-05

Focused validation already run during implementation:

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_block_g.py -q
```

Result: `25 passed`.

Full close validation:

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_block_g.py compact_v5/MAIN/agent/tests/integration/test_block_g2.py compact_v5/MAIN/agent/tests/integration/test_subagent.py -q
py -3.11 -m py_compile compact_v5/MAIN/agent/subagent/agent_memory.py compact_v5/MAIN/agent/subagent/agent_types.py compact_v5/MAIN/agent/subagent/spawn.py compact_v5/MAIN/agent/subagent/worktree.py compact_v5/MAIN/agent/subagent/fork.py compact_v5/MAIN/agent/tests/integration/test_block_g.py
py -3.11 compact_v5/_status/scripts/scope_audit.py --block G
```

Logs to save:

- `compact_v5/_status/v5_completion_audit/logs/block-g-tests.log`
- `compact_v5/_status/v5_completion_audit/logs/block-g-py-compile.log`
- `compact_v5/_status/v5_completion_audit/logs/block-g-scope-audit.log`

Results:

- Combined Block G/G2/subagent tests: `49 passed, 1 skipped`.
- py_compile: `PASS`.
- Scope audit: `READY_TO_REVIEW_CLOSE`, 8 shipped, 0 ship-blocking rows.

Coverage target:

- G-1/G-2 per-agent memory prompt and safe path check.
- G-3 one-shot subagent roles.
- G-4 coordinator slim prompt.
- G-5 shared iteration budget.
- G-6/G-7 subagent prompt wording and notes.
- G-8 fork cache-prefix replay helper evidence.
