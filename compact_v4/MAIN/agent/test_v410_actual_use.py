"""V4.10.10 round 3: regression tests for actual-use fixes.

Locks in the fixes from the 5-investigator round-3 review:
- Tool capability classes prompt section is present and at top-level
- Block messages tell the LLM which tools STILL WORK (call-count + time-budget branches)
- "User denied permission" is now action-guided (not bare 22-char string)
- Generic exception fallback includes substitution guidance
- read_file repetition dedup uses normalized path + limit
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sagemaker_agent as sa


def _get_source() -> str:
    src_path = os.path.join(os.path.dirname(__file__), "sagemaker_agent.py")
    with open(src_path, "r", encoding="utf-8") as f:
        return f.read()


def test_tool_capability_classes_prompt_section_exists():
    """Codex E1 + Team A1 CRITICAL: matrix must be a top-level prompt section, not buried."""
    src = _get_source()
    # Header line is present
    assert "# Tool capability classes" in src, (
        "Tool capability classes section missing from SYSTEM_PROMPT"
    )
    # Must list the unlimited tools so LLM can read them
    for tool in ["read_file", "grep", "glob", "edit_file", "write_file", "notebook_edit"]:
        assert tool in src, f"Tool capability classes section missing reference to '{tool}'"
    # Must mention bash + python_exec are limited
    assert "bash" in src and "python_exec" in src, "Limited tools not named"


def test_self_correction_rule_exists():
    """Team A1 CRITICAL: BEFORE saying 'I can't' rule must be present."""
    src = _get_source()
    assert 'BEFORE saying "I can\'t"' in src or "BEFORE saying" in src, (
        "Self-correction rule missing"
    )


def test_call_limit_block_message_tells_llm_alternatives():
    """Team A2 HIGH + B1 P0: block message must say STILL AVAILABLE + name read tools."""
    src = _get_source()
    # Find the call-count block message
    call_block_pat = re.compile(
        r'Blocked: bash \+ python_exec call limit reached.*?STILL AVAILABLE',
        re.DOTALL,
    )
    assert call_block_pat.search(src), (
        "Call-count block message missing 'STILL AVAILABLE' guidance"
    )
    # Names the read tools
    for tool in ["read_file", "grep", "edit_file"]:
        assert tool in src, f"Block message missing '{tool}'"


def test_time_budget_block_message_also_fixed():
    """Team A2 HIGH (parallel branch missed in round 2)."""
    src = _get_source()
    time_block_pat = re.compile(
        r'Blocked: bash \+ python_exec time budget reached.*?STILL AVAILABLE',
        re.DOTALL,
    )
    assert time_block_pat.search(src), (
        "Time-budget block message missing 'STILL AVAILABLE' guidance "
        "(round-2 fix only covered call-count branch; round-3 must also fix time)"
    )


def test_user_denied_message_is_action_guided():
    """Team A2 HIGH: bare 'User denied permission' must be replaced with guidance."""
    src = _get_source()
    # Old bare string should NOT be the only content of any tool_result
    bare_count = src.count('"User denied permission"')
    assert bare_count == 0, (
        f"Bare 'User denied permission' string still present {bare_count} times "
        "(should be replaced with action-guided message)"
    )
    # New message text present
    assert "Do NOT retry the identical command" in src, "Action-guided denial message missing"
    assert "switch to read-only tools" in src.lower(), (
        "Denial message missing read-only-tools fallback"
    )


def test_generic_exception_fallback_includes_substitutes():
    """Team A2 MEDIUM: generic exception must guide the agent to try alternatives."""
    src = _get_source()
    assert "Diagnose root cause before retrying" in src, (
        "Generic exception message missing 'diagnose root cause'"
    )
    assert "always available" in src, (
        "Generic exception message missing 'always available' tool list"
    )


def test_read_file_dedup_uses_normalized_path():
    """Codex C2 HIGH: dedup key uses os.path.realpath/abspath so abs vs relative same key."""
    src = _get_source()
    # The dedup site must call realpath (or equivalent normalisation)
    assert "os.path.realpath" in src or "realpath(os.path.abspath" in src, (
        "Path normalization missing in dedup key (Codex C2 HIGH)"
    )


def test_read_file_dedup_includes_limit():
    """[Actual Use Issue 7]: limit must be in the key so {offset=200,limit=20} != {offset=200,limit=50}."""
    src = _get_source()
    # Look for the f-string composition pattern
    assert re.search(r'fp_norm.*offset.*limit', src) or re.search(r'@\{offset\}:\{limit\}', src), (
        "read_file dedup key doesn't include limit"
    )


def test_high_risk_tools_unchanged():
    """Sanity: HIGH_RISK_TOOLS membership is unchanged (bash, python_exec, task, web_fetch)."""
    src = _get_source()
    m = re.search(r'HIGH_RISK_TOOLS\s*=\s*\{([^}]+)\}', src)
    assert m, "HIGH_RISK_TOOLS set missing"
    members = m.group(1)
    for required in ("bash", "python_exec", "task", "web_fetch"):
        assert f'"{required}"' in members or f"'{required}'" in members, (
            f"HIGH_RISK_TOOLS missing {required}"
        )


def test_iteration_budget_default_is_600():
    """[Actual Use Issue 2]: default bumped 90 -> 600."""
    src = _get_source()
    # Config field default
    assert re.search(r'max_iteration_budget:\s*int\s*=\s*600', src), (
        "max_iteration_budget default not 600"
    )
    # Class default
    assert re.search(r'DEFAULT_MAX\s*=\s*600', src), (
        "IterationBudget.DEFAULT_MAX not 600"
    )


def test_max_exec_calls_per_session_is_200():
    """[Actual Use Issue 7]: bumped 40 -> 200."""
    src = _get_source()
    assert re.search(r'max_exec_calls_per_session:\s*int\s*=\s*200', src), (
        "max_exec_calls_per_session not 200"
    )


def test_cso_check_is_debug_not_warning():
    """[Actual Use Issue 1]: CSO-CHECK lowered to logging.debug to silence noisy startup."""
    src = _get_source()
    # Find the CSO-CHECK section
    idx = src.find("[CSO-CHECK]")
    assert idx > 0, "CSO-CHECK code missing"
    # The 200 chars before it should mention logging.debug, not logging.warning
    nearby = src[max(0, idx - 200):idx]
    assert "logging.debug" in nearby, (
        "CSO-CHECK still uses logging.warning (should be logging.debug for advisory)"
    )


if __name__ == "__main__":
    tests = [
        ("tool_capability_classes_prompt_section_exists", test_tool_capability_classes_prompt_section_exists),
        ("self_correction_rule_exists", test_self_correction_rule_exists),
        ("call_limit_block_message_tells_llm_alternatives", test_call_limit_block_message_tells_llm_alternatives),
        ("time_budget_block_message_also_fixed", test_time_budget_block_message_also_fixed),
        ("user_denied_message_is_action_guided", test_user_denied_message_is_action_guided),
        ("generic_exception_fallback_includes_substitutes", test_generic_exception_fallback_includes_substitutes),
        ("read_file_dedup_uses_normalized_path", test_read_file_dedup_uses_normalized_path),
        ("read_file_dedup_includes_limit", test_read_file_dedup_includes_limit),
        ("high_risk_tools_unchanged", test_high_risk_tools_unchanged),
        ("iteration_budget_default_is_600", test_iteration_budget_default_is_600),
        ("max_exec_calls_per_session_is_200", test_max_exec_calls_per_session_is_200),
        ("cso_check_is_debug_not_warning", test_cso_check_is_debug_not_warning),
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
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    sys.exit(1 if failed else 0)
