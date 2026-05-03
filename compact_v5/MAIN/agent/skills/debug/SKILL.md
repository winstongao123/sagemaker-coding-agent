---
name: debug
description: Use when the user reports the agent is stuck, looping, or behaving wrong, or asks "what went wrong" — produces a quick triage from runtime/audit logs.
auto_trigger: false
---

# Debug Triage

You are debugging the agent's recent behavior. The user is reporting an
issue (a stuck loop, an unexpected tool call, an error they don't
understand). Your job is to produce a short, actionable triage.

## Inputs available

- **Audit log** at `runtime/audit/` (JSONL, per-session). Tail the most
  recent lines for the active session.
- **Recent tool calls** (from the last ~20 turns of the message buffer).
- **The user's complaint** (what they actually noticed).

## Procedure (4 steps)

1. **Identify the symptom.** What concrete failure is the user pointing
   at? (Loop? Wrong file edited? Slow response? Crash?)
2. **Tail the audit log** for the last 20 entries of the active session.
   Look for: repeated tool_dispatch with the same args (loop), tool_error
   entries (failure), plan_mode_blocked entries (gating), or
   budget_continuation_stop entries (F2 halts).
3. **Cross-check** the audit findings against the symptom. Does the
   timeline explain what the user saw?
4. **Recommend ONE next action.** Either: a specific config change
   (raise a limit, flip a flag), a code fix (point to file:line), or a
   user instruction (try X instead). Prefer the smallest fix that
   addresses the root cause.

## Output shape

- One paragraph: what happened.
- One paragraph: why (root cause).
- One bullet: the recommended next action.

Do NOT write a full incident report. The user wants a triage, not an
investigation. If the audit log is empty or doesn't explain the symptom,
say so explicitly and ask the user a focused follow-up question.
