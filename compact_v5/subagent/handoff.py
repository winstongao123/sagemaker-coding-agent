"""V5 subagent/handoff.py — bounded sub-agent handoff block (Phase 9, ADR-015).

ADAPT port of v4's `_build_subagent_handoff_block` at
`compact_v4/MAIN/agent/sagemaker_agent.py:7771`. Adaptation:
- Pulls inputs as parameters instead of reading from globals
  (`_status_doc_path()`, `build_todo_restoration_message()`, `_RECENT_DIFFS`).
  This decouples the handoff builder from Phase 11 UX wiring; Phase 11
  callers will pass the actual paths/text/files.
- Each section is independently optional; missing inputs yield no section.
- Output is bounded so a verbose AGENT_STATUS or todos list cannot bloat
  the sub-agent's prompt past the cache-boundary tail budget.
- Sanitizes any in-content cache-boundary markers (defense against a
  user-supplied AGENT_STATUS containing `# === DYNAMIC ===` literally).

PORT_LOG: #023.

Output goes AFTER the cached SYSTEM_PROMPT boundary, so the static prefix's
prompt cache is preserved unchanged. Caller (Phase 9 spawn.py) is
responsible for placing this block after the boundary marker.
"""
from __future__ import annotations

import os
from typing import Iterable, Optional


# Same caps as v4 (sagemaker_agent.py:7750). CHAR-based, not byte-based —
# tokenizers see code points, not bytes.
_STATUS_MAX_CHARS: int = 4_000   # ~1000 tokens of AGENT_STATUS slice
_TODOS_MAX_CHARS: int = 2_000    # cap for todos block
_DIFF_MAX_FILES: int = 10        # last N changed files

_BOUNDARY_MARKER: str = "# === DYNAMIC ==="
_BOUNDARY_SANITIZED: str = "# === DYNAMIC === (sanitized)"


def _sanitize(text: str) -> str:
    """Replace any in-content occurrence of the cache-boundary marker so it
    cannot confuse a future split implementation that uses split(marker)."""
    if not text:
        return text
    return text.replace(_BOUNDARY_MARKER, _BOUNDARY_SANITIZED)


def build_handoff_block(
    status_path: Optional[str] = None,
    todos_text: Optional[str] = None,
    recent_files: Optional[Iterable[str]] = None,
) -> str:
    """Build a bounded handoff block for a fresh sub-agent.

    Args:
        status_path: filesystem path to AGENT_STATUS.md. If absent or empty,
            no status slice is added.
        todos_text: pre-rendered todo list (e.g. from
            `build_todo_restoration_message()`). If empty, no todos section.
        recent_files: iterable of file paths edited in the parent session.
            Deduplicated and capped at last `_DIFF_MAX_FILES`. No diff bodies.

    Returns "" if no section produced any content. Never raises.
    """
    parts = []

    # AGENT_STATUS slice — bounded read so we don't load 25KB into every sub-agent.
    if status_path:
        try:
            if os.path.exists(status_path):
                with open(status_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(_STATUS_MAX_CHARS + 1)
                if content.strip():
                    truncated = len(content) > _STATUS_MAX_CHARS
                    if truncated:
                        content = content[:_STATUS_MAX_CHARS]
                    content = _sanitize(content)
                    marker = " (truncated)" if truncated else ""
                    parts.append(f"## AGENT_STATUS.md slice{marker}\n{content}")
        except Exception:
            pass

    # Active todos
    if todos_text:
        try:
            t = todos_text
            if len(t) > _TODOS_MAX_CHARS:
                t = t[:_TODOS_MAX_CHARS] + "\n... (todos truncated)"
            t = _sanitize(t)
            parts.append(f"## Active TODOs (parent session)\n{t}")
        except Exception:
            pass

    # Recent changed files (paths only, no diff bodies)
    if recent_files:
        try:
            seen = []
            file_lines = []
            for entry in list(recent_files)[-_DIFF_MAX_FILES:]:
                p = str(entry).strip()
                if p and p not in seen:
                    seen.append(p)
                    file_lines.append(f"- {p}")
            if file_lines:
                parts.append(
                    f"## Files edited in parent session "
                    f"(last {len(file_lines)}, no diff bodies)\n"
                    + "\n".join(file_lines)
                )
        except Exception:
            pass

    if not parts:
        return ""
    return "# Sub-agent Handoff (parent context, bounded)\n" + "\n\n".join(parts)
