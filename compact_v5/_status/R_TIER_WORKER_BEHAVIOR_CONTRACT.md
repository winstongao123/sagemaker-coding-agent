# R-tier Worker Behavior Contract

Date: 2026-05-03

Purpose: keep an autonomous worker aligned with the user's goals while the user
is AFK.

## Non-negotiable Behavior

| Rule | Worker behavior |
|---|---|
| v5 only | Do not run v4 or Runnable; no comparative AWS spend |
| Minimum spend | Use Haiku by default, mock where specified, low max turns, capped output |
| No blind AWS | Phase A approval required before every AWS call |
| No silent pass | Phase C and quality review required after every pass |
| No silent bug | Any semantic bug writes escalation and stops |
| No missing evidence | Gate must pass before moving to next test |
| No drift | Status, metrics, review log, matrix, and git must be updated every step |
| No local-only work | Every completed step/test/fix is committed and pushed |

## Step Status Protocol

Before starting a test, update:

- `_status/R_TIER_GATE_STATUS.md`
- `_status/r_tier_test_matrix.json` status field
- `_status/R_TIER_PENDING_TESTS.md` if human-readable status changes

After an AWS call, update:

- raw call log
- telemetry JSON
- quality review
- metrics JSONL
- review log
- gate status

After any fix, update:

- code
- lock test
- diagnosis review
- build/status notes
- commit and push

## Git Protocol

After each completed step:

```bash
git status --short
git add <changed files>
git commit -m "v5/r-tier-<TEST>: <concise status>"
git push sageagent v5-build
```

Do not include unrelated dirty files. Current known unrelated dirty item:

- `_archive/compare_code/gg-claude-code-runnable`

## Cost Protocol

Before every AWS call:

```bash
aws budgets describe-budget --account-id 903039434627 --budget-name Bedrock-Monthly-50
py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root . --skip-suite
```

Proceed only if:

- AWS actual spend `< $40`
- AWS forecast spend `< $40`
- local total + next scenario cap `<= $14.25`

## Stop Protocol

If a stop trigger fires:

1. Write `_status/codex_reviews/ESCALATION-<TEST>.md`
2. Add an `ESCALATED` row to `_status/r_tier_review_log.md`
3. Update matrix/status docs
4. Commit
5. Push
6. Stop for user

Never continue after escalation without user approval.
