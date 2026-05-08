# Phase 2 Wave 2: Runnable QueryEngine Line-by-Line Analysis

**Scope:** Comprehensive comparison of Runnable's QueryEngine.ts (1295 LOC), Tool.ts, tools.ts against v5's query_engine.py + tools/registry.py.

---

## Executive Summary

Runnable's QueryEngine is a highly-optimized agent loop with sophisticated state management, permission tracking, structured-output retry limiting, and compact-boundary handling. v5's query_engine.py is a minimal, focused port (~400 LOC). **Gap analysis identifies 8 MISSING features**, most notably **structured-output retry counters (PHASE 8 BLOCKER)** and **discoveredSkillNames reset (PHASE 10 PREP)**. No breaking restructuring required; all gaps are additive.

---

## QueryEngine State & Initialization

| Runnable (lines) | Feature | v5 Status | Adoption Value | Effort |
|---|---|---|---|---|
| 185-207 | mutableMessages: Message[] | ✓ PRESENT | - | - |
| 188 | permissionDenials: SDKPermissionDenial[] | ✗ MISSING | HIGH: SDK reporting | Medium |
| 197 | discoveredSkillNames: Set<string> | ✓ (not reset per turn) | CRITICAL BUG | Trivial |
| 203 | abortController | ✗ MISSING | MEDIUM: user stop | Low |
| 206 | totalUsage: NonNullableUsage | ✗ MISSING | HIGH: token tracking | Medium |

---

## Critical Gaps Ranked by Phase Impact

### Phase 8 BLOCKERS (Must Fix Before Release)

**1. Structured Output Retry Counter (Lines 1004-1048)**
- **Status:** ✗ COMPLETELY MISSING
- **Impact:** Without retry limiting, model loops infinitely retrying SYNTHETIC_OUTPUT_TOOL on JSON failures
- **Required:** countToolCalls helper, retry-check branch, MAX_STRUCTURED_OUTPUT_RETRIES env var, structured_output yield
- **Effort:** Medium (3-4 files, ~50 LOC)
- **v5 Blocker:** YES

**2. discoveredSkillNames.clear() Per Turn (Line 238)**
- **Status:** ✗ NOT RESET (initialized once, persists across turns)
- **Impact:** Phase 7 Phase deferral contract violation; discovered tools leak to subsequent turns
- **Required:** Add 1 line at start of run() method
- **Effort:** Trivial (1 line)
- **v5 Blocker:** YES (Phase 10 prep)

### Phase 9+ Features (Deferrable)

| Feature | v5 Has? | Phase | Effort | Priority |
|---|---|---|---|---|
| wrappedCanUseTool + denial tracking | NO | 9 | Medium | High |
| Orphaned permission handler | NO | 9 | Low | Medium |
| Stream event handling (usage accumulation) | NO | Future | Medium | Low |
| System message handling (compact/snip) | NO | 11 | Medium | Low |
| Attachment handling (max_turns signal) | NO | Future | Low | Low |
| Error diagnostic tracking | NO | 9+ | Low | Low |

---

## Tool Registry & Helpers

All major Runnable registry functions PRESENT in v5:

| Helper | v5 Status | Location |
|---|---|---|
| toolMatchesName | ✓ PRESENT | registry.py:183-185 |
| findToolByName | ✓ PRESENT | registry.py:188-193 |
| filterToolsByDenyRules | ✓ PRESENT (with full MCP logic) | registry.py:200-238 |
| assembleToolPool | ✓ PRESENT | registry.py:264-306 |
| apply_tool_search_deferral | ✓ PRESENT | registry.py:313-370 |
| isDeferredTool | ✗ IMPLICIT (inline logic) | registry.py:358-368 |

**Notable:** v5's filterToolsByDenyRules has SUPERIOR MCP support (server-prefix wildcards) vs Runnable.

---

## Architecture Fit Verdict

### Pure Extensions (No Restructuring)
✓ Structured output retry counter (3-4 files)
✓ Permission denial tracking (wrappedCanUseTool wrapper)
✓ Stream event handling (new match case)
✓ Attachment message handling (new match case)
✓ System message handling (new match case)
✓ Error diagnostic tracking (new fields)
✓ Orphaned permission handler (one-time gate)

### Out-of-Scope Phase 8
✗ Microcompact / context collapse (Phase 11)
✗ Skill auto-trigger (Phase 10)
✗ Sub-agent fork (Phase 9)
✗ Thinking / adaptive config (Phase 11)
✗ Memory path injection (Phase 11)
✗ Coordinator context (Phase 9 coordinator-mode)

### Incompatible with v5 Model
✗ DeepImmutable PermissionContext (v5: simple bool+set)
✗ Interactive permission prompts (v5: .ipynb single-source)
✗ CLI/REPL command UI (Phase 11 responsibility)

---

## Action Items

**CRITICAL (Do Before Phase 8 Ships):**
1. Add `self._discovered_tool_names = set()` at start of run() — 1-line fix
2. Implement structured-output retry counter (countToolCalls, delta check, exit condition) — Medium effort

**RECOMMENDED (Phase 9+):**
3. Add wrappedCanUseTool permission denial tracking
4. Add orphaned permission handler (one-time gate)
5. Add error diagnostic tracking (result_type, content_type, errors[])

**OPTIONAL (Phase 11+):**
6. Stream event handling (if streaming enabled)
7. System message handling (compact/snip boundaries)
8. Attachment message handling (when Bedrock adds)

---

## Conclusion

v5's QueryEngine is **correctly scoped** for Phase 8. The 2 critical gaps (structured-output retry counter + discoveredSkillNames reset) are straightforward to fix. The remaining 6 features are pure additive extensions for Phase 9+. **No breaking changes required.**

**Recommendation:** Add the 2 critical fixes, merge Phase 8, backlog the 6 remaining features for later phases as needed.
