# chat.ipynb Companion

This file mirrors the current notebook usage in `chat.ipynb`.

## Purpose

`chat.ipynb` is a launcher/config notebook for `sagemaker_agent.py`.

## Typical cells

1. Install deps (inside notebook):

```python
!pip install -q boto3 ipywidgets Pillow python-docx pandas openpyxl matplotlib reportlab
```

If using terminal instead of notebook, use plain `pip install` (no `!`).

2. Config UI cell:
- Imports `BEDROCK_MODELS` from `sagemaker_agent.py` (single source of truth)
- Lets you choose model, temperature, thinking budget
- Writes values into `CONFIG`

3. Launch cell:

```python
from sagemaker_agent import CONFIG, create_chat_ui
create_chat_ui()
```

## Current behavior notes

- UI shows live model connection status (validated via Bedrock call).
- `Think Budget` is editable when `Extended Thinking` is ON.
- `Require Approval` toggle exists in UI and defaults OFF for SageMaker reliability.
- Tool list/capabilities in notebook markdown are updated to **17 tools**.

## If behavior seems stale

Restart kernel and rerun all notebook cells to pick up latest Python changes.
