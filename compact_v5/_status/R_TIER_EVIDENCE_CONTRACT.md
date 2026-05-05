# R-tier Evidence Contract

Date: 2026-05-03

Purpose: define exactly what evidence must exist before any R-tier scenario can
be called READY.

## Required Evidence Per Test

| Evidence | Required file | Must contain |
|---|---|---|
| Pre-flight prompt | `_status/codex_reviews/r-tier-<TEST>-phaseA-iter<N>-prompt.txt` | Filled TEMPLATE A with all placeholders replaced |
| Pre-flight review | `_status/codex_reviews/r-tier-<TEST>-phaseA-iter<N>.md` | `APPROVE_FOR_AWS_CALL` before spend |
| Raw run log | `_status/codex_reviews/r-tier-<TEST>-aws-call<N>.log` | Full stdout/stderr from pytest run via tee |
| Failure diagnosis | `_status/codex_reviews/r-tier-<TEST>-phaseB-iter<N>.md` | Required only on failure; must approve retry fix |
| Post-pass review | `_status/codex_reviews/r-tier-<TEST>-phaseC-iter<N>.md` | `GENUINE_PASS` |
| Telemetry | `_status/r-tier-<TEST>-aws-call<N>-telemetry.json` | Required schema, non-empty `per_turn`, completed outcome |
| Quality review | `_status/r-tier-<TEST>-aws-call<N>-quality.md` | Worker + Codex 6-axis grade; no `SEMANTIC_BUG_DETECTED` |
| Metrics ledger | `_status/r_tier_metrics.jsonl` | One row per AWS call with cost/tokens/cache/tool counts, including reviewer/subagent attribution when used |
| Review ledger | `_status/r_tier_review_log.md` | One READY or ESCALATED row per test |
| Escalation | `_status/codex_reviews/ESCALATION-<TEST>.md` | Required if any stop trigger fires |

## Selected-Test Evidence Additions

These fields prevent software-builder tests from passing on prose alone:

| Test | Additional required evidence |
|---|---|
| R13 | Metrics or quality evidence must include `score_total=5`, `score_passed>=4`, and `changed_files_within_fixture=true`. A scored failure is allowed only as an escalated/fix-loop result, not as a READY pass. |
| R14 | Evidence must include `changed_files_within_fixture=true`, stale-symbol grep output, and a fixture note that visible call sites are present. |
| R15 | Evidence must include pre-fix failing-test output, post-fix passing-test output, `false_positive_area_unchanged=true`, and diagnosis trace. |
| R16 | Telemetry must include a typed `software_builder_subchecks` object with all required keys listed below. |
| R19-U1 | Evidence must include `clarification_request_count>=1` and `changed_files_count=0`. |
| R19-U2 | Evidence must include `conflict_detected=true`, `clarification_request_count>=1`, and no speculative edit. |
| R19-U3 | Evidence must include search-before-edit ordering and fixture orthogonality from R14. |
| R19-U6 | Evidence must name the fixture-controlled malformed-output injection and recovery path. |
| R19-U7 | Evidence must include `breaker_fired=true` from a deterministic repeated-call bait fixture unless the run is explicitly escalated as "model recovered before breaker could be tested." |
| R19-U10 | Evidence must include a deterministic final-task anchor that depends on information inserted before compaction/churn, and Phase A must confirm use of the prebuilt transcript/churn fixture unless the user approves a higher cap. |

Required R16 `software_builder_subchecks` keys:

```json
{
  "status_round_trip": true,
  "todo_round_trip": true,
  "named_checkpoint_round_trip": true,
  "verify_done_stale_evidence_blocked": true,
  "compaction_event_emitted": true,
  "cache_evidence_recorded": true,
  "cost_context_reported": true,
  "final_artifact_quality_passed": true
}
```

If `SOFTWARE-SHELL` ships background job lifecycle before R16 runs, R16 must
also include:

```json
{
  "background_shell_start_poll_kill": true
}
```

Cache evidence limitation row template:

```json
{
  "test": "R16",
  "cache_evidence_status": "MODEL_LIMITATION",
  "model": "claude-haiku-4-5",
  "missing_fields": ["cache_read_input_tokens"],
  "explanation": "Bedrock/model response did not expose cache read/write fields for this run.",
  "fallback_evidence": "prompt cache blocks emitted and telemetry recorded zero/unknown explicitly"
}
```

Do not leave cache fields silently blank. Use numeric evidence when available;
otherwise write the explicit limitation row above.
Before writing `MODEL_LIMITATION`, inspect the raw Bedrock/model response
payload for the relevant cache field names and cite the missing-field evidence
in the telemetry or quality review. A capture bug is not a model limitation.

## Required Metrics JSONL Keys

Every `_status/r_tier_metrics.jsonl` row must include:

```json
{
  "test": "R1",
  "call": 1,
  "date": "2026-05-03T00:00:00Z",
  "model": "claude-haiku-4-5",
  "tokens_in": 0,
  "tokens_out": 0,
  "cache_hit_pct": 0.0,
  "wallclock_s": 0.0,
  "tool_calls": 0,
  "subagent_calls": 0,
  "reviewer_calls": 0,
  "subagent_tokens_in": 0,
  "subagent_tokens_out": 0,
  "subagent_cost_usd": 0.0,
  "reviewer_tokens_in": 0,
  "reviewer_tokens_out": 0,
  "reviewer_cost_usd": 0.0,
  "changed_files_within_fixture": true,
  "score_passed": null,
  "score_total": null,
  "completed": true,
  "cost_usd": 0.0,
  "verdict": "GENUINE_PASS"
}
```

Valid pass verdicts: `GENUINE_PASS`, `READY`.

## Required Telemetry Keys

Every telemetry JSON must include:

- `test`
- `call`
- `per_turn`
- `tool_call_summary`
- `compaction_events`
- `subagent_dispatches`
- `cache_efficiency_trend`
- `outcome`
- `software_builder_subchecks` for R16
- reviewer/subagent attribution when the scenario uses `task`,
  `subagent_type="review"`, `subagent_type="verify"`, or any other worker
  role. The attribution must include token/cost/cache evidence from
  `TokenTracker.get_stats()` or `TokenTracker.get_otel_counters()`.

For READY tests:

- `per_turn` must be non-empty
- `outcome.completed` must be `true`
- `outcome.cost_cap_hit` must not be `true`

For tests that use a reviewer/subagent:

- `/cost` or equivalent metrics must show parent and subagent/reviewer cost
  buckets separately.
- telemetry must include `subagent_dispatches`.
- quality review must judge whether the delegation was useful or wasteful.

## Bundle And Retry Policy

Bundled AWS runs are allowed only when the plan explicitly says the bundle is
high-signal and non-overlapping.

- R19-U1+R19-U2 may run as one Stage 4 ambiguity/contradiction bundle.
- R19-U3+R19-U6+R19-U7+R18-E7 may run as one Stage 5 recovery/results bundle.
- R3+R19-U4+R19-U5 may run as one Stage 6 subagent/reviewer bundle.
- The cost cap for a bundled run is the sum of the member test caps.
- The raw log may use a bundle name such as
  `_status/codex_reviews/r-tier-R19-U1+U2-aws-call1.log`.
- Per-test telemetry, metrics, quality, and review-log evidence must still be
  written for each member test id, or the bundle does not satisfy the gate.

Real Bedrock can be nondeterministic. Default policy:

- one Phase C `GENUINE_PASS` is sufficient for low-risk, deterministic
  scenarios if all telemetry and quality evidence is clean;
- rerun once when quality review flags flakiness, marginal pass, unexplained
  tool loops, missing cache/compaction evidence, or borderline token/cost
  behavior;
- cost-cap-hit counts as one failed attempt unless the run stopped before any
  model call due preflight budget refusal;
- after 3 unsuccessful meaningful fix/retry attempts on the same test or
  bundle, stop and write `ESCALATION-<TEST>.md`.

## Quality Review

Quality review must grade:

1. Tool choice optimality
2. Path efficiency
3. Reasoning soundness
4. Resource utilization
5. Wasted calls
6. Outcome quality

Accepted conclusions:

- `NEAR_IDEAL`
- `WORKING_BUT_SUBOPTIMAL`
- `INEFFICIENT` if the output is correct and no semantic bug exists

Blocking conclusion:

- `SEMANTIC_BUG_DETECTED`

## Validation

Run before advancing:

```bash
py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root . --test <TEST>
```

If the gate fails, the worker must not advance to the next test.
