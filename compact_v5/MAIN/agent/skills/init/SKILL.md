---
name: init
description: Use when initializing a SageMaker agent workspace with status and skill scaffolding.
disable_model_invocation: true
---
# Init Workspace

Prepare a local workspace for agent work:

1. Create or preserve `AGENT_STATUS.md`.
2. Create or preserve the workspace `skills/` directory.
3. Keep existing files intact.
4. Report exactly which paths were created.

This skill is user-invoked through `/init`; it is hidden from model auto-use.
