"""Phase 09 unit tests: subagent/env.py — sub-agent env-details builder.

Locks PORT_LOG #022: verbatim port of v4's _build_subagent_env_details.
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


def test_build_env_details_minimum_lines():
    """Without git or workspace, the block must still produce 3 baseline lines."""
    from subagent.env import build_env_details
    out = build_env_details(agent_type="general", depth=1)
    assert "# Sub-agent Environment" in out
    assert "Agent type: general" in out
    assert "Sub-agent depth: 1 (max 2)" in out


def test_build_env_details_with_workspace():
    from subagent.env import build_env_details
    out = build_env_details(agent_type="explore", depth=2, workspace="/tmp/foo")
    assert "Workspace cwd: /tmp/foo" in out
    assert "Sub-agent depth: 2 (max 2)" in out


def test_build_env_details_max_depth_param():
    """max_depth surfaces in the output for the model's awareness."""
    from subagent.env import build_env_details
    out = build_env_details(agent_type="general", depth=3, max_depth=5)
    assert "(max 5)" in out


def test_build_env_details_fail_quiet_on_git_failure(monkeypatch):
    """If git probes raise, the helper produces baseline lines but no git lines.
    Verbatim from v4's contract — sub-agent spawn must not fail on git timeout."""
    from subagent import env as env_mod

    def boom(*a, **kw):
        raise RuntimeError("git fell over")
    monkeypatch.setattr(env_mod, "subprocess", type("M", (), {"run": staticmethod(boom)}))

    out = env_mod.build_env_details(agent_type="general", depth=1)
    assert "Agent type: general" in out
    assert "Git HEAD" not in out
    assert "Git working tree" not in out


def test_build_env_details_under_six_lines():
    """v4 contract: ≤ 6 short lines so smaller models (Haiku 4.5) aren't bloated."""
    from subagent.env import build_env_details
    out = build_env_details(agent_type="general", depth=1, workspace="/tmp")
    line_count = len(out.splitlines())
    assert line_count <= 6, f"env-details produced {line_count} lines, contract is ≤ 6"
