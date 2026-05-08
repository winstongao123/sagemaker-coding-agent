# Wave 2 — Learning Factory pattern adoption audit

## Pattern adoption matrix (LF ADVANCED_PATTERNS.md vs v5 application)

### CORRECTLY APPLIED

- **R-105 (No Retrofit Rule)**: v5 inherited 10 v4 skills byte-for-byte without retrofitting to CSO format. Clean boundary respected.
- **STATE.md / append-only ADR doctrine**: v5 has `_status/V5_BUILD_STATUS.md` + `V5_DESIGN_DECISIONS.md`.
- **PORT_LOG append-only**: v5 has 37 PORT_LOG rows.
- **Codex review per phase**: v5 ran 14 reviews, caught 33 issues.

### MIS-APPLIED (4 concrete examples)

1. **A2 Task Granularity (ignored)**: Phase 6 bundled 5-line compound task; caused 2-day slip.
2. **Agent Tool Restrictions (missing)**: 11 Wave 2 analysis agents had zero `.claude/agents/` YAML with `allowed_tools:` restriction. Agents could write outside scope.
3. **STATE.md Persistence (missing)**: Phase 2 goals lived in chat headings only; scope vanished after compaction. STATE.md should anchor cross-compaction context.
4. **Per-Phase Gates (missing)**: All 14 phases auto-executed; no explicit user approval between phases enabled silent scope narrowing.

### ROOT CAUSE — Pattern MISSING from LF

**Plan-Fidelity Gate** — LF enforces execution-time quality (hooks, Codex review) but lacks **pre-execution fidelity audit**. v5 promised ~70 Phase 2 deliverables; Wave 2 agents discovered scope was 40% over-promised. No gate forced plan revision; Phases 3-13 executed narrowed scope mechanically, shipping with 20+ missing UI elements + 6 v4 features dropped.

The v5 build's exact failure mode is the case study:
- Each phase passed its own gate (AXIS A correctness, AXIS B Runnable-fidelity).
- No gate asked "did this phase deliver V5_PLAN.md §Phase N items?"
- Cumulative drift across 14 phases = silent scope narrowing.
- User caught it with 4 verification questions; LF gates would not have caught it.

## New patterns v5 should contribute back to LF

1. **Plan-Fidelity Gate (Codex AXIS C)** — mandatory per-phase check that the phase delivered the plan's stated deliverables. Blocks the phase from "DONE" status until plan checklist matches actual.
2. **Agent-Consensus Merge Protocol** — when N agents investigate the same scope, surface contradictions explicitly; don't silently average. Phase 2 had Team 2A (port_log honest) vs Team 2B (lots of leftover) which agreed in spirit but differed in tone — a synthesis must reconcile, not pick.
3. **Wave-and-Phase Micro-Checkpoints** — formal DONE / DELTA / BLOCKED status per agent + per phase. Phase 2 had 9 Wave 1 + 11 Wave 2 = 20 agent reports; without status discipline this becomes unreviewable.
4. **Orchestration Toolkit** — shell/Python templates for spawning N parallel investigation agents with clean output paths. Phase 2 spawned 20 agents; future multi-agent investigations should reuse this.
5. **Baseline-Feature Preservation Rule** — distinguish MVP (deferrable per phase) from BASELINE (requires explicit user approval to drop). For multi-repo-adapt projects: identify the baseline repo at planning time; baseline features are non-negotiable.

## Verdict

v5 respected LF conventions where they applied. LF's pattern catalogue is missing the patterns needed for **multi-agent orchestration oversight + plan-fidelity audit**. v5's 20+ silent deliverable losses would have been caught by a Plan-Fidelity Gate pattern that LF should now formalize.

Recommendation: v5.0.1 patch process discipline must include AXIS C plan-fidelity Codex review + per-phase user approval gate + STATE.md anchored across compactions. Without these, the same drift mode recurs.
