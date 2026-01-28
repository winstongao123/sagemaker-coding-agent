"""
File Operations Tools - Read, write, edit, glob, list directory
"""
import os
import glob as globlib
from typing import Dict

# Import will be done at runtime to avoid circular imports
Tool = None
ToolContext = None


def _get_tool_classes():
    global Tool, ToolContext
    if Tool is None:
        from core.tools import Tool as T, ToolContext as TC
        Tool = T
        ToolContext = TC
    return Tool, ToolContext


def read_file(args: dict, ctx) -> str:
    """Read file contents with line numbers."""
    path = args["file_path"]
    offset = args.get("offset", 0)
    limit = args.get("limit", 2000)

    # Handle relative paths
    if not os.path.isabs(path):
        path = os.path.join(ctx.working_dir, path)

    # Normalize path
    path = os.path.normpath(path)

    if not os.path.exists(path):
        return f"Error: File not found: {path}"

    if os.path.isdir(path):
        return f"Error: Path is a directory, not a file: {path}"

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except IOError as e:
        return f"Error reading file: {e}"

    # Track file as read
    ctx.mark_file_read(path)

    total_lines = len(lines)

    # Apply offset and limit
    selected = lines[offset : offset + limit]

    # Format with line numbers
    result = []
    for i, line in enumerate(selected, start=offset + 1):
        # Truncate long lines
        line_content = line.rstrip()
        if len(line_content) > 2000:
            line_content = line_content[:2000] + "..."
        result.append(f"{i:6d}\t{line_content}")

    output = "\n".join(result)

    # Add info about total lines if truncated
    if total_lines > offset + limit:
        output += f"\n\n[Showing lines {offset + 1}-{offset + len(selected)} of {total_lines} total]"

    return output


def write_file(args: dict, ctx) -> str:
    """Write content to file."""
    path = args["file_path"]
    content = args["content"]

    # Handle relative paths
    if not os.path.isabs(path):
        path = os.path.join(ctx.working_dir, path)

    path = os.path.normpath(path)

    # Check if file exists and was read
    if os.path.exists(path) and not ctx.was_file_read(path):
        return "Error: Must read file before overwriting. Use read_file first."

    # Create directory if needed
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except IOError as e:
        return f"Error writing file: {e}"

    return f"Successfully wrote {len(content)} bytes to {path}"


def edit_file(args: dict, ctx) -> str:
    """Edit file by replacing exact string."""
    path = args["file_path"]
    old_string = args["old_string"]
    new_string = args["new_string"]
    replace_all = args.get("replace_all", False)

    # Handle relative paths
    if not os.path.isabs(path):
        path = os.path.join(ctx.working_dir, path)

    path = os.path.normpath(path)

    # Must have read file first
    if not ctx.was_file_read(path):
        return "Error: Must read file before editing. Use read_file first."

    if not os.path.exists(path):
        return f"Error: File not found: {path}"

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except IOError as e:
        return f"Error reading file: {e}"

    # Check if old_string exists
    count = content.count(old_string)
    if count == 0:
        # Provide helpful error message
        if len(old_string) > 50:
            preview = old_string[:50] + "..."
        else:
            preview = old_string
        return f"Error: old_string not found in file. Looking for: '{preview}'"

    if count > 1 and not replace_all:
        return f"Error: old_string appears {count} times. Use replace_all=true or provide more context to make it unique."

    # Replace
    if replace_all:
        new_content = content.replace(old_string, new_string)
        replaced_count = count
    else:
        new_content = content.replace(old_string, new_string, 1)
        replaced_count = 1

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except IOError as e:
        return f"Error writing file: {e}"

    return f"Successfully edited {path} ({replaced_count} replacement{'s' if replaced_count > 1 else ''})"


def glob_files(args: dict, ctx) -> str:
    """Find files matching glob pattern."""
    pattern = args["pattern"]
    path = args.get("path", ctx.working_dir)

    # Handle relative paths
    if not os.path.isabs(path):
        path = os.path.join(ctx.working_dir, path)

    full_pattern = os.path.join(path, pattern)
    matches = globlib.glob(full_pattern, recursive=True)

    # Filter out directories, keep only files
    matches = [m for m in matches if os.path.isfile(m)]

    # Sort by modification time, newest first
    matches = sorted(matches, key=lambda x: os.path.getmtime(x), reverse=True)

    # Limit to 100 results
    if len(matches) > 100:
        matches = matches[:100]
        truncated = True
    else:
        truncated = False

    if not matches:
        return "No files found matching pattern"

    result = "\n".join(matches)
    if truncated:
        result += f"\n\n[Showing first 100 of many matches]"

    return result


def list_directory(args: dict, ctx) -> str:
    """List directory contents."""
    path = args.get("path", ctx.working_dir)

    # Handle relative paths
    if not os.path.isabs(path):
        path = os.path.join(ctx.working_dir, path)

    path = os.path.normpath(path)

    if not os.path.exists(path):
        return f"Error: Path not found: {path}"

    if not os.path.isdir(path):
        return f"Error: Not a directory: {path}"

    entries = []
    try:
        for entry in sorted(os.listdir(path)):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                entries.append(f"[DIR]  {entry}/")
            else:
                try:
                    size = os.path.getsize(full_path)
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    else:
                        size_str = f"{size / (1024 * 1024):.1f} MB"
                    entries.append(f"[FILE] {entry} ({size_str})")
                except OSError:
                    entries.append(f"[FILE] {entry}")
    except PermissionError:
        return f"Error: Permission denied: {path}"

    if not entries:
        return "(empty directory)"

    return "\n".join(entries)


# Tool definitions
def get_tools():
    """Get all file operation tools."""
    Tool, _ = _get_tool_classes()

    READ_FILE = Tool(
        name="read_file",
        description="Read file contents. Returns lines with line numbers. Use offset/limit for large files.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"},
                "offset": {
                    "type": "integer",
                    "description": "Starting line number (0-indexed, default: 0)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum lines to read (default: 2000)",
                },
            },
            "required": ["file_path"],
        },
        execute=read_file,
        requires_approval=False,
    )

    WRITE_FILE = Tool(
        name="write_file",
        description="Write content to a file. Creates file if doesn't exist. MUST read file first if it exists.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["file_path", "content"],
        },
        execute=write_file,
        requires_approval=True,
    )

    EDIT_FILE = Tool(
        name="edit_file",
        description="Edit file by replacing exact string match. MUST read file first. old_string must be EXACT.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"},
                "old_string": {"type": "string", "description": "Exact text to replace"},
                "new_string": {"type": "string", "description": "Replacement text"},
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurrences (default: false)",
                },
            },
            "required": ["file_path", "old_string", "new_string"],
        },
        execute=edit_file,
        requires_approval=True,
    )

    GLOB = Tool(
        name="glob",
        description="Find files by glob pattern (e.g., '**/*.py', 'src/**/*.ts'). Returns up to 100 matches.",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern"},
                "path": {
                    "type": "string",
                    "description": "Directory to search (default: working dir)",
                },
            },
            "required": ["pattern"],
        },
        execute=glob_files,
        requires_approval=False,
    )

    LIST_DIR = Tool(
        name="list_dir",
        description="List directory contents with file types and sizes.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path (default: working dir)",
                }
            },
            "required": [],
        },
        execute=list_directory,
        requires_approval=False,
    )

    return READ_FILE, WRITE_FILE, EDIT_FILE, GLOB, LIST_DIR


# Export tools
READ_FILE, WRITE_FILE, EDIT_FILE, GLOB, LIST_DIR = get_tools()
