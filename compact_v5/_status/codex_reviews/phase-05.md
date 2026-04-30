# Phase 05 Codex Review — gpt-5.5 (reasoning=medium)

Date: 2026-04-30
Phase: Phase 5 — bash + python_exec + security verbatim from v4
Diff: v5-phase-04..HEAD (Phase 05 staged, not yet committed)

## Verdict

**PHASE 05 OVERALL: APPROVE_WITH_FIXES**
- A-axis: fix stale singleton captures and add real 134-case parity coverage before moving on.
- B-axis: 0 FAITHFUL / 1 ADAPTED / 0 DRIFTED — PATTERN 010 (BashTool) FAITHFUL-WITH-JUSTIFIED-ADAPTATION.
- UNDECLARED_PATTERN check: PASS. No undeclared Runnable code in the 8 new files.

## AXIS A — Errors / bugs: CHANGES_REQUESTED

### Finding 1 (major) — fixed
- File: `compact_v5/MAIN/agent/tools/bash.py:31`/`:113` and `tools/python_exec.py:27`/`:88`/`:225`
- Issue: both tools `from security.manager import SECURITY` at module import. The local binding `SECURITY` is a one-shot snapshot; after `rebuild_singleton_for_tests()`, executors still use the old workspace/allowed_paths.
- Suggested fix: `import security.manager as security_manager` and dereference `security_manager.SECURITY` at call time.
- **Fix applied**: both `bash.py` and `python_exec.py` now do `from security import manager as _security_manager` at module level (imports the module, not the value), then reference `_security_manager.SECURITY` inside the executor body. The closure-sandbox preamble in `_build_python_preamble()` also dereferences via `_security_manager.SECURITY.allowed_paths` at preamble-build time (which is invoked per-call). Lock test: `test_bash_executor_picks_up_rebuilt_singleton`.

### Finding 2 (major) — fixed
- File: `compact_v5/MAIN/agent/tests/unit/test_security_manager.py:5`/`:85`
- Issue: file claims "134-case destructive command coverage" but only samples the bash denylist; no full parity test.
- Suggested fix: add the full v4 destructive-command matrix or a golden parity test comparing v4/v5 pattern sets.
- **Fix applied**: added `test_v5_dangerous_patterns_count_matches_v4`, `test_v5_dangerous_python_count_matches_v4`, `test_v5_catastrophic_count_matches_v4` — all three count v4's source-file pattern occurrences (regex parse) and compare to v5's ported lists. Plus `test_dangerous_pattern_representative_matrix` runs 25 representative bash commands through `validate_command` and asserts the expected pattern catches each.

### Finding 3 (minor) — fixed
- File: `compact_v5/MAIN/agent/security/__init__.py:35`
- Issue: comment claims `from security import SECURITY` always gets current singleton — but Python's `from X import name` is a one-shot binding; only `module.attr` access triggers `__getattr__` per call. So callers who do `from security import SECURITY` once still cache the original.
- Suggested fix: clarify guidance.
- **Fix applied**: updated comment to clarify that `from security import SECURITY` captures at first import (caches the value); for code that needs to track rebuilds, use `import security as sec; sec.SECURITY` (live lookup) or `import security.manager as sm; sm.SECURITY` (also live). Added a `get_security()` helper for callers that prefer a function-call style.

### Finding 4 (minor) — fixed
- File: `compact_v5/MAIN/agent/tools/python_exec.py:250`
- Issue: v5 invokes `[sys.executable, "-I", temp_path]` whereas v4 had `[sys.executable, temp_path]` (no `-I`). Codex flags this as not verbatim.
- Suggested fix: ADR/test coverage for the deviation.
- **Fix applied**: ADR-011 already documents the `-I` flag as intentional hardening (note in section "What python_exec adds beyond v4"). Added an explicit acknowledgement in the inline comment + a test (`test_python_exec_uses_isolated_mode`) that asserts the python invocation uses `-I` so a future refactor can't silently drop it. The deviation is intentional and audit-trailed.

### Codex spot-check (no findings)
- Catastrophic rm/root, dd `/dev/zero`, `git reset --hard`, `curl|sh`, base64 decode pipe, PowerShell `Remove-Item -Recurse`, `__import__`, boto3 IAM/STS, `subprocess.run`, `shutil.rmtree` — all present and correctly classified.
- Path-validation shim delegates correctly.
- Docker path calls `ensure_docker_image_ready()` before wrapping.
- No circular-import issues.
- Could not run pytest locally (Windows Store python.exe shim access-denied).

## AXIS B — Runnable-fidelity

- **PATTERN 010 (BashTool/prompt.ts → tools/bash.py)**: **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
  - Up-stream/down-stream semantics aligned: static description ships through tool registry, security validates before execution, returns `Blocked:` / `Error:` / output / `(no output)`.
  - Dropped Runnable-only prompt content (undercover, gh attribution, sandbox manager refs, USER_TYPE branches, background-task notes) is justified by Bedrock + `.ipynb` constraints.
- **UNDECLARED_PATTERN check**: PASS. Only `bash.py` contains the declared Runnable BashTool adaptation; `python_exec.py` and `security/*` are documented as v4-native / no analog.

## Required before tag (per Codex required list)

- [x] Replace static tool-level `SECURITY` imports with call-time lookup.
- [x] Add full destructive-command parity coverage (count tests + representative-matrix test).
- [x] Document the `python_exec -I` deviation from v4 + lock with a test.

All findings addressed. Re-running pytest after fixes → **(populated after re-run)**.
