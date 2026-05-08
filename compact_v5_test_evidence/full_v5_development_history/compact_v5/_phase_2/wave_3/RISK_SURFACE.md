# Wave 3 — Semantic-Bug Risk Surface Enumeration (v5.0.1)

**Date**: 2026-04-30  
**Scope**: 17 semantic-bug risk categories + 48 concrete lock tests for v5.0.1.

---

## Risk Categories

### 1. Concurrency / Race Conditions (5 tests)
- _discovered_tool_names per-run reset missing | core/query_engine.py:192-197
- IterationBudget.consume() race under parallel | core/budget.py:42-48
- _FILES_READ concurrency desync mtime | tools/_file_read_tracking.py:29-89
- _SINGLETON lazy-init TOCTOU | tools/skill.py:77-84
- reset_for_tests() leaves cached state | tools/skill.py:150-151

### 2. State Leakage Between Runs (4 tests)
- _discovered_tool_names persists sessions | core/query_engine.py:165-197
- SkillManager active-state not cleared | tools/skill.py:87,150-151
- Config singleton retains session values | runtime/config.py
- _FILES_READ.clear() doesn't track next session | tools/_file_read_tracking.py:84-88

### 3. Cache Invalidation Bugs (4 tests)
- cache_control placement wrong block | core/cache.py:66-88
- Per-tool schema hash not recomputed | core/cache.py (Phase L)
- Sub-agent cache-prefix not byte-identical | subagent/spawn.py (Phase G2)
- Cold-cache trigger assumes model available | runtime/bedrock_client.py (Phase A)

### 4. Token / Cost Accounting (4 tests)
- Sub-agent tokens not attributed parent | subagent/spawn.py
- Cache-hit count not tracked | runtime/bedrock_client.py (Phase L)
- session_cost_limit not persisted save/load | runtime/session.py (Phase B+)
- Budget.reset() mid-session | core/budget.py:61-64

### 5. Compaction Edge Cases (4 tests)
- Empty messages after compact | runtime/compact.py (Phase A)
- Thinking blocks with tool outputs | runtime/compact.py (Phase A)
- tool_use without tool_result mid-compact | runtime/compact.py (Phase A)
- In-progress approval mid-compact | runtime/compact.py (Phase A/C+)

### 6. Error Path Correctness (4 tests)
- Unknown tool error doesn't restore state | core/query_engine.py:360-365
- retry-after header parsing edge cases | core/retry.py (Phase L)
- MAX_RETRIES exhaustion silent | core/retry.py (Phase L)
- Transient misclassified permanent | core/errors.py:28-51

### 7. Approval Flow Correctness (3 tests)
- Approve/Deny/Always button race | core/query_engine.py (Phase C+)
- Always rule logging misses denials | core/query_engine.py (Phase C+)
- Kernel interrupt mid-approval hangs | core/query_engine.py (Phase C+)

### 8. Skill Name Resolution (3 tests)
- Fuzzy match collision two skills | skills/manager.py (Phase I)
- Typo fuzzy false positive | skills/manager.py (Phase I)
- Cache invalidation skills/ dir change | tools/skill.py

### 9. Sub-Agent Lifecycle (3 tests)
- Depth-limit off-by-one max_depth=2 | subagent/spawn.py:139
- Budget not decremented on timeout | subagent/spawn.py
- Worktree cleanup hangs Windows | subagent/spawn.py (Phase G)

### 10. Notebook UI State Sync (2 tests)
- Agent state != UI after restart | ui/chat_ui.py (Phase E/F)
- User Send while processing | ui/chat_ui.py (Phase E/F)

### 11. Slash Command Edge Cases (3 tests)
- /save mid-tool-execution | core/query_engine.py (Phase D)
- /compact mid-spawn | runtime/compact.py (Phase A/D)
- /clean while active | core/query_engine.py (Phase D)

### 12. AGENT_STATUS Auto-Load Races (2 tests)
- File modified during read | agent/__init__.py (Phase B+)
- Missing vs empty file | agent/__init__.py (Phase B+)

### 13. Rate-Limit Window Edge Cases (2 tests)
- Clock drift client vs server | core/query_engine.py (Phase C+)
- Sliding window O(n^2) memory | core/query_engine.py (Phase C+)

### 14. Output Format Edge Cases (2 tests)
- Markdown malformed backticks | ui/render.py (Phase E)
- HTML escape user content | ui/render.py (Phase E)

### 15. File-State Tracking (2 tests)
- _FILES_READ.clear() post-compact | tools/_file_read_tracking.py:84-88
- edit_file stale mtime check | tools/_file_read_tracking.py:58-81

### 16. Memory Extraction Triggers (2 tests)
- Empty session extraction | runtime/memory_extract.py (Phase H)
- Session errors-only extraction | runtime/memory_extract.py (Phase H)

### 17. Streaming-Related (2 tests)
- Bedrock parsed non-streaming | runtime/bedrock_client.py
- Tool result no OOM | core/query_engine.py:110-116

---

## Severity & Confidence

**CRITICAL (ship-blocker)**: Concurrency #1, State leakage #1, Token #1, Error #1-2.  
**HIGH (Phase-gate)**: Cache, Compaction, Approval, Sub-agent.  
**MEDIUM (Phase-safe)**: Skill, Rate-limits, File-state, Output (Phase E/F).  
**LOW (test-maturity)**: Streaming (never enabled).

**Q4 100% Confidence requires**:
1. Lock test per category BEFORE each Block lands.
2. Real-Bedrock smoke (Block J) + concurrent load.
3. Per-turn/session state audit logs.
4. Codex AXIS A/B/C per phase.

---

**Total: 17 categories × 48 concrete lock tests**
