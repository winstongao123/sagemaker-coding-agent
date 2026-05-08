# SOFTWARE-SUBAGENT Baseline

Status: READY_FOR_BLOCK_CLOSE_REVIEW
Date: 2026-05-05

Canonical source:

- `compact_v5/_status/v5_completion_audit/THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`
- `compact_v5/_status/v5_completion_audit/PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md`
- `compact_v5/_status/v5_completion_audit/BLOCK_ORDER_AND_COVERAGE.md`

Scope reconstructed:

- DS3-S5 requires structured synchronous subagent/reviewer result telemetry: timeout/heartbeat metadata, structured child traces, files changed, tokens, cost, duration, cache attribution, and parent recovery tests.
- PS3-4 requires subagent and reviewer calls to produce structured evidence.
- PS3-6 requires token/cost/cache telemetry to include child/subagent work where available.
- True async/background subagents are not part of this block; that decision was closed in `SOFTWARE-ASYNC-DECISION`.

Pre-block behavior:

- `task` returned the child final text or a budget/max-turn stop string.
- `spawn_subagent` returned Python fields such as text, stop reason, turns, and child messages, but no durable structured envelope suitable for reviewer evidence.
- Child token attribution existed in `runtime.tokens`, but `task` did not surface per-child deltas in its return evidence.
- Parent recovery behavior existed for shared budget and parent-context protection, but it was not represented in the task result surface.

No AWS/R-tier spend was run for this block.
