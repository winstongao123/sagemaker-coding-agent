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

    # Block C C-6 (R1 #123) — UNC path skip on Windows (NTLM credential leak).
    try:
        from security.edit_file_safety import is_unc_path_windows
        if is_unc_path_windows(file_path):
            return (
                "Error: UNC paths (\\\\server\\share\\...) are not allowed on "
                "Windows because reading them leaks NTLM credentials. Copy "
                "the file locally first (e.g. via robocopy) and edit the copy."
            )
    except Exception:
        pass

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
        # Block C C-8 (R1 #111) — Windows OneDrive / AV touch can bump
        # mtime without changing content. If the read tracker has a
        # cached snapshot AND the file content is byte-identical to
        # that snapshot, treat the staleness as a false positive.
        try:
            from security.edit_file_safety import is_staleness_false_positive
            cached = read_tracking.get_last_read_snapshot(abs_path) \
                if hasattr(read_tracking, "get_last_read_snapshot") else None
            if cached is not None:
                last_mtime = cached.get("mtime", 0.0)
                last_text = cached.get("content")
                if is_staleness_false_positive(abs_path, last_mtime, last_text):
                    is_stale = False  # tolerate the touch
        except Exception:
            pass
        if is_stale:
            return f"Error: {stale_msg}"

    # Block C C-5 (R1 #121) — detect UTF-16 / UTF-8-sig BOMs (Notepad-saved).
    _file_encoding = "utf-8"
    _eol = "\n"
    try:
        from security.edit_file_safety import (
            detect_utf16_bom,
            normalize_line_endings,
            normalize_quotes,
        )
        _bom_enc = detect_utf16_bom(abs_path)
        if _bom_enc:
            _file_encoding = _bom_enc
    except Exception:
        pass

    try:
        with open(abs_path, "r", encoding=_file_encoding, errors="replace") as f:
            content = f.read()
    except OSError as e:
        return f"Error: cannot read file: {e}"

    # Block C C-7 (R1 #122) — round-trip line endings: match in LF space,
    # restore on write. Block C C-3 (R1 #115) — fold curly→straight quotes
    # on BOTH file and search needle so smart-quote files match.
    _content_lf = content
    try:
        _content_lf, _eol = normalize_line_endings(content)
        _norm_content = normalize_quotes(_content_lf)
        _norm_old = normalize_quotes(old_string)
    except NameError:
        _norm_content = _content_lf
        _norm_old = old_string

    count = _norm_content.count(_norm_old)
    if count == 0:
        return "Error: old_string not found in file. Must be EXACT match (check indentation, line endings, exact characters)."
    if count > 1 and not replace_all:
        return (
            f"Error: old_string appears {count} times in the file. "
            f"Either provide a larger old_string with more context to make it unique, "
            f"or pass replace_all=true to change every occurrence."
        )

    # Apply replacement on the normalized (LF + straight-quote) content
    # so the match works for smart-quote / CRLF files; then restore the
    # original line endings before writing.
    # Block C C-4 (R1 #116) lock: if the original content uses curly
    # quotes (we detect by comparing the un-normalized vs normalized
    # version), re-wrap new_string in the same curly variant so the
    # file remains stylistically consistent post-edit.
    if "_norm_old" in locals():
        _norm_new = normalize_quotes(new_string)
        try:
            from security.edit_file_safety import preserve_quote_style
            _norm_new = preserve_quote_style(content, _norm_new)
        except Exception:
            pass
    else:
        _norm_new = new_string
    new_content = (
        _norm_content.replace(_norm_old, _norm_new)
        if replace_all
        else _norm_content.replace(_norm_old, _norm_new, 1)
    )
    if _eol != "\n":
        try:
            from security.edit_file_safety import restore_line_endings
            new_content = restore_line_endings(new_content, _eol)
        except Exception:
            pass

    # Block B (PORT_LOG #044): SnapshotManager.save snapshots the
    # current file before edit so /revert restores it. Best-effort —
    # snapshot failure must not block the edit.
    try:
        from runtime.snapshot import SNAPSHOTS
        SNAPSHOTS.save(abs_path)
    except Exception:
        pass

    # Write back in the same encoding we read with (preserves BOM).
    try:
        with open(abs_path, "w", encoding=_file_encoding) as f:
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

    # Block I-1 / I-5 — path-triggered skill auto-activation. When the
    # context provides a SkillManager, ask it which (if any) skills declare
    # this path in their `paths:` frontmatter and auto-activate them.
    # Best-effort: never block a successful edit on this hook.
    activated_note = ""
    try:
        sm = (context or {}).get("skill_manager") if isinstance(context, dict) else None
        if sm is not None and hasattr(sm, "activate_for_path"):
            activated = sm.activate_for_path(abs_path)
            if activated:
                activated_note = (
                    f"\n  [auto-activated skill: {', '.join(activated)} "
                    f"via paths frontmatter]"
                )
    except Exception:
        pass

    return (
        f"Edited {os.path.basename(abs_path)} (line {line_no})\n"
        f"  -{old_lines} lines / +{new_lines} lines{suffix}"
        f"{activated_note}"
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
