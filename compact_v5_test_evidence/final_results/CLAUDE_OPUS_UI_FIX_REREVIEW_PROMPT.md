# Claude Opus UI Fix Re-Review Prompt

You are an independent reviewer for the final SageAgent v5 SageMaker notebook UI fix.

Repository root:

```text
D:\Github\sagemaker-coding-agent
```

Do not edit files. Read the files and git history yourself.

Review target:

```text
git diff 7ac7e099c839109a5cf9be67b5f6308daee6f662..HEAD
```

Also inspect the current production zip:

```text
compact_v5.zip
```

Context:

- Your previous review returned `APPROVE_WITH_FIXES`.
- The worker applied the two low nits:
  1. Removed unused Cell 3 display import.
  2. Updated `chat.md` to explicitly require assignment-form launch: `ui = create_chat_ui()`.
- The earlier substantive fix was already present: `create_chat_ui()` clears output before constructing `V4WidgetChatUI(agent)`, then displays one root widget.

Reviewer task:

1. Confirm the low nits were fixed.
2. Confirm the zip is synchronized with current `chat.ipynb`, `chat.md`, and `ui/chat_ui.py`.
3. Confirm no new blocker was introduced.
4. Give a final ship decision for user visual retest.

Required output format:

```text
VERDICT: APPROVE | APPROVE_WITH_FIXES | REQUEST_CHANGES
SHIP DECISION: READY_FOR_USER_VISUAL_RETEST | NOT_READY
REVIEWED FILES:
- ...
FINDINGS:
- severity: file/path:line or command evidence - finding
EVIDENCE:
- exact commands or file checks you used
FINAL NOTE:
- short explanation for the user
```

