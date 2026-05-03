# PS_V5_TEST_WORKER_FINAL — Single Source of Truth for v5.0.1 R-tier Worker

**This is THE persistent prompt for Claude Code worker executing v5.0.1 R-tier real-AWS testing.**
**Supersedes all earlier handoff docs on conflict (CODEX_AFK_WORKER_PROMPT, CODEX_HANDOFF_PROMPT, CODEX_CONTEXT).**
**Last updated**: 2026-05-04

---

## ROLE — HARD RULE (do NOT violate)

| Role | Tool |
|---|---|
| Worker (executor) | YOU — Claude Code |
| Reviewer (independent verdicts) | Codex CLI invoked from your Bash tool |
| User F5 sign-off | USER (you HALT and ask) |

**NEVER use Codex CLI as a worker.** Codex-as-worker calling Codex-as-reviewer crashes (recursive). If Codex CLI itself crashes, write `ESCALATION-<TEST>.md` and ASK USER before switching reviewer (no silent downgrade to Claude Opus or anything else).

---

## SHELL ENVIRONMENT NOTE

Repo is on Windows. All Bash-style commands below assume **Git Bash** (or PowerShell with `python` invoked as `py -3.11`). If using PowerShell directly:
- `python -u -m pytest` → `py -3.11 -u -m pytest`
- `tee -a file.log` → `Tee-Object -Append file.log`
- `2>&1 | tee` → `2>&1 | Tee-Object`
- `taskkill //F //IM codex.exe` → `taskkill /F /IM codex.exe` (single-slash)
- `/tmp/out.json` → `$env:TEMP\out.json`
- Heredoc `<<'EOF' ... EOF` → use `@'...'@` PowerShell here-string OR write prompt to temp file then `Get-Content`

Worker should use Git Bash (already installed) for simplicity. If unavailable, translate per above.

## CURRENT R1 STATUS (2026-05-04, BEFORE worker resumes)

- auto_approve fix ALREADY APPLIED to R1 test (CONFIG.require_tool_approval=False)
- Real bug found by worker: Unicode stdout encoding crash (cp1252 vs utf-8) DURING AWS call #1
- Unicode stdout fix LANDED at:
  - `compact_v5/MAIN/agent/core/query_engine.py:151` `_make_unicode_safe_output_fn`
  - Lock test: `compact_v5/MAIN/agent/tests/integration/test_unicode_safe_output.py:4`
- Codex iter-4 PRE-FLIGHT verdict (BEFORE Unicode bug discovery) = APPROVE_FOR_AWS_CALL
- Codex iter-4 verdict is now STALE because the code changed AFTER the verdict

WORKER ACTION (mandatory order):
1. Pull latest sageagent v5-build
2. Verify both fixes in place: grep require_tool_approval test_r1; grep _make_unicode_safe_output_fn
3. RE-RUN PHASE A pre-flight on FIXED code (filled TEMPLATE A → Codex CLI iter-5)
4. ONLY after Codex returns APPROVE_FOR_AWS_CALL on iter-5 → run AWS call #2
5. NEVER skip Phase A because "code looks the same as iter-4" — the Unicode fix
   is a real diff that needs an explicit Codex APPROVE before spending AWS again

## PRE-FLIGHT (run in order, STOP if any fails)

```bash
cd D:/Github/sagemaker-coding-agent
git pull sageagent v5-build
git log --oneline -3                    # latest must be 283ca0d or later
git tag -l "v5.0.1-block-*" | wc -l     # must equal 21
cd compact_v5/MAIN/agent && pytest tests/ -q | tail -3   # 775+ pass + 17 skip
taskkill //F //IM codex.exe 2>/dev/null
codex --version                          # codex-cli 0.128.0+
codex exec -m gpt-5.5 -c model_reasoning_effort="high" "say ready"   # <15 sec
aws bedrock-runtime invoke-model --model-id au.anthropic.claude-haiku-4-5-20251001-v1:0 --region ap-southeast-2 --body '{"anthropic_version":"bedrock-2023-05-31","messages":[{"role":"user","content":"hi"}],"max_tokens":10}' /tmp/out.json
aws budgets describe-budget --account-id 903039434627 --budget-name Bedrock-Monthly-50 | grep -A2 ActualSpend  # need <$35 spend
```

---

## READ THESE 4 FILES (mandatory before R1)

1. `compact_v5/docs/PS_V5_TEST_PLAYBOOK.md` — full 42-test spec (§4.1-§4.6)
2. `compact_v5/_status/R_TIER_REVIEW_TEMPLATE.md` — Codex prompt templates A/B/C + CONTEXT-PASSING PROTOCOL
3. `compact_v5/_phase_2/wave_6/WORKER_HINT_2026-05-03.md` — supersedes BUILDER_PROMPT on conflict
4. `compact_v5/_status/V5_BUILD_STATUS.md` — current state

---

## EXECUTION ORDER (42 tests, $14.25 cap)

```
R1   composite dashboard build              real  $1.00
R2   80K context compact + cache_edits      real  $0.50
R3   3 parallel sub-agents                  real  $0.50
R4   30-min cold-cache compact              real  $0.20  (PS#3)
R5   200-bash exec recovery                 real  $0.50  (PS#7)
R6   /dream consolidation 100 entries       real  $0.30
R7   mid-conv Haiku→Sonnet model switch     real  $0.50  (Hermes A28)
R8   malformed JSON repair                  MOCK  $0
R9   approval flow end-to-end               real  $0.30
R10  save→restart→load cost intact          real  $1.00  (PS#5/6)
R11  Sonnet 4.5 end-to-end                  real  $1.50
R12  malformed args + Unicode               real  $0.20
R13  5 HumanEval Python problems            real  $0.50
R14  3-file refactor + pytest green         real  $0.75
R15  find+fix 2 planted bugs                real  $0.50
R16  100-turn Flask CRUD build              real  $1.00
R17  thinking visibility on Sonnet          real  $0.30  (PS#4)
R18  15 INFRA edges (4 mock + 11 real)      mixed $1.60
R19  10 UX edges (ambig/conflict/recovery)  real  $3.10  CRITICAL
                                            TOTAL $14.25
```

---

## PER-TEST LOOP (use verbatim)

```
PHASE A — PRE-FLIGHT (free, no AWS):
  1. YOU write/inspect test code
  2. YOU self-review changes
  3. Fill TEMPLATE A from R_TIER_REVIEW_TEMPLATE.md per CONTEXT-PASSING PROTOCOL
     (inline test code + scenario fixtures, NOT just paths)
  4. Run Codex CLI:
       taskkill //F //IM codex.exe 2>/dev/null
       codex exec --full-auto -s read-only --skip-git-repo-check \
         -m gpt-5.5 -c model_reasoning_effort="high" "$(cat <<'EOF'
       {filled-in TEMPLATE A}
       EOF
       )" 2>&1 | tee compact_v5/_status/codex_reviews/r-tier-<TEST>-phaseA-iter<N>.md
  5. If Codex APPROVE_FOR_AWS_CALL → AWS gate OPENS
     If REJECT → fix → re-PHASE A (free)

AWS CALL (real money, hard cap per test):
  6. Apply (one-time fix): CONFIG.require_tool_approval = False in R-tier setup
  7. taskkill //F //IM codex.exe 2>/dev/null
  8. RUN_REAL_BEDROCK=1 AWS_REGION=ap-southeast-2 python -u -m pytest \
     tests/r_tier/test_<test>.py -v -s 2>&1 | \
     tee compact_v5/_status/codex_reviews/r-tier-<TEST>-aws-call<N>.log
  9. Run build_telemetry.py → telemetry.json
  10. Append JSONL row to r_tier_metrics.jsonl

POST-CALL:
  PASS path:
    11. Codex POST-PASS sanity (TEMPLATE C) — inline telemetry + tail-100 of .log
    12. YOU generate quality.md PASS 1 (6-axis grade)
    13. Codex generates quality.md PASS 2 (independent 6-axis grade)
    14. NEAR_IDEAL or WORKING_BUT_SUBOPTIMAL → log + advance
        SEMANTIC_BUG_DETECTED → write bug-<N>.md → ESCALATE → HALT

  FAIL path:
    11. Codex DIAGNOSIS (TEMPLATE B) — root cause + proposed fix
    12. YOU + Codex BOTH must APPROVE the fix
    13. Apply fix → commit → re-PHASE A on fixed test → AWS call #2

  HARD CAP: 3 AWS calls per test, total. 4th attempt → ESCALATE.

CLOSE TEST:
  15. Append row to r_tier_review_log.md with all 10 file refs
  16. git add the 10 mandatory files for this test
  17. git commit -m "v5/r-tier-<TEST>: <verdict>"
  18. git push sageagent v5-build
  19. ONLY now move to next test
```

---

## 10 EVIDENCE CATEGORIES PER TEST (7 always required + 3 conditional)

```
ALWAYS REQUIRED (7):
1.  _status/codex_reviews/r-tier-<TEST>-phaseA-iter<N>-prompt.txt   # filled TEMPLATE A
2.  _status/codex_reviews/r-tier-<TEST>-phaseA-iter<N>.md           # Codex pre-flight verdict
3.  _status/codex_reviews/r-tier-<TEST>-aws-call<N>.log             # raw Bedrock log
6.  _status/r_tier_metrics.jsonl                                    # JSONL row appended
7.  _status/r_tier_review_log.md                                    # row appended (this test's row)
9.  _status/r-tier-<TEST>-aws-call<N>-telemetry.json                # build_telemetry.py output
10. _status/r-tier-<TEST>-aws-call<N>-quality.md                    # PASS 1 + PASS 2 6-axis grade

CONDITIONAL (only when triggered):
4.  _status/codex_reviews/r-tier-<TEST>-phaseB-iter<N>.md           # Codex diagnosis — ONLY if AWS call FAILED
5.  _status/codex_reviews/r-tier-<TEST>-phaseC-iter<N>.md           # Codex post-pass sanity — ONLY if AWS call PASSED
8.  _status/codex_reviews/ESCALATION-<TEST>.md                      # ONLY if 3-call cap hit, SEMANTIC_BUG_DETECTED, or Codex CLI crash
```

**Hard rule**: every always-required file (7) + the appropriate conditional file (PhaseB IF FAIL, PhaseC IF PASS, ESCALATION IF triggered) must exist before advancing. Do NOT create placeholder files for conditionals that didn't fire — that signals false state.

---

## 6-AXIS QUALITY GRADE (every PASS, every test)

| Axis | What |
|---|---|
| Tool choice optimality (1-5) | Best tool per step? (no `bash` when `python_exec` would do) |
| Path efficiency (1-5) | turns_used vs minimum-possible |
| Reasoning soundness (1-5) | Does thinking_text match actions taken? |
| Resource utilization (1-5) | Sub-agents/compaction/cache used appropriately? |
| Wasted calls (1-5) | REPEATED_calls flagged |
| Outcome quality (1-5) | Artifacts valid + body content correct |

Composite verdict: **NEAR_IDEAL | WORKING_BUT_SUBOPTIMAL | INEFFICIENT | SEMANTIC_BUG_DETECTED**

If you + Codex disagree by >1 point on any axis → flag in quality.md "RECONCILIATION" section.

---

## ESCALATE-to-user triggers (HALT, write ESCALATION-<TEST>.md, ASK USER)

1. 3 AWS calls + still failing on a test
2. Codex returns BLOCKER (not CHANGES_REQUESTED)
3. AWS Budget alert at 80% ($40/$50)
4. You + Codex disagree after 3 review rounds
5. Bedrock returns auth/quota/region/throttle (infra; NOT counted toward 3-call cap)
6. 2 consecutive R-tests fail at AWS call #1
7. Any SEMANTIC_BUG_DETECTED in quality.md PASS 2
8. Codex CLI crashes — do NOT silently switch reviewer

---

## AFTER ALL 42 SCENARIOS DONE (R1-R19 groups; R18 has 15 sub-scenarios E1-E15, R19 has 10 U1-U10 — each must individually be READY)

1. Final full-codebase Codex CLI AXIS A/B/C review
   Save: `_status/codex_reviews/FINAL-iter1.md`
2. Generate `_status/FINAL_v5.0.1_PRODUCT_SUMMARY.md`:
   - 42 test result table (READY/ESCALATED counts)
   - Total cost spent vs $14.25 cap
   - All 7 PS_problems status (expect all GREEN)
   - 6-axis quality scores aggregated
   - Bugs found + fix commits
   - Final ship recommendation
3. git commit + push everything
4. STOP. Do NOT tag v5.0.1 or ship. User F5 verification required.

---

## DEFINITION OF DONE

- [ ] All 42 R-tier tests have READY status in `r_tier_review_log.md`
- [ ] Zero SEMANTIC_BUG_DETECTED outstanding
- [ ] Total spend ≤ $14.25
- [ ] Final full-codebase Codex AXIS A/B/C returns APPROVE
- [ ] `FINAL_v5.0.1_PRODUCT_SUMMARY.md` generated
- [ ] All commits pushed to sageagent remote

After F5 sign-off (USER, not you): tag `v5.0.1` → rebuild zip → ship to SageMaker.

---

## COST + SAFETY (3-layer defense)

| Layer | Trigger |
|---|---|
| App-level `session_cost_limit` per test | Halts agent when test cost > cap |
| AWS Budget `Bedrock-Monthly-50` ($50) | Email at 50/80/100%; **at 100% IAM auto-deny attaches** |
| Per-test review log | `r_tier_review_log.md` runtime visibility |

**Worst case all 42 tests max retry**: ~$45. Hard stop $50. Email at $25 + $40.

---

## REPLY "READY" TO START

If pre-flight clean and 4 docs read → reply **"READY — starting R1 PHASE A pre-flight"** then begin.

If anything unclear → ASK USER FIRST. Don't make assumptions on cost cap, ESCALATE triggers, or scope changes.
