# Sub-agent coordination

- `task` for complex (3+ queries OR multi-file). `glob`/`grep` direct for simple.
- Spawn parallel sub-agents when independent (single message, multiple tool calls).
- Never delegate understanding: synthesise findings yourself.
- Workflow: Research → Synthesise → Implement → Verify.
- `explore` thoroughness: "quick" / "medium" / "very thorough".
- Don't peek at running sub-agent output. Don't predict mid-wait.
