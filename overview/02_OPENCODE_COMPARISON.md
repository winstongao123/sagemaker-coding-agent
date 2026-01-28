# OpenCode vs SageMaker Coding Agent

## Side-by-Side Comparison

| Feature | OpenCode | SageMaker Agent |
|---------|----------|-----------------|
| **Platform** | CLI (Terminal) | Jupyter Notebook |
| **LLM Provider** | Anthropic API | AWS Bedrock |
| **Models** | Claude direct | Claude via Bedrock |
| **Interface** | Terminal UI (tview) | ipywidgets chat |
| **Language** | Go/TypeScript | Python |
| **Security** | Basic | Enhanced |
| **Billing** | Anthropic account | AWS billing |

---

## Feature Comparison

### Prompts & AI Behavior

| Feature | OpenCode | SageMaker Agent | Status |
|---------|----------|-----------------|--------|
| Tone and style | anthropic.txt | prompts/system.txt | ✓ Same |
| Professional objectivity | Yes | Yes | ✓ Same |
| Task management (Todo) | TodoWrite tool | todo_write tool | ✓ Same |
| `<example>` format | Yes | Yes | ✓ Same |
| Code references (file:line) | Yes | Yes | ✓ Same |
| Read before edit rule | Yes | Yes | ✓ Same |

### Flow Design

| Feature | OpenCode | SageMaker Agent | Status |
|---------|----------|-----------------|--------|
| ReAct agent loop | session/processor.ts | core/agent_loop.py | ✓ Same |
| Doom loop detection | 3 identical = stop | 3 identical = stop | ✓ Same |
| Tool registry | tools/index.ts | core/tools.py | ✓ Same |
| JSON Schema validation | Yes | Yes | ✓ Same |
| Permission system | Multi-level | Multi-level | ✓ Same |
| Streaming responses | Yes | Yes | ✓ Same |

### Tools

| Tool | OpenCode | SageMaker Agent | Status |
|------|----------|-----------------|--------|
| read_file | Read | read_file | ✓ Same |
| write_file | Write | write_file | ✓ Same |
| edit_file | Edit | edit_file | ✓ Same |
| glob | Glob | glob | ✓ Same |
| grep | Grep | grep | ✓ Same |
| list_dir | (via bash) | list_dir | ✓ Added |
| bash | Bash | bash | ✓ Same |
| view_image | (limited) | view_image | ✓ Enhanced |
| todo_write | TodoWrite | todo_write | ✓ Same |
| python_exec | (via bash) | python_exec | ✓ Added |
| create_word | - | create_word | ✓ Added |
| create_excel | - | create_excel | ✓ Added |
| semantic_search | - | semantic_search | ✓ Added |

### Features NOT Implemented (Parked)

| Feature | OpenCode | SageMaker Agent | Reason |
|---------|----------|-----------------|--------|
| Skills system | Yes | No | Parked for later |
| MCP integration | Yes | No | Parked for later |
| WebSearch | WebSearch | No | Security (no network) |
| WebFetch | WebFetch | No | Security (no network) |
| Multi-agent (Task) | Task | No | Complexity |
| LSP integration | Yes | No | Requires LSP server |

---

## What We Added (Not in OpenCode)

### Security Enhancements

| Feature | Description |
|---------|-------------|
| Workspace boundary | Path validation - can't escape project |
| Secret detection | Regex for API keys, passwords, tokens |
| Command filtering | Blocks rm -rf, sudo, curl\|bash |
| Network isolation | curl, wget, ssh blocked by default |
| Audit logging | JSONL with hash integrity |
| Output truncation | 50KB max to prevent token explosion |

### Extra Tools

| Tool | Description |
|------|-------------|
| python_exec | Execute Python code with subprocess |
| create_word | Create .docx files (python-docx) |
| create_excel | Create .xlsx files (openpyxl) |
| create_markdown | Create .md files |
| semantic_search | Bedrock Titan Embeddings search |
| list_dir | Dedicated directory listing |

### Context Management

| Feature | Description |
|---------|-------------|
| Context warnings | Alerts at 80%, 90%, 95% usage |
| Checkpoint saving | Auto-save at 80% context |
| Last 3 messages | Preserved before compaction |

---

## Code Mapping

### OpenCode → SageMaker Agent

```
OpenCode                          SageMaker Agent
──────────────────────────────────────────────────────
packages/opencode/src/
├── session/
│   ├── processor.ts      →      core/agent_loop.py
│   └── prompt/
│       └── anthropic.txt →      prompts/system.txt
├── tools/
│   ├── index.ts          →      core/tools.py
│   ├── permission.ts     →      core/permissions.py
│   ├── read.ts           →      tools/file_ops.py
│   ├── write.ts          →      tools/file_ops.py
│   ├── edit.ts           →      tools/file_ops.py
│   ├── glob.ts           →      tools/file_ops.py
│   ├── grep.ts           →      tools/search.py
│   └── bash.ts           →      tools/bash.py
└── provider/
    └── anthropic.ts      →      core/bedrock_client.py
```

---

## Prompt Comparison

### OpenCode (anthropic.txt excerpt)
```
You are OpenCode, the best coding agent on the planet.

# Tone and style
- Only use emojis if the user explicitly requests it...
- Your output will be displayed on a command line interface...

# Task Management
You have access to the TodoWrite tools...
```

### SageMaker Agent (system.txt excerpt)
```
You are SageMaker Coding Agent, a powerful AI assistant...

# Tone and style
- Only use emojis if the user explicitly requests it...
- Your output will be displayed in a Jupyter notebook...

# Task Management
You have access to the todo_write tool...

# Security Context (ADDED)
This agent processes sensitive data. Security controls...
```

---

## Why Not Just Port OpenCode Directly?

1. **Language**: OpenCode is Go/TypeScript, SageMaker needs Python
2. **API**: Anthropic API ≠ Bedrock API (different request format)
3. **Interface**: Terminal UI won't work in Jupyter
4. **Security**: Enterprise use requires stronger controls
5. **Integration**: Needs to work with SageMaker ecosystem

---

## Migration Path

If you want to move from OpenCode to SageMaker Agent:

| OpenCode Concept | SageMaker Equivalent |
|------------------|---------------------|
| `/chat` | Chat widget in agent.ipynb |
| `/commit` | Ask agent to "create a commit" |
| `/review-pr` | Ask agent to "review the changes" |
| `CLAUDE.md` | `AGENTS.md` |
| hooks | Not implemented yet |
| MCP servers | Not implemented yet |
