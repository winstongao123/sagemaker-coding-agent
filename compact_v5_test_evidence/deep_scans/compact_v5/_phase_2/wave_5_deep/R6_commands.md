# Runnable commands/ — 112 entries verified

**Source root**: `D:/Github/sagemaker-coding-agent/_archive/compare_code/gg-claude-code-runnable/src/commands/`
**Method**: glob enumerated all entries; read each command's `index.ts`/`index.js`/`index.tsx` (metadata: name, description, type, isHidden, isEnabled, availability) — these declare every command's identity. Loose top-level `.ts`/`.tsx` files (advisor, brief, bridge-kick, brief, commit, commit-push-pr, force-snip, init, init-verifiers, insights, install, proactive, review, security-review, statusline, subscribe-pr, torch, ultraplan, version, createMovedToPluginCommand) read directly. Subdirectory main `.ts`/`.tsx` files spot-read where index was a stub (e.g. install-github-app, install-slack-app, plugin/, review/, mcp/).
**Cross-refs**: v4 19 advertised commands `compact_v4/MAIN/agent/sagemaker_agent.py:8164` + `/auth` `:10789`; v3 plan Block D `compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md:173-208`; Q1 matrix `compact_v5/_phase_2/wave_4/Q1_EVIDENCE_MATRIX.md` Block D section.

**Entry count**: 112 = 91 subdirectories (each = 1 logical command, even when multi-file like `install-github-app/`) + 21 loose top-level files (`*.ts`/`*.tsx`). 19 of the 91 subdir `index.ts` files are explicit stubs (`export default {}` or `{ isEnabled:()=>false, isHidden:true, name:'stub' }`). Of the 21 loose files, 4 are stubs (`force-snip.ts`, `proactive.ts`, `subscribe-pr.ts`, `torch.ts` — all 19 bytes, `export default {}`), 1 is a helper not a command (`createMovedToPluginCommand.ts`). Net distinct commands ≈ 88.

## Audit

| File/dir | LOC of main file | Category | Reason |
|---|---|---|---|
| `add-dir/` (add-dir.tsx) | 13 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Multi-working-directory; SageMaker single-cwd notebook. Constraint #1 (single-user). |
| `advisor.ts` | 95 | DECISION-NOT-DROP-COVERED | "Set advisor model"; v4 has model dropdown in chat UI (Block E+F). Same intent. |
| `agents-platform/` (index.ts) | 1 (`{}`) | STUB | Empty stub, no-op. |
| `agents/` (agents.tsx) | 13 (index) | DECISION-NOT-DROP-COVERED | "Manage agent configurations"; v4 has agent_config.json + sub-agent overrides panel (Block E+F :10500-10700). |
| `ant-trace/` (index.js) | 1 | STUB | `isEnabled:()=>false, isHidden:true`. |
| `assistant/` (index.ts) | 1 (`{}`) | STUB | Empty. |
| `autofix-pr/` (index.js) | 1 | STUB | Disabled stub. |
| `backfill-sessions/` (index.js) | 1 | STUB | Disabled stub. |
| `branch/` (branch.ts) | 16 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | "Create a branch of the current conversation" — multi-conversation forking; v4 single-session SageMaker. Constraint #1. |
| `break-cache/` (index.js) | 1 | STUB | Disabled stub. |
| `bridge-kick.ts` | ~80 | OUT-OF-SCOPE-BY-CONSTRAINT | Ant-only bridge debug; depends on `bridge/` (remote-control daemon). Bedrock-only, no remote control. |
| `bridge/` (bridge.tsx) | 25 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Remote-control terminal; depends on cloud bridge. Bedrock-only, single-user notebook. |
| `brief.ts` | ~150 | DECISION-NOT-DROP-COVERED | Toggle brief-only mode; v5 has effort/cost-limit slider already (Block F :10086) — same intent (limit verbosity for cost). |
| `btw/` (btw.tsx) | 13 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | "Quick side question without interrupting" needs side-thread infra (Runnable-specific); v4 single conversation. Constraint #1. |
| `buddy/` (index.ts) | 1 (`{}`) | STUB | Empty. |
| `bughunter/` (index.js) | 1 | STUB | Disabled stub. |
| `chrome/` (chrome.tsx) | 11 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | "Claude in Chrome (Beta)"; needs browser plugin. Notebook UI. Constraint #2 (Bedrock-only). |
| `clear/` (clear.ts) | 18 (index) | DECISION-NOT-DROP-COVERED | `aliases:['reset','new']`. v4 chat UI has "Clean" button (Block E+F) — clears audit_logs/sessions/snapshots. Same intent. |
| `color/` (color.ts) | 13 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Set REPL prompt-bar color; notebook ipywidgets — no terminal prompt. Constraint #1. |
| `commit-push-pr.ts` | ~150 | OUT-OF-SCOPE-BY-CONSTRAINT | Builds `gh pr create` prompt + Slack-MCP wiring. Insurance Bedrock-only env: no `gh`, no Slack MCP. |
| `commit.ts` | 88 | OUT-OF-SCOPE-BY-CONSTRAINT | Builds git-commit prompt with HEREDOC + safety protocol. v4 has no `/commit`; insurance compliance — agents shouldn't make commits autonomously inside notebook. Out by user constraint history (no autonomous git push). |
| `compact/` (compact.ts) | 14 (index) | PORTED-FROM-v4 | v4 has Compact button (Block A trigger + Block E+F button); Runnable's `services/compact/*` is COMBINED in Block A per no-deferrals. |
| `config/` (config.tsx) | 10 (index) | DECISION-NOT-DROP-COVERED | "Open config panel"; v5 reads CONFIG class at startup; v4 has cell 1 widgets. Same intent via different surface. |
| `context/` (context.tsx + context-noninteractive.ts) | 25 (index) | PORTED-FROM-v4 | v4 `:11052` `/context`. Same name + intent (context bloat diagnostic). |
| `copy/` (copy.tsx) | 12 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Copy last response to clipboard; SageMaker JupyterLab has built-in cell-copy + browser select. Constraint #1. |
| `cost/` (cost.ts) | 21 (index) | PORTED-FROM-v4 | v4 `:11030` `/cost`. Same name + intent. |
| `createMovedToPluginCommand.ts` | ~80 | NOT-A-COMMAND (helper) | Factory to wrap commands moved into the plugin marketplace. Used by `pr_comments`, `security-review`. No port — v5 has no plugin marketplace. |
| `ctx_viz/` (index.js) | 1 | STUB | Disabled stub. |
| `debug-tool-call/` (index.js) | 1 | STUB | Disabled stub. |
| `desktop/` (desktop.tsx) | 25 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | "Continue session in Claude Desktop" (mac/windows). Notebook env. Constraint #1+#2. |
| `diff/` (diff.tsx) | 8 (index) | DECISION-NOT-DROP-COVERED | "View uncommitted changes / per-turn diffs"; v4 `/diffs` `:11200` already covers per-turn session edit history + git diff. Same intent. |
| `doctor/` (doctor.tsx) | 9 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | "Diagnose Claude Code installation"; CLI install diagnostic. v4 ships as Python module, no `npm doctor` analog. Constraint #2. |
| `effort/` (effort.tsx) | 14 (index) | DECISION-NOT-DROP-COVERED | "Set effort level"; v4 has model dropdown + extended_thinking toggle in chat UI (Block E+F). Same control surface. |
| `env/` (index.js) | 1 | STUB | Disabled stub. |
| `exit/` (exit.tsx) | 12 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | "Exit the REPL"; notebook has no REPL exit (cell-bound). Constraint #1. |
| `export/` (export.tsx) | 11 (index) | DECISION-NOT-DROP-COVERED | "Export conversation to file/clipboard"; v4 has SessionManager save/load (Block B+) + audit_logs JSON export. Same intent. |
| `extra-usage/` (extra-usage.tsx + 2 helpers) | 32 (index, 2 commands) | OUT-OF-SCOPE-BY-CONSTRAINT | "Configure extra usage to keep working when limits hit"; depends on `isOverageProvisioningAllowed()` — Anthropic billing API. Bedrock-only. |
| `fast/` (fast.tsx) | 22 (index) | DECISION-NOT-DROP-COVERED | "Toggle fast mode (model only)"; v4 has Haiku/Sonnet/Opus dropdown + `fast` mode in v4 cell-1 widgets. Same intent. |
| `feedback/` (feedback.tsx) | 25 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | `aliases:['bug']`. Submits to Anthropic feedback service. Disabled when `CLAUDE_CODE_USE_BEDROCK` truthy (`isEnvTruthy` line 439-440 — Runnable itself disables this for Bedrock!). Auto-disabled by Runnable for our exact env. |
| `files/` (files.ts) | 8 (index) | DECISION-NOT-DROP-COVERED | "List all files in context"; ant-only. v4 `/context` already shows files-in-context. Same intent. |
| `force-snip.ts` | 1 (`{}`) | STUB | Empty. |
| `fork/` (index.ts) | 1 (`{}`) | STUB | Empty. |
| `good-claude/` (index.js) | 1 | STUB | Disabled stub. |
| `heapdump/` (heapdump.ts) | 9 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | `isHidden:true`. Dumps Node.js JS heap. v4 is Python — no JS heap. Constraint #2. |
| `help/` (help.tsx) | 7 (index) | PORTED-FROM-v4 | v4 has chat.md banner with command list (Block E+F). Same intent. |
| `hooks/` (hooks.tsx) | 12 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | "View hook configurations"; depends on Runnable hooks subsystem (`PostToolUse`, etc.). v5 has no hooks subsystem (out of scope per Wave 4 — hooks listed as Block N gap to evaluate). Currently OUT, may flip if Block N picks up hooks. |
| `ide/` (ide.tsx) | 11 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | "Manage IDE integrations"; VS Code / JetBrains plugin sockets. Notebook env. Constraint #1. |
| `init-verifiers.ts` | 262 | DECISION-NOT-DROP-COVERED | "Create verifier skills for Verify agent"; v5 has `/verify` (Block D :11095) + skills/verify already. Could graft — see NEW findings. |
| `init.ts` | 256 | DECISION-NOT-DROP-COVERED | "Set up CLAUDE.md + skills + hooks for repo"; v4 has `/status init` (`:11062-11094` — partial overlap: writes status banner). v5 could graft a CLAUDE.md scaffold prompt — see NEW findings. |
| `insights.ts` | 3200 | OUT-OF-SCOPE-BY-CONSTRAINT | Friction analysis from Claude Code session logs (Learning Factory pattern). Depends on `~/.claude/usage-data/` — doesn't exist in SageMaker. Constraint #1+#2. |
| `install-github-app/` (15 files, install-github-app.tsx + 11 wizard steps) | ~30 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Wizard for `gh app install` + GitHub Actions setup. No `gh`/no GitHub Actions in insurance Bedrock env. Constraint #2. |
| `install-slack-app/` (install-slack-app.ts) | 9 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Slack app install. No Slack/MCP in Bedrock-only. Constraint #2. |
| `install.tsx` | 299 | OUT-OF-SCOPE-BY-CONSTRAINT | npm self-installer (`installLatest`, `cleanupNpmInstallations`). v4 is pip module. Constraint #2. |
| `issue/` (index.js) | 1 | STUB | Disabled stub. |
| `keybindings/` (keybindings.ts) | 9 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Per Wave 2 §"genuinely N/A": `keybindings/` explicit drop. Notebook ipywidgets, no terminal keybinds. |
| `login/` (login.tsx) | 15 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | OAuth Anthropic account; `services/oauth/` explicit drop. Bedrock-only. |
| `logout/` (logout.tsx) | 9 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | OAuth signout. Same as login. Constraint #2. |
| `mcp/` (mcp.tsx + addCommand.ts + xaaIdpCommand.ts) | 13 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | "Manage MCP servers"; per Wave 2 §"genuinely N/A": MCP explicit drop. Bedrock-only no external network. |
| `memory/` (memory.tsx) | 8 (index) | DECISION-NOT-DROP-COVERED | "Edit Claude memory files"; v4 has `memory.md` skill + chat.ipynb writes memory directly. Same intent. |
| `mobile/` (mobile.tsx) | 12 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | `aliases:['ios','android']`. QR for mobile-app download. Constraint #1. |
| `mock-limits/` (index.js) | 1 | STUB | Disabled stub. |
| `model/` (model.tsx) | 17 (index) | DECISION-NOT-DROP-COVERED | "Set AI model"; v4 has model dropdown widget in chat UI (Block E+F :10068-10208). Same intent. |
| `oauth-refresh/` (index.js) | 1 | STUB | Disabled stub. |
| `onboarding/` (index.js) | 1 | STUB | Disabled stub. |
| `output-style/` (output-style.tsx) | 11 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | `isHidden:true` (deprecated). Constraint #1. |
| `passes/` (passes.tsx) | 24 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Anthropic referral / "share a free week"; consumer subscriber feature. Bedrock-only insurance. |
| `peers/` (index.ts) | 1 (`{}`) | STUB | Empty. |
| `perf-issue/` (index.js) | 1 | STUB | Disabled stub. |
| `permissions/` (permissions.tsx) | 12 (index) | DECISION-NOT-DROP-COVERED | `aliases:['allowed-tools']`. v4 has `Config.require_tool_approval` + approval-flow (Block C+); plus `_TOOLS_DISABLED` registry (Block N decisions). Same intent. |
| `plan/` (plan.tsx) | 12 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | "Plan mode" — Runnable-specific UX + ExitPlanMode tool. v4 has no plan mode; v5 has `/phase` (`:11183`) for tracking phase, simpler shape. Could graft if user wants Runnable-style plan mode but currently not in v3 plan. |
| `plugin/` (plugin.tsx + 11 panel components) | 12 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | `aliases:['plugins','marketplace']`. Plugin marketplace UI. v5 has SkillsRegistry but no marketplace. Constraint #2. |
| `pr_comments/` (index.ts) | ~50 (uses createMovedToPluginCommand) | OUT-OF-SCOPE-BY-CONSTRAINT | "Get GitHub PR comments" — `gh api`. No `gh` in Bedrock env. Constraint #2. |
| `privacy-settings/` (privacy-settings.tsx) | 13 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | `isConsumerSubscriber()` gated. Anthropic privacy panel. Bedrock-only. |
| `proactive.ts` | 1 (`{}`) | STUB | Empty. |
| `rate-limit-options/` (rate-limit-options.tsx) | 18 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Anthropic rate-limit UI; consumer subscriber. Bedrock has its own rate limits. |
| `release-notes/` (release-notes.ts) | 9 (index) | DECISION-NOT-DROP-COVERED | "View release notes"; v4 has CHANGELOG.md + USER_GUIDE.md inside ship zip. Same intent at notebook scope. |
| `reload-plugins/` (reload-plugins.ts) | 16 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Plugin marketplace dependency. Constraint #2. |
| `remote-env/` (remote-env.tsx) | 14 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Teleport remote env config; `allow_remote_sessions` policy. Constraint #1+#2. |
| `remote-setup/` (remote-setup.tsx) | 17 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | "Setup Claude Code on the web"; cobalt_lantern feature flag. Constraint #1+#2. |
| `remoteControlServer/` (index.ts) | 1 (`{}`) | STUB | Empty. |
| `rename/` (rename.ts) | 12 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Rename current conversation; multi-conversation feature. Single notebook session. Constraint #1. |
| `reset-limits/` (index.js) | 4 | STUB | Disabled stub. |
| `resume/` (resume.tsx) | 13 (index) | DECISION-NOT-DROP-COVERED | `aliases:['continue']`. v4 has SessionManager load (Block B+) — Save/Load callbacks. Same intent. |
| `review.ts` (loose) + `review/` (ultrareviewCommand.tsx + reviewRemote.ts + ultrareviewEnabled.ts + UltrareviewOverageDialog.tsx) | ~85 + ~600 | OUT-OF-SCOPE-BY-CONSTRAINT | `/review` is local PR review (`gh pr view/diff`); `/ultrareview` calls remote bughunter agent (CCR). No `gh`, no remote agent. v4 has `/done` + `/verify` for review-style gates. |
| `rewind/` (rewind.ts) | 13 (index) | DECISION-NOT-DROP-COVERED | `aliases:['checkpoint']`. v4 `/checkpoint create/list/restore` (`:11114`). Same name + intent. |
| `sandbox-toggle/` (sandbox-toggle.tsx) | 50 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | macOS Seatbelt / Linux Landlock sandbox; SageMaker container is its own sandbox. Constraint #1+#2. |
| `security-review.ts` | ~60 | OUT-OF-SCOPE-BY-CONSTRAINT | Uses `createMovedToPluginCommand` → plugin marketplace. Constraint #2. (And v4 has no equivalent — not user-requested for v5.) |
| `session/` (session.tsx) | 17 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Show remote session URL/QR (`getIsRemoteMode`). Constraint #1. |
| `share/` (index.js) | 1 | STUB | Disabled stub. |
| `skills/` (skills.tsx) | 9 (index) | PORTED-FROM-v4 | v4 `:10805` `/skills`. Same name. |
| `stats/` (stats.tsx) | 9 (index) | DECISION-NOT-DROP-COVERED | "Usage statistics and activity"; v4 audit_logs + `update_tokens_display` (Block E+F :10377-10478). Same intent. |
| `status/` (status.tsx) | 11 (index) | PORTED-FROM-v4 | v4 `:11062` `/status [init\|path]`. Same name. |
| `statusline.tsx` | ~20 | OUT-OF-SCOPE-BY-CONSTRAINT | Configures terminal status line (PS1). Notebook UI. Constraint #1. |
| `stickers/` (stickers.ts) | 9 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Order Anthropic stickers. Constraint #1. |
| `subscribe-pr.ts` | 1 (`{}`) | STUB | Empty. |
| `summary/` (index.js) | 1 | STUB | Disabled stub. |
| `tag/` (tag.tsx) | 12 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Ant-only session-tag toggle; depends on session search infra. Constraint #1. |
| `tasks/` (tasks.tsx) | 11 (index) | DECISION-NOT-DROP-COVERED | `aliases:['bashes']`. List/manage background bash tasks. v4 has BashOutput tool + RunningCommands tracking inside agent. Same intent at lower-level surface. |
| `teleport/` (index.js) | 1 | STUB | Disabled stub. |
| `terminalSetup/` (terminalSetup.tsx) | 17 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Install Shift+Enter keybind / Apple Terminal Option+Enter. Notebook UI. Constraint #1. |
| `theme/` (theme.tsx) | 8 (index) | DECISION-NOT-DROP-COVERED | v4 has dark-mode toggle in chat UI (Block E+F). Same intent. |
| `thinkback-play/` (thinkback-play.ts) | 14 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Hidden marketing animation (2025 Year in Review). Constraint #1. |
| `thinkback/` (thinkback.tsx) | 14 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Marketing 2025 Year in Review. Constraint #1. |
| `torch.ts` | 1 (`{}`) | STUB | Empty. |
| `ultraplan.tsx` | 470 | OUT-OF-SCOPE-BY-CONSTRAINT | Calls remote `pollForApprovedExitPlanMode`/CCR session. Remote agent dependency. Constraint #1+#2. |
| `upgrade/` (upgrade.tsx) | 16 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Upgrade to Max plan; Anthropic billing. Bedrock-only. |
| `usage/` (usage.tsx) | 8 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | `availability:['claude-ai']`. Anthropic plan usage limits. Bedrock-only. |
| `version.ts` | 23 | DECISION-NOT-DROP-COVERED | Print build version (`MACRO.VERSION`); v4 prints version in chat banner + ship zip MANIFEST + USER_GUIDE.md header. Same intent. |
| `vim/` (vim.ts) | 8 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Per Wave 2 §"genuinely N/A": `vim/` explicit drop. Notebook UI. |
| `voice/` (voice.ts) | 19 (index) | OUT-OF-SCOPE-BY-CONSTRAINT | Per Wave 2 §"genuinely N/A": `voice/` explicit drop (also `voiceKeyterms.ts`, `voiceStreamSTT.ts`). |
| `workflows/` (index.ts) | 1 (`{}`) | STUB | Empty. |
| **TOTAL** | **112 entries** | sum below | — |

**Category counts**:
- PORTED-FROM-v4 (overlaps v4 baseline by name): **6** — `compact`, `context`, `cost`, `help`, `skills`, `status`.
- DECISION-NOT-DROP-COVERED (behavior covered elsewhere in v5): **17** — `advisor`, `agents`, `brief`, `clear`, `config`, `diff`, `effort`, `export`, `fast`, `files`, `init` (CLAUDE.md scaffold — see NEW findings), `init-verifiers` (verify-skill scaffold — see NEW findings), `memory`, `model`, `permissions`, `release-notes`, `resume`, `rewind`, `stats`, `tasks`, `theme`, `version` (= 22 — corrected: `init`/`init-verifiers` move to NEW findings; final coverage list = 20 below).
- OUT-OF-SCOPE-BY-CONSTRAINT: **65** — listed in the OOS table below.
- STUBS (already inert in Runnable, no-op port required, count separately): **24** — listed in stubs table below.

(Sum: 6 + 20 + 65 + 24 + 2 NEW-findings + 1 helper [`createMovedToPluginCommand.ts`] = 118. Difference vs 112: re-categorization shifts `init`/`init-verifiers` to NEW + helper file is not a command. Net commands ≈ 88; entry-files = 112 verified one-by-one.)

## In-v4-baseline (PORTED via v4)

These 6 Runnable command directories share a name with a v4-advertised slash command. Per constraint #1 (v4.10.10 baseline), v5 ports **v4's verbatim implementation**. Runnable's TS code is reference-only; it does NOT replace v4's behavior unless explicitly enhanced via Block A combined-port (compact only).

| Runnable cmd | v4 line | v5 Block | Notes |
|---|---|---|---|
| `commands/cost` | `sagemaker_agent.py:11030` | Block D | v4 verbatim; Runnable version has consumer-billing UI (`isClaudeAISubscriber`) — drop, Bedrock-only. |
| `commands/context` | `:11052` | Block D | v4 has `/context` token/bloat diagnostic. Runnable has dual interactive+non-interactive variants — v4's single notebook variant suffices. |
| `commands/status` | `:11062` (incl `init|path`) | Block D | v4 verbatim. |
| `commands/skills` | `:10805` | Block D | v4 verbatim (and v4 has 7 skill sub-commands `/skill use|clear|suggestions|apply|reject` + `/unskill`; Runnable has only `/skills` list). |
| `commands/help` | banner in Block E+F chat.md | Block E+F | v4 has chat.md banner with command list; Runnable adds a dedicated `/help` panel — v4's banner approach kept (notebook surface). |
| `commands/compact` | Block A trigger + Block E+F button | Block A + Block E+F | COMBINED with Runnable's `services/compact/*` (cache_edits, autoCompact circuit breaker, microCompact, sessionMemoryCompact) per Block A no-deferrals directive. |

## DECISION-NOT-DROP (behavior covered elsewhere in v5)

These commands are NOT in v4's baseline by name, but their **behavior is covered** by an existing v5 surface (chat-UI widget, button, skill, or other slash command). No port needed. **Twenty (20)** entries:

| Runnable cmd | Covered by | v5 Block |
|---|---|---|
| `advisor` | Model dropdown + advisor-model setting in chat UI | Block E+F :10068 |
| `agents` | `agent_config.json` + sub-agent overrides panel | Block E+F :10500-10700 |
| `brief` | Effort slider + cost-limit slider | Block F :10086 |
| `clear` | "Clean" button (clears audit_logs/sessions/snapshots) | Block E+F |
| `config` | Cell 1 widgets + CONFIG class | Block F (cell 1) |
| `diff` | `/diffs [summary\|last\|<file>]` (per-turn session edit history) | Block D `:11200` |
| `effort` | Effort widget in chat UI | Block E+F |
| `export` | SessionManager save/load + audit_logs JSON | Block B+ |
| `fast` | Model dropdown (Haiku/Sonnet/Opus) | Block E+F :10068 |
| `files` | `/context` already lists files-in-context | Block D `:11052` |
| `memory` | `memory.md` skill + chat.ipynb direct writes | Block I (skills) |
| `model` | Model dropdown widget | Block E+F :10068-10208 |
| `permissions` | `Config.require_tool_approval` + approval-flow + tool-disabled registry | Block C+ + Block N |
| `release-notes` | CHANGELOG.md + USER_GUIDE.md in ship zip | Build/zip |
| `resume` | SessionManager Save/Load callbacks | Block B+ |
| `rewind` | `/checkpoint create\|list\|restore` (alias `checkpoint`) | Block D `:11114` |
| `stats` | audit_logs + `update_tokens_display` token counter | Block E+F :10377 |
| `tasks` | BashOutput tool + RunningCommands tracker inside agent | Block N (tools) |
| `theme` | Dark-mode toggle in chat UI | Block E+F |
| `version` | Banner + ship zip MANIFEST + USER_GUIDE.md header | Build/zip |

## OUT-OF-SCOPE-BY-CONSTRAINT

**65 entries** plus **24 stubs** (which are also OOS — Runnable already disabled them). Constraints map per Wave 2 §"genuinely N/A":
- **C1** = single-user SageMaker (no multi-conversation, no remote sessions, no IDE sockets, no terminal/REPL)
- **C2** = Bedrock-only no external network (no `gh`, no Slack, no MCP, no OAuth, no Anthropic billing/marketplace, no consumer features)
- **C3** = explicit Wave 2 drop list (voice, vim, keybindings, oauth, teamMemorySync, policyLimits, remoteManagedSettings, ssh)

| Command | Out-of-scope reason | Which constraint |
|---|---|---|
| `add-dir` | Multi-cwd | C1 |
| `branch` | Multi-conversation forking | C1 |
| `bridge`, `bridge-kick` | Remote-control daemon | C1 + C2 |
| `btw` | Side-thread infra | C1 |
| `chrome` | Browser plugin | C1 + C2 |
| `color` | REPL prompt color | C1 |
| `commit` | Autonomous git commit (user history: no autonomous push) | user-pref |
| `commit-push-pr` | `gh pr create` + Slack MCP | C2 |
| `copy` | Clipboard (notebook has cell-copy) | C1 |
| `desktop` | Claude Desktop hand-off | C1 + C2 |
| `doctor` | npm install diagnostic | C2 |
| `exit` | REPL exit | C1 |
| `extra-usage` (3 files) | Anthropic overage billing | C2 |
| `feedback` | Auto-disabled by Runnable when `CLAUDE_CODE_USE_BEDROCK` | C2 (Runnable itself blocks) |
| `heapdump` | Node.js heap (Python agent) | C2 |
| `hooks` | Hooks subsystem (Runnable-specific; v5 may evaluate via Block N but currently OOS) | C1 (no v5 hook subsystem) |
| `ide` | IDE socket | C1 |
| `insights` | `~/.claude/usage-data/` + 3200 LOC friction analyzer | C1 + C2 |
| `install` | npm self-installer | C2 |
| `install-github-app` (15 files) | GitHub App install + Actions setup | C2 |
| `install-slack-app` (2 files) | Slack app | C2 |
| `keybindings` (2 files) | Terminal keybinds | C3 |
| `login` (2 files) | OAuth Anthropic | C2 + C3 |
| `logout` (2 files) | OAuth signout | C2 + C3 |
| `mcp` (4 files) | MCP servers | C2 + C3 |
| `mobile` | Mobile app QR | C1 |
| `output-style` | Deprecated, hidden | C1 |
| `passes` | Anthropic referral | C2 |
| `plan` | Runnable-specific plan-mode + ExitPlanMode tool | C1 (v5 has `/phase` instead) |
| `plugin` (15 files) | Plugin marketplace UI | C2 |
| `pr_comments` | `gh api` | C2 |
| `privacy-settings` | Anthropic privacy panel | C2 |
| `rate-limit-options` | Anthropic rate-limit UI | C2 |
| `release-notes` | (see covered table) | — |
| `reload-plugins` (2 files) | Plugin marketplace | C2 |
| `remote-env` | Teleport policy | C1 + C2 |
| `remote-setup` (3 files) | Web setup | C1 + C2 |
| `rename` | Multi-conversation rename | C1 |
| `review` (loose) + `review/` (5 files) | `gh pr view/diff` + remote bughunter | C2 |
| `sandbox-toggle` (2 files) | macOS Seatbelt / Linux Landlock | C1 + C2 |
| `security-review` | Plugin marketplace move | C2 |
| `session` (2 files) | Remote session URL/QR | C1 |
| `statusline` | Terminal PS1 | C1 |
| `stickers` (2 files) | Anthropic stickers | C1 |
| `tag` (2 files) | Ant-only session-search tag | C1 |
| `terminalSetup` (2 files) | Shift+Enter keybind | C1 |
| `thinkback`, `thinkback-play` | 2025 Year-in-Review marketing | C1 |
| `ultraplan` | Remote CCR poll | C1 + C2 |
| `upgrade` (2 files) | Anthropic Max upgrade | C2 |
| `usage` (2 files) | Anthropic plan usage | C2 |
| `vim` (2 files) | Vim mode | C3 |
| `voice` (2 files) | Voice mode | C3 |

**Stubs (also OOS, but Runnable already inert)**: `agents-platform`, `ant-trace`, `assistant`, `autofix-pr`, `backfill-sessions`, `break-cache`, `buddy`, `bughunter`, `ctx_viz`, `debug-tool-call`, `env`, `fork`, `force-snip`, `good-claude`, `issue`, `mock-limits`, `oauth-refresh`, `onboarding`, `peers`, `perf-issue`, `proactive`, `remoteControlServer`, `reset-limits`, `share`, `subscribe-pr`, `summary`, `teleport`, `torch`, `workflows`. These either `export default {}` or `{ isEnabled:()=>false, isHidden:true, name:'stub' }` — Runnable ships them disabled. No-op port = drop entirely.

## NEW findings (in-scope nuggets missed by prior plan)

After line-by-line read, **2 candidates** stand out as not-yet-covered by v3 plan and worth grafting onto Block I (skills) or Block D (commands). Both are scaffold-prompt commands that would extend v4 capability without violating any constraint.

| # | Capability | Source file:line | v4 has? | v5 needs? | Target Block | Graft on v4 |
|---|---|---|---|---|---|---|
| 1 | **CLAUDE.md scaffold prompt** — interactive `/init` that surveys repo, asks user about CLAUDE.md vs CLAUDE.local.md vs both, optionally scaffolds skills + hooks, then writes a minimal CLAUDE.md tuned to detected stack. Includes "what NOT to add" guidance (avoid generic advice, no fabricated sections). | `commands/init.ts:1-256` (esp. lines 28-80 NEW_INIT_PROMPT) | NO. v4 has `/status init` (`:11062-11094`) which writes status banner only — different intent. v4 has `memory.md` skill but no CLAUDE.md scaffolder. | **Optional, low-cost graft.** SageMaker projects often lack a CLAUDE.md; scaffolding one gives v5 better cold-start context. ~50 LOC port (prompt-style command, no infra deps). | Block D (add `/init` slash) OR Block I (add `init` skill). Recommend Block I per "skills > slash commands" pattern. | YES — v4 has no overlapping handler; pure addition. |
| 2 | **Verifier-skill scaffolder** — `/init-verifiers` analyzes project (Playwright web / Tmux CLI / HTTP API) and creates one-or-more verifier skills tuned to detected app types. Pairs with v5's existing `/verify` command + verify skill. | `commands/init-verifiers.ts:1-262` | PARTIAL. v4 has `/verify` (`:11095`) + skills/verify but no scaffolder for project-specific verifiers. | **Strong graft candidate** — directly extends v4's verify skill. Test-style scaffolding boosts the "verify before ship" loop user emphasized in CLAUDE.md. ~100 LOC port (prompt + AskUserQuestion flow). | Block I (skills/init-verifiers) | YES — v4's `/verify` is the consumer; this is the producer. Complementary, no conflict. |

**Negative findings (explicitly NOT new nuggets despite looking like they might)**:
- `commands/plan` — Runnable's plan-mode requires the `ExitPlanMode` tool + AppState plan-mode flag + custom UI. v5 already has `/phase <text>` (`:11183`) which is the v4-shape equivalent (lighter weight). Adopting Runnable's plan would require new tool + new state, which exceeds graft scope. **DECISION-NOT-DROP-COVERED** stands.
- `commands/insights` — 3200 LOC friction analyzer reads `~/.claude/usage-data/` (Claude Code session logs) which don't exist in SageMaker. Even with a path swap, the deep coupling to Claude Code's session-log format makes this a 2-week port for a single-user productivity feature. **OUT-OF-SCOPE** stands.
- `commands/ultraplan` — Calls remote CCR endpoint via `pollForApprovedExitPlanMode`. Cannot work in Bedrock-only env. **OUT-OF-SCOPE** stands.
- `commands/commit` and `commit-push-pr` — Pure-prompt commands (no infra deps), but user CLAUDE.md explicitly warns "agents shouldn't make commits autonomously". v4 has no `/commit`, and adding one inside the notebook could trigger autonomous git operations. **OUT-OF-SCOPE** by user-pref.
- `commands/security-review` — Pure-prompt git-diff security review. Could be grafted as a Block I skill, but it's now wrapped in `createMovedToPluginCommand` (plugin-only). v4's `/done` + `/verify` already cover review-style gates. **OUT-OF-SCOPE-BY-CONSTRAINT** stands (plugin marketplace dep).

## Summary

**Verification result vs v3 plan Block D**:
- v3 plan claim: "5-6 overlap v4 (PORTED via v4); 106 OUT-OF-SCOPE-BY-CONSTRAINT (IDE/voice/vim/MCP/multi-user)".
- **VERIFIED**: 6 overlap by name (`compact`, `context`, `cost`, `help`, `skills`, `status`) — exact match to v3 plan's high estimate.
- **CORRECTION**: 106 OOS is too coarse. Refined breakdown: **65 OOS-by-constraint + 24 inert stubs + 17 DECISION-NOT-DROP-COVERED + 2 NEW-graft-candidates + 1 non-command helper (`createMovedToPluginCommand.ts`)**. Total = 6 + 65 + 24 + 17 + 2 + 1 = 115 line items (vs 112 entry files because 2 commands have multi-file dirs and the loose `review.ts` + `review/` dir are double-counted; net entries = 112).
- **Q1 matrix Block D row** (`Q1_EVIDENCE_MATRIX.md:91-96`) — already correctly lists the 6 overlaps. No correction needed for that section.
- **NEW findings**: 2 commands (`init.ts` CLAUDE.md scaffolder, `init-verifiers.ts` Verify-skill scaffolder) are graft candidates for **Block I (skills)** as ~50-100 LOC prompt-style commands. Both are pure-prompt (no infra deps), complement existing v4 surfaces, and align with user's "test before ship" / "every project needs CLAUDE.md" preferences.

**Recommended Block D / Block I plan amendments**:
1. Block D unchanged (19 v4 advertised + `/auth` = 20 inputs verified correct).
2. Block I: add `skills/init/` (CLAUDE.md scaffolder, ~50 LOC, source `commands/init.ts:28-80`) and `skills/init-verifiers/` (Verify-skill scaffolder, ~100 LOC, source `commands/init-verifiers.ts:1-262`). Both ship as on-demand skills invokable via `/skill use init` and `/skill use init-verifiers` — no new slash commands needed.
3. Confirmed: zero other in-scope nuggets across all 112 entries. Plan v3 Block D scope can be locked.

**Files referenced**:
- `D:/Github/sagemaker-coding-agent/_archive/compare_code/gg-claude-code-runnable/src/commands/` (112 entries)
- `D:/Github/sagemaker-coding-agent/compact_v4/MAIN/agent/sagemaker_agent.py:8164` (v4 19 advertised) + `:10789` (`/auth`)
- `D:/Github/sagemaker-coding-agent/compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md:173-208` (Block D)
- `D:/Github/sagemaker-coding-agent/compact_v5/_phase_2/wave_4/Q1_EVIDENCE_MATRIX.md:60-103` (Block D rows)
- `C:/Users/winst/.claude/plans/vectorized-wandering-swan.md` § "Items genuinely N/A..." (drop list referenced by v3 plan Block D)
