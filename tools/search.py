"""
Search Tools - Grep and Semantic Search
"""
import os
import re
import json
from typing import List, Dict, Tuple, Optional

# Lazy imports to avoid circular dependencies
Tool = None


def _get_tool_class():
    global Tool
    if Tool is None:
        from core.tools import Tool as T
        Tool = T
    return Tool


def grep_search(args: dict, ctx) -> str:
    """Search file contents with regex."""
    pattern = args["pattern"]
    path = args.get("path", ctx.working_dir)
    glob_pattern = args.get("glob", None)
    output_mode = args.get("output_mode", "files_with_matches")
    case_insensitive = args.get("case_insensitive", False)
    context_lines = args.get("context", 0)
    limit = args.get("limit", 100)

    # Handle relative paths
    if not os.path.isabs(path):
        path = os.path.join(ctx.working_dir, path)

    # Compile regex
    flags = re.IGNORECASE if case_insensitive else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"Error: Invalid regex pattern: {e}"

    results = []

    # Find files to search
    if glob_pattern:
        import glob as globlib
        files = globlib.glob(os.path.join(path, glob_pattern), recursive=True)
        files = [f for f in files if os.path.isfile(f)]
    elif os.path.isfile(path):
        files = [path]
    else:
        # Walk directory
        files = []
        for root, dirs, filenames in os.walk(path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in filenames:
                if not f.startswith("."):
                    files.append(os.path.join(root, f))

    match_count = 0
    files_matched = set()

    for filepath in files:
        if match_count >= limit:
            break

        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except (IOError, PermissionError):
            continue

        file_matches = []
        for i, line in enumerate(lines):
            if regex.search(line):
                files_matched.add(filepath)

                if output_mode == "files_with_matches":
                    results.append(filepath)
                    break
                elif output_mode == "content":
                    # Add context lines
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    for j in range(start, end):
                        marker = ">" if j == i else " "
                        file_matches.append(
                            f"{filepath}:{j + 1}{marker} {lines[j].rstrip()}"
                        )
                elif output_mode == "count":
                    file_matches.append(filepath)

                match_count += 1
                if match_count >= limit:
                    break

        if file_matches and output_mode != "files_with_matches":
            results.extend(file_matches)

    if output_mode == "count":
        from collections import Counter
        counts = Counter(results)
        return "\n".join(f"{path}: {count}" for path, count in counts.most_common())

    if not results:
        return "No matches found"

    output = "\n".join(results)
    if match_count >= limit:
        output += f"\n\n[Results limited to {limit} matches]"

    return output


def semantic_search(args: dict, ctx) -> str:
    """Search code using semantic embeddings."""
    query = args["query"]
    top_k = args.get("top_k", 5)

    try:
        from core.semantic_search import SemanticSearch
        searcher = SemanticSearch(
            region=ctx.security_manager.config.region if hasattr(ctx, "security_manager") else "ap-southeast-2",
            index_path=os.path.join(ctx.working_dir, ".code_index"),
        )

        results = searcher.search(query, top_k=top_k)
        return searcher.format_results(results)
    except ImportError:
        return "Error: Semantic search not available. Index the codebase first."
    except Exception as e:
        return f"Error in semantic search: {e}"


# Tool definitions
def get_tools():
    """Get all search tools."""
    Tool = _get_tool_class()

    GREP = Tool(
        name="grep",
        description="Search file contents with regex. Supports context lines, case-insensitive search, and glob filtering.",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory to search",
                },
                "glob": {
                    "type": "string",
                    "description": "Glob pattern to filter files (e.g., '*.py')",
                },
                "output_mode": {
                    "type": "string",
                    "enum": ["files_with_matches", "content", "count"],
                    "description": "Output format (default: files_with_matches)",
                },
                "case_insensitive": {
                    "type": "boolean",
                    "description": "Case insensitive search",
                },
                "context": {
                    "type": "integer",
                    "description": "Lines of context around matches",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results (default: 100)",
                },
            },
            "required": ["pattern"],
        },
        execute=grep_search,
        requires_approval=False,
    )

    SEMANTIC_SEARCH = Tool(
        name="semantic_search",
        description="Search code by meaning using natural language. Finds code by concept, not just keywords.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query describing what you're looking for",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                },
            },
            "required": ["query"],
        },
        execute=semantic_search,
        requires_approval=False,
    )

    return GREP, SEMANTIC_SEARCH


# Export tools
GREP, SEMANTIC_SEARCH = get_tools()
