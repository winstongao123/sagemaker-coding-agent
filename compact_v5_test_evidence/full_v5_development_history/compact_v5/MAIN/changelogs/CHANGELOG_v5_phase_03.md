# CHANGELOG — v5 Phase 03

**Phase**: 03 — Core read-only tools (read_file, grep, glob, list_dir)
**Date closed**: 2026-04-30
**Tag**: `v5-phase-03`
**Branch**: `v5-build`

## Goal

Per ADR-001 (file-per-tool layout) + ADR-009 (this-phase strategy):
- Land 4 read-only tools as separate Python modules under `compact_v5/MAIN/agent/tools/`.
- Each tool calls `register(build_tool(...))` at import time.
- **REUSE v4 executors** (battle-tested Python with security validation, .ipynb cell parsing, large-file guard, binary-file skip, allowed_paths fallback) — **ADAPT Runnable prompt text** (Runnable's WHEN/WHEN NOT structure addresses PS Issue #7 buried-matrix).
- Ship a thin `tools/_path_validation.py` stub that Phase 5 retires when the full v4 SecurityManager port lands.

## ADRs accepted this phase

- **ADR-009** — Phase 3 read-only tools: REUSE v4 executors + ADAPT Runnable prompt text + thin path-validation stub. FAITHFUL-WITH-JUSTIFIED-ADAPTATION (constraint = .ipynb / Bedrock / python_exec).

## Files added

| Path | LOC | Purpose |
|------|-----|---------|
| `compact_v5/MAIN/agent/tools/_path_validation.py` | ~80 | Phase-3 stub of v4 SecurityManager.validate_path. Workspace boundary + symlink escape detection. Phase 5 replaces. |
| `compact_v5/MAIN/agent/tools/read_file.py` | ~170 | v4 executor port + Runnable-adapted prompt. Includes large-file guard + .ipynb cell parsing. Registers `read_file`. |
| `compact_v5/MAIN/agent/tools/grep.py` | ~115 | v4 executor port + Runnable-adapted prompt with **truthfulness correction** (regex not ripgrep). Registers `grep`. |
| `compact_v5/MAIN/agent/tools/glob.py` | ~115 | v4 executor port + Runnable-adapted prompt with v4-specific allowed_paths fallback note. Registers `glob`. |
| `compact_v5/MAIN/agent/tools/list_dir.py` | ~75 | v4 executor port. No Runnable analog (plan-mode users need it because bash is forbidden). Registers `list_dir`. |
| `compact_v5/MAIN/agent/tests/tools/test_phase3_read_only_tools.py` | ~360 | 36 tests (28 distinct + parametrized expansions): registration, metadata flags, plan-mode allowlist membership, path-validation stub, per-tool behavior + boundary checks, registry-level invariants. |
| `compact_v5/docs/PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md` | (NEW user-requested doc) | Living document tracking what v5 changes functionally vs v4.10.10. Phase 0-2 retroactive entries + Phase 3 entries. |
| `compact_v5/docs/PS_V5_LEARNINGS_FROM_REPOS.md` | (NEW user-requested doc) | Living document tracking what we learned + adopted from Runnable / Hermes / LF. Phase 0-2 retroactive entries + Phase 3 entries. Includes "Better than X" cross-phase tracker. |
| `compact_v5/_status/codex_reviews/phase-03.md` | — | Phase 03 Codex review record. |

## Files modified

| Path | Change |
|------|--------|
| `compact_v5/MAIN/agent/tools/__init__.py` | Added 4 import lines that fire registration for the new tool modules. |
| `compact_v5/_status/V5_BUILD_STATUS.md` | Phase 03 closure documented. |
| `compact_v5/_status/V5_DESIGN_DECISIONS.md` | Appended ADR-009. |
| `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` | Added rows #003 (FileReadTool/prompt.ts), #004 (GrepTool/prompt.ts), #005 (GlobTool/prompt.ts) — Codex verdicts after review. |
| `SESSION_STATE.md` | Phase 03 close section. |

## Tests

- `pytest tests/` — **79 passed + 1 skipped** in 0.35s (35 prior phases + 36 initial Phase 03 + 8 new Codex-fix lock tests; 1 skip is the Windows-symlink test that needs admin to create symlinks).
  - 2 smoke
  - 11 bedrock (Phase 01)
  - 22 registry (Phase 02)
  - **36 read-only tools (NEW Phase 03)**:
    - 4 registration + parametrized (4 tools × is_read_only/is_concurrency_safe/requires_approval flag check + plan-mode-membership check) = 8 metadata tests
    - 3 path-validation stub tests (reject outside workspace, accept inside, accept allowed_paths)
    - 7 read_file tests (happy path, missing file, outside workspace, offset/limit, large-file guard, .ipynb cell parsing, directory rejection)
    - 6 grep tests (matches, no-match message, invalid regex, binary-skip, outside workspace, case-insensitive)
    - 4 glob tests (matches, no-match, outside workspace, recursive)
    - 4 list_dir tests (workspace listing, non-directory error, outside workspace, empty directory)
    - 3 registry-level invariants (assemble_tool_pool includes Phase-3 tools, plan-mode pool includes them, alphabetical ordering)

## Codex review

- Model: `gpt-5.5` (reasoning=medium, via stdin pipe per Phase 02 fix — long Phase-03 prompt was 6000 chars, would have hung if passed as cmdline arg)
- Verdict: **APPROVE_WITH_FIXES** → all 4 findings landed in same Phase 03 commit before tagging.
- AXIS A findings (4): all addressed
  - **Major #1**: import-time registration unsafe across `_reset_registry_for_tests()` + reimport. Per-tool modules cached in `sys.modules` won't re-register. **Fix**: each per-tool module exposes `_register()`; `tools.bootstrap_built_ins()` calls them and is idempotent (skips already-registered names). Locked by `test_bootstrap_built_ins_is_idempotent`.
  - **Major #2**: `read_file.py` int coercion crashed on non-integer model input. **Fix**: try/except around `int()` calls, returns `Error: ...` string for invalid offset/limit. Locked by `test_read_file_invalid_offset_returns_error` + `test_read_file_invalid_limit_returns_error`.
  - **Minor #3**: path-validation tests too thin. **Fix**: 4 new tests (`..` traversal, sibling-prefix root, symlink escape on Unix, Windows case normalization).
  - **Minor #4**: missing bad-input executor tests. **Fix**: 4 new tests (invalid offset, invalid limit, malformed .ipynb fallback, glob allowed_paths fallback).
- AXIS B verdicts:
  - **PATTERN 003** (FileReadTool/prompt.ts → tools/read_file.py): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**. constraint=.ipynb. Drops Bash/PDF/image/screenshot claims (capabilities absent in v5).
  - **PATTERN 004** (GrepTool/prompt.ts → tools/grep.py): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**. constraint=Bedrock. Truthful "regex search" instead of Runnable's "ripgrep". Dropped `type` / `output_mode` / `multiline` parameters that the reused v4 executor doesn't implement (PORT_LOG row #004 documents this explicitly per Codex note).
  - **PATTERN 005** (GlobTool/prompt.ts → tools/glob.py): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**. constraint=Bedrock. Adds v4-native allowed_paths fallback note.
  - **UNDECLARED_PATTERN check**: PASS. No undeclared Runnable code in the 4 tool files. `list_dir` correctly has no port row.

## Codex telemetry note (already documented in CHANGELOG_v5_phase_02.md)

- The `failed to record rollout items: thread <id> not found` error and the SQLite `migration 21` warning continue to appear in codex stderr. They are cosmetic — the API response still arrives. No action.

## PS Issue mapping addressed

- **PS Issue #6 (wiring-bug pattern: prompt claims a backend the executor doesn't have)**: grep prompt explicitly says "regex search" / "Python re semantics" instead of Runnable's "built on ripgrep". v5 prompt now matches the implementation.
- **PS Issue #7 (buried-matrix failure mode)**: every read-only tool description ends with explicit WHEN / WHEN NOT sections — adopted from Runnable's prompt structure. Helps the model triage which tool to use under cognitive load. (Full PS #7 fix lands Phase 6 with the sectioned prompt — Phase 3 contributes the per-tool description shape.)

## What is intentionally NOT in this phase

- `view_image` tool — Phase 4 (groups with mutating tools / file UI).
- `semantic_search` tool — Phase 10 (groups with skills).
- `web_fetch`, `ask_user`, `todo_*` tools — Phase 10 (skills + UX integration).
- Full `SecurityManager` port — Phase 5 (replaces `tools/_path_validation.py`).
- Phase-8 globals (FILE_CACHE, _FILES_READ, FILE_UNCHANGED_STUB, _FILE_PARTIAL_READS) — Phase 8 (`core/query_engine.py`).

## Pickup point for next session

- **AGGREGATE AUDIT GATE before Phase 04** — must run `tests/aggregate_audit.py` (when Phase 6 lands; for now manual): static prompt token budget, ADR-to-PORT_LOG ratio (every PORT_LOG row has matching ADR), per-section token caps. If audit FAIL → block Phase 4.
- **Phase 04 — Core mutating tools + diff_widget.py**: read Runnable `EditTool/UI.tsx`, `WriteTool/UI.tsx`, `NotebookEditTool/UI.tsx` for the diff-preview UX semantics. Port executors from v4 (`tool_write_file`, `tool_edit_file`, `tool_notebook_edit`, `tool_view_image`). Build `ui/diff_widget.py` for inline-colored + click-to-expand diff preview in approval prompt (per V5_PLAN.md Phase 4 acceptance criterion).

Resume protocol: `_status/RESUME.md`.
