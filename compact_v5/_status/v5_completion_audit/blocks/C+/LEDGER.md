# Block C+ Ledger

Canonical source: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:115-123`

| row_id | capability | source | priority | fit | expected_target | code_evidence | test_evidence | port_log | adr | historical_review | git_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C+1 | `EnterPlanMode` + `ExitPlanModeV2` | SYNTHESIS_MASTER.md:119; Runnable EnterPlanModeTool/ExitPlanModeV2Tool | MED | NEEDS-ADAPTATION | `commands.py` `/phase` retained; formal tools dropped | `commands.py:476`; `commands.py:671` | `tests/integration/test_block_d.py:227` | #178 | ADR-024 | `reviews/block-c-plus-claude-review-iter1.md` | 90c359a76dbd59e34f95d34374ebe830e75a0b73 | DROPPED_USER_APPROVED | Checkpoint evidence recorded. | APPROVED_ITER1 |
| C+2 | File-history snapshot per-edit | SYNTHESIS_MASTER.md:120; Runnable FileEditTool.ts:431-440 | MED | CLEAN | `runtime/snapshot.py`; `tools/edit_file.py`; `tools/write_file.py` | `runtime/snapshot.py:19`; `runtime/snapshot.py:49`; `tools/edit_file.py:210`; `tools/write_file.py:106` | `tests/integration/test_block_b.py:122` | #179 | ADR-021; ADR-024 | `reviews/block-c-plus-claude-review-iter1.md` | 90c359a76dbd59e34f95d34374ebe830e75a0b73 | SHIPPED | Checkpoint evidence recorded. | APPROVED_ITER1 |
| C+3 | Cancellation/abort signal pattern via Python | SYNTHESIS_MASTER.md:121; Runnable utils/abortController.ts | HIGH | already covered | `runtime/execution_context.py`; `core/query_engine.py`; `tools/bash.py`; `tools/python_exec.py` | `runtime/execution_context.py:28`; `core/query_engine.py:1274`; `tools/bash.py:112`; `tools/python_exec.py:222` | `tests/integration/test_block_c.py:642` | #180 | ADR-049; ADR-024 | `reviews/block-c-plus-claude-review-iter1.md` | 90c359a76dbd59e34f95d34374ebe830e75a0b73 | SHIPPED | Checkpoint evidence recorded. | APPROVED_ITER1 |

EXPECTED_ROWS: 3
LEDGER_ROWS: 3
SHIPPED: 2
PARTIAL: 0
MISSING: 0
DEFERRED_USER_APPROVED: 0
DROPPED_USER_APPROVED: 1
N/A_CONSTRAINT: 0
SHIP_BLOCKING_ROWS: 0 verified by Claude iter1
