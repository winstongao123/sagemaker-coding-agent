# Block 0 Tests

Date: 2026-05-05

## Focused Remap Suite

Command:

```powershell
$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest <focused Block 0 remap nodeids> -q
```

Coverage:

- `tests/integration/test_block0_shim.py`
- 0-2 / 0-4 / 0-6 tests from `tests/integration/test_block_e_f.py`
- 0-3 / 0-8 tests from `tests/integration/test_block_b.py`
- 0-7 / 0-9 tests from `tests/integration/test_block_b_plus.py`
- 0-5 / 0-10 tests from `tests/integration/test_block_c.py`

Result:

```text
30 passed
```

Log:

- `compact_v5/_status/v5_completion_audit/logs/block-0-tests.log`

## Compile

Command:

```powershell
py -3.11 -m py_compile compact_v5/MAIN/agent/prompt/__init__.py compact_v5/MAIN/agent/prompt/env_block.py compact_v5/MAIN/agent/runtime/bedrock_client.py compact_v5/MAIN/agent/runtime/env_validation.py compact_v5/MAIN/agent/runtime/cleanup_registry.py compact_v5/MAIN/agent/runtime/feature_flags.py compact_v5/MAIN/agent/security/scratchpad.py compact_v5/MAIN/agent/security/injection_scanner.py compact_v5/MAIN/agent/skills/manager.py
```

Result: PASS

Log:

- `compact_v5/_status/v5_completion_audit/logs/block-0-py-compile.log`

## Scope Audit

```powershell
py -3.11 compact_v5/_status/scripts/scope_audit.py --block 0 --strict
```

Result:

```text
Expected rows: 10
Ledger rows: 10
SHIPPED: 10
Ship-blocking rows: NONE
Verdict: READY_TO_REVIEW_CLOSE
```

Log:

- `compact_v5/_status/v5_completion_audit/logs/block-0-scope-audit.log`
