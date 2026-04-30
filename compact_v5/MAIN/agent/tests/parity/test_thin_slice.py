"""Phase 08.5 — Thin-slice parity gate (HARD BLOCKER before Phase 9).

Per V5_PLAN.md §Phase 8.5: 10 critical scenarios that span every prior phase.
10/10 must pass before Phase 9 (sub-agent + Task tool) is allowed to start.

The scenarios are not v4-vs-v5 parity (Phase 12 owns that). They are
**cross-phase integration smoke tests** that catch architectural drift
early — if any single phase regresses behavior the others depend on,
this gate fires before more code is layered on top.

Scenario index:
  01. Phase 1 — BedrockClient mock mode round-trips a Response shape.
  02. Phase 2 — Tool registry assembly with deny rules + plan mode.
  03. Phase 3 — read_file dispatch returns content (read-only path live).
  04. Phase 5 — bash dispatch blocked by SecurityManager (DANGEROUS_PATTERNS live).
  05. Phase 5 — python_exec rejects banned import (closure sandbox live).
  06. Phase 6 — System prompt under 2500 token budget; tool_classes at slot 2.
  07. Phase 6 — Cache boundary marker present in assembled prompt.
  08. Phase 7 — apply_tool_search_deferral partitions correctly + tool_search loadable.
  09. Phase 8 — End-to-end QueryEngine: user → tool_use → tool_result → final.
  10. Phase 8 — Phase 7 wiring contract: tool_search promotes deferred tool to next turn.
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
# Fixtures
# ============================================================

@pytest.fixture(autouse=True)
def _reset_registry():
    from tools.registry import _reset_registry_for_tests
    from tools import bootstrap_built_ins
    _reset_registry_for_tests()
    bootstrap_built_ins()
    yield


class _ScriptedClient:
    """Mock Bedrock that returns pre-scripted responses."""

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
            return Response(text="", tool_calls=[ToolCall(cid, name, args)],
                            stop_reason="tool_use")
        raise AssertionError(f"unknown script kind: {kind}")


# ============================================================
# Scenario 01 — Phase 1 BedrockClient mock-mode shape
# ============================================================

def test_thin_slice_01_bedrock_mock_round_trip():
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    resp = client.chat(
        messages=[{"role": "user", "content": "hi"}],
        system="you are helpful",
        tools=[],
        max_tokens=128,
    )
    # Mock returns a Response with end_turn stop and a usage dict
    assert resp.stop_reason in ("end_turn", "tool_use")
    assert isinstance(resp.text, str)


# ============================================================
# Scenario 02 — Phase 2 registry assembly: deny + plan-mode
# ============================================================

def test_thin_slice_02_registry_deny_plus_plan_mode():
    from tools.registry import assemble_tool_pool, PLAN_MODE_ALLOWED_TOOLS

    # Deny bash; plan mode further restricts to read-only allowlist.
    pool = assemble_tool_pool(plan_mode=True, deny_rules={"bash"})
    names = {t.name for t in pool}
    assert "bash" not in names                  # deny applied
    assert "edit_file" not in names             # plan-mode strips mutating
    assert "read_file" in names                 # read-only allowed
    assert names.issubset(PLAN_MODE_ALLOWED_TOOLS)


# ============================================================
# Scenario 03 — Phase 3 read_file dispatch
# ============================================================

def test_thin_slice_03_read_file_dispatch(tmp_path, monkeypatch):
    """read_file must return a structured result for an existing file."""
    target = tmp_path / "hello.txt"
    target.write_text("hello world\n", encoding="utf-8")

    # Point CONFIG.workspace at tmp_path so SECURITY allows reads here.
    from runtime.config import CONFIG
    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    from security import manager as _sm
    _sm.rebuild_singleton_for_tests()

    from tools import find_tool_by_name, all_registered
    rf = find_tool_by_name(all_registered(), "read_file")
    out = rf.execute({"file_path": str(target)})
    assert "hello world" in (out if isinstance(out, str) else str(out))


# ============================================================
# Scenario 04 — Phase 5 bash blocked by DANGEROUS_PATTERNS
# ============================================================

def test_thin_slice_04_bash_blocked_by_security():
    from tools import find_tool_by_name, all_registered
    bash_tool = find_tool_by_name(all_registered(), "bash")
    # `rm -rf /` must be blocked by SECURITY.is_dangerous_command.
    out = bash_tool.execute({"command": "rm -rf /"})
    text = out if isinstance(out, str) else str(out)
    assert "block" in text.lower() or "denied" in text.lower() or "danger" in text.lower()


# ============================================================
# Scenario 05 — Phase 5 python_exec rejects banned import (closure sandbox)
# ============================================================

def test_thin_slice_05_python_exec_blocks_banned_import():
    from tools import find_tool_by_name, all_registered
    pe = find_tool_by_name(all_registered(), "python_exec")
    # `socket` is on the BLOCKED set in Phase 5 dangerous_python.
    out = pe.execute({"code": "import socket"})
    text = out if isinstance(out, str) else str(out)
    # Either the closure sandbox blocks it, or the static-analysis pass does.
    assert ("import" in text.lower() and "block" in text.lower()) \
        or "socket" in text.lower() and "denied" in text.lower() \
        or "not allowed" in text.lower() \
        or "DANGEROUS" in text.upper()


# ============================================================
# Scenario 06 — Phase 6 system prompt under budget + slot-2 invariant
# ============================================================

def test_thin_slice_06_system_prompt_budget_and_slot_2():
    """V5_PLAN.md §Phase 6 acceptance: static prompt ≤ 2500 tokens.
    `total_static_tokens()` is the canonical audit metric (matches
    `tests/aggregate_audit.py`). It excludes assembly framing (boundary
    marker + section separators) which are constant overhead."""
    from prompt import build_system_prompt, CACHE_BOUNDARY
    from prompt.sections import SECTION_ORDER, total_static_tokens

    tokens = total_static_tokens()
    assert tokens <= 2500, f"static prompt = {tokens} tokens (budget 2500)"
    # tool_classes at slot 2 (PS Issue #7 fix). SECTION_ORDER is List[Section];
    # 0-indexed slot 1 = the prompt's "second section".
    assert SECTION_ORDER[1].name == "tool_classes", (
        f"slot-2 must be 'tool_classes', got {SECTION_ORDER[1].name!r}"
    )
    # And the assembled prompt actually contains a boundary marker (Phase 7)
    assert CACHE_BOUNDARY in build_system_prompt(ctx={})


# ============================================================
# Scenario 07 — Phase 6 cache boundary marker present
# ============================================================

def test_thin_slice_07_cache_boundary_marker_present():
    from prompt import build_system_prompt, CACHE_BOUNDARY

    prompt_text = build_system_prompt(ctx={})
    assert CACHE_BOUNDARY in prompt_text, (
        "Cache boundary marker must be present so BedrockClient can split "
        "static (cached) from dynamic (uncached) prompt blocks"
    )
    static_part, dynamic_part = prompt_text.split(CACHE_BOUNDARY, 1)
    assert len(static_part) > 0
    # dynamic_part may be empty (no per-call dynamic section yet) — that's fine.


# ============================================================
# Scenario 08 — Phase 7 deferred-loading partition + tool_search executes
# ============================================================

def test_thin_slice_08_phase7_deferral_round_trip():
    from tools import all_registered, find_tool_by_name, apply_tool_search_deferral

    visible, deferred_names = apply_tool_search_deferral(all_registered(), enabled=True)
    visible_names = {t.name for t in visible}
    # Initial Phase 7 deferred set
    assert "view_image" in deferred_names
    assert "list_dir" in deferred_names
    assert "notebook_edit" in deferred_names
    assert "view_image" not in visible_names
    # tool_search itself stays visible (always_load)
    assert "tool_search" in visible_names

    # tool_search executes and emits a <functions> block + discovered marker
    ts = find_tool_by_name(all_registered(), "tool_search")
    out = ts.execute({"query": "select:view_image"})
    assert "<functions>" in out
    assert "view_image" in out

    from tools.tool_search import tool_search_discovered_names
    discovered = tool_search_discovered_names(out)
    assert "view_image" in discovered


# ============================================================
# Scenario 09 — Phase 8 end-to-end QueryEngine
# ============================================================

def test_thin_slice_09_query_engine_end_to_end():
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([
        ("tool", "c1", "read_file", {"file_path": "any.txt"}),
        ("text", "Read it."),
    ])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="read a file",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "end_turn"
    assert result.text == "Read it."
    assert result.turns_used == 2
    # Conversation has the 4-message round-trip
    assert len(result.messages) == 4


# ============================================================
# Scenario 10 — Phase 8 Phase 7 wiring contract end-to-end
# ============================================================

def test_thin_slice_10_phase7_wiring_promotes_deferred_tool():
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([
        ("tool", "c1", "tool_search", {"query": "select:view_image"}),
        ("tool", "c2", "view_image", {"file_path": "x.png"}),
        ("text", "Done."),
    ])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="look",
        system_prompt="sys",
        tools=all_registered(),
    )
    turn1_names = {t["name"] for t in client.calls[0]["tools"]}
    turn2_names = {t["name"] for t in client.calls[1]["tools"]}
    # Turn 1 must NOT include view_image (deferred); turn 2 MUST (promoted).
    assert "view_image" not in turn1_names
    assert "view_image" in turn2_names
    assert result.stop_reason == "end_turn"
