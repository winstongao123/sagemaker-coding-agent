# SOFTWARE-RESULTS Changelog

Status: READY_FOR_BLOCK_CLOSE_REVIEW
Date: 2026-05-05

Code changes:

- Added `runtime/results.py` with durable result artifact persistence,
  replacement-text construction, stable reference parsing, and replay reads.
- Added read-only `tools/result_replay.py`.
- Registered `result_replay` in the built-in tool surface and plan-mode
  allowlist.
- Updated `core/query_engine.py` to persist large per-tool and aggregate
  over-budget `tool_result` blocks before applying the final Bedrock
  message-budget clamp.

Test changes:

- Added `tests/integration/test_software_results.py`.
- Updated the Block T aggregate tool-result budget regression to assert stable
  replay references instead of accepting marker-only truncation.
- Applied Claude LOW cleanup so storage-disabled mode strips internal
  `_sageagent_*` metadata before returning a tool result.

Affected completed block:

- Block T: the shared `enforce_tool_result_message_budget()` regression changed
  because SOFTWARE-RESULTS intentionally strengthens the QueryEngine behavior
  above the old Block T marker-only budget contract.
