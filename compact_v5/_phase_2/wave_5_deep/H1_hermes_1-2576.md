# Hermes run_agent.py 1-2576 — line-by-line scan

## Read audit
- Lines read: 1-2576 (total 2576 lines in slice; full file 12,880 LOC)
- Read in 4 segments via Read tool (1-700, 700-1400, 1400-2000, 2001-2576)
- Functions / classes / module-level constants identified: 32
  - Module-level helpers: `_get_proxy_from_env`, `_get_proxy_for_base_url`, `_install_safe_stdio`, `_is_destructive_command`, `_should_parallelize_tool_batch`, `_extract_parallel_scope_path`, `_paths_overlap`, `_sanitize_surrogates`, `_sanitize_structure_surrogates`, `_sanitize_messages_surrogates`, `_escape_invalid_chars_in_json_strings`, `_repair_tool_call_arguments`, `_strip_non_ascii`, `_sanitize_messages_non_ascii`, `_sanitize_tools_non_ascii`, `_sanitize_structure_non_ascii`, `_routermint_headers`, `_pool_may_recover_from_rate_limit`, `_qwen_portal_headers`
  - Module-level constants: `_NEVER_PARALLEL_TOOLS`, `_PARALLEL_SAFE_TOOLS`, `_PATH_SCOPED_TOOLS`, `_MAX_TOOL_WORKERS`, `_DESTRUCTIVE_PATTERNS`, `_REDIRECT_OVERWRITE`, `_SURROGATE_RE`, `_QWEN_CODE_VERSION`
  - Classes: `_SafeWriter`, `IterationBudget`, `AIAgent` (start of huge class — only ctor + early helpers in this slice)
  - `AIAgent` methods seen in slice: `base_url` getter/setter, `__init__` (832-2008), `reset_session_state` (2009), `switch_model` (2048), `_safe_print` (2217), `_vprint` (2235), `_should_start_quiet_spinner` (2262), `_should_emit_quiet_tool_messages` (2281), `_emit_status` (2295), `_emit_warning` (2315), `_emit_auxiliary_failure` (2332), `_current_main_runtime` (2343), `_check_compression_model_feasibility` (2353), `_replay_compression_warning` (2476), `_is_direct_openai_url` (2493), `_resolved_api_call_timeout` (2503), `_resolved_api_call_stale_timeout_base` (2523), `_compute_non_stream_stale_timeout` (2547), `_is_openrouter_url` (2561), `_anthropic_prompt_cache_policy` (2565, body extends past slice)

## Capabilities table

| # | Capability | Hermes line:N | v4 has? (file:line or NO) | v5.0.1 needs? | Target Block | Graft strategy |
|---|---|---|---|---|---|---|
| 1 | `_SafeWriter` stdio wrapper — catches OSError/ValueError on broken pipes/closed stdout (systemd, Docker, headless, ThreadPoolExecutor teardown) | 123-169 | NO (v4 prints raw; SageMaker notebook stdout never breaks) | NO | OUT-OF-SCOPE | Notebook UI never has broken pipe; v4 chat.ipynb canonical UI doesn't need this. |
| 2 | `_install_safe_stdio` global stdout/stderr wrap | 205-210 | NO | NO | OUT-OF-SCOPE | Same as #1 — notebook environment. |
| 3 | `_get_proxy_from_env` / `_get_proxy_for_base_url` HTTPS_PROXY + NO_PROXY honor | 172-202 | NO | NO | OUT-OF-SCOPE | Bedrock-only, AWS SDK handles proxy via boto3 config. |
| 4 | `IterationBudget` — thread-safe counter, parent + subagents share or have independent budget; `refund()` for `execute_code` | 213-254 | v4 has plain `max_iterations` int counter in chat loop (sagemaker_agent.py main loop), no shared budget across subagents | YES — v5 has subagent delegation (per Plan v3). Need shared budget so parent + 4 subagents don't blow the cap. | **Block N** (parallel-exec / subagent infra) | Port `IterationBudget` class verbatim. Wire into v5 subagent spawn so parent passes its budget into child or child gets a sub-cap from `delegation.max_iterations`. ~30 LOC. |
| 5 | `_NEVER_PARALLEL_TOOLS` frozenset — interactive tools that break under concurrency | 257-259 | NO (v4 sequential only) | YES (v5.0.1 keeps v4 sequential by default; only relevant if Block N parallel-exec activated). For Bedrock single-user, only `clarify`-style tools matter. | Block N | Keep frozenset minimal: `{"clarify"}` if v5 has clarify, else `{}`. |
| 6 | `_PARALLEL_SAFE_TOOLS` frozenset — read-only tools | 262-274 | NO | YES — needed for Block N safety gate | Block N | Map to v4 tool names: `{"read_file", "tool_glob", "tool_grep", "tool_list_dir", "skill_view", "skills_list"}`. ~10 entries. |
| 7 | `_PATH_SCOPED_TOOLS` — file tools allowed concurrent if paths disjoint | 277 | NO | YES (advanced — Block N optional refinement) | Block N | `{"read_file", "tool_write_file", "tool_edit_file"}`. With `_extract_parallel_scope_path` + `_paths_overlap`. |
| 8 | `_MAX_TOOL_WORKERS = 8` (concurrent worker cap) | 280 | NO | YES — Block N | Block N | Single-user SageMaker: cap at 4 workers (lower than 8) given Bedrock TPM. |
| 9 | `_DESTRUCTIVE_PATTERNS` regex (rm/mv/cp/sed -i/dd/git reset/etc.) + `_REDIRECT_OVERWRITE` (`>` not `>>`) | 283-308 | NO — v4 SecurityManager.validate_command (line 1854) does substring/allowlist, NOT a destructive heuristic regex | YES (defense-in-depth on bash tool) — v4 already has SecurityManager but Hermes adds an extra "looks destructive" hint regex that can bias scheduling | Block N (concurrency gate) AND security defense-in-depth | The regex itself is small (10 LOC). Useful as a **scheduling filter** ("don't parallelize destructive bash") rather than security. v4 SecurityManager handles security. Add `_is_destructive_command()` to v5 only if Block N parallel bash is enabled. **Otherwise SKIP** — v4 sequential bash means the regex serves no purpose. |
| 10 | `_should_parallelize_tool_batch(tool_calls)` — full safety oracle (path overlap + tool whitelist + arg-parse failure → sequential) | 311-352 | NO | YES — core of Block N | **Block N (parallel-exec)** — Plan v3 already cites this range :311-355 | Port intact; replace `tc.function.name` access pattern with v4 ToolCall fields. ~40 LOC. |
| 11 | `_extract_parallel_scope_path` — normalize file path for overlap check (handles `expanduser`, absolute, cwd-relative) | 355-369 | NO | YES — pairs with #10 | Block N | Port. ~14 LOC. Note: Hermes deliberately avoids `resolve()` because file may not exist yet — graft this nuance. |
| 12 | `_paths_overlap` — prefix-based path conflict detection | 372-380 | NO | YES — pairs with #10 | Block N | Port. ~9 LOC. |
| 13 | `_sanitize_surrogates` — replace lone UTF-16 surrogates with U+FFFD | 384-397 | NO | YES — Bedrock Converse API rejects surrogates inside JSON (model output → tool_result content) | **NEW Block (defense)** — call it "Block W: payload-sanitization" or fold into Block I serialization layer | Port `_SURROGATE_RE` + `_sanitize_surrogates`. Trigger before every Bedrock `converse()` call on every message string. Cheap (regex no-op when clean). ~15 LOC. |
| 14 | `_sanitize_structure_surrogates` (recursive walk dict/list) | 404-434 | NO | YES — needed for nested `reasoning_details` etc. | Same Block W | Port. ~30 LOC. |
| 15 | `_sanitize_messages_surrogates` — full message-list walker (content/name/tool_calls/reasoning fields) | 437-502 | NO | YES — same reason | Block W | Port + adapt to v4 ToolCall/Response shapes. ~70 LOC. |
| 16 | `_escape_invalid_chars_in_json_strings` — escape unescaped control chars inside JSON string literals | 505-544 | NO | LIKELY — Bedrock-hosted Claude rarely emits bad JSON, but Haiku 4.5 occasionally does on tool_call args | Block I (tool-call repair) | Port. ~40 LOC. |
| 17 | `_repair_tool_call_arguments` — multi-pass JSON repair (strict=False reparse, trailing comma, brace balance, escape) → fallback `"{}"` | 547-641 | v4 has basic try/except json.loads in tool dispatch; **no multi-pass repair** | YES — Bedrock Claude DOES emit malformed tool_call.input on long contexts (Haiku quirk). Empty `{}` fallback is better than crash. | **Block I (tool-call durability)** — Plan v3 mentions Block I fuzzy-reuse; this complements it | Port verbatim. ~95 LOC. Replace logger calls with v4 logger. Critical resilience feature. |
| 18 | `_strip_non_ascii` + `_sanitize_messages_non_ascii` + `_sanitize_tools_non_ascii` + `_sanitize_structure_non_ascii` — last-resort ASCII fallback for LANG=C systems | 644-743 | NO | NO | OUT-OF-SCOPE — SageMaker is always UTF-8 | OUT-OF-SCOPE. ~100 LOC saved. |
| 19 | `_routermint_headers` (UA for RouterMint Cloudflare bypass) | 762-768 | NO | NO | OUT-OF-SCOPE | Bedrock-only, no RouterMint. |
| 20 | `_pool_may_recover_from_rate_limit` — credential-pool rotation logic | 771-793 | NO | NO | OUT-OF-SCOPE | Bedrock single AWS account, no credential pool. |
| 21 | `_qwen_portal_headers` (Qwen DashScope) | 796-806 | NO | NO | OUT-OF-SCOPE | Bedrock-only. |
| 22 | `AIAgent.__init__` — provider auto-detect (codex_responses / anthropic_messages / bedrock_converse / chat_completions from base_url) | 832-1313 | v4 hardcodes Bedrock | NO (the dispatch logic) | OUT-OF-SCOPE | v4 is Bedrock-only by hard constraint. v5 keeps that. |
| 23 | Bedrock branch of AIAgent.__init__ (`api_mode == "bedrock_converse"`) — region extraction from base_url, **guardrail config** (guardrailIdentifier / guardrailVersion / streamProcessingMode / trace), AnthropicBedrock SDK option | 1242-1312 | v4 BedrockClient (line 2378) — **no guardrail support** | YES (guardrail support is genuinely useful for insurance company) — but v5.0.1 may defer if user doesn't enable | **Block ?** (Bedrock guardrails — NEW capability not in plan) | NEW: lines 1287-1312 show `bedrock.guardrail.*` config block with 4 fields. ~25 LOC graft into v5 BedrockClient. **Add to plan as a small new sub-block**. |
| 24 | `AnthropicBedrock` SDK alternative for Bedrock+Claude (full prompt caching, thinking budgets, adaptive thinking) | 1246-1260 | v4 uses raw boto3 `bedrock-runtime.converse` | DECISION: stick with v4 boto3 path (zip-only ship, fewer deps). AnthropicBedrock SDK adds an extra wheel. | OUT-OF-SCOPE for v5.0.1 | OUT-OF-SCOPE — v4 baseline + native cache_control already gives caching. Re-evaluate in v5.1. |
| 25 | Fine-grained tool streaming beta header for Claude on OpenRouter | 1391-1407 | NO | NO | OUT-OF-SCOPE — no OpenRouter | OUT-OF-SCOPE. |
| 26 | Fallback chain (`_fallback_chain`, list of {provider, model}) — typed retry chain on 429/overload/conn-fail | 1426-1449 | NO — v4 has single retry loop, no model fallback | NO (single Bedrock model) | OUT-OF-SCOPE | OUT-OF-SCOPE — Bedrock-only single model in v5.0.1. Could add fallback Haiku→Sonnet later. |
| 27 | `tools` loaded via `get_tool_definitions(enabled_toolsets, disabled_toolsets, quiet_mode)` and `valid_tool_names` set built from result | 1452-1472 | v4 has flat tool list (sagemaker_agent.py) — no toolset filtering | MAYBE — v5 has skills, not toolsets. Filtering by skill is already in plan. | OUT-OF-SCOPE (different abstraction) | OUT-OF-SCOPE — v4 skill model is the canonical one. |
| 28 | `enabled_toolsets` / `disabled_toolsets` / `check_toolset_requirements()` requirement-validation pattern | 1474-1479 | NO | NO | OUT-OF-SCOPE | OUT-OF-SCOPE. |
| 29 | `ephemeral_system_prompt` — system prompt that runs but is NOT saved to trajectory (key for safe agent infra) | 949, 1486-1488 | NO — v4 always persists full system prompt to session | YES — **Plan v3 already cites :850 + :1486-1488 in Block N** | Block N (subagent ephemeral context) | Already in plan. Confirm graft target: subagent system-prompt path in v5 multi-agent. ~5 LOC. |
| 30 | `prompt_caching` config block — `cache_ttl` 5m vs 1h tier (1h costs 2x write but amortizes long sessions >5min idle) | 1148-1157 | v4 has cache_control with default 5m TTL (Bedrock supports both per AWS docs) | YES — small win for long SageMaker sessions | **Block (caching) — extend existing v5 caching plan** | Add `cache_ttl: "5m" | "1h"` config knob to v5 config.py (only "5m" / "1h" accepted, default "5m"). ~6 LOC. |
| 31 | Anthropic prompt cache policy decision matrix (`_anthropic_prompt_cache_policy`) — returns `(should_cache, use_native_layout)` | 2565-2576+ | v4 has hardcoded cache_control on Bedrock | PARTIAL — v5 only needs the "Bedrock + Claude → cache=True, native_layout=True" branch | OUT-OF-SCOPE (the dispatch); IN-SCOPE (the policy) | Cherry-pick the Bedrock-true branch only. Most of this method is OpenRouter/Anthropic-native dispatch noise. |
| 32 | `_check_compression_model_feasibility` — at session start, validate aux compression model context >= MINIMUM_CONTEXT_LENGTH (64K), auto-lower threshold if aux smaller than main, emit user-visible warning | 2353-2474 | NO — v4 Compactor uses same model for compression as main turn | YES — IF v5 ever uses a separate aux model. Currently v5.0.1 uses same Bedrock model for compaction → not needed. | OUT-OF-SCOPE for v5.0.1 (single-model) | DEFER — re-evaluate when v5 introduces aux model split (none planned for 5.0.1). |
| 33 | `_replay_compression_warning` — gateway warning replay pattern | 2476-2491 | NO | NO | OUT-OF-SCOPE | OUT-OF-SCOPE — single-user SageMaker, no gateway. |
| 34 | `_resolved_api_call_timeout` — provider/model-tier timeout resolution (per-model > provider-wide > env > default 1800s) | 2503-2521 | v4 uses boto3 default timeouts | MINOR — could expose `bedrock.request_timeout_seconds` config knob | OUT-OF-SCOPE for v5.0.1 (low value) | OUT-OF-SCOPE. |
| 35 | `_resolved_api_call_stale_timeout_base` + `_compute_non_stream_stale_timeout` — adaptive stale-detection timeout based on message size (>100K tokens → 600s, >50K → 450s, else base) | 2523-2559 | NO — v4 has no stale-stream detection | NO — Bedrock SDK handles its own request timeout, no SSE in v4 path | OUT-OF-SCOPE | OUT-OF-SCOPE. |
| 36 | `reset_session_state` — DRY helper resetting all token/cache/cost counters + `on_session_reset` hook on context engine | 2009-2046 | v4 inlines counter reset | YES — small DRY win | Block (cleanup / refactor) | Port. ~20 LOC. Useful when v5 adds `/reset` slash command. |
| 37 | `switch_model` — live in-place model swap (rebuild client, refresh prompt-caching policy, update compressor, prune fallback chain to drop old/new provider entries) | 2048-2215 | NO — v4 single-model only | NO for v5.0.1 (single Bedrock model). YES for v5.1+. | OUT-OF-SCOPE for v5.0.1 | OUT-OF-SCOPE — defer to v5.1 if multi-model added. |
| 38 | `_emit_status` / `_emit_warning` / `_emit_auxiliary_failure` — structured status callback channel (CLI vprint + status_callback callable) | 2295-2341 | v4 prints directly to stdout | YES (small win) — clean separation lets ipynb UI subscribe to status events | **Block (UI events)** — could fit notebook progress display | OPTIONAL graft — ~30 LOC. Helpful when v5 ipynb adds progress widgets. |
| 39 | `_safe_print` / `_vprint` — print routing through `_print_fn` (ANSI-safe via prompt_toolkit) + stream-consumer suppression | 2217-2260 | NO | NO | OUT-OF-SCOPE | OUT-OF-SCOPE — notebook uses display(), no ANSI. |

## ALREADY-IN-PLAN (in slice 1-2576)

These items are already covered by existing v3 Plan blocks for the ranges in the slice:

- **`_should_parallelize_tool_batch` and helpers (lines 311-380)** — Plan v3 Block N explicitly cites `:311-355`. The plan should be expanded to also cite **:355-380** (`_extract_parallel_scope_path`, `_paths_overlap`) which are the helper pair making path-scoped parallelism possible.
- **`ephemeral_system_prompt` (lines 850, 949, 1486-1488)** — Plan v3 Block N explicitly cites `:850 + :1486-1488`. Confirmed in slice.
- **`IterationBudget` (lines 213-254)** — implicit in Block N (subagents) but **not yet pinned to a line range in plan**. Should be added: "Port `IterationBudget` 213-254".

## OUT-OF-SCOPE (categorical reasons)

| Category | Items | Reason |
|---|---|---|
| **Multi-provider dispatch** | provider auto-detect (1242-1313 except Bedrock branch), `switch_model`, `_fallback_chain`, OpenRouter / RouterMint / Qwen / Copilot / Kimi headers | v5.0.1 is Bedrock-only by hard constraint (`feedback_sagemaker_bedrock_only_constraint`) |
| **Headless / daemon resilience** | `_SafeWriter`, `_install_safe_stdio`, broken-pipe handling | SageMaker notebook UI has no broken pipe; v4 chat.ipynb canonical UI |
| **Proxy / NO_PROXY** | `_get_proxy_*` | Bedrock via boto3 handles proxy from AWS_* config |
| **ASCII-only fallback** | `_strip_non_ascii`, `_sanitize_messages_non_ascii`, `_sanitize_tools_non_ascii`, `_sanitize_structure_non_ascii` | SageMaker is always UTF-8 (no LANG=C scenarios) |
| **AnthropicBedrock SDK path** | lines 1246-1260 | v4 uses raw boto3 — adding anthropic-bedrock SDK adds a wheel; defer to v5.1 |
| **Streaming SSE stale detection** | `_compute_non_stream_stale_timeout` | v4 boto3 path has its own timeout handling |
| **Aux compression model feasibility** | `_check_compression_model_feasibility` (2353-2474) | v5.0.1 uses same model for compaction; not yet split |
| **Gateway-mode plumbing** | `_replay_compression_warning`, `status_callback` lifecycle | Single-user SageMaker has no Telegram/Discord/Slack gateway |
| **Toolset filtering** | `enabled_toolsets`, `disabled_toolsets`, `check_toolset_requirements` | v4 uses skill-based loading — different abstraction; not portable |
| **Credential pools** | `_pool_may_recover_from_rate_limit` | Single AWS account, single credential |

## NEW additions to v5 Plan (not yet in plan, found in this slice)

| # | Item | Hermes line | Suggested target block | Estimated LOC | Priority |
|---|---|---|---|---|---|
| **A** | **`IterationBudget` class (213-254)** — pin to Block N as explicit line range | 213-254 | Block N | 30 | HIGH (subagent infra needs it) |
| **B** | **`_repair_tool_call_arguments` (547-641)** + `_escape_invalid_chars_in_json_strings` (505-544) — multi-pass tool_call JSON repair with `{}` fallback | 505-641 | **NEW Block I extension or new Block "tool_call durability"** | 130 | HIGH (Haiku malformed args is observed) |
| **C** | **Surrogate sanitization** — `_SURROGATE_RE` + `_sanitize_surrogates` + `_sanitize_structure_surrogates` + `_sanitize_messages_surrogates` (384-502) | 384-502 | **NEW Block "payload sanitization"** (call before every Bedrock converse()) | 115 | MEDIUM (defense-in-depth) |
| **D** | **Bedrock Guardrails config** — `bedrock.guardrail.{guardrail_identifier, guardrail_version, stream_processing_mode, trace}` (1292-1312) | 1287-1312 | **NEW small block "Bedrock guardrails"** | 25 | MEDIUM (insurance compliance use-case) |
| **E** | **Cache TTL config** — `prompt_caching.cache_ttl` ∈ {"5m", "1h"} (1148-1157) | 1148-1157 | extend existing v5 caching block | 6 | LOW (small win for long sessions) |
| **F** | **`reset_session_state` DRY helper (2009-2046)** | 2009-2046 | optional refactor / `/reset` command | 20 | LOW |
| **G** | **`_emit_status` / `_emit_warning` event channel (2295-2341)** | 2295-2341 | notebook progress / future UI events | 30 | LOW |

## Range cross-check vs Plan v3 cited Hermes ranges

Plan v3 cites for Block N:
- `:311-355` — confirmed in slice (parallelism oracle)
- `:8274-8523`, `:8581-8584` — outside slice (later chunks)
- `:4639-4655` (dedup), `:4689-4720` (fuzzy) — outside slice
- `:850 + :1486-1488` (ephemeral) — confirmed in slice
- `AGENTS.md:627-628` — different file

In-slice gaps the plan does NOT yet cover (this scan's contribution):
- `:213-254` IterationBudget — should be added to Block N references
- `:355-380` parallelism path-scope helpers — extension of `:311-355`
- `:384-502` surrogate sanitization — NEW BLOCK
- `:505-641` tool_call JSON repair — NEW BLOCK or extend Block I
- `:1148-1157` cache_ttl — extend caching block
- `:1287-1312` Bedrock guardrails — NEW small block

## Summary

In Hermes lines 1-2576, **39 distinct capabilities** identified.

- **6 ALREADY IN PLAN** (parallelism oracle 311-355, ephemeral prompt 850/1486-1488 — all Block N)
- **7 NEW ADDITIONS recommended** (A-G above): IterationBudget pin, tool_call JSON repair, surrogate sanitization, Bedrock guardrails, cache_ttl config, reset_session_state, emit_status events
- **22 OUT-OF-SCOPE** (multi-provider, headless, proxy, ASCII fallback, gateway plumbing, switch_model, fallback chains, etc. — all violate v5.0.1 Bedrock-only / SageMaker-notebook constraints)

**Highest-value grafts from slice 1-2576:**
1. `_repair_tool_call_arguments` (547-641) — 130 LOC; observed Haiku malformed-args resilience
2. `IterationBudget` (213-254) — 30 LOC; required for subagent infra in Block N
3. Surrogate sanitization (384-502) — 115 LOC; defense-in-depth for Bedrock JSON
4. Bedrock guardrails config (1287-1312) — 25 LOC; insurance compliance fit
5. Path-scoped parallelism helpers (355-380) — 23 LOC; completes Block N parallelism

Total NEW graft estimate from this chunk: **~360 LOC** of pure-value additions to v5.0.1.

No deferrals proposed — all NEW items are recommended for v5.0.1 inclusion per `feedback_v5_no_deferrals`.
