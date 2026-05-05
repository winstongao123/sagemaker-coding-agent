# SOFTWARE-RESULTS Decisions

Status: READY_FOR_BLOCK_CLOSE_REVIEW
Date: 2026-05-05

Decisions:

- Store full large tool results under
  `.sageagent_state/tool_results/<session>/<result-id>.txt`.
- Use stable references with the scheme
  `sageagent-result://<session>/<result-id>`.
- Add append-only JSONL metadata at `.sageagent_state/tool_results/index.jsonl`
  with tool name, tool-use id, reason, size, SHA-256, and path.
- Replace model-visible large results with a bounded preview plus replay
  instructions, not with an unsupported Bedrock content-block field.
- Add read-only `result_replay` so the model can inspect persisted output by
  stable reference after truncation, resume, or compaction.
- Preserve the old message-budget clamp as a final safety net, but persist and
  replace results before the clamp so the clamp should not be the first data
  loss point.

Out of scope:

- Binary result artifact rendering and UI preview widgets remain future work.
- Real AWS proof remains R-tier gated; no AWS/R-tier tests were run.
