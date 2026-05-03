"""Block B+ — FileCache + thread-local context for sub-agents.

Verbatim port of v4's `FileCache` (compact_v4/MAIN/agent/sagemaker_agent.py
lines 893-1017). The FileCache provides:
  - Thread-safe LRU cache for file reads (mtime-validated)
  - Per-thread `in_context` set so parallel sub-agents don't see each
    other's "already loaded" markers
  - save_and_clear_context / restore_context for sub-agent dispatch
    enter/exit boundaries (Plan v3 §Block B+ FileCache class)

The thread-local pattern: when a sub-agent thread enters dispatch, it
calls `enter_thread_local_context()` to get an empty isolated set; when
it exits, `exit_thread_local_context()` reverts to the main set so the
parent's context is preserved.

PORT_LOG: see #049.
"""
from __future__ import annotations

import os
import threading
from typing import Dict, Optional, Set, Tuple


class FileCache:
    """Thread-safe LRU cache for file reads + per-thread context tracking.

    Verified APIs (all parity with v4):
      get(path) / put(path, content)
      is_in_context(path) / mark_in_context(path) / clear_context() / discard_from_context(path)
      save_and_clear_context() / restore_context(saved_set)
      enter_thread_local_context() / exit_thread_local_context()
      clear_all()
    """

    def __init__(self, max_entries: int = 100):
        self.max_entries = max_entries
        self._cache: Dict[str, Tuple[str, float]] = {}  # path -> (content, mtime)
        self._in_context: Set[str] = set()  # main-thread context markers
        self._lock = threading.RLock()
        self._local = threading.local()  # per-thread context for sub-agents

    # --------------------------------------------------------
    # Thread-local context resolution
    # --------------------------------------------------------

    def _get_context_set(self) -> Set[str]:
        """Get the context set for the current thread.

        Note: must use `is not None` (NOT `or`) — empty set is falsy
        but is still a valid thread-local context.
        """
        ctx = getattr(self._local, "in_context", None)
        return ctx if ctx is not None else self._in_context

    # --------------------------------------------------------
    # LRU cache (mtime-validated)
    # --------------------------------------------------------

    def get(self, path: str) -> Optional[str]:
        """Return cached content if file's mtime is unchanged. LRU-promotes."""
        abs_path = os.path.abspath(path)
        with self._lock:
            if abs_path not in self._cache:
                return None
            content, cached_mtime = self._cache[abs_path]
            try:
                current_mtime = os.path.getmtime(abs_path)
                if current_mtime == cached_mtime:
                    # Promote to most-recently-used (move to end of dict).
                    self._cache[abs_path] = self._cache.pop(abs_path)
                    return content
            except OSError:
                pass
            # File changed or unreadable — invalidate.
            del self._cache[abs_path]
            return None

    def put(self, path: str, content: str) -> None:
        """Cache file content + mtime. Evicts LRU at capacity."""
        abs_path = os.path.abspath(path)
        try:
            mtime = os.path.getmtime(abs_path)
            with self._lock:
                if abs_path in self._cache:
                    del self._cache[abs_path]
                elif len(self._cache) >= self.max_entries:
                    lru_key = next(iter(self._cache))
                    del self._cache[lru_key]
                self._cache[abs_path] = (content, mtime)
        except OSError:
            pass

    # --------------------------------------------------------
    # Context tracking (per-thread)
    # --------------------------------------------------------

    def is_in_context(self, path: str) -> bool:
        abs_path = os.path.abspath(path)
        with self._lock:
            return abs_path in self._get_context_set()

    def mark_in_context(self, path: str) -> None:
        abs_path = os.path.abspath(path)
        with self._lock:
            self._get_context_set().add(abs_path)

    def discard_from_context(self, path: str) -> None:
        abs_path = os.path.abspath(path)
        with self._lock:
            self._get_context_set().discard(abs_path)

    def clear_context(self) -> None:
        """Clear context tracking for the current thread."""
        with self._lock:
            ctx = getattr(self._local, "in_context", None)
            if ctx is not None:
                ctx.clear()
            else:
                self._in_context.clear()

    # --------------------------------------------------------
    # Sub-agent boundary helpers (Plan v3 §Block B+)
    # --------------------------------------------------------

    def save_and_clear_context(self) -> Set[str]:
        """Atomic snapshot-and-clear of the MAIN context set.

        Returns the saved set so the caller can later pass it back to
        `restore_context()`. Used at sub-agent dispatch entry to give
        the child a clean slate.
        """
        with self._lock:
            saved = self._in_context.copy()
            self._in_context.clear()
            return saved

    def restore_context(self, saved: Set[str]) -> None:
        """Atomically restore the main context set from a saved snapshot."""
        with self._lock:
            self._in_context = saved

    def enter_thread_local_context(self) -> None:
        """Give the current thread its own isolated empty context set.

        Call at the top of a parallel sub-agent thread so sub-agents
        don't pollute each other's `is_in_context` checks.
        """
        self._local.in_context = set()

    def exit_thread_local_context(self) -> None:
        """Drop thread-local context, reverting to the main context."""
        self._local.in_context = None

    # --------------------------------------------------------
    # Test/maintenance
    # --------------------------------------------------------

    def clear_all(self) -> None:
        """Clear LRU cache + main context. Per-thread contexts unchanged."""
        with self._lock:
            self._cache.clear()
            self._in_context.clear()


# Module-level singleton (parity with v4 `FILE_CACHE = FileCache()`).
FILE_CACHE = FileCache()


__all__ = ["FileCache", "FILE_CACHE"]
