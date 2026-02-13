# Compact V2 Changelog

## v2.9.0 — OpenCode Feature Parity (2026-02-13)

Created `compact_v2/` as an enhanced version of `compact/` that closes the extensibility gap with OpenCode while preserving the single-file SageMaker-native architecture.

### New Features

#### 1. External Config File (`opencode.json` / `.opencode/config.json`)
- Loads optional JSON/JSONC config from workspace root at startup
- Supports `//` single-line comments (JSONC)
- Merges with Python dataclass defaults
- Configures: agents, MCP servers, custom commands, permissions, skills directory

#### 2. Skills System (OpenCode-compatible)
- **Frontmatter parsing**: YAML `---` blocks with `name` and `description` fields
- **Recursive discovery**: Globs `**/SKILL.md` across multiple directories (`.opencode/skill/`, `.opencode/skills/`, `.claude/skills/`, custom)
- **Active skill injection**: Loaded skill content appended to system prompt
- **Combined `skill` tool**: Lists available skills or loads a specific one (replaces old `skill_list` + `skill_read`)
- **XML-formatted descriptions**: Skill list embedded in tool description for LLM awareness
- Example skill: `skills/review/SKILL.md` (code review checklist)

#### 3. Custom Slash Commands (CommandRegistry)
- Define commands in `opencode.json` with templates
- Template variables: `$ARGUMENTS` (full args), `$1`, `$2` (positional)
- `/commands` lists available commands in chat
- `/name args` expands template and sends as user message
- Each command can specify an agent type override

#### 4. Sub-Agent Types (AGENT_TYPES)
- **4 built-in agent types**:
  - `build`: Full-access development agent (all tools, 25 turns)
  - `plan`: Read-only analysis (restricted tools, PLAN_MODE_PROMPT, 15 turns)
  - `explore`: Fast codebase exploration (read-only tools, 10 turns)
  - `general`: Multi-step research (read + write tools, 15 turns)
- **Custom agents**: Define new types or override builtins via `opencode.json`
- **Renamed tool**: `subagent_run` -> `task` (OpenCode-compatible)
- **Agent-specific**: tool allowlists, prompt suffixes, max turns, model overrides
- **Depth limiting**: Configurable `subagent_max_depth` (default 2)

#### 5. MCP Client System (Model Context Protocol)
- **McpStdioClient**: Spawns local MCP servers via subprocess, JSON-RPC over stdin/stdout
  - Full MCP handshake: `initialize` -> `notifications/initialized`
  - Tool discovery via `tools/list`
  - Tool execution via `tools/call`
  - Notification handling, graceful shutdown
- **McpHttpClient**: JSON-RPC over HTTP POST (Streamable HTTP transport)
  - Custom headers, configurable timeout
- **McpManager**: Manages all MCP connections
  - `connect_all()`: Connects to configured servers (supports `enabled: false` to skip)
  - `discover_tools()`: Converts MCP tools to TOOLS registry format with `mcp_<server>_<tool>` naming
  - `status_summary()`: Connection status for UI display
  - `close_all()`: Graceful shutdown of all servers
- **Dynamic tool registration**: MCP tools merged into TOOLS dict at startup

#### 6. Diff Tracking
- `_generate_unified_diff()`: Creates unified diff format for file changes
- `tool_write_file` and `tool_edit_file` now generate and store diffs
- Recent diffs stored in `_RECENT_DIFFS` list for review

#### 7. Configurable Permission Rules
- Config-based `permission_rules` in `opencode.json`
- Per-tool rules: `"bash": "ask"`, `"read_file": "allow"`
- File-pattern rules via fnmatch: `"*.env": "deny"`
- Integrated into `request_approval()` flow

#### 8. WebFetch Tool
- Fetches URL content with HTML-to-markdown conversion
- Strips script/style blocks, converts headings/lists/links
- Blocked in Docker mode with network disabled
- Respects security output truncation

#### 9. UI Enhancements
- Status bar shows: MCP connection count, active skill name, custom commands count
- `/commands` lists available slash commands
- Active skill displayed in mode indicator

### Changed
- **Tool renames**: `skill_list`+`skill_read` -> `skill`, `subagent_run` -> `task`
- **PLAN_MODE_BLOCKED_TOOLS**: Updated for new tool names (`task` replaces `subagent_run`)
- **PLAN_MODE_ALLOWED_TOOLS**: Added `skill`, `web_fetch`
- **HIGH_RISK_TOOLS**: Now `{"bash", "python_exec", "task", "web_fetch"}`
- **Config dataclass**: New fields for `mcp_servers`, `custom_commands`, `permission_rules`, `agent_overrides`, `subagent_max_depth`

### Tests
- 22 new tests in `test_v2_features.py`:
  - Config loading (3): empty path, JSON parsing, JSONC comment stripping
  - SkillManager (3): frontmatter discovery, content reading, XML prompt format
  - CommandRegistry (3): template expansion, unknown commands, listing
  - AGENT_TYPES (4): type definitions, plan read-only, build all-access, explore minimal
  - McpManager (5): empty config, disabled servers, invalid types, missing commands, status summary
  - Diff generation (2): normal diff, empty-to-new diff
  - Tool registry (2): new tool names present, old names removed
- Updated existing test: `test_subagent_tool_runs_in_plan_mode` -> `test_task_tool_runs_with_agent_type`
- **47 total tests pass** (25 existing + 22 new)

### Comparison: Compact V2 vs OpenCode

| Area | OpenCode | Compact V2 |
|------|----------|-----------|
| Security | Permission rules only | 3-layer bash + 3-layer Python AST + Docker + rate limiting |
| Error Recovery | 4 layers | 5 layers (arg auto-fix, type conversion, fuzzy suggest) |
| Document Creation | None | 5 tools (Word, Excel, PDF, Chart, Markdown) |
| Semantic Search | None built-in | Bedrock Titan embeddings + cosine similarity |
| SageMaker Native | Not supported | Native Jupyter widgets, Bedrock integration |
| Architecture | 100+ files | Single file + config |
| MCP | stdio + HTTP + OAuth | stdio + HTTP (no OAuth — not needed on SageMaker) |
| Sub-agents | 5 types | 4 types + custom via config |
| Skills | Glob + frontmatter | Same (upgraded from flat .md) |
| Config | JSONC with schema | JSONC with merge |
| Slash Commands | Template-based | Same |
| Diffs | Unified patches | Same |
| LSP | 7 language servers | Not included (impractical in Jupyter kernel) |
| File Watching | Native watcher | Not included (Jupyter handles changes) |
