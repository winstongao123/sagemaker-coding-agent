"""Block B+ — Session dataclass + SessionManager + SESSIONS singleton.

Verbatim port of v4's `SessionManager` (compact_v4/MAIN/agent/sagemaker_agent.py
lines 2578-2659) + the `Session` dataclass it consumes. Adaptations for v5:
constructor accepts a config object (vs. reading the global CONFIG at
import-time) so tests can pin behavior.

Atomic save: write to tempfile.mkstemp() in the same dir, then os.replace()
into final path (atomic on POSIX + Windows). If write fails, the tmp file
is unlinked.

PORT_LOG: see #048.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# ============================================================
# Session dataclass
# ============================================================

@dataclass
class Session:
    """Persistent session record. Schema mirrors v4."""

    id: str
    created_at: str
    updated_at: str
    title: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    todos: List[Dict[str, Any]] = field(default_factory=list)


# ============================================================
# SessionManager
# ============================================================

class SessionManager:
    """Persistent session storage with atomic save (tempfile + os.replace)."""

    _save_lock = threading.Lock()

    def __init__(self, sessions_dir: Optional[str] = None, config=None):
        self._config_override = config
        cfg = self._config
        self.sessions_dir = sessions_dir or cfg.sessions_dir
        if not cfg.disable_local_traces:
            try:
                os.makedirs(self.sessions_dir, exist_ok=True)
            except OSError as e:
                logging.warning(
                    f"SessionManager: cannot create sessions_dir "
                    f"{self.sessions_dir}: {e}"
                )

    @property
    def _config(self):
        """Resolve CONFIG lazily so reloads in tests don't strand us."""
        if self._config_override is not None:
            return self._config_override
        from runtime.config import CONFIG as _CFG  # noqa: F401
        return _CFG

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    def create(self, title: str = "New Session") -> Session:
        """Create a new session and persist its initial state."""
        session_id = (
            datetime.now().strftime("%Y%m%d_%H%M%S")
            + "_"
            + os.urandom(3).hex()
        )
        now = datetime.now().isoformat()
        session = Session(
            id=session_id,
            created_at=now,
            updated_at=now,
            title=title,
            messages=[],
            metadata={},
        )
        self.save(session)
        return session

    # --------------------------------------------------------
    # Atomic save
    # --------------------------------------------------------

    def save(self, session: Session):
        """Save session to disk (atomic: tmp + os.replace, with lock).

        No-op in stealth mode (CONFIG.disable_local_traces=True). On
        Windows, os.replace() is atomic across the same filesystem.
        """
        if self._config.disable_local_traces:
            return
        session.updated_at = datetime.now().isoformat()
        path = os.path.join(self.sessions_dir, f"{session.id}.json")
        with self._save_lock:
            fd, tmp_path = tempfile.mkstemp(
                suffix=".tmp", dir=self.sessions_dir
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(asdict(session), f, indent=2)
                os.replace(tmp_path, path)
            except Exception:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise

    # --------------------------------------------------------
    # Load / list / delete
    # --------------------------------------------------------

    def load(self, session_id: str) -> Optional[Session]:
        """Load a Session record by id, or None if missing/corrupt."""
        path = os.path.join(self.sessions_dir, f"{session_id}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Tolerate schema evolution: drop unknown fields rather than crash.
            known = {
                "id", "created_at", "updated_at", "title",
                "messages", "metadata", "todos",
            }
            return Session(**{k: v for k, v in data.items() if k in known})
        except (OSError, json.JSONDecodeError, TypeError) as e:
            logging.warning(f"Session load failed for {session_id}: {e}")
            return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all session records (id, title, updated_at), newest first."""
        sessions: List[Dict[str, Any]] = []
        if not os.path.isdir(self.sessions_dir):
            return sessions
        for filename in os.listdir(self.sessions_dir):
            if not filename.endswith(".json"):
                continue
            try:
                with open(
                    os.path.join(self.sessions_dir, filename),
                    "r", encoding="utf-8",
                ) as f:
                    data = json.load(f)
                sessions.append({
                    "id": data["id"],
                    "title": data["title"],
                    "updated_at": data["updated_at"],
                })
            except (json.JSONDecodeError, KeyError, OSError) as e:
                logging.debug(f"Skipping corrupt session file {filename}: {e}")
                continue
        return sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)

    def delete(self, session_id: str) -> bool:
        """Delete a session file. Returns True if a file was removed."""
        path = os.path.join(self.sessions_dir, f"{session_id}.json")
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except OSError:
                return False
        return False


# Module-level singleton (parity with v4 `SESSIONS = SessionManager(CONFIG.sessions_dir)`).
SESSIONS = SessionManager()


__all__ = ["Session", "SessionManager", "SESSIONS"]
