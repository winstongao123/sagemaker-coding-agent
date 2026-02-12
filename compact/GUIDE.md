# Beginner Guide (Start Here)

This guide is for first-time setup in SageMaker.

## 1. Put files in your workspace

You only need:
- `sagemaker_agent.py`
- `chat.ipynb` (optional UI notebook)

## 2. Install dependencies

In notebook or terminal:

```python
!pip install -q boto3 ipywidgets Pillow python-docx pandas openpyxl matplotlib reportlab
```

## 3. Set auth token (required by default)

PowerShell:

```powershell
$env:SAGEMAKER_AGENT_AUTH_TOKEN="replace-with-strong-token"
```

## 4. Start the UI

```python
from sagemaker_agent import create_chat_ui
create_chat_ui()
```

## 5. Authenticate in chat

First message:

```text
/auth replace-with-strong-token
```

## 6. Use the agent

Examples:
- "List files in this folder"
- "Read `app.py` and explain it"
- "Create a plan to refactor this module"

## 7. Important defaults (current code)

- `execution_mode = "docker"`
- `require_auth = True`
- `max_user_messages_per_minute = 10`
- `max_user_messages_per_session = 150`
- `max_exec_calls_per_session = 40`
- `max_exec_seconds_per_session = 900`

## 8. If Docker is unavailable

Set in `sagemaker_agent.py`:

```python
execution_mode = "local"
```

Use local mode only in trusted internal environments.

## 9. Verify installation

```powershell
python -m py_compile sagemaker_agent.py
python -m unittest discover -s tests -v
```
