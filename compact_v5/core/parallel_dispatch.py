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
defined here and wired into core/query_engine.py for synchronous, non-streaming
tool dispatch. Real-AWS/R-tier validation remains gated by explicit approval,
but Block N owns the local dispatcher and QueryEngine integration contract.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import hashlib
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# Hermes parallel ceiling. v5 inherits the same value.
MAX_TOOL_WORKERS: int = 4

NEVER_PARALLEL_TOOLS: frozenset = frozenset({
    "bash",
    "python_exec",
    "task",
    "ask_user",
    "view_image",
    "web_fetch",
})

PARALLEL_SAFE_TOOLS: frozenset = frozenset({
    "read_file",
    "glob",
    "grep",
    "list_dir",
    "semantic_search",
    "todo_read",
    "skill",
})

PATH_SCOPED_TOOLS: frozenset = frozenset({
    "read_file",
    "write_file",
    "edit_file",
    "notebook_edit",
})

_NEVER_PARALLEL_TOOLS = NEVER_PARALLEL_TOOLS
_PARALLEL_SAFE_TOOLS = PARALLEL_SAFE_TOOLS
_PATH_SCOPED_TOOLS = PATH_SCOPED_TOOLS
_MAX_TOOL_WORKERS = MAX_TOOL_WORKERS


@dataclass(frozen=True)
class ToolDispatchSnapshot:
    """Checkpoint snapshot for a tool dispatch worker."""

    tid: str
    tool_name: str
    status: str
    args_hash: str = ""
    result_summary: str = ""


@dataclass(frozen=True)
class ToolRetryClassification:
    """Retry classification for non-streaming Bedrock/tool-call failures."""

    stage: str
    retryable: bool
    recovery: str


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


def _extract_target_path(call_name: str, args: Dict[str, Any]) -> Optional[str]:
    """Extract the canonical target path from a tool call's args.

    Codex iter-1 finding #1: different mutator tools use different arg
    names — write_file/edit_file use `file_path`, notebook_edit uses
    `notebook_path`. Map each tool to its actual path arg.

    Codex iter-1 finding #2: canonicalize via os.path.normpath +
    os.path.abspath so calls like `x.py`, `./x.py`, `/abs/path/x.py`
    that resolve to the same file are detected as conflicting.
    """
    import os
    if not isinstance(args, dict):
        return None
    # Per-tool path arg name.
    raw: Optional[str]
    if call_name == "notebook_edit":
        raw = args.get("notebook_path")
    else:
        # write_file / edit_file / future mutators
        raw = args.get("file_path") or args.get("filepath")
    if not isinstance(raw, str) or not raw:
        return None
    # Canonicalize: absolute + normalized so x.py vs ./x.py vs /abs/x.py
    # collapse to the same key.
    try:
        return os.path.normpath(os.path.abspath(raw))
    except Exception:
        return raw


def detect_path_conflicts(calls: List[Any]) -> Dict[str, List[Any]]:
    """Block N: detect path conflicts within a parallel batch.

    Returns dict mapping conflicting CANONICAL path → list of calls
    touching that path. Caller serializes these calls instead of
    dispatching in parallel.

    Codex iter-1 fix: per-tool path arg + canonicalized comparison
    (see _extract_target_path).

    Read-only tools (read_file / grep / glob) don't conflict — they
    can read in parallel even on the same path.
    """
    by_path: Dict[str, List[Any]] = {}
    for call in calls:
        name = getattr(call, "name", None) or (
            call.get("name") if isinstance(call, dict) else None
        )
        if name not in _FILE_MUTATOR_TOOLS:
            continue
        args = getattr(call, "input", None) if not isinstance(call, dict) else call.get("input")
        path = _extract_target_path(name or "", args or {})
        if not path:
            continue
        by_path.setdefault(path, []).append(call)
    return {p: cs for p, cs in by_path.items() if len(cs) > 1}


def path_scope_key(call: Any) -> str:
    """Return a path-scope key for tools whose calls can conflict by path."""
    name = getattr(call, "name", None) or (
        call.get("name") if isinstance(call, dict) else None
    )
    args = getattr(call, "input", None) if not isinstance(call, dict) else call.get("input")
    return _extract_target_path(name or "", args or {}) or ""


def is_parallel_safe_call(call: Any, tool: Any = None) -> bool:
    """True when a call may run in a parallel batch."""
    name = getattr(call, "name", None) or (
        call.get("name") if isinstance(call, dict) else None
    )
    if name in NEVER_PARALLEL_TOOLS:
        return False
    if tool is not None:
        if getattr(tool, "requires_approval", False):
            return False
        if getattr(tool, "is_destructive", False):
            return False
        if getattr(tool, "is_concurrency_safe", False):
            return True
    return name in PARALLEL_SAFE_TOOLS


def plan_tool_dispatch(calls: List[Any], tools_by_name: Dict[str, Any]) -> Dict[str, Any]:
    """Split calls into parallel-safe and sequential groups with path conflict data."""
    kept, dropped = dedup_tool_calls(calls)
    conflicts = detect_path_conflicts(kept)
    conflict_ids = {
        id(call)
        for conflict_calls in conflicts.values()
        for call in conflict_calls
    }
    parallel: List[Any] = []
    sequential: List[Any] = []
    for call in kept:
        name = getattr(call, "name", None) or (
            call.get("name") if isinstance(call, dict) else None
        )
        tool = tools_by_name.get(name or "")
        if id(call) not in conflict_ids and is_parallel_safe_call(call, tool):
            parallel.append(call)
        else:
            sequential.append(call)
    return {
        "parallel": parallel,
        "sequential": sequential,
        "dropped": dropped,
        "conflicts": conflicts,
    }


def execute_parallel_tool_calls(
    calls: List[Any],
    execute_one: Callable[[Any], Dict[str, Any]],
    checkpoint_callback: Optional[Callable[[ToolDispatchSnapshot], None]] = None,
) -> List[Dict[str, Any]]:
    """Run parallel-safe calls with MAX_TOOL_WORKERS and preserve input order."""
    if not calls:
        return []
    results: Dict[int, Dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=MAX_TOOL_WORKERS) as pool:
        futures = {}
        for idx, call in enumerate(calls):
            name = getattr(call, "name", None) or (
                call.get("name") if isinstance(call, dict) else None
            )
            args = getattr(call, "input", None) if not isinstance(call, dict) else call.get("input")
            tid = getattr(call, "id", None) or (
                call.get("id") if isinstance(call, dict) else str(idx)
            )
            if checkpoint_callback:
                checkpoint_callback(ToolDispatchSnapshot(str(tid), name or "", "started", _args_hash(args)))
            futures[pool.submit(execute_one, call)] = (idx, str(tid), name or "", _args_hash(args))
        for future in as_completed(futures):
            idx, tid, name, args_hash = futures[future]
            try:
                result = future.result()
                results[idx] = result
                status = "finished"
                summary = str(result.get("content", ""))[:120] if isinstance(result, dict) else ""
            except Exception as exc:  # noqa: BLE001
                results[idx] = {
                    "type": "tool_result",
                    "tool_use_id": tid,
                    "content": f"error_during_execution: {type(exc).__name__}: {exc}",
                    "is_error": True,
                }
                status = "error"
                summary = f"{type(exc).__name__}: {exc}"
            if checkpoint_callback:
                checkpoint_callback(ToolDispatchSnapshot(tid, name, status, args_hash, summary))
    return [results[idx] for idx in range(len(calls))]


def enforce_turn_budget(messages: List[Dict[str, Any]], num_tools: int, max_chars: int) -> List[Dict[str, Any]]:
    """Clamp aggregate tool_result content over the last num_tools messages."""
    if num_tools <= 0 or max_chars <= 0:
        return list(messages)
    out = json.loads(json.dumps(messages, ensure_ascii=False, default=str))
    start = max(0, len(out) - num_tools)
    used = 0
    for msg in out[start:]:
        content = msg.get("content")
        blocks = content if isinstance(content, list) else []
        for block in blocks:
            if not isinstance(block, dict) or block.get("type") != "tool_result":
                continue
            text = str(block.get("content", ""))
            remaining = max_chars - used
            if remaining <= 0:
                block["content"] = "[truncated by turn tool-result budget]"
                continue
            if len(text) > remaining:
                block["content"] = text[:remaining] + "\n[truncated by turn tool-result budget]"
                used = max_chars
            else:
                used += len(text)
    return out


def pending_tool_use_ids(tool_calls: List[Any]) -> List[str]:
    return [
        str(getattr(call, "id", None) or (call.get("id") if isinstance(call, dict) else ""))
        for call in tool_calls or []
        if getattr(call, "id", None) or (isinstance(call, dict) and call.get("id"))
    ]


def classify_tool_retry(stage: str, exc: BaseException | str) -> ToolRetryClassification:
    """Classify pre-call, mid-call, and post-call non-streaming retry behavior."""
    text = str(exc).lower()
    stage = stage if stage in {"pre_call", "mid_call", "post_call"} else "post_call"
    if stage == "pre_call":
        return ToolRetryClassification(stage, True, "retry_before_tool_dispatch")
    if stage == "mid_call":
        return ToolRetryClassification(stage, True, "emit_stub_and_retry")
    if "validation" in text or "accessdenied" in text or "permission" in text:
        return ToolRetryClassification(stage, False, "surface_user_error")
    return ToolRetryClassification(stage, True, "retry_after_tool_results")


def mid_call_stub_recovery(tool_use_ids: List[str], reason: str, output_fn: Callable[[str], None] = print) -> List[Dict[str, Any]]:
    output_fn(f"[mid-call-recovery] {len(tool_use_ids)} tool calls recovered with synthetic stubs: {reason}")
    return [
        synthetic_tool_result_stub(tool_use_id, reason=reason)
        for tool_use_id in tool_use_ids
    ]


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
