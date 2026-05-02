# R12 — Bridge + Coordinator + Proactive + AutoDream + SessionTranscript line-by-line scan

**Scanned**: 2026-05-01
**Source root**: `D:/Github/sagemaker-coding-agent/_archive/compare_code/gg-claude-code-runnable/src/`
**Dirs covered**:
- `bridge/` (33 files, ~12,432 LOC, all real)
- `coordinator/` (2 files: `coordinatorMode.ts` 369 LOC real; `workerAgent.ts` 1 LOC stub)
- `proactive/` (2 files: `index.ts` 2 LOC stub; `useProactive.ts` 1 LOC stub)
- `services/autoDream/` (4 files, 551 LOC total, all real)
- `services/sessionTranscript/` (1 file: `sessionTranscript.ts` 1 LOC stub)

**Compared against**:
- v4 baseline: `compact_v4/MAIN/agent/sagemaker_agent.py`
- Plan v3: `compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md`
- Q1 matrix: `compact_v5/_phase_2/wave_4/Q1_EVIDENCE_MATRIX.md`

**Constraints applied**: v5.0.1 single-user SageMaker, Bedrock-only, v4 chat.ipynb canonical UI, NO DEFERRALS (must propose v5 placement now if in-scope).

---

## Method (executed)

1. Globbed each dir → enumerated all files.
2. Read every file. Stub files (≤2 LOC re-exporting `{}` or `export {}`) confirmed by direct read; real files (≥21 LOC) read line-by-line for capability extraction.
3. Categorized each capability against the 4 constraints.
4. Cross-checked Q1 matrix and Plan v3 for "already covered" status.

---

## Stub-confirmation table (no functionality present in this distribution)

| File | LOC | Body | Verdict |
|---|---|---|---|
| `coordinator/workerAgent.ts` | 1 | `export default {}` | STUB — feature-gated out of public dist |
| `proactive/index.ts` | 2 | `// Stub: proactive/index (PROACTIVE feature-gated)` + `export default {}` | STUB — proactive task-suggestion engine NOT in dist |
| `proactive/useProactive.ts` | 1 | `export default {}` | STUB — UI hook for proactive NOT in dist |
| `bridge/peerSessions.ts` | 1 | `export {}` | STUB — peer session feature-gated |
| `services/sessionTranscript/sessionTranscript.ts` | 1 | `export default {}` | STUB — transcript service NOT in dist |

**Implication**: The "proactive task suggestion engine" hypothesis from the prompt is NOT verifiable from this distribution — only the public stub remains. No code to graft. Zero in-scope nuggets from `proactive/`, `coordinator/workerAgent.ts`, `bridge/peerSessions.ts`, `services/sessionTranscript/`.

---

## NEW findings (not yet in v5.0.1 plan)

| # | Capability | Runnable file:line | v4 has? | v5.0.1 needs? | Target Block | How to graft on v4 | Status |
|---|---|---|---|---|---|---|---|
| 1 | **Background memory consolidation (autoDream)** — daemon that fires `/dream`-style consolidation as forked subagent on stop-hook when (a) hours since last ≥ minHours (default 24) AND (b) sessions touched since lastAt ≥ minSessions (default 5) AND (c) lock free. Three-gate cheapest-first ordering: time-stat → session-scan throttle (10 min) → lock acquire. PID + mtime lock at `<memdir>/.consolidate-lock` with stale guard (60 min). Forked agent runs read-only Bash + Edit/Write to `memdir/`, emits `Improved <files>` system message. Rollback rewinds mtime on failure. | `services/autoDream/autoDream.ts:1-324` + `consolidationLock.ts:1-140` + `consolidationPrompt.ts:1-65` + `config.ts:1-21` | NO — v4 has no background memory consolidation; only `_extract_and_append_memories` runs at session-end (Block H) | **YES** — fits "long/complex coding" Q3 axis (v5 must be better at long sessions); auto-dream pays down memory debt across sessions, making the next session orient faster. Aligns with Block H (memory) but is a SEPARATE trigger surface (post-stop-hook background, not session-end). **NO-DEFERRAL rule** (v5.0.1 = combine + better) requires it in v5.0.1, not v5.0.2. | **NEW** Block H+ (recommend) | Add `runtime/auto_dream.py` ≈350 LOC: (1) `init_auto_dream()` returns closure-scoped runner with `lastSessionScanAt`; (2) `read_last_consolidated_at()` stat on `<memdir>/.consolidate-lock` mtime; (3) `try_acquire_lock()` writes PID, verifies via re-read; (4) `rollback_lock(prior_mtime)` restores via `os.utime`; (5) `list_sessions_touched_since(since_ms)` scans transcript dir; (6) `build_consolidation_prompt(memory_root, transcript_dir, extra)` from `consolidationPrompt.ts` (Phase 1 Orient → Phase 2 Gather → Phase 3 Consolidate → Phase 4 Prune+Index); (7) `execute_auto_dream(context)` called from v4 stop-hook equivalent. Gate via `CONFIG.auto_dream_enabled` (settings) ∨ env `SAGEMAKER_AUTO_DREAM=1`. Forked agent uses BedrockClient with restricted tool set (`bash_read_only`, `file_edit`, `file_write` scoped to memdir). Tools-restriction string from `autoDream.ts:217` ("Bash is restricted to read-only commands…") goes in `extra` string (manual `/dream` skips it). | NEW-FINDING (in-scope) |
| 2 | **`/dream` slash command (manual consolidation trigger)** — same prompt body as auto-dream; uses `recordConsolidation()` to optimistically stamp the lock so auto-dream backs off | `services/autoDream/consolidationLock.ts:130-140` (`recordConsolidation`) + reused `consolidationPrompt.ts` | NO — v4's slash command set (Block D) does not include `/dream` | **YES** — natural pair with finding #1; gives the user manual override without spawning auto-dream's background fork timing logic | Block D (slash commands) | Add `/dream` to v4's command dispatcher (`sagemaker_agent.py:8164` advertised list). Handler calls `build_consolidation_prompt(memdir, transcript_dir, "")` → executes via main BedrockClient (not forked) with normal permissions, then calls `record_consolidation()` to stamp lock. ~30 LOC. | NEW-FINDING (in-scope, optional) |
| 3 | **Coordinator system prompt (multi-worker orchestration)** — 369 LOC system prompt teaching the coordinator how to: (a) spawn workers in parallel, (b) NEVER delegate understanding ("based on your findings…" anti-pattern), (c) continue vs spawn fresh decision table, (d) phases (Research → Synthesis YOU → Implementation → Verification), (e) `<task-notification>` XML protocol, (f) example sessions. Includes `getCoordinatorUserContext()` injecting worker tool list + scratchpad dir. Gated by `feature('COORDINATOR_MODE')` + env `CLAUDE_CODE_COORDINATOR_MODE`. | `coordinator/coordinatorMode.ts:1-369` | PARTIAL — v4 has multi-agent (parent + sub-agents via spawn_agent / send_message tools) but NO explicit coordinator-mode system prompt with parallel/serial guidance | **MIXED** — v5 plan Block G (7 agents + worktree) covers spawn mechanics, BUT the prompt-level guidance (synthesis-not-delegation, continue-vs-spawn table, parallel research / serial write rules) is NEW. **Q3 axis #2 "agent coordination"** demands v5 > v4 + Runnable on this; user `feedback_v5_better_definition.md` makes this binding. | Block G (existing) — augment | Extract the 369-LOC prompt body into `runtime/prompts/coordinator_prompt.py` and inject via v4's existing parent-agent system prompt path when `CONFIG.coordinator_mode_enabled`. The 6 sections (Role, Tools, Workers, Workflow, Writing Worker Prompts, Example) port verbatim with substitutions: `${AGENT_TOOL_NAME}` → `spawn_agent`, `${SEND_MESSAGE_TOOL_NAME}` → `send_message`, `${TASK_STOP_TOOL_NAME}` → `stop_agent` (v4 tool names). The continue-vs-spawn decision table (autoDream.ts:282-292) is the most valuable artifact — currently v4 has none. | NEW-FINDING (in-scope, augments existing Block G) |
| 4 | **Coordinator/Normal mode session resume parity** — when resuming a session, detect mode-mismatch, flip `CLAUDE_CODE_COORDINATOR_MODE` env var, log analytics, return user-visible message ("Entered/Exited coordinator mode to match resumed session") | `coordinator/coordinatorMode.ts:49-78` (`matchSessionMode`) | NO | NO — depends on session-mode persistence which v4 doesn't have at session level | N/A | Skip — not worth the session-format change for v5.0.1 | OUT-OF-SCOPE (no v4 analog) |

---

## ALREADY-IN-PLAN (verified covered in v5.0.1 plan)

| Item | Plan Block | Evidence |
|---|---|---|
| Spawn agent / send_message / stop_agent tools | Block G | Q1_EVIDENCE_MATRIX.md (Block T tools — v4 baseline parity) |
| Worktree-isolated sub-agents | Block G | V5_PHASE_2_PLAN_v3.md lines 268-277 |
| Memory extraction at session-end (NOT consolidation) | Block H | V5_PHASE_2_PLAN_v3.md line 293 (`extractMemories.ts` + `sessionMemory.ts` ported) |
| `/dream`-prompt content phases (the Phase-1-Orient/Phase-2-Gather/Phase-3-Consolidate/Phase-4-Prune-Index structure is NOT in plan — but the memory file format spec it relies on IS) | Block H | `memdir/memdir.js` constants `DIR_EXISTS_GUIDANCE`, `ENTRYPOINT_NAME`, `MAX_ENTRYPOINT_LINES` are in Block H's auto-memory port |

---

## OUT-OF-SCOPE-BY-CONSTRAINT (categorical drops with file-level evidence)

### bridge/ — entire directory

| File | LOC | What it does | Why dropped |
|---|---|---|---|
| `bridgeApi.ts` | 539 | HTTP client for claude.ai CCR (Claude Code Remote) — registerEnvironment, pollForWork, acknowledgeWork, stopWork, deregisterEnvironment, sendPermissionResponseEvent, archiveSession, reconnectSession, heartbeatWork | Constraint #1: single-user SageMaker (no claude.ai backend, no OAuth, no remote env) |
| `bridgeConfig.ts` | 48 | OAuth token + base URL resolution for CCR with `CLAUDE_BRIDGE_*` ant-only env overrides | Constraint #1 |
| `bridgeDebug.ts` | 135 | Fault injection for testing bridge transport | Constraint #1 |
| `bridgeEnabled.ts` | 202 | Entitlement check: `isClaudeAISubscriber()` + `tengu_ccr_bridge` GrowthBook gate; `getBridgeDisabledReason()` returns user-facing error strings | Constraint #1 (no claude.ai subscription model, no GrowthBook) |
| `bridgeMain.ts` | 2999 | Top-level bridge daemon: registers environment, polls for work, spawns child claude CLI per session, multi-session/worktree spawn modes, capacity-wake, JWT refresh scheduler, status UI | Constraint #1 (multi-user IDE bridge); chat.ipynb is the only UI (constraint #4) |
| `bridgeMessaging.ts` | 461 | Ingress message handling, control_request/response routing, session-scoped UUID dedup | Constraint #1 |
| `bridgePermissionCallbacks.ts` | 43 | Permission decision routing back to server | Constraint #1 (v4 has local PermissionDialog — Block C+) |
| `bridgePointer.ts` | 210 | Singleton pointer to active bridge handle | Constraint #1 |
| `bridgeStatusUtil.ts` | 163 | Duration formatting for status display | Constraint #1 + #4 (chat.ipynb UI) |
| `bridgeUI.ts` | 530 | Ink-based status display: banner, session list, idle/reconnecting/failed states, QR toggle, multi-session activity | Constraint #4 (Ink UI replaced by chat.ipynb); also Constraint #1 |
| `capacityWake.ts` | 56 | Signal that bridge has spawn capacity (multi-session mode) | Constraint #1 |
| `codeSessionApi.ts` | 168 | Direct claude.ai code-session API client | Constraint #1 |
| `createSession.ts` | 384 | Spawn a new bridge session (worktree creation, env-var setup, child CLI spawn) | Constraint #1 |
| `debugUtils.ts` | 141 | Bridge axios error formatting | Constraint #1 |
| `envLessBridgeConfig.ts` | 165 | v2 env-less bridge config (newer transport) | Constraint #1 |
| `flushGate.ts` | 71 | Coordinate flush of buffered messages on bridge close | Constraint #1 |
| `inboundAttachments.ts` | 175 | Receive file attachments from claude.ai web | Constraint #1 (no web UI) |
| `inboundMessages.ts` | 80 | Decode inbound bridge messages | Constraint #1 |
| `initReplBridge.ts` | 569 | Wire REPL ↔ bridge, dispatch to v1 or v2 transport | Constraint #1 |
| `jwtUtils.ts` | 256 | JWT decode + refresh scheduler with 5-min lookahead | Constraint #1 |
| `pollConfig.ts` + `pollConfigDefaults.ts` | 110+82 | Bridge polling intervals from GrowthBook | Constraint #1 |
| `remoteBridgeCore.ts` | 1008 | Top-level orchestrator for `claude remote-control` daemon | Constraint #1 |
| `replBridge.ts` | 2406 | REPL ↔ bridge message router with HybridTransport, v1/v2 transport selection, control_request handling, capacity wake, flush gate | Constraint #1 |
| `replBridgeHandle.ts` + `replBridgeTransport.ts` | 36+370 | REPL bridge interface types | Constraint #1 |
| `sessionIdCompat.ts` | 57 | `cse_*` ↔ `session_*` ID retag shim for backend compat | Constraint #1 |
| `sessionRunner.ts` | 550 | Spawn child claude CLI as subprocess (control_request decode, activity ring buffer, stdout/stderr capture) | Constraint #1 (no child CLI in SageMaker — v4 runs in-process) |
| `trustedDevice.ts` | 210 | Trusted-device JWT for bridge auth | Constraint #1 |
| `types.ts` | 262 | Bridge type definitions (BridgeConfig, SessionHandle, SessionSpawner, BridgeLogger, etc.) | Constraint #1 |
| `workSecret.ts` | 127 | base64url-encoded WorkSecret decode + SDK URL construction | Constraint #1 |

**Bridge total dropped**: 33 files, ~12,432 LOC. Verdict: **0 in-scope nuggets** from `bridge/` — entire subsystem is the claude.ai Remote Control IDE feature (multi-user, web-driven, child-CLI spawn). Confirms wave_5 categorical drop ("IDE/bridge" row).

### coordinator/workerAgent.ts — STUB

Already shown stub (1 LOC). Verdict: nothing to extract.

### proactive/ — both STUBS

`index.ts` is 2 LOC with comment `// Stub: proactive/index (PROACTIVE feature-gated)`. The proactive task-suggestion engine is NOT shipped in this distribution. Verdict: **the prompt's hypothesis "proactive may have a suggestion engine v5 should adopt" cannot be tested from this dist** — only stubs remain.

### services/sessionTranscript/sessionTranscript.ts — STUB

1 LOC. Verdict: nothing to extract. (Note: actual transcript reading IS done by `services/autoDream/consolidationLock.ts` via `listCandidates(dir, true)` from `utils/listSessionsImpl.js` — that path is in scope as part of finding #1.)

---

## Plan-update recommendations (NEW additions to v5.0.1 — NO DEFERRALS)

### Recommendation R12-1: Add Block H+ (Auto-Dream) to V5_PHASE_2_PLAN_v3.md

**Block H+ — Background Memory Consolidation** (~350 LOC, NEW-IN-V5 + PORTED-FROM-RUNNABLE)

| Item | Source | Spec |
|---|---|---|
| `runtime/auto_dream.py` | NEW | Top-level module: `init_auto_dream()`, `execute_auto_dream(context)`, `_run_auto_dream()` closure-scoped |
| Lock subsystem | Runnable: `services/autoDream/consolidationLock.ts:1-140` | `read_last_consolidated_at()`, `try_acquire_consolidation_lock()`, `rollback_consolidation_lock(prior)`, `list_sessions_touched_since(since_ms)`, `record_consolidation()` |
| Consolidation prompt | Runnable: `services/autoDream/consolidationPrompt.ts:1-65` | `build_consolidation_prompt(memory_root, transcript_dir, extra)` returning the 4-phase Orient/Gather/Consolidate/Prune-Index prompt |
| Config | Runnable: `services/autoDream/config.ts:1-21` | `is_auto_dream_enabled()` reads `CONFIG.auto_dream_enabled` (default False); env override `SAGEMAKER_AUTO_DREAM` |
| Stop-hook integration | Runnable: `autoDream.ts:319-324` | Call `execute_auto_dream(context)` from v4's stop-hook equivalent (last line of `chat.ipynb` turn loop) |
| Forked agent | Runnable: `autoDream.ts:224-233` | Reuse v4's parent BedrockClient.fork pattern; tool set restricted to `bash_read_only` + `file_edit`/`file_write` scoped to memdir |
| Acceptance test | NEW | (1) Set `CONFIG.auto_dream_enabled=True`, `min_hours=0`, `min_sessions=1`. (2) Touch 2 sessions → trigger stop hook. (3) Assert lock-file mtime advanced AND `<memdir>/INDEX.md` updated AND `Improved <files>` system message appended. (4) Run again immediately → assert throttle (no second fire). |

**LOC**: ~350. **Q3 axis fit**: long/complex coding (axis 7) — pays down memory debt automatically across sessions.

### Recommendation R12-2: Add `/dream` to Block D slash commands

`/dream` (manual consolidation trigger) — handler calls `build_consolidation_prompt(memdir, transcript_dir, "")` → main BedrockClient with normal permissions → `record_consolidation()` stamps lock to suppress next auto-fire. ~30 LOC, fits Block D's existing dispatcher.

### Recommendation R12-3: Add coordinator system prompt to Block G

Extract `coordinator/coordinatorMode.ts:111-369` (the 258-LOC system prompt body inside `getCoordinatorSystemPrompt()`) into `runtime/prompts/coordinator_prompt.py`. When `CONFIG.coordinator_mode_enabled=True` (default False), prepend to v4's parent-agent system prompt. Substitute Runnable tool names with v4 names (`AgentTool` → `spawn_agent`, `SendMessageTool` → `send_message`, `TaskStopTool` → `stop_agent`). ~270 LOC. **Q3 axis fit**: agent coordination (axis 2) — gives v5 explicit guidance v4 lacks (synthesize-don't-delegate, continue-vs-spawn decision table, parallel/serial concurrency rules).

---

## Summary

| Metric | Count |
|---|---|
| Files scanned | 42 (33 bridge + 2 coordinator + 2 proactive + 4 autoDream + 1 sessionTranscript) |
| Real files (≥21 LOC) | 37 |
| Stub files | 5 (`coordinator/workerAgent.ts`, `proactive/index.ts`, `proactive/useProactive.ts`, `bridge/peerSessions.ts`, `services/sessionTranscript/sessionTranscript.ts`) |
| Total LOC scanned | ~13,392 |
| **NEW findings recommended for v5.0.1 plan** | **3** (auto-dream Block H+, `/dream` command, coordinator system prompt) |
| Already-in-plan items confirmed | 4 (spawn/send/stop tools, worktree, extractMemories+sessionMemory, memdir constants) |
| Out-of-scope-by-constraint | bridge/ (33 files, 12,432 LOC) + 5 stubs |
| Bridge LOC dropped | 12,432 (entire directory — claude.ai Remote Control IDE feature) |

**Key points**:
1. The prompt's hypothesis "proactive/ may have a suggestion engine v5 should adopt" is **NOT testable** — `proactive/` ships only as a feature-gated stub in this distribution.
2. The prompt's hypothesis "autoDream/ may have in-scope nuggets" is **CONFIRMED** — autoDream is the strongest in-scope finding in this entire scan. It's a 551-LOC working background memory consolidator that v4 lacks. Recommended Block H+.
3. Bridge is fully out of scope as expected (multi-user, claude.ai-driven, child-CLI subprocess spawn) — categorical drop confirmed line-by-line.
4. Coordinator has 1 stub (`workerAgent.ts`) but the real win is `coordinatorMode.ts`'s 258-LOC system prompt — currently missing from plan despite Block G covering spawn mechanics. Recommended augment.
5. `sessionTranscript.ts` is a stub; actual transcript scanning lives in autoDream's lock subsystem (covered by R12-1).

**No-deferrals compliance**: All 3 NEW findings are in-scope under constraints #1-#9 and Q3 axes (long-coding, agent-coordination, memory). They MUST land in v5.0.1, not v5.0.2. R12-1 and R12-3 are the most consequential.
