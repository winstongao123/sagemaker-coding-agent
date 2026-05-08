# SOFTWARE-GATE Baseline

Status: IMPLEMENTED_PENDING_CLAUDE_REVIEW
Date: 2026-05-05

Canonical source:

- `compact_v5/_status/v5_completion_audit/THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`
- `compact_v5/_status/v5_completion_audit/PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md`

Reconstructed scope:

- DS3-S4 / PS3-9: `/verify` and `/done` must be enforced gates, not only advice.
- DS3-S18: close discipline must consume repeated-failure telemetry so failure loops cannot be silently ignored at done time.
- SOFTWARE-GATE must run after state/result/subagent/telemetry blocks because it consumes those evidence surfaces.

Pre-change behavior:

- `/verify` only armed the `verify` skill and returned an advisory prompt.
- `/done` only told the user to run simplify and verify.
- Neither command persisted a deterministic verification record or blocked stale/missing evidence.
