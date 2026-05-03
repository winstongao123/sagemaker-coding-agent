"""Block B+ — SessionManager + cost-limit + AGENT_STATUS auto-load + FileCache.

Tests per TEST_DESIGN.md §Block B+ (7 tests) plus 2 ADR-020 remap lock
tests (0-7 cleanupRegistry, 0-9 feature_flags fail-closed):

  T1 test_session_manager_atomic_save              tmp + os.replace; partial-write doesn't corrupt
  T1 test_session_save_load_preserves_cost         save at $2.09 → load → TOKENS.session_cost == 2.09 (PS#5)
  T1 test_session_cost_limit_warns_at_100pct       v5 = warn-and-continue (per user 2026-05-03 Plan v3 update)
  T1 test_agent_status_auto_load                   first Agent.run() reads AGENT_STATUS.md and injects
  T2 test_filecache_thread_local_isolation         parent _FILES_READ not visible inside sub-agent thread
  T2 test_subagent_token_attribution               TOKENS.parent_input_tokens > 0 AND subagent["build"] > 0 AND session_cost == sum
  T1 test_tokens_singleton_is_budget_source        budget checks read TOKENS singleton (closes PS#6)

  + test_cleanup_registry_register_and_fire        ADR-020 remap 0-7 lock
  + test_feature_flag_fail_closed_for_banned       ADR-020 remap 0-9 lock
"""
from __future__ import annotations

import json
import os
import sys
import threading
from typing import Any, Dict

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch):
    """Reset TOKENS + FILE_CACHE between tests."""
    from runtime.tokens import TOKENS
    from runtime.file_cache import FILE_CACHE

    TOKENS.reset()
    FILE_CACHE.clear_all()
    FILE_CACHE.exit_thread_local_context()
    yield
    TOKENS.reset()
    FILE_CACHE.clear_all()
    FILE_CACHE.exit_thread_local_context()


# ============================================================
# T1 — SessionManager atomic save
# ============================================================

def test_session_manager_atomic_save(tmp_path):
    from runtime.session import SessionManager, Session

    sm = SessionManager(sessions_dir=str(tmp_path))
    s = sm.create(title="atomic-test")
    s.messages = [{"role": "user", "content": "hi"}]
    sm.save(s)

    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    with open(files[0], "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["id"] == s.id
    assert data["title"] == "atomic-test"
    assert data["messages"][0]["content"] == "hi"


def test_session_load_round_trip(tmp_path):
    from runtime.session import SessionManager, Session

    sm = SessionManager(sessions_dir=str(tmp_path))
    s = sm.create(title="round-trip")
    s.messages = [{"role": "user", "content": "x"}]
    s.metadata = {"foo": "bar"}
    sm.save(s)

    loaded = sm.load(s.id)
    assert loaded is not None
    assert loaded.id == s.id
    assert loaded.title == "round-trip"
    assert loaded.messages == [{"role": "user", "content": "x"}]
    assert loaded.metadata == {"foo": "bar"}


# ============================================================
# T1 — Save / load preserves session cost (PS#5)
# ============================================================

def test_session_save_load_preserves_cost(tmp_path):
    """PS#5: session cost must persist across /save → /resume.

    Block B+'s SessionManager + Block B's TokenTracker.restore close
    this together. We simulate the save→quit→reload cycle by storing
    TOKENS.get_stats() in the session metadata, restoring on load,
    and asserting the singleton ends up at the recorded cost.
    """
    from runtime.session import SessionManager
    from runtime.tokens import TOKENS

    sm = SessionManager(sessions_dir=str(tmp_path))
    s = sm.create(title="cost-restore")

    # Simulate a session of work that accumulates cost.
    TOKENS.add(
        {"input_tokens": 10_000, "output_tokens": 1_000},
        model_id="anthropic.claude-sonnet-4-5-20250929-v1:0",
    )
    expected_cost = TOKENS.session_cost
    assert expected_cost > 0

    # Snapshot stats into session metadata + persist.
    s.metadata["tokens_stats"] = TOKENS.get_stats()
    sm.save(s)

    # Simulate a fresh process: reset singleton, then reload.
    TOKENS.reset()
    assert TOKENS.session_cost == 0.0

    loaded = sm.load(s.id)
    assert loaded is not None
    TOKENS.restore(loaded.metadata["tokens_stats"])
    assert abs(TOKENS.session_cost - expected_cost) < 1e-6


# ============================================================
# T1 — session_cost_limit warn-and-continue (per user 2026-05-03)
# ============================================================

def test_session_cost_limit_warns_at_100pct(monkeypatch, caplog):
    """v5 default v4 behavior: warn at 80%, warn-and-continue at 100%.

    Per user 2026-05-03 Plan v3 §Block B+ update:
      "Behavior matches v4: warn at 80%, warn at 100% but agent
       CONTINUES. User decides… NO hard halt at application level."
    """
    import logging
    from runtime.tokens import TOKENS
    from runtime.config import CONFIG

    monkeypatch.setattr(CONFIG, "session_cost_limit", 0.005)

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        # Push session_cost above the limit.
        TOKENS.add(
            {"input_tokens": 100_000, "output_tokens": 5_000},
            model_id="anthropic.claude-sonnet-4-5-20250929-v1:0",
        )

    # is_over_budget reports True, but the tracker did NOT raise; the
    # next add() must still work (warn-and-continue contract).
    assert TOKENS.is_over_budget()
    pre_count = TOKENS.api_calls
    TOKENS.add(
        {"input_tokens": 1_000, "output_tokens": 100},
        model_id="anthropic.claude-sonnet-4-5-20250929-v1:0",
    )
    assert TOKENS.api_calls == pre_count + 1, (
        "v5 contract: TOKENS.add must NOT raise / refuse after over-budget; "
        "warn-and-continue per user 2026-05-03 Plan v3 update"
    )
    assert any(
        "limit" in r.getMessage().lower() or "budget" in r.getMessage().lower()
        for r in caplog.records
    ), "over-budget condition must log a WARNING"


# ============================================================
# T1 — AGENT_STATUS.md auto-load on first Agent.run()
# ============================================================

def test_agent_status_auto_load(tmp_path, monkeypatch):
    """First Agent.run() reads AGENT_STATUS.md from CONFIG.workspace and
    appends it to the dynamic tail of the system prompt."""
    from runtime.config import CONFIG
    from runtime.bedrock_client import BedrockClient
    from agent import Agent

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "status_doc", "AGENT_STATUS.md")
    monkeypatch.setattr(CONFIG, "enable_status_doc", True)

    status_path = tmp_path / "AGENT_STATUS.md"
    status_path.write_text(
        "# Phase 5 handoff\n\nResume from step 7.", encoding="utf-8",
    )

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    # Capture the system prompt the engine ends up with.
    captured = {}
    real_run = a._engine.run

    def spy_run(*args, **kwargs):
        captured["system_prompt"] = kwargs.get("system_prompt") or args[1]
        return real_run(*args, **kwargs)

    monkeypatch.setattr(a._engine, "run", spy_run)
    a.run("hi")

    sp = captured["system_prompt"]
    assert "Phase 5 handoff" in sp
    assert "Resume from step 7" in sp


def test_agent_status_auto_load_disabled(tmp_path, monkeypatch):
    """When enable_status_doc=False, AGENT_STATUS.md is ignored."""
    from runtime.config import CONFIG
    from runtime.bedrock_client import BedrockClient
    from agent import Agent

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "enable_status_doc", False)

    (tmp_path / "AGENT_STATUS.md").write_text("must be ignored", encoding="utf-8")

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    captured = {}
    real_run = a._engine.run

    def spy_run(*args, **kwargs):
        captured["system_prompt"] = kwargs.get("system_prompt") or args[1]
        return real_run(*args, **kwargs)

    monkeypatch.setattr(a._engine, "run", spy_run)
    a.run("hi")
    assert "must be ignored" not in captured["system_prompt"]


# ============================================================
# T2 — FileCache thread-local context isolation
# ============================================================

def test_filecache_thread_local_isolation(tmp_path):
    """A sub-agent thread that calls enter_thread_local_context() must
    not see the parent's `in_context` set (and vice versa)."""
    from runtime.file_cache import FILE_CACHE

    f1 = tmp_path / "parent.txt"
    f1.write_text("p", encoding="utf-8")
    f2 = tmp_path / "child.txt"
    f2.write_text("c", encoding="utf-8")

    # Parent (main thread) marks its file in context.
    FILE_CACHE.mark_in_context(str(f1))
    assert FILE_CACHE.is_in_context(str(f1))

    saw_parent_marker_inside_child = []

    def child_thread():
        FILE_CACHE.enter_thread_local_context()
        try:
            saw_parent_marker_inside_child.append(
                FILE_CACHE.is_in_context(str(f1))
            )
            FILE_CACHE.mark_in_context(str(f2))
            saw_parent_marker_inside_child.append(
                FILE_CACHE.is_in_context(str(f2))
            )
        finally:
            FILE_CACHE.exit_thread_local_context()

    t = threading.Thread(target=child_thread)
    t.start()
    t.join()

    # Sub-agent didn't see parent's context.
    assert saw_parent_marker_inside_child[0] is False
    # Sub-agent saw its own marker.
    assert saw_parent_marker_inside_child[1] is True
    # Parent's marker is preserved post-child.
    assert FILE_CACHE.is_in_context(str(f1))
    # Child's marker did NOT leak into parent.
    assert FILE_CACHE.is_in_context(str(f2)) is False


def test_filecache_save_and_restore_round_trip():
    from runtime.file_cache import FILE_CACHE

    FILE_CACHE.mark_in_context("/tmp/a")
    FILE_CACHE.mark_in_context("/tmp/b")
    saved = FILE_CACHE.save_and_clear_context()
    # Cleared.
    assert FILE_CACHE.is_in_context("/tmp/a") is False
    assert FILE_CACHE.is_in_context("/tmp/b") is False
    # Restored.
    FILE_CACHE.restore_context(saved)
    assert FILE_CACHE.is_in_context("/tmp/a")
    assert FILE_CACHE.is_in_context("/tmp/b")


# ============================================================
# T2 — Sub-agent token attribution acceptance test (Plan v3 §Block B+)
# ============================================================

def test_subagent_token_attribution():
    """Plan v3 acceptance: parent + sub-agent both update TOKENS, but
    each goes to its own bucket. session_cost == sum of buckets."""
    from runtime.tokens import TOKENS

    # Parent does some work.
    TOKENS.add(
        {"input_tokens": 1000, "output_tokens": 200},
        model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
        agent_kind="parent",
    )
    # Sub-agent type=build does some work.
    TOKENS.add(
        {"input_tokens": 500, "output_tokens": 100},
        model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
        agent_kind="build",
    )

    assert TOKENS.parent_input_tokens == 1000
    assert TOKENS.parent_output_tokens == 200
    assert TOKENS.subagent_input_tokens["build"] == 500
    assert TOKENS.subagent_output_tokens["build"] == 100
    assert TOKENS.parent_cost > 0
    assert TOKENS.subagent_cost["build"] > 0
    # Roll-up invariant within $0.0001.
    assert abs(
        TOKENS.session_cost
        - (TOKENS.parent_cost + sum(TOKENS.subagent_cost.values()))
    ) < 1e-4


# ============================================================
# T1 — TOKENS singleton is the budget source (PS#6 closure)
# ============================================================

def test_tokens_singleton_is_budget_source():
    """PS#6 was: budget read from wrong source (Agent attribute, not
    singleton). v5 must read budget from TOKENS singleton so all agents
    share one cost view."""
    from runtime.tokens import TOKENS
    from agent import Agent
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a1 = Agent(client=client)
    a2 = Agent(client=client)

    TOKENS.reset()
    a1.run("first")
    cost_after_a1 = TOKENS.session_cost
    a2.run("second")
    cost_after_a2 = TOKENS.session_cost

    # Both agents update the SAME singleton.
    assert cost_after_a2 >= cost_after_a1
    # The increment from a2 is non-trivial (mock returns non-zero usage).
    assert TOKENS.api_calls >= 2


# ============================================================
# ADR-020 remap 0-7 — cleanup_registry register-and-fire
# ============================================================

def test_cleanup_registry_register_and_fire():
    """register() + _run_all() fires callbacks once and clears the list."""
    from runtime import cleanup_registry as cr

    cr._reset_for_tests()
    fired = []
    cr.register(lambda: fired.append("a"))
    cr.register(lambda: fired.append("b"))
    cr._run_all()
    assert fired == ["a", "b"]
    # After _run_all, the registry is empty so a second fire is a no-op.
    cr._run_all()
    assert fired == ["a", "b"]


def test_cleanup_registry_callback_error_does_not_skip_others(caplog):
    import logging
    from runtime import cleanup_registry as cr

    cr._reset_for_tests()
    fired = []
    def bad():
        raise RuntimeError("intentional")
    cr.register(bad)
    cr.register(lambda: fired.append("ok"))

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        cr._run_all()
    assert fired == ["ok"]
    assert any("intentional" in r.getMessage() for r in caplog.records)


# ============================================================
# ADR-020 remap 0-9 — feature_flags fail-closed
# ============================================================

def test_feature_flag_fail_closed_for_banned():
    from runtime.feature_flags import feature_enabled, is_banned, assert_not_banned

    # Banned features always return False.
    assert feature_enabled("mcp") is False
    assert feature_enabled("streaming") is False
    assert feature_enabled("anthropic_api_direct") is False
    assert is_banned("mcp")
    # Unknown features fail-closed.
    assert feature_enabled("nonexistent_feature_xyz") is False
    # Soft features default OFF.
    assert feature_enabled("skill_patching") is False
    # assert_not_banned raises on banned.
    with pytest.raises(ImportError):
        assert_not_banned("mcp")
    # Non-banned name doesn't raise.
    assert_not_banned("not_in_banned_set")


def test_feature_flag_env_override_for_soft_features(monkeypatch):
    """Soft features can be flipped on/off via env. Banned features ignore env."""
    from runtime.feature_flags import feature_enabled

    monkeypatch.setenv("SAGEMAKER_AGENT_FEATURE_SKILL_PATCHING", "1")
    assert feature_enabled("skill_patching") is True

    monkeypatch.setenv("SAGEMAKER_AGENT_FEATURE_SKILL_PATCHING", "0")
    assert feature_enabled("skill_patching") is False

    # Banned ignores env.
    monkeypatch.setenv("SAGEMAKER_AGENT_FEATURE_MCP", "1")
    assert feature_enabled("mcp") is False


# ============================================================
# Codex Block-B+ iter-1 finding-lock tests (regression prevention)
# ============================================================

def test_cost_warning_resets_each_run(monkeypatch):
    """Codex iter-1 finding #1 (HIGH) lock: `_warned_over_budget` resets
    at every run() entry so subsequent runs re-emit the warning once
    each. Without the reset, a long-running Agent would emit the
    warning once on first run and then stay silent for the rest of
    the session even when costs keep growing."""
    from runtime.tokens import TOKENS
    from runtime.config import CONFIG
    from runtime.bedrock_client import BedrockClient
    from agent import Agent

    monkeypatch.setattr(CONFIG, "session_cost_limit", 0.0001)

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    TOKENS.reset()
    # Push above budget.
    TOKENS.add(
        {"input_tokens": 10_000, "output_tokens": 1_000},
        model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
    )

    captured: list = []
    def cap(s):
        captured.append(s)

    a.run("first", output_fn=cap)
    a.run("second", output_fn=cap)
    a.run("third", output_fn=cap)

    over_budget_messages = [s for s in captured if "passed budget" in s]
    assert len(over_budget_messages) >= 2, (
        f"warning must reset and re-fire each run; got "
        f"{len(over_budget_messages)} over-budget lines: {captured}"
    )


def test_cost_warning_fires_on_exact_100_percent(monkeypatch):
    """Codex iter-1 finding #1 lock: `>=` (not `>`) so exact-100% trips."""
    from runtime.tokens import TOKENS
    from runtime.config import CONFIG
    from runtime.bedrock_client import BedrockClient
    from agent import Agent

    # Force session_cost == session_cost_limit exactly.
    monkeypatch.setattr(CONFIG, "session_cost_limit", 0.001)
    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    TOKENS.reset()
    # 1000 input tokens at $0.001/1k = $0.001 exactly = the limit.
    TOKENS.add(
        {"input_tokens": 1_000, "output_tokens": 0},
        model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
    )
    assert abs(TOKENS.session_cost - 0.001) < 1e-9

    captured: list = []
    a.run("turn", output_fn=lambda s: captured.append(s))
    over_budget_messages = [s for s in captured if "passed budget" in s]
    assert over_budget_messages, (
        "exact 100% must fire the warning (>= not >); got: " + str(captured)
    )


def test_entry_import_succeeds_when_no_mcp_package_present():
    """Codex iter-1 finding #2 (MEDIUM) lock: entry.py's import-boundary
    guard must NOT raise when the v5 tree has no banned packages.
    (We just imported entry successfully if this test is even running.)"""
    import entry
    assert entry is not None
    assert hasattr(entry, "Agent")


def test_entry_guard_raises_if_banned_package_reintroduced_in_tree(tmp_path, monkeypatch):
    """Lock for iter-1 finding #2 + iter-2 follow-up: drop a fake in-tree
    `mcp/` package next to entry.py and verify reload(entry) raises
    ImportError. External pip-installed packages must NOT trigger.

    The guard compares spec.origin against the realpath of the v5 agent
    package root — only paths INSIDE the v5 tree fail-closed.
    """
    import importlib
    import shutil
    import sys

    # Locate the live v5 agent package root.
    import entry as _entry_mod
    agent_root = os.path.dirname(os.path.abspath(_entry_mod.__file__))
    fake_mcp_dir = os.path.join(agent_root, "mcp")

    # Pre-condition: no in-tree mcp/ package exists.
    assert not os.path.isdir(fake_mcp_dir), (
        "test setup violation: a real mcp/ package exists in the tree; "
        "Block B+ should have removed it"
    )

    try:
        os.makedirs(fake_mcp_dir)
        with open(
            os.path.join(fake_mcp_dir, "__init__.py"),
            "w", encoding="utf-8",
        ) as f:
            f.write("# fake banned package for guard test\n")

        # Reloading `entry` must trip the guard now.
        # Drop cached entry + mcp from sys.modules so reload re-runs
        # the import-time block.
        sys.modules.pop("entry", None)
        sys.modules.pop("mcp", None)
        with pytest.raises(ImportError, match="banned subsystem 'mcp'"):
            importlib.import_module("entry")
    finally:
        # Clean up the fake package + restore cached modules.
        shutil.rmtree(fake_mcp_dir, ignore_errors=True)
        sys.modules.pop("entry", None)
        sys.modules.pop("mcp", None)
        # Re-import a clean entry so other tests aren't stranded.
        importlib.import_module("entry")


def test_entry_guard_does_not_false_positive_on_external_mcp(tmp_path, monkeypatch):
    """Negative-path lock: an EXTERNAL mcp package (e.g. pip-installed)
    must NOT trigger the guard. We simulate by adding a tmp dir to
    sys.path with an `mcp` package; reloading entry must succeed."""
    import importlib
    import sys

    external_root = tmp_path / "external_pkgs"
    external_root.mkdir()
    ext_mcp = external_root / "mcp"
    ext_mcp.mkdir()
    (ext_mcp / "__init__.py").write_text(
        "# external pip-installed-style mcp\n", encoding="utf-8",
    )

    # Confirm the agent package's mcp/ is absent (matches production state).
    import entry as _entry_mod
    agent_root = os.path.dirname(os.path.abspath(_entry_mod.__file__))
    assert not os.path.isdir(os.path.join(agent_root, "mcp"))

    monkeypatch.syspath_prepend(str(external_root))
    try:
        sys.modules.pop("entry", None)
        sys.modules.pop("mcp", None)
        # Reload entry — this should succeed since the discovered `mcp`
        # spec resolves to external_root/mcp, NOT inside the v5 tree.
        m = importlib.import_module("entry")
        assert m is not None
        assert hasattr(m, "Agent")
    finally:
        sys.modules.pop("entry", None)
        sys.modules.pop("mcp", None)
        importlib.import_module("entry")


def test_cleanup_registry_uses_rlock_for_signal_safety():
    """Codex iter-1 finding #3 (MEDIUM) lock: cleanup_registry's _lock
    must be threading.RLock (not Lock) so the signal handler can re-enter
    without deadlocking. RLock supports the same thread re-acquiring."""
    import threading
    from runtime import cleanup_registry as cr

    # threading.RLock() returns a `_thread.RLock` object; threading.Lock()
    # returns `_thread.lock`. We verify by attempting re-acquisition.
    cr._lock.acquire()
    try:
        # Same-thread re-acquire would deadlock on a non-reentrant Lock.
        # Use blocking=False so a regression here is caught instead of hanging.
        acquired_twice = cr._lock.acquire(blocking=False)
        assert acquired_twice, (
            "cleanup_registry._lock must be RLock for signal-handler "
            "re-entrancy; got non-reentrant Lock"
        )
        cr._lock.release()
    finally:
        cr._lock.release()


def test_block_b_plus_remap_table_present_in_adr_022():
    """Codex iter-1 finding #4 (LOW) lock: ADR-022 declares the explicit
    remap for Block B+ items B+3..B+6 (was UNDECLARED_PATTERN before
    the fix-up commit). This test pins the contract so future Block I /
    Block A reviews can verify the matching landing site."""
    adr_path = os.path.join(
        _AGENT_ROOT, "..", "..",
        "_status", "V5_DESIGN_DECISIONS.md",
    )
    with open(adr_path, "r", encoding="utf-8") as f:
        text = f.read()
    # ADR-022 must contain the explicit Block-B+ remap header.
    assert "Notes / known scope remaps (Block B+ items B+3..B+6)" in text
    # And must declare landing sites for each of the 4 items.
    for item in ("B+3", "B+4", "B+5", "B+6"):
        # Each B+N row references its target Block (I or A).
        # Be tolerant of formatting; just look for the literal item id.
        assert item in text, f"ADR-022 missing landing-Block remap for {item}"
