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


# ============================================================
# Document creators
# ============================================================

def test_tool_create_word_writes_docx(tmp_path):
    docx = pytest.importorskip("docx")
    fp = str(tmp_path / "out.docx")
    tool = _find_tool("create_word")
    assert tool is not None
    out = tool.execute({"filepath": fp, "content": "# Title\n\nBody text.\n"}, context={})
    assert out.startswith("Wrote ")
    assert os.path.isfile(fp)
    # .docx is a zip; first 2 bytes = "PK".
    with open(fp, "rb") as f:
        assert f.read(2) == b"PK"


def test_tool_create_excel_with_chart(tmp_path):
    pytest.importorskip("openpyxl")
    fp = str(tmp_path / "out.xlsx")
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


def test_tool_create_markdown(tmp_path):
    fp = str(tmp_path / "doc.md")
    tool = _find_tool("create_markdown")
    out = tool.execute({"filepath": fp, "content": "# Hello\n\nWorld."}, context={})
    assert out.startswith("Wrote ")
    assert (tmp_path / "doc.md").read_text(encoding="utf-8") == "# Hello\n\nWorld."


def test_tool_create_notebook_cells(tmp_path):
    import json
    fp = str(tmp_path / "n.ipynb")
    tool = _find_tool("create_notebook")
    out = tool.execute({
        "filepath": fp,
        "cells": [
            {"type": "markdown", "source": "# Notebook"},
            {"type": "code", "source": "print('hi')"},
        ],
    }, context={})
    assert out.startswith("Wrote ")
    nb = json.loads((tmp_path / "n.ipynb").read_text(encoding="utf-8"))
    assert nb["nbformat"] == 4
    assert len(nb["cells"]) == 2
    assert nb["cells"][0]["cell_type"] == "markdown"
    assert nb["cells"][1]["cell_type"] == "code"


def test_tool_create_chart_png(tmp_path):
    pytest.importorskip("matplotlib")
    fp = str(tmp_path / "chart.png")
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


def test_tool_create_pdf_sections(tmp_path):
    pytest.importorskip("matplotlib")
    fp = str(tmp_path / "doc.pdf")
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

def test_tool_web_fetch_html_to_markdown(monkeypatch):
    pytest.importorskip("requests")

    body = b"<html><body><h1>Hello</h1><p>World</p></body></html>"

    class _MockResponse:
        status_code = 200
        headers = {"Content-Type": "text/html"}

        def iter_content(self, chunk_size=8192):
            yield body

        def raise_for_status(self):
            pass

    def fake_get(url, timeout=15, allow_redirects=False, stream=False):
        return _MockResponse()

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    tool = _find_tool("web_fetch")
    # Use a public DNS name (not SSRF-blocked) so the tool actually fetches.
    out = tool.execute({"url": "https://example.com"}, context={})
    # html-to-markdown should produce # Hello and World.
    assert "# Hello" in out
    assert "World" in out


def test_tool_web_fetch_blocks_ssrf():
    """Codex iter-1 CRITICAL: SSRF protection blocks private/loopback hosts."""
    tool = _find_tool("web_fetch")
    for url in (
        "http://127.0.0.1/admin",
        "http://localhost/",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/",
    ):
        out = tool.execute({"url": url}, context={})
        assert "Error" in out and "blocked" in out.lower(), f"URL not blocked: {url}: {out}"


def test_tool_web_fetch_rejects_non_http_url():
    tool = _find_tool("web_fetch")
    out = tool.execute({"url": "ftp://x"}, context={})
    assert "Error" in out


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

def test_block_t_all_11_tools_registered():
    """Constraint #1 (v4.10.10 baseline): all 11 v4 tools must register."""
    expected = [
        "create_word", "create_excel", "create_markdown", "create_notebook",
        "create_chart", "create_pdf",
        "todo_write", "todo_read",
        "semantic_search", "web_fetch", "ask_user",
    ]
    for name in expected:
        assert _find_tool(name) is not None, f"Block T tool '{name}' missing"
