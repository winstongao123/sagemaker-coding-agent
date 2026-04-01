# PS_V4.1_FEATURES — Deferred Feature Reference

> Source: Claude Code leaked source (2026-03-31) → compact_v3 deep review
> Status: v4.0.0 shipped. This doc tracks what's next.
> Target file: compact_v4/MAIN/agent/sagemaker_agent.py

---

## Features To Implement (in order)

### #14 — Prompt Cache Boundary ⭐ HIGHEST ROI
**What:** Split SYSTEM_PROMPT into a static cacheable part + dynamic per-session part. Mark the static part with Bedrock's `cache_control` so Bedrock only processes it once and caches it.

**Why it matters:** Every API call currently sends ~6000 tokens of system prompt. With caching, first call processes all 6000, subsequent calls cost ~0.1× for the cached portion (90% token reduction per turn). On a 60-turn session that's ~300,000 tokens saved.

**Claude Code source:** `src/utils/systemPromptSections.ts` — `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` constant. Static section marked with `cacheControl: { type: "ephemeral" }` in the API call.

**Bedrock implementation:**
```python
# System field changes from string to list of blocks:
"system": [
    {"type": "text", "text": SYSTEM_PROMPT_STATIC,
     "cache_control": {"type": "ephemeral"}},   # ← cached
    {"type": "text", "text": dynamic_part}       # ← not cached (memory, skills, CLAUDE.md)
]
```
Bedrock supports this via `anthropic-beta: prompt-caching-2024-07-31` header.

**Risk:** Bedrock prompt caching was added mid-2024. Verify model supports it. If not supported, gracefully fall back to current string format.

**Config flag:** `enable_prompt_cache: bool = True`

---

### #12 — Dangerous Path Enforcement
**What:** Even if a user clicks "Approve" for a bash command, certain catastrophic operations are always blocked regardless. Hard override that cannot be bypassed.

**Why it matters:** One misclick on "Approve" for `rm -rf /` or `dd if=/dev/zero of=/dev/sda` would destroy the machine. The current approval dialog is the only protection — this adds a second layer that can't be bypassed.

**Claude Code source:** `src/tools/BashTool/bashSecurity.ts` — `DANGEROUS_PATHS` set + override logic that runs AFTER permission classifier.

**Patterns to block absolutely:**
- `rm -rf /`, `rm -rf ~`, `rm -rf /*`, `rm -rf ~/`
- `dd if=/dev/zero`, `dd if=/dev/urandom` (to disk targets)
- `mkfs.*`, `fdisk`, `parted` (disk formatting)
- `:(){:|:&};:` (fork bomb)
- `chmod -R 777 /`, `chmod -R 000 /`
- `> /dev/sda`, `> /dev/hda`

**Implementation:** New check in `SECURITY.validate_command()` that runs before existing denylist, returns hard-blocked error even if command passed allowlist.

**Risk:** Very low — pure additive. None of these patterns have legitimate use in a coding agent.

**Config flag:** None — always on, cannot be disabled.

---

### #10 — Partial View Guard on Edit
**What:** When `read_file` is called with `offset` or `limit` (i.e. only read part of a file), track that the view was partial. If `edit_file` is then called on that file, warn: "You only read lines X-Y of this file. Re-read without offset/limit before editing."

**Why it matters:** Agent reads lines 100-200 of a 2000-line file, then tries to edit line 1500 (which it never saw). It has no idea what surrounds line 1500 — high risk of breaking surrounding code.

**Claude Code source:** `FileEditTool.ts` — `partialView` flag in file state cache. Returns error if file was only partially read.

**Implementation:**
```python
# Extend _FILE_READ_TIMES dict (or new dict):
_FILE_PARTIAL_READS: Dict[str, Tuple[int, int]] = {}
# key = abs_path, value = (offset, limit) if partial, or None if full read

# In tool_read_file: set partial flag if offset > 0 or limit < total_lines
# In tool_edit_file: check and warn if partial flag set
```

**Warning (not hard block):** Return warning message but still allow edit — agent can acknowledge and proceed. Staleness check already hard-blocks; this is advisory.

**Risk:** Low — additive warning only. Clear on session reset alongside `_FILE_READ_TIMES`.

**Config flag:** None — always on.

---

### #11 — Command Auto-Classifier
**What:** Before showing the Approve/Deny dialog for bash commands, automatically classify the command as safe/ask/deny. Read-only commands (git status, ls, cat, echo, pwd, etc.) auto-approve without asking. Obviously destructive commands auto-deny. Only ambiguous commands prompt the dialog.

**Why it matters:** Currently every single bash command pops up a dialog — including completely harmless things like `git log` or `echo hello`. This kills the workflow. Should only ask when genuinely needed.

**Claude Code source:** `src/utils/permissions/` — `classifyBashCommand()` returns `{ behavior: "auto-approve" | "ask" | "deny", reason: string }`.

**Classification rules:**
```
AUTO-APPROVE (read-only):
  git status, git log, git diff, git show, git branch
  ls, find, echo, pwd, cat (single file), head, tail, wc
  python --version, pip list, which, env (no secrets)

ASK (ambiguous):
  git commit, git push, pip install, npm install
  python script.py, bash script.sh
  cp, mv (within workspace)
  mkdir, touch

AUTO-DENY (always block — handled by #12 above):
  rm -rf /, dd if=/dev/zero, mkfs, fork bombs
```

**Implementation:** New `_classify_bash_command(cmd: str) -> Literal["auto_approve", "ask", "deny"]` function called before the approval callback.

**Risk:** Medium — misclassifying a dangerous command as safe is a real risk. Start conservative: only auto-approve the explicitly listed patterns.

**Config flag:** `bash_auto_approve_readonly: bool = True`

---

### #7 — 4-Type Memory Structure
**What:** Restructure `memory.md` into 4 labelled sections instead of a flat file. No new functionality — just organises what's already there.

**Types (from Claude Code's `src/memdir/`):**
1. **[USER]** — Who the user is: role, expertise, preferences
2. **[FEEDBACK]** — How to behave: corrections, confirmed approaches
3. **[PROJECT]** — Ongoing work: goals, decisions, deadlines not in code
4. **[REFERENCE]** — Pointers to external systems: Linear, Grafana, Slack channels

**Why it matters:** Currently `memory.md` is a flat dump. As it grows it becomes hard to load selectively or search. Typed sections let the agent load only relevant types.

**Implementation:** When writing to `memory.md`, prepend the entry with its type tag. When loading, parse sections separately and inject only relevant types based on current context.

**Risk:** Very low — backwards compatible. Old flat memory still loads fine.

**Config flag:** None — always on.

---

### #8 — Memory Auto-Extraction
**What:** At the end of a long session (or when compact runs), the agent makes one additional LLM call: "What from this conversation is worth saving to memory.md?" and writes the result.

**Why it matters:** Currently you have to manually decide what to save. Things get forgotten between sessions. This makes the agent incrementally smarter without user effort.

**Claude Code source:** `src/services/extractMemories/` — runs after each turn, decides what to save per type.

**Implementation:**
```python
MEMORY_EXTRACT_MIN_TURNS = 10  # Only run if session has >= 10 turns
MEMORY_EXTRACT_PROMPT = """
Review this conversation. For each of these types, identify what (if anything) should be saved:
[USER]: facts about who the user is and how they work
[FEEDBACK]: corrections or confirmed approaches for future sessions
[PROJECT]: decisions, goals, or context about the current project
[REFERENCE]: pointers to external resources mentioned

Format: type | key | one-sentence fact
Only include genuinely useful, non-obvious things. Skip ephemeral task details.
"""
```

**Risk:** Medium — bad extraction pollutes memory. LLM call adds cost. Gate behind session length check and make it opt-in first.

**Config flag:** `enable_memory_extraction: bool = False` (off by default, user opts in)

---

## Features to SKIP (permanently or long-term)

### #9 — Auto-Surface Relevant Skills
**Skip reason:** Already partially implemented in v3/v4 (keyword auto-match on send). Full implementation would need semantic matching, which adds complexity without clear payoff given you already have `/skill` commands and auto-match.

### #13 — Worktree Isolation
**Skip reason:** High effort (full git worktree management), and SageMaker notebooks don't benefit much from branch isolation. The existing snapshot/revert system covers the same safety need.

### #15 — Named Teammates
**Skip reason:** Overkill. The `task` tool with sub-agents already covers 95% of multi-agent needs. Named persistent agents are a product feature for team use, not solo SageMaker development.

### #16 — Tree-Sitter AST Bash Parsing
**Skip reason:** Rust/native dependency — impossible to install in standard SageMaker environment. Regex denylist already blocks all practical attacks. The marginal security gain doesn't justify the dependency complexity.

---

## Implementation Status

| # | Feature | Status | Version |
|---|---|---|---|
| 14 | Prompt cache boundary | ✅ Done | v4.1.0 |
| 12 | Dangerous path enforcement | ✅ Done | v4.1.0 |
| 10 | Partial view guard | ✅ Done | v4.1.0 |
| 11 | Command auto-classifier | ✅ Done | v4.1.0 |
| 7 | 4-type memory | ✅ Done | v4.1.0 |
| 8 | Memory auto-extraction | ✅ Done | v4.1.0 |
| 9 | Auto-surface skills | ⏭ Skipped | — |
| 13 | Worktree isolation | ⏭ Skipped | — |
| 15 | Named teammates | ⏭ Skipped | — |
| 16 | Tree-sitter bash | ⏭ Skipped | — |
