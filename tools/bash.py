"""
Bash Tool - Shell command execution with security controls
"""
import subprocess
import os
import signal
from typing import Optional

# Lazy import
Tool = None


def _get_tool_class():
    global Tool
    if Tool is None:
        from core.tools import Tool as T
        Tool = T
    return Tool


def execute_bash(args: dict, ctx) -> str:
    """Execute shell command with security controls."""
    command = args["command"]
    timeout = args.get("timeout", 120)  # 2 minutes default

    # Validate timeout
    if timeout > 600:
        timeout = 600  # Max 10 minutes

    # Security validation is done in ToolRegistry.execute()
    # Additional safety check here
    dangerous_simple = ["rm -rf /", "rm -rf /*", "> /dev/sda", "mkfs", ":(){ :|:& };:"]
    for d in dangerous_simple:
        if d in command:
            return f"Error: Blocked potentially dangerous command"

    try:
        # Prepare environment
        env = os.environ.copy()
        env["TERM"] = "dumb"  # Disable terminal features
        env["NO_COLOR"] = "1"  # Disable colored output

        # Run command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=ctx.working_dir,
            env=env,
        )

        output = result.stdout
        if result.stderr:
            if output:
                output += "\n"
            output += f"[stderr]\n{result.stderr}"

        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"

        # Truncate long output (security manager will also truncate, but this is faster)
        if len(output) > 50000:
            output = output[:50000] + "\n... (output truncated at 50KB)"

        return output if output else "(no output)"

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except subprocess.SubprocessError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error executing command: {str(e)}"


# Tool definition
def get_tool():
    """Get bash tool."""
    Tool = _get_tool_class()

    return Tool(
        name="bash",
        description="Execute shell command. Use for git, pip, system commands. NOT for file reading (use read_file) or searching (use glob/grep).",
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 120, max: 600)",
                },
            },
            "required": ["command"],
        },
        execute=execute_bash,
        requires_approval=True,
    )


# Export tool
BASH = get_tool()
