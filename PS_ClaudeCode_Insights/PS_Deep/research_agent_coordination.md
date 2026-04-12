# CLAUDE CODE AGENT SYSTEM & COORDINATION ARCHITECTURE

## EXECUTIVE SUMMARY

Multi-layered agent orchestration supporting:
1. **Coordinator Mode** — Multi-agent orchestration (coordinator spawns/manages workers)
2. **Fork Subagent** — Background agents inheriting full parent context
3. **In-Process Teammates** — AsyncLocalStorage-isolated agents in same process
4. **Remote Agents** — Background agents in remote CCR environments
5. **Dream Tasks** — Auto-memory consolidation agents
6. **Swarm Teams** — Multi-agent teams with tmux/iTerm2/in-process coordination

---

## 1. COORDINATOR MODE (src/coordinator/coordinatorMode.ts)

### Architecture
- NOT a special agent — main Claude Code session running in coordinator mode
- Workers execute autonomously, notify via `<task-notification>` XML messages
- Feature-gated: `CLAUDE_CODE_COORDINATOR_MODE` env var

### System Prompt (400+ lines)
- Direct workers to research, implement, verify
- Synthesize findings before delegating follow-up
- Tools: Agent (spawn), SendMessage (continue), TaskStop (kill)
- Key: "Parallelism is your superpower"
- Critical: "Workers can't see your conversation — every prompt self-contained"
- Anti-pattern: "Never write 'based on your findings' — do synthesis yourself"

### Worker Tool Restrictions
- Workers get full ASYNC_AGENT_ALLOWED_TOOLS minus internal tools
- Internal only: TeamCreate, TeamDelete, SendMessage, SyntheticOutput
- --simple mode: restricted to Bash, Read, Edit only
- Can access MCP tools from configured servers

### Task Notification Format
```xml
<task-notification>
  <task-id>{agentId}</task-id>
  <status>completed|failed|killed</status>
  <summary>{human-readable}</summary>
  <result>{agent's final response}</result>
  <usage><total_tokens>N</total_tokens><tool_uses>N</tool_uses><duration_ms>N</duration_ms></usage>
</task-notification>
```

---

## 2. TASK MANAGEMENT SYSTEM (src/Task.ts, src/tasks/)

### 7 Task Types
| Type | Prefix | Description |
|------|--------|------------|
| local_bash | b | Shell commands via BashTool |
| local_agent | a | Worker agents (local execution) |
| remote_agent | r | Remote CCR agents (background) |
| in_process_teammate | t | Same-process agents (team) |
| local_workflow | w | Workflow automation |
| monitor_mcp | m | MCP server monitoring |
| dream | d | Auto-memory consolidation |

### Task Lifecycle
Status: pending → running → completed | failed | killed

### Task ID Generation
- Format: {prefix}{8-char-random} (36^8 ≈ 2.8 trillion combinations)
- Cryptographic randomBytes (resists brute-force symlink attacks)

### Base Task State
```typescript
{
  id, type, status, description,
  toolUseId?, startTime, endTime?,
  outputFile, outputOffset, notified
}
```

---

## 3. LOCAL AGENT TASK (src/tasks/LocalAgentTask/)

### State
```typescript
LocalAgentTaskState = TaskStateBase & {
  agentId, prompt, selectedAgent?, agentType, model?,
  abortController?, error?, result?, progress?,
  messages? (capped 50), isBackgrounded, pendingMessages[],
  retain, diskLoaded, evictAfter?
}
```

### Progress Tracking
```typescript
AgentProgress = {
  toolUseCount, tokenCount,
  lastActivity?: ToolActivity,
  recentActivities? (max 5)
}
```

### Lifecycle
1. registerAsyncAgent(agentId, taskState) → creates in AppState
2. updateAsyncAgentProgress(taskId, progress) → UI re-render
3. completeAsyncAgent / failAsyncAgent / killAsyncAgent → terminal
4. enqueueAgentNotification → model notification

### Message Queueing
- queuePendingMessage(taskId, message) — mid-turn follow-ups queued
- drainPendingMessages(taskId) — delivered at tool-round boundary

---

## 4. IN-PROCESS TEAMMATE TASK (src/tasks/InProcessTeammateTask/)

### Purpose
Same-process agents with AsyncLocalStorage isolation, mailbox communication, leader permission control.

### State
```typescript
InProcessTeammateTaskState = TaskStateBase & {
  identity: TeammateIdentity {
    agentId, agentName, teamName, color?,
    planModeRequired, parentSessionId
  },
  prompt, model?, selectedAgent?,
  awaitingPlanApproval, permissionMode,
  messages? (CAPPED at 50), pendingUserMessages[],
  isIdle, shutdownRequested, onIdleCallbacks?[]
}
```

### Memory Capping
TEAMMATE_MESSAGES_UI_CAP = 50 (BQ analysis: 20MB RSS per agent @ 500 turns)

### Permission Flow (Leader ↔ Teammate)
1. Teammate calls hasPermissionsToUseTool() → allow/deny/ask
2. For 'ask': try bash classifier first
3. If still 'ask': show leader's ToolUseConfirm dialog with worker badge
4. Fallback: mailbox-based requests (500ms polling)

---

## 5. REMOTE AGENT TASK (src/tasks/RemoteAgentTask/)

### Types
remote-agent, ultraplan, ultrareview, autofix-pr, background-pr

### State includes:
sessionId, command, title, todoList, log (SDKMessage[]), isLongRunning?, pollStartedAt, reviewProgress?

### Polling
pollRemoteSessionEvents() → subscribes to remote session event stream
registerCompletionChecker(type, checker) → custom completion logic

---

## 6. DREAM TASK (src/tasks/DreamTask/) — Auto-Memory Consolidation

### State
```typescript
DreamTaskState = TaskStateBase & {
  phase: 'starting' | 'updating',
  sessionsReviewing: number,
  filesTouched: string[],
  turns: DreamTurn[] (max 30),
  priorMtime
}
```

### Lifecycle
registerDreamTask → addDreamTurn → completeDreamTask | failDreamTask
Kill rewinds consolidation lock. UI-only notification (no model-facing).

---

## 7. AGENT TOOL & WORKER SPAWNING (src/tools/AgentTool/)

### Input Schema
```typescript
{
  description, prompt, subagent_type?, model?,
  run_in_background?, name?, team_name?,
  mode?, isolation? ('worktree' | 'remote'), cwd?
}
```

### Agent Types
- Built-in: GENERAL_PURPOSE_AGENT, FORK_AGENT
- Custom: from .claude/agents/ or ./.agents/
- Agent definition: YAML frontmatter + markdown prompt

### Async Lifecycle
1. Spawn: registerAsyncAgent → LocalAgentTaskState
2. Execute: runAgent() generator (tool calls, message recording, progress)
3. Track: updateAsyncAgentProgress
4. Complete: completeAsyncAgent / failAsyncAgent / killAsyncAgent

---

## 8. FORK SUBAGENT MODE (src/tools/AgentTool/forkSubagent.ts)

### When Triggered
- Feature gate FORK_SUBAGENT
- NOT coordinator mode, NOT non-interactive
- Omitting subagent_type triggers implicit fork

### The Fork Process
1. **buildForkedMessages()** — Full parent conversation passed to child
   - Identical FORK_PLACEHOLDER_RESULT for all tool_use blocks
   - Maximizes prompt cache hits (identical prefix)
2. **buildChildMessage()** — 10 non-negotiable rules injected
   - No recursive forking, no conversation, use tools directly
   - Output format: Scope, Result, Key files, Files changed, Issues
3. **isInForkChild()** — Detects FORK_BOILERPLATE_TAG to prevent recursion

### Properties
- System prompt: inherited from parent (byte-exact)
- Tools: parent's exact pool (cache-identical)
- Model: inherited
- Permission mode: 'bubble' (surfaces to parent terminal)
- Always async (task notification only)

---

## 9. SEND MESSAGE TOOL (src/tools/SendMessageTool/)

### Routing Mechanisms
1. **Local Agents**: queuePendingMessage → resumeAgentBackground
2. **In-Process Teammates**: writeToMailbox(identity, message) → 500ms polling
3. **Broadcast ("*")**: Send to all teammates
4. **Remote/Bridge Peers**: Route via IPC socket (UDS_INBOX feature)

### Structured Messages
- shutdown_request, shutdown_response, plan_approval_response

---

## 10. TEAM CREATION & SWARM (src/tools/TeamCreateTool/, src/tools/shared/spawnMultiAgent.ts)

### Concepts
- **Leader**: Main Claude Code session
- **Teammates**: Sub-agents spawned with team context
- **Team File**: ~/.claude/teams/{name}.json (persistent)

### Team File Structure
```typescript
{
  name, description?, createdAt,
  leadAgentId, leadSessionId,
  members: TeamMember[],
  subscribers?: string[]
}
```

### Spawning Backends
- **tmux**: Terminal multiplexing (multiple panes)
- **iTerm2**: Native macOS split panes
- **in-process**: Same-process agents (default fallback)

### spawnTeammate() Flow
1. Detect backend (tmux/iTerm2/in-process)
2. If in-process: spawnInProcessTeammate() with AsyncLocalStorage isolation
3. If tmux/pane: spawn CLI in new pane with env vars
4. Update team file, assign color, return SpawnOutput

---

## 11. IN-PROCESS RUNNER (src/utils/swarm/inProcessRunner.ts)

### AsyncLocalStorage Isolation
```typescript
runWithTeammateContext(identity, fn)
// All tool calls within fn see TeammateContext via getTeammateContext()
// Flows to: MCP access, permission decisions, mailbox routes
```

### Idle Notification
onIdleCallbacks: Leader registers callback → triggered when teammate becomes idle

---

## 12. BUDDY SYSTEM (src/buddy/)

### Companion (Perch)
- Small dragon beside input box, occasionally comments
- **Deterministic generation**: Seeded RNG from hash(userId)
- **Companion Bones**: species, eye, hat, stats (from hash)
- **Companion Soul**: name, personality (persisted in config)
- **18 species**: duck, goose, blob, cat, dragon, octopus, owl, penguin, turtle, snail, ghost, axolotl, capybara, cactus, robot, rabbit, mushroom, chonk
- **Rarities**: common (60%), uncommon (25%), rare (10%), epic (4%), legendary (1%)

---

## 13. CONCURRENCY PATTERNS

### Parallel Agent Spawning
- Coordinator spawns multiple workers in single turn (multiple Agent() calls)
- Each returns immediately with async_launched + task_id
- Tasks run concurrently, notifications arrive asynchronously

### Message Queueing at Boundaries
- Mid-turn follow-ups queued (not sent immediately)
- Drained at tool-round boundary (all API messages received)

### Abort Mechanisms
- Kill entire agent: abortController.abort()
- Abort current turn only: currentWorkAbortController.abort() (teammates)
- Teammate loop catches abort, waits for new work

### In-Process Polling
readMailbox(identity) every 500ms — non-blocking, teammate continues generating

---

## 14. AGENT MEMORY & CONTEXT

### Disk Persistence
Each agent writes transcript to: ~/.claude/agents/{agentId}/transcript.jsonl
On resume: sidechain merged into messages (UUID-deduplicated)

### Fork Context Inheritance
Full parent conversation + system prompt + tool pool (all byte-exact for cache hits)

### Scratch Pad (Cross-Worker)
Feature gate: tengu_scratch. Workers read/write shared knowledge. No permission prompts.

---

## 15. ARCHITECTURE DIAGRAM

```
┌─── Main Session (Leader/Coordinator) ──────────────────────────┐
│  AppStateStore: tasks{}, agentNameRegistry, teamContext        │
│  Tools: AgentTool, SendMessage, TaskStop, TeamCreate/Delete    │
└────────────┬──────────────┬──────────────┬────────────────────┘
             │              │              │
    ┌────────▼────────┐ ┌──▼──────────┐ ┌▼───���─────────────┐
    │  Local Agent     │ │ In-Process   │ │  Remote Agent     │
    │  (background)    │ │ Teammate     │ │  (CCR cloud)      │
    │  registerAsync   │ │ AsyncLocal   │ │  pollRemote       │
    │  taskNotify      │ │ mailbox      │ │  sessionEvents    │
    └─────────────────┘ │ permission   │ └──────────────────┘
                        │ idle notify  │
                        └──────────────┘
    ┌─────────────────┐ ┌──────────────┐
    │  Fork Subagent   │ │  Dream Task  │
    │  full parent ctx │ │  memory      │
    │  cache-identical │ │  consolidate │
    └─────────────────┘ └──────────────┘
```
