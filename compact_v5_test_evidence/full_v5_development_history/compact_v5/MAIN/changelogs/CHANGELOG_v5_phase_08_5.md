# V5 Phase 8.5 Changelog — Thin-slice parity gate (HARD BLOCKER)

Date: 2026-04-30
Tag (target): v5-phase-08_5 (canonical decimal-as-underscore form)
Plan reference: V5_PLAN.md §Phase 8.5

## Goal

A HARD blocker before Phase 9 (sub-agent + Task tool). 10 critical
cross-phase integration scenarios — 10/10 must pass before Phase 9 starts.

This is NOT v4-vs-v5 parity (Phase 12 owns that). It is **architectural-drift
detection** — if any single phase regresses behavior the others depend on,
this gate fires before more code is layered on top.

## What landed

`tests/parity/test_thin_slice.py` — 10 scenarios spanning every prior phase:

| # | Phase | Scenario | What it locks |
|---|-------|----------|---------------|
| 01 | 1 | BedrockClient mock-mode round-trip | Response shape + ToolCall dataclass |
| 02 | 2 | Registry assembly: deny rules + plan-mode subset | get_tools/assemble_tool_pool composition |
| 03 | 3 | read_file dispatch with SECURITY rebuild | tool execute path live |
| 04 | 5 | bash blocked by SecurityManager (DANGEROUS_PATTERNS) | dangerous_patterns + dispatch wiring |
| 05 | 5 | python_exec rejects banned `socket` import | dangerous_python + closure sandbox + AST analysis |
| 06 | 6 | Static prompt ≤ 2500 tokens AND tool_classes at slot 2 | PS Issue #7 fix + token budget |
| 07 | 6 | CACHE_BOUNDARY marker present in assembled prompt | Bedrock cache-block split contract |
| 08 | 7 | apply_tool_search_deferral partition + tool_search executes + discovered-names extraction | Phase 7 ↔ Phase 8 wiring contract |
| 09 | 8 | End-to-end QueryEngine: tool_use → tool_result → final | Phase 8 acceptance |
| 10 | 8 | Phase 7 wiring contract: tool_search promotes view_image into next turn | Phase 7 ↔ 8 round-trip |

## Test results

- 10/10 thin-slice scenarios PASS.
- Full suite: **329 passed + 4 skipped** (was 319+4 in Phase 8; +10 thin-slice tests).
- Aggregate audit: all 7 metrics still PASS.

## Notes on scenario authoring

- Scenario 06 measures `total_static_tokens()` (the canonical audit metric)
  rather than `estimate_tokens(build_system_prompt(ctx))` because the
  assembled prompt includes a ~13-token framing overhead (cache-boundary
  marker + section separators) that's expected and constant. The audit's
  2500-token target is for the cached static block.
- Scenario 03 uses `monkeypatch.setattr(CONFIG, 'workspace', tmp_path)` +
  `_security_manager.rebuild_singleton_for_tests()` — same pattern Phase 4
  established for SECURITY singleton test isolation.

## Better than v4

- v4 had no thin-slice equivalent. Refactors landed without a single hard
  gate that exercised every prior layer end-to-end. v5's Phase 8.5 catches
  drift in any single layer before Phase 9 starts.
- v4's parity work landed at the END (just before ship). v5 splits parity
  into two passes: thin-slice (Phase 8.5, after main loop ships) and full
  v4-vs-v5 (Phase 12). Catches drift earlier.

## Next phase

Phase 09 — Sub-agent + Task tool. Port Runnable's `forkSubagent` budget-
sharing pattern; reuse v4's `_build_subagent_handoff_block` and
`_build_subagent_env_details` blocks verbatim.
