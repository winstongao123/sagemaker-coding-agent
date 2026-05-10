"""V5 security/high_risk.py — HIGH_RISK_TOOLS frozenset + helper.

Source: compact_v4/MAIN/agent/sagemaker_agent.py:10487.

These are the tools that MUST trigger an approval prompt regardless of
session state — even if the user has clicked "always allow" on the
tool name. Bedrock + ipywidgets approval flow consumes this set when
deciding whether to suppress the prompt.

The set is FROZEN: callers cannot mutate. Adding a tool to the set
requires a code change.
"""
from __future__ import annotations

from typing import FrozenSet


# v4 verbatim: bash + python_exec are subprocess-launching, task is
# sub-agent-spawning, web_fetch is network-egress. All four require
# explicit per-call approval; "always allow" is intentionally NOT
# offered for these in the UI.
HIGH_RISK_TOOLS: FrozenSet[str] = frozenset({
    "bash",
    "python_exec",
    "task",
    "web_fetch",
})


def is_high_risk(tool_name: str) -> bool:
    """Return True if `tool_name` is in HIGH_RISK_TOOLS."""
    return tool_name in HIGH_RISK_TOOLS
