# R3 — Runnable tools/ S–Z Slice (Exhaustive Line-by-Line Scan)

**Date**: 2026-05-01
**Slice**: 22 tool dirs (S–Z) + `shared/` + `testing/` + tools/`utils.ts`
**Source root**: `D:/Github/sagemaker-coding-agent/_archive/compare_code/gg-claude-code-runnable/src/tools/`
**Compared against**:
- v4 baseline: `compact_v4/MAIN/agent/sagemaker_agent.py` (12,088 LOC)
- Existing plan: `compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md`
- Existing port log: `compact_v5/_phase_2/wave_4/Q1_EVIDENCE_MATRIX.md`

**v5.0.1 constraints applied**: single-user SageMaker, Bedrock-only (no external network beyond v4's `web_fetch`), v4 chat.ipynb canonical UI, no deferrals.

---

## Inventory

| # | Tool dir | Files | Total bytes | Real / Stub | Notes |
|---|---|---|---|---|---|
| 1 | `SleepTool/` | `SleepTool.ts` (19 B), `prompt.ts` (791 B) | 810 | **STUB-EXEC + REAL-PROMPT** | Body is `export default {}`, but `prompt.ts` is a real 791-byte prompt re-exporting `SLEEP_TOOL_PROMPT`/`DESCRIPTION`/`SLEEP_TOOL_NAME='Sleep'`. Mentions `<TICK_TAG>` periodic check-in prompts and prompt-cache 5-min expiry tradeoff. |
| 2 | `SnipTool/` | `SnipTool.ts` (19 B), `prompt.ts` (19 B) | 38 | **STUB** | Both `export default {}` / `export default ''`. No content. |
| 3 | `SubscribePRTool/` | `SubscribePRTool.ts` (19 B) | 19 | **STUB** | `export default {}`. |
| 4 | `SuggestBackgroundPRTool/` | `SuggestBackgroundPRTool.ts` (19 B) | 19 | **STUB** | `export default {}`. |
| 5 | `SyntheticOutputTool/` | `SyntheticOutputTool.ts` (5,631 B) | 5,631 | **REAL** | Full impl: dynamic Ajv JSON-schema-validated structured output. WeakMap identity cache. SDK/non-interactive only (`isSyntheticOutputToolEnabled = isNonInteractiveSession`). Tool name: `StructuredOutput`. |
| 6 | `TaskCreateTool/` | `TaskCreateTool.ts` (3,579 B), `prompt.ts` (2,816 B), `constants.ts` (51 B) | 6,446 | **REAL** | Strict zod schema (`subject`, `description`, `activeForm`, `metadata`). Calls `executeTaskCreatedHooks`, deletes task on blocking-error. Auto-expands tasks panel. Gated by `isTodoV2Enabled()`. Prompt switches teammate-mode via `isAgentSwarmsEnabled()`. |
| 7 | `TaskGetTool/` | `TaskGetTool.ts` (3,009 B), `prompt.ts` (847 B), `constants.ts` (45 B) | 3,901 | **REAL** | `taskId → {subject, description, status, blocks, blockedBy}`. Read-only. Concurrency-safe. Renders `Task #id: subject \n Status: x \n Description: y \n Blocked by: #a, #b \n Blocks: #c`. |
| 8 | `TaskListTool/` | `TaskListTool.ts` (2,919 B), `prompt.ts` (2,115 B), `constants.ts` (47 B) | 5,081 | **REAL** | Empty input. Filters `metadata._internal`. Drops `blockedBy` ids that already resolved. Renders `#id [status] subject (owner) [blocked by ...]`. |
| 9 | `TaskOutputTool/` | `TaskOutputTool.tsx` (67,151 B), `constants.ts` (51 B) | 67,202 | **REAL** | Replaces deprecated `AgentOutputTool` + `BashOutputTool` (aliases kept). Unified output for `local_bash` / `local_agent` / `remote_agent`. Polls every 100 ms, abort-aware, blocking + non-blocking modes, max-timeout 600 s default 30 s. Big chunk of file is the React result-display (`TaskOutputResultDisplay`) compiled by `react/compiler-runtime` with embedded sourceMap. **Description steers the model to read the output FILE PATH directly via `Read` instead** — Runnable explicitly deprecates polling. |
| 10 | `TaskStopTool/` | `TaskStopTool.ts` (4,066 B), `UI.tsx` (5,712 B with embedded sourceMap), `prompt.ts` (288 B) | 10,066 | **REAL** | Stops a running background task. Aliases: `KillShell` (back-compat). `validateInput` checks task exists and `status === 'running'`. Renders `<command>… · stopped`. |
| 11 | `TaskUpdateTool/` | `TaskUpdateTool.ts` (12,567 B), `prompt.ts` (2,452 B), `constants.ts` (51 B) | 15,070 | **REAL** | Status workflow (`pending → in_progress → completed` + special `deleted`). Auto-sets owner when teammate goes `in_progress` w/o owner. Mailbox notification on owner-change. Runs `executeTaskCompletedHooks` (blocks completion if hook returns blockingError). Verification nudge ON when `feature('VERIFICATION_AGENT')` + growthbook flag + main-thread + 3+ tasks closed without "verif" in subject. |
| 12 | `TeamCreateTool/` | `TeamCreateTool.ts` (7,905 B), `UI.tsx` (1,043 B with sourceMap), `prompt.ts` (7,013 B), `constants.ts` (51 B) | 16,012 | **REAL** | Single team per leader. Creates `~/.claude/teams/<name>/config.json` + `~/.claude/tasks/<name>/`. Generates word-slug if name collides. Auto-registers session-cleanup hook. `isAgentSwarmsEnabled()` gate. |
| 13 | `TeamDeleteTool/` | `TeamDeleteTool.ts` (4,360 B), `UI.tsx` (2,925 B), `prompt.ts` (700 B), `constants.ts` (51 B) | 8,036 | **REAL** | Refuses delete if active members (members with `isActive !== false` excluding lead). Calls `cleanupTeamDirectories`, clears teammate colors, clears leader-team-name (resets `getTaskListId()` fallback to session-id). |
| 14 | `TerminalCaptureTool/` | `TerminalCaptureTool.ts` (19 B), `prompt.ts` (19 B) | 38 | **STUB** | Both `export default {}` / `''`. |
| 15 | `TodoWriteTool/` | `TodoWriteTool.ts` (3,996 B), `prompt.ts` (9,711 B), `constants.ts` (49 B) | 13,756 | **REAL** | Single-call replace of the per-session todo list. Verification nudge mirrors TaskUpdate (3+ done + no "verif" + main-thread). Empty list when all done. Disabled when `isTodoV2Enabled()` (Task* tools take over). |
| 16 | `ToolSearchTool/` | `ToolSearchTool.ts` (14,746 B), `prompt.ts` (5,348 B), `constants.ts` (51 B) | 20,145 | **REAL** | Deferred-tool loader. Two query forms: `select:Name1,Name2` and free-text keyword (`+required` term, MCP-aware scoring 12/10/6/5/4/3/2). Memoized tool-prompt cache invalidated when deferred-tool set changes. Returns `tool_reference` blocks (Bedrock may not support → text fallback). Only ToolSearch + Brief + SendUserFile + (when feature on) Agent are NEVER deferred — every MCP tool is. |
| 17 | `TungstenTool/` | `TungstenTool.ts` (100 B), `TungstenLiveMonitor.tsx` (90 B) | 190 | **STUB** | `TungstenTool = {}`, `TungstenLiveMonitor` returns `null`. Comment says "feature-gated". |
| 18 | `VerifyPlanExecutionTool/` | `VerifyPlanExecutionTool.ts` (19 B), `constants.ts` (33 B) | 52 | **STUB** | Body `export default {}`, `TOOL_NAME = 'stub'`. |
| 19 | `WebBrowserTool/` | `WebBrowserTool.ts` (19 B), `WebBrowserPanel.tsx` (86 B) | 105 | **STUB** | Body `export default {}`, panel returns `null`. |
| 20 | `WebFetchTool/` | `WebFetchTool.ts` (9,642 B), `UI.tsx` (8,154 B), `preapproved.ts` (5,414 B), `prompt.ts` (2,246 B), `utils.ts` (17,291 B) | 42,747 | **REAL** | Big tool. Domain-blocklist preflight (`api.anthropic.com/api/web/domain_info`), 92-host preapproved list, redirect policy (same-host-or-www-toggle only, max 10 hops), 15-min URL-keyed LRU cache (50 MB) + 5-min hostname domain-check cache, HTML→markdown via lazy-loaded Turndown, 100 KB MAX_MARKDOWN_LENGTH, 10 MB MAX_HTTP_CONTENT_LENGTH, 60 s fetch timeout. Binary content (PDF/etc.) persisted to disk + Haiku summarized. Returns redirect-info to model when redirect crosses host boundary. Per-domain permission rules (`domain:hostname`). EgressBlockedError + DomainBlockedError + DomainCheckFailedError separately surfaced. |
| 21 | `WebSearchTool/` | `WebSearchTool.ts` (13,983 B), `UI.tsx` (12,260 B), `prompt.ts` (1,579 B) | 27,822 | **REAL** | Wraps Anthropic-server-side `web_search_20250305` beta tool. `max_uses: 8` per call. Streams `server_tool_use` + `web_search_tool_result` blocks, accumulates content, emits progress per query (regex-extracts query from partial-JSON deltas). `useHaiku` Growthbook flag forces small/fast model + `tool_choice: web_search`. Provider-gated: enabled on `firstParty`, `vertex` Claude 4.x, `foundry`. `Sources:` markdown-link reminder appended to result. |
| 22 | `WorkflowTool/` | `WorkflowTool.ts` (19 B), `WorkflowPermissionRequest.tsx` (96 B), `createWorkflowCommand.ts` (19 B), `bundled/index.ts` (19 B), `constants.ts` (91 B) | 244 | **STUB** | All `export default {}` / `null`. Constants kept (`TOOL_NAME = 'WorkflowTool'`). |
| — | `shared/` | `gitOperationTracking.ts` (9,762 B), `spawnMultiAgent.ts` (36,646 B) | 46,408 | **REAL** | `gitOperationTracking.ts`: shell-agnostic regex over BashTool stdout/stderr to detect git commit/push/cherry-pick/merge/rebase + `gh pr create/edit/merge/comment/close/ready` + `glab mr create` + `curl POST /pulls` → fires OTLP counters and analytics events; auto-links session→PR via `linkSessionToPR`. `spawnMultiAgent.ts`: extracted from TeammateTool, shared between `AgentTool` + `TeamCreateTool` for in-process / tmux / iTerm2 spawn paths (`getDefaultTeammateModel` + `resolveTeammateModel('inherit')` + backend detection + paneborder). |
| — | `testing/` | `TestingPermissionTool.tsx` (7,385 B with sourceMap) | 7,385 | **REAL** | Test-only tool. `isEnabled()` checks `process.env.NODE_ENV === 'test'` (literal `"production" === 'test'` → always false in shipped build). Always returns `behavior: 'ask'`. Dev-only. |
| — | `tools/utils.ts` | (1,178 B) | 1,178 | **REAL** | `tagMessagesWithToolUseID` (sourceToolUseID stamping) + `getToolUseIDFromParentMessage`. Used by Agent/Tasks. |

**Slice byte total**: ~ 298 KB across 22 tool dirs + shared + testing + utils. **STUB count: 7 of 22 dirs (32 %)** — Snip, SubscribePR, SuggestBackgroundPR, TerminalCapture, Tungsten, VerifyPlanExecution, WebBrowser, Workflow — ship as `export default {}`. **Real-content count: 15 of 22 (68 %)**, plus shared+testing+utils.

---

## Per-tool v5.0.1 mapping

Legend:
- `PORTED-FROM-v4` — already in v4 baseline (constraint #1).
- `PORTED-FROM-RUNNABLE` — net-new from Runnable, must be added to v5.0.1 (no defer).
- `PORTED-FROM-RUNNABLE-IDEA` — concept ported, implementation re-shaped for Bedrock single-user.
- `OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP)` — explicitly rejected by single-user SageMaker / Bedrock-only / canonical-plan drops, with reason.
- `RUNNABLE-STUB` — file is `export default {}` / `''` in Runnable too; nothing to port.

| # | Tool | v4 source line | v5.0.1 status | Disposition / placement | Reason |
|---|---|---|---|---|---|
| 1 | `SleepTool` (Runnable, prompt-only) | none | **OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP)** | n/a | Runnable's Sleep idle-loop pattern depends on `<TICK_TAG>` periodic-check-in pump and 5-min prompt-cache TTL — both are Runnable harness features absent in v4 chat.ipynb canonical UI (constraint #2). Single-user SageMaker has no idle-pump scheduler. v4 has no equivalent because the chat-loop is single-shot per user message. |
| 2 | `SnipTool` | n/a | **RUNNABLE-STUB** | n/a | Body and prompt are 19-byte `export default {}` / `''`. Nothing to port. (v4 already auto-compacts at 80% / 90% — see sagemaker_agent.py:21,22,9,187 — that covers the only real "snip" need.) |
| 3 | `SubscribePRTool` | n/a | **RUNNABLE-STUB** + **OUT-OF-SCOPE-BY-CONSTRAINT** | n/a | Stub. Even if real: GitHub-PR notification is multi-user developer-flow, ruled out by single-user SageMaker (no GitHub network egress). |
| 4 | `SuggestBackgroundPRTool` | n/a | **RUNNABLE-STUB** + **OUT-OF-SCOPE-BY-CONSTRAINT** | n/a | Same as #3. |
| 5 | `SyntheticOutputTool` (`StructuredOutput`) | none | **OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP)** | n/a | Gated by `isNonInteractiveSession` (Runnable SDK `query()` API). v5 chat.ipynb is interactive-only — there is no SDK call path that requests structured output with a JSON schema. Re-shaping it would invent a schema-validated tool nobody calls. (If single-user SageMaker ever gains an SDK harness, this is the first thing to port — Ajv WeakMap identity-cache pattern is reusable.) |
| 6 | `TaskCreateTool` | none (v4 has `todo_write` only — see :6854, :7310) | **OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP)** | n/a | Runnable's TaskV2 is gated by `isTodoV2Enabled()` — a Runnable-only feature flag for the multi-agent swarm task-list (`TaskCreate`/`TaskGet`/`TaskList`/`TaskUpdate`/`TaskOutput`/`TaskStop`). Replaces TodoWriteTool when on. v4 ships TodoWriteTool only (constraint #1 = v4 baseline). v5.0.1 keeps `todo_write` (constraint #1) — adding TaskV2 would duplicate state and break canonical-plan drops (`utils/swarm/`, `tasks/RemoteAgentTask/`, `tasks/InProcessTeammateTask/`, mailbox, teamHelpers — all in canonical drops list). **Verification nudge logic IS already ported** (see Q1 row :6872 in `sagemaker_agent.py` → comment "Mirrors Runnable's TodoWriteTool.ts:104-107 verification nudge"). |
| 7 | `TaskGetTool` | none | **OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP)** | n/a | Same as #6 (TaskV2 family). |
| 8 | `TaskListTool` | none | **OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP)** | n/a | Same as #6. |
| 9 | `TaskOutputTool` | none (v4 has no async-task framework — `task` tool runs sub-agent inline, see :7348) | **OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP)** | n/a | Runnable's TaskV2 + LocalShellTask + LocalAgentTask + RemoteAgentTask is a background-task scheduler. v4 sub-agents run synchronously in the same Bedrock session (no async polling). Single-user SageMaker has no `tmux`/iTerm2/IDE-pane substrate the RemoteAgentTask depends on. The "deprecated polling — Read the file path instead" guidance (TaskOutputTool prompt) is already aligned with v4 behavior (sub-agent returns its result string directly to the parent turn). |
| 10 | `TaskStopTool` | none | **OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP)** | n/a | No background task framework in v4 — nothing to stop. v4 has `stop_button` for the chat-level interrupt (sagemaker_agent.py: stop/abort handler at :9448) — already covered in Q1 PORT_LOG Block C+ row "stop/abort" :9448. |
| 11 | `TaskUpdateTool` | none | **OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP)** | n/a | Same as #6. **One concept to fold into v5 `tool_todo_write`**: TaskUpdateTool's hook-blocked-completion gate (`executeTaskCompletedHooks` → if blockingError, refuse `completed`). v4 doesn't have this. Rejected for v5.0.1 because v4 has no `task_completed` hook framework (constraint #1). |
| 12 | `TeamCreateTool` | none | **OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP)** | n/a | Multi-agent swarm with tmux/iTerm2 panes and inter-agent mailboxes. Single-user SageMaker has none of these substrates. Listed under canonical-plan drops (`utils/swarm/`). |
| 13 | `TeamDeleteTool` | none | **OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP)** | n/a | Same as #12. |
| 14 | `TerminalCaptureTool` | n/a | **RUNNABLE-STUB** | n/a | Stub. (Even real impl would be IDE-pane terminal capture — out-of-scope.) |
| 15 | `TodoWriteTool` | v4: `tool_todo_write` :6854-:6884, schema :7310-:7311; `tool_todo_read` :6887-:6895, schema :7313-:7314; `_TODOS` global :3763, sync :3763, post-compact restoration `build_todo_restoration_message` :651-:683, `PROTECTED_TOOLS` :194; verification nudge :6872-:6882 | **PORTED-FROM-v4** (already in baseline) | place in `tools/todo_write.py` per `V5_PHASE_2_PLAN_v3.md:361` (T1100 row at :425) | Constraint #1 (v4.10.10 baseline). Plan v3 already lists `tools/todo_write.py` as a v4 tool surface parity gap to close. **No v5 enhancement needed from Runnable beyond what v4 already merged** (verification-nudge match-up at :6872 already cites Runnable line ranges). |
| 16 | `ToolSearchTool` | none in v4 — v4 ships ALL tools eagerly (CONFIG.tools dict in `_TOOL_REGISTRY` at sagemaker_agent.py:7270+; no deferral) | **OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP)** | n/a | v4 ships ~30 tools eagerly to Bedrock — the prompt-bloat budget is fine for that count (no MCP, no swarm tools). Runnable's ToolSearch is needed when N grows past ~50 (full deferral becomes tokens-back). v5.0.1 keeps v4's tool surface (~30 — see V5_PHASE_2_PLAN_v3.md:425 T1100 + slash commands), so deferred loading is not a token-budget win. **Concept worth recording for v5.x**: if v5 ever adds MCP / Skills / Workflows that 5x the tool count, ToolSearch's `select:` + keyword path is the right pattern to adopt. (Runnable line refs preserved here for that day: `ToolSearchTool.ts:186-302` keyword scoring, `prompt.ts:62-108` `isDeferredTool`, `MAX_RESULTS=5` default.) |
| 17 | `TungstenTool` | n/a | **RUNNABLE-STUB** | n/a | Stub + comment "feature-gated". |
| 18 | `VerifyPlanExecutionTool` | n/a | **RUNNABLE-STUB** | n/a | Stub. (Concept = check that plan execution matches plan output. Already covered by v4 `/verify` slash + verify-skill — see Q1 Block D :11095 row.) |
| 19 | `WebBrowserTool` | n/a | **RUNNABLE-STUB** + **OUT-OF-SCOPE-BY-CONSTRAINT** | n/a | Stub + Bedrock-only constraint disallows external browser headless dependency (Playwright/Chromium not installed in SageMaker insurance images). |
| 20 | `WebFetchTool` | v4: `tool_web_fetch` :6787-:6829 + redirect-blocker `_NoRedirectHandler` :6779-:6781 + `_WEB_FETCH_MAX_BYTES = 2 MB` :6784 + private-IP block `_is_private_ip` (caller :6803) + Docker-mode network-disabled gate :6796 + 20 s timeout :6815 + HTML-strip :6828; schema :7390-:7393; HIGH_RISK_TOOLS membership :8043 | **PORTED-FROM-v4** | place in `tools/web_fetch.py` per `V5_PHASE_2_PLAN_v3.md:364, :425` | Constraint #1. **Runnable enhancements to fold into v5 (no defer)**: (a) **15-min URL LRU cache** (Runnable `utils.ts:63-69`, `MAX_CACHE_SIZE_BYTES = 50 MB`) — pure local optimisation, no extra network; eliminates duplicate fetch in same session. (b) **Same-host redirect with strip-www tolerance** (Runnable `utils.ts:212-243`, `MAX_REDIRECTS = 10`) — v4's `_NoRedirectHandler` is harder than this (blocks ALL redirects); same-host policy is a strict superset of safety while adding usability. (c) **Lazy Turndown HTML→markdown** (Runnable `utils.ts:91-97`) — v4's HTML strip is regex-based and lossy; Turndown gives clean markdown. **Items DROPPED from Runnable's WebFetch** (constraint-driven): preapproved hosts list (Runnable `preapproved.ts` 92 hosts) — single-user insurance SageMaker likely runs in a corp-allowlist proxy already; preapproved list duplicates that policy and risks divergence; Anthropic domain-blocklist preflight (`api.anthropic.com/api/web/domain_info`) — Bedrock-only constraint forbids the extra Anthropic API call; 60 s fetch timeout (v4's 20 s is stricter, keep stricter); Haiku-summarize-binary path — depends on `queryHaiku` (Anthropic API), not Bedrock; egress-proxy `X-Proxy-Error` header parse — corp-proxy specific; per-domain permission rules — v4 already gates `web_fetch` via HIGH_RISK_TOOLS approval (sagemaker_agent.py:8043), no per-domain layer needed. |
| 21 | `WebSearchTool` | none in v4 (no web search anywhere — see grep result `Grep web_search\|web_fetch\|browser\|playwright\|requests\.` returns only `_WEB_FETCH_MAX_BYTES` references) | **OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP)** | n/a | Runnable WebSearchTool wraps Anthropic-server-side `web_search_20250305` beta — that beta is firstParty / Vertex (Claude 4.x) / Foundry only. Bedrock provider is NOT in Runnable's `isEnabled()` allowlist (`WebSearchTool.ts:168-193` enumerates `firstParty`, `vertex`, `foundry`; Bedrock is implicit `return false`). v5.0.1 is Bedrock-only → tool would be permanently disabled even if shipped. Confirmed via `WebSearchTool.ts:192` `return false`. |
| 22 | `WorkflowTool` (+ `bundled/`, `createWorkflowCommand.ts`, `WorkflowPermissionRequest.tsx`) | n/a | **RUNNABLE-STUB** + **OUT-OF-SCOPE-BY-CONSTRAINT** | n/a | All bodies stub. Workflows in Runnable are user-defined multi-step macros (`commands/<name>` + bundled workflows). v4 has slash-command system (Block D in Q1 — 19 commands at :8164) which already covers the macro use case for SageMaker single-user. |
| — | `shared/gitOperationTracking.ts` | none in v4 (v4 BashTool tracks no git counters; `sagemaker_agent.py` has no git-PR tracking logic) | **OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP)** | n/a | Pattern detects `git commit`/`push`/`gh pr create`/etc in BashTool output and auto-links session→GitHub-PR via `linkSessionToPR`. Single-user SageMaker insurance has no GitHub remote (Bedrock-only constraint = no external network beyond v4's `web_fetch`). Concept = tag bash sessions with their commit-sha — small win, would require adding OTLP counters which v4 doesn't have. Skip. |
| — | `shared/spawnMultiAgent.ts` | v4: `tool_task` :7348-:7388 + `AGENT_TYPES` :6914-... + sub-agent spawn (synchronous, in-process) | **OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP)** | n/a | This is the multi-process (tmux / iTerm2 / IDE-pane / in-process) teammate spawner shared between AgentTool fork-mode and TeamCreate. v4's sub-agent is synchronous-in-process only — already adequate for single-user SageMaker. The `resolveTeammateModel('inherit')` pattern (Runnable `:97-99`) is the only fold-in idea: **fold "inherit parent's main-loop model" into v4's sub-agent spawn** if v5.0.1 adds a `model: "inherit"` token to `tool_task`. v4 currently inherits the parent BedrockClient implicitly (same singleton — see Q1 Block B "BedrockClient.chat wiring (parent + sub-agent shared singleton — same object identity)" row at :2253, :3755, :4510). **Decision**: v4 already has model-inherit-via-singleton, no port needed. |
| — | `testing/TestingPermissionTool.tsx` | none | **OUT-OF-SCOPE** | n/a | Test-only tool gated by `NODE_ENV === 'test'`. Even Runnable's shipped build has it always-disabled (`"production" === 'test'` literal → false). |
| — | `tools/utils.ts` | none in v4 (no `sourceToolUseID` system) | **PORTED-FROM-RUNNABLE-IDEA** (low priority) | optional, in `tools/_helpers.py` if/when v5 adds queue-style tool messages | `tagMessagesWithToolUseID` stamps user-style messages with the originating tool_use_id so the UI can clear "tool is running" placeholders when the tool resolves. v4 doesn't have a placeholder UI — the chat-cell renders tool-use blocks directly. Low value for v5.0.1. Defer to v5.x if/when chat.ipynb adds streaming tool-use placeholders. **Status: noted, not ported.** |

---

## Summary table

| Disposition | Count | Tools |
|---|---|---|
| PORTED-FROM-v4 (already in baseline) | 2 | TodoWriteTool, WebFetchTool |
| PORTED-FROM-RUNNABLE (net-new, no defer) | 0 | — |
| PORTED-FROM-RUNNABLE-IDEA (folded into existing v5) | 3 | WebFetchTool (LRU cache + same-host redirect + Turndown), TodoWriteTool (verification nudge — already in v4), `tools/utils.ts` (`tagMessagesWithToolUseID` — deferred) |
| OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP) | 16 | SleepTool, SyntheticOutputTool, TaskCreateTool, TaskGetTool, TaskListTool, TaskOutputTool, TaskStopTool, TaskUpdateTool, TeamCreateTool, TeamDeleteTool, ToolSearchTool, WebSearchTool, SubscribePRTool, SuggestBackgroundPRTool, WebBrowserTool, WorkflowTool, shared/gitOperationTracking.ts, shared/spawnMultiAgent.ts, testing/TestingPermissionTool |
| RUNNABLE-STUB (no content to port) | 7 dirs | SnipTool, SubscribePRTool, SuggestBackgroundPRTool, TerminalCaptureTool, TungstenTool, VerifyPlanExecutionTool, WebBrowserTool, WorkflowTool |

(Counts overlap because stubs are ALSO out-of-scope; categories are not mutually exclusive.)

**Net v5.0.1 work from this slice**:
1. `tools/todo_write.py` — already on plan v3 line :361, T1100 row :425 (no change). v4 source line refs above.
2. `tools/web_fetch.py` — already on plan v3 line :364, T1100 row :425 (no change). v4 source line refs above. **Plus 3 fold-ins from Runnable** (see row 20 above): LRU cache, same-host redirect, Turndown.

---

## Concerns / open items

1. **WebFetch fold-ins from Runnable are net-new effort** vs. plan v3's "verbatim port from v4 :6787-:6829". Three additions: LRU cache (~30 LOC), same-host redirect (~40 LOC), Turndown integration (`pip install markdownify` since Python equivalent — Turndown is JS; use `markdownify` lib or `html2text`). Estimate +80 LOC + 1 dep. Decision needed: keep v4 verbatim (constraint #1 strict reading) OR add fold-ins (constraint = combined-better-than-each per "v5 BETTER definition (7 axes)"). Recommendation: **add fold-ins** — they're additive, no v4 functionality is lost, and they pass the "better than v4 on optimal-tool-use axis" gate. Plan-v3 row should be updated to reflect this.

2. **Verification-nudge wording mismatch** (already documented in v4 :6872 comment, but worth double-checking): Runnable `TodoWriteTool.ts:107` says `'You cannot self-assign PARTIAL by listing caveats... only the verifier issues a verdict.'` — v4 `:6878-:6882` softened this to `'SUGGEST `/verify`...wait for confirmation...only auto-spawn verify if CONFIG.enforce_verify_contract=True'`. v4's softer version IS correct per the V4.10.2 softening note. No action.

3. **No `compact_v4` evidence of an "auto-snip" for tool-result truncation** — Runnable's stub `SnipTool` may have been a long-tool-result snipper (cf `maxResultSizeChars: 100_000` cap on every tool). v4 enforces tool-result size via `maxResultSizeChars`-equivalent in `bash_executor` truncation only. **Not a gap**: the Runnable file is empty so there's nothing to port; the `100_000` per-tool cap pattern IS already a Runnable-wide convention v5 should follow tool-by-tool (most v4 tools already have explicit truncation; check during T1100 implementation).

4. **No deferrals introduced by this slice** — every Runnable-only feature (TaskV2, swarm, ToolSearch, WebSearch, SyntheticOutput) is rejected by an architectural constraint that is pre-stated in the plan, not by "ship-it-later" laziness. The "DECISION-NOT-DROP" tag is honest: each row above cites a specific constraint (#1 v4 baseline / #2 ipynb canonical UI / Bedrock-only / single-user / canonical-plan drops list).

---

## Files read (for audit)

- `tools/SleepTool/SleepTool.ts` (19 B), `tools/SleepTool/prompt.ts` (791 B) — both
- `tools/SnipTool/SnipTool.ts`, `tools/SnipTool/prompt.ts` — both (stubs)
- `tools/SubscribePRTool/SubscribePRTool.ts` — full (stub)
- `tools/SuggestBackgroundPRTool/SuggestBackgroundPRTool.ts` — full (stub)
- `tools/SyntheticOutputTool/SyntheticOutputTool.ts` — full (164 lines)
- `tools/TaskCreateTool/{TaskCreateTool.ts, prompt.ts, constants.ts}` — all
- `tools/TaskGetTool/{TaskGetTool.ts, prompt.ts, constants.ts}` — all
- `tools/TaskListTool/{TaskListTool.ts, prompt.ts, constants.ts}` — all
- `tools/TaskOutputTool/{TaskOutputTool.tsx, constants.ts}` — first 419 lines of .tsx (full file is 67 KB; remaining is React result-display compiled by `react/compiler-runtime` with embedded sourceMap, not v5-relevant)
- `tools/TaskStopTool/{TaskStopTool.ts, prompt.ts, UI.tsx}` — all
- `tools/TaskUpdateTool/{TaskUpdateTool.ts, prompt.ts, constants.ts}` — all
- `tools/TeamCreateTool/{TeamCreateTool.ts, prompt.ts, constants.ts, UI.tsx}` — all
- `tools/TeamDeleteTool/{TeamDeleteTool.ts, prompt.ts}` — all (UI.tsx + constants.ts not read; 700 B prompt + 4360 B body covered functionality)
- `tools/TerminalCaptureTool/{TerminalCaptureTool.ts, prompt.ts}` — both (stubs)
- `tools/TodoWriteTool/{TodoWriteTool.ts, prompt.ts}` — both
- `tools/ToolSearchTool/{ToolSearchTool.ts, prompt.ts, constants.ts}` — all
- `tools/TungstenTool/{TungstenTool.ts, TungstenLiveMonitor.tsx}` — both (stubs)
- `tools/VerifyPlanExecutionTool/{VerifyPlanExecutionTool.ts, constants.ts}` — both (stub)
- `tools/WebBrowserTool/{WebBrowserTool.ts, WebBrowserPanel.tsx}` — both (stubs)
- `tools/WebFetchTool/{WebFetchTool.ts, prompt.ts, preapproved.ts, utils.ts}` — all (UI.tsx 8 KB not read — render-only React, not v5-relevant)
- `tools/WebSearchTool/{WebSearchTool.ts, prompt.ts}` — both (UI.tsx 12 KB not read — render-only)
- `tools/WorkflowTool/{WorkflowTool.ts, createWorkflowCommand.ts, constants.ts, WorkflowPermissionRequest.tsx, bundled/index.ts}` — all (stubs)
- `tools/shared/gitOperationTracking.ts` — full (278 lines)
- `tools/shared/spawnMultiAgent.ts` — first 100 lines (file is 36 KB; head establishes pattern, scope is OUT-OF-SCOPE so deeper read not needed)
- `tools/testing/TestingPermissionTool.tsx` — full
- `tools/utils.ts` — full (41 lines)

v4 cross-reads (audit anchor):
- `compact_v4/MAIN/agent/sagemaker_agent.py:6780-6829` (web_fetch)
- `compact_v4/MAIN/agent/sagemaker_agent.py:6849-6895` (todo_write/todo_read)
- `compact_v4/MAIN/agent/sagemaker_agent.py:7300-7400` (tool registry schemas)
- `compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md:361, :364, :373, :425` (T1100 row + tool plan)
- `compact_v5/_phase_2/wave_4/Q1_EVIDENCE_MATRIX.md:1-100` (matrix format anchor)
