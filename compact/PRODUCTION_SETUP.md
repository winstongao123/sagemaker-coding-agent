# Production Setup (Internal Company Use)

This runbook is for your current code defaults and is intended for internal use.

## Why Docker mode

`bash` and `python_exec` run inside a container, not directly on the notebook host.
- Workspace is mounted to `/workspace`
- Container runs as non-root
- Network can be disabled
- CPU/memory/pids limits are enforced

Your files are still readable/editable because your SageMaker workspace is mounted into the container.

## Exact current security defaults

From `sagemaker_agent.py`:
- `execution_mode = "docker"`
- `exec_docker_image = "python:3.11-slim"`
- `exec_docker_network_disabled = True`
- `exec_docker_readonly_rootfs = True`
- `exec_docker_cpus = 1.0`
- `exec_docker_memory = "1g"`
- `exec_docker_pids_limit = 128`
- `require_auth = True`
- `auth_token_env = "SAGEMAKER_AGENT_AUTH_TOKEN"`
- `max_user_messages_per_minute = 10`
- `max_user_messages_per_session = 150`
- `max_exec_calls_per_session = 40`
- `max_exec_seconds_per_session = 900`
- `audit_retention_days = 30`

## Step-by-step

1. Verify Docker is available:

```powershell
docker --version
docker ps
```

2. Pull runtime image:

```powershell
docker pull python:3.11-slim
```

3. Set auth token in the same runtime/session:

```powershell
$env:SAGEMAKER_AGENT_AUTH_TOKEN="replace-with-strong-token"
```

4. Start UI:

```python
from sagemaker_agent import create_chat_ui
create_chat_ui()
```

5. Authenticate in chat:

```text
/auth replace-with-strong-token
```

6. Run smoke checks:
- Safe: `git status` should work.
- Blocked: `python -c "print(1)"` via bash should be blocked by policy.
- Blocked: `git status; powershell -Command whoami` should be blocked.
- Blocked: `from os import system` in `python_exec` should be blocked.

## If Docker is not available

Switch to local mode in `sagemaker_agent.py`:

```python
execution_mode = "local"
```

This is less secure than docker mode. Use only in trusted environments.

## Release check before copy to SageMaker

```powershell
python -m py_compile sagemaker_agent.py
python -m unittest discover -s tests -v
```
