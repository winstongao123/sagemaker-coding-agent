# V5 Phase 13 Changelog — Cutover + ship zip + tag v5.0.0 (FINAL)

Date: 2026-04-30
Tag (target): v5-phase-13 + v5.0.0
ADR: ADR-019
PORT_LOG rows: #036, #037

## Goal (V5_PLAN.md §Phase 13)

Build `compact_v5.zip`, update README, run final smoke + verify, tag
`v5.0.0`. v5 ships only if all prior gates met.

## What landed

### compact_v5/_rebuild_zip.py (PORT_LOG #036)
ADAPT port of v4's `_rebuild_zip.py` for v5's nested-package layout.
Walks `MAIN/agent/{core,tools,skills,runtime,prompt,ui,subagent,security,mcp}`
and flattens the `MAIN/agent/` prefix while preserving package directories.

### compact_v5/verify_ship_zip.py (PORT_LOG #037)
ADAPT port of v4's verifier. v5-specific runtime file list + 2 new
forbidden patterns (changelogs/, _status/). Result: RESULT: PASS.

### compact_v5/README.md
Top-level README. Quick-start, what's in the zip, what v5 brings vs v4
(PS Issues #1/#2/#4/#7 fixes), constraints, version notes.

### compact_v5/CHANGELOG.md
Top-level v5 release notes summarizing all 14 phases + Codex review record
+ PS Issues resolved + final acceptance metrics.

### compact_v5/MAIN/agent/memory.md + AGENT_STATUS.md
Empty placeholders so the runtime auto-load pass finds them.

## Ship verification

```
$ cd compact_v5 && python _rebuild_zip.py
Files: 95  Raw: 654.5 KB  Zip: 248.2 KB  (38%)

$ python verify_ship_zip.py
== Required runtime files at root ==
  [PASS] root/chat.ipynb
  [PASS] root/chat.md
  [PASS] root/entry.py
  [PASS] root/__init__.py
== Required package directories ==
  [PASS] core/__init__.py
  [PASS] prompt/__init__.py
  [PASS] runtime/__init__.py
  [PASS] security/__init__.py
  [PASS] skills/__init__.py
  [PASS] subagent/__init__.py
  [PASS] tools/__init__.py
  [PASS] ui/__init__.py
== Required tool modules ==
  [PASS] tools/{bash, edit_file, glob, grep, list_dir, notebook_edit,
         python_exec, read_file, skill, skill_propose_patch, task,
         tool_search, view_image, write_file}.py
== Required skill directories ==
  [PASS] skills/{batch, clara, design, html, reflexion, report, review,
         security-review, simplify, verify}/SKILL.md
== Forbidden patterns clean (16/16) ==
== Result ==
  RESULT: PASS -- zip is ship-ready
```

## Final acceptance metrics

All V5_PLAN.md success metrics PASS:
- [x] Functional parity with v4.10.10 (Phase 12: 15/15 critical + 10/10 non-critical).
- [x] Static system prompt ≤ 2500 tokens (2498 actual; 45% reduction vs v4 ~5000).
- [x] Per-turn token overhead ≥ 3000 lower than v4 (deferred-loading active).
- [x] All Runnable patterns FAITHFUL or FAITHFUL-WITH-JUSTIFIED-ADAPTATION (no DRIFTED).
- [x] `pytest -q` green for all phases (437 pass + 4 skip).

## PS Issues resolved across v5

- **PS Issue #1** (Hermes filter — skill filtering by available tools) — Phase 10.
- **PS Issue #2** (visible IterationBudget) — Phase 8 data model + Phase 11 widget.
- **PS Issue #4** (visible thinking budget) — Phase 11 widget.
- **PS Issue #7** (tool_classes promotion to slot 2) — Phase 6 sectioned prompt.

## Build/test/audit summary across all 14 phases

| Phase | Tests added | Codex result | Codex findings | Tag |
|-------|-------------|--------------|----------------|-----|
| 00 | 2 | APPROVE | 0 | v5-phase-00 |
| 01 | 11 | APPROVE | 0 | v5-phase-01 |
| 02 | 12 | APPROVE | 0 | v5-phase-02 |
| 03 | 18 | APPROVE | 0 | v5-phase-03 |
| 04 | 27 | APPROVE | 0 | v5-phase-04 |
| 05 | 35 | APPROVE | 0 | v5-phase-05 |
| 06 | 27 | APPROVE_WITH_FIXES | 4 → fixed | v5-phase-06 |
| 07 | 32 | REJECT → fixed | 4 BLOCKERS | v5-phase-07 |
| 08 | 39 | APPROVE_WITH_FIXES | 4 → fixed | v5-phase-08 |
| 08.5 | 10 | APPROVE | 0 | v5-phase-08_5 |
| 09 | 44 | REJECT → fixed | 7 → fixed | v5-phase-09 |
| 10 | 33 | REJECT → fixed | 9 → fixed | v5-phase-10 |
| 11 | 20 | APPROVE_WITH_FIXES | 5 → fixed | v5-phase-11 |
| 12 | 25 | APPROVE (gate) | 0 | v5-phase-12 |
| 13 | 0 | APPROVE (gate) | 0 | v5-phase-13 + v5.0.0 |

**Total: 437 pass + 4 skip across 14 phases. 33 Codex findings caught + fixed.**

## Tag

After Phase 13 commit: `v5-phase-13` AND `v5.0.0` both created at the
same SHA. v4 stays on main untouched throughout.

## What's NOT in v5.0.0

Per V5_PLAN.md §"What v5 is NOT" + per-phase OUT-OF-SCOPE lists:
- Full v4 chat-display HTML rendering (deferred to v5.1+).
- Compact / clean buttons in chat UI.
- Model-switcher widget (CONFIG.model_id is static; restart cell 2).
- Build agent-type with worktree isolation (Phase 9 deferred from initial 4 types).
- Parallel sub-agent dispatch (Runnable async-only).
- /skill apply slash command (mechanism in `apply_proposal`; user-click UI deferred).
- Real SnapshotManager + AuditLogger singleton wiring (best-effort backup file in place).
- Microcompact / context_collapse / 2-stage smart compaction (deferred from Phase 8).

These are tracked for v5.1 / v5.2 future releases.
