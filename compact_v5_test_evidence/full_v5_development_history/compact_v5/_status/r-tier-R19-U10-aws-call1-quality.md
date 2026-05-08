# R19-U10 AWS Call1 Quality Review

Date: 2026-05-06

Verdict: GENUINE_PASS

## Inputs Reviewed

- Raw log: `compact_v5/_status/codex_reviews/r-tier-R19-U10-aws-call1.log`
- Side metrics: `compact_v5/_status/r-tier-R19-U10-aws-call1-side-metrics.json`
- Telemetry: `compact_v5/_status/r-tier-R19-U10-aws-call1-telemetry.json`
- Audit directory: `compact_v5/_status/r_tier_runtime/R19-U10-call1-audit/`
- Runner: `compact_v5/MAIN/agent/tests/r_tier/test_r19_u10_long_coherence.py`

## Artifact Quality

Conclusion: NEAR_IDEAL

- Model: `au.anthropic.claude-haiku-4-5-20251001-v1:0`.
- Cost: `$0.0134`, below the `$0.50` planned cap and `$0.60` hard ceiling.
- The final report was created by one `write_file` call.
- Required markers all appeared:
  - `CODENAME: HYDRA-LIME`
  - `CHECKSUM: kiwi-1842`
  - `RUNTIME: Python 3.12`
  - `OWNER: Priya`
  - `FINAL_TASK: create_coherence_report`
- The stale `Python 3.10` preference did not win; the report used the latest `Python 3.12` preference.
- The final task depended on early/prebuilt context anchors and latest override facts, not on a broad file search.

## Process Quality

Conclusion: NEAR_IDEAL

- Tool order was minimal: `write_file`.
- Tool calls: `1`.
- Repeated tool calls: `0`.
- Failure-loop events: `0`.
- Guard failure classes: `{}`.
- Stop reason: `user_stop`; `max_turns` was not hit.
- The R14/R19-U3 repeated guard/edit/write/exec loop did not recur.
- The model did not ask for clarification or drift from the final task.

## Long-Coherence Evidence

- `logical_turns_represented=150`.
- `prebuilt_transcript_used=true`.
- `model_switch_events_logged=2`.
- `compaction_events_logged=3`.
- Telemetry includes three typed `compact_auto_end` events with `path="prebuilt_transcript"`.
- Telemetry includes two `model_switch_events`:
  - Haiku 4.5 AU -> Sonnet 4.5 AU at logical turn 47.
  - Sonnet 4.5 AU -> Haiku 4.5 AU at logical turn 104.
- Telemetry has one non-empty `per_turn` record, one tool call, and completed outcome.

## Cache / Cost Evidence

Cache evidence is numeric:

- `cache_read_tokens=0`
- `cache_write_tokens=8962`
- `cache_hit_pct=0.0`

No `MODEL_LIMITATION` row is needed because Bedrock usage exposed cache fields. The zero cache-read value is expected for this single real call against a fresh prebuilt transcript.

## Substitution Caveats

This run does not prove 150 live Bedrock calls, live model switching, or natural threshold-triggered compaction. It proves the optimized-plan substitution:

- 150 logical turns are represented by a prebuilt compacted transcript fixture.
- Model switches are fixture audit events with `path="prebuilt_transcript"`.
- Compactions are typed fixture audit events with `path="prebuilt_transcript"`.

This matches the approved R19-U10 Phase A design and the optimized plan's cost-cap rule. Do not overclaim this as a full live 150-turn, multi-model, naturally compacting session.

## Evidence-Capture Note

After R16, `build_telemetry.py` was fixed to read all JSONL files in an audit directory. R19-U10 also added canonical extraction of `model_switch_events` so Phase C can review model-switch fixture evidence from telemetry, not only from side metrics or raw audit files.

Zero-cost checks after the R19-U10 telemetry extractor:

- `py -3.11 -m py_compile compact_v5/_status/scripts/build_telemetry.py compact_v5/MAIN/agent/tests/r_tier/test_r19_u10_long_coherence.py`: PASS
- `py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_build_telemetry.py -q`: 11 passed
- `py -3.11 -m pytest compact_v5/MAIN/agent/tests/r_tier/test_r19_u10_long_coherence.py -q`: 1 skipped without `RUN_REAL_BEDROCK`

## Readiness Judgment

R19-U10 call1 is a genuine artifact and process-quality pass for the bounded prebuilt long-coherence scenario. It is acceptable as a production-readiness signal only for the optimized substitution described above, subject to independent Claude Phase C review and `r_tier_gate.py --test R19-U10`.
