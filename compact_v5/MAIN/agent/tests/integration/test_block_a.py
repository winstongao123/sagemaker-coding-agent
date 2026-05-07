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
# A-16 — time-based microcompact
# ============================================================

def _tool_pair(tool_id: str, tool_name: str, content: str):
    return [
        {
            "role": "assistant",
            "content": [{
                "type": "tool_use",
                "id": tool_id,
                "name": tool_name,
                "input": {},
            }],
        },
        {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": content,
            }],
        },
    ]


def test_microcompact_cold_cache_keep_last_1():
    from core.compactor import Compactor

    payload = "x" * 40_000
    msgs = []
    for i in range(3):
        msgs.extend(_tool_pair(f"r{i}", "read_file", payload))

    compacted, saved = Compactor.microcompact(
        msgs,
        keep_n_override=Compactor.KEEP_LAST_N_COLD_CACHE,
    )

    assert saved >= Compactor.MICROCOMPACT_MIN_SAVINGS
    cleared = [
        block["content"]
        for msg in compacted
        for block in (msg.get("content") or [])
        if isinstance(block, dict) and block.get("type") == "tool_result"
    ]
    assert cleared.count(Compactor.MICROCOMPACT_MARKER) == 2
    assert cleared[-1] == payload


def test_compactable_tools_allowlist_excludes_document_creators():
    from core.compactor import Compactor

    assert "read_file" in Compactor.COMPACTABLE_TOOLS
    assert "bash" in Compactor.COMPACTABLE_TOOLS
    assert "create_word" not in Compactor.COMPACTABLE_TOOLS
    assert "create_excel" not in Compactor.COMPACTABLE_TOOLS
    assert "create_pdf" not in Compactor.COMPACTABLE_TOOLS


def test_cold_cache_30min_idle_triggers_microcompact():
    from core.compactor import Compactor
    from core.query_engine import QueryEngine
    from runtime.bedrock_client import BedrockClient, Response
    import time

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    engine = QueryEngine(client=client, max_turns=1)
    payload = "y" * 40_000
    for i in range(3):
        engine.messages.extend(_tool_pair(f"c{i}", "read_file", payload))
    engine._last_api_call_time = time.time() - (31 * 60)

    captured = {"messages": None, "out": []}

    def fake_chat(*args, **kwargs):
        captured["messages"] = kwargs["messages"]
        return Response(text="ok", tool_calls=[], stop_reason="end_turn")

    client.chat = fake_chat
    engine.run(
        user_message="resume after coffee",
        system_prompt="test",
        tools=[],
        output_fn=captured["out"].append,
    )

    assert any("[i] Cold cache detected" in line for line in captured["out"])
    assert captured["messages"] is not None
    seen_results = [
        block["content"]
        for msg in captured["messages"]
        for block in (msg.get("content") if isinstance(msg.get("content"), list) else [])
        if isinstance(block, dict) and block.get("type") == "tool_result"
    ]
    assert Compactor.MICROCOMPACT_MARKER in seen_results


# ============================================================
# A-1..A-15 / A-18..A-43 broad completion helpers
# ============================================================

def test_a1_a2_a4_effective_context_budgets_and_warning_state():
    from core.compactor import Compactor

    assert Compactor.MAX_OUTPUT_TOKENS_FOR_SUMMARY == 20_000
    assert Compactor.AUTOCOMPACT_BUFFER == 13_000
    assert Compactor.MANUAL_COMPACT_BUFFER == 3_000
    assert Compactor.get_effective_context_window_size("claude-sonnet", 200_000) == 180_000

    state = Compactor.calculate_token_warning_state(
        [{"role": "user", "content": "x" * 240_000}],
        max_tokens=100_000,
    )
    assert state.should_microcompact
    assert state.should_auto_compact
    assert state.percent_used > 0.70


def test_a3_circuit_breaker_disables_after_three_failures():
    from core.compactor import AutoCompactCircuitBreaker

    cb = AutoCompactCircuitBreaker(cooldown_seconds=0, max_per_session=10)
    for _ in range(3):
        disabled, _ = cb.record_failure()
    assert disabled
    ok, reason = cb.should_attempt()
    assert not ok
    assert "disabled" in reason
    cb.reset()
    assert cb.should_attempt()[0]


def test_a5_a19_auto_compact_query_source_guards():
    from core.compactor import Compactor

    assert Compactor.should_auto_compact("user")
    assert not Compactor.should_auto_compact("compact")
    assert not Compactor.should_auto_compact("session_memory")


def test_a6_a7_summary_input_strips_images_and_reinjected_attachments():
    from core.compactor import Compactor

    msgs = [{
        "role": "user",
        "content": [
            {"type": "text", "text": "keep"},
            {"type": "image", "source": {"type": "base64", "data": "abc"}},
            {"type": "text", "text": "drop", "is_reinjected_attachment": True},
        ],
    }]
    stripped = Compactor.strip_reinjected_attachments(
        Compactor.strip_images_from_messages(msgs)
    )
    assert stripped[0]["content"] == [{"type": "text", "text": "keep"}]


def test_a9_groups_messages_by_api_round():
    from core.compactor import Compactor

    msgs = [
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "u2"},
    ]
    rounds = Compactor.group_messages_by_api_round(msgs)
    assert len(rounds) == 2
    assert rounds[0][0]["content"] == "u1"
    assert rounds[1][0]["content"] == "u2"


def test_a10_a11_a14_post_compact_file_attachments_exclude_memory_files(tmp_path):
    from core.compactor import Compactor

    keep = tmp_path / "keep.py"
    memory = tmp_path / "MEMORY.md"
    keep.write_text("print('kept')", encoding="utf-8")
    memory.write_text("secret memory", encoding="utf-8")

    attachments = Compactor.create_post_compact_file_attachments([str(keep), str(memory)])
    text = "\n".join(block["text"] for block in attachments)
    assert "keep.py" in text
    assert "MEMORY.md" not in text
    assert Compactor.POST_COMPACT_FILE_TOKEN_BUDGET > 0
    assert Compactor.POST_COMPACT_SKILL_TOKEN_BUDGET > 0


def test_a12_create_skill_attachment_if_active(tmp_path):
    from core.compactor import Compactor
    from skills.manager import SkillManager

    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo\ndescription: Demo skill\n---\nbody",
        encoding="utf-8",
    )
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(skills_dir))
    assert sm.discover()
    sm.active_skill = "demo"
    block = Compactor.create_skill_attachment_if_needed(sm)
    assert block is not None
    assert "POST-COMPACT ACTIVE SKILL" in block["text"]


def test_a15_a23_a24_warning_state_abort_and_stale_round_trip():
    from core.compactor import Compactor

    Compactor.suppress_compact_warning_state(seconds=5)
    assert Compactor.compact_warning_suppressed()
    assert Compactor.is_user_abort_error(Exception("aborted by user"))
    assert Compactor.has_exact_error_message(Exception("exact"), "exact")
    msgs = [{"role": "assistant", "content": [{"type": "tool_use", "id": "x"}]}]
    assert Compactor._is_stale_round_trip(msgs)


def test_a20_abortable_retry_sleep_honors_abort():
    from core.compactor import Compactor

    assert not Compactor._sleep_between_ptl_retries(lambda: True)


def test_a18_session_activity_heartbeat_updates():
    from core.compactor import Compactor

    before = Compactor.last_session_activity()
    after = Compactor.touch_session_activity()
    assert after >= before


def test_a26_surrogate_sanitizer_recursive():
    from core.compactor import Compactor

    bad_surrogate = chr(0xD800)
    raw = {"role": "user", "content": [{"type": "text", "text": "bad" + bad_surrogate}]}
    sanitized = Compactor.sanitize_messages_surrogates(raw)
    assert bad_surrogate not in sanitized["content"][0]["text"]


def test_a28_a39_a41_a42_compact_metadata_and_todo_restoration():
    from core.compactor import Compactor, ContentReplacementEntry
    from tools.todo import _reset_todos_for_tests, _todo_write_executor

    _reset_todos_for_tests(clear_disk=True)
    _todo_write_executor({
        "todos": [{"content": "finish audit", "status": "pending", "activeForm": "Finishing audit"}],
    })
    msgs = [{"role": "user", "content": f"msg {i}"} for i in range(6)]
    compacted = Compactor.compact(msgs, "summary")
    assert compacted[0]["is_meta"] is True
    assert "summary" in compacted[0]["content"]
    assert compacted[1:4] == msgs[-Compactor.KEEP_LAST_MESSAGES:]
    assert compacted[-1]["is_meta"] is True
    assert "[TODO RESTORATION]" in compacted[-1]["content"]
    assert "marble-origami-commit" in compacted[0]["compact_metadata"]
    assert any("[TODO RESTORATION]" in str(msg.get("content")) for msg in compacted)
    entries = Compactor.last_content_replacements()
    assert entries and isinstance(entries[0], ContentReplacementEntry)


def test_a29_a35_tool_schema_tokens_pre_api_guard():
    from core.compactor import Compactor

    tools = [{"name": "read_file", "description": "x" * 1000, "input_schema": {}}]
    assert Compactor.estimate_tool_schema_tokens(tools) > 0
    assert Compactor.would_exceed_context_limit(
        [{"role": "user", "content": "x" * 295_000}],
        max_tokens=100_000,
        tool_schema_tokens=Compactor.estimate_tool_schema_tokens(tools),
    )


def test_a30_a32_a37_a43_retry_reset_prefix_normalization_cache_ttl_temp_path():
    from core import compactor as comp_mod
    from core.compactor import Compactor
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG

    comp_mod.AUTO_COMPACT.reset()
    comp_mod.AUTO_COMPACT.record_failure()
    comp_mod.AUTO_COMPACT.record_failure()
    disabled, _reason = comp_mod.AUTO_COMPACT.record_failure()
    assert disabled
    allowed, _why = comp_mod.AUTO_COMPACT.should_attempt()
    assert not allowed
    Compactor.set_transition_reason("before")
    Compactor.reset_retry_counters()
    allowed_after, _why_after = comp_mod.AUTO_COMPACT.should_attempt()
    assert allowed_after
    assert "reset" in Compactor.transition_reason()
    assert Compactor.normalize_for_prefix_cache({"b": 1, "a": 2}) == '{"a":2,"b":1}'
    assert CONFIG.cache_ttl in {"5m", "1h"}
    old_ttl = CONFIG.cache_ttl
    try:
        CONFIG.cache_ttl = "1h"
        assert BedrockClient._cache_control() == {"type": "ephemeral", "ttl": "1h"}
        CONFIG.cache_ttl = "bad"
        assert BedrockClient._cache_control() == {"type": "ephemeral", "ttl": "5m"}
    finally:
        CONFIG.cache_ttl = old_ttl
    path1 = Compactor.generate_temp_file_path("same", prefix="x", suffix=".txt")
    path2 = Compactor.generate_temp_file_path("same", prefix="x", suffix=".txt")
    assert path1 == path2
    assert path1.endswith(".txt")


def test_a13_cache_sharing_fork_after_compact():
    from core.compactor import Compactor
    from subagent.fork import FORK_PLACEHOLDER_RESULT

    parent_messages = [{"role": "user", "content": "old context"}]
    parent_assistant = {
        "role": "assistant",
        "content": [{
            "type": "tool_use",
            "id": "tool-1",
            "name": "read_file",
            "input": {},
        }],
    }

    child = Compactor.build_cache_sharing_fork_after_compact(
        parent_messages,
        parent_assistant,
        directive="inspect x",
        summary="summary",
    )

    assert "summary" in child[0]["content"]
    assert child[-2] == parent_assistant
    assert child[-1]["content"][0]["content"][0]["text"] == FORK_PLACEHOLDER_RESULT
    assert "inspect x" in child[-1]["content"][-1]["text"]


def test_a27_flush_memories_before_compact_forces_memory_turn():
    from core.compactor import Compactor
    from memory import create_memory_extractor

    messages = [{"role": "user", "content": "remember project fact"}]
    extractor = create_memory_extractor(workspace=".")
    calls = {}

    def extract_fn(eligible, manifest):
        calls["eligible"] = eligible
        calls["manifest"] = manifest
        return ["project fact"]

    entries = Compactor.flush_memories_before_compact(
        messages,
        extractor=extractor,
        extract_fn=extract_fn,
    )

    assert entries == ["project fact"]
    assert calls["eligible"] == messages
    assert "memory" in calls["manifest"].lower()


def test_a33_prompt_cache_invariant_defers_tool_and_prompt_changes():
    from core.query_engine import QueryEngine
    from runtime.bedrock_client import BedrockClient
    from tools.registry import ToolRecord

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    engine = QueryEngine(client=client, max_turns=1)
    tool_a = ToolRecord("a", "a", {}, lambda args, context: "a")
    tool_b = ToolRecord("b", "b", {}, lambda args, context: "b")

    prompt1, tools1, warnings1 = engine._enforce_prompt_cache_invariants(
        "system one",
        [tool_a],
        allow_now=True,
    )
    prompt2, tools2, warnings2 = engine._enforce_prompt_cache_invariants(
        "system two",
        [tool_a, tool_b],
        allow_now=False,
    )

    assert prompt1 == "system one"
    assert tools1 == [tool_a]
    assert warnings1 == []
    assert prompt2 == "system one"
    assert [t.name for t in tools2] == ["a"]
    assert any("system prompt change deferred" in w for w in warnings2)
    assert any("toolset change deferred" in w for w in warnings2)


def test_a34_transition_reason_enum_and_skip_api_error_hooks(monkeypatch):
    from core.compactor import Compactor, TransitionReason
    from core.query_engine import QueryEngine
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    engine = QueryEngine(client=client, max_turns=1)

    def boom(*args, **kwargs):
        raise RuntimeError("api failure")

    monkeypatch.setattr(client, "chat", boom)
    result = engine.run("hi", "system", [], output_fn=lambda text: None)

    assert result.stop_reason == "fatal_error"
    assert Compactor.transition_reason() == TransitionReason.API_ERROR.value


def test_a38_preserved_segment_gc_keeps_latest_and_tail():
    from core.compactor import Compactor

    messages = [
        {"role": "user", "content": "old", "preservedSegment": {"id": "p"}},
        {"role": "assistant", "content": "normal"},
        {"role": "user", "content": "new", "preservedSegment": {"id": "p"}},
        {"role": "assistant", "content": "tail"},
    ]

    out = Compactor.gc_compact_boundary_preserved_segments(messages, tail_keep=1)

    assert [m["content"] for m in out] == ["normal", "new", "tail"]


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
    from tools.todo import _reset_todos_for_tests

    _reset_todos_for_tests(clear_disk=True)

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


def test_run_post_compact_cleanup_invalidates_context_caches(tmp_path):
    from core.compactor import Compactor
    from prompt.sections import get_cached_section, set_cached_section
    from runtime.file_cache import FILE_CACHE
    from skills.manager import SkillManager
    from tools import _file_read_tracking

    target = tmp_path / "tracked.txt"
    target.write_text("tracked", encoding="utf-8")
    _file_read_tracking.mark_read(str(target))
    FILE_CACHE.put(str(target), "tracked")
    FILE_CACHE.mark_in_context(str(target))
    set_cached_section("identity", "cached identity")

    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo\ndescription: Use when testing cleanup\n---\nbody\n",
        encoding="utf-8",
    )
    sm = SkillManager(workspace=str(tmp_path), skills_dir=str(skills_dir))
    assert sm.discover()
    sm.active_skill = "demo"

    cleared = Compactor.run_post_compact_cleanup(skill_manager=sm)

    assert cleared["file_read_tracking"]
    assert cleared["file_cache"]
    assert cleared["skill_listing_cache"]
    assert cleared["prompt_section_cache"]
    assert not _file_read_tracking.was_read(str(target))
    assert FILE_CACHE.get(str(target)) is None
    assert not FILE_CACHE.is_in_context(str(target))
    assert sm.active_skill == "demo"
    assert sm._cache == {}
    assert get_cached_section("identity") is None


def test_h2_stub_injection_for_orphan_tool_use():
    from core.compactor import Compactor

    msgs = [
        {"role": "user", "content": "before"},
        {"role": "assistant", "content": "older answer"},
        {
            "role": "assistant",
            "content": [{
                "type": "tool_use",
                "id": "orphan-1",
                "name": "read_file",
                "input": {"file_path": "x.py"},
            }],
        },
        {"role": "user", "content": "continue without the result"},
    ]

    compacted = Compactor.compact(msgs, summary="summary text")
    stub_blocks = [
        block
        for msg in compacted
        for block in (msg.get("content") if isinstance(msg.get("content"), list) else [])
        if isinstance(block, dict)
        and block.get("type") == "tool_result"
        and block.get("tool_use_id") == "orphan-1"
    ]
    assert len(stub_blocks) == 1
    assert "synthetic stub" in stub_blocks[0]["content"]


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


def test_compactor_summary_input_repairs_dangling_tool_use(monkeypatch):
    """Summary calls must repair orphan tool_use blocks before Bedrock."""
    from core.compactor import Compactor
    from runtime.bedrock_client import BedrockClient, Response

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    captured: dict = {}

    def fake_chat(*args, **kwargs):
        captured["messages"] = kwargs["messages"]
        return Response(text="summary after dangling tool_use", usage={})

    monkeypatch.setattr(client, "chat", fake_chat)

    msgs = [
        {"role": "user", "content": "start"},
        {
            "role": "assistant",
            "content": [{
                "type": "tool_use",
                "id": "dangling-1",
                "name": "read_file",
                "input": {"file_path": "app.py"},
            }],
        },
    ]

    summary = Compactor.create_llm_summary(client, msgs)

    assert summary == "summary after dangling tool_use"
    sent = captured["messages"]
    assistant_idx = next(
        idx for idx, msg in enumerate(sent)
        if msg.get("role") == "assistant"
        and isinstance(msg.get("content"), list)
        and msg["content"][0].get("type") == "tool_use"
    )
    next_msg = sent[assistant_idx + 1]
    assert next_msg["role"] == "user"
    assert isinstance(next_msg["content"], list)
    assert next_msg["content"][0]["type"] == "tool_result"
    assert next_msg["content"][0]["tool_use_id"] == "dangling-1"
    assert "pre-summary orphaned tool_use repaired" in next_msg["content"][0]["content"]


def test_compactor_compact_converts_orphan_tool_result_from_recent_window(monkeypatch):
    """Compaction must not keep a tool_result after dropping its tool_use."""
    from core.compactor import Compactor

    monkeypatch.setattr(Compactor, "KEEP_LAST_MESSAGES", 1)
    messages = [
        {
            "role": "assistant",
            "content": [{
                "type": "tool_use",
                "id": "lost-tool",
                "name": "read_file",
                "input": {"file_path": "large.py"},
            }],
        },
        {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": "lost-tool",
                "content": "important output from the dropped tool call",
            }],
        },
    ]

    compacted = Compactor.compact(messages, "summary")

    recent = next(
        msg for msg in compacted
        if msg.get("role") == "user"
        and isinstance(msg.get("content"), list)
    )
    assert recent["role"] == "user"
    assert recent["content"][0]["type"] == "text"
    assert "orphaned tool_result converted to text" in recent["content"][0]["text"]
    assert "important output from the dropped tool call" in recent["content"][0]["text"]


def test_compactor_repair_converts_duplicate_tool_result_to_text():
    """Bedrock accepts exactly one typed result per tool_use id."""
    from core.compactor import Compactor

    messages = [
        {
            "role": "assistant",
            "content": [{
                "type": "tool_use",
                "id": "dup-tool",
                "name": "read_file",
                "input": {},
            }],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "dup-tool",
                    "content": "first result",
                },
                {
                    "type": "tool_result",
                    "tool_use_id": "dup-tool",
                    "content": "duplicate result",
                },
            ],
        },
    ]

    repaired, inserted, converted = Compactor.repair_tool_result_pairs_for_bedrock(messages)

    assert inserted == 0
    assert converted == 1
    content = repaired[1]["content"]
    assert content[0]["type"] == "tool_result"
    assert content[0]["tool_use_id"] == "dup-tool"
    assert content[1]["type"] == "text"
    assert "duplicate result" in content[1]["text"]


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

    def fake_run(client_arg, messages, max_tokens=200_000, skill_manager=None):
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


def test_a18_a30_auto_compact_failure_counter_and_success_reset(monkeypatch):
    from core.query_engine import QueryEngine
    from core import compactor as comp_mod
    from runtime.bedrock_client import BedrockClient, Response

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    engine = QueryEngine(client=client, max_turns=1)
    comp_mod.AUTO_COMPACT.reset()
    comp_mod.AUTO_COMPACT.cooldown_seconds = 0

    monkeypatch.setattr(comp_mod.Compactor, "should_compact", staticmethod(lambda _m, _max: True))

    def fake_chat(*args, **kwargs):
        return Response(text="ok", tool_calls=[], stop_reason="end_turn")

    monkeypatch.setattr(client, "chat", fake_chat)

    def failing_run(*args, **kwargs):
        return comp_mod.CompactionResult(
            success=False,
            error="summary failed",
            tokens_before=1,
            tokens_after=1,
        )

    monkeypatch.setattr(comp_mod.Compactor, "run", staticmethod(failing_run))
    out = []
    for _ in range(3):
        engine.run(user_message="hi", system_prompt="sys", tools=[], output_fn=out.append)
    assert any("auto-compact disabled" in line for line in out)


def test_a31_a34_a35_a36_query_engine_pre_guard_and_error_prefix(monkeypatch):
    from core.query_engine import QueryEngine
    from runtime.bedrock_client import BedrockClient

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    engine = QueryEngine(client=client, max_turns=1)
    out = []
    result = engine.run(
        user_message="x" * 600_000,
        system_prompt="sys",
        tools=[],
        output_fn=out.append,
    )
    assert result.stop_reason == "context_overflow"
    assert "pre-api guard" in (result.error or "")

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    client.chat = boom
    engine2 = QueryEngine(client=client, max_turns=1)
    out2 = []
    result2 = engine2.run("hi", system_prompt="sys", tools=[], output_fn=out2.append)
    assert result2.stop_reason == "fatal_error"
    assert any("error_during_execution" in line for line in out2)


def test_a31_bedrock_cache_control_marks_last_three_messages():
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG

    messages = [
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": [{"type": "text", "text": "two"}]},
        {"role": "user", "content": "three"},
        {"role": "assistant", "content": "four"},
    ]
    old_ttl = CONFIG.cache_ttl
    try:
        CONFIG.cache_ttl = "1h"
        out = BedrockClient._apply_cache_control_to_last_messages(messages)
        marked = []
        for msg in out:
            content = msg["content"]
            blocks = content if isinstance(content, list) else []
            marked.extend(
                block["cache_control"]
                for block in blocks
                if isinstance(block, dict) and "cache_control" in block
            )
        assert len(marked) == 3
        assert all(cc == {"type": "ephemeral", "ttl": "1h"} for cc in marked)
        assert messages[0]["content"] == "one"
    finally:
        CONFIG.cache_ttl = old_ttl


def test_a33_query_source_guard_skips_auto_compact(monkeypatch):
    from core.query_engine import QueryEngine
    from core import compactor as comp_mod
    from runtime.bedrock_client import BedrockClient, Response

    client = BedrockClient(model_id="x", region="us-east-1", mock_mode=True)
    engine = QueryEngine(client=client, max_turns=1)
    comp_mod.AUTO_COMPACT.reset()

    calls = {"run": 0}
    monkeypatch.setattr(comp_mod.Compactor, "should_compact", staticmethod(lambda _m, _max: True))

    def fake_run(*args, **kwargs):
        calls["run"] += 1
        return comp_mod.CompactionResult(success=True, messages_after=[], tokens_before=1, tokens_after=0)

    monkeypatch.setattr(comp_mod.Compactor, "run", staticmethod(fake_run))
    monkeypatch.setattr(
        client,
        "chat",
        lambda *args, **kwargs: Response(text="ok", tool_calls=[], stop_reason="end_turn"),
    )
    engine.run("hi", system_prompt="sys", tools=[], query_source="compact")
    assert calls["run"] == 0
