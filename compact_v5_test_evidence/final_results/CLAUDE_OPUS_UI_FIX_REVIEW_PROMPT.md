# Claude Opus UI Fix Review Prompt

You are an independent reviewer for the SageAgent v5 SageMaker notebook UI fix.

Repository root:

```text
D:\Github\sagemaker-coding-agent
```

Do not rely on any worker summary. Read the files and git history yourself.

Review target:

```text
git diff 2cbf9da55cfa7b0147f271589d2bc547883449a3..7ac7e099c839109a5cf9be67b5f6308daee6f662
```

Important context:

- v4’s working UI is in `compact_v4/MAIN/agent/sagemaker_agent.py`.
- v5 production files are in the flattened `compact_v5/` folder.
- The rebuilt production zip is `compact_v5.zip`.
- Evidence documents are under `compact_v5_test_evidence/`.

Reviewer task:

1. Compare the v5 UI launch/display change against v4’s actual display pattern.
2. Verify whether v5 now clears stale notebook output before constructing/displaying widgets.
3. Verify whether `chat.ipynb` avoids child-by-child widget display and avoids extra launch-cell HTML output.
4. Verify whether the production zip contains the corrected files and has no forbidden development/test folders.
5. Identify any remaining likely cause for SageMaker `Error displaying widget: model not found`.
6. Do not edit files.

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

