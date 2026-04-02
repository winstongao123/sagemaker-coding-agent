# PS_[03] Comprehensive Prompt Analysis: Runnable vs V4

> **Purpose**: Track EVERY prompt in Runnable, what V4 learned, what V4 didn't implement and why.
> **Key constraint**: V4 may use Haiku (4,096-token cache minimum). Every token matters.
> **Created**: 2026-04-02 | **V4 version**: 4.3.2

---

## Runnable Prompt Inventory (24 distinct prompts, ~45-55K tokens total)

### Category 1: System Prompts

| # | Prompt | Runnable Source | Tokens | V4 Status | Action |
|---|--------|----------------|--------|-----------|--------|
| 1 | Default System Prompt | `constants/prompts.ts:443-577` | ~9K | IMPLEMENTED (73 lines, ~1.5K tok) | V4 is leaner by design — Haiku-safe |
| 2 | Coordinator System Prompt | `coordinator/coordinatorMode.ts:110-368` | ~3.2K | NOT IMPLEMENTED | See analysis below |
| 3 | Proactive/Autonomous Mode | `constants/prompts.ts:860-914` | ~1.1K | NOT APPLICABLE | V4 is interactive only, no background mode |
| 4 | Environment Info | `constants/prompts.ts:606-709` | ~0.4K | IMPLEMENTED | Workspace, platform, model info injected |

### Category 2: Agent/Sub-agent Prompts

| # | Prompt | Runnable Source | Tokens | V4 Status | Action |
|---|--------|----------------|--------|-----------|--------|
| 5 | Agent Tool Description | `tools/AgentTool/prompt.ts:66-287` | ~2.5K | IMPLEMENTED (v4.3.1) | "Never delegate understanding" included |
| 6 | General Purpose Agent | `built-in/generalPurposeAgent.ts` | ~0.4K | IMPLEMENTED | Similar multi-step guidance |
| 7 | Explore Agent (RO) | `built-in/exploreAgent.ts:12-82` | ~1.1K | PARTIAL | V4 explore has RO tools but lacks explicit "STRICTLY PROHIBITED" phrasing |
| 8 | Verification Agent | `built-in/verificationAgent.ts:9-128` | ~3.6K | NOT IMPLEMENTED | High value — adversarial testing |
| 9 | Subagent Notes | `constants/prompts.ts:766-770` | ~0.15K | PARTIAL | V4 has output format but not absolute-path requirement |

### Category 3: Memory Prompts

| # | Prompt | Runnable Source | Tokens | V4 Status | Action |
|---|--------|----------------|--------|-----------|--------|
| 10 | Memory Extraction | `services/extractMemories/prompts.ts:50-94` | ~0.6K | IMPLEMENTED (v4.2) | WHAT_NOT_TO_SAVE included |
| 11 | Session Memory Update | `services/SessionMemory/prompts.ts:43-80` | ~1.2K | NOT IMPLEMENTED | V4 uses simpler memory.md approach |
| 12 | Memory Types & Guidance | `memdir/memoryTypes.js` | ~0.8K | IMPLEMENTED | 4-type taxonomy (USER/FEEDBACK/PROJECT/REFERENCE) |
| 13 | Memory Loading (System) | `memdir/memdir.ts:186-330` | ~2K | IMPLEMENTED | memory.md loaded into cached prefix |

### Category 4: Compaction Prompts

| # | Prompt | Runnable Source | Tokens | V4 Status | Action |
|---|--------|----------------|--------|-----------|--------|
| 14 | Compact (Full) | `services/compact/prompt.ts:18-142` | ~2.2K | IMPLEMENTED (v4.3.1) | 9-section format, NO_TOOLS preamble |
| 15 | Compact (Partial) | `services/compact/prompt.ts:144-203` | ~1.8K | NOT IMPLEMENTED | Only useful for very long sessions |

### Category 5: Tool Descriptions

| # | Prompt | Runnable Source | Tokens | V4 Status | Action |
|---|--------|----------------|--------|-----------|--------|
| 16 | Bash Tool (90+ lines) | `tools/BashTool/prompt.ts` | ~3.5K | PARTIAL (v4.3.2) | V4 has WHEN/WHEN NOT but shorter. Git protocol NOT included. |
| 17 | File Read Tool | `tools/FileReadTool/prompt.ts:11-48` | ~0.45K | IMPLEMENTED (v4.3.2) | WHEN pattern added |
| 18 | Grep Tool | `tools/GrepTool/prompt.ts:5-17` | ~0.3K | IMPLEMENTED (v4.3.2) | WHEN pattern added |
| 19 | Glob Tool | `tools/GlobTool/prompt.ts:2-6` | ~0.15K | IMPLEMENTED (v4.3.2) | WHEN pattern added |
| 20 | Edit/Write Tools | (referenced) | ~0.3K | IMPLEMENTED | Similar guidance |

### Category 6: Dynamic Sections

| # | Prompt | Runnable Source | Tokens | V4 Status | Action |
|---|--------|----------------|--------|-----------|--------|
| 21 | Function Result Clearing | `constants/prompts.ts:821-839` | ~0.15K | NOT IMPLEMENTED | Low value — V4's microcompact handles this |
| 22 | Output Style Config | `constants/prompts.ts:150-157` | ~0.3K | NOT IMPLEMENTED | Low value — V4 has fixed style |
| 23 | Scratchpad Instructions | `constants/prompts.ts:797-819` | ~0.35K | NOT IMPLEMENTED | Medium value — temp file guidance |
| 24 | Skill Discovery | (referenced) | ~1K | PARTIAL | V4 has skills but no auto-discovery prompt |

---

## Detailed Analysis: What V4 Should Enhance

### HIGH PRIORITY

#### A. Verification Agent Prompt (NOT in V4)
**What Runnable has**: A dedicated adversarial testing agent that tries to BREAK the implementation, not confirm it works. 3,600 tokens of detailed testing strategies per domain (frontend, backend, CLI, infra, data pipelines).

**Key quote**: "Your job is not to confirm the implementation works — it's to try to break it."

**V4 action**: V4 has `skills/review/SKILL.md` and `skills/clara/` but NO adversarial verification agent. The Clara review is code review (static analysis), not runtime testing.

**Decision**: **IMPLEMENT** — Add verification agent type to AGENT_TYPES with adversarial testing prompt. This is the highest-value missing prompt.

**Haiku consideration**: Verification agent runs as sub-agent, so its prompt is separate from main cache. Can be longer.

#### B. Explore Agent Explicit RO Enforcement (PARTIAL in V4)
**What Runnable has**: 
```
"=== CRITICAL: READ-ONLY MODE - NO FILE MODIFICATIONS ===
This is a READ-ONLY exploration task. You are STRICTLY PROHIBITED from:
- Creating new files
- Modifying existing files  
- Deleting files"
```

**V4 action**: V4's explore agent has RO tool restrictions but lacks this explicit prohibition in the prompt. The LLM might still TRY to call write tools even though they're not available, wasting a tool call.

**Decision**: **ENHANCE** — Add explicit RO prohibition to explore agent prompt_suffix.

#### C. Bash Git Safety Protocol (PARTIAL in V4)
**What Runnable has**: 90+ line bash tool description including:
- Complete git commit protocol with HEREDOC
- PR creation protocol with body template
- "NEVER force push to main/master"
- "Create NEW commits, don't amend after hook failure"
- Stage specific files (not `git add -A`)

**V4 has**: System prompt section "Executing Actions with Care" covers git safety but NOT in the bash tool description itself. The AI sees tool descriptions more reliably than system prompt.

**Decision**: **ENHANCE** — Add key git safety rules to bash tool description (not the full 90 lines — Haiku budget constraint).

### MEDIUM PRIORITY

#### D. Subagent Absolute Path Requirement
**What Runnable has**: "In your final response, share file paths (always absolute, never relative)"

**V4 action**: Not explicitly stated in sub-agent prompts.

**Decision**: **ENHANCE** — Add to all sub-agent prompt_suffix strings.

#### E. Partial Compact (NOT in V4)
**What Runnable has**: A variant that only summarizes recent messages, keeping earlier context verbatim.

**V4 action**: V4 always does full summary.

**Decision**: **SKIP** — Full summary is sufficient for V4's typical session length (10-30 turns). Partial compact adds complexity for marginal benefit.

#### F. Scratchpad Instructions (NOT in V4)
**What Runnable has**: Guidance to use a dedicated temp directory instead of /tmp.

**Decision**: **SKIP** — V4 runs in SageMaker Jupyter where temp files go to the notebook directory naturally.

### LOW PRIORITY / NOT APPLICABLE

#### G. Coordinator Mode (NOT in V4)
**Why relevant**: Would enable V4 to orchestrate multiple sub-agents for large tasks.

**Why complex**: Requires complete system prompt REPLACEMENT (not addition), mode switching logic, and SendMessage infrastructure.

**Decision**: **DEFER** — Genuinely needs architectural work. Document the full prompt for future reference. NOT a prompt-only change.

#### H. Session Memory Update (NOT in V4)
**What Runnable has**: 10-section structured session notes.

**Decision**: **SKIP** — V4's memory.md with 4 typed sections is sufficient and simpler.

#### I. Proactive Mode (NOT in V4)
**Decision**: **NOT APPLICABLE** — V4 is interactive-only by design (SageMaker Jupyter).

#### J. Fork Subagent
**Decision**: **NOT POSSIBLE** — Bedrock caching is server-side. Cannot control byte-identical API prefix.

---

## Haiku Caching Constraint Analysis

**Problem**: Haiku 4.5 requires 4,096+ tokens for prompt caching. V4's static system prompt is ~3,565 tokens — BELOW threshold.

**Impact**: When using Haiku, every token of the system prompt is charged at full price every turn. This means:
1. System prompt MUST be lean for Haiku (no bloat)
2. Tool descriptions count toward the system prompt token budget
3. More detailed prompts = higher per-turn cost on Haiku

**Mitigation strategy**:
- Keep system prompt under 100 lines (currently 73 — good)
- Enhanced tool descriptions add ~200 tokens total (acceptable)
- Verification agent prompt is sub-agent only (doesn't affect main cache)
- For Sonnet: system + tools exceeds 4,096, so caching works fine

**Recommendation**: V4's lean prompt is a FEATURE for Haiku, not a bug. Enhancements should be targeted (high-value lines only), not verbose.

---

## V4 Prompt Quality Assessment

### What V4 Does BETTER Than Runnable (for its context)
1. **Leaner system prompt** — 73 lines vs 900+ (critical for Haiku budgets)
2. **Integrated security section** — Trust boundary, workspace enforcement in system prompt
3. **Document workflow** — create_chart FIRST then create_word/pdf guidance
4. **MCP integration** — Auto-registered MCP tools with prefer-MCP guidance
5. **Memory in cached prefix** — Free after first turn on Sonnet

### What V4 Should Improve (from this analysis)
1. Add verification agent type (HIGH — adversarial testing)
2. Add explicit RO prohibition to explore agent (HIGH — prevents wasted calls)
3. Add git safety to bash tool description (MEDIUM — currently only in system prompt)
4. Add absolute path requirement to sub-agent prompts (LOW — quality improvement)

---

## Implementation Tracking

| Enhancement | Priority | Status | V4 Version | Lines Changed |
|------------|----------|--------|------------|---------------|
| WHEN-not-WHAT tool descriptions | HIGH | DONE | v4.3.2 | 5 tools updated |
| Cache-breakage detection | HIGH | DONE | v4.3.2 | 3 locations |
| Verification agent type | HIGH | DONE | v4.3.2 | New "verify" agent type with adversarial testing prompt |
| Explore agent RO enforcement | HIGH | DONE | v4.3.2 | "STRICTLY PROHIBITED" + absolute paths |
| Bash git safety in tool desc | MEDIUM | DONE | v4.3.2 | Git safety rules in bash tool description |
| Subagent absolute path | LOW | DONE | v4.3.2 | All 4 agent types: build, explore, general, verify |
| Coordinator Mode | DEFERRED | — | Future | Architectural |
| Fork Subagent | NOT POSSIBLE | — | — | Bedrock limitation |
| Partial Compact | SKIPPED | — | — | Low value |
| Session Memory Update | SKIPPED | — | — | V4's approach sufficient |
| Proactive Mode | N/A | — | — | Not applicable |

---

*This document tracks ALL 24 Runnable prompts and their V4 status. Updated: 2026-04-02.*
