# Agent Status (long-running task handoff)

This file is loaded into the dynamic tail of the system prompt and
serves as a long-running context handoff between sessions.

Use it to record:
- Current task goal
- Sub-tasks already completed
- Sub-tasks still pending
- Key file paths edited so far
- Anything the next session would otherwise have to re-discover

The agent will read this file at the start of each session.

---

(no active session)
