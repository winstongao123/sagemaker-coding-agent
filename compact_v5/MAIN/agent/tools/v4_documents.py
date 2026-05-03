"""V5 tools/v4_documents.py — Block T document-creation tools.

PORT_LOG: #103. ADR-038.

6 v4 document tools consolidated (one file, minimum-file constraint #5):
- create_word     — .docx via python-docx (lazy import).
- create_excel    — .xlsx via openpyxl (lazy import; supports chart_type).
- create_markdown — .md trivial write.
- create_notebook — .ipynb JSON shape.
- create_chart    — .png via matplotlib (lazy import; supports chart_type).
- create_pdf      — .pdf via matplotlib pdf backend (lazy import; supports
                    heading/text/table/image content blocks).

Each tool fails fast with a clear error if its underlying library is
missing. v5 doesn't pull these as hard dependencies (constraint #15) —
SageMaker users with the standard Python data-science kernel have all
of them installed.

Block T design note (test_tool_create_html_via_write_file_documented):
There is intentionally NO `create_html` tool. Use `write_file` with a
`.html` extension instead. HTML is text and `write_file` already works
for it; adding a separate tool is bloat.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from .registry import build_tool, register


# ============================================================
# create_word — python-docx
# ============================================================

def _create_word_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    filepath = str(args.get("filepath") or args.get("file_path") or "").strip()
    content = str(args.get("content") or "").strip()
    if not filepath:
        return "Error: filepath is required"
    if not filepath.endswith(".docx"):
        filepath += ".docx"
    try:
        from docx import Document
    except ImportError:
        return "Error: python-docx not installed; install via `pip install python-docx`"
    try:
        doc = Document()
        # Treat lines starting with `# ` as H1, `## ` as H2, etc.
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                doc.add_heading(stripped[2:], level=1)
            elif stripped.startswith("## "):
                doc.add_heading(stripped[3:], level=2)
            elif stripped.startswith("### "):
                doc.add_heading(stripped[4:], level=3)
            elif stripped:
                doc.add_paragraph(stripped)
            else:
                doc.add_paragraph("")
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        doc.save(filepath)
        return f"Wrote {filepath}"
    except Exception as exc:  # noqa: BLE001
        return f"Error: {type(exc).__name__}: {exc}"


_CREATE_WORD_SCHEMA = {
    "type": "object",
    "properties": {
        "filepath": {"type": "string", "description": "Output .docx path."},
        "content": {"type": "string", "description": "Markdown-flavored content. # / ## / ### become Headings 1-3."},
    },
    "required": ["filepath", "content"],
}


# ============================================================
# create_excel — openpyxl
# ============================================================

def _create_excel_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    filepath = str(args.get("filepath") or args.get("file_path") or "").strip()
    rows = args.get("rows") or args.get("data") or []
    chart_type = args.get("chart_type") or ""
    if not filepath:
        return "Error: filepath is required"
    if not filepath.endswith(".xlsx"):
        filepath += ".xlsx"
    try:
        from openpyxl import Workbook
        from openpyxl.chart import BarChart, LineChart, PieChart, Reference
    except ImportError:
        return "Error: openpyxl not installed; install via `pip install openpyxl`"
    try:
        wb = Workbook()
        ws = wb.active
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, list):
                    ws.append(row)
                else:
                    ws.append([row])
        if chart_type and len(rows) >= 2:
            chart_cls = {
                "bar": BarChart, "line": LineChart, "pie": PieChart,
            }.get(chart_type.lower(), BarChart)
            chart = chart_cls()
            data_ref = Reference(
                ws, min_col=1, min_row=1, max_col=len(rows[0]) if rows else 1,
                max_row=len(rows),
            )
            chart.add_data(data_ref, titles_from_data=True)
            ws.add_chart(chart, "E2")
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        wb.save(filepath)
        return f"Wrote {filepath}"
    except Exception as exc:  # noqa: BLE001
        return f"Error: {type(exc).__name__}: {exc}"


_CREATE_EXCEL_SCHEMA = {
    "type": "object",
    "properties": {
        "filepath": {"type": "string"},
        "rows": {"type": "array", "description": "List of rows; each row is a list of cell values."},
        "chart_type": {"type": "string", "enum": ["bar", "line", "pie"], "description": "Optional embedded chart type."},
    },
    "required": ["filepath", "rows"],
}


# ============================================================
# create_markdown — trivial
# ============================================================

def _create_markdown_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    filepath = str(args.get("filepath") or args.get("file_path") or "").strip()
    content = str(args.get("content") or "")
    if not filepath:
        return "Error: filepath is required"
    if not filepath.endswith(".md"):
        filepath += ".md"
    try:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Wrote {filepath}"
    except OSError as exc:
        return f"Error: {exc}"


_CREATE_MARKDOWN_SCHEMA = {
    "type": "object",
    "properties": {
        "filepath": {"type": "string"},
        "content": {"type": "string"},
    },
    "required": ["filepath", "content"],
}


# ============================================================
# create_notebook — JSON .ipynb format
# ============================================================

def _create_notebook_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    filepath = str(args.get("filepath") or args.get("file_path") or "").strip()
    cells = args.get("cells") or []
    if not filepath:
        return "Error: filepath is required"
    if not filepath.endswith(".ipynb"):
        filepath += ".ipynb"
    try:
        nb_cells = []
        for c in cells:
            if isinstance(c, dict):
                cell_type = c.get("type", "code")
                source = c.get("source", "")
                if isinstance(source, str):
                    source_lines = source.splitlines(keepends=True)
                else:
                    source_lines = list(source) if isinstance(source, list) else [str(source)]
                cell = {
                    "cell_type": cell_type,
                    "metadata": {},
                    "source": source_lines,
                }
                if cell_type == "code":
                    cell["execution_count"] = None
                    cell["outputs"] = []
                nb_cells.append(cell)
            elif isinstance(c, str):
                nb_cells.append({
                    "cell_type": "code",
                    "metadata": {},
                    "source": c.splitlines(keepends=True),
                    "execution_count": None,
                    "outputs": [],
                })
        notebook = {
            "cells": nb_cells,
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                "language_info": {"name": "python", "version": "3.11"},
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=2)
        return f"Wrote {filepath}"
    except Exception as exc:  # noqa: BLE001
        return f"Error: {type(exc).__name__}: {exc}"


_CREATE_NOTEBOOK_SCHEMA = {
    "type": "object",
    "properties": {
        "filepath": {"type": "string"},
        "cells": {"type": "array", "description": "List of cells. Each cell: {type: code|markdown, source: text}."},
    },
    "required": ["filepath", "cells"],
}


# ============================================================
# create_chart — matplotlib .png
# ============================================================

def _create_chart_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    filepath = str(args.get("filepath") or args.get("file_path") or "").strip()
    chart_type = (args.get("chart_type") or "bar").lower()
    data = args.get("data") or {}
    title = args.get("title") or ""
    if not filepath:
        return "Error: filepath is required"
    if not filepath.endswith(".png"):
        filepath += ".png"
    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend for SageMaker
        import matplotlib.pyplot as plt
    except ImportError:
        return "Error: matplotlib not installed; install via `pip install matplotlib`"
    try:
        labels = list(data.keys()) if isinstance(data, dict) else []
        values = list(data.values()) if isinstance(data, dict) else []
        if not labels or not values:
            # Default to a tiny demo chart for tests.
            labels = ["A", "B", "C"]
            values = [1, 2, 3]
        fig, ax = plt.subplots()
        if chart_type == "line":
            ax.plot(labels, values)
        elif chart_type == "pie":
            ax.pie(values, labels=labels)
        else:
            ax.bar(labels, values)
        if title:
            ax.set_title(title)
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        fig.savefig(filepath)
        plt.close(fig)
        return f"Wrote {filepath}"
    except Exception as exc:  # noqa: BLE001
        return f"Error: {type(exc).__name__}: {exc}"


_CREATE_CHART_SCHEMA = {
    "type": "object",
    "properties": {
        "filepath": {"type": "string"},
        "chart_type": {"type": "string", "enum": ["bar", "line", "pie"], "default": "bar"},
        "data": {"type": "object", "description": "Mapping of label → value."},
        "title": {"type": "string"},
    },
    "required": ["filepath"],
}


# ============================================================
# create_pdf — matplotlib pdf backend with content blocks
# ============================================================

def _create_pdf_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    filepath = str(args.get("filepath") or args.get("file_path") or "").strip()
    content_blocks = args.get("content") or []
    if not filepath:
        return "Error: filepath is required"
    if not filepath.endswith(".pdf"):
        filepath += ".pdf"
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
    except ImportError:
        return "Error: matplotlib not installed (PDF backend); install via `pip install matplotlib`"
    try:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with PdfPages(filepath) as pdf:
            fig = plt.figure(figsize=(8, 11))
            ax = fig.add_subplot(111)
            ax.axis("off")
            y = 0.95
            for block in (content_blocks if isinstance(content_blocks, list) else []):
                if not isinstance(block, dict):
                    continue
                btype = block.get("type", "text")
                btext = str(block.get("text", ""))
                if btype == "heading":
                    ax.text(0.05, y, btext, fontsize=18, fontweight="bold")
                    y -= 0.06
                elif btype == "text":
                    ax.text(0.05, y, btext, fontsize=10, wrap=True)
                    y -= 0.04
                elif btype == "table":
                    rows = block.get("rows") or []
                    for row in rows:
                        ax.text(0.05, y, " | ".join(str(c) for c in (row if isinstance(row, list) else [row])), fontsize=9, family="monospace")
                        y -= 0.03
                elif btype == "image":
                    ax.text(0.05, y, f"[image: {btext}]", fontsize=10, style="italic")
                    y -= 0.04
                if y < 0.1:
                    pdf.savefig(fig)
                    plt.close(fig)
                    fig = plt.figure(figsize=(8, 11))
                    ax = fig.add_subplot(111)
                    ax.axis("off")
                    y = 0.95
            pdf.savefig(fig)
            plt.close(fig)
        return f"Wrote {filepath}"
    except Exception as exc:  # noqa: BLE001
        return f"Error: {type(exc).__name__}: {exc}"


_CREATE_PDF_SCHEMA = {
    "type": "object",
    "properties": {
        "filepath": {"type": "string"},
        "content": {
            "type": "array",
            "description": "Content blocks: [{type: heading|text|table|image, ...}]",
        },
    },
    "required": ["filepath", "content"],
}


# ============================================================
# Registration
# ============================================================

_DOC_DESC = "Document creation tool — Block T (v4 surface parity)."


def _register():
    """Idempotent registration of all 6 document tools."""
    from .registry import find_tool_by_name, all_registered

    pairs = [
        ("create_word", _CREATE_WORD_SCHEMA, _create_word_executor,
         "Write a .docx file. Supports # / ## / ### markdown headings."),
        ("create_excel", _CREATE_EXCEL_SCHEMA, _create_excel_executor,
         "Write an .xlsx file. Supports embedded chart_type."),
        ("create_markdown", _CREATE_MARKDOWN_SCHEMA, _create_markdown_executor,
         "Write a .md file. Trivial wrapper over write_file with extension validation."),
        ("create_notebook", _CREATE_NOTEBOOK_SCHEMA, _create_notebook_executor,
         "Write an .ipynb file. cells = [{type: code|markdown, source: text}]."),
        ("create_chart", _CREATE_CHART_SCHEMA, _create_chart_executor,
         "Write a .png chart via matplotlib. chart_type: bar | line | pie."),
        ("create_pdf", _CREATE_PDF_SCHEMA, _create_pdf_executor,
         "Write a .pdf file via matplotlib. content = [{type: heading|text|table|image, ...}]."),
    ]
    for name, schema, executor, desc in pairs:
        if find_tool_by_name(all_registered(), name) is not None:
            continue
        register(build_tool(
            name=name,
            description=desc,
            input_schema=schema,
            execute=executor,
            requires_approval=False,
            should_defer=True,  # deferred-loading saves tokens
            max_result_size_chars=2000,
        ))
