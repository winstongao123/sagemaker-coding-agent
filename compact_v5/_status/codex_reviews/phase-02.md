# Phase 02 Codex Review — gpt-5.5 (reasoning=medium)

Date: 2026-04-30
Phase: Phase 2 — Tool Protocol + registry
Diff: v5-phase-01..HEAD (Phase 02 staged, not yet committed)

## Verdict

**PHASE 02 OVERALL: APPROVE_WITH_FIXES**
- A-axis: code is close, but plan-mode MCP visibility and MCP deny semantics need fixes before Phase 03.
- B-axis: 0 FAITHFUL / 1 ADAPTED / 1 DRIFTED → after fixes: 0 FAITHFUL / 2 ADAPTED / 0 DRIFTED.

## AXIS A — Errors / bugs: CHANGES_REQUESTED

### Finding 1 (major) — fixed
- File: `compact_v5/MAIN/agent/tools/registry.py:251` (line of `assemble_tool_pool`)
- Issue: `assemble_tool_pool(plan_mode=True, mcp_tools=...)` left MCP tools visible. v4 blocks all tools not in `PLAN_MODE_ALLOWED_TOOLS`, including MCP/new tools, at `compact_v4/MAIN/agent/sagemaker_agent.py:9390`.
- Suggested fix: filter MCP tools through PLAN_MODE_ALLOWED_TOOLS too when plan_mode=True.
- **Fix applied**: `assemble_tool_pool` now applies `[t for t in mcp_filtered if t.name in PLAN_MODE_ALLOWED_TOOLS]` when `plan_mode=True`. Lock test: `test_plan_mode_filters_mcp_tools_too` (asserts MCP tools stripped from pool when plan_mode=True), `test_plan_mode_allows_mcp_tool_only_if_name_in_allowlist` (edge case allowlist-by-name).

### Finding 2 (major) — fixed
- File: `compact_v5/MAIN/agent/tools/registry.py:200` (line of `_filter_by_deny_rules`)
- Issue: `_filter_by_deny_rules()` only supported exact name/alias denies. Runnable `filterToolsByDenyRules()` delegates to `getDenyRuleForTool()`, which also supports MCP server-level rules like `mcp__server` and `mcp__server__*`.
- Suggested fix: support MCP prefix/wildcard deny strings, OR document as intentionally unsupported and remove the parity claim.
- **Fix applied**: `_filter_by_deny_rules` now extracts the server segment from `mcp__<server>__<tool>` names and matches against both `mcp__<server>` (blanket-deny form) and `mcp__<server>__*` (wildcard form). Lock tests: `test_deny_rule_mcp_server_blanket_strips_all_tools_from_that_server`, `test_deny_rule_mcp_server_wildcard_form_matches_too`, `test_deny_rule_does_not_falsely_match_partial_server_name` (guards against `mcp__git` falsely matching `mcp__github__*`).

### Finding 3 (minor) — fixed
- File: `compact_v5/_status/V5_BUILD_STATUS.md:20`
- Issue: Status doc stale: said registry/tests unwritten and Phase 02 tests not run.
- **Fix applied**: status doc rewritten to reflect actual Phase 02 close state (35/35 pytest pass, all 4 Codex findings addressed).

### Finding 4 (nit) — fixed
- File: `compact_v5/MAIN/agent/tools/registry.py:34`
- Issue: unused `field` import from `dataclasses`.
- **Fix applied**: import line changed to `from dataclasses import dataclass`.

### Coverage notes from Codex
- Pre-fix: missing coverage for plan-mode + MCP tools and MCP server-prefix deny rules.
- Post-fix: 5 new tests added covering both areas (3 deny-rule + 2 plan-mode-MCP).
- Codex could not rerun pytest locally because `python.exe` was inaccessible from its PowerShell sandbox. Tests verified locally: **35/35 PASS**.

## AXIS B — Runnable-fidelity

- **PATTERN 001 (Tool.ts → ToolDef Protocol + build_tool)**: **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**.
  - Source intent: define a Tool interface with safe defaults applied via buildTool.
  - v5 implementation: `ToolDef` Protocol + `ToolRecord` dataclass + `build_tool()` factory; defaults match `TOOL_DEFAULTS` (isConcurrencySafe=False, isReadOnly=False, isDestructive=False, enabled=True).
  - Constraint forcing adaptation: `.ipynb` (no JSX/Ink runtime; rendering moved to ipywidgets in Phase 11).
  - Drift risk: none.

- **PATTERN 002 (tools.ts → registry)**: **DRIFTED → FAITHFUL-WITH-JUSTIFIED-ADAPTATION** after fixes.
  - Pre-fix: sorting/dedup matched, but deny-rule semantics omitted MCP server-prefix behavior, and plan mode did not filter MCP tools.
  - Post-fix: MCP prefix/wildcard deny support added; plan-mode allowlist applied to MCP tools; tests for both lock the contract.
  - Constraint forcing adaptation: `.ipynb` (single approval source replaces Runnable's DeepImmutable PermissionContext multi-source rules).
  - Drift risk: none after fixes.

- **UNDECLARED_PATTERN check**: PASS. No additional Runnable port found beyond declared Tool/buildTool and tools registry patterns.

## Required before tag (per Codex required list)

- [x] Filter MCP tools under plan mode → `assemble_tool_pool` updated; `test_plan_mode_filters_mcp_tools_too` locks it.
- [x] Add MCP prefix/wildcard deny support → `_filter_by_deny_rules` extracts server segment + matches `mcp__server` and `mcp__server__*`; 3 new lock tests.
- [x] Add tests for both cases → 5 new tests added (35/35 pass).
- [x] Refresh `V5_BUILD_STATUS.md` → rewritten to reflect actual Phase 02 close state.
- [x] Remove unused `field` import (nit).

All findings addressed. PORT_LOG row #002 verdict updates from DRIFTED to FAITHFUL-WITH-JUSTIFIED-ADAPTATION.
