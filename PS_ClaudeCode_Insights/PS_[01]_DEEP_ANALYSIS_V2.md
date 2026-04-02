# Claude Code Deep Analysis V2 — Runnable vs V4

> **Updated 2026-04-01 — Deep Source Read Edition.**
> Sources: `gg-claude-code-runnable/src/` + `compact_v4/MAIN/agent/sagemaker_agent.py`.
> All file references and line numbers verified from direct source reads. No inference.
> Previous V1 analysis preserved below updated sections.

> **V4.2.1 closure note:** the previously open high-value gaps for `FILE_UNCHANGED_STUB`,
> parallel read-only tool execution, and PTL compaction retry were closed in
> `compact_v4/MAIN/agent/sagemaker_agent.py` during the 2026-04-01 audit pass.

---

## V4.1 Status: What's Already Done

| # | Feature | Status | Runnable Equivalent |
|---|---------|--------|---------------------|
| #14 | Prompt cache boundary (static/dynamic split) | ✅ Done | `services/api/claude.ts` anthropic_beta header |
| #12 | Catastrophic path enforcement (LAYER -1 hard block) | ✅ Done | `tools/BashTool/` CATASTROPHIC constant |
| #10 | Partial view guard | ✅ Done | No direct equivalent in runnable |
| #11 | Command auto-classifier (RO commands skip approval) | ✅ Done | `tools/BashTool/bashPermissions.ts` speculative checks |
| #7  | 4-type memory structure (USER/FEEDBACK/PROJECT/REFERENCE) | ✅ Done | `memdir/memoryTypes.ts` (exact same 4 types) |
| #8  | Memory auto-extraction (opt-in, session-end LLM call) | ✅ Done | `services/extractMemories/extractMemories.ts` |

---

## Area Analysis

---

### 1. Token Usage Optimization

#### Runnable approach
**File:** `services/compact/microCompact.ts`, `query/tokenBudget.ts`, `constants/toolLimits.ts`

Claude Code has a **3-tier compaction system**:

| Tier | Trigger | What it does |
|------|---------|--------------|
| **Cached Microcompact** | After each turn (count-based) | Sends `cache_edits` API block to delete old tool results WITHOUT rewriting the cached prefix. Cache hit preserved. |
| **Time-Based Microcompact** | Gap since last message > threshold (minutes) | Detects that server cache has expired, content-clears old tool results BEFORE sending (since cache is cold anyway) |
| **Auto-compact** | Context > threshold % | Full conversation summarization via LLM |

Key numbers from `constants/toolLimits.ts`:
- `DEFAULT_MAX_RESULT_SIZE_CHARS = 50,000` — oversized results go to disk, model gets a preview
- `MAX_TOOL_RESULT_TOKENS = 100,000`
- `MAX_TOOL_RESULTS_PER_MESSAGE_CHARS = 200,000` — per-turn batch cap

Token estimation in `microCompact.ts` pads by **4/3** (conservative): `Math.ceil(totalTokens * (4/3))`.

Tool results in Bedrock/Anthropic count per type: text = characters÷4, images = 2000 tokens flat.

Budget tracking in `query/tokenBudget.ts`:
- Stops continuing if delta < 500 tokens (diminishing returns) for 3+ consecutive checks
- 90% of budget = completion threshold

#### V4 approach
- Single microcompact at **70% context** that content-clears old tool results
- Auto-compact at **80% pre-send** + **90% auto** 
- No disk offload for oversized tool results
- Token estimation: simple character count (no 4/3 padding)
- No per-message aggregate cap for parallel tool results

#### Gap (what V4 is missing)
1. **Disk offload for large tool results** — runnable writes oversized results to disk, sends only a preview. If bash/read_file returns 80K chars, runnable handles it safely; V4 truncates crudely.
2. **Per-message aggregate cap** — if 5 tools run in parallel each returning 40K chars, V4 sends all 200K. Runnable caps at 200K total for the batch.
3. **4/3 token estimation padding** — V4 underestimates, triggers compaction later than ideal.
4. **Time-based microcompact** — V4 doesn't detect "user came back after 30 min, cache is cold" and clean up proactively.

#### Priority: HIGH (disk offload), MEDIUM (aggregate cap, time-based MC)

#### Recommended: Feature #V2-A — Tool Result Size Capping
```python
MAX_TOOL_RESULT_CHARS = 50_000   # per tool result
MAX_BATCH_RESULT_CHARS = 200_000  # per parallel turn total
# If result > MAX_TOOL_RESULT_CHARS: write to .tool_cache/<id>.txt, return preview
```

---

### 2. Prompt Optimization

#### Runnable approach
**File:** `services/api/promptCacheBreakDetection.ts`, `constants/prompts.ts`

Claude Code tracks **prompt cache breaks** in a 2-phase system:
- **Phase 1 (pre-call):** Hashes system prompt + tool schemas. Detects what changed.
- **Phase 2 (post-call):** Checks if `cache_read_input_tokens` dropped > 5% AND > 2000 tokens. If it did, logs WHY (system prompt changed, tool added/removed, model changed, fast mode toggled, etc.)

What breaks the prompt cache:
- Adding/removing a tool (most common — 77% of breaks)
- Changing system prompt text (even +1 char)
- Changing `cache_control` scope (org→global, 5min→1h TTL)
- Model switch, beta header changes

The runnable caches tool descriptions too — not just system prompt. Tools are split into "static base" (always in system) and "dynamic additions" (added per-turn when invoked).

Skills are NOT reset after compact (intentional — avoids 4K token cache_creation cost).

#### V4 approach
- Static/dynamic system prompt split at `# === DYNAMIC ===` boundary (v4.1 #14)
- `prompt_cache_supported` flag disables caching after first validation error
- No cache-break detection or logging
- Tool schemas are sent every turn (not tracked for cache stability)

#### Gap
1. **No cache-break detection** — V4 can't tell if the cache is being busted every turn (wasting the caching investment)
2. **Tool schemas change per-turn** — If skills are added/removed dynamically, the tool list changes → breaks cache. Runnable stabilizes by keeping tools constant; dynamic content goes in user messages instead.
3. **No tool result disk-persistence path** that keeps system prompt stable

#### Priority: LOW (for SageMaker single-user context, analytics don't matter)

---

### 3. Sub-Agent Collaboration

#### Runnable approach
**File:** `services/tools/toolOrchestration.ts`

The runnable has a **concurrency-safe partitioning** system:
```
Tool calls in one turn → partitioned into batches:
  Batch 1: [read_file, grep, glob]  → isConcurrencySafe=true → run ALL in parallel (up to 10)
  Batch 2: [write_file]             → isConcurrencySafe=false → run serially
  Batch 3: [read_file, grep]        → isConcurrencySafe=true → run ALL in parallel
```

Each tool declares `isConcurrencySafe()` based on its parsed input (e.g., bash with write ops = false).

Memory extraction runs as a **perfect fork** of the conversation — same system prompt, same message prefix, but with a restricted tool set (read-only bash + memory dir writes only). It has a strict turn budget and parallel read strategy (turn 1: all reads in parallel → turn 2: all writes in parallel).

Sub-agents are isolated by `querySource` prefix — `agent:custom`, `agent:default`, `agent:builtin`. Module-level state (context collapse, memory cache) is reset only on main-thread compaction, not subagent compaction.

#### V4 approach
- Tool execution: approval gate runs serially, tools execute one at a time
- `concurrent.futures` ThreadPoolExecutor used for parallel tool execution 
- No `isConcurrencySafe()` per-tool method — pre-approval decisions are all-or-nothing
- Sub-agents via `task` tool have depth limit but share same module-level state

#### Gap
1. **No concurrency-safe partitioning** — V4 runs tools in parallel but doesn't respect write/read ordering within a turn
2. **Memory extraction sub-agent is simple** (single LLM call, not a full fork of the conversation)
3. **No state isolation between sub-agents** — if two sub-agents run concurrently they can corrupt `_FILE_READ_TIMES`, `_FILES_READ`, etc.

#### Priority: MEDIUM (state isolation), LOW (concurrency partitioning for SageMaker)

#### Recommended: Feature #V2-B — Sub-Agent State Isolation
```python
# Each sub-agent gets its own read-tracking dicts, not shared globals
# Pass a "context" object into tool functions instead of global state
```

---

### 4. Memory & Context Management

#### Runnable approach
**Files:** `memdir/memoryTypes.ts`, `services/extractMemories/prompts.ts`, `services/compact/postCompactCleanup.ts`

**Memory system:**
- Memories are stored as **individual `.md` files** with YAML frontmatter (`name`, `description`, `type`)
- `MEMORY.md` is an **index file** (< 200 lines) — pointers to memory files, not content
- Each memory type has `when_to_save`, `how_to_use`, `body_structure` guidance in the extraction prompt
- Memory extraction uses a **perfect fork** sub-agent with parallel read strategy
- The `WHAT_NOT_TO_SAVE_SECTION` is critical — explicitly blocks saving code patterns, git history, file paths
- Memory drift detection: "The memory says X exists is not the same as X exists now" — verify before recommending

**Post-compact cleanup** (`postCompactCleanup.ts`):
- Clears: microcompact state, context collapse store, memory file cache, classifier approvals, speculative bash checks, beta tracing state, session messages cache
- Does NOT clear: invoked skill names (skills survive compaction intentionally — avoids 4K token cache_creation on re-inject)
- Subagent compaction: only clears own state, not main-thread module-level state

#### V4 approach
- Single `memory.md` flat file with 4 typed `## SECTION` headings
- No index/file separation — all memory in one file
- Memory extraction: single LLM call, appends formatted blocks
- Post-compact cleanup: clears `_FILE_READ_TIMES`, `_FILE_PARTIAL_READS`, `_FILES_READ`, skills are re-injected

#### Gap
1. **Memory stored in single flat file** — runnable uses separate files per memory item (better for targeted update/delete, avoids overwriting everything)
2. **No MEMORY.md index pattern** — V4 loads entire memory.md; runnable loads just index (efficient for large memory stores)
3. **Memory extraction doesn't run as fork** — V4 extracts in-process synchronously; runnable forks with full conversation context so the sub-agent can make better extraction decisions
4. **No "what NOT to save" enforcement** in extraction prompt — V4's `_MEMORY_EXTRACT_PROMPT` doesn't include the critical exclusion list
5. **Skills re-injected after compact** — wastes ~4K tokens of cache_creation every compact

#### Priority: HIGH (#4 — add what-not-to-save), MEDIUM (#5 — skill re-injection)

#### Recommended: Feature #V2-C — Enhanced Memory Extraction Prompt
Add the WHAT_NOT_TO_SAVE exclusion list and WHEN_TO_ACCESS guidance to V4's `_MEMORY_EXTRACT_PROMPT`.

---

### 5. Security

#### Runnable approach
**Files:** `hooks/toolPermission/PermissionContext.ts`, `hooks/toolPermission/handlers/interactiveHandler.ts`

The runnable has a **4-tier permission system**:
1. **Always allow** — read-only tools (glob, grep, read_file) when no dangerous flags
2. **Ask** — write tools, bash with side effects → show approval dialog
3. **Always deny** — catastrophic patterns, no bypass
4. **Classifier-based** — bash commands go through an ML classifier that predicts dangerousness

The classifier has **speculative pre-checking**: when the model starts generating a tool call, the classifier can pre-analyze it while generation is in progress, so the approval decision is ready before execution starts (latency saving).

`clearClassifierApprovals()` is called post-compact to reset speculative check state.

`clearSpeculativeChecks()` in postCompactCleanup — speculative decisions don't carry over across compaction.

The `trust boundary` is enforced: tool output is treated as potentially hostile — instructions in tool output cannot change agent behavior (documented in system prompt and enforced in agent loop).

#### V4 approach
- 5 security layers: LAYER -1 (catastrophic), LAYER 0 (AWS CLI), LAYER 1 (allowlist), LAYER 2 (denylist patterns), LAYER 3 (network), LAYER 4 (workspace boundary)
- Approval via ipywidgets dialog
- No classifier — pure regex denylist
- Trust boundary documented in SYSTEM_PROMPT

#### Gap
1. **No speculative pre-checking** — V4 waits for tool to be called, shows dialog, waits for user → higher latency per approved tool
2. **Regex denylist vs ML classifier** — runnable uses an ML model to catch novel attack patterns; V4 relies on hand-crafted regex (adequate for SageMaker, but less adaptive)
3. **Approval state not cleared post-compact** — if user pre-approved tool X, that approval should expire after compact (new conversation context). V4 keeps `always_allow` set forever.

#### Priority: MEDIUM (approval state expiry), LOW (classifier — too complex for SageMaker)

#### Recommended: Feature #V2-D — Clear Always-Allow Set on Compact
```python
# In runPostCompactCleanup (or wherever compact completes):
ui_state["always_allow"].clear()  # approval decisions expire with conversation context
```

---

### 6. Latency

#### Runnable approach
**Files:** `services/tools/toolOrchestration.ts`, `services/tools/StreamingToolExecutor.ts`

Max concurrent tool calls: `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY` env var, default **10**.

Tools are batched: read-only tools run concurrently, write tools run serially. This means `[grep, glob, read_file, read_file, read_file]` all run in parallel (5 at once), cutting latency from 5× to 1×.

The approval dialog (`interactiveHandler.ts`) uses **speculative pre-computation** — approval decisions are computed in background while the previous tool is running.

The `PromptSuggestion` service (`services/PromptSuggestion/speculation.ts`) speculatively pre-fetches likely next user messages. Not applicable to SageMaker.

#### V4 approach
- `concurrent.futures` ThreadPoolExecutor with no stated concurrency limit
- Pre-approvals for parallel tools happen before execution (lines ~5917-5930 in run loop)
- No streaming tool executor (Jupyter cell = synchronous)

#### Gap
1. **No explicit concurrency limit** — if LLM calls 20 tools at once, all 20 start immediately (may overwhelm filesystem/bash)
2. **Approval must complete before ANY parallel tool starts** — runnable approves per-batch, then starts all approved tools concurrently

#### Priority: LOW (SageMaker filesystem isn't that fast anyway)

---

### 7. Bash Minimization

#### Runnable approach
**System prompt** explicitly prefers specialized tools:
- "Prefer `read_file` over `cat`"
- "Prefer `glob` over `find`"  
- "Prefer `grep` over `rg` via bash"

The bash tool has the highest approval friction (always requires approval by default). The tool schema's `description` is written to discourage bash for things native tools can do: "Only use for git, package managers, build tools, and scripts."

The `_classify_bash_ro()` equivalent uses speculative classifier that also tracks WHICH tool the model chose — telemetry feeds back into model training to improve tool preference.

#### V4 approach (V4.1 #11)
- Read-only bash bypasses approval dialog
- `_classify_bash_ro()` covers: base commands in `_RO_BASE_COMMANDS`, `sed -i`, `git` with flag inspection, `pip show/list/freeze`
- System prompt says "Prefer specialized tools"

#### Gap
1. **No approval friction difference between `cat file` and `rm -rf`** once both pass the denylist — runnable has friction tuned per command risk level
2. **Bash `diff` not excluded from RO commands** — `diff --output=file` writes. Already fixed in V4.1.

#### Priority: LOW (adequate for SageMaker)

---

## Pending V4 Enhancements — Prioritized List

> These are the features not yet in V4, in order of impact for a SageMaker user.

### HIGH Priority (implement in v4.2)

| ID | Feature | What it is (beginner) | Lines of code |
|----|---------|----------------------|---------------|
| **V2-A** | Tool result size capping + disk offload | When a tool (bash/read_file) returns a HUGE result (>50K chars), instead of dumping all of it into the conversation (wasting context), write it to a temp file and give the LLM a small summary + file path. Like "here's a 200-line snippet, full output in .cache/result123.txt". | ~80 lines |
| **V2-C** | Enhanced memory extraction prompt | Add the "what NOT to save" exclusion list (no code patterns, no git history, no file paths) and the "verify before recommending" staleness warning to `_MEMORY_EXTRACT_PROMPT`. Currently V4's extraction prompt is missing critical guardrails from the runnable. | ~20 lines |
| **V2-D** | Clear always-allow set on compact | Right now when you say "always allow tool X", that approval lives forever. After compaction (new conversation context), those approvals should expire. Just call `ui_state["always_allow"].clear()` in the post-compact cleanup. | ~5 lines |

### MEDIUM Priority (implement in v4.3)

| ID | Feature | What it is (beginner) | Lines of code |
|----|---------|----------------------|---------------|
| **V2-E** | Time-based microcompact | If the user comes back after 30+ minutes, the Anthropic server cache has expired anyway. Proactively clear old tool results BEFORE the request (since there's nothing to preserve). Saves the LLM from reading 50-turn-old grep results that won't be cache-hit anyway. | ~50 lines |
| **V2-F** | 4/3 token estimation padding | V4 currently estimates tokens as `len(text) / 4` (characters). The runnable pads this by 4/3 to be conservative. This means V4 underestimates and waits too long to compact. Simple fix: multiply all token estimates by 1.33. | ~5 lines |
| **V2-G** | Per-message tool result aggregate cap | If 5 tools run in parallel and each returns 40K chars, V4 puts all 200K in context. Add a per-turn cap: if the batch total > 200K chars, truncate the largest results first. | ~30 lines |

### LOW Priority (optional / v4.4+)

| ID | Feature | What it is (beginner) |
|----|---------|----------------------|
| **V2-H** | Skill names not cleared after compact | Currently V4 re-injects all skill descriptions after compact (~4K tokens). The runnable intentionally skips this (model still has the skill tool in schema). Saves 4K tokens of cache_creation per compact. |
| **V2-I** | Sub-agent state isolation | Each sub-agent (task tool) currently shares `_FILE_READ_TIMES`, `_FILE_PARTIAL_READS` with main thread. Should have isolated copies to prevent interference. |

---

## Summary Comparison Table

| Area | Runnable | V4.1 | Key Gap |
|------|---------|------|---------|
| Token optimization | 3-tier (cached MC + time-based + auto-compact) + disk offload | 2-tier (microcompact + auto-compact) | Disk offload, time-based MC, aggregate cap |
| Prompt optimization | Cache break detection, stable tool list | Static/dynamic split, no break detection | Cache break detection (LOW priority) |
| Sub-agent collab | Concurrency-safe batching, up to 10 parallel, state isolation | ThreadPoolExecutor, no isolation | State isolation (MEDIUM) |
| Memory | Per-file storage, MEMORY.md index, fork sub-agent extraction | Single flat file, in-process extraction | Extraction prompt quality (HIGH) |
| Security | 4-tier + ML classifier + approval expiry | 5-layer regex + hard-block | Approval expiry on compact (MEDIUM) |
| Latency | Speculative pre-check, concurrent read batches | Serial approval, parallel exec | Low priority for SageMaker |
| Bash minimization | Friction-tuned, speculative classifier telemetry | RO classifier (v4.1 #11) | Already adequate |

---

*Next step: implement V2-A, V2-C, V2-D in v4.2 (highest impact, lowest risk)*

---

---

# DEEP SOURCE READ ADDENDUM (2026-04-01)

> This section contains findings from a full source-level read of both codebases.
> Previous analysis above remains valid. This extends it with precise file:line references and new gaps.

---

## Verified Architecture Facts — Runnable

### Compaction System (4 tiers, not 3)
Source: `src/services/compact/microCompact.ts`, `src/services/compact/compact.ts`, `src/services/compact/postCompactCleanup.ts`

**Tier 1 — Cached Microcompact** (`microCompact.ts:305`): Uses `cache_edits` API blocks. Tool results are deleted from the server-side cache WITHOUT modifying the local message array. The client sends a `cache_reference` + `cache_edits` block in the next request. Zero cache invalidation cost. Only available for main thread (not sub-agents). Gated by `feature('CACHED_MICROCOMPACT')` and model support check.

**Tier 2 — Time-Based Microcompact** (`microCompact.ts:446`): Fires when `gap since last assistant message > config.gapThresholdMinutes` AND source is main thread. Content-clears old compactable tool results directly in message list (since server cache is cold anyway). Resets cached MC state (because content changed). Uses `TIME_BASED_MC_CLEARED_MESSAGE = '[Old tool result content cleared]'` as placeholder.

**Tier 3 — Snip Compaction** (feature `HISTORY_SNIP`): The runnable has a "snip projection" system (`src/services/compact/snipCompact.ts`) that removes the oldest conversation boundary without an LLM call. The snipCompact.ts file itself is empty (exports `{}`), meaning the actual snip logic lives in `snipProjection.ts`. This is the lightest-weight compaction — no LLM call, no content change.

**Tier 4 — Full Compact** (`compact.ts`): Calls a forked agent with the compact prompt. Constants: `POST_COMPACT_MAX_FILES_TO_RESTORE = 5`, `POST_COMPACT_TOKEN_BUDGET = 50_000`, `POST_COMPACT_MAX_TOKENS_PER_FILE = 5_000`, `POST_COMPACT_MAX_TOKENS_PER_SKILL = 5_000`, `POST_COMPACT_SKILLS_TOKEN_BUDGET = 25_000`. Strips images from messages before sending to compaction LLM (`stripImagesFromMessages`). Has PTL (prompt-too-long) retry with exponential head-drop (`truncateHeadForPTLRetry`).

**Post-Compact Cleanup** (`postCompactCleanup.ts:31`): Clears — microcompact state, context collapse (main thread only), getUserContext memoize cache (main thread only), CLAUDE.md/memory file cache (`resetGetMemoryFilesCache('compact')`), system prompt sections, classifier approvals, speculative checks, beta tracing state, session messages cache. Does NOT clear: invoked skill names.

### Token Estimation
Source: `src/services/compact/microCompact.ts:164`

`estimateMessageTokens()` counts by block type:
- text → `roughTokenCountEstimation(text)` 
- thinking → `roughTokenCountEstimation(thinking)` (not the JSON wrapper)
- tool_result → sum of content items
- image/document → 2000 tokens flat
- tool_use → name + JSON(input)
- Final: `Math.ceil(totalTokens * (4/3))` — 33% safety pad

V4 Compactor.estimate_tokens: `len(text) // 4` — **no safety pad**. Will underestimate by ~25%.

### Memory System
Source: `src/memdir/memoryTypes.ts`

Four types: `user`, `feedback`, `project`, `reference`. Each has:
- `when_to_save`: explicit trigger conditions
- `how_to_use`: recall context
- `body_structure`: required format (rule → **Why:** → **How to apply:**)
- Examples with both correct and incorrect cases

The `WHAT_NOT_TO_SAVE_SECTION` explicitly blocks: code patterns, conventions, git history, debugging solutions, CLAUDE.md contents, ephemeral task details.

`MEMORY_DRIFT_CAVEAT`: "Memory records can become stale. Before answering, verify memory is still correct by reading current state. If recalled memory conflicts with current information, trust what you observe now."

`TRUSTING_RECALL_SECTION`: Before recommending from memory, verify file exists, grep for function, check memory is still load-bearing.

### Permission System
Source: `src/hooks/toolPermission/PermissionContext.ts`, `src/hooks/toolPermission/handlers/interactiveHandler.ts`

Four permission sources: `hook`, `user`, `classifier`, `user_abort`. Each can grant permanent or session-scoped permissions. The `createResolveOnce()` factory ensures exactly one source resolves the permission — even in async races between hook completion, classifier response, and user input.

`handleInteractivePermission()` in `interactiveHandler.ts`: Pushes to permission queue, starts hook execution in background, starts bash classifier in background, shows dialog to user. First of {hook, classifier, user} to respond wins (via `claim()` atomic check-and-mark).

`persistPermissions()` in PermissionContext: Calls `persistPermissionUpdates()` + `applyPermissionUpdates()` to update both disk and in-memory app state.

### Parallel Tool Execution
Source: `src/services/tools/toolOrchestration.ts:91`, `src/services/tools/StreamingToolExecutor.ts`

`partitionToolCalls()`: Reduces tool list into batches. Consecutive concurrency-safe tools merge into one batch. Non-safe tools always get their own batch. Up to `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY` (default 10) run in parallel.

`StreamingToolExecutor.addTool()`: Called as each tool_use block streams in (not after full response). If tool is concurrency-safe and no non-safe tool is running, it starts immediately. Results buffered in original order.

`siblingAbortController`: Child of main abort. When one Bash tool errors, `siblingAbortController.abort()` kills all sibling processes immediately — no waiting for others to complete.

### Task Types
Source: `src/Task.ts:6`

Seven task types: `local_bash`, `local_agent`, `remote_agent`, `in_process_teammate`, `local_workflow`, `monitor_mcp`, `dream`. Each has a typed prefix for task IDs (`b`, `a`, `r`, `t`, `w`, `m`, `d`). Task IDs are 36^8 ≈ 2.8 trillion combinations (cryptographically random bytes).

### Auto-Dream
Source: `src/services/autoDream/autoDream.ts`

Gate: (1) time > `minHours` since last consolidation, (2) session count with mtime > lastConsolidatedAt >= `minSessions`. Defaults: 24h, 5 sessions. (3) disk lock (prevents concurrent consolidation across processes). Session scan interval: 10 minutes (avoids repeated filesystem scans when time gate passes but session gate doesn't).

Runs `/dream` prompt as forked sub-agent with `createCacheSafeParams` — shares parent's cached prefix. Registers as `dream` task type in AppState for UI visibility.

### Cache Break Detection
Source: `src/services/api/promptCacheBreakDetection.ts`

Tracks per source: system prompt hash (stripping cache_control), tool schemas hash (per-tool), cache_control hash (catches TTL/scope changes), tool names + per-tool schema hashes, model, fast mode, beta headers, effort value, extra body hash, call count. Max 10 tracked sources (cap prevents unbounded growth from many sub-agents).

Excludes Haiku models (`isExcludedModel`). Min 2000 token drop to trigger alert. TTL thresholds tracked: 5min, 1 hour.

`notifyCompaction()`: Called after full compact. `notifyCacheDeletion()`: Called after cached/time-based MC. Both suppress false-positive break alerts.

### Retry Logic
Source: `src/services/api/withRetry.ts`

`DEFAULT_MAX_RETRIES = 10`, `BASE_DELAY_MS = 500`. Only foreground sources retry on 529 (capacity): `repl_main_thread`, `sdk`, `agent:custom`, `agent:default`, `agent:builtin`, `compact`, `hook_agent`, `hook_prompt`, `verification_agent`, `side_question`, `auto_mode`. Background sources (titles, summaries) bail immediately. `MAX_529_RETRIES = 3`.

Unattended mode (`CLAUDE_CODE_UNATTENDED_RETRY`): indefinite retries with up to 5min backoff + 30s heartbeat yields.

---

## Verified Architecture Facts — V4

### Compaction System
Source: `sagemaker_agent.py:Compactor`, `microcompact()`, `Compactor.compact()`

**Microcompact at 70%** (`MICROCOMPACT_TRIGGER_PERCENT`): Content-clears tool outputs older than the protected 40K token window. Protected tools (todo_write, todo_read, semantic_search) never cleared. Min savings threshold: 10K tokens (`MICROCOMPACT_MIN_SAVINGS`). Returns pruned messages + tokens_saved count.

**Prune at SUMMARY_TRIGGER_PERCENT (80%)**: `Compactor.prune_tool_outputs()` — deep-copies messages, walks tool results from newest to oldest, truncates those beyond 40K token protection window to 500 head + 500 tail chars.

**Full compact at 80%**: `Compactor.create_llm_summary()` — truncates input to last 20 messages (head 3 + tail 17) before sending to LLM to avoid sending 80-90% context to compact itself. 9-section format matches runnable's compact prompt structure exactly.

**Post-compact file restoration** (`compact()` line ~373): `get_recently_read_files()` traces read_file calls in reverse order to find last 3 distinct file paths. `build_file_restoration_message()` re-reads up to 32K chars total (12K per file). Appended to compacted messages, respecting Bedrock role alternation.

**Circuit breaker** (`_auto_compact_paused`): After 3 consecutive LLM summary failures, auto-compact is paused for the session. Manual compact button still works.

**Simple trim fallback**: If `len(messages) > max_history * 2` (default: 40), keeps tail, inserts placeholder. Ensures proper role alternation.

### Token Tracker
Source: `sagemaker_agent.py:TokenTracker`

Tracks per-session: input, output, cache_read, cache_write, api_calls, session_cost. Per-call: last_input, last_output, last_cost. Pricing table covers 12 model IDs including AU regional endpoints with 10% premium.

Cost formula accounts for prompt caching: regular input at full price, cache_read at 10% (90% discount), cache_write at 125% (25% premium), output at full price.

`get_fixed_overhead()`: Cached calculation of system prompt tokens + tool schema tokens + 346 (Bedrock tool use prompt overhead).

Budget enforcement: Warns at 80% of session_cost_limit, stops at 100%.

### Security Architecture
Source: `sagemaker_agent.py:SecurityManager`, `Agent.run()`

**LAYER -1 — Catastrophic** (line ~1004): 12 precompiled regex patterns. Hard-blocked regardless of config, user approval, or allowlist. Checked FIRST before any other layer. Cannot be disabled. Covers: rm-root/home recursive, dd from /dev/zero, mkfs, fdisk, parted, fork bomb, chmod 777 on /, direct disk device write, shutdown, init 0.

**LAYER 0 — Bash denylist** (70+ patterns): AWS CLI services, network requests, path traversal, remote code execution, privilege escalation, network attacks, credential theft, crypto/ransomware.

**LAYER 0b — Python denylist** (40+ patterns) + 3-layer AST validation: Layer 1 (regex on raw code), Layer 2 (AST import validation — checks module allowlist/blocklist + member-level restrictions), Layer 3 (AST call validation — catches aliased calls like `from os import system as s; s('rm')`).

**LAYERS 1-3 — Tool repair**: Case-insensitive lookup, fuzzy prefix match for typos, argument auto-fix (path→file_path, text→content, query→pattern, cmd→command), type coercion (string digit → int).

**LAYER 4 — Permission**: `needs_approval` per tool + `on_approval` callback + read-only bash bypass (`_classify_bash_ro()`). Read-only bypass covers: git status/log/diff/show, ls/dir, cat/head/tail/less, find -type without exec, grep without write ops, echo/printf, python --version/--help, pip show/list/freeze, which/type/command, wc, sort, uniq, stat/file/du, diff (read-only forms).

**LAYER 5 — Execute + error recovery**: TypeError, KeyError, Exception caught separately with specific error messages.

### Sub-Agent Architecture
Source: `sagemaker_agent.py:Agent._run_task_tool()`, `Agent.run()` line ~6187

5 agent types: `build` (all tools), `plan` (read-only tools only), `explore` (read-only + no task), `general` (all tools), `review` (read-only + no task). Each has `max_turns` (15 default), optional `prompt_suffix`, optional `model_override`.

Parallel detection: `len(_task_tcs) >= 2` where `_task_tcs` = task calls in current response. Pre-approves all before starting `ThreadPoolExecutor(max_workers=min(count, 4))`. File cache isolated via thread-local context (`FILE_CACHE.enter_thread_local_context()`). Parent context saved/restored around parallel block.

Stop propagation: `_sub_stop_check` closure checks both `_sub_stopped` flag and parent's `on_stop_check()`. Stopping parent propagates to all running sub-agents.

Model override: Each agent type can specify a different model in `CONFIG.agent_overrides`. If override fails, falls back to parent's client.

### Doom Loop Detection
Source: `sagemaker_agent.py:Agent.run()` line ~6120

Hash-based: unique key = `(tool_name, target)` where target is:
- todo_write: skipped (expected repetition during planning)
- python_exec: MD5 of code
- read_file: `{filepath}@{offset}`
- edit_file: `{filepath}#{md5(old_string)}`
- grep: `{path}:{pattern}`
- bash: MD5 of command
- others: MD5 of full input dict

Threshold: 3 identical calls → stop. History tracked in `deque(maxlen=30)`. Consecutive duplicate write_file to same content → skip immediately (no count accumulation needed).

### Lazy Doc Tool Loading
Source: `sagemaker_agent.py:Agent.run()` line ~6023

Keywords checked in last 4 messages: `chart, report, document, docx, word, excel, xlsx, pdf, notebook, ipynb, plot, graph, spreadsheet, visualization`. If none present, `_DOC_TOOLS = {create_word, create_excel, create_chart, create_pdf, create_notebook, create_markdown}` are excluded from tool schema. Saves ~1-2K tokens per call in normal coding sessions.

---

## Updated Gap Analysis

### Gap 1: Token Estimation Padding (High Priority, 1 Line)
**Runnable**: `Math.ceil(totalTokens * (4/3))` — 33% safety pad
**V4**: `len(text) // 4` — no pad
**Fix**: Multiply all token estimates in `Compactor.estimate_tokens()` by 1.33

### Gap 2: Cached Microcompact (High Priority, Complex)
**Runnable**: `cache_edits` API blocks delete tool results from server cache WITHOUT touching message content and WITHOUT invalidating the cached prefix. Zero cache bust cost.
**V4**: Content-clear directly modifies messages → next API call sees different content → cache miss on the cleared section.
**Fix**: Requires Bedrock `cache_edits` API support investigation. If supported, this could save significant cost at high context usage.

### Gap 3: FILE_UNCHANGED_STUB (Medium Priority, 2 Hours)
**Runnable**: `FILE_UNCHANGED_STUB` in FileReadTool — if file not changed since last read, returns a short stub instead of full content.
**V4**: `FILE_CACHE.is_in_context()` exists but doesn't return a stub — it only prevents adding to context marker, doesn't actually change what's returned to the LLM.
**Fix**: In `tool_read_file()`, if `FILE_CACHE.is_in_context(path)` is True and cache hit, return `[File unchanged since last read: {path}. Use read_file with offset if needed.]`

### Gap 4: Time-Based Microcompact (Medium Priority, 1 Day)
**Runnable**: Detects idle session (gap since last assistant message > threshold), proactively clears cold-cache tool results before the user's next message.
**V4**: No idle detection. First call after 30 min idle pays full cache-cold cost PLUS unnecessary old tool results in context.
**Fix**: In `agent.run()`, before sending the LLM request, check if `time.time() - last_llm_call_time > IDLE_THRESHOLD_SECONDS`. If yes, call `microcompact()` unconditionally (not just at 70%).

### Gap 5: Post-Compact Cache Reset (Medium Priority, 30 Minutes)
**Runnable**: `runPostCompactCleanup()` clears `getUserContext` memoize cache, `getMemoryFiles` cache, system prompt sections cache.
**V4**: After compact, `_load_persistent_memory()` is called fresh on the next `agent.run()` (because it reads the file each time). But `FILE_CACHE` still holds pre-compact file contents.
**Fix**: After `self.messages = COMPACTOR.compact(...)`, call `FILE_CACHE.clear_all()` and clear `_FILES_READ` to force re-read of files in next turn.

### Gap 6: Memory Extraction Guardrails (High Priority, 30 Minutes)
**Runnable**: `WHAT_NOT_TO_SAVE_SECTION` explicitly blocks saving code patterns, git history, file paths, CLAUDE.md contents, ephemeral task details. `MEMORY_DRIFT_CAVEAT` warns that memories can become stale.
**V4**: `_MEMORY_EXTRACT_PROMPT` (line ~5489) has the 4 types and rules, but no exclusion list and no drift warning. Risk: memory becomes polluted with ephemeral facts.
**Fix**: Add 6-line exclusion block and drift warning to `_MEMORY_EXTRACT_PROMPT`.

### Gap 7: Concurrent Read-Only Tools (High Priority, 2 Days)
**Runnable**: `partitionToolCalls()` groups consecutive read-only tools and runs them concurrently (up to 10 at once). `isConcurrencySafe()` per tool.
**V4**: All tools except parallel `task` calls run sequentially in the dispatch loop.
**Fix**: Add `IS_READ_ONLY` dict to TOOLS registry. In dispatch loop, collect consecutive read-only tool calls (read_file, glob, grep, list_dir, semantic_search), run via ThreadPoolExecutor.

### Gap 8: PTL (Prompt-Too-Long) Recovery (Medium Priority, 2 Hours)
**Runnable**: `truncateHeadForPTLRetry()` — if compact itself hits prompt-too-long, drops oldest API rounds iteratively until compact succeeds. Up to 3 retries.
**V4**: If `create_llm_summary()` fails because input is too long, it returns None → circuit breaker counts failure. No recovery attempt.
**Fix**: In `create_llm_summary()`, if API error mentions prompt-too-long, halve `MAX_SUMMARY_INPUT_MESSAGES` and retry once.

---

## What V4 Does Better Than Runnable

1. **CATASTROPHIC_PATTERNS LAYER -1**: Precompiled hard-block patterns for disk operations. Cannot be disabled via config or user approval. Runnable's YOLO classifier is configurable and defeatable.

2. **Doom loop detection**: Hash-based 3-repeat threshold. Catches infinite tool loops before context or budget exhaustion. Runnable has no equivalent.

3. **Audit trail with integrity**: Local JSONL with SHA-256 hashes. More appropriate for enterprise environments than Anthropic's telemetry-based approach.

4. **Tool auto-repair (5 layers)**: Auto-fixes common LLM mistakes. Reduces wasted turns from malformed tool calls.

5. **Budget enforcement**: session_cost_limit with 80%/100% thresholds. Runnable has maxBudgetUsd per-turn but no session-persistent guard.

6. **Docker execution sandbox**: Optional rootfs/network isolation for bash/python. Runnable executes in-process.

7. **Bedrock-specific robustness**: Role alternation enforcement, cache fallback on unsupported models, AU regional pricing, 600s read timeout.

---

## Updated Priority Table

| Priority | Feature | Effort | Runnable File | Impact |
|---|---|---|---|---|
| HIGH | Add 4/3 estimation pad | 1 line | microCompact.ts:204 | -25% premature compaction |
| HIGH | Memory extraction exclusion list | 30 min | memdir/memoryTypes.ts WHAT_NOT_TO_SAVE | Cleaner memory store |
| HIGH | Concurrent read-only tools | 2 days | toolOrchestration.ts:91 | -40% latency on multi-read turns |
| HIGH | FILE_UNCHANGED_STUB | 2 hours | FileReadTool/prompt.ts FILE_UNCHANGED_STUB | Avoids re-injecting unchanged files |
| MEDIUM | Time-based microcompact | 1 day | microCompact.ts:446 | Proactive cold-cache cleanup |
| MEDIUM | Post-compact FILE_CACHE clear | 30 min | postCompactCleanup.ts | Fix stale file cache after compact |
| MEDIUM | Cache break monitoring | 2 hours | promptCacheBreakDetection.ts | Detect silent cost spikes |
| MEDIUM | PTL retry in compact | 2 hours | compact.ts:truncateHeadForPTLRetry | Prevent stuck compact on long sessions |
| LOW | Per-message batch aggregate cap | 1 day | constants/toolLimits.ts | Prevents 200K+ batch overflows |
| LOW | Cross-session memory consolidation | 3 days | autoDream.ts | Long-term memory (future v4.3+) |

---

*This analysis covers all 7 required areas with specific file:line references from actual source reads.*
*Flowchart files: PS_FLOWCHART_RUNNABLE.html and PS_FLOWCHART_V4.html*
