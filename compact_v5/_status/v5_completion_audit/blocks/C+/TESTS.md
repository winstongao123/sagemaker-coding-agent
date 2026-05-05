# Block C+ Tests

Date: 2026-05-05

## Local Tests

```powershell
cd D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent
py -3.11 -m pytest tests/integration/test_block_c_plus.py -q
```

Result:

```text
17 passed in 2.91s
```

Python emitted a `RequestsDependencyWarning` about the local `urllib3` /
`chardet` / `charset_normalizer` versions. The test suite passed.

```powershell
cd D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent
py -3.11 -m pytest tests/integration/test_block_b.py::test_snapshot_manager_creates_backup tests/integration/test_block_c.py::test_abort_context_reaches_query_engine_bash_and_python_exec -q
```

Result:

```text
2 passed in 0.51s
```

The same `RequestsDependencyWarning` appeared. The targeted C+2/C+3 tests
passed.

```powershell
cd D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent
py -3.11 -m py_compile ui/approval_dialog.py core/query_engine.py tools/write_file.py tools/edit_file.py runtime/snapshot.py runtime/execution_context.py tools/bash.py tools/python_exec.py tests/integration/test_block_c_plus.py tests/integration/test_block_b.py tests/integration/test_block_c.py
```

Result: PASS, no output.
