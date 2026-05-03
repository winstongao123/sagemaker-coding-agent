"""Block C item 0-5 (ADR-020 remap from Block 0) — per-session scratchpad dir.

Per-session scratch directory under `/tmp/sagemaker_session_<id>/` (or
the platform tempdir on Windows). The directory is pre-allowlisted so
file_safety / path validators accept reads + writes inside it without
triggering "outside workspace" denials. Cleanup runs via
`runtime/cleanup_registry.py` on normal exit / SIGINT / SIGTERM.

Per Runnable constants/prompts.ts:797-819 (R8 #77).

PORT_LOG: see #059.
"""
from __future__ import annotations

import logging
import os
import shutil
import tempfile
import uuid
from typing import Optional


_session_dir: Optional[str] = None


def get_scratchpad_dir() -> str:
    """Return the per-process scratchpad directory; create on first call.

    The directory lives under the platform tempdir with a session-unique
    suffix so concurrent agent processes don't share state.
    """
    global _session_dir
    if _session_dir is not None and os.path.isdir(_session_dir):
        return _session_dir
    base = tempfile.gettempdir()
    sid = uuid.uuid4().hex[:12]
    path = os.path.join(base, f"sagemaker_session_{sid}")
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        logging.warning(f"scratchpad: cannot create {path}: {e}")
        # Fall back to platform tempdir — better than crashing.
        _session_dir = base
        return _session_dir
    _session_dir = path
    # Register GC at process exit. Best-effort: cleanup_registry is
    # imported lazily so import-time failure doesn't break the
    # scratchpad surface.
    try:
        from runtime.cleanup_registry import register
        register(_gc_scratchpad)
    except Exception:
        pass
    return _session_dir


def _gc_scratchpad() -> None:
    """Best-effort delete of the scratchpad dir at process exit."""
    global _session_dir
    if _session_dir and os.path.isdir(_session_dir):
        try:
            shutil.rmtree(_session_dir, ignore_errors=True)
        except Exception as e:  # noqa: BLE001 — best-effort
            logging.warning(f"scratchpad: cleanup failed: {e}")
    _session_dir = None


def is_in_scratchpad(path: str) -> bool:
    """True iff `path` resolves to a location inside the scratchpad dir.

    Used by path-validators to short-circuit the "outside workspace"
    check — scratchpad reads/writes are pre-allowlisted.
    """
    if _session_dir is None:
        return False
    try:
        abs_path = os.path.realpath(path)
        scratch_root = os.path.realpath(_session_dir)
    except OSError:
        return False
    return abs_path.startswith(scratch_root + os.sep) or abs_path == scratch_root


def get_scratchpad_instructions() -> str:
    """Render the prompt-side instructions for using the scratchpad.

    Splice into the env-block / system prompt so the model knows it can
    write throwaway files without triggering allowlist denials.
    """
    sd = get_scratchpad_dir()
    return (
        "## Scratchpad\n\n"
        f"You can write throwaway files (logs, intermediate data, build artifacts) "
        f"to `{sd}`. This directory is pre-allowlisted; reads + writes there will "
        f"NOT be challenged by the path validator. The directory is GC'd at session "
        f"end so contents are non-persistent.\n"
    )


def _reset_for_tests() -> None:
    """Test helper — drop module state so a re-init creates a fresh dir."""
    global _session_dir
    if _session_dir and os.path.isdir(_session_dir):
        shutil.rmtree(_session_dir, ignore_errors=True)
    _session_dir = None


__all__ = [
    "get_scratchpad_dir",
    "get_scratchpad_instructions",
    "is_in_scratchpad",
]
