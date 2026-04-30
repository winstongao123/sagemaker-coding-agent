"""Phase 12 — Critical parity scenarios (V5_PLAN.md §Phase 12, ADR-018).

Per V5_PLAN.md success metric #1 + risk #8: a critical-scenario suite that
MUST pass 100% before v5 ships. Each scenario encodes "this is what v4
does for this input"; v5 must match.

v4 is frozen at compact_v4/MAIN/agent/sagemaker_agent.py. Phase 12 does
NOT execute v4 directly — the v4-expected behavior is encoded inline as
assertion targets, with file:line citations.

15 critical scenarios:
  01. SecurityManager denies `rm -rf /`
  02. SecurityManager denies banned Python imports
  03. plan-mode dispatch gate blocks edit_file
  04. plan-mode dispatch gate blocks always_load mutating tool
  05. RetryPolicy.should_retry semantics for backoff/no_retry
  06. ErrorClassifier categorizes ValidationException/Throttling/etc
  07. static prompt ≤ 2500 tokens AND tool_classes at slot 2 (PS Issue #7)
  08. cache boundary marker present in assembled prompt
  09. Phase 7 deferred-loading round-trip (tool_search → next-turn promotion)
  10. Sub-agent shares parent IterationBudget (Phase 9 contract)
  11. SkillManager auto-trigger default-OFF (v4.9.6 contract)
  12. 10 v4 production skills load
  13. context-overflow exits cleanly with stop_reason="context_overflow"
  14. Tool exception trapped → tool_result with is_error=True
  15. PS Issue #2 (visible IterationBudget) + PS Issue #4 (visible thinking)
      both render via widgets.

ALL 15 MUST PASS before Phase 13 (cutover) tag is created.
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

import pytest

_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# Shared fixtures
# ============================================================

@pytest.fixture(autouse=True)
def fresh_registry():
    from tools.registry import _reset_registry_for_tests
    from tools import bootstrap_built_ins
    from tools import skill as skill_mod
    skill_mod._SINGLETON = None
    _reset_registry_for_tests()
    bootstrap_built_ins()
    yield
    skill_mod._SINGLETON = None


class _ScriptedClient:
    def __init__(self, script):
        self.script = list(script)
        self.calls: List[Dict[str, Any]] = []

    def chat(self, messages, system, tools, max_tokens, temperature,
             thinking_enabled, thinking_budget):
        from runtime.bedrock_client import Response, ToolCall
        self.calls.append({"messages": list(messages), "tools": list(tools or [])})
        if not self.script:
            return Response(text="(end)", tool_calls=[], stop_reason="end_turn")
        kind, *rest = self.script.pop(0)
        if kind == "text":
            return Response(text=rest[0], tool_calls=[], stop_reason="end_turn")
        if kind == "tool":
            cid, name, args = rest
            return Response(text="", tool_calls=[ToolCall(cid, name, args)], stop_reason="tool_use")
        raise AssertionError(f"unknown script kind: {kind}")


# ============================================================
# 01 — Security: bash blocks rm -rf /
# v4 ref: sagemaker_agent.py SecurityManager.is_dangerous_command + DANGEROUS_PATTERNS
# ============================================================

def test_critical_01_security_denies_rm_rf():
    from tools import find_tool_by_name, all_registered
    bash = find_tool_by_name(all_registered(), "bash")
    out = bash.execute({"command": "rm -rf /"})
    text = out if isinstance(out, str) else str(out)
    low = text.lower()
    assert any(k in low for k in ("block", "denied", "danger")), (
        f"v4 SecurityManager denies rm -rf /; v5 output={text[:300]!r}"
    )


# ============================================================
# 02 — Security: python_exec blocks banned import
# v4 ref: dangerous_python.py BLOCKED_MODULES + closure sandbox
# ============================================================

def test_critical_02_security_denies_socket_import():
    from tools import find_tool_by_name, all_registered
    pe = find_tool_by_name(all_registered(), "python_exec")
    out = pe.execute({"code": "import socket"})
    text = out if isinstance(out, str) else str(out)
    low = text.lower()
    assert (
        ("import" in low and "block" in low)
        or "not allowed" in low
        or "denied" in low
        or "DANGEROUS" in text.upper()
    ), f"v4 closure sandbox blocks socket import; v5 output={text[:300]!r}"


# ============================================================
# 03 — Plan-mode dispatch gate blocks mutating edit_file
# v4 ref: sagemaker_agent.py:6905 PLAN_MODE_ALLOWED_TOOLS
# ============================================================

def test_critical_03_plan_mode_blocks_edit_file():
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([
        ("tool", "p1", "edit_file", {"file_path": "x", "old_string": "a", "new_string": "b"}),
        ("text", "blocked"),
    ])
    eng = QueryEngine(client=client, max_turns=3)
    result = eng.run("edit", system_prompt="sys", tools=all_registered(), plan_mode=True)
    tr = result.messages[2]["content"][0]
    assert tr["is_error"] is True
    assert "plan mode" in tr["content"].lower() or "PLAN_MODE_ALLOWED_TOOLS" in tr["content"]


# ============================================================
# 04 — Plan-mode dispatch gate blocks `always_load` mutating tools
# Phase-08 Codex fix lock — strict allowlist, not is_read_only AND not always_load
# ============================================================

def test_critical_04_plan_mode_blocks_always_load_mutating_tool():
    from core import QueryEngine
    from tools.registry import build_tool, register, all_registered

    register(build_tool(
        name="critical_bypass",
        description="synthetic mutating + always_load",
        input_schema={"type": "object", "properties": {}},
        execute=lambda a, context=None: "should not run",
        is_read_only=False,
        always_load=True,
    ))
    client = _ScriptedClient([
        ("tool", "p1", "critical_bypass", {}),
        ("text", "ok"),
    ])
    eng = QueryEngine(client=client, max_turns=3)
    result = eng.run("try bypass", system_prompt="sys", tools=all_registered(), plan_mode=True)
    tr = result.messages[2]["content"][0]
    assert tr["is_error"] is True


# ============================================================
# 05 — RetryPolicy semantics
# v4 ref: sagemaker_agent.py RetryPolicy MAX_RETRIES=4, BACKOFF_RECOVERY={"backoff"}
# ============================================================

def test_critical_05_retry_policy_semantics():
    from core.retry import RetryPolicy
    assert RetryPolicy.MAX_RETRIES == 4
    assert RetryPolicy.should_retry(0, "backoff") is True
    assert RetryPolicy.should_retry(3, "backoff") is True
    assert RetryPolicy.should_retry(4, "backoff") is False
    assert RetryPolicy.should_retry(0, "no_retry") is False
    assert RetryPolicy.should_retry(0, "strip_cache_retry") is False


# ============================================================
# 06 — ErrorClassifier categorizes Bedrock errors
# v4 ref: sagemaker_agent.py ErrorClassifier.classify
# ============================================================

def test_critical_06_error_classifier_categories():
    from core.errors import BedrockErrorCategory, ErrorClassifier
    cat, _, _ = ErrorClassifier.classify(Exception("ThrottlingException: rate"))
    assert cat == BedrockErrorCategory.THROTTLE
    cat, _, _ = ErrorClassifier.classify(Exception("ServiceUnavailable 503"))
    assert cat == BedrockErrorCategory.SERVICE_UNAVAILABLE
    cat, _, _ = ErrorClassifier.classify(Exception("ValidationException: prompt is too long"))
    assert cat == BedrockErrorCategory.CONTEXT_OVERFLOW
    cat, _, _ = ErrorClassifier.classify(Exception("AccessDenied: 403"))
    assert cat == BedrockErrorCategory.ACCESS_DENIED


# ============================================================
# 07 — Static prompt ≤ 2500 tokens + tool_classes at slot 2 (PS Issue #7)
# ============================================================

def test_critical_07_static_prompt_budget_and_tool_classes_slot_2():
    from prompt.sections import SECTION_ORDER, total_static_tokens
    assert total_static_tokens() <= 2500, f"static = {total_static_tokens()} tokens"
    assert SECTION_ORDER[1].name == "tool_classes", (
        f"PS Issue #7: tool_classes must be slot 2; got {SECTION_ORDER[1].name!r}"
    )


# ============================================================
# 08 — Cache boundary marker present in assembled prompt
# ============================================================

def test_critical_08_cache_boundary_marker_present():
    from prompt import build_system_prompt, CACHE_BOUNDARY
    p = build_system_prompt(ctx={})
    assert CACHE_BOUNDARY in p, "cache boundary marker MUST be in assembled prompt"


# ============================================================
# 09 — Phase 7 deferred-loading round-trip end-to-end
# ============================================================

def test_critical_09_phase7_round_trip():
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([
        ("tool", "c1", "tool_search", {"query": "select:view_image"}),
        ("tool", "c2", "view_image", {"file_path": "x.png"}),
        ("text", "Done."),
    ])
    eng = QueryEngine(client=client, max_turns=5)
    result = eng.run("look", system_prompt="sys", tools=all_registered())
    turn1_names = {t["name"] for t in client.calls[0]["tools"]}
    turn2_names = {t["name"] for t in client.calls[1]["tools"]}
    assert "view_image" not in turn1_names
    assert "view_image" in turn2_names, "Phase 7 wiring contract violated"
    assert result.stop_reason == "end_turn"


# ============================================================
# 10 — Sub-agent shares parent IterationBudget (Phase 9 contract)
# ============================================================

def test_critical_10_subagent_shares_parent_budget():
    from agent import Agent
    from core import IterationBudget
    from runtime.bedrock_client import BedrockClient
    from subagent.spawn import spawn_subagent

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    parent = Agent(client=client, budget=IterationBudget(max_iterations=20))
    used_before = parent.budget.used()
    result = spawn_subagent(
        parent_engine=parent._engine, prompt="hi", agent_type="general",
    )
    used_after = parent.budget.used()
    # The sub-agent shared the budget — parent's used() reflects child consumption.
    assert used_after > used_before, "shared budget contract violated"


# ============================================================
# 11 — SkillManager auto-trigger default-OFF (v4.9.6 contract)
# ============================================================

def test_critical_11_skill_auto_trigger_default_off():
    from skills.manager import SkillManager
    skills_root = os.path.join(_AGENT_ROOT, "skills")
    sm = SkillManager(workspace=_AGENT_ROOT, skills_dir=skills_root, enable_auto_trigger=False)
    sm.discover()
    # Default-OFF: even if user_message contains a trigger word, no skills suggested.
    relevant = sm.discover_relevant("/verify the build")
    assert relevant == [], "v4.9.6 default-OFF: auto_trigger must return [] when global gate=False"


# ============================================================
# 12 — 10 v4 production skills load
# ============================================================

def test_critical_12_ten_production_skills_load():
    from skills.manager import SkillManager
    PRODUCTION = {
        "batch", "clara", "design", "html", "reflexion",
        "report", "review", "security-review", "simplify", "verify",
    }
    sm = SkillManager(
        workspace=_AGENT_ROOT,
        skills_dir=os.path.join(_AGENT_ROOT, "skills"),
    )
    sm.discover()
    discovered = set(sm._cache.keys())
    alias_map = {"clara-review": "clara", "code-review": "review"}
    aliases = set(discovered) | {alias_map[n] for n in discovered if n in alias_map}
    missing = PRODUCTION - aliases
    assert not missing, f"missing v4 production skills: {missing}"


# ============================================================
# 13 — Context-overflow exits cleanly
# ============================================================

def test_critical_13_context_overflow_clean_exit():
    from core import QueryEngine
    from tools import all_registered

    class _OverflowClient:
        def chat(self, **_kw):
            raise Exception("ValidationException: prompt is too long")

    eng = QueryEngine(client=_OverflowClient(), max_turns=3)
    result = eng.run("hi", system_prompt="sys", tools=all_registered())
    assert result.stop_reason == "context_overflow"
    assert "context_overflow" in (result.error or "")


# ============================================================
# 14 — Tool exception trapped → tool_result is_error=True
# ============================================================

def test_critical_14_tool_exception_trapped():
    from core import QueryEngine
    from tools.registry import build_tool, register, all_registered

    def _boom(args, context=None):
        raise RuntimeError("kaboom")

    register(build_tool(
        name="critical_boom", description="raises",
        input_schema={"type": "object", "properties": {}},
        execute=_boom, is_read_only=True,
    ))
    client = _ScriptedClient([
        ("tool", "c1", "critical_boom", {}),
        ("text", "recovered"),
    ])
    eng = QueryEngine(client=client, max_turns=3)
    result = eng.run("call boom", system_prompt="sys", tools=all_registered())
    tr = result.messages[2]["content"][0]
    assert tr["is_error"] is True
    assert "kaboom" in tr["content"]


# ============================================================
# 15 — PS Issue #2 (visible budget) + PS Issue #4 (visible thinking)
# ============================================================

def test_critical_15_ps_issues_2_and_4_visible_via_widgets():
    from agent import Agent
    from core import IterationBudget
    from runtime.bedrock_client import BedrockClient
    from ui.widgets import IterationBudgetWidget, ThinkingBudgetWidget

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    a = Agent(client=client, budget=IterationBudget(max_iterations=10),
              thinking_enabled=True, thinking_budget=8192)
    bw = IterationBudgetWidget(budget=a.budget)
    tw = ThinkingBudgetWidget(agent=a)
    # PS #2 — html visibly shows used/total
    assert "0/10" in bw.render_html()
    a.budget.consume(); a.budget.consume()
    assert "2/10" in bw.render_html()
    # PS #4 — html visibly shows thinking ON + budget
    th_html = tw.render_html()
    assert "ON" in th_html
    assert "8192" in th_html
