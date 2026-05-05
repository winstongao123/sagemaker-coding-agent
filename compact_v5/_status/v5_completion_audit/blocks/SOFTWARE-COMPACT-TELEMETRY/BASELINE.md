# SOFTWARE-COMPACT-TELEMETRY Baseline

Status: READY_FOR_BLOCK_CLOSE_REVIEW
Date: 2026-05-05

Canonical source:

- `compact_v5/_status/v5_completion_audit/THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`
- `compact_v5/_status/v5_completion_audit/PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md`
- `compact_v5/_status/v5_completion_audit/BLOCK_ORDER_AND_COVERAGE.md`

Scope reconstructed:

- DS3-S9: manual compact/clean controls are test hardening or explicit no-goal decision.
- DS3-S10: compaction/recovery telemetry must use typed audit events such as `compact_auto_start`, `compact_auto_end`, `compact_micro_start`, `compact_micro_end`, and `compact_failed`.
- DS3-S18: broader repeated-failure loop telemetry must record repeated tool failures and loop blocks.
- PS3-1 and PS3-6: compaction survival and cache/cost telemetry must be visible in local/AWS evidence.

Pre-block behavior:

- Auto/micro compaction primarily surfaced UI text and broad compact-like audit strings.
- `build_telemetry.py` detected compaction by substring and had no failure-loop evidence array.
- Cache trend was present per turn when `chat_response` usage existed, but the top-level trend remained null.
- The same-call repetition guard existed in `QueryEngine`, but repeated failed-call evidence was not durable across top-level runs.

No AWS/R-tier spend was run for this block.
