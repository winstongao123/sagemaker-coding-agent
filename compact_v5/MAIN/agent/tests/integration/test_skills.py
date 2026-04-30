"""Phase 10 integration tests: skill + skill_propose_patch tools.

Locks PORT_LOG #026 (tool_skill) + #027 (tool_skill_propose_patch).

Acceptance (V5_PLAN.md §Phase 10):
- All 10 skills load.
- Auto-trigger respects v4.9.6 default-OFF.
- skill_propose_patch returns no-op message when CONFIG.enable_skill_patching=False.
"""
from __future__ import annotations

import os
import sys

import pytest

_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


@pytest.fixture(autouse=True)
def fresh_registry_and_skills_singleton():
    """Reset the tool registry AND clear the skill tool singleton between
    tests so they get a fresh SkillManager bound to whatever workspace
    fixture the test uses."""
    from tools.registry import _reset_registry_for_tests
    from tools import bootstrap_built_ins
    from tools import skill as skill_mod
    skill_mod._SINGLETON = None
    _reset_registry_for_tests()
    bootstrap_built_ins()
    skill_mod._SINGLETON = None  # reset again post-bootstrap
    yield
    skill_mod._SINGLETON = None


# ============================================================
# Test 1 — skill list returns 10 production skills
# ============================================================

def test_skill_tool_list_returns_10_production_skills(monkeypatch):
    """Bind the singleton to v5's actual skills directory (where Phase 10
    copied the 10 skills). Sanity test: list returns at least 10 entries."""
    from runtime.config import CONFIG
    from tools import find_tool_by_name, all_registered

    # Point CONFIG.workspace at the agent root so the singleton finds skills/
    monkeypatch.setattr(CONFIG, "workspace", _AGENT_ROOT)

    skill_tool = find_tool_by_name(all_registered(), "skill")
    out = skill_tool.execute({"subcommand": "list"})
    # Each line is "- <name>: <description>". 10 v4 skills.
    lines = [ln for ln in out.splitlines() if ln.startswith("- ")]
    assert len(lines) >= 10, f"expected ≥10 skills, got {len(lines)} (output: {out[:300]})"


# ============================================================
# Test 2 — skill activate + deactivate
# ============================================================

def test_skill_tool_activate_then_deactivate(monkeypatch):
    from runtime.config import CONFIG
    from tools import find_tool_by_name, all_registered

    monkeypatch.setattr(CONFIG, "workspace", _AGENT_ROOT)
    skill_tool = find_tool_by_name(all_registered(), "skill")
    out = skill_tool.execute({"subcommand": "activate", "name": "verify"})
    assert "activated" in out.lower()
    out = skill_tool.execute({"subcommand": "deactivate"})
    assert "cleared" in out.lower()


# ============================================================
# Test 3 — skill read returns body of SKILL.md
# ============================================================

def test_skill_tool_read_returns_body(monkeypatch):
    from runtime.config import CONFIG
    from tools import find_tool_by_name, all_registered

    monkeypatch.setattr(CONFIG, "workspace", _AGENT_ROOT)
    skill_tool = find_tool_by_name(all_registered(), "skill")
    out = skill_tool.execute({"subcommand": "read", "name": "verify"})
    # body should contain something verify-related (substring match)
    assert "verif" in out.lower() or len(out) > 100


# ============================================================
# Test 4 — skill unknown subcommand returns error
# ============================================================

def test_skill_tool_unknown_subcommand_errors():
    from tools import find_tool_by_name, all_registered
    skill_tool = find_tool_by_name(all_registered(), "skill")
    out = skill_tool.execute({"subcommand": "blowup"})
    assert "Error" in out
    assert "list" in out  # available subcommands listed


# ============================================================
# Test 5 — skill_propose_patch is no-op when CONFIG.enable_skill_patching=False
# ============================================================

def test_skill_propose_patch_no_op_when_flag_off(monkeypatch):
    """v4.9.5 contract lock: tool MUST return a clear no-op message and NOT
    write a proposal when the flag is off (default)."""
    from runtime.config import CONFIG
    from tools import find_tool_by_name, all_registered

    monkeypatch.setattr(CONFIG, "enable_skill_patching", False)
    monkeypatch.setattr(CONFIG, "workspace", _AGENT_ROOT)
    spp = find_tool_by_name(all_registered(), "skill_propose_patch")
    out = spp.execute({
        "name": "verify",
        "reason": "improve clarity",
        "new_content": "# Verify\nReplacement body",
    })
    assert "OFF" in out or "not written" in out.lower() or "no proposal" in out.lower()


# ============================================================
# Test 6 — skill_propose_patch writes proposal when flag is ON
# ============================================================

def test_skill_propose_patch_writes_when_flag_on(monkeypatch, tmp_path):
    """When CONFIG.enable_skill_patching=True, the tool must write a
    proposal file under skills/<name>/.proposed/<ts>.md and NOT touch the
    live SKILL.md."""
    from runtime.config import CONFIG
    from tools import find_tool_by_name, all_registered, skill as skill_mod

    # Build a sandbox skills dir with one skill
    (tmp_path / "skills" / "demo").mkdir(parents=True)
    live = tmp_path / "skills" / "demo" / "SKILL.md"
    live.write_text(
        "---\nname: demo\ndescription: Use when demo.\n---\nlive body original",
        encoding="utf-8",
    )

    monkeypatch.setattr(CONFIG, "enable_skill_patching", True)
    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "skills_dir", "./skills")
    skill_mod._SINGLETON = None  # force rebuild against the new workspace

    spp = find_tool_by_name(all_registered(), "skill_propose_patch")
    out = spp.execute({
        "name": "demo",
        "reason": "test patch",
        "new_content": "patched body",
    })
    assert "Proposal written" in out
    # Live not modified
    assert "live body original" in live.read_text(encoding="utf-8")
    # Proposal file exists
    proposed_dir = tmp_path / "skills" / "demo" / ".proposed"
    assert proposed_dir.exists()
    proposals = list(proposed_dir.glob("*.md"))
    assert len(proposals) == 1


# ============================================================
# Test 7 — skill + skill_propose_patch are deferred (Phase 7 contract)
# ============================================================

# ============================================================
# Codex Phase-10 fix locks
# ============================================================

def test_singleton_reset_before_early_return(monkeypatch, tmp_path):
    """Codex Phase-10 finding (MEDIUM) lock: `_register()` must reset
    `_SINGLETON` BEFORE the already-registered early-return so re-bootstrap
    flows pick up a fresh CONFIG.workspace."""
    from runtime.config import CONFIG
    from tools import skill as skill_mod
    # Pre-populate a stale singleton bound to /old/workspace
    skill_mod._SINGLETON = "STALE_SENTINEL"
    # Re-register via bootstrap path (skill is already registered, so
    # `_register()` will short-circuit on the find_tool_by_name check).
    skill_mod._register()
    assert skill_mod._SINGLETON is None, (
        "singleton must be reset BEFORE the already-registered short-circuit"
    )


def test_skill_tool_respects_enable_skills_gate(monkeypatch):
    """Codex Phase-10 finding (MEDIUM) lock: skill tool returns a no-op
    message when CONFIG.enable_skills=False. v4 parity."""
    from runtime.config import CONFIG
    from tools import find_tool_by_name, all_registered

    monkeypatch.setattr(CONFIG, "enable_skills", False)
    skill_tool = find_tool_by_name(all_registered(), "skill")
    out = skill_tool.execute({"subcommand": "list"})
    assert "disabled" in out.lower()
    assert "no-ops" in out.lower() or "no-op" in out.lower()


def test_skill_propose_patch_respects_enable_skills_gate(monkeypatch):
    """skill_propose_patch also respects CONFIG.enable_skills (parity with v4)."""
    from runtime.config import CONFIG
    from tools import find_tool_by_name, all_registered

    monkeypatch.setattr(CONFIG, "enable_skills", False)
    monkeypatch.setattr(CONFIG, "enable_skill_patching", True)  # would normally proceed
    spp = find_tool_by_name(all_registered(), "skill_propose_patch")
    out = spp.execute({"name": "verify", "reason": "x", "new_content": "y"})
    assert "disabled" in out.lower()


# ============================================================
# Codex Phase-10 BLOCKER lock: SkillManager wired into QueryEngine.run()
# ============================================================

def test_query_engine_injects_active_skill_into_system_prompt(monkeypatch, tmp_path):
    """Codex Phase-10 BLOCKER lock: when a SkillManager is bound to the
    QueryEngine and a skill is active, the active skill body MUST be
    injected into the dynamic tail of the system prompt seen by Bedrock."""
    from core import QueryEngine, IterationBudget
    from runtime.config import CONFIG
    from skills.manager import SkillManager
    from tools import all_registered

    # Build a sandbox skills dir with one active skill.
    (tmp_path / "skills" / "active_one").mkdir(parents=True)
    (tmp_path / "skills" / "active_one" / "SKILL.md").write_text(
        "---\nname: active_one\ndescription: Use when active.\n---\n"
        "ACTIVE_SKILL_BODY_MARKER",
        encoding="utf-8",
    )
    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(tmp_path / "skills"))
    sm.discover()
    sm.activate("active_one")

    class _Capturing:
        def __init__(self):
            self.last_system = None
        def chat(self, messages, system, tools, max_tokens, temperature,
                 thinking_enabled, thinking_budget):
            from runtime.bedrock_client import Response
            self.last_system = system
            return Response(text="ok", tool_calls=[], stop_reason="end_turn")

    client = _Capturing()
    engine = QueryEngine(client=client, max_turns=2, budget=IterationBudget(),
                         skill_manager=sm)
    engine.run(user_message="hi", system_prompt="BASE_SYS", tools=all_registered())
    assert "BASE_SYS" in client.last_system
    assert "ACTIVE_SKILL_BODY_MARKER" in client.last_system, (
        "Active skill body must be injected into the system prompt"
    )


def test_query_engine_appends_relevant_skill_reminder_to_user_turn(monkeypatch, tmp_path):
    """Phase 10 wiring: when SkillManager.discover_relevant returns names,
    a 'Skills Relevant to This Task' reminder is appended to the user turn
    (so the model sees the suggestion). v4 sagemaker_agent.py:8702 parity."""
    from core import QueryEngine, IterationBudget
    from runtime.config import CONFIG
    from skills.manager import SkillManager
    from tools import all_registered

    (tmp_path / "skills" / "auto_one").mkdir(parents=True)
    (tmp_path / "skills" / "auto_one" / "SKILL.md").write_text(
        "---\n"
        "name: auto_one\n"
        "description: Use when triggered.\n"
        "triggers: trigger_word\n"
        "auto_trigger: true\n"
        "---\nbody",
        encoding="utf-8",
    )
    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    sm = SkillManager(
        workspace=str(tmp_path),
        skills_dir=str(tmp_path / "skills"),
        enable_auto_trigger=True,
    )
    sm.discover()

    class _Capturing:
        def __init__(self):
            self.last_messages = None
        def chat(self, messages, **_):
            from runtime.bedrock_client import Response
            self.last_messages = list(messages)
            return Response(text="ok", tool_calls=[], stop_reason="end_turn")

    client = _Capturing()
    engine = QueryEngine(client=client, max_turns=2, budget=IterationBudget(),
                         skill_manager=sm)
    engine.run(user_message="please run trigger_word now",
               system_prompt="sys", tools=all_registered())
    last_user = client.last_messages[-1]
    content = last_user["content"]
    text = content if isinstance(content, str) else "\n".join(
        b.get("text", "") for b in content if isinstance(b, dict)
    )
    assert "Skills Relevant to This Task" in text
    assert "auto_one" in text


def test_phase10_tools_are_deferred():
    from tools import find_tool_by_name, all_registered, apply_tool_search_deferral

    skill_tool = find_tool_by_name(all_registered(), "skill")
    assert skill_tool is not None
    assert skill_tool.should_defer is True

    spp = find_tool_by_name(all_registered(), "skill_propose_patch")
    assert spp is not None
    assert spp.should_defer is True

    # Both excluded from per-turn payload via Phase 7 deferral
    visible, deferred_names = apply_tool_search_deferral(all_registered(), enabled=True)
    visible_names = {t.name for t in visible}
    assert "skill" not in visible_names
    assert "skill_propose_patch" not in visible_names
    assert "skill" in deferred_names
    assert "skill_propose_patch" in deferred_names
