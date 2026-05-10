"""Structured request/task tracking tools.

These tools complement `todo_write`: todos remain a lightweight working list,
while task_state records durable request IDs, owners, dependencies, notes, and
evidence paths for long supervisor-style work.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from .registry import build_tool, register


_VALID_STATUS = {"pending", "in_progress", "blocked", "completed", "cancelled"}


def _now() -> str:
    from runtime.state import _utc_now
    return _utc_now()


def _load() -> List[Dict[str, Any]]:
    try:
        from runtime.state import STATE
        return _normalize_tasks(STATE.load_tasks())
    except Exception:
        return []


def _save(tasks: List[Dict[str, Any]]) -> None:
    from runtime.state import STATE
    STATE.save_tasks(_normalize_tasks(tasks))


def _slug(value: str) -> str:
    raw = re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-").upper()
    return raw[:24] or "TASK"


def _next_id(tasks: List[Dict[str, Any]], subject: str) -> str:
    prefix = _slug(subject)
    used = {str(t.get("id", "")) for t in tasks}
    for i in range(1, 10000):
        candidate = f"{prefix}-{i:03d}"
        if candidate not in used:
            return candidate
    return f"{prefix}-9999"


def _strings(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)]


def _normalize_task(raw: Dict[str, Any]) -> Dict[str, Any]:
    status = str(raw.get("status", "pending")).strip() or "pending"
    if status not in _VALID_STATUS:
        status = "pending"
    return {
        "id": str(raw.get("id", "")).strip(),
        "subject": str(raw.get("subject", "")).strip(),
        "description": str(raw.get("description", "")).strip(),
        "status": status,
        "owner": str(raw.get("owner", "")).strip(),
        "activeForm": str(raw.get("activeForm", "")).strip(),
        "notes": str(raw.get("notes", "")).strip(),
        "evidence_paths": _strings(raw.get("evidence_paths")),
        "blocks": _strings(raw.get("blocks")),
        "blocked_by": _strings(raw.get("blocked_by")),
        "created_at": str(raw.get("created_at", "")).strip(),
        "updated_at": str(raw.get("updated_at", "")).strip(),
    }


def _normalize_tasks(raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        task = _normalize_task(item)
        if not task["id"] or task["id"] in seen:
            continue
        seen.add(task["id"])
        out.append(task)
    return out


def _find(tasks: List[Dict[str, Any]], task_id: str) -> Optional[Dict[str, Any]]:
    for task in tasks:
        if task.get("id") == task_id:
            return task
    return None


def _append_unique(task: Dict[str, Any], field: str, values: Any) -> None:
    current = list(task.get(field, []) or [])
    for value in _strings(values):
        if value not in current:
            current.append(value)
    task[field] = current


def _task_create_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    subject = str(args.get("subject", "")).strip()
    description = str(args.get("description", "")).strip()
    if not subject:
        return "Error: subject is required"
    tasks = _load()
    stamp = _now()
    task = _normalize_task({
        "id": str(args.get("id", "")).strip() or _next_id(tasks, subject),
        "subject": subject,
        "description": description,
        "status": str(args.get("status", "pending")).strip() or "pending",
        "owner": str(args.get("owner", "")).strip(),
        "activeForm": str(args.get("activeForm", "")).strip(),
        "notes": str(args.get("notes", "")).strip(),
        "evidence_paths": args.get("evidence_paths"),
        "blocks": args.get("blocks"),
        "blocked_by": args.get("blocked_by"),
        "created_at": stamp,
        "updated_at": stamp,
    })
    if _find(tasks, task["id"]):
        return f"Error: task id already exists: {task['id']}"
    tasks.append(task)
    _save(tasks)
    return json.dumps({"created": task}, indent=2, sort_keys=True)


def _task_update_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    task_id = str(args.get("id", "")).strip()
    if not task_id:
        return "Error: id is required"
    tasks = _load()
    task = _find(tasks, task_id)
    if task is None:
        return f"Error: task not found: {task_id}"
    for field in ("subject", "description", "owner", "activeForm", "notes"):
        if field in args and args.get(field) is not None:
            task[field] = str(args.get(field, "")).strip()
    if "status" in args and args.get("status") is not None:
        status = str(args.get("status", "")).strip()
        if status not in _VALID_STATUS:
            return f"Error: status must be one of {', '.join(sorted(_VALID_STATUS))}"
        task["status"] = status
    _append_unique(task, "evidence_paths", args.get("add_evidence_paths"))
    _append_unique(task, "blocks", args.get("add_blocks"))
    _append_unique(task, "blocked_by", args.get("add_blocked_by"))
    task["updated_at"] = _now()
    _save(tasks)
    return json.dumps({"updated": task}, indent=2, sort_keys=True)


def _task_list_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    include_completed = bool(args.get("include_completed", False))
    tasks = _load()
    if not include_completed:
        tasks = [t for t in tasks if t.get("status") not in {"completed", "cancelled"}]
    return json.dumps({"tasks": tasks, "count": len(tasks)}, indent=2, sort_keys=True)


_TASK_CREATE_SCHEMA = {
    "type": "object",
    "properties": {
        "subject": {"type": "string", "description": "Brief actionable task title."},
        "description": {"type": "string", "description": "Detailed requirement or acceptance notes."},
        "id": {"type": "string", "description": "Optional stable id. Auto-generated when omitted."},
        "status": {"type": "string", "enum": sorted(_VALID_STATUS), "default": "pending"},
        "owner": {"type": "string", "description": "Owner such as parent, review, build, or a worker name."},
        "activeForm": {"type": "string", "description": "Short in-progress wording."},
        "notes": {"type": "string"},
        "evidence_paths": {"type": "array", "items": {"type": "string"}},
        "blocks": {"type": "array", "items": {"type": "string"}},
        "blocked_by": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["subject"],
}

_TASK_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "description": "Task id returned by task_create."},
        "subject": {"type": "string"},
        "description": {"type": "string"},
        "status": {"type": "string", "enum": sorted(_VALID_STATUS)},
        "owner": {"type": "string"},
        "activeForm": {"type": "string"},
        "notes": {"type": "string"},
        "add_evidence_paths": {"type": "array", "items": {"type": "string"}},
        "add_blocks": {"type": "array", "items": {"type": "string"}},
        "add_blocked_by": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["id"],
}

_TASK_LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "include_completed": {
            "type": "boolean",
            "description": "Include completed and cancelled tasks.",
            "default": False,
        }
    },
}


def _register():
    from .registry import all_registered, find_tool_by_name

    if find_tool_by_name(all_registered(), "task_create") is None:
        register(build_tool(
            name="task_create",
            description=(
                "Create a durable structured task/request record with id, owner, "
                "dependencies, notes, and evidence paths. Use for long supervisor work."
            ),
            input_schema=_TASK_CREATE_SCHEMA,
            execute=_task_create_executor,
            requires_approval=False,
            should_defer=True,
            max_result_size_chars=6000,
        ))
    if find_tool_by_name(all_registered(), "task_update") is None:
        register(build_tool(
            name="task_update",
            description=(
                "Update durable task/request status, owner, notes, dependencies, "
                "or evidence paths. Use after each significant step."
            ),
            input_schema=_TASK_UPDATE_SCHEMA,
            execute=_task_update_executor,
            requires_approval=False,
            should_defer=True,
            max_result_size_chars=6000,
        ))
    if find_tool_by_name(all_registered(), "task_list") is None:
        register(build_tool(
            name="task_list",
            description="List durable structured tasks/requests for status tracking.",
            input_schema=_TASK_LIST_SCHEMA,
            execute=_task_list_executor,
            requires_approval=False,
            should_defer=True,
            max_result_size_chars=12000,
        ))
