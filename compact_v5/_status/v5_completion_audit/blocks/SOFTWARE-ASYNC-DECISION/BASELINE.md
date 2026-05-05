# SOFTWARE-ASYNC-DECISION Baseline

Date: 2026-05-05

Canonical sources:

- `compact_v5/_status/v5_completion_audit/THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`
- `compact_v5/_status/v5_completion_audit/PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md`

Scope:

- DS3-S6: true async/background subagents.
- Requirement: decide whether v5.0.1 must implement true pollable/background
  subagents now, or document them as post-v5.0.1 while strengthening
  synchronous supervision.

Decision baseline:

- v5.0.1 does not ship true async/background subagents.
- The shipped contract is synchronous one-shot `task` subagents that run to
  completion and return a final answer.
- Structured result envelopes, heartbeat/timeout metadata, cost/cache
  attribution, and reviewer evidence are implemented in
  `SOFTWARE-SUBAGENT`, not here.
