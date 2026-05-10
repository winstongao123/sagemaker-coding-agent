You are an independent release reviewer. Read files from disk; do not rely on this prompt as evidence.

Repo: D:\Github\sagemaker-coding-agent

Review the current local changes for v5 production UI/security after a live SageMaker finding.

Read at minimum:
- compact_v5/ui/chat_ui.py
- compact_v5/chat.md
- compact_v5/prompt/security.md
- compact_v5/docs/README.md
- compact_v5/docs/PS_PS_PS_Check_v5_vs_v4.md
- compact_v5/docs/PS_TEST_REVIEW_FINAL.md
- compact_v4/MAIN/agent/sagemaker_agent.py lines around the v4 markdown renderer and chat UI

Validate:
1. v5 now has a visible live Bedrock-only control and footer/mode line explaining S3 blocked vs S3 read mode.
2. v5 preserves the security intent: Bedrock-only blocks S3; when disabled, S3 read/list may be allowed but S3 delete/admin stays blocked.
3. v5 assistant markdown rendering is materially closer to v4 and supports bold, code fences, bullets, numbered lists, headers, and markdown tables without unsafe raw HTML injection.
4. Prompt-cache/cost/thinking visibility is clearer in footer and per-turn metrics.
5. The fix does not introduce obvious functional drift or break v5 architecture.
6. Documentation records the live finding, why earlier tests missed it, and what was fixed.

Return exactly these sections:
VERDICT: APPROVE or REQUEST_CHANGES
DRIFT_DECISION: NO_DRIFT or DRIFT_FOUND
SECURITY_DECISION: PASS or FAIL
DOC_DECISION: PASS or FAIL
FINDINGS:
- severity, file/path, exact issue, required fix
TEST_GAPS:
- remaining zero-cost or visual checks needed
FINAL_NOTE:
