# PS_V5_TEST_PLAYBOOK — Master Reference for R-tier + Block V Execution

**Audience**: worker (autonomous Mode B execution) + future sessions

**Purpose**: ONE place that has every spec needed to run R1-R16 + Block V correctly. Read at start of every R-tier or Block V session.

**Last updated**: 2026-05-03

**Persistence**: committed to git, pushed to sageagent remote. Survives session restart.

---

## Read order at start of EVERY R-tier session

1. `compact_v5/_phase_2/wave_6/WORKER_HINT_2026-05-03.md` (§9.3 telemetry, §9.4 mandatory outputs, §10 review loop)
2. `compact_v5/_status/R_TIER_REVIEW_TEMPLATE.md` (Codex prompts A/B/C)
3. `compact_v5/docs/PS_V5_TEST_SET.md` (test catalog + costs)
4. **`compact_v5/docs/PS_V5_TEST_PLAYBOOK.md`** ← **THIS FILE** (build_telemetry.py spec + Block V runner + scoring rubric)

---

## Section 1 — `build_telemetry.py` — exact spec

Create at: `compact_v5/_status/scripts/build_telemetry.py`. ~150 LOC.

### Inputs

```bash
python build_telemetry.py \
  --test R1 \
  --call 1 \
  --audit-log MAIN/agent/audit_logs/<session_id>.jsonl \
  --raw-log compact_v5/_status/codex_reviews/r-tier-R1-aws-call1.log \
  --output compact_v5/_status/r-tier-R1-aws-call1-telemetry.json
```

### Algorithm

1. Parse `audit_log` (one JSON per line) into events list
2. Group events by `turn_number` (audit logger should emit `turn` key on every event; if missing, use timestamp ordering)
3. For each turn N: aggregate
   - `tokens_in` = sum of `chat_response.usage.input_tokens` for that turn
   - `tokens_out` = sum of `chat_response.usage.output_tokens`
   - `cache_read_tokens` = sum of `chat_response.usage.cache_read_input_tokens`
   - `cache_write_tokens` = sum of `chat_response.usage.cache_creation_input_tokens`
   - `cache_hit_pct` = `cache_read / (cache_read + cache_write + regular_input)` if denominator > 0 else 0.0
   - `tool_calls` = list of `tool_dispatch` events for that turn (name + truncated args)
   - `wallclock_s` = max(timestamp) - min(timestamp) for that turn
   - `agent_text_chars` = sum of `chat_response.text` length
4. `tool_call_summary`:
   - per-tool count
   - `TOTAL_calls` = sum
   - `REPEATED_calls` = count of identical (name, args) pairs called >1 time
5. `compaction_events`: filter audit_log for `event_type=="compact"`, extract `turn`, `tokens_freed`, `trigger`
6. `subagent_dispatches`: filter audit_log for `event_type in ("subagent_spawn", "subagent_complete")`, pair them by `child_session_id`, extract turn / agent_type / task_summary / tokens_used / wallclock_s
7. `cache_efficiency_trend`:
   - `first_5_turns_avg_hit_pct` = avg of cache_hit_pct for turns 1-5
   - `last_5_turns_avg_hit_pct` = avg of last 5 turns
   - `session_avg_hit_pct` = overall avg
8. `outcome`: parse from raw_log tail
   - `completed` = bool (did agent reach end_turn or hit max_turns/cost_cap)
   - `stop_reason` = string from agent's final message
   - `artifacts_valid` = dict of {file: bool} for expected output files
   - `max_turns_hit` = bool
   - `cost_cap_hit` = bool

### Output schema

See `PS_V5_TEST_SET.md` "Per-test diagnostic telemetry" section. Worker MUST match this schema exactly.

### Validation

After writing telemetry.json, worker MUST:
1. JSON-parse it (catches malformed output)
2. Verify required keys present: test, call, per_turn, tool_call_summary, compaction_events, subagent_dispatches, cache_efficiency_trend, outcome
3. Sanity check: `len(per_turn) > 0`, `outcome.completed in [True, False]`, all `cache_hit_pct in [0.0, 1.0]`
4. If any validation fails: regenerate, do NOT advance to next test

### Codex review of build_telemetry.py

Once written, Codex AXIS A review BEFORE first use. Use the standard `CODEX_REVIEW_TEMPLATE.md` for code-review (not R-tier template). Save as `codex_reviews/build-telemetry-iter1.md`. APPROVE before using on R1.

---

## Section 2 — Block V v4-side runner

### Goal

Run identical task on v4 (`compact_v4/MAIN/agent/sagemaker_agent.py`) and v5 with same:
- Model (`au.anthropic.claude-haiku-4-5-20251001-v1:0`)
- Workspace (pytest tmp_path)
- Initial prompt
- max_turns
- session_cost_limit cap

### v4 launcher pattern

v4 is a single-file monolith. Launch via:

```python
import sys
sys.path.insert(0, "compact_v4/MAIN/agent")
from sagemaker_agent import Agent, BedrockClient, CONFIG, SECURITY

# Same setup as v5 R-test
client = BedrockClient(model_id=_HAIKU_45_AU, region="ap-southeast-2", mock_mode=False)
CONFIG.workspace = str(tmp_path)
CONFIG.session_cost_limit = _BLOCK_V_TASK_COST_CAP
agent = Agent(client=client, max_turns=30)
result = agent.run(_TASK_PROMPT)
```

v4's audit_logs land at `compact_v4/MAIN/agent/audit_logs/<session_id>.jsonl` (same shape as v5 — both use AuditLogger from v4 baseline).

Worker reuses `build_telemetry.py` to aggregate v4-side telemetry. Output naming: `block-v-V1-v4-telemetry.json` and `block-v-V1-v5-telemetry.json`.

### Block V test files structure

Create:
- `compact_v5/MAIN/agent/tests/r_tier/test_block_v.py` — runs all 3 V-tasks on BOTH v4 + v5
- `compact_v5/MAIN/agent/tests/r_tier/block_v_fixtures/` — task workspaces (v4 and v5 share same fixtures)
  - `v1_refactor/` — 50-line Python module to refactor
  - `v2_debug/` — 30-line script with planted off-by-one
  - `v3_flask/` — empty workspace; agent builds 3-endpoint Flask CRUD with tests

Each task has its own pytest function. Each function:
1. Sets up workspace
2. Runs v4 first (1 AWS call cap) → captures telemetry
3. Runs v5 next (3 AWS calls cap if fix needed) → captures telemetry
4. Writes `block-v-<TASK>-comparison.md` with side-by-side results

### Block V cost per task

| Task | v4 cap | v5 cap | Total cap |
|---|---|---|---|
| V1 refactor | $0.30 | $0.30 (3 calls × $0.10 cap each) | $0.60 |
| V2 debug | $0.20 | $0.20 | $0.40 |
| V3 Flask | $0.50 | $0.50 | $1.00 |
| | | **Block V total** | **$2.00** |

---

## Section 3 — Block V scoring rubric

For each task (V1, V2, V3), compute these axes from telemetry.json. v5-wins if SUPERIOR_AXES > INFERIOR_AXES with weighted score.

### Axes + weights

| Axis | How measured | Weight | Direction (lower=better OR higher=better) |
|---|---|---|---|
| Completion | `outcome.completed and outcome.artifacts_valid all True` | 5 | higher |
| Token efficiency | `sum(per_turn.tokens_in + per_turn.tokens_out)` | 3 | LOWER better |
| Cache efficiency | `cache_efficiency_trend.session_avg_hit_pct` | 3 | higher |
| Tool use efficiency | `tool_call_summary.TOTAL_calls` | 2 | LOWER better |
| Tool use waste | `tool_call_summary.REPEATED_calls` | 2 | LOWER better |
| Wallclock | `sum(per_turn.wallclock_s)` | 1 | LOWER better |
| Sub-agent use (when appropriate) | `len(subagent_dispatches)` | 1 | task-dependent (V3 should use; V1/V2 should NOT) |
| Compaction triggered (when needed) | `len(compaction_events)` | 1 | task-dependent (only long tasks) |
| Final cost | `outcome.cost_usd` | 2 | LOWER better |

### Per-task verdict

For each task: compute weighted-axis-wins for v5 vs v4.

```
v5_score = sum(weight[axis] for axis in axes if v5_better(axis))
v4_score = sum(weight[axis] for axis in axes if v4_better(axis))
tie_score = sum(weight[axis] for axis in axes if abs(v5 - v4) < tolerance)

if v5_score > v4_score + 3:
  verdict = "v5 wins decisively"
elif v5_score > v4_score:
  verdict = "v5 wins narrowly"
elif v5_score == v4_score:
  verdict = "tie"
elif v4_score > v5_score:
  verdict = "v4 wins"
```

Tolerance per axis: ±5% for token/wallclock; exact match for completion/artifacts.

### Block V overall verdict

| # tasks v5-won | Verdict |
|---|---|
| 3 of 3 | v5 > v4 PROVEN |
| 2 of 3 | v5 > v4 LIKELY (note specific weakness) |
| 1 of 3 | INCONCLUSIVE — investigate |
| 0 of 3 | v5 ≤ v4 — STOP, escalate to user |

### Output

Write `compact_v5/_status/block-v-FINAL-comparison.md` with:
- Task-by-task scoring table
- Per-axis side-by-side numbers
- Final verdict
- Specific evidence (file:line in telemetry.json) for each claim

This is the EMPIRICAL evidence for "v5 > v4" in the FINAL_v5.0.1_PRODUCT_SUMMARY.md and the eventual Block U `v5_complete.html` "v5 vs v4" tab.

---

## Section 4 — Worker checklist (verbatim, use at every test)

```
PRE-FLIGHT (free):
  [ ] Test code written + collects clean (pytest --collect-only)
  [ ] Filled-in TEMPLATE A pre-flight prompt saved
  [ ] Worker self-review noted in commit msg
  [ ] Codex TEMPLATE A review saved
  [ ] BOTH worker + Codex APPROVE_FOR_AWS_CALL recorded

AWS CALL (real money):
  [ ] taskkill //F //IM codex.exe (clear zombies)
  [ ] tee output to r-tier-<TEST>-aws-call<N>.log
  [ ] Test runs to completion or cap

POST-CALL:
  [ ] Run build_telemetry.py → r-tier-<TEST>-aws-call<N>-telemetry.json
  [ ] Validate telemetry.json (JSON-parse + required keys + sanity)
  PASS path:
    [ ] Codex TEMPLATE C post-pass sanity check (includes telemetry sanity)
    [ ] BOTH worker + Codex GENUINE_PASS recorded
    [ ] Append JSONL row to r_tier_metrics.jsonl
    [ ] Append row to r_tier_review_log.md
  FAIL path:
    [ ] Codex TEMPLATE B diagnosis review
    [ ] If APPROVE_FIX_AND_RETRY: apply fix, commit, re-run from PRE-FLIGHT
    [ ] If 3 AWS calls exhausted: write ESCALATION-<TEST>.md, STOP
  COMMIT:
    [ ] git add all 9 files for this test (per WORKER_HINT §9.4)
    [ ] git commit -m "v5/r-tier-<TEST>: <verdict>"
    [ ] git push sageagent v5-build
    [ ] ONLY now move to next test

If ANY checkbox missed → test INCOMPLETE → do NOT advance.
```

---

## Section 4.5 — Gap closures 2026-05-03 (user "100%" pushback)

### Gap A: Bedrock `thinking` blocks NOT in telemetry schema

ADD to telemetry.json schema (per_turn array each item):

```json
{
  "turn": N,
  ...existing fields...,
  "thinking_text": "<full thinking block text if extended thinking enabled, else null>",
  "thinking_tokens": <int or 0>
}
```

`build_telemetry.py` reads `chat_response.thinking` from audit_logs (v5 BedrockClient should already log thinking blocks if the model returned any with `thinking_enabled=True`). If field missing in audit log, set null + 0.

### Gap B: PS#4 (thinking visibility) needs explicit R-tier scenario

ADD R17 scenario:

| # | Scenario | Catches | Cost cap | Model |
|---|---|---|---|---|
| **R17 — Thinking visibility** | Send hard-reasoning prompt ("Solve 2-step math problem with extended thinking enabled, max_tokens=4096"). Verify agent thinking block is captured + returned to chat history + visible in telemetry.json `per_turn[].thinking_text`. | PS#4 fix end-to-end on real Bedrock | $0.30 | Sonnet 4.5 (only Sonnet supports extended thinking reliably) |

R-tier total: $11.25 → $11.55 (negligible cost increase, closes the gap).

Add R17 test file: `compact_v5/MAIN/agent/tests/r_tier/test_r17_thinking_visibility.py`. Same review discipline as R1-R16.

### Gap C: v5 > Runnable EMPIRICAL — DEFER decision to user

OPTION 1 (current): architectural argument only — Runnable patterns ported with file:line refs in PORT_LOG. Defensible but not empirical.
OPTION 2: add Block V-extended (v5 vs Runnable) — +$2-3 cost + Runnable TS runtime setup overhead (~30 min worker time).

User decides at F5 verification gate. Worker proceeds with Option 1 by default (architectural). If user requests at F5, worker schedules Block V-extended as separate session.

---

## Section 5 — Trigger phrases worker recognizes

| User says | Worker action |
|---|---|
| "go" | Resume autonomous execution per AFK plan |
| "stop" | Halt at current PHASE; do NOT start new AWS call |
| "skip Block V" | Mark Block V as DEFERRED, jump to F5 user gate |
| "halt R-tier" | Stop after current R-test completes; do NOT start next |
| "ESCALATE" | Write ESCALATION-<TEST>.md immediately, halt |
| "show progress" | Print last 3 rows of r_tier_review_log.md + total cost |

---

## Why this playbook exists

User directive 2026-05-03: "are we 100% certain all test well designed, all test, logs, details will be captured to fully diagnostic the v5 when testing in real?"

Honest answer was 90% — 3 gaps existed:
1. build_telemetry.py spec wasn't formalized → fixed in §1 above
2. Block V v4-side runner not specified → fixed in §2
3. Block V scoring rubric not formalized → fixed in §3

This playbook closes all 3 gaps and persists the closure to git so future sessions don't have to re-invent any of this.
