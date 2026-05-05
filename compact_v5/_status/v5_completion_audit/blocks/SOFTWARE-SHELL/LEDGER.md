# SOFTWARE-SHELL Ledger

Status: CLOSED_READY_FOR_GIT_CHECKPOINT
Date: 2026-05-05

Manual software-builder ledger:

| row_id | gap_id | requirement | implementation | code_evidence | test_evidence | doc_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|
| SOFTWARE-SHELL-1 | DS3-S16, PS3-8 | Foreground timeout/stop kills process tree. | `run_subprocess()` starts a new process group, kills the tree on timeout, and `kill_active_process()` uses the same tree-kill path. | `security/manager.py:530`; `security/manager.py:538`; `security/manager.py:580`; `security/manager.py:600` | `tests/integration/test_software_shell.py::test_foreground_timeout_kills_child_process_tree` | `blocks/SOFTWARE-SHELL/DECISIONS.md` | SHIPPED | None. | APPROVED |
| SOFTWARE-SHELL-2 | DS3-S17, PS3-8 | Managed background shell lifecycle. | `ShellJobManager` starts jobs with stdout/stderr logs, polls status, waits, kills, and persists metadata under `.sageagent_state/shell_jobs/index.json`. | `runtime/shell_jobs.py:39`; `runtime/shell_jobs.py:104`; `runtime/shell_jobs.py:141`; `runtime/shell_jobs.py:160`; `runtime/shell_jobs.py:173` | `tests/integration/test_software_shell.py::test_background_shell_job_start_poll_wait_kill` | `blocks/SOFTWARE-SHELL/DECISIONS.md` | SHIPPED | None. | APPROVED |
| SOFTWARE-SHELL-3 | DS3-S17 | Bash tool exposes background job controls honestly. | `bash` schema supports `background`, `action`, and `job_id`; local background starts use the manager, and action paths call poll/wait/kill. | `tools/bash.py:84`; `tools/bash.py:119`; `tools/bash.py:184` | `software-shell-tests.log`; py_compile log | `blocks/SOFTWARE-SHELL/DECISIONS.md` | SHIPPED | Broader bash-tool action integration tests are future hardening, not ship-blocking. | APPROVED |

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
