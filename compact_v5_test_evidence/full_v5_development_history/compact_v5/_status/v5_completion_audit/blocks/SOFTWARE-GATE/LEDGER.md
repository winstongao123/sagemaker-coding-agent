# SOFTWARE-GATE Ledger

Status: IMPLEMENTED_APPROVED
Date: 2026-05-05

Manual software-builder ledger:

| row_id | gap_id | requirement | implementation | code_evidence | test_evidence | doc_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|
| SOFTWARE-GATE-1 | DS3-S4, PS3-9 | `/verify` must be an enforced gate requiring fresh local evidence instead of only arming a skill. | `cmd_verify` runs `runtime.gate.run_verify_gate`, persists `.sageagent_state/gates/last_verify.json`, and returns `verify_passed` or `verify_blocked` with per-category reasons. | `compact_v5/MAIN/agent/commands.py`; `compact_v5/MAIN/agent/runtime/gate.py` | `tests/integration/test_software_gate.py::test_verify_blocks_missing_test_and_review_evidence`; `logs/software-gate-tests.log` | `blocks/SOFTWARE-GATE/DECISIONS.md` | SHIPPED | None pending Claude review. | APPROVED |
| SOFTWARE-GATE-2 | DS3-S4, PS3-9 | `/done` must refuse stale/missing status, test, review, or failed verification evidence. | `cmd_done` runs `runtime.gate.run_done_gate`, requires a fresh passing matching verify record, rechecks evidence freshness, and returns `done_ready` only on pass. | `compact_v5/MAIN/agent/commands.py`; `compact_v5/MAIN/agent/runtime/gate.py` | `tests/integration/test_software_gate.py::test_done_requires_fresh_passing_verify_record`; `tests/integration/test_software_gate.py::test_done_rechecks_status_freshness_after_verify`; `logs/software-gate-tests.log` | `blocks/SOFTWARE-GATE/DECISIONS.md` | SHIPPED | None pending Claude review. | APPROVED |
| SOFTWARE-GATE-3 | DS3-S4, DS3-S7, DS3-S5, DS3-S10, PS3-4, PS3-6, PS3-7 | Full close gate must consume state/status, large-result, subagent, and telemetry evidence created by earlier software-builder blocks. | Full mode checks status file freshness, test logs, Claude/review verdict logs, large result references, structured subagent envelopes, and typed compaction/cache telemetry. | `compact_v5/MAIN/agent/runtime/gate.py`; `compact_v5/MAIN/agent/prompt/commands.md` | `tests/integration/test_software_gate.py::test_done_requires_fresh_passing_verify_record`; `logs/software-gate-tests.log`; `logs/software-gate-command-regression-tests.log` | `blocks/SOFTWARE-GATE/DECISIONS.md`; `prompt/commands.md` | SHIPPED | None pending Claude review. | APPROVED |
| SOFTWARE-GATE-4 | DS3-S18 | `/verify` and `/done` must not silently pass when repeated-failure loop telemetry is present. | Telemetry checks accept typed compaction/cache/failure telemetry but block unresolved `tool_failure_loop_blocked` or `tool_failure_loop_warning` markers. | `compact_v5/MAIN/agent/runtime/gate.py` | `tests/integration/test_software_gate.py::test_done_blocks_unresolved_failure_loop_telemetry`; `logs/software-gate-tests.log` | `blocks/SOFTWARE-GATE/DECISIONS.md` | SHIPPED | None pending Claude review. | APPROVED |

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
