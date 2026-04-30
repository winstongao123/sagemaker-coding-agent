"""Phase 04 unit tests: write_file / edit_file / notebook_edit / view_image.

Tests verify:
1. Each tool registers + has correct flags (is_read_only / is_destructive /
   requires_approval / is_concurrency_safe per ADR-010).
2. Each tool's executor handles happy-path + error cases.
3. write_file / edit_file enforce read-before-mutate (v4 parity).
4. edit_file's stale-check rejects edits if the file changed externally.
5. notebook_edit insert / replace / delete actions all work and are atomic.
6. view_image validates path + size + format.
"""
from __future__ import annotations

import json
import os
import sys
import time

import pytest

# Make `tools`/`runtime` importable from this test (mirrors flat-zip ship layout).
_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Point CONFIG.workspace at a tmpdir; clear allowed_paths; reset
    read-tracking so each test starts with a clean slate."""
    from runtime.config import CONFIG
    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "allowed_paths", [])
    monkeypatch.setattr(CONFIG, "max_file_size", 10 * 1024 * 1024)
    from tools import _file_read_tracking
    _file_read_tracking.reset_for_tests()
    return tmp_path


def _tool(name):
    from tools import find_tool_by_name, all_registered
    t = find_tool_by_name(all_registered(), name)
    assert t is not None, f"{name} not registered"
    return t


# ============================================================
# Registration + flags
# ============================================================

@pytest.mark.parametrize("name", ["write_file", "edit_file", "notebook_edit", "view_image"])
def test_phase4_tools_registered(name):
    t = _tool(name)
    assert t is not None


def test_phase4_mutator_flags():
    """write_file, edit_file, notebook_edit must be is_destructive=True,
    requires_approval=True, is_concurrency_safe=False."""
    for name in ("write_file", "edit_file", "notebook_edit"):
        t = _tool(name)
        assert t.is_read_only is False, f"{name} should be mutating"
        assert t.is_destructive is True, f"{name} should be destructive"
        assert t.is_concurrency_safe is False, f"{name} should NOT be concurrency-safe"
        assert t.requires_approval is True, f"{name} should require approval"


def test_view_image_flags():
    """view_image is read-only, no approval needed (just loads image bytes)."""
    t = _tool("view_image")
    assert t.is_read_only is True
    assert t.is_destructive is False
    assert t.is_concurrency_safe is True
    assert t.requires_approval is False


# ============================================================
# write_file
# ============================================================

def test_write_file_creates_new_file(workspace):
    t = _tool("write_file")
    target = workspace / "new.txt"
    out = t.execute({"file_path": str(target), "content": "hello"})
    assert "Written" in out
    assert target.read_text(encoding="utf-8") == "hello"


def test_write_file_overwrite_requires_prior_read(workspace):
    """v4 parity: overwriting an existing file requires read_file first."""
    t = _tool("write_file")
    target = workspace / "existing.txt"
    target.write_text("original", encoding="utf-8")
    out = t.execute({"file_path": str(target), "content": "replaced"})
    assert out.startswith("Error:")
    assert "read file before overwriting" in out.lower()
    # Original must NOT have changed
    assert target.read_text(encoding="utf-8") == "original"


def test_write_file_overwrite_after_read_succeeds(workspace):
    from tools import _file_read_tracking
    t = _tool("write_file")
    target = workspace / "existing.txt"
    target.write_text("original", encoding="utf-8")
    _file_read_tracking.mark_read(str(target))
    out = t.execute({"file_path": str(target), "content": "replaced"})
    assert "Written" in out
    assert target.read_text(encoding="utf-8") == "replaced"


def test_write_file_append_mode_no_read_required(workspace):
    """Append mode does NOT require a prior read (v4 parity)."""
    t = _tool("write_file")
    target = workspace / "log.txt"
    target.write_text("line 1\n", encoding="utf-8")
    out = t.execute({"file_path": str(target), "content": "line 2\n", "mode": "append"})
    assert "Written" in out
    assert target.read_text(encoding="utf-8") == "line 1\nline 2\n"


def test_write_file_outside_workspace_blocked(workspace):
    t = _tool("write_file")
    other = "C:/Windows/notepad_blocked.exe" if os.name == "nt" else "/etc/blocked"
    out = t.execute({"file_path": other, "content": "evil"})
    assert out.startswith("Error:")
    assert "outside workspace" in out


def test_write_file_creates_parent_directories(workspace):
    t = _tool("write_file")
    target = workspace / "deep" / "nested" / "file.txt"
    out = t.execute({"file_path": str(target), "content": "x"})
    assert "Written" in out
    assert target.exists()


def test_write_file_invalid_mode(workspace):
    t = _tool("write_file")
    target = workspace / "x.txt"
    out = t.execute({"file_path": str(target), "content": "x", "mode": "delete"})
    assert out.startswith("Error:")
    assert "mode must be" in out


def test_write_file_missing_args(workspace):
    t = _tool("write_file")
    out1 = t.execute({"content": "x"})
    assert out1.startswith("Error:")
    out2 = t.execute({"file_path": str(workspace / "x.txt")})
    assert out2.startswith("Error:")


# ============================================================
# edit_file
# ============================================================

def test_edit_file_happy_path(workspace):
    from tools import _file_read_tracking
    t = _tool("edit_file")
    target = workspace / "code.py"
    target.write_text("def hello():\n    pass\n", encoding="utf-8")
    _file_read_tracking.mark_read(str(target))
    out = t.execute({
        "file_path": str(target),
        "old_string": "def hello():",
        "new_string": "def world():",
    })
    assert "Edited" in out
    assert target.read_text(encoding="utf-8") == "def world():\n    pass\n"


def test_edit_file_requires_prior_read(workspace):
    t = _tool("edit_file")
    target = workspace / "code.py"
    target.write_text("def hello():\n    pass\n", encoding="utf-8")
    out = t.execute({
        "file_path": str(target),
        "old_string": "hello",
        "new_string": "world",
    })
    assert out.startswith("Error:")
    assert "read file before editing" in out.lower()


def test_edit_file_old_string_not_found(workspace):
    from tools import _file_read_tracking
    t = _tool("edit_file")
    target = workspace / "code.py"
    target.write_text("aaa", encoding="utf-8")
    _file_read_tracking.mark_read(str(target))
    out = t.execute({
        "file_path": str(target),
        "old_string": "missing",
        "new_string": "x",
    })
    assert out.startswith("Error:")
    assert "not found" in out.lower()


def test_edit_file_old_string_not_unique_requires_replace_all(workspace):
    from tools import _file_read_tracking
    t = _tool("edit_file")
    target = workspace / "code.py"
    target.write_text("a\nb\na\n", encoding="utf-8")
    _file_read_tracking.mark_read(str(target))
    out = t.execute({
        "file_path": str(target),
        "old_string": "a",
        "new_string": "X",
    })
    assert out.startswith("Error:")
    assert "appears 2 times" in out


def test_edit_file_replace_all(workspace):
    from tools import _file_read_tracking
    t = _tool("edit_file")
    target = workspace / "code.py"
    target.write_text("a\nb\na\n", encoding="utf-8")
    _file_read_tracking.mark_read(str(target))
    out = t.execute({
        "file_path": str(target),
        "old_string": "a",
        "new_string": "X",
        "replace_all": True,
    })
    assert "Edited" in out
    assert target.read_text(encoding="utf-8") == "X\nb\nX\n"


def test_edit_file_identical_strings_rejected(workspace):
    from tools import _file_read_tracking
    t = _tool("edit_file")
    target = workspace / "code.py"
    target.write_text("foo", encoding="utf-8")
    _file_read_tracking.mark_read(str(target))
    out = t.execute({
        "file_path": str(target),
        "old_string": "foo",
        "new_string": "foo",
    })
    assert out.startswith("Error:")
    assert "identical" in out.lower()


def test_edit_file_stale_file_rejected(workspace):
    """If the file was modified externally since the agent read it,
    edit_file must reject the operation (v4 parity)."""
    from tools import _file_read_tracking
    t = _tool("edit_file")
    target = workspace / "code.py"
    target.write_text("a\n", encoding="utf-8")
    _file_read_tracking.mark_read(str(target))
    # Wait a moment then external write to bump mtime
    time.sleep(1.1)
    target.write_text("a\nexternal_change\n", encoding="utf-8")
    out = t.execute({
        "file_path": str(target),
        "old_string": "a",
        "new_string": "X",
    })
    assert out.startswith("Error:")
    assert "modified externally" in out.lower() or "stale" in out.lower() or "re-read" in out.lower()


def test_edit_file_outside_workspace_blocked(workspace):
    t = _tool("edit_file")
    other = "C:/Windows/blocked.txt" if os.name == "nt" else "/etc/blocked"
    out = t.execute({"file_path": other, "old_string": "x", "new_string": "y"})
    assert out.startswith("Error:")
    assert "outside workspace" in out


def test_edit_file_missing_file_returns_error(workspace):
    from tools import _file_read_tracking
    t = _tool("edit_file")
    target = workspace / "nope.txt"
    _file_read_tracking.mark_read(str(target))
    out = t.execute({"file_path": str(target), "old_string": "x", "new_string": "y"})
    assert out.startswith("Error:")
    assert "not found" in out.lower()


# ============================================================
# notebook_edit
# ============================================================

def _make_notebook(path, cells):
    """Build a minimal valid .ipynb file at `path` with the given cells."""
    nb = {
        "cells": cells,
        "metadata": {"kernelspec": {"name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(nb), encoding="utf-8")


def test_notebook_edit_insert_at_index(workspace):
    t = _tool("notebook_edit")
    nb_path = workspace / "demo.ipynb"
    _make_notebook(nb_path, [
        {"cell_type": "markdown", "metadata": {}, "source": ["# Title\n"]},
    ])
    out = t.execute({
        "notebook_path": str(nb_path),
        "action": "insert",
        "cell_index": 1,
        "cell_type": "code",
        "source": "print('hello')",
    })
    assert "Inserted" in out
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    assert len(nb["cells"]) == 2
    assert nb["cells"][1]["cell_type"] == "code"


def test_notebook_edit_insert_append_with_negative_index(workspace):
    t = _tool("notebook_edit")
    nb_path = workspace / "demo.ipynb"
    _make_notebook(nb_path, [
        {"cell_type": "markdown", "metadata": {}, "source": ["# A\n"]},
        {"cell_type": "markdown", "metadata": {}, "source": ["# B\n"]},
    ])
    out = t.execute({
        "notebook_path": str(nb_path),
        "action": "insert",
        "cell_index": -1,
        "cell_type": "code",
        "source": "x = 1",
    })
    assert "Inserted" in out
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    assert len(nb["cells"]) == 3
    assert nb["cells"][-1]["cell_type"] == "code"


def test_notebook_edit_replace_cell(workspace):
    t = _tool("notebook_edit")
    nb_path = workspace / "demo.ipynb"
    _make_notebook(nb_path, [
        {"cell_type": "code", "metadata": {}, "source": ["x = 1"], "execution_count": None, "outputs": []},
    ])
    out = t.execute({
        "notebook_path": str(nb_path),
        "action": "replace",
        "cell_index": 0,
        "cell_type": "code",
        "source": "x = 42",
    })
    assert "Replaced" in out
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    assert nb["cells"][0]["source"] == ["x = 42"]


def test_notebook_edit_delete_cell(workspace):
    t = _tool("notebook_edit")
    nb_path = workspace / "demo.ipynb"
    _make_notebook(nb_path, [
        {"cell_type": "markdown", "metadata": {}, "source": ["# A\n"]},
        {"cell_type": "markdown", "metadata": {}, "source": ["# B\n"]},
    ])
    out = t.execute({"notebook_path": str(nb_path), "action": "delete", "cell_index": 0})
    assert "Deleted" in out
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    assert len(nb["cells"]) == 1
    assert nb["cells"][0]["source"] == ["# B\n"]


def test_notebook_edit_invalid_action(workspace):
    t = _tool("notebook_edit")
    nb_path = workspace / "demo.ipynb"
    _make_notebook(nb_path, [{"cell_type": "code", "metadata": {}, "source": []}])
    out = t.execute({"notebook_path": str(nb_path), "action": "rotate", "cell_index": 0})
    assert out.startswith("Error:")
    assert "action must be" in out


def test_notebook_edit_out_of_bounds(workspace):
    t = _tool("notebook_edit")
    nb_path = workspace / "demo.ipynb"
    _make_notebook(nb_path, [{"cell_type": "code", "metadata": {}, "source": []}])
    out = t.execute({"notebook_path": str(nb_path), "action": "delete", "cell_index": 99})
    assert out.startswith("Error:")
    assert "out of bounds" in out


def test_notebook_edit_non_ipynb_path_rejected(workspace):
    t = _tool("notebook_edit")
    target = workspace / "code.py"
    target.write_text("x", encoding="utf-8")
    out = t.execute({
        "notebook_path": str(target),
        "action": "insert",
        "cell_index": 0,
        "cell_type": "code",
        "source": "x",
    })
    assert out.startswith("Error:")
    assert ".ipynb" in out


def test_notebook_edit_atomic_write_preserves_on_failure(workspace, monkeypatch):
    """If the write fails mid-way, the original file must not be corrupted."""
    t = _tool("notebook_edit")
    nb_path = workspace / "demo.ipynb"
    original_cells = [{"cell_type": "code", "metadata": {}, "source": ["original"]}]
    _make_notebook(nb_path, original_cells)
    original_content = nb_path.read_text(encoding="utf-8")

    # Sabotage os.replace to simulate failure during atomic rename
    import os as _os
    real_replace = _os.replace
    def fail_replace(*args, **kwargs):
        raise OSError("simulated rename failure")
    monkeypatch.setattr(_os, "replace", fail_replace)

    out = t.execute({
        "notebook_path": str(nb_path),
        "action": "delete",
        "cell_index": 0,
    })
    # Surface error to the model — accept either "Error:" or "Error writing..." form (v4 parity).
    assert out.lower().startswith("error")
    # Original notebook MUST be intact (atomic write contract)
    assert nb_path.read_text(encoding="utf-8") == original_content
    monkeypatch.setattr(_os, "replace", real_replace)


# ============================================================
# view_image
# ============================================================

def test_view_image_happy_path(workspace):
    """A small PNG file should pass validation and return a confirmation."""
    t = _tool("view_image")
    target = workspace / "tiny.png"
    # Minimal valid 1×1 PNG (8-byte signature + minimal IHDR/IDAT/IEND)
    png_bytes = bytes.fromhex(
        "89504E470D0A1A0A"  # signature
        "0000000D49484452"  # IHDR length=13 + type
        "00000001000000010806000000"  # 1x1 RGBA
        "1F15C4890000000A4944415478DA63000100000500010D0A2DB40000000049454E44AE426082"
    )
    target.write_bytes(png_bytes)
    out = t.execute({"file_path": str(target)})
    assert not out.startswith("Error:"), out
    assert "image/png" in out


def test_view_image_unsupported_format(workspace):
    t = _tool("view_image")
    target = workspace / "doc.pdf"
    target.write_bytes(b"%PDF-1.4\n")
    out = t.execute({"file_path": str(target)})
    assert out.startswith("Error:")
    assert "unsupported format" in out.lower()


def test_view_image_missing_file(workspace):
    t = _tool("view_image")
    out = t.execute({"file_path": str(workspace / "missing.png")})
    assert out.startswith("Error:")
    assert "not found" in out.lower()


def test_view_image_outside_workspace_blocked(workspace):
    t = _tool("view_image")
    other = "C:/Windows/icon.png" if os.name == "nt" else "/etc/icon.png"
    out = t.execute({"file_path": other})
    assert out.startswith("Error:")


def test_view_image_queues_payload_for_phase_8(workspace):
    """Codex Phase-04 finding 2 lock: view_image must queue the base64
    payload for Phase 8 query_engine to inject into the next model turn.
    pop_pending_images() drains the queue atomically."""
    from tools import view_image as vi
    vi.reset_pending_images_for_tests()
    t = _tool("view_image")
    target = workspace / "tiny.png"
    png_bytes = bytes.fromhex(
        "89504E470D0A1A0A"
        "0000000D49484452"
        "00000001000000010806000000"
        "1F15C4890000000A4944415478DA63000100000500010D0A2DB40000000049454E44AE426082"
    )
    target.write_bytes(png_bytes)
    out = t.execute({"file_path": str(target)})
    assert not out.startswith("Error:"), out
    # Drain the pending queue and verify shape
    queued = vi.pop_pending_images()
    assert len(queued) == 1
    block = queued[0]
    assert block["type"] == "image"
    assert block["source"]["type"] == "base64"
    assert block["source"]["media_type"] == "image/png"
    assert isinstance(block["source"]["data"], str) and len(block["source"]["data"]) > 0
    # After draining, the queue is empty
    assert vi.pop_pending_images() == []


def test_notebook_edit_handles_non_oserror_write_failure(workspace, monkeypatch):
    """Codex Phase-04 finding 1 lock: non-OSError exceptions during the
    atomic write must be caught and surfaced as Error: strings (v4 parity).
    Mocks json.dump to raise TypeError to simulate a serialization
    failure."""
    t = _tool("notebook_edit")
    nb_path = workspace / "demo.ipynb"
    _make_notebook(nb_path, [{"cell_type": "code", "metadata": {}, "source": ["x = 1"], "execution_count": None, "outputs": []}])
    original_content = nb_path.read_text(encoding="utf-8")

    import json as _json
    real_dump = _json.dump
    def fail_dump(*args, **kwargs):
        raise TypeError("simulated serialization failure")
    monkeypatch.setattr(_json, "dump", fail_dump)

    out = t.execute({
        "notebook_path": str(nb_path),
        "action": "delete",
        "cell_index": 0,
    })
    assert out.lower().startswith("error")
    assert "TypeError" in out or "simulated serialization" in out
    # Atomic-write contract: original must be intact even on non-OSError failures
    assert nb_path.read_text(encoding="utf-8") == original_content
    monkeypatch.setattr(_json, "dump", real_dump)


# ============================================================
# Registry: Phase 04 tools land cleanly
# ============================================================

def test_assemble_tool_pool_includes_all_phase_4_tools():
    """All 4 Phase-4 tools must show up in the assembled pool."""
    from tools import assemble_tool_pool
    pool_names = {t.name for t in assemble_tool_pool()}
    assert {"write_file", "edit_file", "notebook_edit", "view_image"}.issubset(pool_names)


def test_plan_mode_excludes_mutating_tools():
    """Mutating tools are NOT in PLAN_MODE_ALLOWED_TOOLS — plan mode must
    hide them. view_image IS in the allowlist (it's read-only)."""
    from tools import assemble_tool_pool
    pool = assemble_tool_pool(plan_mode=True)
    names = {t.name for t in pool}
    # write_file / edit_file / notebook_edit are mutating → NOT in plan mode
    assert "write_file" not in names
    assert "edit_file" not in names
    assert "notebook_edit" not in names
    # view_image IS in PLAN_MODE_ALLOWED_TOOLS (it's read-only)
    assert "view_image" in names
