---
name: init-verifiers
description: Use when scaffolding local verifier scripts and explaining how to run verify gates.
disable_model_invocation: true
---
# Init Verifiers

Scaffold verifier guidance for the current workspace:

1. Prefer existing `verify` skill behavior.
2. Keep verifier scripts local and zero-cost.
3. Do not run AWS or R-tier checks without explicit user approval.
4. Report the command or skill invocation the user should run next.

This skill is user-invoked through `/init-verifiers`; it is hidden from model auto-use.
