# Team 1, Agent B — Non-UI parity audit (v4 vs v5)

**Status**: SUMMARY ONLY — Explore agent could not write files, returned content in agent summary. Re-spawn with general-purpose agent recommended for full multi-section detail.

## Summary returned by agent

v5 shipped as feature-narrowed MVP instead of v4 parity. Of 26 audit items, v5 has:

### MISSING (8)
- `Compactor` (microcompact + context_collapse + 2-stage smart compact)
- `TokenTracker` / `TOKENS` singleton + session_cost runtime
- `max_exec_calls_per_session=200` enforcement (config value present, no enforcement gate)
- `_extract_and_append_memories` (config flag only)
- `/save` / `/load` / `/cost` / `/status` slash commands
- AGENT_TYPES registry (plan/build/explore/verify)
- `SnapshotManager` runtime singleton wiring
- `AuditLogger` runtime singleton wiring

### PARTIAL (6)
- `_extract_and_append_memories` (config only)
- Cold-cache detection (no trigger)
- `/compact` button
- Plan-mode allowlist (present but never tested end-to-end)
- Skill name resolution (BROKEN: `clara` → `clara-review` mismatch)
- `_turn_output_tokens` (not tracked)

### PRESENT (12)
- `enable_skill_auto_trigger` config
- session cost tracking config (value only)
- tool deny patterns
- `max_exec_calls` config value
- `_RECENT_DIFFS` comments (not used)
- ChatUI send/stop/clear
- QueryEngine loop
- worktree isolation framework (config flag only)
- Plus the rest of Phase 1-11 ports

### High-severity user-visible gaps
- No cost persistence across sessions
- No compaction (PS#3 regression ~$0.02/30min idle)
- Skill activation fails on name mismatch (PS#7 regression)

## Note for synthesis

This summary is sufficient for the priority list, but the FULL multi-section report (with v4 line citations and v5 file paths for every audit item) was not generated because the Explore agent type lacks the Write tool. Re-run with general-purpose agent type if granular file:line citations are needed for the v5.0.1 implementation plan.
