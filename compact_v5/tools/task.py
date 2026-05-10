"""Phase 9 task tool — sub-agent dispatch (Phase 9, ADR-015).

ADAPT port of:
- gg-claude-code-runnable/src/tools/AgentTool/AgentTool.tsx (1397 LOC) — only the
  tool-shape contract (description + schema + executor signature). Runnable's
  React/Ink UI lives in UI.tsx and is not ported (constraint=.ipynb).
- v4 `_run_task_tool` at sagemaker_agent.py:8350 — the executor logic.

PORT_LOG: #024.

Current v5 surface:
- subagent_type values: general, explore, plan, verify, build, review, fork.
- build agents use best-effort isolated git worktrees.
- task dispatch is synchronous in the parent loop; child output is forwarded
  live through output_fn so the notebook UI can show sub-agent progress while
  the tool is running.

The tool is visible by default in v5.0.1+ software-engineering builds. The
PS_PS v3 acceptance run showed that hiding `task` behind tool_search lets
small models finish long coding work without ever dispatching a reviewer.
The schema is small enough to keep loaded, and the tool remains guarded by
the shared budget, depth limit, per-role allowlists, and reviewer receipts.

The Phase 7 wiring contract (ADR-013/014) requires the executor to receive
the parent QueryEngine via `context["parent_engine"]` so the child can share
the parent's IterationBudget — see acceptance test
`test_subagent_shares_iteration_budget`.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, Optional

from .registry import build_tool, register


_DESCRIPTION = """Launch a sub-agent for a specific, scoped task.

IMPORTANT: if the user explicitly asks for a worker, reviewer, verifier,
helper, subagent, independent review, or saved review evidence, you must use
this tool. A self-written review document is not a substitute for a real
sub-agent result.

Sub-agents run with a FRESH conversation but share the parent agent's iteration budget — they cannot collectively exceed the cost ceiling. Use a sub-agent when:
- The task is well-scoped and self-contained (e.g., "summarize this codebase", "find every TODO comment").
- You want to keep the parent's main context clean (the sub-agent's full transcript is not loaded into the parent — only the final answer is returned).
- You need read-only exploration without polluting the parent's file-read history.

Do NOT use a sub-agent when:
- The task is small enough to do directly in the current turn.
- The next local action depends immediately on the answer and waiting would block the critical path.
- You need persistent state across multiple top-level requests (sub-agents are one-shot).

Inputs:
- description: 1-line summary shown to the user.
- prompt: the actual task description for the sub-agent. Be specific.
- subagent_type: one of `general` | `explore` | `plan` | `verify` | `build` | `review` | `fork` (default `general`).
  - `general` — full tool access; default.
  - `explore` — read-only exploration (no edit/write/exec); produces a report.
  - `plan` — read-only planning (no edit/write/exec); produces a step-by-step plan.
  - `verify` — read + bash; auto-loads the `verify` skill; runs gate checks.
  - `build` — full tools, runs in isolated git worktree.
  - `review` — read-only code review; surfaces concrete issues with file:line.
  - `fork` — inherits parent context conceptually; full tools.

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
            "enum": ["general", "explore", "plan", "verify", "build", "review", "fork"],
            "default": "general",
            "description": "Agent type. general (default; full tools) | explore (read-only) | plan (read-only) | verify (read + bash + auto-loads verify skill) | build (full + isolated git worktree) | review (read-only code review) | fork (full tools, parent-context).",
        },
    },
    "required": ["prompt"],
}


def _safe_slug(value: str, default: str = "subagent") -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", (value or "").strip()).strip("-._")
    return slug[:80] or default


def _atomic_write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def _subagent_receipt_markdown(
    *,
    result: Any,
    envelope: Dict[str, Any],
    description: str,
    prompt: str,
) -> str:
    prompt_preview = prompt.strip()
    if len(prompt_preview) > 2000:
        prompt_preview = prompt_preview[:2000] + "\n...[truncated]"
    return (
        f"# Subagent Receipt: {getattr(result, 'agent_type', 'subagent')}\n\n"
        f"Created: {datetime.utcnow().replace(microsecond=0).isoformat()}Z\n\n"
        f"Description: {description or '(none)'}\n\n"
        "## Prompt Preview\n\n"
        "```text\n"
        f"{prompt_preview}\n"
        "```\n\n"
        "## Result Text\n\n"
        "```text\n"
        f"{result.text or '(no text)'}\n"
        "```\n\n"
        "## Envelope\n\n"
        "```json\n"
        f"{json.dumps(envelope, indent=2, sort_keys=True)}\n"
        "```\n"
    )


def _persist_subagent_receipts(
    *,
    result: Any,
    envelope: Dict[str, Any],
    description: str,
    prompt: str,
) -> list[str]:
    """Persist subagent receipts so long software tasks keep review evidence.

    Always write under `.sageagent_state/subagents` when a workspace is known.
    Also write under `docs/reviews/` and `docs/logs/`. These human-visible
    receipts are required by the PS_PS final acceptance tests and prevent early
    helper runs from disappearing before the project docs tree exists.
    """
    try:
        from runtime.config import CONFIG
        workspace = os.path.abspath(str(getattr(CONFIG, "workspace", "") or os.getcwd()))
    except Exception:
        workspace = os.path.abspath(os.getcwd())
    if not workspace:
        return []

    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    child = _safe_slug(str(getattr(result, "child_session_id", "") or "child"))
    kind = _safe_slug(str(getattr(result, "agent_type", "") or "subagent"))
    filename = f"{stamp}-{kind}-{child}.md"
    receipt = _subagent_receipt_markdown(
        result=result,
        envelope=envelope,
        description=description,
        prompt=prompt,
    )

    paths: list[str] = []
    state_path = os.path.join(workspace, ".sageagent_state", "subagents", filename)
    try:
        _atomic_write_text(state_path, receipt)
        paths.append(state_path)
    except Exception:
        pass

    docs_dir = os.path.join(workspace, "docs")
    review_path = os.path.join(docs_dir, "reviews", filename)
    try:
        _atomic_write_text(review_path, receipt)
        paths.append(review_path)
    except Exception:
        pass
    log_path = os.path.join(docs_dir, "logs", "subagent_artifacts.log")
    try:
        existing = ""
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                existing = f.read()
        line = (
            f"{stamp} agent_type={kind} child_session_id={child} "
            f"review_artifact={review_path}\n"
        )
        _atomic_write_text(log_path, existing + line)
    except Exception:
        pass
    return paths


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

    # Codex Phase-09 finding (medium): silently falling back to general for
    # unknown types hides caller/model errors. v4's explicit-unknown-type
    # contract (sagemaker_agent.py:8366) is preserved here.
    # Block G: validation now consults the full AGENT_TYPES registry
    # (build / plan / explore / verify / general / review / fork) — was
    # the Phase-9 single-entry _AGENT_TYPE_SUFFIXES dict.
    from subagent.agent_types import AGENT_TYPES
    if subagent_type not in AGENT_TYPES:
        available = ", ".join(sorted(AGENT_TYPES.keys()))
        return (
            f"Error: unknown subagent_type '{subagent_type}'. "
            f"Block G supports: {available}."
        )

    if not isinstance(context, dict) or "parent_engine" not in context:
        return (
            "Error: task tool requires `context['parent_engine']` to spawn a "
            "sub-agent (Phase 9 contract). The query_engine should pass this "
            "via the tool dispatch context."
        )
    parent_engine = context["parent_engine"]
    parent_depth = int(context.get("parent_depth", 0))
    try:
        from runtime.config import CONFIG
        subagent_model = str(
            ((getattr(CONFIG, "agent_overrides", {}) or {}).get(subagent_type, {}) or {}).get("model", "")
            or ""
        )
    except Exception:
        subagent_model = ""
    output_fn = print
    if isinstance(context, dict) and callable(context.get("output_fn")):
        output_fn = context["output_fn"]

    # Lazy-import to avoid circular import: subagent.spawn imports
    # core.query_engine which (via tools/__init__.py:bootstrap_built_ins)
    # imports this module.
    from subagent.spawn import spawn_subagent

    summary = description or prompt.replace("\n", " ")[:120]
    child_output_count = 0

    def _subagent_output(text: str) -> None:
        nonlocal child_output_count
        child_output_count += 1
        output_fn(f"[subagent:{subagent_type}:child] {text}")

    output_fn(f"[subagent:{subagent_type}] started: {summary}")
    result = spawn_subagent(
        parent_engine=parent_engine,
        prompt=prompt,
        agent_type=subagent_type,
        parent_depth=parent_depth,
        model_id=subagent_model or None,
        plan_mode=bool(context.get("plan_mode", False)),
        output_fn=_subagent_output,
    )
    token_delta = result.token_delta or {}
    output_fn(
        "[subagent:{kind}] finished: stop={stop} turns={turns} "
        "cost=${cost:.4f} cache={cache_read:,}/{cache_write:,}".format(
            kind=subagent_type,
            stop=result.stop_reason or "unknown",
            turns=int(getattr(result, "turns_used", 0) or 0),
            cost=float(token_delta.get("cost_usd", 0.0) or 0.0),
            cache_read=int(token_delta.get("cache_read_tokens", 0) or 0),
            cache_write=int(token_delta.get("cache_write_tokens", 0) or 0),
        )
    )
    if child_output_count:
        output_fn(f"[subagent:{subagent_type}] streamed child updates={child_output_count}")

    envelope_data = result.to_envelope()
    artifact_paths = _persist_subagent_receipts(
        result=result,
        envelope=envelope_data,
        description=description,
        prompt=prompt,
    )
    if artifact_paths:
        envelope_data["artifact_paths"] = list(artifact_paths)
    envelope = json.dumps(envelope_data, indent=2, sort_keys=True)
    envelope_block = f"\n\n[subagent_result_envelope]\n{envelope}"
    artifact_block = ""
    if artifact_paths:
        artifact_block = "\n\n[subagent_artifacts]\n" + "\n".join(artifact_paths)
    try:
        from runtime.audit import AUDIT as _AUDIT
        _AUDIT.log(
            session_id=str(context.get("session_id", "")) if isinstance(context, dict) else "",
            action="subagent_result",
            tool_name="task",
            parameters={
                "subagent_type": subagent_type,
                "model_id": subagent_model or getattr(
                    getattr(parent_engine, "client", None),
                    "model_id",
                    "",
                ),
                "description": description,
                "child_session_id": result.child_session_id,
            },
            result_summary=json.dumps(result.to_envelope(), sort_keys=True)[:500],
            user_approved=True,
        )
    except Exception:
        pass

    if result.error and result.stop_reason in ("depth_exceeded", "invalid_args"):
        return result.error + envelope_block + artifact_block
    if result.stop_reason in ("budget_exhausted", "max_turns", "context_overflow"):
        # Surface partial work + reason so the parent can react.
        return (
            f"[Sub-agent stopped: {result.stop_reason}]\n"
            f"{result.text or '(no partial output)'}"
            f"{envelope_block}"
            f"{artifact_block}"
        )
    return (result.text or "(sub-agent returned no text)") + envelope_block + artifact_block


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
        should_defer=False,         # supervisor/reviewer work must be discoverable
        always_load=True,
        search_hint="sub-agent fork delegate spawn task launch background",
    ))
