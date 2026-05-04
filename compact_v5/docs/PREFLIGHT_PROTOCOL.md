# Preflight Protocol

Run this zero-cost preflight before starting a block implementation slice and
again before handing a block to Claude review.

## 1. Hooks

- Confirm no active hook or wrapper will run Codex review, nested `codex exec`,
  AWS, SAM, git tag, git reset, git checkout, force push, or unapproved writes.
- Confirm generated review prompts include
  `compact_v5/_status/v5_completion_audit/CLAUDE_REVIEWER_BASE_PROMPT.md`.

## 2. Permissions

- Confirm the task is local and zero-cost.
- Stop before AWS/R-tier spend, git tag/final-ready approval, explicit defer/drop
  decisions, broad architecture changes, destructive git, or unfixable reviewer
  findings.
- For Claude review, clear `ANTHROPIC_API_KEY` only for the subprocess and use
  the subscription-auth command shape documented in
  `PS_CLI_WOKER_DESIGN/CLAUDE_REVIEWER_AUTH.md`.

## 3. Reviewer

- Claude is the independent read-only reviewer.
- Every prompt must require Claude to read canonical context from disk first and
  reconstruct block scope from `SYNTHESIS_MASTER.md`.
- Failed handoffs still get prompt, stdout, stderr/log, matrix, verdict, and
  heartbeat artifacts.

## 4. Tree

- Record `git status --short`.
- Stage only specific files for checkpoint commits.
- Never use `git add -A`, force push, reset, or checkout.
- Do not revert unrelated dirty files.

## 5. Session-State

- Update `blocks/<BLOCK>/STATUS.md` before long work and before/after Claude
  handoffs.
- Rerun `scope_audit.py --block <BLOCK>` after compaction or before any close
  claim.
- Continue from files plus `scope_audit.py`, not terminal scrollback or memory.

