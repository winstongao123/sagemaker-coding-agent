"""V5 subagent/env.py — fresh sub-agent env-details block (Phase 9, ADR-015).

Verbatim port of v4's `_build_subagent_env_details` at
`compact_v4/MAIN/agent/sagemaker_agent.py:7695`. Phase-9 v5 adaptation:
- workspace is a function parameter (not a global) so unit tests can drive it.
- max_depth is a function parameter (not a CONFIG attribute) so callers in
  Phase 11 UX can override per-call.

PORT_LOG: #022.

Output is bounded to ≤ 6 short lines so it does not bloat the prompt for
smaller models (Haiku 4.5). Git probes are fail-quiet — any error or
timeout yields no line for that detail rather than raising.
"""
from __future__ import annotations

import subprocess
from typing import Optional


# Codex Phase-09 finding (DRIFTED): v4 uses 5.0s
# (compact_v4/MAIN/agent/sagemaker_agent.py:7692). Phase 9 v5 must keep
# the same value to qualify as a verbatim PORT.
_GIT_TIMEOUT_S: float = 5.0


def build_env_details(
    agent_type: str,
    depth: int,
    workspace: Optional[str] = None,
    max_depth: int = 2,
) -> str:
    """Build a concise env-details block for a fresh sub-agent.

    Args:
        agent_type: e.g. 'general' / 'build' / 'plan' / 'explore' / 'verify'.
        depth: this child's depth (1 for first sub-agent, 2 for grandchild).
        workspace: working directory; if None, git probes use the current cwd.
        max_depth: hard cap surfaced in the env-details for the model's awareness.
    """
    lines = ["# Sub-agent Environment"]
    lines.append(f"- Agent type: {agent_type}")
    lines.append(f"- Sub-agent depth: {depth} (max {max_depth})")
    if workspace:
        lines.append(f"- Workspace cwd: {workspace}")

    # git HEAD (short SHA) — fail-quiet
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True,
            timeout=_GIT_TIMEOUT_S,
            cwd=workspace or None,
        )
        if r.returncode == 0 and r.stdout.strip():
            lines.append(f"- Git HEAD: {r.stdout.strip()}")
    except Exception:
        pass

    # git working-tree summary — fail-quiet
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True,
            timeout=_GIT_TIMEOUT_S,
            cwd=workspace or None,
        )
        if r.returncode == 0:
            changed = [ln for ln in r.stdout.splitlines() if ln.strip()]
            lines.append(
                f"- Git working tree: {len(changed)} changed file(s)" if changed
                else "- Git working tree: clean"
            )
    except Exception:
        pass

    return "\n".join(lines)
