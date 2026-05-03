"""V5 tools/todo.py — Block T todo_write + todo_read.

PORT_LOG: #103 (Block T). v4 parity tools for in-session todo tracking.
State is process-global (per-engine in v5; tests get isolated state).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .registry import build_tool, register


# Process-global todo list. Reset by tests via _reset_todos_for_tests.
_TODOS: List[Dict[str, Any]] = []


def _reset_todos_for_tests() -> None:
    _TODOS.clear()


def _todo_write_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    todos = args.get("todos") or []
    if not isinstance(todos, list):
        return "Error: todos must be a list of {content, status, activeForm}"
    new_todos: List[Dict[str, Any]] = []
    for t in todos:
        if not isinstance(t, dict):
            continue
        new_todos.append({
            "content": str(t.get("content", "")),
            "status": str(t.get("status", "pending")),
            "activeForm": str(t.get("activeForm", "")),
        })
    _TODOS.clear()
    _TODOS.extend(new_todos)
    return f"Wrote {len(new_todos)} todos."


def _todo_read_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    if not _TODOS:
        return "(no todos)"
    import json as _json
    return _json.dumps(_TODOS)


_TODO_WRITE_SCHEMA = {
    "type": "object",
    "properties": {
        "todos": {
            "type": "array",
            "description": "List of todos. Each: {content, status: pending|in_progress|completed, activeForm}.",
        },
    },
    "required": ["todos"],
}

_TODO_READ_SCHEMA = {"type": "object", "properties": {}}


def _register():
    from .registry import find_tool_by_name, all_registered

    if find_tool_by_name(all_registered(), "todo_write") is None:
        register(build_tool(
            name="todo_write",
            description="Replace the session's todo list. Use to track multi-step work.",
            input_schema=_TODO_WRITE_SCHEMA,
            execute=_todo_write_executor,
            requires_approval=False,
            should_defer=True,
            max_result_size_chars=500,
        ))
    if find_tool_by_name(all_registered(), "todo_read") is None:
        register(build_tool(
            name="todo_read",
            description="Read the session's current todo list as JSON.",
            input_schema=_TODO_READ_SCHEMA,
            execute=_todo_read_executor,
            requires_approval=False,
            should_defer=True,
            max_result_size_chars=2000,
        ))
