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

## Phase 4 — Core mutating tools + diff_widget

### From Runnable: FileWriteTool prompt (PORT_LOG #006)
- **Source**: `gg-claude-code-runnable/src/tools/FileWriteTool/prompt.ts:getWriteToolDescription`.
- **Adopted (ADAPT)**: `tools/write_file.py:_DESCRIPTION` keeps Runnable's "MUST read first before overwriting" rule and the "prefer Edit for modifying existing files" steering.
- **What we dropped**: Runnable's "NEVER create *.md / README files unless explicitly requested" + "no emojis" rules. These are policy rules that belong in the v5 main system prompt at Phase 6 (per ADR-002 file-per-section), not in the per-tool description. Per-tool descriptions should describe MECHANICS, not POLICY — duplicating policy across every tool would bloat the per-turn token cost.
- **What we adapted**: tool naming Runnable `Write` → v5 `write_file` (v4 parity). Added v4-specific `mode='append'` parameter.

### From Runnable: FileEditTool prompt (PORT_LOG #007)
- **Source**: `gg-claude-code-runnable/src/tools/FileEditTool/prompt.ts:getEditToolDescription`.
- **Adopted (ADAPT)**: keeps Runnable's "MUST read first / exact match / replace_all / smallest old_string" guidance.
- **What we adapted**: line-prefix instruction. Runnable says either "line number + tab" or "spaces + line number + arrow" depending on `isCompactLinePrefixEnabled()`. v5 `read_file` uses a fixed `"line number + | + space"` format; the prompt explicitly mentions that exact format so the model knows to strip the prefix.
- **What we kept from v4**: the stale-check (file modified externally since last read → reject the edit). This is a v4-only feature; Runnable doesn't have it.

### From Runnable: NotebookEditTool prompt (PORT_LOG #008)
- **Source**: `gg-claude-code-runnable/src/tools/NotebookEditTool/prompt.ts:DESCRIPTION + PROMPT`.
- **Adopted (ADAPT)**: cell-index 0-based, action-vs-mode parameter naming.
- **Naming difference**: Runnable uses `edit_mode=insert|replace|delete`; v5 uses `action=` (v4 parity — v4's `_NOTEBOOK_EDIT_ACTIONS` set used `action`, and our chat.ipynb users have muscle-memory for it).
- **What we kept from v4**: atomic write (tmp file + rename). Runnable's TS uses Node fs's `writeFileSync` which has different atomicity guarantees on Windows; v5 explicit `tempfile.mkstemp` + `os.replace` matches v4's POSIX-semantic guarantee.

### From Runnable: FileEditTool/UI.tsx → ui/diff_widget.py (PORT_LOG #009)
- **Source**: `gg-claude-code-runnable/src/tools/FileEditTool/UI.tsx`. ~288 LOC of React/Ink JSX that renders the colored diff in the approval prompt.
- **Adopted (ADAPT)**: same UX semantics, different runtime:
  - Runnable emits Ink JSX (terminal renderer); v5 emits HTML strings (ipywidgets renderer).
  - Both use red/green/gray color cues with `+`/`-`/space markers.
  - Both show file path header.
  - Both show ±3 lines context (default) around hunks.
  - Both offer click-to-expand-full-file (Runnable: separate component, v5: native HTML `<details>`).
- **Constraint forcing adaptation**: `.ipynb` (no JSX/Ink runtime). Genuine — Runnable's TSX output is unrenderable in a Jupyter notebook.
- **Better than Runnable**: v5 uses **stdlib only** (`difflib` + `html.escape`) — no React, no Ink, no third-party deps. Runnable's UI.tsx pulls Ink + React + custom diff utilities. v5 ships ~225 LOC vs Runnable's combined ~600 LOC across UI.tsx + dependencies. Plus v5 escapes untrusted content (HTML-injection safety) — Runnable's TSX runs in a terminal where HTML injection isn't a concern; if Runnable ever ports to a web UI, they'd need to add what we have.

### From v4: read-tracking extracted into a tiny module
- **Source**: v4 `_FILES_READ` set + `_FILE_READ_TIMES` dict + `_FILES_READ_LOCK` threading.Lock at `compact_v4/MAIN/agent/sagemaker_agent.py` (around line 4200).
- **Adopted (subset)**: extracted into `tools/_file_read_tracking.py` (~80 LOC). Same contract — `mark_read(path)`, `was_read(path)`, `is_stale(path)`. Phase-4-only stub: Phase 8 query_engine retires it by bringing the same data into session state.
- **Better than v4 (architecturally)**: read-tracking is a single-purpose module with clear ownership instead of three globals scattered through the v4 monolith.

### From v4: notebook atomic-write helper
- **Source**: v4's notebook_edit at `sagemaker_agent.py:5921` used `tempfile.mkstemp` + `os.replace` inline.
- **Adopted (verbatim, refactored)**: extracted into `_atomic_write_json(path, data)` helper inside `tools/notebook_edit.py`. Same logic; cleaner test surface (`test_notebook_edit_atomic_write_preserves_on_failure` mocks `os.replace` to fail and verifies the original notebook is intact).

---

## Cross-phase: "Better than X" Tracker (updated)

| Phase | Better than | Where | What |
|-------|-------------|-------|------|
| 0 | LF | ADR doctrine | Mandatory Addition Gate (4 questions) prevents v4-style aggregate-failure pattern. |
| 0 | LF | STATE.md | 5-step resume protocol with mechanical sha/tag/pytest verification gates. |
| 1 | (n/a) | Bedrock | (PS Issue #4 lock test added — same v4 behavior, now regression-proof.) |
| 2 | Runnable | Tool registry | Duplicate-name registration loudly fails (Runnable allows silent override). |
| 2 | Runnable + v4 | Plan-mode | MCP tools filtered at registry-assembly time, not dispatch time. |
| 3 | Runnable | grep prompt | Truthful backend claim — Runnable says "ripgrep", v5 says "Python re". PS Issue #6 prevention. |
| 3 | Runnable | list_dir | Plan-mode users can inspect directories. Runnable plan-mode users cannot. |
| 3 | Runnable | glob prompt | Documents v4-specific allowed_paths fallback. |
| 3 | v4 | path validation | Scoped 80-LOC extraction vs v4's 600-LOC SecurityManager. |
| 3 | v4 | tool ordering | Cache-stable alphabetical ordering across tool list. |
| 3 | v4 | concurrency flags | Each tool explicitly declares is_concurrency_safe. |
| **4** | **Runnable** | **diff_widget zero-deps** | **Pure stdlib (difflib + html.escape) vs Runnable's React/Ink stack. ~225 LOC vs combined ~600 LOC.** |
| **4** | **Runnable** | **diff_widget HTML escape** | **Untrusted model content escaped — Runnable's terminal renderer doesn't have this concern, but v5's HTML output would be a web-XSS surface without it. Lock test prevents regression.** |
| **4** | **v4** | **diff in approval prompt** | **Inline colored diff at approval time vs v4's text-only summary. Catches misplaced edits BEFORE the user clicks Approve.** |
| **4** | **v4** | **read-tracking module** | **Single-purpose 80-LOC module vs three scattered globals (_FILES_READ + _FILE_READ_TIMES + _FILES_READ_LOCK).** |
| **4** | **v4** | **stale-check error msg** | **Explicit recovery hint ("Re-read with read_file to refresh, then retry") vs v4's bare error string.** |
| **4** | **v4** | **atomic-write tested** | **`_atomic_write_json` is now mockable; `test_notebook_edit_atomic_write_preserves_on_failure` locks the contract.** |
| **5** | **Runnable** | **bash prompt focus** | **Drops Runnable's ~300 lines of undercover/gh/USER_TYPE branches; v5 keeps a focused 90-line description with WHEN/WHEN NOT triage. Smaller per-turn payload + clearer triage.** |
| **5** | **Runnable** | **python_exec dedicated tool** | **Plan-mode users have a sandboxed Python tool. Runnable plan-mode users have nothing — they must use Bash, which plan-mode forbids.** |
| **5** | **Runnable** | **closure sandbox** | **`open()` / `os.open()` / `io.open()` / `os.remove` / `os.rmdir` / `os.posix_spawn` all wrapped at runtime via closures the user code cannot see. Runnable just documents which tools to avoid; v5/v4 enforce in-process.** |
| **5** | **v4** | **security audit boundary** | **5-file `security/` package (auditable in <30 min) vs v4's 1000+ LOC inline in the 12K-line monolith.** |
| **5** | **v4** | **Python 3.11 portability** | **Closure-sandbox allowlist now includes `_collections_abc`, `keyword`, `reprlib`, `_pyio`, `_compat_pickle`, `_warnings` — observed transitive imports needed for `import json` to work on Python 3.11. v4 hit this gap but never patched.** |
| **5** | **v4** | **rebuild_singleton_for_tests** | **Tests rebuild SECURITY against monkeypatched CONFIG in <1s; v4 testing pattern required fresh process per scenario.** |
| **5** | **v4** | **dynamic SECURITY re-export** | **`security/__init__.py` uses module-level `__getattr__` for `SECURITY` — callers that did `from security import SECURITY` always get the CURRENT singleton, even after rebuild. Eliminates stale-reference bugs.** |

---

## Phase 5 — bash + python_exec + security verbatim from v4

### From Runnable: BashTool prompt (PORT_LOG #010)
- **Source**: `gg-claude-code-runnable/src/tools/BashTool/prompt.ts` — 369 lines covering Runnable-specific behaviors (undercover instructions, gh attribution, sandbox manager, USER_TYPE branches, background-task notes).
- **Adopted (ADAPT)**: `tools/bash.py:_DESCRIPTION` keeps the core (~90 LOC vs Runnable's 369). Drops Runnable-specific content — all inapplicable to Bedrock + .ipynb.
- **Better than Runnable**: smaller, focused description; lower per-turn token cost.

### From v4: security/ package extracted from monolith
- **Source**: v4 `compact_v4/MAIN/agent/sagemaker_agent.py:1298-2148` (SecurityManager class) + adjacent regex constants and helpers.
- **Adopted (verbatim port)**: 5 small files in `compact_v5/MAIN/agent/security/`. Constants split into `dangerous_patterns.py` + `dangerous_python.py`; class + helpers in `manager.py`; HIGH_RISK_TOOLS in `high_risk.py`; package re-exports in `__init__.py` (with dynamic `SECURITY` via module-level `__getattr__`).
- **Better than v4 (auditability)**: 5 files in 30 minutes vs 1000+ LOC inside a 12K-line monolith.
- **Better than v4 (testability)**: `rebuild_singleton_for_tests()` lets pytest rebuild SECURITY against monkeypatched CONFIG without spawning a fresh process per scenario.

### From v4: Truncation extracted to runtime/truncation.py
- **Source**: v4 `:756-861`. Used by SECURITY.truncate_output AND directly by tool_bash, tool_python_exec, tool_read_file.
- **Adopted (verbatim)**: `runtime/truncation.py`. Lives in `runtime/` to avoid a circular-import path (security uses Truncation, tools use Truncation, security is imported by tools).

### From v4: closure-based python_exec sandbox preamble
- **Source**: v4 `:5293-5407` — `_build_python_preamble` + `_install_sandbox` closure pattern.
- **Adopted (verbatim)**: `tools/python_exec.py:_build_python_preamble`. Wraps `__import__`, `open`, `os.open`, `io.open`, `os.remove/unlink/rmdir`, `os.posix_spawn` at runtime via closures the user code cannot reach.
- **No Runnable analog**: Runnable has no python_exec.
- **v5 enhancement over v4**: extended import allowlist with Python 3.11 transitive imports (`_collections_abc`, `keyword`, `reprlib`, `_pyio`, `_compat_pickle`, `_warnings`).

### From v4: Bedrock-only mode integrated into validate_command + validate_python
- **Source**: v4 `:1869, 1987-2014`.
- **Adopted (verbatim)**: same Layer-0 checks in `security/manager.py`. When `aws_bedrock_only=True`, all `aws CLI` and all `boto3.client('<service>')` (except `'bedrock-runtime'`) are blocked.

---

## Phase 6 — Sectioned prompt + cache (PS Issue #7 STRUCTURAL FIX)

### From Runnable: systemPromptSections.ts registry pattern (PORT_LOG #011)
- **Source**: `gg-claude-code-runnable/src/constants/systemPromptSections.ts`. ~70 lines: `systemPromptSection(name, compute)` registry, `DANGEROUS_uncachedSystemPromptSection(name, compute, _reason)` for volatile sections, `resolveSystemPromptSections()` async resolver, `clearSystemPromptSections()` invoked on `/clear` or `/compact`.
- **Adopted (ADAPT)**: `prompt/sections.py:Section` dataclass + `SECTION_ORDER` list + memoization functions (`get_cached_section`, `set_cached_section`, `clear_section_cache`).
- **Adapted from**: TS Promise-based async compute fns → Python sync static-string returns. v5 sections are .md FILES, not function returns. Justified by: (a) auditing is grep-friendly, (b) no v5 section currently needs runtime computation, (c) per-section token caps are mechanically enforceable on text files.
- **Reserved for Phase 8+**: `cache_break=True` flag on `Section` dataclass — analogue of Runnable's `DANGEROUS_uncachedSystemPromptSection`. Phase 8+ will use this for runtime-computed sections (per-skill auto-trigger, iteration_budget_status).

### From Runnable: prompts.ts content structure (PORT_LOG #012)
- **Source**: `gg-claude-code-runnable/src/constants/prompts.ts` — 914-LOC f-string with embedded section markers.
- **Adopted (ADAPT)**: 19 prompt/*.md files in v5, each replacing one logical section of v4's monolithic SYSTEM_PROMPT. Content is REWRITTEN in a tighter v5 form (45% reduction: 2739 vs ~5000 tokens).
- **Better than Runnable**: v5 file-per-section means each piece of behavioral guidance is a separate, reviewable, token-capped unit. Runnable's f-string is one diff unit; v5's structure means a security-relevant change to "Executing actions" is a `git diff prompt/executing_actions.md`. The PR review surface is 19× smaller per change.
- **Better than v4**: v4 inherited Runnable's f-string approach; v5 fixes the structural failure mode (PS Issue #7 buried matrix) by promoting `tool_classes` to slot 2 and capping every section's size.

### From Runnable: promptCacheBreakDetection.ts (PORT_LOG #013)
- **Source**: `gg-claude-code-runnable/src/services/api/promptCacheBreakDetection.ts`.
- **Adopted (ADAPT)**: `core/cache.py:detect_cache_break + fingerprint_sections + CacheBreakReport + build_cache_blocks`.
- **What we kept**: section-level SHA hashing, before/after comparison, `CacheBreakWarning` log message identifying which section flipped + token delta.
- **What we deferred**: Runnable's full hash-tree (per-tool hashes, global cache strategy, betas list, cacheControlHash). Phase 6 implementation is intentionally smaller — just enough for the Phase 6 multi-block prompt structure. Phase 12+ may extend.
- **Phase 1 pre-history**: ADR-005 (Phase 1 BedrockClient port) explicitly DEFERRED this from Phase 1 because it required multi-block prompts that didn't exist until Phase 6. Phase 6 closes the loop.

### From v4: SYSTEM_PROMPT content (rewritten, not verbatim)
- **Source**: v4 `compact_v4/MAIN/agent/sagemaker_agent.py:8029-8178` SYSTEM_PROMPT f-string.
- **Adopted (REWRITE)**: every behavioral rule from v4's prompt is preserved in v5's 19 sections, but the prose is tighter. v5's 2739 tokens delivers the same coverage as v4's ~5000.
- **Why a rewrite, not verbatim port**: v4's prompt grew by appending. The aggregate became unreviewable. Rewriting in 19 reviewable units with hard caps is the structural fix — copying the v4 text verbatim would defeat the purpose.

---

## Phase 7 — ToolSearchTool deferred loading

### From Runnable: ToolSearchTool.ts core algorithm (PORT_LOG #014)
- **Source**: `gg-claude-code-runnable/src/tools/ToolSearchTool/ToolSearchTool.ts` — 471 LOC of TS implementing 3 query modes (select / +required / keyword), CamelCase + MCP-prefix name parsing, lodash memoize for description caching, async Promise-based search.
- **Adopted (ADAPT)**: `tools/tool_search.py:_tool_search_executor` — sync Python port preserving the 3 query modes + name parsing + `<functions>` wire format. Drops async/Promise compute (v5 descriptions are static module-level strings; no async needed). Drops lodash-es memoize (overkill for static descriptions). Drops feature-gate branches (FORK_SUBAGENT / KAIROS / KAIROS_BRIEF / GrowthBook flags) — Anthropic-internal experiments.
- **Better than Runnable**: ~250 LOC vs Runnable's 471 LOC. Same functionality, less surface area to maintain.
- **What we preserved verbatim (algorithm-level)**:
  - 3 query modes with the exact same parsing rules
  - CamelCase + `mcp__server__action` name splitting for keyword matching
  - `<functions>{"description":..., "name":..., "parameters":...}</functions>` wire format

### From Runnable: prompt.ts isDeferredTool rule (PORT_LOG #015)
- **Source**: `gg-claude-code-runnable/src/tools/ToolSearchTool/prompt.ts:isDeferredTool` (35 LOC of branching logic).
- **Adopted (ADAPT)**: `tools/tool_search.py:is_deferred_tool` — simplified to `should_defer AND NOT always_load AND name != "tool_search"`. Drops feature-gate branches.
- **Adopted (ADAPT)**: `tools/registry.py:apply_tool_search_deferral` — replaces Phase-2 stub with real partition logic.
- **Better than Runnable**: clearer rule (single 1-line decision instead of 5 branches), same behavior for our use case. Phase 11 may add the MCP-tool default-defer branch when MCP tools land in v5.

---

## Phase 8 — QueryEngine + retry + errors + IterationBudget

### From Hermes (via v4): IterationBudget shared counter
- **Source**: `D:/Github/hermes-agent/run_agent.py:170` (Hermes adopted in v4.9.4 at `compact_v4/MAIN/agent/sagemaker_agent.py:8190`).
- **Adopted (PORT)**: `core/budget.py` — verbatim port. Default 600 (v4.10.10 in-place bump from Hermes default 90 because dev work blew through 90 fast).
- **Adaptation**: `consume() → bool` shape kept. Thread-safe via `threading.Lock`. Sub-agents (Phase 9) will inherit the same instance via constructor injection.
- **Better than Hermes**: Phase 11 will surface remaining/used/total in an ipywidgets progress bar (PS Issue #2). Hermes only logs at exhaustion. v4 logs a single line. v5 makes the budget visible while it burns down.

### From Runnable + v4 inline: ErrorClassifier + RetryPolicy extraction
- **Source**: v4 `sagemaker_agent.py` had inline classifier + retry; Phase 1 inlined them inside `runtime/bedrock_client.py` to avoid Phase-1/Phase-8 circular dep.
- **Adopted (PORT)**: `core/errors.py` (`BedrockErrorCategory` + `ErrorClassifier`) + `core/retry.py` (`RetryPolicy`). `runtime/bedrock_client.py` re-imports both names so existing call-sites work unchanged.
- **Lock test**: `test_runtime_bedrock_client_re_exports_match` in test_errors.py and test_retry.py — asserts class identity (`is` check) so any future drift fails CI.
- **Better than v4**: classifier is now testable without boto3, and other modules (QueryEngine) can import it without pulling the Bedrock client. v4 forced you to instantiate a BedrockClient (or monkey-patch boto3) just to test classification.

### From Runnable: QueryEngine.ts main loop, adapted to .ipynb scope
- **Source**: `_archive/compare_code/gg-claude-code-runnable/src/QueryEngine.ts` (1295 LOC).
- **Adopted (ADAPT)**: `core/query_engine.py` — ~400 LOC.
- **Adaptation**:
  - Sync (no Promise / async generator chain). Constraint=`.ipynb` (synchronous tool execute()).
  - Drops Runnable's complex permission-context graph. v5 collapses to `(plan_mode, deny_rules)` per ADR-008.
  - Drops Runnable's compaction state machine — Phase 11 lands compaction in its own module (microcompact / context_collapse / 2-stage smart compaction).
  - Drops Runnable's transcript / canUseTool wrappers / appState updaters — v5 runs in .ipynb without those surfaces.
  - Drops Runnable's structured-output JSON schema / json_schema retry counter — v5 doesn't ship structured-output mode in Phase 8.
- **Better than Runnable**: explicit IN-SCOPE / OUT-OF-SCOPE list in module docstring with each deferral justified. Reviewable.
- **Phase 7 wiring contract** (the critical adoption): per-turn `apply_tool_search_deferral(enabled=True)` + `_discovered_tool_names` set + `<system-reminder>` injection. Bridges Phase 7 (QUERY mechanism) to Phase 8 (API wiring) — without Phase 8 the Phase 7 deferred-loading would be dead code.

### Studied-only from Hermes: skill filtering by available tools
- **Source**: Hermes filters skills by which tools are currently available so the model isn't told about a "verify" skill if `python_exec` is blocked.
- **Decision**: deferred to Phase 10 where the SKILLS subsystem ships. Phase 8 doesn't include skill auto-trigger because skills don't exist yet.

---

## Phase 9 — Sub-agent + Task tool

### From Runnable: forkSubagent budget-sharing pattern (sync adaptation)
- **Source**: `_archive/compare_code/gg-claude-code-runnable/src/tools/AgentTool/forkSubagent.ts` (210 LOC) + `AgentTool.tsx` (1397 LOC).
- **Adopted (ADAPT)**: `subagent/spawn.py` — sync ADAPT.
- **Adaptation**:
  - Sync (no Promise / async generator chain). Constraint=`.ipynb`.
  - Drops experimental `FORK_SUBAGENT` feature gate (Anthropic-internal A/B).
  - Drops cache-prefix-identical message replay (Runnable optimizes for prompt-cache continuity across sub-agent boundaries; v5 keeps the simpler "fresh sub-conversation" model).
  - Drops `<task-notification>` background dispatch model (needs streaming).
  - Drops coordinator-mode mutual exclusion (v5 has no coordinator).
- **Better than Runnable**: explicit IN-SCOPE / OUT-OF-SCOPE list in module docstring; shared-budget invariant locked to object-identity (`is`) test.

### From Hermes (via v4): IterationBudget sharing across parent + sub-agents
- **Source**: Hermes `run_agent.py:170` (originally) → v4.9.4 adopted at `compact_v4/MAIN/agent/sagemaker_agent.py:8190` → v5 Phase 8 lifted it into its own module (`core/budget.py`) → Phase 9 wires it via `spawn_subagent(budget=parent.budget)`.
- **Adopted (PORT for the budget object; ADAPT for the sharing wiring)**: each spawn shares the SAME budget instance (object identity, not deep copy).
- **Better than Hermes/v4**: lock-tested at three levels — class-level (`_new_child_engine` direct), spawn-level (after `spawn_subagent` flow), and dispatch-level (across nested `task` chains).

### From v4: env-details + handoff blocks (verbatim port + parameter extraction)
- **Source**: `_build_subagent_env_details` (sagemaker_agent.py:7695) + `_build_subagent_handoff_block` (line 7771) + `_sanitize_handoff` (line 7763).
- **Adopted**:
  - `subagent/env.py` PORT — 5.0s git timeout, ≤6 lines, fail-quiet probes.
  - `subagent/handoff.py` ADAPT — same 4000/2000/10 caps, same sanitization, but inputs as parameters not globals (Phase 11 callers will wire them).
- **Better than v4**: separated from the monolith → testable in isolation. Sanitization lock test (`test_handoff_sanitizes_boundary_marker`) is structural (counts unsanitized occurrences) not regex.

### Studied-only from Runnable: agent-color-manager + agentDisplay
- Runnable assigns colors to sub-agents for terminal display. v5 .ipynb shows sub-agent output via ipywidgets (Phase 11), not terminal colors. Pattern not adopted.

### Studied-only from Runnable: agentMemory + agentMemorySnapshot
- Runnable persists per-agent memory state across sessions. v5 already has `runtime/session.py` + memory.md from earlier phases; Phase 9 doesn't add agent-specific memory state (deferred).

---

## Phase 10 — Skills + auto-trigger + Hermes filter

### From Hermes: skill-filtering-by-available-tools (PS Issue #1)
- **Source**: Hermes filters skills by tools they require so the model isn't told about a `verify` skill if bash is blocked.
- **Adopted (ADAPT)**: `skills/manager.py:discover_relevant(active_tools=...)` + `QueryEngine(skill_manager=...)` runtime wiring.
- **Adaptation**:
  - Optional `requires_tools` frontmatter field — Hermes typically declares this in code, v5 declares it in skill metadata so authors own the dependency list.
  - Backwards compatible: skills without the field never filtered. The 10 v4 skills don't declare it; they continue to surface as before.
  - Both CSV scalar (`requires_tools: bash, python_exec`) and YAML list dash-form supported (post Codex Phase-10 fix).
- **Better than Hermes**:
  - Backwards-compatible field — v5 didn't have to retrofit any existing skills.
  - Wired into the runtime loop with a Phase-10 BLOCKER lock test (`test_query_engine_appends_relevant_skill_reminder_to_user_turn`) so the filter doesn't silently rot into dead code.

### From v4: SkillManager (verbatim port + parameter extraction)
- **Source**: `compact_v4/MAIN/agent/sagemaker_agent.py:2684` (`SkillManager`).
- **Adopted (PORT)**: `skills/manager.py` — full v4 surface preserved.
- **Adaptation**: workspace + skills_dir + enable_auto_trigger become constructor parameters (constraint=.ipynb for testability). Frontmatter parser extended to handle YAML lists (Codex Phase-10 finding).
- **Better than v4**: testable in isolation; YAML list parsing supports newer skill authors.

### From v4.9.5: self-patching skills (8 safety rails)
- **Source**: v4.9.5 added `propose_patch` + `apply_proposal` with 8 safety rails: opt-in, propose-not-apply, diff preview, snapshot, audit log, time-stamped filename, per-skill `.proposed/`, required reason + full new_content.
- **Adopted (ADAPT)**: same 8 rails; v5 Phase 10 first pass weakened a few; Codex Phase-10 caught the gaps; post-fix all 8 are honored:
  - Rail 1 (opt-in via `CONFIG.enable_skill_patching=False` default) — preserved.
  - Rail 2 (propose-not-apply) — preserved.
  - Rail 3 (diff preview) — Phase 11 UX wires the visual diff; Phase 10 just writes the proposal.
  - Rail 4 (snapshot) — best-effort `.skill_backup_<ts>` sibling when SnapshotManager not wired (Phase 11 UX wires real snapshot).
  - Rail 5 (audit log) — `logging.info` lines on propose + apply.
  - Rail 6 (time-stamped) — preserved + UUID suffix added (Codex Phase-10 fix for collisions).
  - Rail 7 (per-skill `.proposed/`) — preserved.
  - Rail 8 (required reason + full new_content) — preserved.

### Studied-only from Runnable: SkillTool
- Runnable has a `SkillTool` for invoking skills via tool dispatch. v5 ports the shape (subcommand-style executor) but uses v4 SkillManager underneath. Runnable's React/Ink UI is replaced by Phase 11's ipywidgets. Pattern is documented inline in tools/skill.py.

---

## Phases 11-13

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
| 5 | Runnable | bash prompt focus | Drops Runnable's ~300 lines of undercover/gh/USER_TYPE branches; v5 keeps a focused 90-line description. |
| 5 | Runnable | python_exec dedicated tool | Plan-mode users have a sandboxed Python tool. Runnable plan-mode users have nothing. |
| 5 | Runnable | closure sandbox | open/os.open/io.open/os.remove/os.posix_spawn wrapped at runtime. Runnable just documents which tools to avoid. |
| 5 | v4 | security audit boundary | 5-file package vs v4's 1000+ LOC inline. |
| 5 | v4 | Python 3.11 portability | Closure-sandbox allowlist now includes `_collections_abc` etc. — transitive imports needed for `import json` to work on 3.11. |
| 5 | v4 | rebuild_singleton_for_tests | <1s test rebuilds vs v4's fresh-process-per-scenario. |
| 5 | v4 | dynamic SECURITY re-export | `from security import SECURITY` always returns the current singleton via module `__getattr__`. |
| **6** | **v4** | **PS Issue #7 fix (tool_classes promotion)** | **Tool capability matrix promoted to slot 2 — under cognitive load the model attends to the matrix BEFORE the rest of the prompt. Buried-matrix failure mode structurally prevented.** |
| **6** | **v4** | **per-section token caps** | **Each section has a hard cap; CI gate fails on growth. Prevents the v4 aggregate-failure pattern (every addition individually approved, aggregate never reviewed).** |
| **6** | **v4 + Runnable** | **45% prompt reduction** | **2739 tokens vs v4's ~5000 — half the per-turn system-prompt cost without losing behavioural coverage.** |
| **6** | **v4** | **cache-break self-diagnosis** | **`detect_cache_break` logs which section flipped + token delta. v4 cache breaks were silent — operators had to reverse-engineer cost spikes.** |
| **6** | **Runnable** | **file-per-section** | **19 reviewable .md files vs Runnable's 914-LOC f-string. Each PR review surface is 1/19th the size; security-relevant changes touch one file.** |
| **6** | **Runnable** | **deferred cache-break-detection scope** | **Phase 6 cache-break implementation is intentionally smaller than Runnable's full hash-tree. Per-tool hashes / global cache strategy / betas list deferred to Phase 12+ when those concerns arrive — avoids over-engineering.** |
| **7** | **v4** | **deferred-loading exists at all** | **v4 ships every tool's schema every turn — pure overhead. v5 ports Runnable's deferred-loading. Even with 3 tools deferred (Phase 7 initial) we save ~770 tokens/turn. Phase 13 target ≥3000.** |
| **7** | **Runnable** | **focused tool_search.py** | **~250 LOC vs Runnable's 471 LOC. Drops feature-gate branches (FORK_SUBAGENT / KAIROS / GrowthBook), async wrapping, lodash memoize. Same query-parsing algorithm, less surface.** |
| **8** | **Runnable** | **focused QueryEngine** | **~400 LOC vs Runnable's 1295 LOC. Sync (no Promise chain — constraint=.ipynb). Strict IN-SCOPE / OUT-OF-SCOPE list in docstring. Each deferral (compaction, skills, sub-agent) justified inline.** |
| **8** | **v4** | **agent loop is its own module** | **v4's `Agent.run` is ~1500 LOC inline in the 12K-LOC monolith. v5 isolates it in `core/query_engine.py` — reviewable PR diffs, easy to test, easy to swap.** |
| **8** | **Hermes + v4** | **visible IterationBudget data model** | **Phase 11 will wire `consume/remaining/used/total` to an ipywidgets progress bar. Hermes/v4 only log at exhaustion. PS Issue #2 fix is structural, not just a clearer log.** |
| **8** | **Phase 1** | **byte-equivalent extraction with class-identity locks** | **`test_runtime_bedrock_client_re_exports_match` asserts `core.errors.ErrorClassifier is runtime.bedrock_client.ErrorClassifier`. Any future drift fails CI.** |
| **8** | **v4** | **Phase 7 wiring contract end-to-end live** | **Turn 1 `tools=` excludes deferred tools; model calls `tool_search(select:view_image)`; turn 2 `tools=` includes view_image schema. Validated by `test_tool_search_round_trip_promotes_deferred_tool`. v4 has no such mechanism.** |
| **8** | **v4** | **tool exception trapping** | **v4's tool dispatch leaks raised Python exceptions in some paths. v5 traps every exception and returns a tool_result with `is_error=True` so the model can recover.** |
| **8** | **v4** | **plan-mode dispatch gate after deferral** | **Even if a mutating tool is in per-turn `tools=` (because tool_search discovered it), v5 dispatch refuses to execute it in plan mode. v4 only filters at registry time, not dispatch.** |
| **9** | **v4** | **sub-agent dispatch as 4-module surface** | **v4's _run_task_tool is ~600 LOC inline. v5 splits into env / handoff / spawn / task — each ≤200 LOC, independently testable, reviewable.** |
| **9** | **Runnable** | **focused sync forkSubagent** | **~250 LOC vs Runnable's 210+1397 LOC (forkSubagent + AgentTool.tsx). Drops async wiring, experimental fork branch, coordinator mutex, cache-prefix replay. Same shared-budget invariant.** |
| **9** | **Hermes + v4** | **lock-tested IterationBudget identity** | **Three lock-test levels: class-level, spawn-level, nested-dispatch-level. Hermes/v4 share the budget but don't lock the contract with object-identity tests.** |
| **9** | **v4** | **deep-copy parent immutability guard** | **v5 deep-copies parent.messages before spawn and compares structurally on return. Catches in-place mutations that preserve length. v4 has no equivalent defense.** |
| **9** | **v4** | **structural cache-boundary sanitization lock test** | **`test_handoff_sanitizes_boundary_marker` counts unsanitized occurrences, not regex. Catches any regression that reintroduces a leak.** |
| **9** | **v4** | **explicit unknown-subagent_type error contract** | **v4 errors on unknown types. v5 first pass silently fell back; Codex caught it. Post-fix: `tools/task.py` AND `subagent/spawn.py` both reject with explicit error listing valid types.** |
| **10** | **Hermes** | **PS Issue #1: skill filtering by available tools, backwards-compatible** | **Hermes's filter pattern adopted via optional `requires_tools` frontmatter field. Skills without the field (10 v4 skills) never filtered. Hermes has no fallback. v5 also wires the filter into runtime loop (Codex Phase-10 BLOCKER lock).** |
| **10** | **v4** | **YAML list dash-form for `triggers`/`requires_tools`** | **v4 frontmatter parser handles only CSV scalar. v5 Phase 10 fix: YAML list dash-form works too. Skill authors can use whichever style fits their content.** |
| **10** | **v4.9.5** | **UUID-suffixed proposal filenames + audit + backup-on-apply** | **Same-second proposals would collide in v4.9.5. v5 adds 6-char UUID suffix. Apply always writes `.skill_backup_<ts>` sibling for local reversibility even before SnapshotManager is wired.** |
| **10** | **v4** | **SkillManager testable in isolation** | **v4's SkillManager is buried in the 12K-LOC monolith — every test path requires Agent.run integration. v5's `skills/manager.py` is its own module with 21 unit tests + 12 integration tests.** |
| **10** | **Codex review (Phase 10)** | **runtime integration locked by test, not just by docs** | **Codex first pass caught that the Hermes filter was dead code (no runtime wiring). Post-fix: `test_query_engine_appends_relevant_skill_reminder_to_user_turn` is a BLOCKER lock — any future regression that decouples skill_manager from QueryEngine breaks CI.** |
