"""Durable state helpers for long-running software work.

SOFTWARE-STATE closes the third-scan gap where todos, status/memory context,
and turn recovery were mostly process-local. The helpers here are deliberately
small: JSON state is atomically written under the workspace, and callers decide
which pieces to restore.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(str(tmp_path), str(path))
    except Exception:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


class DurableStateManager:
    """Workspace-scoped durable todo/context/journal state."""

    _lock = threading.Lock()

    def __init__(self, workspace: Optional[str] = None, config: Any = None):
        self._workspace_override = workspace
        self._config_override = config

    @property
    def _config(self):
        if self._config_override is not None:
            return self._config_override
        from runtime.config import CONFIG as _CFG
        return _CFG

    @property
    def workspace(self) -> Path:
        root = self._workspace_override or getattr(self._config, "workspace", os.getcwd())
        return Path(root).resolve()

    @property
    def disabled(self) -> bool:
        return bool(getattr(self._config, "disable_local_traces", False))

    @property
    def state_dir(self) -> Path:
        return self.workspace / ".sageagent_state"

    @property
    def todos_path(self) -> Path:
        return self.state_dir / "todos.json"

    @property
    def tasks_path(self) -> Path:
        return self.state_dir / "tasks.json"

    @property
    def artifacts_path(self) -> Path:
        return self.state_dir / "artifacts.json"

    @property
    def journal_path(self) -> Path:
        return self.state_dir / "turn_journal.jsonl"

    @property
    def recovery_path(self) -> Path:
        return self.state_dir / "last_turn.json"

    def _read_text_file(self, relative_name: str, max_chars: int) -> Dict[str, Any]:
        path = (self.workspace / relative_name).resolve()
        exists = path.is_file()
        text = ""
        if exists:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                text = ""
        truncated = len(text) > max_chars
        if truncated:
            text = text[:max_chars].rstrip() + "\n...[truncated]"
        return {
            "path": str(path),
            "exists": exists,
            "text": text,
            "sha256": _sha256_text(text) if text else "",
            "truncated": truncated,
            "captured_at": _utc_now(),
        }

    def capture_status_memory(self, max_chars: int = 12000) -> Dict[str, Any]:
        """Capture current status/memory pointers and capped text."""
        status_doc = getattr(self._config, "status_doc", "AGENT_STATUS.md")
        status_enabled = bool(getattr(self._config, "enable_status_doc", True))
        status = (
            self._read_text_file(status_doc, max_chars)
            if status_enabled
            else {
                "path": str((self.workspace / status_doc).resolve()),
                "exists": False,
                "text": "",
                "sha256": "",
                "truncated": False,
                "captured_at": _utc_now(),
                "disabled": True,
            }
        )
        memory = self._read_text_file("memory.md", max_chars)
        return {"status": status, "memory": memory, "captured_at": _utc_now()}

    def save_todos(self, todos: List[Dict[str, Any]]) -> None:
        if self.disabled:
            return
        payload = {
            "schema": "sageagent.todos.v1",
            "updated_at": _utc_now(),
            "todos": list(todos),
        }
        with self._lock:
            _atomic_write_json(self.todos_path, payload)

    def load_todos(self) -> List[Dict[str, Any]]:
        if self.disabled or not self.todos_path.is_file():
            return []
        try:
            data = json.loads(self.todos_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        todos = data.get("todos", [])
        if not isinstance(todos, list):
            return []
        return [dict(t) for t in todos if isinstance(t, dict)]

    def save_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        if self.disabled:
            return
        payload = {
            "schema": "sageagent.tasks.v1",
            "updated_at": _utc_now(),
            "tasks": list(tasks),
        }
        with self._lock:
            _atomic_write_json(self.tasks_path, payload)

    def load_tasks(self) -> List[Dict[str, Any]]:
        if self.disabled or not self.tasks_path.is_file():
            return []
        try:
            data = json.loads(self.tasks_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        tasks = data.get("tasks", [])
        if not isinstance(tasks, list):
            return []
        return [dict(t) for t in tasks if isinstance(t, dict)]

    def append_artifact(
        self,
        *,
        path: str,
        kind: str = "file",
        source_tool: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self.disabled or not path:
            return
        artifacts = self.load_artifacts(limit=100)
        resolved = str(Path(path).expanduser().resolve())
        artifacts = [a for a in artifacts if a.get("path") != resolved]
        artifacts.append({
            "path": resolved,
            "kind": kind or "file",
            "source_tool": source_tool or "",
            "metadata": dict(metadata or {}),
            "created_at": _utc_now(),
        })
        payload = {
            "schema": "sageagent.artifacts.v1",
            "updated_at": _utc_now(),
            "artifacts": artifacts[-100:],
        }
        with self._lock:
            _atomic_write_json(self.artifacts_path, payload)

    def load_artifacts(self, limit: int = 20) -> List[Dict[str, Any]]:
        if self.disabled or not self.artifacts_path.is_file():
            return []
        try:
            data = json.loads(self.artifacts_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        artifacts = data.get("artifacts", [])
        if not isinstance(artifacts, list):
            return []
        cleaned = [dict(a) for a in artifacts if isinstance(a, dict)]
        return cleaned[-max(1, int(limit)):]

    def append_journal(self, event: str, payload: Optional[Dict[str, Any]] = None) -> None:
        if self.disabled:
            return
        row = {
            "schema": "sageagent.turn_journal.v1",
            "event": event,
            "at": _utc_now(),
            "payload": payload or {},
        }
        text = json.dumps(row, sort_keys=True) + "\n"
        with self._lock:
            self.journal_path.parent.mkdir(parents=True, exist_ok=True)
            with self.journal_path.open("a", encoding="utf-8") as f:
                f.write(text)

    def save_turn_recovery(
        self,
        *,
        messages: List[Dict[str, Any]],
        todos: List[Dict[str, Any]],
        token_stats: Dict[str, Any],
        status_memory: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self.disabled:
            return
        payload = {
            "schema": "sageagent.turn_recovery.v1",
            "updated_at": _utc_now(),
            "messages": list(messages),
            "todos": list(todos),
            "token_stats": dict(token_stats),
            "status_memory": status_memory or self.capture_status_memory(),
            "result": result or {},
        }
        with self._lock:
            _atomic_write_json(self.recovery_path, payload)

    def load_turn_recovery(self) -> Optional[Dict[str, Any]]:
        if self.disabled or not self.recovery_path.is_file():
            return None
        try:
            data = json.loads(self.recovery_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        return data if isinstance(data, dict) else None


STATE = DurableStateManager()


__all__ = ["DurableStateManager", "STATE"]
