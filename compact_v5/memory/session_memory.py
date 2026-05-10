"""V5 memory/session_memory.py — Block H sessionMemoryUtils.

PORT_LOG: #096 (H-8 + H-9 + H-10).

Source: Runnable services/sessionMemory.ts + sessionMemoryUtils.ts.

Public functions:
- deduplicate_memory_entries(entries) — case-folded fuzzy dedup before write
- has_tool_calls_in_last_assistant_turn(messages) — H-9 predicate
- count_tool_calls_since(messages, since_index, tool_name="") — H-7 helper
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List


READ_ONLY_TOOL_NAMES = {
    "read",
    "read_file",
    "grep",
    "glob",
    "ls",
    "listdir",
    "list_dir",
}
WRITE_TOOL_NAMES = {"edit", "write", "edit_file", "write_file"}


def _input_path(tool_input: Any) -> str:
    if isinstance(tool_input, str):
        return tool_input
    if not isinstance(tool_input, dict):
        return ""
    for key in ("path", "file_path", "filepath", "target_path"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
    return ""


def _same_file(expected: str, actual: str) -> bool:
    if not actual:
        return False
    try:
        return Path(expected).resolve() == Path(actual).resolve()
    except Exception:
        return False


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


def wait_for_session_memory_extraction(
    extractor: Any,
    timeout_s: float = 5.0,
) -> bool:
    """H-8: wait for any in-flight session-memory extraction to drain."""
    drain = getattr(extractor, "drain_pending_extraction", None)
    if not callable(drain):
        return True
    return bool(drain(timeout_s=timeout_s))


def create_memory_file_can_use_tool(memory_file_path: str) -> Callable[[str, Any], bool]:
    """H-10: permission predicate for a single memory file.

    Read-only discovery tools are allowed. Edit/Write are allowed only when the
    target path resolves to exactly `memory_file_path`.
    """

    def can_use(tool_name: str, tool_input: Any = None) -> bool:
        name = (tool_name or "").strip().lower()
        if name in READ_ONLY_TOOL_NAMES:
            return True
        if name in WRITE_TOOL_NAMES:
            return _same_file(memory_file_path, _input_path(tool_input))
        return False

    return can_use
