"""
Python Execution Tool - Sandboxed Python code execution
"""
import subprocess
import tempfile
import os
import sys

# Lazy import
Tool = None


def _get_tool_class():
    global Tool
    if Tool is None:
        from core.tools import Tool as T
        Tool = T
    return Tool


def execute_python(args: dict, ctx) -> str:
    """Execute Python code in isolated subprocess."""
    code = args["code"]
    timeout = args.get("timeout", 60)  # 1 minute default

    # Validate timeout
    if timeout > 300:
        timeout = 300  # Max 5 minutes for Python

    # Create temp file for code
    fd, temp_path = tempfile.mkstemp(suffix=".py", prefix="agent_exec_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)

        # Prepare environment
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        # Run in subprocess
        result = subprocess.run(
            [sys.executable, temp_path],
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

        # Truncate long output
        if len(output) > 50000:
            output = output[:50000] + "\n... (output truncated at 50KB)"

        return output if output else "(no output)"

    except subprocess.TimeoutExpired:
        return f"Error: Code execution timed out after {timeout} seconds"
    except Exception as e:
        return f"Error executing Python code: {str(e)}"
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except OSError:
            pass


# Tool definition
def get_tool():
    """Get Python execution tool."""
    Tool = _get_tool_class()

    return Tool(
        name="python_exec",
        description="Execute Python code. Use for data processing, calculations, generating files (Word, Excel, etc.). Code runs in isolated subprocess.",
        parameters={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 60, max: 300)",
                },
            },
            "required": ["code"],
        },
        execute=execute_python,
        requires_approval=True,
    )


# Export tool
PYTHON_EXEC = get_tool()
