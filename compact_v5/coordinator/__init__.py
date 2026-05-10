"""V5 coordinator/ — Block G3 coordinator-mode system prompt.

Block G3 (NEW BLOCK, ~300 LOC) ports Runnable's coordinator system prompt
that codifies the user's #1 collaboration rule: 4 phases (Research →
Synthesis → Implementation → Verification), never delegate understanding,
continue-vs-spawn matrix, parallel-research/serial-write rules.

Source: _archive/compare_code/gg-claude-code-runnable/src/coordinator/coordinatorMode.ts
- :111-369  getCoordinatorSystemPrompt()
- :80-109   getCoordinatorUserContext()

PORT_LOG: #092 (system prompt) + #093 (user context).

Per ADR-032 — gated by `CONFIG.coordinator_mode_enabled` (default False).
When enabled, the parent agent's system prompt is augmented with the
coordinator block so the model treats itself as an orchestrator and
delegates work to `task` sub-agents.

Adaptations from Runnable (synchronous v5 vs streaming Anthropic-API):
- SendMessage / TaskStop tools dropped (v5 has no async sub-agent
  channel — sub-agents run sync to completion). Re-invoke vs spawn-fresh
  reframed: in v5 "continue" = next user message in same Agent instance
  (parent has the same engine); "spawn fresh" = new task() call.
- subscribe_pr_activity dropped (constraint #9 + #10 — no streaming).
- MCP references dropped (constraint #9).
- Runnable's worker capability descriptions point to v5's actual tools.
"""
from __future__ import annotations

from .system_prompt import get_coordinator_system_prompt  # noqa: F401
from .user_context import get_coordinator_user_context  # noqa: F401
