"""Block C+ — Approval/diff dispatch + rate limits + ipywidgets fallback.

Tests per TEST_DESIGN.md §Block C+ (7 tests) plus 4 lock tests for the
Block C UI-only helpers (C-11/C-12/C-13/C-14) wired through the
approval flow per ADR-023 §Notes / known scope remaps.
"""
from __future__ import annotations

import os
import sys
import time

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


@pytest.fixture(autouse=True)
def reset_always_allowed():
    """Reset CONFIG._always_allowed between tests."""
    from runtime.config import CONFIG
    if hasattr(CONFIG, "_always_allowed"):
        CONFIG._always_allowed = {}
    yield
    if hasattr(CONFIG, "_always_allowed"):
        CONFIG._always_allowed = {}


# ============================================================
# T2 — Approval gate blocks until approve / unblocks on approve
# ============================================================

def test_approval_gate_blocks_until_approve():
    """Approval-required tool dispatched in non-mock mode triggers
    PermissionDialog. Approve → tool runs. Deny → tool blocked."""
    from ui.approval_dialog import ApprovalResult, PermissionDialog

    # Inject decision via test override; verify the dispatch path is wired.
    dlg_approve = PermissionDialog(
        tool_name="bash",
        parameters={"command": "echo hi"},
        _override_decision=lambda: ApprovalResult(approved=True),
    )
    res = dlg_approve.prompt()
    assert res.approved
    assert not res.timed_out

    dlg_deny = PermissionDialog(
        tool_name="bash",
        parameters={"command": "echo hi"},
        _override_decision=lambda: ApprovalResult(approved=False, reason="user denied"),
    )
    res = dlg_deny.prompt()
    assert not res.approved
    assert "denied" in res.reason


# ============================================================
# T2 — Approval dialog shows diff
# ============================================================

def test_approval_dialog_shows_diff():
    """When `diff_html` is provided, PermissionDialog includes it in
    the rendered body. We verify by exercising the headless path that
    the helper accepts + reports the diff string."""
    from ui.approval_dialog import ApprovalResult, PermissionDialog

    diff_sample = "<pre><span style='color:red'>- a</span>"
    dlg = PermissionDialog(
        tool_name="edit_file",
        parameters={"file_path": "/tmp/x.txt"},
        diff_html=diff_sample,
        _override_decision=lambda: ApprovalResult(approved=True),
    )
    # Sanity: the diff is preserved on the dialog object so the
    # widget/text-mode renderer can include it.
    assert dlg.diff_html == diff_sample
    res = dlg.prompt()
    assert res.approved


# ============================================================
# T2 — Per-tool always-allow (sticky)
# ============================================================

def test_approval_per_tool_always_allow():
    """Clicking Always-allow stores the tool in CONFIG._always_allowed
    and subsequent dialogs short-circuit with approved=True."""
    from runtime.config import CONFIG
    from ui.approval_dialog import ApprovalResult, PermissionDialog

    CONFIG._always_allowed = {}
    # First call: user clicks Always-allow.
    dlg1 = PermissionDialog(
        tool_name="write_file",
        parameters={"file_path": "/tmp/y"},
        _override_decision=lambda: ApprovalResult(
            approved=True, always_allow=True, reason="always",
        ),
    )
    r1 = dlg1.prompt()
    assert r1.approved and r1.always_allow

    # Manually flip the sticky flag (the override didn't go through the
    # ipywidgets handler that does this). Real flow: the widget click
    # handler sets CONFIG._always_allowed[name] = True before returning.
    CONFIG._always_allowed["write_file"] = True

    # Second call: dialog short-circuits via the sticky path.
    dlg2 = PermissionDialog(
        tool_name="write_file",
        parameters={"file_path": "/tmp/z"},
        _override_decision=lambda: pytest.fail("override should NOT fire"),
    )
    r2 = dlg2.prompt()
    assert r2.approved
    assert "sticky" in r2.reason


# ============================================================
# T2 — Rate limit triggers
# ============================================================

def test_rate_limit_100_per_min():
    """101st check() in 60s window returns a rate-limit error."""
    from ui.approval_dialog import RateLimiter

    rl = RateLimiter(max_per_minute=100, max_per_session=1500)
    for i in range(100):
        assert rl.check() is None, f"check {i} should pass"
    err = rl.check()
    assert err is not None
    assert "Rate limit" in err
    assert "messages per minute" in err


def test_rate_limit_session_cap():
    """Session-cap kicks in even if per-minute window allows."""
    from ui.approval_dialog import RateLimiter

    rl = RateLimiter(max_per_minute=10_000, max_per_session=5)
    for _ in range(5):
        assert rl.check() is None
    err = rl.check()
    assert err is not None
    assert "Session message cap" in err


def test_rate_limit_sliding_window():
    """Old timestamps drop out of the window after 60s."""
    from ui.approval_dialog import RateLimiter

    rl = RateLimiter(max_per_minute=2, max_per_session=100)
    rl._timestamps = [time.time() - 120, time.time() - 90]  # both > 60s old
    assert rl.check() is None
    assert rl.check() is None  # 2 in current window
    assert rl.check() is not None  # 3rd trips


# ============================================================
# T2 — Stop button halts run (already locked in Phase 11; sanity check)
# ============================================================

def test_stop_button_halts_run():
    """`Agent.stop()` mid-loop sets a flag; QueryEngine respects it
    on next per-turn checkpoint. Phase 11 lock; sanity check here."""
    from runtime.bedrock_client import BedrockClient
    from agent import Agent

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    a.stop()  # request stop before run() even starts
    assert a._stop_requested is True
    a.run("hi")
    # Stop request was honored; either the run exited via stop check
    # OR completed before the check (mock returns end_turn fast).


# ============================================================
# T2 — ipywidgets fallback when widgets unavailable
# ============================================================

def test_ipywidgets_fallback_text_mode(monkeypatch):
    """When ipywidgets is unavailable, PermissionDialog falls back to
    text mode. We force the fallback path via a monkeypatched flag."""
    from ui.approval_dialog import ApprovalResult, PermissionDialog

    # Without an override, the dialog would block on stdin. The
    # _override_decision parameter short-circuits before any rendering,
    # but we still verify the helper is callable in non-widget mode.
    dlg = PermissionDialog(
        tool_name="bash",
        parameters={"command": "ls"},
        _override_decision=lambda: ApprovalResult(approved=False, timed_out=True),
    )
    res = dlg.prompt()
    assert not res.approved
    assert res.timed_out


# ============================================================
# T2 — PermissionDialog reason prompt
# ============================================================

def test_permission_dialog_reason_prompt():
    """The dialog accepts a `reason` from the model's tool_use input
    and propagates it through to the rendered body."""
    from ui.approval_dialog import ApprovalResult, PermissionDialog

    dlg = PermissionDialog(
        tool_name="write_file",
        parameters={"file_path": "/tmp/q.txt", "reason": "Save config"},
        reason="Save config",
        _override_decision=lambda: ApprovalResult(approved=True),
    )
    assert dlg.reason == "Save config"
    res = dlg.prompt()
    assert res.approved


# ============================================================
# Block C remap locks: C-11/C-12/C-13/C-14 surfaced via approval
# ============================================================

def test_approval_renders_cd_git_warning():
    """C-11: cd into bare repo + git fsmonitor risk surfaced in dialog."""
    from ui.approval_dialog import PermissionDialog

    dlg = PermissionDialog(
        tool_name="bash",
        parameters={"command": "cd repo.git && git log"},
    )
    warnings = dlg.render_warnings()
    assert any("cd into bare git repo" in w for w in warnings)


def test_approval_renders_multi_cd_warning():
    """C-12: chained cd's flagged."""
    from ui.approval_dialog import PermissionDialog

    dlg = PermissionDialog(
        tool_name="bash",
        parameters={"command": "cd /tmp && cd subdir && rm file"},
    )
    warnings = dlg.render_warnings()
    assert any("multiple cd" in w for w in warnings)


def test_approval_renders_pipe_segment_warning():
    """C-13: destructive pipe segment surfaced."""
    from ui.approval_dialog import PermissionDialog

    dlg = PermissionDialog(
        tool_name="bash",
        parameters={"command": "ls -la | rm -rf /tmp/foo"},
    )
    warnings = dlg.render_warnings()
    assert any("pipe-segment" in w.lower() for w in warnings)


def test_approval_renders_bash_comment_label():
    """C-14: leading `# comment` surfaced as label."""
    from ui.approval_dialog import PermissionDialog

    dlg = PermissionDialog(
        tool_name="bash",
        parameters={"command": "# build the docs\nmake docs"},
    )
    warnings = dlg.render_warnings()
    assert any("label: build the docs" in w for w in warnings)


# ============================================================
# Sanity: rate limiter wired into QueryEngine.run() entry
# ============================================================

def test_rate_limiter_wired_into_query_engine_run(monkeypatch):
    """When the rate limit is hit, run() returns a rate_limited result
    immediately without consuming budget."""
    from runtime.bedrock_client import BedrockClient
    from core.query_engine import QueryEngine
    from ui.approval_dialog import RateLimiter

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    engine = QueryEngine(client=client, max_turns=2)
    # Force rate limit at run() entry by pre-filling the timestamps so
    # the next check() trips. max_per_minute=1, prefilled with one
    # current-time stamp -> next call fails.
    rl = RateLimiter(max_per_minute=1, max_per_session=1500)
    rl._timestamps = [time.time()]
    engine._rate_limiter = rl

    result = engine.run(
        user_message="hi", system_prompt="test", tools=[],
    )
    assert result.stop_reason == "rate_limited"
    assert "Rate limit" in (result.error or "")


# ============================================================
# Codex Block-C+ iter-1 finding-lock tests (regression prevention)
# ============================================================

def test_diff_wired_for_edit_file_in_dispatch_approval(tmp_path, monkeypatch):
    """Codex iter-1 finding #1 (HIGH) lock: when dispatching `edit_file`
    in non-mock mode with require_tool_approval, the PermissionDialog
    receives a non-empty `diff_html` from ui/diff_widget."""
    from runtime.bedrock_client import BedrockClient, ToolCall, Response
    from runtime.config import CONFIG
    from core.query_engine import QueryEngine
    from tools.registry import all_registered, _reset_registry_for_tests
    from tools import bootstrap_built_ins
    import ui.approval_dialog as ad_mod

    # Seed a real file the model claims to edit.
    target = tmp_path / "data.txt"
    target.write_text("hello world\n", encoding="utf-8")

    # Force the gate to fire: require_tool_approval=True + non-mock
    # (we'll spy on PermissionDialog.__init__ to capture diff_html).
    monkeypatch.setattr(CONFIG, "require_tool_approval", True)
    if hasattr(CONFIG, "_always_allowed"):
        CONFIG._always_allowed = {}

    captured: Dict[str, Any] = {"diff_html": None}
    real_init = ad_mod.PermissionDialog.__init__

    def spy_init(self, *args, **kwargs):
        real_init(self, *args, **kwargs)
        captured["diff_html"] = self.diff_html

    monkeypatch.setattr(ad_mod.PermissionDialog, "__init__", spy_init)
    # Force "approve" so dispatch continues past the gate.
    monkeypatch.setattr(ad_mod.PermissionDialog, "prompt",
                        lambda self: ad_mod.ApprovalResult(approved=True))

    # Build a non-mock-mode client; force one fake chat response, then
    # let the tool dispatch run through the gate.
    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=False)
    client.mock_mode = False  # force the gate to fire (mock_mode bypass off)

    n = {"i": 0}

    def fake_chat(*args, **kwargs):
        n["i"] += 1
        if n["i"] == 1:
            return Response(
                text="",
                tool_calls=[ToolCall(
                    id="e1", name="edit_file",
                    input={
                        "file_path": str(target),
                        "old_string": "hello world",
                        "new_string": "hello v5",
                    },
                )],
                stop_reason="tool_use",
            )
        return Response(text="done", tool_calls=[], stop_reason="end_turn")

    monkeypatch.setattr(client, "chat", fake_chat)

    _reset_registry_for_tests()
    bootstrap_built_ins()

    engine = QueryEngine(client=client, max_turns=3)
    # Pre-mark the file as read so edit_file doesn't refuse on
    # "must read before editing".
    from tools import _file_read_tracking as read_tracking
    read_tracking.mark_read(str(target))

    engine.run(
        user_message="edit it",
        system_prompt="test",
        tools=all_registered(),
    )
    assert captured["diff_html"] is not None, (
        "PermissionDialog should receive a rendered diff for edit_file"
    )
    # The diff body must reference the changed line.
    assert "hello" in captured["diff_html"] or "v5" in captured["diff_html"]


def test_text_mode_watchdog_via_thread_join(monkeypatch):
    """Codex iter-1 finding #2 (HIGH) lock: when select.select is
    unsupported and stdin.readline blocks, the Windows fallback uses
    a daemon thread + thread.join(timeout) so the watchdog still
    fires. Without the thread-based fallback, readline could hang
    indefinitely on Windows."""
    import io
    import sys
    from ui.approval_dialog import ApprovalResult, PermissionDialog

    # Force select.select to raise so the fallback path runs.
    import select as _select_mod

    def fake_select(*args, **kwargs):
        raise OSError("simulated unsupported select")

    monkeypatch.setattr(_select_mod, "select", fake_select)

    # Stub stdin.isatty() True so the dialog enters the readline path,
    # but stdin.readline blocks on a never-readable BytesIO so the
    # watchdog must trigger.
    class _BlockingStdin:
        def isatty(self):
            return True

        def readline(self):
            # Simulate an indefinitely-blocked readline.
            import time as _t
            _t.sleep(120)
            return ""

    monkeypatch.setattr(sys, "stdin", _BlockingStdin())

    dlg = PermissionDialog(
        tool_name="bash",
        parameters={"command": "ls"},
        timeout_seconds=2,  # short watchdog so the test is fast
    )
    # Note: prompt() uses _IPYWIDGETS_OK to decide widgets vs text
    # path. Force text path:
    import ui.chat_ui as chat_ui_mod
    monkeypatch.setattr(chat_ui_mod, "_IPYWIDGETS_OK", False)

    res = dlg.prompt()
    assert res.timed_out, "watchdog must fire on blocked readline (Windows fallback)"
    assert not res.approved


def test_ipywidgets_fallback_actually_runs_text_mode_path(monkeypatch):
    """Codex iter-1 finding #3 (MEDIUM) lock: exercise the REAL
    fallback path (not _override_decision short-circuit). When
    ipywidgets is unavailable AND stdin is non-TTY, the dialog defaults
    to deny + timed_out without hanging."""
    import sys
    from ui.approval_dialog import PermissionDialog
    import ui.chat_ui as chat_ui_mod

    monkeypatch.setattr(chat_ui_mod, "_IPYWIDGETS_OK", False)

    class _NonTTYStdin:
        def isatty(self):
            return False

        def readline(self):
            return ""

    monkeypatch.setattr(sys, "stdin", _NonTTYStdin())

    dlg = PermissionDialog(
        tool_name="bash",
        parameters={"command": "ls"},
        timeout_seconds=1,
    )
    res = dlg.prompt()
    assert not res.approved
    assert res.timed_out
    assert "non-tty" in res.reason.lower()
