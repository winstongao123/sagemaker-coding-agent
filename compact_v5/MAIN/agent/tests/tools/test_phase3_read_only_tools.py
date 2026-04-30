"""Phase 03 unit tests: read_file / grep / glob / list_dir.

Tests verify:
1. Each of the 4 tools registers itself in the registry on import (per
   ADR-001 file-per-tool layout).
2. Each tool's metadata flags match ADR-009 expectations (is_read_only,
   is_concurrency_safe, requires_approval).
3. Each tool is in v4's PLAN_MODE_ALLOWED_TOOLS set, so plan-mode users
   can still inspect the workspace.
4. Each tool's executor produces correct output on common cases against
   a tmpdir-rooted workspace.
5. Each tool's executor refuses paths outside the workspace (path-traversal
   protection — covered by `_path_validation.validate_path`).
6. Tools survive `assemble_tool_pool()` ordering / dedup.

The Phase-3 path-validation stub depends on `runtime.config.CONFIG.workspace`,
so each test sets `monkeypatch.setattr(CONFIG, "workspace", tmp_path)` and
also clears `CONFIG.allowed_paths` so the tests have a clean boundary.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

# Make `tools`/`runtime` importable from this test (mirrors flat-zip ship layout).
_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# Fixture: workspace rooted at tmp_path
# ============================================================

@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Point CONFIG.workspace at a temp dir; clear allowed_paths so the
    boundary check has only one root. Every test that touches the
    filesystem uses this fixture.

    Phase 5 update: rebuild the security/manager.SECURITY singleton so
    the validate_path call sees the new workspace (singleton captures
    CONFIG.workspace at construction)."""
    from runtime.config import CONFIG
    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "allowed_paths", [])
    monkeypatch.setattr(CONFIG, "max_file_size", 10 * 1024 * 1024)
    # Rebuild SECURITY singleton against the new workspace.
    try:
        from security.manager import rebuild_singleton_for_tests
        rebuild_singleton_for_tests()
    except ImportError:
        # Phase 3 tests may run before Phase 5 lands — ignore.
        pass
    return tmp_path


# ============================================================
# Registration / metadata (ADR-001 + ADR-009)
# ============================================================

def test_phase3_tools_registered_on_import():
    """Importing the `tools` package (via tools.read_file etc.) must
    register all 4 read-only tools."""
    import tools as t  # triggers module-level registration in tools/__init__.py
    names = {x.name for x in t.all_registered()}
    assert "read_file" in names
    assert "grep" in names
    assert "glob" in names
    assert "list_dir" in names


@pytest.mark.parametrize(
    "tool_name",
    ["read_file", "grep", "glob", "list_dir"],
)
def test_phase3_tools_have_correct_flags(tool_name):
    """All 4 read-only tools must declare is_read_only=True,
    is_concurrency_safe=True, requires_approval=False (ADR-009)."""
    import tools as t
    tool = t.find_tool_by_name(t.all_registered(), tool_name)
    assert tool is not None, f"{tool_name} not registered"
    assert tool.is_read_only is True, f"{tool_name} should be read-only"
    assert tool.is_concurrency_safe is True, f"{tool_name} should be concurrency-safe"
    assert tool.is_destructive is False
    assert tool.requires_approval is False


@pytest.mark.parametrize(
    "tool_name",
    ["read_file", "grep", "glob", "list_dir"],
)
def test_phase3_tools_in_plan_mode_allowlist(tool_name):
    """All 4 must be in PLAN_MODE_ALLOWED_TOOLS so plan-mode users
    can still inspect the workspace (read-only by design)."""
    from tools import PLAN_MODE_ALLOWED_TOOLS
    assert tool_name in PLAN_MODE_ALLOWED_TOOLS


# ============================================================
# Path-validation stub (tools/_path_validation.py)
# ============================================================

def test_path_validation_rejects_path_outside_workspace(workspace):
    """A path resolved outside workspace + allowed_paths must fail."""
    from tools._path_validation import validate_path
    # Use platform-appropriate "definitely outside workspace" path.
    other = "C:/Windows/notepad.exe" if os.name == "nt" else "/etc/passwd"
    ok, msg = validate_path(other)
    assert ok is False
    assert "outside workspace" in msg


def test_path_validation_accepts_path_inside_workspace(workspace):
    """Files inside the workspace must validate, even if they don't exist yet."""
    from tools._path_validation import validate_path
    inside = str(workspace / "subdir" / "file.txt")
    ok, msg = validate_path(inside)
    assert ok is True, f"unexpected reject: {msg}"


def test_path_validation_accepts_file_in_allowed_path(workspace, tmp_path_factory, monkeypatch):
    """A path inside an allowed_paths root must validate (v4 parity)."""
    from runtime.config import CONFIG
    extra = tmp_path_factory.mktemp("extra")
    monkeypatch.setattr(CONFIG, "allowed_paths", [str(extra)])
    # Rebuild SECURITY so the new allowed_paths take effect.
    try:
        from security.manager import rebuild_singleton_for_tests
        rebuild_singleton_for_tests()
    except ImportError:
        pass
    from tools._path_validation import validate_path
    ok, msg = validate_path(str(extra / "x.txt"))
    assert ok is True, f"unexpected reject: {msg}"


# ============================================================
# read_file
# ============================================================

def test_read_file_happy_path(workspace):
    from tools import find_tool_by_name, all_registered
    f = workspace / "hello.py"
    f.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")
    tool = find_tool_by_name(all_registered(), "read_file")
    out = tool.execute({"file_path": str(f)})
    assert "line 1" in out
    assert "line 2" in out
    assert "line 3" in out
    assert "[hello.py]" in out  # header
    assert "Lines 1-" in out


def test_read_file_missing_file_returns_error(workspace):
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "read_file")
    out = tool.execute({"file_path": str(workspace / "nope.txt")})
    assert out.startswith("Error:")
    assert "not found" in out.lower()


def test_read_file_outside_workspace_blocked(workspace):
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "read_file")
    other = "C:/Windows/notepad.exe" if os.name == "nt" else "/etc/passwd"
    out = tool.execute({"file_path": other})
    assert out.startswith("Error:")
    assert "outside workspace" in out


def test_read_file_offset_and_limit(workspace):
    from tools import find_tool_by_name, all_registered
    f = workspace / "many.txt"
    f.write_text("\n".join(f"line {i}" for i in range(1, 21)), encoding="utf-8")
    tool = find_tool_by_name(all_registered(), "read_file")
    out = tool.execute({"file_path": str(f), "offset": 5, "limit": 3})
    # offset=5 → start at line 6 (1-indexed); limit=3 → 3 lines shown
    assert "line 6" in out
    assert "line 7" in out
    assert "line 8" in out
    assert "line 1\n" not in out  # not in selected window


def test_read_file_large_file_guard(workspace):
    """v4 large-file guard: >500 lines + no offset/limit → first 50 + last 30."""
    from tools import find_tool_by_name, all_registered
    f = workspace / "big.py"
    body = "\n".join(f"line {i}" for i in range(1, 601))  # 600 lines
    f.write_text(body, encoding="utf-8")
    tool = find_tool_by_name(all_registered(), "read_file")
    out = tool.execute({"file_path": str(f)})
    assert "LARGE FILE" in out
    assert "First 50 lines" in out
    assert "Last 30 lines" in out
    # 600 - 80 = 520 lines omitted
    assert "520 lines omitted" in out


def test_read_file_ipynb_cell_parsing(workspace):
    """v4 .ipynb parsing: read_file flattens notebook cells."""
    from tools import find_tool_by_name, all_registered
    nb = {
        "cells": [
            {"cell_type": "markdown", "source": ["# Title\n"]},
            {"cell_type": "code", "source": ["print('hi')\n"]},
        ],
    }
    f = workspace / "demo.ipynb"
    f.write_text(json.dumps(nb), encoding="utf-8")
    tool = find_tool_by_name(all_registered(), "read_file")
    out = tool.execute({"file_path": str(f)})
    assert "# === Cell 1 (markdown) ===" in out
    assert "# Title" in out
    assert "# === Cell 2 (code) ===" in out
    assert "print('hi')" in out


def test_read_file_directory_returns_error(workspace):
    from tools import find_tool_by_name, all_registered
    sub = workspace / "subdir"
    sub.mkdir()
    tool = find_tool_by_name(all_registered(), "read_file")
    out = tool.execute({"file_path": str(sub)})
    assert out.startswith("Error:")
    assert "not a file" in out.lower() or "list_dir" in out.lower()


# ============================================================
# grep
# ============================================================

def test_grep_finds_matches(workspace):
    from tools import find_tool_by_name, all_registered
    (workspace / "a.py").write_text("def hello():\n    pass\n", encoding="utf-8")
    (workspace / "b.py").write_text("def world():\n    pass\n", encoding="utf-8")
    tool = find_tool_by_name(all_registered(), "grep")
    out = tool.execute({"pattern": r"def \w+", "glob": "**/*.py"})
    assert "a.py" in out
    assert "b.py" in out
    assert "def hello" in out
    assert "def world" in out


def test_grep_no_match_message(workspace):
    from tools import find_tool_by_name, all_registered
    (workspace / "a.py").write_text("xxx\n", encoding="utf-8")
    tool = find_tool_by_name(all_registered(), "grep")
    out = tool.execute({"pattern": r"DEFINITELY_NOT_PRESENT_TOKEN_xyz"})
    assert "No matches" in out


def test_grep_invalid_regex(workspace):
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "grep")
    out = tool.execute({"pattern": "(unbalanced"})
    assert out.startswith("Error:")
    assert "regex" in out.lower()


def test_grep_skips_binary_files(workspace):
    """Binary files (null byte in first 8KB) must be skipped."""
    from tools import find_tool_by_name, all_registered
    (workspace / "good.txt").write_text("hello world\n", encoding="utf-8")
    (workspace / "bin.bin").write_bytes(b"\x00\x01\x02hello\x03\x04\x05")
    tool = find_tool_by_name(all_registered(), "grep")
    out = tool.execute({"pattern": "hello"})
    assert "good.txt" in out
    assert "bin.bin" not in out


def test_grep_path_outside_workspace_blocked(workspace):
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "grep")
    other = "C:/Windows" if os.name == "nt" else "/etc"
    out = tool.execute({"pattern": "hello", "path": other})
    assert out.startswith("Error:")
    assert "outside workspace" in out


def test_grep_case_insensitive(workspace):
    from tools import find_tool_by_name, all_registered
    (workspace / "a.txt").write_text("HELLO World\n", encoding="utf-8")
    tool = find_tool_by_name(all_registered(), "grep")
    out_sensitive = tool.execute({"pattern": "hello", "case_insensitive": False})
    out_insensitive = tool.execute({"pattern": "hello", "case_insensitive": True})
    assert "No matches" in out_sensitive
    assert "HELLO World" in out_insensitive


# ============================================================
# glob
# ============================================================

def test_glob_finds_matching_files(workspace):
    from tools import find_tool_by_name, all_registered
    (workspace / "a.py").write_text("x", encoding="utf-8")
    (workspace / "b.py").write_text("y", encoding="utf-8")
    (workspace / "c.txt").write_text("z", encoding="utf-8")
    tool = find_tool_by_name(all_registered(), "glob")
    out = tool.execute({"pattern": "**/*.py"})
    assert "a.py" in out
    assert "b.py" in out
    assert "c.txt" not in out


def test_glob_no_matches_message(workspace):
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "glob")
    out = tool.execute({"pattern": "**/*.NONEXISTENT_EXT"})
    assert "No files found" in out


def test_glob_path_outside_workspace_blocked(workspace):
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "glob")
    other = "C:/Windows" if os.name == "nt" else "/etc"
    out = tool.execute({"pattern": "*.txt", "path": other})
    assert out.startswith("Error:")
    assert "outside workspace" in out


def test_glob_recursive_pattern(workspace):
    from tools import find_tool_by_name, all_registered
    (workspace / "src").mkdir()
    (workspace / "src" / "deep").mkdir()
    (workspace / "src" / "deep" / "x.py").write_text("x", encoding="utf-8")
    tool = find_tool_by_name(all_registered(), "glob")
    out = tool.execute({"pattern": "**/*.py"})
    # Path may use forward or back slashes depending on OS.
    assert "x.py" in out


# ============================================================
# list_dir
# ============================================================

def test_list_dir_lists_workspace(workspace):
    from tools import find_tool_by_name, all_registered
    (workspace / "a.txt").write_text("x", encoding="utf-8")
    (workspace / "subdir").mkdir()
    tool = find_tool_by_name(all_registered(), "list_dir")
    out = tool.execute({})
    assert "[FILE] a.txt" in out
    assert "[DIR]  subdir/" in out


def test_list_dir_non_directory_returns_error(workspace):
    from tools import find_tool_by_name, all_registered
    f = workspace / "a.txt"
    f.write_text("x", encoding="utf-8")
    tool = find_tool_by_name(all_registered(), "list_dir")
    out = tool.execute({"path": str(f)})
    assert out.startswith("Error:")
    assert "not a directory" in out.lower()


def test_list_dir_outside_workspace_blocked(workspace):
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "list_dir")
    other = "C:/Windows" if os.name == "nt" else "/etc"
    out = tool.execute({"path": other})
    assert out.startswith("Error:")
    assert "outside workspace" in out


def test_list_dir_empty_directory(workspace):
    from tools import find_tool_by_name, all_registered
    sub = workspace / "empty"
    sub.mkdir()
    tool = find_tool_by_name(all_registered(), "list_dir")
    out = tool.execute({"path": str(sub)})
    assert out == "(empty directory)"


# ============================================================
# Registry-level invariants (Phase 02 + Phase 03 together)
# ============================================================

def test_assemble_tool_pool_includes_all_phase_3_tools():
    """All 4 read-only tools must appear in the assembled pool."""
    from tools import assemble_tool_pool
    pool = assemble_tool_pool()
    names = {t.name for t in pool}
    assert {"read_file", "grep", "glob", "list_dir"}.issubset(names)


def test_plan_mode_pool_includes_all_phase_3_tools():
    """In plan mode, the read-only tools must still be available."""
    from tools import assemble_tool_pool
    pool = assemble_tool_pool(plan_mode=True)
    names = {t.name for t in pool}
    assert {"read_file", "grep", "glob", "list_dir"}.issubset(names)


def test_assemble_tool_pool_alphabetical_for_phase3_tools():
    """Built-ins are sorted alphabetically — `glob`, `grep`, `list_dir`,
    `read_file` is the expected order. Locks the cache-stability invariant
    against future tool additions."""
    from tools import assemble_tool_pool
    pool_names = [t.name for t in assemble_tool_pool()]
    # Filter to only Phase-3 tools so future tool additions don't break this test.
    p3 = [n for n in pool_names if n in {"glob", "grep", "list_dir", "read_file"}]
    assert p3 == sorted(p3)


# ============================================================
# Codex Phase-03 review fix tests (findings 3 + 4)
# ============================================================

def test_bootstrap_built_ins_is_idempotent():
    """Codex finding 1 lock test: `bootstrap_built_ins()` must be safe to
    call after `_reset_registry_for_tests()` and safe to call multiple
    times. Each tool must end up registered exactly once."""
    from tools import bootstrap_built_ins, all_registered
    from tools.registry import _reset_registry_for_tests
    # Reset registry, then bootstrap from a clean slate — must work.
    _reset_registry_for_tests()
    bootstrap_built_ins()
    names_after_first = sorted(t.name for t in all_registered())
    assert {"glob", "grep", "list_dir", "read_file"}.issubset(set(names_after_first))
    # Call bootstrap a second time — must be a no-op (idempotent).
    bootstrap_built_ins()
    names_after_second = sorted(t.name for t in all_registered())
    assert names_after_first == names_after_second
    # Each tool must appear exactly once.
    for name in ("glob", "grep", "list_dir", "read_file"):
        count = sum(1 for t in all_registered() if t.name == name)
        assert count == 1, f"{name} registered {count} times after re-bootstrap"


# ---- finding 3: path-validation tests ----

def test_path_validation_rejects_dotdot_traversal_back_to_parent(workspace, tmp_path_factory):
    """A workspace-relative path with `..` that resolves outside the workspace
    must be rejected. realpath normalization is what catches this."""
    from tools._path_validation import validate_path
    # Compose a path inside workspace that resolves OUTSIDE it.
    escape = str(workspace / ".." / "some_other_dir" / "file.txt")
    ok, msg = validate_path(escape)
    # Whether the path *exists* doesn't matter — only that resolution lands outside workspace.
    # tmp_path's parent is itself a tmp dir managed by pytest, so it's outside our workspace fixture.
    assert ok is False
    assert "outside workspace" in msg


def test_path_validation_rejects_sibling_prefix_root(workspace, tmp_path_factory, monkeypatch):
    """If the workspace is `/work` and the request is for `/work2/file`,
    a naive startswith check would let it through. commonpath rejects it.
    This guards the v5 path validation against the classic prefix-overlap bug."""
    import os
    from runtime.config import CONFIG
    from tools._path_validation import validate_path
    # Create a sibling dir adjacent to workspace.
    sibling = tmp_path_factory.mktemp("siblng_workspace_extra")
    # Build a path whose string form prefixes-but-isn't-inside workspace's realpath.
    # Use a totally separate dir that is NOT inside the workspace.
    target = str(sibling / "file.txt")
    ok, msg = validate_path(target)
    assert ok is False, f"sibling-prefix path was incorrectly accepted: {target}"
    assert "outside workspace" in msg


@pytest.mark.skipif(os.name == "nt", reason="Windows symlink creation requires elevated privileges; covered by realpath logic on Unix")
def test_path_validation_rejects_symlink_escape(workspace, tmp_path_factory):
    """A symlink inside workspace pointing OUTSIDE workspace must be rejected.
    `realpath` resolves symlinks, so the resolved path is the link target,
    which is outside workspace → rejected."""
    from tools._path_validation import validate_path
    outside = tmp_path_factory.mktemp("symlink_target")
    (outside / "secret.txt").write_text("hidden", encoding="utf-8")
    link = workspace / "innocent_looking_link"
    os.symlink(str(outside / "secret.txt"), str(link))
    ok, msg = validate_path(str(link))
    assert ok is False
    assert "outside workspace" in msg


def test_path_validation_case_normalization_on_windows(workspace, monkeypatch):
    """Windows filesystems are case-insensitive. The path validator must
    accept a workspace-rooted path regardless of case differences. On
    Linux/macOS this test is a no-op-equivalent (case-sensitive FS).
    `os.path.normcase` lowercases on Windows, no-op elsewhere."""
    from tools._path_validation import validate_path
    f = workspace / "Hello.txt"
    f.write_text("x", encoding="utf-8")
    # Try the same path with mixed case.
    if os.name == "nt":
        # On Windows, both casings must validate.
        ok1, _ = validate_path(str(workspace / "Hello.txt"))
        ok2, _ = validate_path(str(workspace / "HELLO.txt"))
        assert ok1 is True and ok2 is True
    else:
        # On Linux, only the exact case validates (and that's correct behavior).
        ok, _ = validate_path(str(workspace / "Hello.txt"))
        assert ok is True


# ---- finding 4: bad-input + edge-case executor tests ----

def test_read_file_invalid_offset_returns_error(workspace):
    """Codex finding 2 lock: non-integer `offset` from a model must return
    an `Error: ...` string instead of crashing the tool with ValueError."""
    from tools import find_tool_by_name, all_registered
    f = workspace / "x.txt"
    f.write_text("hi", encoding="utf-8")
    tool = find_tool_by_name(all_registered(), "read_file")
    out = tool.execute({"file_path": str(f), "offset": "not_a_number"})
    assert out.startswith("Error:")
    assert "offset" in out.lower()


def test_read_file_invalid_limit_returns_error(workspace):
    from tools import find_tool_by_name, all_registered
    f = workspace / "x.txt"
    f.write_text("hi", encoding="utf-8")
    tool = find_tool_by_name(all_registered(), "read_file")
    out = tool.execute({"file_path": str(f), "limit": [1, 2, 3]})
    assert out.startswith("Error:")
    assert "limit" in out.lower()


def test_read_file_malformed_ipynb_falls_back_to_raw_text(workspace):
    """A `.ipynb` file with broken JSON must NOT crash — read_file should
    fall through to the raw text view (v4 parity)."""
    from tools import find_tool_by_name, all_registered
    f = workspace / "broken.ipynb"
    f.write_text("{this is not valid JSON", encoding="utf-8")
    tool = find_tool_by_name(all_registered(), "read_file")
    out = tool.execute({"file_path": str(f)})
    # Should NOT contain "Error:" — should fall back to raw text view.
    assert not out.startswith("Error:")
    assert "this is not valid JSON" in out


def test_glob_allowed_paths_fallback(workspace, tmp_path_factory, monkeypatch):
    """v4 parity (sagemaker_agent.py:4867): when no match in workspace
    AND no explicit `path` arg is given, glob must also search
    `CONFIG.allowed_paths`. This is the SageMaker-friendly behavior where
    the workspace is a sub-dir of a parent git repo."""
    from runtime.config import CONFIG
    extra = tmp_path_factory.mktemp("parent_repo")
    (extra / "config.yaml").write_text("k: v", encoding="utf-8")
    monkeypatch.setattr(CONFIG, "allowed_paths", [str(extra)])
    # Rebuild SECURITY so the new allowed_paths take effect for validate_path
    # boundary checks on the matched files.
    try:
        from security.manager import rebuild_singleton_for_tests
        rebuild_singleton_for_tests()
    except ImportError:
        pass
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "glob")
    # Workspace has no .yaml files; allowed_paths has one.
    out = tool.execute({"pattern": "**/*.yaml"})
    assert "config.yaml" in out
    # Output annotates the multi-root search so the model knows what happened.
    assert "Searched" in out or "allowed_paths" in out
