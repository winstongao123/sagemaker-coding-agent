# SageAgent V4 — chat.ipynb Companion

> This is the markdown companion of `chat.ipynb`. Keep in sync after changes.

## Cell 0 — Title (Markdown)

# SageAgent V4.10.7

AI coding assistant for SageMaker notebooks. 24 tools, 16 security layers, prompt caching (Sonnet 4.5 default — caching activates from 1024 tokens), sub-agent coordination (suggest-not-mandatory verify by default), 11 skills, Runnable-grade review/verification, local-git regression protection, durable status handoff, explicit skill activation, context diagnostics, hardened compaction (microcompact + segment-level Context Collapse + reactive compact + LLM summary), build-agent worktree isolation, surgical Jupyter cell editing, ship-gate verifier, cache-boundary regression test, html skill, and bypass-proof destructive-command coverage (cloud / IaC / storage / DB / persistence / system overwrite). **v4.10.7**.

**Setup:** Run cells 1-3 in order. Cell 1 installs packages (once). Cell 2 shows config widgets. Cell 3 launches the agent.

**Core files:** `sagemaker_agent.py` (~11,800 lines) + this notebook + `memory.md` (auto-populated) + `AGENT_STATUS.md` (long-running handoff) + `skills/` (11 skills).

**Docs:** See `USER_GUIDE.md` for full documentation, `TEST_LOG.md` for Bedrock test results, `../CHANGELOG.md` for release notes.

### What's new in v4.10.7

**v4.10.7 — destructive-command hardening (cross-surface bypass-proof gate):**
1. **~50 new DANGEROUS_PATTERNS** covering cloud destructive subcommands (AWS/GCP/Azure), orchestration (kubectl/helm), IaC (terraform/terragrunt/pulumi), PaaS (heroku/vercel/netlify/wrangler/flyctl/railway), git (remote del/branch -D/tag -d/reflog expire/restore .), storage (lvremove/mkfs/dd to dev/zfs/btrfs/cryptsetup), persistence (crontab -r/systemctl disable/pm2 delete), DB CLI inline (DROP/TRUNCATE/DELETE/FLUSHALL/SHUTDOWN), system-path overwrite, perm lockout, curl|sh.
2. **~12 new DANGEROUS_PYTHON patterns** for cursor.execute DROP, SQLAlchemy drop_all, Mongo dropDatabase/deleteMany, Redis flushall, os.unlink/shutil.rmtree on system paths.
3. **HIGH_RISK_TOOLS = {bash, python_exec, task, web_fetch}** — excluded from Always-Approve UI shortcut, button hidden for those tools, no permanent bypass possible.
4. **Cross-surface propagation** — same denylist mirrored into Claude Code global hook + Learning_Factory source-of-truth hook. OPC inherits. Codex relies on its own sandbox.
5. New test file `test_v410_destructive_coverage.py` — 5 groups, 107 cases, all pass.

### What's new in v4.10.6

**v4.10.6 — html skill: presentation / design / flowchart / architecture HTML deliverables.** Ships 3 reference templates inside `skills/html/references/`. Screenshot-iteration loop (3 rounds) substitutes for Playwright on SageMaker. Anti-patterns enforced: no emojis, HTML IS KING, no truncated tables, Mermaid safe syntax.

### What's new in v4.10.5

**v4.10.5 — Learning_Factory pattern adoption (3 prompt-only additions, no functional changes):**
1. **Post-compact resume protocol** — agent no longer asks "what would you like me to do?" after compact. Reads summary + TODOs + AGENT_STATUS + recently-read files, continues from first unchecked task.
2. **Structured summary sections #12 + #13** — every LLM compact summary now captures Standing Constraints (hard rules surviving compact) and Critical Don't-Forget Context (1-3 most important re-orientation anchors).
3. **Skill self-patching 4-rule check** — was 1 rule, now 4 (Repeated + Non-trivial + Generalizable + Real-pitfall) + explicit memory-vs-skill distinction.
6 new tests, Codex PASS first review. Deliberately NOT adopted: LF's full hook ecosystem, smart-approval judge, tool-failure 5/3/8 (current 3-repeat doom-loop is stricter, not loosening).

### What's new in v4.10.4

**v4.10.4 — sub-agent work-context handoff (closes largest remaining review gap):**
1. Sub-agents now receive a bounded handoff block (AGENT_STATUS slice + active todos + last 10 changed files, paths only). Filled the gap where env-details alone left them flying blind on the larger goal.
2. Opt-out via `CONFIG.enable_subagent_handoff = False`. Boundary-marker sanitization protects against malicious or accidental literal markers in user content. 11 new tests, Codex PASS after 1 fix round.

### What's new in v4.10.3

**v4.10.3 — production-readiness review apply (4 small additions, all additive):**
1. **Ship-gate verifier** — `compact_v4/verify_ship_zip.py`. Run before any release.
2. **Cache-boundary regression test** — 6 tests guarding the static prompt prefix.
3. **Many-skill stress test** — verifies cap holds with 100 / 1000 skills.
4. **Clearer permission denials** — bash/security messages now explain WHY + WHAT to do.

### What's new in v4.10.2

**v4.10.2 — Verify-contract softened (Codex review surfaced contradiction):**
1. **Soft-by-default verify** — system prompt no longer demands verify after 3+ logic edits. It now SUGGESTS `/verify` and waits for user confirmation. Strict mode is opt-in via `CONFIG.enforce_verify_contract=True` in `agent_config.json`.
2. **Stale comment fix** — model dropdown comment updated from "Haiku default" to reflect v4.10.1's Sonnet 4.5 default.

### What's new in v4.10.1

**v4.10.1 — Context Collapse + default Sonnet 4.5:**
1. **`#41b` Context Collapse (segment-level)** — after microcompact replaces stale tool outputs with markers, runs of 3+ consecutive stale tool round-trips collapse into one synthetic Bedrock-safe assistant/user pair. Strict classification: thinking blocks / images / unknown types block the collapse, marker match is exact equality (not substring). 12 tests.
2. **Default model: Haiku 4.5 → Sonnet 4.5** — `au.anthropic.claude-sonnet-4-5-20250929-v1:0`. Cost is ~10x Haiku per token, but the prompt-cache checkpoint threshold drops from 4096 → 1024 tokens, so caching activates earlier and offsets the cost on multi-turn sessions. Switch back via `model_id` in `agent_config.json`.

### What's new in v4.10.0

**v4.10.0 — Runnable parity (5 additions, Codex-reviewed per phase):**
1. **`notebook_edit` tool** — surgically insert / replace / delete a single cell in an existing `.ipynb` (atomic write, preserves cell IDs, resets execution state on code cells). Use this — NOT `create_notebook` — when modifying an existing notebook so you don't blow away cells you didn't touch.
2. **Skill listing token budget** — `SkillManager.list_for_prompt` capped at 1% of context window (hard ceiling 2000 tokens). Auto-trigger surfacing also caps each description at 250 chars. Stops the prompt cache from being blown out by skill churn.
3. **Per-sub-agent env-details** — every sub-agent now sees a 4–6 line block (agent type, depth/max, workspace cwd, git HEAD, working-tree status) injected after the cached SYSTEM_PROMPT boundary. Means a fresh `verify` agent picks up parent's worktree swap automatically.
4. **Model-aware context window** — `BEDROCK_MODEL_CONTEXT_WINDOWS` map covers every Bedrock model. `CONFIG.context_max_tokens` auto-derives from `model_id` at startup. When AWS exposes 1M variants the only change is one entry in the map.
5. **Reactive Compact on `CONTEXT_OVERFLOW`** — when Bedrock rejects "prompt is too long" / "too many tokens", the agent runs microcompact (or placeholder-summary fallback if microcompact freed less than `MICROCOMPACT_MIN_SAVINGS`) and retries the same request once. From your perspective the request just succeeds.

**Skill auto-load REMAINS default OFF** (the v4.9.6 fix is intact). 55 new tests across 5 phases all green; `test_v49_auto_trigger.py` regression 12/12 still green. Codex caught 9 real correctness issues across the five phases — all fixed and re-verified before merging.

### What's new in v4.9.7

**v4.9.7 — Context diagnostic parity:**
1. **`/context` diagnostic** — shows context percentage, fixed overhead estimate, top tool request/result token sources, duplicate full-file reads, and the next recommended action.
2. **Runnable comparison close-out** — keeps V4 focused on SageMaker self-use: local git tree, explicit skills, durable status doc, and no GitHub/remote runtime assumption.

### What's new in v4.9.6

**v4.9.6 — Production hardening from deep review:**
1. **No skill auto-load by default** — `CONFIG.enable_skill_auto_trigger = False`; skills also need explicit `auto_trigger: true` before keyword matching can activate them.
2. **Bedrock-safe compaction** — compacted histories now start with a user summary plus assistant acknowledgement, avoiding assistant-first message history.
3. **Build worktree isolation fixed** — build sub-agents now actually create worktrees, see dirty/untracked parent files, merge back on success, and clean up.
4. **Parallel build safety** — build sub-agent calls serialize when worktree isolation is enabled because notebook `CONFIG.workspace` is process-global.
5. **Durable status handoff** — `AGENT_STATUS.md` is loaded each top-level run and `/status` can inspect or initialize it.
6. **Local-git-only SageMaker policy** — local git tree operations are supported; GitHub/`gh`/PR/push/pull/fetch/clone are not assumed.
7. **Regression tests** — `test_v42_gap_closure.py` covers the new failure modes.

### What's new in v4.7.2

**v4.7.2 — Self-review + design-first workflow:**
1. **`/design` skill** — NEW. Option analysis before coding. Produces Problem / Constraints / 2-3 Options with tradeoffs / Recommendation / Validation. Waits for user to pick before implementing. Triggers on `/design`, "compare approaches", "should I use", "tradeoff". **No extra token cost — only fires when invoked.**
2. **Auto diff-review at checkpoint** — CODE-LEVEL enforcement. After every auto-commit checkpoint, the agent now sees a diff-stat + 3-point self-review checklist (drift check / bugs / plan alignment). Fires deterministically (~95% reliable), survives compaction. **Minimal token cost — ~200 tokens per checkpoint, using cached system prompt.**
3. **Auto `/done quick` before completion** — system prompt rule: agent MUST run `/done quick` (simplify → verify → SHIP verdict) before declaring any task complete. ~80% reliable (prompt-level), but the checkpoint diff-review is the code-level backup. **Uses Bedrock prompt caching — review sub-agent calls reuse the cached system prompt.**

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
| Check context | `/context` (shows token bloat sources and duplicate file reads) |
| Activate skill | `/skill use review` |
| Deactivate one skill (sticky) | `/unskill clara-review` |
| Deactivate all skills (sticky) | `/skill clear` |
| List skills | `/skills` |
| Review pending skill patches (V4.9.5) | `/skill suggestions` |
| Apply a proposed skill patch (diff preview first) | `/skill apply report` then `/skill apply report --yes` |
| Reject pending patches | `/skill reject report` |
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

### Long-Running Status

`AGENT_STATUS.md` is loaded on every top-level run. Keep it concise and current for critical or multi-phase work: current goal, standing user instructions, plan, progress, blockers, changed files, verification, and next step. Use `/status`, `/status init`, and `/status path` from chat.

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
| design | 66 | Option analysis before coding — 2-3 approaches with tradeoffs, wait for user pick (v4.7.2) |
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

### Git Worktree Isolation (V4.4.0, hardened in V4.9.6)

When a **build** sub-agent runs, V4 protects your workspace:

1. If workspace is a git repo → creates an isolated worktree copy
2. If workspace is NOT a git repo → auto-initializes git (no credentials needed)
3. Dirty tracked files and untracked files are overlaid into the worktree so the build agent sees your current workspace state
4. On success → changes merged back to your workspace
5. On failure → changes discarded, your workspace is untouched

If multiple `build` sub-agents are requested at once, V4.9.6 runs them sequentially when worktree isolation is enabled. This preserves isolation because `CONFIG.workspace` is process-global inside the notebook kernel.

**You'll see these messages in chat:**
- `[Worktree] Auto-initialized git for workspace protection` (first time only)
- `[Worktree] Build agent isolated in: /tmp/_worktree_build_...`
- `[Worktree] N file(s) merged back to main workspace` (success)
- `[Worktree] Sub-agent failed — discarding worktree changes` (failure)

**No setup needed.** Works automatically. Your real git config is never touched.

**SageMaker git scope:** this is local git only. Use status/diff/log/worktree/local commits for review and safety. Do not expect GitHub, `gh`, PR creation, or remote git operations from the notebook runtime.

Disable with `"enable_worktree": false` in `agent_config.json` if not wanted.

### Version History

| Version | Key Changes |
|---------|-------------|
| V4.9.7 | Context diagnostic command: token bloat, tool-output sources, duplicate file reads, suggested action |
| V4.9.6 | Production hardening: no default skill auto-load, Bedrock-safe compact history, fixed build worktree isolation, dirty-state worktree overlay, serialized parallel builds, durable status doc |
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
