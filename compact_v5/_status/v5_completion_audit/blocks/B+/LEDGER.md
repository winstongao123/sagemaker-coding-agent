# Block B+ Ledger

Canonical source: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:74-87`

| row_id | capability | source | priority | fit | expected_target | code_evidence | test_evidence | port_log | adr | historical_review | git_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B+1 | Persist session cost + restore on resume (R11 N8, R7 CT-02..04) | SYNTHESIS_MASTER.md:78; Runnable cost-tracker.ts:87-175 | HIGH | CLEAN | `runtime/session.py`; `runtime/tokens.py`; `commands.py`; `ui/chat_ui.py` | `runtime/session.py:100`; `runtime/tokens.py:649`; `commands.py:308`; `commands.py:323`; `ui/chat_ui.py:114`; `ui/chat_ui.py:232` | `tests/integration/test_block_b_plus.py:91`; `tests/integration/test_block_b_plus.py:127`; `tests/integration/test_block_b_plus.py:156` | #170 | ADR-051 | `reviews/block-b-plus-claude-review-iter7.md` | pending Block B+ checkpoint | SHIPPED | Replace pending checkpoint with actual B+ commit SHA after commit/push. | APPROVED_ITER7 |
| B+2 | Canonical-name collapse for per-model usage (R11 N9) | SYNTHESIS_MASTER.md:79; Runnable cost-tracker.ts:181-226 | MED | CLEAN | `runtime/tokens.py` | `runtime/tokens.py:488`; `runtime/tokens.py:559` | `tests/integration/test_block_b_plus.py:198` | #171 | ADR-051 | `reviews/block-b-plus-claude-review-iter7.md` | pending Block B+ checkpoint | SHIPPED | Replace pending checkpoint with actual B+ commit SHA after commit/push. | APPROVED_ITER7 |
| B+3 | 4-line cost block format (R11 N10) | SYNTHESIS_MASTER.md:80; Runnable cost-tracker.ts:228-244 | MED | CLEAN | `runtime/tokens.py`; `commands.py` | `runtime/tokens.py:567`; `commands.py:355` | `tests/integration/test_block_b_plus.py:214` | #172 | ADR-051 | `reviews/block-b-plus-claude-review-iter7.md` | pending Block B+ checkpoint | SHIPPED | Replace pending checkpoint with actual B+ commit SHA after commit/push. | APPROVED_ITER7 |
| B+4 | Local OTel-style counters (cost/token by type) (R11 N11) | SYNTHESIS_MASTER.md:81; Runnable cost-tracker.ts:289-301 | MED | NEEDS-ADAPTATION | `runtime/tokens.py` | `runtime/tokens.py:596` | `tests/integration/test_block_b_plus.py:251` | #173 | ADR-051 | `reviews/block-b-plus-claude-review-iter7.md` | pending Block B+ checkpoint | SHIPPED | Replace pending checkpoint with actual B+ commit SHA after commit/push. | APPROVED_ITER7 |
| B+5 | Recursive advisor sub-cost accounting (R11 N12) | SYNTHESIS_MASTER.md:82; Runnable cost-tracker.ts:304-322 | HIGH | CLEAN | `core/compactor.py`; `runtime/tokens.py` | `core/compactor.py:882`; `core/compactor.py:887` | `tests/integration/test_block_a.py:788`; `tests/integration/test_block_a.py:830` | #174 | ADR-051 | `reviews/block-b-plus-claude-review-iter7.md` | pending Block B+ checkpoint | SHIPPED | Replace pending checkpoint with actual B+ commit SHA after commit/push. | APPROVED_ITER7 |
| B+6 | contextWindow refresh on every cost update (R11 N13) | SYNTHESIS_MASTER.md:83; Runnable cost-tracker.ts:273-274 | LOW | CLEAN | `runtime/tokens.py` | `runtime/tokens.py:505`; `runtime/tokens.py:607` | `tests/integration/test_block_b_plus.py:279` | #175 | ADR-051 | `reviews/block-b-plus-claude-review-iter7.md` | pending Block B+ checkpoint | SHIPPED | Replace pending checkpoint with actual B+ commit SHA after commit/push. | APPROVED_ITER7 |
| B+7 | Exit-time atexit cost flush (R11 N14) | SYNTHESIS_MASTER.md:84; Runnable costHook.ts:6-22 | HIGH | CLEAN | `runtime/tokens.py`; `runtime/cleanup_registry.py` | `runtime/tokens.py:739`; `runtime/tokens.py:750` | `tests/integration/test_block_b_plus.py:575` | #176 | ADR-051 | `reviews/block-b-plus-claude-review-iter7.md` | pending Block B+ checkpoint | SHIPPED | Replace pending checkpoint with actual B+ commit SHA after commit/push. | APPROVED_ITER7 |
| B+8 | `Config` dataclass explicit PORT_LOG row (V1 lesser #9) | SYNTHESIS_MASTER.md:85; v4 sagemaker_agent.py:1018-1149 | MUST | FALSE-POSITIVE | `runtime/config.py` | `runtime/config.py:28`; `runtime/config.py:90`; `runtime/config.py:105`; `runtime/config.py:121` | `tests/integration/test_block_b_plus.py:831` | #177 | ADR-051 | `reviews/block-b-plus-claude-review-iter7.md` | pending Block B+ checkpoint | SHIPPED | Replace pending checkpoint with actual B+ commit SHA after commit/push. | APPROVED_ITER7 |

EXPECTED_ROWS: 8
LEDGER_ROWS: 8
SHIPPED: 8
PARTIAL: 0
MISSING: 0
DEFERRED_USER_APPROVED: 0
DROPPED_USER_APPROVED: 0
N/A_CONSTRAINT: 0
SHIP_BLOCKING_ROWS: 0 verified by Claude iter7
