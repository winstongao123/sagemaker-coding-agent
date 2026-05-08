# SOFTWARE-RESULTS Baseline

Status: READY_FOR_BLOCK_CLOSE_REVIEW
Date: 2026-05-05

Canonical scope:

- `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`: DS3-S7 requires large
  tool-result persistence/replay and content-replacement references.
- `PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md`: PS3-7 requires large
  tool outputs to be persisted and replayable by stable reference.
- `BLOCK_ORDER_AND_COVERAGE.md`: SOFTWARE-RESULTS follows SOFTWARE-SHELL and
  precedes SOFTWARE-SUBAGENT.

Pre-change behavior:

- `QueryEngine._truncate_tool_result()` shortened oversized tool results inline.
- `enforce_tool_result_message_budget()` clamped aggregate tool-result message
  content with a marker.
- Some tool-specific truncation paths saved ad hoc files, but QueryEngine's
  per-tool and aggregate truncation paths did not produce a durable stable
  replay reference.

Risk:

- Long software-building runs could lose the full output needed to inspect
  test logs, generated diagnostics, or large command output after compaction,
  resume, or handoff.
