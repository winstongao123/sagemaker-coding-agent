"""Phase 3 list_dir tool — REUSE v4 verbatim. NO Runnable analog.

Per ADR-009:
- Executor body is a Phase-3 port of v4's `tool_list_dir` at
  `compact_v4/MAIN/agent/sagemaker_agent.py:4952`.
- Runnable does NOT expose a dedicated list_dir tool — its prompt tells
  the model to use `ls` via the Bash tool. v5 keeps a dedicated tool
  because (a) v4 has it, (b) plan mode forbids bash, so the model
  needs `list_dir` to inspect directories during read-only analysis,
  (c) it's the simplest possible tool — no maintenance burden.
- No PORT_LOG row added — pure v4 reuse, no Runnable adoption.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from .registry import build_tool, register
from . import _path_validation as path_security


_DESCRIPTION = """List the contents of a directory.

Usage:
- The path parameter must be an absolute path to a directory. Defaults to the workspace root if omitted.
- Returns up to 100 entries, sorted alphabetically.
- Each entry is prefixed `[DIR]` or `[FILE]`; files include their byte size.
- Use this in plan mode where bash `ls` is unavailable.

WHEN to use:
- Inspecting directory contents
- Discovering project layout when you don't yet have a glob pattern
- Plan-mode analysis (bash is disabled)

WHEN NOT to use:
- Reading a file → use read_file
- Searching by pattern across the tree → use glob (paths) or grep (contents)"""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "Absolute path to a directory. Defaults to workspace root.",
        },
    },
    "required": [],
}


def _list_dir_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    """Phase-3 executor — verbatim port of v4 `tool_list_dir`."""
    raw_path = args.get("path") or ""
    from runtime.config import CONFIG
    if raw_path:
        target = raw_path if os.path.isabs(raw_path) else os.path.join(CONFIG.workspace, raw_path)
    else:
        target = CONFIG.workspace

    ok, msg = path_security.validate_path(target)
    if not ok:
        return f"Error: {msg}"

    if not os.path.isdir(target):
        return f"Error: not a directory: {target}"

    try:
        entries = []
        for entry in sorted(os.listdir(target))[:100]:
            full = os.path.join(target, entry)
            if os.path.isdir(full):
                entries.append(f"[DIR]  {entry}/")
            else:
                try:
                    size = os.path.getsize(full)
                except OSError:
                    size = 0
                entries.append(f"[FILE] {entry} ({size:,} bytes)")
        return "\n".join(entries) if entries else "(empty directory)"
    except OSError as e:
        return f"Error: {e}"


# ============================================================
# Idempotent registration (Codex Phase-03 review finding 1)
# ============================================================

def _register():
    """Idempotent registration of the `list_dir` tool. See read_file.py:_register."""
    from .registry import find_tool_by_name, all_registered
    existing = find_tool_by_name(all_registered(), "list_dir")
    if existing is not None:
        return existing
    return register(build_tool(
        name="list_dir",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_list_dir_executor,
        is_read_only=True,
        is_concurrency_safe=True,
        requires_approval=False,
        search_hint="list directory contents",
    ))
