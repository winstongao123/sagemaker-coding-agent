"""Block I — Skill name resolution + Hermes fuzzy + paths frontmatter +
disable_model_invocation + enabled_when + realpath dedup + scaffolders.

Source: Runnable skills/loadSkillsDir.ts:159-178 (paths) + :84
(disable_model_invocation) + :71 (enabled_when) + :638-810 (realpath
dedup) + :344-396 (CLAUDE_SKILL_DIR/CLAUDE_SESSION_ID substitution);
Hermes run_agent.py:4685-4724 (fuzzy match).

Tests per TEST_DESIGN §Block I (8 T1+T2 tests, $0):
- test_skill_resolve_by_directory_name
- test_skill_resolve_by_metadata_name
- test_skill_fuzzy_match_typo
- test_skill_paths_frontmatter_auto_activate
- test_skill_disable_model_invocation
- test_skill_enabled_when_config_flag
- test_skillify_4_round_interview
- test_skill_manager_realpath_dedup
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def fresh_skills_dir(tmp_path):
    """Create an isolated skills/ directory under a temp workspace."""
    workspace = tmp_path
    skills_dir = workspace / "skills"
    skills_dir.mkdir()
    yield workspace, skills_dir


def _write_skill(parent: Path, dir_name: str, frontmatter: dict, body: str = "skill body"):
    """Helper to write a SKILL.md with the given frontmatter dict."""
    skill_dir = parent / dir_name
    skill_dir.mkdir(exist_ok=True)
    fm = "---\n"
    for k, v in frontmatter.items():
        if isinstance(v, list):
            fm += f"{k}:\n"
            for item in v:
                fm += f"  - {item}\n"
        else:
            fm += f"{k}: {v}\n"
    fm += "---\n"
    (skill_dir / "SKILL.md").write_text(fm + body, encoding="utf-8")
    return skill_dir


# ============================================================
# TEST_DESIGN row 1 — directory-name resolution
# ============================================================

def test_skill_resolve_by_directory_name(fresh_skills_dir):
    """`/skill use clara-review` → loads `skills/clara-review/SKILL.md`
    (resolves by directory name when metadata name is identical)."""
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "clara-review", {
        "name": "clara-review",
        "description": "Use when reviewing Clara-style code.",
    })
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()
    resolved = sm.resolve_name("clara-review")
    assert resolved == "clara-review"


# ============================================================
# TEST_DESIGN row 2 — metadata `name:` resolution
# ============================================================

def test_skill_resolve_by_metadata_name(fresh_skills_dir):
    """`/skill use Clara` (metadata `name: Clara`) → loads
    `skills/clara-review/SKILL.md` (case-insensitive match)."""
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "clara-review", {
        "name": "Clara",
        "description": "Use when reviewing Clara-style code.",
    })
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()
    # Exact match.
    assert sm.resolve_name("Clara") == "Clara"
    # Case-insensitive metadata match.
    assert sm.resolve_name("clara") == "Clara"
    # Directory-name match also resolves to canonical metadata name.
    assert sm.resolve_name("clara-review") == "Clara"


# ============================================================
# TEST_DESIGN row 3 — Hermes fuzzy match (typo)
# ============================================================

def test_skill_fuzzy_match_typo(fresh_skills_dir):
    """`/skill use verfy` → fuzzy resolves to `verify` (Hermes :4689-4720
    cutoff=0.7)."""
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "verify", {
        "name": "verify",
        "description": "Use when running gate checks.",
    })
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()
    assert sm.resolve_name("verfy") == "verify"  # one-letter typo
    assert sm.resolve_name("verifu") == "verify"  # one-letter substitution
    assert sm.resolve_name("verify_skill") == "verify"  # suffix-strip


def test_skill_fuzzy_returns_none_for_unrelated(fresh_skills_dir):
    """Fuzzy match must NOT resolve unrelated queries below cutoff=0.7."""
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "verify", {"name": "verify", "description": "x"})
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()
    assert sm.resolve_name("xyzpdq") is None
    assert sm.resolve_name("zzzzz") is None


# ============================================================
# TEST_DESIGN row 4 — paths frontmatter auto-activation (I-1 / I-5)
# ============================================================

def test_skill_paths_frontmatter_auto_activate(fresh_skills_dir):
    """Skill with `paths: ["*.py"]` auto-activates when user edits .py file."""
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "py-skill", {
        "name": "py-skill",
        "description": "Use when editing Python files.",
        "paths": ["*.py"],
    })
    _write_skill(skills_dir, "md-skill", {
        "name": "md-skill",
        "description": "Use when editing Markdown.",
        "paths": ["*.md"],
    })
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()
    assert sm.active_skill is None

    # Editing a .py file activates py-skill, not md-skill.
    activated = sm.activate_for_path("foo.py")
    assert activated == ["py-skill"]
    assert sm.active_skill == "py-skill"

    # Already-active skill is not re-activated.
    sm.active_skill = "py-skill"
    activated_again = sm.activate_for_path("bar.py")
    assert activated_again == []  # already active, no-op


def test_skill_paths_strips_double_star_suffix(fresh_skills_dir):
    """Runnable's parser strips `/**` suffix; v5 must too (loadSkillsDir.ts:168)."""
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "src-skill", {
        "name": "src-skill",
        "description": "Use under src/.",
        "paths": ["src/**"],   # → normalized to "src" (matches src/* via fnmatch)
    })
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()
    assert sm._cache["src-skill"].paths == ["src"]


def test_skill_paths_all_match_all_collapses_to_none(fresh_skills_dir):
    """All-`**` patterns collapse to None (skill is unconditional)."""
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "any-skill", {
        "name": "any-skill",
        "description": "Use anywhere.",
        "paths": ["**"],
    })
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()
    assert sm._cache["any-skill"].paths is None


# ============================================================
# TEST_DESIGN row 5 — disable_model_invocation (I-2 / R9 #3)
# ============================================================

def test_skill_disable_model_invocation(fresh_skills_dir):
    """Skill with `disable_model_invocation: true` not visible to model
    but callable by user."""
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "user-only", {
        "name": "user-only",
        "description": "Use when user explicitly runs it.",
        "disable_model_invocation": "true",
    })
    _write_skill(skills_dir, "open", {
        "name": "open",
        "description": "Use whenever relevant.",
    })
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()

    # Model-invocable list excludes user-only skills.
    model_list = [s["name"] for s in sm.list_model_invocable()]
    assert "open" in model_list
    assert "user-only" not in model_list

    # User-invocable list includes both.
    user_list = [s["name"] for s in sm.list_user_invocable()]
    assert "user-only" in user_list
    assert "open" in user_list

    # /skill use can still resolve user-only.
    assert sm.resolve_name("user-only") == "user-only"


# ============================================================
# TEST_DESIGN row 6 — enabled_when CONFIG flag (I-3 / R9 #4)
# ============================================================

def test_skill_enabled_when_config_flag(fresh_skills_dir):
    """Skill with `enabled_when: <flag>` only loads when CONFIG.<flag> True."""
    from skills.manager import SkillManager
    from runtime.config import CONFIG

    workspace, skills_dir = fresh_skills_dir
    # Set up a config attribute we control. Use enable_skill_patching
    # which exists in the dataclass and defaults to False.
    _write_skill(skills_dir, "advanced", {
        "name": "advanced",
        "description": "Use when in advanced mode.",
        "enabled_when": "enable_skill_patching",
    })
    _write_skill(skills_dir, "always", {
        "name": "always",
        "description": "Use anytime.",
    })

    _prev = CONFIG.enable_skill_patching
    try:
        # Flag OFF (default) → advanced skill is hidden.
        CONFIG.enable_skill_patching = False
        sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
        sm.discover()
        assert "advanced" not in sm._cache
        assert "always" in sm._cache

        # Flag ON → advanced skill appears.
        CONFIG.enable_skill_patching = True
        sm.discover()
        assert "advanced" in sm._cache
        assert "always" in sm._cache
    finally:
        CONFIG.enable_skill_patching = _prev


# ============================================================
# TEST_DESIGN row 7 — skillify scaffolder (I-9, already in Block D)
# ============================================================

def test_skillify_4_round_interview():
    """`/skillify <name>` returns a CommandResult with side_effect="skillify:<name>".

    The 4-round interview is conducted by the LLM at runtime; this test
    locks the dispatch + side-effect contract. The Skillify SKILL.md (or
    the prompt the model picks up after side-effect) drives the actual
    interview rounds (Identify scope → Decide name → Draft body → Confirm).
    """
    from commands import dispatch_command

    result = dispatch_command("/skillify my-new-skill")
    assert result is not None
    assert result.consumed is True
    assert "skills/my-new-skill" in result.text
    assert result.side_effect == "skillify:my-new-skill"

    # Empty arg → usage hint, no side effect.
    result_empty = dispatch_command("/skillify")
    assert result_empty.consumed is True
    assert "Usage" in result_empty.text


# ============================================================
# TEST_DESIGN row 8 — realpath dedup (I-4 / R9 #23)
# ============================================================

def test_skill_manager_realpath_dedup(fresh_skills_dir):
    """Symlink to same dir loaded once (R9 #23 bug fix).

    Setup: skill at skills/foo/SKILL.md plus a symlink
    skills/foo-link → skills/foo. Both rglob hits, but realpath dedup
    must skip the second.
    """
    import os as _os
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    real_dir = _write_skill(skills_dir, "foo", {
        "name": "foo",
        "description": "Use as foo.",
    })
    link_path = skills_dir / "foo-link"
    try:
        _os.symlink(str(real_dir), str(link_path), target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported in this environment")

    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()
    # Only ONE entry in cache despite two paths reaching the same SKILL.md.
    assert len(sm._cache) == 1
    assert "foo" in sm._cache


# ============================================================
# Behavioral lock tests — substitution + commands wiring + visibility
# ============================================================

def test_skill_var_substitution_skill_dir(fresh_skills_dir):
    """${CLAUDE_SKILL_DIR} resolves to the skill's base_dir (forward-slash)."""
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "vartest", {
        "name": "vartest",
        "description": "Use to test variable substitution.",
    }, body="Skill dir is ${CLAUDE_SKILL_DIR} and session is ${CLAUDE_SESSION_ID}")
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()

    out = sm.substitute_skill_vars(
        content="Skill dir: ${CLAUDE_SKILL_DIR} | Session: ${CLAUDE_SESSION_ID}",
        skill_name="vartest",
        session_id="abc123",
    )
    assert "${CLAUDE_SKILL_DIR}" not in out
    assert "${CLAUDE_SESSION_ID}" not in out
    assert "abc123" in out
    # base_dir must be forward-slashed even on Windows.
    assert "vartest" in out.replace("\\", "/")


def test_skill_var_substitution_unknown_skill_no_op(fresh_skills_dir):
    """Substitution on an unknown skill name leaves ${CLAUDE_SKILL_DIR}
    in place (no crash, returns content unchanged for that var)."""
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()  # empty
    out = sm.substitute_skill_vars(
        content="Foo ${CLAUDE_SKILL_DIR} bar",
        skill_name="nonexistent",
        session_id="",
    )
    assert "${CLAUDE_SKILL_DIR}" in out  # unchanged
    assert out == "Foo ${CLAUDE_SKILL_DIR} bar"


def test_skill_use_command_uses_fuzzy_resolution(fresh_skills_dir, monkeypatch):
    """Block D's /skill use command must route through resolve_name() so
    `/skill use verfy` resolves to `verify` (Block I integration with D)."""
    from skills.manager import SkillManager
    import commands as _cmd_mod

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "verify", {"name": "verify", "description": "x"})
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))

    # Replace the lazy global getter with our isolated SkillManager.
    monkeypatch.setattr(_cmd_mod, "_get_skill_manager", lambda: sm)

    result = _cmd_mod.dispatch_command("/skill use verfy")
    assert result is not None
    assert "verify" in result.text
    assert sm.active_skill == "verify"


def test_skill_paths_with_directory_pattern(fresh_skills_dir):
    """`paths: ["src/*"]` matches files under src/ via fnmatch."""
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "src-files", {
        "name": "src-files",
        "description": "Use when editing src/.",
        "paths": ["src/*"],
    })
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()

    activated = sm.activate_for_path(str(workspace / "src" / "x.py"))
    assert activated == ["src-files"]


def test_skill_debug_and_remember_skills_load(fresh_skills_dir):
    """Block I-10 (debug) + I-11 (remember) bundled skills are
    discoverable after Block I lands them under skills/."""
    # This test runs against the REAL skills/ directory, not the fixture.
    # Use the agent's own workspace.
    from skills.manager import SkillManager
    real_workspace = os.path.dirname(_AGENT_ROOT)  # MAIN/
    real_skills_dir = os.path.join(_AGENT_ROOT, "skills")
    sm = SkillManager(workspace=real_workspace, skills_dir=real_skills_dir)
    sm.discover()
    assert "debug" in sm._cache, (
        "Block I-10 lock: skills/debug/SKILL.md must be discoverable"
    )
    assert "remember" in sm._cache, (
        "Block I-11 lock: skills/remember/SKILL.md must be discoverable"
    )
    # remember has disable_model_invocation:true → not in model_invocable list.
    model_invocable = {s["name"] for s in sm.list_model_invocable()}
    assert "remember" not in model_invocable
    assert "debug" in model_invocable


# ============================================================
# Codex iter-1 finding-lock tests
# ============================================================

def test_paths_directory_root_pattern_activates_descendants(fresh_skills_dir):
    """Codex iter-1 finding #1 lock: `paths: src/**` strips to `src` at
    discover-time and must auto-activate when the user edits ANY file
    under src/, including descendants. fnmatch alone wouldn't match
    `src` against `src/x.py`; the activate_for_path logic adds an
    explicit prefix check.
    """
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "src-skill", {
        "name": "src-skill",
        "description": "Use under src/.",
        "paths": ["src/**"],   # → normalizes to "src"
    })
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()
    # Editing src/foo/bar.py → must activate src-skill.
    activated = sm.activate_for_path(str(workspace / "src" / "foo" / "bar.py"))
    assert activated == ["src-skill"]
    assert sm.active_skill == "src-skill"


def test_paths_first_match_wins_per_adr029(fresh_skills_dir):
    """Codex iter-1 finding #4 lock: when two skills' paths both match
    the edited file, only the FIRST match (by SkillManager._cache order)
    activates. ADR-029 §1 documents first-match-wins; without the fix
    a later-match would silently overwrite active_skill.

    Codex iter-2 finding #1 tightening: pin the expected winner to
    `alpha` (sorted-rglob order puts alpha before beta) so this test
    catches an implementation that activates ONLY beta as well.
    """
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "alpha", {
        "name": "alpha",
        "description": "First.",
        "paths": ["*.py"],
    })
    _write_skill(skills_dir, "beta", {
        "name": "beta",
        "description": "Second.",
        "paths": ["*.py"],
    })
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()
    # Sanity: cache order matches the alphabetical rglob output that
    # discover() iterates, so alpha is "first".
    assert list(sm._cache.keys()) == ["alpha", "beta"]
    activated = sm.activate_for_path("foo.py")
    # Exactly ONE skill activated AND it must be alpha (first in cache
    # order). A loose assert (`activated[0] in {"alpha","beta"}`) would
    # accept an implementation that activates ONLY beta — that's the
    # silent-overwrite bug the iter-2 fix was supposed to close.
    assert activated == ["alpha"]
    assert sm.active_skill == "alpha"


def test_disable_model_invocation_filters_discover_relevant(fresh_skills_dir):
    """Codex iter-1 finding #2 lock: discover_relevant() must skip
    skills with disable_model_invocation:true even when triggers fire.
    Otherwise the model would still see remember/-style user-only
    skills as auto-suggestions.
    """
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "user-only", {
        "name": "user-only",
        "description": "Use when user runs it.",
        "auto_trigger": "true",
        "triggers": ["save"],
        "disable_model_invocation": "true",
    })
    _write_skill(skills_dir, "open-skill", {
        "name": "open-skill",
        "description": "Use anytime.",
        "auto_trigger": "true",
        "triggers": ["save"],
    })
    sm = SkillManager(
        workspace=str(workspace),
        skills_dir=str(skills_dir),
        enable_auto_trigger=True,
    )
    sm.discover()
    relevant = sm.discover_relevant("please save this file")
    assert "open-skill" in relevant
    assert "user-only" not in relevant


def test_disable_model_invocation_blocks_skill_tool_read_and_activate(fresh_skills_dir, monkeypatch):
    """Codex iter-1 finding #2 lock: the model-facing skill TOOL
    (subcommand read / activate) must reject disable_model_invocation
    skills with a clear error pointing the user to /skill use.
    """
    from skills.manager import SkillManager
    from tools import bootstrap_built_ins
    from tools.registry import find_tool_by_name, all_registered, _reset_registry_for_tests
    from tools import skill as _skill_tool_mod

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "user-only", {
        "name": "user-only",
        "description": "Use when user runs it.",
        "disable_model_invocation": "true",
    })
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    monkeypatch.setattr(_skill_tool_mod, "_get_skill_manager", lambda ctx: sm)

    _reset_registry_for_tests()
    bootstrap_built_ins()
    skill_tool = find_tool_by_name(all_registered(), "skill")
    assert skill_tool is not None

    # list MUST omit user-only.
    listed = skill_tool.execute({"subcommand": "list"}, context={})
    assert "user-only" not in listed

    # read MUST reject.
    r_read = skill_tool.execute(
        {"subcommand": "read", "name": "user-only"}, context={},
    )
    assert "user-invocable only" in r_read.lower()

    # activate MUST reject.
    r_act = skill_tool.execute(
        {"subcommand": "activate", "name": "user-only"}, context={},
    )
    assert "user-invocable only" in r_act.lower()


def test_get_active_skill_prompt_substitutes_skill_dir_and_session(fresh_skills_dir):
    """Codex iter-1 finding #3 lock: get_active_skill_prompt() must
    apply substitute_skill_vars() so ${CLAUDE_SKILL_DIR} and
    ${CLAUDE_SESSION_ID} resolve in the injected prompt body.
    """
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "vartest2", {
        "name": "vartest2",
        "description": "Test substitution wiring.",
    }, body="Helpers live at ${CLAUDE_SKILL_DIR}/run.sh under session ${CLAUDE_SESSION_ID}.")

    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()
    sm.active_skill = "vartest2"

    out = sm.get_active_skill_prompt(session_id="sess-XYZ")
    assert "${CLAUDE_SKILL_DIR}" not in out, (
        "get_active_skill_prompt must substitute ${CLAUDE_SKILL_DIR} "
        "(Codex iter-1 finding #3)"
    )
    assert "${CLAUDE_SESSION_ID}" not in out
    assert "sess-XYZ" in out
    # The skill dir is forward-slashed cross-platform.
    assert "vartest2" in out.replace("\\", "/")


def test_skill_realpath_dedup_state_isolated_between_discover_calls(fresh_skills_dir):
    """The seen_realpaths set must be local to discover() (not instance
    state) so multiple discover() calls behave identically."""
    from skills.manager import SkillManager

    workspace, skills_dir = fresh_skills_dir
    _write_skill(skills_dir, "alpha", {"name": "alpha", "description": "x"})
    sm = SkillManager(workspace=str(workspace), skills_dir=str(skills_dir))
    sm.discover()
    assert "alpha" in sm._cache
    # Second discover() call must still find it (not silently dedup itself).
    sm.discover()
    assert "alpha" in sm._cache
