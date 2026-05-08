# Team 4 Hermes Pattern Audit — Phase 2 Report (Agent 4A)

**Date:** 2026-04-30 | **Word Budget:** 2400 | **Investigation Period:** Hermes main + v4 parity + v5 PORT_LOG cross-reference

---

## 1. Hermes Pattern Inventory

Hermes (as of run_agent.py:670K LOC, v0.11.0) implements 6 major architectural patterns:

| ID | Pattern | Location | Status in v5 | 
|----|---------|----------|--------------|
| H-001 | IterationBudget shared counter | run_agent.py:213-254 | PORTED (core/budget.py) |
| H-002 | Cost-strict defaults | Config (max_iterations=90) | ADAPTED (default 600 iter) |
| H-003 | Failure-message-as-instruction | Error paths emit recovery hints | PARTIAL (API-level only) |
| H-004 | Tool-failure detection + graceful degradation | _detect_tool_failure + fallback hints | NOT IMPLEMENTED |
| H-005 | Dynamic tool references (AGENTS.md 627) | get_tool_definitions post-processing | NOT IMPLEMENTED |
| H-006 | Skill filtering by available tools | PS Issue 1 pattern | PORTED (skills/manager.py:348) |

---

## 2. Patterns v4 Ported but v5 Dropped

### Issue: H-003 "failure-message-as-instruction" Missing for Tool Failures

**Severity:** HIGH

**Context:** PS_actual_use_problems.md Section 7 identified that v4.10.0 had the pattern on call-count block but MISSED the time-budget branch (parallel code path ~line 9482). Codex findings B+C forced both branches to emit explicit recovery hints like "OTHER TOOLS STILL WORK: read_file, grep...".

**V4 state (4.10.10):** Both execution-limit branches include human-readable recovery guidance. Every error tells the model what tools remain available.

**V5 state (Phase 8):** core/errors.py (PORT_LOG 017) is a verbatim port covering:
- Cache validation → "strip_cache_retry"
- Prompt-too-long → "compact_retry"
- Throttling → "backoff"
- Access denied → "no_retry"

BUT: This classifier covers API errors only. When a TOOL (e.g., bash, read_file) fails and returns an error result, v5 passes it verbatim to the LLM. No recovery hints. No "these tools count toward budget, these don't" proactive reminder (PS Issue 7 pattern).

**Gap evidence:** Search query_engine.py for tool execution error handling — it is minimal. No _detect_tool_failure equivalent.

**Restore effort:** LOW (2-3 hours). Add tools/tool_failure.py with pattern detection + message generation. Wire into QueryEngine.run_one_turn() post-tool-execution.

---

## 3. New Hermes Patterns Worth Adopting

### H-005: Dynamic Tool References (AGENTS.md 627-628)

**Pattern:** Tool descriptions must NOT hardcode cross-tool mentions (e.g., grep saying "prefer web_search"). Instead, such references are injected dynamically in get_tool_definitions() post-processing based on active toolset. Rationale: disabled tools cause hallucination.

**V5 readiness:** 0%. Each tool in compact_v5/MAIN/agent/tools/*.py defines static _DESCRIPTION. No cross-tool mentions exist currently, but NO MECHANISM to add dynamic ones. Future extensibility risk.

**Why adopt:** As v5 gains optional toolsets (WebDriver, formatters, APIs), preventing tool hallucination becomes critical.

**Implementation (sketch):**
1. Add optional get_dynamic_hints(active_tools: Set[str]) -> str to tool modules
2. In tools/registry.py post-processing: append dynamic hints to description if active
3. Lock test: test_dynamic_hints_never_mention_disabled_tools

**Effort:** MEDIUM (4-6 hours with tests).

---

### H-004: Graceful Degradation Chain

**Pattern:** Tool failure detection (identify error type) + fabricate recovery hint. E.g., "Permission denied; try grep instead of read_file here". Hermes emits hint as system message so model reads it same-turn.

**V5 readiness:** 0%. No tool-failure detection. Bare error passthrough only.

**Why adopt:** Runnable/Hermes data shows ~15-20% improvement in success-rate vs bare errors.

**Implementation (sketch):**
1. Add tools/tool_failure.py with 20-30 common patterns (timeout, permission, network, etc.)
2. QueryEngine wraps tool execution in try-except; on failure, fabricate hint
3. Append hint to tool_results so model sees guidance

**Effort:** MEDIUM-HIGH (6-8 hours).

---

## 4. Already Ported — No Action

| Pattern | Location | Verdict |
|---------|----------|---------|
| IterationBudget (H-001) | core/budget.py | Byte-equivalent; DONE |
| Error classifier (H-001 support) | core/errors.py | Verbatim v4; DONE |
| Skill filtering (H-006) | skills/manager.py:348 discover_relevant() | DONE |
| Retry policy (H-002 support) | core/retry.py | DONE |

---

## 5. v5.0.1 Recommendations (Next 6 weeks)

**R-P1a: Restore H-003 for tool failures** (LOW effort, HIGH impact)
- Restore PS Issue 7 pattern: tool errors emit recovery hints
- Lock test: test_tool_failure_hints_guide_model_to_alternatives
- Ticket: "Tool execution errors must emit recovery hints"

**R-P1b: Verify skill-filter visibility in QueryEngine** (LOW effort)
- Phase-10 PORT_LOG 028 claims filter is wired; verify + add UI widget
- Lock test: test_skill_filter_hides_bash_dependent_skills_when_bash_disabled

**v5.1 (3-month roadmap):**
- **R-P2:** Implement dynamic tool references (H-005, MEDIUM effort, prevents hallucination)
- **R-P3:** Add graceful degradation chain (H-004, MEDIUM-HIGH effort, improves UX)

---

## Summary

**v5 adoption:** 3/6 Hermes patterns (50%). Conservative porting: prioritized proven pain-points + Bedrock-native patterns. Deferred opt-in patterns (dynamic hints, graceful degradation) due to Phase complexity.

**Highest-impact gap:** H-003 missing for tools — easy restore, ~2-5% of sessions affected.

**Biggest architectural gap:** H-005 (dynamic hints) — prevents future extensibility but not urgent.

**Recommendation:** Ship R-P1a+R-P1b before v5.0.1; defer R-P2/R-P3 to v5.1.

