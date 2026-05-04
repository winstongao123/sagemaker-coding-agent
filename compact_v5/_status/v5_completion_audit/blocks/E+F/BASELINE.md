# Block E+F Baseline

Date: 2026-05-04

## Initial Scope Audit

Command:

```powershell
py -3.11 compact_v5\_status\scripts\scope_audit.py --block E+F
```

Result:

```text
Expected rows: 8
Ledger rows: 0
SHIPPED: 0  PARTIAL: 0  MISSING: 0  DEFERRED: 0  DROPPED: 0  N/A: 0
Ledger missing: 8
Ship-blocking rows: EF-1, EF-2, EF-3, EF-4, EF-5, EF-6, EF-7, EF-8
Verdict: LEDGER_INCOMPLETE
```

## Git Baseline

Block A checkpoint is already pushed at:

```text
05f85f442c47c49f0bf1e6e34871b653e13ff7f3
```

Unrelated/pre-existing dirty files are present in the worktree and must not be
reverted or staged unless they become explicitly relevant to Block E+F.

## Canonical Rows

Source: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:199-206`

Rows: `EF-1` through `EF-8`.
