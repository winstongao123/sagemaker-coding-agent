# R-tier Review Template (historical Codex version — superseded for v5 redo)

> **2026-05-04 OVERRIDE**: do not use Codex CLI as reviewer for the v5
> completion redo. Use Claude Code CLI reviewer prompts under
> `_status/v5_completion_audit/`. This file is retained for historical R-tier
> evidence and template content only.

Used at every PHASE A (pre-flight) and PHASE C (diagnosis) per WORKER_HINT_2026-05-03.md §10. Fill `{{...}}` placeholders. Paste into `codex exec --full-auto -s read-only -m gpt-5.5 -c model_reasoning_effort="high" "<prompt>"`.

**Critical rule**: Codex must APPROVE before EACH AWS call. Hard cap = 3 AWS calls per test, total. Both worker AND Codex must agree.

---

## CONTEXT-PASSING PROTOCOL (worker MUST follow when filling templates)

Codex CLI runs in `--sandbox read-only` and CAN read any file in the repo via its own tools. But for token efficiency + reliability, worker MUST inline these snippets directly in the filled-in template (not just paths):

| Section | What to inline | Why |
|---|---|---|
| Test code (PHASE A) | Full test file content (typically <300 lines) | Codex needs to see assertions to grade them |
| Filled scenario fixtures | Inline 5-row CSV / 30-line script / etc. | Critical to grade if test exercises what it claims |
| Telemetry summary (PHASE B/C) | Inline `tool_call_summary` + `outcome` + first/last 5 entries of `per_turn` | Codex needs metrics without parsing 1MB JSON |
| Raw log tail (PHASE B/C) | Inline LAST 100 LINES of `aws-call<N>.log` (not full 500KB-1MB) + the file path so Codex can cat more if needed | Captures stop_reason + final agent text + any error |
| Worker's PASS 1 grade (PASS 2) | Inline FULL PASS 1 markdown | Codex grades independently but should see worker's view to flag disagreements |
| Previous iter findings (iter-N+1) | Inline PREVIOUS Codex verdict's findings (not whole review) | Codex confirms each finding closed |
| File paths (always) | Provide for Codex to cat if it wants more | Fallback if inline summary insufficient |

**Hard rule**: never pass JUST a path expecting Codex to read the file. Always inline the relevant excerpt PLUS provide path for deeper exploration. This protects against:
- Codex token-budget exhaustion mid-review
- Codex not realizing it needs to read a specific file
- Inconsistent reviews depending on what Codex chose to read

---

## TEMPLATE A — PHASE A pre-flight review (BEFORE first AWS call)

```
You are reviewing the PRE-FLIGHT design of an R-tier real-AWS test before
any Bedrock call is made. Each AWS call costs real money (cap ${{COST_CAP}}).
Your job is to catch broken test design, missing assertions, or wasted-spend
risk BEFORE we hit Bedrock.

CONTEXT
- Test: {{TEST_NAME e.g. R14 multi-file refactor}}
- Block(s) being validated: {{BLOCK_IDS e.g. Block H + Block A}}
- What it claims to prove: {{CLAIM e.g. v5 can refactor across 3 files and re-run pytest}}
- Cost cap (session_cost_limit): ${{COST_CAP}}
- Model: {{MODEL e.g. claude-haiku-4-5}}
- Test file: {{TEST_FILE_PATH}}
- Scenario fixtures: {{FIXTURE_PATHS}}

PRODUCE THREE INDEPENDENT VERDICTS.

=== AXIS A — Test design soundness ===
- Does the scenario actually exercise what it claims? Cite the assertion(s)
  that would fail if v5 regressed in the relevant Block.
- Are assertions specific (test specific behavior), not loose (test "no error")?
- Will this test pass even if v5 silently does something wrong? (false-positive risk)
- Are setup/teardown correct? Files cleaned up? No state leaks?
- Could the test pass on a mock that masks a real-Bedrock bug?

Output:
AXIS A VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT
Findings: [severity] file:line — issue — fix

=== AXIS B — Cost-control soundness ===
- Does the scenario fit within ${{COST_CAP}} on AU-Haiku-4.5 at **$1.10/MTok in /
  $5.50/MTok out** (AU geo profile = base $1/$5 × 1.10 premium per Anthropic
  pricing)? AU-Sonnet-4.5: **$3.30/MTok in / $16.50/MTok out**. Estimate token
  volume from the prompt + expected turn count.
- Is `session_cost_limit` actually enforced in the test? Cite the line.
- Could a model loop (e.g. retries failing tool calls) blow the cap before halt?
- Is there a hard turn-limit safeguard? (max_iterations or similar)
- For long-session tests: is compaction expected to fire? Cite the assertion.

Output:
AXIS B VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT
Findings: [cost-risk] specific scenario — mitigation

=== AXIS C — Coverage of v5 EMPIRICAL evidence ===
- What part of v5's PRODUCTION-READINESS does this test contribute empirical
  evidence for? (PS_problem fix / coding ability / sub-agent / memory /
  context / tool use / UX edge / infra resilience)
- Is the claim falsifiable from the test result, or is it just "ran without error"?
- v5-only: Block V (head-to-head v4) DROPPED per user 2026-05-03. v5 vs v4
  vs Runnable comparison stays ARCHITECTURAL ONLY (PORT_LOG file:line refs).
  Do NOT request side-by-side runs.

Output:
AXIS C VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT
Coverage gap (if any): {{what claim still needs separate test}}

=== FINAL ===
PRE-FLIGHT VERDICT: APPROVE_FOR_AWS_CALL | REJECT (do not run AWS)
If REJECT: required fixes before next pre-flight review.
If APPROVE: log to r_tier_review_log.md and proceed to AWS call.
```

---

## TEMPLATE B — PHASE C diagnosis review (AFTER an AWS call FAILED)

```
An R-tier test JUST failed on real Bedrock. AWS call #{{N}} of 3 max consumed.
You are reviewing the worker's failure-diagnosis BEFORE we spend AWS call #{{N+1}}
on a fix. Worker proposes a root cause and a fix — judge both before approving
the next spend.

CONTEXT
- Test: {{TEST_NAME}}
- AWS call number that just failed: #{{N}}
- Cost spent so far on this test: ${{COST_USED}} of ${{COST_CAP}} cap
- Calls remaining in 3-call cap: {{3 - N}}
- Bedrock error / assertion failure: {{ERROR_MESSAGE_OR_ASSERTION_FAIL}}
- Agent log excerpt (last 50 lines): {{LOG_EXCERPT}}

WORKER'S DIAGNOSIS:
{{WORKER_DIAGNOSIS}}

WORKER'S PROPOSED FIX:
{{FIX_DIFF or fix description}}

PRODUCE THREE VERDICTS.

=== AXIS A — Diagnosis correctness ===
- Is the worker's root-cause hypothesis supported by the log evidence?
- Could there be a simpler / different root cause the worker missed?
- Is this a v5 bug, a test-design bug, a Bedrock infra issue, or model flake?
  (Bedrock infra issue = NOT counted toward 3-call cap; escalate to user instead.)

Output:
AXIS A VERDICT: AGREE | DISAGREE | INSUFFICIENT_EVIDENCE
If DISAGREE: alternative root-cause hypothesis.
If INSUFFICIENT_EVIDENCE: what additional log/data is needed (no AWS call required to gather).

=== AXIS B — Fix soundness ===
- Does the proposed fix actually address the root cause from AXIS A?
- Does the fix introduce regression risk to other Blocks? Cite affected files.
- Does the fix fit v5 architecture (combined v4 + Runnable + Hermes + LF)?
- Will a lock test be added so this failure cannot recur silently?

Output:
AXIS B VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT
Findings: file:line — issue — required change

=== AXIS C — Spend-justification ===
- Given {{3 - N}} AWS calls remain, is this fix likely to PASS on the next call?
  (If "unlikely", recommend ESCALATE rather than burn AWS spend on low-probability
  attempt.)
- Is the fix small enough that we won't need a second fix iteration?

Output:
AXIS C VERDICT: APPROVE_FOR_AWS_RETRY | RECOMMEND_ESCALATE
Confidence next-call passes: {{HIGH | MEDIUM | LOW}}
If LOW + only 1 call remaining: recommend ESCALATE.

=== FINAL ===
DIAGNOSIS VERDICT: APPROVE_FIX_AND_RETRY | REJECT_FIX | ESCALATE
If APPROVE_FIX_AND_RETRY: worker applies fix → commits → re-runs pre-flight
(TEMPLATE A) on the FIXED test → only then AWS call #{{N+1}}.
If ESCALATE: stop, do NOT spend AWS call #{{N+1}}, ask user.
```

---

## TEMPLATE C — POST-PASS review (AFTER an AWS call PASSED)

Even on PASS, we want a quick Codex sanity check that the result is real, not a false-positive (e.g., test passed because assertion was too loose).

```
An R-tier test JUST passed on real Bedrock. Verify the PASS is real before
tagging READY and moving to next test.

CONTEXT
- Test: {{TEST_NAME}}
- AWS call that passed: #{{N}} of 3
- Cost: ${{COST_USED}}
- Tokens in/out/cache-hit-pct: {{METRICS}}
- Wallclock seconds: {{WALLCLOCK}}
- Tool-call count: {{TOOL_CALLS}}
- Output artifact (if any): {{OUTPUT_PATH}}

QUESTIONS:
1. Did the assertions actually verify what the test claims? Or did they pass
   trivially (e.g. "assert response is not None" instead of "assert response
   contains correct value")?
2. Are the metrics in expected range? (e.g. cache-hit-pct should be >50% on
   long sessions; if 0% something's wrong even though test "passed")
3. Did the agent take a reasonable path, or did it succeed via lucky workaround?
4. Output artifact valid? (e.g. .docx opens, .csv parses, code compiles)

Output:
POST-PASS VERDICT: GENUINE_PASS | LIKELY_FALSE_POSITIVE | NEEDS_RE_RUN_WITH_TIGHTER_ASSERTIONS
If GENUINE_PASS → log r_tier_metrics.jsonl + tag READY + next test
If LIKELY_FALSE_POSITIVE → tighten assertions + re-pre-flight (counts toward 3-call cap)
If NEEDS_RE_RUN → escalate to user (don't burn AWS automatically)
```

---

## Per-test review log

Every R-tier scenario (R1-R19; R18 has 15 sub-scenarios E1-E15, R19 has 10 U1-U10) maintains a row in `compact_v5/_status/r_tier_review_log.md`:

| Test | PHASE A iters | AWS calls used | PHASE C iters | Final verdict | Cost |
|------|---------------|----------------|---------------|---------------|------|
| R1   | 1 (APPROVE)   | 1              | 0             | READY         | $0.42 |
| R2   | 2 (APPROVE_WITH_FIXES → APPROVE) | 2 | 1 (APPROVE_FIX_AND_RETRY) | READY | $0.83 |
| R6   | 1             | 3              | 2             | ESCALATED     | $0.30 (cap hit) |
