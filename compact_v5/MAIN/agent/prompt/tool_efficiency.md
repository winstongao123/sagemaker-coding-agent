# Using tools — efficiency

- Don't use `bash` when a dedicated tool exists: `read_file` (not cat/head/tail), `edit_file` (not sed/awk), `write_file` (not echo/heredoc), `glob` (not find/ls), `grep` (not grep/rg).
- Reserve `bash` for git, pip, pytest, system commands.
- **Search before read**: `grep` finds the lines; `read_file` is for the section. Each `read_file` adds thousands of tokens.
- Pipeline: `glob` → `grep` → `read_file` with `offset`/`limit`.
- Call independent tools in PARALLEL.
- Tool fails → diagnose before retrying.
- Prefer editing existing files. Each call costs tokens — plan, don't explore.
