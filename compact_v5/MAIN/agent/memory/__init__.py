"""V5 memory/ — Block H Memory extraction + session memory + compaction.

Block H ports Runnable's extractMemories.ts + sessionMemory.ts +
sessionMemoryCompact.ts patterns to a v5 sync-only module.

Source: _archive/compare_code/gg-claude-code-runnable/src/services/extractMemories.ts
        _archive/compare_code/gg-claude-code-runnable/src/services/sessionMemory.ts
        _archive/compare_code/gg-claude-code-runnable/src/services/sessionMemoryCompact.ts
        _archive/compare_code/gg-claude-code-runnable/src/services/sessionMemoryUtils.ts

Public surface:
- extract.py — extract_memories + closure-scoped throttle state + race guard
- session_memory.py — sessionMemoryUtils.dedup + hasToolCallsInLastAssistantTurn
- compact.py — adjustIndexToPreserveAPIInvariants + calculateMessagesToKeepIndex

Block H deferral note: H-18 getUserContext, H-19 getSystemContext, H-20
Onboarding-step model are CONTEXT BLOCK features that architecturally
fit Block N's dynamic-section + AGENTS.md infrastructure. Per ADR-034
§4 they are explicitly DEFERRED to Block N. No silent scope narrowing.
"""
from __future__ import annotations

from .extract import (  # noqa: F401
    MemoryExtractor,
    extract_memories,
    create_memory_extractor,
)
from .session_memory import (  # noqa: F401
    deduplicate_memory_entries,
    has_tool_calls_in_last_assistant_turn,
    count_tool_calls_since,
)
from .compact import (  # noqa: F401
    adjust_index_to_preserve_api_invariants,
    calculate_messages_to_keep_index,
    has_text_blocks,
)
