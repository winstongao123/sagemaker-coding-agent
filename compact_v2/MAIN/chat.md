# chat.ipynb (Markdown Copy)

This file is an auto-generated markdown copy of chat.ipynb cells in order.

## Cell 1 (markdown)

# SageMaker Coding Agent V2

Secure AI coding assistant powered by AWS Bedrock Claude.

**21 Tools:** File ops, bash/python exec, docs/charts/pdf, vision, semantic search, todos, web fetch, skills, sub-agents, ask user

**New in V2:**
- External config (`opencode.json`) with JSONC support
- Skills system (`/skills`, `/skill use <name>`, `/skill clear`)
- Custom slash commands with templates (`/review`, `/test`, etc.)
- Sub-agents (build, plan, explore, general) via `task` tool
- MCP client (local stdio + remote HTTP servers)
- Cost tracking (`/cost`) with per-model Bedrock pricing
- Snapshot & revert (`/revert <file>`, `/revert all`)
- Interactive questions (`ask_user` tool)
- Diff tracking on every edit
- Permission rules (per-tool, file-pattern, command-pattern)
- SSRF-hardened web fetch

**Security:** 3-layer bash + 3-layer Python + workspace boundary + SSRF protection

See `USER_GUIDE.md` for full documentation.

## Cell 2 (code)



## Cell 3 (code)



## Cell 4 (code)



## Cell 5 (markdown)

---

## Quick Start Examples

| Task | Example Prompt |
|------|----------------|
| **Explore** | "List files in this directory" |
| **Read** | "Read the README.md file" |
| **Search** | "Find all Python files with test in the name" |
| **Semantic Search** | "Find where authentication is handled" |
| **Edit** | "Add a comment to the top of file.py" |
| **Execute** | "Run git status" |
| **Create Excel** | "Create an Excel file with employee data" |
| **Create Word** | "Write a project summary document" |
| **Create PDF** | "Create a PDF report with table and chart summary" |
| **Web Fetch** | "Fetch https://example.com and summarize it" |
| **Plan** | "Help me build a REST API with Flask" |

---

## Slash Commands

| Command | What it does |
|---------|-------------|
| `/skills` | List discovered skills |
| `/skill use <name>` | Activate a skill |
| `/skill clear` | Deactivate all skills |
| `/commands` | List custom commands from opencode.json |
| `/cost` | Token usage and cost breakdown |
| `/revert <file>` | Revert file to pre-edit snapshot |
| `/revert all` | Revert all modified files |
| `/compact` | Compress conversation context |
| `/save` | Save session |

---

## Tools (21)

- **File:** `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `list_dir`
- **Exec:** `bash`, `python_exec`
- **Docs:** `create_word`, `create_excel`, `create_markdown`, `create_pdf`
- **Charts:** `create_chart` (bar, line, pie, scatter)
- **Vision:** `view_image`
- **Search:** `semantic_search` (Bedrock Titan embeddings)
- **Planning:** `todo_write`, `todo_read`
- **Web:** `web_fetch` (URL fetch with SSRF protection)
- **Skills:** `skill` (list/load skills)
- **Sub-agents:** `task` (build, plan, explore, general)
- **Interactive:** `ask_user` (mid-conversation questions)

---

## Security

- 3-layer bash validation (allowlist + 70 patterns + restricted mode)
- 3-layer Python validation (AST + import hook + secret detection)
- SSRF protection (private IP blocking, redirect blocking, 2MB limit)
- Workspace boundary enforcement
- Configurable permission rules via `opencode.json`
- Audit logging and session persistence

