"""V5 memory/session_memory.py — Block H sessionMemoryUtils.

PORT_LOG: #096 (H-8 + H-9 + H-10).

Source: Runnable services/sessionMemory.ts + sessionMemoryUtils.ts.

Public functions:
- deduplicate_memory_entries(entries) — case-folded fuzzy dedup before write
- has_tool_calls_in_last_assistant_turn(messages) — H-9 predicate
- count_tool_calls_since(messages, since_index, tool_name="") — H-7 helper
"""
from __future__ import annotations

from typing import Any, Dict, List


def deduplicate_memory_entries(entries: List[str]) -> List[str]:
    """Dedup memory entries before write. Case-folded + whitespace-normalized
    equality; preserves first-seen casing.

    Per Runnable sessionMemoryUtils.ts: dedup is the LAST step before
    writing, so v5 keeps the same contract — call this before
    extractor._append_to_memory_md.
    """
    seen_keys = set()
    out: List[str] = []
    for entry in entries:
        if not isinstance(entry, str):
            continue
        # Normalize: case-folded (Unicode-aware, vs .lower() which is
        # ASCII-only for some characters) + collapse whitespace.
        # Codex iter-1 finding #3 fix: use str.casefold() not str.lower().
        key = " ".join(entry.casefold().split())
        if not key:
            continue
        if key in seen_keys:
            continue
        seen_keys.add(key)
        out.append(entry)
    return out


def has_tool_calls_in_last_assistant_turn(messages: List[Dict[str, Any]]) -> bool:
    """H-9 predicate: returns True iff the last assistant message in
    `messages` has any tool_use content blocks.

    Used by sessionMemoryCompact: don't compact while a tool_use is
    dangling (no matching tool_result yet) — that would leave the buffer
    in an invalid Bedrock-API state.

    Walks BACKWARDS to find the LAST assistant message. Returns False if
    no assistant message exists.
    """
    for m in reversed(messages or []):
        if m.get("role") != "assistant":
            continue
        content = m.get("content")
        if not isinstance(content, list):
            return False  # string content has no tool_use blocks
        for b in content:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                return True
        return False  # found last assistant; no tool_use
    return False


def count_tool_calls_since(
    messages: List[Dict[str, Any]],
    since_index: int = -1,
    tool_name: str = "",
) -> int:
    """H-7: count tool_use blocks in `messages` AFTER `since_index`.

    When `tool_name` is set, count only matching tool calls. When empty,
    counts all tool_use blocks. Used by extractMemories to detect
    "natural break" — accumulated tool calls without an extraction.
    """
    if since_index < 0:
        msgs = messages or []
    else:
        msgs = (messages or [])[since_index + 1:]
    count = 0
    for m in msgs:
        if m.get("role") != "assistant":
            continue
        content = m.get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict) or b.get("type") != "tool_use":
                continue
            if tool_name and b.get("name") != tool_name:
                continue
            count += 1
    return count
