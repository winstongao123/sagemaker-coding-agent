# SOFTWARE-STATE Tests

Status: CLOSED_READY_FOR_GIT_CHECKPOINT
Date: 2026-05-05

Saved logs:

- `logs/software-state-tests.log`
- `logs/software-state-regression-tests.log`
- `logs/software-state-py-compile.log`

Focused tests:

- `tests/integration/test_software_state.py::test_todos_persist_across_memory_reset`
- `tests/integration/test_software_state.py::test_save_resume_round_trip_includes_todos_status_memory`
- `tests/integration/test_software_state.py::test_agent_refreshes_status_and_memory_every_run`
- `tests/integration/test_software_state.py::test_save_can_run_zero_cost_memory_extraction_path`

Regression tests:

- `tests/integration/test_block_b_plus.py::test_save_resume_commands_restore_messages_and_cost`
- `tests/integration/test_block_b_plus.py::test_resume_command_restores_agent_message_buffer`
- `tests/integration/test_block_b_plus.py::test_agent_status_auto_load`
- `tests/integration/test_block_b_plus.py::test_agent_status_auto_load_disabled`

No AWS/R-tier tests were run.
