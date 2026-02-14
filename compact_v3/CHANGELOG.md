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
| `sagemaker_agent.py` | Enhanced | 6,341 (was 6,119 in V2) | +222 net new lines across 6 review rounds |
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

### Total Bug Fix Summary

| Severity | Count | Status |
|----------|-------|--------|
| HIGH | 4 | All fixed (rounds 1-4) |
| MEDIUM | 9 | All fixed (rounds 1-5) |
| LOW | 12 | All fixed (rounds 1-6) |
| LOW UX | 2 | All fixed (round 6) |
| **Total** | **27** | **All fixed** |
