"""Phase 07 unit tests: tools/tool_search.py + apply_tool_search_deferral.

Locks the contract for ADR-013: deferred-loading pattern from Runnable's
ToolSearchTool. Three query modes (select / required-term / keyword),
`<functions>` wire format, deferred-set partition logic.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# Registration + flags
# ============================================================

def test_tool_search_registered():
    from tools import find_tool_by_name, all_registered
    t = find_tool_by_name(all_registered(), "tool_search")
    assert t is not None


def test_tool_search_flags_always_load():
    """tool_search MUST have always_load=True so it's never deferred itself
    (the model needs it to load anything else)."""
    from tools import find_tool_by_name, all_registered
    t = find_tool_by_name(all_registered(), "tool_search")
    assert t is not None
    assert t.always_load is True
    assert t.should_defer is False
    assert t.is_read_only is True
    assert t.requires_approval is False


# ============================================================
# is_deferred_tool
# ============================================================

def test_is_deferred_for_marked_tools():
    """Phase 7 marks view_image / list_dir / notebook_edit as should_defer=True."""
    from tools.tool_search import is_deferred_tool
    assert is_deferred_tool("view_image") is True
    assert is_deferred_tool("list_dir") is True
    assert is_deferred_tool("notebook_edit") is True


def test_is_deferred_false_for_high_frequency_tools():
    from tools.tool_search import is_deferred_tool
    assert is_deferred_tool("read_file") is False
    assert is_deferred_tool("grep") is False
    assert is_deferred_tool("edit_file") is False
    assert is_deferred_tool("bash") is False
    assert is_deferred_tool("python_exec") is False


def test_is_deferred_false_for_tool_search_itself():
    from tools.tool_search import is_deferred_tool
    assert is_deferred_tool("tool_search") is False


def test_is_deferred_false_for_unknown_tool():
    from tools.tool_search import is_deferred_tool
    assert is_deferred_tool("nope_not_a_tool") is False


# ============================================================
# apply_tool_search_deferral — integration with registry
# ============================================================

def test_deferral_disabled_returns_unchanged():
    """Codex Phase-07 review fix #1: signature is now (visible, deferred_names_list)."""
    from tools import all_registered, apply_tool_search_deferral
    tools = all_registered()
    visible, deferred_names = apply_tool_search_deferral(tools, enabled=False)
    assert deferred_names == []
    assert [t.name for t in visible] == [t.name for t in tools]


def test_deferral_enabled_removes_deferred_tools():
    """Codex fix #1: visible INCLUDES tool_search (no duplication); second
    return is the list of deferred tool NAMES (for system-reminder block)."""
    from tools import all_registered, apply_tool_search_deferral
    tools = all_registered()
    visible, deferred_names = apply_tool_search_deferral(tools, enabled=True)
    visible_names = {t.name for t in visible}
    # Deferred tools must NOT be in visible
    assert "view_image" not in visible_names
    assert "list_dir" not in visible_names
    assert "notebook_edit" not in visible_names
    # Always-loaded + non-deferred tools MUST be in visible
    assert "read_file" in visible_names
    assert "edit_file" in visible_names
    assert "bash" in visible_names
    # tool_search itself MUST be in visible (and ONLY in visible — no duplication)
    assert "tool_search" in visible_names
    # Deferred names returned for system-reminder
    assert "view_image" in deferred_names
    assert "list_dir" in deferred_names
    assert "notebook_edit" in deferred_names


def test_deferral_no_duplicate_tool_search():
    """Codex Phase-07 finding 1 lock: tool_search must appear EXACTLY ONCE
    in the assembled per-turn tools list. Phase 8 callers should not need to
    append it (the new return is List[str] of names, not the tool itself)."""
    from tools import all_registered, apply_tool_search_deferral
    tools = all_registered()
    visible, deferred_names = apply_tool_search_deferral(tools, enabled=True)
    tool_search_count = sum(1 for t in visible if t.name == "tool_search")
    assert tool_search_count == 1, (
        f"tool_search should appear exactly once in visible, got {tool_search_count}"
    )
    # The second return is a list of NAMES, not a ToolRecord
    assert isinstance(deferred_names, list)
    for n in deferred_names:
        assert isinstance(n, str)


def test_deferral_enabled_without_tool_search_logs_warning():
    """If the input list lacks tool_search, deferral must safely no-op
    + log a warning."""
    from tools import all_registered, apply_tool_search_deferral
    tools_without_search = [t for t in all_registered() if t.name != "tool_search"]
    visible, deferred_names = apply_tool_search_deferral(tools_without_search, enabled=True)
    # Signature: deferred_names is [] when fallback fires
    assert deferred_names == []
    assert len(visible) == len(tools_without_search)


# ============================================================
# Query modes — select:Name1,Name2
# ============================================================

def test_select_query_exact_match(workspace_safe_environ):
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": "select:view_image"})
    # Result format: <functions>{"description":..., "name":"view_image", ...}</functions>
    assert "<functions>" in out
    assert "</functions>" in out
    assert "view_image" in out


def test_select_query_multiple_names(workspace_safe_environ):
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": "select:view_image,list_dir"})
    assert "view_image" in out
    assert "list_dir" in out


def test_select_query_case_insensitive(workspace_safe_environ):
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": "select:VIEW_IMAGE"})
    assert "view_image" in out


def test_select_query_unknown_name_returns_no_matches(workspace_safe_environ):
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": "select:nope_not_a_real_tool"})
    # Empty match list — wire format still wraps in <functions>
    assert "<functions>" in out
    assert "(no matches)" in out


def test_select_query_only_returns_deferred_tools(workspace_safe_environ):
    """Asking for an always-loaded tool via select: should return nothing —
    the model already has the schema; loading again is a no-op anyway, but
    the tool_search contract is "fetch DEFERRED tools"."""
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": "select:read_file"})
    # read_file is NOT deferred → not in deferred_names → returned as no-match
    assert "(no matches)" in out


# ============================================================
# Query modes — keyword search
# ============================================================

def test_keyword_query_finds_image_tool(workspace_safe_environ):
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": "image visual"})
    # view_image is deferred; description mentions "visual analysis"
    assert "view_image" in out


def test_keyword_query_finds_notebook_tool(workspace_safe_environ):
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": "notebook jupyter"})
    assert "notebook_edit" in out


def test_keyword_query_max_results_cap(workspace_safe_environ):
    """max_results must cap the returned list."""
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": "tool", "max_results": 1})
    # Body should contain at most 1 function entry (plus boundary markers)
    function_lines = [
        line for line in out.split("\n")
        if line.startswith('{"description"')
    ]
    assert len(function_lines) <= 1


# ============================================================
# Query modes — +required term
# ============================================================

def test_required_term_query(workspace_safe_environ):
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    # `+image` requires "image" to be in the parsed name
    out = tool.execute({"query": "+image"})
    assert "view_image" in out
    # list_dir doesn't have "image" in name → must NOT be in result
    assert "list_dir" not in out


def test_required_term_no_matches_returns_empty(workspace_safe_environ):
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": "+xyzzy_nonexistent"})
    assert "(no matches)" in out


# ============================================================
# Wire format: <functions>...</functions>
# ============================================================

def test_functions_block_contains_valid_json(workspace_safe_environ):
    """Each line inside <functions>...</functions> must be valid JSON
    with description / name / parameters keys (Runnable wire format)."""
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": "select:view_image"})
    # Extract content between markers
    inner = out[out.index("<functions>") + len("<functions>"): out.index("</functions>")].strip()
    # First line should be a JSON object
    first_line = inner.split("\n")[0]
    parsed = json.loads(first_line)
    assert "description" in parsed
    assert "name" in parsed
    assert "parameters" in parsed
    assert parsed["name"] == "view_image"
    assert parsed["parameters"]["type"] == "object"


# ============================================================
# Token-saving measurement (V5_PLAN.md acceptance: ≥3000 tokens)
# ============================================================

def test_deferral_saves_tokens_per_turn():
    """Mechanism is the point — even if Phase 7's initial deferred set is
    small (3 tools), demonstrate that deferral DOES reduce per-turn schema
    cost. The full ≥3000-token target lands as Phases 9-10 add more tools."""
    from tools import all_registered, apply_tool_search_deferral
    from prompt.sections import estimate_tokens
    import json as _json

    full = all_registered()
    visible, ts = apply_tool_search_deferral(full, enabled=True)

    def schemas_token_cost(tools_list):
        return sum(
            estimate_tokens(t.description) + estimate_tokens(_json.dumps(t.input_schema))
            for t in tools_list
        )

    full_cost = schemas_token_cost(full)
    visible_cost = schemas_token_cost(visible)
    savings = full_cost - visible_cost
    # Even with only 3 deferred tools (Phase 7 initial pass), savings
    # should be measurable (≥100 tokens). The ≥3000-token target is for
    # Phase 13 final state, not Phase 7 alone.
    assert savings > 0, f"deferral should save tokens; got savings={savings}"
    assert savings >= 100, (
        f"savings {savings} too small; check view_image / list_dir / "
        f"notebook_edit are in the deferred set"
    )


# ============================================================
# Bad input handling
# ============================================================

def test_empty_query_returns_error():
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": ""})
    assert out.startswith("Error:")


def test_invalid_max_results():
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": "image", "max_results": "not_a_number"})
    assert out.startswith("Error:")


# ============================================================
# Codex Phase-07 review fix lock tests
# ============================================================

def test_bare_exact_name_fast_path(workspace_safe_environ):
    """Codex finding (PATTERN 014 fix): models from sub-agents / post-compaction
    sometimes use a bare tool name (e.g., `view_image`) instead of `select:view_image`.
    Runnable has a fast-path for this — v5 must too."""
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": "view_image"})
    assert "view_image" in out
    assert "<functions>" in out
    # Bare name with case mismatch: also case-insensitive
    out_upper = tool.execute({"query": "VIEW_IMAGE"})
    assert "view_image" in out_upper


def test_required_term_searches_description_too(workspace_safe_environ):
    """Codex finding 4 lock: +required must check name + description + search_hint,
    not just name. notebook_edit's description mentions 'Jupyter' so `+jupyter`
    should match it (its NAME doesn't contain 'jupyter')."""
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": "+jupyter"})
    # notebook_edit description mentions "Jupyter notebook"
    assert "notebook_edit" in out


def test_keyword_search_hits_description(workspace_safe_environ):
    """Keyword search across name + description + search_hint."""
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    # `analysis` appears in view_image description ("visual analysis")
    out = tool.execute({"query": "analysis"})
    assert "view_image" in out


def test_active_tools_context_filters_search(workspace_safe_environ):
    """Codex finding 2 lock: tool_search must search ONLY the per-turn pool.
    Pass a restricted active_tools list and verify deferred tools NOT in that
    list are excluded from results."""
    from tools import find_tool_by_name, all_registered
    tool = find_tool_by_name(all_registered(), "tool_search")
    # Restrict the pool to view_image + tool_search ONLY (drop list_dir + notebook_edit)
    full = all_registered()
    restricted = [t for t in full if t.name in ("tool_search", "view_image")]
    out = tool.execute(
        {"query": "select:view_image,list_dir,notebook_edit"},
        context={"active_tools": restricted},
    )
    # view_image is in the restricted pool → loadable
    assert "view_image" in out
    # list_dir + notebook_edit NOT in restricted pool → must NOT appear
    assert '"name": "list_dir"' not in out
    assert '"name": "notebook_edit"' not in out


def test_tool_search_discovered_names_extraction(workspace_safe_environ):
    """Phase-8 contract lock: tool_search_discovered_names parses the hidden
    marker out of a tool_result text. Phase 8 query_engine uses this to
    determine which tools to include in the next turn's API call."""
    from tools import find_tool_by_name, all_registered
    from tools.tool_search import tool_search_discovered_names
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": "select:view_image,list_dir"})
    discovered = tool_search_discovered_names(out)
    assert "view_image" in discovered
    assert "list_dir" in discovered


def test_tool_search_discovered_names_empty_on_no_matches(workspace_safe_environ):
    from tools import find_tool_by_name, all_registered
    from tools.tool_search import tool_search_discovered_names
    tool = find_tool_by_name(all_registered(), "tool_search")
    out = tool.execute({"query": "select:nonexistent_tool"})
    discovered = tool_search_discovered_names(out)
    assert discovered == []


def test_tool_search_discovered_names_handles_missing_marker():
    """Robust against tool_result text without the marker (e.g., earlier turns)."""
    from tools.tool_search import tool_search_discovered_names
    assert tool_search_discovered_names("just some unrelated text") == []
    assert tool_search_discovered_names("") == []


def test_plan_mode_via_active_tools_excludes_mutating_deferred(workspace_safe_environ):
    """Codex finding 2 (deny rules / plan mode): in plan mode, mutating tools
    are filtered out of active_tools by Phase-2 plan-mode-allowlist logic.
    tool_search must NOT expose them."""
    from tools import assemble_tool_pool
    from tools import find_tool_by_name, all_registered
    plan_mode_pool = assemble_tool_pool(plan_mode=True)
    tool = find_tool_by_name(all_registered(), "tool_search")
    # notebook_edit is mutating + deferred — in plan mode it's excluded from the pool
    out = tool.execute(
        {"query": "select:notebook_edit"},
        context={"active_tools": plan_mode_pool},
    )
    # notebook_edit should NOT be returned because it's not in the plan-mode pool
    assert '"name": "notebook_edit"' not in out


# ============================================================
# Fixture: ensure tool_search is registered (safe regardless of test order)
# ============================================================

@pytest.fixture(autouse=True)
def workspace_safe_environ():
    """Phase 2 registry tests call `_reset_registry_for_tests()` which
    clears the registry, then add their custom tools. After such a test
    suite runs, the v5 built-in tools (including tool_search) are gone
    OR replaced by test stubs. Always force-reset + re-bootstrap so
    Phase 7 tests start with a clean v5 built-in tool set."""
    from tools.registry import _reset_registry_for_tests
    from tools import bootstrap_built_ins
    _reset_registry_for_tests()
    bootstrap_built_ins()
    yield
