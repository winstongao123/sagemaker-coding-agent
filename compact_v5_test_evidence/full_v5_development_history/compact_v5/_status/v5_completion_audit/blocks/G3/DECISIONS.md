# Block G3 Decisions

## D-G3-1: Coordinator mode remains default-off

Decision: G3 ships the coordinator prompt and context only behind
`CONFIG.coordinator_mode_enabled`, which defaults to `False`.

Rationale:

- SYNTHESIS_MASTER requires the prompt to be gated by
  `CONFIG.coordinator_mode_enabled`.
- This avoids changing default parent-agent behavior for users who do not opt
  into coordinator mode.

## D-G3-2: Runnable coordinator prompt adapted to v5 synchronous subagents

Decision: Preserve the collaboration rules but adapt worker references to v5's
`task` tool and synchronous worker model.

Rationale:

- v5 subagents run synchronously to completion and do not persist worker
  buffers across task calls.
- The prompt therefore explains v5's continue-vs-spawn semantics as re-launching
  the same subagent type with a self-contained prompt.

## D-G3-3: Real Haiku orchestration remains gated

Decision: Do not run the real Haiku orchestration test during local block close.

Rationale:

- User instructions forbid AWS/R-tier spend.
- The deterministic local prompt, context, and wiring tests are sufficient for
  local completion-audit close.
