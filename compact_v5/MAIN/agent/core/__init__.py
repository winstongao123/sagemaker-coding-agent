"""V5 core/ — agent loop + retry + errors + budget.

Per ADR-014 (Phase 8):
  - core/query_engine.py : main agent loop (Runnable QueryEngine.ts adaptation)
  - core/retry.py        : jittered exponential backoff (Phase-1 RetryPolicy extracted)
  - core/errors.py       : Bedrock error classifier (Phase-1 ErrorClassifier extracted)
  - core/budget.py       : IterationBudget (Hermes pattern via v4)
  - core/cache.py        : prompt-cache block builder + cache-break detection (Phase 6)

Phase 7 contract: query_engine MUST call `apply_tool_search_deferral(enabled=True)`
per turn AND extract discovered tool names via `tool_search_discovered_names()`
to wire deferred tools into the next turn's API call.
"""
from __future__ import annotations

# Re-export the public surface
from .budget import IterationBudget  # noqa: F401
from .errors import (  # noqa: F401
    BedrockErrorCategory,
    ErrorClassifier,
    categorize_retryable,
    extract_nested_error_message,
    parse_max_tokens_context_overflow_error,
    get_retry_after_ms,
)
from .cache_break_detection import (  # noqa: F401
    PerToolCacheBreakDetector,
    is_cache_break_excluded,
    hash_tool_schema,
    notify_cache_deletion,
)
from .retry import RetryPolicy  # noqa: F401
from .query_engine import QueryEngine, run_one_turn, count_tool_calls  # noqa: F401
