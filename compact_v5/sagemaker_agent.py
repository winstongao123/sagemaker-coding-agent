"""v4-compatibility shim — `sagemaker_agent` re-exports v5's public surface.

Block 0 of v5.0.1. Constraint #2 (`v4 chat.ipynb = canonical UI`) requires
that v4's notebook line `from sagemaker_agent import CONFIG, BEDROCK_MODELS,
create_chat_ui` continues to work unchanged on v5. The notebook does not
need to know that v5 reorganized internals into `runtime/`, `agent/`, `ui/`,
etc.; it only needs the public symbols at the historic import path.

This module is intentionally tiny — the implementations live in their
proper v5 modules; here we only re-bind names. The shim's only job is the
import-path invariant.

The full v5 public surface is owned by `entry`. We mirror it here so that
either import works:

    from sagemaker_agent import CONFIG, BEDROCK_MODELS, create_chat_ui  # v4 path
    from entry import CONFIG, BEDROCK_MODELS, create_chat_ui            # v5 path

PORT_LOG: see #038 (Block 0 shim).
"""
from __future__ import annotations

from entry import (  # noqa: F401
    Agent,
    BEDROCK_MODELS,
    CONFIG,
    IterationBudget,
    SkillManager,
    create_chat_ui,
)

__all__ = [
    "Agent",
    "BEDROCK_MODELS",
    "CONFIG",
    "IterationBudget",
    "SkillManager",
    "create_chat_ui",
]
