# R4 — Runnable services/ batch 1 deep line-by-line scan

**Scanned**: 2026-05-01
**Scope**: `_archive/compare_code/gg-claude-code-runnable/src/services/{api,compact,contextCollapse,extractMemories,SessionMemory,AgentSummary,MagicDocs,PromptSuggestion,autoDream,sessionTranscript,toolUseSummary,tools}` + root files `claudeAiLimits.ts`, `claudeAiLimitsHook.ts`, `tokenEstimation.ts`.
**Total LOC scanned**: ~23,123 (Bun-bundle-stripped TypeScript; 8 stub files = `export default {}`).
**Compared against**: `compact_v4/MAIN/agent/sagemaker_agent.py` (12088 LOC monolith).
**Existing v5 plan**: `synthesis/V5_PHASE_2_PLAN_v3.md` Blocks A / B / H / L / G2 / N (post-no-deferrals 2026-04-30).
**Existing port log**: `wave_4/Q1_EVIDENCE_MATRIX.md` (172 rows).
**Constraints**: single-user SageMaker, Bedrock-only, v4 chat.ipynb canonical UI, NO DEFERRALS.

---

## File inventory + per-file LOC + stub status

### `services/api/` (20 files, 10,481 LOC)
| File | LOC | Stub | In current plan? |
|---|---|---|---|
| `errors.ts` | 1207 | no | YES (Block L — partial; line ranges cited) |
| `withRetry.ts` | 822 | no | YES (Block L — partial; getRetryAfterMs cited) |
| `claude.ts` | 3419 | no | NO — main client wrapper (out-of-batch-1 audit) |
| `client.ts` | 389 | no | NO — pure provider shim |
| `promptCacheBreakDetection.ts` | 727 | no | YES (Block L — partial; 8 functions cited) |
| `bootstrap.ts` | 141 | no | NO |
| `errorUtils.ts` | 260 | no | NO |
| `filesApi.ts` | 748 | no | NO (Files API — Bedrock has no equivalent endpoint) |
| `firstTokenDate.ts` | 60 | no | NO |
| `grove.ts` | 357 | no | NO (Anthropic-internal ant survey) |
| `logging.ts` | 788 | no | NO |
| `metricsOptOut.ts` | 159 | no | NO |
| `overageCreditGrant.ts` | 137 | no | NO (subscription-only) |
| `referral.ts` | 281 | no | NO (subscription-only) |
| `sessionIngress.ts` | 514 | no | NO (claude.ai SDK ingress) |
| `ultrareviewQuota.ts` | 38 | no | NO |
| `usage.ts` | 63 | no | NO |
| `dumpPrompts.ts` | 226 | no | NO |
| `emptyUsage.ts` | 22 | no | NO |
| `adminRequests.ts` | 119 | no | NO (admin/anthropic-only) |

### `services/compact/` (16 files, 3,961 LOC)
| File | LOC | Stub | In current plan? |
|---|---|---|---|
| `compact.ts` | 1705 | no | YES (Block A — combined v4) |
| `microCompact.ts` | 530 | no | YES (Block A) |
| `autoCompact.ts` | 351 | no | YES (Block A — circuit breaker) |
| `sessionMemoryCompact.ts` | 630 | no | YES (Block H, but listed as-is — see § new findings) |
| `prompt.ts` | 374 | no | partial (compactPrompt referenced; full text not yet ported) |
| `apiMicrocompact.ts` | 153 | no | NO — server-side context-management (NEW finding) |
| `grouping.ts` | 63 | no | NO (`groupMessagesByApiRound` — NEW finding) |
| `postCompactCleanup.ts` | 77 | no | NO (NEW finding) |
| `timeBasedMCConfig.ts` | 43 | no | NO |
| `compactWarningHook.ts` | 16 | React-only | DROP (Ink/React UI) |
| `compactWarningState.ts` | 18 | no | NO (suppressCompactWarning helper — small but referenced from Block A) |
| `cachedMCConfig.ts` | 1 | YES (`export default {}`) | DROP (cached-MC entirely stripped from this build) |
| `cachedMicrocompact.ts` | 1 | YES | DROP |
| `reactiveCompact.ts` | 1 | YES | DROP |
| `snipCompact.ts` | 1 | YES | DROP |
| `snipProjection.ts` | 1 | YES | DROP |

### `services/contextCollapse/` (3 files, 3 LOC) — ALL STUBS
- `index.ts`, `operations.ts`, `persist.ts` — all `export default {}`. Build was stripped. **DROP entirely** (matches v4 — v4 has no context-collapse; Block A keeps v4-shape compactor).

### `services/extractMemories/` (2 files, 769 LOC)
| File | LOC | In plan? |
|---|---|---|
| `extractMemories.ts` | 615 | YES (Block H) |
| `prompts.ts` | 154 | partial (prompt text not yet fully ported) |

### `services/SessionMemory/` (3 files, 1,026 LOC)
| File | LOC | In plan? |
|---|---|---|
| `sessionMemory.ts` | 495 | YES (Block H) |
| `sessionMemoryUtils.ts` | 207 | YES (Block H) |
| `prompts.ts` | 324 | partial (template + update prompt referenced; full text not ported) |

### `services/AgentSummary/` (1 file, 179 LOC)
- `agentSummary.ts` — periodic 30s-interval forked summary for sub-agent UI display. NOT in plan. **NEW finding** (see § new findings).

### `services/MagicDocs/` (2 files, 381 LOC)
- `magicDocs.ts` (254) + `prompts.ts` (127) — auto-update markdown files headed `# MAGIC DOC: title`. **OUT-OF-SCOPE** — depends on FileReadListener registration + post-sampling-hook + small-fast-model side query; v4 has no equivalent and no PS Issue references it.

### `services/PromptSuggestion/` (2 files, 1,514 LOC)
- `promptSuggestion.ts` (523) + `speculation.ts` (991) — proactive next-prompt suggestion + Bash classifier speculation. **OUT-OF-SCOPE** — UI feature for interactive CLI typed-input suggestions; v4 chat.ipynb has no analog.

### `services/autoDream/` (4 files, 550 LOC)
- `autoDream.ts` (324) + `consolidationPrompt.ts` (65) + `consolidationLock.ts` (140) + `config.ts` (21) — background memory consolidation across sessions. **NEW finding** but mostly OUT-OF-SCOPE — depends on cross-session transcripts (not single-user single-session SageMaker). One sub-piece is reusable (`createAutoMemCanUseTool` is shared with extractMemories — already in Block H scope).

### `services/sessionTranscript/` (1 file, 1 LOC)
- `sessionTranscript.ts` — `export default {}`. Build-stripped (KAIROS feature only). **DROP**.

### `services/toolUseSummary/` (1 file, 112 LOC)
- `toolUseSummaryGenerator.ts` — Haiku-call to summarize a tool batch into ~30-char "git-commit-subject" label for SDK clients. **OUT-OF-SCOPE** — SDK-only mobile-app surface; v4 chat.ipynb prints tool calls inline.

### `services/tools/` (4 files, 3,113 LOC)
| File | LOC | In plan? |
|---|---|---|
| `toolExecution.ts` | 1745 | NO — runToolUse (massive; covers serial path, hooks, OTel, MCP) |
| `StreamingToolExecutor.ts` | 530 | NO — concurrency-aware streaming dispatcher |
| `toolHooks.ts` | 650 | NO — pre/post/failure hook orchestration |
| `toolOrchestration.ts` | 188 | NO |

These are the runtime tool-execution engine. v4 has equivalent (sequential `_run_tool` loop in sagemaker_agent.py), and **Block N** ports parallel-exec from Hermes (verified line refs). Runnable's `StreamingToolExecutor.ts:1-530` is a DIFFERENT design from Hermes (concurrency-safe predicate per-tool + sibling abort + queued/executing/completed/yielded state machine + `discard()` for streaming-fallback), and is **NEW finding** beyond Block N's Hermes-only port.

### Root files (3, 1,033 LOC)
| File | LOC | In plan? |
|---|---|---|
| `tokenEstimation.ts` | 495 | YES (Block B — folded into TokenTracker) but **PARTIAL** — Bedrock path not captured |
| `claudeAiLimits.ts` | 515 | NO — subscription rate-limit math (Pro/Max 5h+7d windows) |
| `claudeAiLimitsHook.ts` | 23 | NO — React hook (DROP — ipynb UI) |

---

## NEW findings — Runnable enhancements NOT yet in v5.0.1 plan

Each row cites Runnable file:line + assesses graft requirement + target Block.

| # | Capability | Runnable refs (file:line) | v4 has? | Bedrock-applicable? | Recommend for v5.0.1? | Target Block | Graft notes |
|---|---|---|---|---|---|---|---|
| 1 | **`getPromptTooLongTokenGap`** — parses `prompt is too long: X tokens > Y maximum` and returns the gap so reactive compact can drop multiple oldest API-rounds in one retry instead of peeling one-at-a-time | `errors.ts:104-118` (uses `parsePromptTooLongTokenCounts` `:85-96`) + consumer at `compact.ts:243-291` (`truncateHeadForPTLRetry`) | NO — v4 reactive compact doesn't gap-parse; just retries | YES — Bedrock returns the same wording (`prompt is too long: N tokens > N maximum`) | **YES** — closes a real PS-class bug (compact-retry stalling) | **L (extend)** | Add to `core/errors.py`: `parse_prompt_too_long_token_counts(raw)` + `get_prompt_too_long_token_gap(err)`. Add to `runtime/compact.py`: when reactive PTL fires, drop oldest groups summing ≥ gap. ~50 LOC. |
| 2 | **`parseMaxTokensContextOverflowError`** — parses `input length and max_tokens exceed context limit: 188059 + 20000 > 200000` and self-adjusts max_tokens | `withRetry.ts:550-595` + retry-loop call at `:388-427` (`overflowData → adjustedMaxTokens`) | NO — v4 fails or compacts on this 400 | YES — Bedrock messages-via-Anthropic-SDK return same string | **YES** — concretely prevents a fail mode | **L** | Add to `core/retry.py`: clamp output budget to `contextLimit - inputTokens - 1000` floor `FLOOR_OUTPUT_TOKENS=3000` + thinking budget. ~30 LOC. |
| 3 | **`getRateLimitResetDelayMs`** — parses `anthropic-ratelimit-unified-reset` header (Unix-sec) and waits to reset rather than polling. Capped at `PERSISTENT_RESET_CAP_MS = 6h` | `withRetry.ts:814-822` | NO | YES — Bedrock proxies the header through | YES | **L** | ~15 LOC. Adjacent to the existing `getRetryAfterMs` already cited in plan. |
| 4 | **`is529Error`** + **`shouldRetry529`** + `FOREGROUND_529_RETRY_SOURCES` (background source 529-drop) | `withRetry.ts:610-621, 84-89, 62-82` | NO — v4 retries 529 on every path | YES — Bedrock returns 529/overloaded | YES — prevents capacity-cascade amplification | **L** | Map querySource → must-retry vs background-drop. v5's "querySource" surface = parent vs subagent. Add `FOREGROUND_529_RETRY_SOURCES = {repl_main_thread, sdk, agent:*, compact, hook_*}`. ~40 LOC. |
| 5 | **`FallbackTriggeredError`** + Opus→Sonnet model-fallback after `MAX_529_RETRIES=3` | `withRetry.ts:160-168, 326-365` | NO | YES — directly applicable (Bedrock fallback inference profile) | YES — solves Opus capacity issue Bedrock users hit too | **L** | Wire `fallback_model` config knob; on 3rd consecutive 529, switch model and retry. ~50 LOC. |
| 6 | **Stale-connection (`ECONNRESET`/`EPIPE`) detection + keep-alive disable on retry** | `withRetry.ts:112-118, 218-230` (calls `disableKeepAlive()`) | NO — v4 just retries with same client | YES — Bedrock SDK uses Node http agent; same failure mode | YES | **L** | `is_stale_connection_error(err)` + on next retry rebuild Bedrock client. ~30 LOC. |
| 7 | **Persistent / unattended retry mode** with chunked `HEARTBEAT_INTERVAL_MS=30s` keep-alive yields, `PERSISTENT_MAX_BACKOFF_MS=5min`, `PERSISTENT_RESET_CAP_MS=6h` | `withRetry.ts:96-104, 170-512` | NO | partial — applies to long Bedrock waits during 429/529 | OPTIONAL — useful for SageMaker JupyterServer kernel idle-disconnect. CONSIDER for v5.0.1. | **L** | env-gated (`SAGEMAKER_UNATTENDED_RETRY=1`). ~80 LOC. Defer to v5.0.2 only if user OKs. |
| 8 | **`extractConnectionErrorDetails`** + `getSSLErrorHint` (walks error.cause chain up to depth 5; classifies SSL codes; surfaces enterprise-proxy fix) | `errorUtils.ts:42-100` | NO | YES — SageMaker corp users hit this with Zscaler/etc | YES | **L** | ~80 LOC. Direct Python port: walk `__cause__` chain. |
| 9 | **`sanitizeAPIError` + `extractNestedErrorMessage`** — strips HTML CloudFlare error pages + handles 2-level nested `{error:{error:{message}}}` (Bedrock vs first-party shapes) | `errorUtils.ts:107-198` | NO | YES — Bedrock error shape EXACTLY matches `{error:{message}}` case | YES | **L** | ~50 LOC. Critical for v5: today the user sees raw HTML on Bedrock 503s. |
| 10 | **`computePerToolHashes`** — per-tool schema hash (NOT just aggregate) with `sanitizeToolName` (`mcp__*`→`mcp`) | `promptCacheBreakDetection.ts:170-196, 183-185` | NO | YES | YES — already partially in plan; needs ALL fields | **L** | Plan v3 cites the function but not the wider extras: also need `cacheControlHash` (cache_control scope/TTL flips), `extraBodyHash` (CLAUDE_CODE_EXTRA_BODY), `effortValue`, `globalCacheStrategy`, `betas` sorted, `autoModeActive`, `isUsingOverage`, `cachedMCEnabled`. **Plan v3 currently lists 8 functions but PromptStateSnapshot has 12 tracked fields; adding the missing 4.** |
| 11 | **`MAX_TRACKED_SOURCES = 10` LRU eviction** in `previousStateBySource` — prevents unbounded memory growth from many sub-agent agentIds | `promptCacheBreakDetection.ts:107, 299-303` | NO | YES — v5 spawns many sub-agents per session | YES | **L** | 5 LOC; trivial. |
| 12 | **`MIN_CACHE_MISS_TOKENS = 2_000`** — minimum absolute drop required to flag a break (vs >5%-only) | `promptCacheBreakDetection.ts:120, 485-491` | NO | YES | YES | **L** | Combined predicate: `cacheReadTokens >= prevCacheRead * 0.95 OR tokenDrop < MIN_CACHE_MISS_TOKENS`. |
| 13 | **TTL-expiry classification**: when no client changes detected, use `timeSinceLastAssistantMsg` to label as `1h TTL expiry` / `5min TTL expiry` / `server-side` | `promptCacheBreakDetection.ts:566-588, 125-127` | NO | YES | YES — turns useless "unknown break" into actionable info | **L** | ~30 LOC. Constants: `CACHE_TTL_5MIN_MS = 5*60_000`, `CACHE_TTL_1HOUR_MS = 60*60_000`. |
| 14 | **`isExcludedModel`** — skip cache-break detection for Haiku (different caching behavior) | `promptCacheBreakDetection.ts:128-131` | NO | YES — Haiku 4.5 default for v4/v5 sub-agents — without this, Haiku-based sub-agents would emit constant false breaks | **CRITICAL** — v5 uses Haiku 4.5 by default, so without this the cache-break detector is permanently noisy on the most common model | **L** | `model.lower().contains('haiku')`. 3 LOC. |
| 15 | **`writeCacheBreakDiff`** — uses `diff.createPatch()` to write before/after diff to `~/.claude/tmp/cache-break-XXXX.diff` for debugging | `promptCacheBreakDetection.ts:708-727, 19-26` | NO | YES — useful for SageMaker debug | OPTIONAL | **L** | ~30 LOC; Python `difflib.unified_diff`. Defer to v5.0.2 if scope tight. |
| 16 | **`getEffectiveContextWindowSize`** + `MAX_OUTPUT_TOKENS_FOR_SUMMARY=20_000` reserve | `autoCompact.ts:33-49` | partial — v4 has model context window const but no per-model max-output-token reserve | YES | YES | **A** | v4's auto-compact threshold is currently a flat constant; per-model + summary-reserve + `CLAUDE_CODE_AUTO_COMPACT_WINDOW` env override is more robust. ~40 LOC. |
| 17 | **`AUTOCOMPACT_BUFFER_TOKENS=13_000`, `WARNING/ERROR=20_000`, `MANUAL_COMPACT=3_000`** — explicit named token budgets | `autoCompact.ts:62-65` | NO — v4 has different magic numbers | YES | YES | **A** | Constants block. ~10 LOC. |
| 18 | **`MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3`** circuit breaker WITH `consecutiveFailures` threading via `AutoCompactTrackingState` | `autoCompact.ts:51-60, 67-70, 257-265, 339-349` | partial — plan v3 says `_auto_compact_paused` global is "PORTED" but Runnable's threaded-tracking-state shape is more robust (per-turn rather than global) | YES | YES | **A** | Replace plan-v3's `_auto_compact_paused` global with Runnable's `AutoCompactTrackingState{compacted, turnCounter, turnId, consecutiveFailures}`. The state threads through `autoCompactIfNeeded` and resets on success. ~30 LOC. |
| 19 | **`calculateTokenWarningState`** with 5 distinct return flags (`percentLeft`, `isAboveWarning/Error/AutoCompact/AtBlocking`) | `autoCompact.ts:93-145` | partial — v4 returns single percentage | YES | YES — needed by Block E+F status bar | **A + E+F** | Block E+F's `update_tokens_display` should consume this. ~50 LOC. |
| 20 | **`shouldAutoCompact` recursion guards** — bail when `querySource ∈ {session_memory, compact, marble_origami}` | `autoCompact.ts:170-183` | NO — v4 doesn't differentiate sub-agent paths | YES | YES — v5 has SessionMemory + Compact sub-agents | **A + H** | ~20 LOC. Without this, sub-agent compact recurses. |
| 21 | **`stripImagesFromMessages`** for compact-summary call — replaces image/document blocks with `[image]/[document]` text markers; descends into `tool_result` content arrays | `compact.ts:145-200` | NO — v4 sends full payload (Bedrock often rejects on PTL during compact retry) | YES | YES — fixes a real Bedrock failure path | **A** | ~50 LOC. Cited by `compact.ts:1294` as part of summary pipeline. |
| 22 | **`stripReinjectedAttachments`** — pre-strips `skill_discovery`/`skill_listing` attachments before summary (re-injected post-compact anyway) | `compact.ts:211-223, 1295` | NO | partial — v5 has skills, so the same waste applies | YES | **A** | ~10 LOC. |
| 23 | **`MAX_PTL_RETRIES = 3` + `PTL_RETRY_MARKER` synthetic user msg + `truncateHeadForPTLRetry`** — recovers compact-itself-too-long via dropping oldest API-round groups | `compact.ts:227-228, 243-291, 462-491` | NO | YES — v5 will hit this on long sessions | YES — explicit user-blocking failure mode | **A** | ~70 LOC. Uses (1) above (`getPromptTooLongTokenGap`) + (24) below (`groupMessagesByApiRound`). |
| 24 | **`groupMessagesByApiRound`** — boundaries on assistant `message.id` change; tracks streaming chunks correctly | `compact/grouping.ts:22-63` | NO — v4 has no API-round grouping | YES | YES — required by (23) | **A** | ~30 LOC. Fundamental utility, also reusable for token-by-round telemetry. |
| 25 | **`POST_COMPACT_TOKEN_BUDGET=50_000`, `POST_COMPACT_MAX_FILES_TO_RESTORE=5`, `POST_COMPACT_MAX_TOKENS_PER_FILE=5_000`, `POST_COMPACT_SKILLS_TOKEN_BUDGET=25_000`, `POST_COMPACT_MAX_TOKENS_PER_SKILL=5_000`** | `compact.ts:122-130` | partial — v4 has token budgets but different magnitudes | YES | YES | **A** | Constants block. ~10 LOC. |
| 26 | **`createPostCompactFileAttachments`** — re-reads recently-touched files (sorted by recency, dedup against `preservedMessages`'s Read tool_results), generates fresh attachments via FileReadTool with token budget | `compact.ts:1415-1464, 1610-1655` | partial — v4 just clears `_FILES_READ`; doesn't re-inject | YES | YES — improves model continuity post-compact | **A** | ~80 LOC. Uses `collectReadToolFilePaths` to skip what's already visible in preserved tail. |
| 27 | **`createSkillAttachmentIfNeeded`** — re-injects active skills' content (sorted most-recent-first, per-skill truncation `POST_COMPACT_MAX_TOKENS_PER_SKILL=5K` budget `POST_COMPACT_SKILLS_TOKEN_BUDGET=25K`, marker `[... skill content truncated; use Read]`) | `compact.ts:1494-1534, 1657-1672` | partial — v4 keeps SKILL_LISTING but not active-skill bodies | YES | YES — v5 has 8+ skills (claude-api, simplify, verify, etc.) | **A** | ~70 LOC. Critical for v5: user-asked feature. |
| 28 | **`createPlanAttachmentIfNeeded`** + `createPlanModeAttachmentIfNeeded` — re-injects plan file + plan-mode reminder | `compact.ts:1470-1486, 1542-1560` | NO — v4 has no plan-mode | partial — only useful if v5 adopts plan mode (which it does not in 5.0.1) | NO — out-of-scope per constraint #1 | DROP-BY-CONSTRAINT | — |
| 29 | **`createAsyncAgentAttachmentsIfNeeded`** — re-injects async-running task references | `compact.ts:1568-1599` | NO | partial — only useful if v5 has async background agents | NO — single-user SageMaker, no async tasks | DROP-BY-CONSTRAINT | — |
| 30 | **`extractDiscoveredToolNames` + `boundaryMarker.compactMetadata.preCompactDiscoveredTools`** — preserves loaded-tool state across compact (since summary doesn't preserve `tool_reference` blocks) | `compact.ts:606-611, 1023-1028` | NO — v4 has no defer-loaded tool concept | NO — v5 doesn't ship deferred-tool-loading (constraint #1) | DROP | — | — |
| 31 | **`reAppendSessionMetadata`** — keeps custom session title/tag inside the 16KB tail window for `--resume` display | `compact.ts:711` | NO | partial — v5 sessions are JSONL via SessionManager (Block B+); same 16K-tail problem applies if resume is implemented | OPTIONAL — only if v5 ships `--resume` UX | DEFER | — |
| 32 | **`partialCompactConversation` (`from`/`up_to`)** — partial compact at message-pivot index, prefix-preserving OR suffix-preserving | `compact.ts:772-1106` | NO — v4 only has full compact | NO — v5 has no message-selector UI (ipynb constraint) | DROP-BY-CONSTRAINT | — | — |
| 33 | **`compactConversation` runs cache-sharing-fork FIRST then streaming-fallback**: 2-attempt streaming retry with `getRetryDelay(attempt)` between (`MAX_COMPACT_STREAMING_RETRIES=2`, GB-gated `tengu_compact_streaming_retry`) | `compact.ts:1136-1392` | partial — v4 just calls compact API once | YES | YES — improves compact reliability | **A** | The cache-sharing fork uses `runForkedAgent` with `skipCacheWrite: true` + same cacheSafeParams; falls back to plain streaming if the fork returns no text. v5 needs both paths. ~150 LOC. Block G2 (`forkSubagent` cache-prefix replay) is the foundation. |
| 34 | **`POST_COMPACT_MAX_FILES_TO_RESTORE` exclusion list**: `getPlanFilePath` + `MEMORY_TYPE_VALUES` (claude.md and friends) | `compact.ts:1674-1705` | NO | YES — v5 has CLAUDE.md and AGENT_STATUS | YES | **A** | ~30 LOC. Without this, v5 re-injects CLAUDE.md as a recently-read file. |
| 35 | **`compactWarningState` store** — `suppressCompactWarning()` after successful compaction, `clearCompactWarningSuppression()` at start of new attempt; tokens-display reads it via `useCompactWarningSuppression` (React) but the pure-state half is reusable | `compact/compactWarningState.ts:1-18`, `compact/microCompact.ts:259, 360, 512` | NO | YES — suppresses bogus "context full" warning right after compaction | YES | **A + E+F** | Pure-state half (`set_suppress() / clear_suppress() / get_suppress()`) ~10 LOC. Status-bar reads. Block E+F update tokens display checks suppression. |
| 36 | **Time-based microcompact** — when `(now - last_assistant_timestamp) > 60min`, content-clear all but last `keepRecent=5` compactable tool results BEFORE the next API call (cache is cold anyway) | `microCompact.ts:411-530, 422-444` (`evaluateTimeBasedTrigger`, `maybeTimeBasedMicrocompact`) + `compact/timeBasedMCConfig.ts:1-43` | NO — v4's microcompact is reactive only | YES — directly applicable; SageMaker users idle for hours | YES — concrete win | **A** | Replace v5 plan's "30-min microcompact fires" with the time-based content-clearing trigger. ~80 LOC. Constants `gapThresholdMinutes=60`, `keepRecent=5`. Includes `TIME_BASED_MC_CLEARED_MESSAGE = "[Old tool result content cleared]"` token-saving marker. |
| 37 | **`COMPACTABLE_TOOLS` allowlist** — only clear/dedup tool_results from {Read, Bash, Grep, Glob, WebSearch, WebFetch, Edit, Write} | `microCompact.ts:41-50` | partial — v4 clears all tool results | YES — preserves create_word/excel/etc | YES | **A** | Constants ~10 LOC. v5 with Block T tools (create_*) MUST exclude those (cumulative work). |
| 38 | **`IMAGE_MAX_TOKEN_SIZE = 2000` constant** — replaces `roughTokenCountEstimation` per-image with conservative fixed estimate (matches `tokenEstimation.ts` block path) | `microCompact.ts:38, 153, 182` | NO — v4 doesn't try to count image tokens | YES — Bedrock images = 2000 tok per Anthropic billing page | YES | **B** | 1 LOC + use site. |
| 39 | **`estimateMessageTokens` 4/3 padding** — pads rough estimate by 4/3 to be conservative since approximation under-counts | `microCompact.ts:164-205, 204` | NO | YES | YES | **B** | Replaces v5's current rough estimator. ~30 LOC. |
| 40 | **`bytesPerTokenForFileType`** — JSON/JSONL/JSONC = 2 bytes/token (vs 4 default); critical when API token-count unavailable on Bedrock | `tokenEstimation.ts:215-242` | NO | YES — Bedrock often falls back to rough count | YES | **B** | ~15 LOC. Consumers: `roughTokenCountEstimationForFileType`. Fixes long-standing v4 underestimate that lets oversized JSON tool-results slip past microcompact. |
| 41 | **`countTokensWithBedrock`** — calls Bedrock `CountTokensCommand` (since `@anthropic-sdk/bedrock-sdk` doesn't expose `countTokens`) | `tokenEstimation.ts:437-495` | NO — v4 uses rough estimation only | YES — DIRECTLY APPLICABLE; v5 currently has no real Bedrock count API | **CRITICAL — YES** | **B** | This is the biggest miss. Plan v3 says "tokenEstimation folded into TokenTracker" but doesn't capture the Bedrock-specific code path. Without this, v5 is stuck on rough estimation forever. ~60 LOC Python (boto3 `bedrock-runtime.count_tokens`). |
| 42 | **`countTokensViaHaikuFallback`** — sends a `max_tokens=1` `messages.create` to Haiku and reads `usage.input_tokens + cache_creation + cache_read` to get accurate count when `countTokensWithAPI` returns null | `tokenEstimation.ts:251-325` | NO | YES — Bedrock has thinking edge cases (Haiku 3.5 doesn't support thinking → fall back to Sonnet) | YES — improves accuracy | **B** | ~80 LOC. Includes `stripToolSearchFieldsFromMessages` (NOT applicable since v5 has no tool-search beta) — drop that part. |
| 43 | **`hasThinkingBlocks`** + `TOKEN_COUNT_THINKING_BUDGET=1024` + `TOKEN_COUNT_MAX_TOKENS=2048` — minimal thinking config for token-count requests | `tokenEstimation.ts:38-56, 32-33` | NO | YES — v5 supports thinking | YES | **B** | ~25 LOC. |
| 44 | **`roughTokenCountEstimationForBlock`** with per-type accuracy: text/thinking/redacted_thinking → text only (not JSON wrapper); tool_use → name+input only (not id wrapper); image/document → fixed 2000; server_tool_use/web_search_tool_result → jsonStringify | `tokenEstimation.ts:391-435` | NO — v4 just does `len(json.dumps(msg))/4` | YES | YES — saves ~5-10% on cumulative count | **B** | ~50 LOC; fundamental upgrade to v5's TokenTracker. |
| 45 | **`hasMemoryWritesSince`** — extractMemories skips when main agent already wrote to memory paths | `extractMemories.ts:113-148, 348-360` | NO | YES — v5 will have the same race | YES | **H** | ~30 LOC. Mutual-exclusion guard between main + forked memory-write agent. |
| 46 | **`countModelVisibleMessagesSince`** — counts messages since cursor UUID; falls back to ALL count if cursor missing (after compact removed it) | `extractMemories.ts:82-110` | NO | YES | YES | **H** | ~25 LOC. Critical: without cursor-not-found fallback, extraction permanently disabled mid-session. |
| 47 | **In-flight extraction tracking + `drainPendingExtraction(timeoutMs=60_000)`** — `inFlightExtractions` Set + Promise.race timeout-bounded drain; called pre-shutdown | `extractMemories.ts:303-304, 569-587, 611-615` | NO — v4 fires-and-forgets | YES — SageMaker kernel can shutdown mid-extract | YES | **H** | ~30 LOC. Plus `pendingContext` stashed-trailing-run pattern: only LATEST stashed context matters; coalesce-vs-replace semantics. |
| 48 | **`turnsSinceLastExtraction` throttle (`tengu_bramble_lintel`, default 1)** + `isTrailingRun` skip-throttle | `extractMemories.ts:316, 374-386` | NO | YES | YES | **H** | ~10 LOC. Even per-1 turns gives a knob for tuning. |
| 49 | **`createAutoMemCanUseTool(memoryDir)`** — Read/Grep/Glob unrestricted; Bash only `isReadOnly()` commands; Edit/Write only paths inside `memoryDir`; everything else denied with `denyAutoMemTool` audit-log | `extractMemories.ts:171-222, 154-164` | NO — v4 has no scoped memory permissions | YES — preserves safety | YES | **H** | ~50 LOC. Reusable by autoDream too. |
| 50 | **`scanMemoryFiles` + `formatMemoryManifest` pre-injected** — extraction prompt includes the existing-memories manifest so the agent doesn't waste a turn on `ls` | `extractMemories.ts:396-413, 30-33` | NO | YES | YES | **H** | ~40 LOC. Frontmatter-scan utility. Important UX. |
| 51 | **Closure-scoped state via `initExtractMemories()`** instead of module-level globals | `extractMemories.ts:296-587` | NO — v4 uses globals | partial — Python style differs but pattern useful for testability | OPTIONAL but RECOMMENDED for unit tests | **H** | Class-encapsulated. Plan-shape decision; minor LOC delta. |
| 52 | **Session-memory tool-call counter** — `countToolCallsSince(messages, sinceUuid)` + thresholded extraction (`hasMetUpdateThreshold` AND `toolCallsBetweenUpdates>=3`) | `sessionMemory.ts:108-181` + `sessionMemoryUtils.ts:184-189` | NO — v4 doesn't have thresholded session memory | YES | YES | **H** | ~50 LOC. The `(tokens AND toolCalls) OR (tokens AND no-tool-calls-in-last-turn)` predicate is the smart "extract at natural break" trigger. |
| 53 | **`waitForSessionMemoryExtraction(timeout=15s, stale=60s)`** — used by `trySessionMemoryCompaction` to await in-progress extraction before compacting | `sessionMemoryUtils.ts:89-105, 12-13` | NO | YES | YES — without this, SM-compact races SM-extract | **H** | ~30 LOC. |
| 54 | **`hasToolCallsInLastAssistantTurn`** + safe-extraction predicate (don't summarize while tool_use is dangling) | `sessionMemory.ts:158-170, 488-495` | NO | YES | YES | **H** | ~15 LOC. Direct port. |
| 55 | **`createMemoryFileCanUseTool(memoryPath)`** — single-file Edit-only allowlist (vs createAutoMemCanUseTool which is whole-dir) | `sessionMemory.ts:460-482` | NO | YES | YES | **H** | ~25 LOC. Required by SM-extract isolation. |
| 56 | **`sessionMemoryCompact.adjustIndexToPreserveAPIInvariants`** — handles tool_use/tool_result pair splits AND thinking-block message.id splits when computing the `messagesToKeep` index | `sessionMemoryCompact.ts:232-314` | NO — v4 has no equivalent invariant-preserving split | YES — Bedrock will 400 on dangling pairs | YES | **H** | ~85 LOC. CRITICAL correctness bug if not ported: SM-compact's startIndex can land mid-pair, summary fails. |
| 57 | **`calculateMessagesToKeepIndex`** — expand backwards from cursor to meet `minTokens=10K + minTextBlockMessages=5 + maxTokens=40K`, floored at last compact-boundary | `sessionMemoryCompact.ts:324-397, 47-61` | NO | YES | YES | **H** | ~80 LOC. Plus `DEFAULT_SM_COMPACT_CONFIG` constants block. |
| 58 | **`SessionMemoryCompactConfig` GrowthBook integration**: `getDynamicConfig_BLOCKS_ON_INIT('tengu_sm_compact_config', defaults)` + zero-value-rejection merge | `sessionMemoryCompact.ts:99-130` | NO | NO — single-user SageMaker, no GB | adapt: replace GB read with config-file read | **H** | ~40 LOC. Pattern useful: file-based config with default-fallback. |
| 59 | **`hasTextBlocks(message)` predicate** — true only for assistant text or user content with non-empty text | `sessionMemoryCompact.ts:135-150` | NO | YES | YES | **H** | ~15 LOC. Used by (57). |
| 60 | **`truncateSessionMemoryForCompact` + `MAX_SECTION_LENGTH=2000`, `MAX_TOTAL_SESSION_MEMORY_TOKENS=12000`** — caps per-section and total session-memory tokens before stuffing into compact summary | `SessionMemory/prompts.ts:8-9, 1-100` | NO | YES | YES | **H** | ~50 LOC + 12-section template constants. |
| 61 | **`isSessionMemoryEmpty`** template-equality check — falls through to legacy compact when memory is just-template | `sessionMemoryCompact.ts:540-543` (caller) + `SessionMemory/prompts.ts` | NO | YES | YES | **H** | ~10 LOC. |
| 62 | **`stripCacheControl`** + `cacheControlHash` — separate hash of full system array WITH cache_control to detect TTL/scope flips that the stripped hash erases | `promptCacheBreakDetection.ts:160-168, 279-281` | NO | YES — v5 will use cache_control with TTLs | YES | **L** | ~20 LOC. Already partly in plan v3 but not the dual-hash strategy. |
| 63 | **PromptCacheBreakDetection — full Snapshot fields**: extending plan v3 to include `globalCacheStrategy`, `betas`, `autoModeActive`, `isUsingOverage`, `cachedMCEnabled`, `effortValue`, `extraBodyHash` (12 total fields, plan v3 has 8) | `promptCacheBreakDetection.ts:227-241` | NO | partial — Bedrock-applicable subset | YES (Bedrock-applicable subset only: `model`, `betas`, `effortValue`, `extraBodyHash`, plus core systemHash/toolsHash/perToolHashes/cacheControlHash) — drop `autoModeActive`/`isUsingOverage`/`cachedMCEnabled` (subscription-only) | **L** | The 4 subscription-specific fields are categorically out-of-scope (Bedrock has no Pro/Max overage). Plan v3 should explicitly enumerate the 8 Bedrock-applicable fields. ~10 LOC delta. |
| 64 | **`StreamingToolExecutor` (concurrency-aware streaming dispatcher)** — `isConcurrencySafe` per tool, queue/executing/yielded state, `siblingAbortController` aborts siblings on bash error, `discard()` for streaming-fallback | `tools/StreamingToolExecutor.ts:1-530` | partial — v4 has serial loop; Block N ports Hermes parallel-exec | YES — DIFFERENT from Hermes | **YES — alternative-or-supplement to Block N** | **N (extend)** | Block N currently ports Hermes ThreadPoolExecutor pattern (`run_agent.py:8581-8584`). Runnable's design is **richer**: per-tool `isConcurrencySafe` predicate (queries the Tool definition), state machine, sibling-abort semantics, streaming-fallback discard. **Recommend: extend Block N with Runnable's pattern** since v5 will have both bash (non-concurrent) and read/grep/glob (concurrent) tools. ~150 LOC. v4-baseline is met by Hermes; Runnable adds quality. |
| 65 | **`runPostToolUseHooks` + `runPreToolUseHooks` + `runPostToolUseFailureHooks` + `executePermissionDeniedHooks`** — full hook-orchestration system with hook_blocking_error / hook_cancelled / hook_additional_context attachment types | `tools/toolHooks.ts:1-650` + `tools/toolExecution.ts:127-131` (call sites) | partial — v4 has audit_log + approval gate but no hook lifecycle | YES — but only minimal subset applies | OPTIONAL — only if v5 adopts hooks-as-extension-point | DEFER (v5.0.2) | The hook-system is a deep architecture choice; v5 already has approval+audit. Defer unless explicitly user-requested. |
| 66 | **`sessionActivity` keep-alive during compact** — `setInterval` 30s `sendSessionActivitySignal()` + re-emit `'compacting'` status to prevent WebSocket bridge timeout | `compact.ts:1167-1176, 1393-1395` | NO | YES — partial — SageMaker kernel idle-timeout applies analogously | YES | **A** | ~20 LOC. Critical for long-compacts on SageMaker. |
| 67 | **Compact-API querySource recursion guards** — `createCompactCanUseTool` denies all tools during compact agent | `compact.ts:1125-1134` | NO — v4's compact subprocess has no tool-permission gate | YES | YES | **A** | ~15 LOC. Without this, compact-agent can fire tools that re-enter the loop. |
| 68 | **`MAX_OUTPUT_TOKENS_FOR_SUMMARY=20_000` and `Math.min(COMPACT_MAX_OUTPUT_TOKENS, modelMax)`** clamp on compact-API call | `compact.ts:1318-1321` + `autoCompact.ts:30, 36-38` | partial — v4 sets max but uses different value | YES | YES | **A** | ~5 LOC. Constants. |
| 69 | **`sleep(retryDelayMs, signal, {abortError: () => new APIUserAbortError()})`** — abortable sleep across retry backoffs | `compact.ts:1369-1371` + `withRetry.ts:288, 511` | partial — v4 has time.sleep() not abortable | YES | YES — user ESC during retry should abort | **A + L** | ~10 LOC Python: use `asyncio.wait_for` with cancel signal OR a polling loop. |
| 70 | **`apiMicrocompact / getAPIContextManagement`** — server-side `clear_tool_uses_20250919` and `clear_thinking_20251015` strategies, configured via `CLAUDE_CODE_USE_API_CLEAR_TOOL_RESULTS` env vars | `compact/apiMicrocompact.ts:1-153` | NO | partial — Bedrock supports `anthropic_beta: ['context-management-...']`? **Verify** | OPTIONAL — pending Bedrock support verification | DEFER until verified | If Bedrock supports it, this is server-side compact (cheaper than client-side). If not, drop. ~150 LOC. |
| 71 | **`runPostCompactCleanup(querySource)`** — main-thread vs sub-agent gating; clears `getUserContext` + `resetGetMemoryFilesCache('compact')` + `clearSystemPromptSections` + `clearClassifierApprovals` + `clearSpeculativeChecks` + `clearBetaTracingState` + `clearSessionMessagesCache` + (cond) `attributionHooks.sweepFileContentCache` | `compact/postCompactCleanup.ts:1-77` | NO — v4 only resets `_FILES_READ` | YES — v5 needs `_FILES_READ.clear()` PLUS skill-listing-cache + memory-file-cache invalidation | YES | **A** | ~40 LOC. Without proper post-compact cache invalidation, post-compact context restoration is wrong. |
| 72 | **`AgentSummary.startAgentSummarization`** — periodic 30s background fork to generate 3-5-word summaries of sub-agent progress | `AgentSummary/agentSummary.ts:1-179` | NO — v4 has no progress display for sub-agents | partial — v5 chat.ipynb has no sub-agent progress widget | NO — out-of-scope (UI surface, ipynb constraint #2/#5) | DROP-BY-CONSTRAINT | — |
| 73 | **`isPersistentRetryEnabled`** + chunked sleep with heartbeat keep-alive for long retries | `withRetry.ts:96-104, 477-507` | NO | YES — applies to SageMaker idle-timeout if user opts in | OPTIONAL | DEFER (v5.0.2) | env-gated, not v5.0.1 critical. |
| 74 | **`mergeHookInstructions`** — merges userInstructions + hookInstructions for compact prompt | `compact.ts:373-381` | NO | NO (no hooks in v5.0.1) | DROP | — | — |
| 75 | **`buildPostCompactMessages` ordering invariant**: `[boundaryMarker, ...summaryMessages, ...messagesToKeep, ...attachments, ...hookResults]` | `compact.ts:330-338` | NO — v4 doesn't have a unified builder | YES | YES | **A** | ~15 LOC. Locks the ordering contract. |
| 76 | **`annotateBoundaryWithPreservedSegment`** — for partial-compact, attaches `preservedSegment{headUuid, anchorUuid, tailUuid}` metadata so the loader can patch chain | `compact.ts:349-367` | NO | NO (no partial compact in v5.0.1, see (32)) | DROP | — | — |
| 77 | **`compactConversation` execute pre/post-compact hooks (`PreCompact` / `SessionStart` 'compact' / `PostCompact`)** | `compact.ts:411-419, 591-594, 719-737` | NO — v4 has no hook pipeline | NO (no hooks in v5.0.1) | DROP-BY-CONSTRAINT | — | — |
| 78 | **`shouldExcludeFromPostCompactRestore` exclusion of `getMemoryPath` for ALL `MEMORY_TYPE_VALUES`** | `compact.ts:1674-1705` | NO | YES — v5 has `memory.md` + `MEMORY.md` | YES | **A** | ~20 LOC. Already in (34) but worth calling out the multi-type list. |
| 79 | **`hasExactErrorMessage(err, ERROR_MESSAGE_USER_ABORT)`** + skip-error-notification-on-user-abort | `compact.ts:1108-1123, 753-755` | NO | YES | YES | **A** | ~15 LOC. UX polish: ESC during compact shouldn't show "Error compacting". |
| 80 | **`isSessionMemoryEmpty` template equality check** to fall back to legacy compact when SM is empty | `sessionMemoryCompact.ts:540-543` | NO | YES | YES | **H** | ~5 LOC. |
| 81 | **`shouldUseSessionMemoryCompaction()`** with env-override `ENABLE_CLAUDE_CODE_SM_COMPACT` / `DISABLE_CLAUDE_CODE_SM_COMPACT` | `sessionMemoryCompact.ts:403-432` | NO | YES | YES | **H** | ~20 LOC. Adapt env-var name: `SAGEMAKER_SM_COMPACT_ENABLE`. |

---

## Items genuinely OUT-OF-SCOPE (categorically dropped, per constraints #1, #2, #5)

| Category | Files | Reason |
|---|---|---|
| Subscription rate-limits | `claudeAiLimits.ts` (515), `claudeAiLimitsHook.ts` (23) | Bedrock-only constraint #1 — no Pro/Max plan, no overage, no `anthropic-ratelimit-unified-*` headers (Bedrock proxies but doesn't generate them) |
| MagicDocs | `MagicDocs/{magicDocs,prompts}.ts` (381) | v4 has no equivalent + depends on FileReadListener registration system v5 doesn't have + post-sampling-hook framework not in v5 |
| PromptSuggestion | `PromptSuggestion/{promptSuggestion,speculation}.ts` (1514) | UI feature for typed-input next-prompt suggestion — v4 chat.ipynb has no typing-suggestion surface |
| ToolUseSummary | `toolUseSummary/toolUseSummaryGenerator.ts` (112) | SDK-only surface (mobile-app row truncating ~30 chars) — v4 chat.ipynb prints inline |
| AgentSummary | `AgentSummary/agentSummary.ts` (179) | Sub-agent UI progress widget — ipynb constraint #2/#5 |
| AutoDream | `autoDream/autoDream.ts` + 3 helpers (550) | Cross-session consolidation — single-session SageMaker constraint |
| sessionTranscript (KAIROS) | stub | Build-stripped (KAIROS-only feature) |
| context-collapse | 3 stubs | Build-stripped (CONTEXT_COLLAPSE-only feature) |
| cached-microcompact | 3 stubs (`cachedMC*`, `snip*`, `reactiveCompact`) | Build-stripped (cache_edits API + ant-only features); Bedrock has no `cache_edits` parameter |
| Files API | `api/filesApi.ts` (748) | Anthropic Files API — Bedrock has no equivalent endpoint |
| Subscription/oauth/grove/referral/sessionIngress/ultrareviewQuota/usage/overageCreditGrant/adminRequests | 1,447 LOC across 9 files | Anthropic-internal or subscription-only |
| React/Ink hooks | `claudeAiLimitsHook.ts`, `compactWarningHook.ts` | ipynb constraint #2 (drop the React layer; keep pure-state half) |
| toolExecution / toolOrchestration / toolHooks PostToolUse hooks etc | `tools/toolExecution.ts` (1745) + `tools/toolOrchestration.ts` (188) + `tools/toolHooks.ts` (650) | Most of this is the broader runtime hook framework + MCP integration + OTel tracing. v4's simpler `_run_tool` is the v5 baseline (constraint #1). **Block N** ports the parallel-exec subset from Hermes. **NEW finding 64** recommends grafting Runnable's `StreamingToolExecutor` design on top of Block N. The remaining 2,000+ LOC of hook orchestration + MCP path is OUT-OF-SCOPE per constraint #1. |
| dumpPrompts / logging / metricsOptOut / firstTokenDate / referral / etc | 1,400 LOC misc | Telemetry/anthropic-internal/admin |

---

## Summary by current-plan Block — recommended deltas

### Block A (Compactor) — current LOC est ~3300; **add ~700**
NEW additions from this scan (LOC est): #16 (40) + #17 (10) + #18 (30) + #19 (50) + #20 (20) + #21 (50) + #22 (10) + #23 (70) + #24 (30) + #25 (10) + #26 (80) + #27 (70) + #33 (150) + #34 (30) + #35 (15) + #36 (80) + #37 (10) + #66 (20) + #67 (15) + #68 (5) + #69 (10) + #71 (40) + #75 (15) + #78 (20) + #79 (15) ≈ +**900 LOC**.
After dedup and shared utility consolidation, realistic additional Block A scope: **+600-700 LOC**.

### Block B (TokenTracker) — current LOC est small; **add ~250**
NEW: #38 (1) + #39 (30) + #40 (15) + #41 (60) + #42 (80) + #43 (25) + #44 (50) ≈ **+260 LOC**.
**The Bedrock `countTokensWithBedrock` (#41) is the most consequential addition** — without it, v5 has no real Bedrock token count at all.

### Block H (Memory Extraction) — current LOC est ~1252; **add ~500**
NEW: #45 (30) + #46 (25) + #47 (30) + #48 (10) + #49 (50) + #50 (40) + #51 (refactor) + #52 (50) + #53 (30) + #54 (15) + #55 (25) + #56 (85) + #57 (80) + #58 (40) + #59 (15) + #60 (50) + #61 (10) + #80 (5) + #81 (20) ≈ **+610 LOC**.
**`adjustIndexToPreserveAPIInvariants` (#56) is a CRITICAL correctness fix** — without it SM-compact will produce conversations the API rejects with 400.

### Block L (Error/Retry/Cache-Break) — current LOC est ~250; **add ~400**
NEW: #1 (50) + #2 (30) + #3 (15) + #4 (40) + #5 (50) + #6 (30) + #8 (80) + #9 (50) + #10 (already partial) + #11 (5) + #12 (5) + #13 (30) + #14 (3) + #15 (30 — opt) + #62 (20) + #63 (10) + #69 (10 — shared with A) ≈ **+460 LOC**.
**`isExcludedModel` for Haiku (#14) is a 3-LOC NOT-OPTIONAL fix** — without it, v5's cache-break detector emits constant false-positive on the default Haiku 4.5.
**`countTokens-context-overflow self-heal (#2) and `getPromptTooLongTokenGap` (#1) are both directly user-blocking fix-paths** that close PS-class failure modes.

### Block N (Net-New patterns) — current LOC est ~300; **add ~150 OR replace pattern**
NEW: #64 (150) — Runnable's `StreamingToolExecutor` design as alternative-or-extension to Hermes ThreadPoolExecutor.
**Recommend: extend Block N to combine Hermes' parallel-exec primitive with Runnable's `isConcurrencySafe` per-tool predicate + sibling-abort + state machine.** Closer to combining-better goal of v5.

---

## Items where current plan v3 cites the function but the impl is incomplete

| Plan v3 row | Plan reference | Actual completeness vs Runnable code |
|---|---|---|
| `categorizeRetryableAPIError` Block L | `errors.ts:1163-1182` | Plan correct; complete. |
| `isPromptTooLongMessage` Block L | `errors.ts:64-77` | Plan correct; complete. |
| `parsePromptTooLongTokenCounts` Block L | `errors.ts:85-96` | Plan correct; complete. |
| `getRetryAfterMs` Block L | `withRetry.ts:803-810` | Plan correct; complete. |
| `computePerToolHashes` Block L | `promptCacheBreakDetection.ts:187-196` | Plan correct; **but plan misses the wider `PromptStateSnapshot` (12 fields) — see #63** |
| `recordPromptState` Block L | `promptCacheBreakDetection.ts:247-...` | Plan correct; **but plan misses the cache_control hash + LRU eviction + Haiku exclusion — see #10/#11/#12/#14** |
| `notifyCacheDeletion` / `notifyCompaction` / `cleanupAgentTracking` / `resetPromptCacheBreakDetection` Block L | `promptCacheBreakDetection.ts:673-704` | Plan correct; complete. |
| Compactor + Runnable cache-sharing Block A | `services/compact/compact.ts:1-1706` etc | **Plan undersized** — the 1706-LOC file contains 80+ helpers; plan v3 just says "combined LOC ~3300". Items #16-#37 + #66-#79 above enumerate the missing pieces. |
| `_extract_and_append_memories` + `extractMemories` + `sessionMemory` Block H | citations correct | **Plan undersized** — items #45-#61 + #80-#81 above enumerate the missing pieces. The two Runnable services have an additional **~580 LOC of orchestration logic** beyond the shape v4 provides. |
| `tokenEstimation` folded into TokenTracker Block B | `services/tokenEstimation.ts` | **Plan undersized** — the Bedrock-specific `countTokensWithBedrock` (#41), Haiku-fallback (#42), per-block accuracy (#44), and JSON byte-rate (#40) are not captured. |

---

## Recommended single change to plan v3 (highest-impact)

Add to `Q1_EVIDENCE_MATRIX.md` Block L, B, A, H, N:
- **+30 PORT_LOG rows** distributed across these blocks for the items #1-#15, #36-#67 above, each with the cited Runnable file:line ref.
- Bring `Q1` total from 172 → ~200 rows.
- Total LOC delta across blocks: **+1900-2200 LOC** — meaningful but not double-current; mostly small dense functions.

Of these, **5 items are NOT-OPTIONAL correctness/safety fixes** (would fail without them):
- (#2) `parseMaxTokensContextOverflowError` self-heal — without it, `400 input length and max_tokens exceed context limit` permanently fails the turn.
- (#9) `extractNestedErrorMessage` — without it, Bedrock 5xx returns raw HTML to user instead of message.
- (#14) Haiku `isExcludedModel` for cache-break detection — without it, sub-agent default-Haiku emits constant false-break events.
- (#41) `countTokensWithBedrock` — without it, v5 has zero real Bedrock token count.
- (#56) `adjustIndexToPreserveAPIInvariants` — without it, SM-compact produces API-400-rejected message sequences.

The other ~25 items are **quality/coverage upgrades** that move v5 ≥ Runnable on the "BETTER" axes (architecture, focus, optimal tool use, token optimization, long-coding) while staying inside Bedrock-only single-user constraints.

---

## Verdict

- **Plan v3 IS source-backed** (172 rows, 0 missing refs, 0 silent drops) — no false claims.
- **Plan v3 IS undersized** vs the actual depth of Runnable's services/ batch 1 — ~30 capabilities cited above are NEW findings that close PS-class bugs, fix correctness issues, or upgrade quality on the explicit v5 "BETTER" axes.
- **5 are NOT-OPTIONAL fixes** that v5.0.1 should adopt to avoid shipping with known-failing paths on Bedrock.
- **8 stub files / 4 build-stripped subsystems** are categorically out-of-scope (cached-MC, context-collapse, KAIROS sessionTranscript) and confirmed dropped — no decision needed.
- Recommended action: extend Q1 evidence matrix by **~30 rows**, extend Blocks A/B/H/L by the LOC deltas above, and re-run Codex AXIS A/B/C against the updated plan.

---

## Files NOT scanned in this batch (deferred to R5)

For batch 2 / future R-reports:
- `services/api/claude.ts` (3419 LOC) — main client wrapper. Worth deep scan for: cacheSafeParams construction, `getAPIMetadata`, `getExtraBodyParams`, `queryHaiku`, `queryModelWithStreaming` shape, `getMaxOutputTokensForModel`, beta header sticky-on patterns.
- `services/api/logging.ts` (788 LOC) — request/response logging shape.
- Other batch-2 dirs (`analytics`, `mcp`, `oauth`, `voice`, `lsp`, `policyLimits`, `plugins`, `remoteManagedSettings`, `settingsSync`, `skillSearch`, `teamMemorySync`, `tips`, `vcr`) — scoped per Wave-5-deep batch sequence.

Generated: 2026-05-01
