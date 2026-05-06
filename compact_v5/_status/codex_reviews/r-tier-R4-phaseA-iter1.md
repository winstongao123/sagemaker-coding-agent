I've completed reading all required files from disk. The design check is complete.

## Decision: APPROVE_FOR_AWS_CALL

### Summary of verification

**A-16 production code path is real and exercised**
- `query_engine.py:682-755` implements the cold-cache microcompact pre-API branch: it gates on `agent_kind=="parent"`, `_last_api_call_time>0`, `Compactor.should_auto_compact(query_source)`, and `now-_last_api_call_time > CONFIG.cold_cache_threshold_seconds`. It calls `Compactor.microcompact(self.messages, keep_n_override=Compactor.KEEP_LAST_N_COLD_CACHE)`, emits typed `compact_micro_start`/`compact_micro_end` audit events with `trigger="cold_cache"`, and prints the user-visible `[i] Cold cache detected` line on success.
- `compactor.py:248-253` defines `MICROCOMPACT_MIN_SAVINGS=5_000`, `KEEP_LAST_N_COLD_CACHE=1`, and `MICROCOMPACT_MARKER`. With KEEP_LAST_N_COLD_CACHE=1, three seeded `read_file` pairs produce exactly two markers.
- `runtime/config.py:122` defines `cold_cache_threshold_seconds: int = 30 * 60`, the field the runner overrides.

**Reshaped runner correctness**
- `test_r4_cold_cache.py:164,186` sets `CONFIG.cold_cache_threshold_seconds=1` and `agent._engine._last_api_call_time=time.time()-5`. Gap (5s) > threshold (1s), conditions all hold (`agent_kind` defaults to "parent"; `agent.run()` defaults `query_source="user"` → `should_auto_compact` is True). Same production code path as the 30-min wallclock case, no skill drift.
- Seeded payload (~140 chars × 350 × 3 ≈ 36–40k tokens) ensures saved tokens >> 5000.
- The new user message is appended via the existing alternation logic (`query_engine.py:496-506`); microcompact still walks all three `read_file` tool_results.

**Lock-test parity**
- `test_block_a.py:133` exercises the same production branch with mock client and 31-min gap.
- `test_software_compact_telemetry.py:68` validates typed `compact_micro_start`/`compact_micro_end` events with `applied=True` and saved_count.

**Cost / model lock**
- Hard-codes `_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"` for both `CONFIG.model_id` and `BedrockClient`. No Sonnet fallback in the test path.
- `CONFIG.session_cost_limit = $0.24` (cap $0.20 × 1.20 retry buffer); `max_turns=2`; `max_tokens=128`; `tools=[]`; one short Haiku turn after seeded local history. `on_stop_check=_hard_cost_halt` blocks any next-turn spend at the ceiling. Estimated cost ~$0.01–0.02, well under cap.
- `RUN_REAL_BEDROCK` skipif gate prevents accidental spend.

**Evidence wiring**
- Side metrics include all required keys (`microcompact_applied`, `microcompact_saved_tokens`, `microcompact_marker_count`, `compact_event_actions`, `process_quality_ok`, `completed`, `verdict`).
- `process_quality_ok` requires the `[i] Cold cache detected` stdout line, ≥2 typed compact events, and no `compact_micro_failed`.
- `build_telemetry.py` will produce non-empty `per_turn` (chat_response event emitted at `query_engine.py:834-863`), typed `compaction_events` via `TYPED_COMPACTION_ACTIONS`, and `agent_attribution` from the side-channel `parent_*` keys.
- `r_tier_gate.py` per-test evidence patterns match the listed required files (`phaseA-iter*`, `aws-call*.log`, `aws-call*-telemetry.json`, `aws-call*-quality.md`, `phaseC-iter*`, metrics row, review log row).

**Non-overlap**
- R2 covered token-threshold auto-compaction; R16 used forced/local compaction with no idle timing; R19-U10 used prebuilt compaction events. Only R4 exercises the time-based pre-API microcompact branch — the same branch the prior `ESCALATION-R4.md` flagged as missing and the user has now ordered shipped.

**No blocking findings.** Stop conditions are well-defined and the runner asserts each one.

`APPROVE_FOR_AWS_CALL`

