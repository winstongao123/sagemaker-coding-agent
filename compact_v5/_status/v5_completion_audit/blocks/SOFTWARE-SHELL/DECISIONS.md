# SOFTWARE-SHELL Decisions

Status: CLOSED_READY_FOR_GIT_CHECKPOINT
Date: 2026-05-05

Decisions:

- Use process groups for foreground shell/python subprocesses, with
  `taskkill /T /F` on Windows and `os.killpg` on POSIX.
- Keep `run_subprocess()` as the shared foreground primitive so both `bash`
  and `python_exec` inherit timeout/no-orphan behavior.
- Add a v5-native `ShellJobManager` for local managed background jobs.
- Store background job stdout/stderr logs and an index under
  `.sageagent_state/shell_jobs/`.
- Expose background controls through `bash` using `background=true` and
  `action=poll|wait|kill`.

Boundary:

- Docker background jobs are explicitly not supported in this block.
