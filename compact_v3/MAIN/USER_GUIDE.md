# SageMaker Coding Agent V2 — User Guide

A single-file AI coding assistant that runs inside a Jupyter notebook on AWS SageMaker, powered by Bedrock Claude.

---

## Table of Contents

1. [What Is This?](#what-is-this)
2. [Prerequisites](#prerequisites)
3. [Quick Start (Step by Step)](#quick-start-step-by-step)
4. [How the Chat Works](#how-the-chat-works)
5. [All 22 Tools Explained](#all-22-tools-explained)
6. [Slash Commands](#slash-commands)
7. [Skills System](#skills-system)
8. [MCP (Model Context Protocol)](#mcp-model-context-protocol)
9. [Sub-Agents](#sub-agents)
10. [Architecture Concepts](#architecture-concepts)
11. [Custom Slash Commands](#custom-slash-commands)
12. [Configuration File (opencode.json)](#configuration-file-opencodejson)
13. [Permission Rules](#permission-rules)
14. [Security](#security)
15. [Cost Tracking](#cost-tracking)
16. [Snapshots & Revert](#snapshots--revert)
17. [UI Features](#ui-features)
18. [File Structure](#file-structure)
19. [Troubleshooting](#troubleshooting)

---

## What Is This?

This is an AI coding assistant that lives inside a Jupyter notebook. You open a notebook (`chat.ipynb`), run the cells, and a **chat interface** appears. You type messages (like "read file X" or "create a chart"), and the AI agent reads your request, picks the right tool, executes it, and replies with results.

**It is NOT a terminal app.** Everything runs as Python code inside the Jupyter kernel. The chat UI is built with `ipywidgets` (text box + send button + output area). You never need to use a terminal — though the agent can run shell commands internally via its `bash` tool.

**Key facts:**
- Single Python file (`sagemaker_agent.py`, ~6000 lines) — no complex multi-package setup
- 21 built-in tools (file editing, code execution, document creation, search, etc.)
- Extensible via Skills (custom instructions), MCP (external tool servers), and Sub-agents
- Built for AWS SageMaker but works in any Jupyter environment with Bedrock access

---

## Prerequisites

Before you start, you need:

1. **AWS Account** with access to Amazon Bedrock
2. **SageMaker Notebook Instance** (or SageMaker Studio) — any instance type works
3. **Bedrock Model Access** — go to the [Bedrock console](https://console.aws.amazon.com/bedrock/) > Model access > Enable the Claude models you want (at minimum: Claude 3 Haiku in `ap-southeast-2` Sydney region)
4. **IAM Role** — your SageMaker execution role needs `bedrock:InvokeModel` permission. SageMaker notebooks usually have this if you've enabled Bedrock access.
5. **Python packages** — installed in the first notebook cell (boto3, ipywidgets, Pillow, python-docx, pandas, openpyxl)

---

## Quick Start (Step by Step)

### Step 1: Upload files to SageMaker

Upload the entire `MAIN/` folder to your SageMaker notebook's file browser. You should have:
```
your-workspace/
├── sagemaker_agent.py
├── chat.ipynb
├── opencode.json        (optional config)
└── skills/
    └── review/
        └── SKILL.md     (example skill)
```

### Step 2: Open `chat.ipynb`

Double-click `chat.ipynb` in the SageMaker file browser to open it.

### Step 3: Run Cell 1 — Install dependencies

```python
!pip install -q boto3 ipywidgets Pillow python-docx pandas openpyxl
```

This installs all required packages. Only needed once per notebook instance.

### Step 4: Run Cell 2 — Configure

A settings panel appears with dropdowns for:
- **Model** — which Claude model to use (default: Claude 3 Haiku — cheapest and fastest)
- **Temperature** — 0.0 for deterministic, higher for creative
- **Thinking** — extended reasoning mode (slower but better for complex tasks)
- **Max Turns** — how many tool-use rounds per message (default: 30)
- **Workspace** — directory for file operations (default: `.` = current directory)
- **Mock Mode** — test the UI without calling Bedrock API

### Step 5: Run Cell 3 — Launch

The chat interface appears. Type a message in the text box and click **Send** (or press Enter).

### Step 6: Start chatting

Try: `"List all files in this directory"` — the agent will use the `list_dir` tool and show you the results.

---

## How the Chat Works

```
You type a message
    ↓
Agent sends your message + conversation history to Bedrock Claude
    ↓
Claude responds — either with text or a tool call (e.g., "I'll read that file")
    ↓
If tool call: agent executes the tool locally, sends result back to Claude
    ↓
Claude processes the result and responds with more text or another tool call
    ↓
This loop continues until Claude gives a final text response (up to Max Turns)
    ↓
You see the full response in the chat window
```

**Important:** The AI doesn't execute code on its own. It calls **tools** that you can see and (optionally) approve. You control what's allowed via the "Require Approval" toggle in the UI.

---

## How It Works Internally

If you want to understand what's happening under the hood, here's how the pieces fit together.

### There is no terminal

This app does **NOT** open a terminal or command line. Everything runs as **Python code inside the Jupyter notebook kernel**. When you open `chat.ipynb` and run the cells, Python code executes in the background — creating the chat UI, handling your messages, calling the AWS API, and executing tools.

### The two files

| File | What it is |
|------|-----------|
| `sagemaker_agent.py` | A Python module (~6000 lines) that contains ALL the agent logic: tool functions, security checks, the AI conversation loop, the chat UI widgets, etc. |
| `chat.ipynb` | A thin Jupyter notebook that imports `sagemaker_agent.py` and calls `create_chat_ui()` to display the chat interface. |

When you run `chat.ipynb`, it does:
```python
from sagemaker_agent import CONFIG, create_chat_ui
# ... apply your settings ...
create_chat_ui()  # ← this creates the chat box and buttons
```

### What `create_chat_ui()` does

It creates `ipywidgets` — interactive Python widgets that render in the notebook:
- A **text input box** where you type messages
- A **Send button** (Enter also works)
- An **output area** that shows the conversation
- Toggle buttons for Plan Mode, Require Approval, Dark Mode
- A status bar showing model, cost, token usage

These are all Python objects — not a web page, not a terminal. They render natively in Jupyter.

### What happens when you click Send

1. Your text goes to the `Agent` class in `sagemaker_agent.py`
2. The Agent builds a message list (system prompt + conversation history + your message)
3. It calls **AWS Bedrock API** via `boto3` — this sends the messages to Claude (the AI model)
4. Claude responds with either:
   - **Plain text** → displayed in the chat
   - **A tool call** → e.g., `{"tool": "read_file", "args": {"path": "main.py"}}`
5. If it's a tool call, the Agent finds the matching Python function (e.g., `tool_read_file()`) and runs it
6. The tool result is added to the conversation, and steps 3-5 repeat
7. When Claude finally responds with plain text (no more tool calls), the loop ends

### How the `bash` tool works (no terminal needed)

When the AI calls the `bash` tool with a command like `git status`, here's what happens:

```python
# Inside sagemaker_agent.py (simplified)
import subprocess

def tool_bash(args):
    command = args["command"]  # e.g., "git status"
    # Security check: is this command allowed?
    SecurityManager.validate_bash(command)
    # Run it using Python's subprocess module
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
    return result.stdout + result.stderr
```

`subprocess.run()` is a Python built-in that runs a shell command **programmatically** — it spawns a hidden process, captures the output as a string, and returns it. You never see a terminal window. The output goes back to Claude as text, and Claude summarizes it for you.

**Same for `python_exec`:** when the AI wants to run Python code, it doesn't open a Python shell. It calls `exec()` within a sandboxed environment inside the same Jupyter kernel, captures the output, and returns it.

### How file tools work

```python
# Simplified examples from sagemaker_agent.py

def tool_read_file(args):
    path = args["path"]
    # Security: must be inside workspace directory
    safe_path = SecurityManager.validate_path(path)
    with open(safe_path) as f:
        return f.read()

def tool_write_file(args):
    path = args["path"]
    content = args["content"]
    safe_path = SecurityManager.validate_path(path)
    # Save backup snapshot before writing
    SnapshotManager.save(safe_path)
    with open(safe_path, "w") as f:
        f.write(content)
    return f"Wrote {len(content)} bytes to {path}"
```

Every tool is just a Python function that does something locally (read a file, run a command, create a document) and returns the result as a string.

### How the AI picks tools

You never tell the AI "use the read_file tool". You say "read main.py" in plain English. The AI (Claude) has been given a description of all 22 tools in the system prompt. Based on your request, it decides which tool to call and with what arguments. This is called **tool use** (or "function calling") — it's a built-in capability of Claude models.

### Summary diagram

```
┌─────────────────────────────────────────────┐
│  Jupyter Notebook (chat.ipynb)              │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  Chat UI (ipywidgets)               │    │
│  │  [Text Input] [Send] [Plan Mode]    │    │
│  │  [Conversation Output Area]         │    │
│  └──────────┬──────────────────────────┘    │
│             │ your message                   │
│             ▼                                │
│  ┌─────────────────────────────────────┐    │
│  │  Agent (sagemaker_agent.py)         │    │
│  │                                     │    │
│  │  ┌──────────┐   ┌───────────────┐   │    │
│  │  │ Bedrock  │◄─►│ Claude Model  │   │    │
│  │  │ API call │   │ (in AWS cloud)│   │    │
│  │  └──────────┘   └───────────────┘   │    │
│  │       │                              │    │
│  │       ▼ tool calls                   │    │
│  │  ┌──────────────────────────────┐   │    │
│  │  │ Tool Functions (22 tools)    │   │    │
│  │  │ read_file, bash, grep, ...   │   │    │
│  │  │ All run locally as Python    │   │    │
│  │  └──────────────────────────────┘   │    │
│  │       │                              │    │
│  │       ▼ security checks              │    │
│  │  ┌──────────────────────────────┐   │    │
│  │  │ SecurityManager              │   │    │
│  │  │ Validates every tool call    │   │    │
│  │  └──────────────────────────────┘   │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

---

## All 22 Tools Explained

Each tool is something the agent can do. You don't call tools directly — you describe what you want in plain English, and the agent picks the right tool.

### File Operations (6 tools)

| Tool | What it does | Example prompt |
|------|-------------|----------------|
| `read_file` | Read contents of a file | "Read main.py" |
| `write_file` | Create or overwrite a file | "Create a file called hello.py with a hello world function" |
| `edit_file` | Make targeted edits to a file (find & replace) | "In app.py, change the port from 8080 to 3000" |
| `glob` | Find files matching a pattern | "Find all `.csv` files in the data folder" |
| `grep` | Search file contents for text/regex | "Search for 'TODO' in all Python files" |
| `list_dir` | List files and folders in a directory | "Show me what's in the src/ directory" |

### Code Execution (2 tools)

| Tool | What it does | Example prompt |
|------|-------------|----------------|
| `bash` | Run a shell command | "Run `git status`" or "Run `ls -la`" |
| `python_exec` | Execute Python code and return output | "Calculate the first 20 Fibonacci numbers" |

**Note:** Both tools have security restrictions — dangerous commands are blocked (see Security section).

### Document Creation (5 tools)

| Tool | What it does | Example prompt |
|------|-------------|----------------|
| `create_word` | Create a `.docx` Word document | "Create a Word doc summarizing the meeting notes" |
| `create_excel` | Create a `.xlsx` Excel spreadsheet | "Create an Excel file with employee salaries" |
| `create_markdown` | Create a `.md` Markdown file | "Write a README.md for this project" |
| `create_notebook` | Create a `.ipynb` Jupyter Notebook with code/markdown cells | "Create a notebook that loads and plots data" |
| `create_pdf` | Create a `.pdf` document | "Create a PDF report with a title page and table" |

### Charts (1 tool)

| Tool | What it does | Example prompt |
|------|-------------|----------------|
| `create_chart` | Create bar, line, pie, or scatter charts (saves as PNG) | "Create a bar chart of monthly sales" |

### Vision (1 tool)

| Tool | What it does | Example prompt |
|------|-------------|----------------|
| `view_image` | Look at an image and describe/analyze it | "Look at screenshot.png and tell me what you see" |

### Search (1 tool)

| Tool | What it does | Example prompt |
|------|-------------|----------------|
| `semantic_search` | AI-powered code search using Bedrock Titan embeddings — finds code by meaning, not just keywords | "Find where user authentication is handled" |

### Planning (2 tools)

| Tool | What it does | Example prompt |
|------|-------------|----------------|
| `todo_write` | Create/update a task list | "Create a plan for building a REST API" |
| `todo_read` | Read the current task list | "Show me the current plan" |

### Web (1 tool)

| Tool | What it does | Example prompt |
|------|-------------|----------------|
| `web_fetch` | Fetch a URL and extract text content | "Fetch https://example.com and summarize it" |

**Note:** Has SSRF protection — can't fetch internal/private network URLs.

### Skills (1 tool)

| Tool | What it does | Example prompt |
|------|-------------|----------------|
| `skill` | List available skills or load one by name | "List available skills" or "Load the code-review skill" |

### Sub-agents (1 tool)

| Tool | What it does | Example prompt |
|------|-------------|----------------|
| `task` | Spawn a child agent with specific capabilities for a sub-task | "Explore the codebase and find all API endpoints" (agent may spawn an explore sub-agent) |

### Interactive (1 tool)

| Tool | What it does | Example prompt |
|------|-------------|----------------|
| `ask_user` | Ask you a question mid-task when the agent needs clarification | (Agent calls this automatically — you'll see a question appear in chat) |

---

## Slash Commands

Slash commands are typed directly in the chat input box (not as natural language). They start with `/`.

| Command | What it does | Example |
|---------|-------------|---------|
| `/skills` | List all discovered skills | `/skills` |
| `/skill use <name>` | Activate a skill for the session | `/skill use code-review` |
| `/skill clear` | Deactivate all skills | `/skill clear` |
| `/commands` | List custom slash commands from `opencode.json` | `/commands` |
| `/cost` | Show token usage and cost breakdown | `/cost` |
| `/revert <file>` | Restore a file to its state before the agent edited it | `/revert app.py` |
| `/revert all` | Restore all files the agent modified | `/revert all` |
| `/compact` | Compress conversation history to free up context window | `/compact` |
| `/save` | Save current session to disk | `/save` |

---

## Skills System

### What are Skills?

Skills are **instruction files** that tell the AI how to behave for a specific task. When you activate a skill, its instructions get added to the AI's system prompt. This is like giving the AI a reference card to follow.

**Example:** The included `code-review` skill tells the AI to check for security issues, code quality, performance, and testing when reviewing code.

### How to Use the Included Skill

1. Make sure `skills/review/SKILL.md` exists in your workspace
2. Type `/skills` in the chat — you should see `code-review` listed
3. Type `/skill use code-review` — the skill is now active
4. Ask: "Review my app.py file" — the AI will follow the code review checklist
5. When done, type `/skill clear` to deactivate

### How to Create Your Own Skill

**Step 1:** Create a folder and file:
```
skills/
  my-skill-name/
    SKILL.md
```

**Step 2:** Write `SKILL.md`:
```markdown
---
name: my-skill-name
description: A brief description of what this skill does
---

## Instructions

When the user asks you to [do something], follow these steps:

1. First, do X
2. Then, do Y
3. Finally, do Z

## Rules

- Always check for A before doing B
- Never do C without asking first
- Format output as a table
```

The `---` section at the top (YAML frontmatter) is optional but recommended. The `name` must match what you use in `/skill use <name>`.

**Step 3:** Verify and use:
```
/skills              → should show your new skill
/skill use my-skill-name  → activate it
```

### Concrete Example: Creating a "Documentation Writer" Skill

Create `skills/doc-writer/SKILL.md`:
```markdown
---
name: doc-writer
description: Generate professional documentation for Python projects
---

## Documentation Writer

When asked to document code:

1. Read the source file completely
2. Identify all classes, functions, and their parameters
3. Write a structured markdown document with:
   - Module overview (1 paragraph)
   - Table of all classes with descriptions
   - Table of all functions with parameters and return types
   - Usage examples for the main entry points
4. Use clear, simple language — assume the reader is a junior developer

## Style Rules
- Use ## for sections, ### for subsections
- Put function signatures in code blocks
- Include type annotations in parameter tables
```

Then: `/skill use doc-writer` and ask "Document the main.py file"

### Where Skills Are Discovered

The agent searches these directories for `**/SKILL.md` files:
- `./skills/` (your workspace)
- `.opencode/skill/`
- `.opencode/skills/`
- `.claude/skills/`

---

## MCP (Model Context Protocol)

### What is MCP?

MCP is a standard way to connect **external tool servers** to the AI agent. Think of it as "plugins" — you can add new capabilities (like database access, API calls, or specialized tools) without modifying the agent code.

An MCP server is a small program that exposes tools. The agent connects to it, discovers what tools are available, and can call them during conversations.

### When Would You Use MCP?

- You want the agent to query a **database** (connect a database MCP server)
- You want the agent to call your **internal APIs** (connect an API MCP server)
- You want the agent to use a **specialized tool** someone else built (connect their MCP server)
- You want to share tools across multiple AI agents (MCP is a standard protocol)

**If you don't need external tools, you can ignore MCP entirely.** The 21 built-in tools cover most use cases.

### How to Set Up MCP

MCP servers are configured in `opencode.json`. There are two types:

#### Type 1: Local Server (runs as a subprocess)

The agent spawns a Python/Node.js process and communicates via stdin/stdout.

**Step 1:** Write an MCP server (example: `my_mcp_server.py`):
```python
import json
import sys

def handle_request(request):
    method = request.get("method")
    if method == "initialize":
        return {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "my-server"}}
    elif method == "tools/list":
        return {"tools": [
            {"name": "greet", "description": "Say hello to someone", "inputSchema": {
                "type": "object", "properties": {"name": {"type": "string", "description": "Person's name"}}, "required": ["name"]
            }}
        ]}
    elif method == "tools/call":
        tool_name = request["params"]["name"]
        args = request["params"]["arguments"]
        if tool_name == "greet":
            return {"content": [{"type": "text", "text": f"Hello, {args['name']}!"}]}
    return {}

# JSON-RPC over stdin/stdout
for line in sys.stdin:
    request = json.loads(line)
    result = handle_request(request)
    response = {"jsonrpc": "2.0", "id": request.get("id"), "result": result}
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()
```

**Step 2:** Add to `opencode.json`:
```json
{
  "mcp": {
    "my-server": {
      "type": "local",
      "command": ["python", "my_mcp_server.py"],
      "env": {},
      "timeout": 30
    }
  }
}
```

**Step 3:** Restart the agent. On startup, it will:
1. Spawn the `my_mcp_server.py` process
2. Run the MCP handshake (initialize)
3. Discover the `greet` tool via `tools/list`
4. Register it as `mcp_my_server_greet` in the agent

**Step 4:** Ask the agent: "Greet Winston" — it will call `mcp_my_server_greet` with `{"name": "Winston"}` and return "Hello, Winston!"

#### Type 2: Remote Server (HTTP endpoint)

The agent sends HTTP POST requests to a URL.

```json
{
  "mcp": {
    "remote-api": {
      "type": "remote",
      "url": "https://my-mcp-endpoint.example.com/rpc",
      "headers": {"Authorization": "Bearer YOUR_TOKEN"},
      "timeout": 30
    }
  }
}
```

Same flow — the agent discovers tools from the remote server and registers them.

### MCP Tool Naming

Tools from MCP servers get prefixed: `mcp_<server-name>_<tool-name>`

If server `my-server` exposes tools `search` and `fetch`, they become:
- `mcp_my_server_search`
- `mcp_my_server_fetch`

### Disabling an MCP Server

Add `"enabled": false` to the server config without removing it:
```json
{
  "mcp": {
    "my-server": {
      "type": "local",
      "command": ["python", "server.py"],
      "enabled": false
    }
  }
}
```

### Safety

- Stdio: timeout-based readline prevents deadlocks
- HTTP: 2MB response limit
- Name collisions with built-in tools are detected and warned

---

## Sub-Agents

### What are Sub-Agents?

Sub-agents are **child AI sessions** that the main agent can spawn to handle specific tasks. Each sub-agent has its own conversation, restricted tools, and turn limit. When it finishes, it returns a summary to the main agent.

**You don't call sub-agents directly.** The main agent decides when to use them. However, you can influence this by how you phrase your request, or by enabling Plan Mode.

### Agent Types

| Type | What it can do | Tools | Max Turns | When it's used |
|------|---------------|-------|-----------|---------------|
| **build** | Full development — read, write, execute | All 22 tools | 25 | "Build a REST API", "Implement feature X" |
| **plan** | Analysis only — can read but not modify | read_file, glob, grep, list_dir, semantic_search, view_image, todo_write, todo_read | 15 | "Analyze the architecture", "Review this code" |
| **explore** | Fast search — minimal tools for speed | read_file, glob, grep, list_dir, semantic_search | 10 | "Find all API endpoints", "Search for auth code" |
| **general** | Research + some execution | read_file, glob, grep, list_dir, bash, python_exec, semantic_search, view_image | 15 | "Research how this module works and write a summary" |

### Examples That Trigger Sub-Agents

| Your prompt | Agent likely spawns |
|-------------|-------------------|
| "Explore the codebase and find all database queries" | `explore` sub-agent |
| "Review main.py for security issues" | `plan` sub-agent |
| "Build a Flask API with CRUD endpoints" | `build` sub-agent |
| "Research how the auth system works across all files" | `general` sub-agent |

### Plan Mode

When Plan Mode is toggled ON in the UI:
- The main agent is restricted to read-only tools
- All sub-agents are forced to `plan` type
- Useful for safe exploration without risk of file changes

### Customizing Sub-Agents

In `opencode.json`:
```json
{
  "agents": {
    "explore": {
      "max_turns": 20
    },
    "build": {
      "max_turns": 50
    }
  }
}
```

### Depth Limit

Sub-agents can spawn their own sub-agents, but only up to 2 levels deep (configurable via `subagent_max_depth` in config). This prevents runaway chains.

---

## Architecture Concepts

If you've seen tools like Claude Code, OpenCode, or Cursor, you may have encountered terms like "skills", "MCP", "hooks", "agents", and "plugins". Here's how they all relate and what our agent supports.

### The 8 Concepts Explained

| Concept | What It Is | Analogy |
|---------|-----------|---------|
| **Skill** | A markdown file with instructions loaded into the AI's prompt | A **recipe card** the AI follows |
| **Command** | A slash shortcut that triggers an action | A **keyboard shortcut** |
| **Rule** | Always-on instructions baked into the system prompt | A **company policy** |
| **Context** | A switchable behavior mode (dev vs review vs research) | A **hat you wear** |
| **MCP Server** | An external program that gives the AI new tools | A **USB device** you plug in |
| **Hook** | A trigger that runs a script before/after tool execution | A **doorbell** (automatic) |
| **Agent** | An isolated child AI session spawned for a specific task | A **contractor** you hire |
| **Plugin** | A bundle that installs skills+commands+hooks together | An **app from the app store** |

### The Key Distinction

```
Skills / Rules / Contexts  = change what the AI KNOWS    (system prompt text)
MCP Servers                = change what the AI CAN DO   (new tools)
Hooks                      = automation AROUND the AI    (before/after triggers)
Agents                     = separate AI INSTANCES       (child sessions)
Plugins                    = PACKAGING of the above      (bundle for distribution)
```

### How This Maps to Our Agent

| Concept | Our Equivalent | Status |
|---------|---------------|--------|
| **Skill** | `skills/name/SKILL.md` + SkillManager | Have it |
| **Command** | `/skills`, `/cost`, `/revert`, `/compact`, `/save`, custom via `opencode.json` | Have it |
| **Rule** | System prompt hardcoded rules (security, tool usage, coding practices) | Have it |
| **Context** | Plan Mode toggle (restricts to read-only tools) | Have it (simpler) |
| **MCP Server** | McpManager (stdio + HTTP transports, auto tool discovery) | Have it |
| **Hook** | Not implemented | Don't need (Jupyter handles file events) |
| **Agent** | `task` tool with 4 types: build, plan, explore, general | Have it |
| **Plugin** | Not applicable | N/A (single-file architecture) |

### Agent vs Plan Mode

These are **not** the same thing:

| | Plan Mode | Plan Agent |
|---|---|---|
| **What** | A toggle that restricts the **main** AI to read-only tools | A **child** AI session spawned via the `task` tool |
| **Context** | Shares your conversation history | Starts fresh (only gets the task description) |
| **Interaction** | You keep chatting with it directly | It works alone and returns a summary |
| **Context window** | Uses your main context window | Has its own separate context window |
| **When to use** | You want to explore/discuss together step by step | You want to offload research/planning while freeing your context |

---

## Custom Slash Commands

### What Are They?

Custom commands let you define reusable prompt templates. Instead of typing a long instruction every time, you type `/commandname arguments`.

### How to Set Up

Add to `opencode.json`:
```json
{
  "commands": {
    "review": {
      "template": "Review this code for bugs, security issues, and performance problems:\n$ARGUMENTS",
      "description": "Code review",
      "agent": "plan"
    },
    "test": {
      "template": "Write comprehensive unit tests for:\n$ARGUMENTS",
      "description": "Generate tests"
    },
    "explain": {
      "template": "Explain this code in simple terms, suitable for a junior developer:\n$ARGUMENTS",
      "description": "Code explainer"
    }
  }
}
```

### How to Use

```
/review app.py           → expands to "Review this code for bugs... app.py"
/test my_module.py       → expands to "Write comprehensive unit tests for: my_module.py"
/explain auth.py         → expands to "Explain this code in simple terms... auth.py"
/commands                → lists all available custom commands
```

### Template Variables

- `$ARGUMENTS` — everything you typed after the command name
- `$1`, `$2` — first and second word after the command name

### Agent Routing

If `"agent"` is set (like `"plan"` in the review example), the expanded prompt is routed through that sub-agent type. This means `/review` runs in read-only mode automatically.

---

## Configuration File (`opencode.json`)

Optional file. Place in your workspace root alongside `sagemaker_agent.py`. Supports JSONC (comments with `//`).

### Full Example

```json
{
  // ── Skills ──
  "skills_dir": "./skills",
  "enable_skills": true,

  // ── Custom slash commands ──
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

  // ── MCP servers ──
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

  // ── Permission overrides ──
  "permissions": {
    "bash": "ask",
    "read_file": "allow",
    "*.env": "deny",
    "bash:rm*": "deny"
  },

  // ── Agent type overrides ──
  "agents": {
    "explore": {
      "max_turns": 20
    }
  }
}
```

If you don't create this file, the agent uses sensible defaults. You only need it if you want custom commands, MCP servers, or permission tweaks.

---

## Permission Rules

Control which tools require approval, which are auto-allowed, and which are blocked.

### Configuration

In `opencode.json` under `"permissions"`:

```json
{
  "permissions": {
    "bash": "ask",           // Always ask before running shell commands
    "python_exec": "ask",   // Always ask before running Python code
    "read_file": "allow",   // Auto-allow file reads (no approval needed)
    "write_file": "ask",    // Ask before writing files
    "*.env": "deny",        // Never allow operations on .env files
    "bash:rm*": "deny"      // Block all rm commands
  }
}
```

### Three Permission Levels

| Level | Behavior |
|-------|----------|
| `"allow"` | Tool executes immediately, no approval prompt |
| `"ask"` | Shows approval prompt in chat — you must click Yes/No |
| `"deny"` | Tool is blocked entirely — agent gets an error message |

### Pattern Matching

- `"*.env"` — matches any file ending in `.env`
- `"bash:rm*"` — matches any bash command starting with `rm`
- Tool names match exactly: `"read_file"`, `"bash"`, `"python_exec"`

### UI Toggle

The **Require Approval** toggle in the UI is a master switch:
- **OFF** (default): All tools auto-execute (fastest workflow)
- **ON**: High-risk tools (bash, python_exec, write_file, edit_file) require approval

Permission rules in `opencode.json` override the UI toggle for specific tools.

---

## Security

### Bash — 3-Layer Validation

1. **Command Allowlist** — blocks dangerous commands like `aws iam`, `curl` to external IPs, `rm -rf /`, `shutdown`, etc.
2. **Pattern Matching** — 70+ dangerous patterns checked (credential access, network exfiltration, system modification)
3. **Restricted Execution Mode** — commands run with limited privileges

### Python — 3-Layer Validation

1. **AST Analysis** — blocks `eval()`, `exec()`, `__import__()`, `compile()` and other dangerous constructs
2. **Import Hook** — allowlist of safe modules only (blocks `subprocess`, `socket`, `ctypes`, `shutil`, etc.)
3. **Secret Detection** — scans for API keys, passwords, tokens in code before execution

### Web Fetch — SSRF Protection

- Blocks private IPs: `127.x`, `10.x`, `172.16-31.x`, `192.168.x`
- Blocks cloud metadata: `169.254.169.254`, `metadata.google.internal`
- Blocks IPv6 ULA (`fc00::/7`) and link-local (`fe80::`)
- Blocks redirects to internal hosts
- 2MB response limit

### Workspace Boundary

All file operations are confined to the workspace directory. The agent cannot read or write files outside your workspace.

---

## Cost Tracking

The agent tracks token usage and estimates cost for every Bedrock API call.

- Type `/cost` to see a detailed breakdown:
  - Input tokens, output tokens, cache hits
  - Dollar amounts per model
  - Total session cost
- Running cost is displayed in the status bar at all times
- Supports pricing for 8 Bedrock models (Haiku, Sonnet, Opus variants)

**Tip:** Use Claude 3 Haiku for routine tasks (cheapest) and switch to Sonnet/Opus for complex reasoning.

---

## Snapshots & Revert

Every time the agent writes or edits a file, a backup is automatically saved to `.snapshots/`.

- `/revert <filename>` — restore a specific file to its pre-edit state
- `/revert all` — restore all files the agent modified
- Maximum 100 snapshots stored; oldest are auto-pruned

**Example:**
```
You: "Rewrite main.py to use async/await"
Agent: (rewrites main.py)
You: "That broke everything"
You: /revert main.py     ← main.py is restored to the version before the rewrite
```

---

## UI Features

| Feature | Description |
|---------|-------------|
| **Plan Mode** toggle | Restricts agent to read-only tools — safe for exploration |
| **Require Approval** toggle | Controls whether high-risk tools need your approval |
| **Auto-Compact** | Automatically compresses conversation when context reaches 90% |
| **Stop button** | Cancel AI processing mid-stream |
| **Dark mode** toggle | Switch between light and dark themes |
| **Session management** | Save, load, or start new sessions |
| **Token usage bar** | Progress bar showing how much of the context window is used |
| **Status bar** | Shows model, connection status, MCP count, cost, active skill |

---

## File Structure

```
MAIN/
├── sagemaker_agent.py    # The agent (~6000 lines, single file)
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

## Troubleshooting

### "Model not accessible" or Bedrock errors

- Check that your SageMaker IAM role has `bedrock:InvokeModel` permission
- Check that the Claude model is enabled in Bedrock console for your region (`ap-southeast-2`)
- Try switching to a different model in the config dropdown

### "Module not found" errors

Run the install cell again:
```python
!pip install -q boto3 ipywidgets Pillow python-docx pandas openpyxl
```

### Chat interface doesn't appear

- Make sure you ran cells in order (Cell 1 → Cell 2 → Cell 3)
- Check the Jupyter kernel is running (restart if needed)
- In SageMaker Studio, use the "Python 3" kernel

### Skills not showing up

- Check that the `skills/` folder is in your workspace directory
- Each skill must be in a subfolder with a `SKILL.md` file: `skills/my-skill/SKILL.md`
- Type `/skills` to see what's discovered

### MCP server won't connect

- For local servers: check that the command works manually (`python my_server.py`)
- For remote servers: check the URL is reachable from SageMaker
- Check `opencode.json` syntax (use a JSON validator)
- Look for connection status in the UI status bar

### Agent is slow

- Switch to Claude 3 Haiku (fastest and cheapest)
- Reduce Max Turns in config
- Turn off Extended Thinking
- Use `/compact` if the conversation is long

### Context window full

- Use `/compact` to compress the conversation
- Start a new session with the "New" button
- Auto-compact triggers at 90% automatically

---

## Example Prompts

| What you want | What to type |
|--------------|-------------|
| List files | "List all files in this directory" |
| Read a file | "Read main.py" |
| Search by name | "Find all Python files with 'test' in the name" |
| Search by content | "Search for 'TODO' in all files" |
| AI-powered search | "Find where user authentication is handled" |
| Edit code | "In app.py, change the port from 8080 to 3000" |
| Run a command | "Run `git status`" |
| Run Python | "Calculate the sum of numbers from 1 to 100" |
| Create Excel | "Create an Excel file with employee salary data" |
| Create Word doc | "Write a project summary document" |
| Create PDF | "Create a PDF report with a summary table" |
| Create chart | "Create a bar chart of monthly revenue" |
| Analyze image | "Look at diagram.png and explain it" |
| Fetch a URL | "Fetch https://example.com and summarize it" |
| Code review | `/skill use code-review` then "Review app.py" |
| Custom command | `/review sagemaker_agent.py` |
| Check cost | `/cost` |
| Undo edit | `/revert app.py` |
| Plan mode | Toggle Plan Mode ON, then "Analyze the architecture" |
| Sub-agent | "Explore the codebase and find all API endpoints" |
