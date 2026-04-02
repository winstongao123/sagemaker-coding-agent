"""
Tool System - Tool registry and execution context
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, Any, List, Optional, Set


@dataclass
class Tool:
    """Definition of a tool available to the agent."""

    name: str
    description: str
    parameters: dict  # JSON Schema for parameters
    execute: Callable[[dict, "ToolContext"], str]
    requires_approval: bool = False


@dataclass
class ToolContext:
    """Execution context passed to tools."""

    working_dir: str
    session_id: str
    files_read: Set[str] = field(default_factory=set)
    security_manager: Any = None
    permission_manager: Any = None
    audit_logger: Any = None

    def mark_file_read(self, path: str):
        """Mark a file as having been read."""
        self.files_read.add(path)

    def was_file_read(self, path: str) -> bool:
        """Check if file was previously read."""
        return path in self.files_read


class ToolRegistry:
    """Registry of available tools."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool."""
        self.tools[tool.name] = tool

    def register_all(self, tools: List[Tool]):
        """Register multiple tools."""
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name."""
        return self.tools.get(name)

    def get_tool_definitions(self, subset: Optional[List[str]] = None) -> List[Dict]:
        """
        Get tool definitions for Bedrock API.

        Args:
            subset: Optional list of tool names to include. If None, returns all.

        Returns:
            List of tool definitions in Bedrock format
        """
        tools_to_include = self.tools.values()
        if subset:
            tools_to_include = [t for t in self.tools.values() if t.name in subset]

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            }
            for tool in tools_to_include
        ]

    def select_tools_for_message(self, message: str) -> List[str]:
        """
        Dynamically select relevant tools based on user message.

        Reduces token usage by not sending all tool definitions.

        Args:
            message: User's message

        Returns:
            List of tool names to include
        """
        msg_lower = message.lower()

        # Always include core tools
        selected = {"read_file", "todo_write", "todo_read"}

        # File operations
        if any(w in msg_lower for w in ["write", "create", "make", "add"]):
            selected.add("write_file")
            selected.add("edit_file")

        if any(w in msg_lower for w in ["edit", "change", "modify", "update", "fix"]):
            selected.add("edit_file")
            selected.add("read_file")

        # Search
        if any(w in msg_lower for w in ["search", "find", "look", "where", "grep"]):
            selected.add("grep")
            selected.add("glob")

        if any(w in msg_lower for w in ["list", "show", "dir", "folder", "files"]):
            selected.add("glob")
            selected.add("list_dir")

        # Execution
        if any(w in msg_lower for w in ["run", "execute", "bash", "git", "npm", "pip", "test"]):
            selected.add("bash")

        if any(w in msg_lower for w in ["python", "script", "code"]):
            selected.add("python_exec")

        # Documents
        if any(w in msg_lower for w in ["word", "docx", "document"]):
            selected.add("create_word")

        if any(w in msg_lower for w in ["excel", "xlsx", "spreadsheet"]):
            selected.add("create_excel")

        if any(w in msg_lower for w in ["markdown", ".md", "readme"]):
            selected.add("create_markdown")

        # Vision
        if any(w in msg_lower for w in ["image", "picture", "screenshot", "png", "jpg"]):
            selected.add("view_image")

        # Semantic search
        if any(w in msg_lower for w in ["semantic", "meaning", "concept"]):
            selected.add("semantic_search")

        return list(selected)

    def execute(self, name: str, args: dict, ctx: ToolContext) -> str:
        """
        Execute a tool by name.

        Args:
            name: Tool name
            args: Tool arguments
            ctx: Execution context

        Returns:
            Tool result as string
        """
        tool = self.tools.get(name)
        if not tool:
            return f"Error: Unknown tool '{name}'"

        # Security check for paths
        if ctx.security_manager:
            # Check file_path parameter
            if "file_path" in args:
                valid, msg = ctx.security_manager.validate_path(args["file_path"])
                if not valid:
                    return f"Security Error: {msg}"

            # Check path parameter
            if "path" in args:
                valid, msg = ctx.security_manager.validate_path(args["path"])
                if not valid:
                    return f"Security Error: {msg}"

            # Check command parameter
            if "command" in args:
                valid, msg = ctx.security_manager.validate_command(args["command"])
                if not valid:
                    return f"Security Error: {msg}"

        # Log the tool call
        if ctx.audit_logger:
            ctx.audit_logger.log(
                session_id=ctx.session_id,
                action="tool_call",
                tool_name=name,
                parameters=args,
                result_summary="executing...",
            )

        try:
            result = tool.execute(args, ctx)

            # Truncate output if needed
            if ctx.security_manager:
                result, was_truncated = ctx.security_manager.truncate_output(result)

            # Log success
            if ctx.audit_logger:
                summary = result[:100] if len(result) > 100 else result
                ctx.audit_logger.log(
                    session_id=ctx.session_id,
                    action="tool_result",
                    tool_name=name,
                    parameters={},
                    result_summary=summary,
                )

            return result

        except Exception as e:
            error_msg = f"Error executing {name}: {str(e)}"

            # Log error
            if ctx.audit_logger:
                ctx.audit_logger.log(
                    session_id=ctx.session_id,
                    action="tool_error",
                    tool_name=name,
                    parameters={},
                    result_summary=error_msg,
                )

            return error_msg

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())

    def get_tool_info(self, name: str) -> Optional[Dict]:
        """Get detailed info about a tool."""
        tool = self.tools.get(name)
        if not tool:
            return None

        return {
            "name": tool.name,
            "description": tool.description,
            "requires_approval": tool.requires_approval,
            "parameters": tool.parameters,
        }
