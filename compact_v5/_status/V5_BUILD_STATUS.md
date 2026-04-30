# V5 Build Status

Last updated: 2026-04-30 (Phase 03 DONE)
Updated by: Phase 03 close pass

## Current phase
- Phase ID: 03 (canonical: 00..13 or 08_5)
- Phase name: Phase 3 — Core read-only tools (read_file, grep, glob, list_dir)
- State: DONE
- Started: 2026-04-30
- Target completion: 2026-04-30 (achieved)

## Previous phase
- Phase 02 DONE — tagged v5-phase-02 at 6c7468f, pushed to sageagent. Codex APPROVE_WITH_FIXES, all 4 findings fixed.

## Done in this phase so far
- [x] Read Runnable `src/tools/FileReadTool/prompt.ts`, `GrepTool/prompt.ts`, `GlobTool/prompt.ts` and v4 executors at `compact_v4/MAIN/agent/sagemaker_agent.py:4258` (read_file), `:4846` (glob), `:4897` (grep), `:4952` (list_dir).
- [x] Append **ADR-009**: Phase 3 read-only tools strategy — REUSE v4 executors + ADAPT Runnable prompt text + thin path-validation stub. FAITHFUL-WITH-JUSTIFIED-ADAPTATION (.ipynb / Bedrock).
- [x] Add 3 PORT_LOG rows: #003 (FileReadTool/prompt.ts → read_file.py), #004 (GrepTool/prompt.ts → grep.py with truthfulness correction), #005 (GlobTool/prompt.ts → glob.py with allowed_paths fallback). Verdicts: all 3 FAITHFUL-WITH-JUSTIFIED-ADAPTATION post-fix.
- [x] **NEW per user request 2026-04-30**: created `compact_v5/docs/PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md` and `compact_v5/docs/PS_V5_LEARNINGS_FROM_REPOS.md` — living documents tracking what v5 changes functionally vs v4 + what we learned/adopted from external repos. Phases 0-2 backfilled retroactively + Phase 3 entries. Includes "Better than X" cross-phase tracker.
- [x] Write `compact_v5/MAIN/agent/tools/_path_validation.py` (~80 LOC; Phase-3 stub of v4 SecurityManager.validate_path; Phase 5 retires).
- [x] Write 4 tool modules:
  - `tools/read_file.py` (~190 LOC; v4 executor port + Runnable-adapted prompt + .ipynb cell parsing + large-file guard + idempotent `_register()`).
  - `tools/grep.py` (~135 LOC; v4 executor port + Runnable-adapted prompt with truthfulness correction).
  - `tools/glob.py` (~135 LOC; v4 executor port + Runnable-adapted prompt with allowed_paths fallback).
  - `tools/list_dir.py` (~95 LOC; v4 executor port; no Runnable analog).
- [x] Update `tools/__init__.py` to expose `bootstrap_built_ins()` and call it at import time.
- [x] Write `tests/tools/test_phase3_read_only_tools.py` (originally 28 tests; +8 Codex-fix lock tests = 36 distinct tests, 36 with parametrization expansions plus 1 Windows-symlink skip).
- [x] `pytest tests/` — **79 passed + 1 skipped** (35 prior + 44 Phase 03).
- [x] **Codex review (gpt-5.5, reasoning=medium, via stdin pipe)** — APPROVE_WITH_FIXES with 2 majors + 2 minors. All addressed in same commit:
  - Major #1: bootstrap_built_ins() idempotent registration (per-tool `_register()` functions).
  - Major #2: read_file int coercion → returns `Error:` string instead of crashing.
  - Minor #3: 4 new path-validation tests (.. traversal, sibling-prefix root, symlink escape, Windows case).
  - Minor #4: 4 new bad-input tests (invalid offset/limit, malformed .ipynb fallback, glob allowed_paths fallback).
- [x] All 3 Runnable patterns verified FAITHFUL-WITH-JUSTIFIED-ADAPTATION post-fix. UNDECLARED_PATTERN check PASS.
- [x] PORT_LOG verdicts updated from `(pending Codex)` to actual values.
- [x] Write `MAIN/changelogs/CHANGELOG_v5_phase_03.md` with full Codex review summary + dropped-params note for grep tool.
- [x] `python tests/lint_phase_id.py 03` — pre-commit 4/5 (commit-subject check the only fail, expected pre-commit; will pass post-commit).

## Remaining for this phase
- [ ] git commit + tag `v5-phase-03` + backfill commit sha + push to sageagent.

## Tests status
- Last `pytest` run: 2026-04-30 — **PASS — 79 passed + 1 skipped** (in 0.35s)
  - 2 smoke
  - 11 bedrock (Phase 01)
  - 22 registry (Phase 02)
  - **36 read-only tools (NEW Phase 03)**: 8 metadata, 7 path-validation (incl. 4 new Codex-fix tests), 9 read_file (incl. 3 new bad-input tests), 6 grep, 5 glob (incl. 1 new allowed_paths fallback test), 4 list_dir, 3 registry-level invariants, 1 idempotent bootstrap lock test.
  - 1 skip = Windows symlink-creation test (needs admin elevation; the realpath/commonpath logic is verified functionally on Unix).
- Failing tests: none

## Codex review status (current phase)
- Last review: 2026-04-30 (gpt-5.5, reasoning=medium, via stdin) — **APPROVE_WITH_FIXES**
- Findings: 2 major + 2 minor — all addressed
- Open review comments: 0
- Saved at: `_status/codex_reviews/phase-03.md`

## Git
- Branch: v5-build
- Last commit: <to-be-filled-after-commit> "v5/phase-03: read-only tools + Codex fixes + PS_V5 docs framework"
- Last tag: v5-phase-03

## Blockers
- none

## Next session: pick up at
- **AGGREGATE AUDIT GATE before Phase 04** (per V5_PLAN.md): run audit checks — static prompt token budget, ADR-to-PORT_LOG ratio, per-section token caps. If audit FAIL, block Phase 04.
- **Phase 04 — Core mutating tools + diff_widget.py**: read Runnable `EditTool/UI.tsx`, `WriteTool/UI.tsx`, `NotebookEditTool/UI.tsx` for the diff-preview UX semantics. Port executors from v4 (`tool_write_file`, `tool_edit_file`, `tool_notebook_edit`, `tool_view_image`). Build `ui/diff_widget.py` for inline-colored + click-to-expand diff preview in approval prompt (per V5_PLAN.md Phase 4 acceptance criterion).
- Resume protocol: see `_status/RESUME.md`.
