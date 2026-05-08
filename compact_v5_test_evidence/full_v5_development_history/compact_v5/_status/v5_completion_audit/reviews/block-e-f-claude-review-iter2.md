All evidence verified. Producing the iter2 review.

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
- EF-1: APPROVE - `_record_tool_denial` at core/query_engine.py:1312 increments `_tool_denials_this_turn`, emits the canonical `"3 tool denials this turn"` warning at line 1321 with metadata, and resets per-turn at line 558. Test `test_ef1_permission_denial_tracking_surfaces_three_denials` (test_block_e_f.py:311) covers callback + output line. Ledger refs verified.
- EF-2: APPROVE - `_max_budget_halt` defined at core/query_engine.py:1333 and called at line 555 INSIDE the per-turn loop BEFORE Bedrock invocation. Reads BOTH `max_budget_usd` (snake) AND `maxBudgetUsd` (camel) from `runtime/config.py:91,232`. Returns `QueryResult(stop_reason="cost_cap", error=...)` with metadata `{session_cost, max_budget_usd}`. Distinct from `session_cost_limit` warn-and-continue path (~line 786-797 sets `_warned_over_budget`).
- EF-3: APPROVE - `FallbackTriggeredError` at core/query_engine.py:85; `_strip_signature_from_content` at line 134 now (a) removes `redacted_thinking` blocks entirely, and (b) pops ANY top-level key whose normalized name contains `signature` plus normalized `encryptedcontent` variants. `_chat_with_fallback` at line 1365 swaps `client.model_id` then sanitizes `messages` and retries once. Test `test_ef3_fallback_switches_model_and_strips_signature_blocks` at test_block_e_f.py:362 actively covers `signature`, `thinkingSignature`, `signature_base64`, `vendor_signature`, and `encryptedContent` variants plus a `redacted_thinking` block, and asserts plain text + the `thinking` key itself are preserved. **Iter1 LOW EF-3 fix CONFIRMED.**
- EF-4: APPROVE - core/formatting.py implements `format_file_size`, `format_duration`, `format_tokens`, `format_cost` with sign handling, sub-1s ms branch, hour rollover, and the small-cost 4-decimal vs `>=$0.01` 2-decimal branch. Re-exported from core/__init__.py:45-48. Test `test_ef4_shared_format_helpers` at test_block_e_f.py:265 covers all four including the 4-decimal branch.
- EF-5: APPROVE - constructor accepts `tool_gen_callback` (core/query_engine.py:272), stored at line 322, fired at line 808 via `_notify_tool_generation` (definition at line 1380) AFTER the assistant turn is appended but BEFORE tool dispatch. The body now `for call in calls:` (line 1386) emits a `tool_generation` event for EVERY visible tool call, not just the first; each call wrapped in try/except so callback errors do not break the loop. Test `test_ef5_tool_gen_callback_fires_before_tool_dispatch` (test_block_e_f.py:403) constructs a Response with TWO ToolCall entries (`c1` and `c2`) and asserts the callback order is `[("callback","write_file","x.txt"), ("callback","write_file","y.txt")]` BEFORE the tool actually executes. **Iter1 LOW EF-5 fix CONFIRMED.**
- EF-6: APPROVE (N/A_CONSTRAINT) - SYNTHESIS_MASTER.md:204 itself marks the row as `~~Stream-delivery duplicate-suppression~~ DROPPED 2026-05-01 per constraint #10 (no streaming)` with `LOC=0`, `Pri=DROP`, `Fit=DROP`. The hard-constraint citation in the ledger row matches the canonical source. No streaming path exists in v5; nothing to implement.
- EF-7: APPROVE (N/A_CONSTRAINT) - SYNTHESIS_MASTER.md:205 itself marks the row as `~~_fire_stream_delta paragraph-break logic~~ DROPPED 2026-05-01 per constraint #10` with `LOC=0`. Same constraint citation; no streaming path exists.
- EF-8: APPROVE - `_emit_status` at core/query_engine.py:1272 builds `{type, message, session_id, agent_kind, metadata}` payload and calls `status_callback` (set in ctor at line 321) inside try/except. `_emit_warning` (line 1298) delegates to `_emit_status` with `event_type="warning"` plus `output_fn` so warnings ALSO go to the output stream while status events do not — matches the documented best-effort isolation. Test `test_ef8_status_event_channel_accepts_status_and_warning_callbacks` (test_block_e_f.py:441) covers both shapes.

FINDINGS:
- INFO: Iter1 LOW EF-3 (signature stripping breadth) is now structurally fixed. The new test asserts five distinct signature key variants AND the encrypted-content variant get stripped while preserving the `thinking` content key — this is the strongest possible local proof against future Bedrock signature-name additions, short of an integration test against a live model.
- INFO: Iter1 LOW EF-5 (first-call-only tool_gen_callback) is now structurally fixed. The test now uses TWO tool calls in a single assistant turn and asserts both are surfaced in order before tool dispatch.
- INFO: TESTS.md references `block-e-f-py-compile-iter2.log` but that file does not exist on disk (only the iter1 `block-e-f-py-compile.log` exists). I independently re-ran `py -3.11 -m py_compile` against all five files listed in TESTS.md and got `py_compile OK`. Pure documentation/log housekeeping miss; not ship-blocking. Worker should add the file or remove the reference before final close.
- LOW _status/scripts/scope_audit.py:217-220 (TOOLING, NOT BLOCK E+F): scope-audit `N/A: 0` summary line still under-reports; the per-row table and ship-blocking verdict remain correct (EF-6/EF-7 still classified `N/A_CONSTRAINT` and not ship-blocking). Pre-existing tooling bug carried over from iter1, properly disclaimed in WORKER_SELF_REVIEW.md as outside Block E+F ownership. Not ship-blocking for Block E+F.
- INFO Independent local re-runs: `py -3.11 -m pytest tests/integration/test_block_e_f.py -q` → 21 passed in 0.49s; `py -3.11 -m pytest tests/integration/test_block_f2.py tests/integration/test_block_e_f.py -q` → 41 passed in 0.56s (covers F2 regression set + the 21 EF tests, no failures); `py -3.11 compact_v5/_status/scripts/scope_audit.py --block "E+F"` → `READY_TO_REVIEW_CLOSE`, no ship-blocking rows.

DISPUTED FINDINGS:
- Iter1 LOW EF-3 (signature stripping breadth): WITHDRAWN. Reread `_strip_signature_from_content` at core/query_engine.py:134-152 — the helper now normalizes each key (lowercase, strip underscores) and drops any whose normalized form contains `signature` or equals `encryptedcontent`, and `redacted_thinking` blocks are entirely skipped. Test at test_block_e_f.py:362 asserts five distinct signature variants and the encrypted-content variant are all removed while preserving the `thinking` key text. Original concern fully addressed within the constraints of a local fix.
- Iter1 LOW EF-5 (first-call-only callback): WITHDRAWN. Reread `_notify_tool_generation` at core/query_engine.py:1380-1399 — body is `for call in calls:` and emits per-call events; test at test_block_e_f.py:403 forces two tool calls in one assistant turn and asserts both events fire before tool execution.
- Iter1 INFO scope_audit.py count-display bug: UPHELD as still-present TOOLING note (not Block E+F's responsibility, not ship-blocking). Worker correctly tracks it separately in WORKER_SELF_REVIEW.md.

REMAINING SHIP-BLOCKING ROWS: 0

VERDICT: APPROVE
SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW
```

Block E+F iter2 passes: all 8 canonical SYNTHESIS_MASTER rows are ledgered; both iter1 LOW findings (EF-3 signature breadth + EF-5 multi-call callback) are structurally fixed in code AND covered by new test assertions; tests independently re-run green (21 + 41); scope_audit independently re-run green with no ship-blocking rows; PORT_LOG #112 + ADR-044 evidence verified. Only fresh INFO is a missing iter2 py_compile log file (TESTS.md references it but the worker apparently didn't write it); I re-ran py_compile myself and it passes, so this is a doc-housekeeping miss, not a ship blocker. The pre-existing scope_audit `N/A: 0` display bug remains, correctly tracked outside Block E+F scope.

