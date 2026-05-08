# SOFTWARE-SUBAGENT Decisions

Status: READY_FOR_BLOCK_CLOSE_REVIEW
Date: 2026-05-05

Decisions:

- Keep v5.0.1 subagents synchronous, consistent with the `SOFTWARE-ASYNC-DECISION` close decision.
- Add `SubagentResult.to_envelope()` as the stable structured evidence surface with schema `sageagent.subagent_result.v1`.
- Include role/agent type, child session id, stop reason, turns used, duration, heartbeat count/last timestamp, timeout/timed-out metadata, files changed, token deltas, cost, cache read/write deltas, error, recovery hint, and bounded summary.
- Append the envelope to `task` output under `[subagent_result_envelope]` so callers and later transcripts can inspect reviewer/subagent evidence without needing internal Python object access.
- Emit a best-effort `subagent_result` audit event for telemetry consumers.
- Record `timed_out=true` for budget/max-turn exhaustion in the accepted synchronous contract; true wall-clock child cancellation remains out of scope for v5.0.1 and would belong with a future async/background worker design.
- Keep full child transcript available on the Python result object for direct tests and future telemetry; the model-visible `task` output receives bounded summary fields rather than full transcript replay.

Out of scope:

- True concurrent or pollable background subagent execution.
- Real AWS reviewer/subagent proof; this remains R-tier gated.
