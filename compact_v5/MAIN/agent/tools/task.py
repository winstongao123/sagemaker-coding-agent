"""Phase 9 task tool — sub-agent dispatch (Phase 9, ADR-015).

ADAPT port of:
- gg-claude-code-runnable/src/tools/AgentTool/AgentTool.tsx (1397 LOC) — only the
  tool-shape contract (description + schema + executor signature). Runnable's
  React/Ink UI lives in UI.tsx and is not ported (constraint=.ipynb).
- v4 `_run_task_tool` at sagemaker_agent.py:8350 — the executor logic.

PORT_LOG: #024.

Phase 9 surface — minimal so the v5 .ipynb shape doesn't drag the full
AGENT_TYPES + worktree complexity across the gate:
- subagent_type values: "general" only. Future phases add build/plan/explore/verify.
- No worktree isolation (build agent's git-worktree dance lands in Phase 11).
- No parallel dispatch (Runnable's parallel sub-agent dispatch is async-only).

The tool is marked `should_defer=True` because spawn is low-frequency:
most turns don't need a sub-agent, so the schema is loaded only when the
model calls tool_search after seeing the deferred-tool reminder.

The Phase 7 wiring contract (ADR-013/014) requires the executor to receive
the parent QueryEngine via `context["parent_engine"]` so the child can share
the parent's IterationBudget — see acceptance test
`test_subagent_shares_iteration_budget`.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .registry import build_tool, register


_DESCRIPTION = """Launch a sub-agent for a specific, scoped task.

Sub-agents run with a FRESH conversation but share the parent agent's iteration budget — they cannot collectively exceed the cost ceiling. Use a sub-agent when:
- The task is well-scoped and self-contained (e.g., "summarize this codebase", "find every TODO comment").
- You want to keep the parent's main context clean (the sub-agent's full transcript is not loaded into the parent — only the final answer is returned).
- You need read-only exploration without polluting the parent's file-read history.

Do NOT use a sub-agent when:
- The task is small enough to do directly in the current turn.
- The result must be incrementally visible to the user (sub-agent runs to completion before returning).
- You need persistent state across multiple top-level requests (sub-agents are one-shot).

Inputs:
- description: 1-line summary shown to the user.
- prompt: the actual task description for the sub-agent. Be specific.
- subagent_type: "general" (default; full tool access). Other types are reserved for future phases.

Returns the sub-agent's final answer as a string. If the sub-agent hits its iteration budget or max_turns, the partial work + reason is returned."""


_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "description": {
            "type": "string",
            "description": "1-line summary of what the sub-agent will do (for display only).",
        },
        "prompt": {
            "type": "string",
            "description": "Full task description sent to the sub-agent. Be specific — the sub-agent has no parent context unless you brief it.",
        },
        "subagent_type": {
            "type": "string",
            "description": "Agent type. 'general' (default) for full tool access. Other types reserved for future phases.",
        },
    },
    "required": ["prompt"],
}


def _task_executor(args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    """Spawn a sub-agent and return its final answer.

    Required context (Phase 9 contract):
      - context["parent_engine"]: the parent QueryEngine. Used to (a) share
        IterationBudget, (b) reuse the BedrockClient, (c) inherit on_stop_check.
        If absent, the executor returns an Error: the model can read.
      - context["parent_depth"] (optional, default 0): the parent's depth.
        Used to enforce the recursion-depth limit.
    """
    description = str(args.get("description", "")).strip()
    prompt = str(args.get("prompt", "")).strip()
    if not prompt:
        return "Error: prompt is required and must be a non-empty string"
    subagent_type = str(args.get("subagent_type", "general")).strip() or "general"

    # Codex Phase-09 finding (medium): Phase-9 supports `general` only.
    # Silently falling back to general for unknown types hides caller/model
    # errors and diverges from v4's explicit-unknown-type contract
    # (compact_v4/MAIN/agent/sagemaker_agent.py:8366). Reject unknowns so
    # the model can self-correct via tool_search before retrying.
    from subagent.spawn import _AGENT_TYPE_SUFFIXES
    if subagent_type not in _AGENT_TYPE_SUFFIXES:
        available = ", ".join(sorted(_AGENT_TYPE_SUFFIXES.keys()))
        return (
            f"Error: unknown subagent_type '{subagent_type}'. "
            f"Phase-9 supports: {available}. "
            "(build/plan/explore/verify types reserved for later phases.)"
        )

    if not isinstance(context, dict) or "parent_engine" not in context:
        return (
            "Error: task tool requires `context['parent_engine']` to spawn a "
            "sub-agent (Phase 9 contract). The query_engine should pass this "
            "via the tool dispatch context."
        )
    parent_engine = context["parent_engine"]
    parent_depth = int(context.get("parent_depth", 0))

    # Lazy-import to avoid circular import: subagent.spawn imports
    # core.query_engine which (via tools/__init__.py:bootstrap_built_ins)
    # imports this module.
    from subagent.spawn import spawn_subagent

    result = spawn_subagent(
        parent_engine=parent_engine,
        prompt=prompt,
        agent_type=subagent_type,
        parent_depth=parent_depth,
        plan_mode=bool(context.get("plan_mode", False)),
    )

    if result.error and result.stop_reason in ("depth_exceeded", "invalid_args"):
        return result.error
    if result.stop_reason in ("budget_exhausted", "max_turns", "context_overflow"):
        # Surface partial work + reason so the parent can react.
        return (
            f"[Sub-agent stopped: {result.stop_reason}]\n"
            f"{result.text or '(no partial output)'}"
        )
    return result.text or "(sub-agent returned no text)"


def _register():
    """Idempotent registration. Called by tools/__init__.py:bootstrap_built_ins."""
    from .registry import find_tool_by_name, all_registered, unregister
    if find_tool_by_name(all_registered(), "task") is not None:
        return  # already registered

    register(build_tool(
        name="task",
        description=_DESCRIPTION,
        input_schema=_INPUT_SCHEMA,
        execute=_task_executor,
        is_read_only=False,         # children may write — fail-closed default
        is_destructive=False,
        is_concurrency_safe=False,  # parallel sub-agents land later
        requires_approval=False,    # the *child* approval gates fire on its tool calls
        should_defer=True,          # low-frequency; deferred via Phase 7
        always_load=False,
        search_hint="sub-agent fork delegate spawn task launch background",
    ))
