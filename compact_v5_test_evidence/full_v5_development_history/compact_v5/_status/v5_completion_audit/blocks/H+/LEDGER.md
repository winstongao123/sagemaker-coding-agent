# Block H+ Ledger

Canonical source: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:286-292`

| row_id | capability | source | priority | fit | expected_target | code_evidence | test_evidence | port_log | adr | historical_review | git_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H+1 | autoDream consolidation engine - MANUAL-TRIGGER ONLY | SYNTHESIS_MASTER.md:290; Runnable services/autoDream/* | HIGH | NEEDS-ADAPTATION | Manual-only `/dream` consolidation engine with 4-phase prompt, file lock, backup/rollback, dry-run path, no daemon/auto-fire/env auto-enable, and UI invocation through `/dream`. | `runtime/dream.py:47`; `runtime/dream.py:94`; `runtime/dream.py:252`; `runtime/dream.py:358`; `commands.py:643`; `commands.py:651`; `ui/chat_ui.py:27`; `ui/chat_ui.py:120`; `ui/chat_ui.py:237` | `tests/integration/test_block_h_plus.py:33`; `tests/integration/test_block_h_plus.py:55`; `tests/integration/test_block_h_plus.py:91`; `tests/integration/test_block_h_plus.py:127`; `tests/integration/test_block_h_plus.py:188`; `tests/integration/test_block_h_plus.py:206`; `tests/integration/test_block_h_plus.py:222`; `tests/integration/test_block_h_plus.py:240`; `tests/integration/test_block_h_plus.py:259`; `tests/integration/test_block_h_plus.py:331`; `tests/integration/test_block_h_plus.py:352`; `tests/integration/test_block_h_plus.py:388`; `logs/block-h-plus-tests.log` | #099; #191 | ADR-035; ADR-052 | `reviews/block-h-plus-claude-review-iter1.md` APPROVE | f2e5a35fe9512a011f5c5eaf99ba5aad7b6045e8 | SHIPPED | None pending Claude review. | APPROVE |


