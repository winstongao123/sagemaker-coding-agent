You are re-reviewing a v5 SageMaker coding-agent Bedrock thinking-signature fix after one cleanup.

Repository: D:\Github\sagemaker-coding-agent

Inspect from disk:
- compact_v5/runtime/bedrock_client.py
- compact_v5/core/query_engine.py
- compact_v5_test_evidence/final_results/CRITICAL_BEDROCK_THINKING_SIGNATURE_REGRESSION.md
- compact_v5_test_evidence/final_results/CLAUDE_OPUS_THINKING_SIGNATURE_FIX_REVIEW.md

Question: is the final implementation safe for user retest of thinking-enabled multi-turn Bedrock chats?

Checks:
1. Signed thinking blocks are preserved and replayed.
2. Unsigned thinking blocks are not synthesized or sent.
3. Old invalid history is sanitized on chat and count-token paths.
4. Fallback/model-switch drops thinking blocks entirely.
5. The post-review cleanup computes token-count `uses_thinking` after sanitization.
6. No unrelated drift.

Output exactly:
VERDICT: APPROVE / APPROVE_WITH_FIXES / REQUEST_CHANGES
SHIP DECISION: READY_FOR_USER_RETEST / NOT_READY
FINDINGS:
