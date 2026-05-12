You are an independent reviewer using Claude CLI subscription auth. Do not assume prior context.

Repository: d:/Github/sagemaker-coding-agent
Branch: v5-build

Task: Review whether the documented fix plan for compact_v5's S3 follow-up tool-discipline failure is complete enough for a worker to implement.

Failure transcript summary:
1. User asked for S3 structure. v5 used aws_s3_list and produced bucket/prefix/object inventory.
2. User then asked: "pick two fiels to invesagte adn tell me hwat you found".
3. Instead of reusing already listed objects or asking which bucket, v5 fired multiple aws_s3_list calls and broadly rescanned S3.

Please review these docs:
- compact_v5_test_evidence/final_results/S3_FOLLOWUP_TOOL_DISCIPLINE_ISSUES_20260512.md
- compact_v5_test_evidence/final_results/S3_FOLLOWUP_TOOL_DISCIPLINE_WORKER_PROMPT_20260512.md

Also inspect relevant code enough to judge coverage:
- compact_v5/tools/aws_s3_list.py
- compact_v5/core/parallel_dispatch.py
- compact_v5/core/query_engine.py
- compact_v5/prompt/tool_classes.md
- compact_v5/ui/chat_ui.py
- compact_v5/runtime/state.py
- compact_v5/runtime/config.py
- compact_v5/tools/v4_documents.py

Questions:
1. Are the documented root causes accurate?
2. Are the proposed blocks sufficient to prevent this failure class?
3. Are any required fixes missing?
4. Are any blocks over-scoped or risky?
5. Is the worker prompt clear enough, including Claude CLI subscription review instructions?

Return one of:
- APPROVE: plan is complete enough for worker execution; list optional minor suggestions only.
- REQUEST_CHANGES: list exact missing required blocks or corrections.

Keep the answer concise but specific.
