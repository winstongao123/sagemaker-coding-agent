# SOFTWARE-SHELL Changelog

Status: CLOSED_READY_FOR_GIT_CHECKPOINT
Date: 2026-05-05

Changed:

- Foreground subprocesses now start in killable process groups.
- Timeout and stop paths now kill the process tree.
- Added `runtime/shell_jobs.py` managed background job lifecycle.
- Added `bash` background start and poll/wait/kill controls.
- Added no-orphan and background lifecycle tests.
- Claude iter2 approved all rows with 0 blockers; worker applied two
  non-blocking LOW cleanup notes.
