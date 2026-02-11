# SageMaker Coding Agent - Complete Version

A secure AI coding assistant for AWS SageMaker.

---

## What Is This?

This is a **complete, multi-file version** of the SageMaker Coding Agent. It's organized into separate modules for better maintainability.

**Best for:**
- Teams maintaining the code long-term
- Developers who want to understand/modify specific parts
- Production deployments

---

## Beginner's Guide: Key Concepts

### What is an AI Coding Agent?

Think of it like having a programmer assistant that can:
- Read and understand your code files
- Edit files when you ask
- Run commands (like `git status`)
- Create documents (Word, Excel)
- Plan multi-step tasks

You talk to it in plain English, and it figures out what tools to use.

### What is AWS Bedrock?

AWS Bedrock is Amazon's service that lets you use AI models (like Claude) via API. Instead of running AI on your computer, you send requests to AWS and get responses back.

```
Your Notebook  →  AWS Bedrock (Claude)  →  Response
    |                    |                    |
 "Fix this bug"    Thinks about it    "Here's the fix..."
```

### What is a ReAct Loop?

ReAct = **Re**ason + **Act**

It's a pattern where the AI:
1. **Thinks** about what to do
2. **Acts** (calls a tool)
3. **Observes** the result
4. **Repeats** until done

```
User: "List Python files"
     ↓
AI thinks: "I should use the glob tool"
     ↓
AI acts: glob("**/*.py")
     ↓
AI observes: ["main.py", "utils.py"]
     ↓
AI responds: "Found 2 Python files: main.py and utils.py"
```

### What is a Tool?

A tool is a function the AI can call. Examples:

| Tool | What it does |
|------|--------------|
| `read_file` | Opens and reads a file |
| `write_file` | Creates/overwrites a file |
| `bash` | Runs terminal commands |
| `glob` | Finds files by pattern |

The AI decides WHICH tool to use based on your request.

### What is Session Management?

Sessions let you save and resume conversations:

```
Monday:
You: "Help me build a login system"
AI: Creates files, makes progress
You: [Click Save]

Tuesday:
You: [Click Load "login system"]
AI: "I remember! We were working on..."
```

### What is an Approval Dialog?

For safety, some actions need your OK:

```
AI: "I want to delete old_file.py"
    [Approve] [Deny]

You click Approve → AI deletes it
You click Deny → AI skips it
```

This prevents the AI from doing dangerous things without asking.

### What is a Doom Loop?

When the AI gets stuck repeating the same action:

```
Turn 1: read_file("config.py")
Turn 2: read_file("config.py")  ← same
Turn 3: read_file("config.py")  ← stuck!
```

The agent detects this and stops, asking you for help.

### What is Context?

Context = all the text in the conversation so far.

AI models have limits (200,000 tokens for Claude). When you approach the limit:
- 80%: Agent saves a checkpoint
- 90%: Warning shown
- 95%: Critical warning

After the limit, old messages get trimmed.

### What is an Audit Log?

A record of everything the AI did:

```
10:30 - read_file("main.py") - OK
10:31 - write_file("test.py") - User approved
10:32 - bash("git status") - OK
```

Useful for security reviews and debugging.

---

## File Structure

```
complete/
├── config.py           # Settings (region, model, limits)
├── agent.ipynb         # Main notebook to run
├── setup.ipynb         # Model discovery & permissions
├── requirements.txt    # Python dependencies
│
├── core/               # Core logic
│   ├── agent_loop.py   # Main ReAct loop
│   ├── bedrock_client.py # AWS API calls
│   ├── permissions.py  # Approval system
│   ├── security.py     # Safety checks
│   ├── audit.py        # Logging
│   ├── memory.py       # Session save/load
│   └── context_manager.py # Context tracking
│
├── tools/              # All 15 tools
│   ├── file_ops.py     # read, write, edit, glob, list
│   ├── search.py       # grep
│   ├── bash.py         # Shell commands
│   ├── python_exec.py  # Python code execution
│   ├── document.py     # Word, Excel, Markdown
│   ├── vision.py       # Image viewing
│   └── todo.py         # Task tracking
│
├── prompts/            # System instructions
│   └── system.txt      # Main prompt
│
├── sessions/           # Saved conversations
└── audit_logs/         # Action history
```

---

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run setup notebook:**
   Open `setup.ipynb` and run all cells to verify Bedrock access.

3. **Start the agent:**
   Open `agent.ipynb` and run all cells.

4. **Chat:**
   Type messages like:
   - "List files in this directory"
   - "Read the README"
   - "Create a Python hello world script"

---

## 15 Tools Explained

| Tool | Purpose | Needs Approval? |
|------|---------|-----------------|
| `read_file` | Read file contents | No |
| `write_file` | Create/overwrite file | Yes |
| `edit_file` | Replace text in file | Yes |
| `glob` | Find files by pattern | No |
| `grep` | Search file contents | No |
| `list_dir` | List folder contents | No |
| `bash` | Run shell command | Yes |
| `python_exec` | Run Python code | Yes |
| `create_word` | Create .docx file | Yes |
| `create_excel` | Create .xlsx file | Yes |
| `create_markdown` | Create .md file | Yes |
| `view_image` | Load image for AI | No |
| `semantic_search` | AI-powered code search | No |
| `todo_write` | Update task list | No |
| `todo_read` | Show task list | No |

---

## Security Features

| Feature | What it does |
|---------|--------------|
| **Workspace Boundary** | Can't access files outside project folder |
| **Secret Detection** | Warns if code contains API keys/passwords |
| **Command Blocking** | Blocks dangerous commands like `rm -rf /` |
| **Approval System** | Write operations need your OK |
| **Audit Logging** | Records all actions with timestamps |

---

## Model Parameters

| Parameter | Range | Description |
|-----------|-------|-------------|
| **Temperature** | 0.0 - 1.0 | Creativity control (0=deterministic, 1=creative) |
| **Extended Thinking** | On/Off | Enable deep reasoning mode |
| **Thinking Budget** | 1024 - 16000 | Tokens for internal reasoning |

---

## Progress Visibility

As the agent works, you see real-time tool execution:

```
[Calling glob...]
[glob result]:
./main.py
./utils.py

[Calling read_file...]
[read_file result]:
     1→import os
     ...
```

---

## Test Results

All 10 comprehensive tests pass:

| Test | Description | Status |
|------|-------------|--------|
| 1 | Explore codebase | ✅ PASS |
| 2 | Code analysis | ✅ PASS |
| 3 | Project setup with todos | ✅ PASS |
| 4 | Search and analyze | ✅ PASS |
| 5 | Bash operations | ✅ PASS |
| 6 | Python execution | ✅ PASS |
| 7 | Multi-file reading | ✅ PASS |
| 8 | Error handling | ✅ PASS |
| 9 | Security validation | ✅ PASS |
| 10 | Combined workflow | ✅ PASS |

Run: `python test_10_cases.py`

---

## See Also

- `../compact/` - Simpler 2-file version
- `../README.md` - Project overview
- `GUIDE.md` - Full documentation
