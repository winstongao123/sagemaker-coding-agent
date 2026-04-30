"""V5 entry.py — cell-0 import target for chat.ipynb (Phase 11, ADR-017).

Re-exports the public surface. Notebook cells should be able to:

    from entry import Agent, create_chat_ui, CONFIG, BEDROCK_MODELS

without knowing which subpackage owns each name.

PORT_LOG: see #031 + #032 (chat.ipynb wiring).
"""
from __future__ import annotations

# Public Agent class (Phase 11 — wraps Phase 1-10 modules)
from agent import Agent  # noqa: F401

# Config singleton + Bedrock model registry (Phase 1)
from runtime.config import CONFIG  # noqa: F401

# Optional Bedrock model list — kept as a module-level constant so the
# config widget in chat.ipynb cell 2 can populate a dropdown.
BEDROCK_MODELS = [
    ("Claude Sonnet 4.5 (anthropic.claude-sonnet-4-5-20250929-v1:0)",
     "anthropic.claude-sonnet-4-5-20250929-v1:0"),
    ("Claude Haiku 4.5 (au.anthropic.claude-haiku-4-5-20251001-v1:0)",
     "au.anthropic.claude-haiku-4-5-20251001-v1:0"),
    ("Claude Sonnet 3.5 (anthropic.claude-3-5-sonnet-20241022-v2:0)",
     "anthropic.claude-3-5-sonnet-20241022-v2:0"),
]

# Chat UI factory (Phase 11)
from ui.chat_ui import create_chat_ui  # noqa: F401

# Skill manager helper for power users who want to inspect / activate
# skills programmatically (Phase 10).
from skills.manager import SkillManager  # noqa: F401

# IterationBudget for power users + tests (Phase 8).
from core.budget import IterationBudget  # noqa: F401
