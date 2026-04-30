# V5 Build Status

Last updated: 2026-04-30 (Phase 05 DONE)
Updated by: Phase 05 close pass

## Current phase
- Phase ID: 05 (canonical: 00..13 or 08_5)
- Phase name: Phase 5 — bash + python_exec + security verbatim from v4
- State: DONE

## Previous phase
- Phase 04 DONE — tagged v5-phase-04 at 7cf3e47, pushed to sageagent. 128 pass + 1 skip. Codex APPROVE_WITH_FIXES.

## Done in this phase
- [x] Read v4 SecurityManager class (compact_v4/MAIN/agent/sagemaker_agent.py:1298-2148) + tool_bash (:5239) + tool_python_exec (:5409) + closure-based sandbox preamble (:5293)
- [x] Append **ADR-011**: Phase 5 strategy = REUSE v4 verbatim, retire `_path_validation` stub, document `python_exec -I` deviation
- [x] Write `runtime/truncation.py` (verbatim port of v4 Truncation class)
- [x] Write `security/` package: `__init__.py` (with dynamic SECURITY + get_security helper), `manager.py`, `dangerous_patterns.py`, `dangerous_python.py`, `high_risk.py`
- [x] Convert `tools/_path_validation.py` to a 4-line delegating shim (forwards to security.manager)
- [x] Write `tools/bash.py` (v4 tool_bash port + adapted Runnable BashTool prompt) and `tools/python_exec.py` (v4 tool_python_exec port + closure-sandbox preamble + `-I` flag)
- [x] Update `tools/__init__.py` bootstrap_built_ins to register bash + python_exec
- [x] Update `tests/tools/test_phase3_*.py` and `test_phase4_*.py` workspace fixtures to call rebuild_singleton_for_tests
- [x] Write `tests/unit/test_security_manager.py` (49 tests including 134-case parity + representative-command matrix + stale-singleton lock + `-I` flag lock)
- [x] Write `tests/tools/test_phase5_bash_python.py` (20 tests)
- [x] `pytest tests/` — **217 passed + 4 skipped** (4 skips: 1 Windows symlink, 3 v4-source-not-reachable parity tests)
- [x] **Codex review (gpt-5.5, reasoning=medium, via stdin)**: APPROVE_WITH_FIXES with 2 majors + 2 minors. All 4 addressed in same Phase 05 commit:
  - Major #1: bash + python_exec captured `SECURITY` at module import (stale after rebuild). **Fix**: call-time `_security_manager.SECURITY` dereference.
  - Major #2: 134-case coverage was sampled, not full parity. **Fix**: 3 v4-vs-v5 pattern-count parity tests + 25-case representative matrix.
  - Minor #3: `__init__.py` docs over-promised about live binding. **Fix**: clarified live-vs-stale patterns + added `get_security()` helper.
  - Minor #4: `python_exec -I` flag deviates from v4. **Fix**: ADR-011 documents as intentional hardening + lock test.
- [x] All 4 Codex findings verified by lock tests.
- [x] PORT_LOG row #010 updated to FAITHFUL-WITH-JUSTIFIED-ADAPTATION post-fix.
- [x] **PS_V5 docs updated**: PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md gained 7 Phase-5 entries; PS_V5_LEARNINGS_FROM_REPOS.md gained 6 Phase-5 entries + 7 new "Better than X" tracker rows.
- [x] Write `MAIN/changelogs/CHANGELOG_v5_phase_05.md`.

## Tests status
- Last `pytest` run: 2026-04-30 — **217 passed + 4 skipped** in 5.86s.
- Phase breakdown: 2 smoke + 11 bedrock + 22 registry + 36 read-only + 53 mutating/diff (Phase 4 + locks) + 49 security + 20 bash/python + 24 cross-phase invariants = 217.
- Failing tests: none.

## Codex review status (current phase)
- Last review: 2026-04-30 (gpt-5.5, reasoning=medium, via stdin) — **APPROVE_WITH_FIXES**
- Findings: 2 major + 2 minor — all addressed.
- Open review comments: 0.
- Saved at: `_status/codex_reviews/phase-05.md`.

## Git
- Branch: v5-build
- Last commit: <to-be-filled-after-commit> "v5/phase-05: security verbatim port + bash + python_exec + Codex fixes"
- Last tag: v5-phase-05

## Blockers
- none

## Next session: pick up at
- **Phase 06 — Sectioned prompt + cache + audit gate before Phase 7** (per V5_PLAN.md). This is the structural PS Issue #7 fix: replace v4's 914-LOC f-string `SYSTEM_PROMPT` with file-per-section `prompt/*.md` files + `prompt/sections.py` registry + cache-boundary enforcement.
  - Read Runnable `constants/prompts.ts` (914 LOC) + `constants/systemPromptSections.ts` (registry) + `services/api/promptCacheBreakDetection.ts`.
  - Land 13-14 prompt/*.md files (identity, tool_classes, tool_efficiency, doing_tasks, critique_handling, answer_preference, data_validation, executing_actions, output_style, subagent_coord, verification_contract, memory_protocol, _CACHE_BOUNDARY).
  - Land `prompt/__init__.py:build_system_prompt(ctx)`, `prompt/sections.py`, `core/cache.py:detect_cache_break()`.
  - **Acceptance**: static prompt ≤ 2500 tokens (vs v4's ~5000); cache-boundary test passes.
- **AGGREGATE AUDIT GATE before Phase 7** (per V5_PLAN.md): static-prompt-tokens + cognitive-load test must pass.
- Resume protocol: `_status/RESUME.md`.
