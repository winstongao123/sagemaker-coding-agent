# PS_V5 — Functional Changes from v4

**Purpose**: This document captures **what v5 changes functionally vs v4.10.10** — not just where modules moved, but what executor behavior changed, what prompt text changed, what defaults changed, and what new constraints were added. Living document, updated each phase.

**Companion docs**:
- `PS_V5_LEARNINGS_FROM_REPOS.md` — what we learned and adopted from Runnable / Hermes / Learning_Factory.
- `V5_RUNNABLE_PORT_LOG.md` — mechanical port-log (Codex-verifiable).
- `V5_DESIGN_DECISIONS.md` — ADRs (architectural rationale).

**Scope rules**:
- Capture every functional delta where v5 BEHAVIOR differs from v4 — even where the v5 code is a verbatim port (because the verbatim port may now interact with new v5 surroundings).
- Skip pure structural changes (file moves, module splits) — those live in V5_PLAN.md and ADRs.
- Each entry MUST cite the v4 source (file:line) and the v5 destination so the diff is auditable.

---

## Phase 0 — Scaffolding (no functional changes)

Phase 0 was scaffolding only — no v4 behavior changed. Skeleton package layout, status docs, smoke tests, `.gitignore`, reference HTMLs copied. v4 still on `master` untouched.

---

## Phase 1 — Bedrock client + Config

Both modules are **verbatim ports** of v4 with three intentional functional improvements:

### 1.1 Lazy CONFIG import in BedrockClient (functional behavior unchanged, dependency cleanup)
- **v4**: `BedrockClient` (`compact_v4/MAIN/agent/sagemaker_agent.py:2378`) imported `CONFIG` at module top, creating an implicit Phase-1/Phase-8 circular dependency once the module split happens.
- **v5**: `runtime/bedrock_client.py` imports CONFIG lazily inside `chat()` to avoid the cycle.
- **Behavior delta**: none for users. Internal refactor only.

### 1.2 Injectable client kwarg (testability)
- **v4**: `BedrockClient.__init__` always called `boto3.client(...)` when `mock_mode=False`. Unit tests had to assign `c.client = fake` after construction, which only worked if boto3 was importable in the test environment.
- **v5**: `BedrockClient.__init__(model_id, region, mock_mode, client=None)` accepts an injected client. Tests now pass a fake client at construction without ever importing boto3.
- **Behavior delta**: production paths unchanged. Test paths no longer require boto3.
- **Driver**: Codex Phase-01 review finding 1 (major).

### 1.3 PS Issue #4 — thinking config sent on EVERY call (locked by test)
- **v4**: thinking config WAS sent every call when `thinking_enabled=True` — but this was implicit. Users complained that thinking blocks only appeared on the first message of a session, leading them to believe the config wasn't being sent.
- **v5**: same code, NOW LOCKED by `test_thinking_config_sent_on_every_call_when_enabled` (3-call assertion). Any future regression where someone adds a "first message only" branch will break the test.
- **Behavior delta**: zero. Test added to prevent future regression.
- **Driver**: PS_actual_use_problems.md Issue #4.

### 1.4 Cache-fallback retry path now tested
- **v4**: `BedrockClient.chat()` had a cache-validation fallback (strip cache_control + retry once) but no test covered it.
- **v5**: same code, NOW LOCKED by `test_cache_validation_error_strips_cache_and_retries_once`. Verifies: 2 invocations, first had cache_control blocks, second flattened to plain string, `prompt_cache_supported=False` after, thinking config preserved on retry.
- **Behavior delta**: zero. Test added to prevent future regression.
- **Driver**: Codex Phase-01 review finding 2 (minor — coverage gap).

### 1.5 Config defaults preserved verbatim
- All 12 v4.10.10 critical defaults preserved (`max_iteration_budget=600`, `max_exec_calls_per_session=200`, `enable_skill_auto_trigger=False`, `enforce_verify_contract=False`, `enable_skill_patching=False`, Sonnet 4.5 default model, etc.). Locked by `test_config_v4_critical_defaults_preserved`.

---

## Phase 2 — Tool Protocol + registry

Replaces v4's monolithic `TOOLS = {...}` 4-tuple dict with a typed `ToolDef` Protocol + `tools/registry.py`. **Five functional improvements** vs v4:

### 2.1 Duplicate tool registration now rejected
- **v4**: `TOOLS = {name: (...)}` is a Python dict; if two skills both registered `verify`, the second silently overrode the first. Real v4 bug.
- **v5**: `register(tool)` raises `ValueError("Tool 'X' already registered")` on duplicate. Caller must call `unregister(name)` first if replacement is intended.
- **Behavior delta**: silent override → loud failure. Locked by `test_register_duplicate_name_raises`.

### 2.2 Plan-mode allowlist now applies to MCP tools too
- **v4**: `PLAN_MODE_ALLOWED_TOOLS` set at `sagemaker_agent.py:6905` filtered tools by name at dispatch time (`:9390`). MCP tools landed in `TOOLS` dict alongside built-ins, so the dispatch-time filter caught them too — but the filter was ad-hoc and easily bypassed by callers reading the TOOLS dict directly.
- **v5**: `assemble_tool_pool(plan_mode=True)` applies the allowlist to BOTH built-ins and MCP tools at registry-assembly time. The model never sees the disallowed tool schema in the initial prompt.
- **Behavior delta**: same final filter, but enforced earlier and more reliably. Locked by `test_plan_mode_filters_mcp_tools_too` and `test_plan_mode_allows_mcp_tool_only_if_name_in_allowlist`.
- **Driver**: Codex Phase-02 review finding 1 (major).

### 2.3 MCP server-prefix deny rules now supported
- **v4**: deny rules were exact-name strings (e.g., `bash`). No way to say "deny all tools from MCP server X" without listing every tool.
- **v5**: `_filter_by_deny_rules` extracts the server segment from `mcp__<server>__<tool>` names and matches both `mcp__server` (blanket-deny) and `mcp__server__*` (wildcard form).
- **Behavior delta**: new capability matching Runnable's `getDenyRuleForTool` semantics. Locked by 3 new tests including a no-partial-match guard (`mcp__git` does NOT match `mcp__github__*`).
- **Driver**: Codex Phase-02 review finding 2 (major).

### 2.4 Cache-stable alphabetical tool ordering
- **v4**: `TOOLS` dict iteration order was insertion-order. Adding a new tool mid-dict shifted later tools' positions in the per-turn `tools` block, busting the prompt cache for every downstream tool on the first turn after the change.
- **v5**: `assemble_tool_pool` sorts built-ins alphabetically and MCP tools alphabetically as a contiguous suffix. New tools land in the alphabetical position with predictable cache impact.
- **Behavior delta**: prompt cache no longer bursts on tool list edits. Locked by `test_assemble_tool_pool_sorts_alphabetically_for_cache_stability`.
- **Source**: Runnable `assembleToolPool` cache invariant (see PORT_LOG #002).

### 2.5 Tool defaults are fail-closed
- **v4**: tool 4-tuple had `requires_approval` as the 2nd element; `is_read_only` was nowhere — callers heuristically guessed by tool name (`read_file` → read-only, etc.).
- **v5**: `ToolRecord` defaults: `is_read_only=False`, `is_destructive=False`, `is_concurrency_safe=False`, `enabled=True`. Tool author who omits any flag gets the safer "assume writes / not concurrency safe" default.
- **Behavior delta**: read-only classification is now explicit per tool, not heuristic. Locked by `test_build_tool_defaults_match_runnable_tool_defaults`.

### 2.6 Phase-7 deferred-loading hook stub
- **v4**: tools.ts deferred-loading pattern doesn't exist. All tool schemas ship in the initial prompt every turn.
- **v5**: `apply_tool_search_deferral(tools, enabled=False)` is published as a stub now. When `enabled=False` (default Phase 3-6), returns `(tools, None)` unchanged — same as v4. Phase 7 fills in the real logic.
- **Behavior delta**: zero in Phases 2-6. Phase 7 saves ≥3000 tokens/turn.

---

## Phase 3 — Core read-only tools (read_file, grep, glob, list_dir)

Four read-only tools land per ADR-001 (file-per-tool) + ADR-009 (REUSE v4 executor + ADAPT Runnable prompt). Multiple functional improvements vs v4:

### 3.1 grep tool — truthfulness fix on backend claim
- **v4 prompt**: v4 didn't make a Runnable-style claim about ripgrep (its description says "regex search").
- **Runnable prompt**: claims "built on ripgrep" (true for Runnable's TS version which embeds ripgrep in the bun binary).
- **v5 prompt**: says "Regex search across files. ... Pattern syntax: Python `re` semantics — literal braces don't need escaping; backreferences and named groups are supported."
- **Why this is "better than Runnable"**: v5's prompt is *honest* about the backend. Runnable's prompt would mislead the model in v5 because v5 doesn't have ripgrep. Pattern syntax differs (ripgrep PCRE2 vs Python re) and the model would write the wrong escapes if it believed the prompt. PS Issue #6 (wiring-bug pattern) prevention.
- **Behavior delta vs v4**: zero (same Python `re` backend); prompt text now anti-pattern proofed.

### 3.2 read_file — minimal v4 port without Phase 8 globals
- **v4**: `tool_read_file` depended on `FILE_CACHE` (LRU), `_FILES_READ`/`_FILE_READ_TIMES` (mtime tracking for edit_file's stale-detection), `_FILE_PARTIAL_READS` (large-file partial-read tracking), `FILE_UNCHANGED_STUB` (skip re-read when mtime unchanged).
- **v5 Phase 3**: minimal port keeps the security check, large-file guard (>500 lines → first 50 + last 30), .ipynb cell parsing. The Phase-8 globals are NOT introduced yet — they'll come back when `core/query_engine.py` lands (Phase 8) and brings the supporting state. Rationale: Phase 3 should not depend on Phase 8 modules.
- **Behavior delta**: when reading the same file twice in a session, Phase 3 v5 always re-reads (no FILE_UNCHANGED_STUB). v4 returns the stub. **Token cost note**: this is a temporary regression for Phase 3-7 only; Phase 8 restores the cache + stub. Reconciliation tracked in Phase 8 ADR.

### 3.3 list_dir — kept dedicated tool against Runnable's "use bash ls" advice
- **Runnable prompt for read_file**: "This tool can only read files, not directories. To read a directory, use an `ls` command via the Bash tool."
- **v5 design**: keeps a dedicated `list_dir` tool. Reasons:
  1. v4 has it.
  2. v5 plan-mode forbids bash; without `list_dir`, plan-mode users can't inspect directories at all.
  3. The 4 read-only tools (read_file, grep, glob, list_dir) map cleanly to the v4.10.10 user mental model and the PLAN_MODE_ALLOWED_TOOLS set.
- **Better than Runnable**: v5 plan-mode users can fully navigate the workspace without bash. Runnable plan-mode users cannot.

### 3.4 path_validation stub — simpler than v4 SecurityManager
- **v4**: full `SecurityManager` class (~600 LOC) handles path validation + 134-case destructive-command pattern matching + DANGEROUS_PYTHON regex set + HIGH_RISK_TOOLS approval machinery + audit logging + output truncation.
- **v5 Phase 3**: ~80 LOC `tools/_path_validation.py` covers ONLY workspace boundary check + symlink escape detection (using `os.path.realpath` + `os.path.commonpath`).
- **Phase 5 contract**: this stub is replaced by the full v4 `SecurityManager` port. The `validate_path(path) -> (ok, msg)` signature is intentionally identical to v4's so swap is one import-line change per file.
- **Behavior delta**: zero for read-only tools (they only need path validation; SecurityManager's command-pattern stuff is for bash + python_exec). Phase 5 ADR will assert no behavior change after the swap.

### 3.5 Cache-stable alphabetical tool ordering — first time exercised
- **v4**: 4 read-only tools were inserted into `TOOLS = {}` dict in declaration order (read_file, write_file, edit_file, glob, grep, list_dir).
- **v5**: alphabetical = `glob`, `grep`, `list_dir`, `read_file`. Locked by `test_assemble_tool_pool_alphabetical_for_phase3_tools`.
- **Behavior delta**: tool ordering in the per-turn prompt changes vs v4. This is a *cache improvement* — adding a future `notebook_edit` tool will land in alphabetical position and only re-cache itself + alphabetically-later tools, not the entire tool block. v4's ordering would have busted the cache for every tool added later.

### 3.6 Tool concurrency-safe flags now explicit
- **v4**: tools didn't expose an `is_concurrency_safe` flag; Phase 8 sub-agent dispatch heuristically guessed.
- **v5**: all 4 read-only tools declare `is_concurrency_safe=True` (Runnable parity). When Phase 9's Task tool dispatches multiple read-only tool calls in parallel, the registry will allow batching.
- **Behavior delta**: zero today (Phase 8/9 not landed). Lock test ensures no future regression where someone forgets to set the flag.

---

## Phase 4 — Core mutating tools + diff_widget

Four mutating tools (`write_file`, `edit_file`, `notebook_edit`, `view_image`) + `ui/diff_widget.py` land per ADR-010. Multiple functional improvements vs v4:

### 4.1 Approval prompt now shows colored diff inline + click-to-expand
- **v4**: approval prompt showed a text summary like `Edited foo.py (line 42)\n  -3 lines / +5 lines\n  Old: 'def...'\n  New: 'def...'`. Users approved without seeing the actual change content; misplaced edits were caught only after the fact.
- **v5**: `ui/diff_widget.py` emits an HTML colored diff with file path header, `+` green / `-` red / context gray rows, line numbers in both BEFORE and AFTER coordinate systems, ±3 lines context by default, plus a `<details>`-wrapped full-file view for click-to-expand. Phase 11 wires this into the ipywidgets approval prompt.
- **Behavior delta**: misplaced edits are catchable at approval time. **Better than v4 AND Runnable**: Runnable's UI.tsx Ink renderer was the inspiration; v5 brings the same UX to ipynb where v4 had only a text summary. (Runnable is not "better" here — they had this; v4 didn't; v5 catches up + integrates with .ipynb.)

### 4.2 Phase-3 + Phase-4 deferred features documented inline (no silent regressions)
- **v4**: write_file invoked `SECURITY.scan_secrets`, `SNAPSHOTS.save`, `_auto_lint_python`, `_maybe_auto_checkpoint` inline.
- **v5 Phase 4**: writes the file but does NOT run those features (they belong to Phase 5 security + Phase 8 query_engine session machinery).
- **Behavior delta**: temporary regression vs v4.10.10 — Phase 4 doesn't snapshot before edit, doesn't lint Python, doesn't auto-commit. Each is documented inline (`# Phase-N deferred: ...`) so reviewers and future-me know the gap. The Phase 5 + Phase 8 ADRs explicitly reconcile.
- **Why this is a defensible regression**: v5 has no QueryEngine yet (Phase 8). The deferred features depend on session state (`_RECENT_DIFFS` queue, `auto_commit_every` counter) that Phase 8 builds. Adding them in Phase 4 would mean re-implementing Phase-8 state machinery twice. Better to land them once when query_engine arrives.

### 4.3 edit_file now rejects edits to externally-modified files (stale-check, was implicit in v4)
- **v4**: `_check_file_staleness` was called inside `tool_edit_file` but the threshold (`abs(mtime_diff) < 0.5s`) was magic-numbered and the failure path returned an error string with no recovery hint.
- **v5**: `tools/_file_read_tracking.is_stale(path) -> (bool, msg)` exposes the same logic with explicit hint: `"File modified externally since last read (read mtime X vs now Y). Re-read with read_file to refresh, then retry the edit."`
- **Behavior delta**: same threshold + check, better error message. Locked by `test_edit_file_stale_file_rejected`.

### 4.4 notebook_edit's atomic write contract is now testable
- **v4**: notebook_edit wrote via `tempfile.mkstemp` + `os.replace`; if the rename failed, the live notebook was preserved. Not tested because v4's monolith made the failure path hard to mock.
- **v5**: same atomic-write logic, now in a small `_atomic_write_json` helper that's directly testable. `test_notebook_edit_atomic_write_preserves_on_failure` mocks `os.replace` to raise OSError and asserts the original notebook is unchanged.
- **Behavior delta**: zero. New test prevents future regression.

### 4.5 view_image is read-only with no Runnable analog
- **Runnable** integrates image reading into FileReadTool — model just calls `read_file("img.png")` and the tool detects the format and returns base64 inline.
- **v4 + v5** keep a dedicated `view_image` tool. Reasons: (a) v4 has it, (b) the SageMaker chat.ipynb workflow surfaces image loading as an explicit user-driven action, (c) the dedicated tool makes audit log entries clearer (auditing `view_image(file_path=...)` is more meaningful than `read_file(file_path=...)` for binary content).
- **Better than Runnable**: clearer audit trail. Not "better" technically — it's a stylistic v4-parity choice that makes audits easier.

### 4.6 HTML escaping in diff_widget — security control
- **v4**: no inline diff in approval prompt → no HTML rendering → no XSS surface.
- **v5**: diff_widget renders HTML for ipywidgets. **Untrusted content** (the model's `old_string`/`new_string`) is HTML-escaped via `html.escape` so a model can't inject `<script>alert(1)</script>` into the approval prompt. Locked by `test_inline_diff_html_escapes_special_chars`.
- **Behavior delta**: new attack surface introduced + new defense. Net: defended.

### 4.7 Mutating tools have explicit `is_destructive=True` + `is_concurrency_safe=False`
- **v4**: tools didn't expose these flags; Phase 8 sub-agent dispatch heuristically guessed.
- **v5**: write_file / edit_file / notebook_edit declare `is_destructive=True` (surfaces in approval prompts), `is_concurrency_safe=False` (Phase 9 Task tool will not parallel-batch them). view_image declares `is_read_only=True` + `is_concurrency_safe=True`.
- **Behavior delta**: zero today (Phase 8/9 not landed). Lock test ensures no future regression.

---

## Phases 5-13

(Future — entries land per phase.)
