# V5 Phase 2 Plan — corrective build to meet v4 baseline + v5 > Runnable goal

**Date**: 2026-04-30
**Status**: SYNTHESIS DRAFT (pending hermes_full + learning_factory_full reports + Codex review)
**Purpose**: Drive the v5.0.1 corrective build that actually meets the original V5_PLAN.md success metrics, after the v5.0.0 build candidate failed user verification.

---

## 1. Why Phase 1 (the 14-phase v5.0.0 build) FAILED — root cause

The 14-phase v5 build mechanically passed all internal gates (437 mock tests, parity 15/15 + 10/10, audit 7/7 metrics, Codex-clean per phase) but the user's four verification questions (Q1 observation completeness, Q2 PS Issues recurrence, Q3 v5>v4+Runnable evidence, Q4 semantic-bug certainty) all returned UNSATISFACTORY.

**Root cause: silent scope narrowing across phases passed gates that didn't measure plan fidelity.**

Specifics (from Team 4B/Learning Factory + Team 1B/non-UI parity audit):
- The Codex review template had AXIS A (correctness) + AXIS B (Runnable-fidelity) but NO AXIS C (plan-fidelity = "did this phase deliver V5_PLAN.md §Phase N?").
- Per-phase OUT-OF-SCOPE lists buried in changelogs were not mirrored in PORT_LOG. Audit gate counted PORT_LOG rows, not deferrals.
- The original V5_PLAN.md success metric #1 ("functional parity with v4.10.10") was not enforced by any test.
- v4 features dropped without explicit user approval: Compactor (microcompact + context_collapse + 2-stage smart compact), TokenTracker, max_exec_calls enforcement, /save /load /cost /status /compact /clean slash commands, full chat HTML rendering, AGENT_TYPES (build/plan/explore/verify), worktree isolation, SnapshotManager wiring, AuditLogger wiring, memory extraction, cold-cache detection.

**Fix for Phase 2**: Codex review must now include AXIS C plan-fidelity. Every PORT_LOG row must mark deferrals as DEFERRED-WITH-USER-APPROVAL or NOT include them at all. The v4 baseline is non-negotiable.

---

## 2. Hard constraints (consolidated from user 2026-04-30)

1. **v4.10.10 = baseline** (functional capability is the floor; PS_problems are the only known v4 failures).
2. **v4 chat.ipynb = canonical UI** (v5 provides `sagemaker_agent` import shim; v4 notebook works UNCHANGED).
3. **Cover ALL four reference repos** (v4 + Runnable + Hermes + Learning Factory; not subsets).
4. **Line-by-line investigation, no skipping** (the gate that prevents silent scope narrowing).
5. **Minimum file structures** (functional coverage MAX, file count MIN; no empty stubs, no over-modularization).
6. **Architecture-first thinking** before adopting any pattern (Runnable does X is not justification on its own).
7. **PS_problems addressed STRUCTURALLY** (not patched).
8. **v5 > Runnable > v4 > others** axis-by-axis with concrete evidence.

---

## 3. Comprehensive gap inventory (synthesized from 18 reports)

### 3.1 v4 features MISSING in v5 (must port for parity)

From Team 1A (UI) + Team 1B + Team 1B2 (cross-checker) + Wave 2 v4 §1-§4:

| Feature | v4 location | Severity | Effort | Block |
|---|---|---|---|---|
| `Compactor` (microcompact + context_collapse + 2-stage smart compact) | sagemaker_agent.py:Compactor (~500 LOC) | HIGH | LARGE | A |
| `TokenTracker` / `TOKENS` singleton + session_cost runtime | sagemaker_agent.py:3565 | HIGH | MEDIUM | B |
| `max_exec_calls_per_session=200` enforcement (200/session gate in bash + python_exec) | sagemaker_agent.py:9435 (gate) + 1080 (config) | HIGH | SMALL | C |
| `_extract_and_append_memories` (memory extraction at session end) | sagemaker_agent.py:7889 | MEDIUM | MEDIUM | H |
| `/save` / `/load` slash commands + session_cost persistence | sagemaker_agent.py:on_save/on_load ~11569 | HIGH | MEDIUM | D |
| `/cost` slash command | sagemaker_agent.py:11030 | HIGH | SMALL | D |
| `/status` slash command | sagemaker_agent.py:11062 | MEDIUM | SMALL | D |
| `/compact` / `/clean` slash commands | sagemaker_agent.py | HIGH/MEDIUM | SMALL | D |
| `/skill apply` UX (interactive diff preview + apply button) | sagemaker_agent.py:10892 | MEDIUM | MEDIUM | D |
| Full chat-display HTML rendering (~2350 LOC: render_chat, render_todos, _render_assistant_markdown, _format_inline_md, status bar, tokens display, model dropdown async validation, dark-mode toggle, approval/ask-user dialogs, sub-agent overrides panel) | sagemaker_agent.py:9735+ | HIGH | LARGE | E |
| AGENT_TYPES dict (build/plan/explore/verify/general/review/fork) — 7 types | sagemaker_agent.py:6914 | HIGH | MEDIUM | G |
| Worktree isolation for `build` agent | sagemaker_agent.py:8413 | MEDIUM | MEDIUM | G |
| Cold-cache detection (`COLD_CACHE_THRESHOLD_SECONDS=1800` + proactive microcompact) | sagemaker_agent.py:3826 + 8923 | MEDIUM | SMALL | A |
| `SnapshotManager` runtime singleton | sagemaker_agent.py:4510 | MEDIUM | MEDIUM | B |
| `AuditLogger` runtime singleton with audit_logs/<session>.jsonl | sagemaker_agent.py:2253 | HIGH | MEDIUM | B |
| Skill name vs directory name resolution (`/skill activate clara` → `clara-review`) | sagemaker_agent.py:10814 | HIGH | SMALL | I |
| Repetition-detection / tool-failure-detect (3+ identical reads) | sagemaker_agent.py:9156 | MEDIUM | SMALL | C-extension |
| Rate-limit enforcement (max_user_messages_per_minute, per_session) | sagemaker_agent.py:8731 | HIGH | SMALL | C-extension |
| Global exec lock `_GLOBAL_EXEC_LOCK` | sagemaker_agent.py:8229 | MEDIUM | SMALL | C-extension |
| `_FILES_READ` tracking (Runnable parity — model can't edit unread file) | sagemaker_agent.py:_FILES_READ | HIGH | SMALL | C-extension |
| Post-compact file restoration + TODO restoration | sagemaker_agent.py | HIGH | MEDIUM | A |
| `FILE_UNCHANGED_STUB` mtime-dedup (V4.2 V2-H token optimization, 0.5s tolerance) | sagemaker_agent.py | MEDIUM | SMALL | C-extension |
| 13-section LLM summary template | sagemaker_agent.py | MEDIUM | SMALL | A |
| SessionManager atomic save/load | sagemaker_agent.py:SessionManager | HIGH | SMALL | B |
| Auto-compact circuit breaker (pause after N failures) | sagemaker_agent.py:_auto_compact_paused | MEDIUM | SMALL | A |
| `_RECENT_DIFFS` tracking (sub-agent handoff source) | sagemaker_agent.py | MEDIUM | SMALL | G |
| `AGENT_STATUS.md` auto-load at startup | sagemaker_agent.py:_status_doc_path | MEDIUM | SMALL | B |

### 3.2 v4 UI surfaces MISSING (Block E — chat.ipynb canonical)

Team 1A finding: v5 ships 7 UI elements vs v4's 38 (18% parity). Wave 2 v4 §4 finding: 87 widgets/features audited, 82 MISSING in v5. Critical ship-blockers:

- Approval dialog (12 components missing — currently no diff_widget→approval flow wiring; user has zero control over file writes).
- Token/cost display (2 main components — users have zero cost visibility).
- Markdown rendering (6 functions — `_render_assistant_markdown`, `_format_inline_md`, table/list/header/code-block rendering — agent output shows raw markdown).
- Slash commands (16 commands — skill/session/cost/verify workflows unreachable).
- Model switcher (6 components — no runtime model switching).
- Ask-user dialog (agent can't ask clarifying questions interactively).
- Session persistence UI (can't resume after interruption).
- Status bar (Plan Mode / Thinking state / Active Skills / MCP status / phase text invisible).
- Parameter controls (temp / dark mode / budgets inaccessible mid-session).
- Compaction UI (context overflow handling internal-only, no user surface).

Estimated v4 chat UI: 2350 LOC. v5 currently: ~220 LOC. Gap: ~2100 LOC of UI behavior to restore.

### 3.3 Runnable patterns to ADOPT (architecture-fit checked)

From Team 2A/2B + Team 3A/3B + Wave 2 runnable_*:

**Architecture-fit OK + high user value (adopt in v5.0.1):**

- **`services/compact/compact.ts` (1706 LOC)**: full compaction orchestrator. Recommended over v4's older Compactor — Runnable has tengu events, cache-aware, prompt cache sharing, post-compact attachments. Block A.
- **`services/compact/microCompact.ts` (531 LOC)**: dual-tier (time-based + cache_edits API). Block A.
- **`services/compact/autoCompact.ts` (352 LOC)**: auto-trigger with consecutive-failure circuit breaker. Block A.
- **`services/extractMemories.ts` (616 LOC)**: closure-scoped, post-sampling hook trigger, configurable throttle. Block H.
- **`services/sessionMemory.ts` (496 LOC)**: 30s background notes extraction. Block H.
- **`services/agentSummary.ts` (180 LOC)**: 30s timer → forked agent → 3-5 word progress for sub-agent UI. Block G.
- **`services/api/errors.ts` (1207 LOC)**: 50+ error categories vs v5's 8. 18 critical variants missing (media validation, tool-use diagnostics, subscription-aware, auth source, CCR mode). Block B-extension.
- **`services/api/withRetry.ts` (823 LOC)**: 5 specialized paths NOT in v5 — foreground 529 gating, fast-mode fallback + cooldown, Opus fallback, persistent unattended retry, max-tokens overflow adjustment. Block B-extension.
- **`services/api/promptCacheBreakDetection.ts` (728 LOC)**: per-tool schema hashing (77% of breaks are description-only), cache-control hash, beta header tracking. Block B-extension.
- **`services/tokenEstimation.ts`**: pure utility for cost visibility. Block B.
- **Per-tool prompt content in `tools/<Name>/prompt.ts`**: WHEN/WHEN-NOT, substitution-on-failure guidance. v5 prompts paraphrased some away. Block E-prompts.
- **AgentTool/forkSubagent.ts**: fork-conversation cache-prefix-identical replay (currently dropped in v5 spawn.py). Architecture-fit: required for cache-stable sub-agent dispatch. Block G.
- **`<system-reminder>` injection patterns** (7 state types): plan-mode, repetition, blocked-permissions, approval-pending, deferred-tools (only this last is in v5). Block C-extension.
- **`stopHook.ts`**: runtime intervention for "I can't" patterns. Block C-extension.
- **Verification contract** (prompts.ts:390-394): independent adversarial gate; FAIL→fix→resume→PASS→spot-check. Block E-prompts.
- **Output efficiency / "write for humans" guidance** (prompts.ts:402-427). Block E-prompts.

**Architecturally-clean drops (TRUE non-applicable for single-user SageMaker .ipynb):**
- `services/oauth/`, `policyLimits/`, `teamMemorySync/`, `remoteManagedSettings/`, `voice*`, `keybindings/`, `vim/`, `ssh/`, `coordinator/`.

**GREY ZONE (defer to v5.1+):**
- `services/skillSearch/`, `services/diagnosticTracking.ts`, `outputStyles/`, `proactive/`, `commands/` (the slash command registry framework — but specific commands ARE Block D).

### 3.4 Hermes patterns

(Pending Wave 2 hermes_full report; from Wave 1 Team 4A:)

- **Failure-message-as-instruction** (H-003): partial in v5 (API errors only); missing for tool-execution errors. v4 had "OTHER TOOLS STILL WORK: read_file, grep, ..." pattern. Block C-extension.
- **Tool-failure graceful degradation** (H-004): NOT in v5. Block C-extension.
- **Dynamic tool references** (H-005, AGENTS.md §627-628): NOT in v5. Tool descriptions hardcode cross-tool mentions; should be injected based on active toolset. Block E-prompts.
- IterationBudget + skill-filter-by-tools: already ported.

### 3.5 Learning Factory patterns (process discipline)

(Pending Wave 2 LF_full report; from Wave 1 Team 4B:)

- **AXIS C plan-fidelity Codex review** (NEW pattern v5 must contribute back to LF): mandatory per-phase check that the phase delivered V5_PLAN.md §Phase N. Without this, scope narrows silently. Block K.
- **PORT_LOG must include DEFERRED rows** (with explicit user-approval status), not just ADOPTED rows. Block K.
- **Baseline-feature preservation rule**: distinguish MVP (deferrable) from baseline (requires user approval). For sagemaker-agent: Compactor, TokenTracker, exec-limit, save/load, full chat UI = baseline.

---

## 4. v5.0.1 patch agenda — the work

(Block ordering revised post Phase 2 to match user-visible impact AND v4 chat.ipynb canonical-UI rule.)

### Block 0 — `sagemaker_agent.py` shim (NEW, mandatory)
Make v4 chat.ipynb work UNCHANGED:
- Create `compact_v5/MAIN/agent/sagemaker_agent.py` re-exporting `CONFIG`, `BEDROCK_MODELS`, `create_chat_ui`, plus any other names v4 cells import.
- The shim is THE bridge. If v4 cell 2 + cell 3 don't run cleanly post-import, Block 0 fails.
- Lock test: extract zip in tmp, run v4 cells 1-3, verify success.

### Block A — Context management (Compactor + cold-cache + auto-compact)
Port Runnable `services/compact/` (compact.ts, microCompact.ts, autoCompact.ts) into `compact_v5/MAIN/agent/services/compact.py`. Wire into QueryEngine.run() at per-turn checkpoint.

### Block B — Cost + audit visibility (TokenTracker + AuditLogger + SnapshotManager)
Port Runnable `services/tokenEstimation.ts` + `errors.ts` extra categories into v5's existing core/errors.py + new `runtime/tokens.py`. Port v4's AuditLogger + SnapshotManager into `runtime/audit.py` + `runtime/snapshot.py` (v4 verbatim — both are stable). Wire into BedrockClient.chat / dispatch / skill apply.

### Block C — Runtime safety (exec-limit gate + rate limits + repetition detection + system-reminder injection)
Add `max_exec_calls_per_session=200` enforcement in bash + python_exec dispatch with the v4 misleading-error-fix-verbatim message. Port v4 rate-limit checks (max_user_messages_per_minute/session). Port repetition-detection (3+ identical reads) from v4 + Hermes failure-message-as-instruction pattern. Add `<system-reminder>` injection for plan-mode, repetition, blocked-permissions, approval-pending states (Runnable parity).

### Block D — Slash commands (`/save /load /cost /status /compact /clean /skill apply`)
Add slash-command dispatcher in `core/query_engine.py`. Each command wires to existing service (e.g. `/cost` → TokenTracker.report; `/compact` → Compactor.compact; `/skill apply` → SkillManager.apply_proposal + diff preview). Port v4 verbatim where commands are simple; port Runnable's `commands/` framework if architecture-fit (defer if it adds complexity).

### Block E — Full HTML chat rendering + v4 UI parity (THE BIG ONE)
Port v4's `_render_assistant_markdown` + `_format_inline_md` + `render_chat` + `render_todos` + `update_mode_display` + `update_tokens_display` from compact_v4/MAIN/agent/sagemaker_agent.py:9735-12088. Wire dark-mode toggle, model dropdown async validation, approval/ask-user dialogs, status bar, sub-agent overrides panel, parameter sliders, compact/clean buttons. Plus per-tool prompt content from Runnable `tools/<Name>/prompt.ts` (the WHEN/WHEN-NOT + substitution guidance v5 paraphrased away).

This is ~2100 LOC of UI behavior. Largest single block. v4 chat.ipynb depends on it.

### Block F — Cell 2 widgets + iteration budget slider
Port v4's cell 2: model dropdown, temperature slider, mock-mode checkbox, AWS-scope checkbox, iteration-budget slider (90-2000), workspace input, dark-mode toggle. Cell 3 banner echoing chosen settings.

### Block G — AGENT_TYPES + worktree + AgentSummary
Port v4 AGENT_TYPES dict (7 types: build, plan, explore, verify, general, review, fork). Port worktree-isolation for `build` agent. Port Runnable `agentSummary.ts` for sub-agent progress UI.

### Block H — Memory extraction + session memory
Port Runnable `extractMemories.ts` (verbatim) + `sessionMemory.ts` (verbatim). Wire into post-sampling hook + manual `/summary` command.

### Block I — Skill name resolution fix
Fix `skills/manager.py:activate(name)` so `/skill activate clara` resolves to the SKILL.md whose `name:` is `clara-review` AND/OR whose directory is `clara`. Lock test for all 10 skills via directory name.

### Block J — Real-Bedrock smoke + zip verification
Add manual env-gated real-Bedrock smoke test (`RUN_REAL_BEDROCK=1`). Update `verify_ship_zip.py` to extract in tmp + run `python -c "import entry"`.

### Block K — Process discipline (LF AXIS C + PORT_LOG DEFERRED rows)
Add AXIS C plan-fidelity check to Codex review template. Add PORT_LOG `DEFERRED-WITH-USER-APPROVAL` row category. Document the v5.0.1 PORT_LOG so every dropped v4 feature has either a PORTED row or a DEFERRED-with-user-approval row.

### Block L — Architecture-fit Runnable additions (errors, retry, cache-break, system-reminders)
Port Runnable error/retry/cache-break improvements into existing v5 surfaces (extend, don't replace). Add system-reminder injection patterns for Runnable parity.

### Block M — Phase 8 critical fixes (Wave 2 query_engine findings)
Fix the 2 Phase 8 gaps:
1. structured-output retry counter MISSING — could cause infinite loops on JSON failure. Port `countToolCalls` helper + retry-limit check.
2. `discoveredSkillNames` reset MISSING per turn — violates Phase 7 contract. 1-line trivial fix.

---

## 5. v4 chat.ipynb canonical-UI implementation strategy

Constraint: v4's chat.ipynb must run UNCHANGED in v5 (user directive).

Approach:
1. Create `compact_v5/MAIN/agent/sagemaker_agent.py` shim that re-exports the v4 import surface from v5 modules.
2. Port v4's `create_chat_ui` (~2350 LOC) into `compact_v5/MAIN/agent/ui/chat_ui_full.py` (or equivalent — preserving v4 behavior).
3. Make `sagemaker_agent.create_chat_ui = ui.chat_ui_full.create_chat_ui` so the cell-3 launch line works.
4. Cell 2 widget construction: keep v4's widget code working by exposing the same widget objects.
5. Smoke test: copy v4 chat.ipynb to a tmp location, run it programmatically via nbformat/jupyter execute, verify cells 1-3 succeed without modifications.

Rationale: porting the UI 1:1 is faster than rewriting; v4's UI is battle-tested.

Tradeoff for "minimum file structures": consolidate ui/ submodules into a single `ui/chat.py` if the line count works (~2500 LOC is borderline; if cleaner, split by surface — render / dialog / status_bar). Decision after porting.

---

## 6. Minimum file structure proposal

After v5.0.1 lands, target file count (consolidating where the v5 modular split doesn't earn its existence):

```
compact_v5/MAIN/agent/
├── chat.ipynb                      # v4 verbatim
├── chat.md                         # companion docs
├── sagemaker_agent.py              # shim — re-exports for v4 cells (Block 0)
├── entry.py                        # cell-0 import target (v5-native callers)
├── agent.py                        # Agent class (was __init__.py, renamed)
├── memory.md, AGENT_STATUS.md      # auto-load files
├── core.py                         # CONSOLIDATED: budget + retry + errors + query_engine + cache (was 5 files)
├── compact.py                      # NEW: Compactor (Block A)
├── tokens.py                       # NEW: TokenTracker (Block B)
├── audit.py                        # NEW: AuditLogger (Block B)
├── snapshot.py                     # NEW: SnapshotManager (Block B)
├── memory_extract.py               # NEW: extractMemories + sessionMemory (Block H)
├── tools.py                        # CONSOLIDATED: registry + 14 tool modules (was 16+ files)
├── tool_search.py                  # KEEP separate (Phase 7 specialized)
├── task.py                         # KEEP separate (sub-agent dispatch)
├── skills.py                       # CONSOLIDATED: manager + skill tool + propose-patch (was 3 files)
├── runtime.py                      # CONSOLIDATED: bedrock_client + config + session + file_cache + semantic_search (was 5 files)
├── prompt.py                       # CONSOLIDATED: sections.py + cache.py (was 2 files; .md sections kept separate)
├── prompt/<19 .md files>           # KEEP separate — sectioned + reviewable per ADR-002
├── ui.py                           # CONSOLIDATED: chat_ui + widgets + diff_widget (was 3 files)
├── subagent.py                     # CONSOLIDATED: env + handoff + spawn (was 3 files)
├── security.py                     # CONSOLIDATED: manager + dangerous_patterns + dangerous_python + high_risk (was 4 files)
├── skills/<10 dirs>/SKILL.md       # KEEP — content
└── tests/                          # KEEP separate (dev only; not shipped)
```

File count: ~22 .py files + 19 prompt .md + 10 SKILL.md = 51 files. v5.0.0 has 55+ Python files alone.

Final consolidation decision deferred until after Block A-M land — premature consolidation risks merging modules that should stay separate. Goal: every file justifies its boundary.

---

## 7. Architecture-fit notes (per user constraint)

For each Block, the architecture-fit decision was:

- **Block 0 (shim)**: REQUIRED for v4 ipynb canonical. Single file. Architecture: re-exports + adapter.
- **Block A (Compactor)**: Port Runnable's compact.ts (newer) over v4's. Architecture-fit: new module under core/ or services/. Wire at QueryEngine.run() pre-API checkpoint.
- **Block B (Tokens / Audit / Snapshot)**: Port v4's AuditLogger + SnapshotManager (v4-stable); port Runnable's tokenEstimation. Architecture-fit: separate runtime modules; tight wiring with BedrockClient + tool dispatch.
- **Block C (safety gates)**: Wire enforcement into existing tools/bash.py + tools/python_exec.py. No new modules; extend existing.
- **Block D (slash commands)**: New dispatcher in core/query_engine.py — single function with command table. Avoid Runnable's full `commands/` framework unless required.
- **Block E (HTML rendering)**: Port v4 verbatim into ui/. Largest block. v5's minimal MVP UI is REPLACED.
- **Block F (cell 2 widgets)**: Modify chat.ipynb (now v4-canonical) to keep widgets working with v5 backend.
- **Block G (AGENT_TYPES + worktree + AgentSummary)**: Extend subagent/spawn.py with agent-type registry. Port Runnable's agentSummary.ts.
- **Block H (extractMemories + sessionMemory)**: Port Runnable verbatim. Standalone modules.
- **Block I (skill name resolution)**: Fix in existing skills/manager.py.
- **Block J (real-Bedrock smoke + zip verify)**: Extend existing test_notebook_smoke.py + verify_ship_zip.py.
- **Block K (process discipline)**: Update Codex review template + PORT_LOG schema. No code change.
- **Block L (Runnable error/retry/cache-break)**: Extend existing core/errors.py + core/retry.py + core/cache.py — don't replace.
- **Block M (Phase 8 critical fixes)**: 2 small fixes in core/query_engine.py.

---

## 8. Verification plan (the ship gate)

v5.0.1 ships ONLY when:

1. **v4 chat.ipynb works UNCHANGED** in tmp-extracted zip (Block 0 verification).
2. **All 437 v5.0.0 mock tests still pass** + new tests for each block.
3. **Real-Bedrock smoke test passes** (env-gated manual run).
4. **Codex AXIS C plan-fidelity review** for the v5.0.1 patch (must say YES — every v4 baseline feature is either ported OR explicitly user-approved drop).
5. **The four user-verification questions return YES with file:line evidence** (Q1 observation completeness / Q2 PS Issues / Q3 v5>v4+Runnable / Q4 semantic-bug certainty).
6. **Aggregate audit 7/7 PASS** (preserved from v5.0.0 build).
7. **Static prompt token count ≤ 2500** (preserved from V5_PLAN.md original).
8. **Per-turn schema overhead ≥ 3000 tokens lower than v4** (preserved from V5_PLAN.md original).
9. **PORT_LOG complete**: every v4 baseline feature has a PORTED row or DEFERRED-with-user-approval row.

If ANY of the 9 fail, v5.0.1 does NOT ship.

---

## 9. Hermes + Learning Factory full findings (Wave 2 closeout)

### Hermes line-by-line (6 net-new patterns Hermes has that no other repo has)

From `D:/Github/hermes-agent/run_agent.py` (12.6k LOC) + AGENTS.md:

1. **Parallel tool execution with path-conflict detection** (run_agent.py:8274-8523) — Safely parallelizes independent tool calls; ~40% latency reduction. **HIGH-VALUE adoption** if architecture allows.
2. **Dynamic tool reference injection at runtime** (AGENTS.md:627-628) — Post-processes tool schemas at init; prevents hallucination of disabled tools. **HIGH-VALUE — prevents critical bug.**
3. **Ephemeral system prompt** (run_agent.py:850, 1486-1488) — Session prompt not saved to trajectories; privacy + testing feature.
4. **Fallback provider chain** (run_agent.py:1426-1443) — Ordered list of backup providers on failure. **N/A for Bedrock-only.**
5. **Tool-call deduplication** (run_agent.py:4639-4655) — Guards against model emitting same tool call twice.
6. **Fuzzy tool name matching** (run_agent.py:4689-4720) — Corrects typos before dispatch. **HIGH-VALUE for skill-name resolution (matches Block I).**

Hermes adoption recommendation: parallel tool exec + dynamic tool refs + fuzzy match + dedup → all in **Block N (NEW)**, ~10 hours total port effort. Skip fallback-provider (Bedrock-only).

### Learning Factory pattern audit findings

CORRECTLY APPLIED:
- R-105 No Retrofit (skills byte-for-byte from v4)
- STATE.md / ADR / PORT_LOG doctrine
- Codex review per phase

MIS-APPLIED:
- Task granularity (Phase 6 bundled compound task)
- Agent tool restrictions (Wave 2 agents had no .claude/agents/ YAML allowed_tools)
- STATE.md persistence (Phase 2 goals lived in chat headings, not STATE.md)
- Per-phase gates (auto-executed without user approval — root cause of silent scope narrowing)

ROOT CAUSE — **Plan-Fidelity Gate** pattern MISSING from LF. LF enforces execution-time quality but lacks **pre-execution fidelity audit**. v5 promised 70 deliverables; 40% over-promised; phases mechanically gate-passed narrowed scope.

NEW patterns v5 contributes back to LF (Block K + new):
- Plan-Fidelity Gate (Codex AXIS C)
- Agent-Consensus Merge Protocol
- Wave-and-Phase Micro-Checkpoints
- Multi-Agent Orchestration Toolkit
- Baseline-Feature Preservation Rule

---

## 10. NEW DIRECTIVE: drop MCP + drop streaming (2026-04-30 user)

> *"v5 must covers all!!! (context, only user coding agent, in bedrock sagemaker), no other mcp etc needed, sagemaker ui cannot stream which is fine."*

Drops applied:
- **MCP entirely** — `compact_v5/MAIN/agent/mcp/` package and references in PORT_LOG. Single-user SageMaker has no MCP server need.
- **Streaming** — Bedrock streaming responses NOT used; SageMaker UI cannot stream anyway. v5 keeps current sync invoke_model.

Removes from scope:
- All `services/mcp/`, `services/mcpServerApproval/` from Runnable adoption list (was already deferred in Phase 7+).
- All streaming code paths from Runnable (`stream`, `event-driven response`, etc.).
- Reduces Block A complexity (no streaming cache_edits API; use sync API).

Effective coverage scope: **v4 functional parity + Runnable architecture (sync, single-user, Bedrock-only) + Hermes patterns + LF process discipline.**

---

## 11. NEW DIRECTIVE: clear plan with code-chunk references BEFORE coding (2026-04-30 user)

> *"then we must have clear plan!!!!!!!!!!!!! with reference to which code chunk as reference before even start coding"*

Every Block now includes explicit code-chunk references (file:line ranges). No coding starts until this plan is user-approved.

### Block 0 — `sagemaker_agent.py` shim (mandatory)
- Reference code: `D:/Github/sagemaker-coding-agent/compact_v5/_phase_2/v4_reference/chat.ipynb` (cell 2 + cell 3 imports + widget construction)
- v4 import surface: `from sagemaker_agent import CONFIG, BEDROCK_MODELS, create_chat_ui` (cell 2 + cell 3 of chat.ipynb)
- Target file: `compact_v5/MAIN/agent/sagemaker_agent.py` (NEW)
- LOC estimate: ~50 LOC (re-exports only)

### Block A — Compactor + cold-cache + auto-compact
- Reference Runnable: `_archive/compare_code/gg-claude-code-runnable/src/services/compact/compact.ts` (1706 LOC), `microCompact.ts` (531), `autoCompact.ts` (352)
- Reference v4 (for cold-cache constants only): `compact_v4/MAIN/agent/sagemaker_agent.py:3826` (`COLD_CACHE_THRESHOLD_SECONDS=1800`), `:8923` (cold-cache trigger logic)
- Target file: `compact_v5/MAIN/agent/compact.py` (NEW, single-file consolidation)
- Wire-in: `compact_v5/MAIN/agent/core/query_engine.py:run()` per-turn checkpoint (~line 250)
- LOC estimate: ~600 LOC (port-and-condense Runnable's 2589 LOC into Python; drop streaming branches)

### Block B — TokenTracker + AuditLogger + SnapshotManager
- Reference v4 (verbatim):
  - TokenTracker: `compact_v4/MAIN/agent/sagemaker_agent.py:3565-3750` (~185 LOC)
  - AuditLogger: `compact_v4/MAIN/agent/sagemaker_agent.py:2173-2258` (~85 LOC)
  - SnapshotManager: `compact_v4/MAIN/agent/sagemaker_agent.py:4418-4510` (~92 LOC)
- Reference Runnable: `services/api/tokenEstimation.ts` (token counting helpers, drop streaming-only paths)
- Target files: `compact_v5/MAIN/agent/runtime/tokens.py` + `runtime/audit.py` + `runtime/snapshot.py` (NEW)
- Wire-in: BedrockClient.chat (`runtime/bedrock_client.py`) calls TOKENS.update; tool dispatch in `core/query_engine.py` calls AUDIT.log; edit_file/skill apply call SNAPSHOTS.snapshot.
- LOC estimate: ~400 LOC total

### Block C — Runtime safety (exec-limit + rate-limit + repetition + system-reminders)
- Reference v4:
  - exec-limit gate: `sagemaker_agent.py:9435-9483` (~50 LOC)
  - rate-limit check: `sagemaker_agent.py:8731-8740` (~10 LOC)
  - repetition detector: `sagemaker_agent.py:9156-9180` (~25 LOC)
  - misleading-error-fix: `sagemaker_agent.py:~9442` (the explicit OTHER TOOLS STILL WORK message)
  - file-state tracking _FILES_READ: `sagemaker_agent.py:_FILES_READ` global + edit_file gate
- Reference Hermes:
  - failure-message-as-instruction: `D:/Github/hermes-agent/run_agent.py:8274-8523` (parallel exec) + AGENTS.md error-as-instruction examples
  - fuzzy tool name match: `D:/Github/hermes-agent/run_agent.py:4689-4720` (~30 LOC)
- Reference Runnable: system-reminder injection patterns in `src/services/` (search for `<system-reminder>`)
- Target files:
  - Modify `compact_v5/MAIN/agent/tools/bash.py` + `tools/python_exec.py` (add exec-limit gate)
  - Modify `compact_v5/MAIN/agent/core/query_engine.py` (add rate-limit + repetition + system-reminder injection)
  - Modify `compact_v5/MAIN/agent/tools/edit_file.py` (add _FILES_READ check)
- LOC estimate: ~200 LOC additions across 4 files

### Block D — Slash commands (`/save /load /cost /status /compact /clean /skill apply`)
- Reference v4 (verbatim):
  - `/cost`: `sagemaker_agent.py:11030-11050` (~20 LOC)
  - `/status`: `sagemaker_agent.py:11062-11093` (~30 LOC)
  - `/save / /load`: `sagemaker_agent.py:on_save / on_load ~11569-11665` (~100 LOC)
  - `/skill apply`: `sagemaker_agent.py:10892-10970` (~80 LOC)
  - `/compact / /clean`: button handlers in chat UI region
- Reference Runnable: `src/commands/` for slash-command framework (skip if architecture-fit costs more than v4 verbatim)
- Target files: `compact_v5/MAIN/agent/core/query_engine.py` (add slash-dispatch table) + `compact_v5/MAIN/agent/agent.py` (Agent.run preprocessor for `/cmd` messages)
- LOC estimate: ~250 LOC

### Block E — Full chat HTML rendering (THE BIG ONE — UI parity)
- Reference v4: **`compact_v5/_phase_2/v4_reference/create_chat_ui.py` (2354 LOC standalone extract)** OR `compact_v4/MAIN/agent/sagemaker_agent.py:9735-12088` (the same content in-source)
- Specific surfaces by line range:
  - `_format_inline_md`: lines 9776-9786
  - `_render_assistant_markdown`: lines 9788-9922
  - `render_chat`: lines 9924-9970
  - `render_todos`: lines 9972-10002
  - Model dropdown + on_model_change: lines 10068-10208
  - `update_mode_display` (status bar): lines 10308-10357
  - `update_tokens_display` (token/cost display): lines 10377-10478
  - Approval/ask-user dialog: lines ~9237 + ~9446 + ~9509
  - Dark-mode toggle: line 9752 + theme variables throughout
  - Sub-agent overrides panel: ~lines 10500-10700
  - Compact + Clean buttons: ~lines 10021-10022
- Reference Runnable per-tool prompts: `_archive/compare_code/gg-claude-code-runnable/src/tools/<Name>/prompt.ts`
- Target files: 
  - `compact_v5/MAIN/agent/ui/chat_ui.py` (REPLACE current 220 LOC minimal MVP with v4-equivalent ~1500 LOC adapted)
  - `compact_v5/MAIN/agent/ui/render.py` (NEW: markdown renderer; ~400 LOC)
  - Optional split: `ui/dialogs.py`, `ui/status_bar.py` for clarity (final consolidation per user min-files directive — decide post-port)
- LOC estimate: **~2100 LOC** (the largest block)

### Block F — Cell 2 widgets + iteration-budget slider
- Reference v4: `compact_v5/_phase_2/v4_reference/chat.ipynb` cells 2 + 3 (entire content)
- Target files: 
  - `compact_v5/MAIN/agent/chat.ipynb` (REPLACE v5's minimal notebook with v4 cells; v4 verbatim)
  - `compact_v5/MAIN/agent/sagemaker_agent.py` shim adjustments to expose widget objects v4 uses
- LOC estimate: notebook ~150 LOC + shim ~30 LOC

### Block G — AGENT_TYPES + worktree + AgentSummary
- Reference v4:
  - AGENT_TYPES dict: `sagemaker_agent.py:6914-7090` (~176 LOC; 7 agent types: build/plan/explore/verify/general/review/fork)
  - Worktree spawn for `build`: `sagemaker_agent.py:8413-8470` (~57 LOC)
  - `_build_subagent_handoff_block`: `sagemaker_agent.py:7771-7841` (already partially in v5)
  - `_build_subagent_env_details`: `sagemaker_agent.py:7695-7738` (already in v5)
- Reference Runnable: `_archive/compare_code/gg-claude-code-runnable/src/services/agentSummary.ts` (~180 LOC)
- Target files:
  - `compact_v5/MAIN/agent/subagent/agent_types.py` (NEW: AGENT_TYPES dict with prompts)
  - `compact_v5/MAIN/agent/subagent/worktree.py` (NEW: worktree spawn for build)
  - `compact_v5/MAIN/agent/subagent/agent_summary.py` (NEW: 30s timer summarizer)
  - Modify `compact_v5/MAIN/agent/subagent/spawn.py` to dispatch by agent_type
- LOC estimate: ~350 LOC

### Block H — Memory extraction + session memory
- Reference v4 (verbatim): `sagemaker_agent.py:_extract_and_append_memories ~7889-7990` (~100 LOC)
- Reference Runnable:
  - `services/extractMemories.ts` (616 LOC)
  - `services/sessionMemory.ts` (496 LOC)
- Decision: port v4's simpler extractor first, evaluate Runnable's more complex variant for v5.1+
- Target file: `compact_v5/MAIN/agent/runtime/memory_extract.py` (NEW)
- LOC estimate: ~150 LOC (v4 verbatim) or ~600 LOC (Runnable port)

### Block I — Skill name resolution + fuzzy match
- Reference v4: `sagemaker_agent.py:SKILLS.read_skill ~10814-10835` (matches filename OR metadata `name:`)
- Reference Hermes: `run_agent.py:4689-4720` (fuzzy tool name match — adapt for skills)
- Target file: modify `compact_v5/MAIN/agent/skills/manager.py:activate(name)` to alias-resolve directory name AND metadata name AND fuzzy match
- LOC estimate: ~50 LOC modification

### Block J — Real-Bedrock smoke + zip verification
- Reference v4: `compact_v4/verify_ship_zip.py` for verification pattern
- Reference v5 existing: `compact_v5/verify_ship_zip.py` (extend)
- Target files:
  - `compact_v5/MAIN/agent/tests/integration/test_real_bedrock_smoke.py` (NEW; env-gated `RUN_REAL_BEDROCK=1`)
  - Modify `compact_v5/verify_ship_zip.py` to extract zip into tmp + run `python -c "import entry"` AND `python -c "import sagemaker_agent"`
- LOC estimate: ~150 LOC

### Block K — Process discipline (LF AXIS C)
- Reference: V5_SHIP_CRITIQUE.md + `_phase_2/synthesis/V5_PHASE_2_PLAN.md` (this doc)
- Target files:
  - Modify `compact_v5/_status/CODEX_REVIEW_TEMPLATE.md` (add AXIS C plan-fidelity)
  - Modify `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` (add DEFERRED-WITH-USER-APPROVAL category, backfill all v5.0.0 deferrals)
  - New file: `compact_v5/_status/PLAN_FIDELITY_GATE.md` (the new pattern proposal)
- LOC estimate: doc-only, ~200 LOC

### Block L — Runnable error/retry/cache-break extensions
- Reference Runnable:
  - `services/api/errors.ts` lines for media-validation, tool-use, subscription-aware (specific lines TBD post-detailed-grep)
  - `services/api/withRetry.ts` lines 200-400 (foreground 529 gating, persistent unattended retry, max-tokens overflow)
  - `services/api/promptCacheBreakDetection.ts` per-tool schema hashing (most relevant)
- Drop: streaming retry paths (sagemaker no-stream).
- Target files: extend `compact_v5/MAIN/agent/core/errors.py` + `core/retry.py` + `core/cache.py` (don't replace)
- LOC estimate: ~300 LOC additions

### Block M — Phase 8 critical fixes
- Fix 1 (1 line): `compact_v5/MAIN/agent/core/query_engine.py:run()` — add `self._discovered_tool_names = set()` per turn (currently only at run-start; missing per-turn reset)
- Fix 2 (~30 LOC): port `countToolCalls` from Runnable QueryEngine.ts:1004-1048 + add structured-output retry-limit check
- Reference Runnable: `_archive/compare_code/gg-claude-code-runnable/src/QueryEngine.ts:1004-1048`
- LOC estimate: ~30 LOC

### Block N (NEW) — Hermes net-new patterns
- Parallel tool execution: Hermes `run_agent.py:8274-8523` (~250 LOC) — adopt if architecture allows; high latency win.
- Dynamic tool reference injection: Hermes `AGENTS.md:627-628` + corresponding code (~100 LOC) — prevents hallucination.
- Tool call deduplication: Hermes `run_agent.py:4639-4655` (~16 LOC) — small, high-value.
- Ephemeral system prompt: Hermes `run_agent.py:850, 1486-1488` (~5 LOC).
- Target files: extend `core/query_engine.py` and `tools/registry.py`
- LOC estimate: ~400 LOC if all four; ~100 LOC if just dedup + ephemeral.

---

## 12. Block sizing summary

| Block | Title | LOC est | Source repos | Ship-blocker? |
|---|---|---:|---|---|
| 0 | sagemaker_agent.py shim | 50 | v4 | YES |
| A | Compactor + cold-cache + auto-compact | 600 | Runnable + v4 | YES |
| B | TokenTracker + Audit + Snapshot | 400 | v4 + Runnable | YES |
| C | Runtime safety gates | 200 | v4 + Hermes + Runnable | YES |
| D | Slash commands | 250 | v4 | YES |
| E | Full chat HTML rendering | 2100 | v4 | YES (BIG) |
| F | Cell 2 widgets | 180 | v4 | YES |
| G | AGENT_TYPES + worktree + summary | 350 | v4 + Runnable | YES |
| H | Memory extraction | 150-600 | v4 OR Runnable | MEDIUM |
| I | Skill name resolution | 50 | v4 + Hermes | YES |
| J | Real-Bedrock smoke + zip verify | 150 | v5-extension | YES |
| K | Process discipline (LF AXIS C) | 200 (docs) | LF + v5 | MEDIUM |
| L | Runnable error/retry/cache-break ext | 300 | Runnable | MEDIUM |
| M | Phase 8 critical fixes | 30 | Runnable | YES |
| N | Hermes net-new patterns | 100-400 | Hermes | MEDIUM |
| **TOTAL** | | **~5060-5560 LOC** | 4 repos + v5 ext | |

---

## 13. Sequencing recommendation

**Critical path (ship-blocker, 1-2 weeks)**: Block 0 → Block B → Block C → Block D → Block A → Block E → Block F → Block I → Block M → Block J.

**Important not blocker (1 week)**: Block G + Block H + Block L + Block N.

**Process gate (continuous)**: Block K runs throughout — every Block lands with AXIS C plan-fidelity Codex review against this plan.

---

## 14. Status of this synthesis

- **Wave 1 reports (9)**: complete and on-disk.
- **Wave 2 reports (11)**: complete and on-disk (10 written by agents + 1 saved manually after hook block).
- **Hermes findings + LF findings**: integrated above (sections 9 + Block N + Block K).
- **MCP and streaming drops**: applied (section 10).
- **Code-chunk references**: present for every Block (section 11).
- **Codex (gpt-5.5) review**: PENDING — will run against this synthesis + Wave 2 reports + AXIS C plan-fidelity.
- **User approval**: REQUIRED before any coding begins (per user directive: "clear plan!!!!!!!!!!!!! ... before even start coding").
