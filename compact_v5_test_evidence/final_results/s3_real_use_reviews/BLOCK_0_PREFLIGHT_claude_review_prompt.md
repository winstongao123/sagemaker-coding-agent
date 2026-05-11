You are an independent reviewer for compact_v5, a SageMaker notebook coding agent. You are not the implementer.

Active tree: compact_v5/
Do not assume compact_v5/compact_v5/ exists.

Architecture context:
- compact_v5/ui/chat_ui.py owns notebook UI rendering/live output.
- compact_v5/tools/ owns tool schemas/executors.
- compact_v5/security/ owns command and Python sandbox policy.
- compact_v5/core/query_engine.py owns LLM/tool loop, final-claim guard, and tool_search deferral.
- compact_v5/agent.py is the public Agent wrapper.
- compact_v5.zip is built from the flattened compact_v5/ tree.

Block 0 goal: preflight/drift baseline only. No source changes.

User-visible failure being fixed in later blocks:
Prompt: "list file and bucket structure of my s3".
Open blockers: S3 safe-read path broken, wrong Bedrock-only diagnosis, drift to local source tree inventory, noisy uncollapsed tool cards, thinking placement/collapse, high cost from retries/verbosity/tool_search/thinking.

Planned block order:
0. Preflight / drift baseline
1. S3 safe-read path
2. Accurate sandbox diagnosis
3. Intent drift guard
4. Tool cards collapse/grouping
5. Thinking placement/collapse
6. Cost controls for simple inventory tasks
7. Final integration / zip / real AWS smoke

Files changed: none.

Diff: compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_0_PREFLIGHT_diff.patch
Tests/evidence: compact_v5_test_evidence/final_results/s3_real_use_reviews/BLOCK_0_PREFLIGHT_tests.log

Review tasks:
1. Check whether the block order is scoped and safe.
2. Check whether active tree assumptions are correct and no stale nested-path assumption is present.
3. Check whether this baseline is sufficient to begin Block 1.
4. Return one verdict only: APPROVE, APPROVE_WITH_NITS, REQUEST_CHANGES, or BLOCKED.
5. List HIGH/MEDIUM/LOW findings with file/line references where possible.
