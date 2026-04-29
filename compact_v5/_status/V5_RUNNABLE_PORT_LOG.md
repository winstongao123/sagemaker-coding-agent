# V5 Runnable Port Log (append-only)

Format: one row per Runnable pattern adopted. Never delete rows. Mark superseded as STATUS=SUPERSEDED-BY-#&lt;id&gt;.

| ID | Date | Phase | Runnable source (file:section) | v5 target | Adoption verdict | Codex error verdict | Codex fidelity verdict | Commit sha | Notes |
|----|------|-------|--------------------------------|-----------|------------------|---------------------|------------------------|------------|-------|

(no rows yet — Phase 0 is scaffolding only; first port-log row appears in Phase 1)

Verdict legend:
- Adoption: PORT (1:1) | ADAPT (semantic match, mechanism differs) | REPLACE (v4-native chosen) | DEFER
- Codex error: PASS | CHANGES_REQUESTED | BLOCKER
- Codex fidelity: FAITHFUL | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | DRIFTED

Enforcement note: every PORT_LOG row MUST reference an `ADR-NNN` in V5_DESIGN_DECISIONS.md (per the Addition Gate). Rows without an ADR reference are rejected by the pre-tag lint check (`tests/lint_phase_id.py`).
