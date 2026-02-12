# SageMaker Coding Agent Documentation

## What This App Is

This is a lean internal coding agent for SageMaker:
- single main code file: `sagemaker_agent.py`
- notebook launcher: `chat.ipynb`
- security-first execution controls
- session memory with compaction

It is intentionally smaller than OpenCode and excludes MCP/subagents/LSP/websearch by design.

## Scope vs OpenCode (Beginner View)

### Same core idea
- Chat with an agent
- Read/edit files
- Run commands
- Keep conversation/session history

### What this app does not aim to copy
- MCP ecosystem
- subagents/task orchestration
- full OpenCode platform breadth

### Current status for your scope
- Strong for internal SageMaker use
- Good security controls for a lean app
- Not a full OpenCode clone (intentional)

## Memory and Session Behavior

The app keeps memory using chat history + compaction:

1. Track context usage.
2. Prune older large tool outputs first.
3. If still high, summarize older conversation.
4. Keep recent conversation and recent outputs.

This is practical and good for long sessions, but like all compactors, extremely long chats may lose some detail. Best practice: split very large work into focused sessions.

## Security Model

### Execution controls
- `bash` command allowlist + denylist checks
- dangerous Python patterns/imports blocked
- high-risk tools (`bash`, `python_exec`) require per-use approval

### Isolation
- default execution mode in code is Docker
- workspace mounted to `/workspace`
- optional no-network, read-only rootfs, non-root user, resource limits

If Docker daemon is unavailable in SageMaker, switch to local mode:

```python
execution_mode = "local"
```

This keeps policy controls but removes container isolation.

In many SageMaker Studio environments, Docker daemon access is not available to notebook users, so local mode is the practical path.

### Operational controls
- auth gate (`/auth <token>`)
- rate/session/exec quotas
- audit log retention

## Is This App Good?

For your stated goal (internal company use, lean SageMaker agent): **yes**.

For full OpenCode parity: **no** (and that is expected with your chosen scope).
