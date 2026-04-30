"""Phase 10 unit tests: skills/manager.py — SkillManager.

Locks PORT_LOG #025 (SkillManager) + #028 (Hermes filter, PS Issue #1) +
#029 (10 skills byte-for-byte from v4).
"""
from __future__ import annotations

import os
import sys

import pytest

_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# Phase 10 acceptance: 10 v4 production skills load
# ============================================================

PRODUCTION_SKILLS = {
    "batch", "clara", "design", "html", "reflexion",
    "report", "review", "security-review", "simplify", "verify",
}


def test_all_10_v4_production_skills_load():
    """Phase 10 acceptance criterion (V5_PLAN.md §Phase 10): all 10 skills load.

    Uses the actual `compact_v5/MAIN/agent/skills/` directory as the canonical
    source (where Phase 10 copied them byte-for-byte from v4)."""
    from skills.manager import SkillManager

    skills_root = os.path.join(_AGENT_ROOT, "skills")
    sm = SkillManager(workspace=_AGENT_ROOT, skills_dir=skills_root)
    cache = sm.discover()
    discovered_names = set(cache.keys())
    # Some v4 skills' frontmatter `name:` differs from the directory name:
    #   skills/clara/SKILL.md     → name: clara-review
    #   skills/review/SKILL.md    → name: code-review
    # Accept the canonical alias map so this lock test doesn't require
    # renaming v4 content (which would void the byte-for-byte port).
    alias_map = {
        "clara-review": "clara",
        "code-review": "review",
    }
    discovered_aliases = set(discovered_names)
    for n in list(discovered_names):
        if n in alias_map:
            discovered_aliases.add(alias_map[n])
    missing = PRODUCTION_SKILLS - discovered_aliases
    assert not missing, f"missing v4 production skills: {missing}"


def test_skill_frontmatter_parsed():
    """Every loaded skill must have a non-empty description and a location path."""
    from skills.manager import SkillManager
    skills_root = os.path.join(_AGENT_ROOT, "skills")
    sm = SkillManager(workspace=_AGENT_ROOT, skills_dir=skills_root)
    sm.discover()
    for name, info in sm._cache.items():
        assert info.description, f"skill '{name}' has empty description"
        assert os.path.exists(info.location), f"skill '{name}' location missing"


# ============================================================
# discover_relevant — auto-trigger + Hermes filter (PS Issue #1)
# ============================================================

def test_auto_trigger_default_off_returns_empty():
    """v4.9.6 default-OFF lock: enable_auto_trigger=False → empty list even
    if a trigger word matches."""
    from skills.manager import SkillManager
    skills_root = os.path.join(_AGENT_ROOT, "skills")
    sm = SkillManager(
        workspace=_AGENT_ROOT, skills_dir=skills_root,
        enable_auto_trigger=False,
    )
    sm.discover()
    relevant = sm.discover_relevant("/verify the build", active_tools=None)
    assert relevant == []


def test_auto_trigger_off_per_skill_default_off(tmp_path):
    """Even with global enable_auto_trigger=True, a skill with auto_trigger=false
    in its frontmatter must NOT auto-load. v4.9.6 contract."""
    from skills.manager import SkillManager
    sd = tmp_path / "skills"
    (sd / "alpha").mkdir(parents=True)
    (sd / "alpha" / "SKILL.md").write_text(
        "---\n"
        "name: alpha\n"
        "description: Use when user mentions alpha.\n"
        "triggers: alpha, /alpha\n"
        "auto_trigger: false\n"
        "---\nbody",
        encoding="utf-8",
    )
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd), enable_auto_trigger=True)
    sm.discover()
    assert sm.discover_relevant("please run alpha now", active_tools=None) == []


def test_auto_trigger_opt_in_works(tmp_path):
    """When BOTH global enable_auto_trigger=True AND per-skill auto_trigger=true,
    triggers work."""
    from skills.manager import SkillManager
    sd = tmp_path / "skills"
    (sd / "beta").mkdir(parents=True)
    (sd / "beta" / "SKILL.md").write_text(
        "---\n"
        "name: beta\n"
        "description: Use when user mentions beta.\n"
        "triggers: beta\n"
        "auto_trigger: true\n"
        "---\nbody",
        encoding="utf-8",
    )
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd), enable_auto_trigger=True)
    sm.discover()
    assert sm.discover_relevant("please run beta now", active_tools=None) == ["beta"]


# ============================================================
# Hermes filter — PS Issue #1 lock
# ============================================================

def test_hermes_filter_skill_filtered_when_required_tool_missing(tmp_path):
    """If a skill declares `requires_tools: bash, python_exec` and one of
    them is not in active_tools, the skill is filtered out of discover_relevant.
    """
    from skills.manager import SkillManager
    sd = tmp_path / "skills"
    (sd / "verify-x").mkdir(parents=True)
    (sd / "verify-x" / "SKILL.md").write_text(
        "---\n"
        "name: verify-x\n"
        "description: Use when verifying.\n"
        "triggers: verify\n"
        "auto_trigger: true\n"
        "requires_tools: bash, python_exec\n"
        "---\nbody",
        encoding="utf-8",
    )
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd), enable_auto_trigger=True)
    sm.discover()
    # active_tools missing python_exec → must be filtered
    assert sm.discover_relevant("please verify", active_tools={"bash"}) == []


def test_hermes_filter_skill_passes_when_all_required_tools_present(tmp_path):
    from skills.manager import SkillManager
    sd = tmp_path / "skills"
    (sd / "verify-y").mkdir(parents=True)
    (sd / "verify-y" / "SKILL.md").write_text(
        "---\n"
        "name: verify-y\n"
        "description: Use when verifying.\n"
        "triggers: verify\n"
        "auto_trigger: true\n"
        "requires_tools: bash, python_exec\n"
        "---\nbody",
        encoding="utf-8",
    )
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd), enable_auto_trigger=True)
    sm.discover()
    # active_tools has both → must pass
    assert sm.discover_relevant("please verify", active_tools={"bash", "python_exec", "read_file"}) == ["verify-y"]


def test_hermes_filter_skipped_when_active_tools_none(tmp_path):
    """Backwards compat: when active_tools=None (no filter), skills with
    requires_tools STILL pass through. The filter is opt-in by passing
    active_tools."""
    from skills.manager import SkillManager
    sd = tmp_path / "skills"
    (sd / "z").mkdir(parents=True)
    (sd / "z" / "SKILL.md").write_text(
        "---\n"
        "name: z\n"
        "description: Use when z.\n"
        "triggers: z\n"
        "auto_trigger: true\n"
        "requires_tools: nonexistent_tool\n"
        "---\nbody",
        encoding="utf-8",
    )
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd), enable_auto_trigger=True)
    sm.discover()
    assert sm.discover_relevant("z", active_tools=None) == ["z"]


def test_hermes_filter_skill_without_requires_tools_never_filtered(tmp_path):
    """Backwards compat: skills without `requires_tools` (the 10 v4 skills)
    must NEVER be filtered by this mechanism."""
    from skills.manager import SkillManager
    sd = tmp_path / "skills"
    (sd / "w").mkdir(parents=True)
    (sd / "w" / "SKILL.md").write_text(
        "---\n"
        "name: w\n"
        "description: Use when w.\n"
        "triggers: w\n"
        "auto_trigger: true\n"
        "---\nbody",
        encoding="utf-8",
    )
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd), enable_auto_trigger=True)
    sm.discover()
    assert sm.discover_relevant("w", active_tools=set()) == ["w"]


# ============================================================
# read_skill / activate / deactivate
# ============================================================

def test_read_skill_returns_body():
    from skills.manager import SkillManager
    skills_root = os.path.join(_AGENT_ROOT, "skills")
    sm = SkillManager(workspace=_AGENT_ROOT, skills_dir=skills_root)
    sm.discover()
    # Pick any production skill (verify is a safe choice — v4 ships it).
    ok, content = sm.read_skill("verify", max_chars=5000)
    assert ok
    assert "verify" in content.lower() or "Verification" in content


def test_read_skill_unknown_returns_error_with_available():
    from skills.manager import SkillManager
    skills_root = os.path.join(_AGENT_ROOT, "skills")
    sm = SkillManager(workspace=_AGENT_ROOT, skills_dir=skills_root)
    sm.discover()
    ok, msg = sm.read_skill("totally_made_up")
    assert not ok
    assert "not found" in msg.lower()


def test_activate_and_deactivate_round_trip():
    from skills.manager import SkillManager
    skills_root = os.path.join(_AGENT_ROOT, "skills")
    sm = SkillManager(workspace=_AGENT_ROOT, skills_dir=skills_root)
    sm.discover()
    ok, msg = sm.activate("verify")
    assert ok
    assert sm.active_skill == "verify"
    sm.deactivate()
    assert sm.active_skill is None


def test_activate_unknown_returns_error():
    from skills.manager import SkillManager
    skills_root = os.path.join(_AGENT_ROOT, "skills")
    sm = SkillManager(workspace=_AGENT_ROOT, skills_dir=skills_root)
    sm.discover()
    ok, msg = sm.activate("nope_not_real")
    assert not ok
    assert "not found" in msg.lower()


# ============================================================
# Self-patching surface (v4.9.5 verbatim)
# ============================================================

def test_propose_patch_writes_to_proposed_dir(tmp_path):
    from skills.manager import SkillManager
    sd = tmp_path / "skills"
    (sd / "k").mkdir(parents=True)
    (sd / "k" / "SKILL.md").write_text(
        "---\nname: k\ndescription: Use when k.\n---\noriginal body", encoding="utf-8")
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd))
    sm.discover()
    ok, payload = sm.propose_patch("k", "improves clarity", "new full body")
    assert ok
    assert ".proposed" in payload
    assert os.path.exists(payload)
    # live SKILL.md unchanged
    live = (sd / "k" / "SKILL.md").read_text(encoding="utf-8")
    assert "original body" in live


def test_propose_patch_requires_reason_and_content(tmp_path):
    from skills.manager import SkillManager
    sd = tmp_path / "skills"
    (sd / "k2").mkdir(parents=True)
    (sd / "k2" / "SKILL.md").write_text(
        "---\nname: k2\ndescription: Use when.\n---\nbody", encoding="utf-8")
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd))
    sm.discover()
    ok, _ = sm.propose_patch("k2", "", "body")
    assert not ok
    ok, _ = sm.propose_patch("k2", "reason", "")
    assert not ok


def test_apply_proposal_overwrites_live_and_deletes_proposal(tmp_path):
    from skills.manager import SkillManager
    sd = tmp_path / "skills"
    (sd / "m").mkdir(parents=True)
    live = sd / "m" / "SKILL.md"
    live.write_text("---\nname: m\ndescription: Use when.\n---\noriginal body",
                    encoding="utf-8")
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd))
    sm.discover()
    ok, prop_path = sm.propose_patch("m", "improvement", "patched body")
    assert ok
    ok, msg = sm.apply_proposal("m")
    assert ok
    # live now contains patched body, proposal file deleted
    assert "patched body" in live.read_text(encoding="utf-8")
    assert not os.path.exists(prop_path)


# ============================================================
# list_for_prompt budget cap
# ============================================================

# ============================================================
# Codex Phase-10 fix lock: YAML list parsing for requires_tools
# ============================================================

def test_yaml_list_form_for_requires_tools(tmp_path):
    """Codex Phase-10 finding (HIGH) lock: `requires_tools` MUST accept YAML
    list dash-form, not just CSV scalar. Without this fix, a YAML-list
    requires_tools silently became None and the Hermes filter was bypassed.
    """
    from skills.manager import SkillManager
    sd = tmp_path / "skills"
    (sd / "yaml_list").mkdir(parents=True)
    (sd / "yaml_list" / "SKILL.md").write_text(
        "---\n"
        "name: yaml_list\n"
        "description: Use when YAML list form.\n"
        "triggers: yaml\n"
        "auto_trigger: true\n"
        "requires_tools:\n"
        "  - bash\n"
        "  - python_exec\n"
        "---\nbody",
        encoding="utf-8",
    )
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd), enable_auto_trigger=True)
    sm.discover()
    info = sm._cache["yaml_list"]
    assert info.requires_tools == ["bash", "python_exec"], (
        f"YAML list parse failed: got {info.requires_tools}"
    )
    # And the Hermes filter actually fires:
    assert sm.discover_relevant("yaml work", active_tools={"bash"}) == []
    assert sm.discover_relevant(
        "yaml work", active_tools={"bash", "python_exec"}
    ) == ["yaml_list"]


def test_yaml_list_form_for_triggers(tmp_path):
    """Triggers also accept YAML list dash-form (same parser path)."""
    from skills.manager import SkillManager
    sd = tmp_path / "skills"
    (sd / "tlist").mkdir(parents=True)
    (sd / "tlist" / "SKILL.md").write_text(
        "---\n"
        "name: tlist\n"
        "description: Use when one of triggers.\n"
        "triggers:\n"
        "  - alpha\n"
        "  - beta\n"
        "auto_trigger: true\n"
        "---\nbody",
        encoding="utf-8",
    )
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd), enable_auto_trigger=True)
    sm.discover()
    assert sm.discover_relevant("alpha work", active_tools=None) == ["tlist"]
    assert sm.discover_relevant("beta work", active_tools=None) == ["tlist"]


# ============================================================
# Codex Phase-10 fix lock: proposal filename uniqueness
# ============================================================

def test_proposal_filename_has_uuid_suffix(tmp_path):
    """Codex Phase-10 finding (HIGH) lock: two proposals in the same second
    must produce DIFFERENT filenames. The fix adds a 6-char uuid hex suffix."""
    from skills.manager import SkillManager
    sd = tmp_path / "skills"
    (sd / "p").mkdir(parents=True)
    (sd / "p" / "SKILL.md").write_text(
        "---\nname: p\ndescription: Use when p.\n---\noriginal",
        encoding="utf-8",
    )
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd))
    sm.discover()
    ok1, path1 = sm.propose_patch("p", "first reason", "first body")
    ok2, path2 = sm.propose_patch("p", "second reason", "second body")
    assert ok1 and ok2
    assert path1 != path2, "two same-second proposals collided on filename"


# ============================================================
# Codex Phase-10 fix lock: snapshot-on-apply (best-effort backup)
# ============================================================

def test_apply_proposal_creates_backup(tmp_path):
    """Codex Phase-10 finding (HIGH) lock: when SnapshotManager isn't wired
    (Phase 10 default), apply still produces a local `.skill_backup_<ts>`
    sibling so the change is reversible — completing safety rail (4)."""
    from skills.manager import SkillManager
    sd = tmp_path / "skills"
    (sd / "q").mkdir(parents=True)
    live = sd / "q" / "SKILL.md"
    live.write_text(
        "---\nname: q\ndescription: Use when q.\n---\noriginal body",
        encoding="utf-8",
    )
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd))
    sm.discover()
    sm.propose_patch("q", "improvement", "patched body")
    ok, msg = sm.apply_proposal("q")
    assert ok, msg
    # A `.skill_backup_<ts>` sibling exists alongside live SKILL.md
    siblings = list((sd / "q").glob("SKILL.md.skill_backup_*"))
    assert len(siblings) >= 1, "no skill backup created on apply"


def test_list_for_prompt_respects_budget(tmp_path):
    from skills.manager import SkillManager
    sd = tmp_path / "skills"
    for i in range(50):
        (sd / f"skill_{i}").mkdir(parents=True)
        (sd / f"skill_{i}" / "SKILL.md").write_text(
            f"---\nname: skill_{i}\ndescription: S{i}\n---\nbody", encoding="utf-8")
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(sd))
    sm.discover()
    out = sm.list_for_prompt(budget_tokens=50)  # very tight budget
    assert "more" in out or out == ""
