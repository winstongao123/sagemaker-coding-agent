# R-tier Gate Status

> **2026-05-04 OVERRIDE**: R-tier review approval for the v5 completion redo
> must come from Claude Code CLI reviewer prompts under
> `_status/v5_completion_audit/`, not Codex CLI review.

Date: 2026-05-05

Purpose: make the real-AWS validation fail closed until every test has enough
review, telemetry, cost accounting, and persisted evidence to support the
v5.0.1 production-readiness decision.

## Gate commands

Run these before any new AWS call:

```bash
cd D:/Github/sagemaker-coding-agent
py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root .
```

Run this after a specific test passes, before advancing:

```bash
py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root . --test R1
```

Run this before each AWS batch to inspect cloud budget headroom:

```bash
aws budgets describe-budget --account-id 903039434627 --budget-name Bedrock-Monthly-50
```

The local gate enforces:

- `r_tier_test_matrix.json` exists, contains all 42 required scenarios, and
  totals exactly `$14.25`
- the 42 v5-only scenarios are materialized as executable R-tier tests
- `_status/r_tier_metrics.jsonl` exists and total local recorded spend stays
  at or below `$14.25`
- per-scenario local spend stays at or below the scenario cap
- a completed test has phase A prompt/review, raw AWS log, phase C review,
  telemetry JSON, quality review, metrics row, and review-log row
- telemetry JSON has the required review schema and non-empty `per_turn`

## AFK worker prompt

Use `compact_v5/docs/CODEX_AFK_WORKER_PROMPT.md` for a fresh autonomous
worker session. It contains:

- exact first commands
- required docs to read
- per-test loop
- AWS Budget checks
- local cost cap rules
- mandatory files
- commit/push requirements
- escalation triggers where the worker must stop and wait for the user

AFK is allowed only under that prompt. The worker may continue test by test
while all gates pass, but must stop on any escalation trigger.

Canonical test queue:

- machine-readable: `compact_v5/_status/r_tier_test_matrix.json`
- human-readable: `compact_v5/_status/R_TIER_PENDING_TESTS.md`

Operating contracts:

- evidence: `compact_v5/_status/R_TIER_EVIDENCE_CONTRACT.md`
- worker behavior: `compact_v5/_status/R_TIER_WORKER_BEHAVIOR_CONTRACT.md`

## Current status

AWS/R-tier execution has started under
`v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md`. Do not use stale
queue order from `R_TIER_PENDING_TESTS.md`.

Completed and pushed:

- R1: call2 Phase C `GENUINE_PASS`, `r_tier_gate.py --test R1` passed on
  refresh after the Unicode stdout fix. Call1 diagnostic crash spend remains
  preserved.
- R2: call1 Phase C `GENUINE_PASS`, `r_tier_gate.py --test R2` passed on
  refresh. This remains the real compaction/recall evidence row.
- R4: call1 Phase C `GENUINE_PASS`, `r_tier_gate.py --test R4` passed.
  Haiku validated the A-16 time-based cold-cache microcompact code path at
  `$0.0230` using the supported injectable threshold instead of a 30-minute
  wall-clock wait. Evidence includes typed `compact_micro_start` /
  `compact_micro_end`, `microcompact_saved_tokens=50360`, two cleared old
  tool-result markers, numeric cache fields, and no repeated tool/failure loop.
  The older `ESCALATION-R4.md` remains preserved as superseded historical
  deferment evidence, not current disposition.
- R5: call1 Phase C `GENUINE_PASS`, `r_tier_gate.py --test R5` passed.
  Haiku validated the exec-limit redirect path at `$0.0157` using the approved
  lowered-cap same-code-path fixture. Evidence includes the blocked exec marker,
  the "other tools still work" recovery instruction, non-exec recovery, and no
  unrelated edits.
- R13: Phase C `GENUINE_PASS`, `r_tier_gate.py --test R13` passed.
- R15: Phase C `GENUINE_PASS`, `r_tier_gate.py --test R15` passed.
- R14: Phase C `GENUINE_PASS`, `r_tier_gate.py --test R14` passed. Artifact
  pass only; serious process-quality follow-up is open in
  `R_TIER_PROCESS_QUALITY_FOLLOWUPS.md`.
- R19-U1: Stage 4 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R19-U1` passed. Low follow-up open for direct
  chat-text clarification instead of `ask_user`.
- R19-U2: Stage 4 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R19-U2` passed.
- R19-U3: Stage 5 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R19-U3` passed. R14/R19-U3 process blocker did not
  recur; one isolated `bash_cd_blocked` event remains a quality penalty, not a
  blocker.
- R19-U6: Stage 5 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R19-U6` passed.
- R19-U7: Stage 5 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R19-U7` passed with `breaker_fired=true`.
- R18-E7: Stage 5 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R18-E7` passed. Call1 diagnostic cap exceed remains
  preserved; call2 passed under the $0.10 planned cap.

- R19-U4: Stage 6 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R19-U4` passed. Call1 diagnostic bundle-blocked spend
  remains preserved.
- R19-U5: Stage 6 bundle call2 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R19-U5` passed. Call1 diagnostic predicate-failure
  spend remains preserved.
- R16: Stage 7 call1 Phase C `GENUINE_PASS`, `r_tier_gate.py --test R16`
  passed. Haiku completed the bounded Flask CRUD app at `$0.0205`, with all
  required `software_builder_subchecks`, numeric cache evidence, forced/local
  compaction evidence, unchanged fixture tests, and no R14/R19-U3 guard-loop
  recurrence.
- R19-U10: Stage 8 call1 Phase C `GENUINE_PASS`,
  `r_tier_gate.py --test R19-U10` passed. Haiku completed the final coherence
  report at `$0.0134` using the approved prebuilt 150-logical-turn transcript
  substitution. Evidence includes three typed prebuilt compaction events, two
  prebuilt model-switch events, final anchor preservation, and no repeated
  guard-loop recurrence. This does not claim 150 live Bedrock calls, live model
  switching, or natural compaction.
- R8, R18-E2, R18-E5, R18-E9, and R18-E12: zero-cost mock cleanup bundle
  Phase A returned `APPROVE_FOR_LOCAL_MOCK`, local pytest reported `5 passed`,
  Claude Phase C returned `GENUINE_PASS`, and per-test gates passed. These
  rows used `local-call` evidence and recorded `$0.0000` spend; no AWS call was
  authorized.
- R6 and R19-U9: bundled `/dream` call1 Phase A returned
  `APPROVE_FOR_AWS_CALL`, AWS Budget was healthy before spend, the real Haiku
  `/dream` path completed at `$0.0059` total shared spend (`$0.0029` allocated
  to each row), Claude Phase C returned `GENUINE_PASS`, and
  `r_tier_gate.py --test R6` / `--test R19-U9` passed. Evidence preserved
  HYDRA-LIME, ap-southeast-2, prod/db/password, Priya, INC-4242, and Python
  3.12; duplicate/stale notes were reduced; DreamLock released; backup existed;
  telemetry showed zero tool calls and zero failure-loop events. A low,
  non-blocking `/dream` output-shape polish follow-up remains tracked in
  `R_TIER_PROCESS_QUALITY_FOLLOWUPS.md`.
- R7: call1 Phase A returned `APPROVE_FOR_AWS_CALL`, AWS Budget was healthy
  before spend, the same Agent session made a live Haiku 4.5 AU -> Sonnet 4.5
  AU Bedrock switch, Sonnet recalled `R7-CONTEXT-VIOLET-913`, numeric
  cache/model usage evidence was recorded, cost was `$0.0175`, Claude Phase C
  returned `GENUINE_PASS`, and `r_tier_gate.py --test R7` passed.
- R11: call1 Phase A returned `APPROVE_FOR_AWS_CALL`, AWS Budget was healthy
  before spend, Sonnet 4.5 AU completed the R1-style dashboard/report workflow
  at `$0.0995`, produced valid `chart.png` and `report.docx`, Claude Phase C
  returned `GENUINE_PASS`, and `r_tier_gate.py --test R11` passed.
- Final post-AWS gate: `py -3.11 compact_v5/_status/scripts/r_tier_gate.py
  --repo-root .` passed after R11. All 42 matrix rows now have accepted
  evidence state (`READY` or `DISPOSITION_OK`), and production readiness is
  pending final post-AWS Claude review.

The local no-AWS gate still passes for suite materialization and cost guard:

- executable R-tier coverage exists for all 42 required scenario markers
- R6-R16, R18-E1..E15, and R19-U1..U10 are materialized in
  `MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py`
- those new specs are zero-cost Phase A contracts, not AWS pass evidence
- `_status/r_tier_metrics.jsonl` remains the spend ledger and must stay at or
  below `$14.25`
- `_status/r_tier_review_log.md` remains the review ledger for READY or
  ESCALATED rows
- `_status/r_tier_test_matrix.json` is initialized and totals `$14.25`
- `_status/R_TIER_PENDING_TESTS.md` lists every pending test, benefit, and
  ready criterion

Do not claim the R-tier suite is production-ready until each required scenario
has Claude-reviewed Phase A approval, allowed AWS/mock execution, phase C
review, telemetry, quality evidence, metrics, and `r_tier_gate.py --test
<TEST>` pass, and the open process-quality follow-ups are resolved or accepted
by final review.

## Stage 5 Call1 Diagnostic Stop And Call2 Resolution

Stage 5 call1 ran on 2026-05-06 and stopped correctly:

- R19-U3: diagnostic/non-ready spend `$0.1090`; artifact path mostly succeeded
  but the R14 repeated failed tool-loop class recurred. Status:
  `PROCESS_BLOCKER_LOCAL_FIX_PENDING_CLAUDE_REVIEW`.
- R18-E7: diagnostic/non-ready spend `$0.1022`; exceeded the `$0.10` cap before
  READY evidence. Status: `PROCESS_BLOCKER_LOCAL_FIX_PENDING_CLAUDE_REVIEW`.
- R19-U6: functional member pass inside blocked bundle.
- R19-U7: functional member pass inside blocked bundle with `breaker_fired=true`.

No prior failed/non-ready spend may be deleted, hidden, or globally reset.
The R14/R19-U3 process blocker was fixed locally, approved by Claude CLI, and
verified by Stage 5 call2 on Haiku. Continue recurrence watch in R16 and later
software-builder tests; any non-intentional repeated guard-class loop remains a
matrix stop condition.

Local blocker fix summary:

- `compact_v5/_status/codex_reviews/r-tier-R14-R19-U3-process-blocker-fix-summary.md`

## Fixes landed in this hardening pass

- `core/query_engine.py` now emits one `chat_response` audit event per Bedrock
  turn, containing usage, cache fields, thinking text, assistant text,
  stop reason, and tool-call summaries. This allows real per-turn telemetry
  instead of relying only on tool-dispatch timing heuristics.
- `build_telemetry.py` now reads both legacy top-level `response` payloads and
  the new `parameters.response` payload emitted by QueryEngine.
- `build_telemetry.py` now reads all JSONL files in an audit directory. R16
  surfaced that a forced/local compaction JSONL and a session JSONL can coexist
  in the same audit directory; the telemetry builder must aggregate both rather
  than picking only the newest file.
- `build_telemetry.py` now extracts `model_switch_events` from audit logs so
  R19-U10 model-switch fixture evidence is visible in canonical telemetry.
- `r_tier_gate.py` was added as a local evidence/cost guard.
- `r_tier_gate.py --repo-root .` now checks per-test evidence for every matrix
  row by default. Use `--skip-evidence` only for local suite/cost development
  checks; the final gate must not use it.

## Mock verification

Zero-AWS tests run after the hardening pass:

```text
py -3.11 -m pytest tests/integration/test_build_telemetry.py tests/integration/test_unicode_safe_output.py tests/integration/test_r_tier_gate.py -q
15 passed

py -3.11 -m pytest tests/integration/test_block_b.py -q
28 passed, 1 skipped
```

Zero-AWS R-tier readiness verification on 2026-05-04:

```text
py -3.11 compact_v5/_status/scripts/r_tier_gate.py --repo-root .
R-tier gate PASSED

$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/r_tier/test_r6_to_r19_readiness_specs.py -q
108 passed

$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_r_tier_gate.py -q
7 passed

$env:PYTHONPATH='D:\Github\sagemaker-coding-agent\compact_v5\MAIN\agent'
py -3.11 -m pytest compact_v5/MAIN/agent/tests/r_tier -q
108 passed, 6 skipped
```

## AWS spend rule

No additional AWS call should run unless:

1. the relevant test has passed phase A review,
2. the expected remaining local cap is enough for the test,
3. AWS Budget headroom is confirmed,
4. raw output is teed to `_status/codex_reviews/r-tier-<TEST>-aws-call<N>.log`,
5. telemetry and quality files are generated immediately after the call,
6. `r_tier_gate.py --test <TEST>` passes before moving on.

## AWS Budget snapshot

Latest checked during Stage 6 on 2026-05-06 with:

```bash
aws budgets describe-budget --account-id 903039434627 --budget-name Bedrock-Monthly-50
```

Result:

- budget limit: `$50.00`
- actual spend: `$0.00`
- forecasted spend: `$0.047`
- health status: `HEALTHY`
- local R-tier ledger before Stage 6 call1: `$1.2912`
- Stage 6 call1 diagnostic/non-ready spend added:
  - R19-U4: `$0.0529`
  - R19-U5: `$0.0366`
- Stage 6 call2 READY spend added:
  - R19-U4: `$0.0537`
  - R19-U5: `$0.0309`
- Stage 7 R16 call1 READY spend added:
  - R16: `$0.0205`
- Stage 8 R19-U10 call1 READY spend added:
  - R19-U10: `$0.0134`
- R4 call1 READY spend added:
  - R4: `$0.0230`
- R17 call1 READY spend added:
  - R17: `$0.0307`
- local R-tier ledger after R17: `$1.5529`
- zero-cost mock cleanup rows added after R17:
  - R8: `$0.0000`
  - R18-E2: `$0.0000`
  - R18-E5: `$0.0000`
  - R18-E9: `$0.0000`
  - R18-E12: `$0.0000`
- local R-tier ledger after mock cleanup remains `$1.5529`
- R6/R19-U9 shared `/dream` call1 READY spend added:
  - R6: `$0.0029`
  - R19-U9: `$0.0029`
- R7 call1 READY spend added:
  - R7: `$0.0175`
- R11 call1 READY spend added:
  - R11: `$0.0995`
- local R-tier ledger after R11: `$1.6757`

## R17 Thinking Visibility Resolution

R17 is READY as of 2026-05-06:

- Phase A iter2 returned `APPROVE_FOR_AWS_CALL` after the runner was corrected
  to satisfy the Bedrock invariant `max_tokens > thinking_budget`.
- AWS Budget was healthy before spend.
- R17 call1 ran only the approved Sonnet 4.5 AU thinking-visibility scenario.
- Cost was `$0.0307`, under the `$0.30` planned cap and `$0.36` hard retry
  ceiling.
- Evidence captured non-empty thinking on both required surfaces:
  assistant history `thinking_chars=1611` and audit/telemetry source
  `audit_thinking_chars=1611`.
- Canonical telemetry includes non-empty `per_turn[0].thinking_text` and
  numeric cache fields (`cache_read_tokens=0`, `cache_write_tokens=3228`).
- Claude Phase C returned `GENUINE_PASS`.
- `r_tier_gate.py --repo-root . --test R17` passed.

## Zero-Cost Mock Cleanup Resolution

R8, R18-E2, R18-E5, R18-E9, and R18-E12 are READY as of 2026-05-06:

- The matrix declares all five rows as `kind=mock`, `model=Mock`, and
  `cost_cap_usd=0.0`.
- Claude Phase A returned `APPROVE_FOR_LOCAL_MOCK`; no AWS spend was
  authorized.
- `test_r_tier_mock_cleanup.py` passed locally with five deterministic locks:
  malformed JSON-string tool args, Bedrock HTML 5xx classification and
  humanization, corrupt session JSON skip, snapshot disk-full safety, and
  audit-log retention.
- The final gate now supports `local-call` raw logs, telemetry, and quality
  files only for matrix rows whose `kind` is `mock`. Cost checks are unchanged,
  so any nonzero mock-row spend still fails the gate.
- Claude Phase C returned `GENUINE_PASS`.
- `r_tier_gate.py --repo-root . --test R8`, `R18-E2`, `R18-E5`, `R18-E9`, and
  `R18-E12` passed.

## Reviewed Disposition Resolution

R9, R10, R12, R18-E1, R18-E3, R18-E4, R18-E6, R18-E8, R18-E10, R18-E11,
R18-E13, R18-E14, R18-E15, and R19-U8 are `DISPOSITION_OK` as of 2026-05-06:

- Claude disposition iter1 returned `APPROVE_DISPOSITION_PLAN`, classifying
  these rows as no-new-AWS dispositions or mappings to existing AWS evidence.
- New local locks were added and passed for the only local gaps Claude found:
  R18-E4 canonical skill activation/no alias surface, R18-E11 subagent timeout
  with parent compaction/resume, and R18-E13 Unicode/RTL `/dream` memory
  round-trip.
- `r_tier_gate.py` now supports a third evidence state keyed by matrix
  `status=DISPOSITION_OK`. These rows require per-test disposition files,
  zero-cost metrics, Phase C `DISPOSITION_OK`, and review-log rows, but do not
  require fake raw logs, telemetry, or quality files.
- Claude Phase C iter2 returned `DISPOSITION_OK`.
- Per-test gates passed for all 14 disposition rows.
- The default final gate now passes all 42 matrix rows.
