# V5 Runnable Port Log (append-only)

Format: one row per Runnable pattern adopted. Never delete rows. Mark superseded as STATUS=SUPERSEDED-BY-#&lt;id&gt;.

| ID | Date | Phase | Runnable source (file:section) | v5 target | Adoption verdict | Codex error verdict | Codex fidelity verdict | Commit sha | Notes |
|----|------|-------|--------------------------------|-----------|------------------|---------------------|------------------------|------------|-------|
| 001 | 2026-04-30 | 02 | src/Tool.ts:`Tool` interface + `buildTool` defaults | compact_v5/MAIN/agent/tools/registry.py:`ToolDef` Protocol + `build_tool()` | ADAPT | PASS | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Drops React/Ink render methods; constraint=.ipynb. ADR-007. Codex APPROVE. |
| 002 | 2026-04-30 | 02 | src/tools.ts:`getAllBaseTools` + `getTools` + `filterToolsByDenyRules` + `assembleToolPool` | compact_v5/MAIN/agent/tools/registry.py:`get_tools()` + `assemble_tool_pool()` + `apply_tool_search_deferral()` stub | ADAPT | PASS (post-fix) | FAITHFUL-WITH-JUSTIFIED-ADAPTATION (post-fix) | 6c7468f | Replaces v4 monolithic TOOLS dict + PLAN_MODE_ALLOWED_TOOLS set. Simpler permission-context tuple (plan_mode + deny_rules) instead of Runnable's DeepImmutable PermissionContext. constraint=.ipynb. ADR-008. **Initial Codex verdict was DRIFTED on plan-mode-MCP-visibility + missing MCP server-prefix deny support; both fixed in same Phase 02 commit (lock tests added). Final verdict FAITHFUL-WITH-JUSTIFIED-ADAPTATION.** |
| 003 | 2026-04-30 | 03 | src/tools/FileReadTool/prompt.ts (DESCRIPTION + renderPromptTemplate) | compact_v5/MAIN/agent/tools/read_file.py:_DESCRIPTION (executor body is v4 port from sagemaker_agent.py:4258) | ADAPT | PASS (post-fix) | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Tool naming `Read` → `read_file` (v4 parity). Drops Ink/JSX/PDF references; redirects "use ls via Bash" → "use list_dir". constraint=.ipynb. ADR-009. Codex Phase-03 finding 2 (int-coercion crash on bad model input) fixed in same commit. |
| 004 | 2026-04-30 | 03 | src/tools/GrepTool/prompt.ts (getDescription) | compact_v5/MAIN/agent/tools/grep.py:_DESCRIPTION (executor body is v4 port from sagemaker_agent.py:4897) | ADAPT | PASS (post-fix) | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | **Truthfulness correction**: Runnable says "built on ripgrep"; v5 (and v4) use Python `re`. v5 prompt says "regex search across files" — PS Issue #6 (wiring-bug pattern) prevention. **Dropped Runnable-only parameters: `type` (file-type ripgrep flag), `output_mode` (content/files/count modes), `multiline` (cross-line patterns). The reused v4 executor doesn't implement them; promising them in the prompt would be a wiring bug.** constraint=Bedrock. ADR-009. Codex Phase-03: AXIS A APPROVE_WITH_FIXES, fixes landed in same commit; AXIS B FAITHFUL-WITH-JUSTIFIED-ADAPTATION. |
| 005 | 2026-04-30 | 03 | src/tools/GlobTool/prompt.ts (DESCRIPTION) | compact_v5/MAIN/agent/tools/glob.py:_DESCRIPTION (executor body is v4 port from sagemaker_agent.py:4846) | ADAPT | PASS (post-fix) | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | (pending) | Adds v4-specific `allowed_paths` fallback note (when no explicit path AND no matches in workspace, also search allowed_paths). Drops Agent tool reference. constraint=Bedrock. ADR-009. Allowed-paths fallback locked by `test_glob_allowed_paths_fallback`. |

**list_dir (Phase 03)** has no Runnable analog — Runnable tells the model to use `ls` via Bash. v5 keeps the dedicated tool because plan mode forbids bash, so list_dir is essential for read-only inspection. Pure v4 reuse — no PORT_LOG row added; documented inline in tools/list_dir.py and ADR-009.

Phase 1 had no Runnable rows (pure v4 reuse — see ADR-005 / ADR-006). First Runnable adoption rows are Phase 02 above.

Verdict legend:
- Adoption: PORT (1:1) | ADAPT (semantic match, mechanism differs) | REPLACE (v4-native chosen) | DEFER
- Codex error: PASS | CHANGES_REQUESTED | BLOCKER
- Codex fidelity: FAITHFUL | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | DRIFTED

Enforcement note: every PORT_LOG row MUST reference an `ADR-NNN` in V5_DESIGN_DECISIONS.md (per the Addition Gate). Rows without an ADR reference are rejected by the pre-tag lint check (`tests/lint_phase_id.py`).
