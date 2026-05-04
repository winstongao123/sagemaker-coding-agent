# Block E+F Ledger

Date: 2026-05-04
Source of expected rows: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:199-206`

| row_id | capability | source | priority | fit | expected_target | code_evidence | test_evidence | port_log | adr | historical_review | git_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EF-1 | Permission-denial tracking surface, `"3 tool denials this turn"` UI | SYNTHESIS_MASTER.md:199 | MED | CLEAN | `core/query_engine.py` status event and approval-denial path | `core/query_engine.py:1145,1166,1272,1312` records approval denials and emits status/warning events. | `test_block_e_f.py:311` covers three denials surfacing through callback and output. | #112 | ADR-044 | NOT_INCLUDED_IN_REDO_REVIEW_BEFORE_ITER1 | working tree implementation pending Block E+F commit | SHIPPED | No implementation action; Claude iter2 approved. | APPROVE |
| EF-2 | `maxBudgetUsd` hard-cap halt | SYNTHESIS_MASTER.md:200 | MUST | CLEAN | `runtime/config.py` and QueryEngine pre-Bedrock guard | `runtime/config.py:91,232` adds hard-cap config and camel-case compatibility; `core/query_engine.py:555,1333` halts before Bedrock when session cost is at or above the cap. | `test_block_e_f.py:280` covers pre-Bedrock hard halt and status warning. | #112 | ADR-044 | NOT_INCLUDED_IN_REDO_REVIEW_BEFORE_ITER1 | working tree implementation pending Block E+F commit | SHIPPED | No implementation action; Claude iter2 approved. | APPROVE |
| EF-3 | `FallbackTriggeredError` model switch plus `stripSignatureBlocks` | SYNTHESIS_MASTER.md:201 | MED | NEEDS-ADAPTATION | `core/query_engine.py` fallback retry helper | `core/query_engine.py:85,134,155,1368` defines fallback error, strips signature variants/redacted thinking blocks, switches model, and retries once. | `test_block_e_f.py:362` covers model switch plus signature/redacted-thinking removal before retry. | #112 | ADR-044 | NOT_INCLUDED_IN_REDO_REVIEW_BEFORE_ITER1 | working tree implementation pending Block E+F commit | SHIPPED | Claude iter2 confirmed iter1 LOW fix. | APPROVE |
| EF-4 | `formatFileSize` / `formatDuration` / `formatTokens` / `formatCost` helpers | SYNTHESIS_MASTER.md:202 | HIGH | CLEAN | `core/formatting.py` shared helper module | `core/formatting.py:9,27,48,57` implements central formatting helpers; `core/__init__.py:45-48` re-exports them. | `test_block_e_f.py:265` covers all four helpers. | #112 | ADR-044 | NOT_INCLUDED_IN_REDO_REVIEW_BEFORE_ITER1 | working tree implementation pending Block E+F commit | SHIPPED | No implementation action; Claude iter2 approved. | APPROVE |
| EF-5 | `tool_gen_callback` on first tool-arg token | SYNTHESIS_MASTER.md:203 | HIGH | CLEAN | QueryEngine tool-use generation event hook | `core/query_engine.py:271,322,808,1380` adds optional `tool_gen_callback` and fires generation events for visible tool calls before dispatch. | `test_block_e_f.py:403` covers callback events before tool execution for multiple calls. | #112 | ADR-044 | NOT_INCLUDED_IN_REDO_REVIEW_BEFORE_ITER1 | working tree implementation pending Block E+F commit | SHIPPED | Claude iter2 confirmed iter1 LOW fix. | APPROVE |
| EF-6 | Stream-delivery duplicate-suppression | SYNTHESIS_MASTER.md:204 | LOW | DROP | Streaming delivery path | NONE_FOUND due v5 no-streaming constraint. | NO_TEST_JUSTIFICATION:v5.0.1 forbids streaming, so no stream delivery duplicate path exists to execute. | #112 | ADR-044 | NOT_INCLUDED_IN_REDO_REVIEW_BEFORE_ITER1 | working tree implementation pending Block E+F commit | N/A_CONSTRAINT | No implementation action; Claude iter2 approved N/A constraint. | APPROVE |
| EF-7 | `_fire_stream_delta` paragraph-break logic | SYNTHESIS_MASTER.md:205 | LOW | DROP | Streaming delta paragraph handling | NONE_FOUND due v5 no-streaming constraint. | NO_TEST_JUSTIFICATION:v5.0.1 forbids streaming, so no `_fire_stream_delta` paragraph path exists to execute. | #112 | ADR-044 | NOT_INCLUDED_IN_REDO_REVIEW_BEFORE_ITER1 | working tree implementation pending Block E+F commit | N/A_CONSTRAINT | No implementation action; Claude iter2 approved N/A constraint. | APPROVE |
| EF-8 | `_emit_status` / `_emit_warning` event channel | SYNTHESIS_MASTER.md:206 | LOW | CLEAN | QueryEngine status/warning callback channel | `core/query_engine.py:271,321,1272,1305` adds optional status callback and status/warning emitters. | `test_block_e_f.py:441` covers status and warning event callback payloads. | #112 | ADR-044 | NOT_INCLUDED_IN_REDO_REVIEW_BEFORE_ITER1 | working tree implementation pending Block E+F commit | SHIPPED | No implementation action; Claude iter2 approved. | APPROVE |

EXPECTED_ROWS: 8
LEDGER_ROWS: 8
SHIPPED: 6
PARTIAL: 0
MISSING: 0
DEFERRED_USER_APPROVED: 0
DROPPED_USER_APPROVED: 0
N/A_CONSTRAINT: 2
SHIP_BLOCKING_ROWS: none
