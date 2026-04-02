# SageAgent V3 — Notebook Content

> Markdown version of chat.ipynb

<style>table { margin-left: 0 !important; } td, th { text-align: left !important; }</style>

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
    value="Claude 4.5 Haiku (AU)",
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
    "review": {
        "template": (
            "Read $ARGUMENTS and perform a thorough code review using this checklist:\n"
            "\n## 1. Security (CRITICAL)\n"
            "Check: hardcoded secrets, SQL injection, command injection, XSS, path traversal, input validation, auth checks, sensitive data in logs\n"
            "\n## 2. Code Quality (HIGH)\n"
            "Check: functions <50 lines, nesting <4 levels, specific error handling, clear naming, no dead code, no debug statements, DRY, consistent style\n"
            "\n## 3. Performance (MEDIUM)\n"
            "Check: N+1 queries, O(n^2) algorithms, missing caching, unnecessary allocations, lazy processing for large collections\n"
            "\n## 4. Architecture (MEDIUM)\n"
            "Check: separation of concerns, follows existing patterns, no circular deps, config externalized\n"
            "\n## 5. Testing (MEDIUM)\n"
            "Check: critical paths covered, edge cases handled, tests independent, error paths tested\n"
            "\n## Output: Summary, Issues (CRITICAL/HIGH/MEDIUM/LOW with file:line), Positive observations, Suggestions, Rating X/10"
        ),
        "description": "Full code review with 5-category checklist (security, quality, performance, architecture, testing)",
        "agent": "plan"
    },
    "explain": {
        "template": (
            "Read $ARGUMENTS and explain thoroughly:\n"
            "1. PURPOSE: What does this code do? What problem does it solve?\n"
            "2. ARCHITECTURE: How is it structured? What are the main components/classes/functions?\n"
            "3. DATA FLOW: How does data move through the code? Trace a typical request/call.\n"
            "4. KEY DECISIONS: What design patterns are used? Why were they chosen?\n"
            "5. DEPENDENCIES: What does it depend on? What depends on it?\n"
            "6. EDGE CASES: What error handling exists? What could go wrong?\n"
            "Use concrete examples from the actual code. Reference specific line numbers."
        ),
        "description": "Deep code explanation (purpose, architecture, data flow, patterns, dependencies, edge cases)"
    },
    "test": {
        "template": (
            "Read $ARGUMENTS and write comprehensive tests:\n"
            "1. Happy path: normal expected behavior\n"
            "2. Edge cases: empty input, None, boundaries, duplicates, max values\n"
            "3. Error cases: invalid input, missing data, permission errors, timeouts\n"
            "4. Integration: how components work together\n"
            "Use pytest style. Each test: Arrange, Act, Assert. Test names describe what is tested.\n"
            "Target: minimum 8 test functions with good coverage of all branches."
        ),
        "description": "Generate comprehensive test suite (happy path, edge cases, error cases, integration)"
    },
    "verify": {
        "template": (
            "Run 6-phase verification on the current workspace:\n"
            "Phase 1 BUILD: run build/compile if applicable (pip install -e . / npm run build)\n"
            "Phase 2 TYPES: run type checker (mypy/pyright/tsc) if available\n"
            "Phase 3 LINT: run linter (ruff/flake8/eslint) if available\n"
            "Phase 4 TESTS: run test suite (pytest/npm test) with coverage if available\n"
            "Phase 5 SECURITY: grep for hardcoded secrets, .env files, debug statements\n"
            "Phase 6 DIFF: git diff to review all changes\n"
            "\nOutput a VERIFICATION REPORT: each phase PASS/FAIL/SKIP, issues found, ready for PR: YES/NO"
        ),
        "description": "6-phase verification: build, types, lint, tests, security scan, diff review"
    },
    "standards": {
        "template": (
            "Review $ARGUMENTS against these coding standards:\n"
            "NAMING: descriptive vars, verb-noun functions, PascalCase classes, UPPER_SNAKE constants\n"
            "FUNCTIONS: single responsibility, <50 lines, <4 params, <4 nesting, early returns\n"
            "ERRORS: specific exceptions (not bare except), no swallowed errors, user-friendly messages\n"
            "PRINCIPLES: KISS, DRY, YAGNI\n"
            "Fix any violations found. Show before/after for each fix."
        ),
        "description": "Apply coding standards (naming, functions, errors, KISS/DRY/YAGNI)"
    },
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
| **Send message** | Type in input box, press Send |
| **Stop agent** | Click Stop button |
| **Check cost** | Type `/cost` |
| **Code review** | Type `/review filename.py` |
| **Explain code** | Type `/explain filename.py` |
| **Generate tests** | Type `/test filename.py` |
| **Verify project** | Type `/verify` |
| **Apply standards** | Type `/standards filename.py` |
| **Revert file** | Type `/revert filename.py` or `/revert all` |
| **Compact context** | Click Compact button (or auto at 80%) |
| **Clean traces** | Click Clean button (removes audit/snapshots, keeps sessions) |
| **Save/Load** | Save button (auto-saves each message) / Session dropdown + Load |

## Quick Start Examples

| Task | What to type |
|------|-------------|
| Read a file | "Read app.py" |
| Find files | "Find all Python files in this project" |
| Fix a bug | "Read app.py, find the bug, and fix it" |
| Create chart | "Create a bar chart from sales.csv showing revenue by product" |
| Create report | "Create a Word report summarizing the data in results.csv" |
| Run command | "Run git status" |
| Analyze image | "Look at screenshot.png and describe what you see" |
| Search code | "Find where authentication is handled in this codebase" |

## 22 Tools

| Category | Tools | Approval? |
|----------|-------|-----------|
| **File** | read_file, write_file, edit_file, glob, grep, list_dir | write/edit need approval |
| **Exec** | bash, python_exec | Both need approval |
| **Docs** | create_word, create_excel, create_chart, create_pdf, create_markdown, create_notebook | Need approval |
| **Intelligence** | view_image (vision), semantic_search (code search), web_fetch (URL fetch only) | web_fetch needs approval |
| **Agents** | skill (load checklist), task (spawn sub-agent), ask_user (ask you a question) | task needs approval |
| **State** | todo_write, todo_read | Auto |

## Sub-Agents (via `/task` or the agent decides automatically)

| Type | What it does | Tools | Max turns |
|------|-------------|-------|-----------|
| **build** | Build, compile, fix errors, run tests | All 22 | 25 |
| **plan** | Architecture analysis, planning (read-only) | 11 (read + web + ask) | 15 |
| **explore** | Fast file search, codebase navigation | 5 (read + grep + glob) | 10 |
| **general** | General coding tasks | 11 (no doc tools) | 15 |
| **review** | Security, quality, performance review | 6 (read + search + vision) | 10 |

## Security (16 layers)

The agent runs inside a security sandbox. Key protections:
- **Bash**: 70 allowed commands only. 75 dangerous patterns blocked. Files restricted to workspace.
- **Python**: 63 regex patterns + AST import validation (67 allowed modules) + runtime sandbox on open/remove.
- **AWS**: `aws_bedrock_only` blocks ALL AWS services except Bedrock (regex + AST + getattr enforcement).
- **Approval dialog**: You see exact command/code and Approve or Deny before execution.
- **Cost limit**: Stops agent if session cost exceeds your configured limit.
- **Audit trail**: Every tool call logged with timestamp and integrity hash.

## Model Pricing (Bedrock, Sydney region)

| Model | Input / 1M tokens | Output / 1M tokens |
|-------|-------------------|-------------------|
| Claude 3 Haiku | $0.25 | $1.25 |
| Claude 3.5 Haiku | $0.80 | $4.00 |
| **Claude 4.5 Haiku (AU)** | **$1.10** | **$5.50** |
| Claude 4.5 Sonnet (AU) | $3.30 | $16.50 |
| Claude 4.5 Opus | $5.00 | $25.00 |
| Claude 4.6 Opus (AU) | $5.50 | $27.50 |

## How It Works

1. You type a message → sent to Claude via Bedrock API
2. Claude decides which tool to use → calls it (with your approval if needed)
3. Tool runs, result sent back to Claude → Claude decides next step or gives final answer
4. Repeats up to 60 turns per message (configurable)
5. Context auto-compacts at 80% usage (prune old tool outputs, then LLM summarize if needed)

## Token Overhead Per API Call

| Component | Tokens |
|-----------|--------|
| System prompt | ~1,200 |
| Tool schemas | ~1,800 (lazy-load: ~1,200 for coding tasks) |
| Bedrock overhead | ~346 |
| **Total per call** | **~3,350** |

## Session Management

| Feature | How |
|---------|-----|
| **Auto-save** | Every message auto-saves (messages, todos, metadata) |
| **Load session** | Session dropdown + Load button |
| **New session** | New button (clears all state) |
| **Checkpoints** | `/checkpoint name` (saves snapshot, max 50) |

## Commands vs Skills

| Method | How | Depth | Persists? |
|--------|-----|-------|-----------|
| `/review app.py` | Inline command — sends condensed checklist once | ~15 lines | No (one-shot) |
| `/skill use review` then "review app.py" | Loads full skill file into system prompt | ~83 lines | Yes (all messages until `/skill clear`) |
| "Read clara_prompts.py then review app.py" | Your own custom prompt file | Unlimited | No (one-shot) |

**Commands** = quick one-shot shortcuts (good enough for most tasks).
**Skills** = persistent behavior change (full checklists, stays active across messages).
**Custom prompts** = your own files (deepest, most flexible).

### Using Skills (if skills/ folder is present)

```
/skill use review            ← load review checklist (active until cleared)
review app.py                ← agent follows full 83-line checklist
review utils.py              ← still following same checklist
/skill clear                 ← deactivate

/skill use verify            ← load 6-phase verification
verify this project          ← runs build, types, lint, tests, security, diff

/skill use coding-standards  ← load KISS/DRY/YAGNI rules
fix app.py                   ← agent applies standards while fixing
/skill clear                 ← deactivate
```

### Available Skills

| Skill | Lines | What it does |
|-------|-------|-------------|
| `review` | 83 | 5-category code review (security/quality/performance/architecture/testing) with severity ratings |
| `verify` | 147 | 6-phase verification with actual shell commands per language + structured report |
| `coding-standards` | 153 | KISS, DRY, YAGNI, naming conventions, function design, error handling |
| `report` | 45 | Report generation workflow (chart-first, then Word/PDF) |

Skills are optional — the agent works without them. Commands cover the same categories with less detail.

## Config

Default config is set in Cell 3 (before launch). Change model, temperature, thinking mode anytime in the chatbot UI during use.

Key security settings (Cell 3):
- `aws_bedrock_only = True` — blocks all AWS except Bedrock
- `session_cost_limit = 1.0` — max $1 per session
- `require_tool_approval = True` — approve/deny before execution

