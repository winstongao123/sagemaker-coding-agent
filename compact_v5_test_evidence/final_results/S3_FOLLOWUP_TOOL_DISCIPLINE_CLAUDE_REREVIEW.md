All 47 tests pass. Verified:

- `_is_status_output` now includes `"[intent-drift guard:"` and `"[truncation guard:"` (chat_ui.py:1323-1324). Prefixes match the exact strings the engine emits at query_engine.py:1132 (`[truncation guard: S3 evidence is partial; continuing]`) and 1142 (`[intent-drift guard: S3 inventory evidence is not ready; continuing]`). These rows are routed to the `system` lane instead of the `assistant` lane, as intended.
- No other behavior changed in chat_ui.py beyond the previously approved tool-id hiding, live `[thinking]` routing, and turn-meta dedup.
- Smoke tests (`test_ui_thinking_smoke`, `test_ui_tool_cards_smoke`) still pass; new tests (`test_s3_followup_tool_discipline`, `test_artifact_workspace_policy`, `test_aws_s3_preview_tool`) pass; full v5 suite 47/47 green.
- Previous approvals for S3 follow-up reuse, capped S3 list fanout, `aws_s3_preview`, artifact tracking + workspace default, ASCII guard, AGENT_STATUS guard, thinking placement, tool-id hiding, and cost behavior remain valid — none of those code paths were touched by this patch.

APPROVE
