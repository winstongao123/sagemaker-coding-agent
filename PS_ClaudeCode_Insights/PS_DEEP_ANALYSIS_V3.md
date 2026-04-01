# Claude Code Deep Analysis V3 — Fresh Runnable Audit (2026-04-01)

> Fresh source audit of gg-claude-code-runnable/src/ (1,438 TypeScript files). Focused on patterns NOT covered in V2 analysis or V2-A through V2-J implementations.

---

## 1. Subagent Coordination (NEW — not in V2 analysis)

### Coordinator Mode vs. Worker Delegation

- **File**: `src/coordinator/coordinatorMode.ts` (lines 36-110)
- **What it does**: Two-tier orchestration pattern where a coordinator agent spawns independent worker agents via the AgentTool. The coordinator acts as orchestrator/synthesizer (NOT a task executor). Spawns workers for research, implementation, verification in parallel. Receives `<task-notification>` XML results when workers complete. Decides whether to continue a worker (SendMessage) or spawn fresh based on context overlap.
- **Key**: The coordinator MUST understand findings before directing follow-up work — prevents "play-acting" agent behaviors.
- **V4 status**: NO — V4 has parallel subagents but no coordinator/worker role distinction.
- **Complexity**: High

### SendMessage Tool for Async Continuation

- **File**: `src/tools/SendMessageTool/SendMessageTool.ts` (lines 149-200+)
- **What it does**: Continues a running worker agent by queuing messages into `LocalAgentTask.pendingMessages`. Messages are drained at tool-round boundaries and sent back asynchronously. Avoids spawning new agents when existing context is valuable.
- **V4 status**: No
- **Complexity**: Medium

### LocalAgentTask State Machine

- **File**: `src/tasks/LocalAgentTask/LocalAgentTask.tsx` (lines 116-300)
- **What it does**:
  - Manages background agent lifecycle with `{ status, agentId, prompt, result, progress, ... }`
  - Tracks `pendingMessages` array for SendMessage queueing
  - `isBackgrounded` flag for foreground/background distinction
  - `enqueueAgentNotification()` formats results into `<task-notification>` XML (lines 197-262)
  - `ProgressTracker` with tool counts and recent activities
  - `notified` flag prevents duplicate notifications
- **V4 status**: No
- **Complexity**: High

### Fork Subagent with Prompt Cache Sharing

- **File**: `src/tools/AgentTool/forkSubagent.ts` (lines 32-169)
- **What it does**: When `subagent_type` is omitted, triggers implicit fork where child inherits parent's full conversation context and rendered system prompt bytes. All fork children produce byte-identical API prefixes — maximizes prompt cache hits across fork children.
  - `buildForkedMessages(directive, assistantMessage)`: keeps full assistant message (all tool_uses, thinking, text), builds single user message with placeholder tool_results, appends per-child directive text block
  - `isInForkChild(messages)`: guards against recursive forking
  - Output format requirements: Scope, Result, Key files, Files changed, Issues
- **V4 status**: No — V4 only has explicit typed subagents.
- **Complexity**: High

### Coordinator-Specific Tool Restrictions

- **File**: `src/coordinator/coordinatorMode.ts` (lines 29-34)
- **What it does**: Defines `INTERNAL_WORKER_TOOLS = { TEAM_CREATE, TEAM_DELETE, SEND_MESSAGE, SYNTHETIC_OUTPUT }` — only coordinator can use Team operations, workers cannot.
- **V4 status**: No
- **Complexity**: Low

---

## 2. Prompt Engineering (NEW — critical learning section)

### Coordinator Mode System Prompt (Complete Role Swap)

- **File**: `src/coordinator/coordinatorMode.ts` (lines 111-369)
- **What it does**: Injects a COMPLETELY DIFFERENT system prompt when `isCoordinatorMode()` is true. The prompt:
  - Redefines agent role as "orchestrator" (not executor)
  - Documents AgentTool, SendMessage, TaskStop operations
  - Teaches task workflow phases: Research → Synthesis → Implementation → Verification
  - Emphasizes **parallelism as superpower** (section 4, line 213)
  - Defines worker prompt synthesis requirements (section 5)
  - Provides explicit decision rules for `continue` vs `spawn fresh` (table, lines 284-291)
  - Includes full example session flow (section 6)
- **Key insight**: This is not a tweak — it's a complete role swap. Coordinator and normal modes have incompatible mental models.
- **V4 status**: No
- **Complexity**: High

### System Prompt Assembly with Memoization

- **File**: `src/utils/queryContext.ts` (lines 44-74)
- **What it does**: `fetchSystemPromptParts()` returns `defaultSystemPrompt[]` (array of sections), `userContext`, `systemContext`. When `customSystemPrompt` is set, skips default. Uses `memoize()` from lodash — sections cached per session. System prompts are **decomposed into independent cacheable sections**.
- **V4 status**: Partial — V4 has static/dynamic split but not component-based assembly.
- **Complexity**: Medium

### Memory Directory Prompt Integration

- **File**: `src/memdir/memdir.ts` (lines 111-147)
- **What it does**:
  - `loadMemoryPrompt()`: reads MEMORY.md + subdirs, truncates to **200 lines / 25KB**, injects into system prompt
  - `truncateEntrypointContent()`: line-truncates first, then byte-truncates, appends warning if capped
  - Constants: `MAX_ENTRYPOINT_LINES = 200`, `MAX_ENTRYPOINT_BYTES = 25,000`
  - Memory is integrated as a **system prompt section** (in cache-key prefix), not separate context
- **V4 status**: Partial — V4 caps at 10KB chars, no line limit.
- **Complexity**: Low → **implement in V4.3.0**

### yolo-classifier Prompts

- **File**: `src/yolo-classifier-prompts/` directory
- **What it does**: Defines prompts for auto-classifying bash commands as read-only vs write. These prompts teach the classifier what patterns are safe (git status, cat, ls) vs dangerous (rm, chmod, curl with POST). Used in `useCanUseTool.tsx` for speculative pre-approval.
- **V4 status**: Partial — V4 has static regex classifier, not LLM-based prompt classifier.
- **Complexity**: Medium (but static regex in V4 may be good enough)

---

## 3. Context and Token Management (NEW patterns beyond V2)

### Token Budget with Diminishing Returns

- **File**: `src/query/tokenBudget.ts` (lines 45-93)
- **What it does**: `checkTokenBudget()` returns `{ action: 'continue' | 'stop' }`:
  - `BudgetTracker` state: `{ continuationCount, lastDeltaTokens, lastGlobalTurnTokens, startedAt }`
  - **Diminishing returns detection**: triggers when `continuationCount >= 3` AND `deltaSinceLastCheck < 500` AND `lastDeltaTokens < 500` → stops continuing
  - **Completion threshold**: stops at `turnTokens >= budget * 0.9` (90% utilization)
  - Logs continuation nudge + returns `continuationCount` for analytics
- **V4 status**: Partial — V4 has fixed turn limits, no diminishing-returns detection.
- **Complexity**: Medium → **implement as warning in V4.3.0**

### Cached Microcompact (Prompt Cache Position Pinning)

- **File**: `src/services/compact/microCompact.ts` (lines 52-135)
- **What it does**: Tool result edits are **pinned to message positions** and re-sent to preserve cache line alignment across multiple API calls.
  - `CachedMCState`: tracks pinned cache edits per user message position
  - `consumePendingCacheEdits()`: returns new edits to insert into API request
  - `pinCacheEdits(userMessageIndex, block)`: locks edits to a message position for re-sending on cache misses
  - `getPinnedCacheEdits()`: returns all previously-pinned edits for re-transmission
  - `markToolsSentToAPIState()`: clears "dirty" flag after API call succeeds
  - `resetMicrocompactState()`: clears on snip/compact boundary
- **Key**: Edits are sticky — must be re-sent at EXACT position in subsequent API calls to maintain cache hit.
- **V4 status**: No
- **Complexity**: High

### Time-Based Microcompact keepRecent

- **File**: `src/services/compact/timeBasedMCConfig.ts` (lines 18-43)
- **What it does**: When cold-cache detected, keeps only `keepRecent = 5` most recent tool results (not just clears based on savings threshold). Pre-API triggering.
- **V4 status**: Partial — V4 has 30-min cold-cache detection (V2-E) but uses `KEEP_LAST_N_PER_TOOL=2` globally, not cold-cache-specific keepRecent.
- **Complexity**: Low → **implement keepRecent parameter in V4.3.0**

### Reactive Compact (Wait for PTL Error)

- **File**: `src/services/compact/autoCompact.ts` (lines 189-198)
- **What it does**: When `feature('REACTIVE_COMPACT')` enabled, disables proactive autocompact. Lets API's `prompt_too_long` error trigger reactive compaction. Saves compaction API calls at cost of one wasted call.
- **Tradeoff**: Proactive = safe, Reactive = efficient (fewer LLM calls)
- **V4 status**: No
- **Complexity**: Medium

### Autocompact Buffer Thresholds

- **File**: `src/services/compact/autoCompact.ts` (lines 72-188)
- **What it does**: `calculateTokenWarningState()` returns 5 boolean flags with specific buffer sizes:
  - `isAboveWarningThreshold`: 20K tokens before limit
  - `isAboveErrorThreshold`: 20K tokens before limit (shown to user as error)
  - `isAboveAutoCompactThreshold`: 13K tokens before limit (triggers autocompact)
  - `isAtBlockingLimit`: 3K tokens before limit (manual compact required)
  - `percentLeft`: % of context remaining
- **V4 status**: Partial — V4 has percentage-based thresholds, not absolute buffer sizes.

---

## 4. Memory Management (NEW patterns)

### Auto Memory Extraction with Forked Agent

- **File**: `src/services/extractMemories/extractMemories.ts`
- **What it does**: Runs once per complete query (when model produces final response with no tool calls). Uses `runForkedAgent()` — perfect fork sharing parent's prompt cache. Extracts memories asynchronously without blocking main agent.
  - `isModelVisibleMessage()`: counts only user + assistant messages (not system/progress)
  - `countModelVisibleMessagesSince()`: counts turns since last extraction run
  - `hasMemoryWritesSince()`: checks if agent already wrote to memory files — **if so, skip extraction** (main agent takes priority, fork is skipped)
  - Forked agent permissions: Read/Grep/Glob unrestricted; Edit/Write only to auto-memory dir
- **Key**: The "already wrote" check prevents double-extraction — main agent's explicit writes always win.
- **V4 status**: Partial — V4 doesn't check "already wrote", always extracts.
- **Complexity**: Medium → **implement "already wrote" check in V4.3.0**

### Memory Staleness (memoryAge)

- **File**: `src/memdir/memoryAge.ts`
- **What it does**: Tracks memory file freshness/age. Can deprioritize stale memories or trigger refresh.
- **V4 status**: Unknown — V4 likely doesn't track memory age.
- **Complexity**: Medium

---

## 5. Permission and Hook System

### useCanUseTool with Bash Classifier Integration

- **File**: `src/hooks/useCanUseTool.tsx` (lines 27-150+)
- **What it does**:
  - Unified permission gate with multiple backends: coordinator handler, swarm worker handler, interactive user prompt
  - Bash classifier: `peekSpeculativeClassifierCheck()` → races classifier promise against timeout → if high-confidence match, auto-approves
  - **Speculative checking**: runs classifier in background BEFORE user is prompted, so if classifier is confident, skips the prompt entirely
- **V4 status**: Partial — V4 has static regex RO classifier, not async speculative checking.
- **Complexity**: High (async classifier backend required)

---

## 6. Summary: What to Implement in V4.3.0

| # | Feature | Source File | V4 Action | Priority |
|---|---------|-------------|-----------|----------|
| V3-A | Token budget diminishing returns | `query/tokenBudget.ts` | Add warning at 3+ turns <500 delta | HIGH |
| V3-B | Memory 200-line / 25KB cap | `memdir/memdir.ts` | Change 10KB→25KB + line cap | HIGH |
| V3-C | keepRecent=1 on cold-cache microcompact | `timeBasedMCConfig.ts` | Pass keep_n_override=1 for cold path | MEDIUM |
| V3-D | Auto-memory "already wrote" check | `extractMemories.ts` | Scan messages for memory.md writes | MEDIUM |
| V3-E | Cache indicator (per-turn line) | new | Emit after TOKENS.add() | HIGH |
| V3-F | Cost savings in /cost output | `TokenTracker` | Add cache_savings_usd field | HIGH |
| — | Coordinator Mode | `coordinatorMode.ts` | Future — too complex for V4.3 | FUTURE |
| — | SendMessage + LocalAgentTask | `LocalAgentTask.tsx` | Future — TS-specific pattern | FUTURE |
| — | Cached Microcompact (position pinning) | `microCompact.ts` | Future — high complexity | FUTURE |
| — | Fork Subagent | `forkSubagent.ts` | Future — requires cache byte-identical prefix | FUTURE |
| — | Reactive Compact | `autoCompact.ts` | Future — low value for SageMaker env | FUTURE |

---

## 7. Key Prompt Engineering Lessons from Runnable

1. **Coordinator prompt is a complete role swap** — not a system prompt addition. Two incompatible agent modes: executor vs orchestrator. Lesson: agent role = separate prompt, not just different tools.

2. **Parallelism needs explicit prompt engineering** — section 4 of coordinator prompt says "parallelism is your superpower". Agents won't parallelize unless explicitly told to AND given the mental model for why.

3. **Worker output format is prescribed** — workers are told to return: Scope, Result, Key files, Files changed, Issues. Structured output from workers makes coordinator synthesis reliable.

4. **Memory is a system prompt section** — injected as part of the cached static prefix, so it's always in the model's context window without costing tokens after first turn.

5. **WHAT_NOT_TO_SAVE is as important as WHAT_TO_SAVE** — the extraction prompt explicitly teaches the LLM what NOT to store (code patterns, git history, ephemeral state). Prevents memory bloat.

6. **Tool descriptions are prompt engineering** — how tools are described to the LLM (their names, parameters, descriptions) directly shapes which tools get called and how. Runnable uses very precise tool descriptions.

---

*Analysis date: 2026-04-01. Source: gg-claude-code-runnable/src/ (1,438 TS files), compact_v4/MAIN/agent/sagemaker_agent.py (8,504 lines, v4.2.1). Fresh audit — does not duplicate V2 analysis.*
