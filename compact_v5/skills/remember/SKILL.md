---
name: remember
description: Use when the user wants to capture a learning into CLAUDE.md / CLAUDE.local.md so future sessions remember it. Runs a 4-step review: scope, fit, draft, append.
disable_model_invocation: true
auto_trigger: false
---

# Remember (Manual Memory Capture)

The user has asked you to remember something across sessions. This skill
writes that knowledge into the workspace's `CLAUDE.md` (project-wide) or
`CLAUDE.local.md` (private, gitignored), depending on what the
information is.

This skill is **user-invocable only** (`disable_model_invocation: true`):
the model never auto-triggers it; the user must explicitly run
`/skill use remember`. Memory is a deliberate write, not an inference.

## Procedure (4 rounds)

### Round 1 — Scope
What is the user asking you to remember? Distill to ONE sentence the
core fact, decision, or preference. If the user gave a long story, the
remembered fact is usually one specific clause. Ask if unclear.

### Round 2 — Fit
Decide where the memory belongs:
- **CLAUDE.md** — project-wide guidance every collaborator should see
  (architecture decisions, build commands, repo-specific conventions).
- **CLAUDE.local.md** — personal preferences the user wants
  remembered but not shared (their working style, private aliases,
  in-progress experiments). This file is gitignored.
- **Neither** — if it's session-specific (a temporary state) or already
  obviously documented elsewhere, decline and explain.

### Round 3 — Draft
Write the entry as a single bullet point under the most appropriate
existing heading, OR create a new heading if none fit. Keep the bullet
under 200 characters when possible. Lead with WHAT (the rule), follow
with WHY (the reason) if non-obvious. Avoid repeating yourself.

### Round 4 — Append
Show the user the diff (single line being added). Confirm before
writing. Use the `edit_file` tool to append, not overwrite.

## What NOT to remember

- One-time bug fixes (they live in the commit message).
- Anything contradicting an existing memory without explaining the
  override.
- Information already derivable from `git log` / current code state.
- Secrets, credentials, or PII — refuse and explain.

If the user asks to forget something, do the inverse: locate the
existing entry, show it, confirm, then `edit_file` to remove it.
