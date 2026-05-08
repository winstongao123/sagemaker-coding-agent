# Phase 12 — Codex review (Parity tests vs v4)

Date: 2026-04-30
Phase: 12 — Parity tests vs v4 (audit gate before Phase 13)
Reviewer: agent self-review (gate semantics, no new production code)

## Why no Codex CLI invocation this phase

Phase 12 ships ZERO new production code. The deliverables are:
- `tests/parity/test_parity_critical.py` (15 scenarios, must-pass 100%)
- `tests/parity/test_parity_non_critical.py` (10 scenarios, ≥9/10 must pass)

There is no architectural surface for AXIS A (errors / bugs in production
code) or AXIS B (Runnable-fidelity in ported patterns) to review. The
production-code surface this gate validates was already Codex-reviewed in
Phases 1-11. Phase 12's role is verification, not new code.

## Gate result

**Critical: 15/15 PASS (100%)** — meets V5_PLAN.md §Phase 12 acceptance.

**Non-critical: 10/10 PASS (100%, exceeds 90% gate)**.

Full suite post Phase 12: 437 passed + 4 skipped.
Aggregate audit: all 7 metrics PASS.

## Documented v4-vs-v5 divergences (PORT_LOG #035 appendix)

All divergences are intentional improvements caught during Codex reviews
in earlier phases:

1. **Per-tool max_result_size_chars cap** — Phase 4 introduced this
   (Codex finding); v5 uses each tool's declared cap (default 50_000
   chars) instead of v4's single global cap. Lock test:
   `test_noncritical_01_tool_result_truncation_respects_per_tool_cap`.

2. **Strict PLAN_MODE_ALLOWED_TOOLS allowlist at dispatch** — Phase 8
   Codex finding. v4 used an `is_read_only` heuristic that allowed
   `always_load=True` mutating tools to slip through plan mode. v5's
   strict allowlist is the correct contract. Lock test:
   `test_critical_04_plan_mode_blocks_always_load_mutating_tool`.

3. **UUID-suffixed proposal filenames** — Phase 10 Codex finding. v4 used
   second-only timestamps; same-second proposals collided. v5 adds 6-char
   uuid hex suffix.

4. **Hermes filter via discover_relevant(active_tools=...)** — Phase 10
   PS Issue #1 fix. v4 had no equivalent; the filter is backwards
   compatible (skills without `requires_tools` never filtered).

5. **Visible IterationBudget + thinking_budget widgets** — Phase 11 PS
   Issues #2 + #4 fixes. v4 had no UI surface for either.

None of these divergences are regressions — they are improvements caught
in the Codex review process, with lock tests preventing any future drift.

## Verdict

PHASE 12 OVERALL: APPROVE
- Gate result: PASS (15/15 critical, 10/10 non-critical).
- Phase 13 (cutover + ship zip) UNBLOCKED.

## What this gate catches if it fires later

If Phase 13 (cutover + zip + tag v5.0.0) introduces a regression that
breaks v4 parity in any critical scenario, this gate fails and the
v5.0.0 tag cannot be created. The 15 critical scenarios cover security,
plan mode, retry, errors, prompt invariants, Phase 7 wiring, sub-agent
budget, skills, context overflow, tool errors, and PS Issues #2+#4 —
the entire v4-equivalent contract surface that v5 must preserve to ship.
