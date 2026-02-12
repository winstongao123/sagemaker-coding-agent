# Notebook Quick Cells

Use these cells in SageMaker.

## Cell 1: Install

```python
!pip install -q boto3 ipywidgets Pillow python-docx pandas openpyxl matplotlib reportlab
```

## Cell 2: Set token (if needed in notebook runtime)

```python
import os
os.environ["SAGEMAKER_AGENT_AUTH_TOKEN"] = "replace-with-strong-token"
```

## Cell 3: Launch

```python
from sagemaker_agent import create_chat_ui
create_chat_ui()
```

## First chat command

```text
/auth replace-with-strong-token
```
