"""Block B+ — cleanup registry (Block 0 item 0-7 remap per ADR-020).

Adapter of Runnable's `cleanupRegistry` (utils/cleanupRegistry.ts:1-26 /
R8 #18). Provides a single registry of best-effort shutdown callables
that fire on:
  - Normal interpreter exit (atexit)
  - SIGINT (Ctrl+C in a shell-driven context)
  - SIGTERM where the OS supports it

Uses: TokenTracker cost-flush at exit (B+7); SnapshotManager log flush
(future); SessionManager final-save; scratchpad gc (Block C 0-5 remap).

PORT_LOG: see #050.
"""
from __future__ import annotations

import atexit
import logging
import signal
import threading
from typing import Callable, List


# Codex Block-B+ finding #3 (MEDIUM) lock: use RLock so a SIGINT
# arriving while register()/_run_all() holds the lock can re-enter
# without deadlocking. The signal handler calls _run_all() which
# acquires the same lock — non-reentrant Lock would deadlock.
_lock = threading.RLock()
_callbacks: List[Callable[[], None]] = []
_installed = False


def register(callback: Callable[[], None]) -> None:
    """Register a no-arg callable to fire on shutdown.

    The callable runs once per process; if it raises, the error is
    logged at WARNING and other callbacks still run.
    """
    with _lock:
        _callbacks.append(callback)
        _ensure_installed_locked()


def unregister(callback: Callable[[], None]) -> None:
    """Remove a previously registered callback (idempotent)."""
    with _lock:
        try:
            _callbacks.remove(callback)
        except ValueError:
            pass


def _run_all() -> None:
    """Fire all registered callbacks. Errors are logged, not re-raised."""
    with _lock:
        cbs = list(_callbacks)
        _callbacks.clear()
    for cb in cbs:
        try:
            cb()
        except Exception as exc:  # noqa: BLE001 — best-effort
            logging.warning(
                f"cleanup_registry: callback {cb!r} raised "
                f"{type(exc).__name__}: {exc}"
            )


def _signal_handler(_signum, _frame):
    _run_all()
    # Re-raise SIGINT semantics so the host (Jupyter / shell) sees the
    # interrupt and can take its normal path.
    raise KeyboardInterrupt


def _ensure_installed_locked() -> None:
    """Install atexit + signal handlers exactly once. Caller holds _lock."""
    global _installed
    if _installed:
        return
    atexit.register(_run_all)
    # Some hosts (Jupyter notebook kernels) override signal handlers;
    # tolerate the install failing — atexit still gives us best-effort.
    try:
        signal.signal(signal.SIGINT, _signal_handler)
    except (ValueError, OSError):
        pass
    try:
        signal.signal(signal.SIGTERM, _signal_handler)
    except (ValueError, OSError, AttributeError):
        pass
    _installed = True


def _reset_for_tests() -> None:
    """Test helper — drop registered callbacks without un-installing handlers."""
    with _lock:
        _callbacks.clear()


__all__ = ["register", "unregister"]
