# Git Checkpoint Policy

Status: ACTIVE
Created: 2026-05-04

The user requires git to be updated regularly so progress can be tracked and
rolled back.

## Required Policy

After each block reaches a clean close state, the worker must create a
specific-file commit and push it to the `sageagent` remote on branch `v5-build`.

A clean close state means:

1. Block ledger has every canonical row from `SYNTHESIS_MASTER.md`.
2. No ship-blocking rows remain.
3. `scope_audit.py --block <BLOCK>` passes.
4. Local relevant tests pass.
5. Claude closure review is usable and has `SHIP DECISION:
   READY_FOR_BLOCK_CLOSE_REVIEW` or stronger.
6. Local/low-risk reviewer findings inside the current block are fixed
   automatically, or explicitly recorded as user-approved follow-up.
7. Block docs, matrix, prompts, reviews, logs, status, changelog, tests, and
   self-review artifacts are updated.
8. Documentation consistency check passes:
   - `blocks/<BLOCK>/STATUS.md` review-attempt count matches
     `blocks/<BLOCK>/REVIEWER_VERDICT.md`.
   - latest usable Claude verdict and ship decision match the latest usable
     review artifact.
   - current blocking-row count matches `scope_audit.py --block <BLOCK>`.
   - `blocks/<BLOCK>/LEDGER.md` has no stale `NOT_YET_CLAUDE_REVIEWED` or
     `reviewer_verdict` = `pending` after a usable Claude approval.
   - `git_evidence` remains an honest pending value before the close commit
     and is replaced with the actual commit SHA in the checkpoint evidence
     update after push.

Before every close commit, grep the block artifacts for stale markers and
either fix them or explicitly document why they are still valid:

```powershell
rg -n "NOT_YET_CLAUDE_REVIEWED|reviewer_verdict.*pending|Review attempts counted.*0|pending Block .* checkpoint" compact_v5/_status/v5_completion_audit/blocks/<BLOCK>
```

## Checkpoint Commits During Long Blocks

For large blocks, the worker may also create checkpoint commits after a
reviewer-approved implementation slice, as long as:

- the slice has tests and artifacts updated,
- the commit message clearly says it is a checkpoint and the block is not
  closed,
- no AWS/R-tier spend occurred,
- no tag is created,
- only specific files are staged.

## Git Safety Rules

- Never use `git add -A`.
- Stage only a specific file list for the block/slice.
- Do not stage unrelated dirty files.
- Do not revert unrelated existing user changes.
- Push only to `sageagent` remote, branch `v5-build`.
- Do not create tags unless the user explicitly approves the tag.
- Do not use `git reset`, `git checkout`, or force push.

## Required Git Evidence

Each block close must update `blocks/<BLOCK>/GIT_CLOSE_PLAN.md` with:

- exact files staged,
- commit message,
- commit SHA,
- push remote and branch,
- `git status --short` after commit/push,
- note that no tag was created.

If commit or push fails, record the failure in `blocks/<BLOCK>/STATUS.md` and
do not proceed silently.
