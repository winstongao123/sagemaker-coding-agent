# Claude Review Request: UI Live Supervisor Final Patch 2026-05-11

Repo root: `D:\Github\sagemaker-coding-agent`

You are the independent read-only Claude reviewer. Use only read/grep/glob/bash
inspection. Do not edit files, do not commit, do not call AWS, and do not rely
on this prompt as source code evidence. Locate and read the files yourself.

## Scope

Review the v5.0.2 UI live-supervisor final patch in the active ship tree:

- `compact_v5/compact_v5/ui/chat_ui.py`
- `compact_v5/compact_v5/core/query_engine.py`
- `compact_v5/compact_v5/tools/task.py`
- `compact_v5/compact_v5/tests/test_ui_live_supervisor_smoke.py`
- docs/evidence under `compact_v5_test_evidence/final_results/`
- zip artifact `compact_v5.zip`

## Required Review Rows

Please review each row explicitly and include the row id in your output:

| Row id | Required check |
|---|---|
| UI-LIVE-STREAM | `output_fn` updates the UI during `agent.run()` and does not duplicate final assistant text. |
| UI-BRACKET-ASSISTANT | Assistant markdown/final answers that start with `[` such as `[SPEC vs SHIPPED]` stay assistant messages, not system cards. |
| UI-TOOL-CARDS | Tool call/result cards render as display-only UI without changing tool dispatch semantics. |
| UI-SUBAGENT-VIS | Subagent lifecycle/result/artifact info is visible, but raw `task` result envelopes are not duplicated as noisy tool cards when already parsed. |
| UI-METRICS-LAYOUT | Existing per-turn metrics are restyled only; no re-plumbing or token accounting behavior change. |
| UI-STOP-STATUS | Stop wording is cooperative and updates while a run is still in flight. |
| UI-COST-MEASURE | Cost-driver line is display-only and does not change model, prompt, cache, compaction, or Bedrock request shape. |
| UI-NO-DRIFT | No unintended changes to prompt/security/Bedrock request shape/compaction/final-claim guard. |
| UI-TEST-EVIDENCE | Smoke tests cover the critical regressions above and pass locally. |
| UI-ZIP-EVIDENCE | `compact_v5.zip` was rebuilt from active tree and verified. |

## Evidence To Inspect

- Current code files listed above.
- `compact_v5_test_evidence/final_results/UI_LIVE_SUPERVISOR_FIX_20260510.md`
- `compact_v5_test_evidence/final_results/UI_LIVE_SUPERVISOR_ZIP_VERIFY_20260510.md`
- `compact_v5_test_evidence/final_results/UI_LIVE_SUPERVISOR_FINAL_VISUAL_20260511.html`
- `compact_v5_test_evidence/final_results/UI_LIVE_SUPERVISOR_FINAL_VISUAL_20260511.png`
- `compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/`

## Local Commands Already Run By Codex

```powershell
python -m py_compile compact_v5/compact_v5/ui/chat_ui.py compact_v5/compact_v5/tests/test_ui_live_supervisor_smoke.py
python compact_v5/compact_v5/tests/test_ui_live_supervisor_smoke.py
```

The smoke script reported all ten tests as PASS.

## Output Format Required

Return:

1. `REVIEWED ROWS` table with every row id above and `PASS`, `WARN`, or `FAIL`.
2. `FINDINGS` ordered by severity with file/line references.
3. `NO-DRIFT VERDICT`.
4. `SHIP DECISION`: one of `APPROVE`, `APPROVE_WITH_WARNINGS`, or `REQUEST_CHANGES`.

If you cannot inspect the repo or the command environment blocks review, say
`NO_VERDICT` and explain the exact blocker.
