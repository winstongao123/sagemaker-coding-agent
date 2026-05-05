# Claude Reviewer Auth Rule

Status: ACTIVE
Created: 2026-05-04

The independent Claude reviewer must use the user's Claude Code subscription
auth path, not an API-key credit path.

## Problem Observed

The interactive Claude Code terminal showed:

```text
Claude Code ... Opus 4.7 ... Claude Max
```

But the worker-spawned non-interactive review returned:

```text
Credit balance is too low
```

Local environment inspection showed `ANTHROPIC_API_KEY` is set. A spawned
non-interactive reviewer can inherit that variable and route through API billing
instead of the Claude Max subscription auth path.

## Required Reviewer Invocation Rule

Before running Claude review from Codex/PowerShell:

1. Do not use `--bare`.
2. Do not pass API-key-only settings.
3. Temporarily clear API-key environment variables for the Claude subprocess.
4. Keep user settings enabled so Claude Code can use its normal subscription
   login. The repo-specific reviewer settings file is still passed explicitly
   with `--settings`.
5. In PowerShell, do not pass `--setting-sources user,project,local`; the comma
   list can be split/mangled by the wrapper. The tested working form is
   `--setting-sources user`.
6. Do not request sandbox/approval escalation for the Claude reviewer command.
   Run the non-escalated read-only command shape below. If the non-escalated
   command fails due network/auth, record and retry per `FAILURE_MODES.md`.
   Escalation can be denied as private-repo egress before Claude executes, which
   produces no usable review.
7. Use `claude.cmd` or `claude -p` with the saved prompt piped through stdin.
   The command must remain read-only: allowed tools are `Read,Grep,Glob,Bash`;
   disallowed tools include `Edit`, `Write`, `NotebookEdit`, git
   commit/push/tag/reset/checkout, `codex`, `aws`, and `sam`.

## Review Context Boundary

Codex must not paste or bundle repository file contents into the Claude prompt
as a replacement for independent review. The prompt should give Claude the
target block, canonical row ids, changed-file paths, artifact paths, command
outputs/log paths, and a concise summary of what the worker believes changed.

Claude Code is responsible for locating and reading the relevant files itself
through read-only tools before producing `REVIEWED ROWS`, `VERDICT`, and
`SHIP DECISION`. This preserves independence while avoiding the misleading
pattern of treating the worker prompt as the source of truth.

## Tested Smoke Result

This command shape was tested from `D:\Github\sagemaker-coding-agent` with
`ANTHROPIC_API_KEY` temporarily cleared:

```text
CLAUDE_REVIEWER_READY subscription_path_smoke
```

Saved evidence:

- `compact_v5/_status/v5_completion_audit/logs/claude-auth-smoke-20260504-163144.out.txt`
- `compact_v5/_status/v5_completion_audit/logs/claude-auth-smoke-20260504-163144.err.txt`

PowerShell pattern:

```powershell
$savedAnthropicApiKey = $env:ANTHROPIC_API_KEY
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
try {
  Get-Content -Raw $promptPath | claude -p `
    --model opus `
    --effort xhigh `
    --permission-mode dontAsk `
    --setting-sources user `
    --settings compact_v5/_status/v5_completion_audit/claude-reviewer-settings.json `
    --tools "Read,Grep,Glob,Bash" `
    --disallowedTools "Edit,Write,NotebookEdit,Bash(git commit*),Bash(git push*),Bash(git tag*),Bash(git reset*),Bash(git checkout*),Bash(codex*),Bash(aws*),Bash(sam*)" `
    > $reviewPath 2> $logPath
}
finally {
  if ($null -ne $savedAnthropicApiKey) {
    $env:ANTHROPIC_API_KEY = $savedAnthropicApiKey
  }
}
```

If Claude still returns `Credit balance is too low` after clearing
`ANTHROPIC_API_KEY`, run the smoke command in `COMMANDS.md` or start an
interactive `claude` session in the same terminal to verify the terminal can see
the Claude Max login, then retry the saved prompt as a new iteration.

If Claude returns `Invalid setting source: user project local`, record that as a
command-shape failure and retry with `--setting-sources user`.

## Recording Rule

If a review fails due auth/billing routing, record it as:

`NO_VERDICT / HANDOFF_FAILED_AUTH_ROUTING`

Do not count it as a review verdict.

If a review fails because the command was malformed, record it as:

`NO_VERDICT / HANDOFF_FAILED_COMMAND_SHAPE`

Do not count it as a review verdict.
