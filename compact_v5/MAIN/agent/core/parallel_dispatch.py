"""V5 core/parallel_dispatch.py — Block N parallel tool dispatch + dedup +
fuzzy + ephemeral prompt + dynamic tool refs.

PORT_LOG: #102. ADR-037.

Source: Hermes run_agent.py + Runnable services/tools/dispatch.

Block N ships:
- MAX_TOOL_WORKERS = 4 (Hermes parallel tool dispatch ceiling).
- dedup_tool_calls — drops same-(name, args) duplicates within a batch.
- fuzzy_resolve_tool_name — difflib cutoff=0.7 (matches Hermes /
  Block I skill-name resolver pattern).
- mark_ephemeral_block / strip_ephemeral_blocks_for_persist — context
  blocks marked `_ephemeral=True` aren't persisted to session log.
- inject_dynamic_tool_refs — Hermes A36 dynamic-ref pattern.
- partial_tool_call_warning — Hermes H2 pattern: mid-call disconnect
  emits a synthetic tool_result stub so the API invariant holds.

The parallel-execution wiring (ThreadPoolExecutor at MAX_TOOL_WORKERS) is
defined here but not yet integrated into core/query_engine.py — that
integration is gated on Block J's real-AWS test fixtures (Block N
ships the dispatcher; Block J wires it into the engine).
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# Hermes parallel ceiling. v5 inherits the same value.
MAX_TOOL_WORKERS: int = 4


# Tools that mutate filesystem state — same path = serialization needed.
# Path-conflict serialization is the v5 read-parallel/write-serial rule.
_FILE_MUTATOR_TOOLS: frozenset = frozenset({
    "write_file", "edit_file", "notebook_edit",
})


def _args_hash(args: Any) -> str:
    """Stable hash of tool args for dedup. Same as Block C repetition
    detector — sha256 of canonical JSON, first 12 hex chars."""
    try:
        canonical = json.dumps(args or {}, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    except Exception:
        return "err"


def dedup_tool_calls(calls: List[Any]) -> Tuple[List[Any], List[Any]]:
    """Block N (PORT_LOG #102): dedup same-(name, args) tool calls within
    a batch.

    Returns (kept_calls, dropped_calls). The first occurrence of each
    (name, args_hash) is kept; subsequent duplicates are dropped (with
    a synthetic tool_result emitted by the caller).

    Args:
        calls: list of tool-call objects with .name and .input attributes
            (or dicts with "name" + "input" keys). Both shapes supported.

    Lock test: 3 identical calls → keep 1, drop 2.
    """
    seen: Set[Tuple[str, str]] = set()
    kept: List[Any] = []
    dropped: List[Any] = []
    for call in calls:
        name = getattr(call, "name", None) or (
            call.get("name") if isinstance(call, dict) else None
        )
        args = getattr(call, "input", None) if not isinstance(call, dict) else call.get("input")
        key = (name or "", _args_hash(args))
        if key in seen:
            dropped.append(call)
        else:
            seen.add(key)
            kept.append(call)
    return kept, dropped


def detect_path_conflicts(calls: List[Any]) -> Dict[str, List[Any]]:
    """Block N: detect path conflicts within a parallel batch.

    Returns dict mapping conflicting path → list of calls touching that
    path. Caller serializes these calls instead of dispatching in
    parallel.

    Currently checks file_path arg of file-mutator tools (write_file /
    edit_file / notebook_edit). Read-only tools (read_file / grep /
    glob) don't conflict — they can read in parallel even on the same
    path.
    """
    by_path: Dict[str, List[Any]] = {}
    for call in calls:
        name = getattr(call, "name", None) or (
            call.get("name") if isinstance(call, dict) else None
        )
        if name not in _FILE_MUTATOR_TOOLS:
            continue
        args = getattr(call, "input", None) if not isinstance(call, dict) else call.get("input")
        if not isinstance(args, dict):
            continue
        path = args.get("file_path") or args.get("filepath")
        if not isinstance(path, str) or not path:
            continue
        by_path.setdefault(path, []).append(call)
    return {p: cs for p, cs in by_path.items() if len(cs) > 1}


def fuzzy_resolve_tool_name(query: str, tool_names: List[str]) -> Optional[str]:
    """Block N: fuzzy-resolve a tool-name typo. Uses difflib's
    get_close_matches with cutoff=0.7 (same as Hermes + Block I skill
    resolver).

    Returns canonical tool_name or None when no match crosses cutoff.
    Exact match returns immediately (case-insensitive).
    """
    from difflib import get_close_matches

    if not query or not tool_names:
        return None

    # Exact (case-insensitive) match.
    ql = query.lower()
    name_map = {n.lower(): n for n in tool_names}
    if ql in name_map:
        return name_map[ql]

    matches = get_close_matches(ql, list(name_map.keys()), n=1, cutoff=0.7)
    if matches:
        return name_map[matches[0]]
    return None


def mark_ephemeral_block(block: Dict[str, Any]) -> Dict[str, Any]:
    """Block N: mark a content block as ephemeral so persistence layer
    skips it. Returns a new dict with `_ephemeral: True` tag.

    Used for transient prompts (system reminders, tool-discovered names,
    nudges) that should not bloat session storage on later reload.
    """
    out = dict(block)
    out["_ephemeral"] = True
    return out


def strip_ephemeral_blocks_for_persist(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter ephemeral blocks from messages before persistence.

    A block with `_ephemeral=True` is dropped. A message whose content
    list becomes empty after filtering is also dropped. String-content
    messages are passed through (no ephemeral mark applies).
    """
    out: List[Dict[str, Any]] = []
    for m in messages:
        content = m.get("content")
        if not isinstance(content, list):
            out.append(m)
            continue
        kept_blocks = [
            b for b in content
            if not (isinstance(b, dict) and b.get("_ephemeral") is True)
        ]
        if kept_blocks:
            new_msg = dict(m)
            new_msg["content"] = kept_blocks
            out.append(new_msg)
    return out


def inject_dynamic_tool_refs(
    tool_schemas: List[Dict[str, Any]],
    refs: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Block N (Hermes A36 dynamic-ref): inject cross-references into
    tool descriptions at init time.

    `refs` is a dict mapping tool_name → reference text to APPEND to
    that tool's description. Used to add "see tool X for related
    operation Y" cross-links without bloating individual tool docstrings.

    Returns a new list of schema dicts; original unmodified.
    """
    out: List[Dict[str, Any]] = []
    for schema in tool_schemas or []:
        name = schema.get("name", "")
        ref = refs.get(name, "")
        if ref:
            new = dict(schema)
            new["description"] = (schema.get("description", "") + "\n\n" + ref).strip()
            out.append(new)
        else:
            out.append(dict(schema))
    return out


def synthetic_tool_result_stub(tool_use_id: str, reason: str = "") -> Dict[str, Any]:
    """Block N (Hermes H2): emit a synthetic tool_result for a
    tool_use that was dropped (deduped) or whose dispatch was
    interrupted (mid-call disconnect). Preserves Bedrock API
    pair-invariant: every tool_use needs a matching tool_result.

    Returns a dict shaped as a tool_result content block.
    """
    text = "[synthetic stub: " + (reason or "tool dispatch was interrupted/deduped") + "]"
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": text,
        "is_error": False,
    }


def partial_tool_call_warning(
    interrupted_tool_use_ids: List[str],
    output_fn: Callable[[str], None] = print,
) -> List[Dict[str, Any]]:
    """Hermes H2 pattern: when an agent loop is interrupted mid-call,
    emit a warning AND return synthetic tool_result stubs so the next
    Bedrock invocation doesn't fail with "tool_use not paired".

    Returns the list of stubs to append as a user-role tool_result message.
    """
    if not interrupted_tool_use_ids:
        return []
    output_fn(
        f"[partial-tool-warning] {len(interrupted_tool_use_ids)} "
        "tool calls interrupted mid-execution; emitting synthetic stubs "
        "so the next API call satisfies the tool_use/tool_result pair invariant."
    )
    return [
        synthetic_tool_result_stub(tu_id, reason="agent loop interrupted")
        for tu_id in interrupted_tool_use_ids
    ]
