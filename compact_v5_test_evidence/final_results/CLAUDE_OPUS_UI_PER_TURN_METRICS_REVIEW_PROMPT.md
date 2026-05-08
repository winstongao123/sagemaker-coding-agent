You are an independent reviewer for a v5 SageMaker coding-agent UI/runtime visibility fix.

Repository: D:\Github\sagemaker-coding-agent

User requirement: cache/cost/reasoning must be visible per assistant turn, not only in the aggregate footer. Also ensure no runtime drift.

Read from disk:
- compact_v5/core/query_engine.py
- compact_v5/ui/chat_ui.py
- compact_v5/runtime/bedrock_client.py
- compact_v5_test_evidence/final_results/CRITICAL_UI_PER_TURN_METRICS_GAP.md
- compact_v5_test_evidence/final_results/CRITICAL_BEDROCK_THINKING_SIGNATURE_REGRESSION.md

Review checks:
1. QueryResult carries display-only thinking safely without changing Bedrock message replay semantics.
2. UI snapshots stats before/after a user turn and renders per-assistant-turn input/output, Cache R/W, cost, without-cache cost, saved cost, calls, and reasoning state.
3. Thinking text, if present, is rendered inline/expandable under the assistant turn.
4. Existing footer/session aggregate metrics remain intact.
5. No drift to Bedrock request body, signature handling, tools, compaction, security, or subagent execution.
6. Identify any remaining gap or test concern.

Output:
VERDICT: APPROVE / APPROVE_WITH_FIXES / REQUEST_CHANGES
DRIFT DECISION: NO_DRIFT / DRIFT_FOUND
FINDINGS:
