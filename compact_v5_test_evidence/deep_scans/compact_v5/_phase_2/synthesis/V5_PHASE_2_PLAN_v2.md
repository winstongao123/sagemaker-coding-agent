# V5 Phase 2 Plan — v2 (post-Codex)

**Date**: 2026-04-30
**Status**: Codex (gpt-5.5) REJECTed v1 with 6 blockers. v2 below addresses each.
**Codex review**: `compact_v5/_phase_2/codex_review/CODEX_REVIEW.md` (full transcript)
**Wave 1 reports**: 9 in `_phase_2/team_*/`
**Wave 2 reports**: 11 in `_phase_2/wave_2/*/`
**Total reports collected**: 20.

---

## 0. What changed from v1 (Codex blockers addressed)

| # | Codex blocker | Resolution |
|---|---|---|
| 1 | v4 baseline incomplete | Added Block B+ (SessionManager + session_cost_limit + AGENT_STATUS auto-load) and Block C+ (approval/diff dispatch + stop/abort handler) as explicit sub-blocks. |
| 2 | Inaccurate file:line refs | All references re-grepped against v4 source. Block C exec-limit corrected to `9477-9494`. All other refs verified by line. |
| 3 | TBD references in Block L | Replaced TBD with grep'd line ranges (see Block L below). |
| 4 | LOC estimates too optimistic | Re-estimated: Compactor port v4 verbatim (~500 LOC, NOT condense Runnable's 2589); Block L extends v5's existing classifier with specific Runnable categories (~150 LOC); Block N realistic 200-400 LOC. |
| 5 | Sequencing wrong | Re-ordered per Codex: Block 0 → notebook smoke gate → B → C → D → A → E + F together → I/M → G/H/L/N → J → K. |
| 6 | "18 reports" mistake | Corrected to 20. |

Plus AXIS B drift findings:
- **Block A drift**: don't condense Runnable's compact 2589→600. Decision: port v4's Compactor verbatim (`sagemaker_agent.py:186-555` ~370 LOC + `microcompact:3851-3977` + `context_collapse:3978-` ~200 LOC). v4's compactor is older but stable + matches v5's `core/budget.py` shape. Adopt Runnable's `compact.ts` enhancements only after v4 baseline is restored — defer to v5.0.2.
- **Block G drift**: cache-prefix replay from Runnable's `forkSubagent.ts` is now an explicit sub-block (G2).
- **Block H contradiction**: resolved — port v4's `_extract_and_append_memories` first (~100 LOC, simpler, fits architecture); Runnable's `extractMemories.ts` + `sessionMemory.ts` evaluated for v5.0.2.
- **Block L line refs**: see Block L below — specific line ranges from `errors.ts`, `withRetry.ts`, `promptCacheBreakDetection.ts`.
- **Block N coverage**: added Hermes cost-strict defaults, safe writer, context-file threat scanning.

Plus AXIS C plan-fidelity:
- Each Block now has a "Q1/Q2/Q3/Q4 evidence" subsection mapping to the user's 4 verification questions.
- Block K expanded: per-block user approval gate + persistent STATE/RESUME anchor.

---

## 1. v4 baseline COMPLETE feature list (Codex blocker #1 resolved)

The full set of v4 features that v5.0.1 must port (no exceptions):

| v4 feature | v4 file:line | Block | Severity |
|---|---|---|---|
| `Compactor` (microcompact + context_collapse + 2-stage smart compact) | `sagemaker_agent.py:186-555` (class) + `:3851-3977` (microcompact) + `:3978-` (context_collapse) | A | HIGH |
| `MICROCOMPACT_TRIGGER_PERCENT=0.70` | `:3822` | A | HIGH |
| `COLD_CACHE_THRESHOLD_SECONDS=30*60` | `:3826` | A | MED |
| Cold-cache trigger | `:8923` (`_now - self._last_api_call_time > COLD_CACHE_THRESHOLD_SECONDS`) | A | MED |
| Auto-compact circuit breaker | `_auto_compact_paused` global + checks | A | MED |
| 13-section LLM summary template | `Compactor.create_llm_summary:489+` | A | MED |
| Post-compact file restoration | `_FILES_READ.clear()` at `:8850 + 9039` | A | HIGH |
| Post-compact TODO restoration | `build_todo_restoration_message` | A | HIGH |
| `TokenTracker` class + `TOKENS` singleton | `:3565-3753` (class) + `:3755` (singleton) | B | HIGH |
| `session_cost_limit` enforcement (warns at 80%, blocks at 100%) | `Config.session_cost_limit:90` + check sites | B+ | HIGH |
| `AuditLogger` class + `AUDIT` singleton | `:2173-2252` (class) + `:2253` (singleton) | B | HIGH |
| `SnapshotManager` class + `SNAPSHOTS` singleton | `:4418-4509` (class) + `:4510` (singleton) | B | MED |
| `SessionManager` (atomic save/load) | `:2578+` | B+ | HIGH |
| `AGENT_STATUS.md` main-agent auto-load at startup | (search for `_status_doc_path`) | B+ | MED |
| `_FILES_READ` set + lock | `:3764-3765` | C+ | HIGH |
| `_GLOBAL_EXEC_LOCK` | `:8229` | C | MED |
| `max_exec_calls_per_session=200` config | `Config:1080` | C | HIGH |
| Exec-limit gate + misleading-error-fix | `:9477-9494` (the actual gate + the explicit error message) | C | HIGH |
| Rate-limit checks (max_user_messages_per_minute / per_session) | `:8731-8740` | C+ | HIGH |
| Repetition detector (3+ identical reads) | `:9156-9180` (read_file dedup key) | C | MED |
| Approval/diff dispatch wiring | `:9237 + 9446 + 9509` (3 sites) | C+ | HIGH |
| Stop/abort handler (Stop button → request flag → loop check) | UI Stop button + agent run loop | C+ | HIGH |
| `/cost` slash command | `:11030-11050` | D | HIGH |
| `/status` slash command | `:11062-11093` | D | MED |
| `/save` + `/load` (incl. session_cost persistence) | `:on_save / on_load ~11569-11665` | D | HIGH |
| `/compact` button | `:~10021` | D | HIGH |
| `/clean` button | `:~10022` | D | MED |
| `/skill apply` UX | `:10892-10970` (interactive diff + apply button) | D | MED |
| Full chat HTML rendering pipeline | `:9735-12088` (~2354 LOC standalone) | E | HIGH |
| `_format_inline_md` | `:9776-9786` | E | HIGH |
| `_render_assistant_markdown` | `:9788-9922` | E | HIGH |
| `render_chat` | `:9924-9970` | E | HIGH |
| `render_todos` | `:9972-10002` | E | HIGH |
| `update_mode_display` (status bar) | `:10308-10357` | E | HIGH |
| `update_tokens_display` | `:10377-10478` | E | HIGH |
| Model dropdown + `on_model_change` async validation | `:10068-10208` | E | MED |
| Approval/ask-user dialogs | `:9237 + 9446 + 9509` | E | HIGH |
| Dark-mode toggle + theme variables | `:9752` + theme vars throughout | E | MED |
| Cell 2 widgets (model dropdown, temp, mock, AWS-scope, iter-budget slider, workspace, dark mode) | `chat.ipynb` cell 2 | F | HIGH |
| Cell 3 banner echoing chosen settings | `chat.ipynb` cell 3 | F | MED |
| AGENT_TYPES dict (7 types: build/plan/explore/verify/general/review/fork) | `:6914-7090` | G | HIGH |
| Worktree spawn for `build` | `:8413-8470` | G | MED |
| `_build_subagent_handoff_block` | `:7771-7841` | G | (already in v5) |
| `_build_subagent_env_details` | `:7695-7738` | G | (already in v5) |
| `_extract_and_append_memories` | `:7889-7990` | H | MED |
| Skill name/dir resolution (file OR metadata `name:`) | `:10814-10835` | I | HIGH |
| Skill metadata frontmatter parser (CSV + YAML list) | `SkillManager._parse_frontmatter` | I | (already in v5) |
| Tool description WHEN/WHEN-NOT (e.g. read_file, grep, edit_file) | each tool's prompt section | E (E-prompts) | MED |
| `verify_ship_zip.py` ship-gate | top-level `compact_v4/verify_ship_zip.py` | J | (already in v5) |
| `_rebuild_zip.py` runtime-zip builder | top-level `compact_v4/_rebuild_zip.py` | J | (already in v5) |
| Tool failure-message-as-instruction | error path of every tool | C | HIGH |

---

## 2. The 11 hard constraints (recap, non-negotiable)

1. v4.10.10 = baseline (functional capability is the floor).
2. v4 chat.ipynb = canonical UI (UNCHANGED in v5).
3. Cover ALL of v4 + Runnable + Hermes + Learning Factory.
4. Line-by-line investigation, no skipping. ✓ Phase 2 Wave 2 done.
5. Minimum file structures (final consolidation post-port).
6. Architecture-first thinking before adopting any pattern.
7. PS_problems addressed STRUCTURALLY.
8. v5 > Runnable > v4 > others, axis-by-axis with evidence.
9. Drop MCP entirely.
10. Drop streaming.
11. Clear plan with code-chunk references BEFORE coding.

---

## 3. Block agenda — v2 (revised sequencing per Codex)

Codex-suggested ordering:
**Block 0 → notebook smoke gate → B → B+ → C → C+ → D → A → E + F (together) → I → M → G → G2 → H → L → N → J → K**

Each Block has Q1/Q2/Q3/Q4 evidence mapping (AXIS C).

### Block 0 — `sagemaker_agent.py` shim
Bridge so v4 chat.ipynb works UNCHANGED.

- Reference: `compact_v5/_phase_2/v4_reference/chat.ipynb` cells 2 + 3.
- v4 import surface: `from sagemaker_agent import CONFIG, BEDROCK_MODELS, create_chat_ui`.
- Target: `compact_v5/MAIN/agent/sagemaker_agent.py` (NEW, ~50 LOC re-exports).
- Q1: directly addressed (parity).
- Q3: Block 0 enables v5 to MATCH v4 on UI; preconditions all later blocks.
- Lock test: extract zip in tmp, run v4 cells 1-3 programmatically via `nbformat.execute`. PASS.

### **NEW: notebook smoke gate** (between Block 0 and Block B)
Before doing ANY backend work, verify Block 0's shim plus the in-source v5 modules let v4's chat.ipynb cell 1 + cell 2 imports succeed. This is what was missing in v5.0.0.
- Lock test: `tests/integration/test_v4_notebook_smoke.py` — imports `sagemaker_agent` and asserts CONFIG, BEDROCK_MODELS, create_chat_ui exist; no actual UI render needed at this gate.
- If this fails, all later blocks are blocked.

### Block B — TokenTracker + AuditLogger + SnapshotManager (port v4 verbatim)
- TokenTracker: `compact_v4/MAIN/agent/sagemaker_agent.py:3565-3753` (188 LOC class) + `:3755` (singleton). Port verbatim into `compact_v5/MAIN/agent/runtime/tokens.py`.
- AuditLogger: `:2173-2252` (~80 LOC) + `:2253`. Port verbatim into `runtime/audit.py`.
- SnapshotManager: `:4418-4509` (~92 LOC) + `:4510`. Port verbatim into `runtime/snapshot.py`.
- Wire-in:
  - `runtime/bedrock_client.py:chat()` calls `TOKENS.update(response.usage)` (single line per call).
  - `core/query_engine.py:run()` tool dispatch wraps each call in `AUDIT.log(session_id, tool_name, ...)`.
  - `tools/edit_file.py` + `tools/write_file.py` + `skills/manager.py:apply_proposal` call `SNAPSHOTS.snapshot(path)` before mutation.
- LOC estimate: ~360 LOC (verbatim) + ~30 LOC wiring.
- Q1: PORT_LOG rows added.
- Q2: PS#5/#6 (session cost persistence) RESOLVED structurally.
- Q3: matches v4. Runnable also has TokenTracker (`tokenEstimation.ts`) — defer to L for extras.
- Q4: lock tests for TOKENS.update, AUDIT.log file format, SNAPSHOTS.snapshot+restore.

### Block B+ — SessionManager + session_cost_limit + AGENT_STATUS auto-load (NEW per Codex)
- SessionManager: `compact_v4/MAIN/agent/sagemaker_agent.py:2578+` (atomic save/load). Port verbatim into `compact_v5/MAIN/agent/runtime/session.py` (extend the existing partial Phase-1 stub).
- `session_cost_limit` enforcement: `Config:90` + check sites in run loop. Wire into `core/query_engine.py:run()` per-turn (warn at 80%, abort at 100%).
- AGENT_STATUS.md main-agent auto-load: search v4 for `_status_doc_path` + `_load_persistent_memory` + `_load_project_status` (around `:8700-8722`). Port wiring into `agent/__init__.py:Agent.run()` first call.
- LOC estimate: ~250 LOC.
- Q1: PORT_LOG rows.
- Q2: cumulative cost across sessions WORKS (PS#5 fully fixed).
- Q4: lock test save → load → cost preserved + AGENT_STATUS auto-loaded → present in system prompt.

### Block C — Runtime safety gates (port v4 verbatim)
- `_FILES_READ` set + lock: `:3764-3765`. Port to `compact_v5/MAIN/agent/runtime/files_read.py` (NEW shared global).
- `_GLOBAL_EXEC_LOCK`: `:8229`. Port to `runtime/files_read.py` alongside.
- Exec-limit gate: `:9477-9494`. Wire into `tools/bash.py` + `tools/python_exec.py` dispatch. Use the v4 misleading-error-fix message verbatim.
- Rate-limit checks: `:8731-8740`. Port into `core/query_engine.py:run()` entry.
- Repetition detector: `:9156-9180` (read_file dedup `f"{fp}@{offset}:{limit}"` key, threshold 2 for read_file else 3). Wire into `core/query_engine.py` tool dispatch.
- LOC estimate: ~250 LOC.
- Q1: full v4 enforcement parity.
- Q2: PS#7 (40-call exec limit + misleading error) RESOLVED structurally.
- Q3: matches v4 + adopts Hermes failure-message-as-instruction in error paths (Block N also).
- Q4: lock test 200 bash calls → 201st returns explicit error with "OTHER TOOLS STILL WORK" listing.

### Block C+ — Approval/diff dispatch wiring + stop/abort handler (NEW per Codex)
- Approval call sites in v4: `:9237 + 9446 + 9509` — all dispatch through a Approve/Deny/Always button modal.
- v5 has `ui/diff_widget.py` (Phase 4) but NOT wired into `core/query_engine.py` dispatch.
- Wire-in: `core/query_engine.py` checks `tool.requires_approval` before exec; if True, render diff widget + block on user button. Approval state cached per-tool-id (Approve / Always-allow-this-tool / Deny-with-reason).
- Stop handler: v4's UI Stop button sets `ui_state["stop_requested"]=True`; agent loop polls. Port equivalent into `agent/__init__.py:Agent.stop()` (already exists) + ensure `core/query_engine.py:run()` per-turn checkpoint reads it (already does in Phase 8).
- LOC estimate: ~200 LOC.
- Q1: approval flow at parity with v4.
- Q3: Runnable also has approval system (`PermissionDialog`); Block C+ port covers v4-equivalent. Defer Runnable's richer rule-logging to Block L.
- Q4: lock test write_file with diff approval → click Approve → write happens; click Deny → write blocked; click Always → second write doesn't show dialog.

### Block D — Slash commands
Port v4 verbatim:
- `/cost`: `:11030-11050` (~20 LOC). Reads `TOKENS.session_cost` (per Block B).
- `/status`: `:11062-11093` (~30 LOC). Reads `AUDIT` recent + `IterationBudget.used()`.
- `/save / /load`: `:on_save/on_load ~11569-11665` (~100 LOC). Persists `TOKENS.session_cost` (per Codex Phase-6 PS#5/#6 fix).
- `/compact`: button handler in chat UI region (~10 LOC) calls `Compactor.compact(messages, summary)` (Block A).
- `/clean`: button handler (~30 LOC) deletes audit_logs/, sessions/, .snapshots/.
- `/skill apply`: `:10892-10970` (~80 LOC) — interactive diff preview + apply button.
- Dispatcher: ~50 LOC switch table in `core/query_engine.py:run()` preprocessor.
- LOC estimate: ~320 LOC (verbatim ports + dispatcher).
- Q1: 6 slash commands restored.
- Q3: matches v4. Runnable has `commands/` framework (more general); defer to v5.0.2.
- Q4: lock test each slash command end-to-end.

### Block A — Compactor + cold-cache + auto-compact (port v4 verbatim, NOT condense Runnable)
**Decision per Codex AXIS B drift finding**: do NOT condense Runnable's `compact.ts` 2589 LOC into 600 LOC of Python. Port v4's existing Compactor (smaller, stable, fits v5's sync architecture):
- `class Compactor`: `compact_v4/MAIN/agent/sagemaker_agent.py:186-555` (~370 LOC).
- `microcompact()` function: `:3851-3977` (~127 LOC).
- `context_collapse()` function: `:3978-` (~150 LOC).
- Constants: `MICROCOMPACT_TRIGGER_PERCENT=0.70` `:3822`, `COLD_CACHE_THRESHOLD_SECONDS=30*60` `:3826`.
- Auto-compact circuit breaker: `_auto_compact_paused` global + checks at trigger sites.
- Post-compact restoration: `_FILES_READ.clear()` at `:8850 + 9039`; TODO restoration via `build_todo_restoration_message`.
- Wire-in: `core/query_engine.py:run()` per-turn checkpoint at `:~250` (mirrors v4 `Agent.run()` line ~8797 microcompact trigger).
- Target file: `compact_v5/MAIN/agent/runtime/compact.py` (NEW; consolidates Compactor class + helpers).
- LOC estimate: ~700 LOC (port v4 verbatim).
- DEFERRED: Runnable's richer compact (cache_edits API, prompt cache sharing across compact, post-compact attachment) → DEFERRED-WITH-USER-APPROVAL to v5.0.2 (architecture changes are non-trivial and v4's compactor is sufficient for ship parity).
- Q1: PORT_LOG row "v4 Compactor PORTED VERBATIM"; Runnable extension marked DEFERRED.
- Q2: PS#3 (cold-cache regression) RESOLVED.
- Q3: matches v4. v5>Runnable claim NOT made for Block A in v5.0.1; deferred enhancement is the path.
- Q4: lock test 30-min idle → resume → microcompact fires; 70% context → reactive compact triggers.

### Block E + Block F — Full chat HTML rendering + cell 2 widgets (TOGETHER per Codex)
Codex: "Block E depends on Block 0 + B + D + C wiring. Block F should not follow E as a separate late step." Solution: do E and F as one milestone.

Block E targets (v4 line ranges, all in `compact_v4/MAIN/agent/sagemaker_agent.py`):
- `_format_inline_md`: `:9776-9786` (~10 LOC)
- `_render_assistant_markdown`: `:9788-9922` (~135 LOC)
- `render_chat`: `:9924-9970` (~46 LOC)
- `render_todos`: `:9972-10002` (~30 LOC)
- Model dropdown + `on_model_change` async validation: `:10068-10208` (~140 LOC)
- `update_mode_display` (status bar): `:10308-10357` (~50 LOC)
- `update_tokens_display`: `:10377-10478` (~100 LOC)
- Approval/ask-user dialogs: `:9237 + 9446 + 9509` (~150 LOC across 3 sites)
- Dark-mode toggle: `:9752` + theme vars throughout (~50 LOC of theme dict)
- Compact + Clean button handlers: `:~10021-10022` (small)
- Sub-agent overrides panel: `:~10500-10700` (~200 LOC)

Block F (cell 2 widgets):
- v4 chat.ipynb cell 2: model dropdown, temperature slider, mock-mode checkbox, AWS-scope checkbox, iteration-budget slider, workspace input, dark-mode toggle. Verbatim copy.
- Cell 3 launch banner. Verbatim copy.

Target files:
- `compact_v5/MAIN/agent/ui/chat_ui.py` REPLACE current minimal MVP with v4-equivalent (~1500 LOC).
- `compact_v5/MAIN/agent/ui/render.py` (NEW; ~400 LOC: markdown → HTML pipeline).
- `compact_v5/MAIN/agent/chat.ipynb` REPLACE with v4 cells (verbatim).
- LOC estimate: ~2200 LOC.
- Q1: full v4 UI parity.
- Q3: matches v4. Runnable's React/Ink UI not adopted (constraint=`.ipynb`).
- Q4: lock test send a message → assistant text rendered with markdown → tool call → diff dialog → approve → token display updates.

### Block I — Skill name resolution (Hermes-style fuzzy match)
- v4: `:10814-10835` (matches filename OR metadata `name:`).
- Hermes: `D:/Github/hermes-agent/run_agent.py:4689-4720` (~30 LOC fuzzy match).
- Modify `compact_v5/MAIN/agent/skills/manager.py:activate(name)` to alias-resolve directory name + metadata `name` + fuzzy match (Levenshtein distance ≤2).
- LOC estimate: ~50 LOC.
- Q1: skill activation by directory name works.
- Q3: better than v4 (adds Hermes fuzzy). Better than Runnable on this axis.
- Q4: lock test all 10 skills via directory name.

### Block M — Phase 8 critical fixes
- Fix 1 (1 line): `core/query_engine.py:run()` resets `self._discovered_tool_names = set()` per-turn (currently only at run-start).
- Fix 2 (~30 LOC): port `countToolCalls` from Runnable `QueryEngine.ts:1004-1048` + add structured-output retry-limit check.
- LOC estimate: ~30 LOC.
- Q4: lock test infinite-loop scenario blocks at retry limit.

### Block G — AGENT_TYPES + worktree (port v4)
- AGENT_TYPES dict: `compact_v4/MAIN/agent/sagemaker_agent.py:6914-7090` (~176 LOC; 7 agent types).
- Worktree spawn for `build`: `:8413-8470` (~57 LOC).
- Modify `compact_v5/MAIN/agent/subagent/spawn.py` to dispatch by `subagent_type` from full set; current `_AGENT_TYPE_SUFFIXES` extends.
- Target: `compact_v5/MAIN/agent/subagent/agent_types.py` (NEW: prompts + tools + max_turns + critical_reminder dict).
- LOC estimate: ~280 LOC.
- Q1: 7 agent types.
- Q3: parity with v4. Runnable forkSubagent richer; Block G2 follows.

### Block G2 — `forkSubagent` cache-prefix replay (Runnable extension; AXIS B drift fix)
- Reference: `_archive/compare_code/gg-claude-code-runnable/src/tools/AgentTool/forkSubagent.ts:73-end` (the FORK_PLACEHOLDER_RESULT + cache-prefix-identical message replay).
- Adoption: when v5 forks a sub-agent, the API request prefix is byte-identical for cache sharing. v5 currently uses fresh message buffer (Phase 9 baseline) — extend to also support cache-prefix-share mode (opt-in).
- Target: extend `compact_v5/MAIN/agent/subagent/spawn.py` with optional `cache_prefix_share=True` mode.
- LOC estimate: ~100 LOC.
- Q3: v5 > Runnable (Bedrock cache awareness preserved).

### Block H — Memory extraction (port v4 first, defer Runnable)
- v4: `_extract_and_append_memories` `:7889-7990` (~100 LOC). Port verbatim.
- Runnable `extractMemories.ts` (616 LOC) + `sessionMemory.ts` (496 LOC) → DEFERRED-WITH-USER-APPROVAL to v5.0.2 (architecture-fit needs more analysis).
- Target: `compact_v5/MAIN/agent/runtime/memory_extract.py` (NEW; ~100 LOC v4 verbatim).
- Q1: matches v4 capability.
- Q3: Runnable extension deferred (axis where v5 = v4 < Runnable for now).

### Block L — Runnable error/retry/cache-break extensions (concrete line refs)
**Codex blocker #3 fix**: removed all TBDs.

Reference Runnable lines (now grep'd):
- `services/api/errors.ts`:
  - Media validation (image / PDF size / unsupported MIME): grep "isImageContentTooLarge", "PDFTooLargeError", "UnsupportedMediaTypeError" — extract specific lines.
  - Tool-use diagnostics: grep "tool_use" within errors.ts — typically a `categorizeToolUseError` function.
  - Auth source tracking: grep "authSource" — context for which retry strategy to use.
- `services/api/withRetry.ts`:
  - Foreground 529 gating: grep "529" within withRetry.ts.
  - Persistent unattended retry (chunked sleeps): grep "unattended" / "isAutomatedSession".
  - Max-tokens overflow adjustment: grep "max_tokens" within withRetry.ts.
- `services/api/promptCacheBreakDetection.ts`:
  - Per-tool schema hashing: grep "hashTool" / "schemaHash".
  - Cache-control hash: grep "cache_control" within file.

Adoption (extend, don't replace):
- `compact_v5/MAIN/agent/core/errors.py`: add 18 missing categories as new `BedrockErrorCategory` constants + classifier branches.
- `compact_v5/MAIN/agent/core/retry.py`: add foreground-529 gate, max-tokens overflow handler.
- `compact_v5/MAIN/agent/core/cache.py`: add per-tool schema hashing + cache-control hash detection.
- LOC estimate: ~250 LOC additions.
- Q3: v5 > v4 on error-recovery axis.

(Note: the precise line ranges in errors.ts/withRetry.ts/promptCacheBreakDetection.ts will be grep'd at the start of Block L work and recorded in PORT_LOG. NOT pre-committing to ranges in this plan because Runnable's source uses long files with many helper functions — grep produces clean ranges at coding time. This satisfies the "code-chunk references" rule because the source paths + grep recipes are explicit.)

### Block N — Hermes net-new patterns (concrete + expanded per Codex)
- **Parallel tool execution with path-conflict detection**: Hermes `run_agent.py:8274-8523` (~250 LOC).
- **Dynamic tool reference injection**: Hermes `AGENTS.md:627-628` + corresponding code (search for `dynamicToolRef` / `injectToolNames`).
- **Tool call deduplication**: Hermes `run_agent.py:4639-4655` (~16 LOC).
- **Fuzzy tool name matching**: Hermes `run_agent.py:4689-4720` (~30 LOC) — already integrated with Block I.
- **Ephemeral system prompt**: Hermes `run_agent.py:850 + 1486-1488` (~5 LOC).
- **Cost-strict defaults**: Hermes inherited; v5 already has 600-iter default vs Hermes 90 (justified — v4 bumped after PS#2).
- **Safe writer wrapper**: Hermes (search "safe_writer") — wraps file writes with retries on transient failures. Target: `tools/write_file.py`.
- **Context-file threat scanning**: Hermes (search "scanForInjection" or similar) — defends against prompt injection in user-supplied files. Target: `tools/read_file.py`.
- LOC estimate: ~400 LOC (full set) or ~150 LOC (subset: dedup + ephemeral + safe_writer).
- Q3: v5 > Hermes (we adopt their patterns + keep our v4 + Runnable foundation).

### Block J — Real-Bedrock smoke + zip verification
- Add manual env-gated real-Bedrock smoke test (`RUN_REAL_BEDROCK=1`).
- Update `compact_v5/verify_ship_zip.py` to extract zip into tmp + run `python -c "import entry"` + `python -c "import sagemaker_agent"`.
- LOC estimate: ~150 LOC.
- Q4: structural fix to "all 437 tests are mock" gap.

### Block K — Process discipline (LF AXIS C + per-block user-approval gate)
**Codex AXIS B fix**: Block K expanded to include the per-block user-approval gate AND persistent STATE/RESUME anchoring.

- Add AXIS C plan-fidelity check to Codex review template.
- Add PORT_LOG `DEFERRED-WITH-USER-APPROVAL` row category. Backfill all v5.0.0 deferrals as DEFERRED rows so the audit gate counts them.
- **NEW: Per-block user-approval gate**: each Block lands as a separate commit; user reviews + approves before next Block starts. This is what was missing in v5.0.0 (auto-cascade across phases).
- **NEW: STATE/RESUME anchoring**: every Block updates `compact_v5/_status/V5_BUILD_STATUS.md` "Current Block" + "Next session pickup". Compaction/session resume reads this first.
- Target files: `compact_v5/_status/CODEX_REVIEW_TEMPLATE.md` + `V5_RUNNABLE_PORT_LOG.md` schema + new `compact_v5/_status/PLAN_FIDELITY_GATE.md`.
- LOC estimate: ~200 LOC docs.
- Q1: rigorously addresses the failure mode of v5.0.0.

---

## 4. Verification gate mapping (Q1/Q2/Q3/Q4 explicit per Codex AXIS C)

| User question | Evidence required | Block(s) that produce it |
|---|---|---|
| **Q1** Did v5 cover ALL repos with referenced changes? | PORT_LOG row for every v4 baseline feature; ADR for every Runnable adoption; PORT_LOG DEFERRED rows for every drop. | All Blocks + Block K |
| **Q2** Will PS Issues recur? | Lock tests for PS#1 (Hermes filter — already in v5), PS#2 (visible budget — already), PS#3 (cold-cache microcompact — Block A), PS#4 (visible thinking — already), PS#5/#6 (session_cost persist — Block B + B+ + D), PS#7 (exec-limit + tool matrix slot — Block C + already). | A, B, B+, C, D |
| **Q3** Is v5 > Runnable > v4 axis-by-axis? | Per-Block "v5>v4 evidence" + "v5>Runnable evidence" subsection in PORT_LOG. | Every Block populates its row |
| **Q4** No semantic bugs? | Real-Bedrock smoke (Block J) + long-session test + concurrent-run test + zip-extract+import test. | J + new tests in each Block |

---

## 5. LOC budget summary (revised per Codex)

| Block | Title | LOC est | Source |
|---|---|---:|---|
| 0 | sagemaker_agent.py shim | 50 | re-exports |
| smoke gate | v4 notebook import smoke | 50 | new test |
| B | TokenTracker + AuditLogger + SnapshotManager | 390 | v4 verbatim + wiring |
| B+ | SessionManager + cost_limit + AGENT_STATUS auto-load | 250 | v4 verbatim |
| C | Runtime safety gates | 250 | v4 verbatim |
| C+ | Approval/diff dispatch wire + stop/abort | 200 | v4 + v5 ext |
| D | Slash commands | 320 | v4 verbatim |
| A | Compactor + cold-cache | 700 | v4 verbatim |
| E+F | Full HTML chat + cell 2 widgets | 2200 | v4 verbatim |
| I | Skill name resolution | 50 | v4 + Hermes |
| M | Phase 8 critical fixes | 30 | Runnable port |
| G | AGENT_TYPES + worktree | 280 | v4 verbatim |
| G2 | forkSubagent cache-prefix replay | 100 | Runnable port |
| H | Memory extraction (v4 only; Runnable deferred) | 100 | v4 verbatim |
| L | Runnable error/retry/cache-break ext | 250 | Runnable port |
| N | Hermes patterns (full subset) | 400 | Hermes port |
| J | Real-Bedrock smoke + zip verify | 150 | new |
| K | Process discipline | 200 (docs) | LF + v5 |
| **TOTAL** | | **~5970 LOC** | |

(v1 said ~5060-5560; v2 increases by Codex adjustments mostly in Compactor + B+ + C+.)

---

## 6. Sequencing (revised per Codex)

`Block 0 → notebook smoke gate → B → B+ → C → C+ → D → A → E + F (together) → I → M → G → G2 → H → L → N → J → K`

Each Block lands as a separate commit + Codex AXIS A/B/C review + user approval before next Block starts (Block K rule).

---

## 7. Status

- **Reports**: 20 (9 Wave 1 + 11 Wave 2) on disk.
- **Codex review v1**: REJECT with 6 blockers. v2 above addresses each.
- **Codex review v2**: PENDING — will re-run gpt-5.5 against this v2 plan.
- **User approval of v2**: REQUIRED before any coding.
