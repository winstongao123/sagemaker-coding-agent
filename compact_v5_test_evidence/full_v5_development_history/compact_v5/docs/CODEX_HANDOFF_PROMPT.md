# CODEX HANDOFF PROMPT — v5.0.1 R-tier Real-AWS Testing

**Copy everything below this line and paste into Codex CLI.**

---

# YOUR JOB

You are taking over from Claude Code. You will execute 42 real-AWS tests against `sagemaker-coding-agent v5.0.1` to validate it is production-ready for single-user SageMaker deployment. You will produce hard evidence that v5 has no semantic bugs, handles real coding workflows correctly, and survives realistic user-experience edge cases.

Cost cap: **$14.25 USD** (well under the $50/mo AWS Budget hard stop).

# WHY WE'RE DOING THIS

`v5.0.1` was built across 21 incremental Blocks (Block 0 → K) by Claude Code with you (Codex) reviewing every Block. 50 Codex APPROVE iterations. 798 mock tests passing. All 7 documented production problems from v4.10.10 ("PS#1-7") are structurally fixed with lock tests preventing regression.

But mock tests don't prove v5 works on real Bedrock. The user wants empirical evidence v5 is production-ready before shipping. That evidence comes from running 42 carefully-designed test scenarios on actual AWS Bedrock and grading the results.

The user also explicitly wants:
- Both YOU (Codex) AND Claude Code (worker) to review every test result before advancing
- Full diagnostic logs captured per test (telemetry, tool use, sub-agent coordination, memory state, context management)
- Iterative fix-and-retest loop when bugs are found
- Hard evidence persisted in git (no claims without file:line refs)
- Block V (head-to-head v4 vs v5) DROPPED to save money — v5-only validation
- ~99% confidence on v5 itself; "v5 > v4 > Runnable" stays architectural per PORT_LOG file:line refs

# HOW TO DO IT

## Step 1: Pull latest + verify state

```bash
cd D:/Github/sagemaker-coding-agent
git pull sageagent v5-build
git log --oneline -5      # latest should be d82c530 (CODEX_CONTEXT) or later
git tag -l "v5.0.1-block-*" | wc -l    # should be 21
cd compact_v5/MAIN/agent && pytest tests/ -q | tail -3   # 775 pass + 17 skip
```

If any of these check fails → STOP, report drift to user. Do NOT proceed.

## Step 2: Read these files BEFORE writing any test (in this order)

1. `compact_v5/docs/CODEX_CONTEXT_v5_R_TIER.md` — your full context
2. `compact_v5/docs/PS_V5_TEST_PLAYBOOK.md` — MASTER spec for all 42 tests (§4.1-§4.6)
3. `compact_v5/docs/PS_V5_TEST_SET.md` — TL;DR test catalog
4. `compact_v5/_phase_2/wave_6/WORKER_HINT_2026-05-03.md` — supersedes BUILDER_PROMPT on conflict
5. `compact_v5/_status/R_TIER_REVIEW_TEMPLATE.md` — your review prompt templates A/B/C
6. `compact_v5/_status/V5_BUILD_STATUS.md` — current state
7. `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` — every Runnable pattern ported (file:line refs)

## Step 3: The 42 tests in execution order

```
R1   composite dashboard build              real-AWS  $1.00
R2   80K context compact + cache_edits      real-AWS  $0.50
R3   3 parallel sub-agents                  real-AWS  $0.50
R4   30-min cold-cache compact              real-AWS  $0.20  (PS#3)
R5   200-bash exec + recovery               real-AWS  $0.50  (PS#7)
R6   /dream consolidation 100 entries       real-AWS  $0.30  (Block H+)
R7   mid-conv Haiku→Sonnet model switch     real-AWS  $0.50  (Hermes A28)
R8   malformed JSON repair                  MOCK      $0     (Block C)
R9   approval flow end-to-end               real-AWS  $0.30  (Block C+)
R10  save→restart→load cost intact          real-AWS  $1.00  (PS#5/6)
R11  Sonnet 4.5 end-to-end                  real-AWS  $1.50
R12  malformed args + Unicode               real-AWS  $0.20  (Block L+H)
R13  5 HumanEval Python problems            real-AWS  $0.50  (coding accuracy)
R14  3-file refactor + pytest green         real-AWS  $0.75  (multi-file)
R15  find+fix 2 planted bugs                real-AWS  $0.50  (debug)
R16  100-turn Flask CRUD build              real-AWS  $1.00  (long-session)
R17  thinking visibility on Sonnet          real-AWS  $0.30  (PS#4)
R18  15 INFRASTRUCTURE edges (4 mock+11 real) mixed  $1.60
R19  10 USER-EXPERIENCE edges               real-AWS  $3.10  (CRITICAL — see below)
                                            TOTAL    $14.25
```

## Step 4: R19 details (the critical UX battery)

These are real-world scenarios that affect user experience — not infrastructure failures:

| # | UX edge | What v5 SHOULD do |
|---|---|---|
| U1 | User says "make this code better" (ambiguous) | Ask clarifying via ask_user, NOT assume |
| U2 | User specs "use REST AND GraphQL" (contradictory) | Recognize conflict, flag to user |
| U3 | Refactor 5-file project where file 5 has hidden inheritance dep | grep BEFORE changing, not blind edit |
| U4 | 3 sub-agents return conflicting findings | Parent reconciles correctly, not blind majority |
| U5 | One sub-agent fails mid-task | Parent recovers + completes with remaining 2 |
| U6 | python_exec returns malformed JSON | Recover via re-call or alternative tool |
| U7 | Agent stuck calling same tool 3+ times | Circuit breaker fires + tries alternative |
| U8 | Memory says "use Python 3.10" then later "use Python 3.12" | /dream resolves; agent uses latest |
| U9 | /dream consolidates 50 entries with duplicates + outdated info | NOTHING important is lost (semantic check) |
| U10 | 150-turn session + 2 model switches + 3 compactions | Stays coherent, final task succeeds |

## Step 5: Per-test discipline (10 MANDATORY output files per test)

For each R-test, you MUST produce all 10 of these. If any missing → test INCOMPLETE → DO NOT advance:

```
1. _status/codex_reviews/r-tier-<TEST>-phaseA-iter<N>-prompt.txt   (your pre-flight prompt, filled-in TEMPLATE A)
2. _status/codex_reviews/r-tier-<TEST>-phaseA-iter<N>.md           (your pre-flight verdict)
3. _status/codex_reviews/r-tier-<TEST>-aws-call<N>.log             (raw Bedrock log via tee)
4. _status/codex_reviews/r-tier-<TEST>-phaseB-iter<N>.md           (diagnosis IF failed)
5. _status/codex_reviews/r-tier-<TEST>-phaseC-iter<N>.md           (post-pass sanity)
6. _status/r_tier_metrics.jsonl                                    (one JSONL row per AWS call)
7. _status/r_tier_review_log.md                                    (one row per test)
8. _status/codex_reviews/ESCALATION-<TEST>.md                      (IF cap hit or BUG)
9. _status/r-tier-<TEST>-aws-call<N>-telemetry.json                (per-turn breakdown)
10. _status/r-tier-<TEST>-aws-call<N>-quality.md                   (worker + Codex 6-axis grade)
```

## Step 6: The test → review → fix → review → ready loop (PER TEST)

```
PHASE A — PRE-FLIGHT (free, no AWS spent):
  - You write/inspect the test code
  - You self-review (read your own changes)
  - You run Codex AXIS A/B/C review (TEMPLATE A from R_TIER_REVIEW_TEMPLATE.md)
  - You + Codex BOTH must APPROVE_FOR_AWS_CALL → AWS gate OPENS
  - If REJECT → fix issues → re-PHASE A (no AWS spent)

AWS CALL #1 (real money, hard cost cap per test):
  - taskkill //F //IM codex.exe  (clear zombies)
  - Run pytest with tee to .log file
  - Capture all 10 mandatory files

PASS path:
  - Codex POST-PASS sanity (TEMPLATE C) — catches false-positives
  - 6-axis quality.md grade (worker + Codex)
  - If NEAR_IDEAL or WORKING_BUT_SUBOPTIMAL → log + advance to next test
  - If SEMANTIC_BUG_DETECTED → write bug.md → ESCALATE to user → HALT

FAIL path:
  - Codex DIAGNOSIS (TEMPLATE B) — root cause + proposed fix
  - You + Codex BOTH must APPROVE the fix
  - Apply fix → commit → re-PHASE A on fixed test → AWS call #2

MAX 3 AWS calls per test, total. 4th attempt → ESCALATE.
```

## Step 7: 6-axis quality grade (every test, every AWS call)

After every PASS, grade on these 6 axes (1-5 each):

1. **Tool choice optimality** — did agent pick BEST tool per step? (no `bash` when `python_exec` would do)
2. **Path efficiency** — turns_used vs minimum-possible
3. **Reasoning soundness** — does thinking_text match actual actions taken?
4. **Resource utilization** — sub-agents/compaction/cache used appropriately?
5. **Wasted calls** — REPEATED_calls flagged
6. **Outcome quality** — artifacts valid + body content correct + tests pass

Composite verdict: **NEAR_IDEAL | WORKING_BUT_SUBOPTIMAL | INEFFICIENT | SEMANTIC_BUG_DETECTED**

## Step 8: Codex command pattern (use exactly this)

```bash
# ALWAYS kill zombies first
taskkill //F //IM codex.exe 2>/dev/null || true

# Run Codex with strict model + reasoning + read-only sandbox
codex exec --full-auto -s read-only --skip-git-repo-check \
  -m gpt-5.5 -c model_reasoning_effort="high" "$(cat <<'EOF'
{paste filled-in TEMPLATE A/B/C from R_TIER_REVIEW_TEMPLATE.md, with all {{...}} placeholders replaced}
EOF
)" 2>&1 | tee compact_v5/_status/codex_reviews/r-tier-<TEST>-phase<X>-iter<N>.md

# Save header in every review file:
# # Codex CLI version: codex-cli 0.128.0
# # Model used: gpt-5.5
# # Reasoning effort: high
# # Date: <ISO timestamp>
```

If gpt-5.5 fails ("requires newer version"), upgrade: `npm install -g @openai/codex@latest`. If that fails, fallback to `gpt-5.3-codex` (also proven for this codebase, 23 prior reviews used it).

## Step 9: ESCALATE-to-user triggers (HALT, do NOT auto-continue)

Stop and ask user if any of these:
1. 3 AWS calls used + still failing on a test
2. Codex returns BLOCKER (not CHANGES_REQUESTED)
3. AWS Budget alert at 80% ($40/$50)
4. You + worker disagree after 3 review rounds
5. Bedrock returns auth/quota/region error (infra, not counted toward 3-call cap)
6. 2 consecutive R-tests fail at AWS call #1
7. Any SEMANTIC_BUG_DETECTED in quality.md

## Step 10: After all 42 tests done

1. Final full-codebase Codex AXIS A/B/C review (your job — independent of test results)
   - Save to `_status/codex_reviews/FINAL-iter1.md`
2. Generate `_status/FINAL_v5.0.1_PRODUCT_SUMMARY.md` for user containing:
   - All 42 test results table (READY/ESCALATED counts)
   - Total cost spent vs $14.25 cap
   - All PS_problems status (1-7 all GREEN expected)
   - 6-axis quality scores aggregated
   - List of any bugs found + fix commits
   - Final ship recommendation
3. Commit + push everything
4. STOP. Do NOT tag v5.0.1 final or ship. User F5 verification required.

# HARD CONSTRAINTS (non-negotiable)

1. **No empirical v4 or Runnable comparison** — Block V dropped per user. v5-only testing.
2. **Max 3 AWS calls per test** — period. ESCALATE after.
3. **Both reviewers must APPROVE before each AWS call** — no skipping.
4. **All 10 mandatory files per test** — incomplete = do not advance.
5. **Cost cap $14.25** — total. AWS Budget hard stop $50.
6. **Strict model: gpt-5.5 -c model_reasoning_effort="high"** — fallback gpt-5.3-codex only if gpt-5.5 unavailable.
7. **AU geo profile (`au.anthropic.*`)** — production model `au.anthropic.claude-sonnet-4-5-20250929-v1:0`, test `au.anthropic.claude-haiku-4-5-20251001-v1:0`. 10% pricing premium tracked via `tokens.py:get_geo_multiplier()`.
8. **No silent scope-narrowing** — if you defer a test, write ESCALATION-<TEST>.md asking user.
9. **Push every commit to sageagent remote** — `git push sageagent v5-build`.
10. **Read PLAYBOOK §4.4-§4.6 before R18/R19** — they have specific Es/Us spec.

# REPOSITORY STATE AT HANDOFF

- Local: `D:/Github/sagemaker-coding-agent/`
- Remote: `https://github.com/winstonpgao/sageagent`
- Branch: `v5-build`
- Latest commit: `d82c530` (CODEX_CONTEXT_v5_R_TIER.md)
- Tests collected: 798 (775 pass + 17 env-skip)
- Codex prior reviews: 50 APPROVE across Blocks 0-K
- All 21 Block tags present: `v5.0.1-block-0` ... `v5.0.1-block-k`
- `build_telemetry.py` aggregator: written by Claude Code worker at `_status/scripts/build_telemetry.py`
- AU 10% premium: fixed in `runtime/tokens.py` with lock tests
- ipywidgets approval blocking: needs `auto_approve_all_tools=True` in R-tier test setup (not yet applied)

# AWS ACCESS

Account: 903039434627. Region: ap-southeast-2 (AU).

Verify access:
```bash
aws bedrock-runtime invoke-model \
  --model-id au.anthropic.claude-haiku-4-5-20251001-v1:0 \
  --region ap-southeast-2 \
  --body '{"anthropic_version":"bedrock-2023-05-31","messages":[{"role":"user","content":"hi"}],"max_tokens":10}' \
  /tmp/out.json && cat /tmp/out.json
```

# EXACT FIRST ACTIONS

```bash
# 1. Pull latest
cd D:/Github/sagemaker-coding-agent
git pull sageagent v5-build

# 2. Verify state
git log --oneline -5
git tag -l "v5.0.1-block-*" | wc -l    # 21
cd compact_v5/MAIN/agent && pytest tests/ -q | tail -3   # 775 pass + 17 skip

# 3. Verify Codex CLI
codex --version    # 0.128.0 or later
codex exec -m gpt-5.5 -c model_reasoning_effort="high" "say ready"

# 4. Verify AWS
aws bedrock-runtime invoke-model --model-id au.anthropic.claude-haiku-4-5-20251001-v1:0 --region ap-southeast-2 --body '{"anthropic_version":"bedrock-2023-05-31","messages":[{"role":"user","content":"hi"}],"max_tokens":10}' /tmp/out.json

# 5. Verify AWS Budget headroom
aws budgets describe-budget --account-id 903039434627 --budget-name Bedrock-Monthly-50 | grep -A2 ActualSpend
# (should be near $0; need >$15 headroom for safe R-tier)

# 6. Read all 7 reference docs (Step 2 above)

# 7. Fix R-tier test setup to disable approval prompts:
#    Add to all R-tier test files in compact_v5/MAIN/agent/tests/r_tier/:
#      from runtime.config import CONFIG
#      CONFIG.require_tool_approval = False
#    OR pass auto_approve_all_tools=True to Agent constructor

# 8. Start R1 PHASE A pre-flight per Step 6 loop

# 9. Continue R1 → R19 → final review → STOP at user F5 gate
```

# DEFINITION OF DONE

v5.0.1 ready for user F5 sign-off when:

- [ ] All 42 R-tier tests have READY status in `_status/r_tier_review_log.md`
- [ ] Zero SEMANTIC_BUG_DETECTED outstanding
- [ ] Total spend ≤ $14.25
- [ ] Final full-codebase Codex AXIS A/B/C returns APPROVE
- [ ] `_status/FINAL_v5.0.1_PRODUCT_SUMMARY.md` generated
- [ ] All commits pushed to sageagent remote

After F5 sign-off (USER does this, not you): tag `v5.0.1` → rebuild zip → ship to SageMaker.

# QUESTIONS BEFORE STARTING

If anything in this prompt is unclear, ASK USER FIRST. Don't make assumptions on:
- Cost cap interpretation
- ESCALATE trigger interpretation
- Whether to fix vs flag a Codex finding
- Test scope changes

If everything is clear: confirm by replying "READY — starting R1 PHASE A pre-flight." Then begin.

---

**END HANDOFF PROMPT.**
