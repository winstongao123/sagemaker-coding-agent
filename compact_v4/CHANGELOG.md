# Compact V4 Changelog

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
