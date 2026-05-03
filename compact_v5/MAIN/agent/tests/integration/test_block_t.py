"""Block T — v4 tool surface parity (11 missing tools).

Source: v4 sagemaker_agent.py tool registry.

Tests per TEST_DESIGN §Block T (11 tests):
- test_tool_create_word_writes_docx
- test_tool_create_excel_with_chart
- test_tool_create_markdown
- test_tool_create_notebook_cells
- test_tool_create_chart_png
- test_tool_create_pdf_sections
- test_tool_todo_write_round_trip
- test_tool_semantic_search_index_then_search
- test_tool_web_fetch_html_to_markdown
- test_tool_ask_user_blocks_then_unblocks
- test_tool_create_html_via_write_file_documented
"""
from __future__ import annotations

import os
import sys
import zipfile

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


def _find_tool(name):
    from tools.registry import find_tool_by_name, all_registered
    return find_tool_by_name(all_registered(), name)


@pytest.fixture(autouse=True)
def fresh_registry():
    from tools.registry import _reset_registry_for_tests
    from tools import bootstrap_built_ins
    _reset_registry_for_tests()
    bootstrap_built_ins()
    yield


@pytest.fixture
def workspace_tmp(tmp_path, monkeypatch):
    """Codex iter-2 CRITICAL fix follow-up: doc creators now enforce
    workspace bounds via SECURITY.validate_path(). Tests that write to
    pytest tmp_path must point CONFIG.workspace at tmp_path and rebuild
    the SECURITY singleton, otherwise the validation correctly rejects
    the out-of-workspace write.

    Yields tmp_path; restores SECURITY at teardown.
    """
    from runtime.config import CONFIG
    import security.manager as sec_mgr
    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    CONFIG.workspace = str(tmp_path)
    sec_mgr.rebuild_singleton_for_tests()
    yield tmp_path
    CONFIG.workspace = saved_ws
    sec_mgr.SECURITY = saved_sec


# ============================================================
# Document creators
# ============================================================

def test_tool_create_word_writes_docx(workspace_tmp):
    docx = pytest.importorskip("docx")
    fp = str(workspace_tmp / "out.docx")
    tool = _find_tool("create_word")
    assert tool is not None
    out = tool.execute({"filepath": fp, "content": "# Title\n\nBody text.\n"}, context={})
    assert out.startswith("Wrote ")
    assert os.path.isfile(fp)
    # .docx is a zip; first 2 bytes = "PK".
    with open(fp, "rb") as f:
        assert f.read(2) == b"PK"


def test_tool_create_word_v4_advertised_fields(workspace_tmp):
    """Codex iter-2 Axis-C lock: create_word v4 advertised
    title/include_toc/header/footer fields are accepted."""
    pytest.importorskip("docx")
    fp = str(workspace_tmp / "fancy.docx")
    tool = _find_tool("create_word")
    out = tool.execute({
        "filepath": fp,
        "content": "Body.",
        "title": "Doc Title",
        "include_toc": True,
        "header": "PageHeader",
        "footer": "PageFooter",
    }, context={})
    assert out.startswith("Wrote ")
    assert os.path.isfile(fp)


def test_tool_create_excel_with_chart(workspace_tmp):
    pytest.importorskip("openpyxl")
    fp = str(workspace_tmp / "out.xlsx")
    tool = _find_tool("create_excel")
    out = tool.execute({
        "filepath": fp,
        "rows": [["Label", "Value"], ["A", 1], ["B", 2], ["C", 3]],
        "chart_type": "bar",
    }, context={})
    assert out.startswith("Wrote ")
    assert os.path.isfile(fp)
    # .xlsx is a zip with [Content_Types].xml. Verify it's a valid zip.
    assert zipfile.is_zipfile(fp)


def test_tool_create_excel_v4_data_dict_shape(workspace_tmp):
    """Codex iter-1/2 HIGH lock: create_excel accepts the v4 list-of-dicts
    `data` shape, plus sheet_name + chart_title + x_column + y_columns.
    """
    pytest.importorskip("openpyxl")
    fp = str(workspace_tmp / "v4shape.xlsx")
    tool = _find_tool("create_excel")
    out = tool.execute({
        "filepath": fp,
        "data": [
            {"month": "Jan", "sales": 100, "cost": 60},
            {"month": "Feb", "sales": 120, "cost": 70},
        ],
        "sheet_name": "Q1",
        "chart_type": "bar",
        "chart_title": "Q1 Sales vs Cost",
        "x_column": "month",
        "y_columns": ["sales", "cost"],
    }, context={})
    assert out.startswith("Wrote ")
    assert zipfile.is_zipfile(fp)


def test_tool_create_markdown(workspace_tmp):
    fp = str(workspace_tmp / "doc.md")
    tool = _find_tool("create_markdown")
    out = tool.execute({"filepath": fp, "content": "# Hello\n\nWorld."}, context={})
    assert out.startswith("Wrote ")
    assert (workspace_tmp / "doc.md").read_text(encoding="utf-8") == "# Hello\n\nWorld."


def test_tool_create_notebook_cells(workspace_tmp):
    import json
    fp = str(workspace_tmp / "n.ipynb")
    tool = _find_tool("create_notebook")
    out = tool.execute({
        "filepath": fp,
        "cells": [
            {"type": "markdown", "source": "# Notebook"},
            {"type": "code", "source": "print('hi')"},
        ],
    }, context={})
    assert out.startswith("Wrote ")
    nb = json.loads((workspace_tmp / "n.ipynb").read_text(encoding="utf-8"))
    assert nb["nbformat"] == 4
    assert len(nb["cells"]) == 2
    assert nb["cells"][0]["cell_type"] == "markdown"
    assert nb["cells"][1]["cell_type"] == "code"


def test_tool_create_chart_png(workspace_tmp):
    pytest.importorskip("matplotlib")
    fp = str(workspace_tmp / "chart.png")
    tool = _find_tool("create_chart")
    out = tool.execute({
        "filepath": fp,
        "chart_type": "bar",
        "data": {"A": 1, "B": 2, "C": 3},
        "title": "Test",
    }, context={})
    assert out.startswith("Wrote ")
    assert os.path.isfile(fp)
    # PNG signature: 0x89 P N G.
    with open(fp, "rb") as f:
        assert f.read(4) == b"\x89PNG"


def test_tool_create_chart_v4_advertised_types_and_fields(workspace_tmp):
    """Codex iter-3 HIGH lock: create_chart now supports v4 advertised
    types (grouped_bar/stacked_bar/scatter/horizontal_bar/combo) and
    v4 advertised fields (xlabel/ylabel/colors/dpi/width/height/style).
    """
    pytest.importorskip("matplotlib")
    tool = _find_tool("create_chart")
    # grouped_bar with series + colors + axis labels + dpi + width/height.
    fp1 = str(workspace_tmp / "grouped.png")
    out1 = tool.execute({
        "filepath": fp1,
        "chart_type": "grouped_bar",
        "data": {
            "labels": ["Q1", "Q2", "Q3"],
            "series": [
                {"name": "Sales", "values": [10, 20, 30]},
                {"name": "Cost", "values": [5, 15, 25]},
            ],
        },
        "title": "Quarterly",
        "xlabel": "Quarter",
        "ylabel": "Amount ($)",
        "colors": ["#1f77b4", "#ff7f0e"],
        "dpi": 150,
        "width": 8,
        "height": 5,
    }, context={})
    assert out1.startswith("Wrote "), out1
    # scatter shape with x/y data.
    fp2 = str(workspace_tmp / "scat.png")
    out2 = tool.execute({
        "filepath": fp2,
        "chart_type": "scatter",
        "data": {"x": [1, 2, 3, 4], "y": [2, 4, 6, 8]},
    }, context={})
    assert out2.startswith("Wrote "), out2
    # horizontal_bar.
    fp3 = str(workspace_tmp / "hbar.png")
    out3 = tool.execute({
        "filepath": fp3,
        "chart_type": "horizontal_bar",
        "data": {"labels": ["X", "Y"], "values": [10, 20]},
    }, context={})
    assert out3.startswith("Wrote "), out3


def test_tool_create_chart_rejects_missing_data(workspace_tmp):
    """Codex iter-3 MEDIUM lock: missing data rejected (v4 required it)."""
    pytest.importorskip("matplotlib")
    tool = _find_tool("create_chart")
    out = tool.execute({
        "filepath": str(workspace_tmp / "bad.png"),
        "chart_type": "bar",
    }, context={})
    assert out.startswith("Error"), out
    assert "data" in out.lower()


def test_tool_create_chart_v4_combo_shape(workspace_tmp, monkeypatch):
    """Codex iter-4/5 MEDIUM lock: create_chart combo type accepts v4
    {labels, bar_values, line_values, bar_label, line_label, line_ylabel}
    shape (sagemaker_agent.py:6194-6214). iter-5 strengthens this by
    spying on the labels actually passed to ax.bar() — proving the
    parser does NOT fall through to the generic dict.keys() path
    (which would render ["labels", "bar_values", ...] as the x-axis).
    """
    pytest.importorskip("matplotlib")

    captured = {"bar_labels": None, "line_labels": None}
    import matplotlib.axes
    real_bar = matplotlib.axes.Axes.bar
    real_plot = matplotlib.axes.Axes.plot

    def spy_bar(self, x, *a, **kw):
        if captured["bar_labels"] is None:
            captured["bar_labels"] = list(x)
        return real_bar(self, x, *a, **kw)

    def spy_plot(self, x, *a, **kw):
        if captured["line_labels"] is None:
            captured["line_labels"] = list(x)
        return real_plot(self, x, *a, **kw)

    monkeypatch.setattr(matplotlib.axes.Axes, "bar", spy_bar)
    monkeypatch.setattr(matplotlib.axes.Axes, "plot", spy_plot)

    fp = str(workspace_tmp / "combo.png")
    tool = _find_tool("create_chart")
    out = tool.execute({
        "filepath": fp,
        "chart_type": "combo",
        "data": {
            "labels": ["Q1", "Q2", "Q3", "Q4"],
            "bar_values": [10, 20, 15, 25],
            "line_values": [12, 18, 14, 22],
            "bar_label": "Revenue",
            "line_label": "Profit",
            "line_ylabel": "Profit ($M)",
        },
        "title": "Annual Performance",
    }, context={})
    assert out.startswith("Wrote "), out
    assert os.path.isfile(fp)
    # The bug case would have bar_labels == ["labels", "bar_values", "line_values", ...].
    assert captured["bar_labels"] == ["Q1", "Q2", "Q3", "Q4"], (
        f"bar got wrong labels: {captured['bar_labels']}"
    )
    assert captured["line_labels"] == ["Q1", "Q2", "Q3", "Q4"], (
        f"line got wrong labels: {captured['line_labels']}"
    )


def test_tool_create_chart_filepath_defaults_to_chart_png(workspace_tmp):
    """Codex iter-4 HIGH lock: v4 defaults filepath to 'chart.png' when
    omitted (sagemaker_agent.py:6049-6052; schema required=[data])."""
    pytest.importorskip("matplotlib")
    # Cd into workspace so relative "chart.png" resolves under it.
    cwd = os.getcwd()
    os.chdir(str(workspace_tmp))
    try:
        tool = _find_tool("create_chart")
        out = tool.execute({
            "chart_type": "bar",
            "data": {"A": 1, "B": 2},
        }, context={})
        assert out.startswith("Wrote "), out
        # Default filepath = chart.png within workspace.
        assert "chart.png" in out
    finally:
        os.chdir(cwd)


def test_tool_create_excel_rejects_empty_payload(workspace_tmp):
    """Codex iter-3 MEDIUM lock: missing data+rows rejected."""
    pytest.importorskip("openpyxl")
    tool = _find_tool("create_excel")
    out = tool.execute({"filepath": str(workspace_tmp / "empty.xlsx")}, context={})
    assert out.startswith("Error"), out
    assert "data" in out.lower() or "rows" in out.lower()


def test_tool_create_pdf_rejects_empty_payload(workspace_tmp):
    """Codex iter-3 MEDIUM lock: missing data+content rejected."""
    pytest.importorskip("matplotlib")
    tool = _find_tool("create_pdf")
    out = tool.execute({"filepath": str(workspace_tmp / "empty.pdf")}, context={})
    assert out.startswith("Error"), out
    assert "data" in out.lower() or "content" in out.lower()


def test_tool_create_pdf_sections(workspace_tmp):
    pytest.importorskip("matplotlib")
    fp = str(workspace_tmp / "doc.pdf")
    tool = _find_tool("create_pdf")
    out = tool.execute({
        "filepath": fp,
        "content": [
            {"type": "heading", "text": "Title"},
            {"type": "text", "text": "Some body text."},
            {"type": "table", "rows": [["A", "B"], [1, 2]]},
            {"type": "image", "text": "/path/to/img.png"},
        ],
    }, context={})
    assert out.startswith("Wrote ")
    assert os.path.isfile(fp)
    # PDF signature.
    with open(fp, "rb") as f:
        assert f.read(4) == b"%PDF"


def test_tool_create_pdf_v4_data_blocks_with_title_and_a4(workspace_tmp):
    """Codex iter-2 HIGH lock: create_pdf accepts v4 `data` (block list),
    `title`, and `page_size` (a4/letter/legal)."""
    pytest.importorskip("matplotlib")
    fp = str(workspace_tmp / "v4pdf.pdf")
    tool = _find_tool("create_pdf")
    out = tool.execute({
        "filepath": fp,
        "title": "Quarterly Report",
        "page_size": "a4",
        # v4 shape: per-block `data` field instead of `text`/`rows`.
        "data": [
            {"type": "heading", "data": "Section 1"},
            {"type": "text", "data": "Body para."},
            {"type": "table", "data": [["A", "B"], [1, 2]]},
        ],
    }, context={})
    assert out.startswith("Wrote ")
    with open(fp, "rb") as f:
        assert f.read(4) == b"%PDF"


def test_tool_create_doc_rejects_out_of_workspace(tmp_path, monkeypatch):
    """Codex iter-2 CRITICAL lock: doc creators reject paths outside
    workspace + allowed_paths. tmp_path is intentionally NOT added to
    workspace so the validation must fail-closed.
    """
    from runtime.config import CONFIG
    import security.manager as sec_mgr
    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    try:
        # Point workspace at a different tmp dir that does NOT contain tmp_path.
        other_root = tmp_path.parent / "other_workspace_root"
        other_root.mkdir(exist_ok=True)
        CONFIG.workspace = str(other_root)
        sec_mgr.rebuild_singleton_for_tests()
        bad_fp = str(tmp_path / "evil.md")
        tool = _find_tool("create_markdown")
        out = tool.execute({"filepath": bad_fp, "content": "x"}, context={})
        assert out.startswith("Error"), f"Expected validation error, got: {out}"
        assert "outside workspace" in out.lower() or "path" in out.lower()
    finally:
        CONFIG.workspace = saved_ws
        sec_mgr.SECURITY = saved_sec


# ============================================================
# todo_write / todo_read round-trip
# ============================================================

def test_tool_todo_write_round_trip():
    import json
    write_tool = _find_tool("todo_write")
    read_tool = _find_tool("todo_read")
    assert write_tool is not None and read_tool is not None
    todos = [
        {"content": "Investigate auth bug", "status": "in_progress", "activeForm": "Investigating"},
        {"content": "Write tests", "status": "pending", "activeForm": "Writing tests"},
    ]
    out = write_tool.execute({"todos": todos}, context={})
    assert "2 todos" in out
    out2 = read_tool.execute({}, context={})
    parsed = json.loads(out2)
    assert len(parsed) == 2
    assert parsed[0]["content"] == "Investigate auth bug"
    assert parsed[1]["status"] == "pending"


def test_tool_todo_read_empty():
    from tools.todo import _reset_todos_for_tests
    _reset_todos_for_tests()
    read_tool = _find_tool("todo_read")
    out = read_tool.execute({}, context={})
    assert "no todos" in out.lower()


# ============================================================
# semantic_search index → search
# ============================================================

def test_tool_semantic_search_index_then_search(tmp_path):
    pytest.importorskip("sklearn")
    # Set up a small corpus.
    (tmp_path / "a.py").write_text("def authenticate(user, password): return True", encoding="utf-8")
    (tmp_path / "b.py").write_text("def calculate_pi(): return 3.14159", encoding="utf-8")
    (tmp_path / "c.md").write_text("# Auth flow\n\nSee authenticate function for details.", encoding="utf-8")

    from tools.semantic_search import _reset_for_tests
    _reset_for_tests()

    tool = _find_tool("semantic_search")
    out_idx = tool.execute({"action": "index", "path": str(tmp_path)}, context={})
    assert "Indexed 3 files" in out_idx

    out_search = tool.execute({
        "action": "search", "path": str(tmp_path),
        "query": "authenticate user", "k": 5,
    }, context={})
    # "authenticate" appears in a.py and c.md → both should rank highly.
    assert "a.py" in out_search or "c.md" in out_search


# ============================================================
# web_fetch with mocked HTTP response
# ============================================================

def test_web_fetch_module_disabled():
    """User decision 2026-05-03: web_fetch is shipped DISABLED in v5.0.1.
    v5's single-user SageMaker context is typically VPC-isolated, so the
    tool would be dead code. Importing the module must raise
    NotImplementedError so accidental re-wiring fails loudly.

    PORT_LOG #103: DECISION-DROP-PER-USER (NOT silent narrowing).
    """
    import importlib
    # Force a fresh import — the module may already be cached.
    import sys
    sys.modules.pop("tools.web_fetch", None)
    with pytest.raises(NotImplementedError) as excinfo:
        importlib.import_module("tools.web_fetch")
    assert "disabled" in str(excinfo.value).lower()


def test_web_fetch_not_in_registry():
    """Block T: web_fetch must NOT appear in the active tool registry."""
    assert _find_tool("web_fetch") is None


# ============================================================
# ask_user — provider hook
# ============================================================

def test_tool_ask_user_blocks_then_unblocks():
    """ask_user uses context['ask_user_response_provider'] in tests."""
    tool = _find_tool("ask_user")
    out = tool.execute(
        {"question": "What is 2+2?"},
        context={"ask_user_response_provider": lambda q: "4"},
    )
    assert out == "4"


def test_tool_ask_user_provider_exception():
    tool = _find_tool("ask_user")

    def raising_provider(question):
        raise RuntimeError("user disconnected")

    out = tool.execute(
        {"question": "x"},
        context={"ask_user_response_provider": raising_provider},
    )
    assert "Error" in out
    assert "user disconnected" in out


# ============================================================
# create_html design note (Wave 6 — write_file with .html ext)
# ============================================================

def test_tool_create_html_via_write_file_documented():
    """Block T design note: there is no separate `create_html` tool.
    Use `write_file` with a `.html` extension. This is the user's
    design decision per Wave 6."""
    # No create_html tool registered.
    assert _find_tool("create_html") is None
    # write_file IS available and accepts .html.
    write = _find_tool("write_file")
    assert write is not None


# ============================================================
# Block T — all 11 tools registered
# ============================================================

def test_block_t_active_tools_registered():
    """Constraint #1 (v4.10.10 baseline) honored as DECISION-DROP-PER-USER:
    10 of 11 v4 tools register; web_fetch dropped 2026-05-03 by user
    (SageMaker VPC-isolated; tool would be dead code). PORT_LOG #103.
    """
    expected_active = [
        "create_word", "create_excel", "create_markdown", "create_notebook",
        "create_chart", "create_pdf",
        "todo_write", "todo_read",
        "semantic_search", "ask_user",
    ]
    for name in expected_active:
        assert _find_tool(name) is not None, f"Block T tool '{name}' missing"
    # Explicit dropped tool — locked here so accidental re-wiring fails.
    assert _find_tool("web_fetch") is None, (
        "web_fetch must remain disabled per user decision 2026-05-03"
    )
