# Claude Final Review Prompt: BLOCK_7_FINAL_INTEGRATION / FINAL S3 REAL-USE FIX

You are reviewing final integration for compact_v5 S3 real-use fixes.

Repo: d:/Github/sagemaker-coding-agent
Active runtime tree: compact_v5/ (flattened). Do not consider compact_v5/compact_v5/ as active.
Ship zip: compact_v5.zip rebuilt from compact_v5/.

Mission prompt: fix blockers from user transcript "list file and bucket structure of my s3".

Please review these artifacts:
- compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_7_FINAL_INTEGRATION_diff.patch
- compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_7_FINAL_INTEGRATION_tests.log
- compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_7_REAL_AWS_S3_SMOKE.log
- compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_7_FINAL_INTEGRATION_status.md
- compact_v5_test_evidence/final_results/UI_LIVE_SUPERVISOR_ZIP_VERIFY_20260510.md
- compact_v5_test_evidence/final_results/S3_REAL_USE_FIX_20260511.md

Per-block prior Claude verdicts:
- Block 0: APPROVE after re-review2
- Block 1: APPROVE after re-review
- Block 2: APPROVE
- Block 3: APPROVE
- Block 4: APPROVE after re-review
- Block 5: APPROVE after re-review
- Block 6: APPROVE

Questions:
1. Does final integration preserve v5 architecture and active flattened tree discipline?
2. Any code drift from the S3 real-use/UI observability/cost-control scope?
3. Any remaining HIGH/MEDIUM regression risk to Bedrock request shape, thinking signatures, tool dispatch, compaction, security, final-claim/intent guard, subagent receipts, or cost/cache accounting?
4. Are tests/checks sufficient, including py_compile, smoke tests, real AWS evidence, and zip verification?
5. Is compact_v5.zip correctly rebuilt from compact_v5/ with required members, forbidden exclusions, testzip None, and required-member hash parity?
6. Verdict: APPROVE / REQUEST_CHANGES

Important real AWS note to evaluate:
- Direct Python aws_s3_list smoke in this local Python cannot call AWS because boto3 is not installed. The tool now returns an actionable missing-boto3 error. A read-only AWS CLI credential/environment probe `aws s3 ls --no-cli-pager` succeeded and listed buckets, proving credentials and S3 permissions in this machine environment. No destructive AWS calls were run.

If you find HIGH or MEDIUM issues, identify them explicitly with file/line references and required fixes.
