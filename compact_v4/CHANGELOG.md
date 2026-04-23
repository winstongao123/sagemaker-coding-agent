# Compact V4 Changelog

## v4.9.5 — Self-patching skills with safety rails (opt-in, handy use) (2026-04-23)

Hermes "closed learning loop" pattern — agent proposes improvements to its own SKILL.md files based on user corrections — but with **human-in-loop approval**. Opt-in via `CONFIG.enable_skill_patching = True` (default OFF). Previously rejected on insurance grounds; back on the table after user re-classified deployment as personal/handy use.

Flow: agent corrects same skill 3+ times → calls `skill_propose_patch` → patch lands in `skills/<name>/.proposed/<ts>.md` (NEVER live) → `/skill suggestions` lists pending → `/skill apply <name>` shows unified diff → `--yes` to apply (snapshots first) → existing `/revert <path>` undoes → audit logged at `audit_logs/skill_patches.jsonl`.

8 safety rails: opt-in flag, propose-not-apply, diff preview, snapshot before apply, audit log per event, `--edit` flag for tweaking, empty-name validation, tool no-ops when disabled.

Detailed: [`compact_v4/MAIN/changelogs/CHANGELOG_v4.9.5.md`](compact_v4/MAIN/changelogs/CHANGELOG_v4.9.5.md). Cross-repo decision: see audit doc §13.

Verification: **92/92 tests green** (19 new + 73 regression). py_compile + ast clean. No Codex (per `feedback_codex_skip_bedrock_patches.md`). Migration: none — fully additive, default OFF.

## v4.9.4 — Hermes patterns: cost ceiling + structured errors + smarter compaction (2026-04-23)

Six hermes-validated production-reliability enhancements, all Bedrock-only / no-external-network. Net change: **+336 / -33 lines** in `sagemaker_agent.py`. **73/73 tests green** (32 new + 41 regression).

1. **`IterationBudget`** — shared LLM-turn counter across parent + sub-agents. Default 90. Stops runaway sub-agent costs. Tunable via `CONFIG.max_iteration_budget`.
2. **`ErrorClassifier`** — ~10 Bedrock SDK exception categories with explicit recovery actions (retry-jitter / shrink-input / abort / etc.). Replaces scattered try/except.
3. **`RetryPolicy`** — jittered exponential backoff (base=1s, cap=30s, max=4) on throttle / transient / service-unavailable. Wired into `BedrockClient.chat()`.
4. **Pre-compact tool-result pruning** — cheap pass that trims oversized `tool_result` bodies (head 800 + tail 400 chars) before the summary LLM sees them.
5. **Auxiliary-model compaction** — opt-in `CONFIG.compaction_model` (e.g. Haiku) for ~10x cheaper summaries while main agent runs Sonnet/Opus.
6. **Structured "Resolved/Pending Questions" sections** in summary template — explicit Q/A blocks on top of the existing 9-section format. Pending Questions = first thing to look at on resume.

Detailed: [`compact_v4/MAIN/changelogs/CHANGELOG_v4.9.4.md`](compact_v4/MAIN/changelogs/CHANGELOG_v4.9.4.md). Cross-repo comparison + adopted/rejected matrix: see audit doc §12.

No Codex this round (per `feedback_codex_skip_bedrock_patches.md`). Migration: none — fully additive, defaults preserve existing behaviour.

## v4.9.3 — Cross-repo enhancements (Bedrock-only fit) (2026-04-23)

Five enhancements pulled from a deep-scan comparison against `gg-claude-code-runnable`, `hermes-agent`, and `Learning_Factory`, filtered for the actual deployment target (SageMaker + Bedrock-only + no external network, insurance-company environment):

1. **Prompt-injection scanner** on `memory.md` / `CLAUDE.md` / `SKILL.md` loads — flags instruction-override, role-hijack, fake reminder tags, exposed credentials, invisible chars (advisory, doesn't block)
2. **CSO description validator** on skill discovery — warns when a skill's frontmatter description text doesn't start with "Use when"
3. **New `/reflexion` skill** — 3-pass critique-refine-judge for high-stakes outputs
4. **SYSTEM_PROMPT** Handling-Critique section gains spec-first ordering rule
5. Doom-loop detection (already existed at line 7368) confirmed — no change needed

Rejected for fit: MCP integration, OpenRouter routing, multi-platform messaging, self-patching skills, mixture-of-agents voting (cost), error classifier (defer to v4.10), permission rule engine (defer to v4.10).

Detailed: [`compact_v4/MAIN/changelogs/CHANGELOG_v4.9.3.md`](compact_v4/MAIN/changelogs/CHANGELOG_v4.9.3.md). Full cross-repo comparison: see audit doc §11.

Verification: **41/41 tests green** (11 new + 30 regression). py_compile + ast clean. No Codex (per `feedback_codex_skip_bedrock_patches.md`).

## v4.9.2 — Doc alignment + minimum-ship zip (2026-04-23)

Documentation-only patch. Closes the three doc gaps surfaced by the v4.9.1 production-readiness scan: `/unskill` is now documented in `USER_GUIDE.md`, `chat.md`, and the agent's own `SYSTEM_PROMPT # Commands` line. Tightens the shipping bundle to runtime essentials only — `compact_v4.zip` shrinks from 40 → **25 files / 239 KB** by dropping test files, dev artefacts, audit docs, historical HTMLs, and `.git`/`__pycache__/.snapshots/.pytest_cache/.code_index/` runtime caches.

Detailed: [`compact_v4/MAIN/changelogs/CHANGELOG_v4.9.2.md`](compact_v4/MAIN/changelogs/CHANGELOG_v4.9.2.md).

No behavioural change. 30/30 tests still green. Migration: none.

## v4.9.1 — /unskill + sticky deactivation + critique-prompt tightening (2026-04-23)

Patch release completing audit §8 coverage. Adds `/unskill <name>` command and sticky deactivation so `/skill clear` and `/unskill` can't be silently undone by the next user message. Tightens the "Handling Critique" SYSTEM_PROMPT section (concrete `read_file` tool call, workspace-absent fallback, concise-ACCEPT exception). Fixes one logic bug found in diff review (`/unskill <nonexistent>` no longer silently succeeds).

Detailed: [`compact_v4/MAIN/changelogs/CHANGELOG_v4.9.1.md`](compact_v4/MAIN/changelogs/CHANGELOG_v4.9.1.md).

Verification: 11/11 v4.9 tests + **10/10 new v4.9.1 tests** + 9/9 v4.7.1 regression tests (30/30 total green), py_compile + ast clean. No Codex this round (patch scope is Bedrock agent UI handlers + prompt text — Codex's generic lens adds nothing here over self-review).

## v4.9.0 — Skill auto_trigger fix + critique-handling rule (2026-04-23)

Fixes the silent `auto_trigger: false` bug shipped in v4.8.0 (opt-out flag parsed but never honoured by the keyword auto-match loop) + hardens keyword match against substring false-positives + adds a SYSTEM_PROMPT rule for handling critiques of the agent's own work + makes skill auto-injection visible to the user with an approximate char-count.

Detailed audit: [`compact_v4/docs/V4_8_SKILL_AUTOTRIGGER_AUDIT.md`](compact_v4/docs/V4_8_SKILL_AUTOTRIGGER_AUDIT.md). Per-change spec: [`compact_v4/MAIN/changelogs/CHANGELOG_v4.9.0.md`](compact_v4/MAIN/changelogs/CHANGELOG_v4.9.0.md).

Verification: self-review (11/11 new tests + 9/9 regression tests green, py_compile/ast clean) + Codex review with `gpt-5.3-codex` (NEEDS-FIX → fix applied → PASS on re-review).

## v4.7.1 — Local-git baseline + compact-survives-TODOs + /regression (2026-04-12)

Base: compact_v4 v4.7.0

### Why This Release (and what was deliberately NOT added)
v4.7.0 shipped six UX features, most of which turned out to be polish. This release is the opposite — **three targeted fixes to real problems**, nothing more. We explicitly rejected auto-test-on-edit, block-on-lint-error, test-framework detection, and test-baseline tracking as overcomplication for a solo coding+review workflow where `/verify`, `/done`, and manual test runs already cover the need.

### 1. Compact now preserves TODO list (real bug fix)
**Before:** When v4 auto-compacted at 80% context, `_TODOS` survived as a sidebar widget but was **not injected into the post-compact message history**. The agent literally lost its task plan across compaction unless the user manually retyped it.

**After:** [`Compactor.compact()`](compact_v4/MAIN/agent/sagemaker_agent.py) now calls a new helper `build_todo_restoration_message()` and merges its output into the post-compact user message alongside the existing file-restoration block. The agent wakes up from compaction seeing:

```
[POST-COMPACT TODO RESTORATION — your task plan from before compaction]

**In progress:**
  🔄 Fix the auth bug

**Pending:**
  ⬜ Write tests
  ⬜ Deploy to staging

**Completed (10):**
  ✅ Refactor tokens  ... and 7 earlier

[Continue from where you left off. Use todo_write to update status.]
```

In-progress shown first (most actionable), pending next, completed truncated to the last 3 (context without bloat). Handles empty todos cleanly (returns `None`, no wasted tokens).

### 2. Auto-commit checkpoint (local-git baseline maintenance)
**Problem:** v4 already shows `git diff HEAD` after every edit — but only if HEAD is recent. If you don't `git commit` for two hours, the diff grows unbounded and stops being useful for "what did this edit change".

**Fix:** New `Config.auto_commit_every: int = 0` (default disabled). When set to N > 0, every N successful edits runs `git commit -am "agent-checkpoint HH:MM:SS (auto)"` locally. **Never pushes.** Keeps `git diff HEAD` always showing only the latest change set.

Silently skipped when:
- Not inside a git repo
- Nothing staged (no changes since last commit)
- Threshold not yet reached

Integrated into both [`tool_write_file`](compact_v4/MAIN/agent/sagemaker_agent.py) and [`tool_edit_file`](compact_v4/MAIN/agent/sagemaker_agent.py) after auto-lint. Non-blocking — any failure is swallowed so it can never break an edit.

### 3. `/regression` thin-wrapper command
Wraps three existing signals into one command for a fast "did I break anything" check:
- `git diff HEAD --stat` (uncommitted files since last commit)
- Session diff summary from `_RECENT_DIFFS` (per-file edit counts this session)
- Suggested test command (`pytest -x -q` if pytest config exists, else `python -m unittest discover -v`)

**Explicitly does NOT:**
- Run tests automatically (user decides)
- Track baseline / detect regressions (use `/verify` for that)
- Parse test output (trust bash + pytest)

~30 lines. Pure convenience over existing primitives. No new state, no new deps.

### Files Changed
- `compact_v4/MAIN/agent/sagemaker_agent.py` — +147 lines (9,719 → 9,866)
  - `Config.auto_commit_every: int = 0` field added
  - `_AUTO_COMMIT_COUNTER`, `_AUTO_COMMIT_LOCK`, `_maybe_auto_checkpoint()` helpers added
  - `build_todo_restoration_message()` helper added
  - `Compactor.compact()` extended to merge TODO restoration into post-compact user message
  - `tool_write_file` + `tool_edit_file` call `_maybe_auto_checkpoint()` after auto-lint
  - New `/regression` slash command handler
  - System-prompt commands line updated with `/regression`
- `compact_v4/MAIN/agent/test_v471_enhancements.py` — **NEW**, 9 real tests (see Verification)
- `compact_v4/CHANGELOG.md` — this entry

### Verification — real tests, not just py_compile
`test_v471_enhancements.py` creates temp git repos and calls real functions. **9/9 PASS:**

```
[auto-commit checkpoint]
  ✓ auto_commit disabled by default
  ✓ auto_commit fires at threshold
  ✓ auto_commit no-op when nothing staged
  ✓ auto_commit no-op outside git repo

[todo restoration helper]
  ✓ empty todos returns None
  ✓ mixed statuses render correctly
  ✓ long completed list is truncated

[compact integration]
  ✓ compact includes todo restoration
  ✓ compact works fine without todos

Result: 9/9 passed
```

Static checks also PASS:
- `py_compile` clean
- `ast.parse` clean
- Warnings-as-errors clean
- Module import succeeds (confirmed `CONFIG.auto_commit_every`, `_maybe_auto_checkpoint`, `build_todo_restoration_message`, `Compactor.compact` all load)

**NOT tested:** Jupyter UI render of `/regression` output (requires live SageMaker kernel). The command handler was verified statically.

### Explicitly rejected (documented so future releases don't re-litigate)

| Feature | Why rejected |
|---|---|
| `auto_test_on_edit` | Runs tests on every edit — slow, noisy, breaks flow. `/verify` already covers user-invoked testing. |
| `block_on_lint_error` | Auto-lint already warns on syntax errors. Blocking is annoying and rarely the right move (sometimes you edit mid-refactor). |
| `_detect_test_framework` / `_run_tests_quick` / `_check_test_regression` / `_LAST_TEST_STATE` | All ~200 lines of framework detection and baseline tracking were in service of auto_test_on_edit. Removing the feature removed the need for all of this. |
| `Config.test_timeout_seconds` / `Config.test_target` | Only useful with auto_test_on_edit. Dropped with it. |
| Module split | Violates "one file SageMaker" constraint. |

---

## v4.7.0 — Coding UX Enhancements: /done gate, /diffs, phase display, budget bar, revert preview, checkpoint restore (2026-04-12)

Base: compact_v4 v4.6.1

### Why This Release
Audit against Learning Factory patterns found five gaps in solo-developer UX: no pre-ship gate, no session-diff browsing, no task/phase indicator, no visual budget warning, no diff preview before revert, no checkpoint restore. All five (plus `/diffs`) now implemented inline in `sagemaker_agent.py` — no new files, no new dependencies, no Codex CLI, no git hooks. Pure Python additions fit the SageMaker notebook + Bedrock runtime.

### New Commands

#### `/done [full|quick]` — Pre-ship gate
Chains `simplify` → `verify` skills with a mandatory final verdict. Agent must produce:
- **SIMPLIFY:** what was changed or "nothing"
- **VERIFY:** PASS / FAIL / PARTIAL with command+output evidence
- **FINAL:** READY-TO-SHIP / NEEDS-WORK / BLOCKED

Refuses to claim "done" unless VERIFY = PASS. Auto-loads both skills, sets phase to `done-gate:<scope>`.

#### `/diffs [summary|last|<file>]` — Session edit history
Exposes the existing `_RECENT_DIFFS` buffer (50-entry rolling window, populated on every Write/Edit).
- `/diffs` or `/diffs summary` — per-file edit counts
- `/diffs last` — show most recent diff
- `/diffs <filename-substring>` — last 3 matching diffs with truncation at 3K each

#### `/phase <text>` / `/phase clear` — Work phase label
Sets a free-form phase shown in both the mode row and the token display. Defaults to `skill:<active>` when no phase is set but a skill is active. 80-char cap.

### Enhancements

#### `/revert` — Diff preview before destructive action
Previously: `/revert <file>` blindly restored the latest snapshot. Now shows a unified diff (current → snapshot) and requires `--yes` to execute. `/revert all` also gated behind `--yes` and lists every affected file first. Early-exit when current already matches snapshot.

#### `/checkpoint restore <name>` — Restore todos from checkpoint
Previously: `/checkpoint list` showed saved checkpoints but no restore path. Now restores `_TODOS` from the named checkpoint and lists which files had been modified at checkpoint time. File-level restore is explicitly NOT auto-applied — user reviews the file list and uses `/revert <file>` per file (safer than blind batch revert).

#### Status bar — Phase indicator
`update_mode_display()` (mode row) now shows `Phase: <text>` after the cost indicator, color-coded cyan. Falls back to `skill:<name>` when no manual phase set.

#### Token display — Budget progress bar
`update_tokens_display()` now renders a 4px progress bar under the context bar when `CONFIG.session_cost_limit > 0`. Green <80%, orange 80–99%, red ≥100%. The backend alert logic (warn at 80%, stop at 100%) already existed at line 2858 — this adds the missing visual.

Also adds `🎯 Phase: <text>` line above the token stats when a phase is set.

### Files Changed
- `compact_v4/MAIN/agent/sagemaker_agent.py` — +214 lines (9505 → 9719)
  - `ui_state["session_phase"]` key added
  - `update_mode_display()` phase part
  - `update_tokens_display()` budget_block + phase_block
  - `/revert` handler: diff preview + `--yes` gate
  - `/checkpoint` handler: new `restore` branch
  - `/done`, `/diffs`, `/phase` handlers added before custom-commands dispatch
  - System-prompt commands line updated

### Verification
- Python syntax: PASS (`py_compile` + `ast.parse`)
- Warnings-as-errors: CLEAN
- Feature markers: 9/9 present
- Not tested: Jupyter UI render (requires SageMaker kernel)

### What Was NOT Ported From Learning Factory
Explicitly evaluated and rejected as unfit for SageMaker+Bedrock solo runtime:
- `codex-judge-gate.sh` / `pre-commit-diff-review.sh` — require local Codex CLI + git pre-commit; v4 already auto-diffs on every Edit at line 3658 and routes review through inline `simplify`/`verify` skills
- `auto-push.sh` / main-push gates — SageMaker notebooks don't commit from the kernel
- `rollback.sh` (shadow-git) — v4's `SnapshotManager` (line 3357) already provides this natively in Python
- Claude Code `settings.json` hooks infrastructure — enforced via `Config.permission_rules` and `ban_patterns`, not bash hooks
- Windows-specific paths in hook scripts — Linux-only SageMaker env

### Design Note: Why `/done` Over Auto-Run-On-Stop
Considered auto-running verify on every "done" intent detection but rejected: too noisy, burns tokens on trivial turns, hides cost. Explicit `/done` command is user-driven — ships only when the user signals intent, matches the existing `/verify` pattern, and produces a named verdict the user can act on.

---

## v4.6.1 — Workspace Path Resolution Fix (2026-04-10)

Base: compact_v4 v4.6.0

### Why This Release
Real-session bug: agent launched in a subfolder could not find files that lived in the parent repo even though `allowed_paths` had auto-detected the repo root. Symptoms:
- `glob "**/sagemaker_agent.py"` returned `"No files found"` (only searched workspace)
- `read_file wins_docs/compact_v4/sagemaker_agent.py` worked (via `_resolve_path` → allowed_paths) but the agent trusted glob's negative result first and gave up
- Error messages didn't show the workspace root or allowed roots, so the agent had no way to self-correct
- Agent never announced its workspace, so users couldn't spot CWD mismatches

Sonnet 4.6 blamed itself for "habit failure" — but the real cause was architectural: the tools gave it no way to know where it was.

### Fixes

#### 1. `_build_workspace_info()` injected into cached system prompt
New helper emits a workspace block (Root + allowed paths + recovery instructions). Injected BEFORE the `# === DYNAMIC ===` marker in `Agent.run()`, so it's part of the cached block — zero per-turn cost.

#### 2. `tool_glob` falls through to `allowed_paths`
When the workspace search returns empty AND no explicit `path` arg was given, glob retries against every root in `SECURITY.allowed_paths`. Previously it returned `"No files found"` even though `read_file` could reach the file. Result lines now append `[Searched N roots (workspace + allowed_paths): ...]` when fall-through was used.

#### 3. Informative error messages (self-correcting)
- `validate_path` "outside workspace" — now includes resolved path, workspace root, allowed roots, and a `glob "**/<filename>"` suggestion
- `tool_read_file` "file not found" — now includes raw requested path, resolved path, workspace root, allowed roots, and `glob`/`bash find` recovery templates
- `tool_glob` "no files found" — now lists searched roots and suggests a broader pattern

#### 4. Workspace announcement on first `run()` call
Top-level agent prints `[Workspace: /path] [Also accessible: /other]` on first turn of the session. Users can spot CWD mismatches before the first file operation.

### Files Changed
- `compact_v4/MAIN/agent/sagemaker_agent.py` — 4 tool impls, 1 new helper, 1 `Agent.run()` injection, 1 `Agent.__init__` field
- `compact_v4/MAIN/agent/test_v461_path_fix.py` — NEW unit test (11 checks, all PASS)

### Verification
- Python syntax: PASS (`ast.parse`)
- Unit test: **11/11 PASS**
  - Fresh git repo created in tempdir
  - Workspace set to `<repo>/subproj/agent/` (subfolder, mirrors real failure scenario)
  - Target file at `<repo>/wins_docs/compact_v4/sagemaker_agent.py` (outside workspace, inside repo)
  - All 4 code paths verified: workspace info block, glob fall-through, read_file via allowed_paths, rich error messages
- No behavior regressions — all changes are additive and gated behind `not all_raw and not explicit_path` or trigger only in error paths

### Cost
Workspace info block ≈ 125 tokens added to cached static portion. One-time cache WRITE premium per session; cache HITs unchanged. Effective cost increase: ~$0.0001 per session.

### Distribution Bundle Changes
- `compact_v4.zip`: rebuilt, 46 files (was 59). Excludes `skills/powerbi-dashboard/` and `skills/powerbi-dashboard-v2/` — these remain in the source repo but are not shipped in the distribution bundle. Ship bundle now contains 8 skills: batch, clara, coding-standards, report, review, security-review, simplify, verify.
- `wins_docs.zip`: rebuilt, 26 files. Same skill filter applied. Same 8 skills.
- Reason: Power BI skills are AIPower-specific and not relevant to general SageMaker coding tasks. Source repo keeps them for the AIPower sync path.

---

## v4.6.0 — Runnable-Grade Review System: Adversarial Verification + Parallel Review (2026-04-10)

Base: compact_v4 v4.5.0

### Why This Release
V4's review and verification system was functional but far behind Runnable (Claude Code's internal implementation).
Deep comparison revealed 3 critical gaps:
1. **Single-pass review** vs Runnable's 3-agent parallel specialization
2. **Confirmatory verification** vs Runnable's adversarial "try to break it" approach
3. **No security review** vs Runnable's 3-phase vulnerability assessment with false-positive filtering

This release ports Runnable's best prompt engineering patterns into V4's skill + sub-agent system.

### New Skills

#### `simplify` — 3-Agent Parallel Code Review + Fix (NEW)
- **What**: Port of Runnable's `/simplify` skill. Reviews changed code using 3 parallel specialized agents.
- **Agents**: Code Reuse (search for duplicate utilities) + Code Quality (anti-patterns) + Efficiency (N+1, hot-path, memory leaks)
- **Workflow**: `git diff` → launch 3 review agents in parallel via `task` tool → aggregate → fix issues directly
- **Key difference from old review**: Agents search the BROADER codebase for evidence (existing patterns, utilities)
- **File**: `skills/simplify/SKILL.md`

#### `security-review` — 3-Phase Vulnerability Assessment (NEW)
- **What**: Port of Runnable's security review command. Focused on signal quality over volume.
- **3 phases**: Repository context research → Comparative analysis → Vulnerability assessment
- **Confidence scoring**: 0.8-1.0 only reported. Below 0.8 = too speculative, excluded.
- **14 hard exclusions**: DOS, secrets-on-disk, rate limiting, regex DOS, theoretical race conditions, etc.
- **7 precedents**: UUIDs unguessable, env vars trusted, React XSS-safe, etc.
- **Output**: Severity (HIGH/MEDIUM only) + Exploit Scenario + Specific Recommendation
- **File**: `skills/security-review/SKILL.md`

### Upgraded Skills

#### `verify` — Adversarial Verification (REWRITTEN)
- **Before**: 6-phase checklist (build, type, lint, test, security, diff). Confirmatory — checked if things work.
- **After**: Adversarial specialist that tries to BREAK the implementation. Ported from Runnable's verification agent.
- **New sections**:
  - **Failure Patterns**: Verification avoidance + "seduced by first 80%" (Runnable pattern)
  - **Anti-rationalization rules**: "reading is not verification", "tests pass means nothing", "probably is not verified"
  - **Type-specific strategies**: Backend/API, CLI, bug fixes, refactoring, Python, data pipelines
  - **Adversarial probes**: Boundary values, concurrency, idempotency, orphan operations
  - **Evidence format**: Every check MUST have Command run + Output observed + Result (no narrative PASS)
  - **Before PASS/FAIL gates**: Must include adversarial probe; must check if "FAIL" is actually intentional
  - **VERDICT requirement**: Machine-parseable `VERDICT: PASS/FAIL/PARTIAL`
- **File**: `skills/verify/SKILL.md`

#### `code-review` — Parallel Review with Fix Loop (REWRITTEN)
- **Before**: Static 5-category checklist (security, quality, performance, architecture, testing). Single pass, report only.
- **After**: 5-phase process: scope → security check → 3 parallel agents → aggregate+fix → report+feedback.
- **New**: Launches 3 parallel review agents (same pattern as simplify)
- **New**: Issues Fixed section (review now fixes, not just reports)
- **New**: Feedback Refinement section (user can provide feedback, review re-examines and updates)
- **File**: `skills/review/SKILL.md`

### Upgraded Agent Types (sagemaker_agent.py)

#### `verify` agent type — prompt_suffix rewritten
- Added: Failure patterns to avoid (verification avoidance, seduced by first 80%)
- Added: Anti-rationalization rules (4 specific excuses named and countered)
- Added: Type-specific verification strategies (Backend, CLI, bug fixes, refactoring, Python)
- Added: Adversarial probe requirement before PASS
- Added: Before-FAIL gate (check if intentional/already handled)
- Added: Evidence format enforcement (command + output required, no narrative)
- Retained: VERDICT: PASS/FAIL/PARTIAL machine-parseable output

#### `review` agent type — prompt_suffix rewritten for parallel specialization
- **Before**: Generic "senior code reviewer" with monolithic checklist
- **After**: "Specialized code review sub-agent" designed for parallel execution
- New: Assigned-dimension focus (reuse OR quality OR efficiency)
- New: Specific checks for each dimension (7 reuse, 8 quality, 7 efficiency)
- New: "Be specific" guidance ('file.py:42-95 extract lines 60-80' not 'function too long')
- Retained: Security always checked regardless of assigned focus

### What Changed (File Summary)
| File | Change | Lines |
|------|--------|-------|
| `skills/simplify/SKILL.md` | NEW — 3-agent parallel review | 60 lines |
| `skills/security-review/SKILL.md` | NEW — 3-phase security assessment | 120 lines |
| `skills/verify/SKILL.md` | REWRITTEN — adversarial verification | 150 lines |
| `skills/review/SKILL.md` | REWRITTEN — parallel review + fix | 120 lines |
| `sagemaker_agent.py` | UPGRADED — verify + review prompt_suffix | +33 net lines |

### Gap Closure: 6 of 7 Runnable Gaps Closed
Deep audit identified 7 remaining gaps vs Runnable. 6 closed in this release (Gap #7 skill discovery skipped — not relevant to SageMaker workflow).

**Gap #1 — Verification Contract (PROMPT)**
- New `# Verification Contract` section in SYSTEM_PROMPT
- MUST verify after 3+ non-trivial file edits (logic, API, data flow)
- Explicitly excludes docs-only, config tweaks, single-file obvious fixes

**Gap #2 — USE WHEN Guidance (PROMPT)**
- Each of 6 agent types now has `USE WHEN:` in task tool description
- Model knows: explore for search, plan for design, verify after edits, build for multi-file, review for code review

**Gap #3 — Multi-Agent False-Positive Filtering (SKILL)**
- Security-review skill gets new Step 4: independent verification pipeline
- 2+ findings → spawn parallel review agents, each verifies ONE finding
- Only findings with confidence >= 0.8 survive

**Gap #4 — Auto-Nudge (CODE)**
- `tool_todo_write()` detects 3+ completed tasks without verification
- Injects NOTE: "Per Verification Contract, spawn verify sub-agent"
- Mirrors Runnable's TodoWriteTool.ts:104-107 nudge pattern

**Gap #5 — Critical Reminder Injection (CODE)**
- New `critical_reminder` field in AGENT_TYPES (verify + review)
- Injected LAST in sub-agent system prompt (closest to model attention)
- Verify: "VERIFICATION-ONLY. Command run + Output observed required."
- Review: "READ-ONLY. Every finding needs file:line + severity + fix."

**Gap #6 — Fork Semantics (CODE)**
- New `fork` agent type with `fork: True` flag
- `Agent.__init__` accepts `initial_messages` (deep-copied from parent)
- Fork child inherits full conversation context — directive-style prompts
- Prompt cache sharing automatic (same system prompt)

**Gap #7 — Skill Discovery Auto-Surfacing (CODE)**
- New `triggers` field in skill YAML frontmatter (comma-separated keywords)
- `SkillInfo.triggers` parsed from frontmatter during `discover()`
- `SkillManager.discover_relevant(user_message)` matches message against triggers
- Relevant skills injected into system prompt as `# Skills Relevant to This Task`
- Trigger specificity prevents confusion: clara triggers on "claims, insurance, compliance"; code-review triggers on "code review, review pr, review diff"
- Tested: "review code" → code-review; "review claims" → clara; "vulnerabilities" → security-review
- All 7 review skills given distinct triggers (no overlap)

### Coordinator-Worker Orchestration (Batch Skill)
- **NEW `batch` skill** — coordinator-worker pattern for large multi-file tasks (5+ files)
- 6 phases: Research → Decompose into 3-30 units → Present plan → Spawn parallel workers → Track progress → Synthesize
- **Role separation enforced**: coordinator NEVER writes code, workers NEVER plan
- Each worker gets self-contained prompt with: goal, task, files, conventions, test recipe
- Workers use `build` agent type (isolated in git worktree)
- Coordinator tracks status table (DONE/FAILED/RUNNING) and runs final verification
- Mirrors Runnable's `batch.ts` + `coordinatorMode.ts` pattern
- Auto-discovered via triggers: "large refactor", "migrate all", "bulk change", "many files"

### Bug Fixes (Post-Release)
- **Sub-agent git access**: Skills now instruct parent to pass `git diff` output in sub-agent prompts (sub-agents can't find `.git` at repo root). Fix: simplify T7 time 58s → 5s.
- **Verify evidence format**: Added CRITICAL REMINDER to verify agent prompt_suffix for format enforcement.

### Verification
- Python syntax check: PASS (ast.parse, 9,305 lines)
- Git diff: Only prompt strings changed (no logic/structure changes)
- No code regression: All existing functionality preserved
- **Live Bedrock: 8/8 PASS on Sonnet 4.6** (23s verify, 195s simplify, 47s security)
- **Live Bedrock: 8/8 PASS on Haiku 4.5** (18s verify, 5s simplify, 15s security)
- Playwright: 6/6 PASS

### Patterns Ported from Runnable
1. **Parallel agent specialization** — decompose review into orthogonal concerns, run concurrently
2. **Anti-rationalization prompting** — name the exact excuses LLMs use, counter each one
3. **Evidence-based verification** — Command + Output required, no narrative claims
4. **Type-specific strategies** — different verification approach per change type
5. **False-positive filtering** — confidence scoring, hard exclusions, precedent-based rules
6. **Machine-parseable verdicts** — VERDICT: PASS/FAIL/PARTIAL for caller parsing
7. **Adversarial probes requirement** — must try to break something before issuing PASS
8. **Feedback refinement loop** — review can be iterated based on user feedback

---

## v4.5.0 — Allowed Paths: Cross-Directory Read+Write Access (2026-04-06)

Base: compact_v4 v4.4.0

### Allowed Paths
- **Why**: Agent was locked to workspace directory only. Could not access files in sibling folders (e.g., other folders inside `sagemaker-coding-agent/` when workspace is `compact_v4/`).
- **What**: New `allowed_paths` config option grants **full read+write** access to additional directories outside workspace.
- **Config**: Set via `agent_config.json`:
  ```json
  { "allowed_paths": ["/path/to/other/dir"] }
  ```
- **Security model**: Defense-in-depth across all 4 layers:
  1. `SecurityManager.validate_path()` — checks both workspace and allowed_paths
  2. Bash Layer 4 — allowed paths accepted in workspace boundary check
  3. Python sandbox — both `_SAFE_READ_PREFIXES` and `_SAFE_WRITE_PREFIXES` extended
  4. All tools (read, write, glob, grep, bash, document generators) work with allowed_paths
- **No regression**: Workspace-only behavior unchanged when `allowed_paths` is empty (default).
- **Validation**: Paths must be absolute, existing directories. Empty strings and relative paths rejected. Invalid paths logged and skipped at init.
- **Sensitive files**: `.env`, credentials, keys still blocked even within allowed_paths.
- **Backward compat**: `allowed_read_paths` key still accepted in agent_config.json.

### Auto-Detect Environment (SageMaker + Git)
- **Why**: User puts compact_v4 anywhere on SageMaker and tells the agent to work on other folders. Must just work without manual config.
- **What**: At startup, auto-detects environment and expands allowed_paths:
  1. **SageMaker**: If `/home/ec2-user/SageMaker/` or `/home/sagemaker-user/` exists, adds it. Agent can access any folder on the instance.
  2. **Git repo**: If workspace is a subdirectory of a git repo, adds repo root. Agent can access sibling folders.
- **Example (SageMaker)**: Agent in `ai_tools_package/compact_v4/` → auto-detects SageMaker → can access `user-default-efs/`, any project folder.
- **Example (Local)**: Workspace = `compact_v4/` → auto-detects `sagemaker-coding-agent/` → can access entire repo.
- **No-op when**: Not on SageMaker AND not in a git subdirectory.
- **Still configurable**: Manual `allowed_paths` in agent_config.json stacks with auto-detect.

### Fix: Relative Path Resolution Across Allowed Paths
- **Why**: When user gives a relative path like `wins_docs/pipeline.py`, agent only searched workspace. If file is in an allowed_path sibling folder, it returned "file not found".
- **What**: New `_resolve_path()` helper. If relative path not found in workspace, searches all allowed_paths. Used by `read_file`, `write_file`, `edit_file`.
- **Example**: Agent workspace = `compact_v4/`, user says "read `pdf_split_merge/pipeline.py`" → found in SageMaker home dir.

### Sonnet 4.6 Support
- Added `au.anthropic.claude-sonnet-4-6-v1:0` to pricing table ($3.30/$16.50 per 1M tokens, AU 10% premium)
- Added to model dropdown (UX selector) — ordered: Haiku 4.5, Sonnet 4.6, Sonnet 4.5, Opus 4.6, Opus 4.5, legacy

### Documentation
- Updated `USER_GUIDE.md` Workspace Boundary section with allowed_paths usage + auto-detect

---

## v4.4.0 — [CRITICAL] Rich Tool Descriptions + Git Worktree Isolation (2026-04-03)

Base: compact_v4 v4.3.3

### [CRITICAL] Rich Tool Descriptions (Runnable Parity)
- **Why**: Haiku still used `bash grep` instead of `grep` tool. Short descriptions didn't provide enough guidance for correct tool selection.
- **What**: Rewrote 7 key tool descriptions from 2-3 lines to 15-30 lines each:
  - `read_file`: Full usage guide, offset/limit guidance, image/notebook support, WHEN/WHEN NOT sections
  - `write_file`: Must-read-first enforcement, prefer edit_file guidance, mode documentation
  - `edit_file`: Exact match requirements, replace_all guidance, indentation preservation
  - `glob`: Pattern syntax guide, recursive matching, "never use bash find" enforcement
  - `grep`: "ALWAYS use for content search, NEVER bash grep" as opening line, regex examples, workflow guidance
  - `bash`: Dedicated tool preference list, git safety rules, command execution notes
  - `task`: Agent type descriptions with capabilities, WHEN/WHEN NOT, prompt-writing guide
- **Impact**: System prompt + tools now exceeds 4,096 tokens → activates Haiku's prompt cache → every turn ~90% cheaper on cached prefix
- **Source**: Modeled on Runnable's `src/tools/*/prompt.ts` style (BashTool ~370 lines, GrepTool ~18 lines, etc.)
- File grew from 8,750 → 9,015 lines (+265 lines)

### [CRITICAL] Git Worktree Isolation for Build Sub-agents
- **Why**: When build sub-agent makes mistakes, the main workspace is corrupted. Worktree creates an isolated copy — mistakes don't affect the original.
- **What**: Before spawning a `build` sub-agent:
  1. Checks if workspace is a git repo
  2. Creates a detached worktree: `git worktree add --detach <temp_path> HEAD`
  3. Temporarily sets `CONFIG.workspace` to worktree path
  4. Sub-agent works in isolation
  5. After completion: copies changed/new files back to main workspace
  6. Always cleans up: `git worktree remove --force`
- **Safety**:
  - Only for `build` type (explore/review/verify/plan are read-only)
  - Only in sequential path (parallel builds skip worktree to avoid CONFIG.workspace race)
  - Graceful fallback if git not available or worktree creation fails
- **Config**: `enable_worktree: true` (default). Disable via `agent_config.json`: `"enable_worktree": false`
- **Code**: `_run_task_tool()` in `sagemaker_agent.py` lines ~6315-6415
- File grew from 9,015 → 9,090 lines (+75 lines)

### Documentation
- Updated `[CRITICAL]_V4_TOKEN_EFFICIENCY.md` with V4.4.0 section
- Updated `[CRITICAL]_V4_SUBAGENT_AND_QUALITY.md` with worktree implementation
- Updated `PS_FLOWCHART_V4.html` comparison table
- Updated `CHANGELOG.md` (this file)
- Updated `SESSION_STATE.md`

---

## v4.3.3 — UI Redesign + Bug Fixes (2026-04-02)

Base: compact_v4 v4.3.2

### UI Layout Redesign
- Session bar moved to top (first action when opening notebook)
- Model + Sub-Agent Models + Plan Mode + Require Approval on one row
- Thinking + Budget + Temperature + Auto-Compact + Dark Mode on second row
- Status line and metrics moved to bottom
- Sections separated by horizontal rules
- Action buttons split: Send/Stop/Clear left, Compact/Clean right

### Checkbox Fix
- All 5 checkboxes now have `indent=False` + `layout=width='auto'`
- Fixes excessive gaps caused by ipywidgets default padding/width

### Markdown Rendering Improvements
- H1: 20px blue with bottom border
- H2: 16px blue
- H3: 14px normal weight
- Bold: white on dark / black on light (visible contrast)
- Inline code: red syntax color (#e06c75), 0.9em
- Code blocks: border, monospace font, 12px, 1.5 line-height
- Numbered lists (1. 2. 3.): now render as proper `<ol>`
- List items: 1.6 line-height, 2px margin
- Paragraphs: 1.5 line-height, 3px margin
- Blank lines: 8px spacer

### Cost Display Fix
- Status line `$0.0000` bug: `update_mode_display()` now called from `update_tokens_display()`
- Metrics bar shows cache savings: `Actual: $X | Without cache: $Y | Saved: $Z (N% cached)`
- When caching inactive: shows `Cache: inactive` in orange

### Diminishing Returns Fix
- Only counts text-only turns (turns with tool calls are skipped — agent is working)
- Tool call turns reset the counter
- Threshold lowered from 500 to 200 tokens

### Commands Removed
- Removed 5 redundant custom_commands from Cell 3 (review, explain, test, verify, standards)
- Skills cover the same categories with richer persistent checklists

### Notebook Updates
- Cell 0: added "How It Works" and "Recommended Workflow" with skill examples
- Cell 2: model dropdown uses dynamic default (no hardcoded name mismatch)
- Cell 3: simplified — security settings only, no commands
- Cell 4: full "Skills — Detailed Usage Guide" with examples, workflow, self-review

### Documentation
- USER_GUIDE.md: V3→V4 title, 6000→8699 lines, 21→25+ tools, 4→6 sub-agents
- chat.md: synced with notebook, removed stale command references
- V4_VS_RUNNABLE_ARCHITECTURE.md: dynamic prompts, sub-agents, verification, auth comparison
- EVALUATION_V4_vs_RUNNABLE_vs_CLAW.md: full competitive analysis with scoped assessment

## v4.3.2 — Complete Runnable Learning Integration (2026-04-02)

Base: compact_v4 v4.3.1

Source: Comprehensive analysis of 6 PDFs + how-claude-code-works repo + full prompt extraction (24 prompts).
See PS_[03]_PROMPT_ANALYSIS.md for complete prompt inventory.

### Cache-Breakage Detection (from Runnable postCompactCleanup pattern)
- Added `_cache_broken_by_compact` flag to Agent class
- After autocompact, flag is set True
- On next API call, detects if cache was invalidated and informs user
- Helps users understand caching behavior after context compression

### WHEN-not-WHAT Tool Descriptions (from Runnable 90-line Bash tool)
- read_file: "WHEN: reading source code... WHEN NOT: searching for patterns (use grep)"
- glob: "WHEN: locating files by name... WHEN NOT: searching file contents (use grep)"
- grep: "WHEN: finding patterns... WHEN NOT: finding files by name (use glob)"
- bash: "WHEN: git operations, pip install... WHEN NOT: reading/editing/writing/searching files"
- task: "WHEN: multi-file research, code review... WHEN NOT: simple reads, quick searches"

### Bash Git Safety in Tool Description
- Added git safety rules directly to bash tool description (not just system prompt)
- "NEVER force-push to main, create NEW commits, stage specific files, use HEREDOC"

### New "verify" Sub-agent Type (from Runnable verificationAgent.ts)
- Adversarial testing agent that tries to BREAK the implementation
- Runs build, tests, linters, edge cases, regressions
- Structured output: Check/Command/Output/Result format with VERDICT: PASS|FAIL|PARTIAL
- Available as `subagent_type="verify"` in task tool

### Enhanced Explore Agent (from Runnable exploreAgent.ts)
- Added "STRICTLY PROHIBITED from creating, modifying, or deleting files"
- Explicit read-only enforcement in prompt (not just tool restriction)
- Prevents wasted tool calls where LLM tries to write despite having no write tools

### Absolute Path Requirement for All Sub-agents
- build, explore, general, verify agents all now require absolute paths in output
- Matches Runnable's subagent notes pattern

### Documentation
- Created PS_[03]_PROMPT_ANALYSIS.md — tracks all 24 Runnable prompts and V4 status
- Updated PS_[04]_LEARNING_JOURNEY.md with PDF integration section
- Created Web_doc/PS_WEBDOC_LEARNINGS.md — cross-references 6 PDFs with verified source code
- Organized PS docs with numbered reading sequence: [01] through [04]
- Built PS_FLOWCHART_RUNNABLE.html (5 tabs, 10 flowcharts) and PS_FLOWCHART_V4.html (5 tabs, 8 flowcharts)

---

## v4.3.1 — Prompt Engineering Upgrade from Runnable (2026-04-01)

Base: compact_v4 v4.3.0

Source: Full prompt extraction and comparison between Runnable Claude Code and V4 — see PS_PROMPT_COMPARISON.md

### P-1 — SYSTEM_PROMPT Expansion (Runnable Parity)
- Added "Doing Tasks" section: don't gold-plate, simplest approach first, read before edit, no unnecessary abstractions
- Added "Executing Actions with Care" section: reversibility awareness, blast radius, confirm risky actions
- Added "Output Efficiency" section: lead with answer, skip filler, concise
- Added "Git Safety" section: never --no-verify, new commits not amend, stage specific files
- Added "Sub-agent Coordination" section: never delegate understanding, parallel spawn, Research→Synthesize→Implement→Verify
- Enhanced Memory section: inline WHAT_NOT_TO_SAVE exclusions
- Net effect: system prompt ~35 lines → ~72 lines. Estimated to push past Haiku 4.5's 4,096 token cache threshold

### P-2 — Tool Description Upgrade
- read_file: added offset/limit guidance, image/PDF support note, "MUST read before edit"
- write_file: added "prefer edit_file for modifications", "MUST read first if exists"
- edit_file: added "old_string must be unique — include more context", replace_all for renaming
- glob: added "use instead of bash find/ls", sorted by mtime
- grep: added "use instead of bash grep/rg", regex support
- bash: added "do NOT use for file read/edit/search — use dedicated tools"
- task: added "do NOT use for simple searches — use glob/grep directly", prompt-writing guidance

### P-3 — Sub-agent Prompt Upgrade
- build: added structured output format (what implemented, files changed, how to test, issues)
- explore: added structured output (Scope, Result, Key files), "report only what you observe"
- general: added structured output (Scope, Result, Key files, Issues), "don't leave half-done"
- All follow Runnable's worker output format pattern

### P-4 — Compact/Summary NO_TOOLS Preamble
- Summary system prompt now includes "You have ZERO tools available — do NOT attempt tool calls"
- Prevents hallucinated tool calls during context compaction (mirrors Runnable's NO_TOOLS_PREAMBLE)

### Bug Fixes (from v4.3.0 testing)
- TokenTracker.add() now saves _model_id when model_id arg provided → accurate cache savings pricing
- get_cache_savings_usd() uses self._model_id (not CONFIG.model_id) for per-session model accuracy

## v4.3.0 — Fresh Runnable Audit Gap Closure (2026-04-01)

Base: compact_v4 v4.2.1

Source: Fresh full audit of gg-claude-code-runnable/src/ (1,438 TS files) — see PS_DEEP_ANALYSIS_V3.md

### V3-A — Diminishing Returns Detection
- Tracks output token count for last 3 turns per run() call
- If 3+ consecutive turns produce <500 output tokens: emits advisory warning
- Mirrors runnable's `query/tokenBudget.ts` BudgetTracker diminishing-returns check
- Resets at start of each run() call; only fires once; top-level agent only (no sub-agent noise)

### V3-B — Memory 200-Line / 25KB Cap
- `_load_persistent_memory()` now caps at `_MEMORY_MAX_LINES=200` lines AND `_MEMORY_MAX_BYTES=25_000` bytes
- Line cap applied first (splitlines), then byte cap (f.read)
- Warning message updated to reflect actual limits hit
- Mirrors runnable's `memdir/memdir.ts` `MAX_ENTRYPOINT_LINES=200`, `MAX_ENTRYPOINT_BYTES=25_000`
- Previously only capped at 10K chars (~8KB, ~2500 tokens) — now aligned with Runnable

### V3-C — Cold-Cache Microcompact keepRecent
- `microcompact()` now accepts `keep_n_override: int = None` parameter
- Cold-cache path (V2-E, 30-min gap detection) now calls `microcompact(keep_n_override=KEEP_LAST_N_COLD_CACHE=1)`
- More aggressive cleanup when cache is cold: keep only last 1 result per tool type (vs normal default of 3)
- Mirrors runnable's `timeBasedMCConfig.ts` `keepRecent=5` pattern

### V3-D — Auto-Memory "Already Wrote" Check
- `_extract_and_append_memories()` now checks if the main agent wrote to `memory.md` this session
- If a `write_file`/`edit_file` tool call targeting `memory.md` is found in messages: extraction is skipped
- Mirrors runnable's `extractMemories.ts` `hasMemoryWritesSince()` — main agent's explicit writes always win
- Prevents duplicate/conflicting memory entries when agent manually curates memory

### V3-E — Per-Turn Cache Indicator (UI)
- After every LLM response (top-level agent only), emits a cache status line via output_fn
- `WRITE X tok`: first turn — system prompt written to Bedrock's server-side cache
- `HIT X tok (saved ~$Y)`: subsequent turns — tokens served from cache with per-turn cost savings shown
- `WRITE X tok | HIT Y tok`: both in same turn (mixed scenario)
- Uses `TOKENS.format_cache_line(usage)` — no output if no cache activity
- Sub-agents suppressed (subagent_depth > 0) to avoid noise

### V3-F — Cache Savings in /cost
- `TokenTracker.get_cache_savings_usd()`: calculates total session USD saved from prompt caching
- `get_cost()` now shows: `$X.XXXX (cache Y% | saved ~$Z)` when cache is active
- Formula: cache_read_tokens × input_price × 0.90 (90% discount = 90% savings vs full price)

### Testing Note
- Behavioral tests run on Bedrock Haiku 4.5 (`anthropic.claude-haiku-4-5-20251001-v1:0`)
- See TEST_LOG.md for pass/fail results per feature

---

## v4.2.1 — Deep Gap Closure + Bedrock Fix (2026-04-01)

Base: compact_v4 v4.2.0

### Critical Fix
- **Bedrock prompt caching**: Removed `anthropic_beta: ["prompt-caching-2024-07-31"]` header.
  Bedrock doesn't use Anthropic beta headers — caching is activated natively via `cache_control`
  blocks in content. This was causing "invalid beta flag" errors on Haiku 4.5 and Sonnet 4.5.
  All Claude models on Bedrock support prompt caching (Haiku 4.5: min 4096 tokens, Sonnet 4.5: min 1024).

### Bug Fix
- **_mc_saved // 4 double-conversion**: Microcompact status message was dividing an already-token
  value by 4. `_mc_saved` from `microcompact()` is already in tokens. Fixed to print directly.

### New Features

#### V2-H — FILE_UNCHANGED_STUB
- If a file hasn't changed since last read (mtime unchanged within 0.5s), returns a short stub
  instead of re-reading the full file content into context
- Saves significant context tokens when LLM re-reads files that weren't modified
- Mirrors runnable's `FILE_UNCHANGED_STUB` from `FileReadTool/prompt.ts`
- Follow-up audit fix: the stub path now runs before the generic "already in context"
  hint, so repeated unchanged reads take the low-token path in real use

#### V2-I — Parallel Read-Only Tool Execution
- Consecutive read-only tools (read_file, glob, grep, list_dir, semantic_search, bash RO)
  batched and run concurrently via ThreadPoolExecutor (max 6 workers)
- Non-RO tools break the batch → accumulated RO batch executed, then sequential continues
- Results merged back into the main dispatch loop via `_ro_parallel_results` dict
- ~40% latency reduction on multi-read turns (3-5 file reads + greps)
- Mirrors runnable's `partitionToolCalls()` from `services/tools/toolOrchestration.ts`

#### V2-J — PTL (Prompt-Too-Long) Recovery
- If `create_llm_summary()` fails with a prompt-too-long error, trims the oldest
  summary context and retries up to 3 times
- Catches both "prompt too long" and "too many tokens" error strings
- Mirrors runnable's `truncateHeadForPTLRetry()` from `services/compact/compact.ts`

### Verification
- Added targeted regression tests for:
  - unchanged file reads returning the stub instead of the generic in-context hint
  - prompt-too-long summary recovery retrying with smaller context
  - consecutive read-only tool calls running concurrently
- Added Playwright checks for both flowchart HTML pages:
  - all V4 tabs
  - all runnable tabs
  - every runnable detail modal in `NODE_DETAILS`
- Real Bedrock ping verified on 2026-04-01:
  - `anthropic.claude-3-haiku-20240307-v1:0` returned `OK`
  - runtime also confirmed the cache-control fallback path is required for this model/region

### Documentation
- PS_FLOWCHART_RUNNABLE.html completely rebuilt as multi-page reference document
  - 5 tabs: Architecture, V4 Has, V4 Missing, V4 Does Better, Deep Details
  - 9 Mermaid flowcharts with 30+ interactive click-to-detail nodes
  - Full comparison tables validated against actual runnable source (1,438 TS files)
  - PDF accuracy assessment (3 Chinese-language analyses cross-referenced)
- PS_FLOWCHART_V4.html expanded to cover:
  - harness responsibilities
  - sub-agent coordination
  - memory and context-management comparison
  - live AWS caching reality by model family
- Deep source analysis: 5 background agents analyzed runnable source covering query loop,
  tool dispatch, context management, permissions, memory, prompts, and model selection
- AWS runtime policy aligned for current testing:
  - default runtime model now AU Haiku 4.5
  - Sonnet 4.5 kept for prompt-cache verification and harder turns

---

## v4.2.0 — Runnable Gap Closure (2026-04-01)

Base: compact_v4 v4.1.0

### New Features (learned from deep dive: runnable vs V4 gap analysis)

#### V2-A — Tool Result Size Cap + Disk Offload
- Results > 50K chars are written to `.tool_cache/<id>_<tool>.txt` in workspace
- Preview (first 2000 + last 500 chars) + file pointer returned to LLM instead
- Runs BEFORE `SECURITY.truncate_output` so full content is always saved
- Fail-open: if disk write fails, original result returned unchanged
- `MAX_TOOL_RESULT_CHARS = 50_000` constant; mirrors runnable's 50K per-tool cap

#### V2-C — Enhanced Memory Extraction Prompt
- Added `WHAT NOT TO SAVE` exclusion section to `_MEMORY_EXTRACT_PROMPT`
- Excludes: code patterns, ephemeral file paths, git history, fix recipes, activity logs, project structural facts
- Exception carved out for canonical project locations (valid `[REFERENCE]` entries)
- Staleness note: function/path/flag memories get "(verify still exists)" annotation
- Mirrors runnable's `WHAT_NOT_TO_SAVE_SECTION` from `src/services/extractMemories/prompts.ts`

#### V2-D — Clear always_allow on Compact
- `always_allow` set cleared on every compact (manual, pre-send, auto, prune-only)
- Added `on_compact_fn: Callable` callback to Agent; propagated to sub-agents
- 3 clear locations: manual `on_compact()`, pre-send `do_pre_send_compact()`, `Agent.run()` auto-compact
- Prune-only path (Stage 1 early return) also clears to cover all code paths

#### V2-E — Time-Based Microcompact (Cold Cache Detection)
- `COLD_CACHE_THRESHOLD_SECONDS = 30 * 60` (30 min)
- If gap since last successful API call exceeds threshold, proactively runs microcompact before next LLM call
- `self._last_api_call_time` tracked on Agent, updated after every successful response
- Reset in `Agent.reset()` so loaded sessions don't inherit stale timestamps
- Only applies if savings >= `MICROCOMPACT_MIN_SAVINGS` (5K tokens)
- Mirrors runnable's `src/services/compact/microCompact.ts` time-based detection

#### V2-F — Conservative 4/3 Token Estimation Padding
- All char-based token estimates updated: `len // 4` → `len // 3` (= chars/4 × 4/3)
- Updated: `ContextManager.estimate_tokens`, `Compactor.estimate_tokens`, `TokenTracker.get_fixed_overhead`, embedding cost estimate
- Only affects non-tiktoken fallback path; tiktoken path remains accurate
- Mirrors runnable's conservative multiplier from `src/query/tokenBudget.ts`
- Effect: compact triggers slightly earlier, preventing context overflow at boundary

#### V2-G — Per-Batch Aggregate Tool Result Cap
- If total chars across all tool results in a batch exceeds 200K, largest results trimmed first
- Protected tools never truncated: `todo_write`, `todo_read`, `semantic_search`, `edit_file`, `write_file`
- Preview: first 1000 chars + pointer to use `read_file` for full content
- Warning emitted if batch still over cap after trimming all trimmable results
- Mirrors runnable's `src/constants/toolLimits.ts` 200K batch cap

### Review Process
- All features reviewed with gpt-5.3-codex (Codex CLI, read-only sandbox)
- Issues found and fixed per feature:
  - V2-A: 1 issue (offload ran AFTER truncation → dead code; fixed ordering)
  - V2-C: 2 issues (file path exclusion contradicted [REFERENCE] type; CLAUDE.md exclusion unactionable)
  - V2-D: 3 issues (sub-agents missing on_compact_fn; lambda get() no-op; prune-only path skipped clear)
  - V2-E: 1 issue (reset() didn't clear _last_api_call_time)
  - V2-F: 1 issue (missed embedding estimate at line ~4839)
  - V2-G: pending Codex final pass

### No Breaking Changes
- All v4.1 API signatures unchanged
- New Agent kwarg `on_compact_fn` is optional (default None)

---

## v4.1.0 — Claude Code Feature Parity (2026-04-01)

Base: compact_v4 v4.0.0

### New Features (learned from Claude Code source analysis)

#### #14 — Prompt Cache Boundary
- `SYSTEM_PROMPT` split at `# === DYNAMIC ===` marker into static (cacheable) + dynamic sections
- Static section cached via Bedrock `anthropic_beta: prompt-caching-2024-07-31` — ~90% token savings on repeated turns
- Graceful fallback: sets `prompt_cache_supported = False` on validation error; retries without cache blocks
- Fallback condition narrowed to explicit cache-control rejection signals only (not broad `ValidationException`)
- Config: `enable_prompt_cache: bool = True` (disable via agent_config.json)

#### #12 — Catastrophic Path Enforcement (Hard Block)
- New `CATASTROPHIC_PATTERNS` on `SecurityValidator` class — 13 patterns covering `rm -rf /`, `dd` disk wipe, `mkfs`, `fdisk`, `fork bomb`, `chmod 777 /`, direct device writes, shutdown/init 0
- Checked as **LAYER -1** before allowlist — cannot be bypassed by config, user approval, or allowlist modification
- Patterns precompiled at class load time (fail-closed: bad regex fails at import, not silently skipped)
- Covers all `rm` flag variants: `-rf`, `-fr`, `-r -f`, `--recursive --force`

#### #10 — Partial View Guard
- Tracks `(start_line, end_line)` in `_FILE_PARTIAL_READS` dict whenever `read_file` uses `offset > 0` or reads fewer lines than total
- If `edit_file` is called on a partially-read file, prepends advisory warning: "You only read lines X-Y of this file"
- Warning is non-blocking — edit still proceeds
- Full read clears the partial flag; write_file also clears it
- Cleared at all 4 session reset locations (Agent.reset, on_clear, on_load, on_new)

#### #11 — Command Auto-Classifier
- Read-only bash commands skip the approval dialog automatically
- `_classify_bash_ro()` checks base command against `_RO_BASE_COMMANDS` frozenset; handles `sed -i/-ni/--in-place`, git read subcommands, `pip list/show/freeze`
- Pipeline detection: any `;`, `&&`, `||`, `>`, `>>` forces `return False`
- `diff` removed from `_RO_BASE_COMMANDS` (`diff --output=file` can write)
- `git stash apply/pop/drop` excluded — "stash" removed from `_RO_GIT_SUBCOMMANDS`
- `sed -ni` now caught (short option group containing 'i' = in-place)
- Wired at LAYER 4 in Agent run loop; `_is_ro_bash` skips `on_approval` call

#### #7 — 4-Type Memory Structure
- `_parse_memory_sections()` splits `memory.md` into typed sections: `## USER`, `## FEEDBACK`, `## PROJECT`, `## REFERENCE`
- Legacy flat-format files loaded under `## Notes` with upgrade prompt
- Each section presented with descriptive label in system prompt
- SYSTEM_PROMPT updated to document 4-type format for agent's own writes
- `_load_persistent_memory()` exception now logged via `logging.warning()` (was silently swallowed)

#### #8 — Memory Auto-Extraction (opt-in)
- At session end (Clear or New Session button), if `>= 4 user turns` and `enable_memory_extraction=True`, runs one LLM call to extract learnings
- Extracts per-type facts in `[TYPE] key | one-sentence fact` format
- Appends to `memory.md` under timestamped comment block as a single atomic write
- Off by default (`enable_memory_extraction: bool = False`) — opt in via agent_config.json
- Existing memory injected into extraction prompt to avoid re-extracting known facts
- `SECURITY.validate_path()` guard added before write

### Review Process
- All 6 features: self-review + Codex review each
- Issues found and fixed per feature:
  - #14: 5 issues (missing `anthropic_beta` body field, no session-level `prompt_cache_supported` flag, broad exception filter, redundant `import logging`, list branch bypasses config gate)
  - #12: 5 issues (rm flag variants, dd order-independence, missing shutdown/init 0, IGNORECASE removed, precompile patterns for fail-closed)
  - #10: 3 issues (empty selection inverted range, `write_file` not clearing partial flag, partial flag not removed in `on_clear`/`on_new` → all fixed)
  - #11: 3 issues (`git stash apply` bypass, `sed -ni` bypass, `diff --output` write capability)
  - #7: 1 issue (silent exception swallow → now logged)
  - #8: 4 issues (`agent.llm` → `agent.client`, `max_tokens=512` too small → 1024, no path security guard, non-atomic write → single `f.write()` call, min_turns 10 → 4)

### No Breaking Changes

---

## v4.0.0 — V4 Feature Release (2026-04-01)

Base: compact_v3 v3.2.3

### New Features

#### CLAUDE.md Auto-Load
- On every send, walks workspace → parent dirs → home looking for `CLAUDE.md` files
- Injects content into system prompt before active skills (parent files first, workspace file wins)
- Deduplicates via realpath to handle symlinks
- Config flag: `"load_claude_md": true` (default true, disable in agent_config.json)
- Caps per-file at 8000 chars

#### Pre-Edit Staleness Check
- Tracks file mtime on every `read_file` and `write_file` under `_FILES_READ_LOCK`
- Before `edit_file` executes: aborts with warning if file was externally modified since last read (0.5s tolerance)
- Prevents silent overwrite of changes made by other processes or users
- Clears mtime tracking on all session resets (Agent.reset, on_clear, on_load, on_new)

#### Post-Edit Git Diff Summary
- After every successful `edit_file`, runs `git diff HEAD` and appends to tool result
- Labelled as "File diff vs HEAD (all uncommitted changes)" — not misleadingly called "current edit"
- 5s subprocess timeout; gracefully skipped if git is not installed or not a git repo
- Diff capped at 3000 chars

#### Microcompact (70% Context Threshold)
- At 70% context (before the 80% full compact), replaces OLD tool result contents with a marker
- Compactable tools: `read_file`, `bash`, `grep`, `glob`, `list_dir`, `web_fetch`, `python_exec`, `create_chart`
- Protected tools never cleared: `todo_write`, `todo_read`, `semantic_search`, `edit_file`, `write_file`, `create_word`, `create_excel`, `ask_user`
- Keeps last 3 results per tool type (newest preserved)
- Only applies if savings >= 5000 tokens
- Clears FILE_CACHE in-context markers if any `read_file` results were discarded
- Correctly handles multiple tool results in a single message (inner blocks reversed for newest-first)

#### Post-Compact File Restoration
- After full compact (summarize + truncate), re-injects content of last 3 recently-read files
- Resolves relative paths via CONFIG.workspace
- Runs SECURITY.validate_path() before reopening any file
- Budget: 12000 chars per file, 32000 chars total
- Respects Bedrock role alternation (appends/merges correctly)

#### Compact Circuit Breaker
- Tracks consecutive `create_llm_summary()` failures (None return = failure)
- After 3 failures: sets `_auto_compact_paused = True` for kernel session
- Auto-compact paused in all automatic paths (Agent.run, pre-send, post-send)
- Manual Compact button NOT gated — user override always works
- Pre-send compact path also increments/resets the shared failure counter

### Review Log
- Self-review: 6 issues found and fixed
- Codex review round 1: 6 further issues found and fixed
- Codex review round 2: 2 more issues fixed (inner reversed in get_recently_read_files, pre-send failure counter)
- Total: 14 issues caught before release

### No Breaking Changes
- All v3 tool API signatures unchanged
- All v3 config fields still work
- New `load_claude_md: bool = True` config field added
