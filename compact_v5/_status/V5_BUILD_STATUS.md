# V5 Build Status

Last updated: 2026-05-04 (**R-tier R1+R2 READY NEAR_IDEAL** — PAUSED per user option (c); resume R3 next session)

Phase ID: R-tier (PHASE 3 of post-Block-K plan)
Last commit sha: a73befc (R2 GENUINE_PASS NEAR_IDEAL 5.00/5 — READY) — pushed sageagent/v5-build

## R-tier progress (2026-05-04 — PAUSED)

**STATUS: PAUSED per user (option c) after R2 NEAR_IDEAL.** Resumable from R3 next session per `compact_v5/docs/PS_V5_TEST_WORKER_FINAL.md`.

| Test | Status | Spend | Notes |
|------|--------|-------|-------|
| R1 | READY (NEAR_IDEAL) | $0.0632 | Composite dashboard build (CSV→summary→chart→docx, 50-turn cap, AU geo). 4 real architectural bugs caught + fixed during PRE-FLIGHT iter1-3: Windows cp1252 Unicode stdout crash, Agent.run not propagating CONFIG.max_tokens/temperature into QueryEngine, AU geo +10% premium under-counted in tokens.py, R-tests blocked by require_tool_approval. AWS calls used: 2 (call#1 $0.03 wasted on Unicode crash, call#2 $0.0332 PASS). |
| R2 | READY (NEAR_IDEAL 5.00/5) | $0.222 | Compactor + auto-compact: 78K-token preamble crosses CONFIG.context_max_tokens=100K threshold; T2 recalls original question via injected [CONVERSATION SUMMARY] block. Strong PASS, no bugs found. AWS calls used: 1 (PASS first call). |
| R3-R17 | pending | — | Resume next session. R3 is next per matrix (multi-file refactor / parallel coordination depending on slot order). |

- **Cumulative R-tier spend: $0.2852 / $14.25 cap (2.0%).**
- HEAD: `a73befc` — `v5/r-tier-R2: GENUINE_PASS NEAR_IDEAL 5.00/5 — READY` (pushed sageagent/v5-build).
- Discipline working: 4 architectural bugs caught during R1 PRE-FLIGHT BEFORE burning AWS — proves the "BOTH worker AND Codex APPROVE before each AWS call" gate is correct.
- Next session resume command: `Read compact_v5/docs/PS_V5_TEST_WORKER_FINAL.md and continue R-tier from R3 (R1+R2 already READY at HEAD a73befc).`

## Block U status (2026-05-03)

**DEFERRED-POST-SHIP per user 2026-05-03**. Code-to-production first.

- Scaffold + archive landed (kept as Block-U-foundation):
  - `compact_v5/HTML/` directory created.
  - `compact_v5/docs/htmls/archive/` with `v4_architecture.html` + `PS_FLOWCHART_V4.html` moved (per WORKER_HINT_2026-05-03.md §3).
- 4 NEW HTMLs DEFERRED (not yet written): `v5_architecture.html`, `PS_FLOWCHART_V5.html`, `v5_complete.html` (7 tabs), `v5_PS_PROBLEMS_FIXED.html`.
- HERMES_VS file rename + v5 column DEFERRED.
- Rationale: HTMLs document a SHIPPED product; building them before R-tier validates v5 risks wasted work if R-tier surfaces a code change. Block U fires after user approves v5.0.1 ship + signs off on R-tier results.
- Block U "R-tier results" tab will be populated with actual R-tier metrics + screenshots from `r_tier_metrics.jsonl`.

## v5.0.1 Block K entry (2026-05-03)

## v5.0.1 Block K entry (2026-05-03)
- Block K — process discipline (LF AXIS C + per-block user gate + STATE/RESUME + 3-critic + A44 test refactor) per TEST_DESIGN §Block K (5 named tests + 1 meta-count = 6 tests, all T4 $0).
- NEW `tests/integration/test_block_k_process.py` (~250 LOC, 6 tests):
  - test_axis_c_template_present
  - test_state_resume_anchor_per_block
  - test_per_block_user_approval_gate_documented
  - test_a44_no_change_detector_tests_audit
  - test_lint_phase_id
  - test_block_k_5_of_5_test_count (meta-count lock)
- UPDATED `_status/CODEX_REVIEW_TEMPLATE.md` — added AXIS C "Reference-repo coverage gaps" section with MUST/DEFER/DROP/N/A disposition categories per LF / WORKER_HINT_2026-05-03.md.
- Codex Block K iter-1 = APPROVE_WITH_FIXES (3 major + 3 minor); iter-2 fixes in progress.
- 781 pass + 17 skip (was 775 + 17 at end of Block J; +6 net for Block K).
- verify_ship_zip PASS (134 files / 377.1 KB / 36%).
- PORT_LOG row + ADR-040 + tag `v5.0.1-block-k` will follow Codex APPROVE.

## v5.0.1 Block J entry (2026-05-03)
- THE SHIP GATE: 7 tests in `tests/integration/test_block_j_ship_gate.py` per TEST_DESIGN §Block J + 1 meta-count lock = 8 tests.
- 4 T4 tests pass on every pytest invocation: zip rebuild + extract + python-c import (entry + sagemaker_agent shim).
- 3 T5 tests env-gated `RUN_REAL_BEDROCK=1` (~$0.02 total): hello-world / tool-use round-trip / compact-then-continue.
- **CAUGHT REAL BUG**: flat-zip layout couldn't import. `entry.py` does `from agent import Agent` but Agent class lived in `__init__.py` (invisible by that name in flat-zip cwd).
- **FIX**: moved `Agent` class + `_load_agent_status_text` from `MAIN/agent/__init__.py` to `MAIN/agent/agent.py` (real module). `__init__.py` rewritten as thin re-export via `from .agent import Agent` (relative import).
- Works in BOTH source layout (tests put `MAIN/agent` on sys.path → finds `agent.py` directly) AND flat-zip layout (`agent.py` at root).
- PORT_LOG #104 + ADR-039.
- 775 pass + 17 skip (was 770 + 14; +5 net pass for Block J T4 + 3 net skip for T5 env-gated).
- verify_ship_zip PASS (133 files / 376.0 KB / 36%).

## v5.0.1 Block T entry (2026-05-03)
- **10 of 11 v4 tools active** across 5 new files (constraint #5 minimum-file): tools/v4_documents.py (create_word/excel/markdown/notebook/chart/pdf, 6 tools consolidated) + tools/todo.py (todo_write + todo_read) + tools/semantic_search.py + tools/web_fetch.py (DISABLED — see below) + tools/ask_user.py.
- **web_fetch DECISION-DROP-PER-USER 2026-05-03**: ships disabled in v5.0.1 (module-level `raise NotImplementedError` guard + bootstrap import commented out). v5 single-user SageMaker context typically VPC-isolated; web_fetch active = SSRF surface for zero benefit. NOT silent narrowing — explicit user override; PORT_LOG row 103-A. Re-enable steps documented in tools/web_fetch.py docstring.
- Lazy-import pattern: external libs (python-docx / openpyxl / matplotlib / requests / sklearn) imported at execute time. Tool registration always succeeds; missing lib returns Error.
- create_html intentionally NOT a separate tool — use write_file with .html ext (Wave 6 design note).
- WIRED tools/__init__.py to register the 10 active tools in bootstrap_built_ins (web_fetch line commented + flagged "DISABLED 2026-05-03").
- iter-2 schema parity: create_word adds title/include_toc/header/footer; create_excel adds sheet_name/chart_title/x_column/y_columns + accepts list-of-dicts data; create_pdf adds title/page_size + accepts v4 per-block data; create_chart accepts {labels,values}.
- iter-2 path validation fix: `_validate_doc_path` now uses `SECURITY.validate_path()` (was `_resolve_path` which is a path-join helper, not a gate). All 6 doc creators write to `abs_path` returned by validation. requires_approval=True for all 6.
- 19+ tests in tests/integration/test_block_t.py: 10 active-tool tests + 4 v4-shape locks (word v4 fields / excel v4 dict-shape / pdf v4 blocks / out-of-workspace reject) + 2 web_fetch-disabled locks (module-import-raises / not-in-registry) + create_html-doc + 2 todo behavior locks + 1 active-set registry lock + iter-3 chart/empty-payload locks. (Active SSRF test removed when web_fetch was disabled — SSRF logic remains in unreachable code in tools/web_fetch.py for forward re-enable.)
- Block G3 test test_coordinator_user_context_NOT_injected_for_subagent updated to use coordinator-specific markers (Phase-7 deferred-tool reminder legitimately mentions create_word now).
- PORT_LOG #103 + #103-A + ADR-038.
- 764 pass + 14 skip (was 745 + 14 baseline; +19 pass net new).

## v5.0.1 Block N entry (2026-05-03)
- NEW `core/parallel_dispatch.py` (~150 LOC): MAX_TOOL_WORKERS=4 + dedup_tool_calls + detect_path_conflicts + fuzzy_resolve_tool_name + mark_ephemeral_block + strip_ephemeral_blocks_for_persist + inject_dynamic_tool_refs + synthetic_tool_result_stub + partial_tool_call_warning.
- EXTENDED core/__init__.py with re-exports.
- 11 tests + 3 deferred (parallel-exec timing → Block J real-AWS, T5 real-Haiku → R-tier R3) per ADR-037.
- PORT_LOG #102 + ADR-037.
- 743 pass + 14 skip; verify_ship_zip PASS (128 files / 361.1 KB).

## v5.0.1 Block L entry (2026-05-03)
- EXTENDED `core/errors.py` (~150 LOC): BedrockErrorCategory 9→18 categories + categorize_retryable + extract_nested_error_message (R4 #9 MUST) + parse_max_tokens_context_overflow_error (R4 #2 MUST) + get_retry_after_ms.
- NEW `core/cache_break_detection.py` (~120 LOC): hash_tool_schema + PerToolCacheBreakDetector + is_cache_break_excluded(model_id) (R4 #14 MUST: Haiku exclusion w/ cross-region prefix stripping) + notify_cache_deletion.
- EXTENDED `core/__init__.py`: re-exports.
- 9 new tests in `tests/integration/test_block_l.py` + 2 T2 deferred (daemon-thread + 30s heartbeat → Block J real-AWS gate per ADR-036 §3): 6 TEST_DESIGN-named (18-categories / max-tokens-recovers / humanizes-5xx-html / retry-after / per-tool-cache-break / haiku-excluded) + 3 behavior locks (classifier-recognizes-new-cats / hash-deterministic / notify-skips-excluded).
- PORT_LOG rows #100-#101 + ADR-036.
- `verify_ship_zip.py`: PASS (127 files / 357.2 KB / 36%).
- Pytest: **729 passed + 11 skipped** (was 720 + 9 at Block H+; +9 pass + 2 skip net new).

## v5.0.1 Block H+ entry (2026-05-03)
- NEW `runtime/dream.py` (~250 LOC): DREAM_PROMPT_TEMPLATE (4 phases: Orient → Gather → Consolidate → Prune+Index) + DreamLock (file-based with stale-recovery >600s) + run_dream(workspace, consolidator) + get_dream_prompt + DreamResult + _backup_memory_md + _restore_from_backup. **MANUAL TRIGGER ONLY per user decision 2026-05-01** — daemon scheduler / asyncio / atexit / env auto-enable INTENTIONALLY DROPPED.
- 11 new tests + 1 T5 skip in `tests/integration/test_block_h_plus.py`: 4 TEST_DESIGN-named (4-phases-prompt / lock-prevents-concurrent / rollback-on-failure / no-daemon-no-auto-fire) + 1 T5 skip + 6 behavior locks. The "no-daemon-no-auto-fire" test grep-scans the entire agent codebase for forbidden patterns — fails if any leak in.
- PORT_LOG row #099 + ADR-035.
- `verify_ship_zip.py`: PASS (126 files / 350.6 KB / 36%).
- Pytest: **717 passed + 9 skipped** (was 706 + 8 at Block H; +11 pass + 1 skip net new).

## v5.0.1 Block H entry (2026-05-03)
- NEW `memory/` package (~450 LOC): memory/extract.py (MemoryExtractor + closure-scoped throttle state) + memory/session_memory.py (dedup + has_tool_calls_in_last_assistant_turn + count_tool_calls_since) + memory/compact.py (adjust_index_to_preserve_api_invariants H-11 MUST + calculate_messages_to_keep_index + has_text_blocks).
- 16 new tests in `tests/integration/test_block_h.py`: 6 TEST_DESIGN-named (extract-and-append-v4-session-end / closure-scoped-state / dedup-before-write / adjust-index-preserves-api-invariants / handles-empty-session / compact-no-400-sequence) + 10 behavior locks (isolated-state / preserves-casing / no-op-when-safe / dangling-tool-use-handled / calc-keep-index / has-tool-calls-predicate / count-tool-calls-since / drain-pending / has-text-blocks / scan-memory-files).
- PORT_LOG rows #095-#098 + ADR-034.
- ADR-034 §4 explicitly defers H-13/H-15/H-16/H-17 (SM-compact config knobs) + H-18/H-19/H-20 (CLAUDE.md context aggregation, getSystemContext, onboarding) — NO silent scope narrowing; both groups have target blocks + rationale documented.
- `verify_ship_zip.py`: PASS (125 files / 346.6 KB / 36%).
- Pytest: **703 passed + 8 skipped** (was 687 + 8 at Block G2; +16 pass net).

## v5.0.1 Block G2 entry (2026-05-03)
- NEW `subagent/fork.py` (~210 LOC): is_in_fork_child + build_child_message + build_forked_messages + serialize_for_cache_prefix + cache_prefix_match_length helpers + FORK_BOILERPLATE_TAG / FORK_PLACEHOLDER_RESULT verbatim from Runnable.
- EXTENDED `subagent/__init__.py`: re-exports new fork surface.
- 8 new tests + 1 T5 skip in `tests/integration/test_block_g2.py`: 3 TEST_DESIGN-named (byte-identical-prefix / cache-aware-serialization / real-bedrock skipped) + 6 behavior locks (placeholder-text-constant / fork-detection / no-tool-use-fallback / directive-only-in-last-block / parent-history-preserved / non-assistant-parent-rejected).
- PORT_LOG row #094 + ADR-033.
- ADR-033 §4: spawn_subagent wiring for agent_type="fork" deferred to Block L (real-Bedrock cache-prefix exercise has architectural fit there).
- `verify_ship_zip.py`: PASS (121 files / 338.9 KB / 36%).
- Pytest: **687 passed + 8 skipped** (was 679 + 7 at Block G3; +8 pass + 1 skip net new).

## v5.0.1 Block G3 entry (2026-05-03)
- NEW `coordinator/` module (~250 LOC): coordinator/system_prompt.py (4-phase orchestrator block) + coordinator/user_context.py (worker-tools + scratchpad description) + __init__.py.
- EXTENDED `runtime/config.py`: `coordinator_mode_enabled: bool = False` flag (default OFF) + `_SCALAR_FIELDS` row.
- WIRED `core/query_engine.py.run()`: append-only coordinator block when `CONFIG.coordinator_mode_enabled AND agent_kind=="parent"`. Best-effort try/except so missing module doesn't block run.
- 11 new tests in `tests/integration/test_block_g3.py`: 4 TEST_DESIGN-named (4-phases / synthesize-not-delegate / continue-vs-spawn / parallel-research-serial-write) + 1 T5 skip (real-Haiku orchestration deferred to R-tier R3) + 4 user-context tests + 3 engine-wiring locks (appended-when-on / not-appended-when-off / not-appended-for-subagent).
- PORT_LOG rows #092-#093 + ADR-032.
- `verify_ship_zip.py`: PASS (120 files / 334.7 KB / 36%).
- Pytest: **675 passed + 7 skipped** (was 664 + 6 at Block G; +11 pass + 1 skip net new).

## v5.0.1 Block G entry (2026-05-03)
- NEW `subagent/agent_types.py` (~180 LOC): AgentType dataclass with `allowed_tools` field + AGENT_TYPES dict (7 entries) + DEFAULT_AGENT_PROMPT + SUBAGENT_NOTES + ONE_SHOT_BUILTIN_AGENT_TYPES + _READ_ONLY_TOOLS / _VERIFY_TOOLS allowlists + get_agent_type/get_agent_prompt(is_coordinator).
- NEW `subagent/worktree.py` (~120 LOC): create_worktree() + cleanup_worktree() with 3-tier fallback (git → fallback_copy → fallback_tempdir).
- EXTENDED `subagent/spawn.py`: per-type max_turns clamping + worktree creation for build with CONFIG.workspace swap (build agents actually run inside the worktree, restored in finally) + verify-skill auto-load + tool allowlist filtering (no `task` for restricted agents — would bypass allowlist via build-child).
- EXTENDED `tools/task.py`: JSON-schema enum + per-type description + validation against full AGENT_TYPES.
- EXTENDED `subagent/__init__.py`: re-exports new public surface.
- 22 new tests in `tests/integration/test_block_g.py`: 8 TEST_DESIGN-named + 6 initial behavior locks + 6 iter-2 finding-locks (build-runs-in-worktree / explore-allowlist / plan-allowlist / verify-allowlist / general-full-registry / task-schema-lists-7) + 2 iter-3 finding-locks (restricted-agents-no-task-allowlist / explore-no-task-end-to-end).
- Codex AXIS A/B/C 3-iter cycle (gpt-5.5 -c model_reasoning_effort=high throughout):
  - iter 1: REJECT — 1 BLOCKER (worktree CONFIG.workspace not swapped) + 1 HIGH (allowlist prompt-only) + 1 MEDIUM (task description "general only") + 1 DOC (G-1/G-2 deferral undeclared).
  - iter 2: REJECT — 1 HIGH (`task` in restricted allowlist let explore spawn build) + 1 MEDIUM (loose test assertion).
  - iter 3: **APPROVE** — clean. (`_status/codex_reviews/block-g-iter3.md`).
- PORT_LOG rows #086-#091 + ADR-031.
- `verify_ship_zip.py`: PASS (117 files / 329.5 KB / 36%).
- Pytest: **664 passed + 6 skipped** (was 642 + 6 at Block M; +22 pass net).

## v5.0.1 Block M entry (2026-05-03)
- EXTENDED `core/query_engine.py`: count_tool_calls() helper + 2 new QueryEngine ctor params (synthetic_output_tool_name, max_structured_output_retries; both default OFF) + per-turn retry-limit gate emitting stop_reason="error_max_structured_output_retries" + per-run discoveredSkillNames reset (skill_manager._pending_activations.clear() at run() entry; best-effort try/except).
- EXTENDED `core/__init__.py`: re-exports count_tool_calls.
- 11 new tests in `tests/integration/test_block_m.py`: 5 pure-function (count_tool_calls edge cases — empty / no-match / multi-match / ignores user-role / handles string content) + 3 TEST_DESIGN-named (discovered-tool-names-reset-per-turn / structured-output-retry-limit-3 / infinite-loop-blocked-at-retry-limit) + 3 behavior locks (default-off-no-halt / clamp-to-min-1 / baseline-captured-from-prior-session).
- PORT_LOG rows #084-#085 + ADR-030.
- `verify_ship_zip.py`: PASS (115 files / 322.2 KB / 36%).
- Pytest: **642 passed + 6 skipped** (was 631 + 6 at Block I; +11 pass net).

## v5.0.1 Block I entry (2026-05-03)
- EXTENDED `skills/manager.py` (~280 LOC): SkillInfo + paths/disable_model_invocation/enabled_when fields + discover() realpath dedup + new frontmatter parsing + activate_for_path() + resolve_name() (Hermes fuzzy) + list_model_invocable/list_user_invocable + substitute_skill_vars().
- WIRED `core/query_engine.py`: dispatch context now passes skill_manager + session_id to tools; get_active_skill_prompt(session_id) wired to substitute ${CLAUDE_SKILL_DIR} / ${CLAUDE_SESSION_ID}.
- WIRED `tools/edit_file.py`: post-write activate_for_path() hook (best-effort; never blocks edit).
- WIRED `tools/skill.py`: list uses list_model_invocable; read/activate reject disable_model_invocation skills (Codex iter-1 #2).
- WIRED `commands.py`: cmd_skill_use now routes through resolve_name() (replaces prior startswith-3-letter suggestion).
- NEW `skills/debug/SKILL.md` (Block I-10) + `skills/remember/SKILL.md` (Block I-11, disable_model_invocation:true).
- 21 new tests in `tests/integration/test_block_i.py` + 1 symlink test skipped on Windows: 8 TEST_DESIGN-named + 8 behavioral locks + 5 Codex iter-1 finding-locks.
- Codex AXIS A/B/C 3-iter cycle (gpt-5.5 -c model_reasoning_effort=high throughout):
  - iter 1 (initial Block I): APPROVE_WITH_FIXES — 4 code findings (paths/**-descendants, disable_model_invocation in discover_relevant + skill tool, I-6 substitution unwired, first-match-wins) + 1 doc finding (PORT_LOG #082 missing I-12 deferral / verify remap / gap #8).
  - iter 2 (4 code fixes + PORT_LOG #083 added): APPROVE_WITH_FIXES — 2 findings (loose first-match test, PORT_LOG #072 lost Notes column with F2 spillover into #083).
  - iter 3 (test tightened + PORT_LOG row repair): **APPROVE** — clean. (`_status/codex_reviews/block-i-iter3.md`).
- PORT_LOG rows #073-#083 + ADR-029.
- Block I-12 (frontmatter parser improvements) explicitly deferred to Block N per ADR-029 §6. Wave 6 gap #8 tool-vs-skill precedence documented in PORT_LOG #083.
- `verify_ship_zip.py`: PASS (115 files / 321.2 KB / 36%).
- Pytest: **631 passed + 6 skipped** (was 610 + 5 at Block F2; +21 pass + 1 skip net).

## v5.0.1 Block F2 entry (2026-05-03)
- NEW `core/budget_continuation.py` (~145 LOC): BudgetTracker + check_iteration_budget + get_budget_continuation_message + COMPLETION_THRESHOLD=0.9 + DIMINISHING_THRESHOLD=2 (iteration-adapted from Runnable's 500 tokens).
- EXTENDED `runtime/config.py`: `enable_token_budget_continuation: bool = False` (default OFF per Wave 6 NLT row #21 opt-in contract) + `_SCALAR_FIELDS` row.
- WIRED `core/query_engine.py`: at the no-tool_calls (end_turn) branch, before `stop_reason = "end_turn"; break`. Best-effort try/except (logs warning on raise per Codex iter-1 #2). StopDecision telemetry logged + AUDIT.log("budget_continuation_stop") for cost_cap/diminishing/above_threshold paths (per Codex iter-1 #1). Sub-agents always halt (parent-only). Cost-cap halt has priority. `self._budget_tracker = None` reset at run() entry.
- 20 new tests in `tests/integration/test_block_f2.py`:
  - 7 pure-function tests + 3 TEST_DESIGN-named + 4 behavioral locks (initial 14).
  - 3 iter-2 finding-locks (StopDecision audit / exception-logged / snapshot-restore-pattern).
  - 3 iter-3 finding-locks (pct in completion_event for cost_cap / diminishing / above_threshold).
- Codex AXIS A/B/C 3-iter cycle (gpt-5.5 -c model_reasoning_effort=high throughout):
  - iter 1 (3 files initial): APPROVE_WITH_FIXES — 3 findings (StopDecision telemetry / silent F2 swallow / test globals snapshot pattern).
  - iter 2 (4 files iter-2 fix): APPROVE_WITH_FIXES — 2 findings (meta-lock test still violated rule it locked / completion_event missing pct).
  - iter 3 (4 files iter-3 fix): **APPROVE** — clean. Findings: none. (`_status/codex_reviews/block-f2-iter3.md`).
- PORT_LOG row #072 + ADR-028. Closes Wave 6 NLT row #21 (cost-cap + opt-in contracts).
- `verify_ship_zip.py`: PASS (113 files / 314.4 KB / 36%).
- Pytest: **610 passed + 5 skipped** (was 590 + 5 at Block E+F; +20 pass net).

## v5.0.1 Block E+F entry (2026-05-03)
- NEW `prompt/env_block.py` (~125 LOC): get_session_start_date (lru_cached) + get_local_month_year + get_knowledge_cutoff (5-model lookup + cross-region prefix strip) + get_os_string + get_shell_hint + render_env_block.
- 15 new tests in `tests/integration/test_block_e_f.py` (12 initial + 3 finding-locks for iter-1) covering all 3 ADR-020 remap rows + integration into build_system_prompt + session-start memoization + POSIX shell hint.
- WIRED `prompt/__init__.py` build_system_prompt: render_env_block now spliced into dynamic tail (with ctx["skip_env_block"] opt-out for tests).
- Codex AXIS A/B/C 2-iter cycle (gpt-5.3-codex throughout):
  - iter 1 (2 files): REJECT with 3 findings (HIGH integration gap, MEDIUM session-start mismatch, LOW POSIX shell test).
  - iter 2 (3 files): APPROVE — all 3 fixes verified clean.
- PORT_LOG row #071 + ADR-027. Closes ADR-020 §Notes / known scope remaps rows 0-2 + 0-4 + 0-6.
- Phase 6/11 prompt surface unchanged (no regressions).
- `verify_ship_zip.py`: PASS (112 files / 311.0 KB / 37%).
- Pytest: **590 passed + 5 skipped** (was 575 + 5 at Block A; +15 pass net).

## v5.0.1 Block A entry (2026-05-03)
- NEW `core/compactor.py` (~430 LOC): Compactor (v4 port lines 186-635) + AutoCompactCircuitBreaker + apply_cache_control_to_blocks + count_tokens_via_haiku_fallback (B-2 remap) + _summary_client advisor attribution (B+5 remap).
- 25 new tests in `tests/integration/test_block_a.py` (21 initial + 4 finding-locks for iter-1) covering estimate / prune / should_compact / compact / create_llm_summary / run end-to-end + circuit-breaker cooldown + cache_control + B-2 fallback + B+5 advisor cost attribution + 4 finding-locks (PTL user-first, PRUNE_MIN_SAVINGS rollback, CB atomic try_attempt, query_engine wiring).
- WIRED `core/query_engine.py`: per-turn auto-compact gate (Compactor.should_compact + AUTO_COMPACT.try_attempt + Compactor.run when allowed; emits "[auto-compact] saved N tokens; continuing." or "[auto-compact skipped: <reason>]").
- Codex AXIS A/B/C 2-iter cycle (gpt-5.3-codex throughout):
  - iter 1 (3 files): REJECT with 4 findings (HIGH PTL retry user-first; MEDIUM PRUNE_MIN_SAVINGS rollback lost; MEDIUM CB atomicity; MEDIUM helpers unwired).
  - iter 2 (4 files): APPROVE — all 4 fixes verified clean.
- PORT_LOG rows #066-#070 + ADR-026. Closes B-2 (Block B deferred → Block A) + B+5 (Block B+ deferred → Block A).
- `verify_ship_zip.py`: PASS (111 files / 308.1 KB / 37%).
- Pytest: **575 passed + 5 skipped** (was 550 + 5 at Block D; +25 pass net).

## v5.0.1 Block D entry (2026-05-03)
- NEW `commands.py` (~450 LOC): 27-command dispatch table + handler functions + CommandResult shape.
- WIRED `ui/chat_ui.py` (ConsoleChatUI + WidgetChatUI): pre-agent dispatch when message starts with `/`.
- 24 canonical commands: 17 v4 advertised + /auth + 6 LF additions; +1 alias (/skill suggestion) for v4-parity per sagemaker_agent.py:10874 = 25 in full listing.
- 22 new tests in `tests/integration/test_block_d.py` (19 initial + 3 finding-locks for iter-1/iter-2) covering dispatch table, /auth env match/mismatch/skipped, all major handlers, ConsoleChatUI routing, /revert all safety, alias routing, canonical count exactness.
- Codex AXIS A/B/C 4-iter cycle (gpt-5.3-codex throughout):
  - iter 1 (3 files): APPROVE_WITH_FIXES with 2 findings (1 HIGH /revert all safety + 1 MEDIUM accounting drift).
  - iter 2 (3 files): APPROVE_WITH_FIXES — finding #2 still inconsistent (27-vs-24 mismatch).
  - iter 3 (2 files): REJECT — inner docstring still claimed 26/27.
  - iter 4 (1 file): APPROVE — inner docstring also reconciled.
- PORT_LOG row #065 + ADR-025.
- `verify_ship_zip.py`: PASS (110 files / 300.9 KB / 37%).
- Pytest: **550 passed + 5 skipped** (was 528 + 5 at Block C+; +22 pass net).

## v5.0.1 Block C+ entry (2026-05-03)
- NEW `ui/approval_dialog.py` (~280 LOC): PermissionDialog + RateLimiter + ApprovalResult.
- WIRED `core/query_engine.py`: rate-limit gate at run() entry (returns stop_reason="rate_limited"); approval gate before tool.execute() (gated on require_tool_approval + tool.requires_approval + NOT client.mock_mode).
- 17 new tests in `tests/integration/test_block_c_plus.py` (14 initial + 3 finding-locks for iter-1) covering all 7 TEST_DESIGN §Block C+ items + 4 Block-C remap locks (cd+git/multi-cd/pipe-segment/comment-label) + 3 lifecycle locks + 3 real-path locks (dispatch diff capture, Windows watchdog, non-TTY fallback).
- Codex AXIS A/B/C 2-iter cycle (gpt-5.3-codex throughout):
  - iter 1 (3 files): REJECT with 3 findings (2 HIGH wiring, 1 MEDIUM test coverage).
  - iter 2 (4 files): APPROVE — all 3 fixes verified clean.
- PORT_LOG row #064 + ADR-024. Closes ADR-023 §Notes / known scope remaps for Block-C UI items.
- `verify_ship_zip.py`: PASS (109 files / 293.5 KB / 37%).
- Pytest: **528 passed + 5 skipped** (was 511 + 5 at Block C; +17 pass net).

## v5.0.1 Block C entry (2026-05-03)
- 5 NEW security helper modules: json_repair (~115 LOC), injection_scanner (~100 LOC), scratchpad (~110 LOC), edit_file_safety (~190 LOC), bash_safety (~225 LOC).
- EXTENDED `security/manager.py` SECRET_PATTERNS 13→38 (R5 A1, 25 gitleaks patterns added).
- WIRED `tools/edit_file.py` (UNC reject + UTF-16 BOM detection + quote norm + line-ending round-trip), `tools/bash.py` (exit-code semantics annotation), `core/query_engine.py` (exec-limit gate PS#7 fix + repetition detector + JSON repair on tool_use.input).
- 21 new tests in `tests/integration/test_block_c.py` (17 initial + 4 finding-locks for iter-1) covering all 12 TEST_DESIGN §Block C items + 2 ADR-020 remap lock tests + 3 helper-coverage tests + 4 finding-locks.
- Codex AXIS A/B/C 2-iteration cycle (gpt-5.3-codex throughout):
  - iter 1 (6 files): APPROVE_WITH_FIXES with 4 findings (2 HIGH wiring, 2 MEDIUM correctness).
  - iter 2 (5 files): APPROVE — all 4 fixes verified clean.
- PS#7 STRUCTURALLY ADDRESSED: exec-limit gate emits v4 verbatim "OTHER TOOLS STILL WORK" message; lock test test_exec_limit_200_then_201_blocked.
- PORT_LOG rows #057-#063 + ADR-023. Closes Block 0 ADR-020 remap rows 0-5 (scratchpad) + 0-10 (v4-native injection scanner).
- `verify_ship_zip.py`: PASS (108 files / 286.8 KB / 37%).
- Pytest: **511 passed + 5 skipped** (was 490 + 5 at Block B+; +21 pass net).
Updated by: Mode B autonomous build (Codex-only-gate; user reviews FINAL product after Block K + R-tier)

## v5.0.1 Block B+ entry (2026-05-03)
- 4 NEW runtime modules: `runtime/session.py` (~165 LOC), `runtime/file_cache.py` (~165 LOC), `runtime/cleanup_registry.py` (~95 LOC), `runtime/feature_flags.py` (~85 LOC).
- WIRED `core/query_engine.py` (per-run cost runtime warning at 100%+; warn-and-continue per user 2026-05-03 plan update), `subagent/spawn.py` (FILE_CACHE.save_and_clear_context + restore_context try/finally around child.run), `agent/__init__.py` (Agent.run AGENT_STATUS auto-load — once per Agent instance, 8 KB cap, after CACHE_BOUNDARY), `runtime/tokens.py` (cleanup_registry _flush_cost_on_exit registration).
- LAZY @property `_config` on all 4 singletons (TokenTracker / AuditLogger / SnapshotManager / SessionManager) so `importlib.reload(runtime.config)` doesn't strand them.
- 22 new tests in `tests/integration/test_block_b_plus.py` (14 initial + 6 finding-locks for iter-1 + 2 entry-guard locks for iter-2). PS#5 + PS#6 closed end-to-end via test_session_save_load_preserves_cost + test_tokens_singleton_is_budget_source.
- Codex AXIS A/B/C 3-iteration cycle (all gpt-5.3-codex):
  - iter 1 (13 files): APPROVE_WITH_FIXES, 4 findings (1 HIGH + 2 MEDIUM + 1 LOW).
  - iter 2 (5 files): APPROVE_WITH_FIXES on finding #2 (guard false-positive on external mcp).
  - iter 3 (2 files): APPROVE — guard now realpath-rooted; 2 lock tests exercise both branches.
- Removed empty `compact_v5/MAIN/agent/mcp/` placeholder (Phase 0-1 leftover; constraint #9 enforcement).
- PORT_LOG rows #048-#055 + ADR-022. Closes Block-0 ADR-020 remap rows 0-7 (cleanupRegistry) + 0-9 (feature_flags fail-closed) + B+3..B+6 explicit landing-Block remap (B+3/B+4/B+6 → Block I; B+5 → Block A).
- `verify_ship_zip.py`: PASS (103 files / 273.5 KB / 38%).
- Pytest: **490 passed + 5 skipped** (was 469 + 5 at Block B; +21 pass net).

## v5.0.1 Block B entry (2026-05-03)
- 4 NEW runtime modules: `runtime/tokens.py` (~480 LOC), `runtime/audit.py` (~155 LOC), `runtime/snapshot.py` (~135 LOC), `runtime/env_validation.py` (~60 LOC).
- EXTENDED `runtime/bedrock_client.py`: BEDROCK_EXTRA_PARAMS_HEADERS frozenset (3 betas: interleaved-thinking + 1m-context + tool-search) + `count_tokens()` method (B-1, R4 #41 MUST) with thinking-aware body.
- WIRED `core/query_engine.py` (TOKENS.add + AUDIT.log on ALL 4 dispatch paths: success / raised / unknown-tool / plan-mode-blocked + agent_kind/session_id ctor params), `subagent/spawn.py` (agent_type → agent_kind), `tools/edit_file.py` + `tools/write_file.py` (SNAPSHOTS.save best-effort), `runtime/config.py` (env-validation wiring on 5 numeric knobs).
- 28 new tests in `tests/integration/test_block_b.py` (27 pass + 1 T5 skipped). 18 from initial scope + 10 finding-lock tests covering each Codex iter-1 finding.
- Codex AXIS A/B/C iter 1 (gpt-5.5): APPROVE_WITH_FIXES with 6 findings (1 HIGH AU pricing, 1 HIGH dual audit-log paths, 3 MEDIUM, 1 LOW). All 6 fixed; each has 1+ covering lock test.
- Codex iter 2 (gpt-5.3-codex, focused 6-file prompt): **APPROVE** — all 6 fixes verified clean (`_status/codex_reviews/block-b-iter2.md`). gpt-5.5 had hung on the same review; gpt-5.3-codex (the Codex-CLI-tuned variant) completed in ~6 min / 27k tokens.
- PORT_LOG rows #039-#047 + ADR-021. Closes 9 Wave-5-DEEP findings (B-1 / B-3..B-11 / B-13 / R4 #14 / R8 #74) + Block-0 ADR-020 remap rows 0-3 + 0-8.
- PS_problems #5 + #6 STRUCTURALLY ADDRESSED (TokenTracker.restore + singleton-as-budget-source + canonicalize_model_id strips au.).
- `verify_ship_zip.py`: PASS (100 files / 263.6 KB / 38%).
- Pytest: **469 passed + 5 skipped** (was 442 + 4 at Block 0; +27 pass + 1 skip).
- Codex resilience rule codified in `BUILDER_PROMPT.md` §Step 8 (lock-tests-as-fallback under network failure).

## v5.0.1 Block 0 entry (2026-05-02)
- `compact_v5/MAIN/agent/sagemaker_agent.py` (NEW, 31 LOC): re-exports v5's public surface at the v4-canonical import path.
- 5 lock tests in `tests/integration/test_block0_shim.py` per TEST_DESIGN §Block 0 — 5/5 green.
- Notebook smoke gate: `test_chat_ipynb_cells_1_3` parses + execs cells 1-3 against mock Bedrock — green.
- PORT_LOG row #038 + ADR-020 added.
- Tagged `v5.0.1-block-0` at commit `19e7823`, pushed to sageagent.
- `verify_ship_zip.py`: PASS (96 files / 249.0 KB compressed / 38% ratio).
- Pytest: **442 passed + 4 skipped** (was 437 + 4 at v5.0.0; +5 net).

## Wave 6 entry (2026-05-01)
- 5 parallel agents brainstormed 25 user-perspective scenarios each (125 raw, 111 unique post-dedup) covering: long sessions / tool failures / multi-file tasks / sub-agents / notebook UX.
- Synthesis: `compact_v5/_phase_2/wave_6/PS_Plan_Edge_Cases_Thinking.md`.
- **Verdict**: 74 HANDLED / 42 NEEDS-LOCK-TEST / 9 POSSIBLE-GAP.
- **All 9 POSSIBLE-GAPs close within existing 21 Blocks** (~45 LOC code + 5 doc rows + 1 ADR; +0.23% plan size).
- 42 NEEDS-LOCK-TEST items distributed across existing per-Block Q4 sections (lock test count 95 → 135, +44%).
- **No new Blocks needed**. Plan v5.0.1 confirmed comprehensive for realistic SageMaker user scenarios.
- Block 0 ready to start.

## Wave 5-DEEP entry (2026-05-01)
- 20 parallel agents read every file in v4 (12,088 LOC) + Runnable (~2010 .ts files) + Hermes (12,880 LOC) + LF tree.
- ~150 net-new findings consolidated in `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md`.
- 233 new PORT_LOG rows (Q1 215 → 448).
- 3 new Blocks: G3 (Coordinator System Prompt), F2 (Auto-Continuation under iteration budget), H+ (Auto-Dream daemon).
- 8 NOT-OPTIONAL correctness fixes flagged (R4 ×5 + H2 stub-injection + H5 A28 cache-invariant + R7 N8 token-accounting).
- 3 Hermes critical policies adopted (A28 cache-invariant, A36 dynamic ref, A44 no-change-detector tests).
- ~80 categorical drops (no v5.0.2 punt; per constraint citation).
- LOC: 11,330 → ~16,200 (1.43x).
- Updated build sequence: `0 → smoke → B → B+ → C → C+ → D → A → E+F → F2 → I → M → G → G3 → G2 → H → H+ → L → N → T → J → K`.
- Reading order for builder: SYNTHESIS_MASTER.md → V5_PHASE_2_PLAN_v3.md (renamed conceptually to v5) → Q1_EVIDENCE_MATRIX.md.
- DONE 2026-05-02: Codex APPROVE_WITH_FIXES on post-DEEP plan → 5 fixes applied (block count, LOC math, Q1 PASS reframing, no-streaming filter EF-6/7 + N-7/8/9 retag, plan body stale tables) → CONFIDENCE_REPORT.md generated. Pre-Block-0 gate MET.

## Phase 2 final state (Q1-Q4 all evidenced)

- **Wave 1 (9 reports)**: high-level v4/Runnable/Hermes/LF audit. ✓ on disk.
- **Wave 2 (11 reports)**: line-by-line, no-skip. ✓ on disk.
- **Wave 3 (3 reports)**: COMBINED_ARCHITECTURE + COMPLETENESS_VERIFY + RISK_SURFACE. ✓ on disk.
- **Wave 4 (4 evidence matrices)**: Q1 (159 rows, 0 missing refs) + Q2 (CERTAIN-NO-RECUR all 7 PS) + Q3 (v5 ≥ Runnable post-no-deferrals; v5 > v4 decisive) + Q4 (26 bug classes locked). ✓ on disk.
- **Codex APPROVE** (gpt-5.5) on plan v3. v3c review final.
- **User APPROVED** plan via ExitPlanMode.
- **INDEX.md**: organized materials reference for builders.

## Plan v4 final state (2026-05-01, Codex APPROVE)

After 4 rounds of Codex (gpt-5.5) review, plan v4 reached APPROVE on all 3 axes (errors / v5 fit / reference-repo coverage). Major changes from v3:
1. **No deferrals**: 5 prior DEFERRED items flipped to PORTED (auto-compact circuit breaker → A; Runnable cache_edits → A; Runnable extractMemories + sessionMemory → H; Hermes AGENTS.md:627-628 → N; Runnable commands dispatcher pattern → D).
2. **Block D expansion (Codex AXIS C)**: 7 → 19 advertised v4 commands + 1 `/auth` auth-gate = 20 inputs (constraint #1 v4.10.10 baseline). Verified line refs at sagemaker_agent.py:8164 + :10789-:11341.
3. **Block T NEW (Codex AXIS C)**: 11 missing v4 tools added (create_word/excel/markdown/notebook/chart/pdf, todo_write/read, semantic_search, web_fetch, ask_user). Both schema + impl line refs verified by grep against v4 source.
4. **Block B+ FileCache class**: now correctly references sagemaker_agent.py:893-1017 with verified APIs save_and_clear_context / restore_context / enter_thread_local_context / exit_thread_local_context.
5. **Sub-agent token attribution acceptance test** added to Block B+.
6. **Total**: ~11,330 LOC across **18 Blocks**: 0 → smoke → B → B+ → C → C+ → D → A → E+F → I → M → G → G2 → H → L → N → T → J → K.

## Sequence (final, 18 blocks)

`Block 0 → notebook smoke gate → B → B+ → C → C+ → D → A → E+F (together) → I → M → G → G2 → H → L → N → T → J → K`

Each block: separate commit + Codex 3-axis review (errors / v5 fit / reference-repo coverage) + per-block user approval gate (Block K discipline) + STATE/RESUME anchor.

**Awaiting user signal to start Block 0** (sagemaker_agent.py shim + notebook smoke gate). Per Block K, each block requires user approval before next starts.

## Where things stand

**v5.0.0 (Phase 1, 14 phases)**: BUILD CANDIDATE — SHIP BLOCKED. Tagged at `30735e1` for traceability only. Failed user verification because of silent scope narrowing across 14 phases. See `_status/V5_SHIP_CRITIQUE.md`.

**Phase 2 (corrective investigation)**: IN PROGRESS.
- **Wave 1 (high-level inventory)**: COMPLETE. 9 agents covered v5-vs-v4 (UI + non-UI parity, including a 2nd cross-checker), v5-vs-Runnable (PORT_LOG honesty + leftover + cross-check + code-experience), Hermes patterns, Learning Factory patterns. All reports in `_phase_2/team_*/AGENT_*_REPORT.md`.
- **Wave 2 (line-by-line, no-skip coverage)**: STARTING. User directive: every important section of every reference repo must be scanned line-by-line. Wave 1 was high-level; Wave 2 is exhaustive.

## Hard constraints from user (consolidated 2026-04-30)

1. **v4.10.10 = baseline.** Functional capability of v4 is the floor. Don't drop v4 features in name of architectural cleanliness.
2. **v4 chat.ipynb = canonical UI.** v5 provides `sagemaker_agent` shim so v4's notebook works unchanged.
3. **Cover ALL repos**: v4 + Runnable + Hermes + Learning Factory. Not subsets.
4. **Line-by-line investigation, no skip.** This is the MUST gate.
5. **Minimum file structures.** Maximum coverage in minimum file count.
6. **Architecture-first.** Pattern adoption from any reference must pass architecture-fit check.
7. **Structurally address PS_problems** (not patch).
8. **v5 > Runnable > v4 > others.** Axis-by-axis evidence required.

## Current acceptance bar (revised)

v5 ships when:
1. **v4 functional parity** (every v4 feature mapped + ported OR explicitly user-approved drop)
2. v4 chat.ipynb works unchanged via `sagemaker_agent` shim
3. Static prompt ≤ 2500 tokens (preserved from original V5_PLAN.md)
4. Per-turn schema overhead ≥ 3000 lower than v4 (preserved)
5. All Runnable patterns FAITHFUL or FAITHFUL-WITH-JUSTIFIED-ADAPTATION
6. **Coverage proof**: every line-by-line agent report has a "what would be missed if not investigated" section
7. **Minimum file count**: justify each file's existence vs alternative consolidation
8. `pytest -q` green
9. Real Bedrock smoke test passes (not just mock)
10. User-verification questions return YES with evidence (the 4-question gate)

## Current phase
- Phase ID: 13 (build mechanically closed)
- Phase name: Phase 13 — Cutover + ship zip + tag v5.0.0
- State: **BUILD CANDIDATE — SHIP BLOCKED**
- See: `_status/V5_SHIP_CRITIQUE.md` for the failure analysis and v5.0.1 patch agenda.

## Why ship is blocked

User verdict (2026-04-30):
> *"Clearly this operation failed. Because all questions unsatisfactory."*
> *"It proves that Claude code is incapable of coding. Because it 1) deferred the requests, without remission 2) not meeting initial goal and design."*

The four user-verification questions exposed:
- Q1 (complete observation + references): PARTIAL — v5 deferred Compactor, TokenTracker, exec-limit enforcement, memory extraction, save/load slash commands, full chat UI without permission.
- Q2 (no PS Issues recur): NO — PS #3, #5, #6 regressed in v5 (no compaction, no cost tracking, no save/load persistence).
- Q3 (better than v4 + Runnable): MIXED — better on architecture, worse on feature coverage. New v5 bug: skill name vs directory mismatch (`/skill activate clara` fails).
- Q4 (no semantic bugs): NO — zero real-Bedrock turns; concurrency unenforced; verify_ship_zip only checks file presence.

Original V5_PLAN.md success metric #1 (functional parity with v4.10.10) is NOT MET. The "minimal MVP" framing in per-phase OUT-OF-SCOPE lists was unilateral scope narrowing, not user-approved deferral.

## Phase 13 summary
- compact_v5.zip built: 95 files / 248.2 KB compressed / 38% ratio.
- verify_ship_zip.py: **RESULT: PASS — zip is ship-ready**.
- README.md + CHANGELOG.md written.
- Empty placeholders: memory.md + AGENT_STATUS.md.
- Final state: 437 pass + 4 skip; aggregate audit all 7 metrics PASS; 19 ADRs / 36 PORT_LOG rows.

## v5 ship state (FINAL)

| Metric | Value | Target | Status |
|---|---|---|---|
| Phases done | 14/14 | 14 | DONE |
| Tests | 437 pass + 4 skip | green | PASS |
| Static prompt | 2498 tokens | ≤ 2500 | PASS |
| Tool count | 14 | ≤ v4 (~30) | PASS |
| Skill count | 10 | = 10 | PASS |
| Aggregate audit | 7/7 | 7/7 | PASS |
| Parity critical | 15/15 | 100% | PASS |
| Parity non-critical | 10/10 | ≥ 90% | PASS |
| ADR-to-PORT_LOG ratio | 19 ADRs / 36 rows | every row → ADR | PASS |
| Codex findings caught | 33 | tracked | all FIXED |

## PS Issues resolved
- #1 (Hermes filter) — Phase 10
- #2 (visible IterationBudget) — Phase 8 data + Phase 11 widget
- #4 (visible thinking budget) — Phase 11 widget
- #7 (tool_classes slot 2) — Phase 6

## Phase 12 summary
- 25 new tests across 2 files: `tests/parity/test_parity_critical.py` (15 scenarios, must-pass 100%) + `tests/parity/test_parity_non_critical.py` (10 scenarios, ≥9/10).
- **Result: 15/15 critical PASS + 10/10 non-critical PASS (100% on both gates)**.
- Documented v4-vs-v5 divergences (all intentional improvements) in PORT_LOG #035 appendix.
- 437 pass + 4 skip (was 412+4 in Phase 11 → +25 net new).
- Phase 12 ships ZERO new production code; gate semantics only.

## Phase 11 summary
- 7 new files: agent/__init__.py (Agent class) + entry.py + ui/chat_ui.py + ui/widgets.py + chat.ipynb + chat.md + tests/integration/test_notebook_smoke.py.
- 1 modified: ui/__init__.py (re-exports).
- 20 new tests (15 initial + 5 Codex-fix lock tests).
- Codex review: APPROVE_WITH_FIXES first pass (1 HIGH + 3 MEDIUM + 1 LOW). All 5 fixed in same commit.
- Post-fix: AXIS A PASS, AXIS B 5 ADAPTED / 0 DRIFTED.
- 412 pass + 4 skip (was 392+4 in Phase 10 → +20 net new).
- **PS Issue #2 (visible budget) RESOLVED** + **PS Issue #4 (visible thinking) RESOLVED**.

## Phase 10 summary
- 5 new files: skills/__init__.py + skills/manager.py + 10 skill dirs (PURE COPY) + tools/skill.py + tools/skill_propose_patch.py.
- 2 modified: tools/__init__.py + core/query_engine.py (added skill_manager wiring).
- 33 new tests (21 unit + 12 integration, including 9 Codex-fix lock tests).
- Codex review: REJECT first pass (1 BLOCKER + 4 HIGH + 2 MEDIUM + 2 UNDECLARED). All 9 fixed in same commit.
- Post-fix: AXIS A PASS, AXIS B 3 FAITHFUL / 2 ADAPTED / 0 DRIFTED.
- 392 pass + 4 skip (was 359+4 in Phase 9 → +33 net new).
- PS Issue #1 (Hermes filter) RESOLVED.

## Phase 09 summary
- 4 new files: subagent/env.py + subagent/handoff.py + subagent/spawn.py + tools/task.py.
- 2 modified: tools/__init__.py (registers task tool), core/query_engine.py (passes parent_engine + parent_depth in dispatch context).
- 44 new tests (5 env + 9 handoff + 30 integration including 5 Codex-fix lock tests + 1 line in test_query_engine.py).
- Codex review: REJECT first pass (1 BLOCKER + 3 substantive + 1 low + 1 DRIFTED + 1 UNDECLARED_PATTERN). All 7 fixed in same commit.
- Post-fix: AXIS A PASS, AXIS B 2 FAITHFUL / 2 ADAPTED / 0 DRIFTED.
- 359 pass + 4 skip (was 329+4 in Phase 8.5 → +30 net new).

## Phase 08.5 thin-slice gate (HARD BLOCKER before Phase 9)
- 10 critical cross-phase integration scenarios in `tests/parity/test_thin_slice.py`.
- 10/10 PASS — Phase 9 unblocked.
- Scenarios span: Phase 1 BedrockClient, Phase 2 registry, Phase 3 read_file dispatch, Phase 5 bash + python_exec security, Phase 6 prompt budget + cache boundary, Phase 7 deferral round-trip, Phase 8 QueryEngine end-to-end, Phase 8 wiring contract.
- 329 pass + 4 skip total.
- Codex review: NOT_RUN (Phase 8.5 is mechanical / scenario-driven; Codex review for cross-phase architectural drift was already done at Phase 8).

## Codex review status (current phase)
- First pass: APPROVE_WITH_FIXES (2 substantive + 2 test gaps).
- Findings:
  - [high] `_discovered_tool_names` leaks across runs → reset at run() entry. Lock test: test_discovered_tools_reset_between_runs.
  - [medium] plan-mode bypass via always_load=True → strict v4 allowlist (PLAN_MODE_ALLOWED_TOOLS). Lock test: test_engine_plan_mode_blocks_always_load_mutating_tool.
  - [medium] cross-run reset test gap → covered by lock test 1.
  - [low] plan-mode bypass test gap → covered by lock test 2.
- Post-fix: AXIS A PASS, AXIS B 2 FAITHFUL / 2 ADAPTED / 0 DRIFTED.
- Saved at: `_status/codex_reviews/phase-08.md`.

## Done in this phase (Phase 08)
- [x] ADR-014 appended (Phase 8 strategy: REPLACEMENT of v4 Agent.run, EXTRACTION of Phase-1 inline classes, ADDITION of IterationBudget; explicit IN-SCOPE / OUT-OF-SCOPE).
- [x] Wrote `core/__init__.py` (re-exports IterationBudget / BedrockErrorCategory / ErrorClassifier / RetryPolicy / QueryEngine / run_one_turn).
- [x] Wrote `core/budget.py` (PORT_LOG #016 — verbatim Hermes-via-v4 IterationBudget).
- [x] Wrote `core/errors.py` (PORT_LOG #017 — extracted Phase-1 BedrockErrorCategory + ErrorClassifier).
- [x] Wrote `core/retry.py` (PORT_LOG #018 — extracted Phase-1 RetryPolicy).
- [x] Updated `runtime/bedrock_client.py` to re-import errors + retry from core/ (byte-equivalent, lock-tested).
- [x] Wrote `core/query_engine.py` (PORT_LOG #019 — ~400 LOC adapt of Runnable QueryEngine.ts; Phase 7 wiring contract end-to-end).
- [x] 37 new tests across `tests/unit/test_budget.py` (7) + `tests/unit/test_errors.py` (10) + `tests/unit/test_retry.py` (7) + `tests/integration/test_query_engine.py` (12 — including the **Phase 8 acceptance test** `test_tool_search_round_trip_promotes_deferred_tool`).
- [x] PORT_LOG #016-019 added with verdicts pending Codex review.
- [x] PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md: 6 Phase-8 entries (8.1-8.6).
- [x] PS_V5_LEARNINGS_FROM_REPOS.md: 4 Phase-8 source entries + 7 new "Better than X" tracker rows.
- [x] Wrote `MAIN/changelogs/CHANGELOG_v5_phase_08.md`.

## Tests status (post Phase 08 + Codex fixes)
- Last `pytest` run: 2026-04-30 — **319 passed + 4 skipped** in 5.81s.
- Phase 8 contributes 39 new tests (37 initial + 2 Codex-fix lock tests).

## Aggregate audit (post Phase 08)
- Static prompt tokens: 2498 ≤ 2500 ✓
- Per-section caps: all respected ✓
- Cap sum: 2880 ≤ 2900 ✓
- Section names unique ✓
- tool_classes at slot 2 (PS Issue #7 fix) ✓
- Tool count: 11 (v4 ~30) ✓
- ADR-to-PORT_LOG ratio: 19 PORT_LOG rows / 14 ADRs — all rows reference an ADR ✓

## Codex review status (current phase)
- Status: NOT_RUN — pending review of Phase 8 implementation.
- Will save at `_status/codex_reviews/phase-08.md`.

## Previous phase
- Phase 07 DONE — tagged v5-phase-07 at d42c5ba, pushed. 280 pass + 4 skips. Codex REJECT first pass, all 4 blockers fixed.

## Done in Phase 07
- [x] ADR-013 written (Phase 7 strategy + 3-mode query parser + isDeferredTool rule + Phase-8 wiring contract).
- [x] Wrote `tools/tool_search.py` (~330 LOC; bare-name fast path + select / +required / keyword query modes + name parsing + `<functions>` wire format + Phase-8 `tool_search_discovered_names()` extraction helper).
- [x] Replaced Phase-2 stub `apply_tool_search_deferral` with real partition logic. Codex-fix #1 changed signature to `(visible_with_tool_search, deferred_names_list)` to eliminate duplicate-tool_search bug.
- [x] Marked `view_image`, `list_dir`, `notebook_edit` as `should_defer=True`. tool_search itself has `always_load=True` (never deferred).
- [x] Updated `tools/__init__.py` bootstrap_built_ins to register tool_search.
- [x] Updated 2 Phase-2 stub tests in test_registry.py + added 1 new partition test.
- [x] Wrote 32 Phase-7 tests in test_tool_search.py.
- [x] Codex review (gpt-5.5, reasoning=medium, via stdin): **REJECT first pass with 4 BLOCKERS**. All 4 fixed in same Phase 07 commit:
  - Blocker #1: signature change (no duplicate tool_search). Lock tests: test_deferral_no_duplicate_tool_search + 2 in test_registry.
  - Blocker #2: per-turn active_tools via context. Lock test: test_active_tools_context_filters_search.
  - Blocker #3: documented Phase-7=QUERY / Phase-8=WIRING split + added `tool_search_discovered_names()` extraction helper. Lock tests (3): extraction + empty + missing-marker.
  - Blocker #4: name + description + search_hint search. Lock tests: required-against-description + keyword-hits-description.
- [x] Plus added bare-exact-name fast path + plan-mode interaction lock test (Runnable parity finding from Codex's PATTERN 014).
- [x] Pre-Phase-8 audit (re-run): all 7 metrics PASS.
- [x] PORT_LOG rows #014 + #015 added with verdicts.
- [x] **PS_V5 docs updated**: 5 Phase-7 functional-change entries + 2 Phase-7 learnings + 2 new "Better than X" tracker rows.
- [x] Wrote `MAIN/changelogs/CHANGELOG_v5_phase_07.md`.

## Tests status
- Last `pytest` run: 2026-04-30 — **280 passed + 4 skipped** in 5.90s.
- Phase 7 contributes 32 new tests in test_tool_search.py + updates in test_registry.py.

## Codex review status (current phase)
- First pass: REJECT (4 blockers + PATTERN 014 DRIFTED).
- Post-fix: ALL 4 blockers addressed with lock tests; PATTERN 014 expected to upgrade to FAITHFUL-WITH-JUSTIFIED-ADAPTATION.
- Saved at: `_status/codex_reviews/phase-07.md`.

## Token-saving measurement
- Phase 6 baseline: ~4000 tokens/turn for tools block.
- Phase 7 (3 deferred): ~3230 tokens/turn — **~770 tokens saved per turn**.
- Phase 13 cumulative target: ≥3000 tokens (lands as Phases 9-10 add task / todo_* / create_* / web_fetch / ask_user / skill_* to deferred set).

## Git
- Branch: v5-build
- Last commit: 6a49879 (v5/block-g3: iter-3 fixes — Codex iter-2 APPROVE_WITH_FIXES) — pending push
- Last tag: v5.0.1-block-g3 (Block G3 done, Codex 3-iter cycle ended APPROVE) — pending
- Pushed to sageagent: 2026-05-02 (housekeeping commit)
- HISTORICAL: Phase 0-13 commits 572e07dd93dc..469b390 (covered in compact_v5/MAIN/changelogs/)

## Blockers
- none

## Next session: pick up at

**R-tier R1-R12 real-AWS validation (PHASE 3, $3-7 cap)**.

User decision 2026-05-03 (Path B): Block U HTMLs DEFERRED post-ship. v5 is substantively ship-gate-ready (781 pass + 17 skip, 14 code Blocks tagged, verify_ship_zip PASS). R-tier proves "v5 has no semantic bugs on real Bedrock" and is the actual ship gate.

Sequence:
1. **PHASE 3 — R1-R12** ($3-7): per WORKER_HINT §10 + R_TIER_REVIEW_TEMPLATE TEMPLATE A/B/C. Max 3 AWS calls per test, BOTH worker AND Codex APPROVE before each call.
2. **PHASE 4 — R13-R16 enhanced** ($5-6): coding accuracy / multi-file refactor / bug detection / long session.
3. **PHASE 5 — Block V head-to-head v4 vs v5** ($2-3): comparative benchmark, USER-APPROVAL needed before scheduling.
4. **PHASE 6 — Final gate**: full-codebase Codex AXIS A/B/C review + present v5.0.1 product summary to user before tagging.
5. **POST-SHIP** — Block U HTMLs (4 NEW + HERMES update + Playwright + tag).

R-tier discipline (HARD RULES):
- 3 AWS calls per test, total. BOTH worker AND Codex must APPROVE before each call.
- ESCALATE-to-user triggers: 3 calls + still failing / Codex BLOCKER / AWS Budget 80% ($40/$50) / worker+Codex disagree after 3 rounds / Bedrock infra error / 2 consecutive R-tests fail at call #1.
- Append row to `compact_v5/_status/r_tier_review_log.md` after every test.
- Append JSONL to `compact_v5/_status/r_tier_metrics.jsonl`.

- Block 0 status: DONE — tag `v5.0.1-block-0` at `19e7823`; pushed.
- Block B status: DONE — tag `v5.0.1-block-b` at `ee01142`; pushed.
- Block B+ status: DONE — tag `v5.0.1-block-b-plus` at `ff30e8d`; pushed.
- Block C status: DONE — tag `v5.0.1-block-c` at `77c6eb4`; pushed.
- Block C+ status: DONE — tag `v5.0.1-block-c-plus` at `f9e4000`; pushed.
- Block D status: DONE — tag `v5.0.1-block-d` at `7a19715`; pushed.
- Block A status: DONE — tag `v5.0.1-block-a` at `c87a823`; pushed.
- Block E+F status: DONE — tag `v5.0.1-block-e-f` at `2388e64`; pushed.
- Block F2 status: DONE — tag `v5.0.1-block-f2` at `9d3cd50`; pushed.
- Block I status: DONE — tag `v5.0.1-block-i` at `c46be09`; pushed.
- Block M status: DONE — tag `v5.0.1-block-m` at `09b6114`; pushed.
- Block G status: DONE — tag `v5.0.1-block-g` at `0fe6454`; pushed.
- Block G3 status: DONE — tag `v5.0.1-block-g3` at `6a49879`; pushed.
- Block G2 status: DONE — tag `v5.0.1-block-g2` at `4a7fd7e`; pushed.
- Block H status: DONE — tag `v5.0.1-block-h` at `9759c11`; pushed.
- Block H+ status: DONE — tag `v5.0.1-block-h-plus` at `d40493e`; pushed.
- Block L status: DONE — tag `v5.0.1-block-l` at `686a3d5`; pushed.
- Block N status: DONE — tag `v5.0.1-block-n` at `136f41b`; pushed.
- Block T status: DONE — tag `v5.0.1-block-t` at `1cda54a`; pushed.
- Block J status: DONE — tag `v5.0.1-block-j` at `cab61ec`; pushed.
- Block K status: DONE — tag `v5.0.1-block-k` at `d89067c`; pushed.
- Block U status: DEFERRED-POST-SHIP — scaffold + archive landed at `9c8fcb4`+later; 4 NEW HTMLs deferred per user 2026-05-03 (Path B: code-to-production first).
- Mode: B (Codex-only-gate, autonomous; user reviews FINAL product only).
- Worker prompt: `compact_v5/_phase_2/wave_6/BUILDER_PROMPT.md`.
- Pre-Block-0 gates ALL MET (2026-05-02 reconciliation):
  - ✓ Plan v4 Codex APPROVE: `_status/codex_reviews/plan-v4-final-APPROVE.md`
  - ✓ Wave 5-DEEP synthesis: `_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` (21 Blocks, ~19,300 LOC, 448 PORT_LOG rows)
  - ✓ CONFIDENCE_REPORT: `_phase_2/wave_5_deep/CONFIDENCE_REPORT.md` (9-axis verdict)
  - ✓ Wave 6 PS_Plan_Edge_Cases: `_phase_2/wave_6/PS_Plan_Edge_Cases_Thinking.md` (111 user scenarios, 9 GAPs closed)
  - ✓ TEST_DESIGN: `_phase_2/wave_6/TEST_DESIGN.md` (T1-T5 + R1-R12)
  - ✓ Auto-Dream decision: manual `/dream` only (no daemon)
  - ✓ Codex stale-text fixes (5 of 5) applied to SYNTHESIS_MASTER + plan v3
- Sequence: 0 → smoke → B → B+ → C → C+ → D → A → E+F → F2 → I → M → G → G3 → G2 → H → H+ → L → N → T → J → K. Each Block: Codex AXIS A/B/C → APPROVE → tag → push → next.
- After Block K: R1-R12 real-AWS scenarios (~$3-7).
- After R-tier: STOP, present final product to user.

(Historical Phase-13 entry: v5.0.0 tagged at `469b390` for traceability, SHIP-BLOCKED per V5_SHIP_CRITIQUE. v5.0.1 builds on top — does not delete v5.0.0 code, adds 21 Blocks worth of fixes + extensions.)

(Historical Phase 08 plan reference, kept for resume-after-compact context):
- **Phase 08 — QueryEngine + retry + errors + IterationBudget UI** (per V5_PLAN.md): read Runnable `QueryEngine.ts` (1295 LOC) + `withRetry.ts` + `services/api/errors.ts`. Land:
  - `core/query_engine.py` — main agent loop. **MUST call `apply_tool_search_deferral(enabled=True)` and `tool_search_discovered_names()` to wire deferred tools** (Phase 7's blocker #3 contract).
  - `core/retry.py` — withRetry adaptation.
  - `core/errors.py` — error message generators.
  - `core/budget.py` — IterationBudget (Hermes-style; PS Issue #2 visible-budget UI).
- **Phase 8 acceptance**: end-to-end mock test (tool_use → tool runs → final answer) AND tool_search deferred-loading round-trip works.
- Resume protocol: see `_status/RESUME.md`.

## Pre-Phase-7 aggregate audit
- Static prompt tokens: 2498 ≤ 2500 ✓
- Per-section caps: all respected ✓
- Cap sum 2880 ≤ budget 2900 ✓
- Section names unique ✓
- tool_classes at slot 2 (PS Issue #7 fix) ✓
- Tool count: v5 has 10 tools, v4 has ~30 ✓
- ADR-to-PORT_LOG ratio: 13 rows / 12 ADRs, all referenced ✓
- Verdict: ALL PASS, Phase 7 UNBLOCKED.

## Previous phase
- Phase 06 DONE — tagged v5-phase-06 at e1a7d1a, pushed. Plus Phase 06.1 tightening (0a57152). 247 pass + 4 skips.

## Previous phase
- Phase 05 DONE — tagged v5-phase-05 at 603cb76, pushed. 217 pass + 4 skips.

## Done in this phase
- [x] Append **ADR-012**: 19-section design + token caps + cache-boundary contract.
- [x] Write `prompt/sections.py` (Section dataclass + SECTION_ORDER + token caps + memoization + Runnable parity).
- [x] Write 19 `prompt/*.md` files: identity, tool_classes (PROMOTED to slot 2), system, tool_efficiency, doing_tasks, critique_handling, answer_preference, data_validation, executing_actions, output_style, subagent_coord, status_doc, verification_contract, memory_protocol, documents, security, mcp, commands, skill_patching.
- [x] Write `prompt/_CACHE_BOUNDARY.md` marker file.
- [x] Write `prompt/__init__.py` with `build_system_prompt(ctx)` + canonical `CACHE_BOUNDARY` constant (single source of truth).
- [x] Write `core/cache.py` (CacheBlock + build_cache_blocks + fingerprint_sections + detect_cache_break + CacheBreakReport).
- [x] Write `tests/unit/test_prompt_assembly.py` (18 tests including 4 Codex-fix lock tests) and `tests/unit/test_cache.py` (9 tests).
- [x] `pytest tests/` — **247 passed + 4 skipped**.
- [x] **Codex review (gpt-5.5, reasoning=medium, via stdin)**: APPROVE_WITH_FIXES with 1 major + 2 minors + 1 nit. All 4 fixed in same Phase 06 commit:
  - Major: caps sum to 3090, not budget. **Fix**: tightened caps to sum 2880 ≤ 2900.
  - Minor: `build_cache_blocks` stripped leading newlines. **Fix**: removed `.lstrip("\n")`; lock test for byte-equivalence.
  - Minor: boundary constants duplicated/inconsistent. **Fix**: single-source `prompt.CACHE_BOUNDARY`; lock test asserts equality across modules.
  - Nit: `detect_cache_break` assumes unique section names. **Fix**: `test_section_names_are_unique` lock.
- [x] All 3 Runnable patterns FAITHFUL-WITH-JUSTIFIED-ADAPTATION post-fix. UNDECLARED_PATTERN PASS.
- [x] PORT_LOG rows #011 + #012 + #013 added with verdicts.
- [x] **PS_V5 docs updated**: 7 Phase-6 functional-change entries + 4 Phase-6 learnings entries + 6 new "Better than X" tracker rows.
- [x] Write `MAIN/changelogs/CHANGELOG_v5_phase_06.md`.

## Tests status
- Last `pytest` run: 2026-04-30 — **247 passed + 4 skipped** in 5.68s.
- Phase 06 contributes 27 new tests (18 prompt assembly + 9 cache).
- Failing tests: none.

## Codex review status (current phase)
- Last review: 2026-04-30 (gpt-5.5, reasoning=medium, via stdin) — **APPROVE_WITH_FIXES**.
- Findings: 1 major + 2 minors + 1 nit — all addressed.
- Open review comments: 0.
- Saved at: `_status/codex_reviews/phase-06.md`.

## Static prompt metrics
- v4 estimate: ~5000 tokens.
- v5 Phase 06 actual: **2739 tokens** (45% reduction).
- STATIC_TOKEN_BUDGET: 2900 (Phase 06 actual + 6% headroom).
- Per-section cap sum: 2880 (≤ STATIC_TOKEN_BUDGET, locked by test).
- V5_PLAN.md target: ≤2500. Phase 13 polish goal: tighten to 2500.

## PS Issue #7 STRUCTURAL FIX
- `tool_classes.md` at slot 2 (right after identity, before "system"). Locked by `test_tool_classes_section_at_slot_2`.
- File-per-section forces reviewable PR diffs.
- Per-section token caps prevent regrowth to a 914-LOC monolith.
- Aggregate audit gate (before Phase 7) runs cognitive-load test on the current prompt structure.

## Git
- Branch: v5-build
- Last commit: e1a7d1a8eecf42a3ed9fb256d3ed618c514c4a71 "v5/phase-06: sectioned prompt + cache + Codex fixes (PS Issue #7 fix)"
- Last tag: v5-phase-06

## Blockers
- none

## (Historical) Phase 06 close (kept for traceability)
- **Phase 07 (HISTORICAL — already shipped in v5.0.0)**: ToolSearchTool deferred loading. Acceptance: per-turn schema overhead dropped ≥3000 tokens vs Phase 6 baseline. PASSED.
- v5.0.0 Phases 08-13 also shipped (see compact_v5/MAIN/changelogs/).
- **CURRENT pickup is Block 0** (post-Wave-6 v5.0.1 build) — see "Next session: pick up at" section above.
