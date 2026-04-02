# Task B + C Execution Plan for Sonnet

> **Purpose**: Exact instructions for a Sonnet session to complete Task B and Task C.
> **Prerequisites**: Task A is DONE. V4.3.1 pushed (commit 656fb28).
> **Remote**: Push to `sageagent` only (NOT origin).

---

## Task B — HTML Deep Dive + Prompts

### B1: Extract Runnable Prompts (DONE — reference only)
All Runnable prompts have been extracted and documented in:
- `PS_ClaudeCode_Insights/PS_PROMPT_COMPARISON.md` — full side-by-side analysis
- No new extraction needed. Use this doc as source material for the HTML Prompts tab.

### B2: Rebuild RUNNABLE HTML
**File**: `d:/Github/sagemaker-coding-agent/PS_ClaudeCode_Insights/Web_doc/PS_FLOWCHART_RUNNABLE.html`

**Read first**: The existing HTML file to understand current structure.

**Required tabs** (in order):
1. **Architecture** — Full flowcharts of Runnable's architecture:
   - ReAct agent loop (query → tool dispatch → response)
   - Context management (prompt cache boundary, microcompact, autocompact, PTL retry)
   - Sub-agent system (AgentTool → fork/fresh, coordinator mode, SendMessage)
   - Memory system (4 types, extraction, staleness, MEMORY.md index)
   - Tool dispatch (parallel RO tools, tool preference hierarchy)
   Use Mermaid.js flowcharts with dark theme.

2. **Prompts** — NEW TAB. Content from `PS_PROMPT_COMPARISON.md`:
   - System prompt sections breakdown (15+ sections, what each does)
   - Tool description patterns (WHEN not just WHAT)
   - Coordinator mode prompt (full role-swap, 4 workflow phases)
   - Memory extraction prompt (WHAT_NOT_TO_SAVE, 4-type)
   - Compact/summary prompt (NO_TOOLS, 9 sections, analysis scratchpad)
   - Sub-agent prompts (output format, "never delegate understanding")
   Each with beginner-friendly explanation + actual prompt text.

3. **Cross-Compare** — MUST BE IDENTICALLY STRUCTURED to V4.html's Cross-Compare tab:
   - Same sections, same order, same headings
   - For side-by-side viewing in two browser windows
   - Sections: Agent Loop, Context Management, Token Optimization, Sub-agents, Memory, Security, Prompt Engineering
   - Each section: what Runnable does, how it works, strengths/weaknesses

4. **Highlights** — What Runnable does really well:
   - Prompt engineering as competitive moat
   - Coordinator mode (orchestrator vs executor)
   - Memoized prompt assembly (systemPromptSection caching)
   - Tool description depth (90 lines for Bash tool)
   - "Never delegate understanding" principle
   - Feature-gated conditional sections
   - Analysis scratchpad stripping in compact

### B3: Rebuild V4 HTML
**File**: `d:/Github/sagemaker-coding-agent/PS_ClaudeCode_Insights/Web_doc/PS_FLOWCHART_V4.html`

**Read first**: The existing HTML file.

**Required tabs** (in order):
1. **Architecture** — Full flowcharts of V4 architecture:
   - Agent.run() loop (prompt build → Bedrock call → tool dispatch → response)
   - BedrockClient (cache boundary, system/tools formatting, fallback)
   - TokenTracker (cost, budget, cache savings)
   - Compactor (LLM summary, microcompact, PTL retry)
   - Sub-agent system (AGENT_TYPES, depth limiting, parallel execution)
   - Memory system (4 types, extraction, 200-line cap, "already wrote" check)
   - Security (workspace boundary, catastrophic blocks, RO classifier)
   Use Mermaid.js flowcharts with dark theme.

2. **Security** — NEW TAB. List all security features:
   - Workspace boundary enforcement (`_enforce_workspace()`)
   - Path traversal blocking
   - Catastrophic command blocklist (rm -rf /, format, etc.)
   - Read-only command auto-classifier (git status, ls, etc. bypass approval)
   - AWS access tiers (READ/WRITE allowed, DELETE/ADMIN blocked)
   - Sub-agent depth limiting (`CONFIG.subagent_max_depth`)
   - Tool result size cap (50K chars) + disk offload
   - Per-batch aggregate cap (200K)
   - Session cost budget limit
   - Trust boundary (never follow tool output instructions)

3. **Cross-Compare** — IDENTICALLY STRUCTURED to RUNNABLE.html's Cross-Compare tab:
   - Same sections, same order, same headings
   - Sections: Agent Loop, Context Management, Token Optimization, Sub-agents, Memory, Security, Prompt Engineering

4. **What V4 Learned** — Features implemented from Runnable:
   - V4.1: 6 features (cache boundary, catastrophic block, etc.)
   - V4.2: 9 features (tool result caps, WHAT_NOT_TO_SAVE, etc.)
   - V4.3: 6 features (diminishing returns, memory cap, etc.)
   - V4.3.1: Prompt engineering upgrade (4 system prompt sections, 7 tool descriptions, 3 sub-agent prompts)

### B4: Playwright Tests
After rebuilding both HTMLs, run Playwright to verify:
```bash
npx playwright test --config=ps_playwright.config.ts
```
Check:
- All Mermaid charts render and are centered
- Mobile viewport (375px): readable, no horizontal scroll
- Tablet viewport (768px): readable
- No garbled characters or encoding issues
- All tabs clickable and showing correct content

### B5: Codex Review
Run `/codex:rescue` to review:
- HTML UX: garbled chars, chart rendering, mobile compatibility
- Codebase coverage: does the HTML accurately represent ALL agent features?
- Cross-Compare: are both tabs identically structured?

### B-PUSH
After each stage: `git add ... && git commit && git push sageagent master`

---

## Task C — Ship Package

### C1: Security Tab in V4 HTML
Already covered in B3 tab 2. If doing Task C before Task B, create a minimal security tab.

### C2: Update chat.ipynb
**File**: `d:/Github/sagemaker-coding-agent/compact_v4/MAIN/agent/chat.ipynb`

**Read first**: The existing notebook to see its md cell structure.

Add/update markdown cells documenting V4.3.0 + V4.3.1:
- V3-A: Diminishing returns detection (3+ turns <500 output tokens → warning)
- V3-B: Memory 200-line / 25KB cap
- V3-C: Cold-cache microcompact (keepRecent=1)
- V3-D: Auto-memory "already wrote" check
- V3-E: Per-turn cache indicator (WRITE/HIT/INACTIVE)
- V3-F: Cache savings USD in /cost
- P-1: SYSTEM_PROMPT expansion (6 new sections from Runnable)
- P-2: Tool descriptions upgraded (7 tools)
- P-3: Sub-agent structured output format
- P-4: Compact NO_TOOLS preamble
- Bug fix: Empty dynamic system prompt block
- Bug fix: Cache savings model pricing

### C3: Update md companion of chat.ipynb
Find the md companion doc of chat.ipynb (NOT sagemaker_agent.md which is the .py companion).
Search: `glob **/*.md` in compact_v4 for a file that mirrors chat.ipynb content.
Update it to match the updated chat.ipynb.

### C4: Update compact_v4.zip
**File**: `d:/Github/sagemaker-coding-agent/compact_v4/compact_v4.zip`

Contents to include:
```
compact_v4/
  MAIN/
    agent/
      sagemaker_agent.py    (V4.3.1)
      chat.ipynb             (updated in C2)
      USER_GUIDE.md
      TEST_LOG.md
      memory.md              (template)
      skills/
        coding-standards/SKILL.md
        review/SKILL.md
        verify/SKILL.md
        report/SKILL.md (if exists)
  CHANGELOG.md
```
Do NOT include: Power BI skills, Web_doc/, PS_ docs, compare_code/, .git/

Build command:
```bash
cd d:/Github/sagemaker-coding-agent
# Remove old zip
rm compact_v4/compact_v4.zip
# Create new zip
python -c "
import zipfile, os
with zipfile.ZipFile('compact_v4/compact_v4.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    base = 'compact_v4/MAIN/agent'
    for root, dirs, files in os.walk(base):
        # Skip Power BI skills
        if 'powerbi' in root.lower():
            continue
        for f in files:
            if f.endswith(('.py', '.ipynb', '.md')):
                fp = os.path.join(root, f)
                zf.write(fp, fp.replace('compact_v4/', ''))
    zf.write('compact_v4/CHANGELOG.md', 'CHANGELOG.md')
"
```

### C5: Clara Review
**Read these files** in order:
1. `D:\OneDrive - ArcSage\Coding Agent\clara_review_prompts\HOW_TO_USE.md`
2. `D:\OneDrive - ArcSage\Coding Agent\clara_review_prompts\00_CONTEXT.md`
3. `D:\OneDrive - ArcSage\Coding Agent\clara_review_prompts\01_DISCOVERY.md`
4. `D:\OneDrive - ArcSage\Coding Agent\clara_review_prompts\02_COMPONENT1.md`
5. `D:\OneDrive - ArcSage\Coding Agent\clara_review_prompts\03_COMPONENT2_3.md`
6. `D:\OneDrive - ArcSage\Coding Agent\clara_review_prompts\04_PROD_READINESS.md`
7. `D:\OneDrive - ArcSage\Coding Agent\clara_review_prompts\05_SYNTHESIS.md`
8. `D:\OneDrive - ArcSage\Coding Agent\clara_review_prompts\AGENT_BUGS.md`
9. `D:\OneDrive - ArcSage\Coding Agent\Clara Research\agent_frameworks_retrac.md`
10. `D:\OneDrive - ArcSage\Coding Agent\Clara Research\retrac_langgraph.py`

**Review criteria**:
a) Are all prompts clear enough for Haiku 4.5? (short sentences, explicit instructions, no ambiguity)
b) Can V4 run these prompts? Check:
   - Does V4 have the tools needed (read_file, glob, grep, bash for git)?
   - Are the prompts compatible with V4's system prompt and tool names?
   - Can V4's sub-agent system handle the multi-section structure?
c) Can we create Clara-specific skills?
   - Read existing skills in `compact_v4/MAIN/agent/skills/` for the SKILL.md format
   - Create `compact_v4/MAIN/agent/skills/clara/` with skill files for each Clara section

### C6: Ship Method Research
Research: what is the safest way to transfer files to a company SageMaker instance via Microsoft Teams?
Options to evaluate:
1. Teams chat file attachment (zip)
2. Teams channel file upload
3. OneDrive/SharePoint shared link
4. Direct SageMaker notebook upload via browser

Consider: IT audit visibility, file size limits, retention policies, DLP scanning.
Recommend the safest method.

### C7: Ship List + Confidence
Produce a table:

| File | Purpose | Size | Ship? |
|------|---------|------|-------|
| sagemaker_agent.py | Core agent V4.3.1 | ~8.5K lines | YES |
| chat.ipynb | Jupyter entry point | Updated in C2 | YES |
| USER_GUIDE.md | User documentation | Existing | YES |
| TEST_LOG.md | Test evidence | 17 tests | YES |
| CHANGELOG.md | Version history | V4.0→4.3.1 | YES |
| memory.md | Memory template | Empty template | YES |
| skills/ | Skill definitions | 5+ skills | YES |
| compact_v4.zip | Complete package | All above | YES |

**Confidence %**: Based on TEST_LOG.md facts:
- Code quality: 17/17 tests pass, Codex reviewed, 2 bugs found and fixed
- Feature completeness: 22 features from Runnable implemented
- Prompt quality: V4.3.1 prompt upgrade from Runnable patterns verified on Bedrock
- Edge cases: FILE_UNCHANGED_STUB, path traversal, depth limits, diminishing returns all tested

**Ready to use %**: What works vs what needs user setup:
- Works immediately: All coding tasks, tool usage, sub-agents, memory, context management
- Needs user config: AWS credentials, model selection in CONFIG, workspace path
- Not included: Power BI skills (separate delivery), Clara skills (C5)

---

## Execution Order

**Recommended**: C2 → C3 → C4 → C5 → C6 → C7 → B2 → B3 → B4 → B5 → Push

**Rationale**: Task C (ship package) is more urgent. Task B (HTML deep dive) is for learning/documentation. Do C first so the package is ready to ship, then enhance docs.

---

*Created: 2026-04-01 by Claude Opus 4.6 session.*
