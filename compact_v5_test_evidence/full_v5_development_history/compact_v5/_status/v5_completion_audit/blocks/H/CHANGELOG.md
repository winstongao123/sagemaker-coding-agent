# Block H Changelog

Date: 2026-05-05

- Added `create_auto_mem_can_use_tool` for H-5 scoped auto-memory extractor permissions.
- Added `wait_for_session_memory_extraction` and `create_memory_file_can_use_tool` for H-8/H-10 session-memory isolation.
- Added `SessionMemoryCompactConfig`, `truncate_session_memory_for_compact`, `is_session_memory_empty`, and `should_use_session_memory_compaction` for H-13/H-15/H-16/H-17.
- Added `memory/context.py` with `get_user_context`, `get_system_context`, and `OnboardingState` for H-18/H-19/H-20.
- Wired Block H user/system context into `prompt.build_system_prompt` dynamic content and passed workspace context from `Agent.run`.
- Expanded `tests/integration/test_block_h.py` to cover all 20 canonical H rows.
- Added PORT_LOG #196 and ADR-034 completion-audit addendum superseding the historical #098 deferral row.
- Created Block H audit artifacts and ledger.
