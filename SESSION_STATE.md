# SESSION STATE — sagemaker-coding-agent

## Last Session: 2026-04-13 — PS_Deep E-Book Creation

### What Changed
- **NEW: PS_ClaudeCode_Insights/PS_Deep/** — Complete deep-dive of Claude Code Runnable codebase
  - `PS_DEEP_DIVE_RUNNABLE.html` — 10-chapter standalone e-book (992 lines)
    - Left sidebar navigation + right content with What/Why/How/Key Learning boxes
    - 20+ Mermaid flowcharts covering every subsystem
    - Focus: Agentic Design (Ch.2) + Harness Engineering (Ch.3)
    - Teaching angle: "How to build similar systems" for any domain
  - 8 research markdown docs from parallel agent deep-dive of 2,010 TS files:
    - research_core_architecture.md (310 lines)
    - research_agent_coordination.md (350 lines) — coordinator, tasks, swarm, fork
    - research_tool_system.md (206 lines) — 60+ tools, YOLO classifier
    - research_memory_context.md (191 lines) — query engine 18K lines, compaction
    - research_hooks_plugins.md (216 lines) — 25 hooks, plugins, bridge, SDK
    - research_prompts_llm.md (194 lines) — all system prompts, prompt engineering
    - research_cli_commands.md (126 lines) — 90+ commands, skills, keybindings
    - research_remote_advanced.md (105 lines) — CCR, SSH, proxy

- **UPDATED: PS_FLOWCHART_RUNNABLE.html**
  - Stats corrected: 2,010 files (was 1,438), 60+ tools (was 58), 25 hooks (was 24), 90+ commands (was 112)
  - Sub-agent section expanded with coordinator mode, fork subagent, in-process teammates
  - Link to PS_Deep e-book added

- **UPDATED: PS_FLOWCHART_V4.html**
  - Added "2b. Runnable's Full Agent Architecture" section with 7-row comparison table
  - Gap analysis: V4 vs Runnable on task types, coordinator, fork, teammate isolation, spawning backends

### Key Findings from Deep Dive
- Runnable has 7 task types (not just "subagents")
- Coordinator mode has a 400+ line system prompt with synthesis protocol
- Fork subagent uses FORK_PLACEHOLDER_RESULT for near-100% cache hits
- In-process teammates use AsyncLocalStorage for isolation
- Query engine (query.ts) is 18,623 lines — the largest single file
- BashTool is 161KB — the most complex tool
- YOLO classifier is two-stage: Fast (50ms XML) → Thinking (256+ token CoT)

### To Resume
- PS_Deep e-book is complete and Playwright-verified
- Consider enhancing VS_LANGGRAPH.html with new findings
- Consider adding more content to e-book (remote execution chapter is lighter)
