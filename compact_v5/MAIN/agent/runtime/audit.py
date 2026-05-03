"""Block B — AuditLogger + AuditEntry verbatim port.

Verbatim port of v4's `AuditLogger` (compact_v4/MAIN/agent/sagemaker_agent.py
lines 2173-2253) plus its `AuditEntry` dataclass (lines 2156-2170).
Adaptations for v5: constructor takes a config object (instead of reading
the global CONFIG singleton at import time) so tests can pin
`audit_dir` + `audit_retention_days` + `disable_local_traces` without
monkey-patching the live runtime.

PORT_LOG: see #043.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class AuditEntry:
    """Single audit log entry. SHA256(content_prefix) hash for tamper detection."""

    timestamp: str
    session_id: str
    action: str
    tool_name: Optional[str]
    parameters: Dict[str, Any]
    result_summary: str
    user_approved: bool
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            content = (
                f"{self.timestamp}|{self.session_id}|{self.action}|"
                f"{self.tool_name}|{self.result_summary}"
            )
            self.hash = hashlib.sha256(content.encode()).hexdigest()[:32]


class AuditLogger:
    """Thread-safe append-only audit trail with integrity hashes.

    Writes one JSONL file per session+date. Sensitive parameter keys
    (password / secret / token / api_key / etc.) are redacted before
    serialization. Long string values are summarized as `[N chars]`.
    """

    SENSITIVE_KEYS = {
        "password", "secret", "key", "token", "credential",
        "api_key", "auth", "bearer", "private",
    }

    def __init__(self, audit_dir: Optional[str] = None, config=None):
        from runtime.config import CONFIG as _CFG  # local import avoids cycles
        self._config = config if config is not None else _CFG
        self.audit_dir = audit_dir or self._config.audit_dir
        self._lock = threading.Lock()
        self._disabled = self._config.disable_local_traces
        if not self._disabled:
            try:
                os.makedirs(self.audit_dir, exist_ok=True)
                self.prune_old_logs(self._config.audit_retention_days)
            except OSError as e:
                logging.warning(f"AuditLogger: cannot create audit_dir {self.audit_dir}: {e}")
                self._disabled = True

    # --------------------------------------------------------
    # Path resolution
    # --------------------------------------------------------

    def _get_log_path(self, session_id: str) -> str:
        date = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.audit_dir, f"{date}_{session_id}.jsonl")

    # --------------------------------------------------------
    # Public log API
    # --------------------------------------------------------

    def log(
        self,
        session_id: str,
        action: str,
        tool_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        result_summary: str = "",
        user_approved: bool = True,
    ):
        """Append an audit entry. No-op when stealth-mode disabled."""
        if self._disabled:
            return
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            action=action,
            tool_name=tool_name,
            parameters=self._sanitize_params(parameters or {}),
            result_summary=result_summary[:500] if result_summary else "",
            user_approved=user_approved,
        )
        log_path = self._get_log_path(session_id)
        with self._lock:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry)) + "\n")

    # --------------------------------------------------------
    # Sanitizer (verbatim from v4)
    # --------------------------------------------------------

    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        sanitized: Dict[str, Any] = {}
        for k, v in params.items():
            if any(s in k.lower() for s in self.SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, str) and len(v) > 1000:
                sanitized[k] = f"[{len(v)} chars]"
            else:
                sanitized[k] = v
        return sanitized

    # --------------------------------------------------------
    # Read API
    # --------------------------------------------------------

    def get_session_log(self, session_id: str) -> List[Dict[str, Any]]:
        """Return all entries for a session_id, sorted by timestamp."""
        if self._disabled or not os.path.isdir(self.audit_dir):
            return []
        entries: List[Dict[str, Any]] = []
        for filename in os.listdir(self.audit_dir):
            if session_id in filename and filename.endswith(".jsonl"):
                path = os.path.join(self.audit_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                entries.append(json.loads(line))
                except (OSError, json.JSONDecodeError):
                    continue
        return sorted(entries, key=lambda x: x.get("timestamp", ""))

    # --------------------------------------------------------
    # Retention
    # --------------------------------------------------------

    def prune_old_logs(self, retention_days: int):
        """Delete audit logs older than retention_days based on filename date prefix."""
        if retention_days <= 0 or not os.path.isdir(self.audit_dir):
            return
        cutoff = datetime.now().date() - timedelta(days=retention_days)
        for filename in os.listdir(self.audit_dir):
            if not filename.endswith(".jsonl"):
                continue
            date_str = filename.split("_", 1)[0]
            try:
                file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            if file_date < cutoff:
                try:
                    os.remove(os.path.join(self.audit_dir, filename))
                except OSError:
                    pass


# Module-level singleton (parity with v4 `AUDIT = AuditLogger(CONFIG.audit_dir)`).
AUDIT = AuditLogger()


__all__ = ["AuditEntry", "AuditLogger", "AUDIT"]
