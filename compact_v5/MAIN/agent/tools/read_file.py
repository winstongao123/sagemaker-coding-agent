"""Phase 3 read_file tool — REUSE v4 executor + ADAPT Runnable prompt text.

Per ADR-009:
- Executor body is a Phase-3 port of v4's `tool_read_file` at
  `compact_v4/MAIN/agent/sagemaker_agent.py:4258`. v5 simplifies the v4
  body by dropping FILE_CACHE / FILE_UNCHANGED_STUB / mtime-tracking
  (those Phase 8 globals will be re-introduced when query_engine.py
  lands; this Phase 3 minimal port keeps the security check, the
  large-file guard, and the .ipynb cell parsing — the parts that affect
  the model's view of the file).
- Description text is adapted from
  `gg-claude-code-runnable/src/tools/FileReadTool/prompt.ts` —
  Runnable's prompt is more directive on WHEN/WHEN NOT, addresses
  PS Issue #7 (buried-matrix failure mode).

PORT_LOG: row #003 (Runnable FileReadTool/prompt.ts → tools/read_file.py).
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from .registry import build_tool, register
from . import _path_validation as path_security
from runtime.tool_surface import (
    FileTooLargeError,
    read_file_in_range,
    semantic_number,
)
from runtime.file_safety import is_binary_content


# ============================================================
# Description (adapted from Runnable's renderPromptTemplate)
# ============================================================
# Note: Runnable's prompt names the tool `Read`. v5 exposes it as
# `read_file` (v4 parity — prevents the model from confusing it with
# generic English "read"). The description text is adapted accordingly.
_DESCRIPTION = """Reads a file from the local filesystem. You can access any file directly by using this tool.
Assume this tool is able to read all files on the machine. If the User provides a path to a file assume that path is valid. It is okay to read a file that does not exist; an error will be returned.

Usage:
- The file_path parameter must be an absolute path, not a relative path
- By default reads up to 2000 lines from the beginning of the file
- For files >500 lines without offset/limit, only the first 50 + last 30 lines are shown — use grep to find the section you need, then read_file with offset and limit
- When you already know which part of the file you need, only read that part. This can be important for larger files.
- Results are returned with line numbers (1-indexed)
- Can read .ipynb notebooks — returns all cells with their cell-type headers
- Can only read files, not directories. Use list_dir for directories.
- You MUST read a file before editing it with edit_file. The edit_file call will fail otherwise.
- If you read a file that exists but has empty contents you will receive a system reminder warning in place of file contents.

WHEN to use:
- Reading a specific file or section you already know the path to
- Viewing file contents before making edits
- Checking the current state of a file after changes

WHEN NOT to use:
- Searching for patterns across files → use grep FIRST to find locations, then read_file with offset/limit
- Finding files by name or extension → use glob
- Reading directory listings → use list_dir"""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Absolute path to the file to read.",
        },
        "offset": {
            "type": "integer",
            "description": "Start line, 0-indexed. Default 0 (beginning of file).",
        },
        "limit": {
            "type": "integer",
            "description": "Max number of lines to read. Default 2000.",
        },
    },
    "required": ["file_path"],
}


_MAX_FILE_SIZE_DEFAULT = 10 * 1024 * 1024  # 10 MB; matches v4 CONFIG.max_file_size


def _read_file_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    """Phase-3 executor — minimal Python port of v4 `tool_read_file`.

    Returns the file contents (with line numbers, 1-indexed) as a single
    string. On error, returns `"Error: <reason>"` matching v4 contract.
    """
    file_path = args.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return "Error: file_path is required and must be a non-empty string"

    # Codex Phase-03 review finding 2: model-supplied non-integer offset/limit
    # used to crash the tool with ValueError/TypeError. Now returns an Error:
    # string the model can read and recover from.
    raw_offset = args.get("offset", 0) if args.get("offset") is not None else 0
    raw_limit = args.get("limit", 2000) if args.get("limit") is not None else 2000
    try:
        offset = int(semantic_number(raw_offset, integer=True))
    except (TypeError, ValueError):
        return f"Error: offset must be a non-negative integer; got {raw_offset!r}"
    try:
        limit = int(semantic_number(raw_limit, integer=True))
    except (TypeError, ValueError):
        return f"Error: limit must be a positive integer; got {raw_limit!r}"
    if offset < 0:
        return f"Error: offset must be >=0; got {offset}"
    if limit < 1:
        return f"Error: limit must be >=1; got {limit}"

    ok, msg = path_security.validate_path(file_path)
    if not ok:
        return f"Error: {msg}"

    abs_path = path_security.resolve_path(file_path)
    if not os.path.exists(abs_path):
        return f"Error: File not found: {file_path} (resolved to {abs_path})"
    if not os.path.isfile(abs_path):
        return f"Error: Not a file: {abs_path} (use list_dir for directories)"
    try:
        with open(abs_path, "rb") as probe:
            sample = probe.read(8192)
        if is_binary_content(sample, filename=abs_path):
            return f"Error: Refusing to read binary file: {abs_path}"
    except OSError as e:
        return f"Error: cannot read file: {e}"

    # Lazy import CONFIG so test envs without a config still load.
    from runtime.config import CONFIG
    max_file_size = getattr(CONFIG, "max_file_size", _MAX_FILE_SIZE_DEFAULT)
    try:
        range_read = read_file_in_range(
            abs_path,
            offset=0,
            limit=None,
            max_bytes=max_file_size,
        )
        content = range_read.text
        file_size = range_read.file_size
    except FileTooLargeError as e:
        return (
            f"Error: File too large ({e.size:,} bytes, max {e.max_bytes:,}). "
            f"Use grep to search inside it, or read_file with offset/limit."
        )
    except OSError as e:
        return f"Error: cannot read file: {e}"

    # .ipynb cell parsing (v4 parity — read_file flattens notebook cells)
    if abs_path.endswith(".ipynb"):
        try:
            nb = json.loads(content)
            cells = nb.get("cells") or []
            parts = []
            for idx, cell in enumerate(cells):
                if not isinstance(cell, dict):
                    continue
                cell_type = cell.get("cell_type", "code")
                source = "".join(cell.get("source") or [])
                parts.append(f"# === Cell {idx + 1} ({cell_type}) ===")
                parts.append(source)
                parts.append("")
            content = "\n".join(parts)
        except (ValueError, KeyError, TypeError):
            # Not valid notebook JSON — fall through to raw text view.
            pass

    if not content:
        return f"[{os.path.basename(abs_path)}] (empty file — no content to display)"

    lines = content.split("\n")
    total_lines = len(lines)

    # v4 large-file guard: >500 lines + no explicit offset/limit → first 50 + last 30
    if total_lines > 500 and offset == 0 and limit >= 2000:
        head = lines[:50]
        tail = lines[-30:]
        head_text = "\n".join(f"{i + 1:4}| {ln[:2000]}" for i, ln in enumerate(head))
        tail_text = "\n".join(
            f"{total_lines - 30 + i + 1:4}| {ln[:2000]}" for i, ln in enumerate(tail)
        )
        return (
            f"[{os.path.basename(abs_path)}] {total_lines} lines total — LARGE FILE, "
            f"showing first 50 + last 30 lines.\n"
            f"Use grep to find specific code, then read_file with offset/limit for the exact section.\n\n"
            f"--- First 50 lines ---\n{head_text}\n\n"
            f"--- Last 30 lines ---\n{tail_text}\n\n"
            f"[{total_lines - 80} lines omitted. Use: read_file with offset=N limit=M, or grep to search.]"
        )

    selected = lines[offset:offset + limit]
    rendered = []
    for i, ln in enumerate(selected, start=offset + 1):
        if len(ln) > 2000:
            ln = ln[:2000] + "..."
        rendered.append(f"{i:4}| {ln}")
    body = "\n".join(rendered)

    header = f"[{os.path.basename(abs_path)}] Lines {offset + 1}-{offset + len(selected)} of {total_lines}"
    if offset + limit < total_lines:
        header += f" [use offset={offset + limit} for more]"

    return f"{header}\n{body}"


# ============================================================
# Idempotent registration (per ADR-001 file-per-tool layout)
# Codex Phase-03 review finding 1: import-time registration was not safe
# across `_reset_registry_for_tests()` + reimport, since per-tool modules
# stay cached in sys.modules and won't re-execute their top-level
# `register(...)` call. The fix: expose a `_register()` function that
# `tools/__init__.py:bootstrap_built_ins()` calls. Idempotent: skips if
# the tool is already registered (so re-bootstrap after a test reset is
# safe and doesn't trip the registry's loud-fail-on-duplicate guard).
# ============================================================

def _register():
    """Idempotent registration of the `read_file` tool.

    Returns the tool record. If the tool is already in the registry,
    returns the existing record (no-op for the registry). This allows
    test fixtures to call `_reset_registry_for_tests()` followed by
    `bootstrap_built_ins()` to restore the default state.
    """
    from .registry import find_tool_by_name, all_registered
    existing = find_tool_by_name(all_registered(), "read_file")
    if existing is not None:
        return existing
    return register(build_tool(
        name="read_file",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_read_file_executor,
        is_read_only=True,
        is_concurrency_safe=True,    # Runnable parity: read ops are safe in parallel
        requires_approval=False,
        search_hint="read file contents with line numbers",  # for Phase-7 ToolSearch
    ))
