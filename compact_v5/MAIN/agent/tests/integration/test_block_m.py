"""Block M — Phase 8 critical fixes (per-run discoveredSkillNames reset +
structured-output retry-limit counter).

Source: Runnable QueryEngine.ts:197 (discoveredSkillNames Set) + :238
(.clear() at run-entry) + :1004-1048 (countToolCalls helper +
MAX_STRUCTURED_OUTPUT_RETRIES guard).

Tests per TEST_DESIGN §Block M (3 T1+T2 tests, $0):
- test_discovered_tool_names_reset_per_turn — locks per-run reset of
  SkillManager._pending_activations (the v5 analog of Runnable's
  discoveredSkillNames). TEST_DESIGN catalogue name preserved
  verbatim — the literal "tool" naming refers to the Runnable
  concept; in v5 the surface is skills (PORT_LOG #085 reconciles).
- test_structured_output_retry_limit_3 — at retry limit 3, halts.
- test_infinite_loop_blocked_at_retry_limit — model returns malformed
  structured output 3x → halt with stop_reason
  "error_max_structured_output_retries".
"""
from __future__ import annotations

import os
import sys
from typing import Any

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# Fixtures + scripted client (same shape as test_query_engine.py)
# ============================================================

class _ScriptedClient:
    """Minimal mock Bedrock client."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []
        self.model_id = "anthropic.claude-haiku-4-5-20251001-v1:0"
        self.mock_mode = True

    def chat(self, messages, system, tools, max_tokens, temperature,
             thinking_enabled, thinking_budget):
        from runtime.bedrock_client import Response, ToolCall
        self.calls.append({"messages": list(messages)})
        if not self.script:
            return Response(text="(end)", tool_calls=[],
                            stop_reason="end_turn", usage={})
        kind, *rest = self.script.pop(0)
        if kind == "text":
            return Response(text=rest[0], tool_calls=[],
                            stop_reason="end_turn", usage={})
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
        raise AssertionError(f"unknown kind {kind}")


@pytest.fixture(autouse=True)
def fresh_registry():
    from tools.registry import _reset_registry_for_tests
    from tools import bootstrap_built_ins
    _reset_registry_for_tests()
    bootstrap_built_ins()
    yield


# ============================================================
# Pure-function tests — count_tool_calls helper
# ============================================================

def test_count_tool_calls_empty_messages():
    from core import count_tool_calls
    assert count_tool_calls([], "any") == 0


def test_count_tool_calls_no_match():
    from core import count_tool_calls
    msgs = [
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "1", "name": "read_file", "input": {}},
        ]},
    ]
    assert count_tool_calls(msgs, "structured_output") == 0


def test_count_tool_calls_multiple_matches():
    from core import count_tool_calls
    msgs = [
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "1", "name": "x", "input": {}},
            {"type": "text", "text": "thinking..."},
        ]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "1", "content": ""}]},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "2", "name": "x", "input": {}},
        ]},
    ]
    assert count_tool_calls(msgs, "x") == 2


def test_count_tool_calls_ignores_user_role():
    """tool_use blocks ONLY count when on assistant turns. A tool_use-
    shaped block accidentally on a user turn is malformed and ignored."""
    from core import count_tool_calls
    msgs = [
        {"role": "user", "content": [
            {"type": "tool_use", "id": "1", "name": "x", "input": {}},
        ]},
    ]
    assert count_tool_calls(msgs, "x") == 0


def test_count_tool_calls_handles_string_content():
    """An assistant turn with a plain-string content (not a list) doesn't
    crash count_tool_calls."""
    from core import count_tool_calls
    msgs = [
        {"role": "assistant", "content": "I'm done."},
    ]
    assert count_tool_calls(msgs, "x") == 0


# ============================================================
# TEST_DESIGN row 1 — discoveredSkillNames per-run reset (M-1)
# ============================================================

def test_discovered_tool_names_reset_per_turn(tmp_path):
    """TEST_DESIGN catalogue name preserved verbatim. The actual surface
    in v5 is SkillManager._pending_activations (the analog of Runnable's
    discoveredSkillNames Set at QueryEngine.ts:197). The list is cleared
    at run() entry per Runnable QueryEngine.ts:238 verbatim — prevents
    skill activations from a prior user message from contaminating the
    next message.
    """
    from core import QueryEngine
    from skills.manager import SkillManager
    from tools import all_registered

    # Set up an isolated SkillManager with one stub skill.
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    sk = skills_dir / "alpha"
    sk.mkdir()
    (sk / "SKILL.md").write_text(
        "---\nname: alpha\ndescription: Use anytime.\n---\nbody",
        encoding="utf-8",
    )
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(skills_dir))
    sm.discover()
    # Pre-pollute pending_activations as if a prior run() had activated.
    sm._pending_activations.append("alpha")
    assert sm._pending_activations == ["alpha"]

    # Engine.run() must clear the list before the for-loop body executes.
    client = _ScriptedClient([("text", "ok")])
    engine = QueryEngine(client=client, max_turns=2, skill_manager=sm)
    engine.run(user_message="hi", system_prompt="sys", tools=all_registered())

    # Block M-1 lock: list cleared at run() entry.
    assert sm._pending_activations == [], (
        "SkillManager._pending_activations must be cleared at run() entry "
        "(Block M-1, Runnable QueryEngine.ts:238 parity)"
    )


# ============================================================
# TEST_DESIGN row 2 — structured-output retry limit at 3 (M-2)
# ============================================================

def test_structured_output_retry_limit_3():
    """When `synthetic_output_tool_name` is configured and the
    pre-existing assistant messages already contain >= 3 tool_use of
    that name, the engine must halt at the FIRST turn with
    stop_reason="error_max_structured_output_retries".
    """
    from core import QueryEngine
    from runtime.bedrock_client import ToolCall
    from tools import all_registered

    client = _ScriptedClient([
        # Each turn the model produces another malformed structured output.
        ("tool", "c1", "structured_output", {}),
        ("tool", "c2", "structured_output", {}),
        ("tool", "c3", "structured_output", {}),
        ("text", "should never reach"),
    ])
    engine = QueryEngine(
        client=client,
        max_turns=10,
        synthetic_output_tool_name="structured_output",
        max_structured_output_retries=3,
    )
    result = engine.run(
        user_message="give structured output",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "error_max_structured_output_retries"
    # Halt FIRES at the top of turn 4 (after 3 tool_use accumulated).
    # turns_used should be exactly 3 (the 3 invocations that produced
    # the structured_output tool_use blocks).
    assert result.turns_used == 3


# ============================================================
# TEST_DESIGN row 3 — full-loop infinite-loop block (M-2)
# ============================================================

def test_infinite_loop_blocked_at_retry_limit():
    """End-to-end: model returns malformed structured output 3 times in
    a row → engine halts cleanly. Without this guard the loop would
    continue until max_turns, wasting tokens.
    """
    from core import QueryEngine
    from tools import all_registered

    # Model produces 5 consecutive malformed structured outputs. With
    # retry_limit=3, halt fires before the 4th. turns_used=3 (only 3
    # tool_use turns executed).
    client = _ScriptedClient([
        ("tool", "c1", "synth_out", {}),
        ("tool", "c2", "synth_out", {}),
        ("tool", "c3", "synth_out", {}),
        ("tool", "c4", "synth_out", {}),
        ("tool", "c5", "synth_out", {}),
    ])
    engine = QueryEngine(
        client=client,
        max_turns=20,
        synthetic_output_tool_name="synth_out",
        max_structured_output_retries=3,
    )
    result = engine.run(
        user_message="output JSON",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "error_max_structured_output_retries"
    # max_turns=20 was NOT hit — the retry-limit guard fired first.
    assert result.turns_used < 20
    assert result.turns_used == 3


# ============================================================
# Behavioral lock tests
# ============================================================

def test_default_synthetic_output_tool_name_is_none():
    """Block M-2: when no synthetic_output_tool_name is configured, the
    engine must NOT halt on any tool — preserves backwards compatibility
    with all existing tests / users that don't use structured output."""
    from core import QueryEngine
    from tools import all_registered

    client = _ScriptedClient([
        ("tool", "c1", "read_file", {"file_path": "x"}),
        ("text", "done"),
    ])
    engine = QueryEngine(client=client, max_turns=5)
    assert engine.synthetic_output_tool_name is None
    result = engine.run(
        user_message="read",
        system_prompt="sys",
        tools=all_registered(),
    )
    # Normal end_turn — no early halt.
    assert result.stop_reason == "end_turn"


def test_retry_limit_clamps_to_minimum_one():
    """Block M-2: max_structured_output_retries < 1 silently clamps to 1
    (max(1, int(...)) per __init__). Prevents division-by-zero or
    negative-loop semantics."""
    from core import QueryEngine

    e1 = QueryEngine(client=_ScriptedClient([]), max_structured_output_retries=0)
    assert e1.max_structured_output_retries == 1
    e2 = QueryEngine(client=_ScriptedClient([]), max_structured_output_retries=-5)
    assert e2.max_structured_output_retries == 1
    e3 = QueryEngine(client=_ScriptedClient([]), max_structured_output_retries=10)
    assert e3.max_structured_output_retries == 10


def test_initial_structured_output_calls_baseline_captured(tmp_path):
    """Block M-2: when run() starts on an engine that already has
    pre-existing assistant messages with N synthetic_output tool_use
    blocks, the baseline N is captured so the per-run retry limit
    accounts only for THIS run's calls (not the prior session's)."""
    from core import QueryEngine
    from runtime.bedrock_client import ToolCall

    # Pre-pollute messages with 5 prior synthetic_output calls.
    pre_msgs = [
        {"role": "user", "content": "earlier"},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": f"old-{i}", "name": "synth", "input": {}}
            for i in range(5)
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": f"old-{i}", "content": ""}
            for i in range(5)
        ]},
    ]
    client = _ScriptedClient([("text", "fresh")])
    engine = QueryEngine(
        client=client, max_turns=5,
        synthetic_output_tool_name="synth",
        max_structured_output_retries=3,
    )
    engine.messages = list(pre_msgs)  # simulate carried-over session
    from tools import all_registered
    result = engine.run(
        user_message="continue",
        system_prompt="sys",
        tools=all_registered(),
    )
    # Baseline=5 captured; 0 new synth calls; not halted.
    assert engine._initial_structured_output_calls == 5
    assert result.stop_reason == "end_turn"
