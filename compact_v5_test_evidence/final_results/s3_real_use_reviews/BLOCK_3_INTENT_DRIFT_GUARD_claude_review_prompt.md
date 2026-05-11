# Claude Review Prompt: BLOCK_3_INTENT_DRIFT_GUARD

You are reviewing only Block 3 of compact_v5 S3 real-use fixes.

Repo: d:/Github/sagemaker-coding-agent
Active runtime tree: compact_v5/ (flattened). Do not consider compact_v5/compact_v5/ as active.

Block goal:
- Intent drift guard.
- For the transcript request "list file and bucket structure of my s3", the agent must not answer by listing the local compact_v5/source tree. It should use read-only S3 inventory tooling or clearly report the actual S3 blocker.

Changed files for this block:
- compact_v5/core/query_engine.py
- compact_v5/tests/test_s3_intent_drift_guard.py

Please review:
- compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_3_INTENT_DRIFT_GUARD_diff.patch
- compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_3_INTENT_DRIFT_GUARD_tests.log
- compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_3_INTENT_DRIFT_GUARD_status.md

Questions:
1. Does this block preserve v5 architecture?
2. Any code drift from the scope of S3 intent drift prevention?
3. Any regression risk to Bedrock request shape, thinking signatures, tool dispatch, compaction, security, final-claim guard, subagent receipts, or cost/cache accounting?
4. Are tests/checks sufficient for this block?
5. Verdict: APPROVE / REQUEST_CHANGES

If you find HIGH or MEDIUM issues, identify them explicitly with file/line references and required fixes.
