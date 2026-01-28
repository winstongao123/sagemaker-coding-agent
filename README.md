# SageMaker Coding Agent

A secure, fully functional AI coding assistant for AWS SageMaker, powered by Amazon Bedrock Claude models.

## Features

### Core Capabilities
- **Chat Interface** - ipywidgets-based chat in Jupyter notebook
- **Code Assistance** - Read, search, edit, write files
- **Shell Execution** - Run bash commands with approval
- **Python Execution** - Run Python code for data processing
- **Document Generation** - Create Word, Excel, Markdown files
- **Vision** - Analyze images and screenshots
- **Session Memory** - Save/load conversation history

### Security (for Sensitive Data)
- **Workspace Boundary** - Cannot access files outside project
- **Secret Detection** - Warns on API keys, passwords, credentials
- **Command Filtering** - Blocks dangerous commands (rm -rf, sudo, etc.)
- **Network Isolation** - curl, wget, ssh blocked by default
- **Audit Logging** - Immutable log with integrity verification
- **Approval System** - Write operations need user confirmation

### AI Features
- **OpenCode-style Prompts** - Professional, task-focused responses
- **Todo Tracking** - Automatic task management
- **Doom Loop Detection** - Stops repetitive tool calls
- **Context Warnings** - Alerts at 80%, 90%, 95% context usage
- **Semantic Search** - Find code by meaning (optional)

---

## Quick Start

### Option A: Run in SageMaker (Recommended)

Upload the entire `sagemaker-coding-agent/` folder to your SageMaker notebook instance.

### Option B: Run Locally (for Testing)

You can test locally if you have AWS credentials:

```bash
# 1. Configure AWS credentials
aws configure
# Enter: Access Key, Secret Key, Region (ap-southeast-2)

# 2. Ensure Bedrock access is enabled in your AWS account

# 3. Install Jupyter
pip install jupyter

# 4. Run
cd sagemaker-coding-agent
jupyter notebook
```

Open `setup.ipynb` first, then `agent.ipynb`.

---

### 1. Upload to SageMaker (if using SageMaker)

Upload the entire `sagemaker-coding-agent/` folder to your SageMaker notebook instance.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or in a notebook cell:
```python
!pip install boto3 ipywidgets pandas openpyxl python-docx Pillow numpy
```

### 3. Run Setup

Open **`setup.ipynb`** and run all cells to:
- Discover available Bedrock models in your region
- Check permissions
- Save configuration

### 4. Start Chatting

Open **`agent.ipynb`** and run the cells to start the chat interface.

---

## Usage Guide

### Basic Chat

Type your request in the input box and click **Send**:

```
"List all Python files in this project"
"Read the config.py file"
"Create a hello.py file that prints Hello World"
"Run git status"
```

### Approval System

When the agent wants to:
- **Write/edit files** → Asks once per session
- **Run bash commands** → Asks every time
- **Run Python code** → Asks every time
- **Create documents** → Asks every time

Click **Approve** or **Deny** in the dialog.

### Task Tracking

The agent automatically tracks tasks. For complex requests:

```
"Help me refactor the authentication module"
```

The agent will:
1. Create a todo list
2. Mark tasks in progress
3. Complete tasks one by one
4. Show progress throughout

### Document Generation

```
"Create a Word document summarizing the project"
"Create an Excel file with user data: name=Alice age=30, name=Bob age=25"
"Create a README.md for this project"
```

### Code Search

**Keyword search (grep):**
```
"Search for 'def authenticate' in all Python files"
```

**Semantic search (meaning-based):**
```
"Find code that handles user login"
```

Note: Semantic search requires indexing first (see setup.ipynb).

### Image Analysis

```
"Analyze the screenshot at ./error.png"
"What does the diagram in architecture.png show?"
```

---

## Configuration

### Default Settings (config.py)

| Setting | Default | Description |
|---------|---------|-------------|
| region | ap-southeast-2 | AWS region (Sydney) |
| primary_model | claude-3-5-sonnet | Main model |
| max_turns | 50 | Max agent loop iterations |
| max_tokens | 4096 | Max response tokens |
| allow_network | False | Block network commands |

### Change Configuration

Edit `agent_config.json` after running setup, or:

```python
from config import AgentConfig
config = AgentConfig.load()
config.region = "us-east-1"
config.save()
```

### Project Instructions (AGENTS.md)

Create an `AGENTS.md` file in your project root to give the agent custom instructions:

```markdown
# Project Instructions

## Code Style
- Use type hints for all functions
- Follow PEP 8

## Important Files
- config.py - Main configuration
- core/ - Core modules

## Testing
- Run tests with: pytest tests/
```

---

## File Structure

```
sagemaker-coding-agent/
├── agent.ipynb          # Main chat interface
├── setup.ipynb          # Setup & model discovery
├── config.py            # Configuration class
├── requirements.txt     # Python dependencies
│
├── core/
│   ├── agent_loop.py    # ReAct loop + doom detection
│   ├── audit.py         # Audit logging
│   ├── bedrock_client.py# Bedrock API
│   ├── context_manager.py# Context warnings
│   ├── memory.py        # Session persistence
│   ├── permissions.py   # Approval system
│   ├── project_config.py# AGENTS.md loading
│   ├── prompts.py       # Prompt builder
│   ├── security.py      # Security controls
│   ├── semantic_search.py# Titan Embeddings
│   └── tools.py         # Tool registry
│
├── tools/
│   ├── bash.py          # Shell execution
│   ├── document.py      # Word/Excel/MD
│   ├── file_ops.py      # File operations
│   ├── python_exec.py   # Python execution
│   ├── search.py        # Grep + semantic
│   ├── todo.py          # Task tracking
│   └── vision.py        # Image analysis
│
├── prompts/
│   └── system.txt       # System prompt
│
├── sessions/            # Saved conversations
└── audit_logs/          # Action audit trail
```

---

## Available Tools

### Read-Only (No Approval)
| Tool | Description |
|------|-------------|
| `read_file` | Read file with line numbers |
| `glob` | Find files by pattern |
| `grep` | Search file contents |
| `list_dir` | List directory |
| `view_image` | Analyze images |
| `todo_read` | Check task list |
| `semantic_search` | Search by meaning |

### Write Operations (Approval Required)
| Tool | Description |
|------|-------------|
| `write_file` | Create/overwrite file |
| `edit_file` | Replace text in file |
| `create_word` | Create .docx |
| `create_excel` | Create .xlsx |
| `create_markdown` | Create .md |

### Execution (Always Asks)
| Tool | Description |
|------|-------------|
| `bash` | Run shell commands |
| `python_exec` | Run Python code |

---

## Security Details

### Blocked Commands
- `rm -rf /` - Recursive delete
- `sudo` - Privilege escalation
- `curl | bash` - Pipe to shell
- `dd if=` - Direct disk access
- Network commands (when disabled)

### Secret Detection
Warns when content contains:
- API keys
- AWS credentials
- Passwords
- Private keys
- Database connection strings
- JWT tokens

### Audit Log
Every action is logged to `audit_logs/` with:
- Timestamp
- Tool name
- Parameters (sanitized)
- Result summary
- Hash for integrity verification

Check integrity:
```python
from core.audit import AuditLogger
audit = AuditLogger()
is_valid, issues = audit.verify_integrity("session_id")
```

---

## Troubleshooting

### "Access denied" for Bedrock models

1. Go to AWS Console → Amazon Bedrock
2. Click "Model access" → "Manage model access"
3. Enable Claude models
4. Re-run setup.ipynb

### "Must read file before editing"

The agent must call `read_file` before `edit_file`. This is a safety feature. Ask the agent to read the file first.

### Context limit warnings

At 80% context, a checkpoint is saved. At 95%, consider starting a new session. The agent will warn you.

### Tool execution denied

Click **Approve** in the dialog, or check if the command is blocked for security reasons.

---

## Requirements

- AWS SageMaker notebook instance
- Bedrock access with Claude models enabled
- Python 3.8+
- IAM permissions: `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`

---

## Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | This file - overview and usage |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Full technical design |
| [docs/AWS_SETUP_VERIFICATION.md](docs/AWS_SETUP_VERIFICATION.md) | AWS credential setup guide |
| [docs/test_bedrock.py](docs/test_bedrock.py) | Bedrock access test script |

---

## Based On

This agent is inspired by [OpenCode](https://github.com/sst/opencode) with adaptations for:
- AWS Bedrock (instead of direct Anthropic API)
- Jupyter notebook interface (instead of CLI)
- Enhanced security for sensitive data processing
