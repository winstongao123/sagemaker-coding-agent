# SageMaker Coding Agent

Secure AI coding assistant powered by AWS Bedrock Claude.

**Features:**
- 15 tools (file ops, bash, python exec, documents, vision, semantic search, todos)
- Security controls (workspace boundary, secret detection, command filtering)
- Approval-based execution for write operations
- Session management & audit logging
- Context monitoring with warnings

## Cell 1: Install dependencies (run once)

```python
!pip install -q boto3 ipywidgets Pillow python-docx pandas openpyxl
```

## Cell 2: Configuration

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
    value=30,
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

## Cell 3: Launch Agent

```python
# ============================================================
# LAUNCH AGENT WITH CONFIGURATION
# ============================================================

from sagemaker_agent import CONFIG, create_chat_ui
from IPython.display import display, HTML

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

## Quick Start Examples

Try these prompts to test the agent:

| Task | Example Prompt |
|------|----------------|
| **Explore** | "List files in this directory" |
| **Read** | "Read the README.md file" |
| **Search** | "Find all Python files with 'test' in the name" |
| **Semantic Search** | "Find where authentication is handled" |
| **Edit** | "Add a comment to the top of file.py" |
| **Execute** | "Run git status" |
| **Create Excel** | "Create an Excel file with employee data" |
| **Create Word** | "Write a project summary document" |
| **Plan** | "Help me build a REST API with Flask" |

---

## Capabilities

**15 Tools:**
- File: `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `list_dir`
- Shell: `bash`
- Python: `python_exec`
- Documents: `create_word`, `create_excel`, `create_markdown`
- Vision: `view_image`
- Search: `semantic_search` (AI-powered code search)
- Planning: `todo_write`, `todo_read`

**Security:**
- Workspace boundary enforcement
- Secret detection (API keys, passwords, tokens)
- Dangerous command blocking
- Approval required for write operations
- Immutable audit logging
