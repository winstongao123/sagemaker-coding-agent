# Block G3 Tests

Status: LOCAL_PASS

Focused G3 suite:

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_block_g3.py -q
```

Result:

```text
15 passed, 1 skipped
```

Saved log:

- `compact_v5/_status/v5_completion_audit/logs/block-g3-tests.log`

Compile check:

```powershell
py -3.11 -m py_compile compact_v5/MAIN/agent/coordinator/system_prompt.py compact_v5/MAIN/agent/coordinator/user_context.py compact_v5/MAIN/agent/coordinator/__init__.py compact_v5/MAIN/agent/core/query_engine.py compact_v5/MAIN/agent/runtime/config.py
```

Result:

```text
py_compile PASS
```

Saved log:

- `compact_v5/_status/v5_completion_audit/logs/block-g3-py-compile.log`

AWS/R-tier:

- Not run.
- `test_coordinator_prompt_real_haiku_orchestration` remains skipped unless
  `RUN_REAL_BEDROCK` is explicitly approved.

Scope audit:

```powershell
py -3.11 compact_v5/_status/scripts/scope_audit.py --block G3
```

Result:

```text
READY_TO_REVIEW_CLOSE; ship-blocking rows: NONE
```

Saved log:

- `compact_v5/_status/v5_completion_audit/logs/block-g3-scope-audit.log`

Post-review close gates after LOW fixes:

- Focused G3 suite: `15 passed, 1 skipped`
  (`logs/block-g3-close-tests.log`)
- py_compile: `py_compile PASS`
  (`logs/block-g3-close-py-compile.log`)
- `scope_audit.py --block G3`: `READY_TO_REVIEW_CLOSE`, ship-blocking rows
  `NONE` (`logs/block-g3-close-scope-audit.log`)
- G3-specific stale marker search: no matches for pending review markers or
  stale `test_block_g3` count text.
