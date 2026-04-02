# Setup and Use Guide (Beginner)

This guide now has **two paths**:

1. `Path A (Personal default)` - easiest, works in most SageMaker environments.
2. `Path B (Shared/Secure)` - auth on, optional Docker isolation.

## 1) Required files

Copy these into SageMaker workspace:
- `sagemaker_agent.py`
- `chat.ipynb`
- `SETUP_AND_USE.md`
- `DOCUMENTATION.md`
- `sagemaker_agent.md`
- `chat.md`

## 2) Install dependencies

If using SageMaker terminal:

```bash
pip install -U pip
pip install boto3 ipywidgets Pillow python-docx pandas openpyxl matplotlib reportlab
```

If using a notebook cell:

```python
!pip install -q boto3 ipywidgets Pillow python-docx pandas openpyxl matplotlib reportlab
```

## Path A (Personal default - recommended for you)

Use this if you are the only user.

### A1) Default config (already set in code)

In `sagemaker_agent.py` defaults:

```python
execution_mode = "local"
require_auth = False
```

No auth token is needed in this path.

### A2) Launch UI

```python
from sagemaker_agent import create_chat_ui
create_chat_ui()
```

You can use it directly. No `/auth` step.

---

## Path B (Shared/Secure mode)

Use this if other users might access the notebook/session.

### B1) Turn on auth

Set in `sagemaker_agent.py`:

```python
require_auth = True
```

Set token (terminal/bash):

```bash
export SAGEMAKER_AGENT_AUTH_TOKEN="replace-with-strong-token"
```

Then authenticate in chat:

```text
/auth replace-with-strong-token
```

### B2) Optional: Docker isolation

Keep/set:

```python
execution_mode = "docker"
```

Then check Docker:

```powershell
docker --version
docker ps
docker pull python:3.11-slim
```

In many SageMaker Studio environments, Docker daemon is not exposed to notebook users by default.

If you see `Cannot connect to the Docker daemon...`, Docker isolation is unavailable in your current SageMaker environment.

In that case, set this once in `sagemaker_agent.py`:

```python
execution_mode = "local"
```

Then restart kernel and run UI again.

This app still works in local mode (no container isolation).

#### If you want Docker isolation in SageMaker Studio

This is possible, but requires admin/domain setup:

1. Enable Studio Docker access at the Domain level (`EnableDockerAccess=ENABLED`).
2. Create a new Studio app (or restart/recreate app as required by your setup) after domain change.
3. Ensure Docker CLI is available in that app image.
4. Re-run the checks:

```bash
docker --version
docker info
```

If `docker info` works, switch back to docker mode:

```python
execution_mode = "docker"
```

## 4) Launch UI

```python
from sagemaker_agent import create_chat_ui
create_chat_ui()
```

## 5) Quick test

1. Ask: `list files in current folder`
2. Ask: `read sagemaker_agent.py`
3. Ask: `create a plan to refactor logging`

## 6) Security smoke test

1. Try risky bash command via agent:
   - `git status; powershell -Command whoami`
   - should be blocked.
2. Try dangerous python_exec:
   - `from os import system`
   - should be blocked.

## 7) Pre-release check

```powershell
python -m py_compile sagemaker_agent.py
python -m unittest discover -s tests -v
```

## FAQ: Is SageMaker not supporting Docker?

Not exactly. SageMaker Studio can support Docker/local mode, but many domains have it disabled by default.

If your domain is not configured for Docker access, you will see daemon errors and must use local mode.

You can still run the app in local mode. For stronger isolation, use another runtime that supports daemon/container execution.
