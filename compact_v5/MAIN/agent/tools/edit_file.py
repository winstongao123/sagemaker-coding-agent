"""Phase 4 edit_file tool — REUSE v4 executor + ADAPT Runnable prompt.

Per ADR-010:
- Executor body is a Phase-4 minimal port of v4 `tool_edit_file` at
  `compact_v4/MAIN/agent/sagemaker_agent.py:4729`. Keeps: must-read-first
  enforcement, exact-match enforcement, replace_all flag, stale-check
  (file modified externally since last read).
- Phase-5+8 deferred: SnapshotManager.save (snapshot-before-edit), auto-
  lint-Python, auto-commit-checkpoint, post-edit `git diff` summary.
- Description text is adapted from
  `gg-claude-code-runnable/src/tools/FileEditTool/prompt.ts`.

PORT_LOG: row #007.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from .registry import build_tool, register
from . import _path_validation as path_security
from . import _file_read_tracking as read_tracking


_DESCRIPTION = """Performs exact string replacements in files.

Usage:
- You MUST use read_file at least once in the conversation before editing. This tool will error if you attempt an edit without reading the file (prevents blind misplaced edits).
- When editing text from read_file output, ensure you preserve the exact indentation (tabs/spaces) as it appears AFTER the line number prefix. The line number prefix format is: line number + `|` + space. Everything after that is the actual file content to match. Never include any part of the line number prefix in old_string or new_string.
- ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
- The edit will FAIL if `old_string` is not unique in the file. Either provide a larger string with more surrounding context to make it unique, or use `replace_all=true` to change every instance of `old_string`.
- Use `replace_all=true` for replacing and renaming strings across the file. This parameter is useful for renaming a variable.
- Use the smallest old_string that's clearly unique — usually 2-4 adjacent lines is sufficient. Avoid including 10+ lines of context when less uniquely identifies the target.
- Approval prompt shows colored before/after diff inline + click-to-expand-full-file (per V5_PLAN.md Phase 4).
- Approval is required before the edit happens.

WHEN to use:
- Modifying specific sections of existing code (bug fixes, feature additions, refactoring)
- Renaming variables, functions, or strings across a file (with replace_all=true)
- Any targeted change to an existing file

WHEN NOT to use:
- Creating brand-new files → use write_file
- Complete file rewrites → use write_file
- Editing notebook cells → use notebook_edit
- Never use bash sed / awk to edit files — use this dedicated tool instead"""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Absolute path to the file to edit.",
        },
        "old_string": {
            "type": "string",
            "description": "Exact text to replace. Must match EXACTLY including indentation.",
        },
        "new_string": {
            "type": "string",
            "description": "Replacement text.",
        },
        "replace_all": {
            "type": "boolean",
            "description": "If true, replace every occurrence. Default false (must be unique).",
        },
    },
    "required": ["file_path", "old_string", "new_string"],
}


def _edit_file_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    file_path = args.get("file_path")
    old_string = args.get("old_string")
    new_string = args.get("new_string")
    replace_all = bool(args.get("replace_all", False))

    if not isinstance(file_path, str) or not file_path:
        return "Error: file_path is required and must be a non-empty string"
    if not isinstance(old_string, str):
        return "Error: old_string is required and must be a string"
    if not isinstance(new_string, str):
        return "Error: new_string is required and must be a string"
    if old_string == new_string:
        return "Error: old_string and new_string are identical — nothing to change"

    ok, msg = path_security.validate_path(file_path)
    if not ok:
        return f"Error: {msg}"

    abs_path = os.path.abspath(path_security.resolve_path(file_path))
    if not os.path.isfile(abs_path):
        return f"Error: File not found or not a regular file: {abs_path}"

    if not read_tracking.was_read(abs_path):
        return (
            "Error: Must read file before editing. Use read_file first to load the "
            "current state of the file, then retry the edit."
        )

    is_stale, stale_msg = read_tracking.is_stale(abs_path)
    if is_stale:
        return f"Error: {stale_msg}"

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        return f"Error: cannot read file: {e}"

    count = content.count(old_string)
    if count == 0:
        return "Error: old_string not found in file. Must be EXACT match (check indentation, line endings, exact characters)."
    if count > 1 and not replace_all:
        return (
            f"Error: old_string appears {count} times in the file. "
            f"Either provide a larger old_string with more context to make it unique, "
            f"or pass replace_all=true to change every occurrence."
        )

    new_content = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)

    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except OSError as e:
        return f"Error: cannot write file: {e}"

    # Re-mark read so the next edit doesn't falsely fail the staleness check.
    read_tracking.mark_read(abs_path)

    # Compute change summary
    old_lines = old_string.count("\n") + 1
    new_lines = new_string.count("\n") + 1
    pos = content.find(old_string)
    line_no = content[:pos].count("\n") + 1 if pos >= 0 else 1
    suffix = f" ({count} replacements)" if (count > 1 and replace_all) else ""
    return (
        f"Edited {os.path.basename(abs_path)} (line {line_no})\n"
        f"  -{old_lines} lines / +{new_lines} lines{suffix}"
    )


def _register():
    """Idempotent registration of edit_file. See read_file.py:_register."""
    from .registry import find_tool_by_name, all_registered
    if find_tool_by_name(all_registered(), "edit_file") is not None:
        return find_tool_by_name(all_registered(), "edit_file")
    return register(build_tool(
        name="edit_file",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_edit_file_executor,
        is_read_only=False,
        is_destructive=True,            # Modifies file content
        is_concurrency_safe=False,      # Two edits to same file race
        requires_approval=True,         # ADR-010: approval prompt with diff
        search_hint="exact string replace in file",
    ))
