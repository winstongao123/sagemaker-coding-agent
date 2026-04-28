"""V4.10.0 #10 — surgical .ipynb cell editor.

Tests:
1. insert middle (between cells)
2. insert append (cell_index=-1 OR >= len)
3. replace code cell — preserves cell id, resets execution_count/outputs
4. replace markdown cell
5. delete cell
6. invalid action returns Error:
7. cell_index out of bounds on replace/delete returns Error:
8. missing required arg (source) on insert/replace returns Error:
9. atomic write — temp file cleaned up on failure
10. preserves cells we did not touch (round-trip safety)
"""

from __future__ import annotations

import atexit
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sagemaker_agent as sa


# v4.10.2: track and clean up tempdirs at process exit. Without this the test
# leaves dozens of v410_nb_* dirs inside CONFIG.workspace which then end up
# in the ship zip if rebuilt before manual cleanup.
_TEMP_DIRS: list = []


def _cleanup_tempdirs():
    for d in _TEMP_DIRS:
        try:
            shutil.rmtree(d, ignore_errors=True)
        except Exception:
            pass


atexit.register(_cleanup_tempdirs)


def _seed_notebook(path: str, sources):
    """Create a minimal valid .ipynb at `path` with the given list of sources.
    Each source produces a code cell with that text + an id."""
    cells = []
    for i, src in enumerate(sources):
        cells.append({
            "cell_type": "code",
            "metadata": {},
            "source": [src],
            "execution_count": None,
            "outputs": [],
            "id": f"cell-{i}",
        })
    nb = {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                     "language_info": {"name": "python", "version": "3.10.0"}},
        "cells": cells,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)


def _read_cells(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["cells"]


def _setup():
    """Create tmp .ipynb inside CONFIG.workspace so SECURITY.validate_path passes."""
    tmp = tempfile.mkdtemp(prefix="v410_nb_edit_", dir=sa.CONFIG.workspace)
    _TEMP_DIRS.append(tmp)
    nb_path = os.path.join(tmp, "test.ipynb")
    _seed_notebook(nb_path, ["a", "b", "c"])
    return tmp, nb_path


def test_insert_middle():
    tmp, nb_path = _setup()
    out = sa.tool_notebook_edit({
        "path": nb_path, "action": "insert", "cell_index": 1,
        "cell_type": "code", "source": "INSERTED",
    })
    assert "Edited" in out and "now 4 cells" in out, out
    cells = _read_cells(nb_path)
    assert len(cells) == 4
    assert cells[1]["source"] == ["INSERTED"]
    # Original cells preserved
    assert cells[0]["source"] == ["a"]
    assert cells[2]["source"] == ["b"]
    assert cells[3]["source"] == ["c"]


def test_insert_append_with_negative_index():
    tmp, nb_path = _setup()
    out = sa.tool_notebook_edit({
        "path": nb_path, "action": "insert", "cell_index": -1,
        "cell_type": "markdown", "source": "# end",
    })
    assert "now 4 cells" in out, out
    cells = _read_cells(nb_path)
    assert cells[3]["cell_type"] == "markdown"
    assert cells[3]["source"] == ["# end"]


def test_replace_code_cell_preserves_id_and_resets_outputs():
    tmp, nb_path = _setup()
    out = sa.tool_notebook_edit({
        "path": nb_path, "action": "replace", "cell_index": 1,
        "cell_type": "code", "source": "x = 1\nprint(x)",
    })
    assert "now 3 cells" in out, out
    cells = _read_cells(nb_path)
    assert len(cells) == 3
    # ID preserved
    assert cells[1].get("id") == "cell-1"
    # Source replaced
    assert cells[1]["source"] == ["x = 1\n", "print(x)"]
    # Code cell properties reset
    assert cells[1]["execution_count"] is None
    assert cells[1]["outputs"] == []


def test_replace_markdown_cell():
    tmp, nb_path = _setup()
    out = sa.tool_notebook_edit({
        "path": nb_path, "action": "replace", "cell_index": 0,
        "cell_type": "markdown", "source": "# title",
    })
    assert "now 3 cells" in out, out
    cells = _read_cells(nb_path)
    assert cells[0]["cell_type"] == "markdown"
    assert cells[0]["source"] == ["# title"]
    # Markdown cells should NOT have execution_count/outputs keys
    assert "execution_count" not in cells[0]
    assert "outputs" not in cells[0]


def test_delete_cell():
    tmp, nb_path = _setup()
    out = sa.tool_notebook_edit({
        "path": nb_path, "action": "delete", "cell_index": 1,
    })
    assert "now 2 cells" in out, out
    cells = _read_cells(nb_path)
    assert len(cells) == 2
    assert cells[0]["source"] == ["a"]
    assert cells[1]["source"] == ["c"]


def test_invalid_action():
    tmp, nb_path = _setup()
    out = sa.tool_notebook_edit({"path": nb_path, "action": "wat", "cell_index": 0})
    assert out.startswith("Error:"), out


def test_out_of_bounds_replace():
    tmp, nb_path = _setup()
    out = sa.tool_notebook_edit({
        "path": nb_path, "action": "replace", "cell_index": 99,
        "cell_type": "code", "source": "x",
    })
    assert "out of bounds" in out, out


def test_out_of_bounds_delete():
    tmp, nb_path = _setup()
    out = sa.tool_notebook_edit({"path": nb_path, "action": "delete", "cell_index": 99})
    assert "out of bounds" in out, out


def test_missing_source_on_insert():
    tmp, nb_path = _setup()
    out = sa.tool_notebook_edit({
        "path": nb_path, "action": "insert", "cell_index": 0, "cell_type": "code",
    })
    assert out.startswith("Error:"), out
    assert "source" in out.lower()


def test_missing_cell_type_on_replace():
    tmp, nb_path = _setup()
    out = sa.tool_notebook_edit({
        "path": nb_path, "action": "replace", "cell_index": 0, "source": "x",
    })
    assert out.startswith("Error:"), out


def test_nonexistent_file():
    tmp = tempfile.mkdtemp(prefix="v410_nb_missing_", dir=sa.CONFIG.workspace)
    _TEMP_DIRS.append(tmp)
    out = sa.tool_notebook_edit({
        "path": os.path.join(tmp, "missing.ipynb"),
        "action": "insert", "cell_index": 0, "cell_type": "code", "source": "x",
    })
    assert out.startswith("Error:"), out
    assert "does not exist" in out


def test_non_serialisable_metadata_returns_error_string():
    """Codex 2026-04-28 fix: json.dump can raise TypeError if a cell carries
    non-serialisable metadata (e.g., bytes from a corrupted notebook). The
    tool must return 'Error: ...' rather than propagate the exception, AND
    the original notebook must remain untouched (atomicity)."""
    tmp = tempfile.mkdtemp(prefix="v410_nb_corrupt_", dir=sa.CONFIG.workspace)
    _TEMP_DIRS.append(tmp)
    nb_path = os.path.join(tmp, "test.ipynb")
    # Hand-craft a notebook with non-JSON-serialisable metadata embedded as a
    # placeholder. We can't put bytes in via json.dump (it would fail on seed),
    # so instead we seed normally and then mutate via direct file write to
    # inject a value we'll mutate in-memory by monkey-patching json.dump.
    _seed_notebook(nb_path, ["a", "b"])
    pre_size = os.path.getsize(nb_path)
    pre_mtime = os.path.getmtime(nb_path)
    # Force the write phase to fail by injecting a non-serialisable object
    # via monkeypatch of json.dump:
    real_dump = sa.json.dump
    def boom_dump(*args, **kwargs):
        raise TypeError("Object of type bytes is not JSON serializable")
    sa.json.dump = boom_dump
    try:
        out = sa.tool_notebook_edit({
            "path": nb_path, "action": "insert", "cell_index": 0,
            "cell_type": "code", "source": "x",
        })
    finally:
        sa.json.dump = real_dump

    assert out.startswith("Error:"), out
    # Original notebook untouched (atomic replace happens AFTER successful dump)
    assert os.path.getsize(nb_path) == pre_size, "Original notebook size changed despite failure"
    # Tmp file should be cleaned up
    assert not os.path.exists(nb_path + ".v410.tmp"), ".v410.tmp left behind on failure"


def test_round_trip_does_not_corrupt_other_cells():
    tmp, nb_path = _setup()
    sa.tool_notebook_edit({
        "path": nb_path, "action": "insert", "cell_index": 0,
        "cell_type": "markdown", "source": "header",
    })
    cells = _read_cells(nb_path)
    # Original 3 cells must be intact (now at indices 1, 2, 3)
    assert cells[1]["source"] == ["a"]
    assert cells[2]["source"] == ["b"]
    assert cells[3]["source"] == ["c"]
    assert cells[1].get("id") == "cell-0"


if __name__ == "__main__":
    tests = [
        ("insert_middle", test_insert_middle),
        ("insert_append_with_negative_index", test_insert_append_with_negative_index),
        ("replace_code_cell_preserves_id_and_resets_outputs", test_replace_code_cell_preserves_id_and_resets_outputs),
        ("replace_markdown_cell", test_replace_markdown_cell),
        ("delete_cell", test_delete_cell),
        ("invalid_action", test_invalid_action),
        ("out_of_bounds_replace", test_out_of_bounds_replace),
        ("out_of_bounds_delete", test_out_of_bounds_delete),
        ("missing_source_on_insert", test_missing_source_on_insert),
        ("missing_cell_type_on_replace", test_missing_cell_type_on_replace),
        ("nonexistent_file", test_nonexistent_file),
        ("non_serialisable_metadata_returns_error_string", test_non_serialisable_metadata_returns_error_string),
        ("round_trip_does_not_corrupt_other_cells", test_round_trip_does_not_corrupt_other_cells),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            print(f"FAIL  {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
