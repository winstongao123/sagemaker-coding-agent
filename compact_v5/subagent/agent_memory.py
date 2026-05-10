"""Per-agent memory helpers for Block G.

Adapted from Runnable's AgentTool/agentMemory.ts. v5 keeps the same
project/user/local scoping model but implements it as synchronous, local
file reads for the SageMaker notebook runtime.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional


MEMORY_ENTRYPOINT = "MEMORY.md"
AGENT_MEMORY_SCOPES = frozenset({"user", "project", "local"})


def sanitize_agent_type_for_path(agent_type: str) -> str:
    """Return a directory-safe agent type name."""
    value = str(agent_type or "general").replace(":", "-").strip()
    value = re.sub(r"[\\/]+", "-", value)
    value = value.replace("..", "-")
    value = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip(".-")
    return value or "general"


def _resolve(path: str) -> str:
    return os.path.abspath(os.path.normpath(os.path.expanduser(path)))


def _is_relative_to(path: str, root: str) -> bool:
    path_abs = _resolve(path)
    root_abs = _resolve(root)
    try:
        return os.path.commonpath([path_abs, root_abs]) == root_abs
    except ValueError:
        return False


def get_agent_memory_dir(
    agent_type: str,
    scope: str,
    *,
    workspace: Optional[str] = None,
    memory_base: Optional[str] = None,
) -> str:
    """Return the scoped memory directory for an agent type."""
    if scope not in AGENT_MEMORY_SCOPES:
        raise ValueError(f"unknown agent memory scope: {scope!r}")

    dir_name = sanitize_agent_type_for_path(agent_type)
    workspace_root = _resolve(workspace or os.getcwd())
    user_base = _resolve(memory_base or os.path.join(Path.home(), ".claude"))

    if scope == "project":
        root = os.path.join(workspace_root, ".claude", "agent-memory")
    elif scope == "local":
        root = os.path.join(workspace_root, ".claude", "agent-memory-local")
    else:
        root = os.path.join(user_base, "agent-memory")
    return os.path.join(root, dir_name)


def get_agent_memory_entrypoint(
    agent_type: str,
    scope: str,
    *,
    workspace: Optional[str] = None,
    memory_base: Optional[str] = None,
) -> str:
    return os.path.join(
        get_agent_memory_dir(
            agent_type,
            scope,
            workspace=workspace,
            memory_base=memory_base,
        ),
        MEMORY_ENTRYPOINT,
    )


def is_agent_memory_path(
    absolute_path: str,
    *,
    workspace: Optional[str] = None,
    memory_base: Optional[str] = None,
    remote_memory_dir: Optional[str] = None,
) -> bool:
    """Return True iff path is inside a known agent-memory root."""
    if not absolute_path:
        return False
    path_abs = _resolve(absolute_path)
    workspace_root = _resolve(workspace or os.getcwd())
    user_base = _resolve(memory_base or os.path.join(Path.home(), ".claude"))

    roots = [
        os.path.join(user_base, "agent-memory"),
        os.path.join(workspace_root, ".claude", "agent-memory"),
        os.path.join(workspace_root, ".claude", "agent-memory-local"),
    ]
    if remote_memory_dir:
        roots.append(os.path.join(_resolve(remote_memory_dir), "projects"))
    return any(_is_relative_to(path_abs, root) for root in roots)


def load_agent_memory_prompt(
    agent_type: str,
    scope: str,
    *,
    workspace: Optional[str] = None,
    memory_base: Optional[str] = None,
) -> str:
    """Load scoped persistent memory into a subagent prompt appendix."""
    memory_dir = get_agent_memory_dir(
        agent_type,
        scope,
        workspace=workspace,
        memory_base=memory_base,
    )
    os.makedirs(memory_dir, exist_ok=True)
    entrypoint = os.path.join(memory_dir, MEMORY_ENTRYPOINT)
    try:
        content = Path(entrypoint).read_text(encoding="utf-8")
    except OSError:
        content = ""

    if scope == "user":
        scope_note = (
            "Since this memory is user-scope, keep learnings general because "
            "they apply across projects."
        )
    elif scope == "project":
        scope_note = (
            "Since this memory is project-scope, tailor memories to this "
            "repository and its workflow."
        )
    else:
        scope_note = (
            "Since this memory is local-scope, tailor memories to this "
            "project and machine."
        )

    body = content.strip() or (
        f"Your {MEMORY_ENTRYPOINT} is currently empty. When you save new "
        "memories, they will appear here."
    )
    return "\n".join(
        [
            "# Persistent Agent Memory",
            "",
            f"Memory directory: `{memory_dir}`",
            "",
            f"- {scope_note}",
            "- Treat this memory as context. Do not rewrite it unless the user asks.",
            "",
            f"## {MEMORY_ENTRYPOINT}",
            "",
            body,
        ]
    )
