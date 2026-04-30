# PS_V5 — Learnings from External Repos

**Purpose**: This document tracks **what we learned and adopted from each external reference repo** — Runnable Claude Code, Hermes, Learning_Factory — and how those learnings translated into v5 design / code. Living document, updated each phase.

**Companion docs**:
- `PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md` — what v5 changes vs v4.10.10.
- `V5_RUNNABLE_PORT_LOG.md` — mechanical port-log (Codex-verifiable).
- `V5_DESIGN_DECISIONS.md` — ADRs (architectural rationale).
- `compact_v5/docs/htmls/PS_DEEP_DIVE_RUNNABLE.html` — 10-chapter Runnable architecture e-book.
- `compact_v5/docs/htmls/HERMES_VS_CODING_AGENT_v4.html` — Hermes vs v4 comparison.

**Scope rules**:
- Each entry MUST cite the source repo + file:section + the v5 destination.
- Distinguish between adopted (lands in v5) vs studied-only (informs design but no code lands).
- Note adaptations forced by v5 constraints (Bedrock / no-network / python_exec / .ipynb).
- Document the "we made it BETTER than X" delta where applicable — required by the v5 mission ("v5 must be better than Runnable, Hermes, LF").

**Source repos**:
- **Runnable Claude Code** — primary textbook. Path: `_archive/compare_code/gg-claude-code-runnable/src/`. Released TS reference implementation of Anthropic's Claude Code CLI.
- **Hermes** — agent-loop patterns (IterationBudget, skill filtering by available tools, graceful failure). Path: `D:/Github/hermes-agent/`.
- **Learning_Factory** — build-process infrastructure (STATE.md persistence, shadow-git checkpoints, design-log doctrine). Path: `D:/Github/Learning_Factory/`.

---

## Phase 0 — Scaffolding

### From Learning_Factory: append-only ADR doctrine
- **Source**: LF design-log convention: ADRs are numbered (ADR-NNN), append-only, mark superseded with `STATUS=SUPERSEDED-BY-ADR-XXX`.
- **Adopted**: `compact_v5/_status/V5_DESIGN_DECISIONS.md` follows this exact format. Codex review template requires every PORT_LOG row to reference an ADR-NNN.
- **Better than LF**: v5 adds the mandatory **Addition Gate** template (4 questions: replacement-or-addition / architectural justification / cost / cost-worth-it) for any pattern adoption. LF didn't enforce this — v4 in fact failed because every addition individually passed review but the aggregate broke. The Addition Gate prevents that.

### From LF: STATE.md persistence + Resume Protocol
- **Source**: LF `STATE.md` pattern — single living file that captures session state for cold-resume.
- **Adopted**: `compact_v5/_status/V5_BUILD_STATUS.md` is mechanical, overwrite-each-session, with explicit "Last commit sha" field that the resume protocol verifies on cold restart.
- **Better than LF**: v5 adds a 5-step **resume protocol** (`_status/RESUME.md`) with mechanical sha + tag + pytest verification gates. STOP if any check disagrees. LF's STATE.md is informational; v5's is enforcement.

### From Runnable: file-per-section system prompt registry pattern (deferred to Phase 6)
- **Source**: `gg-claude-code-runnable/src/constants/systemPromptSections.ts` (TS section-function registry with cache-boundary marker).
- **Studied, not yet adopted**: Phase 6 ports this. The reference HTML `PS_FLOWCHART_RUNNABLE.html` is included in `compact_v5/docs/htmls/` for design reference until then.

### Reference HTMLs preserved
- **Source**: 6 HTMLs from `PS_ClaudeCode_Insights/` and `compact_v4/docs/`.
- **Adopted**: copied verbatim to `compact_v5/docs/htmls/` (PS_DEEP_DIVE_RUNNABLE, PS_FLOWCHART_RUNNABLE, PS_FLOWCHART_V4, PS_RUNNABLE_VS_LANGGRAPH, HERMES_VS_CODING_AGENT_v4, v4_architecture). These serve as design references during v5 build; Phase 13 generates v5-specific HTMLs alongside.

---

## Phase 1 — Bedrock client + Config

### From Runnable: studied, intentionally NOT adopted (cache-break detection deferred)
- **Source**: `gg-claude-code-runnable/src/services/api/promptCacheBreakDetection.ts`.
- **Studied**: Runnable's detector is sophisticated (systemHash + toolsHash + perToolHashes + cacheControlHash + globalCacheStrategy + betas list). It compares cache-relevant state across turns to identify which section flipped.
- **NOT adopted yet**: it requires multi-block system prompts that v5 doesn't have until Phase 6's `prompt/sections.py` lands. Porting now would build a detector against a structure that doesn't exist yet, causing rework.
- **Deferred to Phase 6** (per ADR-005).
- **Better-than-Runnable angle**: Runnable's detector is reactive (logs breaks after they happen). v5 will combine this with a Codex-verified pre-flight cache invariant test, so cache breaks fail at CI rather than in production.

### From Runnable: claude.ts client NOT adopted (Bedrock-native v4 reused)
- **Source**: `gg-claude-code-runnable/src/services/api/claude.ts`.
- **Reason**: Anthropic-direct (subscriber/OAuth/teamMemory paths). Bedrock has none of those. v4's `BedrockClient` is already Bedrock-native, prompt-cache-aware, retry-classifier-equipped. Verbatim port wins.
- **PORT_LOG**: no row added (pure v4 reuse). ADR-005 documents the decision.

---

## Phase 2 — Tool Protocol + registry

### From Runnable: Tool interface shape (PORT_LOG #001)
- **Source**: `gg-claude-code-runnable/src/Tool.ts` — `Tool` interface + `buildTool` defaults (TOOL_DEFAULTS at line 757).
- **Adopted (ADAPT)**: v5's `ToolDef` Protocol + `ToolRecord` dataclass + `build_tool()` factory.
- **What we kept**: `TOOL_DEFAULTS` semantics — fail-closed defaults (`is_concurrency_safe=False`, `is_read_only=False`, `is_destructive=False`, `enabled=True`). Alias-aware lookup (`toolMatchesName` / `findToolByName`). `searchHint` for ToolSearch (Phase 7). `shouldDefer` / `alwaysLoad` flags.
- **What we dropped**: ALL React/Ink rendering methods (`renderToolUseMessage`, `renderToolResultMessage`, `renderToolUseRejectedMessage`, `renderToolUseProgressMessage`, etc.). Reason: v5 ipywidgets renders in `ui/chat_ui.py` (Phase 11). Constraint = `.ipynb`.
- **What we dropped**: `inputJSONSchema` (MCP-only forward to JSON-Schema since Runnable uses Zod for built-ins) — Python doesn't need the dual-form, single `input_schema: dict` works for both.
- **What we dropped**: `interruptBehavior`, `setToolJSX`, `addNotification`, `sendOSNotification`, `getActivityDescription`, `getToolUseSummary` — no REPL/Ink runtime in `.ipynb`.

### From Runnable: tools.ts registry + assembleToolPool cache invariant (PORT_LOG #002)
- **Source**: `gg-claude-code-runnable/src/tools.ts` — `getAllBaseTools`, `getTools(permissionContext)`, `filterToolsByDenyRules`, `assembleToolPool`, `toolMatchesName`, `findToolByName`.
- **Adopted (ADAPT)**: v5's `tools/registry.py` — `register/unregister`, `get_tools(plan_mode, deny_rules)`, `assemble_tool_pool(plan_mode, deny_rules, mcp_tools)`, `apply_tool_search_deferral(tools, enabled)` stub.
- **What we kept**: cache-stable alphabetical ordering (built-ins prefix → MCP suffix → uniqBy with built-ins winning). MCP server-prefix deny semantics (`mcp__server` and `mcp__server__*`). Plan-mode read-only allowlist semantics.
- **Adapted**: Runnable's complex `DeepImmutable PermissionContext` (multi-source rules: user config / project config / settings / MCP scopes / plan-mode / bypass mode) collapsed into v5's `(plan_mode: bool, deny_rules: set[str] | None)` tuple. Reason: v5's `.ipynb` has a SINGLE approval source (ipywidgets prompt per call). Runnable's multi-source surface doesn't apply. Constraint = `.ipynb`.
- **Better than Runnable**: v5's registry **rejects duplicate registrations** with a loud `ValueError`. Runnable allows tool authors to override existing entries silently — real bug source in v4 where two skills both registered `verify` and the second won. Locked by `test_register_duplicate_name_raises`.
- **Better than Runnable**: v5's `assemble_tool_pool(plan_mode=True)` enforces the allowlist on MCP tools at registry-assembly time. v4 enforced at dispatch time, which let the model see the disallowed tool schema in the initial prompt. v5 hides them entirely.

### From Hermes: studied, NOT yet adopted
- **Source**: `D:/Github/hermes-agent/` IterationBudget pattern (shared budget across parent + sub-agents).
- **Studied**: Hermes's IterationBudget caps total iterations across the parent + every spawned sub-agent. v5 will adopt this in Phase 8 (QueryEngine) and Phase 9 (Sub-agent + Task tool).
- **Deferred**: Phase 8/9 ADRs will track adoption.

---

## Phase 3 — Core read-only tools

### From Runnable: FileReadTool prompt structure (PORT_LOG #003)
- **Source**: `gg-claude-code-runnable/src/tools/FileReadTool/prompt.ts`. Specifically `renderPromptTemplate(lineFormat, maxSizeInstruction, offsetInstruction)` which builds the description string from constituent parts.
- **Adopted (ADAPT)**: `tools/read_file.py:_DESCRIPTION` is a static string adapted from `renderPromptTemplate` with v4-specific bits: tool naming `Read` → `read_file`, "use ls via Bash" → "use list_dir for directories", drops PDF support reference (Phase 4 may add), drops Ink/JSX rendering refs.
- **What we kept**: Runnable's WHEN/WHEN NOT structure — explicitly listing when the tool IS the right choice and when it's NOT. This addresses PS Issue #7 (buried-matrix failure mode in v4 where the tool list was a flat bullet list with no triage guidance, and the model under-attended to mid-list bullets). Each v5 read-only tool description ends with WHEN/WHEN NOT.
- **What we adapted**: tool naming. v4 uses `read_file`, Runnable uses `Read`. v5 keeps `read_file` to avoid confusing the model with the English verb "read".

### From Runnable: GrepTool prompt with critical correction (PORT_LOG #004)
- **Source**: `gg-claude-code-runnable/src/tools/GrepTool/prompt.ts`. The Runnable text says `"A powerful search tool built on ripgrep"`.
- **Adopted (ADAPT) with truthfulness correction**: v5 prompt says "Regex search across files." and "Pattern syntax: Python `re` semantics".
- **Why we corrected**: v5 (and v4) implement grep with Python's `re` module — there is no ripgrep binary in the runtime. If we'd kept Runnable's text verbatim, the model would write ripgrep PCRE2 patterns (e.g., `(?P<name>...)` works but `(?P_name_...)` doesn't, ripgrep extensions like `[[:alpha:]]` don't behave identically to Python's). PS Issue #6 (wiring-bug pattern: tool description claims behavior the executor doesn't implement) — the exact failure mode v5 is meant to prevent.
- **Better than Runnable**: v5 grep prompt is *implementation-truthful*. Runnable's prompt would be wrong in v5's environment.

### From Runnable: GlobTool prompt + v4 allowed_paths fallback addition (PORT_LOG #005)
- **Source**: `gg-claude-code-runnable/src/tools/GlobTool/prompt.ts`. 5-line description.
- **Adopted (ADAPT)** with one v4-specific addition: explicit note about the `allowed_paths` fallback ("if no match in workspace AND no explicit path arg, also search any directories in CONFIG.allowed_paths").
- **Why we added the v4 note**: v4's glob has this fallback (sagemaker_agent.py:4867), and SageMaker users frequently work inside a sub-directory of a parent git repo where the upper levels are in allowed_paths. Without the prompt note, the model wouldn't know that searching from the workspace root might silently extend to the parent.
- **Better than Runnable**: v5 glob can find files in adjacent project dirs without the model needing to know about the allowed_paths feature.

### From Runnable: list_dir studied, NOT adopted (Runnable doesn't have it)
- **Source**: Runnable doesn't have a dedicated list_dir tool — its FileReadTool prompt says "use ls via Bash".
- **Decision**: v5 keeps the dedicated tool (v4 parity). Reason: v5 plan-mode forbids bash, so without `list_dir`, plan-mode users can't inspect directories. v4's `tool_list_dir` was already minimal (~25 LOC) so the maintenance cost is negligible.
- **Better than Runnable**: v5 plan-mode users can navigate the workspace fully. Runnable plan-mode users cannot.

### From v4 SecurityManager: scoped path-validation extraction
- **Source**: v4's `SecurityManager.validate_path` at `compact_v4/MAIN/agent/sagemaker_agent.py`.
- **Adopted (subset)**: extracted the workspace boundary check + symlink escape detection into a new `tools/_path_validation.py` module (~80 LOC). The 134-case destructive-command portion is irrelevant to read-only tools.
- **Phase 5 retirement**: the full SecurityManager port lands in Phase 5; the 4 tool modules switch their imports to use `security.manager.validate_path`. The signature is intentionally identical so the swap is one line per file.
- **Better than v4 (architecturally)**: Phase 3 read-only tools don't pull in the entire 600-LOC SecurityManager class just to do path validation. Cleaner dependencies, faster import, easier to test.

---

## Cross-phase: "Better than X" Tracker (updated)

| Phase | Better than | Where | What |
|-------|-------------|-------|------|
| 0 | LF | ADR doctrine | Mandatory Addition Gate (4 questions) prevents v4-style aggregate-failure pattern. |
| 0 | LF | STATE.md | 5-step resume protocol with mechanical sha/tag/pytest verification gates. |
| 1 | (n/a) | Bedrock | (PS Issue #4 lock test added — same v4 behavior, now regression-proof.) |
| 2 | Runnable | Tool registry | Duplicate-name registration loudly fails (Runnable allows silent override). |
| 2 | Runnable + v4 | Plan-mode | MCP tools filtered at registry-assembly time, not dispatch time. |
| **3** | **Runnable** | **grep prompt** | **Truthful backend claim — Runnable says "ripgrep", v5 says "Python re" (matching what's actually implemented). PS Issue #6 prevention.** |
| **3** | **Runnable** | **list_dir** | **Plan-mode users can inspect directories. Runnable plan-mode users cannot (no list_dir, bash forbidden).** |
| **3** | **Runnable** | **glob prompt** | **Documents v4-specific allowed_paths fallback so the model understands the search scope.** |
| **3** | **v4** | **path validation** | **Scoped extraction (~80 LOC) from v4's 600-LOC SecurityManager — read-only tools don't pull in the whole security class.** |
| **3** | **v4** | **tool ordering** | **Cache-stable alphabetical ordering means future tool additions don't bust the prompt cache for every existing tool.** |
| **3** | **v4** | **concurrency flags** | **Each tool explicitly declares is_concurrency_safe — Phase 9's Task tool can batch parallel read-only calls without heuristics.** |

---

## Phases 4-13

(Future — entries land per phase.)

---

## Cross-phase: "Better than X" Tracker

This section consolidates every place v5 is better than the source repo, for quick scanning.

| Phase | Better than | Where | What |
|-------|-------------|-------|------|
| 0 | LF | ADR doctrine | Mandatory Addition Gate (4 questions) prevents v4-style aggregate-failure pattern. |
| 0 | LF | STATE.md | 5-step resume protocol with mechanical sha/tag/pytest verification gates. |
| 1 | (n/a) | Bedrock | (PS Issue #4 lock test added — same v4 behavior, now regression-proof.) |
| 2 | Runnable | Tool registry | Duplicate-name registration loudly fails (Runnable allows silent override). |
| 2 | Runnable + v4 | Plan-mode | MCP tools filtered at registry-assembly time, not dispatch time. |
