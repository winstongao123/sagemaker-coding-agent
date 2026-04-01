# SageAgent V4 — chat.ipynb Companion

> This is the markdown companion of `chat.ipynb`. Keep in sync after changes.

## Cell 0 — Title (Markdown)

# SageAgent V4

AI coding assistant for SageMaker notebooks. 22 tools, 16 security layers, prompt caching, sub-agent coordination. v4.3.1.

**Setup:** Run cells 1-3 in order. Cell 1 installs packages (once). Cell 2 shows config widgets. Cell 3 launches the agent.

**Docs:** See `USER_GUIDE.md` for full documentation, `TEST_LOG.md` for Bedrock test results.

---

## Cell 1 — Install Dependencies (Code)

```python
!pip install -q boto3 ipywidgets Pillow python-docx pandas openpyxl
```

---

## Cell 2 — Configuration Widgets (Code)

- Imports `BEDROCK_MODELS` from `sagemaker_agent.py` (single source of truth)
- Creates dropdown widgets: Model, Temperature, Thinking, Max Turns, Workspace, Mock Mode
- Region: Sydney (`ap-southeast-2`)
- Default model: Claude 4.5 Haiku (AU)

---

## Cell 3 — Launch Agent (Code)

Security & cost settings:
- `aws_bedrock_only = True` -- blocks all AWS except Bedrock
- `require_tool_approval = True` -- approve/deny before execution
- `session_cost_limit = 1.0` -- max $1 per session

Custom slash commands: `/review`, `/explain`, `/test`, `/verify`, `/standards`

Applies widget config and calls `create_chat_ui()`.

---

## Cell 4 — Documentation (Markdown)

### Quick Reference

| Action | How |
|--------|-----|
| Send message | Type in input box, press Send |
| Stop agent | Click Stop button |
| Check cost | `/cost` (shows token usage, cache savings, session cost) |
| Code review | `/review filename.py` |
| Explain code | `/explain filename.py` |
| Generate tests | `/test filename.py` |
| Verify project | `/verify` |
| Apply standards | `/standards filename.py` |
| Revert file | `/revert filename.py` or `/revert all` |
| Compact context | Click Compact button (or auto at 80%) |
| Save/Load | Save button / Session dropdown + Load |

### 22 Tools

| Category | Tools | Approval? |
|----------|-------|-----------|
| File | read_file, write_file, edit_file, glob, grep, list_dir | write/edit need approval |
| Exec | bash, python_exec | Both need approval |
| Docs | create_word, create_excel, create_chart, create_pdf, create_markdown, create_notebook | Need approval |
| Intelligence | view_image, semantic_search, web_fetch | web_fetch needs approval |
| Agents | skill, task, ask_user | task needs approval |
| State | todo_write, todo_read | Auto |

### Sub-Agents

| Type | What it does | Tools | Max turns |
|------|-------------|-------|-----------|
| build | Build, compile, fix errors, run tests | All 22 | 25 |
| plan | Architecture analysis, planning (read-only) | 11 | 15 |
| explore | Fast file search, codebase navigation | 5 | 10 |
| general | General coding tasks | 11 | 15 |
| review | Security, quality, performance review | 6 | 10 |

Sub-agents use structured output format (Scope, Result, Key files, Issues).

### Security (16 layers)

- Bash: 70 allowed commands, 75 dangerous patterns blocked
- Python: 63 regex patterns + AST import validation + runtime sandbox
- AWS: bedrock_only blocks ALL services except Bedrock
- Path traversal: workspace enforcement + symlink resolution
- Catastrophic blocks: rm -rf /, format, mkfs hard-blocked
- Sub-agent depth limit: max 2 levels
- Tool result caps: 50K/200K chars
- Approval dialog, cost limit, audit trail

### Prompt Caching

- System prompt + tool schemas cached after first turn (90% cheaper on subsequent turns)
- Cache indicator: WRITE / HIT / INACTIVE shown per turn
- Sonnet 4.5: caching works (1,024 min). Haiku 4.5: may not activate (<4,096 tokens)
- `/cost` shows cumulative cache savings in USD

### Context Management

- Auto-compact at 80% context usage
- Microcompact on cold cache (>30 min idle, keepRecent=1)
- PTL retry: trim + retry up to 3 times on prompt-too-long
- FILE_UNCHANGED_STUB: re-reading unchanged files returns stub
- Diminishing returns: advisory warning after 3+ low-output turns
- Compact summary: zero-tool mode prevents ghost tool calls

### Memory System (4 types)

| Type | What it stores |
|------|---------------|
| user | Role, preferences, expertise |
| feedback | Corrections and confirmations |
| project | Ongoing work context, deadlines |
| reference | Pointers to external resources |

Auto-extracted at session end. Stored in `memory.md`. Capped at 200 lines / 25KB. WHAT_NOT_TO_SAVE rules exclude code/git noise.

### Model Pricing (Bedrock, Sydney region)

| Model | Input / 1M | Output / 1M |
|-------|-----------|------------|
| Claude 3 Haiku | $0.25 | $1.25 |
| Claude 3.5 Haiku | $0.80 | $4.00 |
| Claude 4.5 Haiku (AU) | $1.10 | $5.50 |
| Claude 4.5 Sonnet (AU) | $3.30 | $16.50 |
| Claude 4.5 Opus | $5.00 | $25.00 |
| Claude 4.6 Opus (AU) | $5.50 | $27.50 |

### Token Overhead Per API Call

| Component | Tokens |
|-----------|--------|
| System prompt | ~1,500 |
| Tool schemas | ~1,800 |
| Bedrock overhead | ~346 |
| Total per call | ~3,650 |

### Skills

| Skill | Lines | What it does |
|-------|-------|-------------|
| review | 83 | 5-category code review with severity ratings |
| verify | 147 | 6-phase verification + structured report |
| coding-standards | 153 | KISS, DRY, YAGNI, naming, function design |
| report | 45 | Report generation workflow |
| clara | 80 | ClaRA review methodology: evidence labeling, R/A/G thresholds, PII patterns |
| clara-full-review | 150 | Full 5-phase ClaRA codebase review with user pause between phases (~$6 est.) |

### ClaRA Review Workflow

The `clara-full-review` skill runs a 5-phase production readiness assessment:
1. Discovery -- file tree, dependencies, AWS inventory, code metrics
2. Component 1 -- bug validation, CHECK_REGISTRY, test evidence
3. Components 2+3 -- agent definitions, orchestration, SQL risks
4. Production Readiness -- R/A/G scorecard, cost projections, FTE impact
5. Synthesis -- final report + business case

Usage: `/skill use clara-full-review` then "Start the ClaRA review". Agent pauses for user review between phases. See `skills/clara/V4_NOTES.md` for V4 config.

### Version History

| Version | Key Changes |
|---------|-------------|
| V4.3.1 | Prompt engineering upgrade: 6 system prompt sections, 7 tool descriptions, sub-agent structured output, compact zero-tool mode |
| V4.3.0 | Diminishing returns, memory 200-line cap, cold-cache microcompact, auto-memory guard, cache indicator, cache savings USD |
| V4.2.1 | FILE_UNCHANGED_STUB, parallel RO tools, PTL retry, Bedrock cache fix |
| V4.2.0 | Tool result caps, WHAT_NOT_TO_SAVE memory, cold-cache microcompact, 4/3 token padding |
| V4.1.0 | Cache boundary, catastrophic blocks, command auto-classifier, 4-type memory |
| V4.0.0 | Base V4 architecture |

See `CHANGELOG.md` for full details.
