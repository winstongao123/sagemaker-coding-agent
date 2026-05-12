# S3 Follow-Up Tool Discipline Issues - 2026-05-12

## Status

Open worker block. Do not mark v5 fully solved for S3 workflows until these
items are implemented, tested, independently reviewed, and packaged into
`compact_v5_ship.zip`.

Plan-review status: independent Claude CLI subscription review returned
`APPROVE` after two `REQUEST_CHANGES` loops tightened the root cause, exact
S3 call cap, artifact path-validation mechanism, and status-doc heuristic.
Final review path:
`compact_v5_test_evidence/final_results/s3_followup_tool_discipline_reviews/PLAN_REVIEW_CLAUDE_REREVIEW2.md`.

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
| Follow-up intent not preserved | P0 | "pick two files" after an S3 inventory caused new broad listing calls. | Treat as a continuation of the previous S3 result unless user asks to refresh. |
| S3 list fanout too easy | P0 | Multiple distinct `aws_s3_list` calls were emitted in one follow-up. They were sequential, not true parallel; the model produced many tool uses and the dispatcher allowed distinct args through. | Add a per-turn cap / same-name throttle for `aws_s3_list`; do not broad-rescan buckets for a small follow-up. |
| No "reuse previous evidence first" rule | P0 | v5 did not choose from already listed object paths. | Reuse recent visible/session S3 object list before calling tools. |
| No safe object preview/read tool | P0 | `aws_s3_list` can list names only, so "investigate files" has no clean read path. | Add read-only `aws_s3_preview` with size/content-type safety limits. |
| Truncation truth gap | P0 | Earlier response claimed "all/complete" even when CDK output was truncated at 50 items. | Never claim all/complete when a continuation token or truncation marker exists. |
| ASCII compliance gap | P1 | User requested ASCII; generated output contained emoji, arrows, and box-drawing characters. | If ASCII requested, output and generated files must use plain ASCII only. |
| Workspace default wrong for deliverables | P1 | Created `S3_Structure_Diagram.md` under `/home/sagemaker-user/compact_v5_ship`. | User artifacts should default outside the v5 runtime folder, e.g. `/home/sagemaker-user/sageagent_workspace`. |
| Created artifact memory weak | P1 | User asked where the file was; v5 searched again instead of answering from the create result. | Track created artifact paths in UI/session state and final answers. |
| AGENT_STATUS overuse | P1 | v5 edited `AGENT_STATUS.md` for a simple S3 inventory/report task. | Reserve status updates for project/long-running coding tasks or explicit request. |
| Tool ID exposed too prominently | P2 | UI shows raw `toolu_bdrk_...` IDs in normal tool cards. | Hide raw ids by default; keep them in debug/details. |
| Cost drift | P1 | Follow-up had too many calls, verbose output, and Thinking ON in later turn. | Keep simple S3 follow-ups low-call, concise, and Thinking OFF unless user enables it. |

## Root Causes

| Root Cause | Code / Design Area |
|---|---|
| `aws_s3_list` is always loaded and easy for the model to choose. | `compact_v5/tools/aws_s3_list.py` |
| The model can emit many distinct `aws_s3_list` calls in one assistant turn; existing dedup only drops identical `(name, args)` duplicates. Because `aws_s3_list.requires_approval=True`, this is sequential fanout, not true parallel dispatch. | `compact_v5/core/query_engine.py`; `compact_v5/core/parallel_dispatch.py` |
| Prompt guidance says to use `aws_s3_list` for S3 inventory, but not to reuse known results on follow-up. | `compact_v5/prompt/tool_classes.md`; system task guidance |
| Session state does not expose a compact "recent S3 objects/artifacts" memory to the model/UI. | `runtime/state.py`, `ui/chat_ui.py`, possible new helper |
| There is no S3 object preview tool with strict read-only limits. | missing tool |
| File writes default to current runtime working directory when workspace is `"."`; user deliverables then land under `/home/sagemaker-user/compact_v5_ship/`. Runtime state/audit dirs also depend on workspace, so the fix must avoid moving all state roots accidentally. | `runtime/config.py`, `entry.py`, `ui/chat_ui.py`, document tools |

## Required Fix Blocks

| Block | Goal | Acceptance |
|---|---|---|
| 1. S3 follow-up reuse guard | At turn start, extract recent `aws_s3_list` object paths from a bounded window of `self.messages` (last 6 user/assistant turns or about 8 KB of recent tool-result text) and inject a compact reminder for S3 follow-ups. | Transcript replay makes zero broad bucket-rescan calls when recent object paths exist. |
| 2. S3 same-name fanout cap | Add a per-`QueryEngine.run` turn cap of 2 `aws_s3_list` calls, independent of parallel-dispatch flags. | The 3rd S3 list call in one user turn returns a synthetic block saying to reuse prior results or narrow the prefix. |
| 3. Safe S3 preview tool | Add always-loaded `aws_s3_preview` for small text/CSV/JSON object previews using S3 Range reads. | Can inspect two chosen files with byte cap and binary/large-object refusal. |
| 4. Truncation truth gate | Prevent "all/complete" claims when any list result is truncated; enforce near final-text claim, mirroring existing final-claim guards. | Regression test with truncated S3 result forces "partial/truncated" wording or continuation. |
| 5. User artifact policy | Keep runtime state/audit roots unchanged, but default newly created user deliverables outside the v5 runtime folder, pass path validation, and track created files. | Add a user-artifacts root such as `CONFIG.user_artifacts_root`, include it in allowed paths, rebase only user deliverables there when no project workspace is chosen, and answer file-location questions from recorded artifact state. |
| 6. ASCII contract | Honor explicit ASCII-only requests only when user asks for ASCII. | Generated diagram/report contains only bytes `< 0x80` when user asks ASCII. |
| 7. Status-doc guard | Do not update `AGENT_STATUS.md` for small non-project tasks using a concrete heuristic. | Update status only when user asks for status/progress/handoff, `iter_used > 15`, or project-source writes exceed 3 files; simple S3 report prompts do not edit status. |
| 8. UI polish | Hide raw tool ids by default. | Tool card summary is readable; id appears only in details/debug. |
| 9. Cost proof | Show before/after call and token budget for the transcript. | Replay stays within agreed call budget and Thinking remains OFF for simple S3 follow-up. |

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
