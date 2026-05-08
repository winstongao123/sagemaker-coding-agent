# Final Test Suite Index

This folder is the easy-to-find archive for the PS/PS human acceptance tests and
their AWS/comparison evidence.

It lives next to `compact_v5/`, not inside the production runtime zip. The
production zip stays small; this archive stays in GitHub as proof and reference.

## Final Test Prompts

| Test | Easy path | Original restored path | Purpose |
|---|---|---|---|
| PS/PS v1 | `final_test_suites/PS_PS_FINAL_TEST.md` | `compact_v5/docs/PS_PS_FINAL_TEST.md` | First human long-running software engineering acceptance prompt. |
| PS/PS v2 | `final_test_suites/PS_PS_FINAL_TEST_v2.md` | `compact_v5/docs/PS_PS_FINAL_TEST_v2.md` | Improved Sonnet test with stronger zip validation and UI watch list. |
| PS/PS v3 | `final_test_suites/PS_PS_FINAL_TEST_v3.md` | `compact_v5/docs/PS_PS_FINAL_TEST_v3.md` | Final Haiku test focused on UI metrics, subagent evidence, v5 code scan, long coding, and valid package output. |

## Final Result Summaries

| Result | Easy path | What it proves |
|---|---|---|
| v2 result | `final_results/PS_PS_FINAL_TEST_v2_RESULT.md` | Records the v2 acceptance outcome and lessons. |
| v3 result | `final_results/PS_PS_FINAL_TEST_v3_RESULT.md` | Records the final v3 pass after subagent evidence and Bedrock tool-pairing fixes. |
| Full test review | `final_results/PS_TEST_REVIEW_FINAL.md` | Explains every major R-tier / PS/PS issue found, fixed, reviewed, and retested. |
| Fresh v4-vs-v5 report | `final_results/Critical_PS_PS_V4_FRESH_COMPARE_REPORT.md` | Side-by-side evidence that v5 is stronger than v4 on the software-engineering benchmark. |

## Full Evidence Bundles

| Bundle | Path | Contents |
|---|---|---|
| AWS v1 acceptance | `compact_v5/_status/aws_acceptance_v1/` | Real Sonnet AWS run logs, visual summary, pytest logs, zip validation, and salvaged result zip. |
| v3 comparison | `compact_v5/_status/ps_ps_v3_compare/` | Same Haiku benchmark run against v4 and v5, with prompts, stdout logs, pytest logs, and summaries. |
| fresh v4 comparison | `compact_v5/_status/ps_ps_v4_fresh_compare/` | Later fresh comparison plus Runnable lessons for final guard hardening. |
| R-tier matrix | `compact_v5/_status/r_tier_test_matrix.json` | Final 42-row R-tier status: READY and reviewed disposition rows. |
| R-tier telemetry | `compact_v5/_status/r_tier_metrics.jsonl` | Recorded R-tier cost/telemetry events. |
| final Claude review | `compact_v5/_status/v5_completion_audit/reviews/final-claude-post-aws-production-readiness-review.md` | Independent final production-readiness review. |

## Explain Like Age 9

The `compact_v5.zip` file is the small robot you send to the company machine.

This `compact_v5_test_evidence/` folder is the robot's report card and test
videos. Keep it in GitHub, but do not put it inside the company zip.
