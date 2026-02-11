# Vertex AI Gemini Coding Agent

Secure AI coding assistant powered by GCP Vertex AI Gemini 2.5.

**Features:**
- 15 tools (file ops, bash, python exec, documents, vision, semantic search, todos)
- Security controls (workspace boundary, secret detection, command filtering)
- Approval-based execution for write operations
- Session management & audit logging
- Context monitoring with warnings (1M token context)

**Prerequisites:**
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project algebraic-pact-478006-h0
```

## Cell 1: Install dependencies (run once)

```python
!pip install -q google-cloud-aiplatform ipywidgets Pillow python-docx pandas openpyxl
```

## Cell 2: Configuration

```python
# ============================================================
# CONFIGURATION
# ============================================================

import ipywidgets as widgets
from IPython.display import display, HTML

# Available Gemini models in Vertex AI (use stable versions)
AVAILABLE_MODELS = {
    "Gemini 2.0 Flash (Recommended)": "gemini-2.0-flash-001",
    "Gemini 1.5 Flash": "gemini-1.5-flash-002",
    "Gemini 1.5 Pro": "gemini-1.5-pro-002",
}

# Available Vertex AI regions
AVAILABLE_REGIONS = {
    "US Central 1 (Iowa)": "us-central1",
    "US East 4 (Virginia)": "us-east4",
    "Europe West 1 (Belgium)": "europe-west1",
}

# Temperature options
TEMPERATURE_OPTIONS = {
    "0.0 - Deterministic": 0.0,
    "0.7 - Balanced": 0.7,
    "1.0 - Creative": 1.0,
}

PROJECT_ID = "algebraic-pact-478006-h0"

display(HTML("<h3>Gemini Agent Configuration</h3>"))

project_input = widgets.Text(value=PROJECT_ID, description='Project ID:', layout=widgets.Layout(width='400px'))
region_dropdown = widgets.Dropdown(options=list(AVAILABLE_REGIONS.keys()), value="US Central 1 (Iowa)", description='Region:')
model_dropdown = widgets.Dropdown(options=list(AVAILABLE_MODELS.keys()), value="Gemini 2.0 Flash (Recommended)", description='Model:')
temperature_dropdown = widgets.Dropdown(options=list(TEMPERATURE_OPTIONS.keys()), value="0.0 - Deterministic", description='Temperature:')
thinking_checkbox = widgets.Checkbox(value=False, description='Thinking Mode')
max_turns_slider = widgets.IntSlider(value=30, min=5, max=100, step=5, description='Max Turns:')
workspace_input = widgets.Text(value='.', description='Workspace:')

display(widgets.VBox([project_input, region_dropdown, model_dropdown, temperature_dropdown, thinking_checkbox, workspace_input, max_turns_slider]))
```

## Cell 3: Launch Agent

```python
# ============================================================
# LAUNCH AGENT - Run this cell to start
# ============================================================
# For SageMaker: Just run cells 1, 2, then this cell

from IPython.display import display, clear_output
clear_output(wait=True)

# Fresh import (removes cached module)
import sys
for mod in list(sys.modules.keys()):
    if 'gemini_agent' in mod:
        del sys.modules[mod]

import gemini_agent
from gemini_agent import CONFIG, create_chat_ui

# Apply config from cell 2
CONFIG.project_id = project_input.value
CONFIG.region = AVAILABLE_REGIONS[region_dropdown.value]
CONFIG.model_id = AVAILABLE_MODELS[model_dropdown.value]
CONFIG.workspace = workspace_input.value
CONFIG.max_turns = max_turns_slider.value
CONFIG.temperature = TEMPERATURE_OPTIONS[temperature_dropdown.value]
CONFIG.thinking_enabled = thinking_checkbox.value

# Launch (only one display call)
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
- Search: `semantic_search` (AI-powered code search with Vertex AI Embeddings)
- Planning: `todo_write`, `todo_read`

**Security:**
- Workspace boundary enforcement
- Secret detection (API keys, passwords, tokens)
- Dangerous command blocking
- Approval required for write operations
- Immutable audit logging

**Gemini 2.5 Features:**
- 1 million token context window
- Thinking mode for complex reasoning
- Native function calling
- Temperature range 0.0-2.0
