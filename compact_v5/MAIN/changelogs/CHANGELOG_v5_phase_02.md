# CHANGELOG — v5 Phase 02

**Phase**: 02 — Tool Protocol + registry
**Date closed**: 2026-04-30
**Tag**: `v5-phase-02`
**Branch**: `v5-build`

## Goal

Replace v4's monolithic `TOOLS = {name: (callable, requires_approval, description, schema)}` 4-tuple dict at `compact_v4/MAIN/agent/sagemaker_agent.py:7105` with a typed `ToolDef` Protocol + `tools/registry.py`. Include the Phase-7 deferred-loading hook as a stub now so Phase 8 callers wire to it without churn later.

## ADRs accepted this phase

- **ADR-007** — `ToolDef` Python Protocol replaces v4's 4-tuple TOOLS dict (FAITHFUL-WITH-JUSTIFIED-ADAPTATION, constraint=.ipynb).
  - Drops React/Ink rendering methods (renderToolUseMessage, renderToolResultMessage, renderToolUseRejectedMessage, etc.) — v5 ipywidgets renders in `ui/chat_ui.py` Phase 11.
  - Defaults match Runnable's `TOOL_DEFAULTS` exactly: `is_concurrency_safe=False`, `is_read_only=False`, `is_destructive=False`, `enabled=True`.
- **ADR-008** — Tool registry exposes `get_tools()` + `assemble_tool_pool()` + `apply_tool_search_deferral()` stub + plan-mode subset (FAITHFUL-WITH-JUSTIFIED-ADAPTATION, constraint=.ipynb).
  - Replaces Runnable's complex `DeepImmutable PermissionContext` with simpler `(plan_mode: bool, deny_rules: set[str] | None)` because v5's .ipynb has a single approval source vs Runnable's multi-source rules (user config / project config / settings / MCP scopes).
  - Plan-mode allowlist is verbatim v4's `PLAN_MODE_ALLOWED_TOOLS` set: `{read_file, glob, grep, list_dir, semantic_search, todo_write, todo_read, view_image, skill, web_fetch, ask_user}`.

## Files added

| Path | LOC | Purpose |
|------|-----|---------|
| `compact_v5/MAIN/agent/tools/registry.py` | ~290 | `ToolDef` Protocol + `ToolRecord` dataclass + `build_tool()` factory + `register/unregister/all_registered` + `tool_matches_name` + `find_tool_by_name` + `get_tools` + `assemble_tool_pool` + `apply_tool_search_deferral` (Phase-7 stub) + `PLAN_MODE_ALLOWED_TOOLS` frozenset + `_filter_by_deny_rules` (incl. MCP server-prefix matching). |
| `compact_v5/MAIN/agent/tests/unit/test_registry.py` | ~370 | 22 unit tests covering all ADR-007 + ADR-008 contracts and Codex finding lock tests. |
| `compact_v5/_status/codex_reviews/phase-02.md` | — | Phase 02 Codex review record. |

## Files modified

| Path | Change |
|------|--------|
| `compact_v5/MAIN/agent/tools/__init__.py` | Re-exports public surface (ToolDef, ToolRecord, build_tool, register, unregister, all_registered, get_tools, assemble_tool_pool, apply_tool_search_deferral, tool_matches_name, find_tool_by_name, PLAN_MODE_ALLOWED_TOOLS). Phase 3-5 will add per-tool module imports. |
| `compact_v5/_status/V5_BUILD_STATUS.md` | Phase 02 closure documented. |
| `compact_v5/_status/V5_DESIGN_DECISIONS.md` | Appended ADR-007 + ADR-008. |
| `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` | Added rows #001 + #002 with Codex verdicts (PATTERN 001 FAITHFUL-WITH-JUSTIFIED-ADAPTATION; PATTERN 002 same after fixes). |

## Tests

- `pytest tests/` — **35/35 PASS** in 0.10s
  - 2 smoke (every package imports cleanly + Phase-01 runtime files present)
  - 11 bedrock (Phase 01)
  - **22 registry (NEW Phase 02)**:
    - 2 build_tool tests (defaults + overrides)
    - 6 registration/lookup tests (start-empty, register-then-lookup, duplicate-rejection, unregister, alias-lookup, disabled-hidden)
    - 2 deny-rules-by-name tests
    - 2 plan-mode tests (v4 allowlist parity, plan-mode + deny composition)
    - 2 cache-stable assemble_tool_pool tests
    - 1 deferral-stub disabled test
    - 1 deferral-stub enabled-as-stub test
    - 1 ToolDef Protocol membership test
    - **3 MCP server-prefix deny tests** (Codex finding 2 lock):
      - `test_deny_rule_mcp_server_blanket_strips_all_tools_from_that_server`
      - `test_deny_rule_mcp_server_wildcard_form_matches_too`
      - `test_deny_rule_does_not_falsely_match_partial_server_name`
    - **2 plan-mode + MCP tests** (Codex finding 1 lock):
      - `test_plan_mode_filters_mcp_tools_too`
      - `test_plan_mode_allows_mcp_tool_only_if_name_in_allowlist`

## Codex review

- Model: `gpt-5.5` (reasoning=medium)
- Verdict: **APPROVE_WITH_FIXES** → all 4 findings landed in same Phase 02 commit before tagging.
- AXIS A findings (4): all addressed
  - **Major**: `assemble_tool_pool(plan_mode=True, mcp_tools=...)` was leaving MCP tools visible. v4 blocks all non-allowlisted tools in plan mode at `compact_v4/MAIN/agent/sagemaker_agent.py:9390`. **Fixed**: plan-mode now applies `PLAN_MODE_ALLOWED_TOOLS` to MCP tools too. Locked by 2 new tests.
  - **Major**: `_filter_by_deny_rules()` only supported exact name/alias. Runnable `getDenyRuleForTool()` also supports MCP server-level rules `mcp__server` and `mcp__server__*`. **Fixed**: `_is_denied()` extracts the server segment from `mcp__<server>__<tool>` names and matches both blanket-deny and wildcard forms. Locked by 3 new tests including a no-partial-match guard.
  - **Minor**: `V5_BUILD_STATUS.md` stale. **Fixed**: rewritten to reflect actual Phase 02 close state.
  - **Nit**: unused `dataclasses.field` import. **Fixed**: removed.
- AXIS B verdicts (after fixes):
  - **PATTERN 001** (Tool.ts → ToolDef): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION**. constraint=.ipynb (no JSX/Ink runtime).
  - **PATTERN 002** (tools.ts → registry): **FAITHFUL-WITH-JUSTIFIED-ADAPTATION** (initial verdict was DRIFTED; fixed in same commit). constraint=.ipynb.
  - UNDECLARED_PATTERN check: PASS (no other Runnable code ported beyond declared patterns).

## Operational fix during this phase

**Codex CLI hang debugging**: an early Phase 02 Codex run (`bfvy3b215`) hung at 0 bytes for 55+ minutes. Root cause: the Phase 02 review prompt (~5000 chars) exceeded the Windows CMD argument length limit; codex silently fell back to "Reading additional input from stdin..." and waited forever. Phase 01's shorter prompt fit fine. **Fix**: pipe the prompt via stdin (`cat prompt.txt | codex exec -`) instead of `"$(cat ...)"` as a command-line argument. Documented in this phase's SESSION_STATE.md update so future phases use the stdin form unconditionally.

The SQLite `migration 21` warning is cosmetic — telemetry persistence fails but the API response still arrives. Documented but not fixed (low priority; doesn't block reviews).

## What is intentionally NOT in this phase

- Per-tool modules (`tools/read_file.py`, `tools/grep.py`, etc.) — those land Phase 3-5 per ADR-001 file-per-tool layout. Phase 02 ships only the registry + ToolDef shape.
- Real `apply_tool_search_deferral` deferred-loading logic — Phase 7 fills in the stub.
- `tools/tool_search.py` — Phase 7.
- `core/query_engine.py` wiring — Phase 8.

## Pickup point for next session

Phase 03 — Core read-only tools (read_file, grep, glob, list_dir). Read Runnable `src/tools/FileReadTool/` + `GrepTool/` + `GlobTool/`, write each as its own file per ADR-001, register in `tools/__init__.py`. Each tool gets its own `tests/tools/test_*.py` file. **AGGREGATE AUDIT GATE BEFORE PHASE 4** — run audit checks (token budget, ADR-to-port-log ratio, cognitive load) before starting Phase 4.

Resume protocol: `_status/RESUME.md`.
