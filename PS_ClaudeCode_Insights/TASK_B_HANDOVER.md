# Task B — HTML Deep Dive Handover for Sonnet

> **Created by**: Claude Opus 4.6 session (Task A + Task C complete)
> **For**: Sonnet session to execute Task B
> **Date**: 2026-04-02
> **Git state**: Commit `a8d090f` pushed to `sageagent`
> **Push to**: `sageagent` remote ONLY (NOT origin)

---

## GOAL

Create two HTML files that let a **beginner** fully understand both codebases **without reading any code**. Side-by-side comparison in two browser windows. Every architecture flow, every prompt pattern, every engineering decision — captured in flowcharts and beginner-friendly explanations.

---

## CRITICAL RULES

1. **Push to `sageagent` remote only** — `git push sageagent master`
2. **After each stage**: update docs, push git
3. **Use Codex** (`/codex:rescue`) to review at each stage
4. **Playwright tests** after HTML changes: `npx playwright test --config=ps_playwright.config.ts`
5. **Both HTMLs must have identically-structured Cross-Compare tabs** — same sections, same order, same headings — for side-by-side viewing
6. **No missed architecture** — every agentic design pattern must be in the HTML

---

## FILES TO CREATE/UPDATE

### 1. RUNNABLE HTML
**File**: `d:/Github/sagemaker-coding-agent/PS_ClaudeCode_Insights/Web_doc/PS_FLOWCHART_RUNNABLE.html`

### 2. V4 HTML
**File**: `d:/Github/sagemaker-coding-agent/PS_ClaudeCode_Insights/Web_doc/PS_FLOWCHART_V4.html`

---

## READ THESE FILES FIRST (in order)

These contain ALL the research and analysis already done:

1. `d:/Github/sagemaker-coding-agent/PS_ClaudeCode_Insights/PS_DEEP_ANALYSIS_V2.md` — V2 audit (586 lines, 10 features extracted)
2. `d:/Github/sagemaker-coding-agent/PS_ClaudeCode_Insights/PS_DEEP_ANALYSIS_V3.md` — V3 audit (226 lines, 6 features extracted)
3. `d:/Github/sagemaker-coding-agent/PS_ClaudeCode_Insights/PS_PROMPT_COMPARISON.md` — Full prompt extraction (Runnable vs V4 side-by-side)
4. `d:/Github/sagemaker-coding-agent/PS_ClaudeCode_Insights/PS_LEARNING_JOURNEY.md` — Complete learning record (what was learned, implemented, skipped)
5. `d:/Github/sagemaker-coding-agent/compact_v4/MAIN/agent/sagemaker_agent.py` — V4 source (v4.3.1, ~8500 lines)
6. `d:/Github/sagemaker-coding-agent/compact_v4/CHANGELOG.md` — V4 version history
7. `d:/Github/sagemaker-coding-agent/compact_v4/MAIN/agent/TEST_LOG.md` — 22 Bedrock tests

For Runnable codebase reference (TypeScript, 1,438 files):
8. `d:/Github/sagemaker-coding-agent/PS_ClaudeCode_Insights/` — all PS_ files contain extracted analysis
9. The Runnable source was in `gg-claude-code-runnable/src/` but may not be available. Use the PS_ docs as your source — they contain all extracted findings.

---

## TAB STRUCTURE — BOTH HTMLs MUST MATCH

### RUNNABLE HTML — 5 tabs

| Tab | Content |
|-----|---------|
| **1. Architecture** | Full flowcharts (Mermaid.js, dark theme) |
| **2. Prompts** | All prompt patterns extracted and explained |
| **3. Cross-Compare** | Identically structured to V4's Cross-Compare tab |
| **4. Highlights** | What Runnable does really well |
| **5. Details** | Deep dive: token flows, caching mechanics, security model |

### V4 HTML — 5 tabs

| Tab | Content |
|-----|---------|
| **1. Architecture** | Full flowcharts (Mermaid.js, dark theme) |
| **2. Security** | All 16 security layers with flowcharts |
| **3. Cross-Compare** | Identically structured to Runnable's Cross-Compare tab |
| **4. What V4 Learned** | Features implemented from Runnable (V4.1→4.3.1) |
| **5. Details** | Deep dive: Bedrock integration, caching, cost tracking |

---

## TAB 1: ARCHITECTURE — Required Flowcharts

Both HTMLs need these flowcharts. Use Mermaid.js with dark theme. Each flowchart must have:
- Beginner-friendly title
- 2-3 sentence explanation ABOVE the chart
- Labels on every arrow
- Color coding: green=happy path, orange=fallback, red=error

### Flowcharts for RUNNABLE Architecture tab:

1. **ReAct Agent Loop** — query → LLM call → tool dispatch → tool execution → result back to LLM → response or next tool
2. **Context Management Pipeline** — prompt cache boundary → microcompact → autocompact → PTL retry → snip boundaries
3. **Sub-agent System** — AgentTool → decision (fork vs fresh) → worker execution → output format → coordinator synthesis → SendMessage
4. **Memory System** — 4 types → extraction prompt → WHAT_NOT_TO_SAVE filter → staleness check → MEMORY.md index → 200-line cap
5. **Tool Dispatch** — user message → tool selection → parallel RO classification → approval check → execution → result size cap → disk offload
6. **Prompt Assembly** — systemPromptSection cache → conditional sections (MCP, coordinator) → feature flags → static/dynamic split → cache_control blocks
7. **Compact/Summary Flow** — context usage check → prune strategy (keep_n) → LLM summary (NO_TOOLS) → analysis scratchpad strip → resume

### Flowcharts for V4 Architecture tab:

1. **Agent.run() Loop** — prompt build → BedrockClient.call() → response parse → tool dispatch → approval → execution → next turn or done
2. **BedrockClient** — system prompt (static) → cache boundary → tools array → dynamic messages → Bedrock InvokeModel → response parse → token tracking
3. **TokenTracker** — per-turn tracking → cache_read/write detection → cost calculation → model-aware pricing → budget check → /cost display
4. **Compactor** — should_compact check → prune_tool_outputs (keep recent) → LLM summary (zero-tool mode) → PTL retry (3 attempts) → microcompact (cold cache)
5. **Sub-agent System** — AGENT_TYPES → tool subset → depth limit check → context isolation (save/clear/restore) → structured output (Scope/Result/Files/Issues)
6. **Memory System** — 4 types → extraction prompt → WHAT_NOT_TO_SAVE → "already wrote" guard → 200-line/25KB cap → memory.md
7. **Security Layers** — workspace boundary → path traversal check → catastrophic block → RO classifier → bash allowlist → python AST → AWS bedrock-only → approval dialog → cost limit
8. **File Operations Flow** — read_file → FILE_CACHE check → FILE_UNCHANGED_STUB → content delivery → write_file → cache update → edit_file → exact match

---

## TAB 2: PROMPTS (Runnable) / SECURITY (V4)

### Runnable Prompts Tab — Content from PS_PROMPT_COMPARISON.md:

For EACH prompt type, show:
- **What it is** (1-2 sentences, beginner level)
- **Why it matters** (what goes wrong without it)
- **Actual prompt text** (in a code block, key sections highlighted)
- **Engineering lesson** (what V4 learned from this)

Prompt types to cover:
1. **System Prompt** — 15+ sections, what each does, how they shape behavior
2. **Tool Descriptions** — WHEN not just WHAT pattern, 7 key tools, anti-patterns
3. **Coordinator Mode** — complete role-swap prompt, 4 workflow phases, "parallelism is your superpower"
4. **Memory Extraction** — WHAT_NOT_TO_SAVE, 4-type structure, staleness
5. **Compact/Summary** — NO_TOOLS preamble, 9 sections to preserve, analysis scratchpad
6. **Sub-agent Prompts** — worker output format (Scope/Result/Files/Issues), "never delegate understanding"
7. **Bash Tool Description** — 90 lines, the most detailed tool description, shows pattern

### V4 Security Tab — All 16 layers:

For EACH layer, show:
- **What it blocks** (with example)
- **How it works** (code mechanism: regex, AST, allowlist, etc.)
- **Flowchart** where applicable
- **Why it matters in SageMaker** (shared infrastructure context)

Security layers:
1. Workspace boundary enforcement (`_enforce_workspace()`)
2. Path traversal blocking (symlink resolution)
3. Catastrophic command blocklist (rm -rf /, format, mkfs, etc.)
4. Bash command allowlist (70 allowed commands)
5. Bash dangerous pattern blocklist (75 patterns)
6. Python regex validation (63 patterns)
7. Python AST import validation (67 allowed modules)
8. Python runtime sandbox (open/remove intercepted)
9. AWS bedrock-only enforcement (regex + AST + getattr)
10. Read-only command auto-classifier (bypass approval)
11. Tool approval dialog (user sees exact command)
12. Sub-agent depth limiting (CONFIG.subagent_max_depth)
13. Tool result size cap (50K chars per tool)
14. Per-batch aggregate cap (200K chars)
15. Session cost budget limit
16. Trust boundary (never follow tool output instructions)

---

## TAB 3: CROSS-COMPARE — MUST BE IDENTICAL STRUCTURE

Both HTMLs must have these exact sections in this exact order:

### Section 1: Agent Loop
- How messages flow through the system
- Tool dispatch mechanism
- Turn management
- Stop conditions

### Section 2: Context Management
- When and how context is compressed
- Pruning strategies
- Cache boundary design
- Token estimation

### Section 3: Token Optimization
- Prompt caching (how, when, savings)
- FILE_UNCHANGED_STUB
- Tool result caps
- Lazy tool loading
- Microcompact

### Section 4: Sub-agents
- Types and capabilities
- Spawning mechanism
- Context isolation
- Output format
- Depth limiting
- Parallel execution

### Section 5: Memory
- 4-type system
- Extraction prompt
- WHAT_NOT_TO_SAVE
- Staleness / caps
- "Already wrote" guard

### Section 6: Security
- Workspace enforcement
- Command validation
- AWS access control
- Approval flow

### Section 7: Prompt Engineering
- System prompt structure
- Tool description patterns
- Conditional sections
- Compact/summary prompts

For EACH section in EACH HTML:
- **How [Runnable/V4] does it** (2-3 paragraphs)
- **Key files/functions** (with brief descriptions)
- **Strengths** (what works well)
- **Limitations** (what could be better)
- **Beginner explanation** (in simple terms, what this means)

---

## TAB 4: HIGHLIGHTS (Runnable) / WHAT V4 LEARNED (V4)

### Runnable Highlights:
1. Prompt engineering as competitive moat (900+ line system prompt)
2. Coordinator mode (complete role-swap, orchestrator vs executor)
3. Memoized prompt assembly (systemPromptSection caching)
4. Tool description depth (90 lines for Bash tool alone)
5. "Never delegate understanding" principle
6. Feature-gated conditional sections (MCP, coordinator, IDE)
7. Analysis scratchpad stripping in compact
8. Fork subagent (byte-identical API prefix)
9. Position-pinned cache edits
10. Speculative bash classifier (LLM-based permission)

### What V4 Learned (organized by version):
- **V4.1.0**: Cache boundary, catastrophic blocks, RO classifier, 4-type memory, extraction prompt
- **V4.2.0**: Tool result caps (50K/200K), WHAT_NOT_TO_SAVE, cold-cache microcompact, 4/3 padding
- **V4.2.1**: FILE_UNCHANGED_STUB, parallel RO tools, PTL retry
- **V4.3.0**: Diminishing returns, memory 200-line cap, cold-cache keepRecent=1, auto-memory guard, cache indicator
- **V4.3.1**: 6 system prompt sections, 7 tool descriptions, sub-agent structured output, compact zero-tool mode
- **NOT implemented** (and why): Coordinator mode, SendMessage, Fork subagent, position-pinned cache, reactive compact, LLM bash classifier

---

## TAB 5: DETAILS

### Runnable Details tab:
- Token flow diagram (input → cache boundary → cached vs uncached → output → cost)
- Mermaid sequence diagram: full API call lifecycle
- Tool registration system (how tools are defined, loaded, cached)
- How coordinator mode switches system prompts
- How snip boundaries work
- Lazy tool loading mechanism

### V4 Details tab:
- Bedrock API integration (InvokeModel, message format, system/tools/messages)
- Cache mechanics (cache_control blocks, TTL, Haiku vs Sonnet thresholds)
- Cost tracking flow (TokenTracker → per-model pricing → cache savings → /cost display)
- Skill system (SKILL.md format, loading, persistence, clearing)
- Custom commands (template expansion, $ARGUMENTS, agent delegation)
- Clara review workflow (5-phase, component selection, output files)

---

## HTML TECHNICAL REQUIREMENTS

1. **Mermaid.js** for all flowcharts — use CDN: `<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>`
2. **Dark theme** — dark background (#1e1e1e), light text (#d4d4d4), colored nodes
3. **Charts centered** — CSS `text-align: center` on mermaid containers
4. **Mobile responsive** — readable at 375px (phone) and 768px (tablet), no horizontal scroll
5. **Tab navigation** — JavaScript tab switching, active tab highlighted
6. **No garbled characters** — use UTF-8 encoding, avoid special Unicode arrows (use `->` not `→`)
7. **Code blocks** — syntax highlighted, dark background, monospace font
8. **Beginner callouts** — use colored boxes for "In simple terms..." explanations
9. **Each section collapsible** — `<details><summary>` for long sections

---

## PLAYWRIGHT TESTS

After building both HTMLs, run:
```bash
npx playwright test --config=ps_playwright.config.ts
```

Check:
- [ ] All Mermaid charts render (no error boxes)
- [ ] Charts are centered (not left-aligned)
- [ ] Mobile viewport (375px): readable, no horizontal scroll
- [ ] Tablet viewport (768px): readable
- [ ] No garbled characters or encoding issues
- [ ] All tabs clickable and showing correct content
- [ ] Both Cross-Compare tabs have identical section count and order

If `ps_playwright.config.ts` doesn't exist, create it:
```typescript
import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './PS_ClaudeCode_Insights/Web_doc/',
  use: { baseURL: 'file://' },
});
```

---

## CODEX REVIEW (at each stage)

Run `/codex:rescue` after completing each tab to check:
1. **UX**: garbled chars, chart rendering, mobile compatibility
2. **Coverage**: does the HTML accurately represent ALL agent features from the codebase?
3. **Cross-Compare alignment**: are both tabs identically structured?
4. **Accuracy**: do flowcharts match actual code behavior?

---

## EXECUTION ORDER

1. Read all PS_ docs listed above (understand what's already analyzed)
2. Build RUNNABLE HTML Tab 1 (Architecture flowcharts)
3. Build V4 HTML Tab 1 (Architecture flowcharts)
4. Playwright test both
5. Build RUNNABLE Tab 2 (Prompts) + V4 Tab 2 (Security)
6. Build Cross-Compare tabs (both at same time to ensure alignment)
7. Build remaining tabs
8. Playwright test all
9. Codex review
10. Push: `git add PS_ClaudeCode_Insights/Web_doc/ && git commit && git push sageagent master`

---

## WHAT "FULLY UNDERSTAND WITHOUT READING CODE" MEANS

For every concept, provide THREE levels:
1. **One-line summary** — what it does in plain English
2. **How it works** — mechanism, with flowchart
3. **Why it matters** — what goes wrong without it, real example

If a beginner reads both HTMLs side by side, they should be able to:
- Explain how a ReAct agent loop works
- Describe how prompt caching saves money
- Compare how Runnable vs V4 handle sub-agents
- Understand why certain architectural decisions were made
- Know what Runnable does that V4 doesn't (and why)
- Appreciate prompt engineering as an engineering discipline

---

## GIT REMINDERS

```bash
# After each stage:
cd d:/Github/sagemaker-coding-agent
git add PS_ClaudeCode_Insights/Web_doc/
git commit -m "html: [description of what was added]"
git push sageagent master
```

Never push to `origin`. Always `sageagent`.

---

*Created: 2026-04-02 by Claude Opus 4.6 session. Task A complete (100%), Task C complete (shipped). This handover is for Task B only.*
