# Commands

Run from repo root:

```powershell
cd D:\Github\sagemaker-coding-agent
```

## Start Worker

```powershell
codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -m gpt-5.5 -c model_reasoning_effort="high" -C D:\Github\sagemaker-coding-agent - < compact_v5\_status\v5_completion_audit\06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md
```

## Claude Smoke Test

```powershell
$old=$env:ANTHROPIC_API_KEY; Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue; claude -p --model opus --effort xhigh --permission-mode dontAsk --setting-sources user --settings compact_v5\_status\v5_completion_audit\claude-reviewer-settings.json --tools "" --add-dir D:\Github\sagemaker-coding-agent --output-format text "Say CLAUDE_REVIEWER_READY and the model alias you are using. Do not run tools."; if ($old) { $env:ANTHROPIC_API_KEY=$old }
```

## Monitor Review Output

```powershell
Get-ChildItem compact_v5\_status\v5_completion_audit\reviews -File |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 10 Name,Length,LastWriteTime
```

Healthy review file:

- non-zero length
- contains `VERDICT:`
- contains `SHIP DECISION:`
- is not just a plan, stale prompt complaint, or sandbox complaint

## Monitor State

```powershell
Get-Content compact_v5\_status\v5_completion_audit\ledger\CLAUDE_REVIEW_MATRIX.md
Get-Content compact_v5\_status\v5_completion_audit\blocks\A\STATUS.md
Get-Content compact_v5\_status\v5_completion_audit\blocks\A\REVIEWER_VERDICT.md
```

## Local No-AWS Test Gate

```powershell
py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root .
```

## Scope Completeness Gate

```powershell
py -3.11 compact_v5\_status\scripts\scope_audit.py --block A
powershell -NoProfile -ExecutionPolicy Bypass -File compact_v5\_status\scripts\verify_scope_completeness.ps1 -Block A
```

## Forbidden Commands

- `codex exec review`
- nested `codex exec`
- AWS/R-tier spend commands
- `git reset`
- `git checkout`
- `git add -A`
- `git tag` unless explicitly approved
- `git push --force`

## Required Block-Close Git Checkpoint

After a block is clean, commit and push with a specific file list:

```powershell
git add -- <specific block files only>
git commit -m "v5/block-<block>: <summary>"
git push sageagent v5-build
```

Never stage unrelated dirty files. Update `blocks/<BLOCK>/GIT_CLOSE_PLAN.md`
with the staged file list, commit SHA, push target, and post-push status.
