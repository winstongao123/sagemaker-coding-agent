"""Block 0 item 0-8 (remapped to Block B per ADR-020) — env-var validation.

Adapter of Runnable's `validateBoundedIntEnvVar` (utils/envValidation.ts:1-39).
A single helper for sanitizing all numeric env knobs (max_turns, budget,
cost_limit, retention_days, etc.) so config loaders never crash on
malformed values and instead clamp to documented bounds.

PORT_LOG: see #045.
"""
from __future__ import annotations

import logging
import os
from typing import Optional


def validate_bounded_int_env_var(
    name: str,
    *,
    minimum: int,
    maximum: int,
    default: int,
    env: Optional[dict] = None,
) -> int:
    """Read an env var and clamp it into [minimum, maximum].

    Returns `default` when:
      - The variable is not set
      - The value cannot be parsed as int
      - The value is outside the [minimum, maximum] window (clamps + logs)

    Logs at WARNING level when a value is found but rejected/clamped, so
    operators can spot configuration drift without the runtime crashing.
    """
    source = env if env is not None else os.environ
    raw = source.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        logging.warning(
            f"env var {name}={raw!r} is not an integer; using default {default}"
        )
        return default
    if value < minimum:
        logging.warning(
            f"env var {name}={value} below minimum {minimum}; clamped to minimum"
        )
        return minimum
    if value > maximum:
        logging.warning(
            f"env var {name}={value} above maximum {maximum}; clamped to maximum"
        )
        return maximum
    return value


__all__ = ["validate_bounded_int_env_var"]
