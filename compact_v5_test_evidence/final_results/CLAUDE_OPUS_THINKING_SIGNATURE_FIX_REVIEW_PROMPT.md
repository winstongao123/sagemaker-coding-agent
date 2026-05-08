You are an independent reviewer for a v5 SageMaker coding-agent runtime fix.

Repository: D:\Github\sagemaker-coding-agent

Review goal: verify the Bedrock extended-thinking signature bug is correctly fixed and does not introduce drift.

User-visible failure:

ValidationException: messages.1.content.0.thinking.signature: Field required

Files to inspect from disk:

- compact_v5/runtime/bedrock_client.py
- compact_v5/core/query_engine.py
- compact_v5_test_evidence/final_results/CRITICAL_BEDROCK_THINKING_SIGNATURE_REGRESSION.md

Required review checks:

1. Response parsing preserves model-supplied signed thinking blocks.
2. QueryEngine replays signed thinking blocks only, and does not synthesize unsigned thinking blocks from display-only thinking text.
3. Outgoing Bedrock chat/count-token messages defensively drop unsigned thinking/redacted_thinking blocks, including old bad in-memory history.
4. Fallback/model-switch replay drops thinking blocks instead of removing only signatures and leaving invalid thinking.
5. The fix still allows thinking text to exist for UI/metrics visibility.
6. No unrelated files or behavior appear changed.

Expected output format:

VERDICT: APPROVE or APPROVE_WITH_FIXES or REQUEST_CHANGES
SHIP DECISION: READY_FOR_USER_RETEST or NOT_READY
FINDINGS:
- list any blockers or low-risk followups

Do not edit files. Read only.
