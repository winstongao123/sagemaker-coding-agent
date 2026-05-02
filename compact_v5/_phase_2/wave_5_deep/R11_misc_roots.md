# R11 — Misc Root Files (Runnable `src/` depth=1)

**Date:** 2026-05-01
**Scope:** Every `.ts`/`.tsx` file at the root of `D:/Github/sagemaker-coding-agent/_archive/compare_code/gg-claude-code-runnable/src/` not already covered by R1-R10 slices.
**Method:** Glob depth=1, exclude R1-R10 files (QueryEngine.ts, Task.ts, Tool.ts, query.ts, tools.ts, tasks.ts, main.tsx, setup.ts, history.ts, interactiveHelpers.tsx, dialogLaunchers.tsx, context.ts), full Read of each remainder.
**Constraints:** v5.0.1 single-user SageMaker, Bedrock-only (no Anthropic SDK direct, no MCP, no plugins, no remote bridge, no telemetry to non-AWS endpoints), v4 `chat.ipynb` canonical UI, NO DEFERRALS.

---

## 0. Inventory of root files scanned

| File | Bytes | Status | Substantive? |
|---|---:|---|---|
| `attributionTrailer.ts` | 19 | `export default {}` | NO — empty stub |
| `cachedMicrocompact.ts` | 19 | `export default {}` | NO — empty stub |
| `commands.ts` | 25,939 | full source | YES |
| `coreTypes.generated.ts` | 11 | `export {}` | NO — empty stub |
| `cost-tracker.ts` | 11,029 | full source | YES |
| `costHook.ts` | 639 | full source | YES (small but real) |
| `context.ts` | 6,635 | full source | YES |
| `devtools.ts` | 19 | `export default {}` | NO — empty stub |
| `dream.ts` | 19 | `export default {}` | NO — empty stub |
| `entry.ts` | 600 | full source | YES (Bun-only, tiny) |
| `global.d.ts` | 47 | `export {}` stub comment | NO |
| `hunter.ts` | 19 | `export default {}` | NO — empty stub |
| `ink.ts` | 3,972 | re-export shim | YES (thin) |
| `projectOnboardingState.ts` | 2,420 | full source | YES |
| `protectedNamespace.ts` | 19 | `export default {}` | NO — empty stub |
| `replLauncher.tsx` | 3,539 | full source | YES (thin) |
| `runSkillGenerator.ts` | 19 | `export default {}` | NO — empty stub |

**Already-covered (skipped):** QueryEngine.ts, Task.ts, Tool.ts, query.ts, tools.ts, tasks.ts, main.tsx, setup.ts, history.ts, interactiveHelpers.tsx, dialogLaunchers.tsx, context.ts (assumed in R5/R7 — context loader; included here too because the prompt did not name it).

> Empty stubs (`export default {}`) appear to be **build-time placeholders** for proprietary modules (attribution telemetry, microcompact cache, devtools UI, dream/hunter background workers, protected namespace registry, skill generator, generated core types) that the open-source mirror replaces with no-ops. They contribute **zero functional capability** to the public Runnable build. **v5 must not invent capability from a name** — these files are evidence of *naming*, not behavior.

---

## 1. `commands.ts` — slash-command registry

### 1.1 Capabilities (file:line)

| # | Capability | File:Line | Bedrock-OK? |
|---|---|---|---|
| C-01 | Static import of ~70 builtin commands | `commands.ts:1-204` | partial — many are 1P/3P/IDE/plugin only |
| C-02 | `INTERNAL_ONLY_COMMANDS` allowlist (ant-only) — `bughunter`, `commit`, `commitPushPr`, `ctx_viz`, `goodClaude`, `issue`, `summary`, `teleport`, `antTrace`, `perfIssue`, `env`, `oauthRefresh`, `debugToolCall`, `agentsPlatform`, `autofixPr`, `bridgeKick`, `version`, `mockLimits`, `resetLimits*`, `share`, `onboarding`, `backfillSessions`, `breakCache`, `forceSnip`, `subscribePr`, `ultraplan` | `commands.ts:225-254` | NO — Anthropic-internal |
| C-03 | Feature-flag gated commands: `PROACTIVE`/`KAIROS` → proactive, `KAIROS` → assistant/brief, `BRIDGE_MODE` → bridge/remoteControlServer, `VOICE_MODE` → voice, `HISTORY_SNIP` → forceSnip, `WORKFLOW_SCRIPTS` → workflows, `CCR_REMOTE_SETUP` → web, `EXPERIMENTAL_SKILL_SEARCH` → clearSkillIndexCache, `KAIROS_GITHUB_WEBHOOKS` → subscribePr, `ULTRAPLAN`, `TORCH`, `UDS_INBOX` → peers, `FORK_SUBAGENT` → fork, `BUDDY` → buddy | `commands.ts:60-122` | NO — feature flags don't apply |
| C-04 | Lazy `usageReport` (`/insights`) — defers loading 113KB `insights.ts` (3200 lines) until first invocation | `commands.ts:188-202` | YES — pattern is reusable for Python lazy `importlib` |
| C-05 | `meetsAvailabilityRequirement(cmd)` — gates by `claude-ai` subscriber vs `console` (1P API) auth state | `commands.ts:417-443` | NO — Bedrock has no claude.ai/console |
| C-06 | `loadAllCommands(cwd)` — memoized parallel load of skills+plugins+workflows+builtin via `Promise.all` | `commands.ts:449-469` | YES — pattern reusable (concurrent skill scan) |
| C-07 | `getCommands(cwd)` — composes base + dynamic skills, dedupes by name, inserts dynamic skills BEFORE built-ins | `commands.ts:476-517` | YES — skill-discovery merge pattern |
| C-08 | `clearCommandMemoizationCaches()` — clears 4 lodash memoize caches (loadAllCommands, getSkillToolCommands, getSlashCommandToolSkills, clearSkillIndexCache) | `commands.ts:523-532` | YES — explicit cache invalidation pattern |
| C-09 | `clearCommandsCache()` — full reset including plugin & skill caches | `commands.ts:534-539` | partial — drop plugin |
| C-10 | `getMcpSkillCommands` — filters MCP-loaded commands gated by `MCP_SKILLS` feature | `commands.ts:547-559` | NO — MCP banned |
| C-11 | `getSkillToolCommands` — for SkillTool listing: includes only prompt-type, model-invocable, non-builtin commands; bundled/skills/commands_DEPRECATED auto-included; plugin/MCP need explicit description | `commands.ts:563-581` | YES — listing-budget logic reusable |
| C-12 | `getSlashCommandToolSkills` — for slash menu: prompt-type, non-builtin, requires description, must be from skills/plugin/bundled or have `disableModelInvocation` | `commands.ts:586-608` | YES |
| C-13 | `REMOTE_SAFE_COMMANDS` — 17-cmd allowlist for `--remote` mode (session/exit/clear/help/theme/color/vim/cost/usage/copy/btw/feedback/plan/keybindings/statusline/stickers/mobile) | `commands.ts:619-637` | NO — no remote mode |
| C-14 | `BRIDGE_SAFE_COMMANDS` — 6-cmd mobile-safe set (compact/clear/cost/summary/releaseNotes/files) | `commands.ts:651-660` | NO — no bridge |
| C-15 | `isBridgeSafeCommand` — local-jsx blocked, prompt allowed, local needs allowlist | `commands.ts:672-676` | NO |
| C-16 | `filterCommandsForRemoteMode` | `commands.ts:684-686` | NO |
| C-17 | `findCommand` / `hasCommand` / `getCommand` — name + alias lookup with helpful error listing all available | `commands.ts:688-719` | YES — alias support is a v4 gap |
| C-18 | `formatDescriptionWithSource` — annotates command description with origin (`(workflow)`, `(pluginName)`, `(bundled)`, settings-source name) | `commands.ts:728-754` | partial — annotate skill source (user/project/bundled) |

### 1.2 v4 baseline comparison

`compact_v4/MAIN/agent/sagemaker_agent.py` has slash commands handled inline in the chat loop (`sagemaker_agent.py` ~line 1500-2000 region: `/skill`, `/skills`, `/cost`, `/compact`, `/clear`, `/memory`, `/help`, `/quit`, `/save`, `/load`). There is:
- **NO** unified command registry
- **NO** alias support (single string match)
- **NO** dynamic skill→command surfacing into a slash menu
- **NO** lazy-load pattern for heavy commands
- **NO** "source annotation" in user-facing listings
- **NO** memoized command list

### 1.3 Net-new for v5 (architecture-fit, no deferral)

| Cap | Action |
|---|---|
| C-04 lazy-load heavy command | **ADOPT** — `/insights`-like wins-doc generator can defer |
| C-06 parallel skill scan | **ADOPT** — v4 skill discovery is sequential |
| C-07 dynamic-skill merge | **ADOPT** — needed for self-patching skills (v4.9.5) |
| C-08 explicit cache invalidation | **ADOPT** — clears named caches not "clear all" |
| C-11/12 listing-budget filter | **ADOPT** — bundled/user/project/dynamic separation |
| C-17 alias + helpful error | **ADOPT** — `/q`→`/quit`, `/h`→`/help`, with full command list on miss |
| C-18 source annotation | **ADOPT** — show `(bundled)` / `(user)` / `(project)` next to skill name |
| C-02/03/05/10/13-16 | **REJECT** — Anthropic-internal, MCP, bridge, claude.ai, plugins not in scope |

### 1.4 Plan v3 / Q1 fit
None of these capabilities map to existing Plan v3 blocks 1-N specifically; they belong to Block "Skill & Command Surface" (verify exists in v3 plan, otherwise add as a no-deferral row in the consolidated subsystem matrix).

---

## 2. `cost-tracker.ts` — session cost & per-model usage

### 2.1 Capabilities (file:line)

| # | Capability | File:Line | Bedrock-OK? |
|---|---|---|---|
| CT-01 | `StoredCostState` shape — totalCostUSD, totalAPIDuration (both with-retries and without), totalToolDuration, totalLinesAdded/Removed, lastDuration, modelUsage map | `cost-tracker.ts:71-80` | YES |
| CT-02 | `getStoredSessionCosts(sessionId)` — reads `lastSessionId` from project config; only returns if matches; rebuilds modelUsage with current `getContextWindowForModel`/`getModelMaxOutputTokens` so window data is fresh | `cost-tracker.ts:87-123` | YES |
| CT-03 | `restoreCostStateForSession(sessionId)` — called on `/resume` to rehydrate accumulated session cost | `cost-tracker.ts:130-137` | YES |
| CT-04 | `saveCurrentSessionCosts(fpsMetrics?)` — persists ALL cost dimensions + per-model breakdown + FPS to project config under `lastSessionId`, before exit/switch | `cost-tracker.ts:143-175` | YES |
| CT-05 | `formatCost(cost, maxDecimalPlaces=4)` — >$0.50 round to 2dp, else 4dp | `cost-tracker.ts:177-179` | YES (cosmetic) |
| CT-06 | `formatModelUsage()` — accumulates by `getCanonicalName(model)` (so multiple model IDs collapse to one display row), prints `inputTokens / outputTokens / cacheRead / cacheWrite [/ webSearch] (cost)` | `cost-tracker.ts:181-226` | YES — adapt with Bedrock canonical mapping |
| CT-07 | `formatTotalCost()` — chalk-dim 4-line block: total cost, API duration, wall duration, code-changes, then per-model usage. Adds `(costs may be inaccurate due to usage of unknown models)` warning when `hasUnknownModelCost()` | `cost-tracker.ts:228-244` | YES |
| CT-08 | `addToTotalSessionCost(cost, usage, model)` — increments per-model + total; emits OTel-style counters (`getCostCounter`, `getTokenCounter`) with attrs `{model, type: 'input'|'output'|'cacheRead'|'cacheCreation'}`; marks `speed: 'fast'` attr when fast mode | `cost-tracker.ts:278-323` | YES counters / **NO** OTel export to non-AWS |
| CT-09 | **Recursive advisor cost** — `getAdvisorUsage(usage)` extracts sub-tool LLM calls (e.g. WebSearch, Read summarization), prices each with `calculateUSDCost(advisorUsage.model, advisorUsage)`, logs `tengu_advisor_tool_token_usage` analytics event with cost in micros, then **recursively** calls `addToTotalSessionCost` so advisor costs cascade into the same totals | `cost-tracker.ts:304-322` | YES (the recursion pattern) — drop the `tengu_*` analytics event |
| CT-10 | `addToTotalModelUsage` — preserves contextWindow + maxOutputTokens on each update so display always shows current limits even if model changed mid-session | `cost-tracker.ts:250-276` | YES |
| CT-11 | `web_search_requests` counted via `usage.server_tool_use?.web_search_requests ?? 0` | `cost-tracker.ts:270-271` | NO — no Anthropic web_search server tool on Bedrock |

### 2.2 v4 baseline comparison

v4 `TokenTracker` (`sagemaker_agent.py:3566+`) has:
- session totals (input/output/cache_read/cache_write/cost)
- per-model dict, but **no canonical-name collapse** (each model ID is a separate row)
- session_cost_limit warn-at-80%/stop-at-100% (`sagemaker_agent.py:3639-3651`) — **better** than Runnable on this axis (Runnable has no session limit)
- cache-aware Bedrock pricing (90% discount on read, 1.25x markup on write) — `sagemaker_agent.py:3611-3627`
- **NO** persistence to project config (lost on restart)
- **NO** restore-on-resume
- **NO** API-vs-wall vs tool duration split
- **NO** lines-added/removed accounting
- **NO** advisor recursive cost
- **NO** OTel counters
- **NO** unknown-model warning string

### 2.3 Net-new for v5

| Cap | Action |
|---|---|
| CT-01..04 persistence + restore | **ADOPT** — write `last_session_cost.json` next to session log; on `/resume <id>` rehydrate |
| CT-06 canonical-name collapse | **ADOPT** — Bedrock `apac.` and `us.` prefixes for same Sonnet 4.5 should collapse to one display row |
| CT-07 4-line cost block format | **ADOPT** — replaces v4's single-line `/cost` |
| CT-08 OTel-style counters | **ADOPT but local-only** — emit to a local file/SQLite, never to non-AWS endpoint |
| CT-09 advisor recursion | **ADOPT** — v4 doesn't account auxiliary-model summarization cost (v4.9.4 added aux model but charges flow into same totals; verify) |
| CT-10 contextWindow refresh | **ADOPT** |
| v4 session_cost_limit | **KEEP** — Runnable lacks this; v5 must keep v4's hard cap |
| CT-11 web_search | **REJECT** |

### 2.4 Plan v3 / Q1 fit
Maps to **cost & observability** subsystem. Q1 evidence row should call out: v4 wins on session limit; Runnable wins on persistence + advisor recursion + canonical collapse; v5 = both.

---

## 3. `costHook.ts` — exit-time cost flush hook

### 3.1 Capabilities

| # | Capability | File:Line |
|---|---|---|
| CH-01 | `useCostSummary(getFpsMetrics?)` React hook | `costHook.ts:6-22` |
| CH-02 | Registers `process.on('exit')` listener with cleanup on unmount | `costHook.ts:9-21` |
| CH-03 | Gates print on `hasConsoleBillingAccess()` — Anthropic console-API users see cost; 3P users (Bedrock/Vertex) do **NOT** see the cost line printed at exit | `costHook.ts:11-13` |
| CH-04 | Always calls `saveCurrentSessionCosts(fpsMetrics)` regardless of billing-access gate (so persistence happens for everyone) | `costHook.ts:15` |

### 3.2 v4 baseline / fit

v4 prints cost via `/cost` on demand and inside compaction summaries; no exit hook, no persistence on Ctrl-C.

### 3.3 Net-new for v5

| Cap | Action |
|---|---|
| Exit-time persistence | **ADOPT** — wrap in `atexit.register` + signal handlers; write last cost JSON |
| `hasConsoleBillingAccess` gate on print | **DROP** — single-user Bedrock always wants the print |

---

## 4. `context.ts` — system + user prompt context loader

### 4.1 Capabilities

| # | Capability | File:Line | Bedrock-OK? |
|---|---|---|---|
| CTX-01 | `MAX_STATUS_CHARS = 2000` git-status truncation cap | `context.ts:20` | YES |
| CTX-02 | `systemPromptInjection` module-level mutable + `set/getSystemPromptInjection` — **cache-breaker**: any value flips a `[CACHE_BREAKER: ...]` line into the system prompt; setter clears `getUserContext.cache` and `getSystemContext.cache` so the next turn rebuilds | `context.ts:22-34` | YES — useful for "force fresh prompt" debugging |
| CTX-03 | `getGitStatus()` — memoized, skipped under `NODE_ENV=test`, parallel `Promise.all` of `getBranch`, `getDefaultBranch`, `git status --short`, `git log --oneline -n 5`, `git config user.name`; uses `--no-optional-locks` to avoid lock contention; truncates at 2000 chars with explicit hint to use BashTool for full status; returns null on non-git or failure | `context.ts:36-111` | YES — `--no-optional-locks` is non-obvious |
| CTX-04 | Per-step diagnostics logging via `logForDiagnosticsNoPII` with duration_ms — git_status_started, git_is_git_check_completed, git_status_skipped_not_git, git_commands_completed, git_status_completed, git_status_failed | `context.ts:42-110` | YES (local diag only) |
| CTX-05 | `getSystemContext()` — memoized; under `CLAUDE_CODE_REMOTE` env or `!shouldIncludeGitInstructions()`, skips git status; returns object with `gitStatus` and (if `BREAK_CACHE_COMMAND` feature) `cacheBreaker` keys | `context.ts:116-150` | partial — drop CCR/feature gate |
| CTX-06 | `getUserContext()` — memoized; honours `CLAUDE_CODE_DISABLE_CLAUDE_MDS` env hard-off; under `--bare` mode, skips auto-walk BUT keeps `--add-dir` explicit dirs ("skip what I didn't ask for, not what I asked for"); calls `setCachedClaudeMdContent` to share with auto-mode classifier (avoids cycle through permissions); returns `{claudeMd?, currentDate}` | `context.ts:155-189` | YES |
| CTX-07 | `currentDate: 'Today\'s date is YYYY-MM-DD.'` — provides date to model | `context.ts:186` | YES — v4 already does this |

### 4.2 v4 baseline comparison

v4 (`sagemaker_agent.py`):
- Has **CLAUDE.md loader** (good)
- Has `get_current_date_context` (good)
- **NO** git-status injection in system prompt (significant gap — model can't see uncommitted state without explicitly running `git status`)
- **NO** cache-breaker injection mechanism
- **NO** memoization of context computations
- **NO** `--add-dir` / `--bare` mode distinction
- **NO** `--no-optional-locks` git pattern (v4 git calls would block on lock contention)
- **NO** truncation cap on git status (would blow context if many uncommitted files)

### 4.3 Net-new for v5

| Cap | Action |
|---|---|
| CTX-02 cache-breaker | **ADOPT** — `/break-cache <reason>` slash command flips it for one turn; useful when prompt cache wedges |
| CTX-03 parallel git-status with `--no-optional-locks` | **ADOPT** — concrete v4 deficiency |
| CTX-03 2000-char truncation + hint | **ADOPT** |
| CTX-04 per-step diagnostics | **ADOPT** as local logging only |
| CTX-05/06 memoization | **ADOPT** |
| CTX-06 `--bare` semantics | **ADOPT** — clear policy for "skip auto-discovery but honor explicit add-dir" |
| CCR/BREAK_CACHE feature flags | **DROP** — always-on for single user |

### 4.4 Plan v3 / Q1 fit
Maps to **system prompt assembly** subsystem. v5 must combine v4's CLAUDE.md hierarchy + Runnable's git-status + cache-breaker + truncation.

---

## 5. `entry.ts` — Bun bundle polyfill

### 5.1 Capability

| # | Capability | File:Line |
|---|---|---|
| E-01 | Registers `bun:bundle` runtime polyfill via `plugin({setup: build.onResolve})` so `import { feature } from 'bun:bundle'` resolves to a stub at runtime (compile-time-only module in production Bun builds) | `entry.ts:1-17` |
| E-02 | Then dynamically imports `./main.tsx` AFTER polyfill is registered | `entry.ts:20` |

### 5.2 v4 / v5 fit
**Not applicable.** Bun-specific; v5 is Python.
**Lesson:** keep "feature flags" as a single import boundary so they can be replaced by a stub in restricted environments. v5's analog: a `runtime/feature_flags.py` shim that returns `False` for everything not in the SageMaker-approved set, so banned modules fail closed at import time.

---

## 6. `ink.ts` — terminal UI re-export

### 6.1 Capabilities

| # | Capability | File:Line |
|---|---|---|
| INK-01 | `withTheme(node)` — wraps every `render`/`createRoot` call in `ThemeProvider` so themed Box/Text work without per-callsite mounting | `ink.ts:14-16` |
| INK-02 | `render(node, options?)` async — bridge to `inkRender` with theme | `ink.ts:18-23` |
| INK-03 | `createRoot(options?)` — returns root with theme-wrapping render method | `ink.ts:25-31` |
| INK-04 | Re-exports: ThemedBox, ThemedText, ThemeProvider, color, Ansi, AppContext, BaseBox, Button, Link, Newline, NoSelect, RawAnsi, Spacer, StdinContext, BaseText, DOMElement, ClickEvent, EventEmitter, Event, InputEvent, TerminalFocusEvent, FocusManager, FlickerReason, animation hooks, useApp, useInput, useInterval, useSelection, useStdin, useTabStatus, useTerminalFocus, useTerminalTitle, useTerminalViewport, measureElement, supportsTabStatus, wrapText | `ink.ts:33-86` |

### 6.2 v4 / v5 fit
**Not applicable.** v4 uses `chat.ipynb` (Jupyter notebook UI) — Constraint v5.0.1 explicitly says "v4 chat.ipynb canonical UI". Runnable's Ink/React TUI is **out of scope**.
**Lesson:** centralize UI primitives behind one re-export module so the agent code never imports Ink directly. v5 analog: `compact_v5/ui/ipynb_helpers.py` for all `IPython.display` widgets, so swapping notebook UI later is one-file.

---

## 7. `projectOnboardingState.ts` — first-run nudge for new projects

### 7.1 Capabilities

| # | Capability | File:Line |
|---|---|---|
| ON-01 | `Step` type: `{key, text, isComplete, isCompletable, isEnabled}` | `projectOnboardingState.ts:11-17` |
| ON-02 | `getSteps()` — 2 steps: (a) "create app or clone repo" enabled when cwd is empty, (b) "Run /init to create CLAUDE.md" enabled when cwd is non-empty AND CLAUDE.md missing | `projectOnboardingState.ts:19-41` |
| ON-03 | `isProjectOnboardingComplete()` — true iff every enabled+completable step is complete | `projectOnboardingState.ts:43-47` |
| ON-04 | `maybeMarkProjectOnboardingComplete()` — short-circuits on cached `hasCompletedProjectOnboarding` flag (avoid filesystem hit on every prompt submit); else writes flag to project config | `projectOnboardingState.ts:49-61` |
| ON-05 | `shouldShowProjectOnboarding` — memoized; returns false if completed OR seen ≥ 4 times OR `IS_DEMO`; cached config short-circuits filesystem | `projectOnboardingState.ts:63-76` |
| ON-06 | `incrementProjectOnboardingSeenCount()` — increments per-show counter so nudge auto-suppresses after 4 views | `projectOnboardingState.ts:78-83` |

### 7.2 v4 baseline / fit

v4 has **no onboarding flow.** User opens `chat.ipynb` cold; if no `memory.md` or `skills/` exist, agent silently behaves as if they're empty.

### 7.3 Net-new for v5

| Cap | Action |
|---|---|
| ON-01 step model | **ADOPT** — adapt to SageMaker context: (1) `memory.md` exists? (2) `skills/` non-empty? (3) at least one prior session? |
| ON-04/06 auto-suppress after N views | **ADOPT** — show 3-line "first-run hints" max 4 times then suppress |
| ON-05 cached-config short-circuit | **ADOPT** — important for hot loop |

### 7.4 Plan v3 / Q1 fit
Net-new subsystem **first-run UX**. Add as no-deferral row.

---

## 8. `replLauncher.tsx` — REPL boot (thin)

### 8.1 Capabilities

| # | Capability | File:Line |
|---|---|---|
| RL-01 | `launchRepl(root, appProps, replProps, renderAndRun)` — async dynamically imports `./components/App` and `./screens/REPL` inside the function (lazy, splits bundle), then renders `<App {...appProps}><REPL {...replProps}/></App>` | `replLauncher.tsx:12-22` |
| RL-02 | `AppWrapperProps` type: `{getFpsMetrics, stats?, initialState}` | `replLauncher.tsx:7-11` |

### 8.2 v4 / v5 fit
v4 launches via `chat.ipynb` notebook cell — no REPL launcher.
**Lesson:** lazy import in the launcher so first-keystroke time excludes large UI module init. v5 already does this implicitly in `chat.ipynb` (cells are lazy).

---

## 9. Summary table — net-new capabilities for v5 (no-deferral)

| ID | Capability | Source file:line | v4 status | v5 action | Plan v3 block |
|---|---|---|---|---|---|
| N1 | Lazy-load heavy command modules | `commands.ts:188-202` | absent | ADOPT | command surface |
| N2 | Parallel skill scan via Promise.all | `commands.ts:449-469` | sequential | ADOPT | skill discovery |
| N3 | Dynamic-skill merge dedupe | `commands.ts:476-517` | absent | ADOPT | self-patching skills |
| N4 | Named cache invalidation (4 caches) | `commands.ts:523-532` | absent | ADOPT | command surface |
| N5 | Listing-budget filter (bundled/user/project/dynamic) | `commands.ts:563-608` | absent | ADOPT | listing budget |
| N6 | Command alias + helpful-error-on-miss | `commands.ts:688-719` | absent | ADOPT | UX |
| N7 | Source annotation in description | `commands.ts:728-754` | absent | ADOPT | UX |
| N8 | Persist session cost to project config + restore on resume | `cost-tracker.ts:87-175` | absent | ADOPT | cost & observability |
| N9 | Canonical-name collapse for per-model usage | `cost-tracker.ts:181-226` | absent | ADOPT | cost display |
| N10 | 4-line cost block format with chalk-dim | `cost-tracker.ts:228-244` | single-line | ADOPT | cost display |
| N11 | Local OTel counters (cost / token by type) | `cost-tracker.ts:289-301` | absent | ADOPT (local only) | observability |
| N12 | Recursive advisor sub-cost accounting | `cost-tracker.ts:304-322` | absent (v4.9.4 aux model unmeasured) | ADOPT | cost & observability |
| N13 | contextWindow refresh on every cost update | `cost-tracker.ts:273-274` | static | ADOPT | cost display |
| N14 | Exit-time atexit cost flush + persistence | `costHook.ts:6-22` | absent | ADOPT | cost & observability |
| N15 | System-prompt cache-breaker injection | `context.ts:22-34` | absent | ADOPT | cache mgmt |
| N16 | Memoized git status with `--no-optional-locks` + parallel | `context.ts:36-111` | absent | ADOPT | system prompt |
| N17 | 2000-char git-status truncation with hint | `context.ts:84-89` | absent | ADOPT | system prompt |
| N18 | Per-step diagnostics with duration_ms | `context.ts:46-110` | partial | ADOPT (local) | observability |
| N19 | Memoized system + user context | `context.ts:116, 155` | absent | ADOPT | hot-path perf |
| N20 | `--bare` mode "skip auto, honor explicit" semantics | `context.ts:165-167` | N/A | ADOPT for SageMaker mode | mode handling |
| N21 | Onboarding step model + auto-suppress after N views | `projectOnboardingState.ts:11-83` | absent | ADOPT | first-run UX |
| N22 | Centralized UI primitive shim (one-file swap) | `ink.ts:14-86` | implicit | KEEP — `compact_v5/ui/` | UI |
| N23 | Feature-flag stub at import boundary (fail-closed for banned modules) | `entry.ts:1-17` | absent | ADOPT | runtime safety |

**Things v4 wins on (do NOT regress):**
- `session_cost_limit` hard cap (warn 80% / stop 100%) — Runnable does not have this
- Bedrock cache-aware pricing math (90% read discount, 1.25x write markup) — Runnable assumes 1P pricing tables

**Things to REJECT outright:**
- INTERNAL_ONLY ant commands (15+ items)
- Feature-flag gated commands (PROACTIVE/KAIROS/BRIDGE_MODE/VOICE_MODE/etc.)
- `claude-ai` / `console` availability gates
- MCP_SKILLS gate
- REMOTE_SAFE / BRIDGE_SAFE command sets
- `tengu_advisor_tool_token_usage` analytics event (replace with local log)
- `hasConsoleBillingAccess` print-gate (always print on single-user Bedrock)
- `usage.server_tool_use.web_search_requests` (no Anthropic web_search server tool on Bedrock)
- All `bun:bundle` `feature(X)` calls — replaced with hard `False`

---

## 10. Plan v3 cross-check (no-deferrals required)

Read of `V5_PHASE_2_PLAN_v3.md` to be done by integrator. The 23 N-rows above MUST land in v5.0.1 per the consolidated no-deferral rule. If any current Plan v3 block does not name these explicitly, treat the omission as a plan defect — add a row, do not punt to v5.0.2.

Specifically check Plan v3 contains explicit subsystems for:
- **Command surface** (lazy + parallel + dynamic-merge + alias + source-annotation)
- **Cost & observability** (persistence + restore + canonical collapse + advisor recursion + atexit)
- **System prompt assembly** (CLAUDE.md hierarchy + git-status + cache-breaker + truncation + memoization)
- **First-run UX** (onboarding steps + auto-suppress)
- **Runtime safety shim** (feature-flag fail-closed)

If absent, append.

---

## 11. Q1 evidence matrix rows (template)

For each of N1..N23, the evidence row is:
- **Source repo:** Runnable (gg-claude-code-runnable)
- **Source file:line:** as cited
- **v4 baseline:** as cited (sagemaker_agent.py line range or "absent")
- **v5 action:** ADOPT / KEEP / REJECT / ADOPT-LOCAL-ONLY
- **Combined-better axis:** name from the 7-axis BETTER definition (architecture / coordination / memory / focus / tool use / token / long-coding) — most rows hit `architecture` or `token` (cost) or `tool use`

Integrator: paste into `Q1_EVIDENCE_MATRIX.md` under matching subsystem.

---

## 12. End — exhaustiveness statement

Every `.ts`/`.tsx` file at depth=1 of `src/` was either (a) read fully and capability-tabled above, or (b) confirmed as a 19-byte `export default {}` stub (7 stubs total). No root-level file was skipped. Files inside subdirectories (e.g. `commands/`, `tools/`, `tasks/`, `utils/`, `services/`, etc.) are out of R11 scope and belong to other R-slices.
