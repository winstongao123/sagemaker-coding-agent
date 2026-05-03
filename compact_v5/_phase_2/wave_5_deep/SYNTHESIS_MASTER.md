# Wave 5-DEEP SYNTHESIS MASTER

**Date**: 2026-05-01
**Inputs**: 20 deep-scan reports (R1-R12 Runnable, H1-H5 Hermes, L1-L2 Learning Factory, V1 v4 inventory verify)
**Baseline**: `V5_PHASE_2_PLAN_v3.md` (post-no-deferrals v4 corrections, 18 Blocks, ~11,330 LOC pre-Wave-5-DEEP)
**Hard constraints (recap)**: single-user SageMaker, Bedrock-only, v4 chat.ipynb canonical UI, no streaming, no MCP, NO DEFERRALS, COMBINE-and-do-better.

---

## 1. Verdict

**APPROVE-WITH-MAJOR-EXPANSION**. Plan v4 is structurally sound but materially undersized vs the actual depth of the four reference repos. Wave-5-DEEP surfaces **~150 net-new findings** across 20 reports. After applying the no-deferrals rule, post-Wave-5-DEEP scope grows from ~11,330 LOC to **~19,300 LOC** across **21 Blocks** counting E+F as 1 combined block (adds Block G3 Coordinator-Prompt + Block F2 Auto-Continuation + Block H+ Auto-Dream as three new sub-blocks; renames the implicit "v4-baseline-already-there" rows into explicit PORT_LOG rows; folds all Hermes/Runnable/LF deltas into existing Blocks). Per-Block NEW deltas in §3 sum to ~7,943 LOC NEW; corrected from initial estimate of ~16,200 LOC per Codex AXIS A 2026-05-01.

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

> **Build-time remap** (added 2026-05-02 per ADR-020): only item 0-1 (shim) lands inside Block 0. Items 0-2 through 0-10 keep their PORT_LOG origin here but are *implemented* in the Block that owns the touched module. Per-item landing Block + lock test in `_status/V5_DESIGN_DECISIONS.md` §ADR-020 → "Notes / known scope remaps". Constraint #3 (no deferrals) is honored by an explicit per-item landing Block + test gate, not by silent push-out.

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| 0-1 | SYSTEM_PROMPT verbatim re-export (V1 gap #6) | v4 | sagemaker_agent.py:8029-8189 | 0 (ref) | MUST | CLEAN | Add doc-only PORT_LOG row + ensure shim re-exports. v5 already has `prompt/*.md` (Phase 6) which covers this; FALSE-POSITIVE-AT-CODE-LEVEL but DOC-GAP — add row to plan. |
| 0-2 | `getSessionStartDate()` memoized + `getLocalMonthYear()` (R8 #67) | Runnable | constants/common.ts:1-34 | 15 | HIGH | CLEAN | Tool prompts mentioning today's date must use month-year not ISO date or cache busts at midnight. |
| 0-3 | `BEDROCK_EXTRA_PARAMS_HEADERS` Set (R8 #74) | Runnable | constants/betas.ts:38-43 | 5 | MUST | CLEAN | Load-bearing Bedrock invariant — interleaved-thinking + 1m-context betas go in extraBodyParams not headers. |
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
| B+2 | Canonical-name collapse for per-model usage (R11 N9) | Runnable | cost-tracker.ts:181-226 | 40 | MED | CLEAN | Bedrock `apac.` and `us.` prefixes → one row. |
| B+3 | 4-line cost block format (R11 N10) | Runnable | cost-tracker.ts:228-244 | 15 | MED | CLEAN | Replaces v4 single-line `/cost`. |
| B+4 | Local OTel-style counters (cost/token by type) (R11 N11) | Runnable | cost-tracker.ts:289-301 | 25 | MED | NEEDS-ADAPTATION | Local file/SQLite only — never external endpoint. |
| B+5 | Recursive advisor sub-cost accounting (R11 N12) | Runnable | cost-tracker.ts:304-322 | 30 | HIGH | CLEAN | v4.9.4 aux model unmeasured. |
| B+6 | contextWindow refresh on every cost update (R11 N13) | Runnable | cost-tracker.ts:273-274 | 5 | LOW | CLEAN | Per-update refresh. |
| B+7 | Exit-time atexit cost flush (R11 N14) | Runnable | costHook.ts:6-22 | 20 | HIGH | CLEAN | Wraps in atexit + signal handlers. |
| B+8 | `Config` dataclass explicit PORT_LOG row (V1 lesser #9) | v4 | sagemaker_agent.py:1018-1149 | 0 | MUST | FALSE-POSITIVE | Single row prevents silent field drop. |

**Block B+ total NEW: ~225 LOC + 1 doc row.**

### Block C (Runtime safety gates)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| C-1 | SecurityManager class explicit PORT_LOG row (V1 gap #8) | v4 | sagemaker_agent.py:1298-2106 | 0 (already in v5 Phase 5) | MUST | FALSE-POSITIVE-DOC-GAP | 808 LOC, biggest non-Compactor class — needs explicit row. |
| C-2 | secretScanner.ts 25 NEW gitleaks patterns + redactSecrets() (R5 A1) | Runnable | services/teamMemorySync/secretScanner.ts | 80 | HIGH | CLEAN | Combines with v4 13 patterns → 38 patterns + redaction helper. |
| C-3 | `findActualString` quote-normalized match (R1 #115) | Runnable | FileEditTool/utils.ts:73-93 | 20 | HIGH | CLEAN | Curly→straight quote normalization. |
| C-4 | `preserveQuoteStyle` (R1 #116) | Runnable | FileEditTool/utils.ts:104-120 | 15 | MED | CLEAN | If file uses curly, re-wrap new_string. |
| C-5 | UTF-16 LE BOM detection on edit (R1 #121) | Runnable | FileEditTool.ts:208-214 | 15 | HIGH | CLEAN | Notepad-saved files. |
| C-6 | UNC path skip on Windows (NTLM credential leak) (R1 #123) | Runnable | FileEditTool.ts:179-181 | 5 | HIGH | CLEAN | Defensive Windows. |
| C-7 | `\r\n`→`\n` normalization preserving original on write (R1 #122) | Runnable | FileEditTool utils | 20 | HIGH | CLEAN | Round-trip line endings. |
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
| C-18 | Multi-pass JSON repair `_repair_tool_call_arguments` (H1 #17) | Hermes | run_agent.py:547-641 | 95 | **HIGH-MUST** | CLEAN | Bedrock Claude (esp. Haiku) emits malformed args; `{}` fallback better than crash. (Resolves R5 prior OUT-OF-SCOPE — see §7.) |
| C-19 | `_escape_invalid_chars_in_json_strings` (H1 #16) | Hermes | run_agent.py:505-544 | 40 | MED | CLEAN | Pairs with #C-18. |

**Block C total NEW: ~555 LOC + 1 doc row.**

### Block C+ (Approval/diff dispatch + stop/abort + rate limits)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| C+1 | `EnterPlanMode` + `ExitPlanModeV2` (R1 #84-91, #97-104) | Runnable | EnterPlanModeTool/ExitPlanModeV2Tool | 200 | MED | NEEDS-ADAPTATION | OPTIONAL — formalizes v4's PLAN_MODE_ALLOWED_TOOLS into a dedicated mode. Drop teammate routing + auto-mode classifier. **DECISION: KEEP-LIGHT (~80 LOC)** for plan-mode toggle without ExitPlanMode tool ceremony, OR **DROP** since v4's `/phase` is the lighter-weight equivalent. **Verdict: DROP (KEEP `/phase`)** to avoid scope creep. See §9. |
| C+2 | File-history snapshot per-edit (R1 #127) | Runnable | FileEditTool.ts:431-440 | 40 | MED | CLEAN | Pre-edit content backup → enables `/rollback` (Block D extension). |
| C+3 | Cancellation/abort signal pattern via Python (paired with C-17) | Runnable | utils/abortController.ts | (in C-17) | HIGH | already covered | — |

**Block C+ total NEW: ~40 LOC (after dropping Plan Mode).**

### Block D (Slash commands + custom expander)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| D-1 | Lazy-load heavy command (R11 N1) | Runnable | commands.ts:188-202 | 20 | MED | CLEAN | Python `importlib` on demand. |
| D-2 | Parallel skill scan via Promise.all (R11 N2) | Runnable | commands.ts:449-469 | 25 | LOW | CLEAN | v5 skill discovery currently sequential. |
| D-3 | Dynamic-skill merge dedupe (R11 N3) | Runnable | commands.ts:476-517 | 30 | MED | CLEAN | Self-patching skills support. |
| D-4 | Named cache invalidation (4 caches) (R11 N4) | Runnable | commands.ts:523-532 | 20 | MED | CLEAN | Better than "clear all". |
| D-5 | Listing-budget filter (bundled/user/project/dynamic) (R11 N5) | Runnable | commands.ts:563-608 | 40 | MED | CLEAN | Token budget for skill listing. |
| D-6 | Command alias + helpful-error-on-miss (R11 N6) | Runnable | commands.ts:688-719 | 30 | MED | CLEAN | `/q→/quit`, full list on miss. |
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
| A-5 | `shouldAutoCompact` recursion guards (R4 #20) | Runnable | autoCompact.ts:170-183 | 20 | HIGH | CLEAN | Bail when querySource ∈ {session_memory, compact}. |
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
| A-23 | `hasExactErrorMessage` + skip-error-on-user-abort (R4 #79) | Runnable | compact.ts:1108-1123 | 15 | LOW | CLEAN | UX polish — ESC during compact. |
| A-24 | `_is_stale_round_trip` confirm port (V1 lesser) | v4 | sagemaker_agent.py:3919-3975 | 0 (verify) | MUST | FALSE-POSITIVE | Used by `context_collapse`; explicit confirmation. |
| A-25 | Stub-injection for missing tool_results post-compact (H2 F7) | Hermes | run_agent.py:4585-4604 | 25 | **MUST** | CLEAN | Without it, Bedrock 400-errors after compact. |
| A-26 | Surrogate sanitization recursive walker (H1 #14, #15) | Hermes | run_agent.py:384-502 | 115 | HIGH | CLEAN | `_sanitize_messages_surrogates` before every Bedrock converse. |
| A-27 | `flush_memories` pre-compression turn (H4 F2) | Hermes | run_agent.py:7913-8157 | 80 | HIGH | NEEDS-ADAPTATION | One-turn memory-only call before compact. |
| A-28 | `_compress_context` post-compaction details (todo re-inject, file-dedup reset, token refresh) (H4 F3) | Hermes | run_agent.py:8158-8272 | 50 | HIGH | CLEAN | Adopt items 1, 3, 5; skip session-split (SQLite-specific). |
| A-29 | Tool-schema tokens in pre-compression estimate (H4 F8 / R7 GAP-7) | Hermes | run_agent.py:9507-9513 | 20 | HIGH | CLEAN | "20-30K+ tokens v4 estimate misses". |
| A-30 | Post-compression retry-counter reset (H4 F8) | Hermes | run_agent.py:9544 | 10 | HIGH | CLEAN | Prevents "(empty)" right after compaction. |
| A-31 | `apply_anthropic_cache_control` Bedrock cache application (H4 F12) | Hermes | run_agent.py:9851-9856 | 30 | HIGH | CLEAN | Confirm Block A applies cache_control at system + last-3 messages. |
| A-32 | Prefix-stable normalization (sorted JSON keys + content strip) (H4 F13) | Hermes | run_agent.py:9870-9895 | 25 | HIGH | CLEAN | Free 5-15% cache-hit boost. |
| A-33 | A28 prompt-cache invariant policy (H5 A28) | Hermes | AGENTS.md:Policy | 0 (policy/audit) | **MUST** | NEEDS-ADAPTATION | NEVER rebuild system prompt mid-conv; toolset changes deferred to next session via `--now` opt-in. v4 violates this — v5.0.1 must enforce. |
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
| I-7 | `skills/init/` (CLAUDE.md scaffolder) — folds D-8 here | Runnable | commands/init.ts | (in D-8) | MED | CLEAN | — |
| I-8 | `skills/init-verifiers/` — folds D-9 here | Runnable | commands/init-verifiers.ts | (in D-9) | MED | CLEAN | — |
| I-9 | `skills/skillify/` — folds D-10 here | Runnable | bundled/skillify.ts | (in D-10) | MED | CLEAN | — |
| I-10 | `skills/debug/` (R9 #20) | Runnable | bundled/debug.ts:1-103 | 20 | LOW | CLEAN | Tail audit_logs, ERROR/WARN summary. |
| I-11 | `skills/remember/` 4-step review (R9 #18) | Runnable | bundled/remember.ts:9-62 | 50 | LOW | CLEAN | CLAUDE.md/CLAUDE.local.md only. |
| I-12 | Frontmatter parser improvements (auto-quote, brace-expand, coerce desc) (R8 #24, #50) | Runnable | utils/frontmatterParser.ts:1-371 | 150 | HIGH | CLEAN | Real failure modes. |
| I-13 | `tool_skill` + `tool_skill_propose_patch` registry rows (R2 finding 2) | v4 | sagemaker_agent.py:6674, 6703 | 0 (already wired Block D) | LOW | doc-only | Confirm Block D dispatcher + add note. |

**Block I total NEW: ~335 LOC.**

### Block M (Phase 8 critical fixes — already in v3)

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
| G-8 | `forkSubagent` cache-prefix replay (already Block G2 in plan) | Runnable | forkSubagent.ts:73-end | 100 | HIGH | already in plan | — |

**Block G total NEW: ~155 LOC.**

### Block G3 (NEW BLOCK — Coordinator System Prompt) **CRITICAL**

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| G3-1 | Coordinator 258-LOC system prompt (R7 N1) | Runnable | coordinator/coordinatorMode.ts:111-369 | 270 | **HIGH-MUST** | NEEDS-ADAPTATION | Codifies user's #1 collaboration rule: 4 phases, never delegate understanding, continue-vs-spawn matrix, parallel-research/serial-write rules. Substitute Runnable tool names (AgentTool→spawn_agent, etc.). Gated by `CONFIG.coordinator_mode_enabled` (default False). |
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
| H-11 | `adjustIndexToPreserveAPIInvariants` (R4 #56) | Runnable | sessionMemoryCompact.ts:232-314 | 85 | **MUST** | CLEAN | CRITICAL: SM-compact startIndex landing mid-pair → API 400 reject. |
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

### Block H+ (NEW BLOCK — Memory Consolidation Engine, MANUAL-TRIGGER ONLY)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| H+1 | autoDream consolidation engine — MANUAL-TRIGGER ONLY (user decision 2026-05-01) | Runnable | services/autoDream/* | 350 | HIGH | NEEDS-ADAPTATION | Memory consolidation engine: 4-phase prompt (Orient → Gather → Consolidate → Prune+Index) + lock + rollback-on-fail. **NO DAEMON, NO AUTO-FIRE, NO ENV AUTO-ENABLE.** Fires ONLY when user invokes `/dream` slash command (D-11). Drop `autoDream` daemon scheduler + 3-gate auto-trigger + `SAGEMAKER_AUTO_DREAM` env var. Target: `runtime/dream.py` (NOT `auto_dream.py`). USER_GUIDE must document `/dream` usage clearly. |

**Block H+ total NEW: ~350 LOC. NEW BLOCK.**

### Block L (Error/retry/cache-break)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| L-1 | `getPromptTooLongTokenGap` parse + drop multiple groups (R4 #1) | Runnable | errors.ts:104-118 | 50 | HIGH | CLEAN | Closes compact-retry stalling PS-class bug. |
| L-2 | `parseMaxTokensContextOverflowError` (R4 #2) | Runnable | withRetry.ts:550-595 | 30 | **MUST** | CLEAN | Without it, context-overflow 400s permanently fail the turn. |
| L-3 | `getRateLimitResetDelayMs` Unix-sec parse (R4 #3) | Runnable | withRetry.ts:814-822 | 15 | HIGH | CLEAN | `anthropic-ratelimit-unified-reset` header. |
| L-4 | `is529Error` + querySource-aware retry-vs-drop (R4 #4) | Runnable | withRetry.ts:610-621, 84-89 | 40 | HIGH | CLEAN | Prevents capacity-cascade amplification. |
| L-5 | `FallbackTriggeredError` Opus→Sonnet on 3x 529 (R4 #5) | Runnable | withRetry.ts:160-168 | 50 | HIGH | NEEDS-ADAPTATION | Bedrock fallback inference profile. |
| L-6 | Stale-connection + keep-alive disable on retry (R4 #6) | Runnable | withRetry.ts:112-118 | 30 | HIGH | CLEAN | Bedrock SDK uses Node-equivalent http; rebuild client. |
| L-7 | Persistent retry mode (env-gated) (R4 #7) | Runnable | withRetry.ts:96-104 | 80 | MED | NEEDS-ADAPTATION | `SAGEMAKER_UNATTENDED_RETRY=1` for SageMaker idle-disconnect. |
| L-8 | `extractConnectionErrorDetails` SSL error walk + hint (R4 #8) | Runnable | errorUtils.ts:42-100 | 80 | HIGH | CLEAN | Corp Zscaler/proxy fixes. |
| L-9 | `sanitizeAPIError` + `extractNestedErrorMessage` (R4 #9) | Runnable | errorUtils.ts:107-198 | 50 | **MUST** | CLEAN | Without it, Bedrock 5xx returns raw HTML to user. |
| L-10 | Full PromptStateSnapshot 12 fields → 8 Bedrock-applicable (R4 #10, #63) | Runnable | promptCacheBreakDetection.ts:170-241 | 30 | HIGH | CLEAN | Drop 4 subscription-specific. |
| L-11 | `MAX_TRACKED_SOURCES=10` LRU eviction (R4 #11) | Runnable | promptCacheBreakDetection.ts:107 | 5 | MED | CLEAN | Trivial. |
| L-12 | `MIN_CACHE_MISS_TOKENS=2_000` (R4 #12) | Runnable | promptCacheBreakDetection.ts:120 | 5 | MED | CLEAN | Combined predicate. |
| L-13 | TTL-expiry classification (1h/5min/server-side) (R4 #13) | Runnable | promptCacheBreakDetection.ts:566-588 | 30 | HIGH | CLEAN | Turns useless break into actionable info. |
| L-14 | `isExcludedModel` Haiku exclusion (R4 #14) | Runnable | promptCacheBreakDetection.ts:128-131 | 3 | **MUST** | CLEAN | Without it, Haiku 4.5 sub-agents emit constant false breaks. |
| L-15 | `writeCacheBreakDiff` for debugging (R4 #15) | Runnable | promptCacheBreakDetection.ts:708-727 | 30 | LOW | CLEAN | Optional debug. |
| L-16 | `stripCacheControl` + `cacheControlHash` dual hash (R4 #62) | Runnable | promptCacheBreakDetection.ts:160-168 | 20 | HIGH | CLEAN | Detects TTL/scope flips. |
| L-17 | API error humanizer (Bedrock-only variant) (H2 N3) | Hermes | run_agent.py:3552-3590 | 40 | HIGH | NEEDS-ADAPTATION | Drop Cloudflare branch; keep JSON-body + status_code. |
| L-18 | Roll-back to last assistant turn helper (H2 N2) | Hermes | run_agent.py:3317-3346 | 30 | MED | CLEAN | Defensive utility. |
| L-19 | One-extra primary-recovery after max retries (H3 G18) | Hermes | run_agent.py:6988-7066 | 30 | MED | CLEAN | Bedrock can hit transient TCP. |
| L-20 | Three-tier recovery ladder pattern (H3 G19) | Hermes | run_agent.py:5528-5610 | 0 (architectural) | HIGH | NEEDS-ADAPTATION | "retry → IAM token refresh → user-error" architectural lesson. |
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
| N-5 | Sequential path bookkeeping parity (H4 §2.4) | Hermes | run_agent.py:8727-9112 | 150 | HIGH | CLEAN | Sequential is fallback when batch unsafe. |
| N-6 | `enforce_turn_budget` over `messages[-num_tools:]` (H4 §2.2) | Hermes | run_agent.py:8714-8725 | 30 | HIGH | CLEAN | Token cap on tool result aggregate. |
| N-7 | `partial_tool_names` tracking + warning-on-death (H3 G7) | Hermes | run_agent.py:6175, 6663-6687 | 40 | HIGH | NEEDS-ADAPTATION | Re-purpose for non-streaming Bedrock invoke: track tool_use blocks pending tool_result; warn if conversation ends mid-call. v5 has no streaming (constraint #10). |
| N-8 | Retry classifier — three categories (H3 G5) | Hermes | run_agent.py:6302-6549 | 100 | HIGH | NEEDS-ADAPTATION | Pre-call / mid-call / post-call retry policy on non-streaming Bedrock invoke. Drop stream-delivery state machine; keep retry-classification logic. |
| N-9 | Mid-call stub recovery with user-visible warning (H3 G6) | Hermes | run_agent.py:6644-6709 | 60 | HIGH | NEEDS-ADAPTATION | Re-purposed: when Bedrock invoke is cancelled/disconnected mid-tool-call (non-streaming), inject synthetic tool_result stub. v5 has no streaming (constraint #10) — this is for invoke-level disconnects, not stream chunks. |
| N-10 | Bedrock streaming three-callback model (H3 G20) | Hermes | bedrock_adapter.py | — | DROPPED | OUT-OF-SCOPE-CONSTRAINT-#10 | NO STREAMING in v5.0.1. |
| N-11 | Reset stream-delivery tracking per attempt (H3 G21) | Hermes | run_agent.py:6034-6036 | — | DROPPED | constraint #10 | — |
| N-12 | Local-provider stale-detector disable (H3 G22) | Hermes | run_agent.py:6014-6019 | — | DROPPED | not applicable | — |
| N-13 | `StreamingToolExecutor` concurrent state machine pattern (R4 #64) | Runnable | tools/StreamingToolExecutor.ts | — | DROPPED | constraint #10 | Hermes ThreadPoolExecutor pattern (already in plan) suffices for non-streaming concurrent. |
| N-14 | Plan v3 dynamic tool-ref injection cited via AGENTS.md:627-628 (H5 A36) | Hermes | AGENTS.md:627-628 | 0 | MUST | already in plan | Confirm Q1 evidence row. |
| N-15 | Fuzzy tool-name matching (already in plan) | Hermes | run_agent.py:4689-4720 | (already) | already | — | — |
| N-16 | Tool-call dedup (already in plan) | Hermes | run_agent.py:4639-4655 | (already) | already | — | — |
| N-17 | Surrogate sanitize at request-time (folded into A-26) | Hermes | run_agent.py:9897-9901 | (in A-26) | already | — | — |
| N-18 | Tool interface enrichments (`aliases`, `maxResultSizeChars`, `isDestructive`, `interruptBehavior`) (R7 N14) | Runnable | Tool.ts:362-695 | 60 | MED | CLEAN | Adds to BaseTool. |
| N-19 | TaskCreate/Get/List/Update/Output/Stop tools | Runnable | tasks/* | — | DROPPED | constraint #1 | TaskV2 swarm not in v5. |

**Block N total NEW: ~673 LOC (after dropping streaming items).**

### Block T (v4 tool surface parity)

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| T-1 | `notebook_edit` (v4 :5921 schema :7275) (R2 finding #1, V1 gap #2) | v4 | sagemaker_agent.py:5921 + 7275 | 120 | MUST | FALSE-POSITIVE-ALREADY-IN-V5 | v5 already has `tools/notebook_edit.py` (Phase 4). Add Block T row 12 explicitly to plan. |
| T-2 | `view_image` (v4 :6419 schema :7307) (V1 gap #3) | v4 | sagemaker_agent.py:6419 + 7307 | 40 | MUST | FALSE-POSITIVE-ALREADY-IN-V5 | v5 already has `tools/view_image.py` (Phase 4). Add Block T row 13. |
| T-3 | `SemanticSearch` class verbatim port (V1 gap #4) | v4 | sagemaker_agent.py:6461-6610 | 150 | MUST | CLEAN | Block T `tool_semantic_search` is hollow without underlying class. |
| T-4 | WebFetch fold-ins: 15-min URL LRU cache + same-host redirect + Turndown (R3 row 20) | Runnable | utils.ts:63-243 | 80 | HIGH | NEEDS-ADAPTATION | Python `markdownify` for Turndown; `MAX_REDIRECTS=10` same-host policy. **Confirms approval of fold-ins.** **DROPPED 2026-05-03 per user — SageMaker single-user typically VPC-isolated; web_fetch ships disabled in v5.0.1 (NotImplementedError module guard). PORT_LOG row 103-A. NOT silent narrowing — explicit user override.** |
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

### Block F2 (NEW BLOCK — Auto-continuation under iteration budget) **CRITICAL**

| # | Capability | Repo | file:line | LOC | Pri | Fit | Graft |
|---|---|---|---|---|---|---|---|
| F2-1 | TokenBudget auto-continuation (R7 N4) | Runnable | query/tokenBudget.ts:1-93 + query.ts:1308-1355 | 100 | HIGH | NEEDS-ADAPTATION | v5 IterationBudgetWidget shows budget but doesn't auto-continue. <90% AND not diminishing-returns → inject nudge + continue. |

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
| **F2 (NEW)** | — | +100 | 100 | 1 |
| I | 50 | +335 | 385 | 13 |
| M | 30 | 0 | 30 | 0 |
| G | 280 | +155 | 435 | 8 |
| **G3 (NEW)** | — | +300 | 300 | 2 |
| G2 | 100 | 0 | 100 | 0 |
| H | 1,252 | +945 | 2,197 | 20 |
| **H+ (NEW)** | — | +350 | 350 | 1 |
| L | 250 | +966 | 1,216 | 28 |
| N | 300 | +673 | 973 | 19 (12 ports + 7 dropped clarifications) |
| T | 1,100 | +780 | 1,880 | 12 |
| J | 150 | 0 | 150 | 0 |
| K | 200 | 0 | 200 | 8 (process/policy) |
| **TOTAL** | **11,330** | **+8,545** (Wave-5-DEEP) | **~16,200** (after dedup ~5%) | **+233 rows** |

(Conservative ~5% dedup reduces TOTAL to ~15,400-16,200 LOC. Pre-Wave-5 was 11,330; post-Wave-5-DEEP is ~16,200. Growth factor 1.43x — material but not double, consistent with R4's "+1900-2200 LOC" estimate scaled across the other 19 reports.)

---

## 4. New blocks recommended

| Block | Reason | LOC | Sequencing |
|---|---|---:|---|
| **G3 — Coordinator System Prompt** | R7 N1's 258-LOC prompt encodes user's #1 collaboration rule (4 phases, never delegate understanding, continue-vs-spawn matrix). Plan v3 Block G has 7 sub-agent types but no orchestration prompt. **Q3 axis 2 (agent coordination) demands this.** | 300 | After Block G, before Block G2 |
| **F2 — Auto-Continuation Under Iteration Budget** | R7 N4 — IterationBudgetWidget without auto-continue is half the feature. <90% threshold + diminishing-returns halt. | 100 | After Block E+F |
| **H+ — Memory Consolidation Engine (manual `/dream` only)** | R12 R12-1 — fits Q3 long/complex coding axis; pays down memory debt across sessions. ~350 LOC. **NO daemon, NO auto-fire** (user decision 2026-05-01). Fires only when user runs `/dream`. | 350 | After Block H |

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
- 0-9 (feature-flag fail-closed) — Python `runtime/feature_flags.py` shim
- A-13 (compactConversation cache-sharing-fork) — Pairs with G2 Bedrock cache invariants
- A-27 (flush_memories) — Aux-client first, fallback primary; v5 may use same client
- A-33 (A28 prompt-cache invariant policy) — Refactor v5 prompt builder
- A-40 (SYSTEM_PROMPT_DYNAMIC_BOUNDARY) — Refactor `_build_system_prompt`
- C-17 (combinedAbortSignal + AsyncLocalStorage cwd) — Python `contextvars` + `asyncio.Event`
- F2-1 (TokenBudget auto-continue) — Wire into v5 query loop
- G3-1 (Coordinator system prompt) — Substitute Runnable tool names; gated on CONFIG flag
- H-13 (SessionMemoryCompactConfig) — Replace GrowthBook with config-file
- H+1 (memory consolidation engine, manual /dream only) — synchronous Python (no threading, no asyncio, no daemon)
- L-5 (FallbackTriggeredError model switch) — Bedrock fallback inference profile
- L-7 (Persistent retry mode) — env-gated `SAGEMAKER_UNATTENDED_RETRY`
- L-17 (API error humanizer) — Drop Cloudflare, keep JSON-body
- L-20 (Three-tier recovery ladder) — "retry → IAM token refresh → user-error"
- L-21 (Daemon-thread Bedrock call) — boto3 thread pattern
- L-28 (Bedrock Guardrails) — boto3 Bedrock parameter
- N-3 (parallelism constants) — Filter `_PARALLEL_SAFE_TOOLS` to v5 tool surface
- N-4 (worker race fix + checkpoint) — Python threading
- N-8 (two-policy stream retry) — Adapt to non-streaming "API call dropped mid-tool"
- N-9 (partial stub recovery) — Adapt to non-streaming
- T-4 (WebFetch fold-ins) — Python `markdownify`
- T-7 (readFileInRange) — `aiofiles` or `seek` Python

### CONFLICT-REJECT
- C+1 (EnterPlanMode formal mode) — REJECT in favor of v4's `/phase`. v5 already has lighter-weight equivalent.
- N-10 / N-11 / N-12 / N-13 (streaming tool executor + streaming retry resets) — REJECT per constraint #10 (no streaming).

### FALSE-POSITIVE-ALREADY-IN-V5 (V1 findings — implementation-level present but PORT_LOG-row missing)
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
| V1.5 | `_scan_for_prompt_injection` + `_INJECTION_PATTERNS` | :7509-7541 | `security/prompt_injection.py` (NEW) | MISSING | **PORT** ~40 LOC (NOT a Hermes adoption — v4-native) |
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
- **R1 G1-G7 streaming retry classifier**: KEEP. Adapt as non-stream patterns (`partial_tool_names` warning works on Bedrock Converse non-streaming when SDK retry exhausts mid-tool — same outcome). The two-policy retry classifier (pre-delivery / mid-tool-call / post-delivery) translates cleanly to non-streaming: Bedrock Converse can fail mid-call before any output is parsed, or after the JSON tool_use block but before tool execution.

### R5 prior "OUT-OF-SCOPE" (JSON repair) vs H1 "HIGH PRIORITY" (multi-pass JSON repair)
- **H1's `_repair_tool_call_arguments` (95 LOC)** observes Haiku-on-Bedrock emitting malformed `arguments` strings on long contexts. R5's prior reasoning applied to Runnable's broader auto-repair (which depends on Hermes-only patterns) — R5 was right to skip Runnable's specific path. H1 surfaces the **same primitive** that v5 needs for Bedrock-Haiku resilience. **VERDICT: ADOPT (Block C-18, C-19).** Hermes lines 547-641 + 505-544 verbatim port. Resolves the PS-class "tool call empty arguments" failure.

### R5 prior "OUT-OF-SCOPE" (surrogate sanitize) vs H1 "MEDIUM PRIORITY"
- **H1's surrogate sanitization (115 LOC)** is defense-in-depth for any Bedrock JSON content. R5 deferred because Runnable's parent feature (team-mem upload) was OOS. H1 demonstrates an independent Bedrock failure mode (model output → tool_result content with lone surrogates → boto3 JSON encoder crashes). **VERDICT: ADOPT (Block A-26).** Lines 384-502 verbatim. Per-Bedrock-call defensive layer.

### V1 "missing notebook_edit/view_image/skill" vs Wave 5 "v5 already has these"
- **V1's claim**: 11 v4 tools listed in Block T misses notebook_edit + view_image (v4 has 22+ tools).
- **Wave 5 reality**: `compact_v5/MAIN/agent/tools/notebook_edit.py` and `view_image.py` exist (built in Phase 4).
- **VERDICT**: V1 is right at PORT_LOG-row level (rows missing); wrong at code level (files present). **Action**: Add 2 PORT_LOG rows to Block T (T-1, T-2 marked FALSE-POSITIVE-ALREADY-IN-V5). Block T row count goes 11 → 13.

### R1 "Block J worktree" confusion clarification
- **R1 references Block J** in items #92, #105 ("EnterWorktree"/"ExitWorktree").
- **Plan v3 reality**: Block J = real-Bedrock smoke + zip verification. Worktree spawn lives in **Block G** (`AGENT_TYPES + worktree`).
- **VERDICT**: R1's "Block J" mentions are mis-tagged. **Action**: Re-tag to **Block G**. Drop EnterWorktree/ExitWorktree formal tools (R1 #92-108) — v4's worktree spawn is implicit (not a user-facing tool); SageMaker workspace usually `/home/sagemaker-user/`, not a git repo.

### MCP yes/no
- **Constraint #9**: Drop MCP entirely.
- **V1 reports MCP classes "PRESENT in v5 runtime/mcp_client.py"** — but actual filesystem inspection shows only `mcp/__init__.py` (empty).
- **VERDICT**: V1 was wrong. MCP is genuinely dropped in v5. Constraint #9 holds. No `mcp_client.py` to delete.

---

## 8. Critical rules adopted (Hermes A28 / A36 / A44)

### A28 — Prompt-cache invariant policy (Block A + Block 0)
**Statement**: NEVER rebuild system prompt mid-conversation. NEVER change toolsets mid-conversation. NEVER reload memories mid-conversation. The ONLY mid-conversation context mutation allowed is during context compression. Slash commands that mutate system-prompt state default to deferred invalidation (next session) with opt-in `--now` flag.
**Enforcement**:
- Block 0: `prompt/_CACHE_BOUNDARY.md` marker file (already exists in v5) — formalize via Block A-40 static/dynamic boundary refactor.
- Block A: A-21 `runPostCompactCleanup` invalidates cache **only on compact**.
- Block D: `/skill use --now` opt-in pattern; default = next-session.
- Block I: I-1 conditional `paths:` skill activation defers to next request boundary.

### A36 — Dynamic cross-tool reference (Block N — already in plan)
**Statement**: Tool schema descriptions MUST NOT mention tools from other toolsets by name (causes hallucination). Dynamic injection in `get_tool_definitions()` post-processing.
**Enforcement**: Plan v3 Block N already commits to this. Confirm Q1 evidence row cites Hermes AGENTS.md:627-628.

### A44 — No change-detector tests (Block K policy)
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
| Codex Responses API (H2 C29) | Bedrock-only | — |
| Anthropic API direct (H1 #22, H3 §1.7) | Bedrock-only | v5 uses boto3 Bedrock. |
| Gateway / `/steer` / interactive-handler (H2 C27-C30, H3 6-7-9) | No gateway in v5 single-user | — |
| Background-task subsystem (R7 C44-C49, Task/tasks/) | Constraint #1 + #2 | No bg-task UI in chat.ipynb. |
| `claude ps` / `--resume` / multi-conversation (R6 branch/rename) | Single-session | — |
| `/insights` (R6) | Host Claude Code logs only | Doesn't apply inside SageMaker agent. |
| Auto-dream `partialCompactConversation` (R4 #32) | No message-selector UI in ipynb | Drop. |
| Profile system (H5 A30-A32) | Single-user | — |
| Vim / keybindings / terminal setup (R6, R8 #46) | chat.ipynb UI | — |
| `cron` / scheduled remote agents (R2 ScheduleCronTool) | No daemon in SageMaker | — |
| `commit` / `commit-push-pr` slash commands (R6) | User-pref no autonomous commits | — |
| `branch` / `rename` (R6) | Single-conversation | — |
| Bridge / Remote / RemoteTrigger / SendUserFile (R2, R3, R10) | Bedrock-only no external network | — |
| WebSearch (R3 #21) | Bedrock provider not in `isEnabled()` allowlist | Permanently disabled even if shipped. |
| ASCII-only fallback (H1 #18) | SageMaker is UTF-8 | — |
| Credential pool / fallback chain (H1 #20, H3 §1.5/1.6/1.12, H5 #12-13, #15-16) | Single Bedrock IAM | — |
| `/factory-report` accept/reject loop (L2 LF-CMD-3) | Factory-level meta, not v5 | — |
| 4-agent UX grading (L2 LF-AUDIT-2) | v5 has no UX surface beyond frozen v4 chat.ipynb | — |
| `.claude/settings.json` per-project doctrine (L2 LF-DOC-10) | SageMaker has no Claude Code settings layer | — |
| LF hooks/* host-side (L1 most rows) | Host-side dev workflow, not Bedrock agent | — |
| Codex gpt-5.3-codex commit-gate (L1 codex-judge-gate) | Bedrock-only forbids OpenAI inside SageMaker | — |
| `tagMessagesWithToolUseID` (R3 utils.ts) | No streaming UI placeholders in v5 | — |
| Lazy hook framework / settings.json hooks (R9 #6-#10) | No multi-tenant settings infra | v4's audit_log + approval gate suffices for single-user. |
| Skill-improvement survey (R9 #7) | v4.9.5 model-proposes-patch is superior | — |
| Bash classifier auto-approval (R9 #8) | No permission dialog to race in single-user trust mode | — |
| `fileSuggestions.ts` @-mention typeahead (R9 #11) | No @-typeahead UI in Jupyter input | — |
| Output styles (R9 #19, R8 #72) | Fixed system prompt in v5 | — |
| TaskV2 family (R3 TaskCreate/Get/List/Update/Output/Stop) | Multi-agent swarm out-of-scope | — |
| Buddy/companion virtual pet (R10) | UI gimmick | — |

**Total drops with categorical reason: ~80 patterns/tools.**

---

## 10. Total LOC estimate + sequence

### Pre-Wave-5 → Post-Wave-5-DEEP
- **Pre-Wave-5**: 11,330 LOC, 18 Blocks (E+F counted as 1 combined)
- **Post-Wave-5-DEEP**: ~19,300 LOC (corrected per Codex AXIS A 2026-05-01 — actual sum of per-Block NEW deltas is ~7,943 LOC NEW + 11,330 LOC pre-DEEP = ~19,273; rounded to ~19,300), **21 Blocks** counting E+F as 1 combined block (added: G3, F2, H+); plus notebook-smoke-gate checkpoint after Block 0
- **Growth**: 1.70x (consistent with R4 alone projecting +1,900-2,200 LOC and being one of 20 slices)
- **New PORT_LOG rows**: +233 (Q1 matrix grows from 215 → ~448 rows)
- **New blocks**: G3 (Coordinator Prompt), F2 (Auto-Continuation), H+ (Auto-Dream)

### Updated build sequence

```
Block 0  → notebook smoke gate
        → B   (TokenTracker + Bedrock count + ToolResult)
        → B+  (SessionManager + cost UI + FileCache)
        → C   (Runtime safety + secret scanner + bash hardening + JSON repair)
        → C+  (Approval/diff + rate limits — minus Plan Mode)
        → D   (Slash commands + custom expander + new skills + /dream)
        → A   (Compactor COMBINED + cache invariants + sanitize)
        → E + F  (UI rendering + cell widgets)
        → F2  (NEW — auto-continuation under iteration budget)
        → I   (Skill discovery + paths: + scaffolders)
        → M   (Phase 8 fixes — already small)
        → G   (AGENT_TYPES + worktree + agent memory scoped)
        → G3  (NEW — coordinator system prompt)
        → G2  (forkSubagent cache-prefix replay)
        → H   (Memory extraction COMBINED + invariant-preserving SM-compact)
        → H+  (NEW — memory consolidation engine, manual /dream only, no daemon)
        → L   (Error/retry/cache-break + Bedrock guardrails + daemon-thread call)
        → N   (Parallel exec + dynamic tool refs — full citations)
        → T   (v4 tool surface + WebFetch fold-ins + readFileInRange)
        → J   (Real-Bedrock smoke + zip verify)
        → K   (Process discipline + AXIS C + 3-critic + A44 test refactor)
```

Each Block lands as **commit + Codex AXIS A/B/C 3-critic review + user approval** (per Block K + L2 LF-DOC-5).

---

## 11. Files to update

### `V5_PHASE_2_PLAN_v3.md` → write **`V5_PHASE_2_PLAN_v5.md`** (renaming v4→v5 since this is post-Wave-5-DEEP)
Sections that need changes:
- §1 (v4 baseline COMPLETE table): add 14 rows from V1 verifier (ToolResult / SecurityManager class / SemanticSearch / SYSTEM_PROMPT / BedrockClient / Config dataclass / ContextManager / Truncation / RetryHandler decision / MCP-drop confirmation / load_project_instructions / _scan_for_prompt_injection / Config piecemeal-to-master).
- §2 (15 hard constraints): unchanged.
- §3 (Block-by-block plan): expand each Block with the per-block deltas from §3 above. Add Block G3, F2, H+ as new sub-sections.
- §4 (Sequencing): replace with the updated sequence in §10 above.
- §5 (LOC summary): replace with §3 table above (post-Wave-5 totals).
- §6 (4 user-question evidence): no change to mapping; reinforce K-6 (no-change-detector) under Q4.
- §7 (Status): append "Wave 5-DEEP synthesis complete; +233 PORT_LOG rows; 3 new Blocks; pending Codex AXIS A/B/C 3-critic review."

### `Q1_EVIDENCE_MATRIX.md`
Append rows N to N+232 (rows 216-448). Each row references one source file:line. Add new column `evidence_tier: VERIFIED | LISTED` (per K-2). Mark all 233 new rows VERIFIED (Wave-5-DEEP read full files). Mark Wave 1-4 prior rows that didn't verify source as LISTED (separate audit pass).

### `Q3_BETTER_THAN_MATRIX.md`
Add new axis row "security/PII protection" (R5 finding) — v5 > v4 (38 patterns + redaction vs 13 patterns).

### `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` (THIS FILE)
Canonical builder reference going forward. Builder applies verbatim before each Block.

### `V5_BUILD_STATUS.md`
Append entry:
```
2026-05-01 Wave 5-DEEP synthesis complete.
- 20 reports consumed (R1-R12, H1-H5, L1-L2, V1)
- ~150 net-new findings consolidated
- 233 PORT_LOG rows added (Q1 matrix 215 → 448)
- 3 new Blocks: G3 (Coordinator Prompt), F2 (Auto-Continuation), H+ (Memory Consolidation Engine, manual /dream only — no daemon)
- 5 NOT-OPTIONAL correctness fixes flagged
- LOC: 11,330 → ~16,200 (1.43x)
- Pending: Codex AXIS A/B/C 3-critic review per Block K
- Reading order: SYNTHESIS_MASTER.md → V5_PHASE_2_PLAN_v5.md → Q1_EVIDENCE_MATRIX.md
```

### `compact_v5/_phase_2/wave_5_deep/00-SYNTHESIS.md`
Symlink or short pointer to SYNTHESIS_MASTER.md so the audit-dir shape (per K-1, L2 LF-DOC-6) is satisfied.

### Audit dir naming retrofit
Rename current Wave-5-DEEP files to follow pattern (`01-R1-tools-A-F.md`, `02-R2-tools-G-R.md`, ..., `21-V1-v4-inventory.md`, `22-SYNTHESIS-MASTER.md`) — DEFERRED: optional polish per K-1; not a blocker.

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
