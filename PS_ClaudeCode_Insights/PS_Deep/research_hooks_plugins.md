# CLAUDE CODE HOOKS, PLUGINS, SERVICES & EXTENSION SYSTEMS

## 1. HOOKS SYSTEM (src/hooks/, src/utils/hooks.ts, src/schemas/hooks.ts)

### Architecture
- **executeHooks()** — Main generator function yielding hook messages (3300+ lines)
- **getAllHooks()** ��� Aggregates from 6 sources: user, project, local, managed, plugin, session
- **Hook types:** command, prompt, agent, http, function (in-memory only)

### 25 Hook Events

**Tool/Permission:**
- PreToolUse — Before tool; can approve/deny/ask; modify updatedInput
- PostToolUse — After success; modify updatedMCPToolOutput
- PostToolUseFailure — On tool failure
- PermissionRequest — Before permission prompt; allow/deny with updatedInput
- PermissionDenied — When denied; control retry behavior

**Session Lifecycle:**
- SessionStart — Init; provide initialUserMessage; register watchPaths
- SessionEnd — Cleanup (1500ms timeout default)
- Setup — One-time setup

**User Input:**
- UserPromptSubmit — Before processing; inject additionalContext

**Agents & Tasks:**
- SubagentStart, SubagentStop — Subagent lifecycle
- Stop, StopFailure — Async blocking gate (exit code 2 = blocking)
- TaskCreated, TaskCompleted — Task lifecycle
- TeammateIdle — Teammate inactivity

**File & Config:**
- FileChanged — File modification (requires watchPaths from prior hook)
- CwdChanged — Working directory changes
- ConfigChange, InstructionsLoaded

**Compaction:**
- PreCompact, PostCompact — Before/after transcript compaction

**Other:**
- Notification, Elicitation, ElicitationResult, WorktreeCreate, WorktreeRemove

### 4 Hook Types

1. **Command** (`type: 'command'`) — Shell execution (bash/PowerShell), 10m timeout, exit code 2 = blocking
2. **Prompt** (`type: 'prompt'`) — LLM evaluation via $ARGUMENTS
3. **Agent** (`type: 'agent'`) — Agentic verifier, 60s timeout, Haiku default
4. **HTTP** (`type: 'http'`) — POST to URL with env var interpolation, URL whitelist enforcement

### Hook Input/Output Protocol

**Common Input:**
```json
{
  "session_id": "uuid",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/working/dir",
  "permission_mode": "allow|deny|ask",
  "agent_id": "subagent-uuid",
  "agent_type": "agent-type"
}
```

**JSON Output:**
- continue, stopReason, suppressOutput, decision (approve/block)
- hookSpecificOutput: permissionDecision, updatedInput, updatedMCPToolOutput, additionalContext, initialUserMessage, watchPaths

### Async Hooks
- `async: true` in JSON output → returns immediately
- Tracked in AsyncHookRegistry
- asyncRewake: exit code 2 wakes model via task notification

### Enterprise Controls
- allowManagedHooksOnly — Only managed-settings.json hooks execute
- disableAllHooks — Blocks everything including status line

---

## 2. PLUGINS SYSTEM (src/plugins/, src/services/plugins/)

### Plugin Structure
```typescript
LoadedPlugin = {
  name, manifest, path, source, repository,
  enabled?, isBuiltin?,
  hooksConfig?, mcpServers?, lspServers?,
  commandsPath?, skillsPaths?, agentsPaths?,
  outputStylesPaths?, commandsMetadata?, settings?
}
```

### Plugin Manifest
```json
{
  "name": "plugin-name", "version": "1.0.0",
  "commands": "commands/", "agents": "agents/",
  "skills": "skills/", "hooks": "hooks/hooks.json",
  "outputStyles": "output-styles/",
  "mcpServers": {...}, "lspServers": {...},
  "requirements": ["dependency@marketplace"],
  "permissions": { "allow": [...], "deny": [...] }
}
```

### Plugin Scopes
user (~/.claude/plugins/), project (.claude/plugins/), local (.claude/plugins.local/), dynamic (runtime), enterprise (managed-mcp.json), claudeai (proxy), managed (managed-settings.json)

### Plugin Error Types (24 discriminated union variants)
generic-error, path-not-found, git-auth-failed, git-timeout, network-error, manifest-parse-error, manifest-validation-error, plugin-not-found, marketplace-not-found, marketplace-load-failed, mcp-config-invalid, mcp-server-suppressed-duplicate, lsp-config-invalid, lsp-server-start-failed, lsp-server-crashed, lsp-request-timeout, lsp-request-failed, hook-load-failed, component-load-failed, mcpb-download-failed, mcpb-extract-failed, mcpb-invalid-manifest, marketplace-blocked-by-policy, dependency-unsatisfied, plugin-cache-miss

---

## 3. SERVICES LAYER (src/services/)

### Core Services
- **Analytics** — Event logging, Datadog, GrowthBook feature flags, kill-switch telemetry
- **API** — Claude API client, HTTP retry, file upload, session ingress, usage tracking, overage credit
- **MCP** — 8 transport types (stdio, SSE, HTTP, WebSocket, SDK, IDE, proxy), OAuth + XAA, tool caching
- **LSP** — Language Server Protocol integration
- **Plugins** — Loading, validation, marketplace, MCPB bundles
- **Tools** — Pre/post tool hooks, permission aggregation, blocking errors
- **Compact** — autoCompact, compact, microCompact, reactiveCompact, sessionMemoryCompact

---

## 4. BRIDGE SYSTEM (src/bridge/)

### Purpose
IDE integration + remote session management via WebSocket/HTTP.

### Components
- **BridgeApi** — OAuth-authenticated HTTP to Anthropic servers
- **Bridge Config** — Machine, directory, branch, git URL, capacity
- **Bridge Messaging** — Message queue, work acknowledgment, status updates
- **Session Runner** — Work item processing, output streaming

### Protocol Flow
1. registerBridgeEnvironment() → Get environment_id + secret
2. pollForWork() → Long-poll for IDE requests
3. Process work (run queries, handle permissions)
4. sendPermissionResponse() → Results back to IDE
5. Idempotent re-registration for session resumption

---

## 5. SDK ARCHITECTURE (src/entrypoints/sdk/)

### Public API
```typescript
// Sessions
unstable_v2_createSession(options): SDKSession
unstable_v2_resumeSession(sessionId, options): SDKSession
unstable_v2_prompt(message, options): Promise<SDKResultMessage>

// Queries
query({ prompt, options }): Query
getSessionMessages(sessionId): Promise<SessionMessage[]>
listSessions(): Promise<SDKSessionInfo[]>

// Session Mutations
renameSession, tagSession, forkSession

// MCP Tools
createSdkMcpServer(options): McpSdkServerConfigWithInstance
tool(name, description, inputSchema, handler): SdkMcpToolDefinition
```

### Generated Types
- coreTypes.generated.ts — From Zod schemas via scripts/generate-sdk-types.ts
- Serializable message types, tool definitions, settings types
- runtimeTypes.ts — Non-serializable callbacks, SDKSession interface

---

## 6. COST TRACKING (src/cost-tracker.ts, src/costHook.ts)

### Tracking
- Per-model token counts (input, output, cache read, cache creation)
- USD cost calculation via per-model pricing lookup
- API duration + wall duration + code change LOC
- FPS metrics (optional)

### Persistence
- Saved to .claude/settings.json keyed by lastSessionId
- Restored on session resume via restoreCostStateForSession()
- React hook useCostSummary() for UI display

---

## 7. CONFIGURATION SOURCES (Layered)

### Settings Precedence
1. Command-line arguments
2. Local settings (.claude/settings.local.json)
3. Project settings (.claude/settings.json)
4. User settings (~/.claude/settings.json)
5. Managed settings (admin)

### Hook Sources (6)
userSettings, projectSettings, localSettings, managedSettings, pluginHooks, sessionHooks

### MCP Server Sources
.mcp.json (project), ~/.mcp.json (user), plugin manifests, managed settings, settings.json

---

## 8. SECURITY & TRUST MODEL

- Workspace Trust Dialog required before any hooks/tool execution
- shouldSkipHookDueToTrust() blocks all hooks without trust
- Permission rules: fine-grained allow/deny/ask
- URL whitelisting: allowedHttpHookUrls
- Env var whitelisting: httpHookAllowedEnvVars
- Enterprise: marketplace blocklists/allowlists, managed-hooks-only
- MCP policy: allowedMcpServers/deniedMcpServers
