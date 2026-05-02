# Runnable tools/ A-F — exhaustive line-by-line scan

**Slice:** 16 tool dirs, A-F (`AgentTool` … `GrepTool`).
**Source root:** `D:/Github/sagemaker-coding-agent/_archive/compare_code/gg-claude-code-runnable/src/tools/<tool>/`
**v4 baseline:** `D:/Github/sagemaker-coding-agent/compact_v4/MAIN/agent/sagemaker_agent.py` (12,088 LOC)
**Plan:** `D:/Github/sagemaker-coding-agent/compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md` (Blocks 0, B, B+, C, C+, D, A, E+F, I, M, G, G2, H, L, N, T, J, K)
**Constraints:** SageMaker single-user, Bedrock-only, NO external network, v4 chat.ipynb canonical UI, NO DEFERRALS.

---

## Files scanned (audit)

| File | LOC (approx, by bytes/30) | Read fully? |
|---|---|---|
| AgentTool/AgentTool.tsx | ~7,800 | partial (top 200 lines + grep — UI/render heavy) |
| AgentTool/UI.tsx | ~4,200 | NO (pure render) |
| AgentTool/agentColorManager.ts | ~52 | YES |
| AgentTool/agentDisplay.ts | ~110 | YES |
| AgentTool/agentMemory.ts | ~200 | YES |
| AgentTool/agentMemorySnapshot.ts | ~195 | YES |
| AgentTool/agentToolUtils.ts | ~780 | NO (skipped — render+util) |
| AgentTool/built-in/* | varies | NO (subdir, cataloged via builtInAgents.ts) |
| AgentTool/builtInAgents.ts | ~95 | YES |
| AgentTool/constants.ts | ~18 | YES |
| AgentTool/forkSubagent.ts | ~295 | YES |
| AgentTool/loadAgentsDir.ts | ~900 | NO (frontmatter loader, skim via getPrompt deps) |
| AgentTool/prompt.ts | ~565 | YES |
| AgentTool/resumeAgent.ts | ~320 | NO (resume only) |
| AgentTool/runAgent.ts | ~1,225 | partial (top 120 — orchestration mass) |
| AskUserQuestionTool/AskUserQuestionTool.tsx | ~1,340 | partial (top 150) |
| AskUserQuestionTool/prompt.ts | ~98 | YES |
| BashTool/BashTool.tsx | ~5,400 | partial (top 120) |
| BashTool/BashToolResultMessage.tsx | ~640 | NO (render) |
| BashTool/UI.tsx | ~850 | NO (render) |
| BashTool/bashCommandHelpers.ts | ~295 | YES |
| BashTool/bashPermissions.ts | ~3,380 | NO (huge — pattern matching & permission, capability captured via prompt+modeValidation) |
| BashTool/bashSecurity.ts | ~3,505 | NO (huge — same as above) |
| BashTool/commandSemantics.ts | ~140 | YES |
| BashTool/commentLabel.ts | ~14 | YES |
| BashTool/destructiveCommandWarning.ts | ~103 | YES |
| BashTool/modeValidation.ts | ~115 | YES |
| BashTool/pathValidation.ts | ~1,500 | NO |
| BashTool/prompt.ts | ~715 | YES |
| BashTool/readOnlyValidation.ts | ~2,345 | NO |
| BashTool/sedEditParser.ts | ~330 | YES |
| BashTool/sedValidation.ts | ~740 | NO |
| BashTool/shouldUseSandbox.ts | ~180 | YES |
| BashTool/toolName.ts | ~3 | YES |
| BashTool/utils.ts | ~225 | YES |
| BriefTool/BriefTool.ts | ~265 | YES |
| BriefTool/UI.tsx | ~480 | NO (render) |
| BriefTool/attachments.ts | ~135 | YES |
| BriefTool/prompt.ts | ~65 | YES |
| BriefTool/upload.ts | ~200 | YES |
| ConfigTool/ConfigTool.ts | ~465 | YES |
| ConfigTool/UI.tsx | ~190 | NO (render) |
| ConfigTool/constants.ts | ~2 | YES |
| ConfigTool/prompt.ts | ~100 | YES |
| ConfigTool/supportedSettings.ts | ~220 | YES |
| CtxInspectTool/CtxInspectTool.ts | 2 | YES (stub `export default {}`) |
| DiscoverSkillsTool/prompt.ts | 2 | YES (stub `export default ''`) |
| EnterPlanModeTool/EnterPlanModeTool.ts | ~140 | YES |
| EnterPlanModeTool/UI.tsx | ~180 | NO (render) |
| EnterPlanModeTool/constants.ts | ~3 | YES |
| EnterPlanModeTool/prompt.ts | ~265 | YES |
| EnterWorktreeTool/EnterWorktreeTool.ts | ~150 | YES |
| EnterWorktreeTool/UI.tsx | ~110 | NO (render) |
| EnterWorktreeTool/constants.ts | ~3 | YES |
| EnterWorktreeTool/prompt.ts | ~50 | YES |
| ExitPlanModeTool/ExitPlanModeV2Tool.ts | ~580 | partial (top 250) |
| ExitPlanModeTool/UI.tsx | ~380 | NO (render) |
| ExitPlanModeTool/constants.ts | ~5 | YES |
| ExitPlanModeTool/prompt.ts | ~70 | YES |
| ExitWorktreeTool/ExitWorktreeTool.ts | ~400 | YES |
| ExitWorktreeTool/UI.tsx | ~135 | NO (render) |
| ExitWorktreeTool/constants.ts | ~3 | YES |
| ExitWorktreeTool/prompt.ts | ~70 | YES |
| FileEditTool/FileEditTool.ts | ~705 | YES |
| FileEditTool/UI.tsx | ~1,170 | NO (render) |
| FileEditTool/constants.ts | ~13 | YES |
| FileEditTool/prompt.ts | ~65 | YES |
| FileEditTool/types.ts | ~90 | YES |
| FileEditTool/utils.ts | ~775 | partial (top 120 — quote norm) |
| FileReadTool/FileReadTool.ts | ~1,340 | partial (top 300 + tail 200 — schemas, dedup, image/PDF/notebook) |
| FileReadTool/UI.tsx | ~755 | NO (render) |
| FileReadTool/imageProcessor.ts | ~100 | NO (capability inferred from prompt) |
| FileReadTool/limits.ts | ~110 | YES |
| FileReadTool/prompt.ts | ~100 | YES |
| FileWriteTool/FileWriteTool.ts | ~510 | partial (read prompt+ts shape) |
| FileWriteTool/UI.tsx | ~1,470 | NO (render) |
| FileWriteTool/prompt.ts | ~35 | YES |
| GlobTool/GlobTool.ts | ~210 | YES |
| GlobTool/UI.tsx | ~270 | NO (render) |
| GlobTool/prompt.ts | ~15 | YES |
| GrepTool/GrepTool.ts | ~690 | partial (top 200 + 200..500 — schema, head_limit, args build) |
| GrepTool/UI.tsx | ~735 | NO (render) |
| GrepTool/prompt.ts | ~40 | YES |

**TOTAL files in slice: 81 files.** Approx LOC: ~52,000 (incl. UI/render). Logic LOC scanned in full or near-full: ~10,500. UI/render LOC (deliberately skimmed — not portable to ipynb canonical UI): ~13,000. Largest unscanned-in-full files (`bashPermissions`, `bashSecurity`, `pathValidation`, `readOnlyValidation`, `sedValidation`) are the bash safety stack — capability captured at the contract level via `prompt.ts` + `modeValidation.ts` + `destructiveCommandWarning.ts` + `shouldUseSandbox.ts` + `commandSemantics.ts`; full-port not appropriate for SageMaker single-user (see drops).

---

## Capabilities table

Legend for "Target Block": refers to existing v3 plan blocks. "NEW" = capability not yet in plan and being proposed. "DROP" = capability incompatible with SageMaker constraints.

### AgentTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 1 | `Agent` tool name (legacy alias `Task`) | constants.ts:1-3 | Partial — v4 uses `task` (line 8278+) | Y — rename to `Agent` for cache parity & wire-name with skills/hooks | Block A (sub-agent) | Add LEGACY alias map: `task→Agent` so old transcripts replay. |
| 2 | Sub-agent definition shape (whenToUse / tools / disallowedTools) | loadAgentsDir.ts (header), prompt.ts:43-46 | v4 has `AGENT_TYPES` dict (sagemaker_agent.py:7387 enum) | Y — adopt `tools` allowlist + `disallowedTools` denylist per-agent | Block A | Replace v4 `AGENT_TYPES` dict with frontmatter-loaded definitions; tools∩denylist filter mirrors `getToolsDescription`. |
| 3 | `formatAgentLine` — inline agent listing in tool prompt | prompt.ts:43-46 | NO | Y — tool description builds from agent list at startup | Block A | Mirror `getPrompt(effectiveAgents)`; v4 currently inlines static AGENT_TYPES enum. |
| 4 | `shouldInjectAgentListInMessages` — agent list as attachment vs inline (cache-bust avoidance) | prompt.ts:59-64 | NO | N — single-user SM has stable agent list at startup; no MCP/plugin churn | N/A | DROP — keep inline (no cache churn risk in SM). |
| 5 | `forkEnabled` / `FORK_AGENT` — implicit fork inheriting parent context | forkSubagent.ts:32-72 | v4 line 7364 mentions `fork` agent type but no inheritance logic | Y — fork is the cache-cheapest sub-agent path | Block A NEW: fork sub-block | Port `buildForkedMessages` (assistant_msg + placeholder tool_results + directive). v4 needs to pass parent's full message list to fork child unchanged. |
| 6 | `FORK_PLACEHOLDER_RESULT` — byte-identical placeholder for cache sharing | forkSubagent.ts:93 | NO | Y — directly enables prompt cache reuse on Bedrock | Block A fork | Constant string; child API request prefix is byte-identical except final directive. **Bedrock cache_control compatible.** |
| 7 | `isInForkChild` — guard against recursive forks via boilerplate tag detection | forkSubagent.ts:78-89 | NO | Y | Block A fork | Inspect msg history for `<fork-boilerplate>` tag. |
| 8 | `buildChildMessage` — directive-mode child prompt rules (10 rules; "Scope:" output format) | forkSubagent.ts:171-198 | NO | Y — concrete fork worker contract | Block A fork | Port verbatim; aligns with v4's own /nonstop reporting style. |
| 9 | `buildWorktreeNotice` — fork-in-worktree path translation notice | forkSubagent.ts:205-210 | NO | Conditional — only if Block J (worktree) ships | Block J | Port if worktree adopted. |
| 10 | Persistent agent memory (`user`/`project`/`local` scopes) — `agentMemory.ts` | agentMemory.ts:13-177 | v4 has `memory.md` global only (no per-agent scoping) | Y — Hermes-axis improvement; per-agent memory critical for verify/review agents to learn | Block M (memory) ENHANCE | Port `getAgentMemoryDir(scope)` with paths `<workspace>/.claude/agent-memory/<agentType>/MEMORY.md` (project) and `~/.claude/agent-memory/<agentType>/MEMORY.md` (user). Local scope can DROP for SM (no VCS distinction needed). |
| 11 | `loadAgentMemoryPrompt` — inject scoped memory in agent system prompt | agentMemory.ts:138-177 | v4 injects `memory.md` into main agent prompt only | Y | Block M | Each agent definition with `memory: project|user` triggers prompt injection at spawn. |
| 12 | `isAgentMemoryPath` — path-traversal-safe memory dir check | agentMemory.ts:68-104 | NO (no per-agent memory) | Y | Block M | Port `path.normalize` based check; security-relevant. |
| 13 | `sanitizeAgentTypeForPath` — colon→dash for plugin agent types on Windows | agentMemory.ts:20-22 | NO | Y if plugin namespace used | Block M | Port. |
| 14 | Memory snapshot sync (project→local) — `agentMemorySnapshot.ts` | agentMemorySnapshot.ts:1-198 | NO | N — single-user SM doesn't need team memory sync | N/A | DROP. |
| 15 | `builtInAgents` — built-in agent registry (general-purpose, statusline-setup, explore, plan, code-guide, verification) | builtInAgents.ts:22-72 | v4 has 7 hardcoded types incl. fork/build/general/explore/plan/review/verify (line 7353-7365) | Y but v4's set is already richer | Block A | Keep v4 set; cherry-pick `claude-code-guide` only if user-facing. |
| 16 | `agentColorManager` — assign color per agent type for UI | agentColorManager.ts:1-67 | NO (chat.ipynb has no per-agent colors) | OPTIONAL — chat.ipynb canonical UI could benefit (8-color palette) | Block A polish | Port to ipywidgets palette; non-blocking. |
| 17 | `agentDisplay.AGENT_SOURCE_GROUPS` — agent precedence (user>project>local>policy>plugin>flag>built-in) | agentDisplay.ts:24-32 | NO (single source) | Conditional — only if multi-source agents adopted | Block A | DROP for v5.0.1 (single source). |
| 18 | `resolveAgentOverrides` — annotate which source overrode an agent | agentDisplay.ts:46-72 | NO | N | N/A | DROP. |
| 19 | `ONE_SHOT_BUILTIN_AGENT_TYPES` — skip agentId/SendMessage trailer for one-shot agents | constants.ts:9-12 | NO | Y — token-saver for explore/plan in v4 | Block A | Tag `explore`, `plan`, `verify` as one-shot in agent registry; sub-agent runner skips trailer for these. |
| 20 | `getPrompt(isCoordinator)` — slim vs full prompt | prompt.ts:202-213 | NO | Y | Block A | Coordinator gets shared block only; non-coordinator gets full when-not-to-use + writing-the-prompt. |
| 21 | "Writing the prompt" guidance — never delegate understanding, give file:line | prompt.ts:99-113 | YES — already in v4 line 7377-7383 | Already in plan | Block A | KEEP v4's text (parity); cross-check forkEnabled branch for fork-specific tweaks. |
| 22 | `getActivityDescription` / `getToolUseSummary` — tool description for status line | (across all tools) | NO | OPTIONAL | Block A polish | Skip for ipynb canonical UI unless added to status sidebar. |
| 23 | `run_in_background` parameter — background sub-agent | AgentTool.tsx:87 | NO | OPTIONAL — single-user SM rarely needs this | Block A | DROP for v5.0.1; revisit if cell UI grows async support. |
| 24 | `isolation: "worktree"` parameter | AgentTool.tsx:99 | NO | Conditional | Block J | Surface only if Block J ships. |
| 25 | `isolation: "remote"` (CCR remote env) | AgentTool.tsx:99 | NO | N — Bedrock-only, no remote execution surface | N/A | DROP. |
| 26 | Agent-specific MCP servers (frontmatter `mcpServers`) | runAgent.ts:96-130 | NO | N — Bedrock-only, no external MCP | N/A | DROP. |
| 27 | `assembleToolPool(agentDef)` — per-agent tool subset assembly | AgentTool.tsx:16 import | v4 has `agent_tools` filter (line 8370-8372) | Already in v4 | N/A | KEEP v4 logic. |
| 28 | `cwd` parameter for sub-agent | AgentTool.tsx:100 | NO | N — single workspace | N/A | DROP. |

### AskUserQuestionTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 29 | Multiple-choice question shape (1-4 questions × 2-4 options) | AskUserQuestionTool.tsx:62-67 | v4 `tool_ask_user` is single Q/A free text + flat options list (line 6743) | Y — structured multiselect saves tokens | Block A NEW | Replace v4 `tool_ask_user` schema with `{questions: [{question, header, options:[{label,description,preview?}], multiSelect}]}`. Wire ipywidgets: list of questions, radio/checkbox per question. |
| 30 | `header` (≤12-char chip), `description` (per option), `preview` (markdown/HTML side-by-side) | AskUserQuestionTool.tsx:21-22 | NO | Partial — preview low priority for ipynb | Block A NEW | header+description Y; preview OPTIONAL (would need ipywidgets HBox of monospace box). |
| 31 | "Other" option auto-injected at runtime | prompt.ts:38-40 | NO | Y | Block A NEW | UI layer adds "Other → text input" as last option. |
| 32 | UNIQUENESS_REFINE — reject duplicate question/option labels | AskUserQuestionTool.tsx:32-54 | NO | Y — defensive | Block A NEW | Port zod refine to JSON-schema validator. |
| 33 | Plan-mode rule: don't ask "Is plan ready?" — use `ExitPlanMode` instead | prompt.ts:42 | NO (no plan mode) | Conditional on Block C+ adopting EnterPlanMode | Block C+ | Doc-only; no code change. |
| 34 | `annotations` — per-Q free-text notes from user | AskUserQuestionTool.tsx:25-30 | NO | OPTIONAL — nice-to-have | Block A NEW | Add `notes` text input under each question. |
| 35 | Disabled when `--channels` active (Telegram/Discord) | AskUserQuestionTool.tsx:135-143 | N/A | N | N/A | DROP. |

### BashTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 36 | Tool-preference items (Glob>find, Grep>grep, Read>cat, Edit>sed, Write>echo) | prompt.ts:280-291 | v4 has implicit guidance in skill prompts but not in bash prompt | Y — token-saver, prevents wasteful subprocess fallbacks | Block B | Append to v4 bash tool description. |
| 37 | "Avoid using this tool to run X commands" + dedicated tool list | prompt.ts:354-362 | Partial | Y | Block B | Add to v4 bash description. |
| 38 | Multiple-commands subitems (parallel calls in one message; `&&` chains; `;` ignores fails; no newlines) | prompt.ts:297-302 | NO (v4 prompt is silent on chaining) | Y — improves tool-call efficiency | Block B | Add to v4 bash description. |
| 39 | Git subitems — new commits not amend, never `-A`, never skip hooks | prompt.ts:304-308 | Partial — v4 system prompt has git rules (line 8050+) | Already partly in plan | Block B/sysprompt | Cross-link with v4 system prompt; dedupe. |
| 40 | Sleep subitems — Monitor tool / `run_in_background` / no retry-loops / `sleep N>=2` blocked | prompt.ts:310-328 | NO | Y partial — block long sleep at first command | Block B | Add to v4 bash description. Note: Monitor tool itself is OUT (see drops below). |
| 41 | `getDefaultBashTimeoutMs` / `getMaxBashTimeoutMs` — runtime timeout config | prompt.ts:27-33 | v4 has hardcoded timeout (line 5239+) | Y — make configurable | Block B | Move to CONFIG. |
| 42 | Background usage note — `run_in_background` parameter | prompt.ts:35-40 | NO | OPTIONAL | Block B | DROP for v5.0.1. |
| 43 | Dedup wrapper for sandbox config (`/tmp` deduping, `$TMPDIR` substitution to keep cache stable across users) | prompt.ts:166-202 | N/A (no sandbox in SM) | N | N/A | DROP. |
| 44 | Sandbox section in prompt (allowOnly/denyWithinAllow) | prompt.ts:172-273 | N/A | N | N/A | DROP. |
| 45 | `dangerouslyDisableSandbox` parameter | shouldUseSandbox.ts:12-16 | N/A | N | N/A | DROP. |
| 46 | Embedded find/grep aliasing (`hasEmbeddedSearchTools`) | prompt.ts:281-291 | N/A | N | N/A | DROP. |
| 47 | Commit & PR instructions — undercover stripping, attribution texts | prompt.ts:42-160 | Partial | OPTIONAL — most is git protocol that v4 inherits via system prompt | Block B/sysprompt | Cherry-pick "Use HEREDOC" + "no -uall" + "no `-i` flag" guidance into v4 system prompt. DROP `getUndercoverInstructions`. |
| 48 | `extractBashCommentLabel` — first-line `# comment` becomes UI label | commentLabel.ts:8-13 | NO | Y — small, useful for chat.ipynb history | Block B polish | Port verbatim. |
| 49 | `interpretCommandResult` — per-command exit-code semantics (grep 1=no match, find 1=partial, diff 1=differs, test 1=false) | commandSemantics.ts:1-140 | NO | Y — prevents v4 from treating `grep` 1 as error | Block B | Port verbatim. Affects `tool_bash` post-process. |
| 50 | `getDestructiveCommandWarning` — pattern catalog (rm -rf, git push --force, DROP TABLE, kubectl delete, terraform destroy, …) | destructiveCommandWarning.ts:12-89 | Partial (v4 SECURITY blocks some) | Y — display in approval dialog | Block B | Port table; v4 chat.ipynb approval HBox already has 2 buttons → add warning text above. |
| 51 | `checkPermissionMode` — Accept-Edits mode auto-allows mkdir/touch/rm/rmdir/mv/cp/sed | modeValidation.ts:7-115 | NO (v4 has 4 trust modes but not Accept-Edits) | Y — Hermes-axis | Block B+ | Add `acceptEdits` mode to v4 PermissionMode enum. Auto-allow filesystem-only commands. |
| 52 | `bashCommandIsSafeAsync_DEPRECATED` — full bash AST safety check | bashCommandHelpers.ts → bashSecurity.ts | Partial — v4 has SECURITY.is_command_allowed (line 1298+) | Y but DEEP-PORT not advisable | Block B | Keep v4's regex-based check; cherry-pick `interpretCommandResult` + `getDestructiveCommandWarning` only. Full AST port = 5K+ LOC, low ROI for single-user. |
| 53 | Cd+git compound detection (bare-repo fsmonitor bypass guard) | bashCommandHelpers.ts:50-82 | NO | Y — security bug class | Block B | Port `if hasCd && hasGit → ask` guard. ~40 LOC. |
| 54 | Multiple-cd detection — `cd a && cd b && X` requires approval | bashCommandHelpers.ts:32-47 | NO | Y | Block B | Port. ~10 LOC. |
| 55 | Pipe-segment per-segment permission check + suggestion aggregation | bashCommandHelpers.ts:84-156 | NO | Y partial | Block B | Add "split on `\|`, check each segment" — improves accuracy on `cmd1 \| cmd2` where v4 currently checks whole string. |
| 56 | `parseSedEditCommand` / `applySedSubstitution` — render `sed -i` as virtual edit + apply | sedEditParser.ts:1-322 | NO | OPTIONAL — model is told to use `Edit` not `sed`, so rare | Block B polish | DROP unless Block B+ adds bash sed-edit recognition. |
| 57 | `stripEmptyLines` / `formatOutput` (truncated_content with "[N lines truncated]") | utils.ts:22-165 | v4 has truncation (line 5300+) | Y — adopt the "[N lines truncated]" format | Block B | Tweak v4's truncation message format. |
| 58 | `isImageOutput` / `parseDataUri` / `buildImageToolResult` — bash stdout containing `data:image/...` returns as image | utils.ts:49-91 | NO | OPTIONAL — useful if user runs matplotlib in bash | Block B polish | Port; rare path but cheap to add. |
| 59 | `resizeShellImageOutput` — re-encode large image stdout (matplotlib dpi=300 path) | utils.ts:110-131 | NO | OPTIONAL | Block B polish | Skip unless image-output adopted. |
| 60 | `MAX_IMAGE_FILE_SIZE` 20 MB stdout cap | utils.ts:96 | NO | OPTIONAL | Block B polish | Same. |
| 61 | `resetCwdIfOutsideProject` — auto-cd back if `cd` left allowed working dir | utils.ts:170-192 | Partial — v4 SECURITY blocks paths but doesn't auto-reset cwd | Y | Block B | Port; prevents cwd drift in long sessions. |
| 62 | `stdErrAppendShellResetMessage` — tell model when shell cwd was reset | utils.ts:167-168 | NO | Y | Block B | Same. |
| 63 | `createContentSummary` — MCP content block summary | utils.ts:198-223 | N/A (no MCP in v5) | N | N/A | DROP. |
| 64 | `BASH_SEARCH_COMMANDS` / `BASH_READ_COMMANDS` / `BASH_LIST_COMMANDS` / `BASH_SEMANTIC_NEUTRAL_COMMANDS` / `BASH_SILENT_COMMANDS` sets | BashTool.tsx:60-81 | NO | Y — used to mark tool-results for collapsibility / silent expectation | Block B polish | Port the sets; chat.ipynb collapsibles can use them. |
| 65 | `isSearchOrReadBashCommand` — pipeline-aware classifier | BashTool.tsx:95-153 | NO | OPTIONAL | Block B polish | Skip unless ipynb adds collapsibles. |
| 66 | `containsExcludedCommand` (settings excluded commands list) | shouldUseSandbox.ts:20-128 | NO (no sandbox) | N | N/A | DROP. |
| 67 | `BINARY_HIJACK_VARS` strip + wrapper strip + iterative fixed-point | shouldUseSandbox.ts:80-101 | NO | N | N/A | DROP. |
| 68 | `parseForSecurity` AST → `getTreeSitterAnalysis` (subshells, command groups detection) | bashCommandHelpers.ts → utils/bash/parser.ts | NO | OPTIONAL | Block B+ | DEFER — heavy port; v4's regex-based unsafe-compound check is "good enough" for trusted single-user. |

### BriefTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 69 | `SendUserMessage` (alias `Brief`) — primary user-facing reply channel + status='proactive'/'normal' | BriefTool.ts:136-204, prompt.ts:6-22 | NO — v4 streams text directly to chat | OPTIONAL — could improve clarity; "ack→work→result" pattern | Block A polish | DROP for v5.0.1 — chat.ipynb already shows assistant text top-level; adding a tool layer is a regression for ipynb canonical UI. |
| 70 | `BRIEF_PROACTIVE_SECTION` — "Talking to the user" prompt block | prompt.ts:12-22 | Partial — system prompt has chat-style guidance | OPTIONAL | Block A polish | Cherry-pick "ack first, then work, then send result" wording into v4 system prompt. |
| 71 | `validateAttachmentPaths` / `resolveAttachments` | attachments.ts:26-110 | NO | N | N/A | DROP — chat.ipynb attaches via ipywidgets file uploader, not tool-side. |
| 72 | `uploadBriefAttachment` to private_api `/api/oauth/file_upload` | upload.ts:1-175 | N/A | N — Bedrock-only, no Anthropic API | N/A | DROP. |
| 73 | `isBriefEntitled` / `isBriefEnabled` — KAIROS feature flag entitlement | BriefTool.ts:88-134 | N/A | N | N/A | DROP. |

### ConfigTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 74 | Get/set runtime settings via tool (theme/model/permissions.defaultMode/verbose/etc.) | ConfigTool.ts:67-434 | NO | OPTIONAL — chat.ipynb has manual `CONFIG` editing | Block C polish | DROP for v5.0.1 — chat.ipynb canonical UI exposes CONFIG at top of notebook; adding a tool is redundant. |
| 75 | `SUPPORTED_SETTINGS` registry shape (source/type/options/validateOnWrite/formatOnRead/appStateKey) | supportedSettings.ts:14-186 | NO | OPTIONAL | Block C polish | Document as patterns for future config UX; do not implement now. |
| 76 | `validateModel` async — checks Bedrock model ID is valid | supportedSettings.ts:104 | Partial — v4 has hardcoded MODEL list | OPTIONAL | Block C polish | Add startup-time Bedrock list-foundation-models probe; reject unknown model IDs early. |
| 77 | `permissions.defaultMode: 'auto'` (TRANSCRIPT_CLASSIFIER) | supportedSettings.ts:117-119 | NO | N — auto-classifier requires LLM-grade classifier service | N/A | DROP. |
| 78 | `voiceEnabled` setting | supportedSettings.ts:144-152 | N/A | N | N/A | DROP. |
| 79 | `remoteControlAtStartup` setting (BRIDGE_MODE) | supportedSettings.ts:153-163 | N/A | N | N/A | DROP. |
| 80 | `taskCompleteNotifEnabled` / `inputNeededNotifEnabled` / `agentPushNotifEnabled` (KAIROS push) | supportedSettings.ts:164-185 | N/A | N | N/A | DROP. |
| 81 | `ConfigTool.shouldDefer = true` — deferred-tool pattern | ConfigTool.ts:86 | NO | Conditional — only if any deferred tool ports | (varies) | Note that several Runnable tools use `shouldDefer` to delay schema announcement until activation. v5 sub-agent runtime can use this for verify/etc. |

### CtxInspectTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 82 | (file is `export default {}`) — STUB | CtxInspectTool.ts:1 | YES — v4 has Compactor + ContextManager | N | N/A | DROP — Runnable's CtxInspectTool is a no-op stub. v4's compactor (line 186+) and ContextManager (line 3464+) already do better. |

### DiscoverSkillsTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 83 | (file is `export default ''`) — STUB | DiscoverSkillsTool/prompt.ts:1 | YES — v4 has SkillManager (line 2684+) and `tool_skill` (line 6674+) | N | N/A | DROP — Runnable's discovery happens via `loadSkillsDir` + `discoverSkillDirsForPaths` triggered from FileEditTool/FileReadTool, not via this tool. Capability handled inside file tools (see #112 below). |

### EnterPlanModeTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 84 | `EnterPlanMode` — switches PermissionMode to `plan`, returns workflow instructions | EnterPlanModeTool.ts:77-126 | v4 has PLAN_MODE_ALLOWED_TOOLS (line 6905) but no enter/exit tools | Y — formal mode-switch with user gate | Block C+ | Add `enter_plan_mode` tool to v4. Sets PERMISSION_MODE='plan'. Tool description = port prompt.ts (interview phase OR full WHAT_HAPPENS section). |
| 85 | "What Happens in Plan Mode" 6-step section | prompt.ts:4-14 | Partial — v4 plan_mode allowlist exists | Y | Block C+ | Inject as system-reminder when mode flips. |
| 86 | When-to-use criteria (7 categories incl. "If you would use AskUserQuestion to clarify approach, use EnterPlanMode") | prompt.ts:23-66 | NO | Y — concrete triggers help model use it | Block C+ | Port full criteria list. |
| 87 | When-NOT-to-use (typo, console.log, simple) | prompt.ts:58-65 | NO | Y | Block C+ | Same. |
| 88 | `prepareContextForPlanMode` (auto-mode classifier activation) | EnterPlanModeTool.ts:11 | N/A | N — TRANSCRIPT_CLASSIFIER off | N/A | DROP. |
| 89 | Disabled in agent contexts (`context.agentId`) | EnterPlanModeTool.ts:78-80 | NO | Y — sub-agents can't enter plan mode | Block C+ | Port guard. |
| 90 | Disabled when `--channels` active | EnterPlanModeTool.ts:60-66 | N/A | N | N/A | DROP. |
| 91 | `handlePlanModeTransition` — telemetry hook | EnterPlanModeTool.ts:83 | NO | OPTIONAL | Block C+ | Add audit log entry for plan-mode transitions. |

### EnterWorktreeTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 92 | `EnterWorktree` — create `.claude/worktrees/<slug>` git worktree, switch session cwd | EnterWorktreeTool.ts:77-119 | NO | Conditional — only valuable if SM workspace is git-repo (rare for shared notebooks) | Block J | DROP for v5.0.1 — SM workspace usually `/home/sagemaker-user/`, not a git repo. Block J was already conditional in plan v3. |
| 93 | `validateWorktreeSlug` — letters/digits/dots/_-/, ≤64 chars, "/"-segmented | EnterWorktreeTool.ts:27-37 | N/A | N | N/A | DROP. |
| 94 | Hooks-based VCS-agnostic isolation (WorktreeCreate/WorktreeRemove hooks) | prompt.ts:21-22 | N/A | N | N/A | DROP. |
| 95 | `clearSystemPromptSections` / `clearMemoryFileCaches` / `getPlansDirectory.cache.clear` on cwd-change | EnterWorktreeTool.ts:99-101 | NO | OPTIONAL — only if cwd-cached state exists in v5 | Block M | Note for Block M: if memory.md per-cwd cached, must invalidate on cwd-change. Today v4 isn't cwd-cached so N/A. |
| 96 | `findCanonicalGitRoot` — resolve to main repo root before worktree-add | EnterWorktreeTool.ts:84-89 | N/A | N | N/A | DROP. |

### ExitPlanModeTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 97 | `ExitPlanModeV2` — present plan from disk for approval, then switch to default mode | ExitPlanModeV2Tool.ts:147-244+ | NO | Y | Block C+ | Pair with #84. Plan content read from `<plansDir>/<slug>.md` (written by model during plan mode, via `Write`/`Edit`). Tool itself takes no `plan` param. |
| 98 | Plan persisted to disk (`getPlanFilePath`); SDK injects `plan`/`planFilePath` via `normalizeToolInput` | ExitPlanModeV2Tool.ts:97-108, 246 | NO | Y | Block C+ | Port `getPlansDirectory` returning `.claude/plans/`. Hook v4's normalizer to read content. |
| 99 | `allowedPrompts` parameter — semantic Bash permissions (`{tool: 'Bash', prompt: 'run tests'}`) | ExitPlanModeV2Tool.ts:64-89 | NO | OPTIONAL — needs LLM-grade classifier | Block C+ NEW | Conditional — adopt only if Block B+ adds prompt-based permissions. Otherwise DROP. |
| 100 | `validateInput` — reject if not currently in plan mode | ExitPlanModeV2Tool.ts:195-220 | NO | Y | Block C+ | Port. |
| 101 | `requiresUserInteraction` true for non-teammates | ExitPlanModeV2Tool.ts:185-194 | NO | Y | Block C+ | chat.ipynb shows approval HBox (Approve/Edit/Reject). |
| 102 | `planWasEdited` flag — true when user edited plan in CCR web UI | ExitPlanModeV2Tool.ts:125-130 | N/A | OPTIONAL — if chat.ipynb approval lets user edit textarea, mirror flag | Block C+ | Add edit-textarea to approval widget. |
| 103 | Teammate plan-approval mailbox routing | ExitPlanModeV2Tool.ts:38-40, 197 | N/A | N | N/A | DROP. |
| 104 | `setHasExitedPlanMode` / `setNeedsAutoModeExitAttachment` — session-state telemetry | ExitPlanModeV2Tool.ts:9 | NO | OPTIONAL | Block C+ | Add session flag. |

### ExitWorktreeTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 105 | `ExitWorktree` action `keep|remove` + `discard_changes` flag | ExitWorktreeTool.ts:30-44 | N/A | Conditional on Block J | Block J | DROP for v5.0.1. |
| 106 | `countWorktreeChanges` — fail-closed on git-status/rev-list error (returns null = unsafe) | ExitWorktreeTool.ts:79-113 | N/A | N | N/A | DROP. |
| 107 | Tmux session kill-on-remove / keep-on-keep | ExitWorktreeTool.ts:24-25 | N/A | N | N/A | DROP. |
| 108 | `restoreSessionToOriginalCwd` — restores cwd, projectRoot, hooks snapshot, prompt sections, memory caches | ExitWorktreeTool.ts:122-146 | N/A | N | N/A | DROP. |
| 109 | `isDestructive(input)` — true when `action === 'remove'` (drives auto-classifier) | ExitWorktreeTool.ts:168-170 | NO | OPTIONAL — pattern useful for v5 destructive-tool tagging | Block B | Note pattern: tools self-declare `isDestructive(input)` for permission-mode logic. |

### FileEditTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 110 | Pre-read enforcement — error if file not in `readFileState` before edit | FileEditTool.ts:275-287 | YES — v4 line 4291+ tracks `_FILE_READ_TIMES` | KEEP | Block C | v4 already does this — verify message wording matches Runnable's "Read it again before attempting to write it." |
| 111 | Staleness check — error if file mtime > last-read mtime, with content-fallback for Windows cloud-sync false positives | FileEditTool.ts:289-311 | Partial — v4 line 4348 sets mtime on read, but no Windows content-fallback | Y — Windows fix | Block C | Port the `isFullRead && fileContent === readTimestamp.content` fallback for Windows OneDrive/antivirus mtime spurious bumps. |
| 112 | Skill discovery on every edit (`discoverSkillDirsForPaths` + `activateConditionalSkillsForPaths`) | FileEditTool.ts:404-423 | NO | Y — auto-loads skills based on edited path | Block C/skills | Port; replaces v4's static skill registry with path-triggered activation. |
| 113 | LSP `didChange` + `didSave` notification post-write | FileEditTool.ts:494-514 | N/A — no LSP in SM | N | N/A | DROP. |
| 114 | `notifyVscodeFileUpdated` MCP push | FileEditTool.ts:517 | N/A | N | N/A | DROP. |
| 115 | `findActualString` — quote-normalized match (curly→straight) | utils.ts:73-93 | NO | Y — model frequently emits curly quotes after copy-paste | Block C | Port verbatim. ~20 LOC. |
| 116 | `preserveQuoteStyle` — if file uses curly quotes, re-wrap new_string with curly | utils.ts:104-120 | NO | Y | Block C | Port; preserves user typography. |
| 117 | `normalizeQuotes` / `LEFT_*_CURLY_QUOTE` constants | utils.ts:21-37 | NO | Y | Block C | Port. |
| 118 | `replace_all` boolean parameter | types.ts:15-17 | YES — v4 supports `replace_all` | KEEP | N/A | Already in v4. |
| 119 | Multiple-match detection — count matches, ask if >1 and !replace_all, return `{actualOldString}` for retry | FileEditTool.ts:329-343 | YES — v4 line 4729+ has multi-match logic | Verify parity | Block C | Cross-check error message format. |
| 120 | `MAX_EDIT_FILE_SIZE = 1 GiB` byte-stat guard pre-edit | FileEditTool.ts:84, 186-200 | Partial — v4 has `max_file_size` config | Y — distinguish edit-cap from read-cap | Block C | Add separate edit-cap. |
| 121 | UTF-16 LE BOM detection (`0xFF 0xFE`) | FileEditTool.ts:208-214 | NO | Y — Windows files | Block C | Port; without it, edits to Notepad-saved files fail silently. |
| 122 | `\r\n` → `\n` normalization on read; `writeTextContent` preserves original line endings | FileEditTool.ts:214 + utils/file.ts | Partial — v4 reads with errors='replace' | Y — improve | Block C | Port `readFileSyncWithMetadata` shape: returns `{content, encoding, lineEndings}` so writes restore original. |
| 123 | UNC path skip on Windows (NTLM credential leak prevention) | FileEditTool.ts:179-181 | NO | Y — Windows defensive | Block C | Port; ~3 LOC. |
| 124 | Reject edit on `.ipynb` — must use `NotebookEdit` | FileEditTool.ts:266-273 | v4 has `tool_notebook_edit` (line 5921) | Verify | Block C | Add same guard. |
| 125 | `validateInputForSettingsFileEdit` — Claude settings file schema validation pre-write | FileEditTool.ts:346-359 | NO | OPTIONAL | Block C polish | DROP unless Block C+ ships settings tooling. |
| 126 | `checkTeamMemSecrets` — reject edits to team memory that introduce secrets | FileEditTool.ts:144-147 | N/A | N | N/A | DROP. |
| 127 | `fileHistoryEnabled` / `fileHistoryTrackEdit` — pre-edit content hash backup for rewind | FileEditTool.ts:431-440 | NO | Y — Hermes-axis safety | Block C+ NEW | Port: write `<workspace>/.claude/file-history/<hash>.bak` before each edit. Powers a `/rollback` command later. |
| 128 | `getPatchForEdit` — generates structured `diff` patch for UI rendering | utils.ts (header) | Partial — v4 returns string diff | Y | Block C | Port to return both string + structured hunks for chat.ipynb diff widget. |
| 129 | `findSimilarFile` + `suggestPathUnderCwd` — file-not-found suggestions | FileEditTool.ts:230-246 | YES — v4 has hint string at line 4276-4280 | Verify | Block C | Cross-check parity. |
| 130 | `expandPath` — `~` and relative path expansion at backfillObservableInput | FileEditTool.ts:115-121 | YES — v4 `_resolve_path` (line 4269) | KEEP | N/A | Already in v4. |
| 131 | `inputsEquivalent` — dedup check for edit retries | FileEditTool.ts:363-385 | NO | OPTIONAL | Block C polish | DROP. |
| 132 | `diagnosticTracker.beforeFileEdited` (LSP diagnostics replay) | FileEditTool.ts:425 | N/A | N | N/A | DROP. |
| 133 | `gitDiff` quartz-lantern remote experiment | FileEditTool.ts:545-558 | N/A | N | N/A | DROP. |
| 134 | `logEvent('tengu_write_claudemd')` analytics hook | FileEditTool.ts:528 | NO | N | N/A | DROP. |
| 135 | `mapToolResultToToolResultBlockParam` — "All occurrences were successfully replaced" vs "successfully" depending on `replaceAll` | FileEditTool.ts:575-594 | Partial | Y | Block C | Port message format. |

### FileReadTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 136 | `MAX_LINES_TO_READ = 2000` default + `offset`/`limit` params | prompt.ts:11, FileReadTool.ts:227-242 | YES — v4 line 4262 | KEEP | N/A | Already in v4. |
| 137 | `FILE_UNCHANGED_STUB` — return stub if same range re-read and mtime unchanged | prompt.ts:7-9, FileReadTool.ts:524-572 | YES — v4 line 4287-4304 | KEEP, verify dedup logic parity | Block C | Cross-check: Runnable dedups only when `existingState.offset !== undefined` (came from prior Read) and `!existingState.isPartialView`. v4 should match. |
| 138 | `tengu_read_dedup_killswitch` GB toggle | FileReadTool.ts:536-542 | N/A | N | N/A | DROP — keep dedup unconditional in SM. |
| 139 | Skill discovery on every read | FileReadTool.ts:575-591 | NO | Y | Block C/skills | Same as #112. |
| 140 | Image read (PNG/JPG/GIF/WEBP) returns `content: [{type:'image', source:base64}]` | FileReadTool.ts:248-298, 654-668 | v4 has `tool_view_image` (line 6419) separate tool | Y — fold into `Read` | Block C | Make `read_file` polymorphic on extension: text → text; image → image block. Bedrock supports image content blocks via Claude vision. |
| 141 | PDF read (single-blob ≤10 pages OR `pages: "1-5"` extraction) returns `DocumentBlockParam` | FileReadTool.ts:60-66, 305-313, 670-685 | NO | OPTIONAL — Bedrock Claude supports PDF document blocks | Block C polish | Add `pages` param. PDF in Bedrock is supported via document content. |
| 142 | Notebook (`.ipynb`) read — returns array of cells via `mapNotebookCellsToToolResult` | FileReadTool.ts:299-305, 670-671 | YES — v4 lines 4324-4339 parse notebook to text | Y — adopt structured cells | Block C | Replace v4's text-flatten with `cells: [{type, source, outputs}]` returned as multiple text blocks. Improves Bedrock comprehension. |
| 143 | Text result wraps with `CYBER_RISK_MITIGATION_REMINDER` system-reminder (skipped for opus-4-6) | FileReadTool.ts:729-738 | NO | Y — defensive against malware-as-input | Block C | Port; appends a `<system-reminder>` to every Read result. |
| 144 | `memoryFileFreshnessPrefix` — auto-memory files get age annotation | FileReadTool.ts:747-753 | NO | Y if Block M (memory) ports | Block M | Port. |
| 145 | `MaxFileReadTokenExceededError` — token-count check post-read (rough estimate + API tokenizer fallback) | FileReadTool.ts:175-185, 755-772 | Partial — v4 has byte-cap, not token-cap | Y — token cap is more accurate | Block C | Add token-cap with fallback to estimate; wire to Bedrock count_tokens. |
| 146 | `BLOCKED_DEVICE_PATHS` set — `/dev/zero`, `/dev/urandom`, `/dev/stdin`, `/proc/<pid>/fd/0-2` | FileReadTool.ts:98-128 | NO | Y — Linux SM defensive | Block C | Port. ~30 LOC. |
| 147 | `getAlternateScreenshotPath` — macOS thin-space U+202F retry for AM/PM screenshot filenames | FileReadTool.ts:147-159 | NO | OPTIONAL — only macOS users | Block C | DROP for SM (Linux). |
| 148 | UNC path skip | FileReadTool.ts:461-467 | NO | Y | Block C | Port. |
| 149 | Binary extension reject (`hasBinaryExtension`) | FileReadTool.ts:471-482 | NO | Y | Block C | Port; v4 currently reads any extension as text. |
| 150 | `IMAGE_EXTENSIONS` set | FileReadTool.ts:188 | YES (in v4 view_image) | KEEP | N/A | Re-use. |
| 151 | `parsePDFPageRange` validation (`"1-5"`, `"3"`, `"10-20"`) | FileReadTool.ts:418-440 | NO | OPTIONAL | Block C polish | Port if PDF read adopted. |
| 152 | `roughTokenCountEstimationForFileType` — language-aware char→token ratio | FileReadTool.ts:21-22 | Partial — v4 uses `len(s)//3` (line 3720) | Y — language-aware is more accurate | Block C | Port; improves token-cap accuracy. |
| 153 | `addLineNumbers` formatting — `cat -n` style with line-number prefix | prompt.ts:14, FileReadTool.ts:725-727 | YES — v4 prepends `i+1:4| line` | KEEP, verify format | N/A | Already in v4. Cross-check format: Runnable allows compact (line+TAB) or verbose (spaces+arrow); v4 uses `{i+1:4}|` — fine. |
| 154 | `OFFSET_INSTRUCTION_TARGETED` vs `OFFSET_INSTRUCTION_DEFAULT` (GrowthBook nudge) | prompt.ts:17-21 | NO | OPTIONAL | Block C polish | Adopt targeted-range wording in v4 prompt. |
| 155 | `getFileReadIgnorePatterns` — `.gitignore`+`.claudeignore`-aware path-deny rules | FileReadTool.ts:67-71 | NO | OPTIONAL | Block C polish | DROP unless Block B+ adds permission rules. |
| 156 | `registerFileReadListener` — file-read pubsub for other services | FileReadTool.ts:165-173 | NO | N | N/A | DROP. |
| 157 | Empty-file warning — `<system-reminder>Warning: file exists but contents are empty.</system-reminder>` | FileReadTool.ts:705-707 | NO | Y | Block C | Port; matches Runnable's behavior. |
| 158 | `tengu_amber_wren` GB-driven `maxSizeBytes`/`maxTokens` override | limits.ts:53-92 | N/A | N | N/A | DROP — fix at CONFIG. |

### FileWriteTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 159 | Pre-read requirement for existing files | prompt.ts:6-8 | YES — v4 enforces | KEEP | N/A | Already in v4. |
| 160 | "Prefer Edit for existing files" | prompt.ts:14-15 | NO | Y | Block C | Add to v4 write tool description. |
| 161 | "NEVER create *.md / README unless explicitly requested" | prompt.ts:16 | NO | Y — saves token churn from gold-plating | Block C | Add. |
| 162 | "Only use emojis if user explicitly requests" | prompt.ts:17 | NO | Y | Block C | Add. |
| 163 | Overwrites existing file | prompt.ts:14 | YES | KEEP | N/A | — |

### GlobTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 164 | Glob pattern returns `filenames` (relative paths) sorted by mtime | GlobTool.ts:154-165 | YES — v4 line 4846 | Verify mtime sort + relativize | Block C | Cross-check; ensure v4 sorts by mtime. |
| 165 | `truncated: true` flag at 100 results + suggestion message | GlobTool.ts:39-51, 187-195 | Partial — v4 may already cap | Verify cap+message | Block C | Add `truncated` flag and "(Results are truncated...)" suffix. |
| 166 | Path validation: must exist + must be directory | GlobTool.ts:94-131 | YES | Verify | Block C | Cross-check error messages. |
| 167 | `getGlobExclusionsForPluginCache` — orphaned plugin filter | GlobTool.ts:20 | N/A | N | N/A | DROP. |
| 168 | UNC path skip | GlobTool.ts:100-103 | NO | Y | Block C | Port. |
| 169 | "Use Agent for open-ended search" prompt nudge | prompt.ts:7 | NO | Y | Block C | Add to v4 glob description. |
| 170 | `toRelativePath` — convert absolute to relative (token-saver) | GlobTool.ts:165 | Partial | Y | Block C | Cross-check; v4 should always relativize. |

### GrepTool

| # | Capability | Source file:line | v4 has? | v5.0.1 needs? | Target Block | Graft strategy on v4 |
|---|---|---|---|---|---|---|
| 171 | Ripgrep-backed search (NOT user shelling out to grep/rg) | prompt.ts:8-11 | YES — v4 line 4897 uses subprocess | Verify | Block C | KEEP (uses ripgrep subprocess); add prompt warning "NEVER invoke grep/rg as Bash". |
| 172 | `output_mode: 'content' \| 'files_with_matches' \| 'count'` | GrepTool.ts:52-57 | Partial — v4 may only return content | Y — three modes | Block C | Add 3 modes. files_with_matches is the default and cheapest. |
| 173 | `head_limit` (default 250, `0`=unlimited) + `offset` | GrepTool.ts:80-85, 108-128 | NO | Y — bound context bloat | Block C | Port `applyHeadLimit` + `formatLimitInfo`. Critical for token efficiency. |
| 174 | `appliedLimit` only emitted when truncation occurred (so model can paginate with offset) | GrepTool.ts:121-127 | NO | Y | Block C | Port. |
| 175 | `glob` filter (with brace-preserving split) | GrepTool.ts:46-51, 391-409 | Partial | Y | Block C | Port brace-aware split logic. |
| 176 | `type` filter (rg `--type js|py|rust|...`) | GrepTool.ts:74-79, 386-389 | NO | Y | Block C | Add. |
| 177 | `-A`/`-B`/`-C`/`context` line-context params (only valid when output_mode='content') | GrepTool.ts:58-67 | NO | Y | Block C | Port. |
| 178 | `-n` show-line-numbers (default true in content mode) | GrepTool.ts:68-69 | Partial | Y | Block C | Default true. |
| 179 | `-i` case-insensitive | GrepTool.ts:71-73 | YES | KEEP | N/A | — |
| 180 | `multiline` flag (`-U --multiline-dotall`) | GrepTool.ts:86-88 | NO | Y — needed for cross-line patterns | Block C | Add. |
| 181 | `--max-columns 500` — prevent base64/minified noise | GrepTool.ts:336-338 | NO | Y | Block C | Add. |
| 182 | VCS-directory exclusion (`.git`, `.svn`, `.hg`, `.bzr`, `.jj`, `.sl`) | GrepTool.ts:95-102, 332-335 | Partial | Y | Block C | Port full set. |
| 183 | Pattern-starts-with-dash → `-e` flag | GrepTool.ts:380-384 | NO | Y — defensive | Block C | Port; ~4 LOC. |
| 184 | `getFileReadIgnorePatterns` mapped to `--glob !pattern` | GrepTool.ts:411-427 | NO | OPTIONAL | Block C polish | DROP unless Block B+ adds permission ignore. |
| 185 | `toRelativePath` per-line for content mode (after head_limit applied — order matters for performance) | GrepTool.ts:445-465 | Partial | Y | Block C | Port "limit-then-relativize" order. |
| 186 | `numFiles`/`numLines`/`numMatches` count tracking + summary message | GrepTool.ts:144-155, 280-291 | Partial | Y | Block C | Port summary format. |
| 187 | `RipgrepTimeoutError` propagation (don't silently return "no matches" on timeout) | GrepTool.ts:436-441 | NO | Y — correctness | Block C | Port; raise distinct timeout error vs. zero results. |

---

## ALREADY-IN-PLAN

These items in v3 plan already cover Runnable A-F capabilities — capture the cross-link:

- **Block 0** — repo prep, no Runnable item.
- **Block A (sub-agent)** — covers #1, #2, #3, #5-9, #15, #19, #20, #21, #27 (kept from v4), #29-32, #34. Adds fork sub-block.
- **Block B (bash hardening)** — covers #36-40, #48-50, #53-55, #57, #61-62, #64.
- **Block B+ (permission modes)** — covers #51, #109 (`isDestructive` pattern), #99 (allowedPrompts conditional).
- **Block C (file ops)** — covers #110, #111, #115-117, #119, #121-124, #128-130, #135, #136, #137, #139-150, #152-154, #157, #159-166, #168-187.
- **Block C+ (plan mode)** — covers #84-87, #89, #91, #97-98, #100-102, #104.
- **Block D (already in plan)** — Out of A-F slice.
- **Block E+F** — Out of A-F slice.
- **Block I** — Out of A-F slice.
- **Block M (memory)** — covers #10-13, #95 (cwd cache invalidation note), #144.
- **Block G/G2/H** — Out of A-F slice.
- **Block L/N/T** — Out of A-F slice.
- **Block J (worktree, conditional)** — covers #92-93, #105-108. **Recommend DROP for v5.0.1.**
- **Block K** — Out of A-F slice.

**Net: ~80 of 187 capabilities already mapped to existing plan blocks.**

---

## NEW capabilities (additions to plan)

These are items not yet in v3 plan that the builder should graft:

| New # | Block | Capability | Reason |
|---|---|---|---|
| N1 | Block A | Fork sub-block (cap #5-9): `FORK_AGENT`, `buildForkedMessages`, `FORK_PLACEHOLDER_RESULT`, `isInForkChild`, `buildChildMessage` | Bedrock prompt-cache reuse on sub-agents — biggest Hermes-axis win in slice. |
| N2 | Block A | Per-agent persistent memory (cap #10-13): scoped `agent-memory/<type>/MEMORY.md` | Enables verify/review agents to learn — Hermes-axis. |
| N3 | Block B | `interpretCommandResult` exit-code semantics table (cap #49) | Fixes v4 treating `grep` exit 1 as error. |
| N4 | Block B | `getDestructiveCommandWarning` pattern table (cap #50) | Surfaces "may discard uncommitted changes" / "may overwrite remote history" to user before approve. |
| N5 | Block B | `extractBashCommentLabel` (cap #48) | UI label from `# comment` first line — small UX win. |
| N6 | Block B | `resetCwdIfOutsideProject` + `stdErrAppendShellResetMessage` (cap #61-62) | Prevents cwd drift in long sessions. |
| N7 | Block B | Cd+git compound + multi-cd detection (cap #53-54) | Closes a real security hole (bare-repo fsmonitor bypass). |
| N8 | Block B | Pipe-segment-aware permission check (cap #55) | More accurate than v4's whole-string match. |
| N9 | Block C | Quote normalization in edits (cap #115-117) | Prevents copy-paste edit failures (curly vs. straight quotes). |
| N10 | Block C | UTF-16 LE BOM detection + line-ending preservation (cap #121-122) | Windows-saved file edits silently corrupt today. |
| N11 | Block C | UNC path skip across all file tools (cap #123, #148, #168) | Windows NTLM credential leak prevention. |
| N12 | Block C | `BLOCKED_DEVICE_PATHS` (cap #146) | Prevent infinite read on `/dev/zero`. |
| N13 | Block C | Token-count cap + tokenizer fallback (cap #145, #152) | More accurate than byte-cap. |
| N14 | Block C | `CYBER_RISK_MITIGATION_REMINDER` system-reminder on Read (cap #143) | Defensive against malware-as-input. |
| N15 | Block C | Image/PDF/Notebook polymorphic Read (cap #140-142) | Folds 3 v4 tools into Read; uses Bedrock vision/document blocks. |
| N16 | Block C | Skill discovery on file edit/read (cap #112, #139) | Path-triggered skill activation — replaces v4's static registry. |
| N17 | Block C | Grep `head_limit`/`offset` + 3 output modes + `multiline` + `type` filter + `-A/-B/-C` (cap #173-180) | Single biggest token-saver in Block C. |
| N18 | Block C | Grep `--max-columns 500` + VCS exclusion (cap #181-182) | Quality-of-output. |
| N19 | Block C | `RipgrepTimeoutError` (cap #187) | Correctness — distinguish timeout from no-results. |
| N20 | Block C+ | `EnterPlanMode` + `ExitPlanMode` formal mode-switch (cap #84-104) | Hermes-axis flow improvement; v4's plan-mode allowlist exists but no formal entry/exit. |
| N21 | Block C+ | File-history backup before edit (cap #127) | Powers a `/rollback` command later. |
| N22 | Block A | `ONE_SHOT_BUILTIN_AGENT_TYPES` (cap #19) | Token-saver for explore/plan/verify. |
| N23 | Block A NEW | AskUserQuestion structured multiselect (cap #29-32, #34) | Replaces v4's free-text ask_user. |

**23 NEW items to graft onto v3 plan.**

---

## OUT-OF-SCOPE drops (categorical reason)

### Category D1 — External network / cloud-only services (Bedrock-only constraint)

- #4 `shouldInjectAgentListInMessages` (no MCP/plugin churn in single-user SM)
- #25 `isolation: "remote"` (CCR remote env)
- #26 Agent-specific MCP servers
- #66 `containsExcludedCommand` (sandbox-related)
- #67 `BINARY_HIJACK_VARS` strip + wrapper-strip iterative
- #71 `validateAttachmentPaths` / `resolveAttachments`
- #72 `uploadBriefAttachment` to private_api
- #73 `isBriefEntitled` / `isBriefEnabled` KAIROS gates
- #78 `voiceEnabled` setting
- #79 `remoteControlAtStartup` (BRIDGE_MODE)
- #80 KAIROS push notification settings
- #88 `prepareContextForPlanMode` auto-mode classifier
- #90 `--channels` Telegram/Discord disable
- #94 Hooks-based VCS-agnostic isolation
- #103 Teammate plan-approval mailbox
- #107 Tmux session keep/kill
- #113 LSP `didChange`/`didSave`
- #114 `notifyVscodeFileUpdated`
- #126 `checkTeamMemSecrets` team-memory secret guard
- #132 `diagnosticTracker` LSP diagnostics replay
- #133 `gitDiff` quartz-lantern remote experiment
- #138 `tengu_read_dedup_killswitch` GB toggle
- #155 `getFileReadIgnorePatterns` (gitignore) — DEFER
- #156 `registerFileReadListener` pubsub
- #158 `tengu_amber_wren` GB read limit
- #167 `getGlobExclusionsForPluginCache`
- #184 GrepTool ignore-patterns mapping — DEFER

### Category D2 — Sandbox stack (no sandbox in single-user SM, network blocked anyway)

- #43 Sandbox `dedup` wrapper for prompt
- #44 Sandbox section in prompt
- #45 `dangerouslyDisableSandbox` parameter
- #46 Embedded find/grep aliasing
- #47 Most of `getCommitAndPRInstructions` (undercover stripping)

### Category D3 — Heavy AST stack (low-ROI for trusted single-user)

- #52 Full `bashCommandIsSafeAsync_DEPRECATED` AST port (~5K LOC)
- #56 `parseSedEditCommand` / `applySedSubstitution` (model is told to use Edit not sed)
- #58-60 Image stdout decode/resize chain (matplotlib data-URI path is rare)
- #68 `parseForSecurity` AST → `getTreeSitterAnalysis`
- #131 `inputsEquivalent` edit-retry dedup

### Category D4 — Stub files in source (no behavior to port)

- #82 `CtxInspectTool.ts` is `export default {}` — stub
- #83 `DiscoverSkillsTool/prompt.ts` is `export default ''` — stub

### Category D5 — Stronger v4 equivalent already exists

- #14 Memory snapshot sync (v4 has single `memory.md` global; team sync N/A)
- #17-18 Multi-source agent override resolution (single-source in v5)
- #74-77 ConfigTool runtime settings tool (chat.ipynb exposes CONFIG at notebook top — explicit)
- #69-70 BriefTool send-message tool (chat.ipynb shows assistant text top-level natively)
- #16 `agentColorManager` (chat.ipynb has no per-agent color today)

### Category D6 — Worktree (Block J recommended DROP for v5.0.1)

- #92-96, #105-108 — All EnterWorktree/ExitWorktree mechanics. SM workspace usually not a git repo.

### Category D7 — macOS/external-platform specific

- #147 `getAlternateScreenshotPath` (macOS thin-space U+202F)

### Category D8 — Non-portable to Bedrock-only

- #125 `validateInputForSettingsFileEdit`
- #134 `tengu_write_claudemd` analytics
- #99 `allowedPrompts` semantic Bash permissions (needs LLM-grade classifier service)

**Total drops: ~58 capabilities. Net adopt: ~129 (80 already-in-plan + 49 new line items rolled up into the 23 N-items above).**

---

## Summary

| | |
|---|---|
| Files in slice | 81 |
| Files scanned full or near-full | 36 (logic) |
| UI/render files deliberately skimmed | 19 |
| Heavy permission/AST files capability-only | 5 (bashPermissions, bashSecurity, pathValidation, readOnlyValidation, sedValidation) |
| Total LOC in slice | ~52,000 |
| Logic LOC scanned in detail | ~10,500 |
| Capabilities cataloged | **187** |
| Already-in-plan (covered by v3 blocks) | **~80** |
| NEW (must graft, aggregated as 23 N-items spanning ~49 line capabilities) | **23 N-items / 49 line caps** |
| Out-of-scope drops | **~58** |

**Confidence:** HIGH for FileEdit, FileRead, FileWrite, Glob, Grep, ConfigTool, BriefTool, AskUserQuestion, EnterPlanMode, ExitPlanMode, EnterWorktree, ExitWorktree, CtxInspect, DiscoverSkills (full prompt + main .ts read or stub confirmed). MEDIUM for AgentTool main and BashTool main (top + grep + key sub-files; render mass skimmed). LOW for permission stack (bashPermissions/Security/pathValidation/readOnly/sedValidation) — capability captured at contract level not line level; full-port not advised, surface-level checklist sufficient for SageMaker single-user trust model.

**Top 5 highest-value graft targets onto v4:**
1. **N17** — Grep `head_limit`/`offset` + 3 output modes + multiline + type + context (biggest token-saver in slice)
2. **N1** — Fork sub-block (Bedrock prompt-cache reuse, big Hermes-axis win)
3. **N15** — Image/PDF/Notebook polymorphic Read (folds 3 v4 tools, leverages Bedrock vision)
4. **N9-N11** — Quote normalization + UTF-16 BOM + UNC skip (Windows correctness fixes for v4 today)
5. **N20** — EnterPlanMode/ExitPlanMode formal mode-switch (Hermes-axis flow, replaces v4's loose plan_mode flag)
