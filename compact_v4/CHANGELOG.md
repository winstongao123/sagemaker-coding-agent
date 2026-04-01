# Compact V4 Changelog

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

#### V2-I — Parallel Read-Only Tool Execution
- Consecutive read-only tools (read_file, glob, grep, list_dir, semantic_search, bash RO)
  batched and run concurrently via ThreadPoolExecutor (max 6 workers)
- Non-RO tools break the batch → accumulated RO batch executed, then sequential continues
- Results merged back into the main dispatch loop via `_ro_parallel_results` dict
- ~40% latency reduction on multi-read turns (3-5 file reads + greps)
- Mirrors runnable's `partitionToolCalls()` from `services/tools/toolOrchestration.ts`

#### V2-J — PTL (Prompt-Too-Long) Recovery
- If `create_llm_summary()` fails with a prompt-too-long error, halves input and retries once
- Catches both "prompt too long" and "too many tokens" error strings
- Mirrors runnable's `truncateHeadForPTLRetry()` from `services/compact/compact.ts`

### Documentation
- PS_FLOWCHART_RUNNABLE.html completely rebuilt as multi-page reference document
  - 5 tabs: Architecture, V4 Has, V4 Missing, V4 Does Better, Deep Details
  - 9 Mermaid flowcharts with 30+ interactive click-to-detail nodes
  - Full comparison tables validated against actual runnable source (1,438 TS files)
  - PDF accuracy assessment (3 Chinese-language analyses cross-referenced)
- Deep source analysis: 5 background agents analyzed runnable source covering query loop,
  tool dispatch, context management, permissions, memory, prompts, and model selection

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
