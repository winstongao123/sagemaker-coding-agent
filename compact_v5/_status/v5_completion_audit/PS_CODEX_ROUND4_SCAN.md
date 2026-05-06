# PS_CODEX_ROUND4_SCAN

Date: 2026-05-06

Goal: run a fourth source-level comparison against v4 and Runnable before final
shipping, focused on whether v5 is still the best practical single-person
SageMaker coding agent and whether any UI/runtime regression was introduced
during packaging.

## Scope

- v4 UI and notebook behavior: three scan passes across `chat.ipynb`,
  `sagemaker_agent.py`, ship zip scripts, and user-facing guide text.
- Runnable Claude Code architecture: three scan passes across sub-agent/task UI,
  async task orchestration, cache/context systems, and quality gates.
- v5 source/tests/docs: checked against the scan findings, current completion
  audit, R-tier evidence, and ship packaging.

## Must-Fix Findings Landed In This Pass

| Finding | Why it mattered | Disposition |
|---|---|---|
| v5 sub-agent UI showed fake role dropdowns (`Explorer`, `Worker`, `Reviewer`). | v4 uses model dropdowns for real child model overrides; fake roles confuse users and do not map to the task schema. | Fixed. v5 now exposes `explore`, `review`, `general`, `build`, `plan` model dropdowns with `Same as main` + all Bedrock models. |
| `task` passed `model_id` to `spawn_subagent`, but `spawn_subagent` did not accept it. | Any sub-agent call through the task tool could raise `TypeError`. | Fixed. `spawn_subagent` accepts `model_id`, reads `CONFIG.agent_overrides`, creates a child client, and preserves the parent client. |
| v5 notebook banner/config colors drifted from v4. | User-facing v5 looked unlike the proven v4 notebook and produced unreadable light styling in dark notebooks. | Fixed. Cell 2/3 now restore the dark v4 config box and dark green launch banner. |
| Ship zip could include `.sageagent_state`. | A production zip must not leak local runtime state or absolute paths. | Fixed. Rebuild excludes it and verifier forbids it. |
| Release README still described the old failed v5.0.0 checkpoint. | Production-facing docs contradicted final audit status. | Fixed. README now describes v5.0.1 production candidate and supersedes v5.0.0. |

## Larger Runnable Gaps Not Landed In This Pass

| Gap | Runnable reference behavior | v5.0.1 status | Reason not added here |
|---|---|---|---|
| Durable async/background sub-agent tasks | Runnable can detach agents, track background tasks, stop them, and retrieve output later. | v5 sub-agents are synchronous one-shot tasks with envelopes, shared budget, worktree support, and audit records. | Requires a larger task scheduler/state machine and fresh R-tier tests. Not safe as a packaging/UI parity patch. |
| Live sub-agent activity pane | Runnable displays agent rows, elapsed time, tokens, queued messages, and controls. | v5 records sub-agent envelopes and token/cost deltas, but UI only shows sub-agent mode summary. | Valuable future UX block, not required to fix v4 parity regression. |
| Queue messages to running child agents | Runnable can send messages to running tasks. | v5 child agents complete synchronously. | Depends on async task substrate. |
| Preserve changed build worktrees | Runnable keeps useful changed worktrees. | v5 build sub-agent uses isolated worktree but cleanup is best-effort and not a durable handoff surface. | Needs explicit UX and cleanup policy. |
| API-side task-budget signal | Runnable can pass `output_config.task_budget`. | v5 uses local iteration budget and Bedrock `max_tokens`; no Anthropic API-only `output_config`. | Bedrock API shape differs; local budget/cost gates are the production path. |
| Deeper cache-break diagnosis | Runnable records broad cache-key snapshots. | v5 has tool-schema/cache-control detection and R-tier evidence, but not full Runnable diagnostics. | Future observability polish. |

## Confidence Statement

The round-4 scan found real regressions, and the must-fix ones are now patched
with lock tests. The larger gaps are architectural enhancements, not hidden
claims: they remain documented as future work. Production readiness should still
be judged by the completed block audit, R-tier gates, final Claude review, and
the post-fix ship verifier.
