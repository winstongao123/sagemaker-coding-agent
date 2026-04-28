"""V4.10.4: Bounded sub-agent handoff block.

Tests:
1. Empty state (no AGENT_STATUS, no todos, no diffs) → empty string.
2. AGENT_STATUS only → handoff includes the slice, bounded.
3. AGENT_STATUS oversized → truncated to _SUBAGENT_STATUS_MAX_CHARS with "(truncated)" marker.
4. Todos present → handoff includes them, bounded.
5. Recent diffs present → handoff lists last N file paths (no diff bodies).
6. All three sources present → all included, deterministic order.
7. Disabled via CONFIG flag → empty string.
8. Cache-prefix safety: handoff text never contains the cache boundary marker (would split the cache wrong).
9. Never raises (bogus paths, locked files, broken state).
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sagemaker_agent as sa


def _reset_state():
    """Clear globals so tests don't bleed state into each other."""
    sa._TODOS.clear() if hasattr(sa, "_TODOS") else None
    if hasattr(sa, "_RECENT_DIFFS"):
        with sa._RECENT_DIFFS_LOCK:
            sa._RECENT_DIFFS.clear()


def _set_workspace(monkeypatch=None) -> str:
    tmp = tempfile.mkdtemp(prefix="v410_handoff_")
    sa.CONFIG.workspace = tmp
    return tmp


def test_empty_state_returns_empty():
    _reset_state()
    saved_ws = sa.CONFIG.workspace
    try:
        ws = _set_workspace()
        # No AGENT_STATUS file, no todos, no diffs
        out = sa._build_subagent_handoff_block()
        # When workspace has no AGENT_STATUS the slice is omitted.
        # Todos empty → omitted. Diffs empty → omitted. Should be empty.
        assert out == "", f"Expected empty handoff for empty state, got: {out!r}"
    finally:
        sa.CONFIG.workspace = saved_ws


def test_agent_status_only_included_and_bounded():
    _reset_state()
    saved_ws = sa.CONFIG.workspace
    try:
        ws = _set_workspace()
        with open(os.path.join(ws, "AGENT_STATUS.md"), "w", encoding="utf-8") as f:
            f.write("# Goal\n- Ship v4.10.4\n## Plan\n- Step 1\n- Step 2\n")
        out = sa._build_subagent_handoff_block()
        assert "Sub-agent Handoff" in out
        assert "AGENT_STATUS.md slice" in out
        assert "Ship v4.10.4" in out
        assert len(out) <= sa._SUBAGENT_STATUS_MAX_CHARS + 500  # slice + markers
    finally:
        sa.CONFIG.workspace = saved_ws


def test_agent_status_oversized_truncated():
    _reset_state()
    saved_ws = sa.CONFIG.workspace
    try:
        ws = _set_workspace()
        big = "X" * (sa._SUBAGENT_STATUS_MAX_CHARS + 5_000)
        with open(os.path.join(ws, "AGENT_STATUS.md"), "w", encoding="utf-8") as f:
            f.write(big)
        out = sa._build_subagent_handoff_block()
        assert "(truncated)" in out, "Oversized AGENT_STATUS should be marked truncated"
        # Sliced content should not exceed the cap (modulo header bytes)
        slice_len = out.count("X")
        assert slice_len <= sa._SUBAGENT_STATUS_MAX_CHARS, (
            f"Truncated slice length {slice_len} exceeded cap {sa._SUBAGENT_STATUS_MAX_CHARS}"
        )
    finally:
        sa.CONFIG.workspace = saved_ws


def test_todos_included_when_present():
    _reset_state()
    saved_ws = sa.CONFIG.workspace
    try:
        ws = _set_workspace()
        sa._TODOS.append({"content": "Implement handoff", "status": "in_progress", "activeForm": "Implementing handoff"})
        sa._TODOS.append({"content": "Write tests", "status": "pending", "activeForm": "Writing tests"})
        out = sa._build_subagent_handoff_block()
        assert "Active TODOs" in out
        assert "Implement handoff" in out
        assert "Write tests" in out
    finally:
        sa.CONFIG.workspace = saved_ws
        _reset_state()


def test_recent_diffs_listed_no_diff_bodies():
    _reset_state()
    saved_ws = sa.CONFIG.workspace
    try:
        ws = _set_workspace()
        with sa._RECENT_DIFFS_LOCK:
            sa._RECENT_DIFFS.append({"file": "/a/path/foo.py", "diff": "+ HUGE DIFF BODY", "time": 1.0})
            sa._RECENT_DIFFS.append({"file": "/a/path/bar.py", "diff": "+ ANOTHER", "time": 2.0})
        out = sa._build_subagent_handoff_block()
        assert "Files edited in parent session" in out
        assert "foo.py" in out
        assert "bar.py" in out
        # Diff bodies must NOT be included (would blow the budget)
        assert "HUGE DIFF BODY" not in out, "Handoff must not contain diff bodies"
    finally:
        sa.CONFIG.workspace = saved_ws
        _reset_state()


def test_all_three_sections_when_all_present():
    _reset_state()
    saved_ws = sa.CONFIG.workspace
    try:
        ws = _set_workspace()
        with open(os.path.join(ws, "AGENT_STATUS.md"), "w", encoding="utf-8") as f:
            f.write("# Status\n## Goal\n- Test\n")
        sa._TODOS.append({"content": "T1", "status": "in_progress", "activeForm": "Working on T1"})
        with sa._RECENT_DIFFS_LOCK:
            sa._RECENT_DIFFS.append({"file": "/x/y.py", "diff": "+ ...", "time": 1.0})
        out = sa._build_subagent_handoff_block()
        assert "AGENT_STATUS.md slice" in out
        assert "Active TODOs" in out
        assert "Files edited" in out
    finally:
        sa.CONFIG.workspace = saved_ws
        _reset_state()


def test_disabled_via_config_returns_empty():
    _reset_state()
    saved_ws = sa.CONFIG.workspace
    saved_flag = getattr(sa.CONFIG, "enable_subagent_handoff", True)
    try:
        ws = _set_workspace()
        with open(os.path.join(ws, "AGENT_STATUS.md"), "w", encoding="utf-8") as f:
            f.write("# Goal\n- Should not appear\n")
        sa.CONFIG.enable_subagent_handoff = False
        out = sa._build_subagent_handoff_block()
        assert out == "", f"Disabled flag should yield empty handoff; got: {out!r}"
    finally:
        sa.CONFIG.workspace = saved_ws
        sa.CONFIG.enable_subagent_handoff = saved_flag
        _reset_state()


def test_handoff_does_not_contain_cache_boundary_marker():
    """Critical: handoff text must NOT include the '# === DYNAMIC ===' marker.
    If it did, BedrockClient.chat would split the cache at the wrong point."""
    _reset_state()
    saved_ws = sa.CONFIG.workspace
    try:
        ws = _set_workspace()
        with open(os.path.join(ws, "AGENT_STATUS.md"), "w", encoding="utf-8") as f:
            f.write("normal status content\n")
        sa._TODOS.append({"content": "T1", "status": "in_progress", "activeForm": "Working"})
        out = sa._build_subagent_handoff_block()
        assert "# === DYNAMIC ===" not in out, (
            "Handoff text must not contain the cache boundary marker"
        )
    finally:
        sa.CONFIG.workspace = saved_ws
        _reset_state()


def test_handoff_sanitizes_user_content_with_boundary_marker():
    """Codex 2026-04-28 fix: if a user's AGENT_STATUS or todo content
    literally contains the cache boundary marker, the handoff sanitizer
    must replace it before injection."""
    _reset_state()
    saved_ws = sa.CONFIG.workspace
    try:
        ws = _set_workspace()
        # User-supplied AGENT_STATUS that happens to contain the marker.
        with open(os.path.join(ws, "AGENT_STATUS.md"), "w", encoding="utf-8") as f:
            f.write("Plan:\n- Do something\n# === DYNAMIC ===\n- Another step\n")
        out = sa._build_subagent_handoff_block()
        # The literal marker must NOT appear in the handoff output.
        assert "# === DYNAMIC ===\n" not in out and "# === DYNAMIC ===" not in out.replace(
            "# === DYNAMIC === (sanitized)", ""
        ), (
            f"Sanitizer must replace literal boundary marker in user content; got: {out!r}"
        )
        # The sanitized form should appear instead so the user can see it was intercepted.
        assert "(sanitized)" in out
    finally:
        sa.CONFIG.workspace = saved_ws
        _reset_state()


def test_handoff_sanitizes_user_todos_with_boundary_marker():
    """Same protection but on the todo content path."""
    _reset_state()
    saved_ws = sa.CONFIG.workspace
    try:
        ws = _set_workspace()
        sa._TODOS.append({
            "content": "Sneaky todo with # === DYNAMIC === inside it",
            "status": "in_progress",
            "activeForm": "Trying to break the cache",
        })
        out = sa._build_subagent_handoff_block()
        assert "Sneaky todo with" in out
        # The literal marker cannot appear unsanitized.
        marker_count = out.count("# === DYNAMIC ===")
        sanitized_count = out.count("# === DYNAMIC === (sanitized)")
        assert marker_count == sanitized_count, (
            f"All marker occurrences should be sanitized; raw={marker_count}, "
            f"sanitized={sanitized_count}"
        )
    finally:
        sa.CONFIG.workspace = saved_ws
        _reset_state()


def test_never_raises_on_bogus_paths_or_state():
    """A sub-agent spawn MUST NOT fail because handoff probing misbehaved.
    Any internal exception must be swallowed."""
    _reset_state()
    saved_ws = sa.CONFIG.workspace
    try:
        sa.CONFIG.workspace = "/this/path/does/not/exist/anywhere"
        # Should not raise
        out = sa._build_subagent_handoff_block()
        assert isinstance(out, str)
    finally:
        sa.CONFIG.workspace = saved_ws
        _reset_state()


if __name__ == "__main__":
    tests = [
        ("empty_state_returns_empty", test_empty_state_returns_empty),
        ("agent_status_only_included_and_bounded", test_agent_status_only_included_and_bounded),
        ("agent_status_oversized_truncated", test_agent_status_oversized_truncated),
        ("todos_included_when_present", test_todos_included_when_present),
        ("recent_diffs_listed_no_diff_bodies", test_recent_diffs_listed_no_diff_bodies),
        ("all_three_sections_when_all_present", test_all_three_sections_when_all_present),
        ("disabled_via_config_returns_empty", test_disabled_via_config_returns_empty),
        ("handoff_does_not_contain_cache_boundary_marker", test_handoff_does_not_contain_cache_boundary_marker),
        ("handoff_sanitizes_user_content_with_boundary_marker", test_handoff_sanitizes_user_content_with_boundary_marker),
        ("handoff_sanitizes_user_todos_with_boundary_marker", test_handoff_sanitizes_user_todos_with_boundary_marker),
        ("never_raises_on_bogus_paths_or_state", test_never_raises_on_bogus_paths_or_state),
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
            import traceback
            traceback.print_exc()
            print(f"ERROR {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
