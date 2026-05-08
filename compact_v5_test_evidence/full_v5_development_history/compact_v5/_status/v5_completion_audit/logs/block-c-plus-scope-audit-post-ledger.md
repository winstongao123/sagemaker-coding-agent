=== Block C+ ===
Expected rows: 3
Ledger rows: 3
SHIPPED: 2  PARTIAL: 0  MISSING: 0  DEFERRED: 0  DROPPED: 1  N/A: 0
Ledger missing: 0  Weak shipped evidence: 0  Unknown disposition: 0
Ship-blocking rows: NONE
Verdict: READY_TO_REVIEW_CLOSE

| row_id | disposition | ship_blocking | evidence_problems | capability |
|---|---|---:|---|---|
| C+1 | DROPPED_USER_APPROVED | NO |  | `EnterPlanMode` + `ExitPlanModeV2` (R1 #84-91, #97-104) |
| C+2 | SHIPPED | NO |  | File-history snapshot per-edit (R1 #127) |
| C+3 | SHIPPED | NO |  | Cancellation/abort signal pattern via Python (paired with C-17) |
