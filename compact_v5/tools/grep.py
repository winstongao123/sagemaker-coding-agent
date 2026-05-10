"""Phase 3 grep tool — REUSE v4 executor + ADAPT Runnable prompt text.

Per ADR-009:
- Executor body is a Phase-3 port of v4's `tool_grep` at
  `compact_v4/MAIN/agent/sagemaker_agent.py:4897`. Pure Python `re`
  module — no ripgrep binary dependency (v4 made the same choice for
  Bedrock-only / no-bun-runtime constraint).
- Description text is adapted from
  `gg-claude-code-runnable/src/tools/GrepTool/prompt.ts`. **Critical
  truthfulness correction**: Runnable's prompt says "built on ripgrep",
  but v5 (and v4) use Python `re`. The v5 prompt says "regex search"
  to avoid the false claim — PS Issue #6 (wiring-bug pattern)
  prevention. This is a documented intentional fidelity-improvement
  away from Runnable's text.

PORT_LOG: row #004 (Runnable GrepTool/prompt.ts → tools/grep.py).
"""
from __future__ import annotations

import glob as glob_module
import os
import re
from typing import Any, Dict, Optional

from .registry import build_tool, register
from . import _path_validation as path_security


# ============================================================
# Description (adapted from Runnable's getDescription)
# ============================================================
# Differences from Runnable text:
# - "built on ripgrep" → "regex search across files" (truthful: v5 uses Python re).
# - Tool naming: Runnable `Grep` → v5 `grep` (v4 parity).
# - Removed `multiline` parameter reference (v5 doesn't expose it; Python re's
#   `re.DOTALL` is per-call rather than global; can be added in a future phase
#   if the model needs cross-line matches).
_DESCRIPTION = """Regex search across files. Use this for any code/text search across the workspace.

Usage:
- ALWAYS use grep for search tasks. NEVER invoke `grep` or `rg` via bash — this dedicated tool has correct permissions and the right defaults.
- Supports full Python regex syntax (e.g., "log.*Error", "function\\s+\\w+")
- Filter files by glob pattern with the `glob` parameter (e.g., "**/*.py", "**/*.tsx")
- Output is one match per line: `<file>:<line>: <text>` (text trimmed to 300 chars)
- Use the task tool for open-ended searches that need multiple rounds of grep+glob.
- Pattern syntax: Python `re` semantics — literal braces don't need escaping; backreferences and named groups are supported.
- Binary files are skipped automatically (null-byte detection in first 8KB).
- Results capped at 100 matches; narrow your pattern or path if you need more.

WHEN to use:
- Searching code or text for a regex pattern across a workspace
- Finding all references / call sites / definitions of a symbol
- Anywhere you would otherwise reach for `grep` or `rg` in bash

WHEN NOT to use:
- Finding files by NAME → use glob (grep searches contents, glob searches paths)
- Reading a known file → use read_file
- Listing a directory → use list_dir"""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "pattern": {
            "type": "string",
            "description": "Python regex pattern to search for in file contents.",
        },
        "path": {
            "type": "string",
            "description": "Directory to search in (absolute path). Defaults to workspace root.",
        },
        "glob": {
            "type": "string",
            "description": "Glob pattern to filter which files are searched (e.g., '**/*.py'). Default: '**/*'.",
        },
        "case_insensitive": {
            "type": "boolean",
            "description": "If true, match case-insensitively (re.IGNORECASE). Default false.",
        },
    },
    "required": ["pattern"],
}


def _grep_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    """Phase-3 executor — minimal port of v4 `tool_grep`."""
    pattern = args.get("pattern")
    if not isinstance(pattern, str) or not pattern:
        return "Error: pattern is required and must be a non-empty string"

    glob_pattern = args.get("glob") or "**/*"
    case_insensitive = bool(args.get("case_insensitive") or False)
    raw_path = args.get("path")

    from runtime.config import CONFIG
    if raw_path:
        search_root = raw_path if os.path.isabs(raw_path) else os.path.join(CONFIG.workspace, raw_path)
    else:
        search_root = CONFIG.workspace

    ok, msg = path_security.validate_path(search_root)
    if not ok:
        return f"Error: {msg}"

    flags = re.IGNORECASE if case_insensitive else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"Error: invalid regex: {e}"

    full_glob = os.path.join(search_root, glob_pattern)
    files = glob_module.glob(full_glob, recursive=True)

    results = []
    for filepath in files:
        if len(results) >= 100:
            break
        if not os.path.isfile(filepath):
            continue
        # Per-file boundary check (symlink escape protection — v4 parity)
        file_ok, _ = path_security.validate_path(filepath)
        if not file_ok:
            continue
        # Binary skip: null byte in first 8KB
        try:
            with open(filepath, "rb") as bf:
                if b"\x00" in bf.read(8192):
                    continue
        except OSError:
            continue
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    if regex.search(line):
                        snippet = line.strip()[:300]
                        results.append(f"{filepath}:{i}: {snippet}")
                        if len(results) >= 100:
                            break
        except (OSError, UnicodeError):
            continue

    if not results:
        return f"No matches for /{pattern}/ in {search_root} (filter: {glob_pattern})"

    output = "\n".join(results)
    if len(results) >= 100:
        output += "\n\n[WARNING: Results capped at 100 matches. Narrow your pattern or path for complete results.]"
    return output


# ============================================================
# Idempotent registration (Codex Phase-03 review finding 1)
# ============================================================

def _register():
    """Idempotent registration of the `grep` tool. See read_file.py:_register
    for the full rationale (test reset / module reload safety)."""
    from .registry import find_tool_by_name, all_registered
    existing = find_tool_by_name(all_registered(), "grep")
    if existing is not None:
        return existing
    return register(build_tool(
        name="grep",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_grep_executor,
        is_read_only=True,
        is_concurrency_safe=True,
        requires_approval=False,
        search_hint="regex search file contents",
    ))
