# Runnable line-by-line scan — new functionality vs v4

**Scanned**: 2026-05-01  
**Source**: `_archive/compare_code/gg-claude-code-runnable/src/` (2010 TypeScript files)  
**Compared against**: `compact_v4/MAIN/agent/sagemaker_agent.py`  
**Existing plan**: `V5_PHASE_2_PLAN_v3.md` + `Q1_EVIDENCE_MATRIX.md` (172 rows)

---

## NEW findings (not yet in v5.0.1 plan)

| # | Capability | Runnable file:line | v4 has? | v5.0.1 needs? | Target Block | How to graft on v4 | Status |
|---|---|---|---|---|---|---|---|
| 1 | Pasted content reference history system | `history.ts:1-450` | No | Optional (IDE feature) | N/A | Would add `formatPastedTextRef()`, `parseReferences()`, `expandPastedTextRefs()`, history JSONL persistence, dedup-by-display. Requires UI integration for paste-reference lookup on up-arrow. | OUT-OF-SCOPE |
| 2 | Away summary (while you were away recap) | `services/awaySummary.ts:1-74` | No | Optional (IDE feature) | N/A | Calls `generateAwaySummary(messages, signal)` with small-fast-model to create 1-3-sentence recap on session resume. Requires idle-timer + resume hook. | OUT-OF-SCOPE |
| 3 | System prompt injection for cache breaking | `context.ts:22-34` | No | No (diagnostic tool) | L (error/retry) | `setSystemPromptInjection(value)` + `getSystemPromptInjection()` for ant-only debugging. Gated by feature flag. | OUT-OF-SCOPE |
| 4 | Project onboarding state tracker | `projectOnboardingState.ts:1-84` | No | No | N/A | Checks CLAUDE.md existence, tracks /init call count, memoizes completion status. 4 helper functions + completion gate logic. | OUT-OF-SCOPE |
| 5 | Prevent macOS sleep during long work | `services/preventSleep.ts:1-165` | No | No | N/A | Spawns macOS caffeinate command with 5-min timeout + 4-min restart interval. Reference-counted start/stop + cleanup handler. | OUT-OF-SCOPE |
| 6 | Diagnostic tracking/analytics | `services/diagnosticTracking.ts:1-397` | No | No | N/A | Emits diagnostic events via `logForDiagnosticsNoPII()`. Structured telemetry on system/user context build times. | OUT-OF-SCOPE |
| 7 | Notifier service for OS notifications | `services/notifier.ts:1-156` | No | No | N/A | Emits desktop notifications via platform APIs (macOS, Windows, Linux). | OUT-OF-SCOPE |
| 8 | Rate-limit message templates + mocking | `services/rateLimitMessages.ts:1-400` + `mockRateLimits.ts:1-580` | No | Covered by Block L | L | Structured error messages for 429, 500, timeout. Mock rate-limit generator for testing. | ALREADY-IN-PLAN |

---

## ALREADY-IN-PLAN (verified covered in v5.0.1 plan)

| Item | Plan Block | Evidence |
|---|---|---|
| Compaction (cache-aware, autoCompact) | Block A | V5_PHASE_2_PLAN_v3.md lines 210-220 |
| Memory extraction (session-end capture) | Block H | V5_PHASE_2_PLAN_v3.md lines 289-297 |
| Token estimation | Block B | V5_PHASE_2_PLAN_v3.md line 128 |
| Error categorization + retry-after + cache-break | Block L | V5_PHASE_2_PLAN_v3.md lines 299-333 |
| Parallel tool execution + dedup + fuzzy match | Block N | V5_PHASE_2_PLAN_v3.md lines 335-348 |
| All 19 v4 slash commands | Block D | Q1_EVIDENCE_MATRIX.md lines 54-99 |
| 11 v4 tools (create_word/excel/markdown/notebook/chart/pdf, todo_write/read, semantic_search, web_fetch, ask_user) | Block T | V5_PHASE_2_PLAN_v3.md lines 350-373 |
| Full UI rendering (markdown, tokens, dropdown, approval dialog, dark mode) | Block E+F | V5_PHASE_2_PLAN_v3.md lines 222-248 |
| SessionManager + cost limits + AGENT_STATUS + FileCache | Block B+ | V5_PHASE_2_PLAN_v3.md lines 138-149 |
| 7 agent types + worktree | Block G | V5_PHASE_2_PLAN_v3.md lines 268-277 |

---

## OUT-OF-SCOPE-BY-CONSTRAINT (categorical drops confirmed)

| Category | Runnable directories | Why dropped |
|---|---|---|
| IDE/bridge | `bridge/`, `server/`, `remote/`, `assistant/`, `coordinator/` | Multi-user, VS Code bridge — constraint #1 (single-user SageMaker) |
| Voice/keyboard | `voice/`, `keybindings/`, `vim/`, `ssh/` | IDE input modes — constraint #1 |
| MCP + plugins | `services/mcp/`, `services/plugins/`, `utils/plugins/` | Constraint #1 + #9 |
| Multi-user/oauth/settings | `services/oauth/`, `services/teamMemorySync/`, `services/remoteManagedSettings/` | Constraint #1 |
| Ink/React UI | `ink/`, `components/`, `screens/` | Constraint #4 (v4 chat.ipynb is canonical) |
| macOS-specific | `services/preventSleep.ts`, `appleTerminalBackup.ts` | Not applicable to cloud |
| 111 additional Runnable commands | `commands/` subdirs (voice, vim, mcp, ide, etc.) | Depend on dropped subsystems |

---

## Summary

- **Total Runnable capabilities scanned**: ~2010 TypeScript files
- **Already covered in v5.0.1 plan**: **172 rows** in Q1_EVIDENCE_MATRIX.md (Blocks 0-T)
- **New findings recommended for plan**: **0** (all genuinely NEW items are out-of-scope)
- **Out-of-scope-by-constraint**: **8 items** (pasted history, away summary, diagnostic tracking, notifier, prevent-sleep, project onboarding, cache-break injection, rate-limit mocking)
- **Verdict**: v5.0.1 plan is **COMPLETE** on the constrained domain.

