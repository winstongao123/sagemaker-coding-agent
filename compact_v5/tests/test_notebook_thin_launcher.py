import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import entry
from entry import (
    CONFIG,
    _apply_notebook_config,
    _make_notebook_controls,
    launch_config_ui,
    launch_chat_ui,
    launch_ui,
)
from ui.chat_ui import V4WidgetChatUI


def test_chat_notebook_launcher_cells_stay_thin():
    nb = json.loads((ROOT / "chat.ipynb").read_text(encoding="utf-8"))
    launch_cell = "".join(nb["cells"][2]["source"])

    assert len(launch_cell.splitlines()) <= 20
    assert "launch_ui" in launch_cell
    assert "launch_config_ui" not in launch_cell
    assert "launch_chat_ui" not in launch_cell
    assert "def _ensure_sageagent_path" not in launch_cell
    assert "display(ui.render())" not in launch_cell
    assert "render_parts" not in launch_cell


def test_notebook_dependency_cell_does_not_mutate_widget_stack():
    nb = json.loads((ROOT / "chat.ipynb").read_text(encoding="utf-8"))
    install_cell = "".join(nb["cells"][1]["source"])

    assert "!pip install" in install_cell
    assert "import ipywidgets as widgets" in install_cell
    assert "boto3" in install_cell
    assert "Pillow" in install_cell

    pip_lines = [
        line
        for line in install_cell.splitlines()
        if line.strip().startswith("!pip install")
    ]
    assert pip_lines, "Cell 1 must keep the runtime dependency install line"
    for line in pip_lines:
        assert "ipywidgets" not in line
        assert "jupyterlab_widgets" not in line
        assert "widgetsnbextension" not in line


def test_notebook_config_helper_applies_console_safe_defaults():
    controls = _make_notebook_controls(None)
    controls["workspace"].value = "workspace-x"
    controls["mock_mode"].value = True
    controls["thinking"].value = False
    controls["bedrock_only"].value = True
    state = SimpleNamespace(controls=controls)

    old = {
        "model_id": CONFIG.model_id,
        "workspace": CONFIG.workspace,
        "mock_mode": CONFIG.mock_mode,
        "thinking_enabled": CONFIG.thinking_enabled,
        "aws_bedrock_only": CONFIG.aws_bedrock_only,
    }
    try:
        _apply_notebook_config(state)
        assert CONFIG.workspace == "workspace-x"
        assert CONFIG.mock_mode is True
        assert CONFIG.thinking_enabled is False
        assert CONFIG.aws_bedrock_only is True
    finally:
        for name, value in old.items():
            setattr(CONFIG, name, value)


def test_notebook_launch_defaults_to_v4_widget_ui():
    captured = {}
    old_factory = entry.create_chat_ui
    old = {
        "model_id": CONFIG.model_id,
        "workspace": CONFIG.workspace,
        "mock_mode": CONFIG.mock_mode,
        "thinking_enabled": CONFIG.thinking_enabled,
        "aws_bedrock_only": CONFIG.aws_bedrock_only,
    }

    def fake_create_chat_ui(**kwargs):
        captured.update(kwargs)
        return "widget-ui"

    try:
        state = SimpleNamespace(controls=_make_notebook_controls(None), use_widgets=True)
        entry.create_chat_ui = fake_create_chat_ui
        assert launch_chat_ui(state) == "widget-ui"
        assert captured["force_console"] is False
    finally:
        entry.create_chat_ui = old_factory
        for name, value in old.items():
            setattr(CONFIG, name, value)


def test_combined_launch_ui_defaults_to_v4_widget_ui():
    captured = {}
    old_factory = entry.create_chat_ui
    old = {
        "model_id": CONFIG.model_id,
        "workspace": CONFIG.workspace,
        "mock_mode": CONFIG.mock_mode,
        "thinking_enabled": CONFIG.thinking_enabled,
        "aws_bedrock_only": CONFIG.aws_bedrock_only,
        "max_turns": CONFIG.max_turns,
        "max_iteration_budget": CONFIG.max_iteration_budget,
    }

    def fake_create_chat_ui(**kwargs):
        captured.update(kwargs)
        return "combined-widget-ui"

    try:
        entry.create_chat_ui = fake_create_chat_ui
        assert launch_ui(use_widgets=True, workspace="workspace-y", max_turns=120) == "combined-widget-ui"
        assert captured["force_console"] is False
        assert CONFIG.workspace == "workspace-y"
        assert CONFIG.max_turns == 120
    finally:
        entry.create_chat_ui = old_factory
        for name, value in old.items():
            setattr(CONFIG, name, value)


def test_notebook_console_fallback_is_explicit_opt_in():
    captured = {}
    old_factory = entry.create_chat_ui
    old = {
        "model_id": CONFIG.model_id,
        "workspace": CONFIG.workspace,
        "mock_mode": CONFIG.mock_mode,
        "thinking_enabled": CONFIG.thinking_enabled,
        "aws_bedrock_only": CONFIG.aws_bedrock_only,
    }

    def fake_create_chat_ui(**kwargs):
        captured.update(kwargs)
        return "console-ui"

    try:
        state = launch_config_ui(use_widgets=False)
        assert state.use_widgets is False
        entry.create_chat_ui = fake_create_chat_ui
        assert launch_chat_ui(state) == "console-ui"
        assert captured["force_console"] is True
    finally:
        entry.create_chat_ui = old_factory
        for name, value in old.items():
            setattr(CONFIG, name, value)


def test_notebook_control_defaults_match_production_docs():
    controls = _make_notebook_controls(None)

    assert controls["mock_mode"].value is False
    assert controls["thinking"].value is False
    assert controls["bedrock_only"].value is True
    assert controls["workspace"].value == "."
    assert controls["max_turns"].value == 60
    assert controls["iteration_budget"].value == 600


def test_notebook_overrides_accept_numeric_values():
    controls = _make_notebook_controls(None)

    entry._apply_control_overrides(
        controls,
        {"temperature": 0.3, "thinking_budget": 8192},
    )

    assert controls["temperature"].value == "0.3 - Low creativity"
    assert controls["thinking_budget"].value == "8192 - Extended"


def test_notebook_invalid_numeric_overrides_are_ignored():
    controls = _make_notebook_controls(None)

    entry._apply_control_overrides(
        controls,
        {"temperature": 0.6, "thinking_budget": 5000},
    )

    assert controls["temperature"].value == "0.0 - Deterministic"
    assert controls["thinking_budget"].value == "4096 - Standard"


def test_launch_chat_ui_explicit_widget_override_is_honored():
    captured = {}
    old_factory = entry.create_chat_ui
    old = {
        "model_id": CONFIG.model_id,
        "workspace": CONFIG.workspace,
        "mock_mode": CONFIG.mock_mode,
        "thinking_enabled": CONFIG.thinking_enabled,
        "aws_bedrock_only": CONFIG.aws_bedrock_only,
    }

    def fake_create_chat_ui(**kwargs):
        captured.update(kwargs)
        return "widget-ui"

    try:
        state = launch_config_ui()
        entry.create_chat_ui = fake_create_chat_ui
        assert launch_chat_ui(state, use_widgets=True) == "widget-ui"
        assert captured["force_console"] is False
    finally:
        entry.create_chat_ui = old_factory
        for name, value in old.items():
            setattr(CONFIG, name, value)


def test_combined_ui_mock_mode_toggle_rebuilds_real_client_when_disabled():
    class FakeClient:
        def __init__(self):
            self.mock_mode = False
            self.client = object()
            self.rebuild_count = 0

        def _rebuild_bedrock_client(self):
            self.rebuild_count += 1
            self.client = object()
            return True

    fake_client = FakeClient()
    ui = V4WidgetChatUI.__new__(V4WidgetChatUI)
    ui.agent = SimpleNamespace(client=fake_client)
    ui._render_status = lambda: None
    ui._append_message = lambda *args, **kwargs: None

    old_mock = CONFIG.mock_mode
    try:
        ui._on_mock_mode_change({"new": True})
        assert CONFIG.mock_mode is True
        assert fake_client.mock_mode is True
        assert fake_client.client is None

        ui._on_mock_mode_change({"new": False})
        assert CONFIG.mock_mode is False
        assert fake_client.mock_mode is False
        assert fake_client.rebuild_count == 1
        assert fake_client.client is not None
    finally:
        CONFIG.mock_mode = old_mock


if __name__ == "__main__":
    test_chat_notebook_launcher_cells_stay_thin()
    test_notebook_dependency_cell_does_not_mutate_widget_stack()
    test_notebook_config_helper_applies_console_safe_defaults()
    test_notebook_launch_defaults_to_v4_widget_ui()
    test_combined_launch_ui_defaults_to_v4_widget_ui()
    test_notebook_console_fallback_is_explicit_opt_in()
    test_notebook_control_defaults_match_production_docs()
    test_notebook_overrides_accept_numeric_values()
    test_notebook_invalid_numeric_overrides_are_ignored()
    test_launch_chat_ui_explicit_widget_override_is_honored()
    test_combined_ui_mock_mode_toggle_rebuilds_real_client_when_disabled()
    print("notebook thin launcher smoke: OK")
