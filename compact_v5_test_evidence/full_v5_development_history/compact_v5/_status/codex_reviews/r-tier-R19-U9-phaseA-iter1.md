I've read the loop spec, optimized plan, evidence contract, runner, dream module, chat UI dispatch, gate script, matrix rows, readiness specs, and metrics ledger. Cumulative R-tier spend so far is well under $2 of the $14.25 cap, leaving plenty of headroom for the $0.72 hard ceiling.

# PRE-FLIGHT VERDICT: APPROVE_FOR_AWS_CALL

## Stop-condition checks (all pass)

1. **Production path exercised.** The runner imports `runtime.dream.run_dream` and `runtime.dream.get_dream_prompt` and calls `run_dream(str(tmp_path), consolidator=_llm_consolidator)` — the same call shape `chat_ui._invoke_dream` (`compact_v5/MAIN/agent/ui/chat_ui.py:38-67`) uses. The consolidator wraps the real `BedrockClient` with `mock_mode=False` against `au.anthropic.claude-haiku-4-5-20251001-v1:0`, and the prompt body comes from the real `DREAM_PROMPT_TEMPLATE` (`runtime/dream.py:47-81`). No bypass of `DreamLock`, backup, or phase ordering.

2. **Cannot pass with required facts missing.** `_REQUIRED_FACTS` (`test_r6_r19_u9_dream_bundle.py:31-38`) covers `HYDRA-LIME`, `ap-southeast-2`, `prod/db/password`, `Priya`, `INC-4242`, `Python 3.12`. `required_facts_preserved = all(hits.values())` is a required term in `bundle_completed`, and `bundle_completed` is asserted. Case-insensitive substring is strict enough for these tokens.

3. **Cost accounting is honest, no double-count.** `cost_used = float(TOKENS.session_cost)` is the single real charge. `allocated_cost = cost_used / 2.0` and `_write_side_metrics` overwrites `cost_usd` with the allocated half before persisting to `r-tier-R6-aws-call1-side-metrics.json` and `r-tier-R19-U9-aws-call1-side-metrics.json`. Two per-test rows summing to the actual bundle total is the same convention used by Stage 5/6 bundles and matches the gate's per-test buffered ceiling check (`cost_cap_usd * 1.20 = $0.36` per row, sum = $0.72 hard ceiling). `CONFIG.session_cost_limit = _BUNDLE_HARD_CEILING_USD` enforces the ceiling at the runtime level. Worker must ingest JSONL rows from side-metrics (not from the printed `[R6_R19_U9_METRICS]` line, whose `cost_usd` is the full bundle total).

4. **DreamLock/backup/phase evidence present.** `phases_ok` checks `result.phases_executed == ["Orient", "Gather", "Consolidate", "Prune+Index"]`; `lock_released` checks `dream.lock` is unlinked; `backup_ok` checks `memory.md.bak` contains `HYDRA-LIME` and `INC-4242` (proves backup captured pre-write state). All three are required terms of `bundle_completed`.

5. **R19-U9 does not need a separate AWS call after this.** R19-U9 is a semantic checklist over the same `/dream` consolidated output. Splitting would rerun the identical Bedrock call for zero additional signal. R19-U8 (memory conflict "latest wins") is independent and already `DISPOSITION_OK` in the matrix, so no overlap risk.

6. **Local evidence is sufficient for `r_tier_gate.py` once worker runs the standard post-run step.** Phase A prompt + this review will satisfy the `phaseA-iter*` and `phaseA-iter*-prompt` patterns. Side-metrics + audit JSONL events under `r_tier_runtime/R6+R19-U9-call1-audit/` give the worker enough to build per-test `r-tier-<TEST>-aws-call1-telemetry.json` (with `per_turn`, `tool_call_summary`, `compaction_events`, `subagent_dispatches`, `cache_efficiency_trend`, `outcome`) via `build_telemetry.py`, the same path used for R16/R19-U10/R4. `process_quality_ok` (exactly one `chat_response`, no `tool_failure*`) gives the quality review a real signal.

## Bundle design assessment

**Non-redundant and sufficient.** R6 measures consolidation mechanics (4-phase ordering, dedup of duplicate region/owner/codename notes, stale Python-3.10 collapse, lock release, backup/rollback path, cost cap). R19-U9 measures semantic fact preservation over the same output. One real Haiku call exercises both production behaviors that map to the actual UI dispatch surface. The 100-entry fixture (verified by the inline `assert len(...) == 100`) plus the explicit required-fact set make the bundle high-signal for one shared call. No overlap with R4 cold-cache or R19-U10 long-coherence.

## Cost accounting assessment

**Acceptable.** Single live charge, half-allocated to two per-test rows, runtime ceiling enforced via `CONFIG.session_cost_limit`. Per-test rows stay within `0.30 * 1.20 = $0.36` ceiling individually and sum to the real total. Pre-spend ledger headroom is healthy.

## Findings (none blocking)

- Worker must remember to populate `r_tier_metrics.jsonl` from the side-metrics files (allocated half), not from the bundle-total `[R6_R19_U9_METRICS]` print line. Standard for prior bundles.
- Worker must generate per-test `telemetry.json` files post-run via the existing audit-to-telemetry builder; runner does not auto-emit them. This is consistent with all prior bundle runs and is listed in the required-evidence section.

PRE-FLIGHT VERDICT: **APPROVE_FOR_AWS_CALL**
