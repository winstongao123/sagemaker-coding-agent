"""Block B — SnapshotManager + SNAPSHOTS singleton.

Verbatim port of v4's `SnapshotManager` (compact_v4/MAIN/agent/sagemaker_agent.py
lines 4418-4510). Adaptations for v5: constructor takes a config object
instead of reading the global CONFIG singleton at import time.

PORT_LOG: see #044.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
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
        self._checkpoints: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._load_index()

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

    @property
    def index_path(self) -> str:
        return os.path.join(self._dir, "index.json")

    def _load_index(self) -> None:
        path = self.index_path
        if not os.path.isfile(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError, TypeError):
            return
        snapshots = data.get("snapshots", [])
        checkpoints = data.get("checkpoints", [])
        if isinstance(snapshots, list):
            self._log = [dict(s) for s in snapshots if isinstance(s, dict)]
        if isinstance(checkpoints, list):
            self._checkpoints = [
                dict(c) for c in checkpoints if isinstance(c, dict)
            ]

    def _persist_index_locked(self) -> None:
        if self._config.disable_local_traces:
            return
        os.makedirs(self._dir, exist_ok=True)
        payload = {
            "schema": "sageagent.snapshots.v1",
            "updated_at": time.time(),
            "snapshots": list(self._log),
            "checkpoints": list(self._checkpoints),
        }
        fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=self._dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, sort_keys=True)
                f.write("\n")
            os.replace(tmp_path, self.index_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

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
                    "id": f"{ts}_{suffix}",
                    "file": filepath,
                    "rel": rel,
                    "snapshot": snap_path,
                    "time": time.time(),
                }
                self._log.append(entry)
                if len(self._log) > self.MAX_SNAPSHOTS:
                    evicted_path = self._evict_oldest_locked()
                self._persist_index_locked()
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

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._checkpoints)

    def create_checkpoint(self, name: str, files: List[str]) -> Dict[str, Any]:
        entries: List[Dict[str, Any]] = []
        for filepath in files:
            snap_path = self.save(filepath)
            if not snap_path:
                continue
            with self._lock:
                matching = [e for e in self._log if e.get("snapshot") == snap_path]
                if matching:
                    entries.append(dict(matching[-1]))
        checkpoint = {
            "name": name,
            "time": time.time(),
            "entries": entries,
        }
        with self._lock:
            self._checkpoints = [
                c for c in self._checkpoints if c.get("name") != name
            ]
            self._checkpoints.append(checkpoint)
            self._persist_index_locked()
        return checkpoint

    def preview_revert(self, filepath: str) -> Tuple[bool, str]:
        with self._lock:
            matching = [e for e in self._log if e["file"] == filepath]
        if not matching:
            return False, f"No snapshots for {filepath}"
        latest = matching[-1]
        return (
            True,
            "Preview only; re-run with `--yes` to restore "
            f"{filepath} from snapshot {latest['snapshot']}",
        )

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

    def preview_checkpoint_restore(self, name: str) -> Tuple[bool, str]:
        with self._lock:
            matches = [c for c in self._checkpoints if c.get("name") == name]
        if not matches:
            return False, f"Checkpoint not found: {name}"
        entries = matches[-1].get("entries", [])
        files = [e.get("file", "") for e in entries if isinstance(e, dict)]
        if not files:
            return False, f"Checkpoint '{name}' has no restorable files"
        lines = "\n".join(f"  {f}" for f in files)
        return (
            True,
            f"Preview only; re-run with `--yes` to restore checkpoint '{name}'.\n"
            f"Files that would be restored:\n{lines}",
        )

    def restore_checkpoint(self, name: str) -> Tuple[bool, str]:
        with self._lock:
            matches = [c for c in self._checkpoints if c.get("name") == name]
        if not matches:
            return False, f"Checkpoint not found: {name}"
        checkpoint = matches[-1]
        restored: List[str] = []
        for entry in checkpoint.get("entries", []):
            if not isinstance(entry, dict):
                continue
            filepath = entry.get("file")
            snapshot = entry.get("snapshot")
            if not filepath or not snapshot or not os.path.isfile(snapshot):
                continue
            try:
                shutil.copy2(snapshot, filepath)
                restored.append(str(entry.get("rel") or filepath))
            except OSError:
                continue
        if not restored:
            return False, f"Checkpoint '{name}' restored 0 files"
        return True, f"Restored checkpoint '{name}': {', '.join(restored)}"

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
