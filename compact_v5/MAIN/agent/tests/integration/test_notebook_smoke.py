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


def test_bedrock_models_keep_v4_default_and_dropdown_options():
    from entry import BEDROCK_MODELS

    labels = [label for label, _mid in BEDROCK_MODELS]
    model_ids = [mid for _label, mid in BEDROCK_MODELS]

    assert BEDROCK_MODELS[0] == (
        "Claude 4.5 Sonnet (AU) - default",
        "au.anthropic.claude-sonnet-4-5-20250929-v1:0",
    )
    assert "au.anthropic.claude-haiku-4-5-20251001-v1:0" in model_ids
    assert "au.anthropic.claude-sonnet-4-6" in model_ids
    assert "Claude 4.6 Opus (AU)" in labels


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


def test_widget_status_shows_cache_savings_and_subagent_attribution():
    from ui.chat_ui import V4WidgetChatUI, _IPYWIDGETS_OK
    if not _IPYWIDGETS_OK:
        pytest.skip("ipywidgets not installed")
    from agent import Agent
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    from tools.todo import restore_todos

    TOKENS.reset()
    restore_todos([
        {
            "content": "Review subagent evidence",
            "status": "in_progress",
            "activeForm": "Reviewing subagent evidence",
        }
    ])
    client = BedrockClient(model_id=CONFIG.model_id, region=CONFIG.region, mock_mode=True)
    ui = V4WidgetChatUI(Agent(client=client))
    TOKENS.add(
        {
            "input_tokens": 1000,
            "output_tokens": 200,
            "cache_read_input_tokens": 100,
            "cache_creation_input_tokens": 50,
        },
        model_id=CONFIG.model_id,
        agent_kind="parent",
    )
    TOKENS.add(
        {
            "input_tokens": 500,
            "output_tokens": 100,
            "cache_read_input_tokens": 40,
            "cache_creation_input_tokens": 20,
        },
        model_id=CONFIG.model_id,
        agent_kind="review",
    )

    ui._render_status()
    html = ui._tokens_html.value
    assert "Cache R/W 140/70" in html
    assert "Saved $0." in html
    assert "Saved:" in html
    assert "Without cache:" in html
    assert "Reasoning: Thinking" in html
    assert "Agents: parent" in html
    assert "review $" in html
    assert "cache 40/20" in html
    assert "Reasoning: Thinking" in ui._mode_html.value
    assert "Todos (1/1 active)" in ui._todo_display.value


def test_task_tool_streams_subagent_lifecycle_to_output_fn(monkeypatch):
    from tools import task as task_tool

    class FakeResult:
        text = "review complete"
        stop_reason = "end_turn"
        turns_used = 2
        error = ""
        token_delta = {
            "cost_usd": 0.0123,
            "cache_read_tokens": 40,
            "cache_write_tokens": 20,
        }
        child_session_id = "child-1"

        def to_envelope(self):
            return {
                "schema": "sageagent.subagent_result.v1",
                "stop_reason": self.stop_reason,
            }

    def fake_spawn_subagent(**kwargs):
        kwargs["output_fn"]("[child says hello]")
        return FakeResult()

    monkeypatch.setattr("subagent.spawn.spawn_subagent", fake_spawn_subagent)
    outputs = []
    result = task_tool._task_executor(
        {
            "prompt": "Review the package",
            "subagent_type": "review",
            "description": "final review",
        },
        context={"parent_engine": object(), "output_fn": outputs.append},
    )

    assert outputs[0] == "[subagent:review] started: final review"
    assert "[child says hello]" in outputs
    assert outputs[-1] == "[subagent:review] finished: stop=end_turn turns=2 cost=$0.0123 cache=40/20"
    assert "review complete" in result


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


def test_chat_ipynb_has_v4_style_model_dropdown_and_sydney_default():
    import json
    nb_path = os.path.join(_AGENT_ROOT, "chat.ipynb")
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    sources_concat = "\n".join("".join(c.get("source", [])) for c in nb["cells"])

    assert "model_dropdown = widgets.Dropdown" in sources_concat
    assert "options=list(AVAILABLE_MODELS.keys())" in sources_concat
    assert 'REGION = "ap-southeast-2"' in sources_concat
    assert "default_model_name" in sources_concat
    assert "CONFIG.model_id = AVAILABLE_MODELS[_value(model_dropdown)]" in sources_concat


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


def _v4_widget_ui_or_skip():
    try:
        import ipywidgets  # noqa: F401
    except Exception:
        pytest.skip("ipywidgets not available")
    from agent import Agent
    from runtime.bedrock_client import BedrockClient
    from ui.chat_ui import V4WidgetChatUI

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    return V4WidgetChatUI(Agent(client=client))


def test_v4_style_ui_plan_and_auto_compact_toggles_drive_agent_state():
    ui = _v4_widget_ui_or_skip()

    ui._plan_mode.value = True
    assert ui.agent.plan_mode is True
    assert "Plan: ON" in ui._mode_html.value

    ui._auto_compact.value = False
    assert ui.agent.auto_compact_enabled is False
    assert "Auto-Compact: OFF" in ui._mode_html.value


def test_v4_style_ui_subagent_model_overrides_match_v4_contract(monkeypatch):
    ui = _v4_widget_ui_or_skip()
    from entry import BEDROCK_MODELS
    from runtime.config import CONFIG

    monkeypatch.setattr(CONFIG, "agent_overrides", {})
    ui._subagent_toggle.value = True
    assert ui._subagent_panel.layout.display != "none"
    assert list(ui._subagent_model_dropdowns) == ["explore", "review", "general", "build", "plan"]
    for dropdown in ui._subagent_model_dropdowns.values():
        assert dropdown.options[0] == ("Same as main", "")
        assert list(dropdown.options[1:]) == list(BEDROCK_MODELS)

    target = BEDROCK_MODELS[-1][1]
    ui._subagent_model_dropdowns["review"].value = target
    assert CONFIG.agent_overrides["review"]["model"] == target

    ui._subagent_model_dropdowns["review"].value = ""
    assert "review" not in CONFIG.agent_overrides


def test_v4_style_ui_subagent_model_overrides_do_not_pollute_dynamic_prompt(monkeypatch):
    from agent import Agent
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG

    captured = {}
    monkeypatch.setattr(CONFIG, "agent_overrides", {"review": {"model": "child-model"}})
    agent = Agent(
        client=BedrockClient(model_id="parent-model", region="us-east-1", mock_mode=True),
    )

    def fake_engine_run(**kwargs):
        captured.update(kwargs)
        from core.query_engine import QueryResult
        return QueryResult(text="ok", messages=[], stop_reason="end_turn", turns_used=0)

    agent._engine.run = fake_engine_run
    agent.run("do normal work", tools=[])

    assert "Notebook UI Sub-Agent Preferences" not in captured["system_prompt"]
    assert captured["system_prompt"].count("# === DYNAMIC ===") == 1


def test_v4_style_ui_state_blocks_keep_one_boundary(monkeypatch):
    import importlib
    from agent import Agent
    from runtime.bedrock_client import BedrockClient

    captured = {}
    agent_mod = importlib.import_module(Agent.__module__)
    monkeypatch.setattr(
        agent_mod,
        "_load_agent_state_context_blocks",
        lambda: ["## Handoff: AGENT_STATUS\n\nphase: ui test"],
    )
    agent = Agent(
        client=BedrockClient(model_id="x", region="us-east-1", mock_mode=True),
    )

    def fake_engine_run(**kwargs):
        captured.update(kwargs)
        from core.query_engine import QueryResult
        return QueryResult(text="ok", messages=[], stop_reason="end_turn", turns_used=0)

    agent._engine.run = fake_engine_run
    agent.run("go", tools=[])

    assert "## Handoff: AGENT_STATUS" in captured["system_prompt"]
    assert captured["system_prompt"].count("# === DYNAMIC ===") == 1


def test_v4_style_ui_custom_prompt_without_boundary_gets_one_boundary():
    from agent import Agent
    from runtime.bedrock_client import BedrockClient

    captured = {}
    agent = Agent(
        client=BedrockClient(model_id="x", region="us-east-1", mock_mode=True),
        system_prompt="custom system prompt without boundary",
    )

    def fake_engine_run(**kwargs):
        captured.update(kwargs)
        from core.query_engine import QueryResult
        return QueryResult(text="ok", messages=[], stop_reason="end_turn", turns_used=0)

    agent._engine.run = fake_engine_run
    agent.run("go", tools=[])

    assert captured["system_prompt"].count("# === DYNAMIC ===") == 0


def test_v4_style_ui_model_dropdown_updates_config_and_live_client(monkeypatch):
    ui = _v4_widget_ui_or_skip()
    from runtime.config import CONFIG

    monkeypatch.setattr(CONFIG, "model_id", "before")
    target = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
    ui._model_dropdown.value = target

    assert CONFIG.model_id == target
    assert ui.agent.client.model_id == target


def test_v4_style_ui_render_rebuilds_fresh_widget_models_after_first_display():
    """SageMaker/Jupyter can retain stale widget-view state across reruns.
    The v5 UI must be able to hand the frontend a fresh model tree when
    display(ui.render()) is called again, instead of reusing stale model IDs.
    """
    ui = _v4_widget_ui_or_skip()

    first = ui.render()
    first_model_id = getattr(first, "model_id", "")
    second = ui.render()
    second_model_id = getattr(second, "model_id", "")

    assert first_model_id
    assert second_model_id
    assert second is not first
    assert second_model_id != first_model_id
    assert "Cache R/W" in ui._tokens_html.value
    assert "Reasoning: Thinking" in ui._tokens_html.value


def test_v4_style_ui_removes_dead_approval_and_ask_user_placeholders(monkeypatch):
    ui = _v4_widget_ui_or_skip()
    from runtime.config import CONFIG
    monkeypatch.setattr(CONFIG, "require_tool_approval", True)

    assert not hasattr(ui, "_approval_box")
    assert not hasattr(ui, "_ask_user_box")
    # Real approval UI remains separate in ui.approval_dialog and the visible
    # Require Approval checkbox still drives CONFIG.require_tool_approval.
    ui._approval_toggle.value = False
    assert CONFIG.require_tool_approval is False


def test_v4_style_ui_clean_removes_traces_but_keeps_sessions(tmp_path, monkeypatch):
    ui = _v4_widget_ui_or_skip()
    from runtime.config import CONFIG

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "audit_dir", str(tmp_path / "audit_logs"))
    for path in (
        tmp_path / "audit_logs",
        tmp_path / ".snapshots",
        tmp_path / ".code_index",
        tmp_path / "truncated_outputs",
        tmp_path / ".sageagent_state",
        tmp_path / ".sageagent_sessions",
    ):
        path.mkdir()
    (tmp_path / ".exec_budget.json").write_text("{}", encoding="utf-8")

    ui._on_clean(None)

    assert not (tmp_path / "audit_logs").exists()
    assert not (tmp_path / ".snapshots").exists()
    assert not (tmp_path / ".exec_budget.json").exists()
    assert (tmp_path / ".sageagent_sessions").exists()
    assert any("sessions kept" in msg for _role, msg, _ts in ui._messages)


def test_v4_style_ui_compact_button_uses_compactor_and_replaces_messages(monkeypatch):
    ui = _v4_widget_ui_or_skip()
    from core.compactor import Compactor

    ui.agent.replace_messages([
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "second"},
    ])
    calls = {"compact": 0, "replace": 0}

    monkeypatch.setattr(
        Compactor,
        "flush_memories_before_compact",
        classmethod(lambda cls, messages, **_kwargs: None),
    )
    monkeypatch.setattr(
        Compactor,
        "prune_tool_outputs",
        classmethod(lambda cls, messages, max_tokens: (list(messages), 0)),
    )
    monkeypatch.setattr(
        Compactor,
        "create_llm_summary",
        classmethod(lambda cls, client, messages: "summary"),
    )

    def fake_compact(cls, messages, summary):
        calls["compact"] += 1
        return [{"role": "user", "content": f"compacted:{summary}"}]

    monkeypatch.setattr(Compactor, "compact", classmethod(fake_compact))
    monkeypatch.setattr(
        Compactor,
        "create_post_compact_file_attachments",
        classmethod(lambda cls: []),
    )
    monkeypatch.setattr(
        Compactor,
        "create_skill_attachment_if_needed",
        classmethod(lambda cls, skill_manager=None: None),
    )
    monkeypatch.setattr(
        Compactor,
        "run_post_compact_cleanup",
        classmethod(lambda cls, skill_manager=None: {}),
    )

    original_replace = ui.agent.replace_messages

    def tracked_replace(messages):
        calls["replace"] += 1
        original_replace(messages)

    ui.agent.replace_messages = tracked_replace
    ui._on_compact(None)

    assert calls == {"compact": 1, "replace": 1}
    assert ui.agent.messages == [{"role": "user", "content": "compacted:summary"}]
    assert any("Compacted:" in msg for _role, msg, _ts in ui._messages)


def test_v4_style_ui_session_buttons_dispatch_expected_commands(monkeypatch):
    ui = _v4_widget_ui_or_skip()
    commands = []

    monkeypatch.setattr(
        ui,
        "_dispatch_ui_command",
        lambda command: commands.append(command),
    )

    ui._session_name.value = "demo"
    ui._save_btn.click()
    ui._session_dropdown.options = [("demo", "session-1")]
    ui._session_dropdown.value = "session-1"
    ui._load_btn.click()

    assert commands == ["/save demo", "/resume session-1"]
