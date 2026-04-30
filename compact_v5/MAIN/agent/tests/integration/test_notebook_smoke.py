"""Phase 11 smoke test: chat.ipynb executes a hello-world turn against mock Bedrock.

Phase 11 acceptance (V5_PLAN.md §Phase 11): "notebook executes hello-world
turn against mock Bedrock."

Locks PORT_LOG #030-#034 (Phase 11 surface). Does NOT exercise ipywidgets
rendering directly (that requires a real Jupyter); instead asserts:
- entry.py imports cleanly
- create_chat_ui returns a usable handle
- ConsoleChatUI.send() against mock Bedrock returns text
- IterationBudgetWidget tracks consumption after run
- ThinkingBudgetWidget reflects agent state

Acceptance test for the smoke gate: `test_hello_world_turn_via_console_ui`.
"""
from __future__ import annotations

import os
import sys

import pytest

_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


@pytest.fixture(autouse=True)
def fresh_registry():
    from tools.registry import _reset_registry_for_tests
    from tools import bootstrap_built_ins
    _reset_registry_for_tests()
    bootstrap_built_ins()
    yield


# ============================================================
# Test 1 — entry.py public surface imports
# ============================================================

def test_entry_module_re_exports_public_surface():
    """`from entry import Agent, create_chat_ui, CONFIG, BEDROCK_MODELS` —
    the cell-0 import line in chat.ipynb. Must work cleanly without errors."""
    import entry
    assert hasattr(entry, "Agent")
    assert hasattr(entry, "create_chat_ui")
    assert hasattr(entry, "CONFIG")
    assert hasattr(entry, "BEDROCK_MODELS")
    assert hasattr(entry, "SkillManager")
    assert hasattr(entry, "IterationBudget")


def test_bedrock_models_list_is_well_formed():
    from entry import BEDROCK_MODELS
    assert isinstance(BEDROCK_MODELS, list)
    assert len(BEDROCK_MODELS) >= 1
    for label, mid in BEDROCK_MODELS:
        assert isinstance(label, str) and label
        assert isinstance(mid, str) and mid


# ============================================================
# Test 2 — Agent class basic behavior
# ============================================================

def test_agent_constructs_via_mock_client():
    from agent import Agent
    from runtime.bedrock_client import BedrockClient
    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    assert a.client is client
    assert a.budget.total() > 0


def test_agent_run_returns_query_result_with_mock_bedrock():
    """The smoke gate. Phase 11 acceptance lock."""
    from agent import Agent
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    result = a.run("hello world")
    # Mock Bedrock for "hello world" returns a `[MOCK] Received: ...` text
    assert result.text
    assert result.stop_reason in ("end_turn", "tool_use", "max_turns")


def test_agent_clear_resets_messages():
    from agent import Agent
    from runtime.bedrock_client import BedrockClient
    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    a.run("hi")
    assert len(a.messages) > 0
    a.clear()
    assert a.messages == []


def test_agent_clear_preserves_budget_by_default():
    """clear() does NOT reset budget unless `reset_budget=True`."""
    from agent import Agent
    from runtime.bedrock_client import BedrockClient
    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    a.run("hi")
    used_before = a.budget.used()
    assert used_before >= 1
    a.clear()
    assert a.budget.used() == used_before
    a.clear(reset_budget=True)
    assert a.budget.used() == 0


def test_agent_set_thinking_updates_state():
    from agent import Agent
    from runtime.bedrock_client import BedrockClient
    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    assert a.thinking_enabled is False
    a.set_thinking(enabled=True, budget=8192)
    assert a.thinking_enabled is True
    assert a.thinking_budget == 8192


# ============================================================
# Test 3 — create_chat_ui factory
# ============================================================

def test_create_chat_ui_returns_handle_with_agent():
    from ui.chat_ui import create_chat_ui, ConsoleChatUI, WidgetChatUI
    from agent import Agent
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    ui = create_chat_ui(agent=a)
    assert ui is not None
    assert ui.agent is a
    # Either ConsoleChatUI (no ipywidgets) OR WidgetChatUI (ipywidgets present)
    assert isinstance(ui, (ConsoleChatUI, WidgetChatUI))


def test_create_chat_ui_lazy_path_via_config(monkeypatch):
    """When called without an agent, factory builds one from CONFIG."""
    from ui.chat_ui import create_chat_ui
    from runtime.config import CONFIG

    monkeypatch.setattr(CONFIG, "mock_mode", True)
    ui = create_chat_ui()
    assert ui is not None
    assert ui.agent is not None


# ============================================================
# Test 4 — ConsoleChatUI smoke (Phase 11 acceptance)
# ============================================================

def test_hello_world_turn_via_console_ui(monkeypatch):
    """**Phase 11 acceptance**: ConsoleChatUI.send('hello world') returns
    text against mock Bedrock without raising. This is the smoke gate
    that V5_PLAN.md §Phase 11 calls out."""
    from ui.chat_ui import ConsoleChatUI
    from agent import Agent
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    ui = ConsoleChatUI(a)
    out = ui.send("hello world")
    assert isinstance(out, str)
    assert out  # non-empty
    # And the budget consumed at least one iteration
    assert a.budget.used() >= 1


# ============================================================
# Test 5 — IterationBudgetWidget tracks consumption (PS Issue #2)
# ============================================================

def test_iteration_budget_widget_html_reflects_consumption():
    from ui.widgets import IterationBudgetWidget
    from core import IterationBudget

    b = IterationBudget(max_iterations=10)
    w = IterationBudgetWidget(budget=b)
    html_initial = w.render_html()
    assert "0/10" in html_initial
    b.consume(); b.consume(); b.consume()
    html_after = w.render_html()
    assert "3/10" in html_after


def test_iteration_budget_widget_render_returns_handle():
    """When ipywidgets is available, render() returns the IntProgress;
    otherwise returns the HTML fallback string. Both are truthy."""
    from ui.widgets import IterationBudgetWidget
    from core import IterationBudget

    w = IterationBudgetWidget(budget=IterationBudget(max_iterations=5))
    handle = w.render()
    assert handle is not None


# ============================================================
# Test 6 — ThinkingBudgetWidget surfaces agent state (PS Issue #4)
# ============================================================

def test_thinking_budget_widget_html_shows_state():
    from ui.widgets import ThinkingBudgetWidget
    from agent import Agent
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client, thinking_enabled=True, thinking_budget=8192)
    w = ThinkingBudgetWidget(agent=a)
    html = w.render_html()
    assert "ON" in html
    assert "8192" in html

    a.set_thinking(enabled=False)
    html2 = w.render_html()
    assert "OFF" in html2


# ============================================================
# Test 7 — chat.ipynb file is well-formed JSON with required cells
# ============================================================

def test_chat_ipynb_is_valid_notebook():
    """v5 must ship a chat.ipynb the user can open in Jupyter. Verify it's
    valid JSON with the expected cells: install / config / launch."""
    import json
    nb_path = os.path.join(_AGENT_ROOT, "chat.ipynb")
    if not os.path.exists(nb_path):
        pytest.skip(f"chat.ipynb not yet created at {nb_path}")
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    assert "cells" in nb
    assert isinstance(nb["cells"], list)
    assert len(nb["cells"]) >= 3, "chat.ipynb needs at least install / config / launch cells"
    # First code cell should reference pip install or import
    code_cells = [c for c in nb["cells"] if c.get("cell_type") == "code"]
    assert len(code_cells) >= 2
    # Some cell must import from `entry`
    sources_concat = "\n".join("".join(c.get("source", [])) for c in nb["cells"])
    assert "entry" in sources_concat or "create_chat_ui" in sources_concat


# ============================================================
# Test 8 — chat.md companion exists
# ============================================================

# ============================================================
# Codex Phase-11 fix locks
# ============================================================

def test_lazy_factory_threads_max_turns_and_budget(monkeypatch):
    """Codex Phase-11 finding (HIGH) lock: lazy `create_chat_ui()` must read
    `CONFIG.max_turns` + `CONFIG.max_iteration_budget` and pass them to
    Agent. Without this, notebook config changes never reach runtime."""
    from runtime.config import CONFIG
    from ui.chat_ui import create_chat_ui

    monkeypatch.setattr(CONFIG, "mock_mode", True)
    monkeypatch.setattr(CONFIG, "max_turns", 7)
    monkeypatch.setattr(CONFIG, "max_iteration_budget", 13)
    ui = create_chat_ui()
    # Agent should reflect the config-driven turn ceiling + budget total.
    assert ui.agent._engine.max_turns == 7
    assert ui.agent.budget.total() == 13


def test_console_ui_render_returns_html_object_when_ipython_available():
    """Codex Phase-11 finding (medium) lock: `ConsoleChatUI.render()` must
    return an `IPython.display.HTML` object so `display(ui.render())` in
    the notebook shows rendered HTML, not the literal string."""
    from ui.chat_ui import ConsoleChatUI
    from agent import Agent
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    ui = ConsoleChatUI(a)
    handle = ui.render()
    # In any environment that has IPython (test env does), it's an HTML
    # object — not a bare string.
    try:
        from IPython.display import HTML
        assert isinstance(handle, HTML), (
            f"render() returned {type(handle).__name__}, expected IPython.display.HTML"
        )
    except ImportError:
        # Pure-Python env without IPython — string is acceptable
        assert isinstance(handle, str)


def test_iteration_budget_widget_reflects_subagent_consumption():
    """Codex Phase-11 finding (medium) lock: PS Issue #2 contract — the
    widget must reflect the SHARED budget used across parent + sub-agents.
    Spawn a sub-agent and verify the parent's widget sees its consumption."""
    from agent import Agent
    from core import IterationBudget
    from runtime.bedrock_client import BedrockClient
    from subagent.spawn import spawn_subagent
    from ui.widgets import IterationBudgetWidget

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    parent = Agent(client=client, budget=IterationBudget(max_iterations=20))
    widget = IterationBudgetWidget(budget=parent.budget)

    # Pre-spawn: 0 used.
    assert "0/20" in widget.render_html()

    # Spawn a child via the same engine. The mock client returns end_turn
    # immediately so child uses 1 iteration.
    spawn_subagent(parent_engine=parent._engine, prompt="hi", agent_type="general")

    # Widget reflects the SHARED budget — sub-agent consumption shows up
    # in the parent's widget.
    html_after = widget.render_html()
    assert parent.budget.used() >= 1
    assert "0/20" not in html_after, (
        "widget did not update to reflect sub-agent's consumption of shared budget"
    )


def test_create_chat_ui_returns_console_when_ipywidgets_unavailable(monkeypatch):
    """Codex Phase-11 finding (medium) lock: the factory's branch selection
    is determined by `_IPYWIDGETS_OK`. Force-False to assert the fallback
    branch is reachable."""
    from ui import chat_ui as chat_mod
    from agent import Agent
    from runtime.bedrock_client import BedrockClient
    from ui.chat_ui import ConsoleChatUI

    monkeypatch.setattr(chat_mod, "_IPYWIDGETS_OK", False)
    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    ui = chat_mod.create_chat_ui(agent=a)
    assert isinstance(ui, ConsoleChatUI)


def test_chat_ipynb_kernelspec_and_entry_wiring():
    """Codex Phase-11 finding (low) lock: tighten chat.ipynb assertions —
    kernelspec must be python3 and the launch cell must import from `entry`."""
    import json
    nb_path = os.path.join(_AGENT_ROOT, "chat.ipynb")
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    ks = nb.get("metadata", {}).get("kernelspec", {})
    assert ks.get("name") == "python3", f"kernelspec.name={ks.get('name')!r}"
    assert ks.get("language") == "python"
    # At least one code cell explicitly imports create_chat_ui from entry.
    code_cells = [c for c in nb["cells"] if c.get("cell_type") == "code"]
    has_create_chat_ui_import = any(
        "from entry import create_chat_ui" in "".join(c.get("source", []))
        for c in code_cells
    )
    assert has_create_chat_ui_import, (
        "chat.ipynb launch cell must import `create_chat_ui` from `entry`"
    )


def test_chat_md_companion_exists():
    md_path = os.path.join(_AGENT_ROOT, "chat.md")
    if not os.path.exists(md_path):
        pytest.skip(f"chat.md not yet created at {md_path}")
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    assert text.strip()
    # Should reference the cell-0 import line + budget/thinking widgets
    low = text.lower()
    assert "chat.ipynb" in low or "notebook" in low
