Files reviewed from disk:
- `PS_AWS_TEST_EXECUTION_LOOP.md` (loop, Phase A gate, evidence locations)
- `OPTIMIZED_AWS_VALIDATION_PLAN.md` (matrix optimisation, retry buffer policy)
- `R_TIER_EVIDENCE_CONTRACT.md` (required evidence/keys, validation gate)
- `r_tier_test_matrix.json` (R17 row: real, Sonnet 4.5 AU, cap $0.30, status `EXECUTABLE_PENDING_RUN`)
- `tests/r_tier/test_r17_thinking_visibility.py`
- `tests/r_tier/test_r6_to_r19_readiness_specs.py` (R17 not in spec map; R17 has its own dedicated runner â€” consistent with R1/R2/R3/R4/R13/R16/R19-U10 pattern)
- `compact_v5/_status/scripts/build_telemetry.py`
- `tests/integration/test_build_telemetry.py`
- `runtime/bedrock_client.py`
- `core/query_engine.py` (chat_response emission at lines 833-865)
- Phase A iter1 prompt file (present on disk)
- `r_tier_metrics.jsonl` â€” no prior R17 row, this is call1 with no preserved diagnostic spend to reconcile

# R17 Phase A review

## Q1 â€” Real-AWS need (vs local mock)
Yes, R17 is still needed as a real Sonnet row.

- The local lock tests already passed (3 passed in the worker zero-cost run): `test_thinking_config_sent_on_every_call_when_enabled` only proves the Bedrock request body always carries `thinking={...}`, and the two `build_telemetry` thinking tests only prove the aggregator can extract `parameters.response.thinking` when audit JSONL contains it. Neither proves a Sonnet response actually returns a thinking block, that QueryEngine writes `getattr(response, "thinking", "")` non-empty into the audit log, or that Agent persists a `{"type":"thinking",...}` block into `agent.messages`. Only a real Bedrock call exercises that end-to-end PS#4 path.
- R2/R4/R16/R19-U10 do not require extended thinking and do not validate thinking text in either history or telemetry source. R17 is the only matrix row that pins this PS#4 evidence.
- R17 is the only Sonnet row currently scheduled outside R11. Running R17 here also gives a small Sonnet smoke for the AU profile id used in the matrix without taking on R11's $1.50 budget.

## Q2 â€” Production path coverage
Yes. The runner exercises the intended PS#4 path:

- `CONFIG.thinking_enabled=True`, `CONFIG.thinking_budget=4096`, and `Agent(thinking_enabled=True, thinking_budget=4096)` flow into the production loop.
- `bedrock_client.chat()` (lines 388-393) unconditionally sets `body["thinking"]={"type":"enabled","budget_tokens": clamped}` and forces `temperature=1` whenever the caller passes `thinking_enabled=True`. PS#4's "send config every turn, not just first turn" contract is locked by `test_thinking_config_sent_on_every_call_when_enabled` and reused live here.
- `_parse()` (lines 541-566) accumulates thinking blocks into `Response.thinking`.
- QueryEngine (lines 833-865) writes a `chat_response` audit row with `parameters.response = {"usage", "thinking", "text", "stop_reason", "tool_calls"}` for every model turn. The R17 helper `_chat_response_thinking` reads exactly `parameters.response.thinking`, and `build_telemetry.py._aggregate_per_turn` reads the same nested field (covered by `test_build_telemetry_reads_query_engine_nested_chat_response`).
- The runner asserts thinking is present in both `agent.messages` (assistant content blocks of `type=="thinking"`) and the audit `chat_response` events. That dual check is what makes R17 a real PS#4 visibility proof rather than an "implicit" smoke.

## Q3 â€” Cost cap, stop rules, evidence
Adequate.

- Planned cap $0.30, hard ceiling $0.36 (cap Ã— 1.20) matches the user-approved retry-buffer rule in `R_TIER_EVIDENCE_CONTRACT.md` and `OPTIMIZED_AWS_VALIDATION_PLAN.md`.
- `CONFIG.session_cost_limit` is set to the hard ceiling and `on_stop_check=_hard_cost_halt` halts the loop before exceeding it. Final assertion fails if `cost_used > _R17_HARD_CEILING_USD`.
- `tools=[]`, `max_turns=8`, and a bounded two-train reasoning prompt make tool-loop cost zero by construction (`tool_calls=0` is the expected metric). Sonnet 4.5 with `max_tokens=2048` and `thinking_budget=4096` should converge in 1-2 turns; even at 8 turns the spend stays well under cap.
- Stop conditions cover Phase A approval, budget headroom, hard ceiling, max_turns, missing thinking in either history or audit, telemetry build failure, and unexpected tool/exec loops. No prior R17 metrics row means no diagnostic spend reconciliation is required for call1.
- The required evidence list in the prompt matches `R_TIER_EVIDENCE_CONTRACT.md` (Phase A prompt/review, raw log, side metrics, telemetry, quality, metrics row, review-log row, Phase C, gate). Side metrics path (`r-tier-R17-aws-call1-side-metrics.json`) is the canonical input for `build_telemetry --metrics-side-channel`.

## Q4 â€” Isolation and non-overlap
Sufficient.

- No tools, no subagents, no compaction-driving fixture. R17 isolates "does Sonnet return a thinking block, and does v5 capture it on both surfaces" without confounding capabilities.
- Sonnet usage is justified: the matrix specifies Sonnet 4.5 AU for R17 because Sonnet is the production thinking model and the row's purpose is real-model thinking visibility. This is not a Haiku-substitutable test.
- AU profile id `au.anthropic.claude-sonnet-4-5-20250929-v1:0` and default region `ap-southeast-2` align with prior matrix runs.
- The R14/R19-U3 guard-loop recurrence watch surface is intentionally tiny here (zero tools), which is acceptable because this row is not the loop-watching test.

## Minor observations (non-blocking)
- `test_r6_to_r19_readiness_specs.py` does not include an "R17" entry. R17 is exempted from that parametrised spec because it has its own dedicated runner (same pattern as R1/R2/R3/R4/R13/R16/R19-U10 already in production). Not a blocker, but if the worker wants a belt-and-braces marker, a follow-up could add an R17 entry to that spec map. Do not block this run on it.
- `cache_hit_pct` is set to 0.0 in side metrics; the actual numeric cache fields will come from `TokenTracker.get_stats()` and through `_aggregate_per_turn` from the audit `usage`. Keep that and let `build_telemetry` populate the per-turn cache fields so the evidence is not silently zero. If Bedrock returns no cache fields for this short Sonnet call, record the explicit `MODEL_LIMITATION` row per the contract instead of leaving cache fields blank.
- Quality review must explicitly grade thinking-block usefulness (more than just "present, >50 chars") so a degenerate "ok." thinking string does not silently pass production-readiness signal. The runner's 50-char floor is a structural lower bound, not a quality grade.

## Decision

R17 is safe and useful to run on real AWS now under the stated cap, ceiling, stop rules, and evidence contract.

APPROVE_FOR_AWS_CALL
