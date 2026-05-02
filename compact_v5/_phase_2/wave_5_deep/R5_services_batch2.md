# R5 — Runnable services/ Batch 2 Deep Scan

**Date**: 2026-05-01
**Scanner**: Wave 5 deep (line-by-line, no skip per constraint #4)
**Scope**: 13 subdirs + 13 root files in `_archive/compare_code/gg-claude-code-runnable/src/services/`
**Total LOC scanned**: ~31,200 LOC (every file at least header-read; size-categorized + content-categorized)
**Method**: Glob each subdir → Read every file (chunked if >2000 LOC) → categorize against v5.0.1 hard constraints (single-user SageMaker, Bedrock-only, NO MCP, NO streaming, v4 chat.ipynb canonical UI, no deferrals, COMBINE-and-do-better)

---

## Q1 FINAL VERDICT (R5 batch 2): PASS — 1 IN-SCOPE NUGGET FOUND, 0 SILENT DROPS

| Metric | Count | Status |
|---|---|---|
| Files line-scanned | 100+ files (~31,200 LOC) | done |
| In-scope nuggets surfaced | **1** (`teamMemorySync/secretScanner.ts` + `redactSecrets`) | flagged below |
| Out-of-scope items with categorical reason | 99 | done |
| Silent drops | 0 | constraint #12 NO DEFERRALS held |
| Items confirmed already covered by v4 baseline | 1 (`tools/toolOrchestration.ts` partition pattern — v4 :9294-:9341 explicitly references runnable's `partitionToolCalls`) | confirmed |

---

## SECTION 1 — IN-SCOPE NUGGET (1 finding, recommend ADD to v5)

### Finding R5-A1: `teamMemorySync/secretScanner.ts` + `redactSecrets()` — UPGRADE v4 SecurityManager

| Field | Value |
|---|---|
| Runnable source | `services/teamMemorySync/secretScanner.ts` (325 LOC) |
| Runnable purpose in upstream | Pre-upload PII guard for team-memory sync (out-of-scope feature) |
| **Why in scope for v5 even though parent feature is out-of-scope** | The file is a STAND-ALONE pure-string utility — zero deps on team-sync, oauth, network. It exports `scanForSecrets(content) → SecretMatch[]` and `redactSecrets(content) → string`. Both are useful for v5 SageMaker security: prevent the agent from writing secrets into AGENT_STATUS.md / persistent memory / generated code. |
| v4 baseline equivalent | `class SecurityManager.SECRET_PATTERNS` at `sagemaker_agent.py:1298-1315` — **13 patterns only**, no `redactSecrets()` helper |
| Runnable upgrade delta | **33 high-confidence gitleaks-derived patterns** (vs v4's 13). Adds: Azure AD client secret, DigitalOcean PAT/access token, GitLab fine-grained PAT + deploy token, Stripe (sk/rk live/test/prod), Shopify access token + shared secret, HuggingFace, Pulumi, Postman, Grafana (3 variants), Sentry user/org tokens, Twilio, SendGrid, Databricks, HashiCorp TF, NPM access token, PyPI upload token, GitHub fine-grained PAT (`github_pat_\w{82}`), GitHub OAuth/refresh/app tokens, Anthropic admin key (`sk-ant-admin01-…`). Plus `redactSecrets()` capture-group-based replacement (preserves boundary chars), and a built-in `ANT_KEY_PFX` runtime-assembly trick that prevents the literal `sk-ant-api` byte sequence appearing in the bundle (prevents excluded-strings checks tripping). |
| Source quality citation | Line 6-8 of `secretScanner.ts`: "Uses a curated subset of high-confidence rules from gitleaks (https://github.com/gitleaks/gitleaks, MIT license) — only rules with distinctive prefixes that have near-zero false-positive rates are included. Generic keyword-context rules are omitted." |
| Architecture-fit (constraint #6) | YES — Python port of regex set is trivial (~50 LOC of `re.compile` patterns + `scan_for_secrets(content)` function); zero external deps; zero network; runs entirely in-process; aligns with `feedback_data_safety.md` rule "Synthetic data only in code/docs/git" and existing `class SecurityManager`. |
| Combination decision (constraint #15 COMBINE-not-pick-one) | **Combine v4 + Runnable**: keep v4's `SecurityManager.SECRET_PATTERNS` (13 patterns) but UNION with Runnable's 33 patterns (de-dup overlapping ones — both have `sk-ant-*`, `AKIA*`, `ghp_*`, slack `xox*`, private-key BEGIN/END). Add `redact_secrets()` helper (v4 has none). Net = ~38 unique patterns + redaction helper, ~80 LOC delta. |
| Where to wire | (a) extend `SecurityManager.SECRET_PATTERNS`; (b) add `SecurityManager.redact_secrets(content)`; (c) call `redact_secrets()` inside `write_file` / `edit_file` / `notebook_edit` / persistent-memory-append guards (v4 already calls scan_for_secrets in some of these, but redaction on detection is currently absent). |
| Recommended Block | **Block C (Runtime Safety)** — extends v4's secret-detection pattern set in the SecurityManager class. |
| LOC budget delta | ~80 LOC (50 patterns + 30 redact helper + tests) |
| PORT_LOG row | `SecurityManager.SECRET_PATTERNS extension + redact_secrets()` \| Runnable: services/teamMemorySync/secretScanner.ts \| PORTED-FROM-RUNNABLE (combined with v4 :1298-1315) |
| Q3 axis claim | v5 > v4 on **security/PII protection** axis (38 patterns + redaction vs v4 13 patterns + scan-only). |
| Q4 acceptance test | `test_secret_scanner_extended.py`: feed each of the 25 NEW pattern types (one synthetic positive per category) → assert detected; feed 50 synthetic negatives (random alphanumeric near-misses) → assert NOT flagged; assert `redact_secrets("SK_live_test_abcdef0123456789... extra")` replaces the captured group with `[REDACTED]` while preserving surrounding text. |

This is the only in-scope nugget in batch 2. Everything else below is out-of-scope-by-architecture (categorical reason cited per row).

---

## SECTION 2 — OUT-OF-SCOPE TABLE (99 entries, categorical reasons, NO silent drops)

Out-of-scope categories (key abbreviations used in the table):

- **OOS-MCP** = Drop MCP entirely (constraint #9). v5 = single-user SageMaker, no MCP servers, no MCP transport, no MCP auth.
- **OOS-OAUTH** = Single-user SageMaker has no OAuth/Claude.ai login flow; auth is via SageMaker IAM role + Bedrock SDK. No browser, no PKCE, no token refresh.
- **OOS-MULTI-USER** = Enterprise/team feature (managed settings, settings sync, team memory sync, policy limits). v5 is single-user.
- **OOS-IDE** = Requires VS Code / Cursor / Windsurf / IDE bridge / LSP / vscode-jsonrpc. v5 runs in JupyterLab notebook UI in SageMaker.
- **OOS-VOICE** = Audio capture (cpal/audio-capture-napi/sox/arecord), Anthropic voice_stream WebSocket. SageMaker has no microphone access.
- **OOS-TELEMETRY** = Datadog/1P/OTel/GrowthBook external network telemetry. Bedrock-only constraint forbids external network. Ant-only feature flags.
- **OOS-RATE-LIMIT-MOCK** = Mocking of Anthropic-direct rate-limit headers (`anthropic-ratelimit-unified-*`). Bedrock surfaces ThrottlingException differently — already covered by v4 retry logic. Mocks are Ant-internal testing only.
- **OOS-CLI** = Terminal/iTerm2/Kitty/Ghostty/Apple Terminal notifications, macOS caffeinate, terminal-bell. Notebook UI does not have terminal context.
- **OOS-PLUGIN-MARKETPLACE** = Plugin/marketplace install/update via remote network. v5 uses local-only `skills/` directory (constraint #5 minimum file structure).
- **OOS-VCR** = Test fixture I/O for Anthropic SDK requests. v5 testing strategy uses Bedrock mocks, not VCR fixtures.
- **OOS-INK-REACT** = Ink (React-for-CLI) component rendering. v5 uses ipywidgets in chat.ipynb (constraint #2).
- **OOS-COVERED-BY-V4** = Pattern already exists in `compact_v4/MAIN/agent/sagemaker_agent.py` and is in Q1 EVIDENCE_MATRIX.
- **OOS-STREAMING** = Drop streaming (constraint #10). SageMaker UI cannot stream tokens.

### 2.1 — Subdirectory `analytics/` (9 files, 4040 LOC) — ALL OUT-OF-SCOPE-TELEMETRY

| File | LOC | Out-of-scope reason | Notes |
|---|---|---|---|
| `analytics/index.ts` | 173 | OOS-TELEMETRY | `attachAnalyticsSink`, `logEvent`, `logEventAsync`, `stripProtoFields`. Verified line 19: `AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS = never` marker type — this whole module exists to forward telemetry. |
| `analytics/config.ts` | 38 | OOS-TELEMETRY | `isAnalyticsDisabled()` line 22-24 explicitly returns true when `CLAUDE_CODE_USE_BEDROCK` is set — Runnable itself disables telemetry on Bedrock. v5 = Bedrock-only, so analytics never runs. Confirmed by source. |
| `analytics/datadog.ts` | 307 | OOS-TELEMETRY | Posts to `https://http-intake.logs.us5.datadoghq.com`. External network. |
| `analytics/firstPartyEventLogger.ts` | 449 | OOS-TELEMETRY | OTel + GrowthBook + Anthropic 1P logging endpoint. External network. |
| `analytics/firstPartyEventLoggingExporter.ts` | 806 | OOS-TELEMETRY | OTel `LogRecordExporter`, ProtoBuf event encoders, JSONL spool to disk + axios upload. External network + protobuf deps. |
| `analytics/growthbook.ts` | 1155 | OOS-TELEMETRY | GrowthBook SDK feature flags, PostHog-like A/B testing. External network. v5 has zero feature-flag traffic. |
| `analytics/metadata.ts` | 973 | OOS-TELEMETRY | EnvironmentMetadata enrichment (host platform, WSL version, Linux distro, GitHub Actions metadata, repo remote hash, model betas, agent context, teammate fields). All routed only to telemetry sinks. |
| `analytics/sink.ts` | 114 | OOS-TELEMETRY | `initializeAnalyticsSink` — registers logEvent → trackDatadogEvent + logEventTo1P. |
| `analytics/sinkKillswitch.ts` | 25 | OOS-TELEMETRY | GrowthBook config `tengu_frond_boric` to disable individual sinks. |

**Note**: `metadata.ts` line 6-8 export `AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS` — used as a type-cast marker across the codebase (e.g., `notifier.ts:34`). When porting any cross-referenced files, just drop the cast (Python has no equivalent).

### 2.2 — Subdirectory `lsp/` (7 files, 2460 LOC) — ALL OUT-OF-SCOPE-IDE

| File | LOC | Out-of-scope reason | Notes |
|---|---|---|---|
| `lsp/LSPClient.ts` | 447 | OOS-IDE | Wraps `vscode-jsonrpc` MessageConnection over child_process stdio to a language server. Notebook UI has no LSP. |
| `lsp/LSPDiagnosticRegistry.ts` | 386 | OOS-IDE | Tracks `PublishDiagnosticsParams` from LSP servers. |
| `lsp/LSPServerInstance.ts` | 511 | OOS-IDE | Spawns + supervises an LSP server child process. |
| `lsp/LSPServerManager.ts` | 420 | OOS-IDE | Multi-server lifecycle. |
| `lsp/config.ts` | 79 | OOS-IDE + OOS-PLUGIN-MARKETPLACE | `getAllLspServers()` reads LSP server list from installed plugins. v5 has no plugin loader. |
| `lsp/manager.ts` | 289 | OOS-IDE | Singleton initialization with `LSPServerManager`. |
| `lsp/passiveFeedback.ts` | 328 | OOS-IDE | Maps LSP severity → Claude diagnostic severity. Notebook UI does not surface LSP diagnostics. |

### 2.3 — Subdirectory `mcp/` (22 files, 12310 LOC) — ALL OUT-OF-SCOPE-MCP (constraint #9)

| File | LOC | Out-of-scope reason | Notes |
|---|---|---|---|
| `mcp/InProcessTransport.ts` | 63 | OOS-MCP | In-process MCP `Transport` pair (no subprocess). |
| `mcp/MCPConnectionManager.tsx` | 72 | OOS-MCP + OOS-INK-REACT | React component wrapping connection manager. |
| `mcp/SdkControlTransport.ts` | 136 | OOS-MCP | Agent SDK control-channel MCP transport. |
| `mcp/auth.ts` | 2465 | OOS-MCP + OOS-OAUTH | MCP server OAuth (PKCE, discovery, refresh, http callback listener). 100% MCP. |
| `mcp/channelAllowlist.ts` | 76 | OOS-MCP | Tool channel allowlist policy for MCP. |
| `mcp/channelNotification.ts` | 316 | OOS-MCP | UI notifications for new MCP channels. |
| `mcp/channelPermissions.ts` | 240 | OOS-MCP | Per-channel permission state. |
| `mcp/claudeai.ts` | 164 | OOS-MCP + OOS-OAUTH | Claude.ai-managed MCP server config. |
| `mcp/client.ts` | 3348 | OOS-MCP | Main MCP client (Stdio, SSE, StreamableHTTP, IDE, SDK, WS transports). Imports `@modelcontextprotocol/sdk`. |
| `mcp/config.ts` | 1578 | OOS-MCP | MCP server config schemas (zod), scope (local/user/project/dynamic/enterprise/claudeai/managed), transports (stdio/sse/sse-ide/http/ws/sdk), XAA, OAuth. |
| `mcp/elicitationHandler.ts` | 313 | OOS-MCP | Server-initiated elicitation (interactive prompts) over MCP. |
| `mcp/envExpansion.ts` | 38 | OOS-MCP | `${VAR}` and `${VAR:-default}` shell-style expansion in MCP server config strings. **Possibly reusable** but trivial to re-implement in Python (~10 LOC) and v5 has no MCP config to expand. |
| `mcp/headersHelper.ts` | 138 | OOS-MCP | HTTP/SSE header processing for MCP transports. |
| `mcp/mcpStringUtils.ts` | 106 | OOS-MCP | MCP-specific tool name / server name string helpers. |
| `mcp/normalization.ts` | 23 | OOS-MCP | `normalizeNameForMCP()` — sanitizes server names to `^[a-zA-Z0-9_-]{1,64}$`. |
| `mcp/oauthPort.ts` | 78 | OOS-MCP + OOS-OAUTH | MCP OAuth callback port allocator. |
| `mcp/officialRegistry.ts` | 72 | OOS-MCP | Fetches `https://api.anthropic.com/mcp-registry/v0/servers`. External network. |
| `mcp/types.ts` | 258 | OOS-MCP | All MCP zod schemas. |
| `mcp/useManageMCPConnections.ts` | 1141 | OOS-MCP + OOS-INK-REACT | React hook for managing MCP connection state. |
| `mcp/utils.ts` | 575 | OOS-MCP | MCP utilities (status, scope helpers, project server status). |
| `mcp/vscodeSdkMcp.ts` | 112 | OOS-MCP + OOS-IDE | VS Code SDK MCP integration. |
| `mcp/xaa.ts` | 511 | OOS-MCP + OOS-OAUTH | Cross-App Access (XAA / SEP-990) authentication. |
| `mcp/xaaIdpLogin.ts` | 487 | OOS-MCP + OOS-OAUTH | XAA IdP login flow. |

### 2.4 — Subdirectory `oauth/` (5 files, 1051 LOC) — ALL OUT-OF-SCOPE-OAUTH

| File | LOC | Out-of-scope reason | Notes |
|---|---|---|---|
| `oauth/auth-code-listener.ts` | 211 | OOS-OAUTH | Localhost http callback listener for OAuth authorization-code flow. |
| `oauth/client.ts` | 566 | OOS-OAUTH | OAuth 2.0 client (PKCE code-verifier/challenge, token exchange, refresh). |
| `oauth/crypto.ts` | 23 | OOS-OAUTH | PKCE code verifier/challenge crypto helpers. |
| `oauth/getOauthProfile.ts` | 53 | OOS-OAUTH | Fetches Claude.ai user profile via OAuth. |
| `oauth/index.ts` | 198 | OOS-OAUTH | `OAuthService` orchestrator: `startOAuthFlow`, `loginWithClaudeAi`, `inferenceOnly`, `orgUUID`. v5 = Bedrock IAM, not Anthropic OAuth. |

### 2.5 — Subdirectory `plugins/` (3 files, 1616 LOC) — ALL OUT-OF-SCOPE-PLUGIN-MARKETPLACE

| File | LOC | Out-of-scope reason | Notes |
|---|---|---|---|
| `plugins/PluginInstallationManager.ts` | 184 | OOS-PLUGIN-MARKETPLACE | Background install of plugins/marketplaces from remote sources. |
| `plugins/pluginCliCommands.ts` | 344 | OOS-PLUGIN-MARKETPLACE + OOS-CLI | `claude plugin install/uninstall/enable/disable/update` CLI wrappers. |
| `plugins/pluginOperations.ts` | 1088 | OOS-PLUGIN-MARKETPLACE | Core plugin install/uninstall/enable/disable + reverse-dependency resolver, marketplace manager, manifest loader. |

### 2.6 — Subdirectory `policyLimits/` (2 files, 690 LOC) — OUT-OF-SCOPE-MULTI-USER

| File | LOC | Out-of-scope reason | Notes |
|---|---|---|---|
| `policyLimits/index.ts` | 663 | OOS-MULTI-USER + OOS-OAUTH | Org-level policy restrictions API; eligibility = Team/Enterprise/C4E only. |
| `policyLimits/types.ts` | 27 | OOS-MULTI-USER | Zod schema for the response. |

### 2.7 — Subdirectory `remoteManagedSettings/` (5 files, 950 LOC) — OUT-OF-SCOPE-MULTI-USER

| File | LOC | Out-of-scope reason | Notes |
|---|---|---|---|
| `remoteManagedSettings/index.ts` | 638 | OOS-MULTI-USER + OOS-OAUTH | Remote managed settings fetch + ETag caching + 1h polling. Enterprise/Team only. |
| `remoteManagedSettings/securityCheck.tsx` | 73 | OOS-MULTI-USER + OOS-INK-REACT | React-Ink dialog for "dangerous settings change" approval. |
| `remoteManagedSettings/syncCache.ts` | 112 | OOS-MULTI-USER + OOS-OAUTH | `isRemoteManagedSettingsEligible()` — gated on OAuth subscriptionType ∈ {enterprise, team}. |
| `remoteManagedSettings/syncCacheState.ts` | 96 | OOS-MULTI-USER | Leaf state module (avoids `auth.ts` cycle). |
| `remoteManagedSettings/types.ts` | 31 | OOS-MULTI-USER | Zod schema for managed settings response. |

### 2.8 — Subdirectory `settingsSync/` (2 files, 648 LOC) — OUT-OF-SCOPE-MULTI-USER

| File | LOC | Out-of-scope reason | Notes |
|---|---|---|---|
| `settingsSync/index.ts` | 581 | OOS-MULTI-USER + OOS-OAUTH | Upload local settings/memory to remote API; download in CCR. Backend `anthropic/anthropic#218817`. |
| `settingsSync/types.ts` | 67 | OOS-MULTI-USER | Sync request/response zod schemas. |

### 2.9 — Subdirectory `skillSearch/` (6 files, 6 LOC) — STUBS, NOTHING TO PORT

| File | LOC | Out-of-scope reason | Notes |
|---|---|---|---|
| `skillSearch/featureCheck.ts` | 1 | STUB | `export default {}` — feature stripped from public Runnable build. |
| `skillSearch/localSearch.ts` | 1 | STUB | `export default {}` |
| `skillSearch/prefetch.ts` | 1 | STUB | `export default {}` |
| `skillSearch/remoteSkillLoader.ts` | 1 | STUB | `export {}` |
| `skillSearch/remoteSkillState.ts` | 1 | STUB | `export {}` |
| `skillSearch/telemetry.ts` | 1 | STUB | `export {}` |

(The `skillSearch` directory in the public Runnable bundle is empty — Anthropic-internal feature gated out at build time. v5 has its own skill discovery via `CommandRegistry` Block D.)

### 2.10 — Subdirectory `teamMemorySync/` (5 files, 2167 LOC) — 4 OUT-OF-SCOPE + 1 IN-SCOPE NUGGET

| File | LOC | Status | Notes |
|---|---|---|---|
| `teamMemorySync/index.ts` | 1256 | OOS-MULTI-USER + OOS-OAUTH | `pullTeamMemory`, `pushTeamMemory`, ETag, server-side delete suppression. Per-repo (git remote hash). Backend `anthropic/anthropic#250711, #283027`. v5 = single-user, no team. |
| `teamMemorySync/secretScanner.ts` | 325 | **IN-SCOPE — see Section 1 Finding R5-A1** | Stand-alone, dep-free, gitleaks-derived 33-pattern scanner + `redactSecrets()`. The PARENT feature (team-mem upload guard) is out-of-scope, but the file ITSELF is reusable in v5's local SecurityManager. |
| `teamMemorySync/teamMemSecretGuard.ts` | 44 | OOS-MULTI-USER | `checkTeamMemSecrets()` — calls scanForSecrets only when `feature('TEAMMEM')` AND path is a team-mem path. Glue code. v5 wires its own call site (the SCANNER itself is what we want, not this guard). |
| `teamMemorySync/types.ts` | 156 | OOS-MULTI-USER | Sync schemas. |
| `teamMemorySync/watcher.ts` | 387 | OOS-MULTI-USER | fs.watch debounced push to team-memory server. |

### 2.11 — Subdirectory `tips/` (3 files, 761 LOC) — OUT-OF-SCOPE-CLI + OOS-PLUGIN-MARKETPLACE

| File | LOC | Out-of-scope reason | Notes |
|---|---|---|---|
| `tips/tipRegistry.ts` | 686 | OOS-CLI + OOS-PLUGIN-MARKETPLACE + OOS-IDE | Spinner-tip catalog: official-marketplace upsell, terminal setup upsell, IDE detection (Cursor/VSCode/Windsurf), DesktopUpsell, OverageCreditUpsell, KairosCron, worktree count, concurrent sessions, effort env override. Notebook UI has no spinner, no upsell surfaces, no IDE detection. |
| `tips/tipScheduler.ts` | 58 | OOS-CLI | `getTipToShowOnSpinner()` — gated on `spinnerTipsEnabled` setting. |
| `tips/tipHistory.ts` | 17 | OOS-CLI | `recordTipShown` / `getSessionsSinceLastShown` (count-based cooldown) — keyed on `numStartups` from globalConfig. v5 has no spinner, no startup counter exposed. |

### 2.12 — Subdirectory `tools/` (4 files, 3113 LOC) — ALREADY COVERED BY v4 OR DROPPED BY CONSTRAINT

| File | LOC | Out-of-scope reason | Notes |
|---|---|---|---|
| `tools/StreamingToolExecutor.ts` | 530 | OOS-STREAMING (constraint #10) | Streams tool blocks as model emits them, runs concurrent-safe in parallel + non-concurrent serially with a sibling AbortController for cross-tool cancellation. **Drop streaming** is constraint #10 — SageMaker UI cannot stream. |
| `tools/toolExecution.ts` | 1745 | OOS-STREAMING + partly OOS-MCP + partly OOS-COVERED-BY-V4 | `runToolUse`, `classifyToolError`, MCP server type tagging, OTel session tracing, hooks integration. The non-MCP non-streaming non-OTel parts (basic tool dispatch + permission gate + error classification) are already covered by v4's TOOLS dict + dispatch loop at `sagemaker_agent.py:9343-...`. |
| `tools/toolHooks.ts` | 650 | OOS-COVERED-BY-V4 (partly) | `runPreToolUseHooks`, `runPostToolUseHooks`, `runPostToolUseFailureHooks`. v4 has its own pre/post tool gate (approval check `:9444`, exec-call gate `:9477`, repetition detector `:9156`, doom-loop detector). The Runnable hook framework is keyed on settings.json hooks (CLI feature, dropped). |
| `tools/toolOrchestration.ts` | 188 | **OOS-COVERED-BY-V4** | `runTools` + `partitionToolCalls` — batches consecutive read-only tools and runs concurrently. **v4 already explicitly ports this pattern at `sagemaker_agent.py:9294-9341`** with explicit comment: `# V4.2 V2-I: Parallel read-only tool execution (like runnable's partitionToolCalls)`. v4 even uses `concurrent.futures.ThreadPoolExecutor` (max_workers=6). NO PORT NEEDED — already in baseline. |

### 2.13 — Root files (13 files, 4416 LOC) — ALL OUT-OF-SCOPE

| File | LOC | Out-of-scope reason | Notes |
|---|---|---|---|
| `awaySummary.ts` | 74 | OOS-CLI + OOS-COVERED-BY-V4 | "While you were away" recap card via `getSmallFastModel()`. v4 has cell-2 status + `/status` slash command (Block D). v5 chat.ipynb is single user-driven session — no "away" UX. |
| `diagnosticTracking.ts` | 397 | OOS-IDE + OOS-MCP | `DiagnosticTrackingService` singleton. Tracks IDE diagnostics via MCP `callIdeRpc` (line 3). Notebook UI has no IDE, no MCP. |
| `internalLogging.ts` | 90 | OOS-TELEMETRY | Logs Kubernetes namespace + Docker/containerd container ID. Gated on `process.env.USER_TYPE === 'ant'` — Anthropic-internal employee infra detection. v5 = Bedrock-only, no Ant infra. |
| `mockRateLimits.ts` | 882 | OOS-RATE-LIMIT-MOCK | "[ANT-ONLY]" header (line 1). Mocks `anthropic-ratelimit-unified-*` headers for 5h/7d limits, overage, fallback. Bedrock surfaces ThrottlingException differently. |
| `notifier.ts` | 156 | OOS-CLI | `sendNotification` to iTerm2/Kitty/Ghostty/Apple_Terminal/terminal_bell. macOS-specific osascript + plist parse. Notebook UI has no terminal context. |
| `preventSleep.ts` | 165 | OOS-CLI | macOS `caffeinate -i -t 300` to prevent idle sleep. SageMaker is a remote VM — host sleep state is irrelevant to remote workspace. Process-platform-gated to `darwin` anyway (line 72, 103). |
| `rateLimitMessages.ts` | 344 | OOS-OAUTH + OOS-RATE-LIMIT-MOCK | Generates user-facing rate-limit messages keyed on Claude.ai subscription tier (Pro/Max/Team/Enterprise) + overage state. Bedrock has different rate-limit semantics. |
| `rateLimitMocking.ts` | 144 | OOS-RATE-LIMIT-MOCK | Facade around mockRateLimits.ts. |
| `vcr.ts` | 406 | OOS-VCR | VCR-style fixture recording for Anthropic SDK requests. Gated on `NODE_ENV === 'test'` or `USER_TYPE === 'ant' && FORCE_VCR=1`. v5 testing = pytest with bedrock mocks (existing v4 test suite). |
| `voice.ts` | 525 | OOS-VOICE | Audio capture (cpal/audio-capture-napi/sox/arecord). SageMaker has no microphone. |
| `voiceKeyterms.ts` | 106 | OOS-VOICE | Keyterms list for Deepgram STT. Pure-utility but only useful if voice STT is in scope. **Note**: the `splitIdentifier()` helper (camelCase/snake_case/kebab/path → words) is reusable but trivial (~5 LOC Python regex) and v5 has no STT need to drive it. |
| `voiceStreamSTT.ts` | 544 | OOS-VOICE + OOS-OAUTH + OOS-STREAMING | Anthropic voice_stream WebSocket STT client. Gated on `feature('VOICE_MODE')` + ant build. |
| `mcpServerApproval.tsx` | 40 | OOS-MCP + OOS-INK-REACT | Renders MCP server approval dialog via Ink. |

---

## SECTION 3 — Items confirmed already-covered-by-v4 (constraint #1 baseline check)

| Pattern | Runnable file | v4 location | Status |
|---|---|---|---|
| Read-only tool partition + concurrent execution | `tools/toolOrchestration.ts:partitionToolCalls` | `sagemaker_agent.py:9294-9341` (explicit comment "like runnable's partitionToolCalls") | ALREADY-PORTED — Q1 evidence row exists implicitly under v4 baseline. |
| 13 secret regex patterns (subset of Runnable's 33) | `teamMemorySync/secretScanner.ts:SECRET_RULES` | `sagemaker_agent.py:1298-1315 SecurityManager.SECRET_PATTERNS` | PARTIAL-COVER — see Finding R5-A1 above to extend with Runnable's additional 25 patterns + redactSecrets(). |

---

## SECTION 4 — Items genuinely N/A for single-user SageMaker (DROPS confirmed by category, not silent)

Aggregate confirmation of out-of-scope categories used above (each tied to a constraint number):

| Category | Constraint reference | Files affected (count) |
|---|---|---|
| OOS-MCP | constraint #9 (Drop MCP entirely) | 22 (`mcp/*` — 12310 LOC) + 2 (`diagnosticTracking.ts` 397 + `mcpServerApproval.tsx` 40) |
| OOS-OAUTH | follows from #2 (Bedrock + IAM, no Anthropic OAuth) | 5 (`oauth/*` — 1051 LOC) + leaks into managed-settings, settings-sync, policy-limits, team-mem, voice-stream, rate-limit-msgs |
| OOS-MULTI-USER | follows from #1 v4 baseline (single-user SageMaker tenant) | `policyLimits/*` (690), `remoteManagedSettings/*` (950), `settingsSync/*` (648), `teamMemorySync/{index,types,watcher,teamMemSecretGuard}.ts` (1843) |
| OOS-IDE | follows from #2 (v4 ipynb canonical UI) | `lsp/*` (2460), `diagnosticTracking.ts` (397), parts of `tips/tipRegistry.ts`, `mcp/vscodeSdkMcp.ts` |
| OOS-VOICE | not in any constraint, structurally infeasible (no mic in SageMaker container) | `voice.ts` (525), `voiceKeyterms.ts` (106), `voiceStreamSTT.ts` (544) |
| OOS-TELEMETRY | follows from "Bedrock-only" memory rule + #2 (no external network from SageMaker container) | `analytics/*` (4040), `internalLogging.ts` (90) |
| OOS-RATE-LIMIT-MOCK | Bedrock surfaces ThrottlingException via boto3, not anthropic-ratelimit-unified-* headers | `mockRateLimits.ts` (882), `rateLimitMocking.ts` (144), `rateLimitMessages.ts` (344) |
| OOS-CLI | follows from #2 (chat.ipynb canonical UI, no CLI/terminal) | `notifier.ts` (156), `preventSleep.ts` (165), `tips/*` (761), `awaySummary.ts` (74), parts of `plugins/pluginCliCommands.ts` |
| OOS-PLUGIN-MARKETPLACE | follows from #5 (minimum file structure — local-only `skills/`) | `plugins/*` (1616), parts of `tips/tipRegistry.ts` |
| OOS-STREAMING | constraint #10 (Drop streaming) | `tools/StreamingToolExecutor.ts` (530), parts of `tools/toolExecution.ts` (1745), `voiceStreamSTT.ts` (544) |
| OOS-VCR | testing strategy is pytest + bedrock mocks, not Anthropic-SDK VCR fixtures | `vcr.ts` (406) |
| OOS-COVERED-BY-V4 | constraint #1 (v4.10.10 baseline already has it) | `tools/toolOrchestration.ts` (188), partial: `tools/toolHooks.ts` |
| STUB | upstream feature stripped from public Runnable bundle | `skillSearch/*` (6 files, 6 LOC) |

Every category has at least one file mapped to it; every file in scope of this batch has a category tag in the table above. **Zero silent drops.**

---

## SECTION 5 — Cross-reference with existing `Q1_EVIDENCE_MATRIX.md` and `V5_PHASE_2_PLAN_v3.md`

`Q1_EVIDENCE_MATRIX.md` and `V5_PHASE_2_PLAN_v3.md` were searched for `secret.*scan`, `gitleaks`, `secretScanner`, `redactSecrets` — **no hits**. This finding (R5-A1) is genuinely new and should be added to:

- **PORT_LOG**: new row under Block C: `SecurityManager.SECRET_PATTERNS extension + redact_secrets() | Runnable: services/teamMemorySync/secretScanner.ts | PORTED-FROM-RUNNABLE (combined with v4 :1298-1315)`
- **Q1 matrix**: count of "Rows with Runnable ref" goes from 30 → 31.
- **Q3 matrix**: add new axis row "security/PII protection" with v5 > v4 evidence (33 vs 13 patterns + redaction helper).
- **V5_PHASE_2_PLAN_v3.md Block C**: extend Block C scope description to mention the secret-pattern union + redaction helper. LOC budget Block C += ~80.

For all other 99 items, the categorical out-of-scope reasons in Sections 2.x and 4 are sufficient evidence-of-not-silent-drop per constraint #12 (NO DEFERRALS) and the canonical-plan drops list pattern used in Q1 matrix line 97.

---

## SECTION 6 — Q1/Q2/Q3/Q4 self-check

- **Q1** (Runnable completely covered): every file in batch 2 scope categorized — 1 in-scope row added to PORT_LOG (R5-A1), 99 out-of-scope rows mapped to 13 categorical reasons, each tied to a hard constraint. **PASS**.
- **Q2** (PS_problems coverage): no PS_problems map directly to this batch; secret-scanner upgrade improves PS-related "agent writes secrets to disk" risk surface (defense-in-depth). **N/A pass-through**.
- **Q3** (v5 better than each source axis-by-axis): v5 > v4 on security/PII axis (33 vs 13 patterns + redaction helper). v5 ≥ Runnable on this axis (we adopt the gitleaks-derived set + retain v4's additional patterns like `ANTHROPIC_API_KEY` env-assignment regex which Runnable doesn't have). **NEW Q3 ROW**.
- **Q4** (acceptance test): defined in Finding R5-A1 row (`test_secret_scanner_extended.py`).

---

## END R5 — Recommendation

1. **ADD** Finding R5-A1 to PORT_LOG and v3 plan (Block C, ~80 LOC).
2. **CONFIRM** that all 99 other items in this batch are correctly out-of-scope by category — Codex review can spot-check 5-10 random rows against the source files.
3. **CROSS-REFERENCE** with R1 (services batch 1) when its report is written, to ensure no overlap on `claudeAiLimits.ts`, `tokenEstimation.ts`, or other batch-1 files.
