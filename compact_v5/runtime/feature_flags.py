"""Block B+ — feature flags + import-boundary fail-closed (ADR-020 0-9 remap).

Adapter of Runnable's entry.ts:1-17 (R11 N23) — when a banned module is
queried, the helper returns False so any code branch that gates
`if feature_enabled("X"):` short-circuits. Used to guarantee that v5
never accidentally imports the dropped subsystems (MCP servers,
streaming Bedrock, Anthropic-direct paths).

Per v5.0.1 hard constraints:
  #9 — drop MCP entirely (single-user SageMaker; no remote tool servers)
  #10 — drop streaming (SageMaker UI cannot stream)

PORT_LOG: see #051.
"""
from __future__ import annotations

import logging
import os
from typing import Dict


# Hard-banned features. `feature_enabled("mcp")` returns False even if
# an env var asks for it; the only way to flip these on would be to
# edit this file (which the build process would catch).
_BANNED_FEATURES = frozenset({
    "mcp",                    # constraint #9
    "streaming",              # constraint #10
    "anthropic_api_direct",   # we run on Bedrock only
})


# Soft-toggleable features. Off by default; can be flipped via env.
_SOFT_FEATURES: Dict[str, bool] = {
    "skill_patching": False,           # opt-in self-patching skills
    "skill_auto_trigger": False,       # v4.9.6 default-OFF
    "memory_extraction": False,        # Block H lands this
}


def feature_enabled(name: str) -> bool:
    """Return True iff `name` is a soft feature that's currently enabled.

    Banned features always return False, regardless of any override.
    Unknown names also return False (fail-closed) so a typo never
    accidentally activates a feature.
    """
    if name in _BANNED_FEATURES:
        return False
    if name not in _SOFT_FEATURES:
        return False
    # Env override: SAGEMAKER_AGENT_FEATURE_<NAME>=1 / 0 / true / false.
    env_key = f"SAGEMAKER_AGENT_FEATURE_{name.upper()}"
    raw = os.environ.get(env_key)
    if raw is not None:
        if raw.strip().lower() in {"1", "true", "yes", "on"}:
            return True
        if raw.strip().lower() in {"0", "false", "no", "off"}:
            return False
        logging.warning(
            f"feature_flags: {env_key}={raw!r} not recognised; ignoring"
        )
    return _SOFT_FEATURES[name]


def is_banned(name: str) -> bool:
    """Public helper to assert a name is in the banned set."""
    return name in _BANNED_FEATURES


def assert_not_banned(name: str) -> None:
    """Raise ImportError if a caller tries to import a banned subsystem.

    Used by `__init__.py` import guards in modules that must never be
    loaded (e.g. a reintroduced `mcp/` package). Caller-style:

        from runtime.feature_flags import assert_not_banned
        assert_not_banned("mcp")  # raises if anyone re-adds MCP support
    """
    if name in _BANNED_FEATURES:
        raise ImportError(
            f"feature '{name}' is banned by v5.0.1 hard constraint; "
            f"this module must not be importable."
        )


__all__ = [
    "feature_enabled",
    "is_banned",
    "assert_not_banned",
]
