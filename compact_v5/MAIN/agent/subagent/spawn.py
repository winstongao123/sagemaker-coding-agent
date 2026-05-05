"""V5 subagent/spawn.py — fork-style sub-agent spawn (Phase 9, ADR-015).

ADAPT port of Runnable's `forkSubagent.ts` (210 LOC). v5 adaptation:
- Synchronous (no Promise / async generator chain). Constraint=.ipynb.
- Drops Runnable's experimental fork branch (FORK_SUBAGENT feature gate),
  cache-prefix-identical message replay, and `<task-notification>`
  background dispatch model — those need streaming/async to be useful.
- Drops Runnable's coordinator-mode mutual exclusion (v5 has no coordinator).
- v5's spawn ALWAYS shares the parent's IterationBudget instance — that is
  Hermes's PS Issue #2 contract and the Phase-9 acceptance criterion.
- Drops AGENT_TYPES configuration registry — Phase 9 supports `general` only;
  build/plan/explore/verify agent types are deferred (their large prompts
  are reviewable as data later).
- Includes depth-limit enforcement (v4 sagemaker_agent.py:8354 parity).

PORT_LOG: #021.

Acceptance criteria (V5_PLAN.md §Phase 9):
- Parent context unchanged after sub-agent run.
- Child shares IterationBudget instance.

Usage:
    parent = QueryEngine(client=..., budget=IterationBudget())
    text, child = spawn_subagent(parent, "summarize this codebase", "general")
    # parent.messages is unchanged; child.budget is parent.budget.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple

from .env import build_env_details
from .handoff import build_handoff_block


# Default cap on sub-agent depth. Matches v4 CONFIG.subagent_max_depth=2.
DEFAULT_MAX_DEPTH: int = 2

# Block G — full AGENT_TYPES registry (build / plan / explore / verify /
# general / review / fork) lands as a sibling module. Spawn dispatches via
# get_agent_type for type validation + worktree / skill auto-load.


@dataclass
class SubagentResult:
    """Outcome of `spawn_subagent`. Returned alongside the child engine so
    callers can inspect message buffer / budget / stop reason / turns_used.

    `text`            — final assistant text (the sub-agent's answer).
    `stop_reason`     — same as QueryResult.stop_reason.
    `turns_used`      — turns the child consumed.
    `child_messages`  — the child's full conversation buffer (for audit).
    `error`           — short message when stop_reason indicates failure.
    `agent_type`      — what type was requested.
    `depth`           — depth the child ran at.
    """
    text: str = ""
    stop_reason: str = ""
    turns_used: int = 0
    child_messages: List[Any] = field(default_factory=list)
    error: Optional[str] = None
    agent_type: str = "general"
    depth: int = 1


def _new_child_engine(parent_engine: Any, max_turns: int, agent_type: str = "general") -> Any:
    """Construct a fresh QueryEngine that shares the parent's IterationBudget.

    Lazy-imports to avoid a circular load at module-import time
    (core.query_engine imports tools/registry which may import
    tools/task.py which imports this module).

    Block B: `agent_type` is forwarded as `agent_kind` so TOKENS.add()
    attributes the child's input/output/cost to the right per-agent
    bucket. The child also gets a fresh session_id so AUDIT.log entries
    can be filtered to a single sub-agent run.
    """
    from core.query_engine import QueryEngine
    return QueryEngine(
        client=parent_engine.client,
        max_turns=max_turns,
        budget=parent_engine.budget,            # SHARED — the Phase-9 contract
        on_stop_check=parent_engine.on_stop_check,
        agent_kind=agent_type,
    )


def _resolve_agent_suffix(agent_type: str) -> Optional[str]:
    """Look up the prompt suffix for a known agent type.

    Returns None for unknown types so the caller (spawn_subagent / task tool)
    can surface an explicit error instead of silently falling back. Phase-9
    Codex finding: silent fallback masks contract bugs.

    Block G: now consults the AGENT_TYPES registry (was: tiny dict keyed on
    "general" only). Returns the per-type system_suffix.
    """
    from .agent_types import get_agent_type
    at = get_agent_type(agent_type)
    return at.system_suffix if at is not None else None


def spawn_subagent(
    parent_engine: Any,
    prompt: str,
    agent_type: str = "general",
    parent_depth: int = 0,
    max_turns: int = 25,
    max_depth: int = DEFAULT_MAX_DEPTH,
    base_system_prompt: Optional[str] = None,
    workspace: Optional[str] = None,
    status_path: Optional[str] = None,
    todos_text: Optional[str] = None,
    recent_files: Optional[List[str]] = None,
    plan_mode: bool = False,
    output_fn: Callable[[str], None] = print,
) -> SubagentResult:
    """Spawn a sub-agent with the parent's shared IterationBudget.

    The child gets:
      - A FRESH message buffer (no parent conversation leakage).
      - The parent's BedrockClient, IterationBudget, on_stop_check (shared).
      - A system prompt = base_system_prompt + env_details + handoff_block
        + agent-type suffix, with the cache boundary preserved.

    Returns a `SubagentResult` with the child's final answer + audit info.

    Phase 9 contract (V5_PLAN.md §Phase 9):
      - Parent's `messages` buffer is NOT mutated.
      - Child's `budget is parent_engine.budget` (object identity).
      - Depth-limit enforcement: depth >= max_depth → blocked with error
        result, no Bedrock call made.
    """
    child_depth = parent_depth + 1

    # Depth-limit gate (v4 sagemaker_agent.py:8354 parity).
    if child_depth > max_depth:
        return SubagentResult(
            text="",
            stop_reason="depth_exceeded",
            error=(
                f"Blocked: sub-agent depth limit reached "
                f"({child_depth} > max {max_depth})"
            ),
            agent_type=agent_type,
            depth=child_depth,
        )

    # Validate prompt — empty prompt is a programming error in the caller.
    p = (prompt or "").strip()
    if not p:
        return SubagentResult(
            text="",
            stop_reason="invalid_args",
            error="Error: prompt is required",
            agent_type=agent_type,
            depth=child_depth,
        )

    # Validate agent type. The task tool already gates on this at the
    # dispatch layer, but spawn_subagent is also called directly by Phase
    # 11 UX wiring, so guard here too. Codex Phase-09 finding: don't
    # silently fall back to `general`.
    suffix = _resolve_agent_suffix(agent_type)
    if suffix is None:
        from .agent_types import AGENT_TYPES
        available = ", ".join(sorted(AGENT_TYPES.keys()))
        return SubagentResult(
            text="",
            stop_reason="invalid_args",
            error=(
                f"Error: unknown agent_type '{agent_type}'. "
                f"Block G supports: {available}."
            ),
            agent_type=agent_type,
            depth=child_depth,
        )

    # Block G — resolve the AgentType row for per-type max_turns / worktree
    # / auto_load_skill knobs.
    from .agent_types import get_agent_type
    agent_def = get_agent_type(agent_type)
    if agent_def is not None:
        # Per-type max_turns: caller can override via the max_turns param.
        # Default policy: use the per-type ceiling unless caller passed
        # something smaller (defense in depth — caller knows the task).
        max_turns = min(max_turns, agent_def.max_turns)

    # Assemble the child's system prompt:
    #   <static> [+ env_details + handoff_block + agent_type_suffix in dynamic tail]
    # If base_system_prompt has the boundary marker, inject our extras after it.
    # Otherwise append at the end.
    from prompt import build_system_prompt, CACHE_BOUNDARY

    base = base_system_prompt or build_system_prompt(ctx={})
    env_details = build_env_details(
        agent_type=agent_type,
        depth=child_depth,
        workspace=workspace,
        max_depth=max_depth,
    )
    handoff = build_handoff_block(
        status_path=status_path,
        todos_text=todos_text,
        recent_files=recent_files,
    )

    dynamic_extras = [env_details, handoff, suffix]
    dynamic_extras = [x for x in dynamic_extras if x]

    if dynamic_extras:
        addendum = "\n\n" + "\n\n".join(dynamic_extras)
        if CACHE_BOUNDARY in base:
            # Append after the existing dynamic tail (preserve cached prefix).
            child_prompt = base + addendum
        else:
            # No boundary — append at the end with our own boundary so future
            # cache-block builders see the static/dynamic split.
            child_prompt = base + CACHE_BOUNDARY + addendum
    else:
        child_prompt = base

    # Construct child engine. The shared-budget invariant is enforced by
    # _new_child_engine — verified by test_subagent_shares_iteration_budget.
    child = _new_child_engine(parent_engine, max_turns=max_turns, agent_type=agent_type)

    # Codex Phase-09 finding (BLOCKER): thread the child's depth so that
    # IF the child itself dispatches `task`, the QueryEngine's tool-dispatch
    # context picks up the correct `parent_depth` via
    # `getattr(self, "_subagent_depth", 0)`. Without this line, nested
    # `task` chains all see parent_depth=0 and the recursion guard never
    # fires. Lock test: test_nested_subagent_recursion_blocked_at_max_depth.
    child._subagent_depth = child_depth

    # Snapshot the parent's full message buffer for a defense-in-depth
    # mutation check. Codex Phase-09 finding (medium): the prior version
    # checked only length, so an in-place mutation that preserves length
    # (e.g. modifying messages[i]["content"] of an existing entry) would
    # evade detection. We deep-copy so post-hoc comparison is structural.
    import copy
    parent_msgs_snapshot = copy.deepcopy(parent_engine.messages)

    # Resolve the child's tool pool. Block G iter-2 (Codex finding #2 HIGH):
    # specialized agents (explore/plan/verify/review) get a tool allowlist
    # enforced at spawn — prompt-only "Do NOT edit files" wording was not a
    # contract. When agent_def.allowed_tools is set, child_tools is filtered
    # to that subset; otherwise the full registry is used.
    #
    # Block G iter-3 (Codex iter-2 finding #1 HIGH): do NOT auto-include the
    # `task` tool for restricted agents. Otherwise a read-only explore agent
    # could call task(subagent_type="build") and regain mutating tools via
    # a child — completely bypassing the allowlist contract. Restricted
    # agents are intentionally one-shot leaf-roles; they don't need to
    # spawn further sub-agents.
    # `tool_search` is still safe to include (it just changes which tool
    # schemas are visible; it cannot reach mutators that aren't in the
    # allowlist).
    from tools import all_registered
    child_tools = all_registered()
    if agent_def is not None and agent_def.allowed_tools:
        _allow = set(agent_def.allowed_tools)
        # Block G iter-3: tool_search is harmless (read-only metadata),
        # task is NOT auto-included — restricted agents stay restricted.
        _allow.add("tool_search")
        child_tools = [t for t in child_tools if t.name in _allow]
        logging.debug(
            "[subagent] agent_type=%s tool allowlist (%d tools): %s",
            agent_type, len(child_tools), sorted(t.name for t in child_tools),
        )

    # Block B+ (PORT_LOG #053): save+clear FILE_CACHE main context
    # before the child runs so the child sees a fresh in-context set;
    # restore the parent's set after the child returns. Best-effort —
    # if FILE_CACHE singleton is unavailable, dispatch still proceeds.
    _file_cache_saved = None
    try:
        from runtime.file_cache import FILE_CACHE as _FC
        _file_cache_saved = _FC.save_and_clear_context()
    except Exception:
        pass

    # Block G — worktree spawn for `build` agents. Best-effort; on hard
    # failure, runs in parent dir with a warning.
    _worktree_path: Optional[str] = None
    if agent_def is not None and agent_def.needs_worktree:
        try:
            from .worktree import create_worktree
            from runtime.config import CONFIG as _CFG_W
            _wt_parent = workspace or getattr(_CFG_W, "workspace", os.getcwd())
            _worktree_path, _wt_source = create_worktree(_wt_parent)
            if _worktree_path:
                logging.info(
                    "[subagent] build agent isolated in worktree=%s (source=%s)",
                    _worktree_path, _wt_source,
                )
            else:
                logging.warning(
                    "[subagent] build agent worktree creation failed — "
                    "running in parent cwd."
                )
        except Exception as _wt_exc:
            logging.warning("[subagent] worktree setup raised: %s", _wt_exc)
            _worktree_path = None

    # Block G — verify agent auto-loads the verify skill so its body sits
    # in the child's system prompt as the gate-check checklist.
    if (
        agent_def is not None
        and agent_def.auto_load_skill
        and parent_engine.skill_manager is not None
    ):
        try:
            ok, _msg = parent_engine.skill_manager.activate(agent_def.auto_load_skill)
            if ok:
                # Inject the active skill body into the child's system prompt
                # tail (cannot share parent's skill_manager state directly
                # since child has its own SkillManager surface in v5).
                _skill_body = parent_engine.skill_manager.get_active_skill_prompt(
                    session_id=getattr(parent_engine, "session_id", ""),
                )
                if _skill_body:
                    child_prompt = child_prompt + _skill_body
        except Exception as _sk_exc:
            logging.warning(
                "[subagent] verify-skill auto-load failed: %s", _sk_exc,
            )

    # Block G-1/G-2: per-agent memory prompt for agent types with memory
    # enabled. Keep this best-effort so a corrupt memory file never blocks a
    # subagent from running.
    if agent_def is not None and getattr(agent_def, "memory_scope", None):
        try:
            from .agent_memory import load_agent_memory_prompt
            from runtime.config import CONFIG as _CFG_M

            _memory_workspace = workspace or getattr(_CFG_M, "workspace", os.getcwd())
            child_prompt = (
                child_prompt
                + "\n\n"
                + load_agent_memory_prompt(
                    agent_type=agent_type,
                    scope=agent_def.memory_scope,
                    workspace=_memory_workspace,
                )
            )
        except Exception as _mem_exc:
            logging.warning("[subagent] agent memory load failed: %s", _mem_exc)

    # Block G iter-2 (Codex finding #1 BLOCKER): swap CONFIG.workspace to
    # the worktree path so tools that read `CONFIG.workspace` (bash cwd,
    # security path checks, edit_file allowed-paths) actually run inside
    # the isolated worktree. Restore in finally so the parent sees its
    # original workspace afterward — even if child.run raises.
    _saved_workspace = None
    if _worktree_path:
        try:
            from runtime.config import CONFIG as _CFG_S
            _saved_workspace = _CFG_S.workspace
            _CFG_S.workspace = _worktree_path
            logging.debug(
                "[subagent] swapped CONFIG.workspace=%s -> %s for build agent",
                _saved_workspace, _worktree_path,
            )
        except Exception as _ws_exc:
            logging.warning(
                "[subagent] CONFIG.workspace swap failed: %s", _ws_exc,
            )
            _saved_workspace = None

    try:
        # The child runs synchronously to completion or budget exhaustion.
        result = child.run(
            user_message=p,
            system_prompt=child_prompt,
            tools=child_tools,
            plan_mode=plan_mode,
            output_fn=output_fn,
        )
    finally:
        # Always restore parent's in-context set, even if child raised.
        if _file_cache_saved is not None:
            try:
                from runtime.file_cache import FILE_CACHE as _FC
                _FC.restore_context(_file_cache_saved)
            except Exception:
                pass
        # Block G iter-2 — restore CONFIG.workspace before worktree cleanup
        # so subsequent parent-side tools see the original workspace again.
        if _saved_workspace is not None:
            try:
                from runtime.config import CONFIG as _CFG_S
                _CFG_S.workspace = _saved_workspace
            except Exception:
                pass
        # Block G — worktree cleanup on child completion (or failure).
        # Best-effort; logs but doesn't block.
        if _worktree_path:
            try:
                from .worktree import cleanup_worktree
                cleanup_worktree(_worktree_path)
            except Exception as _wt_cleanup_exc:
                logging.warning(
                    "[subagent] worktree cleanup raised: %s", _wt_cleanup_exc,
                )

    # Defense-in-depth: confirm the parent buffer wasn't mutated. Structural
    # comparison via the deep snapshot — catches in-place edits that preserve
    # length as well as length-changing mutations.
    if parent_engine.messages != parent_msgs_snapshot:
        # This should never happen if the contract holds. Surface a clear
        # error rather than silently corrupt parent state.
        return SubagentResult(
            text=result.text,
            stop_reason="parent_context_mutated",
            error=(
                "Internal error: parent_engine.messages was mutated by "
                "sub-agent dispatch. Phase-9 contract violated."
            ),
            child_messages=result.messages,
            agent_type=agent_type,
            depth=child_depth,
        )

    return SubagentResult(
        text=result.text,
        stop_reason=result.stop_reason,
        turns_used=result.turns_used,
        child_messages=result.messages,
        error=result.error,
        agent_type=agent_type,
        depth=child_depth,
    )
