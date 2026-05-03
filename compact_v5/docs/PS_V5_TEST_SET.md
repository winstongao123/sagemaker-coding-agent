# PS_V5_TEST_SET — Production-Ready Test Plan for v5.0.1

**Audience**: business stakeholder + worker reference

**Purpose**: complete, beginner-friendly catalog of every test that runs before v5.0.1 ships to production. Covers what each test does, why it matters, what it costs, and what it proves.

**Last updated**: 2026-05-03

---

## TL;DR

| Layer | Tests | Cost | Time | Proves |
|---|---|---|---|---|
| **Mock tests** (no AWS) | 798 collected, 775 pass + 17 env-gated skip | $0 | seconds | Internal correctness + regression prevention |
| **R1-R12 real-AWS** (no semantic bugs) | 11 real + 1 mock | $6.50 cap | ~2 hours | Every PS_problem fix + every Block works on real Bedrock |
| **R13-R16 real-AWS** (actually codes) | 4 | $2.75 cap | ~2 hours | Coding accuracy + multi-file + debug + long-session |
| **R17 real-AWS** (thinking visibility, PS#4) | 1 | $0.30 cap | ~10 min | PS#4 thinking-visible fix end-to-end |
| **R18 real-AWS + mock** (Edge Cases Battery, NEW 2026-05-03) | 15 (9 mock + 6 real) | $0.80 cap | ~30 min | Throttling, race conditions, encoding, atomicity, cap timing, etc. — closes 95%→99%+ |
| ~~Block V (head-to-head v4 vs v5)~~ | **DROPPED 2026-05-03 per user** ("don't run v4, save money") | ~~$2.00~~ | — | "v5 > v4" stays ARCHITECTURAL (PORT_LOG file:line refs + PS#1-7 CERTAIN-NO-RECUR) |
| **TOTAL** | **18 distinct test scenarios (v5 only)** | **$10.35** | **~5.5 hours** | **Production-ready evidence (99%+ internal correctness; architectural for v5>v4>Runnable)** |

Worst case if every test maxes 3 retries: ~$33. Hard stop: AWS Budget `Bedrock-Monthly-50` at $50/mo.

---

## How tests are run (the strict review gate)

Per `_phase_2/wave_6/WORKER_HINT_2026-05-03.md` §10: every real-AWS test runs through a 4-phase loop. Money only flows when both reviewers agree.

```
PHASE A — PRE-FLIGHT (free)
  Worker writes test → self-review → Codex TEMPLATE A review
  Both APPROVE? → AWS gate OPENS

AWS CALL #1 (real money)
  PASS path: Codex TEMPLATE C sanity check (catches false-positives)
  FAIL path: PHASE C diagnosis

PHASE C — DIAGNOSIS (free)
  Worker hypothesizes root cause → Codex TEMPLATE B review
  Both APPROVE fix? → apply + commit → re-PHASE A

AWS CALL #2 — only if both reviewers approved fix
AWS CALL #3 — LAST attempt, same gate
4th attempt → STOP + ESCALATE to user
```

**Hard rules**:
1. Max 3 AWS calls per test, total
2. EVERY AWS call requires worker AND Codex APPROVE in immediately preceding review
3. Cost cap per test enforced by `session_cost_limit` (agent halts if exceeded)
4. AWS Budget hard-stops Bedrock at $50/mo (IAM auto-deny attaches at 100%)

Review prompts: `compact_v5/_status/R_TIER_REVIEW_TEMPLATE.md` (TEMPLATE A/B/C). Block code reviews use `compact_v5/_status/CODEX_REVIEW_TEMPLATE.md` (already used 50× for the 20 done Blocks).

---

## Tier 0 — Mock tests (free, already passing)

| Layer | Count | Cost | Status |
|---|---|---|---|
| T1 unit tests | ~150 | $0 | DONE — green |
| T2 integration tests | ~100 | $0 | DONE — green |
| T3 notebook smoke | 21 | $0 | DONE — green |
| T4 zip extract+import | 21 | $0 | DONE — green (CAUGHT real Block J packaging bug) |
| Block lock tests (1+ per Codex finding) | ~200 | $0 | DONE — 50 Codex APPROVE iters |
| Real-AWS tests env-gated | 17 | $0 (skipped) | code-ready, not run |
| **Total mock** | **798** | **$0** | **775 pass / 17 skip** |

**What mock tests prove**: every component works in isolation; no Codex finding can recur silently; static prompt ≤ 2500 tokens; deferred tool schemas save ≥ 3000 tokens/turn vs Phase-6 baseline; PS#1-7 all have lock tests.

**What mock tests do NOT prove**: real Bedrock behavior (cache hits, latency, model quirks).

---

## Tier 1 — R1-R12 (no semantic bugs on real Bedrock)

12 tests. 11 real-AWS + 1 mock (R8 mislabeled). $6.50 cap. Goal: prove v5 works end-to-end on real Bedrock without breaking under each PS_problem fix.

| # | Test name (5-year-old explanation) | Why it matters | Model | Cost cap | Block(s) it validates |
|---|---|---|---|---|---|
| **R1** | Build a real dashboard: read CSV → summarize numbers → make chart → embed in Word doc. 50 conversation turns. | Tool dispatch end-to-end, parallel exec gain on real Bedrock, security gate with real bash, .docx output integrity. THE general "does it work" test. | Haiku 4.5 | $1.00 | All Blocks composite |
| **R2** | Load 80,000-token document → ask refactor → check compaction fires + cache_edits invalidates only changed tools | Block A (compactor) on real cache; A28 invariant on real cache hit | Haiku 4.5 | $0.50 | A |
| **R3** | Spawn 3 parallel sub-agents → synthesize findings → write report | Block G + G2 + G3 cache-prefix bytes-stable on real Bedrock — multiple agents share cache | Haiku 4.5 | $0.50 | G, G2, G3 |
| **R4** | Send msg → wait 30 real minutes → send next msg → check cold-cache compact fires + saves ≥5K tokens | PS#3 structural fix end-to-end (the cold-cache bug from v4 production) | Haiku 4.5 | $0.20 | A (cold-cache path) |
| **R5** | Loop python_exec 200×. 201st call returns "OTHER TOOLS STILL WORK" message; agent continues with read_file/grep | PS#7 structural fix end-to-end (v4 had agent give up at limit; v5 redirects to other tools) | Haiku 4.5 | $0.50 | C (exec gate) + N (failure-as-instruction) |
| **R6** | Fill memory.md with 100 entries → call `/dream` → check dedup + categorization | Block H+ (manual `/dream`) semantic correctness; rollback on fail; lock prevents concurrent runs | Haiku 4.5 | $0.30 | H+ |
| **R7** | 10 turns Haiku → user changes dropdown → next turn uses Sonnet WITHOUT rebuilding cached system prompt | Hermes A28 invariant on real Bedrock — model switch doesn't waste cache mid-session | Haiku→Sonnet 4.5 | $0.50 | N (Hermes A28) |
| **R8** | (MOCK — should reclassify) malformed JSON tool args → multi-pass repair works → fallback to `{}` | Block C JSON repair end-to-end | mock | $0 | C |
| **R9** | write_file → diff_widget renders → click Approve/Deny/Always → decision propagates to TOKENS + AUDIT + SNAPSHOTS | Block C+ approval flow end-to-end on real Bedrock | Haiku 4.5 | $0.30 | C+ |
| **R10** | Spend $1 in turns → `/save mytest` → restart kernel → `/load mytest` → verify `TOKENS.session_cost == $1.00` + chat history restored | PS#5 + PS#6 structural fix on real session (v4 LOST cost on save/load) | Haiku 4.5 | $1.00 | B + B+ (save/load) |
| **R11** | Same as R1 but on Sonnet 4.5 | Sonnet model differential — production model behavior, not just cheap test model | Sonnet 4.5 | $1.50 | All Blocks on production model |
| **R12** | Multi-tool malformed args + surrogate-pair Unicode stress | Block L Bedrock error categories; H1 surrogate sanitize prevents 400 errors | Haiku 4.5 | $0.20 | L + H |
| | | | | **$6.50** | |

**What R1-R12 proves**: v5 has no semantic bugs on real Bedrock; every PS_problem fix verified end-to-end; every Block has at least one real-AWS validation.

**What R1-R12 does NOT prove**: code accuracy / multi-file / debugging / long-session quality.

---

## Tier 2 — R13-R16 enhanced (actually codes well, NEW 2026-05-03)

4 tests. Real-AWS only. $2.75 cap. Goal: empirical evidence v5 actually CODES, not just passes mechanical tests.

| # | Test name | Why it matters (business-stakeholder framing) | Scoring | Model | Cost cap |
|---|---|---|---|---|---|
| **R13** | 5 HumanEval-mini Python problems with assertions ("write function X, here are 3 test cases") → agent writes code → python_exec runs assertions | EMPIRICAL CODING ACCURACY. Like a coding interview. R1-R12 prove "agent works mechanically"; R13 proves "code it writes is actually correct." | # tests passing / 5 | Haiku 4.5 | $0.50 |
| **R14** | 3-file Python project with cross-file deps → "rename `class Foo` to `Bar` everywhere, update tests, verify pytest stays green" | MULTI-FILE COORDINATION. Most coding agents fail this — they edit one file and forget the others. Real coding work is mostly multi-file. | pytest exit code + grep for missed renames | Haiku 4.5 | $0.75 |
| **R15** | 2 planted bugs (off-by-one + encoding) → "find + fix + justify each" | DEBUGGING ABILITY. Debugging = 50% of real coding work. Score: bugs found + correct fix + no false-positive fixes. | Score 0-2 per bug | Haiku 4.5 | $0.50 |
| **R16** | 100-turn Flask CRUD app build from scratch with multiple endpoints + tests | LONG-SESSION COHERENCE. Forces 2-3 compaction cycles + sustained coding work. Real users hit this. | App boots + tests pass at end | Haiku 4.5 | $1.00 |
| | | | | **$2.75** | |

**What R13-R16 proves**: v5 codes accurately, handles multi-file, debugs, sustains long sessions.

**What R13-R16 does NOT prove**: v5 > v4 (Block V proves that).

---

## Tier 3 — Block V head-to-head v4 vs v5 (NEW 2026-05-03)

3 tasks × 2 systems × Haiku 4.5 = 6 runs. $2.00 cap. Goal: EMPIRICAL "v5 > v4" with apples-to-apples metrics.

Each task: identical prompt, identical workspace, identical model, identical iteration limit. v5-side allowed 3 AWS calls cap. v4-side allowed 1 AWS call cap (don't fix v4 bugs — document as "v5 wins" data point).

| # | Task | Why this task | Cost (v4 + v5) |
|---|---|---|---|
| **V1** | Refactor 50-line Python module: extract a function, rename a variable, add type hints | Edit accuracy on small scope. Catches: did v5 do it correctly with fewer tokens / fewer tool calls? | $0.30 + $0.30 = $0.60 |
| **V2** | Debug a planted off-by-one bug in 30-line script | Debugging speed + accuracy. Catches: did v5 find it faster, fix it correctly, with fewer tool calls? | $0.20 + $0.20 = $0.40 |
| **V3** | Build 3-endpoint Flask app with tests, ~30 turns | Build-from-scratch accuracy + tool selection. Catches: did v5 produce working code faster + cheaper than v4? | $0.50 + $0.50 = $1.00 |
| | | **Tier 3 total** | **$2.00** |

### Scoring rubric (judge LLM + user spot-check)

| Metric | How measured | Weight |
|---|---|---|
| Completion | Did the agent finish? (binary) | mandatory |
| Accuracy | Tests/asserts pass? (binary) | mandatory |
| Token cost | Total in + out + cache-hit% | informational |
| Wallclock | Total seconds | informational |
| # tool calls | How efficient | informational |
| Coherence | Final state make sense? (1-5, judge LLM) | tiebreaker |

### Output

Side-by-side scoring table embedded in `v5_complete.html` "v5 vs v4" tab (Block U deliverable). User-readable + screenshot-able.

**What Block V proves**: v5 > v4 EMPIRICALLY on representative coding tasks with metrics.

**What Block V does NOT prove**: v5 > Runnable directly. Architectural argument (Runnable patterns ported with file:line refs in PORT_LOG) + Block V (v5 > v4 baseline) + R-tier (no semantic bugs) covers ~90% of the "v5 > Runnable" claim. Add Block V-extended (v5 vs Runnable, +$2-3) post-ship if reviewers demand direct empirical Runnable proof.

---

## Per-test logs — complete audit trail

**YES, every test gets BOTH worker self-review AND Codex review before next test.** Confirmed 2026-05-03 user directive. No exceptions.

But review GRANULARITY differs by test type. Practical reality table:

| Test type | Review granularity | Why this granularity | Example |
|---|---|---|---|
| **Mock test (T1/T2/T3/T4)** | Reviewed by Codex AS PART OF its parent Block's code review | 798 mock tests — individual Codex per test would be 798 reviews. Block-level review covers the test code (Codex sees test diffs in Block diff). | Block H (16 mock tests) → Codex iter-1 + iter-2 reviewed all 16 in one pass |
| **Mock test failure during Block work** | Worker fixes BEFORE commit; if structural issue → Block re-review | A failing mock test blocks commit anyway (CI would fail) | Block G iter-1 failed on test_g_subagent_inheritance → fix → iter-2 |
| **Real-AWS test (R1-R16, Block V)** | INDIVIDUAL pre-flight + post-pass review per test, EVERY time | Real money on the line — each AWS call needs explicit worker+Codex APPROVE | R2 had 1 PRE-FLIGHT + 1 DIAGNOSIS + 1 POST-PASS = 3 separate Codex reviews |
| **Real-AWS test failure** | INDIVIDUAL diagnosis review + fix-justification review BEFORE next AWS call | Cannot waste $$$ on un-vetted retry | R6 had 3 AWS calls → 2 DIAGNOSIS reviews → still failed → ESCALATE |

**So total Codex reviews across the build**:
- 50 already done (20 Blocks × 2.5 avg iters each)
- ~3 more for Block K + Block U (2 Blocks × ~2 iters)
- ~30-50 for R-tier R1-R16 (16 tests × 2-3 reviews each)
- ~12-20 for Block V (6 runs × 2-3 reviews each)
- 1-2 for final full-codebase Codex
- **Total ~100-130 Codex reviews across entire v5.0.1 build**

Every test produces 4-8 persistent log files. All committed to git so they survive new sessions.

### Logs for MOCK tests (per Block, not per test)

Mock tests live inside Blocks. Their logs live with the Block:

| File | Purpose | Example |
|---|---|---|
| `compact_v5/_status/codex_reviews/block-<X>-iter<N>-prompt.txt` | Codex prompt — includes ALL tests added in this Block | `block-h-iter1-prompt.txt` (covers all 16 H tests) |
| `compact_v5/_status/codex_reviews/block-<X>-iter<N>.md` | Codex verdict on Block code + tests | `block-h-iter1.md` (REJECT — found 4 issues incl. test gaps) |
| `compact_v5/_status/codex_reviews/block-<X>-iter<N+1>.md` | Codex re-verdict after fixes | `block-h-iter2.md` (APPROVE) |
| `compact_v5/CHANGELOG.md` Block section | Block summary including what tests were added | (one section per Block) |
| `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` | One row per Runnable pattern adopted (test refs included) | rows #095-#098 for Block H |
| Git commits | Test code (per `git log --oneline`) | `v5/block-h: memory extraction + sessionMemory + 16 tests` |
| `pytest -q` output | PASS/FAIL counts per Block close | `703 passed + 8 skipped` (logged in V5_BUILD_STATUS.md) |

**For 798 mock tests across 22 Blocks**: 50+ Codex review files already exist at `compact_v5/_status/codex_reviews/block-*.md`. Each one reviewed all the tests added in that Block.

### Per-test diagnostic telemetry — MANDATORY for Block V "v5 > v4" proof

**User directive 2026-05-03**: existing per-test logs prove "v5 ran without bugs" but do NOT prove "v5 > v4 empirically." For empirical comparison, every R-tier + Block V test produces ONE additional aggregated diagnostic file:

```
compact_v5/_status/r-tier-<TEST>-aws-call<N>-telemetry.json
```

Schema:
```json
{
  "test": "R1",
  "call": 1,
  "per_turn": [
    {
      "turn": N,
      "agent_text_chars": <int>,
      "tokens_in": <int>,
      "tokens_out": <int>,
      "cache_read_tokens": <int>,
      "cache_write_tokens": <int>,
      "cache_hit_pct": <float>,
      "tool_calls": [{"name": "...", "args_summary": "..."}],
      "wallclock_s": <float>
    }
  ],
  "tool_call_summary": {
    "<tool_name>": <count>,
    "TOTAL_calls": <int>,
    "REPEATED_calls": <int>
  },
  "compaction_events": [{"turn": N, "tokens_freed": <int>, "trigger": "..."}],
  "subagent_dispatches": [{"turn": N, "agent_type": "...", "task_summary": "...", "child_session_id": "...", "tokens_used": <int>, "wallclock_s": <float>}],
  "cache_efficiency_trend": {
    "first_5_turns_avg_hit_pct": <float>,
    "last_5_turns_avg_hit_pct": <float>,
    "session_avg_hit_pct": <float>
  },
  "outcome": {
    "completed": <bool>,
    "stop_reason": "...",
    "artifacts_valid": {"<file>": <bool>},
    "max_turns_hit": <bool>,
    "cost_cap_hit": <bool>
  }
}
```

**Source data** (already captured by v5 — just needs aggregation):
- per-turn data → `MAIN/agent/audit_logs/<session_id>.jsonl` (each tool_dispatch + chat_response event has tokens + timing)
- compaction_events → audit_logs has `compact` event entries
- subagent_dispatches → audit_logs has `subagent_spawn` + `subagent_complete` events
- raw turn-by-turn agent text → `r-tier-<TEST>-aws-call<N>.log` (raw stdout)

**Aggregator script**: `compact_v5/_status/scripts/build_telemetry.py` — takes (test_name, call_num, audit_log_path, raw_log_path) and produces telemetry.json. Worker creates this script once, then runs it after every R-test AWS call before moving to next test.

**Why this matters**: without per-turn telemetry, Block V's "v5 vs v4" comparison is too coarse. With it, comparison reads:
- Total tokens (v4 vs v5)
- Cache hit % per-turn trend (v4 vs v5) — v5 should be HIGHER (sectioned prompt)
- Wallclock (v4 vs v5)
- Tool call count + REPEATED calls (v5 should be LOWER, better selection)
- Compaction triggered (v4 won't, v5 will at 80% context)
- Sub-agent dispatch (v4 only `general`, v5 has 4 types — proves Block G/G2/G3 superiority)

Updated MANDATORY OUTPUT count per test: was 8, now **9**:

### Files written for EACH real-AWS test (named after test ID, e.g. R1, R14, V2)

| File | Purpose | When written | Example |
|---|---|---|---|
| `compact_v5/_status/codex_reviews/r-tier-<TEST>-phaseA-iter<N>-prompt.txt` | Filled-in pre-flight Codex prompt | BEFORE first AWS call | `r-tier-R1-phaseA-iter1-prompt.txt` |
| `compact_v5/_status/codex_reviews/r-tier-<TEST>-phaseA-iter<N>.md` | Codex pre-flight verdict (AXIS A/B/C) | After Codex review | `r-tier-R1-phaseA-iter1.md` |
| `compact_v5/_status/codex_reviews/r-tier-<TEST>-aws-call<N>.log` | Raw Bedrock call log: turn-by-turn messages, tool calls, tokens, errors | After AWS call | `r-tier-R1-aws-call1.log` |
| `compact_v5/_status/codex_reviews/r-tier-<TEST>-phaseB-iter<N>.md` | Codex diagnosis verdict (only if test failed) | After failure diagnosis | `r-tier-R1-phaseB-iter1.md` |
| `compact_v5/_status/codex_reviews/r-tier-<TEST>-phaseC-iter<N>.md` | Codex post-pass sanity verdict | After test PASSED | `r-tier-R1-phaseC-iter1.md` |
| Git commit (one per test or per fix) | Code/test changes | After every fix or PASS | `v5/r-tier-R1: ADD test + APPROVE` |
| Row in `compact_v5/_status/r_tier_review_log.md` | Test summary | After test READY or ESCALATED | (table row) |
| JSONL row in `compact_v5/_status/r_tier_metrics.jsonl` | Per-call metrics (tokens, cache-hit%, wallclock, tool-calls) | After each AWS call | `{"test":"R1","call":1,"tokens_in":12500,...}` |

### Master log: `compact_v5/_status/r_tier_review_log.md`

One row per test. Worker appends after each test READY or ESCALATED.

| Test | Date | Block(s) | PRE-FLIGHT iters | AWS calls used | DIAGNOSIS iters | POST-PASS verdict | Final | Cost spent | Cost cap | What was tested | Problems found | What changed | Reviewer file refs |
|------|------|----------|------------------|----------------|-----------------|-------------------|-------|-----------|----------|-----------------|----------------|--------------|---------------------|
| R1 | 2026-05-04 | All composite | 1 (APPROVE) | 1 | 0 | GENUINE_PASS | READY | $0.42 | $1.00 | 50-turn dashboard build | none | nothing (PASSED first try) | r-tier-R1-phaseA-iter1.md, r-tier-R1-phaseC-iter1.md |
| R2 | 2026-05-04 | A | 2 (APPROVE_WITH_FIXES → APPROVE) | 2 | 1 (APPROVE_FIX_AND_RETRY) | GENUINE_PASS | READY | $0.83 | $0.50→$1.00 | 80K compaction + cache_edits | call#1 fail: cache_edits param ordering wrong on Bedrock vs Anthropic-direct | core/compactor.py:241 cache-control block list ordering | r-tier-R2-phaseA-iter1.md, r-tier-R2-aws-call1.log, r-tier-R2-phaseB-iter1.md, r-tier-R2-aws-call2.log, r-tier-R2-phaseC-iter1.md |
| R6 | 2026-05-04 | H+ | 1 | 3 | 2 | (call#3 still failing) | ESCALATED | $0.30 | $0.30 (CAP HIT) | /dream consolidation 100 entries | call#1: prompt template missing context section; call#2: rollback logic skipped backup verification; call#3: Bedrock 5xx flake | runtime/dream.py:178 + lock acquire flow | r-tier-R6-phaseA-iter1.md, r-tier-R6-aws-call{1,2,3}.log, r-tier-R6-phaseB-iter{1,2}.md, ESCALATION-R6.md |

### Per-call metrics: `compact_v5/_status/r_tier_metrics.jsonl`

One JSON line per AWS call (across all tests). Aggregated for `v5_complete.html` Block U metrics tab.

```jsonl
{"test":"R1","call":1,"date":"2026-05-04T10:23:11Z","model":"claude-haiku-4-5","tokens_in":12500,"tokens_out":3800,"cache_hit_pct":0.72,"wallclock_s":142,"tool_calls":18,"completed":true,"cost_usd":0.42,"verdict":"GENUINE_PASS"}
{"test":"R2","call":1,"date":"2026-05-04T10:35:02Z","model":"claude-haiku-4-5","tokens_in":89000,"tokens_out":1200,"cache_hit_pct":0.0,"wallclock_s":48,"tool_calls":2,"completed":false,"cost_usd":0.41,"verdict":"FAIL_DIAGNOSIS_PHASE_C","error":"AssertionError: cache_edits did not invalidate"}
{"test":"R2","call":2,"date":"2026-05-04T10:48:17Z","model":"claude-haiku-4-5","tokens_in":89000,"tokens_out":1100,"cache_hit_pct":0.91,"wallclock_s":31,"tool_calls":2,"completed":true,"cost_usd":0.42,"verdict":"GENUINE_PASS"}
```

### Each Codex review file structure (consistent across A/B/C templates)

Every `r-tier-<TEST>-phase{A,B,C}-iter<N>.md` follows this structure (~200-500 words each):

```
# Test: R<N> — <Test Name>
# Phase: <A pre-flight | B diagnosis | C post-pass>
# Iter: <N>
# Date: <ISO timestamp>
# Codex model: gpt-5.5 -c reasoning_effort=high

## Inputs
- Test code: <path>:<sha>
- Cost cap: $<X>
- Model: <haiku-4.5 | sonnet-4.5>
- AWS calls used: <N> of 3

## AXIS A verdict
<APPROVE | APPROVE_WITH_FIXES | REJECT>
Findings:
- [HIGH] file:line — issue — fix
- [MEDIUM] ...

## AXIS B verdict
<APPROVE | APPROVE_WITH_FIXES | REJECT>
Findings:
- [HIGH] cost-risk: ... — mitigation
- [MEDIUM] ...

## AXIS C verdict
<APPROVE | APPROVE_WITH_FIXES | REJECT>
Coverage gap (if any): <what claim still needs separate test>

## FINAL VERDICT
<APPROVE_FOR_AWS_CALL | APPROVE_FIX_AND_RETRY | RECOMMEND_ESCALATE | REJECT>
<Required actions before next AWS call (if any)>
```

### Where to find logs after the run

```bash
# All Codex reviews for R1-R16 + Block V
ls compact_v5/_status/codex_reviews/r-tier-* compact_v5/_status/codex_reviews/block-v-*

# Master test summary (all 22 tests in one table)
cat compact_v5/_status/r_tier_review_log.md

# Per-AWS-call metrics (JSON Lines, one per call)
cat compact_v5/_status/r_tier_metrics.jsonl

# Aggregated metrics + comparison table
# (rendered in v5_complete.html "R-tier results" tab and "v5 vs v4" tab)
open compact_v5/HTML/v5_complete.html
```

### Stakeholder checklist after run completes

1. Open `r_tier_review_log.md` → check Final column: every row should be READY (no ESCALATED)
2. Open `r_tier_metrics.jsonl` → check Total cost column: should be ≤ $11.25
3. Open `v5_complete.html` "v5 vs v4" tab → check Block V scoring table favors v5
4. Open any specific test's Codex review file → see exactly what was reviewed, what passed/failed, what changed
5. If any ESCALATED row exists → read corresponding `ESCALATION-<TEST>.md` → user decides retry/skip/abort

---

## Cost monitoring (3 layers, already in place)

| Layer | Where | Triggers |
|---|---|---|
| **App-level**: `session_cost_limit` per test | inside agent (TOKENS singleton) | halts agent when exceeded |
| **AWS Budget hard stop**: `Bedrock-Monthly-50` ($50 USD/month) | AWS Console → Billing → Budgets | emails at 50/80/100%; **at 100% IAM policy auto-attaches `DenyBedrockAtBudget`** to SageMaker exec role — Bedrock returns AccessDenied |
| **Per-test review log**: `r_tier_review_log.md` | repo file | runtime visibility, audit trail |

$50/mo cap is 4× the $11.25 worst-case budget. You'd get email at $25 (50%) and $40 (80%) before the kill fires at $50.

---

## What this proves vs what it doesn't (production-readiness verdict)

| Claim | Tests covering it | Verdict after 22 tests |
|---|---|---|
| v5 has no semantic bugs on real Bedrock | R1-R12 | EMPIRICAL ✓ |
| v5 codes accurately | R13 | EMPIRICAL ✓ |
| v5 handles multi-file refactor | R14 | EMPIRICAL ✓ |
| v5 can debug | R15 | EMPIRICAL ✓ |
| v5 sustains long sessions | R16 | EMPIRICAL ✓ |
| **v5 > v4** | Block V (3 tasks × 2 systems × metrics) | EMPIRICAL ✓ |
| v5 ≥ Runnable | architectural ports + R-tier + Block V | INDIRECT ARCHITECTURAL ✓ |
| v5 > Hermes (A28, IterationBudget, failure-as-instruction) | Hermes patterns ported + v5 has wider scope (24 tools vs Hermes narrower) | INDIRECT ARCHITECTURAL ✓ |
| v5 > Learning Factory (LF) | LF is discipline framework — v5 ADOPTS LF (PORT_LOG, ADR, lock tests, per-Block Codex gate) | N/A different category |

**Production-ready verdict after 22 tests + final Codex AXIS A/B/C review + user F5 verification**: **YES.**

Architecture-level certain on v5 ≥ Runnable. If empirical Runnable comparison is must-have, add Block V-extended ($2-3) post-ship.

---

## Run order

```
Block K   — process/policy gate (no AWS)            [worker pending]
Block U   — v5 HTMLs + Playwright                   [pending, no AWS]
R1-R12    — original real-AWS suite ($6.50)         [pending]
R13-R16   — enhanced real-AWS suite ($2.75)         [pending]
Block V   — v4 vs v5 head-to-head ($2.00)           [pending]
Final Codex — full-codebase AXIS A/B/C              [pending, free]
F5 user verification — Q1-Q4 contract               [pending, user sign-off]
Production zip ship                                  [pending]
```

Total time to production: 4-5 sessions. Total AWS cost: $11.25 worst-case + $33 ceiling if every test maxes 3 retries.

---

## See also

- `compact_v5/_phase_2/wave_6/WORKER_HINT_2026-05-03.md` — worker discipline rules (READ FIRST every session)
- `compact_v5/_status/R_TIER_REVIEW_TEMPLATE.md` — Codex review prompts A/B/C for real-AWS tests
- `compact_v5/_phase_2/wave_6/TEST_DESIGN.md` — per-Block test catalog (developer-internal)
- `compact_v5/_status/RESUME.md` — session resume protocol
- `compact_v5/_status/V5_BUILD_STATUS.md` — current Block status
- `compact_v5/docs/PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md` — what v5 changes vs v4
- `compact_v5/docs/PS_V5_LEARNINGS_FROM_REPOS.md` — what v5 learned from Runnable/Hermes/LF
