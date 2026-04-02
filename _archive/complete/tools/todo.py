"""
Todo Tools - Task tracking and management
"""
from typing import List, Dict

# Lazy import
Tool = None


def _get_tool_class():
    global Tool
    if Tool is None:
        from core.tools import Tool as T
        Tool = T
    return Tool


# Global todo storage (per session, stored in context)
_todos: List[Dict] = []


def todo_write(args: dict, ctx) -> str:
    """Update todo list."""
    global _todos
    _todos = args["todos"]

    # Format for display
    lines = ["Todo List Updated:"]
    for todo in _todos:
        status = todo.get("status", "pending")
        content = todo.get("content", "")

        status_icon = {"pending": "[ ]", "in_progress": "[>]", "completed": "[x]"}.get(
            status, "[?]"
        )

        lines.append(f"  {status_icon} {content}")

    # Count by status
    pending = sum(1 for t in _todos if t.get("status") == "pending")
    in_progress = sum(1 for t in _todos if t.get("status") == "in_progress")
    completed = sum(1 for t in _todos if t.get("status") == "completed")

    lines.append("")
    lines.append(f"  ({pending} pending, {in_progress} in progress, {completed} completed)")

    return "\n".join(lines)


def todo_read(args: dict, ctx) -> str:
    """Read current todo list."""
    global _todos

    if not _todos:
        return "No todos. Use todo_write to create a task list."

    lines = ["Current Todos:"]
    for i, todo in enumerate(_todos, 1):
        status = todo.get("status", "pending")
        content = todo.get("content", "")
        active_form = todo.get("activeForm", "")

        status_icon = {"pending": "[ ]", "in_progress": "[>]", "completed": "[x]"}.get(
            status, "[?]"
        )

        line = f"  {i}. {status_icon} {content}"
        if status == "in_progress" and active_form:
            line += f" (currently: {active_form})"

        lines.append(line)

    return "\n".join(lines)


def get_todos() -> List[Dict]:
    """Get current todo list (for external access)."""
    global _todos
    return _todos.copy()


def clear_todos():
    """Clear all todos (for session reset)."""
    global _todos
    _todos = []


# Tool definitions
def get_tools():
    """Get all todo tools."""
    Tool = _get_tool_class()

    TODO_WRITE = Tool(
        name="todo_write",
        description="Create or update task list. Use for tracking multi-step work. Each todo needs: content (imperative form), activeForm (present continuous), status (pending/in_progress/completed).",
        parameters={
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Task description (imperative form, e.g., 'Fix the bug')",
                            },
                            "activeForm": {
                                "type": "string",
                                "description": "Present continuous form (e.g., 'Fixing the bug')",
                            },
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "completed"],
                                "description": "Task status",
                            },
                        },
                        "required": ["content", "activeForm", "status"],
                    },
                }
            },
            "required": ["todos"],
        },
        execute=todo_write,
        requires_approval=False,
    )

    TODO_READ = Tool(
        name="todo_read",
        description="Read current todo list to check task status.",
        parameters={"type": "object", "properties": {}, "required": []},
        execute=todo_read,
        requires_approval=False,
    )

    return TODO_WRITE, TODO_READ


# Export tools
TODO_WRITE, TODO_READ = get_tools()
