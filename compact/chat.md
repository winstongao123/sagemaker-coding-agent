# chat.ipynb Companion

This notebook is only a launcher/UI helper.

## Minimal cells

```python
!pip install -q boto3 ipywidgets Pillow python-docx pandas openpyxl matplotlib reportlab
```

```python
import os
os.environ["SAGEMAKER_AGENT_AUTH_TOKEN"] = "replace-with-strong-token"
```

```python
from sagemaker_agent import create_chat_ui
create_chat_ui()
```

## First command in chat

```text
/auth replace-with-strong-token
```

For full setup details, use `SETUP_AND_USE.md`.
