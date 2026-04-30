# Sub-agent coordination

- `task` for complex (3+ queries OR multi-file). `glob`/`grep` direct for simple (<3 queries).
- Spawn parallel sub-agents when independent (single message, multiple tool calls).
- Never delegate understanding: synthesise findings yourself. Never write "based on findings, fix it."
- Workflow: Research → Synthesise → Implement → Verify.
- `explore` thoroughness: "quick" / "medium" / "very thorough".
- Don't peek at running sub-agent output. Wait for completion. Don't predict mid-wait.
