"""Phase 09 unit tests: subagent/handoff.py — bounded sub-agent handoff block.

Locks PORT_LOG #023: ADAPT port of v4's _build_subagent_handoff_block.
"""
from __future__ import annotations

import os
import sys

import pytest

_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


def test_handoff_returns_empty_when_no_inputs():
    from subagent.handoff import build_handoff_block
    assert build_handoff_block() == ""


def test_handoff_status_slice(tmp_path):
    from subagent.handoff import build_handoff_block
    sp = tmp_path / "AGENT_STATUS.md"
    sp.write_text("Phase 9 in progress\n", encoding="utf-8")
    out = build_handoff_block(status_path=str(sp))
    assert "AGENT_STATUS.md slice" in out
    assert "Phase 9 in progress" in out
    assert "(truncated)" not in out


def test_handoff_status_truncation(tmp_path):
    from subagent.handoff import build_handoff_block
    sp = tmp_path / "AGENT_STATUS.md"
    sp.write_text("X" * 5000, encoding="utf-8")
    out = build_handoff_block(status_path=str(sp))
    assert "(truncated)" in out
    # The X's were trimmed to 4000 chars, so the output is bounded
    assert out.count("X") <= 4000


def test_handoff_todos_section():
    from subagent.handoff import build_handoff_block
    todos = "1. Finish Phase 9\n2. Run Codex"
    out = build_handoff_block(todos_text=todos)
    assert "Active TODOs" in out
    assert "Finish Phase 9" in out


def test_handoff_todos_truncation():
    from subagent.handoff import build_handoff_block
    big = "y" * 3000
    out = build_handoff_block(todos_text=big)
    assert "todos truncated" in out


def test_handoff_recent_files_dedup_and_cap():
    from subagent.handoff import build_handoff_block
    files = ["/a.py", "/b.py", "/a.py"] + [f"/x{i}.py" for i in range(15)]
    out = build_handoff_block(recent_files=files)
    assert "Files edited in parent session" in out
    # Caps at 10 most-recent unique files
    line_count = sum(1 for line in out.splitlines() if line.startswith("- "))
    assert line_count <= 10


def test_handoff_sanitizes_boundary_marker(tmp_path):
    """A user-supplied AGENT_STATUS containing the cache-boundary marker must
    not corrupt downstream cache-block splitting. See v4 sagemaker_agent.py:7754.

    Contract: every occurrence of `# === DYNAMIC ===` is replaced by
    `# === DYNAMIC === (sanitized)`. So the count of unsanitized markers
    (those NOT followed by ` (sanitized)`) is zero."""
    from subagent.handoff import build_handoff_block
    sp = tmp_path / "AGENT_STATUS.md"
    sp.write_text("Status info\n# === DYNAMIC ===\nMore info\n", encoding="utf-8")
    out = build_handoff_block(status_path=str(sp))
    assert "# === DYNAMIC === (sanitized)" in out
    # Total marker count == sanitized marker count (every marker is sanitized)
    total_markers = out.count("# === DYNAMIC ===")
    sanitized_markers = out.count("# === DYNAMIC === (sanitized)")
    assert total_markers == sanitized_markers, (
        f"unsanitized cache boundary marker leaked: "
        f"{total_markers - sanitized_markers} unsanitized occurrence(s)"
    )


def test_handoff_fail_quiet_on_unreadable_status():
    """Missing status_path must not raise — sub-agent spawn must be robust."""
    from subagent.handoff import build_handoff_block
    out = build_handoff_block(status_path="/this/does/not/exist/xyz.md")
    assert out == ""  # nothing else provided either


def test_handoff_combined_sections(tmp_path):
    from subagent.handoff import build_handoff_block
    sp = tmp_path / "AGENT_STATUS.md"
    sp.write_text("Status\n", encoding="utf-8")
    out = build_handoff_block(
        status_path=str(sp),
        todos_text="1. foo\n2. bar",
        recent_files=["/x.py", "/y.py"],
    )
    assert "AGENT_STATUS.md slice" in out
    assert "Active TODOs" in out
    assert "Files edited" in out
    # Header
    assert out.startswith("# Sub-agent Handoff (parent context, bounded)")
