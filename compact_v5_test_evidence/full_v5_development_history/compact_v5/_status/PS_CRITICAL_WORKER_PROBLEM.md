# PS_CRITICAL_WORKER_PROBLEM

Date: 2026-05-06
Status: RESOLVED_BY_COMPLETION_REDO_AND_FINAL_POST_AWS_REVIEW
Author: Codex audit

This file documents the critical worker/process problem discovered during
v5.0.1 R-tier validation. It is intentionally direct: v5.0.1 has real built
code and real passing AWS evidence, but the build/review process did not
prove the full post-Wave-5-DEEP scope was implemented.

Final resolution:

- The completion redo built the row-level ledger and strict scope gates that
  this incident required.
- A-16 cold-cache microcompact was implemented before production and R4 was
  closed as READY with Claude Phase C `GENUINE_PASS`.
- The default R-tier gate now checks all matrix rows by default.
- The final R-tier matrix has 28 `READY` rows and 14 `DISPOSITION_OK` rows.
- Final Claude post-AWS review returned
  `PRODUCTION_READINESS_DECISION: APPROVE_PRODUCTION_READY`.

The historical findings below are preserved as root-cause evidence for why the
redo was necessary. They are no longer the current ship decision.

## Executive Verdict

v5.0.1 is not "nothing built." Many blocks contain real code, tests, tags,
and Codex reviews. R1, R2, R3, and R5 produced useful real-AWS evidence.

The failure is different:

1. The canonical plan required v5.0.1 to combine v4 + Runnable + Hermes +
   Learning Factory with no silent deferrals.
2. Several block implementations were closed against a narrower block prompt
   / TEST_DESIGN / changelog scope.
3. Codex reviews approved that narrower submitted scope.
4. The status log then marked blocks DONE and R-tier began as if DONE meant
   full SYNTHESIS_MASTER completeness.
5. R4 exposed the contradiction before AWS spend because A-16 cold-cache
   microcompact is not implemented.

## Canonical Plan Evidence

| File | Evidence |
|---|---|
| `_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md:1-31` | Post-Wave-5-DEEP plan states SYNTHESIS_MASTER is canonical and `v5 = v4 + Runnable + Hermes + LF COMBINED`. |
| `_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md:18-24` | Plan says 21 Blocks, about 19,300 LOC, +233 PORT_LOG rows, and 8 NOT-OPTIONAL correctness fixes. |
| `_phase_2/wave_6/BUILDER_PROMPT.md:13-19` | Mission says v5.0.1 must cover v4 baseline, be >= Runnable on better axes, be > v4, avoid all PS problems, and handle 111 scenarios. |
| `_phase_2/wave_6/BUILDER_PROMPT.md:23-37` | Hard constraints include cover all v4 + Runnable + Hermes + LF, line-by-line investigation, and NO DEFERRALS. |
| `_phase_2/wave_6/BUILDER_PROMPT.md:45-48` | Worker required to read SYNTHESIS_MASTER, PS_Plan_Edge_Cases, and TEST_DESIGN before coding. |
| `_status/RESUME.md:47-52` | Resume protocol required pasting block-specific SYNTHESIS_MASTER scope and TEST_DESIGN into builder prompt. |
| `_status/RESUME.md:55-61` | Drift prevention required PORT_LOG rows and ADRs for every adopted Runnable/Hermes/LF pattern. |
| `_status/RESUME.md:83-90` | Tag forbidden if Codex findings remain; user approval gate required. |

## Current Built Status From Logs

The repo really does contain block tags, status entries, mock tests, and
Codex review artifacts.

| Block | Plan rows | PORT_LOG rows seen | TEST_DESIGN tests | Actual tests | Missing TEST_DESIGN names | Tag evidence | Audit status |
|---|---:|---:|---:|---:|---:|---|---|
| 0 | 10 | scattered/remap | 5 | 5 | 0 | `v5.0.1-block-0` @ `19e7823` | Mostly OK; remap-heavy trace. |
| B | 16 | 7-10 depending remap counting | 8 | 29 | 1 renamed/mismatch | `v5.0.1-block-b` @ `ee01142` | Real code built; item trace incomplete. |
| B+ | 8 | about 10 | 7 | 21 | 0 | `v5.0.1-block-b-plus` @ `ff30e8d` | Real code built; some remap evidence weak. |
| C | 19 | about 5 | 12 | 21 | 4 renamed/mismatch | `v5.0.1-block-c` @ `77c6eb4` | Real code built; C-15/C-16/C-17 need row audit. |
| C+ | 3 | 1 | 7 | 17 | 0 | `v5.0.1-block-c-plus` @ `f9e4000` | Real code built; plan rows not granularly closed. |
| D | 13 | 1 bundled | 26 listed, parser saw 1 due slash names | 22 | naming mismatch | `v5.0.1-block-d` @ `7a19715` | Functional command surface likely built; trace bundled. |
| A | 43 | 5 actual rows #066-#070 | 12 | 25 | 12 | `v5.0.1-block-a` @ `c87a823` | CRITICAL DRIFT. Cold-cache and stub-injection missing. |
| E+F | 8 | 1 remap-only row #071 | 14 | 15 | 14 | `v5.0.1-block-e-f` @ `2388e64` | CRITICAL DRIFT. Built env_block remaps, not UI/status scope. |
| F2 | 2 | 1 | 3 | 20 | 0 | `v5.0.1-block-f2` @ `9d3cd50` | Likely built; row count small but tests expanded. |
| I | 13 | 11+ | 8 | 22 | 0 | `v5.0.1-block-i` @ `c46be09` | Mostly well traced; I-12 explicitly deferred/remapped. |
| M | 0 | 2 | historical extra | 11 | n/a | `v5.0.1-block-m` @ `09b6114` | Extra critical fixes only; OK. |
| G | 8 | about 6 | 8 | 22 | 0 | `v5.0.1-block-g` @ `0fe6454` | Real code built; some wiring/remap risk. |
| G3 | 2 | 2 | 5 | 16 | 0 | `v5.0.1-block-g3` @ `6a49879` | Likely OK. |
| G2 | part of G/G2 plan | 1 | 3 | 9 | 0 | `v5.0.1-block-g2` @ `4a7fd7e` | Helpers built; runtime fork wiring must be confirmed. |
| H | 20 | 4 | 6 | 19 | 0 | `v5.0.1-block-h` @ `9759c11` | Built with explicit deferrals; deferred targets need closure audit. |
| H+ | 1 | 1 | 5 | 15 | 0 | `v5.0.1-block-h-plus` @ `d40493e` | Likely OK; manual-only dream decision explicit. |
| L | 28 | 2 | 8 | 14 | 0 | `v5.0.1-block-l` @ `686a3d5` | Partial. Error/cache pieces built; larger guardrail scope not proven. |
| N | 19 | 1 | 9 | 16 | 0 | `v5.0.1-block-n` @ `136f41b` | Partial. Helpers built; runtime parallel wiring not proven. |
| T | 12 | 2 | 11 | 25 | 1 (`web_fetch`, user-dropped) | `v5.0.1-block-t` @ `1cda54a` | v4 tool surface mostly built; Wave fold-ins need row audit. |
| J | 0 | 1 | ship-gate tests | 8 | n/a | `v5.0.1-block-j` @ `cab61ec` | Ship-gate code built. |
| K | 8 | 0 clear rows | 5 | 6 | 0 | `v5.0.1-block-k` @ `d89067c` | Process tests built; PORT_LOG/ADR closure weak. |

Important: the "Actual tests" column proves work happened. The "Audit status"
column flags that work does not equal full canonical scope closure.

## Critical Block A Evidence

SYNTHESIS_MASTER Block A lists A-1 through A-43:

| Key item | Plan evidence | Current evidence | Status |
|---|---|---|---|
| A-16 time-based microcompact | `SYNTHESIS_MASTER.md:164` | No `microcompact`, `cold_cache`, idle-resume, or elapsed-time trigger in `MAIN/agent` compactor path. | MISSING |
| A-25 stub injection for missing tool_results post-compact | `SYNTHESIS_MASTER.md:173` | Generic stub helper exists in `core/parallel_dispatch.py`, but `core/compactor.py:488-506` returns summary + recent messages only. | MISSING IN COMPACTOR |
| Block A expected scope size | `SYNTHESIS_MASTER.md:145-193` | 43 planned rows, about 1510 LOC. | NOT CLOSED |
| Block A actual PORT_LOG | `V5_RUNNABLE_PORT_LOG.md` rows #066-#070 | v4 Compactor, circuit breaker, cache_edits, B-2, B+5. | 5 ROWS |
| Block A tests promised | `TEST_DESIGN.md:162-179` | 12 named tests including cold-cache and stub injection. | NOT IMPLEMENTED BY NAME |
| Block A actual tests | `test_block_a.py:1-14` | Header lists narrower tests: estimate/prune/80% trigger/summary/circuit breaker/cache_edits/B-2/B+5. | NARROWED |
| Block A review prompt | `codex_reviews/block-a-iter1.md:13-26` | Asked Codex to review Compactor + circuit breaker + cache_edits + B-2/B+5. | NARROWED PROMPT |
| Block A final review | `codex_reviews/block-a.md:1091` | APPROVE after fixing submitted-scope issues. | APPROVED NARROWER SCOPE |

## Critical E+F Evidence

| Item | Evidence | Status |
|---|---|---|
| TEST_DESIGN expected E+F UI/status work | `TEST_DESIGN.md:183-202` lists render_chat, assistant markdown, todos, token display, status bar, dark mode, model dropdown, budget widgets, session dropdown/load, autosave, long text collapse, thinking config. | EXPECTED |
| Actual `test_block_e_f.py` header | `test_block_e_f.py:1-10` says Block E+F covers env_block + ADR-020 0-2/0-4/0-6 remap closure. | NARROWED |
| Actual missing names | All 14 TEST_DESIGN E+F names are absent by exact function name. | CRITICAL DRIFT |
| Changelog wording | `CHANGELOG.md:3-31` says env_block + ADR-020 remap closure. | Changelog matches narrowed scope, not TEST_DESIGN. |

## Why Codex Review Did Not Catch It

Codex did not approve full SYNTHESIS_MASTER completeness. Codex approved the
scope presented in each per-block review prompt.

| Mechanism | Evidence | Effect |
|---|---|---|
| Review template had intent but no mechanical ledger | `CODEX_REVIEW_TEMPLATE.md:59-89` says no silent narrowing, but does not require enumerating every SYNTHESIS_MASTER row with SHIP/DEFER/DROP evidence. | Human/prompt can omit rows. |
| Builder prompt said to check SYNTHESIS_MASTER | `BUILDER_PROMPT.md:172-175` says Axis C should ask whether the block ported everything tagged for it. | Correct rule existed. |
| Actual Block A prompt narrowed the question | `block-a-iter1.md:13-26` only asks about Compactor/circuit breaker/cache_edits/B-2/B+5. | Codex reviewed the narrow block. |
| Actual E+F prompt narrowed the question | `block-e-f-iter1.md:27` asks whether ADR-020 0-2/0-4/0-6 are covered. | Codex reviewed env_block remaps, not UI scope. |
| Status log treated narrowed APPROVE as block DONE | `V5_BUILD_STATUS.md:556-576` lists all blocks DONE/tagged. | R-tier started from false completeness assumption. |

Root cause:

The process relied on natural-language "no silent scope narrowing" rules, but
did not require a generated, row-by-row, machine-checkable ledger from
SYNTHESIS_MASTER to code/tests/PORT_LOG/review evidence. Once a block prompt
omitted rows, Codex could pass the submitted work while the canonical scope
remained incomplete.

## R-tier Test Suite Status

The R-tier plan is valuable but not currently complete.

| Source | Evidence |
|---|---|
| `docs/CODEX_CONTEXT_v5_R_TIER.md:21-33` | Defines 42 scenarios with $14.25 total cap. |
| `docs/CODEX_CONTEXT_v5_R_TIER.md:37-52` | R1-R12 cover composite and PS problem fixes. R4 explicitly covers 30-min idle/cold-cache compact. |
| `_status/R_TIER_GATE_STATUS.md:30-40` | Gate requires all 42 scenarios materialized and completed evidence for each done test. |
| `_status/R_TIER_GATE_STATUS.md:71-81` | As of initial gate doc, many tests were not materialized. |
| Current local gate run on 2026-05-04 | Fails for missing executable markers for R4, R6-R16, R18-E1..E15, and R19-U1..U10. |
| `_status/r_tier_review_log.md:3-7` | R1, R2, R3, R5 have real evidence; R4 was deferred before spend. |

Current R-tier interpretation:

| Test | Current result | Meaning |
|---|---|---|
| R1 | GENUINE_PASS | Composite workflow worked and found/fixed Unicode/max_tokens/AU cost bugs. |
| R2 | GENUINE_PASS | Existing token-threshold compactor works on real Bedrock. It does not prove cold-cache A-16. |
| R3 | GENUINE_PASS | Sub-agent scenario worked for tested Phase-9 path. |
| R4 | DEFERRED-NOT-IMPLEMENTED | Correctly stopped because A-16 is absent. |
| R5 | GENUINE_PASS | Exec-limit recovery works. |
| R6-R16, R18, R19 | Not executable according to gate | Test suite is not ready to prove 42-scenario coverage. |

## Immediate Required Actions

1. Halt new AWS R-tier calls except zero-cost audits.
2. Build a row-level ledger for all 233 SYNTHESIS_MASTER planned rows.
3. For each row, record:
   - source block item id
   - source file:line from SYNTHESIS_MASTER
   - current status: SHIPPED / PARTIAL / MISSING / DEFERRED / DROPPED
   - exact code file:line evidence
   - exact test evidence
   - PORT_LOG row
   - ADR row
   - review prompt that included the row
   - review verdict that closed it
   - git commit/tag
4. Patch the runtime blockers before resuming R-tier:
   - A-16 cold-cache microcompact
   - A-25 post-compact tool_result stub injection in compactor path
   - E+F promised UI/status tests or explicit row-by-row disposition
   - L large-scope guardrail gaps
   - N runtime parallel execution wiring if still in scope
   - K process/PORT_LOG closure
5. Add a new independent Claude-review requirement:
   - Claude reviewer must receive the ledger.
   - Claude reviewer must independently regenerate the row list from
     SYNTHESIS_MASTER, not trust the worker.
   - Claude reviewer must reject if any SYNTHESIS_MASTER row lacks disposition.
   - A block cannot be marked DONE from tests alone.

## Current Ship Decision

v5.0.1 production readiness is approved by final post-AWS Claude review.

Canonical closeout files:

- `compact_v5/_status/v5_completion_audit/FINAL_POST_AWS_PRODUCTION_READY.md`
- `compact_v5/_status/v5_completion_audit/reviews/final-claude-post-aws-production-readiness-review.md`
- `compact_v5/_status/R_TIER_GATE_STATUS.md`
- `compact_v5/_status/r_tier_test_matrix.json`

Historical diagnostic/non-ready spend and failed evidence remain preserved.
