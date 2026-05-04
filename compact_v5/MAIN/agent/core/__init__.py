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
    classify_axios_error,
    ConfigParseError,
    drop_prompt_too_long_message_groups,
    extract_connection_error_details,
    extract_nested_error_message,
    fallback_model_for_529,
    get_prompt_too_long_token_gap,
    get_rate_limit_reset_delay_ms,
    get_retry_after_ms,
    humanize_api_error,
    is_529_error,
    is_fs_inaccessible,
    parse_max_tokens_context_overflow_error,
    rollback_to_last_assistant_turn,
    sanitize_api_error,
    ShellError,
    short_error_stack,
    should_retry_529,
    TelemetrySafeError,
    to_error,
)
from .cache_break_detection import (  # noqa: F401
    cache_control_hash,
    classify_ttl_expiry,
    MAX_TRACKED_SOURCES,
    MIN_CACHE_MISS_TOKENS,
    PerToolCacheBreakDetector,
    PromptStateSnapshot,
    is_cache_break_excluded,
    hash_tool_schema,
    notify_cache_deletion,
    strip_cache_control,
    write_cache_break_diff,
)
from .parallel_dispatch import (  # noqa: F401
    NEVER_PARALLEL_TOOLS,
    PARALLEL_SAFE_TOOLS,
    PATH_SCOPED_TOOLS,
    MAX_TOOL_WORKERS,
    _MAX_TOOL_WORKERS,
    _NEVER_PARALLEL_TOOLS,
    _PARALLEL_SAFE_TOOLS,
    _PATH_SCOPED_TOOLS,
    classify_tool_retry,
    dedup_tool_calls,
    detect_path_conflicts,
    enforce_turn_budget,
    execute_parallel_tool_calls,
    fuzzy_resolve_tool_name,
    is_parallel_safe_call,
    mark_ephemeral_block,
    mid_call_stub_recovery,
    path_scope_key,
    pending_tool_use_ids,
    plan_tool_dispatch,
    strip_ephemeral_blocks_for_persist,
    inject_dynamic_tool_refs,
    synthetic_tool_result_stub,
    ToolDispatchSnapshot,
    ToolRetryClassification,
    partial_tool_call_warning,
)
from .retry import RetryPolicy  # noqa: F401
from .formatting import (  # noqa: F401
    format_cost,
    format_duration,
    format_file_size,
    format_tokens,
)
from .query_engine import (  # noqa: F401
    FallbackTriggeredError,
    QueryEngine,
    count_tool_calls,
    run_one_turn,
    strip_signature_blocks,
)
