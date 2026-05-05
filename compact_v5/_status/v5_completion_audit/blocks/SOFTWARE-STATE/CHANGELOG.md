# SOFTWARE-STATE Changelog

Status: CLOSED_PUSHED
Date: 2026-05-05

Changed:

- Added `runtime/state.py` for workspace-scoped durable todos, status/memory
  capture, turn journal, and last-turn recovery JSON.
- Updated `tools/todo.py` so todos persist to disk and can be restored after
  in-memory reset or fresh process start.
- Updated `/save` and `/resume` to include todos, status/memory context, and
  recovery metadata.
- Updated `Agent.run()` to refresh `AGENT_STATUS.md` and `memory.md` every
  top-level turn and write turn journal/recovery evidence.
- Added zero-cost SOFTWARE-STATE integration tests.

Unchanged:

- Existing `Session` schema remains backward-compatible.
- Real LLM memory extraction remains opt-in and outside local zero-cost tests.
- Named checkpoint indexes remain for `SOFTWARE-CHECKPOINT`.

Review:

- Claude review iter1 approved all 5 rows with 0 remaining ship-blocking rows.
- No code changes were required after review.
