# R11 Phase A Independent Review

## Verdict: APPROVE_FOR_AWS_CALL

Independently read on disk:
- `compact_v5/MAIN/agent/tests/r_tier/test_r11_sonnet_e2e.py` (286 lines)
- `compact_v5/MAIN/agent/tests/r_tier/test_r1_dashboard.py` (R1 baseline, 264 lines)
- `compact_v5/_status/r_tier_test_matrix.json` (R11 row: Sonnet 4.5 AU, $1.50 cap, EXECUTABLE_PENDING_REVIEW)
- `compact_v5/_status/R_TIER_EVIDENCE_CONTRACT.md`
- `compact_v5/_status/v5_completion_audit/PS_AWS_TEST_EXECUTION_LOOP.md`
- `compact_v5/MAIN/agent/runtime/tokens.py:538-540` (`is_over_budget`)
- `compact_v5/MAIN/agent/agent.py:98-139` (`max_turns` + `on_stop_check`)

Both prior `r-tier-R11-phaseA-iter1.md` and `.err.log` are empty (1 line) — this is a fresh review.

## Genuine-Sonnet workflow (pass)

Lines `test_r11_sonnet_e2e.py:35,131,143`: model id `au.anthropic.claude-sonnet-4-5-20250929-v1:0` is set on `CONFIG.model_id` *and* passed directly to `BedrockClient(...)` with `mock_mode=False`. Real-AWS gating at line 84-87 (`RUN_REAL_BEDROCK`). The prompt at lines 48-61 is the same R1 composite (read CSV → summarize → bar-chart PNG → Word report) — the test exercises the full tool/artifact loop, not just chat or thinking.

## Stub-defense on artifacts (pass)

Lines 155-173 enforce:
- `chart.png`: file exists, first 4 bytes == `\x89PNG`, size ≥ 1000 bytes (matplotlib bar charts of 5 points produce ≥5KB; a stub PNG is a few hundred bytes).
- `report.docx`: file exists, `zipfile.is_zipfile`, `word/document.xml` present, contains `Sales Report` heading, contains ≥1 CSV category from {Electronics, Apparel, Books, Toys, Garden}, contains either total `21400`/`21,400` or top-2 `14000`/`14,000`.

These are the same body-content checks R1 added in its iter-1 fix and are difficult to fake without performing the real CSV math. Lines 251-261 also assert `stop_reason != "max_turns"` and forbid any `tool_failure_loop_*` audit events.

## Cost / hard-halt controls (pass, with note)

- `max_tokens = 2048` (line 132) — caps per-turn output, same as R1.
- `max_turns = 35` (line 150) — more conservative than R1's 50.
- `enable_prompt_cache = True` (line 136).
- `_hard_cost_halt` (lines 145-148) calls `TOKENS.is_over_budget()`, which compares `session_cost` against `CONFIG.session_cost_limit` set at line 130 to `_R11_HARD_CEILING_USD = 1.80`.
- Final assertion (lines 263-266) checks `cost_used <= _R11_HARD_CEILING_USD`.

Sonnet 4.5 worst-case per-turn output ≈ 2048 × $15/MTok ≈ $0.031, so 35 turns of pure-output ≈ $1.07 plus input — $1.50 planned cap is plausible and $1.80 ceiling has real headroom.

**Note (non-blocking)**: R11 sets the hard halt at the *buffered ceiling* ($1.80), unlike R1 which halts at the planned cap ($1.00). This is consistent with the user's explicit authorization in the prompt ("Hard retry ceiling: $1.80 under the user-approved +20% retry buffer") and with `R_TIER_EVIDENCE_CONTRACT.md` §"Bundle And Retry Policy". Acceptable, but post-run quality review should confirm cost stayed under planned cap on first call; if first call lands between $1.50 and $1.80, that is `cost-cap-hit` and counts as one failed attempt under the contract.

## Overlap analysis (pass)

- R1 (Haiku 4.5 AU) — composite workflow on the cheap model only.
- R7 (Haiku→Sonnet) — switch + cache only, no tools, no artifacts.
- R17 (Sonnet) — thinking visibility only, no tools, no artifacts.
- R11 — only row exercising the *full tool/artifact loop on the production Sonnet*. Non-redundant.

## Scope / batching (pass)

The runner is a single `pytest.mark.skipif`-gated function in a dedicated file. The proposed command (`pytest compact_v5/MAIN/agent/tests/r_tier/test_r11_sonnet_e2e.py -q`) targets only this file and cannot batch other AWS rows. CONFIG/SECURITY/cwd are saved and restored in `finally` (lines 268-285).

## Evidence plan (pass, with two follow-ups for Phase C)

The runner writes:
- `compact_v5/_status/r_tier_runtime/R11-call{call}-audit/*.jsonl` — via `AUDIT.__init__(audit_dir=...)` at line 138 ✓
- `compact_v5/_status/r-tier-R11-aws-call{call}-side-metrics.json` — line 246 ✓ (covers metrics-ledger keys: model, tokens, cache, cost, tool_calls, subagent/reviewer attribution=0, completed, verdict, model_usage, failure_loop_events, process_quality_ok, audit_dir).

The runner does **not** itself write:
- `r-tier-R11-aws-call1-telemetry.json` (per-turn / tool_call_summary / outcome) — same gap as R1; outer harness must produce it from the audit jsonl after the run.
- `r-tier-R11-aws-call1-quality.md`, `r-tier-R11-phaseC-iter1.md`, `r_tier_metrics.jsonl` row, `r_tier_review_log.md` row, `r-tier-R11-gate.txt` — all worker/Claude responsibilities post-run.

Phase C must confirm those exist before declaring R11 ready; that is an evidence-contract requirement, not a runner defect.

## Minor caveats (non-blocking)

1. `AUDIT.__init__(audit_dir=...)` at line 138 is not symmetrically restored. Acceptable for a standalone real-AWS run; flag if future tests share a process.
2. `cache_hit_pct = session_cache_read / max(1, session_input)` (line 207) is a ratio not a percentage despite the name — quality review should not be misled.
3. `SECURITY` rebuild at line 137 is restored only via assignment (line 285), same pattern as R1.

## Decision

`APPROVE_FOR_AWS_CALL`

Conditions for the spend:
- Run only `test_r11_sonnet_e2e.py` with `RUN_REAL_BEDROCK=1 R_TIER_CALL=1 AWS_REGION=ap-southeast-2`.
- Tee full stdout/stderr to `compact_v5/_status/codex_reviews/r-tier-R11-aws-call1.log`.
- After the run, the worker (not the runner) must write `r-tier-R11-aws-call1-telemetry.json`, `-quality.md`, the metrics-ledger row, the review-log row, the gate file, and Phase C `r-tier-R11-phaseC-iter1.md` returning `GENUINE_PASS`.
- Phase C must verify: cost stayed at or under $1.50 on first call (cost between $1.50 and $1.80 is a cost-cap-hit retry, per contract); `failure_loop_events == 0`; tool dispatch sequence shows real read_file → python_exec/create_chart → create_word; docx body assertions pass on the real artifact.
