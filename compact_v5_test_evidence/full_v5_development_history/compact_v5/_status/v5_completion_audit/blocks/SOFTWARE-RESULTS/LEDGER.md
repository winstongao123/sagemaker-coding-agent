# SOFTWARE-RESULTS Ledger

Status: READY_FOR_BLOCK_CLOSE_REVIEW
Date: 2026-05-05

Manual software-builder ledger:

| row_id | gap_id | requirement | implementation | code_evidence | test_evidence | doc_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|
| SOFTWARE-RESULTS-1 | DS3-S7, PS3-7 | Persist oversized single tool results before model-visible truncation. | `QueryEngine` keeps raw tool output until message assembly and `runtime.results.persist_large_tool_results()` stores results exceeding the tool max. | `core/query_engine.py`; `runtime/results.py` | `tests/integration/test_software_results.py::test_per_tool_large_result_persists_and_replays`; `logs/software-results-tests.log` | `blocks/SOFTWARE-RESULTS/DECISIONS.md` | SHIPPED | None. | APPROVED |
| SOFTWARE-RESULTS-2 | DS3-S7, PS3-7 | Persist aggregate over-budget tool-result messages before final budget clamp. | The tool-result message is scanned as a batch; when aggregate content exceeds the Bedrock message budget, each replaced result is persisted and receives a replay ref. | `core/query_engine.py`; `runtime/results.py` | `tests/integration/test_software_results.py::test_aggregate_tool_result_budget_persists_every_replaced_result`; `tests/integration/test_block_t.py::test_block_t_query_engine_enforces_tool_result_message_budget`; `logs/software-results-regression-tests.log` | `blocks/SOFTWARE-RESULTS/DECISIONS.md` | SHIPPED | None. | APPROVED |
| SOFTWARE-RESULTS-3 | DS3-S7, PS3-7 | Stable replay/reference surface for content replacements. | `result_replay` is a read-only/concurrency-safe tool that reads `sageagent-result://...` refs with offset/limit support. | `tools/result_replay.py`; `tools/__init__.py`; `tools/registry.py`; `runtime/results.py` | `tests/integration/test_software_results.py::test_result_replay_tool_registered_as_read_only`; `logs/software-results-tests.log` | `blocks/SOFTWARE-RESULTS/DECISIONS.md`; `OPTIMIZED_AWS_VALIDATION_PLAN.md` | SHIPPED | None. | APPROVED |

Manual ledger summary:

```text
EXPECTED_ROWS: 3
LEDGER_ROWS: 3
SHIPPED: 3
PARTIAL: 0
MISSING: 0
DEFERRED_USER_APPROVED: 0
DROPPED_USER_APPROVED: 0
N/A_CONSTRAINT: 0
SHIP_BLOCKING_ROWS: 0
```
