"""SOFTWARE-CHECKPOINT durable checkpoint tests."""
from __future__ import annotations

import json
import os
import sys


_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


def test_snapshot_index_survives_manager_restart(tmp_path):
    from runtime.snapshot import SnapshotManager

    target = tmp_path / "app.py"
    target.write_text("v1", encoding="utf-8")

    sm = SnapshotManager(workspace=str(tmp_path))
    sm.save(str(target))
    checkpoint = sm.create_checkpoint("alpha", [str(target)])

    index_path = tmp_path / ".snapshots" / "index.json"
    assert index_path.is_file()
    data = json.loads(index_path.read_text(encoding="utf-8"))
    assert data["schema"] == "sageagent.snapshots.v1"
    assert data["checkpoints"][0]["name"] == "alpha"
    assert checkpoint["entries"][0]["file"] == str(target)

    restarted = SnapshotManager(workspace=str(tmp_path))
    assert restarted.list_snapshots(str(target))
    assert restarted.list_checkpoints()[0]["name"] == "alpha"


def test_revert_requires_preview_before_single_file_mutation(tmp_path, monkeypatch):
    from commands import dispatch_command
    from runtime.config import CONFIG
    from runtime.snapshot import SnapshotManager
    import runtime.snapshot as snapshot_mod

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    sm = SnapshotManager(workspace=str(tmp_path))
    monkeypatch.setattr(snapshot_mod, "SNAPSHOTS", sm)

    target = tmp_path / "data.txt"
    target.write_text("v1", encoding="utf-8")
    sm.save(str(target))
    target.write_text("v2", encoding="utf-8")

    preview = dispatch_command(f"/revert {target}")
    assert "Preview only" in preview.text
    assert "--yes" in preview.text
    assert target.read_text(encoding="utf-8") == "v2"

    restored = dispatch_command(f"/revert {target} --yes")
    assert restored.side_effect == f"reverted:{target}"
    assert target.read_text(encoding="utf-8") == "v1"


def test_named_checkpoint_restore_requires_confirm_and_lists_after_restart(
    tmp_path,
    monkeypatch,
):
    from commands import dispatch_command
    from runtime.config import CONFIG
    from runtime.snapshot import SnapshotManager
    import runtime.snapshot as snapshot_mod

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    sm = SnapshotManager(workspace=str(tmp_path))
    monkeypatch.setattr(snapshot_mod, "SNAPSHOTS", sm)

    target = tmp_path / "service.py"
    target.write_text("v1", encoding="utf-8")
    sm.save(str(target))
    created = dispatch_command("/checkpoint create before-refactor")
    assert created.side_effect == "checkpoint:before-refactor"
    target.write_text("v2", encoding="utf-8")

    restarted = SnapshotManager(workspace=str(tmp_path))
    monkeypatch.setattr(snapshot_mod, "SNAPSHOTS", restarted)

    listed = dispatch_command("/checkpoint list")
    assert "before-refactor" in listed.text

    preview = dispatch_command("/checkpoint restore before-refactor")
    assert "Preview only" in preview.text
    assert str(target) in preview.text
    assert target.read_text(encoding="utf-8") == "v2"

    restored = dispatch_command("/checkpoint restore before-refactor --yes")
    assert restored.side_effect == "checkpoint_restored:before-refactor"
    assert target.read_text(encoding="utf-8") == "v1"
