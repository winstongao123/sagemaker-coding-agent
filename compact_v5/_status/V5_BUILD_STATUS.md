# V5 Build Status

Last updated: 2026-04-30 (Phase 02 DONE)
Updated by: Phase 02 close pass

## Current phase
- Phase ID: 02 (canonical: 00..13 or 08_5)
- Phase name: Phase 2 — Tool Protocol + registry
- State: DONE
- Started: 2026-04-30
- Target completion: 2026-04-30 (achieved)

## Done in this phase so far
- [x] Read Runnable `src/Tool.ts` (`Tool` interface + `buildTool` defaults) and `src/tools.ts` (`getAllBaseTools`, `getTools`, `filterToolsByDenyRules`, `assembleToolPool`, `toolMatchesName`, `findToolByName`)
- [x] Read v4 monolithic `TOOLS` dict at `compact_v4/MAIN/agent/sagemaker_agent.py:7105` and `PLAN_MODE_ALLOWED_TOOLS` set at `:6905`
- [x] Append **ADR-007**: `ToolDef` Python Protocol replaces v4's 4-tuple TOOLS dict (FAITHFUL-WITH-JUSTIFIED-ADAPTATION, constraint=.ipynb)
- [x] Append **ADR-008**: Tool registry exposes `get_tools()` + `assemble_tool_pool()` + `apply_tool_search_deferral()` stub + plan-mode subset (FAITHFUL-WITH-JUSTIFIED-ADAPTATION, constraint=.ipynb)
- [x] Add 2 PORT_LOG rows: #001 (Tool.ts → ToolDef) and #002 (tools.ts → registry.py)
- [x] Write `compact_v5/MAIN/agent/tools/__init__.py` (re-exports)
- [x] Write `compact_v5/MAIN/agent/tools/registry.py` (~290 LOC: ToolDef Protocol + ToolRecord + build_tool + register/unregister/all_registered + tool_matches_name + find_tool_by_name + get_tools + assemble_tool_pool + apply_tool_search_deferral stub + PLAN_MODE_ALLOWED_TOOLS frozenset)
- [x] Write `compact_v5/MAIN/agent/tests/unit/test_registry.py` (22 tests)
- [x] `pytest tests/` — 35/35 PASS (2 smoke + 11 bedrock + 22 registry)
- [x] **Codex review (gpt-5.5, reasoning=medium)** — APPROVE_WITH_FIXES, all 4 findings addressed in same phase before tagging:
  - Major: `assemble_tool_pool(plan_mode=True)` was leaving MCP tools visible — FIXED (now applies PLAN_MODE_ALLOWED_TOOLS to MCP tools too, locked by `test_plan_mode_filters_mcp_tools_too`)
  - Major: deny-rules didn't support Runnable's MCP server-prefix form (`mcp__server` and `mcp__server__*`) — FIXED (locked by 3 new tests including no-partial-match guard)
  - Minor: V5_BUILD_STATUS.md was stale — FIXED in this rewrite
  - Nit: unused `field` import — FIXED
- [x] AXIS B verdicts after fixes: PATTERN 001 FAITHFUL-WITH-JUSTIFIED-ADAPTATION; PATTERN 002 FAITHFUL-WITH-JUSTIFIED-ADAPTATION (initial verdict was DRIFTED, fixed in same commit). UNDECLARED_PATTERN check PASS.
- [x] PORT_LOG verdicts updated from `(pending Codex)` to actual values
- [x] `python tests/lint_phase_id.py 02` — pre-commit 4/5 (commit-subject check the only fail, expected pre-commit)
- [x] Investigated and resolved Codex hang: long prompt (~5000 chars) exceeded Windows CMD argument limit, codex silently fell back to "Reading additional input from stdin..." and waited forever. Fix: pipe prompt via stdin instead of `"$(cat ...)"` argument.
- [x] Write `MAIN/changelogs/CHANGELOG_v5_phase_02.md`
- [x] git commit (subject: `v5/phase-02: tool protocol + registry + Codex fixes`)
- [x] git tag `v5-phase-02`

## Remaining for this phase
- [ ] (none — Phase 02 done)

## Tests status
- Last `pytest` run: 2026-04-30 — **PASS — 35/35** (`tests/test_smoke.py` 2/2 + `tests/unit/test_bedrock.py` 11/11 + `tests/unit/test_registry.py` 22/22)
- Failing tests: none

## Codex review status (current phase)
- Last review: 2026-04-30 (gpt-5.5, reasoning=medium) — **APPROVE_WITH_FIXES**
- Findings: 2 major + 1 minor + 1 nit — all addressed
- Open review comments: 0
- Saved at: `_status/codex_reviews/phase-02.md`

## Git
- Branch: v5-build
- Last commit: <to-be-filled-after-commit> "v5/phase-02: tool protocol + registry + Codex fixes"
- Last tag: v5-phase-02

## Blockers
- none

## Next session: pick up at
- **Start Phase 03 — Core read-only tools.** Read Runnable `src/tools/FileReadTool/` + `GrepTool/` + `GlobTool/` + (no v5 list_dir analog in Runnable; reuse v4 directly). Per ADR-001 (file-per-tool layout) write each tool as its own module: `tools/read_file.py`, `tools/grep.py`, `tools/glob.py`, `tools/list_dir.py`. Each calls `register(build_tool(...))` at import time. Update `tools/__init__.py` to import the new modules. Add `tests/tools/test_*.py` per tool. **AGGREGATE AUDIT GATE BEFORE PHASE 4** — run audit checks (token budget, ADR-to-port-log ratio, cognitive load) before starting Phase 4.
- Resume protocol: see `_status/RESUME.md`.
