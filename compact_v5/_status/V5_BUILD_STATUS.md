# V5 Build Status

Last updated: 2026-04-30 (Phase 0 scaffolding)
Updated by: Phase 0 init

## Current phase
- Phase ID: 00 (canonical: 00..13 or 08_5)
- Phase name: Phase 0 — Scaffold compact_v5/ skeleton
- State: IN_PROGRESS
- Started: 2026-04-30
- Target completion: 2026-04-30

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
- [ ] git commit Phase-00 follow-up (HTMLs + PS mapping + ADR-003/004 + AXIS B strengthening)
- [ ] Re-run `lint_phase_id.py 00` after commit
- [ ] Re-run Codex review (gpt-5.5 reasoning=high) on full Phase 00 state
- [ ] git tag `v5-phase-00`
- [ ] Update this file: State=DONE, Last commit sha, "Next session: pick up at" → Phase 01

## Tests status
- Last `pytest` run: 2026-04-30 — PASS (2 passed, 0 failed) — `tests/test_smoke.py` only
- Failing tests (if any): none

## Codex review status (current phase)
- Last review: 2026-04-30 — APPROVE (scaffold-only, no Runnable port to evaluate; full Codex `exec` review starts at Phase 01)
- Open review comments: 0

## Git
- Branch: v5-build
- Last commit: <pending — first commit at end of Phase 0>
- Last tag: <none yet>

## Blockers
- none

## Next session: pick up at
- Phase 00, step "Add .gitignore entries"
- Resume protocol: see _status/RESUME.md
