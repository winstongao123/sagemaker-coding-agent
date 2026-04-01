# PS_PROMPT_COMPARISON — Runnable Claude Code vs V4 Prompt Engineering

> **Purpose**: Side-by-side comparison of ALL prompts in Runnable Claude Code vs SageMaker Coding Agent V4.
> **Date**: 2026-04-01
> **V4 version**: 4.3.1 (after prompt upgrade)
> **Runnable source**: `gg-claude-code-runnable/src/` (1,438 TypeScript files)

---

## 1. System Prompt

### Runnable (~900 lines across 15+ sections)
- `constants/prompts.ts`: getSystemPrompt() → array of memoized sections
- Sections: Identity, System, Doing Tasks, Actions with Care, Using Tools, Session Guidance, Tone/Style, Output Efficiency, Environment, Memory, MCP, Scratchpad
- Dynamic boundary: `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` separates cacheable/volatile content
- Feature-gated conditional sections (PROACTIVE, KAIROS, COORDINATOR, BUDDY, etc.)
- Model-aware variations (ANT_USER_TYPE branching for internal Anthropic users)

### V4 (~72 lines, single constant)
- `sagemaker_agent.py` line 5870: SYSTEM_PROMPT string
- Sections: System, Using Tools, Doing Tasks, Executing Actions, Output, Sub-agent Coordination, Memory, Documents, Security, MCP, Commands
- Cache boundary: `# === DYNAMIC ===` marker
- Dynamic content: memory + project instructions + skills appended after boundary

### What V4 Learned (v4.3.1)
| Section | Source | V4 Implementation |
|---------|--------|------------------|
| "Doing Tasks" | `getSimpleDoingTasksSection()` lines 199-253 | Condensed to 8 rules: don't gold-plate, simplest approach, read before edit, no unnecessary abstractions |
| "Actions with Care" | `getActionsSection()` lines 255-267 | 6 rules: reversibility, blast radius, destructive/hard-to-reverse/visible actions |
| "Output Efficiency" | `getOutputEfficiencySection()` lines 403-428 | 4 rules: lead with answer, skip filler, one sentence not three |
| "Git Safety" | `BashTool/prompt.ts` lines 42-161 | 5 rules: no --no-verify, new commits, no force push main, HEREDOC, specific staging |
| "Sub-agent Coordination" | `coordinator/coordinatorMode.ts` lines 198-336 | 4 rules: parallel spawn, never delegate understanding, Research→Synthesize→Implement→Verify |
| "Using Tools" | `getUsingYourToolsSection()` lines 269-314 | Tool preference hierarchy (dedicated over bash), parallel calls, diagnose failures |

### What V4 Intentionally Skipped
| Section | Reason |
|---------|--------|
| Feature-gated sections (PROACTIVE, KAIROS, BUDDY) | Not applicable to SageMaker notebook environment |
| ANT_USER_TYPE branching | Internal Anthropic feature |
| Scratchpad directory | V4 uses workspace directly |
| Numeric length anchors (≤25 words between tools) | Over-constraining for coding tasks |
| Undercover instructions | Internal Anthropic feature |
| Language preference injection | SageMaker users work in English |

---

## 2. Tool Descriptions

### Runnable Pattern
- Each tool has a `prompt.ts` file with 10-90 lines of description
- Describes WHEN to use (not just WHAT it does)
- Includes anti-patterns ("do NOT use bash when…")
- Parameter descriptions include constraints and examples
- **Key insight**: Tool descriptions ARE prompt engineering — they directly shape which tools the LLM calls

### V4 Before vs After (v4.3.1)

| Tool | Before (v4.3.0) | After (v4.3.1) | Runnable Equivalent |
|------|-----------------|----------------|-------------------|
| read_file | "Read file contents with line numbers" | "Read file contents with line numbers. Use offset/limit for large files. Can read images, PDFs, notebooks. You MUST read before editing." | 30+ lines covering absolute paths, PDF pages, notebooks, images, cat -n format |
| write_file | "Write content to file. Must read first if overwriting." | "You MUST read first if file exists. Prefer edit_file for modifications — use write_file only for new files or complete rewrites." | Prefers Edit over Write, NEVER create docs unless asked |
| edit_file | "Edit file by replacing EXACT string match. Must read first." | "old_string must be unique — include more context if not, or use replace_all=true for all occurrences." | Detailed uniqueness guidance, replace_all for renaming |
| bash | "Run shell command. Use for git, pip, scripts." | "Do NOT use for file read/edit/search — use dedicated tools instead." | 90+ lines: tool preference, git safety, parallel commands, sleep guidance, sandbox |
| grep | "Search for text or keywords inside files." | "Search file contents using regex. Use this instead of bash grep/rg." | Multiline, output modes, file type filtering, head_limit |
| glob | "Find files by name pattern" | "Use this instead of bash find/ls. Results sorted by modification time." | Sorted by mtime, use for file finding not bash |
| task | "Spawn sub-agent: explore, plan, review, build, general." | "Do NOT use for simple searches — use glob/grep directly. Write prompts like briefing a colleague." | 220 lines: when/how to delegate, fork vs fresh, never delegate understanding |

---

## 3. Sub-agent Prompts

### Runnable Patterns
- **AgentTool** (`tools/AgentTool/prompt.ts`): 220+ lines on delegation strategy
- **DEFAULT_AGENT_PROMPT**: "Complete the task fully — don't gold-plate, but don't leave it half-done"
- **Worker output format**: Scope, Result, Key files, Files changed, Issues
- **Coordinator Mode**: Complete system prompt replacement for orchestration
- **SendMessage**: Continue existing workers with synthesized follow-up

### V4 Sub-agent Prompts (v4.3.1)

| Type | Before | After |
|------|--------|-------|
| build | `""` (empty) | "Complete implementation fully. Report: what implemented, files changed, how to test, issues." |
| explore | "Search efficiently. Return file paths and line numbers." | "Structured output: Scope, Result, Key files. Report only what you observe." |
| general | "Complete the task and return a summary." | "Don't gold-plate, don't leave half-done. Structured: Scope, Result, Key files, Issues." |
| review | (35-line checklist — already strong) | Unchanged — already at Runnable quality |
| plan | PLAN_MODE_PROMPT (read-only, 3-line) | Unchanged — adequate for planning |

### What V4 Cannot Do (Architecture Limitations)
- **Coordinator Mode**: Requires two incompatible system prompts + mode switching. Deferred to V4.4.
- **SendMessage**: Requires async message queue between agents. V4's sub-agents run synchronously.
- **Fork Subagent**: Requires byte-identical API prefix. Very high complexity, medium value.

---

## 4. Memory Extraction Prompt

### Runnable (`services/extractMemories/prompts.ts`)
- `buildExtractAutoOnlyPrompt()`: 44 lines
- Limits extraction agent to reading last ~N messages
- Two-step save: write memory file, then update MEMORY.md index
- Explicit WHAT_NOT_TO_SAVE section
- Team vs private scope awareness

### V4 (`_MEMORY_EXTRACT_PROMPT`, line 5695)
- 32 lines, 4-type format: [USER], [FEEDBACK], [PROJECT], [REFERENCE]
- Max 3 items per type
- WHAT_NOT_TO_SAVE section (added V4.2.0 V2-C)
- Parenthetical "(verify still exists)" note for specific references

### Comparison: **V4 is at parity** for single-user use. Missing: team/private scope (not needed for SageMaker).

---

## 5. Compact/Summary Prompt

### Runnable (`services/compact/prompt.ts`)
- 375 lines across 3 prompt variants: BASE, PARTIAL, PARTIAL_UP_TO
- `NO_TOOLS_PREAMBLE`: "You have ZERO tools available. Do NOT attempt tool calls."
- `<analysis>` scratchpad: analysis is drafted then stripped from output
- 9 required sections (identical to V4's)
- `formatCompactSummary()`: strips analysis drafting from output
- Custom instructions support

### V4 (`Compactor.create_summary_prompt()`)
- 38 lines, 9 sections (matches Runnable's required sections)
- **v4.3.1 NEW**: NO_TOOLS preamble added to summary system prompt
- Brief fallback summary for quick compaction (5 preservation points)
- PTL retry with head truncation (V4.2.1)

### Comparison: V4 has the same 9-section structure. Added NO_TOOLS in v4.3.1. Missing: analysis scratchpad stripping (low priority — V4's summary is already clean).

---

## 6. Coordinator Prompt (Runnable Only)

### Runnable (`coordinator/coordinatorMode.ts`, lines 111-369)
This is Runnable's most sophisticated prompt — a complete role swap:

1. **Identity**: "You are an orchestrator, not an executor"
2. **Tools**: Agent, SendMessage, TaskStop
3. **Worker output format**: task-notification XML
4. **Task Workflow**: Research → Synthesis → Implementation → Verification
5. **"Never delegate understanding"**: Synthesize findings yourself before directing
6. **Continue vs spawn**: Decision criteria for reusing workers
7. **Prompt-writing guidance**: "Brief like a smart colleague who just walked in"

### V4 Equivalent
- No coordinator mode (V4.4 future)
- V4.3.1 adds coordination principles directly to SYSTEM_PROMPT:
  - "Never delegate understanding"
  - "Research → Synthesize → Implement → Verify"
  - "Spawn multiple sub-agents in parallel when independent"
- These principles work even without full coordinator mode

---

## 7. Caching Impact of Prompt Changes

### Token Budget Analysis
| Version | System Prompt | System + Tools (est) | Haiku 4.5 Cache | Sonnet 4.5 Cache |
|---------|--------------|---------------------|-----------------|------------------|
| v4.3.0 | ~424 tokens | ~3,565 tokens | INACTIVE (< 4,096) | ACTIVE |
| v4.3.1 | ~700 tokens | ~3,840 tokens | BORDERLINE (test needed) | ACTIVE |
| Target | ~850 tokens | ~4,200 tokens | ACTIVE (> 4,096) | ACTIVE |

### ROI Argument
- Better prompts → fewer wasted tool calls → fewer tokens overall
- If prompt crosses 4,096 threshold → Haiku caching activates → 90% savings on system tokens after turn 1
- Net savings: more prompt tokens up front, but dramatically fewer wasted calls + cache savings per turn

---

## 8. Summary: What V4 Learned from Runnable's Prompts

| Category | Patterns Learned | V4 Status |
|----------|-----------------|-----------|
| System prompt behavioral sections | 6 sections (Doing Tasks, Actions, Output, Git, Tools, Subagent) | ✅ Implemented v4.3.1 |
| Tool descriptions as prompt engineering | WHEN to use, not just WHAT; anti-patterns; constraints | ✅ Implemented v4.3.1 |
| Structured sub-agent output | Scope/Result/Key files/Issues format | ✅ Implemented v4.3.1 |
| NO_TOOLS compact preamble | Prevents hallucinated tool calls in summary | ✅ Implemented v4.3.1 |
| WHAT_NOT_TO_SAVE in memory | Exclude derivable facts from memory | ✅ Implemented v4.2.0 |
| Coordinator mode (full role swap) | Two-prompt orchestration | Deferred V4.4 |
| SendMessage (worker continuation) | Async message queue | Not applicable (sync subagents) |
| Feature-gated sections | Conditional prompts based on state | Not applicable (simpler architecture) |
| Analysis scratchpad stripping | Draft → strip → output | Low priority |

**Conclusion**: V4.3.1 has learned and implemented every prompt pattern from Runnable that is applicable to a Python/SageMaker/Bedrock single-file agent. The remaining patterns (Coordinator Mode, SendMessage, Fork Subagent) require architectural changes deferred to V4.4.

---

*Created: 2026-04-01. See also: PS_LEARNING_JOURNEY.md, PS_DEEP_ANALYSIS_V2.md, PS_DEEP_ANALYSIS_V3.md*
