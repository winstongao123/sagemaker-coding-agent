# SageAgent V3 — Notebook Content

> Markdown version of chat.ipynb. Copy cells into a Jupyter notebook to run.

# SageAgent V3

AI coding assistant for SageMaker notebooks. 22 tools, 16 security layers, v3.2.3.

**Setup:** Run cells 1-3 in order. Cell 1 installs packages (once). Cell 2 shows config widgets. Cell 3 launches the agent.

**Docs:** See `USER_GUIDE.md` for full documentation, `v3_architecture.html` for interactive architecture guide.

### Cell 1 (code)

```python
# Install dependencies (run once)
!pip install -q boto3 ipywidgets Pillow python-docx pandas openpyxl
```

### Cell 2 (code)

```python
# ============================================================
# CONFIGURATION
# ============================================================
# Models are imported from sagemaker_agent.py (single source of truth)

import ipywidgets as widgets
from IPython.display import display, HTML
from sagemaker_agent import BEDROCK_MODELS

# Convert BEDROCK_MODELS list-of-tuples to dict for config cell
AVAILABLE_MODELS = dict(BEDROCK_MODELS)

# Temperature options
TEMPERATURE_OPTIONS = {
    "0.0 - Deterministic": 0.0,
    "0.3 - Low creativity": 0.3,
    "0.5 - Balanced": 0.5,
    "0.7 - High creativity": 0.7,
    "1.0 - Maximum creativity": 1.0,
}

# Thinking budget options
THINKING_BUDGET_OPTIONS = {
    "1024 - Minimal": 1024,
    "2048 - Light": 2048,
    "4096 - Standard": 4096,
    "8192 - Extended": 8192,
    "16000 - Maximum": 16000,
}

# Region - Sydney (ap-southeast-2)
REGION = "ap-southeast-2"

# Create configuration widgets
display(HTML("<h3>Agent Configuration</h3>"))

model_dropdown = widgets.Dropdown(
    options=list(AVAILABLE_MODELS.keys()),
    value="Claude 3 Haiku",
    description='Model:',
    style={'description_width': '120px'},
    layout=widgets.Layout(width='450px')
)

temperature_dropdown = widgets.Dropdown(
    options=list(TEMPERATURE_OPTIONS.keys()),
    value="0.0 - Deterministic",
    description='Temperature:',
    style={'description_width': '120px'},
    layout=widgets.Layout(width='350px')
)

thinking_checkbox = widgets.Checkbox(
    value=False,
    description='Enable Extended Thinking (slower, uses more tokens)',
    indent=False,
    style={'description_width': 'auto'}
)

thinking_budget_dropdown = widgets.Dropdown(
    options=list(THINKING_BUDGET_OPTIONS.keys()),
    value="4096 - Standard",
    description='Thinking Budget:',
    style={'description_width': '120px'},
    layout=widgets.Layout(width='350px')
)

max_turns_slider = widgets.IntSlider(
    value=60,
    min=5,
    max=100,
    step=5,
    description='Max Turns:',
    style={'description_width': '120px'},
    layout=widgets.Layout(width='400px')
)

workspace_input = widgets.Text(
    value='.',
    description='Workspace:',
    placeholder='Directory for file operations',
    style={'description_width': '120px'},
    layout=widgets.Layout(width='400px')
)

mock_toggle = widgets.Checkbox(
    value=False,
    description='Mock Mode (test without API)',
    indent=False,
    style={'description_width': 'auto'}
)

# Display configuration UI
config_box = widgets.VBox([
    model_dropdown,
    widgets.HTML(f"<p style='margin:5px 0;color:#888;'>Region: Sydney ({REGION})</p>"),
    temperature_dropdown,
    thinking_checkbox,
    thinking_budget_dropdown,
    workspace_input,
    max_turns_slider,
    mock_toggle,
], layout=widgets.Layout(padding='10px', border='1px solid #444', margin='10px 0', background='#2d2d2d'))

display(config_box)
display(HTML("<p style='color:#888;font-size:12px;'>Configure settings above, then run the next cell to start.</p>"))
```

### Cell 3 (code)

```python
# ============================================================
# LAUNCH AGENT WITH CONFIGURATION
# ============================================================

from sagemaker_agent import CONFIG, create_chat_ui
from IPython.display import display, HTML

# Security & cost settings (previously in agent_config.json)
CONFIG.aws_bedrock_only = True          # Block ALL AWS services except Bedrock
CONFIG.require_tool_approval = True     # Show Approve/Deny dialog before execution
CONFIG.session_cost_limit = 1.0         # Max $1.00 per session (warns at 80%, stops at 100%)

# Custom slash commands: /review, /explain, /test
CONFIG.custom_commands = {
    "review": {"template": "Review the following code for bugs, security issues, and improvements:\n$ARGUMENTS", "description": "Code review", "agent": "plan"},
    "explain": {"template": "Explain this code in detail, including what it does and how it works:\n$ARGUMENTS", "description": "Explain code"},
    "test": {"template": "Write comprehensive tests for:\n$ARGUMENTS", "description": "Generate tests"},
}

# Apply configuration from widgets above
CONFIG.model_id = AVAILABLE_MODELS[model_dropdown.value]
CONFIG.region = REGION  # Sydney
CONFIG.workspace = workspace_input.value
CONFIG.max_turns = max_turns_slider.value
CONFIG.mock_mode = mock_toggle.value
CONFIG.temperature = TEMPERATURE_OPTIONS[temperature_dropdown.value]
CONFIG.thinking_enabled = thinking_checkbox.value
CONFIG.thinking_budget = THINKING_BUDGET_OPTIONS[thinking_budget_dropdown.value]

# Display current config
thinking_str = f"Thinking: On (budget: {CONFIG.thinking_budget})" if CONFIG.thinking_enabled else "Thinking: Off"
display(HTML(f"""
<div style="background:#1e3a1e;padding:10px;border-radius:5px;margin:10px 0;color:#d4d4d4;">
<b>Configuration Applied</b><br>
Model: {model_dropdown.value} | Region: Sydney | Temp: {CONFIG.temperature}<br>
{thinking_str} | Mock: {'Yes' if CONFIG.mock_mode else 'No'}
</div>
"""))

# Launch the chat interface
create_chat_ui()
```

---

## Quick Reference

| Action | How |
|--------|-----|
| **Send message** | Type in the input box, press Send |
| **Stop agent** | Click Stop button |
| **Check cost** | Type `/cost` |
| **Code review** | Type `/review filename.py` |
| **Revert file** | Type `/revert filename.py` or `/revert all` |
| **Compact context** | Click Compact button (or auto at 80%) |
| **Clean traces** | Click Clean button (removes audit/snapshots, keeps sessions) |
| **Save session** | Click Save button (auto-saves after each message) |
| **Load session** | Use Session dropdown + Load button |

## Config (Cell 3)

All settings are in the launch cell. Key ones:
- `aws_bedrock_only = True` — blocks all AWS except Bedrock
- `session_cost_limit = 1.0` — max $1 per session
- `require_tool_approval = True` — approve/deny dialog before execution

Change the model in Cell 2 dropdown. Default: Claude 3 Haiku (cheapest).

For full docs: `USER_GUIDE.md` | Architecture: `v3_architecture.html`

