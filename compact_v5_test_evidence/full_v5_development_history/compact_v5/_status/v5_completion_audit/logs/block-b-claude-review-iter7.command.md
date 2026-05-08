# Block B Claude Review Iter7 Command Note

Date: 2026-05-04
Purpose: normal non-escalated read-only Claude closure review retry after iter6 returned `ConnectionRefused`.

Command shape:

```powershell
$savedAnthropicApiKey = $env:ANTHROPIC_API_KEY
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
try {
  Get-Content -Raw compact_v5/_status/v5_completion_audit/prompts/block-b-claude-review-iter7-prompt.md | claude.cmd -p `
    --model opus `
    --effort xhigh `
    --permission-mode dontAsk `
    --setting-sources user `
    --settings compact_v5/_status/v5_completion_audit/claude-reviewer-settings.json `
    --tools "Read,Grep,Glob,Bash" `
    --disallowedTools "Edit,Write,NotebookEdit,Bash(git commit*),Bash(git push*),Bash(git tag*),Bash(git reset*),Bash(git checkout*),Bash(codex*),Bash(aws*),Bash(sam*)" `
    > compact_v5/_status/v5_completion_audit/reviews/block-b-claude-review-iter7.md `
    2> compact_v5/_status/v5_completion_audit/logs/block-b-claude-review-iter7.log
}
finally {
  if ($null -ne $savedAnthropicApiKey) {
    $env:ANTHROPIC_API_KEY = $savedAnthropicApiKey
  }
}
```

No sandbox/approval escalation requested. `ANTHROPIC_API_KEY` is cleared only for the Claude subprocess and restored afterward.
