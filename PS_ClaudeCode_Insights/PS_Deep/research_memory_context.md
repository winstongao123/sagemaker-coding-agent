# CLAUDE CODE MEMORY, CONTEXT MANAGEMENT & QUERY SYSTEM

## Executive Summary

Multi-layered system: memdir (persistent file-based memory), QueryEngine (18,623-line conversation loop), 4-tier compaction, token budget tracking, session history, project onboarding state.

---

## 1. MEMORY DIRECTORY SYSTEM (memdir/)

### Core Files

#### memdir.ts (507 lines)
- **Entrypoint truncation**: Max 200 lines / 25KB for MEMORY.md
- **Memory prompt building**: Two modes — typed instructions only vs. with MEMORY.md content
- **KAIROS mode**: Append-only daily logs instead of MEMORY.md index
- **Team memory**: Combined prompt when team+auto both enabled

#### memoryTypes.ts (272 lines)
**Four Memory Types:**
1. **user** (always private) — role, goals, knowledge, preferences
2. **feedback** (default private) — what to repeat/avoid, with Why + How to apply
3. **project** (bias toward team) — current work state, deadlines, decisions
4. **reference** (usually team) — external system pointers

**Prompt Sections:** TYPES_SECTION_COMBINED, WHAT_NOT_TO_SAVE_SECTION, WHEN_TO_ACCESS_SECTION, TRUSTING_RECALL_SECTION

#### paths.ts (279 lines)
**Path Resolution Chain:**
1. CLAUDE_COWORK_MEMORY_PATH_OVERRIDE env var
2. autoMemoryDirectory in settings.json (user-trusted sources only)
3. ~/.claude/projects/<sanitized-git-root>/memory/ (default)

#### teamMemPaths.ts (293 lines)
**Security Hardening (PSR M22186):**
- sanitizePathKey(): Rejects null bytes, URL-encoded traversals
- realpathDeepestExisting(): Symlink-aware validation
- Protection: URL-encoded traversal, Unicode normalization, Windows backslash, symlink escape, dangling symlink, absolute path injection, ELOOP cycles

#### findRelevantMemories.ts (142 lines)
**Algorithm:** Scan → format manifest → Sonnet classifier → return top 5 relevant memories

#### memoryScan.ts (95 lines)
Fast scan: readdir recursive, parse frontmatter (30 lines max), sort newest-first, cap 200

#### memoryAge.ts (54 lines)
Age calculation + staleness warnings for memories >1 day old

---

## 2. QUERY ENGINE (query.ts — 18,623 lines)

### Architecture: Async generator state machine

**Query Loop Lifecycle:**
1. Build config snapshot (gates once)
2. Prefetch relevant memories (parallel)
3. Normalize messages for API
4. Call API (queryModelWithStreaming)
5. Process response (tool calls, thinking blocks, errors)
6. Token budget check
7. Continue decisions (tools pending? compact triggered? max turns?)
8. Yield message events

### Key State
```
messages, toolUseContext, autoCompactTracking,
maxOutputTokensRecoveryCount (max 3), hasAttemptedReactiveCompact,
turnCount, transition (why previous iteration continued)
```

### Token Budget (query/tokenBudget.ts)
- **Continue** if: budget > 0, turn tokens < 90%, NOT diminishing returns
- **Diminishing Returns**: continuationCount >= 3 AND last TWO deltas < 500 tokens
- **Stop** with completion event when diminishing or budget exhausted

---

## 3. COMPACTION SYSTEM (services/compact/)

### autoCompact.ts — Threshold Detection
```
effectiveContextWindow = contextWindow - min(maxOutputTokens, 20_000)
autoCompactThreshold = effectiveContextWindow - 13,000 tokens
```

**Thresholds:**
| Threshold | Tokens Before Limit | Trigger |
|-----------|-------------------|---------|
| Auto-Compact | 13,000 | Proactive compaction |
| Warning | 20,000 | UI warning (yellow) |
| Error | 20,000 | UI error (red) |
| Blocking | 3,000 | Manual compact required |

**Circuit Breaker:** MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3

### compact.ts — Full Summarization
1. Strip images from user messages
2. Group messages by API round
3. Call Claude with compact prompt
4. Return CompactionResult with summary

**Post-Compact Constants:**
- POST_COMPACT_MAX_FILES_TO_RESTORE = 5
- POST_COMPACT_TOKEN_BUDGET = 50,000
- POST_COMPACT_MAX_TOKENS_PER_FILE = 5,000
- POST_COMPACT_MAX_TOKENS_PER_SKILL = 5,000
- POST_COMPACT_SKILLS_TOKEN_BUDGET = 25,000

### microCompact.ts — Tool Result Pruning
- Prunes: FILE_READ, SHELL, GREP, GLOB, WEB_SEARCH, WEB_FETCH, FILE_EDIT, FILE_WRITE
- Time-based: clear old tool results
- Size-based: truncate oversized results

### cachedMicrocompact.ts — Server-Side Cache Edits
- CachedMCState: pending vs. pinned cache edits
- consumePendingCacheEdits(), getPinnedCacheEdits(), pinCacheEdits()
- Uses Anthropic's cache_edits API (not message mutation)

### reactiveCompact.ts — API-Triggered Recovery
- Triggered on prompt_too_long error
- Suppresses proactive autocompact when enabled
- isWithheldPromptTooLong: suppress error from SDK until recovery attempted

---

## 4. HISTORY MANAGEMENT (history.ts — 465 lines)

**Storage:** ~/.claude/history.jsonl (global, filtered by project at read time)

**Paste Content:** Small (≤1024 bytes) inline, large → hash reference to paste store

**Write Path:** Queue → batch flush with file lock → append JSONL
**Read Path:** Pending + disk, reverse order, deduped by display

**Security:** File mode 0o600, lock-protected writes, 10s stale lock timeout

---

## 5. PROJECT ONBOARDING (projectOnboardingState.ts — 84 lines)

**Steps:**
1. workspace: "Create app or clone repo" (if dir empty)
2. claudemd: "Run /init for CLAUDE.md" (if dir not empty)

**Show Condition:** !completed && seenCount < 4 && !IS_DEMO

---

## 6. FEATURE FLAGS

| Gate | Purpose |
|------|---------|
| KAIROS | Assistant mode (daily logs) |
| EXTRACT_MEMORIES | Memory extraction background agent |
| REACTIVE_COMPACT | Reactive compaction on API error |
| CACHED_MICROCOMPACT | Ant-only tool result caching |
| TOKEN_BUDGET | Token budget auto-continuation |
| MEMORY_SHAPE_TELEMETRY | Memory selection telemetry |

---

## 7. ERROR RECOVERY

**max_output_tokens:** Retry up to 3 times, withhold error from SDK
**Autocompact failures:** Circuit breaker after 3, fall back to manual /compact
**Symlink escapes:** Throw PathTraversalError, skip file, log security event

---

## 8. MEMORY FILE FORMAT

**Frontmatter (YAML):**
```yaml
---
name: User prefers terse responses
description: Communication preference for response style
type: feedback
---
```

**MEMORY.md Index:** One-line entries, ~150 chars each, max 200 lines / 25KB

**File Paths:**
```
~/.claude/projects/<git-root>/memory/
  MEMORY.md, <topic>.md
  team/MEMORY.md, team/<topic>.md
  logs/YYYY/MM/YYYY-MM-DD.md (KAIROS)
~/.claude/history.jsonl
```
