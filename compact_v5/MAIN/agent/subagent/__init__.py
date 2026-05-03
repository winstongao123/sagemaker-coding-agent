"""V5 subagent/ — sub-agent spawn + AGENT_TYPES + worktree (Phase 9 + Block G).

Phase 9 (ADR-015): forkSubagent-style spawn with shared IterationBudget.
Block G (ADR-031): full AGENT_TYPES registry + worktree isolation +
verify-skill auto-load.

Public surface (re-exported below):
- spawn_subagent / SubagentResult — core spawn entry
- AGENT_TYPES / get_agent_type / get_agent_prompt / ONE_SHOT_BUILTIN_AGENT_TYPES
- create_worktree / cleanup_worktree
- build_env_details / build_handoff_block
"""
from __future__ import annotations

from .spawn import spawn_subagent, SubagentResult, DEFAULT_MAX_DEPTH  # noqa: F401
from .agent_types import (  # noqa: F401
    AGENT_TYPES,
    AgentType,
    DEFAULT_AGENT_PROMPT,
    SUBAGENT_NOTES,
    ONE_SHOT_BUILTIN_AGENT_TYPES,
    get_agent_type,
    get_agent_prompt,
)
from .worktree import create_worktree, cleanup_worktree, WORKTREE_SUBDIR  # noqa: F401
from .fork import (  # noqa: F401
    build_forked_messages,
    build_child_message,
    is_in_fork_child,
    cache_prefix_match_length,
    FORK_BOILERPLATE_TAG,
    FORK_PLACEHOLDER_RESULT,
)
from .env import build_env_details  # noqa: F401
from .handoff import build_handoff_block  # noqa: F401
