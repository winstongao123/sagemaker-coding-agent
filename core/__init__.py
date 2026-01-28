"""
SageMaker Coding Agent - Core Module
"""
from .security import SecurityManager, SecurityConfig
from .audit import AuditLogger, AuditEntry
from .bedrock_client import BedrockClient, Response, ToolCall
from .tools import Tool, ToolRegistry, ToolContext
from .permissions import PermissionManager, PermissionAction, PermissionResult
from .agent_loop import AgentLoop, AgentState
from .memory import SessionManager, Session
from .context_manager import ContextManager, ContextCheckpoint
from .project_config import ProjectConfig
from .prompts import PromptBuilder

__all__ = [
    "SecurityManager",
    "SecurityConfig",
    "AuditLogger",
    "AuditEntry",
    "BedrockClient",
    "Response",
    "ToolCall",
    "Tool",
    "ToolRegistry",
    "ToolContext",
    "PermissionManager",
    "PermissionAction",
    "PermissionResult",
    "AgentLoop",
    "AgentState",
    "SessionManager",
    "Session",
    "ContextManager",
    "ContextCheckpoint",
    "ProjectConfig",
    "PromptBuilder",
]
