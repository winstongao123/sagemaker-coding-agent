# V5 Phase 8 Changelog — QueryEngine + retry + errors + IterationBudget

Date: 2026-04-30
Tag (target): v5-phase-08
ADR: ADR-014
PORT_LOG rows: #016, #017, #018, #019

## Goal

Land the main agent loop. Phase 8 delivers the four core/ modules called out
in V5_PLAN.md:

- `core/query_engine.py` — main loop (Runnable QueryEngine.ts adaptation)
- `core/retry.py` — jittered exponential backoff (extracted from Phase 1)
- `core/errors.py` — Bedrock error classifier (extracted from Phase 1)
- `core/budget.py` — IterationBudget (Hermes pattern via v4)

Acceptance (V5_PLAN.md §Phase 8): "end-to-end mock test (tool_use → tool runs
→ final answer) AND tool_search deferred-loading round-trip works."

## What landed

### core/budget.py (PORT_LOG #016)

Verbatim port of v4's `IterationBudget`. Thread-safe shared counter across
parent + sub-agents. DEFAULT_MAX=600 iterations. `consume()` returns False
when exhausted; `remaining()/used()/total()` for UI surfacing (Phase 11
ipywidgets progress bar — addresses PS Issue #2).

### core/errors.py (PORT_LOG #017)

Extracted Phase-1 inline `BedrockErrorCategory` + `ErrorClassifier` from
`runtime/bedrock_client.py`. Byte-equivalent classification semantics. The
Phase-1 module re-imports both names so existing call-sites and tests
work unchanged (lock test `test_runtime_bedrock_client_re_exports_match`
asserts class identity).

### core/retry.py (PORT_LOG #018)

Extracted Phase-1 inline `RetryPolicy`. v4's MAX_RETRIES=4 + ~1s/2s/4s/8s
sleep curve + 30% jitter retained verbatim. ADAPT verdict because Runnable's
`withRetry.ts` retry-after header parsing is dropped (v5 doesn't expose
retry-after through the Bedrock client wrapper).

### core/query_engine.py (PORT_LOG #019)

Minimal Phase-8 port of Runnable's `QueryEngine.ts` (1295 LOC) — v5 lands
~400 LOC. Owns the message buffer + IterationBudget for one `run()` call.

Per-turn responsibilities:
1. Stop-check + budget gate.
2. **Phase 7 wiring contract** (the headline feature):
   - `apply_tool_search_deferral(tools, enabled=True)` per turn → returns
     `(visible_tools, deferred_names)`.
   - For each tool name discovered via prior `tool_search` calls (via
     `_discovered_tool_names` set), promote it from deferred → visible.
   - Inject a `<system-reminder>` text block on the trailing user turn
     listing the still-deferred tool names (transient, doesn't mutate
     persisted messages).
3. Bedrock invocation via `client.chat(...)`.
4. Append assistant turn (thinking + text + tool_use blocks).
5. Tool dispatch — emit one tool_result per tool_use call. Plan-mode
   gate blocks mutating tools at dispatch (read-only allowlist parity
   with v4 PLAN_MODE_ALLOWED_TOOLS).
6. After each tool_search call, extract `tool_search_discovered_names()`
   from the result text and merge into `_discovered_tool_names` so the
   next turn's `tools=` payload includes those schemas.

OUT OF SCOPE (deferred to later phases per ADR-014):
- Microcompact / context_collapse (Phase 11)
- 2-stage smart compaction (Phase 11)
- Skill auto-trigger (Phase 10)
- forkSubagent (Phase 9)
- File-read state tracking
- Diminishing-returns / repetition guard

Each deferral is justified inline in the module's docstring.

### Tests (37 new)

- `tests/unit/test_budget.py` (7 tests) — defaults, consume, exhaustion,
  reset, thread-safety with 20 concurrent consumers, shared-budget across
  pseudo-sub-agents.
- `tests/unit/test_errors.py` (10 tests) — every category branch + truncation
  + class-identity lock against runtime/bedrock_client re-exports.
- `tests/unit/test_retry.py` (7 tests) — MAX_RETRIES, should_retry branches,
  jitter floor/ceiling, doubling-curve, class-identity lock.
- `tests/integration/test_query_engine.py` (12 tests) — single-turn end_turn,
  tool dispatch round-trip, deferred-tool exclusion, **tool_search round-trip
  promotion (Phase 8 acceptance gate)**, budget exhaustion, max_turns,
  unknown-tool error path, tool exception trapping, system-reminder injection,
  context_overflow exit, run_one_turn helper, plan-mode dispatch gate.

## Test results

- Last full `pytest` run (post Codex fixes): 2026-04-30 — **319 passed + 4 skipped**
  (was 280+4 in Phase 7).
- 39 net-new tests added by Phase 8 (37 initial + 2 Codex-fix lock tests).

## Codex review

- First pass: APPROVE_WITH_FIXES. 2 substantive findings + 2 test gaps.
  - [high] `_discovered_tool_names` leaks across runs.
  - [medium] plan-mode bypass via `always_load=True`.
  - [medium] cross-run reset test gap.
  - [low] plan-mode always_load bypass test gap.
- All 4 addressed in same Phase 08 commit:
  - `core/query_engine.py` `run()` resets `self._discovered_tool_names = set()` at entry.
  - `core/query_engine.py` plan-mode dispatch gate uses strict `PLAN_MODE_ALLOWED_TOOLS` allowlist (replacing the prior `is_read_only AND not always_load` exemption).
  - Lock tests `test_discovered_tools_reset_between_runs` + `test_engine_plan_mode_blocks_always_load_mutating_tool`.
- Post-fix: AXIS A PASS, AXIS B 2 FAITHFUL / 2 ADAPTED / 0 DRIFTED.
- Saved at: `_status/codex_reviews/phase-08.md`.

## Aggregate audit (post-Phase-8)

All 7 mechanical metrics PASS:
- Static prompt tokens: 2498 ≤ 2500 ✓
- Per-section caps: all respected ✓
- Cap sum: 2880 ≤ 2900 ✓
- Section names unique ✓
- tool_classes at slot 2 ✓
- Tool count: 11 (v4 ~30) ✓
- ADR-to-PORT_LOG ratio: 19 PORT_LOG rows / 14 ADRs — all rows reference an ADR ✓

## Better than v4

Per `docs/PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md` (Phase 8 entries):
- v4 monolithic `Agent.run` is ~1500 LOC mixing budget gate, compaction,
  microcompact, skill auto-trigger, sub-agent dispatch, tool execution,
  retry, error classification. v5's `QueryEngine` is ~400 LOC with a strict
  IN-SCOPE / OUT-OF-SCOPE contract; deferred concerns land in their own
  modules at their own phases. Reviewable and testable.
- v5 wires the Phase 7 deferred-loading contract end-to-end on the first
  turn the engine ships. v4 has no such mechanism (every tool schema is
  loaded every turn).
- v5's tool-result truncation respects each tool's `max_result_size_chars`
  (v4 used a single global cap).
- v5 traps tool exceptions and returns a tool_result with `is_error=True`
  to the model so it can recover; v4 leaks raised exceptions in some paths.

## Better than Runnable

- v5 QueryEngine is sync (no Promise / async generator chain) because v5
  ships in `.ipynb` with synchronous tool execute() — easier to reason
  about, fewer cancellation edge cases.
- v5 enforces a single Phase-7 wiring contract: a deferred tool MUST be
  promoted into `tools=` payload after `tool_search` discovers it.
  Runnable manages this through a more complex permission/discovery state
  graph; v5 collapses it to a single `_discovered_tool_names` set.

## Next phase

Phase 08.5 — **Thin-slice parity gate**. Run 10 critical v4-vs-v5 scenarios
BEFORE the skill/sub-agent expansion in Phase 9. Hard blocks Phase 9 from
starting unless 10/10 pass.
