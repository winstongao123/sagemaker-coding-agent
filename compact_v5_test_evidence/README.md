# compact_v5 Test Evidence Archive

This folder keeps the v5 test prompts, results, logs, and comparison evidence out
of the minimum production ship zip.

It is intentionally outside `compact_v5/`, so rebuilding `compact_v5.zip` from
the production runtime folder will not include these files.

## What Is Here

| Folder/File | What it means |
|---|---|
| `compact_v5/docs/PS_PS_FINAL_TEST*.md` | Human-facing long-running software engineering acceptance prompts and result summaries. |
| `compact_v5/docs/PS_TEST_REVIEW_FINAL.md` | Final readable review of what the test suite found and fixed. |
| `compact_v5/docs/Critical_PS_PS_V4_FRESH_COMPARE_REPORT.md` | Fresh v4-vs-v5 comparison summary. |
| `compact_v5/_status/PS_PS_FINAL_TEST*.md` | Original status-copy versions of the PS/PS acceptance prompts/results. |
| `compact_v5/_status/aws_acceptance_v1/` | First real AWS/Sonnet acceptance run evidence. |
| `compact_v5/_status/ps_ps_v3_compare/` | Haiku v4-vs-v5 comparison evidence where v5 completed the task and v4 drifted. |
| `compact_v5/_status/ps_ps_v4_fresh_compare/` | Fresh comparison logs and Runnable lessons used for final guard hardening. |
| `compact_v5/_status/r_tier_test_matrix.json` | Final R-tier matrix with READY / DISPOSITION_OK rows. |
| `compact_v5/_status/r_tier_metrics.jsonl` | R-tier spend/telemetry records. |
| `compact_v5/_status/R_TIER_*.md` | R-tier gate/status/follow-up summaries. |
| `compact_v5/_status/v5_completion_audit/FINAL_POST_AWS_*.md` | Final post-AWS production-readiness summaries. |
| `compact_v5/_status/v5_completion_audit/reviews/final-claude-post-aws-production-readiness-review.md` | Final independent Claude production-readiness review. |

## Explain Like Age 9

The company zip is the robot you ship.

This folder is the robot's report card, homework, and test videos.

They should stay in Git so we can prove what happened, but they should not be
inside the small production zip.
