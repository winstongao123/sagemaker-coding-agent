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
