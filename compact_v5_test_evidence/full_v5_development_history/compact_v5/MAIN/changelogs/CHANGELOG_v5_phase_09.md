# V5 Phase 9 Changelog — Sub-agent + Task tool (forkSubagent budget sharing)

Date: 2026-04-30
Tag (target): v5-phase-09
ADR: ADR-015
PORT_LOG rows: #021, #022, #023, #024

## Goal (V5_PLAN.md §Phase 9)

Port `forkSubagent` budget-sharing pattern; reuse v4 handoff blocks. Acceptance:
- Parent context unchanged after sub-agent run.
- Child shares IterationBudget instance (object identity).

## What landed

### subagent/env.py (PORT_LOG #022 — PORT, FAITHFUL)
Verbatim port of v4's `_build_subagent_env_details` (sagemaker_agent.py:7695).
Workspace + max_depth become function parameters. Fail-quiet git probes
(5.0s timeout matching v4). ≤6 lines (Haiku 4.5 budget).

### subagent/handoff.py (PORT_LOG #023 — ADAPT, FAITHFUL-WITH-JUSTIFIED-ADAPTATION)
ADAPT port of v4's `_build_subagent_handoff_block`. Inputs as parameters
instead of globals (v5 callers in Phase 11 will wire them). Same caps
(4000 chars status / 2000 chars todos / 10 most-recent files), same
cache-boundary marker sanitization, same fail-quiet contract.

### subagent/spawn.py (PORT_LOG #021 — ADAPT, FAITHFUL post-fix)
Sync ADAPT port of Runnable's `forkSubagent.ts`. Drops experimental fork
branch, cache-prefix-identical message replay, `<task-notification>`
background dispatch, coordinator-mode mutual exclusion. Keeps:
- Shared-budget contract (`child.budget is parent.budget`).
- Depth-limit gate with proper threading via `child._subagent_depth`.
- Empty-prompt rejection.
- Deep-copy parent immutability guard.
- Unknown agent-type explicit-error contract.

### tools/task.py (PORT_LOG #024 — ADAPT, FAITHFUL-WITH-JUSTIFIED-ADAPTATION)
Task tool registration + executor. Phase-9 minimal scope: `general`
only. Marked `should_defer=True` (low-frequency; loaded via tool_search).
Requires `context['parent_engine']` from QueryEngine dispatch.

### Tests (44 new)
- `tests/unit/test_subagent_env.py` (5 tests)
- `tests/unit/test_subagent_handoff.py` (9 tests)
- `tests/integration/test_subagent.py` (15 tests, including 5 Codex-fix
  lock tests)
- 1 Codex-fix line added to `tests/integration/test_query_engine.py`
  (`task` exclusion in deferred-tools test).

## Test results

- Last full `pytest` run (post Codex fixes): 2026-04-30 — **359 passed + 4
  skipped** (was 329+4 in Phase 8.5; +30 net new tests).
- Aggregate audit: all 7 metrics PASS.

## Codex review

- First pass: REJECT. 1 BLOCKER + 3 substantive + 1 low + 1 DRIFTED + 1
  UNDECLARED_PATTERN.
  - **HIGH/BLOCKER**: depth not threaded (`_subagent_depth` never set).
  - **medium**: parent immutability check too weak (length-only).
  - **medium**: silent fallback for unknown subagent_type.
  - **medium** (test gap): no real-spawn budget-identity test.
  - **low** (test gap): `task` exclusion not asserted.
  - **DRIFTED**: env.py git timeout 5s→2s without justification.
  - **UNDECLARED_PATTERN**: depth plumbing not documented.
- All 7 addressed in same commit:
  - `subagent/spawn.py`: `child._subagent_depth = child_depth`; deep-copy
    immutability guard; unknown-type explicit error.
  - `subagent/env.py`: `_GIT_TIMEOUT_S` restored to 5.0s.
  - `tools/task.py`: unknown subagent_type rejected with explicit error.
  - 5 new lock tests + 1 assertion added to existing test.
  - PORT_LOG verdicts upgraded post-fix.
- Post-fix: AXIS A PASS, AXIS B 2 FAITHFUL / 2 ADAPTED / 0 DRIFTED.
- Saved at: `_status/codex_reviews/phase-09.md`.

## Better than v4

- v4's _run_task_tool is ~600 LOC inline in the monolith and not testable
  in isolation. v5 splits into 4 modules (env / handoff / spawn / task)
  each independently testable.
- v4 silently truncates handoff blocks; v5 sanitizes cache-boundary
  markers in handoff content (defense against AGENT_STATUS containing
  `# === DYNAMIC ===` literally).
- v5's deep-copy parent immutability guard catches in-place mutations
  that v4's check (length-only equivalent in spirit) would miss.

## Better than Runnable

- v5 spawn is sync (constraint=.ipynb), with explicit IN-SCOPE / OUT-OF-SCOPE
  documented. Runnable's forkSubagent ships an experimental feature gate +
  cache-prefix replay + background `<task-notification>` model that needs
  streaming/async to be useful.
- v5 enforces shared-budget invariant via Phase-9 acceptance tests
  (`is parent.budget` object identity). Runnable doesn't lock this contract
  with a test of equivalent strength.

## Next phase

Phase 10 — Skills + auto-trigger + Hermes filter (PS Issue #1). Port v4's
SkillManager + 10 skills directories byte-for-byte. Add Hermes-style skill
filtering by available tools. Aggregate audit gate before Phase 11.
