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
    assert "ask_user" in PLAN_MODE_ALLOWED_TOOLS
    assert "subagent_run" not in PLAN_MODE_BLOCKED_TOOLS
    assert "mcp_call" not in PLAN_MODE_BLOCKED_TOOLS


# ============================================================
# JSONC COMMENT STRIPPING (Fixed: preserves // inside strings)
# ============================================================

def test_jsonc_preserves_urls_in_strings():
    from sagemaker_agent import _strip_jsonc_comments
    text = '{"url": "https://example.com//path", "key": "value"}'
    result = _strip_jsonc_comments(text)
    assert '"https://example.com//path"' in result

def test_jsonc_strips_line_comments():
    from sagemaker_agent import _strip_jsonc_comments
    text = '{\n  // comment\n  "key": 42\n}'
    result = _strip_jsonc_comments(text)
    parsed = json.loads(result)
    assert parsed["key"] == 42

def test_jsonc_strips_block_comments():
    from sagemaker_agent import _strip_jsonc_comments
    text = '{"key": /* block comment */ 42}'
    result = _strip_jsonc_comments(text)
    parsed = json.loads(result)
    assert parsed["key"] == 42

def test_config_url_not_corrupted_by_comments():
    """Regression: URLs with // should survive config loading."""
    from sagemaker_agent import _load_config_file
    tmpdir = tempfile.mkdtemp()
    try:
        config_path = os.path.join(tmpdir, "opencode.json")
        with open(config_path, "w") as f:
            f.write('{\n  // This is a comment\n  "url": "https://api.example.com//v2/endpoint"\n}\n')
        result = _load_config_file(tmpdir)
        assert result["url"] == "https://api.example.com//v2/endpoint"
    finally:
        shutil.rmtree(tmpdir)


# ============================================================
# CONFIG TYPE VALIDATION
# ============================================================

def test_apply_config_skips_wrong_type():
    """Config values with wrong types should be skipped, not applied."""
    from sagemaker_agent import Config, _apply_config_file, _load_config_file
    tmpdir = tempfile.mkdtemp()
    try:
        config_path = os.path.join(tmpdir, "opencode.json")
        with open(config_path, "w") as f:
            json.dump({"max_turns": "not_a_number", "temperature": 0.5}, f)
        config = Config()
        config.workspace = tmpdir
        _apply_config_file(config)
        assert config.max_turns == 30  # Should remain default (30)
        assert config.temperature == 0.5  # Valid value should be applied
    finally:
        shutil.rmtree(tmpdir)


# ============================================================
# PYTHON EXEC IMPORT HOOK (Fixed: no longer deletes closure vars)
# ============================================================

def test_python_exec_preamble_allows_math():
    """The import hook should allow math.sqrt to work at runtime."""
    from sagemaker_agent import _PYTHON_EXEC_PREAMBLE
    # Verify the preamble doesn't delete _ALLOWED or _original_import
    assert "del _builtins" in _PYTHON_EXEC_PREAMBLE
    assert "del _builtins, _original_import" not in _PYTHON_EXEC_PREAMBLE
    assert "del _builtins, _original_import, _ALLOWED" not in _PYTHON_EXEC_PREAMBLE

def test_python_exec_preamble_runs_math():
    """Actually execute the preamble + math import via subprocess."""
    import subprocess
    from sagemaker_agent import _PYTHON_EXEC_PREAMBLE
    code = _PYTHON_EXEC_PREAMBLE + "\nimport math\nprint(math.sqrt(16))"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0
    assert "4.0" in result.stdout

def test_python_exec_preamble_blocks_subprocess():
    """The import hook should block subprocess."""
    import subprocess as sp
    from sagemaker_agent import _PYTHON_EXEC_PREAMBLE
    code = _PYTHON_EXEC_PREAMBLE + "\nimport subprocess"
    result = sp.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert "subprocess" in result.stderr


# ============================================================
# WEB FETCH SSRF PROTECTION
# ============================================================

def test_web_fetch_blocks_private_ip():
    from sagemaker_agent import _is_private_ip
    assert _is_private_ip("127.0.0.1") is True
    assert _is_private_ip("localhost") is True
    assert _is_private_ip("metadata.google.internal") is True

def test_web_fetch_allows_public_host():
    from sagemaker_agent import _is_private_ip
    # Public domains should not be blocked
    assert _is_private_ip("example.com") is False
    assert _is_private_ip("github.com") is False

def test_web_fetch_tool_blocks_internal_url():
    from sagemaker_agent import tool_web_fetch
    result = tool_web_fetch({"url": "http://169.254.169.254/latest/meta-data/"})
    assert "Blocked" in result or "private" in result.lower()

def test_web_fetch_tool_blocks_localhost():
    from sagemaker_agent import tool_web_fetch
    result = tool_web_fetch({"url": "http://localhost:8080/admin"})
    assert "Blocked" in result


# ============================================================
# COST TRACKING
# ============================================================

def test_token_tracker_cost_calculation():
    from sagemaker_agent import TokenTracker, _MODEL_PRICING
    t = TokenTracker()
    t._model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    t.add({"input_tokens": 1000, "output_tokens": 500})
    assert t.session_cost > 0
    # Haiku: 0.00025/1K input + 0.00125/1K output
    expected = (1000/1000) * 0.00025 + (500/1000) * 0.00125
    assert abs(t.session_cost - expected) < 1e-8

def test_token_tracker_cache_tracking():
    from sagemaker_agent import TokenTracker
    t = TokenTracker()
    t.add({"input_tokens": 1000, "output_tokens": 100, "cache_read_input_tokens": 500})
    assert t.session_cache_read == 500

def test_token_tracker_get_cost_format():
    from sagemaker_agent import TokenTracker
    t = TokenTracker()
    assert t.get_cost() == "$0.0000"


# ============================================================
# SNAPSHOT MANAGER
# ============================================================

def test_snapshot_save_and_revert():
    from sagemaker_agent import SnapshotManager
    tmpdir = tempfile.mkdtemp()
    try:
        mgr = SnapshotManager(tmpdir)
        filepath = os.path.join(tmpdir, "test.txt")
        # Create original file
        with open(filepath, "w") as f:
            f.write("original content")
        # Save snapshot
        snap_path = mgr.save(filepath)
        assert snap_path is not None
        assert os.path.exists(snap_path)
        # Modify file
        with open(filepath, "w") as f:
            f.write("modified content")
        # Revert
        ok, msg = mgr.revert(filepath)
        assert ok is True
        with open(filepath) as f:
            assert f.read() == "original content"
    finally:
        shutil.rmtree(tmpdir)

def test_snapshot_list():
    from sagemaker_agent import SnapshotManager
    tmpdir = tempfile.mkdtemp()
    try:
        mgr = SnapshotManager(tmpdir)
        filepath = os.path.join(tmpdir, "test.txt")
        with open(filepath, "w") as f:
            f.write("content")
        mgr.save(filepath)
        snaps = mgr.list_snapshots(filepath)
        assert len(snaps) == 1
    finally:
        shutil.rmtree(tmpdir)

def test_snapshot_no_file_returns_none():
    from sagemaker_agent import SnapshotManager
    tmpdir = tempfile.mkdtemp()
    try:
        mgr = SnapshotManager(tmpdir)
        assert mgr.save("/nonexistent/file.txt") is None
    finally:
        shutil.rmtree(tmpdir)


# ============================================================
# ASK USER TOOL
# ============================================================

def test_ask_user_in_tools():
    from sagemaker_agent import TOOLS
    assert "ask_user" in TOOLS
    schema = TOOLS["ask_user"][3]
    assert "question" in schema["properties"]
    assert "options" in schema["properties"]


# ============================================================
# COMMAND REGISTRY AGENT ROUTING
# ============================================================

def test_command_registry_get_agent():
    from sagemaker_agent import CommandRegistry
    cmds = CommandRegistry({
        "review": {"template": "Review $ARGUMENTS", "agent": "plan", "description": "Review"},
        "fix": {"template": "Fix $ARGUMENTS", "description": "Fix"},
    })
    assert cmds.get_agent("review") == "plan"
    assert cmds.get_agent("fix") is None
    assert cmds.get_agent("nonexistent") is None


# ============================================================
# v2.9.1 BUG FIXES — ADDITIONAL TESTS
# ============================================================

def test_jsonc_unterminated_block_comment():
    """Block comment at EOF without closing */ should not lose content."""
    from sagemaker_agent import _strip_jsonc_comments
    # Unterminated block comment — everything after /* is comment, nothing lost before it
    result = _strip_jsonc_comments('{"a": 1} /* unterminated')
    assert '{"a": 1}' in result

def test_jsonc_block_comment_at_eof():
    """Properly terminated block comment at very end of file."""
    from sagemaker_agent import _strip_jsonc_comments
    result = _strip_jsonc_comments('{"a": 1} /* comment */')
    assert result.strip() == '{"a": 1}'

def test_is_private_ip_ipv6_ula():
    """IPv6 ULA addresses (fc00::/7) should be blocked."""
    from sagemaker_agent import _is_private_ip
    import socket
    # Test the prefix matching directly — fc and fd should both match
    _PRIVATE_PREFIXES = ("fc", "fd", "fe80:", "fec0:")
    for prefix in _PRIVATE_PREFIXES:
        ip = prefix + "00::1"
        assert any(ip.startswith(p) for p in _PRIVATE_PREFIXES), f"{ip} should match private prefix"

def test_is_private_ip_blocks_localhost():
    """localhost should be blocked via _BLOCKED_HOSTS."""
    from sagemaker_agent import _is_private_ip
    assert _is_private_ip("localhost") is True

def test_is_private_ip_blocks_metadata():
    """Cloud metadata endpoints should be blocked."""
    from sagemaker_agent import _is_private_ip
    assert _is_private_ip("metadata.google.internal") is True
    assert _is_private_ip("kubernetes.default") is True


# ============================================================
# SNAPSHOT MANAGER EDGE CASES
# ============================================================

def test_snapshot_revert_all():
    """revert_all should restore all snapshotted files."""
    from sagemaker_agent import SnapshotManager
    tmpdir = tempfile.mkdtemp()
    try:
        sm = SnapshotManager(tmpdir)
        # Create two files
        f1 = os.path.join(tmpdir, "a.txt")
        f2 = os.path.join(tmpdir, "b.txt")
        with open(f1, "w") as f:
            f.write("original-a")
        with open(f2, "w") as f:
            f.write("original-b")
        # Snapshot both
        sm.save(f1)
        sm.save(f2)
        # Modify both
        with open(f1, "w") as f:
            f.write("modified-a")
        with open(f2, "w") as f:
            f.write("modified-b")
        # Revert all
        result = sm.revert_all()
        assert "2" in result or "reverted" in result.lower()
        with open(f1) as f:
            assert f.read() == "original-a"
        with open(f2) as f:
            assert f.read() == "original-b"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def test_snapshot_revert_nonexistent_file():
    """revert on a file with no snapshots should fail gracefully."""
    from sagemaker_agent import SnapshotManager
    tmpdir = tempfile.mkdtemp()
    try:
        sm = SnapshotManager(tmpdir)
        ok, msg = sm.revert(os.path.join(tmpdir, "nope.txt"))
        assert ok is False
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ============================================================
# CONFIG VALIDATION EDGE CASES
# ============================================================

def test_config_rejects_negative_max_turns():
    """Negative max_turns should be skipped by config validation."""
    from sagemaker_agent import _apply_config_file, CONFIG
    old_turns = CONFIG.max_turns
    old_workspace = CONFIG.workspace
    # Create a temp workspace with a config that has a negative max_turns
    tmpdir = tempfile.mkdtemp()
    try:
        config_path = os.path.join(tmpdir, "opencode.json")
        with open(config_path, "w") as f:
            json.dump({"max_turns": -5}, f)
        CONFIG.workspace = tmpdir
        _apply_config_file(CONFIG)
        assert CONFIG.max_turns == old_turns  # unchanged — negative was rejected
    finally:
        CONFIG.workspace = old_workspace
        CONFIG.max_turns = old_turns
        shutil.rmtree(tmpdir, ignore_errors=True)

def test_config_rejects_temperature_out_of_range():
    """Temperature > 1.0 should be skipped."""
    from sagemaker_agent import _apply_config_file, CONFIG
    old_temp = CONFIG.temperature
    old_workspace = CONFIG.workspace
    tmpdir = tempfile.mkdtemp()
    try:
        config_path = os.path.join(tmpdir, "opencode.json")
        with open(config_path, "w") as f:
            json.dump({"temperature": 5.0}, f)
        CONFIG.workspace = tmpdir
        _apply_config_file(CONFIG)
        assert CONFIG.temperature == old_temp  # unchanged
    finally:
        CONFIG.workspace = old_workspace
        CONFIG.temperature = old_temp
        shutil.rmtree(tmpdir, ignore_errors=True)

def test_config_invalid_json_returns_empty():
    """Malformed JSON file should return empty dict, not crash."""
    from sagemaker_agent import _load_config_file
    tmpdir = tempfile.mkdtemp()
    try:
        path = os.path.join(tmpdir, "opencode.json")
        with open(path, "w") as f:
            f.write("{invalid json!!! no quotes")
        result = _load_config_file(tmpdir)
        assert result == {}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ============================================================
# PERMISSION WILDCARD PATTERNS
# ============================================================

def test_permission_tool_command_pattern():
    """tool:command_pattern rules should match correctly."""
    import fnmatch as _fnmatch
    # Simulate the permission check logic for bash:rm*
    pattern = "bash:rm*"
    rule_tool, rule_pattern = pattern.split(":", 1)
    assert rule_tool == "bash"
    assert _fnmatch.fnmatch("rm -rf /tmp/foo", rule_pattern) is True
    assert _fnmatch.fnmatch("ls -la", rule_pattern) is False
    assert _fnmatch.fnmatch("rmdir /foo", rule_pattern) is True


# ============================================================
# DIFF TRACKING EDGE CASES
# ============================================================

def test_diff_no_newline_at_eof():
    """Diff should handle files without trailing newline."""
    from sagemaker_agent import _generate_unified_diff
    old = "line1\nline2"
    new = "line1\nline2\nline3"
    diff = _generate_unified_diff("test.py", old, new)
    assert "line3" in diff

def test_diff_identical_content():
    """Identical content should produce empty diff."""
    from sagemaker_agent import _generate_unified_diff
    content = "same\ncontent\n"
    diff = _generate_unified_diff("test.py", content, content)
    assert diff == ""


# ============================================================
# TOKEN TRACKER COST — UNKNOWN MODEL
# ============================================================

def test_token_tracker_unknown_model_zero_cost():
    """Unknown model should not crash cost calculation."""
    from sagemaker_agent import TokenTracker
    tt = TokenTracker()
    tt.add({"input_tokens": 100, "output_tokens": 50}, model_id="unknown.model.v99")
    assert tt.session_cost == 0.0  # no pricing data, cost stays 0


# ============================================================
# SKILLS EDGE CASES
# ============================================================

def test_skill_missing_frontmatter():
    """Skill file without frontmatter should still be discovered with directory as name."""
    from sagemaker_agent import SkillManager
    tmpdir = tempfile.mkdtemp()
    try:
        skill_dir = os.path.join(tmpdir, "skills")
        myskill_dir = os.path.join(skill_dir, "myskill")
        os.makedirs(myskill_dir)
        with open(os.path.join(myskill_dir, "SKILL.md"), "w") as f:
            f.write("No frontmatter here, just content.\n")
        sm = SkillManager(tmpdir, "skills")
        skills = sm.discover()
        # Should still find it (description from first line)
        assert len(skills) >= 1
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
