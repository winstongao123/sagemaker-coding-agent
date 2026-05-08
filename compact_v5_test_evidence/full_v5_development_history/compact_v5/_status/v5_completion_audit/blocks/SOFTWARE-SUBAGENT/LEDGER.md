# SOFTWARE-SUBAGENT Ledger

Status: READY_FOR_BLOCK_CLOSE_REVIEW
Date: 2026-05-05

Manual software-builder ledger:

| row_id | gap_id | requirement | implementation | code_evidence | test_evidence | doc_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|
| SOFTWARE-SUBAGENT-1 | DS3-S5, PS3-4 | Subagent and reviewer calls must return a structured result envelope. | `SubagentResult.to_envelope()` returns schema `sageagent.subagent_result.v1`; `task` appends it under `[subagent_result_envelope]`. | `subagent/spawn.py`; `tools/task.py` | `tests/integration/test_software_subagent.py::test_task_tool_returns_structured_subagent_envelope`; `logs/software-subagent-tests.log` | `blocks/SOFTWARE-SUBAGENT/DECISIONS.md` | SHIPPED | None. | APPROVED |
| SOFTWARE-SUBAGENT-2 | DS3-S5 | Envelope includes supervision metadata: child session, role, stop reason, duration, heartbeat, timeout/timed-out, files changed, summary, and recovery hint. | Direct spawn records duration, heartbeat count/timestamp, child session, stop reason, files changed from child tool-use transcript, bounded summary, and recovery hint for budget/max-turn/parent mutation/error paths. | `subagent/spawn.py` | `tests/integration/test_software_subagent.py::test_spawn_subagent_result_envelope_has_tokens_files_and_heartbeat`; `tests/integration/test_software_subagent.py::test_budget_exhausted_task_tool_includes_recovery_envelope`; `logs/software-subagent-tests.log` | `blocks/SOFTWARE-SUBAGENT/DECISIONS.md` | SHIPPED | None. | APPROVED |
| SOFTWARE-SUBAGENT-3 | PS3-6 | Envelope includes child token, cost, and cache attribution where available. | Spawn snapshots `runtime.tokens.TOKENS.get_stats()` before and after the child and computes per-agent child deltas for input/output/cache/cost. | `subagent/spawn.py`; `runtime/tokens.py` | `tests/integration/test_software_subagent.py::test_spawn_subagent_result_envelope_has_tokens_files_and_heartbeat`; `tests/integration/test_subagent.py::test_task_tool_executor_spawns_subagent`; `logs/software-subagent-regression-tests.log` | `blocks/SOFTWARE-SUBAGENT/DECISIONS.md` | SHIPPED | None. | APPROVED |
| SOFTWARE-SUBAGENT-4 | DS3-S5, PS3-4 | Parent recovery behavior must be testable when a child stops early or cannot run. | Budget/max-turn results surface partial output plus structured envelope; invalid/depth cases carry recovery hints; parent-context mutation recovery remains explicit. | `subagent/spawn.py`; `tools/task.py` | `tests/integration/test_software_subagent.py::test_budget_exhausted_task_tool_includes_recovery_envelope`; `tests/integration/test_subagent.py::test_task_tool_surfaces_budget_exhaustion`; `logs/software-subagent-regression-tests.log` | `blocks/SOFTWARE-SUBAGENT/DECISIONS.md` | SHIPPED | None. | APPROVED |

Manual ledger summary:

```text
EXPECTED_ROWS: 4
LEDGER_ROWS: 4
SHIPPED: 4
PARTIAL: 0
MISSING: 0
DEFERRED_USER_APPROVED: 0
DROPPED_USER_APPROVED: 0
N/A_CONSTRAINT: 0
SHIP_BLOCKING_ROWS: 0
```
