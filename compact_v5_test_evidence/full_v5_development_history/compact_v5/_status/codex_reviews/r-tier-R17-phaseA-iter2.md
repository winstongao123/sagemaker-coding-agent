# R17 Phase A iter2 review

Files read from disk:
- `compact_v5/_status/v5_completion_audit/PS_AWS_TEST_EXECUTION_LOOP.md`
- `compact_v5/_status/v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md`
- `compact_v5/_status/R_TIER_EVIDENCE_CONTRACT.md`
- `compact_v5/_status/r_tier_test_matrix.json` (R17 row: real, Sonnet 4.5 AU, cap $0.30, status `EXECUTABLE_PENDING_RUN`)
- `compact_v5/MAIN/agent/tests/r_tier/test_r17_thinking_visibility.py`
- `compact_v5/_status/codex_reviews/r-tier-R17-phaseA-iter1.md`
- `compact_v5/_status/scripts/build_telemetry.py`
- `compact_v5/MAIN/agent/tests/integration/test_build_telemetry.py`
- `compact_v5/MAIN/agent/tests/unit/test_bedrock.py`
- `compact_v5/MAIN/agent/runtime/bedrock_client.py`
- `compact_v5/MAIN/agent/core/query_engine.py` (lines 605-620, 783-794, 820-870)
- `compact_v5/MAIN/agent/agent.py` (lines 195-231)
- `compact_v5/MAIN/agent/runtime/tokens.py` (MODEL_COSTS, `add()`, `is_over_budget`)

## Q1 â€” Bedrock thinking invariant under iter2

The iter2 change correctly satisfies the Bedrock invariant.

- Bedrock requires `max_tokens > thinking.budget_tokens` whenever extended thinking is enabled. With `thinking_budget=4096` and `max_tokens=8192`, the invariant holds with a 4096-token margin.
- iter1 set `max_tokens=2048` with `thinking_budget=4096`. That combination would fail Bedrock validation before any model output, so iter1's `APPROVE_FOR_AWS_CALL` was for an unrunnable configuration. Iter2 is the minimum sensible fix that actually exercises the PS#4 path.
- Propagation is intact: `test_r17` sets `CONFIG.max_tokens = 8192` (line 108); `Agent.run()` reads `_max_tokens = getattr(_CFG, "max_tokens", 4096)` and passes it to `QueryEngine.run()` (`agent.py` lines 200-228); `QueryEngine.run()` forwards `max_tokens=max_tokens` to `BedrockClient.chat()` (line 790); `BedrockClient.chat()` writes `body["max_tokens"] = max_tokens` (line 376) and `body["thinking"] = {"type":"enabled","budget_tokens": clamped}` plus `temperature=1` (lines 388-393).
- The test still records `"max_tokens": CONFIG.max_tokens` in side metrics (line 191), so iter2 evidence will show 8192 in `r-tier-R17-aws-call1-side-metrics.json` and Phase C can verify the fix landed.

## Q2 â€” Cost model under the new max_tokens

The cost model still holds under the planned cap and buffered hard ceiling.

- Sonnet 4.5 base pricing in `MODEL_COSTS` (`runtime/tokens.py:63`): input $0.003/1K, output $0.015/1K. Bedrock counts thinking tokens as output tokens, so `TOKENS.add()` already captures thinking spend correctly. The `au.` prefix is canonicalised before lookup.
- Worst-case per turn (full `max_tokens=8192` output saturation): 8192 Ã— $0.000015 â‰ˆ $0.123 output + ~$0.015 input â‰ˆ $0.138. Realistic per turn for a bounded two-train math problem: ~3-4K thinking + ~150-300 text â†’ â‰ˆ $0.05-$0.07. The cost change from iter1's broken `max_tokens=2048` to iter2's `max_tokens=8192` is effectively neutral for this prompt because the model would never have been able to run at iter1 settings, and the prompt does not pull anywhere near 8192 output tokens for an unambiguous math answer.
- Runtime guardrails:
  - `CONFIG.session_cost_limit` is set to `_R17_HARD_CEILING_USD` ($0.36) (runner line 105).
  - `_hard_cost_halt` calls `TOKENS.is_over_budget()` (`tokens.py:538-540`), which compares `session_cost >= limit`.
  - `QueryEngine.run()` checks `on_stop_check` at the **start of every turn** (`query_engine.py:611-620`), before the next Bedrock invoke. So once cumulative cost â‰¥ $0.36, the loop halts before another paid call.
  - The runner's final assertion `cost_used <= _R17_HARD_CEILING_USD` is a post-run hard fail.
- Even a degenerate sequence of â‰ˆ3 fully-saturated turns (â‰ˆ$0.41) is implausible for a `tools=[]`, no-state, single-question prompt against Sonnet, and would still trip the hard-halt-then-assert path; AWS spend would be preserved as diagnostic, not silently inflated.
- Planned cap $0.30 / hard ceiling $0.36 (cap Ã— 1.20) matches the user-approved buffer rule in `R_TIER_EVIDENCE_CONTRACT.md` and `OPTIMIZED_AWS_VALIDATION_PLAN.md`. No prior R17 metrics row exists, so there is no diagnostic spend to reconcile for call1.

## Q3 â€” Safe and useful to run

- Production path coverage is unchanged from iter1 and still real:
  - `Agent(thinking_enabled=True, thinking_budget=4096)` flows through `QueryEngine.run()` into `BedrockClient.chat()`, which sends `body["thinking"]` on every call (locked by `test_thinking_config_sent_on_every_call_when_enabled`).
  - `BedrockClient._parse()` accumulates `thinking` blocks into `Response.thinking` (`bedrock_client.py:541-566`).
  - `QueryEngine` writes `chat_response` audit rows with `parameters.response = {"usage","thinking","text","stop_reason","tool_calls"}` per turn (`query_engine.py:833-865`).
  - `_chat_response_thinking` in the runner reads exactly `parameters.response.thinking`, and `build_telemetry.py:_aggregate_per_turn` reads the same nested field (`build_telemetry.py:159-167`, locked by `test_build_telemetry_reads_query_engine_nested_chat_response`).
  - The runner asserts thinking presence on **two surfaces** (`agent.messages` content blocks of `type=="thinking"` AND audit `chat_response`), which is what makes R17 a real PS#4 visibility proof.
- Isolation: `tools=[]`, `max_turns=8`, no subagents, no compaction-driving fixture. The R14/R19-U3 guard-loop recurrence watch surface is intentionally tiny (zero tools); not a coverage gap because R17 is not the loop-watching row.
- Stop conditions cover Phase A approval, budget headroom, hard ceiling, max_turns, missing thinking on either surface, telemetry build failure, and unexpected tool/exec loops. Required evidence list matches `R_TIER_EVIDENCE_CONTRACT.md`.

## Minor observations (non-blocking)

- Quality review must explicitly grade thinking-block content quality (not only presence/length), so a degenerate "ok." thinking string cannot silently pass production-readiness signal. The runner's 50-char floor is a structural lower bound, not a quality grade.
- `cache_hit_pct` is initialised to `0.0` in side metrics; let `build_telemetry` populate per-turn cache fields from audit `usage`. If Sonnet returns no cache fields for this short call, record the explicit `MODEL_LIMITATION` row per the contract instead of leaving cache fields silently blank. Inspect the raw response payload before declaring a model limitation.
- The iter2 prompt notes the worker caught the Bedrock `max_tokens > thinking.budget_tokens` invariant after iter1 approved. Phase C should explicitly verify side-metrics `max_tokens=8192` and `thinking_budget=4096` so this fix is locked into evidence, not just code.

## Decision

R17 iter2 satisfies the Bedrock thinking invariant, preserves the cost model under the stated cap and buffered hard ceiling, and is still safe and useful to run on real AWS now under the stated stop rules and evidence contract.

APPROVE_FOR_AWS_CALL
