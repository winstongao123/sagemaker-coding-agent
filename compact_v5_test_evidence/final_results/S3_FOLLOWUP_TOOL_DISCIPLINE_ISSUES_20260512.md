# S3 Follow-Up Tool Discipline Issues - 2026-05-12

## Status

Implemented and independently reviewed. The source fix is complete; v5 should
not be marked packaged for this block until `compact_v5_ship.zip` is rebuilt
from the current tree and the zip verification doc is refreshed.

Plan-review status: independent Claude CLI subscription review returned
`APPROVE` after two `REQUEST_CHANGES` loops tightened the root cause, exact
S3 call cap, artifact path-validation mechanism, and status-doc heuristic.
Final review path:
`compact_v5_test_evidence/final_results/s3_followup_tool_discipline_reviews/PLAN_REVIEW_CLAUDE_REREVIEW2.md`.

Implementation review paths:
- `compact_v5_test_evidence/final_results/S3_FOLLOWUP_TOOL_DISCIPLINE_CLAUDE_REVIEW.md`
  -> `APPROVE`.
- `compact_v5_test_evidence/final_results/S3_FOLLOWUP_TOOL_DISCIPLINE_CLAUDE_REREVIEW.md`
  -> `APPROVE` after the status-prefix polish fix.

Verification:
- `py -3.10 -m py_compile compact_v5/core/query_engine.py compact_v5/ui/chat_ui.py compact_v5/agent.py compact_v5/tools/aws_s3_preview.py compact_v5/tools/artifacts.py compact_v5/tools/v4_documents.py compact_v5/tools/write_file.py compact_v5/runtime/state.py compact_v5/runtime/config.py compact_v5/security/manager.py`
- `py -3.10 -m pytest compact_v5/tests -q` -> `47 passed`.

## Trigger Transcript

The user had just asked for S3 file/bucket structure. v5 successfully used
`aws_s3_list` and produced a relationship file. Then the user asked:

```text
pick two fiels to invesagte adn tell me hwat you found
```

Instead of reusing the previous S3 inventory and selecting two known objects,
v5 launched another broad S3 scan:

```text
[03:14:48] Tool: aws_s3_list ... done
[03:14:48] Tool: aws_s3_list ... done
[03:14:48] Tool: aws_s3_list ... done
[03:14:48] Tool: aws_s3_list ... done
[03:15:05] Tool: aws_s3_list ... done
[03:15:05] Tool: aws_s3_list ... done
```

This was a simple follow-up, not a request to refresh the full S3 inventory.

## Diagnosis

| Issue | Severity | Evidence | Expected Behavior |
|---|---:|---|---|
| Follow-up intent not preserved | P0 | "pick two files" after an S3 inventory caused new broad listing calls. | **Fixed:** follow-up reminders reuse recent S3 object paths before new list calls. |
| S3 list fanout too easy | P0 | Multiple distinct `aws_s3_list` calls were emitted in one follow-up. They were sequential, not true parallel; the model produced many tool uses and the dispatcher allowed distinct args through. | **Fixed:** follow-up turns cap `aws_s3_list` at 2 calls. |
| No "reuse previous evidence first" rule | P0 | v5 did not choose from already listed object paths. | **Fixed:** bounded recent S3 object extraction and reminder injection. |
| No safe object preview/read tool | P0 | `aws_s3_list` can list names only, so "investigate files" has no clean read path. | **Fixed:** read-only `aws_s3_preview` with Range cap and binary refusal. |
| Truncation truth gap | P0 | Earlier response claimed "all/complete" even when CDK output was truncated at 50 items. | **Fixed:** final guard blocks complete/all claims after truncated S3 evidence. |
| ASCII compliance gap | P1 | User requested ASCII; generated output contained emoji, arrows, and box-drawing characters. | **Fixed:** write/document tools reject non-ASCII content when user explicitly asks ASCII. |
| Workspace default wrong for deliverables | P1 | Created `S3_Structure_Diagram.md` under `/home/sagemaker-user/compact_v5_ship`. | **Fixed:** deliverables rebase to `CONFIG.user_artifacts_root` when workspace is the runtime package. |
| Created artifact memory weak | P1 | User asked where the file was; v5 searched again instead of answering from the create result. | **Fixed:** created artifacts persist to `.sageagent_state/artifacts.json` and are injected for file-location follow-ups. |
| AGENT_STATUS overuse | P1 | v5 edited `AGENT_STATUS.md` for a simple S3 inventory/report task. | **Fixed:** small S3/report tasks cannot update status unless explicitly requested. |
| Tool ID exposed too prominently | P2 | UI shows raw `toolu_bdrk_...` IDs in normal tool cards. | **Fixed:** raw id hidden from summary; retained only inside details. |
| Cost drift | P1 | Follow-up had too many calls, verbose output, and Thinking ON in later turn. | **Fixed:** simple S3 inventory/follow-up disables thinking for that turn and reduces list fanout. |

## Root Causes

| Root Cause | Code / Design Area |
|---|---|
| `aws_s3_list` is always loaded and easy for the model to choose. | `compact_v5/tools/aws_s3_list.py` |
| The model can emit many distinct `aws_s3_list` calls in one assistant turn; existing dedup only drops identical `(name, args)` duplicates. Because `aws_s3_list.requires_approval=True`, this is sequential fanout, not true parallel dispatch. | `compact_v5/core/query_engine.py`; `compact_v5/core/parallel_dispatch.py` |
| Prompt guidance says to use `aws_s3_list` for S3 inventory, but not to reuse known results on follow-up. | `compact_v5/prompt/tool_classes.md`; system task guidance |
| Session state does not expose a compact "recent S3 objects/artifacts" memory to the model/UI. | `runtime/state.py`, `ui/chat_ui.py`, possible new helper |
| There is no S3 object preview tool with strict read-only limits. | missing tool |
| File writes default to current runtime working directory when workspace is `"."`; user deliverables then land under `/home/sagemaker-user/compact_v5_ship/`. Runtime state/audit dirs also depend on workspace, so the fix must avoid moving all state roots accidentally. | `runtime/config.py`, `entry.py`, `ui/chat_ui.py`, document tools |

## Shipped Fix Blocks

| Block | Goal | Acceptance |
|---|---|---|
| 1. S3 follow-up reuse guard | Shipped in `core/query_engine.py`. | Recent S3 object paths are injected before follow-up turns. |
| 2. S3 same-name fanout cap | Shipped in `core/query_engine.py`. | The 3rd follow-up `aws_s3_list` call is blocked. |
| 3. Safe S3 preview tool | Shipped as `tools/aws_s3_preview.py`. | Bounded Range read, binary refusal, Bedrock-only aware. |
| 4. Truncation truth gate | Shipped in `core/query_engine.py`. | Complete/all claims are blocked after truncated S3 evidence. |
| 5. User artifact policy | Shipped in `runtime/config.py`, `runtime/state.py`, `security/manager.py`, `tools/artifacts.py`, write/document tools. | Runtime-state roots stay unchanged; user deliverables default outside runtime package workspaces. |
| 6. ASCII contract | Shipped in write/document tools. | Non-ASCII writes fail when the user asks for ASCII. |
| 7. Status-doc guard | Shipped in `core/query_engine.py`. | Small S3/report tasks cannot edit `AGENT_STATUS.md` unless explicit. |
| 8. UI polish | Shipped in `ui/chat_ui.py`. | Tool summary hides raw `toolu_...` ids. |
| 9. Cost proof | Shipped via behavior and tests. | S3 follow-up calls are capped; thinking is disabled for simple S3 inventory/follow-up turns. |

## Non-Goals

- Do not rework the whole agent loop.
- Do not remove `aws_s3_list`; it is the correct safe listing path.
- Do not add destructive S3 operations.
- Do not make S3 preview read unlimited data.
- Do not make the model silently refresh all buckets when the user asks a
  narrow follow-up.

## Tests To Add

1. Follow-up replay: first save a synthetic S3 inventory in session context,
   then prompt "pick two files to investigate". Assert no full bucket rescan.
2. S3 fanout: verify repeated distinct `aws_s3_list` calls in one assistant
   turn are capped with a synthetic tool result on the 3rd call.
3. S3 preview: small `.csv`, `.txt`, `.json` object preview succeeds; large or
   binary object returns a bounded refusal.
4. Truncation: truncated list cannot produce "all files" or "complete" final
   claim without continuation.
5. ASCII: generated diagram/report for an explicit ASCII request contains only
   bytes `< 0x80`.
6. Workspace: no report file is created under `compact_v5_ship/` or the v5
   runtime folder by default.
7. Artifact memory: asking "where is the file?" answers from recorded artifact
   path without `tool_search` or directory scan.

## Review Requirement

Each block must be reviewed independently by Claude CLI using subscription
auth:

```powershell
$env:ANTHROPIC_API_KEY=$null
Get-Content -Raw .\path\to\review_prompt.md | claude -p
```

Save each review prompt, diff, output, and final verdict under:

```text
compact_v5_test_evidence/final_results/s3_followup_tool_discipline_reviews/
```

Claude must return literal `APPROVE` before the next block proceeds, or the
worker must fix and re-review the block.
