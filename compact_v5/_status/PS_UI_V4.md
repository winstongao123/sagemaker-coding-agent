# PS_UI_V4 - v4 Notebook UI Contract

Date: 2026-05-06

Purpose: record the v4 UI behavior that v5 must preserve so the production
notebook feels like the proven v4 SageMaker agent while running the stronger v5
engine.

## Source Lines Reviewed

- v4 notebook config cell: `compact_v4/MAIN/agent/chat.ipynb`, configuration
  cell around the imported `BEDROCK_MODELS`, temperature, thinking, workspace,
  mock-mode, Bedrock-only, and iteration-budget widgets.
- v4 notebook launch cell: `compact_v4/MAIN/agent/chat.ipynb`, launch cell that
  applies widget values and displays the dark `Configuration Applied` banner.
- v4 UI factory: `compact_v4/MAIN/agent/sagemaker_agent.py:9735-12088`.
- v4 sub-agent model override contract:
  `compact_v4/MAIN/agent/sagemaker_agent.py:8402-8411` and
  `compact_v4/MAIN/agent/sagemaker_agent.py:10249-10296`.

## Required v4 Behaviors

| Area | v4 behavior | v5 parity requirement |
|---|---|---|
| Config cell | Dark bordered config box with model, region, temperature, extended thinking, thinking budget, workspace, max turns, iteration budget, mock mode, Bedrock-only. | Keep same controls, same defaults, and same dark styling. |
| Mock default | `Mock Mode` default is off. | v5 notebook must default to real Bedrock unless user ticks mock mode. |
| Launch banner | Dark green `Configuration Applied` banner with model label, Sydney region, temp, thinking state, cost budget, iteration ceiling, AWS scope, and skill/cost hints. | v5 launch banner must use the same dark banner and information density. |
| Main UI layout | Session row, model row, sub-agent model toggle, plan/approval controls, thinking/cost/auto-compact/dark/height controls, chat, input, Send/Stop/Clear/Compact/Clean. | v5 must keep v4 operator muscle memory. |
| Sub-agent controls | Toggle label `Sub-Agent Models`, five model dropdowns: `explore`, `review`, `general`, `build`, `plan`; options are `Same as main` plus all `BEDROCK_MODELS`. | v5 must not show fake role dropdowns like Explorer/Worker/Reviewer. |
| Sub-agent runtime | On spawn, v4 reads `CONFIG.agent_overrides[agent_type]["model"]` and creates a child Bedrock client without mutating the parent client. | v5 `spawn_subagent` must read the same config and preserve parent client/model. |
| Thinking | Toggling thinking exposes the budget control and propagates to the agent. | v5 must keep visible thinking/budget control and call `Agent.set_thinking`. |
| Send/Stop | v4 uses a background send thread so widget callbacks can still process Stop/approval/ask-user events. | v5 must not block the notebook callback thread during long runs. |
| Programmatic fallback | Console fallback can call `ui.send(...)`; widget path should also provide a small `send()` helper for troubleshooting. | v5 widget UI now returns a thread from `send()` so docs are true. |
| Ship zip | Runtime zip must not include local state, tests, cache, sessions, or `.sageagent_state`. | v5 ship verifier must fail if state leaks into the zip. |

## Round-4 Fix Applied

- Restored v4-style sub-agent model dropdowns in `ui/chat_ui.py`.
- Removed dynamic prompt steering for sub-agent preferences; v5 now follows v4
  by using `CONFIG.agent_overrides` at dispatch time.
- Fixed `task -> spawn_subagent(model_id=...)` so sub-agent model selection no
  longer breaks the task tool.
- Added focused lock tests for UI model dropdowns and child model override.
- Restored the dark v4 notebook configuration and launch banner.
- Hardened `_rebuild_zip.py` and `verify_ship_zip.py` against `.sageagent_state`
  leakage and stale release README markers.

## Deferred Larger UI/Architecture Items

The round-4 scans also identified larger Runnable-style enhancements that are
not quick UI parity fixes:

- Durable asynchronous/background sub-agent task handles.
- Live sub-agent activity pane with elapsed time, token delta, status, and stop.
- Queued messages to running sub-agents.
- Worktree preservation when a build sub-agent changes files.
- Deeper context/cost drilldown in the notebook UI.

These are documented in `v5_completion_audit/PS_CODEX_ROUND4_SCAN.md` as future
architecture work. They must not be silently claimed as implemented.
