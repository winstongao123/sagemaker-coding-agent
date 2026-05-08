# Round 4 Subagent Trust Audit

Date: 2026-05-08

Purpose: answer the user's trust question after the SageMaker UI fix required
multiple rounds: if the UI could still be wrong, independently check whether
test-discovered problems were really fixed and whether v5 missed important
lessons from v4, Runnable Claude Code, Hermes, and Learning Factory.

## Method

Six already-running background agents were queried and their read-only reports
were consolidated:

- Three agents focused on test/fix evidence and production readiness claims.
- Three agents focused on reference-repo parity and missed architecture lessons.

This document records findings plus a local validation pass against the active
flattened production folder `compact_v5/` and `compact_v5.zip`.

## Findings Summary

| Area | Agent Finding | Current Validation | Disposition |
|---|---|---|---|
| UI display contract | v5 displayed child widgets separately and could produce `Loading widget...` / stale model errors. | Fixed in `compact_v5/ui/chat_ui.py`, `compact_v5/chat.ipynb`, and `compact_v5.zip`: one root widget, no child split, and v4-style `clear_output(wait=True)` before widget construction/display. Structural smoke passed. | Fixed, but needs user's SageMaker visual re-test after fresh zip + kernel restart. |
| UI run loop / Stop | Older report said `_on_send` was synchronous. | Current flattened `compact_v5/ui/chat_ui.py` uses `threading.Thread` and `_run_thread`; `py_compile` passed. | Fixed in active flattened runtime. |
| Subagent type mismatch | Older report said UI used invalid `explorer/worker/reviewer`. | Current UI uses `explore`, `review`, `general`, `build`, `plan`; these align with `subagent.agent_types` and task schema. Local alignment smoke passed. | Fixed in active flattened runtime. |
| `task` tool model override | Older report said `spawn_subagent(..., model_id=...)` did not accept `model_id`. | Current `compact_v5/subagent/spawn.py` accepts `model_id` and resolves child client overrides. | Fixed in active flattened runtime. |
| Production zip local state leak | Older report said `.sageagent_state` leaked into zip. | Current `compact_v5.zip` has 0 `.sageagent_state`, 0 `_status`, 0 `_phase_2`, 0 `MAIN`, 0 PS tests, 0 PowerBI entries; `testzip` passed. | Fixed. |
| Release docs stale marker | Older report found stale `v5.0.0 SHIP BLOCKED` in historical README. | Current flattened production folder has no `compact_v5/README.md`; production guidance is `chat.md` + docs/htmls. Development history is archived outside zip. | Not a production-zip blocker, but history docs must remain clearly archived. |
| Ask-user notebook path | Agents flagged that `ask_user` relies on context provider or `input()`. | Current production code still has this design. | Remaining risk for interactive notebook ask-user flows; should be lock-tested if ask-user is production-critical. |
| Approval widget wait | Agents flagged `PermissionDialog._prompt_widgets()` spin-waits. | Current UI runs agent work in background thread, reducing callback deadlock risk, but real notebook approval UX still needs visual/interactive test. | Remaining interactive-test need, not proven by local structural smoke. |
| Runnable-style live subagent window | Runnable has rich live task/subagent status; v5 has supervisor view, subagent start/finish messages, saved envelopes, and metrics, but no separate live subagent window. | Matches v5.0.1 design tradeoff; user may still want a later UI pane. | Accepted limitation unless user requires live subagent switching before production. |
| Runnable async background subagents | Runnable supports durable async tasks; v5 subagents are synchronous/one-shot with saved evidence. | Current code and docs intentionally avoid full async background subagents in v5.0.1. | Accepted limitation for notebook v5.0.1; future enhancement if needed. |
| Cache-break / microcompact depth | Runnable has deeper cache-break snapshots and API cache_edits; v5 adapts to Bedrock cache_control and local telemetry. | Matches documented Bedrock constraint; tested R-tier cache/cost surfaces, but not identical to Runnable. | Accepted adaptation, not a missed direct port. |

## Local Validation Commands

```text
py -3.11 -m py_compile compact_v5\ui\chat_ui.py compact_v5\tools\task.py compact_v5\subagent\spawn.py compact_v5\ui\approval_dialog.py compact_v5\tools\ask_user.py
```

Result: PASS.

```text
SUBAGENT_TYPE_ALIGNMENT_PASS
```

Result: UI subagent types match task schema and `AGENT_TYPES`.

```text
zipfile.ZipFile("compact_v5.zip").testzip()
```

Result: `None`.

Zip forbidden production entries:

```text
.sageagent_state: 0
_status: 0
_phase_2: 0
MAIN: 0
PS_PS_FINAL_TEST: 0
powerbi: 0
```

## UI Visual Check Artifact

Because this machine cannot attach to the user's remote SageMaker frontend, the
local visual check is a generated HTML/screenshot artifact plus a structural
ipywidgets smoke:

- `compact_v5_test_evidence/final_results/UI_V5_VISUAL_CHECK_AFTER_FIX.html`
- `compact_v5_test_evidence/final_results/UI_V5_VISUAL_CHECK_AFTER_FIX.png`
- `compact_v5_test_evidence/final_results/UI_V5_VISUAL_CHECK_AFTER_FIX.txt`

The screenshot verifies the intended v4-style dark layout and footer surface.
The structural smoke verifies the actual runtime widget tree: one root `VBox`,
dropdowns/buttons/textarea present, `Cache R/W`, `Saved`, and `Sub-Agents`
status present.

Claude Opus reviewed the UI fix after the clear-before-construct patch:

- `compact_v5_test_evidence/final_results/CLAUDE_OPUS_UI_FIX_REVIEW_PROMPT.md`
- `compact_v5_test_evidence/final_results/CLAUDE_OPUS_UI_FIX_REVIEW.md`
- `compact_v5_test_evidence/final_results/CLAUDE_OPUS_UI_FIX_REVIEW.err.log`

Result: `VERDICT: APPROVE_WITH_FIXES`, `SHIP DECISION:
READY_FOR_USER_VISUAL_RETEST`. Claude found only low/non-blocking nits:
remove the unused Cell 3 display import and make the assignment-form launch
requirement explicit. Those nits were applied before the final zip rebuild.

Claude Opus re-reviewed the final nit fixes:

- `compact_v5_test_evidence/final_results/CLAUDE_OPUS_UI_FIX_REREVIEW_PROMPT.md`
- `compact_v5_test_evidence/final_results/CLAUDE_OPUS_UI_FIX_REREVIEW.md`
- `compact_v5_test_evidence/final_results/CLAUDE_OPUS_UI_FIX_REREVIEW.err.log`

Final result: `VERDICT: APPROVE`, `SHIP DECISION:
READY_FOR_USER_VISUAL_RETEST`. Claude verified the zip members match the
working-tree files and that Cell 3 contains only assignment-form launch.

## Honest Trust Verdict

The audit increases confidence that several previously scary findings are fixed
in the active flattened production runtime, but it does not justify blind trust.

Before production use, the remaining hard gate is a fresh SageMaker visual run
from the rebuilt zip:

1. Restart kernel.
2. Clear notebook outputs.
3. Run Cells 1-3 from the latest `chat.ipynb`.
4. Confirm the UI renders as one complete control surface, not repeated
   `Loading widget...`.
5. Run a small message and confirm footer metrics update.
6. Run the final acceptance test if UI passes.

If the UI still shows repeated `Loading widget...` after those steps, v5 is not
ready regardless of prior R-tier evidence.
