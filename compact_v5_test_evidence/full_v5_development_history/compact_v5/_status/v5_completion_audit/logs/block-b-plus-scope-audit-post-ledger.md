# Block B+ Post-Ledger Scope Audit

Date: 2026-05-05

Command:

```powershell
py -3.11 compact_v5/_status/scripts/scope_audit.py --block B+
```

Result:

```text
=== Block B+ ===
Expected rows: 8
Ledger rows: 8
SHIPPED: 8  PARTIAL: 0  MISSING: 0  DEFERRED: 0  DROPPED: 0  N/A: 0
Ledger missing: 0  Weak shipped evidence: 0  Unknown disposition: 0
Ship-blocking rows: NONE
Verdict: READY_TO_REVIEW_CLOSE
```
