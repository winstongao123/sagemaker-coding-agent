# Phase 2 Wave 2: V4 Section 2 Analysis (Lines 3000–6000)

## Overview
Lines 3000–6000 cover: **Compactor class** (context pruning/summarization), **microcompact/context_collapse** algorithms, **SkillManager + SkillInfo** (skill discovery/patching), **MCP client managers** (stdio/HTTP), **file-state tracking** (_FILES_READ, _FILE_READ_TIMES, _FILE_PARTIAL_READS), **token accounting** (TokenTracker, _MODEL_PRICING), and **command registry**.

**Source:** `D:/Github/sagemaker-coding-agent/compact_v4/MAIN/agent/sagemaker_agent.py:3000–6000`

---

## Component Analysis Table

| **Component** | **V4 Lines** | **Purpose** | **V5 Status** | **V5 Location** | **Severity** | **Notes** |
|---|---|---|---|---|---|---|
| **Compactor.estimate_tokens()** | 186–212 | Tiktoken-based token count, fallback chars/3 | PRESENT | core/budget.py | HIGH | Conservative 4/3 multiplier |
| **Compactor.prune_tool_outputs()** | 215–272 | Protect last 40K tokens + special tools; truncate stale results | PARTIAL | core/cache.py | HIGH | PROTECTED_TOOLS mapping incomplete |
| **Compactor.create_summary_prompt()** | 275+ | 9-section summary template (Primary, Tech, Files, Errors, State, Q's, Next, Agent Summary) | PARTIAL | runtime/truncation.py | MEDIUM | Hermes pattern |
| **MICROCOMPACT_TRIGGER_PERCENT** | 3822 | 0.70 — trigger at 70% context | PRESENT | runtime/config.py | MEDIUM | Pre-triggers full compaction |
| **COLD_CACHE_THRESHOLD_SECONDS** | 3826 | 1800s — proactive microcompact on 30min+ gaps | PRESENT | core/budget.py | HIGH | Bedrock cache TTL margin |
| **microcompact()** | 3851–3895 | Replace old tool results with marker; keep last N per tool | PARTIAL | runtime/truncation.py | HIGH | Must clear FILE_CACHE context |
| **_is_stale_round_trip()** | 3919–3975 | Detect assistant-only + marker-only user messages | **MISSING** | — | HIGH | Breaks context_collapse |
| **context_collapse()** | 3978–4017 | Collapse 3+ stale round-trip pairs into synthetic 2-message block | **MISSING** | — | MEDIUM | V4.10.0 feature |
| **ContextManager** | 3464–3529 | Usage tracking + 3-level warnings (80%/90%/95%) | PRESENT | core/budget.py | HIGH | Fixed overhead estimation |
| **TokenTracker** | 3565–3755 | Session cost/cache tracking; budget checks | PRESENT | core/budget.py | HIGH | Cache pricing 10% read / 125% write |
| **SkillManager** | 2684+ | Discover SKILL.md; filter by relevance; patching system | PRESENT | skills/manager.py | HIGH | Phase 10 ported byte-for-byte |
| **SkillInfo** | 2674–2681 | Metadata: name, description, location, auto_trigger flag | PRESENT | skills/manager.py | MEDIUM | Hermes filter v5+ addition |
| **_TODOS global** | 3763 | Todo list synced to ui_state | PRESENT | runtime/state.py | MEDIUM | Persistence coupling |
| **_FILES_READ** | 3764–3767 | Set + lock: track read files + mtime + partial ranges | PRESENT | core/cache.py | HIGH | Staleness + dedup detection |
| **FILE_UNCHANGED_STUB** | 3768 | Token-saving stub return (V4.2 V2-H) | PRESENT | core/cache.py | MEDIUM | Mtime-based optimization |
| **McpStdioClient** | 3122–3276 | JSON-RPC stdio transport | PRESENT | runtime/mcp_client.py | MEDIUM | Process spawning + timeout |
| **McpManager** | 3348–3451 | Multi-server mgmt + name collision detection | PRESENT | runtime/mcp_client.py | MEDIUM | Closure-based tool handlers |
| **_offload_large_result()** | 3771–3811 | Save large outputs to .tool_cache; return preview | PARTIAL | runtime/truncation.py | MEDIUM | Path normalization needed |

---

## MISSING Components (Regression Risk)

| **What** | **Regression** |
|---|---|
| `_is_stale_round_trip()` | context_collapse() cannot detect stale pairs; markers accumulate; no collapse happens → context bloat in long research sessions |
| `context_collapse()` | Segment-level coalescing disabled; consecutive tool round-trips with marker-only results waste 40+ tokens each |

---

## V5 Port Status

- **PRESENT (ready):** TokenTracker, ContextManager, SkillManager, MCP clients, file tracking, _TODOS
- **PARTIAL (needs work):** microcompact integration, Compactor.prune_tool_outputs (PROTECTED_TOOLS), _offload_large_result (path handling)
- **MISSING (critical):** _is_stale_round_trip, context_collapse (both v4.10 features)

---

## Key Coupling Notes

1. **microcompact() ↔ FILE_CACHE.clear_context()**: If read_file results cleared, agent must forget cached file state
2. **COLD_CACHE_THRESHOLD_SECONDS**: V5 runtime must poll inter-call gaps; trigger aggressive microcompact on >1800s gaps
3. **FILE_UNCHANGED_STUB (V4.2 V2-H)**: Preserve exact 0.5s mtime tolerance for staleness checks
4. **Skill audit trail (_log_skill_patch_event)**: JSONL ensures patch transparency; no audit = untracked changes
5. **Cold-cache path (KEEP_LAST_N_COLD_CACHE=1)**: Apply on 30min+ gaps for aggressive context recovery

---

**Completion Estimate:** PRESENT (4–6h) + PARTIAL (6–10h) + MISSING (4–6h) = **14–22 hours**

