"""V5 ui/diff_widget.py — colored inline + expandable diff for the approval prompt.

Per ADR-010, V5_PLAN.md Phase 4 acceptance criterion:
    edit_file, write_file, AND notebook_edit approval prompts each show
    colored before/after diff inline (red removed, green added, gray
    context) with file path header + line numbers + ±3 lines context +
    click-to-expand-full-file BEFORE the user clicks Approve.

Adopted from Runnable's `gg-claude-code-runnable/src/tools/FileEditTool/UI.tsx`
React/Ink diff component (PORT_LOG row #009). v5 emits HTML strings instead
of Ink JSX (constraint = .ipynb). Phase 11 wires the HTML into an
ipywidgets `HTML` widget inside the approval prompt.

Phase 4 deliverable: HTML emission + tests. Phase 11 wires into UX.

The widget exposes two functions:
  - `render_inline_diff(file_path, before_text, after_text, context=3)`
    → returns HTML string with the colored diff visible immediately.
  - `render_expandable_diff(file_path, before_text, after_text)`
    → returns HTML wrapping inline diff in `<details>` so the full-file
       view is collapsible. Used in approval prompts.

Both use stdlib `difflib.unified_diff` for the diff content. No new
dependencies.
"""
from __future__ import annotations

import difflib
import html
import os
from typing import List


# ============================================================
# Color palette (matches Runnable's UI.tsx ANSI conventions adapted to web)
# ============================================================
# Inline-styles used so the HTML renders correctly inside a Jupyter notebook
# cell output where stylesheet inheritance is unreliable. Colors picked for
# readability on both light and dark notebook themes.
_COLOR_ADDED_BG = "#e6ffec"      # very light green
_COLOR_ADDED_FG = "#1a7f37"      # dark green
_COLOR_REMOVED_BG = "#ffebe9"    # very light red
_COLOR_REMOVED_FG = "#cf222e"    # dark red
_COLOR_CONTEXT_BG = "#f6f8fa"    # very light gray
_COLOR_CONTEXT_FG = "#57606a"    # mid gray
_COLOR_HUNK_BG = "#ddf4ff"       # light blue (hunk header)
_COLOR_HUNK_FG = "#0969da"       # GitHub blue


# ============================================================
# Public renderers
# ============================================================

def render_inline_diff(
    file_path: str,
    before_text: str,
    after_text: str,
    context: int = 3,
) -> str:
    """Render an inline colored diff as HTML.

    Args:
        file_path: file being edited (shown in header).
        before_text: original full-file content.
        after_text: post-edit full-file content.
        context: lines of context shown around each change. Default 3.

    Returns:
        An HTML fragment (no `<html>`/`<body>` wrapper) suitable for
        ipywidgets.HTML or `display(HTML(...))`. Includes its own
        inline styles, no external CSS needed.

    Note: empty diff (before == after) returns a header + "No changes"
    note rather than an empty string, so the approval prompt always shows
    something meaningful.
    """
    before_lines = before_text.splitlines()
    after_lines = after_text.splitlines()

    diff_lines = list(difflib.unified_diff(
        before_lines, after_lines,
        fromfile=f"a/{os.path.basename(file_path)}",
        tofile=f"b/{os.path.basename(file_path)}",
        n=context,
        lineterm="",
    ))

    if not diff_lines:
        # Codex Phase-04 review finding 3: `splitlines()` strips trailing
        # newlines so a file change that ONLY toggles the EOF newline
        # would silently render as "No changes". Surface it explicitly.
        before_eof_nl = before_text.endswith("\n")
        after_eof_nl = after_text.endswith("\n")
        if before_eof_nl != after_eof_nl:
            change = (
                "added trailing newline at EOF" if after_eof_nl
                else "removed trailing newline at EOF"
            )
            return _wrap(
                _header(file_path)
                + _row_note(f"No content changes — only the final newline differs ({change}).")
            )
        return _wrap(_header(file_path) + _row_note("No changes — file content is identical."))

    return _wrap(_header(file_path) + _render_unified(diff_lines))


def render_expandable_diff(
    file_path: str,
    before_text: str,
    after_text: str,
    context: int = 3,
) -> str:
    """Render the inline diff PLUS a click-to-expand `<details>` block
    containing the full-file view (no truncation).

    Used in the approval prompt so the user sees the focused diff
    immediately and can drill into the whole file if uncertain.
    """
    inline = render_inline_diff(file_path, before_text, after_text, context=context)

    full_diff_lines = list(difflib.unified_diff(
        before_text.splitlines(), after_text.splitlines(),
        fromfile=f"a/{os.path.basename(file_path)}",
        tofile=f"b/{os.path.basename(file_path)}",
        n=10_000,  # effectively whole-file context
        lineterm="",
    ))
    full = (
        '<details style="margin-top:6px;">'
        '<summary style="cursor:pointer;font-size:0.9em;color:#57606a;">'
        'Show full-file diff (click to expand)'
        '</summary>'
        + _wrap(_render_unified(full_diff_lines) if full_diff_lines else _row_note("No changes."))
        + '</details>'
    )
    return inline + full


def render_new_file_diff(file_path: str, content: str) -> str:
    """Specialised renderer for write_file when the file does not yet exist.
    All lines are shown as additions."""
    if not content:
        return _wrap(_header(file_path) + _row_note("(empty file will be created)"))
    rows = []
    for i, ln in enumerate(content.splitlines(), 1):
        rows.append(_row_added(i, ln))
    return _wrap(_header(file_path, badge="NEW FILE") + "".join(rows))


# ============================================================
# Internal helpers
# ============================================================

def _wrap(body: str) -> str:
    """Wrap body in an outer `<div>` with the v5 diff styling."""
    return (
        '<div style="font-family:ui-monospace,SFMono-Regular,Consolas,monospace;'
        'font-size:0.85em;line-height:1.45;border:1px solid #d0d7de;'
        'border-radius:6px;overflow:hidden;margin:4px 0;">'
        + body
        + '</div>'
    )


def _header(file_path: str, badge: str = "") -> str:
    safe = html.escape(file_path)
    badge_html = ""
    if badge:
        badge_html = (
            f'<span style="margin-left:8px;padding:1px 6px;border-radius:3px;'
            f'background:{_COLOR_HUNK_BG};color:{_COLOR_HUNK_FG};'
            f'font-size:0.85em;font-weight:600;">{html.escape(badge)}</span>'
        )
    return (
        f'<div style="padding:6px 10px;background:#f6f8fa;'
        f'border-bottom:1px solid #d0d7de;font-weight:600;color:#1f2328;">'
        f'{safe}{badge_html}</div>'
    )


def _row_note(text: str) -> str:
    return (
        f'<div style="padding:6px 10px;color:{_COLOR_CONTEXT_FG};'
        f'font-style:italic;">{html.escape(text)}</div>'
    )


def _row_added(line_no: int | str, text: str) -> str:
    return _row("+", line_no, text, _COLOR_ADDED_BG, _COLOR_ADDED_FG)


def _row_removed(line_no: int | str, text: str) -> str:
    return _row("-", line_no, text, _COLOR_REMOVED_BG, _COLOR_REMOVED_FG)


def _row_context(line_no: int | str, text: str) -> str:
    return _row(" ", line_no, text, _COLOR_CONTEXT_BG, _COLOR_CONTEXT_FG)


def _row_hunk(text: str) -> str:
    safe = html.escape(text)
    return (
        f'<div style="padding:2px 10px;background:{_COLOR_HUNK_BG};'
        f'color:{_COLOR_HUNK_FG};font-weight:600;">{safe}</div>'
    )


def _row(marker: str, line_no: int | str, text: str, bg: str, fg: str) -> str:
    safe_text = html.escape(text)
    safe_marker = html.escape(marker)
    return (
        f'<div style="display:flex;background:{bg};color:{fg};'
        f'padding:1px 0;">'
        f'<span style="display:inline-block;width:46px;text-align:right;'
        f'padding-right:8px;color:{_COLOR_CONTEXT_FG};opacity:0.85;'
        f'border-right:1px solid #eaeef2;flex-shrink:0;">{line_no}</span>'
        f'<span style="display:inline-block;width:18px;text-align:center;'
        f'flex-shrink:0;">{safe_marker}</span>'
        f'<span style="white-space:pre;">{safe_text}</span>'
        f'</div>'
    )


def _render_unified(diff_lines: List[str]) -> str:
    """Translate `difflib.unified_diff` output into colored HTML rows.

    `unified_diff` emits:
      - `--- a/path` and `+++ b/path` headers (skipped — we have our own header)
      - `@@ -L,N +L,N @@` hunk markers
      - `+line` / `-line` / ` line` content rows

    We track the running line numbers in the BEFORE and AFTER files so each
    row gets the correct line number annotation.
    """
    out: List[str] = []
    before_no = 0
    after_no = 0

    for raw in diff_lines:
        if raw.startswith("---") or raw.startswith("+++"):
            continue  # skip file-name headers; we render our own
        if raw.startswith("@@"):
            # Parse hunk header, e.g. "@@ -10,5 +10,7 @@"
            try:
                # Format: "@@ -<oldStart>,<oldCount> +<newStart>,<newCount> @@"
                inner = raw.strip().strip("@").strip()
                parts = inner.split()
                old_part = parts[0]  # "-10,5"
                new_part = parts[1]  # "+10,7"
                before_no = int(old_part.lstrip("-").split(",")[0])
                after_no = int(new_part.lstrip("+").split(",")[0])
            except (ValueError, IndexError):
                # Defensive: malformed hunk header — render verbatim and continue
                pass
            out.append(_row_hunk(raw))
            continue

        if raw.startswith("+"):
            out.append(_row_added(after_no, raw[1:]))
            after_no += 1
        elif raw.startswith("-"):
            out.append(_row_removed(before_no, raw[1:]))
            before_no += 1
        else:
            # context line (begins with " " or is empty after leading space)
            text = raw[1:] if raw.startswith(" ") else raw
            # Choose `before_no` to display because the line exists in both;
            # display "L/L" only when before_no != after_no.
            label = (
                str(before_no) if before_no == after_no
                else f"{before_no}/{after_no}"
            )
            out.append(_row_context(label, text))
            before_no += 1
            after_no += 1

    return "".join(out)
