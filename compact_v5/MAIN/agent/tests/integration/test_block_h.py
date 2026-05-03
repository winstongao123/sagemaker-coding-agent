"""Block H — Memory extraction (COMBINED v4 + Runnable extractMemories +
sessionMemory).

Source: Runnable services/extractMemories.ts + sessionMemory.ts +
sessionMemoryCompact.ts + sessionMemoryUtils.ts.

Tests per TEST_DESIGN §Block H (6 tests, $0):
- test_extract_and_append_memories_v4_session_end
- test_extract_memories_closure_scoped_state
- test_session_memory_dedup_before_write
- test_adjust_index_preserves_api_invariants
- test_memory_extraction_handles_empty_session
- test_session_memory_compact_no_400_sequence
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
# TEST_DESIGN row 1 — v4 session-end trigger writes memory.md
# ============================================================

def test_extract_and_append_memories_v4_session_end(tmp_path):
    """Session-end trigger writes new entries to memory.md (v4 behavior).

    With force=True (the v4 session-end semantics), extraction runs even
    if throttle gates haven't tripped.
    """
    from memory import create_memory_extractor

    extractor = create_memory_extractor(workspace=str(tmp_path))

    def fake_llm(messages, manifest):
        return ["User prefers TypeScript", "Project uses pytest"]

    messages = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": [{"type": "text", "text": "Hi back"}]},
    ]

    new_entries = extractor.extract_memories(
        messages, extract_fn=fake_llm, force=True,
    )
    assert new_entries == ["User prefers TypeScript", "Project uses pytest"]
    # File written under workspace as memory.md.
    md = (tmp_path / "memory.md").read_text(encoding="utf-8")
    assert "User prefers TypeScript" in md
    assert "Project uses pytest" in md


# ============================================================
# TEST_DESIGN row 2 — closure-scoped throttle state
# ============================================================

def test_extract_memories_closure_scoped_state(tmp_path):
    """extractMemories has closure-scoped throttle state (Runnable pattern).

    Two calls in quick succession on the same MemoryExtractor instance
    must respect throttles — the second call should NOT trigger
    extraction even though force=False, because turns/tool-calls haven't
    crossed the threshold yet.
    """
    from memory import create_memory_extractor

    ext = create_memory_extractor(
        workspace=str(tmp_path),
        turns_since_threshold=5,
        tool_call_threshold=10,
    )
    msgs = [
        {"role": "user", "content": "x"},
        {"role": "assistant", "content": [{"type": "text", "text": "y"}]},
    ]

    calls = []

    def fake_llm(messages, manifest):
        calls.append(1)
        return ["whatever"]

    # No throttles tripped yet → should NOT extract.
    out_a = ext.extract_memories(msgs, extract_fn=fake_llm)
    assert out_a == [], "below-threshold call must not extract"

    # Bump turns and tool-calls past the threshold.
    for _ in range(5):
        ext.increment_turn()
    for _ in range(10):
        ext.increment_tool_call()
    out_b = ext.extract_memories(msgs, extract_fn=fake_llm)
    assert out_b == ["whatever"]

    # State reset after extraction.
    assert ext._turns_since_last_extraction == 0
    assert ext._tool_calls_since_last_extraction == 0
    # And another immediate call is throttled again.
    out_c = ext.extract_memories(msgs, extract_fn=fake_llm)
    assert out_c == []


def test_extract_memories_separate_extractors_have_isolated_state(tmp_path):
    """Two MemoryExtractor instances are isolated — closure-scoped state
    doesn't leak (this is the v5 vs v4 win: v4 had a global, racy)."""
    from memory import create_memory_extractor

    a = create_memory_extractor(workspace=str(tmp_path / "a"))
    b = create_memory_extractor(workspace=str(tmp_path / "b"))
    a._last_extracted_message_index = 5
    assert b._last_extracted_message_index == -1


# ============================================================
# TEST_DESIGN row 3 — sessionMemoryUtils dedup before write
# ============================================================

def test_session_memory_dedup_before_write():
    """`sessionMemoryUtils` deduplicates before writing memory.md."""
    from memory import deduplicate_memory_entries

    raw = [
        "Project uses Python 3.11",
        "  project uses python 3.11  ",  # whitespace + case variant
        "Project uses Python 3.11",  # exact dup
        "Tests run via pytest",
        "PROJECT USES PYTHON 3.11",  # all-caps variant
    ]
    deduped = deduplicate_memory_entries(raw)
    assert deduped == ["Project uses Python 3.11", "Tests run via pytest"]


def test_session_memory_dedup_preserves_first_seen_casing():
    """When variants conflict, the first-seen string wins."""
    from memory import deduplicate_memory_entries

    out = deduplicate_memory_entries(
        ["lowercase first", "LOWERCASE FIRST", "Lowercase First"]
    )
    assert out == ["lowercase first"]


# ============================================================
# TEST_DESIGN row 4 — adjustIndexToPreserveAPIInvariants (R4 #56 MUST)
# ============================================================

def test_adjust_index_preserves_api_invariants():
    """adjustIndexToPreserveAPIInvariants returns indices that keep
    tool_use/tool_result paired (R4 #56 MUST).

    Buffer layout:
      msg[0] user "do work"
      msg[1] assistant tool_use id="t1"
      msg[2] user tool_result for t1
      msg[3] assistant text "done"

    A naive cut at index 2 would orphan the tool_use at msg[1] from its
    tool_result at msg[2]. The adjust function must pull the cut to
    msg[1] (or earlier) so the pair stays together.
    """
    from memory import adjust_index_to_preserve_api_invariants

    msgs = [
        {"role": "user", "content": "do work"},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "t1", "name": "x", "input": {}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": ""},
        ]},
        {"role": "assistant", "content": [{"type": "text", "text": "done"}]},
    ]
    # Naive cut at 2 would split the pair (1,2). adjust must pull to ≤1.
    out = adjust_index_to_preserve_api_invariants(msgs, candidate_index=2)
    assert out <= 1, (
        f"adjusted index {out} must be ≤1 to keep tool_use+tool_result paired"
    )


def test_adjust_index_no_op_when_safe():
    """When candidate already lands cleanly (between completed pairs),
    the function returns it unchanged."""
    from memory import adjust_index_to_preserve_api_invariants

    msgs = [
        {"role": "user", "content": "x"},
        {"role": "assistant", "content": [{"type": "text", "text": "y"}]},
        {"role": "user", "content": "z"},
        {"role": "assistant", "content": [{"type": "text", "text": "w"}]},
    ]
    assert adjust_index_to_preserve_api_invariants(msgs, 2) == 2


def test_adjust_index_handles_dangling_tool_use():
    """A dangling tool_use (no matching tool_result yet) doesn't crash."""
    from memory import adjust_index_to_preserve_api_invariants

    msgs = [
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "t1", "name": "x", "input": {}},
        ]},
        # No matching tool_result — agent crashed mid-call.
    ]
    out = adjust_index_to_preserve_api_invariants(msgs, candidate_index=1)
    assert isinstance(out, int)
    assert 0 <= out <= len(msgs)


def test_calculate_messages_to_keep_index():
    """High-level wrapper: keep N messages from the end, but adjust if
    the cut would split a pair."""
    from memory import calculate_messages_to_keep_index

    msgs = [
        {"role": "user", "content": "x"},
        {"role": "assistant", "content": [{"type": "text", "text": "y"}]},
        {"role": "user", "content": "z"},
    ]
    # max_keep_count=2 → naive candidate = 1; no pairs → returns 1 unchanged.
    assert calculate_messages_to_keep_index(msgs, max_keep_count=2) == 1
    # max_keep_count >= len → keep all = 0.
    assert calculate_messages_to_keep_index(msgs, max_keep_count=99) == 0
    assert calculate_messages_to_keep_index(msgs, max_keep_count=0) == 0


# ============================================================
# TEST_DESIGN row 5 — empty session → no extraction, no error
# ============================================================

def test_memory_extraction_handles_empty_session(tmp_path):
    """session with 0 user messages → no extraction, no error."""
    from memory import create_memory_extractor

    ext = create_memory_extractor(workspace=str(tmp_path))
    out = ext.extract_memories(messages=[], extract_fn=lambda m, x: ["bogus"], force=True)
    assert out == [], "empty session must not extract"
    # No memory.md written.
    assert not (tmp_path / "memory.md").exists()


# ============================================================
# TEST_DESIGN row 6 — compact preserves Bedrock validity
# ============================================================

def test_session_memory_compact_no_400_sequence():
    """Compact run on a session with mixed tool_use/tool_result → resulting
    messages valid for Bedrock (every tool_use has a matching tool_result
    in the kept buffer; no orphaned pairs)."""
    from memory import (
        adjust_index_to_preserve_api_invariants,
        calculate_messages_to_keep_index,
    )

    # Build a realistic messy buffer.
    msgs = [
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "a", "name": "read", "input": {}},
            {"type": "tool_use", "id": "b", "name": "read", "input": {}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "a", "content": "x"},
            {"type": "tool_result", "tool_use_id": "b", "content": "y"},
        ]},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "c", "name": "edit", "input": {}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "c", "content": "ok"},
        ]},
        {"role": "assistant", "content": [{"type": "text", "text": "done"}]},
    ]
    # Compact to keep last 3 messages.
    cut = calculate_messages_to_keep_index(msgs, max_keep_count=3)
    kept = msgs[cut:]

    # Validate: every tool_use_id in `kept` has a matching tool_result
    # IN `kept` (or vice versa); no orphans.
    use_ids = set()
    result_ids = set()
    for m in kept:
        content = m.get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                use_ids.add(b.get("id"))
            elif b.get("type") == "tool_result":
                result_ids.add(b.get("tool_use_id"))
    # Pairs in kept-buffer must match.
    assert use_ids == result_ids, (
        f"Kept buffer has orphaned tool_use/tool_result: "
        f"uses={use_ids}, results={result_ids}"
    )


# ============================================================
# Behavioral lock tests
# ============================================================

def test_has_tool_calls_in_last_assistant_turn():
    """H-9 predicate: True iff the last assistant has tool_use blocks."""
    from memory import has_tool_calls_in_last_assistant_turn

    msgs_no_tool = [
        {"role": "user", "content": "x"},
        {"role": "assistant", "content": [{"type": "text", "text": "y"}]},
    ]
    assert has_tool_calls_in_last_assistant_turn(msgs_no_tool) is False

    msgs_with_tool = [
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "t", "name": "x", "input": {}},
        ]},
    ]
    assert has_tool_calls_in_last_assistant_turn(msgs_with_tool) is True

    # Last assistant has no tool_use even if earlier one did.
    msgs_old_tool = [
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "old", "name": "x", "input": {}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "old", "content": ""},
        ]},
        {"role": "assistant", "content": [{"type": "text", "text": "done"}]},
    ]
    assert has_tool_calls_in_last_assistant_turn(msgs_old_tool) is False


def test_count_tool_calls_since():
    """H-7 helper: count tool_use blocks after a cursor."""
    from memory import count_tool_calls_since

    msgs = [
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "1", "name": "read", "input": {}},
        ]},
        {"role": "user", "content": "x"},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "2", "name": "read", "input": {}},
            {"type": "tool_use", "id": "3", "name": "edit", "input": {}},
        ]},
    ]
    assert count_tool_calls_since(msgs, since_index=-1) == 3
    assert count_tool_calls_since(msgs, since_index=0) == 2
    assert count_tool_calls_since(msgs, since_index=-1, tool_name="read") == 2
    assert count_tool_calls_since(msgs, since_index=-1, tool_name="edit") == 1


def test_drain_pending_extraction_returns_true_when_idle(tmp_path):
    """H-3 drain: when no extraction is in flight, returns True immediately."""
    from memory import create_memory_extractor

    ext = create_memory_extractor(workspace=str(tmp_path))
    assert ext.drain_pending_extraction(timeout_s=0.01) is True


def test_has_text_blocks():
    """H-14: predicate distinguishes text-bearing content from tool-only."""
    from memory.compact import has_text_blocks

    assert has_text_blocks([{"type": "text", "text": "hi"}]) is True
    assert has_text_blocks([{"type": "tool_use", "id": "1", "name": "x", "input": {}}]) is False
    assert has_text_blocks([]) is False
    assert has_text_blocks("plain string") is True
    assert has_text_blocks(None) is False


# ============================================================
# Codex iter-1 finding-lock tests
# ============================================================

def test_h11_fixed_point_loop_handles_cascading_pair_pulls():
    """Codex iter-1 finding #1 BLOCKER lock: when a later pair pulls
    the cut backward, the algorithm must re-check earlier pairs that
    might newly become split.

    Buffer layout (indices in []):
      [0] user "task"
      [1] assistant: tool_use a (id=a)
      [2] assistant: tool_use b (id=b)
      [3] user: tool_result for a
      [4] user: text "ok"
      [5] user: tool_result for b
      [6] assistant: text "done"

    Pair a: (1, 3). Pair b: (2, 5).

    candidate=4 splits pair b (2, 5). First-pass adjusts to 2.
    But adjusted=2 also splits pair a (1, 3). Without fixed-point loop,
    we'd return 2 (still split). With fixed-point: pull again to 1.

    Lock: candidate=4 → final adjusted ≤ 1.
    """
    from memory import adjust_index_to_preserve_api_invariants

    msgs = [
        {"role": "user", "content": "task"},  # 0
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "a", "name": "x", "input": {}},
        ]},  # 1
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "b", "name": "y", "input": {}},
        ]},  # 2
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "a", "content": ""},
        ]},  # 3
        {"role": "user", "content": "ok"},  # 4
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "b", "content": ""},
        ]},  # 5
        {"role": "assistant", "content": [{"type": "text", "text": "done"}]},  # 6
    ]
    out = adjust_index_to_preserve_api_invariants(msgs, candidate_index=4)
    assert out <= 1, (
        f"Cascading pair pulls require fixed-point loop. Got {out}, "
        f"expected ≤1 (both pairs (1,3) and (2,5) must end up on the "
        f"same side of the cut)."
    )


def test_drain_pending_extraction_actually_blocks_until_complete(tmp_path):
    """Codex iter-1 finding #2 BLOCKER lock: drain_pending_extraction
    must BLOCK until the in-flight extraction completes, not return
    immediately.

    Setup: spawn an extraction in a background thread that holds for
    ~50ms. Call drain from the main thread. drain must wait at least
    ~40ms (the slower of: extraction duration, drain timeout) before
    returning.
    """
    import threading
    import time
    from memory import create_memory_extractor

    ext = create_memory_extractor(workspace=str(tmp_path))

    def slow_extract(messages, manifest):
        time.sleep(0.05)
        return ["entry"]

    msgs = [
        {"role": "user", "content": "x"},
        {"role": "assistant", "content": [{"type": "text", "text": "y"}]},
    ]

    started = threading.Event()
    bg_done = threading.Event()

    def bg():
        started.set()
        ext.extract_memories(msgs, extract_fn=slow_extract, force=True)
        bg_done.set()

    t = threading.Thread(target=bg)
    t.start()
    started.wait(timeout=2.0)
    # Give the bg thread time to enter extract_memories' try block + clear
    # the idle event before main calls drain.
    time.sleep(0.005)

    drain_start = time.monotonic()
    ok = ext.drain_pending_extraction(timeout_s=2.0)
    drain_elapsed = time.monotonic() - drain_start

    t.join(timeout=2.0)
    assert ok is True, "drain must return True after extraction finishes"
    # Must have blocked at least ~30ms (the bg sleep was 50ms minus our 5ms head-start).
    assert drain_elapsed > 0.020, (
        f"drain returned in {drain_elapsed*1000:.1f}ms — must block "
        "until in-flight extraction completes (Codex iter-1 #2)"
    )
    # And the bg extraction did finish.
    assert bg_done.is_set()


def test_dedup_uses_casefold_for_unicode():
    """Codex iter-1 finding #3 LOW lock: dedup must use str.casefold(),
    not str.lower(). casefold handles Unicode case-folding (e.g.
    German ß → ss) where lower() is ASCII-only-ish.

    Lock: 'ß' and 'ss' must be treated as equal under casefold.
    """
    from memory import deduplicate_memory_entries

    out = deduplicate_memory_entries(["Straße", "STRASSE"])
    # casefold('Straße') == 'strasse' == casefold('STRASSE') → dedup to 1.
    assert len(out) == 1, (
        f"casefold should dedup German ß↔ss; got {out!r}. Codex iter-1 #3."
    )


def test_scan_memory_files_lists_md_under_workspace(tmp_path):
    """H-6: scan_memory_files lists existing .md files under workspace."""
    from memory import create_memory_extractor

    (tmp_path / "memory.md").write_text("- entry 1", encoding="utf-8")
    (tmp_path / "skills" / "x").mkdir(parents=True)
    (tmp_path / "skills" / "x" / "SKILL.md").write_text("---\nname: x\n---", encoding="utf-8")

    ext = create_memory_extractor(workspace=str(tmp_path))
    files = ext.scan_memory_files()
    # Both files appear (relative paths, forward-slashed).
    assert "memory.md" in files
    assert "skills/x/SKILL.md" in files
