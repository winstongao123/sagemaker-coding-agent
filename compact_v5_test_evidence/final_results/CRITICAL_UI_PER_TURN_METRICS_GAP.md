# Critical UI Per-Turn Metrics Gap

Date: 2026-05-08

## User-visible gap

The v5 UI footer showed aggregate cache/cost/reasoning information, but each assistant message did not show its own turn-level cache/cost/reasoning evidence. The header text said cache and reasoning were visible below every turn, but the rendered message rows did not carry that metadata.

## Why prior tests missed it

Previous checks validated that the footer/status area contained cache/cost/reasoning metrics and that the widget could render. They did not assert the message-row contract: after a model run, the assistant row itself must include the turn delta and any captured thinking text.

## Fix

- `QueryResult` now carries display-only `thinking` text captured during the run.
- `chat_ui.py` snapshots token/cost/cache stats before and after each user message.
- Assistant messages now render an inline per-turn metadata strip:
  - input/output tokens,
  - Cache R/W,
  - turn cost,
  - without-cache cost,
  - saved dollars,
  - API calls,
  - reasoning state.
- If thinking text exists, the assistant row includes an expandable reasoning block.

## Regression proof

Zero-cost local checks passed:

```text
public_create_chat_ui_inline_turn_metrics: PASS
widget_inline_metrics_smoke: PASS
py_compile: PASS
```

The public UI smoke uses `create_chat_ui(auto_display=False)`, appends an assistant
message with turn metadata, and asserts the rendered chat HTML contains the
per-turn `Cache R/W`, cost, without-cache cost, saved amount, calls, reasoning
state, and captured thinking text. The renderer accepts both internal
`cache_read`/`cache_write` keys and natural `cache_read_tokens`/`cache_write_tokens`
aliases so future tests do not accidentally miss this UI contract.

## Scope

This is UI/reporting only plus `QueryResult.thinking` plumbing. It does not change Bedrock request shape, tool dispatch, compaction, security, subagent execution, or cache-control behavior.
