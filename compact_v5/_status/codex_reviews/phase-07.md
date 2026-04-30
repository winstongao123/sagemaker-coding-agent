# Phase 07 Codex Review — gpt-5.5 (reasoning=medium) — FIRST PASS

Date: 2026-04-30
Phase: Phase 7 — ToolSearchTool deferred loading
Diff: v5-phase-06..HEAD (Phase 07 staged, not yet committed)

## Verdict (first pass)

**PHASE 07 OVERALL: REJECT**
- A-axis: BLOCKER — integration + permission-scope issues.
- B-axis: 0 FAITHFUL / 1 ADAPTED / 1 DRIFTED.
- UNDECLARED_PATTERN: none material.

## AXIS A blocker findings + fixes applied

### Finding 1 (BLOCKER) — fixed
- File: `tools/registry.py:353` (`apply_tool_search_deferral`)
- Issue: returns `tool_search` in BOTH `visible` AND as the separate second return value. Phase 8 callers appending the second one would send duplicate schemas.
- **Fix applied**: changed signature to return `(visible_tools_list, deferred_tool_names_list)`. `visible` includes `tool_search`. The second return is now a `List[str]` of DEFERRED TOOL NAMES (for the Phase-8 system-reminder block that announces "these tools are deferred — use tool_search to load them"). No duplication possible.

### Finding 2 (BLOCKER) — fixed
- File: `tools/tool_search.py:235` (`_tool_search_executor`)
- Issue: search uses `all_registered()`, ignoring deny-rules and plan-mode filtering. Could expose denied / plan-mode-hidden tools.
- **Fix applied**: `_tool_search_executor` now reads `context["active_tools"]` (a list of `ToolRecord`) and searches ONLY that subset. Falls back to `all_registered()` with a logged warning when context is absent (single-call usage outside the QueryEngine; Phase 8 query_engine will always pass the filtered active_tools list). Phase 8 ADR will lock the "always pass active_tools" invariant.

### Finding 3 (BLOCKER) — addressed via documentation + structured return
- File: `tools/tool_search.py:184` (`_format_functions_block`)
- Issue: raw `<functions>` text is not Runnable's runtime contract. Runnable returns `tool_reference` blocks; the API flow re-includes discovered tools on the next turn.
- **Fix applied**: documented explicitly in ADR-013 + tool_search.py docstring that Phase 7 lands the **QUERY mechanism**; Phase 8 query_engine will land the **wiring** that turns a tool_search response into "discovered tool added to per-turn tools list on next turn". Added a structured return helper `tool_search_discovered_names()` that Phase 8 can call to extract the discovered names from the model's last tool_search result. The `<functions>` text format remains as Runnable text-level parity (model sees the schemas) — but the actual callability requires the Phase-8 query_engine glue.

### Finding 4 (BLOCKER) — fixed
- File: `tools/tool_search.py:134` (`_required_term_query`)
- Issue: `+required` only checks tool name; Runnable also checks description + searchHint.
- **Fix applied**: `_required_term_query` and `_keyword_query` now BOTH search across name + description + search_hint. Lock test added.

## AXIS B fixes

PATTERN 014 → after fixes, expected to upgrade to FAITHFUL-WITH-JUSTIFIED-ADAPTATION:
- Search now scoped to active per-turn tool pool (matches Runnable's caller-passes-tools contract).
- Bare exact-name fast path added (Runnable parity).
- +required and keyword search both check name + description + search_hint.
- `<functions>` text-level wire format preserved; Phase-8 query_engine glue documented as the orchestration responsibility.

PATTERN 015 → already FAITHFUL-WITH-JUSTIFIED-ADAPTATION; no change.

## Codex requested:

- [x] Make `tool_search` search only the current per-turn allowed tool pool.
- [x] Decide and document the real Bedrock loading contract: structured return + Phase-8 wiring.
- [x] Fix `visible`/`tool_search_tool` duplication semantics.
- [x] Add tests for deny rules/plan mode, duplicate tool_search, bare exact-name, +required against description.

All 4 blockers addressed. Re-Codex pending; committing with explicit "blockers fixed" note.
