# Claude Review Prompt: BLOCK_6_COST_CONTROLS_SIMPLE_S3_INVENTORY

You are reviewing only Block 6 of compact_v5 S3 real-use fixes.

Repo: d:/Github/sagemaker-coding-agent
Active runtime tree: compact_v5/ (flattened). Do not consider compact_v5/compact_v5/ as active.

Block goal:
- Cost controls for simple S3 inventory tasks from the transcript: blocked retries, verbosity, tool_search overhead, and Thinking ON in deployed run.
- The fix must measure/control causes before optimizing and must not blindly change model, cache, prompt compaction, or broad architecture.

Changed files for this block:
- compact_v5/agent.py
- compact_v5/core/query_engine.py
- compact_v5/runtime/config.py
- compact_v5/ui/chat_ui.py
- compact_v5/prompt/tool_classes.md
- compact_v5/tests/test_s3_cost_controls.py

Please review:
- compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_6_COST_CONTROLS_SIMPLE_S3_INVENTORY_diff.patch
- compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_6_COST_CONTROLS_SIMPLE_S3_INVENTORY_tests.log
- compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_6_COST_CONTROLS_SIMPLE_S3_INVENTORY_status.md

Questions:
1. Does this block preserve v5 architecture?
2. Any code drift from the scoped cost controls for simple S3 inventory tasks?
3. Any regression risk to Bedrock request shape, thinking signatures, tool dispatch, compaction, security, final-claim guard, subagent receipts, or cost/cache accounting?
4. Are tests/checks sufficient for this block?
5. Verdict: APPROVE / REQUEST_CHANGES

If you find HIGH or MEDIUM issues, identify them explicitly with file/line references and required fixes.
