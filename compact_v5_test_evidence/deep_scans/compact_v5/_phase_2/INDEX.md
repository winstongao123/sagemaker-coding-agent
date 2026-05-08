# Phase 2 — Materials Index (for v5.0.1 builders)

**Purpose**: This is the canonical index of every Phase 2 deliverable. Workers building v5.0.1 should start here and follow the references.

## TL;DR — start here (post-Wave-5-DEEP + Wave 6, 2026-05-01)

**Canonical (post-DEEP) for builders**:
1. **`wave_6/BUILDER_PROMPT.md`** — **THE WORKER PROMPT**. Self-contained instructions for any worker (sub-agent, Codex, fresh Claude session) to implement one Block correctly. Paste Block-specific scope/tests/scenarios into the placeholder sections.
2. **`wave_5_deep/SYNTHESIS_MASTER.md`** — POST-DEEP CANONICAL. 21 Blocks, ~19,345 LOC, 448 PORT_LOG rows, every NEW finding with file:line + LOC + architectural-fit verdict.
3. **`wave_5_deep/CONFIDENCE_REPORT.md`** — 9-axis verdict v5 > Runnable > v4 with evidence.
4. **`wave_6/PS_Plan_Edge_Cases_Thinking.md`** — 111 user scenarios; 74 HANDLED + 42 NEEDS-LOCK-TEST + 9 POSSIBLE-GAP (all closed in existing Blocks).
5. **`wave_6/TEST_DESIGN.md`** — per-Block test catalogue (T1-T5 tiers + R1-R12 high-value real-AWS scenarios + per-Block close ritual).
6. **`synthesis/V5_PHASE_2_PLAN_v3.md`** — Block-level scoping (header points to SYNTHESIS_MASTER for grafts).
7. **`wave_4/Q1-Q4 evidence matrices`** — Q1 PORT_LOG (215 + 233 pending materialization per Block); Q2 PS_problems CERTAIN-NO-RECUR; Q3 9-axis matrix incl. security/PII; Q4 26 bug classes.

**Source code references** (read-only):
- v4: `compact_v4/MAIN/agent/sagemaker_agent.py` (12,088 LOC)
- Runnable: `_archive/compare_code/gg-claude-code-runnable/src/` (2010 .ts/.tsx files)
- Hermes: `D:/Github/hermes-agent/run_agent.py` (12,880 LOC) + AGENTS.md
- LF: `D:/Github/Learning_Factory/`

## Reading order for a new worker

If you are about to start coding a Block, read in this order:

1. **`wave_5_deep/SYNTHESIS_MASTER.md`** — find your Block; read every PORT_LOG row + architectural-fit verdict + Q4 lock test list.
2. **`wave_6/PS_Plan_Edge_Cases_Thinking.md`** — find scenarios tagged with your Block; treat NEEDS-LOCK-TEST items as additional Q4 rows you must add.
3. **`synthesis/V5_PHASE_2_PLAN_v3.md`** — Block scoping.
4. **`wave_3/COMBINED_ARCHITECTURE.md`** — combined-architecture decision per Block.
5. Source code at cited file:line in v4 / Runnable / Hermes / LF.
6. Existing v5 code at target paths.
7. **`wave_4/Q4_BUG_COVERAGE.md`** for original Block lock tests + Wave-6 additions.

## Decision log (2026-05-01)

- **Auto-Dream (Block H+) is MANUAL-TRIGGER ONLY**. No daemon, no auto-fire. User invokes `/dream` slash command (Block D) to consolidate memory.md + AGENT_STATUS.md. USER_GUIDE must clearly document `/dream` usage.
- **No-deferrals enforced**: 0 DEFERRED rows; every drop is OUT-OF-SCOPE-BY-CONSTRAINT with citation.
- **21 Blocks** counting E+F as 1 combined: 0 → smoke → B → B+ → C → C+ → D → A → E+F → F2 → I → M → G → G3 → G2 → H → H+ → L → N → T → J → K.

## Folder structure (with redundancy notes)

```
_phase_2/
├── INDEX.md                          # this file
├── v4_reference/                     # v4 chat UI source as standalone reference
│   ├── chat.ipynb                    # v4 notebook (canonical UI)
│   ├── chat.md                       # v4 notebook companion
│   ├── USER_GUIDE.md                 # v4 user docs
│   └── create_chat_ui.py             # v4 create_chat_ui extracted (2354 LOC standalone)
│
├── team_1_v4_vs_v5/                  # Wave 1 — v4 vs v5 audit
│   ├── AGENT_1A_REPORT.md            # UI parity (87 widgets / v5 has 7)
│   ├── AGENT_1B_REPORT.md            # non-UI parity (initial)
│   └── AGENT_1B2_REPORT.md           # non-UI parity (cross-checker for 1B)
│       (NOTE: 1B + 1B2 overlap; 1B2 is independent verification.
│        Read 1B for inventory, 1B2 for cross-check.)
│
├── team_2_runnable_vs_v5_a/          # Wave 1 — Runnable adoption verify
│   ├── AGENT_2A_REPORT.md            # PORT_LOG honesty audit (FAITHFUL verdicts)
│   └── AGENT_2B_REPORT.md            # leftover Runnable patterns to adopt
│
├── team_3_runnable_vs_v5_b/          # Wave 1 — independent Runnable cross-check
│   ├── AGENT_3A_REPORT.md            # cross-check of 2A/2B findings
│   └── AGENT_3B_REPORT.md            # code-experience patterns deep dive
│
├── team_4_hermes_lf/                 # Wave 1 — Hermes + LF
│   ├── AGENT_4A_REPORT.md            # Hermes patterns
│   └── AGENT_4B_REPORT.md            # LF patterns + AXIS C gap analysis
│
├── wave_2/                           # Wave 2 — line-by-line audit (no skip)
│   ├── v4_section_1/REPORT.md        # v4 lines 1-3000 (Config, BedrockClient, classes)
│   ├── v4_section_2/REPORT.md        # v4 lines 3000-6000 (Compactor, SkillManager)
│   ├── v4_section_3/REPORT.md        # v4 lines 6000-9000 (Agent class, dispatch)
│   ├── v4_section_4/REPORT.md        # v4 lines 9000-12088 (chat UI; 87 features)
│   ├── runnable_query_engine/REPORT.md       # Runnable QueryEngine.ts + Tool.ts + tools.ts
│   ├── runnable_services_api/REPORT.md       # Runnable errors.ts + withRetry.ts + cache-break detection
│   ├── runnable_compact_extract/REPORT.md    # Runnable compact + microCompact + extract + sessionMemory
│   ├── runnable_tools/REPORT.md              # Runnable tool implementations
│   ├── runnable_prompts_commands/REPORT.md   # Runnable prompts.ts (914 LOC) + commands/ + hooks/
│   ├── hermes_full/REPORT.md                 # Hermes 6 net-new patterns (verified line refs)
│   └── learning_factory_full/REPORT.md       # LF pattern catalog + AXIS C gap proposal
│
├── wave_3/                           # Wave 3 — synthesis-driving audits
│   ├── COMBINED_ARCHITECTURE.md      # per-Block: v4+Runnable+Hermes+LF combination decision
│   ├── COMPLETENESS_VERIFY.md        # 67 gaps audited; 63 mapped (94%); 4 candidates for v4
│   └── RISK_SURFACE.md               # 17 semantic-bug categories (Q4 input)
│
├── wave_4/                           # Wave 4 — Q1-Q4 evidence matrices
│   ├── Q1_EVIDENCE_MATRIX.md         # every change has source ref
│   ├── Q2_PS_COVERAGE.md             # all 7 PS Issues have lock test + scenario
│   ├── Q3_BETTER_THAN_MATRIX.md      # axis-by-axis v5 vs v4 vs Runnable evidence
│   └── Q4_BUG_COVERAGE.md            # every risk class has lock test + Block owner
│
├── synthesis/                        # the v5.0.1 plan, version history
│   ├── V5_PHASE_2_PLAN.md            # v1 — REJECTED by Codex (6 blockers)
│   ├── V5_PHASE_2_PLAN_v2.md         # v2 — REJECTED by Codex (4 blockers)
│   └── V5_PHASE_2_PLAN_v3.md         # v3 — Codex APPROVE; the canonical detailed plan
│       (v1, v2 kept for traceability of the iteration; v3 is the source of truth.)
│
└── codex_review/                     # Codex review trail
    ├── codex_prompt.txt              # prompt used for v1 review
    ├── CODEX_REVIEW.md               # v1 review (REJECT)
    ├── CODEX_REVIEW_v2.md            # v2 review (REJECT)
    ├── CODEX_REVIEW_v3.md            # v3 review (REJECT — close)
    ├── CODEX_REVIEW_v3b.md           # v3b review (APPROVE_WITH_FIXES)
    └── CODEX_REVIEW_v3c.md           # v3c review (APPROVE — final)
```

## Redundancy notes (for future cleanup)

- **synthesis/V5_PHASE_2_PLAN.md + v2.md** can be archived — superseded by v3. Kept for review-iteration traceability only. Builders should ignore v1/v2.
- **team_1_v4_vs_v5/AGENT_1B_REPORT.md** and **AGENT_1B2_REPORT.md** are intentional cross-checkers (independent investigation). Keep both — they overlap by design.
- **wave_4 matrices** supersede the Wave 1 + Wave 2 + Wave 3 reports for builder-facing summary. Wave 1-3 reports remain for traceability of how matrices were derived.
- **codex_review/** files are historical — only `CODEX_REVIEW_v3c.md` reflects the current approved state.

## Builder workflow (per-Block)

For each of the 17 Blocks (0 → smoke → B → B+ → C → C+ → D → A → E+F → I → M → G → G2 → H → L → N → J → K):

1. Read Block's section in `synthesis/V5_PHASE_2_PLAN_v3.md`.
2. Read Block's section in `wave_3/COMBINED_ARCHITECTURE.md`.
3. Read source ranges cited in v4 / Runnable / Hermes / LF.
4. Read existing v5 code at target file paths.
5. Implement.
6. Add lock tests per `wave_4/Q4_BUG_COVERAGE.md` rows owned by this Block.
7. Run pytest — must be green.
8. Run Codex (gpt-5.5) AXIS A/B/C review on the diff.
9. Get user approval before next Block.
10. Update PORT_LOG + CHANGELOG_v5_block_X.md + V5_BUILD_STATUS.md.

## Hard constraints (apply to every Block)

(consolidated from user directives 2026-04-30):
1. v4.10.10 = baseline (functional capability is the floor).
2. v4 chat.ipynb = canonical UI (UNCHANGED in v5 via shim).
3. Cover ALL of v4 + Runnable + Hermes + LF (NO DEFERRALS).
4. Line-by-line investigation, no skip (this Phase 2 satisfies it).
5. Minimum file structures (consolidate post-port).
6. Architecture-first thinking before adopting any pattern.
7. PS_problems STRUCTURALLY fixed.
8. v5 > Runnable > v4 > others on the axes that matter.
9. Drop MCP entirely.
10. Drop streaming.
11. Clear plan with code-chunk refs (this is it).

## Status

- Wave 1: COMPLETE (9 reports).
- Wave 2: COMPLETE (11 reports).
- Wave 3: COMPLETE (3 reports).
- Wave 4: 2/4 IN-DISK (Q2, Q4); Q1 + Q3 still running.
- Codex APPROVE on v3 plan: confirmed (v3c).
- Plan APPROVED by user via ExitPlanMode.

When Q1 + Q3 land + matrices are reviewed, builders proceed Block-by-Block.
