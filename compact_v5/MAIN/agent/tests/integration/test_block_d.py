"""Block D — Slash-command dispatcher (19 v4/B+ advertised + /auth + 6 LF = 26 canonical).

The dispatch table also carries one alias (`/skill suggestion` singular,
v4-parity) for a full count of 25. Tests assert these exact numbers.

Tests cover:
  - Dispatch table has exactly 26 canonical + 1 alias = 27 entries.
  - is_command() / dispatch_command() routing for each.
  - /auth gate behavior (env var match / mismatch).
  - Per-command handler returns CommandResult with consumed=True.
  - Chat-UI integration: ConsoleChatUI.send("/cost") routes to dispatcher.
  - Codex iter-1/iter-2 finding-lock tests (revert-all safety, alias
    routing, count accounting).
"""
from __future__ import annotations

import os
import sys

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# T1 — Dispatch table coverage
# ============================================================

def test_dispatch_table_canonical_count_is_exact_26():
    """19 v4/B+ advertised + /auth + 6 LF = exactly 26 canonical commands.

    Codex iter-2 finding #2 lock: assert EXACTLY this count (not a
    floor) so the documented headline matches `list_commands()`. The
    `/skill suggestion` (singular) alias is the 27th entry in the
    full listing — included for v4-parity per sagemaker_agent.py:10874.
    """
    from commands import list_commands

    canonical = list_commands(include_aliases=False)
    full = list_commands()

    expected_prefixes = {
        # v4 advertised (17):
        "/skills", "/skill use", "/skill clear", "/unskill",
        "/skill suggestions", "/skill apply", "/skill reject",
            "/save", "/resume", "/revert", "/cost", "/context", "/status",
        "/verify", "/checkpoint", "/phase", "/diffs",
        "/regression", "/done",
        # /auth gate (1):
        "/auth",
        # LF additions (6):
        "/simplify", "/init", "/init-verifiers",
        "/skillify", "/dream", "/promote-to-skill",
    }
    assert len(expected_prefixes) == 26, (
        f"expected_prefixes set should be exactly 26; got {len(expected_prefixes)}"
    )
    assert set(canonical) == expected_prefixes, (
        f"canonical mismatch:\n"
        f"  in canonical not expected: {set(canonical) - expected_prefixes}\n"
        f"  in expected not canonical: {expected_prefixes - set(canonical)}"
    )
    # The alias IS present in the full listing.
    assert "/skill suggestion" in full
    # Full listing is exactly 27 (canonical 26 + 1 alias).
    assert len(full) == 27
    assert len(canonical) == 26


def test_is_command_recognises_prefixes():
    from commands import is_command

    assert is_command("/cost")
    assert is_command("/skill use clara")
    assert is_command("/auth tok123")
    assert not is_command("hello")
    assert not is_command("/unknown")


def test_dispatch_unknown_command_returns_not_consumed():
    from commands import dispatch_command

    cr = dispatch_command("/never-heard-of-this")
    assert not cr.consumed
    assert "Unknown command" in cr.text


# ============================================================
# T1 — /auth gate
# ============================================================

def test_auth_command_passes_when_env_matches(monkeypatch):
    from runtime.config import CONFIG
    from commands import dispatch_command

    monkeypatch.setattr(CONFIG, "require_auth", True)
    monkeypatch.setattr(CONFIG, "auth_token_env", "TEST_AUTH_TOKEN")
    monkeypatch.setenv("TEST_AUTH_TOKEN", "secret123")

    cr = dispatch_command("/auth secret123")
    assert cr.consumed
    assert not cr.deny_auth
    assert "OK" in cr.text


def test_auth_command_denies_on_mismatch(monkeypatch):
    from runtime.config import CONFIG
    from commands import dispatch_command

    monkeypatch.setattr(CONFIG, "require_auth", True)
    monkeypatch.setattr(CONFIG, "auth_token_env", "TEST_AUTH_TOKEN")
    monkeypatch.setenv("TEST_AUTH_TOKEN", "secret123")

    cr = dispatch_command("/auth wrong")
    assert cr.consumed
    assert cr.deny_auth
    assert "fail" in cr.text.lower()


def test_auth_command_skipped_when_not_required(monkeypatch):
    from runtime.config import CONFIG
    from commands import dispatch_command

    monkeypatch.setattr(CONFIG, "require_auth", False)
    cr = dispatch_command("/auth anything")
    assert not cr.deny_auth
    assert "not required" in cr.text.lower()


# ============================================================
# T1 — /cost dispatches to TokenTracker
# ============================================================

def test_cost_command_includes_session_summary():
    from runtime.tokens import TOKENS
    from commands import dispatch_command

    TOKENS.reset()
    TOKENS.add(
        {"input_tokens": 1000, "output_tokens": 200},
        model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
    )
    cr = dispatch_command("/cost")
    assert cr.consumed
    assert "Session cost:" in cr.text
    assert "Tokens:" in cr.text
    assert "Parent:" in cr.text


# ============================================================
# T1 — /skills + /skill use + /skill clear
# ============================================================

def test_skills_command_lists_available(tmp_path, monkeypatch):
    from runtime.config import CONFIG
    from commands import dispatch_command, _get_skill_manager

    # Reset the singleton + point at a temp skills dir.
    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "skills_dir", str(tmp_path / "skills"))
    import commands as cmd_mod
    cmd_mod._SKILLS_SINGLETON = None  # force rebuild

    # Seed two skills.
    skills = tmp_path / "skills"
    skills.mkdir()
    for name in ("alpha", "beta"):
        d = skills / name
        d.mkdir()
        (d / "SKILL.md").write_text(
            f"---\nname: {name}\n"
            f"description: Use when {name} is needed.\n---\nbody",
            encoding="utf-8",
        )

    cr = dispatch_command("/skills")
    assert cr.consumed
    assert "alpha" in cr.text
    assert "beta" in cr.text


def test_skill_use_activates(tmp_path, monkeypatch):
    from runtime.config import CONFIG
    from commands import dispatch_command, _get_skill_manager

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "skills_dir", str(tmp_path / "skills"))
    import commands as cmd_mod
    cmd_mod._SKILLS_SINGLETON = None

    sk = tmp_path / "skills" / "demo"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text(
        "---\nname: demo\ndescription: Use when demo.\n---\nbody",
        encoding="utf-8",
    )

    cr = dispatch_command("/skill use demo")
    assert cr.consumed
    assert "demo" in cr.text.lower()
    sm = _get_skill_manager()
    assert sm.active_skill == "demo"

    cr2 = dispatch_command("/skill clear")
    assert sm.active_skill is None


# ============================================================
# T1 — /context, /phase, /status init
# ============================================================

def test_context_command_returns_estimate():
    from commands import dispatch_command

    cr = dispatch_command("/context")
    assert cr.consumed
    assert "Context window estimate" in cr.text


def test_phase_command_records_phase():
    from commands import dispatch_command

    cr = dispatch_command("/phase shipping v5.0.1")
    assert cr.consumed
    assert "shipping v5.0.1" in cr.text


def test_status_init_creates_file(tmp_path, monkeypatch):
    from runtime.config import CONFIG
    from commands import dispatch_command

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "status_doc", "AGENT_STATUS.md")

    cr = dispatch_command("/status init")
    assert cr.consumed
    assert (tmp_path / "AGENT_STATUS.md").exists()


# ============================================================
# T1 — /revert routing to SnapshotManager
# ============================================================

def test_revert_command_lists_when_no_args(tmp_path, monkeypatch):
    from runtime.config import CONFIG
    from runtime.snapshot import SnapshotManager
    import runtime.snapshot as snap_mod
    from commands import dispatch_command

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    test_sm = SnapshotManager(workspace=str(tmp_path))
    monkeypatch.setattr(snap_mod, "SNAPSHOTS", test_sm)

    cr = dispatch_command("/revert")
    assert cr.consumed
    assert "no snapshots" in cr.text.lower()

    # Now seed a snapshot and re-test.
    f = tmp_path / "x.txt"
    f.write_text("v1", encoding="utf-8")
    test_sm.save(str(f))
    cr2 = dispatch_command("/revert")
    assert "x.txt" in cr2.text


# ============================================================
# T1 — LF additions: /init, /skillify, /dream, /promote-to-skill
# ============================================================

def test_init_command_creates_workspace_files(tmp_path, monkeypatch):
    from runtime.config import CONFIG
    from commands import dispatch_command

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "status_doc", "AGENT_STATUS.md")

    cr = dispatch_command("/init")
    assert cr.consumed
    assert (tmp_path / "AGENT_STATUS.md").exists()
    assert (tmp_path / "skills").is_dir()


def test_skillify_command_requires_name():
    from commands import dispatch_command

    cr = dispatch_command("/skillify")
    assert cr.consumed
    assert "Usage" in cr.text


def test_dream_command_returns_explanation():
    from commands import dispatch_command

    cr = dispatch_command("/dream")
    assert cr.consumed
    assert "memory" in cr.text.lower()


def test_promote_to_skill_requires_name():
    from commands import dispatch_command

    cr = dispatch_command("/promote-to-skill")
    assert cr.consumed
    assert "Usage" in cr.text


# ============================================================
# T2 — ConsoleChatUI.send routes commands without invoking agent
# ============================================================

def test_console_chat_ui_routes_command(monkeypatch):
    """ConsoleChatUI.send('/cost') must hit the dispatcher and NOT
    invoke agent.run()."""
    from runtime.bedrock_client import BedrockClient
    from agent import Agent
    from ui.chat_ui import ConsoleChatUI

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    ui = ConsoleChatUI(a)

    invoked = {"agent_run": False}
    real_run = a.run

    def spy_run(*args, **kwargs):
        invoked["agent_run"] = True
        return real_run(*args, **kwargs)

    monkeypatch.setattr(a, "run", spy_run)
    out = ui.send("/cost")
    assert "Session cost:" in out
    assert not invoked["agent_run"], "/cost must NOT invoke agent.run()"


def test_console_chat_ui_falls_through_for_non_command():
    """Non-command messages still go to agent.run()."""
    from runtime.bedrock_client import BedrockClient
    from agent import Agent
    from ui.chat_ui import ConsoleChatUI

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client)
    ui = ConsoleChatUI(a)
    out = ui.send("hello agent")
    assert isinstance(out, str)
    assert out  # mock returns a non-empty reply


# ============================================================
# Codex Block-D iter-1 finding-lock tests (regression prevention)
# ============================================================

def test_revert_all_without_yes_does_not_revert(tmp_path, monkeypatch):
    """Codex iter-1 finding #1 (HIGH safety) lock: bare `/revert all`
    is a preview, NOT a bulk revert. Only `/revert all --yes` actually
    reverts. Without this guard, a destructive operation runs without
    explicit confirmation."""
    from runtime.config import CONFIG
    from runtime.snapshot import SnapshotManager
    import runtime.snapshot as snap_mod
    from commands import dispatch_command

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    test_sm = SnapshotManager(workspace=str(tmp_path))
    monkeypatch.setattr(snap_mod, "SNAPSHOTS", test_sm)

    # Seed a real file + snapshot, then mutate.
    f = tmp_path / "data.txt"
    f.write_text("v1", encoding="utf-8")
    test_sm.save(str(f))
    f.write_text("v2", encoding="utf-8")
    assert f.read_text(encoding="utf-8") == "v2"

    # Bare `/revert all` should PREVIEW, not revert.
    cr_preview = dispatch_command("/revert all")
    assert cr_preview.consumed
    assert "destructive" in cr_preview.text.lower()
    assert "--yes" in cr_preview.text
    # File remains mutated.
    assert f.read_text(encoding="utf-8") == "v2", (
        "/revert all without --yes must NOT revert files"
    )

    # `/revert all --yes` actually reverts.
    cr_revert = dispatch_command("/revert all --yes")
    assert cr_revert.consumed
    assert cr_revert.side_effect == "revert_all"
    assert f.read_text(encoding="utf-8") == "v1", "after --yes, files reverted"


def test_skill_suggestion_alias_routes_correctly():
    """Codex iter-1 finding #2 lock: the `/skill suggestion` (singular)
    alias is documented v4 parity and routes to the same handler as
    `/skill suggestions`. Verifies the alias is intentional, not stale."""
    from commands import dispatch_command

    cr_singular = dispatch_command("/skill suggestion")
    cr_plural = dispatch_command("/skill suggestions")
    # Both should consume + return identical-shape responses.
    assert cr_singular.consumed and cr_plural.consumed
    # Same routing target ⇒ same text contract (modulo tense).
    # The body text comes from the same handler, so they match exactly.
    assert cr_singular.text == cr_plural.text


def test_list_commands_canonical_count_excludes_alias():
    """list_commands(include_aliases=False) returns 27 canonical
    prefixes (alias collapsed); default returns 28 (alias included)."""
    from commands import list_commands

    canonical = list_commands(include_aliases=False)
    full = list_commands()  # default: include_aliases=True
    assert "/skill suggestion" not in canonical
    assert "/skill suggestion" in full
    # Full listing has exactly one more entry than canonical.
    assert len(full) == len(canonical) + 1
