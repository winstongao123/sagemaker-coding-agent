# sagemaker_agent.py Companion

This companion reflects the current behavior in `sagemaker_agent.py`.

## Current defaults (Config)

- `execution_mode = "local"`
- `require_auth = False`
- `require_tool_approval = False` (SageMaker-safe default)
- `max_user_messages_per_minute = 10`
- `max_user_messages_per_session = 150`
- `max_exec_calls_per_session = 40`
- `max_exec_seconds_per_session = 900`

## Tooling

The agent exposes **17 tools**:
- File: `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `list_dir`
- Exec: `bash`, `python_exec`
- Docs/data: `create_word`, `create_excel`, `create_markdown`, `create_pdf`, `create_chart`
- Other: `view_image`, `semantic_search`, `todo_write`, `todo_read`

## Security model

- Workspace path boundary enforcement
- Secret scanning for generated content
- Command allowlist + dangerous pattern blocking
- Python execution validation (denylist + AST import checks + runtime import allowlist)
- Optional tool approval gate (UI toggle: `Require Approval`)
- Session/audit logging

## UX/runtime notes

- Model switch performs a live Bedrock validation call and updates status.
- Mode line shows: model, connection status, plan, thinking, auth, approval, exec mode.
- Approval UI can block in some SageMaker kernels; default keeps approval OFF.
- Context compaction uses prune + summary flow and preserves alternation safety.

## Source of truth

If this file and code ever differ, trust `sagemaker_agent.py`.
