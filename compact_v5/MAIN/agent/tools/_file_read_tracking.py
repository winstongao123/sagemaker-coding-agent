"""Phase 4 file-read tracking stub.

Tracks which files the agent has read in the current session. Used by:
  - `write_file` to enforce "read before overwrite" (v4 parity)
  - `edit_file` to enforce "read before edit" (v4 parity)

This is a session-level singleton, NOT a per-process cache. Phase 8's
`core/query_engine.py` will populate it organically every time the
agent invokes the `read_file` tool. Phase 4 ships it standalone so:
  (a) write_file / edit_file can enforce the contract NOW
  (b) tests can pre-mark files as "read" before exercising mutators

Phase 8 retires this module: the read-tracking responsibility moves
into the QueryEngine session state. The 4 tool modules will switch
from `tools._file_read_tracking.{mark_read, was_read}` to
`core.session.files_read` (or equivalent) — one-line import change.

Replaces v4 `_FILES_READ` set and `_FILE_READ_TIMES` dict at
`compact_v4/MAIN/agent/sagemaker_agent.py` (around line 4200).
"""
from __future__ import annotations

import os
import threading
from typing import Dict, Set, Tuple

# Process-global state, threadsafe. Single-threaded ipynb is the primary
# target but the lock is cheap insurance.
_LOCK = threading.Lock()
_FILES_READ: Set[str] = set()
_FILE_READ_TIMES: Dict[str, float] = {}


def mark_read(abs_path: str) -> None:
    """Record that the agent has read this file in the current session."""
    if not abs_path:
        return
    with _LOCK:
        _FILES_READ.add(abs_path)
        try:
            _FILE_READ_TIMES[abs_path] = os.path.getmtime(abs_path)
        except OSError:
            pass


def was_read(abs_path: str) -> bool:
    """Return True if `mark_read(abs_path)` was called this session."""
    with _LOCK:
        return abs_path in _FILES_READ


def get_read_mtime(abs_path: str) -> float | None:
    """Return the file's mtime captured at read time, or None if not tracked."""
    with _LOCK:
        return _FILE_READ_TIMES.get(abs_path)


def is_stale(abs_path: str) -> Tuple[bool, str]:
    """v4 parity: warn if the file was modified externally since the agent read it.

    Returns (is_stale, message). Caller should reject the edit if is_stale=True.
    """
    last = get_read_mtime(abs_path)
    if last is None:
        return False, ""
    try:
        current = os.path.getmtime(abs_path)
    except OSError:
        return False, ""
    # v4 parity (sagemaker_agent.py:4189): "modified externally" means a
    # FORWARD jump in mtime. A backward jump (e.g., `git checkout` to an
    # older commit) keeps the file's content in a state the agent already
    # saw, so v4 doesn't flag it. v5 matches this directional check.
    # Codex Phase-04 review finding 4 (nit) fix (was: bidirectional `abs(...)`).
    if current - last > 0.5:
        return True, (
            f"File modified externally since last read "
            f"(read mtime {last:.0f} vs now {current:.0f}). "
            f"Re-read with read_file to refresh, then retry the edit."
        )
    return False, ""


def reset_for_tests() -> None:
    """Clear all tracked state. Tests only — do not call in production."""
    with _LOCK:
        _FILES_READ.clear()
        _FILE_READ_TIMES.clear()
