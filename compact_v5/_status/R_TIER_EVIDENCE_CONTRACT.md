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
| Metrics ledger | `_status/r_tier_metrics.jsonl` | One row per AWS call with cost/tokens/cache/tool counts |
| Review ledger | `_status/r_tier_review_log.md` | One READY or ESCALATED row per test |
| Escalation | `_status/codex_reviews/ESCALATION-<TEST>.md` | Required if any stop trigger fires |

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

For READY tests:

- `per_turn` must be non-empty
- `outcome.completed` must be `true`
- `outcome.cost_cap_hit` must not be `true`

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
