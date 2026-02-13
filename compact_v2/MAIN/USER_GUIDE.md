# SageMaker Coding Agent — User Guide

A single-file AI coding assistant for AWS SageMaker, powered by Bedrock Claude.

---

## Quick Start

1. Copy this folder to your SageMaker workspace
2. Install dependencies: `pip install boto3 ipywidgets Pillow python-docx pandas openpyxl`
3. Open `chat.ipynb`, run all cells
4. Start chatting

---

## Built-in Tools (21)

| Category | Tools |
|----------|-------|
| **File ops** | `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `list_dir` |
| **Execution** | `bash`, `python_exec` |
| **Documents** | `create_word`, `create_excel`, `create_markdown`, `create_pdf` |
| **Charts** | `create_chart` (bar, line, pie, scatter) |
| **Vision** | `view_image` |
| **Search** | `semantic_search` (Bedrock Titan embeddings) |
| **Planning** | `todo_write`, `todo_read` |
| **Web** | `web_fetch` (URL fetch with SSRF protection) |
| **Skills** | `skill` (list/load skills) |
| **Sub-agents** | `task` (spawn specialized child agents) |
| **Interactive** | `ask_user` (ask questions mid-conversation) |

---

## Slash Commands (Built-in)

| Command | What it does |
|---------|-------------|
| `/skills` | List all discovered skills |
| `/skill use <name>` | Activate a skill (injected into system prompt) |
| `/skill clear` | Deactivate all skills |
| `/commands` | List custom slash commands from `opencode.json` |
| `/cost` | Show token usage and cost breakdown |
| `/revert <file>` | Revert a file to pre-edit snapshot |
| `/revert all` | Revert all modified files |
| `/compact` | Manually compact conversation context |
| `/save` | Save current session |

---

## Configuration (`opencode.json`)

Optional. Place in your workspace root. Supports JSONC (comments with `//`).

```json
{
  // Skills
  "skills_dir": "./skills",
  "enable_skills": true,

  // Custom slash commands
  "commands": {
    "review": {
      "template": "Review this code for bugs and security issues:\n$ARGUMENTS",
      "description": "Code review",
      "agent": "plan"
    },
    "test": {
      "template": "Write tests for:\n$ARGUMENTS",
      "description": "Generate tests"
    }
  },

  // MCP servers
  "mcp": {
    "my-server": {
      "type": "local",
      "command": ["python", "my_mcp_server.py"],
      "env": {},
      "timeout": 30
    },
    "remote-api": {
      "type": "remote",
      "url": "https://my-mcp-endpoint.example.com/rpc",
      "headers": {"Authorization": "Bearer TOKEN"},
      "timeout": 30
    }
  },

  // Permission overrides
  "permissions": {
    "bash": "ask",
    "read_file": "allow",
    "*.env": "deny",
    "bash:rm*": "deny"
  },

  // Agent type overrides
  "agents": {
    "explore": {
      "max_turns": 20
    }
  }
}
```

---

## Skills

Skills are markdown instruction files that get injected into the system prompt when activated.

**Create a skill:**
```
skills/
  my-skill/
    SKILL.md
```

**SKILL.md format** (YAML frontmatter optional):
```markdown
---
name: my-skill
description: What this skill does
---

Your instructions for the LLM here...
```

**Use it:**
1. `/skills` — confirm it's discovered
2. `/skill use my-skill` — activate (stays active for the session)
3. Chat normally — the LLM follows your skill instructions
4. `/skill clear` — deactivate when done

The LLM can also call the `skill` tool on its own to list or load skills without you typing slash commands.

**Discovery paths:** `./skills/`, `.opencode/skill/`, `.opencode/skills/`, `.claude/skills/`

**Included example:** `skills/review/SKILL.md` — a code review checklist (security, quality, performance, testing). Activate with `/skill use code-review`.

---

## MCP (Model Context Protocol)

Connect external tool servers to extend the agent's capabilities.

**Two transport types:**

| Type | Config | How it works |
|------|--------|-------------|
| `local` | `"command": ["python", "server.py"]` | Spawns subprocess, JSON-RPC over stdin/stdout |
| `remote` | `"url": "https://..."` | HTTP POST JSON-RPC |

**What happens on startup:**
1. Each configured server is connected (MCP handshake)
2. Tools are discovered via `tools/list`
3. Each tool becomes `mcp_<server>_<tool>` in the agent
4. The LLM can call them like any built-in tool
5. Status bar shows connection count

**Disable a server** without removing config: `"enabled": false`

**Tool naming:** If server `my-server` exposes tools `search` and `fetch`, they register as:
- `mcp_my_server_search`
- `mcp_my_server_fetch`

**Safety:** Deadlock protection on stdio (timeout-based readline), 2MB response limit on HTTP, name collision detection with warnings.

---

## Sub-Agents

The LLM can spawn child agents for specialized tasks via the `task` tool.

| Agent Type | Access | Max Turns | Use Case |
|-----------|--------|-----------|----------|
| `build` | All tools | 25 | Full development tasks |
| `plan` | Read-only | 15 | Analysis, code review |
| `explore` | Read-only (minimal) | 10 | Fast codebase search |
| `general` | Read + write | 15 | Multi-step research |

Custom agents can be defined in `opencode.json` under `"agents"`. Override max_turns, prompt, or model per agent type.

When **Plan Mode** is ON, all sub-agents are forced to `plan` type (read-only). Sub-agent depth is limited to 2 levels by default (configurable via `subagent_max_depth`).

**How it works:** The LLM decides when to spawn a sub-agent. For example, if you ask "explore the codebase and find all API endpoints", it may call `task` with `subagent_type: "explore"`. The child agent runs with restricted tools and returns a summary.

---

## Custom Slash Commands

Define in `opencode.json` under `"commands"`:

```json
{
  "commands": {
    "review": {
      "template": "Review this code:\n$ARGUMENTS",
      "description": "Code review",
      "agent": "plan"
    }
  }
}
```

**Template variables:** `$ARGUMENTS` (full text), `$1`, `$2` (positional args)

**Usage:** Type `/review sagemaker_agent.py` in chat. The template expands and sends as a message. If `"agent"` is set, it routes through that sub-agent type.

---

## Security

**Bash** — 3-layer validation:
1. Command allowlist (blocks `aws`, `curl` to external, `rm -rf /`, etc.)
2. Pattern matching (70+ dangerous patterns)
3. Restricted execution mode

**Python** — 3-layer validation:
1. AST analysis (blocks `eval`, `exec`, `__import__`)
2. Import hook (allowlist of safe modules, blocks `subprocess`, `socket`, etc.)
3. Secret detection (API keys, passwords, tokens)

**Web fetch** — SSRF protection:
- Blocks private IPs (127.x, 10.x, 172.16-31.x, 192.168.x)
- Blocks cloud metadata (169.254.169.254, metadata.google.internal)
- Blocks IPv6 ULA (fc00::/7) and link-local (fe80::)
- Blocks redirects to internal hosts
- 2MB response limit

**Workspace boundary** — all file operations confined to workspace directory.

---

## Cost Tracking

- Per-model pricing for 8 Bedrock models (Haiku, Sonnet, Opus variants)
- `/cost` shows detailed breakdown: input/output tokens, cache hits, dollar amounts
- Running cost displayed in status bar

---

## Snapshots & Revert

Every file write/edit automatically creates a backup in `.snapshots/`.

- `/revert <filename>` — restore to pre-edit state
- `/revert all` — restore all modified files
- Max 100 snapshots, oldest auto-pruned

---

## UI Features

- **Plan Mode** toggle — restricts agent to read-only tools
- **Auto-Compact** — automatically compresses conversation at 90% context
- **Stop button** — cancel LLM processing mid-stream
- **Dark mode** toggle
- **Session management** — save/load/new sessions
- **Token usage** — progress bar showing context window usage

---

## File Structure

```
MAIN/
├── sagemaker_agent.py    # The agent (5963 lines, single file)
├── sagemaker_agent.md    # Markdown copy of the above
├── chat.ipynb            # Jupyter notebook launcher
├── chat.md               # Markdown copy of the notebook
├── opencode.json         # Configuration (optional, JSONC)
├── USER_GUIDE.md         # This file
└── skills/
    └── review/
        └── SKILL.md      # Example: code review skill
```

---

## Example Prompts

| What you want | What to type |
|--------------|-------------|
| Explore files | "List all Python files in this directory" |
| Read code | "Read sagemaker_agent.py and explain the SecurityManager class" |
| Edit code | "Add error handling to the login function in app.py" |
| Run command | "Run git status" |
| Create doc | "Create an Excel file with a sales summary" |
| Code review | `/skill use code-review` then "Review app.py" |
| Custom command | `/review sagemaker_agent.py` (uses your opencode.json template) |
| Check cost | `/cost` |
| Undo edit | `/revert app.py` |
| Plan mode | Toggle Plan Mode ON, then "Analyze the architecture of this project" |
