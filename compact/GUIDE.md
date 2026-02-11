# SageMaker Coding Agent - Compact Version

## Complete Guide & Documentation

A secure AI coding assistant for AWS SageMaker - **2-file simple version**.

**Files:** `sagemaker_agent.py` + `chat.ipynb` = Everything you need!

---

# Part 1: Beginner's Guide - Understanding the Concepts

## What Is This App?

This is an **AI coding assistant** that runs in Jupyter notebooks on AWS SageMaker. You chat with it in plain English, and it helps you:

- Read and edit code files
- Run terminal commands
- Search your codebase
- Create documents (Word, Excel, Markdown)
- Plan and track multi-step tasks

Think of it like having a junior developer who can read your files and execute commands, but always asks permission before doing anything risky.

**Compact version = Same features, only 2 files!**

---

## Core Concepts Explained

### 1. What is AWS Bedrock?

**Simple explanation:** AWS Bedrock is Amazon's AI service. Instead of running an AI model on your computer, you send requests to AWS and get responses back.

```
┌─────────────┐         ┌─────────────────┐         ┌─────────────┐
│ Your Code   │  ──────►│  AWS Bedrock    │  ──────►│  Response   │
│ "Fix bug"   │         │  (Claude AI)    │         │  "Here..."  │
└─────────────┘         └─────────────────┘         └─────────────┘
```

**Why use it?**
- No need for expensive GPU hardware
- Always have the latest AI models
- Pay only for what you use

### 2. What is Claude?

Claude is the AI model made by Anthropic. It's like ChatGPT but from a different company. We use Claude because:
- It's good at coding tasks
- Available on AWS Bedrock
- Has a large context window (200K tokens = ~150K words)

### 3. What is a Tool?

A **tool** is a function that the AI can call to interact with the real world.

**Without tools:**
```
You: "What files are in this folder?"
AI: "I don't know, I can't see your computer."
```

**With tools:**
```
You: "What files are in this folder?"
AI: [calls list_dir tool]
AI: "I found: main.py, utils.py, README.md"
```

**Our 15 tools:**
| Tool | What it does | Example |
|------|--------------|---------|
| `read_file` | Read a file | "Read main.py" |
| `write_file` | Create/replace a file | "Create hello.py" |
| `edit_file` | Change part of a file | "Fix the typo on line 5" |
| `glob` | Find files by pattern | "Find all .py files" |
| `grep` | Search inside files | "Find where 'TODO' is used" |
| `list_dir` | List folder contents | "What's in this folder?" |
| `bash` | Run shell command | "Run git status" |
| `python_exec` | Execute Python code | "Calculate 2+2" |
| `create_word` | Make Word document | "Create a report.docx" |
| `create_excel` | Make Excel spreadsheet | "Create data.xlsx" |
| `create_markdown` | Make Markdown file | "Create notes.md" |
| `view_image` | Look at an image | "What's in screenshot.png?" |
| `semantic_search` | AI-powered code search | "Find authentication logic" |
| `todo_write` | Update task list | (internal planning) |
| `todo_read` | Read task list | (internal planning) |

### 4. What is the ReAct Loop?

**ReAct** = **Re**ason + **Act**

It's the pattern the AI follows:

```
┌─────────────────────────────────────────────────────────┐
│                    ReAct Loop                            │
│                                                          │
│  1. RECEIVE user message                                 │
│         ↓                                                │
│  2. THINK: "What should I do?"                          │
│         ↓                                                │
│  3. ACT: Call a tool (or respond with text)             │
│         ↓                                                │
│  4. OBSERVE: See the tool's result                      │
│         ↓                                                │
│  5. REPEAT from step 2 (or finish if done)              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Example:**
```
You: "Create a Python file that prints hello, then run it"

AI thinks: "I need to create a file, then execute it. Two steps."
AI acts: write_file("hello.py", "print('hello')")
AI observes: "File created"
AI thinks: "Now I need to run it"
AI acts: bash("python hello.py")
AI observes: "hello"
AI responds: "Done! Created hello.py and ran it. Output was 'hello'"
```

### 5. What is a Session?

A **session** is a saved conversation. It includes:
- All messages (yours and AI's)
- The conversation context

**Why sessions matter:**
```
Monday:
  You: "Help me build a login system"
  AI: [creates auth.py, starts work]
  You: [click Save Session]

Tuesday:
  You: [click Load Session]
  AI: "I remember we were building a login system. Let's continue..."
```

Without sessions, the AI forgets everything when you close the notebook.

### 6. What is Context?

**Context** = all the text the AI can "see" at once.

Claude has a **200,000 token limit** (~150,000 words). This includes:
- System prompt (instructions)
- All previous messages
- Tool results

**What happens when context fills up:**
- 80%: Agent warns you
- 90%: Stronger warning
- 95%: Critical - about to lose old messages
- 100%: Old messages get trimmed (forgotten)

### 7. What is the Approval System?

Some actions are dangerous (writing files, running commands). The approval system asks you before doing them:

```
┌─────────────────────────────────────────┐
│  Approval Required                       │
│                                          │
│  Tool: write_file                        │
│  File: important_data.py                 │
│  Content: [preview...]                   │
│                                          │
│  [Approve]  [Deny]                       │
└─────────────────────────────────────────┘
```

- **Approve**: AI does the action
- **Deny**: AI skips it, continues with other tasks

### 8. What is a Doom Loop?

A **doom loop** is when the AI gets stuck repeating the same action:

```
Turn 1: read_file("config.py")
Turn 2: read_file("config.py")  ← same thing
Turn 3: read_file("config.py")  ← stuck in a loop!
```

**Why it happens:**
- AI is confused
- The task is impossible
- File doesn't exist but AI keeps trying

**Our solution:** After 3 identical calls, the agent stops and warns you.

### 9. What is the Audit Log?

A **record of everything** the AI did:

```
audit_logs/2024-01-29_session123.jsonl:

{"timestamp": "10:30:00", "action": "read_file", "file": "main.py"}
{"timestamp": "10:30:05", "action": "edit_file", "file": "main.py", "approved": true}
{"timestamp": "10:30:10", "action": "bash", "command": "git status"}
```

**Why it matters:**
- Security: See exactly what happened
- Debugging: Find where things went wrong
- Compliance: Prove what the AI did/didn't do

### 10. What is Workspace Boundary?

The AI can **only access files in your project folder**. It cannot:
- Read `/etc/passwd` (system files)
- Access `~/.ssh/` (your SSH keys)
- Go to `../../../` (parent directories)

This prevents accidents and security issues.

### 11. What is Mock Mode?

**Mock mode** = test without calling AWS Bedrock (no API costs).

The agent returns fake responses, useful for:
- Testing the UI
- Checking if everything is set up
- Development without burning tokens

Enable in `chat.ipynb`: Check the "Mock Mode" checkbox.

### 12. What is Streaming? (Why We Don't Have It)

**Streaming** = text appears character-by-character as AI generates it (like ChatGPT typing).

```
Without streaming:  [Wait 5 sec...] → Full response appears
With streaming:     H...e...l...l...o... → Appears letter by letter
```

**Why we don't have it:**
- ipywidgets (Jupyter) doesn't handle streaming well
- Added complexity for minimal benefit
- Agent still works, just shows full response at end

---

# Part 2: Architecture

## System Overview (Compact Version)

```
┌────────────────────────────────────────────────────────────────────────┐
│                          chat.ipynb                                     │
│                     (User Interface Notebook)                           │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ Cell 1: Install dependencies                                     │  │
│  │ Cell 2: Configuration UI (model, region, workspace, mock mode)   │  │
│  │ Cell 3: Launch agent → calls create_chat_ui()                    │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                      Chat Widget UI                              │  │
│  │  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐   │  │
│  │  │ Input Box    │  │ Output Area     │  │ Session Controls │   │  │
│  │  │ [________]   │  │ User: ...       │  │ [Save] [Load]    │   │  │
│  │  │ [Send]       │  │ AI: ...         │  │ [Clear]          │   │  │
│  │  └──────────────┘  └─────────────────┘  └──────────────────┘   │  │
│  │                                                                  │  │
│  │  ┌──────────────────────────────────────────────────────────┐   │  │
│  │  │ Approval Dialog: [Approve] [Deny]                         │   │  │
│  │  └──────────────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        sagemaker_agent.py                               │
│                      (Everything in One File!)                          │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ CONFIGURATION                                                   │   │
│  │ - Config dataclass (region, model, limits)                      │   │
│  │ - Global CONFIG instance                                        │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ SECURITY                                                        │   │
│  │ - SecurityManager (path validation, command filtering, secrets) │   │
│  │ - SECURITY global instance                                      │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ AUDIT LOGGING                                                   │   │
│  │ - AuditEntry dataclass                                          │   │
│  │ - AuditLogger class                                             │   │
│  │ - AUDIT global instance                                         │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ BEDROCK CLIENT                                                  │   │
│  │ - BedrockClient class (chat(), mock mode)                       │   │
│  │ - Talks to AWS Bedrock API                                      │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ SESSION MANAGEMENT                                              │   │
│  │ - Session dataclass                                             │   │
│  │ - SessionManager (create, save, load, list)                     │   │
│  │ - SESSIONS global instance                                      │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ CONTEXT MANAGER                                                 │   │
│  │ - Token estimation                                              │   │
│  │ - 80/90/95% warnings                                            │   │
│  │ - CONTEXT global instance                                       │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ TOOLS (15 total)                                                │   │
│  │ - tool_read_file, tool_write_file, tool_edit_file               │   │
│  │ - tool_glob, tool_grep, tool_list_dir                           │   │
│  │ - tool_bash, tool_python_exec                                   │   │
│  │ - tool_create_word, tool_create_excel, tool_create_markdown     │   │
│  │ - tool_view_image, tool_todo_write, tool_todo_read              │   │
│  │ - TOOLS registry dict                                           │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ SYSTEM PROMPT                                                   │   │
│  │ - Instructions for the AI (~40 lines)                           │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ AGENT                                                           │   │
│  │ - Agent class with run() method                                 │   │
│  │ - ReAct loop logic                                              │   │
│  │ - Doom loop detection                                           │   │
│  │ - History trimming                                              │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ CHAT UI                                                         │   │
│  │ - create_chat_ui() function                                     │   │
│  │ - ipywidgets-based interface                                    │   │
│  └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
                      ┌──────────────────────────┐
                      │     AWS Bedrock          │
                      │     (Claude AI)          │
                      └──────────────────────────┘
```

## File Structure (Just 2 Files + Folders!)

```
compact/
│
├── sagemaker_agent.py    # EVERYTHING (~1200 lines)
│   ├── Config            # Settings
│   ├── SecurityManager   # Safety checks
│   ├── AuditLogger       # Action logging
│   ├── BedrockClient     # AWS API
│   ├── SessionManager    # Save/load
│   ├── ContextManager    # Token tracking
│   ├── 15 tool functions # All tools
│   ├── SYSTEM_PROMPT     # AI instructions
│   ├── Agent             # Main loop
│   └── create_chat_ui()  # Jupyter UI
│
├── chat.ipynb            # Run this to use
│   ├── Cell 1: pip install
│   ├── Cell 2: Configuration UI
│   ├── Cell 3: Launch
│   └── Cell 4: Quick start examples
│
├── GUIDE.md              # This documentation
│
├── sessions/             # Saved conversations
│   └── *.json
│
└── audit_logs/           # Action history
    └── *.jsonl
```

## Data Flow

```
1. USER opens chat.ipynb, runs cells
   │
   ▼
2. Configuration UI appears
   │  - Select model (Claude 3.5 Sonnet, etc.)
   │  - Select region (Sydney, US East, etc.)
   │  - Set workspace folder
   │  - Enable mock mode if testing
   │
   ▼
3. USER clicks "Run" on launch cell
   │
   ▼
4. create_chat_ui() builds the interface
   │
   ▼
5. USER types message, clicks Send
   │
   ▼
6. Agent.run() starts ReAct loop
   │
   ├── BedrockClient.chat() calls AWS
   │         │
   │         ▼
   │   Claude thinks → returns text or tool calls
   │         │
   │         ▼
   │   If tool calls:
   │   ├── SecurityManager checks safety
   │   ├── Approval dialog (if write operation)
   │   ├── Tool executes
   │   ├── AuditLogger records action
   │   └── Loop continues
   │
   ▼
7. Final response displayed
   │
   ▼
8. USER can Save/Load/Clear session
```

---

# Part 3: User Interaction

## Configuration UI (in chat.ipynb)

When you run cell 2, you see:

```
┌────────────────────────────────────────────────────┐
│ ⚙️ Agent Configuration                             │
│                                                    │
│ Model:     [Claude 3.5 Sonnet v2 (Recommended) ▼] │
│ Region:    [Sydney (ap-southeast-2)            ▼] │
│ Workspace: [.                                   ] │
│ Max Turns: [═══════════●══] 30                    │
│ ☐ Mock Mode (test without API)                    │
│                                                    │
│ Configure settings above, then run the next cell. │
└────────────────────────────────────────────────────┘
```

## Chat Widget UI

After running cell 3:

```
┌────────────────────────────────────────────────────┐
│ SageMaker Coding Agent                             │
│ Secure AI assistant | 15 tools | Session mgmt     │
├────────────────────────────────────────────────────┤
│ Session: [New Session ▼] [Load] ☐ Dark Mode        │
├────────────────────────────────────────────────────┤
│ Temperature: [═══●════] 0.5  ☐ Extended Thinking   │
│ Think Budget: [═══════●] 4096                      │
├────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────┐│
│ │ [10:30] You:                                   ││
│ │ List files in this directory                   ││
│ │                                                ││
│ │ [10:30] Agent:                                 ││
│ │ [Calling list_dir...]                          ││
│ │ [list_dir result]:                             ││
│ │ [DIR]  src/                                    ││
│ │ [FILE] main.py (1,234 bytes)                   ││
│ │ ...                                            ││
│ └────────────────────────────────────────────────┘│
├────────────────────────────────────────────────────┤
│ [Type your message...                            ] │
│ [Send] [Clear] [Save Session]    Ready (15% ctx)  │
└────────────────────────────────────────────────────┘
```

## Live Controls (No Restart Required!)

| Control | What it does |
|---------|--------------|
| **Temperature** | Slider 0.0-1.0 - Adjusts creativity in real-time |
| **Extended Thinking** | Checkbox - Enables deep reasoning mode |
| **Think Budget** | Slider 1024-16000 - Tokens for thinking (when enabled) |
| **Dark Mode** | Checkbox - Toggles dark theme instantly |

**Note:** When Extended Thinking is enabled, temperature is automatically set to 1.0 (required by Claude).

## Buttons Explained

| Button | What it does |
|--------|--------------|
| **Send** | Send your message to the agent |
| **Clear** | Reset conversation, start fresh |
| **Save Session** | Save conversation to `sessions/` folder |
| **Load** | Load selected session (displays all saved messages) |
| **Approve** | Allow agent to do the action (in approval dialog) |
| **Deny** | Block the action (in approval dialog) |

## Dark Mode

Toggle the **Dark Mode** checkbox for a dark-themed interface:

| Mode | User Messages | Agent Messages | Tool Results | System Messages |
|------|--------------|----------------|--------------|-----------------|
| Light | Light blue | Light gray | Orange tint | Light red |
| Dark | Dark blue | Dark gray | Brown | Dark red |

The background and all message colors adapt instantly when toggled.

## Progress Visibility

As the agent works, you see **real-time progress** in the output:

```
[Calling glob...]
[glob result]:
./main.py
./utils.py
./tests/test_main.py

[Calling read_file...]
[read_file result]:
     1→import os
     2→import sys
     ...

Agent: I found 3 Python files. Here's the content of main.py...
```

This helps you:
- Know the agent is working (not stuck)
- See exactly what tools are being called
- Understand what data the agent is seeing
- Debug issues if something goes wrong

## What Happens When...

### You Send a Message While Agent is Working

**Current behavior: You must wait.**

The agent runs synchronously. When processing:
1. Status shows "Processing..."
2. You see tool calls in real-time (`[Calling grep...]`, `[grep result]:...`)
3. You CAN click Approve/Deny if asked
4. When done, status returns to "Ready"

### You Click Clear

- Conversation history erased
- Output area cleared
- Session file NOT deleted (you can still load it)

### You Click Save Session

- Current conversation saved to `sessions/` folder
- Dropdown updated with new session
- You can load it later

### You Click Load

- Selected session restored from file
- **All saved messages displayed** in chat window:
  - User messages
  - Agent responses
  - Tool calls and results
- Message count shown: "Loaded session: Title (X messages)"
- Continue where you left off with full context

## Limitations

| Feature | Status |
|---------|--------|
| Stop/Cancel mid-task | Not available |
| Background execution | Not available - UI blocks |
| Streaming (typing effect) | Not available |
| Multiple conversations | One at a time |
| Auto-save | Manual only |

---

# Part 4: Security

## What's Protected

### Workspace Boundary
Agent can ONLY access files in your project folder.

**Blocked:** `/etc/passwd`, `~/.ssh/`, `../../../`
**Allowed:** `./main.py`, `./src/utils.py`

### Sensitive Files (Always Blocked)
- `.env`, `.env.local`, `.env.production`
- `credentials.json`, `secrets.json`
- SSH keys (`id_rsa`, `id_ed25519`)
- `.netrc`, `.npmrc`, `.pypirc`

### Secret Detection
Warns before saving files containing:
- API keys
- Passwords
- AWS credentials
- JWT tokens
- Private keys
- Database URLs

### Dangerous Commands (Blocked)
- `rm -rf /` - Delete everything
- `sudo` - Privilege escalation
- `curl | bash` - Remote code execution
- `dd if=` - Direct disk access

### Audit Trail
Every action logged to `audit_logs/` with:
- Timestamp
- Tool name
- Parameters
- Result
- User approval status
- Hash for integrity

---

# Part 5: Configuration Options

## In chat.ipynb UI

| Setting | Options | Description |
|---------|---------|-------------|
| **Model** | Claude 3.5 Sonnet v2, Sonnet, Opus, Haiku | Which AI model |
| **Region** | Sydney, US East, US West, Frankfurt, Tokyo, Singapore | AWS region |
| **Workspace** | Any path | Folder for file operations |
| **Max Turns** | 5-100 | Max ReAct iterations |
| **Temperature** | 0.0 - 1.0 | Creativity control (0=deterministic, 1=creative) |
| **Extended Thinking** | On/Off | Enable deep reasoning mode |
| **Thinking Budget** | 1024 - 16000 | Tokens allocated for thinking (when enabled) |
| **Mock Mode** | On/Off | Test without API calls |

### Model Parameters Explained

**Temperature (0.0 - 1.0)**
- `0.0`: Deterministic, same answer every time
- `0.5`: Balanced creativity
- `1.0`: Maximum creativity/randomness

**Extended Thinking**
When enabled, Claude spends more time "thinking" before responding. Useful for:
- Complex multi-step problems
- Code architecture decisions
- Debugging tricky issues

**Thinking Budget**
Controls how many tokens Claude can use for internal reasoning (1024-16000). Higher = deeper thinking but slower responses.

## In sagemaker_agent.py (defaults)

| Setting | Default | Description |
|---------|---------|-------------|
| `region` | `ap-southeast-2` | Sydney |
| `model_id` | Claude 3.5 Sonnet v2 | Best model |
| `max_tokens` | 4096 | Per response |
| `max_history` | 20 | Before trimming |
| `max_output_chars` | 5000 | Tool output limit |

---

# Part 6: Quick Start

## Setup (One Time)

1. **Copy files to SageMaker:**
   - `sagemaker_agent.py`
   - `chat.ipynb`

2. **Open `chat.ipynb`**

3. **Run Cell 1** (install dependencies):
   ```
   !pip install -q boto3 ipywidgets Pillow python-docx pandas openpyxl
   ```

4. **Make sure Bedrock access is enabled:**
   - AWS Console → Bedrock → Model access
   - Enable Claude models

## Daily Usage

1. Open `chat.ipynb`
2. Run Cell 2 (configuration) - adjust settings if needed
3. Run Cell 3 (launch) - chat widget appears
4. Start chatting!

## Example Prompts

```
"List all files here"
"Read main.py"
"Find all TODO comments"
"Create a hello world Python script"
"Run git status"
"Create an Excel file with sample employee data"
"Help me fix the bug on line 42"
```

---

# Part 7: Troubleshooting

| Problem | Solution |
|---------|----------|
| "Access denied" from Bedrock | Enable Claude in AWS Bedrock console |
| "Path outside workspace" | Use relative paths, check workspace setting |
| "Must read file before writing" | Call read_file first, then write/edit |
| "Command blocked" | Security blocking dangerous command |
| Agent stuck / repeating | Doom loop - rephrase your request |
| Context warnings | Save session, start fresh conversation |

---

# Part 8: Complete vs Compact Comparison

| Aspect | Complete Version | Compact Version |
|--------|-----------------|-----------------|
| **Files** | ~15 files | **2 files** |
| **Lines of code** | ~2000 across files | ~1200 in one file |
| **Features** | All 15 tools | All 15 tools |
| **Security** | Full | Full |
| **Sessions** | Yes | Yes |
| **Audit** | Yes | Yes |
| **Config UI** | No | **Yes** |
| **Maintainability** | Better (modular) | Harder (one big file) |
| **Deployment** | Copy folder | **Copy 2 files** |
| **Best for** | Teams, long-term | Quick setup, sharing |

**Both versions have IDENTICAL functionality!**

---

# Part 9: Test Results

Both versions pass all 10 comprehensive tests with 5+ step flows:

| Test | Description | Compact | Complete |
|------|-------------|---------|----------|
| 1 | Explore codebase (glob, list_dir, read) | ✅ PASS | ✅ PASS |
| 2 | Code analysis (grep, read, multiple files) | ✅ PASS | ✅ PASS |
| 3 | Project setup with todos | ✅ PASS | ✅ PASS |
| 4 | Search and analyze patterns | ✅ PASS | ✅ PASS |
| 5 | Bash operations (git, system info) | ✅ PASS | ✅ PASS |
| 6 | Python execution (code, data) | ✅ PASS | ✅ PASS |
| 7 | Multi-file reading (5+ files) | ✅ PASS | ✅ PASS |
| 8 | Error handling (missing files, bad paths) | ✅ PASS | ✅ PASS |
| 9 | Security validation (blocked paths, commands) | ✅ PASS | ✅ PASS |
| 10 | Combined workflow (multi-tool sequence) | ✅ PASS | ✅ PASS |

**Run tests yourself:** `python test_10_cases.py`

---

## See Also

- `../complete/` - Multi-file organized version
- `../README.md` - Project overview
- `../test_10_cases.py` - Comprehensive test suite
