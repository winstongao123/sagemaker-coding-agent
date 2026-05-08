I've read all eight files from disk. Let me deliver the verdict.

# Phase A Review — R19-U10 Long Coherence (AWS call1)

## Verdict

**APPROVE_FOR_AWS_CALL**

## Evidence-of-fit checks (PASS)

1. **Plan-allowed substitution.** `OPTIMIZED_AWS_VALIDATION_PLAN.md:101` and `R_TIER_EVIDENCE_CONTRACT.md:38` explicitly authorize representing 150 logical turns via a prebuilt transcript/churn fixture under the $0.50 cap. The Phase A prompt and the test `_PROMPT` honestly disclose the substitution; the runner emits typed `compact_auto_end` audit events with `parameters.path="prebuilt_transcript"` and matching `model_switch` events tagged `prebuilt_transcript` (`test_r19_u10_long_coherence.py:264-295`). No covert "natural compaction" claim.

2. **Anchors are recoverable purely from the seeded transcript.** Each of the five required outputs maps to a literal anchor in `_prebuilt_messages()`:
   - HYDRA-LIME, kiwi-1842 → turn-1 user message + first compaction summary
   - Python 3.12 (with explicit "Python 3.10 is stale") and Priya → second compaction summary
   - create_coherence_report → third compaction summary
   
   So the test does not require the model to read fixture files; it only needs to honor the transcript. AGENT_STATUS.md/memory.md add redundancy but are not load-bearing.

3. **Cost containment.** `CONFIG.session_cost_limit = $0.60` (hard ceiling), `max_turns=4`, `IterationBudget(max_iterations=8)`, `CONFIG.max_tokens=1024`, and `on_stop_check=_hard_cost_halt` short-circuit when over budget OR when all five markers are present. Haiku 4.5 AU at this turn budget is well under the $0.50 plan; the 1.20× hard ceiling matches the documented retry-buffer policy.

4. **Test isolation.** Saves and restores `CONFIG.workspace`, `audit_dir`, `session_cost_limit`, `model_id`, `max_tokens`, `require_tool_approval`, `disable_local_traces`, `status_doc`, `SECURITY`, `SESSIONS`, `SNAPSHOTS`, and `cwd`. `TOKENS.reset()` and `AUDIT.__init__(audit_dir=...)` re-scope to the per-call audit dir. Workspace is `tmp_path`.

5. **Recurrence watch for R14/R19-U3 holds.** `process_quality_ok` requires `not repeated_guard_loop` (any guard class with `>=2` failures), `stop_reason != "max_turns"`, `len(order) <= 8`, and `len(failure_events) == 0`. This satisfies the recurrence-watch policy in `R_TIER_PROCESS_QUALITY_FOLLOWUPS.md:79-82`.

6. **Telemetry integrity.** `telemetry_ok` requires exactly 2 `model_switch` events, `>=3` `compact_auto_end` events, and `>=19` agent messages. With 18 prebuilt messages plus the user prompt, the messages bound is satisfied immediately. `build_telemetry.py` already aggregates JSONL events from a directory (`test_build_telemetry.py:152-194` proves this), so the audit dir → canonical telemetry path is exercised by lock tests.

7. **Local gates pass.** Worker reports `py_compile` PASS, AWS-gated pytest skipped correctly, and `test_build_telemetry.py` 10/10. Imports in the R-tier test resolve cleanly under `PYTHONPATH=compact_v5/MAIN/agent`.

8. **Cap, model, and stop conditions match the plan.** Haiku 4.5 AU only, planned $0.50, hard ceiling $0.60, no Sonnet escalation. Stop conditions in the prompt (max_turns, stale-pref override, guard-loop recurrence, missing anchor, missing evidence file) all map to assertions or to the post-run worker review.

## Non-blocking flags for the worker post-run

- The runner writes side-metrics inline; the canonical `r-tier-R19-U10-aws-call1-telemetry.json` must be built afterwards by running `build_telemetry.py` against `compact_v5/_status/r_tier_runtime/R19-U10-call1-audit/`. Phase C must verify it has non-empty `per_turn` and the typed compaction events.
- Phase C quality review must explicitly call out that the model-switch and compaction events are `path="prebuilt_transcript"` substitutions, not natural events, to prevent silent morphing of the claim.
- `agent._engine.messages = _prebuilt_messages()` uses a private attribute; if Block-V refactors `_engine.messages`, regenerate the seeding path before re-running.
- `_hard_cost_halt` re-reads `final_coherence_report.md` each check. Acceptable; bounded by `max_turns=4`.

## Safe-to-spend checklist

- [x] Phase A design honest about substitutions
- [x] Anchors solvable from prebuilt transcript alone
- [x] Cost ceiling enforced in CONFIG and runner halt
- [x] Process-quality (R14/R19-U3 recurrence) enforced
- [x] Required evidence files declared
- [x] Local zero-cost gates green
- [x] Cap, model, max_turns, max_tokens consistent with plan

**APPROVE_FOR_AWS_CALL** — proceed to user budget/headroom check, then the documented AWS command. Stop and escalate if any of the prompt's stop conditions trigger.


