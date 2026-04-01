# PS_LEARNING_JOURNEY — V4 Development from Runnable Claude Code

> **Purpose**: Comprehensive record of what was learned from studying the Runnable Claude Code codebase, how it was applied to V4, what decisions were made and why.
> **Date**: 2026-04-01
> **V4 version at time of writing**: 4.3.0
> **Runnable source**: `gg-claude-code-runnable/src/` (1,438 TypeScript files)

---

## 1. What Is This Document?

This documents the full engineering journey of building V4 of the SageMaker Coding Agent by studying the production Claude Code (Claude's own CLI tool) codebase. The goal was not to copy it, but to extract every relevant agentic engineering lesson and apply what makes sense in a Python/SageMaker/Bedrock environment.

---

## 2. How We Studied Runnable

### Phase 1 — V2 Analysis (before V4.2)
Initial deep dive produced `PS_DEEP_ANALYSIS_V2.md` (586 lines). Covered:
- Token optimization (microcompact, disk offload, batch caps)
- Memory extraction (WHAT_NOT_TO_SAVE, 4-type structure)
- Context management (cold cache detection, 4/3 token padding)
- Tool dispatch (parallel RO tools, FILE_UNCHANGED_STUB, PTL retry)

This produced **V2-A through V2-J** (10 features) implemented in V4.2.0 and V4.2.1.

### Phase 2 — V3 Fresh Audit (2026-04-01)
Second full audit of all 1,438 TS files, focused on patterns NOT covered by V2. Produced `PS_DEEP_ANALYSIS_V3.md` (226 lines). Found:
- Subagent coordination (Coordinator Mode, SendMessage, LocalAgentTask, Fork Subagent)
- Prompt engineering (coordinator role-swap prompt, memoized assembly, tool description patterns)
- Context management (position-pinned cache edits, diminishing returns, reactive compact)
- Memory (forked extraction, staleness, "already wrote" guard)
- Permissions (speculative bash classifier)

This produced **V3-A through V3-F** (6 features) implemented in V4.3.0.

---

## 3. What We Implemented (Chronological)

### V4.0 → V4.1 (6 Claude Code features)
| Feature | From Runnable |
|---------|--------------|
| Prompt cache boundary (static/dynamic split) | `services/api/claude.ts` |
| Catastrophic path hard block | `tools/BashTool/` CATASTROPHIC constant |
| Partial view guard | No direct equivalent |
| Command auto-classifier (RO bypass) | `tools/BashTool/bashPermissions.ts` |
| 4-type memory (USER/FEEDBACK/PROJECT/REFERENCE) | `memdir/memoryTypes.ts` |
| Memory auto-extraction at session end | `services/extractMemories/extractMemories.ts` |

### V4.2.0 (V2-A through V2-G from Runnable)
| Feature | From Runnable |
|---------|--------------|
| Tool result size cap + disk offload (50K chars) | `constants/toolLimits.ts` |
| Enhanced memory extraction prompt (WHAT_NOT_TO_SAVE) | `services/extractMemories/prompts.ts` |
| Clear always_allow on compact | `services/compact/autoCompact.ts` |
| Cold-cache time-based microcompact (30 min) | `services/compact/timeBasedMCConfig.ts` |
| Conservative 4/3 token estimation padding | `query/tokenBudget.ts` |
| Per-batch aggregate tool result cap (200K) | `constants/toolLimits.ts` |

### V4.2.1 (V2-H through V2-J + Bedrock fix)
| Feature | From Runnable |
|---------|--------------|
| FILE_UNCHANGED_STUB | `FileReadTool/prompt.ts` |
| Parallel read-only tool execution | `services/tools/toolOrchestration.ts` partitionToolCalls() |
| PTL retry logic (3 attempts) | `services/compact/compact.ts` truncateHeadForPTLRetry() |
| Fix: remove anthropic_beta header for Bedrock | Bedrock-specific (not Runnable) |

### V4.3.0 (V3-A through V3-F + bug fixes)
| Feature | From Runnable | V4 Status |
|---------|--------------|-----------|
| Diminishing returns warning (3+ turns <500 tok) | `query/tokenBudget.ts` | Advisory only |
| Memory 200-line / 25KB cap | `memdir/memdir.ts` | Exact match |
| Cold-cache keepRecent=1 (more aggressive) | `timeBasedMCConfig.ts` | Implemented |
| Auto-memory "already wrote" skip | `extractMemories.ts` hasMemoryWritesSince() | Implemented |
| Per-turn cache indicator (WRITE/HIT/INACTIVE) | New in V4 | Implemented |
| Cache savings USD in /cost | New in V4 | Implemented |
| Bug: empty dynamic system prompt block | Bedrock-specific | Fixed |
| Bug: cache savings used wrong model pricing | New in V4 | Fixed |

---

## 4. What We Did NOT Implement (and Why)

| Pattern | Runnable File | Reason Not Implemented |
|---------|--------------|----------------------|
| **Coordinator Mode** | `coordinator/coordinatorMode.ts` | High complexity. Requires two incompatible system prompts, mode-switching logic, full orchestrator mental model. Deferred to V4.4. |
| **SendMessage Tool** | `tools/SendMessageTool/` | TypeScript-specific async message queue. Python equivalent needs different infrastructure. |
| **LocalAgentTask state machine** | `tasks/LocalAgentTask/` | UI-bound TypeScript state. Not applicable to Jupyter notebook context. |
| **Cached Microcompact (position pinning)** | `services/compact/microCompact.ts` | Requires tracking edit positions across API calls. High complexity, medium value. |
| **Fork Subagent** | `tools/AgentTool/forkSubagent.ts` | Requires byte-identical API prefix engineering. Very high complexity. |
| **Reactive Compact** | `services/compact/autoCompact.ts` | Low value for SageMaker: wastes one API call to hit PTL error. PTL retry (V2-J) is better. |
| **Memory staleness tracking** | `memdir/memoryAge.ts` | Unknown complexity. Low immediate value. |
| **LLM-based bash classifier** | `tools/BashTool/bashPermissions.js` | Requires LLM call for every bash command. V4's static regex classifier is sufficient. |
| **Snip boundaries** | `QueryEngine.ts` | UI/history feature. Not applicable. |
| **Component-based prompt assembly** | `utils/queryContext.ts` | V4 has static/dynamic split. Full memoized component assembly is over-engineering for single-file agent. |

---

## 5. Prompt Engineering Lessons from Runnable

This is the most important section — what Runnable does with prompts is its hidden engineering moat.

### Lesson 1: Coordinator Prompt Is a Complete Role Swap
**File**: `src/coordinator/coordinatorMode.ts` (lines 111-369)

Runnable doesn't add instructions to the system prompt when acting as an orchestrator. It **replaces the entire system prompt** with a different one that:
- Defines the agent's identity as "orchestrator" not "executor"
- Teaches workflow phases: Research → Synthesis → Implementation → Verification
- Explicitly says "parallelism is your superpower" — agents don't parallelize unless told to
- Prescribes worker output format: Scope, Result, Key files, Files changed, Issues
- Provides a decision table for "continue existing worker vs spawn fresh"

**V4 implication**: V4's system prompt says "Parallel independent tools." This is one line. Runnable's approach shows that parallelism needs a full section with mental model, examples, and explicit instruction. Opportunity for V4.4.

### Lesson 2: Tool Descriptions ARE Prompt Engineering
**File**: Various tool files in `src/tools/`

How a tool is named and described in the tools array directly shapes which tools the LLM calls and how. Runnable uses precise, action-oriented descriptions:
- Short imperative names (read_file not "ReadFileFromFilesystem")
- Description explains WHEN to use, not just WHAT it does
- Parameter descriptions include constraints and examples

**V4 implication**: V4's tool descriptions were written once and not revisited. Reviewing them against Runnable patterns could reduce unnecessary tool calls.

### Lesson 3: WHAT_NOT_TO_SAVE Is as Important as WHAT_TO_SAVE
**File**: `src/services/extractMemories/prompts.ts`

The memory extraction prompt has an explicit section listing what NOT to save: code patterns, git history, fix recipes, ephemeral state, project structural facts. Without this, the LLM saves noise that bloats memory.

**V4 status**: Implemented in V4.2.0 (V2-C). This was the most immediately impactful prompt lesson.

### Lesson 4: Memory Is a System Prompt Section (Not Context Injection)
**File**: `src/memdir/memdir.ts`

Memory is injected as part of the static system prompt prefix — in the cache-key. This means:
- Memory is always present in the model's context
- After first turn, memory tokens are free (served from cache)
- V4 does the same: `_load_persistent_memory()` appends to `_base_prompt` before caching

**V4 status**: Correctly implemented. Memory is part of the cached static section.

### Lesson 5: Worker Output Format Is Prescribed
**File**: `src/tools/AgentTool/forkSubagent.ts` (lines 189-195)

Workers are told exactly what format to return: Scope, Result, Key files, Files changed, Issues. This makes coordinator synthesis reliable — if workers return free-form text, synthesis is unpredictable.

**V4 status**: V4's subagent types have `prompt_suffix` that adds role instructions but not structured output format. Opportunity to add output format requirements to subagent prompts.

### Lesson 6: Parallel Tool Execution Needs Explicit Permission in Prompt
**File**: `src/coordinator/coordinatorMode.ts` section 4

The coordinator prompt explicitly tells the agent: "When you need information from multiple sources, call multiple tools at once. Don't wait for one to finish before starting another."

**V4 status**: V4's system prompt says "Parallel independent tools." Could be more explicit about the mental model.

---

## 6. V4 Prompt System — What to Improve (Next Actions)

Based on studying Runnable, these are prompt-level improvements V4 should make:

| # | Improvement | Priority | Status |
|---|-------------|----------|--------|
| P1 | Add explicit parallelism + sub-agent coordination to SYSTEM_PROMPT | HIGH | ✅ DONE (v4.3.1) |
| P2 | Add structured output format to subagent `prompt_suffix` (Scope/Result/Files/Issues) | HIGH | ✅ DONE (v4.3.1) |
| P3 | Upgrade all tool descriptions for precision (WHEN to use, not just WHAT) | MEDIUM | ✅ DONE (v4.3.1) |
| P4 | Add "Doing Tasks", "Actions with Care", "Output Efficiency", "Git Safety" sections | HIGH | ✅ DONE (v4.3.1) |
| P5 | Add NO_TOOLS preamble to compact/summary LLM call | MEDIUM | ✅ DONE (v4.3.1) |
| P6 | Add coordinator mode prompt (complete role swap) for orchestration tasks | FUTURE (V4.4) | TODO |
| P7 | Add conditional dynamic prompt sections (MCP section only if MCP present) | LOW | TODO |

---

## 7. Testing Record

### What Was Tested on Bedrock

| Test ID | Description | Model | Status | Date |
|---------|-------------|-------|--------|------|
| T1 | Cache INACTIVE warning (Haiku, below threshold) | Haiku 4.5 | PASS | 2026-04-01 |
| T2 | Cache WRITE+HIT (Sonnet, warm cache) | Sonnet 4.5 | PASS | 2026-04-01 |
| T3 | Parallel RO tools (glob + grep) | Haiku 4.5 | PASS | 2026-04-01 |
| T4 | Subagent isolation (explore type) | Haiku 4.5 | PASS | 2026-04-01 |
| T5 | Memory 200-line cap (V3-B) | Haiku 4.5 | PASS | 2026-04-01 |
| T6 | Multi-turn 5 turns, no ghost tool calls | Haiku 4.5 | PASS | 2026-04-01 |
| T7 | FILE_UNCHANGED_STUB inside/outside workspace | Haiku 4.5 | PASS | 2026-04-01 |
| T8 | Diminishing returns logic | Sonnet 4.5 | PASS | 2026-04-01 |
| T9 | Subagent depth limit hard stop | Haiku 4.5 | PASS | 2026-04-01 |
| T10 | Cache savings USD correct model pricing | Sonnet 4.5 | PASS | 2026-04-01 |

### Bugs Found During Testing (Fixed)
1. Empty dynamic system prompt block → Bedrock ValidationException (fixed in V4.3.0)
2. `get_cache_savings_usd()` used `CONFIG.model_id` instead of session model (fixed in V4.3.0)

### Haiku 4.5 Caching Note
Haiku 4.5 requires 4,096 token minimum for prompt caching. Current system+tools = ~3,565 tokens — below threshold. Caching shows as `[Cache: INACTIVE]`. Use Sonnet 4.5 for caching. This is a model constraint, not a bug.

---

## 8. What Remains Unlearned from Runnable

**v4.3.1 UPDATE**: All prompt patterns have now been extracted and studied. See `PS_PROMPT_COMPARISON.md` for the full side-by-side analysis.

**Resolved in v4.3.1:**
- ✅ Tool description patterns — all 7 key tools upgraded
- ✅ Compact/summary LLM prompt — NO_TOOLS preamble added
- ✅ Subagent prompt_suffix patterns — structured output format added to explore/general/build
- ✅ Coordinator principles — "never delegate understanding", Research→Synthesize→Implement→Verify added to SYSTEM_PROMPT
- ✅ yolo-classifier prompts — confirmed empty placeholder files in Runnable (nothing to learn)

**Still deferred (architectural, not prompt):**
- **Coordinator Mode** — requires two-prompt system + mode switching. Deferred to V4.4.
- **SendMessage** — requires async message queue. Not applicable to sync subagents.
- **Fork Subagent** — requires byte-identical API prefix. Very high complexity.
- **Conditional dynamic sections** — MCP-only section, feature flags. Low priority for single-file agent.

---

## 9. Codex Reviews Performed

| Version | Date | Finding | Resolved |
|---------|------|---------|---------|
| V4.2.0 | 2026-04-01 | 6/10 SSE issues | All fixed |
| V4.3.0 initial | 2026-04-01 | False positive (on_compact_fn stale line number) | N/A |
| V4.3.0 final | 2026-04-01 | Background job started, output empty | Inconclusive |
| V4.3.1 prompt upgrade | 2026-04-01 | Pending | TBD |

### V4.3.1 — Prompt Engineering Upgrade
Implemented after full prompt extraction from Runnable. See `PS_PROMPT_COMPARISON.md` for details.
- SYSTEM_PROMPT: 35 → 72 lines (6 new sections from Runnable)
- Tool descriptions: 7 tools upgraded to Runnable-quality (WHEN not just WHAT)
- Sub-agent prompts: 3 types upgraded with structured output format
- Compact prompt: NO_TOOLS preamble added

---

*Last updated: 2026-04-01.*
