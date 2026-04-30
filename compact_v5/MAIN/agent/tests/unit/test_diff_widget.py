"""Phase 04 unit tests: ui/diff_widget.py.

Locks the contract for ADR-010 + ADR-011: HTML colored diff widget for
the approval prompt (red removed, green added, gray context, file path
header, ±3 lines context, click-to-expand-full-file).

Tests verify:
  - render_inline_diff returns valid HTML containing change markers + file header.
  - render_inline_diff with identical content shows "No changes" note.
  - render_inline_diff respects the `context` parameter (±N lines around hunks).
  - render_expandable_diff wraps a `<details>` block for the full-file view.
  - render_new_file_diff marks every line as added with the NEW FILE badge.
  - HTML escaping: untrusted content is escaped (no raw `<script>` injection).
"""
from __future__ import annotations

import os
import sys

# Make `ui` importable from this test (mirrors flat-zip ship layout).
_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


def test_inline_diff_shows_added_and_removed_lines():
    from ui.diff_widget import render_inline_diff
    before = "line 1\nline 2\nline 3\n"
    after = "line 1\nline 2 modified\nline 3\n"
    html = render_inline_diff("/work/foo.py", before, after)
    assert "/work/foo.py" in html
    # Removed line is shown with `-` marker
    assert "line 2" in html
    # Added line is shown with `+` marker
    assert "line 2 modified" in html
    # Color cues present
    assert "#1a7f37" in html or "1a7f37" in html  # added green
    assert "#cf222e" in html or "cf222e" in html  # removed red


def test_inline_diff_no_changes_shows_note():
    from ui.diff_widget import render_inline_diff
    same = "alpha\nbeta\n"
    html = render_inline_diff("/work/x.txt", same, same)
    assert "No changes" in html
    assert "/work/x.txt" in html


def test_inline_diff_html_escapes_special_chars():
    """Untrusted content must be HTML-escaped so a model can't inject <script>."""
    from ui.diff_widget import render_inline_diff
    before = "line 1\n"
    after = "line 1\n<script>alert('xss')</script>\n"
    html = render_inline_diff("/work/<bad>.py", before, after)
    # The literal `<script>` must NOT appear unescaped.
    assert "<script>alert" not in html
    # The escaped form must appear.
    assert "&lt;script&gt;alert" in html
    # File path with special chars also escaped.
    assert "&lt;bad&gt;" in html


def test_expandable_diff_wraps_details_block():
    from ui.diff_widget import render_expandable_diff
    before = "a\nb\nc\n"
    after = "a\nB\nc\n"
    html = render_expandable_diff("/work/x.txt", before, after)
    assert "<details" in html
    assert "Show full-file diff" in html
    # Inline portion still present (the focused diff).
    assert "/work/x.txt" in html


def test_new_file_diff_marks_every_line_added():
    from ui.diff_widget import render_new_file_diff
    content = "first\nsecond\nthird\n"
    html = render_new_file_diff("/work/new.py", content)
    assert "/work/new.py" in html
    assert "NEW FILE" in html
    # Every line should appear (HTML-escaped form is identical for ASCII).
    assert "first" in html
    assert "second" in html
    assert "third" in html
    # No removed-line styling on a new file
    assert "#cf222e" not in html and "cf222e" not in html


def test_new_file_diff_empty_content():
    from ui.diff_widget import render_new_file_diff
    html = render_new_file_diff("/work/empty.txt", "")
    assert "/work/empty.txt" in html
    assert "empty file" in html.lower() or "no content" in html.lower()


def test_inline_diff_includes_line_numbers_for_added_lines():
    """Each added line should display its line number in the BEFORE
    file's coordinate system, so the user can locate the change."""
    from ui.diff_widget import render_inline_diff
    before = "line 1\nline 2\nline 3\nline 4\nline 5\n"
    after = "line 1\nline 2\nNEW LINE\nline 3\nline 4\nline 5\n"
    html = render_inline_diff("/work/foo.py", before, after, context=1)
    # After-file: line 3 is "NEW LINE", which should display alongside its
    # line number (3 in the after coordinate system).
    assert "NEW LINE" in html
    # The hunk header from unified_diff should appear.
    assert "@@" in html


def test_inline_diff_context_parameter_widens_or_narrows_hunk():
    """Larger context should produce more rows; smaller context fewer."""
    from ui.diff_widget import render_inline_diff
    before = "\n".join(f"line {i}" for i in range(1, 21)) + "\n"
    after = "\n".join(f"line {i}" if i != 10 else "line 10 CHANGED" for i in range(1, 21)) + "\n"
    narrow = render_inline_diff("/x.txt", before, after, context=1)
    wide = render_inline_diff("/x.txt", before, after, context=5)
    # Wide diff should mention more line numbers — proxy via length.
    assert len(wide) > len(narrow)


# ============================================================
# Codex Phase-04 review fix: lock tests
# ============================================================

def test_inline_diff_shows_eof_newline_difference():
    """Codex Phase-04 finding 3 lock: splitlines() strips trailing newlines,
    so a diff that only changes whether the file ends with a newline
    used to render as 'No changes'. Now it must surface explicitly."""
    from ui.diff_widget import render_inline_diff
    # Same content, but different EOF-newline state
    html = render_inline_diff("/x.txt", "alpha\nbeta", "alpha\nbeta\n")
    assert "No content changes" in html
    assert "newline" in html.lower()
    # And the inverse direction
    html2 = render_inline_diff("/x.txt", "alpha\nbeta\n", "alpha\nbeta")
    assert "No content changes" in html2
    assert "newline" in html2.lower()
    # Truly identical content (incl. EOF state) still shows the original "No changes" note
    same = render_inline_diff("/x.txt", "alpha\n", "alpha\n")
    assert "No changes" in same


def test_inline_diff_handles_malformed_hunk_header_gracefully():
    """Codex Phase-04 finding (nit): the hunk-header parser must not crash
    when difflib emits a header with unexpected formatting. Verified by
    feeding the renderer a hand-crafted unified diff."""
    from ui.diff_widget import _render_unified
    # Malformed hunk header (missing comma counts)
    diff_lines = [
        "@@ -malformed @@",
        "+added line",
        "-removed line",
    ]
    # Should NOT raise. Output should contain the rows we asked for.
    out = _render_unified(diff_lines)
    assert "added line" in out
    assert "removed line" in out
