You are Claude Opus acting as an independent reviewer for a narrow v5 UI/runtime fix.

Repo: D:\Github\sagemaker-coding-agent

Read these files from disk:

- compact_v5/core/query_engine.py
- compact_v5/ui/chat_ui.py
- compact_v5/runtime/bedrock_client.py
- compact_v5_test_evidence/final_results/CRITICAL_UI_PER_TURN_METRICS_GAP.md
- compact_v5_test_evidence/final_results/CRITICAL_BEDROCK_THINKING_SIGNATURE_REGRESSION.md

Review goal:

The user found that v5 claimed cache/reasoning would be visible per turn, but the
notebook only showed footer-level metrics. The fix should:

1. Keep Bedrock signed-thinking handling safe. Display thinking text must never be
   synthesized back into Bedrock request history.
2. Add per-assistant-turn inline UI metrics: input/output, Cache R/W, cost,
   without-cache cost, saved amount, API calls, reasoning state.
3. Show captured thinking/reasoning inline under the assistant turn, collapsed or
   readable, without breaking the aggregate footer.
4. Avoid drift to tools, subagents, compaction, security, model request body, or
   cache-control.
5. Confirm the evidence file accurately states the gap, fix, and local tests.

Output exactly:

VERDICT: APPROVE or REQUEST_CHANGES
DRIFT DECISION: NO_DRIFT or DRIFT_FOUND

Then list findings. If you request changes, include exact file/line guidance.
