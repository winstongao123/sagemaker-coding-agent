# Plan: v5 — SageMaker-native Re-implementation of Runnable Claude Code

**Status**: Draft v1, pending iterative Codex plan-review (target: up to 10 rounds, until both Codex and the planning agent declare 100% confidence).

---

## Context

### Why this is being built

v4.10.10 (current production) shipped successfully but a real session log revealed a **prompt-engineering failure**: the tool-availability matrix added in round 2 was buried mid-list in a 5000+ token system prompt. Under cognitive load (40-call exec limit hit), the LLM under-attended to mid-list bullets and incorrectly concluded "all tools blocked", refused to keep working, asked the user to restart the kernel.

The 5-investigator deep dive (Team A1 prompt-engineering, A2 tool-design, B1 session forensics, B2 Hermes/Runnable comparative, Codex deep architectural) identified the root cause as **aggregate prompt growth from multi-source integration** (Hermes patterns + Runnable patterns + Learning_Factory patterns + v4-original additions = ~5000+ static tokens). Each individual integration was reviewed; the aggregate failed.

Round 3 fixes (8 in-place changes) addressed the immediate failure but **could not address the structural cause** without an architectural refactor. Specifically: v4's monolithic 11K-line `sagemaker_agent.py` cannot adopt Runnable's deferred-tool-schema pattern (saves ~5500 tokens/turn) without significant restructuring.

### What v5 is

**v5 = SageMaker-native Python re-implementation of Runnable Claude Code, adopting Runnable as the primary textbook, with Hermes and Learning_Factory as support references.**

- Runnable Claude Code (TypeScript at `D:/Github/sagemaker-coding-agent/_archive/compare_code/gg-claude-code-runnable/`) is the primary architectural source.
- Hermes (`D:/Github/hermes-agent/`) provides agent-loop patterns (IterationBudget, skill filtering by available tools, graceful failure).
- Learning_Factory (`D:/Github/Learning_Factory/`) provides build-process infrastructure (STATE.md persistence, shadow-git checkpoints, design-log doctrine).

**Source-citation rule**: every non-trivial architectural decision must cite a primary source. Runnable is the default. Hermes / Learning_Factory / v4 reuse is allowed only with (a) explicit rationale and (b) a Runnable-non-applicability note in the ADR.

### What v5 is NOT

- NOT a from-scratch invention — every non-trivial architectural decision must cite a primary source (Runnable by default; Hermes/Learning_Factory/v4 reuse allowed only with explicit rationale and Runnable-non-applicability note in ADR).
- NOT a v4 replacement at ship time — v4 stays on `main` untouched throughout v5 build.
- NOT a refactor — it's a sibling implementation with a clean port map.

### Hard constraints (preserved from v4)

- Bedrock-only (no Anthropic API; uses boto3 `bedrock-runtime`).
- No GitHub network at runtime (local git only inside SageMaker).
- `python_exec` is the canonical Python execution tool (NOT bash python).
- Ships as flat zip — `chat.ipynb` runs without `pip install` of a v5 package.
- All 10 v4 production skills (`batch`, `clara`, `design`, `html`, `reflexion`, `report`, `review`, `security-review`, `simplify`, `verify`) preserved byte-for-byte.
- All v4 destructive-command coverage (`SecurityManager`, `DANGEROUS_PATTERNS`, `DANGEROUS_PYTHON`, `HIGH_RISK_TOOLS`) preserved verbatim.
- `verify_ship_zip.py` ship-gate verifier preserved.

### Success metric

v5 ships when:
1. Functional parity with v4.10.10 (same skills work, same security holds, same notebook UX).
2. Static system prompt **≤ 2500 tokens** (vs v4's ~5000) measured by `prompt/sections.py::estimate_tokens()`.
3. Per-turn token overhead **≥ 3000 tokens lower** than v4 due to deferred tool schemas (`tool_search.py`).
4. All Runnable patterns adopted carry a Codex AXIS-B verdict of FAITHFUL or FAITHFUL-WITH-JUSTIFIED-ADAPTATION (no DRIFTED).
5. `pytest -q` green for all phases.

If any of these slip, v5 does NOT ship — v4.10.10 remains production until they do.

---

## Recommended approach

### v5 folder layout (final)

```
compact_v5/
├── CHANGELOG.md
├── _rebuild_zip.py                  # adapted from v4 — flattens nested source to ship-zip root
├── verify_ship_zip.py               # REUSED verbatim from v4
├── _status/                         # tracking docs (NEW; see §Tracking infrastructure)
│   ├── V5_BUILD_STATUS.md
│   ├── V5_RUNNABLE_PORT_LOG.md
│   ├── V5_DESIGN_DECISIONS.md
│   ├── CODEX_REVIEW_TEMPLATE.md
│   ├── RESUME.md
│   └── codex_reviews/
│       ├── phase-0.md
│       └── ...
├── docs/
│   ├── V5_ARCHITECTURE.md
│   ├── PORT_MAP.md
│   └── PROMPT_LAYERING.md
└── MAIN/
    ├── agent/
    │   ├── chat.ipynb               # ports v4's notebook UX, calls v5 agent
    │   ├── chat.md
    │   ├── memory.md
    │   ├── AGENT_STATUS.md
    │   ├── __init__.py
    │   ├── entry.py                 # cell-0 import target
    │   ├── agent.py                 # public Agent class only (~600 LOC)
    │   ├── core/
    │   │   ├── query_engine.py      # main loop (Runnable QueryEngine.ts)
    │   │   ├── tool_dispatch.py
    │   │   ├── retry.py             # ports withRetry.ts
    │   │   ├── errors.py            # ports services/api/errors.ts
    │   │   ├── context_window.py    # microcompact + context_collapse (REUSE v4)
    │   │   ├── cache.py             # cache_control block placement
    │   │   └── budget.py            # IterationBudget (Hermes), repetition guard
    │   ├── prompt/
    │   │   ├── __init__.py          # build_system_prompt(ctx) -> List[Block]
    │   │   ├── sections.py          # systemPromptSection() registry + memo
    │   │   ├── identity.md
    │   │   ├── tool_classes.md      # PROMOTED top-level (fixes v4.10.10 failure)
    │   │   ├── tool_efficiency.md
    │   │   ├── doing_tasks.md
    │   │   ├── critique_handling.md
    │   │   ├── answer_preference.md
    │   │   ├── data_validation.md
    │   │   ├── executing_actions.md
    │   │   ├── output_style.md
    │   │   ├── subagent_coord.md
    │   │   ├── verification_contract.md
    │   │   ├── memory_protocol.md
    │   │   └── _CACHE_BOUNDARY.md   # marker file (not string-split)
    │   ├── tools/
    │   │   ├── __init__.py
    │   │   ├── registry.py          # get_tools(ctx) + apply_tool_search_deferral()
    │   │   ├── tool_search.py       # ports ToolSearchTool (the key win)
    │   │   ├── shared/
    │   │   ├── read_file.py         # one tool per file
    │   │   ├── write_file.py
    │   │   ├── edit_file.py
    │   │   ├── glob.py
    │   │   ├── grep.py
    │   │   ├── list_dir.py
    │   │   ├── bash.py
    │   │   ├── python_exec.py
    │   │   ├── notebook_edit.py
    │   │   ├── view_image.py
    │   │   ├── web_fetch.py
    │   │   ├── ask_user.py
    │   │   ├── task.py              # sub-agent
    │   │   ├── skill.py
    │   │   ├── skill_propose_patch.py
    │   │   ├── todo_write.py
    │   │   ├── todo_read.py
    │   │   ├── semantic_search.py
    │   │   ├── create_word.py
    │   │   ├── create_excel.py
    │   │   ├── create_pdf.py
    │   │   ├── create_chart.py
    │   │   ├── create_markdown.py
    │   │   └── create_notebook.py
    │   ├── security/                # REUSED verbatim from v4
    │   │   ├── manager.py
    │   │   ├── dangerous_patterns.py
    │   │   ├── dangerous_python.py
    │   │   └── high_risk.py
    │   ├── runtime/
    │   │   ├── bedrock_client.py
    │   │   ├── session.py
    │   │   ├── audit.py
    │   │   ├── snapshot.py
    │   │   ├── file_cache.py
    │   │   └── config.py
    │   ├── subagent/
    │   │   ├── spawn.py
    │   │   ├── handoff.py
    │   │   ├── env.py
    │   │   └── memory_extract.py
    │   ├── skills/                  # 10 v4 skills ported byte-for-byte
    │   │   ├── manager.py
    │   │   ├── batch/
    │   │   ├── clara/
    │   │   ├── design/
    │   │   ├── html/
    │   │   ├── reflexion/
    │   │   ├── report/
    │   │   ├── review/
    │   │   ├── security-review/
    │   │   ├── simplify/
    │   │   └── verify/
    │   ├── ui/
    │   │   ├── chat_ui.py
    │   │   ├── html_escape.py
    │   │   ├── widgets.py
    │   │   └── diff_widget.py     # Phase 4: colored diff in approval prompt (Runnable EditTool/UI.tsx pattern)
    │   ├── mcp/
    │   │   ├── stdio_client.py
    │   │   ├── http_client.py
    │   │   └── manager.py
    │   └── tests/
    │       ├── conftest.py
    │       ├── unit/
    │       ├── tools/
    │       ├── integration/
    │       └── parity/              # v4-vs-v5 parity tests at Phase 11
    └── changelogs/
```

### Port map (Runnable → v5) — final decisions

| Runnable source | v5 target | Decision | Rationale |
|---|---|---|---|
| `tools.ts` | `tools/registry.py` | **PORT** | Replaces v4 monolithic TOOLS dict; supports feature gates + plan-mode subset |
| `tools/<Name>/` (dir-per-tool) | `tools/<name>.py` (file-per-tool) | **ADAPT** | Python doesn't need `.tsx` UI files; flat-zip ship surface preserved |
| `tools/ToolSearchTool/` | `tools/tool_search.py` + `registry.py::apply_tool_search_deferral()` | **PORT** | Highest-leverage import: defers schema for low-frequency tools, saves ~3000 tokens/turn |
| `constants/systemPromptSections.ts` | `prompt/sections.py` | **PORT** | Section registry + memoization + cache-boundary enforcement |
| `constants/prompts.ts` (914 LOC f-string) | 13 × `prompt/*.md` files + `prompt/__init__.py::build_system_prompt()` | **ADAPT** | One section per file → unreviewable monolith → reviewable units |
| `services/api/claude.ts` | `runtime/bedrock_client.py` + `core/cache.py` | **REPLACE** | v4's BedrockClient is already Bedrock-native; steal only cache-block placement |
| `services/api/errors.ts` (1207 LOC) | `core/errors.py` | **ADAPT** | Port LLM-readable error message generators AND error-taxonomy + retryability classification semantics for Bedrock-equivalent failures; only OAuth/subscriber paths are excluded |
| `services/api/withRetry.ts` (822 LOC) | `core/retry.py` | **ADAPT** | Merge into v4's RetryHandler; add jittered exponential backoff + retry-after support |
| `QueryEngine.ts` (1295 LOC) | `core/query_engine.py` | **PORT** | Extract Agent.run from v4 monolith into dedicated loop |
| `tools/AgentTool/` | `subagent/spawn.py` + `tools/task.py` | **ADAPT** | Port forkSubagent budget-sharing; keep v4's SageMaker-specific handoff/env blocks |
| `tools/EditTool/UI.tsx`, `WriteTool/UI.tsx`, `NotebookEditTool/UI.tsx` (diff preview) | `ui/diff_widget.py` + integration into approval prompt | **ADAPT** | TS/React Ink diff renderer → Python ipywidgets HTML diff. Same UX semantics: colored diff (`+` green, `-` red) shown inline in approval prompt for write_file/edit_file/notebook_edit BEFORE user clicks Approve. Catches misplaced edits before they land. |
| `services/api/promptCacheBreakDetection.ts` | `core/cache.py::detect_cache_break()` | **PORT** | Identify which section flipped → log CacheBreakWarning |
| `commands/` slash commands | — | **DEFER** | v4 skills + auto-trigger cover this surface (mapped in PORT_MAP.md) |
| `services/oauth/`, `policyLimits/`, `teamMemorySync/` | — | **DEFER** | Anthropic-direct only; Bedrock has no equivalent (no v4 coverage required) |
| `hooks/`, `voice/`, `vim/`, `keybindings/` | — | **DEFER** | UI-layer features; not applicable to ipynb chat (no v4 coverage required) |

**DEFER mapping rule**: every DEFER row above MUST have a corresponding entry in `compact_v5/docs/PORT_MAP.md` with this exact structured format:

```
- Pattern: <Runnable source path:section>
- Reason code: NO_EQUIVALENT | COVERED_BY_V4 | DEFER_TO_V5_1
- v4 covering behavior (if COVERED_BY_V4): <file:line>
- Reviewer sign-off: <user-or-Codex YYYY-MM-DD>
```

Prevents silent capability gaps and forces explicit traceability.

### v4 components reused verbatim (~6500 of 12088 LOC)

- `SecurityManager` + `DANGEROUS_PATTERNS` + `DANGEROUS_PYTHON` + `HIGH_RISK_TOOLS` (battle-tested, 134-case coverage)
- All 10 production skills (port directories byte-for-byte)
- `SkillManager` + skill discovery
- `SnapshotManager` (shadow-git checkpoints)
- `AuditLogger` + `AuditEntry`
- `Config` + JSONC loader
- `SessionManager`, `FileCache`, `SemanticSearch`
- `MCP{Stdio,Http}Client` + `McpManager`
- `verify_ship_zip.py`
- `_rebuild_zip.py` (adapted to walk nested tree, flatten on output)
- `microcompact()` and `context_collapse()` (already strong; steal Runnable's cache-keyed compact result for a small win)
- `build_todo_restoration_message`, `build_file_restoration_message`
- `Truncation` output capper

---

### Phase breakdown (final, 14 checkpoints: phases 0–13 plus hard gate 8.5)

| # | Phase | Goal | Deliverable | Runnable source | v4 inherited | Acceptance | Effort |
|---|---|---|---|---|---|---|---|
| 0 | Scaffold | Create `compact_v5/` skeleton, `_status/` docs, branch `v5-build` | folder tree + 5 status docs + `tests/test_smoke.py` | n/a | layout from `compact_v4/` | smoke test passes (imports only); status docs exist | S |
| 1 | Bedrock client + Config | Port v4's BedrockClient + Config into `runtime/` | `runtime/bedrock_client.py`, `runtime/config.py`, `tests/unit/test_bedrock.py` | `services/api/claude.ts` (cache placement only) | v4 BedrockClient | mock-Bedrock test passes | S |
| 2 | Tool Protocol + registry | Define `ToolDef` Protocol + `registry.py` + tool-search-deferral hook | `tools/__init__.py`, `tools/registry.py`, `tests/unit/test_registry.py` | `tools.ts`, `Tool.ts` | v4 PLAN_MODE_ALLOWED set | registry lists tools w/o loading schemas; deferred tools annotated | M |
| 3 | Core read-only tools | Implement read_file, grep, glob, list_dir | `tools/read_file.py`, `grep.py`, `glob.py`, `list_dir.py`, `tests/tools/test_*.py` | `tools/FileReadTool/`, `GrepTool/`, `GlobTool/` | v4 implementations | each tool unit-tested | M |
| 4 | Core mutating tools + **diff preview UI (inline + expandable)** | Implement write_file, edit_file, notebook_edit, view_image; render colored diff in approval prompt before apply (Runnable EditTool/UI.tsx pattern). UX: inline colored chunks (±3 lines context, line numbers, file path header) + click `Expand full file` HTML `<details>` for whole-file view. | `tools/write_file.py`, `edit_file.py`, `notebook_edit.py`, `view_image.py`, `ui/diff_widget.py` | `tools/WriteTool/UI.tsx`, `EditTool/UI.tsx`, `NotebookEditTool/UI.tsx` | v4 implementations + v4 approval prompt machinery | each tool unit-tested; security gate fires on system paths; **edit_file, write_file, AND notebook_edit approval prompts each show colored before/after diff inline (red removed, green added, gray context) with file path header + line numbers + ±3 lines context + click-to-expand-full-file using `ui/diff_widget.py` BEFORE user clicks Approve — no exceptions** | M |
| 5 | Bash + python_exec + security | Wire `SecurityManager` into bash + python_exec dispatch | `tools/bash.py`, `tools/python_exec.py`, `security/` (port verbatim from v4), `tests/unit/test_security.py` | `tools/BashTool/` (semantics) | v4 SecurityManager (verbatim) | 134-case destructive coverage from v4 still passes | M |
| 6 | Sectioned prompt + cache | Port `prompt/sections.py` + 13 `*.md` files + cache-boundary marker | `prompt/__init__.py`, `prompt/sections.py`, 13 prompt MD files, `core/cache.py`, `tests/unit/test_prompt_assembly.py` | `constants/prompts.ts`, `systemPromptSections.ts`, `promptCacheBreakDetection.ts` | v4 system prompt content (split into files) | static prompt ≤ 2500 tokens; cache-boundary test passes | L |
| 7 | ToolSearchTool deferred loading | Port deferred-tool pattern; mark low-frequency tools as deferred | `tools/tool_search.py`, `registry.py::apply_tool_search_deferral()`, `tests/unit/test_tool_search.py` | `tools/ToolSearchTool/` | n/a | per-turn schema overhead drops ≥3000 tokens vs Phase 6 baseline | M |
| 8 | QueryEngine + retry + errors | Wire main loop, retry, error message generators | `core/query_engine.py`, `core/retry.py`, `core/errors.py`, `tests/integration/test_query_engine.py` | `QueryEngine.ts`, `withRetry.ts`, `services/api/errors.ts` | v4 Agent.run (extracted) | end-to-end mock test: tool_use → tool runs → final answer | L |
| 8.5 | **Thin-slice parity gate** (canonical id `P08_5`) | Run 10 critical v4-vs-v5 scenarios (tool block recovery, security deny, retry, prompt assembly, resume) BEFORE skills/sub-agent expansion to catch architectural drift early | `tests/parity/test_thin_slice.py` | v4 critical scenarios | n/a | 10/10 must pass — **HARD BLOCKS phase 9 from starting** | S |
| 9 | Sub-agent + Task tool | Port forkSubagent budget sharing; reuse v4 handoff blocks | `subagent/spawn.py`, `subagent/handoff.py`, `subagent/env.py`, `tools/task.py`, `tests/integration/test_subagent.py` | `tools/AgentTool/`, `forkSubagent.ts` | v4 _build_subagent_handoff_block, _build_subagent_env_details | parent context unchanged; child shares IterationBudget | L |
| 10 | Skills + auto-trigger + skill_propose_patch | Port `SkillManager` + 10 skills directories | `skills/manager.py`, `skills/<10 dirs>`, `tools/skill.py`, `tools/skill_propose_patch.py`, `tests/integration/test_skills.py` | `tools/SkillTool/` | v4 SkillManager + 10 skills (verbatim) | all 10 skills load; auto-trigger respects v4.9.6 default-OFF | M |
| 11 | Notebook UX + entry | Port v4 chat.ipynb to v5 imports + chat_ui | `entry.py`, `agent.py`, `chat.ipynb`, `chat.md`, `ui/chat_ui.py`, `tests/integration/test_notebook_smoke.py` | n/a | v4 chat.ipynb cells | notebook executes hello-world turn against mock Bedrock | M |
| 12 | Parity tests vs v4 | Run fixed scenarios against v4 and v5; assert behavior parity | `tests/parity/test_parity_*.py` | n/a | v4 test suite | Critical scenario suite 100%; non-critical ≥90%; differences logged in PORT_LOG | M |
| 13 | Cutover + ship zip | Build `compact_v5.zip`, update README, tag `v5.0.0` | `_rebuild_zip.py` (adapted), `verify_ship_zip.py`, `CHANGELOG.md` | v4 zip pipeline | zip extracts and runs notebook smoke test; ship-gate PASS | S |

Each phase ends with: tests pass + Codex review (two-axis) ≥ APPROVE_WITH_FIXES + git commit + tag `v5-phase-N` + status docs updated.

---

### Tracking infrastructure

Three persistent docs in `compact_v5/_status/`. Templates below are **mechanical** — agents update by section, not by free-form rewrite.

#### `V5_BUILD_STATUS.md` (overwrite each session)

```markdown
# V5 Build Status

Last updated: <YYYY-MM-DD HH:MM TZ>
Updated by: <session-id or "human">

## Current phase
- Phase ID: <ID> (canonical: 00..13 or 08_5)
- Phase name: <e.g. "Phase 3: Core read-only tools">
- State: NOT_STARTED | IN_PROGRESS | CODE_COMPLETE | UNDER_REVIEW | DONE
- Started: <YYYY-MM-DD>
- Target completion: <YYYY-MM-DD>

## Done in this phase so far
- [x] <bullet>

## Remaining for this phase
- [ ] <bullet>

## Tests status
- Last `pytest` run: <YYYY-MM-DD HH:MM> — PASS/FAIL (<n> passed, <m> failed)
- Failing tests (if any): <names>

## Codex review status (current phase)
- Last review: <YYYY-MM-DD> — APPROVE | APPROVE_WITH_FIXES | REJECT | NOT_RUN
- Open review comments: <count>; see PORT_LOG row(s) <ids>

## Git
- Branch: v5-build
- Last commit: <sha> "<subject>"
- Last tag: v5-phase-<ID_prev>

## Blockers
- <one line each, or "none">

## Next session: pick up at
- Phase <ID>, step "<remaining bullet>"
- Resume protocol: see _status/RESUME.md
```

#### `V5_RUNNABLE_PORT_LOG.md` (append-only)

```markdown
# V5 Runnable Port Log (append-only)

Format: one row per Runnable pattern adopted. Never delete rows. Mark superseded as STATUS=SUPERSEDED-BY-#<id>.

| ID | Date | Phase | Runnable source (file:section) | v5 target | Adoption verdict | Codex error verdict | Codex fidelity verdict | Commit sha | Notes |
|----|------|-------|--------------------------------|-----------|------------------|---------------------|------------------------|------------|-------|
| 001 | YYYY-MM-DD | N | tools/ToolSearchTool/prompt.ts §"deferred" | tools/tool_search.py | PORT | PASS | FAITHFUL | abc123 | — |

Verdict legend:
- Adoption: PORT (1:1) | ADAPT (semantic match, mechanism differs) | REPLACE (v4-native chosen) | DEFER
- Codex error: PASS | CHANGES_REQUESTED | BLOCKER
- Codex fidelity: FAITHFUL | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | DRIFTED
```

#### `V5_DESIGN_DECISIONS.md` (append-only ADRs)

```markdown
# V5 Design Decisions (append-only)

## ADR-001 — <title>
- Date: <YYYY-MM-DD>
- Phase ID: <ID>
- Status: PROPOSED | ACCEPTED | SUPERSEDED-BY-ADR-<id>
- Context: <2-4 sentences>
- Options considered:
  1. <option> — pro/con
  2. <option> — pro/con
- Decision: <chosen>
- Rationale: <1-3 sentences>
- Runnable-fidelity impact: FAITHFUL | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | DRIFTED — <why>
- Affected files: <paths>
- Linked port-log rows: #<id>
```

---

### Addition Gate (per pattern, BEFORE any port code is written)

**The principle**: every Runnable/Hermes/LF pattern adopted in v5 must demonstrate that it makes v5 **better, not just bigger**. v4's failure was that each addition passed review but the aggregate became unworkable. v5 prevents this with a per-pattern gate.

**Mandatory ADR template — must be ACCEPTED before any port code is committed**:

```markdown
## ADR-NNN — Adopt <pattern name> from <Runnable | Hermes | LF>
- Date: <YYYY-MM-DD>
- Phase ID: <ID>
- Source: <file:section in source repo>

### Question 1 — Replacement or addition?
- Does this REPLACE something v4 already has? (Y/N)
- If YES: what does it replace? Cite v4 file:line.
- If NO (it's an ADDITION): proceed to Q2-Q4 with extra scrutiny.

### Question 2 — Architectural justification (ADDITIONS only)
What user-visible improvement does this produce? Be concrete.
NOT acceptable: "matches Runnable", "completes the parity", "best practice".
Acceptable: "saves N tokens per turn", "fixes failure mode X documented at Y", "reduces failure recovery time from N to M".

### Question 3 — Cost
- Token cost (static prompt): +/-N tokens vs current.
- Token cost (per turn): +/-N tokens vs current.
- Code complexity: +/-N LOC vs not adopting.
- Maintenance: who updates this if Runnable changes?

### Question 4 — Cost worth it?
For ADDITIONS only: is the improvement in Q2 worth the cost in Q3?
If unsure → mark this pattern DEFER, not PORT.

### Decision
- ACCEPTED for v5.0 / DEFERRED to v5.1+ / REJECTED
- If DEFERRED or REJECTED: pattern row in port_log is NOT created.
- If ACCEPTED: port_log row is created, links to this ADR.

### Budget reservation (mandatory before ACCEPTED)
Update the "Token-by-section table" in `prompt/sections.py` with projected token cost (+N static, +N per-turn) BEFORE this ADR can be ACCEPTED. If the reservation exceeds the phase budget, decision must be DEFER (not ACCEPTED).

### Reconciliation (mandatory after code lands in same phase)
After the port code lands, projected (+N) vs measured delta must be reconciled in this ADR within ±10% tolerance. If the measured cost exceeds projection by >10%, ADR status reverts to PROPOSED and the port-log row is blocked from receiving Codex verdicts until the ADR is re-justified or the code is re-budgeted.

### Linked port-log row
#<id> (filled in when port code lands)
```

**Enforcement**: `V5_RUNNABLE_PORT_LOG.md` rows REJECT if there's no `ADR-NNN` reference. The Codex review template at each phase checks PORT_LOG rows have ADR references.

### Aggregate Audit (fixed gates: before phases 4, 7, 10, 13; plus hard gate 8.5 before phase 9)

At fixed checkpoints — **before phases 4, 7, 10, 13** — enforce only metrics whose prerequisite features are already implemented. **Plus an independent hard gate 8.5 before phase 9** (the thin-slice parity gate). Audits gate the next phase from starting.

**Metric checks** (mechanical, run by `tests/aggregate_audit.py`):

| Metric | Pass criterion | Action if fail |
|---|---|---|
| Static prompt tokens | At every audit: ≤ current phase budget; after phase 6: ≤ 2500 absolute | block next phase; rebudget/promote/defer sections until within budget |
| Per-turn schema overhead | From phase 7 onward through phase 8.5: must be **strictly lower than phase-6 baseline on every audit run** AND must show **at least one strict decrease before phase 9** (proves deferred-loading actually fired and stays fired); after phase 9: ≤ v4 baseline − 3000 | block; defer additional tool schemas or redesign registry |
| Tool count | ≤ v4 count + 0 (no net new tools through v5.0) | block; remove or DEFER |
| Skill count | = 10 (v4 production skills, no additions) | block; reject any new skills |
| ADR-to-port-log ratio | every PORT_LOG row has matching ADR | block; backfill ADRs or revert ports |
| Token-by-section table | published, every section has a hard cap, none exceeded | block; refactor section that exceeds cap |
| Local-vs-Bedrock token estimate parity | local `estimate_tokens()` within ±5% of sampled Bedrock prompt accounting on fixed fixtures | block; recalibrate estimator |
| Total request tokens (long-session fixture set) | p95 total input tokens **non-increasing from phase 6 onward** on fixed long-session fixtures | block; add compaction or DEFER pending features |

**Cognitive-load test** (Codex-evaluated, ≤ 200 words from Codex):

```
Codex prompt:
You are auditing v5's current state at end of phase {{ID}} (canonical 00..13 or 08_5).
Read compact_v5/MAIN/agent/prompt/*.md and tools/registry.py.
Simulate: an LLM has just received "Blocked: bash + python_exec
limit reached (200/session)" mid-task.

(a) Will the LLM know to continue with read_file/grep/edit_file?
    Cite which prompt section(s) tell it so.
(b) Will the LLM see those sections under cognitive load (long
    conversation, recent error)? Reason about prompt structure
    and section ordering.
(c) Are there sections buried (mid-list, mid-document) that
    should be promoted?

Output: VERDICT PASS or FAIL with one-paragraph rationale.
```

**FAIL → next phase blocked.** Audit findings get an ADR; fix in the current phase or revert.

### Per-phase Codex review template

Saved at `compact_v5/_status/CODEX_REVIEW_TEMPLATE.md`. Two-axis verdict required. Filled per phase.

```
You are reviewing PHASE {{ID}} of v5 — SageMaker-native re-implementation of Runnable Claude Code (canonical 00..13 or 08_5).

CONTEXT
- Repo: sagemaker-coding-agent
- Branch: v5-build
- Phase: {{NAME}}
- Goal: {{GOAL}}
- Diff: {{GIT_RANGE e.g. v5-phase-{{ID_prev}}..HEAD}}
- Constraints v5 MUST honor: Bedrock-only, no GitHub network, python_exec sandbox, .ipynb workflow, must coexist with v4 unchanged.

RUNNABLE PATTERNS ADOPTED THIS PHASE (porting agent's claims):
{{TABLE: pattern_id | runnable_source_path:section | v5_target_file | claimed_verdict (PORT/ADAPT/REPLACE/DEFER) | justification_for_adaptation_if_any}}

PRODUCE TWO VERDICTS.

=== AXIS A — Errors / bugs ===
For each changed file:
- Correctness defects
- Regressions vs v4 (cite v4 file:line)
- Security (esp. python_exec, file IO, prompt injection)
- Concurrency / races
- Dead code, TODOs left in
- Test coverage gaps

Output:
AXIS A VERDICT: PASS | CHANGES_REQUESTED | BLOCKER
Findings: [severity] file:line — description — fix

=== AXIS B — Runnable-fidelity ===
For EACH pattern row above, judge independently. Read the cited Runnable source before judging.

PATTERN {{id}}: FAITHFUL | FAITHFUL-WITH-JUSTIFIED-ADAPTATION | DRIFTED
- Source intent (1-2 sentences):
- v5 implementation (1-2 sentences):
- Constraint forcing adaptation (closed list: Bedrock | no-network | python_exec | .ipynb | none):
- Drift risk if any:
- Required change to reach FAITHFUL (if currently DRIFTED):

If you find a pattern in the code NOT listed in the table, flag as UNDECLARED_PATTERN.

=== FINAL ===
PHASE {{ID}} OVERALL: APPROVE | APPROVE_WITH_FIXES | REJECT
A-axis: <one-line>
B-axis: <count of FAITHFUL / ADAPTED / DRIFTED>
Required before next phase:
- <bullet>
```

**Auto-reject rule**: `FAITHFUL-WITH-JUSTIFIED-ADAPTATION` + constraint = `none` → automatic REJECT (= unjustified drift labeled as adaptation).

---

### Git checkpoint strategy

- **Branch**: long-lived `v5-build` off `main` at start. `main` keeps v4 untouched. Merge to `main` only at Phase 13 cutover.
- **Commit granularity**: one commit per meaningful step within a phase (~2-6 commits/phase). Convention: `v5/phase-{ID}: <imperative subject>` where `ID ∈ {00..13, 08_5}`.
- **Tag at checkpoint end**: immutable `v5-phase-{ID}` where `ID ∈ {00..13, 08_5}` (canonical zero-padded form; decimal-as-underscore for 8.5, e.g. `v5-phase-08_5`). Tag is only created after Codex returns APPROVE or APPROVE_WITH_FIXES AND all required fixes are merged (no open finding ≥ CHANGES_REQUESTED). Rollback = `git checkout v5-phase-{ID_prev}`.
- **Committed**: source under `compact_v5/MAIN/agent/`, tests, status docs, CHANGELOG, Codex transcripts (`_status/codex_reviews/phase-{ID}.md`).
- **Not committed**: `compact_v5.zip`, `__pycache__/`, runtime `audit_logs/`, runtime `sessions/`, any `.env`. Add to `.gitignore` Phase 0.
- **No force-push, no amend** after a tag is created. Fixes after a tag → next phase or `v5-phase-{ID}.1` patch tag.

---

### Resume protocol (after compaction)

`compact_v5/_status/RESUME.md` contains the verbatim checklist:

```
RESUME PROTOCOL — v5 build

Step 1. Read in this order, do NOT skip or skim:
  1. compact_v5/_status/V5_BUILD_STATUS.md
  2. compact_v5/_status/V5_DESIGN_DECISIONS.md
  3. compact_v5/_status/V5_RUNNABLE_PORT_LOG.md
  4. The phase row for the current phase in PLAN.md (this plan, copied to compact_v5/docs/V5_PLAN.md at Phase 0)
  5. Last 3 commits: git log -n 3 v5-build
  6. Most recent Codex review: compact_v5/_status/codex_reviews/phase-{ID_prev}.md

Step 2. Verify state consistency:
  a. git status — must be clean OR only contain files explicitly listed in V5_BUILD_STATUS.md "Remaining for this phase"; otherwise STOP and report drift.
  b. git rev-parse v5-build — must equal "Last commit" sha in V5_BUILD_STATUS.md
  c. `git for-each-ref refs/tags/v5-phase-* --sort=-version:refname --format='%(refname:short)' --count=1` — must equal expected prior checkpoint tag (deterministic, cross-platform; `head` is not portable to PowerShell-only environments). For phase 9, must equal `v5-phase-08_5` (not `v5-phase-08`).
  d. cd compact_v5/MAIN/agent && pytest -q — match "Tests status" in V5_BUILD_STATUS.md
  e. If any of (a)-(d) disagree, STOP. Do not code. Report drift to user.

Step 3. Pick up work:
  - Open V5_BUILD_STATUS.md "Next session: pick up at"
  - Re-read the phase goal in V5_PLAN.md
  - Re-read the Runnable source(s) listed for this phase BEFORE writing code
  - Update V5_BUILD_STATUS.md: bump "Last updated", set State=IN_PROGRESS

Step 4. As you work:
  - Every Runnable pattern adopted → append row to V5_RUNNABLE_PORT_LOG.md (Codex verdicts blank until review)
  - Every non-trivial choice → append ADR to V5_DESIGN_DECISIONS.md
  - Commit per meaningful step

Step 5. Close the phase:
  - pytest must be green
  - Run Codex with template; save output to _status/codex_reviews/phase-{ID}.md
  - Address all AXIS A BLOCKER and CHANGES_REQUESTED findings (new commits, NOT amend); unresolved items must be recorded as explicit, user-approved exceptions in V5_BUILD_STATUS.md
  - Fill Codex verdicts in V5_RUNNABLE_PORT_LOG.md
  - Tag is FORBIDDEN if any open Codex finding has severity ≥ CHANGES_REQUESTED. Tag: git tag v5-phase-{ID}
  - Update V5_BUILD_STATUS.md: State=DONE, "Next session: pick up at" → phase N+1
  - Commit doc updates
```

---

### Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Pattern invention — agent invents new patterns instead of porting Runnable, claims FAITHFUL | High | High | Codex AXIS B requires citing Runnable source path:section. `UNDECLARED_PATTERN` flag catches code without source citation. PORT_LOG append-only + reviewed each phase. |
| 2 | Status-doc drift after compaction — agent loses thread, docs diverge from git | High | High | Resume protocol Step 2 verifies sha + tag + pytest match docs; STOP on mismatch. Status doc has explicit "Last commit sha" field that is mechanically checkable. |
| 3 | Drifted "FAITHFUL-WITH-JUSTIFIED-ADAPTATION" abuse — agent labels true drift as justified | Medium | High | Codex template forces explicit "Constraint forcing adaptation" from a closed list. `none` + adaptation label = auto-reject. |
| 4 | v4 regressions during cutover — v5 ships missing v4 behavior | Medium | High | Phase 12 parity tests run v4 and v5 against same scenario set; differences logged before tag `v5.0.0`. v4 stays on `main` untouched throughout. |
| 5 | Phase-too-large — phase doesn't finish in 1-2 sessions, leaves repo half-done across compactions | Medium | Medium | Phase ≤ ~6 commits, gated by acceptance criteria. If a phase exceeds 2 sessions, split into N.a / N.b with own tags. Resume always lands on a tagged commit. |
| 6 | Aggregate prompt growth — v5 makes the same mistake as v4 | Medium | High | Hard token budget per section + per-prompt total ≤ 2500 tokens enforced by `prompt/sections.py::estimate_tokens()` at aggregate audit gates and at ship gate. Test fails ship-gate if exceeded. |
| 7 | Cache breaks invisibly — adding/reordering prompt sections silently breaks cache | Medium | Medium | `core/cache.py::detect_cache_break()` ports Runnable's break detection; logs `CacheBreakWarning` on cross-turn cache-token regression. |
| 8 | Parity blind spots — ≥90% scenario parity can hide critical regressions | Medium | High | Add must-pass critical-scenario suite (security deny, blocked-tool continuation, retry, prompt assembly, resume after compaction) requiring 100% pass; the ≥90% threshold applies only to non-critical scenarios. |
| 9 | Token metric mismatch — local `estimate_tokens()` differs from Bedrock real tokenizer | Medium | High | Dual-metric gate: local estimate + sampled live Bedrock prompt accounting on fixed fixtures; aggregate audit fails if estimates diverge >5%. |
| 10 | Legacy prompt contamination — byte-for-byte v4 skill carryover may import v4 prompt anti-patterns | Medium | Medium | Run per-skill prompt budget + buried-instruction audit before tagging Phase 10; refactor or DEFER offending skills. |
| 11 | Deferral non-use under stress — LLM may not call `tool_search` when needed | Medium | High | Add tests where model must recover via `tool_search` after blocked tools; phase 7 fails if no recovery path. Cognitive-load audit (phase 6 onward) checks that deferred tools are actually discoverable. |
| 12 | Scenario-set bias / fixture gaming — parity suite overfits to curated fixtures and still passes 100% | Medium | High | Maintain locked baseline + rotating adversarial fixtures; require delta review and explicit user/Codex approval for any fixture edits. |
| 13 | Decimal-phase automation breakage — tooling/scripts may assume integer-only phase ids and break on `8.5` | Medium | Medium | Canonical checkpoint id schema (`P00..P13`, `P08_5`) used everywhere (git tags, status fields, test paths, codex review filenames). Plan-level grep guard against bare `8.5` in scripts. |
| 14 | Checkpoint identity drift — tag name, status doc Phase ID field, and Codex review filename diverge | Medium | Medium | Single canonical Phase ID field (`00..13`, `08_5`) in V5_BUILD_STATUS.md; pre-tag lint check (`tests/lint_phase_id.py`) validates tag name, codex review filename, and status field all match before allowing `git tag` to be created. `lint_phase_id.py` runs in CI and is a required pre-tag check in phase-close checklist. |

---

## Critical files for implementation

- `compact_v5/_status/V5_BUILD_STATUS.md` (Phase 0)
- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` (Phase 0)
- `compact_v5/_status/V5_DESIGN_DECISIONS.md` (Phase 0)
- `compact_v5/_status/CODEX_REVIEW_TEMPLATE.md` (Phase 0)
- `compact_v5/_status/RESUME.md` (Phase 0)
- `compact_v5/MAIN/agent/tools/tool_search.py` (Phase 7 — the key win)
- `compact_v5/MAIN/agent/prompt/sections.py` (Phase 6 — fixes the buried-matrix failure mode)
- `compact_v5/MAIN/agent/tools/registry.py` (Phase 2 — replaces v4 monolith TOOLS)
- `compact_v5/MAIN/agent/core/query_engine.py` (Phase 8 — extracts Agent.run)
- `compact_v5/_rebuild_zip.py` (Phase 13 — adapt v4 builder for nested → flat)

Reference (read-only) anchors:
- `D:/Github/sagemaker-coding-agent/compact_v4/MAIN/agent/sagemaker_agent.py` (v4 monolith — source-of-truth for current behavior)
- `D:/Github/sagemaker-coding-agent/_archive/compare_code/gg-claude-code-runnable/src/tools/ToolSearchTool/prompt.ts`
- `D:/Github/sagemaker-coding-agent/_archive/compare_code/gg-claude-code-runnable/src/tools.ts`
- `D:/Github/sagemaker-coding-agent/_archive/compare_code/gg-claude-code-runnable/src/QueryEngine.ts`
- `D:/Github/sagemaker-coding-agent/_archive/compare_code/gg-claude-code-runnable/src/constants/prompts.ts`

---

## Verification (end-to-end)

When the v5 build is complete (Phase 13 done), the user can verify by:

1. **Functional smoke test**:
   ```
   cd compact_v5/MAIN/agent
   pytest -q
   # All tests in unit/, tools/, integration/, parity/ must pass.
   ```

2. **Build the ship zip**:
   ```
   cd compact_v5
   python _rebuild_zip.py
   python verify_ship_zip.py    # must report "RESULT: PASS — zip is ship-ready"
   ```

3. **Smoke-run the notebook**:
   ```
   # In SageMaker (or local Jupyter):
   # 1. Unzip compact_v5.zip
   # 2. Open chat.ipynb
   # 3. Run cells 1-3 (install / config / launch)
   # 4. Send a hello-world message — verify Bedrock invocation, security gate, tool dispatch
   ```

4. **Token-budget verification**:
   ```
   cd compact_v5/MAIN/agent
   python -c "from prompt import build_system_prompt, estimate_tokens; \
              p = build_system_prompt(default_ctx()); \
              assert estimate_tokens(p) <= 2500, 'static prompt too long'"
   ```

5. **Parity verification**:
   ```
   pytest -q tests/parity/
   # Logs scenario-by-scenario v4-vs-v5 differences. ≥90% parity required.
   ```

6. **Codex final review**:
   - Run Codex on the full v5 codebase with the AXIS A + AXIS B template.
   - Verdict must be APPROVE on both axes.
   - All PORT_LOG rows must have Codex verdicts filled in.
   - All ADRs must be ACCEPTED (none PROPOSED).

If any of (1)-(6) fail, **v5 does not ship.** v4.10.10 remains production until the failure is addressed.
