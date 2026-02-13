# chat.ipynb

## Cell 0 (markdown)

# SageMaker Coding Agent V2

Secure AI coding assistant powered by AWS Bedrock Claude.

**22 Tools:** File ops, bash/python exec, docs/charts/pdf/notebooks, vision, semantic search, todos, web fetch, skills, sub-agents, ask user

**New in V2:**
- External config (`opencode.json`) with JSONC support
- Skills system (`/skills`, `/skill use <name>`, `/skill clear`)
- Custom slash commands with templates (`/review`, `/test`, etc.)
- Sub-agents (build, plan, explore, general) via `task` tool
- MCP client (local stdio + remote HTTP servers)
- Cost tracking (`/cost`) with per-model Bedrock pricing
- Snapshot & revert (`/revert <file>`, `/revert all`)
- Interactive questions (`ask_user` tool)
- Diff tracking on every edit
- Permission rules (per-tool, file-pattern, command-pattern)
- SSRF-hardened web fetch

**Security:** 3-layer bash + 3-layer Python + workspace boundary + SSRF protection

See `USER_GUIDE.md` for full documentation.

## Cell 1 (code)

```python
# Install dependencies (run once)
!pip install -q boto3 ipywidgets Pillow python-docx pandas openpyxl
```

## Cell 2 (code)

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

## Cell 3 (code)

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

## Cell 4 (markdown)

---

## Quick Start Examples

| Task | Example Prompt |
|------|----------------|
| **Explore** | "List files in this directory" |
| **Read** | "Read the README.md file" |
| **Search** | "Find all Python files with test in the name" |
| **Semantic Search** | "Find where authentication is handled" |
| **Edit** | "Add a comment to the top of file.py" |
| **Execute** | "Run git status" |
| **Create Excel** | "Create an Excel file with employee data" |
| **Create Word** | "Write a project summary document" |
| **Create PDF** | "Create a PDF report with table and chart summary" |
| **Web Fetch** | "Fetch https://example.com and summarize it" |
| **Plan** | "Help me build a REST API with Flask" |

---

## Slash Commands

| Command | What it does |
|---------|-------------|
| `/skills` | List discovered skills |
| `/skill use <name>` | Activate a skill |
| `/skill clear` | Deactivate all skills |
| `/commands` | List custom commands from opencode.json |
| `/cost` | Token usage and cost breakdown |
| `/revert <file>` | Revert file to pre-edit snapshot |
| `/revert all` | Revert all modified files |
| `/compact` | Compress conversation context |
| `/save` | Save session |

---

## Tools (22)

- **File:** `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `list_dir`
- **Exec:** `bash`, `python_exec`
- **Docs:** `create_word`, `create_excel`, `create_markdown`, `create_notebook`, `create_pdf`
- **Charts:** `create_chart` (bar, line, pie, scatter — displayed inline)
- **Vision:** `view_image`
- **Search:** `semantic_search` (Bedrock Titan embeddings)
- **Planning:** `todo_write`, `todo_read`
- **Web:** `web_fetch` (URL fetch with SSRF protection)
- **Skills:** `skill` (list/load skills)
- **Sub-agents:** `task` (build, plan, explore, general)
- **Interactive:** `ask_user` (mid-conversation questions)

---

## Security

- 3-layer bash validation (allowlist + 70 patterns + restricted mode)
- 3-layer Python validation (AST + import hook + secret detection)
- SSRF protection (private IP blocking, redirect blocking, 2MB limit)
- Workspace boundary enforcement
- Configurable permission rules via `opencode.json`
- Audit logging and session persistence

