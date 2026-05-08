# Block G Decisions

Date: 2026-05-05

## G-1/G-2 Deferral Superseded

Historical PORT_LOG #090 deferred per-agent memory prompt/path checks to Block H. The completion audit treats canonical Block G rows as ship-blocking unless implemented or explicitly user-dispositioned, so this pass ships the small Block G-owned surface directly:

- `load_agent_memory_prompt()` reads scoped per-agent `MEMORY.md`.
- `is_agent_memory_path()` uses normalized absolute paths plus `commonpath`.
- `review` agents opt into project-scoped memory through `AgentType.memory_scope`.
- `spawn_subagent()` appends memory prompt text best-effort.

Block H remains responsible for session memory extraction and dream/consolidation workflows.

## No New Project Commands

Decision: Do not add `/project-*` commands. Block G changes stay inside subagent role/prompt/runtime helpers.

## AWS/R-tier Boundary

Decision: No AWS/R-tier spend. Block G validation is zero-cost local tests plus Claude read-only review.

## Fork Runtime Wiring Advisory

Claude iter1 noted that ADR-033 still treats `agent_type="fork"` cache-prefix runtime wiring as outside the G helper scope. This is not a Block G blocker because canonical G-8 says the fork replay helper is already the Block G2 planned slice, and that helper/test evidence exists. Track runtime fork-spawn cache-prefix behavior as pre-AWS hardening evidence for the G2/L/final review path.
