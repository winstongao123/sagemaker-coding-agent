# Claude Review Prompt: BLOCK_2_ACCURATE_SANDBOX_DIAGNOSIS

You are reviewing only Block 2 of compact_v5 S3 real-use fixes.

Repo: d:/Github/sagemaker-coding-agent
Active runtime tree: compact_v5/ (flattened). Do not consider compact_v5/compact_v5/ as active.

Block goal:
- Accurate sandbox diagnosis.
- Agent/tool outputs must not misdiagnose Python sandbox import failures or bash S3 allowlist failures as Bedrock-only when CONFIG.aws_bedrock_only is false or when the actual block text does not say aws_bedrock_only=true.

Changed files for this block:
- compact_v5/security/diagnostics.py
- compact_v5/tools/python_exec.py
- compact_v5/prompt/security.md
- compact_v5/tests/test_restriction_diagnostics.py

Please review:
- compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_2_ACCURATE_SANDBOX_DIAGNOSIS_diff.patch
- compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_2_ACCURATE_SANDBOX_DIAGNOSIS_tests.log
- compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_2_ACCURATE_SANDBOX_DIAGNOSIS_status.md

Questions:
1. Does this block preserve v5 architecture?
2. Any code drift from the scope of accurate sandbox diagnosis?
3. Any regression risk to Bedrock request shape, thinking signatures, tool dispatch, compaction, security, final-claim guard, subagent receipts, or cost/cache accounting?
4. Are tests/checks sufficient for this block?
5. Verdict: APPROVE / REQUEST_CHANGES

If you find HIGH or MEDIUM issues, identify them explicitly with file/line references and required fixes.
