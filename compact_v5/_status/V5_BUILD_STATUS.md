# V5 Build Status

Last updated: 2026-04-30 (Phase 06 DONE — PS Issue #7 STRUCTURALLY FIXED)
Updated by: Phase 06 close pass

## Current phase
- Phase ID: 06 (canonical: 00..13 or 08_5)
- Phase name: Phase 6 — Sectioned prompt + cache (PS Issue #7 STRUCTURAL FIX)
- State: DONE

## Previous phase
- Phase 05 DONE — tagged v5-phase-05 at 603cb76, pushed. 217 pass + 4 skips.

## Done in this phase
- [x] Append **ADR-012**: 19-section design + token caps + cache-boundary contract.
- [x] Write `prompt/sections.py` (Section dataclass + SECTION_ORDER + token caps + memoization + Runnable parity).
- [x] Write 19 `prompt/*.md` files: identity, tool_classes (PROMOTED to slot 2), system, tool_efficiency, doing_tasks, critique_handling, answer_preference, data_validation, executing_actions, output_style, subagent_coord, status_doc, verification_contract, memory_protocol, documents, security, mcp, commands, skill_patching.
- [x] Write `prompt/_CACHE_BOUNDARY.md` marker file.
- [x] Write `prompt/__init__.py` with `build_system_prompt(ctx)` + canonical `CACHE_BOUNDARY` constant (single source of truth).
- [x] Write `core/cache.py` (CacheBlock + build_cache_blocks + fingerprint_sections + detect_cache_break + CacheBreakReport).
- [x] Write `tests/unit/test_prompt_assembly.py` (18 tests including 4 Codex-fix lock tests) and `tests/unit/test_cache.py` (9 tests).
- [x] `pytest tests/` — **247 passed + 4 skipped**.
- [x] **Codex review (gpt-5.5, reasoning=medium, via stdin)**: APPROVE_WITH_FIXES with 1 major + 2 minors + 1 nit. All 4 fixed in same Phase 06 commit:
  - Major: caps sum to 3090, not budget. **Fix**: tightened caps to sum 2880 ≤ 2900.
  - Minor: `build_cache_blocks` stripped leading newlines. **Fix**: removed `.lstrip("\n")`; lock test for byte-equivalence.
  - Minor: boundary constants duplicated/inconsistent. **Fix**: single-source `prompt.CACHE_BOUNDARY`; lock test asserts equality across modules.
  - Nit: `detect_cache_break` assumes unique section names. **Fix**: `test_section_names_are_unique` lock.
- [x] All 3 Runnable patterns FAITHFUL-WITH-JUSTIFIED-ADAPTATION post-fix. UNDECLARED_PATTERN PASS.
- [x] PORT_LOG rows #011 + #012 + #013 added with verdicts.
- [x] **PS_V5 docs updated**: 7 Phase-6 functional-change entries + 4 Phase-6 learnings entries + 6 new "Better than X" tracker rows.
- [x] Write `MAIN/changelogs/CHANGELOG_v5_phase_06.md`.

## Tests status
- Last `pytest` run: 2026-04-30 — **247 passed + 4 skipped** in 5.68s.
- Phase 06 contributes 27 new tests (18 prompt assembly + 9 cache).
- Failing tests: none.

## Codex review status (current phase)
- Last review: 2026-04-30 (gpt-5.5, reasoning=medium, via stdin) — **APPROVE_WITH_FIXES**.
- Findings: 1 major + 2 minors + 1 nit — all addressed.
- Open review comments: 0.
- Saved at: `_status/codex_reviews/phase-06.md`.

## Static prompt metrics
- v4 estimate: ~5000 tokens.
- v5 Phase 06 actual: **2739 tokens** (45% reduction).
- STATIC_TOKEN_BUDGET: 2900 (Phase 06 actual + 6% headroom).
- Per-section cap sum: 2880 (≤ STATIC_TOKEN_BUDGET, locked by test).
- V5_PLAN.md target: ≤2500. Phase 13 polish goal: tighten to 2500.

## PS Issue #7 STRUCTURAL FIX
- `tool_classes.md` at slot 2 (right after identity, before "system"). Locked by `test_tool_classes_section_at_slot_2`.
- File-per-section forces reviewable PR diffs.
- Per-section token caps prevent regrowth to a 914-LOC monolith.
- Aggregate audit gate (before Phase 7) runs cognitive-load test on the current prompt structure.

## Git
- Branch: v5-build
- Last commit: e1a7d1a8eecf42a3ed9fb256d3ed618c514c4a71 "v5/phase-06: sectioned prompt + cache + Codex fixes (PS Issue #7 fix)"
- Last tag: v5-phase-06

## Blockers
- none

## Next session: pick up at
- **AGGREGATE AUDIT GATE before Phase 07**: runs full audit matrix (ADR-PORT_LOG ratio, static prompt tokens, tool count, cognitive-load test). Phase 7 starts only on PASS.
- **Phase 07 — ToolSearchTool deferred loading**: read Runnable `tools/ToolSearchTool/`. Land `tools/tool_search.py` + `apply_tool_search_deferral()` real implementation (Phase 2 stub gets replaced). Mark low-frequency tools as `should_defer=True`. **Acceptance**: per-turn schema overhead drops ≥3000 tokens vs Phase 6 baseline. PS Issue addressed: lower per-turn token cost generally.
- Resume protocol: see `_status/RESUME.md`.
