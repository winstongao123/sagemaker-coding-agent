# V5 Design Decisions (append-only ADRs)

Each entry is a mini-ADR. Never edit a closed entry; supersede with a new one referencing the old by id.

---

## ADR-001 — File-per-tool layout instead of dir-per-tool
- Date: 2026-04-30
- Phase ID: 00
- Status: ACCEPTED
- Source: V5_PLAN.md §"Port map (Runnable → v5)" row `tools/<Name>/` → `tools/<name>.py`

### Question 1 — Replacement or addition?
- Does this REPLACE something v4 already has? **YES** — replaces v4's monolithic `TOOLS = {}` dict in `compact_v4/MAIN/agent/sagemaker_agent.py:7105`.

### Question 2 — Architectural justification (ADDITIONS only)
N/A — this is a replacement, not an addition.

### Question 3 — Cost
- Token cost (static prompt): 0 (tool-loading is runtime-only).
- Token cost (per turn): 0 (per-tool schemas already shipped per turn in v4 too).
- Code complexity: ~25 separate files vs 1 monolith — but each file is small, testable, and the deferred-loading pattern (Phase 7) requires per-tool isolation.
- Maintenance: one tool per file; adding a new tool = adding one file + one `registry.py` entry.

### Question 4 — Cost worth it?
N/A (replacement).

### Decision
- **ACCEPTED for v5.0**

### Rationale
Runnable uses dir-per-tool (`tools/BashTool/{prompt.ts, executor.tsx, UI.tsx}`) because TS/React needs separate JSX/types files. Python doesn't — one file per tool with `prompt`, `schema`, `execute`, `is_read_only` attributes is enough. ADAPT verdict (mechanism differs, intent preserved). The Addition Gate is N/A here because this is a structural rewrite of a v4 component, not a new feature.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** — constraint = `.ipynb workflow` (Python flat-zip ship surface; no JSX/React/Ink runtime).

### Affected files
- compact_v5/MAIN/agent/tools/*.py (all tool modules)
- compact_v5/MAIN/agent/tools/registry.py
- compact_v5/_rebuild_zip.py (flatten step)

### Linked port-log rows
(filled in during Phase 2)

---

## ADR-002 — File-per-section system prompt with `prompt/*.md`
- Date: 2026-04-30
- Phase ID: 00
- Status: ACCEPTED
- Source: V5_PLAN.md §"The single key architectural improvement"

### Question 1 — Replacement or addition?
- Does this REPLACE something v4 already has? **YES** — replaces v4's `SYSTEM_PROMPT` 5000-token f-string at `compact_v4/MAIN/agent/sagemaker_agent.py:8029`.

### Question 2 — Architectural justification
This IS the structural fix for v4's "buried matrix" failure. Each section becomes a reviewable, token-budgeted unit. Adding new content requires creating a new file (mechanically reviewed) instead of appending to an unreviewable monolith.

### Question 3 — Cost
- Token cost (static prompt): expected REDUCTION from ~5000 to ≤2500 (target).
- Code complexity: ~14 small `.md` files + `prompt/sections.py` (~200 LOC) vs 1 giant f-string. Trade dispersion for reviewability.

### Question 4 — Cost worth it?
N/A (replacement; the cost IS reduced complexity per file).

### Decision
- **ACCEPTED for v5.0** — load-bearing for Phase 6.

### Runnable-fidelity impact
**FAITHFUL** — directly ports `constants/systemPromptSections.ts` registry pattern. Python `.md` files are the equivalent of TS section-functions; cache-boundary marker file replaces TS `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` constant.

### Affected files
- compact_v5/MAIN/agent/prompt/__init__.py
- compact_v5/MAIN/agent/prompt/sections.py
- compact_v5/MAIN/agent/prompt/*.md (14 files)

### Linked port-log rows
(filled in during Phase 6)

---

## ADR-003 — v5 must address ALL 7 issues from `PS_actual_use_problems.md`
- Date: 2026-04-30
- Phase ID: 00
- Status: ACCEPTED
- Source: User instruction 2026-04-30 + `compact_v4/docs/PS_actual_use_problems.md` (copied to `compact_v5/docs/PS_actual_use_problems.md`)

### Question 1 — Replacement or addition?
- This is a **scope binding**, not a feature. v4.10.10 in-place fixes addressed issues 1, 2, 5, 6, 7 partially. v5 must address ALL 7 structurally.

### Question 2 — Architectural justification
v4's failure was that issues were patched individually but the ARCHITECTURE didn't change. v5's structural opportunity (sectioned prompt, deferred loading, Hermes skill filter) lets each issue get a structural fix instead of a patch. Specifically:
- Issue 1 (CSO warnings) → audit-level discipline (Phase 10 tests)
- Issue 2 (iter budget) → UI slider + status bar (Phases 1, 8, 11)
- Issue 3 (cold cache) → reuse v4 + status indicator (Phase 8)
- Issue 4 (thinking) → docs + status indicator (Phase 1, 6)
- Issue 5 (session cost persist) → SessionManager.save/load round-trip (Phase 1)
- Issue 6 (wiring bug pattern) → Codex AXIS-A gate enforcement (every phase)
- Issue 7 (buried matrix) → sectioned prompt + cognitive-load audit (Phase 6, 7)

### Question 3 — Cost
- Token cost: 0 (this is process discipline, not prompt content).
- Code complexity: small additions to V5_PS_ISSUES_MAPPING.md + per-phase tests.
- Maintenance: each phase that addresses an issue must include a test asserting the issue's failure mode no longer occurs.

### Question 4 — Cost worth it?
**Yes**. The user explicitly required this. Skipping it means v5 fails on launch the same way v4 did.

### Decision
- **ACCEPTED for v5.0** — binding constraint on every phase that maps to a PS issue.

### Rationale
The detailed mapping lives in `compact_v5/docs/V5_PS_ISSUES_MAPPING.md`. Each entry specifies: root cause, v4.10.10 in-place fix (if any), v5 target phase, v5 acceptance criterion, and "better than v4" delta. Aggregate audit checks that mapped issues are addressed before allowing the next phase.

### Runnable-fidelity impact
**N/A** — this is process discipline, not a Runnable port.

### Affected files
- compact_v5/docs/V5_PS_ISSUES_MAPPING.md (new this phase)
- compact_v5/docs/PS_actual_use_problems.md (copied from v4 for reference)
- Per-phase test files (each phase's tests must include the mapped regression)

### Linked port-log rows
None — this is process discipline, not a Runnable port.

---

## ADR-004 — Reference HTMLs copied to `compact_v5/docs/htmls/`
- Date: 2026-04-30
- Phase ID: 00
- Status: ACCEPTED
- Source: User instruction 2026-04-30 + existing v4 HTMLs in `compact_v4/MAIN/agent/` and `PS_ClaudeCode_Insights/`

### Question 1 — Replacement or addition?
- ADDITION (reference HTMLs to support v5 build context). Not a code feature.

### Question 2 — Architectural justification (ADDITIONS only)
The user explicitly asked for these as design references during v5 build. They serve as:
- Architectural diagrams users can compare side-by-side (v4 vs Runnable vs LangGraph)
- Visual reference for the deep-dive port discipline (Phase 6, 7, 8 will benefit)
- Future v5 architecture HTMLs (to be generated in Phase 13) will sit alongside, enabling v5-vs-v4-vs-Runnable comparison.

### Question 3 — Cost
- Token cost: 0 (HTMLs are not loaded by the agent runtime).
- Repo size: +500 KB (6 HTMLs).
- Code complexity: 0.

### Question 4 — Cost worth it?
Yes — small repo cost, valuable design reference for building v5.

### Decision
- **ACCEPTED for v5.0**

### Files added (Phase 00)
- compact_v5/docs/htmls/PS_DEEP_DIVE_RUNNABLE.html (Runnable architecture deep-dive)
- compact_v5/docs/htmls/PS_FLOWCHART_RUNNABLE.html (Runnable flowchart)
- compact_v5/docs/htmls/PS_FLOWCHART_V4.html (v4 flowchart, for comparison)
- compact_v5/docs/htmls/PS_RUNNABLE_VS_LANGGRAPH.html (Runnable vs LangGraph comparison)
- compact_v5/docs/htmls/HERMES_VS_CODING_AGENT_v4.html (Hermes vs v4 comparison)
- compact_v5/docs/htmls/v4_architecture.html (v4 architecture HTML)

### Future (Phase 13)
- compact_v5/docs/htmls/v5_architecture.html (NEW — generated at Phase 13)
- compact_v5/docs/htmls/PS_FLOWCHART_V5.html (NEW — generated at Phase 13)
- compact_v5/docs/htmls/PS_V5_VS_RUNNABLE.html (NEW — comparison generated at Phase 13)

### Runnable-fidelity impact
**N/A** — these are reference docs, not adopted patterns.

### Linked port-log rows
None.

---

## (Append future ADRs below this line — keep numerical order 005, 006, ...)
