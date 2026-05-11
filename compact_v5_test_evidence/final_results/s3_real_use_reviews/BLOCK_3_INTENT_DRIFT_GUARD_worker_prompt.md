# BLOCK_3_INTENT_DRIFT_GUARD Worker Prompt

Mission block: Intent drift guard.

Scope:
- Keep fixes in flattened compact_v5/ runtime tree.
- Prevent the agent from replacing an S3 inventory request with local compact_v5/source-tree inventory.
- Preserve architecture; do not change Bedrock request shape, tool schemas, security policy, compaction, or final-claim guard behavior beyond a narrow pre-final reminder.

Implementation summary:
- Added a conservative S3 inventory detector to QueryEngine.
- Added an intent-drift guard before final answer emission when an S3 inventory request receives a local workspace/source-tree answer without an S3 answer or explicit S3 blocker.
- Added zero-cost smoke checks for trigger and non-trigger cases.
