"""
SageMaker Coding Agent - Tools Module
"""
from .file_ops import READ_FILE, WRITE_FILE, EDIT_FILE, GLOB, LIST_DIR
from .search import GREP, SEMANTIC_SEARCH
from .bash import BASH
from .python_exec import PYTHON_EXEC
from .document import CREATE_WORD, CREATE_EXCEL, CREATE_MARKDOWN
from .vision import VIEW_IMAGE
from .todo import TODO_WRITE, TODO_READ

# All available tools
ALL_TOOLS = [
    # Read-only tools (no approval needed)
    READ_FILE,
    GLOB,
    GREP,
    LIST_DIR,
    VIEW_IMAGE,
    TODO_READ,
    SEMANTIC_SEARCH,
    # Write tools (approval required)
    WRITE_FILE,
    EDIT_FILE,
    CREATE_MARKDOWN,
    # High-risk tools (always ask)
    BASH,
    PYTHON_EXEC,
    CREATE_WORD,
    CREATE_EXCEL,
    # Task management
    TODO_WRITE,
]

__all__ = [
    "READ_FILE",
    "WRITE_FILE",
    "EDIT_FILE",
    "GLOB",
    "LIST_DIR",
    "GREP",
    "SEMANTIC_SEARCH",
    "BASH",
    "PYTHON_EXEC",
    "CREATE_WORD",
    "CREATE_EXCEL",
    "CREATE_MARKDOWN",
    "VIEW_IMAGE",
    "TODO_WRITE",
    "TODO_READ",
    "ALL_TOOLS",
]
