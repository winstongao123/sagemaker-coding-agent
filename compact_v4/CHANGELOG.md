# Compact V4 Changelog

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
- `_classify_bash_ro()` checks base command against `_RO_BASE_COMMANDS` frozenset; handles `sed -i`, `git branch/tag/remote` with flag inspection, `pip list/show/freeze`
- Tee-in-pipeline detection: `| tee` forces `return False` (write op regardless of left side)
- Uses `shlex.split()` for correct tokenization of quoted args (was `str.split()`)
- `git branch/tag/remote` now inspected for write flags (`-d`, `-D`, `--delete`, etc.) before classifying as read-only
- Wired at LAYER 4 in Agent run loop; `_is_ro_bash` skips `on_approval` call

#### #7 — 4-Type Memory Structure
- `_parse_memory_sections()` splits `memory.md` into typed sections: `## USER`, `## FEEDBACK`, `## PROJECT`, `## REFERENCE`
- Legacy flat-format files loaded under `## Notes` with upgrade prompt
- Each section presented with descriptive label in system prompt
- SYSTEM_PROMPT updated to document 4-type format for agent's own writes

#### #8 — Memory Auto-Extraction (opt-in)
- At session end (Clear or New Session button), if `>= 10 turns` and `enable_memory_extraction=True`, runs one LLM call to extract learnings
- Extracts per-type facts in `[TYPE] key | one-sentence fact` format
- Appends to `memory.md` under timestamped comment block
- Off by default (`enable_memory_extraction: bool = False`) — opt in via agent_config.json
- Existing memory injected into extraction prompt to avoid re-extracting known facts

### Review Process
- All 6 features: self-review + Codex review each
- Issues found and fixed per feature:
  - #14: 5 issues (missing anthropic_beta header, no session-level disable flag, broad exception filter, redundant import, list branch bypasses config gate)
  - #12: 5 issues (rm flag variants, dd order-independence, missing shutdown/init 0, IGNORECASE inappropriate, fail-open on regex error)
  - #10: 0 issues (Codex: clean)
  - #11: 3 issues (tee bypass, git flag inspection, shlex.split)
  - #7: already implemented
  - #8: 1 issue (agent.llm → agent.client)

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
