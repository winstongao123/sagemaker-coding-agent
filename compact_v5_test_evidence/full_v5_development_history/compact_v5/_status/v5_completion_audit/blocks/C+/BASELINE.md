# Block C+ Baseline

Date: 2026-05-05

Initial `scope_audit.py --block C+` before this block ledger existed:

```text
Expected rows: 3
Ledger rows: 0
Ship-blocking rows: C+1, C+2, C+3
Verdict: LEDGER_INCOMPLETE
```

Post-ledger local audit:

```text
Expected rows: 3
Ledger rows: 3
SHIPPED: 2  PARTIAL: 0  MISSING: 0  DEFERRED: 0  DROPPED: 1  N/A: 0
Ship-blocking rows: NONE
Verdict: READY_TO_REVIEW_CLOSE
```
