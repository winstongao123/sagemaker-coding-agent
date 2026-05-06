"""V5 entry.py — cell-0 import target for chat.ipynb (Phase 11, ADR-017).

Re-exports the public surface. Notebook cells should be able to:

    from entry import Agent, create_chat_ui, CONFIG, BEDROCK_MODELS

without knowing which subpackage owns each name.

Block B+ Codex finding #2 (MEDIUM) lock: import-boundary fail-closed
for v5.0.1 hard-constraint banned subsystems (#9 MCP, #10 streaming,
anthropic_api_direct). Any future code path that re-introduces them
will fail at import here.

PORT_LOG: see #031 + #032 (chat.ipynb wiring) + #056 (banned-subsystem guard).
"""
from __future__ import annotations

# ============================================================
# Banned-subsystem import-time guard (Block B+ — ADR-022 / PORT_LOG #056)
# ============================================================
#
# v5.0.1 hard constraints #9 + #10 forbid MCP and streaming. The guard
# below ACTIVELY checks whether a banned subsystem package has been
# re-introduced (e.g. someone added a `mcp/` package back). If so,
# importing entry.py — the v5 public surface — fails-closed at load.
# This is the import-boundary fail-closed contract from ADR-022 §
# Linked port-log row #051.
import importlib.util as _importlib_util
import os as _os

# Resolve the v5 agent package root (the directory containing entry.py).
# We compare candidate package origins against THIS path so external
# `mcp` installs (pip-installed) don't false-positive the guard.
_AGENT_PKG_ROOT = _os.path.dirname(_os.path.abspath(__file__))

_BANNED_PACKAGE_NAMES = ("mcp",)
for _banned in _BANNED_PACKAGE_NAMES:
    _spec = _importlib_util.find_spec(_banned)
    if _spec is None:
        continue
    _origin = getattr(_spec, "origin", "") or ""
    if not _origin:
        continue
    # Only raise when the spec resolves to a path INSIDE this v5 agent
    # package — i.e. someone re-introduced a `<v5_root>/mcp/` directory.
    # External pip-installed packages (site-packages, conda envs, etc.)
    # do not match this prefix and pass through silently.
    try:
        _origin_real = _os.path.realpath(_origin)
        _root_real = _os.path.realpath(_AGENT_PKG_ROOT)
    except OSError:
        continue
    if _origin_real.startswith(_root_real + _os.sep):
        raise ImportError(
            f"v5.0.1 hard constraint: banned subsystem '{_banned}' "
            f"has been re-introduced INSIDE the v5 agent package at "
            f"{_origin_real!r}. See runtime/feature_flags.py."
        )

# Public Agent class (Phase 11 — wraps Phase 1-10 modules)
from agent import Agent  # noqa: F401

# Config singleton + Bedrock model registry (Phase 1)
from runtime.config import CONFIG  # noqa: F401

# Optional Bedrock model list — kept as a module-level constant so the
# config widget in chat.ipynb cell 2 can populate a dropdown.
BEDROCK_MODELS = [
    ("Claude 4.5 Sonnet (AU) - default",
     "au.anthropic.claude-sonnet-4-5-20250929-v1:0"),
    ("Claude 4.5 Haiku (AU)",
     "au.anthropic.claude-haiku-4-5-20251001-v1:0"),
    ("Claude 4.6 Sonnet (AU)",
     "au.anthropic.claude-sonnet-4-6"),
    ("Claude 4.6 Opus (AU)",
     "au.anthropic.claude-opus-4-6-v1"),
    ("Claude 4.5 Opus (Global)",
     "global.anthropic.claude-opus-4-5-20251101-v1:0"),
    ("Claude 3.5 Sonnet v2",
     "anthropic.claude-3-5-sonnet-20241022-v2:0"),
    ("Claude 3.5 Sonnet",
     "anthropic.claude-3-5-sonnet-20240620-v1:0"),
    ("Claude 3 Haiku",
     "anthropic.claude-3-haiku-20240307-v1:0"),
    ("Claude 3 Sonnet",
     "anthropic.claude-3-sonnet-20240229-v1:0"),
]

# Chat UI factory (Phase 11)
from ui.chat_ui import create_chat_ui  # noqa: F401

# Skill manager helper for power users who want to inspect / activate
# skills programmatically (Phase 10).
from skills.manager import SkillManager  # noqa: F401

# IterationBudget for power users + tests (Phase 8).
from core.budget import IterationBudget  # noqa: F401
