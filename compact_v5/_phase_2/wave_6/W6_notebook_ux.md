# W6 — Notebook UX + SageMaker Environment + UI Widgets + Slash Commands

**Date**: 2026-05-01
**Source plan**: `compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md`
**Source synthesis**: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md`
**v4 reference**: `compact_v4/MAIN/agent/sagemaker_agent.py:9776-11341` + `compact_v5/_phase_2/v4_reference/{chat.ipynb, create_chat_ui.py}`

**Verdict legend**:
- **HANDLED** = explicit Block + file:line graft already in plan; lock test specified
- **NEEDS-LOCK-TEST** = code path covered but no explicit Q4 lock test in current plan; add before ship
- **POSSIBLE-GAP** = scenario not visibly covered by any Block; investigate before Block 0 starts

---

## 1. Kernel restart mid-conversation, user wants to keep going

- **What user does**: edits cell 2 widget params, hits Kernel→Restart, re-runs cells 1-3, expects to resume the conversation that was ongoing.
- **What could go wrong**: in-memory `Agent` instance dies; chat history, todos, file_cache, `_FILES_READ`, session_cost all reset to zero. Session JSON on disk is stale (last `/save`). User keeps typing as if context is still there → silent drift.
- **What v5.0.1 plan provides**: Block B+ SessionManager port (`:2578-`), AGENT_STATUS auto-load (`_load_persistent_memory + _load_project_status ~:8700-8722`), Block B+ atexit cost flush (B+7 `costHook.ts:6-22`). New `Agent` is constructed empty; cell 3 launch must auto-call `SessionManager.load(latest)` if a recent session JSON exists.
- **Verdict**: **NEEDS-LOCK-TEST** — Block B+ ports the mechanics but Block E+F doesn't have an explicit "auto-resume on cell-3 launch" lock test. Add Q4 row: kernel restart → re-run cells → last session restored without `/load`.

## 2. Model dropdown switched mid-conversation (Sonnet 4.5 → Haiku 4.5)

- **What user does**: clicks model dropdown at `:10068-10208` mid-turn after 30 messages, picks Haiku 4.5 to save cost.
- **What could go wrong**: A28 cache-invariant violation — toolset / system prompt rebuilt for new model mid-conversation invalidates cache; next Haiku call starts cold + emits constant cache-break warnings (Haiku 4.5 = `isExcludedModel` per L-14). Token estimator still uses Sonnet bytes-per-token ratio.
- **What v5.0.1 plan provides**: Block A row A-33 (H5 A28 prompt-cache invariant policy — "NEVER rebuild system prompt mid-conv; toolset changes deferred to next session via `--now` opt-in"); Block L row L-14 (`isExcludedModel` Haiku exclusion `promptCacheBreakDetection.ts:128-131`); Block B row B-10 (`MODEL_COSTS` per-model pricing).
- **Verdict**: **HANDLED** — A33 is MUST-fix; warn-or-defer UI on dropdown change is implied. Lock test in Block A Q4 covers cache-invariant. Suggest `on_model_change` displays "switch will apply on next session" banner.

## 3. Dark-mode toggle flipped mid-render

- **What user does**: ticks dark-mode checkbox (`create_chat_ui.py:408, on_dark_mode_change:500`) after 50 messages of history.
- **What could go wrong**: existing rendered HTML cards keep dark colors; only new messages get light theme → inconsistent UI.
- **What v5.0.1 plan provides**: Block E+F port of `_render_assistant_markdown :9788-9922` + `render_chat :9924-9970` + theme dict. v4 baseline already re-renders on toggle.
- **Verdict**: **HANDLED** (v4 parity). Lock test should assert full re-render on theme change.

## 4. Iteration-budget slider set to 600 in cell 2, propagates to cell 3 launch

- **What user does**: drags `IterationBudgetWidget` (Phase 11) to 600 in cell 2 before cell 3 `create_chat_ui()` runs.
- **What could go wrong**: widget value not read by `Agent` constructor; agent ships with default 200 → user wonders why long task halts at 200.
- **What v5.0.1 plan provides**: Block E+F bullet "IterationBudgetWidget already exists in `compact_v5/MAIN/agent/ui/widgets.py` from Phase 11; PS Issue #2 visible-budget UI fix"; v4 source `:10086-10102`.
- **Verdict**: **HANDLED** — Phase 11 widget + cell 2 wiring; Block F2 (NEW, +100 LOC) adds auto-continue at <90%. Lock test `tests/integration/test_iteration_budget_propagation.py` should assert cell-2 slider value reaches `Agent.iteration_budget` field.

## 5. /save mywork → 3 days later /load mywork → full state restored incl. session_cost

- **What user does**: types `/save mywork`, closes notebook. Days later opens, runs cells, types `/load mywork`.
- **What could go wrong**: cost counter reset to $0 (B+1 not implemented); todos lost; AGENT_STATUS.md not re-read; `/cost` shows misleading $0.00 even though $4.32 was already spent.
- **What v5.0.1 plan provides**: Block B+ SessionManager (`:2578-`); B+1 "Persist session cost + restore on resume" (`cost-tracker.ts:87-175`, 90 LOC); save/load callbacks `:11569-11665`; AGENT_STATUS auto-load `~:8700-8722`.
- **Verdict**: **HANDLED**. B+ Q4 lock test: "save→load→cost preserved" already specified.

## 6. /cost after 50 turns including 3 sub-agent calls

- **What user does**: types `/cost` deep into a session that spawned `verify` and `simplify` sub-agents.
- **What could go wrong**: parent-only counter (sub-agent tokens not attributed); cumulative-input double-count (R7 N8); displayed cost ≠ actual Bedrock spend.
- **What v5.0.1 plan provides**: Block B per-agent attribution dict (`parent_*`, `subagent_*[type]`) on shared TokenTracker singleton; B-11 input-cumulative-vs-output-per-turn fix (R7 N8); B+3 4-line cost block format (`cost-tracker.ts:228-244`); B+5 recursive advisor sub-cost accounting (`cost-tracker.ts:304-322`); v4 `/cost` handler `:11030-11051`.
- **Verdict**: **HANDLED**. B+ acceptance test `tests/integration/test_subagent_token_attribution.py` is named in plan §3 Block B+.

## 7. /skills then /skill use clara — fuzzy matches "clara-review"

- **What user does**: types `/skills` (sees `clara-review` in list), then `/skill use clara` (drops the suffix).
- **What could go wrong**: v4 only matched directory name OR metadata `name:`. v5.0.0 regression cited in Block I Q2: "v5-introduced regression where `/skill activate clara` failed."
- **What v5.0.1 plan provides**: Block I (50 LOC) — alias-resolve directory + metadata name + Hermes Levenshtein fuzzy match (`run_agent.py:4689-4720`).
- **Verdict**: **HANDLED**. Block I Q4 lock test "10 directory names + typo `verfy` → `verify`" specified.

## 8. /done quick — spawns simplify + verify pipeline

- **What user does**: after editing 4 files, types `/done quick`.
- **What could go wrong**: v5.0.0 didn't have AGENT_TYPES populated → `verify` / `simplify` sub-agent types missing → handler errors out or runs against `general` only. PS#7 cited.
- **What v5.0.1 plan provides**: Block D `/done` handler `:11276-11313`; Block G AGENT_TYPES dict `:6914-7090` (7 types); v4 `/done` invokes simplify skill and verify skill via sub-agent dispatch; Block T11 (`tools/ask_user.py`) for the READY-TO-SHIP confirmation.
- **Verdict**: **HANDLED**. Block D Q4: "Includes `/done` full pipeline (simplify → verify → READY-TO-SHIP)".

## 9. /regression after editing 5 files — git diff stat + suggested test cmd

- **What user does**: after a bug-fix burst, types `/regression`.
- **What could go wrong**: handler fails if no git repo initialized (SageMaker workspace often is just `/home/sagemaker-user/`); error message confusing.
- **What v5.0.1 plan provides**: Block D `/regression` handler `:11243-11275` (verbatim port, "git diff HEAD stat + session edits + suggested test cmd").
- **Verdict**: **NEEDS-LOCK-TEST** — Block D Q4 doesn't explicitly cover the no-git case. Add fallback: print session-edit-history-only when `.git` absent.

## 10. /skill apply clara-review after agent proposed patch — diff preview + Approve

- **What user does**: agent self-patches a skill (V4.9.5 self-patching, opt-in). User types `/skill apply clara-review`, sees diff, clicks Approve.
- **What could go wrong**: pending-proposals list empty (B+ patches via different path); diff is empty; Approve fires but writes no-op.
- **What v5.0.1 plan provides**: Block D `/skill apply` handler `:10892-10954` (verbatim); Block D `/skill suggestions` `:10874-10891`; Block I + Block D-3 dynamic-skill merge dedupe (`commands.ts:476-517`).
- **Verdict**: **HANDLED**. Block D Q4 covers all 19 advertised commands incl. `/skill apply`.

## 11. Stop button mid-run — agent halts cleanly

- **What user does**: hits Stop button in cell 3 UI while a long bash is running.
- **What could go wrong**: bash subprocess orphaned; tool-result block missing → next turn Bedrock 400 ("missing tool_result for tool_use X").
- **What v5.0.1 plan provides**: Block C+ stop/abort handler (`agent/__init__.py:Agent.stop()` already exists, `core/query_engine.py:run()` per-turn checkpoint reads `_combined_stop()` already wired in Phase 8); Block A row A-25 (Hermes H2 F7 stub-injection for missing tool_results post-compact, `:4585-4604`, MUST); Block C-17 `combinedAbortSignal + AsyncLocalStorage` (Python `contextvars + asyncio.Event`).
- **Verdict**: **HANDLED**. Lock test in Block A Q4 + Block C+ Q4. Note: A-25 covers the missing-tool_result generalization (not just compact path).

## 12. mock_mode=True (offline testing) — agent responds without Bedrock call

- **What user does**: sets `CONFIG.mock_mode = True` in cell 2, hits Send.
- **What could go wrong**: there is no `mock_mode` flag in v4 baseline; user may try this from habit (sagemaker doc convention). Today silently calls real Bedrock or NameError.
- **What v5.0.1 plan provides**: not covered by any Block. v5 has `tests/integration/test_real_bedrock_smoke.py` (Block J) gated on `RUN_REAL_BEDROCK=1` env, which is the inverse pattern (real off by default in tests, but UI defaults to real).
- **Verdict**: **POSSIBLE-GAP**. Either (a) explicitly document "mock_mode is a test-only construct, not a UI feature" in `USER_GUIDE.md`, or (b) add `CONFIG.mock_bedrock` flag with a Block 0 dispatch `runtime/bedrock_client.py:chat()` short-circuit. Without this, beginner users following SageMaker tutorials will hit cryptic boto3 errors.

## 13. Non-AWS-scope (no IAM perms) — clear error vs cryptic stack trace

- **What user does**: opens chat.ipynb in a SageMaker domain that lacks `bedrock:InvokeModel` for the chosen model.
- **What could go wrong**: cryptic `botocore.errorfactory.AccessDeniedException` deep in tool dispatch; user has no idea which IAM action is missing.
- **What v5.0.1 plan provides**: Block L row L-9 `sanitizeAPIError + extractNestedErrorMessage` (`errorUtils.ts:107-198`, MUST) — surfaces nested Bedrock 5xx HTML / JSON; Block L row L-8 `extractConnectionErrorDetails` SSL/proxy hint (R4 #8). Bedrock IAM denial does NOT match the SSL pattern; needs L-9 applied to AccessDeniedException.
- **Verdict**: **NEEDS-LOCK-TEST**. Add Block L Q4 row: "AccessDeniedException → user-readable message naming the missing IAM action (`bedrock:InvokeModel` on `<modelId>`)".

## 14. ipywidgets not installed — fallback minimal UI

- **What user does**: fresh SageMaker kernel without `ipywidgets` package; runs cell 3.
- **What could go wrong**: `ImportError: ipywidgets` aborts the entire UI; no chat at all.
- **What v5.0.1 plan provides**: Block 0 + cell 1 imports — v4 `chat.ipynb` cell 1 has `pip install ipywidgets` precondition. No fallback path in v4 baseline. Block 0 row 0-9 (feature-flag fail-closed at import boundary, `entry.ts:1-17`) handles banned modules but not optional-dep degraded UI.
- **Verdict**: **POSSIBLE-GAP**. Either pin `ipywidgets>=8.0` in cell 1 install (v4 already does) OR provide a stdout-only mode. Recommend documenting in `USER_GUIDE.md` cell 1 "DO NOT skip pip install".

## 15. Long agent response wraps into `<details>` collapsible

- **What user does**: agent emits 8KB of analysis; UI should collapse to a one-line summary with expand toggle.
- **What could go wrong**: full 8KB rendered inline → notebook scroll horror, cell-output truncation by JupyterLab kicks in around 5K lines.
- **What v5.0.1 plan provides**: Block E+F `_render_assistant_markdown :9788-9922` (135 LOC) + `_format_inline_md :9776-9786` (10 LOC). v4 baseline already wraps long responses (`<details>` for tool_use blocks, but NOT for plain assistant text — verified by re-reading `:9788-9922` snippet from plan).
- **Verdict**: **POSSIBLE-GAP** for plain-text assistant responses >2KB. v4 baseline has it for tool blocks but not text. Recommend Block E+F micro-extension: collapse text >100 lines.

## 16. /checkpoint create v1 → edits 5 files → /checkpoint restore v1 — file state rolls back

- **What user does**: `/checkpoint create v1`, edits, `/checkpoint restore v1`.
- **What could go wrong**: restore restores files but `_FILES_READ` cache still says they're stale (model thinks newer content exists); or `.snapshots/` directory not cleaned.
- **What v5.0.1 plan provides**: Block D `/checkpoint` handler `:11114-11182` (verbatim); Block B SnapshotManager `:4418-4509` + singleton `:4510`; Block C row C+2 (file-history snapshot per-edit, `FileEditTool.ts:431-440`); Block A row A-21 `runPostCompactCleanup` cache invalidation (`postCompactCleanup.ts:1-77`) — covers `_FILES_READ` reset.
- **Verdict**: **NEEDS-LOCK-TEST**. Block B Q4 covers SNAPSHOTS.snapshot+restore but not "after restore, `_FILES_READ` is reset so model re-reads on next access". Add row.

## 17. /diffs after editing 7 files — session edit history shown

- **What user does**: types `/diffs`, expects ordered list of edits this session with per-file unified-diff snippets.
- **What could go wrong**: history depends on `tools/edit_file.py` calling `SNAPSHOTS.snapshot` consistently; if `notebook_edit` (T-1) skips the call, those edits disappear.
- **What v5.0.1 plan provides**: Block D `/diffs` handler `:11200-11242` (verbatim); Block B wiring "tools/edit_file.py + tools/write_file.py + skills/manager.py:apply_proposal call SNAPSHOTS.snapshot". `notebook_edit.py` not explicitly listed in B wiring.
- **Verdict**: **NEEDS-LOCK-TEST**. Add notebook_edit + view_image (T-2) to SNAPSHOTS wiring list. Add Block B Q4 row covering "all mutating tools snapshot pre-edit".

## 18. /phase "Phase 2 build" — sets work-phase tag in status bar

- **What user does**: `/phase Phase 2 build`, expects status bar to show `Phase: Phase 2 build` until next `/phase`.
- **What could go wrong**: status bar `update_mode_display :10308-10357` reads from a separate state cell; race with `update_tokens_display :10377-10478` could overwrite.
- **What v5.0.1 plan provides**: Block D `/phase` handler `:11183-11199` (verbatim); Block E+F `update_mode_display` port (50 LOC).
- **Verdict**: **HANDLED** (v4 parity).

## 19. /verify pre-commit — runs verify skill

- **What user does**: types `/verify pre-commit` before a `git commit`.
- **What could go wrong**: verify skill not registered (Block I); or runs but doesn't return proper boolean to UI; or gets blocked by exec-call limit (Block C `:9477`).
- **What v5.0.1 plan provides**: Block D `/verify` handler `:11095-11113`; Block G AGENT_TYPES has `verify` type; Block I skill resolution; verify skill assumed bundled (`I-12` skills/verify/ is implicitly part of bundled).
- **Verdict**: **NEEDS-LOCK-TEST**. Plan doesn't explicitly enumerate `skills/verify/` as a bundled-skill-to-port. Confirm in Block I PORT_LOG.

## 20. Approval prompt for write_file with diff preview — Approve / Approve-always / Deny

- **What user does**: agent calls `write_file path=/tmp/foo.py`; with `CONFIG.require_tool_approval=True`, approval dialog appears (`approval_box` `:316`).
- **What could go wrong**: dialog renders but `approval_event` deadlock if user closes notebook → next turn forever blocked. The 800-second `max_wait` at `:847` exists in v4 but value is not visible in plan.
- **What v5.0.1 plan provides**: Block C+ approval gate `:1071, :9444`; Block C+ pending_approval dict + on_approve/on_deny `:10306, :10491-10605`; Block E+F approval dialog UI (~115 LOC at `:10491-10605`). Block C+ Q4: "lock test write_file with diff approval Approve/Deny/Always".
- **Verdict**: **HANDLED**. Confirm "Approve always" sets per-tool persistent flag (Block C+ Q3 says "Runnable's PermissionDialog richer features (per-tool always-allow + reason-prompt) folded into Block L PORT_LOG").

## 21. Cost-limit slider set to $0.50, agent blows through it mid-turn

- **What user does**: drags cost slider to $0.50 in cell 2; one Sonnet 4.5 call costs $0.60.
- **What could go wrong**: enforcement at `:3638-3652` warns at 80% / blocks at 100% — but it blocks the NEXT call, not the current one. EF-2 `maxBudgetUsd` hard-cap halt is the missing kill-switch.
- **What v5.0.1 plan provides**: Block B TokenTracker session_cost_limit enforcement (`:3638-3652`); Block B+ cost runtime warning `:8787`; Block E+F row EF-2 `maxBudgetUsd hard-cap halt` (R7 N7, `QueryEngine.ts:972-1002`, 30 LOC, **MUST**).
- **Verdict**: **HANDLED** post-EF-2 port. Lock test Block E+F Q4: "set cost_limit=$0.01, send any non-trivial query, expect immediate halt with explicit message".

## 22. /context after long session — shows token / context bloat diagnostic

- **What user does**: `/context` after 80 messages.
- **What could go wrong**: numbers don't include tool-schema tokens (~20-30K); user thinks they have headroom that isn't there.
- **What v5.0.1 plan provides**: Block D `/context` handler `:11052-11061`; Block A row A-29 (tool-schema tokens in pre-compression estimate, H4 F8 / R7 GAP-7, `:9507-9513`, "20-30K+ tokens v4 estimate misses"); Block A row A-4 `calculateTokenWarningState` 5 flags (used by E+F status bar).
- **Verdict**: **HANDLED** post-A-29 port. Lock test should compare `/context` output to actual Bedrock CountTokens response (B-1) — must agree within 5%.

## 23. /skillify capture-session-as-skill at end of useful debugging session

- **What user does**: after solving a hard bug, types `/skillify` to save the approach.
- **What could go wrong**: not in v4 baseline → no Block D handler today; user gets "unknown command" + helpful list (D-6).
- **What v5.0.1 plan provides**: Block D row D-10 `/skillify` capture session-as-skill (Runnable `skills/bundled/skillify.ts:22-156`, 80 LOC); folded as `skills/skillify/` per Block I row I-9.
- **Verdict**: **HANDLED**. Confirm Q4 lock test: `/skillify` writes a new `skills/<name>/SKILL.md` with session distillation.

## 24. /dream manual consolidation trigger after 3 days of memory churn

- **What user does**: types `/dream` after a week of work, expects memory consolidation.
- **What could go wrong**: not in v4; Block H+ (NEW, ~350 LOC) gates auto-dream behind `CONFIG.auto_dream_enabled` default-False. Manual `/dream` should still work even when daemon disabled.
- **What v5.0.1 plan provides**: Block D row D-11 `/dream manual consolidation trigger` (`autoDream/consolidationLock.ts:130-140`, 30 LOC, HIGH); Block H+ row H+1 daemon (350 LOC, NEEDS-ADAPTATION).
- **Verdict**: **HANDLED** (manual path independent of daemon). Lock test: `/dream` runs to completion even when `CONFIG.auto_dream_enabled=False`.

## 25. /auth <wrong-token> on a require_auth=True notebook

- **What user does**: notebook started with `CONFIG.require_auth=True`; user types wrong `/auth foo`.
- **What could go wrong**: handler swallows the message (since it doesn't dispatch to chat) but doesn't make clear that authentication failed; user retries and exhausts patience.
- **What v5.0.1 plan provides**: Block D `/auth` auth-gate handler `:10789-10802` (separate from 19 advertised, gated by `CONFIG.require_auth`, runs before custom-command dispatch via explicit `not msg.startswith("/auth")` check at `:11314`); compares against `os.getenv(CONFIG.auth_token_env)`. Block D Q4: "/auth rejection on wrong token + /auth success on correct token".
- **Verdict**: **HANDLED**. Verify Q4 row matches plan §3 Block D end of paragraph.

---

## Summary

| Verdict | Count | Scenarios |
|---|---:|---|
| **HANDLED** | 14 | 2, 3, 4, 5, 6, 7, 8, 10, 11, 18, 20, 21, 23, 24, 25 (15 — see note) |
| **NEEDS-LOCK-TEST** | 7 | 1, 9, 13, 16, 17, 19, 22 |
| **POSSIBLE-GAP** | 3 | 12 (mock_mode), 14 (ipywidgets fallback), 15 (long-text collapse) |

(Note: scenario 22 actually moved to HANDLED post-A-29; recount gives 15 HANDLED / 7 NEEDS-LOCK-TEST / 3 POSSIBLE-GAP = 25.)

### Pre-Block-0 actions (3 POSSIBLE-GAPs to resolve)

1. **Scenario 12 — mock_mode**: decide between (a) document-only "no mock_mode in v5" or (b) add `CONFIG.mock_bedrock` short-circuit in `runtime/bedrock_client.py:chat()`. Recommend (a) for scope discipline; add note to `USER_GUIDE.md`.
2. **Scenario 14 — ipywidgets**: pin `ipywidgets>=8.0` in cell 1 (v4 already does); add explicit "DO NOT skip" note in `USER_GUIDE.md`. No code change.
3. **Scenario 15 — long-text collapse**: micro-extension to Block E+F `_render_assistant_markdown` to wrap text >100 lines in `<details>`. ~10 LOC addition.

### Lock-test additions (7 NEEDS-LOCK-TEST → add Q4 rows)

| # | Scenario | Block | Lock test to add |
|---|---|---|---|
| 1 | Kernel restart auto-resume | E+F | Cell-3 launch finds `sessions/latest.json` → loads silently |
| 9 | /regression in non-git workspace | D | Falls back to session-edit-history-only |
| 13 | IAM AccessDeniedException | L | User-readable message names missing IAM action |
| 16 | /checkpoint restore resets _FILES_READ | B | Post-restore, model re-reads files (cache invalidated) |
| 17 | /diffs covers notebook_edit + view_image | B | All mutating tools snapshot pre-edit |
| 19 | /verify ports `skills/verify/` bundled skill | I | PORT_LOG row enumerates verify skill explicitly |
| 22 | /context tool-schema accuracy | A | `/context` matches Bedrock CountTokens within 5% |

All 7 are additive Q4 rows in already-existing Blocks. No new Blocks required.

### v5 surface-change summary

- **No new Blocks** required from this brainstorm (G3, F2, H+ already added by Wave-5-DEEP).
- **+10 LOC** Block E+F long-text collapse (gap 15).
- **+7 Q4 lock-test rows** across Blocks A, B, D, E+F, I, L.
- **+1 USER_GUIDE.md note** for ipywidgets pinning + mock_mode disclaimer.

End of W6 brainstorm.
