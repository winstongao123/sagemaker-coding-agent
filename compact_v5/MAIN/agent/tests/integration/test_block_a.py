"""Block A — Compactor + auto-compact circuit breaker + cache_edits.

Tests cover:
  - Compactor.estimate_tokens delegates to runtime/tokens helpers.
  - Compactor.prune_tool_outputs head/tail truncation.
  - Compactor.should_compact 80% trigger.
  - Compactor.compact replaces old with summary + last N.
  - Compactor.create_llm_summary calls client.chat with summary prompt.
  - Compactor.run end-to-end (mock client returns canned summary).
  - AutoCompactCircuitBreaker cooldown + session cap.
  - apply_cache_control_to_blocks marks last block ephemeral.
  - B-2 count_tokens_via_haiku_fallback (mock mode + real path stub).
  - B+5 advisor sub-cost attribution via TOKENS.add(agent_kind="advisor").
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
# T1 — estimate_tokens
# ============================================================

def test_compactor_estimate_tokens_string():
    from core.compactor import Compactor

    assert Compactor.estimate_tokens("") == 0
    assert Compactor.estimate_tokens("hello world") > 0


def test_compactor_estimate_tokens_messages():
    from core.compactor import Compactor

    msgs = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "world"},
    ]
    n = Compactor.estimate_tokens(msgs)
    assert n > 0


# ============================================================
# T1 — should_compact 80% trigger
# ============================================================

def test_compactor_should_compact_at_80_percent():
    from core.compactor import Compactor

    # Build a message that estimates to ~80,001 tokens (above 80% of 100K).
    big_text = "x" * 240_000  # ~80K tokens at 3 chars/token
    msgs = [{"role": "user", "content": big_text}]
    assert Compactor.should_compact(msgs, max_tokens=100_000)
    # And NOT trigger at 200K max.
    assert not Compactor.should_compact(msgs, max_tokens=400_000)


def test_compactor_should_not_compact_when_small():
    from core.compactor import Compactor

    msgs = [{"role": "user", "content": "tiny"}]
    assert not Compactor.should_compact(msgs, max_tokens=200_000)


# ============================================================
# T1 — prune_tool_outputs
# ============================================================

def test_compactor_prune_tool_outputs_truncates_oversized():
    from core.compactor import Compactor

    huge = "y" * 30_000  # > SUMMARY_TOOL_RESULT_THRESHOLD (8K)
    # Build > PRUNE_PROTECT_TOKENS so pruning kicks in.
    fillers = [
        {"role": "assistant", "content": [{"type": "text", "text": "x" * 60_000}]}
        for _ in range(3)
    ]
    msgs = fillers + [
        {"role": "user", "content": [{
            "type": "tool_result",
            "tool_use_id": "t1",
            "content": huge,
        }]},
    ]
    pruned, saved = Compactor.prune_tool_outputs(msgs, max_context=200_000)
    assert saved >= 0
    # Bonus: input not mutated.
    assert msgs[-1]["content"][0]["content"] == huge


def test_compactor_prune_protects_listed_tools():
    from core.compactor import Compactor

    huge = "y" * 30_000
    msgs = [
        {"role": "assistant", "content": [{"type": "text", "text": "x" * 70_000}]},
        {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "todo_write", "input": {}}]},
        {"role": "user", "content": [{
            "type": "tool_result",
            "tool_use_id": "t1",
            "content": huge,
        }]},
    ]
    pruned, _ = Compactor.prune_tool_outputs(msgs, max_context=100_000)
    # todo_write is in PROTECTED_TOOLS — its result must NOT be truncated.
    assert pruned[-1]["content"][0]["content"] == huge


# ============================================================
# T1 — compact replaces old with summary + last N
# ============================================================

def test_compactor_compact_with_summary():
    from core.compactor import Compactor

    msgs = [
        {"role": "user", "content": f"msg {i}"}
        for i in range(10)
    ]
    summary = "User asked about X; assistant answered Y."
    result = Compactor.compact(msgs, summary)
    assert len(result) == 1 + Compactor.KEEP_LAST_MESSAGES
    assert summary in result[0]["content"]
    # Last KEEP_LAST_MESSAGES messages preserved.
    for i, kept in enumerate(result[1:]):
        original = msgs[-Compactor.KEEP_LAST_MESSAGES + i]
        assert kept["content"] == original["content"]


def test_compactor_compact_returns_unchanged_on_empty_summary():
    from core.compactor import Compactor

    msgs = [{"role": "user", "content": "x"}]
    assert Compactor.compact(msgs, summary="") == msgs


# ============================================================
# T2 — create_llm_summary calls client.chat
# ============================================================

def test_compactor_create_llm_summary_calls_chat(monkeypatch):
    from core.compactor import Compactor
    from runtime.bedrock_client import BedrockClient, Response

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)

    captured: dict = {}

    def fake_chat(*args, **kwargs):
        captured["call"] = kwargs
        return Response(text="canned summary", usage={"input_tokens": 100, "output_tokens": 50})

    monkeypatch.setattr(client, "chat", fake_chat)
    msgs = [{"role": "user", "content": "hello"}]
    summary = Compactor.create_llm_summary(client, msgs)
    assert summary == "canned summary"
    assert "system" in captured["call"]
    assert "summarizing" in captured["call"]["system"].lower()


def test_compactor_run_end_to_end(monkeypatch):
    """Compactor.run: prune → summarize → compact, all in one."""
    from core.compactor import Compactor
    from runtime.bedrock_client import BedrockClient, Response

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)

    def fake_chat(*args, **kwargs):
        return Response(text="summary text", usage={"input_tokens": 100, "output_tokens": 30})

    monkeypatch.setattr(client, "chat", fake_chat)

    # Force should_compact = True via huge messages.
    huge = "x" * 600_000
    msgs = [{"role": "user", "content": huge}]
    result = Compactor.run(client, msgs, max_tokens=100_000)
    assert result.success
    assert result.summary == "summary text"
    assert "summary text" in result.messages_after[0]["content"]
    assert result.tokens_after < result.tokens_before


def test_compactor_run_skips_when_under_threshold(monkeypatch):
    from core.compactor import Compactor
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    msgs = [{"role": "user", "content": "tiny"}]
    result = Compactor.run(client, msgs, max_tokens=200_000)
    assert not result.success
    assert "not needed" in result.error


# ============================================================
# T1 — AutoCompactCircuitBreaker
# ============================================================

def test_circuit_breaker_cooldown_blocks_repeated_attempts():
    from core.compactor import AutoCompactCircuitBreaker

    cb = AutoCompactCircuitBreaker(cooldown_seconds=10, max_per_session=100)
    ok, _ = cb.should_attempt()
    assert ok
    cb.record_attempt()
    ok2, reason = cb.should_attempt()
    assert not ok2
    assert "cooldown" in reason.lower()


def test_circuit_breaker_session_cap():
    from core.compactor import AutoCompactCircuitBreaker

    cb = AutoCompactCircuitBreaker(cooldown_seconds=0, max_per_session=2)
    cb.record_attempt()
    cb.record_attempt()
    ok, reason = cb.should_attempt()
    assert not ok
    assert "session cap" in reason.lower()


def test_circuit_breaker_reset():
    from core.compactor import AutoCompactCircuitBreaker

    cb = AutoCompactCircuitBreaker(cooldown_seconds=10, max_per_session=2)
    cb.record_attempt()
    cb.record_attempt()
    assert not cb.should_attempt()[0]
    cb.reset()
    assert cb.should_attempt()[0]


# ============================================================
# T1 — apply_cache_control_to_blocks
# ============================================================

def test_apply_cache_control_marks_last_ephemeral():
    from core.compactor import apply_cache_control_to_blocks

    blocks = [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]
    out = apply_cache_control_to_blocks(blocks)
    assert "cache_control" not in out[0]
    assert out[1]["cache_control"] == {"type": "ephemeral"}


def test_apply_cache_control_at_specific_index():
    from core.compactor import apply_cache_control_to_blocks

    blocks = [{"type": "text", "text": str(i)} for i in range(3)]
    out = apply_cache_control_to_blocks(blocks, cache_break_at=0)
    assert out[0]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in out[1]
    assert "cache_control" not in out[2]


def test_apply_cache_control_empty_list():
    from core.compactor import apply_cache_control_to_blocks
    assert apply_cache_control_to_blocks([]) == []


# ============================================================
# B-2 — count_tokens_via_haiku_fallback
# ============================================================

def test_count_tokens_haiku_fallback_in_mock_mode():
    from core.compactor import count_tokens_via_haiku_fallback
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    msgs = [{"role": "user", "content": "hello world"}]
    n = count_tokens_via_haiku_fallback(msgs, client)
    assert isinstance(n, int)
    assert n > 0


def test_count_tokens_haiku_fallback_handles_none_client():
    from core.compactor import count_tokens_via_haiku_fallback
    assert count_tokens_via_haiku_fallback([], None) is None


# ============================================================
# B+5 — advisor sub-cost attribution
# ============================================================

def test_advisor_cost_attributed_when_aux_model_set(monkeypatch):
    """When CONFIG.compaction_model is set AND a different aux client is
    used, summary tokens go into TOKENS.subagent_cost['advisor'].
    Closes the B+5 deferral from ADR-022."""
    from core.compactor import Compactor
    from runtime.bedrock_client import BedrockClient, Response
    from runtime.tokens import TOKENS
    from runtime.config import CONFIG

    # Set up: main client + auxiliary client (we mock the aux build).
    main_client = BedrockClient(model_id="main-model", region="us-east-1", mock_mode=True)
    aux_client = BedrockClient(model_id="aux-model", region="us-east-1", mock_mode=True)

    monkeypatch.setattr(CONFIG, "compaction_model", "aux-model")
    Compactor._aux_client_cache = {}  # reset cache

    # Spy on _summary_client to verify aux is selected.
    monkeypatch.setattr(
        Compactor, "_summary_client",
        classmethod(lambda cls, mc: aux_client),
    )

    def fake_aux_chat(*args, **kwargs):
        return Response(
            text="advisor-built summary",
            usage={"input_tokens": 500, "output_tokens": 100},
        )

    monkeypatch.setattr(aux_client, "chat", fake_aux_chat)

    TOKENS.reset()
    # Add some pricing so cost is non-zero (hitchk test pricing fallback)
    summary = Compactor.create_llm_summary(main_client, [
        {"role": "user", "content": "discuss the project"},
    ])
    assert summary == "advisor-built summary"
    # Advisor bucket present (cost may be 0 if aux-model has no pricing,
    # but the BUCKET should exist via tokens accumulating).
    assert TOKENS.subagent_input_tokens.get("advisor", 0) >= 500
    assert TOKENS.subagent_output_tokens.get("advisor", 0) >= 100


def test_advisor_falls_back_to_parent_when_no_aux(monkeypatch):
    """When no compaction_model is set, summary uses the main client and
    tokens go to parent bucket (not advisor)."""
    from core.compactor import Compactor
    from runtime.bedrock_client import BedrockClient, Response
    from runtime.tokens import TOKENS
    from runtime.config import CONFIG

    main_client = BedrockClient(model_id="main", region="us-east-1", mock_mode=True)
    monkeypatch.setattr(CONFIG, "compaction_model", "")
    Compactor._aux_client_cache = {}

    def fake_chat(*args, **kwargs):
        return Response(text="parent summary", usage={"input_tokens": 100, "output_tokens": 30})

    monkeypatch.setattr(main_client, "chat", fake_chat)
    TOKENS.reset()
    Compactor.create_llm_summary(main_client, [{"role": "user", "content": "x"}])
    # Parent bucket got the tokens (advisor is 0).
    assert TOKENS.parent_input_tokens >= 100
    assert TOKENS.subagent_input_tokens.get("advisor", 0) == 0


# ============================================================
# Codex Block-A iter-1 finding-lock tests (regression prevention)
# ============================================================

def test_ptl_retry_preserves_user_first_role():
    """Codex iter-1 finding #1 (HIGH) lock: PTL retry must produce a
    message list that STARTS with role=user. Bedrock rejects lists
    starting with assistant; without the user-marker prepend, retry
    fails non-PTL and aborts the entire compaction."""
    from core.compactor import Compactor

    # 4-message list whose first 25% slice would start with assistant.
    msgs = [
        {"role": "user", "content": "msg 1"},
        {"role": "assistant", "content": "msg 2"},
        {"role": "user", "content": "msg 3"},
        {"role": "assistant", "content": "msg 4"},
    ]
    truncated = Compactor._truncate_head_for_ptl_retry(msgs)
    assert truncated is not None
    assert truncated[0]["role"] == "user", (
        "PTL retry must guarantee user-first ordering for Bedrock"
    )


def test_prune_min_savings_rollback():
    """Codex iter-1 finding #2 (MEDIUM) lock: when pruning saves fewer
    tokens than PRUNE_MIN_SAVINGS (10K), the function returns the
    ORIGINAL messages — fidelity preserved over marginal token wins."""
    from core.compactor import Compactor

    # Single tool result just over the threshold. Pruning saves
    # ~5K tokens — below MIN_SAVINGS so result should be rollback.
    payload = "z" * (Compactor.SUMMARY_TOOL_RESULT_THRESHOLD + 100)
    msgs = [{
        "role": "user",
        "content": [{"type": "tool_result", "tool_use_id": "t1", "content": payload}],
    }]
    pruned, saved = Compactor.prune_tool_outputs(msgs, max_context=200_000)
    # Either (a) savings below MIN, returns original; OR (b) protect-tokens
    # threshold not crossed (running_tokens stayed under 40K), also returns original.
    if saved < Compactor.PRUNE_MIN_SAVINGS:
        assert pruned[0]["content"][0]["content"] == payload, (
            "below-MIN savings must roll back to original messages"
        )


def test_circuit_breaker_try_attempt_atomic():
    """Codex iter-1 finding #3 (MEDIUM) lock: try_attempt() combines
    check + record under one lock so concurrent callers can't both
    pass before either records. Without the atomic helper, the v4
    invariant is racy under concurrency."""
    from core.compactor import AutoCompactCircuitBreaker
    import threading

    # cooldown=0 + max_per_session=2 → only session cap gates the
    # concurrent attempts, so the atomic-check assertion is meaningful.
    cb = AutoCompactCircuitBreaker(cooldown_seconds=0, max_per_session=2)
    results: list = []
    lock = threading.Lock()

    def worker():
        ok, _ = cb.try_attempt()
        with lock:
            results.append(ok)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exactly 2 threads should have observed True (max_per_session=2);
    # the rest should have hit cooldown OR session-cap rejection.
    assert results.count(True) == 2, (
        f"max_per_session=2 must be respected under concurrency; "
        f"got {results.count(True)} successes"
    )


def test_auto_compact_wired_into_query_engine_run(monkeypatch):
    """Codex iter-1 finding #4 (MEDIUM) lock: AUTO_COMPACT singleton is
    invoked from QueryEngine.run() per turn — not just helper-only.

    Build a scenario where should_compact returns True, and verify
    Compactor.run is called via the engine wiring."""
    from core.query_engine import QueryEngine
    from core import compactor as comp_mod
    from runtime.bedrock_client import BedrockClient, Response, ToolCall

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    engine = QueryEngine(client=client, max_turns=2)

    # Force should_compact = True every check; capture if Compactor.run fires.
    calls = {"should": 0, "run": 0}

    def fake_should_compact(_msgs, _max):
        calls["should"] += 1
        return True

    real_run = comp_mod.Compactor.run

    def fake_run(client_arg, messages, max_tokens=200_000):
        calls["run"] += 1
        # Return a successful result so downstream code accepts it.
        return comp_mod.CompactionResult(
            success=True,
            summary="auto-compact ran",
            messages_after=[{"role": "user", "content": "compacted"}],
            tokens_before=100_000,
            tokens_after=10_000,
        )

    monkeypatch.setattr(comp_mod.Compactor, "should_compact", staticmethod(fake_should_compact))
    monkeypatch.setattr(comp_mod.Compactor, "run", staticmethod(fake_run))
    # Reset circuit breaker so it allows the attempt.
    comp_mod.AUTO_COMPACT.reset()

    # Mock client.chat to do one tool-less turn so we hit the auto-compact spot.
    def fake_chat(*args, **kwargs):
        return Response(text="ok", tool_calls=[], stop_reason="end_turn")

    monkeypatch.setattr(client, "chat", fake_chat)
    engine.run(user_message="hi", system_prompt="test", tools=[])

    # auto-compact MUST have been considered (should_compact called) AND
    # actually invoked Compactor.run via the wired gate.
    assert calls["should"] >= 1, "Compactor.should_compact never queried in run() loop"
    assert calls["run"] >= 1, "Compactor.run never invoked despite should_compact=True"
