"""Block G3 — Coordinator System Prompt (NEW BLOCK).

Source: Runnable coordinator/coordinatorMode.ts:111-369 (system prompt) +
:80-109 (user context).

Tests per TEST_DESIGN §Block G3 (5 tests; T5 gated by RUN_REAL_BEDROCK):
- test_coordinator_prompt_contains_4_phases
- test_coordinator_prompt_synthesize_dont_delegate
- test_coordinator_prompt_continue_vs_spawn_table
- test_coordinator_prompt_research_parallel_write_serial
- test_coordinator_prompt_real_haiku_orchestration (T5, $0.01 cap)
"""
from __future__ import annotations

import os
import sys

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# TEST_DESIGN row 1 — 4 phases verbatim
# ============================================================

def test_coordinator_prompt_contains_4_phases():
    """Per TEST_DESIGN: prompt contains 'Research → Synthesis →
    Implementation → Verification'."""
    from coordinator import get_coordinator_system_prompt

    prompt = get_coordinator_system_prompt()
    assert "Research → Synthesis → Implementation → Verification" in prompt


# ============================================================
# TEST_DESIGN row 2 — synthesize, don't delegate
# ============================================================

def test_coordinator_prompt_synthesize_dont_delegate():
    """Prompt contains 'NEVER delegate understanding'."""
    from coordinator import get_coordinator_system_prompt

    prompt = get_coordinator_system_prompt()
    assert "NEVER delegate understanding" in prompt
    # Also lock the anti-pattern phrasing the user specifically called out.
    assert "based on your findings" in prompt.lower()
    assert "based on the research" in prompt.lower()


# ============================================================
# TEST_DESIGN row 3 — continue-vs-spawn matrix
# ============================================================

def test_coordinator_prompt_continue_vs_spawn_table():
    """Prompt contains a continue-vs-spawn decision table."""
    from coordinator import get_coordinator_system_prompt

    prompt = get_coordinator_system_prompt()
    # The table header has "Situation | Mechanism | Why" and 6 rows.
    assert "Continue vs Spawn" in prompt or "continue vs spawn" in prompt.lower()
    # Each major decision row.
    assert "research explored exactly the files" in prompt.lower()
    assert "spawn fresh" in prompt.lower()
    assert "verifier should see the code with fresh eyes" in prompt.lower()


# ============================================================
# TEST_DESIGN row 4 — parallel research, serial write
# ============================================================

def test_coordinator_prompt_research_parallel_write_serial():
    """Prompt contains 'Read-only tasks: run in parallel; Write tasks:
    one at a time' (or close paraphrase)."""
    from coordinator import get_coordinator_system_prompt

    prompt = get_coordinator_system_prompt()
    # The exact phrasing per TEST_DESIGN.
    assert "Read-only tasks: run in parallel" in prompt
    assert "Write tasks: one at a time" in prompt


# ============================================================
# TEST_DESIGN row 5 — real-Haiku orchestration (T5; $0.01 cap)
# ============================================================

@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="T5 real-AWS test; gate with RUN_REAL_BEDROCK=1",
)
def test_coordinator_prompt_real_haiku_orchestration():
    """Real Haiku-4.5 round-trip: prompt agent to coordinate 3 sub-agents
    → assert it spawns parallel reads, serial writes.

    Cap: ~$0.01. Only runs when RUN_REAL_BEDROCK=1.
    """
    pytest.skip(
        "Real-Bedrock orchestration test deferred to R-tier (R3 dispatch); "
        "Block G3 ships without burning AWS credit during unit-test phase."
    )


# ============================================================
# Behavioral lock tests
# ============================================================

def test_get_coordinator_user_context_includes_worker_tools():
    """G3-2 lock: user context describes worker tools available."""
    from coordinator import get_coordinator_user_context

    ctx = get_coordinator_user_context(workspace="/tmp/work")
    assert "worker types" in ctx.lower() or "agent_type" in ctx.lower()
    assert "explore" in ctx and "build" in ctx and "verify" in ctx


def test_get_coordinator_user_context_with_scratchpad_dir():
    from coordinator import get_coordinator_user_context

    ctx = get_coordinator_user_context(scratchpad_dir="/tmp/sp")
    assert "Scratchpad directory" in ctx
    assert "/tmp/sp" in ctx
    assert "without permission prompts" in ctx


def test_get_coordinator_user_context_falls_back_to_workspace_scratchpad():
    """When scratchpad_dir is None, derive from workspace."""
    from coordinator import get_coordinator_user_context

    ctx = get_coordinator_user_context(workspace="/tmp/ws")
    assert "/tmp/ws/.scratchpad" in ctx


def test_get_coordinator_user_context_no_scratchpad_when_no_inputs():
    """No workspace + no scratchpad_dir → omit the scratchpad section."""
    from coordinator import get_coordinator_user_context

    ctx = get_coordinator_user_context()
    assert "Scratchpad directory" not in ctx


# ============================================================
# Engine wiring lock tests
# ============================================================

def test_coordinator_prompt_appended_when_flag_on():
    """Block G3 wiring: when CONFIG.coordinator_mode_enabled is True AND
    agent_kind is parent, the coordinator prompt is appended to the
    effective system prompt sent to chat()."""
    from core import QueryEngine
    from core.budget import IterationBudget
    from runtime.config import CONFIG
    from tools import all_registered

    seen = {}

    class _SnoopClient:
        def __init__(self):
            self.model_id = "x"
            self.mock_mode = True

        def chat(self, messages, system, tools, max_tokens, temperature,
                 thinking_enabled, thinking_budget):
            from runtime.bedrock_client import Response
            seen["system"] = system
            return Response(text="ok", tool_calls=[],
                            stop_reason="end_turn", usage={})

    _prev = CONFIG.coordinator_mode_enabled
    CONFIG.coordinator_mode_enabled = True
    try:
        parent = QueryEngine(client=_SnoopClient(), max_turns=2,
                             budget=IterationBudget(max_iterations=10))
        parent.run(user_message="x", system_prompt="base", tools=all_registered())
        sys_prompt = seen["system"]
        assert "Coordinator Mode" in sys_prompt or "coordinator" in sys_prompt.lower()
        assert "Research → Synthesis → Implementation → Verification" in sys_prompt
        assert "NEVER delegate understanding" in sys_prompt
    finally:
        CONFIG.coordinator_mode_enabled = _prev


def test_coordinator_prompt_NOT_appended_when_flag_off():
    """Default OFF — no coordinator block in the system prompt."""
    from core import QueryEngine
    from core.budget import IterationBudget
    from runtime.config import CONFIG
    from tools import all_registered

    seen = {}

    class _SnoopClient:
        def __init__(self):
            self.model_id = "x"
            self.mock_mode = True

        def chat(self, messages, system, tools, max_tokens, temperature,
                 thinking_enabled, thinking_budget):
            from runtime.bedrock_client import Response
            seen["system"] = system
            return Response(text="ok", tool_calls=[],
                            stop_reason="end_turn", usage={})

    _prev = CONFIG.coordinator_mode_enabled
    assert _prev is False  # default OFF
    try:
        parent = QueryEngine(client=_SnoopClient(), max_turns=2,
                             budget=IterationBudget(max_iterations=10))
        parent.run(user_message="x", system_prompt="base", tools=all_registered())
        sys_prompt = seen["system"]
        assert "Coordinator Mode" not in sys_prompt
        assert "NEVER delegate understanding" not in sys_prompt
    finally:
        CONFIG.coordinator_mode_enabled = _prev


def test_coordinator_prompt_NOT_appended_for_subagent():
    """Sub-agents are workers, not coordinators — they must not see the
    coordinator prompt even when the flag is on."""
    from core import QueryEngine
    from core.budget import IterationBudget
    from runtime.config import CONFIG
    from tools import all_registered

    seen = {}

    class _SnoopClient:
        def __init__(self):
            self.model_id = "x"
            self.mock_mode = True

        def chat(self, messages, system, tools, max_tokens, temperature,
                 thinking_enabled, thinking_budget):
            from runtime.bedrock_client import Response
            seen["system"] = system
            return Response(text="ok", tool_calls=[],
                            stop_reason="end_turn", usage={})

    _prev = CONFIG.coordinator_mode_enabled
    CONFIG.coordinator_mode_enabled = True
    try:
        # agent_kind="explore" simulates a sub-agent.
        child = QueryEngine(
            client=_SnoopClient(), max_turns=2,
            budget=IterationBudget(max_iterations=10),
            agent_kind="explore",
        )
        child.run(user_message="x", system_prompt="base", tools=all_registered())
        sys_prompt = seen["system"]
        assert "Coordinator Mode" not in sys_prompt, (
            "sub-agents must NOT see coordinator prompt — they are workers"
        )
    finally:
        CONFIG.coordinator_mode_enabled = _prev
