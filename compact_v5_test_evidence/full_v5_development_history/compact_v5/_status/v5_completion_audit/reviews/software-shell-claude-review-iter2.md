I have independently verified scope, code evidence, test logs, and DECISIONS.md. SYNTHESIS_MASTER has no SOFTWARE-SHELL rows (as expected per the addendum); canonical scope is reconstructed from DS3-S16, DS3-S17, and PS3-8.

```text
EXPECTED ROW COUNT: 3
LEDGER ROW COUNT: 3
DISPOSITION COUNTS:
- SHIPPED: 3
- PARTIAL: 0
- MISSING: 0
- DEFERRED_USER_APPROVED: 0
- DROPPED_USER_APPROVED: 0
- N/A_CONSTRAINT: 0

REVIEWED ROWS:
- SOFTWARE-SHELL-1: APPROVE - DS3-S16/PS3-8 covered: security/manager.py:580 run_subprocess opens process group (CREATE_NEW_PROCESS_GROUP / start_new_session), :600 calls _kill_process_tree on TimeoutExpired, :538 _kill_process_tree uses taskkill /T /F on Windows and os.killpg SIGTERM->SIGKILL on POSIX, :530 kill_active_process re-uses the same tree-kill path; lock-test test_foreground_timeout_kills_child_process_tree creates parent->child sentinel and asserts the sentinel file is never written after a 1s timeout (passes per software-shell-tests.log "2 passed in 4.66s"); DECISIONS.md documents Windows/POSIX strategy.
- SOFTWARE-SHELL-2: APPROVE - DS3-S17/PS3-8 covered: runtime/shell_jobs.py ShellJobManager.start (:104) launches with new process group/session and durable stdout/stderr log files, status (:141) polls returncode and emits tails, wait (:160) honors timeout, kill (:173) routes through _kill_process_tree, _persist writes index.json under .sageagent_state/shell_jobs and _load_index recovers entries after restart (marking them unknown_after_restart honestly); test_background_shell_job_start_poll_wait_kill exercises start/poll/wait/kill and asserts index.json exists; passes per logs.
- SOFTWARE-SHELL-3: APPROVE - DS3-S17 bash tool honestly exposes background surface: tools/bash.py:84-98 schema declares background/action/job_id, :119-137 routes action=poll|wait|kill through SHELL_JOBS, :184-194 starts background jobs via SHELL_JOBS.start, :159-160 explicitly errors when background+docker (matching DECISIONS.md boundary), description text (:55) and module docstring (:18-23) state that background is v5-native and not promised beyond what is implemented; py_compile log = PASS; integration tests exercise the manager that bash.py wires to. Future broader bash action integration tests are noted in the ledger as nice-to-have, not ship-blocking.

FINDINGS:
- LOW runtime/shell_jobs.py:109-125: start() closes its `out`/`err` Python file objects in the `finally` block immediately after Popen returns. POSIX/Windows both leave the child's inherited descriptor open so writes still succeed (and the test confirms this), but a one-line comment noting this is intentional would prevent a future reader from "fixing" it. Non-blocking.
- LOW runtime/shell_jobs.py:66-80 _load_index: setting `status = "unknown_after_restart"` is correct restart semantics, but `kill()` on a recovered job (proc is None) still sets status to "killed" without verifying the original PID is actually gone. Acceptable for v5.0.1 personal SageMaker scope; documented boundary would be cleaner. Non-blocking.

DISPUTED FINDINGS:
- NONE

REMAINING SHIP-BLOCKING ROWS: 0

VERDICT: APPROVE
SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW
```
