# Long-running status — AGENT_STATUS.md

For multi-phase / long-running work, maintain `AGENT_STATUS.md` as durable handoff.

Use `todo_write` for the lightweight live checklist. Use `task_create`,
`task_update`, and `task_list` for durable request tracking with IDs, owners,
dependencies, notes, and evidence paths. Use `AGENT_STATUS.md` for cross-session
handoff: Goal, Standing Instructions, Plan, Progress, Blockers, Files Changed,
Verification, Next Step.

Update on priority changes, after major phases, before stopping. Concise + factual. Keep next step obvious.
