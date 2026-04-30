# V5 Phase 10 Changelog — Skills + auto-trigger + Hermes filter (PS Issue #1)

Date: 2026-04-30
Tag (target): v5-phase-10
ADR: ADR-016
PORT_LOG rows: #025, #026, #027, #028, #029

## Goal (V5_PLAN.md §Phase 10)

Port v4's SkillManager + 10 skills directories byte-for-byte. Add Hermes-style skill filtering by available tools. Acceptance:
- All 10 skills load.
- Auto-trigger respects v4.9.6 default-OFF.

## What landed

### skills/manager.py (PORT_LOG #025 — PORT, FAITHFUL-WITH-JUSTIFIED-ADAPTATION)
PORT port of v4's `SkillManager` (sagemaker_agent.py:2684, ~470 LOC). v5 takes
`workspace` + `skills_dir` + `enable_auto_trigger` as constructor parameters
(v4 read from globals). Full v4 surface preserved: discover / list_skills /
read_skill / activate / deactivate / discover_relevant / list_for_prompt /
propose_patch / list_proposals / get_latest_proposal / apply_proposal.

Phase-10 frontmatter parser upgrade (Codex Phase-10 fix): now handles YAML
list dash-form for `requires_tools` and `triggers`, in addition to v4's CSV
scalar form.

### skills/<10 dirs>/ (PORT_LOG #029 — PURE COPY, FAITHFUL)
10 v4 production skills copied byte-for-byte:
batch / clara / design / html / reflexion / report / review / security-review
/ simplify / verify.

Codex Phase-10 confirmed all 10 SKILL.md hashes match v4.

### tools/skill.py (PORT_LOG #026 — ADAPT, FAITHFUL post-fix)
Skill tool with subcommand surface (list / read / activate / deactivate).
Marked `should_defer=True` per Phase 7 deferred set. Lazy-built singleton
with reset-before-early-return ordering. Respects `CONFIG.enable_skills`
gate (v4 parity).

### tools/skill_propose_patch.py (PORT_LOG #027 — ADAPT, FAITHFUL-WITH-JUSTIFIED-ADAPTATION)
Opt-in self-patching tool. `CONFIG.enable_skill_patching=False` (default)
returns no-op message. When enabled: 8 safety rails preserved — propose-
not-apply, required reason + full new_content, never overwrites live
SKILL.md, time-stamped + uuid-suffixed filenames (Phase 10 fix), per-skill
`.proposed/`, audit-log on propose (Phase 10 fix), backup-on-apply
(Phase 10 fix). SnapshotManager singleton wiring deferred to Phase 11 UX.

### Hermes filter (PORT_LOG #028 — ADAPT, FAITHFUL post-fix)
PS Issue #1 fix. Optional `requires_tools` frontmatter; skills declaring
it are filtered out when their required tools aren't in the active set.
Backwards compatible — skills without the field are never filtered.

`QueryEngine(skill_manager=...)` invokes the filter per turn (Codex
Phase-10 BLOCKER fix): injects active skill body into system prompt
+ appends "Skills Relevant to This Task" reminder to the user turn.

### Tests (33 new)
- `tests/unit/test_skill_manager.py` (21 tests, including 4 Codex-fix lock tests)
- `tests/integration/test_skills.py` (12 tests, including 5 Codex-fix lock tests)
- 1 line in `tests/integration/test_query_engine.py` (skill exclusion in deferred test).

## Test results

- Last full `pytest` run: 2026-04-30 — **392 passed + 4 skipped** (was 359+4
  in Phase 9; +33 net new tests).
- Aggregate audit: all 7 metrics PASS.

## Codex review

- First pass: REJECT. 1 BLOCKER + 4 HIGH + 2 MEDIUM + 2 UNDECLARED_PATTERN.
  - **BLOCKER**: SkillManager not wired into runtime loop.
  - **HIGH**: frontmatter parser doesn't handle YAML lists.
  - **HIGH**: proposal filename collisions on same-second writes.
  - **HIGH**: 8 safety rails not all preserved (no audit, no snapshot).
  - **MEDIUM**: singleton reset early-return ordering.
  - **MEDIUM**: `enable_skills` config gate dropped.
  - **UNDECLARED**: runtime integration gap, enable_skills parity gap.
- All 8 issues addressed in same commit; 9 lock tests added.
- Post-fix: AXIS A PASS, AXIS B 3 FAITHFUL / 2 ADAPTED / 0 DRIFTED.
- Saved at: `_status/codex_reviews/phase-10.md`.

## Better than v4

- v4 skill machinery is inline in the monolith (~470 LOC at line 2684).
  v5 splits into `skills/` package + 2 deferred tools — testable in
  isolation, swappable, reviewable.
- v5's SkillManager parses YAML list dash-form for `requires_tools` and
  `triggers`. v4 only handles CSV scalar.
- Proposal filenames now have UUID suffix (no same-second collisions).
- Best-effort backup file on apply (`.skill_backup_<ts>` sibling) when
  SnapshotManager isn't wired — local reversibility even before Phase 11.

## Better than Hermes

- Hermes's skill-filtering-by-available-tools pattern is ported as the
  optional `requires_tools` frontmatter field. v5 makes this BACKWARDS
  COMPATIBLE — skills without the field never get filtered (the 10 v4
  skills don't declare it). Hermes has no such fallback.
- v5 wires the filter into the actual runtime loop — `QueryEngine(skill_manager=...)`
  invokes `discover_relevant(active_tools=visible_tool_names)` per turn so
  the model only sees relevant suggestions.

## Next phase

Phase 11 — Notebook UX + entry + thinking/budget UI (PS Issue #4). Port
v4's chat.ipynb + chat_ui.py. Wire IterationBudget, thinking budget,
diff-widget, skill_propose_patch UX (the SnapshotManager + AuditLogger
singletons that Phase 10's safety rails reference).
