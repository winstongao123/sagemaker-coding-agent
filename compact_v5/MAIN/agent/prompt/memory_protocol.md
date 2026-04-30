# Memory — memory.md

`write_file` to `memory.md` for cross-session context. Auto-loaded on agent start.

4 typed sections:
- `## USER` — role, expertise, preferences
- `## FEEDBACK` — what to repeat / avoid (one-line *why*)
- `## PROJECT` — goals, decisions, current state
- `## REFERENCE` — external pointers (URLs, paths, docs)

Save DECISIONS / PATTERNS, not ephemeral state. Don't save: code patterns (read from code), git history (`git log` is authoritative), fix recipes (the fix is in the code).
