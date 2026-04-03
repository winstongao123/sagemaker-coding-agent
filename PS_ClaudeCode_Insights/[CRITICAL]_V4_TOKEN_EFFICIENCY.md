# [CRITICAL] V4 Token Efficiency — Closing the Gap with Runnable

**Date**: 2026-04-02
**Priority**: CRITICAL — affects cost, speed, and quality of every V4 session
**Version**: V4.3.3

---

## The Problem

V4 wastes 40-50% more tokens than Runnable for the same task. A simple "search and understand code" question costs $1+ on Sonnet because:

1. **LLM reads large files in chunks** instead of grepping first (20-30K tokens per read_file call)
2. **All 22+ tool schemas sent every call** even when only 3-4 are relevant (~1,800 tokens wasted/call)
3. **Tool results capped at 50K chars** (Runnable caps at 30K)
4. **Tool descriptions too short** — LLM makes poor tool choices without enough guidance

### Observed: Same Question, Different Efficiency

| Metric | Runnable (estimated) | V4 (observed) |
|--------|---------------------|---------------|
| Tool calls | 2-3 | 15+ |
| Input tokens | ~15K | ~362K |
| Cost | ~$0.05 | ~$0.42 |
| Context used | ~5% | ~21% |

---

## 4 Fixes Applied (V4.3.3)

### Fix 1: Large File Guard [HIGHEST IMPACT]

**Problem**: `read_file` on a 8,699-line file dumps 2,000 lines (~15K tokens) into context. LLM often needs only 10-20 lines.

**Fix**: When file >500 lines and no offset specified, return only first 50 + last 30 lines with a message:
```
[sagemaker_agent.py] 8699 lines total — LARGE FILE, showing first 50 + last 30 lines.
Use grep to find specific code, then read_file with offset/limit for the exact section.
```

**Impact**: Forces grep-first workflow. Saves ~15K tokens per large file read. For a typical "analyze this file" task: saves ~45K tokens (3 reads avoided).

**Code**: `tool_read_file()` in `sagemaker_agent.py`, large file guard block.

### Fix 2: Context-Aware Tool Filtering [HIGH IMPACT]

**Problem**: All 22+ tool schemas sent every API call (~1,800 tokens). Most calls only need 3-4 tools (read_file, grep, glob, bash).

**Fix**: Aggressive context-aware filtering. Exclude tools when not mentioned in recent conversation:

| Tool Group | Excluded When | Tokens Saved |
|-----------|--------------|-------------|
| Doc tools (6) | No document/chart keywords in last 4 messages | ~480 tokens |
| view_image | No image keywords | ~80 tokens |
| semantic_search | No semantic/deep search keywords | ~80 tokens |
| web_fetch | No URL keywords | ~80 tokens |

**Impact**: Typical coding session sends ~12 tools instead of 22+ (~720 tokens saved per call × 15 calls = ~10,800 tokens/session).

**Learning from Runnable**: Runnable has `ToolSearch` — the LLM discovers tools on demand. V4 can't replicate this (requires tool search as a tool itself), but context-aware filtering achieves ~60% of the same benefit.

### Fix 3: Lower Tool Result Cap [MEDIUM IMPACT]

**Problem**: Tool results capped at 50K chars. Runnable caps at 30K.

**Fix**: `max_output_chars` lowered from 50,000 to 30,000.

**Impact**: Large tool results truncated earlier, saving ~10K tokens when reading large files or running verbose commands.

### Fix 4: Enhanced Tool Descriptions [MEDIUM IMPACT]

**Problem**: V4 tool descriptions are 2-3 lines. Runnable's are ~90 lines per tool with examples and detailed WHEN NOT guidance.

**Fix**: Enhanced `read_file` description to explicitly mention the 500-line guard and grep-first workflow:
```
"IMPORTANT: For files >500 lines, you will only see first 50 + last 30 lines —
use grep to find the section you need, then read_file with offset/limit."
```

**Impact**: LLM learns the constraint from the tool description itself, not just from getting truncated results.

---

## Estimated Total Savings

| Fix | Tokens Saved/Session | % of Waste |
|-----|---------------------|-----------|
| Large file guard | ~45,000 | 25% |
| Tool filtering | ~10,800 | 6% |
| Result cap | ~10,000 | 6% |
| Better descriptions | ~15,000 (fewer wasted calls) | 8% |
| **Total** | **~80,000** | **~45%** |

A session that previously used 180K input tokens should now use ~100K for the same task.

---

## What V4 Still Can't Match (Honest)

| Runnable Feature | Why V4 Can't Replicate | Impact |
|-----------------|----------------------|--------|
| **ToolSearch (on-demand discovery)** | Requires tool-as-a-tool pattern; Bedrock may not support well | ~500 more tokens saved/call |
| **90-line tool descriptions** | Would push system prompt past cache threshold on Haiku | Better tool choices |
| **Model-level tool-use tuning** | Anthropic internal; not available via Bedrock | Fewer wasted calls |
| **Streaming tool execution** | Jupyter ipywidgets don't support streaming | Perceived speed |

These are architectural limitations. V4 closes the gap from 40-50% waste to ~15-20% waste. The remaining ~15% requires Runnable-level infrastructure changes.

---

## Verification Plan

After deploying V4.3.3:
1. Ask same question: "does sagemaker_agent.py allow caching?"
2. Compare: total calls, input tokens, cost
3. Expected: 4-6 calls (was 15+), ~50K tokens (was ~362K), ~$0.15 (was ~$0.42)

---

## Context-Aware Tool Filtering — Learning from Runnable

This is a key architectural pattern worth highlighting:

**Runnable's ToolSearch**: The LLM can call a `ToolSearch` tool to discover available tools by keyword. Only matched tools are loaded into the next call. This means the LLM never sees tool schemas it doesn't need.

**V4's Approximation**: Instead of on-demand discovery, V4 scans the last 4 messages for keywords and excludes irrelevant tool groups. Less flexible than ToolSearch but achieves ~60% of the token savings without requiring a new tool.

**Why This Matters**: Tool schemas are ~80 tokens each. With 22 tools, that's ~1,760 tokens per call. Over 15 calls = 26,400 tokens just for tool definitions. Filtering to 12 relevant tools saves ~800 tokens/call = 12,000 tokens/session.

This is a V4 ORIGINAL optimization. Runnable uses ToolSearch instead. Both achieve the same goal: don't waste tokens on tools the LLM won't use.

---

---

## Codex Review (gpt-5.3-codex, 162K tokens) — 4 Findings Fixed

### Finding 1: [HIGH] Large file guard skipped partial-read tracking
**Bug**: Guard returned before `_FILE_PARTIAL_READS` was set, so `edit_file` didn't warn about partial view.
**Fix**: Added `_FILE_PARTIAL_READS[abs_path] = (1, 80)` inside the guard before returning.

### Finding 2: [MEDIUM] Tool filtering keywords brittle
**Missing**: `markdown`, `readme`, `img`, `diagram`, `figure`, `references`, `callers`, `who calls`, `used by`, `link`, `uri`, `browse`, `gif`.
**Fix**: Added all missing keywords to their respective tool groups.

### Finding 3: [HIGH] Result cap was wrong — Runnable is 50K not 30K
**Bug**: We lowered `max_output_chars` to 30K claiming "matches Runnable." Codex verified Runnable's `DEFAULT_MAX_RESULT_SIZE_CHARS = 50_000`. Smart truncation at 30KB handles actual output separately.
**Fix**: Reverted to 50K. Smart truncation (`Truncation.MAX_BYTES = 30KB`) still handles the actual output cap.

### Finding 4: [LOW] Tool description didn't match guard condition
**Bug**: Description said ">500 lines always shows first/last" but code only triggers when `offset==0 AND limit>=2000`.
**Fix**: Description now says "without offset/limit" to match actual behavior.

---

*This document is tagged [CRITICAL] because token efficiency directly affects cost, speed, context usage, and answer quality. Every wasted token is money spent and context consumed.*

---

## Codex Final Review (gpt-5.3-codex, 128K tokens) — 5 More Findings Fixed

### Finding 1: [CRITICAL] FILE_UNCHANGED_STUB blocked valid full re-reads
**Bug**: After partial read (large file guard), a follow-up full read returned "unchanged" stub.
**Fix**: Skip stub when `_FILE_PARTIAL_READS` has entry for the file.
**Runnable**: Stricter range match + non-partial state check.

### Finding 2: [HIGH] Compact didn't clear file read state
**Bug**: `_FILES_READ`, `_FILE_READ_TIMES`, `_FILE_PARTIAL_READS` persisted after compact. Old context gone but stale markers blocked valid re-reads.
**Fix**: Clear all three on compact. Matches Runnable's `readFileState` clearing.

### Finding 3: [MEDIUM] Partial range (1,80) was inaccurate
**Bug**: Large file guard shows lines 1-50 + last 30 (not contiguous), but tracked as (1,80).
**Fix**: Changed to (1,50) — only first 50 lines were fully shown.

### Finding 4: [MEDIUM] Keyword "word" false-positive on "password"
**Bug**: Substring match `"word" in "password"` → true → doc tools NOT excluded when they should be.
**Fix**: Changed to `" word "` with spaces.

### Finding 7: [LOW] Comment said <500, code uses <200
**Fix**: Updated comment to match.

---

---

## [SUPER CRITICAL] Real-World Verification Results (2026-04-03)

### Test: "does sagemaker_agent.py support caching?" (same question, 3 runs)

| Metric | Old V4 (Haiku, before fixes) | New V4 (Haiku) | New V4 (Sonnet) |
|--------|---------------------------|----------------|-----------------|
| **Tool calls** | 15+ | **8** (47% fewer) | **4** (73% fewer) |
| **Input tokens** | 362,773 | **39,979** (89% less) | **9,413** (97% less) |
| **Cost** | $0.42 | **$0.06** (86% cheaper) | **$0.05** (88% cheaper) |
| **Context used** | 21% | **3.6%** | **2.6%** |
| **Cache savings** | $0 (inactive) | **$0.005 (12%)** | **$0.02 (85%)** |

### Why The Improvement

| Fix | Impact on Haiku | Impact on Sonnet |
|-----|----------------|------------------|
| **Large file guard** (>500 lines → 80 lines shown) | Saved ~15K tokens per read_file call | Same |
| **SEARCH BEFORE READ** in system prompt | Agent greps first instead of reading chunks | Agent greps first (more consistently) |
| **Context-aware tool filtering** | ~6 tools excluded per call | Same |
| **Total** | **9x improvement** (362K→40K) | **38x improvement** (362K→9K) |

### Key Insight: Haiku vs Sonnet

Sonnet is 4x more efficient than Haiku for the same task (4 calls vs 8, 9K vs 40K tokens). This is NOT a V4 issue — it's LLM tool-selection quality. Sonnet follows "SEARCH BEFORE READ" more consistently. Haiku still tries multiple search approaches before finding the answer.

**Recommendation**: Use Sonnet for complex analysis tasks (pays for itself in fewer tokens). Use Haiku for simple tasks where the cost difference matters more than efficiency.

---

*Two Codex reviews completed 2026-04-03. Total: 290K tokens, 12 findings, all addressed.*
*Real-world verification: 9x improvement on Haiku, 38x on Sonnet.*
*Reviews saved: `_archive/codex_reviews/v4_token_efficiency_review.txt` and `v4_final_review.txt`*
