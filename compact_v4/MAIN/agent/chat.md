# SageAgent V4 — chat.ipynb Companion

> This is the markdown companion of `chat.ipynb`. Keep in sync after changes.

## Cell 0 — Title (Markdown)

# SageAgent V4.7.1

AI coding assistant for SageMaker notebooks. 25+ tools, 16 security layers, prompt caching, sub-agent coordination, 10 skills, Runnable-grade review/verification, local-git regression protection. **v4.7.1**.

**Setup:** Run cells 1-3 in order. Cell 1 installs packages (once). Cell 2 shows config widgets. Cell 3 launches the agent.

**Core files:** `sagemaker_agent.py` (9,866 lines) + this notebook + `memory.md` (auto-populated) + `skills/` (10 skills).

**Docs:** See `USER_GUIDE.md` for full documentation, `TEST_LOG.md` for Bedrock test results, `../CHANGELOG.md` for release notes.

### What's new in v4.7.0 + v4.7.1

**v4.7.1 — Three targeted fixes (anti-bloat release):**
1. **Compact preserves TODO list** — bug fix. Agent was losing its task plan across auto-compaction. Now re-injects todos into post-compact messages.
2. **Auto-commit checkpoint** — `Config.auto_commit_every = N` (default off). Runs `git commit -am "agent-checkpoint (auto)"` locally every N edits. Never pushes. Keeps `git diff HEAD` showing only the latest change set.
3. **`/regression`** — thin wrapper: `git diff HEAD --stat` + session edit summary + suggested test command.

**v4.7.0 — Coding UX enhancements:**
- `/done [full|quick]` — pre-ship gate (simplify → verify → READY-TO-SHIP verdict)
- `/diffs [summary|last|<file>]` — session edit history from `_RECENT_DIFFS` buffer
- `/phase <text>` — work phase indicator in status bar + token display
- `/revert <file>` — now shows diff preview before revert; requires `--yes` to execute
- `/checkpoint restore <name>` — restore todos from named checkpoint
- Budget progress bar in token display when `Config.session_cost_limit > 0`

**v4.6.1 — Workspace path resolution fix:**
Agent in a subfolder can now find files in parent git repo. `glob` falls through to `allowed_paths`. Informative error messages with recovery templates.

**Troubleshooting:** If you see "file not found" or empty glob results, check the `[Workspace: ...]` line at session start. Your target file must live under that Root or under one of the `Also accessible` roots (auto-detected: git repo root, SageMaker home). Otherwise add it explicitly via `agent_config.json` → `allowed_paths`.

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

Skills-based workflow: `/skills`, `/skill use <name>`, `/skill clear`, `/verify`

Applies widget config and calls `create_chat_ui()`.

---

## Cell 4 — Documentation (Markdown)

### Quick Reference

| Action | How |
|--------|-----|
| Send message | Type in input box, press Send |
| Stop agent | Click Stop button |
| Check cost | `/cost` (shows token usage, cache savings, session cost) |
| Activate skill | `/skill use review` |
| Deactivate skills | `/skill clear` |
| List skills | `/skills` |
| **Pre-ship gate** | `/done full` (simplify → verify → READY-TO-SHIP verdict) |
| **Regression check** | `/regression` (git diff stat + session edits + test suggestion) |
| Verify project | `/verify` (adversarial testing skill) |
| Session diffs | `/diffs` (summary), `/diffs last`, `/diffs <file>` |
| Set work phase | `/phase refactoring auth` (shown in status bar) |
| Revert file | `/revert filename.py` (shows diff preview → `/revert filename.py --yes` to confirm) |
| Revert all | `/revert all --yes` (destructive, requires `--yes`) |
| Checkpoint | `/checkpoint create milestone-1`, `/checkpoint list`, `/checkpoint restore milestone-1` |
| Compact context | Click Compact button (or auto at 80%) — **TODOs now preserved** |
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
| explore | Fast file search, codebase navigation (STRICTLY read-only) | 5 | 10 |
| verify | Adversarial testing — tries to BREAK the code | 7 | 15 |
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
| clara-full-review | 190 | Selective 5-phase ClaRA review — run all, pick phases, pick components, or pick sections (~$0.80-$5.85) |

### ClaRA Review Workflow

The `clara-full-review` skill runs a production readiness assessment. You choose what to review:

ClaRA has 3 components you can review individually or together:
- **C1**: End-to-End Claims (document extraction + 21 assessment checks)
- **C2**: Agentic Framework (Bedrock inline agents, supervisor, Snowflake)
- **C3**: UI Layer (Streamlit/Cognito, minimal prototype)

Example commands:
- "Start the ClaRA review" -- all components, all phases
- "Review C1 (End-to-End Claims) only" -- Phase 1 + 2 + 4(C1) + 5
- "Review C2 (Agentic Framework) only" -- Phase 1 + 3(3.1-3.9) + 4(C2) + 5
- "Review C1 and C2, skip UI" -- Phase 1 + 2 + 3(3.1-3.9) + 4(C1+C2) + 5
- "Just validate the 9 bugs" -- Phase 2 section 2.2 only
- "Just the R/A/G scorecard for C1" -- Phase 4 (C1) only

5 phases: Discovery, Component 1, Components 2+3, Prod Readiness, Synthesis.
Agent pauses for your review between phases. Output files are cumulative.
Cost: ~$0.80 (discovery only) to ~$5.85 (full review). See `skills/clara/V4_NOTES.md`.

For ClaRA sessions, increase cost limit in Cell 3:
```python
CONFIG.session_cost_limit = 10.0
CONFIG.max_turns = 80
```

### Sub-Agent Coordination

The agent can spawn sub-agents for complex tasks. This happens two ways:

1. **You ask**: "use a build sub-agent to create X" or "review this code"
2. **Agent decides**: when a task needs 5+ tool calls or spans 3+ files, the agent spawns a sub-agent automatically

**6 sub-agent types:**

| Type | What it does | Can write files? |
|------|-------------|-----------------|
| explore | Fast codebase search (quick/medium/thorough) | No |
| plan | Architecture design, step-by-step plans | No |
| review | Evidence-based code review | No |
| verify | Adversarial testing — tries to BREAK your code | No (runs tests) |
| build | Full development — read, write, execute, test | Yes |
| general | Multi-step research + execution | Yes |

### Git Worktree Isolation (V4.4.0)

When a **build** sub-agent runs, V4 protects your workspace:

1. If workspace is a git repo → creates an isolated worktree copy
2. If workspace is NOT a git repo → auto-initializes git (no credentials needed)
3. Build agent works in the isolated copy
4. On success → changes merged back to your workspace
5. On failure → changes discarded, your workspace is untouched

**You'll see these messages in chat:**
- `[Worktree] Auto-initialized git for workspace protection` (first time only)
- `[Worktree] Build agent isolated in: /tmp/_worktree_build_...`
- `[Worktree] N file(s) merged back to main workspace` (success)
- `[Worktree] Sub-agent failed — discarding worktree changes` (failure)

**No setup needed.** Works automatically. Your real git config is never touched.

Disable with `"enable_worktree": false` in `agent_config.json` if not wanted.

### Version History

| Version | Key Changes |
|---------|-------------|
| V4.4.0 | [CRITICAL] Rich tool descriptions (7 tools, 15-32 lines each), git worktree isolation for build agents, auto git-init, 6 review fixes |
| V4.3.3 | UI redesign, markdown rendering, cost display, diminishing returns fix, cache savings display |
| V4.3.2 | Complete Runnable learning: cache-breakage detection, WHEN-not-WHAT tool descriptions, verify agent, explore RO enforcement, bash git safety, absolute paths |
| V4.3.1 | Prompt engineering upgrade: 6 system prompt sections, 7 tool descriptions, sub-agent structured output, compact zero-tool mode |
| V4.3.0 | Diminishing returns, memory 200-line cap, cold-cache microcompact, auto-memory guard, cache indicator, cache savings USD |
| V4.2.1 | FILE_UNCHANGED_STUB, parallel RO tools, PTL retry, Bedrock cache fix |
| V4.2.0 | Tool result caps, WHAT_NOT_TO_SAVE memory, cold-cache microcompact, 4/3 token padding |
| V4.1.0 | Cache boundary, catastrophic blocks, command auto-classifier, 4-type memory |
| V4.0.0 | Base V4 architecture |

See `CHANGELOG.md` for full details.
