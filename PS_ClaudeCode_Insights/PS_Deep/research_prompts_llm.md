# CLAUDE CODE SYSTEM PROMPTS & PROMPT ENGINEERING

## 1. SYSTEM PROMPT ARCHITECTURE

### 1.1 Core Prefix Selection (src/constants/system.ts)
- `DEFAULT_PREFIX`: "You are Claude Code, Anthropic's official CLI for Claude."
- `AGENT_SDK_CLAUDE_CODE_PRESET_PREFIX`: For non-interactive Agent SDK
- `AGENT_SDK_PREFIX`: For pure agent context
- Dynamic routing via getCLISyspromptPrefix() based on API provider + session type

### 1.2 Section System (src/constants/systemPromptSections.ts)
- `systemPromptSection(name, compute)` — Memoized, cached until /clear or /compact
- `DANGEROUS_uncachedSystemPromptSection(name, compute, reason)` — Recomputes every turn, breaks prompt cache
- All sections resolved via resolveSystemPromptSections() in parallel

### 1.3 Prompt Building Priority (src/utils/systemPrompt.ts)
1. Override System Prompt (loop mode) — REPLACES all
2. Coordinator System Prompt (CLAUDE_CODE_COORDINATOR_MODE)
3. Agent System Prompt (mainThreadAgentDefinition)
4. Custom System Prompt (--system-prompt flag)
5. Default System Prompt
Plus: appendSystemPrompt always added at end

---

## 2. MAIN SYSTEM PROMPT ASSEMBLY (src/constants/prompts.ts)

### Static Sections
- getSimpleIntroSection() — "You are an interactive agent..."
- getSimpleSystemSection() — "All text output displayed to user..."
- getSimpleDoingTasksSection() — Code writing instructions
- getSimpleToolsSection() — How to use tools
- getHooksSection() — User-defined hooks
- getSystemRemindersSection() — <system-reminder> tags info

### Dynamic Sections
- Memory system (if enabled)
- Language preference
- Output style
- MCP instructions (connected servers)
- Tool availability
- Model information
- Session context

### Cache Boundary
```
SYSTEM_PROMPT_DYNAMIC_BOUNDARY = '__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__'
```
- BEFORE boundary: scope='global' (cross-user cacheable)
- AFTER boundary: scope='org' or no cache

---

## 3. COORDINATOR MODE PROMPT (src/coordinator/coordinatorMode.ts)

Replaces standard prompt when CLAUDE_CODE_COORDINATOR_MODE=1:
- Role: Orchestrate tasks across workers
- Tools: Agent (spawn), SendMessage (continue), TaskStop
- Workflow: Research → Synthesis → Implementation → Verification
- Key rule: "Parallelism is your superpower"
- Workers receive <task-notification> XML blocks as user-role messages

**Critical Prompt Engineering:**
- "Workers can't see your conversation — every prompt is self-contained"
- "Never write 'based on your findings' — do synthesis yourself"
- "Prove you understood by including specific file paths, line numbers"

---

## 4. TOOL PROMPT DESCRIPTIONS (src/tools/[Tool]/prompt.ts)

40+ tools each with detailed prompt.ts:

**BashTool** (200+ lines): Bash execution, git operations, PR creation, safety rules, cross-references to specialized tools, CRITICAL protocol sections

**AgentTool**: How to spawn subagents, "brief like colleague who just walked in", fork vs spawn decision matrix, execution examples

**FileReadTool, FileEditTool, FileWriteTool**: Usage constraints, file size limits, "read before edit" rule

**GlobTool, GrepTool**: Search patterns, when to use each, ripgrep syntax

**WebFetchTool, WebSearchTool**: URL handling, content extraction

**ToolSearchTool**: Deferred tool loading, how to discover tools

---

## 5. COMPACTION PROMPTS (src/services/compact/prompt.ts)

### Full Compact Summary Sections
1. Primary Request and Intent
2. Key Technical Concepts
3. Files and Code Sections (with snippets)
4. Errors and Fixes
5. Problem Solving
6. All User Messages (critical)
7. Pending Tasks
8. Current Work (very detailed for resumption)
9. Optional Next Step

**Key Rule:** NO_TOOLS_PREAMBLE — "Respond with TEXT ONLY. Tool calls REJECTED."

### Memory Extraction (src/services/extractMemories/prompts.ts)
- Runs as "perfect fork" with same system prompt
- Turn 1: All File Reads in parallel
- Turn 2: All Write/Edit in parallel
- Four-type taxonomy with private/team scoping

### Session Memory (src/services/SessionMemory/prompts.ts)
Template sections: Title, Current State, Task Spec, Files/Functions, Workflow, Errors, Codebase Docs, Learnings, Key Results, Worklog
- Per-section: ~2000 tokens, Total: ~12000 tokens

### Magic Docs (src/services/MagicDocs/prompts.ts)
"BE TERSE. High signal only." — Architecture, patterns, gotchas, NOT exhaustive lists

---

## 6. YOLO CLASSIFIER PROMPTS (src/utils/permissions/yolo-classifier-prompts/)

### Templates
- `auto_mode_system_prompt.txt` — Core classifier prompt
- `permissions_external.txt` — User-facing defaults
- `permissions_anthropic.txt` — Ant-internal stricter rules

### Template Substitution
- `<user_allow_rules_to_replace>` — Auto-approve actions
- `<user_deny_rules_to_replace>` — Require confirmation
- `<user_environment_to_replace>` — User context

### Auto Mode Critique (src/cli/handlers/autoMode.ts)
Evaluates user rules for: Clarity, Completeness, Conflicts, Actionability

---

## 7. PROMPT CACHING & API (src/services/api/claude.ts)

### buildSystemPromptBlocks()
Returns TextBlockParam[] with cache_control metadata:
- Before boundary: scope='global' (cross-org)
- After boundary: scope='org'
- getCacheControl() determines scope from querySource

### API Request Assembly
```typescript
system = buildSystemPromptBlocks(systemPrompt, enablePromptCaching)
messages = MessageParam[] (user/assistant/tool_result)
tools = BetaToolUnion[] (with cache_control for deferred tools)
```

### Streaming
Content block start/delta/stop events, usage tracking, tool use streaming, VCR recording

---

## 8. TOKEN MANAGEMENT

- `tokenCountFromLastAPIResponse()` — Actual from API
- `tokenCountWithEstimation()` — Estimate when unavailable
- `roughTokenCountEstimation()` — ~1 token per 4 chars
- Context management: auto-compact when approaching limit

---

## 9. MODEL SELECTION

### Constants
- Frontier: Claude Opus 4.6
- Models: opus (claude-opus-4-6), sonnet (claude-sonnet-4-6), haiku (claude-haiku-4-5-20251001)

### Routing
- Main loop: getDefaultOpusModel() or from CLI/settings
- Quick tasks: getSmallFastModel() → Haiku
- Classifier: Side query, separate from main loop budget

---

## 10. HIDDEN MOAT: PROMPT ENGINEERING TECHNIQUES

1. **Modular Sections** — Cacheable, cleared on /compact, parallel resolution
2. **Synthesization Protocol** — Parent proves understanding before delegating
3. **Tool Precision** — 40+ descriptions prevent wrong-tool misuse
4. **Context Continuity** — Auto-compaction + session memory
5. **Cache-First Design** — Boundary splits global/dynamic, amortized first-turn cost
6. **Behavioral Guardrails** — No-tool preambles, don't-peek, no fabrication
7. **Adaptive Routing** — Coordinator/proactive/output styles swap prompts
8. **Isolation by Design** — Worker prompts self-contained, parallel-safe
9. **Unlimited Context** — Seamless compaction transparent to user

### Buddy/Companion (src/buddy/prompt.ts)
Injects companion intro: "A small [species] named [name] sits beside input box..."
One-line-or-less response when user addresses companion directly.

### Feature Flag Conditional Prompts
PROACTIVE, KAIROS, COORDINATOR_MODE, TEAMMATE, BUDDY, TRANSCRIPT_CLASSIFIER — bundler removes unreachable branches.
