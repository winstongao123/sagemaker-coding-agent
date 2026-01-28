# SageMaker Coding Agent - Project Overview

## What Is This?

A **SageMaker version of OpenCode** - a secure AI coding assistant that runs in Jupyter notebooks using AWS Bedrock Claude models.

---

## Quick Summary

| Aspect | Description |
|--------|-------------|
| **What** | AI coding assistant for SageMaker |
| **Based On** | OpenCode (CLI tool by SST) |
| **LLM** | AWS Bedrock Claude models |
| **Interface** | Jupyter notebook with ipywidgets chat |
| **Security** | Enhanced for sensitive data |
| **Region** | ap-southeast-2 (Sydney) default |

---

## Why This Exists

**Problem:** OpenCode is a great CLI coding assistant, but:
- Uses Anthropic API directly (not enterprise-friendly)
- Runs in terminal (not SageMaker compatible)
- Limited security controls

**Solution:** SageMaker Coding Agent:
- Uses AWS Bedrock (enterprise billing, compliance)
- Runs in Jupyter notebooks
- Enhanced security for sensitive data

---

## What It Does

### Core Capabilities
1. **Read/Write/Edit files** - Full file manipulation
2. **Search code** - Grep + semantic search
3. **Run commands** - Bash with approval
4. **Run Python** - Execute code safely
5. **Create documents** - Word, Excel, Markdown
6. **Analyze images** - Vision/screenshots
7. **Track tasks** - Todo list management

### Security Features
1. **Workspace boundary** - Can't access files outside project
2. **Secret detection** - Warns on API keys/passwords
3. **Command filtering** - Blocks dangerous commands
4. **Audit logging** - Every action logged
5. **Approval system** - User approves writes/executes

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    agent.ipynb                          │
│                 (Chat Interface)                        │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   Agent Loop                            │
│            (core/agent_loop.py)                         │
│                                                         │
│  1. Build messages (history + user input)               │
│  2. Call Bedrock Claude                                 │
│  3. Parse response (text + tool calls)                  │
│  4. If tool calls:                                      │
│     - Security check                                    │
│     - Permission check                                  │
│     - Execute tool                                      │
│     - Audit log                                         │
│     - Loop back                                         │
│  5. If no tool calls: return response                   │
└─────────────────────┬───────────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ Security │ │  Tools   │ │ Bedrock  │
    │ Manager  │ │ Registry │ │  Client  │
    └──────────┘ └──────────┘ └──────────┘
```

---

## File Structure

```
sagemaker-coding-agent/
│
├── agent.ipynb              # Main chat interface
├── setup.ipynb              # Model discovery & config
├── config.py                # Configuration class
├── requirements.txt         # Dependencies
├── README.md                # User documentation
├── IMPLEMENTATION_PLAN.md   # Full technical spec
│
├── core/                    # Core engine
│   ├── agent_loop.py        # ReAct loop
│   ├── bedrock_client.py    # Bedrock API
│   ├── security.py          # Security controls
│   ├── audit.py             # Audit logging
│   ├── permissions.py       # Approval system
│   ├── tools.py             # Tool registry
│   ├── memory.py            # Session storage
│   ├── context_manager.py   # Context warnings
│   ├── prompts.py           # Prompt builder
│   └── project_config.py    # AGENTS.md loading
│
├── tools/                   # Tool implementations
│   ├── file_ops.py          # read, write, edit, glob
│   ├── search.py            # grep, semantic search
│   ├── bash.py              # Shell commands
│   ├── python_exec.py       # Python execution
│   ├── document.py          # Word/Excel/MD
│   ├── vision.py            # Image analysis
│   └── todo.py              # Task tracking
│
├── prompts/
│   └── system.txt           # System prompt
│
├── docs/                    # Documentation
├── overview/                # This folder
├── review/                  # Code review
├── tests/                   # Unit tests
├── sessions/                # Saved sessions
└── audit_logs/              # Action logs
```

---

## How It Works

### 1. User Types Message
```
User: "Read config.py and add a new setting"
```

### 2. Agent Loop Runs
```python
# Build messages
messages = history + [{"role": "user", "content": user_message}]

# Call Bedrock
response = bedrock.chat(messages, system_prompt, tools)

# Response has tool call
if response.tool_calls:
    for tool in response.tool_calls:
        # Check security
        if not security.validate(tool):
            return "Blocked"

        # Check permission
        if not permissions.check(tool):
            return "Denied"

        # Execute
        result = tool.execute()

        # Audit log
        audit.log(tool, result)

        # Add result and loop
        messages.append(tool_result)
```

### 3. Response Returned
```
Agent: I've read config.py. Here's the content...
       I'll now add the new setting.
       [Requests approval for edit]
```

---

## OpenCode Patterns Used

### From Prompts (anthropic.txt)
- Tone and style (concise, no emojis)
- Professional objectivity
- Task management with examples
- Tool usage policy
- Code references (file:line)

### From Flow Design
- ReAct agent loop
- Doom loop detection (3 identical calls = stop)
- Tool registry with schemas
- Multi-level permissions
- Streaming responses

---

## Security Model

### Defense in Depth

```
Layer 1: Input Validation
├── Path must be in workspace
├── Command must pass safety check
└── Parameters must match schema

Layer 2: Permission Check
├── Read tools: auto-allow
├── Write tools: ask once per session
└── Execute tools: always ask

Layer 3: Execution Sandbox
├── Subprocess isolation
├── Timeout enforcement
└── Output truncation

Layer 4: Audit Trail
├── Every action logged
├── Hash integrity
└── Sensitive data redacted
```

---

## Getting Started

### Prerequisites
- AWS account with Bedrock access
- Python 3.8+
- Jupyter notebook

### Quick Start
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure AWS
aws configure

# 3. Start Jupyter
jupyter notebook

# 4. Open setup.ipynb (run all cells)
# 5. Open agent.ipynb (start chatting)
```

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Python files | 23 |
| Lines of code | 4,274 |
| Unit tests | 17 |
| Tools | 13 |
| System prompt | ~1,500 tokens |
| OpenCode parity | ~75% |
