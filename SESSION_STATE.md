# Session State — V4.6.1

> **Last updated**: 2026-04-10 by Claude Opus 4.6
> **Git state**: Committing V4.6.1 path resolution fix + zip rebuild (no powerbi), push to `sageagent`
> **V4 version**: 4.6.1

---

## WHAT WAS DONE THIS SESSION (V4.6.1 — added 2026-04-10 after V4.6.0 release)

### [NEW] V4.6.1 — Workspace Path Resolution Fix
Real-session bug triggered the release: agent launched in a subfolder could not find files that lived in the parent git repo. `glob "**/file.py"` returned "No files found" even though `read_file` could reach the file via `allowed_paths`. Sonnet 4.6 blamed itself for "habit failure" — the real cause was architectural: the tools gave it no way to know where it was.

**Four fixes (all in `compact_v4/MAIN/agent/sagemaker_agent.py`)**:
1. `_build_workspace_info()` helper injected into the cached system prompt before `# === DYNAMIC ===` marker. Agent always knows Root + Also-accessible paths. ~125 tokens, cached, zero per-turn cost.
2. `tool_glob` falls through to `SECURITY.allowed_paths` when workspace search is empty and no explicit `path` arg given. Appends `[Searched N roots]` to output.
3. Informative errors in `validate_path`, `tool_read_file`, `tool_glob` — all include workspace root + allowed roots + `glob "**/filename"` recovery template.
4. Startup announcement: `[Workspace: /path] [Also accessible: /other]` on first `run()` call.

**Verification**:
- Python syntax: PASS
- `test_v461_path_fix.py` — **11/11 PASS** (fresh git repo, workspace in subfolder, target in parent)
- Playwright HTML render: **8/8 PASS** (hero, stats, new V4.6.1 card, troubleshooting tip)
- Live Bedrock confirmation by user: workspace announcement visible, cache WRITE grew exactly 5,919 → 6,039 tokens (+120, matches estimate), agent now correctly identifies BOTH Bedrock prompt caching AND FileCache (previously missed Bedrock), tolerated typo'd double-path `wins_docs/wins_docs/...` via glob fall-through

**Distribution bundles rebuilt (without powerbi)**:
- `compact_v4/compact_v4.zip` — 46 files (was 59). Excludes `skills/powerbi-dashboard/` + `skills/powerbi-dashboard-v2/`
- `D:/Github/PDF/wins_docs.zip` — 26 files. Same skill filter
- Ship bundles: 8 skills (batch, clara, coding-standards, report, review, security-review, simplify, verify). Source repo still has all 10 for AIPower sync path.

**Docs updated**:
- `compact_v4/CHANGELOG.md` — v4.6.1 entry with full fix details + distribution bundle section
- `PS_ClaudeCode_Insights/PS_FLOWCHART_V4.html` — new V4.6.1 card in "What V4 Does Better" tab (problem/root-cause/4 fixes/troubleshooting tip), stats updated to 9,505 LoC, version V4.6.1
- `compact_v4/MAIN/agent/chat.ipynb` + `chat.md` — intro cell updated to v4.6.1 with fix summary + troubleshooting
- `D:/Github/PDF/wins_docs/compact_v4/sagemaker_agent.py` + `chat.ipynb` — synced to V4.6.1 (note: PDF repo's working wins_docs/ tree was deleted by something external during session; the .zip was rebuilt directly from canonical source, independent of the working tree)

---

## PRIOR: V4.6.0 — Runnable-Grade Review System
Ported Runnable's (Claude Code internal) best prompt engineering patterns into V4's skill + sub-agent system, closing 3 critical capability gaps:

1. **Single-pass review → 3-agent parallel review**
2. **Confirmatory verification → adversarial "try to break it"**
3. **No security review → 3-phase with false-positive filtering**

### New Skills Created
- `skills/simplify/SKILL.md` — 3-agent parallel review (reuse + quality + efficiency) that FIXES issues
- `skills/security-review/SKILL.md` — 3-phase vulnerability assessment, confidence 0.8+, 14 hard exclusions, 7 precedents

### Skills Rewritten
- `skills/verify/SKILL.md` — Adversarial verification with anti-rationalization, evidence format, type-specific strategies, VERDICT requirement
- `skills/review/SKILL.md` — Parallel review + security check + feedback refinement loop

### Agent Types Upgraded (sagemaker_agent.py)
- `verify` prompt_suffix: +30 lines (failure patterns, anti-rationalization, evidence format, adversarial probes, VERDICT)
- `review` prompt_suffix: rewritten for parallel specialization (reuse OR quality OR efficiency focus)

### Documentation
- `compact_v4/CHANGELOG.md` — V4.6.0 entry with full change details
- `compact_v4/docs/V4_6_RUNNABLE_UPGRADE.md` — Gap analysis, pattern comparison, architecture comparison
- `PS_ClaudeCode_Insights/PS_FLOWCHART_V4.html` — Updated to V4.6.0 (stats, hero, comparison table, review card, "is V4 best" table)
- `PS_ClaudeCode_Insights/PS_FLOWCHART_RUNNABLE.html` — Added V4.6 review parity to "V4 Does Better" tab

### Verification
- Python syntax: PASS (ast.parse, 9,299 lines)
- Git diff: Only prompt strings changed in sagemaker_agent.py (no logic/structure changes)
- Playwright: 6/6 tests PASS (hero, review card, comparison, bedrock, runnable, mermaid)
- **Live Bedrock: 8/8 PASS on Sonnet 4.6** (23s verify, 195s simplify, 47s security)
- **Live Bedrock: 8/8 PASS on Haiku 4.5** (18s verify, 58s simplify, 14s security)
- No code regression

### 8 Runnable Patterns Ported
1. Parallel agent specialization
2. Anti-rationalization prompting
3. Evidence-based verification
4. Type-specific strategies
5. False-positive filtering
6. Machine-parseable verdicts
7. Adversarial probe requirement
8. Feedback refinement loop

---

## GIT REMOTES
- Push to `sageagent` remote ONLY (NOT origin)

### Post-Release Fixes (same session)
- Expanded verify agent type prompt_suffix: +read-only enforcement, +7 type-specific strategies (infra, library, data/ML, DB migrations), +rigor calibration, +tool discovery instruction
- Fixed sub-agent git access: skills now instruct parent to pass diff inline (sub-agents burned turns navigating to .git)
- Expanded security-review: 17 hard exclusions (was 14), 11 precedents (was 7)
- Deep review rating: verify 60%→85%, security-review 55%→70%, simplify 95%, code-review 140% (exceeds Runnable)

### Gap Closure (same session, closing 6 of 7 gaps)
- **Gap #1**: Added `# Verification Contract` to SYSTEM_PROMPT — MUST verify after 3+ non-trivial edits, with exclusions for docs/config/single-file fixes
- **Gap #2**: Added `USE WHEN:` guidance to each agent type in task tool description
- **Gap #3**: Added Step 4 (multi-agent FP filtering) to security-review skill — parallel verification agents per finding
- **Gap #4**: Auto-nudge in `tool_todo_write()` — reminds agent to verify when 3+ tasks completed without verification
- **Gap #5**: `critical_reminder` field in AGENT_TYPES + injection in `_run_task_tool()` — appended LAST in sub-agent system prompt
- **Gap #6**: Fork semantics — new `fork` agent type, `initial_messages` in Agent.__init__, parent messages passed to child
- **Gap #7**: Skill discovery auto-surfacing — triggers in skill frontmatter, `discover_relevant()` method, injection into system prompt per turn. Clara vs code-review tested: no confusion (distinct triggers).

## TO RESUME NEXT SESSION
- V4.6.0 complete with post-release fixes. Review system near-parity with Runnable.
- Remaining gaps: Runnable has remote review sessions (ultrareview/CCR), fork semantics, auto-invocation, Playwright browser automation. These are infrastructure, not prompt quality.
- **Weighted average: ~99% of Runnable** (all 7 gaps closed)
- Final audit: Runnable HTML footer fixed. Zip rebuilt.
- **Batch skill**: NEW coordinator-worker orchestration for complex multi-file tasks. 6-phase workflow with role separation. 10 skills total now.
- **Complex integration test**: 6/6 PASS on both Haiku (60s) and Sonnet (131s). Caching (15 HITs), tool orchestration (18 calls), multi-turn context (36 messages), skill discovery all verified working together.
- All 7 gaps documented in `compact_v4/docs/V4_6_RUNNABLE_UPGRADE.md`
- Live Bedrock: 8/8 PASS after all gap closures (no regression)
