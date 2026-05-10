"""V5 agent package init — re-export Agent from agent.py.

Block J ship-gate fix (2026-05-03): the Agent class previously lived
in this __init__.py, but `entry.py` imports `from agent import Agent`
which fails in the FLAT ship-zip layout because there's no module
named `agent` (just an `__init__.py` at root, which is not visible by
that name).

Fix: Agent class moved to a real `agent.py` module. This __init__.py
re-exports it via the relative import `from .agent import Agent` so
the source-layout `MAIN/agent/` package still works AND the flat-zip
layout (where `agent.py` sits at root next to `entry.py`) works too:

  - Source layout (test-time): pytest puts `MAIN/agent` on sys.path.
    `from agent import Agent` finds `MAIN/agent/agent.py` directly.
    No package __init__ is involved on this path.
  - Flat-zip layout: `agent.py` is at root next to `__init__.py`.
    `from agent import Agent` finds `agent.py` directly. __init__.py
    is irrelevant in this mode.

  Codex Block J iter-1 LOW: importing `agent` AS A PACKAGE with only
  `MAIN` on sys.path will run THIS __init__.py, but `agent.py` itself
  uses absolute imports (`from core ...`, `from tools ...`, etc.) that
  require `MAIN/agent` on sys.path too. So the package-import mode
  works only when BOTH `MAIN` and `MAIN/agent` are on path, which is
  exactly the pytest scenario. The flat-zip and source-layout direct
  contracts that actually ship are both fine; package-only-import
  from MAIN is explicitly out-of-contract and not a regression.

PORT_LOG: see #031 (original) + Block J ship-gate row.
"""
from __future__ import annotations

# Relative import — `.agent` resolves to the sibling `agent.py` submodule
# inside this package, NOT the package itself. This avoids the
# self-import circular that bare `from agent import Agent` would cause.
from .agent import Agent, _load_agent_status_text  # noqa: F401

__all__ = ["Agent"]
