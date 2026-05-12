# S3 Follow-Up Tool Discipline Fix - 2026-05-12

## Verdict

Fixed in source and independently reviewed by Claude CLI subscription mode.
The block closes the real-use problems seen after the S3 inventory prompt:
over-scanning follow-ups, confusing thinking placement, raw tool IDs, weak
artifact memory, wrong default artifact folder, ASCII-contract misses, status
doc spam, and truncated "complete" claims.

## SPEC vs SHIPPED

| SPEC | SHIPPED |
|---|---|
| Reuse prior S3 evidence for follow-ups | `QueryEngine` extracts recent concrete `s3://bucket/key` object paths and injects a reuse-first reminder. |
| Stop broad follow-up rescans | Follow-up `aws_s3_list` calls are capped at 2 per user turn; the 3rd returns a synthetic blocker. |
| Inspect chosen S3 files safely | Added always-loaded, read-only `aws_s3_preview` with S3 Range reads, byte cap, Bedrock-only awareness, and binary refusal. |
| Thinking should not appear after results | Engine emits `[thinking]` before tool dispatch/final text; UI renders it as a collapsed `thinking` row and no longer duplicates it under metrics. |
| Hide confusing raw tool IDs | Tool summary hides `toolu_...`; the ID remains only inside details for debugging. |
| Remember generated files | Created artifacts are recorded in `.sageagent_state/artifacts.json`; file-location follow-ups get a reminder from that state. |
| Do not save reports inside runtime package by default | Added `CONFIG.user_artifacts_root` (`~/sageagent_workspace`) and rebase logic for relative deliverables when workspace is `compact_v5` or `compact_v5_ship`. |
| Honor ASCII requests | Write/document tools reject non-ASCII generated content when the user explicitly asks for ASCII. |
| Avoid AGENT_STATUS spam | Small S3/report tasks cannot edit `AGENT_STATUS.md` unless status/handoff was explicitly requested. |
| Prevent false complete claims | S3 truncation guard blocks "complete/all" final claims when recent evidence includes truncation or continuation tokens. |
| Keep cost low for simple S3 work | Simple S3 inventory/follow-up turns disable thinking for that turn only and reduce broad list fanout. |

## Verification

- `py -3.10 -m py_compile compact_v5/core/query_engine.py compact_v5/ui/chat_ui.py compact_v5/agent.py compact_v5/tools/aws_s3_preview.py compact_v5/tools/artifacts.py compact_v5/tools/v4_documents.py compact_v5/tools/write_file.py compact_v5/runtime/state.py compact_v5/runtime/config.py compact_v5/security/manager.py`
- `py -3.10 -m pytest compact_v5/tests -q` -> `47 passed`
- `git diff --check` -> no whitespace errors

## Claude Reviews

| Review | Result | Path |
|---|---|---|
| Implementation review | `APPROVE` | `S3_FOLLOWUP_TOOL_DISCIPLINE_CLAUDE_REVIEW.md` |
| Re-review after status-prefix polish | `APPROVE` | `S3_FOLLOWUP_TOOL_DISCIPLINE_CLAUDE_REREVIEW.md` |

Claude reviewed with subscription mode by clearing API-token routing:

```powershell
$env:ANTHROPIC_API_KEY=$null
$env:CLAUDE_CODE_USE_BEDROCK=$null
Get-Content -Raw .\compact_v5_test_evidence\final_results\S3_FOLLOWUP_TOOL_DISCIPLINE_CLAUDE_REVIEW_PROMPT.md | claude -p
```

## Target Validation Prompt

After uploading the refreshed ship zip to SageMaker, validate with:

```text
list all files of my s3, i need ascii diagram with structure
```

Then follow up:

```text
pick two files to investigate and tell me what you found
```

Expected behavior:
- no fresh full-bucket rescan when recent object paths exist;
- at most two `aws_s3_list` calls in the follow-up;
- use `aws_s3_preview` for selected file content;
- ASCII-only diagram output;
- any generated report saved under the user artifact root unless a project
  workspace is configured;
- no `AGENT_STATUS.md` edit unless explicitly requested.
