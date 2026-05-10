You are Claude Code acting as an independent read-only reviewer.

Review Block 5 of the v5 solve-all pass. Do not edit files.

Repository root: `D:/Github/sagemaker-coding-agent`

Goal: verify display-only prompt/token/cache measurement visibility. This block must not change model selection, prompt content, cache behavior, compaction, or tool schemas.

Changed files:
- `compact_v5/agent.py`
- `compact_v5/ui/chat_ui.py`
- `compact_v5/tests/test_prompt_metrics_smoke.py`

Expected changes:
- `Agent` records `last_prompt_metrics` before each engine run.
- Metrics include system/static/dynamic prompt chars, cache boundary count, visible/deferred tool counts, visible/deferred schema chars, status/memory chars, and thinking state/budget.
- UI footer renders a "Prompt metrics:" line from `agent.last_prompt_metrics`.
- No prompt text is modified and no cache-control behavior is changed.
- Smoke test verifies the metrics exist and do not require a real Bedrock call.

Verification commands run by Codex:
- `python -m py_compile compact_v5/agent.py compact_v5/ui/chat_ui.py compact_v5/tests/test_prompt_metrics_smoke.py`
- `python compact_v5/tests/test_prompt_metrics_smoke.py`
- manual import check printed a populated `last_prompt_metrics` dict with one cache boundary.

Please inspect the files yourself and return:
- Verdict: APPROVE, APPROVE_WITH_FIXES, or BLOCK
- Findings table, if any
- Whether this block drifted beyond display-only measurement
