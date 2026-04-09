# Compact V4 Changelog

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

### Verification
- Python syntax check: PASS (ast.parse, 9299 lines)
- Git diff: Only prompt_suffix strings changed in sagemaker_agent.py (no logic/structure changes)
- No code regression: All existing functionality preserved

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
