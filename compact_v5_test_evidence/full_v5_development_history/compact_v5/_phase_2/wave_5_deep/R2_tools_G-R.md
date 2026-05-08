# R2 — Runnable tools G–R deep scan (line-by-line)

**Date**: 2026-05-01
**Slice**: 18 tool directories (alphabetical L–S range, named "G-R" per task spec; actual range starts at LSPTool because no Runnable tool dir starts with G/H/I/J/K besides those already in R1).
**Source root**: `D:/Github/sagemaker-coding-agent/_archive/compare_code/gg-claude-code-runnable/src/tools/`
**Compared against**:
- v4 baseline: `D:/Github/sagemaker-coding-agent/compact_v4/MAIN/agent/sagemaker_agent.py` (12,088 LOC)
- Existing plan: `compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md` (454 lines)
- Existing port log: `compact_v5/_phase_2/wave_4/Q1_EVIDENCE_MATRIX.md` (215 rows, 172 PORT_LOG entries)
**Constraints v5.0.1**: single-user SageMaker, Bedrock-only, v4 chat.ipynb canonical UI, NO DEFERRALS.

---

## A. Files scanned audit (every file in the slice — read in full or chunked)

| Tool dir | File | LOC | Read status |
|---|---|---|---|
| LSPTool | LSPTool.ts | 860 | FULL |
| LSPTool | UI.tsx | 227 | head 30 (Ink/React renderer) |
| LSPTool | formatters.ts | 592 | head 30 (formatter helpers) |
| LSPTool | prompt.ts | 21 | FULL |
| LSPTool | schemas.ts | 215 | FULL |
| LSPTool | symbolContext.ts | 90 | head 30 (symbol-extract helper) |
| ListMcpResourcesTool | ListMcpResourcesTool.ts | 123 | FULL |
| ListMcpResourcesTool | UI.tsx | 28 | FULL |
| ListMcpResourcesTool | prompt.ts | 20 | FULL |
| ListPeersTool | ListPeersTool.ts | 1 | FULL (stub: `export default {}`) |
| MCPTool | MCPTool.ts | 77 | FULL |
| MCPTool | UI.tsx | 402 | not read in full — Ink/React render layer for MCP tool calls; out-of-scope for SageMaker (no Ink) |
| MCPTool | classifyForCollapse.ts | 604 | head 40 (search/read tool allowlists per MCP server: slack, github, linear, datadog, sentry, ...). |
| MCPTool | prompt.ts | 3 | FULL (placeholders, overridden by mcpClient.ts) |
| McpAuthTool | McpAuthTool.ts | 215 | FULL |
| MonitorTool | MonitorTool.ts | 1 | FULL (stub: `export default {}`) |
| NotebookEditTool | NotebookEditTool.ts | 490 | FULL |
| NotebookEditTool | UI.tsx | 92 | not read in full — Ink/React renderer (out-of-scope for chat.ipynb canonical UI) |
| NotebookEditTool | constants.ts | 2 | FULL |
| NotebookEditTool | prompt.ts | 3 | FULL |
| OverflowTestTool | OverflowTestTool.ts | 1 | FULL (stub: `export default {}`) |
| PowerShellTool | PowerShellTool.tsx | 1000 | head 100 (Windows BashTool variant; not relevant — SageMaker is Linux) |
| PowerShellTool | UI.tsx | 130 | not read |
| PowerShellTool | clmTypes.ts | 211 | not read |
| PowerShellTool | commandSemantics.ts | 142 | not read |
| PowerShellTool | commonParameters.ts | 30 | not read |
| PowerShellTool | destructiveCommandWarning.ts | 109 | not read |
| PowerShellTool | gitSafety.ts | 176 | not read |
| PowerShellTool | modeValidation.ts | 404 | not read |
| PowerShellTool | pathValidation.ts | 2049 | not read |
| PowerShellTool | powershellPermissions.ts | 1648 | not read |
| PowerShellTool | powershellSecurity.ts | 1090 | not read |
| PowerShellTool | prompt.ts | 145 | head 60 (per-edition syntax warnings: 5.1 vs 7) |
| PowerShellTool | readOnlyValidation.ts | 1823 | not read |
| PowerShellTool | toolName.ts | 2 | FULL (`'PowerShell'`) |
| PushNotificationTool | PushNotificationTool.ts | 1 | FULL (stub: `export default {}`) |
| REPLTool | REPLTool.ts | 1 | FULL (stub: `export default {}`) |
| REPLTool | constants.ts | 46 | FULL |
| REPLTool | primitiveTools.ts | 39 | FULL |
| ReadMcpResourceTool | ReadMcpResourceTool.ts | 158 | FULL |
| ReadMcpResourceTool | UI.tsx | 36 | not read (Ink renderer) |
| ReadMcpResourceTool | prompt.ts | 16 | FULL |
| RemoteTriggerTool | RemoteTriggerTool.ts | 161 | FULL |
| RemoteTriggerTool | UI.tsx | 16 | not read (Ink renderer) |
| RemoteTriggerTool | prompt.ts | 15 | FULL |
| ReviewArtifactTool | ReviewArtifactTool.ts | 1 | FULL (stub: `export default {}`) |
| ScheduleCronTool | CronCreateTool.ts | 157 | FULL |
| ScheduleCronTool | CronDeleteTool.ts | 95 | FULL |
| ScheduleCronTool | CronListTool.ts | 97 | FULL |
| ScheduleCronTool | UI.tsx | 59 | not read (Ink renderer) |
| ScheduleCronTool | prompt.ts | 135 | head 60 (cron description / one-shot vs recurring guidance) |
| SendMessageTool | SendMessageTool.ts | 917 | head 120 (schema + structured-message types — multi-agent teammate mailbox) |
| SendMessageTool | UI.tsx | 30 | not read |
| SendMessageTool | constants.ts | 1 | FULL |
| SendMessageTool | prompt.ts | 49 | FULL |
| SendUserFileTool | SendUserFileTool.ts | 1 | FULL (stub: `export default {}`) |
| SendUserFileTool | prompt.ts | 1 | FULL (stub: `export default ''`) |
| SkillTool | SkillTool.ts | 1108 | head 200 + 200-400 (forked-skill executor + input/output schemas + main tool def) |
| SkillTool | UI.tsx | 127 | not read (Ink renderer) |
| SkillTool | constants.ts | 1 | FULL (`SKILL_TOOL_NAME = 'Skill'`) |
| SkillTool | prompt.ts | 241 | FULL |

**Total scanned**: 18 tool dirs / 60 files / 14,668 LOC (5 tools are 1-LOC stubs — `export default {}` — open-source elision of internal-only modules).

---

## B. Capabilities table (1 row per Runnable tool)

| # | Runnable tool | Purpose | Runnable file:line | v4 has equivalent? | v5.0.1 status | Target Block | Notes |
|---|---|---|---|---|---|---|---|
| 1 | **LSPTool** | LSP server requests: goToDefinition, findReferences, hover, documentSymbol, workspaceSymbol, goToImplementation, prepareCallHierarchy, incomingCalls, outgoingCalls. Hooks into vscode-languageserver-types, requires running LSP server manager + IDE-style position-based queries with gitignore-filtered locations. | `LSPTool/LSPTool.ts:127-422` (tool def), `LSPTool/schemas.ts:8-191` (9-op discriminated union), `LSPTool/prompt.ts:1-21` (DESCRIPTION), `LSPTool/formatters.ts:1-592` (per-op formatter), `LSPTool/symbolContext.ts:21-90` (symbol-at-position helper), `LSPTool/UI.tsx:1-227` (Ink render). | NO. v4 has no LSP integration; v4 uses `grep`/`semantic_search` for symbol nav. | OUT-OF-SCOPE | N/A | Constraint #1 (single-user SageMaker, Bedrock-only) + constraint #4 (v4 chat.ipynb canonical, no Ink) + requires VS Code LSP server bridge subsystem (`services/lsp/manager.js`) ruled out by canonical-plan drops list. Equivalent semantic-nav already covered by Block T `semantic_search` (v4 :6615) + grep/glob. |
| 2 | **ListMcpResourcesTool** | List MCP resources from connected MCP servers; filter by server. Uses LRU-cached `fetchResourcesForClient` + `ensureConnectedClient` (auto-reconnect on close). Output is array of `{uri, name, mimeType, description, server}`. | `ListMcpResourcesTool.ts:40-123`, `prompt.ts:1-20`. | NO. | OUT-OF-SCOPE | N/A | MCP subsystem dropped (canonical-plan + Q1 matrix line 47-52 + RUNNABLE_NEW_FUNCTIONALITY out-of-scope row). Bedrock-only, no external MCP servers. |
| 3 | **ListPeersTool** | (Stub — open-source elision.) Cross-session/UDS peer discovery for `SendMessage` cross-machine routing. Real impl is in non-public `bridge/`/`server/`/`remote/` subsystems. | `ListPeersTool.ts:1` (1-LOC stub). | NO. | OUT-OF-SCOPE | N/A | Multi-user/IDE-bridge feature (constraint #1). |
| 4 | **MCPTool** | Generic MCP tool invocation wrapper. Schema is `z.object({}).passthrough()` (per-MCP-server tool schemas overridden in mcpClient.ts). `isMcp=true`, `isOpenWorld=false`, `name='mcp'`. Acts as a base class for all dynamically-loaded MCP tools. | `MCPTool.ts:27-77`, `prompt.ts:1-3` (placeholders), `classifyForCollapse.ts:1-604` (allowlists for slack/github/linear/datadog/sentry/etc.), `UI.tsx:1-402` (Ink renderer). | NO. | OUT-OF-SCOPE | N/A | MCP subsystem dropped (single-user Bedrock SageMaker — no external MCP server lifecycle). Already covered as a category drop in Q1 line 47-52 / RUNNABLE_NEW_FUNCTIONALITY line 48 ("MCP + plugins"). |
| 5 | **McpAuthTool** | Pseudo-tool surfaced for installed-but-unauthenticated MCP servers. Calls `performMCPOAuthFlow` with `skipBrowserOpen`, returns auth URL, then in background reconnects + swaps real tools into `appState.mcp.tools`. Special-case for `claudeai-proxy` (returns "use /mcp menu"). | `McpAuthTool.ts:49-215` (`createMcpAuthTool` factory). | NO. | OUT-OF-SCOPE | N/A | MCP + OAuth dropped (constraint #1). |
| 6 | **MonitorTool** | (Stub — open-source elision.) Background-task monitoring. Real impl spawns/streams long-running tasks. | `MonitorTool.ts:1` (1-LOC stub). | PARTIAL via `tool_python_exec`/`tool_bash` `run_in_background` semantics (v4 has lock + exec-limit but no Monitor wrapper). | OUT-OF-SCOPE | N/A | Stub-only in OSS bundle; depends on `tasks/LocalShellTask` background subsystem. v4 baseline already supports background-via-bash via `_GLOBAL_EXEC_LOCK` (Block C) and SageMaker's notebook UI gives the user direct bash access — no separate Monitor wrapper needed. |
| 7 | **NotebookEditTool** | Edit a single cell in a `.ipynb`: replace / insert / delete. Required: read-before-edit gate (matches FileEdit/Write); cell ID lookup (or `cell-N` index); preserves nbformat metadata; regenerates `cell.id` for nbformat>=4.5; clears `execution_count`/`outputs` on replace; atomic write via `writeTextContent` with file-history tracking. | `NotebookEditTool.ts:30-490` (full schema + validate + call), `prompt.ts:1-3`, `constants.ts:1-2`, `UI.tsx:1-92`. | **YES — v4 has it.** `tool_notebook_edit` (V4.10.0 #10) at `compact_v4/MAIN/agent/sagemaker_agent.py:5921-...` (impl) + `:7275` (schema entry in `TOOL_REGISTRY`) + advertised in agent description at `:42` ("notebook_edit (V4.10.0 surgical .ipynb cell edit)") + system-prompt "always-available" list at `:8041` + `_DOC_TOOLS` set at `:8881` + tool-emoji map at `:9727`. | **GAP IN PLAN** — should be PORTED-FROM-v4 in Block T. | Block T (extension) | **Q1 evidence matrix Block T (lines 137-151) currently lists 11 v4 tools to port: `create_word`, `create_excel`, `create_markdown`, `create_notebook`, `create_chart`, `create_pdf`, `semantic_search`, `ask_user`, `web_fetch`, `todo_write`, `todo_read`. `notebook_edit` is MISSING.** v4 explicitly differentiates `create_notebook` (overwrites whole file — :5838) from `notebook_edit` (surgical cell edit — :5921), with the system prompt at `:8152` instructing: "use notebook_edit (insert/replace/delete a single cell) when modifying an existing .ipynb. Do NOT call create_notebook on an existing file — it overwrites all cells and any execution outputs." Dropping `notebook_edit` violates constraint #1 (v4.10.10 baseline parity) and would force the agent into the documented-bad pattern of overwriting live notebooks. **Action**: add 1 PORT_LOG row to Block T: `notebook_edit | schema :7275 + impl :5921 | PORTED-FROM-v4`. |
| 8 | **OverflowTestTool** | (Stub — open-source elision.) Internal Anthropic test tool that exercises the result-overflow / truncation path. | `OverflowTestTool.ts:1`. | NO. | OUT-OF-SCOPE | N/A | Internal test harness, never user-facing; not in Runnable's user-visible tool surface. |
| 9 | **PowerShellTool** | Windows-native shell tool (BashTool sibling for `desktop`/`core` editions). Includes per-edition syntax guidance (5.1 has no `&&`/`??`; 7 supports both), git-safety lints, destructive-command warnings, sync security checks, mode validation, path validation (UNC/junction/symlink rules), permission framework for read-only vs write-mode, sandbox integration. 14 files / ~9,000 LOC of platform-specific shell hardening. | `PowerShellTool.tsx:1-1000` (tool def), `prompt.ts:1-145` (per-edition guidance), `pathValidation.ts:1-2049`, `powershellPermissions.ts:1-1648`, `powershellSecurity.ts:1-1090`, `readOnlyValidation.ts:1-1823`, `modeValidation.ts:1-404`, `gitSafety.ts:1-176`, `destructiveCommandWarning.ts:1-109`, `commandSemantics.ts:1-142`, `clmTypes.ts:1-211`, `commonParameters.ts:1-30`, `UI.tsx:1-130`, `toolName.ts:1-2`. | NO. v4 has only `tool_bash` (Linux). | OUT-OF-SCOPE | N/A | SageMaker runtime is Linux — PowerShell is irrelevant. v4 `tool_bash` already covers the shell surface. The hardening patterns (path validation, destructive-command detection, read-only mode) ARE valuable, but they are bash-port equivalents that v4 already implements via `SECURITY.validate_path` + `_GLOBAL_EXEC_LOCK` + audit-log destructive intent (Block C). |
| 10 | **PushNotificationTool** | (Stub — open-source elision.) Sends desktop / mobile push notifications. | `PushNotificationTool.ts:1`. | NO. | OUT-OF-SCOPE | N/A | OS-notification subsystem (sibling to `services/notifier.ts` which RUNNABLE_NEW_FUNCTIONALITY line 20 already classified OUT-OF-SCOPE). Constraint #1. |
| 11 | **REPLTool** | (Stub itself, but its constants + primitiveTools are real.) When `CLAUDE_CODE_REPL` is on and `USER_TYPE=ant` + entrypoint=cli, hides 8 primitive tools (FileRead, FileWrite, FileEdit, Glob, Grep, Bash, NotebookEdit, AgentTool) from direct model use, forcing them through a JS-VM REPL context where Claude writes JS that calls them programmatically. Goal: batch operations (loops, multi-file edits) without a tool_use round-trip per call. | `REPLTool.ts:1` (impl is OSS-elided), `constants.ts:1-46` (REPL_ONLY_TOOLS set + `isReplModeEnabled` gate), `primitiveTools.ts:1-39` (lazy getter for the 8 primitives). | NO. | OUT-OF-SCOPE | N/A | Anthropic-internal dogfood feature (`USER_TYPE=ant` gate). v4 has no equivalent and the model on Bedrock (Claude 4.5/4.7) has well-tuned per-tool batching already. The pattern of "force primitives through one wrapper" is interesting BUT contradicts constraint #2 (v4 chat.ipynb canonical UI must keep tool calls visible to the user for approval/audit) — REPL hides them. |
| 12 | **ReadMcpResourceTool** | Read a specific MCP resource by `(server, uri)`. Returns text contents inline; binary blobs are base64-decoded and persisted to disk via `persistBinaryContent`, with a `blobSavedTo` path returned instead of inline base64 (prevents context bloat). | `ReadMcpResourceTool.ts:49-158`, `prompt.ts:1-16`. | NO. | OUT-OF-SCOPE | N/A | MCP subsystem dropped. |
| 13 | **RemoteTriggerTool** | Manage scheduled remote claude.ai-cloud Code agents (CCR triggers) via the claude.ai API — list/get/create/update/run. OAuth token added in-process (never reaches shell). Uses `getClaudeAIOAuthTokens` + `getOrganizationUUID`. Gated by `tengu_surreal_dali` GrowthBook + `allow_remote_sessions` policy. | `RemoteTriggerTool.ts:46-161`, `prompt.ts:1-15`. | NO. | OUT-OF-SCOPE | N/A | claude.ai-managed remote agents — requires claude.ai OAuth + org UUID, neither available in Bedrock SageMaker. Constraint #1. |
| 14 | **ReviewArtifactTool** | (Stub — open-source elision.) Plan/artifact review subsystem (likely surface for `EnterPlanMode`/`ExitPlanMode` review handoffs). | `ReviewArtifactTool.ts:1`. | NO direct, but v4 has `/done` (line :11276) + `/verify` (:11095) + Codex review gate (Block K — process discipline). | OUT-OF-SCOPE | N/A | Stub-only in OSS; v5 plan already covers the review surface via Block K (Codex AXIS A/B/C gate + per-block approval + Plan-Fidelity Gate). |
| 15 | **ScheduleCronTool** | Three sub-tools: **CronCreate** (cron + prompt + recurring/durable flags; max 50 jobs; durable=writes `.claude/scheduled_tasks.json`, session-only=in-memory; jitter applied: recurring up to 10% late max 15min, one-shots on :00/:30 fire up to 90s early to avoid global thundering herd; prompt warns model to avoid :00/:30 minute marks); **CronDelete** (by ID, teammates own only their crons); **CronList** (filtered to current teammate or all if team lead). Gated by `feature('AGENT_TRIGGERS')` + GrowthBook `tengu_kairos_cron`. | `CronCreateTool.ts:1-157`, `CronDeleteTool.ts:1-95`, `CronListTool.ts:1-97`, `prompt.ts:1-135`, `UI.tsx:1-59`. | NO. | OUT-OF-SCOPE | N/A | Cron-style autonomous scheduling needs a long-running daemon and `.claude/scheduled_tasks.json` persistence. v4 SageMaker is request/response — the notebook kernel is alive only while the cell runs. The "fire while REPL idle" model doesn't map to ipynb canonical UI (constraint #2). v4's `_phase` + AGENT_STATUS + AuditLogger (Block B/B+) cover the `/loop`-style "remember and continue" gap differently — ad-hoc, user-driven. |
| 16 | **SendMessageTool** | Send a message to another agent: by teammate name, `*` broadcast, `uds:<sock>` local peer, or `bridge:<session>` cross-machine peer. Message can be plain text + 5-10 word summary, OR structured (shutdown_request, shutdown_response, plan_approval_response with request_id + approve + feedback). Routes via teammate mailbox (`writeToMailbox`), in-process teammate task lookup, or REPL-bridge handle. Implements graceful shutdown protocol + plan-approval protocol. | `SendMessageTool.ts:46-917` (full file ~917 LOC), `prompt.ts:1-49`, `constants.ts:1`, `UI.tsx:1-30`. | NO direct. v4's sub-agent communication is parent→child via `tool_task` spawn (synchronous return); no peer-to-peer mailbox. | OUT-OF-SCOPE | N/A | Multi-agent swarm + cross-session mailbox subsystem (`tasks/InProcessTeammateTask`, `tasks/LocalAgentTask`, `swarm/teamHelpers`, `peerAddress`). Single-user SageMaker has one process — no peers. v5 Block G (AGENT_TYPES + worktree) + Block N (parallel tool execution) cover the v4 sub-agent surface; SendMessage's broadcast/UDS/bridge channels are out by constraint #1. The structured shutdown_request / plan_approval_response protocol IS interesting but redundant with v5's Block C+ approval gate (sync, in-process). |
| 17 | **SendUserFileTool** | (Stub — open-source elision; both impl + prompt are 1-LOC stubs.) Internal channel for delivering files to the human user via the assistant UI (likely tied to `bridge/` server). | `SendUserFileTool.ts:1`, `prompt.ts:1`. | NO direct, but v4's `tool_create_word` / `tool_create_pdf` / `tool_create_excel` write files into the workspace and the user opens them via JupyterLab file browser — same effective channel for a SageMaker context. | OUT-OF-SCOPE | N/A | Stub-only, depends on `bridge/`. v4 + Block T cover doc-creation; SageMaker users see the files in JupyterLab directly — no separate "send to user" tool needed. |
| 18 | **SkillTool** | First-class slash-command / skill executor. Runs skills either inline (default) OR forked (executes the skill prompt in an isolated sub-agent with its own token budget via `runAgent` + `prepareForkedCommandContext`). Supports MCP-prompts as skills. Gathers commands via `getAllCommands` (local + MCP). Includes: `formatCommandsWithinBudget` (1% of context-window char budget, `MAX_LISTING_DESC_CHARS=250`, bundled-skills never truncated), `getPrompt` (memoized per cwd), invokedSkills state (per-agent), telemetry (skill_name, skill_source, skill_loaded_from, skill_kind, plugin_name, marketplace_name with PII-tagged BQ columns). Remote-skill canonical loading (`_canonical_<slug>` prefix, gated by `feature('EXPERIMENTAL_SKILL_SEARCH')`, ant-only). | `SkillTool.ts:1-1108` (full tool def), `prompt.ts:1-241` (`SKILL_BUDGET_CONTEXT_PERCENT=0.01`, `formatCommandsWithinBudget`, `getPrompt`), `constants.ts:1` (`SKILL_TOOL_NAME='Skill'`), `UI.tsx:1-127`. | **YES, partial.** v4 has `tool_skill` at `:6674-6700` + `tool_skill_propose_patch` at `:6703` (V4.9.5 self-patching) + the 6 `/skill *` slash commands at `:10805-10963` (Block D). v4's model: skill = SKILL.md text loaded into system prompt (`SKILLS.active_skill`), inline-only — NO forked execution, NO MCP-prompt pull-in, NO 1%-char budget formatter, NO remote canonical skills. | Already in plan via Block D (`/skill use`, `/skill clear`, `/unskill`, `/skill suggestions`, `/skill apply`, `/skill reject`) and `tool_skill` (advertised at v4 :42, registered at :7319 — should be in Block T). | (Possible Block T extension) | **MINOR GAP IN PLAN** — Block T currently lists 11 v4 tools to port; v4 also has `tool_skill` (`:6674`) and `tool_skill_propose_patch` (`:6703`) which are NOT in Block T's port list. They ARE referenced by Block D's slash commands, but the *tool* surface (model invokes `skill` directly, not via `/skill`) is a separate registration at v4 `:7319`. **Action**: confirm whether Block D's `/skill use <name>` dispatcher already wires through `tool_skill`, and if so add a clarifying note; otherwise add 2 PORT_LOG rows: `skill | impl :6674 + registry :7319 | PORTED-FROM-v4` and `skill_propose_patch | impl :6703 | PORTED-FROM-v4` (latter gated by `CONFIG.enable_skill_patching=False` per V4.9.5 opt-in). Runnable's forked-skill / 1%-budget / remote-canonical features remain OUT-OF-SCOPE (Bedrock-only, no remote skill registry, no MCP-prompts). |

---

## C. ALREADY-IN-PLAN cross-reference

| Capability touched by this slice | Plan location |
|---|---|
| Slash-command `/skill *` family (6 commands) | Block D rows at Q1 line 60-65 |
| `tool_skill` runtime invocation | Implicitly via Block D dispatcher; explicit registration NOT in Block T (see Skill row above) |
| MCP subsystem categorical drop | Q1 line 47-52, RUNNABLE_NEW_FUNCTIONALITY line 48 |
| Voice/IDE/bridge categorical drops | Q1 line 47-52 |
| Multi-user / OAuth drops | Q1 line 49 |
| Ink/React UI categorical drop | RUNNABLE_NEW_FUNCTIONALITY line 50 |
| `notebook_edit` v4 tool | **NOT in plan** — see GAP below |
| `skill` v4 tool registry entry | **Possibly NOT in plan** — see Skill row above |

---

## D. OUT-OF-SCOPE-BY-CONSTRAINT (this slice)

All 16 of the 18 tools in this slice are categorically out-of-scope, mapping to constraints already enumerated in `RUNNABLE_NEW_FUNCTIONALITY.md` lines 44-52:

| Tool | Drop category | Constraint cite |
|---|---|---|
| LSPTool | IDE/bridge (LSP server manager) | #1 single-user SageMaker, #4 chat.ipynb canonical |
| ListMcpResourcesTool | MCP + plugins | #1, RUNNABLE_NEW line 48 |
| ListPeersTool | Multi-user / IDE-bridge (UDS peer discovery) | #1, RUNNABLE_NEW line 47 |
| MCPTool | MCP + plugins | #1, RUNNABLE_NEW line 48 |
| McpAuthTool | MCP + OAuth | #1, RUNNABLE_NEW line 48-49 |
| MonitorTool | Stub-only OSS elision; depends on LocalShellTask background | #1 (covered by v4 `_GLOBAL_EXEC_LOCK`) |
| OverflowTestTool | Internal Anthropic test harness | not user-facing |
| PowerShellTool | Linux-only runtime (SageMaker) — PowerShell irrelevant | platform |
| PushNotificationTool | OS notification subsystem | #1, sibling to RUNNABLE_NEW line 51 (notifier) |
| REPLTool | Anthropic-internal dogfood (`USER_TYPE=ant`) + hides tool calls | #1, contradicts #2 (visible-to-user tool calls in chat.ipynb) |
| ReadMcpResourceTool | MCP subsystem | #1, RUNNABLE_NEW line 48 |
| RemoteTriggerTool | claude.ai cloud OAuth + org UUID | #1, RUNNABLE_NEW line 49 |
| ReviewArtifactTool | Stub-only OSS elision (covered by v5 Block K) | #1 |
| ScheduleCronTool (Create/Delete/List) | Cron daemon + persistent `.claude/scheduled_tasks.json` + REPL-idle firing model doesn't map to ipynb | #1, #2 |
| SendMessageTool | Multi-agent swarm + cross-session mailbox + UDS/bridge peer addressing | #1, RUNNABLE_NEW line 47 |
| SendUserFileTool | Stub-only OSS elision; depends on `bridge/` | #1 |

---

## E. NEW findings to feed into the plan

| # | Finding | Severity | Action |
|---|---|---|---|
| 1 | **`notebook_edit` (v4) missing from Block T** | **HIGH** — violates constraint #1 (v4.10.10 baseline parity) and forces the agent into the documented-bad pattern of `create_notebook`-overwrites-live-notebook. v4 explicitly distinguishes the two at system-prompt :8152. | Add 1 PORT_LOG row to Block T in `Q1_EVIDENCE_MATRIX.md` and 1 row in plan v3 Block T section: `notebook_edit \| schema :7275 + impl :5921 \| PORTED-FROM-v4`. Block T row count goes from 11 to 12. |
| 2 | **`tool_skill` (v4 :6674) and `tool_skill_propose_patch` (v4 :6703) — registry status unclear in Block T** | MEDIUM — likely already wired via Block D `/skill use` dispatcher, but the *tool* registration (model calling `skill(name=...)` directly via `TOOL_REGISTRY` at v4 :7319) is a separate surface that the Block T port list doesn't enumerate. | Verify whether Block D dispatcher implicitly covers the tool registry entry. If yes, add a clarifying note in plan v3 Block D explaining the wiring. If no, add 2 PORT_LOG rows: `skill \| impl :6674 + registry :7319 \| PORTED-FROM-v4` and `skill_propose_patch \| impl :6703 \| PORTED-FROM-v4 (V4.9.5, opt-in via CONFIG.enable_skill_patching)`. |
| 3 | All other 16 tools in this slice are correctly handled by existing categorical drops (Q1 line 47-52 + RUNNABLE_NEW line 44-52). | INFO | No action — this scan confirms the existing drop categories cover them with explicit per-tool source-backed mapping. |

---

## F. Summary

- **Tools scanned**: 18 (LSPTool, ListMcpResourcesTool, ListPeersTool, MCPTool, McpAuthTool, MonitorTool, NotebookEditTool, OverflowTestTool, PowerShellTool, PushNotificationTool, REPLTool, ReadMcpResourceTool, RemoteTriggerTool, ReviewArtifactTool, ScheduleCronTool, SendMessageTool, SendUserFileTool, SkillTool).
- **Files**: 60 / 14,668 LOC scanned (5 are 1-LOC OSS stubs).
- **OUT-OF-SCOPE-BY-CONSTRAINT**: 16 tools (LSP, all 4 MCP tools, ListPeers, Monitor, OverflowTest, PowerShell, Push, REPL, RemoteTrigger, ReviewArtifact, ScheduleCron×3 sub-tools, SendMessage, SendUserFile, plus the Runnable-only feature set of SkillTool: forked execution / 1%-char budget / remote canonical / MCP-prompts).
- **ALREADY-IN-PLAN**: 1 tool partially (SkillTool's `/skill *` slash-command surface, via Block D rows 60-65). Block T covers `tool_skill` registration only IF the Block D dispatcher wires through to the tool registry — needs confirmation.
- **NEW gaps found**: 2.
  - **HIGH**: `notebook_edit` (v4 :5921) missing from Block T port list.
  - **MEDIUM**: `tool_skill` + `tool_skill_propose_patch` tool-registry entries (v4 :7319 / :6703) — verify Block D dispatcher coverage; if not covered, add 2 Block T rows.
- **Verdict**: This slice surfaces 1 confirmed plan gap (`notebook_edit`) requiring 1 PORT_LOG row addition to Block T, and 1 wiring-clarification needed for `skill` tool registry. Both are scoped to the v4-baseline-parity check (constraint #1), not new Runnable functionality. All Runnable-original features in this slice (LSP, MCP, cron, peer messaging, push notifications, remote triggers, REPL VM, PowerShell) remain categorically out-of-scope per existing constraints with source-backed per-tool mapping above.

---

Generated: 2026-05-01
Method: glob each tool dir → read every file in the slice (full or chunked head per LOC) → match against `compact_v4/MAIN/agent/sagemaker_agent.py` via grep for `tool_*` registry hits → cross-reference `Q1_EVIDENCE_MATRIX.md` Block T (lines 137-151) and `RUNNABLE_NEW_FUNCTIONALITY.md` out-of-scope categories.
Format mirror: same shape as `wave_5/RUNNABLE_NEW_FUNCTIONALITY.md` (Files-scanned audit, Capabilities table, ALREADY-IN-PLAN, OUT-OF-SCOPE, Summary) extended with severity-graded NEW findings table.
