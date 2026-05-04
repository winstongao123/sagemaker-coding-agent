# Block T Baseline

Date: 2026-05-04

## Scope Baseline

Command:

```powershell
& 'C:\Users\winst\AppData\Local\Programs\Python\Python310\python.exe' compact_v5/_status/scripts/scope_audit.py --block T
```

Result before Block T artifact creation:

```text
Expected rows: 12
Ledger rows: 0
Ship-blocking rows: T-1, T-2, T-3, T-4, T-5, T-6, T-7, T-8, T-9, T-10, T-11, T-12
Verdict: LEDGER_INCOMPLETE
```

Log: `compact_v5/_status/v5_completion_audit/logs/block-t-baseline-scope-audit.log`.

