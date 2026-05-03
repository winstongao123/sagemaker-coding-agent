# Worker hints — read at start of every Block (2026-05-03)

These supersede prior wording in BUILDER_PROMPT.md / SYNTHESIS_MASTER.md if any conflict exists.

## 1. Model defaults — FINAL

- **Production default**: `au.anthropic.claude-sonnet-4-5-20250929-v1:0` (Sonnet 4.5 AU). User has NO Sonnet 4.6 access — never reference 4.6 in any new code, doc, test, ADR, PORT_LOG row.
- **Test default (R1-R10, R12 + all integration tests)**: `au.anthropic.claude-haiku-4-5-20251001-v1:0` (Haiku 4.5).
- **R11 only**: Sonnet 4.5 (was 4.6 — already updated in `TEST_DESIGN.md`).
- All 6 active files were swept 2026-05-03 (env_block.py, tokens.py, test_block_l.py, TEST_DESIGN.md, W6_notebook_ux.md, V5_PHASE_2_PLAN_v3.md). Historical `wave_5_deep/` + `codex_reviews/` files left as audit history.

## 2. web_fetch — DROP per user (2026-05-03)

- Remove `web_fetch` from `tools/registry.py` (do NOT register).
- Add module-level `raise NotImplementedError("web_fetch disabled per user 2026-05-03 — SageMaker is VPC-isolated, no outbound. SSRF guard kept as documentation only.")` in `tools/web_fetch.py` so import-by-test still works.
- Append PORT_LOG row tagged `DECISION-DROP-PER-USER` citing user message + this hint file.
- Update SYNTHESIS_MASTER.md tools table to mark web_fetch DROPPED (not deferred).
- ADR row in V5_DESIGN_DECISIONS.md.

## 3. v5 learning HTML — ADD a new Block "U" at end (after K, before R-tier)

User's HTML-purpose memory (`feedback_html_purpose.md`): HTMLs are learning tools. v5 needs the SAME HTML coverage v4 had. Existing `compact_v5/docs/htmls/` has 6 v4-era files (none describe v5).

### Existing HTMLs to KEEP/UPDATE/ARCHIVE
- ARCHIVE (rename to `compact_v5/docs/htmls/archive/`): `v4_architecture.html`, `PS_FLOWCHART_V4.html`
- KEEP as reference (no change): `PS_FLOWCHART_RUNNABLE.html`, `PS_DEEP_DIVE_RUNNABLE.html`, `PS_RUNNABLE_VS_LANGGRAPH.html`
- UPDATE (add v5 column + rename): `HERMES_VS_CODING_AGENT_v4.html` → `HERMES_VS_v4_VS_v5.html`
- UPDATE: `PS_DEEP_DIVE_RUNNABLE.html` — add side-panel "ported to v5 at file:line" annotations on every Runnable subsystem

### NEW HTMLs to CREATE (Block U deliverable)
- `compact_v5/HTML/v5_architecture.html` — v5 file tree + per-module purpose + Bedrock data flow + cache layout (~2000 LOC)
- `compact_v5/HTML/PS_FLOWCHART_V5.html` — core loop, sub-agent dispatch, compact, memory, dream, cache, approval (Mermaid) (~1500 LOC)
- `compact_v5/HTML/v5_complete.html` — single-file, inline CSS/JS, no CDN; 7 tabs (~3000 LOC):
  1. Architecture (file tree + per-module purpose)
  2. Prompts (every system + tool + sub-agent + memory + compact prompt extracted inline with explanation)
  3. Tools (each of v5's tools with examples + anti-patterns + token cost)
  4. PS_problems FIXED (1-7 with v4 file:line + v5 file:line + lock test name)
  5. v5 vs v4 vs Runnable vs Hermes vs LF (cross-comparison aligned table per axis)
  6. Block-by-Block log (Blocks 0..K with commit sha + Codex iters + tests delta + PORT_LOG rows)
  7. R-tier results (filled after R-tier runs)
- `compact_v5/HTML/v5_PS_PROBLEMS_FIXED.html` — each of PS#1-7 with v4 file:line + v5 file:line + lock test name + before/after diff (~800 LOC)

### Block U sequence
1. U-1 scaffold `compact_v5/HTML/` + template (header/nav/theme/Mermaid include/tab JS)
2. U-2 `v5_architecture.html` (read every v5 module + write inline doc)
3. U-3 `PS_FLOWCHART_V5.html` (Mermaid for core loop / sub-agent / compact / memory / dream / cache / approval)
4. U-4 `v5_complete.html` Prompts tab — extract every prompt (system + 19 sections + 24 tool prompts + sub-agent + memory + compact + Coordinator) inline
5. U-5 `v5_complete.html` PS_problems tab — read `_phase_2/wave_3/RISK_SURFACE.md` + grep v4/v5 file:line for each PS#1-7
6. U-6 `v5_complete.html` cross-comparison tab — v4 × Runnable × Hermes × LF × v5 aligned (axis = building block; cell = file:line ref + ported-to-v5 status)
7. U-7 `v5_complete.html` Block log tab — read every commit msg + Codex transcript + PORT_LOG row + tests delta
8. U-8 archive + UPDATE existing HTMLs (Hermes column added, v4 archived)
9. U-9 Playwright validation — open every HTML, screenshot, verify Mermaid renders, mobile (375px) responsive
10. U-10 Codex AXIS A/B/C review of HTML structure + content fidelity → user-approval gate

NOT optional — user reads HTML, not source code. Lands as separate commit + Codex review + user-approval gate.

## 4. Per-Block discipline (unchanged but reinforced)

Every Block tag commit MUST update:
- `_status/V5_BUILD_STATUS.md` — Block-row table + last commit sha + tests delta
- `_status/V5_RUNNABLE_PORT_LOG.md` — append row(s) for every adoption/drop/decision
- `_status/V5_DESIGN_DECISIONS.md` — append ADR(s) for every non-trivial choice
- `_status/codex_reviews/block-<X>.md` — full Codex transcript (every iter)
- `MAIN/changelogs/CHANGELOG_v5.0.1.md` — Block summary
- `SESSION_STATE.md` — current state pre-commit
- `~/.claude/projects/d--Github/memory/project_v5_phase2_final_state.md` — Block-progress table row update
- `git push sageagent v5-build` AND `git push sageagent v5.0.1-block-<X>` (the tag)

If any of the above missing → commit is INCOMPLETE, do NOT tag, fix in same commit.

## 6. Changelog file (Block K reconcile)

Two changelog locations exist; pick ONE for v5.0.1 per Block K:
- `compact_v5/CHANGELOG.md` (root, single file, currently used by worker — append-only per-Block sections)
- `compact_v5/MAIN/changelogs/CHANGELOG_v5.0.1.md` (planned in V5_PHASE_2_PLAN_v3.md but never created)

**Decision**: keep root `CHANGELOG.md` as the canonical v5.0.1 changelog (worker is already using it; matches v4 convention `compact_v4/CHANGELOG.md`). In Block K, ADD a header note pointing here from `MAIN/changelogs/`. Don't duplicate.

## 7. R-tier ENHANCED — add R13-R16 (per user 2026-05-03)

Original R1-R12 ($3-7) proves "v5 no semantic bugs" but does NOT prove coding accuracy/multi-file/debugging/long-session. ADD:

| # | Scenario | Catches | Cost |
|---|---|---|---|
| **R13 — Coding accuracy** | 10 HumanEval-mini Python tasks → agent writes → python_exec runs assertions → score pass/fail | Empirical coding accuracy | $1.00 |
| **R14 — Multi-file refactor** | 5-file Python project → "rename class Foo to Bar, update all callers + tests, verify pytest green" | Cross-file coordination + verification loop | $1.50 |
| **R15 — Bug detection** | 3 planted bugs (off-by-one + race + encoding) → "find + fix + justify" → score bugs-found + correct-fix + no-false-positives | Debugging ability | $1.00 |
| **R16 — Long session** | 200-turn build a Flask CRUD with tests; multiple compact cycles; final pytest passes | Memory + compactor + cache cohesion under sustained load | $2.00 |

R-tier total: $7 → $12-13 (still under $50/mo cap).

**Metrics collection (no extra cost)**: every R-test logs to `r_tier_metrics.jsonl` — `{test, tokens_in, tokens_out, cache_hit_pct, wallclock_s, tool_calls, completed}` — then aggregate report goes into `v5_complete.html` Block U tab 7.

## 8. Block V — Comparative benchmark (RECOMMENDED, not yet in plan)

After R-tier, ONE optional Block V: head-to-head v5 vs v4 vs Runnable on 5 representative coding tasks with same Sonnet 4.5. ~$15-20.

**5 tasks × 3 systems × Sonnet 4.5 = 15 runs:**
1. Refactor 200-line Python module (extract / rename / type-hint)
2. Debug planted "wrong index" bug in 50-line script
3. Multi-file feature (add CSV export to 5-file project)
4. Explore "what does this codebase do?" on 20-file unfamiliar repo
5. Long task: build minimal Flask CRUD with tests, ~50 turns

**Scoring rubric**: completion (binary) / accuracy via tests (binary) / token cost / wallclock / # tool calls / coherence 1-5. Anonymize output and let user OR judge LLM score.

Output: scoring table in `v5_complete.html` "v5 vs Runnable vs v4" tab. Without this, "v5 > Runnable > v4" claim stays architectural only — empirical proof requires this Block. User must APPROVE Block V before scheduling.

**R-tier + Block V combined**: ~$25-35. Gets EMPIRICAL "v5 > Runnable > v4" with screenshot-able evidence.

## 9.5. Codex review prompt files — WHICH TEMPLATE TO USE WHEN

Two review-prompt files exist. Use the right one for the right job:

| Situation | Template file | Codex command |
|---|---|---|
| Reviewing a Block code change (Block 0..N, T, J, K, U) | `compact_v5/_status/CODEX_REVIEW_TEMPLATE.md` | already in use, 50 iters successful |
| **R-tier test PRE-FLIGHT (before AWS call)** | `compact_v5/_status/R_TIER_REVIEW_TEMPLATE.md` **§ TEMPLATE A** | see below |
| **R-tier test FAILED (diagnosis before retry)** | `compact_v5/_status/R_TIER_REVIEW_TEMPLATE.md` **§ TEMPLATE B** | see below |
| **R-tier test PASSED (false-positive sanity check)** | `compact_v5/_status/R_TIER_REVIEW_TEMPLATE.md` **§ TEMPLATE C** | see below |
| Block V head-to-head test design + result | same R_TIER_REVIEW_TEMPLATE.md (use A/B/C as applicable) | same |
| Final full-codebase Codex review (after all Blocks done) | `CODEX_REVIEW_TEMPLATE.md` adapted for full-codebase scope | manual |

### Exact Codex command pattern (used at every review)

```bash
# Always: kill any zombie codex processes first (per BUILDER_PROMPT.md hang-fix)
taskkill //F //IM codex.exe 2>/dev/null || true

# Then run Codex with the strict model + reasoning level + read-only sandbox
codex exec --full-auto -s read-only -m gpt-5.5 -c model_reasoning_effort="high" "$(cat <<'EOF'
{paste filled-in template here, with all {{...}} placeholders replaced}
EOF
)"

# Save output to:
# - Block reviews: compact_v5/_status/codex_reviews/block-<X>-iter<N>.md
# - R-tier reviews: compact_v5/_status/codex_reviews/r-tier-<TEST>-phase<A|B|C>-iter<N>.md
# - Block V reviews: compact_v5/_status/codex_reviews/block-v-<TASK>-<v4|v5>-phase<A|B|C>-iter<N>.md

# After saving, ALSO append a row to compact_v5/_status/r_tier_review_log.md
```

### Per-test review log (mandatory)

After every R-tier or Block V test completes (PASS, FAIL+ESCALATE, or READY), append a row to `compact_v5/_status/r_tier_review_log.md`:

| Test | Date | PHASE A iters | AWS calls used | PHASE C iters | PHASE C verdict | Final | Cost spent | Cost cap | Reviewer files |
|------|------|---------------|----------------|---------------|-----------------|-------|-----------|----------|----------------|
| R1 | 2026-05-04 | 1 (APPROVE) | 1 | 0 | n/a | READY | $0.42 | $1.00 | r-tier-R1-phaseA-iter1.md, r-tier-R1-phaseC-iter0.md (none) |

If file `r_tier_review_log.md` doesn't exist when first R-test runs, create it with the header row + the test's row.

### Worker checklist for EACH R-tier or Block V test

1. Read TEMPLATE A (PHASE A pre-flight) from `R_TIER_REVIEW_TEMPLATE.md`
2. Fill `{{...}}` with this test's specifics (test name, claim, cost cap, model, fixture paths)
3. Worker self-review FIRST (read own diff, sanity-check assertions)
4. Run Codex with TEMPLATE A → save to `codex_reviews/r-tier-<TEST>-phaseA-iter1.md`
5. Both APPROVE? → AWS gate OPENS → run AWS call #1
6. PASS path → Codex TEMPLATE C (sanity) → if GENUINE_PASS: log + READY + next test
7. FAIL path → Codex TEMPLATE B (diagnosis) → if APPROVE_FIX_AND_RETRY: apply fix + re-run TEMPLATE A on fixed test → AWS call #2
8. AWS call #3 = LAST. If still failing → ESCALATE to user (do NOT spend AWS call #4)
9. Append row to `r_tier_review_log.md`
10. ONLY after row appended → move to next test

## 10. Test → review → fix → review → ready LOOP (per R-test, per Block V comparison)

User confirmed 2026-05-03 with STRICTER constraint: **AWS invocation only when BOTH Claude Code (worker) AND Codex APPROVE that test is READY. Hard cap = 3 AWS calls per test, total (not "3 retries on top of an initial run").**

The expensive operation is the AWS call. NEVER spend AWS money on an un-vetted attempt. Both reviewers must agree before each AWS call.

```
PER_TEST_LOOP (max 3 AWS calls total, period):

  PHASE A — PRE-FLIGHT (no AWS spend):
    1. Worker prepares test code + scenario fixtures + assertions
    2. Worker self-review: read own diff, sanity check assertions cover scenario
    3. If worker unsure → DO NOT call Codex yet, refine first
    4. Codex AXIS A/B/C review on test code + scenario design
       (Codex sees the test definition, NOT the AWS result)
    5. If Codex APPROVE → AWS gate OPEN (proceed to PHASE B)
       If Codex APPROVE_WITH_FIXES → apply fixes → re-review (loop A)
       If Codex REJECT → revise → re-review (loop A)
    6. AXIOM: zero AWS calls have happened yet. Loop A is free.

  PHASE B — AWS CALL #1 (first real-Bedrock invocation):
    7. AWS call #1 runs (cost: up to test's session_cost_limit cap)
    8. PASS path:
       a. Worker self-review: tokens / wallclock / tool-calls / output integrity
       b. Codex AXIS A/B/C review on results
       c. BOTH APPROVE → log r_tier_metrics.jsonl → tag test READY → next test
       d. EITHER says fix-needed → go to PHASE C
    9. FAIL path: go to PHASE C

  PHASE C — DIAGNOSIS (no AWS spend):
   10. Worker self-review: error + agent log → root-cause hypothesis
   11. Codex AXIS A review on diagnosis
   12. BOTH APPROVE diagnosis → propose fix
   13. Worker reviews fix proposal
   14. Codex AXIS B review on fix
   15. BOTH APPROVE fix → apply + commit
   16. Re-run PHASE A (pre-flight) on the FIXED test before next AWS call
   17. AXIOM: NO AWS call until PHASE A passes again

  PHASE D — AWS CALL #2 (only if both reviewers approved fix in PHASE C):
   18. AWS call #2 runs
   19. PASS → log + READY + next test
   20. FAIL → PHASE C again (diagnosis #2)

  PHASE E — AWS CALL #3 (LAST attempt, only if both reviewers approved fix #2):
   21. AWS call #3 runs
   22. PASS → log + READY + next test
   23. FAIL → STOP + ESCALATE to user (cap reached)
```

### HARD RULES (no exceptions)

1. **Max 3 AWS calls per test, period.** Not "3 retries plus 1 initial" — exactly 3 invocations of real Bedrock per test.
2. **EVERY AWS call requires BOTH worker AND Codex APPROVE in the immediately preceding PHASE A or PHASE C review.** No silent skip. No "worker thinks it's fine, ship it." No "Codex didn't fully review but probably ok."
3. **If worker and Codex disagree → DEFER the AWS call.** Resolve disagreement via additional review iteration BEFORE spending AWS money.
4. **Cumulative cost per test must not exceed `session_cost_limit` cap.** If retry would push over cap, STOP + ESCALATE before the AWS call.
5. **No AWS call during PHASE A or PHASE C.** All review + diagnosis work is free; AWS only fires in PHASE B / D / E.

### Mandatory ESCALATE-to-user triggers

Worker MUST stop and ask user (not autonomously continue) if:
1. 3 AWS calls used + still failing
2. Cost cap hit on a test (could be on call #1 if scenario is pathological)
3. Codex returns BLOCKER (not CHANGES_REQUESTED) — architectural problem
4. Fix would require NEW Block (scope expansion)
5. Real-Bedrock returns auth/quota/region/throttle error — infrastructure issue, NOT counted as a "failed test attempt" (don't burn budget on infra issues)
6. Two consecutive R-tests fail at AWS call #1 — possible systemic issue, pause for review
7. Worker and Codex cannot reach agreement after 3 review rounds in PHASE A or PHASE C

### Block V same discipline (with one nuance)

Each Block V task (3 tasks × 2 systems v4 + v5 = 6 AWS-side runs) follows the same loop.

- v5-side run fails → bug in v5 → fix → re-test (consumes from v5's 3-call cap)
- v4-side run fails → v4 bug (existing, not v5's job to fix). Document the v4 failure as a v5-WIN data point. Do NOT spend additional v4-side AWS calls trying to fix v4. v4 stays at 1 AWS call per task.

So Block V actual cap = 3 (v5) + 1 (v4) = 4 AWS calls per task max × 3 tasks = 12 max AWS calls for entire Block V.

## 11. Codex still STRICT

## 8. Codex still STRICT

`codex exec --full-auto -s read-only -m gpt-5.5 -c model_reasoning_effort="high"` per iter. Always APPROVE required (no max-iter skip). 3-stage retry on internet failure (kill zombies → wait+retry → fallback gpt-5.3-codex → ESCALATE if all fail).
