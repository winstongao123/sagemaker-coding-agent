"""Tests for compact_v2 new features: config loading, skills, commands, agent types, MCP, diffs."""
import json
import os
import sys
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ============================================================
# CONFIG FILE LOADING
# ============================================================

def test_load_config_file_returns_empty_when_no_file():
    from sagemaker_agent import _load_config_file
    result = _load_config_file("/nonexistent/path")
    assert result == {}


def test_load_config_file_parses_json():
    from sagemaker_agent import _load_config_file
    tmpdir = tempfile.mkdtemp()
    try:
        config_path = os.path.join(tmpdir, "opencode.json")
        with open(config_path, "w") as f:
            json.dump({"enable_skills": False, "max_turns": 50}, f)
        result = _load_config_file(tmpdir)
        assert result["enable_skills"] is False
        assert result["max_turns"] == 50
    finally:
        shutil.rmtree(tmpdir)


def test_load_config_file_strips_jsonc_comments():
    from sagemaker_agent import _load_config_file
    tmpdir = tempfile.mkdtemp()
    try:
        config_path = os.path.join(tmpdir, "opencode.json")
        with open(config_path, "w") as f:
            f.write('{\n  // This is a comment\n  "max_turns": 42\n}\n')
        result = _load_config_file(tmpdir)
        assert result["max_turns"] == 42
    finally:
        shutil.rmtree(tmpdir)


# ============================================================
# SKILL MANAGER
# ============================================================

def test_skill_manager_discovers_frontmatter_skills():
    from sagemaker_agent import SkillManager
    tmpdir = tempfile.mkdtemp()
    try:
        skills_dir = os.path.join(tmpdir, "skills", "review")
        os.makedirs(skills_dir)
        with open(os.path.join(skills_dir, "SKILL.md"), "w") as f:
            f.write("---\nname: code-review\ndescription: Review code\n---\n## Instructions\nDo a review.\n")
        mgr = SkillManager(tmpdir, "skills")
        skills = mgr.discover()
        assert "code-review" in skills
        assert skills["code-review"].description == "Review code"
    finally:
        shutil.rmtree(tmpdir)


def test_skill_manager_reads_content_without_frontmatter():
    from sagemaker_agent import SkillManager
    tmpdir = tempfile.mkdtemp()
    try:
        skills_dir = os.path.join(tmpdir, "skills", "test")
        os.makedirs(skills_dir)
        with open(os.path.join(skills_dir, "SKILL.md"), "w") as f:
            f.write("---\nname: test-skill\ndescription: Test\n---\nActual content here.\n")
        mgr = SkillManager(tmpdir, "skills")
        mgr.discover()
        ok, content = mgr.read_skill("test-skill")
        assert ok is True
        assert "Actual content here" in content
        assert "---" not in content  # Frontmatter stripped
    finally:
        shutil.rmtree(tmpdir)


def test_skill_manager_list_for_prompt_xml():
    from sagemaker_agent import SkillManager
    tmpdir = tempfile.mkdtemp()
    try:
        skills_dir = os.path.join(tmpdir, "skills", "demo")
        os.makedirs(skills_dir)
        with open(os.path.join(skills_dir, "SKILL.md"), "w") as f:
            f.write("---\nname: demo\ndescription: Demo skill\n---\nContent.\n")
        mgr = SkillManager(tmpdir, "skills")
        mgr.discover()
        xml = mgr.list_for_prompt()
        assert "<available_skills>" in xml
        assert "<name>demo</name>" in xml
        assert "<description>Demo skill</description>" in xml
    finally:
        shutil.rmtree(tmpdir)


# ============================================================
# COMMAND REGISTRY
# ============================================================

def test_command_registry_expand():
    from sagemaker_agent import CommandRegistry
    cmds = CommandRegistry({
        "review": {"template": "Review this:\n$ARGUMENTS", "description": "Code review"},
        "fix": {"template": "Fix $1 in $2", "description": "Fix something"},
    })
    result = cmds.expand("review", "src/main.py")
    assert result == "Review this:\nsrc/main.py"

    result2 = cmds.expand("fix", "bug utils.py")
    assert result2 == "Fix bug in utils.py"


def test_command_registry_returns_none_for_unknown():
    from sagemaker_agent import CommandRegistry
    cmds = CommandRegistry({"review": {"template": "Review $ARGUMENTS"}})
    assert cmds.expand("unknown", "args") is None


def test_command_registry_list():
    from sagemaker_agent import CommandRegistry
    cmds = CommandRegistry({
        "review": {"template": "...", "description": "Code review"},
        "test": {"template": "...", "description": "Run tests"},
    })
    listed = cmds.list_commands()
    assert len(listed) == 2
    names = {c["name"] for c in listed}
    assert names == {"review", "test"}


# ============================================================
# AGENT TYPES
# ============================================================

def test_agent_types_defined():
    from sagemaker_agent import AGENT_TYPES
    assert "build" in AGENT_TYPES
    assert "plan" in AGENT_TYPES
    assert "explore" in AGENT_TYPES
    assert "general" in AGENT_TYPES


def test_agent_types_plan_is_readonly():
    from sagemaker_agent import AGENT_TYPES
    plan = AGENT_TYPES["plan"]
    assert plan["tools"] is not None
    # Plan should not have write tools
    assert "write_file" not in plan["tools"]
    assert "edit_file" not in plan["tools"]
    assert "bash" not in plan["tools"]


def test_agent_types_build_has_all_tools():
    from sagemaker_agent import AGENT_TYPES
    build = AGENT_TYPES["build"]
    assert build["tools"] is None  # None means all tools


def test_agent_types_explore_is_minimal():
    from sagemaker_agent import AGENT_TYPES
    explore = AGENT_TYPES["explore"]
    assert explore["tools"] is not None
    assert "read_file" in explore["tools"]
    assert "glob" in explore["tools"]
    assert "bash" not in explore["tools"]


# ============================================================
# MCP MANAGER
# ============================================================

def test_mcp_manager_empty_config():
    from sagemaker_agent import McpManager
    mgr = McpManager({})
    mgr.connect_all()
    assert mgr.status_summary() == ""
    assert mgr.discover_tools() == {}


def test_mcp_manager_disabled_server():
    from sagemaker_agent import McpManager
    mgr = McpManager({"test": {"type": "local", "command": ["echo"], "enabled": False}})
    mgr.connect_all()
    assert mgr.status["test"] == "disabled"


def test_mcp_manager_invalid_type():
    from sagemaker_agent import McpManager
    mgr = McpManager({"test": {"type": "invalid"}})
    mgr.connect_all()
    assert mgr.status["test"] == "failed"


def test_mcp_manager_missing_command():
    from sagemaker_agent import McpManager
    mgr = McpManager({"test": {"type": "local", "command": []}})
    mgr.connect_all()
    assert mgr.status["test"] == "failed"


def test_mcp_manager_status_summary():
    from sagemaker_agent import McpManager
    mgr = McpManager({"a": {"type": "local", "command": []}, "b": {"type": "local", "command": [], "enabled": False}})
    mgr.connect_all()
    summary = mgr.status_summary()
    assert "0/2" in summary


# ============================================================
# DIFF GENERATION
# ============================================================

def test_generate_unified_diff():
    from sagemaker_agent import _generate_unified_diff
    old = "line1\nline2\nline3\n"
    new = "line1\nline2_modified\nline3\n"
    diff = _generate_unified_diff("/tmp/test.py", old, new)
    assert "---" in diff
    assert "+++" in diff
    assert "-line2" in diff
    assert "+line2_modified" in diff


def test_generate_unified_diff_empty_old():
    from sagemaker_agent import _generate_unified_diff
    diff = _generate_unified_diff("/tmp/test.py", "", "new content\n")
    assert "+new content" in diff


# ============================================================
# TOOL REGISTRY
# ============================================================

def test_tools_registry_has_new_tools():
    from sagemaker_agent import TOOLS
    assert "skill" in TOOLS
    assert "task" in TOOLS
    assert "web_fetch" in TOOLS
    # Old names should be gone
    assert "skill_list" not in TOOLS
    assert "skill_read" not in TOOLS
    assert "mcp_call" not in TOOLS
    assert "subagent_run" not in TOOLS


def test_plan_mode_blocked_tools_updated():
    from sagemaker_agent import PLAN_MODE_BLOCKED_TOOLS, PLAN_MODE_ALLOWED_TOOLS
    assert "task" in PLAN_MODE_BLOCKED_TOOLS
    assert "skill" in PLAN_MODE_ALLOWED_TOOLS
    assert "subagent_run" not in PLAN_MODE_BLOCKED_TOOLS
    assert "mcp_call" not in PLAN_MODE_BLOCKED_TOOLS


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
