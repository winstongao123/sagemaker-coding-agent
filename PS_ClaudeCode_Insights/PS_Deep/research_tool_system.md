# CLAUDE CODE TOOL SYSTEM: Comprehensive Research

## 1. TOOL ARCHITECTURE FOUNDATION

### 1.1 Core Tool Definition (Tool.ts)

**Base Tool Type:** `Tool<Input, Output, P>` interface:
- **Input**: Zod-validated JSON schema for tool parameters
- **Output**: The result data type
- **P**: Progress data type extending `ToolProgressData`

**Critical Tool Methods:**
- `call()` - Executes the tool with validated input
- `checkPermissions()` - Security decision point (returns `PermissionResult`)
- `description()` - Dynamic description based on input
- `prompt()` - Tool documentation for the LLM
- `isConcurrencySafe()` - Can tool run in parallel? (defaults `false`)
- `isReadOnly()` - Does tool modify files/system? (defaults `false`)
- `isDestructive()` - Is operation irreversible? (defaults `false`)
- `toAutoClassifierInput()` - Compact representation for YOLO classifier

**Tool Builder Pattern:** `buildTool()` wraps tool definitions with safe defaults:
- isEnabled: () => true
- isConcurrencySafe: () => false (fail-closed)
- isReadOnly: () => false (fail-closed)
- checkPermissions: () => { behavior: 'allow' }
- toAutoClassifierInput: () => '' (skip classifier by default)

### 1.2 Tool Registration System (tools.ts)

**All 60+ Tools Registered Here:**

Core tools (always available):
- AgentTool, BashTool, FileReadTool, FileEditTool, FileWriteTool
- GlobTool, GrepTool, WebFetchTool, WebSearchTool
- NotebookEditTool, TodoWriteTool, SkillTool
- EnterPlanModeTool, ExitPlanModeV2Tool, AskUserQuestionTool
- TaskOutputTool, TaskStopTool, ToolSearchTool
- ListMcpResourcesTool, ReadMcpResourceTool

**Feature-Gated Tools:**
- REPLTool (USER_TYPE=ant), ConfigTool (Ant-only)
- SleepTool (PROACTIVE/KAIROS), ScheduleCronTool (AGENT_TRIGGERS)
- WebBrowserTool (WEB_BROWSER_TOOL), LSPTool (ENABLE_LSP_TOOL)
- EnterWorktreeTool, ExitWorktreeTool (worktree-enabled)
- WorkflowTool (WORKFLOW_SCRIPTS), TerminalCaptureTool (TERMINAL_PANEL)
- TeamCreateTool, TeamDeleteTool (agent swarms)
- SendMessageTool (coordinator mode), PowerShellTool (Windows)
- SnipTool (HISTORY_SNIP), MonitorTool (MONITOR_TOOL)

**Tool Pool Assembly** (`assembleToolPool`):
1. Get built-in tools via `getTools()` (respects permission filtering)
2. Filter MCP tools by deny rules
3. Deduplicate by name (built-ins take precedence)
4. Sort for prompt cache stability

---

## 2. PERMISSION SYSTEM

### 2.1 Permission Modes

**Five External Modes (user-facing):**
- `acceptEdits` - Auto-approve file edits in working directory
- `bypassPermissions` - Unrestricted access
- `default` - Standard permission checks
- `dontAsk` - Auto-deny on permission prompts
- `plan` - Plan mode (special flow)

**Two Internal Modes:**
- `auto` - YOLO auto-classifier
- `bubble` - Internal mode

### 2.2 Permission Decision Flow

**PermissionResult Union:**
- PermissionAllowDecision: { behavior: 'allow', updatedInput? }
- PermissionAskDecision: { behavior: 'ask', prompt? }
- PermissionDenyDecision: { behavior: 'deny', reason }

### 2.3 Permission Check Pipeline (6 Stages)

1. **Early Denials** - Check blanket deny rules
2. **Rule-Based Permissions** - allow/deny/ask rules with pattern matching
3. **Hook Execution** - PreToolUse hooks (can override)
4. **Classifier Check** - YOLO classifier (auto mode only)
5. **Denial Tracking** - After 5 denials → force 'ask'
6. **User Prompt** - Show permission UI

---

## 3. YOLO AUTO-CLASSIFIER SYSTEM

### 3.1 Two-Stage Classifier

**Stage 1 - "Fast" (max_tokens=64):**
- Immediate decision with stop_sequences
- XML parsing: `<block>yes</block>` or `<block>no</block>`
- ~50ms typical response time

**Stage 2 - "Thinking" (escalation if Stage 1 blocks):**
- Chain-of-thought reasoning (max_tokens=256+)
- Reduces false positives on borderline commands

**Three Modes:** both (default), fast, thinking

### 3.2 Safe Allowlist (Auto-Approved Tools)

Read-only (never classified): FileReadTool, GrepTool, GlobTool, ToolSearchTool
Task/UI: TodoWriteTool, TaskCreateTool, AskUserQuestionTool, EnterPlanModeTool
Swarm: TeamCreateTool, SendMessageTool, WorkflowTool
Other: SleepTool

Bash/PowerShell: ALWAYS classified with semantic rules.

### 3.3 Classifier Prompts

- `auto_mode_system_prompt.txt` - Security boundaries + user rules
- `permissions_external.txt` - User-facing defaults
- `permissions_anthropic.txt` - Ant-internal stricter rules
- Transcript: compact JSON Lines (user text + tool_use blocks only)

---

## 4. TOOL EXECUTION PIPELINE

### 4.1 Per-Tool Call Sequence

1. **Validation** - Zod schema + tool-specific constraints
2. **Permission Check** - Tool-specific security + rules
3. **Pre-Hooks** - User-defined hooks can intercept/modify
4. **Classifier** - YOLO check (auto mode only)
5. **Tool Call** - Execute with ToolUseContext
6. **Post-Hooks** - Validate/transform output
7. **Error Handling** - Recovery suggestions

### 4.2 Large Result Handling

When output exceeds maxResultSizeChars:
1. Write full result to disk: `~/.claude/tool_results/{uuid}`
2. Return preview (~500 chars) to LLM
3. Append file path for reference

Special: FileReadTool has maxResultSizeChars: Infinity

---

## 5. KEY TOOL IMPLEMENTATIONS

### 5.1 BashTool (161KB, most complex)

- Parses command AST (bash syntax)
- Detects destructive operations
- Semantic command matching (e.g., `git *`)
- Subcommand analysis for compound commands
- Image output detection, cd tracking, git attribution

### 5.2 FileEditTool

- File size check (reject >1GB), UNC path rejection
- Team memory secret detection
- Git diff calculation, LSP diagnostic clearing

### 5.3 Tool Search (Deferred Loading)

- 60+ tools would overload token budget
- Mark tools with `shouldDefer: true`
- LLM uses ToolSearchTool to discover tools on demand
- Core tools always loaded, rest deferred

---

## 6. TOOL CONTEXT & INTEGRATION

### 6.1 ToolUseContext provides:
- Commands, Messages, AppState
- getAppState()/setAppState(), requestPrompt()
- handleElicitation(), appendSystemMessage()
- setToolJSX(), addNotification()

### 6.2 MCP Tool Integration
- Registered in appState.mcp.tools
- Built-ins first (cache stability), then sorted MCP
- Permission rules: `mcp__server1` or `mcp__server1__*`

---

## 7. SAFETY & TELEMETRY

### 7.1 Security Philosophy (Fail-Closed)
- isConcurrencySafe: false by default
- isReadOnly: false by default
- Classifier blocks on unparseable responses

### 7.2 Telemetry Events
- tengu_tool_use, tengu_tool_error, tengu_permission_decision
- tengu_auto_mode_outcome, tengu_tool_duration
- All sanitized (no file paths, no env vars)

---

## COMPLETE TOOL LIST (60+)

**Always Available (20):** AgentTool, BashTool, FileReadTool, FileEditTool, FileWriteTool, GlobTool, GrepTool, WebFetchTool, WebSearchTool, NotebookEditTool, TodoWriteTool, ExitPlanModeV2Tool, AskUserQuestionTool, SkillTool, EnterPlanModeTool, BriefTool, TaskOutputTool, TaskStopTool, ListMcpResourcesTool, ReadMcpResourceTool, ToolSearchTool

**Feature-Gated (40+):** REPLTool, ConfigTool, TungstenTool, SleepTool, ScheduleCronTool, RemoteTriggerTool, MonitorTool, SendUserFileTool, PushNotificationTool, SubscribePRTool, WebBrowserTool, LSPTool, EnterWorktreeTool, ExitWorktreeTool, VerifyPlanExecutionTool, WorkflowTool, TerminalCaptureTool, CtxInspectTool, OverflowTestTool, ListPeersTool, TeamCreateTool, TeamDeleteTool, SendMessageTool, PowerShellTool, SnipTool, TestingPermissionTool, TaskCreateTool, TaskGetTool, TaskUpdateTool, TaskListTool, SuggestBackgroundPRTool, MCPTool (dynamic)
