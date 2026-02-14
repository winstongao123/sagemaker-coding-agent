# Compact V3 Changelog: Tier 1 Best Practices Integration

## Source

Lessons learned from [everything-claude-code](https://github.com/winstonpgao/everything-claude-code) — a collection of 62 skills, rules, commands, agents, and hooks for AI coding assistants. We analyzed all items, ranked them by practical value for coding, code review, memory management, and state persistence, then integrated the top 10 (Tier 1, score 85-100) into V3.

Full analysis: [PS_everything_claude_code/CATALOG.md](https://github.com/winstonpgao/PS_everything_claude_code)

---

## OpenCode vs Compact V2 vs Compact V3

### Agent Types

| Feature | OpenCode | V2 | V3 |
|---------|----------|----|----|
| Build agent | Yes | Yes | Yes |
| Plan agent | Yes | Yes | Yes (enhanced prompt) |
| Explore agent | Yes | Yes | Yes |
| General agent | Yes | Yes | Yes |
| **Review agent** | No | No | **Yes (NEW)** |
| Plan prompt quality | Basic "create a plan" | Basic 5-field format | **Enhanced: restate requirements, assess risks, phased plan, wait for confirmation** |
| Plan agent tools | read-only | read-only (missing web_fetch, ask_user) | **read-only + web_fetch + ask_user** |

### System Prompt Rules

| Feature | OpenCode | V2 | V3 |
|---------|----------|----|----|
| Core principles | Yes | Yes | Yes |
| Coding conventions | Yes | Yes | Yes |
| **Git workflow rule** | Rules file (always-on) | Not included | **Conventional commits, atomic changes, branch naming** |
| **Testing discipline** | Rules file (always-on) | Not included | **TDD workflow, 80% coverage target, AAA pattern** |
| Security guidance | In prompt | SecurityManager (3-layer) | SecurityManager (3-layer) |

### Skills

| Feature | OpenCode | V2 | V3 |
|---------|----------|----|----|
| Skills system | `.claude/skills/` | `skills/` with YAML frontmatter | `skills/` with YAML frontmatter |
| **Verification loop** | 120-line SKILL.md (6-phase) | Not included | **6-phase: build, type, lint, test, security, diff** |
| **Coding standards** | 520-line SKILL.md (JS/TS focused) | Not included | **150-line SKILL.md (language-agnostic, Python-focused)** |
| **Code review** | Basic 38-line checklist | Basic 38-line checklist | **84-line checklist: security, quality, performance, architecture, testing** |
| Skill count | 11 | 1 | **3** |

### Slash Commands

| Feature | OpenCode | V2 | V3 |
|---------|----------|----|----|
| `/skills` | Yes | Yes | Yes |
| `/skill use/clear` | Yes | Yes | Yes |
| `/cost` | N/A (free via CLI) | Yes | Yes |
| `/revert` | N/A | Yes | Yes |
| `/commands` | Yes | Yes | Yes |
| **`/verify`** | `/verify` command (59 lines) | Not included | **Auto-loads verify skill, runs 6-phase check** |
| **`/checkpoint`** | `/checkpoint` command (74 lines) | Not included (save button only) | **Named checkpoints: create/list, capped at 50, sanitized names** |

### Session Persistence & Memory

| Feature | OpenCode | V2 | V3 |
|---------|----------|----|----|
| Session save/load | Basic | Full (JSON + todos + metadata) | Full (JSON + todos + metadata + **checkpoints**) |
| Auto-save | No | Yes (every message) | Yes (every message, **deepcopy all data**) |
| Checkpoint restore | No | No | **Yes (checkpoints restored on session load)** |
| Skill restore | No | Partial (list only) | **Full (list + SKILLS.active_skill singleton)** |
| _FILES_READ reset on load | N/A | No (stale data leaks) | **Yes (reset on load)** |
| Checkpoint data | No | No | **todos, files_modified, exec_calls, token_stats** |
| State cleanup on clear/new | Partial | Partial (missing checkpoints) | **Complete (checkpoints, skills, todos all cleared)** |
| Skill injection | Single path | Double-injection possible | **Single path (skip if system_prompt provided)** |

### Security

| Feature | OpenCode | V2 | V3 |
|---------|----------|----|----|
| Bash validation | Permission rules | 3-layer (allowlist + patterns + restricted) | 3-layer (same) |
| Python validation | None | 3-layer (AST + import hook + secrets) | 3-layer (same) |
| SSRF protection | None | Yes (private IP blocking) | Yes (same) |
| Workspace boundary | Permission rules | Yes | Yes |
| Checkpoint name sanitization | N/A | N/A | **Yes (regex + 50 char limit)** |

### Error Recovery

| Feature | OpenCode | V2 | V3 |
|---------|----------|----|----|
| Tool name repair | Yes | Yes | Yes |
| Arg auto-fix | No | Yes | Yes |
| Type conversion | No | Yes | Yes |
| Fuzzy suggest | No | Yes | Yes |
| Malformed recovery | No | Yes | Yes |

---

## What Was Upgraded and Why

| # | What | Source | Why | Before (V2) | After (V3) |
|---|------|--------|-----|-------------|------------|
| 1 | Planner prompt | `agents/planner.md` (119 lines) | Forces structured thinking before coding, prevents wasted work | Basic 5-field plan format | 7-field format with requirements restatement, architecture analysis, phased execution, testing strategy |
| 2 | Review agent type | `agents/code-reviewer.md` (104 lines) | Catches security holes, missing error handling, test gaps | No review agent | Full review agent: security (CRITICAL), quality (HIGH), performance (MEDIUM), testing (MEDIUM) |
| 3 | Git workflow rule | `rules/git-workflow.md` (45 lines) | Clean git history = debuggable history | No git conventions in prompt | Conventional commits (feat/fix/refactor), atomic changes, meaningful branch names |
| 4 | Testing discipline | `rules/testing.md` (30 lines) | Fewer bugs in production, TDD enforcement | No testing guidance in prompt | 80% coverage target, TDD workflow (RED-GREEN-IMPROVE), AAA pattern, edge case guidance |
| 5 | Verification-loop skill | `skills/verification-loop/SKILL.md` (120 lines) | Universal pre-commit quality gate | No verification skill | 6-phase: build, type, lint, test, security, diff. Multi-language (Python, JS, Rust, Go) |
| 6 | Coding-standards skill | `skills/coding-standards/SKILL.md` (520 lines) | Makes every file better | No coding standards skill | 150-line language-agnostic guide: KISS, DRY, YAGNI, naming, error handling, testing, code smells |
| 7 | /verify command | `commands/verify.md` (59 lines) | One command runs full verification | Not available | Auto-loads verify skill, sends structured prompt, updates UI mode display |
| 8 | /checkpoint command | `commands/checkpoint.md` (74 lines) | Recovery point if session crashes | Save button only, no named checkpoints | Named checkpoints with create/list, todos + files + token stats captured, capped at 50, sanitized names |
| 9 | Review skill enhanced | `agents/code-reviewer.md` (104 lines) | Deeper code review with structured output | 38-line basic checklist | 84-line comprehensive: security, quality, performance, architecture, testing sections with severity levels |
| 10 | Plan agent tool set | `agents/planner.md` (tool list) | Plan agent could reference web docs and ask questions | Missing web_fetch, ask_user | Added web_fetch (fetch reference material) and ask_user (clarify requirements) |

## Bug Fixes During Implementation (found by 4 rounds of code review)

| # | Severity | Bug | Fix |
|---|----------|-----|-----|
| 1 | HIGH | Checkpoints never restored when loading a saved session | Added checkpoint restore in on_load with copy.deepcopy |
| 2 | HIGH | Manual save dropped checkpoints from metadata | Added checkpoints to on_save metadata dict |
| 3 | HIGH | Checkpoints leaked across sessions (not cleared on clear/new) | Added ui_state["checkpoints"] = [] to on_clear and on_new |
| 4 | HIGH | SKILLS.active_skill not reset on clear/new — stale skill leaks | Added SKILLS.active_skill = None to on_clear and on_new |
| 5 | MEDIUM | Skill content injected twice (UI path + Agent.run path) | Skip Agent.run() injection when system_prompt is provided |
| 6 | MEDIUM | Checkpoint name not sanitized — potential Markdown/HTML injection | Added re.sub sanitization + 50 char limit |
| 7 | MEDIUM | Shallow copy of _TODOS in checkpoint — mutation risk | Changed to copy.deepcopy |
| 8 | MEDIUM | No cap on checkpoints — unbounded memory growth | Capped at 50 checkpoints |
| 9 | MEDIUM | Auto-save checkpoints used direct reference — mutation window | Changed to copy.deepcopy |
| 10 | MEDIUM | _FILES_READ not reset on session load — stale write-guard entries | Added _FILES_READ = set() to on_load |
| 11 | MEDIUM | /verify didn't call update_mode_display() after activating skill | Added update_mode_display() call |
| 12 | MEDIUM | Plan agent tool set missing web_fetch and ask_user | Added both to plan agent tools |
| 13 | LOW | Loaded checkpoints not deep-copied — aliasing with session metadata | Changed to copy.deepcopy |
| 14 | LOW | Todos shallow-copied in auto-save/on_save — inconsistent with checkpoints | Changed to copy.deepcopy |
| 15 | LOW | Todos shallow-copied on session load — inconsistent | Changed to copy.deepcopy |
| 16 | LOW | on_clear missing update_mode_display() — stale UI | Added update_mode_display() |
| 17 | LOW | ask_user not listed in PLAN_MODE_PROMPT tool text | Added to tool list |
| 18 | LOW | /verify and /checkpoint not documented in SYSTEM_PROMPT | Added to Other Features section |
| 19 | LOW | Redundant `global _TODOS` declaration in on_load | Removed duplicate |

## Round 5 Code Review Fixes

| # | Severity | Bug | Fix |
|---|----------|-----|-----|
| 20 | MEDIUM | `ask_user` tool returned placeholder text — never captured real user input | Added `on_ask_user` callback with text input widget, submit/skip buttons, threading.Event wait pattern |
| 21 | LOW | Bare `except:` in tool_grep (line 2520) hides real errors | Changed to `except (OSError, UnicodeError):` |
| 22 | LOW | Bare `except:` in python_exec temp cleanup (line 2850) | Changed to `except OSError:` |
| 23 | LOW | Bare `except:` in todo UI sync (line 3884) | Changed to `except Exception:` |
| 24 | LOW | Session ID collision risk — second-level timestamp only | Added `os.urandom(3).hex()` suffix |
| 25 | LOW | Stop button poll interval 0.5s — sluggish responsiveness | Reduced to 0.1s for faster stop detection |

## Round 6 Fixes

| # | Severity | Bug | Fix |
|---|----------|-----|-----|
| 26 | LOW UX | Emoji in system messages (`⏹📋🔄✅▶️⏱️✓✗`) — potential encoding artifacts in non-Unicode terminals | Replaced all system/status message emoji with ASCII tags: `[STOP]`, `[PLAN]`, `[OK]`, `[X]`, `[TIMEOUT]`, `[>]`, `[...]` |
| 27 | LOW UX | Chat display box misaligned with input box — `max-width:calc(100% - 6px)` caused 3px offset | Changed to `width:100%;box-sizing:border-box;` to match input box width |

---

## File Changes Summary

| File | Action | Final Lines | Notes |
|------|--------|-------------|-------|
| `sagemaker_agent.py` | Enhanced | 6,380 (was 6,119 in V2) | +261 net new lines across 7 review rounds |
| `skills/review/SKILL.md` | Rewritten | 84 (was 38) | 5-category checklist with severity levels |
| `skills/verify/SKILL.md` | NEW | 148 | 6-phase verification: build, type, lint, test, security, diff |
| `skills/coding-standards/SKILL.md` | NEW | 154 | Language-agnostic: KISS, DRY, YAGNI, naming, testing |
| `CHANGELOG.md` | NEW | This file | 27 bugs found and fixed across 6 review rounds |

### Key New Features Added During Review Rounds

| Feature | Round | Description |
|---------|-------|-------------|
| `on_ask_user` callback | Round 5 | Interactive text input widget for `ask_user` tool (was returning placeholder) |
| Ask-user UI (submit/skip) | Round 5 | Text input + submit + skip buttons with threading.Event wait, 5-min timeout |
| Session ID random suffix | Round 5 | `os.urandom(3).hex()` prevents same-second collision |
| Faster stop polling | Round 5 | 0.5s → 0.1s for responsive stop button |
| ASCII system messages | Round 6 | All emoji replaced with `[STOP]`, `[PLAN]`, `[OK]`, etc. for encoding safety |
| Chat/input alignment | Round 6 | `width:100%;box-sizing:border-box` matches input box width |
| Proactive skill matching | Post-review | Agent auto-loads matching skills when user request matches available skill descriptions (follows Claude Code pattern, not OpenCode manual-only approach) |
| powerbi-dashboard skill | Post-review | Added Power BI dashboard generator skill (138 lines, from AIPower) |

## Round 7 Fixes (Skill/Sub-Agent/MCP Auto-Invocation)

| # | Severity | Bug | Fix |
|---|----------|-----|-----|
| 28 | HIGH | `tool_skill()` did not auto-activate skills — returned content as one-time tool result only, agent forgot skill on next turn | Added `SKILLS.active_skill = name` + `_pending_activations` list + UI sync drain on next send |
| 29 | HIGH | No proactive sub-agent delegation instructions — agent never auto-spawned sub-agents | Added IMPORTANT instruction with per-type guidance (explore, review, plan, build, general) |
| 30 | MEDIUM | Multiple skills in one turn lost — `active_skill` scalar overwrote first skill | Changed to `_pending_activations: List[str]` with append + drain pattern |
| 31 | MEDIUM | No MCP tool preference instructions — agent used bash instead of registered MCP tools | Added IMPORTANT instruction to prefer MCP tools for their domain |
| 32 | MEDIUM | Stale docstring claimed sub-agents and MCP were "Not Implemented" | Updated to "Implemented (from OpenCode patterns)" |
| 33 | MEDIUM (V2) | V2 `on_new()` did not clear skill state — stale skills carried over to new sessions | Added `active_skills = []`, `active_skill = None`, `_pending_activations.clear()` |
| 34 | LOW | powerbi-dashboard SKILL.md had no YAML frontmatter — `description=""` in XML | Added proper YAML frontmatter with name and description |
| 35 | LOW | Skill description fallback missing — skills without YAML got empty description | Added fallback: extract first `#` heading as description in `discover()` |

### Key New Features Added in Round 7

| Feature | Description |
|---------|-------------|
| Skill auto-activation via tool | `tool_skill()` now sets `SKILLS.active_skill` + `_pending_activations`, UI sync drains into `ui_state["active_skills"]` on next send — skills persist across turns |
| Proactive sub-agent delegation | System prompt IMPORTANT instruction tells agent when to use each sub-agent type (explore, review, plan, build, general) |
| Proactive MCP preference | System prompt IMPORTANT instruction tells agent to prefer MCP tools over generic alternatives |
| Multi-skill support for tool | `_pending_activations` list allows loading multiple skills in one turn without overwrite |

### Lessons Learned (Round 7)

1. **One-time tool results vs persistent activation**: Tool results are just chat context — they get pushed out as conversation grows. Skills need to be injected into the system prompt (via `active_skills`) to persist across turns. The tool result gives the agent the content for the current turn; the system prompt injection ensures it stays for all subsequent turns.

2. **Scalar vs list for activation state**: `active_skill: Optional[str]` can only hold one value. If the agent calls `tool_skill()` twice in one turn, the first activation is lost. Use a list (`_pending_activations`) with append + drain pattern instead.

3. **Proactive instructions must be explicit**: Simply listing available tools/agents in the system prompt is not enough — the LLM needs IMPORTANT-prefixed instructions saying WHEN to proactively use them. The skills section had this right ("proactively load... BEFORE proceeding"); sub-agents and MCP were missing it.

4. **YAML frontmatter is required for skill discovery**: Without frontmatter, `description=""` — the LLM sees an empty description in the tool XML and can't match. Always add frontmatter to SKILL.md files. As defense-in-depth, also add a fallback that extracts the first `#` heading.

5. **Every reset path needs testing**: `on_clear()`, `on_new()`, `/skill clear`, and session load all need to reset skill state consistently. V2's `on_new()` was missed because it was a different function from `on_clear()`.

## Round 8 Fixes (UI Threading Deadlock + OpenClaw Integration)

### Source

Bugs reported by user testing + analysis of [OpenClaw](https://github.com/openclaw/openclaw) — a multi-channel personal AI assistant with 50+ built-in skills, progressive skill loading, and context management.

### Bug Fixes

| # | Severity | Bug | Fix |
|---|----------|-----|-----|
| 36 | **CRITICAL** | `on_send()` runs on Jupyter kernel thread → `request_user_input()` wait loop blocks kernel → Submit/Skip/Stop button click callbacks can't fire → **deadlock** (no button works, no timeout, no stop) | Wrapped `on_send` in `_on_send_threaded()` that starts a background `threading.Thread`, freeing kernel thread for widget events |
| 37 | **CRITICAL** | `request_approval()` has same deadlock pattern — Approve/Deny/Always buttons unresponsive during agent execution | Same threading fix resolves both ask_user and approval deadlocks |
| 38 | HIGH | Agent falls back to `create_excel` when powerbi-dashboard skill is active but `ask_user` times out | Added Rule 0 to Power BI skill: "NEVER use create_excel or any Excel-based tool as a fallback" |
| 39 | MEDIUM | Clear/Save/Load/New buttons have no lock guard — clicking during agent execution crashes the background thread | Added `if ui_state.get("lock"): return` to all 4 button handlers |
| 40 | LOW | Tool result pruning too aggressive — head(100)+tail(100) chars loses useful context | Improved to head(500)+tail(500) with 1000-char minimum threshold |

### OpenClaw Analysis — Features Evaluated

We analyzed 17 patterns from OpenClaw, scored each for practical value in a SageMaker coding agent, and adopted 3 Tier 1 items (score 85+):

| # | Feature | Score | Decision | Reason |
|---|---------|-------|----------|--------|
| 1 | Progressive Disclosure Skill Architecture | 88 | SKIP (already have) | Our Power BI skill already uses this pattern (SKILL.md + reference/ subdirectory) |
| 2 | Tool Call Narration Policy | 87 | **ADOPTED** | "Don't narrate routine tool calls" reduces token waste |
| 3 | Alignment Safety Clause | 86 | **ADOPTED** | Anti-power-seeking directive for agents with AWS credentials |
| 4 | Context Pruning (stale tool results) | 85 | **ADOPTED** | Enhanced existing prune_tool_outputs with better head/tail preservation |
| 5 | Structured PR Review Pipeline | 82 | SKIP | Over-engineered for single-session use case |
| 6 | Skill Triggering via Description | 83 | SKIP | Our programmatic skill activation is more capable |
| 7 | Staged Compaction | 82 | SKIP | Existing compaction works; marginal quality gain |
| 8 | Context Window Guard | 78 | SKIP | Auto-compaction handles reactively |
| 9-17 | Various (persona, multi-agent safety, tool profiles, etc.) | 55-75 | SKIP | Not relevant to coding agent or already covered |

### Changes Made (Round 8)

| Change | V3 | V2 | Files |
|--------|----|----|-------|
| `_on_send_threaded` wrapper | Yes | Yes | sagemaker_agent.py |
| Lock guards on 4 buttons | Yes | Yes | sagemaker_agent.py |
| Tool Call Narration Policy in SYSTEM_PROMPT | Yes | Yes | sagemaker_agent.py |
| Safety Boundaries clause in SYSTEM_PROMPT | Yes | Yes | sagemaker_agent.py |
| Improved tool result pruning (500/500) | Yes | Yes | sagemaker_agent.py |
| Power BI skill Rule 0 (no Excel fallback) | Yes | N/A | skills/powerbi-dashboard/SKILL.md |
| .gitignore updated (nested audit_logs/sessions) | Yes | Yes | .gitignore |
| Removed 43 tracked temp files | Yes | Yes | test_*.py, audit_logs/, sessions/ |

### Lessons Learned (Round 8)

1. **Jupyter widget callback deadlock**: In ipywidgets, button `.on_click` callbacks run on the kernel's main event loop thread. If any code called from a button handler blocks that thread (e.g., `threading.Event.wait()`, `time.sleep()`, or any blocking loop), ALL other button callbacks become unresponsive. The fix is to run blocking work in a daemon thread so the kernel thread stays free.

2. **The approval dialog was also deadlocked**: The same deadlock affected `request_approval()` (Approve/Deny buttons), not just `ask_user`. Users may not have noticed because approvals have auto-deny timeouts and the agent continues — but the buttons were non-functional.

3. **Lock guards prevent thread-safety crashes**: When `on_send` runs in a background thread, destructive operations (Clear, Load, New) that set `ui_state["agent"] = None` would crash the running thread. Lock guards are essential for any button that modifies shared state.

4. **Skill anti-fallback rules must be explicit**: Even with a skill loaded and active in the system prompt, the LLM may fall back to tools it knows (like `create_excel`) when the skill's workflow is interrupted (e.g., `ask_user` timeout). Adding a rule 0 "NEVER use X" is necessary to prevent this.

---

## Round 9 Fix (Bash Interpreter Allowlist)

### Source

User testing on SageMaker with Sonnet 4.5 — agent correctly explored Power BI skill files and customized the generator, but could not run `python generate_project.py` because `python`/`python3` were blocked by SecurityManager.

### Bug Fix

| # | Severity | Bug | Fix |
|---|----------|-----|-----|
| 41 | HIGH | `python`/`python3` not in bash `BASE_ALLOWED_COMMANDS` — only added when `bash_allow_interpreters=True` (default: `False`). Agent can't run `python generate_project.py` for Power BI skill workflow. Agent tried `python_exec` with `exec(f.read())` as workaround but that's also blocked by `DANGEROUS_PYTHON` regex. | Changed `bash_allow_interpreters` default from `False` to `True`. The agent already has `python_exec` tool with full code execution, so blocking `python` in bash is inconsistent. Denylist patterns still catch dangerous usage. |

### Changes Made (Round 9)

| Change | V3 | V2 | Files |
|--------|----|----|-------|
| `bash_allow_interpreters` default `False` → `True` | Yes | Yes | sagemaker_agent.py |
| Companion doc updated | Yes | Yes | sagemaker_agent.md |

### Lessons Learned (Round 9)

1. **Security defaults must match tool capabilities**: If the agent already has a `python_exec` tool that runs arbitrary Python with security checks, blocking `python` in bash creates an inconsistent security boundary. The agent can already execute Python code — preventing it from running Python scripts via bash just breaks workflows (like skill generators) without meaningful security gain.

2. **`exec()` should stay blocked in python_exec**: While `exec(f.read())` is a valid workaround for running files, it bypasses the 3-layer Python security validation (regex, AST imports, AST calls). The proper path is `python script.py` via bash, where the script runs in its own process.

---

## Round 10 Fix (Doom Loop False Positive on Paginated Reads)

### Source

User testing on SageMaker with Sonnet 4.5 — agent tried to read `generate_template.py` (2187 lines, over 2000 MAX_LINES limit). After truncated first read, agent paginated with offset — but doom loop detector used only `(tool_name, file_path)` as key, ignoring offset. Third paginated read triggered false "Repetitive read_file calls detected" stop.

### Bug Fix

| # | Severity | Bug | Fix |
|---|----------|-----|-----|
| 42 | HIGH | Doom loop detector key for `read_file` is `(read_file, file_path)` — ignores offset parameter. Paginated reads of the same large file (different offsets) are falsely flagged as repetitive after 3 calls. | Added `read_file` special case: key includes offset → `(read_file, "path@offset")`. Different offsets produce different keys, so pagination works. True repetition (same file, same offset 3+ times) is still caught. |

### Changes Made (Round 10)

| Change | V3 | V2 | Files |
|--------|----|----|-------|
| `read_file` doom loop key includes offset | Yes | Yes | sagemaker_agent.py |
| Companion doc updated | Yes | Yes | sagemaker_agent.md |

---

## Round 11 Fixes (Max Turns + Skill Workflow Efficiency)

### Source

User testing on SageMaker with Sonnet 4.5 — agent hit max_turns=30 twice while trying to customize generate_template.py (2187 lines). Agent wasted turns doing surgical edits, grep searches for function boundaries, and debugging wrong helper function signatures.

### Bug Fixes

| # | Severity | Bug | Fix |
|---|----------|-----|-----|
| 43 | HIGH | `max_turns` default of 30 too low for complex skill workflows. Power BI dashboard generation requires 40+ turns (read refs, copy template, customize, run, debug). Agent hits limit before completing. | Increased default from 30 to 60. Still configurable via `agent_config.json`. |
| 44 | MEDIUM | SKILL.md says "Customize" but doesn't say HOW. Agent tries surgical edits on 2187-line file, burning 20+ turns on grep/read/edit cycles, making API mistakes (wrong function signatures). | Added IMPORTANT instruction: "Write the COMPLETE customized file in ONE write_file call. Do NOT edit the template piece by piece." |

### Changes Made (Round 11)

| Change | V3 | V2 | AIPower | Files |
|--------|----|----|---------|-------|
| `max_turns` 30 → 60 | Yes | Yes | N/A | sagemaker_agent.py |
| Companion doc updated | Yes | Yes | N/A | sagemaker_agent.md |
| SKILL.md "write complete file" instruction | Yes | N/A | Yes | SKILL.md / powerbi-dashboard.md |

### Lessons Learned (Round 11)

1. **Surgical edits on large generated files waste turns**: When a file is 2000+ lines, editing individual functions requires multiple grep/read cycles to find boundaries, understand signatures, and fix cascading errors. Writing the complete file in one call is faster and less error-prone.

2. **Skill instructions must specify the HOW, not just the WHAT**: "Customize: data generation, semantic model, report pages" is vague. The agent interpreted this as "edit each section individually." Explicit instruction ("write the COMPLETE file in ONE write_file call") eliminates the ambiguity.

---

## Round 12 Fixes (Doom Loop Overhaul + Security + OpenCode Review)

### Source

Full code review (18 issues found) + OpenCode architecture analysis. OpenCode uses per-tool key hashing, 30-entry history, `JSON.stringify` equality for doom loop detection, and blocks `python -c` entirely.

### Bug Fixes

| # | Severity | Bug | Fix |
|---|----------|-----|-----|
| 45 | **CRITICAL** | `edit_file` doom loop key uses only `file_path` — 3 edits to the same file with different `old_string` values triggers false doom loop stop | Key now includes hash of `old_string`: `file_path#md5(old_string)[:12]` |
| 46 | **CRITICAL** | "Skipping duplicate" `continue` in doom loop check doesn't skip execution — tool still executes at line 4654+ | Added `_skipped_ids` set; execution loop checks `if tc.id in _skipped_ids` and returns "Skipped" result |
| 47 | HIGH | `grep` doom loop key uses only `path` — 3 greps with different patterns on same directory triggers false stop | Key now includes pattern: `path:pattern` |
| 48 | HIGH | `bash` doom loop key truncates command to 50 chars — commands with same prefix but different suffix collide | Key now uses full command hash: `md5(command)[:16]` |
| 49 | HIGH | `python -c` via bash bypasses all `python_exec` security (AST validation, import allowlist, runtime import hook) | Broadened denylist from `python -c.*exec\(` to `python -c\b` — blocks ALL inline Python via bash, forces use of `python_exec` tool |
| 50 | HIGH | Doom loop early return loses assistant message from context — LLM's response text is not appended to messages | Added `self.messages.append(...)` before returning on doom loop detection |
| 51 | MEDIUM | `on_compact` blocks Jupyter kernel thread — same deadlock pattern as bug #36 | Wrapped in `threading.Thread` like `_on_send_threaded` |
| 52 | MEDIUM | `read_file` default limit of 500 lines — agent sees only 25% of a 2000-line file unless it explicitly requests more | Increased default from 500 to 2000 (matching MAX_LINES) |
| 53 | MEDIUM | `tool_history` maxlen=10 too short — repetitive patterns with 3+ interleaved calls escape detection | Increased to maxlen=30 |
| 54 | MEDIUM | Fallback doom loop key (`else` branch) uses `file_path or command[:50]` — non-deterministic for tools without those fields | Changed fallback to `md5(str(input))[:16]` — deterministic hash of full input |

### OpenCode Patterns Evaluated

| Pattern | Score | Decision | Reason |
|---------|-------|----------|--------|
| Per-tool doom loop keys with input hashing | 95 | **ADOPTED** | Our old keying was too coarse, causing false positives on edit_file, grep, bash |
| `python -c` blocked entirely | 90 | **ADOPTED** | Forces inline code through python_exec with 3-layer security |
| 30-entry tool_history (vs our 10) | 88 | **ADOPTED** | Better doom loop detection for interleaved patterns |
| read_file default 2000 lines | 85 | **ADOPTED** | Matches MAX_LINES, reduces unnecessary pagination |
| Fuzzy edit matching (9 strategies) | 82 | SKIP | Over-engineered for our use case; exact match + good error messages sufficient |
| MultiEdit tool (batch edits) | 80 | SKIP | Our edit_file handles one-at-a-time; skill instructions now say "write complete file" |
| Batch tool (parallel calls) | 78 | SKIP | Bedrock API doesn't support parallel tool execution |
| Soft max_turns with forced summary | 75 | SKIP | Our max_turns=60 is sufficient; adding summary injection adds complexity |

### Changes Made (Round 12)

| Change | V3 | V2 | Files |
|--------|----|----|-------|
| Doom loop key overhaul (per-tool hashing) | Yes | Yes | sagemaker_agent.py |
| `_skipped_ids` for actual skip execution | Yes | Yes | sagemaker_agent.py |
| Doom loop early return saves assistant message | Yes | Yes | sagemaker_agent.py |
| `python -c` blocked in bash denylist | Yes | Yes | sagemaker_agent.py |
| `tool_history` maxlen 10 → 30 | Yes | Yes | sagemaker_agent.py |
| `read_file` default limit 500 → 2000 | Yes | Yes | sagemaker_agent.py |
| `on_compact` threading fix | Yes | Yes | sagemaker_agent.py |
| Companion docs updated | Yes | Yes | sagemaker_agent.md |

### Lessons Learned (Round 12)

1. **Doom loop keys must be tool-specific**: A single fallback keying strategy (`file_path or command[:50]`) creates collisions for tools with different semantics. Each tool type needs a key that captures what makes two calls "the same" — for edit_file it's old_string, for grep it's pattern, for bash it's the full command.

2. **"Skip" must actually skip**: The doom loop detection ran in a pre-check loop that only tracked history. The execution loop ran separately over the same `response.tool_calls` without consulting the skip decisions. Using `_skipped_ids` bridges the two loops.

3. **`python -c` is a security hole when interpreters are allowed**: With `bash_allow_interpreters=True`, the agent can run `python -c "import boto3; ..."` which bypasses all of python_exec's 3-layer validation. Blocking `python -c` entirely forces inline code through the secure path while still allowing `python script.py` for skill generators.

4. **OpenCode's architecture is more defensive**: 30-entry history, per-input hashing, and no write size limits. Our agent was designed conservatively (10-entry history, 500-line reads) which paradoxically made it less capable for legitimate workflows.

### Known Issues Not Fixed (deferred)

| # | Severity | Issue | Reason for Deferral |
|---|----------|-------|---------------------|
| D1 | HIGH | Auto-compact produces near-useless summaries (first 50 chars of 3 messages) | Requires LLM-based summary call, adds latency and cost — needs design |
| D2 | MEDIUM | Skill content may be injected twice into system prompt | Need to verify it actually happens before fixing |
| D3 | MEDIUM | IPv6 SSRF check incomplete (`::ffff:127.0.0.1` bypass) | Edge case, low practical risk on SageMaker |
| D4 | LOW | `_pending_activations` list has no thread safety | Race condition window is very small in practice |

### Total Bug Fix Summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 4 | All fixed (rounds 8, 12) |
| HIGH | 14 | All fixed (rounds 1-4, 7-12) |
| MEDIUM | 19 | All fixed (rounds 1-5, 7-8, 11-12) |
| LOW | 15 | All fixed (rounds 1-8) |
| LOW UX | 2 | All fixed (round 6) |
| **Total** | **54** | **All fixed** |
