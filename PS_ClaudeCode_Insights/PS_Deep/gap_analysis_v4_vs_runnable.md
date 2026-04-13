# Gap Analysis: V4 vs Runnable (2026-04-13)
## Based on PS_Deep Research of 2,010-file Runnable Codebase

## VERDICT: V4 is ~97% functionally equivalent. 6 actionable gaps, ~8 hours to close.

---

## Tier 1: Implement Immediately (60 lines, ~2 hours)

| # | Gap | Effort | What to Do |
|---|-----|--------|------------|
| 1 | Critical reminder re-injection | 20 lines | Append format/behavior reminders each LLM turn, not just once. Prevents verify agents from drifting off spec in long conversations. |
| 2 | Cache breakage warning | 10 lines | When post-compact LLM call misses cache, show "[!] Prompt cache miss — cost spike expected." |
| 3 | Post-compact FILE_CACHE cleanup | 30 lines | Clear FILE_CACHE context markers when file results are pruned. Agent currently thinks files still in context after compaction removes them. |

## Tier 2: This Sprint (140 lines, ~4 hours)

| # | Gap | Effort | What to Do |
|---|-----|--------|------------|
| 4 | Auto-nudge on 3+ tasks | 40 lines | Track task count. After 3+ tasks, auto-inject "Remember to verify." |
| 5 | Diminishing returns detection | 40 lines | Track output tokens/turn. If <10% of input for 2+ turns, switch to read-only. |
| 6 | Security review FP filtering | 60 lines | Spawn parallel verify agents for top security findings before reporting. |

## Tier 3: Defer (Low ROI)

| # | Gap | Notes |
|---|-----|-------|
| 7 | +2 verify strategies (async, webhook) | 1 hour, ~1% coverage gap |
| 8 | Skill preconditions | 30 lines, nice-to-have |
| 9 | Tool result offloading to disk | Medium effort, saves context |

## Tier 4: Blocked

| # | Gap | Why |
|---|-----|-----|
| 10 | Fork cache sharing | Needs Bedrock API support. Runnable gets ~100% cache hit on forks. V4 pays ~$0.01-0.05 per sub-agent cache creation. |

---

## WHAT V4 ALREADY MATCHES (no action needed)

- 7 agent types with coordinator pattern and parallel dispatch
- 4-tier compaction (MC + summary + PTL retry + circuit breaker)
- 22 tools with 100+ security patterns (fail-closed)
- Adversarial verification with 4 anti-rationalizations
- 3-agent parallel code review
- Cache boundary design (DYNAMIC marker)
- 4-type memory system (USER/FEEDBACK/PROJECT/REFERENCE)
- System prompt matches Runnable 9-section structure
