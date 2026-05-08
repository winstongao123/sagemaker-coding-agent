# Changelog — v5 Phase 00 (Scaffold)

Date: 2026-04-30
Phase ID: 00
Tag (after close commit): v5-phase-00
Branch: v5-build (parented from `master` at v4 commit `3ba3425`)

## Goal

Foundational scaffolding for the v5 build. NO Python source code is ported in Phase 00 — all of v5 starts from this paperwork and tracking infrastructure. Phase 01 begins true Runnable porting.

## Commits in this phase

| sha | Subject | Notes |
|---|---|---|
| `5259adf` | scaffold compact_v5/ skeleton + tracking docs + smoke test | Initial folder tree, 5 status docs, 2 ADRs (001 file-per-tool, 002 file-per-section prompt), .gitignore, smoke test (2/2), lint script (5/5), V5_PLAN.md copied to docs/ |
| `cd5f00e` | PS issue mapping + axis-B integration check + Codex 5.5 prep | New compact_v5/docs/V5_PS_ISSUES_MAPPING.md (7 PS issues mapped to v5 phases). New ADR-003 (PS issue mapping), ADR-004 (HTMLs). AXIS B template strengthened with integration-semantic check (up-stream caller match, down-stream dependency, state/cache contract, error contract). Codex CLI upgraded 0.116.0 → 0.125.0; gpt-5.5 reachable. |
| `03abf29` | copy reference HTMLs to compact_v5/docs/htmls/ | 6 HTMLs co-located with v5 source: PS_DEEP_DIVE_RUNNABLE.html, PS_FLOWCHART_RUNNABLE.html, PS_FLOWCHART_V4.html, PS_RUNNABLE_VS_LANGGRAPH.html, HERMES_VS_CODING_AGENT_v4.html, v4_architecture.html. PS_RUNNABLE_VS_LANGGRAPH.html had 5 documentation-example desc-field strings prefixed with "Use when..." to satisfy CSO lint while preserving pedagogical intent. |
| `<close>` | address Codex review findings + close phase | Fixes 3 minor findings from Codex (gpt-5.5) AXIS A: V5_BUILD_STATUS.md stale fields → DONE state with proper Next-session pointer; test_smoke.py recursive scan with allowlist; ADR ordering 001→002→003→004 (was 001→003→004→002); Codex review saved to phase-00.md. Phase 00 OVERALL: APPROVE. |

## Deliverables in compact_v5/

```
compact_v5/
├── .gitignore
├── MAIN/
│   ├── agent/
│   │   ├── __init__.py + 14 sub-package __init__.py files
│   │   ├── core/, prompt/, tools/, tools/shared/, security/, runtime/,
│   │   │   subagent/, skills/, ui/, mcp/  (empty packages)
│   │   └── tests/{__init__.py, test_smoke.py, lint_phase_id.py,
│   │              unit/, tools/, integration/, parity/}
│   └── changelogs/
│       └── CHANGELOG_v5_phase_00.md  (this file)
├── _status/
│   ├── V5_BUILD_STATUS.md           (mechanical phase tracker; State=DONE)
│   ├── V5_RUNNABLE_PORT_LOG.md       (append-only port-log; empty after Phase 00)
│   ├── V5_DESIGN_DECISIONS.md        (4 ADRs accepted: 001 file-per-tool, 002 file-per-section prompt, 003 PS issue mapping, 004 reference HTMLs)
│   ├── CODEX_REVIEW_TEMPLATE.md      (per-phase 2-axis template w/ integration-semantic check)
│   ├── RESUME.md                     (5-step cold-resume protocol)
│   └── codex_reviews/
│       └── phase-00.md               (gpt-5.5 review: APPROVE_WITH_FIXES → APPROVE after close fixes)
└── docs/
    ├── V5_PLAN.md                    (verbatim copy of approved plan)
    ├── PS_actual_use_problems.md     (copied from compact_v4/docs/)
    ├── V5_PS_ISSUES_MAPPING.md       (7 PS issues mapped to v5 phases)
    └── htmls/                        (6 reference HTMLs)
```

## Tests

| Test | Result |
|---|---|
| `tests/test_smoke.py` | 2/2 PASS (every package imports cleanly + recursive no-v4-leak scan) |
| `tests/lint_phase_id.py 00` | 5/5 PASS (canonical ID schema, status doc, codex review file, last commit subject, no existing tag) |

## Codex review

Round 1 (gpt-5.5): **APPROVE_WITH_FIXES** with 3 minor findings (stale status fields, shallow smoke test, ADR ordering).
Close commit addressed all 3.
Phase 00 OVERALL: **APPROVE**.

## ADRs accepted in Phase 00

| ID | Title | Status |
|---|---|---|
| ADR-001 | File-per-tool layout instead of dir-per-tool | ACCEPTED |
| ADR-002 | File-per-section system prompt with `prompt/*.md` | ACCEPTED |
| ADR-003 | v5 must address ALL 7 issues from `PS_actual_use_problems.md` | ACCEPTED |
| ADR-004 | Reference HTMLs copied to `compact_v5/docs/htmls/` | ACCEPTED |

## Runnable patterns adopted in Phase 00

**None.** Phase 00 is scaffold-only. First Runnable port lands in Phase 01 (BedrockClient cache placement from `services/api/claude.ts`).

## Next phase (Phase 01)

**Goal**: Port v4's BedrockClient + Config to `compact_v5/MAIN/agent/runtime/`.
**Runnable source**: `services/api/claude.ts` (cache placement only — v4 already Bedrock-native).
**v4 source inherited**: BedrockClient class verbatim.
**Acceptance**: mock-Bedrock test passes; config loaded from env; thinking config sent on every Bedrock call when CONFIG.thinking_enabled=True (addresses PS Issue #4 verification).
**Effort**: S.

Resume protocol: see `compact_v5/_status/RESUME.md`.
