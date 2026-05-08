# CHANGELOG — v5 Phase 04

**Phase**: 04 — Core mutating tools (write_file, edit_file, notebook_edit, view_image) + ui/diff_widget.py
**Date closed**: 2026-04-30
**Tag**: `v5-phase-04`
**Branch**: `v5-build`

## Goal

Per ADR-001 (file-per-tool layout) + ADR-010 (Phase 4 strategy):
- Land 4 mutating tools as separate Python modules under `compact_v5/MAIN/agent/tools/`.
- REUSE v4 executors (battle-tested with security validation, atomic writes, stale-checks) — ADAPT Runnable prompt text.
- Land `ui/diff_widget.py` for colored inline + click-to-expand diff in approval prompts (V5_PLAN.md Phase 4 acceptance criterion).
- Ship a thin `tools/_file_read_tracking.py` stub that Phase 8 retires when query_engine session state arrives.

## Aggregate audit gate (pre-Phase-04, 2026-04-30)

Verdict: **PASS**.
- ADR-to-PORT_LOG ratio: PASS (5/5 PORT_LOG rows reference an ADR)
- 9 ADRs accepted (001-009)
- Tool count: v5 has 4 tools, v4 has 30 — under ceiling
- Static prompt tokens / per-turn schema overhead: deferred to Phase 6/7 baselines.

## ADRs accepted this phase

- **ADR-010** — Phase 4 mutating tools: REUSE v4 executors + ADAPT Runnable prompts + diff_widget UI. FAITHFUL-WITH-JUSTIFIED-ADAPTATION (constraint = .ipynb / Bedrock / python_exec).

## Files added

| Path | LOC | Purpose |
|------|-----|---------|
| `compact_v5/MAIN/agent/tools/_file_read_tracking.py` | ~80 | Phase-4 stub of v4 _FILES_READ + _FILE_READ_TIMES; threadsafe; Phase 8 retires when query_engine session state arrives. |
| `compact_v5/MAIN/agent/tools/write_file.py` | ~125 | v4 executor port + Runnable prompt; requires read-before-overwrite; mode=write|append. Registers `write_file`. |
| `compact_v5/MAIN/agent/tools/edit_file.py` | ~165 | v4 executor port + Runnable prompt; exact-match enforcement; replace_all; stale-check. Registers `edit_file`. |
| `compact_v5/MAIN/agent/tools/notebook_edit.py` | ~205 | v4 executor port + Runnable prompt; insert/replace/delete; atomic write. Registers `notebook_edit`. |
| `compact_v5/MAIN/agent/tools/view_image.py` | ~125 | v4 executor port; validates path/size/format. No Runnable analog. Registers `view_image`. |
| `compact_v5/MAIN/agent/ui/diff_widget.py` | ~225 | HTML colored diff (red removed / green added / gray context, file path header, ±3 lines, click-to-expand `<details>`). Stdlib only (`difflib` + `html.escape`). |
| `compact_v5/MAIN/agent/tests/tools/test_phase4_mutating_tools.py` | ~440 | 31 distinct tests covering registration + flags + per-tool happy/error paths + read-before-mutate enforcement + stale-check + atomic-write + plan-mode interaction. |
| `compact_v5/MAIN/agent/tests/unit/test_diff_widget.py` | ~120 | 8 tests covering HTML rendering + escape + expandable + new-file. |
| `compact_v5/_status/codex_reviews/phase-04.md` | — | Phase 04 Codex review record. |

## Files modified

| Path | Change |
|------|--------|
| `compact_v5/MAIN/agent/tools/__init__.py` | Added 4 imports + `bootstrap_built_ins()` extension. |
| `compact_v5/_status/V5_BUILD_STATUS.md` | Phase 04 closure documented. |
| `compact_v5/_status/V5_DESIGN_DECISIONS.md` | Appended ADR-010. |
| `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` | Added rows #006-009. |
| `compact_v5/docs/PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md` | Phase 4 entries (7 items). |
| `compact_v5/docs/PS_V5_LEARNINGS_FROM_REPOS.md` | Phase 4 entries + "Better than X" tracker rows. |

## Tests

- `pytest tests/` — **128 passed + 1 skipped** in 1.63s (post-Codex-fix). Phase breakdown: 35 prior + 39 initial Phase 04 + 4 new Codex-fix lock tests; 1 skip is the pre-existing Windows-symlink test.
  - 2 smoke
  - 11 bedrock (Phase 01)
  - 22 registry (Phase 02)
  - 36 read-only tools + path-validation (Phase 03 incl. Codex-fix lock tests)
  - **31 Phase 04 mutating tools (NEW)**:
    - 4 registration tests (parametrized over 4 tools)
    - 1 mutating-flag check + 1 view_image-flag check
    - 8 write_file tests
    - 9 edit_file tests (incl. stale-check, replace_all, identical-string rejection)
    - 8 notebook_edit tests (incl. atomic-write contract)
    - 4 view_image tests
    - 2 plan-mode interaction tests (mutators excluded, view_image included)
  - **8 Phase 04 diff_widget tests (NEW)**: rendering + HTML-escape security + expandable wrapper + new-file + line-numbers + context-width.

## Codex review

- Model: `gpt-5.5` (reasoning=medium, via stdin pipe)
- Verdict: **APPROVE_WITH_FIXES** → all 5 findings (1 major + 2 minor + 2 nits) addressed in the same Phase 04 commit before tagging.
- AXIS A findings:
  - **Major #1**: notebook_edit only caught `OSError` around `_atomic_write_json`; non-OSError failures (e.g., serialization) escaped as raw exceptions. **Fix**: catch `Exception as e` matching v4 (sagemaker_agent.py:6024). Locked by `test_notebook_edit_handles_non_oserror_write_failure` (mocks `json.dump` to raise TypeError).
  - **Minor #2**: `view_image` computed base64 but had no side channel to hand off to Phase 8. **Fix**: added `_PENDING_IMAGES` queue + `pop_pending_images()` accessor (mirrors v4 `_PENDING_IMAGES` at sagemaker_agent.py:6456). Locked by `test_view_image_queues_payload_for_phase_8`.
  - **Minor #3**: `diff_widget.render_inline_diff` used `splitlines()` which strips trailing newlines; an EOF-newline-only change rendered as "No changes". **Fix**: explicit before/after `endswith("\n")` comparison surfaces the EOF-newline change. Locked by `test_inline_diff_shows_eof_newline_difference`.
  - **Nit #4**: stale-check in `_file_read_tracking.is_stale` used `abs(current - last) > 0.5` (bidirectional). v4 uses directional `current > last + 0.5` (sagemaker_agent.py:4189) so a `git checkout` to an older mtime doesn't falsely trigger. **Fix**: matched v4 directional semantics.
  - **Nit #5**: missing tests for malformed `@@` hunk headers + EOF-newline visibility + non-OSError notebook write. **Fix**: 3 new lock tests.
- AXIS B verdicts:
  - **PATTERN 006** (FileWriteTool/prompt.ts → write_file.py): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
  - **PATTERN 007** (FileEditTool/prompt.ts → edit_file.py): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
  - **PATTERN 008** (NotebookEditTool/prompt.ts → notebook_edit.py): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
  - **PATTERN 009** (FileEditTool/UI.tsx → diff_widget.py): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
  - **UNDECLARED_PATTERN check**: PASS. view_image correctly declares no Runnable analog.

Tests after fixes: **128 passed + 1 skipped** (the 1 skip is the Windows-symlink test from Phase 03).

## PS Issue mapping

- (No new PS Issues addressed in Phase 4 directly — Phase 4 supports the Phase 6 prompt-section work + the Phase 8 query_engine work.)
- The diff-widget approval-prompt UX prevents a class of "silent misplaced edit" failures that PS_actual_use_problems.md captured anecdotally; while not formally one of the 7 PS issues, it's a v5 improvement over v4.

## Phase-N deferred features (documented inline; reconciliation in target phase ADRs)

- **write_file**: SECURITY.scan_secrets (Phase 5), SnapshotManager.save (Phase 8), auto-lint Python (Phase 8), auto-commit checkpoint (Phase 8), `_RECENT_DIFFS` recording (Phase 8).
- **edit_file**: SnapshotManager.save (Phase 8), auto-lint Python (Phase 8), auto-commit checkpoint (Phase 8), post-edit `git diff` summary (Phase 8), `_RECENT_DIFFS` recording (Phase 8).
- **view_image**: `_PENDING_IMAGES` queue injection into next API turn (Phase 8 query_engine builds the Bedrock content block).
- **path validation + read tracking**: stubs in `tools/_path_validation.py` and `tools/_file_read_tracking.py`; Phase 5 + Phase 8 ADRs reconcile and replace.

## Pickup point for next session

- **Phase 05 — bash + python_exec + security verbatim from v4**: this is the security port. Read v4's `SecurityManager` class + `DANGEROUS_PATTERNS` + `DANGEROUS_PYTHON` + `HIGH_RISK_TOOLS` (134-case destructive command coverage). Land:
  - `compact_v5/MAIN/agent/security/__init__.py`
  - `compact_v5/MAIN/agent/security/manager.py` (port verbatim from v4)
  - `compact_v5/MAIN/agent/security/dangerous_patterns.py`
  - `compact_v5/MAIN/agent/security/dangerous_python.py`
  - `compact_v5/MAIN/agent/security/high_risk.py`
  - `compact_v5/MAIN/agent/tools/bash.py`
  - `compact_v5/MAIN/agent/tools/python_exec.py`
- **Phase 5 retires**: `tools/_path_validation.py` stub (replaced by `security.manager.validate_path`).
- **Phase 5 acceptance**: 134-case destructive-command coverage from v4 still passes; SECURITY-related tests in v5 pytest.
- Resume protocol: `_status/RESUME.md`.
