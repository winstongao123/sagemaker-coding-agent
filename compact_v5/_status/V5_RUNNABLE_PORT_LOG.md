# V5 Runnable Port Log (append-only)

Format: one row per Runnable pattern adopted. Never delete rows. Mark superseded as STATUS=SUPERSEDED-BY-#&lt;id&gt;.

| ID | Date | Phase | Runnable source (file:section) | v5 target | Adoption verdict | Codex error verdict | Codex fidelity verdict | Commit sha | Notes |
|----|------|-------|--------------------------------|-----------|------------------|---------------------|------------------------|------------|-------|
| 001 | 2026-04-30 | 02 | src/Tool.ts:`Tool` interface + `buildTool` defaults | compact_v5/MAIN/agent/tools/registry.py:`ToolDef` Protocol + `build_tool()` | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Drops React/Ink render methods; constraint=.ipynb. ADR-007. Codex APPROVE. |
| 002 | 2026-04-30 | 02 | src/tools.ts:`getAllBaseTools` + `getTools` + `filterToolsByDenyRules` + `assembleToolPool` | compact_v5/MAIN/agent/tools/registry.py:`get_tools()` + `assemble_tool_pool()` + `apply_tool_search_deferral()` stub | ADAPT | PASS (post-fix) | FAITHFUL-WITH-JUSTIFIED-ADAPTATION (post-fix) | (pending) | Replaces v4 monolithic TOOLS dict + PLAN_MODE_ALLOWED_TOOLS set. Simpler permission-context tuple (plan_mode + deny_rules) instead of Runnable's DeepImmutable PermissionContext. constraint=.ipynb. ADR-008. **Initial Codex verdict was DRIFTED on plan-mode-MCP-visibility + missing MCP server-prefix deny support; both fixed in same Phase 02 commit (lock tests added). Final verdict FAITHFUL-WITH-JUSTIFIED-ADAPTATION.** |

Phase 1 had no Runnable rows (pure v4 reuse — see ADR-005 / ADR-006). First Runnable adoption rows are Phase 02 above.

Verdict legend:
- Adoption: PORT (1:1) | ADAPT (semantic match, mechanism differs) | REPLACE (v4-native chosen) | DEFER
- Codex error: PASS | CHANGES_REQUESTED | BLOCKER
- Codex fidelity: FAITHFUL | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | DRIFTED

Enforcement note: every PORT_LOG row MUST reference an `ADR-NNN` in V5_DESIGN_DECISIONS.md (per the Addition Gate). Rows without an ADR reference are rejected by the pre-tag lint check (`tests/lint_phase_id.py`).
