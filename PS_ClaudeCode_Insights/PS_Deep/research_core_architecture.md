# CLAUDE CODE CORE ARCHITECTURE: Comprehensive Research

## Executive Summary

Claude Code's core architecture is a sophisticated initialization and state management system designed around early-startup optimization, runtime plugin/skill loading, and multi-modal execution contexts (interactive CLI, SDK, remote sessions). The system separates concerns into **bootstrap state**, **context management**, **application state**, and **type definitions**, with careful attention to performance profiling, permission systems, and graceful degradation.

---

## 1. ENTRY POINTS & INITIALIZATION

### 1.1 entry.ts - Bun Bundle Polyfill
**File**: `/src/entry.ts`

**Purpose**: Runtime bootstrap wrapper that registers the `bun:bundle` polyfill before main module loads. This is necessary because `bun:bundle` is compile-time-only in production Bun builds.

**Key Pattern**:
```typescript
plugin({
  name: 'bun-bundle-polyfill',
  setup(build) {
    build.onResolve({ filter: /^bun:bundle$|^bundle$/ }, (args) => {
      return {
        path: import.meta.dir + '/stubs/bun-bundle-runtime.ts',
        namespace: 'file',
      }
    })
  },
})
```

**Key Insight**: Uses Bun's plugin system to intercept and redirect `bun:bundle` imports at runtime, allowing compile-time feature flags to work in production builds.

---

### 1.2 main.tsx - Main Application Bootstrap (4696 lines)
**File**: `/src/main.tsx`

**Purpose**: The primary entry point orchestrating the entire startup sequence. Handles CLI parsing, configuration loading, permission setup, model resolution, plugin initialization, and either launching interactive REPL or headless execution.

**Startup Sequence (Critical Order)**:

1. **Profiling & Parallel Prefetch** (lines 1-34):
   - `profileCheckpoint('main_tsx_entry')` - marks entry for startup metrics
   - `startMdmRawRead()` - launches macOS MDM settings read in parallel (expensive)
   - `startKeychainPrefetch()` - prefetches OAuth + legacy API key from macOS keychain
   - These fire asynchronously while imports continue (~135ms of parallel I/O)

2. **Feature Gating & Conditional Imports** (lines 87-94):
   - Uses `feature('COORDINATOR_MODE')` for dead-code elimination on coordinator mode
   - Uses `feature('KAIROS')` to conditionally load assistant/AI Companion features
   - Lazy-requires via `require()` to avoid circular dependencies

3. **Configuration & Settings Loading**:
   - Applies safe environment variables before trust dialog
   - Loads MDM settings (macOS enterprise management)
   - Initializes policy limits and remote managed settings
   - Applies extra CA certificates for MTLS

4. **Plugin & Skill Initialization**:
   - Loads plugin cache, validates versions, discovers MCP servers
   - Initializes bundled plugins and skills
   - Scans user-specified plugin directories
   - Builds merged tool/command/resource lists

5. **Permission Setup & Model Resolution**:
   - Initializes permission mode (normal/auto/plan/bypass)
   - Parses tool allow/deny lists
   - Validates auto-mode eligibility
   - Resolves main loop model (Opus 4.6 by default)

6. **Analytics & Telemetry Initialization**:
   - Initializes GrowthBook feature flags
   - Sets up OpenTelemetry meters and counters
   - Configures telemetry sinks for metrics collection

7. **Interactive vs. Headless Dispatch**:
   - Interactive: `launchRepl()` → React/Ink terminal UI
   - Headless: `runHeadless()` → single query execution
   - Coordinator mode: special orchestration path

**Design Patterns**:
- **Early-exit guards**: Validates minimal requirements before heavy module loading
- **Lazy imports**: Defers large modules (OpenTelemetry ~400KB) until needed
- **Parallel prefetch**: MDM/keychain reads fire while imports continue
- **Memoization**: Git status, context, user context cached for session stability
- **Feature flags**: Compile-time bundling for dead code elimination

---

### 1.3 entrypoints/ - SDK & Sandbox Integration
**Files**: `/src/entrypoints/*.ts`

#### agentSdkTypes.ts
Defines the **public SDK API** - core types, hook events, and function signatures that SDK consumers use.

**Key Exports**:
- `HOOK_EVENTS` - array of all hook event types (PreToolUse, PostToolUse, SessionStart, etc.)
- `query()`, `unstable_v2_createSession()`, `createSdkMcpServer()` - entry functions (throw if called outside SDK context)
- Hook event type definitions + schemas

#### init.ts - Initialization Pipeline
**Purpose**: Post-config initialization that runs after `main.tsx` validates settings.

**Sequence**:
1. Enable config system & validate settings.json
2. Apply safe environment variables (before trust dialog)
3. Setup graceful shutdown handlers
4. Initialize 1P event logging (OpenTelemetry, async)
5. Populate OAuth account info if needed
6. Detect JetBrains IDE + GitHub repo
7. Configure mTLS + HTTP proxy agents
8. Lazy-load telemetry if needed

---

## 2. BOOTSTRAP STATE MANAGEMENT

### 2.1 bootstrap/state.ts - Global Session State
**File**: `/src/bootstrap/state.ts`

**Purpose**: Single source of truth for mutable session-global state. Accessed via getter/setter functions to allow refactoring.

**Architectural Intent**: "DO NOT ADD MORE STATE HERE - BE JUDICIOUS WITH GLOBAL STATE" (line 31)

**State Categories**:

#### Session Identity
```typescript
sessionId: SessionId                    // UUID, unique per session
parentSessionId: SessionId | undefined  // For session lineage (plan → implementation)
projectRoot: string                     // Stable project root (set once at startup)
originalCwd: string                     // Working directory at start
cwd: string                             // Current working directory (can change)
```

#### Model & Execution Context
```typescript
mainLoopModelOverride: ModelSetting | undefined   // CLI --model flag
initialMainLoopModel: ModelSetting                 // Session's default model
modelUsage: { [modelName: string]: ModelUsage }   // Token/cost tracking per model
kairosActive: boolean                             // Assistant mode enabled
isRemoteMode: boolean                             // --remote flag
mainThreadAgentType: string | undefined           // --agent flag value
```

#### Metrics & Telemetry
```typescript
meter: Meter | null
sessionCounter: AttributedCounter | null          // "claude_code.sessions"
locCounter: AttributedCounter | null              // "claude_code.loc"
costCounter: AttributedCounter | null             // "$"
tokenCounter: AttributedCounter | null            // Tokens
startTime: number                                  // Session start timestamp
totalAPIDuration: number                           // Cumulative API call time
totalToolDuration: number                          // Cumulative tool execution time
turnToolCount: number                              // Tools called this turn
turnToolDurationMs: number                         // Total tool time this turn
```

#### Permission & Policy
```typescript
sessionBypassPermissionsMode: boolean              // Session-only bypass flag
allowedSettingSources: SettingSource[]             // Which config files to read
flagSettingsPath?: string                          // --settings flag
flagSettingsInline?: Record<string, unknown>       // --set CLI overrides
```

#### Plugin & Hook System
```typescript
inlinePlugins: string[]                            // --plugin-dir paths
registeredHooks: Partial<Record<HookEvent, RegisteredHookMatcher[]>> | null
invokedSkills: Map<string, {...}>                  // Skills invoked this session
sessionCronTasks: SessionCronTask[]                // Durable scheduled tasks
```

#### Cache & Optimization
```typescript
cachedClaudeMdContent: string | null              // CLAUDE.md content for auto-mode classifier
promptCache1hAllowlist: string[] | null           // Cache 1h TTL allowlist from GrowthBook
promptCache1hEligible: boolean | null             // User's eligibility (latched)
fastModeHeaderLatched: boolean | null             // Fast mode header sticky-on
afkModeHeaderLatched: boolean | null              // Auto mode header sticky-on
```

---

## 3. CONTEXT MANAGEMENT

### 3.1 context.ts - User & System Context
**File**: `/src/context.ts`

**Purpose**: Provides memoized, session-stable context for the main prompt.

**Key Functions**:

#### getSystemContext()
Memoized function returning prompt-prefix data: gitStatus, cacheBreaker.
- Skipped in CCR (remote mode) for performance
- Git status truncated to 2000 chars max

#### getGitStatus()
Parallelizes 5 git commands: getBranch(), getDefaultBranch(), status --short, log --oneline -n 5, config user.name

#### getUserContext()
Returns CLAUDE.md + injected memory files + git status.

---

## 4. APPLICATION STATE (React/Ink)

### 4.1 state/AppStateStore.ts - UI State Definition
**File**: `/src/state/AppStateStore.ts`

**Large Type**: `AppState` contains:
- Settings & Configuration (mainLoopModel, verbose, etc.)
- UI Layout (expandedView, selectedIPAgentIndex, footerSelection)
- Remote Session (CCR URL, connection status, bridge state)
- Tools & Permissions (toolPermissionContext, agent type)
- MCP & Plugins (clients, tools, commands, resources)
- Tasks & Execution (active tasks, todo lists per agent)
- Thinking & Reasoning (thinkingEnabled, promptSuggestionEnabled)
- Speculation (pipelined generation state)

### 4.2 state/store.ts - Generic Store Pattern
Simple reactive store: getState(), setState(updater), subscribe(listener)

### 4.3 state/onChangeAppState.ts - State Change Side Effects
Hooks into mutations to sync CCR, settings.json, credential caches.

---

## 5. TYPE SYSTEM & SCHEMAS

### 5.1 types/ids.ts - Branded ID Types
Type-safe IDs: SessionId, AgentId with pattern validation.

### 5.2 types/hooks.ts - Hook System Types
HookCallback, HookResult, discriminated union for hook responses.

### 5.3 types/plugin.ts - Plugin System Types
LoadedPlugin, PluginError (discriminated union with specific error types).

### 5.4 schemas/hooks.ts - Hook Configuration Schemas
4 hook types: command (shell), prompt (LLM), http (webhook), agent (agentic verification)

### 5.5 coreTypes.generated.ts - SDK Type Generation
Auto-generated from Zod schemas via scripts/generate-sdk-types.ts.

---

## 6. CONSTANTS & CONFIGURATION

### 6.1 constants/common.ts
Session date memoization for prompt-cache stability.

### 6.2 constants/system.ts
System prompt prefix (CLI vs SDK vs pure agent), attribution header with version + fingerprint.

---

## 7. SETUP & SESSION INITIALIZATION

### 7.1 setup.ts
Post-bootstrap: Node.js version check, UDS messaging server, terminal restoration, git config, hooks loading, worktree management, project config, SessionStart hooks.

---

## 8. KEY DESIGN PATTERNS

1. **Memoization for Cache Stability** — git status, dates, CLAUDE.md
2. **Parallel Prefetch** — MDM/keychain reads overlap module loading
3. **Bootstrap Isolation** — getter/setter pattern limits global state
4. **Feature Flag Dead-Code Elimination** — Bun compiler removes unused branches
5. **AppState → CCR Sync** — single choke point for external sync
6. **Lazy Error Dialogs** — React only loaded if settings invalid

---

## 9. CRITICAL INITIALIZATION ORDER

1. Profiling checkpoints BEFORE heavy imports
2. MDM/keychain prefetch BEFORE trust dialog
3. Graceful shutdown BEFORE async work
4. Safe env vars BEFORE TLS handshakes
5. Settings loading BEFORE permission mode
6. Trust dialog AFTER settings
7. Telemetry AFTER trust
8. Plugin loading AFTER telemetry
9. REPL launch AFTER context ready

---

## 10. MODULE SUMMARY TABLE

| Module | Purpose | Key Exports |
|--------|---------|------------|
| **entry.ts** | Bun bundle polyfill | Plugin registration |
| **main.tsx** | CLI bootstrap (4696 lines) | Startup orchestration |
| **bootstrap/state.ts** | Global session state | getSessionId(), setCwd() |
| **context.ts** | Memoized prompt context | getSystemContext(), getGitStatus() |
| **state/AppStateStore.ts** | React UI state type | AppState |
| **state/store.ts** | Immutable store pattern | createStore<T>() |
| **types/ids.ts** | Branded ID types | SessionId, AgentId |
| **types/hooks.ts** | Hook system types | HookCallback, HookResult |
| **types/plugin.ts** | Plugin system types | LoadedPlugin, PluginError |
| **schemas/hooks.ts** | Hook config schemas | HookCommandSchema |
| **entrypoints/init.ts** | Post-config init | init() |
| **entrypoints/agentSdkTypes.ts** | SDK public API | query(), tool() |
| **setup.ts** | Session setup | setup() |
| **constants/system.ts** | System prompt + attribution | getCLISyspromptPrefix() |
