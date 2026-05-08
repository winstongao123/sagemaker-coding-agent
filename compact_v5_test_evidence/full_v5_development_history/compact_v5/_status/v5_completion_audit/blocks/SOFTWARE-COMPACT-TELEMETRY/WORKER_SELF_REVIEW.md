# SOFTWARE-COMPACT-TELEMETRY Worker Self-Review

Status: READY_FOR_BLOCK_CLOSE_REVIEW
Date: 2026-05-05

Checks performed:

- Reconstructed scope from third-scan software-builder docs.
- Verified typed compaction audit events no longer depend on substring-only telemetry.
- Verified audit parameter names avoid the existing secret sanitizer's `token` key redaction.
- Verified cache-hit trend is computed when per-turn Bedrock usage is present.
- Verified repeated failed-call telemetry persists across top-level `run()` calls for one engine.
- Confirmed no AWS/R-tier spend was run.

Residual risks:

- Failure signatures are in-memory per `QueryEngine` instance; full restart-persistent loop suppression is left to future policy unless SOFTWARE-GATE consumes status/telemetry evidence differently.
- Manual `/compact` or `/clean` command UX is explicitly not added for v5.0.1; this block provides forced local compaction coverage and typed telemetry.
