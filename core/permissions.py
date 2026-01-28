"""
Permission System - Multi-level approval for tool execution
"""
from dataclasses import dataclass, field
from typing import Dict, Set, Optional, Callable
from enum import Enum


class PermissionAction(Enum):
    """Permission action types."""

    ALLOW = "allow"  # Always allow
    DENY = "deny"  # Always deny
    ASK = "ask"  # Ask user each time
    ASK_ONCE = "ask_once"  # Ask once per session


@dataclass
class PermissionRequest:
    """Request for user permission."""

    tool_name: str
    operation: str
    target: str  # file path, command, etc.
    risk_level: str  # "low", "medium", "high"


@dataclass
class PermissionResult:
    """Result of permission check."""

    allowed: bool
    reason: str
    remember: bool = False  # Remember this decision


class PermissionManager:
    """Multi-level permission system with audit integration."""

    # Default permission rules by tool
    DEFAULT_RULES = {
        # Read-only tools - always allow
        "read_file": PermissionAction.ALLOW,
        "glob": PermissionAction.ALLOW,
        "grep": PermissionAction.ALLOW,
        "list_dir": PermissionAction.ALLOW,
        "view_image": PermissionAction.ALLOW,
        "todo_read": PermissionAction.ALLOW,
        "semantic_search": PermissionAction.ALLOW,
        # Write tools - ask once per session
        "write_file": PermissionAction.ASK_ONCE,
        "edit_file": PermissionAction.ASK_ONCE,
        "create_markdown": PermissionAction.ASK_ONCE,
        # High-risk tools - always ask
        "bash": PermissionAction.ASK,
        "python_exec": PermissionAction.ASK,
        "create_word": PermissionAction.ASK,
        "create_excel": PermissionAction.ASK,
        # Task management - always allow
        "todo_write": PermissionAction.ALLOW,
    }

    def __init__(
        self,
        audit_logger=None,
        on_permission_request: Optional[Callable[[PermissionRequest], PermissionResult]] = None,
    ):
        """
        Initialize permission manager.

        Args:
            audit_logger: AuditLogger instance for logging decisions
            on_permission_request: Callback to prompt user for permission
        """
        self.audit = audit_logger
        self.on_request = on_permission_request
        self.session_approvals: Dict[str, Set[str]] = {}  # session_id -> approved patterns
        self.always_approved: Set[str] = set()
        self.always_denied: Set[str] = set()

    def check_permission(
        self,
        session_id: str,
        tool_name: str,
        target: str,
        context: Optional[Dict] = None,
    ) -> PermissionResult:
        """
        Check if operation is permitted.

        Args:
            session_id: Current session identifier
            tool_name: Name of tool being called
            target: Target of operation (file path, command, etc.)
            context: Additional context

        Returns:
            PermissionResult with decision
        """
        rule = self.DEFAULT_RULES.get(tool_name, PermissionAction.ASK)
        pattern = f"{tool_name}:{target}"

        # Check always-denied list first
        if pattern in self.always_denied:
            self._log_decision(session_id, tool_name, target, False, "Always denied")
            return PermissionResult(allowed=False, reason="Always denied")

        # Always allow
        if rule == PermissionAction.ALLOW:
            return PermissionResult(allowed=True, reason="Tool always allowed")

        # Always deny
        if rule == PermissionAction.DENY:
            self._log_decision(session_id, tool_name, target, False, "Denied by rule")
            return PermissionResult(allowed=False, reason="Tool not permitted")

        # Check if in always-approved list
        if pattern in self.always_approved:
            return PermissionResult(allowed=True, reason="Always approved")

        # Check if already approved for this session (ASK_ONCE)
        if rule == PermissionAction.ASK_ONCE:
            if session_id in self.session_approvals:
                # Check for exact match or tool-level approval
                if pattern in self.session_approvals[session_id]:
                    return PermissionResult(allowed=True, reason="Previously approved this session")
                if f"{tool_name}:*" in self.session_approvals[session_id]:
                    return PermissionResult(allowed=True, reason="Tool approved for session")

        # Need to ask user
        if self.on_request:
            request = PermissionRequest(
                tool_name=tool_name,
                operation=context.get("operation", "execute") if context else "execute",
                target=target,
                risk_level=self._assess_risk(tool_name, target),
            )
            result = self.on_request(request)

            # Log the decision
            self._log_decision(session_id, tool_name, target, result.allowed, result.reason)

            # Remember if requested
            if result.remember:
                self._remember_decision(session_id, pattern, result.allowed)

            return result

        # No handler - deny by default for safety
        return PermissionResult(allowed=False, reason="No permission handler configured")

    def _assess_risk(self, tool_name: str, target: str) -> str:
        """Assess risk level of operation."""
        high_risk = {"bash", "python_exec"}
        if tool_name in high_risk:
            return "high"

        # Check target for sensitive patterns
        sensitive = [".env", "secret", "password", "credential", "key", "token", "auth"]
        if any(s in target.lower() for s in sensitive):
            return "high"

        if tool_name in {"write_file", "edit_file"}:
            return "medium"

        return "low"

    def _log_decision(
        self, session_id: str, tool_name: str, target: str, allowed: bool, reason: str
    ):
        """Log permission decision to audit trail."""
        if self.audit:
            self.audit.log(
                session_id=session_id,
                action="permission_decision",
                tool_name=tool_name,
                parameters={"target": target, "reason": reason},
                result_summary="Approved" if allowed else "Denied",
                user_approved=allowed,
            )

    def _remember_decision(self, session_id: str, pattern: str, allowed: bool):
        """Remember a permission decision."""
        if allowed:
            if session_id not in self.session_approvals:
                self.session_approvals[session_id] = set()
            self.session_approvals[session_id].add(pattern)
        else:
            self.always_denied.add(pattern)

    def approve_tool_for_session(self, session_id: str, tool_name: str):
        """Approve all uses of a tool for this session."""
        if session_id not in self.session_approvals:
            self.session_approvals[session_id] = set()
        self.session_approvals[session_id].add(f"{tool_name}:*")

    def always_allow(self, tool_name: str, target: str = "*"):
        """Always allow a specific tool/target combination."""
        self.always_approved.add(f"{tool_name}:{target}")

    def always_deny(self, tool_name: str, target: str = "*"):
        """Always deny a specific tool/target combination."""
        self.always_denied.add(f"{tool_name}:{target}")

    def clear_session(self, session_id: str):
        """Clear all approvals for a session."""
        if session_id in self.session_approvals:
            del self.session_approvals[session_id]

    def get_session_approvals(self, session_id: str) -> Set[str]:
        """Get all approvals for a session."""
        return self.session_approvals.get(session_id, set())
