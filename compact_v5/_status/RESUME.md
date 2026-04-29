# RESUME PROTOCOL — v5 build

Use this checklist cold (zero prior context) to land ready to code.

## Step 1 — Read in this order, do NOT skip or skim:
1. compact_v5/_status/V5_BUILD_STATUS.md
2. compact_v5/_status/V5_DESIGN_DECISIONS.md
3. compact_v5/_status/V5_RUNNABLE_PORT_LOG.md
4. The phase row for the current phase in `compact_v5/docs/V5_PLAN.md`
5. Last 3 commits: `git log -n 3 v5-build`
6. Most recent Codex review: `compact_v5/_status/codex_reviews/phase-{ID_prev}.md`

## Step 2 — Verify state consistency:
a. `git status` — must be clean OR only contain files explicitly listed in V5_BUILD_STATUS.md "Remaining for this phase"; otherwise STOP and report drift.
b. `git rev-parse v5-build` — must equal "Last commit" sha in V5_BUILD_STATUS.md
c. `git for-each-ref refs/tags/v5-phase-* --sort=-version:refname --format='%(refname:short)' --count=1` — must equal expected prior checkpoint tag (deterministic, cross-platform). For phase 9, must equal `v5-phase-08_5` (not `v5-phase-08`).
d. `cd compact_v5/MAIN/agent && pytest -q` — must match "Tests status" in V5_BUILD_STATUS.md
e. If any of (a)-(d) disagree, STOP. Do not code. Report drift to user.

## Step 3 — Pick up work:
- Open V5_BUILD_STATUS.md "Next session: pick up at"
- Re-read the phase goal in V5_PLAN.md
- Re-read the Runnable source(s) listed for this phase BEFORE writing code
- Update V5_BUILD_STATUS.md: bump "Last updated", set State=IN_PROGRESS

## Step 4 — As you work:
- Every Runnable pattern adopted → append row to V5_RUNNABLE_PORT_LOG.md (Codex verdicts blank until review)
- Every non-trivial choice → append ADR to V5_DESIGN_DECISIONS.md
- Commit per meaningful step; convention: `v5/phase-{ID}: <imperative subject>`

## Step 5 — Close the phase:
- pytest must be green
- Run Codex with template (`_status/CODEX_REVIEW_TEMPLATE.md`); save output to `_status/codex_reviews/phase-{ID}.md`
- Address all AXIS A BLOCKER and CHANGES_REQUESTED findings (new commits, NOT amend); unresolved items must be recorded as explicit, user-approved exceptions in V5_BUILD_STATUS.md
- Fill Codex verdicts in V5_RUNNABLE_PORT_LOG.md
- Run `python tests/lint_phase_id.py` — must pass (canonical Phase ID consistency)
- Tag is FORBIDDEN if any open Codex finding has severity ≥ CHANGES_REQUESTED. Tag: `git tag v5-phase-{ID}`
- Update V5_BUILD_STATUS.md: State=DONE, "Next session: pick up at" → next phase
- Commit doc updates
