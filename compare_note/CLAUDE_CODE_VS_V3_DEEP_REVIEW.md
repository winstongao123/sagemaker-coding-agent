# Deep Review: Claude Code vs compact_v3 → v4 Upgrade Plan

> Source compared:
> - Claude Code (leaked source): `compare_code/gg-claude-code-runnable/src/`
> - compact_v3: `compact_v3/MAIN/agent/sagemaker_agent.py`
> - Date: 2026-04-01

---

## SECTION 1: SYSTEM PROMPT & CONTEXT MANAGEMENT

### Claude Code: Multi-layer, cache-optimised

**Architecture**: Modular sections with API-level prompt caching

1. **Static cacheable prefix** — tool rules, actions, tone, style (marked `scope: global`)
2. **Dynamic boundary marker** (`SYSTEM_PROMPT_DYNAMIC_BOUNDARY`) — separates cached from per-session
3. **Dynamic content** — memory, environment, skills, MCP instructions, token budget
4. **Memoized sections** — `systemPromptSection()` caches each section independently until `/clear`
5. **Dangerous sections** — `DANGEROUS_uncachedSystemPromptSection()` recomputes every turn

**Key win**: First message processes full system prompt (~32K tokens). Subsequent messages only process the dynamic portion (~1-3K tokens). 90%+ reduction in input tokens per turn.

### compact_v3: Monolithic string

- Single `SYSTEM_PROMPT` variable (~120 tokens)
- Simple string concatenation for plan mode + skills
- No API-level caching boundary
- Every message includes full system prompt from scratch

### v4 Action: Add prompt cache boundary
Split system prompt into:
```python
SYSTEM_PROMPT_STATIC = "..."    # Mark for cache (rules, tools, security)
SYSTEM_PROMPT_DYNAMIC = "..."   # Per-session (memory, skills, env)
```
On Bedrock: use `cachePoint` in message structure.

---

## SECTION 2: TOKEN MANAGEMENT & COMPACTION

### Claude Code: Sophisticated 3-stage pipeline

**Stage 1: Microcompact (mid-stream)**
- Replaces old tool results with `[Old tool result content cleared]` marker
- Only applies to COMPACTABLE_TOOLS (file read, bash, grep, web fetch)
- Never removes tool outputs that affect current decisions
- `cachedMCState` + `pinnedEdits` persist across API calls

**Stage 2: Auto-compact threshold**
- Triggers at: `effective_context_window - 13K buffer` (~75% for 200K window)
- Reserves 20K tokens for the LLM's compaction output itself
- Circuit breaker: `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3`

**Stage 3: Post-compact file restoration**
- Re-injects top 5 recently-read files after compaction
- Budget: 50K total, 5K per file, 25K for skills
- Prevents agent from losing file context after compact

**Token counting**:
- Uses real API `usage` data as primary source
- Falls back to 4 chars/token estimation
- Correctly handles parallel tool calls (walks back to first sibling message)
- Excludes cache tokens from context window calculation

### compact_v3: Simple 2-stage prune + summarize

**Stage 1: Prune**
- Keeps last 40K tokens of tool outputs
- Protected tools never pruned: `todo_write`, `todo_read`, `semantic_search`
- Only prunes if savings >= 10K tokens
- Trigger: 80% context

**Stage 2: Summarize**
- 9-section LLM summary (Intent, Concepts, Files, Errors, etc.)
- Keeps summary + last 3 messages
- Max 20 messages sent to LLM to avoid bloat

**Gap**: No microcompact, no post-compact file restoration, no circuit breaker.

### v4 Actions
1. Add microcompact: replace old tool outputs with markers when context > 70%
2. Add circuit breaker: stop retrying compact after 3 failures
3. Post-compact: re-inject last 3 read files into context
4. Real token count from API response when available

---

## SECTION 3: TOOLS — GAPS AND ENHANCEMENTS

### What Claude Code has that compact_v3 doesn't

| Tool | What it does | v4 Priority |
|---|---|---|
| `BriefTool` | Smart context compaction on demand | High |
| `EnterPlanMode/ExitPlanMode` | Clean mode switching with state save/restore | Medium |
| `EnterWorktree/ExitWorktree` | Git worktree isolation for risky work | Medium |
| `MonitorTool` | Real-time shell output monitoring | Low |
| `CronScheduleTool` | Background job scheduling | Low |
| `NotebookEditTool` | Cell-level Jupyter editing (not full rewrite) | Low |
| `SendUserFileTool` | File delivery to user | Low |

### What compact_v3 has that Claude Code doesn't
| Tool | What it does |
|---|---|
| `create_word` | .docx with tables, images, TOC |
| `create_excel` | .xlsx with charts |
| `create_pdf` | Structured PDF |
| `create_chart` | PNG charts (bar, line, pie) |
| `python_exec` | Sandboxed Python with import allowlist |
| `semantic_search` | Vector-based code search |

→ Keep all compact_v3 document tools. Claude Code doesn't have them.

### Tool Execution Flow Comparison

| Aspect | Claude Code | compact_v3 |
|---|---|---|
| Error recovery | Per-tool (BashTool timeout + auto-background) | Global exponential backoff |
| Output truncation | Tiered: per-tool → per-message (200K) → disk | Smart head+tail, 30KB cap, disk save |
| Validation stages | 3-stage: rules → input validation → hook approval | Denylist pattern match |
| Timeout | 30s default, auto-background at 15s | 600s bash, 300s python |
| Output persistence | `/tool-results/` with preview path | `./truncated_outputs/` |

### v4 Action: Add per-turn aggregate output budget
After all tool calls in a turn, if total > 200K chars, trim the largest outputs first.

---

## SECTION 4: GIT INTEGRATION (REGRESSION PREVENTION)

### Claude Code: FileEditTool pre-checks

Before every file edit:
1. Read cached file state (timestamp + content hash)
2. Fetch current git diff: `fetchSingleFileGitDiff()`
3. Check for stale reads (file changed since last read)
4. Detect partial view (file was only partially read)
5. Validate encoding (BOM, UTF-16 vs UTF-8)
6. UNC path guard (prevents NTLM credential leak on Windows)
7. Generate patch for analytics after edit

### compact_v3: No git awareness
- Basic file-exists check only
- No staleness detection
- No git diff before edit
- User must manually run `git diff` via bash

### v4 Actions (HIGH PRIORITY — main regression prevention)
1. **Pre-edit git diff**: Before any `edit_file`, run `git diff HEAD <filepath>` and show it in the tool output
2. **Staleness detection**: Track file mtime/hash on read; reject edit if file changed since
3. **Partial view guard**: If file was read with offset/limit, warn before editing
4. **Post-edit summary**: Show line count changed + diff summary in tool result

```python
# v4 edit_file enhancement:
def tool_edit_file(args):
    # 1. Check staleness
    if file_was_modified_since_last_read(path):
        return "Error: file changed since last read. Re-read before editing."
    # 2. Show pre-edit diff
    git_diff = run_bash(f"git diff HEAD {path}")
    # 3. Apply edit
    ...
    # 4. Show post-edit summary
    return f"Edited {path}. {lines_changed} lines changed.\nCurrent git diff:\n{git_diff}"
```

---

## SECTION 5: AGENT-TO-SUBAGENT COORDINATION

### Claude Code: 5-path spawning model

| Path | Sync/Async | Isolation | When to use |
|---|---|---|---|
| **Fork** | Async only | None (parent context) | High-volume parallel work, cache hits |
| **Worktree** | Both | Git worktree | Risky changes, experimental |
| **Teammate** | Async | Thread-local or tmux | Named, addressable long-running agents |
| **Remote** | Async only | Remote CCR env | Cloud-scale parallelism |
| **Named subagent** | Both | Shared/cloned parent | Standard delegation |

**Context passing to subagents**:
- File state cache: cloned (avoids partial-view blocking of parent)
- Tool pool: filtered by agent type allowlist
- System prompt: agent definition's own prompt (not parent's)
- MCP servers: parent servers + agent-specific servers
- Permission mode: respects definition's `permissionMode`

**Depth control**:
- Fork: recursive guard via `isInForkChild()` tag in messages
- Named: `maxTurns` per definition (default 200)
- compact_v3: `subagent_max_depth = 2`

### compact_v3: ThreadPoolExecutor parallel execution
- Runs multiple `task` tool calls concurrently (max 4 workers)
- Thread-local file cache isolation per sub-agent
- `save_and_clear_context()` before sub-agent, restore after
- `subagent_max_depth = 2` hard limit
- Agent types: explore, plan, review, build, general

**Gap**: compact_v3 has the parallel execution infrastructure but no worktree isolation, no fork pattern, no named teammates.

### v4 Actions
1. **Document context isolation rules explicitly** in code comments
2. **Add worktree mode** for risky edits: create temp git branch, work there, offer to merge
3. **Named subagents**: allow defining `agent_types` in config with model + tool overrides
4. Keep existing ThreadPoolExecutor parallel execution (it works well)

---

## SECTION 6: SECURITY

### Claude Code: Structural (AST-based)

**Bash security**:
- AST parsing via tree-sitter (detects Zsh-specific attacks, process substitution)
- Command-specific path extractors (rm, cp, mv each know their argument structure)
- **Dangerous path enforcement** overrides allowlist (even if user approved `rm:*`, `rm -rf /` is blocked)
- Permission classifier with confidence scoring (auto-approve safe, ask medium, deny high-risk)

**Permission classifier auto-approves**:
- `git status`, `echo`, `ls`, `cat` → safe
- `git commit`, `pip install` → ask
- `rm -rf`, `sudo` → deny

### compact_v3: Pattern-based (regex denylist)

**Bash security**:
- 70+ bash denylist patterns (destructive, credential, network, system)
- Basic `realpath()` workspace boundary check
- No AST, no command-specific extractors

**Python security** (compact_v3 advantage):
- 40+ Python patterns blocked
- Import hook with 60+ module allowlist
- Wraps `open()`, `os.open()`, `os.remove()` at runtime
- Blocks ALL subprocess (Claude Code doesn't have Python-specific blocking)

### v4 Actions
1. Keep compact_v3's Python sandbox — Claude Code doesn't have it
2. Add dangerous-path enforcement that overrides user allowlist rules
3. Add simple command classifier (auto-approve read-only commands without asking)
4. Consider tree-sitter for bash if dependency is acceptable

---

## SECTION 7: SKILLS SYSTEM

### Claude Code: 6-source, feature-rich

**Skill sources** (in priority order):
1. Bundled (shipped with app)
2. Plugin-provided
3. Project-level (`.claude/skills/`)
4. User-level (`~/.claude/skills/`)
5. Managed/policy
6. MCP skill builders

**Frontmatter fields**: name, description, whenToUse, effort, arguments, paths, hooks, model, tools

**CLAUDE.md integration**: Auto-discovers in project hierarchy, cached in state, disabled via env var

**Auto-surfacing**: Relevant skills injected into system prompt each turn (not just when user asks)

**Lazy loading**: Only loads frontmatter until skill is actually invoked

**Deduplication**: realpath-based, prevents duplicate loading via symlinks

### compact_v3: Simple 3-dir scan

**Sources**: `.agent/skills/`, `.claude/skills/`, `./skills/`
**Frontmatter**: name, description, tags only
**No CLAUDE.md, no auto-surfacing, no lazy loading, no deduplication**

### v4 Actions (HIGH PRIORITY)
1. **Add CLAUDE.md auto-loading**: On startup, read `CLAUDE.md` from workspace root → inject into system prompt
2. **Add parent dir search**: Walk up to find CLAUDE.md in parent dirs (stop at home)
3. **Auto-surface relevant skills**: Each turn, check which skill descriptions match recent messages → inject skill name hints
4. **Add `effort` field to frontmatter**: Signals token cost (low/medium/high) for lazy loading decisions

```python
# v4 CLAUDE.md loader
def load_project_instructions(workspace: str) -> str:
    instructions = []
    path = workspace
    while path != os.path.dirname(path):  # walk up to root
        claude_md = os.path.join(path, "CLAUDE.md")
        if os.path.exists(claude_md):
            instructions.append(open(claude_md).read()[:10000])
        path = os.path.dirname(path)
    return "\n\n---\n\n".join(reversed(instructions))
```

---

## SECTION 8: MEMORY SYSTEM

### Claude Code: 4-type structured memory

**Types**:
1. **user** — role, preferences, knowledge level
2. **feedback** — what to do/avoid (corrections AND confirmations)
3. **project** — ongoing work, goals, decisions not in code
4. **reference** — pointers to external systems (Linear, Grafana, Slack)

**Features**:
- Each type = separate file per topic
- MEMORY.md index (200-line limit)
- Auto-extraction after each turn (LLM reads conversation, decides what to save)
- Semantic recall (relevant memories injected into system prompt)
- Private/Team scope
- 25KB size limit with truncation

### compact_v3: Single memory.md

- One flat file, no types, no extraction
- Manual editing only
- No recall mechanism
- Loaded at startup (first 10K chars)

### v4 Actions
1. **Add 4-type structure to memory.md** — simple sections with headers
2. **Add memory extraction prompt** — after long sessions, run: "What from this session should be remembered?"
3. **Auto-inject relevant memory** — search memory.md for keywords matching current task
4. Keep single-file approach (simpler for SageMaker context)

---

## SUMMARY: v4 PRIORITY LIST

### HIGH — Do these first (regression prevention + stability)

| # | Feature | Why | Effort |
|---|---|---|---|
| 1 | **CLAUDE.md auto-load** | Project context without manual injection | Low |
| 2 | **Pre-edit git diff + staleness check** | Regression prevention | Medium |
| 3 | **Post-edit diff summary** | User can see what changed | Low |
| 4 | **Microcompact** — replace old tool results mid-stream | Save tokens without full compact | Medium |
| 5 | **Post-compact file restoration** | Don't lose file context after compact | Low |
| 6 | **Circuit breaker** for compact failures | Stability | Low |

### MEDIUM — Do these in v4.1

| # | Feature | Why | Effort |
|---|---|---|---|
| 7 | **4-type memory structure** | Better memory organisation | Low |
| 8 | **Memory extraction** (turn-end LLM) | Auto-save learnings | Medium |
| 9 | **Auto-surface relevant skills** | Reduce manual skill invocation | Medium |
| 10 | **Partial view guard on edit** | Prevent blind edits | Low |
| 11 | **Command auto-classifier** (read-only = skip approval) | Less friction | Medium |
| 12 | **Dangerous path enforcement** | Override allowlist for catastrophic ops | Low |

### LOW — Future versions

| # | Feature | Why | Effort |
|---|---|---|---|
| 13 | Worktree isolation for risky edits | Sandboxed experimentation | High |
| 14 | Prompt cache boundary | Token savings (Bedrock may not support) | Medium |
| 15 | Named teammates | Multi-agent coordination | High |
| 16 | tree-sitter AST bash parsing | More accurate security | High |

---

## FILES TO STUDY IN CLAUDE CODE FOR IMPLEMENTATION

| Feature | Claude Code file |
|---|---|
| System prompt structure | `src/constants/prompts.ts` |
| Prompt caching boundary | `src/utils/systemPromptSections.ts` |
| Microcompact logic | `src/services/compact/microCompact.ts` |
| Auto-compact threshold | `src/services/compact/autoCompact.ts` |
| Post-compact restore | `src/services/compact/compact.ts` |
| Token counting | `src/utils/tokens.ts`, `src/utils/tokenEstimation.ts` |
| Pre-edit git diff | `src/tools/FileEditTool/` |
| Staleness detection | `src/tools/FileEditTool/FileEditTool.ts` |
| CLAUDE.md loading | `src/context.ts` |
| Skills system | `src/skills/loadSkillsDir.ts` |
| Memory 4-type system | `src/memdir/` |
| Memory extraction | `src/services/extractMemories/` |
| Permission classifier | `src/utils/permissions/` |
| Dangerous path enforcement | `src/tools/BashTool/bashSecurity.ts` |
| AgentTool coordination | `src/tools/AgentTool/` |
| Worktree isolation | `src/tools/AgentTool/worktree.ts` |
