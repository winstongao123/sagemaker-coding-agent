=== Block B+ ===
Expected rows: 8
Ledger rows: 8
SHIPPED: 8  PARTIAL: 0  MISSING: 0  DEFERRED: 0  DROPPED: 0  N/A: 0
Ledger missing: 0  Weak shipped evidence: 0  Unknown disposition: 0
Ship-blocking rows: NONE
Verdict: READY_TO_REVIEW_CLOSE

| row_id | disposition | ship_blocking | evidence_problems | capability |
|---|---|---:|---|---|
| B+1 | SHIPPED | NO |  | Persist session cost + restore on resume (R11 N8, R7 CT-02..04) |
| B+2 | SHIPPED | NO |  | Canonical-name collapse for per-model usage (R11 N9) |
| B+3 | SHIPPED | NO |  | 4-line cost block format (R11 N10) |
| B+4 | SHIPPED | NO |  | Local OTel-style counters (cost/token by type) (R11 N11) |
| B+5 | SHIPPED | NO |  | Recursive advisor sub-cost accounting (R11 N12) |
| B+6 | SHIPPED | NO |  | contextWindow refresh on every cost update (R11 N13) |
| B+7 | SHIPPED | NO |  | Exit-time atexit cost flush (R11 N14) |
| B+8 | SHIPPED | NO |  | `Config` dataclass explicit PORT_LOG row (V1 lesser #9) |
