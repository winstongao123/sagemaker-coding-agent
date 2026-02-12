# sagemaker_agent.py Companion

This file explains where to change key behavior in `sagemaker_agent.py`.

## Common edits

1. Security/ops defaults: `Config` dataclass
- execution mode, docker limits, auth requirement, quotas

2. Command security: `SecurityManager`
- `BASE_ALLOWED_COMMANDS`
- command validation + python validation rules

3. Execution paths
- `tool_bash`
- `tool_python_exec`

4. UI/auth flow
- `create_chat_ui`
- `/auth` gate and approval UI

5. Session/memory loop
- `Agent.run`
- compaction + rate/session/exec budgets

## Source of truth

Always trust `sagemaker_agent.py` over docs if there is mismatch.
