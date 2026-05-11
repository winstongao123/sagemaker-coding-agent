import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from entry import CONFIG, _apply_notebook_config, _make_notebook_controls


def test_chat_notebook_launcher_cells_stay_thin():
    nb = json.loads((ROOT / "chat.ipynb").read_text(encoding="utf-8"))
    config_cell = "".join(nb["cells"][2]["source"])
    launch_cell = "".join(nb["cells"][3]["source"])

    assert len(config_cell.splitlines()) <= 20
    assert len(launch_cell.splitlines()) <= 10
    assert "launch_config_ui" in config_cell
    assert "launch_chat_ui" in launch_cell
    assert "def _ensure_sageagent_path" not in config_cell + launch_cell
    assert "display(ui.render())" not in config_cell + launch_cell
    assert "render_parts" not in config_cell + launch_cell


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


if __name__ == "__main__":
    test_chat_notebook_launcher_cells_stay_thin()
    test_notebook_config_helper_applies_console_safe_defaults()
    print("notebook thin launcher smoke: OK")
