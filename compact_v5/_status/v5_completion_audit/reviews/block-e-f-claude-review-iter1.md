I have now read the canonical control files (`00_MASTER_PROTOCOL.md`, `03_LEDGER_SCHEMA.md`, `SYNTHESIS_MASTER.md:199-206`, `scope_audit.py`), the worker artifacts (LEDGER, WORKER_SELF_REVIEW, STATUS), the implementation (query_engine.py / formatting.py / __init__.py / config.py), the integration test (`test_block_e_f.py`), the saved logs, and the linked PORT_LOG #112 + ADR-044. I independently reconstructed the EF-1..EF-8 row list from `SYNTHESIS_MASTER.md` before consulting any worker-supplied summary.

```text
EXPECTED ROW COUNT: 8
LEDGER ROW COUNT: 8
DISPOSITION COUNTS:
- SHIPPED: 6
- PARTIAL: 0
- MISSING: 0
- DEFERRED_USER_APPROVED: 0
- DROPPED_USER_APPROVED: 0
- N/A_CONSTRAINT: 2

REVIEWED ROWS:
- EF-1: APPROVE - `_record_tool_denial` at query_engine.py:1308 increments per-turn counter; emits `"3 tool denials this turn"` warning at threshold (line 1316-1321); reset at run() entry (line 381) and per-turn (line 554). Test `test_ef1_permission_denial_tracking_surfaces_three_denials` at test_block_e_f.py:311 forces three denials in one assistant turn and asserts both the warning event payload and the output line. Ledger code refs verified.
- EF-2: APPROVE - `_max_budget_halt` defined at query_engine.py:1329 and called at line 551 INSIDE the per-turn for-loop BEFORE `_chat_with_fallback` at line 697. Reads BOTH `max_budget_usd` (snake_case, config.py:91) AND `maxBudgetUsd` (camelCase compat key in `_SCALAR_FIELDS` at config.py:232). Returns `QueryResult(stop_reason="cost_cap", error=...)`. Distinct surface from `session_cost_limit` warn-and-continue path (~lines 786-794, sets `_warned_over_budget` and continues). Test `test_ef2_max_budget_usd_hard_cap_halts_before_bedrock` proves `client.calls == []` (no Bedrock call) and `result.stop_reason == "cost_cap"`.
- EF-3: APPROVE - `FallbackTriggeredError` at query_engine.py:85; `strip_signature_blocks` at line 151 strips `signature` + `encrypted_content` keys and removes `redacted_thinking` blocks entirely; `_chat_with_fallback` at line 1361 catches the error, swaps `client.model_id`, sanitizes `messages`, retries once. Test `test_ef3_fallback_switches_model_and_strips_signature_blocks` asserts model swap, signature stripped, redacted_thinking removed, plain text preserved.
- EF-4: APPROVE - `core/formatting.py` implements `format_file_size`, `format_duration`, `format_tokens`, `format_cost`. Re-exported in `core/__init__.py:44-49`. Test `test_ef4_shared_format_helpers` covers all four including the small-cost 4-decimal branch and ≥0.01 2-decimal branch.
- EF-5: APPROVE - constructor accepts `tool_gen_callback` (query_engine.py:268), stored at line 318, fired at line 804 via `_notify_tool_generation` (definition at 1376) AFTER the assistant turn is appended but BEFORE the tool-dispatch loop (which begins later in the for-body). Only fires when `response.tool_calls` is non-empty; reports the first tool call. Wrapped in try/except so callback errors do not break the loop. Test `test_ef5_tool_gen_callback_fires_before_tool_dispatch` proves the callback fires BEFORE `tool.execute`.
- EF-6: APPROVE (N/A_CONSTRAINT) - `SYNTHESIS_MASTER.md:204` itself marks this row as `~~Stream-delivery duplicate-suppression~~ DROPPED 2026-05-01 per constraint #10 (no streaming)` with `LOC=0`, `Pri=DROP`, `Fit=DROP`. The hard-constraint citation in the ledger row matches the canonical source. No streaming path exists in v5; nothing to implement.
- EF-7: APPROVE (N/A_CONSTRAINT) - `SYNTHESIS_MASTER.md:205` itself marks this as `~~_fire_stream_delta paragraph-break logic~~ DROPPED 2026-05-01 per constraint #10` with `LOC=0`. Same as EF-6: hard-constraint citation matches; no streaming path exists.
- EF-8: APPROVE - `_emit_status` at query_engine.py:1268 builds `{type, message, session_id, agent_kind, metadata}` payload and calls `status_callback` (set in ctor at line 317) inside try/except. `_emit_warning` (line 1294) delegates to `_emit_status` with `event_type="warning"`. Status events do NOT go to `output_fn`; only warnings do (line 1291-1292) — matches the documented "best-effort callback isolation" claim. Test `test_ef8_status_event_channel_accepts_status_and_warning_callbacks` covers both.

FINDINGS:
- LOW core/query_engine.py:1376 (EF-5 adaptation): the callback fires once on the FIRST tool call only; if multiple tool calls appear in one assistant turn, the model_id/tool/input of the 2nd-Nth calls are not surfaced to UI. This matches Hermes "first tool-arg token" semantics under v5's no-streaming adaptation, but consumers expecting per-call notification will not get it. Not ship-blocking; documented behavior in worker self-review.
- LOW core/query_engine.py:144 (EF-3 signature stripping breadth): only `signature` + `encrypted_content` keys are popped, and only `redacted_thinking` blocks are skipped. If Bedrock adds new provider-specific signature fields in future model versions (e.g., per-vendor signature names), the strip helper will silently leave them in. Worker self-review explicitly flags this as a residual risk. Not ship-blocking under current Sonnet 4.5 / Haiku 4.5 surface.
- LOW _status/scripts/scope_audit.py:217-220 (TOOLING, NOT BLOCK E+F): the disposition→count key map lower-cases `"N/A_CONSTRAINT"` to `"n/a_constraint"`, which does not match the counts dict key `"na_constraint"`, so the printed `N/A: 0` summary line under-reports. The per-row table and ship-blocking verdict are still correct (rows still classified `N/A_CONSTRAINT` in items[] and not flagged ship-blocking). This is a pre-existing tooling bug, NOT introduced by Block E+F, and does not affect the verdict. Worth a tracking row but not Block E+F's responsibility.
- INFO logs/block-e-f-pytest.log + logs/block-e-f-query-f2-regression.log: UTF-16-LE-with-BOM encoding (PowerShell default redirect) makes the logs hard to grep but the visible `21 passed` and `34 passed` numbers match worker claims.

DISPUTED FINDINGS:
- NONE: worker has not disputed any prior finding (no prior reviewer iteration).

REMAINING SHIP-BLOCKING ROWS: 0

VERDICT: APPROVE
SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW
```

Block E+F passes: 8/8 canonical rows ledgered, 6 SHIPPED rows have concrete code + test + PORT_LOG #112 + ADR-044 evidence, EF-2 hard-halt is verifiably pre-Bedrock and distinct from `session_cost_limit`, and EF-6/EF-7 `N/A_CONSTRAINT` matches the SYNTHESIS_MASTER `DROPPED 2026-05-01 per constraint #10` annotation. The two LOW findings on EF-3 strip breadth and EF-5 first-call-only are documented adaptations and do not block ship; the `scope_audit.py` count-line bug is a separate tooling concern.

