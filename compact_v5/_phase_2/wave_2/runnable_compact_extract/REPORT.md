# Wave 2 — Runnable context-management services (compact, extract, summary, sessionMemory)

## All 5 services MISSING in v5

### COMPACT SERVICE (16 files, ~2000+ LOC)
- `compact.ts` (1706 LOC): Main orchestrator. Streaming API calls, prompt cache sharing, PTL retry logic, post-compact attachments (files, plans, skills, agents).
- `autoCompact.ts` (352 LOC): Auto-trigger with consecutive-failure circuit breaker, token thresholds, effective-window calc.
- `microCompact.ts` (531 LOC): Two-tier — time-based clearing (idle >N min) + cached MC with cache_edits API.
- `reactiveCompact.ts`: PTL-driven (referenced; files empty).
- v5 status: ZERO. Port effort: HIGH (1000+ LOC core). Architecture fit: new `services/compact/`, integration with QueryEngine.run() ~line 250-350.

### TOKEN ESTIMATION SERVICE
- `tokenEstimation.ts` (~150 LOC): `roughTokenCountEstimation()`, API token counting, thinking/tool_reference block handling.
- `apiMicrocompact.ts` (~100 LOC): Native API context_management strategies (clear_thinking, clear_tool_uses).
- v5 status: MISSING. Port effort: MEDIUM (200 LOC). Architecture fit: pure utility, no state.

### EXTRACT MEMORIES SERVICE
- `extractMemories.ts` (616 LOC): Forked subagent reads conversation + writes to memory dir.
- Gate: feature flag `tengu_passport_quail`, post-sampling hook trigger.
- Closure-scoped state: cursor, in-flight tracking, coalesced calls.
- Throttle: configurable turn frequency (`tengu_bramble_lintel`).
- v5 status: MISSING. Port effort: MEDIUM. Architecture fit: standalone, no QueryEngine coupling.

### SESSION MEMORY SERVICE
- `sessionMemory.ts` (496 LOC): Periodic ~30s background markdown notes extraction.
- Cached config: `tengu_sm_config` (minimumTokensBetweenUpdate, toolCallsBetweenUpdates).
- Post-sampling hook + manual `/summary` command trigger.
- State: `lastMemoryMessageUuid`, extraction in-progress flag.
- v5 status: MISSING. Port effort: MEDIUM. Architecture fit: standalone hook, light coupling.

### AGENT SUMMARY SERVICE
- `agentSummary.ts` (180 LOC): 30s timer → forked agent → 3-5 word progress summary for UI.
- Used in coordinator mode for sub-agent tracking.
- v5 status: MISSING. Port effort: LOW (isolated). Architecture fit: tight coupling with LocalAgentTask.

### CONTEXT COLLAPSE SERVICE
- index.ts, operations.ts are EMPTY STUBS (export {}).
- Not implemented in Runnable; deprecated. (v4 has its own context_collapse — port v4's instead.)

## Recommendations

| Service | Port Decision | Reasoning |
|---|---|---|
| Compact | **Runnable verbatim** | 1706 LOC; complex state, tengu events, cache-aware. Supersedes v4's older Compactor. |
| MicroCompact | **Runnable verbatim** | Native cache_edits API + time-based trigger. v5-aligned. |
| TokenEstimation | **Runnable verbatim** | Pure utility; latest block types (thinking, redacted_thinking). |
| ExtractMemories | **Runnable verbatim** | Closure-scoped, minimal coupling, feature-gated. |
| SessionMemory | **Runnable verbatim** | Gate + tengu_sm_config production-ready. /summary clear integration. |
| AgentSummary | **Port + adapt** | Foundation from Runnable; v5 task API may differ from LocalAgentTask. |
| ContextCollapse | **Port v4** (Runnable empty) | v4 has the working code. |

## v5.0.1 integration points

1. Wire `autoCompact()` into QueryEngine.run() ~line 250 (pre-response check).
2. Wire `microcompactMessages()` in pre-API path (~line 180).
3. Register post-sampling hooks for `extractMemories`, `sessionMemory` in init().
4. Add `tokenEstimation.ts` to `services/` as pure utility.
5. Thread `RecompactionInfo` through for analytics alignment.

Estimated **~500 LOC of v5 glue** plus the port volumes.
