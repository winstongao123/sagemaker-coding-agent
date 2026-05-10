"""V5 subagent/agent_types.py — Block G AGENT_TYPES registry.

PORT_LOG: #086.

Source:
- v4 sagemaker_agent.py:6914-7090 (~176 LOC original AGENT_TYPES dict)
- Runnable AgentTool/constants.ts (ONE_SHOT_BUILTIN_AGENT_TYPES)
- Runnable AgentTool/prompt.ts (DEFAULT_AGENT_PROMPT phrasing)

Each agent type is one row with:
- system_suffix: a per-agent prompt suffix appended to the base system
  prompt. Sets task-shape expectations.
- max_turns: ceiling on the sub-agent's turn count (independent of the
  shared IterationBudget, which is the cost-cap; max_turns is the
  task-scope-cap).
- one_shot: True for Explore/Plan/Verify-style agents that produce a
  single report and don't accept follow-up; matches Runnable's
  ONE_SHOT_BUILTIN_AGENT_TYPES (constants.ts:9-12). One-shot agents
  skip the agentId/SendMessage/usage trailer in their system prompt
  to save tokens.
- auto_load_skill: optional skill name to auto-activate in the child's
  SkillManager before run(). Used by `verify` to load skills/verify/
  for the verification gate-checks.
- needs_worktree: True for `build` — spawns the child in an isolated
  git worktree so concurrent build agents don't clobber each other.
  v4 sagemaker_agent.py:8413+ (~57 LOC).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# Block G-6: DEFAULT_AGENT_PROMPT verbatim (Runnable constants/prompts.ts:758).
# Battle-tested wording: tells sub-agents NOT to gold-plate; the parent
# only needs the answer, not surrounding cleanup. Keeps token cost
# predictable for cheap fanout patterns (Explore + Plan).
DEFAULT_AGENT_PROMPT = (
    "You are a sub-agent working on a focused task. Always use ABSOLUTE "
    "file paths (cwd may reset between bash calls). In your final "
    "response, share relevant file paths and key findings. Be concise — "
    "the parent will read your full reply. Do NOT add features, "
    "refactor, or introduce abstractions beyond what the task requires."
)


# Block G-7: "Notes" appendix to subagent system prompt
# (Runnable constants/prompts.ts:766-770). Each line fixes a real
# failure mode in the wild.
SUBAGENT_NOTES = (
    "\n\nNotes:\n"
    "- Always include a short description of what you'll do before tool calls.\n"
    "- When you launch multiple research tasks, run them in parallel.\n"
    "- The parent notebook UI can see lifecycle updates and forwarded child "
    "output while you run, but your final reply is still the durable handoff. "
    "Surface findings explicitly in your reply."
)


@dataclass(frozen=True)
class AgentType:
    name: str
    system_suffix: str
    max_turns: int = 25
    one_shot: bool = False
    auto_load_skill: Optional[str] = None
    needs_worktree: bool = False
    memory_scope: Optional[str] = None
    # Block G iter-2 (Codex finding #2 HIGH): allowed_tools allowlist enforced
    # at spawn time (was: prompt-only "Do NOT edit files" wording, which the
    # model could ignore). When None, the child gets the full registry.
    # When set, child_tools is filtered to this list before child.run.
    allowed_tools: Optional[tuple] = None  # tuple for frozen-dataclass safety


# Read-only tool allowlist for explore / plan / review. These agents must not
# mutate files, execute shell commands, or mutate parent task/todo state.
# semantic_search is included because it is read-only.
_READ_ONLY_TOOLS: tuple = (
    "read_file", "grep", "glob", "list_dir", "view_image",
    "todo_read", "semantic_search", "ask_user",
)
# Verify allowlist: read-only + bash (so verify can run pytest / lint /
# build commands). NO edit/write tools.
_VERIFY_TOOLS: tuple = _READ_ONLY_TOOLS + ("bash", "python_exec")


# Block G-1: AGENT_TYPES dict — 7 entries per TEST_DESIGN test_agent_types_dict_has_7.
# Names match v4 + Runnable conventions.
AGENT_TYPES: dict = {
    "general": AgentType(
        name="general",
        system_suffix=DEFAULT_AGENT_PROMPT + SUBAGENT_NOTES,
    ),
    "explore": AgentType(
        name="explore",
        system_suffix=(
            DEFAULT_AGENT_PROMPT
            + "\n\nFocus: read-only exploration. Use Read, Grep, Glob to "
            "understand the codebase. Do NOT edit files. Return a concise "
            "summary with file:line references for key findings."
            + SUBAGENT_NOTES
        ),
        max_turns=20,
        one_shot=True,  # Block G-3: ONE_SHOT_BUILTIN_AGENT_TYPES
        allowed_tools=_READ_ONLY_TOOLS,
    ),
    "plan": AgentType(
        name="plan",
        system_suffix=(
            DEFAULT_AGENT_PROMPT
            + "\n\nFocus: produce an implementation plan. Read code as "
            "needed (Read, Grep, Glob). Do NOT write code. Return a "
            "step-by-step plan with file paths and what to change."
            + SUBAGENT_NOTES
        ),
        max_turns=15,
        one_shot=True,
        allowed_tools=_READ_ONLY_TOOLS,
    ),
    "verify": AgentType(
        name="verify",
        system_suffix=(
            DEFAULT_AGENT_PROMPT
            + "\n\nFocus: run verification gates. Use the loaded `verify` "
            "skill body for the exact checklist. Report PASS/FAIL per gate "
            "and a single overall verdict at the end."
            + SUBAGENT_NOTES
        ),
        max_turns=20,
        one_shot=True,
        auto_load_skill="verify",  # Block G — TEST_DESIGN row 3
        allowed_tools=_VERIFY_TOOLS,  # read-only + bash + python_exec
    ),
    "build": AgentType(
        name="build",
        system_suffix=(
            DEFAULT_AGENT_PROMPT
            + "\n\nFocus: implement the requested change. You are running "
            "inside an isolated git worktree, so file edits won't affect "
            "the parent's working tree until the parent merges. Run tests "
            "before declaring done."
            + SUBAGENT_NOTES
        ),
        max_turns=40,
        needs_worktree=True,  # Block G — TEST_DESIGN row 2
    ),
    "review": AgentType(
        name="review",
        system_suffix=(
            DEFAULT_AGENT_PROMPT
            + "\n\nFocus: code review. Read the diff or files at the cited "
            "paths and report concrete issues with file:line. Avoid "
            "praise — surface bugs, security risks, and unclear semantics."
            + SUBAGENT_NOTES
        ),
        max_turns=20,
        one_shot=True,
        allowed_tools=_READ_ONLY_TOOLS,
        memory_scope="project",
    ),
    "fork": AgentType(
        name="fork",
        system_suffix=(
            DEFAULT_AGENT_PROMPT
            + "\n\nFocus: continue the parent's task in a forked context. "
            "You inherit the parent's full conversation. Pick up where "
            "the parent left off and complete the task."
            + SUBAGENT_NOTES
        ),
        max_turns=50,
    ),
}


# Block G-3: Runnable's ONE_SHOT_BUILTIN_AGENT_TYPES set.
# (Computed from AGENT_TYPES so they stay in sync.)
ONE_SHOT_BUILTIN_AGENT_TYPES = frozenset(
    name for name, t in AGENT_TYPES.items() if t.one_shot
)


def get_agent_type(name: str) -> Optional[AgentType]:
    """Look up an AgentType by name. Returns None for unknown names so
    the caller (spawn_subagent) can surface a clear error rather than
    silently falling back to general."""
    return AGENT_TYPES.get(name)


def get_agent_prompt(name: str, is_coordinator: bool = False) -> str:
    """Block G-4 (Runnable AgentTool/prompt.ts:202-213): coordinators get
    a slim prompt, non-coordinators get the full system_suffix.

    For v5, the slim prompt is the suffix without the Notes appendix
    (the coordinator system prompt covers usage notes itself, per Block
    G3 ADR). When is_coordinator=False, returns the full suffix
    including Notes.
    """
    agent = AGENT_TYPES.get(name)
    if agent is None:
        return DEFAULT_AGENT_PROMPT + SUBAGENT_NOTES
    if is_coordinator:
        # Slim: drop Notes appendix.
        return agent.system_suffix.replace(SUBAGENT_NOTES, "")
    return agent.system_suffix
