# compact_v4 Implementation Plan

> Status: REVIEWED x2 — self-review + Codex review complete. Ready to implement.
> Base: compact_v3 copied to compact_v4/MAIN/
> Target file: compact_v4/MAIN/agent/sagemaker_agent.py

---

## Review Log

### Self-Review Round 1 (2026-04-01) — 6 issues fixed

| # | Issue | Fix |
|---|---|---|
| SR-1 | Integration used `system_prompt` var but actual var is `_base_prompt` | Changed to `_base_prompt` |
| SR-2 | `_FILE_READ_TIMES` updates not under `_FILES_READ_LOCK` — race condition | All reads/writes under lock |
| SR-3 | Microcompact first pass built `tool_counts` dict never used | Removed; single pass sufficient |
| SR-4 | `_find_tool_name()` called but never defined | Added full definition |
| SR-5 | Post-compact restoration could create user→user sequence | Role alternation guard added |
| SR-6 | Wrapped `COMPACTOR.compact()` (never throws). `CONFIG.auto_compact` doesn't exist | Wrap `create_llm_summary()`; use module-level `_auto_compact_paused` flag |

### Codex Review Round 1 (2026-04-01) — 6 further issues fixed

| # | Feature | Issue | Fix |
|---|---|---|---|
| CR-1 | F1 | `load_claude_md` config flag not wired into `_SCALAR_FIELDS` — cannot be set from `agent_config.json` | Add to `_SCALAR_FIELDS` |
| CR-2 | F1 | Injection in `Agent.run()` lands AFTER active skills (wrong precedence) | Inject in `on_send()` UI flow at line ~6941, before `# Active Skills` block |
| CR-3 | F2 | `_FILES_READ` uses `abspath`, plan used `realpath` for `_FILE_READ_TIMES` — key mismatch | Standardise on `abspath` everywhere |
| CR-4 | F2 | `_FILE_READ_TIMES` never cleared on session reset/clear/load/new — stale mtimes persist across sessions | Clear `_FILE_READ_TIMES` wherever `_FILES_READ` is cleared (5 locations) |
| CR-5 | F2 | After `edit_file`/`write_file` the mtime is stale → next edit would falsely trigger staleness | Update `_FILE_READ_TIMES[abs_path]` after every successful write |
| CR-6 | F3 | `git diff HEAD` shows all uncommitted changes, not just the current edit | Label clearly as "file diff vs HEAD"; existing per-edit unified diff already captured — expose it |
| CR-7 | F4 | Inner `content` list of a user message iterated forward while outer messages iterated reverse — "keep last N" applies in wrong order | Reverse inner block list too (reverse, process, un-reverse) |
| CR-8 | F4 | After clearing `read_file` results, FILE_CACHE in-context markers not cleared — agent thinks files are still in context | Call `FILE_CACHE.discard_from_context(path)` for each cleared result |
| CR-9 | F5 | `os.path.isfile(path)` skips valid relative paths (resolved via `CONFIG.workspace` in `tool_read_file`) | Resolve path through `CONFIG.workspace` before `isfile` check |
| CR-10 | F5 | Restoration opens files without `SECURITY.validate_path()` — could restore out-of-workspace file from failed tool call | Run `SECURITY.validate_path()` before every `open()` |
| CR-11 | F5 | Budget trim clips to `POST_COMPACT_MAX_CHARS_PER_FILE` regardless of remaining global budget | Trim to `min(POST_COMPACT_MAX_CHARS_PER_FILE, POST_COMPACT_TOTAL_BUDGET - total_chars)` |
| CR-12 | F6 | `create_llm_summary()` swallows exceptions internally, returns `None` — outer `except` never fires | Treat `summary is None` as failure; increment counter on `None` return |
| CR-13 | F6 | Circuit breaker only in `Agent.run()` — UI auto-compact paths (line ~6597, ~6966) and manual compact (~7263) not covered | Check `_auto_compact_paused` in all three compact paths |

---

## Scope

6 features, all additive (no breaking changes to v3 behaviour):

| # | Feature | User Benefit | Risk |
|---|---|---|---|
| 1 | CLAUDE.md auto-load | Project instructions auto-injected | Low |
| 2 | Pre-edit git diff + staleness check | Regression prevention | Low |
| 3 | Post-edit diff summary | User sees what changed | Low |
| 4 | Microcompact (old tool results) | Save tokens mid-stream | Medium |
| 5 | Post-compact file restoration | Don't lose file context after compact | Low |
| 6 | Compact circuit breaker | Stability, stop runaway retries | Low |

NOT in v4 (defer to v4.1):
- 4-type memory taxonomy
- Tree-sitter bash parsing
- Worktree isolation
- Prompt cache boundary

---

## Feature 1: CLAUDE.md Auto-Load

### What
Walk from workspace root up to home dir, collect `CLAUDE.md` files, inject into system prompt.

### Where
- New function: `load_project_instructions(workspace: str) -> str` — place after `_load_persistent_memory()`
- Config: `load_claude_md: bool = True` in `Config` dataclass + **`_SCALAR_FIELDS`** (CR-1)
- Call site: `on_send()` in UI flow at line ~6941, BEFORE the `# Active Skills` block (CR-2)
  - Sub-agent case (Agent.run directly): inject in `Agent.run()` only at `subagent_depth == 0` AND only if UI path is not active

### Design
```python
def load_project_instructions(workspace: str) -> str:
    """Walk workspace → parent dirs → home, collect CLAUDE.md files."""
    if not CONFIG.load_claude_md:
        return ""
    instructions = []
    path = os.path.abspath(workspace)
    home = os.path.expanduser("~")
    seen = set()
    while True:
        claude_md = os.path.join(path, "CLAUDE.md")
        real = os.path.realpath(claude_md)
        if real not in seen and os.path.isfile(claude_md):
            seen.add(real)
            try:
                content = open(claude_md, encoding="utf-8", errors="ignore").read()
            except Exception:
                content = ""
            if content.strip():
                instructions.append(f"# Project Instructions ({claude_md})\n{content[:8000]}")
        if path == home or path == os.path.dirname(path):
            break
        path = os.path.dirname(path)
    return "\n\n---\n\n".join(reversed(instructions))  # parent first, project last wins
```

### Config additions
```python
# In Config dataclass:
load_claude_md: bool = True

# In _SCALAR_FIELDS dict:
"load_claude_md": bool,
```

### Integration in on_send() (line ~6941, in UI flow)
```python
# EXISTING (simplified):
base_prompt = system_prompt if system_prompt is not None else SYSTEM_PROMPT
# ADD before active skills block:
project_instructions = load_project_instructions(CONFIG.workspace)
if project_instructions:
    base_prompt = base_prompt + "\n\n" + project_instructions
# EXISTING continues:
if active_skills:
    system_prompt = base_prompt + "\n\n# Active Skills\n" + ...
else:
    system_prompt = base_prompt
```

### Edge Cases
- File missing: skip silently
- Encoding error: `errors="ignore"` + outer try/except
- Too long: cap at 8000 chars per file
- Sub-agents: skip (depth > 0)
- Circular symlinks: track seen real paths (dedup by realpath)

---

## Feature 2: Pre-Edit Git Diff + Staleness Check

### What
Track file mtime on every read. Before `edit_file` executes: abort if file changed since last read.
Show current `git diff HEAD` after every successful edit.

### Where
- `_FILE_READ_TIMES: Dict[str, float]` — add alongside `_FILES_READ` at line ~2534
- Track mtime in `tool_read_file()` under `_FILES_READ_LOCK` (line ~2601)
- Update mtime after `edit_file` and `write_file` successful writes (CR-5)
- Clear `_FILE_READ_TIMES` everywhere `_FILES_READ` is cleared (5 locations) (CR-4)

### New globals and helpers
```python
# Alongside _FILES_READ at line ~2534:
_FILE_READ_TIMES: Dict[str, float] = {}  # abs_path -> mtime when last read
# Always updated under _FILES_READ_LOCK


def _check_file_staleness(path: str) -> Optional[str]:
    """Returns warning if file changed since last read, else None."""
    abs_path = os.path.abspath(path)  # Use abspath, consistent with _FILES_READ (CR-3)
    with _FILES_READ_LOCK:
        last_mtime = _FILE_READ_TIMES.get(abs_path)
    if last_mtime is None:
        return None
    try:
        current_mtime = os.path.getmtime(path)
    except OSError:
        return None
    if current_mtime > last_mtime + 0.5:
        return (f"WARNING: {path} was modified since last read "
                f"(read_mtime={last_mtime:.0f}, current={current_mtime:.0f}). "
                f"Re-read the file before editing to avoid overwriting changes.")
    return None


def _get_git_diff(path: str) -> str:
    """Get git diff HEAD for a file. Returns '' if not a git repo or git not found."""
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD", "--", path],
            capture_output=True, text=True, timeout=5,
            cwd=os.path.dirname(os.path.abspath(path)) or CONFIG.workspace
        )
        return result.stdout.strip()
    except Exception:
        return ""
```

### Integration in tool_read_file (line ~2601)
```python
# EXISTING:
with _FILES_READ_LOCK:
    _FILES_READ.add(abs_path)
# ADD (inside same lock block):
    try:
        _FILE_READ_TIMES[abs_path] = os.path.getmtime(path)
    except OSError:
        pass
```

### Integration in tool_edit_file (before existing must-read check, line ~2884)
```python
abs_path = os.path.abspath(path)

# NEW: staleness check (abort if modified externally since last read)
stale_warning = _check_file_staleness(path)
if stale_warning:
    return stale_warning

# EXISTING: must-read check
with _FILES_READ_LOCK:
    if abs_path not in _FILES_READ:
        return "Error: Must read file before editing. Use read_file first."

# ... existing edit logic (SNAPSHOTS, read, replace, write) ...

# After successful write — update mtime (CR-5):
with _FILES_READ_LOCK:
    try:
        _FILE_READ_TIMES[abs_path] = os.path.getmtime(path)
    except OSError:
        pass

# NEW: post-edit git diff (CR-6: labelled clearly as "file diff vs HEAD")
post_diff = _get_git_diff(path)
# EXISTING result string:
result = f"Edited {os.path.basename(path)} (line {lines_before})\n"
result += f"  -{old_lines} lines / +{new_lines} lines"
if count > 1 and replace_all:
    result += f" ({count} replacements)"
result += f"\n  Old: {repr(old_preview)}\n  New: {repr(new_preview)}"
# NEW:
if post_diff:
    result += f"\n\nFile diff vs HEAD (all uncommitted changes):\n```diff\n{post_diff[:3000]}\n```"
# EXISTING lint:
lint_err = _auto_lint_python(abs_path)
if lint_err:
    result += f"\n{lint_err}"
return result
```

### Integration in tool_write_file (after successful write, line ~2830)
```python
# EXISTING:
with _FILES_READ_LOCK:
    _FILES_READ.add(abs_path)
# ADD (same lock block):
    try:
        _FILE_READ_TIMES[abs_path] = os.path.getmtime(path)
    except OSError:
        pass
```

### Clear _FILE_READ_TIMES at 5 session-reset locations (CR-4)
Add `_FILE_READ_TIMES.clear()` inside `_FILES_READ_LOCK` wherever `_FILES_READ.clear()` is called:
1. `Agent.reset()` line ~5687
2. `on_clear()` line ~7055
3. `on_load()` line ~7106
4. `on_new()` line ~7232
5. Auto-compact prune path line ~6606 (only clear context markers, not mtime — leave mtime here since files don't change during prune)

Actually for location 5 (prune path): do NOT clear `_FILE_READ_TIMES` — prune doesn't reset the session. Only clear at true session boundaries (locations 1-4).

### Edge Cases
- Not a git repo: returns "" — skip diff section gracefully
- `git` not on PATH: `FileNotFoundError` caught by `except Exception`
- Large diff: cap at 3000 chars
- Staleness: return early, force re-read
- Post-edit mtime update prevents false stale warning on next edit of same file

---

## Feature 3: Post-Edit Diff Summary (part of Feature 2)
Covered above. The `git diff HEAD` shows all uncommitted changes to the file (CR-6: labelled as "File diff vs HEAD (all uncommitted changes)" — not misleadingly called "current edit diff"). The existing `_generate_unified_diff()` result is already shown in the compact result line.

---

## Feature 4: Microcompact (Replace Old Tool Results Mid-Stream)

### What
When context >= 70% (before 80% full compact), replace old tool result contents with a marker.

### Compactable tools
`read_file`, `bash`, `grep`, `glob`, `list_dir`, `web_fetch`, `python_exec`, `create_chart`

### Non-compactable tools (never clear)
`todo_write`, `todo_read`, `semantic_search`, `edit_file`, `write_file`, `create_word`, `create_excel`, `ask_user`

### Design
```python
MICROCOMPACT_TRIGGER_PERCENT = 0.70
MICROCOMPACT_TOOLS = {
    "read_file", "bash", "grep", "glob", "list_dir",
    "web_fetch", "python_exec", "create_chart"
}
MICROCOMPACT_MARKER = "[Tool output cleared to save context — re-run if needed]"
MICROCOMPACT_MIN_SAVINGS = 5000
KEEP_LAST_N_PER_TOOL = 3


def _find_tool_name(messages: List[Dict], tool_use_id: str) -> str:
    """Walk messages to find the tool name for a given tool_use_id."""
    for msg in messages:
        if msg.get("role") == "assistant":
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if (isinstance(block, dict) and
                            block.get("type") == "tool_use" and
                            block.get("id") == tool_use_id):
                        return block.get("name", "")
    return ""


def microcompact(messages: List[Dict]) -> Tuple[List[Dict], int]:
    """
    Replace old tool result contents with marker. Newest-first pass.
    Keeps last KEEP_LAST_N_PER_TOOL results per tool type.
    Returns (new_messages, tokens_saved).
    """
    tokens_before = CONTEXT.estimate_tokens(messages)
    keep_counts: Dict[str, int] = {}
    cleared_read_file_paths: Set[str] = set()  # Track for FILE_CACHE cleanup (CR-8)

    result_msgs = []
    for msg in reversed(messages):  # newest first
        if msg.get("role") == "user":
            content = msg.get("content", [])
            if isinstance(content, list):
                # CR-7: also reverse inner blocks so "keep last N" is newest-first
                new_content_reversed = []
                for block in reversed(content):
                    if (isinstance(block, dict) and
                            block.get("type") == "tool_result"):
                        tool_id = block.get("tool_use_id", "")
                        tool_name = _find_tool_name(messages, tool_id)
                        if tool_name in MICROCOMPACT_TOOLS:
                            keep_counts[tool_name] = keep_counts.get(tool_name, 0) + 1
                            already_cleared = block.get("content") == MICROCOMPACT_MARKER
                            if keep_counts[tool_name] > KEEP_LAST_N_PER_TOOL and not already_cleared:
                                block = {**block, "content": MICROCOMPACT_MARKER}
                                if tool_name == "read_file":
                                    # Will discard from FILE_CACHE context after loop (CR-8)
                                    # We can't easily get path here; discard handled globally below
                                    cleared_read_file_paths.add(tool_id)
                    new_content_reversed.append(block)
                # Restore original order for this message
                msg = {**msg, "content": list(reversed(new_content_reversed))}
        result_msgs.append(msg)

    result_msgs = list(reversed(result_msgs))

    # CR-8: Discard FILE_CACHE in-context markers for cleared read_file results
    # We cleared read_file outputs — agent can no longer see file content in context.
    # Strategy: clear ALL in-context markers so agent re-reads files fresh.
    # (More targeted: walk result_msgs to find paths, but full clear is safe here.)
    if cleared_read_file_paths:
        FILE_CACHE.clear_context()

    tokens_saved = tokens_before - CONTEXT.estimate_tokens(result_msgs)
    return result_msgs, tokens_saved
```

### Integration in Agent.run() (BEFORE existing 80% compact block, line ~5246)
```python
# NEW: microcompact at 70%
_mc_usage = CONTEXT.get_usage(self.messages)
if (not _auto_compact_paused and
        _mc_usage["percent"] >= MICROCOMPACT_TRIGGER_PERCENT and
        _mc_usage["percent"] < COMPACTOR.SUMMARY_TRIGGER_PERCENT):
    _mc_msgs, _mc_saved = microcompact(self.messages)
    if _mc_saved >= MICROCOMPACT_MIN_SAVINGS:
        self.messages = _mc_msgs
        output_fn(f"[Microcompact: freed ~{_mc_saved // 4} tokens]")

# EXISTING: full compact at 80%
if COMPACTOR.should_compact(...):
    ...
```

### Edge Cases
- Tool ID not found: `_find_tool_name()` returns "" — not in MICROCOMPACT_TOOLS, block untouched
- Already cleared: skip if `content == MICROCOMPACT_MARKER`
- Savings threshold: only apply if >= MICROCOMPACT_MIN_SAVINGS
- FILE_CACHE: cleared if any read_file results were discarded

---

## Feature 5: Post-Compact File Restoration

### What
After full compact, re-inject recently-read file contents so agent doesn't lose file context.

### Design
```python
POST_COMPACT_MAX_FILES = 3
POST_COMPACT_MAX_CHARS_PER_FILE = 12000   # ~3K tokens
POST_COMPACT_TOTAL_BUDGET = 32000          # ~8K tokens total


def get_recently_read_files(messages: List[Dict], n: int = POST_COMPACT_MAX_FILES) -> List[str]:
    """Return last N distinct file paths from read_file tool calls (resolved absolute paths)."""
    seen: List[str] = []
    seen_set: Set[str] = set()
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if (isinstance(block, dict) and
                            block.get("type") == "tool_use" and
                            block.get("name") == "read_file"):
                        raw_path = block.get("input", {}).get("file_path", "")
                        if not raw_path:
                            continue
                        # CR-9: resolve relative paths via CONFIG.workspace
                        if not os.path.isabs(raw_path):
                            path = os.path.join(CONFIG.workspace, raw_path)
                        else:
                            path = raw_path
                        path = os.path.abspath(path)
                        if path not in seen_set and os.path.isfile(path):
                            seen.append(path)
                            seen_set.add(path)
                            if len(seen) >= n:
                                return seen
    return seen


def build_file_restoration_message(files: List[str]) -> Optional[str]:
    """Build restoration text for recently-read files after compact."""
    sections = []
    total_chars = 0
    for path in files:
        remaining_budget = POST_COMPACT_TOTAL_BUDGET - total_chars
        if remaining_budget <= 0:
            break
        # CR-10: security check before opening
        ok, _ = SECURITY.validate_path(path)
        if not ok:
            continue
        try:
            content = open(path, encoding="utf-8", errors="ignore").read()
            # CR-11: trim to min(per-file cap, remaining budget)
            max_chars = min(POST_COMPACT_MAX_CHARS_PER_FILE, remaining_budget)
            if len(content) > max_chars:
                content = content[:max_chars]
            sections.append(f"# Re-injected file: {path}\n```\n{content}\n```")
            total_chars += len(content)
        except Exception:
            pass
    if not sections:
        return None
    return ("After compaction, here are recently-read files for context:\n\n"
            + "\n\n".join(sections))
```

### Integration in Compactor.compact() (line ~373)
```python
@classmethod
def compact(cls, messages: List[Dict], summary: str) -> List[Dict]:
    # NEW: capture recently-read files BEFORE discarding old messages
    recently_read = get_recently_read_files(messages)

    summary_msg = {
        "role": "assistant",
        "content": f"[CONVERSATION SUMMARY]\n{summary}\n[END SUMMARY - Continuing from here]"
    }
    n = cls.KEEP_LAST_MESSAGES
    recent_messages = copy.deepcopy(messages[-n:] if len(messages) > n else messages)
    while recent_messages and recent_messages[0].get("role") != "user":
        recent_messages.pop(0)
    if not recent_messages:
        recent_messages = [{"role": "user", "content": "[Conversation compacted. Continue from summary.]"}]

    compacted = [summary_msg] + recent_messages

    # NEW: append file restoration, guarding role alternation (SR-5)
    restoration_text = build_file_restoration_message(recently_read)
    if restoration_text:
        last_role = compacted[-1].get("role") if compacted else None
        if last_role == "assistant":
            compacted.append({"role": "user", "content": restoration_text})
        elif last_role == "user":
            last_content = compacted[-1].get("content", "")
            if isinstance(last_content, str):
                compacted[-1]["content"] = last_content + "\n\n" + restoration_text
            elif isinstance(last_content, list):
                compacted[-1]["content"].append({"type": "text", "text": restoration_text})

    return compacted
```

### Edge Cases
- File deleted: `os.path.isfile()` check skips it
- Relative paths: resolved via `CONFIG.workspace` (CR-9)
- Security: `SECURITY.validate_path()` before every open (CR-10)
- Budget: trimmed to `min(per-file cap, remaining budget)` (CR-11)
- Role alternation: guarded (SR-5)

---

## Feature 6: Compact Circuit Breaker

### What
After 3 consecutive `create_llm_summary()` failures (including `None` returns), pause auto-compact.

### Design
```python
# Module-level (NOT Config — auto_compact is a UI widget):
_auto_compact_paused: bool = False
MAX_COMPACT_FAILURES = 3
```

In `Agent.__init__()`:
```python
self._compact_failure_count = 0
```

### Integration: wrap create_llm_summary in Agent.run() (line ~5256)
```python
if COMPACTOR.should_compact(self.messages, CONFIG.context_max_tokens):
    if not _auto_compact_paused:
        output_fn("[i] Context high - creating LLM summary...")
        summary = None
        try:
            summary = COMPACTOR.create_llm_summary(self.client, self.messages)
        except Exception as e:
            pass  # create_llm_summary already swallows internally; this is belt-and-suspenders
        # CR-12: treat None return as failure (create_llm_summary returns None on any error)
        if summary is None:
            self._compact_failure_count += 1
            if self._compact_failure_count >= MAX_COMPACT_FAILURES:
                global _auto_compact_paused
                _auto_compact_paused = True
                output_fn(f"[!] Compact failed {MAX_COMPACT_FAILURES} times. "
                          f"Auto-compact paused for this session.")
            else:
                output_fn(f"[!] Compact summary failed "
                          f"({self._compact_failure_count}/{MAX_COMPACT_FAILURES}).")
            summary = "Conversation compacted (summary unavailable). Continue from recent context."
        else:
            self._compact_failure_count = 0  # Reset on success
        self.messages = COMPACTOR.compact(self.messages, summary)
        output_fn("[i] Conversation compacted to preserve context")
    else:
        output_fn("[!] Auto-compact paused (too many failures). Use manual Compact button.")
```

### CR-13: Also gate UI auto-compact paths
Add `if not _auto_compact_paused:` check in three places:
1. Pre-send auto-compact in `do_pre_send_compact()` line ~6597
2. Post-turn auto-compact check line ~6966
3. Manual compact button `on_compact()` line ~7263 — do NOT gate this one (user explicitly clicked it)

For paths 1 and 2, wrap the compaction logic:
```python
if auto_compact_checkbox.value and pct >= 80 and not _auto_compact_paused:
    ...
```

### Edge Cases
- `create_llm_summary()` returns None: counted as failure (CR-12)
- Reset on session restart: `_compact_failure_count` is instance-level, resets with new Agent
- `_auto_compact_paused` is module-level — persists for kernel lifetime (intentional; manual compact still works)
- Manual compact button: NOT gated — user override always works

---

## Implementation Order

1. Feature 6 (circuit breaker) — ~20 lines, lowest risk
2. Feature 1 (CLAUDE.md) — self-contained new function + config wiring
3. Feature 2+3 (git diff + staleness) — tool_read_file + tool_edit_file + tool_write_file + 4 clear locations
4. Feature 5 (post-compact restore) — Compactor.compact() extension
5. Feature 4 (microcompact) — new function + trigger in Agent.run()

---

## Testing Plan

### Test cases
```
# Feature 1
test_claude_md_load_workspace_root()
test_claude_md_load_parent_dir()
test_claude_md_missing_silently_skipped()
test_claude_md_too_long_truncated()
test_claude_md_subagent_skipped()
test_claude_md_config_flag_disables()
test_claude_md_circular_symlink_skipped()

# Feature 2
test_read_file_tracks_mtime()
test_read_file_mtime_thread_safe()
test_edit_file_stale_detection_aborts()
test_edit_file_not_stale_proceeds()
test_edit_file_updates_mtime_after_write()
test_write_file_updates_mtime_after_write()
test_mtime_cleared_on_session_reset()
test_mtime_cleared_on_clear()
test_mtime_cleared_on_load()
test_mtime_cleared_on_new()
test_edit_file_git_diff_shown()
test_edit_file_not_git_repo_no_diff()
test_edit_file_git_diff_capped_at_3000()

# Feature 4
test_microcompact_clears_old_results()
test_microcompact_keeps_last_n_newest()
test_microcompact_protects_todo_tools()
test_microcompact_skips_already_cleared()
test_microcompact_min_savings_threshold()
test_find_tool_name_returns_correct()
test_find_tool_name_returns_empty_for_unknown()
test_microcompact_clears_file_cache_context()
test_microcompact_reverses_inner_blocks_correctly()

# Feature 5
test_post_compact_restore_files()
test_post_compact_restore_file_deleted_skipped()
test_post_compact_restore_relative_path_resolved()
test_post_compact_restore_security_check()
test_post_compact_restore_budget_per_file_cap()
test_post_compact_restore_budget_global_cap()
test_post_compact_restore_role_alternation_assistant_last()
test_post_compact_restore_role_alternation_user_last()

# Feature 6
test_circuit_breaker_counts_none_returns()
test_circuit_breaker_pauses_after_3_failures()
test_circuit_breaker_resets_on_success()
test_circuit_breaker_pauses_ui_auto_compact()
test_circuit_breaker_does_not_gate_manual_compact()
```

---

## Version & Changelog
- Version: v4.0.0
- Changes from v3:
  - ADD: CLAUDE.md auto-load (`load_project_instructions()`, injected before active skills)
  - ADD: Pre-edit staleness check (`_check_file_staleness()`, aborts on external modification)
  - ADD: Mtime tracking on all reads + writes (`_FILE_READ_TIMES`)
  - ADD: Post-edit git diff summary in `tool_edit_file` result
  - ADD: Microcompact at 70% context (`microcompact()`, keeps last 3 results per tool)
  - ADD: Post-compact file restoration (`get_recently_read_files()`, `build_file_restoration_message()`)
  - ADD: Compact circuit breaker (`_auto_compact_paused`, 3-failure threshold)
  - ADD: Config field `load_claude_md: bool = True`
  - No breaking changes to v3 tool API or config format

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `git diff` subprocess hangs | Low | Medium | 5s timeout, `except Exception` |
| CLAUDE.md too long | Low | Low | 8000 char cap |
| Microcompact corrupts message structure | Low | High | Deep copy not needed — dict spread `{**block}` creates new dict |
| Post-compact restore out-of-workspace file | Fixed | High | CR-10: `SECURITY.validate_path()` before open |
| Role alternation bug in post-compact restore | Fixed | High | SR-5 guard |
| `_FILE_READ_TIMES` race condition | Fixed | Medium | CR-4: always under `_FILES_READ_LOCK` |
| False stale warning after self-edit | Fixed | Medium | CR-5: update mtime after write |
| Circuit breaker never trips | Fixed | Medium | CR-12: treat `None` return as failure |
