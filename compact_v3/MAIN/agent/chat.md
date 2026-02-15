## Cell 0 (markdown)

# SageMaker Coding Agent V3

Secure AI coding assistant powered by AWS Bedrock Claude.

**22 Tools:** File ops, bash/python exec, docs/charts/pdf/notebooks, vision, semantic search, todos, web fetch, skills, sub-agents, ask user

**Security:** 3-layer bash + 3-layer Python + workspace boundary + SSRF protection

---

## Version History

### V1 (compact/) -- 5,042 lines
The original single-file agent, ported from OpenCode patterns to Python/SageMaker.
- 22 tools (file ops, bash/python exec, docs, charts, vision, semantic search)
- Security controls (workspace boundary, secret detection, command filtering)
- Tool approval toggle (default OFF for SageMaker)
- Session management and audit logging
- Context monitoring and compaction
- Sub-agents (build, plan, explore, general)
- Skills system and MCP client

### V2 (compact_v2/) -- 6,323 lines (+1,281 over V1)
Major feature release adding external config, cost tracking, and error recovery.
- External config (`opencode.json`) with JSONC support
- Skills system with YAML frontmatter (`/skills`, `/skill use <name>`, `/skill clear`)
- Custom slash commands with templates (`/review`, `/test`, etc.)
- Cost tracking (`/cost`) with per-model Bedrock pricing
- Snapshot and revert (`/revert <file>`, `/revert all`)
- Interactive questions (`ask_user` tool)
- Diff tracking on every edit
- Permission rules (per-tool, file-pattern, command-pattern)
- SSRF-hardened web fetch
- Error recovery (tool name repair, arg auto-fix, type conversion, fuzzy suggest)
- Auto-save sessions every message
- Bedrock client config (600s read timeout for large outputs)
- Python sandbox: C-extension accelerator whitelist + relative import support
- SageMaker deadlock fix (Send button fallback for approval dialogs)

### V3 (compact_v3/) -- 6,558 lines (+235 over V2, 27 bugs fixed)
Best practices integration from [everything-claude-code](https://github.com/winstonpgao/everything-claude-code). 6 rounds of code review.
- **Review agent** type (security, quality, performance, architecture, testing)
- **Enhanced planner** prompt (restate requirements, assess risks, phased plan)
- Plan agent has `web_fetch` + `ask_user` tools
- **`/verify` command** (6-phase: build, type, lint, test, security, diff)
- **`/checkpoint` command** (named checkpoints with create/list, capped at 50)
- **Git workflow rules** (conventional commits, atomic changes, branch naming)
- **Testing discipline rules** (TDD, 80% coverage target, AAA pattern)
- **5 skills**: verification-loop (148 lines), coding-standards (154 lines), review (84 lines), powerbi-dashboard (V1 template-based), powerbi-dashboard-v2 (config-driven engine, 461 lines)
- Interactive `ask_user` with text input widget + submit/skip buttons
- Session checkpoint persistence (save/load/restore with deepcopy)
- ASCII system messages (no emoji encoding issues)
- `_FILES_READ` reset on session load (no stale write-guard)
- Single skill injection path (no double-injection)
- Session ID collision prevention (`os.urandom(3).hex()` suffix)
- SageMaker deadlock fix (Send button fallback for approval + ask_user dialogs)

See `USER_GUIDE.md` for full documentation.


## Cell 1 (code)




## Cell 2 (code)




## Cell 3 (code)




## Cell 4 (markdown)

---

## Token Display

The chat UI shows two token metrics:

| Metric | What it shows |
|--------|---------------|
| **API Totals (In/Out/Calls)** | Cumulative tokens across ALL API calls. Each call sends system prompt + tool definitions + full conversation history, so this grows fast. |
| **Context Window (% / max)** | Current conversation size only (user + assistant messages). Does NOT include system prompt or tool schemas (see below). |

### Token Overhead Per API Call

| Component | Tokens | Optimized? |
|-----------|--------|------------|
| System prompt | ~1,200 | Yes (compressed from ~2,100) |
| Tool schemas (22 tools) | ~1,800 | Yes (trimmed redundant descriptions) |
| **Fixed overhead** | **~3,000** | **Saved ~1,300 tokens/call vs pre-optimization** |

The gap between API Totals and Context Window is normal. Example: 6 API calls with ~5K tokens each = ~30K cumulative input, but Context Window shows only ~900 tokens (just conversation messages).

### What's Optimized
- System prompt compressed 128 -> 62 lines (removed redundancy, merged sections)
- Tool descriptions shortened (removed duplicate info already in parameter schemas)
- Sub-agents use filtered tool sets (explore: 5 tools, plan: 10, review: 6 — not all 22)
- History compaction at 80% context window (LLM summary + tool output pruning)

### Not Yet Possible (Bedrock limitation)
- Prompt caching (Bedrock doesn't support `cache_control` like Anthropic direct API)
- Tool schema caching (sent fresh every call)

---

## Quick Start Examples

| Task | Example Prompt |
|------|----------------|
| **Explore** | "List files in this directory" |
| **Read** | "Read the README.md file" |
| **Search** | "Find all Python files with test in the name" |
| **Semantic Search** | "Find where authentication is handled" |
| **Edit** | "Add a comment to the top of file.py" |
| **Execute** | "Run git status" |
| **Create Excel** | "Create an Excel file with employee data" |
| **Create Word** | "Write a project summary document" |
| **Create PDF** | "Create a PDF report with table and chart summary" |
| **Create Notebook** | "Create a notebook that loads and analyzes data" |
| **Create Chart** | "Create a bar chart of monthly sales data" |
| **Web Fetch** | "Fetch https://example.com and summarize it" |
| **Plan** | "Help me build a REST API with Flask" |
| **Review** | "Review the code I just wrote for security issues" |
| **Power BI** | "Create a 4-page sales dashboard with KPIs and charts" |

---

## Tools (22)

| Category | Tool | Description |
|----------|------|-------------|
| **File** | `read_file` | Read file contents (offset/limit for large files, max 500 lines default) |
| | `write_file` | Write file (must read first if file exists) |
| | `edit_file` | Find-and-replace edit (exact match required, `replace_all` toggle) |
| | `glob` | Find files by pattern (e.g., `**/*.py`) |
| | `grep` | Search file contents by regex |
| | `list_dir` | List directory contents |
| **Exec** | `bash` | Run shell commands (timeout max 600s, 3-layer security validation) |
| | `python_exec` | Execute Python code (timeout max 300s, AST + import validation) |
| **Docs** | `create_word` | Generate Word documents (.docx) |
| | `create_excel` | Generate Excel spreadsheets (.xlsx) |
| | `create_markdown` | Generate Markdown files |
| | `create_notebook` | Generate Jupyter notebooks (.ipynb) |
| | `create_pdf` | Generate PDF reports (markdown or table format) |
| **Charts** | `create_chart` | Generate charts displayed inline (bar, line, pie, scatter, horizontal_bar) |
| **Vision** | `view_image` | View and analyze images |
| **Search** | `semantic_search` | Bedrock Titan embeddings (3 actions: index, search, status) |
| **Planning** | `todo_write` | Create/update task list |
| | `todo_read` | Read current task list |
| **Web** | `web_fetch` | Fetch URL content (SSRF-hardened, 2MB limit, redirect blocking) |
| **Skills** | `skill` | List/load skill files from `skills/` directory |
| **Sub-agents** | `task` | Spawn sub-agent (build, plan, explore, general, review) |
| **Interactive** | `ask_user` | Ask user mid-conversation (text input + submit/skip buttons, 5-min timeout) |

---

## Sub-Agents

| Agent | Tools Available | Max Turns | Use Case |
|-------|----------------|-----------|----------|
| **build** | All tools (file, exec, docs) | 25 | Build, compile, fix errors, run tests |
| **plan** | read-only + `web_fetch` + `ask_user` | 15 | Architecture planning with web research and clarification |
| **explore** | read-only + `semantic_search` + `view_image` | 10 | Codebase exploration and analysis |
| **general** | All except docs/charts/pdf | 15 | General-purpose coding tasks |
| **review** | read-only + `semantic_search` + `view_image` | 10 | Code review: security, quality, performance, architecture, testing |

**Plan agent** (V3 enhanced): Restates requirements, assesses risks, creates phased plan, waits for user confirmation before coding.

---

## Slash Commands

| Command | What it does |
|---------|-------------|
| `/skills` | List all discovered skills from `skills/` directory |
| `/skill use <name>` | Activate a skill (injected into system prompt) |
| `/skill clear` | Deactivate all active skills |
| `/commands` | List custom slash commands from `opencode.json` |
| `/cost` | Token usage and cost breakdown by model |
| `/revert <file>` | Revert file to pre-edit snapshot |
| `/revert all` | Revert all modified files to pre-edit snapshots |
| `/compact` | Compress conversation context (summarize history to reduce tokens) |
| `/save` | Save current session (messages, todos, metadata, checkpoints) to JSON |
| `/verify` | Run 6-phase verification: build, type-check, lint, test, security scan, diff review |
| `/verify quick` | Quick verification (build + lint only) |
| `/checkpoint <name>` | Create named checkpoint (saves todos, files modified, token stats; capped at 50) |
| `/checkpoint list` | List all checkpoints with timestamps and todo counts |

---

## Skills (5)

Skills are markdown files with YAML frontmatter in the `skills/` directory. When activated via `/skill use <name>`, their content is injected into the system prompt. The agent proactively matches user requests to available skills and auto-loads them (no manual activation needed).

| Skill | Lines | What it does |
|-------|-------|-------------|
| **review** | 84 | Code review checklist: security (CRITICAL), quality (HIGH), performance (MEDIUM), architecture, testing. Structured output with severity ratings. |
| **verify** | 148 | 6-phase verification loop: (1) build check, (2) type check (pyright/mypy/tsc), (3) lint (ruff/eslint), (4) test suite with coverage, (5) security scan (secrets, .env), (6) diff review. Outputs VERIFICATION REPORT with PASS/FAIL per phase. |
| **coding-standards** | 154 | Language-agnostic coding standards: KISS, DRY, YAGNI, naming conventions, error handling, function design (<50 lines), testing (AAA pattern, 80% coverage), code smells. |
| **powerbi-dashboard** | 322 | Power BI V1 dashboard generator (template-based): 4-phase workflow (requirements, data analysis, design, build). 14 chart types, star schema, DAX measures, PBIR/TMDL output. Sales/business data only. |
| **powerbi-dashboard-v2** | 461 | Power BI V2 config-driven engine: edit SCHEMA dict for any data domain. Supports CSV ingestion, calculated columns, M preprocessing, auto-layout. Tested with 7 dashboards across sales, enrollment, healthcare, HR, logistics, marketing, retail. |

**Skill format**: `skills/<name>/SKILL.md` with optional YAML frontmatter (`name`, `description`, `version`).

---

## Configuration

### Widget Configuration (Cell 2)

| Setting | Options | Default |
|---------|---------|---------|
| **Model** | Claude 3 Haiku, Claude 3 Sonnet, Claude 3.5 Sonnet (v1/v2), Claude 4.5 Sonnet/Haiku/Opus, Claude 4.6 Opus | Claude 3 Haiku |
| **Temperature** | 0.0 (deterministic) to 1.0 (max creativity) | 0.0 |
| **Extended Thinking** | On/Off (uses more tokens, slower, better reasoning) | Off |
| **Thinking Budget** | 1024 / 2048 / 4096 / 8192 / 16000 tokens | 4096 |
| **Max Turns** | 5-100 (agent loop iterations per message) | 60 |
| **Workspace** | Directory path for file operations | `.` (current) |
| **Mock Mode** | Test UI without API calls | Off |

### External Configuration (`opencode.json`)

Optional JSON/JSONC config file for:
- **Permission rules**: Per-tool, file-pattern, and command-pattern allow/deny rules
- **Custom commands**: Slash command templates (e.g., `/review`, `/test`)
- **Skills directory**: Custom skills path
- **Agent overrides**: Custom agent configurations
- **MCP servers**: External tool integrations

---

## Session Management

| Feature | How it works |
|---------|-------------|
| **Auto-save** | Every message auto-saves session (messages, todos, metadata, checkpoints) |
| **Manual save** | `/save` or Save button |
| **Load session** | Session dropdown + Load button (restores messages, todos, skills, checkpoints, model) |
| **Checkpoints** | `/checkpoint <name>` saves a snapshot (todos, files modified, exec calls, token stats). Capped at 50 per session. |
| **New session** | New button clears all state (messages, todos, checkpoints, active skills) |
| **Session ID** | Timestamp + random suffix (`os.urandom(3).hex()`) prevents collision |

---

## Security

| Layer | Protection |
|-------|-----------|
| **Bash (3-layer)** | Allowlist of safe commands + 70 dangerous patterns blocked + restricted mode |
| **Python (3-layer)** | AST validation + import hook (blocks os/subprocess/shutil) + secret detection |
| **SSRF** | Private IP blocking, redirect blocking, 2MB response limit |
| **Workspace** | All file operations restricted to configured workspace directory |
| **Write guard** | Must `read_file` before `write_file` on existing files |
| **Permissions** | Configurable per-tool rules via `opencode.json` |
| **Audit** | Immutable audit trail with integrity verification |
| **Approval** | Tool approval ON by default (Approve/Deny dialog for bash, python_exec, task, web_fetch) |

### System Prompt Rules (V3)

| Rule | Description |
|------|-------------|
| **Git workflow** | Conventional commits (`feat:`, `fix:`, `refactor:`), atomic changes, meaningful branch names, verify no secrets before commit |
| **Testing discipline** | TDD when appropriate (RED-GREEN-IMPROVE), 80% coverage target, AAA pattern (Arrange-Act-Assert), test edge cases, don't modify tests to pass |

---

## Error Recovery

| Feature | What it does |
|---------|-------------|
| **Tool name repair** | Fuzzy-matches misspelled tool names (e.g., `readfile` -> `read_file`) |
| **Arg auto-fix** | Corrects common argument errors automatically |
| **Type conversion** | Converts wrong types (string to int, etc.) |
| **Fuzzy suggest** | Suggests similar tool names when no match found |
| **Malformed recovery** | Recovers from malformed JSON in tool calls |

---

## Cost Tracking

Use `/cost` to see token usage and estimated cost. Pricing is per-model based on Bedrock rates.

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|----------------------|
| Claude 3 Haiku | $0.25 | $1.25 |
| Claude 3 Sonnet | $3.00 | $15.00 |
| Claude 3.5 Sonnet | $3.00 | $15.00 |

---

## Architecture

```
compact_v3/MAIN/
  agent/
    sagemaker_agent.py    <- Agent engine (6,558 lines)
    chat.ipynb            <- This notebook (UI launcher)
    opencode.json         <- External config (permissions, commands)
    USER_GUIDE.md         <- Full documentation
    skills/
      review/SKILL.md           <- Code review skill (84 lines)
      verify/SKILL.md           <- Verification loop skill (148 lines)
      coding-standards/SKILL.md <- Coding standards skill (154 lines)
      powerbi-dashboard/        <- Power BI V1 dashboard generator (template-based)
        SKILL.md                  <- Skill prompt (322 lines)
        GUIDE.md                  <- Beginner guide
        generate_template.py      <- Working template (95 KB)
        reference/
          SOP.md                  <- 25 lessons learned
          STYLING.md              <- Visual styling reference
          theme.json              <- Color palette
        tested/
          generate_project.py     <- University dashboard example
      powerbi-dashboard-v2/     <- Power BI V2 dashboard generator (config-driven)
        SKILL.md                  <- Skill prompt (461 lines)
        GUIDE.md                  <- Guide with tested examples
        generate_engine.py        <- Config-driven engine
        reference/
          SOP.md                  <- Lessons learned
          STYLING.md              <- Visual styling reference
          theme.json              <- Color palette
        tested/
          generate_project.py     <- University enrollment example
  tests/
    enrollment/             <- Enrollment test (generated data, 4 pages)
    csv/                    <- Retail CSV test (real CSV data, 3 pages)
    healthcare/             <- Healthcare test (generated data, 5 pages)
    hr/                     <- HR Workforce test (3 pages, calc cols)
    logistics/              <- Supply Chain test (4 pages, combo charts)
    marketing/              <- Marketing test (3 pages, all visual types)
```

