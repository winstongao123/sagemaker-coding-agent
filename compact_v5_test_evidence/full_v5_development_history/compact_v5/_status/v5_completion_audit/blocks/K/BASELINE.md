# Block K Baseline

Date: 2026-05-04

## Scope Baseline

Command:

```powershell
& 'C:\Users\winst\AppData\Local\Programs\Python\Python310\python.exe' compact_v5/_status/scripts/scope_audit.py --block K
```

Result before Block K artifact creation:

```text
Expected rows: 8
Ledger rows: 0
Ship-blocking rows: K-1, K-2, K-3, K-4, K-5, K-6, K-7, K-8
Verdict: LEDGER_INCOMPLETE
```

## Git Baseline

HEAD after Block N transition checkpoint:

```text
fd9be06 v5/audit: record block n close and start block k
```

Known unrelated dirty files remain outside Block K scope and must not be staged.

