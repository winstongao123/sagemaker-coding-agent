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
| **T5 Real-Bedrock single round-trip** | `RUN_REAL_BEDROCK=1 pytest tests/integration/test_real_bedrock_smoke.py::test_<name>` — one Haiku-4.5 round-trip per test | gated, only on 6 high-risk Blocks + Block J | ~$0.005-0.05 each |
| **T6 User acceptance** | YOU run a real task in SageMaker chat.ipynb with `session_cost_limit=$2.00` | per Block, after I commit | depends on session |

---

## Pass/fail criteria

A Block ships only when ALL of:
1. Every T1 + T2 test green
2. T3 smoke green (notebook cells 1-3 + open WidgetChatUI without error)
3. T4 zip extract+import green
4. T5 real-Bedrock smoke green (only for high-risk Blocks)
5. Codex 3-axis review APPROVE on the diff
6. T6 user acceptance — you say "go" to next Block

Any single failure = stop, fix, re-test, re-Codex, re-approve.

---

## Per-Block test plan

### Block 0 — `sagemaker_agent.py` shim + notebook smoke gate

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_smoke_imports` | T1 | `from sagemaker_agent import CONFIG, BEDROCK_MODELS, create_chat_ui` succeeds | $0 |
| `test_smoke_no_cso_warnings` | T1 | running shim with default LOG_LEVEL emits 0 WARNING-level CSO-CHECK lines (closes PS#1) | $0 |
| `test_chat_ipynb_cells_1_3` | T3 | `papermill chat.ipynb out.ipynb` runs cells 1-3 without exception | $0 |
| `test_widget_chat_ui_renders` | T2 | `create_chat_ui()` returns a `WidgetChatUI` object with non-empty `_panel` | $0 |
| `test_v4_import_compat` | T1 | every name v4 chat.ipynb references (`CONFIG.session_cost_limit`, `BEDROCK_MODELS`, etc.) is re-exported | $0 |

**Block 0 ships when**: 5/5 green. **Total AWS cost: $0.**

---

### Block B — TokenTracker + AuditLogger + SnapshotManager + Runnable tokenEstimation

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

### Block B+ — SessionManager + cost-limit + AGENT_STATUS + FileCache thread-local

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_session_manager_atomic_save` | T1 | save → tmp file → atomic rename; partial-write doesn't corrupt | $0 |
| `test_session_save_load_preserves_cost` | T1 | save at $2.09 → load → `TOKENS.session_cost == 2.09` (closes PS#5) | $0 |
| `test_session_cost_limit_blocks_at_100pct` | T1 | when `session_cost > session_cost_limit`, agent halts with explicit message | $0 |
| `test_agent_status_auto_load` | T1 | first `Agent.run()` call reads `AGENT_STATUS.md` and injects into system prompt | $0 |
| `test_filecache_thread_local_isolation` | T2 | parent `_FILES_READ` not visible inside sub-agent thread context (uses verified v4 APIs `save_and_clear_context` + `enter_thread_local_context`) | $0 |
| `test_subagent_token_attribution` | T2 | spawn parent + sub-agent → assert `TOKENS.parent_input_tokens > 0` AND `TOKENS.subagent_input_tokens["build"] > 0` AND `session_cost == sum_of(per_agent_cost) ± $0.0001` | $0 |
| `test_tokens_singleton_is_budget_source` | T1 | budget checks read TOKENS singleton, NOT Agent attribute (closes PS#6) | $0 |

**Block B+ ships when**: 7/7 green. **Total AWS cost: $0.**

---

### Block C — Runtime safety + secret scanner + JSON repair + injection scan + bash hardening

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_exec_limit_200_then_201_blocked` | T2 | run 200 mocked bash → 201st returns exact error including `OTHER TOOLS STILL WORK: read_file, grep, glob, edit_file, write_file, notebook_edit, task, ask_user, view_image, web_fetch are NOT counted by this limit.` (closes PS#7) | $0 |
| `test_repetition_detector_blocks_3rd_dup` | T2 | same `read_file(path=X)` 3 times → 3rd blocked with dedup message | $0 |
| `test_security_manager_blocks_dangerous_rm` | T1 | `bash("rm -rf /")` returns DANGER block message | $0 |
| `test_security_manager_blocks_etc_passwd` | T1 | `read_file("/etc/passwd")` returns PATH-VALIDATION block | $0 |
| `test_security_manager_blocks_aws_destroy` | T1 | `bash("aws s3 rm s3://prod --recursive")` blocked | $0 |
| `test_secret_scanner_38_patterns` | T1 | each of 38 secret patterns (13 v4 + 25 from Runnable) detects + redacts in test fixture | $0 |
| `test_json_repair_malformed_args` | T1 | `_repair_tool_call_arguments({"foo":"bar)` → `{"foo":"bar"}` (Hermes :547-641); empty `{}` fallback if irrecoverable | $0 |
| `test_injection_scanner_v4_native` | T1 | `_scan_for_prompt_injection` detects v4's 12 patterns + invisible chars (v4:7509-7541) | $0 |
| `test_files_read_thread_local_save_restore` | T1 | `save_and_clear_context()` + `restore_context()` + `enter_thread_local_context()` all from v4:893-1017 verbatim | $0 |
| `test_quote_normalization_curly_to_straight` | T1 | edit_file with `"foo"` matches `"foo"` (curly quotes) (R1 #115) | $0 |
| `test_utf16_bom_detected` | T1 | edit_file on Notepad-saved file (UTF-16 LE BOM) handled correctly (R1 #121) | $0 |
| `test_unc_path_skip_windows` | T1 | `\\\\server\\share\\file.txt` rejected on Windows (NTLM credential leak prevention) (R1 #123) | $0 |

**Block C ships when**: 12/12 green. **Total AWS cost: $0.**

---

### Block C+ — Approval/diff + rate limits + ipywidgets fallback + PermissionDialog richer

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_approval_gate_blocks_until_approve` | T2 | write_file with `require_tool_approval=True` blocks; mock approve → unblocks | $0 |
| `test_approval_dialog_shows_diff` | T2 | `pending_approval` UI renders colored diff (red/green/gray context) | $0 |
| `test_approval_per_tool_always_allow` | T2 | "Always allow" sets `_always_allowed[tool_name]=True`; subsequent calls skip dialog | $0 |
| `test_rate_limit_100_per_min` | T2 | 101st message in 60s window → rate-limit error with countdown | $0 |
| `test_stop_button_halts_run` | T2 | `Agent.stop()` mid-tool-loop sets stop flag; QueryEngine respects it | $0 |
| `test_ipywidgets_fallback_text_mode` | T2 | when `ipywidgets` unavailable, `WidgetChatUI` falls back to `ConsoleChatUI` with `ask_user`-text-mode for approvals (60s watchdog timeout) | $0 |
| `test_permission_dialog_reason_prompt` | T2 | dialog shows model's "reason" string from tool_use args | $0 |

**Block C+ ships when**: 7/7 green. **Total AWS cost: $0.**

---

### Block D — Slash commands (19 advertised + /auth + /simplify expander + /init + /init-verifiers + /skillify + /dream + /promote-to-skill)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_slash_dispatch_/cost` | T2 | `/cost` returns formatted 4-line cost block | $0 |
| `test_slash_dispatch_/status` | T2 | `/status` returns status with model + active skills + phase | $0 |
| `test_slash_dispatch_/save_<name>` | T2 | `/save mywork` writes `sessions/mywork.json` with full state | $0 |
| `test_slash_dispatch_/load_<name>` | T2 | `/load mywork` restores state including `TOKENS.session_cost` | $0 |
| `test_slash_dispatch_/compact` | T2 | `/compact` invokes `Compactor.compact()` (Block A trigger) | $0 |
| `test_slash_dispatch_/clean` | T2 | `/clean` removes `audit_logs/` + `sessions/` + `.snapshots/` files | $0 |
| `test_slash_dispatch_/skills_list` | T2 | `/skills` lists all 10 skills | $0 |
| `test_slash_dispatch_/skill_use_clara` | T2 | `/skill use clara` resolves `clara` → `clara-review` (fuzzy from Block I) | $0 |
| `test_slash_dispatch_/skill_apply_proposal` | T2 | `/skill apply <name>` shows diff + applies | $0 |
| `test_slash_dispatch_/revert_<file>` | T2 | `/revert path/to/file.py` rolls back to last snapshot | $0 |
| `test_slash_dispatch_/context` | T2 | `/context` shows token/context bloat diagnostic | $0 |
| `test_slash_dispatch_/verify_quick` | T2 | `/verify quick` invokes verify skill | $0 |
| `test_slash_dispatch_/checkpoint_create_v1` | T2 | `/checkpoint create v1` snapshots all touched files | $0 |
| `test_slash_dispatch_/checkpoint_restore_v1` | T2 | `/checkpoint restore v1` rolls back all to v1 state | $0 |
| `test_slash_dispatch_/phase_text` | T2 | `/phase Phase 2 build` sets work-phase tag in status bar | $0 |
| `test_slash_dispatch_/diffs_summary` | T2 | `/diffs summary` shows session edit history summary | $0 |
| `test_slash_dispatch_/regression` | T2 | `/regression` runs `git diff HEAD --stat` + suggests test cmd | $0 |
| `test_slash_dispatch_/done_quick` | T2 | `/done quick` runs simplify → verify pipeline → READY-TO-SHIP verdict | $0 |
| `test_slash_dispatch_/commands` | T2 | `/commands` lists custom commands from `agent_config.json` | $0 |
| `test_slash_dispatch_/auth_token` | T2 | `/auth <token>` validates against `os.getenv(CONFIG.auth_token_env)` (when `require_auth=True`) | $0 |
| `test_slash_dispatch_/simplify_falls_through_to_skill` | T2 | `/simplify` (no dedicated handler) hits expander at `:11330` → resolves to `skills/simplify/SKILL.md` | $0 |
| `test_slash_dispatch_/dream_invokes_consolidation` | T2 | `/dream` invokes Block H+ memory consolidation (manual-only) | $0 |
| `test_slash_dispatch_/init_scaffolds_claude_md` | T2 | `/init` generates project CLAUDE.md from interactive prompt | $0 |
| `test_slash_dispatch_/skillify_captures_session` | T2 | `/skillify` runs 4-round AskUserQuestion → saves new skill | $0 |
| `test_slash_dispatch_/promote_to_skill` | T2 | `/promote-to-skill` writes proposal to `state/skill-proposals/` | $0 |
| `test_dispatcher_unknown_slash_falls_through` | T2 | `/unknown_command` not in registry → falls through to chat (not error) | $0 |

**Block D ships when**: 26/26 green. **Total AWS cost: $0.**

---

### Block A — Compactor + cold-cache + auto-compact (COMBINED v4 + Runnable)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_compactor_2stage_prune_plus_llm_summary` | T2 | mocked LLM summary; assert prune step removes tool outputs older than threshold; LLM step generates 13-section template | $0 |
| `test_microcompact_threshold_70pct` | T2 | when `total_tokens / context_window > 0.70` → microcompact fires | $0 |
| `test_context_collapse_threshold_85pct` | T2 | when > 0.85 → context_collapse fires | $0 |
| `test_cold_cache_30min_idle_triggers_microcompact` | T2 | mock `time.time()` to simulate 30min idle → next msg → microcompact fires + log line `[i] Cold cache detected` (closes PS#3) | $0 |
| `test_keep_last_n_cold_cache_1` | T2 | after cold-cache compact, only last 1 message retained | $0 |
| `test_post_compact_files_read_clear` | T2 | after compact, `_FILES_READ.clear()` runs (model can re-read files) | $0 |
| `test_post_compact_todo_restoration_message` | T2 | after compact, `build_todo_restoration_message` injected | $0 |
| `test_auto_compact_circuit_breaker_3_failures` | T2 | 3 consecutive `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES` → autoCompact disabled with warning | $0 |
| `test_cache_edits_per_tool_invalidation` | T2 | per-tool schema hash change → only that tool's cache invalidated | $0 |
| `test_a28_cache_invariant_no_mid_session_rebuild` | T2 | system prompt rebuild attempted mid-conversation → blocked with warning (`/cmd --now` opt-in only) | $0 |
| `test_h2_stub_injection_for_orphan_tool_use` | T2 | post-compact, dangling `tool_use` block → synthetic `tool_result` stub injected (prevents Bedrock 400) | $0 |
| `test_compact_fires_real_haiku_long_context` | T5 | real Haiku-4.5 round-trip with 80K+ token input → triggers compact → next call succeeds | ~$0.01 |

**Block A ships when**: 12/12 green. **Total AWS cost: ~$0.01.**

---

### Block E+F — HTML chat rendering + cell 2 widgets + complete session UI + IterationBudgetWidget + ThinkingBudgetWidget

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_render_chat_user_message` | T1 | `render_chat()` produces HTML with user message in correct color | $0 |
| `test_render_chat_assistant_markdown` | T1 | `_render_assistant_markdown()` converts markdown → HTML (code blocks, tables, lists) | $0 |
| `test_render_todos_status_icons` | T1 | TODO list renders with ✅/🔄/⬜ icons | $0 |
| `test_update_tokens_display_shows_pct` | T1 | token display shows `X / Y (Z%)` and `cache hit %` | $0 |
| `test_update_mode_display_status_bar` | T1 | status bar shows model + active skills + phase + cost | $0 |
| `test_dark_mode_toggle_swaps_theme` | T2 | dark-mode toggle swaps theme dict; chat re-renders | $0 |
| `test_model_dropdown_lists_all_models` | T2 | dropdown contains Haiku-4.5 + Sonnet-4.6 + Opus options | $0 |
| `test_iteration_budget_widget_shows_used_total` | T1 | widget HTML shows `<progress>` + `used/total` + color cue (closes PS#2 visible UI) | $0 |
| `test_thinking_budget_widget_shows_on_off` | T1 | widget HTML shows `thinking=ON\|OFF, budget=N tokens` (closes PS#4 visible UI) | $0 |
| `test_session_dropdown_lists_saves` | T2 | session dropdown lists all `sessions/*.json` files | $0 |
| `test_session_load_button_restores` | T2 | clicking load → `SessionManager.load()` → state restored | $0 |
| `test_auto_save_on_send` | T2 | every send auto-saves to `last_session.json` | $0 |
| `test_long_text_details_collapse` | T1 | text > 5000 chars wrapped in `<details><summary>show more</summary>...</details>` (Wave 6 GAP fix) | $0 |
| `test_thinking_config_sent_every_call` | T1 | mocked BedrockClient.chat: thinking config in every payload (closes PS#4) | $0 |

**Block E+F ships when**: 14/14 green. **Total AWS cost: $0.**

---

### Block F2 — Auto-continuation under iteration budget

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_f2_auto_continue_at_under_90pct` | T2 | iteration_used < 90% AND not diminishing-returns → auto-continue | $0 |
| `test_f2_blocks_at_90pct` | T2 | iteration_used >= 90% → halts + asks user | $0 |
| `test_f2_respects_cost_cap` | T2 | even if iteration_used < 90%, if `session_cost > session_cost_limit` → halt | $0 |

**Block F2 ships when**: 3/3 green. **Total AWS cost: $0.**

---

### Block I — Skill name resolution + Hermes fuzzy + paths frontmatter + scaffolders

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_skill_resolve_by_directory_name` | T1 | `/skill use clara-review` → loads `skills/clara-review/SKILL.md` | $0 |
| `test_skill_resolve_by_metadata_name` | T1 | `/skill use Clara` (metadata `name: Clara`) → loads `skills/clara-review/` | $0 |
| `test_skill_fuzzy_match_typo` | T1 | `/skill use verfy` → fuzzy resolves to `verify` (Hermes :4689-4720) | $0 |
| `test_skill_paths_frontmatter_auto_activate` | T2 | skill with `paths: ["*.py"]` auto-activates when user edits .py file | $0 |
| `test_skill_disable_model_invocation` | T2 | skill with `disable_model_invocation: true` not visible to model but callable by user | $0 |
| `test_skill_enabled_when_config_flag` | T2 | skill with `enabled_when: CONFIG.advanced_mode` only loads when flag True | $0 |
| `test_skillify_4_round_interview` | T2 | `/skillify` runs 4 AskUserQuestion rounds → writes `skills/<new>/SKILL.md` | $0 |
| `test_skill_manager_realpath_dedup` | T1 | symlink to same dir loaded once (R9 #23 bug fix) | $0 |

**Block I ships when**: 8/8 green. **Total AWS cost: $0.**

---

### Block M — Phase 8 critical fixes (per-turn discovery reset + structured-output retry counter)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_discovered_tool_names_reset_per_turn` | T1 | `self._discovered_tool_names` resets at start of each turn (not just run-start) | $0 |
| `test_structured_output_retry_limit_3` | T1 | `countToolCalls` blocks at retry limit 3 → halts with explicit message | $0 |
| `test_infinite_loop_blocked_at_retry_limit` | T2 | model returns malformed structured output 3x → halt | $0 |

**Block M ships when**: 3/3 green. **Total AWS cost: $0.**

---

### Block G — AGENT_TYPES + worktree + handoff/env

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_agent_types_dict_has_7` | T1 | `AGENT_TYPES.keys() == {build, plan, explore, verify, general, review, fork}` | $0 |
| `test_subagent_build_spawns_worktree` | T2 | `task(subagent_type="build")` creates `worktrees/<id>/` (mocked git) | $0 |
| `test_subagent_verify_loads_verify_skill` | T2 | `task(subagent_type="verify")` loads verify skill in sub-agent context | $0 |
| `test_subagent_handoff_block_built` | T1 | `_build_subagent_handoff_block()` produces v4-equivalent text | $0 |
| `test_subagent_env_details_built` | T1 | `_build_subagent_env_details()` includes cwd + git status + tool list | $0 |
| `test_max_subagent_depth_2_blocks_grandchild` | T2 | parent → child OK; child → grandchild blocked with `MAX_SUBAGENT_DEPTH=2` error (Wave 6 GAP fix) | $0 |
| `test_iteration_budget_shared_object_identity` | T2 | parent and sub-agent share SAME `IterationBudget` object (object identity check) | $0 |
| `test_worktree_cleanup_on_completion` | T2 | sub-agent completion removes worktree | $0 |

**Block G ships when**: 8/8 green. **Total AWS cost: $0.**

---

### Block G3 — Coordinator System Prompt (NEW)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_coordinator_prompt_contains_4_phases` | T1 | system prompt for `task` tool contains "Research → Synthesis → Implementation → Verification" | $0 |
| `test_coordinator_prompt_synthesize_dont_delegate` | T1 | prompt contains "NEVER delegate understanding" | $0 |
| `test_coordinator_prompt_continue_vs_spawn_table` | T1 | prompt contains continue-vs-spawn decision table | $0 |
| `test_coordinator_prompt_research_parallel_write_serial` | T1 | prompt contains "Read-only tasks: run in parallel; Write tasks: one at a time" | $0 |
| `test_coordinator_prompt_real_haiku_orchestration` | T5 | real Haiku-4.5 round-trip: prompt agent to coordinate 3 sub-agents → assert it spawns parallel reads, serial writes | ~$0.01 |

**Block G3 ships when**: 5/5 green. **Total AWS cost: ~$0.01.**

---

### Block G2 — forkSubagent cache-prefix replay

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_forkSubagent_byte_identical_prefix` | T1 | parent + child API requests have BYTE-identical prefix when `cache_prefix_share=True` | $0 |
| `test_forkSubagent_cache_aware_serialization` | T1 | message serialization deterministic (sorted keys, no random IDs in prefix) | $0 |
| `test_g2_cache_prefix_real_bedrock` | T5 | real Bedrock call: parent + child → second call cache_read_input_tokens > 0 (cache hit verified) | ~$0.01 |

**Block G2 ships when**: 3/3 green. **Total AWS cost: ~$0.01.**

---

### Block H — Memory extraction (COMBINED v4 + Runnable extractMemories + sessionMemory)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_extract_and_append_memories_v4_session_end` | T1 | session-end trigger writes new entries to `memory.md` (v4 behavior) | $0 |
| `test_extract_memories_closure_scoped_state` | T1 | extractMemories has closure-scoped throttle state (Runnable pattern) | $0 |
| `test_session_memory_dedup_before_write` | T1 | `sessionMemoryUtils` deduplicates before writing memory.md | $0 |
| `test_adjust_index_preserves_api_invariants` | T1 | `adjustIndexToPreserveAPIInvariants` returned indices keep tool_use/tool_result paired (R4 #56 MUST) | $0 |
| `test_memory_extraction_handles_empty_session` | T1 | session with 0 user messages → no extraction, no error | $0 |
| `test_session_memory_compact_no_400_sequence` | T2 | compact run on session with mixed tool_use/tool_result → resulting messages valid for Bedrock | $0 |

**Block H ships when**: 6/6 green. **Total AWS cost: $0.**

---

### Block H+ — Memory consolidation engine (`/dream` MANUAL ONLY, no daemon)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_dream_4_phase_prompt_orient_gather_consolidate_prune` | T1 | dream prompt contains 4 phases in correct order | $0 |
| `test_dream_lock_file_prevents_concurrent_runs` | T1 | `dream.lock` file blocks 2nd `/dream` invocation | $0 |
| `test_dream_rollback_on_failure` | T2 | mid-run failure → `memory.md.bak` restored; original `memory.md` untouched | $0 |
| `test_dream_no_daemon_no_auto_fire` | T1 | search v5 codebase: no `Thread`/`asyncio.create_task`/`atexit.register(dream)`/`SAGEMAKER_AUTO_DREAM` env var (verifies user decision 2026-05-01) | $0 |
| `test_dream_real_consolidation_haiku` | T5 | real `/dream` invocation on test memory.md → outputs cleaner file (~$0.05) | ~$0.05 |

**Block H+ ships when**: 5/5 green. **Total AWS cost: ~$0.05.**

---

### Block L — Error/retry/cache-break + Bedrock guardrails + daemon-thread call

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_categorize_retryable_18_error_types` | T1 | each of 18 Runnable error categories → correct retryable verdict (R4 18 categories) | $0 |
| `test_parse_max_tokens_overflow_recovers` | T1 | `parseMaxTokensContextOverflowError` triggers compact + retry (R4 #2 MUST) | $0 |
| `test_extract_nested_error_message_humanizes_5xx_html` | T1 | Bedrock 5xx with raw HTML → user sees clean error message (R4 #9 MUST) | $0 |
| `test_retry_after_header_parsed` | T1 | `getRetryAfterMs` parses `Retry-After: 5` → 5000ms wait | $0 |
| `test_per_tool_cache_break_detection` | T1 | per-tool schema hash change → `notifyCacheDeletion` fires for that tool only | $0 |
| `test_haiku_excluded_from_cache_break_3loc` | T1 | Haiku-4.5 model_id in EXCLUDED set → cache-break detector skips (R4 #14 MUST) | $0 |
| `test_daemon_thread_bedrock_call_responds_to_ctrl_c` | T2 | Bedrock call wrapped in daemon thread; main thread Ctrl-C raises KeyboardInterrupt cleanly | $0 |
| `test_30s_heartbeat_during_long_call` | T2 | heartbeat ping every 30s during long call → status bar updates | $0 |

**Block L ships when**: 8/8 green. **Total AWS cost: $0.**

---

### Block N — Parallel tool execution + dynamic tool refs + dedup + fuzzy + ephemeral prompt

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_parallel_exec_3_independent_reads` | T2 | 3 read_file calls dispatched in parallel → completion in MAX(call_time), not SUM | $0 |
| `test_parallel_exec_path_conflict_serializes_writes` | T2 | 2 write_file to same path → serialized (not parallel) | $0 |
| `test_tool_call_dedup_blocks_redundant` | T2 | same `(tool_name, args)` 3x in one batch → 2 calls deduped | $0 |
| `test_fuzzy_tool_name_typo_resolves` | T1 | `read_filee` → fuzzy resolves to `read_file` | $0 |
| `test_ephemeral_system_prompt_not_persisted` | T1 | ephemeral prompt fragment not written to session log | $0 |
| `test_dynamic_tool_ref_injection_at_init` | T1 | tool schemas at init have cross-references injected (Hermes A36) | $0 |
| `test_max_tool_workers_4` | T1 | `_MAX_TOOL_WORKERS=4` constant; 5 parallel calls → 4 in flight + 1 queued | $0 |
| `test_n7_partial_tool_names_warning_on_disconnect` | T2 | mid-call disconnect → warning + synthetic tool_result stub | $0 |
| `test_n_real_3_parallel_reads_haiku` | T5 | real Bedrock 3 parallel read_file calls → wallclock < SUM (validate ~40% gain) | ~$0.005 |

**Block N ships when**: 9/9 green. **Total AWS cost: ~$0.005.**

---

### Block T — v4 tool surface parity (11 missing tools)

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
| `test_tool_web_fetch_html_to_markdown` | T2 | mocked HTTP response → `web_fetch` returns markdown text | $0 |
| `test_tool_ask_user_blocks_then_unblocks` | T2 | `ask_user` blocks until user responds; mock response unblocks | $0 |
| `test_tool_create_html_via_write_file_documented` | T1 | docs note: `create_html` not a separate tool; use `write_file(*.html)` (Wave 6 design note) | $0 |

**Block T ships when**: 11/11 green. **Total AWS cost: $0.**

---

### Block J — Real-Bedrock smoke + zip extract+import (THE SHIP GATE)

This is THE final gate before tagging. **All real-AWS testing concentrates here.**

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_zip_rebuild_succeeds` | T4 | `python _rebuild_zip.py` produces `compact_v5.zip` | $0 |
| `test_zip_extract_in_tmpdir` | T4 | `verify_ship_zip.py` extracts zip in fresh tmpdir | $0 |
| `test_zip_python_c_import_entry` | T4 | `python -c "import entry"` succeeds in extracted dir | $0 |
| `test_zip_python_c_import_sagemaker_agent` | T4 | `python -c "import sagemaker_agent; sagemaker_agent.create_chat_ui()"` succeeds | $0 |
| `test_real_bedrock_hello_world` | T5 | real Haiku-4.5 round-trip: send "say hello", assert non-empty text response | ~$0.005 |
| `test_real_bedrock_tool_use_round_trip` | T5 | real Haiku-4.5: send "list files in /tmp", assert tool_use(name="list_dir") + tool_result + final text | ~$0.005 |
| `test_real_bedrock_compact_then_continue` | T5 | real call with 80K-token preamble → compact fires → next call succeeds with reduced prefix | ~$0.01 |

**Block J ships when**: 7/7 green. **Total AWS cost: ~$0.02.**

This block + the per-block T5 tests = total ~$0.10 across the entire build.

---

### Block K — Process discipline (LF AXIS C + per-block user gate + STATE/RESUME + 3-critic + A44 test refactor)

| Test | Tier | Assertion | Cost |
|---|---|---|---|
| `test_axis_c_template_present` | T4 | `_status/CODEX_REVIEW_TEMPLATE.md` contains AXIS A + AXIS B + AXIS C sections | $0 |
| `test_state_resume_anchor_per_block` | T4 | every Block tag has corresponding `V5_BUILD_STATUS.md` "Last commit sha" matching | $0 |
| `test_per_block_user_approval_gate_documented` | T4 | `RESUME.md` Step 5 contains "Tag is FORBIDDEN if any open Codex finding has severity ≥ CHANGES_REQUESTED" | $0 |
| `test_a44_no_change_detector_tests_audit` | T4 | scan `tests/` for `assert "X" in MODELS` / `assert COUNT == N` — fail if found (rewrite as invariant) | $0 |
| `test_lint_phase_id` | T4 | `tests/lint_phase_id.py` validates tag name + status field + codex review filename match | $0 |

**Block K ships when**: 5/5 green. **Total AWS cost: $0.**

---

---

## R-tier — high-value real-AWS scenarios (added 2026-05-01 per user directive)

User directive: "AWS test allowed but must be carefully designed and optimized for v5 to collect MOST value to see if user using it without any semantic bugs."

These are end-to-end USER-SIMULATING scenarios run on real Bedrock. Each has a hard cost cap. Run after Block K (process discipline) lands but before tag.

| # | Scenario | What it catches | Model | Cost cap |
|---|---|---|---|---|
| **R1** | 50-turn dashboard build: read CSV → python_exec to summarize → create_chart → create_word with embedded chart | Tool dispatch round-trips end-to-end, parallel exec wallclock gain on real Bedrock, security gate with real bash, .docx output integrity | Haiku-4.5 | $1.00 |
| **R2** | Long context: load 80K-token preamble → ask "refactor this module" → verify compaction fires + cache_edits invalidates only changed tools | Block A semantic correctness on Bedrock cache; A28 invariant on real cache hit | Haiku-4.5 | $0.50 |
| **R3** | Sub-agent dispatch: parent spawns 3 parallel research sub-agents → synthesize → write report. Verify cache-prefix replay shares cache | Block G + G2 + G3 cache-prefix bytes-stable on real Bedrock | Haiku-4.5 | $0.50 |
| **R4** | 30-min idle: send msg → wait 30min real-time → send next. Verify cold-cache compact fires + saves ≥5K tokens | PS#3 structural fix end-to-end | Haiku-4.5 | $0.20 |
| **R5** | 200-bash: agent loops python_exec 200x. 201st returns exact "OTHER TOOLS STILL WORK" message; agent continues with read_file/grep | PS#7 structural fix end-to-end | Haiku-4.5 | $0.50 |
| **R6** | Memory consolidation: build memory.md to 100 entries → `/dream` → verify deduplication + categorization works | Block H+ semantic correctness; rollback on fail; lock prevents concurrent | Haiku-4.5 | $0.30 |
| **R7** | Model switch mid-conversation: 10 turns on Haiku → user changes dropdown → next turn uses Sonnet. **A28 invariant**: prompt cache NOT rebuilt mid-conversation; switch applies next session | Hermes A28 critical policy on real Bedrock | Haiku→Sonnet | $0.50 |
| **R8** | Error recovery: mock Bedrock return malformed JSON tool args → multi-pass repair works → if irrecoverable, `{}` fallback used + agent continues | Block C JSON repair end-to-end | Haiku-4.5 (mocked) | $0.20 |
| **R9** | Approval flow: write_file → diff_widget renders → user clicks Approve/Deny/Always → decision propagates to TOKENS + AUDIT + SNAPSHOTS | Block C+ approval flow end-to-end | Haiku-4.5 | $0.30 |
| **R10** | Save/load: spend $1 in turns → `/save mytest` → restart kernel → `/load mytest` → verify `TOKENS.session_cost == $1.00` and chat history restored | PS#5 + PS#6 structural fix on real session | Haiku-4.5 | $1.00 |
| **R11** | Sonnet end-to-end: same as R1 but on Sonnet-4.6. Catches model-specific behavior differences | Sonnet-4.6 | $1.50 |
| **R12** | Multi-tool malformed args stress: model returns `{"path": "/tmp/", "content": "<UNCLOSED` → JSON repair fires; model returns surrogate-pair Unicode → sanitizer fires | Block L Bedrock error categories; H1 surrogate sanitize | Haiku-4.5 | $0.20 |

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

**Block K codifies this ritual; it's not a separate test or a separate Block — it runs at every Block close.**

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
6. Try `/cost`, `/status`, `/save mytest`, `/load mytest` — all work
7. **If green**: v5.0.1 acceptance gate PASS

---

## Pass/fail rule (non-negotiable)

A Block tag is FORBIDDEN if ANY:
- T1/T2/T3/T4 test red
- T5 (when applicable) red
- Codex AXIS A/B/C verdict ≠ APPROVE
- You haven't approved the diff

After tag: STATE/RESUME anchor updated, PORT_LOG row materialized, V5_BUILD_STATUS bumped, next Block starts.

**Total estimated build time** (with you reviewing each Block): 2-4 weeks of focused work. **Total estimated cost**: under $5 in AWS. **Confidence after Block J + first 5 real sessions**: ~99%.
