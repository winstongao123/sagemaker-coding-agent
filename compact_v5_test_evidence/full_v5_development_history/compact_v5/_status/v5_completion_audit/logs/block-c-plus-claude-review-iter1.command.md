# Block C+ Claude Review Iter1 Command

Date: 2026-05-05

Purpose: run C+ closure review with Claude read-only after the pre-review smoke
passed.

Command shape:

```powershell
$old=$env:ANTHROPIC_API_KEY
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
try {
  Get-Content -Raw compact_v5/_status/v5_completion_audit/prompts/block-c-plus-claude-review-iter1.md | C:\Users\winst\AppData\Roaming\npm\claude.cmd -p --model opus --effort xhigh --permission-mode dontAsk --setting-sources user --settings compact_v5/_status/v5_completion_audit/claude-reviewer-settings.json --tools "Read,Grep,Glob,Bash" --disallowedTools "Edit,Write,NotebookEdit,Bash(git commit*),Bash(git push*),Bash(git tag*),Bash(git reset*),Bash(git checkout*),Bash(codex*),Bash(aws*),Bash(sam*)" --output-format text > compact_v5/_status/v5_completion_audit/reviews/block-c-plus-claude-review-iter1.md 2> compact_v5/_status/v5_completion_audit/logs/block-c-plus-claude-review-iter1.log
  exit $LASTEXITCODE
}
finally { if ($old) { $env:ANTHROPIC_API_KEY=$old } }
```

Result:

- Exit code: 0
- Review: `compact_v5/_status/v5_completion_audit/reviews/block-c-plus-claude-review-iter1.md`
- Stderr/log: `compact_v5/_status/v5_completion_audit/logs/block-c-plus-claude-review-iter1.log`
- Verdict: `APPROVE / SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW`
- Remaining ship-blocking rows: 0
