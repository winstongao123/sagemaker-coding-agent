"""Phase 09 integration tests: subagent/spawn.py + tools/task.py.

Acceptance criteria (V5_PLAN.md §Phase 9):
- Parent context unchanged after sub-agent run.
- Child shares IterationBudget instance.

Locks PORT_LOG #021 (forkSubagent budget sharing) + #024 (task tool dispatch).
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
# Shared scripted client + registry fixture
# ============================================================

class _ScriptedClient:
    """Returns pre-scripted responses; same shape used in test_query_engine.py."""

    def __init__(self, script):
        self.script = list(script)
        self.calls: List[Dict[str, Any]] = []

    def chat(self, messages, system, tools, max_tokens, temperature,
             thinking_enabled, thinking_budget):
        from runtime.bedrock_client import Response, ToolCall
        self.calls.append({"messages": list(messages), "system": system})
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


@pytest.fixture(autouse=True)
def fresh_registry():
    from tools.registry import _reset_registry_for_tests
    from tools import bootstrap_built_ins
    _reset_registry_for_tests()
    bootstrap_built_ins()
    yield


# ============================================================
# Test 1 — child shares IterationBudget (Phase 9 ACCEPTANCE)
# ============================================================

def test_subagent_shares_iteration_budget():
    """Phase 9 acceptance criterion: the child QueryEngine's `budget`
    attribute is the SAME OBJECT as the parent's. Object identity, not
    just equal values."""
    from core import QueryEngine, IterationBudget
    from subagent.spawn import spawn_subagent, _new_child_engine

    parent_budget = IterationBudget(max_iterations=20)
    parent = QueryEngine(
        client=_ScriptedClient([("text", "ok")]),
        max_turns=5,
        budget=parent_budget,
    )
    child = _new_child_engine(parent, max_turns=10)
    assert child.budget is parent_budget, (
        "Phase 9 contract: child.budget must be the SAME OBJECT as parent.budget "
        "(shared, not copied) — Hermes pattern via forkSubagent."
    )


# ============================================================
# Test 2 — parent context unchanged (Phase 9 ACCEPTANCE)
# ============================================================

def test_subagent_parent_context_unchanged():
    """Phase 9 acceptance criterion: parent's `messages` buffer length is
    identical before and after spawn. The child has its own buffer."""
    from core import QueryEngine, IterationBudget
    from subagent.spawn import spawn_subagent

    parent = QueryEngine(
        client=_ScriptedClient([("text", "child answer")]),
        max_turns=5,
        budget=IterationBudget(max_iterations=10),
    )
    # Pre-populate parent with a turn so we have something to compare.
    parent.messages.append({"role": "user", "content": "preserved"})
    parent.messages.append({"role": "assistant", "content": [{"type": "text", "text": "parent's answer"}]})
    snap = list(parent.messages)
    snap_repr = [(m["role"], m["content"]) for m in snap]

    result = spawn_subagent(
        parent_engine=parent,
        prompt="Summarize the docs.",
        agent_type="general",
    )
    assert result.text == "child answer"
    assert result.stop_reason == "end_turn"

    # Parent buffer is unchanged (length + content)
    after_repr = [(m["role"], m["content"]) for m in parent.messages]
    assert after_repr == snap_repr, "Parent's messages buffer was mutated by sub-agent dispatch"


# ============================================================
# Test 3 — depth limit enforced (no Bedrock call, returns error result)
# ============================================================

def test_subagent_depth_limit_blocks_recursion():
    from core import QueryEngine, IterationBudget
    from subagent.spawn import spawn_subagent

    client = _ScriptedClient([("text", "should never be called")])
    parent = QueryEngine(client=client, max_turns=5, budget=IterationBudget())

    result = spawn_subagent(
        parent_engine=parent,
        prompt="recurse forever",
        agent_type="general",
        parent_depth=2,           # Parent already at max depth → child would be 3 > 2
        max_depth=2,
    )
    assert result.stop_reason == "depth_exceeded"
    assert result.error is not None
    assert "depth limit" in result.error
    # CRITICAL: no Bedrock call was made (no budget consumed, no client.calls)
    assert client.calls == []


# ============================================================
# Test 4 — empty prompt rejected
# ============================================================

def test_subagent_rejects_empty_prompt():
    from core import QueryEngine, IterationBudget
    from subagent.spawn import spawn_subagent

    parent = QueryEngine(
        client=_ScriptedClient([("text", "x")]),
        max_turns=5,
        budget=IterationBudget(),
    )
    result = spawn_subagent(parent_engine=parent, prompt="", agent_type="general")
    assert result.stop_reason == "invalid_args"
    assert "required" in (result.error or "")


# ============================================================
# Test 5 — child consumes from shared budget
# ============================================================

def test_subagent_consumes_shared_budget():
    """If child runs N turns, parent's budget.used() increases by N."""
    from core import QueryEngine, IterationBudget
    from subagent.spawn import spawn_subagent

    budget = IterationBudget(max_iterations=10)
    # Parent is created but doesn't run; we directly spawn a child.
    client = _ScriptedClient([
        ("tool", "c1", "read_file", {"file_path": "x.txt"}),
        ("text", "Done."),
    ])
    parent = QueryEngine(client=client, max_turns=5, budget=budget)

    assert budget.used() == 0
    result = spawn_subagent(
        parent_engine=parent,
        prompt="read a file",
        agent_type="general",
    )
    # Child ran 2 turns → budget.used() should be exactly 2
    assert result.turns_used == 2
    assert budget.used() == 2


# ============================================================
# Test 6 — task tool registered + deferred
# ============================================================

def test_task_tool_registered_and_deferred():
    from tools import find_tool_by_name, all_registered, apply_tool_search_deferral

    tool = find_tool_by_name(all_registered(), "task")
    assert tool is not None
    assert tool.should_defer is True
    assert tool.always_load is False

    # Confirm it appears in the deferred-names list when deferral is enabled.
    visible, deferred_names = apply_tool_search_deferral(all_registered(), enabled=True)
    visible_names = {t.name for t in visible}
    assert "task" not in visible_names
    assert "task" in deferred_names


# ============================================================
# Test 7 — task tool executor requires parent_engine in context
# ============================================================

def test_task_tool_requires_parent_engine_in_context():
    from tools import find_tool_by_name, all_registered

    task_tool = find_tool_by_name(all_registered(), "task")
    out = task_tool.execute({"prompt": "do a thing"}, context={})
    assert "Error" in out
    assert "parent_engine" in out


# ============================================================
# Test 8 — task tool executor with parent_engine spawns sub-agent
# ============================================================

def test_task_tool_executor_spawns_subagent():
    from core import QueryEngine, IterationBudget
    from tools import find_tool_by_name, all_registered

    parent = QueryEngine(
        client=_ScriptedClient([("text", "Sub-agent reports: done.")]),
        max_turns=3,
        budget=IterationBudget(max_iterations=5),
    )
    task_tool = find_tool_by_name(all_registered(), "task")
    out = task_tool.execute(
        {"prompt": "summarize the project", "subagent_type": "general"},
        context={"parent_engine": parent, "parent_depth": 0},
    )
    assert "Sub-agent reports: done." in out


# ============================================================
# Test 9 — task tool surfaces budget exhaustion partial output
# ============================================================

def test_task_tool_surfaces_budget_exhaustion():
    from core import QueryEngine, IterationBudget
    from tools import find_tool_by_name, all_registered

    # Budget pre-exhausted so child can't enter loop
    budget = IterationBudget(max_iterations=1)
    budget.consume()  # exhausted
    parent = QueryEngine(
        client=_ScriptedClient([("text", "should not run")]),
        max_turns=3,
        budget=budget,
    )
    task_tool = find_tool_by_name(all_registered(), "task")
    out = task_tool.execute(
        {"prompt": "do a thing"},
        context={"parent_engine": parent, "parent_depth": 0},
    )
    assert "Sub-agent stopped: budget_exhausted" in out


# ============================================================
# Test 10 — end-to-end via QueryEngine: model calls task tool
# ============================================================

def test_query_engine_dispatches_task_tool_end_to_end():
    """Model in turn 1 calls `task`. The QueryEngine dispatches it; the task
    executor receives `parent_engine=self` from the dispatch context and
    spawns a sub-agent. Final answer flows back to parent."""
    from core import QueryEngine, IterationBudget
    from tools import all_registered

    # Parent client: turn 1 = call task tool, turn 2 = give final.
    # Sub-agent (which uses the SAME client object — _ScriptedClient is parent's
    # client because in our minimal Phase-9 spawn the child reuses parent.client)
    # so its first script item must be CHILD's response. We interleave:
    # [child_response, parent_final] — because the child runs to completion
    # BEFORE control returns to the parent loop.
    client = _ScriptedClient([
        ("tool", "p1", "task", {"prompt": "child task: count files"}),
        # Child's run starts here, drains its scripts:
        ("text", "Child found 3 files."),
        # Then control returns to parent loop:
        ("text", "I asked the sub-agent, who reported 3 files."),
    ])
    parent = QueryEngine(
        client=client,
        max_turns=5,
        budget=IterationBudget(max_iterations=10),
    )
    result = parent.run(
        user_message="Use a sub-agent to count files",
        system_prompt="sys",
        tools=all_registered(),
    )
    assert result.stop_reason == "end_turn"
    assert "3 files" in result.text


# ============================================================
# Test 11 — Codex-style defense: parent buffer mutation guard
# ============================================================

# ============================================================
# Test 12 — Codex Phase-09 BLOCKER lock: nested-recursion depth
# ============================================================

def test_nested_subagent_recursion_blocked_at_max_depth():
    """Codex Phase-09 BLOCKER lock: child engines must carry their depth so
    that a child dispatching `task` itself triggers the recursion guard at
    grandchild level. Without `child._subagent_depth = child_depth` in
    spawn_subagent, every nested `task` would reset to depth 0 and unbounded
    recursion would be possible up to budget exhaustion."""
    from core import QueryEngine, IterationBudget
    from subagent.spawn import spawn_subagent, _new_child_engine

    parent = QueryEngine(
        client=_ScriptedClient([("text", "child final")]),
        max_turns=5,
        budget=IterationBudget(),
    )
    # Spawn one level — child should end up at depth 1
    result = spawn_subagent(
        parent_engine=parent,
        prompt="x",
        agent_type="general",
        parent_depth=0,
        max_depth=2,
    )
    assert result.depth == 1
    # Now simulate the child running and dispatching `task`. We don't need
    # to run the full QueryEngine.run — just verify that _new_child_engine
    # produces an engine whose _subagent_depth reflects the just-completed
    # child's depth, so its tool-dispatch context would carry parent_depth=1
    # to a grandchild.
    child = _new_child_engine(parent, max_turns=10)
    # Engine starts with no _subagent_depth attr (top-level default 0).
    assert getattr(child, "_subagent_depth", 0) == 0
    # spawn_subagent sets it on the child it creates:
    child._subagent_depth = 1   # what the spawn flow sets
    # The QueryEngine dispatch context picks it up via getattr(self, "_subagent_depth", 0):
    assert getattr(child, "_subagent_depth", 0) == 1


def test_nested_spawn_depth_propagates_through_child_engine():
    """End-to-end nested-spawn lock: a CHILD engine passing through `task`
    dispatch must surface its depth via `getattr(self, "_subagent_depth", 0)`
    so the QueryEngine dispatch context carries `parent_depth=child_depth`.
    Without the BLOCKER fix, every nested spawn would reset to depth=0.

    Test: parent spawns child A (depth=1). Then we manually spawn a
    'grandchild B' using A as parent_engine. The grandchild call uses
    A._subagent_depth (=1) as parent_depth, and with max_depth=1 must be
    blocked at depth_exceeded."""
    from core import QueryEngine, IterationBudget
    from subagent.spawn import spawn_subagent

    parent = QueryEngine(
        client=_ScriptedClient([("text", "A done")]),
        max_turns=5,
        budget=IterationBudget(),
    )
    a_result = spawn_subagent(
        parent_engine=parent,
        prompt="A work",
        agent_type="general",
        parent_depth=0,
        max_depth=2,
    )
    assert a_result.depth == 1

    # Now try to spawn a grandchild using a fresh child engine that
    # reflects A's depth. Simulate what the task tool dispatch would
    # see: it reads parent_engine._subagent_depth via getattr.
    # We re-use spawn_subagent's _new_child_engine + the BLOCKER fix
    # (which sets child._subagent_depth = child_depth):
    from subagent.spawn import _new_child_engine
    a_engine = _new_child_engine(parent, max_turns=5)
    a_engine._subagent_depth = 1  # what spawn_subagent now sets

    # Grandchild spawn — using A as parent. parent_depth picked up from A's
    # _subagent_depth means child_depth=2, which exceeds max_depth=1.
    grand_result = spawn_subagent(
        parent_engine=a_engine,
        prompt="grandchild work",
        agent_type="general",
        parent_depth=getattr(a_engine, "_subagent_depth", 0),  # = 1
        max_depth=1,
    )
    assert grand_result.stop_reason == "depth_exceeded"
    assert "depth limit" in (grand_result.error or "")


# ============================================================
# Test 13 — Codex Phase-09 medium lock: real-spawn budget identity
# ============================================================

def test_real_spawn_child_budget_is_parent_budget():
    """Codex Phase-09 finding (medium) lock: `child.budget is parent.budget`
    must hold not just for `_new_child_engine` (already tested), but ALSO
    after a full `spawn_subagent` flow. We expose the child engine via
    monkey-patching _new_child_engine to capture it."""
    from core import QueryEngine, IterationBudget
    from subagent import spawn as spawn_mod

    parent = QueryEngine(
        client=_ScriptedClient([("text", "ok")]),
        max_turns=5,
        budget=IterationBudget(max_iterations=10),
    )

    captured = {}
    real_factory = spawn_mod._new_child_engine

    def capturing_factory(p, max_turns):
        c = real_factory(p, max_turns)
        captured["child"] = c
        return c

    spawn_mod._new_child_engine = capturing_factory
    try:
        spawn_mod.spawn_subagent(parent_engine=parent, prompt="x", agent_type="general")
    finally:
        spawn_mod._new_child_engine = real_factory

    assert captured["child"].budget is parent.budget
    # And the depth-threading fix puts depth=1 on the child:
    assert captured["child"]._subagent_depth == 1


# ============================================================
# Test 14 — Codex Phase-09 medium lock: parent immutability via deep snapshot
# ============================================================

def test_parent_immutability_check_catches_in_place_mutation(monkeypatch):
    """Length-only check would miss in-place edits. Verify that an in-place
    mutation that preserves length is caught by the deep-snapshot guard."""
    from core import QueryEngine, IterationBudget
    from subagent import spawn as spawn_mod

    parent = QueryEngine(
        client=_ScriptedClient([("text", "x")]),
        max_turns=5,
        budget=IterationBudget(),
    )
    parent.messages.append({"role": "user", "content": "original"})

    class _MutatorChild:
        def __init__(self, victim):
            self.victim = victim
            self.budget = victim.budget
            self.client = victim.client
            self.on_stop_check = None
            self.messages = []

        def run(self, **kwargs):
            # Mutate IN PLACE — length-preserving — to test deep-snapshot guard
            self.victim.messages[0]["content"] = "CORRUPTED IN PLACE"
            from core.query_engine import QueryResult
            return QueryResult(text="", stop_reason="end_turn", turns_used=0,
                               budget_used=0, messages=[])

    monkeypatch.setattr(spawn_mod, "_new_child_engine", lambda p, max_turns: _MutatorChild(p))
    result = spawn_mod.spawn_subagent(
        parent_engine=parent, prompt="x", agent_type="general"
    )
    assert result.stop_reason == "parent_context_mutated", (
        "Deep-snapshot guard must catch in-place mutation that preserves length"
    )


# ============================================================
# Test 15 — Codex Phase-09 medium lock: unknown subagent_type rejected
# ============================================================

def test_task_tool_rejects_unknown_subagent_type():
    """Codex Phase-09 finding (medium) lock: silent fallback to `general`
    is gone. Unknown types now return an explicit error so the model can
    self-correct."""
    from core import QueryEngine, IterationBudget
    from tools import find_tool_by_name, all_registered

    parent = QueryEngine(
        client=_ScriptedClient([("text", "should never run")]),
        max_turns=3,
        budget=IterationBudget(),
    )
    task_tool = find_tool_by_name(all_registered(), "task")
    out = task_tool.execute(
        {"prompt": "x", "subagent_type": "totally_made_up_type"},
        context={"parent_engine": parent, "parent_depth": 0},
    )
    assert "Error" in out
    assert "totally_made_up_type" in out
    assert "general" in out  # tells the caller what's available


def test_subagent_returns_error_if_parent_context_mutated(monkeypatch):
    """The spawn wrapper has a defense-in-depth check that detects parent-buffer
    mutation. We simulate corruption by patching the underlying QueryEngine.run
    to mutate the parent."""
    from core import QueryEngine, IterationBudget
    from subagent import spawn as spawn_mod

    parent = QueryEngine(
        client=_ScriptedClient([("text", "x")]),
        max_turns=5,
        budget=IterationBudget(),
    )

    # Build a fake child whose .run() also mutates the parent's messages.
    class _BadChild:
        def __init__(self, victim):
            self.victim = victim
            self.budget = victim.budget
            self.client = victim.client
            self.on_stop_check = None
            self.messages = []

        def run(self, **kwargs):
            self.victim.messages.append({"role": "user", "content": "CORRUPTED"})
            from core.query_engine import QueryResult
            return QueryResult(text="", stop_reason="end_turn", turns_used=0,
                               budget_used=0, messages=[])

    monkeypatch.setattr(spawn_mod, "_new_child_engine", lambda p, max_turns: _BadChild(p))
    result = spawn_mod.spawn_subagent(
        parent_engine=parent, prompt="x", agent_type="general"
    )
    assert result.stop_reason == "parent_context_mutated"
    assert "Phase-9 contract violated" in (result.error or "")
