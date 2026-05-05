# Block F2 Ledger

Canonical source: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:392-398`

| row_id | capability | source | priority | fit | expected_target | code_evidence | test_evidence | port_log | adr | historical_review | git_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F2-1 | TokenBudget auto-continuation (R7 N4) | SYNTHESIS_MASTER.md:396; Runnable query/tokenBudget.ts:1-93 + query.ts:1308-1355 | HIGH | NEEDS-ADAPTATION | Parent query loop auto-continues under an explicit iteration budget when usage is under 90 percent, not diminishing, not a subagent, and not over cost cap. | `core/budget_continuation.py:82`; `core/query_engine.py:862`; `runtime/config.py:141` | `tests/integration/test_block_f2.py:40`; `tests/integration/test_block_f2.py:220`; `tests/integration/test_block_f2.py:424`; `tests/integration/test_block_f2.py:649`; logs `block-f2-tests.log`, `block-f2-software-readiness.log`, `block-f2-scope-audit.log` | #072 | ADR-028 | `reviews/block-f2-claude-review-iter1.md` | pending close commit | SHIPPED | Checkpoint evidence pending after close commit. | APPROVED_ITER1 |

EXPECTED_ROWS: 1
LEDGER_ROWS: 1
SHIPPED: 1
PARTIAL: 0
MISSING: 0
DEFERRED_USER_APPROVED: 0
DROPPED_USER_APPROVED: 0
N/A_CONSTRAINT: 0
SHIP_BLOCKING_ROWS: 0 verified by Claude iter1
