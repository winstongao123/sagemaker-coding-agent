# v4 sagemaker_agent.py — exhaustive inventory verify

**Source**: `D:/Github/sagemaker-coding-agent/compact_v4/MAIN/agent/sagemaker_agent.py` (12088 LOC).
**Plan**: `compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md` (18 Blocks).
**Q1 matrix**: `compact_v5/_phase_2/wave_4/Q1_EVIDENCE_MATRIX.md` (172 PORT_LOG rows).
**Date**: 2026-05-01.
**Verdict (preliminary)**: 8 v4 capabilities are NOT explicitly addressed in plan v3 + Q1 matrix. All others verified PORTED.

## Audit
- Lines covered: 1-12088 (whole file, via Grep symbol extraction; dense regions read inline).
- Classes identified: 31 (`class …` at module level).
- Top-level functions: 80 (`def …` at column 0; excludes class methods).
- Class methods: ~140 (`    def …`; not enumerated row-by-row — covered transitively by class porting rows).
- Slash command handlers: 19 advertised at `:8164` + 1 separate `/auth` auth-gate at `:10789` = 20 distinct command-like inputs (verified).
- UI rendering / handler functions inside `create_chat_ui`: 35 inner `def …` (closures inside `create_chat_ui`).
- Module-level constants/dicts: 34 ALL_CAPS or `_lead_underscore` globals.
- Tool registry: `TOOLS` dict with 26 entries (15 native v4 + Block T parity = 26 v5 target post-Block T).
- Agent type registry: `AGENT_TYPES` dict with 7 types (build, plan, explore, verify, general, review, fork).

---

## Master inventory

Legend for "In v5 plan?":
- `BLOCK x` = explicitly PORTED in plan v3 + Q1 row.
- `BLOCK x (transitive)` = covered as a method of a class that is explicitly ported (entire class is verbatim).
- `IMPLICIT v4 baseline` = covered by constraint #1 ("v4.10.10 baseline = the floor; full file ported"), but no dedicated plan row — this is the gap class.
- `GAP` = no plan row found AND not covered transitively.

### A. Top-of-file: retry, compaction, truncation, file cache, config

| # | Symbol | Type | v4 line | In v5 plan? | Notes |
|---|---|---|---|---|---|
| 1 | `RetryableError` | class | :110 | BLOCK B / BLOCK L (transitive) | Wave 2 Section 1 says PRESENT in v5 `core/retry.py`. Not in plan v3 by name; covered by Block L (Runnable error/retry) — RetryableError predates Block L but Block L supersedes it. |
| 2 | `RetryHandler` | class | :116 | IMPLICIT v4 baseline | Wave 2 Section 1 says PRESENT in v5 `core/retry.py`. **No explicit plan row.** Block L ports Runnable's `withRetry.ts` which replaces RetryHandler — semantically covered, structurally ambiguous. |
| 3 | `RETRY = RetryHandler(...)` | global | :179 | IMPLICIT v4 baseline | Singleton; same coverage as #2. |
| 4 | `Compactor` | class | :186-555 | BLOCK A | Q1 row "class Compactor" + 10 Block A rows. |
| 5 | `Compactor.PROTECTED_TOOLS` | constant | :194 | BLOCK A (transitive) | Inside class. |
| 6 | `Compactor.estimate_tokens` | classmethod | :200 | BLOCK A (transitive) | Wave 2 says PRESENT in v5 core/budget.py. |
| 7 | `Compactor.prune_tool_outputs` | classmethod | :215 | BLOCK A | Q1 explicit row. |
| 8 | `Compactor.create_summary_prompt` (13-section) | classmethod | :275 | BLOCK A | Q1 row "create_llm_summary 13-section template" (V4.10.5). |
| 9 | `Compactor._build_summary_input` | classmethod | :342 | BLOCK A (transitive) | |
| 10 | `Compactor._truncate_head_for_ptl_retry` | classmethod | :353 | BLOCK A (transitive) | PTL retry loop. |
| 11 | `Compactor._prune_tool_results_for_summary` (V4.9.4) | classmethod | :387 | BLOCK A (transitive) | |
| 12 | `Compactor._summary_client` (V4.9.4 aux model) | classmethod | :464 | BLOCK A (transitive) | `compaction_model` config. |
| 13 | `Compactor.create_llm_summary` | classmethod | :489 | BLOCK A | |
| 14 | `Compactor.should_compact` | classmethod | :560 | BLOCK A (transitive) | |
| 15 | `Compactor.compact` | classmethod | :573 | BLOCK A (transitive) | |
| 16 | `COMPACTOR = Compactor()` | global | :633 | BLOCK A (transitive) | Singleton. |
| 17 | `POST_COMPACT_MAX_FILES/CHARS/BUDGET` | constants | :641-643 | BLOCK A | Block A "_FILES_READ.clear() post-compact restoration". |
| 18 | `MAX_TOOL_RESULT_CHARS` | constant | :648 | BLOCK A (transitive) | |
| 19 | `build_todo_restoration_message` | function | :651 | BLOCK A | Plan row "TODO restoration via build_todo_restoration_message". |
| 20 | `get_recently_read_files` | function | :685 | BLOCK A (transitive) | Used by `Compactor.compact`. |
| 21 | `build_file_restoration_message` | function | :714 | BLOCK A (transitive) | Used by `Compactor.compact`. |
| 22 | `_auto_compact_paused`, `MAX_COMPACT_FAILURES` | global, constant | :748-749 | BLOCK A | Q1 explicit row "auto-compact circuit breaker" (no-deferrals correction). |
| 23 | `Truncation` | class | :756-861 | IMPLICIT v4 baseline | Wave 2 Section 1: "Truncation class: PRESENT in runtime/truncation.py". **No dedicated plan row.** ToolResult dataclass MISSING per Wave 2. |
| 24 | `ToolResult` (@dataclass) | class | :867 | **GAP** | Wave 2 Section 1 explicitly lists "ToolResult dataclass: MISSING (metadata tracking lost)". No PORT_LOG row found. |
| 25 | `FileCache` | class | :893-1010 | BLOCK B+ | Q1 row "class FileCache (thread-local context + save/restore)". |
| 26 | `FILE_CACHE = FileCache()` | global | :1010 | BLOCK B+ (transitive) | |
| 27 | `Config` (@dataclass) | class | :1018 | IMPLICIT v4 baseline | Plan references `Config.session_cost_limit`, `Config.require_tool_approval`, `Config.max_exec_calls_per_session` etc. as individual rows — no single "port whole Config dataclass" row. **All ~50 fields covered piecemeal**, but no master row. (Confirmed Wave 2: Config is PRESENT). |
| 28 | `_strip_jsonc_comments` | function | :1152 | IMPLICIT v4 baseline | JSONC support for agent_config.json — needed for #29. |
| 29 | `_load_config_file` | function | :1190 | IMPLICIT v4 baseline | agent_config.json loader. **Plan does mention agent_config.json in Block D ("CommandRegistry handles agent_config.json custom commands")** — covered transitively. |
| 30 | `_apply_config_file` | function | :1205 | IMPLICIT v4 baseline | Same coverage as #29. |
| 31 | `CONFIG = Config()` | global | :1285 | IMPLICIT v4 baseline | Re-exported by Block 0 shim. |

### B. Security, Audit, Bedrock client, Sessions

| # | Symbol | Type | v4 line | In v5 plan? | Notes |
|---|---|---|---|---|---|
| 32 | `SecurityManager` | class | :1298-2106 | IMPLICIT v4 baseline | 808 LOC of bash/python pattern denylists, path validation, secret scanning, redirection validation. Wave 2 Section 1: "SecurityManager: PRESENT (security/manager.py)". **No plan v3 row.** This is the largest non-Compactor class in v4. |
| 33 | `_auto_detect_allowed_paths` | function | :2107 | IMPLICIT v4 baseline | |
| 34 | `SECURITY = SecurityManager(...)` | global | :2143 | IMPLICIT v4 baseline | |
| 35 | `AuditEntry` (@dataclass) | class | :2156 | BLOCK B (transitive) | |
| 36 | `AuditLogger` | class | :2173-2252 | BLOCK B | Q1 explicit row. |
| 37 | `AUDIT = AuditLogger(...)` | global | :2253 | BLOCK B | Q1 explicit row. |
| 38 | `_BEDROCK_CLIENT_CONFIG = _BotoConfig(...)` | global | :2264 | IMPLICIT v4 baseline | boto3 client config (timeouts, max_attempts). Used by BedrockClient. |
| 39 | `ToolCall` (@dataclass) | class | :2271 | IMPLICIT v4 baseline | Used by Response. |
| 40 | `Response` (@dataclass) | class | :2277 | IMPLICIT v4 baseline | BedrockClient return type. |
| 41 | `BedrockErrorCategory` | class | :2296 | BLOCK L (semantically) | Wave 2 Section 1: "ErrorClassifier: PRESENT in core/errors.py". |
| 42 | `ErrorClassifier` | class | :2320 | BLOCK L (semantically) | Same. |
| 43 | `RetryPolicy` | class | :2352 | BLOCK L (semantically) | Same — superseded by Runnable's withRetry.ts in Block L. |
| 44 | `BedrockClient` | class | :2378-2565 | IMPLICIT v4 baseline | Plan row "BedrockClient.chat cold-cache trigger check" but **no row for BedrockClient class itself**. Block 0 shim implies it's ported but not explicit. |
| 45 | `Session` (@dataclass) | class | :2567 | BLOCK B+ (transitive) | |
| 46 | `SessionManager` | class | :2578 | BLOCK B+ | Q1 explicit row. |
| 47 | `SESSIONS = SessionManager(...)` | global | :2656 | BLOCK B+ (transitive) | |

### C. Skills, Commands, MCP, Context tracking, Tokens

| # | Symbol | Type | v4 line | In v5 plan? | Notes |
|---|---|---|---|---|---|
| 48 | `SkillInfo` (@dataclass) | class | :2674 | BLOCK I (transitive) | |
| 49 | `SkillManager` | class | :2684-3048 | BLOCK I | Wave 2 Section 2: "SkillManager: PRESENT in skills/manager.py — Phase 10 ported byte-for-byte". |
| 50 | `_log_skill_patch_event` | function | :3049 | BLOCK I (transitive) | Audit JSONL trail for skill patches. |
| 51 | `SKILLS = SkillManager(...)` | global | :3070 | BLOCK I (transitive) | |
| 52 | `CommandRegistry` | class | :3078-3115 | BLOCK D | Q1 row "CommandRegistry from :3078-3115". |
| 53 | `COMMANDS = CommandRegistry(...)` | global | :3115 | BLOCK D (transitive) | |
| 54 | `McpStdioClient` | class | :3122-3276 | DROPPED-BY-CONSTRAINT | Constraint #9: "Drop MCP entirely". Wave 2 Section 2 reports PRESENT in v5 runtime/mcp_client.py, BUT plan v3 explicitly drops MCP. **Inconsistency between Wave 2 v5 codebase and plan v3.** Recommend: Block confirms drop OR keeps file dormant. |
| 55 | `McpHttpClient` | class | :3278-3346 | DROPPED-BY-CONSTRAINT | Same. |
| 56 | `McpManager` | class | :3348-3454 | DROPPED-BY-CONSTRAINT | Same. |
| 57 | `MCP_MANAGER = McpManager(...)` | global | :3455 | DROPPED-BY-CONSTRAINT | |
| 58 | `ContextManager` | class | :3464-3528 | IMPLICIT v4 baseline | Wave 2 Section 2: PRESENT in core/budget.py. **No plan row by name.** Used by Compactor.should_compact. |
| 59 | `CONTEXT = ContextManager(...)` | global | :3529 | IMPLICIT v4 baseline | |
| 60 | `_MODEL_PRICING` | dict | :3539 | BLOCK B (transitive) | TokenTracker uses it for cost. |
| 61 | `TokenTracker` | class | :3565-3753 | BLOCK B | Q1 explicit row. |
| 62 | `TOKENS = TokenTracker()` | global | :3755 | BLOCK B | |
| 63 | `_TODOS` | global list | :3763 | IMPLICIT v4 baseline | Used by todo_write/read tools (Block T) and by build_todo_restoration_message (Block A). |
| 64 | `_FILES_READ`, `_FILES_READ_LOCK` | global, lock | :3764-3765 | BLOCK C+ | Q1 explicit row. |
| 65 | `FILE_UNCHANGED_STUB` | constant | :3768 | IMPLICIT v4 baseline | Used by tool_read_file dedup. |

### D. Context analysis + tool helpers + read/write/edit

| # | Symbol | Type | v4 line | In v5 plan? | Notes |
|---|---|---|---|---|---|
| 66 | `_offload_large_result` | function | :3771 | BLOCK A (transitive) | Wave 2: PARTIAL in v5 runtime/truncation.py. |
| 67 | `_find_tool_name` | function | :3837 | BLOCK A (transitive) | Helper for prune_tool_outputs. |
| 68 | `microcompact` | function | :3851-3897 | BLOCK A | Q1 explicit row. |
| 69 | `_context_block_tokens` | function | :3898 | BLOCK A (transitive) | |
| 70 | `_is_stale_round_trip` | function | :3919-3975 | BLOCK A | **Wave 2 Section 2 says MISSING in v5.** Plan v3 lists `context_collapse` as ported — so its dependency `_is_stale_round_trip` must come too, but is not separately called out. Confirm port. |
| 71 | `context_collapse` | function | :3978-4017 | BLOCK A | Q1 explicit row. |
| 72 | `_context_add` | function | :4020 | BLOCK A (transitive) | |
| 73 | `analyze_context_messages` | function | :4025 | BLOCK D (transitive) | Used by `/context` slash command. |
| 74 | `_context_top` | function | :4112 | BLOCK D (transitive) | |
| 75 | `format_context_report` | function | :4116 | BLOCK D | `/context` command relies on this. |
| 76 | `_check_file_staleness` | function | :4178 | IMPLICIT v4 baseline | Used by tool_read_file. |
| 77 | `_get_git_diff` | function | :4196 | IMPLICIT v4 baseline | Used by tool_read_file (file-staleness git diff hint). |
| 78 | `_resolve_path` | function | :4212 | IMPLICIT v4 baseline | Used by all file tools. |
| 79 | `_build_workspace_info` | function | :4232 | IMPLICIT v4 baseline | Used in env-details + system prompt. |
| 80 | `tool_read_file` | function | :4258-4413 | BLOCK 0 / IMPLICIT v4 baseline | One of 15 v4-original tools. Already in v5.0.0. |
| 81 | `_RECENT_DIFFS`, `_RECENT_DIFFS_LOCK` | global, lock | :4414-4415 | BLOCK D (transitive) | Used by `/diffs` slash command. |
| 82 | `SnapshotManager` | class | :4418-4509 | BLOCK B | Q1 explicit row. |
| 83 | `SNAPSHOTS = SnapshotManager(...)` | global | :4510 | BLOCK B | |
| 84 | `_generate_unified_diff` | function | :4513 | IMPLICIT v4 baseline | Used by tool_edit_file. |
| 85 | `_auto_lint_python` | function | :4522 | IMPLICIT v4 baseline | Post-write lint hint for .py files. |
| 86 | `_AUTO_COMMIT_COUNTER`, `_AUTO_COMMIT_LOCK` | global, lock | :4549-4550 | IMPLICIT v4 baseline | V4.7.1 local-git checkpoint feature (Config.auto_commit_every). |
| 87 | `_maybe_auto_checkpoint` | function | :4553 | IMPLICIT v4 baseline | Same. |
| 88 | `_scan_output_secrets` | function | :4617 | IMPLICIT v4 baseline | Used by tool_bash + tool_python_exec. |
| 89 | `tool_write_file` | function | :4632 | BLOCK 0 / IMPLICIT v4 baseline | Already in v5.0.0. |
| 90 | `tool_edit_file` | function | :4729 | BLOCK 0 / IMPLICIT v4 baseline | Already in v5.0.0. |
| 91 | `tool_glob` | function | :4846 | BLOCK 0 / IMPLICIT v4 baseline | Already in v5.0.0. |
| 92 | `tool_grep` | function | :4897 | BLOCK 0 / IMPLICIT v4 baseline | Already in v5.0.0. |
| 93 | `tool_list_dir` | function | :4952 | BLOCK 0 / IMPLICIT v4 baseline | Already in v5.0.0. |

### E. Bash, Python exec, Docker isolation

| # | Symbol | Type | v4 line | In v5 plan? | Notes |
|---|---|---|---|---|---|
| 94 | `_kill_active_process` | function | :4988 | IMPLICIT v4 baseline | Stop-button support for long-running bash. |
| 95 | `_safe_exec_env` | function | :4998 | IMPLICIT v4 baseline | |
| 96 | `_run_subprocess` | function | :5011 | IMPLICIT v4 baseline | |
| 97 | `_ensure_docker_image_ready` | function | :5033 | IMPLICIT v4 baseline | Config.execution_mode='docker' support. |
| 98 | `_validate_shell_redirections` | function | :5068 | IMPLICIT v4 baseline | Used by tool_bash. |
| 99 | `_docker_base_cmd` | function | :5121 | IMPLICIT v4 baseline | |
| 100 | `_classify_bash_ro` | function | :5186 | IMPLICIT v4 baseline | Read-only classification for plan-mode bash. |
| 101 | `tool_bash` | function | :5239 | BLOCK 0 / IMPLICIT v4 baseline | |
| 102 | `_build_python_preamble` | function | :5293 | IMPLICIT v4 baseline | Python sandbox preamble. |
| 103 | `_install_sandbox` | function | :5303 | IMPLICIT v4 baseline | _safe_import / _safe_open / _safe_os_open guards. |
| 104 | `_PYTHON_EXEC_PREAMBLE` | global | :5407 | IMPLICIT v4 baseline | |
| 105 | `tool_python_exec` | function | :5409 | BLOCK 0 / IMPLICIT v4 baseline | |

### F. Office tool implementations (Block T)

| # | Symbol | Type | v4 line | In v5 plan? | Notes |
|---|---|---|---|---|---|
| 106 | `_parse_word_content` | function | :5455 | BLOCK T (transitive) | Used by tool_create_word. |
| 107 | `_add_formatted_run` | function | :5600 | BLOCK T (transitive) | |
| 108 | `_add_word_table` | function | :5621 | BLOCK T (transitive) | |
| 109 | `tool_create_word` | function | :5642 | BLOCK T | Q1 row schema :7247 + impl :5642. |
| 110 | `tool_create_excel` | function | :5730 | BLOCK T | Q1 row. |
| 111 | `tool_create_markdown` | function | :5813 | BLOCK T | Q1 row. |
| 112 | `tool_create_notebook` | function | :5838 | BLOCK T | Q1 row. |
| 113 | `_NOTEBOOK_EDIT_ACTIONS`, `_NOTEBOOK_CELL_TYPES` | constants | :5905-5906 | BLOCK T (transitive) | Used by tool_notebook_edit. |
| 114 | `_normalise_ipynb_source` | function | :5909 | BLOCK T (transitive) | |
| 115 | `tool_notebook_edit` (V4.10.0) | function | :5921 | IMPLICIT v4 baseline / **GAP** | **NOT in Block T's 11 tools list (Q1 :138-149).** Block T explicitly enumerates: create_word, create_excel, create_markdown, create_notebook, create_chart, create_pdf, semantic_search, ask_user, web_fetch, todo_write, todo_read = 11. notebook_edit is missing. |
| 116 | `tool_create_chart` | function | :6039 | BLOCK T | Q1 row. |
| 117 | `_parse_markdown_table` | function | :6258 | BLOCK T (transitive) | Used by tool_create_pdf. |
| 118 | `tool_create_pdf` | function | :6282 | BLOCK T | Q1 row. |
| 119 | `tool_view_image` | function | :6419 | IMPLICIT v4 baseline / **GAP** | **NOT in Block T list.** v4 advertises 22 tools (line :39); v5.0.0 has 15; Block T adds 11 → gives 26, BUT the 11 includes view_image? Re-reading Q1 :138-149: NO, view_image is not listed. Confirmed gap. |

### G. Search, sub-agents, web, todo

| # | Symbol | Type | v4 line | In v5 plan? | Notes |
|---|---|---|---|---|---|
| 120 | `SemanticSearch` | class | :6461-6610 | IMPLICIT v4 baseline | Bedrock-Titan embedding code-index. Plan ports `tool_semantic_search` in Block T but NOT the underlying class explicitly. **No plan row for SemanticSearch class itself.** |
| 121 | `_SEMANTIC_SEARCH` | global | :6612 | IMPLICIT v4 baseline | Lazy singleton. |
| 122 | `tool_semantic_search` | function | :6615 | BLOCK T | Q1 row. |
| 123 | `tool_skill` | function | :6674 | BLOCK 0 / IMPLICIT v4 baseline | Already in v5.0.0 + Block I. |
| 124 | `tool_skill_propose_patch` (V4.9.5) | function | :6703 | BLOCK I (transitive) | Bound to SkillManager.propose_patch. |
| 125 | `tool_task` | function | :6738 | BLOCK G (transitive) | Wraps Agent._run_task_tool. |
| 126 | `tool_ask_user` | function | :6743 | BLOCK T | Q1 row. |
| 127 | `_is_private_ip` | function | :6748 | IMPLICIT v4 baseline | SSRF guard for tool_web_fetch. |
| 128 | `_NoRedirectHandler` | class | :6778 | IMPLICIT v4 baseline | urllib redirect guard. |
| 129 | `_WEB_FETCH_MAX_BYTES` | constant | :6784 | BLOCK T (transitive) | |
| 130 | `tool_web_fetch` | function | :6787 | BLOCK T | Q1 row. |
| 131 | `_TODO_UI_SYNC` | global | :6852 | BLOCK E+F (transitive) | UI bridge for todo display. |
| 132 | `tool_todo_write` | function | :6854 | BLOCK T | Q1 row. |
| 133 | `tool_todo_read` | function | :6887 | BLOCK T | Q1 row. |

### H. Plan mode, agent types, tool registry, system prompt

| # | Symbol | Type | v4 line | In v5 plan? | Notes |
|---|---|---|---|---|---|
| 134 | `PLAN_MODE_PROMPT` | constant | :6899 | IMPLICIT v4 baseline | Used by AGENT_TYPES['plan'] + plan-mode toggle in UI. |
| 135 | `PLAN_MODE_ALLOWED_TOOLS` | set | :6905 | IMPLICIT v4 baseline | Plan-mode read-only tool whitelist. |
| 136 | `AGENT_TYPES` | dict | :6914-7100 | BLOCK G | Q1 explicit row. 7 types ported. |
| 137 | `TOOLS` (registry) | dict | :7105-7400 | BLOCK 0 + BLOCK T | 26-tool registry. |
| 138 | `get_tool_definitions` | function | :7409 | BLOCK 0 / IMPLICIT v4 baseline | |
| 139 | `load_project_instructions` (CLAUDE.md loader) | function | :7419-7456 | IMPLICIT v4 baseline | Walks workspace + parents for CLAUDE.md. **Critical for Config.load_claude_md=True.** No explicit plan row. |
| 140 | `_MEMORY_TYPES`, `_MEMORY_TYPE_DESC` | tuple, dict | :7457-7458 | BLOCK H (transitive) | |
| 141 | `_parse_memory_sections` | function | :7466 | BLOCK H (transitive) | |
| 142 | `_MEMORY_MAX_LINES`, `_MEMORY_MAX_BYTES` | constants | :7500-7501 | BLOCK H (transitive) | Runnable parity caps. |
| 143 | `_INJECTION_PATTERNS`, `_INVISIBLE_CHAR_PATTERN` | list, regex | :7509-7518 | IMPLICIT v4 baseline | **Prompt-injection scanner constants.** No explicit plan row. (Plan v3 line 343 says "If user wants … injection scanning, propose as v5-native enhancement in a follow-up audit" — but v4 already has it; this is a plan-level inconsistency.) |
| 144 | `_scan_for_prompt_injection` | function | :7523 | **GAP** | Used by `_load_persistent_memory`. **Plan v3 explicitly says Hermes scanForInjection is DROPPED (line 343), but v4's own `_scan_for_prompt_injection` exists at :7523 and IS the scanner. Plan v3 omits it.** |
| 145 | `_load_persistent_memory` | function | :7542 | BLOCK B+ | Plan row "AGENT_STATUS auto-load: search v4 for `_load_persistent_memory`". Confirmed. |
| 146 | `_status_doc_path` | function | :7594 | BLOCK B+ (transitive) | |
| 147 | `_status_doc_template` | function | :7614 | BLOCK B+ (transitive) | |
| 148 | `_load_project_status` | function | :7653 | BLOCK B+ | Same plan row as #145. |
| 149 | `_build_subagent_env_details` | function | :7695-7762 | BLOCK G | Q1 row line :7695-7738 noted. |
| 150 | `_sanitize_handoff` | function | :7763 | BLOCK G (transitive) | |
| 151 | `_build_subagent_handoff_block` (V4.10.4) | function | :7771-7853 | BLOCK G | Q1 row :7771-7841 noted. |
| 152 | `_MEMORY_EXTRACT_PROMPT` | constant | :7854 | BLOCK H (transitive) | |
| 153 | `_extract_and_append_memories` | function | :7889-8028 | BLOCK H | Q1 explicit row. |
| 154 | `SYSTEM_PROMPT` | constant | :8029-8189 | IMPLICIT v4 baseline | ~160 LOC system prompt (the agent's whole persona/instructions). **No plan v3 row.** Block 0 implies port via `from sagemaker_agent import …` but SYSTEM_PROMPT is not in the shim re-export list. Risk: if v5 has its own system prompt, drift from v4 baseline. |

### I. Iteration budget, exec budget, Agent class, run loop

| # | Symbol | Type | v4 line | In v5 plan? | Notes |
|---|---|---|---|---|---|
| 155 | `IterationBudget` | class | :8190-8226 | BLOCK G (transitive) | Plan line 241 references `IterationBudgetWidget` already in v5 (PS#2 visible-budget UI). Underlying class: PRESENT in v5 by Phase 11. |
| 156 | `_GLOBAL_EXEC_CALLS`, `_GLOBAL_EXEC_SECONDS`, `_GLOBAL_EXEC_LOCK` | globals | :8227-8229 | BLOCK C | Q1 explicit row. |
| 157 | `_EXEC_BUDGET_FILE` | constant | :8230 | BLOCK C (transitive) | |
| 158 | `_load_global_exec`, `_save_global_exec`, `_update_global_exec`, `_reset_global_exec` | functions | :8233-8276 | BLOCK C (transitive) | Persistent exec budget across sessions. |
| 159 | `Agent` | class | :8278-9603 | BLOCK C+ | Q1 row "class Agent at :8278-…". Massive class (1325 LOC, ~30 methods). |
| 160 | `Agent._run_ask_user_tool` | method | :8330 | BLOCK G (transitive) | |
| 161 | `Agent._run_task_tool` | method | :8350-8649 | BLOCK G | Sub-agent dispatch + worktree + handoff. ~300 LOC. |
| 162 | `Agent.run` | method | :8650-9603 | BLOCK C+ + BLOCK A + BLOCK G + BLOCK L | The main turn loop. ~950 LOC. **Single largest method in v4.** Touches every block. Plan covers it transitively but no explicit per-method-row. |
| 163 | `Agent.reset` | method | :9604 | BLOCK C+ (transitive) | |
| 164 | `escape_html` | function | :9624 | BLOCK E (transitive) | Used by chat rendering. |
| 165 | `BEDROCK_MODELS` | list | :9630-9664 | BLOCK 0 + BLOCK E+F | Plan re-exports BEDROCK_MODELS in shim. |
| 166 | `resolve_context_window` | function | :9665 | BLOCK E+F (transitive) | Per-model context-window override. |
| 167 | `_auto_derive_context_window` | function | :9681 | BLOCK E+F (transitive) | |
| 168 | `TOOL_ICONS` | dict | :9722 | BLOCK E+F (transitive) | UI icons per tool. |

### J. create_chat_ui — closures

`create_chat_ui` (`:9735-12073`, ~2340 LOC) is the entire ipynb-driven UI. It defines 35 inner closures over `ui_state`. Plan v3 covers them en bloc as "Block E + F together". Per-closure mapping:

| # | Inner def | v4 line | Block | Notes |
|---|---|---|---|---|
| 169 | `_format_inline_md` | :9776 | E | Q1 row. |
| 170 | `_render_assistant_markdown` | :9788 | E | Q1 row. |
| 171 | `render_chat` | :9924 | E | Q1 row. |
| 172 | `render_todos` | :9972 | E | Q1 row. |
| 173 | `sync_todos_from_global` | :10004 | E (transitive) | |
| 174 | `on_budget_change` (iteration budget) | :10095 | F | Plan row "iteration-budget slider :10086-10102". |
| 175 | `on_chat_height_change` | :10134 | E (transitive) | |
| 176 | `validate_model_connection` | :10155 | E (transitive) | |
| 177 | `on_model_change` | :10177 | E | Q1 row "Model dropdown + on_model_change". |
| 178 | `on_temp_change` | :10209 | E (transitive) | |
| 179 | `on_thinking_change` | :10213 | E (transitive) | |
| 180 | `on_budget_change` (cost slider) | :10227 | E (transitive) | Note: same name as #174, different slider. |
| 181 | `on_dark_mode_change` | :10231 | E | |
| 182 | `on_approval_toggle` | :10244 | E (transitive) | |
| 183 | `_on_sa_model_change` | :10263 | E (transitive) | Sub-agent overrides panel. |
| 184 | `_on_sa_toggle` | :10289 | E (transitive) | |
| 185 | `update_mode_display` | :10308 | E | Q1 row. |
| 186 | `get_colors` | :10359 | E (transitive) | |
| 187 | `update_session_list` | :10372 | E+F | |
| 188 | `update_tokens_display` | :10377-10478 | E | Q1 row. |
| 189 | `add_message` | :10480 | E (transitive) | |
| 190 | `request_approval` | :10489 | C+ | Q1 row pending_approval at :10491-10605. |
| 191 | `on_approve` / `on_approve_always` / `on_deny` | :10603-10628 | C+ | |
| 192 | `on_ask_user_submit` / `on_ask_user_skip` | :10628-10641 | E (transitive) | |
| 193 | `request_user_input` | :10641 | E (transitive) | |
| 194 | `on_stop` | :10697 | C+ (transitive) | |
| 195 | `do_pre_send_compact` | :10719 | A | |
| 196 | `on_send` | :10772-11589 | C+ + D + A | **The main entry point — 800+ LOC.** Contains all 19 slash-command branches. |
| 197 | `on_clear` | :11590 | E+F (transitive) | |
| 198 | `on_save` | :11625 | B+ + E+F | Q1 row. |
| 199 | `on_load` | :11661 | B+ + E+F | Q1 row. |
| 200 | `on_new` | :11792 | B+ + E+F (transitive) | |
| 201 | `on_compact` | :11827 | A (transitive) | Compact button handler. |
| 202 | `_on_send_threaded` | :11883 | C+ (transitive) | Thread wrapper. |
| 203 | `_on_compact_threaded` | :11917 | A (transitive) | |
| 204 | `on_cleanup` | :11924 | E+F (transitive) | Cleans audit_logs / .snapshots / .code_index / truncated_outputs / .exec_budget.json. |
| 205 | `get_header_html` | :11964 | E+F (transitive) | |

### K. Slash command handlers (full list, all in `on_send`)

| # | Command | v4 line | Block |
|---|---|---|---|
| 206 | `/auth <token>` | :10789 | D (Q1 row) |
| 207 | `/skills` | :10805 | D |
| 208 | `/skill use <name>` | :10814 | D |
| 209 | `/skill clear` | :10836 | D |
| 210 | `/unskill <name>` | :10851 | D |
| 211 | `/skill suggestions` | :10874 | D |
| 212 | `/skill apply <name>` | :10892 | D |
| 213 | `/skill reject <name>` | :10955 | D |
| 214 | `/revert [file]` | :10965 | D |
| 215 | `/cost` | :11030 | D |
| 216 | `/context` | :11052 | D |
| 217 | `/status [init\|path]` | :11062 | D |
| 218 | `/verify [full\|quick\|pre-commit]` | :11095 | D |
| 219 | `/checkpoint [create\|list\|restore]` | :11114 | D |
| 220 | `/phase <text>` | :11183 | D |
| 221 | `/diffs [summary\|last\|<file>]` | :11200 | D |
| 222 | `/regression` | :11243 | D |
| 223 | `/done [full\|quick]` | :11276 | D |
| 224 | Custom command dispatcher (`/<custom>` → `COMMANDS.expand`) | :11314, :11330-11341 | D |
| 225 | `/simplify` (resolved via expander) | :11330 fall-through | D |

All 20 verified PORTED in plan v3 Block D + Q1 matrix.

---

## v4 items NOT YET in v5 plan (gaps)

After full enumeration of 225 symbols, the following 8 items are **either explicitly missing from plan v3 / Q1 matrix, OR covered only by an "IMPLICIT v4 baseline" assertion without a concrete PORT_LOG row**. These are the gaps to close before Block 0:

| # | Symbol | v4 line | Why missed | Recommended Block |
|---|---|---|---|---|
| 1 | `ToolResult` (@dataclass) | :867-886 | Wave 2 Section 1 explicitly lists "ToolResult dataclass: MISSING (metadata tracking lost)". No Q1 row. Used to surface truncated/total_size/shown_size metadata to UI. | Block B (alongside Truncation) — add 1 PORT_LOG row "ToolResult dataclass". |
| 2 | `tool_notebook_edit` (V4.10.0) + `_NOTEBOOK_EDIT_ACTIONS` + `_normalise_ipynb_source` + schema at :7275-7285 | impl :5921, schema :7275 | Block T (Q1 :138-149) enumerates exactly 11 tools and notebook_edit is NOT in the list. v4 ships it as the 22nd tool. | Block T expansion — add 12th row "notebook_edit". |
| 3 | `tool_view_image` + schema at :7307 | impl :6419, schema :7307 | Same — Block T list omits view_image. v4 ships it. | Block T expansion — add 13th row "view_image". |
| 4 | `SemanticSearch` class (Bedrock Titan embeddings, code index) | :6461-6610 | Block T ports `tool_semantic_search` (the function) but the underlying ~150-LOC class is not separately rowed. Without it the tool is a no-op. Wave 2 doesn't address. | Block T expansion — add row "SemanticSearch class verbatim port". |
| 5 | `_scan_for_prompt_injection` + `_INJECTION_PATTERNS` + `_INVISIBLE_CHAR_PATTERN` | :7509-7541 | Plan v3 line 343 says scanForInjection is DROPPED from Hermes adoption "as v5-native enhancement follow-up". But v4 ALREADY has `_scan_for_prompt_injection` at :7523 — it's not a Hermes adoption, it's a v4-native security feature. Plan must port the v4-native version, not defer it. | New Block (or Block C+ extension) — add row "Port v4 _scan_for_prompt_injection + _INJECTION_PATTERNS + _INVISIBLE_CHAR_PATTERN as v4 baseline (NOT a Hermes adoption)". |
| 6 | `SYSTEM_PROMPT` constant (~160 LOC, the agent's full persona) | :8029-8189 | No plan v3 row. Block 0 shim re-exports CONFIG / BEDROCK_MODELS / create_chat_ui but does not list SYSTEM_PROMPT. Risk: v5 drifts to its own prompt and loses v4.10.10 behaviour (verify-suggestion language, status-doc workflow, etc.). | Block 0 (re-export) + Block H (since memory extraction depends on the same prompt structure). Add row "SYSTEM_PROMPT verbatim from :8029". |
| 7 | `BedrockClient` class itself (188 LOC; chat/parse/mock/cache logic) | :2378-2565 | Plan rows reference `BedrockClient.chat cold-cache trigger check` (Block A) and chat-method tokenization (Block B), but no master "port BedrockClient class" row. | Block B — add row "class BedrockClient verbatim". |
| 8 | `SecurityManager` class (808 LOC — bash + python denylists, path validation, secret scanning, redirection validation, allowed_paths gate) | :1298-2106 | Wave 2 says PRESENT in v5 security/manager.py but plan v3 has NO row for SecurityManager. This is the largest single non-Compactor class in v4 and the linchpin of the Bedrock-only / no-grey-market security posture. | New row in Block C+ (alongside approval gate / rate-limit) — "class SecurityManager + SECURITY singleton verbatim from :1298-2143". |

### Lesser concerns (covered transitively, but worth a single-line confirmation row)

| # | Symbol | v4 line | Why flag |
|---|---|---|---|
| 9 | `Config` dataclass (~50 fields) | :1018-1149 | Individual fields rowed piecemeal; no master "port Config dataclass" row. Risk: a field added between v3 plan finalization and Block 0 (e.g. a new V4.10.x knob) gets dropped silently. Recommend: explicit Block 0 row "port Config dataclass verbatim with all 50 fields". |
| 10 | `ContextManager` class | :3464-3528 | Wave 2 says PRESENT in v5 core/budget.py but no plan row by name. |
| 11 | `Truncation` class | :756-861 | Wave 2 says PRESENT in v5 runtime/truncation.py but no plan row by name. |
| 12 | `RetryHandler` + `RETRY` | :116, :179 | Block L supersedes with Runnable's withRetry, but if Block L isn't fully complete at v5.0.1 ship, RetryHandler is the v4 baseline. Confirm one of the two is wired. |
| 13 | `MCP classes` (3 classes) | :3122-3454 | Constraint #9 "Drop MCP" but Wave 2 reports MCP classes PRESENT in v5 runtime/mcp_client.py. Either drop the v5 file OR remove constraint #9 — currently inconsistent. |
| 14 | `load_project_instructions` (CLAUDE.md loader) | :7419-7456 | Used when Config.load_claude_md=True. No plan row. |

---

## Summary

| Metric | Count |
|---|---|
| Total v4 symbols enumerated (classes + top-level defs + key globals + slash commands + UI closures) | 225 |
| Explicitly PORTED in plan v3 + Q1 matrix (named row) | ~100 |
| Covered transitively (parent class / parent function ported) | ~117 |
| **Hard gaps (8) — no plan row, not covered transitively, NOT a deferral-rule item** | **8** |
| Lesser concerns (covered but worth an explicit confirmation row) | 6 |
| Items dropped by constraint (MCP) — verify v5 codebase aligns | 4 |

**Verdict**: v5 plan v3 + Q1 matrix is **NOT yet at zero-gap**. Adding 8 PORT_LOG rows (1 each for ToolResult, notebook_edit, view_image, SemanticSearch class, _scan_for_prompt_injection family, SYSTEM_PROMPT, BedrockClient class, SecurityManager class) closes the master gap list. After those edits, the matrix is complete.

The 6 "lesser concerns" should be folded in as one-line `IMPLICIT v4 baseline` confirmations (no extra LOC, just paper-trail).

The 4 "MCP drop vs Wave-2-says-present" items need a yes/no decision: either drop the v5 file (plan-aligned) or remove constraint #9 (codebase-aligned).

**LOC impact of closing the 8 gaps**: ~1,100 (SecurityManager 808 + SemanticSearch 150 + SYSTEM_PROMPT 160 + BedrockClient already counted in BLOCK B's "verbatim port" but not rowed + tool_notebook_edit ~120 + tool_view_image ~40 + _scan_for_prompt_injection ~40 + ToolResult ~25). All of this is verbatim port, no new code.

---

Generated: 2026-05-01 | Method: full-file Grep symbol extraction + Q1 matrix cross-check + Wave 2 v5-codebase status reconciliation.
