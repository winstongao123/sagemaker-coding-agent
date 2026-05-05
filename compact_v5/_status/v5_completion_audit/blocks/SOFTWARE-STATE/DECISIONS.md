# SOFTWARE-STATE Decisions

Status: CLOSED_READY_FOR_GIT_CHECKPOINT
Date: 2026-05-05

Decisions:

- Use a small workspace-local `.sageagent_state/` directory for durable todos,
  turn journal, and last-turn recovery metadata.
- Keep writes atomic for JSON recovery records so interrupted saves do not
  corrupt the only copy.
- Preserve `Session.todos` and add session metadata for status/memory context
  rather than overwriting `AGENT_STATUS.md` or `memory.md` on resume.
- Refresh `AGENT_STATUS.md` and `memory.md` on every top-level `Agent.run()`
  when the default system prompt is used.
- Allow the prompt-cache invariant to update for fresh status/memory dynamic
  context because this block explicitly requires current state before turns.
- Wire memory extraction through `/save` only when
  `CONFIG.enable_memory_extraction=True`; the default path remains zero-cost.
- Track Claude's non-blocking note that future per-turn toolset injection
  should revisit whether `prompt_cache_now=True` needs narrowing; no current
  SOFTWARE-STATE blocker because the code path only refreshes state context.

Boundaries:

- `SOFTWARE-CHECKPOINT` owns durable named checkpoint indexes and safe restore.
- `SOFTWARE-GATE` owns blocking done/verify requirements.
- `SOFTWARE-COMPACT-TELEMETRY` owns typed compaction evidence and cache metrics.
