# CODEX CONTEXT — v5.0.1 R-tier Real-AWS Testing

**Audience**: Codex (or any LLM) taking over v5 R-tier execution from Claude Code.

**Goal**: Run all 42 test scenarios on real AWS Bedrock, validate v5.0.1 is production-ready for single-user SageMaker deployment, produce hard evidence v5 has no semantic bugs and handles real coding workflows correctly.

**Date**: 2026-05-03

---

## 1. What v5.0.1 IS

`sagemaker-coding-agent` v5.0.1 — Bedrock-only Python coding agent for single-user SageMaker notebook (`chat.ipynb`). Replaces v4.10.10 (which had 7 documented production problems = "PS#1-7").

v5 = v4 functional baseline + Runnable architecture + Hermes patterns + Learning Factory discipline. 21 Blocks built incrementally (Block 0 → K), each Codex-reviewed (50 APPROVE iters), 798 mock tests green.

Production model: `au.anthropic.claude-sonnet-4-5-20250929-v1:0`
Test model: `au.anthropic.claude-haiku-4-5-20251001-v1:0`
Region: `ap-southeast-2` (AU)

## 2. What we're testing now

42 distinct test scenarios on real AWS Bedrock. Total cost cap: **$14.25** (well under $50/mo AWS Budget hard stop).

| Tier | Tests | Cost | What it proves |
|---|---|---|---|
| Mock (already passing) | 798 (775 pass + 17 skip) | $0 | Internal correctness, no regression of any Codex finding |
| **R1-R12** Composite + PS_problem fixes | 12 (11 real + 1 mock) | $6.50 | Every PS_problem fix works on real Bedrock |
| **R13-R16** Coding ability | 4 real | $2.75 | Coding accuracy + multi-file + debug + long-session |
| **R17** Thinking visibility (PS#4) | 1 real | $0.30 | Extended thinking blocks captured in chat history |
| **R18** Infrastructure edges | 15 (4 mock + 11 real) | $1.60 | Throttling, races, encoding, atomicity, cap timing |
| **R19** User-experience edges | 10 real | $3.10 | Ambiguous specs, hidden deps, sub-agent fails, tool recovery, memory conflicts, long-session model-switch |
| **TOTAL** | **42** | **$14.25** | **~99% v5 production-readiness** |

## 3. The 42 test scenarios in detail

### R1-R12 — composite + PS_problem fixes (real-AWS, $6.50)

| # | What it does | Cost | PS fix proven |
|---|---|---|---|
| R1 | 50-turn dashboard build (CSV → chart → Word doc) | $1.00 | Composite tool dispatch + cost tracking |
| R2 | 80K context compact + cache_edits invalidation | $0.50 | Block A compactor on real cache |
| R3 | 3 parallel sub-agents → synthesize report | $0.50 | Block G + G2 + G3 cache-prefix bytes-stable |
| R4 | 30-min idle then resume → cold-cache compact | $0.20 | PS#3 cold-cache fix |
| R5 | 200 bash exec → 201st returns "OTHER TOOLS WORK" | $0.50 | PS#7 exec-gate fix |
| R6 | /dream consolidates 100 entries | $0.30 | Block H+ memory consolidation |
| R7 | Mid-conv Haiku→Sonnet — cache NOT rebuilt | $0.50 | Hermes A28 invariant |
| R8 | Malformed JSON tool args → multi-pass repair | $0 (mock) | Block C JSON repair |
| R9 | write_file → diff_widget → Approve/Deny → propagates | $0.30 | Block C+ approval flow |
| R10 | Spend $1 → /save → restart kernel → /load → cost intact | $1.00 | PS#5 + PS#6 cost-on-save/load |
| R11 | Same as R1 but on Sonnet 4.5 (model differential) | $1.50 | Production model compatibility |
| R12 | Multi-tool malformed args + Unicode surrogates | $0.20 | Block L errors + H surrogate sanitize |

### R13-R16 — coding ability (real-AWS, $2.75)

| # | Scenario | Cost | Proves |
|---|---|---|---|
| R13 | 5 HumanEval-mini Python problems → assertions pass | $0.50 | Coding accuracy |
| R14 | 3-file rename refactor → pytest stays green | $0.75 | Multi-file coordination |
| R15 | Find + fix 2 planted bugs (off-by-one + encoding) | $0.50 | Debugging ability |
| R16 | Build 3-endpoint Flask CRUD with tests, 100 turns | $1.00 | Long-session app build |

### R17 — thinking visibility, PS#4 (real-AWS, $0.30)

Sonnet 4.5 with extended thinking enabled. Verify thinking blocks appear in agent chat history + telemetry `per_turn.thinking_text` populated.

### R18 — infrastructure edge cases (mixed, $1.60)

11 real-AWS + 4 mock (mocks justified — can't be forced on real cheaply):
- E1 force throttling (real, $0.30)
- E2 5xx flake (mock — can't force)
- E3 cost cap mid-call (real, $0.10)
- E4 skill alias activation (real, $0.10)
- E5 corrupt session JSON (mock — pure file IO)
- E6 empty/missing files (real, $0.10)
- E7 50K-token output truncation (real, $0.10)
- E8 concurrent sub-agent races (real, $0.10)
- E9 disk-full snapshot (mock — can't force)
- E10 plan-mode allowlist (real, $0.10)
- E11 sub-agent timeout during compaction (real, $0.20)
- E12 audit log rotation (mock — pure file IO)
- E13 Unicode/RTL memory.md (real, $0.10)
- E14 /dream interrupt mid-write (real, $0.20)
- E15 cache TTL mid-conv (real, $0.20)

### R19 — user-experience edge cases (real-AWS, $3.10) ★ CRITICAL

These are the real-world scenarios users actually hit:

| # | UX edge | Axis | Cost |
|---|---|---|---|
| U1 | Ambiguous requirement ("make it better") — agent SHOULD ask clarifying via ask_user, not assume | Coding ability | $0.20 |
| U2 | Contradictory specs ("use REST AND GraphQL") — agent recognizes + flags conflict | Coding ability | $0.20 |
| U3 | Large refactor with HIDDEN cross-file dep — agent must grep before changing | Coding + tool use | $0.50 |
| U4 | 3 sub-agents return CONFLICTING findings — parent reconciles correctly | Sub-agent coord | $0.40 |
| U5 | Sub-agent FAILS mid-task — parent recovers + completes | Sub-agent coord | $0.30 |
| U6 | Tool produces garbage output — agent recovers via re-call or alternative | Tool use | $0.20 |
| U7 | Agent stuck calling SAME tool 3+ times — circuit breaker fires + tries alternative | Tool use | $0.20 |
| U8 | Memory conflicts (user said X then Y) — /dream resolves; agent uses latest | Memory | $0.30 |
| U9 | /dream consolidates 50 entries — verify NOTHING important lost | Memory | $0.30 |
| U10 | 150-turn session + 2 model switches + 3 compactions — stays coherent | Context mgmt | $0.50 |

## 4. Per-test discipline — STRICT rules

### Every R-test produces 10 mandatory files

For each AWS-side R-test (R1-R19):
1. `_status/codex_reviews/r-tier-<TEST>-phaseA-iter<N>-prompt.txt` — pre-flight prompt
2. `_status/codex_reviews/r-tier-<TEST>-phaseA-iter<N>.md` — Codex pre-flight verdict (AXIS A/B/C)
3. `_status/codex_reviews/r-tier-<TEST>-aws-call<N>.log` — raw Bedrock log (every turn)
4. `_status/codex_reviews/r-tier-<TEST>-phaseB-iter<N>.md` — diagnosis IF call failed
5. `_status/codex_reviews/r-tier-<TEST>-phaseC-iter<N>.md` — post-pass sanity
6. JSONL row in `_status/r_tier_metrics.jsonl` — tokens/cache/wallclock/cost
7. Row in `_status/r_tier_review_log.md` — master test summary
8. `_status/codex_reviews/ESCALATION-<TEST>.md` — IF 3 AWS calls hit cap or BUG detected
9. `_status/r-tier-<TEST>-aws-call<N>-telemetry.json` — per-turn breakdown via build_telemetry.py
10. `_status/r-tier-<TEST>-aws-call<N>-quality.md` — worker + Codex 6-axis quality grade

If ANY file missing → test INCOMPLETE → do NOT advance to next test.

### Test → review → fix → review → ready loop

```
PHASE A — PRE-FLIGHT (free, no AWS):
  Worker writes test → self-review → Codex AXIS A/B/C review
  BOTH must APPROVE → AWS gate OPENS

AWS CALL #1 (real money, hard cost cap per test):
  PASS → Codex POST-PASS sanity (TEMPLATE C)
       → 6-axis quality.md (worker + Codex grade)
       → If NEAR_IDEAL or WORKING_BUT_SUBOPTIMAL → log + advance
       → If SEMANTIC_BUG_DETECTED → ESCALATE to user, halt
  FAIL → Codex DIAGNOSIS (TEMPLATE B)
       → BOTH APPROVE fix → re-PRE-FLIGHT → AWS call #2

AWS CALL #2/3 (only if both reviewers approved fix)

MAX 3 AWS calls per test, total. 4th attempt → ESCALATE.
```

### 6-axis quality grade per test

After every AWS call, Codex grades on:
1. Tool choice optimality (1-5)
2. Path efficiency (1-5)
3. Reasoning soundness (per thinking text) (1-5)
4. Resource utilization (sub-agents, compaction, cache) (1-5)
5. Wasted calls (REPEATED_calls) (1-5)
6. Outcome quality (artifacts valid + body content) (1-5)

Composite verdict: NEAR_IDEAL | WORKING_BUT_SUBOPTIMAL | INEFFICIENT | SEMANTIC_BUG_DETECTED

## 5. Codex command pattern (use exactly this)

```bash
# 1. Always kill zombies first
taskkill //F //IM codex.exe 2>/dev/null || true

# 2. Run Codex with strict model + reasoning + read-only sandbox
codex exec --full-auto -s read-only --skip-git-repo-check \
  -m gpt-5.5 -c model_reasoning_effort="high" "$(cat <<'EOF'
{filled-in template from R_TIER_REVIEW_TEMPLATE.md}
EOF
)" 2>&1 | tee compact_v5/_status/codex_reviews/r-tier-<TEST>-phase<X>-iter<N>.md

# 3. Save Codex CLI version + model in every review file header:
#    # Codex CLI version: codex-cli 0.128.0
#    # Model used: gpt-5.5
#    # Reasoning effort: high
#    # Date: <ISO timestamp>
```

If gpt-5.5 fails ("requires newer version"), upgrade CLI: `npm install -g @openai/codex@latest` then retry. Fallback to gpt-5.3-codex if upgrade not possible.

## 6. Cost monitoring (3 layers, can't fail)

| Layer | Trigger |
|---|---|
| App-level `session_cost_limit` per test | Halts agent when test cost > cap |
| AWS Budget `Bedrock-Monthly-50` ($50 USD) | Email at 50%/80%/100%; **at 100% IAM auto-deny attaches** to SageMaker exec role |
| Per-test review log | `r_tier_review_log.md` — runtime visibility |

**Worst case all 42 tests max retry**: ~$45. Hard stop $50. Email at $25 + $40.

## 7. ESCALATE-to-user triggers

Worker MUST stop and ask user (not auto-continue) if:
1. 3 AWS calls + still failing on a test
2. Codex returns BLOCKER (not CHANGES_REQUESTED)
3. AWS Budget alert at 80% ($40/$50)
4. Worker + Codex disagree after 3 review rounds
5. Bedrock returns auth/quota/region error (infra issue, NOT counted toward 3-call cap)
6. 2 consecutive R-tests fail at AWS call #1
7. Any SEMANTIC_BUG_DETECTED in quality.md PASS 2

## 8. Files in repo Codex needs to read

| File | Purpose |
|---|---|
| `compact_v5/docs/PS_V5_TEST_PLAYBOOK.md` | MASTER reference — full spec for all 42 tests |
| `compact_v5/docs/PS_V5_TEST_SET.md` | TL;DR test catalog + costs |
| `compact_v5/_phase_2/wave_6/WORKER_HINT_2026-05-03.md` | All persistent worker rules (supersedes BUILDER_PROMPT on conflict) |
| `compact_v5/_status/R_TIER_REVIEW_TEMPLATE.md` | Codex prompt templates A (pre-flight) / B (diagnosis) / C (post-pass) |
| `compact_v5/_status/V5_BUILD_STATUS.md` | Current state + last commit |
| `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` | Every Runnable pattern adopted |
| `compact_v5/_status/V5_DESIGN_DECISIONS.md` | ADR log |
| `compact_v5/MAIN/agent/` | The actual v5 code (Python) |

## 9. What's been done (state at handoff)

- 21 Blocks all DONE + tagged (v5.0.1-block-0 through v5.0.1-block-k)
- 50 Codex APPROVE reviews across the Blocks
- 798 mock tests passing (775 pass + 17 env-skip)
- All 7 PS_problems fixed with lock tests
- Real-AWS test infrastructure ready (audit_log + token tracking + cost cap)
- Worker started R1 — caught real bug (ipywidgets blocking pytest), fixed it
- AU 10% pricing premium fix in `tokens.py` (Codex caught it during R1 pre-flight)
- `build_telemetry.py` aggregator written by worker
- All status persisted in git, pushed to `sageagent` remote (https://github.com/winstonpgao/sageagent)

## 10. What Codex (you) needs to do

1. Pull latest: `git pull sageagent v5-build`
2. Read PLAYBOOK §4.1 through §4.6 (full test spec)
3. Read R_TIER_REVIEW_TEMPLATE.md (your review prompt structure)
4. Run R1 first (composite test) per §4 discipline
5. After each test: produce all 10 mandatory files
6. After R1 PASS → R2 → R3 → ... → R19
7. After R19 PASS → final full-codebase Codex AXIS A/B/C review
8. Generate `compact_v5/_status/FINAL_v5.0.1_PRODUCT_SUMMARY.md` for user
9. STOP at F5 user verification gate (do NOT tag v5.0.1 final or ship)

## 11. Definition of done

v5.0.1 production-ready when:
- All 42 R-tier tests have READY status in r_tier_review_log.md
- Zero SEMANTIC_BUG_DETECTED outstanding
- Total cost ≤ $14.25
- Final full-codebase Codex returns APPROVE
- User signs F5 verification (Q1-Q4 from V5_SHIP_CRITIQUE.md)

After F5 sign-off → tag v5.0.1 → rebuild zip → ship to SageMaker.

## 12. Key constraints (hard, non-negotiable)

1. v4.10.10 IS BASELINE — v5 must match or exceed v4 functional surface
2. v4 chat.ipynb canonical UI (preserved)
3. Cover ALL 4 reference repos (v4 + Runnable + Hermes + LF)
4. Line-by-line investigation, NO scope-narrowing
5. Architecture-first — no pattern adoption without arch-fit
6. Structurally fix all 7 PS_problems
7. Bedrock-only (no Anthropic API direct, no other providers)
8. python_exec is canonical Python tool (NOT bash python)
9. Single-user SageMaker context (NOT multi-tenant)
10. AU geo profile (`au.anthropic.*`) — 10% pricing premium tracked

## 13. Trust verification

Every claim in this doc traceable to:
- Git: `git log --oneline -50 v5-build` shows 100+ Block commits
- Tags: `git tag -l "v5.0.1-block-*"` shows 21 Block tags
- Codex reviews: `compact_v5/_status/codex_reviews/` has 50+ APPROVE files
- PORT_LOG: `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` has 100+ rows with file:line refs
- Mock tests: `cd compact_v5/MAIN/agent && pytest tests/ -q` shows 775 pass + 17 skip

## 14. AWS access

Codex needs AWS CLI configured for `ap-southeast-2`. Permissions: Bedrock model invocation on `au.*` cross-region inference profiles. Account: 903039434627.

Verify: `aws bedrock-runtime invoke-model --model-id au.anthropic.claude-haiku-4-5-20251001-v1:0 --region ap-southeast-2 --body '{"anthropic_version":"bedrock-2023-05-31","messages":[{"role":"user","content":"hi"}],"max_tokens":10}' /tmp/out.json`

## 15. Repository

- Local: `D:/Github/sagemaker-coding-agent/`
- Remote: `https://github.com/winstonpgao/sageagent`
- Branch: `v5-build`
- Latest commit at handoff: `85f636d` (R19 UX edges added)
- Working tree status: clean except for in-progress R-tier work

---

**END CONTEXT.** Codex now has everything to execute R1-R19 + final review autonomously per the strict discipline above.
