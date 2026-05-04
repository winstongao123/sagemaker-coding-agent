# Block K Ledger

Status: READY_FOR_SCOPE_AUDIT
Date: 2026-05-04

Canonical scope: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:377-390`.

| row_id | capability | source | priority | fit | expected_target | code_evidence | test_evidence | port_log | adr | historical_review | git_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| K-1 | Audit-dir shape `<date>-<topic>/01-..._N.md + 00-SYNTHESIS.md` (L2 LF-DOC-6) | LF `docs/audits/`; `SYNTHESIS_MASTER.md:381`; retrofit note `SYNTHESIS_MASTER.md:709-710` | HIGH | CLEAN | `compact_v5/_phase_2/wave_5_deep/00-SYNTHESIS.md`; `compact_v5/docs/audits/README.md` | `compact_v5/_phase_2/wave_5_deep/00-SYNTHESIS.md:5`; `compact_v5/docs/audits/README.md:6-20` | `compact_v5/MAIN/agent/tests/integration/test_block_k_process.py:47` | PORT_LOG #115 | ADR-047 | `reviews/block-k-claude-review-iter1.md`; `reviews/block-k-claude-review-iter2.md` | pending Block K close checkpoint commit | SHIPPED | Close checkpoint in progress. | APPROVE_ITER3 |
| K-2 | PORT_LOG `evidence_tier` column (VERIFIED/LISTED) (L2 LF-DOC-8) | LF `docs/REUSABLE_MODULES.md`; `SYNTHESIS_MASTER.md:382` | HIGH | CLEAN | `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` | `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md:5`; Block K rows `:172-179` | `compact_v5/MAIN/agent/tests/integration/test_block_k_process.py:59` | PORT_LOG #116 | ADR-047 | `reviews/block-k-claude-review-iter1.md`; `reviews/block-k-claude-review-iter2.md` | pending Block K close checkpoint commit | SHIPPED | Close checkpoint in progress. | APPROVE_ITER3 |
| K-3 | CHANGELOG-as-postmortem entry shape (L2 LF-CHANGELOG-1) | LF `CHANGELOG.md`; `SYNTHESIS_MASTER.md:383` | MED | CLEAN | `compact_v5/CHANGELOG.md`; Block K changelog artifact | `compact_v5/CHANGELOG.md:3-21` | `compact_v5/MAIN/agent/tests/integration/test_block_k_process.py:89` | PORT_LOG #117 | ADR-047 | `reviews/block-k-claude-review-iter1.md`; `reviews/block-k-claude-review-iter2.md` | pending Block K close checkpoint commit | SHIPPED | Close checkpoint in progress. | APPROVE_ITER3 |
| K-4 | Pre-flight 5-category gate (L2 LF-DOC-2) | LF `docs/PREFLIGHT_PROTOCOL.md`; `SYNTHESIS_MASTER.md:384`; builder gate `SYNTHESIS_MASTER.md:714-726` | HIGH | CLEAN | `compact_v5/docs/PREFLIGHT_PROTOCOL.md` | `compact_v5/docs/PREFLIGHT_PROTOCOL.md:6-45` | `compact_v5/MAIN/agent/tests/integration/test_block_k_process.py:96` | PORT_LOG #118 | ADR-047 | `reviews/block-k-claude-review-iter1.md`; `reviews/block-k-claude-review-iter2.md` | pending Block K close checkpoint commit | SHIPPED | Close checkpoint in progress. | APPROVE_ITER3 |
| K-5 | Three-critic AXIS A/B/C (value/timing/cost) (L2 LF-DOC-5) | LF `docs/audits/2026-04-21-a-plus-review/`; `SYNTHESIS_MASTER.md:385` | MED | CLEAN | `compact_v5/docs/audits/THREE_CRITIC_REVIEW.md`; reviewer prompt requirements | `compact_v5/docs/audits/THREE_CRITIC_REVIEW.md:4-29` | `compact_v5/MAIN/agent/tests/integration/test_block_k_process.py:115` | PORT_LOG #119 | ADR-047 | `reviews/block-k-claude-review-iter1.md`; `reviews/block-k-claude-review-iter2.md` | pending Block K close checkpoint commit | SHIPPED | Close checkpoint in progress. | APPROVE_ITER3 |
| K-6 | A44 No-change-detector-tests policy (H5 A44) | Hermes `AGENTS.md:Test-policy`; `SYNTHESIS_MASTER.md:386`; A44 statement `SYNTHESIS_MASTER.md:521-531` | MUST | CLEAN | `AGENTS.md`; `compact_v5/MAIN/agent/tests/integration/test_block_k_process.py` | `AGENTS.md:69-80` | `compact_v5/MAIN/agent/tests/integration/test_block_k_process.py:138` | PORT_LOG #120 | ADR-047 | `reviews/block-k-claude-review-iter1.md`; `reviews/block-k-claude-review-iter2.md` | pending Block K close checkpoint commit | SHIPPED | Close checkpoint in progress. | APPROVE_ITER3 |
| K-7 | A39 No-wire-dead-code without E2E (H5 A39) | Hermes `AGENTS.md:Pitfall`; `SYNTHESIS_MASTER.md:387` | HIGH | CLEAN | `AGENTS.md`; Block K lock tests | `AGENTS.md:92-101` | `compact_v5/MAIN/agent/tests/integration/test_block_k_process.py:158` | PORT_LOG #121 | ADR-047 | `reviews/block-k-claude-review-iter1.md`; `reviews/block-k-claude-review-iter2.md` | pending Block K close checkpoint commit | SHIPPED | Close checkpoint in progress. | APPROVE_ITER3 |
| K-8 | A41 Hermetic test parity (H5 A41) | Hermes `AGENTS.md`; `SYNTHESIS_MASTER.md:388` | MED | CLEAN | `AGENTS.md`; Block K lock tests | `AGENTS.md:82-88` | `compact_v5/MAIN/agent/tests/integration/test_block_k_process.py:166` | PORT_LOG #122 | ADR-047 | `reviews/block-k-claude-review-iter1.md`; `reviews/block-k-claude-review-iter2.md` | pending Block K close checkpoint commit | SHIPPED | Close checkpoint in progress. | APPROVE_ITER3 |

EXPECTED_ROWS: 8
LEDGER_ROWS: 8
SHIPPED: 8
PARTIAL: 0
MISSING: 0
DEFERRED_USER_APPROVED: 0
DROPPED_USER_APPROVED: 0
N/A_CONSTRAINT: 0
SHIP_BLOCKING_ROWS: 0
