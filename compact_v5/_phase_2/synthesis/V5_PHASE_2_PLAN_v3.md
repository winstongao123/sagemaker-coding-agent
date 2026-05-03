# V5 Phase 2 Plan — v5 (post-Wave-5-DEEP synthesis 2026-05-01)

> **STATUS UPDATE 2026-05-01 (Wave 5-DEEP applied)**: After Codex APPROVE on plan v4, user requested true exhaustive line-by-line scan. 20 parallel agents read every file in v4 + Runnable + Hermes + LF. Result: ~150 net-new findings. SYNTHESIS_MASTER.md is the canonical post-DEEP reference.
>
> **Read order for builder**:
> 1. `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` (POST-DEEP CANONICAL — every NEW finding with file:line + LOC + Block + architectural-fit verdict)
> 2. `compact_v5/_phase_2/wave_5_deep/CONFIDENCE_REPORT.md` (9-axis verdict v5 > Runnable > v4)
> 3. `compact_v5/_phase_2/wave_6/PS_Plan_Edge_Cases_Thinking.md` (111 unique user scenarios; 74 HANDLED / 42 NEEDS-LOCK-TEST / 9 POSSIBLE-GAP all closing in existing Blocks)
> 4. This file (Block-level scoping + Q1/Q2/Q3/Q4 evidence)
> 5. `compact_v5/_phase_2/wave_4/Q1_EVIDENCE_MATRIX.md` (PORT_LOG rows, growing 215 → ~448 with evidence_tier column)
>
> **Wave 6 small deltas (2026-05-01)** — 111 user scenarios verified, 9 POSSIBLE-GAPs closed within existing Blocks: Block C+ +30 LOC ipywidgets fallback (60s watchdog + ask_user text mode); Block G +5 LOC `MAX_SUBAGENT_DEPTH=2`; Block E+F +10 LOC long-text `<details>` collapse; **Block H+ Auto-Dream is MANUAL-TRIGGER ONLY (user decision 2026-05-01)** — no daemon, no auto-fire; only runs when user invokes `/dream` slash command (Block D). USER_GUIDE must document `/dream` usage clearly: "Run `/dream` when memory.md or AGENT_STATUS.md feel cluttered after long sessions; it forks a sub-agent that consolidates+prunes+indexes your memory files. Costs ~$0.01-0.05 in API calls. Safe to run anytime, idempotent." Plus doc rows for mock_mode disclaimer + ipywidgets pin + PermissionDialog Q1 row + Block I tool-vs-skill precedence + create_html design note. Plan total: 21 Blocks, ~19,345 LOC (+0.23%); lock tests 95 → 135.
>
> **Per-Block close ritual (NOT separate Blocks; codified by Block K)** — at every Block close: (1) Update `V5_BUILD_STATUS.md` (Last commit sha + state + next pickup); (2) Append PORT_LOG rows for that Block; (3) Append ADR(s) to `V5_DESIGN_DECISIONS.md`; (4) Save Codex AXIS A/B/C review to `_status/codex_reviews/block-<X>.md`; (5) `git add` SPECIFIC files (never `-A`); (6) Run pytest T1+T2 + verify_ship_zip.py; (7) **Rebuild `compact_v5.zip`** via `_rebuild_zip.py`; (8) Tag `v5.0.1-block-<X>` ONLY after Codex APPROVE + user approval; (9) **Push to `sageagent` remote**; (10) Update HTML companion docs if architecture changed; (11) Sync `chat.md` if Block E+F/F; (12) Sync ship zip to OneDrive. See `wave_6/TEST_DESIGN.md` for full ritual + test catalogue.
>
> **Real-AWS testing (revised 2026-05-01 per user directive "carefully designed for v5, optimized for value not minimum spend")** — 12 R-tier end-to-end USER-SIMULATING scenarios run after Block K, before tag. Each scenario has hard cost cap $0.20-$1.50. Total R-tier real-AWS cost: ~$3-7. Plus per-Block T5 single round-trips on 6 high-risk Blocks (~$0.10). Grand total real-AWS through ship: ~$4-10. Catalogue in `wave_6/TEST_DESIGN.md` §R-tier.
>
> **Post-Wave-5-DEEP scope** (corrected per Codex AXIS A 2026-05-01):
> - **21 Blocks** counting E+F as one combined block (added: **G3** Coordinator System Prompt ~300 LOC, **F2** Auto-Continuation under iteration budget ~100 LOC, **H+** Auto-Dream daemon ~350 LOC). Plus notebook-smoke-gate checkpoint after Block 0.
> - **~19,300 LOC** total (corrected from synthesis-agent estimate of ~16,200 — actual sum of per-Block NEW deltas in SYNTHESIS_MASTER §3 is ~7,943 LOC NEW + 11,330 LOC pre-DEEP = ~19,273 LOC).
> - **+233 PORT_LOG rows** in Q1 matrix (215 → 448).
> - **8 NOT-OPTIONAL correctness fixes** (per SYNTHESIS_MASTER §1): R4 #2 parseMaxTokensContextOverflowError + R4 #9 extractNestedErrorMessage + R4 #14 isExcludedModel Haiku cache-break + R4 #41 countTokensWithBedrock + R4 #56 adjustIndexToPreserveAPIInvariants + H2 stub-injection for missing tool_results + H5 A28 cache-invariant policy + R7 N8 token-accounting input-cumulative-vs-output-per-turn.
> - **3 critical Hermes policies adopted**: A28 prompt-cache invariant (Block 0 + A), A36 dynamic cross-tool ref (Block N already), A44 no-change-detector tests (Block K).
> - **Drops**: ~80 patterns/tools categorically out-of-scope (no v5.0.2 punt; every drop has constraint citation).
>
> **Updated build sequence**:
> `Block 0 → notebook smoke gate → B → B+ → C → C+ → D → A → E+F → F2 → I → M → G → G3 → G2 → H → H+ → L → N → T → J → K`
>
> Per-Block deltas inline below remain valid as SCOPING reference; SYNTHESIS_MASTER.md is the GRAFT reference (source file:line + LOC + architectural-fit verdict per finding).

**v5 = v4 + Runnable + Hermes + LF COMBINED** (per memory rule `feedback_v5_combine_to_be_better.md`). Every Block ports the combined version, not "one verbatim".

---

# V5 Phase 2 Plan — v3 historical content (corrected to v4)

**Date**: 2026-04-30
**Status**: v2 was REJECTed (4 of 6 blockers still open: line-ref accuracy, Block L specificity, Q1/Q2/Q3/Q4 per-block, Block N Hermes claims).
**v3 fixes**: all line refs re-grepped against source; Block L now has concrete line ranges; Q1/Q2/Q3/Q4 evidence subsection in every Block; Block N Hermes claims pruned to verified ones only.
**Codex review path**: v1 REJECT → v2 REJECT → v3 (this).
**Wave 1 + Wave 2**: 9 + 11 = 20 reports on disk.

> **Reading order for the user**: this document supersedes v1 and v2. v1 + v2 are kept in `_phase_2/synthesis/` for traceability. This v3 is the approval-grade plan.

---

## 1. v4 baseline COMPLETE (re-grepped 2026-04-30)

| v4 feature | v4 file:line (ACCURATE) | Block | Severity |
|---|---|---|---|
| `Compactor` class | `sagemaker_agent.py:186-555` | A | HIGH |
| `Compactor.prune_tool_outputs` | `:215-...` | A | HIGH |
| `Compactor.create_llm_summary` (13-section template) | `:489-...` | A | MED |
| `microcompact()` function | `:3851-3977` | A | HIGH |
| `context_collapse()` function | `:3978-...` | A | HIGH |
| `MICROCOMPACT_TRIGGER_PERCENT = 0.70` | `:3822` | A | HIGH |
| `COLD_CACHE_THRESHOLD_SECONDS = 30*60` | `:3826` | A | MED |
| Cold-cache trigger logic | `:8923` | A | MED |
| `class AuditLogger` | `:2173-2252` | B | HIGH |
| `AUDIT = AuditLogger(CONFIG.audit_dir)` | `:2253` | B | HIGH |
| `class SessionManager` | `:2578-...` | B+ | HIGH |
| `class TokenTracker` | `:3565-3753` | B | HIGH |
| `TOKENS = TokenTracker()` | `:3755` | B | HIGH |
| `_FILES_READ` set + `_FILES_READ_LOCK` | `:3764-3765` | C+ | HIGH |
| `class SnapshotManager` | `:4418-4509` | B | MED |
| `SNAPSHOTS = SnapshotManager(CONFIG.workspace)` | `:4510` | B | MED |
| `_GLOBAL_EXEC_LOCK = threading.Lock()` | `:8229` | C | MED |
| `class Agent` | `:8278-...` | C+ | HIGH |
| `_FILES_READ.clear()` post-compact restoration | `:8850 + :9039` | A | HIGH |
| Approval gate check `CONFIG.require_tool_approval` | `:9444` | C+ | HIGH |
| Exec-call gate `_GLOBAL_EXEC_CALLS >= max_exec_calls_per_session` | `:9477-9478` | C | HIGH |
| Misleading-error-fix message ("Blocked: bash + python_exec...") | `:9482-9489` | C | HIGH |
| Repetition detector (read_file dedup `f"{fp}@{offset}:{limit}"`) | `:9156-9180` | C | MED |
| Rate-limit checks (max_user_messages_per_minute / per_session) | `:8731-8740` | C+ | HIGH |
| `Config.require_tool_approval` | `:1071` | C+ | HIGH |
| `Config.max_exec_calls_per_session = 200` | `:1080` | C | HIGH |
| `Config.session_cost_limit` | `:1082` | B+ | HIGH |
| `Config.session_cost_limit` enforcement (warns 80% / blocks 100%) | `:3638-3652` (in TokenTracker) | B+ | HIGH |
| Cost runtime warning at run-loop | `:8787` | B+ | HIGH |
| AGENT_TYPES dict (7 types) | `:6914-7090` | G | HIGH |
| Worktree spawn for `build` | `:8413-...` | G | MED |
| `_build_subagent_handoff_block` | `:7771-7841` | G | (in v5) |
| `_build_subagent_env_details` | `:7695-7738` | G | (in v5) |
| `_extract_and_append_memories` | `:7889-8028` (140 LOC; ends at SYSTEM_PROMPT def at 8029) | H | MED |
| `pending_approval` dict + on_approve/on_deny handlers | `:10306, :10491-10605` | C+ | HIGH |
| Approval gate UI integration in dispatch | `:9231 + 9444 + 9448` | C+ | HIGH |
| `/cost` slash command handler | `~:11030-11050` | D | HIGH |
| `/status` slash command handler | `~:11062-11093` | D | MED |
| Session save/load callbacks (`on_save`/`on_load`, incl. session_cost) | `~:11569-11665` | E+F (session UI) + B+ (SessionManager) | HIGH |
| `/skill apply` UX | `~:10892-10970` | D | MED |
| Compact button | `~:10021` | E+F (button) → A (trigger) | HIGH |
| Clean button | `~:10022` | E+F (button) | MED |
| Full v4 baseline command surface: 19 advertised at `:8164` (`/skills`, `/skill use/clear`, `/unskill`, `/skill suggestions/reject`, `/skill apply`, `/revert`, `/cost`, `/context`, `/status`, `/verify`, `/checkpoint`, `/phase`, `/diffs`, `/regression`, `/done`, `/simplify` via expander, `/commands`) + 1 separate `/auth` auth-gate at `:10789` = 20 command-like inputs | `:8164 + :10789-:11341` | D | HIGH |
| `_format_inline_md` | `:9776-9786` | E | HIGH |
| `_render_assistant_markdown` | `:9788-9922` | E | HIGH |
| `render_chat()` | `:9924-9970` | E | HIGH |
| `render_todos()` | `:9972-10002` | E | HIGH |
| Model dropdown + `on_model_change` | `:10068-10208` | E | MED |
| `update_mode_display()` (status bar) | `:10308-10357` | E | HIGH |
| `update_tokens_display()` | `:10377-10478` | E | HIGH |
| Cost-limit slider (cell 2 in v4 chat.ipynb) | chat.ipynb cell 2 + agent code at `:10086-10102` | F | HIGH |
| Approval dialog UI | `:10491-10605` | E | HIGH |
| Dark-mode toggle | `:9752` + theme dict | E | MED |
| Sub-agent overrides panel | `:~10500-10700` | E | MED |
| `BedrockClient.chat` cold-cache trigger check | `:8923` | A | MED |
| Cell 2 widgets (whole notebook) | chat.ipynb cells 1-3 + supporting code in agent | F | HIGH |
| AGENT_STATUS.md auto-load | `:_load_persistent_memory + _load_project_status ~:8700-8722` | B+ | MED |

This list is the **non-negotiable v4 baseline**. Every row gets a PORT_LOG row in the v5.0.1 patch. No silent drops.

---

## 2. The 15 hard constraints (recap, full set 2026-05-01)

1. **v4.10.10 baseline** (functional capability is the floor).
2. **v4 chat.ipynb canonical UI** (must run UNCHANGED via `sagemaker_agent` shim).
3. **Cover ALL 4 repos** (v4 + Runnable + Hermes + LF).
4. **Line-by-line investigation, no skipping** ✓ Wave 2 done.
5. **Minimum file structures** (consolidate post-port).
6. **Architecture-first thinking** before adopting any pattern.
7. **PS_problems STRUCTURALLY fixed** (not patched).
8. **v5 ≥ Runnable AND v5 > v4 decisively** axis-by-axis with file:line evidence (Q3 matrix). The settled Q3 claim is v5 ≥ Runnable on every axis (post-no-deferrals; v5 > Runnable on the SageMaker-specific axes) AND v5 > v4 decisively (15+ axes).
9. **Drop MCP** entirely (single-user SageMaker).
10. **Drop streaming** (SageMaker UI cannot stream).
11. **Clear plan with code-chunk refs** BEFORE coding (v3 + Q1 matrix).
12. **NO DEFERRALS** (no v5.0.2 punt; everything in v5.0.1).
13. **Bedrock caching parity for sub-agents** (cache_control on parent + sub-agent prefix replay via Block G2).
14. **Token + cost metrics covering parent + sub-agent** (Block B + B+ TokenTracker shared singleton).
15. **COMBINE not pick-one + do BETTER** (memory rule `feedback_v5_combine_to_be_better.md` 2026-05-01).

Plus standing rules: quality not rush, status/changelogs/PORT_LOG updated each Block.

---

## 3. Block-by-block plan with Q1/Q2/Q3/Q4 evidence

> **Every Block has Q1/Q2/Q3/Q4 evidence subsection** so the user can map each block back to their 4 verification questions.

### Block 0 — `sagemaker_agent.py` shim
- Reference: `compact_v5/_phase_2/v4_reference/chat.ipynb` cells 2 + 3 imports.
- Target: `compact_v5/MAIN/agent/sagemaker_agent.py` (NEW, ~50 LOC re-exports of `CONFIG`, `BEDROCK_MODELS`, `create_chat_ui`, plus any other names v4 cells reference).
- LOC est: 50.
- **Q1**: PORT_LOG row "shim for v4 chat.ipynb canonical UI" added.
- **Q2**: bridges all PS issues (none alone solved here; all enabled).
- **Q3**: matches v4 import surface; better than v5.0.0 (which had no shim).
- **Q4**: lock test `test_v4_notebook_smoke.py` runs `from sagemaker_agent import ...` and asserts each name exists.

### Notebook smoke gate (between 0 and B)
- Lock test: imports succeed; no actual UI render needed at this gate.
- If gate fails, all later blocks blocked.

### Block B — TokenTracker + AuditLogger + SnapshotManager (port v4 verbatim) + tokenEstimation
- TokenTracker: `compact_v4/MAIN/agent/sagemaker_agent.py:3565-3753` (188 LOC) + singleton `:3755`. Verbatim into `runtime/tokens.py`. Extended with **per-agent attribution dict** (`parent_*`, `subagent_*[type]`) — same singleton, parent + sub-agent both update it via BedrockClient.chat hook (object-identity preserved).
- Runnable tokenEstimation: `_archive/compare_code/gg-claude-code-runnable/src/services/tokenEstimation.ts`. Folded into `runtime/tokens.py` as `estimate_tokens()` helper used by Block A's cache-sharing math (microcompact + autoCompact circuit-breaker thresholds).
- AuditLogger: `:2173-2252` (~80 LOC) + singleton `:2253`. Verbatim into `runtime/audit.py`.
- SnapshotManager: `:4418-4509` (~92 LOC) + singleton `:4510`. Verbatim into `runtime/snapshot.py`.
- Wiring: `runtime/bedrock_client.py:chat()` calls `TOKENS.update`; `core/query_engine.py:run()` tool dispatch wraps `AUDIT.log`; `tools/edit_file.py` + `tools/write_file.py` + `skills/manager.py:apply_proposal` call `SNAPSHOTS.snapshot`.
- LOC est: 360 verbatim + 30 wiring + 50 tokenEstimation port = 440.
- **Q1**: 3 PORT_LOG rows; v4 line refs cited in each.
- **Q2**: PS#5/#6 (session cost wiring + persistence) STRUCTURALLY resolved.
- **Q3**: matches v4. v5 > v4 only on testability axis (modular not monolithic).
- **Q4**: lock test for TOKENS.update() + AUDIT.log() file format + SNAPSHOTS.snapshot+restore.

### Block B+ — SessionManager + cost-limit + AGENT_STATUS auto-load + FileCache thread-local

**Default-values update (user 2026-05-03)**:
- `CONFIG.session_cost_limit = 20.0` (v5 default; visible budget for awareness, NOT a hard cap; v4 default was 0.0 = no limit)
- `CONFIG.model_id = "au.anthropic.claude-sonnet-4-6-..."` (default Sonnet 4.6; carry v4.10.1+ preference forward)
- **Behavior matches v4**: warn at 80%, warn at 100% but agent CONTINUES. User decides whether to manually click Stop, raise budget, or let it run. NO hard halt at application level — that's deliberate, matches v4 UX, lets user overspend on critical tasks if they choose. The TRUE hard halt is at cloud level (AWS Budget Action $50/month + GCP Cloud Function $200/month) — those auto-stop without user intervention.
- SessionManager: `:2578-...` (atomic save/load). Verbatim into `runtime/session.py` (extends Phase-1 stub).
- session_cost_limit enforcement: TokenTracker has `:3638-3652` block (warns 80% / blocks 100%). Already wires from B.
- Cost runtime warning at run-loop: `:8787` printed as `[Cost ${TOKENS.session_cost} passed budget ${CONFIG.session_cost_limit} — continuing.]`. Wire in `core/query_engine.py:run()`.
- AGENT_STATUS auto-load: search v4 for `_load_persistent_memory`, `_load_project_status` (around `:8700-8722`). Port wiring into `agent/__init__.py:Agent.run()` first call.
- **FileCache thread-local context + save/restore** (reconciled 2026-05-01): port v4's `class FileCache` at `compact_v4/MAIN/agent/sagemaker_agent.py:893-1017` (125 LOC). Verified APIs: `save_and_clear_context()` (`:975-980`), `restore_context()` (`:982-985`), `enter_thread_local_context()` (`:987-990`), `exit_thread_local_context()` (`:992-...`). Parent + sub-agent FileCache state is saved + cleared at sub-agent dispatch entry; thread-local context isolates concurrent sub-agents; restore on dispatch exit. Target `runtime/file_cache.py` (separate from `runtime/files_read.py` which holds the simpler `_FILES_READ` set from Block C).
- **Acceptance test (sub-agent token + cost attribution)**: spawn parent agent → call sub-agent with type="build" → assert `TOKENS.parent_input_tokens > 0`, `TOKENS.subagent_input_tokens["build"] > 0`, `TOKENS.parent_output_tokens > 0`, `TOKENS.subagent_output_tokens["build"] > 0`, `TOKENS.session_cost == sum_of(per_agent_cost) ± $0.0001`. Lock test in `tests/integration/test_subagent_token_attribution.py`.
- LOC est: 325 (SessionManager ~150 + AGENT_STATUS wiring ~50 + FileCache class verbatim 125).
- **Q1**: 4 PORT_LOG rows (SessionManager + cost-limit + AGENT_STATUS + FileCache thread-local class).
- **Q2**: PS#5 (cost-across-sessions) RESOLVED + AGENT_STATUS continuity preserved.
- **Q3**: v4 parity.
- **Q4**: lock tests save→load→cost preserved + AGENT_STATUS injected into system prompt.

### Block C — Runtime safety gates (exec-limit + repetition)
- _FILES_READ set + lock: `:3764-3765`. Verbatim into shared `runtime/files_read.py`.
- _GLOBAL_EXEC_LOCK: `:8229`. Same module.
- Exec-limit gate: `:9477-9478` (the IF check). Misleading-error-fix message: `:9482-9489` (the message body verbatim — "Blocked: bash + python_exec call limit reached..."). Wire into `tools/bash.py` + `tools/python_exec.py` dispatch.
- Repetition detector: `:9156-9180` (read_file dedup key + threshold-2). Wire into `core/query_engine.py` tool dispatch.
- LOC est: 250.
- **Q1**: 4 PORT_LOG rows.
- **Q2**: PS#7 (40-call exec limit + misleading error) STRUCTURALLY fixed.
- **Q3**: v4 parity + adds Hermes failure-message-as-instruction (Block N integration).
- **Q4**: lock test 200 bash → 201st returns explicit message with "OTHER TOOLS STILL WORK" listing.

### Block C+ — Approval/diff dispatch wiring + stop/abort handler + rate limits
- Approval gate: `Config.require_tool_approval :1071`. Gate check in dispatch at `:9444`. Approval UI integration at `:9231` (pre-bash) and `:9448` (pre-tool-execute). pending_approval dict + on_approve/on_deny: `:10306, :10491-10605` (~100 LOC).
- Wire-in: `core/query_engine.py` checks `tool.requires_approval AND CONFIG.require_tool_approval`; if both, render diff_widget + block on user button.
- Stop/abort: `agent/__init__.py:Agent.stop()` already exists; ensure `core/query_engine.py:run()` per-turn checkpoint reads `_combined_stop()` (already wired in Phase 8).
- Rate-limit: `:8731-8740`. Port verbatim into `core/query_engine.py:run()` entry.
- LOC est: 200.
- **Q1**: 3 PORT_LOG rows (approval + stop + rate-limit).
- **Q2**: addresses approval-flow gap (was unwired in v5.0.0).
- **Q3**: v4 parity. Runnable's PermissionDialog richer features (per-tool always-allow + reason-prompt) folded into Block L PORT_LOG (no deferral; ported alongside Runnable error/retry/cache-break extensions).
- **Q4**: lock test write_file with diff approval Approve/Deny/Always; lock test 100 messages/min triggers rate limit.

### Block D — Slash commands (full v4 baseline parity: 19 advertised + 1 auth-gate)
v4 advertises 19 slash commands at `compact_v4/MAIN/agent/sagemaker_agent.py:8164` and dispatches them via `msg.startswith()` / `msg ==` in the chat-input handler, PLUS one separate auth-gate handler `/auth <token>` (not in the advertised list, gated by `CONFIG.require_auth`). **Constraint #1 (v4.10.10 baseline) requires ALL of them.** Verified via grep + Read:

- `/auth <token>` — `:10789-:10802` — notebook auth-token gate (compares `msg[len("/auth "):]` against `os.getenv(CONFIG.auth_token_env)`). Tracked SEPARATELY from the 19 advertised commands because it runs BEFORE custom-command dispatch (see explicit `not msg.startswith("/auth")` check at `:11314`) and is conditional on `CONFIG.require_auth`.
- `/skills` — `:10805-10813` (list available skills)
- `/skill use <name>` — `:10814-10835` (activate skill; lifts `/unskill` block)
- `/skill clear` — `:10836-10850` (deactivate all skills sticky for session)
- `/unskill <name>` — `:10851-10873` (V4.9.1 — deactivate one skill, sticky)
- `/skill suggestions` (also `/skill suggestion`) — `:10874-10891` (V4.9.5 — list pending agent-proposed patches)
- `/skill apply <name> [--yes|--edit]` — `:10892-10954` (V4.9.5 — preview diff then apply)
- `/skill reject <name>` — `:10955-10964` (V4.9.5 — discard pending patches)
- `/revert <file>` (and `/revert all --yes`) — `:10965-11029` (diff preview + apply)
- `/cost` — `:11030-11051` (session cost summary)
- `/context` — `:11052-11061` (token/context bloat diagnostic)
- `/status` (and `/status init|path`) — `:11062-11094` (status bar dump)
- `/verify [full|quick|pre-commit]` — `:11095-11113` (run verify-skill gate)
- `/checkpoint [create <name>|list|restore <name>]` — `:11114-11182` (snapshot management)
- `/phase <text>` — `:11183-11199` (set work phase in status bar)
- `/diffs [summary|last|<file>]` — `:11200-11242` (session edit history)
- `/regression` — `:11243-11275` (git diff HEAD stat + session edits + suggested test cmd)
- `/done [full|quick]` — `:11276-11313` (simplify+verify gate → READY-TO-SHIP verdict)
- `/simplify` — advertised at `:8164` but has NO dedicated `msg.startswith("/simplify")` handler in v4 because it falls through to the custom-command expander at `:11330`. v4's `/simplify` resolves via `COMMANDS.expand` to the `skills/simplify/SKILL.md` shortcut (the same skill `/done` invokes in its Phase-1 simplify step at `:11300`). v5 ports this via the same dispatcher fall-through (CommandRegistry custom-command expansion) — no dedicated handler needed; just ensure `skills/simplify/` is registered (Block I).
- `/commands` — `:11319-:11329` (list custom commands from agent_config.json) + custom-command expander fallback at `:11330-:11341` (handles `/simplify` and any `agent_config.json`-defined name).

UI buttons (NOT slash-typed but session UI surfaces — port to Block E+F not Block D):
- Compact button → triggers `Compactor.compact()` (Block A trigger).
- Clean button → cleanup audit_logs/ + sessions/ + .snapshots/.
- Save/Load callbacks → SessionManager (Block B+).

Block D scope: dispatcher + 19 handlers, ported verbatim with line ranges above. Custom-command expansion (`COMMANDS.expand`) at `:11330-11341` ports `CommandRegistry` from `:3078-3115` (handles `agent_config.json` custom commands).

- LOC est: ~700 (v4 verbatim port: dispatcher ~50 + 18 dedicated handlers averaging ~30 LOC each + custom-command expander ~30 + CommandRegistry ~80 + `/auth` auth-gate ~15; `/simplify` reuses the expander, no extra LOC).
- **Q1**: 18 dedicated-handler PORT_LOG rows + 1 expander/`/simplify` row + 1 `/auth` auth-gate row + 1 dispatcher row + 1 CommandRegistry row = 22 rows. All from `compact_v4/MAIN/agent/sagemaker_agent.py` with the verified line ranges above. **Count framing**: 19 advertised commands at `:8164` (18 with dedicated handlers + `/simplify` via expander) PLUS 1 separate `/auth` auth-gate at `:10789` = 20 distinct command-like inputs total.
- **Q2**: addresses Codex AXIS C "v4 baseline undercount" finding 2026-05-01; closes the silent-drop pattern that caused v5.0.0 failure.
- **Q3**: v5 = v4 (constraint #1 floor). Runnable's `commands/` directory has 112 entries (93 subdirectories + 19 root command files); the 6 that overlap v4's set by name (`cost`, `status`, `compact`, `skills`, `help`, `context`) are not separately ported — v4's verbatim implementation IS the v5 implementation per constraint #1. The other 106 Runnable command entries are out-of-scope-by-constraint per the explicit "Items genuinely N/A for single-user SageMaker (DROPS confirmed)" categorical list in the canonical plan at `C:/Users/winst/.claude/plans/vectorized-wandering-swan.md` (§ "Items genuinely N/A..."): `services/oauth/`, `services/teamMemorySync/`, `services/policyLimits/`, `services/remoteManagedSettings/`, `voice/`, `voiceKeyterms.ts`, `voiceStreamSTT.ts`, `keybindings/`, `vim/`, `ssh/` — and by extension all `commands/<x>` that depend on these subsystems (`commands/voice`, `commands/vim`, `commands/oauth`, `commands/ide`, `commands/chrome`, `commands/desktop`, `commands/mcp`, `commands/bridge`, `commands/commit-push-pr`, `commands/branch`, `commands/init`, `commands/hooks`, etc.). Slash-command **dispatcher pattern** from Runnable IS adopted as v5's registry shape.
- **Q4**: lock test all 20 command-like inputs end-to-end (19 advertised + `/auth`): typed message → handler called → expected side-effect observed. Includes `/done` full pipeline (simplify → verify → READY-TO-SHIP) + `/regression` + `/checkpoint create/list/restore` + `/auth` rejection on wrong token + `/auth` success on correct token.

### Block A — Compactor + cold-cache + auto-compact (COMBINED v4 + Runnable, post-no-deferrals)
- Compactor: `:186-555` (370 LOC) + microcompact `:3851-3977` (127 LOC) + context_collapse `:3978-...` (~150 LOC) + constants `:3822, :3826` + cold-cache trigger `:8923` + auto-compact circuit breaker (`_auto_compact_paused` global).
- Post-compact restoration: `_FILES_READ.clear()` at `:8850, :9039`; TODO restoration via `build_todo_restoration_message`.
- Wire-in: `core/query_engine.py:run()` per-turn checkpoint mirroring v4's `Agent.run` line ~8797.
- Target: `runtime/compact.py` (NEW; consolidates Compactor + helpers).
- LOC est: ~3300 (COMBINED v4 Compactor ~700 + Runnable services/compact/* ~2589, deduplicated).
- COMBINED with Runnable's compact.ts (cache_edits API, prompt cache sharing across compact, post-compact attachments). Runnable refs: `services/compact/compact.ts:1-1706` + `microCompact.ts:1-531` + `autoCompact.ts:1-352`. Combined LOC: ~3300 (v4 + Runnable, deduplicated).
- **Q1**: 5 PORT_LOG rows (4 v4 + 1 Runnable combined). NO DEFERRED rows post user no-deferrals directive 2026-04-30.
- **Q2**: PS#3 (cold-cache regression) RESOLVED.
- **Q3**: v5 ≥ Runnable on Block A post-combination. v5 has cache-aware compaction (Runnable cache_edits API) + autoCompact circuit-breaker + v4's smaller class shape + LF STATE.md anchoring. v5 > v4 (v4 had no cache_edits; v4 had no Runnable circuit-breaker thresholds).
- **Q4**: lock test 30-min idle → resume → microcompact fires + freed ≥5K tokens; 70% context → reactive compact triggers.

### Block E + F (TOGETHER per Codex sequencing)
**Block E** — Full HTML chat rendering:
- _format_inline_md: `:9776-9786` (10 LOC)
- _render_assistant_markdown: `:9788-9922` (135 LOC)
- render_chat: `:9924-9970` (46 LOC)
- render_todos: `:9972-10002` (30 LOC)
- Model dropdown + on_model_change: `:10068-10208` (140 LOC)
- update_mode_display: `:10308-10357` (50 LOC)
- update_tokens_display: `:10377-10478` (100 LOC)
- Approval dialog UI: `:10491-10605` (~115 LOC)
- Dark-mode toggle theme dict
- Sub-agent overrides panel: `~:10500-10700` (~200 LOC)

Target files: `ui/chat_ui.py` (REPLACE current 220 LOC MVP) + new `ui/render.py` (markdown→HTML pipeline).

**Block F** — Cell 2 widgets + cell 3 launch + complete session UI:
- v4 chat.ipynb cells 1-3 verbatim copy.
- Cost-limit slider integration: `:10086-10102` (~16 LOC).
- **Complete session UI** (reconciled 2026-05-01 from COMPLETENESS_VERIFY): session dropdown + load button + save button + on_save/on_load callbacks + auto-save on send. Port from v4 `:11569-11665` (save/load handlers) + `:10491-10605` (UI dispatch). Target `ui/chat_ui.py` extension.
- **`IterationBudgetWidget`** (already exists in `compact_v5/MAIN/agent/ui/widgets.py` from Phase 11; PS Issue #2 visible-budget UI fix): port the wiring into Cell 2 launch panel + status bar. Source: v4's iteration-budget slider at `:10086-10102` plus v5's existing widget class. Confirms PS#2 RESOLVED.
- **`ThinkingBudgetWidget`** (already exists in `compact_v5/MAIN/agent/ui/widgets.py` from Phase 11; PS Issue #4 visible-thinking-budget UI fix): port the wiring into Cell 2. Source: v4's thinking budget config + v5's existing widget. Confirms PS#4 RESOLVED.
- LOC est: ~2300 (E+F together, including session UI + budget-widget wiring).

- **Q1**: ~9 PORT_LOG rows; every UI surface from v4 mapped.
- **Q2**: addresses approval-flow gap, cost-visibility gap (PS#5).
- **Q3**: v4 parity in UI; Runnable React/Ink not adopted (constraint=`.ipynb`).
- **Q4**: lock test send message → assistant text rendered with markdown → tool_use → diff dialog → Approve → token display updates → /cost shows running total.

### Block I — Skill name resolution
- v4 logic: `:10814-10835` (file OR metadata `name:`). Hermes fuzzy match: `D:/Github/hermes-agent/run_agent.py:4689-4720` (~30 LOC, Levenshtein-style).
- Modify `compact_v5/MAIN/agent/skills/manager.py:activate(name)` to alias-resolve directory + metadata name + fuzzy match.
- LOC est: 50.
- **Q1**: 1 PORT_LOG row covering v4 + Hermes adoption.
- **Q2**: addresses the v5-introduced regression where `/skill activate clara` failed (the `clara`→`clara-review` mismatch). Without Block I, this v5 NEW bug ships.
- **Q3**: v5 > v4 (adds fuzzy). v5 > Runnable on this axis (Runnable's SkillTool doesn't have fuzzy).
- **Q4**: lock test `/skill activate clara` (and 9 other directory names) all succeed; lock test typo `/skill activate verfy` resolves to `verify`.

### Block M — Phase 8 critical fixes (Wave 2 finding)
- Fix 1: `core/query_engine.py:run()` resets `self._discovered_tool_names = set()` per-turn (currently only at run-start).
- Fix 2: port `countToolCalls` from Runnable `QueryEngine.ts:1004-1048` + structured-output retry-limit check.
- LOC est: 30.
- **Q1**: 2 PORT_LOG rows — Phase 7 wiring contract enforcement + Runnable QueryEngine.ts:1004-1048 import.
- **Q2**: prevents an infinite-loop semantic bug (PS#-style failure had this not been caught in Wave 2).
- **Q3**: v5 > v5.0.0 baseline (Wave 2 found these gaps); matches Runnable's structured-output safety.
- **Q4**: lock test infinite-loop scenario blocks at retry limit + per-turn discovery reset.

### Block G — AGENT_TYPES + worktree
- AGENT_TYPES dict: `:6914-7090` (~176 LOC; 7 types).
- Worktree spawn for build: `:8413-...` (~57 LOC).
- Modify `subagent/spawn.py` to dispatch by subagent_type from full set.
- New file: `subagent/agent_types.py` (prompts + tools + max_turns + critical_reminder).
- LOC est: 280.
- **Q1**: 7 PORT_LOG rows for 7 types + 1 row for worktree.
- **Q2**: addresses task-tool capability gap — Phase 9 only had `general`; users couldn't invoke `verify` / `simplify` etc as v4 documented. The cited PS#7 `/done quick` flow (verify + simplify) requires this.
- **Q3**: v4 parity. v5 > v4 only on testability (modular). G2 adds the v5>Runnable axis.
- **Q4**: lock test for each agent type + worktree creation/cleanup for build.

### Block G2 — forkSubagent cache-prefix replay
- Reference: `_archive/compare_code/gg-claude-code-runnable/src/tools/AgentTool/forkSubagent.ts:73-end`.
- Cache-prefix-identical message replay: when v5 forks a sub-agent, the API request prefix is byte-identical for cache sharing. Currently v5 uses fresh message buffer.
- Extend `subagent/spawn.py` with optional `cache_prefix_share=True` mode.
- LOC est: 100.
- **Q1**: 1 PORT_LOG row (Runnable forkSubagent.ts:73-end).
- **Q2**: cost-side improvement (better cache hit rate on sub-agent dispatch); no PS Issue specifically but reduces $/turn.
- **Q3**: v5 > Runnable (Bedrock cache awareness preserved with the same cache-prefix discipline Runnable uses for Anthropic API).
- **Q4**: lock test parent + child API request bytes share identical prefix when cache_prefix_share=True.

### Block H — Memory extraction (COMBINED v4 + Runnable, post-no-deferrals)
- v4: `_extract_and_append_memories` `:7889-8028` (140 LOC). Verbatim port.
- Target: `runtime/memory_extract.py` (NEW).
- LOC est: 140.
- COMBINED with Runnable's `services/extractMemories/extractMemories.ts` (1-616 LOC) + `services/SessionMemory/sessionMemory.ts` (1-496 LOC) + `services/SessionMemory/sessionMemoryUtils.ts`. Combined LOC: ~1252 (v4 + both Runnable services + utils).
- **Q1**: 3 PORT_LOG rows (1 v4 + 2 Runnable). NO DEFERRED rows post user no-deferrals directive.
- **Q2**: enables session-end learning capture; addresses long-term-memory gap that PS_problems implicitly references via the AGENT_STATUS continuity narrative.
- **Q3**: v5 > v4 + ≥ Runnable. Block H combines v4 simpler trigger + Runnable's closure-scoped state (extractMemories.ts) + Runnable's configurable throttle (sessionMemory.ts). v5 ≥ Runnable on extraction depth.
- **Q4**: lock test session-end trigger writes new entries to memory.md; lock test handles empty session (no extraction).

### Block L — Runnable error/retry/cache-break extensions (concrete refs)
**Codex blocker fix**: replaced grep recipes with actual line ranges from `_archive/compare_code/gg-claude-code-runnable/src/services/api/`:

`errors.ts`:
- `categorizeRetryableAPIError`: `:1163-end` (the master classifier).
- `isPromptTooLongMessage`: `:62-...`
- `parsePromptTooLongTokenCounts`: `:85-...`
- `isMediaSizeError`: `:133-...`
- `isMediaSizeErrorMessage`: `:147-...`
- `getPdfTooLargeErrorMessage` / `getPdfPasswordProtectedErrorMessage` / `getPdfInvalidErrorMessage` / `getImageTooLargeErrorMessage` / `getRequestTooLargeErrorMessage`: `:170-200`
- `REPEATED_529_ERROR_MESSAGE`: `:166`
- `API_TIMEOUT_ERROR_MESSAGE`: `:169`
- 18 missing v5 categories cover: media-size, repeated-529, request-too-large, timeout, custom-off-switch.

`withRetry.ts`:
- `getRetryAfterMs` (function definition): `:803-810` (parses retry-after header). Call sites at `:284-285`, `:288-294` (short-wait gate + fast-mode fallback hold).
- Retry-after parse + delay: `:431-462`.
- `retryAfterHeader` parse helper: `:532-536`.

`promptCacheBreakDetection.ts`:
- `computeHash`: `:170-...`
- `computePerToolHashes`: `:187-198` (per-tool schema hashing).
- `buildDiffableContent`: `:206-...`
- `recordPromptState`: `:247-...`
- `notifyCacheDeletion`: `:673-...`
- `notifyCompaction`: `:689-...`
- `cleanupAgentTracking`: `:700-...`
- `resetPromptCacheBreakDetection`: `:704-...`

Adoption: extend `core/errors.py` (18 categories) + `core/retry.py` (retry-after, fast-mode fallback) + `core/cache.py` (per-tool hashing, cache-control hash). NO replacement of v5 surfaces — extension only.
- LOC est: 250.
- **Q1**: ~15 PORT_LOG rows (one per Runnable function/constant cited above with its line range).
- **Q2**: addresses error-categorization gap (PS-style risk: model gets generic error and gives up). Per-tool cache-break diagnostics also helps debug PS-Issue-style cache cost spikes.
- **Q3**: v5 > v4 on error-recovery + retry sophistication + cache-break diagnostics. v5 ≈ Runnable post-port (Runnable's surface fully replicated for Bedrock-applicable subset).
- **Q4**: lock test for each new error category + retry-after gating + per-tool cache-break detection (verify hash changes on tool description edit triggers `notifyCacheDeletion`).

### Block N — Hermes net-new patterns (verified line refs only)
**Codex blocker fix**: removed unverifiable claims (safe_writer, scanForInjection — these names don't exist in Hermes source). Block N now only includes patterns whose Hermes line ranges I confirmed by grep:

- **Parallel tool execution with path-conflict detection**: Hermes path-conflict detection at `run_agent.py:311-355` + dispatch logic at `:8274-8523` + ThreadPoolExecutor at `:8581-8584`. Combined ~300 LOC. HIGH user value (40% latency win on independent tool calls).
- **Tool call deduplication**: Hermes `run_agent.py:4639-4655` (verified). ~16 LOC. Small + safe.
- **Fuzzy tool name matching**: Hermes `run_agent.py:4689-4720` (verified). ~30 LOC. Already integrated with Block I.
- **Ephemeral system prompt**: Hermes `run_agent.py:850, 1486-1488` (verified). ~5 LOC.
- **Dynamic tool reference injection**: Hermes `AGENTS.md:627-628` (verified). Implementation = post-process tool schemas at init to inject context-aware references. Block N port: implement in `core/query_engine.py` build-tools-payload phase. NO DEFERRAL.
- DROPPED from Block N (Codex blocker fix): `safe_writer` + `scanForInjection` (no Hermes line ref by those names) AND "Cost-strict defaults" (no specific Hermes line — v5 default 600 was already chosen by v4 in v4.10.10 as a v4-native decision per PS#2; not a Hermes adoption). If user wants atomic file writes + injection scanning, propose as v5-native enhancement in a follow-up audit.
- LOC est: 300 (verified subset only).
- **Q1**: 5 PORT_LOG rows (parallel-exec, dedup, fuzzy-match, ephemeral-prompt, dynamic-tool-ref-injection) — each with verified Hermes line ref. Updated 2026-05-01 to add the 5th row (dynamic-tool-ref-injection) per user no-deferrals directive.
- **Q2**: parallel-exec addresses operator latency (~40% on independent multi-tool calls); dedup prevents subtle PS-style "model loops on same tool with same args" issue.
- **Q3**: v5 > Hermes — we adopt their verified patterns + keep v4 + Runnable foundation.
- **Q4**: lock test parallel-exec independent reads (≥40% wallclock gain) + dedup blocks redundant calls + fuzzy match resolves typos + ephemeral prompt not persisted to session log.

### Block T — v4 tool surface parity (Codex AXIS C 2026-05-01 finding)
v5.0.0 ships 15 tools. v4 ships 26. v5.0.1 closes the gap by porting the 11 missing v4 tools verbatim. Source: `compact_v4/MAIN/agent/sagemaker_agent.py:7247-7399` (the `TOOL_REGISTRY` dict).

| Tool | v4 line | v5 target | Notes |
|---|---|---|---|
| `create_word` | schema :7247-7248 + impl :5642 | `tools/create_word.py` | docx generation; uses python-docx |
| `create_excel` | schema :7250-7258 + impl :5730 | `tools/create_excel.py` | xlsx + embedded chart; uses openpyxl |
| `create_markdown` | schema :7260-7261 + impl :5813 | `tools/create_markdown.py` | simple .md writer |
| `create_notebook` | schema :7263-7270 + impl :5838 | `tools/create_notebook.py` | full .ipynb create (distinct from `notebook_edit` which is surgical) |
| `create_chart` | schema :7287-7297 + impl :6039 | `tools/create_chart.py` | matplotlib PNG renderer |
| `create_pdf` | schema :7299-7305 + impl :6282 | `tools/create_pdf.py` | reportlab PDF; structured sections |
| `todo_write` | schema :7310-7311 + impl :6854 | `tools/todo_write.py` | TodoTracker mutator (closes Q3 axis 4 gap Codex flagged) |
| `todo_read` | schema :7313-7314 + impl :6887 | `tools/todo_read.py` | TodoTracker reader |
| `semantic_search` | schema :7316-7317 + impl :6615 | `tools/semantic_search.py` | AI-indexed code search; index/search/status actions |
| `web_fetch` | schema :7390-7393 + impl :6787 | `tools/web_fetch.py` | URL → readable text (max 30KB) |
| `ask_user` | schema :7395-7399 + impl :6743 | `tools/ask_user.py` | interactive question (used by approval flow) |

All 11 schema + impl line refs verified by grep against v4 source 2026-05-01. Each tool is a verbatim port; v5's existing `tools/registry.py` slot pattern accepts each as a new `ToolDef`.

- LOC est: ~1100 (11 tools × ~100 LOC each verbatim incl. impl + schema; some heavier — create_pdf ~200, semantic_search ~250, others ~50-80).
- **Q1**: 11 PORT_LOG rows.
- **Q2**: closes Codex AXIS C 2026-05-01 v4 baseline gap; addresses TodoTracker port called out in Q3 axis 4.
- **Q3**: v5 = v4 (constraint #1 floor).
- **Q4**: lock test each tool: file-creating tools (create_*) write expected file; todo_write/read round-trips; semantic_search index→search returns hits; web_fetch returns text; ask_user blocks for response then unblocks.

### Block J — Real-Bedrock smoke + zip verification
- New manual env-gated smoke test (`RUN_REAL_BEDROCK=1`) in `tests/integration/test_real_bedrock_smoke.py`.
- Update `compact_v5/verify_ship_zip.py` to extract zip in tmp + run `python -c "import entry"` AND `python -c "import sagemaker_agent"`.
- LOC est: 150.
- **Q1**: 1 PORT_LOG row (v5-native enhancement to ship-gate verifier).
- **Q2**: structurally addresses the v5.0.0 failure mode (Codex caught issues mock tests didn't).
- **Q3**: v5 > v4 (v4 has no extract-and-import zip check) > Runnable (no equivalent gate).
- **Q4**: addresses "all 437 v5.0.0 tests are mock" gap — primary target of this block.

### Block K — Process discipline (LF AXIS C + per-block user gate + STATE/RESUME)
- Add AXIS C plan-fidelity check to `compact_v5/_status/CODEX_REVIEW_TEMPLATE.md`.
- PORT_LOG schema: rows are PORTED only (post user no-deferrals 2026-04-30/05-01). The historical v5.0.0 silent-drops are catalogued in `V5_SHIP_CRITIQUE.md` as a one-time audit artifact (not a future-allowed category). No new DEFERRED rows accepted — every change must be PORTED with source ref.
- **NEW: per-block user-approval gate** — each Block lands as separate commit; user approves before next Block starts.
- **NEW: STATE/RESUME anchoring** — every Block updates `V5_BUILD_STATUS.md` with current Block + next-session pickup. Compaction-resilient.
- New file: `compact_v5/_status/PLAN_FIDELITY_GATE.md` (the new pattern v5 contributes back to LF).
- LOC est: 200 (docs).
- **Q1**: rigorously addresses scope-narrowing failure mode (per user no-deferrals: every change is a PORTED row with source ref; the DEFERRED row category itself is removed, only PORTED is allowed).
- **Q2**: prevents PS-style regressions because the Plan-Fidelity Gate forces every PS Issue resolution to remain on the active Block list — they can't be silently moved to "future."
- **Q3**: v5 > LF (v5 contributes Plan-Fidelity Gate back). v5 > v4 (v4 had no formal phase gate). v5 > Runnable (Runnable has no phase-gate concept).
- **Q4**: addresses the meta-failure mode that allowed v5.0.0 to ship without semantic-bug coverage — by gating each Block on Codex AXIS A/B/C + user approval.

---

## 4. Sequencing (final per Codex)

`Block 0 → notebook smoke gate → B → B+ → C → C+ → D → A → E + F (together) → I → M → G → G2 → H → L → N → T → J → K`

Each Block lands as commit + Codex AXIS A/B/C review + user approval before next Block (Block K rule).

---

## 5. LOC summary (revised)

| Block | LOC | |
|---|---:|---|
| 0 + smoke gate | 100 | new |
| B | 440 | v4 verbatim + wiring + Runnable tokenEstimation |
| B+ | 325 | v4 SessionManager + AGENT_STATUS wiring + FileCache class verbatim |
| C | 250 | v4 verbatim |
| C+ | 200 | v4 + v5 ext |
| D | 700 | v4 verbatim — full 19-command parity (Codex AXIS C 2026-05-01 expansion) + dispatcher + CommandRegistry |
| A | 3300 | v4 + Runnable services/compact/* COMBINED (post-no-deferrals) |
| E + F | 2300 | v4 verbatim + complete session UI |
| I | 50 | v4 + Hermes |
| M | 30 | Runnable port |
| G | 280 | v4 verbatim |
| G2 | 100 | Runnable port |
| H | 1252 | v4 + Runnable extractMemories + sessionMemory COMBINED (post-no-deferrals) |
| L | 250 | Runnable extension |
| N | 300 | Hermes verified ports (incl. dynamic tool ref injection, post-no-deferrals) |
| T | 1100 | v4 tool surface parity (Codex AXIS C 2026-05-01: 11 missing v4 tools — create_word/excel/markdown/notebook/chart/pdf, todo_write/read, semantic_search, web_fetch, ask_user) |
| J | 150 | new |
| K | 200 (docs) | LF + v5 |
| **TOTAL (post-no-deferrals + v4 baseline + tool parity 2026-05-01)** | **~11,330 LOC** | combined v4 + Runnable + Hermes + LF |

LOC delta vs v3 (~5,910): + ~2,600 from Block A combined Runnable compact + ~1,112 from Block H combined Runnable memory + ~380 from Block D full v4 command parity + ~1,100 from Block T v4 tool surface parity (Codex AXIS C 2026-05-01: 11 missing v4 tools) + ~50 tokenEstimation in Block B + ~125 FileCache class in Block B+ + ~100 session UI in Block E+F + ~52 misc deltas.

---

## 6. Verification — the 4 user questions explicitly mapped

| Q | Evidence required | Block(s) producing it |
|---|---|---|
| **Q1** All repos covered with refs | PORT_LOG row per v4 baseline feature; ADR per Runnable adoption; NO DEFERRED rows allowed (per user 2026-04-30/05-01 — every drop is a PORTED row or doesn't exist). | All Blocks + Block K |
| **Q2** No PS Issues recur | Lock tests for PS#1 (already in v5), PS#2 (already), PS#3 (Block A), PS#4 (already), PS#5/#6 (Block B + B+ + D), PS#7 (Block C + already). | A, B, B+, C, D |
| **Q3** v5 ≥ Runnable AND v5 > v4 decisively, axis-by-axis | Per-Block "Q3" subsection with concrete v4-line + Runnable-line refs proving v5 incorporates the better-of-each. Q3_BETTER_THAN_MATRIX.md is settled to "v5 ≥ Runnable on every axis (post-no-deferrals); v5 > Runnable on SageMaker-specific axes; v5 > v4 decisively." | All Blocks |
| **Q4** No semantic bugs | Real-Bedrock smoke (Block J) + long-session test + concurrent-run test + zip-extract-import test. | J + each Block's lock tests |

---

## 7. Status

- **Reports**: 20 (9 Wave 1 + 11 Wave 2). On disk.
- **Codex v1**: REJECT (6 blockers).
- **Codex v2**: REJECT (4 blockers — ref accuracy, Block L specificity, Q1-Q4 per-block, Block N Hermes claims).
- **v3 fixes**: all line refs re-grepped against source; Block L has concrete line ranges; Q1-Q4 in every Block; Block N pruned to verified Hermes patterns only.
- **Codex v3**: APPROVE on plan v3 (post v3c fixes).
- **User no-deferrals directive 2026-04-30 / 2026-05-01**: 5 prior DEFERRED items flipped to PORTED. v3 → v4 corrections applied INLINE in this document.
- **Codex v4 review (2026-05-01)**: AXIS A REJECT → fixes applied (canonical refs + FileCache class line + Runnable extractMemories/sessionMemory paths + Block N row count + tokenEstimation assignment + Runnable-only command decision table + sub-agent attribution acceptance test). Pending re-run.
- **User approval**: REQUIRED before any coding.
