# SageMaker Coding Agent - Complete Version

## Complete Guide & Documentation

A secure AI coding assistant for AWS SageMaker - Multi-file organized version.

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
- 80%: Agent saves checkpoint, warns you
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

---

# Part 2: Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                        (agent.ipynb)                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────┐    │
│  │ Chat Input  │  │Chat Output  │  │ Session Controls         │    │
│  │ [________]  │  │ User: ...   │  │ [Save] [Load] [Clear]    │    │
│  │ [Send]      │  │ AI: ...     │  │ Dropdown: [Session v]    │    │
│  └─────────────┘  └─────────────┘  └──────────────────────────┘    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Approval Dialog (when needed)                                 │  │
│  │ "AI wants to write_file(test.py)"  [Approve] [Deny]          │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           CORE MODULES                               │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │    Config    │    │    Agent     │    │   BedrockClient      │  │
│  │              │    │              │    │                      │  │
│  │ - region     │    │ - run()      │───►│ - chat()             │  │
│  │ - model_id   │◄───│ - messages   │    │ - mock_mode          │  │
│  │ - workspace  │    │ - doom check │    │                      │  │
│  │ - limits     │    │              │    │ AWS Bedrock API      │  │
│  └──────────────┘    └──────┬───────┘    └──────────────────────┘  │
│                             │                                        │
│  ┌──────────────────────────▼───────────────────────────────────┐  │
│  │                       TOOLS (15)                              │  │
│  │                                                               │  │
│  │  File Operations    Shell        Python      Documents        │  │
│  │  ┌────────────┐   ┌────────┐   ┌────────┐  ┌─────────────┐  │  │
│  │  │ read_file  │   │ bash   │   │python_ │  │create_word  │  │  │
│  │  │ write_file │   │        │   │exec    │  │create_excel │  │  │
│  │  │ edit_file  │   └────────┘   └────────┘  │create_md    │  │  │
│  │  │ glob       │                            └─────────────┘  │  │
│  │  │ grep       │   Vision        Planning                     │  │
│  │  │ list_dir   │   ┌────────┐   ┌────────────┐               │  │
│  │  └────────────┘   │view_   │   │ todo_write │               │  │
│  │                   │image   │   │ todo_read  │               │  │
│  │                   └────────┘   └────────────┘               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Security    │  │    Audit     │  │      Session             │  │
│  │  Manager     │  │    Logger    │  │      Manager             │  │
│  │              │  │              │  │                          │  │
│  │-validate_path│  │-log()        │  │-create()                 │  │
│  │-validate_cmd │  │-get_log()    │  │-save()                   │  │
│  │-scan_secrets │  │-verify()     │  │-load()                   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Context Manager                            │  │
│  │  - estimate_tokens()  - check_and_warn()  - 80/90/95% alerts │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────┐
                    │      AWS Bedrock            │
                    │      (Claude AI)            │
                    │                             │
                    │  Region: ap-southeast-2     │
                    └─────────────────────────────┘
```

## File Structure

```
complete/
│
├── config.py              # All settings in one place
│   └── AgentConfig        # Dataclass with region, model, limits
│
├── agent.ipynb            # Main notebook - run this to use the agent
│   └── Chat widget UI     # Input box, output area, buttons
│
├── setup.ipynb            # Run first to check Bedrock access
│   └── Model discovery    # Tests which Claude models are available
│
├── requirements.txt       # Python packages to install
│
├── core/                  # Brain of the agent
│   ├── __init__.py
│   ├── agent_loop.py      # Main ReAct loop logic
│   ├── bedrock_client.py  # Talks to AWS Bedrock API
│   ├── permissions.py     # Approval dialog logic
│   ├── security.py        # Path validation, command filtering
│   ├── audit.py           # Action logging
│   ├── memory.py          # Session save/load
│   └── context_manager.py # Token counting, warnings
│
├── tools/                 # All 15 tools
│   ├── __init__.py
│   ├── file_ops.py        # read, write, edit, glob, list_dir
│   ├── search.py          # grep
│   ├── bash.py            # Shell command execution
│   ├── python_exec.py     # Python code execution
│   ├── document.py        # Word, Excel, Markdown creation
│   ├── vision.py          # Image loading
│   └── todo.py            # Task list management
│
├── prompts/
│   └── system.txt         # Instructions given to the AI
│
├── sessions/              # Saved conversations (JSON files)
│   └── 20240129_103000.json
│
└── audit_logs/            # Action history (JSONL files)
    └── 2024-01-29_session123.jsonl
```

## Data Flow

```
1. USER types "List all Python files"
   │
   ▼
2. UI adds message to conversation history
   │
   ▼
3. AGENT.run() starts the ReAct loop
   │
   ▼
4. BEDROCK_CLIENT sends request to AWS
   │
   ├─── Request includes:
   │    - System prompt (instructions)
   │    - Conversation history
   │    - Tool definitions
   │
   ▼
5. CLAUDE (on AWS) thinks and responds
   │
   ├─── Response might be:
   │    a) Just text → Go to step 9
   │    b) Tool call → Continue to step 6
   │
   ▼
6. SECURITY checks the tool call
   │
   ├─── Path valid? Command safe?
   │    - If no → Return error, go to step 5
   │
   ▼
7. APPROVAL (if needed for write operations)
   │
   ├─── Show dialog, wait for user click
   │    - Deny → Return "denied", go to step 5
   │
   ▼
8. TOOL executes
   │
   ├─── AUDIT logs the action
   │
   ├─── Result truncated if too long
   │
   ▼
9. CONTEXT_MANAGER checks usage
   │
   ├─── Over 80%? Show warning
   │
   ▼
10. If more tool calls needed → Go to step 4
    │
    ▼
11. FINAL response shown to user
    │
    ▼
12. SESSION updated (if save clicked)
```

---

# Part 3: User Interaction

## UI Components

| Component | What it does |
|-----------|--------------|
| **Input Box** | Type your messages here |
| **Send Button** | Send message to agent |
| **Output Area** | Shows conversation (scrollable) |
| **Clear Button** | Reset conversation, start fresh |
| **Save Session** | Save current conversation to file |
| **Load Dropdown** | Select a saved session |
| **Load Button** | Load the selected session (displays all messages) |
| **Status** | Shows "Ready", "Processing...", context % |
| **Approval Dialog** | Appears when agent needs permission |

## Live Controls (in agent.ipynb)

These controls update settings **without restarting**:

| Control | What it does |
|---------|--------------|
| **Temperature** | Dropdown 0.0-1.0 - Adjusts creativity in real-time |
| **Extended Thinking** | Checkbox - Enables deep reasoning mode |
| **Think Budget** | Dropdown 1024-16000 - Tokens for thinking |
| **Dark Mode** | Checkbox - Toggles dark theme instantly |

**Note:** Extended Thinking requires temperature=1.0 (set automatically when enabled).

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

The agent runs synchronously (blocking). When processing:
1. Status shows "Processing..."
2. You see tool calls in real-time (`[Calling grep...]`, `[grep result]:...`)
3. Approval dialog CAN appear (you can click Approve/Deny)
4. When done, status returns to "Ready"

You cannot send another message until the current one finishes.

### You Click Clear

1. Conversation history erased
2. Todo list cleared
3. Files-read tracking reset
4. Output area cleared
5. Status reset to "Ready"
6. **Session file NOT deleted** (you can still load it)

### You Save a Session

1. Current messages saved to `sessions/{id}.json`
2. ID based on timestamp (e.g., `20240129_103000`)
3. Dropdown updated with new session
4. Confirmation message shown

### You Load a Session

1. Selected session loaded from file
2. Messages restored to agent
3. **All saved messages displayed** in chat window:
   - User messages
   - Agent responses
   - Tool calls and results
4. Message count shown: "Loaded session: Title (X messages)"
5. You can continue chatting with full history

## Limitations (Not Implemented)

| Feature | Status |
|---------|--------|
| Stop/Cancel button | Not available - must wait for completion |
| Background execution | Not available - UI blocks |
| Streaming (typewriter effect) | Not available - full response only |
| Multiple conversations | One at a time |
| Auto-save | Manual save only |
| Undo/Redo | Not available |

---

# Part 4: Security

## Workspace Boundary

The agent can ONLY access files inside your project folder.

**Blocked:**
```
/etc/passwd              # System files
~/.ssh/id_rsa            # SSH keys
../../../etc/passwd      # Path traversal
C:\Windows\System32      # System directories
```

**Allowed:**
```
./main.py                # Files in project
./src/utils.py           # Subdirectories
./docs/README.md         # Any depth within project
```

## Sensitive File Blocking

These files are ALWAYS blocked, even in workspace:

- `.env`, `.env.local`, `.env.production`
- `credentials.json`, `secrets.json`
- `id_rsa`, `id_ed25519` (SSH keys)
- `.netrc`, `.npmrc`, `.pypirc`

## Secret Detection

When writing files, content is scanned for:

| Pattern | Example |
|---------|---------|
| API Keys | `api_key = "sk-abc123..."` |
| Passwords | `password = "secret123"` |
| AWS Keys | `AKIA...` (20 chars) |
| JWT Tokens | `eyJhbG...` |
| Private Keys | `-----BEGIN RSA PRIVATE KEY-----` |
| Database URLs | `postgres://user:pass@host` |
| GitHub Tokens | `ghp_...` |
| Slack Tokens | `xoxb-...` |

If detected, agent warns you before saving.

## Dangerous Command Blocking

These bash patterns are BLOCKED:

| Pattern | Reason |
|---------|--------|
| `rm -rf /` | Deletes everything |
| `dd if=` | Direct disk access |
| `mkfs` | Formats drives |
| `curl \| bash` | Runs remote code |
| `wget \| sh` | Runs remote code |
| `chmod 777` | Insecure permissions |
| `sudo` | Privilege escalation |
| `nc -l` | Network listener |

## Audit Trail

Every action is logged to `audit_logs/`:

```json
{
  "timestamp": "2024-01-29T10:30:00",
  "session_id": "20240129_103000",
  "action": "tool_call",
  "tool_name": "write_file",
  "parameters": {"file_path": "test.py"},
  "result_summary": "Written 100 chars",
  "user_approved": true,
  "hash": "a1b2c3d4..."  # Integrity verification
}
```

The hash ensures logs can't be tampered with.

---

# Part 5: Configuration

## Settings in config.py

| Setting | Default | Description |
|---------|---------|-------------|
| `region` | `ap-southeast-2` | AWS region (Sydney) |
| `model_id` | Claude 3.5 Sonnet v2 | Which Claude model |
| `workspace` | `.` | Project folder |
| `max_turns` | 30 | Max ReAct loop iterations |
| `max_tokens` | 4096 | Max tokens per response |
| `max_history` | 20 | Messages before trimming |
| `max_output_chars` | 5000 | Tool output truncation |
| `mock_mode` | False | Test without API |
| `temperature` | 1.0 | Creativity (0.0-1.0) |
| `thinking_enabled` | False | Extended thinking mode |
| `thinking_budget` | 10000 | Tokens for thinking |

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

## Changing Settings

Edit `config.py`:

```python
@dataclass
class AgentConfig:
    region: str = "us-east-1"  # Change region
    max_turns: int = 50        # Allow more turns
```

---

# Part 6: Quick Start

## First Time Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Check Bedrock access:**
   Open `setup.ipynb`, run all cells. Should show which models are available.

3. **Enable models in AWS Console:**
   - Go to AWS Console → Bedrock → Model access
   - Enable Claude models
   - Wait for approval (usually instant)

## Daily Usage

1. Open `agent.ipynb`
2. Run all cells
3. Chat widget appears
4. Type your request, click Send
5. Approve any write operations
6. Save session when done

## Example Prompts

```
"List all files in this project"
"Read the main.py file"
"Find all TODO comments in the code"
"Create a Python function that calculates factorial"
"Run the tests"
"Create an Excel file with sample data"
"Help me fix the bug on line 42 of utils.py"
```

---

# Part 7: Troubleshooting

## "Access denied" from Bedrock

1. Go to AWS Console → Bedrock → Model access
2. Click "Manage model access"
3. Enable Claude models
4. Check IAM role has `bedrock:InvokeModel` permission

## "Path outside workspace"

1. Check your workspace setting in config.py
2. Use relative paths (./file.py, not /home/user/file.py)
3. Don't use `..` to go to parent directories

## "Must read file before writing"

This is a safety feature. First call `read_file`, then `write_file` or `edit_file`.

## "Command blocked"

Security is blocking a dangerous command. Review what you're trying to do. Some commands (like `sudo`) are never allowed.

## Agent stuck / Doom loop

If you see "Repetitive tool calls detected":
1. The agent is confused about the task
2. Try rephrasing your request
3. Be more specific about what you want

## Context running out

When you see 80/90/95% warnings:
1. Save your session
2. Start a new conversation
3. Load the session summary if needed

---

# Part 8: Comparison with OpenCode

| Feature | OpenCode | This App |
|---------|----------|----------|
| File operations | Yes | Yes (15 tools) |
| Bash execution | Yes | Yes |
| Python execution | Yes | Yes |
| Word/Excel creation | No | Yes (bonus) |
| Session management | Yes | Yes |
| Approval system | Yes | Yes |
| Security controls | Yes | Yes |
| Audit logging | Yes | Yes |
| Context warnings | Yes | Yes |
| Streaming responses | Yes | No |
| Web search | Yes | No |
| Multi-agent | Yes | No |
| Skills/Plugins | Yes | No |

**Summary:** Core coding features match OpenCode. Missing: streaming, web access, advanced features.

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

- `../compact/` - Simpler 2-file version (same features, less files)
- `../README.md` - Project overview
- `../test_10_cases.py` - Comprehensive test suite
