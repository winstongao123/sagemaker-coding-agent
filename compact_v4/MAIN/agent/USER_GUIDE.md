# SageAgent V4 — User Guide (v4.10.6)


## What's new in v4.10.6 (2026-04-28, `html` skill for design deliverables)

User asked: "Can v4 build presentation / design / flowchart HTMLs like Clara_Design_v9, clara_textract_PRESENTATION, flowcharts.html?" Yes — and now with a dedicated skill so it's reliable.

Activate with `/skill use html`. Then ask for any of:
- **Presentation HTML** — single-page slide-style, hero + section cards
- **Tabbed design doc** — sidebar nav, decision-log tables, status pills, Mermaid blocks
- **Flowchart page** — Mermaid as centrepiece, business-rule annotations
- **Architecture report** — layers, stats, comparisons (uses `v3_architecture.html` as template)

The skill ships 3 reference HTMLs inside `skills/html/references/` (copies of `Clara_Design_v9.html`, `clara_textract_v1_PRESENTATION.html`, `flowcharts.html`). The agent reads ONLY the matching reference for your request — not all three — to save tokens.

**Screenshot iteration loop** (substitutes for Playwright on SageMaker):
1. Agent writes the HTML.
2. Agent gives you the `file:///D:/...html` URL (with `#tab0` if tabbed).
3. You open + screenshot the part that's wrong, save to `<folder>/_shots/v1.png`.
4. Agent uses `view_image` on the screenshot.
5. Agent edits to fix. Loop. After 3 rounds without convergence, asks whether to keep going.

Anti-patterns enforced: no emojis, HTML IS KING (no "see docs/" pointers), no truncated tables, no lorem/placeholder, Mermaid safe syntax, final step always asks for screenshot review.

## What's new in v4.10.5 (2026-04-28, Learning_Factory pattern adoption)

User asked Codex what to learn from Learning_Factory. Codex flagged 3 prompt-only patterns worth adopting:

- **Post-compact resume protocol** — system prompt now tells the agent: after compact, do NOT ask "what would you like me to do?". Read the `[CONVERSATION SUMMARY]` block + restored TODOs + AGENT_STATUS.md + recently-read files block, and continue from the first unchecked task. Asks user only when blocked on a real decision.
- **Structured summary sections #12 + #13** — every LLM-generated compact summary now also captures **Standing Constraints** (hard rules / standing user instructions that must survive compaction) and **Critical Don't-Forget Context** (the 1-3 most important re-orientation anchors).
- **Skill self-patching 4-rule check** — was 1 rule (3+ same correction); now 4 (Repeated + Non-trivial + Generalizable + Real-pitfall-avoiding) plus explicit memory-vs-skill distinction. Stops noise patches for one-off preferences.

Deliberately NOT adopted: LF's full hook ecosystem (not a SageMaker fit), smart approval LLM judge (cost), tool-failure 5/3/8 thresholds (current 3-repeat doom-loop is already stricter — NOT loosened), heavy rollback ecosystem (local git is enough).

6 new tests in `test_v410_lf_patterns.py`. Codex PASS on first review (no fix round needed). Full v4.10.x + regression suite: 91/91 across 10 files.

## What's new in v4.10.4 (2026-04-28, sub-agent work-context handoff)

User's Codex follow-up review pointed out that v4.10.3 sub-agents only saw env-details (cwd / git HEAD / depth) but NOT the work context (current goal, active todos, changed files). If the parent forgot to brief them in the prompt, sub-agents flew blind. Fixed:

- **Sub-agents now receive a bounded handoff block** — appended after the cached SYSTEM_PROMPT boundary (so the prompt cache prefix is preserved unchanged), containing three optional sections:
  - `AGENT_STATUS.md` slice (truncated to 4,000 chars / ~1000 tokens)
  - Active todos via the existing `build_todo_restoration_message()`
  - Last 10 changed-file paths (NO diff bodies — would blow the budget)
- **Opt-out** via `CONFIG.enable_subagent_handoff = False` in `agent_config.json` if you prefer the v4.10.3 env-details-only behavior.
- **Boundary-marker sanitization** — if user-supplied AGENT_STATUS or todo content contains the literal `# === DYNAMIC ===` cache boundary marker, the handoff sanitizer replaces it before injection. Defends against future cache-split implementation changes.
- **Fail-quiet** — every section is wrapped in `try/except`. A sub-agent spawn cannot fail because handoff probing misbehaved.

11 new tests in `test_v410_subagent_handoff.py`. Codex flagged 2 edges in round 1 (chars vs bytes naming, missing sanitizer); both fixed; round 2 PASS.

## What's new in v4.10.3 (2026-04-28, production-readiness review apply)

User asked Codex for a production-readiness review of v4.10.2. Most items were already done; 4 small additions worth applying:

- **Ship-gate verifier (`compact_v4/verify_ship_zip.py`)** — run `python verify_ship_zip.py` before any release. Checks required runtime files, no forbidden artefacts (test tempdirs, caches, `.proposed/` patches), version sanity, flat-root layout. Catches the kind of test-tempdir leak that almost shipped in v4.10.2.
- **Cache-boundary regression test** — `test_v410_cache_boundary.py` (6 tests) asserts the static portion of the system prompt is byte-identical across calls and meets the Sonnet 4.5 cache threshold (1024 tokens). Future edits that accidentally inject dynamic content into the cached prefix will fail this test immediately.
- **Many-skill stress test** — verifies skill listing stays under cap with 100 skills (no truncation needed) and 1000 skills (truncation kicks in, cap honored).
- **Clearer permission denials** — when `bash` is denied, the message now explains WHY (allowlist), suggests the closest allowed alternative (if any prefix matches), and points to the right Python tool (`python_exec`, `edit_file`). Same for pattern denials.

## What's new in v4.10.2 (2026-04-28, contradiction fix)

Codex review caught a real contradiction in the system prompt: it simultaneously demanded `verify` after 3+ logic-changing edits AND told the model to SUGGEST it without auto-running. Model behaviour was unpredictable. Resolved:

- **Verify is now suggest-and-confirm by default.** After 3+ logic-changing edits the agent will say "I edited N files. Want me to run /verify (adversarial probe) before declaring done?" and wait for your reply. No more surprise verify-subagent spawns.
- **Strict mode opt-in.** Set `enforce_verify_contract: true` in `agent_config.json` for production-discipline workflows where verify must always run before completion. Default `False`.

## What's new in v4.10.1 (2026-04-28, same-day follow-up)

- **`#41b` Context Collapse (segment-level)** — after microcompact replaces stale tool outputs with markers, runs of 3+ consecutive stale tool round-trips collapse into one synthetic 2-message pair. Strict classification: thinking / image / unknown block types in the assistant message block the collapse; marker match is exact equality, not substring. Mirrors Runnable's `contextCollapse` feature gate. 12 tests, Codex PASS.
- **Default model: Haiku 4.5 → Sonnet 4.5.** Cost ~10x per token but cache activates earlier (threshold 1024 vs 4096 tokens), so multi-turn sessions partially offset. Override in `agent_config.json` via `model_id`.

## What's new in v4.10.0 (2026-04-28)

Five Runnable-parity upgrades. Each one has its own regression test file and was reviewed by Codex (gpt-5.3-codex) per phase.

- **`notebook_edit` tool** — surgically insert / replace / delete a single cell in an existing `.ipynb` without overwriting the whole file. Use this when you ask the agent to "add a cell that does X" — `create_notebook` is now reserved for brand-new notebooks. Atomic write, preserves cell IDs, returns `Error:` strings rather than raising.
- **Skill listing budget cap** — the skill list embedded in the `skill` tool description is now hard-capped at 1% of the active context window (or 2,000 tokens, whichever is smaller). When a workspace has many skills, the trailing entries collapse to `...(+N more)`. Stops the prompt cache from being blown out by skill churn.
- **Per-sub-agent env-details** — every sub-agent the parent spawns now sees a 4–6-line block: agent type, depth/max, workspace cwd, git HEAD, working-tree status. Means a fresh `verify` agent picks up a parent's worktree swap automatically. Git probes are 5s timeout, fail-quiet — they never break sub-agent spawn.
- **`context_max_tokens` auto-derives from `model_id`** — `BEDROCK_MODEL_CONTEXT_WINDOWS` maps each model to its window. When AWS exposes a 1M Bedrock variant, you change one entry in the map and `agent_config.json` `model_id`; everything else (compaction triggers, microcompact, prune) rebases automatically. You can still explicitly override `context_max_tokens` via `agent_config.json`.
- **Reactive Compact** — when Bedrock rejects a request with "prompt is too long" (which can happen even if the local token estimator says you're fine), the agent now runs microcompact (or a placeholder-summary fallback if microcompact didn't free enough), clears file-read state, and retries the same request once. Capped at 1 reactive recovery per `run()` call. From your perspective the request just succeeds.

Skill auto-load remains default OFF (the v4.9.6 fix is still in force; `test_v49_auto_trigger.py` 12/12 green). No skill loads itself unless BOTH `CONFIG.enable_skill_auto_trigger=True` AND the per-skill frontmatter has `auto_trigger: true`.



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
11. [Skills Workflow](#skills-workflow-replaces-custom-commands)
12. [Configuration File (agent_config.json)](#configuration-file-agent-config-json)
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
- Single Python file (`sagemaker_agent.py`, 8,699 lines) — no complex multi-package setup
- 25+ built-in tools (file editing, code execution, document creation, search, etc.)
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

If using `compact_v4.zip`, extract it directly into your SageMaker workspace. The zip uses a flat runtime root layout, so it should not create a nested `MAIN/agent/` wrapper. You should have:
```
your-workspace/
├── sagemaker_agent.py
├── chat.ipynb
├── AGENT_STATUS.md        (long-running handoff state)
├── memory.md             (cross-session memory, optional/auto-managed)
├── agent_config.json        (optional config)
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
| `sagemaker_agent.py` | A Python module (8,699 lines) that contains ALL the agent logic: tool functions, security checks, the AI conversation loop, the chat UI widgets, etc. |
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

You never tell the AI "use the read_file tool". You say "read main.py" in plain English. The AI (Claude) has been given a description of all 24 tools in the system prompt. Based on your request, it decides which tool to call and with what arguments. This is called **tool use** (or "function calling") — it's a built-in capability of Claude models.

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
│  │  │ Tool Functions (24 tools)    │   │    │
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

## All 25+ Tools Explained

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
| `create_notebook` | Create a NEW `.ipynb` Jupyter Notebook with code/markdown cells | "Create a notebook that loads and plots data" |
| `notebook_edit` | **V4.10.0:** Surgically edit ONE cell of an EXISTING `.ipynb` (insert/replace/delete). Atomic write, preserves cell IDs. Use this — NOT `create_notebook` — when modifying an existing notebook so you don't blow away cells you didn't touch. | "Add a new code cell after cell 3 that loads data" |
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
| `/skill use <name>` | Activate a skill for the session (lifts any prior `/unskill` block on this skill) | `/skill use code-review` |
| `/skill clear` | Deactivate all currently-active skills (sticky — they won't auto-re-match this session) | `/skill clear` |
| `/unskill <name>` | Deactivate ONE specific skill — stays off for the session even if user message would auto-match it. Lifted only by `/skill use <name>` or new session. | `/unskill clara-review` |
| `/skill suggestions` | **(V4.9.5)** List pending agent-proposed patches across all skills. See § Self-patching skills below. | `/skill suggestions` |
| `/skill apply <name>` | **(V4.9.5)** Preview a proposed patch as a unified diff. Add `--yes` to apply, `--edit` to tweak first. | `/skill apply report` then `/skill apply report --yes` |
| `/skill reject <name>` | **(V4.9.5)** Discard ALL pending proposals for a skill. Audit-logged. | `/skill reject report` |
| `/commands` | List custom slash commands from `agent_config.json` | `/commands` |
| `/cost` | Show token usage and cost breakdown | `/cost` |
| `/context` | Show context/token diagnostics: top tool-output sources, duplicate file reads, and suggested action | `/context` |
| `/revert <file>` | **Preview diff** first (current → snapshot). Use `--yes` to confirm. | `/revert app.py` then `/revert app.py --yes` |
| `/revert all --yes` | Restore all files the agent modified (destructive, requires `--yes`) | `/revert all --yes` |
| `/diffs` | Summary of session edits per file | `/diffs` |
| `/diffs last` | Show most recent unified diff | `/diffs last` |
| `/diffs <file>` | Show last 3 diffs matching filename substring | `/diffs app.py` |
| `/regression` | **Fast "did I break anything" check** — prints `git diff HEAD --stat` + session edit summary + suggested test command | `/regression` |
| `/done [full\|quick]` | **Pre-ship gate:** runs simplify → verify, produces READY-TO-SHIP / NEEDS-WORK / BLOCKED verdict | `/done full` |
| `/phase <text>` | Set current work phase shown in status bar and token display | `/phase refactoring auth` |
| `/phase clear` | Clear the phase indicator | `/phase clear` |
| `/status` | Show the durable long-running task handoff file (`AGENT_STATUS.md`) | `/status` |
| `/status init` | Create the default `AGENT_STATUS.md` template if missing | `/status init` |
| `/status path` | Show the exact status doc path | `/status path` |
| `/checkpoint create <name>` | Save todos + file list + token stats as a named checkpoint | `/checkpoint create phase-1-complete` |
| `/checkpoint list` | List all saved checkpoints in session | `/checkpoint list` |
| `/checkpoint restore <name>` | Restore todos from checkpoint (files NOT auto-reverted — review list then `/revert` per file) | `/checkpoint restore phase-1-complete` |
| `/compact` | Compress conversation history to free up context window | `/compact` |
| `/save` | Save current session to disk | `/save` |

**Note on `/done`:** Chains `simplify` (reuse/quality/efficiency auto-fix) then `verify` (adversarial build/test/type/security) with a mandatory verdict. Refuses to claim "done" unless VERIFY = PASS. Use instead of manually running `/simplify` then `/verify`.

**Note on `/revert` safety:** All revert operations now show a diff preview first. The `--yes` flag is required to actually write files. This prevents accidental loss of current work.

**Note on cost budget:** If `CONFIG.session_cost_limit > 0`, a 4px budget bar appears under the context bar in the token display. Green <80%, orange 80–99%, red ≥100%. Agent auto-stops at 100%.

**Note on auto-commit checkpoint (v4.7.1):** Set `CONFIG.auto_commit_every = N` (e.g. 5) in agent_config.json to have v4 run `git commit -am "agent-checkpoint HH:MM:SS (auto)"` locally every N successful edits. **Never pushes** — local only. Keeps `git diff HEAD` always showing just the latest change set so you (and the agent) get a clean "what just changed" read-out. Default is 0 (disabled).

**Note on SageMaker git scope (v4.9.6):** Treat git as a local tree only. The agent can use `git status`, `git diff`, `git log`, local commits/checkpoints, and git worktrees. It should not use GitHub, `gh`, PR creation, or remote operations such as `git push`, `git pull`, `git fetch`, or `git clone` from SageMaker.

**Note on compact + todos (v4.7.1):** When v4 auto-compacts at 80% context, the TODO list is now re-injected into the post-compact message so the agent remembers its task plan. In-progress tasks shown first, completed tasks truncated to last 3. Previously the agent would lose this across compaction and need re-briefing.

**Note on long-running status (v4.9.6):** `AGENT_STATUS.md` is loaded on every top-level run when `CONFIG.enable_status_doc = True` (default). Use it for durable handoff state: current goal, standing user instructions, plan, progress, blockers, changed files, verification, and next step. This complements `todo_write` (live task list), checkpoints (snapshots of task state), and compaction summaries (conversation continuity).

**Note on `/context` (v4.9.7):** Use this during long-running tasks when the context bar climbs or the agent starts repeating reads. It shows what is consuming context, highlights duplicate full-file reads, and tells you whether to compact, switch to targeted `grep`/offset reads, or keep going.

**Note on `/regression`:** Thin wrapper — prints git diff stat, session edit counts, and a suggested test command. Does NOT run tests itself (you run them via bash) and does NOT track baselines. For automated adversarial testing use `/verify`. For a full ship gate use `/done`.

---

## Sub-agents — when, how, and what they share

V4 spawns sub-agents through the **`task` tool**. There is **no agent-team / inter-process coordination** (that's a Runnable feature for multi-Claude scenarios — irrelevant for SageMaker self-use). What you have is one parent agent that can spawn typed children. **7 agent types**, each with its own tool allowlist and prompt suffix:

| Type | When to use it | Tools | Context inheritance |
|------|---|---|---|
| `general` | Catch-all when no other type fits. Default. | All | empty start |
| `explore` | Research / search across files (3+ queries) | Read-only | empty start |
| `plan` | Design before code. 2-3 options with tradeoffs. | Read-only allowlist | empty start |
| `build` | Implement features spanning 3+ files | All + git worktree isolation | empty start |
| `verify` | Adversarial probe (tries to BREAK the code) | All | empty start |
| `review` | One focused review dimension (reuse / quality / efficiency) | Read-only | empty start |
| `fork` | Continue a thread you were just on | All | **shares parent context** (deep copy) |

**What sub-agents share with the parent:**
- The cached `SYSTEM_PROMPT` prefix (same prompt cache hit for parent + sub-agents).
- The `IterationBudget` (default 90, set via `CONFIG.max_iteration_budget`) — parent + children **collectively** can't blow this ceiling.
- The token tracker (`TOKENS` singleton) — sub-agent costs ARE counted in the running total shown in the cost bar / `/cost` / `/context` output.
- The depth limit (`CONFIG.subagent_max_depth = 2`) — no infinite recursion.
- Sonnet 4.5 model by default (or whatever `CONFIG.model_id` is). Override per-type via `CONFIG.agent_overrides[<type>]["model"]`.

**What sub-agents DON'T share:**
- Conversation history — except for `fork`, every sub-agent starts with empty `messages` ([sagemaker_agent.py:7822](compact_v4/MAIN/agent/sagemaker_agent.py)).
- Per-agent token breakdown is NOT displayed; only the running total.

**How does the sub-agent know what to read first?**
The parent passes a `prompt` argument when calling `task`. That string is the entire briefing. As of v4.10.0 the sub-agent also sees a small **env-details block** (cwd, git HEAD, working tree summary) appended after the cached prompt boundary, so a fresh `verify` agent picks up the parent's worktree state automatically. Past that, the sub-agent uses its own grep/glob/read tools to discover what it needs.

**Best-practice parent prompt:**
> "Read `D:/path/foo.py:50-200` and verify the new error handler. Tests at `tests/test_foo.py`. Original spec is in AGENT_STATUS.md Plan section. Verdict: PASS / PARTIAL / FAIL."

NOT this:
> "check the foo code"

**Do you need to say "use a sub-agent for X"?**
**No** — but you can. Three triggers:
1. The model decides to call `task` based on the system prompt heuristic: "Use task tool for complex work (3+ queries or multi-file). Use glob/grep directly for simple searches."
2. You explicitly ask: "use the explore agent for X" or "spawn a build subagent". Model honors.
3. **Verify after 3+ logic-changing edits** — as of v4.10.2 this is a **suggestion, not auto** (default). Agent says *"I edited N files. Want me to run /verify?"* and waits for your confirmation. Strict mode is opt-in via `CONFIG.enforce_verify_contract = True` in `agent_config.json`.

There is **no keyword pattern** that auto-spawns a sub-agent from your phrasing. Saying "subagent" in a question won't trigger anything. (Skill auto-trigger is a separate mechanism — also default OFF since V4.9.6.)

**Costs and metrics:**
- Sub-agent calls go through the same `BedrockClient` (or a per-type model override) → `TOKENS.add(...)` → running total shown in the cost bar.
- The cache-line indicator (e.g. "cache_read=15K, write=2K") shows only for the top-level agent (`subagent_depth == 0`) to avoid noise from sub-agent calls.
- Use `/cost` for the per-session running total, `/context` for what's currently consuming context, `/diffs` for what's been edited, `/status` for the long-running handoff file.

---

## Skills System

### What are Skills?

Skills are **instruction files** that tell the AI how to behave for a specific task. When you activate a skill, its instructions get added to the AI's system prompt. This is like giving the AI a reference card to follow.

**Example:** The included `code-review` skill tells the AI to check for security issues, code quality, performance, and testing when reviewing code.

### Activating Skills (V4.8.0+, hardened V4.9.6)

Skills require explicit activation via `/command`. They do NOT auto-trigger on keywords by default — this prevents unwanted skill activation when you're just having a conversation. (This was a real bug in V4.8: a message saying "review the X code" would silently inject a 8K-char `clara-review` audit methodology into every prompt thereafter. V4.9.6 closed it with two independent gates.)

**Two gates, both default OFF:**
1. Global flag: `CONFIG.enable_skill_auto_trigger: bool = False`
2. Per-skill frontmatter: `auto_trigger: false` (default false when key absent)

Auto-trigger only fires when **BOTH** gates are flipped to True. The `test_v49_auto_trigger.py` regression test (12 cases) enforces this — it runs as part of every release verification.

```
/skills                  ← list all available skills
/skill use <name>        ← activate a skill (stays on for ALL messages until cleared)
/skill clear             ← deactivate ALL active skills (sticky — won't auto-re-match)
/unskill <name>          ← deactivate ONE skill (sticky — won't auto-re-match this session)
/verify                  ← shortcut: auto-activates verify + runs it
/done [full|quick]       ← pre-ship gate: simplify → verify → SHIP verdict
/simplify                ← shortcut: auto-activates simplify + runs it
/security-review         ← shortcut: auto-activates security-review + runs it
```

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

**Auto-trigger policy (v4.9.6):** skills do **not** auto-load by default. Use `/skill use <name>` or a slash command. Keyword auto-trigger only works when both are true:
- `CONFIG.enable_skill_auto_trigger = True`
- the skill frontmatter explicitly says `auto_trigger: true`

This prevents accidental long-context skill injection from ordinary words in a prompt or file path.

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
- `.agent/skills/`
- `.agent/skillss/`
- `.claude/skills/`

---

## Self-patching skills (V4.9.5, opt-in)

The agent can **propose improvements to its own skills** based on what it learns during use — but it never modifies a `SKILL.md` directly. Every change goes through your review.

### When you want this

- You're using the agent for personal / dev / handy work (not regulated environment)
- You're tired of correcting the agent the same way over and over
- You want the agent to remember workflow improvements across sessions

### Enable it

```python
# In the chat UI, or in agent_config.json:
CONFIG.enable_skill_patching = True
```

Default is `False`. When OFF, the `skill_propose_patch` tool no-ops — agent suggests improvements in chat instead of writing files.

### How the loop works

1. **You correct the agent on the same skill 3+ times.** Example: "set dpi=150" repeated three times when running `/report`.
2. **Agent proposes a patch** by calling its `skill_propose_patch` tool with `name`, `reason`, and the full new SKILL.md body.
3. **The patch lands in `skills/<name>/.proposed/<timestamp>.md`** — never in the live `SKILL.md`.
4. **Banner appears in chat:** `Patch proposed for skill 'report'. Review with: /skill suggestions`
5. **You review:** `/skill suggestions` lists all pending patches. `/skill apply <name>` shows a unified diff.
6. **You decide:** `--yes` to apply, `--edit` to tweak the proposed file before applying, or `/skill reject <name>` to discard.
7. **Apply also snapshots** the live `SKILL.md` — easy rollback via existing `/revert <skill-path>`.
8. **Audit log:** every propose / apply / reject lands in `audit_logs/skill_patches.jsonl`.

### Example session

```
You: /report on Q4 sales
Agent: [creates blurry chart on Windows]
You: set dpi=150

You: /report on Q3
Agent: [forgets, blurry again]
You: dpi=150 AGAIN

You: /report on Q2
Agent: I've noticed this is the third correction on dpi.
       Proposed a patch to skills/report/SKILL.md.
       Review with: /skill suggestions

You: /skill suggestions

[System]: Pending skill patches (1):
            - report   proposed 2026-04-23 15:30:45
              reason: Windows chart-render dpi default

          Review with: /skill apply report

You: /skill apply report

[System]: Diff for skill 'report':
          ```diff
          -1. Create chart PNG with create_chart
          +1. Create chart PNG with create_chart, dpi=150
           2. Embed PNG in Word doc with create_word
          ```
          Apply? Type:
            /skill apply report --yes        (apply now)
            /skill apply report --edit       (open the proposed file and tweak first)
            /skill reject report             (discard, never apply)

You: /skill apply report --yes
[System]: ✓ Snapshot saved (use /revert if needed)
          ✓ Patch applied to skills/report/SKILL.md
          ✓ Audit logged
```

### Safety rails

| Rail | What it guarantees |
|---|---|
| Default OFF | Feature requires explicit `CONFIG.enable_skill_patching = True` |
| Propose, don't auto-apply | Patches sit in `.proposed/` until you `apply` or `reject` |
| Diff shown before apply | You see exact changes before they go live |
| Snapshot before apply | Existing `/revert <path>` undoes the change |
| Audit log per event | `audit_logs/skill_patches.jsonl` records every propose / apply / reject |
| Empty-name validation | Agent can't propose patches for non-existent skills |

### When NOT to enable

- Insurance / regulated environment where every behaviour change needs human sign-off (the proposal log helps but adds review burden)
- Multi-user shared workspace where two agents could fight over the same SKILL.md (still safe, but coordination is on you)

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

MCP servers are configured in `agent_config.json`. There are two types:

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

**Step 2:** Add to `agent_config.json`:
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
| **build** | Full development — read, write, execute | All 25+ tools | 25 | "Build a REST API", "Implement feature X" |
| **plan** | Analysis only — can read but not modify | read_file, glob, grep, list_dir, semantic_search, view_image, todo_write, todo_read | 15 | "Analyze the architecture", "Plan a refactor" |
| **explore** | Fast search — minimal tools for speed | read_file, glob, grep, list_dir, semantic_search | 10 | "Find all API endpoints", "Search for auth code" |
| **verify** | Adversarial testing — tries to BREAK the code | read_file, glob, grep, bash, python_exec, list_dir, semantic_search | 15 | `/verify` or "Test this thoroughly" |
| **review** | Security, quality, performance review | read_file, glob, grep, list_dir, semantic_search, view_image | 10 | "Review this code for issues" |
| **general** | Research + some execution | read_file, glob, grep, list_dir, bash, python_exec, semantic_search, view_image | 15 | "Research how this module works and write a summary" |
| **fork** | Inherits parent context (cache-optimized) | Parent's tools | Parent's limit | Internal — spawned for cache-efficient continuation |

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

In `agent_config.json`:
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

If you've seen tools like Claude Code, SageAgent, or Cursor, you may have encountered terms like "skills", "MCP", "hooks", "agents", and "plugins". Here's how they all relate and what our agent supports.

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
| **Command** | `/skills`, `/cost`, `/revert`, `/compact`, `/save`, custom via `agent_config.json` | Have it |
| **Rule** | System prompt hardcoded rules (security, tool usage, coding practices) | Have it |
| **Context** | Plan Mode toggle (restricts to read-only tools) | Have it (simpler) |
| **MCP Server** | McpManager (stdio + HTTP transports, auto tool discovery) | Have it |
| **Hook** | Not implemented | Don't need (Jupyter handles file events) |
| **Agent** | `task` tool with 6 types: build, plan, explore, verify, review, general | Have it |
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

## Skills Workflow (Replaces Custom Commands)

Skills are the recommended way to get structured behavior. They persist across messages and provide richer checklists than one-shot commands.

### Typical Session

```
/skill use coding-standards          ← turn on at start (stays active all session)
"write a function to parse CSV"      ← agent follows KISS/DRY/YAGNI while coding
/verify                              ← after done, runs build/lint/test/security/diff
/skill use review                    ← activate review checklist
"review the changes I just made"     ← agent follows 5-category checklist
/skill clear                         ← deactivate all skills
```

### Available Skills

| Skill | What it does |
|-------|-------------|
| `coding-standards` | KISS, DRY, YAGNI, naming, function design — turn on at session start |
| `verify` | 6-phase: build → types → lint → test → security → diff |
| `review` | 5-category code review (security/quality/performance/architecture/testing) |
| `report` | Professional report generation (charts-first) |
| `clara` | ClaRA 5-phase codebase review (~$6) |

### Skill Commands

```
/skills              ← list all available skills
/skill use <name>    ← activate (stays on until cleared)
/skill clear         ← deactivate ALL
/verify              ← shortcut: auto-activates verify + runs it
```

See `chat.ipynb` Cell 4 for detailed examples and creating custom skills.

---

## Configuration File (`agent_config.json`)

Optional file. Place in your workspace root alongside `sagemaker_agent.py`. Supports JSONC (comments with `//`).

### Full Example

```json
{
  // ── Skills ──
  "skills_dir": "./skills",
  "enable_skills": true,
  "enable_skill_auto_trigger": false,
  "enable_status_doc": true,
  "status_doc": "AGENT_STATUS.md",

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

In `agent_config.json` under `"permissions"`:

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

Permission rules in `agent_config.json` override the UI toggle for specific tools.

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

All file operations are confined to the workspace directory by default.

**Allowed Paths** (v4.5.0+): You can grant the agent **full read+write** access to additional directories outside the workspace. This is useful when the agent needs to access code, data, or documentation in sibling directories or parent folders.

Configure in `agent_config.json`:
```json
{
  "allowed_paths": [
    "/home/user/shared-libs",
    "/home/user/other-project/src"
  ]
}
```

- Paths must be absolute directories that exist on disk.
- The agent can **read and write** files, run bash commands, and use all tools on these paths — same as workspace.
- Sensitive file blocking (.env, credentials, keys) still applies within allowed_paths.
- Symlink escape protection still applies — symlinks that resolve outside both workspace and allowed_paths are blocked.
- Backward compatible: `allowed_read_paths` key is also accepted.

**Auto-Detect Environment**: The agent automatically expands access based on where it's running:
- **SageMaker**: Detects `/home/ec2-user/SageMaker/` or `/home/sagemaker-user/` and adds it to allowed_paths. You can put compact_v4 anywhere on the instance and the agent can work on any folder when you give it a path.
- **Git repo**: If your workspace is a subdirectory of a git repository, the agent adds the repo root to allowed_paths. Running from `compact_v4/` gives access to the entire repo.

No configuration needed — just works.

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

### Layout

```
Row 1: [Name] [💾Save] [Session▼] [📁Load] [+New] | [Model▼]
Row 2: [Temp] [Thinking] [Budget] [Dark] | [Plan Mode] [☑Auto-Compact] [Chat Height]
Chat:  HTML widget with internal scroll
Row 3: [Send] [Stop] [Clear] [Compact] [🧹Clean] | [Status]
Row 4: Token usage with progress bar + budget bar + cost
```

### Toggles & Sliders

| Control | What it does |
|---------|-------------|
| **Plan Mode** | Restricts agent to read-only tools — safe for exploration |
| **Require Approval** | Controls whether high-risk tools need your approval before execution |
| **Auto-Compact** | Automatically compresses conversation when context reaches 80% |
| **Dark Mode** | Switch between light and dark themes (updates all existing messages) |
| **Temp** slider | Temperature (0.0 = deterministic, 1.0 = creative) — changes take effect on next message |
| **Thinking** checkbox | Enable extended thinking mode (slower, uses more tokens, better for complex tasks) |
| **Chat Height** slider | Resize the chat window (200–1200px). Drag or use the slider |
| **Budget $** | Session cost display. Changes reflect immediately in the budget bar. Display-only — warns at 80% but does NOT stop the agent |

### Buttons

| Button | What it does |
|--------|-------------|
| **Send** | Send your message to the agent (Enter also works) |
| **Stop** | Cancel the agent mid-stream. Current tool call finishes, then stops |
| **Clear** (yellow, trash icon) | **Reset the conversation.** Saves memories from current session first, then wipes: messages, todos, file cache, read tracking, skills, tokens, checkpoints. Result: blank chat, "Ready" status — like starting fresh without restarting the kernel |
| **Compact** | Manually compress the conversation. Two-stage: prunes old tool results, then LLM-summarizes if needed. Use when context is getting full or agent starts forgetting earlier work |
| **🧹 Clean** (eraser icon) | **Delete disk artifacts** the agent created over time. Removes: `audit_logs/`, `.snapshots/`, `.code_index/`, `truncated_outputs/`, `.exec_budget.json`. **Keeps sessions** (conversation history preserved). Always safe — none of these are your code or data. Only caveat: `/revert` won't work for previous edits after cleaning since snapshots are gone |
| **💾 Save** | Save current session (messages, todos, skills, token stats, checkpoints) |
| **📁 Load** | Load a previously saved session from the dropdown |
| **+New** | Start a new session (calls Clear internally) |

### Session Management

Sessions persist your conversation across kernel restarts:
- **Save** stores: messages, model used, active skills, todos, checkpoints, token stats
- **Load** restores everything — you can pick up exactly where you left off
- Sessions are stored locally in the workspace directory
- The session dropdown shows all saved sessions by name and timestamp

### Token & Cost Display (Row 4)

The metrics bar shows:
- **📊 Tokens**: Input/output counts and API call count
- **Context bar**: Green/orange/red progress bar showing context window usage (compact triggers at 80%)
- **💰 Cost**: Session cost, last call cost, model rate, cache savings
- **Budget bar**: If budget > 0, shows spend vs limit with color coding (green < 80% < orange < 100% < red)
- **🎯 Phase**: Current work phase if set via `/phase` command

---

## File Structure

```
MAIN/
├── sagemaker_agent.py    # The agent (~6000 lines, single file)
├── sagemaker_agent.md    # Markdown copy of the above
├── chat.ipynb            # Jupyter notebook launcher
├── chat.md               # Markdown copy of the notebook
├── agent_config.json         # Configuration (optional, JSONC)
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
- Check `agent_config.json` syntax (use a JSON validator)
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
| Activate skill | `/skill use review` then "review sagemaker_agent.py" |
| Check cost | `/cost` |
| Undo edit | `/revert app.py` |
| Plan mode | Toggle Plan Mode ON, then "Analyze the architecture" |
| Sub-agent | "Explore the codebase and find all API endpoints" |
