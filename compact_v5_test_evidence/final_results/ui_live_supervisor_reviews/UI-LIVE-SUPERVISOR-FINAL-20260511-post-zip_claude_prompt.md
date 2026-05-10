# Claude Re-Review Request: UI Live Supervisor Post-Zip Fix 2026-05-11

Repo root: `D:\Github\sagemaker-coding-agent`

You are the independent read-only Claude reviewer. Use only read/grep/glob/bash
inspection. Do not edit files, do not commit, do not call AWS, and do not rely
on this prompt as source code evidence. Locate and read files yourself.

## Purpose

Your previous usable review correctly returned `REQUEST_CHANGES` because
`compact_v5.zip` was stale and its `ui/chat_ui.py` lacked:

- `_is_status_output()` allowlist for bracket-leading assistant text;
- early return after parsed `task` subagent envelopes.

Codex rebuilt `compact_v5.zip` from `compact_v5/compact_v5/` and updated the
zip verification document to include SHA-256 parity checks between required zip
members and active source files.

## Please Verify

1. `compact_v5.zip` now contains the active `ui/chat_ui.py` with both fixes.
2. `UI_LIVE_SUPERVISOR_ZIP_VERIFY_20260510.md` records `testzip=None`, no
   missing required members, no forbidden entries, and no hash mismatches.
3. The active source still satisfies all rows from your previous review:
   `UI-LIVE-STREAM`, `UI-BRACKET-ASSISTANT`, `UI-TOOL-CARDS`,
   `UI-SUBAGENT-VIS`, `UI-METRICS-LAYOUT`, `UI-STOP-STATUS`,
   `UI-COST-MEASURE`, `UI-NO-DRIFT`, `UI-TEST-EVIDENCE`, and
   `UI-ZIP-EVIDENCE`.

Evidence paths:

- `compact_v5.zip`
- `compact_v5/compact_v5/ui/chat_ui.py`
- `compact_v5/compact_v5/tests/test_ui_live_supervisor_smoke.py`
- `compact_v5_test_evidence/final_results/UI_LIVE_SUPERVISOR_ZIP_VERIFY_20260510.md`
- `compact_v5_test_evidence/final_results/UI_LIVE_SUPERVISOR_FINAL_VISUAL_20260511.html`
- `compact_v5_test_evidence/final_results/UI_LIVE_SUPERVISOR_FINAL_VISUAL_20260511.png`

Local commands rerun by Codex after rebuild:

```powershell
python -m py_compile compact_v5/compact_v5/ui/chat_ui.py compact_v5/compact_v5/agent.py compact_v5/compact_v5/core/query_engine.py compact_v5/compact_v5/tools/task.py compact_v5/compact_v5/subagent/spawn.py compact_v5/compact_v5/tests/test_ui_live_supervisor_smoke.py
python compact_v5/compact_v5/tests/test_ui_live_supervisor_smoke.py
Expand-Archive compact_v5.zip; python -c "import entry"
```

## Output Format Required

Return:

1. `REVIEWED ROWS` table with `PASS`, `WARN`, or `FAIL`.
2. `FINDINGS` ordered by severity with file/line references.
3. `NO-DRIFT VERDICT`.
4. `SHIP DECISION`: one of `APPROVE`, `APPROVE_WITH_WARNINGS`, or `REQUEST_CHANGES`.
