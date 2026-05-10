"""V5 memory package - Block H.

Block H ports Runnable memory extraction, session memory, session-memory
compaction, context, and onboarding helpers to v5's synchronous runtime.
"""
from __future__ import annotations

from .compact import (  # noqa: F401
    SessionMemoryCompactConfig,
    adjust_index_to_preserve_api_invariants,
    calculate_messages_to_keep_index,
    has_text_blocks,
    is_session_memory_empty,
    should_use_session_memory_compaction,
    truncate_session_memory_for_compact,
)
from .context import (  # noqa: F401
    OnboardingState,
    get_system_context,
    get_user_context,
    should_show_onboarding,
)
from .extract import (  # noqa: F401
    MemoryExtractor,
    create_auto_mem_can_use_tool,
    create_memory_extractor,
    extract_memories,
)
from .session_memory import (  # noqa: F401
    count_tool_calls_since,
    create_memory_file_can_use_tool,
    deduplicate_memory_entries,
    has_tool_calls_in_last_assistant_turn,
    wait_for_session_memory_extraction,
)
