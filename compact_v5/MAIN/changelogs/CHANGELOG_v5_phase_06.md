# CHANGELOG — v5 Phase 06

**Phase**: 06 — Sectioned prompt + cache (PS Issue #7 STRUCTURAL FIX)
**Date closed**: 2026-04-30
**Tag**: `v5-phase-06`
**Branch**: `v5-build`

## Goal — the fix that motivated v5

v4's flat 914-LOC `SYSTEM_PROMPT` f-string created a "buried matrix" failure mode: under cognitive load (40-call exec limit hit), the model under-attended to mid-list bullets and concluded "all tools blocked", refused to keep working. Round 3 v4.10.10 patches were behavioral; the structural fix required architectural change.

Phase 06 is that structural fix: replace the monolithic f-string with 19 file-per-section `prompt/*.md` files + a registry + token caps + cache-break detection. Promote `tool_classes` to slot 2 so the tool-capability matrix is among the FIRST things the model reads.

## ADRs accepted this phase

- **ADR-012** — Phase 6 sectioned prompt: file-per-section + token budget + cache-boundary contract.

## Files added

| Path | LOC | Purpose |
|------|-----|---------|
| `compact_v5/MAIN/agent/prompt/__init__.py` | ~95 | `build_system_prompt(ctx)` + canonical `CACHE_BOUNDARY` constant. |
| `compact_v5/MAIN/agent/prompt/sections.py` | ~200 | `Section` dataclass + `SECTION_ORDER` + per-section token caps + `STATIC_TOKEN_BUDGET=2900` + memoization (`get/set/clear_section_cache`) + Runnable parity. |
| 19 × `compact_v5/MAIN/agent/prompt/*.md` | ~2740 tokens total | Per-section content. `tool_classes.md` at slot 2 (PS Issue #7 fix). |
| `compact_v5/MAIN/agent/prompt/_CACHE_BOUNDARY.md` | — | Marker file containing `# === DYNAMIC ===`. |
| `compact_v5/MAIN/agent/core/cache.py` | ~180 | `CacheBlock` + `build_cache_blocks` + `fingerprint_sections` + `detect_cache_break` + `CacheBreakReport`. |
| `compact_v5/MAIN/agent/tests/unit/test_prompt_assembly.py` | ~265 | 18 tests including 4 new Codex-fix lock tests. |
| `compact_v5/MAIN/agent/tests/unit/test_cache.py` | ~120 | 9 tests for cache-break detection. |
| `compact_v5/_status/codex_reviews/phase-06.md` | — | Phase 06 Codex review record. |

## Files modified

| Path | Change |
|------|--------|
| `compact_v5/_status/V5_BUILD_STATUS.md` | Phase 06 closure documented. |
| `compact_v5/_status/V5_DESIGN_DECISIONS.md` | Appended ADR-012 (19-section design + token-cap table + cache-boundary contract). |
| `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` | Added rows #011 (systemPromptSections.ts → sections.py), #012 (prompts.ts → 19 .md files), #013 (promptCacheBreakDetection.ts → core/cache.py). |
| `compact_v5/docs/PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md` | 7 Phase-6 entries. |
| `compact_v5/docs/PS_V5_LEARNINGS_FROM_REPOS.md` | 4 Phase-6 entries + 6 new "Better than X" tracker rows. |

## Tests

- `pytest tests/` — **247 passed + 4 skipped** in 5.68s.
- Phase breakdown:
  - 2 smoke
  - 11 bedrock (Phase 01)
  - 22 registry (Phase 02)
  - 36 read-only tools + path-validation (Phase 03)
  - 53 mutating tools / diff_widget (Phase 04)
  - 49 security + 20 bash/python (Phase 05)
  - **27 prompt assembly + cache (NEW Phase 06)** — including 4 Codex-fix lock tests:
    - `test_section_caps_sum_to_static_token_budget` — sum of caps ≤ STATIC_TOKEN_BUDGET
    - `test_section_names_are_unique` — SECTION_ORDER uniqueness
    - `test_boundary_constants_match_across_modules` — single source of truth for cache boundary
    - `test_build_cache_blocks_dynamic_part_is_byte_equivalent` — no lstrip; matches Phase-1 BedrockClient behavior
- 4 skips: 1 Windows symlink + 3 v4-source-not-reachable parity (from Phase 5).

## Codex review

- Model: `gpt-5.5` (reasoning=medium, via stdin pipe)
- Verdict: **APPROVE_WITH_FIXES** → all 4 findings (1 major + 2 minors + 1 nit) addressed in the same Phase 06 commit.
- AXIS A findings:
  - **Major**: section caps sum to 3090, not `STATIC_TOKEN_BUDGET=2900`. **Fix**: tightened per-section caps (`tool_classes` 420→410, `doing_tasks` 320→300, `verification_contract` 180→170, `skill_patching` 240→225, etc.) so cap sum is now 2880 ≤ 2900. Lock test added.
  - **Minor**: `build_cache_blocks` stripped leading newlines from dynamic block; `runtime/bedrock_client.py` preserves them. **Fix**: removed `.lstrip("\n")`; lock test asserts byte-equivalence.
  - **Minor**: cache-boundary constants duplicated across 3 files with inconsistent trailing-newline state. **Fix**: single source of truth `prompt.CACHE_BOUNDARY` (no trailing newline, matches Phase-1 BedrockClient literal); `core.cache` imports from `prompt`; `runtime/bedrock_client.py` keeps its local literal but a lock test asserts string equality across all 3 modules.
  - **Nit**: `detect_cache_break` assumes unique section names (dict-keyed). **Fix**: `test_section_names_are_unique` locks the invariant.
- AXIS B verdicts:
  - **PATTERN 011** (systemPromptSections.ts → sections.py): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION** (constraint=Bedrock).
  - **PATTERN 012** (prompts.ts → 19 .md files): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION** (constraint=Bedrock).
  - **PATTERN 013** (promptCacheBreakDetection.ts → core/cache.py): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION** (constraint=Bedrock).
  - **UNDECLARED_PATTERN check**: PASS.

## PS Issue mapping addressed

- **PS Issue #7 — buried-matrix failure mode (THE motivation for v5)**: STRUCTURALLY FIXED in this phase.
  - Mechanism 1: file-per-section forces every prompt addition through a reviewable PR diff at the per-file level.
  - Mechanism 2: per-section token caps prevent any single section from growing back to a 914-LOC dump.
  - Mechanism 3: `tool_classes.md` at slot 2 means under cognitive load the LLM attends to the tool-capability matrix BEFORE the rest of the prompt. Locked by `test_tool_classes_section_at_slot_2`.
  - Mechanism 4: aggregate audit gate (Phase 07 entry) runs the cognitive-load test against the current prompt structure before Phase 7 starts.
- **PS Issue #2 — iteration budget visible**: not Phase 6 (Phase 8 query_engine wires the IterationBudget UI in Phase 11).
- **PS Issue #4 — thinking config sent every call**: locked Phase 1; no change Phase 6.

## Better-than-v4 + Better-than-Runnable

- **Better than v4**: PS Issue #7 structurally prevented; per-section caps prevent regression; cache-break self-diagnosis.
- **Better than Runnable**: file-per-section vs Runnable's 914-LOC f-string (1/19th the PR review surface per change). Phase 6 cache-break detector intentionally smaller than Runnable's full hash-tree (no per-tool hashes / global-cache strategy / betas list yet — those land Phase 12+).
- **Better than both**: 45% prompt reduction (2739 vs ~5000 tokens) without losing behavioral coverage.

## Static prompt budget — interim vs Phase 13 polish

- V5_PLAN.md target: ≤2500 tokens.
- Phase 06 actual: 2739 tokens (45% reduction from v4's ~5000).
- `STATIC_TOKEN_BUDGET=2900` (Phase-6 actual + 6% headroom for minor edits).
- **Phase 13 polish goal**: tighten to ≤2500. ADR-012 explicitly documents this.

## Pickup point for next session

- **AGGREGATE AUDIT GATE before Phase 07** (per V5_PLAN.md): runs the full audit metric matrix:
  - ADR-to-PORT_LOG ratio (every PORT_LOG row references an ADR) — currently 11 PORT_LOG rows, 12 ADRs.
  - Static prompt tokens — 2739 (under 2900 budget; 45% reduction from v4).
  - Tool count — currently 10 v5 tools (read_file, grep, glob, list_dir, write_file, edit_file, notebook_edit, view_image, bash, python_exec). v4 has 30. Well under v4+0.
  - Cognitive-load test (Codex-evaluated): simulate "Blocked: bash + python_exec limit reached (200/session)" and check the prompt structure leads the model to continue with read_file/grep/edit_file. Phase 7 starts only on PASS.
- **Phase 07 — ToolSearchTool deferred loading**: read Runnable `tools/ToolSearchTool/` and adopt the deferred-tool-schema pattern. Acceptance: per-turn schema overhead drops ≥3000 tokens vs Phase 6 baseline.
- Resume protocol: `_status/RESUME.md`.
