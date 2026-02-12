# Setup and Use Guide (Beginner)

## 1) Required files

Copy these into SageMaker workspace:
- `sagemaker_agent.py`
- `chat.ipynb`
- `SETUP_AND_USE.md`
- `DOCUMENTATION.md`
- `sagemaker_agent.md`
- `chat.md`

## 2) Install dependencies

```python
!pip install -q boto3 ipywidgets Pillow python-docx pandas openpyxl matplotlib reportlab
```

## 3) Verify Docker (recommended mode)

```powershell
docker --version
docker ps
docker pull python:3.11-slim
```

If Docker is unavailable, set `execution_mode = "local"` in `sagemaker_agent.py` (less secure).

## 4) Set auth token

PowerShell:

```powershell
$env:SAGEMAKER_AGENT_AUTH_TOKEN="replace-with-strong-token"
```

Notebook alternative:

```python
import os
os.environ["SAGEMAKER_AGENT_AUTH_TOKEN"] = "replace-with-strong-token"
```

## 5) Launch UI

```python
from sagemaker_agent import create_chat_ui
create_chat_ui()
```

## 6) Authenticate in chat

```text
/auth replace-with-strong-token
```

## 7) Quick test

1. Ask: `list files in current folder`
2. Ask: `read sagemaker_agent.py`
3. Ask: `create a plan to refactor logging`

## 8) Security smoke test

1. Try risky bash command via agent:
   - `git status; powershell -Command whoami`
   - should be blocked.
2. Try dangerous python_exec:
   - `from os import system`
   - should be blocked.

## 9) Pre-release check

```powershell
python -m py_compile sagemaker_agent.py
python -m unittest discover -s tests -v
```
