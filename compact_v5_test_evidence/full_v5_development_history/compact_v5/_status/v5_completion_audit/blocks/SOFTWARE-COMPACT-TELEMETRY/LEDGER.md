# SOFTWARE-COMPACT-TELEMETRY Ledger

Status: READY_FOR_BLOCK_CLOSE_REVIEW
Date: 2026-05-05

Manual software-builder ledger:

| row_id | gap_id | requirement | implementation | code_evidence | test_evidence | doc_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|
| SOFTWARE-COMPACT-TELEMETRY-1 | DS3-S10, PS3-1 | Auto and micro compaction must emit typed telemetry, not only UI text or substring-detected logs. | `QueryEngine` emits `compact_micro_start`, `compact_micro_end`, `compact_micro_failed`, `compact_auto_start`, `compact_auto_end`, `compact_auto_skipped`, and `compact_failed`. | `core/query_engine.py` | `tests/integration/test_software_compact_telemetry.py::test_microcompact_emits_typed_audit_events`; `tests/integration/test_software_compact_telemetry.py::test_auto_compact_emits_typed_start_and_end`; `logs/software-compact-telemetry-tests.log` | `blocks/SOFTWARE-COMPACT-TELEMETRY/DECISIONS.md` | SHIPPED | None. | APPROVED |
| SOFTWARE-COMPACT-TELEMETRY-2 | DS3-S10, PS3-6 | Telemetry builder must consume typed compaction events, cache evidence, and parent/subagent/reviewer attribution. | `build_telemetry.py` records typed compaction events, cache trend, `agent_attribution`, and validates required keys. | `_status/scripts/build_telemetry.py` | `tests/integration/test_build_telemetry.py`; `logs/software-compact-telemetry-build-telemetry-tests.log` | `blocks/SOFTWARE-COMPACT-TELEMETRY/DECISIONS.md` | SHIPPED | None. | APPROVED |
| SOFTWARE-COMPACT-TELEMETRY-3 | DS3-S18 | Repeated failed tool calls need durable loop-break telemetry. | `QueryEngine` records failure signatures across runs, emits `tool_failure_recorded`, warns on consecutive failures, and blocks the third identical failed call with `tool_failure_loop_blocked`. | `core/query_engine.py` | `tests/integration/test_software_compact_telemetry.py::test_repeated_tool_failure_loop_is_audited_and_blocked`; `logs/software-compact-telemetry-tests.log` | `blocks/SOFTWARE-COMPACT-TELEMETRY/DECISIONS.md` | SHIPPED | None. | APPROVED |
| SOFTWARE-COMPACT-TELEMETRY-4 | DS3-S9 | Manual compact/clean control must be either added or explicitly dispositioned with local coverage. | No new `/compact` command is added for v5.0.1; direct forced micro/auto compaction tests prove the accepted compaction trigger surfaces and typed telemetry under the third-scan TEST_HARDENING_ONLY branch. User-facing manual compact/clean remains future unless AWS evidence requires it. | `core/query_engine.py`; `commands.py` unchanged command surface | `tests/integration/test_software_compact_telemetry.py`; `logs/software-compact-telemetry-tests.log` | `blocks/SOFTWARE-COMPACT-TELEMETRY/DECISIONS.md` | SHIPPED | None. | APPROVED |

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
