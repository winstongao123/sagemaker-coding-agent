# Phase 2 Wave 2: Runnable Tool Implementation Audit

## Executive Summary

Runnable v8 tools are heavily rewritten from v5, with substantial behavioral changes:
- **AgentTool**: Fork semantics added (context inheritance, cache replay). Architecture shifts from simple spawn to complex multi-mode.
- **BashTool**: Largely preserved; prompt expanded with git skills, undercover mode, background tasks.
- **FileReadTool/FileEditTool/FileWriteTool**: Prompt guidance expanded significantly. Editor UX refinements.
- **GlobTool/GrepTool**: Prompts simplified (reference external agents). Executors stable.
- **NotebookEditTool**: New tool in Runnable (not in v5).

**Critical Lost Behaviors**: Fork caching and memory snapshot logic is Runnable-specific. Most other behaviors recoverable via code audit.

---

## Per-Tool Analysis Table

| Tool | Runnable File | Key Behaviors | v5 Equiv | Lost in v5 | Effort | Arch |
|------|---|---|---|---|---|---|
| **AgentTool** | prompt.ts, runAgent.ts, forkSubagent.ts, agentMemory.ts | Fork mode (context inherit), cache replay, memory snapshots, MCP servers, skill preload | subagent/spawn.py (simple) | Fork caching, fork-child rules, MCP+skill, snapshot logic | HIGH | v8-only |
| **BashTool** | prompt.ts, destructiveCommandWarning.ts | Git skills (ant-only), undercover, background tasks, sandbox detection | bash.py + git.py | Ant features, git wrapper, permission scoping | MEDIUM | Separable |
| **FileReadTool** | FileReadTool.ts, prompt.ts | Image/PDF/notebook, screenshot path resolution, blocked devices | file_read.py | Multimodal details, screenshot hacks, token estimation | MEDIUM | Feature-additive |
| **FileEditTool** | FileEditTool.ts, prompt.ts | Pre-read check, team-mem guard, git diff, file history | edit.py | Pre-read enforcement, team-mem, history tracking | MEDIUM | Integration-heavy |
| **FileWriteTool** | FileWriteTool.ts, prompt.ts | Pre-read for existing, mkdir on write, skill discovery | write.py | Pre-read warning, skill activation | EASY | Separable |
| **GlobTool** | GlobTool.ts, prompt.ts | Fast glob, 100-file truncation, agent dispatch hint | glob_tool.py | Behavior unchanged; prompt narrowed | TRIVIAL | Stable |
| **GrepTool** | GrepTool.ts, prompt.ts | Ripgrep wrapper, output modes, context, filtering | grep_tool.py | Behavior unchanged; prompt simplified | TRIVIAL | Stable |
| **NotebookEditTool** | NotebookEditTool.ts, prompt.ts | Cell-level edit (insert/delete/replace) | N/A | N/A | EASY | New |
| **SkillTool** | MCPTool variant | Listing budget, char truncation, bundled priority | skill_loader.py | Discovery, freshness, plugin namespace | MEDIUM | Integrable |

---

## AgentTool: Largest Delta

**Runnable additions** (forkSubagent.ts, lines 172–195):
- Fork child non-negotiable rules (no meta-commentary, tools only, commit before report).
- Scope/Result/Key files/Files changed/Issues structured output format.
- `buildChildMessage()` constructs boilerplate with `FORK_BOILERPLATE_TAG`.

**runAgent.ts architecture**:
- Lines 375–379: Fork message filtering (`filterIncompleteToolCalls`).
- Lines 648–657: Initialize agent-specific MCP servers.
- Lines 577–646: Skill preload from agent frontmatter.
- Line 715: `preserveToolUseResults` for transcript visibility.

**agentMemory.ts scope system**:
- User scope: `~/.claude/agent-memory/<agentType>/MEMORY.md`
- Project scope: `.claude/agent-memory/<agentType>/MEMORY.md`
- Local scope: `.claude/agent-memory-local/<agentType>/MEMORY.md` (not in VCS)
- buildMemoryPrompt() injects scope-aware guidelines.

**v5 equivalent**: subagent/spawn.py (~40 lines, simple fork + optional memory).

**Restoration effort**: Fork rules + memory scopes need directory structure + MEMORY.md generator. Cache replay is Runnable-specific and optional.

---

## BashTool: Conditional Git Integration

**prompt.ts lines 42–75**:
- Ant-internal: Reference `/commit` + `/commit-push-pr` skills (lines 57–66).
- External: Full inline git safety protocol (88 lines of detailed rules).
- All: Undercover mode instructions (keep internal codenamesSecret).
- Background tasks note (lines 35–40).

**v5**: Single inline protocol, no skill dispatch.

**Lost**: Skill integration, ant-internal safety.

**Restoration**: Conditional git instructions based on USER_TYPE + ant vs. external.

---

## FileTools: Prompt Expansion, Integration Hooks

**FileReadTool.ts**:
- Lines 96–128: BLOCKED_DEVICE_PATHS (device file guards).
- Lines 147–150: Screenshot space resolution (macOS thin-space U+202F).
- Image processing (compress, downsample, metadata).
- Token estimation integration.

**FileEditTool.ts**:
- Lines 137–151: validateInput checks readFileState for pre-read.
- Team-mem secret guard (line 144).
- Git diff tracking (line 41).
- LSP diagnostic clearing (line 6).

**FileWriteTool.ts**:
- Pre-read warning for existing files.
- Skill activation on write (discoverSkillDirsForPaths).

**Algorithms**: Unchanged from v5. Integration points are v8-specific (readFileState, team-mem, LSP).

---

## GlobTool / GrepTool: Prompt-Only Deltas

**Runnable prompts**: Minimal (7 lines Glob, 18 lines Grep). Delegate to Agent for open-ended searches.

**v5 prompts**: ~50+ lines each, detailed feature docs.

**Lost**: Inline feature documentation.

**Restoration**: Paste v5 prompts directly.

---

## Restoration Priority

| Phase | Task | Effort |
|-------|------|--------|
| 2.5 | Fork child rules + memory dir structure | LOW |
| 2.5 | GlobTool/GrepTool full prompts | EASY |
| 3 | Agent memory persistence (buildMemoryPrompt) | MEDIUM |
| 3 | Git safety protocol checks | EASY |
| 4 (opt) | MCP server integration in agents | HIGH |
| 4 (opt) | Skill preload in agent frontmatter | MEDIUM |

---

*Report generated 2026-04-30 — Phase 2 Wave 2 Analysis*
