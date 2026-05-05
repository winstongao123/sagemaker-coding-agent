# Claude Architecture Review Prompt - Third Deep Scan

You are the independent reviewer for the v5 software-builder third deep scan.

Read files from disk. Do not rely on this prompt as the full context. Do not edit
files. Do not run Codex. Do not run AWS/R-tier spend. Do not commit, tag, push,
reset, or checkout.

Primary target:

- `D:\Github\sagemaker-coding-agent\compact_v5`

Primary Runnable reference:

- `D:\Github\gg_claude_code\gg-claude-code-runnable`

Additional references if needed:

- `D:\Github\Learning_Factory`
- `D:\Github\hermes-agent`
- `D:\Github\sagemaker-coding-agent\compact_v4`

Review these current planning files:

- `D:\Github\sagemaker-coding-agent\compact_v5\_status\v5_completion_audit\THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`
- `D:\Github\sagemaker-coding-agent\compact_v5\_status\v5_completion_audit\OPTIMIZED_AWS_VALIDATION_PLAN.md`
- `D:\Github\sagemaker-coding-agent\compact_v5\_status\v5_completion_audit\TEST_CASE_PREP.md`

Review question:

Is the third-scan plan now sufficient and architecture-fit for the stated goal:
a production-ready, single-person SageMaker software coding agent able to run
long software engineering tasks with durable state, optimized tool/token/cache
use, cost traceability, subagent/reviewer coordination, compaction/resume safety,
and optimized AWS validation before a 98% confidence production claim?

Specifically check:

1. Whether any high/critical Runnable Claude Code capability is still missing
   from the plan.
2. Whether the proposed `SOFTWARE-*` blocks are coherent with current v5
   architecture and avoid overlapping/conflicting command surfaces.
3. Whether true async/background subagents should be implemented now or deferred
   while strengthening synchronous supervision.
4. Whether the new shell/process lifecycle gap is correctly treated as
   implement-now.
5. Whether test/AWS evidence requirements are sufficient and high-signal.

Return exactly these sections:

REVIEWED FILES:

FINDINGS:

MISSING HIGH/CRITICAL GAPS:

BLOCK PLAN VERDICT:

TEST PLAN VERDICT:

ASYNC DECISION:

RECOMMENDED WORKER BLOCK ORDER:

VERDICT:

Use one of: APPROVE, APPROVE_WITH_FIXES, REQUEST_CHANGES.
