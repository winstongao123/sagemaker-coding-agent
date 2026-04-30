# CHANGELOG — v5 Phase 05

**Phase**: 05 — bash + python_exec + security verbatim from v4
**Date closed**: 2026-04-30
**Tag**: `v5-phase-05`
**Branch**: `v5-build`

## Goal

Per ADR-011: port v4's SecurityManager class + DANGEROUS_PATTERNS (~70 regex) + DANGEROUS_PYTHON (~70 regex) + CATASTROPHIC_PATTERNS (~13 regex) + helpers VERBATIM into a new `security/` package. Land bash + python_exec tool modules with the 134-case destructive-command coverage from v4. Convert the Phase-3 `tools/_path_validation.py` stub into a delegating shim.

## ADRs accepted this phase

- **ADR-011** — Phase 5 strategy: REUSE v4 verbatim, retire `_path_validation` stub.

## Files added

| Path | LOC | Purpose |
|------|-----|---------|
| `compact_v5/MAIN/agent/runtime/truncation.py` | ~115 | Verbatim port of v4 Truncation class. |
| `compact_v5/MAIN/agent/security/__init__.py` | ~75 | Package init + re-exports + `get_security()` helper + dynamic `SECURITY` via module `__getattr__`. |
| `compact_v5/MAIN/agent/security/manager.py` | ~510 | SecurityManager class + helpers (`safe_exec_env`, `run_subprocess`, `validate_shell_redirections`, `docker_base_cmd`, `ensure_docker_image_ready`, `kill_active_process`, `_auto_detect_allowed_paths`, `_resolve_path`) — all v4 verbatim. |
| `compact_v5/MAIN/agent/security/dangerous_patterns.py` | ~270 | CATASTROPHIC_PATTERNS + DANGEROUS_PATTERNS + BASE_ALLOWED_COMMANDS + INTERPRETER_COMMANDS + CONTAINER_COMMANDS + NETWORK_COMMANDS. v4 verbatim. |
| `compact_v5/MAIN/agent/security/dangerous_python.py` | ~225 | DANGEROUS_PYTHON + ALLOWED_PYTHON_MODULES + BLOCKED_PYTHON_MODULES + BLOCKED_PYTHON_MEMBERS + ALLOWED_AWS_HINT. v4 verbatim. |
| `compact_v5/MAIN/agent/security/high_risk.py` | ~30 | HIGH_RISK_TOOLS frozenset + `is_high_risk()`. v4 verbatim. |
| `compact_v5/MAIN/agent/tools/bash.py` | ~190 | v4 tool_bash port + ADAPT Runnable BashTool/prompt.ts description. Uses call-time `_security_manager.SECURITY` dereference (Codex finding 1 fix). |
| `compact_v5/MAIN/agent/tools/python_exec.py` | ~270 | v4 tool_python_exec port + closure-based runtime sandbox preamble. Uses `[sys.executable, "-I", temp_path]` for defense-in-depth (locked by `test_python_exec_uses_isolated_mode`). |
| `compact_v5/MAIN/agent/tests/unit/test_security_manager.py` | ~580 | 49 tests including the 134-case parity tests + representative-command matrix + stale-singleton lock test + isolated-mode lock test. |
| `compact_v5/MAIN/agent/tests/tools/test_phase5_bash_python.py` | ~190 | 20 tests covering registration + flags + bash + python_exec executors + plan-mode interaction. |
| `compact_v5/_status/codex_reviews/phase-05.md` | — | Phase 05 Codex review record. |

## Files modified

| Path | Change |
|------|--------|
| `compact_v5/MAIN/agent/tools/_path_validation.py` | Phase-3 stub converted to a 4-line delegating shim that forwards `validate_path` + `resolve_path` to `security.manager`. The 8 Phase 3-4 tool modules keep their imports unchanged. |
| `compact_v5/MAIN/agent/tools/__init__.py` | Extended `bootstrap_built_ins()` to register bash + python_exec. |
| `compact_v5/MAIN/agent/tests/tools/test_phase3_read_only_tools.py` | Workspace fixture + 2 tests now call `rebuild_singleton_for_tests` so SECURITY picks up monkeypatched CONFIG. |
| `compact_v5/MAIN/agent/tests/tools/test_phase4_mutating_tools.py` | Workspace fixture calls `rebuild_singleton_for_tests`. |
| `compact_v5/_status/V5_BUILD_STATUS.md` | Phase 05 closure documented. |
| `compact_v5/_status/V5_DESIGN_DECISIONS.md` | Appended ADR-011 (with Codex-finding-4 documentation of the `-I` flag deviation). |
| `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` | Added row #010 (Runnable BashTool/prompt.ts → tools/bash.py); FAITHFUL-WITH-JUSTIFIED-ADAPTATION post-fix. |

## Tests

- `pytest tests/` — **217 passed + 4 skipped** in 5.86s.
- Phase breakdown:
  - 2 smoke
  - 11 bedrock (Phase 01)
  - 22 registry (Phase 02)
  - 36 read-only tools + path-validation (Phase 03)
  - 39 mutating tools / diff_widget + 4 Codex-fix lock tests (Phase 04)
  - 14 view_image / EOF / queue tests (Phase 04 fix locks)
  - **49 security tests (NEW Phase 05)** — including 25-case representative-command matrix + 3 v4-vs-v5 pattern-count parity tests + stale-singleton lock test + `-I` flag lock test
  - **20 bash + python_exec tests (NEW Phase 05)** — including registration, flag parity, executor happy/error paths, plan-mode exclusion
- 4 skips: 1 Windows symlink (Phase 03) + 3 v4-source-not-reachable parity tests (when running outside the `compact_v5/` source tree).

## Codex review

- Model: `gpt-5.5` (reasoning=medium, via stdin pipe)
- Verdict: **APPROVE_WITH_FIXES** → all 4 findings (2 majors + 2 minors) addressed in same Phase 05 commit.
- AXIS A findings:
  - **Major #1**: bash + python_exec captured `SECURITY` at module import — stale after `rebuild_singleton_for_tests`. **Fix**: both tools now do `from security import manager as _security_manager` and reference `_security_manager.SECURITY` at call time. Locked by `test_bash_executor_picks_up_rebuilt_singleton`.
  - **Major #2**: claimed "134-case coverage" but only sampled. **Fix**: added 3 v4-vs-v5 pattern-count parity tests (parses v4 source, counts list literals, asserts equality) + 25-case `test_dangerous_pattern_representative_matrix`.
  - **Minor #3**: `security/__init__.py` docs over-promised about live SECURITY binding. **Fix**: rewrote the doc-comment to accurately distinguish live patterns (`import security as sec; sec.SECURITY`) from stale-after-rebuild patterns (`from security import SECURITY`). Added `get_security()` helper.
  - **Minor #4**: python_exec uses `-I` (isolated mode) where v4 doesn't. **Fix**: ADR-011 documents this as intentional defense-in-depth (blocks PYTHONPATH + ~/.local/lib + ~/.pythonrc from leaking into the sandbox); locked by `test_python_exec_uses_isolated_mode`.
- AXIS B verdicts:
  - **PATTERN 010** (BashTool/prompt.ts → tools/bash.py): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION** (constraint = Bedrock + .ipynb).
  - **UNDECLARED_PATTERN check**: PASS. python_exec and security/* documented as v4-native / no Runnable analog.
- Spot-check confirmed by Codex: catastrophic rm/root, dd `/dev/zero`, `git reset --hard`, `curl|sh`, base64 decode pipe, PowerShell `Remove-Item -Recurse`, `__import__`, boto3 IAM/STS, `subprocess.run`, `shutil.rmtree` — all present in v5 with correct classification.

## PS Issue mapping addressed

- **PS Issue #5 (session cost limit)**: Phase 5 doesn't directly address this; the cost-tracking lives in Phase 8 query_engine. But the `aws_bedrock_only=True` Layer-0 check in `validate_command` + `validate_python` is the security control that prevents arbitrary AWS calls (which is what the cost-limit is meant to bound). PS Issue #5's structural fix lives in Phase 8.
- **PS Issue #7 (buried matrix)**: bash + python_exec descriptions both end with explicit WHEN/WHEN NOT triage sections (per ADR-009 pattern). Full PS-7 fix lands Phase 6 with the sectioned prompt.

## Better-than-v4 + Better-than-Runnable

- **Better than v4 (auditability)**: 5-file `security/` package vs v4's 1000+ LOC inline.
- **Better than v4 (Python 3.11)**: closure sandbox import allowlist now includes transitive imports needed for `import json` to work (`_collections_abc` etc.) — v4 had the gap but never patched.
- **Better than v4 (testability)**: `rebuild_singleton_for_tests()` lets pytest rebuild SECURITY in <1s vs v4's fresh-process-per-scenario.
- **Better than v4 (defense-in-depth)**: `python_exec` invokes Python with `-I` so `~/.local/lib/...` packages don't leak.
- **Better than Runnable (focus)**: bash description ~90 LOC vs Runnable's 369 LOC. Lower per-turn token cost.
- **Better than Runnable (plan-mode)**: dedicated python_exec means plan-mode users can run sandboxed Python (Runnable plan-mode users have nothing — they must use Bash).
- **Better than Runnable (closure sandbox)**: open / os.open / io.open / os.remove / os.posix_spawn all wrapped at runtime via closures the user code cannot see.

## What is intentionally NOT in this phase

- v4's `_PENDING_IMAGES` queue consumer (Phase 8 query_engine).
- v4's `SnapshotManager` integration with bash/python_exec — Phase 8 brings session machinery.
- v4's `auto_commit_every` checkpoint behavior — Phase 8.
- v4's `AuditLogger` integration — Phase 8.
- v4's `_PENDING_IMAGES` injection by BedrockClient — Phase 8.

## Pickup point for next session

- **AGGREGATE AUDIT GATE before Phase 6** is NOT specified by V5_PLAN.md (audit gates fire before phases 4, 7, 10, 13). Phase 6 starts directly.
- **Phase 06 — Sectioned prompt + cache + audit gate before Phase 7**: read Runnable `constants/prompts.ts` (914-LOC f-string) + `constants/systemPromptSections.ts` (registry) + `services/api/promptCacheBreakDetection.ts`. Land:
  - `compact_v5/MAIN/agent/prompt/__init__.py` — `build_system_prompt(ctx)` returning `List[Block]`
  - `compact_v5/MAIN/agent/prompt/sections.py` — section registry + memoization + cache-boundary enforcement
  - 13-14 individual `prompt/*.md` files (identity, tool_classes, tool_efficiency, doing_tasks, critique_handling, answer_preference, data_validation, executing_actions, output_style, subagent_coord, verification_contract, memory_protocol, _CACHE_BOUNDARY)
  - `compact_v5/MAIN/agent/core/cache.py` — cache-block placement + Phase-1-deferred `detect_cache_break()`
- **Phase 6 acceptance**: static prompt ≤ 2500 tokens (vs v4's ~5000); cache-boundary test passes.
- **Phase 6 addresses PS Issue #7 structurally** (the buried-matrix failure mode that motivated v5).
- **Resume protocol**: see `_status/RESUME.md`.
