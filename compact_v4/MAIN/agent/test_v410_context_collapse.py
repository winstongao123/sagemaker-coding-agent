"""V4.10.1 #41b — Context Collapse (segment-level).

Tests:
1. No stale pairs → no-op.
2. Single stale pair (below COLLAPSE_MIN_SEGMENT_LEN=3) → kept verbatim.
3. 3+ consecutive stale pairs → collapsed into 1 synthetic 2-message pair.
4. Mixed: real text + stale segment + more real text → only stale segment collapsed.
5. Two separate stale runs → both collapsed independently.
6. Stale pair with a tool_result that's NOT marker (real content) → NOT collapsed.
7. Assistant message with text content → NOT considered stale (carries signal).
8. Bedrock role alternation preserved after collapse.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sagemaker_agent as sa


def _stale_pair(tool_id: str, name: str = "read_file"):
    """Build (assistant tool_use, user tool_result with marker) — i.e. already microcompacted."""
    a = {"role": "assistant", "content": [
        {"type": "tool_use", "id": tool_id, "name": name, "input": {"file_path": "x"}},
    ]}
    u = {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tool_id, "content": sa.MICROCOMPACT_MARKER},
    ]}
    return [a, u]


def _real_pair(tool_id: str):
    """Build a NON-stale tool round-trip (tool_result has real content)."""
    a = {"role": "assistant", "content": [
        {"type": "tool_use", "id": tool_id, "name": "read_file", "input": {"file_path": "x"}},
    ]}
    u = {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tool_id, "content": "real file contents"},
    ]}
    return [a, u]


def _user_text(text: str):
    return {"role": "user", "content": text}


def _assistant_text(text: str):
    return {"role": "assistant", "content": text}


def _alternation_ok(messages):
    """Check Bedrock-style role alternation (user must come first; no two same-role in a row)."""
    if not messages:
        return True
    last = None
    for m in messages:
        r = m.get("role")
        if last is not None and r == last:
            return False
        last = r
    return True


def test_no_stale_pairs_is_noop():
    msgs = [_user_text("hi")] + _real_pair("a") + [_assistant_text("done")]
    out, n = sa.context_collapse(msgs)
    assert n == 0
    assert out == msgs


def test_single_stale_pair_below_threshold_kept():
    """COLLAPSE_MIN_SEGMENT_LEN=3, so 1 stale pair must NOT be collapsed."""
    msgs = [_user_text("q")] + _stale_pair("a") + [_assistant_text("ans")]
    out, n = sa.context_collapse(msgs)
    assert n == 0
    assert out == msgs


def test_three_consecutive_stale_pairs_collapsed():
    msgs = (
        [_user_text("research this")]
        + _stale_pair("a") + _stale_pair("b") + _stale_pair("c")
        + [_assistant_text("done")]
    )
    out, n = sa.context_collapse(msgs)
    assert n == 1, f"Expected 1 collapsed segment, got {n}"
    # Output: user, assistant(elided 3), user(continue), assistant(done) = 4 messages
    assert len(out) == 4, f"Expected 4 messages after collapse, got {len(out)}: {out}"
    assert out[0]["role"] == "user"
    assert out[1]["role"] == "assistant"
    assert "Elided 3 stale tool calls" in out[1]["content"]
    assert out[2]["role"] == "user"
    assert out[3]["role"] == "assistant"
    assert _alternation_ok(out), f"Role alternation broken: {[m['role'] for m in out]}"


def test_mixed_stale_and_real_only_collapses_stale():
    msgs = (
        [_user_text("start")]
        + _real_pair("real1")  # NOT stale
        + _stale_pair("s1") + _stale_pair("s2") + _stale_pair("s3")  # 3 stale → collapse
        + _real_pair("real2")  # NOT stale
        + [_assistant_text("end")]
    )
    out, n = sa.context_collapse(msgs)
    assert n == 1
    # Verify the real pairs survived
    real_tool_use_ids = [
        b.get("id")
        for m in out
        if m.get("role") == "assistant" and isinstance(m.get("content"), list)
        for b in m["content"]
        if isinstance(b, dict) and b.get("type") == "tool_use"
    ]
    assert "real1" in real_tool_use_ids and "real2" in real_tool_use_ids
    assert _alternation_ok(out)


def test_two_separate_stale_runs_both_collapsed():
    msgs = (
        [_user_text("start")]
        + _stale_pair("a1") + _stale_pair("a2") + _stale_pair("a3")  # run 1: 3 stale
        + _real_pair("middle")  # interrupt — breaks the run
        + _stale_pair("b1") + _stale_pair("b2") + _stale_pair("b3") + _stale_pair("b4")  # run 2: 4 stale
        + [_assistant_text("end")]
    )
    out, n = sa.context_collapse(msgs)
    assert n == 2, f"Expected 2 collapsed segments, got {n}"
    assert _alternation_ok(out)


def test_real_tool_result_not_collapsed():
    """A tool_result with REAL content (not the microcompact marker) must
    survive context_collapse even if surrounded by other stale pairs."""
    real_pair = _real_pair("real")
    msgs = (
        [_user_text("q")]
        + _stale_pair("a") + real_pair + _stale_pair("b") + _stale_pair("c")
        + [_assistant_text("ans")]
    )
    out, n = sa.context_collapse(msgs)
    # The real pair breaks the run. Stale pair "a" alone is below threshold
    # (only 1 pair). Stale pairs "b"+"c" are also below threshold (only 2 pairs).
    # So nothing should collapse.
    assert n == 0, f"Expected no collapse with real pair breaking the run; got {n}"
    assert out == msgs


def test_assistant_with_text_breaks_stale_run():
    """An assistant message that contains real text (not just tool_use) is
    NOT a stale candidate, even if followed by a tool_result. Such messages
    should break the stale run."""
    pair_with_text = [
        {"role": "assistant", "content": [
            {"type": "text", "text": "I'll check this file."},
            {"type": "tool_use", "id": "with_text", "name": "read_file", "input": {"file_path": "x"}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "with_text", "content": sa.MICROCOMPACT_MARKER},
        ]},
    ]
    msgs = (
        [_user_text("start")]
        + _stale_pair("a") + _stale_pair("b")
        + pair_with_text  # breaks the run because of the text block
        + _stale_pair("c")
        + [_assistant_text("done")]
    )
    out, n = sa.context_collapse(msgs)
    # Without the text-bearing pair the longest stale run is 2 (a, b) — below threshold.
    assert n == 0, f"Text-bearing pair should break stale run; got n={n}"


def test_alternation_preserved_after_collapse():
    msgs = (
        [_user_text("research")]
        + _stale_pair("a") + _stale_pair("b") + _stale_pair("c") + _stale_pair("d")
        + [_assistant_text("ok")]
    )
    out, n = sa.context_collapse(msgs)
    assert n == 1
    assert _alternation_ok(out), f"Roles after collapse not alternating: {[m['role'] for m in out]}"


def test_collapse_at_start_of_messages():
    """Edge case: stale run at the very start — no preceding user message."""
    msgs = _stale_pair("a") + _stale_pair("b") + _stale_pair("c") + [_assistant_text("ok")]
    out, n = sa.context_collapse(msgs)
    assert n == 1
    assert out[0]["role"] == "assistant"  # synthetic ack
    assert "Elided 3 stale tool calls" in out[0]["content"]


def test_thinking_block_protects_from_collapse():
    """Codex 2026-04-28 fix: assistant message containing a 'thinking' block
    (or any non-text/non-tool_use block) is NOT stale, even if it has tool_use
    + marker tool_result. Such blocks carry signal collapse must not drop."""
    pair_with_thinking = [
        {"role": "assistant", "content": [
            {"type": "thinking", "thinking": "I should be careful here."},
            {"type": "tool_use", "id": "with_thinking", "name": "read_file", "input": {"file_path": "x"}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "with_thinking", "content": sa.MICROCOMPACT_MARKER},
        ]},
    ]
    msgs = (
        [_user_text("research")]
        + _stale_pair("a") + _stale_pair("b")
        + pair_with_thinking
        + _stale_pair("c")
        + [_assistant_text("done")]
    )
    out, n = sa.context_collapse(msgs)
    # Without the thinking-bearing pair the longest stale run is 2 (a, b) — below threshold.
    assert n == 0, f"Thinking-block pair should break stale run; got n={n}"


def test_marker_substring_in_real_result_not_collapsed():
    """Codex 2026-04-28 fix: a real tool result containing the marker as a
    SUBSTRING (not exact value) must NOT be classified as stale."""
    fake_stale_pair = [
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "fake", "name": "read_file", "input": {"file_path": "x"}},
        ]},
        # tool_result content includes the marker text but ALSO has real content.
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "fake",
             "content": f"Here is the file content. {sa.MICROCOMPACT_MARKER} Also see line 42."},
        ]},
    ]
    msgs = (
        [_user_text("research")]
        + _stale_pair("a") + _stale_pair("b")
        + fake_stale_pair
        + _stale_pair("c")
        + [_assistant_text("done")]
    )
    out, n = sa.context_collapse(msgs)
    # The fake-stale pair has real content, so it breaks the run.
    # Stale pair "a"+"b" alone is 2 — below threshold. "c" alone is 1.
    assert n == 0, f"Marker-as-substring should NOT count as stale; got n={n}"


def test_idempotent_does_not_double_collapse():
    """Running context_collapse twice on the same messages produces the same
    output the second time (the synthetic markers are NOT themselves stale)."""
    msgs = (
        [_user_text("q")]
        + _stale_pair("a") + _stale_pair("b") + _stale_pair("c")
        + [_assistant_text("done")]
    )
    out1, n1 = sa.context_collapse(msgs)
    out2, n2 = sa.context_collapse(out1)
    assert n1 == 1
    assert n2 == 0, f"Second pass collapsed something it shouldn't: {n2}"
    assert out2 == out1


if __name__ == "__main__":
    tests = [
        ("no_stale_pairs_is_noop", test_no_stale_pairs_is_noop),
        ("single_stale_pair_below_threshold_kept", test_single_stale_pair_below_threshold_kept),
        ("three_consecutive_stale_pairs_collapsed", test_three_consecutive_stale_pairs_collapsed),
        ("mixed_stale_and_real_only_collapses_stale", test_mixed_stale_and_real_only_collapses_stale),
        ("two_separate_stale_runs_both_collapsed", test_two_separate_stale_runs_both_collapsed),
        ("real_tool_result_not_collapsed", test_real_tool_result_not_collapsed),
        ("assistant_with_text_breaks_stale_run", test_assistant_with_text_breaks_stale_run),
        ("alternation_preserved_after_collapse", test_alternation_preserved_after_collapse),
        ("collapse_at_start_of_messages", test_collapse_at_start_of_messages),
        ("thinking_block_protects_from_collapse", test_thinking_block_protects_from_collapse),
        ("marker_substring_in_real_result_not_collapsed", test_marker_substring_in_real_result_not_collapsed),
        ("idempotent_does_not_double_collapse", test_idempotent_does_not_double_collapse),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            print(f"FAIL  {name}: {e}")
            failed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
