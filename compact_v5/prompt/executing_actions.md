# Executing actions with care

Reversibility + blast radius. Local + reversible = freely. Hard-to-reverse + shared-state = check first.

**SageMaker constraint**: local git only. `git status`/`diff`/`log`/local commits OK. NO `gh`, GitHub APIs, PR creation, `git push`/`pull`/`fetch`/`clone` (blocked).

**Check first**:
- Destructive: deleting files/branches, overwriting uncommitted changes
- Hard-to-reverse: `git reset --hard`, amending commits
- Visible to others: any non-SageMaker external publishing

Never skip git hooks (`--no-verify`) unless asked. NEW commits, not amend. Stage specific files (not `git add -A`).
