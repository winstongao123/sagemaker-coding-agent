"""
Audit Logger - CRITICAL SECURITY MODULE

Provides immutable audit trail for all agent actions with:
- Append-only JSONL logging
- Hash integrity verification
- Sensitive data redaction
"""
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict


@dataclass
class AuditEntry:
    """Single audit log entry."""

    timestamp: str
    session_id: str
    action: str
    tool_name: Optional[str]
    parameters: Dict[str, Any]
    result_summary: str
    user_approved: bool
    hash: str = ""

    def __post_init__(self):
        """Generate hash for integrity verification."""
        if not self.hash:
            content = f"{self.timestamp}|{self.session_id}|{self.action}|{self.tool_name}|{self.result_summary}"
            self.hash = hashlib.sha256(content.encode()).hexdigest()[:32]


class AuditLogger:
    """Immutable audit trail for all agent actions."""

    # Keys that should be redacted in logs
    SENSITIVE_KEYS = {
        "password",
        "secret",
        "key",
        "token",
        "credential",
        "api_key",
        "apikey",
        "auth",
        "bearer",
        "private",
    }

    def __init__(self, audit_dir: str = "./audit_logs"):
        self.audit_dir = audit_dir
        os.makedirs(audit_dir, exist_ok=True)

    def _get_log_path(self, session_id: str) -> str:
        """Get log file path for session."""
        date = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.audit_dir, f"{date}_{session_id}.jsonl")

    def log(
        self,
        session_id: str,
        action: str,
        tool_name: Optional[str] = None,
        parameters: Optional[Dict] = None,
        result_summary: str = "",
        user_approved: bool = True,
    ):
        """
        Log an action to the audit trail.

        Args:
            session_id: Current session identifier
            action: Action type (e.g., "tool_call", "permission_requested")
            tool_name: Name of tool being called
            parameters: Tool parameters (will be sanitized)
            result_summary: Brief summary of result
            user_approved: Whether user approved this action
        """
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            action=action,
            tool_name=tool_name,
            parameters=self._sanitize_params(parameters or {}),
            result_summary=result_summary[:500],  # Limit summary size
            user_approved=user_approved,
        )

        # Append to log file (JSONL format for append-only)
        log_path = self._get_log_path(session_id)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry)) + "\n")

    def _sanitize_params(self, params: Dict) -> Dict:
        """Remove sensitive data from parameters before logging."""
        sanitized = {}

        for k, v in params.items():
            key_lower = k.lower()

            # Check if key contains sensitive words
            if any(s in key_lower for s in self.SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, str):
                # Truncate long strings
                if len(v) > 1000:
                    sanitized[k] = f"[{len(v)} chars]"
                else:
                    sanitized[k] = v
            elif isinstance(v, dict):
                # Recursively sanitize nested dicts
                sanitized[k] = self._sanitize_params(v)
            elif isinstance(v, list):
                # Truncate long lists
                if len(v) > 10:
                    sanitized[k] = f"[{len(v)} items]"
                else:
                    sanitized[k] = v
            else:
                sanitized[k] = v

        return sanitized

    def get_session_log(self, session_id: str) -> List[Dict]:
        """Retrieve all entries for a session."""
        entries = []

        # Check all log files for this session
        for filename in os.listdir(self.audit_dir):
            if session_id in filename and filename.endswith(".jsonl"):
                log_path = os.path.join(self.audit_dir, filename)
                with open(log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            entries.append(json.loads(line))

        # Sort by timestamp
        entries.sort(key=lambda x: x.get("timestamp", ""))
        return entries

    def verify_integrity(self, session_id: str) -> Tuple[bool, List[str]]:
        """
        Verify audit log hasn't been tampered with.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        entries = self.get_session_log(session_id)
        issues = []

        for i, entry in enumerate(entries):
            content = (
                f"{entry['timestamp']}|{entry['session_id']}|"
                f"{entry['action']}|{entry['tool_name']}|{entry['result_summary']}"
            )
            expected_hash = hashlib.sha256(content.encode()).hexdigest()[:32]

            if entry.get("hash") != expected_hash:
                issues.append(f"Entry {i}: Hash mismatch (possible tampering)")

        return len(issues) == 0, issues

    def get_session_summary(self, session_id: str) -> Dict:
        """Get summary statistics for a session."""
        entries = self.get_session_log(session_id)

        if not entries:
            return {"total_actions": 0}

        tool_counts = {}
        denied_count = 0

        for entry in entries:
            tool = entry.get("tool_name", "unknown")
            tool_counts[tool] = tool_counts.get(tool, 0) + 1

            if not entry.get("user_approved", True):
                denied_count += 1

        return {
            "total_actions": len(entries),
            "tool_counts": tool_counts,
            "denied_actions": denied_count,
            "first_action": entries[0].get("timestamp") if entries else None,
            "last_action": entries[-1].get("timestamp") if entries else None,
        }

    def export_session(self, session_id: str, output_path: str):
        """Export session log to a single JSON file."""
        entries = self.get_session_log(session_id)
        is_valid, issues = self.verify_integrity(session_id)

        export_data = {
            "session_id": session_id,
            "exported_at": datetime.now().isoformat(),
            "integrity_valid": is_valid,
            "integrity_issues": issues,
            "summary": self.get_session_summary(session_id),
            "entries": entries,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)
