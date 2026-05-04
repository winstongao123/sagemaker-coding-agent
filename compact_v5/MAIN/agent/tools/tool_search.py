"""Phase 7 tool_search tool — deferred-loading lookup (port of Runnable's ToolSearchTool).

Per ADR-013:
- Source: gg-claude-code-runnable/src/tools/ToolSearchTool/ToolSearchTool.ts (471 LOC)
                                                       prompt.ts (121 LOC)

Three query modes (Runnable parity):
- bare exact name (e.g. `view_image`) → fast-path return that tool's schema.
- `select:Read,Edit,Grep` → exact-name fetch (case-insensitive).
- `+slack send` → required-term + ranking (slack MUST be in name OR description OR search_hint).
- `notebook jupyter` → keyword search across name + description + search_hint.

Result wire format: `<functions>{"description": ..., "name": ..., "parameters": ...}</functions>`
(Runnable text-level parity — model SEES the schemas).

**IMPORTANT — Phase 7 vs Phase 8 split** (Codex Phase-07 review finding 3):

Phase 7 lands the **QUERY mechanism**: tool_search returns `<functions>` text
with the matched schemas, AND records the discovered names in a Phase-8-
consumable structured form via `tool_search_discovered_names()`.

Phase 8 query_engine will land the **API wiring** that turns a discovered-
name into "this tool is added to the per-turn `tools=` API param on the next
turn" — making the deferred tool actually callable. v5 query_engine is
required to:
  1. Call `apply_tool_search_deferral(tools, enabled=True)` per turn.
  2. After each model turn, scan tool_use blocks for `tool_search` calls.
  3. Extract discovered names via `tool_search_discovered_names(...)` from
     the tool_search tool_result text.
  4. On the next turn, include those tools' full schemas in the `tools=`
     API param so they're callable.

PORT_LOG: #014 (ToolSearchTool.ts → executor) + #015 (prompt.ts → description + isDeferredTool).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from .registry import build_tool, register, find_tool_by_name, all_registered, ToolRecord
from runtime.tool_surface import XML_FUNCTIONS_TAG


# ============================================================
# Description (Runnable parity, drops feature-gate branches)
# ============================================================
_DESCRIPTION = """Fetches full schema definitions for deferred tools so they can be called.

Deferred tools appear by name in <system-reminder> messages. Until fetched, only the name is known — there is no parameter schema, so the tool cannot be invoked. This tool takes a query, matches it against the deferred tool list, and returns the matched tools' complete JSONSchema definitions inside a <functions> block. Once a tool's schema appears in that result, it is callable exactly like any tool defined at the top of the prompt.

Result format: each matched tool appears as one <function>{"description": "...", "name": "...", "parameters": {...}}</function> line inside the <functions> block — the same encoding as the tool list at the top of this prompt.

Query forms:
- "select:Read,Edit,Grep" — fetch these exact tools by name
- "notebook jupyter" — keyword search, up to max_results best matches
- "+slack send" — require "slack" in the name, rank by remaining terms"""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Query to find deferred tools. Use 'select:<tool_name>' for direct selection, or keywords to search.",
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results to return (default: 5)",
        },
    },
    "required": ["query"],
}


# ============================================================
# is_deferred_tool — port of Runnable prompt.ts:isDeferredTool
# ============================================================

def is_deferred_tool(tool_name: str) -> bool:
    """Return True if the named tool is deferred (only loadable via tool_search).

    Rules (Runnable parity, simplified for v5):
    - `always_load=True` → never deferred (explicit opt-out).
    - tool_search itself → never deferred.
    - Otherwise → deferred IFF `should_defer=True`.

    MCP tools default to deferred in Runnable (workflow-specific). v5 follows
    the same convention; future MCP integration will set `is_mcp=True` and
    this function will treat them as deferred-by-default (TODO Phase 11+).
    """
    tool = find_tool_by_name(all_registered(), tool_name)
    if tool is None:
        return False
    if tool.always_load:
        return False
    if tool.name == "tool_search":
        return False
    return tool.should_defer


# ============================================================
# Name parsing (Runnable parity: parseToolName)
# ============================================================

def _parse_tool_name(name: str) -> Tuple[List[str], str, bool]:
    """Split tool name into (parts, full, is_mcp) for keyword matching."""
    if name.startswith("mcp__"):
        without_prefix = name[len("mcp__"):].lower()
        parts: List[str] = []
        for seg in without_prefix.split("__"):
            parts.extend(p for p in seg.split("_") if p)
        full = without_prefix.replace("__", " ").replace("_", " ")
        return parts, full, True

    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", name).replace("_", " ").lower()
    parts = [p for p in spaced.split() if p]
    return parts, " ".join(parts), False


def _haystack_for_tool(tool: ToolRecord) -> str:
    """Build the searchable haystack text for one tool. Includes name parts +
    description + search_hint (Codex Phase-07 review finding 4 — Runnable
    checks all three, not just name)."""
    _, full_name, _ = _parse_tool_name(tool.name)
    desc = (tool.description or "").lower()
    hint = (tool.search_hint or "").lower()
    return f"{full_name} {desc} {hint}"


# ============================================================
# Active-tools resolution (Codex Phase-07 review finding 2)
# ============================================================

def _resolve_active_tools(context: Optional[Dict[str, Any]]) -> List[ToolRecord]:
    """Return the per-turn allowed tool pool.

    Codex finding 2: tool_search must search ONLY the current per-turn pool
    (after deny-rules + plan-mode filtering), not the global registry. Phase 8
    query_engine MUST pass `context["active_tools"]`. If absent, fall back to
    `all_registered()` with a warning.
    """
    if context and isinstance(context.get("active_tools"), list):
        return list(context["active_tools"])
    logging.warning(
        "[tool_search] context['active_tools'] not provided; falling back to "
        "all_registered(). Phase 8 query_engine MUST pass active_tools so deny-"
        "rules + plan-mode filtering apply to deferred-tool lookups."
    )
    return all_registered()


# ============================================================
# Query modes
# ============================================================

def _bare_exact_name_match(query: str, deferred_tools: List[ToolRecord]) -> Optional[str]:
    """Codex finding (PATTERN 014): Runnable has a fast-path for queries that
    are just a bare tool name. Models from sub-agents / post-compaction
    sometimes use `view_image` instead of `select:view_image`. Match
    case-insensitively."""
    q = query.strip().lower()
    if not q or " " in q or q.startswith("select:") or q.startswith("+"):
        return None
    for t in deferred_tools:
        if t.name.lower() == q:
            return t.name
    return None


def _select_query(query: str, deferred_tools: List[ToolRecord]) -> List[str]:
    """`select:Name1,Name2,...` mode."""
    targets = [n.strip().lower() for n in query[len("select:"):].split(",") if n.strip()]
    deferred_lower = {t.name.lower(): t.name for t in deferred_tools}
    return [deferred_lower[t] for t in targets if t in deferred_lower]


def _required_term_query(query: str, deferred_tools: List[ToolRecord], max_results: int) -> List[str]:
    """`+term rest` mode — `term` MUST appear in name + description + search_hint
    (Codex finding 4); remaining terms rank.
    """
    tokens = query.strip().split()
    if not tokens or not tokens[0].startswith("+"):
        return []
    required = tokens[0].lstrip("+").lower()
    optional = [t.lower() for t in tokens[1:]]

    candidates: List[Tuple[str, int]] = []
    for tool in deferred_tools:
        haystack = _haystack_for_tool(tool)
        if required not in haystack:
            continue
        score = sum(1 for t in optional if t in haystack)
        candidates.append((tool.name, score))
    candidates.sort(key=lambda x: (-x[1], x[0]))
    return [c[0] for c in candidates[:max_results]]


def _keyword_query(query: str, deferred_tools: List[ToolRecord], max_results: int) -> List[str]:
    """Keyword search over name + description + search_hint."""
    terms = [t.lower() for t in query.strip().split() if t]
    if not terms:
        return []
    term_patterns = [re.compile(rf"\b{re.escape(t)}\b") for t in terms]

    candidates: List[Tuple[str, int]] = []
    for tool in deferred_tools:
        haystack = _haystack_for_tool(tool)
        score = sum(1 for p in term_patterns if p.search(haystack))
        if score > 0:
            candidates.append((tool.name, score))
    candidates.sort(key=lambda x: (-x[1], x[0]))
    return [c[0] for c in candidates[:max_results]]


# ============================================================
# Wire format + Phase-8 structured-result helper
# ============================================================

_DISCOVERED_NAMES_TAG = "<!-- v5_discovered:"
_DISCOVERED_NAMES_TAG_END = "-->"


def _format_functions_block(matched_names: List[str], all_active: List[ToolRecord]) -> str:
    """Build the `<functions>...</functions>` wire block + a hidden HTML-style
    comment that Phase-8 query_engine uses to extract the discovered names.

    The visible portion (`<functions>...</functions>`) is Runnable wire-format
    parity — the model sees the schemas. The hidden marker is v5-specific
    (Phase-7 / Phase-8 contract) so query_engine can reliably extract the
    discovered names without re-parsing the JSON."""
    if not matched_names:
        # Still embed the (empty) discovered marker so query_engine has a
        # consistent extraction path.
        return (
            f"<{XML_FUNCTIONS_TAG}>\n(no matches)\n</{XML_FUNCTIONS_TAG}>\n"
            f"{_DISCOVERED_NAMES_TAG}{_DISCOVERED_NAMES_TAG_END}"
        )
    lines = [f"<{XML_FUNCTIONS_TAG}>"]
    for name in matched_names:
        tool = next((t for t in all_active if t.name == name), None)
        if tool is None:
            continue
        entry = {
            "description": tool.description,
            "name": tool.name,
            "parameters": tool.input_schema,
        }
        lines.append(json.dumps(entry, ensure_ascii=False))
    lines.append(f"</{XML_FUNCTIONS_TAG}>")
    # Hidden marker for Phase 8 query_engine extraction.
    discovered_csv = ",".join(matched_names)
    lines.append(f"{_DISCOVERED_NAMES_TAG}{discovered_csv}{_DISCOVERED_NAMES_TAG_END}")
    return "\n".join(lines)


def tool_search_discovered_names(tool_result_text: str) -> List[str]:
    """Extract the list of names discovered by a prior tool_search invocation.

    Phase-7 deliverable for Phase-8 wiring. Phase 8 query_engine calls this
    on each tool_result for tool_search, then includes those tools in the
    next turn's `tools=` API param so they become callable.

    Returns an empty list if the marker is absent or empty.
    """
    start = tool_result_text.find(_DISCOVERED_NAMES_TAG)
    if start < 0:
        return []
    start += len(_DISCOVERED_NAMES_TAG)
    end = tool_result_text.find(_DISCOVERED_NAMES_TAG_END, start)
    if end < 0:
        return []
    csv = tool_result_text[start:end].strip()
    if not csv:
        return []
    return [n.strip() for n in csv.split(",") if n.strip()]


# ============================================================
# Executor
# ============================================================

def _tool_search_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    """Phase-7 tool_search executor.

    Sequence:
      1. Validate query (non-empty string).
      2. Normalise max_results.
      3. Resolve active tool pool from context (Codex finding 2).
      4. Filter to deferred subset.
      5. Bare exact name fast path → return that tool's schema directly.
      6. Dispatch on query mode (select / +required / keyword).
      7. Return `<functions>` block with matched schemas + discovered-names marker.
    """
    query = args.get("query")
    if not isinstance(query, str) or not query.strip():
        return "Error: query is required and must be a non-empty string"

    raw_max = args.get("max_results", 5)
    try:
        max_results = int(raw_max)
    except (TypeError, ValueError):
        return f"Error: max_results must be an integer; got {raw_max!r}"
    max_results = max(1, min(max_results, 50))

    active_tools = _resolve_active_tools(context)
    deferred_tools = [t for t in active_tools if is_deferred_tool(t.name)]

    if not deferred_tools:
        return (
            "<functions>\n"
            "(no deferred tools in current active set -- apply_tool_search_deferral "
            "may be disabled, or no tools have should_defer=True in this pool)\n"
            "</functions>\n"
            f"{_DISCOVERED_NAMES_TAG}{_DISCOVERED_NAMES_TAG_END}"
        )

    q = query.strip()

    # Bare exact-name fast path (Codex Phase-07 review)
    bare_match = _bare_exact_name_match(q, deferred_tools)
    if bare_match is not None:
        return _format_functions_block([bare_match], deferred_tools)

    if q.lower().startswith("select:"):
        matches = _select_query(q, deferred_tools)
    elif q.startswith("+"):
        matches = _required_term_query(q, deferred_tools, max_results)
    else:
        matches = _keyword_query(q, deferred_tools, max_results)

    return _format_functions_block(matches, deferred_tools)


# ============================================================
# Idempotent registration — always_load=True (never deferred)
# ============================================================

def _register():
    """Idempotent registration of tool_search."""
    if find_tool_by_name(all_registered(), "tool_search") is not None:
        return find_tool_by_name(all_registered(), "tool_search")
    return register(build_tool(
        name="tool_search",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_tool_search_executor,
        is_read_only=True,
        is_destructive=False,
        is_concurrency_safe=True,
        requires_approval=False,
        always_load=True,             # NEVER deferred itself (Runnable parity)
        search_hint="load deferred tool schemas",
    ))
