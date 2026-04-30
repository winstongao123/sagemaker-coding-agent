"""Phase 02 unit tests: ToolDef Protocol + tools/registry.py.

Locks the contract for ADR-007 (`ToolDef` Protocol replaces v4's 4-tuple
`TOOLS` dict) and ADR-008 (registry exposes get_tools / assemble_tool_pool /
apply_tool_search_deferral stub + plan-mode subset).

Tests use `_reset_registry_for_tests()` between cases so registration
ordering doesn't leak across tests. The Phase 2 registry ships empty —
real tools land in Phase 3-5.
"""
from __future__ import annotations

import os
import sys

# Make `tools` importable from this test (mirrors flat-zip ship layout).
_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


def _reset():
    from tools.registry import _reset_registry_for_tests
    _reset_registry_for_tests()


def _noop_execute(args, context=None):
    return {"ok": True, "args": args}


# ============================================================
# build_tool defaults (ADR-007 buildTool parity)
# ============================================================

def test_build_tool_defaults_match_runnable_tool_defaults():
    """build_tool defaults must mirror Runnable's TOOL_DEFAULTS:
    is_concurrency_safe=False, is_read_only=False, is_destructive=False,
    enabled=True. Fail-closed: a tool author who omits the flag gets the
    safer 'assume writes / not concurrency safe' default."""
    from tools import build_tool
    t = build_tool(
        name="dummy",
        description="dummy desc",
        input_schema={"type": "object", "properties": {}},
        execute=_noop_execute,
    )
    assert t.name == "dummy"
    assert t.aliases == ()
    assert t.search_hint == ""
    assert t.should_defer is False
    assert t.always_load is False
    assert t.is_read_only is False
    assert t.is_destructive is False
    assert t.is_concurrency_safe is False
    assert t.requires_approval is False
    assert t.enabled is True
    assert t.max_result_size_chars == 50_000


def test_build_tool_overrides_apply():
    from tools import build_tool
    t = build_tool(
        name="grep",
        description="search files",
        input_schema={"type": "object", "properties": {"pattern": {"type": "string"}}},
        execute=_noop_execute,
        is_read_only=True,
        is_concurrency_safe=True,
        search_hint="search file contents regex",
        should_defer=True,
    )
    assert t.is_read_only is True
    assert t.is_concurrency_safe is True
    assert t.search_hint == "search file contents regex"
    assert t.should_defer is True


# ============================================================
# Registration + lookup
# ============================================================

def test_phase_2_registry_starts_empty():
    """Phase 2 registry contains no tools — the file-per-tool modules
    haven't landed yet (Phase 3-5). get_tools() must return [] cleanly."""
    _reset()
    from tools import get_tools, all_registered
    assert get_tools() == []
    assert all_registered() == []


def test_register_then_lookup():
    _reset()
    from tools import build_tool, register, get_tools, find_tool_by_name
    t = register(build_tool("read_file", "read", {"type": "object"}, _noop_execute, is_read_only=True))
    assert get_tools() == [t]
    assert find_tool_by_name(get_tools(), "read_file") is t
    assert find_tool_by_name(get_tools(), "missing") is None


def test_register_duplicate_name_raises():
    """v4 had a silent-override bug where two skills both registered
    'verify' and the second won. Registry must reject duplicates."""
    _reset()
    from tools import build_tool, register
    register(build_tool("verify", "first", {"type": "object"}, _noop_execute))
    try:
        register(build_tool("verify", "second", {"type": "object"}, _noop_execute))
    except ValueError as e:
        assert "already registered" in str(e)
        return
    raise AssertionError("expected ValueError on duplicate registration")


def test_unregister_removes_tool():
    _reset()
    from tools import build_tool, register, unregister, get_tools
    register(build_tool("a", "a", {"type": "object"}, _noop_execute))
    register(build_tool("b", "b", {"type": "object"}, _noop_execute))
    assert unregister("a") is True
    assert [t.name for t in get_tools()] == ["b"]
    assert unregister("missing") is False


def test_alias_lookup_matches_runnable_toolMatchesName():
    _reset()
    from tools import build_tool, register, find_tool_by_name, tool_matches_name, get_tools
    t = register(build_tool(
        "edit_file", "edit", {"type": "object"}, _noop_execute,
        aliases=("FileEditTool", "edit"),  # Runnable old name + short alias
    ))
    assert tool_matches_name(t, "edit_file")
    assert tool_matches_name(t, "FileEditTool")
    assert tool_matches_name(t, "edit")
    assert not tool_matches_name(t, "unrelated")
    assert find_tool_by_name(get_tools(), "FileEditTool") is t


# ============================================================
# Filtering: enabled / deny rules / plan mode
# ============================================================

def test_disabled_tools_are_hidden():
    _reset()
    from tools import build_tool, register, get_tools
    register(build_tool("on", "x", {"type": "object"}, _noop_execute))
    register(build_tool("off", "x", {"type": "object"}, _noop_execute, enabled=False))
    names = [t.name for t in get_tools()]
    assert "on" in names
    assert "off" not in names


def test_deny_rules_filter_by_name():
    _reset()
    from tools import build_tool, register, get_tools
    register(build_tool("a", "x", {"type": "object"}, _noop_execute))
    register(build_tool("b", "x", {"type": "object"}, _noop_execute))
    register(build_tool("c", "x", {"type": "object"}, _noop_execute))
    names = [t.name for t in get_tools(deny_rules={"b"})]
    assert names == ["a", "c"]


def test_deny_rules_filter_by_alias():
    """Runnable's filterToolsByDenyRules uses the same matcher as the
    runtime permission check — alias matches must also be filtered."""
    _reset()
    from tools import build_tool, register, get_tools
    register(build_tool(
        "edit_file", "edit", {"type": "object"}, _noop_execute,
        aliases=("FileEditTool",),
    ))
    register(build_tool("read_file", "read", {"type": "object"}, _noop_execute))
    # Deny by alias should kick edit_file out
    names = [t.name for t in get_tools(deny_rules={"FileEditTool"})]
    assert names == ["read_file"]


def test_plan_mode_filters_to_v4_allowlist():
    """v4 PLAN_MODE_ALLOWED_TOOLS parity:
    {read_file, glob, grep, list_dir, semantic_search, todo_write,
     todo_read, view_image, skill, web_fetch, ask_user}.
    Mutating tools (write_file, edit_file, bash, python_exec, task) are
    filtered out in plan mode."""
    _reset()
    from tools import build_tool, register, get_tools, PLAN_MODE_ALLOWED_TOOLS
    # Register a mix of read-only and mutating tools by name
    for name in ["read_file", "grep", "list_dir", "write_file", "edit_file", "bash", "python_exec"]:
        register(build_tool(name, "x", {"type": "object"}, _noop_execute))
    plan = {t.name for t in get_tools(plan_mode=True)}
    # Only the names that are in the allowlist AND were registered survive
    expected = {"read_file", "grep", "list_dir"}  # the registered ∩ allowlist
    assert plan == expected
    # Sanity check: the allowlist constant exposes the v4 set
    assert "read_file" in PLAN_MODE_ALLOWED_TOOLS
    assert "write_file" not in PLAN_MODE_ALLOWED_TOOLS


def test_plan_mode_and_deny_rules_compose():
    """Deny rules + plan mode together: deny applies first, plan-mode
    subset applies second. Order must not matter for correctness — both
    filters are intersections."""
    _reset()
    from tools import build_tool, register, get_tools
    for name in ["read_file", "grep", "list_dir"]:
        register(build_tool(name, "x", {"type": "object"}, _noop_execute))
    out = {t.name for t in get_tools(plan_mode=True, deny_rules={"grep"})}
    assert out == {"read_file", "list_dir"}


# ============================================================
# Cache-stable ordering (Runnable assembleToolPool invariant)
# ============================================================

def test_assemble_tool_pool_sorts_alphabetically_for_cache_stability():
    """Runnable's assembleToolPool sorts each partition alphabetically and
    keeps built-ins as a contiguous prefix. The server-side prompt-cache
    breakpoint sits after the last built-in; any interleaving invalidates
    the cache for every downstream tool. Test asserts the alphabetical
    ordering invariant inside each partition."""
    _reset()
    from tools import build_tool, register, assemble_tool_pool
    # Register in non-alphabetical insertion order
    for name in ["zeta", "alpha", "mike"]:
        register(build_tool(name, "x", {"type": "object"}, _noop_execute))
    mcp_tools = [
        build_tool("mcp__server__zoo", "x", {"type": "object"}, _noop_execute),
        build_tool("mcp__server__apple", "x", {"type": "object"}, _noop_execute),
    ]
    pool = assemble_tool_pool(mcp_tools=mcp_tools)
    names = [t.name for t in pool]
    # Built-ins alphabetical first, then MCP alphabetical
    assert names == [
        "alpha", "mike", "zeta",
        "mcp__server__apple", "mcp__server__zoo",
    ]


def test_assemble_tool_pool_dedup_built_in_wins():
    """When a built-in and an MCP tool collide on name, built-in wins
    (insertion order is preserved by the dedup pass — Runnable
    `uniqBy([...builtIn, ...mcp], 'name')` semantics)."""
    _reset()
    from tools import build_tool, register, assemble_tool_pool
    register(build_tool("dup", "built-in", {"type": "object"}, _noop_execute))
    mcp_tool = build_tool("dup", "mcp", {"type": "object"}, _noop_execute)
    pool = assemble_tool_pool(mcp_tools=[mcp_tool])
    assert len(pool) == 1
    assert pool[0].description == "built-in"


# ============================================================
# MCP server-prefix deny rules (Codex Phase-02 review finding 2)
# Runnable parity: `permissions.ts:getDenyRuleForTool` supports
# server-level rules like `mcp__server` and `mcp__server__*` that strip
# every tool from a given MCP server.
# ============================================================

def test_deny_rule_mcp_server_blanket_strips_all_tools_from_that_server():
    _reset()
    from tools import build_tool, register, get_tools
    register(build_tool("mcp__github__list_prs", "x", {"type": "object"}, _noop_execute))
    register(build_tool("mcp__github__create_pr", "x", {"type": "object"}, _noop_execute))
    register(build_tool("mcp__slack__send", "x", {"type": "object"}, _noop_execute))
    register(build_tool("read_file", "x", {"type": "object"}, _noop_execute))

    # Blanket-deny the entire `github` MCP server.
    names = {t.name for t in get_tools(deny_rules={"mcp__github"})}
    assert names == {"mcp__slack__send", "read_file"}


def test_deny_rule_mcp_server_wildcard_form_matches_too():
    _reset()
    from tools import build_tool, register, get_tools
    register(build_tool("mcp__github__list_prs", "x", {"type": "object"}, _noop_execute))
    register(build_tool("mcp__slack__send", "x", {"type": "object"}, _noop_execute))

    # Wildcard form (Runnable supports both `mcp__server` and `mcp__server__*`).
    names = {t.name for t in get_tools(deny_rules={"mcp__github__*"})}
    assert names == {"mcp__slack__send"}


def test_deny_rule_does_not_falsely_match_partial_server_name():
    """`mcp__git` must NOT deny `mcp__github__*` — the matcher splits on
    `__` and matches only the full server segment, not a prefix."""
    _reset()
    from tools import build_tool, register, get_tools
    register(build_tool("mcp__github__list", "x", {"type": "object"}, _noop_execute))
    register(build_tool("mcp__git__status", "x", {"type": "object"}, _noop_execute))

    names = {t.name for t in get_tools(deny_rules={"mcp__git"})}
    # Only the `git` server is denied; `github` is a different server name.
    assert names == {"mcp__github__list"}


# ============================================================
# Plan mode + MCP tools (Codex Phase-02 review finding 1)
# v4 parity (sagemaker_agent.py:9390): plan mode is a hard allowlist by
# name — MCP/new tools that don't appear in PLAN_MODE_ALLOWED_TOOLS get
# filtered out. v5 enforces this at registry assembly so the model never
# sees the disallowed tool schema in the initial prompt.
# ============================================================

def test_plan_mode_filters_mcp_tools_too():
    _reset()
    from tools import build_tool, register, assemble_tool_pool
    register(build_tool("read_file", "x", {"type": "object"}, _noop_execute))
    register(build_tool("write_file", "x", {"type": "object"}, _noop_execute))

    mcp_tools = [
        build_tool("mcp__github__list_prs", "x", {"type": "object"}, _noop_execute),
        build_tool("mcp__github__create_pr", "x", {"type": "object"}, _noop_execute),
    ]
    # Plan mode: MCP tools are not in PLAN_MODE_ALLOWED_TOOLS, so they
    # MUST be stripped from the assembled pool. Only the read-only
    # built-in `read_file` survives.
    pool = assemble_tool_pool(plan_mode=True, mcp_tools=mcp_tools)
    assert [t.name for t in pool] == ["read_file"]


def test_plan_mode_allows_mcp_tool_only_if_name_in_allowlist():
    """Edge case: if an MCP tool happens to share a name in
    PLAN_MODE_ALLOWED_TOOLS (unlikely but defensible), it's allowed.
    This guards against hardcoding 'no MCP in plan mode' — the actual
    v4 rule is purely allowlist-by-name."""
    _reset()
    from tools import build_tool, assemble_tool_pool
    # An MCP tool literally named `web_fetch` (which IS in the allowlist).
    # Real MCP tools never have this name (they're prefixed mcp__server__),
    # but the test exists to lock the rule shape.
    mcp_tools = [build_tool("web_fetch", "x", {"type": "object"}, _noop_execute)]
    pool = assemble_tool_pool(plan_mode=True, mcp_tools=mcp_tools)
    assert [t.name for t in pool] == ["web_fetch"]


# ============================================================
# Deferred-loading stub (Phase 7 fills in)
# ============================================================

def test_apply_tool_search_deferral_disabled_returns_unchanged():
    """Phase 2 stub: when enabled=False, returns (tools, None) unchanged."""
    _reset()
    from tools import build_tool, register, get_tools, apply_tool_search_deferral
    register(build_tool("a", "x", {"type": "object"}, _noop_execute))
    register(build_tool("b", "x", {"type": "object"}, _noop_execute, should_defer=True))
    tools = get_tools()
    visible, search_tool = apply_tool_search_deferral(tools, enabled=False)
    assert [t.name for t in visible] == ["a", "b"]
    assert search_tool is None


def test_apply_tool_search_deferral_enabled_phase_2_stub_is_safe():
    """Phase 2 stub: even when enabled=True, the stub must not break —
    returns (tools, None). Phase 7 will replace this with real deferred-
    loading logic (saves ≥3000 tokens/turn vs Phase 6 baseline)."""
    _reset()
    from tools import build_tool, register, get_tools, apply_tool_search_deferral
    register(build_tool("a", "x", {"type": "object"}, _noop_execute))
    register(build_tool("b", "x", {"type": "object"}, _noop_execute, should_defer=True))
    tools = get_tools()
    visible, search_tool = apply_tool_search_deferral(tools, enabled=True)
    # Phase 2 stub keeps everything visible — Phase 7 will defer `b`.
    assert [t.name for t in visible] == ["a", "b"]
    assert search_tool is None  # Phase 7 will return the ToolSearchTool here


# ============================================================
# Protocol membership (ToolDef Protocol per ADR-007)
# ============================================================

def test_tool_record_satisfies_tooldef_protocol():
    """A ToolRecord built via build_tool must satisfy the ToolDef
    Protocol at runtime (typing.runtime_checkable). This proves the
    Protocol shape is realisable without forcing every field to be a
    method (Runnable's Tool interface is method-heavy because of TS;
    Python Protocols can mix attrs + methods)."""
    from tools import build_tool, ToolDef
    t = build_tool("x", "y", {"type": "object"}, _noop_execute)
    assert isinstance(t, ToolDef)


# ============================================================
# Standalone runner
# ============================================================

if __name__ == "__main__":
    tests = [
        ("build_tool_defaults_match_runnable_tool_defaults", test_build_tool_defaults_match_runnable_tool_defaults),
        ("build_tool_overrides_apply",                       test_build_tool_overrides_apply),
        ("phase_2_registry_starts_empty",                    test_phase_2_registry_starts_empty),
        ("register_then_lookup",                             test_register_then_lookup),
        ("register_duplicate_name_raises",                   test_register_duplicate_name_raises),
        ("unregister_removes_tool",                          test_unregister_removes_tool),
        ("alias_lookup_matches_runnable_toolMatchesName",    test_alias_lookup_matches_runnable_toolMatchesName),
        ("disabled_tools_are_hidden",                        test_disabled_tools_are_hidden),
        ("deny_rules_filter_by_name",                        test_deny_rules_filter_by_name),
        ("deny_rules_filter_by_alias",                       test_deny_rules_filter_by_alias),
        ("plan_mode_filters_to_v4_allowlist",                test_plan_mode_filters_to_v4_allowlist),
        ("plan_mode_and_deny_rules_compose",                 test_plan_mode_and_deny_rules_compose),
        ("assemble_tool_pool_sorts_alphabetically",          test_assemble_tool_pool_sorts_alphabetically_for_cache_stability),
        ("assemble_tool_pool_dedup_built_in_wins",           test_assemble_tool_pool_dedup_built_in_wins),
        ("apply_tool_search_deferral_disabled",              test_apply_tool_search_deferral_disabled_returns_unchanged),
        ("apply_tool_search_deferral_enabled_stub",          test_apply_tool_search_deferral_enabled_phase_2_stub_is_safe),
        ("tool_record_satisfies_tooldef_protocol",           test_tool_record_satisfies_tooldef_protocol),
        ("deny_rule_mcp_server_blanket",                     test_deny_rule_mcp_server_blanket_strips_all_tools_from_that_server),
        ("deny_rule_mcp_server_wildcard",                    test_deny_rule_mcp_server_wildcard_form_matches_too),
        ("deny_rule_no_partial_match",                       test_deny_rule_does_not_falsely_match_partial_server_name),
        ("plan_mode_filters_mcp_tools_too",                  test_plan_mode_filters_mcp_tools_too),
        ("plan_mode_allows_mcp_only_if_name_allowlisted",    test_plan_mode_allows_mcp_tool_only_if_name_in_allowlist),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            print(f"FAIL  {name}:\n  {e}")
            failed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} Phase 02 registry tests passed")
    sys.exit(1 if failed else 0)
