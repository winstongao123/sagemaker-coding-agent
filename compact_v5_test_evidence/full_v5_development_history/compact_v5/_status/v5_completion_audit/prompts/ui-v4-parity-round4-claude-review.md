# Claude Review Prompt - UI v4 Parity Round 4

You are the independent reviewer. Do not trust this prompt as evidence; read the
repo files yourself.

Repo path: `D:\Github\sagemaker-coding-agent`

Review target:

- `compact_v5/_status/PS_UI_V4.md`
- `compact_v5/_status/v5_completion_audit/PS_CODEX_ROUND4_SCAN.md`
- `compact_v5/MAIN/agent/ui/chat_ui.py`
- `compact_v5/MAIN/agent/agent.py`
- `compact_v5/MAIN/agent/tools/task.py`
- `compact_v5/MAIN/agent/subagent/spawn.py`
- `compact_v5/MAIN/agent/chat.ipynb`
- `compact_v5/MAIN/agent/tests/integration/test_notebook_smoke.py`
- `compact_v5/MAIN/agent/tests/integration/test_subagent.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_j_ship_gate.py`
- `compact_v5/_rebuild_zip.py`
- `compact_v5/verify_ship_zip.py`
- `compact_v5/README.md`

Canonical references to read:

- v4 UI: `compact_v4/MAIN/agent/chat.ipynb`
- v4 UI/sub-agent implementation:
  `compact_v4/MAIN/agent/sagemaker_agent.py`
- Runnable reference repo:
  `D:\Github\gg_claude_code\gg-claude-code-runnable`

Questions:

1. Does v5 now preserve the important v4 notebook UI contract, especially dark
   config/banner behavior and sub-agent model dropdowns?
2. Does `task -> spawn_subagent` now work with model overrides without mutating
   the parent model/client?
3. Did the patch avoid regressing v5 architecture, cache-boundary behavior,
   completion-audit claims, and production zip minimum-ship constraints?
4. Are the larger Runnable gaps documented honestly as future architecture work
   rather than silently claimed as implemented?
5. Are the focused tests and ship verifier sufficient for this patch?

Required output format:

```
VERDICT: APPROVE | APPROVE_WITH_FIXES | REQUEST_CHANGES
SHIP DECISION: READY_FOR_UI_PARITY_CLOSE | NOT_READY
FINDINGS:
- [severity] file:line - issue
REVIEWED FILES:
- ...
```

If you request changes, make them concrete and limited to this UI/sub-agent/zip
parity patch.
