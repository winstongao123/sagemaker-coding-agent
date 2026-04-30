"""Phase 4 write_file tool — REUSE v4 executor + ADAPT Runnable prompt.

Per ADR-010:
- Executor body is a Phase-4 minimal port of v4 `tool_write_file` at
  `compact_v4/MAIN/agent/sagemaker_agent.py:4632`. The Phase-4 minimal port
  keeps the security check, the read-before-overwrite enforcement, and
  basic file write. Phase-5+8 additions (secrets scan, snapshot, auto-lint,
  auto-commit) are noted inline and added at the appropriate phase.
- Description text is adapted from
  `gg-claude-code-runnable/src/tools/FileWriteTool/prompt.ts`.

PORT_LOG: row #006.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from .registry import build_tool, register
from . import _path_validation as path_security
from . import _file_read_tracking as read_tracking


_DESCRIPTION = """Writes content to a file, creating it if it doesn't exist or overwriting if it does.

Usage:
- This tool will OVERWRITE the existing file if there is one at the provided path.
- If this is an existing file, you MUST use read_file first to read its contents. This tool will error if you haven't read the file (prevents blind clobber).
- Prefer edit_file for modifying existing files — it only sends the diff portion, saving tokens. Use write_file only for creating new files or complete rewrites.
- Supports `mode='write'` (default — overwrites entire file) and `mode='append'` (adds to end). Append mode does NOT require a prior read.
- The file_path parameter must be an absolute path, not a relative path. Parent directories are created automatically.
- Approval prompt shows colored before/after diff (green = added, red = removed) inline + click-to-expand-full-file (per V5_PLAN.md Phase 4).
- Approval is required before the write happens.

WHEN to use:
- Creating a brand-new file that doesn't exist yet
- Complete rewrite of an existing file (after reading it first)
- Appending content to the end of a file (mode='append')

WHEN NOT to use:
- Modifying specific sections of an existing file → use edit_file (cheaper, safer, fewer tokens)
- Editing notebook cells → use notebook_edit
- Never use bash echo / heredoc / cat to write files — use this dedicated tool instead"""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Absolute path to the file to write.",
        },
        "content": {
            "type": "string",
            "description": "Content to write.",
        },
        "mode": {
            "type": "string",
            "enum": ["write", "append"],
            "description": "'write' (default) overwrites the entire file. 'append' adds to the end without requiring a prior read.",
        },
    },
    "required": ["file_path", "content"],
}


def _write_file_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    file_path = args.get("file_path")
    content = args.get("content")
    mode = args.get("mode", "write")

    if not isinstance(file_path, str) or not file_path:
        return "Error: file_path is required and must be a non-empty string"
    if not isinstance(content, str):
        return "Error: content is required and must be a string"
    if mode not in ("write", "append"):
        return f"Error: mode must be 'write' or 'append'; got {mode!r}"

    ok, msg = path_security.validate_path(file_path)
    if not ok:
        return f"Error: {msg}"

    abs_path = os.path.abspath(path_security.resolve_path(file_path))

    # v4 parity: in 'write' mode, refuse to clobber an existing file unless
    # the agent has read it first. Phase-8 query_engine populates
    # `_file_read_tracking` whenever read_file is invoked.
    if mode == "write" and os.path.exists(abs_path) and not read_tracking.was_read(abs_path):
        return (
            "Error: Must read file before overwriting. Use read_file first, "
            "or use mode='append' to add content without prior read."
        )

    # Phase-5 deferred: secrets scan (v4 SECURITY.scan_secrets) — landing in
    # Phase 5 with the full security/ port. Phase 4 ships without it because
    # the secrets scanner depends on the Phase-5 SecurityManager state.
    # Phase-5 ADR will reconcile this gap.

    try:
        # Phase-8 deferred: SnapshotManager.save (snapshot-before-write for revert).
        # Lands with Phase 8 query_engine session machinery.
        dir_path = os.path.dirname(abs_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        open_mode = "a" if mode == "append" else "w"
        with open(abs_path, open_mode, encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        return f"Error writing file: {e}"

    # After write, the file's "current state" is what we just wrote, so mark
    # it as read so a subsequent edit_file doesn't trip the read-first check.
    read_tracking.mark_read(abs_path)

    return f"Written {len(content):,} chars to {abs_path}"


def _register():
    """Idempotent registration of write_file. See read_file.py:_register."""
    from .registry import find_tool_by_name, all_registered
    if find_tool_by_name(all_registered(), "write_file") is not None:
        return find_tool_by_name(all_registered(), "write_file")
    return register(build_tool(
        name="write_file",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_write_file_executor,
        is_read_only=False,
        is_destructive=True,            # Overwrites existing files
        is_concurrency_safe=False,      # Two writes to same path race
        requires_approval=True,         # ADR-010: approval prompt with diff
        search_hint="write file create or overwrite",
    ))
