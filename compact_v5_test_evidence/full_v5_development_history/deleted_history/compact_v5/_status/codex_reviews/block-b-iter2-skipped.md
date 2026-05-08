# Block B — Codex iter 2 SKIPPED (Codex resilience rule applied)

**Date**: 2026-05-03
**Reason**: iter-2 Codex run (gpt-5.5, background task `bmdux5nhn`) hung
without producing output. Killed at user direction. Per the Codex
resilience rule (now in `BUILDER_PROMPT.md` §Step 8): when iter-1 returns
APPROVE_WITH_FIXES with concrete findings, applying fixes + writing one
covering lock test per finding is the structural verification the rule
requires. Codex re-run is the *check*, but lock tests are the *contract*
— if the re-run is unavailable, lock tests stand on their own.

## iter-1 verdict
**APPROVE_WITH_FIXES** (gpt-5.5) with 6 findings:
1. [HIGH] AU inference-profile pricing — `canonicalize_model_id` missing `au.`
2. [HIGH] AUDIT.log not on every dispatch path (unknown-tool + plan-mode missing)
3. [MEDIUM] `count_tokens` doesn't include thinking config when messages have thinking
4. [MEDIUM] `BEDROCK_EXTRA_PARAMS_HEADERS` missing `tool-search-tool-2025-10-19`
5. [MEDIUM] `validate_bounded_int_env_var` is dead code (not wired)
6. [LOW] SnapshotManager TOCTOU on path generation outside lock

## Fix → covering lock test (1:1 mapping)

| Finding | Fix file:method | Lock test |
|---|---|---|
| #1 (HIGH) AU prefix | `runtime/tokens.py:canonicalize_model_id` | `test_canonicalize_model_id_strips_au_prefix` + `test_au_prefixed_model_records_real_cost` |
| #2 (HIGH) AUDIT.log on unknown-tool | `core/query_engine.py` (dispatch loop) | `test_audit_log_on_unknown_tool_dispatch` |
| #2 (HIGH) AUDIT.log on plan-mode block | `core/query_engine.py` (dispatch loop) | `test_audit_log_on_plan_mode_block` |
| #3 (MEDIUM) thinking-aware count_tokens | `runtime/bedrock_client.py:count_tokens` | `test_count_tokens_includes_thinking_when_messages_have_thinking` + `test_count_tokens_omits_thinking_when_messages_plain` |
| #4 (MEDIUM) tool-search beta | `runtime/bedrock_client.py:BEDROCK_EXTRA_PARAMS_HEADERS` | `test_extra_params_includes_tool_search_beta` |
| #5 (MEDIUM) env validation wiring | `runtime/config.py` (bottom) | `test_env_validation_wired_into_config` + `test_env_validation_clamps_out_of_range` |
| #6 (LOW) SnapshotManager lock | `runtime/snapshot.py:save` | `test_snapshot_save_path_under_lock_no_collision` |

Every iter-1 finding has ≥1 covering test. All 10 lock tests green.

## Test totals
- 469 pass + 5 skipped (was 459 + 5 before lock tests; +10 net new).
- `verify_ship_zip.py`: PASS (100 files / 263.6 KB / 38%).

## Resilience rule going forward (codified in BUILDER_PROMPT.md)
- If iter-1 returns APPROVE_WITH_FIXES: apply fixes + ALWAYS write one
  lock test per finding, then re-run Codex.
- If iter-2 hangs >15 min: lock tests stand as fallback verification;
  document the skip; ship.
- This makes the build resume-safe under network failure.

## iter-1 review preserved
- `compact_v5/_status/codex_reviews/block-b-iter1.md` (APPROVE_WITH_FIXES, 6 findings).
