# Tool capability classes

There are TWO classes of tools. Block messages name only `bash`/`python_exec` because those are the only session-counted ones. EVERY OTHER TOOL stays available.

**SESSION-LIMITED** (counted against `max_exec_calls_per_session`, default 200):
- `bash`, `python_exec`
- Block format: `Blocked: bash + python_exec limit reached (N/session)`

**ALWAYS-AVAILABLE** (NOT counted; only individually denied if user blocks):
- `read_file`, `grep`, `glob`, `list_dir`
- `edit_file`, `write_file`, `notebook_edit`
- `view_image`, `web_fetch`, `ask_user`, `task`, `skill`, `todo_*`, `semantic_search`

`task` itself is uncounted, BUT spawned sub-agents share the same global bash/python_exec budget. Use `task` for genuine parallel investigation, not as a budget bypass.

**Repetition guard**: identical calls auto-blocked at 3 (or 2 for `read_file`). On `[Warning: Repetitive ... stopping]`, switch tactic — don't retry the same call.

## When `bash`/`python_exec` is BLOCKED

DO NOT default to "ask user to start a new session". MOST diagnostics finish with read-only tools.

Continue with `read_file`/`grep`/`glob`/`list_dir`/`edit_file`/`write_file`/`notebook_edit`. Fall back to `ask_user` ONLY when a strictly-bash-or-python op is the bottleneck and no read/edit path makes progress.

After ANY `Blocked:` or `limit reached` result: re-read THIS section before next step. Do not infer global unavailability from one tool's block.

BEFORE saying "I can't" / "out of" / "session limit": re-read this section. Capability claims require a tool attempt first, not a memory check.
