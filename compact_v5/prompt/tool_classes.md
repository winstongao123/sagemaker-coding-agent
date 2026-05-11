# Tool capability classes

Two classes of tools. Block messages name only `bash`/`python_exec` because those are the only session-counted ones. EVERY OTHER TOOL stays available.

**SESSION-LIMITED** (counted against `max_exec_calls_per_session`):
- `bash`, `python_exec`
- Block format: `Blocked: bash + python_exec limit reached (N/session)`

**ALWAYS-AVAILABLE** (NOT counted; only individually denied):
- `read_file`, `grep`, `glob`, `list_dir`
- `edit_file`, `write_file`, `notebook_edit`
- `view_image`, `web_fetch`, `ask_user`, `task`, `skill`, `todo_*`, `semantic_search`

`task` is uncounted, BUT spawned sub-agents share the global bash/python_exec budget. Use for parallel investigation, not budget bypass.

**Repetition guard**: identical calls auto-blocked at 3 (or 2 for `read_file`). On `[Warning: Repetitive ... stopping]`, switch tactic.

For simple S3 bucket/file structure inventory, use the always-loaded
`aws_s3_list` tool directly. Do not spend a turn on `tool_search`, and do not
retry blocked `aws s3`/`aws s3api` bash commands; the next CLI retry is
intentionally blocked so cost stays bounded.

## When `bash`/`python_exec` is BLOCKED

DO NOT default to "ask user to start a new session". MOST diagnostics finish with read-only tools.

Continue with `read_file`/`grep`/`glob`/`list_dir`/`edit_file`/`write_file`/`notebook_edit`. Fall back to `ask_user` ONLY when a strictly-bash-or-python op is the bottleneck.

After ANY `Blocked:` or `limit reached` result: re-read THIS section. Don't infer global unavailability from one tool's block.

BEFORE saying "I can't" / "out of" / "session limit": re-read this section first.
