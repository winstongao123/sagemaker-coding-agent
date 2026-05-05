# SOFTWARE-COMPACT-TELEMETRY Decisions

Status: READY_FOR_BLOCK_CLOSE_REVIEW
Date: 2026-05-05

Decisions:

- Emit typed compaction audit actions from `QueryEngine` for auto-compact and cold-cache microcompact paths.
- Use neutral audit parameter names such as `saved_count`, `before_count`, and `after_count` so the existing audit sanitizer does not redact token-count telemetry as a secret.
- Keep historical substring-compatible compaction extraction in `build_telemetry.py`, but mark events with `typed=true/false` so new evidence can require typed events.
- Compute cache trend from per-turn `chat_response` cache-hit percentages when Bedrock usage fields are present.
- Keep the existing side-channel token/cost/cache attribution changes and extend them as active SOFTWARE-COMPACT-TELEMETRY evidence because this block owns telemetry consumption.
- Add durable failure-loop audit events: `tool_failure_recorded`, `tool_failure_loop_warning`, and `tool_failure_loop_blocked`.
- Do not add a new user-facing `/compact` or `/clean` command in v5.0.1. Manual compaction remains a future UX improvement unless AWS Phase A/Phase C evidence shows it is necessary. This block adds direct local coverage for forced micro/auto compaction and typed telemetry instead, satisfying the DS3-S9 test-hardening/no-goal branch.

Out of scope:

- Full OTel/export pipeline remains future DS3-S13 scope.
- AWS proof of natural long-session compaction remains R-tier gated.
