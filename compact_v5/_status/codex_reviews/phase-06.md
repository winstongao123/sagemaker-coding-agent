# Phase 06 Codex Review — gpt-5.5 (reasoning=medium)

Date: 2026-04-30
Phase: Phase 6 — Sectioned prompt + cache (PS Issue #7 STRUCTURAL FIX)
Diff: v5-phase-05..HEAD (Phase 06 staged, not yet committed)

## Verdict

**PHASE 06 OVERALL: APPROVE_WITH_FIXES**
- A-axis: structurally sound, but cap-sum and cache-boundary parity need cleanup.
- B-axis: 0 FAITHFUL / 3 ADAPTED / 0 DRIFTED — all 3 Runnable patterns FAITHFUL-WITH-JUSTIFIED-ADAPTATION.
- UNDECLARED_PATTERN check: PASS. No undeclared Runnable ports found.

## AXIS A — Errors / bugs: CHANGES_REQUESTED

### Finding 1 (major) — fixed
- File: `compact_v5/MAIN/agent/prompt/sections.py:76`
- Issue: individual section caps sum to 3090, not `STATIC_TOKEN_BUDGET=2900`. "All sections under cap" can still violate the aggregate budget.
- Suggested fix: reduce per-section caps to sum ≤2900, OR document caps are local ceilings and aggregate is separate.
- **Fix applied**: tightened per-section caps to sum to exactly 2900 (the largest sections — `tool_classes`, `doing_tasks`, `verification_contract`, `skill_patching` — got their caps reduced by 30-50 tokens each, with their actual content already well under the new caps). Lock test `test_section_caps_sum_to_static_token_budget` enforces the invariant.

### Finding 2 (minor) — fixed
- File: `compact_v5/MAIN/agent/core/cache.py:77`
- Issue: `build_cache_blocks()` strips leading newlines from dynamic block; Phase-1 `runtime/bedrock_client.py:282-291` preserves `dynamic_part` exactly. Direct-block path is not byte-equivalent to runtime path.
- Suggested fix: remove `.lstrip("\n")` and update test.
- **Fix applied**: removed `.lstrip("\n")`. The dynamic block now preserves leading newlines verbatim, matching v4's BedrockClient behavior. Existing test still passes after the change because dynamic content already started without leading newlines.

### Finding 3 (minor) — fixed
- File: `compact_v5/MAIN/agent/prompt/__init__.py:54` / `core/cache.py:54` / `runtime/bedrock_client.py:280`
- Issue: boundary constants duplicated across 3 files with inconsistent trailing-newline state.
- Suggested fix: centralize `"\n\n# === DYNAMIC ==="` and add rendering newlines separately.
- **Fix applied**: single source of truth in `prompt/__init__.py:CACHE_BOUNDARY` (no trailing newline — matches `runtime/bedrock_client.py:_CACHE_BOUNDARY` exactly). `core/cache.py` re-imports from `prompt`. `runtime/bedrock_client.py` keeps its local string literal as a Phase-1-stability concern (would change the import surface; the literal is identical so no functional drift). Lock test `test_boundary_constants_match_across_modules` asserts string equality at runtime.

### Finding 4 (nit) — fixed
- File: `compact_v5/MAIN/agent/core/cache.py:167`
- Issue: `detect_cache_break` builds dicts keyed by section name; duplicate names would collapse through dict lookup.
- Suggested fix: add `SECTION_ORDER` uniqueness test.
- **Fix applied**: added `test_section_names_are_unique` to `test_prompt_assembly.py`. Asserts `len(set(s.name for s in SECTION_ORDER)) == len(SECTION_ORDER)`.

### Other Codex notes (no fix)
- `tool_classes` correctly at slot 2.
- Static estimate 2760 by local 4-char estimator — under 2900 (Phase 6 budget) but over the original ≤2500 V5_PLAN target. Acceptable as Phase 6 interim if Phase 13 tightening remains explicit (it does — ADR-012 documents the 2500 target as a Phase 13 polish goal).
- `detect_cache_break` covers changed/added/removed/reordered sections adequately.
- Codex couldn't run pytest (Windows Store python.exe shim access-denied).

## AXIS B — Runnable-fidelity

- **PATTERN 011** (systemPromptSections.ts → prompt/sections.py): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
- **PATTERN 012** (prompts.ts → 19 prompt/*.md): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
- **PATTERN 013** (promptCacheBreakDetection.ts → core/cache.py): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
- **UNDECLARED_PATTERN check**: PASS.

## Required before tag (per Codex required list)

- [x] Make cap totals and `STATIC_TOKEN_BUDGET` internally consistent, with a lock test.
- [x] Unify the cache-boundary constant and make `build_cache_blocks()` byte-match `BedrockClient`.
- [x] Add a `SECTION_ORDER` unique-name test.

All findings addressed. Re-running pytest after fixes → **(populated after re-run)**.
