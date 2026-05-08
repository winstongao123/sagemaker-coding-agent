# Claude Final Review Prompt - Third Deep Scan Worker Readiness

You are the independent architecture reviewer for the v5.0.1 third deep scan
and worker continuation plan.

Read files from disk. Do not rely on this prompt as the full context. Do not
edit files. Do not run Codex. Do not run AWS/R-tier spend. Do not commit, tag,
push, reset, or checkout.

Primary target repo:

- `D:\Github\sagemaker-coding-agent`

Primary current v5 target:

- `D:\Github\sagemaker-coding-agent\compact_v5`

Primary Runnable reference:

- `D:\Github\gg_claude_code\gg-claude-code-runnable`

Additional references if needed:

- `D:\Github\Learning_Factory`
- `D:\Github\hermes-agent`
- `D:\Github\sagemaker-coding-agent\compact_v4`

Review these files:

- `compact_v5/_status/v5_completion_audit/THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`
- `compact_v5/_status/v5_completion_audit/reviews/third-deep-scan-claude-architecture-review-2026-05-05.md`
- `compact_v5/_status/v5_completion_audit/TEST_CASE_PREP.md`
- `compact_v5/_status/v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md`
- `compact_v5/_status/v5_completion_audit/STATUS.md`
- `compact_v5/_status/v5_completion_audit/BLOCK_ORDER_AND_COVERAGE.md`
- `compact_v5/_status/v5_completion_audit/06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md`

Question:

After the latest updates, is the third deep-scan architecture plan and
`SOFTWARE-*` worker block plan ready for Codex worker continuation?

Check specifically:

1. The exact Runnable source path is correct and primary.
2. No high/critical architecture gap from Runnable/Hermes/Learning Factory/v4 is
   missing from the plan.
3. The `SOFTWARE-*` blocks are coherent, ordered correctly, and do not add
   conflicting command surfaces.
4. The test/AWS updates are sufficient for the worker to update local tests and
   pre-AWS evidence contracts.
5. The worker can continue from files only without relying on chat memory.

Return exactly:

REVIEWED FILES:

FINDINGS:

MISSING HIGH/CRITICAL GAPS:

PLAN READINESS:

WORKER PROMPT READINESS:

VERDICT:

Use one of: APPROVE, APPROVE_WITH_FIXES, REQUEST_CHANGES.
