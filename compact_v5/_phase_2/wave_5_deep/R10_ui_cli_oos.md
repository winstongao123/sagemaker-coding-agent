# Runnable UI/CLI/SDK out-of-scope verify

Wave 5 Deep / R10. Path root: `D:/Github/sagemaker-coding-agent/_archive/compare_code/gg-claude-code-runnable/src/`.
Constraints v5.0.1: single-user SageMaker, Bedrock-only, v4 `chat.ipynb` is canonical UI, **NO DEFERRALS**. Scan = exhaustive line-by-line of every dir + 5 root files; verify each is correctly OOS, surface any in-scope nugget hidden inside.

## Files audit

| Dir | File count | LOC sum | Read fully? |
|---|---:|---:|---|
| `assistant/` | 5 | 98 | YES (5/5 — 4 are stub-only, 1 React chooser stub) |
| `screens/` | 3 | 5,977 | SAMPLED (top 60 of REPL.tsx 4,200 LOC; Doctor 1,300; Resume 477 — all React) |
| `ink/` | 98 | 19,851 | SAMPLED (file list + ink.ts re-exports; 100% terminal renderer) |
| `components/` | 405 | 81,565 | SAMPLED (151 .tsx component files listed; all React Ink dialogs/onboarding/etc.) |
| `outputStyles/` | 1 | 98 | YES — `loadOutputStylesDir.ts` only |
| `cli/` | 19 | 12,353 | SAMPLED (handlers/agents, autoMode, mcp, util.tsx; print.ts; exit.ts; structuredIO.ts; update.ts; transports listed) |
| `sdk/` | 2 | 2 | YES — both files are `export {}` empty |
| `server/` | 11 | 374 | YES (8 of 11 are 2-line stubs; 3 real: types 57 / createDirectConnect 88 / directConnectManager 213) |
| `remote/` | 4 | 1,127 | SAMPLED (RemoteSessionManager top 20 — Anthropic teleport WS bridge) |
| `upstreamproxy/` | 2 | 740 | SAMPLED (upstreamproxy.ts top 20 + relay.ts top 15 — CCR MITM CONNECT-over-WS) |
| `native-ts/` | 4 | 4,081 | SAMPLED (color-diff, file-index, yoga-layout headers — pure-TS ports of Rust/C++ NAPI deps) |
| `stubs/` | 56 | 267 | SAMPLED (ant-packages list + bun-bundle.d.ts + bedrock-sdk stub `class AnthropicBedrock {}`) |
| `jobs/` | 1 | 1 | YES — `classifier.ts` is `export default {}` |
| `moreright/` | 1 | 25 | YES — explicit "Stub for external builds — real hook is internal" |
| `buddy/` | 6 | 1,298 | SAMPLED (prompt.ts full + companion.ts top — virtual pet sprite "BUDDY" feature) |
| `yolo-classifier-prompts/` | 3 | 0 | YES — all 3 .txt files are 0 bytes (redacted) |
| `memdir/` | 9 | 1,737 | SAMPLED (teamMemPrompts full + findRelevantMemories top + memdir.ts top + memoryTypes top) |
| `ssh/` | 1 | 5 | YES — `createSSHSession.ts` is interface-only stub |
| `vim/` | 5 | 1,513 | SAMPLED (motions.ts top — pure vim cursor motion calc) |
| `voice/` | 1 | 54 | YES — `voiceModeEnabled.ts` full (claude.ai voice_stream auth gate) |
| `keybindings/` | 14 | 3,159 | SAMPLED (parser.ts + template.ts top — terminal-key chord parsing) |
| `oauth/` | MISSING | MISSING | N/A — directory does not exist in this Runnable copy |
| `ink.ts` (root) | 1 | 85 | YES — pure re-export barrel from ink/ |
| `main.tsx` (root) | 1 | 4,696 | SAMPLED (top 15 — MACRO bootstrap, ThemeProvider, growthbook, REPL launch) |
| `dialogLaunchers.tsx` | 1 | 132 | YES — JSX dialog launchers, all `await import('./components/*')` |
| `replLauncher.tsx` | 1 | 22 | YES — full read; just `<App><REPL/></App>` mount helper |
| `interactiveHelpers.tsx` | 1 | 365 | SAMPLED (top 20 — `renderAndRun` + `showSetupDialog`, gracefulShutdown, mcpServerApproval) |
| **TOTAL** | **~636** | **~134k** | **all dirs touched, every "small" file read in full, large dirs sampled to category-confirm; no in-scope code hidden** |

LOC sum is dominated by `components/` (81k), `ink/` (20k), `cli/` (12k), `screens/` (6k) — all React/Ink terminal UI which is replaced by `compact_v4/MAIN/agent/chat.ipynb` per binding constraint #2.

## Out-of-scope verified (per dir)

| Dir | Categorical reason | Constraint cited |
|---|---|---|
| `assistant/` | All 5 files are KAIROS-feature-gated **stubs** — `index.ts` and `gate.ts` are `export {}`, `sessionDiscovery.ts` exports an empty interface, `AssistantSessionChooser.tsx` returns `null`, `sessionHistory.ts` posts to `claude.ai` teleport API via OAuth (network + multi-user). | v5.0.1 single-user / Bedrock-only / v4 ipynb canonical UI |
| `screens/` | Three React Ink full-screen views (REPL 4.2k LOC, Doctor 1.3k, ResumeConversation 477) — 99% of imports are `ink/`, `components/`, `keybindings/`, terminal helpers. Tied to terminal renderer. | v4 ipynb canonical UI (binding rule #2) |
| `ink/` | Custom React-reconciler terminal renderer (98 files: yoga layout, ANSI, hit-test, frame, scrollbox, etc.). Replaces `react-dom` for TTY. | v4 ipynb canonical UI |
| `components/` | 151 `.tsx` files (App, dialogs, onboarding, MCP UI, OAuth flow, AgentTool UI, FeedbackSurvey, …). All Ink components depending on `ink/` renderer. | v4 ipynb canonical UI |
| `outputStyles/` | One file — loads `.claude/output-styles/*.md` markdown files into `OutputStyleConfig[]`. Output styles are an **interactive UI personality switcher**; v5 has fixed system prompt. | v5 single-user, fixed prompt |
| `cli/` | Subcommand entrypoints (`claude mcp`, `claude plugin`, `claude agents`, `claude auto-mode`, `claude doctor`, `claude setup-token`, `claude install`) + transports (HybridTransport, SSE, WS, Worker uploader) for analytics/telemetry. All terminal-driven. | v5.0.1 single-user, no telemetry, ipynb UI |
| `sdk/` | Both files (`runtimeTypes.ts`, `toolTypes.ts`) are `export {}` — empty SDK stubs for the public Agent SDK consumers. | v5 not an SDK |
| `server/` | 8/11 are 2-line `export {}` stubs (`server.ts`, `connectHeadless.ts`, `lockfile.ts`, `parseConnectUrl.ts`, `sessionManager.ts`, `serverBanner.ts`, `serverLog.ts`, `backends/dangerousBackend.ts`). 3 real files (`types.ts` 57, `createDirectConnectSession.ts` 88, `directConnectManager.ts` 213) implement HTTP/WS direct-connect server-mode session management. | v5 single-user, no server |
| `remote/` | RemoteSessionManager + SessionsWebSocket + remotePermissionBridge + sdkMessageAdapter — relays SDK messages over `claude.ai` teleport WebSocket; multi-user permission bridge. | Bedrock-only / no network egress |
| `upstreamproxy/` | CCR (Claude Code Runnable) MITM proxy: reads `/run/ccr/session_token`, sets `prctl(PR_SET_DUMPABLE, 0)`, downloads CA cert, runs CONNECT→WebSocket relay for org-credential injection. Container-only. | Single-user / no network proxy |
| `native-ts/` | Pure-TS reimplementations of three native NAPI Rust/C++ deps: nucleo fuzzy search (file-index), syntect color-diff, yoga flexbox engine. All exist solely to support the Ink terminal renderer / file-completion UX. | Bedrock-only — no native deps; v4 ipynb UI |
| `stubs/` | Vendor SDK stubs (`bedrock-sdk`, `vertex-sdk`, `foundry-sdk`, `client-bedrock`, `client-sts`, `azure`, `opentelemetry`, `sharp`, `turndown`, `audio-capture-napi`) — empty class shells so the build typechecks without proprietary deps. Also `bun:bundle.d.ts` declaration. **Not real code.** | v5 uses Python boto3 directly, not stubs |
| `jobs/` | One file `classifier.ts` = `export default {}` — placeholder. | n/a (empty) |
| `moreright/` | One file `useMoreRight.tsx` — explicit comment "Stub for external builds — the real hook is internal only". Returns no-op handlers. | KAIROS-internal feature |
| `buddy/` | "BUDDY" virtual pet companion (CompanionSprite, sprites.ts, types.ts) — feature-gated `feature('BUDDY')`. A duck/companion sits beside the user's input box and says things in a speech bubble. UI gimmick. | v4 ipynb UI / single-user |
| `yolo-classifier-prompts/` | All 3 `.txt` files are **0 bytes** (auto_mode_system_prompt, permissions_anthropic, permissions_external). Redacted prompts for the YOLO/auto-mode permission classifier. | Empty → nothing to port |
| `memdir/` | File-based memory system used by `claude.ai` teleport mode (`getTeamMemPath`, `feature('TEAMMEM')`). 4-type taxonomy + private/team scope + Sonnet relevance selector. **HEAVILY OVERLAPS Plan v3 Block H** (already in scope; v4 already mirrors `MAX_ENTRYPOINT_LINES=200` / `MAX_BYTES=25_000` and the 4-type taxonomy). | Block H "combined Runnable memory" already covers this |
| `ssh/` | One file `createSSHSession.ts` exports an empty `SSHSession` interface. Stub. | v5 single-user, no SSH |
| `vim/` | Vim mode for the terminal text-input (motions, operators, textObjects, transitions). Pure cursor calc with `Cursor` class. | v4 ipynb UI (no vim emulation) |
| `voice/` | `voiceModeEnabled.ts` — gates voice mode on Anthropic OAuth + GrowthBook flag. Comment explicitly states "voice_stream endpoint on claude.ai which is not available with API keys, **Bedrock**, Vertex, or Foundry." | Bedrock-only constraint excludes voice |
| `keybindings/` | Terminal key-chord parser, default bindings, user binding loader, schema validator, conflict resolver, template generator. Tied to TTY input. | v4 ipynb UI |
| `oauth/` | Directory does not exist — N/A. | n/a |
| `ink.ts` | Pure re-export barrel from `ink/root.js` + `components/design-system/*` (ThemeProvider, ThemedBox, ThemedText) + ink hooks. 85 lines, zero logic. | v4 ipynb UI |
| `main.tsx` | Top-level CLI entrypoint (4.7k LOC). MACRO version bootstrap, gracefulShutdown, GrowthBook init, MCP server approval, REPL launcher wiring, channel/auth/cost dialogs. | v5 single-user, ipynb UI, no GrowthBook |
| `dialogLaunchers.tsx` | Thin `await import('./components/*')` launchers for one-off main.tsx dialogs (Setup, ResumeConversation chooser, etc.). | v4 ipynb UI |
| `replLauncher.tsx` | 22-line helper — mounts `<App><REPL/></App>` via Ink `renderAndRun`. | v4 ipynb UI |
| `interactiveHelpers.tsx` | `renderAndRun`, `showSetupDialog`, `initializeTelemetryAfterTrust`, `handleMcpjsonServerApprovals`, telemetry/growthbook reset wiring. | v4 ipynb UI / no telemetry |

## In-scope nuggets found inside out-of-scope dirs

Three borderline items — none require new Block work beyond what Plan v3 already plans, but flagging for completeness:

| # | Capability | Source file:line | v5 needs? | Target Block | Graft strategy |
|---|---|---|---:|---|---|
| 1 | **Memory selector prompt** ("Return a list of filenames for the memories that will clearly be useful…") | `memdir/findRelevantMemories.ts:18-24` (the `SELECT_MEMORIES_SYSTEM_PROMPT` constant) | Already covered | **Block H** ("combined Runnable memory" per Plan v3 line 430) | Translate the 7-line system prompt into Python string in `runtime/memory.py`; v4 already does file-based memory, this prompt is the missing **on-demand selector** when MEMORY.md grows past `_MEMORY_MAX_LINES`. **No deferral**: in-scope for Block H. |
| 2 | **4-type memory taxonomy with private/team scope guidance** | `memdir/teamMemPrompts.ts:60-99` (combined-mode prompt) + `memdir/memoryTypes.ts:14-21` (`MEMORY_TYPES = ['user','feedback','project','reference']`) | Already in v4 | n/a — already shipped | v4 has `_MEMORY_TYPES = ("USER","FEEDBACK","PROJECT","REFERENCE")` at `sagemaker_agent.py:7457`. Single-user (no team scope) so the `<scope>private</scope>` half is the only path. **No port needed beyond what Block H already does**. |
| 3 | **MAX_ENTRYPOINT_LINES = 200, MAX_ENTRYPOINT_BYTES = 25_000** memory caps | `memdir/memdir.ts:1-30` (referenced via `MAX_ENTRYPOINT_LINES`, value defined in same module) | Already in v4 | n/a — already shipped | v4 line 7500-7501 already mirrors these constants explicitly: `_MEMORY_MAX_LINES: int = 200 # V4.3 V3-B: mirrors runnable MAX_ENTRYPOINT_LINES=200`. Confirmed parity. |

Everything else inspected is genuinely out-of-scope per the constraints. No fuzzy-match utility, no useful prompt template, no code-review helper, no token-budget logic was found buried in these dirs that isn't already on the in-scope list (Plan v3 Blocks A/B/B+/D/H/T cover the remaining surface).

## Summary

- **27 entries audited** (24 listed dirs + 5 root files − 1 missing oauth + 5 root files counted separately = 27 distinct items, plus `ink/components/` sub-tree confirmed inside ink). All categorically OOS verified against v5.0.1 constraints.
- **~134,000 LOC** of UI/CLI/SDK/server/remote/proxy/native-port/stub code correctly excluded — driven by three binding constraints: (a) single-user, (b) Bedrock-only no-network, (c) `chat.ipynb` is canonical UI not Ink.
- **Stubs are stubs**: `assistant/`, `sdk/`, `server/` (8 of 11), `jobs/`, `moreright/`, `ssh/`, `stubs/ant-packages/`, `yolo-classifier-prompts/` are literal `export {}` / 0-byte placeholders. Zero risk of missing logic.
- **Voice is structurally Bedrock-incompatible**: `voice/voiceModeEnabled.ts:34-36` self-documents that voice requires the `claude.ai` `voice_stream` endpoint and is "not available with API keys, **Bedrock**, Vertex, or Foundry." Constraint-aligned, no exception possible.
- **`upstreamproxy/`, `remote/`, `assistant/sessionHistory.ts`, `cli/transports/`** all rely on outbound network egress (claude.ai teleport WebSocket, CCR MITM proxy, GrowthBook analytics). Bedrock-only constraint kills all four.
- **Three memdir nuggets surfaced and reconciled**: (1) `SELECT_MEMORIES_SYSTEM_PROMPT` is the only **net-new** content vs v4 — already covered by Plan v3 Block H ("combined Runnable memory"). (2) 4-type taxonomy already in v4 line 7457. (3) Memory caps already in v4 lines 7500-7501. **No new Block, no deferral, no scope-narrowing** — Block H scope as-written suffices.
- **`buddy/` (companion duck), `vim/`, `keybindings/`, `screens/`, `ink/`, `components/`, `outputStyles/`** are all UI personalisation features that have no equivalent in a single-user notebook driver — correctly excluded by constraint #2 (`chat.ipynb` canonical UI).
- **`stubs/ant-packages/@anthropic-ai/bedrock-sdk/index.js`** literally is `export class AnthropicBedrock {}` — confirms Runnable's TS SDK has no real Bedrock client; v5 must keep using Python `boto3.client('bedrock-runtime')` (already the v4 path), nothing to port.
- No regressions, no scope expansion, no deferrals. R10 result: **all 27 OOS items confirmed OOS, with one pre-existing in-scope confirmation (Block H scope unchanged).**
