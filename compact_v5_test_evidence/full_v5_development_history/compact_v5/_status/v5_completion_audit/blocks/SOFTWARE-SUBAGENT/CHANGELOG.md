# SOFTWARE-SUBAGENT Changelog

Status: READY_FOR_BLOCK_CLOSE_REVIEW
Date: 2026-05-05

Changed implementation:

- `compact_v5/MAIN/agent/subagent/spawn.py`
  - added structured `SubagentResult` envelope fields;
  - added child duration, heartbeat, files-changed extraction, token/cost/cache delta calculation, and recovery hints;
  - preserved parent-context mutation recovery while surfacing it in the envelope.
- `compact_v5/MAIN/agent/tools/task.py`
  - appends `[subagent_result_envelope]` JSON to successful and stopped task results;
  - logs best-effort `subagent_result` audit records.

Changed tests:

- `compact_v5/MAIN/agent/tests/integration/test_software_subagent.py`
  - verifies direct spawn envelope token/cache/cost/files/heartbeat metadata;
  - verifies `task` returns a structured reviewer envelope;
  - verifies budget exhaustion includes recovery metadata.

Validation logs:

- `compact_v5/_status/v5_completion_audit/logs/software-subagent-tests.log`
- `compact_v5/_status/v5_completion_audit/logs/software-subagent-regression-tests.log`
- `compact_v5/_status/v5_completion_audit/logs/software-subagent-py-compile.log`

Affected original blocks:

- Block G/G2/G3 subagent surfaces are strengthened but not reopened. The change is reviewed under active `SOFTWARE-SUBAGENT` scope because it is prompted by DS3-S5/PS3-4/PS3-6.
