# User Guide - SageMaker Coding Agent

## Getting Started

### Step 1: Install Dependencies

```bash
cd sagemaker-coding-agent
pip install -r requirements.txt
```

Or in Jupyter:
```python
!pip install boto3 ipywidgets pandas openpyxl python-docx Pillow numpy
```

### Step 2: Configure AWS

```bash
aws configure
# AWS Access Key ID: YOUR_KEY
# AWS Secret Access Key: YOUR_SECRET
# Default region: ap-southeast-2
# Default output format: json
```

### Step 3: Run Setup

1. Open `setup.ipynb`
2. Run all cells
3. This discovers available Bedrock models and saves config

### Step 4: Start Chatting

1. Open `agent.ipynb`
2. Run all cells
3. Type in the input box, click Send

---

## Basic Usage

### Chat Interface

```
┌────────────────────────────────────────────────┐
│  SageMaker Coding Agent                        │
├────────────────────────────────────────────────┤
│                                                │
│  [You]: List all Python files                  │
│                                                │
│  [Agent]: I'll list the Python files...        │
│           Found 23 .py files:                  │
│           - config.py                          │
│           - core/agent_loop.py                 │
│           ...                                  │
│                                                │
├────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────┐  │
│  │ Type your message...                     │  │
│  └──────────────────────────────────────────┘  │
│  [Send] [Clear]               Status: Ready    │
└────────────────────────────────────────────────┘
```

### Example Requests

#### File Operations
```
"List all files in the src folder"
"Read the config.py file"
"Read lines 50-100 of agent_loop.py"
"Create a new file called test.py with a hello world function"
"Edit config.py and change the region to us-east-1"
```

#### Search
```
"Search for 'TODO' in all Python files"
"Find all files that contain 'def main'"
"Search for functions that handle authentication"  (semantic search)
```

#### Code Tasks
```
"Fix the bug in line 42 of security.py"
"Add error handling to the read_file function"
"Refactor this code to be more readable"
"Add type hints to all functions in tools.py"
```

#### Shell Commands
```
"Run git status"
"Run pytest tests/"
"Install pandas with pip"
```

#### Documents
```
"Create a Word document summarizing this project"
"Create an Excel file with this data: name=Alice age=30, name=Bob age=25"
"Create a README.md for this folder"
```

---

## Approval System

### When Approval Is Needed

| Action | Approval |
|--------|----------|
| Read file | Auto-allowed |
| Search files | Auto-allowed |
| List directory | Auto-allowed |
| View image | Auto-allowed |
| Check todos | Auto-allowed |
| Write file | Ask once per session |
| Edit file | Ask once per session |
| Run bash | Always ask |
| Run Python | Always ask |
| Create documents | Always ask |

### Approval Dialog

```
┌────────────────────────────────────────────────┐
│  Approval Required                             │
├────────────────────────────────────────────────┤
│  Tool: bash                                    │
│  Input: git status                             │
│                                                │
│  [Approve] [Deny] [ ] Remember for session     │
└────────────────────────────────────────────────┘
```

- **Approve**: Allow this action
- **Deny**: Block this action
- **Remember**: Don't ask again for this session

---

## Task Tracking

The agent automatically tracks tasks for complex work:

### Example
```
User: "Help me add user authentication to the app"

Agent: I'll break this down into tasks:

Todo List:
  [ ] Research existing auth code
  [>] Design authentication flow
  [ ] Implement login function
  [ ] Add session management
  [ ] Write tests

Working on: Designing authentication flow...
```

### Task Status Icons
- `[ ]` - Pending
- `[>]` - In progress
- `[x]` - Completed

---

## Context Management

### Context Warnings

| Level | Usage | What Happens |
|-------|-------|--------------|
| Normal | 0-80% | Continue normally |
| Warning | 80% | Checkpoint saved |
| High | 90% | Alert shown |
| Critical | 95% | Strong warning |

### Warning Message
```
⚠️ Context is at 80% (160k/200k tokens).
I've saved a checkpoint to `_temp_context.md`
```

### Starting Fresh
Click **Clear** button to start a new session.

---

## Project Instructions (AGENTS.md)

Create an `AGENTS.md` file in your project root:

```markdown
# Project Instructions

## Code Style
- Use Python 3.9+ features
- Always add type hints
- Follow PEP 8

## Project Structure
- src/ - Main source code
- tests/ - Unit tests
- docs/ - Documentation

## Testing
Run tests with: pytest tests/ -v

## Important Notes
- Don't modify files in vendor/
- API keys are in .env (never commit)
```

The agent will read this file and follow the instructions.

---

## Session Management

### Save Session
Sessions are auto-saved to `sessions/` folder.

### Load Previous Session
```python
# In agent.ipynb
session_id = "20240128_120000"
current_session = sessions.load(session_id)
```

### List Sessions
```python
sessions.list_sessions()
# Returns: [{"id": "...", "title": "...", "message_count": 5}, ...]
```

---

## Troubleshooting

### "Access denied for Bedrock"
1. Go to AWS Bedrock Console
2. Enable Claude models in Model Access
3. Re-run setup.ipynb

### "Throttling exception"
- You hit the daily token limit
- Wait until tomorrow OR
- Request quota increase from AWS Support

### "Must read file before editing"
- The agent must call read_file before edit_file
- This is a safety feature
- Ask: "Read config.py and then edit line 10"

### "Path outside workspace"
- The agent can only access files in the project folder
- Security feature to prevent accessing /etc/passwd etc.

### "Command blocked"
- Dangerous commands are blocked (rm -rf, sudo, etc.)
- Network commands blocked by default
- This is intentional for security

---

## Tips for Best Results

### Be Specific
```
Good: "Read lines 50-75 of config.py"
Bad:  "Show me the config"

Good: "Create a function that validates email addresses"
Bad:  "Add validation"
```

### Use Context
```
"In the file we just read, fix the bug on line 42"
"Using the same approach, add another function"
```

### Break Down Complex Tasks
```
"Let's implement user auth. First, create the database models."
"Now add the login endpoint."
"Finally, add session management."
```

### Review Before Approving
Always review the proposed changes before clicking Approve, especially for:
- File writes/edits
- Bash commands
- Python execution

---

## Keyboard Shortcuts (in Jupyter)

| Shortcut | Action |
|----------|--------|
| Shift+Enter | Run cell |
| Ctrl+Enter | Run cell, stay |
| Esc | Exit edit mode |
| Enter | Enter edit mode |
| A | Insert cell above |
| B | Insert cell below |
