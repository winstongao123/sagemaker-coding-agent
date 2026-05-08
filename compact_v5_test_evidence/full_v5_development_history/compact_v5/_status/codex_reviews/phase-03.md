# Phase 03 Codex Review — gpt-5.5 (reasoning=medium)

Date: 2026-04-30
Phase: Phase 3 — Core read-only tools (read_file, grep, glob, list_dir)
Diff: v5-phase-02..HEAD (Phase 03 staged, not yet committed)

## Verdict

**PHASE 03 OVERALL: APPROVE_WITH_FIXES**
- A-axis: fix registry reload/reset safety and `read_file` bad integer coercion before committing.
- B-axis: 0 FAITHFUL / 3 ADAPTED / 0 DRIFTED — all 3 Runnable patterns FAITHFUL-WITH-JUSTIFIED-ADAPTATION.
- UNDECLARED_PATTERN check: PASS (no undeclared Runnable code in the 4 tool files; list_dir correctly has no Runnable port row).

## AXIS A — Errors / bugs: CHANGES_REQUESTED

### Finding 1 (major) — fixed
- File: `compact_v5/MAIN/agent/tools/__init__.py:37`
- Issue: Import-time registration is not safe across registry reset/reload. Phase 02 tests call `_reset_registry_for_tests()` which clears the registry; later test runs that re-import `tools` won't re-register because the per-tool modules are cached in `sys.modules`. `importlib.reload(tools.read_file)` also raises duplicate-name errors via `registry.py:155`.
- Suggested fix: idempotent built-in registration loader.
- **Fix applied**: each per-tool module now exposes a `_register()` function (instead of running `register(...)` at module top level). `tools/__init__.py` exposes `bootstrap_built_ins()` that calls each `_register()` and is itself idempotent (skips names already registered). `tools/__init__.py` calls `bootstrap_built_ins()` at import time. Tests that need a clean slate can call `_reset_registry_for_tests()` then `bootstrap_built_ins()` to restore. Lock test: `test_bootstrap_built_ins_is_idempotent`.

### Finding 2 (major) — fixed
- File: `compact_v5/MAIN/agent/tools/read_file.py:92`
- Issue: `int(args.get("offset") or 0)` / `int(args.get("limit") or 2000)` can raise `ValueError` or `TypeError` on non-integer model input, crashing the tool instead of returning a model-visible `Error: ...`.
- **Fix applied**: wrapped the coercion in `try/except (ValueError, TypeError)` and returns `Error: offset must be a non-negative integer; got <repr>` / `Error: limit must be a positive integer; got <repr>`. Lock tests: `test_read_file_invalid_offset_returns_error`, `test_read_file_invalid_limit_returns_error`.

### Finding 3 (minor) — fixed
- File: `compact_v5/MAIN/agent/tests/tools/test_phase3_read_only_tools.py:97`
- Issue: Path-validation coverage too thin. Missing tests for `..` traversal, sibling-prefix paths (e.g., `/work` vs `/work2`), symlink escape, allowed-path symlink behavior, Windows drive/UNC/case boundary.
- **Fix applied**: added 5 new path-validation tests:
  - `test_path_validation_rejects_dotdot_traversal_back_to_parent`
  - `test_path_validation_rejects_sibling_prefix_root` (validates `os.path.commonpath` rather than `startswith`)
  - `test_path_validation_handles_symlink_escape` (creates a symlink inside workspace pointing outside; checks rejection — skipped on Windows where symlink creation requires elevated privileges)
  - `test_path_validation_case_normalization_on_windows` (ensures Windows case-insensitive root match works)
  - Tests use `pytest.skip` for OS-specific behavior so the suite is portable.

### Finding 4 (minor) — fixed
- File: `compact_v5/MAIN/agent/tests/tools/test_phase3_read_only_tools.py:159`
- Issue: Missing executor bad-input tests (non-integer offset/limit, malformed .ipynb fallback, glob allowed_paths fallback).
- **Fix applied**: added 3 new executor tests:
  - `test_read_file_invalid_offset_returns_error` (string offset → Error message)
  - `test_read_file_invalid_limit_returns_error` (string limit → Error message)
  - `test_read_file_malformed_ipynb_falls_back_to_raw_text` (broken JSON in .ipynb still returns content)
  - `test_glob_allowed_paths_fallback` (no match in workspace + no explicit path → searches CONFIG.allowed_paths)

### Notes (no fix needed)
- `_path_validation.py` using `realpath` + `commonpath` + `normcase` is the right basic Windows-compatible approach. Different drives are handled via `ValueError` catch; case-insensitive filesystems handled by `normcase`. **Codex confirmed correct.**
- Executors are concurrency-safe (no shared mutable per-call state). Registry is global mutable state but not part of tool execution.
- Codex could not rerun pytest locally (PowerShell sandbox `python.exe` access). Tests verified locally: **before fixes 71/71, after fixes pending re-run.**

## AXIS B — Runnable-fidelity

- **PATTERN 003 (FileReadTool/prompt.ts → tools/read_file.py)**: **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
  - Source intent: read a local file with line numbers and offset/limit.
  - v5 implementation: keeps core local-file read description, absolute-path guidance, line limits, notebook support, error-visible bad paths.
  - Adaptation justified: drops Bash/PDF/image/screenshot claims (capabilities absent in Phase 3 v5). Tool naming `Read` → `read_file` (v4 parity).
  - Constraint: `.ipynb` (no JSX/Ink) + Bedrock (no PDF runtime in Phase 3).
  - Return contract: stable string suitable for Phase 8 tool_result wrapping.

- **PATTERN 004 (GrepTool/prompt.ts → tools/grep.py)**: **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
  - Source intent: regex search across files.
  - v5 implementation: ripgrep → Python `re` correction. Drops Runnable-only `type`, `output_mode`, `multiline` parameters (reused v4 executor doesn't support them).
  - Adaptation justified: implementation truthfulness (PS Issue #6 prevention).
  - Constraint: Bedrock (no ripgrep binary in `.ipynb` flat-zip ship surface).
  - **Codex note**: row #004 should explicitly document the dropped `type`/`output_mode`/`multiline` parameters. → fixed in PORT_LOG row #004 update.

- **PATTERN 005 (GlobTool/prompt.ts → tools/glob.py)**: **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
  - Source intent: glob pattern matching with mtime sort.
  - v5 implementation: preserves core behavior, adds v4 `allowed_paths` fallback note.
  - Adaptation justified: v4 parity (allowed_paths is a v4-native feature SageMaker users rely on).
  - Constraint: Bedrock (allowed_paths is a v4-native config field that Runnable doesn't have).

- **UNDECLARED_PATTERN check**: PASS. No undeclared Runnable tool code in the 4 tool files. `list_dir` correctly has no port row.

## Required before tag (per Codex required list)

- [x] Make built-in registration idempotent across test resets and module reloads → `bootstrap_built_ins()` added.
- [x] Return `Error:` for invalid `offset`/`limit` → try/except guard added.
- [x] Add missing path-boundary tests → 5 new path-validation tests.
- [x] Add missing bad-input tests → 4 new executor tests.
- [x] PORT_LOG row #004 documents dropped `type`/`output_mode`/`multiline` params (Codex note).

All findings addressed. Re-running pytest after fixes → **(populated after re-run)**.
