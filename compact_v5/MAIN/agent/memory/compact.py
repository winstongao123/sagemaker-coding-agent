"""V5 memory/compact.py — Block H session-memory compaction helpers.

PORT_LOG: #097 (H-11 + H-12 + H-14).

Source: Runnable services/sessionMemoryCompact.ts.

H-11 adjustIndexToPreserveAPIInvariants is the **MUST** correctness fix:
without it, sessionMemoryCompact picks a startIndex that lands mid-pair
(tool_use without its tool_result, or vice versa) → Bedrock 400 reject
on the very next API call. This module is small but critical.

Public functions:
- adjust_index_to_preserve_api_invariants(messages, candidate_index)
  → returns an index that keeps tool_use/tool_result paired.
- calculate_messages_to_keep_index(messages, max_keep_count)
  → choose a starting cut-point that satisfies H-11.
- has_text_blocks(content) — H-14 helper.
"""
from __future__ import annotations

from typing import Any, Dict, List


def has_text_blocks(content: Any) -> bool:
    """H-14: True iff `content` is a list with at least one text block.

    Used by H-12: a candidate cut-point with no text content above is
    not a useful boundary (the resulting buffer would have no human-
    readable summary anchor).
    """
    if not isinstance(content, list):
        return isinstance(content, str) and bool(content.strip())
    for b in content:
        if isinstance(b, dict) and b.get("type") == "text":
            text = b.get("text", "")
            if isinstance(text, str) and text.strip():
                return True
    return False


def _collect_pair_indices(messages: List[Dict[str, Any]]) -> Dict[str, int]:
    """Return a dict mapping tool_use_id → index-of-message-containing-it
    AND tool_result_id → index-of-message-containing-it.

    Used by adjust_index_to_preserve_api_invariants.
    """
    use_to_index: Dict[str, int] = {}
    result_to_index: Dict[str, int] = {}
    for i, m in enumerate(messages or []):
        content = m.get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                tid = b.get("id")
                if tid:
                    use_to_index[tid] = i
            elif b.get("type") == "tool_result":
                tid = b.get("tool_use_id")
                if tid:
                    result_to_index[tid] = i
    return {"uses": use_to_index, "results": result_to_index}


def adjust_index_to_preserve_api_invariants(
    messages: List[Dict[str, Any]],
    candidate_index: int,
) -> int:
    """H-11 — the **MUST** correctness fix.

    Given a `candidate_index` (where compaction wants to start dropping
    older messages), return an adjusted index that:
    1. Never lands in the middle of a tool_use/tool_result pair (would
       cause Bedrock 400 on the next API call).
    2. Floors at 0 if the candidate would split a pair.
    3. Returns `candidate_index` unchanged when it's already pair-safe.

    The adjustment direction is "earlier" — if the cut would split a
    pair, we move the cut earlier so BOTH sides of the pair are kept
    in the post-compact buffer (or both are dropped). This may sacrifice
    some compaction savings to preserve API validity.
    """
    msgs = messages or []
    if not msgs:
        return 0
    if candidate_index <= 0:
        return 0
    if candidate_index >= len(msgs):
        return len(msgs)

    # Build pair index.
    indices = _collect_pair_indices(msgs)
    use_to_index = indices["uses"]
    result_to_index = indices["results"]

    # Codex iter-1 finding #1 BLOCKER fix: fixed-point loop.
    # A single pass through use_to_index can leave earlier pairs split.
    # Example: candidate=7 splits pair (5,8) → adjusted=5. But 5 splits
    # an earlier pair (2,6) which we already visited. Iterate until no
    # further pulls happen.
    adjusted = candidate_index
    while True:
        next_adjusted = adjusted
        for tid, use_idx in use_to_index.items():
            result_idx = result_to_index.get(tid)
            if result_idx is None:
                # Dangling tool_use (no result yet); the cut must NOT split
                # it from any preceding tool_result-bearing context.
                continue
            lo = min(use_idx, result_idx)
            hi = max(use_idx, result_idx)
            # If the cut lands between lo and hi, the pair is split.
            # Pull adjusted to lo so the whole pair lands AFTER the cut.
            if lo < next_adjusted <= hi:
                next_adjusted = min(next_adjusted, lo)
        if next_adjusted == adjusted:
            break
        adjusted = next_adjusted
    return max(0, min(adjusted, len(msgs)))


def calculate_messages_to_keep_index(
    messages: List[Dict[str, Any]],
    max_keep_count: int,
) -> int:
    """H-12: pick a starting index for the keep-set.

    Strategy:
    1. Start with `len(messages) - max_keep_count` as the naive candidate.
    2. Floor at 0 (keep everything if buffer is shorter).
    3. Pass through adjust_index_to_preserve_api_invariants to shift
       earlier if the naive cut splits a pair.
    """
    msgs = messages or []
    if not msgs or max_keep_count <= 0:
        return 0
    if max_keep_count >= len(msgs):
        return 0
    candidate = len(msgs) - max_keep_count
    return adjust_index_to_preserve_api_invariants(msgs, candidate)
