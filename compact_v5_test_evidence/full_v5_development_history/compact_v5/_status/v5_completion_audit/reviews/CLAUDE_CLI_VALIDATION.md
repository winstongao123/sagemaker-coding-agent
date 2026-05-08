# Claude CLI Validation

Date: 2026-05-04
Status: VALIDATED_SUBSCRIPTION_PATH

## Command Tried

```powershell
claude -p --model opus --effort high --permission-mode plan --add-dir D:\Github\sagemaker-coding-agent --max-budget-usd 0.20 --output-format text "Say CLAUDE_REVIEWER_READY and the model alias you are using."
```

## Result

```text
Credit balance is too low
```

## Interpretation

Claude Code CLI is installed and supports `--model` / `--effort`.

The first command failed because this shell had `ANTHROPIC_API_KEY` set. That
forced the API-credit path instead of the user's Claude Max subscription path.

## Successful Subscription Validation

Command:

```powershell
$old=$env:ANTHROPIC_API_KEY; Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue; claude -p --model opus --effort high --permission-mode plan --setting-sources local --settings compact_v5\_status\v5_completion_audit\claude-reviewer-settings.json --tools "" --add-dir D:\Github\sagemaker-coding-agent --output-format text "Say CLAUDE_REVIEWER_READY and the model alias you are using. Do not run tools."; if ($old) { $env:ANTHROPIC_API_KEY=$old }
```

Result:

```text
CLAUDE_REVIEWER_READY -- claude-opus-4-7
```

Conclusion: Claude Code reviewer is validated on the subscription path. Final
review commands must unset `ANTHROPIC_API_KEY` for the process and use the
hook-isolated settings file.
