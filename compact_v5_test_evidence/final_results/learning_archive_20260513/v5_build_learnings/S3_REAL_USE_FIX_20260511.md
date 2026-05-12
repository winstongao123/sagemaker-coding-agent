# S3 Real-Use Fix - 2026-05-11

Active runtime tree: `compact_v5/`

Prompt that triggered the work: `list file and bucket structure of my s3`

## SPEC vs SHIPPED

| Spec | Shipped |
|---|---|
| Fix broken/contradictory S3 safe-read path | Added read-only `aws_s3_list`, always visible, plan-mode allowed, Bedrock-only aware. |
| Stop Bedrock-only misdiagnosis | Bash S3 blocks name the bash allowlist; Python import blocks name the Python sandbox import allowlist. |
| Prevent S3-to-source-tree drift | Added S3 intent-drift guard before final answers. |
| Collapse/group tool cards | Tool call/result UI cards are grouped by `tool_use_id` and closed by default. |
| Collapse/reposition thinking | Thinking details are closed by default and render before per-turn metrics. |
| Control simple S3 inventory cost | Simple S3 inventory avoids `tool_search`, one-strike blocks repeated bash S3 retries, and disables Extended Thinking for that turn only. |
| Preserve architecture | No model/cache/compaction rewrite; Bedrock client/request schema unchanged except narrow per-turn thinking disable. |

## Evidence

Per-block artifacts live under:

`compact_v5_test_evidence/final_results/s3_real_use_reviews/`

Each block saved worker prompt, diff, tests, Claude review prompt, and Claude
output. Blocks 0-6 reached Claude `APPROVE` after required fixes.

## Tests

Focused zero-cost smokes:

- `compact_v5/tests/test_aws_s3_list_tool.py`
- `compact_v5/tests/test_restriction_diagnostics.py`
- `compact_v5/tests/test_s3_intent_drift_guard.py`
- `compact_v5/tests/test_ui_tool_cards_smoke.py`
- `compact_v5/tests/test_ui_thinking_smoke.py`
- `compact_v5/tests/test_s3_cost_controls.py`

Required py_compile checks are recorded in the final integration review
artifacts.
