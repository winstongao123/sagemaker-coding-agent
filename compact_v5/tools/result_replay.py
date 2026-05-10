"""Replay durable tool-result artifacts by stable reference."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .registry import all_registered, build_tool, find_tool_by_name, register
from runtime.results import RESULTS
from runtime.tool_surface import semantic_number


_DESCRIPTION = """Reads a full persisted tool-result artifact by stable ref.

Use this when a previous tool_result says it was persisted as
sageagent-result://... because the model-visible output was shortened.
Supports optional character offset and limit for inspecting large outputs in
chunks without loading the whole artifact into the conversation."""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "ref": {
            "type": "string",
            "description": "Stable result reference, e.g. sageagent-result://session/result-id.",
        },
        "offset": {
            "type": "integer",
            "description": "Character offset to start replaying from. Default 0.",
        },
        "limit": {
            "type": "integer",
            "description": "Maximum characters to return. Default 50000.",
        },
    },
    "required": ["ref"],
}


def _execute(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    ref = args.get("ref")
    if not isinstance(ref, str) or not ref:
        return "Error: ref is required and must be a non-empty string"
    try:
        offset = int(semantic_number(args.get("offset", 0), integer=True))
    except (TypeError, ValueError):
        return f"Error: offset must be a non-negative integer; got {args.get('offset')!r}"
    try:
        limit = int(semantic_number(args.get("limit", 50_000), integer=True))
    except (TypeError, ValueError):
        return f"Error: limit must be a positive integer; got {args.get('limit')!r}"
    if offset < 0:
        return f"Error: offset must be >=0; got {offset}"
    if limit < 1:
        return f"Error: limit must be >=1; got {limit}"
    return RESULTS.read(ref, offset=offset, limit=limit)


def _register():
    existing = find_tool_by_name(all_registered(), "result_replay")
    if existing is not None:
        return existing
    return register(build_tool(
        name="result_replay",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_execute,
        is_read_only=True,
        is_concurrency_safe=True,
        requires_approval=False,
        search_hint="replay full persisted tool results by sageagent-result reference",
    ))
