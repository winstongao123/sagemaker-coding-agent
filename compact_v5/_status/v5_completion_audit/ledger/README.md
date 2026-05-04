# Master Ledger Outputs

This folder is for cross-block generated ledgers and summaries.

Expected files:

| File | Purpose |
|---|---|
| `MASTER_SCOPE_LEDGER.md` | All canonical rows across all blocks. |
| `MASTER_STATUS_SUMMARY.md` | Counts by block and disposition. |
| `SHIP_BLOCKERS.md` | Current ship-blocking rows only. |

Do not mark v5.0.1 F5-ready until `SHIP_BLOCKERS.md` is empty or every item
has explicit user-approved drop/defer status.
