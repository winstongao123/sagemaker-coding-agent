# Sub-agent coordination

- `task` for complex (3+ queries OR multi-file). `glob`/`grep` direct for simple.
- If the user explicitly asks for a worker, reviewer, verifier, helper,
  subagent, or saved reviewer evidence, you MUST call the `task` tool for
  that role. Manually writing a `docs/reviews/*.md` file is not a substitute
  for a real subagent/reviewer run.
- After each `task` result, preserve the returned `[subagent_artifacts]` or
  `[subagent_result_envelope]` paths in the project review/status docs before
  claiming done.
- Spawn parallel sub-agents when independent (single message, multiple tool calls).
- Never delegate understanding: synthesise findings yourself.
- Workflow: Research → Synthesise → Implement → Verify.
- `explore` thoroughness: "quick" / "medium" / "very thorough".
- Don't peek at running sub-agent output. Don't predict mid-wait.
