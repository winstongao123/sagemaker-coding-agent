You are an independent reviewer using Claude CLI subscription auth. Do not assume prior context.

Repository: d:/Github/sagemaker-coding-agent
Branch: v5-build
Goal: compact_v5 must preserve compact v4's ask_user notebook behavior. When the model/tool asks the human for clarification mid-run, v5 should show a visible in-notebook prompt, allow Submit/Skip, support using the main Send button as a fallback, then resume the agent run. This must be inside the one combined v5 UI, not a separate config block.

Please review the diff in compact_v5_test_evidence/final_results/ask_user_ui_reviews/ROUND_1_ASK_USER_UI.diff plus these files:
- compact_v5/agent.py
- compact_v5/core/query_engine.py
- compact_v5/ui/chat_ui.py
- compact_v5/tools/ask_user.py
- compact_v5/tests/test_ui_ask_user_smoke.py

Reference behavior from v4/v3 archive:
- _archive/compact_v3/ship/sagemaker_agent.py ask_user handlers around request_user_input: visible Agent Question box, Submit/Skip, 5 minute timeout, main Send fallback, stop resolves pending input.

Check for:
1. Does ask_user provider get passed from UI -> Agent.run -> QueryEngine.run -> tool.execute context?
2. Does the UI display correctly in the combined v5 UI, not as console input?
3. Does Submit work?
4. Does Skip work?
5. Does main Send fallback work while the agent is running?
6. Does Stop resolve a pending ask_user wait?
7. Any deadlock, regression, or architectural drift from v4/v5?
8. Are tests adequate for this patch?

Return one of:
- APPROVE: no HIGH/MEDIUM blockers
- REQUEST_CHANGES: list exact blockers

Keep it concise but specific.
