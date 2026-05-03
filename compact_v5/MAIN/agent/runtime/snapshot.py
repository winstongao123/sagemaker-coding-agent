"""Block B — SnapshotManager + SNAPSHOTS singleton.

Verbatim port of v4's `SnapshotManager` (compact_v4/MAIN/agent/sagemaker_agent.py
lines 4418-4510). Adaptations for v5: constructor takes a config object
instead of reading the global CONFIG singleton at import time.

PORT_LOG: see #044.
"""
from __future__ import annotations

import os
import re
import shutil
import threading
import time
from typing import Any, Dict, List, Optional, Tuple


class SnapshotManager:
    """Thread-safe file backup manager. Saves a backup before edit_file /
    write_file / skill_apply_proposal so users can revert.

    Each snapshot is `<workspace>/.snapshots/<unix_ms>_<safe_relpath>`.
    LRU eviction at 200 entries: prefers to drop a duplicate snapshot
    of the most-snapped file (keep at least 1 per file).
    """

    MAX_SNAPSHOTS = 200

    def __init__(self, workspace: Optional[str] = None, config=None):
        self._config_override = config
        self._workspace = workspace or self._config.workspace
        self._dir = os.path.join(self._workspace, ".snapshots")
        self._log: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    @property
    def _config(self):
        """Resolve CONFIG lazily so reloads in tests don't strand us."""
        if self._config_override is not None:
            return self._config_override
        from runtime.config import CONFIG as _CFG  # noqa: F401
        return _CFG

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    def save(self, filepath: str) -> Optional[str]:
        """Snapshot a file before modification. Returns snapshot path or None.

        No-op when CONFIG.disable_local_traces is True (stealth mode).

        Codex Block-B finding #6 (LOW) lock: path generation + copy run
        under the lock so two concurrent saves of the same file in the
        same millisecond cannot collide on `snap_path`. UUID suffix
        added for further safety even at sub-ms resolution.
        """
        if self._config.disable_local_traces:
            return None
        if not os.path.isfile(filepath):
            return None
        try:
            os.makedirs(self._dir, exist_ok=True)
            try:
                rel = os.path.relpath(filepath, self._workspace)
            except ValueError:
                # Different drive on Windows — fall back to absolute basename.
                rel = os.path.basename(filepath)
            safe_name = re.sub(r"[^\w.]", "_", rel)
            evicted_path: Optional[str] = None
            with self._lock:
                # ts + uuid suffix derived under lock so collision is
                # eliminated for concurrent same-file saves.
                import uuid as _uuid
                ts = int(time.time() * 1000)
                suffix = _uuid.uuid4().hex[:8]
                snap_path = os.path.join(self._dir, f"{ts}_{suffix}_{safe_name}")
                shutil.copy2(filepath, snap_path)
                entry = {
                    "file": filepath,
                    "rel": rel,
                    "snapshot": snap_path,
                    "time": time.time(),
                }
                self._log.append(entry)
                if len(self._log) > self.MAX_SNAPSHOTS:
                    evicted_path = self._evict_oldest_locked()
            # Remove evicted snapshot file outside lock (I/O can be slow).
            if evicted_path:
                try:
                    os.remove(evicted_path)
                except OSError:
                    pass
            return snap_path
        except OSError:
            return None

    def _evict_oldest_locked(self) -> Optional[str]:
        """Pick a snapshot to evict. Caller must hold self._lock."""
        file_counts: Dict[str, int] = {}
        for e in self._log:
            file_counts[e["file"]] = file_counts.get(e["file"], 0) + 1
        most_snapped = max(file_counts, key=file_counts.get)
        for i, e in enumerate(self._log):
            if e["file"] == most_snapped and file_counts[most_snapped] > 1:
                evicted = self._log.pop(i)
                return evicted["snapshot"]
        # All files have exactly one snapshot — drop the oldest.
        evicted = self._log.pop(0)
        return evicted["snapshot"]

    # --------------------------------------------------------
    # List / revert
    # --------------------------------------------------------

    def list_snapshots(self, filepath: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if filepath:
                return [e for e in self._log if e["file"] == filepath]
            return list(self._log)

    def revert(self, filepath: str) -> Tuple[bool, str]:
        """Revert a file to its most recent snapshot."""
        with self._lock:
            matching = [e for e in self._log if e["file"] == filepath]
        if not matching:
            return False, f"No snapshots for {filepath}"
        latest = matching[-1]
        if not os.path.isfile(latest["snapshot"]):
            return False, "Snapshot file missing"
        try:
            shutil.copy2(latest["snapshot"], filepath)
            return (
                True,
                f"Reverted {filepath} to snapshot from "
                f"{time.strftime('%H:%M:%S', time.localtime(latest['time']))}",
            )
        except OSError as e:
            return False, f"Revert failed: {e}"

    def revert_all(self) -> str:
        """Revert all files to their earliest snapshots."""
        reverted: List[str] = []
        with self._lock:
            files_seen: Dict[str, Dict[str, Any]] = {}
            for entry in self._log:
                if entry["file"] not in files_seen:
                    files_seen[entry["file"]] = entry
        for filepath, entry in files_seen.items():
            if os.path.isfile(entry["snapshot"]):
                try:
                    shutil.copy2(entry["snapshot"], filepath)
                    reverted.append(entry["rel"])
                except OSError:
                    pass
        if reverted:
            return f"Reverted {len(reverted)} files: {', '.join(reverted)}"
        return "No files to revert"


# Module-level singleton (parity with v4 `SNAPSHOTS = SnapshotManager(CONFIG.workspace)`).
SNAPSHOTS = SnapshotManager()


__all__ = ["SnapshotManager", "SNAPSHOTS"]
