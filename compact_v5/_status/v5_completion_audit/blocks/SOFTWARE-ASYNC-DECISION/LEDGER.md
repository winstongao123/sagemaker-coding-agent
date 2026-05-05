# SOFTWARE-ASYNC-DECISION Ledger

Status: CLOSED_PUSHED
Date: 2026-05-05

Canonical source: `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` DS3-S6 and
`PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md` software-builder block
table.

Manual software-builder ledger:

| row_id | gap_id | requirement | decision | code_evidence | test_evidence | doc_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|
| SOFTWARE-ASYNC-DECISION-1 | DS3-S6 | Decide true async/background subagent scope for v5.0.1. | True async/background subagents are post-v5.0.1; v5.0.1 must not claim pollable/background child workers. | `tools/task.py:158` marks task not concurrency-safe; `tools/task.py` description says subagents run to completion. | `tests/integration/test_software_async_decision.py::test_task_tool_declares_sync_one_shot_no_background_contract` | `blocks/SOFTWARE-ASYNC-DECISION/DECISIONS.md` | SHIPPED | None; decision block only. | APPROVED |
| SOFTWARE-ASYNC-DECISION-2 | DS3-S6, DS3-S5 | Preserve strengthened synchronous supervision path. | Sync supervision hardening is required in later blocks: `SOFTWARE-SUBAGENT` for structured envelopes and `SOFTWARE-GATE` for enforced completion gates. | `coordinator/__init__.py` documents no async channel and sync-to-completion adaptation. | `tests/integration/test_software_async_decision.py::test_coordinator_docs_state_async_channel_is_not_in_v5` | `BLOCK_ORDER_AND_COVERAGE.md`; `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md:164-166` | SHIPPED | Continue to later software blocks for implementation evidence. | APPROVED |
| SOFTWARE-ASYNC-DECISION-3 | DS3-S6 | Avoid silent drift or false async UX. | No `task` input schema fields expose `background`, `job_id`, `poll`, `wait`, `kill`, or `async`. | `tools/task.py:62-86` input schema only supports description, prompt, and subagent_type. | `tests/integration/test_software_async_decision.py::test_task_tool_declares_sync_one_shot_no_background_contract` | `blocks/SOFTWARE-ASYNC-DECISION/DECISIONS.md` | SHIPPED | None. | APPROVED |

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
