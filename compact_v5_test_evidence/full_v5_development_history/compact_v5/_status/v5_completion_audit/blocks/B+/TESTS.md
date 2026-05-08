# Block B+ Tests

Date: 2026-05-05

## Local Tests

```powershell
cd D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent
py -3.11 -m pytest tests/integration/test_block_b_plus.py -q
```

Result:

```text
29 passed in 0.62s
```

Python emitted a `RequestsDependencyWarning` about the local `urllib3` /
`chardet` / `charset_normalizer` versions. The test suite passed.

```powershell
cd D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent
py -3.11 -m pytest tests/integration/test_block_d.py -q
```

Result:

```text
22 passed in 0.56s
```

Python emitted the same `RequestsDependencyWarning`; the test suite passed.

```powershell
cd D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent
py -3.11 -m pytest tests/integration/test_block_a.py::test_advisor_cost_attributed_when_aux_model_set tests/integration/test_block_a.py::test_advisor_falls_back_to_parent_when_no_aux -q
```

Result:

```text
2 passed in 0.05s
```

The same `RequestsDependencyWarning` appeared. The targeted B+5 advisor tests
passed.

```powershell
cd D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent
py -3.11 -m py_compile commands.py ui/chat_ui.py tests/integration/test_block_b_plus.py tests/integration/test_block_d.py
```

Result: PASS, no output.

## Scope Audit

Before `LEDGER.md` existed:

```powershell
py -3.11 compact_v5/_status/scripts/scope_audit.py --block B+
```

Result:

```text
Expected rows: 8
Ledger rows: 0
Ship-blocking rows: B+1, B+2, B+3, B+4, B+5, B+6, B+7, B+8
Verdict: LEDGER_INCOMPLETE
```

Post-ledger audit:

```powershell
py -3.11 compact_v5/_status/scripts/scope_audit.py --block B+
```

Result:

```text
Expected rows: 8
Ledger rows: 8
SHIPPED: 8  PARTIAL: 0  MISSING: 0  DEFERRED: 0  DROPPED: 0  N/A: 0
Ship-blocking rows: NONE
Verdict: READY_TO_REVIEW_CLOSE
```
