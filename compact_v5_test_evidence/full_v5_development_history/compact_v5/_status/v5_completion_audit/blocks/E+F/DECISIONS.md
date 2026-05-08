# Block E+F Decisions

Date: 2026-05-04

## EF-2 Hard Cap

`max_budget_usd` is a hard stop checked before Bedrock invocation. It is kept
separate from the existing `session_cost_limit` path, which remains a
warn-and-continue threshold and is covered by existing QueryEngine/F2 tests.
`maxBudgetUsd` is accepted as config-file compatibility for the canonical row
name, while Python code uses snake_case.

## EF-3 Fallback Adaptation

The fallback path is synchronous because v5.0.1 is Bedrock-only and
no-streaming. `FallbackTriggeredError` changes `client.model_id` when possible,
strips model-bound thinking signatures and redacted thinking blocks, and retries
the same call once. After Claude iter1 LOW review, the stripping rule removes
any top-level thinking block key whose normalized name contains `signature`,
plus encrypted-content variants, so future provider signature names do not
silently replay.

## EF-5 Tool Generation Signal

Without streaming, there is no first token callback. The v5 adaptation emits
`tool_gen_callback` when complete tool calls become visible in the assistant
response, before tool dispatch. Claude iter1 noted the first implementation
surfaced only the first call; the final version emits an event for every visible
tool call while preserving the first-call signal.

## EF-6 and EF-7

Both streaming rows are `N/A_CONSTRAINT`. The active v5 rules forbid streaming,
so stream-delivery duplicate suppression and `_fire_stream_delta` paragraph
logic are not runtime surfaces in this repo.
