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

## ADR-005 — BedrockClient: REUSE v4 verbatim (Bedrock-native), defer Runnable cache-break detection to Phase 6
- Date: 2026-04-30
- Phase ID: 01
- Status: ACCEPTED
- Source: V5_PLAN.md Phase 1 row + `compact_v4/MAIN/agent/sagemaker_agent.py:2378-2560` (v4 BedrockClient) + `gg-claude-code-runnable/src/services/api/claude.ts` + `services/api/promptCacheBreakDetection.ts`

### Question 1 — Replacement or addition?
- Does this REPLACE something v4 already has? **YES** — moves v4's `BedrockClient` class from `sagemaker_agent.py:2378` into the dedicated module `compact_v5/MAIN/agent/runtime/bedrock_client.py`. Behavior preserved verbatim.

### Question 2 — Architectural justification
N/A — replacement, not addition. v4's BedrockClient is already Bedrock-native, has prompt cache fallback, retry classifier, mock mode, thinking mode. Runnable's `claude.ts` is Anthropic-direct (subscriber/OAuth flows), not applicable to Bedrock.

### Question 3 — Cost
- Token cost: 0 (runtime client, not in prompt).
- Code complexity: extracts ~180 LOC from v4 monolith into a clean module. No behavior change.
- Maintenance: one place to update Bedrock-specific code.

### Question 4 — Cost worth it?
N/A (replacement).

### Decision
- **ACCEPTED for v5.0** — verbatim move of v4's `BedrockClient` to `runtime/bedrock_client.py` + minor import adjustments.

### Why NOT port Runnable's `promptCacheBreakDetection.ts` here
Runnable's detection is sophisticated (systemHash + toolsHash + perToolHashes + cacheControlHash + globalCacheStrategy + betas list etc.) and depends on having multi-block system prompt + cache-control state. v5 doesn't have multi-block prompts until Phase 6 lands. Porting now would build a detector against a structure that doesn't exist yet, causing rework.

**DEFER to Phase 6** when `prompt/sections.py` produces multi-block system prompts; the cache-break detector then has real state to compare against.

### Runnable-fidelity impact
N/A for ADR-005 itself (no Runnable code adopted yet). Phase 6 ADR will track the cache-break-detection port.

### Affected files
- compact_v5/MAIN/agent/runtime/bedrock_client.py (new — verbatim move from v4)
- compact_v5/MAIN/agent/tests/unit/test_bedrock.py (new — mock-mode + thinking-config-on-every-call regression for PS Issue #4)

### Linked port-log rows
None for Phase 1 (no Runnable port in this phase; pure v4 reuse).

---

## ADR-006 — Config + JSONC loader: REUSE v4 verbatim
- Date: 2026-04-30
- Phase ID: 01
- Status: ACCEPTED
- Source: `compact_v4/MAIN/agent/sagemaker_agent.py` `Config` class + `_strip_jsonc_comments` helper

### Question 1 — Replacement or addition?
- Does this REPLACE something v4 already has? **YES** — moves v4 Config to `compact_v5/MAIN/agent/runtime/config.py`.

### Question 2 — Architectural justification
N/A — verbatim move.

### Question 3 — Cost
- Token cost: 0.
- Code complexity: ~300 LOC moves to its own module. Cleaner imports.

### Question 4 — Cost worth it?
N/A (replacement).

### Decision
- **ACCEPTED for v5.0** — verbatim move with v5-relative path adjustments only.

### Critical fields preserved (sanity check)
- `model_id`, `region`, `workspace`, `temperature`, `max_turns`, `max_iteration_budget=600`, `max_exec_calls_per_session=200`, `aws_bedrock_only`, `enable_prompt_cache=True`, `thinking_enabled`, `thinking_budget`, `session_cost_limit`, `enable_skill_auto_trigger=False` (v4.9.6 default), `enable_skill_patching=False`, `enforce_verify_contract=False`.

### Runnable-fidelity impact
N/A — pure v4 reuse.

### Affected files
- compact_v5/MAIN/agent/runtime/config.py (new — verbatim move from v4)

### Linked port-log rows
None for Phase 1.

---

## ADR-007 — `ToolDef` Python Protocol replaces v4's 4-tuple `TOOLS` dict
- Date: 2026-04-30
- Phase ID: 02
- Status: ACCEPTED
- Source: Runnable `src/Tool.ts` (`Tool` interface + `buildTool` defaults) + v4 `compact_v4/MAIN/agent/sagemaker_agent.py:7105` (`TOOLS = {name: (callable, requires_approval, description, schema)}`)

### Question 1 — Replacement or addition?
- **REPLACEMENT.** Replaces v4's monolithic `TOOLS = {...}` 4-tuple dict (`(callable, requires_approval, description, schema)` per entry) with a typed `ToolDef` Protocol. Each tool becomes a small object with named attributes instead of a positional 4-tuple, which silently grew confusing as fields were added.

### Question 2 — Architectural justification (ADDITIONS only)
N/A — replacement.

### Question 3 — Cost
- Token cost (static prompt): **0**. The Protocol is a runtime/type construct, not in the system prompt. The per-tool description text is unchanged from v4.
- Token cost (per turn): **0**. Same as v4.
- Code complexity: ~120 LOC for `tools/registry.py` (Protocol + `build_tool` + `tool_matches_name` + `find_tool_by_name` + `get_tools` + `apply_tool_search_deferral` stub). v4's TOOLS dict is ~600 LOC of 4-tuple entries embedded in the monolith; v5 splits each tool into its own file (ADR-001) so the registry itself stays tiny.
- Maintenance: adding a new tool now requires creating one file + adding one `register()` call. Schemas/descriptions live next to their executors.

### Question 4 — Cost worth it?
N/A (replacement; the cost IS reduced complexity).

### Decision
- **ACCEPTED for v5.0** — `ToolDef` Protocol with these fields (Runnable parity columns shown):
  - `name` (Runnable: `name`)
  - `aliases` (Runnable: `aliases`) — backwards-compat lookup
  - `description` (Runnable: `prompt()`) — appears in system prompt block for this tool
  - `input_schema` (Runnable: `inputSchema`) — JSON-Schema dict (Python doesn't need Zod; v4 already uses dict-based schemas which Bedrock accepts)
  - `search_hint` (Runnable: `searchHint`) — 3-10 word phrase for ToolSearch keyword matching (used in Phase 7)
  - `should_defer` (Runnable: `shouldDefer`) — Phase-7 deferred-loading marker
  - `always_load` (Runnable: `alwaysLoad`) — never-defer marker
  - `is_read_only` (Runnable: `isReadOnly()`) — used for Plan-Mode allowlist + denial classification
  - `is_destructive` (Runnable: `isDestructive()`) — surfaced in approval prompt
  - `is_concurrency_safe` (Runnable: `isConcurrencySafe()`) — for parallel tool batching
  - `requires_approval` (v4-native; Runnable splits this into `checkPermissions()`) — kept v4-style for Bedrock/SageMaker constraint where approval flow is ipywidgets-driven, not a TS permission context
  - `enabled` (Runnable: `isEnabled()`) — feature gate
  - `max_result_size_chars` (Runnable: `maxResultSizeChars`) — output cap; default 50_000 to match v4 `max_output_chars`
  - `execute(args, context) -> dict` (Runnable: `call(args, context, ...)`) — the executor

- Methods that Runnable exposes but v5 OMITS (with reason):
  - All `render*` methods (`renderToolUseMessage`, `renderToolResultMessage`, etc.) → no JSX/Ink in v5; rendering happens in `ui/chat_ui.py` via ipywidgets (Phase 11). Constraint: `.ipynb`.
  - `inputJSONSchema` (MCP-only) → folded into the single `input_schema` field; v5 has no Zod-vs-JSON-Schema split.
  - `interruptBehavior`, `setToolJSX`, `addNotification`, `sendOSNotification` → no REPL/Ink runtime. Constraint: `.ipynb`.
  - `getActivityDescription`, `getToolUseSummary` → ipywidgets shows simpler progress; deferred to Phase 11 if needed.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** — constraint = `.ipynb` (no JSX/Ink/React; rendering moved to ipywidgets in Phase 11).
- Up-stream caller: `runtime/bedrock_client.py::chat()` accepts `tools` per-call; same as Runnable `claude.ts` consuming `getTools()`.
- Down-stream wiring: Phase 3-5 tools ship as one file each (ADR-001) and are registered via `register(tool)` calls in `tools/__init__.py`.
- State/cache contract: tool list is sorted by name in `assemble_tool_pool()` to match Runnable's prompt-cache stability requirement (alphabetical ordering, MCP tools as a contiguous suffix).

### Affected files
- compact_v5/MAIN/agent/tools/__init__.py
- compact_v5/MAIN/agent/tools/registry.py
- compact_v5/MAIN/agent/tests/unit/test_registry.py

### Linked port-log rows
- #001 (will be added in this phase): `Runnable Tool.ts → v5 ToolDef Protocol`

---

## ADR-008 — Tool registry: `get_tools()` + `apply_tool_search_deferral()` stub + plan-mode subset
- Date: 2026-04-30
- Phase ID: 02
- Status: ACCEPTED
- Source: Runnable `src/tools.ts` (`getAllBaseTools`, `getTools`, `filterToolsByDenyRules`, `assembleToolPool`) + v4 `PLAN_MODE_ALLOWED_TOOLS` set at `compact_v4/MAIN/agent/sagemaker_agent.py:6905`

### Question 1 — Replacement or addition?
- **REPLACEMENT.** Replaces v4's inline tool-allowlist filtering logic (which lived inside `Agent.run()` at `compact_v4/MAIN/agent/sagemaker_agent.py:8876` and again at `:9390`) with a single `get_tools(plan_mode=False, deny_rules=None)` entry point. Caller no longer reaches into a global TOOLS dict + global PLAN_MODE_ALLOWED_TOOLS set — it asks the registry.

### Question 2 — Architectural justification
N/A — replacement.

### Question 3 — Cost
- Token cost: 0.
- Code complexity: small. `get_tools()` + `assemble_tool_pool()` + `apply_tool_search_deferral()` stub = ~80 LOC.

### Question 4 — Cost worth it?
N/A.

### Decision
- **ACCEPTED for v5.0** — registry exposes:
  - `register(tool: ToolDef)` — Phase 3-5 tools register themselves at module import time.
  - `get_tools(plan_mode=False, deny_rules=None) -> list[ToolDef]` — returns the active tool list for the current call. Filters: (1) `enabled` flag, (2) deny rules (Runnable `filterToolsByDenyRules` parity), (3) plan-mode read-only subset (v4 `PLAN_MODE_ALLOWED_TOOLS` parity).
  - `assemble_tool_pool(plan_mode, deny_rules, mcp_tools=None)` — Runnable `assembleToolPool` parity; sorts built-ins alphabetically then MCP tools alphabetically (cache-stability invariant from Runnable).
  - `apply_tool_search_deferral(tools, enabled=False) -> tuple[list[ToolDef], ToolDef | None]` — **Phase 2 STUB**: when `enabled=False`, returns `(tools, None)`; full deferred-loading logic lands in Phase 7 with `tools/tool_search.py`. Stub exists now so callers can wire to it without churn later.
  - `tool_matches_name(tool, name) -> bool` (Runnable parity)
  - `find_tool_by_name(tools, name) -> ToolDef | None` (Runnable parity)
- **Plan-mode subset** is hardcoded to v4's `PLAN_MODE_ALLOWED_TOOLS` set (`{read_file, glob, grep, list_dir, semantic_search, todo_write, todo_read, view_image, skill, web_fetch, ask_user}`). When a tool with that name is registered, plan mode lets it through; otherwise it's filtered out.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** — constraint = `none` for the registry shape itself, BUT:
- Runnable's `permissionContext` (a complex `DeepImmutable` of allow/deny/ask rules + plan-mode + bypass mode + MCP server-prefix rules) is REPLACED with a simpler `(plan_mode: bool, deny_rules: set[str] | None)` pair.
- Justification: Runnable's permission context exists because the Anthropic-direct CLI has multi-source rules (user config, project config, settings, MCP server scopes). v5's Bedrock-only `.ipynb` has none of those sources — approval is a single ipywidgets prompt per call. Constraint = **`.ipynb`** (single approval source).
- Up-stream caller: Phase 8's `core/query_engine.py` calls `get_tools(plan_mode=ctx.plan_mode)` per turn (mirrors Runnable's `claude.ts` calling `getTools(permissionContext)` per request).
- Down-stream wiring: tools' `requires_approval` flag drives the ipywidgets approval prompt; v5 does NOT call Runnable's `checkPermissions()` (which returns a structured `PermissionResult`) because there's no permission context to check against. Instead, `requires_approval=True` triggers the user prompt directly. Documented as a v4-native ADAPT, not drift.
- Error contract: tool execution errors propagate as raised exceptions; `core/query_engine.py` (Phase 8) maps to `tool_result` blocks. Runnable's pattern is identical.

Auto-reject avoidance: constraint is **`.ipynb`** (not `none`), so this is a legitimate `FAITHFUL-WITH-JUSTIFIED-ADAPTATION` — the simpler permission-context tuple is forced by the .ipynb single-source approval flow.

### Affected files
- compact_v5/MAIN/agent/tools/registry.py (the registry implementation)
- compact_v5/MAIN/agent/tools/__init__.py (re-exports + future tool registrations)
- compact_v5/MAIN/agent/tests/unit/test_registry.py

### Linked port-log rows
- #001 (this phase): `Runnable Tool.ts → v5 ToolDef Protocol`
- #002 (this phase): `Runnable tools.ts (getAllBaseTools, getTools, filterToolsByDenyRules, assembleToolPool) → v5 tools/registry.py`

---

## (Append future ADRs below this line — keep numerical order 009, 010, ...)
