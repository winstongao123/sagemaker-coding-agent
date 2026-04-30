# V5 Build Status

Last updated: 2026-04-30 (Phase 04 DONE)
Updated by: Phase 04 close pass

## Current phase
- Phase ID: 04 (canonical: 00..13 or 08_5)
- Phase name: Phase 4 — Core mutating tools (write_file, edit_file, notebook_edit, view_image) + ui/diff_widget.py
- State: DONE

## Aggregate audit (pre-Phase-04, 2026-04-30)
- ADR-to-PORT_LOG ratio: PASS — 9 PORT_LOG rows post-Phase-04, all reference an ADR.
- ADRs accepted: 10 (001-010).
- Tool count: v5 has 8 tools post-Phase-04 (read_file, grep, glob, list_dir, write_file, edit_file, notebook_edit, view_image), v4 has 30 — well under ceiling.
- Verdict: PASS, Phase 04 unblocked. Phase 05 starts after this close.

## Previous phase
- Phase 03 DONE — tagged v5-phase-03 at 3507215. Codex APPROVE_WITH_FIXES, all 4 findings fixed.

## Done in this phase
- [x] Read Runnable `src/tools/FileWriteTool/prompt.ts`, `FileEditTool/prompt.ts`, `NotebookEditTool/prompt.ts`, `FileEditTool/UI.tsx` and v4 executors (`tool_write_file:4632`, `tool_edit_file:4729`, `tool_notebook_edit:5921`, `tool_view_image:6419`).
- [x] Append **ADR-010**: Phase 4 strategy — REUSE v4 executors + ADAPT Runnable prompts + diff_widget UI. FAITHFUL-WITH-JUSTIFIED-ADAPTATION (constraint = .ipynb / Bedrock / python_exec).
- [x] Add 4 PORT_LOG rows (#006-009) with Codex verdicts: all 4 patterns FAITHFUL-WITH-JUSTIFIED-ADAPTATION post-fix.
- [x] Write `tools/_file_read_tracking.py` (~80 LOC; Phase-4 stub of v4 _FILES_READ + _FILE_READ_TIMES; Phase 8 retires).
- [x] Write 4 tool modules: `tools/write_file.py`, `edit_file.py`, `notebook_edit.py`, `view_image.py` (~620 LOC total). Each has idempotent `_register()`.
- [x] Write `ui/diff_widget.py` (~245 LOC; HTML colored diff with red/green/gray rows, file path header, ±3 lines context, click-to-expand `<details>`, HTML-escape security; stdlib only — no new deps).
- [x] Update `tools/__init__.py` to bootstrap the 4 new tools.
- [x] Write 31 mutating-tool tests + 8 diff_widget tests (39 new Phase 04 tests).
- [x] **Codex review (gpt-5.5, reasoning=medium, via stdin)**: APPROVE_WITH_FIXES with 1 major + 2 minor + 2 nits — all addressed in same commit:
  - Major #1: notebook_edit broader exception catch.
  - Minor #2: view_image `_PENDING_IMAGES` side channel + `pop_pending_images()` accessor.
  - Minor #3: diff_widget EOF-newline visibility.
  - Nit #4: stale-check directional semantics (current > last + 0.5).
  - Nit #5: 3 new lock tests for the above.
- [x] All 4 Runnable patterns verified FAITHFUL-WITH-JUSTIFIED-ADAPTATION post-fix. UNDECLARED_PATTERN check PASS.
- [x] **NEW user-requested docs updated**: PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md (7 Phase-4 entries) + PS_V5_LEARNINGS_FROM_REPOS.md (Runnable PORT_LOG #006-009 entries + 6 new "Better than X" tracker rows).
- [x] Write `MAIN/changelogs/CHANGELOG_v5_phase_04.md`.

## Tests status
- Last `pytest` run: 2026-04-30 — **128 passed + 1 skipped** in 1.63s (post-Codex-fix).
- Phase breakdown: 2 smoke + 11 bedrock + 22 registry + 36 read-only tools + **39 mutating tools / diff_widget + 4 Codex-fix lock tests + 14 view_image/queue/EOF tests** ≈ 128.
- Failing tests: none.
- 1 skip = Windows symlink test from Phase 03 (admin elevation needed).

## Codex review status (current phase)
- Last review: 2026-04-30 (gpt-5.5, reasoning=medium, via stdin) — **APPROVE_WITH_FIXES**
- Findings: 1 major + 2 minor + 2 nits — all addressed.
- Open review comments: 0.
- Saved at: `_status/codex_reviews/phase-04.md`.

## Git
- Branch: v5-build
- Last commit: 7cf3e47 "v5/phase-04: mutating tools + diff_widget + Codex fixes"
- Last tag: v5-phase-04

## Blockers
- none

## Next session: pick up at
- **Phase 05 — bash + python_exec + security verbatim from v4**: this is the security port. Read v4's `SecurityManager` class + `DANGEROUS_PATTERNS` + `DANGEROUS_PYTHON` + `HIGH_RISK_TOOLS` (134-case destructive command coverage). Port verbatim. Land:
  - `compact_v5/MAIN/agent/security/__init__.py`
  - `compact_v5/MAIN/agent/security/manager.py`
  - `compact_v5/MAIN/agent/security/dangerous_patterns.py`
  - `compact_v5/MAIN/agent/security/dangerous_python.py`
  - `compact_v5/MAIN/agent/security/high_risk.py`
  - `compact_v5/MAIN/agent/tools/bash.py`
  - `compact_v5/MAIN/agent/tools/python_exec.py`
- **Phase 5 retires `tools/_path_validation.py`** — 4 read-only tool modules switch their import from `tools._path_validation` to `security.manager`. The 4 mutating tool modules already use `tools._path_validation` so they switch too.
- **Phase 5 acceptance**: 134-case destructive-command coverage from v4 still passes; SECURITY-related tests in v5 pytest. PS Issue #7 structural fix (per V5_PS_ISSUES_MAPPING.md).
- Resume protocol: see `_status/RESUME.md`.
