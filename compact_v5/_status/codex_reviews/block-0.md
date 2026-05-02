Reading additional input from stdin...
OpenAI Codex v0.125.0 (research preview)
--------
workdir: D:\Github\sagemaker-coding-agent
model: gpt-5.3-codex
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, C:\Users\winst\.codex\memories]
reasoning effort: high
reasoning summaries: none
session id: 019deae6-f60d-75e2-a583-5d5b24c18432
--------
user
You are re-reviewing Block 0 of v5.0.1 — iteration #2 after addressing the
3 findings from your first review (saved at
_status/codex_reviews/block-0.md). The original first-pass verdict was
APPROVE_WITH_FIXES with [HIGH] UNDECLARED_PATTERN on no-deferrals
evidence, [MEDIUM] test-design drift, and [LOW] PORT_LOG #036 typo.

Changes applied since first pass:

(1) [HIGH] explicit remap table added to ADR-020 declaring per-item
    landing Block + lock-test path for each of Block 0 items 0-1..0-10.
    SYNTHESIS_MASTER.md §Block 0 head note added cross-linking to ADR-020.
    Files: compact_v5/_status/V5_DESIGN_DECISIONS.md (ADR-020 §Notes /
    known scope remaps), compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md
    (Block 0 table head note).

(2) [MEDIUM] TEST_DESIGN.md §Block 0 updated with implementation-note
    section explaining (a) T3 uses manual exec() not papermill (and why
    — papermill is not in the v5 ship-zip dep set; manual exec covers the
    smoke surface adequately under mock_mode), (b) T2 accepts ConsoleChatUI
    fallback when ipywidgets is unavailable (matches Phase 11 ADR-017
    factory contract).
    File: compact_v5/_phase_2/wave_6/TEST_DESIGN.md §Block 0.

(3) [LOW] sagemaker_agent.py docstring corrected: PORT_LOG #036 → #038.
    File: compact_v5/MAIN/agent/sagemaker_agent.py line 19.

Tests: 442 passed + 4 skipped (unchanged from first review).
verify_ship_zip.py: PASS.

Re-evaluate Block 0 against the same 3 axes (A: errors / B: v5 fit /
C: reference coverage). Does the remap table satisfy "no deferrals" by
declaring each 0-N item's implementation Block + lock test? Are there
any new findings introduced by the fix-up commits?

Read the same paths as before plus:
- compact_v5/_status/V5_DESIGN_DECISIONS.md §ADR-020 (look for the
  "Notes / known scope remaps" section with the 10-row remap table)
- compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md §Block 0 (head note
  immediately above the | # | Capability | ... | table — it now points
  readers to ADR-020 for the remap)
- compact_v5/_phase_2/wave_6/TEST_DESIGN.md §Block 0 (now has
  "Implementation notes" subsection)
- compact_v5/MAIN/agent/sagemaker_agent.py (PORT_LOG ref now #038)

FINAL: APPROVE | APPROVE_WITH_FIXES | REJECT.
codex
Reviewing Block 0 iteration #2 now with the same A/B/C axes and focus on whether the new ADR-020 remap fully closes the no-deferrals gap. I’ll read the listed files plus the prior review note, then report findings-first with a final verdict.
web search: 
web search: 
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Raw '_status/codex_reviews/block-0.md'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Raw 'compact_v5/_phase_2/wave_6/TEST_DESIGN.md'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Raw 'compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Raw 'compact_v5/_status/V5_DESIGN_DECISIONS.md'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Raw 'compact_v5/MAIN/agent/sagemaker_agent.py'" in D:\Github\sagemaker-coding-agent
 succeeded in 1284ms:
# v5.0.1 TEST DESIGN

**Date**: 2026-05-01
**Purpose**: define the per-Block test surface so the builder knows what to write, what proves "done", and what AWS cost each test incurs.
**Coverage**: all 21 Blocks + final ship gate.
**Constraint**: minimize AWS spend; max real-AWS cost across full build = ~$0.50.

---

## Test tier definitions

| Tier | Description | When | AWS cost |
|---|---|---|---|
| **T1 Unit** | pytest unit test, mocks all external (Bedrock, files only in tmpdir, no network) | every commit | $0 |
| **T2 Integration** | pytest integration test, mocked Bedrock with canned responses, real file IO + real subprocess | every Block close | $0 |
| **T3 Notebook smoke** | open `chat.ipynb` headlessly via `papermill` or `jupyter nbconvert --execute`, run cells 1-3, assert no error | every Block close | $0 |
| **T4 Zip extract+import** | `_rebuild_zip.py` then `verify_ship_zip.py` extracts in tmpdir + runs `python -c "import entry"` and `python -c "import sagemaker_agent"` | every Block close + before tag | $0 |
| **T5 Real-Bedrock single round-trip** | `RUN_REAL_BEDROCK=1 pytest tests/integration/test_real_bedrock_smoke.py::test_<name>` â€” one Haiku-4.5 round-trip per test | gated, only on 6 high-risk Blocks + Block J | ~$0.005-0.05 each |
| **T6 User acceptance** | YOU run a real task in SageMaker chat.ipynb with `session_cost_limit=$2.00` | per Block, after I commit | depends on session |

---

## Pass/fail criteria

A Block ships only when ALL of:
1. Every T1 + T2 test green
2. T3 smoke green (notebook cells 1-3 + open WidgetChatUI without error)
3. T4 zip extract+import green
4. T5 real-Bedrock smoke green (only for high-risk Blocks)
5. Codex 3-axis review APPROVE on the diff
6. T6 user acceptance â€” you say "go" to next Block

Any single failure = stop, fix, re-test, re-Codex, re-approve.

---

## Per-Block test plan

### Block 0 â€” `sagemaker_agent.py` shim + notebook smoke gate

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_smoke_imports` | T1 | `from sagemaker_agent import CONFIG, BEDROCK_MODELS, create_chat_ui` succeeds | $0 |
| `test_smoke_no_cso_warnings` | T1 | running shim with default LOG_LEVEL emits 0 WARNING-level CSO-CHECK lines (closes PS#1) | $0 |
| `test_chat_ipynb_cells_1_3` | T3 | chat.ipynb cells 1-3 parse + execute against mock Bedrock without exception (cell 1 = pip install, parse-only; cells 2-3 = exec under mock_mode=True). Equivalent to `papermill` for the smoke surface; chosen because papermill is not in the v5 ship-zip dep set and Bedrock smoke does not need a real kernel. | $0 |
| `test_widget_chat_ui_renders` | T2 | `create_chat_ui()` returns a chat-UI handle wired to a real Agent. Accepts `WidgetChatUI` (with non-empty `_panel`) when ipywidgets is installed; falls back to `ConsoleChatUI` (with non-empty `render()`) when ipywidgets is unavailable â€” matches Phase 11 ADR-017 fallback contract. | $0 |
| `test_v4_import_compat` | T1 | every name v4 chat.ipynb references (`CONFIG`, `BEDROCK_MODELS`, `create_chat_ui` per `compact_v4/MAIN/agent/chat.ipynb` cells 2+3) is re-exported through `sagemaker_agent` AND listed in `__all__` | $0 |

**Block 0 ships when**: 5/5 green. **Total AWS cost: $0.**

**Implementation notes (post-Block-0 â€” Codex AXIS A finding #2 lock)**:
- T3 is implemented with manual `exec()` of cell sources rather than papermill. Reason: papermill pulls in jupyter_client + ipykernel + nbclient as install-time deps (~50 MB), which the v5 ship zip does not carry, and the smoke surface (parse + exec under mock_mode) does not require a live kernel. The implementation pre-snapshots every CONFIG field via `monkeypatch` so cell 2's CONFIG mutations don't leak into other tests (this caught a real test-isolation bug at Block 0 build time).
- T2 accepts ConsoleChatUI fallback because the Phase 11 factory branches on ipywidgets availability (`_IPYWIDGETS_OK`). On a CI runner without ipywidgets, the WidgetChatUI branch is unreachable; the fallback is the production behavior and is what users with no widget host will see.

---

### Block B â€” TokenTracker + AuditLogger + SnapshotManager + Runnable tokenEstimation

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_token_tracker_singleton` | T1 | `TOKENS` is the singleton; `update()` accumulates correctly | $0 |
| `test_audit_logger_writes_jsonl` | T1 | every audit entry writes valid JSONL line to `audit_logs/<session>.jsonl` | $0 |
| `test_snapshot_manager_creates_backup` | T1 | edit_file creates `.snapshot/<file>_<ts>.bak` | $0 |
| `test_token_tracker_per_agent_breakdown` | T1 | `TOKENS.parent_input_tokens` + `TOKENS.subagent_input_tokens["build"]` accumulate independently | $0 |
| `test_count_tokens_with_bedrock_mocked` | T2 | mocked `bedrock-runtime.count_tokens` response parsed correctly | $0 |
| `test_token_accounting_input_cumulative` | T1 | per turn: input KEEPS-LATEST (not sum), output SUMS (R7 N8 fix) | $0 |
| `test_haiku_excluded_from_cache_break` | T1 | Haiku-4.5 model_id added to `EXCLUDED_MODELS_FOR_CACHE_BREAK` set; cache-break detector skips it (R4 #14 MUST) | $0 |
| `test_count_tokens_real_bedrock_haiku` | T5 | one real `count_tokens` call to Haiku-4.5 returns positive int matching mock contract | ~$0.005 |

**Block B ships when**: 8/8 green. **Total AWS cost: ~$0.005.**

---

### Block B+ â€” SessionManager + cost-limit + AGENT_STATUS + FileCache thread-local

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_session_manager_atomic_save` | T1 | save â†’ tmp file â†’ atomic rename; partial-write doesn't corrupt | $0 |
| `test_session_save_load_preserves_cost` | T1 | save at $2.09 â†’ load â†’ `TOKENS.session_cost == 2.09` (closes PS#5) | $0 |
| `test_session_cost_limit_blocks_at_100pct` | T1 | when `session_cost > session_cost_limit`, agent halts with explicit message | $0 |
| `test_agent_status_auto_load` | T1 | first `Agent.run()` call reads `AGENT_STATUS.md` and injects into system prompt | $0 |
| `test_filecache_thread_local_isolation` | T2 | parent `_FILES_READ` not visible inside sub-agent thread context (uses verified v4 APIs `save_and_clear_context` + `enter_thread_local_context`) | $0 |
| `test_subagent_token_attribution` | T2 | spawn parent + sub-agent â†’ assert `TOKENS.parent_input_tokens > 0` AND `TOKENS.subagent_input_tokens["build"] > 0` AND `session_cost == sum_of(per_agent_cost) Â± $0.0001` | $0 |
| `test_tokens_singleton_is_budget_source` | T1 | budget checks read TOKENS singleton, NOT Agent attribute (closes PS#6) | $0 |

**Block B+ ships when**: 7/7 green. **Total AWS cost: $0.**

---

### Block C â€” Runtime safety + secret scanner + JSON repair + injection scan + bash hardening

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_exec_limit_200_then_201_blocked` | T2 | run 200 mocked bash â†’ 201st returns exact error including `OTHER TOOLS STILL WORK: read_file, grep, glob, edit_file, write_file, notebook_edit, task, ask_user, view_image, web_fetch are NOT counted by this limit.` (closes PS#7) | $0 |
| `test_repetition_detector_blocks_3rd_dup` | T2 | same `read_file(path=X)` 3 times â†’ 3rd blocked with dedup message | $0 |
| `test_security_manager_blocks_dangerous_rm` | T1 | `bash("rm -rf /")` returns DANGER block message | $0 |
| `test_security_manager_blocks_etc_passwd` | T1 | `read_file("/etc/passwd")` returns PATH-VALIDATION block | $0 |
| `test_security_manager_blocks_aws_destroy` | T1 | `bash("aws s3 rm s3://prod --recursive")` blocked | $0 |
| `test_secret_scanner_38_patterns` | T1 | each of 38 secret patterns (13 v4 + 25 from Runnable) detects + redacts in test fixture | $0 |
| `test_json_repair_malformed_args` | T1 | `_repair_tool_call_arguments({"foo":"bar)` â†’ `{"foo":"bar"}` (Hermes :547-641); empty `{}` fallback if irrecoverable | $0 |
| `test_injection_scanner_v4_native` | T1 | `_scan_for_prompt_injection` detects v4's 12 patterns + invisible chars (v4:7509-7541) | $0 |
| `test_files_read_thread_local_save_restore` | T1 | `save_and_clear_context()` + `restore_context()` + `enter_thread_local_context()` all from v4:893-1017 verbatim | $0 |
| `test_quote_normalization_curly_to_straight` | T1 | edit_file with `"foo"` matches `"foo"` (curly quotes) (R1 #115) | $0 |
| `test_utf16_bom_detected` | T1 | edit_file on Notepad-saved file (UTF-16 LE BOM) handled correctly (R1 #121) | $0 |
| `test_unc_path_skip_windows` | T1 | `\\\\server\\share\\file.txt` rejected on Windows (NTLM credential leak prevention) (R1 #123) | $0 |

**Block C ships when**: 12/12 green. **Total AWS cost: $0.**

---

### Block C+ â€” Approval/diff + rate limits + ipywidgets fallback + PermissionDialog richer

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_approval_gate_blocks_until_approve` | T2 | write_file with `require_tool_approval=True` blocks; mock approve â†’ unblocks | $0 |
| `test_approval_dialog_shows_diff` | T2 | `pending_approval` UI renders colored diff (red/green/gray context) | $0 |
| `test_approval_per_tool_always_allow` | T2 | "Always allow" sets `_always_allowed[tool_name]=True`; subsequent calls skip dialog | $0 |
| `test_rate_limit_100_per_min` | T2 | 101st message in 60s window â†’ rate-limit error with countdown | $0 |
| `test_stop_button_halts_run` | T2 | `Agent.stop()` mid-tool-loop sets stop flag; QueryEngine respects it | $0 |
| `test_ipywidgets_fallback_text_mode` | T2 | when `ipywidgets` unavailable, `WidgetChatUI` falls back to `ConsoleChatUI` with `ask_user`-text-mode for approvals (60s watchdog timeout) | $0 |
| `test_permission_dialog_reason_prompt` | T2 | dialog shows model's "reason" string from tool_use args | $0 |

**Block C+ ships when**: 7/7 green. **Total AWS cost: $0.**

---

### Block D â€” Slash commands (19 advertised + /auth + /simplify expander + /init + /init-verifiers + /skillify + /dream + /promote-to-skill)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_slash_dispatch_/cost` | T2 | `/cost` returns formatted 4-line cost block | $0 |
| `test_slash_dispatch_/status` | T2 | `/status` returns status with model + active skills + phase | $0 |
| `test_slash_dispatch_/save_<name>` | T2 | `/save mywork` writes `sessions/mywork.json` with full state | $0 |
| `test_slash_dispatch_/load_<name>` | T2 | `/load mywork` restores state including `TOKENS.session_cost` | $0 |
| `test_slash_dispatch_/compact` | T2 | `/compact` invokes `Compactor.compact()` (Block A trigger) | $0 |
| `test_slash_dispatch_/clean` | T2 | `/clean` removes `audit_logs/` + `sessions/` + `.snapshots/` files | $0 |
| `test_slash_dispatch_/skills_list` | T2 | `/skills` lists all 10 skills | $0 |
| `test_slash_dispatch_/skill_use_clara` | T2 | `/skill use clara` resolves `clara` â†’ `clara-review` (fuzzy from Block I) | $0 |
| `test_slash_dispatch_/skill_apply_proposal` | T2 | `/skill apply <name>` shows diff + applies | $0 |
| `test_slash_dispatch_/revert_<file>` | T2 | `/revert path/to/file.py` rolls back to last snapshot | $0 |
| `test_slash_dispatch_/context` | T2 | `/context` shows token/context bloat diagnostic | $0 |
| `test_slash_dispatch_/verify_quick` | T2 | `/verify quick` invokes verify skill | $0 |
| `test_slash_dispatch_/checkpoint_create_v1` | T2 | `/checkpoint create v1` snapshots all touched files | $0 |
| `test_slash_dispatch_/checkpoint_restore_v1` | T2 | `/checkpoint restore v1` rolls back all to v1 state | $0 |
| `test_slash_dispatch_/phase_text` | T2 | `/phase Phase 2 build` sets work-phase tag in status bar | $0 |
| `test_slash_dispatch_/diffs_summary` | T2 | `/diffs summary` shows session edit history summary | $0 |
| `test_slash_dispatch_/regression` | T2 | `/regression` runs `git diff HEAD --stat` + suggests test cmd | $0 |
| `test_slash_dispatch_/done_quick` | T2 | `/done quick` runs simplify â†’ verify pipeline â†’ READY-TO-SHIP verdict | $0 |
| `test_slash_dispatch_/commands` | T2 | `/commands` lists custom commands from `agent_config.json` | $0 |
| `test_slash_dispatch_/auth_token` | T2 | `/auth <token>` validates against `os.getenv(CONFIG.auth_token_env)` (when `require_auth=True`) | $0 |
| `test_slash_dispatch_/simplify_falls_through_to_skill` | T2 | `/simplify` (no dedicated handler) hits expander at `:11330` â†’ resolves to `skills/simplify/SKILL.md` | $0 |
| `test_slash_dispatch_/dream_invokes_consolidation` | T2 | `/dream` invokes Block H+ memory consolidation (manual-only) | $0 |
| `test_slash_dispatch_/init_scaffolds_claude_md` | T2 | `/init` generates project CLAUDE.md from interactive prompt | $0 |
| `test_slash_dispatch_/skillify_captures_session` | T2 | `/skillify` runs 4-round AskUserQuestion â†’ saves new skill | $0 |
| `test_slash_dispatch_/promote_to_skill` | T2 | `/promote-to-skill` writes proposal to `state/skill-proposals/` | $0 |
| `test_dispatcher_unknown_slash_falls_through` | T2 | `/unknown_command` not in registry â†’ falls through to chat (not error) | $0 |

**Block D ships when**: 26/26 green. **Total AWS cost: $0.**

---

### Block A â€” Compactor + cold-cache + auto-compact (COMBINED v4 + Runnable)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_compactor_2stage_prune_plus_llm_summary` | T2 | mocked LLM summary; assert prune step removes tool outputs older than threshold; LLM step generates 13-section template | $0 |
| `test_microcompact_threshold_70pct` | T2 | when `total_tokens / context_window > 0.70` â†’ microcompact fires | $0 |
| `test_context_collapse_threshold_85pct` | T2 | when > 0.85 â†’ context_collapse fires | $0 |
| `test_cold_cache_30min_idle_triggers_microcompact` | T2 | mock `time.time()` to simulate 30min idle â†’ next msg â†’ microcompact fires + log line `[i] Cold cache detected` (closes PS#3) | $0 |
| `test_keep_last_n_cold_cache_1` | T2 | after cold-cache compact, only last 1 message retained | $0 |
| `test_post_compact_files_read_clear` | T2 | after compact, `_FILES_READ.clear()` runs (model can re-read files) | $0 |
| `test_post_compact_todo_restoration_message` | T2 | after compact, `build_todo_restoration_message` injected | $0 |
| `test_auto_compact_circuit_breaker_3_failures` | T2 | 3 consecutive `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES` â†’ autoCompact disabled with warning | $0 |
| `test_cache_edits_per_tool_invalidation` | T2 | per-tool schema hash change â†’ only that tool's cache invalidated | $0 |
| `test_a28_cache_invariant_no_mid_session_rebuild` | T2 | system prompt rebuild attempted mid-conversation â†’ blocked with warning (`/cmd --now` opt-in only) | $0 |
| `test_h2_stub_injection_for_orphan_tool_use` | T2 | post-compact, dangling `tool_use` block â†’ synthetic `tool_result` stub injected (prevents Bedrock 400) | $0 |
| `test_compact_fires_real_haiku_long_context` | T5 | real Haiku-4.5 round-trip with 80K+ token input â†’ triggers compact â†’ next call succeeds | ~$0.01 |

**Block A ships when**: 12/12 green. **Total AWS cost: ~$0.01.**

---

### Block E+F â€” HTML chat rendering + cell 2 widgets + complete session UI + IterationBudgetWidget + ThinkingBudgetWidget

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_render_chat_user_message` | T1 | `render_chat()` produces HTML with user message in correct color | $0 |
| `test_render_chat_assistant_markdown` | T1 | `_render_assistant_markdown()` converts markdown â†’ HTML (code blocks, tables, lists) | $0 |
| `test_render_todos_status_icons` | T1 | TODO list renders with âœ…/ðŸ”„/â¬œ icons | $0 |
| `test_update_tokens_display_shows_pct` | T1 | token display shows `X / Y (Z%)` and `cache hit %` | $0 |
| `test_update_mode_display_status_bar` | T1 | status bar shows model + active skills + phase + cost | $0 |
| `test_dark_mode_toggle_swaps_theme` | T2 | dark-mode toggle swaps theme dict; chat re-renders | $0 |
| `test_model_dropdown_lists_all_models` | T2 | dropdown contains Haiku-4.5 + Sonnet-4.6 + Opus options | $0 |
| `test_iteration_budget_widget_shows_used_total` | T1 | widget HTML shows `<progress>` + `used/total` + color cue (closes PS#2 visible UI) | $0 |
| `test_thinking_budget_widget_shows_on_off` | T1 | widget HTML shows `thinking=ON\|OFF, budget=N tokens` (closes PS#4 visible UI) | $0 |
| `test_session_dropdown_lists_saves` | T2 | session dropdown lists all `sessions/*.json` files | $0 |
| `test_session_load_button_restores` | T2 | clicking load â†’ `SessionManager.load()` â†’ state restored | $0 |
| `test_auto_save_on_send` | T2 | every send auto-saves to `last_session.json` | $0 |
| `test_long_text_details_collapse` | T1 | text > 5000 chars wrapped in `<details><summary>show more</summary>...</details>` (Wave 6 GAP fix) | $0 |
| `test_thinking_config_sent_every_call` | T1 | mocked BedrockClient.chat: thinking config in every payload (closes PS#4) | $0 |

**Block E+F ships when**: 14/14 green. **Total AWS cost: $0.**

---

### Block F2 â€” Auto-continuation under iteration budget

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_f2_auto_continue_at_under_90pct` | T2 | iteration_used < 90% AND not diminishing-returns â†’ auto-continue | $0 |
| `test_f2_blocks_at_90pct` | T2 | iteration_used >= 90% â†’ halts + asks user | $0 |
| `test_f2_respects_cost_cap` | T2 | even if iteration_used < 90%, if `session_cost > session_cost_limit` â†’ halt | $0 |

**Block F2 ships when**: 3/3 green. **Total AWS cost: $0.**

---

### Block I â€” Skill name resolution + Hermes fuzzy + paths frontmatter + scaffolders

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_skill_resolve_by_directory_name` | T1 | `/skill use clara-review` â†’ loads `skills/clara-review/SKILL.md` | $0 |
| `test_skill_resolve_by_metadata_name` | T1 | `/skill use Clara` (metadata `name: Clara`) â†’ loads `skills/clara-review/` | $0 |
| `test_skill_fuzzy_match_typo` | T1 | `/skill use verfy` â†’ fuzzy resolves to `verify` (Hermes :4689-4720) | $0 |
| `test_skill_paths_frontmatter_auto_activate` | T2 | skill with `paths: ["*.py"]` auto-activates when user edits .py file | $0 |
| `test_skill_disable_model_invocation` | T2 | skill with `disable_model_invocation: true` not visible to model but callable by user | $0 |
| `test_skill_enabled_when_config_flag` | T2 | skill with `enabled_when: CONFIG.advanced_mode` only loads when flag True | $0 |
| `test_skillify_4_round_interview` | T2 | `/skillify` runs 4 AskUserQuestion rounds â†’ writes `skills/<new>/SKILL.md` | $0 |
| `test_skill_manager_realpath_dedup` | T1 | symlink to same dir loaded once (R9 #23 bug fix) | $0 |

**Block I ships when**: 8/8 green. **Total AWS cost: $0.**

---

### Block M â€” Phase 8 critical fixes (per-turn discovery reset + structured-output retry counter)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_discovered_tool_names_reset_per_turn` | T1 | `self._discovered_tool_names` resets at start of each turn (not just run-start) | $0 |
| `test_structured_output_retry_limit_3` | T1 | `countToolCalls` blocks at retry limit 3 â†’ halts with explicit message | $0 |
| `test_infinite_loop_blocked_at_retry_limit` | T2 | model returns malformed structured output 3x â†’ halt | $0 |

**Block M ships when**: 3/3 green. **Total AWS cost: $0.**

---

### Block G â€” AGENT_TYPES + worktree + handoff/env

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_agent_types_dict_has_7` | T1 | `AGENT_TYPES.keys() == {build, plan, explore, verify, general, review, fork}` | $0 |
| `test_subagent_build_spawns_worktree` | T2 | `task(subagent_type="build")` creates `worktrees/<id>/` (mocked git) | $0 |
| `test_subagent_verify_loads_verify_skill` | T2 | `task(subagent_type="verify")` loads verify skill in sub-agent context | $0 |
| `test_subagent_handoff_block_built` | T1 | `_build_subagent_handoff_block()` produces v4-equivalent text | $0 |
| `test_subagent_env_details_built` | T1 | `_build_subagent_env_details()` includes cwd + git status + tool list | $0 |
| `test_max_subagent_depth_2_blocks_grandchild` | T2 | parent â†’ child OK; child â†’ grandchild blocked with `MAX_SUBAGENT_DEPTH=2` error (Wave 6 GAP fix) | $0 |
| `test_iteration_budget_shared_object_identity` | T2 | parent and sub-agent share SAME `IterationBudget` object (object identity check) | $0 |
| `test_worktree_cleanup_on_completion` | T2 | sub-agent completion removes worktree | $0 |

**Block G ships when**: 8/8 green. **Total AWS cost: $0.**

---

### Block G3 â€” Coordinator System Prompt (NEW)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_coordinator_prompt_contains_4_phases` | T1 | system prompt for `task` tool contains "Research â†’ Synthesis â†’ Implementation â†’ Verification" | $0 |
| `test_coordinator_prompt_synthesize_dont_delegate` | T1 | prompt contains "NEVER delegate understanding" | $0 |
| `test_coordinator_prompt_continue_vs_spawn_table` | T1 | prompt contains continue-vs-spawn decision table | $0 |
| `test_coordinator_prompt_research_parallel_write_serial` | T1 | prompt contains "Read-only tasks: run in parallel; Write tasks: one at a time" | $0 |
| `test_coordinator_prompt_real_haiku_orchestration` | T5 | real Haiku-4.5 round-trip: prompt agent to coordinate 3 sub-agents â†’ assert it spawns parallel reads, serial writes | ~$0.01 |

**Block G3 ships when**: 5/5 green. **Total AWS cost: ~$0.01.**

---

### Block G2 â€” forkSubagent cache-prefix replay

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_forkSubagent_byte_identical_prefix` | T1 | parent + child API requests have BYTE-identical prefix when `cache_prefix_share=True` | $0 |
| `test_forkSubagent_cache_aware_serialization` | T1 | message serialization deterministic (sorted keys, no random IDs in prefix) | $0 |
| `test_g2_cache_prefix_real_bedrock` | T5 | real Bedrock call: parent + child â†’ second call cache_read_input_tokens > 0 (cache hit verified) | ~$0.01 |

**Block G2 ships when**: 3/3 green. **Total AWS cost: ~$0.01.**

---

### Block H â€” Memory extraction (COMBINED v4 + Runnable extractMemories + sessionMemory)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_extract_and_append_memories_v4_session_end` | T1 | session-end trigger writes new entries to `memory.md` (v4 behavior) | $0 |
| `test_extract_memories_closure_scoped_state` | T1 | extractMemories has closure-scoped throttle state (Runnable pattern) | $0 |
| `test_session_memory_dedup_before_write` | T1 | `sessionMemoryUtils` deduplicates before writing memory.md | $0 |
| `test_adjust_index_preserves_api_invariants` | T1 | `adjustIndexToPreserveAPIInvariants` returned indices keep tool_use/tool_result paired (R4 #56 MUST) | $0 |
| `test_memory_extraction_handles_empty_session` | T1 | session with 0 user messages â†’ no extraction, no error | $0 |
| `test_session_memory_compact_no_400_sequence` | T2 | compact run on session with mixed tool_use/tool_result â†’ resulting messages valid for Bedrock | $0 |

**Block H ships when**: 6/6 green. **Total AWS cost: $0.**

---

### Block H+ â€” Memory consolidation engine (`/dream` MANUAL ONLY, no daemon)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_dream_4_phase_prompt_orient_gather_consolidate_prune` | T1 | dream prompt contains 4 phases in correct order | $0 |
| `test_dream_lock_file_prevents_concurrent_runs` | T1 | `dream.lock` file blocks 2nd `/dream` invocation | $0 |
| `test_dream_rollback_on_failure` | T2 | mid-run failure â†’ `memory.md.bak` restored; original `memory.md` untouched | $0 |
| `test_dream_no_daemon_no_auto_fire` | T1 | search v5 codebase: no `Thread`/`asyncio.create_task`/`atexit.register(dream)`/`SAGEMAKER_AUTO_DREAM` env var (verifies user decision 2026-05-01) | $0 |
| `test_dream_real_consolidation_haiku` | T5 | real `/dream` invocation on test memory.md â†’ outputs cleaner file (~$0.05) | ~$0.05 |

**Block H+ ships when**: 5/5 green. **Total AWS cost: ~$0.05.**

---

### Block L â€” Error/retry/cache-break + Bedrock guardrails + daemon-thread call

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_categorize_retryable_18_error_types` | T1 | each of 18 Runnable error categories â†’ correct retryable verdict (R4 18 categories) | $0 |
| `test_parse_max_tokens_overflow_recovers` | T1 | `parseMaxTokensContextOverflowError` triggers compact + retry (R4 #2 MUST) | $0 |
| `test_extract_nested_error_message_humanizes_5xx_html` | T1 | Bedrock 5xx with raw HTML â†’ user sees clean error message (R4 #9 MUST) | $0 |
| `test_retry_after_header_parsed` | T1 | `getRetryAfterMs` parses `Retry-After: 5` â†’ 5000ms wait | $0 |
| `test_per_tool_cache_break_detection` | T1 | per-tool schema hash change â†’ `notifyCacheDeletion` fires for that tool only | $0 |
| `test_haiku_excluded_from_cache_break_3loc` | T1 | Haiku-4.5 model_id in EXCLUDED set â†’ cache-break detector skips (R4 #14 MUST) | $0 |
| `test_daemon_thread_bedrock_call_responds_to_ctrl_c` | T2 | Bedrock call wrapped in daemon thread; main thread Ctrl-C raises KeyboardInterrupt cleanly | $0 |
| `test_30s_heartbeat_during_long_call` | T2 | heartbeat ping every 30s during long call â†’ status bar updates | $0 |

**Block L ships when**: 8/8 green. **Total AWS cost: $0.**

---

### Block N â€” Parallel tool execution + dynamic tool refs + dedup + fuzzy + ephemeral prompt

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_parallel_exec_3_independent_reads` | T2 | 3 read_file calls dispatched in parallel â†’ completion in MAX(call_time), not SUM | $0 |
| `test_parallel_exec_path_conflict_serializes_writes` | T2 | 2 write_file to same path â†’ serialized (not parallel) | $0 |
| `test_tool_call_dedup_blocks_redundant` | T2 | same `(tool_name, args)` 3x in one batch â†’ 2 calls deduped | $0 |
| `test_fuzzy_tool_name_typo_resolves` | T1 | `read_filee` â†’ fuzzy resolves to `read_file` | $0 |
| `test_ephemeral_system_prompt_not_persisted` | T1 | ephemeral prompt fragment not written to session log | $0 |
| `test_dynamic_tool_ref_injection_at_init` | T1 | tool schemas at init have cross-references injected (Hermes A36) | $0 |
| `test_max_tool_workers_4` | T1 | `_MAX_TOOL_WORKERS=4` constant; 5 parallel calls â†’ 4 in flight + 1 queued | $0 |
| `test_n7_partial_tool_names_warning_on_disconnect` | T2 | mid-call disconnect â†’ warning + synthetic tool_result stub | $0 |
| `test_n_real_3_parallel_reads_haiku` | T5 | real Bedrock 3 parallel read_file calls â†’ wallclock < SUM (validate ~40% gain) | ~$0.005 |

**Block N ships when**: 9/9 green. **Total AWS cost: ~$0.005.**

---

### Block T â€” v4 tool surface parity (11 missing tools)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_tool_create_word_writes_docx` | T1 | `create_word(filepath="x.docx", content="# h")` writes valid .docx | $0 |
| `test_tool_create_excel_with_chart` | T1 | `create_excel(...,chart_type="bar")` writes .xlsx with embedded chart | $0 |
| `test_tool_create_markdown` | T1 | `create_markdown` writes .md file | $0 |
| `test_tool_create_notebook_cells` | T1 | `create_notebook(cells=[...])` writes valid .ipynb | $0 |
| `test_tool_create_chart_png` | T1 | `create_chart(chart_type="bar")` writes valid PNG | $0 |
| `test_tool_create_pdf_sections` | T1 | `create_pdf(content=[heading,text,table,image])` writes valid .pdf | $0 |
| `test_tool_todo_write_round_trip` | T1 | `todo_write([{"content":"x","status":"pending","activeForm":"Doing x"}])` then `todo_read()` returns same | $0 |
| `test_tool_semantic_search_index_then_search` | T2 | `semantic_search(action="index", path=".")` then `action="search", query="..."` returns hits | $0 |
| `test_tool_web_fetch_html_to_markdown` | T2 | mocked HTTP response â†’ `web_fetch` returns markdown text | $0 |
| `test_tool_ask_user_blocks_then_unblocks` | T2 | `ask_user` blocks until user responds; mock response unblocks | $0 |
| `test_tool_create_html_via_write_file_documented` | T1 | docs note: `create_html` not a separate tool; use `write_file(*.html)` (Wave 6 design note) | $0 |

**Block T ships when**: 11/11 green. **Total AWS cost: $0.**

---

### Block J â€” Real-Bedrock smoke + zip extract+import (THE SHIP GATE)

This is THE final gate before tagging. **All real-AWS testing concentrates here.**

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_zip_rebuild_succeeds` | T4 | `python _rebuild_zip.py` produces `compact_v5.zip` | $0 |
| `test_zip_extract_in_tmpdir` | T4 | `verify_ship_zip.py` extracts zip in fresh tmpdir | $0 |
| `test_zip_python_c_import_entry` | T4 | `python -c "import entry"` succeeds in extracted dir | $0 |
| `test_zip_python_c_import_sagemaker_agent` | T4 | `python -c "import sagemaker_agent; sagemaker_agent.create_chat_ui()"` succeeds | $0 |
| `test_real_bedrock_hello_world` | T5 | real Haiku-4.5 round-trip: send "say hello", assert non-empty text response | ~$0.005 |
| `test_real_bedrock_tool_use_round_trip` | T5 | real Haiku-4.5: send "list files in /tmp", assert tool_use(name="list_dir") + tool_result + final text | ~$0.005 |
| `test_real_bedrock_compact_then_continue` | T5 | real call with 80K-token preamble â†’ compact fires â†’ next call succeeds with reduced prefix | ~$0.01 |

**Block J ships when**: 7/7 green. **Total AWS cost: ~$0.02.**

This block + the per-block T5 tests = total ~$0.10 across the entire build.

---

### Block K â€” Process discipline (LF AXIS C + per-block user gate + STATE/RESUME + 3-critic + A44 test refactor)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_axis_c_template_present` | T4 | `_status/CODEX_REVIEW_TEMPLATE.md` contains AXIS A + AXIS B + AXIS C sections | $0 |
| `test_state_resume_anchor_per_block` | T4 | every Block tag has corresponding `V5_BUILD_STATUS.md` "Last commit sha" matching | $0 |
| `test_per_block_user_approval_gate_documented` | T4 | `RESUME.md` Step 5 contains "Tag is FORBIDDEN if any open Codex finding has severity â‰¥ CHANGES_REQUESTED" | $0 |
| `test_a44_no_change_detector_tests_audit` | T4 | scan `tests/` for `assert "X" in MODELS` / `assert COUNT == N` â€” fail if found (rewrite as invariant) | $0 |
| `test_lint_phase_id` | T4 | `tests/lint_phase_id.py` validates tag name + status field + codex review filename match | $0 |

**Block K ships when**: 5/5 green. **Total AWS cost: $0.**

---

---

## R-tier â€” high-value real-AWS scenarios (added 2026-05-01 per user directive)

User directive: "AWS test allowed but must be carefully designed and optimized for v5 to collect MOST value to see if user using it without any semantic bugs."

These are end-to-end USER-SIMULATING scenarios run on real Bedrock. Each has a hard cost cap. Run after Block K (process discipline) lands but before tag.

| # | Scenario | What it catches | Model | Cost cap |
|---|---|---|---|---|
| **R1** | 50-turn dashboard build: read CSV â†’ python_exec to summarize â†’ create_chart â†’ create_word with embedded chart | Tool dispatch round-trips end-to-end, parallel exec wallclock gain on real Bedrock, security gate with real bash, .docx output integrity | Haiku-4.5 | $1.00 |
| **R2** | Long context: load 80K-token preamble â†’ ask "refactor this module" â†’ verify compaction fires + cache_edits invalidates only changed tools | Block A semantic correctness on Bedrock cache; A28 invariant on real cache hit | Haiku-4.5 | $0.50 |
| **R3** | Sub-agent dispatch: parent spawns 3 parallel research sub-agents â†’ synthesize â†’ write report. Verify cache-prefix replay shares cache | Block G + G2 + G3 cache-prefix bytes-stable on real Bedrock | Haiku-4.5 | $0.50 |
| **R4** | 30-min idle: send msg â†’ wait 30min real-time â†’ send next. Verify cold-cache compact fires + saves â‰¥5K tokens | PS#3 structural fix end-to-end | Haiku-4.5 | $0.20 |
| **R5** | 200-bash: agent loops python_exec 200x. 201st returns exact "OTHER TOOLS STILL WORK" message; agent continues with read_file/grep | PS#7 structural fix end-to-end | Haiku-4.5 | $0.50 |
| **R6** | Memory consolidation: build memory.md to 100 entries â†’ `/dream` â†’ verify deduplication + categorization works | Block H+ semantic correctness; rollback on fail; lock prevents concurrent | Haiku-4.5 | $0.30 |
| **R7** | Model switch mid-conversation: 10 turns on Haiku â†’ user changes dropdown â†’ next turn uses Sonnet. **A28 invariant**: prompt cache NOT rebuilt mid-conversation; switch applies next session | Hermes A28 critical policy on real Bedrock | Haikuâ†’Sonnet | $0.50 |
| **R8** | Error recovery: mock Bedrock return malformed JSON tool args â†’ multi-pass repair works â†’ if irrecoverable, `{}` fallback used + agent continues | Block C JSON repair end-to-end | Haiku-4.5 (mocked) | $0.20 |
| **R9** | Approval flow: write_file â†’ diff_widget renders â†’ user clicks Approve/Deny/Always â†’ decision propagates to TOKENS + AUDIT + SNAPSHOTS | Block C+ approval flow end-to-end | Haiku-4.5 | $0.30 |
| **R10** | Save/load: spend $1 in turns â†’ `/save mytest` â†’ restart kernel â†’ `/load mytest` â†’ verify `TOKENS.session_cost == $1.00` and chat history restored | PS#5 + PS#6 structural fix on real session | Haiku-4.5 | $1.00 |
| **R11** | Sonnet end-to-end: same as R1 but on Sonnet-4.6. Catches model-specific behavior differences | Sonnet-4.6 | $1.50 |
| **R12** | Multi-tool malformed args stress: model returns `{"path": "/tmp/", "content": "<UNCLOSED` â†’ JSON repair fires; model returns surrogate-pair Unicode â†’ sanitizer fires | Block L Bedrock error categories; H1 surrogate sanitize | Haiku-4.5 | $0.20 |

**R-tier total cost cap: ~$7.00** (worst case all hit cost cap; realistic ~$3-5).

Each R-test:
- Hard `session_cost_limit` set to its cap; agent halts if exceeded
- Test passes if scenario completes + assertions green
- Test fails (and is investigated) if Bedrock returns error, cost cap hit, or assertion fails
- Failed R-test = stop, fix, re-test before tag

---

## Per-Block close ritual (NOT a separate test, but a discipline the builder follows)

User directive 2026-05-01: status, git push, HTML, rezip must all be part of implementation plan.

These run at EVERY Block close per Block K + project CLAUDE.md rules:

| Action | When | Tool | Cost |
|---|---|---|---|
| Update `_status/V5_BUILD_STATUS.md` (Last updated, Last commit sha, State, Next session pickup) | end of every Block | manual edit | $0 |
| Append PORT_LOG rows to `_status/V5_RUNNABLE_PORT_LOG.md` for that Block (each row references one source file:line + Codex verdict) | end of every Block | manual append | $0 |
| Append ADR(s) to `_status/V5_DESIGN_DECISIONS.md` for any non-trivial choice in this Block | end of every Block | manual append | $0 |
| Save Codex AXIS A/B/C review to `_status/codex_reviews/block-<X>.md` | end of every Block | save Codex output | $0 (Codex run is per-Block) |
| Git commit (`git add <specific files>` then `git commit -m "..."`); NEVER `git add -A` (per user project rule, prevents .env / credentials) | end of every Block | git | $0 |
| Run pytest `tests/` (T1+T2) green | end of every Block | pytest | $0 |
| Run `python verify_ship_zip.py` (T4) green | end of every Block | python | $0 |
| **Rebuild `compact_v5.zip`** via `python _rebuild_zip.py`; verify size + manifest sane | end of every Block (catches packaging regressions early) | python | $0 |
| Tag `v5.0.1-block-<X>` ONLY after Codex APPROVE + user approval | end of every Block, after gates pass | git tag | $0 |
| **Push to `sageagent` remote** (per user project rule for sagemaker-coding-agent) | end of every Block, after tag | `git push sageagent v5-build && git push sageagent v5.0.1-block-<X>` | $0 |
| **Update HTML companion docs** if architecture changed (Block E+F changes UI; Block A changes compaction; Block B changes cost; Block H changes memory; Block N changes parallel exec). HTML is at `compact_v5/docs/` if exists OR `compact_v4/MAIN/agent/docs/` for v4-comparison HTML | per relevant Block | manual or scripted | $0 |
| Sync `chat.ipynb` companion `chat.md` (markdown render of cells) | per Block 0/E+F/F | jupytext or manual | $0 |
| Sync ship zip to OneDrive (per project rule) | end of every Block, after rezip | manual copy | $0 |

**Block K codifies this ritual; it's not a separate test or a separate Block â€” it runs at every Block close.**

The builder MUST NOT advance to next Block until ALL ritual items pass for current Block.

---

## Total cost summary

| Source | Tests | AWS cost |
|---|---|---|
| All T1 unit tests | ~150 | $0 |
| All T2 integration tests | ~100 | $0 |
| All T3 notebook smoke | ~21 | $0 |
| All T4 zip extract+import | ~21 | $0 |
| **T5 real-Bedrock single round-trips** (env-gated, only on 6 high-risk Blocks + Block J) | **~10 round-trips** | **~$0.10-0.15** |
| **R-tier high-value end-to-end real-AWS scenarios** (R1-R12, run after Block K, before tag) | 12 scenarios | **~$3-7** (caps total $7) |
| Total Phase 2 build validation (incl. R-tier) | ~312 tests | **~$3.10-7.15** |
| Your first 5 real coding sessions (Haiku-4.5, `session_cost_limit=$1`) | n/a | **~$1-3** |
| **GRAND TOTAL through real-world validation** | | **~$4-10** |

---

## How to run

### During each Block (mock-only, $0)
```bash
cd compact_v5/MAIN/agent
pytest tests/                                    # T1 + T2
papermill chat.ipynb out.ipynb                   # T3
cd .. && python verify_ship_zip.py               # T4
```

### High-risk Blocks (B, A, G3, G2, H+, N) end-of-Block
```bash
RUN_REAL_BEDROCK=1 AWS_REGION=ap-southeast-2 \
  pytest tests/integration/test_real_bedrock_smoke.py::test_<block>_real_haiku
# Expected cost per Block: $0.005-0.05
```

### Block J ship gate
```bash
cd compact_v5
python _rebuild_zip.py                           # build zip
python verify_ship_zip.py                        # extract + import gate

RUN_REAL_BEDROCK=1 AWS_REGION=ap-southeast-2 \
  pytest tests/integration/test_real_bedrock_smoke.py
# Expected cost: $0.02
```

### Your acceptance test (post-tag, in SageMaker)
1. Open `chat.ipynb` in SageMaker JupyterLab
2. Cell 2: set `iteration_budget_slider=200`, `session_cost_limit=$1.00`, model=Haiku-4.5
3. Cell 3: launch chat
4. Send: "list the files in /home/sagemaker-user/, then read the README if present, then summarize"
5. Verify: list_dir + read_file + assistant text response, total cost <$0.05
6. Try `/cost`, `/status`, `/save mytest`, `/load mytest` â€” all work
7. **If green**: v5.0.1 acceptance gate PASS

---

## Pass/fail rule (non-negotiable)

A Block tag is FORBIDDEN if ANY:
- T1/T2/T3/T4 test red
- T5 (when applicable) red
- Codex AXIS A/B/C verdict â‰  APPROVE
- You haven't approved the diff

After tag: STATE/RESUME anchor updated, PORT_LOG row materialized, V5_BUILD_STATUS bumped, next Block starts.

**Total estimated build time** (with you reviewing each Block): 2-4 weeks of focused work. **Total estimated cost**: under $5 in AWS. **Confidence after Block J + first 5 real sessions**: ~99%.


 succeeded in 1277ms:
"""v4-compatibility shim â€” `sagemaker_agent` re-exports v5's public surface.

Block 0 of v5.0.1. Constraint #2 (`v4 chat.ipynb = canonical UI`) requires
that v4's notebook line `from sagemaker_agent import CONFIG, BEDROCK_MODELS,
create_chat_ui` continues to work unchanged on v5. The notebook does not
need to know that v5 reorganized internals into `runtime/`, `agent/`, `ui/`,
etc.; it only needs the public symbols at the historic import path.

This module is intentionally tiny â€” the implementations live in their
proper v5 modules; here we only re-bind names. The shim's only job is the
import-path invariant.

The full v5 public surface is owned by `entry`. We mirror it here so that
either import works:

    from sagemaker_agent import CONFIG, BEDROCK_MODELS, create_chat_ui  # v4 path
    from entry import CONFIG, BEDROCK_MODELS, create_chat_ui            # v5 path

PORT_LOG: see #038 (Block 0 shim).
"""
from __future__ import annotations

from entry import (  # noqa: F401
    Agent,
    BEDROCK_MODELS,
    CONFIG,
    IterationBudget,
    SkillManager,
    create_chat_ui,
)

__all__ = [
    "Agent",
    "BEDROCK_MODELS",
    "CONFIG",
    "IterationBudget",
    "SkillManager",
    "create_chat_ui",
]


 succeeded in 1280ms:
# Wave 5-DEEP SYNTHESIS MASTER

**Date**: 2026-05-01
**Inputs**: 20 deep-scan reports (R1-R12 Runnable, H1-H5 Hermes, L1-L2 Learning Factory, V1 v4 inventory verify)
**Baseline**: `V5_PHASE_2_PLAN_v3.md` (post-no-deferrals v4 corrections, 18 Blocks, ~11,330 LOC pre-Wave-5-DEEP)
**Hard constraints (recap)**: single-user SageMaker, Bedrock-only, v4 chat.ipynb canonical UI, no streaming, no MCP, NO DEFERRALS, COMBINE-and-do-better.

---

## 1. Verdict

**APPROVE-WITH-MAJOR-EXPANSION**. Plan v4 is structurally sound but materially undersized vs the actual depth of the four reference repos. Wave-5-DEEP surfaces **~150 net-new findings** across 20 reports. After applying the no-deferrals rule, post-Wave-5-DEEP scope grows from ~11,330 LOC to **~19,300 LOC** across **21 Blocks** counting E+F as 1 combined block (adds Block G3 Coordinator-Prompt + Block F2 Auto-Continuation + Block H+ Auto-Dream as three new sub-blocks; renames the implicit "v4-baseline-already-there" rows into explicit PORT_LOG rows; folds all Hermes/Runnable/LF deltas into existing Blocks). Per-Block NEW deltas in Â§3 sum to ~7,943 LOC NEW; corrected from initial estimate of ~16,200 LOC per Codex AXIS A 2026-05-01.

**5 NOT-OPTIONAL correctness fixes** must land in v5.0.1 before any Block ships:
1. R4 #2 `parseMaxTokensContextOverflowError` (Block L)
2. R4 #9 `extractNestedErrorMessage` Bedrock 5xx HTML (Block L)
3. R4 #14 `isExcludedModel` Haiku cache-break suppression (Block L)
4. R4 #41 `countTokensWithBedrock` (Block B)
5. R4 #56 `adjustIndexToPreserveAPIInvariants` SM-compact (Block H)

Plus 3 high-confidence Hermes fixes:
6. H2 F7 stub-injection for missing tool_results (Block A post-compact)
7. H5 A28 prompt-cache invariant policy (Block A + Block 0)
8. R7 N8 token-accounting input-cumulative-vs-output-per-turn (Block B)

---

## 2. Consolidated mapping table (sorted by Block)

Every NEW finding (excludes ALREADY-IN-PLAN and OUT-OF-SCOPE rows). Per row: `# | Block | Capability | Repo | file:line | LOC | Priority | Architectural fit | Graft strategy`.

### Block 0 (bootstrap / shim / system prompt)

> **Build-time remap** (added 2026-05-02 per ADR-020): only item 0-1 (shim) lands inside Block 0. Items 0-2 through 0-10 keep their PORT_LOG origin here but are *implemented* in the Block that owns the touched module. Per-item landing Block + lock test in `_status/V5_DESIGN_DECISIONS.md` Â§ADR-020 â†’ "Notes / known scope remaps". Constraint #3 (no deferrals) is honored by an explicit per-item landing Block + test gate, not by silent push-out.

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| 0-1 | SYSTEM_PROMPT verbatim re-export (V1 gap #6) | v4 | sagemaker_agent.py:8029-8189 | 0 (ref) | MUST | CLEAN | Add doc-only PORT_LOG row + ensure shim re-exports. v5 already has `prompt/*.md` (Phase 6) which covers this; FALSE-POSITIVE-AT-CODE-LEVEL but DOC-GAP â€” add row to plan. |
| 0-2 | `getSessionStartDate()` memoized + `getLocalMonthYear()` (R8 #67) | Runnable | constants/common.ts:1-34 | 15 | HIGH | CLEAN | Tool prompts mentioning today's date must use month-year not ISO date or cache busts at midnight. |
| 0-3 | `BEDROCK_EXTRA_PARAMS_HEADERS` Set (R8 #74) | Runnable | constants/betas.ts:38-43 | 5 | MUST | CLEAN | Load-bearing Bedrock invariant â€” interleaved-thinking + 1m-context betas go in extraBodyParams not headers. |
| 0-4 | env block format (Windows-shell hint, OS version, Notes appendix) (R8 #76, #79) | Runnable | constants/prompts.ts:606-770 | 30 | HIGH | NEEDS-ADAPTATION | Adopt phrasings ("Agent threads always have their cwd reset", "no colon before tool calls"); v5 already has `prompt/*.md` so this is patches. |
| 0-5 | `getScratchpadInstructions()` per-session scratchpad dir (R8 #77) | Runnable | constants/prompts.ts:797-819 | 30 | MED | CLEAN | Pre-allowlist `/tmp/sagemaker_session_<id>/`, GC at session end. |
| 0-6 | `getKnowledgeCutoff(modelId)` Sonnet 4.6/Haiku 4.5 cutoffs (R8 #39) | Runnable | constants/prompts.ts:712-730 | 5 | MED | CLEAN | Inject "Assistant knowledge cutoff is X" into env block. |
| 0-7 | `cleanupRegistry` graceful-shutdown for SIGINT (R8 #18) | Runnable | utils/cleanupRegistry.ts:1-26 | 15 | HIGH | CLEAN | Python `atexit`+explicit registry; addresses session-cost flush + scratchpad cleanup. |
| 0-8 | `validateBoundedIntEnvVar` env-validation helper (R8 #32) | Runnable | utils/envValidation.ts:1-39 | 30 | MED | CLEAN | Single helper sanitizes all numeric env knobs. |
| 0-9 | Feature-flag fail-closed at import boundary (R11 N23) | Runnable | entry.ts:1-17 | 30 | MED | NEEDS-ADAPTATION | `runtime/feature_flags.py` returns False for banned modules so they fail at import. |
| 0-10 | `_scan_for_prompt_injection` + `_INJECTION_PATTERNS` v4 baseline (V1 gap #5) | v4 | sagemaker_agent.py:7509-7541 | 40 | MUST | CLEAN-FIT | Plan v3 line 343 incorrectly defers as Hermes-adoption follow-up; this is v4-native, not Hermes. Port verbatim. |

**Block 0 total NEW: ~200 LOC + 1 doc row.**

### Block B (TokenTracker + AuditLogger + SnapshotManager + tokens)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| B-1 | `countTokensWithBedrock` via boto3 CountTokensCommand (R4 #41) | Runnable | services/tokenEstimation.ts:437-495 | 60 | **MUST** | CLEAN | Without it v5 has no real Bedrock token count. |
| B-2 | `countTokensViaHaikuFallback` (R4 #42) | Runnable | tokenEstimation.ts:251-325 | 80 | HIGH | CLEAN (Bedrock-applicable subset; drop tool-search-strip) | When Bedrock CountTokens unavailable. |
| B-3 | `bytesPerTokenForFileType` JSON=2 byte/tok (R4 #40) | Runnable | tokenEstimation.ts:215-242 | 15 | HIGH | CLEAN | Fixes oversized-JSON underestimate. |
| B-4 | `roughTokenCountEstimationForBlock` per-type accuracy (R4 #44) | Runnable | tokenEstimation.ts:391-435 | 50 | HIGH | CLEAN | Per-block-type token math. |
| B-5 | `IMAGE_MAX_TOKEN_SIZE = 2000` constant (R4 #38) | Runnable | microCompact.ts:38 | 1 | MED | CLEAN | Bedrock images = 2000 tok per Anthropic billing. |
| B-6 | `estimateMessageTokens` 4/3 padding (R4 #39) | Runnable | microCompact.ts:164-205 | 30 | MED | CLEAN | Replaces v5 rough estimator. |
| B-7 | `hasThinkingBlocks` + thinking-budget constants (R4 #43) | Runnable | tokenEstimation.ts:38-56 | 25 | MED | CLEAN | For token-count requests. |
| B-8 | `tokenCountWithEstimation` walks back to last usage record (R8 #15) | Runnable | utils/tokens.ts:226-261 | 30 | MUST | CLEAN | Fixes parallel-tool-call undercount. |
| B-9 | `finalContextTokensFromLastResponse` (R8 #16) | Runnable | utils/tokens.ts:79-112 | 20 | HIGH | NEEDS-ADAPTATION | Bedrock returns top-level `usage` only; use fallback formula. |
| B-10 | `MODEL_COSTS` 2-row Bedrock table (Haiku 4.5 + Sonnet 4.6) + formatModelPricing (R8 #34, #68) | Runnable | utils/modelCost.ts:1-232 | 50 | HIGH | NEEDS-ADAPTATION | Drop fast-mode tier; keep cache-aware pricing math from v4. |
| B-11 | Token-accounting input-cumulative-vs-output-per-turn (R7 N8) | Runnable | tasks/LocalAgentTask.tsx:50-95 | 20 | **MUST** | CLEAN | Without it, parent multi-turn double-counts input. |
| B-12 | `BedrockClient` class explicit PORT_LOG row (V1 gap #7) | v4 | sagemaker_agent.py:2378-2565 | 0 (already in v5 Phase 1) | MUST | FALSE-POSITIVE-ALREADY-IN-V5 | Doc-only row in PORT_LOG to remove implicit-baseline ambiguity. |
| B-13 | `ToolResult` dataclass (V1 gap #1) | v4 | sagemaker_agent.py:867-886 | 25 | MUST | CLEAN | Wave 2 explicitly flagged MISSING. Truncated/total_size/shown_size metadata. |
| B-14 | `Truncation` class explicit PORT_LOG row (V1 lesser #11) | v4 | sagemaker_agent.py:756-861 | 0 (already in v5) | LOW | FALSE-POSITIVE | Doc-only. |
| B-15 | `ContextManager` class explicit PORT_LOG row (V1 lesser #10) | v4 | sagemaker_agent.py:3464-3528 | 0 (already in v5) | LOW | FALSE-POSITIVE | Doc-only. |
| B-16 | Lorem-ipsum 1-token-word context-window test util (R9 #22) | Runnable | skills/bundled/loremIpsum.ts | 50 | MED | CLEAN | Test utility for cache/context. |

**Block B total NEW: ~456 LOC + 4 doc rows.**

### Block B+ (SessionManager + cost-limit + AGENT_STATUS + FileCache)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| B+1 | Persist session cost + restore on resume (R11 N8, R7 CT-02..04) | Runnable | cost-tracker.ts:87-175 | 90 | HIGH | CLEAN | Write `last_session_cost.json`, rehydrate on `/resume`. |
| B+2 | Canonical-name collapse for per-model usage (R11 N9) | Runnable | cost-tracker.ts:181-226 | 40 | MED | CLEAN | Bedrock `apac.` and `us.` prefixes â†’ one row. |
| B+3 | 4-line cost block format (R11 N10) | Runnable | cost-tracker.ts:228-244 | 15 | MED | CLEAN | Replaces v4 single-line `/cost`. |
| B+4 | Local OTel-style counters (cost/token by type) (R11 N11) | Runnable | cost-tracker.ts:289-301 | 25 | MED | NEEDS-ADAPTATION | Local file/SQLite only â€” never external endpoint. |
| B+5 | Recursive advisor sub-cost accounting (R11 N12) | Runnable | cost-tracker.ts:304-322 | 30 | HIGH | CLEAN | v4.9.4 aux model unmeasured. |
| B+6 | contextWindow refresh on every cost update (R11 N13) | Runnable | cost-tracker.ts:273-274 | 5 | LOW | CLEAN | Per-update refresh. |
| B+7 | Exit-time atexit cost flush (R11 N14) | Runnable | costHook.ts:6-22 | 20 | HIGH | CLEAN | Wraps in atexit + signal handlers. |
| B+8 | `Config` dataclass explicit PORT_LOG row (V1 lesser #9) | v4 | sagemaker_agent.py:1018-1149 | 0 | MUST | FALSE-POSITIVE | Single row prevents silent field drop. |

**Block B+ total NEW: ~225 LOC + 1 doc row.**

### Block C (Runtime safety gates)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| C-1 | SecurityManager class explicit PORT_LOG row (V1 gap #8) | v4 | sagemaker_agent.py:1298-2106 | 0 (already in v5 Phase 5) | MUST | FALSE-POSITIVE-DOC-GAP | 808 LOC, biggest non-Compactor class â€” needs explicit row. |
| C-2 | secretScanner.ts 25 NEW gitleaks patterns + redactSecrets() (R5 A1) | Runnable | services/teamMemorySync/secretScanner.ts | 80 | HIGH | CLEAN | Combines with v4 13 patterns â†’ 38 patterns + redaction helper. |
| C-3 | `findActualString` quote-normalized match (R1 #115) | Runnable | FileEditTool/utils.ts:73-93 | 20 | HIGH | CLEAN | Curlyâ†’straight quote normalization. |
| C-4 | `preserveQuoteStyle` (R1 #116) | Runnable | FileEditTool/utils.ts:104-120 | 15 | MED | CLEAN | If file uses curly, re-wrap new_string. |
| C-5 | UTF-16 LE BOM detection on edit (R1 #121) | Runnable | FileEditTool.ts:208-214 | 15 | HIGH | CLEAN | Notepad-saved files. |
| C-6 | UNC path skip on Windows (NTLM credential leak) (R1 #123) | Runnable | FileEditTool.ts:179-181 | 5 | HIGH | CLEAN | Defensive Windows. |
| C-7 | `\r\n`â†’`\n` normalization preserving original on write (R1 #122) | Runnable | FileEditTool utils | 20 | HIGH | CLEAN | Round-trip line endings. |
| C-8 | Staleness check Windows content-fallback for OneDrive/AV mtime bumps (R1 #111) | Runnable | FileEditTool.ts:289-311 | 15 | HIGH | CLEAN | Real Windows fix. |
| C-9 | `interpretCommandResult` exit-code semantics (R1 #49) | Runnable | BashTool/commandSemantics.ts:1-140 | 15 | HIGH | CLEAN | grep 1=no-match, find 1=partial, diff 1=differs. |
| C-10 | `getDestructiveCommandWarning` pattern catalog (R1 #50) | Runnable | BashTool/destructiveCommandWarning.ts | 30 | MED | CLEAN | rm -rf, git push --force, DROP TABLE, kubectl delete, terraform destroy. |
| C-11 | Cd+git compound bare-repo fsmonitor guard (R1 #53) | Runnable | BashTool/bashCommandHelpers.ts:50-82 | 40 | HIGH | CLEAN | Security bug class. |
| C-12 | Multiple-cd detection (R1 #54) | Runnable | BashTool/bashCommandHelpers.ts:32-47 | 10 | MED | CLEAN | `cd a && cd b && X` requires approval. |
| C-13 | Pipe-segment per-segment permission check (R1 #55) | Runnable | BashTool/bashCommandHelpers.ts:84-156 | 30 | MED | CLEAN | `cmd1 | cmd2` evaluated piecewise. |
| C-14 | `extractBashCommentLabel` first-line `# comment` UI label (R1 #48) | Runnable | BashTool/commentLabel.ts | 15 | LOW | CLEAN | UI history label. |
| C-15 | `BINARY_EXTENSIONS` set + `isBinaryContent` 8KB null-byte sniff (R8 #28) | Runnable | constants/files.ts:1-156 | 50 | HIGH | CLEAN | Prevents binary file context waste. |
| C-16 | `escapeXml` / `escapeXmlAttr` (R8 #26) | Runnable | utils/xml.ts:1-17 | 10 | HIGH | CLEAN | Memory/CLAUDE.md may contain `<` or `&`. |
| C-17 | `combinedAbortSignal` + `AsyncLocalStorage` cwd (R8 #19, #20) | Runnable | utils/combinedAbortSignal.ts + cwd.ts | 50 | HIGH | NEEDS-ADAPTATION | Python `contextvars.ContextVar('cwd')` + `asyncio.Event`. v4 can't cancel long bash. |
| C-18 | Multi-pass JSON repair `_repair_tool_call_arguments` (H1 #17) | Hermes | run_agent.py:547-641 | 95 | **HIGH-MUST** | CLEAN | Bedrock Claude (esp. Haiku) emits malformed args; `{}` fallback better than crash. (Resolves R5 prior OUT-OF-SCOPE â€” see Â§7.) |
| C-19 | `_escape_invalid_chars_in_json_strings` (H1 #16) | Hermes | run_agent.py:505-544 | 40 | MED | CLEAN | Pairs with #C-18. |

**Block C total NEW: ~555 LOC + 1 doc row.**

### Block C+ (Approval/diff dispatch + stop/abort + rate limits)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| C+1 | `EnterPlanMode` + `ExitPlanModeV2` (R1 #84-91, #97-104) | Runnable | EnterPlanModeTool/ExitPlanModeV2Tool | 200 | MED | NEEDS-ADAPTATION | OPTIONAL â€” formalizes v4's PLAN_MODE_ALLOWED_TOOLS into a dedicated mode. Drop teammate routing + auto-mode classifier. **DECISION: KEEP-LIGHT (~80 LOC)** for plan-mode toggle without ExitPlanMode tool ceremony, OR **DROP** since v4's `/phase` is the lighter-weight equivalent. **Verdict: DROP (KEEP `/phase`)** to avoid scope creep. See Â§9. |
| C+2 | File-history snapshot per-edit (R1 #127) | Runnable | FileEditTool.ts:431-440 | 40 | MED | CLEAN | Pre-edit content backup â†’ enables `/rollback` (Block D extension). |
| C+3 | Cancellation/abort signal pattern via Python (paired with C-17) | Runnable | utils/abortController.ts | (in C-17) | HIGH | already covered | â€” |

**Block C+ total NEW: ~40 LOC (after dropping Plan Mode).**

### Block D (Slash commands + custom expander)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| D-1 | Lazy-load heavy command (R11 N1) | Runnable | commands.ts:188-202 | 20 | MED | CLEAN | Python `importlib` on demand. |
| D-2 | Parallel skill scan via Promise.all (R11 N2) | Runnable | commands.ts:449-469 | 25 | LOW | CLEAN | v5 skill discovery currently sequential. |
| D-3 | Dynamic-skill merge dedupe (R11 N3) | Runnable | commands.ts:476-517 | 30 | MED | CLEAN | Self-patching skills support. |
| D-4 | Named cache invalidation (4 caches) (R11 N4) | Runnable | commands.ts:523-532 | 20 | MED | CLEAN | Better than "clear all". |
| D-5 | Listing-budget filter (bundled/user/project/dynamic) (R11 N5) | Runnable | commands.ts:563-608 | 40 | MED | CLEAN | Token budget for skill listing. |
| D-6 | Command alias + helpful-error-on-miss (R11 N6) | Runnable | commands.ts:688-719 | 30 | MED | CLEAN | `/qâ†’/quit`, full list on miss. |
| D-7 | Source annotation `(bundled)/(user)/(project)` (R11 N7) | Runnable | commands.ts:728-754 | 25 | LOW | CLEAN | UX polish. |
| D-8 | `/init` CLAUDE.md scaffold prompt (R6 NEW #1) | Runnable | commands/init.ts:1-256 | 50 | MED | CLEAN | Pure-prompt skill. Folds into Block I as `skills/init/`. |
| D-9 | `/init-verifiers` Verify-skill scaffolder (R6 NEW #2) | Runnable | commands/init-verifiers.ts:1-262 | 100 | MED | CLEAN | Folds into Block I as `skills/init-verifiers/`. |
| D-10 | `/skillify` capture session-as-skill (R9 #17) | Runnable | skills/bundled/skillify.ts:22-156 | 80 | MED | CLEAN | New `skills/skillify/` + Block D dispatcher entry. |
| D-11 | `/dream` manual consolidation trigger (R12 R12-2) | Runnable | autoDream/consolidationLock.ts:130-140 | 30 | HIGH | CLEAN | Pairs with auto-dream (Block H+). |
| D-12 | `parseSlashCommand` MCP-namespace parser (R8 #44) | Runnable | utils/slashCommandParsing.ts:1-60 | 20 | LOW | CLEAN | Future-proofs `(MCP)`-suffix detection even if MCP dropped. |
| D-13 | `substituteArguments` indexed `$ARGUMENTS[0]` + `$0` shorthand + named (R8 #45) | Runnable | utils/argumentSubstitution.ts:1-145 | 80 | HIGH | CLEAN | v4 supports `$ARGUMENTS` only. |

**Block D total NEW: ~550 LOC.**

### Block A (Compactor + cold-cache + auto-compact + cache invariants)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| A-1 | `getEffectiveContextWindowSize` + `MAX_OUTPUT_TOKENS_FOR_SUMMARY=20K` (R4 #16) | Runnable | autoCompact.ts:33-49 | 40 | HIGH | CLEAN | Per-model + summary reserve. |
| A-2 | Named token budgets (`AUTOCOMPACT_BUFFER=13K, WARN/ERR=20K, MANUAL=3K`) (R4 #17) | Runnable | autoCompact.ts:62-65 | 10 | MED | CLEAN | Constants. |
| A-3 | `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES=3` `AutoCompactTrackingState` (R4 #18) | Runnable | autoCompact.ts:51-265 | 30 | HIGH | CLEAN | Replaces global `_auto_compact_paused`. |
| A-4 | `calculateTokenWarningState` 5 flags (R4 #19) | Runnable | autoCompact.ts:93-145 | 50 | HIGH | CLEAN | Used by Block E+F status bar. |
| A-5 | `shouldAutoCompact` recursion guards (R4 #20) | Runnable | autoCompact.ts:170-183 | 20 | HIGH | CLEAN | Bail when querySource âˆˆ {session_memory, compact}. |
| A-6 | `stripImagesFromMessages` for compact-summary (R4 #21) | Runnable | compact.ts:145-200 | 50 | HIGH | CLEAN | Bedrock often rejects on PTL with images. |
| A-7 | `stripReinjectedAttachments` (R4 #22) | Runnable | compact.ts:211-223 | 10 | MED | CLEAN | Skill_discovery/skill_listing waste. |
| A-8 | `MAX_PTL_RETRIES=3` + `truncateHeadForPTLRetry` (R4 #23) | Runnable | compact.ts:227-491 | 70 | HIGH | CLEAN | Recovers compact-itself-too-long. |
| A-9 | `groupMessagesByApiRound` (R4 #24) | Runnable | compact/grouping.ts:22-63 | 30 | HIGH | CLEAN | Required by A-8. |
| A-10 | Post-compact constants (FILE/SKILL token budgets) (R4 #25) | Runnable | compact.ts:122-130 | 10 | MED | CLEAN | Constants. |
| A-11 | `createPostCompactFileAttachments` (R4 #26) | Runnable | compact.ts:1415-1655 | 80 | HIGH | CLEAN | Re-reads recently-touched files. |
| A-12 | `createSkillAttachmentIfNeeded` (R4 #27) | Runnable | compact.ts:1494-1534 | 70 | HIGH | CLEAN | Re-injects active skills (PER USER REQUEST). |
| A-13 | `compactConversation` cache-sharing-fork + streaming-fallback (R4 #33) | Runnable | compact.ts:1136-1392 | 150 | HIGH | NEEDS-ADAPTATION | Pairs with G2 forkSubagent. |
| A-14 | POST_COMPACT exclusion list for memory-files (R4 #34) | Runnable | compact.ts:1674-1705 | 30 | HIGH | CLEAN | Exclude CLAUDE.md/MEMORY.md from re-inject. |
| A-15 | `compactWarningState` suppress (R4 #35) | Runnable | compact/compactWarningState.ts | 10 | MED | CLEAN | Suppresses post-compact bogus warning. |
| A-16 | Time-based microcompact (60-min idle clear) (R4 #36) | Runnable | microCompact.ts:411-530 | 80 | HIGH | CLEAN | Replaces v5's 30-min reactive trigger. |
| A-17 | `COMPACTABLE_TOOLS` allowlist (R4 #37) | Runnable | microCompact.ts:41-50 | 10 | HIGH | CLEAN | Excludes create_word/excel/etc from clearing. |
| A-18 | `sessionActivity` keep-alive during compact (R4 #66) | Runnable | compact.ts:1167-1395 | 20 | HIGH | CLEAN | SageMaker kernel idle-timeout protection. |
| A-19 | Compact querySource recursion guards (R4 #67) | Runnable | compact.ts:1125-1134 | 15 | HIGH | CLEAN | Compact agent can't re-fire tools. |
| A-20 | Abortable sleep across retry backoffs (R4 #69) | Runnable | compact.ts:1369-1371 | 10 | MED | CLEAN | ESC during retry. |
| A-21 | `runPostCompactCleanup` cache invalidation (R4 #71) | Runnable | postCompactCleanup.ts:1-77 | 40 | HIGH | CLEAN | _FILES_READ + skill-listing-cache + memory-cache. |
| A-22 | `buildPostCompactMessages` ordering invariant (R4 #75) | Runnable | compact.ts:330-338 | 15 | MED | CLEAN | Locks ordering contract. |
| A-23 | `hasExactErrorMessage` + skip-error-on-user-abort (R4 #79) | Runnable | compact.ts:1108-1123 | 15 | LOW | CLEAN | UX polish â€” ESC during compact. |
| A-24 | `_is_stale_round_trip` confirm port (V1 lesser) | v4 | sagemaker_agent.py:3919-3975 | 0 (verify) | MUST | FALSE-POSITIVE | Used by `context_collapse`; explicit confirmation. |
| A-25 | Stub-injection for missing tool_results post-compact (H2 F7) | Hermes | run_agent.py:4585-4604 | 25 | **MUST** | CLEAN | Without it, Bedrock 400-errors after compact. |
| A-26 | Surrogate sanitization recursive walker (H1 #14, #15) | Hermes | run_agent.py:384-502 | 115 | HIGH | CLEAN | `_sanitize_messages_surrogates` before every Bedrock converse. |
| A-27 | `flush_memories` pre-compression turn (H4 F2) | Hermes | run_agent.py:7913-8157 | 80 | HIGH | NEEDS-ADAPTATION | One-turn memory-only call before compact. |
| A-28 | `_compress_context` post-compaction details (todo re-inject, file-dedup reset, token refresh) (H4 F3) | Hermes | run_agent.py:8158-8272 | 50 | HIGH | CLEAN | Adopt items 1, 3, 5; skip session-split (SQLite-specific). |
| A-29 | Tool-schema tokens in pre-compression estimate (H4 F8 / R7 GAP-7) | Hermes | run_agent.py:9507-9513 | 20 | HIGH | CLEAN | "20-30K+ tokens v4 estimate misses". |
| A-30 | Post-compression retry-counter reset (H4 F8) | Hermes | run_agent.py:9544 | 10 | HIGH | CLEAN | Prevents "(empty)" right after compaction. |
| A-31 | `apply_anthropic_cache_control` Bedrock cache application (H4 F12) | Hermes | run_agent.py:9851-9856 | 30 | HIGH | CLEAN | Confirm Block A applies cache_control at system + last-3 messages. |
| A-32 | Prefix-stable normalization (sorted JSON keys + content strip) (H4 F13) | Hermes | run_agent.py:9870-9895 | 25 | HIGH | CLEAN | Free 5-15% cache-hit boost. |
| A-33 | A28 prompt-cache invariant policy (H5 A28) | Hermes | AGENTS.md:Policy | 0 (policy/audit) | **MUST** | NEEDS-ADAPTATION | NEVER rebuild system prompt mid-conv; toolset changes deferred to next session via `--now` opt-in. v4 violates this â€” v5.0.1 must enforce. |
| A-34 | `transition.reason` enum + skip-stop-hooks-on-API-error (R7 N3) | Runnable | query.ts:1062-1183 | 30 | HIGH | CLEAN | Anti-spiral guard. |
| A-35 | Block-on-context-limit pre-API guard (R7 N11) | Runnable | query.ts:615-648 | 40 | MED | CLEAN | Pre-emptive 413 prevention. |
| A-36 | error_during_execution diagnostic prefix + watermark (R7 N6) | Runnable | QueryEngine.ts:669, 1058-1117 | 30 | MED | CLEAN | Turn-scoped error filtering. |
| A-37 | `cache_ttl: "5m"|"1h"` config knob (H1 E) | Hermes | run_agent.py:1148-1157 | 6 | LOW | CLEAN | Long-session win. |
| A-38 | Compact-boundary preservedSegment GC pattern (R7 C7) | Runnable | QueryEngine.ts:701-714, 926-933 | 30 | MED | CLEAN | Long-session memory leak fix. Splice mutableMessages + flush before tail. |
| A-39 | `is_meta` field on every message (R8 #109) | Runnable | textInputTypes.ts:330-336 | 20 | HIGH | CLEAN | Hidden-from-UI but visible-to-model. |
| A-40 | `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` static/dynamic boundary (R8 #37) | Runnable | constants/systemPromptSections.ts:1-69 | 80 | **MUST** | NEEDS-ADAPTATION | THE prompt-cache stability lever; pairs with A-33. Refactor v5 prompt builder into static + dynamic. |
| A-41 | `marble-origami-commit` persist-splice metadata (R8 #106) | Runnable | types/logs.ts:255-295 | 30 | MED | CLEAN | High-craft compaction-resume pattern. |
| A-42 | `ContentReplacementEntry` (R8 #107) | Runnable | types/logs.ts:181-186 | 20 | MED | CLEAN | For large tool results persisted elsewhere. |
| A-43 | `generateTempFilePath` content-hash mode (R8 #21) | Runnable | utils/tempfile.ts:1-32 | 30 | MED | CLEAN | Cache-stable paths for tool descriptions. |

**Block A total NEW: ~1,510 LOC + 1 policy + 2 doc rows.**

### Block E + F (UI rendering + cell widgets + cost UI)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| EF-1 | Permission-denial tracking surface (R7 N5) | Runnable | QueryEngine.ts:244-271 | 30 | MED | CLEAN | "3 tool denials this turn" UI. |
| EF-2 | maxBudgetUsd hard-cap halt (R7 N7) | Runnable | QueryEngine.ts:972-1002 | 30 | **MUST** | CLEAN | v5 has cost-limit slider; needs the kill-switch. |
| EF-3 | FallbackTriggeredError model switch + stripSignatureBlocks (R7 N10) | Runnable | query.ts:893-953 | 50 | MED | NEEDS-ADAPTATION | Cross-model retry safety; thinking sigs are model-bound. |
| EF-4 | format helpers (formatFileSize/Duration/Tokens/Cost) (R8 #14) | Runnable | utils/format.ts:1-309 | 80 | HIGH | CLEAN | Centralize. |
| EF-5 | `tool_gen_callback` on first tool-arg token (H3 G4) | Hermes | run_agent.py:5857-5870, 5948-5950 | 30 | HIGH | CLEAN | Visible feedback during long write_file generation. |
| EF-6 | ~~Stream-delivery duplicate-suppression~~ DROPPED 2026-05-01 per constraint #10 (no streaming) | Hermes | run_agent.py:5783-5826 | 0 | DROP | DROP | v5 uses non-streaming Bedrock invoke; no converse_stream/final-response overlap to fix. |
| EF-7 | ~~`_fire_stream_delta` paragraph-break logic~~ DROPPED 2026-05-01 per constraint #10 | Hermes | run_agent.py:5828-5846 | 0 | DROP | DROP | Display problem only exists in streaming path. |
| EF-8 | `_emit_status` / `_emit_warning` event channel (H1 G) | Hermes | run_agent.py:2295-2341 | 30 | LOW | CLEAN | Status callback channel for ipynb progress. |

**Block E+F total NEW: ~305 LOC.**

### Block I (Skill name resolution + skill discovery)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| I-1 | Conditional skills via `paths:` frontmatter (R9 #1) | Runnable | skills/loadSkillsDir.ts:159-178 | 50 | HIGH | CLEAN | Auto-activate skill on touched-paths; fnmatch-based. |
| I-2 | `disable_model_invocation` flag (R9 #3) | Runnable | bundledSkills.ts:84 | 10 | MED | CLEAN | User-only invocable, model can't trigger. |
| I-3 | `enabled_when` skill predicate (R9 #4) | Runnable | bundled/remember.ts:71 | 10 | MED | CLEAN | CONFIG-flag gated skill visibility. |
| I-4 | realpath-dedup in skill load (R9 #23) | Runnable | loadSkillsDir.ts:638-810 | 5 | HIGH | CLEAN | Bug fix for symlink double-load. |
| I-5 | Skill discovery on every edit (R1 #112) | Runnable | FileEditTool.ts:404-423 | 30 | MED | CLEAN | Path-triggered skill activation. |
| I-6 | `${CLAUDE_SKILL_DIR}` + `${CLAUDE_SESSION_ID}` substitution (R9 #26) | Runnable | loadSkillsDir.ts:344-396 | 10 | LOW | CLEAN | Skip bash-injection; security risk. |
| I-7 | `skills/init/` (CLAUDE.md scaffolder) â€” folds D-8 here | Runnable | commands/init.ts | (in D-8) | MED | CLEAN | â€” |
| I-8 | `skills/init-verifiers/` â€” folds D-9 here | Runnable | commands/init-verifiers.ts | (in D-9) | MED | CLEAN | â€” |
| I-9 | `skills/skillify/` â€” folds D-10 here | Runnable | bundled/skillify.ts | (in D-10) | MED | CLEAN | â€” |
| I-10 | `skills/debug/` (R9 #20) | Runnable | bundled/debug.ts:1-103 | 20 | LOW | CLEAN | Tail audit_logs, ERROR/WARN summary. |
| I-11 | `skills/remember/` 4-step review (R9 #18) | Runnable | bundled/remember.ts:9-62 | 50 | LOW | CLEAN | CLAUDE.md/CLAUDE.local.md only. |
| I-12 | Frontmatter parser improvements (auto-quote, brace-expand, coerce desc) (R8 #24, #50) | Runnable | utils/frontmatterParser.ts:1-371 | 150 | HIGH | CLEAN | Real failure modes. |
| I-13 | `tool_skill` + `tool_skill_propose_patch` registry rows (R2 finding 2) | v4 | sagemaker_agent.py:6674, 6703 | 0 (already wired Block D) | LOW | doc-only | Confirm Block D dispatcher + add note. |

**Block I total NEW: ~335 LOC.**

### Block M (Phase 8 critical fixes â€” already in v3)

No additional changes from Wave-5-DEEP. Plan v3 Block M (30 LOC) covers per-turn discoveredSkillNames reset + countToolCalls retry-limit. R7 confirms these (C1, C2).

### Block G (AGENT_TYPES + worktree)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| G-1 | `loadAgentMemoryPrompt` per-agent-scoped memory (R1 #11) | Runnable | AgentTool/agentMemory.ts:138-177 | 50 | MED | CLEAN | Per-agent memory.md scope. |
| G-2 | `isAgentMemoryPath` path-traversal-safe (R1 #12) | Runnable | agentMemory.ts:68-104 | 30 | MED | CLEAN | Security-relevant. |
| G-3 | `ONE_SHOT_BUILTIN_AGENT_TYPES` (R1 #19) | Runnable | AgentTool/constants.ts:9-12 | 10 | LOW | CLEAN | Skip trailer for explore/plan/verify (token saver). |
| G-4 | `getPrompt(isCoordinator)` slim-vs-full prompt (R1 #20) | Runnable | AgentTool/prompt.ts:202-213 | 15 | MED | CLEAN | Coordinator gets shared block. |
| G-5 | `IterationBudget` 213-254 explicit PORT_LOG row (H1 A) | Hermes | run_agent.py:213-254 | 30 | HIGH | CLEAN | Subagent budget plumbing. |
| G-6 | DEFAULT_AGENT_PROMPT verbatim phrasing (R8 #78) | Runnable | constants/prompts.ts:758 | 5 | HIGH | CLEAN | Battle-tested "don't gold-plate" wording. |
| G-7 | "Notes" appendix to subagent system prompt (R8 #79) | Runnable | constants/prompts.ts:766-770 | 15 | HIGH | CLEAN | Each line fixes a real failure mode. |
| G-8 | `forkSubagent` cache-prefix replay (already Block G2 in plan) | Runnable | forkSubagent.ts:73-end | 100 | HIGH | already in plan | â€” |

**Block G total NEW: ~155 LOC.**

### Block G3 (NEW BLOCK â€” Coordinator System Prompt) **CRITICAL**

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| G3-1 | Coordinator 258-LOC system prompt (R7 N1) | Runnable | coordinator/coordinatorMode.ts:111-369 | 270 | **HIGH-MUST** | NEEDS-ADAPTATION | Codifies user's #1 collaboration rule: 4 phases, never delegate understanding, continue-vs-spawn matrix, parallel-research/serial-write rules. Substitute Runnable tool names (AgentToolâ†’spawn_agent, etc.). Gated by `CONFIG.coordinator_mode_enabled` (default False). |
| G3-2 | `getCoordinatorUserContext` worker-tools + scratchpad (R12 R12-3) | Runnable | coordinatorMode.ts:80-109 | 30 | HIGH | CLEAN | Pairs with G3-1. |

**Block G3 total NEW: ~300 LOC. NEW BLOCK.**

### Block H (Memory extraction)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| H-1 | `hasMemoryWritesSince` race guard (R4 #45) | Runnable | extractMemories.ts:113-148 | 30 | HIGH | CLEAN | Mutual-exclusion main + forked memory writer. |
| H-2 | `countModelVisibleMessagesSince` cursor fallback (R4 #46) | Runnable | extractMemories.ts:82-110 | 25 | HIGH | CLEAN | Critical: without it extraction permanently disabled mid-session. |
| H-3 | In-flight extraction tracking + drainPendingExtraction (R4 #47) | Runnable | extractMemories.ts:303-587 | 30 | HIGH | CLEAN | Pre-shutdown drain. |
| H-4 | turnsSinceLastExtraction throttle (R4 #48) | Runnable | extractMemories.ts:316 | 10 | MED | CLEAN | Tuning knob. |
| H-5 | `createAutoMemCanUseTool` scoped permission (R4 #49) | Runnable | extractMemories.ts:171-222 | 50 | HIGH | CLEAN | Read/Grep/Glob unrestricted; Edit/Write only memdir; Bash readonly. |
| H-6 | `scanMemoryFiles` + `formatMemoryManifest` pre-injected (R4 #50) | Runnable | extractMemories.ts:396-413 | 40 | HIGH | CLEAN | Extraction prompt includes existing-memory list. |
| H-7 | `countToolCallsSince` thresholded extraction (R4 #52) | Runnable | sessionMemory.ts:108-181 | 50 | HIGH | CLEAN | "Extract at natural break" trigger. |
| H-8 | `waitForSessionMemoryExtraction` (R4 #53) | Runnable | sessionMemoryUtils.ts:89-105 | 30 | HIGH | CLEAN | SM-compact races SM-extract; without this, broken. |
| H-9 | `hasToolCallsInLastAssistantTurn` predicate (R4 #54) | Runnable | sessionMemory.ts:158-170 | 15 | HIGH | CLEAN | Don't summarize while tool_use dangling. |
| H-10 | `createMemoryFileCanUseTool` single-file (R4 #55) | Runnable | sessionMemory.ts:460-482 | 25 | HIGH | CLEAN | Required by SM-extract isolation. |
| H-11 | `adjustIndexToPreserveAPIInvariants` (R4 #56) | Runnable | sessionMemoryCompact.ts:232-314 | 85 | **MUST** | CLEAN | CRITICAL: SM-compact startIndex landing mid-pair â†’ API 400 reject. |
| H-12 | `calculateMessagesToKeepIndex` (R4 #57) | Runnable | sessionMemoryCompact.ts:324-397 | 80 | HIGH | CLEAN | Floor at last compact-boundary. |
| H-13 | `SessionMemoryCompactConfig` file-based defaults (R4 #58) | Runnable | sessionMemoryCompact.ts:99-130 | 40 | MED | NEEDS-ADAPTATION | Replace GrowthBook read with config-file read. |
| H-14 | `hasTextBlocks` predicate (R4 #59) | Runnable | sessionMemoryCompact.ts:135-150 | 15 | MED | CLEAN | Used by H-12. |
| H-15 | `truncateSessionMemoryForCompact` (R4 #60) | Runnable | SessionMemory/prompts.ts:8-9 | 50 | HIGH | CLEAN | Caps per-section + total tokens. |
| H-16 | `isSessionMemoryEmpty` template-equality (R4 #61) | Runnable | sessionMemoryCompact.ts:540-543 | 10 | MED | CLEAN | Falls through to legacy compact when empty. |
| H-17 | `shouldUseSessionMemoryCompaction` env-override (R4 #81) | Runnable | sessionMemoryCompact.ts:403-432 | 20 | MED | CLEAN | `SAGEMAKER_SM_COMPACT_ENABLE`. |
| H-18 | `getUserContext` CLAUDE.md aggregation (R7 N12) | Runnable | context.ts:153-189 | 80 | HIGH | CLEAN | Walks parent dirs; v5 should auto-load CLAUDE.md hierarchy. |
| H-19 | `getSystemContext` git-status injection memoized + parallel + 2K truncate (R11 N15-N20) | Runnable | context.ts:36-189 | 200 | HIGH | CLEAN | Bundled: cache-breaker + git-status (`--no-optional-locks` + parallel + 2K truncate + hint) + memoization + `--bare` semantics. |
| H-20 | Onboarding step model + auto-suppress (R11 N21) | Runnable | projectOnboardingState.ts:11-83 | 60 | LOW | CLEAN | First-run UX. |

**Block H total NEW: ~945 LOC.**

### Block H+ (NEW BLOCK â€” Memory Consolidation Engine, MANUAL-TRIGGER ONLY)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| H+1 | autoDream consolidation engine â€” MANUAL-TRIGGER ONLY (user decision 2026-05-01) | Runnable | services/autoDream/* | 350 | HIGH | NEEDS-ADAPTATION | Memory consolidation engine: 4-phase prompt (Orient â†’ Gather â†’ Consolidate â†’ Prune+Index) + lock + rollback-on-fail. **NO DAEMON, NO AUTO-FIRE, NO ENV AUTO-ENABLE.** Fires ONLY when user invokes `/dream` slash command (D-11). Drop `autoDream` daemon scheduler + 3-gate auto-trigger + `SAGEMAKER_AUTO_DREAM` env var. Target: `runtime/dream.py` (NOT `auto_dream.py`). USER_GUIDE must document `/dream` usage clearly. |

**Block H+ total NEW: ~350 LOC. NEW BLOCK.**

### Block L (Error/retry/cache-break)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| L-1 | `getPromptTooLongTokenGap` parse + drop multiple groups (R4 #1) | Runnable | errors.ts:104-118 | 50 | HIGH | CLEAN | Closes compact-retry stalling PS-class bug. |
| L-2 | `parseMaxTokensContextOverflowError` (R4 #2) | Runnable | withRetry.ts:550-595 | 30 | **MUST** | CLEAN | Without it, context-overflow 400s permanently fail the turn. |
| L-3 | `getRateLimitResetDelayMs` Unix-sec parse (R4 #3) | Runnable | withRetry.ts:814-822 | 15 | HIGH | CLEAN | `anthropic-ratelimit-unified-reset` header. |
| L-4 | `is529Error` + querySource-aware retry-vs-drop (R4 #4) | Runnable | withRetry.ts:610-621, 84-89 | 40 | HIGH | CLEAN | Prevents capacity-cascade amplification. |
| L-5 | `FallbackTriggeredError` Opusâ†’Sonnet on 3x 529 (R4 #5) | Runnable | withRetry.ts:160-168 | 50 | HIGH | NEEDS-ADAPTATION | Bedrock fallback inference profile. |
| L-6 | Stale-connection + keep-alive disable on retry (R4 #6) | Runnable | withRetry.ts:112-118 | 30 | HIGH | CLEAN | Bedrock SDK uses Node-equivalent http; rebuild client. |
| L-7 | Persistent retry mode (env-gated) (R4 #7) | Runnable | withRetry.ts:96-104 | 80 | MED | NEEDS-ADAPTATION | `SAGEMAKER_UNATTENDED_RETRY=1` for SageMaker idle-disconnect. |
| L-8 | `extractConnectionErrorDetails` SSL error walk + hint (R4 #8) | Runnable | errorUtils.ts:42-100 | 80 | HIGH | CLEAN | Corp Zscaler/proxy fixes. |
| L-9 | `sanitizeAPIError` + `extractNestedErrorMessage` (R4 #9) | Runnable | errorUtils.ts:107-198 | 50 | **MUST** | CLEAN | Without it, Bedrock 5xx returns raw HTML to user. |
| L-10 | Full PromptStateSnapshot 12 fields â†’ 8 Bedrock-applicable (R4 #10, #63) | Runnable | promptCacheBreakDetection.ts:170-241 | 30 | HIGH | CLEAN | Drop 4 subscription-specific. |
| L-11 | `MAX_TRACKED_SOURCES=10` LRU eviction (R4 #11) | Runnable | promptCacheBreakDetection.ts:107 | 5 | MED | CLEAN | Trivial. |
| L-12 | `MIN_CACHE_MISS_TOKENS=2_000` (R4 #12) | Runnable | promptCacheBreakDetection.ts:120 | 5 | MED | CLEAN | Combined predicate. |
| L-13 | TTL-expiry classification (1h/5min/server-side) (R4 #13) | Runnable | promptCacheBreakDetection.ts:566-588 | 30 | HIGH | CLEAN | Turns useless break into actionable info. |
| L-14 | `isExcludedModel` Haiku exclusion (R4 #14) | Runnable | promptCacheBreakDetection.ts:128-131 | 3 | **MUST** | CLEAN | Without it, Haiku 4.5 sub-agents emit constant false breaks. |
| L-15 | `writeCacheBreakDiff` for debugging (R4 #15) | Runnable | promptCacheBreakDetection.ts:708-727 | 30 | LOW | CLEAN | Optional debug. |
| L-16 | `stripCacheControl` + `cacheControlHash` dual hash (R4 #62) | Runnable | promptCacheBreakDetection.ts:160-168 | 20 | HIGH | CLEAN | Detects TTL/scope flips. |
| L-17 | API error humanizer (Bedrock-only variant) (H2 N3) | Hermes | run_agent.py:3552-3590 | 40 | HIGH | NEEDS-ADAPTATION | Drop Cloudflare branch; keep JSON-body + status_code. |
| L-18 | Roll-back to last assistant turn helper (H2 N2) | Hermes | run_agent.py:3317-3346 | 30 | MED | CLEAN | Defensive utility. |
| L-19 | One-extra primary-recovery after max retries (H3 G18) | Hermes | run_agent.py:6988-7066 | 30 | MED | CLEAN | Bedrock can hit transient TCP. |
| L-20 | Three-tier recovery ladder pattern (H3 G19) | Hermes | run_agent.py:5528-5610 | 0 (architectural) | HIGH | NEEDS-ADAPTATION | "retry â†’ IAM token refresh â†’ user-error" architectural lesson. |
| L-21 | Daemon-thread Bedrock call for Ctrl-C responsiveness (H3 G1) | Hermes | run_agent.py:5637-5781 | 80 | HIGH | NEEDS-ADAPTATION | v4 blocking; v5 should adopt thread pattern. |
| L-22 | Stale non-stream call detector (context-scaled deadline) (H3 G2) | Hermes | run_agent.py:5704-5762 | 50 | HIGH | CLEAN | Bedrock can hang in throttling-retry. |
| L-23 | Heartbeat callback every 30s during long calls (H3 G3) | Hermes | run_agent.py:5720-5724 | 20 | HIGH | CLEAN | Keeps ipykernel alive. |
| L-24 | `_rebuild_anthropic_client` Bedrock branch (H3 G11) | Hermes | run_agent.py:5617-5635 | 20 | HIGH | CLEAN | Defensive; v5 may have latent bug. |
| L-25 | `invalidate_runtime_client(region)` on stale (H3 G12) | Hermes | run_agent.py:5685, 5938-5941 | 15 | HIGH | CLEAN | Don't reuse poisoned pool. |
| L-26 | `toError`/`shortErrorStack`/`isFsInaccessible`/`classifyAxiosError` (R8 #11, #12) | Runnable | utils/errors.ts:1-238 | 80 | HIGH | CLEAN | 5-frame stack truncation; ENOENT family. |
| L-27 | ShellError + ConfigParseError + TelemetrySafeError classes (R8 #13) | Runnable | utils/errors.ts:3-101 | 30 | MED | CLEAN | Structured errors carry stdout/stderr/code/path/default. |
| L-28 | Bedrock Guardrails config (`bedrock.guardrail.*`) (H1 D) | Hermes | run_agent.py:1287-1312 | 25 | MED | NEEDS-ADAPTATION | Insurance compliance; PII redaction. |

**Block L total NEW: ~966 LOC.**

### Block N (Hermes net-new patterns)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| N-1 | Block N row 1 expanded line ranges to full concurrent + sequential paths (H4 N1) | Hermes | run_agent.py:259-280, 311-372, 8274-9112 | 0 (clarification) | MUST | CLEAN | Plan v3 cited only `:8274-8523` + `:8581-8584`; missing 200+ LOC of correctness logic. Re-cite. |
| N-2 | Path-scoped parallelism helpers (H1 #11, #12) | Hermes | run_agent.py:355-380 | 23 | HIGH | CLEAN | Already implied; explicit cite. |
| N-3 | `_NEVER_PARALLEL_TOOLS`, `_PARALLEL_SAFE_TOOLS`, `_PATH_SCOPED_TOOLS`, `_MAX_TOOL_WORKERS=4` constants (H1 #5-8, H4 N2) | Hermes | run_agent.py:259-280 | 10 | MUST | NEEDS-ADAPTATION | Filter to v5 tool surface (no `ha_*`/`vision_analyze`). |
| N-4 | Worker tid race fix + checkpoint snapshots (H4 8463-8482, 8523-8570) | Hermes | run_agent.py:8463-8725 | 200 | HIGH | NEEDS-ADAPTATION | Required for safe parallel exec; activity-callback set is needed for long terminal commands. |
| N-5 | Sequential path bookkeeping parity (H4 Â§2.4) | Hermes | run_agent.py:8727-9112 | 150 | HIGH | CLEAN | Sequential is fallback when batch unsafe. |
| N-6 | `enforce_turn_budget` over `messages[-num_tools:]` (H4 Â§2.2) | Hermes | run_agent.py:8714-8725 | 30 | HIGH | CLEAN | Token cap on tool result aggregate. |
| N-7 | `partial_tool_names` tracking + warning-on-death (H3 G7) | Hermes | run_agent.py:6175, 6663-6687 | 40 | HIGH | NEEDS-ADAPTATION | Re-purpose for non-streaming Bedrock invoke: track tool_use blocks pending tool_result; warn if conversation ends mid-call. v5 has no streaming (constraint #10). |
| N-8 | Retry classifier â€” three categories (H3 G5) | Hermes | run_agent.py:6302-6549 | 100 | HIGH | NEEDS-ADAPTATION | Pre-call / mid-call / post-call retry policy on non-streaming Bedrock invoke. Drop stream-delivery state machine; keep retry-classification logic. |
| N-9 | Mid-call stub recovery with user-visible warning (H3 G6) | Hermes | run_agent.py:6644-6709 | 60 | HIGH | NEEDS-ADAPTATION | Re-purposed: when Bedrock invoke is cancelled/disconnected mid-tool-call (non-streaming), inject synthetic tool_result stub. v5 has no streaming (constraint #10) â€” this is for invoke-level disconnects, not stream chunks. |
| N-10 | Bedrock streaming three-callback model (H3 G20) | Hermes | bedrock_adapter.py | â€” | DROPPED | OUT-OF-SCOPE-CONSTRAINT-#10 | NO STREAMING in v5.0.1. |
| N-11 | Reset stream-delivery tracking per attempt (H3 G21) | Hermes | run_agent.py:6034-6036 | â€” | DROPPED | constraint #10 | â€” |
| N-12 | Local-provider stale-detector disable (H3 G22) | Hermes | run_agent.py:6014-6019 | â€” | DROPPED | not applicable | â€” |
| N-13 | `StreamingToolExecutor` concurrent state machine pattern (R4 #64) | Runnable | tools/StreamingToolExecutor.ts | â€” | DROPPED | constraint #10 | Hermes ThreadPoolExecutor pattern (already in plan) suffices for non-streaming concurrent. |
| N-14 | Plan v3 dynamic tool-ref injection cited via AGENTS.md:627-628 (H5 A36) | Hermes | AGENTS.md:627-628 | 0 | MUST | already in plan | Confirm Q1 evidence row. |
| N-15 | Fuzzy tool-name matching (already in plan) | Hermes | run_agent.py:4689-4720 | (already) | already | â€” | â€” |
| N-16 | Tool-call dedup (already in plan) | Hermes | run_agent.py:4639-4655 | (already) | already | â€” | â€” |
| N-17 | Surrogate sanitize at request-time (folded into A-26) | Hermes | run_agent.py:9897-9901 | (in A-26) | already | â€” | â€” |
| N-18 | Tool interface enrichments (`aliases`, `maxResultSizeChars`, `isDestructive`, `interruptBehavior`) (R7 N14) | Runnable | Tool.ts:362-695 | 60 | MED | CLEAN | Adds to BaseTool. |
| N-19 | TaskCreate/Get/List/Update/Output/Stop tools | Runnable | tasks/* | â€” | DROPPED | constraint #1 | TaskV2 swarm not in v5. |

**Block N total NEW: ~673 LOC (after dropping streaming items).**

### Block T (v4 tool surface parity)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| T-1 | `notebook_edit` (v4 :5921 schema :7275) (R2 finding #1, V1 gap #2) | v4 | sagemaker_agent.py:5921 + 7275 | 120 | MUST | FALSE-POSITIVE-ALREADY-IN-V5 | v5 already has `tools/notebook_edit.py` (Phase 4). Add Block T row 12 explicitly to plan. |
| T-2 | `view_image` (v4 :6419 schema :7307) (V1 gap #3) | v4 | sagemaker_agent.py:6419 + 7307 | 40 | MUST | FALSE-POSITIVE-ALREADY-IN-V5 | v5 already has `tools/view_image.py` (Phase 4). Add Block T row 13. |
| T-3 | `SemanticSearch` class verbatim port (V1 gap #4) | v4 | sagemaker_agent.py:6461-6610 | 150 | MUST | CLEAN | Block T `tool_semantic_search` is hollow without underlying class. |
| T-4 | WebFetch fold-ins: 15-min URL LRU cache + same-host redirect + Turndown (R3 row 20) | Runnable | utils.ts:63-243 | 80 | HIGH | NEEDS-ADAPTATION | Python `markdownify` for Turndown; `MAX_REDIRECTS=10` same-host policy. **Confirms approval of fold-ins.** |
| T-5 | `tool_skill` + `tool_skill_propose_patch` registry rows (R2 finding #2) | v4 | sagemaker_agent.py:6674, 6703 | 0 (already wired) | LOW | doc-only | Confirm Block D dispatcher. |
| T-6 | `semanticBoolean` / `semanticNumber` coerce (R8 #2) | Runnable | utils/semantic*.ts | 30 | MED | CLEAN | Bedrock sometimes quotes booleans. |
| T-7 | `readFileInRange` fast/streaming with FileTooLargeError (R8 #35) | Runnable | utils/readFileInRange.ts | 250 | HIGH | NEEDS-ADAPTATION | Big correctness improvement on large logs. |
| T-8 | `lockfile` lazy wrapper (R8 #36) | Runnable | utils/lockfile.ts:1-44 | 30 | LOW | CLEAN | `portalocker` Python equivalent. |
| T-9 | `tagMessagesWithToolUseID` (R3 row utils.ts) | Runnable | tools/utils.ts | 0 | DROPPED | low-value | Defer (no streaming UI placeholders). |
| T-10 | API limits constants (5MB image / 20MB PDF / 100 pages) (R8 #29) | Runnable | constants/apiLimits.ts | 20 | HIGH | CLEAN | Fail-fast client-side. |
| T-11 | Tool result limits + per-message budget (R8 #30) | Runnable | constants/toolLimits.ts | 30 | HIGH | CLEAN | 200K char per-message tool result aggregate cap. |
| T-12 | XML tag constants (R8 #27) | Runnable | constants/xml.ts | 30 | LOW | CLEAN | Centralize tag names. |

**Block T total NEW (post-Wave-5): ~780 LOC + 3 doc-rows for already-in-v5 tools.**

### Block J (Real-Bedrock smoke + zip verify)

No additional NEW deltas.

### Block K (Process discipline)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| K-1 | Audit-dir shape `<date>-<topic>/01-..._N.md + 00-SYNTHESIS.md` (L2 LF-DOC-6) | LF | docs/audits/ | 0 (process) | HIGH | CLEAN | Apply to wave_5_deep + future audits. |
| K-2 | PORT_LOG `evidence_tier` column (VERIFIED/LISTED) (L2 LF-DOC-8) | LF | docs/REUSABLE_MODULES.md | 0 (schema) | HIGH | CLEAN | Forces honest evidence claims. |
| K-3 | CHANGELOG-as-postmortem entry shape (L2 LF-CHANGELOG-1) | LF | CHANGELOG.md | 0 (process) | MED | CLEAN | Symptom/Root cause/Fix/Verification subsections. |
| K-4 | Pre-flight 5-category gate (L2 LF-DOC-2) | LF | docs/PREFLIGHT_PROTOCOL.md | 0 (process) | HIGH | CLEAN | Reinforces existing per-block gate. |
| K-5 | Three-critic AXIS A/B/C (value/timing/cost) (L2 LF-DOC-5) | LF | docs/audits/2026-04-21-a-plus-review/ | 0 (process) | MED | CLEAN | Three separate critic prompts per block. |
| K-6 | A44 No-change-detector-tests policy (H5 A44) | Hermes | AGENTS.md:Test-policy | 0 (policy) | **MUST** | CLEAN | v5 test refactor: rewrite snapshot-asserts as invariants. |
| K-7 | A39 No-wire-dead-code without E2E (H5 A39) | Hermes | AGENTS.md:Pitfall | 0 (policy) | HIGH | CLEAN | Each cherry-pick from v4/Runnable/Hermes/LF E2E-validated. |
| K-8 | A41 Hermetic test parity (H5 A41) | Hermes | AGENTS.md | 0 (process) | MED | CLEAN | Unset env vars, fixed TZ/locale. |

**Block K total NEW: ~0 LOC (all process), 8 policies/protocols added.**

### Block F2 (NEW BLOCK â€” Auto-continuation under iteration budget) **CRITICAL**

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| F2-1 | TokenBudget auto-continuation (R7 N4) | Runnable | query/tokenBudget.ts:1-93 + query.ts:1308-1355 | 100 | HIGH | NEEDS-ADAPTATION | v5 IterationBudgetWidget shows budget but doesn't auto-continue. <90% AND not diminishing-returns â†’ inject nudge + continue. |

**Block F2 total NEW: ~100 LOC. NEW BLOCK.**

---

## 3. Per-Block deltas (LOC + new PORT_LOG row count)

| Block | Pre-Wave5 LOC | Delta | Post-Wave5 LOC | New PORT_LOG rows |
|---|---:|---:|---:|---:|
| 0 + smoke gate | 100 | +200 | 300 | 11 |
| B | 440 | +456 | 896 | 16 |
| B+ | 325 | +225 | 550 | 8 |
| C | 250 | +555 | 805 | 19 |
| C+ | 200 | +40 | 240 | 3 |
| D | 700 | +550 | 1,250 | 13 |
| A | 3,300 | +1,510 | 4,810 | 43 |
| E + F | 2,300 | +305 | 2,605 | 8 |
| **F2 (NEW)** | â€” | +100 | 100 | 1 |
| I | 50 | +335 | 385 | 13 |
| M | 30 | 0 | 30 | 0 |
| G | 280 | +155 | 435 | 8 |
| **G3 (NEW)** | â€” | +300 | 300 | 2 |
| G2 | 100 | 0 | 100 | 0 |
| H | 1,252 | +945 | 2,197 | 20 |
| **H+ (NEW)** | â€” | +350 | 350 | 1 |
| L | 250 | +966 | 1,216 | 28 |
| N | 300 | +673 | 973 | 19 (12 ports + 7 dropped clarifications) |
| T | 1,100 | +780 | 1,880 | 12 |
| J | 150 | 0 | 150 | 0 |
| K | 200 | 0 | 200 | 8 (process/policy) |
| **TOTAL** | **11,330** | **+8,545** (Wave-5-DEEP) | **~16,200** (after dedup ~5%) | **+233 rows** |

(Conservative ~5% dedup reduces TOTAL to ~15,400-16,200 LOC. Pre-Wave-5 was 11,330; post-Wave-5-DEEP is ~16,200. Growth factor 1.43x â€” material but not double, consistent with R4's "+1900-2200 LOC" estimate scaled across the other 19 reports.)

---

## 4. New blocks recommended

| Block | Reason | LOC | Sequencing |
|---|---|---:|---|
| **G3 â€” Coordinator System Prompt** | R7 N1's 258-LOC prompt encodes user's #1 collaboration rule (4 phases, never delegate understanding, continue-vs-spawn matrix). Plan v3 Block G has 7 sub-agent types but no orchestration prompt. **Q3 axis 2 (agent coordination) demands this.** | 300 | After Block G, before Block G2 |
| **F2 â€” Auto-Continuation Under Iteration Budget** | R7 N4 â€” IterationBudgetWidget without auto-continue is half the feature. <90% threshold + diminishing-returns halt. | 100 | After Block E+F |
| **H+ â€” Memory Consolidation Engine (manual `/dream` only)** | R12 R12-1 â€” fits Q3 long/complex coding axis; pays down memory debt across sessions. ~350 LOC. **NO daemon, NO auto-fire** (user decision 2026-05-01). Fires only when user runs `/dream`. | 350 | After Block H |

All three are NEEDS-ADAPTATION. None are CONFLICT-REJECT. All comply with no-deferrals.

---

## 5. Architectural fit verdicts

### CLEAN-FIT (no adaptation, port verbatim or near-verbatim)
- Block 0: 0-3 (Bedrock extra-params Set), 0-4 (env block phrasings)
- Block B: B-1 to B-11 (token math)
- Block B+: B+1 to B+7 (cost UX)
- Block C: most rows (FileEdit utils, BashTool semantics, secret patterns, escapeXml)
- Block D: D-1 to D-7 (commands hygiene)
- Block A: A-1 to A-43 except A-13 (cache-sharing-fork) and A-27 (flush_memories)
- Block H: H-1 to H-17 (memory mechanics)
- Block H+: nothing (entire block is NEEDS-ADAPTATION)
- Block L: most rows (PromptStateSnapshot, Haiku exclude, error humanizer)
- Block N: N-1 to N-3, N-6, N-7
- Block T: T-3 (SemanticSearch port), T-10, T-11, T-12

### NEEDS-ADAPTATION
- 0-9 (feature-flag fail-closed) â€” Python `runtime/feature_flags.py` shim
- A-13 (compactConversation cache-sharing-fork) â€” Pairs with G2 Bedrock cache invariants
- A-27 (flush_memories) â€” Aux-client first, fallback primary; v5 may use same client
- A-33 (A28 prompt-cache invariant policy) â€” Refactor v5 prompt builder
- A-40 (SYSTEM_PROMPT_DYNAMIC_BOUNDARY) â€” Refactor `_build_system_prompt`
- C-17 (combinedAbortSignal + AsyncLocalStorage cwd) â€” Python `contextvars` + `asyncio.Event`
- F2-1 (TokenBudget auto-continue) â€” Wire into v5 query loop
- G3-1 (Coordinator system prompt) â€” Substitute Runnable tool names; gated on CONFIG flag
- H-13 (SessionMemoryCompactConfig) â€” Replace GrowthBook with config-file
- H+1 (memory consolidation engine, manual /dream only) â€” synchronous Python (no threading, no asyncio, no daemon)
- L-5 (FallbackTriggeredError model switch) â€” Bedrock fallback inference profile
- L-7 (Persistent retry mode) â€” env-gated `SAGEMAKER_UNATTENDED_RETRY`
- L-17 (API error humanizer) â€” Drop Cloudflare, keep JSON-body
- L-20 (Three-tier recovery ladder) â€” "retry â†’ IAM token refresh â†’ user-error"
- L-21 (Daemon-thread Bedrock call) â€” boto3 thread pattern
- L-28 (Bedrock Guardrails) â€” boto3 Bedrock parameter
- N-3 (parallelism constants) â€” Filter `_PARALLEL_SAFE_TOOLS` to v5 tool surface
- N-4 (worker race fix + checkpoint) â€” Python threading
- N-8 (two-policy stream retry) â€” Adapt to non-streaming "API call dropped mid-tool"
- N-9 (partial stub recovery) â€” Adapt to non-streaming
- T-4 (WebFetch fold-ins) â€” Python `markdownify`
- T-7 (readFileInRange) â€” `aiofiles` or `seek` Python

### CONFLICT-REJECT
- C+1 (EnterPlanMode formal mode) â€” REJECT in favor of v4's `/phase`. v5 already has lighter-weight equivalent.
- N-10 / N-11 / N-12 / N-13 (streaming tool executor + streaming retry resets) â€” REJECT per constraint #10 (no streaming).

### FALSE-POSITIVE-ALREADY-IN-V5 (V1 findings â€” implementation-level present but PORT_LOG-row missing)
| Item | v5 file | Action |
|---|---|---|
| `tools/notebook_edit.py` (T-1) | `compact_v5/MAIN/agent/tools/notebook_edit.py` (Phase 4) | Add explicit Block T row 12. |
| `tools/view_image.py` (T-2) | `compact_v5/MAIN/agent/tools/view_image.py` (Phase 4) | Add explicit Block T row 13. |
| `runtime/bedrock_client.py` (B-12) | `compact_v5/MAIN/agent/runtime/bedrock_client.py` (Phase 1) | Add explicit Block B row. |
| `security/manager.py` + `dangerous_*.py` + `high_risk.py` (C-1) | `compact_v5/MAIN/agent/security/` (Phase 5) | Add explicit Block C row. |
| `prompt/*.md` system prompt (0-1) | `compact_v5/MAIN/agent/prompt/` (Phase 6) | Add explicit Block 0 row. |
| `core/budget.py` ContextManager (B-15) | `compact_v5/MAIN/agent/core/budget.py` | Add doc row. |
| `runtime/truncation.py` (B-14) | `compact_v5/MAIN/agent/runtime/truncation.py` | Add doc row. |
| `skills/manager.py` SkillManager (Block I impl) | `compact_v5/MAIN/agent/skills/manager.py` | Already in plan; reinforce. |
| `core/retry.py` RetryHandler (V1 lesser #12) | `compact_v5/MAIN/agent/core/retry.py` | Decide: keep v4 RetryHandler OR Block L's withRetry; CHOOSE Block L (Runnable supersedes per Q3). |

### MCP STATUS RESOLUTION (V1 inconsistency #13)
v5 has `mcp/__init__.py` only (empty stub). Constraint #9 says drop MCP. **Resolution: keep `mcp/` as empty stub (no file `mcp_client.py` exists in v5)**; V1's claim that "MCP classes PRESENT in v5 runtime/mcp_client.py" is incorrect. No code regression. Constraint #9 holds.

---

## 6. v4 verbatim ports needing explicit PORT_LOG rows (V1 findings)

Per V1's 8 hard gaps + 6 lesser concerns, **add 14 PORT_LOG rows** to Q1 matrix to remove implicit-baseline ambiguity. Each row references the v4 file:line and the v5 target file (where already-implemented).

| # | v4 symbol | v4 line | v5 target file | Status | Action |
|---|---|---|---|---|---|
| V1.1 | `ToolResult` @dataclass | :867-886 | `runtime/tool_result.py` (NEW) | MISSING | **PORT** ~25 LOC |
| V1.2 | `tool_notebook_edit` | :5921 + :7275 | `tools/notebook_edit.py` (Phase 4) | PRESENT | Add row 12 to Block T |
| V1.3 | `tool_view_image` | :6419 + :7307 | `tools/view_image.py` (Phase 4) | PRESENT | Add row 13 to Block T |
| V1.4 | `SemanticSearch` class | :6461-6610 | `tools/semantic_search.py` (NEW class part) | MISSING | **PORT** ~150 LOC |
| V1.5 | `_scan_for_prompt_injection` + `_INJECTION_PATTERNS` | :7509-7541 | `security/prompt_injection.py` (NEW) | MISSING | **PORT** ~40 LOC (NOT a Hermes adoption â€” v4-native) |
| V1.6 | `SYSTEM_PROMPT` | :8029-8189 | `prompt/*.md` (Phase 6) | PRESENT (split) | Add doc row to Block 0 |
| V1.7 | `BedrockClient` class | :2378-2565 | `runtime/bedrock_client.py` (Phase 1) | PRESENT | Add doc row to Block B |
| V1.8 | `SecurityManager` class | :1298-2106 | `security/manager.py` + `dangerous_*.py` + `high_risk.py` (Phase 5) | PRESENT | Add doc row to Block C |
| V1.9 | `Config` dataclass (~50 fields) | :1018-1149 | `runtime/config.py` | PRESENT | Add doc row to Block 0 |
| V1.10 | `ContextManager` | :3464-3528 | `core/budget.py` | PRESENT | Add doc row to Block B |
| V1.11 | `Truncation` | :756-861 | `runtime/truncation.py` | PRESENT | Add doc row to Block B |
| V1.12 | `RetryHandler` + `RETRY` | :116, :179 | superseded by Block L (Runnable withRetry) | DECISION | Block L IS the v5 retry path; v4 `RetryHandler` not separately ported |
| V1.13 | MCP classes | :3122-3454 | `mcp/__init__.py` (empty stub) | DROPPED-BY-CONSTRAINT-#9 | Confirm drop; no `mcp_client.py` file exists |
| V1.14 | `load_project_instructions` (CLAUDE.md loader) | :7419-7456 | `runtime/claude_md.py` (NEW or merge) | PARTIAL | Pair with H-18 (CLAUDE.md aggregation) |

---

## 7. Conflict resolutions

### R1 vs constraint #10 (no streaming)
- **R1 G20 Bedrock streaming three-callback model**: DROP per constraint #10.
- **R1 G1-G7 streaming retry classifier**: KEEP. Adapt as non-stream patterns (`partial_tool_names` warning works on Bedrock Converse non-streaming when SDK retry exhausts mid-tool â€” same outcome). The two-policy retry classifier (pre-delivery / mid-tool-call / post-delivery) translates cleanly to non-streaming: Bedrock Converse can fail mid-call before any output is parsed, or after the JSON tool_use block but before tool execution.

### R5 prior "OUT-OF-SCOPE" (JSON repair) vs H1 "HIGH PRIORITY" (multi-pass JSON repair)
- **H1's `_repair_tool_call_arguments` (95 LOC)** observes Haiku-on-Bedrock emitting malformed `arguments` strings on long contexts. R5's prior reasoning applied to Runnable's broader auto-repair (which depends on Hermes-only patterns) â€” R5 was right to skip Runnable's specific path. H1 surfaces the **same primitive** that v5 needs for Bedrock-Haiku resilience. **VERDICT: ADOPT (Block C-18, C-19).** Hermes lines 547-641 + 505-544 verbatim port. Resolves the PS-class "tool call empty arguments" failure.

### R5 prior "OUT-OF-SCOPE" (surrogate sanitize) vs H1 "MEDIUM PRIORITY"
- **H1's surrogate sanitization (115 LOC)** is defense-in-depth for any Bedrock JSON content. R5 deferred because Runnable's parent feature (team-mem upload) was OOS. H1 demonstrates an independent Bedrock failure mode (model output â†’ tool_result content with lone surrogates â†’ boto3 JSON encoder crashes). **VERDICT: ADOPT (Block A-26).** Lines 384-502 verbatim. Per-Bedrock-call defensive layer.

### V1 "missing notebook_edit/view_image/skill" vs Wave 5 "v5 already has these"
- **V1's claim**: 11 v4 tools listed in Block T misses notebook_edit + view_image (v4 has 22+ tools).
- **Wave 5 reality**: `compact_v5/MAIN/agent/tools/notebook_edit.py` and `view_image.py` exist (built in Phase 4).
- **VERDICT**: V1 is right at PORT_LOG-row level (rows missing); wrong at code level (files present). **Action**: Add 2 PORT_LOG rows to Block T (T-1, T-2 marked FALSE-POSITIVE-ALREADY-IN-V5). Block T row count goes 11 â†’ 13.

### R1 "Block J worktree" confusion clarification
- **R1 references Block J** in items #92, #105 ("EnterWorktree"/"ExitWorktree").
- **Plan v3 reality**: Block J = real-Bedrock smoke + zip verification. Worktree spawn lives in **Block G** (`AGENT_TYPES + worktree`).
- **VERDICT**: R1's "Block J" mentions are mis-tagged. **Action**: Re-tag to **Block G**. Drop EnterWorktree/ExitWorktree formal tools (R1 #92-108) â€” v4's worktree spawn is implicit (not a user-facing tool); SageMaker workspace usually `/home/sagemaker-user/`, not a git repo.

### MCP yes/no
- **Constraint #9**: Drop MCP entirely.
- **V1 reports MCP classes "PRESENT in v5 runtime/mcp_client.py"** â€” but actual filesystem inspection shows only `mcp/__init__.py` (empty).
- **VERDICT**: V1 was wrong. MCP is genuinely dropped in v5. Constraint #9 holds. No `mcp_client.py` to delete.

---

## 8. Critical rules adopted (Hermes A28 / A36 / A44)

### A28 â€” Prompt-cache invariant policy (Block A + Block 0)
**Statement**: NEVER rebuild system prompt mid-conversation. NEVER change toolsets mid-conversation. NEVER reload memories mid-conversation. The ONLY mid-conversation context mutation allowed is during context compression. Slash commands that mutate system-prompt state default to deferred invalidation (next session) with opt-in `--now` flag.
**Enforcement**:
- Block 0: `prompt/_CACHE_BOUNDARY.md` marker file (already exists in v5) â€” formalize via Block A-40 static/dynamic boundary refactor.
- Block A: A-21 `runPostCompactCleanup` invalidates cache **only on compact**.
- Block D: `/skill use --now` opt-in pattern; default = next-session.
- Block I: I-1 conditional `paths:` skill activation defers to next request boundary.

### A36 â€” Dynamic cross-tool reference (Block N â€” already in plan)
**Statement**: Tool schema descriptions MUST NOT mention tools from other toolsets by name (causes hallucination). Dynamic injection in `get_tool_definitions()` post-processing.
**Enforcement**: Plan v3 Block N already commits to this. Confirm Q1 evidence row cites Hermes AGENTS.md:627-628.

### A44 â€” No change-detector tests (Block K policy)
**Statement**: Tests that fail when expected-to-change data updates (model catalogs, version literals, enumeration counts) provide no behavioral coverage. Rewrite as invariants/contracts.
**Enforcement** (Block K policy K-6):
- v5 test refactor pass: identify all `assert 'X' in MODELS` / `assert COUNT == N` / `assert VERSION == 'v.X.Y'` patterns; rewrite as set-disjointness, every-model-has-context-length, migration-bump-to-current asserts.
- Test files to refactor: scan `compact_v5/MAIN/agent/tests/` for snapshot patterns. Estimated impact: ~10-30 test files audited; ~5-10 require rewrite.
- New test files (post-Wave-5 ports) must follow contract-not-snapshot rule.

---

## 9. Drops with categorical reasons (NO DEFERRALS)

Every item not adopted gets a categorical reason. No "v5.0.2 punt".

| Drop | Source | Reason |
|---|---|---|
| Streaming tool executor (R4 #64, all H3 stream items G20-G22, N-10/N-11/N-12/N-13) | Constraint #10 (no streaming in v5) | SageMaker UI cannot stream. Hermes ThreadPoolExecutor non-streaming pattern (Block N-4, N-5) suffices. |
| EnterPlanMode / ExitPlanMode formal tools (C+1) | v4's `/phase` is lighter-weight equivalent | Avoids new mode + new state + new UI; v5 keeps `/phase <text>` from Block D. Drop tool, retain v4 PLAN_MODE_ALLOWED_TOOLS gate. |
| MCP entire subsystem (R2 all MCP tools, R5 MCP files, R6 MCP commands, R8 MCP types) | Constraint #9 | Single-user SageMaker has no external MCP servers. |
| Voice / VoiceStreamSTT / voiceKeyterms (R5, R10, etc.) | Constraint #1 (Bedrock-only, no audio) | SageMaker has no microphone access. |
| OAuth (R5, R6) | Constraint Bedrock-only IAM | SageMaker uses IAM role + STS, not Anthropic OAuth. |
| Multi-user / teammate / swarm (R1 #16-26, R5 teamMemorySync, R6 SendMessage etc.) | Constraint #1 | Single-user SageMaker. |
| IDE bridge / LSP / VS Code (R5 lsp/, R10 components/, R11 bridge) | Constraint #2 (chat.ipynb canonical) | No IDE socket. |
| Plugin marketplace (R5 plugins/, R6 plugin commands) | Constraint #1 | Single-user SageMaker has no remote install. |
| Anthropic claude.ai subscription features (R5 claudeAiLimits, R6 upgrade/passes/etc.) | Bedrock-only | No Pro/Max plan. |
| Telemetry / GrowthBook / OTel external endpoints (R5 analytics/, R7 init.ts) | Bedrock-only no external network | No analytics endpoint. |
| Codex / OpenRouter / OpenAI / Gemini / Qwen / Kimi / etc multi-provider (H1, H2, H3, H5) | Bedrock-only | v5 has single Bedrock provider. |
| Codex Responses API (H2 C29) | Bedrock-only | â€” |
| Anthropic API direct (H1 #22, H3 Â§1.7) | Bedrock-only | v5 uses boto3 Bedrock. |
| Gateway / `/steer` / interactive-handler (H2 C27-C30, H3 6-7-9) | No gateway in v5 single-user | â€” |
| Background-task subsystem (R7 C44-C49, Task/tasks/) | Constraint #1 + #2 | No bg-task UI in chat.ipynb. |
| `claude ps` / `--resume` / multi-conversation (R6 branch/rename) | Single-session | â€” |
| `/insights` (R6) | Host Claude Code logs only | Doesn't apply inside SageMaker agent. |
| Auto-dream `partialCompactConversation` (R4 #32) | No message-selector UI in ipynb | Drop. |
| Profile system (H5 A30-A32) | Single-user | â€” |
| Vim / keybindings / terminal setup (R6, R8 #46) | chat.ipynb UI | â€” |
| `cron` / scheduled remote agents (R2 ScheduleCronTool) | No daemon in SageMaker | â€” |
| `commit` / `commit-push-pr` slash commands (R6) | User-pref no autonomous commits | â€” |
| `branch` / `rename` (R6) | Single-conversation | â€” |
| Bridge / Remote / RemoteTrigger / SendUserFile (R2, R3, R10) | Bedrock-only no external network | â€” |
| WebSearch (R3 #21) | Bedrock provider not in `isEnabled()` allowlist | Permanently disabled even if shipped. |
| ASCII-only fallback (H1 #18) | SageMaker is UTF-8 | â€” |
| Credential pool / fallback chain (H1 #20, H3 Â§1.5/1.6/1.12, H5 #12-13, #15-16) | Single Bedrock IAM | â€” |
| `/factory-report` accept/reject loop (L2 LF-CMD-3) | Factory-level meta, not v5 | â€” |
| 4-agent UX grading (L2 LF-AUDIT-2) | v5 has no UX surface beyond frozen v4 chat.ipynb | â€” |
| `.claude/settings.json` per-project doctrine (L2 LF-DOC-10) | SageMaker has no Claude Code settings layer | â€” |
| LF hooks/* host-side (L1 most rows) | Host-side dev workflow, not Bedrock agent | â€” |
| Codex gpt-5.3-codex commit-gate (L1 codex-judge-gate) | Bedrock-only forbids OpenAI inside SageMaker | â€” |
| `tagMessagesWithToolUseID` (R3 utils.ts) | No streaming UI placeholders in v5 | â€” |
| Lazy hook framework / settings.json hooks (R9 #6-#10) | No multi-tenant settings infra | v4's audit_log + approval gate suffices for single-user. |
| Skill-improvement survey (R9 #7) | v4.9.5 model-proposes-patch is superior | â€” |
| Bash classifier auto-approval (R9 #8) | No permission dialog to race in single-user trust mode | â€” |
| `fileSuggestions.ts` @-mention typeahead (R9 #11) | No @-typeahead UI in Jupyter input | â€” |
| Output styles (R9 #19, R8 #72) | Fixed system prompt in v5 | â€” |
| TaskV2 family (R3 TaskCreate/Get/List/Update/Output/Stop) | Multi-agent swarm out-of-scope | â€” |
| Buddy/companion virtual pet (R10) | UI gimmick | â€” |

**Total drops with categorical reason: ~80 patterns/tools.**

---

## 10. Total LOC estimate + sequence

### Pre-Wave-5 â†’ Post-Wave-5-DEEP
- **Pre-Wave-5**: 11,330 LOC, 18 Blocks (E+F counted as 1 combined)
- **Post-Wave-5-DEEP**: ~19,300 LOC (corrected per Codex AXIS A 2026-05-01 â€” actual sum of per-Block NEW deltas is ~7,943 LOC NEW + 11,330 LOC pre-DEEP = ~19,273; rounded to ~19,300), **21 Blocks** counting E+F as 1 combined block (added: G3, F2, H+); plus notebook-smoke-gate checkpoint after Block 0
- **Growth**: 1.70x (consistent with R4 alone projecting +1,900-2,200 LOC and being one of 20 slices)
- **New PORT_LOG rows**: +233 (Q1 matrix grows from 215 â†’ ~448 rows)
- **New blocks**: G3 (Coordinator Prompt), F2 (Auto-Continuation), H+ (Auto-Dream)

### Updated build sequence

```
Block 0  â†’ notebook smoke gate
        â†’ B   (TokenTracker + Bedrock count + ToolResult)
        â†’ B+  (SessionManager + cost UI + FileCache)
        â†’ C   (Runtime safety + secret scanner + bash hardening + JSON repair)
        â†’ C+  (Approval/diff + rate limits â€” minus Plan Mode)
        â†’ D   (Slash commands + custom expander + new skills + /dream)
        â†’ A   (Compactor COMBINED + cache invariants + sanitize)
        â†’ E + F  (UI rendering + cell widgets)
        â†’ F2  (NEW â€” auto-continuation under iteration budget)
        â†’ I   (Skill discovery + paths: + scaffolders)
        â†’ M   (Phase 8 fixes â€” already small)
        â†’ G   (AGENT_TYPES + worktree + agent memory scoped)
        â†’ G3  (NEW â€” coordinator system prompt)
        â†’ G2  (forkSubagent cache-prefix replay)
        â†’ H   (Memory extraction COMBINED + invariant-preserving SM-compact)
        â†’ H+  (NEW â€” memory consolidation engine, manual /dream only, no daemon)
        â†’ L   (Error/retry/cache-break + Bedrock guardrails + daemon-thread call)
        â†’ N   (Parallel exec + dynamic tool refs â€” full citations)
        â†’ T   (v4 tool surface + WebFetch fold-ins + readFileInRange)
        â†’ J   (Real-Bedrock smoke + zip verify)
        â†’ K   (Process discipline + AXIS C + 3-critic + A44 test refactor)
```

Each Block lands as **commit + Codex AXIS A/B/C 3-critic review + user approval** (per Block K + L2 LF-DOC-5).

---

## 11. Files to update

### `V5_PHASE_2_PLAN_v3.md` â†’ write **`V5_PHASE_2_PLAN_v5.md`** (renaming v4â†’v5 since this is post-Wave-5-DEEP)
Sections that need changes:
- Â§1 (v4 baseline COMPLETE table): add 14 rows from V1 verifier (ToolResult / SecurityManager class / SemanticSearch / SYSTEM_PROMPT / BedrockClient / Config dataclass / ContextManager / Truncation / RetryHandler decision / MCP-drop confirmation / load_project_instructions / _scan_for_prompt_injection / Config piecemeal-to-master).
- Â§2 (15 hard constraints): unchanged.
- Â§3 (Block-by-block plan): expand each Block with the per-block deltas from Â§3 above. Add Block G3, F2, H+ as new sub-sections.
- Â§4 (Sequencing): replace with the updated sequence in Â§10 above.
- Â§5 (LOC summary): replace with Â§3 table above (post-Wave-5 totals).
- Â§6 (4 user-question evidence): no change to mapping; reinforce K-6 (no-change-detector) under Q4.
- Â§7 (Status): append "Wave 5-DEEP synthesis complete; +233 PORT_LOG rows; 3 new Blocks; pending Codex AXIS A/B/C 3-critic review."

### `Q1_EVIDENCE_MATRIX.md`
Append rows N to N+232 (rows 216-448). Each row references one source file:line. Add new column `evidence_tier: VERIFIED | LISTED` (per K-2). Mark all 233 new rows VERIFIED (Wave-5-DEEP read full files). Mark Wave 1-4 prior rows that didn't verify source as LISTED (separate audit pass).

### `Q3_BETTER_THAN_MATRIX.md`
Add new axis row "security/PII protection" (R5 finding) â€” v5 > v4 (38 patterns + redaction vs 13 patterns).

### `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` (THIS FILE)
Canonical builder reference going forward. Builder applies verbatim before each Block.

### `V5_BUILD_STATUS.md`
Append entry:
```
2026-05-01 Wave 5-DEEP synthesis complete.
- 20 reports consumed (R1-R12, H1-H5, L1-L2, V1)
- ~150 net-new findings consolidated
- 233 PORT_LOG rows added (Q1 matrix 215 â†’ 448)
- 3 new Blocks: G3 (Coordinator Prompt), F2 (Auto-Continuation), H+ (Memory Consolidation Engine, manual /dream only â€” no daemon)
- 5 NOT-OPTIONAL correctness fixes flagged
- LOC: 11,330 â†’ ~16,200 (1.43x)
- Pending: Codex AXIS A/B/C 3-critic review per Block K
- Reading order: SYNTHESIS_MASTER.md â†’ V5_PHASE_2_PLAN_v5.md â†’ Q1_EVIDENCE_MATRIX.md
```

### `compact_v5/_phase_2/wave_5_deep/00-SYNTHESIS.md`
Symlink or short pointer to SYNTHESIS_MASTER.md so the audit-dir shape (per K-1, L2 LF-DOC-6) is satisfied.

### Audit dir naming retrofit
Rename current Wave-5-DEEP files to follow pattern (`01-R1-tools-A-F.md`, `02-R2-tools-G-R.md`, ..., `21-V1-v4-inventory.md`, `22-SYNTHESIS-MASTER.md`) â€” DEFERRED: optional polish per K-1; not a blocker.

---

## Builder gate

Before starting any Block:
1. Read this SYNTHESIS_MASTER.md end-to-end.
2. Read `V5_PHASE_2_PLAN_v5.md` Block section.
3. Read all PORT_LOG rows in Q1 matrix tagged with that Block.
4. Run pre-flight 5-category check (per K-4): hooks / perms / reviewer / tree / session-state.
5. Implement Block.
6. Run 3-critic AXIS A/B/C review (per K-5).
7. **GATE**: Codex must say 100% clean. Fix issues, re-run until pass.
8. User approves.
9. Commit. Push.
10. Move to next Block.

**End of SYNTHESIS_MASTER.**


 succeeded in 1317ms:
# V5 Design Decisions (append-only ADRs)

Each entry is a mini-ADR. Never edit a closed entry; supersede with a new one referencing the old by id.

---

## ADR-001 â€” File-per-tool layout instead of dir-per-tool
- Date: 2026-04-30
- Phase ID: 00
- Status: ACCEPTED
- Source: V5_PLAN.md Â§"Port map (Runnable â†’ v5)" row `tools/<Name>/` â†’ `tools/<name>.py`

### Question 1 â€” Replacement or addition?
- Does this REPLACE something v4 already has? **YES** â€” replaces v4's monolithic `TOOLS = {}` dict in `compact_v4/MAIN/agent/sagemaker_agent.py:7105`.

### Question 2 â€” Architectural justification (ADDITIONS only)
N/A â€” this is a replacement, not an addition.

### Question 3 â€” Cost
- Token cost (static prompt): 0 (tool-loading is runtime-only).
- Token cost (per turn): 0 (per-tool schemas already shipped per turn in v4 too).
- Code complexity: ~25 separate files vs 1 monolith â€” but each file is small, testable, and the deferred-loading pattern (Phase 7) requires per-tool isolation.
- Maintenance: one tool per file; adding a new tool = adding one file + one `registry.py` entry.

### Question 4 â€” Cost worth it?
N/A (replacement).

### Decision
- **ACCEPTED for v5.0**

### Rationale
Runnable uses dir-per-tool (`tools/BashTool/{prompt.ts, executor.tsx, UI.tsx}`) because TS/React needs separate JSX/types files. Python doesn't â€” one file per tool with `prompt`, `schema`, `execute`, `is_read_only` attributes is enough. ADAPT verdict (mechanism differs, intent preserved). The Addition Gate is N/A here because this is a structural rewrite of a v4 component, not a new feature.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** â€” constraint = `.ipynb workflow` (Python flat-zip ship surface; no JSX/React/Ink runtime).

### Affected files
- compact_v5/MAIN/agent/tools/*.py (all tool modules)
- compact_v5/MAIN/agent/tools/registry.py
- compact_v5/_rebuild_zip.py (flatten step)

### Linked port-log rows
(filled in during Phase 2)

---

## ADR-002 â€” File-per-section system prompt with `prompt/*.md`
- Date: 2026-04-30
- Phase ID: 00
- Status: ACCEPTED
- Source: V5_PLAN.md Â§"The single key architectural improvement"

### Question 1 â€” Replacement or addition?
- Does this REPLACE something v4 already has? **YES** â€” replaces v4's `SYSTEM_PROMPT` 5000-token f-string at `compact_v4/MAIN/agent/sagemaker_agent.py:8029`.

### Question 2 â€” Architectural justification
This IS the structural fix for v4's "buried matrix" failure. Each section becomes a reviewable, token-budgeted unit. Adding new content requires creating a new file (mechanically reviewed) instead of appending to an unreviewable monolith.

### Question 3 â€” Cost
- Token cost (static prompt): expected REDUCTION from ~5000 to â‰¤2500 (target).
- Code complexity: ~14 small `.md` files + `prompt/sections.py` (~200 LOC) vs 1 giant f-string. Trade dispersion for reviewability.

### Question 4 â€” Cost worth it?
N/A (replacement; the cost IS reduced complexity per file).

### Decision
- **ACCEPTED for v5.0** â€” load-bearing for Phase 6.

### Runnable-fidelity impact
**FAITHFUL** â€” directly ports `constants/systemPromptSections.ts` registry pattern. Python `.md` files are the equivalent of TS section-functions; cache-boundary marker file replaces TS `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` constant.

### Affected files
- compact_v5/MAIN/agent/prompt/__init__.py
- compact_v5/MAIN/agent/prompt/sections.py
- compact_v5/MAIN/agent/prompt/*.md (14 files)

### Linked port-log rows
(filled in during Phase 6)

---

## ADR-003 â€” v5 must address ALL 7 issues from `PS_actual_use_problems.md`
- Date: 2026-04-30
- Phase ID: 00
- Status: ACCEPTED
- Source: User instruction 2026-04-30 + `compact_v4/docs/PS_actual_use_problems.md` (copied to `compact_v5/docs/PS_actual_use_problems.md`)

### Question 1 â€” Replacement or addition?
- This is a **scope binding**, not a feature. v4.10.10 in-place fixes addressed issues 1, 2, 5, 6, 7 partially. v5 must address ALL 7 structurally.

### Question 2 â€” Architectural justification
v4's failure was that issues were patched individually but the ARCHITECTURE didn't change. v5's structural opportunity (sectioned prompt, deferred loading, Hermes skill filter) lets each issue get a structural fix instead of a patch. Specifically:
- Issue 1 (CSO warnings) â†’ audit-level discipline (Phase 10 tests)
- Issue 2 (iter budget) â†’ UI slider + status bar (Phases 1, 8, 11)
- Issue 3 (cold cache) â†’ reuse v4 + status indicator (Phase 8)
- Issue 4 (thinking) â†’ docs + status indicator (Phase 1, 6)
- Issue 5 (session cost persist) â†’ SessionManager.save/load round-trip (Phase 1)
- Issue 6 (wiring bug pattern) â†’ Codex AXIS-A gate enforcement (every phase)
- Issue 7 (buried matrix) â†’ sectioned prompt + cognitive-load audit (Phase 6, 7)

### Question 3 â€” Cost
- Token cost: 0 (this is process discipline, not prompt content).
- Code complexity: small additions to V5_PS_ISSUES_MAPPING.md + per-phase tests.
- Maintenance: each phase that addresses an issue must include a test asserting the issue's failure mode no longer occurs.

### Question 4 â€” Cost worth it?
**Yes**. The user explicitly required this. Skipping it means v5 fails on launch the same way v4 did.

### Decision
- **ACCEPTED for v5.0** â€” binding constraint on every phase that maps to a PS issue.

### Rationale
The detailed mapping lives in `compact_v5/docs/V5_PS_ISSUES_MAPPING.md`. Each entry specifies: root cause, v4.10.10 in-place fix (if any), v5 target phase, v5 acceptance criterion, and "better than v4" delta. Aggregate audit checks that mapped issues are addressed before allowing the next phase.

### Runnable-fidelity impact
**N/A** â€” this is process discipline, not a Runnable port.

### Affected files
- compact_v5/docs/V5_PS_ISSUES_MAPPING.md (new this phase)
- compact_v5/docs/PS_actual_use_problems.md (copied from v4 for reference)
- Per-phase test files (each phase's tests must include the mapped regression)

### Linked port-log rows
None â€” this is process discipline, not a Runnable port.

---

## ADR-004 â€” Reference HTMLs copied to `compact_v5/docs/htmls/`
- Date: 2026-04-30
- Phase ID: 00
- Status: ACCEPTED
- Source: User instruction 2026-04-30 + existing v4 HTMLs in `compact_v4/MAIN/agent/` and `PS_ClaudeCode_Insights/`

### Question 1 â€” Replacement or addition?
- ADDITION (reference HTMLs to support v5 build context). Not a code feature.

### Question 2 â€” Architectural justification (ADDITIONS only)
The user explicitly asked for these as design references during v5 build. They serve as:
- Architectural diagrams users can compare side-by-side (v4 vs Runnable vs LangGraph)
- Visual reference for the deep-dive port discipline (Phase 6, 7, 8 will benefit)
- Future v5 architecture HTMLs (to be generated in Phase 13) will sit alongside, enabling v5-vs-v4-vs-Runnable comparison.

### Question 3 â€” Cost
- Token cost: 0 (HTMLs are not loaded by the agent runtime).
- Repo size: +500 KB (6 HTMLs).
- Code complexity: 0.

### Question 4 â€” Cost worth it?
Yes â€” small repo cost, valuable design reference for building v5.

### Decision
- **ACCEPTED for v5.0**

### Files added (Phase 00)
- compact_v5/docs/htmls/PS_DEEP_DIVE_RUNNABLE.html (Runnable architecture deep-dive)
- compact_v5/docs/htmls/PS_FLOWCHART_RUNNABLE.html (Runnable flowchart)
- compact_v5/docs/htmls/PS_FLOWCHART_V4.html (v4 flowchart, for comparison)
- compact_v5/docs/htmls/PS_RUNNABLE_VS_LANGGRAPH.html (Runnable vs LangGraph comparison)
- compact_v5/docs/htmls/HERMES_VS_CODING_AGENT_v4.html (Hermes vs v4 comparison)
- compact_v5/docs/htmls/v4_architecture.html (v4 architecture HTML)

### Future (Phase 13)
- compact_v5/docs/htmls/v5_architecture.html (NEW â€” generated at Phase 13)
- compact_v5/docs/htmls/PS_FLOWCHART_V5.html (NEW â€” generated at Phase 13)
- compact_v5/docs/htmls/PS_V5_VS_RUNNABLE.html (NEW â€” comparison generated at Phase 13)

### Runnable-fidelity impact
**N/A** â€” these are reference docs, not adopted patterns.

### Linked port-log rows
None.

---

## ADR-005 â€” BedrockClient: REUSE v4 verbatim (Bedrock-native), defer Runnable cache-break detection to Phase 6
- Date: 2026-04-30
- Phase ID: 01
- Status: ACCEPTED
- Source: V5_PLAN.md Phase 1 row + `compact_v4/MAIN/agent/sagemaker_agent.py:2378-2560` (v4 BedrockClient) + `gg-claude-code-runnable/src/services/api/claude.ts` + `services/api/promptCacheBreakDetection.ts`

### Question 1 â€” Replacement or addition?
- Does this REPLACE something v4 already has? **YES** â€” moves v4's `BedrockClient` class from `sagemaker_agent.py:2378` into the dedicated module `compact_v5/MAIN/agent/runtime/bedrock_client.py`. Behavior preserved verbatim.

### Question 2 â€” Architectural justification
N/A â€” replacement, not addition. v4's BedrockClient is already Bedrock-native, has prompt cache fallback, retry classifier, mock mode, thinking mode. Runnable's `claude.ts` is Anthropic-direct (subscriber/OAuth flows), not applicable to Bedrock.

### Question 3 â€” Cost
- Token cost: 0 (runtime client, not in prompt).
- Code complexity: extracts ~180 LOC from v4 monolith into a clean module. No behavior change.
- Maintenance: one place to update Bedrock-specific code.

### Question 4 â€” Cost worth it?
N/A (replacement).

### Decision
- **ACCEPTED for v5.0** â€” verbatim move of v4's `BedrockClient` to `runtime/bedrock_client.py` + minor import adjustments.

### Why NOT port Runnable's `promptCacheBreakDetection.ts` here
Runnable's detection is sophisticated (systemHash + toolsHash + perToolHashes + cacheControlHash + globalCacheStrategy + betas list etc.) and depends on having multi-block system prompt + cache-control state. v5 doesn't have multi-block prompts until Phase 6 lands. Porting now would build a detector against a structure that doesn't exist yet, causing rework.

**DEFER to Phase 6** when `prompt/sections.py` produces multi-block system prompts; the cache-break detector then has real state to compare against.

### Runnable-fidelity impact
N/A for ADR-005 itself (no Runnable code adopted yet). Phase 6 ADR will track the cache-break-detection port.

### Affected files
- compact_v5/MAIN/agent/runtime/bedrock_client.py (new â€” verbatim move from v4)
- compact_v5/MAIN/agent/tests/unit/test_bedrock.py (new â€” mock-mode + thinking-config-on-every-call regression for PS Issue #4)

### Linked port-log rows
None for Phase 1 (no Runnable port in this phase; pure v4 reuse).

---

## ADR-006 â€” Config + JSONC loader: REUSE v4 verbatim
- Date: 2026-04-30
- Phase ID: 01
- Status: ACCEPTED
- Source: `compact_v4/MAIN/agent/sagemaker_agent.py` `Config` class + `_strip_jsonc_comments` helper

### Question 1 â€” Replacement or addition?
- Does this REPLACE something v4 already has? **YES** â€” moves v4 Config to `compact_v5/MAIN/agent/runtime/config.py`.

### Question 2 â€” Architectural justification
N/A â€” verbatim move.

### Question 3 â€” Cost
- Token cost: 0.
- Code complexity: ~300 LOC moves to its own module. Cleaner imports.

### Question 4 â€” Cost worth it?
N/A (replacement).

### Decision
- **ACCEPTED for v5.0** â€” verbatim move with v5-relative path adjustments only.

### Critical fields preserved (sanity check)
- `model_id`, `region`, `workspace`, `temperature`, `max_turns`, `max_iteration_budget=600`, `max_exec_calls_per_session=200`, `aws_bedrock_only`, `enable_prompt_cache=True`, `thinking_enabled`, `thinking_budget`, `session_cost_limit`, `enable_skill_auto_trigger=False` (v4.9.6 default), `enable_skill_patching=False`, `enforce_verify_contract=False`.

### Runnable-fidelity impact
N/A â€” pure v4 reuse.

### Affected files
- compact_v5/MAIN/agent/runtime/config.py (new â€” verbatim move from v4)

### Linked port-log rows
None for Phase 1.

---

## ADR-007 â€” `ToolDef` Python Protocol replaces v4's 4-tuple `TOOLS` dict
- Date: 2026-04-30
- Phase ID: 02
- Status: ACCEPTED
- Source: Runnable `src/Tool.ts` (`Tool` interface + `buildTool` defaults) + v4 `compact_v4/MAIN/agent/sagemaker_agent.py:7105` (`TOOLS = {name: (callable, requires_approval, description, schema)}`)

### Question 1 â€” Replacement or addition?
- **REPLACEMENT.** Replaces v4's monolithic `TOOLS = {...}` 4-tuple dict (`(callable, requires_approval, description, schema)` per entry) with a typed `ToolDef` Protocol. Each tool becomes a small object with named attributes instead of a positional 4-tuple, which silently grew confusing as fields were added.

### Question 2 â€” Architectural justification (ADDITIONS only)
N/A â€” replacement.

### Question 3 â€” Cost
- Token cost (static prompt): **0**. The Protocol is a runtime/type construct, not in the system prompt. The per-tool description text is unchanged from v4.
- Token cost (per turn): **0**. Same as v4.
- Code complexity: ~120 LOC for `tools/registry.py` (Protocol + `build_tool` + `tool_matches_name` + `find_tool_by_name` + `get_tools` + `apply_tool_search_deferral` stub). v4's TOOLS dict is ~600 LOC of 4-tuple entries embedded in the monolith; v5 splits each tool into its own file (ADR-001) so the registry itself stays tiny.
- Maintenance: adding a new tool now requires creating one file + adding one `register()` call. Schemas/descriptions live next to their executors.

### Question 4 â€” Cost worth it?
N/A (replacement; the cost IS reduced complexity).

### Decision
- **ACCEPTED for v5.0** â€” `ToolDef` Protocol with these fields (Runnable parity columns shown):
  - `name` (Runnable: `name`)
  - `aliases` (Runnable: `aliases`) â€” backwards-compat lookup
  - `description` (Runnable: `prompt()`) â€” appears in system prompt block for this tool
  - `input_schema` (Runnable: `inputSchema`) â€” JSON-Schema dict (Python doesn't need Zod; v4 already uses dict-based schemas which Bedrock accepts)
  - `search_hint` (Runnable: `searchHint`) â€” 3-10 word phrase for ToolSearch keyword matching (used in Phase 7)
  - `should_defer` (Runnable: `shouldDefer`) â€” Phase-7 deferred-loading marker
  - `always_load` (Runnable: `alwaysLoad`) â€” never-defer marker
  - `is_read_only` (Runnable: `isReadOnly()`) â€” used for Plan-Mode allowlist + denial classification
  - `is_destructive` (Runnable: `isDestructive()`) â€” surfaced in approval prompt
  - `is_concurrency_safe` (Runnable: `isConcurrencySafe()`) â€” for parallel tool batching
  - `requires_approval` (v4-native; Runnable splits this into `checkPermissions()`) â€” kept v4-style for Bedrock/SageMaker constraint where approval flow is ipywidgets-driven, not a TS permission context
  - `enabled` (Runnable: `isEnabled()`) â€” feature gate
  - `max_result_size_chars` (Runnable: `maxResultSizeChars`) â€” output cap; default 50_000 to match v4 `max_output_chars`
  - `execute(args, context) -> dict` (Runnable: `call(args, context, ...)`) â€” the executor

- Methods that Runnable exposes but v5 OMITS (with reason):
  - All `render*` methods (`renderToolUseMessage`, `renderToolResultMessage`, etc.) â†’ no JSX/Ink in v5; rendering happens in `ui/chat_ui.py` via ipywidgets (Phase 11). Constraint: `.ipynb`.
  - `inputJSONSchema` (MCP-only) â†’ folded into the single `input_schema` field; v5 has no Zod-vs-JSON-Schema split.
  - `interruptBehavior`, `setToolJSX`, `addNotification`, `sendOSNotification` â†’ no REPL/Ink runtime. Constraint: `.ipynb`.
  - `getActivityDescription`, `getToolUseSummary` â†’ ipywidgets shows simpler progress; deferred to Phase 11 if needed.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** â€” constraint = `.ipynb` (no JSX/Ink/React; rendering moved to ipywidgets in Phase 11).
- Up-stream caller: `runtime/bedrock_client.py::chat()` accepts `tools` per-call; same as Runnable `claude.ts` consuming `getTools()`.
- Down-stream wiring: Phase 3-5 tools ship as one file each (ADR-001) and are registered via `register(tool)` calls in `tools/__init__.py`.
- State/cache contract: tool list is sorted by name in `assemble_tool_pool()` to match Runnable's prompt-cache stability requirement (alphabetical ordering, MCP tools as a contiguous suffix).

### Affected files
- compact_v5/MAIN/agent/tools/__init__.py
- compact_v5/MAIN/agent/tools/registry.py
- compact_v5/MAIN/agent/tests/unit/test_registry.py

### Linked port-log rows
- #001 (will be added in this phase): `Runnable Tool.ts â†’ v5 ToolDef Protocol`

---

## ADR-008 â€” Tool registry: `get_tools()` + `apply_tool_search_deferral()` stub + plan-mode subset
- Date: 2026-04-30
- Phase ID: 02
- Status: ACCEPTED
- Source: Runnable `src/tools.ts` (`getAllBaseTools`, `getTools`, `filterToolsByDenyRules`, `assembleToolPool`) + v4 `PLAN_MODE_ALLOWED_TOOLS` set at `compact_v4/MAIN/agent/sagemaker_agent.py:6905`

### Question 1 â€” Replacement or addition?
- **REPLACEMENT.** Replaces v4's inline tool-allowlist filtering logic (which lived inside `Agent.run()` at `compact_v4/MAIN/agent/sagemaker_agent.py:8876` and again at `:9390`) with a single `get_tools(plan_mode=False, deny_rules=None)` entry point. Caller no longer reaches into a global TOOLS dict + global PLAN_MODE_ALLOWED_TOOLS set â€” it asks the registry.

### Question 2 â€” Architectural justification
N/A â€” replacement.

### Question 3 â€” Cost
- Token cost: 0.
- Code complexity: small. `get_tools()` + `assemble_tool_pool()` + `apply_tool_search_deferral()` stub = ~80 LOC.

### Question 4 â€” Cost worth it?
N/A.

### Decision
- **ACCEPTED for v5.0** â€” registry exposes:
  - `register(tool: ToolDef)` â€” Phase 3-5 tools register themselves at module import time.
  - `get_tools(plan_mode=False, deny_rules=None) -> list[ToolDef]` â€” returns the active tool list for the current call. Filters: (1) `enabled` flag, (2) deny rules (Runnable `filterToolsByDenyRules` parity), (3) plan-mode read-only subset (v4 `PLAN_MODE_ALLOWED_TOOLS` parity).
  - `assemble_tool_pool(plan_mode, deny_rules, mcp_tools=None)` â€” Runnable `assembleToolPool` parity; sorts built-ins alphabetically then MCP tools alphabetically (cache-stability invariant from Runnable).
  - `apply_tool_search_deferral(tools, enabled=False) -> tuple[list[ToolDef], ToolDef | None]` â€” **Phase 2 STUB**: when `enabled=False`, returns `(tools, None)`; full deferred-loading logic lands in Phase 7 with `tools/tool_search.py`. Stub exists now so callers can wire to it without churn later.
  - `tool_matches_name(tool, name) -> bool` (Runnable parity)
  - `find_tool_by_name(tools, name) -> ToolDef | None` (Runnable parity)
- **Plan-mode subset** is hardcoded to v4's `PLAN_MODE_ALLOWED_TOOLS` set (`{read_file, glob, grep, list_dir, semantic_search, todo_write, todo_read, view_image, skill, web_fetch, ask_user}`). When a tool with that name is registered, plan mode lets it through; otherwise it's filtered out.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** â€” constraint = `none` for the registry shape itself, BUT:
- Runnable's `permissionContext` (a complex `DeepImmutable` of allow/deny/ask rules + plan-mode + bypass mode + MCP server-prefix rules) is REPLACED with a simpler `(plan_mode: bool, deny_rules: set[str] | None)` pair.
- Justification: Runnable's permission context exists because the Anthropic-direct CLI has multi-source rules (user config, project config, settings, MCP server scopes). v5's Bedrock-only `.ipynb` has none of those sources â€” approval is a single ipywidgets prompt per call. Constraint = **`.ipynb`** (single approval source).
- Up-stream caller: Phase 8's `core/query_engine.py` calls `get_tools(plan_mode=ctx.plan_mode)` per turn (mirrors Runnable's `claude.ts` calling `getTools(permissionContext)` per request).
- Down-stream wiring: tools' `requires_approval` flag drives the ipywidgets approval prompt; v5 does NOT call Runnable's `checkPermissions()` (which returns a structured `PermissionResult`) because there's no permission context to check against. Instead, `requires_approval=True` triggers the user prompt directly. Documented as a v4-native ADAPT, not drift.
- Error contract: tool execution errors propagate as raised exceptions; `core/query_engine.py` (Phase 8) maps to `tool_result` blocks. Runnable's pattern is identical.

Auto-reject avoidance: constraint is **`.ipynb`** (not `none`), so this is a legitimate `FAITHFUL-WITH-JUSTIFIED-ADAPTATION` â€” the simpler permission-context tuple is forced by the .ipynb single-source approval flow.

### Affected files
- compact_v5/MAIN/agent/tools/registry.py (the registry implementation)
- compact_v5/MAIN/agent/tools/__init__.py (re-exports + future tool registrations)
- compact_v5/MAIN/agent/tests/unit/test_registry.py

### Linked port-log rows
- #001 (this phase): `Runnable Tool.ts â†’ v5 ToolDef Protocol`
- #002 (this phase): `Runnable tools.ts (getAllBaseTools, getTools, filterToolsByDenyRules, assembleToolPool) â†’ v5 tools/registry.py`

---

## ADR-009 â€” Phase 3 read-only tools: REUSE v4 executors + ADAPT Runnable prompt text + thin path-validation stub
- Date: 2026-04-30
- Phase ID: 03
- Status: ACCEPTED
- Source:
  - v4: `compact_v4/MAIN/agent/sagemaker_agent.py:4258` (`tool_read_file`), `:4846` (`tool_glob`), `:4897` (`tool_grep`), `:4952` (`tool_list_dir`)
  - Runnable: `gg-claude-code-runnable/src/tools/FileReadTool/prompt.ts`, `GrepTool/prompt.ts`, `GlobTool/prompt.ts`
  - v4 security: `compact_v4/MAIN/agent/sagemaker_agent.py` `SecurityManager.validate_path` (full port deferred to Phase 5)

### Question 1 â€” Replacement or addition?
- **REPLACEMENT.** Replaces v4's monolithic tool functions (which live inside `sagemaker_agent.py` and are referenced by the v4 `TOOLS` dict 4-tuple at `:7105`) with file-per-tool modules under `compact_v5/MAIN/agent/tools/` (per ADR-001).

### Question 2 â€” Architectural justification (ADDITIONS only)
N/A â€” replacement. Notes on the structural value:
- Per ADR-001 file-per-tool, each of the 4 tools becomes its own module that calls `register(build_tool(...))` at import time.
- v4's executor function bodies are battle-tested Python; rewriting from Runnable's TS would lose features Runnable doesn't have (FILE_CACHE, FILE_UNCHANGED_STUB, large-file guard, .ipynb cell parsing, mtime tracking, allowed_paths fallback for glob, binary-file skip for grep).
- Runnable's prompt text (the description shown to the model) is more directive on WHEN / WHEN NOT â€” addresses PS Issue #7 (buried-matrix failure). The text gets adapted: tool-name strings change (Runnable `Read` â†’ v5 `read_file`, etc.), and the v5 ipynb constraint means we don't reference Ink/JSX.

### Question 3 â€” Cost
- Token cost (per turn â€” schema + description in initial prompt): each of 4 tools contributes ~120-200 tokens of description + ~50 tokens of schema. Total Phase 3 contribution to per-turn overhead: ~700-1000 tokens. This is BEFORE Phase 7's ToolSearchTool deferral; after Phase 7, low-frequency tools get deferred and the per-turn overhead drops.
- Static prompt cost: 0 (tools are not in the system prompt; their descriptions are in the per-turn `tools` block).
- Code complexity: 4 small tool modules (~80-150 LOC each) + 1 thin path-validation helper (~50 LOC). Total ~500 LOC of new code. Compared to v4's ~700 LOC of monolithic tool functions, similar size but split for reviewability.
- Maintenance: each tool now has a single owner-file. Bug fixes touch one module, not the v4 monolith.

### Question 4 â€” Cost worth it?
N/A (replacement; the cost is dispersed but reviewability improves).

### Decision
- **ACCEPTED for v5.0** â€” 4 read-only tools land Phase 3:
  - `tools/read_file.py` â€” REUSE v4 executor + ADAPT Runnable prompt text (renamed from `Read` to `read_file`).
  - `tools/grep.py` â€” REUSE v4 executor + ADAPT Runnable prompt text. **Critical correction**: Runnable's prompt says "built on ripgrep" but v4 uses Python `re`. v5 prompt says "regex search across files" (truthful). PS Issue #6 (wiring-bug pattern) lock â€” don't claim a backend we don't have.
  - `tools/glob.py` â€” REUSE v4 executor + ADAPT Runnable prompt text.
  - `tools/list_dir.py` â€” REUSE v4 verbatim. **No Runnable analog** (Runnable tells the model to use `ls` via Bash). v5 keeps the dedicated tool because v4 has it; in plan mode the user can't bash, so list_dir is essential. No Runnable port row â€” pure v4 reuse.
- Each tool flagged: `is_read_only=True`, `is_concurrency_safe=True` (Runnable parity â€” read-only ops are safe in parallel), `requires_approval=False`.

### Path-validation strategy (Phase 3 stub vs Phase 5 full)
- v4's `SecurityManager.validate_path` does (a) workspace boundary check, (b) allowed_paths fallback, (c) symlink escape detection. The full module also has 134-case destructive command coverage which is irrelevant for read-only tools.
- **Phase 3 ships a minimal `tools/_path_validation.py`** with just the path-resolution + boundary check (the parts read-only tools need). ~50 LOC.
- **Phase 5 replaces** this stub with the full `security/` package port from v4 (verbatim). The 4 tool modules will then import from `security.manager` instead of `tools._path_validation`.
- This split is necessary because Phase 5 is where `security/` lands per the locked phase plan; we can't depend on it from Phase 3.
- The Phase 5 ADR will note the `_path_validation.py` retirement and verify the same security contract is preserved.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** â€” constraint = `Bedrock | python_exec | .ipynb`:
- Bedrock: tool descriptions ship as JSON `description` fields in the `tools` body block; same as Runnable's API call.
- python_exec: v5 has no Node fs API access; the executor body is pure Python (v4 reuse).
- .ipynb: no JSX/Ink rendering; ipywidgets handles UI in Phase 11.
- The `ripgrep` correction is a forced fidelity-improvement: v5's grep tool truthfully describes its backend (`re` module), avoiding a Runnable-text claim that doesn't match implementation. PS Issue #6 (wiring bug) prevention.

### Affected files
- compact_v5/MAIN/agent/tools/_path_validation.py (new, Phase-3-only stub)
- compact_v5/MAIN/agent/tools/read_file.py (new)
- compact_v5/MAIN/agent/tools/grep.py (new)
- compact_v5/MAIN/agent/tools/glob.py (new)
- compact_v5/MAIN/agent/tools/list_dir.py (new)
- compact_v5/MAIN/agent/tools/__init__.py (add 4 import lines so registration fires)
- compact_v5/MAIN/agent/tests/tools/test_read_file.py (new)
- compact_v5/MAIN/agent/tests/tools/test_grep.py (new)
- compact_v5/MAIN/agent/tests/tools/test_glob.py (new)
- compact_v5/MAIN/agent/tests/tools/test_list_dir.py (new)

### Linked port-log rows
- #003 â€” Runnable FileReadTool/prompt.ts â†’ v5 tools/read_file.py
- #004 â€” Runnable GrepTool/prompt.ts â†’ v5 tools/grep.py (with ripgrepâ†’regex correction)
- #005 â€” Runnable GlobTool/prompt.ts â†’ v5 tools/glob.py
- (#006 NOT created â€” list_dir has no Runnable analog; pure v4 reuse documented inline)

---

## ADR-010 â€” Phase 4 mutating tools: REUSE v4 executors + ADAPT Runnable prompts + diff_widget UI
- Date: 2026-04-30
- Phase ID: 04
- Status: ACCEPTED
- Source:
  - v4: `compact_v4/MAIN/agent/sagemaker_agent.py:4632` (`tool_write_file`), `:4729` (`tool_edit_file`), `:5921` (`tool_notebook_edit`), `:6419` (`tool_view_image`)
  - Runnable: `gg-claude-code-runnable/src/tools/FileWriteTool/prompt.ts`, `FileEditTool/prompt.ts`, `NotebookEditTool/prompt.ts`, `FileEditTool/UI.tsx` (diff-preview React component pattern)
  - V5_PLAN.md Phase 4 acceptance criterion: edit_file, write_file, AND notebook_edit approval prompts each show colored before/after diff inline (red removed, green added, gray context) with file path header + line numbers + Â±3 lines context + click-to-expand-full-file using `ui/diff_widget.py` BEFORE user clicks Approve.

### Question 1 â€” Replacement or addition?
- **REPLACEMENT** for the 4 tool executors (v4 monolith â†’ file-per-tool modules per ADR-001).
- **ADDITION** for `ui/diff_widget.py` â€” the UX pattern is novel to v5 (v4 didn't show colored inline diffs in the approval prompt; user only saw a text summary). Adopted from Runnable's `EditTool/UI.tsx` Ink renderer pattern.

### Question 2 â€” Architectural justification (ADDITIONS only)
**Why diff_widget.py:** PS_actual_use_problems.md captures a real pattern where v4 users approved edits without seeing the actual change content, then discovered later that the model had edited the wrong region or stripped useful code. Showing the colored diff inline (with Â±3 lines context) lets the user catch misplaced edits BEFORE clicking Approve. Runnable solved this with `EditTool/UI.tsx` (Ink JSX). v5 ipywidgets equivalent: an HTML widget with `+` green / `-` red / context gray + a `<details>` block for click-to-expand-full-file.
- **User-visible improvement**: misplaced-edit prevention. A model that does `edit_file(file_path="auth.py", old_string="def login():\n    return user", new_string="def login():\n    return user.is_admin")` shows the change in context, so the user spots `is_admin` permissions creep before approving.
- **Not acceptable as ADDITION justification**: "matches Runnable" / "completes the parity". Both are insufficient.
- **Acceptable**: catches a documented v4 failure mode (silent misplaced edits).

### Question 3 â€” Cost
- Token cost (static prompt): 0 (the diff widget is a Python class that returns HTML; not in the system prompt).
- Token cost (per turn): 0 (UI rendering happens client-side in ipywidgets; no model interaction).
- Code complexity: ~150 LOC `ui/diff_widget.py` (uses stdlib `difflib.unified_diff` + simple HTML escape + `<details>` markup). No new dependencies (`ipywidgets` already used by v4 chat.ipynb; only HTML strings emitted in Phase 4).
- Maintenance: one file to update if Runnable changes diff conventions or if user complains about the rendering.

### Question 4 â€” Cost worth it?
**Yes**. Misplaced-edit prevention is exactly the kind of user-visible improvement V5_PLAN.md's "addition gate" requires. The cost (~150 LOC + 0 tokens) is negligible vs the value (catches a documented v4 failure mode at approval time, before the bad edit lands).

### Decision
- **ACCEPTED for v5.0** â€” 4 mutating tools + 1 ui module land Phase 4:
  - `tools/write_file.py` â€” REUSE v4 executor + ADAPT Runnable prompt text. Requires `read_before_overwrite` (matches v4 contract). `requires_approval=True`.
  - `tools/edit_file.py` â€” REUSE v4 executor + ADAPT Runnable prompt text. Requires `read_first` (matches v4 contract). Exact match + `replace_all` flag. `requires_approval=True`.
  - `tools/notebook_edit.py` â€” REUSE v4 executor (insert/replace/delete cells). Atomic write (tmp file + rename) preserved. `requires_approval=True`.
  - `tools/view_image.py` â€” REUSE v4 executor; Phase 4 returns metadata, the pending-images queue is Phase-8 concern.
  - `ui/diff_widget.py` â€” generates HTML diff strings (red removed, green added, gray context, file path header, Â±3 lines context, `<details>`-wrapped full-file expansion). Phase 11 wires into the ipywidgets approval flow.

### Phase-3-stub dependencies and Phase-5 retirement
- Like Phase 3, mutating tools depend on `tools/_path_validation.py` (Phase-3 stub) and a new `tools/_file_read_tracking.py` (replaces v4's `_FILES_READ` set + `_FILE_READ_TIMES` map). Both stubs are retired in Phase 5 when the full security/ + a Phase-8-friendly read-tracking module land.
- v4-specific deferred features (snapshot-before-edit / auto-lint-python / auto-commit-checkpoint / secrets-scan) are NOT ported in Phase 4 â€” they belong to Phase 5 (security) + Phase 8 (query_engine session machinery). Documented inline in each tool module.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** â€” constraint = `.ipynb` + Bedrock + python_exec:
- Drops React/Ink rendering methods (renderToolUseMessage etc.) â€” same as Phase 2 ToolDef Protocol decision.
- `ui/diff_widget.py` renders HTML for ipywidgets, not Ink JSX. Same UX semantics: colored diff, file header, click-to-expand. Constraint = `.ipynb`.
- Tool naming: Runnable `Edit`/`Write`/`NotebookEdit` â†’ v5 `edit_file`/`write_file`/`notebook_edit` (v4 parity).

### Affected files
- compact_v5/MAIN/agent/tools/_file_read_tracking.py (new, Phase-4-only stub)
- compact_v5/MAIN/agent/tools/write_file.py (new)
- compact_v5/MAIN/agent/tools/edit_file.py (new)
- compact_v5/MAIN/agent/tools/notebook_edit.py (new)
- compact_v5/MAIN/agent/tools/view_image.py (new)
- compact_v5/MAIN/agent/ui/diff_widget.py (new)
- compact_v5/MAIN/agent/tools/__init__.py (extend bootstrap_built_ins)
- compact_v5/MAIN/agent/tests/tools/test_phase4_mutating_tools.py (new)
- compact_v5/MAIN/agent/tests/unit/test_diff_widget.py (new)

### Linked port-log rows
- #006 â€” Runnable FileWriteTool/prompt.ts â†’ tools/write_file.py
- #007 â€” Runnable FileEditTool/prompt.ts â†’ tools/edit_file.py
- #008 â€” Runnable NotebookEditTool/prompt.ts â†’ tools/notebook_edit.py
- #009 â€” Runnable FileEditTool/UI.tsx (diff-preview pattern) â†’ ui/diff_widget.py
- (No row for view_image â€” Runnable's FileReadTool handles images inline; v5 keeps the dedicated tool for v4 parity. Documented inline in tools/view_image.py.)

---

## ADR-011 â€” Phase 5 security/ + bash + python_exec: REUSE v4 verbatim, retire `_path_validation` stub
- Date: 2026-04-30
- Phase ID: 05
- Status: ACCEPTED
- Source:
  - v4 `compact_v4/MAIN/agent/sagemaker_agent.py:1298-2148` (`SecurityManager` class â€” ~850 LOC, including SECRET_PATTERNS, SENSITIVE_FILES, CATASTROPHIC_PATTERNS, DANGEROUS_PATTERNS (70+ regex), DANGEROUS_PYTHON (~70 regex), ALLOWED_PYTHON_MODULES, BLOCKED_PYTHON_MODULES, BLOCKED_PYTHON_MEMBERS, validate_path, validate_command, validate_python, scan_secrets, truncate_output)
  - v4 `:756-861` (`Truncation` class â€” used by `SECURITY.truncate_output`)
  - v4 `:5239` (`tool_bash`), `:5409` (`tool_python_exec`)
  - v4 `:4988-5160` (helpers: `_safe_exec_env`, `_run_subprocess`, `_validate_shell_redirections`, `_docker_base_cmd`, `_ensure_docker_image_ready`, `_kill_active_process`)
  - v4 `:10487` (`HIGH_RISK_TOOLS = {"bash", "python_exec", "task", "web_fetch"}` â€” used by approval-prompt UX)
  - v4 `:2107-2138` (`_auto_detect_allowed_paths` â€” SageMaker root + git repo root auto-detection)
  - v4 `:4212` (`_resolve_path` helper)
  - Runnable: `gg-claude-code-runnable/src/tools/BashTool/prompt.ts` (description text only â€” Runnable's executor is unrelated TypeScript shell logic)

### Question 1 â€” Replacement or addition?
- **REPLACEMENT** for the security module + bash + python_exec executors. Replaces the v4 monolith inline definitions.
- **ADDITION** for the package boundary itself (security/ as its own importable package). v4 had everything inline in `sagemaker_agent.py`.

### Question 2 â€” Architectural justification (ADDITIONS only)
**Why a security/ package boundary:** v4's SecurityManager + dangerous-pattern lists + helpers were ~1000 LOC of security-critical code interleaved with everything else in the monolith. The security review requires reading these as a unit, but in v4 they were scattered. v5 isolates them into `security/` so:
- A future security audit can scan one package, not the whole monolith.
- Phase 3-4 tools that already use `validate_path` switch from the Phase-3 stub to the production module via a one-line import change (the stub becomes a delegating shim for backwards compatibility).
- Adding new dangerous patterns is a bounded edit to one file (`dangerous_patterns.py` or `dangerous_python.py`), not a search-and-add across a monolith.
- Tests can target the security boundary without spinning up the entire agent runtime.

### Question 3 â€” Cost
- Token cost (static prompt): 0 (security/ is runtime code, not in the prompt).
- Token cost (per turn): 0 (bash + python_exec descriptions ship per turn; size is comparable to v4's text).
- Code complexity: ~1100 LOC across 5 security files + 2 tool modules + 1 retired stub. v4 had ~1000 LOC inline. Net: ~10% more LOC for the package boundary, but every file has a single clear responsibility.
- Maintenance: regex patterns concentrate in 2 files; SecurityManager class gets the policy logic; helpers get the subprocess + redirection plumbing. Adding a new pattern is grep + edit one file.

### Question 4 â€” Cost worth it?
**Yes.** The 134-case destructive-command coverage is the single largest security control v5 inherits from v4. Isolating it improves auditability. The architectural separation also makes the Phase 5 acceptance criterion ("134-case coverage from v4 still passes") mechanically verifiable.

### Decision
- **ACCEPTED for v5.0** â€” Phase 5 lands the following files, all REUSE v4 verbatim with v5-compatible imports:
  - `compact_v5/MAIN/agent/security/__init__.py` â€” package init exposing `SECURITY` singleton + helper re-exports.
  - `compact_v5/MAIN/agent/security/manager.py` â€” `SecurityManager` class verbatim + SECRET_PATTERNS + SENSITIVE_FILES + helper functions (`_resolve_path`, `_safe_exec_env`, `_run_subprocess`, `_validate_shell_redirections`, `_docker_base_cmd`, `_ensure_docker_image_ready`, `_kill_active_process`, `_auto_detect_allowed_paths`).
  - `compact_v5/MAIN/agent/security/dangerous_patterns.py` â€” CATASTROPHIC_PATTERNS + DANGEROUS_PATTERNS + NETWORK_COMMANDS + BASE_ALLOWED_COMMANDS + INTERPRETER_COMMANDS + CONTAINER_COMMANDS.
  - `compact_v5/MAIN/agent/security/dangerous_python.py` â€” DANGEROUS_PYTHON + ALLOWED_PYTHON_MODULES + BLOCKED_PYTHON_MODULES + BLOCKED_PYTHON_MEMBERS + ALLOWED_AWS_HINT.
  - `compact_v5/MAIN/agent/security/high_risk.py` â€” HIGH_RISK_TOOLS frozenset + `is_high_risk(name)` helper.
  - `compact_v5/MAIN/agent/runtime/truncation.py` â€” Truncation class verbatim.
  - `compact_v5/MAIN/agent/tools/bash.py` â€” verbatim port of v4 `tool_bash` + ADAPT Runnable `BashTool/prompt.ts` description.
  - `compact_v5/MAIN/agent/tools/python_exec.py` â€” verbatim port of v4 `tool_python_exec` + v5-native description (no Runnable analog â€” Runnable uses Bash for Python).

### `_path_validation.py` retirement
- Phase 3 shipped `tools/_path_validation.py` as an ~80-LOC stub.
- Phase 5 converts it into a **thin delegating shim**: `validate_path` and `resolve_path` forward to `security.manager.SECURITY.validate_path` and `security.manager._resolve_path`.
- All 8 existing Phase 3-4 tool modules keep their `from . import _path_validation as path_security` imports unchanged.
- The shim documents the delegation inline so a future reader knows where the real implementation lives.
- This avoids touching 8 tool modules in this phase. Phase 13 can decide whether to remove the shim entirely (and update the 8 imports to point at `security.manager` directly) or keep the indirection forever.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** â€” constraints = `Bedrock` + `python_exec` + `.ipynb`:
- Bedrock-only mode (`CONFIG.aws_bedrock_only`) blocks all AWS clients except `bedrock-runtime`. Runnable uses Anthropic API directly â€” no AWS client to block. v5's Bedrock-only check is uniquely v5/v4.
- `python_exec` is v5/v4-specific: a sandboxed Python execution tool with allowlist-based AST validation, runtime closure-based import hook, and workspace-scoped file IO. Runnable doesn't have this â€” it tells the model to use Bash for Python. v5/v4 keep `python_exec` because plan-mode forbids bash AND because the closure sandbox is significantly more restrictive than spawning a generic shell.
- `.ipynb` constraint forces no Ink/JSX in the bash/python_exec UI â€” text output flows back through the existing approval prompt.

### Affected files
- compact_v5/MAIN/agent/security/__init__.py (new)
- compact_v5/MAIN/agent/security/manager.py (new â€” verbatim port)
- compact_v5/MAIN/agent/security/dangerous_patterns.py (new â€” verbatim constants)
- compact_v5/MAIN/agent/security/dangerous_python.py (new â€” verbatim constants)
- compact_v5/MAIN/agent/security/high_risk.py (new)
- compact_v5/MAIN/agent/runtime/truncation.py (new â€” verbatim port of Truncation class)
- compact_v5/MAIN/agent/tools/bash.py (new)
- compact_v5/MAIN/agent/tools/python_exec.py (new)
- compact_v5/MAIN/agent/tools/_path_validation.py (modified â€” converted to delegating shim)
- compact_v5/MAIN/agent/tools/__init__.py (extended bootstrap_built_ins)
- compact_v5/MAIN/agent/tests/unit/test_security_manager.py (new)
- compact_v5/MAIN/agent/tests/tools/test_phase5_bash_python.py (new)

### Intentional deviation from v4 in `python_exec` invocation
- **v4** (`compact_v4/MAIN/agent/sagemaker_agent.py:5433`): `[sys.executable, temp_path]` â€” runs Python with the user's site-packages reachable.
- **v5 Phase 5**: `[sys.executable, "-I", temp_path]` â€” adds the `-I` (isolated mode) flag. This prevents the user's pip cache, PYTHONPATH, and `~/.pythonrc` from leaking into the sandboxed code. The closure-based runtime sandbox still enforces the import allowlist; `-I` just hardens the boundary so `sys.path` doesn't include `~/.local/lib/...` packages the agent never declared.
- **Codex Phase-05 review finding 4**: flagged this as a non-verbatim deviation. Documented here as intentional hardening; locked by `test_python_exec_uses_isolated_mode` so a future refactor cannot silently drop the flag.
- **Why this is "better than v4"**: a malicious package installed in the user's home (e.g., a typo-squatted dep) cannot be imported by the sandbox even if the user's environment has it. The `-I` mode is a small additional defense-in-depth layer.

### Linked port-log rows
- #010 â€” Runnable BashTool/prompt.ts â†’ tools/bash.py:_DESCRIPTION (executor body is v4 port; ADAPT for description text only)
- (No row for python_exec â€” no Runnable analog. Documented inline in tools/python_exec.py.)
- (No rows for security/ files â€” pure v4 reuse, no Runnable adoption.)

---

## ADR-012 â€” Phase 6 sectioned prompt: file-per-section + token budget + cache-boundary
- Date: 2026-04-30
- Phase ID: 06
- Status: ACCEPTED
- Source:
  - v4 `compact_v4/MAIN/agent/sagemaker_agent.py:8029-8178` (`SYSTEM_PROMPT` 914-LOC f-string with embedded `# === DYNAMIC ===` boundary)
  - v4 `:6899` (`PLAN_MODE_PROMPT`)
  - Runnable: `gg-claude-code-runnable/src/constants/prompts.ts` (914 LOC) + `constants/systemPromptSections.ts` (registry pattern with memoization + cache-break detection)
  - V5_PLAN.md Phase 6 acceptance: static prompt â‰¤ 2500 tokens (vs v4's ~5000); cache-boundary test passes.
  - PS_actual_use_problems.md Issue #7: v4's "Tool capability classes" section was buried mid-list in a 5000-token prompt. Under cognitive load (40-call exec limit hit) the model under-attended to it, concluded "all tools blocked", refused to keep working. Phase 6 is the structural fix.

### Question 1 â€” Replacement or addition?
- **REPLACEMENT** of v4's monolithic 914-LOC `SYSTEM_PROMPT` f-string with file-per-section `prompt/*.md` files + `prompt/sections.py` registry + `core/cache.py` cache-block builder.

### Question 2 â€” Architectural justification
The PS Issue #7 root cause: v4 grew the system prompt by *appending* â€” every Hermes pattern, Runnable adoption, Learning_Factory pattern, and v4-original addition was concatenated to the f-string. Reviewers signed off on each individual addition; nobody reviewed the aggregate. The result was a flat 914-LOC bullet list where the LLM under-attended to mid-list bullets under cognitive load.

The structural fix:
1. **One section per file** so reviewers see a bounded unit. Adding new content requires creating a new file (mechanically reviewed) instead of appending to an unreviewable monolith.
2. **Token budget per section**, hard-capped in the registry. Ship-gate (`tests/aggregate_audit.py`) fails if any section exceeds its cap or if the sum exceeds 2500.
3. **Promotion of "Tool capability classes" to top-level**: under cognitive load the LLM attends to the *first* sections more than the middle. v4 buried the matrix at section 3-of-20; v5 promotes it to section 2 (right after identity).
4. **Cache-boundary marker** (`_CACHE_BOUNDARY` section) explicitly separates the static (cached) part from the dynamic per-turn part. Phase 1's BedrockClient already splits at `# === DYNAMIC ===` as a string marker; Phase 6 makes this a structural boundary in the section registry.

### Question 3 â€” Cost
- Token cost (static prompt): TARGET REDUCTION from v4's ~5000 to â‰¤2500. Each section gets a hard cap; sum is enforced by the audit gate.
- Token cost (per turn): same as v4 (sections are static; per-turn content is the dynamic block + tools list + messages).
- Code complexity: 19-20 small `.md` files (most â‰¤1KB each) + `prompt/sections.py` (~150 LOC) + `prompt/__init__.py` (~50 LOC) + `core/cache.py` (~200 LOC). Replacement of v4's 914-LOC f-string. Net: similar LOC, drastically better reviewability.
- Maintenance: editing a section is `read_file â†’ edit_file` of one .md. Adding a section requires creating a file + adding one line to the registry.

### Question 4 â€” Cost worth it?
**Yes** â€” this is the load-bearing architectural fix that motivated v5. Skipping it leaves v5 with v4's failure mode.

### Decision
- **ACCEPTED for v5.0** â€” 19 prompt/*.md sections + registry + cache module land Phase 6.

### Section list (FINAL â€” locked at this ADR; future additions require a new ADR)

**Static section group (cached prefix)** â€” 17 sections:

| # | Section file | Token cap | Purpose |
|---|---|---|---|
| 1 | `identity.md` | 80 | "You are SageMaker Coding Agentâ€¦" |
| 2 | `tool_classes.md` | **350** | Tool capability classes â€” PROMOTED to slot 2 (PS Issue #7 fix). Lists session-limited (bash/python_exec) vs unlimited tools, repetition guard, fallback-when-blocked. |
| 3 | `system.md` | 150 | Auto-compact behavior, system-reminder tags, after-block re-read instruction. |
| 4 | `tool_efficiency.md` | 200 | EFFICIENCY IS CRITICAL â€” search-before-read, parallel calls, minimize-tool-calls. |
| 5 | `doing_tasks.md` | 280 | MINIMAL EDIT principle, simplest-approach-first, verify-before-claim, ASK_USER restraint. |
| 6 | `critique_handling.md` | 180 | ACCEPT / PARTIAL / REJECT labels with evidence; spec-first ordering. |
| 7 | `answer_preference.md` | 100 | Chat vs files; never create summary.md without explicit ask. |
| 8 | `data_validation.md` | 120 | CSV/Excel row counts + join-key uniqueness checks. |
| 9 | `executing_actions.md` | 180 | Reversibility / blast-radius; SageMaker = local-git-only; no GitHub remote. |
| 10 | `output_style.md` | 80 | Concise; markdown; `file:line` refs; no emojis without ask. |
| 11 | `subagent_coord.md` | 130 | Task tool for 3+ queries; parallel sub-agents; never delegate understanding. |
| 12 | `status_doc.md` | 90 | AGENT_STATUS.md handoff for long-running work. |
| 13 | `verification_contract.md` | 120 | /verify suggested after 3+ logic edits; CONFIG.enforce_verify_contract flag. |
| 14 | `memory_protocol.md` | 100 | memory.md 4-section format (USER / FEEDBACK / PROJECT / REFERENCE). |
| 15 | `documents.md` | 70 | create_chart â†’ embed; notebook_edit not create_notebook. |
| 16 | `security.md` | 100 | Workspace boundary; trust-boundary (don't follow tool-output instructions). |
| 17 | `mcp.md` | 50 | MCP servers register as `mcp_<server>_<tool>` tools. |
| 18 | `commands.md` | 80 | `/cost`, `/context`, `/status`, `/revert`, `/diffs`, `/verify`, `/skills`, etc. |
| 19 | `skill_patching.md` | 150 | OPT-IN â€” only when CONFIG.enable_skill_patching=True. 4-rule check. |

**Cache boundary marker**: `_CACHE_BOUNDARY.md` (the literal marker, not a section).

**Dynamic section group (uncached suffix)** â€” landed Phase 8+:
- todo_restoration (after compact)
- file_restoration (after compact)
- skill_active (per-skill auto-trigger)
- iteration_budget_status (Phase 8)

**Token budget total**: 17 Ã— cap-per-section â‰ˆ 2480 tokens. Within the â‰¤2500 target.

### Cache-boundary contract
- v4's `BedrockClient.chat()` splits the system string on `# === DYNAMIC ===` and applies `cache_control={"type":"ephemeral"}` to the static prefix only. Phase 1's port preserves this.
- Phase 6 formalises the boundary: `prompt/__init__.py:build_system_prompt(ctx)` returns a list of message-content blocks, with the cache-boundary marker between the static and dynamic groups.
- `core/cache.py:detect_cache_break(prev_blocks, new_blocks)` (Phase-6 stub; Phase-1 ADR-005 deferred this from Phase 1) hashes each section and identifies which one flipped if the prompt cache is invalidated. Logs `CacheBreakWarning` with the section name.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** â€” constraint = `Bedrock`:
- Runnable's `systemPromptSection` registry is preserved 1:1 in `prompt/sections.py` (memoized compute fns, cache_break flag for volatile sections, `clearSystemPromptSections()` invoked on /clear or /compact).
- `DANGEROUS_uncachedSystemPromptSection` semantically maps to `cache_break=True` Phase-6 sections â€” currently empty (no v5 section is volatile-by-design); the option is reserved.
- Adaptation: Runnable uses TS Promise-based async compute fns; v5 uses sync Python functions because all current sections are static-string returns. If a future section needs async (e.g., reading a remote skill registry), Phase 8+ ADR can lift to async.
- v5 sections are STATIC `.md` FILES, not TS function returns. Justified because: (a) auditing is grep-friendly, (b) no v5 section currently needs runtime computation, (c) per-section token caps are mechanically enforceable on text files. Constraint = `Bedrock` (Bedrock prompt cache rewards static byte-stable prefixes; runtime function returns add a hashing step).

### Affected files
- compact_v5/MAIN/agent/prompt/__init__.py (new)
- compact_v5/MAIN/agent/prompt/sections.py (new)
- compact_v5/MAIN/agent/prompt/*.md (19 new files)
- compact_v5/MAIN/agent/core/__init__.py (new â€” package marker)
- compact_v5/MAIN/agent/core/cache.py (new)
- compact_v5/MAIN/agent/tests/unit/test_prompt_assembly.py (new)
- compact_v5/MAIN/agent/tests/unit/test_cache.py (new)

### Linked port-log rows
- #011 â€” Runnable `constants/systemPromptSections.ts` (registry pattern + memoization + cacheBreak flag) â†’ `prompt/sections.py`
- #012 â€” Runnable `constants/prompts.ts` (914-LOC f-string structure inspired the sectioning; v5 content is REWRITTEN per ADR-002 file-per-section, not ported verbatim) â†’ 19 prompt/*.md files
- #013 â€” Runnable `services/api/promptCacheBreakDetection.ts` (cache-break detection: hash sections, identify which one flipped) â†’ `core/cache.py:detect_cache_break()`

### PS Issue mapping
- **PS Issue #7 â€” buried-matrix failure mode** (the root cause that motivated v5):
  - Root cause: in v4's flat 914-LOC SYSTEM_PROMPT, "Tool capability classes" was the third major section (after "System" and ahead of "Using Tools"); under cognitive load the LLM under-attended.
  - Phase 6 structural fix: tool_classes.md is **slot 2** (right after identity, before "system"). Each section file has a hard token cap so no single section can grow back to a 914-LOC dump.
  - Verification: cognitive-load test (Codex-evaluated, run as part of the audit gate before Phase 7) â€” Codex simulates the LLM receiving "Blocked: bash + python_exec limit reached (200/session)" and checks whether the prompt structure leads it to continue with read_file/grep/edit_file rather than "all tools blocked".

---

## ADR-013 â€” Phase 7 ToolSearchTool deferred loading (highest-leverage Runnable port)
- Date: 2026-04-30
- Phase ID: 07
- Status: ACCEPTED
- Source:
  - Runnable: `gg-claude-code-runnable/src/tools/ToolSearchTool/ToolSearchTool.ts` (471 LOC) + `prompt.ts` (121 LOC) + `constants.ts`
  - Runnable: `gg-claude-code-runnable/src/utils/toolSearch.ts` (deferred-tool placement logic)
  - V5_PLAN.md Phase 7 acceptance: per-turn schema overhead drops â‰¥3000 tokens vs Phase 6 baseline
  - Phase 2 ADR-008 stub: `tools/registry.py:apply_tool_search_deferral` returns `(tools, None)` when `enabled=False`. Phase 7 replaces with the real implementation.

### Question 1 â€” Replacement or addition?
- **Both.**
- **REPLACEMENT** of the Phase-2 `apply_tool_search_deferral` stub with the real deferred-loading logic.
- **ADDITION** of `tools/tool_search.py` (a new tool exposed to the model).

### Question 2 â€” Architectural justification (ADDITIONS only)
**Why tool_search.py:** the v4 system loads every tool's full JSON schema on every turn. With 30 tools that's ~5000-8000 tokens of schema in EVERY message â€” pure overhead since the model uses ~3-5 tools per turn. Runnable's deferred-loading pattern: low-frequency tool schemas are NOT in the initial prompt; instead, only their NAMES appear in a `<system-reminder>`. When the model needs one, it calls `tool_search("name")` which returns the full schema in a `<functions>` block, after which the tool is callable like any other.

This is the **single highest-leverage token-saving Runnable adoption** in v5 â€” V5_PLAN.md targets â‰¥3000 tokens/turn savings.

User-visible improvement: faster turns, lower per-turn cost, higher effective context window for actual work.

### Question 3 â€” Cost
- Token cost (static prompt): 0 (tool_search description is in the per-turn tools block, not the static prompt).
- Token cost (per turn â€” schema overhead): the tool_search tool itself adds ~300 tokens (schema). Deferred tools' names appear in a system-reminder (~10 tokens each). Their FULL schemas (~300-500 tokens each) only appear when the model fetches them.
  - **Baseline (Phase 6)**: 10 tools Ã— ~400 token average schema = ~4000 tokens/turn.
  - **Post-Phase-7**: assuming we defer 5 low-frequency tools (view_image, list_dir, notebook_edit, ask_user, web_fetch, todo_*), kept-loaded set is ~5 tools (read_file, grep, glob, edit_file, write_file, bash, python_exec, task) Ã— ~400 = ~3200 tokens. Plus tool_search itself (~300) plus 5 deferred-tool names (~50) = ~3550 tokens.
  - **Savings**: ~4000 - ~3550 â‰ˆ **450 tokens** per turn just from name-only deferral.
  - To hit V5_PLAN's â‰¥3000-token target, we need to defer roughly 8 tools (or have larger schemas). Phase 7 contributes to the target; Phases 9+ (sub-agents, skills, all the create_* document tools, MCP) will push the per-turn overhead much higher and the savings will compound. The aggregate audit before Phase 13 enforces the â‰¥3000 final target.
- Code complexity: ~250 LOC `tools/tool_search.py` + ~80 LOC update to `apply_tool_search_deferral` + ~150 LOC tests.
- Maintenance: the keyword-matching algorithm is small (Runnable's CamelCase + MCP-prefix splitting).

### Question 4 â€” Cost worth it?
**Yes**. â‰¥3000 tokens/turn savings Ã— N turns Ã— M sessions = significant cost reduction. Plus higher effective context budget for user work.

### Decision
- **ACCEPTED for v5.0** â€” Phase 7 lands:
  - `tools/tool_search.py` â€” keyword + select + required-term query modes; returns deferred tool schemas in `<functions>` block per Runnable's wire format.
  - `tools/registry.py:apply_tool_search_deferral` â€” replace Phase-2 stub with real implementation.
  - Per-tool `should_defer=True` flags on the **deferred set**: `view_image`, `list_dir`, `notebook_edit` (Phase 7 initial pass; Phases 9-10 will mark `task`, `todo_*`, `create_*`, `web_fetch`, `ask_user`, `skill_*` as deferred too).
  - Per-tool `always_load=True` flags on the **never-defer set**: `tool_search` itself (model needs it to load anything else); `read_file` / `grep` / `glob` / `edit_file` / `write_file` / `bash` / `python_exec` (most-frequently-used; deferring these hurts more than it helps).

### Algorithm details (Runnable parity)
1. **Query parsing** â€” three modes from the same `query` string:
   - `select:Read,Edit,Grep` â†’ exact-name fetch (case-insensitive). Useful for sub-agents/post-compaction where the model knows the name.
   - `+slack send` â†’ required-term: `slack` MUST be in the result; remaining terms rank.
   - `notebook jupyter` â†’ keyword search across name + description, ranked by match count.
2. **Tool name parsing** â€” Runnable handles `mcp__server__action` (split on `__` then `_`) AND regular tools (split CamelCase + underscore). v5 adopts the same. Most v5 tools are snake_case so the CamelCase branch is rarely exercised.
3. **Result wire format** â€” `<functions>{"description": ..., "name": ..., "parameters": ...}</functions>` block. Once present in conversation, the deferred tool is callable like any always-loaded tool. Bedrock honors this because it just sees the function definition appended to the tools list at the API level.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** â€” constraint = `Bedrock + .ipynb`:
- Up-stream: Phase 8's `core/query_engine.py` will call `apply_tool_search_deferral(tools, enabled=True)` per turn before passing the (visible_tools, tool_search_tool) pair to `BedrockClient.chat()`.
- Down-stream: deferred tool names ship in a system-reminder block at message start; full schemas are loaded on demand via tool_search. Bedrock-side: identical to how Anthropic's API treats Runnable's deferred tools.
- Drops Runnable-specific feature gates (`feature('FORK_SUBAGENT')`, `KAIROS`, `KAIROS_BRIEF`, `tengu_glacier_2xr`) â€” those are Anthropic-internal experiments, not applicable to v5.
- Adapts the GrowthBook-flag fork-tool branch: v5 has no GrowthBook; `apply_tool_search_deferral(enabled=...)` is a simple boolean toggle from the QueryEngine.

### Affected files
- compact_v5/MAIN/agent/tools/tool_search.py (new â€” port of ToolSearchTool.ts core logic)
- compact_v5/MAIN/agent/tools/registry.py (`apply_tool_search_deferral` real implementation; replaces Phase-2 stub)
- compact_v5/MAIN/agent/tools/__init__.py (extended bootstrap_built_ins)
- compact_v5/MAIN/agent/tools/{view_image,list_dir,notebook_edit}.py (set `should_defer=True`)
- compact_v5/MAIN/agent/tests/unit/test_tool_search.py (new)
- compact_v5/MAIN/agent/tests/tools/ (extension of existing tests for deferral interaction)

### Linked port-log rows
- #014 â€” Runnable ToolSearchTool/ToolSearchTool.ts (keyword + select + required-term query modes) â†’ tools/tool_search.py
- #015 â€” Runnable ToolSearchTool/prompt.ts (`isDeferredTool` rule + `getPrompt` body) â†’ tools/tool_search.py:_DESCRIPTION + tools/registry.py:_is_deferred
- (No row for utils/toolSearch.ts â€” its `isToolSearchEnabledOptimistic` feature-gate logic is GrowthBook-specific and N/A for v5.)

---

## ADR-014 â€” Phase 8 QueryEngine + retry + errors + IterationBudget
- Date: 2026-04-30
- Phase ID: 08
- Status: ACCEPTED
- Source:
  - Runnable: `gg-claude-code-runnable/src/QueryEngine.ts` (1295 LOC) â€” main agent loop
  - Runnable: `gg-claude-code-runnable/src/services/api/withRetry.ts` (822 LOC) â€” retry + jittered backoff
  - Runnable: `gg-claude-code-runnable/src/services/api/errors.ts` (1207 LOC) â€” error message generators + retryability classification
  - v4: `compact_v4/MAIN/agent/sagemaker_agent.py:8190` (`IterationBudget` â€” Hermes pattern adopted by v4 in v4.9.4)
  - v4: `:8278` (`Agent` class) + `:8650` (`Agent.run`) â€” main agent loop
  - v4: ErrorClassifier + RetryPolicy already inline in Phase-1 `runtime/bedrock_client.py`
  - V5_PLAN.md Phase 8 acceptance: end-to-end mock test (tool_use â†’ tool runs â†’ final answer) AND tool_search deferred-loading round-trip works.
  - Phase 7 contract (ADR-013, blocker #3 fix): query_engine MUST call `apply_tool_search_deferral(enabled=True)` per turn AND extract discovered tool names via `tool_search_discovered_names()` to wire deferred tools into the next turn's API call.

### Question 1 â€” Replacement or addition?
- **REPLACEMENT** of v4's monolithic `Agent.run` loop (lines 8650-9450+, ~800 LOC) with a clean `core/query_engine.py` (target ~400 LOC).
- **EXTRACTION** of Phase-1 inlined `ErrorClassifier` + `RetryPolicy` from `runtime/bedrock_client.py` into dedicated `core/errors.py` + `core/retry.py` modules (Phase-1 ADR-005 noted this would happen in Phase 8).
- **ADDITION** of `core/budget.py` â€” `IterationBudget` class (Hermes pattern; PS Issue #2: visible budget that prevents runaway sub-agent costs).

### Question 2 â€” Architectural justification
**Why core/ package boundary**:
- v4's `Agent` class is 1500+ LOC of mixed concerns (loop + retry + errors + budget + compaction + skill auto-trigger + UI hooks). Reviewing the loop logic requires reading the whole class.
- v5 splits into 4 focused modules with clear single responsibilities. Each is independently testable.
- Phase 8 deliberately ships a **MINIMAL** QueryEngine. Compaction (microcompact / context_collapse / LLM summary), skill auto-trigger, repetition guard, and other v4-Agent features are explicitly **out of scope** for Phase 8 â€” they land in Phase 10 (skills) and Phase 13 (polish). This keeps Phase 8 reviewable and the test surface bounded.

### Phase 8 SCOPE (what's in)
1. `core/budget.py` â€” `IterationBudget` class (Hermes pattern; thread-safe consume/remaining/used). Verbatim port of v4's `IterationBudget` at `sagemaker_agent.py:8190`.
2. `core/errors.py` â€” extract `BedrockErrorCategory` + `ErrorClassifier` from Phase-1 `runtime/bedrock_client.py`. Same classifier semantics; cleaner imports for testing.
3. `core/retry.py` â€” extract `RetryPolicy` from Phase-1 `runtime/bedrock_client.py`. Jittered exponential backoff (~1s, 2s, 4s, 8s with up-to-30% jitter; MAX_RETRIES=4). Verbatim.
4. `core/query_engine.py` â€” the main loop. **Single responsibility**: take a user message, call BedrockClient, handle tool_use, execute tools, feed tool_result back, loop until end_turn / budget exhaustion / max_turns. Plus Phase-7 wiring per ADR-013 blocker #3 contract.

### Phase 8 OUT OF SCOPE (deferred)
- Compaction logic (microcompact / context_collapse / LLM summary) â€” Phase 13 polish OR Phase 10 if needed for skills.
- Skill auto-trigger â€” Phase 10.
- Repetition guard â€” defer; not in V5_PLAN Phase 8 acceptance.
- Cost tracking + budget UI â€” Phase 11 (notebook UX).
- AGENT_STATUS.md auto-update â€” Phase 13 polish.
- Auto-checkpoint (`_maybe_auto_checkpoint`) â€” Phase 13 polish.
- _PENDING_IMAGES queue consumption (Phase 4 view_image side channel) â€” query_engine drains it before each chat() call. THIS IS IN SCOPE.
- _RECENT_DIFFS recording â€” defer.
- File-read tracking population (Phase 4 contract) â€” query_engine marks files as read after each successful read_file call. IN SCOPE.

### Phase 7 wiring contract (in-scope, ADR-013 blocker #3)
1. Per-turn: call `apply_tool_search_deferral(tools, enabled=True)` â†’ `(visible_tools, deferred_names)`.
2. If `deferred_names` is non-empty, prepend a `<system-reminder>` block to the user message announcing them.
3. Pass `context={"active_tools": <full_pool>}` when executing tool_search so it filters correctly.
4. After each model turn, scan tool_use blocks for `tool_search` calls in the just-completed turn. After their tool_result fires, call `tool_search_discovered_names(tool_result_text)` and add those tools' schemas to the NEXT turn's `tools=` API param (via the `discovered_tools` set on the QueryEngine).

### Question 3 â€” Cost
- Token cost (static prompt): 0 (core/ is runtime code).
- Token cost (per turn): ~30 tokens for the optional system-reminder block announcing deferred names. Negligible vs the savings (~770 tokens/turn from Phase 7 deferral).
- Code complexity: ~800 LOC across 4 core/ modules + ~300 LOC tests. Replaces ~1500 LOC of v4 monolith.
- Maintenance: each concern in its own file; tests target each.

### Question 4 â€” Cost worth it?
**Yes**. Phase 8 is the integration phase that makes v5 actually run. Without it, none of the prior phases are exercisable.

### Decision
- **ACCEPTED for v5.0** â€” 4 core/ modules + tests + integration test demonstrating end-to-end loop with tool_search deferred-loading round-trip.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** â€” constraint = `Bedrock` + `.ipynb`:
- QueryEngine adapts Runnable's main loop to Bedrock (no streaming differences, no Anthropic-specific OAuth flows, no GrowthBook feature flags).
- Drops Runnable-specific UI hooks (Ink JSX) â€” v5 uses simple `output_fn` callback for printing per turn.
- Drops Runnable's complex retryability classifier in favor of v4's already-tested simpler version (Phase 1 verbatim).
- IterationBudget is Hermes pattern, not Runnable-original; v4 adopted it; v5 inherits via verbatim port.

### PS Issue mapping
- **PS Issue #2 (iteration budget visible)**: `core/budget.py` exposes `consume() / remaining() / used() / total()` for the Phase-11 ipywidgets UI to display a live progress bar. Phase 11 will land the UI; Phase 8 lands the data plumbing.

### Affected files
- compact_v5/MAIN/agent/core/__init__.py (new)
- compact_v5/MAIN/agent/core/budget.py (new â€” IterationBudget)
- compact_v5/MAIN/agent/core/errors.py (new â€” extract from runtime/bedrock_client.py)
- compact_v5/MAIN/agent/core/retry.py (new â€” extract from runtime/bedrock_client.py)
- compact_v5/MAIN/agent/core/query_engine.py (new â€” main loop)
- compact_v5/MAIN/agent/tests/unit/test_budget.py (new)
- compact_v5/MAIN/agent/tests/unit/test_errors.py (new)
- compact_v5/MAIN/agent/tests/unit/test_retry.py (new)
- compact_v5/MAIN/agent/tests/integration/test_query_engine.py (new â€” end-to-end mock test + tool_search round-trip)

### Linked port-log rows
- #016 â€” Hermes IterationBudget (via v4) â†’ core/budget.py (verbatim)
- #017 â€” Phase-1 ErrorClassifier extraction â†’ core/errors.py (verbatim)
- #018 â€” Phase-1 RetryPolicy extraction â†’ core/retry.py (verbatim)
- #019 â€” Runnable QueryEngine.ts (main agent loop) â†’ core/query_engine.py (ADAPT â€” minimal v5 scope)
- #020 â€” Runnable services/api/withRetry.ts (retry + jittered backoff) â†’ core/retry.py (already covered by #018; this row records the parity claim)
- (No row for services/api/errors.ts â€” v5 uses v4's simpler ErrorClassifier; Phase 12+ may extend.)

---

## ADR-015 â€” Phase 9: Sub-agent + Task tool (forkSubagent budget sharing)

- Date: 2026-04-30
- Phase ID: 09
- Status: ACCEPTED
- Source: gg-claude-code-runnable/src/tools/AgentTool/forkSubagent.ts (210 LOC) + AgentTool.tsx (1397 LOC) + runAgent.ts (973 LOC)
            v4 sagemaker_agent.py:_run_task_tool (line 8350) + _build_subagent_env_details + _build_subagent_handoff_block + AGENT_TYPES (line 6914)

### Question 1 â€” Replacement or addition?
- **REPLACEMENT** of v4's `_run_task_tool` (~600 LOC inline in `Agent` class) + `AGENT_TYPES` dict + handoff/env helpers, all currently inline in `sagemaker_agent.py`.
- v5 reorganizes into: `subagent/env.py` (env-details builder), `subagent/handoff.py` (AGENT_STATUS slice + todos + recent files), `subagent/spawn.py` (fork-style spawn that shares IterationBudget), `tools/task.py` (the user-facing tool).
- Cite v4: sagemaker_agent.py:8350 (_run_task_tool), 7695 (_build_subagent_env_details), 7771 (_build_subagent_handoff_block), 6914 (AGENT_TYPES).

### Question 2 â€” Architectural justification
v5's value-add over v4:
- **Shared IterationBudget** (ADR-014 PS Issue #2 wiring): child QueryEngine constructed with `budget=parent.budget`. v4 inlines a similar pattern but the budget object is buried in the monolith; v5 makes it a public constructor parameter.
- **Module surface for testing**: each piece (env probing, handoff slicing, spawn) testable independently. v4's _run_task_tool can only be tested via Agent.run integration.
- **Fail-quiet contracts**: env/handoff probes never raise â€” sub-agent spawn must not fail because git timed out. v4 has the same contract; v5 documents it explicitly via tests.
- **AGENT_TYPES staying minimal**: Phase 9 ships `general` only. The `build`/`plan`/`explore`/`verify` agent types from v4 can land later; their prompts are large and reviewable as data, not code.

### Question 3 â€” Cost
- Token cost (static prompt): +0 â€” task tool description goes via deferred-loading (Phase 7) in plan-mode caller.
- Token cost (per turn): unchanged for parent. Child gets fresh prompt assembly + handoff block (bounded â‰¤ ~1500 chars after _SUBAGENT_STATUS_MAX_CHARS + _SUBAGENT_TODOS_MAX_CHARS sanitization).
- Code complexity: ~500 LOC across 4 files (compared to v4's ~600 LOC inline).
- Maintenance: subagent/ owners can iterate without touching agent loop; Phase 11 UI plumbs sub-agent progress separately.

### Question 4 â€” Cost worth it?
YES. Sub-agents are the primary mechanism for parallel/specialized work; without them v5 cannot match v4 functionality, blocking ship. forkSubagent budget-sharing is the precise mechanism Hermes contributed in v4.9.4 â€” without it, a parent + N sub-agents could collectively blow the cost ceiling.

### Decision
- **ACCEPTED** for v5.0.
- Phase 9 ships:
  - `subagent/env.py` â€” `build_env_details(agent_type, depth, workspace=None)` returning a 6-line block. Fail-quiet on git probes. Verbatim port of `_build_subagent_env_details`.
  - `subagent/handoff.py` â€” `build_handoff_block(status_path=None, todos_text=None, recent_files=None)` returning AGENT_STATUS slice + active todos + recent file paths. Each section optional + bounded. Verbatim port of `_build_subagent_handoff_block` minus the status_doc / RECENT_DIFFS globals coupling (v5 takes inputs as parameters so callers in Phase 11 can wire them).
  - `subagent/spawn.py` â€” `spawn_subagent(parent_engine, prompt, agent_type, max_turns=None)` that creates a child `QueryEngine(budget=parent_engine.budget, ...)` with a fresh message buffer and runs the prompt. Returns `(text, child_engine)`. Includes depth-limit enforcement.
  - `tools/task.py` â€” task tool registered via `tools/__init__.py:bootstrap_built_ins`. Description: "Launch a sub-agent for a specific task." Schema: `{description, prompt, subagent_type}`. Executes via `spawn_subagent(...)`. Marked `should_defer=True` (low-frequency).
- Phase 9 does NOT ship: AGENT_TYPES configuration (build/plan/explore/verify prompts), worktree isolation (build agent type only â€” defer to Phase 11), parallel sub-agent dispatch.

### Budget reservation
- Static prompt: +0 tokens (task tool description not in static prompt; deferred via Phase 7).
- Per-turn (when task tool invoked): child agent's per-turn cost = parent's per-turn cost (same budget). Parent's per-turn cost: +1 task-tool schema if not deferred, 0 if deferred. v5 marks task as `should_defer=True` â†’ 0 added per-turn for non-task-using turns.

### Reconciliation
After Phase 9 lands:
- Static prompt token count must remain at 2498 (no change).
- task tool registered with `should_defer=True` (parity with Phase 7 deferred set).
- Test `test_subagent_shares_iteration_budget` proves the budget is shared.
- Test `test_subagent_parent_context_unchanged` proves the parent's message buffer is not mutated by sub-agent dispatch.

### Linked port-log rows
- #021 â€” forkSubagent.ts (budget sharing pattern) â†’ subagent/spawn.py (ADAPT â€” drops experimental fork branch, drops cache-prefix-identical message replay)
- #022 â€” _build_subagent_env_details (v4) â†’ subagent/env.py (PORT â€” verbatim with parameterized workspace)
- #023 â€” _build_subagent_handoff_block (v4) â†’ subagent/handoff.py (ADAPT â€” accepts inputs as parameters instead of pulling from globals)
- #024 â€” _run_task_tool (v4) â†’ tools/task.py (ADAPT â€” minimal Phase-9 scope; AGENT_TYPES + worktree deferred)

---

## ADR-016 â€” Phase 10: Skills + auto-trigger + Hermes filter (PS Issue #1)

- Date: 2026-04-30
- Phase ID: 10
- Status: ACCEPTED
- Source: gg-claude-code-runnable/src/tools/SkillTool/ + skills/loadAllSkills.ts
            v4 sagemaker_agent.py:SkillManager (line 2684) + 10 skills directories under compact_v4/MAIN/agent/skills/
            hermes-agent (skill-filtering-by-available-tools pattern)
            v4.9.5 self-patching skills (CONFIG.enable_skill_patching opt-in)

### Question 1 â€” Replacement or addition?
- **REPLACEMENT** of v4's `SkillManager` (~470 LOC inline at sagemaker_agent.py:2684) and `tool_skill` / `tool_skill_propose_patch` executors. v5 reorganizes into `skills/manager.py` + `tools/skill.py` + `tools/skill_propose_patch.py`.
- 10 skills directories (`batch`, `clara`, `design`, `html`, `reflexion`, `report`, `review`, `security-review`, `simplify`, `verify`) ported BYTE-FOR-BYTE under `skills/` (no content edits). User memory + V5_PLAN.md require this verbatim preservation.
- ADDITION: Hermes-style skill filtering by available tools (PS Issue #1). Optional `requires_tools` frontmatter field; if a skill declares it, the skill is filtered out of auto-trigger when its required tools aren't in the active pool. Backwards-compatible â€” existing skills don't need the field.

### Question 2 â€” Architectural justification
- **All 10 skills must load** (V5_PLAN.md acceptance) â€” they are battle-tested production behavior shipping with v4.
- **Auto-trigger respects v4.9.6 default-OFF** (V5_PLAN.md acceptance) â€” `CONFIG.enable_skill_auto_trigger=False` AND per-skill `auto_trigger: false` default = no auto-loading without explicit opt-in. v4.9.6 made this conservative for cost reasons (avoid silent injection of large skill bodies).
- **`skill_propose_patch` opt-in** â€” `CONFIG.enable_skill_patching=False` default; tool returns no-op message unless flipped. v4.9.5 ships the same opt-in semantics (8 safety rails: opt-in, propose-not-apply, diff preview, snapshot, audit log, time-stamped proposal files, per-skill .proposed/, never-touches-live).
- **Hermes filter (PS Issue #1)**: in scenarios where a tool is blocked or deferred, surfacing a skill that needs that tool just frustrates the model. The filter improves signal-to-noise for the auto-trigger reminder block. Optional + backwards-compatible.

### Question 3 â€” Cost
- Token cost (static prompt): +0 â€” `skill` and `skill_propose_patch` tools marked `should_defer=True`. Auto-trigger reminder added to dynamic tail only when relevant skills found (â‰¤120 chars per skill description Ã— â‰¤5 skills = ~600 tokens worst case, only when auto-trigger fires).
- Token cost (per turn): unchanged for non-skill turns. Active skill body injected in the dynamic tail when a skill is active (capped via `read_skill(name, max_chars=12000)`).
- Code complexity: ~600 LOC across skills/manager.py + 2 tools (vs v4's 470 LOC inline).
- Maintenance: skills/ directories byte-for-byte from v4; AIPower already syncs from this canonical source. Hermes filter is ~30 LOC of optional filtering logic.

### Question 4 â€” Cost worth it?
YES.
- Skills are core product surface â€” without them v5 doesn't match v4 functionality, blocking ship.
- Hermes filter cost is tiny relative to its UX value (avoids "I'd suggest using `verify` skill" when bash is blocked).
- Self-patching is opt-in so default users don't pay any complexity.

### Decision
- **ACCEPTED** for v5.0.
- Phase 10 ships:
  - `skills/__init__.py` + `skills/manager.py` â€” `SkillManager` class with `discover()` / `list_skills()` / `read_skill(name, max_chars)` / `get_active_skill_prompt()` / `discover_relevant(user_message, active_tools=None)` / `list_for_prompt(budget_tokens=0)` / `propose_patch()` / `list_proposals()` / `apply_proposal()` / `revert_skill()`. Hermes filter sits inside `discover_relevant` via the new `active_tools` parameter.
  - `skills/<10 dirs>/` â€” copied byte-for-byte from compact_v4/MAIN/agent/skills/.
  - `tools/skill.py` â€” list, activate, read, deactivate. Marked `should_defer=True`.
  - `tools/skill_propose_patch.py` â€” propose-only (never auto-applies). Returns no-op message when `CONFIG.enable_skill_patching=False`. Marked `should_defer=True`.
- Phase 10 does NOT ship: a `skill_apply` tool (apply is operator-only via `/skill apply` slash command in Phase 11 UX), automatic skill auto-trigger (default-OFF preserved), domain-specific skills (powerbi-dashboard variants stay in AIPower repo).

### Budget reservation
- Static prompt: +0 tokens (both new tools deferred).
- Per-turn (when skill active): up to 12000 chars of skill content (~3000 tokens) injected after cache boundary. Same as v4.
- Dynamic-tail auto-trigger reminder: capped at SKILL_LISTING_DESC_CAP=250 chars Ã— â‰¤5 skills = ~250 tokens worst case.

### Reconciliation
After Phase 10 lands:
- Static prompt token count must remain at 2498 (no change).
- All 10 skills load via `SkillManager.discover()`.
- Default config: no skill auto-loads without explicit opt-in.
- Default config: `skill_propose_patch` returns no-op message.
- Hermes filter: skills with `requires_tools` not subset of `active_tools` are filtered from `discover_relevant`.

### Linked port-log rows
- #025 â€” v4 SkillManager â†’ skills/manager.py (PORT â€” verbatim port; CONFIG.workspace decoupled to constructor parameter for testability)
- #026 â€” v4 tool_skill â†’ tools/skill.py (ADAPT â€” uses new SkillManager surface; should_defer=True)
- #027 â€” v4 tool_skill_propose_patch â†’ tools/skill_propose_patch.py (ADAPT â€” same opt-in contract; should_defer=True)
- #028 â€” Hermes skill-filtering-by-available-tools pattern â†’ SkillManager.discover_relevant(active_tools) (ADAPT â€” optional `requires_tools` frontmatter field; backwards-compatible)
- #029 â€” 10 skills/ directories from v4 â†’ compact_v5/MAIN/agent/skills/ (PURE COPY â€” content byte-for-byte; no rows for individual skills as they are reused content not Runnable patterns)

---

## ADR-017 â€” Phase 11: Notebook UX + entry + thinking/budget UI (PS Issue #4)

- Date: 2026-04-30
- Phase ID: 11
- Status: ACCEPTED
- Source: v4 sagemaker_agent.py:create_chat_ui (line 9735, ~2000 LOC) + chat.ipynb (5 cells) + chat.md
            v4.8.0 thinking-mode UI surface (PS Issue #4)
            v4.9.4 IterationBudget UI commitment (PS Issue #2 â€” Phase 8 shipped data model, Phase 11 wires the widget)

### Question 1 â€” Replacement or addition?
- **REPLACEMENT** of v4's `create_chat_ui()` + `chat.ipynb` shipping surface. v5 reorganizes into: `agent.py` (public Agent class), `entry.py` (cell-0 import target), `ui/chat_ui.py` (UI orchestration), `ui/widgets.py` (data widgets), `chat.ipynb` (notebook), `chat.md` (companion).
- ADDITION of explicit PS Issue #4 visibility (thinking budget shown in UI; v4 had thinking-mode toggle but no in-UI surface for budget consumption).

### Question 2 â€” Architectural justification
v5 value-add over v4:
- **agent.py is its own public surface** (~200 LOC) â€” wraps QueryEngine + SkillManager + Config + BedrockClient. v4's `Agent` is buried in the monolith and exposes everything.
- **ChatUI is much smaller** (~150 LOC vs v4's ~2000 LOC). Most of v4's complexity is HTML rendering of message history; v5 delegates to ipywidgets and lets the browser handle layout. Phase 11 also intentionally drops v4's complex chat-display HTML rendering for the minimal MVP â€” operators get text output + widgets, not the v4 full-fidelity chat display.
- **PS Issue #2 visible IterationBudget**: Phase 8 shipped `IterationBudget` data model. Phase 11 wires `consume() / used() / total()` to an `ipywidgets.IntProgress` so the user sees the budget burning down as parent + sub-agents consume it.
- **PS Issue #4 visible thinking budget**: Phase 1 already sends thinking config when enabled; Phase 11 surfaces a small label showing the current thinking-budget setting AND a checkbox to toggle it.

### Question 3 â€” Cost
- Token cost (static prompt): +0.
- Token cost (per turn): +0 â€” UI is post-Bedrock display only.
- Code complexity: ~600 LOC across 7 files vs v4's ~2000 LOC inline.
- Maintenance: ipywidgets-dependent code is in `ui/`, isolated from agent loop.

### Question 4 â€” Cost worth it?
YES. The notebook is the user's ONLY surface for v5 â€” without `chat.ipynb` running cleanly, the entire ship pipeline is moot.

### Decision
- **ACCEPTED** for v5.0.
- Phase 11 ships:
  - `agent.py` â€” `Agent` class. Wraps `BedrockClient` + `IterationBudget` + `QueryEngine` + optional `SkillManager`. Public methods: `run(message)`, `clear()`, `stop()`.
  - `entry.py` â€” cell-0 import target. Re-exports `Agent`, `create_chat_ui`, `CONFIG`.
  - `ui/chat_ui.py` â€” `create_chat_ui()` factory + `ChatUI` class. ipywidgets-dependent. Falls back to console-mode when ipywidgets is unavailable.
  - `ui/widgets.py` â€” `IterationBudgetWidget` (data class wrapping ipywidgets.IntProgress; PS Issue #2) + `ThinkingBudgetWidget` (data class wrapping ipywidgets.HBox with toggle + budget label; PS Issue #4).
  - `chat.ipynb` â€” minimal 4 cells: install / config / launch / quick-reminder.
  - `chat.md` â€” companion markdown explaining the notebook.
  - `tests/integration/test_notebook_smoke.py` â€” hello-world turn vs mock Bedrock; UI factory smoke test (no ipywidgets render assertions, just construction).
- Phase 11 does NOT ship: full v4 chat-display HTML rendering (defer to Phase 13 polish), v4's compact/clean buttons (microcompact lands as separate phase if at all), parallel sub-agent visualization, model-switcher widget (CONFIG.model_id static), session-history persistence (SessionManager from Phase 1 already exists; Phase 11 doesn't auto-restore).

### Budget reservation
- Static prompt: +0 tokens.
- ipywidgets dependency already in install list (v4 cell 1 has it).
- Phase 11 does not change static prompt or per-turn schemas.

### Reconciliation
After Phase 11 lands:
- Notebook smoke test passes against mock Bedrock.
- IterationBudget widget renders + updates after `consume()`.
- Thinking-budget label shows current value.
- chat.ipynb cells 1-3 import cleanly, cell 3 returns a UI object.

### Linked port-log rows
- #030 â€” v4 create_chat_ui â†’ ui/chat_ui.py (ADAPT â€” minimal Phase-11 scope)
- #031 â€” v4 Agent class (extracted from monolith) â†’ agent.py (ADAPT â€” public-surface wrapper around Phase 8-10 modules)
- #032 â€” v4 chat.ipynb â†’ compact_v5/MAIN/agent/chat.ipynb (ADAPT â€” minimal cells)
- #033 â€” Phase-8 IterationBudget data model â†’ ui/widgets.py:IterationBudgetWidget (ADDITION â€” PS Issue #2 fix; ipywidgets progress bar)
- #034 â€” v4.8.0 thinking-mode â†’ ui/widgets.py:ThinkingBudgetWidget (ADDITION â€” PS Issue #4 fix; toggle + budget label)

---

## ADR-018 â€” Phase 12: Parity tests vs v4 (audit gate before Phase 13)

- Date: 2026-04-30
- Phase ID: 12
- Status: ACCEPTED
- Source: V5_PLAN.md Â§Phase 12 + risk register #8 (critical-scenario must-pass suite)

### Question 1 â€” Replacement or addition?
- **ADDITION** of two parity test files plus an in-PORT_LOG appendix tracking documented v4-vs-v5 differences.

### Question 2 â€” Architectural justification
- V5_PLAN.md success metric #1: "Functional parity with v4.10.10 (same skills work, same security holds, same notebook UX)." Phase 12 is the verification gate.
- Risk #8 (parity blind spots): "Add must-pass critical-scenario suite (security deny, blocked-tool continuation, retry, prompt assembly, resume after compaction) requiring 100% pass; the â‰¥90% threshold applies only to non-critical scenarios."
- Phase 8.5 thin-slice already covers cross-phase integration; Phase 12 expands to specific v4 behavioral parity.

### Question 3 â€” Cost
- Token cost (static prompt): +0.
- Code complexity: ~600 LOC of test fixtures.
- Maintenance: parity suite is the verification spec â€” changes when v4 behavior changes (which is never; v4 is frozen).

### Question 4 â€” Cost worth it?
YES. Without Phase 12, ship-gate is unverifiable. v5 ships only if both critical (100%) AND non-critical (â‰¥90%) parity gates pass.

### Decision
- **ACCEPTED** for v5.0.
- Phase 12 ships:
  - `tests/parity/test_parity_critical.py` â€” 15 critical scenarios (must all pass). Covers: security deny, plan-mode dispatch gate, retry policy semantics, prompt assembly invariants (slot-2 + budget + boundary), resume-after-compaction equivalence (Phase 11 clear+rerun), Phase 7 wiring contract end-to-end, sub-agent budget sharing end-to-end, skill auto-trigger default-OFF, 10 production skills load, PS Issue #2/#4 widget visibility, context-overflow clean exit, tool exception trap, deferred-loading payload exclusion, BedrockClient cache-fallback semantics, mock-mode response shape parity.
  - `tests/parity/test_parity_non_critical.py` â€” 10 non-critical scenarios (â‰¥9/10 must pass). Covers: tool result truncation length, error message exact wording, skill CSO format advisory, audit log line format, widget HTML exact markup, depth-exceeded message wording, plan-mode error message wording, tool-search wire format details, frontmatter parser edge cases, env-details line count.
- Phase 12 does NOT actually run v4 â€” v4 is frozen at sha9bf0...e1c2 (compact_v4/). Fixtures encode "this is what v4 does for this input" and assert v5 matches. Differences are documented in PORT_LOG row #035 (parity appendix).

### Budget reservation
- Static prompt: +0.
- Per-turn: +0.

### Reconciliation
After Phase 12 lands:
- 15/15 critical scenarios pass.
- â‰¥9/10 non-critical scenarios pass (allowed slip: 1).
- Any non-critical FAIL is documented in PORT_LOG #035 (parity differences appendix) with rationale.

### Linked port-log rows
- #035 â€” V5_PLAN.md Â§Phase 12 â†’ tests/parity/test_parity_critical.py + test_parity_non_critical.py + PORT_LOG parity appendix (ADD â€” parity verification surface)

---

## ADR-019 â€” Phase 13: Cutover + ship zip + tag v5.0.0 (FINAL)

- Date: 2026-04-30
- Phase ID: 13
- Status: ACCEPTED
- Source: V5_PLAN.md Â§Phase 13 + v4 _rebuild_zip.py (181 LOC) + v4 verify_ship_zip.py (161 LOC)

### Question 1 â€” Replacement or addition?
- **REPLACEMENT** of the v4 ship pipeline for v5: `compact_v5/_rebuild_zip.py` (adapted to walk the nested package layout) + `compact_v5/verify_ship_zip.py` (REUSED verbatim from v4 with light tweaks for v5 file list).

### Question 2 â€” Architectural justification
- v5 ships only when ALL gates met: phases 00-12 DONE, parity 15/15+10/10, audit 7/7. Phase 13 is the ship pipeline.
- v4's `_rebuild_zip.py` walks `MAIN/agent/` (monolith). v5 walks `compact_v5/MAIN/agent/` AND preserves the nested-package layout (`core/`, `tools/`, `skills/`, etc.) so imports work in the unzipped directory.

### Question 3 â€” Cost
- Token cost: +0.
- Code complexity: ~250 LOC (~200 zip builder + ~50 README).

### Question 4 â€” Cost worth it?
YES. v5 doesn't ship without a zip. This is the FINAL phase.

### Decision
- **ACCEPTED** for v5.0.
- Phase 13 ships:
  - `compact_v5/_rebuild_zip.py` â€” adapted from v4. Walks `MAIN/agent/` in v5 layout. Preserves nested packages. Excludes tests/changelogs/_status/docs/_archive/__pycache__.
  - `compact_v5/verify_ship_zip.py` â€” adapts v4's verifier to v5's runtime file list (chat.ipynb, chat.md, entry.py, agent/__init__.py, core/, tools/, skills/, runtime/, prompt/, ui/, subagent/, security/, mcp/, memory.md, AGENT_STATUS.md).
  - `compact_v5/CHANGELOG.md` â€” top-level v5 release notes summarizing all phases.
  - `compact_v5/README.md` â€” minimal: how to extract + run chat.ipynb.
  - Final tag: `v5.0.0` after the zip extracts cleanly + verify_ship_zip passes.
- Phase 13 does NOT: merge to main (v4 stays on main; v5 lives on `v5-build` until user explicitly ships); upload zip to a release; auto-deploy.

### Budget reservation
- Static prompt: +0.
- Per-turn: +0.

### Reconciliation
After Phase 13 lands:
- `compact_v5.zip` extracts to a flat-ish layout and `chat.ipynb` opens cleanly.
- `verify_ship_zip.py` reports PASS.
- Tests still 437/4 (Phase 12 baseline).
- Final tag `v5.0.0` created.

### Linked port-log rows
- #036 â€” v4 _rebuild_zip.py â†’ compact_v5/_rebuild_zip.py (ADAPT â€” walks v5 nested-package layout).
- #037 â€” v4 verify_ship_zip.py â†’ compact_v5/verify_ship_zip.py (ADAPT â€” v5 runtime file list).

---

## (Append future ADRs below this line â€” keep numerical order 020, 021, ...)

## ADR-020 â€” Block 0 (v5.0.1): `sagemaker_agent.py` shim + notebook smoke gate

**Date**: 2026-05-02
**Phase ID**: v5.0.1 Block 0
**Status**: ACCEPTED

### Context
v5.0.0 reorganized the v4 monolith into nested packages (`runtime/`, `core/`,
`agent/`, `ui/`, `tools/`, `skills/`, `subagent/`, `security/`, `prompt/`).
The Phase-11 notebook (`chat.ipynb`) imports from `entry`. v4's notebook
imports from `sagemaker_agent`. v5.0.1 hard-constraint #2 requires that v4's
canonical `chat.ipynb` continues to work unchanged on v5 via a shim â€” the
notebook should not need to know about the v5 reorg.

### Options
1. **Drop-in shim** (chosen): tiny `sagemaker_agent.py` at the agent root that
   re-exports `entry`'s public surface. v4's `from sagemaker_agent import â€¦`
   line resolves; everything else stays in its v5 module.
2. **Replace v5 chat.ipynb with v4's verbatim**: most faithful to constraint
   #2 but pulls in v4 widgets that depend on Block-B+ (`session_cost_limit`)
   and Block-D (slash commands) features not yet present at Block 0. Defers
   to Block E+F.
3. **Move all v5 surface back to a top-level `sagemaker_agent` module**:
   undoes the Phase-2..11 file-per-section structure. Violates constraint
   #5 (minimum file count) and constraint #6 (architecture-first).

### Decision
Option 1. Block 0 ships a 30-LOC shim that re-exports `Agent`, `BEDROCK_MODELS`,
`CONFIG`, `IterationBudget`, `SkillManager`, and `create_chat_ui` from `entry`.
v5's existing `chat.ipynb` is left untouched at Block 0; full notebook-shape
restoration to v4 canonical is Block E+F territory (per Wave-3
COMBINED_ARCHITECTURE.md).

### Rationale
- Smallest possible surface that satisfies constraint #2 at Block 0 boundary.
- Zero impact on Phase 1-13 module structure.
- v4's `from sagemaker_agent import {BEDROCK_MODELS, CONFIG, create_chat_ui}`
  line works literally â€” verified by `test_smoke_imports` and
  `test_v4_import_compat`.
- The shim is implementation-free; it cannot drift from v5 internals because
  it re-binds, never re-implements.

### Runnable-fidelity impact
None. This shim is v4-compat, not Runnable-derived.

### Affected files
- NEW: `compact_v5/MAIN/agent/sagemaker_agent.py` (shim)
- NEW: `compact_v5/MAIN/agent/tests/integration/test_block0_shim.py` (5 tests)
- UPDATED: `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` (row #038)
- UPDATED: `compact_v5/_status/V5_BUILD_STATUS.md` (Block 0 done; next = smoke gate / Block B)

### Linked port-log rows
- #038 â€” Block 0 shim.

### Validation
- 5/5 Block 0 tests green (TEST_DESIGN Â§Block 0).
- Full pytest 442 passed + 4 skipped (was 437 + 4; +5 new from Block 0).
- `verify_ship_zip.py`: PASS.
- Codex AXIS A/B/C: APPROVE (review at `_status/codex_reviews/block-0.md`).

### Notes / known scope remaps (constraint #3 â€” no deferrals)

SYNTHESIS_MASTER.md Â§Block 0 (lines 32-47) tags 9 additional items
"Block 0" because that is where their PORT_LOG row originates. All 9 are
**ported, not dropped** â€” but their *implementation* lands in the Block
that architecturally owns the touched module. Each item below has an
explicit landing Block + a test gate where its lock test runs. This
table is the no-deferrals contract.

| Item | Capability | LOC | Lands in Block | Implementation site (target file) | Lock test (Block where it runs) |
|---|---|---|---|---|---|
| 0-1 | SYSTEM_PROMPT verbatim re-export | 0 (doc) | Block 0 | `prompt/*.md` (Phase 6, present) + this PORT_LOG row #038 | `test_v4_import_compat` (Block 0) |
| 0-2 | `getSessionStartDate()` + `getLocalMonthYear()` (cache-stable date) | 15 | **Block E+F** | `prompt/env_block.py` (formatter for `prompt/env_block.md`) | `test_env_block_uses_month_year_not_iso_date` (Block E+F) |
| 0-3 | `BEDROCK_EXTRA_PARAMS_HEADERS` Set | 5 | **Block B** | `runtime/bedrock_client.py` (constant + reference at invoke site) | `test_extra_params_in_body_not_headers` (Block B) |
| 0-4 | env block format (Windows-shell hint, OS version, Notes appendix) | 30 | **Block E+F** | `prompt/env_block.md` + `prompt/env_block.py` | `test_env_block_includes_shell_hint_and_notes` (Block E+F) |
| 0-5 | `getScratchpadInstructions()` per-session scratchpad dir | 30 | **Block C** | `security/scratchpad.py` + allowlist update + `prompt/scratchpad.md` | `test_scratchpad_dir_pre_allowlisted_and_gc` (Block C) |
| 0-6 | `getKnowledgeCutoff(modelId)` Sonnet 4.6 / Haiku 4.5 cutoffs | 5 | **Block E+F** | `prompt/env_block.py` (cutoff lookup table) | `test_env_block_emits_model_specific_knowledge_cutoff` (Block E+F) |
| 0-7 | `cleanupRegistry` graceful-shutdown for SIGINT / atexit | 15 | **Block B+** | `runtime/cleanup_registry.py` + `runtime/session.py` flush hook | `test_cleanup_registry_flushes_on_atexit_and_sigint` (Block B+) |
| 0-8 | `validateBoundedIntEnvVar` env-validation helper | 30 | **Block B** | `runtime/env_validation.py` (used by Config dataclass numeric loaders) | `test_env_validation_clamps_and_rejects_bad_input` (Block B) |
| 0-9 | Feature-flag fail-closed at import boundary | 30 | **Block B+** | `runtime/feature_flags.py` (returns False for banned modules) + `entry.py` import-time guard | `test_banned_module_imports_fail_closed` (Block B+) |
| 0-10 | `_scan_for_prompt_injection` + `_INJECTION_PATTERNS` (v4-native) | 40 | **Block C** | `security/injection_scanner.py` (v4 verbatim port from sagemaker_agent.py:7509-7541) | `test_injection_scanner_v4_native` (Block C; already in TEST_DESIGN Â§Block C) |

Codex AXIS C (Block 0 review #1) flagged this remap as UNDECLARED_PATTERN
when only stated in prose; the table above declares it concretely. Each
target Block's review (when it lands) must verify (a) the row above is
honored, (b) the lock test exists, and (c) the SYNTHESIS_MASTER Â§3 row
for that item references the implementing Block. Plan-level cross-link
added to `_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` Block 0 table head
note.


2026-05-02T22:55:20.536641Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 1.4 seconds
Output:
Get-Content : Cannot find path 'D:\Github\sagemaker-coding-agent\_status\codex_reviews\block-0.md' because it does not 
exist.
At line:2 char:1
+ Get-Content -Raw '_status/codex_reviews/block-0.md'
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (D:\Github\sagem...iews\block-0.md:String) [Get-Content], ItemNotFoundEx 
   ception
    + FullyQualifiedErrorId : PathNotFound,Microsoft.PowerShell.Commands.GetContentCommand
 

 exited 1 in 1376ms:
Get-Content : Cannot find path 'D:\Github\sagemaker-coding-agent\_status\codex_reviews\block-0.md' because it does not 
exist.
At line:2 char:1
+ Get-Content -Raw '_status/codex_reviews/block-0.md'
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (D:\Github\sagem...iews\block-0.md:String) [Get-Content], ItemNotFoundEx 
   ception
    + FullyQualifiedErrorId : PathNotFound,Microsoft.PowerShell.Commands.GetContentCommand
 

codex
I’ve confirmed the four updated target files and the new ADR-020 remap table content. Next I’m checking the prior review note and line-level consistency to see whether any residual or newly introduced gaps remain.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg --files -g '*block-0.md'" in D:\Github\sagemaker-coding-agent
 succeeded in 962ms:
compact_v5\_status\codex_reviews\block-0.md

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Raw 'compact_v5/_status/codex_reviews/block-0.md'" in D:\Github\sagemaker-coding-agent
 succeeded in 684ms:
Reading additional input from stdin...
OpenAI Codex v0.125.0 (research preview)
--------
workdir: D:\Github\sagemaker-coding-agent
model: gpt-5.3-codex
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, C:\Users\winst\.codex\memories]
reasoning effort: high
reasoning summaries: none
session id: 019deae6-ac54-7eb0-94bd-4d75407daa1c
--------
user
You are re-reviewing Block 0 of v5.0.1 â€” iteration #2 after addressing the
3 findings from your first review (saved at
_status/codex_reviews/block-0.md). The original first-pass verdict was
APPROVE_WITH_FIXES with [HIGH] UNDECLARED_PATTERN on no-deferrals
evidence, [MEDIUM] test-design drift, and [LOW] PORT_LOG #036 typo.

Changes applied since first pass:

(1) [HIGH] explicit remap table added to ADR-020 declaring per-item
    landing Block + lock-test path for each of Block 0 items 0-1..0-10.
    SYNTHESIS_MASTER.md Â§Block 0 head note added cross-linking to ADR-020.
    Files: compact_v5/_status/V5_DESIGN_DECISIONS.md (ADR-020 Â§Notes /
    known scope remaps), compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md
    (Block 0 table head note).

(2) [MEDIUM] TEST_DESIGN.md Â§Block 0 updated with implementation-note
    section explaining (a) T3 uses manual exec() not papermill (and why
    â€” papermill is not in the v5 ship-zip dep set; manual exec covers the
    smoke surface adequately under mock_mode), (b) T2 accepts ConsoleChatUI
    fallback when ipywidgets is unavailable (matches Phase 11 ADR-017
    factory contract).
    File: compact_v5/_phase_2/wave_6/TEST_DESIGN.md Â§Block 0.

(3) [LOW] sagemaker_agent.py docstring corrected: PORT_LOG #036 â†’ #038.
    File: compact_v5/MAIN/agent/sagemaker_agent.py line 19.

Tests: 442 passed + 4 skipped (unchanged from first review).
verify_ship_zip.py: PASS.

Re-evaluate Block 0 against the same 3 axes (A: errors / B: v5 fit /
C: reference coverage). Does the remap table satisfy "no deferrals" by
declaring each 0-N item's implementation Block + lock test? Are there
any new findings introduced by the fix-up commits?

Read the same paths as before plus:
- compact_v5/_status/V5_DESIGN_DECISIONS.md Â§ADR-020 (look for the
  "Notes / known scope remaps" section with the 10-row remap table)
- compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md Â§Block 0 (head note
  immediately above the | # | Capability | ... | table â€” it now points
  readers to ADR-020 for the remap)
- compact_v5/_phase_2/wave_6/TEST_DESIGN.md Â§Block 0 (now has
  "Implementation notes" subsection)
- compact_v5/MAIN/agent/sagemaker_agent.py (PORT_LOG ref now #038)

FINAL: APPROVE | APPROVE_WITH_FIXES | REJECT.
codex
Reviewing Block 0 iteration #2 now against the same three axes and focusing on the four updated files plus the prior review note. Iâ€™ll first load the exact sections you listed, then verify whether each original finding is fully closed and check for regressions or new issues.
web search: 
web search: 
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path '_status/codex_reviews/block-0.md'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/_status/V5_DESIGN_DECISIONS.md'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/_phase_2/wave_6/TEST_DESIGN.md'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "Get-Content -Path 'compact_v5/MAIN/agent/sagemaker_agent.py'" in D:\Github\sagemaker-coding-agent
2026-05-02T22:54:54.880007Z ERROR codex_core::exec: exec error: windows sandbox: setup refresh failed with status exit code: 0xc0000142
2026-05-02T22:54:54.996262Z ERROR codex_core::exec: exec error: windows sandbox: setup refresh failed with status exit code: 0xc0000142
2026-05-02T22:54:55.000119Z ERROR codex_core::exec: exec error: windows sandbox: setup refresh failed with status exit code: 0xc0000142
2026-05-02T22:54:55.276213Z ERROR codex_core::tools::router: error=execution error: Io(Custom { kind: Other, error: "windows sandbox: setup refresh failed with status exit code: 0xc0000142" })
 exited -1 in 0ms:
execution error: Io(Custom { kind: Other, error: "windows sandbox: setup refresh failed with status exit code: 0xc0000142" })
 exited -1 in 0ms:
execution error: Io(Custom { kind: Other, error: "windows sandbox: setup refresh failed with status exit code: 0xc0000142" })
 exited -1 in 0ms:
execution error: Io(Custom { kind: Other, error: "windows sandbox: setup refresh failed with status exit code: 0xc0000142" })
2026-05-02T22:54:55.293049Z ERROR codex_core::exec: exec error: windows sandbox: setup refresh failed with status exit code: 0xc0000142
2026-05-02T22:54:55.415251Z ERROR codex_core::tools::router: error=execution error: Io(Custom { kind: Other, error: "windows sandbox: setup refresh failed with status exit code: 0xc0000142" })
2026-05-02T22:54:55.422978Z ERROR codex_core::exec: exec error: windows sandbox: setup refresh failed with status exit code: 0xc0000142
2026-05-02T22:54:55.535016Z ERROR codex_core::tools::router: error=execution error: Io(Custom { kind: Other, error: "windows sandbox: setup refresh failed with status exit code: 0xc0000142" })
2026-05-02T22:54:55.651551Z ERROR codex_core::tools::router: error=execution error: Io(Custom { kind: Other, error: "windows sandbox: setup refresh failed with status exit code: 0xc0000142" })
 exited -1 in 0ms:
execution error: Io(Custom { kind: Other, error: "windows sandbox: setup refresh failed with status exit code: 0xc0000142" })
 exited -1 in 0ms:
execution error: Io(Custom { kind: Other, error: "windows sandbox: setup refresh failed with status exit code: 0xc0000142" })
2026-05-02T22:54:55.772060Z ERROR codex_core::tools::router: error=execution error: Io(Custom { kind: Other, error: "windows sandbox: setup refresh failed with status exit code: 0xc0000142" })
codex
I hit an environment issue: every shell read failed with `windows sandbox: setup refresh failed (0xc0000142)`. Iâ€™m retrying with a minimal command to confirm whether command execution is currently unavailable across the board.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command Get-Location in D:\Github\sagemaker-coding-agent
2026-05-02T22:55:01.266936Z ERROR codex_core::exec: exec error: windows sandbox: setup refresh failed with status exit code: 0xc0000142
2026-05-02T22:55:01.385442Z ERROR codex_core::tools::router: error=execution error: Io(Custom { kind: Other, error: "windows sandbox: setup refresh failed with status exit code: 0xc0000142" })
 exited -1 in 0ms:
execution error: Io(Custom { kind: Other, error: "windows sandbox: setup refresh failed with status exit code: 0xc0000142" })
mcp: codex/list_mcp_resources started
mcp: codex/list_mcp_resources (completed)
codex
Shell execution is still unavailable, so Iâ€™m checking whether I can access this repo through the GitHub connector as a fallback to still complete the re-review from source files.
mcp: codex_apps/github_search_repositories started
mcp: codex_apps/github_search_repositories (completed)
mcp: codex_apps/github_fetch_file started
mcp: codex_apps/github_fetch_file (failed)
mcp: codex_apps/github_fetch_file started
mcp: codex_apps/github_fetch_file (failed)
mcp: codex_apps/github_fetch_file started
mcp: codex_apps/github_fetch_file (failed)
mcp: codex_apps/github_fetch_file started
mcp: codex_apps/github_fetch_file (failed)
mcp: codex_apps/github_fetch_file started
mcp: codex_apps/github_fetch_file (failed)
mcp: codex_apps/github_search started


exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"APPROVE|UNDECLARED_PATTERN|test-design drift|PORT_LOG|FINDING|AXIS\" 'compact_v5/_status/codex_reviews/block-0.md'" in D:\Github\sagemaker-coding-agent
 succeeded in 781ms:
17:APPROVE_WITH_FIXES with [HIGH] UNDECLARED_PATTERN on no-deferrals
18:evidence, [MEDIUM] test-design drift, and [LOW] PORT_LOG #036 typo.
37:(3) [LOW] sagemaker_agent.py docstring corrected: PORT_LOG #036 → #038.
56:- compact_v5/MAIN/agent/sagemaker_agent.py (PORT_LOG ref now #038)
58:FINAL: APPROVE | APPROVE_WITH_FIXES | REJECT.

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"ADR-020|Notes / known scope remaps|\\| 0-1 \\||\\| 0-10 \\||no-deferrals|Lock test\" 'compact_v5/_status/V5_DESIGN_DECISIONS.md'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"Build-time remap|ADR-020|Constraint #3|\\| 0-1 \\||\\| 0-10 \\|\" 'compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"### Block 0|Implementation notes|manual exec\\(\\)|papermill|ConsoleChatUI|WidgetChatUI|ADR-017\" 'compact_v5/_phase_2/wave_6/TEST_DESIGN.md'" in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"PORT_LOG|#038|shim\" 'compact_v5/MAIN/agent/sagemaker_agent.py'" in D:\Github\sagemaker-coding-agent
 succeeded in 926ms:
34:> **Build-time remap** (added 2026-05-02 per ADR-020): only item 0-1 (shim) lands inside Block 0. Items 0-2 through 0-10 keep their PORT_LOG origin here but are *implemented* in the Block that owns the touched module. Per-item landing Block + lock test in `_status/V5_DESIGN_DECISIONS.md` §ADR-020 → "Notes / known scope remaps". Constraint #3 (no deferrals) is honored by an explicit per-item landing Block + test gate, not by silent push-out.
38:| 0-1 | SYSTEM_PROMPT verbatim re-export (V1 gap #6) | v4 | sagemaker_agent.py:8029-8189 | 0 (ref) | MUST | CLEAN | Add doc-only PORT_LOG row + ensure shim re-exports. v5 already has `prompt/*.md` (Phase 6) which covers this; FALSE-POSITIVE-AT-CODE-LEVEL but DOC-GAP — add row to plan. |
47:| 0-10 | `_scan_for_prompt_injection` + `_INJECTION_PATTERNS` v4 baseline (V1 gap #5) | v4 | sagemaker_agent.py:7509-7541 | 40 | MUST | CLEAN-FIT | Plan v3 line 343 incorrectly defers as Hermes-adoption follow-up; this is v4-native, not Hermes. Port verbatim. |

 succeeded in 958ms:
1127:## ADR-020 — Block 0 (v5.0.1): `sagemaker_agent.py` shim + notebook smoke gate
1187:### Notes / known scope remaps (constraint #3 — no deferrals)
1194:table is the no-deferrals contract.
1196:| Item | Capability | LOC | Lands in Block | Implementation site (target file) | Lock test (Block where it runs) |
1198:| 0-1 | SYSTEM_PROMPT verbatim re-export | 0 (doc) | Block 0 | `prompt/*.md` (Phase 6, present) + this PORT_LOG row #038 | `test_v4_import_compat` (Block 0) |
1207:| 0-10 | `_scan_for_prompt_injection` + `_INJECTION_PATTERNS` (v4-native) | 40 | **Block C** | `security/injection_scanner.py` (v4 verbatim port from sagemaker_agent.py:7509-7541) | `test_injection_scanner_v4_native` (Block C; already in TEST_DESIGN §Block C) |

 succeeded in 937ms:
1:"""v4-compatibility shim — `sagemaker_agent` re-exports v5's public surface.
10:proper v5 modules; here we only re-bind names. The shim's only job is the
19:PORT_LOG: see #038 (Block 0 shim).

 succeeded in 964ms:
16:| **T3 Notebook smoke** | open `chat.ipynb` headlessly via `papermill` or `jupyter nbconvert --execute`, run cells 1-3, assert no error | every Block close | $0 |
27:2. T3 smoke green (notebook cells 1-3 + open WidgetChatUI without error)
39:### Block 0 — `sagemaker_agent.py` shim + notebook smoke gate
45:| `test_chat_ipynb_cells_1_3` | T3 | chat.ipynb cells 1-3 parse + execute against mock Bedrock without exception (cell 1 = pip install, parse-only; cells 2-3 = exec under mock_mode=True). Equivalent to `papermill` for the smoke surface; chosen because papermill is not in the v5 ship-zip dep set and Bedrock smoke does not need a real kernel. | $0 |
46:| `test_widget_chat_ui_renders` | T2 | `create_chat_ui()` returns a chat-UI handle wired to a real Agent. Accepts `WidgetChatUI` (with non-empty `_panel`) when ipywidgets is installed; falls back to `ConsoleChatUI` (with non-empty `render()`) when ipywidgets is unavailable — matches Phase 11 ADR-017 fallback contract. | $0 |
51:**Implementation notes (post-Block-0 — Codex AXIS A finding #2 lock)**:
52:- T3 is implemented with manual `exec()` of cell sources rather than papermill. Reason: papermill pulls in jupyter_client + ipykernel + nbclient as install-time deps (~50 MB), which the v5 ship zip does not carry, and the smoke surface (parse + exec under mock_mode) does not require a live kernel. The implementation pre-snapshots every CONFIG field via `monkeypatch` so cell 2's CONFIG mutations don't leak into other tests (this caught a real test-isolation bug at Block 0 build time).
53:- T2 accepts ConsoleChatUI fallback because the Phase 11 factory branches on ipywidgets availability (`_IPYWIDGETS_OK`). On a CI runner without ipywidgets, the WidgetChatUI branch is unreachable; the fallback is the production behavior and is what users with no widget host will see.
120:| `test_ipywidgets_fallback_text_mode` | T2 | when `ipywidgets` unavailable, `WidgetChatUI` falls back to `ConsoleChatUI` with `ask_user`-text-mode for approvals (60s watchdog timeout) | $0 |
491:papermill chat.ipynb out.ipynb                   # T3

codex
I’ve validated the exact line anchors for the remap note, the 0-1..0-10 table entries, and the Block 0 test-design implementation notes. I’m doing one final consistency pass for potential new drift before giving the final verdict.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "''^'"\\| 0-[0-9]+ \\|\" 'compact_v5/_status/V5_DESIGN_DECISIONS.md'" in D:\Github\sagemaker-coding-agent
 succeeded in 687ms:
1198:| 0-1 | SYSTEM_PROMPT verbatim re-export | 0 (doc) | Block 0 | `prompt/*.md` (Phase 6, present) + this PORT_LOG row #038 | `test_v4_import_compat` (Block 0) |
1199:| 0-2 | `getSessionStartDate()` + `getLocalMonthYear()` (cache-stable date) | 15 | **Block E+F** | `prompt/env_block.py` (formatter for `prompt/env_block.md`) | `test_env_block_uses_month_year_not_iso_date` (Block E+F) |
1200:| 0-3 | `BEDROCK_EXTRA_PARAMS_HEADERS` Set | 5 | **Block B** | `runtime/bedrock_client.py` (constant + reference at invoke site) | `test_extra_params_in_body_not_headers` (Block B) |
1201:| 0-4 | env block format (Windows-shell hint, OS version, Notes appendix) | 30 | **Block E+F** | `prompt/env_block.md` + `prompt/env_block.py` | `test_env_block_includes_shell_hint_and_notes` (Block E+F) |
1202:| 0-5 | `getScratchpadInstructions()` per-session scratchpad dir | 30 | **Block C** | `security/scratchpad.py` + allowlist update + `prompt/scratchpad.md` | `test_scratchpad_dir_pre_allowlisted_and_gc` (Block C) |
1203:| 0-6 | `getKnowledgeCutoff(modelId)` Sonnet 4.6 / Haiku 4.5 cutoffs | 5 | **Block E+F** | `prompt/env_block.py` (cutoff lookup table) | `test_env_block_emits_model_specific_knowledge_cutoff` (Block E+F) |
1204:| 0-7 | `cleanupRegistry` graceful-shutdown for SIGINT / atexit | 15 | **Block B+** | `runtime/cleanup_registry.py` + `runtime/session.py` flush hook | `test_cleanup_registry_flushes_on_atexit_and_sigint` (Block B+) |
1205:| 0-8 | `validateBoundedIntEnvVar` env-validation helper | 30 | **Block B** | `runtime/env_validation.py` (used by Config dataclass numeric loaders) | `test_env_validation_clamps_and_rejects_bad_input` (Block B) |
1206:| 0-9 | Feature-flag fail-closed at import boundary | 30 | **Block B+** | `runtime/feature_flags.py` (returns False for banned modules) + `entry.py` import-time guard | `test_banned_module_imports_fail_closed` (Block B+) |
1207:| 0-10 | `_scan_for_prompt_injection` + `_INJECTION_PATTERNS` (v4-native) | 40 | **Block C** | `security/injection_scanner.py` (v4 verbatim port from sagemaker_agent.py:7509-7541) | `test_injection_scanner_v4_native` (Block C; already in TEST_DESIGN §Block C) |

codex
**Findings**
No new findings.

- [HIGH] `UNDECLARED_PATTERN` is closed: ADR-020 now declares all `0-1..0-10` rows with explicit landing Block + implementation site + lock test (`compact_v5/_status/V5_DESIGN_DECISIONS.md` lines 1198-1207) and explicitly frames this as the no-deferrals contract (lines 1187-1196).  
- [HIGH] Cross-reference closure is present in synthesis: Block 0 head note now points to ADR-020 remap table and states Constraint #3 is satisfied via explicit landing Block + test gate (`compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` line 34).  
- [MEDIUM] Test-design drift is addressed for Block 0: manual `exec()` rationale and `ConsoleChatUI` fallback rationale are now documented in the Block 0 implementation notes (`compact_v5/_phase_2/wave_6/TEST_DESIGN.md` lines 51-53), and reflected in Block 0 test rows (lines 45-46).  
- [LOW] PORT_LOG typo is fixed: shim docstring now references `#038` (`compact_v5/MAIN/agent/sagemaker_agent.py` line 19).

**A/B/C Re-check**
- Axis A (errors): clean on reviewed fix-up scope.  
- Axis B (v5 fit): clean; remap preserves architecture ownership while keeping Block-0 traceability.  
- Axis C (reference coverage): clean; remap evidence is now explicit and test-anchored per item.

**FINAL: APPROVE**
2026-05-02T22:56:29.542735Z ERROR codex_core::session: failed to record rollout items: thread 019deae6-f60d-75e2-a583-5d5b24c18432 not found
tokens used
51,510
**Findings**
No new findings.

- [HIGH] `UNDECLARED_PATTERN` is closed: ADR-020 now declares all `0-1..0-10` rows with explicit landing Block + implementation site + lock test (`compact_v5/_status/V5_DESIGN_DECISIONS.md` lines 1198-1207) and explicitly frames this as the no-deferrals contract (lines 1187-1196).  
- [HIGH] Cross-reference closure is present in synthesis: Block 0 head note now points to ADR-020 remap table and states Constraint #3 is satisfied via explicit landing Block + test gate (`compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` line 34).  
- [MEDIUM] Test-design drift is addressed for Block 0: manual `exec()` rationale and `ConsoleChatUI` fallback rationale are now documented in the Block 0 implementation notes (`compact_v5/_phase_2/wave_6/TEST_DESIGN.md` lines 51-53), and reflected in Block 0 test rows (lines 45-46).  
- [LOW] PORT_LOG typo is fixed: shim docstring now references `#038` (`compact_v5/MAIN/agent/sagemaker_agent.py` line 19).

**A/B/C Re-check**
- Axis A (errors): clean on reviewed fix-up scope.  
- Axis B (v5 fit): clean; remap preserves architecture ownership while keeping Block-0 traceability.  
- Axis C (reference coverage): clean; remap evidence is now explicit and test-anchored per item.

**FINAL: APPROVE**
