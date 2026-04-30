# CHANGELOG — v5 Phase 07

**Phase**: 07 — ToolSearchTool deferred loading (highest-leverage Runnable port)
**Date closed**: 2026-04-30
**Tag**: `v5-phase-07`
**Branch**: `v5-build`

## Goal

Port Runnable's deferred-loading pattern: low-frequency tool schemas are NOT in the per-turn prompt; only their names appear in a `<system-reminder>`. When the model needs one, it calls `tool_search("<query>")` which returns the full schema in a `<functions>` block. Phase 7 lands the QUERY mechanism; Phase 8 query_engine will land the API wiring that makes discovered tools callable.

## ADRs accepted this phase

- **ADR-013** — Phase 7 ToolSearchTool deferred loading: 3-mode query parser, `<functions>` wire format, `is_deferred_tool` rule, real `apply_tool_search_deferral` (replaces Phase-2 stub).

## Files added

| Path | LOC | Purpose |
|------|-----|---------|
| `compact_v5/MAIN/agent/tools/tool_search.py` | ~330 | 3 query modes (bare-name / select / +required / keyword) + name-parsing + `<functions>` wire format + Phase-8 discovered-names extraction helper. |
| `compact_v5/MAIN/agent/tests/unit/test_tool_search.py` | ~420 | 32 tests including 7 Codex-fix lock tests. |
| `compact_v5/_status/codex_reviews/phase-07.md` | — | Phase 07 Codex review record (REJECT first pass + all 4 blockers fixed). |

## Files modified

| Path | Change |
|------|--------|
| `compact_v5/MAIN/agent/tools/registry.py:apply_tool_search_deferral` | **Replaced Phase-2 stub** with real partition logic. **Codex fix #1**: signature changed from `(visible, tool_search_tool_or_None)` to `(visible, deferred_names_list)` — eliminates the duplicate-tool_search bug. tool_search is now ALWAYS in `visible`; the second return is the list of deferred tool NAMES (for Phase-8's system-reminder block). |
| `compact_v5/MAIN/agent/tools/__init__.py` | Extended `bootstrap_built_ins()` to register tool_search. |
| `compact_v5/MAIN/agent/tools/{view_image,list_dir,notebook_edit}.py` | Added `should_defer=True` flag. |
| `compact_v5/MAIN/agent/tests/unit/test_registry.py` | Updated 2 Phase-2 stub tests to the new (visible, names_list) signature; added a third test for the partition behavior. |
| `compact_v5/_status/V5_BUILD_STATUS.md` | Phase 07 closure documented. |
| `compact_v5/_status/V5_DESIGN_DECISIONS.md` | Appended ADR-013. |
| `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` | Added rows #014 + #015. |
| `compact_v5/docs/PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md` | 5 Phase-7 entries. |
| `compact_v5/docs/PS_V5_LEARNINGS_FROM_REPOS.md` | 2 Phase-7 entries + 2 new "Better than X" tracker rows. |

## Tests

- `pytest tests/` — **280 passed + 4 skipped**.
- Phase 7 contributes 32 new tests in `test_tool_search.py` + 1 updated + 2 new in `test_registry.py`.
- 4 skips: 1 Windows symlink + 3 v4-source-not-reachable parity (pre-existing from Phase 5).

## Codex review

- Model: `gpt-5.5` (reasoning=medium, via stdin pipe)
- **First pass: REJECT** with 4 BLOCKERS + PATTERN 014 DRIFTED.
- **All 4 blockers fixed in same Phase 07 commit**:
  - **Blocker #1** — `apply_tool_search_deferral` returned tool_search in BOTH `visible` AND as a separate return; Phase 8 callers appending the second one would send duplicate schemas. **Fix**: signature changed to `(visible_with_tool_search, deferred_names_list)`. tool_search appears in visible exactly once; second return is `List[str]` of names for the system-reminder block. Lock tests: `test_deferral_no_duplicate_tool_search`, `test_apply_tool_search_deferral_enabled_with_tool_search_partitions`.
  - **Blocker #2** — `tool_search` executor used `all_registered()`, not the per-turn filtered pool — could expose deny-listed / plan-mode-hidden tools. **Fix**: `_resolve_active_tools(context)` reads `context["active_tools"]` (Phase 8 query_engine MUST pass this). Falls back to `all_registered()` with a logged warning. Lock test: `test_active_tools_context_filters_search`.
  - **Blocker #3** — raw `<functions>` text wasn't a complete Runnable runtime contract; v5 had no proven Bedrock loading flow. **Fix**: documented Phase 7 = QUERY mechanism, Phase 8 = wiring. Added `tool_search_discovered_names()` helper that parses a hidden v5-specific marker (`<!-- v5_discovered:NAME1,NAME2 -->`) out of the tool_result text. Phase 8 query_engine will call this and add discovered tools to the next turn's `tools=` API param. Lock tests: `test_tool_search_discovered_names_extraction`, `test_tool_search_discovered_names_empty_on_no_matches`, `test_tool_search_discovered_names_handles_missing_marker`.
  - **Blocker #4** — `+required` only checked tool name; Runnable also checks description + searchHint. **Fix**: `_required_term_query` and `_keyword_query` now BOTH search across name + description + search_hint via `_haystack_for_tool()`. Lock tests: `test_required_term_searches_description_too`, `test_keyword_search_hits_description`.
- **Plus** added bare-exact-name fast path (Runnable parity) per Codex's PATTERN 014 finding. Lock test: `test_bare_exact_name_fast_path`.
- **Plus** added plan-mode interaction lock test: `test_plan_mode_via_active_tools_excludes_mutating_deferred`.
- AXIS B verdicts (post-fix):
  - **PATTERN 014** (ToolSearchTool.ts → tool_search.py): expected upgrade from DRIFTED to **FAITHFUL-WITH-JUSTIFIED-ADAPTATION** (lock tests cover all 4 blocker fixes).
  - **PATTERN 015** (prompt.ts → is_deferred_tool + apply_tool_search_deferral): unchanged at **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.

## Aggregate audit (re-run after fixes)

ALL 7 metrics PASS:
- Static prompt: 2498 ≤ 2500 ✓
- Per-section caps respected ✓
- Cap sum 2880 ≤ budget 2900 ✓
- Section names unique ✓
- tool_classes at slot 2 ✓
- Tool count: 11 v5 vs ~30 v4 ✓
- ADR-to-PORT_LOG ratio: 15 rows / 13 ADRs, all referenced ✓

## Token-saving measurement

- Phase 6 baseline: ~4000 tokens/turn for the tools block.
- Phase 7 with 3 deferred (view_image, list_dir, notebook_edit): ~3230 tokens/turn — **~770 tokens saved**.
- Phase 13 target: ≥3000 tokens. Cumulative savings land as Phases 9-10 add task / todo_* / create_* / web_fetch / ask_user / skill_* to the deferred set.

## Phase 7 = QUERY mechanism; Phase 8 = WIRING

This split is critical for Codex's blocker #3 resolution:
- Phase 7's `<functions>` text is Runnable wire-format parity — the model SEES the schemas.
- Phase 8 query_engine MUST:
  1. Call `apply_tool_search_deferral(tools, enabled=True)` per turn.
  2. After each model turn, scan tool_use blocks for tool_search calls.
  3. Extract discovered names via `tool_search_discovered_names(text)`.
  4. On the next turn, include those tools' full schemas in the `tools=` API param.

The Phase-7 hidden marker (`<!-- v5_discovered:NAME1,NAME2 -->`) makes the extraction step (3) robust without re-parsing the JSON.

## Pickup point for next session

- **Phase 08 — QueryEngine + retry + errors + IterationBudget UI**: read Runnable `QueryEngine.ts` (1295 LOC) + `withRetry.ts` + `services/api/errors.ts`. Land:
  - `compact_v5/MAIN/agent/core/query_engine.py` — main agent loop. MUST call `apply_tool_search_deferral(enabled=True)` and `tool_search_discovered_names()` to wire deferred tools (Phase 7's blocker #3 contract).
  - `compact_v5/MAIN/agent/core/retry.py` — withRetry adaptation.
  - `compact_v5/MAIN/agent/core/errors.py` — error message generators.
  - `compact_v5/MAIN/agent/core/budget.py` — IterationBudget (Hermes-style; PS Issue #2 visible budget).
- **Phase 8 acceptance**: end-to-end mock test (tool_use → tool runs → final answer) AND `tool_search` deferred-loading round-trip works.
- Resume protocol: see `_status/RESUME.md`.
