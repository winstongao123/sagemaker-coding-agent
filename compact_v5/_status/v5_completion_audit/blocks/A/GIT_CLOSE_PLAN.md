# Block A Git Close Plan

Status: READY_FOR_SPECIFIC_FILE_COMMIT_PUSH
Date: 2026-05-04

Block A has 43/43 shipped rows, 0 ship-blocking rows, and Claude iter11
returned `APPROVE` with `SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW`.

The three LOW iter10 findings A-22, A-30, and A-37 were fixed and re-reviewed
by Claude iter11. Per latest user instruction, create a commit and push branch
`v5-build` to `sageagent`; do not tag unless the user explicitly approves.

Use only a specific file list. Never use `git add -A`.

## Exact Staged File List For Checkpoint

These paths are the exact files to stage for the Block A checkpoint. The
staging command must pass this list explicitly; no wildcard, directory add, or
`git add -A`.

```text
AGENTS.md
compact_v5/MAIN/agent/core/compactor.py
compact_v5/MAIN/agent/core/query_engine.py
compact_v5/MAIN/agent/runtime/bedrock_client.py
compact_v5/MAIN/agent/runtime/config.py
compact_v5/MAIN/agent/skills/manager.py
compact_v5/MAIN/agent/tests/integration/test_block_a.py
compact_v5/MAIN/agent/tests/r_tier/test_r4_cold_cache.py
compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py
compact_v5/MAIN/agent/tools/_file_read_tracking.py
compact_v5/_status/V5_BUILD_STATUS.md
compact_v5/_status/V5_DESIGN_DECISIONS.md
compact_v5/_status/V5_RUNNABLE_PORT_LOG.md
compact_v5/_status/scripts/scope_audit.py
compact_v5/_status/scripts/verify_scope_completeness.ps1
compact_v5/_status/v5_completion_audit/00_MASTER_PROTOCOL.md
compact_v5/_status/v5_completion_audit/03_LEDGER_SCHEMA.md
compact_v5/_status/v5_completion_audit/04_COMMANDS.md
compact_v5/_status/v5_completion_audit/06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md
compact_v5/_status/v5_completion_audit/CLAUDE_REVIEWER_BASE_PROMPT.md
compact_v5/_status/v5_completion_audit/PS_COMPACTION_RESUME_CHECKLIST.md
compact_v5/_status/v5_completion_audit/PS_WORKER_REVIEWER_DECISION.md
compact_v5/_status/v5_completion_audit/README.md
compact_v5/_status/v5_completion_audit/STATUS.md
compact_v5/_status/v5_completion_audit/TEST_CASE_PREP.md
compact_v5/_status/v5_completion_audit/blocks/A/BASELINE.md
compact_v5/_status/v5_completion_audit/blocks/A/CHANGELOG.md
compact_v5/_status/v5_completion_audit/blocks/A/DECISIONS.md
compact_v5/_status/v5_completion_audit/blocks/A/GIT_CLOSE_PLAN.md
compact_v5/_status/v5_completion_audit/blocks/A/LEDGER.md
compact_v5/_status/v5_completion_audit/blocks/A/MEMORY_UPDATE.md
compact_v5/_status/v5_completion_audit/blocks/A/PROMPTS.md
compact_v5/_status/v5_completion_audit/blocks/A/REVIEWER_VERDICT.md
compact_v5/_status/v5_completion_audit/blocks/A/REVIEW_LOOP_BLOCKED.md
compact_v5/_status/v5_completion_audit/blocks/A/SELF_REFLECTION.md
compact_v5/_status/v5_completion_audit/blocks/A/STATUS.md
compact_v5/_status/v5_completion_audit/blocks/A/TESTS.md
compact_v5/_status/v5_completion_audit/blocks/A/WORKER_SELF_REVIEW.md
compact_v5/_status/v5_completion_audit/blocks/README.md
compact_v5/_status/v5_completion_audit/claude-reviewer-settings.json
compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md
compact_v5/_status/v5_completion_audit/ledger/README.md
compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter1.log
compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter2.log
compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter3.log
compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter4.log
compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter5.log
compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter6.log
compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter6.prompt.stdin.tmp
compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter7.log
compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter8.log
compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter9.log
compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter10.log
compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter11.log
compact_v5/_status/v5_completion_audit/logs/block-a-scope-audit-after-broad-helper-slice.log
compact_v5/_status/v5_completion_audit/logs/block-a-scope-audit-after-iter10-low-fixes.log
compact_v5/_status/v5_completion_audit/logs/block-a-scope-audit-after-remaining-rows.log
compact_v5/_status/v5_completion_audit/logs/block-a-scope-audit-before-next-implementation.log
compact_v5/_status/v5_completion_audit/logs/block-a-scope-audit-final-before-git.log
compact_v5/_status/v5_completion_audit/logs/claude-auth-smoke-20260504-162954.err.txt
compact_v5/_status/v5_completion_audit/logs/claude-auth-smoke-20260504-162954.out.txt
compact_v5/_status/v5_completion_audit/logs/claude-auth-smoke-20260504-163054.err.txt
compact_v5/_status/v5_completion_audit/logs/claude-auth-smoke-20260504-163054.out.txt
compact_v5/_status/v5_completion_audit/logs/claude-auth-smoke-20260504-163144.err.txt
compact_v5/_status/v5_completion_audit/logs/claude-auth-smoke-20260504-163144.out.txt
compact_v5/_status/v5_completion_audit/logs/codex-worker-write-iter0-block-a-codex-continue-after-claude-iter0.err.log
compact_v5/_status/v5_completion_audit/logs/codex-worker-write-iter0-block-a-codex-continue-after-claude-iter0.out.md
compact_v5/_status/v5_completion_audit/logs/scope-audit-block-a-2026-05-04.json
compact_v5/_status/v5_completion_audit/prompts/README.md
compact_v5/_status/v5_completion_audit/prompts/block-a-claude-review-2026-05-04.md
compact_v5/_status/v5_completion_audit/prompts/block-a-claude-review-iter7.md
compact_v5/_status/v5_completion_audit/prompts/block-a-claude-review-iter8.md
compact_v5/_status/v5_completion_audit/prompts/block-a-claude-review-iter11.md
compact_v5/_status/v5_completion_audit/prompts/block-a-claude-review-post-implementation-2026-05-04.md
compact_v5/_status/v5_completion_audit/prompts/block-a-codex-continue-after-claude-iter0.md
compact_v5/_status/v5_completion_audit/prompts/block-a-worker-ledger-2026-05-04.md
compact_v5/_status/v5_completion_audit/reviews/CLAUDE_CLI_VALIDATION.md
compact_v5/_status/v5_completion_audit/reviews/README.md
compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter1.md
compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter2.md
compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter3.md
compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter4.md
compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter5.md
compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter6.md
compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter7.md
compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter8.md
compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter9.md
compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter10.md
compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter11.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/CLAUDE_REVIEWER_AUTH.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/COMMANDS.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/CURRENT_STATUS.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/FAILURE_MODES.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/FLOW.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/FOLDER_MAP.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/GIT_CHECKPOINT_POLICY.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/LEARNING_FACTORY_ADAPTATION.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/PROGRESS_VISIBILITY.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/README.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/STATE_FILES.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/WORKER_HANDOFF_TEMPLATE.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/WORKER_LED_LOOP.md
compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/WORKER_REVIEWER_TRANSCRIPT_RULE.md
```

Current candidate files touched by Block A:

- `compact_v5/MAIN/agent/core/compactor.py`
- `compact_v5/MAIN/agent/core/query_engine.py`
- `compact_v5/MAIN/agent/runtime/bedrock_client.py`
- `compact_v5/MAIN/agent/runtime/config.py`
- `compact_v5/MAIN/agent/skills/manager.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_a.py`
- `compact_v5/MAIN/agent/tests/r_tier/test_r4_cold_cache.py`
- `compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py`
- `compact_v5/MAIN/agent/tools/_file_read_tracking.py`
- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md`
- `compact_v5/_status/V5_DESIGN_DECISIONS.md`
- `compact_v5/_status/V5_BUILD_STATUS.md`
- `compact_v5/_status/v5_completion_audit/STATUS.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/CHANGELOG.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/DECISIONS.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/GIT_CLOSE_PLAN.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/LEDGER.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/MEMORY_UPDATE.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/REVIEWER_VERDICT.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/STATUS.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/TESTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/WORKER_SELF_REVIEW.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/PROMPTS.md`
- `compact_v5/_status/v5_completion_audit/blocks/A/REVIEW_LOOP_BLOCKED.md`
- `compact_v5/_status/v5_completion_audit/prompts/block-a-claude-review-iter7.md`
- `compact_v5/_status/v5_completion_audit/prompts/block-a-claude-review-iter8.md`
- `compact_v5/_status/v5_completion_audit/prompts/block-a-claude-review-iter11.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter7.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter8.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter9.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter10.md`
- `compact_v5/_status/v5_completion_audit/reviews/block-a-claude-review-iter11.md`
- `compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter7.log`
- `compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter8.log`
- `compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter9.log`
- `compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter10.log`
- `compact_v5/_status/v5_completion_audit/logs/block-a-claude-review-iter11.log`
- `compact_v5/_status/v5_completion_audit/logs/block-a-scope-audit-after-broad-helper-slice.log`
- `compact_v5/_status/v5_completion_audit/logs/block-a-scope-audit-after-remaining-rows.log`
- `compact_v5/_status/v5_completion_audit/logs/block-a-scope-audit-after-iter10-low-fixes.log`
- `compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md`
- `compact_v5/_status/v5_completion_audit/PS_CLI_WOKER_DESIGN/GIT_CHECKPOINT_POLICY.md`
- `AGENTS.md`

Also include any Block A LOW-fix files/artifacts created after this plan.

Required close commands after LOW findings are resolved/accepted:

```powershell
git add -- <specific files only>
git commit -m "v5/block-a: complete compactor closure audit"
git push sageagent v5-build
```

After push, update this file with:

- exact staged file list
- commit SHA
- push result
- `git status --short`
- note: no tag created
