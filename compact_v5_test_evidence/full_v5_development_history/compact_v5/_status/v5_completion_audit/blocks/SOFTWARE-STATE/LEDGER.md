# SOFTWARE-STATE Ledger

Status: CLOSED_PUSHED
Date: 2026-05-05

Canonical source: `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` DS3-S1,
DS3-S2, DS3-S3, DS3-S11 and `PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md`
PS3-1 through PS3-3.

Manual software-builder ledger:

| row_id | gap_id | requirement | implementation | code_evidence | test_evidence | doc_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|
| SOFTWARE-STATE-1 | DS3-S1, PS3-2 | Todos/work ledger must be durable, not process-only. | `todo_write` mirrors normalized todos to workspace `.sageagent_state/todos.json`; `todo_read` restores from disk after in-memory reset. | `runtime/state.py:130`; `runtime/state.py:141`; `tools/todo.py:63`; `tools/todo.py:69`; `tools/todo.py:76`; `tools/todo.py:85` | `tests/integration/test_software_state.py::test_todos_persist_across_memory_reset` | `blocks/SOFTWARE-STATE/DECISIONS.md` | SHIPPED | None. | APPROVED |
| SOFTWARE-STATE-2 | DS3-S2, PS3-1 | `/save` and `/resume` must preserve more than messages/token stats. | `/save` stores messages, token stats, durable todos, capped status/memory context, and recovery paths; `/resume` restores messages, token stats, and todos. | `commands.py:329`; `commands.py:337`; `commands.py:342`; `commands.py:344`; `commands.py:364`; `commands.py:377`; `runtime/session.py` existing `Session.todos` schema | `tests/integration/test_software_state.py::test_save_resume_round_trip_includes_todos_status_memory`; B+ regression log | `blocks/SOFTWARE-STATE/DECISIONS.md` | SHIPPED | Named checkpoint index remains in `SOFTWARE-CHECKPOINT`. | APPROVED |
| SOFTWARE-STATE-3 | DS3-S2, PS3-1 | Crash-safe per-turn journal and auto-restore metadata must exist. | `Agent.run()` appends `turn_start` and `turn_finish` journal rows and atomically writes `last_turn.json` with messages, todos, token stats, status/memory context, and result summary. | `runtime/state.py:151`; `runtime/state.py:168`; `agent.py:209`; `agent.py:237`; `agent.py:248` | `tests/integration/test_software_state.py::test_agent_refreshes_status_and_memory_every_run` | `blocks/SOFTWARE-STATE/DECISIONS.md` | SHIPPED | Automatic UI resume prompt remains future UI polish; durable data is present locally. | APPROVED |
| SOFTWARE-STATE-4 | DS3-S3, DS3-S11, PS3-3 | Top-level turns must refresh status and memory context. | `Agent.run()` reads current `AGENT_STATUS.md` and `memory.md` every top-level turn and permits the dynamic prompt update for that fresh state. | `agent.py:60`; `agent.py:80`; `agent.py:169`; `agent.py:230`; `runtime/state.py:110` | `tests/integration/test_software_state.py::test_agent_refreshes_status_and_memory_every_run`; B+ status regression log | `blocks/SOFTWARE-STATE/DECISIONS.md` | SHIPPED | None. | APPROVED |
| SOFTWARE-STATE-5 | DS3-S11 | Memory extraction path must be wired without AWS/R-tier spend. | `/save` calls an opt-in zero-cost memory extraction path only when `CONFIG.enable_memory_extraction=True`; tests inject a local extractor function. | `commands.py:337`; `commands.py:410`; `memory/extract.py` existing extractor core | `tests/integration/test_software_state.py::test_save_can_run_zero_cost_memory_extraction_path` | `blocks/SOFTWARE-STATE/DECISIONS.md` | SHIPPED | Real LLM extraction proof remains R-tier/AWS gated. | APPROVED |

Manual ledger summary:

```text
EXPECTED_ROWS: 5
LEDGER_ROWS: 5
SHIPPED: 5
PARTIAL: 0
MISSING: 0
DEFERRED_USER_APPROVED: 0
DROPPED_USER_APPROVED: 0
N/A_CONSTRAINT: 0
SHIP_BLOCKING_ROWS: 0
```
