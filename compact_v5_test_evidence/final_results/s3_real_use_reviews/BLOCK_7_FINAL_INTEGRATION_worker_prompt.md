# BLOCK_7_FINAL_INTEGRATION Worker Prompt

Mission block: Final integration / zip / real AWS smoke.

Scope:
- Update docs/status for S3 real-use fixes.
- Run required py_compile checks and focused zero-cost smoke tests.
- Attempt read-only real AWS S3 smoke without destructive calls.
- Rebuild compact_v5.zip from flattened compact_v5/ active tree, excluding tests/cache/status/evidence/git folders.
- Verify zip opens, testzip() is None, required members exist, forbidden folders absent, required member hash parity passes.

Implementation summary:
- Updated AGENT_STATUS.md, chat.md, PS_PS_FINAL_TEST_v3_REAL_USE_ISSUES.md, PS_PS_FINAL_TEST_v3_UI_ISSUES.md, PS_TEST_REVIEW_FINAL.md, and added S3_REAL_USE_FIX_20260511.md.
- Added missing-boto3 handling to aws_s3_list after local direct tool smoke showed this Python lacks boto3.
- Real AWS credential/environment probe via read-only `aws s3 ls --no-cli-pager` succeeded and listed buckets. Direct Python tool smoke returned the new actionable missing-boto3 message in this local Python.
- Rebuilt compact_v5.zip from compact_v5/ and wrote zip verification report.
