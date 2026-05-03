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

## ADR-009 — Phase 3 read-only tools: REUSE v4 executors + ADAPT Runnable prompt text + thin path-validation stub
- Date: 2026-04-30
- Phase ID: 03
- Status: ACCEPTED
- Source:
  - v4: `compact_v4/MAIN/agent/sagemaker_agent.py:4258` (`tool_read_file`), `:4846` (`tool_glob`), `:4897` (`tool_grep`), `:4952` (`tool_list_dir`)
  - Runnable: `gg-claude-code-runnable/src/tools/FileReadTool/prompt.ts`, `GrepTool/prompt.ts`, `GlobTool/prompt.ts`
  - v4 security: `compact_v4/MAIN/agent/sagemaker_agent.py` `SecurityManager.validate_path` (full port deferred to Phase 5)

### Question 1 — Replacement or addition?
- **REPLACEMENT.** Replaces v4's monolithic tool functions (which live inside `sagemaker_agent.py` and are referenced by the v4 `TOOLS` dict 4-tuple at `:7105`) with file-per-tool modules under `compact_v5/MAIN/agent/tools/` (per ADR-001).

### Question 2 — Architectural justification (ADDITIONS only)
N/A — replacement. Notes on the structural value:
- Per ADR-001 file-per-tool, each of the 4 tools becomes its own module that calls `register(build_tool(...))` at import time.
- v4's executor function bodies are battle-tested Python; rewriting from Runnable's TS would lose features Runnable doesn't have (FILE_CACHE, FILE_UNCHANGED_STUB, large-file guard, .ipynb cell parsing, mtime tracking, allowed_paths fallback for glob, binary-file skip for grep).
- Runnable's prompt text (the description shown to the model) is more directive on WHEN / WHEN NOT — addresses PS Issue #7 (buried-matrix failure). The text gets adapted: tool-name strings change (Runnable `Read` → v5 `read_file`, etc.), and the v5 ipynb constraint means we don't reference Ink/JSX.

### Question 3 — Cost
- Token cost (per turn — schema + description in initial prompt): each of 4 tools contributes ~120-200 tokens of description + ~50 tokens of schema. Total Phase 3 contribution to per-turn overhead: ~700-1000 tokens. This is BEFORE Phase 7's ToolSearchTool deferral; after Phase 7, low-frequency tools get deferred and the per-turn overhead drops.
- Static prompt cost: 0 (tools are not in the system prompt; their descriptions are in the per-turn `tools` block).
- Code complexity: 4 small tool modules (~80-150 LOC each) + 1 thin path-validation helper (~50 LOC). Total ~500 LOC of new code. Compared to v4's ~700 LOC of monolithic tool functions, similar size but split for reviewability.
- Maintenance: each tool now has a single owner-file. Bug fixes touch one module, not the v4 monolith.

### Question 4 — Cost worth it?
N/A (replacement; the cost is dispersed but reviewability improves).

### Decision
- **ACCEPTED for v5.0** — 4 read-only tools land Phase 3:
  - `tools/read_file.py` — REUSE v4 executor + ADAPT Runnable prompt text (renamed from `Read` to `read_file`).
  - `tools/grep.py` — REUSE v4 executor + ADAPT Runnable prompt text. **Critical correction**: Runnable's prompt says "built on ripgrep" but v4 uses Python `re`. v5 prompt says "regex search across files" (truthful). PS Issue #6 (wiring-bug pattern) lock — don't claim a backend we don't have.
  - `tools/glob.py` — REUSE v4 executor + ADAPT Runnable prompt text.
  - `tools/list_dir.py` — REUSE v4 verbatim. **No Runnable analog** (Runnable tells the model to use `ls` via Bash). v5 keeps the dedicated tool because v4 has it; in plan mode the user can't bash, so list_dir is essential. No Runnable port row — pure v4 reuse.
- Each tool flagged: `is_read_only=True`, `is_concurrency_safe=True` (Runnable parity — read-only ops are safe in parallel), `requires_approval=False`.

### Path-validation strategy (Phase 3 stub vs Phase 5 full)
- v4's `SecurityManager.validate_path` does (a) workspace boundary check, (b) allowed_paths fallback, (c) symlink escape detection. The full module also has 134-case destructive command coverage which is irrelevant for read-only tools.
- **Phase 3 ships a minimal `tools/_path_validation.py`** with just the path-resolution + boundary check (the parts read-only tools need). ~50 LOC.
- **Phase 5 replaces** this stub with the full `security/` package port from v4 (verbatim). The 4 tool modules will then import from `security.manager` instead of `tools._path_validation`.
- This split is necessary because Phase 5 is where `security/` lands per the locked phase plan; we can't depend on it from Phase 3.
- The Phase 5 ADR will note the `_path_validation.py` retirement and verify the same security contract is preserved.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** — constraint = `Bedrock | python_exec | .ipynb`:
- Bedrock: tool descriptions ship as JSON `description` fields in the `tools` body block; same as Runnable's API call.
- python_exec: v5 has no Node fs API access; the executor body is pure Python (v4 reuse).
- .ipynb: no JSX/Ink rendering; ipywidgets handles UI in Phase 11.
- The `ripgrep` correction is a forced fidelity-improvement: v5's grep tool truthfully describes its backend (`re` module), avoiding a Runnable-text claim that doesn't match implementation. PS Issue #6 (wiring bug) prevention.

### Affected files
- compact_v5/MAIN/agent/tools/_path_validation.py (new, Phase-3-only stub)
- compact_v5/MAIN/agent/tools/read_file.py (new)
- compact_v5/MAIN/agent/tools/grep.py (new)
- compact_v5/MAIN/agent/tools/glob.py (new)
- compact_v5/MAIN/agent/tools/list_dir.py (new)
- compact_v5/MAIN/agent/tools/__init__.py (add 4 import lines so registration fires)
- compact_v5/MAIN/agent/tests/tools/test_read_file.py (new)
- compact_v5/MAIN/agent/tests/tools/test_grep.py (new)
- compact_v5/MAIN/agent/tests/tools/test_glob.py (new)
- compact_v5/MAIN/agent/tests/tools/test_list_dir.py (new)

### Linked port-log rows
- #003 — Runnable FileReadTool/prompt.ts → v5 tools/read_file.py
- #004 — Runnable GrepTool/prompt.ts → v5 tools/grep.py (with ripgrep→regex correction)
- #005 — Runnable GlobTool/prompt.ts → v5 tools/glob.py
- (#006 NOT created — list_dir has no Runnable analog; pure v4 reuse documented inline)

---

## ADR-010 — Phase 4 mutating tools: REUSE v4 executors + ADAPT Runnable prompts + diff_widget UI
- Date: 2026-04-30
- Phase ID: 04
- Status: ACCEPTED
- Source:
  - v4: `compact_v4/MAIN/agent/sagemaker_agent.py:4632` (`tool_write_file`), `:4729` (`tool_edit_file`), `:5921` (`tool_notebook_edit`), `:6419` (`tool_view_image`)
  - Runnable: `gg-claude-code-runnable/src/tools/FileWriteTool/prompt.ts`, `FileEditTool/prompt.ts`, `NotebookEditTool/prompt.ts`, `FileEditTool/UI.tsx` (diff-preview React component pattern)
  - V5_PLAN.md Phase 4 acceptance criterion: edit_file, write_file, AND notebook_edit approval prompts each show colored before/after diff inline (red removed, green added, gray context) with file path header + line numbers + ±3 lines context + click-to-expand-full-file using `ui/diff_widget.py` BEFORE user clicks Approve.

### Question 1 — Replacement or addition?
- **REPLACEMENT** for the 4 tool executors (v4 monolith → file-per-tool modules per ADR-001).
- **ADDITION** for `ui/diff_widget.py` — the UX pattern is novel to v5 (v4 didn't show colored inline diffs in the approval prompt; user only saw a text summary). Adopted from Runnable's `EditTool/UI.tsx` Ink renderer pattern.

### Question 2 — Architectural justification (ADDITIONS only)
**Why diff_widget.py:** PS_actual_use_problems.md captures a real pattern where v4 users approved edits without seeing the actual change content, then discovered later that the model had edited the wrong region or stripped useful code. Showing the colored diff inline (with ±3 lines context) lets the user catch misplaced edits BEFORE clicking Approve. Runnable solved this with `EditTool/UI.tsx` (Ink JSX). v5 ipywidgets equivalent: an HTML widget with `+` green / `-` red / context gray + a `<details>` block for click-to-expand-full-file.
- **User-visible improvement**: misplaced-edit prevention. A model that does `edit_file(file_path="auth.py", old_string="def login():\n    return user", new_string="def login():\n    return user.is_admin")` shows the change in context, so the user spots `is_admin` permissions creep before approving.
- **Not acceptable as ADDITION justification**: "matches Runnable" / "completes the parity". Both are insufficient.
- **Acceptable**: catches a documented v4 failure mode (silent misplaced edits).

### Question 3 — Cost
- Token cost (static prompt): 0 (the diff widget is a Python class that returns HTML; not in the system prompt).
- Token cost (per turn): 0 (UI rendering happens client-side in ipywidgets; no model interaction).
- Code complexity: ~150 LOC `ui/diff_widget.py` (uses stdlib `difflib.unified_diff` + simple HTML escape + `<details>` markup). No new dependencies (`ipywidgets` already used by v4 chat.ipynb; only HTML strings emitted in Phase 4).
- Maintenance: one file to update if Runnable changes diff conventions or if user complains about the rendering.

### Question 4 — Cost worth it?
**Yes**. Misplaced-edit prevention is exactly the kind of user-visible improvement V5_PLAN.md's "addition gate" requires. The cost (~150 LOC + 0 tokens) is negligible vs the value (catches a documented v4 failure mode at approval time, before the bad edit lands).

### Decision
- **ACCEPTED for v5.0** — 4 mutating tools + 1 ui module land Phase 4:
  - `tools/write_file.py` — REUSE v4 executor + ADAPT Runnable prompt text. Requires `read_before_overwrite` (matches v4 contract). `requires_approval=True`.
  - `tools/edit_file.py` — REUSE v4 executor + ADAPT Runnable prompt text. Requires `read_first` (matches v4 contract). Exact match + `replace_all` flag. `requires_approval=True`.
  - `tools/notebook_edit.py` — REUSE v4 executor (insert/replace/delete cells). Atomic write (tmp file + rename) preserved. `requires_approval=True`.
  - `tools/view_image.py` — REUSE v4 executor; Phase 4 returns metadata, the pending-images queue is Phase-8 concern.
  - `ui/diff_widget.py` — generates HTML diff strings (red removed, green added, gray context, file path header, ±3 lines context, `<details>`-wrapped full-file expansion). Phase 11 wires into the ipywidgets approval flow.

### Phase-3-stub dependencies and Phase-5 retirement
- Like Phase 3, mutating tools depend on `tools/_path_validation.py` (Phase-3 stub) and a new `tools/_file_read_tracking.py` (replaces v4's `_FILES_READ` set + `_FILE_READ_TIMES` map). Both stubs are retired in Phase 5 when the full security/ + a Phase-8-friendly read-tracking module land.
- v4-specific deferred features (snapshot-before-edit / auto-lint-python / auto-commit-checkpoint / secrets-scan) are NOT ported in Phase 4 — they belong to Phase 5 (security) + Phase 8 (query_engine session machinery). Documented inline in each tool module.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** — constraint = `.ipynb` + Bedrock + python_exec:
- Drops React/Ink rendering methods (renderToolUseMessage etc.) — same as Phase 2 ToolDef Protocol decision.
- `ui/diff_widget.py` renders HTML for ipywidgets, not Ink JSX. Same UX semantics: colored diff, file header, click-to-expand. Constraint = `.ipynb`.
- Tool naming: Runnable `Edit`/`Write`/`NotebookEdit` → v5 `edit_file`/`write_file`/`notebook_edit` (v4 parity).

### Affected files
- compact_v5/MAIN/agent/tools/_file_read_tracking.py (new, Phase-4-only stub)
- compact_v5/MAIN/agent/tools/write_file.py (new)
- compact_v5/MAIN/agent/tools/edit_file.py (new)
- compact_v5/MAIN/agent/tools/notebook_edit.py (new)
- compact_v5/MAIN/agent/tools/view_image.py (new)
- compact_v5/MAIN/agent/ui/diff_widget.py (new)
- compact_v5/MAIN/agent/tools/__init__.py (extend bootstrap_built_ins)
- compact_v5/MAIN/agent/tests/tools/test_phase4_mutating_tools.py (new)
- compact_v5/MAIN/agent/tests/unit/test_diff_widget.py (new)

### Linked port-log rows
- #006 — Runnable FileWriteTool/prompt.ts → tools/write_file.py
- #007 — Runnable FileEditTool/prompt.ts → tools/edit_file.py
- #008 — Runnable NotebookEditTool/prompt.ts → tools/notebook_edit.py
- #009 — Runnable FileEditTool/UI.tsx (diff-preview pattern) → ui/diff_widget.py
- (No row for view_image — Runnable's FileReadTool handles images inline; v5 keeps the dedicated tool for v4 parity. Documented inline in tools/view_image.py.)

---

## ADR-011 — Phase 5 security/ + bash + python_exec: REUSE v4 verbatim, retire `_path_validation` stub
- Date: 2026-04-30
- Phase ID: 05
- Status: ACCEPTED
- Source:
  - v4 `compact_v4/MAIN/agent/sagemaker_agent.py:1298-2148` (`SecurityManager` class — ~850 LOC, including SECRET_PATTERNS, SENSITIVE_FILES, CATASTROPHIC_PATTERNS, DANGEROUS_PATTERNS (70+ regex), DANGEROUS_PYTHON (~70 regex), ALLOWED_PYTHON_MODULES, BLOCKED_PYTHON_MODULES, BLOCKED_PYTHON_MEMBERS, validate_path, validate_command, validate_python, scan_secrets, truncate_output)
  - v4 `:756-861` (`Truncation` class — used by `SECURITY.truncate_output`)
  - v4 `:5239` (`tool_bash`), `:5409` (`tool_python_exec`)
  - v4 `:4988-5160` (helpers: `_safe_exec_env`, `_run_subprocess`, `_validate_shell_redirections`, `_docker_base_cmd`, `_ensure_docker_image_ready`, `_kill_active_process`)
  - v4 `:10487` (`HIGH_RISK_TOOLS = {"bash", "python_exec", "task", "web_fetch"}` — used by approval-prompt UX)
  - v4 `:2107-2138` (`_auto_detect_allowed_paths` — SageMaker root + git repo root auto-detection)
  - v4 `:4212` (`_resolve_path` helper)
  - Runnable: `gg-claude-code-runnable/src/tools/BashTool/prompt.ts` (description text only — Runnable's executor is unrelated TypeScript shell logic)

### Question 1 — Replacement or addition?
- **REPLACEMENT** for the security module + bash + python_exec executors. Replaces the v4 monolith inline definitions.
- **ADDITION** for the package boundary itself (security/ as its own importable package). v4 had everything inline in `sagemaker_agent.py`.

### Question 2 — Architectural justification (ADDITIONS only)
**Why a security/ package boundary:** v4's SecurityManager + dangerous-pattern lists + helpers were ~1000 LOC of security-critical code interleaved with everything else in the monolith. The security review requires reading these as a unit, but in v4 they were scattered. v5 isolates them into `security/` so:
- A future security audit can scan one package, not the whole monolith.
- Phase 3-4 tools that already use `validate_path` switch from the Phase-3 stub to the production module via a one-line import change (the stub becomes a delegating shim for backwards compatibility).
- Adding new dangerous patterns is a bounded edit to one file (`dangerous_patterns.py` or `dangerous_python.py`), not a search-and-add across a monolith.
- Tests can target the security boundary without spinning up the entire agent runtime.

### Question 3 — Cost
- Token cost (static prompt): 0 (security/ is runtime code, not in the prompt).
- Token cost (per turn): 0 (bash + python_exec descriptions ship per turn; size is comparable to v4's text).
- Code complexity: ~1100 LOC across 5 security files + 2 tool modules + 1 retired stub. v4 had ~1000 LOC inline. Net: ~10% more LOC for the package boundary, but every file has a single clear responsibility.
- Maintenance: regex patterns concentrate in 2 files; SecurityManager class gets the policy logic; helpers get the subprocess + redirection plumbing. Adding a new pattern is grep + edit one file.

### Question 4 — Cost worth it?
**Yes.** The 134-case destructive-command coverage is the single largest security control v5 inherits from v4. Isolating it improves auditability. The architectural separation also makes the Phase 5 acceptance criterion ("134-case coverage from v4 still passes") mechanically verifiable.

### Decision
- **ACCEPTED for v5.0** — Phase 5 lands the following files, all REUSE v4 verbatim with v5-compatible imports:
  - `compact_v5/MAIN/agent/security/__init__.py` — package init exposing `SECURITY` singleton + helper re-exports.
  - `compact_v5/MAIN/agent/security/manager.py` — `SecurityManager` class verbatim + SECRET_PATTERNS + SENSITIVE_FILES + helper functions (`_resolve_path`, `_safe_exec_env`, `_run_subprocess`, `_validate_shell_redirections`, `_docker_base_cmd`, `_ensure_docker_image_ready`, `_kill_active_process`, `_auto_detect_allowed_paths`).
  - `compact_v5/MAIN/agent/security/dangerous_patterns.py` — CATASTROPHIC_PATTERNS + DANGEROUS_PATTERNS + NETWORK_COMMANDS + BASE_ALLOWED_COMMANDS + INTERPRETER_COMMANDS + CONTAINER_COMMANDS.
  - `compact_v5/MAIN/agent/security/dangerous_python.py` — DANGEROUS_PYTHON + ALLOWED_PYTHON_MODULES + BLOCKED_PYTHON_MODULES + BLOCKED_PYTHON_MEMBERS + ALLOWED_AWS_HINT.
  - `compact_v5/MAIN/agent/security/high_risk.py` — HIGH_RISK_TOOLS frozenset + `is_high_risk(name)` helper.
  - `compact_v5/MAIN/agent/runtime/truncation.py` — Truncation class verbatim.
  - `compact_v5/MAIN/agent/tools/bash.py` — verbatim port of v4 `tool_bash` + ADAPT Runnable `BashTool/prompt.ts` description.
  - `compact_v5/MAIN/agent/tools/python_exec.py` — verbatim port of v4 `tool_python_exec` + v5-native description (no Runnable analog — Runnable uses Bash for Python).

### `_path_validation.py` retirement
- Phase 3 shipped `tools/_path_validation.py` as an ~80-LOC stub.
- Phase 5 converts it into a **thin delegating shim**: `validate_path` and `resolve_path` forward to `security.manager.SECURITY.validate_path` and `security.manager._resolve_path`.
- All 8 existing Phase 3-4 tool modules keep their `from . import _path_validation as path_security` imports unchanged.
- The shim documents the delegation inline so a future reader knows where the real implementation lives.
- This avoids touching 8 tool modules in this phase. Phase 13 can decide whether to remove the shim entirely (and update the 8 imports to point at `security.manager` directly) or keep the indirection forever.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** — constraints = `Bedrock` + `python_exec` + `.ipynb`:
- Bedrock-only mode (`CONFIG.aws_bedrock_only`) blocks all AWS clients except `bedrock-runtime`. Runnable uses Anthropic API directly — no AWS client to block. v5's Bedrock-only check is uniquely v5/v4.
- `python_exec` is v5/v4-specific: a sandboxed Python execution tool with allowlist-based AST validation, runtime closure-based import hook, and workspace-scoped file IO. Runnable doesn't have this — it tells the model to use Bash for Python. v5/v4 keep `python_exec` because plan-mode forbids bash AND because the closure sandbox is significantly more restrictive than spawning a generic shell.
- `.ipynb` constraint forces no Ink/JSX in the bash/python_exec UI — text output flows back through the existing approval prompt.

### Affected files
- compact_v5/MAIN/agent/security/__init__.py (new)
- compact_v5/MAIN/agent/security/manager.py (new — verbatim port)
- compact_v5/MAIN/agent/security/dangerous_patterns.py (new — verbatim constants)
- compact_v5/MAIN/agent/security/dangerous_python.py (new — verbatim constants)
- compact_v5/MAIN/agent/security/high_risk.py (new)
- compact_v5/MAIN/agent/runtime/truncation.py (new — verbatim port of Truncation class)
- compact_v5/MAIN/agent/tools/bash.py (new)
- compact_v5/MAIN/agent/tools/python_exec.py (new)
- compact_v5/MAIN/agent/tools/_path_validation.py (modified — converted to delegating shim)
- compact_v5/MAIN/agent/tools/__init__.py (extended bootstrap_built_ins)
- compact_v5/MAIN/agent/tests/unit/test_security_manager.py (new)
- compact_v5/MAIN/agent/tests/tools/test_phase5_bash_python.py (new)

### Intentional deviation from v4 in `python_exec` invocation
- **v4** (`compact_v4/MAIN/agent/sagemaker_agent.py:5433`): `[sys.executable, temp_path]` — runs Python with the user's site-packages reachable.
- **v5 Phase 5**: `[sys.executable, "-I", temp_path]` — adds the `-I` (isolated mode) flag. This prevents the user's pip cache, PYTHONPATH, and `~/.pythonrc` from leaking into the sandboxed code. The closure-based runtime sandbox still enforces the import allowlist; `-I` just hardens the boundary so `sys.path` doesn't include `~/.local/lib/...` packages the agent never declared.
- **Codex Phase-05 review finding 4**: flagged this as a non-verbatim deviation. Documented here as intentional hardening; locked by `test_python_exec_uses_isolated_mode` so a future refactor cannot silently drop the flag.
- **Why this is "better than v4"**: a malicious package installed in the user's home (e.g., a typo-squatted dep) cannot be imported by the sandbox even if the user's environment has it. The `-I` mode is a small additional defense-in-depth layer.

### Linked port-log rows
- #010 — Runnable BashTool/prompt.ts → tools/bash.py:_DESCRIPTION (executor body is v4 port; ADAPT for description text only)
- (No row for python_exec — no Runnable analog. Documented inline in tools/python_exec.py.)
- (No rows for security/ files — pure v4 reuse, no Runnable adoption.)

---

## ADR-012 — Phase 6 sectioned prompt: file-per-section + token budget + cache-boundary
- Date: 2026-04-30
- Phase ID: 06
- Status: ACCEPTED
- Source:
  - v4 `compact_v4/MAIN/agent/sagemaker_agent.py:8029-8178` (`SYSTEM_PROMPT` 914-LOC f-string with embedded `# === DYNAMIC ===` boundary)
  - v4 `:6899` (`PLAN_MODE_PROMPT`)
  - Runnable: `gg-claude-code-runnable/src/constants/prompts.ts` (914 LOC) + `constants/systemPromptSections.ts` (registry pattern with memoization + cache-break detection)
  - V5_PLAN.md Phase 6 acceptance: static prompt ≤ 2500 tokens (vs v4's ~5000); cache-boundary test passes.
  - PS_actual_use_problems.md Issue #7: v4's "Tool capability classes" section was buried mid-list in a 5000-token prompt. Under cognitive load (40-call exec limit hit) the model under-attended to it, concluded "all tools blocked", refused to keep working. Phase 6 is the structural fix.

### Question 1 — Replacement or addition?
- **REPLACEMENT** of v4's monolithic 914-LOC `SYSTEM_PROMPT` f-string with file-per-section `prompt/*.md` files + `prompt/sections.py` registry + `core/cache.py` cache-block builder.

### Question 2 — Architectural justification
The PS Issue #7 root cause: v4 grew the system prompt by *appending* — every Hermes pattern, Runnable adoption, Learning_Factory pattern, and v4-original addition was concatenated to the f-string. Reviewers signed off on each individual addition; nobody reviewed the aggregate. The result was a flat 914-LOC bullet list where the LLM under-attended to mid-list bullets under cognitive load.

The structural fix:
1. **One section per file** so reviewers see a bounded unit. Adding new content requires creating a new file (mechanically reviewed) instead of appending to an unreviewable monolith.
2. **Token budget per section**, hard-capped in the registry. Ship-gate (`tests/aggregate_audit.py`) fails if any section exceeds its cap or if the sum exceeds 2500.
3. **Promotion of "Tool capability classes" to top-level**: under cognitive load the LLM attends to the *first* sections more than the middle. v4 buried the matrix at section 3-of-20; v5 promotes it to section 2 (right after identity).
4. **Cache-boundary marker** (`_CACHE_BOUNDARY` section) explicitly separates the static (cached) part from the dynamic per-turn part. Phase 1's BedrockClient already splits at `# === DYNAMIC ===` as a string marker; Phase 6 makes this a structural boundary in the section registry.

### Question 3 — Cost
- Token cost (static prompt): TARGET REDUCTION from v4's ~5000 to ≤2500. Each section gets a hard cap; sum is enforced by the audit gate.
- Token cost (per turn): same as v4 (sections are static; per-turn content is the dynamic block + tools list + messages).
- Code complexity: 19-20 small `.md` files (most ≤1KB each) + `prompt/sections.py` (~150 LOC) + `prompt/__init__.py` (~50 LOC) + `core/cache.py` (~200 LOC). Replacement of v4's 914-LOC f-string. Net: similar LOC, drastically better reviewability.
- Maintenance: editing a section is `read_file → edit_file` of one .md. Adding a section requires creating a file + adding one line to the registry.

### Question 4 — Cost worth it?
**Yes** — this is the load-bearing architectural fix that motivated v5. Skipping it leaves v5 with v4's failure mode.

### Decision
- **ACCEPTED for v5.0** — 19 prompt/*.md sections + registry + cache module land Phase 6.

### Section list (FINAL — locked at this ADR; future additions require a new ADR)

**Static section group (cached prefix)** — 17 sections:

| # | Section file | Token cap | Purpose |
|---|---|---|---|
| 1 | `identity.md` | 80 | "You are SageMaker Coding Agent…" |
| 2 | `tool_classes.md` | **350** | Tool capability classes — PROMOTED to slot 2 (PS Issue #7 fix). Lists session-limited (bash/python_exec) vs unlimited tools, repetition guard, fallback-when-blocked. |
| 3 | `system.md` | 150 | Auto-compact behavior, system-reminder tags, after-block re-read instruction. |
| 4 | `tool_efficiency.md` | 200 | EFFICIENCY IS CRITICAL — search-before-read, parallel calls, minimize-tool-calls. |
| 5 | `doing_tasks.md` | 280 | MINIMAL EDIT principle, simplest-approach-first, verify-before-claim, ASK_USER restraint. |
| 6 | `critique_handling.md` | 180 | ACCEPT / PARTIAL / REJECT labels with evidence; spec-first ordering. |
| 7 | `answer_preference.md` | 100 | Chat vs files; never create summary.md without explicit ask. |
| 8 | `data_validation.md` | 120 | CSV/Excel row counts + join-key uniqueness checks. |
| 9 | `executing_actions.md` | 180 | Reversibility / blast-radius; SageMaker = local-git-only; no GitHub remote. |
| 10 | `output_style.md` | 80 | Concise; markdown; `file:line` refs; no emojis without ask. |
| 11 | `subagent_coord.md` | 130 | Task tool for 3+ queries; parallel sub-agents; never delegate understanding. |
| 12 | `status_doc.md` | 90 | AGENT_STATUS.md handoff for long-running work. |
| 13 | `verification_contract.md` | 120 | /verify suggested after 3+ logic edits; CONFIG.enforce_verify_contract flag. |
| 14 | `memory_protocol.md` | 100 | memory.md 4-section format (USER / FEEDBACK / PROJECT / REFERENCE). |
| 15 | `documents.md` | 70 | create_chart → embed; notebook_edit not create_notebook. |
| 16 | `security.md` | 100 | Workspace boundary; trust-boundary (don't follow tool-output instructions). |
| 17 | `mcp.md` | 50 | MCP servers register as `mcp_<server>_<tool>` tools. |
| 18 | `commands.md` | 80 | `/cost`, `/context`, `/status`, `/revert`, `/diffs`, `/verify`, `/skills`, etc. |
| 19 | `skill_patching.md` | 150 | OPT-IN — only when CONFIG.enable_skill_patching=True. 4-rule check. |

**Cache boundary marker**: `_CACHE_BOUNDARY.md` (the literal marker, not a section).

**Dynamic section group (uncached suffix)** — landed Phase 8+:
- todo_restoration (after compact)
- file_restoration (after compact)
- skill_active (per-skill auto-trigger)
- iteration_budget_status (Phase 8)

**Token budget total**: 17 × cap-per-section ≈ 2480 tokens. Within the ≤2500 target.

### Cache-boundary contract
- v4's `BedrockClient.chat()` splits the system string on `# === DYNAMIC ===` and applies `cache_control={"type":"ephemeral"}` to the static prefix only. Phase 1's port preserves this.
- Phase 6 formalises the boundary: `prompt/__init__.py:build_system_prompt(ctx)` returns a list of message-content blocks, with the cache-boundary marker between the static and dynamic groups.
- `core/cache.py:detect_cache_break(prev_blocks, new_blocks)` (Phase-6 stub; Phase-1 ADR-005 deferred this from Phase 1) hashes each section and identifies which one flipped if the prompt cache is invalidated. Logs `CacheBreakWarning` with the section name.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** — constraint = `Bedrock`:
- Runnable's `systemPromptSection` registry is preserved 1:1 in `prompt/sections.py` (memoized compute fns, cache_break flag for volatile sections, `clearSystemPromptSections()` invoked on /clear or /compact).
- `DANGEROUS_uncachedSystemPromptSection` semantically maps to `cache_break=True` Phase-6 sections — currently empty (no v5 section is volatile-by-design); the option is reserved.
- Adaptation: Runnable uses TS Promise-based async compute fns; v5 uses sync Python functions because all current sections are static-string returns. If a future section needs async (e.g., reading a remote skill registry), Phase 8+ ADR can lift to async.
- v5 sections are STATIC `.md` FILES, not TS function returns. Justified because: (a) auditing is grep-friendly, (b) no v5 section currently needs runtime computation, (c) per-section token caps are mechanically enforceable on text files. Constraint = `Bedrock` (Bedrock prompt cache rewards static byte-stable prefixes; runtime function returns add a hashing step).

### Affected files
- compact_v5/MAIN/agent/prompt/__init__.py (new)
- compact_v5/MAIN/agent/prompt/sections.py (new)
- compact_v5/MAIN/agent/prompt/*.md (19 new files)
- compact_v5/MAIN/agent/core/__init__.py (new — package marker)
- compact_v5/MAIN/agent/core/cache.py (new)
- compact_v5/MAIN/agent/tests/unit/test_prompt_assembly.py (new)
- compact_v5/MAIN/agent/tests/unit/test_cache.py (new)

### Linked port-log rows
- #011 — Runnable `constants/systemPromptSections.ts` (registry pattern + memoization + cacheBreak flag) → `prompt/sections.py`
- #012 — Runnable `constants/prompts.ts` (914-LOC f-string structure inspired the sectioning; v5 content is REWRITTEN per ADR-002 file-per-section, not ported verbatim) → 19 prompt/*.md files
- #013 — Runnable `services/api/promptCacheBreakDetection.ts` (cache-break detection: hash sections, identify which one flipped) → `core/cache.py:detect_cache_break()`

### PS Issue mapping
- **PS Issue #7 — buried-matrix failure mode** (the root cause that motivated v5):
  - Root cause: in v4's flat 914-LOC SYSTEM_PROMPT, "Tool capability classes" was the third major section (after "System" and ahead of "Using Tools"); under cognitive load the LLM under-attended.
  - Phase 6 structural fix: tool_classes.md is **slot 2** (right after identity, before "system"). Each section file has a hard token cap so no single section can grow back to a 914-LOC dump.
  - Verification: cognitive-load test (Codex-evaluated, run as part of the audit gate before Phase 7) — Codex simulates the LLM receiving "Blocked: bash + python_exec limit reached (200/session)" and checks whether the prompt structure leads it to continue with read_file/grep/edit_file rather than "all tools blocked".

---

## ADR-013 — Phase 7 ToolSearchTool deferred loading (highest-leverage Runnable port)
- Date: 2026-04-30
- Phase ID: 07
- Status: ACCEPTED
- Source:
  - Runnable: `gg-claude-code-runnable/src/tools/ToolSearchTool/ToolSearchTool.ts` (471 LOC) + `prompt.ts` (121 LOC) + `constants.ts`
  - Runnable: `gg-claude-code-runnable/src/utils/toolSearch.ts` (deferred-tool placement logic)
  - V5_PLAN.md Phase 7 acceptance: per-turn schema overhead drops ≥3000 tokens vs Phase 6 baseline
  - Phase 2 ADR-008 stub: `tools/registry.py:apply_tool_search_deferral` returns `(tools, None)` when `enabled=False`. Phase 7 replaces with the real implementation.

### Question 1 — Replacement or addition?
- **Both.**
- **REPLACEMENT** of the Phase-2 `apply_tool_search_deferral` stub with the real deferred-loading logic.
- **ADDITION** of `tools/tool_search.py` (a new tool exposed to the model).

### Question 2 — Architectural justification (ADDITIONS only)
**Why tool_search.py:** the v4 system loads every tool's full JSON schema on every turn. With 30 tools that's ~5000-8000 tokens of schema in EVERY message — pure overhead since the model uses ~3-5 tools per turn. Runnable's deferred-loading pattern: low-frequency tool schemas are NOT in the initial prompt; instead, only their NAMES appear in a `<system-reminder>`. When the model needs one, it calls `tool_search("name")` which returns the full schema in a `<functions>` block, after which the tool is callable like any other.

This is the **single highest-leverage token-saving Runnable adoption** in v5 — V5_PLAN.md targets ≥3000 tokens/turn savings.

User-visible improvement: faster turns, lower per-turn cost, higher effective context window for actual work.

### Question 3 — Cost
- Token cost (static prompt): 0 (tool_search description is in the per-turn tools block, not the static prompt).
- Token cost (per turn — schema overhead): the tool_search tool itself adds ~300 tokens (schema). Deferred tools' names appear in a system-reminder (~10 tokens each). Their FULL schemas (~300-500 tokens each) only appear when the model fetches them.
  - **Baseline (Phase 6)**: 10 tools × ~400 token average schema = ~4000 tokens/turn.
  - **Post-Phase-7**: assuming we defer 5 low-frequency tools (view_image, list_dir, notebook_edit, ask_user, web_fetch, todo_*), kept-loaded set is ~5 tools (read_file, grep, glob, edit_file, write_file, bash, python_exec, task) × ~400 = ~3200 tokens. Plus tool_search itself (~300) plus 5 deferred-tool names (~50) = ~3550 tokens.
  - **Savings**: ~4000 - ~3550 ≈ **450 tokens** per turn just from name-only deferral.
  - To hit V5_PLAN's ≥3000-token target, we need to defer roughly 8 tools (or have larger schemas). Phase 7 contributes to the target; Phases 9+ (sub-agents, skills, all the create_* document tools, MCP) will push the per-turn overhead much higher and the savings will compound. The aggregate audit before Phase 13 enforces the ≥3000 final target.
- Code complexity: ~250 LOC `tools/tool_search.py` + ~80 LOC update to `apply_tool_search_deferral` + ~150 LOC tests.
- Maintenance: the keyword-matching algorithm is small (Runnable's CamelCase + MCP-prefix splitting).

### Question 4 — Cost worth it?
**Yes**. ≥3000 tokens/turn savings × N turns × M sessions = significant cost reduction. Plus higher effective context budget for user work.

### Decision
- **ACCEPTED for v5.0** — Phase 7 lands:
  - `tools/tool_search.py` — keyword + select + required-term query modes; returns deferred tool schemas in `<functions>` block per Runnable's wire format.
  - `tools/registry.py:apply_tool_search_deferral` — replace Phase-2 stub with real implementation.
  - Per-tool `should_defer=True` flags on the **deferred set**: `view_image`, `list_dir`, `notebook_edit` (Phase 7 initial pass; Phases 9-10 will mark `task`, `todo_*`, `create_*`, `web_fetch`, `ask_user`, `skill_*` as deferred too).
  - Per-tool `always_load=True` flags on the **never-defer set**: `tool_search` itself (model needs it to load anything else); `read_file` / `grep` / `glob` / `edit_file` / `write_file` / `bash` / `python_exec` (most-frequently-used; deferring these hurts more than it helps).

### Algorithm details (Runnable parity)
1. **Query parsing** — three modes from the same `query` string:
   - `select:Read,Edit,Grep` → exact-name fetch (case-insensitive). Useful for sub-agents/post-compaction where the model knows the name.
   - `+slack send` → required-term: `slack` MUST be in the result; remaining terms rank.
   - `notebook jupyter` → keyword search across name + description, ranked by match count.
2. **Tool name parsing** — Runnable handles `mcp__server__action` (split on `__` then `_`) AND regular tools (split CamelCase + underscore). v5 adopts the same. Most v5 tools are snake_case so the CamelCase branch is rarely exercised.
3. **Result wire format** — `<functions>{"description": ..., "name": ..., "parameters": ...}</functions>` block. Once present in conversation, the deferred tool is callable like any always-loaded tool. Bedrock honors this because it just sees the function definition appended to the tools list at the API level.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** — constraint = `Bedrock + .ipynb`:
- Up-stream: Phase 8's `core/query_engine.py` will call `apply_tool_search_deferral(tools, enabled=True)` per turn before passing the (visible_tools, tool_search_tool) pair to `BedrockClient.chat()`.
- Down-stream: deferred tool names ship in a system-reminder block at message start; full schemas are loaded on demand via tool_search. Bedrock-side: identical to how Anthropic's API treats Runnable's deferred tools.
- Drops Runnable-specific feature gates (`feature('FORK_SUBAGENT')`, `KAIROS`, `KAIROS_BRIEF`, `tengu_glacier_2xr`) — those are Anthropic-internal experiments, not applicable to v5.
- Adapts the GrowthBook-flag fork-tool branch: v5 has no GrowthBook; `apply_tool_search_deferral(enabled=...)` is a simple boolean toggle from the QueryEngine.

### Affected files
- compact_v5/MAIN/agent/tools/tool_search.py (new — port of ToolSearchTool.ts core logic)
- compact_v5/MAIN/agent/tools/registry.py (`apply_tool_search_deferral` real implementation; replaces Phase-2 stub)
- compact_v5/MAIN/agent/tools/__init__.py (extended bootstrap_built_ins)
- compact_v5/MAIN/agent/tools/{view_image,list_dir,notebook_edit}.py (set `should_defer=True`)
- compact_v5/MAIN/agent/tests/unit/test_tool_search.py (new)
- compact_v5/MAIN/agent/tests/tools/ (extension of existing tests for deferral interaction)

### Linked port-log rows
- #014 — Runnable ToolSearchTool/ToolSearchTool.ts (keyword + select + required-term query modes) → tools/tool_search.py
- #015 — Runnable ToolSearchTool/prompt.ts (`isDeferredTool` rule + `getPrompt` body) → tools/tool_search.py:_DESCRIPTION + tools/registry.py:_is_deferred
- (No row for utils/toolSearch.ts — its `isToolSearchEnabledOptimistic` feature-gate logic is GrowthBook-specific and N/A for v5.)

---

## ADR-014 — Phase 8 QueryEngine + retry + errors + IterationBudget
- Date: 2026-04-30
- Phase ID: 08
- Status: ACCEPTED
- Source:
  - Runnable: `gg-claude-code-runnable/src/QueryEngine.ts` (1295 LOC) — main agent loop
  - Runnable: `gg-claude-code-runnable/src/services/api/withRetry.ts` (822 LOC) — retry + jittered backoff
  - Runnable: `gg-claude-code-runnable/src/services/api/errors.ts` (1207 LOC) — error message generators + retryability classification
  - v4: `compact_v4/MAIN/agent/sagemaker_agent.py:8190` (`IterationBudget` — Hermes pattern adopted by v4 in v4.9.4)
  - v4: `:8278` (`Agent` class) + `:8650` (`Agent.run`) — main agent loop
  - v4: ErrorClassifier + RetryPolicy already inline in Phase-1 `runtime/bedrock_client.py`
  - V5_PLAN.md Phase 8 acceptance: end-to-end mock test (tool_use → tool runs → final answer) AND tool_search deferred-loading round-trip works.
  - Phase 7 contract (ADR-013, blocker #3 fix): query_engine MUST call `apply_tool_search_deferral(enabled=True)` per turn AND extract discovered tool names via `tool_search_discovered_names()` to wire deferred tools into the next turn's API call.

### Question 1 — Replacement or addition?
- **REPLACEMENT** of v4's monolithic `Agent.run` loop (lines 8650-9450+, ~800 LOC) with a clean `core/query_engine.py` (target ~400 LOC).
- **EXTRACTION** of Phase-1 inlined `ErrorClassifier` + `RetryPolicy` from `runtime/bedrock_client.py` into dedicated `core/errors.py` + `core/retry.py` modules (Phase-1 ADR-005 noted this would happen in Phase 8).
- **ADDITION** of `core/budget.py` — `IterationBudget` class (Hermes pattern; PS Issue #2: visible budget that prevents runaway sub-agent costs).

### Question 2 — Architectural justification
**Why core/ package boundary**:
- v4's `Agent` class is 1500+ LOC of mixed concerns (loop + retry + errors + budget + compaction + skill auto-trigger + UI hooks). Reviewing the loop logic requires reading the whole class.
- v5 splits into 4 focused modules with clear single responsibilities. Each is independently testable.
- Phase 8 deliberately ships a **MINIMAL** QueryEngine. Compaction (microcompact / context_collapse / LLM summary), skill auto-trigger, repetition guard, and other v4-Agent features are explicitly **out of scope** for Phase 8 — they land in Phase 10 (skills) and Phase 13 (polish). This keeps Phase 8 reviewable and the test surface bounded.

### Phase 8 SCOPE (what's in)
1. `core/budget.py` — `IterationBudget` class (Hermes pattern; thread-safe consume/remaining/used). Verbatim port of v4's `IterationBudget` at `sagemaker_agent.py:8190`.
2. `core/errors.py` — extract `BedrockErrorCategory` + `ErrorClassifier` from Phase-1 `runtime/bedrock_client.py`. Same classifier semantics; cleaner imports for testing.
3. `core/retry.py` — extract `RetryPolicy` from Phase-1 `runtime/bedrock_client.py`. Jittered exponential backoff (~1s, 2s, 4s, 8s with up-to-30% jitter; MAX_RETRIES=4). Verbatim.
4. `core/query_engine.py` — the main loop. **Single responsibility**: take a user message, call BedrockClient, handle tool_use, execute tools, feed tool_result back, loop until end_turn / budget exhaustion / max_turns. Plus Phase-7 wiring per ADR-013 blocker #3 contract.

### Phase 8 OUT OF SCOPE (deferred)
- Compaction logic (microcompact / context_collapse / LLM summary) — Phase 13 polish OR Phase 10 if needed for skills.
- Skill auto-trigger — Phase 10.
- Repetition guard — defer; not in V5_PLAN Phase 8 acceptance.
- Cost tracking + budget UI — Phase 11 (notebook UX).
- AGENT_STATUS.md auto-update — Phase 13 polish.
- Auto-checkpoint (`_maybe_auto_checkpoint`) — Phase 13 polish.
- _PENDING_IMAGES queue consumption (Phase 4 view_image side channel) — query_engine drains it before each chat() call. THIS IS IN SCOPE.
- _RECENT_DIFFS recording — defer.
- File-read tracking population (Phase 4 contract) — query_engine marks files as read after each successful read_file call. IN SCOPE.

### Phase 7 wiring contract (in-scope, ADR-013 blocker #3)
1. Per-turn: call `apply_tool_search_deferral(tools, enabled=True)` → `(visible_tools, deferred_names)`.
2. If `deferred_names` is non-empty, prepend a `<system-reminder>` block to the user message announcing them.
3. Pass `context={"active_tools": <full_pool>}` when executing tool_search so it filters correctly.
4. After each model turn, scan tool_use blocks for `tool_search` calls in the just-completed turn. After their tool_result fires, call `tool_search_discovered_names(tool_result_text)` and add those tools' schemas to the NEXT turn's `tools=` API param (via the `discovered_tools` set on the QueryEngine).

### Question 3 — Cost
- Token cost (static prompt): 0 (core/ is runtime code).
- Token cost (per turn): ~30 tokens for the optional system-reminder block announcing deferred names. Negligible vs the savings (~770 tokens/turn from Phase 7 deferral).
- Code complexity: ~800 LOC across 4 core/ modules + ~300 LOC tests. Replaces ~1500 LOC of v4 monolith.
- Maintenance: each concern in its own file; tests target each.

### Question 4 — Cost worth it?
**Yes**. Phase 8 is the integration phase that makes v5 actually run. Without it, none of the prior phases are exercisable.

### Decision
- **ACCEPTED for v5.0** — 4 core/ modules + tests + integration test demonstrating end-to-end loop with tool_search deferred-loading round-trip.

### Runnable-fidelity impact
**FAITHFUL-WITH-JUSTIFIED-ADAPTATION** — constraint = `Bedrock` + `.ipynb`:
- QueryEngine adapts Runnable's main loop to Bedrock (no streaming differences, no Anthropic-specific OAuth flows, no GrowthBook feature flags).
- Drops Runnable-specific UI hooks (Ink JSX) — v5 uses simple `output_fn` callback for printing per turn.
- Drops Runnable's complex retryability classifier in favor of v4's already-tested simpler version (Phase 1 verbatim).
- IterationBudget is Hermes pattern, not Runnable-original; v4 adopted it; v5 inherits via verbatim port.

### PS Issue mapping
- **PS Issue #2 (iteration budget visible)**: `core/budget.py` exposes `consume() / remaining() / used() / total()` for the Phase-11 ipywidgets UI to display a live progress bar. Phase 11 will land the UI; Phase 8 lands the data plumbing.

### Affected files
- compact_v5/MAIN/agent/core/__init__.py (new)
- compact_v5/MAIN/agent/core/budget.py (new — IterationBudget)
- compact_v5/MAIN/agent/core/errors.py (new — extract from runtime/bedrock_client.py)
- compact_v5/MAIN/agent/core/retry.py (new — extract from runtime/bedrock_client.py)
- compact_v5/MAIN/agent/core/query_engine.py (new — main loop)
- compact_v5/MAIN/agent/tests/unit/test_budget.py (new)
- compact_v5/MAIN/agent/tests/unit/test_errors.py (new)
- compact_v5/MAIN/agent/tests/unit/test_retry.py (new)
- compact_v5/MAIN/agent/tests/integration/test_query_engine.py (new — end-to-end mock test + tool_search round-trip)

### Linked port-log rows
- #016 — Hermes IterationBudget (via v4) → core/budget.py (verbatim)
- #017 — Phase-1 ErrorClassifier extraction → core/errors.py (verbatim)
- #018 — Phase-1 RetryPolicy extraction → core/retry.py (verbatim)
- #019 — Runnable QueryEngine.ts (main agent loop) → core/query_engine.py (ADAPT — minimal v5 scope)
- #020 — Runnable services/api/withRetry.ts (retry + jittered backoff) → core/retry.py (already covered by #018; this row records the parity claim)
- (No row for services/api/errors.ts — v5 uses v4's simpler ErrorClassifier; Phase 12+ may extend.)

---

## ADR-015 — Phase 9: Sub-agent + Task tool (forkSubagent budget sharing)

- Date: 2026-04-30
- Phase ID: 09
- Status: ACCEPTED
- Source: gg-claude-code-runnable/src/tools/AgentTool/forkSubagent.ts (210 LOC) + AgentTool.tsx (1397 LOC) + runAgent.ts (973 LOC)
            v4 sagemaker_agent.py:_run_task_tool (line 8350) + _build_subagent_env_details + _build_subagent_handoff_block + AGENT_TYPES (line 6914)

### Question 1 — Replacement or addition?
- **REPLACEMENT** of v4's `_run_task_tool` (~600 LOC inline in `Agent` class) + `AGENT_TYPES` dict + handoff/env helpers, all currently inline in `sagemaker_agent.py`.
- v5 reorganizes into: `subagent/env.py` (env-details builder), `subagent/handoff.py` (AGENT_STATUS slice + todos + recent files), `subagent/spawn.py` (fork-style spawn that shares IterationBudget), `tools/task.py` (the user-facing tool).
- Cite v4: sagemaker_agent.py:8350 (_run_task_tool), 7695 (_build_subagent_env_details), 7771 (_build_subagent_handoff_block), 6914 (AGENT_TYPES).

### Question 2 — Architectural justification
v5's value-add over v4:
- **Shared IterationBudget** (ADR-014 PS Issue #2 wiring): child QueryEngine constructed with `budget=parent.budget`. v4 inlines a similar pattern but the budget object is buried in the monolith; v5 makes it a public constructor parameter.
- **Module surface for testing**: each piece (env probing, handoff slicing, spawn) testable independently. v4's _run_task_tool can only be tested via Agent.run integration.
- **Fail-quiet contracts**: env/handoff probes never raise — sub-agent spawn must not fail because git timed out. v4 has the same contract; v5 documents it explicitly via tests.
- **AGENT_TYPES staying minimal**: Phase 9 ships `general` only. The `build`/`plan`/`explore`/`verify` agent types from v4 can land later; their prompts are large and reviewable as data, not code.

### Question 3 — Cost
- Token cost (static prompt): +0 — task tool description goes via deferred-loading (Phase 7) in plan-mode caller.
- Token cost (per turn): unchanged for parent. Child gets fresh prompt assembly + handoff block (bounded ≤ ~1500 chars after _SUBAGENT_STATUS_MAX_CHARS + _SUBAGENT_TODOS_MAX_CHARS sanitization).
- Code complexity: ~500 LOC across 4 files (compared to v4's ~600 LOC inline).
- Maintenance: subagent/ owners can iterate without touching agent loop; Phase 11 UI plumbs sub-agent progress separately.

### Question 4 — Cost worth it?
YES. Sub-agents are the primary mechanism for parallel/specialized work; without them v5 cannot match v4 functionality, blocking ship. forkSubagent budget-sharing is the precise mechanism Hermes contributed in v4.9.4 — without it, a parent + N sub-agents could collectively blow the cost ceiling.

### Decision
- **ACCEPTED** for v5.0.
- Phase 9 ships:
  - `subagent/env.py` — `build_env_details(agent_type, depth, workspace=None)` returning a 6-line block. Fail-quiet on git probes. Verbatim port of `_build_subagent_env_details`.
  - `subagent/handoff.py` — `build_handoff_block(status_path=None, todos_text=None, recent_files=None)` returning AGENT_STATUS slice + active todos + recent file paths. Each section optional + bounded. Verbatim port of `_build_subagent_handoff_block` minus the status_doc / RECENT_DIFFS globals coupling (v5 takes inputs as parameters so callers in Phase 11 can wire them).
  - `subagent/spawn.py` — `spawn_subagent(parent_engine, prompt, agent_type, max_turns=None)` that creates a child `QueryEngine(budget=parent_engine.budget, ...)` with a fresh message buffer and runs the prompt. Returns `(text, child_engine)`. Includes depth-limit enforcement.
  - `tools/task.py` — task tool registered via `tools/__init__.py:bootstrap_built_ins`. Description: "Launch a sub-agent for a specific task." Schema: `{description, prompt, subagent_type}`. Executes via `spawn_subagent(...)`. Marked `should_defer=True` (low-frequency).
- Phase 9 does NOT ship: AGENT_TYPES configuration (build/plan/explore/verify prompts), worktree isolation (build agent type only — defer to Phase 11), parallel sub-agent dispatch.

### Budget reservation
- Static prompt: +0 tokens (task tool description not in static prompt; deferred via Phase 7).
- Per-turn (when task tool invoked): child agent's per-turn cost = parent's per-turn cost (same budget). Parent's per-turn cost: +1 task-tool schema if not deferred, 0 if deferred. v5 marks task as `should_defer=True` → 0 added per-turn for non-task-using turns.

### Reconciliation
After Phase 9 lands:
- Static prompt token count must remain at 2498 (no change).
- task tool registered with `should_defer=True` (parity with Phase 7 deferred set).
- Test `test_subagent_shares_iteration_budget` proves the budget is shared.
- Test `test_subagent_parent_context_unchanged` proves the parent's message buffer is not mutated by sub-agent dispatch.

### Linked port-log rows
- #021 — forkSubagent.ts (budget sharing pattern) → subagent/spawn.py (ADAPT — drops experimental fork branch, drops cache-prefix-identical message replay)
- #022 — _build_subagent_env_details (v4) → subagent/env.py (PORT — verbatim with parameterized workspace)
- #023 — _build_subagent_handoff_block (v4) → subagent/handoff.py (ADAPT — accepts inputs as parameters instead of pulling from globals)
- #024 — _run_task_tool (v4) → tools/task.py (ADAPT — minimal Phase-9 scope; AGENT_TYPES + worktree deferred)

---

## ADR-016 — Phase 10: Skills + auto-trigger + Hermes filter (PS Issue #1)

- Date: 2026-04-30
- Phase ID: 10
- Status: ACCEPTED
- Source: gg-claude-code-runnable/src/tools/SkillTool/ + skills/loadAllSkills.ts
            v4 sagemaker_agent.py:SkillManager (line 2684) + 10 skills directories under compact_v4/MAIN/agent/skills/
            hermes-agent (skill-filtering-by-available-tools pattern)
            v4.9.5 self-patching skills (CONFIG.enable_skill_patching opt-in)

### Question 1 — Replacement or addition?
- **REPLACEMENT** of v4's `SkillManager` (~470 LOC inline at sagemaker_agent.py:2684) and `tool_skill` / `tool_skill_propose_patch` executors. v5 reorganizes into `skills/manager.py` + `tools/skill.py` + `tools/skill_propose_patch.py`.
- 10 skills directories (`batch`, `clara`, `design`, `html`, `reflexion`, `report`, `review`, `security-review`, `simplify`, `verify`) ported BYTE-FOR-BYTE under `skills/` (no content edits). User memory + V5_PLAN.md require this verbatim preservation.
- ADDITION: Hermes-style skill filtering by available tools (PS Issue #1). Optional `requires_tools` frontmatter field; if a skill declares it, the skill is filtered out of auto-trigger when its required tools aren't in the active pool. Backwards-compatible — existing skills don't need the field.

### Question 2 — Architectural justification
- **All 10 skills must load** (V5_PLAN.md acceptance) — they are battle-tested production behavior shipping with v4.
- **Auto-trigger respects v4.9.6 default-OFF** (V5_PLAN.md acceptance) — `CONFIG.enable_skill_auto_trigger=False` AND per-skill `auto_trigger: false` default = no auto-loading without explicit opt-in. v4.9.6 made this conservative for cost reasons (avoid silent injection of large skill bodies).
- **`skill_propose_patch` opt-in** — `CONFIG.enable_skill_patching=False` default; tool returns no-op message unless flipped. v4.9.5 ships the same opt-in semantics (8 safety rails: opt-in, propose-not-apply, diff preview, snapshot, audit log, time-stamped proposal files, per-skill .proposed/, never-touches-live).
- **Hermes filter (PS Issue #1)**: in scenarios where a tool is blocked or deferred, surfacing a skill that needs that tool just frustrates the model. The filter improves signal-to-noise for the auto-trigger reminder block. Optional + backwards-compatible.

### Question 3 — Cost
- Token cost (static prompt): +0 — `skill` and `skill_propose_patch` tools marked `should_defer=True`. Auto-trigger reminder added to dynamic tail only when relevant skills found (≤120 chars per skill description × ≤5 skills = ~600 tokens worst case, only when auto-trigger fires).
- Token cost (per turn): unchanged for non-skill turns. Active skill body injected in the dynamic tail when a skill is active (capped via `read_skill(name, max_chars=12000)`).
- Code complexity: ~600 LOC across skills/manager.py + 2 tools (vs v4's 470 LOC inline).
- Maintenance: skills/ directories byte-for-byte from v4; AIPower already syncs from this canonical source. Hermes filter is ~30 LOC of optional filtering logic.

### Question 4 — Cost worth it?
YES.
- Skills are core product surface — without them v5 doesn't match v4 functionality, blocking ship.
- Hermes filter cost is tiny relative to its UX value (avoids "I'd suggest using `verify` skill" when bash is blocked).
- Self-patching is opt-in so default users don't pay any complexity.

### Decision
- **ACCEPTED** for v5.0.
- Phase 10 ships:
  - `skills/__init__.py` + `skills/manager.py` — `SkillManager` class with `discover()` / `list_skills()` / `read_skill(name, max_chars)` / `get_active_skill_prompt()` / `discover_relevant(user_message, active_tools=None)` / `list_for_prompt(budget_tokens=0)` / `propose_patch()` / `list_proposals()` / `apply_proposal()` / `revert_skill()`. Hermes filter sits inside `discover_relevant` via the new `active_tools` parameter.
  - `skills/<10 dirs>/` — copied byte-for-byte from compact_v4/MAIN/agent/skills/.
  - `tools/skill.py` — list, activate, read, deactivate. Marked `should_defer=True`.
  - `tools/skill_propose_patch.py` — propose-only (never auto-applies). Returns no-op message when `CONFIG.enable_skill_patching=False`. Marked `should_defer=True`.
- Phase 10 does NOT ship: a `skill_apply` tool (apply is operator-only via `/skill apply` slash command in Phase 11 UX), automatic skill auto-trigger (default-OFF preserved), domain-specific skills (powerbi-dashboard variants stay in AIPower repo).

### Budget reservation
- Static prompt: +0 tokens (both new tools deferred).
- Per-turn (when skill active): up to 12000 chars of skill content (~3000 tokens) injected after cache boundary. Same as v4.
- Dynamic-tail auto-trigger reminder: capped at SKILL_LISTING_DESC_CAP=250 chars × ≤5 skills = ~250 tokens worst case.

### Reconciliation
After Phase 10 lands:
- Static prompt token count must remain at 2498 (no change).
- All 10 skills load via `SkillManager.discover()`.
- Default config: no skill auto-loads without explicit opt-in.
- Default config: `skill_propose_patch` returns no-op message.
- Hermes filter: skills with `requires_tools` not subset of `active_tools` are filtered from `discover_relevant`.

### Linked port-log rows
- #025 — v4 SkillManager → skills/manager.py (PORT — verbatim port; CONFIG.workspace decoupled to constructor parameter for testability)
- #026 — v4 tool_skill → tools/skill.py (ADAPT — uses new SkillManager surface; should_defer=True)
- #027 — v4 tool_skill_propose_patch → tools/skill_propose_patch.py (ADAPT — same opt-in contract; should_defer=True)
- #028 — Hermes skill-filtering-by-available-tools pattern → SkillManager.discover_relevant(active_tools) (ADAPT — optional `requires_tools` frontmatter field; backwards-compatible)
- #029 — 10 skills/ directories from v4 → compact_v5/MAIN/agent/skills/ (PURE COPY — content byte-for-byte; no rows for individual skills as they are reused content not Runnable patterns)

---

## ADR-017 — Phase 11: Notebook UX + entry + thinking/budget UI (PS Issue #4)

- Date: 2026-04-30
- Phase ID: 11
- Status: ACCEPTED
- Source: v4 sagemaker_agent.py:create_chat_ui (line 9735, ~2000 LOC) + chat.ipynb (5 cells) + chat.md
            v4.8.0 thinking-mode UI surface (PS Issue #4)
            v4.9.4 IterationBudget UI commitment (PS Issue #2 — Phase 8 shipped data model, Phase 11 wires the widget)

### Question 1 — Replacement or addition?
- **REPLACEMENT** of v4's `create_chat_ui()` + `chat.ipynb` shipping surface. v5 reorganizes into: `agent.py` (public Agent class), `entry.py` (cell-0 import target), `ui/chat_ui.py` (UI orchestration), `ui/widgets.py` (data widgets), `chat.ipynb` (notebook), `chat.md` (companion).
- ADDITION of explicit PS Issue #4 visibility (thinking budget shown in UI; v4 had thinking-mode toggle but no in-UI surface for budget consumption).

### Question 2 — Architectural justification
v5 value-add over v4:
- **agent.py is its own public surface** (~200 LOC) — wraps QueryEngine + SkillManager + Config + BedrockClient. v4's `Agent` is buried in the monolith and exposes everything.
- **ChatUI is much smaller** (~150 LOC vs v4's ~2000 LOC). Most of v4's complexity is HTML rendering of message history; v5 delegates to ipywidgets and lets the browser handle layout. Phase 11 also intentionally drops v4's complex chat-display HTML rendering for the minimal MVP — operators get text output + widgets, not the v4 full-fidelity chat display.
- **PS Issue #2 visible IterationBudget**: Phase 8 shipped `IterationBudget` data model. Phase 11 wires `consume() / used() / total()` to an `ipywidgets.IntProgress` so the user sees the budget burning down as parent + sub-agents consume it.
- **PS Issue #4 visible thinking budget**: Phase 1 already sends thinking config when enabled; Phase 11 surfaces a small label showing the current thinking-budget setting AND a checkbox to toggle it.

### Question 3 — Cost
- Token cost (static prompt): +0.
- Token cost (per turn): +0 — UI is post-Bedrock display only.
- Code complexity: ~600 LOC across 7 files vs v4's ~2000 LOC inline.
- Maintenance: ipywidgets-dependent code is in `ui/`, isolated from agent loop.

### Question 4 — Cost worth it?
YES. The notebook is the user's ONLY surface for v5 — without `chat.ipynb` running cleanly, the entire ship pipeline is moot.

### Decision
- **ACCEPTED** for v5.0.
- Phase 11 ships:
  - `agent.py` — `Agent` class. Wraps `BedrockClient` + `IterationBudget` + `QueryEngine` + optional `SkillManager`. Public methods: `run(message)`, `clear()`, `stop()`.
  - `entry.py` — cell-0 import target. Re-exports `Agent`, `create_chat_ui`, `CONFIG`.
  - `ui/chat_ui.py` — `create_chat_ui()` factory + `ChatUI` class. ipywidgets-dependent. Falls back to console-mode when ipywidgets is unavailable.
  - `ui/widgets.py` — `IterationBudgetWidget` (data class wrapping ipywidgets.IntProgress; PS Issue #2) + `ThinkingBudgetWidget` (data class wrapping ipywidgets.HBox with toggle + budget label; PS Issue #4).
  - `chat.ipynb` — minimal 4 cells: install / config / launch / quick-reminder.
  - `chat.md` — companion markdown explaining the notebook.
  - `tests/integration/test_notebook_smoke.py` — hello-world turn vs mock Bedrock; UI factory smoke test (no ipywidgets render assertions, just construction).
- Phase 11 does NOT ship: full v4 chat-display HTML rendering (defer to Phase 13 polish), v4's compact/clean buttons (microcompact lands as separate phase if at all), parallel sub-agent visualization, model-switcher widget (CONFIG.model_id static), session-history persistence (SessionManager from Phase 1 already exists; Phase 11 doesn't auto-restore).

### Budget reservation
- Static prompt: +0 tokens.
- ipywidgets dependency already in install list (v4 cell 1 has it).
- Phase 11 does not change static prompt or per-turn schemas.

### Reconciliation
After Phase 11 lands:
- Notebook smoke test passes against mock Bedrock.
- IterationBudget widget renders + updates after `consume()`.
- Thinking-budget label shows current value.
- chat.ipynb cells 1-3 import cleanly, cell 3 returns a UI object.

### Linked port-log rows
- #030 — v4 create_chat_ui → ui/chat_ui.py (ADAPT — minimal Phase-11 scope)
- #031 — v4 Agent class (extracted from monolith) → agent.py (ADAPT — public-surface wrapper around Phase 8-10 modules)
- #032 — v4 chat.ipynb → compact_v5/MAIN/agent/chat.ipynb (ADAPT — minimal cells)
- #033 — Phase-8 IterationBudget data model → ui/widgets.py:IterationBudgetWidget (ADDITION — PS Issue #2 fix; ipywidgets progress bar)
- #034 — v4.8.0 thinking-mode → ui/widgets.py:ThinkingBudgetWidget (ADDITION — PS Issue #4 fix; toggle + budget label)

---

## ADR-018 — Phase 12: Parity tests vs v4 (audit gate before Phase 13)

- Date: 2026-04-30
- Phase ID: 12
- Status: ACCEPTED
- Source: V5_PLAN.md §Phase 12 + risk register #8 (critical-scenario must-pass suite)

### Question 1 — Replacement or addition?
- **ADDITION** of two parity test files plus an in-PORT_LOG appendix tracking documented v4-vs-v5 differences.

### Question 2 — Architectural justification
- V5_PLAN.md success metric #1: "Functional parity with v4.10.10 (same skills work, same security holds, same notebook UX)." Phase 12 is the verification gate.
- Risk #8 (parity blind spots): "Add must-pass critical-scenario suite (security deny, blocked-tool continuation, retry, prompt assembly, resume after compaction) requiring 100% pass; the ≥90% threshold applies only to non-critical scenarios."
- Phase 8.5 thin-slice already covers cross-phase integration; Phase 12 expands to specific v4 behavioral parity.

### Question 3 — Cost
- Token cost (static prompt): +0.
- Code complexity: ~600 LOC of test fixtures.
- Maintenance: parity suite is the verification spec — changes when v4 behavior changes (which is never; v4 is frozen).

### Question 4 — Cost worth it?
YES. Without Phase 12, ship-gate is unverifiable. v5 ships only if both critical (100%) AND non-critical (≥90%) parity gates pass.

### Decision
- **ACCEPTED** for v5.0.
- Phase 12 ships:
  - `tests/parity/test_parity_critical.py` — 15 critical scenarios (must all pass). Covers: security deny, plan-mode dispatch gate, retry policy semantics, prompt assembly invariants (slot-2 + budget + boundary), resume-after-compaction equivalence (Phase 11 clear+rerun), Phase 7 wiring contract end-to-end, sub-agent budget sharing end-to-end, skill auto-trigger default-OFF, 10 production skills load, PS Issue #2/#4 widget visibility, context-overflow clean exit, tool exception trap, deferred-loading payload exclusion, BedrockClient cache-fallback semantics, mock-mode response shape parity.
  - `tests/parity/test_parity_non_critical.py` — 10 non-critical scenarios (≥9/10 must pass). Covers: tool result truncation length, error message exact wording, skill CSO format advisory, audit log line format, widget HTML exact markup, depth-exceeded message wording, plan-mode error message wording, tool-search wire format details, frontmatter parser edge cases, env-details line count.
- Phase 12 does NOT actually run v4 — v4 is frozen at sha9bf0...e1c2 (compact_v4/). Fixtures encode "this is what v4 does for this input" and assert v5 matches. Differences are documented in PORT_LOG row #035 (parity appendix).

### Budget reservation
- Static prompt: +0.
- Per-turn: +0.

### Reconciliation
After Phase 12 lands:
- 15/15 critical scenarios pass.
- ≥9/10 non-critical scenarios pass (allowed slip: 1).
- Any non-critical FAIL is documented in PORT_LOG #035 (parity differences appendix) with rationale.

### Linked port-log rows
- #035 — V5_PLAN.md §Phase 12 → tests/parity/test_parity_critical.py + test_parity_non_critical.py + PORT_LOG parity appendix (ADD — parity verification surface)

---

## ADR-019 — Phase 13: Cutover + ship zip + tag v5.0.0 (FINAL)

- Date: 2026-04-30
- Phase ID: 13
- Status: ACCEPTED
- Source: V5_PLAN.md §Phase 13 + v4 _rebuild_zip.py (181 LOC) + v4 verify_ship_zip.py (161 LOC)

### Question 1 — Replacement or addition?
- **REPLACEMENT** of the v4 ship pipeline for v5: `compact_v5/_rebuild_zip.py` (adapted to walk the nested package layout) + `compact_v5/verify_ship_zip.py` (REUSED verbatim from v4 with light tweaks for v5 file list).

### Question 2 — Architectural justification
- v5 ships only when ALL gates met: phases 00-12 DONE, parity 15/15+10/10, audit 7/7. Phase 13 is the ship pipeline.
- v4's `_rebuild_zip.py` walks `MAIN/agent/` (monolith). v5 walks `compact_v5/MAIN/agent/` AND preserves the nested-package layout (`core/`, `tools/`, `skills/`, etc.) so imports work in the unzipped directory.

### Question 3 — Cost
- Token cost: +0.
- Code complexity: ~250 LOC (~200 zip builder + ~50 README).

### Question 4 — Cost worth it?
YES. v5 doesn't ship without a zip. This is the FINAL phase.

### Decision
- **ACCEPTED** for v5.0.
- Phase 13 ships:
  - `compact_v5/_rebuild_zip.py` — adapted from v4. Walks `MAIN/agent/` in v5 layout. Preserves nested packages. Excludes tests/changelogs/_status/docs/_archive/__pycache__.
  - `compact_v5/verify_ship_zip.py` — adapts v4's verifier to v5's runtime file list (chat.ipynb, chat.md, entry.py, agent/__init__.py, core/, tools/, skills/, runtime/, prompt/, ui/, subagent/, security/, mcp/, memory.md, AGENT_STATUS.md).
  - `compact_v5/CHANGELOG.md` — top-level v5 release notes summarizing all phases.
  - `compact_v5/README.md` — minimal: how to extract + run chat.ipynb.
  - Final tag: `v5.0.0` after the zip extracts cleanly + verify_ship_zip passes.
- Phase 13 does NOT: merge to main (v4 stays on main; v5 lives on `v5-build` until user explicitly ships); upload zip to a release; auto-deploy.

### Budget reservation
- Static prompt: +0.
- Per-turn: +0.

### Reconciliation
After Phase 13 lands:
- `compact_v5.zip` extracts to a flat-ish layout and `chat.ipynb` opens cleanly.
- `verify_ship_zip.py` reports PASS.
- Tests still 437/4 (Phase 12 baseline).
- Final tag `v5.0.0` created.

### Linked port-log rows
- #036 — v4 _rebuild_zip.py → compact_v5/_rebuild_zip.py (ADAPT — walks v5 nested-package layout).
- #037 — v4 verify_ship_zip.py → compact_v5/verify_ship_zip.py (ADAPT — v5 runtime file list).

---

## (Append future ADRs below this line — keep numerical order 020, 021, ...)

## ADR-025 — Block D (v5.0.1): Slash-command dispatcher (20 v4 + /auth + 6 LF)

**Date**: 2026-05-03
**Phase ID**: v5.0.1 Block D
**Status**: ACCEPTED

### Context
v4 dispatched `/foo` commands inline in the chat-input handler, with
~700 LOC of cascaded if/elif chains across sagemaker_agent.py:10789-:11341.
v5 needs the same surface (constraint #1 v4.10.10 baseline) but in a
testable shape. Plus 6 Learning-Factory additions documented in
Wave-5-DEEP entry.

### Decision
Single `commands.py` module with:
- `CommandResult` dataclass — return shape with consumed/deny_auth/side_effect.
- One handler function per command (cmd_cost / cmd_skills / cmd_revert / etc.).
- Dispatch table (`_DISPATCH`) — single source of truth ordered so
  longer prefixes win (`/skill clear` matches before `/skills`).
- `/auth` runs BEFORE custom dispatch per v4 :11314 explicit check.
- `is_command()` + `dispatch_command()` public API.
- Wired in `ConsoleChatUI.send` + `WidgetChatUI._on_send`: messages
  starting with `/` route to dispatcher BEFORE agent.run().

### Rationale
- Flat dispatch table is easier to test than v4's monolithic if/elif.
- Each handler is small (10-30 LOC) and delegates to existing v5
  services (SkillManager, SnapshotManager, TOKENS, CONFIG).
- LF additions (/init, /skillify, /dream, /promote-to-skill) are
  scaffolding-only here; Block H+ wires the real /dream writer, Block
  I extends the others.
- Order matters in dispatch table — `/skill suggestions` listed before
  `/skill use` so the longer prefix wins. Verified by spot tests.

### Affected files
- NEW: `compact_v5/MAIN/agent/commands.py` (~450 LOC)
- NEW: `compact_v5/MAIN/agent/tests/integration/test_block_d.py` (19 tests)
- MODIFIED: `compact_v5/MAIN/agent/ui/chat_ui.py` — pre-agent dispatch
  in both `ConsoleChatUI.send` and `WidgetChatUI._on_send`.

### Linked port-log rows
- #065 — commands dispatcher + chat-UI routing

### Validation
- 547 pass + 5 skipped (was 528 + 5 at end of Block C+; +19 net new).
- verify_ship_zip.py: PASS (110 files / 300.1 KB / 37%).

## ADR-024 — Block C+ (v5.0.1): Approval/diff dispatch + rate limits + ipywidgets fallback + Block-C UI remaps

**Date**: 2026-05-03
**Phase ID**: v5.0.1 Block C+
**Status**: ACCEPTED

### Context
Block C shipped runtime safety helpers (destructive catalog, cd+git
guard, multi-cd, pipe-segment, comment-label) but their UI-flow wiring
was explicitly deferred to Block C+ per ADR-023's "Notes / known
scope remaps" table. Block C+ also adds the approval gate (Phase 4
ADR-010 commitment) + rate limiter (v4 :8731-8740) + per-tool
always-allow + reason prompt + ipywidgets-headless fallback.

### Decision
Single `ui/approval_dialog.py` module with three exports:
  - `PermissionDialog` — per-tool dialog, ipywidgets + text-mode paths.
  - `ApprovalResult` — dataclass (approved / always_allow / reason / timed_out).
  - `RateLimiter` — sliding-window message rate limit + per-session cap.

Wire-in QueryEngine.run():
  - Rate limit check at run() entry; on hit, return `stop_reason="rate_limited"`
    without consuming budget.
  - Approval gate before tool.execute(): when both flags set AND
    `client.mock_mode is False`, prompt + block on user decision.

### Key contracts (locked by tests)
1. **mock_mode bypass.** When `client.mock_mode=True` (test runs), the
   gate is silent — tests don't wedge on stdin. Verified via existing
   525-test suite which constructs all clients with `mock_mode=True`.
2. **Sticky always-allow.** First-time Always-allow stores
   `CONFIG._always_allowed[tool_name] = True`; subsequent dialogs
   short-circuit to ApprovalResult(approved=True, always_allow=True,
   reason="sticky: ..."). Sticky check runs FIRST (before
   `_override_decision`) so even tests with overrides honor it.
3. **Headless watchdog.** ipywidgets-unavailable → text-mode prompt
   with 60s timeout; non-TTY stdin → defaults to DENY (never silent
   auto-approve).
4. **Block-C helper integration.** PermissionDialog.render_warnings()
   pulls from `security.bash_safety` for the four Block-C UI-only
   helpers (C-11/C-12/C-13/C-14) and surfaces them in the dialog body.
5. **Rate limit sliding window.** Drops timestamps older than 60s
   before count; per-session cap separate from per-minute cap.

### Affected files
- NEW: `compact_v5/MAIN/agent/ui/approval_dialog.py` (~280 LOC)
- NEW: `compact_v5/MAIN/agent/tests/integration/test_block_c_plus.py` (14 tests)
- MODIFIED: `compact_v5/MAIN/agent/core/query_engine.py` (gate + rate limiter wiring)

### Linked port-log rows
- #064 — PermissionDialog + RateLimiter + Block-C UI remap wiring

### Validation
- 525 pass + 5 skipped (was 511 + 5 at end of Block C; +14 net new).
- verify_ship_zip.py: PASS (109 files / 292.8 KB / 37%).
- Closes ADR-023 §Notes / known scope remaps for Block-C UI items
  (C-11/C-12/C-13/C-14 lock-tested via test_approval_renders_*).

## ADR-023 — Block C (v5.0.1): Runtime safety + JSON repair + injection scan + bash hardening + ADR-020 0-5 / 0-10 remap

**Date**: 2026-05-03
**Phase ID**: v5.0.1 Block C
**Status**: ACCEPTED

### Context
v5.0.0 left several runtime-safety gaps that PS#7 + Wave-5-DEEP R1/R5
flagged: 40-call exec limit hit mid-task, no JSON repair on malformed
tool args, no injection scanner on skill bodies, secret-scanner light
on patterns (13 vs Runnable's 38), no Windows-edit safety (UTF-16 BOM,
UNC, CRLF, smart quotes, OneDrive mtime drift), no bash-side exit-code
semantics or destructive-command catalog. Block C closes all of these
plus ADR-020 remap rows 0-5 (scratchpad) and 0-10 (v4-native injection
scanner).

### Decision
Pure additive: 5 new helper modules + 2 tool extensions + query_engine
gate wiring. Zero changes to existing class APIs.

NEW modules (all under `runtime/` or `security/` for proximity to use):
- `security/json_repair.py` (~115 LOC) — Hermes-style malformed-JSON
  repair (5 strategies, fallback `{}`).
- `security/injection_scanner.py` (~100 LOC) — 12 v4 patterns +
  invisible/zero-width char class.
- `security/scratchpad.py` (~110 LOC) — per-process scratchpad dir
  under platform tempdir; cleanup_registry-registered GC.
- `security/edit_file_safety.py` (~190 LOC) — quote norm + UTF-16 BOM +
  UNC reject + CRLF round-trip + Windows staleness fallback.
- `security/bash_safety.py` (~225 LOC) — exit-code semantics + 13-pattern
  destructive catalog + cd+git compound + multi-cd + pipe-segment
  splitter + bash-comment-label extractor.

EXTENDED:
- `security/manager.py` — SECRET_PATTERNS expanded 13 → 38 (R5 A1).
- `tools/edit_file.py` — wired UNC reject + UTF-16 BOM detection + quote
  norm + line-ending round-trip on read/write.
- `tools/bash.py` — wired interpret_command_result post-exec.
- `core/query_engine.py` — wired exec-limit gate (PS#7 verbatim message)
  + repetition detector (3rd identical call blocks) + JSON repair on
  tool_use.input string parsing.

### Rationale
- Each helper module is self-contained: zero cross-module coupling.
  Lets future blocks (e.g. Block A Compactor) consume them without
  pulling in tool-level state.
- Exec-limit gate counts bash + python_exec only (v4 parity). 200-call
  default (v4.10.10 baseline; was 40 in earlier v4). The OTHER TOOLS
  STILL WORK message is preserved verbatim so the model can recover.
- Repetition detector: same (tool_name, args_hash) on 3rd consecutive
  identical call (threshold=2 within rolling 6-call window). Catches
  the most common stuck-loop shape without false-positives on
  legitimate retry-with-different-args patterns.
- JSON repair: 5 progressive strategies. First successful one wins;
  irrecoverable garbage falls back to `{}` (caller's tool surfaces
  the missing-arg error to the model).
- Edit-file wiring: BOM detection runs FIRST so UTF-16 LE files (Notepad
  default) are read correctly. Match runs in normalized space (LF + ASCII
  quotes); restore happens at write to preserve the file's original
  shape.
- Destructive catalog (13 patterns) covers rm -rf / git force-push /
  reset --hard / clean / DROP/TRUNCATE / kubectl delete / terraform
  destroy / docker rm,rmi,prune / dd to /dev/ / fork bomb / aws s3 rb
  --force / redis FLUSHALL. Approval flow (Block C+) consumes these.

### Runnable-fidelity impact
- All 14 Block C SYNTHESIS_MASTER items + 2 ADR-020 remap rows
  (0-5, 0-10) implemented or tested. C-4 preserveQuoteStyle is included
  as a helper but not wired into edit_file (intentional — it's a UX
  niceness, not a correctness gate; C-3 normalize_quotes is the
  load-bearing piece).
- v4 verbatim port: SECRET_PATTERNS (13 v4 patterns preserved + 25 new).
  Exec-limit gate text + threshold preserved.
- Net-new: scratchpad uses cleanup_registry (Block B+) for GC instead
  of v4's __del__ pattern.

### Affected files
- NEW: `compact_v5/MAIN/agent/security/json_repair.py`
- NEW: `compact_v5/MAIN/agent/security/injection_scanner.py`
- NEW: `compact_v5/MAIN/agent/security/scratchpad.py`
- NEW: `compact_v5/MAIN/agent/security/edit_file_safety.py`
- NEW: `compact_v5/MAIN/agent/security/bash_safety.py`
- NEW: `compact_v5/MAIN/agent/tests/integration/test_block_c.py`
- MODIFIED: `compact_v5/MAIN/agent/security/manager.py` (SECRET_PATTERNS)
- MODIFIED: `compact_v5/MAIN/agent/tools/edit_file.py` (UNC + BOM + norm wiring)
- MODIFIED: `compact_v5/MAIN/agent/tools/bash.py` (exit-code semantics)
- MODIFIED: `compact_v5/MAIN/agent/core/query_engine.py` (exec-limit + repetition + json_repair)

### Linked port-log rows
- #057 — Hermes JSON repair
- #058 — v4-native injection scanner (ADR-020 0-10 remap)
- #059 — scratchpad (ADR-020 0-5 remap)
- #060 — edit_file safety (C-3..C-8)
- #061 — bash safety (C-9..C-14)
- #062 — exec-limit + repetition detector (PS#7 fix)
- #063 — secret pattern expansion (R5 A1, 13 → 38)

### Validation
- 507 pass + 5 skipped (was 490 + 5 at end of Block B+; +17 net new).
- verify_ship_zip.py: PASS (108 files / 286.8 KB / 37%).
- PS#7 STRUCTURALLY closed (exec-limit gate + verbatim recovery message).

### Notes / known scope remaps (Block C UI-only helpers → Block C+)

Codex Block-C iter-1 finding #2 (HIGH) flagged that several Block C
helpers exist but aren't wired into runtime flow. After analysis, the
unwired helpers are all approval/UI surface — they feed Block C+'s
approval flow + history display rather than the core dispatch path.
The table below records the explicit Block-C+ landing site for each.

| Item | Capability | LOC | Lands in Block | Implementation site (target file) | Lock test (Block where it runs) |
|---|---|---|---|---|---|
| C-11 | cd+git compound bare-repo guard | 40 | **Block C+** (approval flow) | `ui/approval_dialog.py`: surface warning before bash exec | `test_approval_warns_on_cd_git_bare_repo` (Block C+) |
| C-12 | Multiple-cd detection | 10 | **Block C+** (approval flow) | `ui/approval_dialog.py`: bump approval requirement for multi-cd | `test_approval_required_on_multi_cd` (Block C+) |
| C-13 | Pipe-segment per-segment permission | 30 | **Block C+** (approval flow) | `ui/approval_dialog.py`: per-segment approval line | `test_approval_per_pipe_segment` (Block C+) |
| C-14 | Bash comment-label extraction | 15 | **Block C+** (UI history) | `ui/widgets.py:HistoryRow`: render comment as label | `test_history_row_labels_with_bash_comment` (Block C+) |

All four helpers are already in `security/bash_safety.py` (Block C)
with 100% test coverage. Block C+ wiring is API-stable — no helper
changes needed.

Block C iter-1 finding #2 also flagged C-13 (pipe-segment) and the
bash destructive-warning catalog as unwired. **Both are now wired in
tools/bash.py** post-iter-1 (the warning is annotated to output;
Block C+ adds the pre-exec approval surface). Lock coverage already
exists via test_destructive_command_warning + test_pipe_segment_permission_check.

## ADR-022 — Block B+ (v5.0.1): SessionManager + cost-limit + AGENT_STATUS + FileCache + ADR-020 0-7/0-9 remap

**Date**: 2026-05-03
**Phase ID**: v5.0.1 Block B+
**Status**: ACCEPTED

### Context
Block B closed PS#5 (cost not persisted) + PS#6 (budget read from wrong
source) at the data layer (TokenTracker.restore + singleton). Block B+
ships the persistence + handoff machinery that consumes those data
points: SessionManager (atomic save/load), AGENT_STATUS.md auto-load
(handoff continuity), FileCache thread-local context (sub-agent
isolation boundary), cleanup_registry (atexit cost-flush — Block 0 item
0-7 remap), feature_flags fail-closed (Block 0 item 0-9 remap).

### Decision
Verbatim ports of v4 SessionManager (~80 LOC) + FileCache (~125 LOC).
v5 adapts only:
- Constructor `config` injection on all four singletons
  (TokenTracker / AuditLogger / SnapshotManager / SessionManager)
  with **lazy `@property _config`** so `importlib.reload(runtime.config)`
  in tests doesn't strand the singleton on a stale CONFIG instance.
  Caught by `test_session_cost_limit_warns_at_100pct` failing
  intermittently when run after `test_env_validation_wired_into_config`.
- Cost-runtime warning is per-`run()`-instance via `_warned_over_budget`
  flag, not per-process; this avoids spamming the user with the same
  warning every turn.
- AGENT_STATUS auto-load is **idempotent** — read once per Agent
  instance, cached in `_agent_status_text`. Subsequent `run()` calls
  reuse the cached text. Cap at 8 KB so a runaway status doc can't
  blow out the prompt.
- cleanup_registry tolerates Jupyter kernel signal-handler hijacking
  (`signal.signal()` install wrapped in `try/except`).
- session_cost_limit is **warn-and-continue** at 100% per user
  2026-05-03 Plan v3 update — v5 matches v4 UX. True hard halt is at
  cloud-budget level (AWS Budget Action / GCP Cloud Function — see
  `docs/CLOUD_COST_CAPS_SETUP.md`).

### Rationale
- Lazy `@property _config` lookup is cheap (one attribute access +
  module dict lookup) and eliminates a class of test-isolation bugs
  that would have grown over time.
- Block 0 ADR-020 0-7 (cleanup_registry) lands in B+ because B+ is the
  first block with a real consumer (TokenTracker._flush_cost_on_exit).
  Block 0 ADR-020 0-9 (feature_flags) lands here because B+ is the
  first block whose modules use feature_enabled() at import time.
- AGENT_STATUS auto-load reads the file once per Agent instance, not
  per turn — handoff continuity should reflect what the user wrote at
  session start, not racing-with-edits status updates.
- session_cost_limit warn-vs-halt: matches v4 UX. Per user
  2026-05-03 update, hard halts belong at cloud-budget level so even
  unattended overnight runs are bounded without breaking the
  visible-budget UX users prefer.

### Runnable-fidelity impact
- SessionManager: TS Promise → Python sync; tempfile.mkstemp + os.replace
  is the equivalent atomic-rename pattern.
- FileCache: TS class → Python class with threading.RLock + threading.local.
- cleanupRegistry: full equivalence (atexit + signal handlers).
- entry.ts fail-closed: feature_flags helper exposes the same surface
  Runnable's `flags.ts` provides.
- Cost-runtime warning: v4 had print(); v5 routes through query_engine
  output_fn so notebook UI captures it.

### Affected files
- NEW: `compact_v5/MAIN/agent/runtime/session.py`
- NEW: `compact_v5/MAIN/agent/runtime/file_cache.py`
- NEW: `compact_v5/MAIN/agent/runtime/cleanup_registry.py`
- NEW: `compact_v5/MAIN/agent/runtime/feature_flags.py`
- NEW: `compact_v5/MAIN/agent/tests/integration/test_block_b_plus.py`
- MODIFIED: `compact_v5/MAIN/agent/runtime/tokens.py` (lazy @property
  _config + atexit cost-flush registration)
- MODIFIED: `compact_v5/MAIN/agent/runtime/audit.py` (lazy @property)
- MODIFIED: `compact_v5/MAIN/agent/runtime/snapshot.py` (lazy @property)
- MODIFIED: `compact_v5/MAIN/agent/__init__.py` (Agent.run AGENT_STATUS
  auto-load + first-call cache)
- MODIFIED: `compact_v5/MAIN/agent/core/query_engine.py` (cost runtime
  warning post-chat())
- MODIFIED: `compact_v5/MAIN/agent/subagent/spawn.py` (FILE_CACHE
  save/restore around child.run try/finally)

### Linked port-log rows
- #048 — SessionManager
- #049 — FileCache
- #050 — cleanup_registry (ADR-020 0-7 remap)
- #051 — feature_flags (ADR-020 0-9 remap)
- #052 — cost runtime warning
- #053 — sub-agent FILE_CACHE save/restore boundary
- #054 — atexit cost-flush
- #055 — AGENT_STATUS auto-load

### Validation
- 483 pass + 5 skipped (was 469 + 5 at end of Block B; +14 net new).
- verify_ship_zip.py: PASS (104 files / 272.4 KB / 38%).

### PS_problems closed/extended
- **PS#5** (session cost not persisted): SessionManager round-trip
  test confirms TOKENS.session_cost survives save → load. Lock test:
  test_session_save_load_preserves_cost.
- **PS#6** (budget read from wrong source): test_tokens_singleton_is_budget_source
  asserts both Agents share TOKENS state. Lock test in this Block.

### Notes / known scope remaps (Block B+ items B+3..B+6)

Codex Block-B+ iter-1 finding #4 (LOW) flagged B+3..B+6 as
UNDECLARED_PATTERN until remap is concretely declared. Per
constraint #3 (no deferrals), this table records the explicit
landing Block + lock test for each:

| Item | Capability | LOC | Lands in Block | Implementation site (target file) | Lock test (Block where it runs) |
|---|---|---|---|---|---|
| B+3 | 4-line cost block format (R11 N10) | 15 | **Block I** (UI/widgets) | `ui/widgets.py:CostWidget.render_html` (4-line block: total / per-model / per-agent / cache) | `test_cost_widget_renders_4_line_block` (Block I) |
| B+4 | Local OTel-style counters (R11 N11) | 25 | **Block I** | `runtime/tokens.py:TokenTracker.get_otel_counters()` (local SQLite/JSON only — never external endpoint per Bedrock-only constraint) | `test_otel_counters_emitted_locally_only` (Block I) |
| B+5 | Recursive advisor sub-cost accounting (R11 N12) | 30 | **Block A** (Compactor) | `core/compactor.py` calls `TOKENS.add(usage, agent_kind="advisor")` for the auxiliary compaction-summary model | `test_advisor_sub_cost_attributed` (Block A) |
| B+6 | contextWindow refresh on every cost update (R11 N13) | 5 | **Block I** | hook `IterationBudgetWidget.update()` to fire on every TOKENS.add (per-update refresh) | `test_iteration_budget_widget_refreshes_on_token_add` (Block I) |

Each row's TARGET BLOCK must verify:
- (a) the row above is honored
- (b) the lock test exists and is green
- (c) PORT_LOG row references the implementing Block

This closes Codex iter-1 finding #4 (UNDECLARED_PATTERN) for B+3..B+6.

## ADR-021 — Block B (v5.0.1): TokenTracker + AuditLogger + SnapshotManager + tokenEstimation + ADR-020 0-3/0-8 remap

**Date**: 2026-05-03
**Phase ID**: v5.0.1 Block B
**Status**: ACCEPTED

### Context
v5.0.0 shipped without TokenTracker / AuditLogger / SnapshotManager — a
documented PS_problem (#5 cost not persisted, #6 budget read from wrong
source). Block B closes that gap with verbatim ports of v4's three
classes plus Runnable's tokenEstimation helpers (so Block A Compactor
has accurate context-budget math) plus per-agent attribution so parent
+ sub-agent costs roll up correctly. Block 0 items 0-3 (BEDROCK_EXTRA_
PARAMS_HEADERS) and 0-8 (validate_bounded_int_env_var) land here per
ADR-020's remap table — Block B owns runtime/bedrock_client + runtime/
config consumers.

### Options
1. **Verbatim ports + Runnable estimators** (chosen): port v4's
   TokenTracker / AuditLogger / SnapshotManager byte-for-byte (modulo
   constructor injection of `config`), add Runnable's tokenEstimation
   helpers, extend TokenTracker with per-agent attribution. Wire only
   in places that already exist (QueryEngine, edit_file, write_file).
   Skill apply_proposal wiring deferred to Block I (skill manager).
2. **Re-implement from Runnable's TokenTracker**: would lose v4's
   cache-aware pricing math (cache_read=10%, cache_write=125%) which
   v5 needs for Bedrock prompt caching cost reporting. Rejected.
3. **Skip per-agent attribution to Block B+**: Plan v3 Block B+
   acceptance test demands `TOKENS.parent_input_tokens > 0 AND
   TOKENS.subagent_input_tokens["build"] > 0` so the data model has
   to land here even if the wiring contract finalizes in B+. Done as
   chosen.

### Decision
Option 1. Block B ships:
- `runtime/tokens.py` (verbatim TokenTracker + MODEL_COSTS + per-agent
  attribution + EXCLUDED_MODELS_FOR_CACHE_BREAK + IMAGE_MAX_TOKEN_SIZE
  + bytes_per_token_for_file_type + estimate_message_tokens +
  has_thinking_blocks + rough_token_count_for_block + rough_token_
  count_for_message + final_context_tokens_from_last_response +
  token_count_with_estimation + ToolResult dataclass)
- `runtime/audit.py` (verbatim AuditLogger + AuditEntry)
- `runtime/snapshot.py` (verbatim SnapshotManager)
- `runtime/env_validation.py` (validate_bounded_int_env_var per
  ADR-020 0-8 remap)
- `runtime/bedrock_client.py` extended:
    - `BEDROCK_EXTRA_PARAMS_HEADERS` frozenset (per ADR-020 0-3 remap)
    - `BedrockClient.count_tokens()` method (B-1, R4 #41 MUST)
- Wiring:
    - `core/query_engine.py` — TOKENS.add(usage, model_id, agent_kind)
      after every chat() return; AUDIT.log on every tool dispatch
      (success + failure paths); `agent_kind` + `session_id` ctor params
    - `subagent/spawn.py` — `_new_child_engine` accepts `agent_type`
      and forwards to QueryEngine ctor as `agent_kind`
    - `tools/edit_file.py` + `tools/write_file.py` — SNAPSHOTS.save
      best-effort before write/edit
- Tests: 18 new (17 pass + 1 T5 skipped without RUN_REAL_BEDROCK).

### Rationale
- Verbatim ports preserve v4's battle-tested invariants (cache pricing
  math, LRU snapshot eviction, redaction sensitive-key set).
- Constructor `config` injection avoids the v4 import-time global
  dependency that Phase 1-13 already moved away from for `BedrockClient`.
- Per-agent attribution data model lives on the same singleton so
  `session_cost == parent_cost + sum(subagent_cost.values())` is
  enforceable (the test_token_tracker_per_agent_breakdown lock pins
  this within $0.0001).
- ADR-020 0-3 and 0-8 land here because runtime/bedrock_client.py and
  runtime/config.py consumers are the targets — Block 0 didn't touch
  either.
- The remaining ADR-020 remap rows (0-4 / 0-5 / 0-6 / 0-7 / 0-9 / 0-10)
  land in their declared Blocks (B+ / C / E+F) — none silently dropped.

### Runnable-fidelity impact
- MODEL_COSTS: dropped `fast-mode` tier (Anthropic-direct only); kept
  cache-aware math. FAITHFUL-WITH-JUSTIFIED-ADAPTATION.
- tokenEstimation: TS Promise-based async → Python sync. Per-block-type
  math preserved. countTokensViaHaikuFallback (B-2) deferred-with-
  intent to Block A (where it's used) — no scope drop.
- EXCLUDED_MODELS_FOR_CACHE_BREAK: net-new (R4 #14 was a Wave-5-DEEP
  finding not in original Runnable code).

### Affected files
- NEW: `compact_v5/MAIN/agent/runtime/tokens.py`
- NEW: `compact_v5/MAIN/agent/runtime/audit.py`
- NEW: `compact_v5/MAIN/agent/runtime/snapshot.py`
- NEW: `compact_v5/MAIN/agent/runtime/env_validation.py`
- NEW: `compact_v5/MAIN/agent/tests/integration/test_block_b.py`
- MODIFIED: `compact_v5/MAIN/agent/runtime/bedrock_client.py`
- MODIFIED: `compact_v5/MAIN/agent/core/query_engine.py`
- MODIFIED: `compact_v5/MAIN/agent/subagent/spawn.py`
- MODIFIED: `compact_v5/MAIN/agent/tools/edit_file.py`
- MODIFIED: `compact_v5/MAIN/agent/tools/write_file.py`
- MODIFIED: `compact_v5/MAIN/agent/tests/integration/test_subagent.py`
  (mock signatures updated to accept new `agent_type` kwarg)

### Linked port-log rows
- #039 — TokenTracker
- #040 — MODEL_COSTS + EXCLUDED_MODELS_FOR_CACHE_BREAK + canonicalize_model_id
- #041 — Runnable tokenEstimation helpers
- #042 — ToolResult dataclass
- #043 — AuditLogger + AuditEntry
- #044 — SnapshotManager
- #045 — validate_bounded_int_env_var (Block 0 item 0-8 remap)
- #046 — BEDROCK_EXTRA_PARAMS_HEADERS (Block 0 item 0-3 remap)
- #047 — BedrockClient.count_tokens

### Validation
- 459 pass + 5 skipped (was 442 + 4 at end of Block 0; +17 pass + 1 skip).
- verify_ship_zip.py: PASS (100 files / 262.4 KB / 38%).
- 1 T5 test gated by `RUN_REAL_BEDROCK=1` (~$0.005); to be run as part
  of Block J real-Bedrock smoke gate so Block B doesn't burn API budget
  per local pytest.

### PS_problems addressed
- **PS#5 (session cost not persisted)**: TokenTracker has `restore()`
  reconstructor; Block B+ wires it to SessionManager `/resume`.
- **PS#6 (budget read from wrong source)**: `_TOKENS.add` always reads
  CONFIG.session_cost_limit; Block B+ acceptance test
  test_tokens_singleton_is_budget_source pins this.

## ADR-020 — Block 0 (v5.0.1): `sagemaker_agent.py` shim + notebook smoke gate

**Date**: 2026-05-02
**Phase ID**: v5.0.1 Block 0
**Status**: ACCEPTED

### Context
v5.0.0 reorganized the v4 monolith into nested packages (`runtime/`, `core/`,
`agent/`, `ui/`, `tools/`, `skills/`, `subagent/`, `security/`, `prompt/`).
The Phase-11 notebook (`chat.ipynb`) imports from `entry`. v4's notebook
imports from `sagemaker_agent`. v5.0.1 hard-constraint #2 requires that v4's
canonical `chat.ipynb` continues to work unchanged on v5 via a shim — the
notebook should not need to know about the v5 reorg.

### Options
1. **Drop-in shim** (chosen): tiny `sagemaker_agent.py` at the agent root that
   re-exports `entry`'s public surface. v4's `from sagemaker_agent import …`
   line resolves; everything else stays in its v5 module.
2. **Replace v5 chat.ipynb with v4's verbatim**: most faithful to constraint
   #2 but pulls in v4 widgets that depend on Block-B+ (`session_cost_limit`)
   and Block-D (slash commands) features not yet present at Block 0. Defers
   to Block E+F.
3. **Move all v5 surface back to a top-level `sagemaker_agent` module**:
   undoes the Phase-2..11 file-per-section structure. Violates constraint
   #5 (minimum file count) and constraint #6 (architecture-first).

### Decision
Option 1. Block 0 ships a 30-LOC shim that re-exports `Agent`, `BEDROCK_MODELS`,
`CONFIG`, `IterationBudget`, `SkillManager`, and `create_chat_ui` from `entry`.
v5's existing `chat.ipynb` is left untouched at Block 0; full notebook-shape
restoration to v4 canonical is Block E+F territory (per Wave-3
COMBINED_ARCHITECTURE.md).

### Rationale
- Smallest possible surface that satisfies constraint #2 at Block 0 boundary.
- Zero impact on Phase 1-13 module structure.
- v4's `from sagemaker_agent import {BEDROCK_MODELS, CONFIG, create_chat_ui}`
  line works literally — verified by `test_smoke_imports` and
  `test_v4_import_compat`.
- The shim is implementation-free; it cannot drift from v5 internals because
  it re-binds, never re-implements.

### Runnable-fidelity impact
None. This shim is v4-compat, not Runnable-derived.

### Affected files
- NEW: `compact_v5/MAIN/agent/sagemaker_agent.py` (shim)
- NEW: `compact_v5/MAIN/agent/tests/integration/test_block0_shim.py` (5 tests)
- UPDATED: `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` (row #038)
- UPDATED: `compact_v5/_status/V5_BUILD_STATUS.md` (Block 0 done; next = smoke gate / Block B)

### Linked port-log rows
- #038 — Block 0 shim.

### Validation
- 5/5 Block 0 tests green (TEST_DESIGN §Block 0).
- Full pytest 442 passed + 4 skipped (was 437 + 4; +5 new from Block 0).
- `verify_ship_zip.py`: PASS.
- Codex AXIS A/B/C: APPROVE (review at `_status/codex_reviews/block-0.md`).

### Notes / known scope remaps (constraint #3 — no deferrals)

SYNTHESIS_MASTER.md §Block 0 (lines 32-47) tags 9 additional items
"Block 0" because that is where their PORT_LOG row originates. All 9 are
**ported, not dropped** — but their *implementation* lands in the Block
that architecturally owns the touched module. Each item below has an
explicit landing Block + a test gate where its lock test runs. This
table is the no-deferrals contract.

| Item | Capability | LOC | Lands in Block | Implementation site (target file) | Lock test (Block where it runs) |
|---|---|---|---|---|---|
| 0-1 | SYSTEM_PROMPT verbatim re-export | 0 (doc) | Block 0 | `prompt/*.md` (Phase 6, present) + this PORT_LOG row #038 | `test_v4_import_compat` (Block 0) |
| 0-2 | `getSessionStartDate()` + `getLocalMonthYear()` (cache-stable date) | 15 | **Block E+F** | `prompt/env_block.py` (formatter for `prompt/env_block.md`) | `test_env_block_uses_month_year_not_iso_date` (Block E+F) |
| 0-3 | `BEDROCK_EXTRA_PARAMS_HEADERS` Set | 5 | **Block B** | `runtime/bedrock_client.py` (constant + reference at invoke site) | `test_extra_params_in_body_not_headers` (Block B) |
| 0-4 | env block format (Windows-shell hint, OS version, Notes appendix) | 30 | **Block E+F** | `prompt/env_block.md` + `prompt/env_block.py` | `test_env_block_includes_shell_hint_and_notes` (Block E+F) |
| 0-5 | `getScratchpadInstructions()` per-session scratchpad dir | 30 | **Block C** | `security/scratchpad.py` + allowlist update + `prompt/scratchpad.md` | `test_scratchpad_dir_pre_allowlisted_and_gc` (Block C) |
| 0-6 | `getKnowledgeCutoff(modelId)` Sonnet 4.6 / Haiku 4.5 cutoffs | 5 | **Block E+F** | `prompt/env_block.py` (cutoff lookup table) | `test_env_block_emits_model_specific_knowledge_cutoff` (Block E+F) |
| 0-7 | `cleanupRegistry` graceful-shutdown for SIGINT / atexit | 15 | **Block B+** | `runtime/cleanup_registry.py` + `runtime/session.py` flush hook | `test_cleanup_registry_flushes_on_atexit_and_sigint` (Block B+) |
| 0-8 | `validateBoundedIntEnvVar` env-validation helper | 30 | **Block B** | `runtime/env_validation.py` (used by Config dataclass numeric loaders) | `test_env_validation_clamps_and_rejects_bad_input` (Block B) |
| 0-9 | Feature-flag fail-closed at import boundary | 30 | **Block B+** | `runtime/feature_flags.py` (returns False for banned modules) + `entry.py` import-time guard | `test_banned_module_imports_fail_closed` (Block B+) |
| 0-10 | `_scan_for_prompt_injection` + `_INJECTION_PATTERNS` (v4-native) | 40 | **Block C** | `security/injection_scanner.py` (v4 verbatim port from sagemaker_agent.py:7509-7541) | `test_injection_scanner_v4_native` (Block C; already in TEST_DESIGN §Block C) |

Codex AXIS C (Block 0 review #1) flagged this remap as UNDECLARED_PATTERN
when only stated in prose; the table above declares it concretely. Each
target Block's review (when it lands) must verify (a) the row above is
honored, (b) the lock test exists, and (c) the SYNTHESIS_MASTER §3 row
for that item references the implementing Block. Plan-level cross-link
added to `_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` Block 0 table head
note.
