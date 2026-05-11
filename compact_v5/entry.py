"""V5 entry.py — cell-0 import target for chat.ipynb (Phase 11, ADR-017).

Re-exports the public surface. Notebook cells should be able to:

    from entry import Agent, create_chat_ui, CONFIG, BEDROCK_MODELS

without knowing which subpackage owns each name.

Block B+ Codex finding #2 (MEDIUM) lock: import-boundary fail-closed
for v5.0.1 hard-constraint banned subsystems (#9 MCP, #10 streaming,
anthropic_api_direct). Any future code path that re-introduces them
will fail at import here.

PORT_LOG: see #031 + #032 (chat.ipynb wiring) + #056 (banned-subsystem guard).
"""
from __future__ import annotations

# ============================================================
# Banned-subsystem import-time guard (Block B+ — ADR-022 / PORT_LOG #056)
# ============================================================
#
# v5.0.1 hard constraints #9 + #10 forbid MCP and streaming. The guard
# below ACTIVELY checks whether a banned subsystem package has been
# re-introduced (e.g. someone added a `mcp/` package back). If so,
# importing entry.py — the v5 public surface — fails-closed at load.
# This is the import-boundary fail-closed contract from ADR-022 §
# Linked port-log row #051.
import importlib.util as _importlib_util
import os as _os

# Resolve the v5 agent package root (the directory containing entry.py).
# We compare candidate package origins against THIS path so external
# `mcp` installs (pip-installed) don't false-positive the guard.
_AGENT_PKG_ROOT = _os.path.dirname(_os.path.abspath(__file__))

_BANNED_PACKAGE_NAMES = ("mcp",)
for _banned in _BANNED_PACKAGE_NAMES:
    _spec = _importlib_util.find_spec(_banned)
    if _spec is None:
        continue
    _origin = getattr(_spec, "origin", "") or ""
    if not _origin:
        continue
    # Only raise when the spec resolves to a path INSIDE this v5 agent
    # package — i.e. someone re-introduced a `<v5_root>/mcp/` directory.
    # External pip-installed packages (site-packages, conda envs, etc.)
    # do not match this prefix and pass through silently.
    try:
        _origin_real = _os.path.realpath(_origin)
        _root_real = _os.path.realpath(_AGENT_PKG_ROOT)
    except OSError:
        continue
    if _origin_real.startswith(_root_real + _os.sep):
        raise ImportError(
            f"v5.0.1 hard constraint: banned subsystem '{_banned}' "
            f"has been re-introduced INSIDE the v5 agent package at "
            f"{_origin_real!r}. See runtime/feature_flags.py."
        )

# Public Agent class (Phase 11 — wraps Phase 1-10 modules)
from agent import Agent  # noqa: F401

# Config singleton + Bedrock model registry (Phase 1)
from runtime.config import CONFIG  # noqa: F401
from types import SimpleNamespace as _SimpleNamespace

# Optional Bedrock model list — kept as a module-level constant so the
# config widget in chat.ipynb cell 2 can populate a dropdown.
BEDROCK_MODELS = [
    ("Claude 4.5 Sonnet (AU) - default",
     "au.anthropic.claude-sonnet-4-5-20250929-v1:0"),
    ("Claude 4.5 Haiku (AU)",
     "au.anthropic.claude-haiku-4-5-20251001-v1:0"),
    ("Claude 4.6 Sonnet (AU)",
     "au.anthropic.claude-sonnet-4-6"),
    ("Claude 4.6 Opus (AU)",
     "au.anthropic.claude-opus-4-6-v1"),
    ("Claude 4.5 Opus (Global)",
     "global.anthropic.claude-opus-4-5-20251101-v1:0"),
    ("Claude 3.5 Sonnet v2",
     "anthropic.claude-3-5-sonnet-20241022-v2:0"),
    ("Claude 3.5 Sonnet",
     "anthropic.claude-3-5-sonnet-20240620-v1:0"),
    ("Claude 3 Haiku",
     "anthropic.claude-3-haiku-20240307-v1:0"),
    ("Claude 3 Sonnet",
     "anthropic.claude-3-sonnet-20240229-v1:0"),
]

# Chat UI factory (Phase 11)
from ui.chat_ui import create_chat_ui  # noqa: F401


# ============================================================
# Thin notebook launcher helpers
# ============================================================
#
# Keep chat.ipynb close to v4's user contract: the notebook should launch the
# app, not carry the implementation. These helpers own the v5 path/config
# plumbing that had drifted into long notebook cells.

_TEMPERATURE_OPTIONS = {
    "0.0 - Deterministic": 0.0,
    "0.3 - Low creativity": 0.3,
    "0.5 - Balanced": 0.5,
    "0.7 - High creativity": 0.7,
    "1.0 - Maximum creativity": 1.0,
}

_THINKING_BUDGET_OPTIONS = {
    "1024 - Minimal": 1024,
    "2048 - Light": 2048,
    "4096 - Standard": 4096,
    "8192 - Extended": 8192,
    "16000 - Maximum": 16000,
}

_NOTEBOOK_REGION = "ap-southeast-2"
_LAST_NOTEBOOK_CONFIG_UI = None


class _NotebookValue:
    def __init__(self, value):
        self.value = value


def _widget_value(widget_or_value):
    return getattr(widget_or_value, "value", widget_or_value)


def _label_for_model(model_id):
    for label, mid in BEDROCK_MODELS:
        if mid == model_id:
            return label
    return BEDROCK_MODELS[0][0]


def _make_notebook_controls(widgets=None):
    model_labels = [label for label, _ in BEDROCK_MODELS]
    default_model = _label_for_model(getattr(CONFIG, "model_id", BEDROCK_MODELS[0][1]))
    if default_model not in model_labels:
        default_model = model_labels[0]

    if widgets is None:
        return {
            "model": _NotebookValue(default_model),
            "temperature": _NotebookValue("0.0 - Deterministic"),
            "thinking_budget": _NotebookValue("4096 - Standard"),
            "max_turns": _NotebookValue(60),
            "iteration_budget": _NotebookValue(600),
            "workspace": _NotebookValue("."),
            "mock_mode": _NotebookValue(True),
            "thinking": _NotebookValue(False),
            "bedrock_only": _NotebookValue(True),
        }

    return {
        "model": widgets.Dropdown(
            options=model_labels,
            value=default_model,
            description="Model:",
            style={"description_width": "120px"},
            layout=widgets.Layout(width="520px"),
        ),
        "temperature": widgets.Dropdown(
            options=list(_TEMPERATURE_OPTIONS.keys()),
            value="0.0 - Deterministic",
            description="Temperature:",
            style={"description_width": "120px"},
            layout=widgets.Layout(width="360px"),
        ),
        "thinking_budget": widgets.Dropdown(
            options=list(_THINKING_BUDGET_OPTIONS.keys()),
            value="4096 - Standard",
            description="Thinking Budget:",
            style={"description_width": "120px"},
            layout=widgets.Layout(width="360px"),
        ),
        "max_turns": widgets.IntSlider(
            value=60,
            min=5,
            max=100,
            step=5,
            description="Max Turns:",
            style={"description_width": "120px"},
            layout=widgets.Layout(width="400px"),
        ),
        "iteration_budget": widgets.IntSlider(
            value=600,
            min=90,
            max=2000,
            step=50,
            description="Iter Budget:",
            style={"description_width": "120px"},
            layout=widgets.Layout(width="400px"),
        ),
        "workspace": widgets.Text(
            value=".",
            description="Workspace:",
            placeholder="Directory for file operations",
            style={"description_width": "120px"},
            layout=widgets.Layout(width="400px"),
        ),
        "mock_mode": widgets.Checkbox(
            value=False,
            description="Mock Mode (test without API)",
            indent=False,
        ),
        "thinking": widgets.Checkbox(
            value=False,
            description="Enable Extended Thinking (slower, uses more tokens)",
            indent=False,
        ),
        "bedrock_only": widgets.Checkbox(
            value=True,
            description="Bedrock-only (block S3, Lambda, Textract, etc.)",
            indent=False,
        ),
    }


def _apply_notebook_config(config_ui=None):
    controls = getattr(config_ui, "controls", None) or _make_notebook_controls(None)
    available_models = dict(BEDROCK_MODELS)
    CONFIG.model_id = available_models[_widget_value(controls["model"])]
    CONFIG.region = _NOTEBOOK_REGION
    CONFIG.workspace = _widget_value(controls["workspace"])
    CONFIG.max_turns = int(_widget_value(controls["max_turns"]))
    CONFIG.max_iteration_budget = int(_widget_value(controls["iteration_budget"]))
    CONFIG.mock_mode = bool(_widget_value(controls["mock_mode"]))
    CONFIG.temperature = _TEMPERATURE_OPTIONS[_widget_value(controls["temperature"])]
    CONFIG.thinking_enabled = bool(_widget_value(controls["thinking"]))
    CONFIG.thinking_budget = _THINKING_BUDGET_OPTIONS[_widget_value(controls["thinking_budget"])]
    CONFIG.require_tool_approval = True
    CONFIG.aws_bedrock_only = bool(_widget_value(controls["bedrock_only"]))
    CONFIG.session_cost_limit = 5.0
    CONFIG.enable_skill_auto_trigger = False
    return CONFIG


def launch_config_ui():
    """Display v4-style config controls and return a small config handle."""
    global _LAST_NOTEBOOK_CONFIG_UI

    try:
        import ipywidgets as widgets
        from IPython.display import HTML, display
    except Exception:
        controls = _make_notebook_controls(None)
        state = _SimpleNamespace(controls=controls)
        state.apply = lambda: _apply_notebook_config(state)
        state.apply()
        _LAST_NOTEBOOK_CONFIG_UI = state
        print(
            "ipywidgets unavailable; using console-safe defaults "
            f"(model={CONFIG.model_id}, mock_mode={CONFIG.mock_mode})."
        )
        return state

    controls = _make_notebook_controls(widgets)
    state = _SimpleNamespace(controls=controls)
    state.apply = lambda: _apply_notebook_config(state)
    state.apply()
    _LAST_NOTEBOOK_CONFIG_UI = state

    display(HTML("<h3>Agent Configuration</h3>"))
    config_box = widgets.VBox(
        [
            controls["model"],
            widgets.HTML(
                f"<p style='margin:5px 0;color:#888;'>"
                f"Region: Sydney ({_NOTEBOOK_REGION})</p>"
            ),
            controls["temperature"],
            controls["thinking"],
            controls["thinking_budget"],
            controls["workspace"],
            controls["max_turns"],
            controls["iteration_budget"],
            controls["mock_mode"],
            controls["bedrock_only"],
        ],
        layout=widgets.Layout(
            padding="10px",
            border="1px solid #444",
            margin="10px 0",
            background="#2d2d2d",
        ),
    )
    display(config_box)
    display(
        HTML(
            "<p style='color:#888;font-size:12px;'>"
            "Configure settings above, then run the next cell to start.</p>"
        )
    )
    return state


def launch_chat_ui(config_ui=None):
    """Apply notebook controls and launch the auto-displayed chat UI."""
    if config_ui is None:
        config_ui = _LAST_NOTEBOOK_CONFIG_UI
    _apply_notebook_config(config_ui)
    return create_chat_ui()

# Skill manager helper for power users who want to inspect / activate
# skills programmatically (Phase 10).
from skills.manager import SkillManager  # noqa: F401

# IterationBudget for power users + tests (Phase 8).
from core.budget import IterationBudget  # noqa: F401
