# SOFTWARE-COMPACT-TELEMETRY Changelog

Status: READY_FOR_BLOCK_CLOSE_REVIEW
Date: 2026-05-05

Changed implementation:

- `compact_v5/MAIN/agent/core/query_engine.py`
  - emits typed audit events for cold-cache microcompact start/end/failure;
  - emits typed audit events for auto-compact start/end/skipped/failure;
  - tracks failed tool signatures across top-level runs and blocks the third identical failed call with durable audit evidence.
- `compact_v5/_status/scripts/build_telemetry.py`
  - adds `failure_loop_events` to required telemetry output;
  - marks compaction events as typed or legacy;
  - computes cache-hit trend from per-turn usage;
  - includes parent/subagent/reviewer token/cost/cache attribution from the side channel.

Changed tests:

- `compact_v5/MAIN/agent/tests/integration/test_software_compact_telemetry.py`
- `compact_v5/MAIN/agent/tests/integration/test_build_telemetry.py`

Affected original blocks:

- Block A compaction paths are strengthened under active SOFTWARE-COMPACT-TELEMETRY scope.
- Block N repeated-call protection is strengthened under active SOFTWARE-COMPACT-TELEMETRY scope.
- Pre-existing uncommitted telemetry-builder edits are incorporated because they map directly to PS3-6 and this block's telemetry-consumption requirement.
