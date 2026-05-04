# Compaction Resume Checklist

Status: ACTIVE
Created: 2026-05-04

Use this after context compaction, terminal interruption, new worker session, or
any moment where chat memory may be incomplete.

## Goal

The worker must be able to pick up exactly what remains without trusting chat
memory.

## Required Resume Steps

1. Change to repo root:

   `D:\Github\sagemaker-coding-agent`

2. Treat chat, terminal scrollback, and compacted summaries as hints only.
   Do not implement, review, or close from memory.

3. Reread persistent control files:

   - `compact_v5/_status/v5_completion_audit/06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md`
   - `compact_v5/_status/v5_completion_audit/PS_WORKER_REVIEWER_DECISION.md`
   - `compact_v5/_status/v5_completion_audit/CLAUDE_REVIEWER_BASE_PROMPT.md`
   - `compact_v5/_status/v5_completion_audit/00_MASTER_PROTOCOL.md`
   - `compact_v5/_status/v5_completion_audit/03_LEDGER_SCHEMA.md`
   - `compact_v5/_status/PS_AGENT_SELF_REFLECTION.md`
   - `compact_v5/_status/v5_completion_audit/STATUS.md`
   - `compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md`

4. Identify the current block from:

   - `compact_v5/_status/v5_completion_audit/STATUS.md`
   - latest `compact_v5/_status/v5_completion_audit/blocks/<BLOCK>/STATUS.md`
   - latest modified block folder

5. For that block, reread:

   - `blocks/<BLOCK>/LEDGER.md`
   - `blocks/<BLOCK>/STATUS.md`
   - `blocks/<BLOCK>/TESTS.md`
   - `blocks/<BLOCK>/CHANGELOG.md`
   - `blocks/<BLOCK>/DECISIONS.md`
   - `blocks/<BLOCK>/WORKER_SELF_REVIEW.md`
   - `blocks/<BLOCK>/REVIEWER_VERDICT.md`
   - `blocks/<BLOCK>/PROMPTS.md`

6. Recompute remaining work mechanically:

   ```powershell
   py -3.11 compact_v5\_status\scripts\scope_audit.py --block <BLOCK>
   ```

7. Compare the scope audit result against the block heartbeat:

   - expected rows
   - ledger rows
   - shipped/partial/missing counts
   - ship-blocking row list
   - current task
   - last completed action
   - next 3 todo items

8. Inspect latest prompt/review/log artifacts:

   - newest `prompts/block-<block>-*.md`
   - newest `reviews/block-<block>-*.md`
   - newest `logs/block-<block>-*.log`

9. Inspect the worktree:

   ```powershell
   git status --short
   ```

   Do not revert or overwrite existing changes. If uncommitted changes touch
   the current block, inspect them and continue with them.

10. Resume from files only:

   - If ledger/status and scope audit agree, continue the next todo.
   - If they disagree, stop and write
     `blocks/<BLOCK>/RESUME_CONFLICT.md` before coding.
   - If there is an unresolved Claude finding, resolve/dispute/re-review before
     claiming closure.

11. Before sending the next Claude review after resume, verify the prompt
    includes `CLAUDE_REVIEWER_BASE_PROMPT.md` and instructs Claude to reread
    `SYNTHESIS_MASTER.md` directly before trusting worker context.

## Required Heartbeat Fields

Every active block `STATUS.md` must contain:

- current task
- last completed action
- next 3 todo items
- review attempts recorded
- ship-blocking row count
- blocker or human decision needed

## Rule

After compaction, never continue from memory. Continue from files plus
`scope_audit.py`.

If the worker cannot prove the current block, remaining rows, latest usable
Claude verdict, and next todo from files, it must stop and write
`blocks/<BLOCK>/RESUME_CONFLICT.md`.
