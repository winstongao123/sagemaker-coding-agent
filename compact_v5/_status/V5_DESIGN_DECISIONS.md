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

## (Append future ADRs below this line — keep numerical order 014, 015, ...)
