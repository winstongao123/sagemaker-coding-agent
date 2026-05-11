# BLOCK_6_COST_CONTROLS_SIMPLE_S3_INVENTORY Worker Prompt

Mission block: Cost controls for simple inventory tasks.

Scope:
- Measure/control known cost drivers without changing model choice, cache policy, or compaction policy.
- Keep S3 inventory path cheap: no tool_search tax, no repeated blocked bash S3 retries, no Extended Thinking overhead for simple read-only S3 inventory turns.
- Preserve v5 architecture and Bedrock/security semantics.

Implementation summary:
- Added narrow simple-S3-inventory detector in Agent.
- Added config flag disable_thinking_for_simple_s3_inventory=True; when enabled and the request is simple read-only S3 inventory, Agent sends that turn with thinking_enabled=False and emits a visible [cost control] line. It does not change the configured model, cache, compaction, temperature, or persistent thinking setting.
- Added last_effective_thinking_enabled so UI metrics report the per-turn effective thinking state.
- Added bash aws s3/aws s3api one-strike retry guard using existing QueryEngine failure-class mechanics.
- Added prompt guidance that aws_s3_list is always-loaded for simple S3 inventory and blocked aws s3 bash should not be retried.
- Added zero-cost smoke checks for thinking suppression, aws_s3_list visibility without tool_search, and retry guard classification.
