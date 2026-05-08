# H5 — Hermes run_agent.py 10305-12880 + AGENTS.md + Other Files (Chunk 5/5)

**Scope:** Final tail of `run_agent.py` (lines 10305–12880, ~2576 LOC), full `AGENTS.md` (765 lines), plus repo-wide audit of remaining Python/markdown surfaces (truncated Glob — top-level layout captured, depth subdirs noted as out-of-scope per v5 single-user/Bedrock-only constraints).

**Constraints applied:** v5.0.1 single-user SageMaker, Bedrock-only, no external network, v4 `chat.ipynb` canonical UI, NO DEFERRALS.

---

## 1. Files Audit

### 1A. `run_agent.py` 10305-12880
Single contiguous block: end of `run_conversation()` retry/recovery loop + post-loop wrap-up + `chat()` simple wrapper + `main()` Fire CLI entrypoint. ~2576 LOC, no class boundaries, all inside one method then the module-level `main()`.

### 1B. `AGENTS.md` (full, 765 lines)
Pure developer guide / prompt template for AI assistants. Sections: Dev Environment, Project Structure, File Dep Chain, AIAgent class signature, CLI Architecture, TUI Architecture, Adding Tools, Adding Configuration, Skin/Theme System, Plugins, Skills, Important Policies, Profiles, Known Pitfalls, Testing.

### 1C. Other files (Glob truncated at depth 4 — captured top-level + key dirs)
Truncated Glob shows hermes-agent has at minimum:
- `acp_adapter/` (3 files: `__init__`, `__main__`, `auth.py`) — ACP server (VS Code/Zed/JetBrains)
- `acp_registry/` (`agent.json`, `icon.svg`)
- `agent/` (only `__init__.py`, `prompt_caching.py`, `trajectory.py` shown in top — full subdir hidden by truncation; AGENTS.md says "provider adapters, memory, caching, compression, etc.")
- `cron/` (only `__init__.py` shown)
- `datagen-config-examples/` (jsonl + yaml configs, 4 files)
- `docker/SOUL.md`
- `environments/` — RL training (Atropos), SWE bench, terminal bench, yc bench, tblite, tool_call_parsers for 9 model families (deepseek_v3, deepseek_v3_1, glm45, glm47, kimi_k2, llama, longcat, qwen, qwen3_coder)
- `gateway/` (only top-level `__init__`, `mirror.py`, `pairing.py`, `sticker_cache.py`, `builtin_hooks/__init__.py`, `platforms/ADDING_A_PLATFORM.md`, `platforms/homeassistant.py` shown)
- `hermes_cli/` (only `colors.py`, `default_soul.py` shown)
- `nix/configMergeScript.nix`
- `optional-skills/` (autonomous-ai-agents, blockchain — 2 SKILL.md visible)
- `RELEASE_v0.2.0.md` … `RELEASE_v0.7.0.md`
- `MANIFEST.in`, `LICENSE`, `.plans/openai-api-server.md`, `.plans/streaming-support.md`

Glob hit truncation cap; deeper Python source (run_agent.py, model_tools.py, cli.py, hermes_state.py, agent/*, hermes_cli/*, gateway/*, plugins/*, tools/*, ui-tui/*, tui_gateway/*, tests/*) not enumerated. AGENTS.md describes them as ~12k LOC (run_agent), ~11k LOC (cli), ~15k tests across ~700 files.

---

## 2. Capabilities Table — run_agent.py 10305-12880

| # | Hermes Capability | Lines | What | v5 Plan Status | Disposition |
|---|---|---|---|---|---|
| 1 | **finish_reason normalization across 4 transports** (codex_responses incomplete-detail parsing, anthropic_messages stop_reason map, bedrock_converse normalize, chat_completions + Ollama/GLM "suspicious stop = truncated") | 10305-10341 | Per-transport finish_reason resolution | Block N (transports) — Bedrock only needed | ALREADY-IN-PLAN (Bedrock branch only) |
| 2 | **Length truncation continuation** (3-retry budget, "[System: continuation]" user message, prefix accumulation in `truncated_response_prefix`, progressive max_tokens boost 2x→3x cap 32 768) | 10342-10464, 11619-11626, 12374-12377 | Auto-continue truncated assistant messages | Block N coding-loop | ALREADY-IN-PLAN |
| 3 | **Thinking-budget exhaustion detection** (regex `<think|thinking|reasoning|REASONING_SCRATCHPAD>`, content-after-think check, user-friendly `/thinkon low` guidance) | 10365-10424 | Reasoning ate all output tokens — bail with hint | Block J (extended thinking) | ALREADY-IN-PLAN |
| 4 | **Truncated tool-call retry** (1-shot retry on tool_calls + finish_reason=length; refuse to execute partial JSON on second occurrence) | 10466-10492 | Don't run incomplete tool-call args | Block N coding-loop | ALREADY-IN-PLAN |
| 5 | **Rollback to last assistant turn** on truncation when prior history exists | 10494-10521 | Recovery to last-good state | Block N coding-loop | ALREADY-IN-PLAN |
| 6 | **Token usage normalization + persistence** (`normalize_usage()`, session DB `update_token_counts`, cost estimation `estimate_usage_cost()`, billing_provider/billing_mode/subscription_included tracking) | 10523-10615 | Per-call token + cost ledger | Block O (token tracking) | ALREADY-IN-PLAN (subset — single-user, no DB row writes) |
| 7 | **Cache-hit % surface** (cache_read_tokens / prompt_tokens display, supports OpenAI/Kimi/DeepSeek/Qwen auto-prefix-cache + Anthropic marker-injection) | 10617-10637 | Display cache stats | Block J cache | ALREADY-IN-PLAN |
| 8 | **Nous rate-limit clear-on-success** (cross-session shared-file via `agent.nous_rate_guard`) | 10639-10650 | Provider-specific recovery hook | — | OUT-OF-SCOPE (Bedrock only) |
| 9 | **Interrupted API call handling** (spinner stop, persist session, set interrupted flag, partial response) | 10652-10663 | InterruptedError mid-call | Block N | ALREADY-IN-PLAN |
| 10 | **UnicodeEncodeError two-pass recovery** (surrogate strip pass + ASCII-codec pass; sanitises messages, api_messages, api_kwargs, prefill_messages, tools, system prompt, ephemeral system, default_headers, api_key) | 10684-10835 | Bad-paste / C-locale recovery | — | OUT-OF-SCOPE (single-user SageMaker, UTF-8 default) |
| 11 | **`classify_api_error()` + `FailoverReason` enum** (rate_limit, billing, overloaded, context_overflow, payload_too_large, long_context_tier, thinking_signature, etc.) | 10843-10856 | Structured error classification | Block N | ALREADY-IN-PLAN (subset — Bedrock failures only) |
| 12 | **Credential pool rotation** (`_recover_with_credential_pool` for 401/429) | 10858-10865 | Multi-key rotation | — | OUT-OF-SCOPE (single-user, single Bedrock IAM identity) |
| 13 | **Provider-specific 401 refresh paths** (codex / nous / copilot / anthropic) — each with one-shot `_try_refresh_*_client_credentials()` + diagnostic auth-method print | 10866-10941 | Provider OAuth refresh | — | OUT-OF-SCOPE (Bedrock IAM only) |
| 14 | **Anthropic thinking-block signature recovery** (HTTP 400 from mutated turn → strip all `reasoning_details`, one-shot retry) | 10943-10968 | Caching-induced sig-invalid | — | OUT-OF-SCOPE (Bedrock Converse signs differently; v5 won't mutate mid-turn) |
| 15 | **Long-context-tier 429 fallback** (Anthropic Claude Max 1M → 200k drop, mark `_context_probe_persistable=False`) | 11047-11103 | Subscription-tier downgrade | — | OUT-OF-SCOPE (Bedrock has fixed quotas) |
| 16 | **Eager rate-limit fallback chain** (skip exponential backoff, jump to `_try_activate_fallback`; pool-may-recover guard) | 11105-11126 | Cross-provider failover | — | OUT-OF-SCOPE (single Bedrock model) |
| 17 | **Nous 429 cross-session record** (`record_nous_rate_limit`, skip-to-max-retries) | 11128-11158 | Cross-session rate-limit cache | — | OUT-OF-SCOPE |
| 18 | **413 payload-too-large compression loop** (max_compression_attempts gate, `_compress_context()`, conversation_history reset, exhausted-error return with `compression_exhausted=True`) | 11160-11210 | Auto-compress on 413 | Block J compaction | ALREADY-IN-PLAN |
| 19 | **Context-overflow auto-shrink** (`parse_context_limit_from_error`, `parse_available_output_tokens_from_error`, `get_next_probe_tier`, output-cap vs input-too-large distinction, MiniMax delta-only-overflow handling, persist parsed limit to `save_context_length`) | 11212-11369 | Detect window from error, step down | Block J compaction | ALREADY-IN-PLAN (general pattern; MiniMax/Minimaxi-specific OUT-OF-SCOPE) |
| 20 | **Non-retryable client error gate** (ssl.SSLError exclusion, json.JSONDecodeError = retryable transient, fallback before abort, large-failed-session persist skip to prevent growth loop #1630) | 11371-11469 | 4xx classification + auth-error coaching | Block N | ALREADY-IN-PLAN (subset) |
| 21 | **Max-retries primary-transport recovery** (`_try_recover_primary_transport` rebuilds client once on transient transport error before fallback) | 11471-11488 | Stale TCP/TLS pool repair | — | OUT-OF-SCOPE (boto3 handles this internally for Bedrock) |
| 22 | **SSE stream-drop diagnosis** (no status_code + "connection lost/reset/closed" → user hint about large write_file → suggest `execute_code` with `open()`) | 11496-11524 | Actionable error UX | — | OUT-OF-SCOPE (Bedrock Converse non-streaming in v5) |
| 23 | **Retry-After honouring** (header parse, cap 120s) + **jittered_backoff** (base 2s, max 60s) + **interrupt-aware sleep** (200ms increments, gateway activity touch every 30s) | 11554-11602 | Backoff loop | Block N | ALREADY-IN-PLAN |
| 24 | **Compression restart counter** (counts toward retry_count to prevent infinite compress-loop) | 11609-11617 | Compression-loop guard | Block J | ALREADY-IN-PLAN |
| 25 | **`_get_transport().normalize_response()` post-loop** (multimodal content list flatten — extract `text` parts, stringify dict content) | 11637-11665 | Provider-shape normalisation for non-OpenAI servers (llama-server etc.) | Block N transports | ALREADY-IN-PLAN (Bedrock only — but multimodal-list flattening is generally useful) |
| 26 | **`post_api_request` plugin hook** (per-call: usage, model, finish_reason, tool_call_count) | 11667-11690 | Plugin instrumentation surface | — | OUT-OF-SCOPE (no plugin system in v5) |
| 27 | **Subagent reasoning relay** (parent display gets first-line of child reasoning via `tool_progress_callback("_thinking", first_line)` when `_delegate_depth > 0`) + **`reasoning.available` event** for any structured callback | 11699-11719 | Subagent thought streaming to parent | Block M (subagents) | ALREADY-IN-PLAN |
| 28 | **Incomplete `<REASONING_SCRATCHPAD>` retry** (opened-but-never-closed XML → 2 retries → save partial + roll back to last assistant) | 11721-11751 | Tag-based truncation guard | Block J | ALREADY-IN-PLAN |
| 29 | **Codex incomplete continuation** (`finish_reason="incomplete"` w/ codex_responses → preserve interim content+reasoning+codex_reasoning_items, dedup detection, 3-retry continue) | 11753-11800 | Codex-specific incomplete loop | — | OUT-OF-SCOPE (no codex_responses transport) |
| 30 | **Tool-name auto-repair** (`_repair_tool_call(name)` fuzzy-match before validation; injects auto-repaired name into `tc.function.name`) | 11811-11818 | Hallucinated tool-name recovery | Block N coding-loop | ALREADY-IN-PLAN |
| 31 | **Invalid tool-call name handler** (3-retry budget, error message lists all valid tools, "Skipped: another tool call invalid" for siblings) | 11819-11860 | Self-correcting tool-name errors | Block N | ALREADY-IN-PLAN |
| 32 | **Invalid tool-call args recovery** (truncation detect via "doesn't end with `}`/`]`", router-rewrite-finish-reason guard, 3-retry then inject tool-error results to keep role alternation) | 11862-11952 | JSON-arg validation + recovery | Block N | ALREADY-IN-PLAN |
| 33 | **`_cap_delegate_task_calls` + `_deduplicate_tool_calls`** (post-call guardrails on `tool_calls` list before append/execute) | 11953-11960 | Limit subagent fan-out, dedupe identical calls | Block M, Block N | ALREADY-IN-PLAN |
| 34 | **Content-with-tools fallback capture** (`_last_content_with_tools` snapshot when turn has both content+tools; `_last_content_tools_all_housekeeping` flag; HOUSEKEEPING_TOOLS = `{memory, todo, skill_manage, session_search}`; `_mute_post_response` when stream consumers + housekeeping-only) | 11962-11989 | Reuse mid-turn answer if follow-up empty | Block J | ALREADY-IN-PLAN (general pattern; housekeeping set adapts to v5 tools) |
| 35 | **Thinking-prefill removal before assistant append** (pop trailing `_thinking_prefill` messages so we don't double up; reset `_thinking_prefill_retries`/`_empty_content_retries`) | 11991-12015 | Thinking-only continuation cleanup | Block J | ALREADY-IN-PLAN |
| 36 | **Stream-display close before tool exec** (`stream_delta_callback(None)` to flush response box; TTS `_stream_callback` excluded — None is end-of-stream there) | 12017-12030 | UX flush | — | OUT-OF-SCOPE (no TUI/streaming-box in v5 ipynb) |
| 37 | **`_execute_tool_calls()` dispatch** + per-turn retry-counter resets (`truncated_tool_call_retries=0`) + `_stream_needs_break=True` flag for next paragraph | 12032-12045 | Per-turn state hygiene | Block N | ALREADY-IN-PLAN |
| 38 | **Iteration-budget refund for `execute_code`-only turns** (RPC-style cheap calls don't burn budget) | 12047-12052 | Budget accounting | Block N | ALREADY-IN-PLAN |
| 39 | **Real-token-based compression decision** (uses `last_prompt_tokens` from API; falls back to `estimate_messages_tokens_rough()` if 0; only `prompt_tokens` — NOT completion+reasoning, fixes #12026 thinking-model premature compression) | 12054-12089 | Token-accurate auto-compress | Block J | ALREADY-IN-PLAN (CRITICAL: v5 must follow prompt-only rule for thinking models) |
| 40 | **Final-response branch** (no tool calls): | 12098-12400 | | | |
| 40a | Partial-stream recovery (`_current_streamed_assistant_text` already delivered → use it) | 12116-12133 | Stream-died-mid-response salvage | — | OUT-OF-SCOPE (non-streaming in v5) |
| 40b | Prior-turn fallback content (housekeeping-only tools → use earlier content as final) | 12135-12159 | Empty-after-tools shortcut | Block J | ALREADY-IN-PLAN |
| 40c | Post-tool empty-response nudge ("(empty)" assistant + user message asking it to continue, role-alternation safe) | 12161-12211 | One-shot model-stuck recovery (#9400) | Block J | ALREADY-IN-PLAN |
| 40d | Thinking-only prefill continuation (structured reasoning but no text → 2-retry self-prefill) | 12213-12243 | Reasoning models that whiff text | Block J | ALREADY-IN-PLAN |
| 40e | Empty-response 3-retry (covers truly-empty AND reasoning-only after prefill exhausted) | 12245-12272 | Generic empty retry | Block J | ALREADY-IN-PLAN |
| 40f | Fallback-provider chain for persistent empty (`_try_activate_fallback()`) | 12274-12302 | Cross-provider empty escape | — | OUT-OF-SCOPE |
| 40g | Terminal "(empty)" with reasoning-preview log + status emit | 12304-12339 | Final user-facing empty + diagnostic | Block J | ALREADY-IN-PLAN |
| 40h | Codex intermediate-ack continuation (2-retry with `_looks_like_codex_intermediate_ack`) | 12345-12372 | Codex "got it, working on it" recovery | — | OUT-OF-SCOPE |
| 40i | Truncated-prefix concatenation + length_continue_retries reset | 12374-12377 | Multi-step continuation stitching | Block N | ALREADY-IN-PLAN |
| 40j | `_strip_think_blocks()` for user-facing string (raw kept in messages for trajectory) | 12379-12380 | Display vs. trajectory separation | Block J | ALREADY-IN-PLAN |
| 40k | Pop trailing `_thinking_prefill` before final append (avoid consecutive assistant msgs that break Anthropic strict alternation) | 12384-12393 | Anthropic Messages alternation invariant | — | OUT-OF-SCOPE (Bedrock Converse handles alternation differently) |
| 41 | **Outer-loop exception with assistant-tool_calls completion** (walk back to find unanswered tool_call_ids, inject error tool-results so API doesn't reject next call for missing tool replies) | 12402-12435 | Crash-during-tool-exec recovery | Block N | ALREADY-IN-PLAN |
| 42 | **Near-max-iterations error break** (final assistant message appended to keep history valid for resume — avoids consecutive user messages) | 12442-12450 | Resume-safety on bail | Block N | ALREADY-IN-PLAN |
| 43 | **Budget-exhausted summary** (`_handle_max_iterations` injects user msg + makes ONE toolless API call asking for summary) | 12452-12469 | Graceful turn-budget exit | Block N | ALREADY-IN-PLAN |
| 44 | **Turn-exit diagnostic logger** (`_turn_exit_reason` enum-string set at every exit point; INFO normally, WARNING when last_msg_role=tool — surfaces "agent just stopped mid-work" pattern; logs model, api_calls, budget, tool_turns, last_msg_role, response_len, session_id, last_tool_name) | 12484-12526 | Turn observability | Block O (telemetry) | ALREADY-IN-PLAN |
| 45 | **`post_llm_call` plugin hook** (per-turn: messages snapshot, model, platform) | 12528-12545 | Plugin sync hook | — | OUT-OF-SCOPE |
| 46 | **`/steer` drain** (any pending steer landed after final turn → `result["pending_steer"]` so caller can replay as next user turn instead of losing it) | 12580-12586 | Mid-turn user steering preservation | — | OUT-OF-SCOPE (no steering UI in ipynb) |
| 47 | **Result envelope** (15 fields: final_response, last_reasoning, messages, api_calls, completed, partial, interrupted, response_previewed, model, provider, base_url, all token counters, last_prompt_tokens, estimated_cost_usd, cost_status, cost_source) | 12555-12579 | Rich return contract | Block O | ALREADY-IN-PLAN (subset — single provider/model in v5) |
| 48 | **Skill-nudge interval check** (`_iters_since_skill >= _skill_nudge_interval` and `skill_manage` in valid_tools → trigger background review) | 12598-12604 | Auto-skill-review cadence | — | OUT-OF-SCOPE (v5 has skills but no auto-skill-management) |
| 49 | **External memory provider per-turn sync** (`_sync_external_memory_for_turn`) | 12606-12611 | Honcho/mem0/etc. integration | — | OUT-OF-SCOPE (Bedrock-only, no external memory backends) |
| 50 | **Background review subprocess spawn** (`_spawn_background_review` — runs AFTER response delivered so doesn't compete with user task) | 12613-12623 | Async memory/skill review | — | OUT-OF-SCOPE |
| 51 | **`on_session_end` plugin hook** (final hook, completed/interrupted flags) | 12632-12646 | Plugin lifecycle close | — | OUT-OF-SCOPE |
| 52 | **`chat()` thin wrapper** — single-message convenience returning `result["final_response"]`, accepts `stream_callback` | 12650-12662 | Public simple API | Block N | ALREADY-IN-PLAN |
| 53 | **`main()` Fire CLI entrypoint** (toolset listing, enabled/disabled/save_trajectories/save_sample/verbose flags, default Python-3.13 demo query, sample-trajectory-to-UUID-jsonl save) | 12665-12876 | Module-level CLI for direct invocation | — | OUT-OF-SCOPE (v5 entrypoint = ipynb, no Fire CLI) |

---

## 3. Capabilities Table — AGENTS.md (prompt template / dev guide)

AGENTS.md is the *prompt seed* for any AI assistant working ON Hermes (not the agent's runtime system prompt — that's elsewhere). Every distinct instruction pattern below is a candidate for v5's own AGENTS.md / CLAUDE.md style.

| # | Section | Distinct Instruction Pattern | v5 Plan Status | Disposition |
|---|---|---|---|---|
| A1 | Dev Env | "Prefer `.venv`; fall back to `venv`. `scripts/run_tests.sh` probes .venv → venv → `$HOME/.hermes/hermes-agent/venv` for worktree shared venvs." | — | OUT-OF-SCOPE (SageMaker has fixed kernel) |
| A2 | Project Structure | "File counts shift constantly — don't treat tree as exhaustive. Filesystem is canonical." | Plan (every block) | ALREADY-IN-PLAN (apply to v5 docs) |
| A3 | Project Structure | Names load-bearing entry points: run_agent.py, model_tools.py, toolsets.py, cli.py, hermes_state.py, hermes_constants.py, hermes_logging.py, batch_runner.py | Block A skeleton | ALREADY-IN-PLAN (v5 has equivalent: sagemaker_agent.py, tools.py, etc.) |
| A4 | Project Structure | Profile-aware paths: `get_hermes_home()` / `display_hermes_home()` | — | OUT-OF-SCOPE (single profile in SageMaker) |
| A5 | File Dep Chain | Bottom-up: `tools/registry.py → tools/*.py → model_tools.py → run_agent.py + cli.py + batch_runner.py + environments/` | Block A | ALREADY-IN-PLAN |
| A6 | AIAgent class | "Real `__init__` takes ~60 parameters. Read run_agent.py for full list." Doc shows minimum subset only. | — | NOTABLE pattern — v5 plan has tighter constructor; principle "doc shows minimum, code is canonical" applies |
| A7 | Agent Loop | "Entirely synchronous, with interrupt checks, budget tracking, and a one-turn grace call (`_budget_grace_call`)." | Block N | ALREADY-IN-PLAN |
| A8 | Agent Loop | OpenAI message format `{role, content}`; reasoning in `assistant_msg["reasoning"]` | Block J | ALREADY-IN-PLAN |
| A9 | CLI Architecture | Rich + prompt_toolkit + KawaiiSpinner + skin engine + slash command registry | — | OUT-OF-SCOPE (ipynb UI in v5) |
| A10 | Slash Command Registry | "Central `COMMAND_REGISTRY` list of `CommandDef` objects. Every downstream consumer derives from this registry automatically — CLI, Gateway, Telegram, Slack, Autocomplete, Help." | — | OUT-OF-SCOPE BUT NOTABLE — single-source-of-truth pattern, applicable to v5 tool registry |
| A11 | Adding a Slash Command | 4-step procedure with code template, plus CommandDef fields (name, description, category, aliases, args_hint, cli_only, gateway_only, gateway_config_gate) | — | OUT-OF-SCOPE |
| A12 | TUI Architecture | Process model: Node Ink ↔ stdio JSON-RPC ↔ Python tui_gateway ↔ AIAgent | — | OUT-OF-SCOPE |
| A13 | TUI dashboard rule | "Do NOT re-implement primary chat experience in React — embedded `hermes --tui` owns transcript/composer/PTY-terminal. Structured React UI around the TUI is allowed when it is not a second chat surface." | — | NOTABLE design rule (single-surface UI) |
| A14 | Adding New Tools | 2-file requirement: `tools/your_tool.py` (with `registry.register()` + `check_fn` + `requires_env`) + `toolsets.py` add to `_HERMES_CORE_TOOLS` or new toolset. Auto-discovery: any `tools/*.py` with top-level `register()` is auto-imported. All handlers MUST return JSON string. | Block A tools | ALREADY-IN-PLAN (v5 has tool registry pattern) |
| A15 | Adding New Tools | "Path references in tool schemas: use `display_hermes_home()` to be profile-aware. Schema generated at import time, AFTER profile override." | — | OUT-OF-SCOPE |
| A16 | Adding New Tools | "Agent-level tools (todo, memory): intercepted by `run_agent.py` BEFORE `handle_function_call()`. See `tools/todo_tool.py` pattern." | Block J/L (todo+memory) | ALREADY-IN-PLAN |
| A17 | Adding Configuration | 3 distinct loaders: `load_cli_config()`, `load_config()`, direct YAML — gateway uses different one than CLI. "If you add a key and CLI sees it but gateway doesn't, you're on wrong loader." | — | OUT-OF-SCOPE (v5 has single config) |
| A18 | Adding Configuration | "Config version bump ONLY when actively migrating/transforming user config. Adding new key handled by deep-merge automatically." | — | NOTABLE — config-evolution discipline |
| A19 | Adding Configuration | ".env = SECRETS ONLY. Non-secret settings (timeouts, thresholds, flags, paths, display) belong in config.yaml, not .env. Bridge from yaml to env var when internal code needs the env var." | — | OUT-OF-SCOPE (no .env in v5) |
| A20 | Adding Configuration | Working directory: CLI uses `os.getcwd()`; messaging uses `terminal.cwd` from yaml; `MESSAGING_CWD` removed with deprecation warning. | — | OUT-OF-SCOPE |
| A21 | Skin/Theme | "Skins are PURE DATA — no code changes needed to add a new skin." Built-in: default/ares/mono/slate. User skins drop into `~/.hermes/skins/*.yaml`. | — | OUT-OF-SCOPE |
| A22 | Plugins | TWO plugin surfaces: General (`PluginManager`, lifecycle hooks pre/post tool/llm + on_session_start/end + register_tool + register_cli_command) and Memory-provider (`MemoryProvider` ABC: sync_turn, prefetch, shutdown, post_setup). | — | OUT-OF-SCOPE |
| A23 | Plugins | **CRITICAL RULE (Teknium May 2026):** "Plugins MUST NOT modify core files (run_agent.py, cli.py, gateway/run.py, hermes_cli/main.py). If a plugin needs a capability the framework doesn't expose, expand the generic plugin surface — never hardcode plugin-specific logic into core. PR #5295 removed 95 lines of hardcoded honcho argparse." | — | NOTABLE — applies to v5 skill system (skills must not patch core sagemaker_agent.py) |
| A24 | Plugins | Discovery timing pitfall: `discover_plugins()` only runs as side-effect of importing `model_tools.py`. Code paths that skip that import must call `discover_plugins()` explicitly (idempotent). | — | OUT-OF-SCOPE |
| A25 | Skills | TWO surfaces: `skills/` (built-in default-on) and `optional-skills/` (heavy/niche, opt-in via `hermes skills install official/<cat>/<skill>`). 13 categories. | Block L | ALREADY-IN-PLAN (v5 has skills + optional-skills already in compact_v4) |
| A26 | Skills | "When reviewing skill PRs, check which directory they target — heavy-dep or niche skills belong in `optional-skills/`." | Block L | ALREADY-IN-PLAN (review rule) |
| A27 | Skills frontmatter | `name, description, version, platforms` (OS gating list), `metadata.hermes.tags`, `.category`, `.config` (settings stored under `skills.config.<key>`, prompted during setup, injected at load). | Block L | NOTABLE — v5 skill frontmatter could adopt platforms/category/config; tags already in v4. |
| A28 | **Prompt Caching Must Not Break** (POLICY) | "Hermes-Agent ensures caching remains valid throughout a conversation. Do NOT alter past context mid-conversation, change toolsets mid-conversation, reload memories or rebuild system prompts mid-conversation. The ONLY time we alter context is during context compression. Slash commands that mutate system-prompt state must be cache-aware: default to deferred invalidation (next session), opt-in `--now` flag for immediate. See `/skills install --now` canonical pattern." | Block J cache | **CRITICAL ALREADY-IN-PLAN** — v5 must enforce same invariant. v4 currently rebuilds system prompt mid-session (cache violation). v5.0.1 must adopt `--now` deferred-invalidation pattern. |
| A29 | Background Process Notifications | `terminal(background=true, notify_on_complete=true)` triggers gateway watcher; verbosity via `display.background_process_notifications` (all/result/error/off). | — | OUT-OF-SCOPE |
| A30 | Profiles | `_apply_profile_override()` sets `HERMES_HOME` before any module imports. All `get_hermes_home()` references scope to active profile automatically. | — | OUT-OF-SCOPE |
| A31 | Profiles | 6 profile-safe rules: (1) use `get_hermes_home()` not `~/.hermes`, (2) use `display_hermes_home()` for user-facing prints, (3) module-level constants OK (cached at import after override), (4) test mocks must mock both `Path.home` AND set HERMES_HOME, (5) gateway adapters use `acquire_scoped_lock()`/`release_scoped_lock()` to prevent two profiles using same credential, (6) profile ops are HOME-anchored not HERMES_HOME-anchored — `_get_profiles_root()` returns `Path.home() / ".hermes" / "profiles"`. | — | OUT-OF-SCOPE |
| A32 | Pitfalls — Hardcode `~/.hermes` | "Source of 5 bugs fixed in PR #3575." | — | OUT-OF-SCOPE |
| A33 | Pitfalls — `simple_term_menu` | "Don't introduce new uses — ghost-duplication bug in tmux/iTerm2. New menus must use `hermes_cli/curses_ui.py` (stdlib curses)." | — | OUT-OF-SCOPE |
| A34 | Pitfalls — `\033[K` ANSI erase-to-EOL | "Leaks as literal `?[K` text under prompt_toolkit's patch_stdout. Use space-padding `f'\\r{line}{' ' * pad}'`." | — | NOTABLE — terminal-rendering pitfall, v5 ipynb display might hit similar |
| A35 | Pitfalls — `_last_resolved_tool_names` | "Process-global in `model_tools.py`. `_run_single_child()` in `delegate_tool.py` saves/restores around subagent execution. New code reading this global may see stale values during child runs." | Block M (subagents) | ALREADY-IN-PLAN (v5 subagent isolation must avoid global-state leak) |
| A36 | Pitfalls — **Cross-tool refs in schemas** | "Tool schema descriptions MUST NOT mention tools from other toolsets by name (e.g. `browser_navigate` saying 'prefer web_search'). Those tools may be unavailable (missing keys, disabled toolset), causing model to hallucinate calls to non-existent tools. If cross-reference needed, add it dynamically in `get_tool_definitions()` in `model_tools.py` — see `browser_navigate` / `execute_code` post-processing blocks for the pattern." | **Block N (dynamic tool ref)** — AGENTS.md:627-628 IS the user-cited reference | **ALREADY-IN-PLAN — Q1 EVIDENCE.** This is exactly the pattern v5 plan Block N adopts: dynamic post-processing in tool-definition builder, not static descriptions. v5 must implement same `get_tool_definitions()` post-processing pass for skill+tool cross-refs. |
| A37 | Pitfalls — Gateway dual guards | "Two sequential guards: (1) base adapter `_pending_messages` queue when session active, (2) gateway runner intercepts /stop, /new, /queue, /status, /approve, /deny. Any new command that must reach runner while agent blocked MUST bypass BOTH guards and dispatch inline, not via `_process_message_background()` (races session lifecycle)." | — | OUT-OF-SCOPE |
| A38 | Pitfalls — Squash merges from stale | "Before squash-merging a PR, ensure branch is up-to-date with main (`git fetch origin main && git reset --hard origin/main` in worktree, re-apply commits). Stale branch's version of unrelated file silently overwrites recent main fixes when squashed. Verify with `git diff HEAD~1..HEAD` after — unexpected deletions = red flag." | — | NOTABLE git-hygiene rule, applies to v5 dev process |
| A39 | Pitfalls — Don't wire dead code without E2E | "Unused code never shipped was dead for a reason. Before wiring an unused module into a live code path, E2E test the real resolution chain with actual imports (not mocks) against a temp HERMES_HOME." | — | NOTABLE — "no Frankenstein refactor" rule, applies to v5 cherry-picks from v4/Runnable/Hermes/LF |
| A40 | Pitfalls — Tests must not write to `~/.hermes` | `_isolate_hermes_home` autouse fixture in `tests/conftest.py` redirects HERMES_HOME to temp dir. Profile-tests also mock `Path.home()`. | — | OUT-OF-SCOPE |
| A41 | Testing — `scripts/run_tests.sh` mandatory | "ALWAYS use `scripts/run_tests.sh` — do not call `pytest` directly. Wrapper enforces hermetic CI parity: unset all `*_API_KEY`/`*_TOKEN`, TZ=UTC, LANG=C.UTF-8, 4 xdist workers matching GHA ubuntu-latest. Direct pytest on 16+core dev machine with API keys diverges from CI." | — | OUT-OF-SCOPE BUT NOTABLE — v5 test parity discipline; SageMaker test invocation needs same hermeticity |
| A42 | Testing — `tests/conftest.py` autouse fixture | Enforces 4 of 5 hermeticity points so ANY pytest invocation (IDE etc.) gets hermetic behaviour. Wrapper is belt-and-suspenders. | — | NOTABLE pattern |
| A43 | Testing — without wrapper | "If you must (Windows or IDE shelling pytest directly), at minimum activate venv and pass `-n 4`. Worker count > 4 surfaces test-ordering flakes CI never sees." | — | NOTABLE |
| A44 | Testing — **Don't write change-detector tests** (POLICY) | "A test is a change-detector if it fails whenever data EXPECTED TO CHANGE gets updated — model catalogs, config version numbers, enumeration counts, hardcoded provider-model lists. These add no behavioral coverage; they just guarantee routine source updates break CI. **Don't write:** `assert 'gemini-2.5-pro' in _PROVIDER_MODELS['gemini']`, `assert DEFAULT_CONFIG['_config_version'] == 21`, `assert len(_PROVIDER_MODELS['huggingface']) == 8`. **Do write:** existence checks, migration-bump-to-current asserts, set-disjointness invariants, every-model-has-context-length contract. Rule: if test reads like a snapshot of current data, delete it. If it reads like a contract about how two pieces of data MUST RELATE, keep it." | — | **CRITICAL NOTABLE** — v5 test discipline must adopt this. Many existing v4 tests are change-detectors. |

---

## 4. ALREADY-IN-PLAN (consolidated)

| Plan Block | Hermes capabilities covered |
|---|---|
| Block A (skeleton, project layout) | A2, A3, A5 |
| Block J (extended thinking, caching, compaction) | #3, #4, #5, #7, #18, #19, #24, #28, #34, #35, #39, #40b, #40c, #40d, #40e, #40g, #40j, A8, A28 (CRITICAL cache invariant), A36 |
| Block L (skills) | A16, A25, A26, A27 |
| Block M (subagents) | #27, #33, A35 |
| Block N (coding loop, dynamic tool ref, transports, error classification) | #1 (Bedrock branch only), #2, #4, #5, #11 (subset), #20, #23, #25 (Bedrock), #30, #31, #32, #33, #37, #38, #41, #42, #43, #52, A7, A14, **A36 (Q1 evidence — dynamic cross-tool ref via `get_tool_definitions()` post-processing)** |
| Block O (token tracking, telemetry) | #6 (subset), #44, #47 |

**Q1 evidence highlight (AGENTS.md:627-628 = pitfall A36):** Hermes prohibits hardcoded cross-tool references in static schema descriptions and instead requires dynamic injection in `get_tool_definitions()` (model_tools.py) using `browser_navigate`/`execute_code` post-processing as canonical. v5 plan Block N already commits to identical dynamic post-processing for skill+tool cross-references — Hermes confirms the pattern works at production scale.

---

## 5. OUT-OF-SCOPE (single-user / Bedrock-only / no-deferral verified)

These Hermes capabilities are explicitly OUT-OF-SCOPE for v5.0.1 because they require infrastructure or constraints v5 does not have. None of them is a deferred v5 feature — each is excluded by hard constraint.

| Hermes feature | Why OUT-OF-SCOPE |
|---|---|
| Multi-provider failover chain (#16, #21, #29, #40f, #40h, #13) | v5 = single Bedrock provider, single Claude model. No fallback chain to switch to. |
| Credential pool rotation (#12) | v5 = single SageMaker IAM identity. No multi-key pool. |
| Provider-specific 401 refresh (Codex/Nous/Copilot/Anthropic-OAuth) (#13) | v5 = Bedrock IAM via boto3 STS. No OAuth refresh paths. |
| Long-context-tier 429 handling (#15) | Bedrock has fixed quota tiers, no Claude Max 1M subscription model. |
| Anthropic thinking-block signature recovery (#14) | Bedrock Converse signs differently; v5 cache-aware design avoids the mid-turn mutation that triggers this in Anthropic Messages API. |
| Stream-drop SSE diagnosis (#22, #36, #40a) | Bedrock Converse non-streaming in v5.0.1 (per Q1 transport decision). |
| Codex `incomplete` continuation + intermediate-ack (#29, #40h) | No `codex_responses` transport in v5. |
| Nous rate-limit cross-session record (#8, #17) | Single-user, single-session — no cross-process coordination needed. |
| UnicodeEncodeError surrogate/ASCII recovery (#10) | SageMaker is UTF-8 by default; clipboard-paste edge cases not in v5 ipynb scope. |
| `post_api_request`/`post_llm_call`/`on_session_end` plugin hooks (#26, #45, #51, A22, A23, A24) | v5 has NO plugin system. Skills are not plugins (different surface). |
| External memory provider sync (#49, #50) | v5 uses local file-based memory only (Bedrock-only constraint, no external network). |
| `/steer` mid-turn user steering (#46) | No interactive steering UI in ipynb. |
| Skill-nudge auto-review (#48) | v5 keeps skill management explicit (per "skills must not patch core" rule). |
| `main()` Fire CLI entrypoint (#53) | v5 entry = ipynb cell, not module-level CLI. |
| Profile system (A4, A30, A31, A32, A40) | Single-user SageMaker, single profile. |
| All TUI / Ink / dashboard / xterm.js / PTY surfaces (A9, A12, A13, A29) | v5 UI = chat.ipynb canonical, no replacement. |
| Slash command registry (A10, A11) | No slash commands in ipynb. |
| Skin/theme engine (A21) | No display layer to skin. |
| `simple_term_menu` / curses_ui pitfall (A33) | No interactive menus in v5. |
| Gateway dual-guard pattern (A37) | No gateway in v5. |
| `MESSAGING_CWD` deprecation (A20) | No messaging adapter. |
| Slack/Telegram/Discord/etc. adapters (mentioned passim) | v5 has no messaging surface. |
| `scripts/run_tests.sh` wrapper (A41, A42, A43) | Out-of-scope for SageMaker runtime; the *discipline* (hermetic CI parity) is NOTABLE for v5 test process. |

---

## 6. NOTABLE patterns (worth referencing in v5 design docs but not Block-N-style adopted code)

- **A6** — "Doc shows minimum subset; code is canonical (~60-param `__init__`)." Discipline for v5 docs.
- **A10/A11** — Single-source-of-truth registry pattern (one `COMMAND_REGISTRY` → CLI/gateway/help/menu/autocomplete derive automatically). Applicable architecturally to v5 tool registry.
- **A13** — Single-surface UI rule: "do not re-implement primary chat experience elsewhere." v5 equivalent: do not build a parallel UI to chat.ipynb.
- **A18** — Config-version bump ONLY for actual migrations.
- **A23** — "Plugins MUST NOT modify core files." v5 equivalent: skills must not patch `sagemaker_agent.py`. (v4.9.5 self-patching skills were re-classified as personal-not-insurance for exactly this reason — see MEMORY `feedback_sagemaker_bedrock_only_constraint`.)
- **A28 (CRITICAL)** — Cache invariant: never rebuild system prompt / change toolsets / reload memories mid-conversation. v4 currently violates this in places; v5.0.1 must enforce. Adopt `--now` deferred-invalidation pattern for any state-mutating control.
- **A34** — `\033[K` ANSI pitfall — relevant if v5 ipynb adds spinner-style display.
- **A38** — Stale-branch squash-merge silent reverts. Git hygiene for v5 dev.
- **A39** — "Don't wire dead code without E2E." v5 cherry-picks from v4/Runnable/Hermes/LF must each be E2E-validated, not just code-grafted.
- **A41** — Hermetic test parity. v5 SageMaker test invocation needs equivalent (unset env vars, fixed TZ/locale, bounded workers).
- **A44 (CRITICAL)** — Don't write change-detector tests. Many v4 tests are exactly this (catalog snapshots, version literal asserts, count asserts). v5 test refactor should convert them to invariants per Hermes rule.

---

## 7. Summary

**Coverage:** Final 2576 lines of run_agent.py (turn-end recovery, post-loop wrap, chat wrapper, Fire main) + 765 lines of AGENTS.md + top-level Glob of remaining repo (truncated at depth 4 — deep `agent/`, `gateway/`, `hermes_cli/`, `tools/`, `plugins/`, `tests/` not enumerable in one call but their roles documented in AGENTS.md and prior chunks).

**Findings (53 run_agent.py capabilities + 44 AGENTS.md instruction patterns = 97 total):**
- **ALREADY-IN-PLAN:** ~58 (all error-recovery loops, compression, length-continuation, tool-name/JSON repair, empty-response retries, prefill, prompt-only token compression rule, dynamic cross-tool-ref pattern, turn-exit diagnostics, result envelope, content-with-tools fallback, tool-call dedup/cap, AGENTS.md skill discipline, A36-Q1 evidence)
- **OUT-OF-SCOPE:** ~32 (multi-provider failover, credential pool, OAuth refresh, plugins, profiles, TUI/CLI/skin/gateway/messaging, codex_responses, anthropic-mid-turn-sig recovery, long-context tier, Nous cross-session, Unicode codec recovery, Fire main, MESSAGING_CWD, all 13+ messaging adapters)
- **NOTABLE (design discipline, not code):** ~7 (single-source-of-truth registry, A28 cache invariant CRITICAL, A23 plugins-don't-patch-core CRITICAL, A39 no-wire-dead-code, A44 no-change-detector-tests CRITICAL, A41 hermetic test parity, A38 squash-merge git hygiene)

**Q1 evidence point — AGENTS.md:627-628:** confirmed exactly as expected. Hermes rule "tool schema descriptions must not mention tools from other toolsets by name" with the canonical solution "add it dynamically in `get_tool_definitions()` in `model_tools.py` — see browser_navigate/execute_code post-processing blocks." This is the precise pattern v5 plan Block N has committed to for skill+tool cross-references.

**No NEW deferrals identified.** Every Hermes capability either (a) is already covered by a v5.0.1 plan block, (b) is hard-blocked by Bedrock-only / single-user constraints (so cannot be deferred — there is no v5.0.2 to defer to), or (c) is a discipline pattern that informs v5 design docs without adding code.

**Three CRITICAL findings v5 must adopt:**
1. **A28 prompt-cache invariant** — v4 partially violates this; v5.0.1 must enforce no-mid-turn-mutation rule and `--now` deferred-invalidation for any control that mutates system state.
2. **A36 dynamic cross-tool reference** — Q1 evidence confirmed; v5 Block N already aligned.
3. **A44 no-change-detector-tests** — v4 tests have many; v5 test refactor should rewrite as invariants/contracts.

**Files referenced (absolute paths):**
- `D:/Github/hermes-agent/run_agent.py` (lines 10305-12880)
- `D:/Github/hermes-agent/AGENTS.md`
- `D:/Github/hermes-agent/.plans/streaming-support.md`, `D:/Github/hermes-agent/.plans/openai-api-server.md`
- `D:/Github/hermes-agent/RELEASE_v0.{2..7}.0.md`
- `D:/Github/sagemaker-coding-agent/compact_v4/MAIN/agent/sagemaker_agent.py` (v4 baseline)
- `D:/Github/sagemaker-coding-agent/compact_v5/_phase_2/wave_4/Q1_EVIDENCE_MATRIX.md`
