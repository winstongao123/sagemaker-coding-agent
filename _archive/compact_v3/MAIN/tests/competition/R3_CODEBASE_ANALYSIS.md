# Round 3: Comprehensive Codebase Analysis Competition

**Target**: sagemaker_agent.py (7,472 lines)
**Task**: Find EVERYTHING that can be optimized or improved
**All 3 agents ran for real.**

## Results Summary

| Metric | Claude Code (Opus 4.6) | Codex (gpt-5.3) | V3 (Haiku 4.5) |
|--------|:---:|:---:|:---:|
| **Total findings** | **35** | **37** | 28 |
| CRITICAL | 2 | 5 | ~2 |
| HIGH | 8 | 12 | ~5 |
| MEDIUM | 13 | 13 | ~12 |
| LOW | 12 | 7 | ~9 |
| Time | 188s | ~300s | 295s |
| Cost | ~$2.50 | ~$0.50 | $1.51 |
| Line-level citations | Every finding | Every finding | Partial |

## Winner: Codex (37 findings, 5 CRITICAL)

## Diagnosis: Why V3 Found Fewer

V3 on Haiku spent most turns **writing 6 deliverable documents** (1,500+ lines of markdown reports) instead of finding more issues. This is a behavioral pattern of Haiku — it's eager to generate output rather than analyze deeply.

- **Claude Code (Opus)**: Deep analysis, found subtle race conditions and architectural issues
- **Codex**: Most findings, aggressive about classifying severity, found subprocess and threading issues
- **V3 (Haiku)**: Found the main issues but spent budget writing reports instead of digging deeper

## Unique Findings by Agent

### Only Claude Code found:
- BUG-09: RetryHandler false positives on HTTP status codes (substring match on "500")
- PERF-05: render_chat re-renders ALL messages from scratch every time
- SEC-01: Workspace path injection in Python sandbox preamble (`repr()` needed)
- ARCH-03: Tool registry uses tuples instead of typed objects

### Only Codex found:
- Subprocess timeout doesn't hard-kill children (zombie processes)
- Parallel interactive approvals can deadlock
- Global exec budget resets on session reset (budget bypass)
- Quoted-path bypass in command validation regex
- Truncated output says "saved: None" in stealth mode

### All 3 found:
- `_FILES_READ` race condition (reassigned without lock)
- `PLAN_MODE_BLOCKED_TOOLS` dead code
- Hardcoded SECRET_KEY
- Module-level side effects at import time
- `create_chat_ui` is too long (1,725 lines)
- `Agent.run()` is too long (515 lines)

## Top 10 Most Impactful Fixes (Combined)

| # | Finding | Source | Severity | Effort |
|---|---------|--------|----------|--------|
| 1 | Workspace path injection in sandbox preamble | Claude | CRITICAL | Small |
| 2 | Subprocess timeout doesn't kill children | Codex | CRITICAL | Small |
| 3 | `_FILES_READ` race condition (4 locations) | All 3 | HIGH | Small |
| 4 | RetryHandler false-positive on status codes | Claude | MEDIUM | Small |
| 5 | Truncated output "saved: None" in stealth | Codex | MEDIUM | Small |
| 6 | `create_excel` reports "with chart" incorrectly | Codex | MEDIUM | Small |
| 7 | render_chat re-renders all messages every time | Claude | MEDIUM | Medium |
| 8 | Global exec budget resets on session reset | Codex | MEDIUM | Small |
| 9 | `escape_html` defined after first usage | Claude | MEDIUM | Small |
| 10 | Cleanup button runs without lock guard | Codex | LOW | Small |

## Honest Assessment

For **comprehensive codebase analysis**, model quality matters:
- **Opus found subtle, deep issues** (race conditions, injection paths, architectural problems)
- **Codex found the most issues** and was aggressive on severity
- **Haiku found the obvious issues** but wasted budget on report-writing

**Conclusion**: For thorough code review, use the strongest model you can afford. V3 on Haiku is good for quick reviews but misses subtle issues that Opus catches.
