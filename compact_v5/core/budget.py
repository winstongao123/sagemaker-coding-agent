"""V5 core/budget.py — IterationBudget (Hermes pattern via v4).

Per ADR-014: verbatim port of v4's IterationBudget at
`compact_v4/MAIN/agent/sagemaker_agent.py:8190`. v4 itself adopted this
from `D:/Github/hermes-agent/run_agent.py:170` in v4.9.4.

PORT_LOG: #016.

Why this exists (PS Issue #2):
A parent agent could otherwise spawn N sub-agents that each loop
max_turns times, blowing the cost ceiling. Insurance/audit values
predictable cost ceilings per user request. Counter is shared across
parent + sub-agents (the parent creates one budget at the start of
`run()`; sub-agents inherit the same instance).

Phase 11 (notebook UX) will wire the budget's `consume() / remaining()
/ used() / total()` methods into an ipywidgets progress bar so the
user can SEE the budget burning down — addressing PS Issue #2's
"budget is invisible until exhausted" complaint.
"""
from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional


class IterationBudget:
    """Thread-safe counter shared across a parent agent and its spawned sub-agents.

    A parent agent creates one budget at the start of run(); sub-agents inherit
    the same instance. Each LLM turn (success or failure) increments the counter.
    When `consume()` returns False, the agent surfaces a "budget exhausted"
    message and stops cleanly, preserving partial work.
    """

    DEFAULT_MAX = 600  # v4.10.10 in-place: 90 -> 600 (Hermes default 90 too tight for SageMaker dev)

    def __init__(self, max_iterations: int = DEFAULT_MAX):
        self._max = max(1, int(max_iterations))
        self._used = 0
        self._lock = threading.Lock()

    def consume(self) -> bool:
        """Atomically reserve one iteration. Returns False if budget is exhausted."""
        with self._lock:
            if self._used >= self._max:
                return False
            self._used += 1
            return True

    def remaining(self) -> int:
        with self._lock:
            return max(0, self._max - self._used)

    def used(self) -> int:
        with self._lock:
            return self._used

    def total(self) -> int:
        return self._max

    def reset(self) -> None:
        """Reset counter to 0. Tests + manual /reset only — not a normal flow."""
        with self._lock:
            self._used = 0


class ContextManager:
    """Monitor context usage and provide v4-compatible threshold warnings."""

    def __init__(self, max_tokens: int = 200_000):
        self.max_tokens = int(max_tokens)
        self.last_warning_level = 0

    def estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate message tokens with the v4 conservative chars/3 rule."""
        total_chars = 0
        for message in messages:
            if not isinstance(message, dict):
                total_chars += len(str(message))
                continue
            content = message.get("content", "")
            if isinstance(content, str):
                total_chars += len(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        total_chars += len(str(block.get("text", "")))
                        total_chars += len(str(block.get("content", "")))
                    else:
                        total_chars += len(str(block))
            else:
                total_chars += len(str(content))
        return total_chars // 3

    def get_usage(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Return token usage stats, including fixed prompt/tool overhead."""
        tokens = self.estimate_tokens(messages)
        try:
            from runtime.tokens import TOKENS
            tokens += TOKENS.get_fixed_overhead()
        except Exception:
            tokens += 3350

        percent = tokens / self.max_tokens if self.max_tokens > 0 else 0.0
        return {
            "tokens": tokens,
            "max_tokens": self.max_tokens,
            "percent": percent,
            "level": (
                "critical" if percent >= 0.95
                else "high" if percent >= 0.90
                else "medium" if percent >= 0.80
                else "normal"
            ),
        }

    def check_and_warn(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Return the next threshold warning, once per 80/90/95 level."""
        usage = self.get_usage(messages)
        percent = usage["percent"]
        tokens = usage["tokens"]

        if percent >= 0.95 and self.last_warning_level < 95:
            self.last_warning_level = 95
            return f"[!] Context at 95% ({tokens:,}/{self.max_tokens:,} tokens). Compaction imminent!"
        if percent >= 0.90 and self.last_warning_level < 90:
            self.last_warning_level = 90
            return f"[!] Context at 90% ({tokens:,}/{self.max_tokens:,} tokens). Approaching limit."
        if percent >= 0.80 and self.last_warning_level < 80:
            self.last_warning_level = 80
            return f"[i] Context at 80% ({tokens:,}/{self.max_tokens:,} tokens). Consider starting fresh."
        return None

    def reset(self) -> None:
        """Reset context warning state."""
        self.last_warning_level = 0


def _default_context_max_tokens() -> int:
    try:
        from runtime.config import CONFIG
        return int(CONFIG.context_max_tokens)
    except Exception:
        return 200_000


CONTEXT = ContextManager(_default_context_max_tokens())


__all__ = ["IterationBudget", "ContextManager", "CONTEXT"]
