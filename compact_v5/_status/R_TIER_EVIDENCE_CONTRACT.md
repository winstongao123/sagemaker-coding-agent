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
| Quality review | `_status/r-tier-<TEST>-aws-call<N>-quality.md` | Functional result and process result graded separately; no `SEMANTIC_BUG_DETECTED`; no unresolved critical process-quality blocker |
| Metrics ledger | `_status/r_tier_metrics.jsonl` | One row per AWS call with cost/tokens/cache/tool counts, including reviewer/subagent attribution when used |
| Review ledger | `_status/r_tier_review_log.md` | One READY or ESCALATED row per test |
| Escalation | `_status/codex_reviews/ESCALATION-<TEST>.md` | Required if any stop trigger fires |

## Selected-Test Evidence Additions

These fields prevent software-builder tests from passing on prose alone:

| Test | Additional required evidence |
|---|---|
| R13 | Metrics or quality evidence must include `score_total=5`, `score_passed>=4`, and `changed_files_within_fixture=true`. A scored failure is allowed only as an escalated/fix-loop result, not as a READY pass. |
| R14 | Evidence must use Haiku 4.5 AU, include `changed_files_within_fixture=true`, stale-symbol grep output, a fixture note that visible call sites are present, visible read/search before edit, tool-count/failure-loop telemetry, and process-quality review of read-before-edit/write/exec guard failures. A correct artifact alone is not READY. |
| R15 | Evidence must include pre-fix failing-test output, post-fix passing-test output, `false_positive_area_unchanged=true`, and diagnosis trace. |
| R16 | Telemetry must include a typed `software_builder_subchecks` object with all required keys listed below. |
| R19-U1 | Evidence must include `clarification_request_count>=1` and `changed_files_count=0`. |
| R19-U2 | Evidence must include `conflict_detected=true`, `clarification_request_count>=1`, and no speculative edit. |
| R19-U3 | Evidence must use Haiku 4.5 AU, include search-before-edit ordering, fixture orthogonality from R14, tool-count/failure-loop telemetry, and no non-intentional repeated read-before-edit/write or exec failure loop. A correct artifact alone is not READY. |
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
- process-quality counters or summaries for repeated calls, blocked/failed
  tool calls, search-before-edit behavior, unexpected edits, recovery path,
  and artifact verification where the runner can observe them
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

- the matrix `cost_cap_usd` remains the planned per-test budget;
- the hard local retry ceiling is the planned cap plus the user-approved 20%
  buffer (`cost_cap_usd * 1.20`);
- cumulative spend must be preserved in `r_tier_metrics.jsonl`, side metrics,
  raw logs, and review logs. Do not delete, rewrite, hide, or reset failed
  diagnostic spend to fit under the cap;
- if a retry needs the 20% buffer, the Phase A or Phase B record must say why
  the earlier call was diagnostic/non-ready and why the retry is expected to
  stay below the buffered ceiling;
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

Quality review must grade artifact quality and process quality separately.

Artifact quality must grade:

1. Correctness of the produced software or answer
2. Test/assertion strength
3. Absence of unrelated edits
4. Final verification quality

Process quality must grade:

1. Tool choice optimality
2. Path efficiency
3. Reasoning soundness
4. Resource utilization
5. Wasted calls
6. Outcome quality
7. Context/status/memory/checkpoint continuity when applicable
8. Subagent/reviewer coordination and attribution when applicable
9. Recovery discipline after failed, blocked, or malformed tool results

The review must explicitly state whether a functional pass is also acceptable
as a production-readiness signal. A run can be a genuine artifact pass while
still opening a production-readiness follow-up.

Accepted conclusions:

- `NEAR_IDEAL`
- `WORKING_BUT_SUBOPTIMAL` only if the weakness is bounded, non-recurring, and
  either fixed immediately or tracked in
  `_status/R_TIER_PROCESS_QUALITY_FOLLOWUPS.md`

Process-risk conclusions:

- `INEFFICIENT_PROCESS_FOLLOWUP_REQUIRED` if the output is correct but tool
  loops, wasted calls, weak coordination, missing attribution, or context/memory
  weakness must be fixed or explicitly accepted before final readiness
- `PROCESS_BLOCKER` if the behavior would make v5 unsafe or unreliable for
  long-running software work

Guard-loop rule:

- Repeated `edit_file`/`write_file` read-before-mutate failures, blocked `cd`
  variants, or repeated failing `python_exec` attempts are not "fine" merely
  because the final artifact is correct.
- If the run shows a non-intentional guard-class loop after the 2026-05-06
  R14/R19-U3 fix, classify process quality as `PROCESS_BLOCKER` and stop the
  matrix.
- R14 and R19-U3 retries must prove Haiku can pass with acceptable process
  quality. Do not bypass the blocker by switching those tests to Sonnet.
- Quality reviews must explicitly inspect model id, tool count, failure-loop
  count, guard failure classes, and visible read/search-before-edit ordering
  where applicable.
- Historical diagnostic/non-ready metrics rows must remain in
  `r_tier_metrics.jsonl` and continue to count toward cumulative spend. A later
  READY gate may pass only when there is also a completed `GENUINE_PASS`/`READY`
  metrics row for the test.
- The intentional R19-U7 repeated-call fixture is exempt only for its
  deterministic bait tool; any unrelated repeated guard-class loop in that run
  is still blocking.

Blocking conclusion:

- `SEMANTIC_BUG_DETECTED`
- `PROCESS_BLOCKER`

If `INEFFICIENT_PROCESS_FOLLOWUP_REQUIRED` appears, the test may remain a
genuine functional pass, but final production readiness is blocked until the
follow-up is resolved, explicitly accepted by the user, or promoted into
implementation work and retested.

## Validation

Run before advancing:

```bash
py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root . --test <TEST>
```

If the gate fails, the worker must not advance to the next test.
