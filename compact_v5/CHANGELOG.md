# compact_v5 changelog

## v5.0.0 — Build candidate, SHIP BLOCKED (2026-04-30)

> User verdict: **operation FAILED.** All four verification questions
> returned unsatisfactory answers. v5 deferred features without
> permission and did not meet V5_PLAN.md success metric #1 (functional
> parity with v4.10.10). See `_status/V5_SHIP_CRITIQUE.md` for the full
> failure analysis and the v5.0.1 patch agenda.
>
> The 14-phase build mechanically closed all internal gates (tests,
> audit, parity, Codex). The build is preserved at git tag `v5.0.0` for
> traceability, but should NOT be treated as a release until the v5.0.1
> patch (Compactor + TokenTracker + exec-limit enforcement + skill
> name-mismatch fix + real-Bedrock smoke + parity UX) lands.

SageMaker-native re-implementation of Runnable Claude Code. Built across
14 phases (00 → 13, plus 08.5 hard parity gate). Per-phase changelogs at
`MAIN/changelogs/CHANGELOG_v5_phase_NN.md`. Every phase Codex-reviewed
with all flagged issues fixed in same commit + lock tests.

### Phases

- **Phase 00** — Scaffold + ADR/PORT_LOG doctrine + canonical Phase ID.
- **Phase 01** — BedrockClient + Config (verbatim port from v4).
- **Phase 02** — Tool Protocol + registry + plan-mode allowlist + MCP filter.
- **Phase 03** — Core read-only tools (read_file / grep / glob / list_dir).
- **Phase 04** — Core mutating tools + diff_widget approval UX.
- **Phase 05** — bash + python_exec + security/ package (134-case verbatim).
- **Phase 06** — 19-section prompt @ ≤ 2500 tokens + cache-break detection.
              **PS Issue #7 fix**: tool_classes promoted to slot 2.
- **Phase 07** — ToolSearchTool deferred loading (~770 tokens/turn savings).
- **Phase 08** — QueryEngine + retry + errors + IterationBudget (PS Issue #2 data model).
- **Phase 08.5** — Thin-slice parity gate (10/10 critical scenarios).
- **Phase 09** — Sub-agent + Task tool with shared IterationBudget.
- **Phase 10** — Skills + auto-trigger + Hermes filter.
              **PS Issue #1 fix**: skills filtered by available tools.
- **Phase 11** — Notebook UX + entry + thinking/budget UI.
              **PS Issue #2 fix**: visible IterationBudget widget.
              **PS Issue #4 fix**: visible thinking budget widget.
- **Phase 12** — Parity tests vs v4: 15/15 critical + 10/10 non-critical PASS.
- **Phase 13** — Cutover + ship zip + tag v5.0.0 (this release).

### Final state

- **Tests**: 437 pass + 4 skip.
- **Static prompt**: 2498 tokens (within 2500 budget; 45% reduction vs v4 ~5000).
- **Per-turn schema**: ~3230 tokens (vs Phase 6 baseline ~4000; ~770/turn saved).
- **Tool count**: 14 (vs v4 ~30 — flatter surface).
- **Skill count**: 10 production skills (byte-for-byte from v4).
- **PS Issues resolved**: #1 (Hermes filter), #2 (visible budget), #4 (visible thinking), #7 (tool_classes promotion).
- **PORT_LOG**: 37 rows / 19 ADRs / aggregate audit 7/7 metrics PASS.

### Codex review record

Every phase Codex-reviewed (gpt-5.3-codex via stdin). Findings:
- **Phase 06**: 1 major + 2 minor + 1 nit → all fixed.
- **Phase 07**: 4 BLOCKERS → all fixed with lock tests.
- **Phase 08**: 4 findings (cross-run reset, plan-mode bypass) → all fixed.
- **Phase 09**: 7 findings (depth threading, immutability, agent-type) → all fixed.
- **Phase 10**: 9 findings (BLOCKER runtime integration) → all fixed.
- **Phase 11**: 5 findings (CONFIG threading, fallback rendering) → all fixed.
- **Phase 12**: gate-only, no production code.
- All others: clean APPROVE first pass.

### What v5 is NOT

- NOT a v4 replacement on `main` (v4 stays untouched).
- NOT auto-deployed (user explicitly tags + ships).
- NOT a refactor — sibling implementation with clean port map.

### Hard constraints (preserved from v4)

- Bedrock-only (no Anthropic API; uses boto3 `bedrock-runtime`).
- No GitHub network at runtime (local git only inside SageMaker).
- `python_exec` is the canonical Python execution tool (NOT bash python).
- Ships as flat zip — `chat.ipynb` runs without `pip install` of a v5 package.
- All 10 v4 production skills preserved byte-for-byte.
- All v4 destructive-command coverage preserved verbatim (134-case).

### Acceptance gates (V5_PLAN.md success metric)

- [x] Functional parity with v4.10.10 (Phase 12: 15/15 + 10/10 PASS).
- [x] Static system prompt ≤ 2500 tokens (2498 actual).
- [x] Per-turn token overhead ≥ 3000 lower than v4 (deferred-loading active).
- [x] Runnable patterns FAITHFUL or FAITHFUL-WITH-JUSTIFIED-ADAPTATION (no DRIFTED).
- [x] `pytest -q` green (437 pass + 4 skip).
