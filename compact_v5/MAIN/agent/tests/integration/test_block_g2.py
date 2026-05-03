"""Block G2 — forkSubagent cache-prefix replay.

Source: Runnable tools/AgentTool/forkSubagent.ts:73-end (~140 LOC).

Tests per TEST_DESIGN §Block G2 (3 tests; T5 deferred to R-tier R3):
- test_forkSubagent_byte_identical_prefix
- test_forkSubagent_cache_aware_serialization
- test_g2_cache_prefix_real_bedrock (T5, RUN_REAL_BEDROCK gate)
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
# Test fixtures
# ============================================================

def _make_parent_messages_with_tool_use():
    """Construct a realistic parent message buffer containing a user
    turn, an assistant turn with tool_use, and a tool_result user turn —
    the typical pre-fork state where the model is mid-task."""
    return [
        {"role": "user", "content": "Investigate the auth module."},
        {"role": "assistant", "content": [
            {"type": "thinking", "thinking": "Let me read the relevant files."},
            {"type": "text", "text": "Reading auth..."},
            {"type": "tool_use", "id": "tu_1", "name": "read_file",
             "input": {"file_path": "/src/auth/validate.ts"}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "tu_1",
             "content": "function validate(...) { ... }"}
        ]},
    ]


def _make_assistant_with_multiple_tool_uses():
    """Assistant message with 3 tool_use blocks (parallel research pattern)."""
    return {
        "role": "assistant",
        "content": [
            {"type": "text", "text": "I'll investigate from three angles in parallel."},
            {"type": "tool_use", "id": "tu_a", "name": "read_file",
             "input": {"file_path": "/a.py"}},
            {"type": "tool_use", "id": "tu_b", "name": "read_file",
             "input": {"file_path": "/b.py"}},
            {"type": "tool_use", "id": "tu_c", "name": "grep",
             "input": {"pattern": "TODO", "path": "/src"}},
        ],
    }


# ============================================================
# TEST_DESIGN row 1 — byte-identical prefix
# ============================================================

def test_forkSubagent_byte_identical_prefix():
    """Two fork children spawned with different directives but the same
    parent state must have BYTE-identical message buffers up to (and
    including) the placeholder tool_results — only the final directive
    text block differs.
    """
    from subagent.fork import (
        build_forked_messages,
        cache_prefix_match_length,
        serialize_for_cache_prefix,
    )

    parent_messages = _make_parent_messages_with_tool_use()
    asst_msg = _make_assistant_with_multiple_tool_uses()

    child_a = build_forked_messages(
        parent_messages=parent_messages,
        parent_assistant_message=asst_msg,
        directive="Focus on validate.ts:42 null pointer.",
    )
    child_b = build_forked_messages(
        parent_messages=parent_messages,
        parent_assistant_message=asst_msg,
        directive="Investigate session expiry handling.",
    )

    # Total length must match (same parent state, same shape).
    assert len(child_a) == len(child_b)

    # All but the LAST message must be byte-identical (the final user
    # message has the per-child directive text — that's the only
    # variation point).
    n_match = cache_prefix_match_length(child_a, child_b)
    assert n_match == len(child_a) - 1, (
        f"Cache prefix should match all but the last message; "
        f"matched {n_match}/{len(child_a)} for byte-identical prefix"
    )

    # The replayed assistant message (full tool_use list) is byte-identical.
    asst_serial_a = serialize_for_cache_prefix([child_a[-2]])
    asst_serial_b = serialize_for_cache_prefix([child_b[-2]])
    assert asst_serial_a == asst_serial_b, (
        "Replayed parent assistant message must be byte-identical across "
        "fork children for prompt-cache sharing"
    )


def test_forkSubagent_placeholder_result_text_constant():
    """Block G2 lock: the placeholder tool_result text is verbatim from
    Runnable's FORK_PLACEHOLDER_RESULT — must be identical across all
    children (cache-key compatibility with Anthropic-API-direct deployments
    if v5 ever runs alongside one)."""
    from subagent.fork import FORK_PLACEHOLDER_RESULT, build_forked_messages

    asst = _make_assistant_with_multiple_tool_uses()
    child = build_forked_messages([], asst, "anything")
    # 1 assistant + 1 user
    assert len(child) == 2
    last_user = child[-1]
    assert last_user["role"] == "user"
    placeholders = [b for b in last_user["content"] if b.get("type") == "tool_result"]
    assert len(placeholders) == 3  # one per parent tool_use
    for p in placeholders:
        # Each placeholder content is a list of one text block with the
        # exact Runnable-cache-compatible literal.
        text_blocks = [b for b in p["content"] if b.get("type") == "text"]
        assert len(text_blocks) == 1
        assert text_blocks[0]["text"] == FORK_PLACEHOLDER_RESULT
        assert text_blocks[0]["text"] == "Fork started — processing in background"


# ============================================================
# TEST_DESIGN row 2 — cache-aware serialization (deterministic)
# ============================================================

def test_forkSubagent_cache_aware_serialization():
    """serialize_for_cache_prefix must be deterministic — sorted keys, no
    random IDs. Two structurally equal message dicts with different key
    insertion order must serialize identically.
    """
    from subagent.fork import serialize_for_cache_prefix

    msg_a = {"role": "user", "content": [{"type": "text", "text": "hi"}]}
    msg_b = {"content": [{"text": "hi", "type": "text"}], "role": "user"}
    assert serialize_for_cache_prefix([msg_a]) == serialize_for_cache_prefix([msg_b])

    # Different content text → different serialization (sanity).
    msg_c = {"role": "user", "content": [{"type": "text", "text": "bye"}]}
    assert serialize_for_cache_prefix([msg_a]) != serialize_for_cache_prefix([msg_c])


# ============================================================
# TEST_DESIGN row 3 — real Bedrock cache hit (DEFERRED to R-tier)
# ============================================================

@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="T5 real-Bedrock test; deferred to R-tier R3 (sub-agent dispatch + cache-prefix)",
)
def test_g2_cache_prefix_real_bedrock():
    """Real Bedrock call: parent + child → second call cache_read_input_tokens
    > 0 (cache hit verified). Cap: ~$0.01.

    Per ADR-033 §Notes: deferred to R-tier R3 to avoid burning credit
    during unit-test phase — the byte-identical-prefix lock is sufficient
    for correctness; the real cache verification belongs with the rest of
    the real-AWS suite.
    """
    pytest.skip(
        "Deferred to R-tier R3 (sub-agent dispatch + cache-prefix); "
        "Block G2 ships without real-AWS during unit-test phase."
    )


# ============================================================
# Behavioral lock tests
# ============================================================

def test_is_in_fork_child_detects_boilerplate_tag():
    """is_in_fork_child must return True for messages carrying the
    fork-boilerplate tag in any user-role text block."""
    from subagent.fork import (
        is_in_fork_child,
        build_child_message,
        FORK_BOILERPLATE_TAG,
    )

    # No tag → False.
    no_fork = [
        {"role": "user", "content": "ordinary message"},
        {"role": "assistant", "content": [{"type": "text", "text": "ok"}]},
    ]
    assert is_in_fork_child(no_fork) is False

    # Tag in user list-content → True.
    fork_user = [
        {"role": "user", "content": [
            {"type": "text", "text": build_child_message("scope X")}
        ]},
    ]
    assert is_in_fork_child(fork_user) is True

    # Tag in user string content → True (defensive path).
    fork_str = [
        {"role": "user", "content": f"<{FORK_BOILERPLATE_TAG}> some directive"},
    ]
    assert is_in_fork_child(fork_str) is True

    # Tag in assistant message → False (boilerplate is user-only).
    fork_in_asst = [
        {"role": "assistant", "content": [
            {"type": "text", "text": f"<{FORK_BOILERPLATE_TAG}> sneaky"}
        ]},
    ]
    assert is_in_fork_child(fork_in_asst) is False


def test_build_forked_messages_no_tool_use_falls_back_to_directive_only():
    """When the parent assistant message has zero tool_use blocks,
    build_forked_messages still returns a sensible buffer ending with
    the directive."""
    from subagent.fork import build_forked_messages, FORK_BOILERPLATE_TAG

    asst_no_tools = {
        "role": "assistant",
        "content": [{"type": "text", "text": "Done — no tools needed."}],
    }
    child = build_forked_messages([], asst_no_tools, "follow up on X")
    # Last message is a user turn with the directive boilerplate.
    last = child[-1]
    assert last["role"] == "user"
    found = any(
        isinstance(b, dict)
        and b.get("type") == "text"
        and FORK_BOILERPLATE_TAG in b.get("text", "")
        for b in last["content"]
    )
    assert found, "directive (with boilerplate tag) must be present"


def test_build_forked_messages_directive_appears_only_in_last_block():
    """The per-child directive text appears ONLY in the trailing user
    message's text block — not in the assistant replay (otherwise prefix
    sharing breaks)."""
    from subagent.fork import build_forked_messages

    asst = _make_assistant_with_multiple_tool_uses()
    child = build_forked_messages([], asst, "UNIQUE_DIRECTIVE_MARKER_XYZ_123")

    # Walk every block; only count "UNIQUE_DIRECTIVE_MARKER_XYZ_123" hits.
    hit_locations = []
    for i, m in enumerate(child):
        content = m.get("content")
        if isinstance(content, str):
            if "UNIQUE_DIRECTIVE_MARKER_XYZ_123" in content:
                hit_locations.append(("string", i))
        elif isinstance(content, list):
            for j, b in enumerate(content):
                if isinstance(b, dict):
                    text_field = (
                        b.get("text") or "" if b.get("type") == "text"
                        else ""
                    )
                    if "UNIQUE_DIRECTIVE_MARKER_XYZ_123" in str(text_field):
                        hit_locations.append((m["role"], i, j))

    assert len(hit_locations) == 1, (
        f"Directive marker must appear exactly once (in the trailing user "
        f"text block); found at: {hit_locations}"
    )
    # That single location must be in the LAST message (a user turn).
    role, i, j = hit_locations[0]
    assert role == "user"
    assert i == len(child) - 1


def test_build_forked_messages_preserves_parent_history_byte_identical():
    """The first len(parent_messages) entries of the child buffer must
    be byte-identical to parent_messages — they are the cache prefix."""
    from subagent.fork import build_forked_messages, serialize_for_cache_prefix

    parent = _make_parent_messages_with_tool_use()
    asst = _make_assistant_with_multiple_tool_uses()
    child = build_forked_messages(parent, asst, "directive A")

    for i, p in enumerate(parent):
        c = child[i]
        assert serialize_for_cache_prefix([c]) == serialize_for_cache_prefix([p]), (
            f"parent message {i} must be byte-identical in child buffer"
        )


def test_build_forked_messages_rejects_non_assistant_parent_message():
    """A parent_assistant_message with role != 'assistant' must raise."""
    from subagent.fork import build_forked_messages

    bad = {"role": "user", "content": [{"type": "text", "text": "x"}]}
    with pytest.raises(ValueError, match="role='assistant'"):
        build_forked_messages([], bad, "directive")
