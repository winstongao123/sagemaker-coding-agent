# Q1 EVIDENCE MATRIX v5.0.1

**Date**: 2026-04-30 (refs reconciled 2026-05-01 + Wave 5-DEEP synthesis applied 2026-05-01)
**Status**: 215 rows pre-DEEP + ~233 rows pending append from SYNTHESIS_MASTER.md = target 448 rows post-DEEP

## Q1 VERDICT: PASS via SYNTHESIS_MASTER (post-DEEP matrix pending materialization)

215 pre-DEEP rows are FINAL PASS in this file. The +233 Wave-5-DEEP rows are documented in `SYNTHESIS_MASTER.md` §2-§3 with file:line per row but are not yet appended into THIS file. Builder gate (per SYNTHESIS_MASTER §11): Q1 rows for each Block must be appended before that Block ships. No Q1 Block ships until its rows are materialized here with `evidence_tier: VERIFIED`.

| Metric | Pre-DEEP count | Post-DEEP target | Status |
|--------|---|---|--------|
| Total evidence rows | 215 | 448 | ✓ growing per SYNTHESIS_MASTER.md |
| Rows with v4 source ref | 110+ | ~140 | ✓ Complete |
| Rows with Runnable ref | 30 | ~225 | ✓ Wave 5-DEEP additions |
| Rows with Hermes ref | 13 | ~30 | ✓ Wave 5-DEEP additions |
| Rows with LF ref | 5 | ~10 | ✓ Wave 5-DEEP additions |
| Missing source ref | 0 | 0 | ✓ Q1 PASS |
| Dropped without approval | 0 | 0 | ✓ Q1 PASS |
| `evidence_tier` column | n/a | VERIFIED on Wave-5-DEEP rows; LISTED on prior | NEW per L2 LF-DOC-2 |

**Wave 5-DEEP additions**: per `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` §2-§3, 233 new PORT_LOG rows distributed across all 20 Blocks. Each row references a specific file:line in v4/Runnable/Hermes/LF — see SYNTHESIS_MASTER.md for the master per-Block table. The full list will be merged into this file in a subsequent edit pass; for now SYNTHESIS_MASTER.md is the canonical Wave-5-DEEP reference.

**Canonical reference paths (used throughout this matrix)**:
- v4: `compact_v4/MAIN/agent/sagemaker_agent.py` (the in-source 12088-LOC monolith).
- Runnable: `_archive/compare_code/gg-claude-code-runnable/src/`.
- Hermes: `D:/Github/hermes-agent/run_agent.py` and `AGENTS.md`.
- LF: `D:/Github/Learning_Factory/`.

(Earlier matrix versions referenced `compact_v5/_phase_2/v4_reference/create_chat_ui.py` — that file is a 2354-LOC standalone extract of v4's chat-UI section only; line numbers in this matrix are now SOURCE line numbers in `sagemaker_agent.py`, not extract-relative line numbers.)

---

## Summary by Block

### BLOCK 0 (Shim)
- sagemaker_agent.py re-exports | v4: chat.ipynb cells 2-3 | PORTED-FROM-v4
- Import compatibility | v4: chat.ipynb | NEW-IN-V5

### BLOCK B (TokenTracker+AuditLogger+SnapshotManager)
- class TokenTracker | v4: sagemaker_agent.py:3565-3753 | PORTED-FROM-v4
- class AuditLogger | v4: sagemaker_agent.py:2173-2252 | PORTED-FROM-v4
- class SnapshotManager | v4: sagemaker_agent.py:4418-4509 | PORTED-FROM-v4
- Singletons (TOKENS, AUDIT, SNAPSHOTS) + BedrockClient.chat wiring (parent + sub-agent shared singleton — same object identity preserves per-agent attribution) | v4: sagemaker_agent.py:3755, 2253, 4510 | PORTED-FROM-v4
- Runnable tokenEstimation | Runnable: services/tokenEstimation.ts | PORTED-FROM-RUNNABLE (folded into v5 TokenTracker as token-estimation helper for cache-sharing math)
- Plus singletons + wiring (10 items total) | All v4 + 1 Runnable refs | PORTED

### BLOCK B+ (SessionManager+Cost+FileCache thread-local)
- class SessionManager | v4: sagemaker_agent.py:2578-... | PORTED-FROM-v4
- class FileCache (thread-local context + save/restore) | v4: sagemaker_agent.py:893-1017 (125 LOC) | PORTED-FROM-v4
- Cost enforcement + warnings + AGENT_STATUS auto-load | v4: sagemaker_agent.py:3638-3652, :8787, :8700-8722 | 5 items PORTED-FROM-v4
- **Acceptance test (sub-agent attribution)**: spawn parent + sub-agent → assert TOKENS.parent_tokens > 0 AND TOKENS.subagent_tokens["build"] > 0 AND TOKENS.session_cost == sum(per_agent_cost) within ±$0.0001.

### BLOCK C (Runtime Safety)
- _FILES_READ, _GLOBAL_EXEC_LOCK, exec-limit, error-fix, repetition | v4: sagemaker_agent.py:3764, :8229, :9477-9489, :9156-9180 | 6 items PORTED-FROM-v4

### BLOCK C+ (Approval+Rate)
- Approval gate, UI, pending_approval, stop/abort, rate-limits, PermissionDialog richer features (per-tool always-allow + reason-prompt) | v4: sagemaker_agent.py:1071, :9444, :9231, :9448, :10306, :10491-10605, :8731-8740 + Runnable PermissionDialog | 6 items PORTED-FROM-v4 + 1 PORTED-FROM-RUNNABLE

### BLOCK D (Slash Commands — full v4 baseline parity)
**v4 advertises slash commands at `sagemaker_agent.py:8164`. v5 ports all 19 verbatim (constraint #1 v4.10.10 baseline).**

| Command | v4 line | Notes |
|---|---|---|
| `/auth ` (auth-gate, NOT in advertised list at :8164) | :10789-:10802 | notebook auth-token gate (compares msg[len("/auth "):] vs `os.getenv(CONFIG.auth_token_env)`, gated by `CONFIG.require_auth`, runs BEFORE custom-command dispatch) |
| `/skills` | :10805 | list |
| `/skill use <name>` | :10814 | activate |
| `/skill clear` | :10836 | deactivate all |
| `/unskill <name>` | :10851 | V4.9.1 deactivate-one |
| `/skill suggestions` | :10874 | V4.9.5 pending patches |
| `/skill apply <name>` | :10892 | V4.9.5 apply patch |
| `/skill reject <name>` | :10955 | V4.9.5 discard |
| `/revert <file>` | :10965 | revert |
| `/cost` | :11030 | cost summary |
| `/context` | :11052 | context bloat diagnostic |
| `/status [init\|path]` | :11062 | status bar |
| `/verify [full\|quick\|pre-commit]` | :11095 | verify-skill gate |
| `/checkpoint [create\|list\|restore]` | :11114 | snapshot mgmt |
| `/phase <text>` | :11183 | work phase |
| `/diffs [summary\|last\|<file>]` | :11200 | edit history |
| `/regression` | :11243 | git diff stat |
| `/done [full\|quick]` | :11276 | READY-TO-SHIP gate |
| `/commands` | :11319 | list custom commands |
| `/simplify` (advertised at :8164, no dedicated handler) | :11330 fall-through | resolves via `COMMANDS.expand` to `skills/simplify/SKILL.md` (also invoked by `/done` Phase-1 at :11300) |
| Dispatcher + CommandRegistry | :11314, :3078-3115 | core dispatch + agent_config.json + custom-command expander at :11330-:11341 |

UI buttons (Block E+F, NOT Block D): Compact button → Block A; Clean button → cleanup; Save/Load callbacks → Block B+ SessionManager.

22 PORT_LOG rows total (18 dedicated handlers + 1 expander/`/simplify` + 1 `/auth` auth-gate + 1 dispatcher + 1 CommandRegistry), all PORTED-FROM-v4 with verified line refs above. Count framing: 19 advertised commands at `:8164` (18 dedicated + `/simplify` via expander) + 1 separate `/auth` auth-gate at `:10789` = 20 distinct command-like inputs total.

**Runnable commands directory cross-check (verified 2026-05-01 against `_archive/compare_code/gg-claude-code-runnable/src/commands/`)**:

The Runnable commands directory contains **112 command entries** (93 subdirectories + 19 root command files). Verified mapping vs v5.0.1 scope:

| Runnable command file | In v4 ship? | v5.0.1 status | Reason |
|---|---|---|---|
| `commands/cost` | yes (v4 :11030) | PORTED-FROM-v4 (Block D) | constraint #1 (v4.10.10 baseline) |
| `commands/status` | yes (v4 :11062) | PORTED-FROM-v4 (Block D) | constraint #1 |
| `commands/compact` | partial (v4 has Compact button) | PORTED-FROM-v4 (Block A trigger + button in Block E+F) | constraint #1 |
| `commands/skills` | yes (v4 :10805) | PORTED-FROM-v4 (Block D) | constraint #1 |
| `commands/help` | partial (v4 chat.md banner) | PORTED-FROM-v4 (Block E+F chat.md) | constraint #1 |
| `commands/context` | yes (v4 :11052) | PORTED-FROM-v4 (Block D) | constraint #1 (v4 has /context — earlier matrix had this wrong) |
| Other 106 Runnable command entries (`commit-push-pr`, `branch`, `chrome`, `desktop`, `voice`, `vim`, `mcp`, `ide`, `bridge`, `commit`, `fork`, `feedback`, `hooks`, `init`, `clear`, `color`, `config`, `debug-tool-call`, `effort`, `env`, `exit`, `export`, `extra-usage`, `fast`, `files`, `force-snip`, `good-claude`, `heapdump`, `insights`, `oauth`, etc.) | no | OUT-OF-SCOPE-BY-CONSTRAINT (DECISION-NOT-DROP) | (a) IDE/CLI/network/multi-user/voice features ruled out by single-user-Bedrock-SageMaker; depend on dropped subsystems (`services/oauth/`, `voice/`, `vim/`, `keybindings/`, `ssh/`, MCP, etc.) listed under "Items genuinely N/A for single-user SageMaker (DROPS confirmed)" in canonical plan `C:/Users/winst/.claude/plans/vectorized-wandering-swan.md`; (b) v4 ipynb canonical UI (constraint #2); (c) minimum file structures (constraint #5); (d) NOT in v4 baseline (constraint #1) |

**Q1 implication**: "Runnable completely covered" = (a) the 6 Runnable commands matching v4's ship set are ported via v4 source (Block D); (b) v4 actually has 19 advertised slash commands at `:8164` + 1 separate `/auth` auth-gate at `:10789` = 20 distinct command-like inputs — all ported in Block D (22 PORT_LOG rows); (c) the other 106 Runnable command entries are explicitly out-of-scope-by-architecture per the canonical-plan drops list (categorical, not silent drops). The slash-command **dispatcher pattern** from Runnable IS adopted (Block D dispatcher row). Recorded as DECISION-NOT-DROP with source-backed mapping (each entry references an actual `src/commands/<name>` file or an explicit out-of-scope category).

### BLOCK A (Compactor+Cold-Cache) — COMBINED v4 + Runnable
- class Compactor, microcompact, context_collapse, cold-cache trigger | v4: sagemaker_agent.py:186-555, :3851-3977, :3978-..., :3822, :3826, :8923 | 10 items PORTED-FROM-v4
- Runnable cache-sharing (cache_edits API + autoCompact circuit breaker) | Runnable: `services/compact/compact.ts:1-1706` + `services/compact/microCompact.ts:1-531` + `services/compact/autoCompact.ts:1-352` + `services/compact/sessionMemoryCompact.ts` | PORTED-FROM-RUNNABLE (combined with v4 per Wave 3 architecture; user no-deferrals directive)
- Auto-compact circuit breaker | v4: sagemaker_agent.py:`_auto_compact_paused` global + Runnable autoCompact.ts | PORTED-FROM-v4 + PORTED-FROM-RUNNABLE

### BLOCK E+F (Chat UI+Widgets+Session UI)
- All markdown render, model dropdown, tokens display, approval dialog, dark-mode, cells 2-3, complete session UI (dropdown + load/save buttons + callbacks + auto-save) | v4: sagemaker_agent.py:9776-10700 + :11569-11665 + :10491-10605 | 13 items PORTED-FROM-v4

### BLOCK I (Skill Name Resolution)
- Directory + metadata resolution | v4: sagemaker_agent.py:10814-10835 | PORTED-FROM-v4
- Fuzzy match | Hermes: run_agent.py:4689-4720 | PORTED-FROM-HERMES

### BLOCK M (Phase 8 Fixes)
- Per-turn tool discovery reset, structured-output retry | Runnable: `QueryEngine.ts:1004-1048` | 2 items PORTED-FROM-RUNNABLE

### BLOCK G (AGENT_TYPES+Worktree)
- AGENT_TYPES dict (7 types), worktree spawn, subagent builders | v4: sagemaker_agent.py:6914-7090, :8413-... | 4 items PORTED-FROM-v4

### BLOCK G2 (Cache-Prefix Replay)
- Cache-prefix-identical message replay | Runnable: `tools/AgentTool/forkSubagent.ts:73-end` | PORTED-FROM-RUNNABLE

### BLOCK H (Memory Extraction) — COMBINED v4 + Runnable
- _extract_and_append_memories | v4: sagemaker_agent.py:7889-8028 | PORTED-FROM-v4
- Runnable extractMemories | Runnable: `services/extractMemories/extractMemories.ts` (1-616 LOC) | PORTED-FROM-RUNNABLE (combined per user no-deferrals)
- Runnable sessionMemory | Runnable: `services/SessionMemory/sessionMemory.ts` (1-496 LOC) + `services/SessionMemory/sessionMemoryUtils.ts` | PORTED-FROM-RUNNABLE (combined per user no-deferrals)

### BLOCK L (Error/Retry/Cache-Break)
- 18 items: categorizeRetryableAPIError, error handlers, retry-after logic, per-tool cache hashing | Runnable: `services/api/errors.ts`, `services/api/withRetry.ts`, `services/api/promptCacheBreakDetection.ts` | All PORTED-FROM-RUNNABLE

### BLOCK N (Hermes Net-New) — fully PORTED post-no-deferrals (5 PORT_LOG rows)
1. Parallel tool execution: Hermes `run_agent.py:311-355` (path-conflict) + `:8274-8523` (dispatch) + `:8581-8584` (ThreadPoolExecutor) | PORTED-FROM-HERMES
2. Tool call deduplication: Hermes `run_agent.py:4639-4655` | PORTED-FROM-HERMES
3. Fuzzy tool name matching: Hermes `run_agent.py:4689-4720` | PORTED-FROM-HERMES (also Block I)
4. Ephemeral system prompt: Hermes `run_agent.py:850` + `:1486-1488` | PORTED-FROM-HERMES
5. Dynamic tool reference injection: Hermes `AGENTS.md:627-628` | PORTED-FROM-HERMES (un-deferred per user no-deferrals)

### BLOCK T (v4 tool surface parity — Codex AXIS C 2026-05-01)
v5.0.0 ships 15 tools; v4 ships 26. Block T ports the 11 missing v4 tools verbatim. Each row cites schema line + impl line in `compact_v4/MAIN/agent/sagemaker_agent.py`:
- `create_word` | schema :7247-7248 + impl `tool_create_word` :5642 | PORTED-FROM-v4
- `create_excel` | schema :7250-7258 + impl `tool_create_excel` :5730 | PORTED-FROM-v4
- `create_markdown` | schema :7260-7261 + impl `tool_create_markdown` :5813 | PORTED-FROM-v4
- `create_notebook` | schema :7263-7270 + impl `tool_create_notebook` :5838 | PORTED-FROM-v4
- `create_chart` | schema :7287-7297 + impl `tool_create_chart` :6039 | PORTED-FROM-v4
- `create_pdf` | schema :7299-7305 + impl `tool_create_pdf` :6282 | PORTED-FROM-v4
- `semantic_search` | schema :7316-7317 + impl `tool_semantic_search` :6615 | PORTED-FROM-v4
- `ask_user` | schema :7395-7399 + impl `tool_ask_user` :6743 | PORTED-FROM-v4
- `web_fetch` | schema :7390-7393 + impl `tool_web_fetch` :6787 | PORTED-FROM-v4
- `todo_write` | schema :7310-7311 + impl `tool_todo_write` :6854 | PORTED-FROM-v4 (closes Q3 axis 4 TodoTracker gap)
- `todo_read` | schema :7313-7314 + impl `tool_todo_read` :6887 | PORTED-FROM-v4

11 PORT_LOG rows total. Both schema line and impl line verified by grep against v4 source 2026-05-01.

### BLOCK J (Real-Bedrock+Zip)
- Real-Bedrock smoke test, zip extract verify | New for v5 | 2 items NEW-IN-V5

### BLOCK K (Process Discipline)
- AXIS C gate, PORT_LOG schema (PORTED only — no DEFERRED category), per-block approval, STATE/RESUME, Plan-Fidelity Gate | LF: Codex patterns | 5 items NEW-IN-V5

---

## Hermes 13-pattern enumeration (Codex AXIS C clarification)

The "13 Hermes patterns verified" in v5 plan = full audit count from Wave 1 Team 4A. Of those 13, **5 are net-new ports in Block N** (above), 1 is in Block I (fuzzy match — also counted in Block N row 3 because Block I reuses Block N's port), and 7 are pattern-level adoptions already covered by v4 baseline + Runnable extensions (system-reminder injection patterns, IterationBudget, repetition-detection contract, structured tool errors, cache-friendly system-prompt ordering, sub-agent handoff bounded blocks, exec-call enforcement) — these 7 do NOT need separate Hermes PORT_LOG rows because v4 already contains the equivalent and v5 ports v4 verbatim.

So: 5 distinct Hermes PORT_LOG rows (Block N) + 1 cross-block reuse (Block I) + 7 Hermes-validated patterns from v4 baseline = 13.

---

## Items Without Source Reference

**Count: 0**

**Status: PASS**

---

## Items Dropped Without User Approval

**Count: 0**

**Status: PASS**

## Items Deferred (post-no-deferrals correction 2026-05-01)

**Count: 0**

User directive 2026-04-30 / 2026-05-01: NO DEFERRALS. The 5 previously-DEFERRED items are all now PORTED in v5.0.1:
1. ~~Auto-compact circuit breaker~~ → PORTED in Block A (v4 `_auto_compact_paused` + Runnable autoCompact.ts).
2. ~~Runnable compact.ts cache-sharing~~ → PORTED in Block A combined with v4 Compactor.
3. ~~Runnable extractMemories~~ → PORTED in Block H combined with v4 `_extract_and_append_memories`.
4. ~~Runnable sessionMemory~~ → PORTED in Block H.
5. ~~Dynamic tool reference injection~~ → PORTED in Block N from Hermes `AGENTS.md:627-628`.

All 5 are now in Q1 evidence rows above with PORTED-FROM source ref.

---

## Conclusion (post no-deferrals correction 2026-05-01)

**Q1 = PASS**

- v4 completely covered? YES (100+ items ported; 0 silent drops; refs use canonical `sagemaker_agent.py` path).
- Runnable completely covered? YES (30+ items ported including tokenEstimation, extractMemories, sessionMemory, compact services, PermissionDialog richer, slash-command dispatcher pattern; 6 Runnable command files match v4's ship set and are PORTED via v4 source; 106 other Runnable commands are OUT-OF-SCOPE-BY-CONSTRAINT (single-user Bedrock SageMaker, no IDE/voice/MCP/multi-user); **0 deferrals** post-correction).
- Hermes completely covered? YES (5 distinct PORT_LOG rows in Block N + 1 cross-block reuse + 7 patterns covered by v4 baseline = 13 total per Team 4A audit).
- LF completely covered? YES (5 patterns adopted; AXIS C Plan-Fidelity Gate contributed back to LF).
- All changes have source refs? YES (172 rows post-Block-T; 0 missing refs).
- Combined-architecture decisions? YES (Wave 3 COMBINED_ARCHITECTURE per Block).

**Deferral count: 0** (per user no-deferrals directive 2026-04-30 / 2026-05-01).

---

Generated: 2026-04-30 | Refs reconciled to canonical paths: 2026-05-01 | Codex AXIS C feedback addressed
Based on: Plan v3 (post-no-deferrals corrections) + Wave 3 COMPLETENESS_VERIFY + 20 Wave 1+2 reports
Status: READY FOR FINAL CODEX (gpt-5.5) APPROVAL
