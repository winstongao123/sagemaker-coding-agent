# V4.3.3 — Efficiency & Budget Fixes (2026-04-02)

## Critical Issue: Tool Call Efficiency

### Problem Discovered
V4 agent made 15+ tool calls for a single question, burning $1.03 on Sonnet. The LLM repeatedly called `read_file` to scan an 8,699-line file instead of using `grep` to find specific code. Each `read_file` added thousands of tokens to context, causing exponential cost growth.

### Root Cause
V4 had WHEN-not-WHAT tool descriptions (v4.3.2) but the **system prompt** lacked explicit efficiency guidance. Runnable Claude Code has stronger directives:
- `"SEARCH BEFORE READ"` — grep first, read_file only for specific sections
- `"MINIMIZE TOOL CALLS"` — each call costs tokens, plan before acting
- `"Do NOT use bash when a dedicated tool exists"` — with explicit substitution list

### Fix Applied
Added to system prompt (`SYSTEM_PROMPT` in `sagemaker_agent.py`):
```
# Using Tools — EFFICIENCY IS CRITICAL
- SEARCH BEFORE READ: Use grep to find specific code, not read_file to scan large files.
  Each read_file adds thousands of tokens to context. grep finds exact lines needed.
- Use glob to locate files, then grep to find content, then read_file only for
  the specific section you need (use offset/limit).
- MINIMIZE TOOL CALLS: Each call costs tokens. Plan your approach before starting —
  don't explore aimlessly.
```

### Expected Impact
- Fewer tool calls per question (15+ → 3-5 for typical queries)
- Lower context growth (less file content in conversation)
- Lower cost (fewer tokens sent per call)
- More stable behavior (less variation between runs)

### Why Runnable Doesn't Have This Problem
Runnable's system prompt (`prompts.ts` line 292-301) has explicit "use X instead of Y" rules in the **system prompt itself**, not just in tool descriptions. The system prompt is the first thing the LLM reads — tool descriptions are secondary context. V4 now matches this pattern.

---

## Critical Issue: Budget Hard-Stop

### Problem Discovered
When session cost hit the $1.00 limit, the agent stopped immediately with no option to continue. User lost the in-progress work and had to start a new session.

### Fix Applied
1. **Budget slider added to UI** — adjustable $0.50 to $20.00 in $0.50 steps
2. **Soft-stop instead of hard-stop** — agent warns and tells user to raise the Budget $ slider, instead of killing the session
3. **Default raised** — $1.00 → $5.00 (Sonnet can burn $1 in 5 minutes)
4. **Live adjustment** — changing the slider during a run takes effect immediately

### Before
```
[Session cost $1.0356 reached limit $1.00. Stopping.]
← Session dead. Must start new session.
```

### After
```
[Session cost $5.12 reached limit $5.00. Increase Budget $ slider in UI to continue, or click Stop.]
← Raise slider to $10 → agent continues automatically
```

---

## Cache Percentage Bug

### Problem
Metrics bar showed `172% cached` — cache percentage exceeded 100%.

### Root Cause
`session_cache_read` accumulates across all API calls. With many cache hits, total cache-read tokens can exceed total input tokens (since each call reports them independently).

### Fix
Capped at 100%: `min(100, (session_cache_read / session_input * 100))`

---

## Status
- System prompt efficiency guidance: **Added**
- Budget slider in UI: **Added**
- Soft-stop on budget: **Added**
- Default budget $1 → $5: **Changed**
- Cache % capped at 100%: **Fixed**
- All changes in `sagemaker_agent.py` v4.3.3
