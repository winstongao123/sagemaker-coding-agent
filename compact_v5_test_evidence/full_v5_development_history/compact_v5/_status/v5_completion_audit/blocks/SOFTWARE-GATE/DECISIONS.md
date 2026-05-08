# SOFTWARE-GATE Decisions

Status: IMPLEMENTED_PENDING_CLAUDE_REVIEW
Date: 2026-05-05

## Decision: local deterministic evidence gate

`/verify` now runs a zero-cost local gate and writes `.sageagent_state/gates/last_verify.json`. `/done` refuses to pass unless that record is fresh, passing, and matches the requested mode. `/done` then re-runs the evidence checks so stale status or failed telemetry after verification still blocks close.

## Decision: full vs quick evidence scope

`full` mode requires fresh status, test, review, result, subagent, and telemetry evidence. `quick` mode requires fresh status, test, and review evidence. Tests cover `full` because the third-scan software-builder requirement needs the stricter close discipline before production-readiness claims.

## Decision: telemetry failure loops are blocking evidence

Fresh telemetry can satisfy the telemetry category only when it contains accepted telemetry markers and no unresolved `tool_failure_loop_blocked` or `tool_failure_loop_warning` marker. A failure-loop marker means the agent has evidence of repeated failed calls that must be addressed before `/done` can claim ready.

## Decision: no overlapping command family

No `/project-*` command was added. The existing `/verify` and `/done` surfaces were strengthened in place, following `PS_SOFTWARE_PROJECT_WORKFLOW.md`.
