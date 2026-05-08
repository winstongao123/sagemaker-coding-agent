# L2 — Learning_Factory docs/ + state/ + root .md DEEP SCAN

**Date**: 2026-05-01
**Scope**: `D:/Github/Learning_Factory/docs/`, `state/`, root `*.md` (CLAUDE.md, README.md, CHANGELOG.md, NEW_PC_PROMPT.md, CRITICAL_HOOK_SURROGATE_FIX.md), plus `templates/` (procedural overlap), `commands/`, `agents/designer.md`. **No `design-log/` exists** (assumption in prompt was wrong; design artifacts live under `docs/audits/<date>-<topic>/`). **No root-level `STATE.md`, `AGENT_STATUS.md`, or `PORT_LOG.md`** — those exist only as `templates/STATE.md` and `docs/[3]_STATE.md` (the LF repo's own state file, not a portable shape).
**Lens**: Block K = STATE/RESUME + AXIS C + per-block approval + PORT_LOG schema.
**Constraints**: v5.0.1 single-user SageMaker, Bedrock-only, v4 chat.ipynb canonical UI, no deferrals.
**Comparison anchors**:
- v4: `compact_v4/MAIN/agent/sagemaker_agent.py`
- Wave 5 prior: `compact_v5/_phase_2/wave_5/LF_NEW_FUNCTIONALITY.md` (5 NEW patterns surfaced)
- Plan v3 Block K, Q1 matrix.

---

## Files audit (full read, line-by-line)

| Path | Lines | Status | Procedural payload for v5 Block K |
|---|---|---|---|
| `CLAUDE.md` | 130 | READ | Rule 1 STATE.md / Rule 2 one-agent-one-job-one-output / Rule 3 know-what's-done. CSO + two-stage review + task granularity additions. |
| `README.md` | 104 | READ | Folder map, install instructions, modes table. Zero procedural beyond CLAUDE.md. |
| `CHANGELOG.md` | 486 | READ | Pattern-A demonstration. Multi-version journal (1.3 → 1.7.6 → 2026-04-28 hardening). Demonstrates "every code change updates CHANGELOG" enforced by hook. |
| `NEW_PC_PROMPT.md` | n/a | LISTED | Bootstrap prompt for fresh machine (3 commands). |
| `CRITICAL_HOOK_SURROGATE_FIX.md` | n/a | LISTED | Incident postmortem — UTF-16 lone surrogate bug. Doctrine: incident docs at root. |
| `VERSION` | 1 | LISTED | Single-line version file. |
| `docs/CHANGELOG_PROTOCOL.md` | 104 | READ | **Pattern A + C hybrid doctrine**. Required structure, ship-time workflow, binding rules. **HIGH-VALUE for Block K**. |
| `docs/PREFLIGHT_PROTOCOL.md` | 182 | READ | 5-category pre-flight checklist (hooks / permissions / external reviewer / working tree / session state). `/preflight` skill spec, FAIL/WARN/PASS reporting, audit-log to `~/.claude/logs/preflight-<ts>.json`. **HIGH-VALUE**. |
| `docs/SMOKE_TEST_PROTOCOL.md` | 180 | READ | Real-CLI smoke vs unit fakes; `REAL_CLI=1` env gate; semantic assertions; per-project minimum suite (1 CLI roundtrip + 1 stream-json parse + LLM-quality path). |
| `docs/SKILL_PROMOTION_PROTOCOL.md` | 151 | READ | Skill vs memory taxonomy, four promotion triggers, SKILL.md frontmatter shape, `state/skill-proposals/` landing zone, supersession rules. Wave 5 prior already extracted this. |
| `docs/SETTINGS_PROTOCOL.md` | 121 | READ | `.claude/settings.json` per-project doctrine: allow/deny lists, expected residual prompts on `.claude/**` writes, onboarding checklist, why commit settings.json. |
| `docs/ADVANCED_PATTERNS.md` | 148 | READ | **D-0090 red-team protocol**. 10 patterns scanned → 4 ADOPT-light + 6 REJECT with reasons. Codifies "every external scan must red-team before adoption" as binding. |
| `docs/IMPLEMENTATION_PLAN.md` | 188 | READ | 3-phase install plan (global foundation → gstack skills → Ralph). Older (2026-04-03), largely obsolete. Procedural value: phased + decision-gated install model. |
| `docs/REFERENCE_CHECKLIST.md` | n/a | READ-skim | Repo evaluation checklist (skip — content layer not procedural). |
| `docs/DETAILED_LEARNING_CHECKLIST.md` | n/a | READ-skim | Per-repo learning protocol — overlap with `templates/LEARN_AND_EXTRACT.md`. |
| `docs/COMPETITIVE_LANDSCAPE.md` | n/a | READ-skim | 30-repo evaluation table (content, not procedural). |
| `docs/REUSABLE_MODULES.md` | 100+ | READ (head) | 72-module catalogue. Verification field (VERIFIED/LISTED) is the **only procedural cell** — dual-tier source-evidence flagging. |
| `docs/FACTORY_BLUEPRINT.md` | n/a | READ-skim | Master plan, supplanted by FACTORY_VISUAL.html. |
| `docs/PS_RUNNABLE_ARCHITECTURE.md` | n/a | READ-skim | Architecture comparison (content layer). |
| `docs/PS_FACTORY_STATUS_2026-04-05.md` | n/a | READ-skim | Status snapshot. |
| `docs/PS_FACTORY_STATUS_2026-04-06.md` | n/a | READ-skim | Status snapshot. |
| `docs/PS_enforcement_research_2026-04-04.md` | n/a | READ-skim | Hook enforcement research. |
| `docs/DEMO_EXAMPLES.md` | n/a | READ-skim | Demo prompts. |
| `docs/NEXT_SESSION_RUNNABLE_VS_LANGGRAPH.md` | n/a | READ-skim | Open question pad. |
| `docs/[1]_INSTALL.md`, `[2]_QUICK_REFERENCE.md`, `[3]_STATE.md` | 3 files | READ | Numbered-prefix doc-ordering convention. `[3]_STATE.md` = LF repo's own state, ASCII-bracket prefix forces sort order in file lists. |
| `docs/PS_FACTORY_MANUAL.md` | n/a | READ-skim | Manual-style overview. |
| `docs/audits/2026-04-20-deep-scan/` | 14 files | READ key reports (00 + 04 + 09) | **D-0091 round-2 audit**. 13 repos under "harness lens". Decision table: 23 ADOPT / 5 ADOPT-LIGHT / 15 COVERED / 12 REJECT. Per-repo report file shape: dated subdir + numbered files + final `00-FINAL-DECISION-TABLE.md`. **HIGH-VALUE shape for v5 audit dirs**. |
| `docs/audits/2026-04-21-ux-review/` | 2 files | READ | 4-agent / 2-team UX review with grade matrix per persona. Synthesis file aggregates. |
| `docs/audits/2026-04-21-a-plus-review/` | 3 files | READ | 3 critic agents (value / timing / cost) red-team an A+ proposal. Each verdict matrix has 80/20 alt column. **Three-critic protocol** = exactly what AXIS A/B/C wants. |
| `state/tmp/commit-msg.txt` | n/a | LISTED | Sole `state/` content — scratch commit-msg holder. **No state/ persistence shape exists in LF**; LF leaves that to per-project STATE.md. |
| `state/skill-proposals/` | n/a | NOT PRESENT | Documented in protocol; not created until first promotion. Confirms "lazy-create" doctrine. |
| `templates/STATE.md` | 33 | READ | 7-section template: Goal / Current Phase / Done / NOT Done / Decisions / Files Changed / Blockers. **Direct shape for v5 STATE.md**. |
| `templates/CLAUDE_PROJECT.md` | 32 | READ | Per-project rule template: session-start protocol, session-end protocol, remote-agent rules, git rules. |
| `templates/VERIFICATION_STRATEGY.md` | 45 | READ | Verify-by-change-type table + adversarial probes + check output format ending in `VERDICT: PASS/FAIL/PARTIAL`. **VERDICT shape directly portable**. |
| `templates/CODING_PRINCIPLES.md` | 41 | READ | Don't/Do tables + git rules. |
| `templates/LEARN_AND_EXTRACT.md` | 183 | READ | 5-phase repo-learning recipe (Scan / Deep dive / HTML / Extract / Apply). One session per phase. |
| `templates/LEARN_CODEBASE.md` | n/a | READ-skim | Simpler variant of LEARN_AND_EXTRACT. |
| `templates/BUILD_HTML_REPORT.md` | n/a | READ-skim | HTML doctrine (Mermaid syntax safety). |
| `templates/HARNESS_SETUP.md` | n/a | READ-skim | Env setup. |
| `commands/codex-review.md` | 117 | READ | 2-tier fallback Codex review. Tier 1 CLI with rich-context prompt assembly; Tier 2 structured self-review with rubric checklist + 0-100 scoring + PASS/FAIL gate. **Block K reviewer protocol**. |
| `commands/design.md` | 82 | READ | `/design` command spec — design.md doc shape, gate semantics ("WAIT for user pick"), when-to-use vs `/plan`. |
| `commands/factory-report.md` | n/a | READ-skim | OBSERVE-REPORT loop with accept/reject feedback. |
| `commands/promote-to-skill.md` | n/a | READ-skim | Skill-promotion command stub. |
| `commands/reflexion.md` | n/a | READ-skim | Self-refinement loop spec. |
| `commands/rollback.md` | n/a | READ-skim | Shadow-git rollback CLI. |
| `agents/designer.md` | 60+ | READ | Read-only designer agent spec — Read/Grep/Glob/WebFetch/WebSearch only, gate "MUST WAIT", problem→constraints→options→chosen→validation. |
| `agents/db-reviewer.md`, `test-runner.md`, `api-reviewer.md`, `env-validator.md` | 4 files | LISTED | Specialist read-only reviewer agents. |
| `skills/mermaid-html-safe-syntax.md` | n/a | LISTED | Sole skill (mermaid escaping). |
| `memories/*.md` | 30 files | LISTED | Portable preference files. Procedural value already in user's MEMORY.md. |

**Total .md inspected**: ~70 (full read or targeted skim). LF docs are short + structured as advertised — full coverage cheap.

---

## Patterns table (procedural finds for Block K)

Each row = one procedural pattern. "Block K fit" = how cleanly it absorbs into v5.0.1 Block K (STATE/RESUME + AXIS C + per-block approval + PORT_LOG).

| # | Pattern | Source file | What it gives | Block K fit | v5.0.1 status |
|---|---|---|---|---|---|
| LF-DOC-1 | Pattern A + C changelog hybrid (CHANGELOG.md one-liners + `docs/releases/<v>/{notes,decisions,blockers,migration}.md`) | `docs/CHANGELOG_PROTOCOL.md` | Doctrine: short index + deep archive. Required ship workflow. Binding rules. | DIRECT — replace v5 ad-hoc CHANGELOG with this shape | NEW for plan v3 |
| LF-DOC-2 | Pre-flight 5-category checklist (hooks / perms / reviewer / tree / session) with PASS/FAIL/WARN reporting + audit log | `docs/PREFLIGHT_PROTOCOL.md` | Run-before-block-start safety verification. `/preflight` skill spec. | DIRECT — Block K PRE-BLOCK gate | NEW for plan v3 |
| LF-DOC-3 | Smoke vs unit two-tier test gate (`REAL_CLI=1` env-gated, semantic-not-string assertions, 5-test cap, runs before ship + after refactor + nightly) | `docs/SMOKE_TEST_PROTOCOL.md` | Catches integration drift unit fakes hide. | PARTIAL — Bedrock-only v5 has no Anthropic CLI, but the structural pattern (env-gate the slow real-thing) is portable to Bedrock smoke (`REAL_BEDROCK=1`) | NEW (light) |
| LF-DOC-4 | D-0090 red-team protocol — every external scan triggers 3-agent stress-test BEFORE adoption (kills 6/10 patterns on average) | `docs/ADVANCED_PATTERNS.md` | Anti-tech-stacking discipline. Documents "considered and rejected with reasons" alongside accepts. | DIRECT — AXIS C "considered + rejected" must follow this. Wave 5 deep is itself running this protocol. | ALREADY-IN-PLAN (AXIS C) |
| LF-DOC-5 | Three-critic red-team (value / timing / cost) per major proposal, each with verdict matrix and 80/20 alternative column | `docs/audits/2026-04-21-a-plus-review/{01,02,03}.md` | Anti-A+-theater. Critics produce DROP / DEFER / KEEP / MODIFY verdicts. | DIRECT — AXIS A/B/C per-block reviews can adopt this 3-critic shape verbatim | ALREADY-IN-PLAN (extend) |
| LF-DOC-6 | Audit dir shape: `docs/audits/<YYYY-MM-DD>-<topic>/` + numbered per-source reports (`01-X.md` ... `13-Y.md`) + `00-FINAL-DECISION-TABLE.md` synthesis | `docs/audits/2026-04-20-deep-scan/` | Sortable filenames force read-order; final synthesis is always at top alphabetically. Reproducible across audit cycles. | DIRECT — wave_5_deep should follow this shape; v5 future audits same | NEW (apply to wave_5_deep) |
| LF-DOC-7 | `[N]_FILENAME.md` numbered prefix in `docs/` for ordered onboarding paths (`[1]_INSTALL.md`, `[2]_QUICK_REFERENCE.md`, `[3]_STATE.md`) | `docs/[1-3]_*.md` | Solves doc-ordering ambiguity without forcing a manual TOC | LIGHT — apply to `compact_v5/_phase_2/` if onboarding sequence matters | OPTIONAL |
| LF-DOC-8 | VERIFIED vs LISTED dual-tier evidence flag in catalogues — agent must mark whether it actually read source or just README | `docs/REUSABLE_MODULES.md` | Forces honest evidence claims. Catches "read README, claimed feature" drift. | DIRECT — PORT_LOG schema column "evidence_tier: VERIFIED / LISTED" | NEW for PORT_LOG |
| LF-DOC-9 | Skill-promotion workflow (mistake → SKILL.md proposal → owner-gated → `~/.claude/skills/`) with `state/skill-proposals/` landing zone | `docs/SKILL_PROMOTION_PROTOCOL.md` | Turns transient learnings into durable skills. Skill vs memory taxonomy. Supersession rules. | INDIRECT — Wave 5 prior already extracted this; v5 Block D scope | ALREADY-IN-PLAN (wave 5) |
| LF-DOC-10 | Project `.claude/settings.json` per-project allow/deny doctrine (commit to git, expected residual prompts on `.claude/**`, onboarding checklist) | `docs/SETTINGS_PROTOCOL.md` | Reproducible per-project permissions; auditable; team-portable. | OUT-OF-SCOPE — single-user SageMaker has no per-project Claude Code settings; Bedrock has different perms layer | OUT-OF-SCOPE |
| LF-TPL-1 | STATE.md 7-section shape (Goal / Phase / Done / NOT Done / Decisions / Files Changed / Blockers) | `templates/STATE.md` | Survives compaction. Carries state between sessions. | DIRECT — v5 root `STATE.md` should follow this exact shape (already in plan v3) | ALREADY-IN-PLAN |
| LF-TPL-2 | CLAUDE_PROJECT.md session-start / session-end protocol (read STATE → report phase → wait → work → update STATE → commit/push) | `templates/CLAUDE_PROJECT.md` | Codifies the resume ritual. Remote-agent boundary rules ("only read+write to designated output file"). | DIRECT — v5 CLAUDE.md project rules section | ALREADY-IN-PLAN (extend) |
| LF-TPL-3 | VERIFICATION_STRATEGY check-output format (Command run / Output observed / Result PASS-FAIL) ending with `VERDICT: PASS/FAIL/PARTIAL` | `templates/VERIFICATION_STRATEGY.md` | Forces evidence per check. Adversarial probes always (concurrency / boundary / idempotency / orphan). | DIRECT — Block K per-block verification report shape; AXIS C reports same | ALREADY-IN-PLAN (formalize) |
| LF-TPL-4 | LEARN_AND_EXTRACT 5-phase recipe (Scan→Deep dive→HTML→Extract→Apply) — one session per phase, STATE.md carries between | `templates/LEARN_AND_EXTRACT.md` | Repeatable repo-study workflow with explicit phase outputs | INDIRECT — wave_5_deep is already running a variant; v5 doesn't need recipe | OUT-OF-SCOPE |
| LF-CMD-1 | `/codex-review` 2-tier fallback (CLI Tier 1 with rich-context prompt assembly; structured self-review Tier 2 with rubric + 0-100 score + PASS/FAIL gate at 90) | `commands/codex-review.md` | Independent reviewer never blocks because of tooling. Always falls back to checklist. | DIRECT — v5 Block K reviewer = Codex (Bedrock-skip per user feedback `feedback_codex_skip_bedrock_patches.md` for UI/prompt-only changes; use for general code) + structured self-review fallback | ALREADY-IN-PLAN (clarify) |
| LF-CMD-2 | `/design` command + designer agent (read-only, 2-3 options each with cost/complexity/risk L/M/H, MUST WAIT for option pick) | `commands/design.md` + `agents/designer.md` | WHAT/WHY before HOW. Anti-premature-implementation gate. | DIRECT — v5 Block K per-block "design before plan" gate | NEW (light add) |
| LF-CMD-3 | `/factory-report` accept/reject feedback loop (suggestions tracked in `~/.claude/factory-improve/acceptance.json`; 2-rejection cool-down demotion) | `commands/factory-report.md` + CHANGELOG 1.7.1 | Self-improvement without statistical-attribution problems. User accept = ground truth. | OUT-OF-SCOPE — v5 single-block scope, factory-level meta-loop is Learning_Factory's job not v5's | OUT-OF-SCOPE |
| LF-CHANGELOG-1 | Headline-entry CHANGELOG with embedded full incident postmortems (root cause / fix / verification) inline (e.g. v1.7.5 cd-extraction bug, v1.7.4 surrogate API 400) | `CHANGELOG.md` | Git history alone insufficient — postmortem in CHANGELOG ensures discoverable from one place | DIRECT — v5 CHANGELOG entries should include incident-class entries with same shape | LIGHT (apply when incidents occur) |
| LF-CHANGELOG-2 | Parking lot per release ("v1.7.0 candidates", "v1.6.0 candidates") — explicit deferral list with WHY each was deferred | `CHANGELOG.md` 1.5.0/1.6.0/1.7.0 | Documents what didn't ship and why. Anti-silent-drop. | NEAR-DIRECT — but v5 NO-DEFERRALS rule forbids this. Use only for genuine post-v5.0.1 future-version candidates, not within-v5 work. | RESTRICTED-USE |
| LF-CHANGELOG-3 | Per-version "Why" prose section explaining user-decision rationale (e.g. v1.7.0 "User decision after design review: 'go B'") | `CHANGELOG.md` | Locks in decision provenance — months later you know why a thing was chosen | DIRECT — PORT_LOG already plans for "rationale" column; reinforce | ALREADY-IN-PLAN |
| LF-AUDIT-1 | "Already covered" column in pattern-decision tables — explicit map from candidate-pattern → existing v5 equivalent | `docs/audits/.../00-FINAL-DECISION-TABLE.md` (15 COVERED rows) | Forces "do we already have this?" check before accept | DIRECT — AXIS C report sections must include COVERED column | ALREADY-IN-PLAN (reinforce) |
| LF-AUDIT-2 | UX/QA review pattern: 4-agent / 2-team grading with per-tab grade table + top-N must-fix sorted by impact×cost + "what to NOT fix now" with rationale | `docs/audits/2026-04-21-ux-review/00-SYNTHESIS.md` | Disciplined "ship at A- and iterate" decision-making | INDIRECT — v5 no UX surface, but per-block "must-fix vs defer" disciplined accept/reject is portable | OUT-OF-SCOPE structurally (no v5 UX) |

**Total**: 22 patterns. **5 DIRECT-fit-for-Block-K** (LF-DOC-1, LF-DOC-2, LF-DOC-6, LF-DOC-8, LF-CMD-1). **3 NEW-light** (LF-DOC-3, LF-CMD-2, LF-CHANGELOG-1). **9 ALREADY-IN-PLAN** (rest of the relevant ones already covered by plan v3 or wave 5 prior). **5 OUT-OF-SCOPE** (LF-DOC-10, LF-TPL-4, LF-CMD-3, LF-CHANGELOG-2 (restricted), LF-AUDIT-2).

---

## ALREADY-IN-PLAN (cross-reference to plan v3 + wave 5 prior + Q1 matrix)

These appeared in the deep scan but are already specified in v5.0.1 plan. Listed for completeness — no action.

| Pattern | Where in plan v3 / wave 5 / Q1 |
|---|---|
| STATE.md 7-section shape | Plan v3 Block K STATE/RESUME spec uses identical shape (Goal / Phase / Done / Not done / Decisions / Files / Blockers) |
| AXIS C "considered and rejected with reasons" | Plan v3 Block K AXIS C explicit; D-0090 doctrine is the source |
| PORT_LOG schema with rationale column | Plan v3 Block K PORT_LOG row format includes `rationale` field |
| Per-block approval gate | Plan v3 Block K's approval flow IS the LF/CLAUDE_PROJECT session-start "report phase, wait" pattern |
| Skill-promotion workflow | Wave 5 prior `LF_NEW_FUNCTIONALITY.md` already extracted (Pattern 5: `/promote-to-skill` Block D ~200 LOC) |
| CSO + task-granularity hooks | Wave 5 prior already adopted as inherited LF hooks |
| Tool-failure detection | Wave 5 prior optional adoption |
| 4-phase Wave 5 deep audit "considered/accepted/rejected" structure | LF docs/audits/2026-04-20-deep-scan/00-FINAL-DECISION-TABLE.md provides shape; wave_5 SYNTHESIS.md follows it |
| VERDICT: PASS/FAIL/PARTIAL formal language | Plan v3 Block K verification format inherits VERIFICATION_STRATEGY.md template |

---

## OUT-OF-SCOPE for v5.0.1 Block K (with reasons)

| Pattern | Why out-of-scope |
|---|---|
| LF-DOC-10 — `.claude/settings.json` per-project doctrine | Single-user SageMaker, Bedrock-only. Claude Code settings.json layer doesn't apply inside SageMaker notebook runtime. Bedrock has its own permissions surface. |
| LF-TPL-4 — LEARN_AND_EXTRACT 5-phase recipe | wave_5_deep (this audit) is already executing a variant; v5.0.1 itself doesn't need it as part of Block K. |
| LF-CMD-3 — `/factory-report` self-improvement loop | Factory-level meta-feature for the Learning_Factory project itself, not for SageMaker agent. |
| LF-AUDIT-2 — UX/QA 4-agent grading | v5 has no UX surface beyond v4 chat.ipynb canonical UI (which is frozen). |
| LF-DOC-7 — `[N]_FILENAME.md` numbered prefix | Optional onboarding-ergonomics polish; not Block K critical path. |
| `setup.sh` / `import-memories.sh` install scripts | LF distribution mechanism, not v5 internal architecture. |
| `hooks/*.sh` (21 hooks) | Architecturally inherited via LF as global Claude Code hooks (already in user CLAUDE.md "Git Push Policy" + Wave 5 prior). v5 doesn't ship hooks. |
| Multi-project / cross-project memory patterns | v5 = single-agent single-project SageMaker; LF's 30-memory portable system is a Claude Code-wide concern, not a v5 concern. |
| `commands/rollback.md` shadow-git CLI | v5 Bedrock runtime has no shadow-git harness; OPC-style rollback isn't needed for SageMaker single-session usage. |
| `commands/reflexion.md` self-refinement loop | Useful pattern but plan v3 already covers via per-block AXIS-A retry semantics. |
| Specialist agents (db-reviewer, api-reviewer, env-validator, test-runner) | v5 single-agent design; spawning subagents not in v5.0.1 scope. |

---

## Block K refinements driven by THIS scan (3 concrete additions)

These are the only **new procedural items this scan recommends** for v5.0.1 Block K. Each is light-touch and self-contained.

1. **Audit-dir shape (LF-DOC-6)** — apply now to `compact_v5/_phase_2/wave_5_deep/`: number-prefixed per-source files + `00-SYNTHESIS.md` final aggregation. Confirms reproducibility across future audit cycles.

2. **PORT_LOG `evidence_tier` column (LF-DOC-8)** — add `evidence_tier: VERIFIED | LISTED` field to PORT_LOG schema. VERIFIED = agent read source file end-to-end; LISTED = README/doc claim only. Catches "claimed pattern, never read it" drift.

3. **CHANGELOG-as-postmortem (LF-CHANGELOG-1)** — when v5 hits a real incident (regression, hook failure, etc.), CHANGELOG entry includes Symptom / Root cause / Fix / Verification subsections inline (LF v1.7.5 + v1.7.6 are templates).

Plus **2 reinforcements** of items already in plan:

4. **Pre-flight 5-category gate (LF-DOC-2)** — Block K already has pre-block approval; explicitly map LF's 5 categories (hooks / perms / reviewer / tree / session-state) to v5's pre-block checklist so categories are covered.

5. **Three-critic AXIS A/B/C (LF-DOC-5)** — when running per-block reviews, run them as 3 separate critic prompts (value / timing / cost) rather than one combined critic. Wave 5 a-plus-review proves this catches different things.

---

## Summary

- **Files audited**: ~70 LF .md files (full + skim), full read on 30 procedurally-relevant ones.
- **`design-log/` does not exist**: design artefacts live in dated `docs/audits/<topic>/` subdirs; assumption in prompt was incorrect.
- **`state/` is near-empty**: only `tmp/commit-msg.txt`. LF deliberately leaves state persistence to per-project STATE.md; no LF-level state shape to copy.
- **Patterns surfaced**: 22. Direct-fit for v5 Block K: 5. Light-add: 3. Already in plan v3 / wave 5: 9. Out-of-scope: 5.
- **Net new for Block K from THIS scan**: 3 concrete adds (audit-dir shape, PORT_LOG evidence-tier column, CHANGELOG-postmortem shape) + 2 reinforcements (pre-flight 5-category gate, 3-critic AXIS reviews).
- **No deferrals proposed**: all out-of-scope items are genuine architecture/scope mismatches (single-user SageMaker + Bedrock-only + frozen v4 UI), not Runnable-style "punt to v5.0.2".
- **v5 vs LF on process maturity**: v5.0.1 plan v3 + wave 5 + these 3 adds = parity or better with LF on procedural surface relevant to SageMaker single-agent scope.
