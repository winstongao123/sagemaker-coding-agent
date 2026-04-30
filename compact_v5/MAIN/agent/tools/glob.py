"""Phase 3 glob tool — REUSE v4 executor + ADAPT Runnable prompt text.

Per ADR-009:
- Executor body is a Phase-3 port of v4's `tool_glob` at
  `compact_v4/MAIN/agent/sagemaker_agent.py:4846`. Includes v4's
  `allowed_paths` fallback (when no explicit path arg AND no matches
  in workspace, also search the allowed_paths roots).
- Description text is adapted from
  `gg-claude-code-runnable/src/tools/GlobTool/prompt.ts`.

PORT_LOG: row #005 (Runnable GlobTool/prompt.ts → tools/glob.py).
"""
from __future__ import annotations

import glob as glob_module
import os
from typing import Any, Dict, Optional

from .registry import build_tool, register
from . import _path_validation as path_security


# ============================================================
# Description (adapted from Runnable's DESCRIPTION constant)
# ============================================================
_DESCRIPTION = """Fast file pattern matching tool that finds files by name or path pattern.

Usage:
- Supports standard glob patterns: `**/*.py`, `src/**/*.ts`, `*.json`, `test_*.py`
- `**` matches any number of directories (recursive)
- `*` matches any characters within a single path segment
- Returns matching file paths sorted by modification time (newest first)
- Use the optional `path` parameter to limit the search to a specific directory (defaults to workspace root)
- If no `path` is given AND nothing matches in the workspace, the tool will also search any directories in `CONFIG.allowed_paths` (e.g., a parent git repo) — useful when the workspace was opened inside a sub-directory.
- Results capped at 100; if more than 100 candidate paths exist, narrow the pattern.

WHEN to use:
- Finding files by name or extension (e.g., all Python files: `**/*.py`)
- Locating a specific file when you know part of its name
- Discovering project structure

WHEN NOT to use:
- Searching FILE CONTENTS for patterns → use grep (glob only matches file names/paths)
- Open-ended exploration requiring multiple rounds → use the task tool with explore type"""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "pattern": {
            "type": "string",
            "description": "Glob pattern (e.g., '**/*.py').",
        },
        "path": {
            "type": "string",
            "description": "Directory to search in (absolute path). Defaults to workspace root.",
        },
    },
    "required": ["pattern"],
}


def _glob_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    """Phase-3 executor — minimal port of v4 `tool_glob`."""
    pattern = args.get("pattern")
    if not isinstance(pattern, str) or not pattern:
        return "Error: pattern is required and must be a non-empty string"

    explicit_path = "path" in args and args.get("path") not in (None, "")
    raw_path = args.get("path")

    from runtime.config import CONFIG
    if raw_path:
        search_root = raw_path if os.path.isabs(raw_path) else os.path.join(CONFIG.workspace, raw_path)
    else:
        search_root = CONFIG.workspace

    ok, msg = path_security.validate_path(search_root)
    if not ok:
        return f"Error: {msg}. Workspace root: {CONFIG.workspace}"

    full_pattern = os.path.join(search_root, pattern)
    all_raw = glob_module.glob(full_pattern, recursive=True)
    searched_roots = [search_root]

    # v4 parity: when no match in workspace AND no explicit path arg, also
    # search allowed_paths (e.g., the git repo root auto-detected above the
    # workspace). Lets the model find files in adjacent project dirs.
    if not all_raw and not explicit_path:
        for ap in (CONFIG.allowed_paths or []):
            ap_str = str(ap)
            if ap_str == search_root or ap_str in searched_roots:
                continue
            extra = glob_module.glob(os.path.join(ap_str, pattern), recursive=True)
            if extra:
                all_raw.extend(extra)
                searched_roots.append(ap_str)

    total_raw = len(all_raw)
    raw_matches = all_raw[:200]
    # Per-file boundary check (symlink escape protection)
    valid = [m for m in raw_matches if path_security.validate_path(m)[0]]
    total_valid = len(valid)
    matches = valid[:100]
    matches = sorted(
        matches,
        key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0,
        reverse=True,
    )
    if not matches:
        roots_str = ", ".join(r.replace("\\", "/") for r in searched_roots)
        return (
            f"No files found. Searched: {roots_str}. "
            f"Try a broader pattern (e.g. **/{os.path.basename(pattern) or pattern}) "
            f"or use list_dir to inspect the directory tree."
        )

    output = "\n".join(matches)
    if len(searched_roots) > 1:
        output += (
            f"\n\n[Searched {len(searched_roots)} roots (workspace + allowed_paths): "
            f"{', '.join(r.replace(chr(92), '/') for r in searched_roots)}]"
        )
    if total_raw > 200 or total_valid > 100:
        output += (
            f"\n\n[WARNING: Showing {len(matches)} of {total_raw} total matches. "
            f"Narrow your pattern for complete results.]"
        )
    return output


# ============================================================
# Idempotent registration (Codex Phase-03 review finding 1)
# ============================================================

def _register():
    """Idempotent registration of the `glob` tool. See read_file.py:_register."""
    from .registry import find_tool_by_name, all_registered
    existing = find_tool_by_name(all_registered(), "glob")
    if existing is not None:
        return existing
    return register(build_tool(
        name="glob",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_glob_executor,
        is_read_only=True,
        is_concurrency_safe=True,
        requires_approval=False,
        search_hint="find files by glob pattern",
    ))
