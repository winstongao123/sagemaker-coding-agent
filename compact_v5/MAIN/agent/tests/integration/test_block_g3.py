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
    # The table header.
    assert "Continue vs Spawn" in prompt or "continue vs spawn" in prompt.lower()
    # Major decision rows must be present (covers the 6 scenarios).
    plower = prompt.lower()
    # Phase-transition / explore-findings-need-implementation row.
    assert "phase transition" in plower or "implement" in plower
    assert "spawn fresh" in plower
    # The verification scenario uses verify-specific wording in v5.
    assert "verify" in plower
    assert "subagent_type" in prompt
    # The wrong-approach anti-anchoring rule.
    assert "anchoring" in plower or "pollutes" in plower


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


# ============================================================
# Codex iter-1 finding-lock tests
# ============================================================

def test_coordinator_block_preserved_when_skill_active(tmp_path):
    """Codex iter-1 finding #1 HIGH lock: when an active skill exists,
    the coordinator block must NOT be silently overwritten by the skill
    body assignment. Both the coordinator + skill bodies should appear
    in the final effective_system_prompt.
    """
    from core import QueryEngine
    from core.budget import IterationBudget
    from runtime.config import CONFIG
    from skills.manager import SkillManager
    from tools import all_registered

    # Set up an isolated SkillManager with one active skill.
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    sk = skills_dir / "myskill"
    sk.mkdir()
    (sk / "SKILL.md").write_text(
        "---\nname: myskill\ndescription: Test skill body marker.\n---\n"
        "SKILL_BODY_MARKER_XYZ",
        encoding="utf-8",
    )
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(skills_dir))
    sm.discover()
    sm.active_skill = "myskill"

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
        parent = QueryEngine(
            client=_SnoopClient(), max_turns=2,
            budget=IterationBudget(max_iterations=10),
            skill_manager=sm,
        )
        parent.run(user_message="x", system_prompt="base", tools=all_registered())
        sys_prompt = seen["system"]
        # BOTH must appear — coordinator block + skill body.
        assert "Coordinator Mode" in sys_prompt or "NEVER delegate understanding" in sys_prompt, (
            "Coordinator block must be preserved when skill is active "
            "(Codex iter-1 #1)"
        )
        assert "SKILL_BODY_MARKER_XYZ" in sys_prompt, (
            "Skill body must still be present"
        )
    finally:
        CONFIG.coordinator_mode_enabled = _prev


def test_coordinator_prompt_v5_continue_semantics_no_persistent_worker():
    """Codex iter-1 finding #2 HIGH lock: the Continue vs Spawn matrix
    must reflect v5's sync/fresh-buffer reality, NOT Runnable's
    persistent-worker semantics. Verify the prompt explicitly says:
    - Worker buffer never persists
    - Coordinator is the durable context
    - Continue = same agent_type + restate findings
    """
    from coordinator import get_coordinator_system_prompt

    prompt = get_coordinator_system_prompt()
    # The v5 reality must be stated. Tolerate markdown bold splitting
    # words across newlines: just verify both keywords appear close-by.
    norm = prompt.replace("\n", " ").replace("**", "")
    assert "synchronously to completion" in norm
    assert "fresh conversation buffer" in norm or "fresh buffer" in norm
    # No SendMessage-style persistent-worker claim.
    assert "SendMessage" not in prompt
    # The coordinator-as-durable-context guidance.
    assert (
        "Worker buffer NEVER persists" in prompt
        or "coordinator is the durable" in prompt.lower()
    )
    # Continue semantics in v5 explicitly: same subagent_type + restate.
    assert "subagent_type" in prompt
    assert "restate" in prompt.lower()

    # Codex iter-2 finding #2 tightening: the Continue row examples must
    # NOT show a cross-type transition (e.g. explore→build). Cross-type
    # is the Spawn-fresh case in v5. Search for any "X→Y" arrow inside
    # a Continue row to catch contradictory examples.
    import re as _re
    # Find all rows that start with `| ... | Continue |` and check their
    # third-column "What this means" content.
    continue_rows = _re.findall(
        r"\|[^|]*\|\s*Continue\s*\|\s*([^|\n]+)\|",
        prompt,
    )
    assert continue_rows, "expected at least one Continue row in the table"
    for row_content in continue_rows:
        # Reject any cross-type arrow (explore→build, build→verify, etc.).
        cross_type = _re.search(
            r"\b(explore|plan|verify|build|review|general|fork)→(?!\1\b)"
            r"(explore|plan|verify|build|review|general|fork)\b",
            row_content,
        )
        assert cross_type is None, (
            f"Continue row example uses a cross-type arrow "
            f"({cross_type.group()}). v5's `Continue` is same-type "
            f"only — cross-type belongs in Spawn fresh. Row: {row_content!r}"
        )


def test_coordinator_user_context_injected_into_first_user_message():
    """Codex iter-1 finding #3 MEDIUM lock: when coordinator_mode is on,
    the parent's first user message must be augmented with the worker-
    tools-context block (via get_coordinator_user_context). PORT_LOG
    #093 promises this — Runnable wires it the same way at QueryEngine.ts:302-307.
    """
    from core import QueryEngine
    from core.budget import IterationBudget
    from runtime.config import CONFIG
    from tools import all_registered

    captured_messages = []

    class _SnoopClient:
        def __init__(self):
            self.model_id = "x"
            self.mock_mode = True

        def chat(self, messages, system, tools, max_tokens, temperature,
                 thinking_enabled, thinking_budget):
            from runtime.bedrock_client import Response
            captured_messages.extend(list(messages))
            return Response(text="ok", tool_calls=[],
                            stop_reason="end_turn", usage={})

    _prev = CONFIG.coordinator_mode_enabled
    CONFIG.coordinator_mode_enabled = True
    try:
        parent = QueryEngine(
            client=_SnoopClient(), max_turns=2,
            budget=IterationBudget(max_iterations=10),
        )
        parent.run(
            user_message="initial query",
            system_prompt="base", tools=all_registered(),
        )
        # The first turn's messages must include the original user query
        # AND the worker-tools-context block.
        joined_user_text = ""
        for m in captured_messages:
            if m.get("role") != "user":
                continue
            content = m.get("content")
            if isinstance(content, str):
                joined_user_text += content
            elif isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "text":
                        joined_user_text += b.get("text", "")
        assert "initial query" in joined_user_text
        # Worker-tools-context block markers.
        assert "worker types" in joined_user_text.lower() or (
            "agent_type" in joined_user_text.lower()
        ), (
            "G3-2 user context must be injected into the first user message "
            "when coordinator_mode is on (Codex iter-1 #3)"
        )
        # Per get_coordinator_user_context: lists explore/plan/verify/build.
        for at in ("explore", "build", "verify"):
            assert at in joined_user_text, f"Worker type {at!r} missing from user context"
    finally:
        CONFIG.coordinator_mode_enabled = _prev


def test_coordinator_user_context_NOT_injected_for_subagent():
    """Sub-agents must NOT get the coordinator user context block (they
    are workers, not coordinators)."""
    from core import QueryEngine
    from core.budget import IterationBudget
    from runtime.config import CONFIG
    from tools import all_registered

    captured = []

    class _SnoopClient:
        def __init__(self):
            self.model_id = "x"
            self.mock_mode = True

        def chat(self, messages, system, tools, max_tokens, temperature,
                 thinking_enabled, thinking_budget):
            from runtime.bedrock_client import Response
            captured.extend(list(messages))
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
        child.run(user_message="explore x", system_prompt="base",
                  tools=all_registered())
        joined = ""
        for m in captured:
            if m.get("role") != "user":
                continue
            content = m.get("content")
            if isinstance(content, str):
                joined += content
            elif isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "text":
                        joined += b.get("text", "")
        assert "explore x" in joined
        # No worker-tools-context block leaked to the sub-agent.
        # Codex iter-2 finding #3 tightening: assert markers UNIQUE to
        # the coordinator user-context block (NOT the Phase-7 deferred-
        # tool reminder, which legitimately mentions tool names like
        # create_word in any agent's message stream).
        joined_lower = joined.lower()
        # Scratchpad section markers — only emitted by get_coordinator_user_context.
        assert "without permission prompts" not in joined
        assert "scratchpad directory" not in joined_lower
        # The exact phrase "worker types are" / "Workers have access" that
        # only appears in get_coordinator_user_context.
        assert "workers have access to v5's" not in joined.lower()
        assert "worker types are:" not in joined.lower()
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
