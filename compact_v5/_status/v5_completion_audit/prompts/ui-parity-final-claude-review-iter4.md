# UI Parity Final Claude Review Iter4

You are the independent Claude reviewer. Do not trust this worker summary; read the files from disk.

Repository root:

`D:\Github\sagemaker-coding-agent`

Review goal:

Confirm the final v5 notebook UI parity cleanup is ready after the iter3 low finding was addressed.

Canonical context to read:

- `AGENTS.md`
- `compact_v5/_status/v5_completion_audit/CLAUDE_REVIEWER_BASE_PROMPT.md`
- `compact_v5/_status/v5_completion_audit/06_CODEX_WORKER_SELF_COORDINATED_PROMPT.md`
- `compact_v5/_status/V5_DESIGN_DECISIONS.md`
- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md`
- `compact_v5/docs/PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md`
- `compact_v5/docs/PS_V5_LEARNINGS_FROM_REPOS.md`
- `compact_v5/_status/PS_TEST_REVIEW_FINAL.md`
- `compact_v5/docs/htmls/V5_DESIGN_OVERVIEW.html`

Files to inspect:

- `compact_v5/MAIN/agent/agent.py`
- `compact_v5/MAIN/agent/core/query_engine.py`
- `compact_v5/MAIN/agent/ui/chat_ui.py`
- `compact_v5/MAIN/agent/tests/integration/test_notebook_smoke.py`
- `compact_v5/MAIN/agent/chat.md`

Specific checks:

1. v5 UI keeps v4 operator muscle memory while preserving v5 architecture.
2. Plan Mode, Auto-Compact, model dropdown, session buttons, Compact, Clean, and sub-agent preferences are wired to real v5 runtime surfaces.
3. No hidden duplicate approval/ask-user placeholder boxes remain in the UI.
4. The UI no longer writes directly to private `Agent` fields or `Agent._engine.messages`; it should use public methods such as `replace_messages`, `set_plan_mode`, `set_auto_compact`, and `set_ui_subagent_preferences`.
5. Sub-agent preferences are documented and guarded by tests, including disabled behavior and cache-boundary behavior.
6. Tests cover the final UI wiring and are appropriate zero-cost readiness tests.
7. The ship zip verification and scope/R-tier gates are not contradicted by this UI change.

Evidence already run by worker:

- `py -3.11 -m py_compile compact_v5/MAIN/agent/agent.py compact_v5/MAIN/agent/core/query_engine.py compact_v5/MAIN/agent/ui/chat_ui.py`
- From `compact_v5/MAIN/agent`: focused pytest suite returned `47 passed`.
- `py -3.11 compact_v5/_status/scripts/scope_audit.py --all --strict`: `TOTAL_SHIP_BLOCKING_ROWS: 0`.
- `py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root .`: `R-tier gate PASSED`.
- From `compact_v5`: `py -3.11 verify_ship_zip.py`: `RESULT: PASS -- zip is ship-ready`.

Required output format:

```
VERDICT: APPROVE | APPROVE_WITH_FIXES | REQUEST_CHANGES
SHIP DECISION: UI_READY | NOT_READY
FINDINGS:
- ...
REVIEWED FILES:
- ...
```

If there are no blocking findings, use `VERDICT: APPROVE` and `SHIP DECISION: UI_READY`.
