# V5 Build Status

Last updated: 2026-04-30 (Phase 0 closing)
Updated by: Phase 0 close

## Current phase
- Phase ID: 00 (canonical: 00..13 or 08_5)
- Phase name: Phase 0 — Scaffold compact_v5/ skeleton
- State: DONE
- Started: 2026-04-30
- Completed: 2026-04-30

## Done in this phase so far
- [x] Created `v5-build` branch off `master`
- [x] Created `compact_v5/` folder tree (15 packages + _status/ + docs/ + MAIN/changelogs/)
- [x] Created 5 tracking docs in `_status/`
- [x] 4 ADRs accepted (ADR-001 file-per-tool, ADR-002 file-per-section prompt, ADR-003 v5 addresses all 7 PS_actual_use_problems issues, ADR-004 reference HTMLs copied)
- [x] Added `.gitignore`
- [x] Created per-package `__init__.py` files (15 packages, all empty)
- [x] Created `tests/test_smoke.py` — passes 2/2
- [x] Created `tests/lint_phase_id.py` — pre-tag canonical-ID lint, passes 5/5
- [x] Copied V5_PLAN.md to `compact_v5/docs/V5_PLAN.md`
- [x] Wrote Phase 00 Codex review stub (`_status/codex_reviews/phase-00.md`)
- [x] First commit `5259adf` on `v5-build` (`v5/phase-00: scaffold compact_v5/...`)
- [x] Codex CLI upgraded 0.116.0 → 0.125.0 + memory updated for gpt-5.5 default
- [x] Copied 6 reference HTMLs to `compact_v5/docs/htmls/` (PS_DEEP_DIVE_RUNNABLE, PS_FLOWCHART_RUNNABLE, PS_FLOWCHART_V4, PS_RUNNABLE_VS_LANGGRAPH, HERMES_VS_CODING_AGENT_v4, v4_architecture)
- [x] Copied `PS_actual_use_problems.md` to `compact_v5/docs/`
- [x] Created `compact_v5/docs/V5_PS_ISSUES_MAPPING.md` — every issue mapped to v5 phase that addresses it + acceptance criteria
- [x] Strengthened CODEX_REVIEW_TEMPLATE.md AXIS B with integration-semantic check (up-stream caller, down-stream deps, state/cache contract, error contract)

## Remaining for this phase
- [x] git commit `cd5f00e` non-HTML follow-up (PS mapping + ADR-003/004 + AXIS B strengthening)
- [x] git commit `03abf29` HTMLs (6 reference HTMLs)
- [ ] Re-run Codex review (gpt-5.5 reasoning=high) on full Phase 00 state
- [ ] Re-run `lint_phase_id.py 00`
- [ ] git tag `v5-phase-00`
- [ ] Update this file: State=DONE, Last commit sha, "Next session: pick up at" → Phase 01

## Tests status
- Last `pytest` run: 2026-04-30 — PASS — `tests/test_smoke.py` (recursive scan for v4 leaks)
- Failing tests (if any): none

## Codex review status (current phase)
- Last review: 2026-04-30 — APPROVE_WITH_FIXES (gpt-5.5) — 3 minor findings, all addressed in Phase 0 close commit
  1. V5_BUILD_STATUS.md stale fields → updated (this edit)
  2. test_smoke.py too shallow → made recursive with allowlist
  3. ADR ordering in V5_DESIGN_DECISIONS.md (001, 003, 004, 002) → reordered to 001, 002, 003, 004
- Open review comments: 0 (all addressed)

## Git
- Branch: v5-build
- Last commit: <to be filled by Phase 0 close commit>
- Last tag: v5-phase-00 (after Phase 0 close commit + lint pass)

## Blockers
- none

## Next session: pick up at
- Phase 01: Bedrock client + Config (port v4 BedrockClient to runtime/bedrock_client.py + Config to runtime/config.py)
- Read order per RESUME.md Step 1: V5_BUILD_STATUS.md → V5_DESIGN_DECISIONS.md → V5_RUNNABLE_PORT_LOG.md → V5_PLAN.md phase 01 row → last 3 commits → Codex review of phase-00.md
- Resume protocol: see _status/RESUME.md
