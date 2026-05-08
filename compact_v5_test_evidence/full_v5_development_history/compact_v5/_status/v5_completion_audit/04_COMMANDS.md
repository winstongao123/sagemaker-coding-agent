# Commands

Run from repo root:

```powershell
cd D:\Github\sagemaker-coding-agent
```

## CLI Availability

Checked 2026-05-04:

```powershell
claude --version
# 2.1.119 / 2.1.126 observed across sessions

codex --version
# codex-cli 0.128.0
```

Claude reviewer smoke validation initially failed with `Credit balance is too
low` because the worker subprocess took the API-credit path instead of the
Claude Code subscription path. For reviewer automation on Windows/PowerShell,
use explicit `C:\Users\winst\AppData\Roaming\npm\claude.cmd`, temporarily clear
`ANTHROPIC_API_KEY` for the child process, use `--setting-sources user`, and do
not use `--add-dir` or `--permission-mode bypassPermissions`.

## Start Codex Worker

Codex is worker-only in this redo. Do not use Codex CLI as reviewer and do not
spawn nested `codex exec`.

```powershell
codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -m gpt-5.5 -c model_reasoning_effort="high" -C D:\Github\sagemaker-coding-agent - < compact_v5\_status\v5_completion_audit\06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md
```

## Claude Reviewer Smoke Test

Use this before the first review in a new terminal/session:

```powershell
$old=$env:ANTHROPIC_API_KEY; Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue; "Reply exactly: CLAUDE_REVIEWER_READY subscription_path_smoke" | C:\Users\winst\AppData\Roaming\npm\claude.cmd -p --model opus --effort xhigh --permission-mode dontAsk --setting-sources user --settings compact_v5\_status\v5_completion_audit\claude-reviewer-settings.json --tools "" --output-format text; if ($old) { $env:ANTHROPIC_API_KEY=$old }
```

Expected output includes `CLAUDE_REVIEWER_READY` and the active Opus alias.

## Direct Claude Review Pattern

The worker must generate a fresh review prompt under `prompts/`. Every prompt
must include the full contents of `CLAUDE_REVIEWER_BASE_PROMPT.md` plus the
current block/changelist context.

The worker then runs Claude directly and saves stdout/stderr:

```powershell
$prompt="compact_v5\_status\v5_completion_audit\prompts\<fresh-prompt>.md"
$out="compact_v5\_status\v5_completion_audit\reviews\<review-output>.md"
$log="compact_v5\_status\v5_completion_audit\logs\<review-log>.log"
$old=$env:ANTHROPIC_API_KEY; Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
Get-Content -Raw $prompt | C:\Users\winst\AppData\Roaming\npm\claude.cmd -p --model opus --effort xhigh --permission-mode dontAsk --setting-sources user --settings compact_v5\_status\v5_completion_audit\claude-reviewer-settings.json --tools "Read,Grep,Glob,Bash" --disallowedTools "Edit,Write,NotebookEdit,Bash(codex *),Bash(git commit *),Bash(git push *),Bash(git reset *),Bash(git checkout *)" --output-format text 2> $log | Tee-Object -FilePath $out
if ($old) { $env:ANTHROPIC_API_KEY=$old }
```

A usable review must contain `VERDICT:` and `SHIP DECISION:`.

## Baseline Gate

```powershell
git status --short
git rev-parse HEAD
git tag --list "v5.0.1-block*" --sort=creatordate
py -3.11 compact_v5\_status\scripts\r_tier_gate.py --repo-root .
```

Current known gate state as of 2026-05-04: local no-AWS marker/cost gate passes.
R6-R16, R18-E1..E15, and R19-U1..U10 are materialized as zero-cost readiness
specs in `MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py`. This is
not AWS pass evidence.

## Scope Completeness Gate

Run for one block:

```powershell
py -3.11 compact_v5\_status\scripts\scope_audit.py --block A
```

Strict wrapper, suitable before any block close claim:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File compact_v5\_status\scripts\verify_scope_completeness.ps1 -Block A
```

Run all blocks as a summary:

```powershell
py -3.11 compact_v5\_status\scripts\scope_audit.py --all --summary
```

## Useful Audit Commands

```powershell
rg -n "A-16|A-25|Block A|microcompact|cold-cache|tool_result" compact_v5
Get-Content compact_v5\_status\v5_completion_audit\ledger\CLAUDE_REVIEW_MATRIX.md
Get-Content compact_v5\_status\v5_completion_audit\blocks\A\STATUS.md
Get-Content compact_v5\_status\v5_completion_audit\blocks\A\REVIEWER_VERDICT.md
```

Run one block test file:

```powershell
cd compact_v5\MAIN\agent
py -3.11 -m pytest tests\integration\test_block_a.py -q
```

## Commands The Worker Must Not Run

- Codex CLI review
- nested `codex exec`
- AWS/R-tier spend commands
- `git reset`
- `git checkout`
- `git add -A`
- `git commit`, `git push`, or `git tag` until a block is fully approved and
  the git close plan is explicitly allowed
