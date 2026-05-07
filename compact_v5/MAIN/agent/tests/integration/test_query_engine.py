"""Phase 08 integration tests: core/query_engine.py — end-to-end agent loop.

Acceptance criterion (V5_PLAN.md §Phase 8):
- end-to-end mock test (tool_use → tool runs → final answer)
- tool_search deferred-loading round-trip works

Locks PORT_LOG #019: Runnable QueryEngine.ts adapted to v5 .ipynb shape.
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
# Test fixtures
# ============================================================

class _ScriptedClient:
    """Mock Bedrock client that returns pre-scripted responses in order.

    Each entry is one of:
      - ("text", "final answer")              → stop_reason=end_turn, no tools
      - ("tool", call_id, tool_name, args)    → tool_use block
      - ("text+tool", text, call_id, name, args) → both text and tool_use
    """

    def __init__(self, script):
        self.script = list(script)
        self.calls = []  # list of (messages, tools_payload)

    def chat(self, messages, system, tools, max_tokens, temperature,
             thinking_enabled, thinking_budget):
        from runtime.bedrock_client import Response, ToolCall
        self.calls.append({
            "messages": list(messages),
            "tools": list(tools or []),
        })
        if not self.script:
            return Response(text="(no more scripted responses)", tool_calls=[],
                            stop_reason="end_turn", usage={})
        kind, *rest = self.script.pop(0)
        if kind == "text":
            return Response(text=rest[0], tool_calls=[], stop_reason="end_turn", usage={})
        if kind == "tool":
            cid, name, args = rest
            return Response(
                text="", tool_calls=[ToolCall(cid, name, args)],
                stop_reason="tool_use", usage={},
            )
        if kind == "text+tool":
            txt, cid, name, args = rest
            return Response(
                text=txt,
                tool_calls=[ToolCall(cid, name, args)],
                stop_reason="tool_use", usage={},
            )
        raise AssertionError(f"unknown script kind: {kind}")


@pytest.fixture(autouse=True)
def fresh_registry():
    """Phase 7 / Phase 2 tests mutate the registry; force-reset for Phase 8."""
    from tools.registry import _reset_registry_for_tests
    from tools import bootstrap_built_ins
    _reset_registry_for_tests()
    bootstrap_built_ins()
    yield


# ============================================================
# Test 1 — basic single-turn end_turn
# ============================================================

def test_engine_returns_final_text_on_end_turn():
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([("text", "Hello world.")])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="say hi",
        system_prompt="you are an assistant",
        tools=all_registered(),
    )
    assert result.stop_reason == "end_turn"
    assert result.text == "Hello world."
    assert result.turns_used == 1


# ============================================================
# Test 2 — tool_use → tool runs → tool_result → final answer
# ============================================================

def test_engine_dispatches_tool_then_finalizes():
    from core import QueryEngine
    from tools import all_registered

    # Turn 1: model asks for read_file. Turn 2: model gives final answer.
    client = _ScriptedClient([
        ("tool", "call_1", "read_file", {"file_path": "nonexistent_for_test.txt"}),
        ("text", "I read the file."),
    ])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="read a file",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "end_turn"
    assert result.text == "I read the file."
    assert result.turns_used == 2
    # Conversation must contain: user, assistant(tool_use), user(tool_result), assistant(text).
    roles = [m["role"] for m in result.messages]
    assert roles == ["user", "assistant", "user", "assistant"]
    # The tool_result block must have correct tool_use_id.
    tr_block = result.messages[2]["content"][0]
    assert tr_block["type"] == "tool_result"
    assert tr_block["tool_use_id"] == "call_1"


def test_engine_repairs_invalid_tool_result_pairs_before_api_call():
    """Long compaction/recovery must not send invalid tool_result blocks."""
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([("text", "recovered")])
    engine = QueryEngine(client=client, max_turns=2)
    engine.messages = [
        {
            "role": "assistant",
            "content": [{
                "type": "tool_use",
                "id": "dup",
                "name": "read_file",
                "input": {},
            }],
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "dup", "content": "first"},
                {"type": "tool_result", "tool_use_id": "dup", "content": "duplicate"},
                {"type": "tool_result", "tool_use_id": "lost", "content": "orphan"},
            ],
        },
    ]

    result = engine.run(
        user_message="continue",
        system_prompt="sys",
        tools=all_registered(),
    )

    assert result.stop_reason == "end_turn"
    sent_user = client.calls[0]["messages"][1]
    typed_results = [
        block for block in sent_user["content"]
        if isinstance(block, dict) and block.get("type") == "tool_result"
    ]
    text_blocks = [
        block for block in sent_user["content"]
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    assert [block["tool_use_id"] for block in typed_results] == ["dup"]
    joined_text = "\n".join(block["text"] for block in text_blocks)
    assert "duplicate" in joined_text
    assert "orphan" in joined_text


# ============================================================
# Test 3 — Phase 7 wiring contract: tools= payload excludes deferred tools by default
# ============================================================

def test_engine_excludes_deferred_tools_from_first_turn_payload():
    """First turn, no tool_search calls yet: per-turn `tools=` must NOT include
    view_image, list_dir, notebook_edit. tool_search itself MUST be included."""
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([("text", "ok")])
    engine = QueryEngine(client=client, max_turns=2)
    engine.run(
        user_message="hi",
        system_prompt="sys",
        tools=all_registered(),
    )
    sent_tools = client.calls[0]["tools"]
    sent_names = {t["name"] for t in sent_tools}
    assert "tool_search" in sent_names
    assert "view_image" not in sent_names
    assert "list_dir" not in sent_names
    assert "notebook_edit" not in sent_names
    # Phase 9 added `task` tool with should_defer=True — must also be excluded.
    assert "task" in sent_names
    # Phase 10 added `skill` and `skill_propose_patch` with should_defer=True.
    assert "skill" not in sent_names
    assert "skill_propose_patch" not in sent_names
    # high-frequency tools must remain visible
    assert "read_file" in sent_names
    assert "edit_file" in sent_names


# ============================================================
# Test 4 — Phase 7 round-trip: tool_search promotes deferred tool into next turn
# ============================================================

def test_tool_search_round_trip_promotes_deferred_tool():
    """Phase 8 acceptance: model calls tool_search → query_engine extracts the
    discovered names → next turn's `tools=` payload includes those tools.

    The hidden marker `<!-- v5_discovered:NAME --> ` emitted by tool_search is
    extracted via `tool_search_discovered_names()` and the named tool's full
    schema is added to the next turn's payload."""
    from core import QueryEngine
    from tools import all_registered

    # Turn 1: model calls tool_search for view_image (a deferred tool).
    # Turn 2: model now calls view_image (its schema was promoted).
    # Turn 3: model gives final answer.
    client = _ScriptedClient([
        ("tool", "call_1", "tool_search", {"query": "select:view_image"}),
        ("tool", "call_2", "view_image", {"file_path": "nonexistent.png"}),
        ("text", "Done."),
    ])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="look at an image",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "end_turn"
    assert result.turns_used == 3

    # Turn 1 payload: view_image is NOT in tools=
    turn1_names = {t["name"] for t in client.calls[0]["tools"]}
    assert "view_image" not in turn1_names
    assert "tool_search" in turn1_names

    # Turn 2 payload: view_image IS in tools= (promoted by Phase 7 wiring)
    turn2_names = {t["name"] for t in client.calls[1]["tools"]}
    assert "view_image" in turn2_names, (
        "view_image must be promoted into per-turn payload after tool_search "
        "discovered it"
    )


def test_engine_warns_and_records_status_on_max_turns(tmp_path, monkeypatch):
    """Long software runs get a finalization nudge and resume state at max_turns."""
    from core import QueryEngine
    from runtime.config import CONFIG
    from tools import all_registered

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "status_doc", "AGENT_STATUS.md")
    monkeypatch.setattr(CONFIG, "enable_status_doc", True)
    (tmp_path / "AGENT_STATUS.md").write_text(
        "# Status\n\nCurrent phase: implementing", encoding="utf-8",
    )
    client = _ScriptedClient([
        ("tool", f"call_{i}", "read_file", {"file_path": f"x{i}.txt"})
        for i in range(5)
    ])
    out = []
    engine = QueryEngine(client=client, max_turns=3)
    result = engine.run(
        user_message="loop",
        system_prompt="sys",
        tools=all_registered(),
        output_fn=out.append,
    )

    assert result.stop_reason == "max_turns"
    last_messages = client.calls[-1]["messages"]
    assert "Turn budget warning" in str(last_messages[-1]["content"])
    status_text = (tmp_path / "AGENT_STATUS.md").read_text(encoding="utf-8")
    assert "SAGEAGENT_MAX_TURNS_RESUME_STATE" in status_text
    assert "Stop reason: max_turns" in status_text
    assert "Completion claim: NOT_DONE" in status_text
    assert any("AGENT_STATUS.md updated for max_turns resume" in line for line in out)


# ============================================================
# Test 5 — IterationBudget gate stops the loop
# ============================================================

def test_engine_stops_on_budget_exhausted():
    """Pre-consume the budget so the first turn can't be entered."""
    from core import QueryEngine, IterationBudget
    from tools import all_registered

    budget = IterationBudget(max_iterations=2)
    budget.consume()
    budget.consume()  # exhausted

    client = _ScriptedClient([("text", "should not be reached")])
    engine = QueryEngine(client=client, max_turns=5, budget=budget)
    result = engine.run(
        user_message="hi",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "budget_exhausted"
    assert result.turns_used == 0
    assert client.calls == []  # client.chat() was never called


# ============================================================
# Test 6 — max_turns cap
# ============================================================

def test_engine_stops_at_max_turns(monkeypatch):
    """If model never returns end_turn, the loop must exit cleanly at max_turns."""
    from core import QueryEngine
    from tools import all_registered
    from runtime.config import CONFIG

    monkeypatch.setattr(CONFIG, "enable_status_doc", False)

    # Always returns tool_use for read_file → engine never reaches end_turn.
    looping_script = [
        ("tool", f"call_{i}", "read_file", {"file_path": f"x{i}.txt"})
        for i in range(20)
    ]
    client = _ScriptedClient(looping_script)
    engine = QueryEngine(client=client, max_turns=3)
    result = engine.run(
        user_message="loop",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "max_turns"
    assert result.turns_used == 3


# ============================================================
# Test 7 — unknown tool name surfaces error to model
# ============================================================

def test_engine_returns_error_tool_result_for_unknown_tool():
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([
        ("tool", "call_1", "definitely_not_a_tool", {}),
        ("text", "ok, sorry"),
    ])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="call a tool that doesn't exist",
        system_prompt="sys",
        tools=all_registered(),
    )
    # Loop continues — model gets an error tool_result and can recover
    assert result.stop_reason == "end_turn"
    tr_block = result.messages[2]["content"][0]
    assert tr_block["is_error"] is True
    assert "unknown tool" in tr_block["content"]


# ============================================================
# Test 8 — tool that raises is surfaced to model, not user
# ============================================================

def test_engine_traps_tool_exception():
    from core import QueryEngine
    from tools.registry import build_tool, register, all_registered

    def boom(args, context=None):
        raise RuntimeError("kaboom")

    register(build_tool(
        name="boom_tool",
        description="raises",
        input_schema={"type": "object", "properties": {}},
        execute=boom,
        is_read_only=True,
    ))

    client = _ScriptedClient([
        ("tool", "call_1", "boom_tool", {}),
        ("text", "recovered"),
    ])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="call boom",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "end_turn"
    tr = result.messages[2]["content"][0]
    assert tr["is_error"] is True
    assert "RuntimeError" in tr["content"]
    assert "kaboom" in tr["content"]


# ============================================================
# Test 9 — system reminder injected for deferred tools
# ============================================================

def test_engine_injects_deferred_tools_system_reminder_on_first_turn():
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([("text", "ok")])
    engine = QueryEngine(client=client, max_turns=2)
    engine.run(
        user_message="hi",
        system_prompt="sys",
        tools=all_registered(),
    )
    sent_messages = client.calls[0]["messages"]
    last_user = sent_messages[-1]
    assert last_user["role"] == "user"
    # The system reminder must be appended as a text block on the user turn
    if isinstance(last_user["content"], list):
        joined = "\n".join(
            blk.get("text", "") for blk in last_user["content"]
            if isinstance(blk, dict)
        )
    else:
        joined = last_user["content"]
    assert "<system-reminder>" in joined
    assert "view_image" in joined
    assert "tool_search" in joined  # mentioned as the loader


# ============================================================
# Test 10 — context_overflow stops cleanly
# ============================================================

def test_engine_stops_on_context_overflow():
    """Bedrock raising prompt-too-long must classify as context_overflow and
    return cleanly with stop_reason set."""
    from core import QueryEngine
    from tools import all_registered

    class OverflowClient:
        def chat(self, **_kw):
            raise Exception("ValidationException: prompt is too long")

    engine = QueryEngine(client=OverflowClient(), max_turns=5)
    result = engine.run(
        user_message="hi",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "context_overflow"
    assert "context_overflow" in (result.error or "")


# ============================================================
# Test 11 — run_one_turn helper
# ============================================================

def test_run_one_turn_helper_applies_deferral():
    from core import run_one_turn
    from tools import all_registered

    client = _ScriptedClient([("text", "single turn")])
    response = run_one_turn(
        client=client,
        messages=[{"role": "user", "content": "hi"}],
        system_prompt="sys",
        tools=all_registered(),
    )
    assert response.text == "single turn"
    sent_names = {t["name"] for t in client.calls[0]["tools"]}
    assert "view_image" not in sent_names
    assert "tool_search" in sent_names


# ============================================================
# Test 12 — plan mode blocks mutating tools at dispatch
# ============================================================

def test_engine_blocks_mutating_tool_in_plan_mode():
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([
        ("tool", "call_1", "edit_file", {"file_path": "x", "old_string": "a", "new_string": "b"}),
        ("text", "noted"),
    ])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="edit a file",
        system_prompt="sys",
        tools=all_registered(),
        plan_mode=True,
    )
    tr = result.messages[2]["content"][0]
    assert tr["is_error"] is True
    assert "plan mode" in tr["content"]


# ============================================================
# Test 13 — Codex Phase-08 finding 2 lock: plan-mode strict allowlist
# ============================================================

def test_engine_plan_mode_blocks_always_load_mutating_tool():
    """Codex Phase-08 finding (medium) lock: a mutating tool that has
    `always_load=True` MUST still be blocked in plan mode. The previous
    dispatch gate exempted always_load tools, which would let any future
    always_load mutating tool slip past plan mode. The fix enforces a
    strict v4-style allowlist (PLAN_MODE_ALLOWED_TOOLS) at dispatch."""
    from core import QueryEngine
    from tools.registry import build_tool, register, all_registered

    register(build_tool(
        name="bypass_attempt_tool",
        description="synthetic mutating + always_load tool — must still be blocked in plan mode",
        input_schema={"type": "object", "properties": {}},
        execute=lambda args, context=None: "should never execute in plan mode",
        is_read_only=False,         # MUTATING
        always_load=True,           # always-loaded — would have bypassed old gate
        requires_approval=True,
    ))

    client = _ScriptedClient([
        ("tool", "call_1", "bypass_attempt_tool", {}),
        ("text", "blocked, ok"),
    ])
    engine = QueryEngine(client=client, max_turns=5)
    result = engine.run(
        user_message="try to bypass",
        system_prompt="sys",
        tools=all_registered(),
        plan_mode=True,
    )
    tr = result.messages[2]["content"][0]
    assert tr["is_error"] is True, (
        "Mutating always_load=True tool must still be blocked in plan mode"
    )
    assert "PLAN_MODE_ALLOWED_TOOLS" in tr["content"] or "plan mode" in tr["content"]


# ============================================================
# Test 14 — Codex Phase-08 finding 1 lock: discovered tools reset between runs
# ============================================================

def test_discovered_tools_reset_between_runs():
    """Codex Phase-08 finding (high) lock: `_discovered_tool_names` MUST be
    cleared at each `run()` start. Otherwise a tool_search discovery in
    run #1 would silently widen the per-turn `tools=` payload on run #2.

    Run #1: model calls tool_search to discover view_image.
    Run #2: model just sends a final answer.
    The first turn of run #2 must NOT include view_image in `tools=`.
    """
    from core import QueryEngine
    from tools import all_registered

    # Run #1: discovers view_image via tool_search.
    client_run1 = _ScriptedClient([
        ("tool", "call_1", "tool_search", {"query": "select:view_image"}),
        ("text", "discovered"),
    ])
    engine = QueryEngine(client=client_run1, max_turns=5)
    engine.run(
        user_message="discover view_image",
        system_prompt="sys",
        tools=all_registered(),
    )
    # Sanity: after run #1, view_image was promoted at some turn.
    assert "view_image" in engine._discovered_tool_names

    # Run #2: same engine, fresh user message. view_image MUST NOT be in
    # the first turn's tools= payload because the discovered set is reset.
    engine.client = _ScriptedClient([("text", "ok")])
    engine.run(
        user_message="hi again",
        system_prompt="sys",
        tools=all_registered(),
    )
    run2_first_turn_names = {t["name"] for t in engine.client.calls[0]["tools"]}
    assert "view_image" not in run2_first_turn_names, (
        "Discovered tool names from run #1 leaked into run #2's first turn payload"
    )
    # And the discovered set itself is empty after the second run starts (only
    # populated if the second run also calls tool_search, which it doesn't).
    assert "view_image" not in engine._discovered_tool_names


def test_final_claim_guard_rejects_stale_status_and_missing_zip(tmp_path, monkeypatch):
    """A done claim must not end the run when local evidence is still red."""
    from core import QueryEngine
    from runtime.config import CONFIG
    from tools import all_registered

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "status_doc", "AGENT_STATUS.md")
    monkeypatch.setattr(CONFIG, "enable_status_doc", True)
    (tmp_path / "AGENT_STATUS.md").write_text(
        "Current phase: PENDING\nTests: 79/80, 1 failed\n", encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "TEST_REPORT.md").write_text(
        "1 failed, 79 passed", encoding="utf-8",
    )
    client = _ScriptedClient([
        ("text", "Project complete. All tests pass."),
        ("text", "NOT_DONE: tests and zip still need correction."),
    ])
    out = []
    engine = QueryEngine(client=client, max_turns=3)
    result = engine.run(
        user_message="Required artifact: mini_research_worklog_result.zip",
        system_prompt="sys",
        tools=all_registered(),
        output_fn=out.append,
    )

    assert result.stop_reason == "end_turn"
    assert result.text.startswith("NOT_DONE")
    assert len(client.calls) == 2
    assert any("final-claim guard" in line for line in out)
