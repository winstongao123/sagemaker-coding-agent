# PS_TEST_REVIEW_FINAL

Date: 2026-05-06
Branch: `v5-build`
Purpose: final human-readable test review for v5.0.1 after the AWS/R-tier fix-test-review loop.

## Explain It Like You Are 9

We tested v5 like a robot helper that must build software.

The tests were not just "does it answer once?" tests. They were obstacle courses:

- Can it remember the goal after the conversation gets long?
- Can it use tools without wasting calls?
- Can it ask helper agents and collect their work?
- Can it keep a notebook of status, logs, costs, and mistakes?
- Can it stop when AWS money or evidence is unsafe?
- Can it fix a real bug, get reviewed, and try again?

Sometimes v5 tripped. That was good: the test found something real. The rule was:

1. Save the failed log.
2. Explain why it failed.
3. Fix code or test harness.
4. Run local lock tests.
5. Ask Claude reviewer to check the fix.
6. Retry only when budget and review gates allow it.
7. Save the passing evidence and push it to git.

So the important result is not "nothing failed." The important result is "failures were caught, fixed, reviewed, retested, and recorded."

## Final Scoreboard

| Item | Final State |
|---|---|
| R-tier matrix rows | 42 total |
| Final row states | 28 `READY`, 14 `DISPOSITION_OK` |
| Final R-tier gate | Passed |
| Final Claude production review | `APPROVE_PRODUCTION_READY` |
| Local Bedrock/R-tier spend | `$1.6757 / $14.25` |
| AWS Budget checked | `Bedrock-Monthly-50`, healthy at last recorded check |
| Final one-by-one gate rerun | 42 of 42 per-test gates passed plus default gate |
| Final one-by-one gate log | `compact_v5/_status/r-tier-final-one-by-one-gates.log` |
| Production-readiness claim | Approved for v5.0.1 scope |

Canonical final evidence:

- `compact_v5/_status/v5_completion_audit/FINAL_POST_AWS_PRODUCTION_READY.md`
- `compact_v5/_status/v5_completion_audit/FINAL_POST_AWS_WORKER_SELF_REVIEW.md`
- `compact_v5/_status/v5_completion_audit/reviews/final-claude-post-aws-production-readiness-review.md`
- `compact_v5/_status/R_TIER_GATE_STATUS.md`
- `compact_v5/_status/r_tier_test_matrix.json`
- `compact_v5/_status/r_tier_metrics.jsonl`
- `compact_v5/_status/PS_PS_FINAL_TEST.md` - final human acceptance test for a
  long-running supervisor/worker/reviewer software engineering task.

## v5 vs Runnable vs v4 vs Other Repos

Kid version: v5 is not just a copy of one older robot. It is v4's SageMaker
notebook body, Runnable's stronger coding-agent brain patterns, Hermes's budget
and failure discipline, and Learning Factory's "write down proof before saying
done" habit.

Scan confidence note:

- Scan 1/2: Wave 2 + Wave 5 + Wave 5-DEEP checked v4, Runnable, Hermes, and
  Learning Factory and produced `SYNTHESIS_MASTER.md`.
- Scan 3: `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` checked the already-built
  v5 against the long-running software-builder goal.
- Every accepted third-scan gap was mapped to a `SOFTWARE-*` block, reviewed by
  Claude, tested locally, then covered by R-tier/local evidence or explicitly
  accepted as future polish.
- Current final status: no known ship-blocking missing feature remains for
  v5.0.1 personal SageMaker software-builder scope. This is not a mathematical
  promise that no future bug exists; it means all known scan/test/review gaps
  are closed, dispositioned, or accepted as nonblocking.

### Side-By-Side Coverage Matrix

| Capability | v5 final | Runnable Claude Code | v4 SageMaker agent | Hermes agent | Learning Factory | Gap status after 3 scans | Explain like 9 |
|---|---|---|---|---|---|---|---|
| SageMaker notebook UI | Kept `chat.ipynb`, `entry.py`, `sagemaker_agent.py`, widgets. | Not notebook-first; CLI/app-oriented. | Main source of the notebook shape. | Not its focus. | Not its focus. | Covered. | v5 keeps your familiar steering wheel. |
| Bedrock-native runtime | Bedrock payload cleaning, model config, cost/cap handling, API boundary tests. | Anthropic-direct patterns, not Bedrock-native. | Bedrock/SageMaker baseline. | Cost-aware ideas, not this exact Bedrock UI. | Process only. | Covered; R13 proved and fixed API leak. | v5 speaks AWS correctly. |
| Long context and compaction | Auto-compact, microcompact, A-16 cold-cache path, typed telemetry, resume checks. | Strong compact/cache reference. | Existing compactor baseline. | Cache/failure discipline ideas. | Status evidence discipline. | Covered; R4/R16/R19-U10 evidence. | v5 repacks the backpack without losing homework. |
| Tool use and tool efficiency | Tool-search, result replay, read tracking, loop breaker, quality followups. | Rich tool contracts and schema loading. | Practical read/edit/shell/notebook tools. | Guardrail/failure-loop ideas. | Review/gate process. | Covered; R14/R19-U3 fixed systemic loop issue. | v5 learns not to bang the same hammer forever. |
| Subagents and reviewers | Structured sync subagent envelopes, parent recovery, review evidence, telemetry. | Strong helper-agent reference, more async/streaming. | Weaker helper story. | Coordination/failure patterns. | Worker-reviewer discipline. | Covered for sync supervision; true async documented future. | Helper robots bring receipts. |
| Durable task state | Durable todos, status, memory, save/resume, checkpoints, journal/recovery. | Has task/session patterns. | Has `AGENT_STATUS.md` and memory basics. | Budget/failure discipline. | Strong file-backed state habits. | Covered by `SOFTWARE-STATE` and AWS/local tests. | v5 writes notes so it remembers tomorrow. |
| Checkpoints and revert safety | Named checkpoint index, preview/restore behavior, restart-safe listing. | Has richer file-state ideas. | Snapshot/revert basics. | Not central. | Process/checkpoint habits. | Covered by `SOFTWARE-CHECKPOINT`. | v5 can save a game checkpoint before risky moves. |
| Large result handling | Persistent result replay and replacement references. | Strong full-output persistence idea. | Thinner output handling. | Failure/retry discipline. | Evidence preservation. | Covered by `SOFTWARE-RESULTS` and R18-E7. | Big logs go in a box with a label. |
| Shell/process safety | Timeout/stop process cleanup, background job lifecycle, logs, no-orphan tests. | Has long-running tool/process patterns. | Basic shell execution. | Strong process kill/recovery pattern. | Stop-on-failure discipline. | Covered by `SOFTWARE-SHELL`. | v5 turns off the machine when the timer ends. |
| Memory and `/dream` | Memory loading, extraction path, `/dream`, fact preservation evidence. | Strong memory extraction reference. | Memory baseline. | Not central. | Durable lessons/status habit. | Covered; output-shape polish future. | v5 remembers important facts and cleans the notebook. |
| Review/no-drift | Scope audit, row ledgers, Claude review, final gates, pushed evidence. | Not your exact audit loop. | Earlier v4 process was weaker. | Failure discipline helps. | Main source of no-drift habit. | Covered; final Claude approved. | v5 must show homework before saying done. |
| Token/cache/cost telemetry | Parent/model/tool/cache spend tracked; subagent telemetry present with polish followup. | Strong cache/token reference. | Less complete. | Budget discipline. | Not runtime telemetry. | Covered for production; richer side display future. | v5 has a money meter. |
| Optimized AWS proof | 42-row R-tier matrix: 28 READY, 14 DISPOSITION_OK, $1.6757 spend. | Reference code only, not your Bedrock proof. | Prior baseline, not enough alone. | Patterns only. | Process only. | Covered; all per-test gates passed. | v5 ran obstacle courses, not just a spelling test. |

| Area | Runnable Claude Code | v4 SageMaker Agent | Hermes Agent | Learning Factory | What v5 Covers | Explain Like You Are 9 |
|---|---|---|---|---|---|---|
| Notebook UI | CLI/app-style coding agent, not SageMaker notebook first. | Strong SageMaker notebook shape. | Not the main pattern. | Not the main pattern. | Keeps v4-style `chat.ipynb`, `sagemaker_agent.py`, and notebook widgets. | v5 keeps the old steering wheel so you can still drive it in SageMaker. |
| Bedrock/SageMaker fit | Not Bedrock-native. | Already works in SageMaker/Bedrock. | Has cost-conscious agent ideas. | Process repo, not Bedrock runtime. | Uses Bedrock-native request handling, model IDs, cost tracking, and API-boundary cleaning. | v5 speaks the language your AWS car understands. |
| Long context and compaction | Strong compaction/cache patterns. | Had compaction, but less complete for long coding work. | Helps with budgets and failure limits. | Saves state/process docs. | Adds auto-compact, cold-cache microcompact A-16, post-compact cleanup, resume/status/memory checks. | When the backpack gets too full, v5 repacks it without losing the homework. |
| Tool use | Rich tool contracts and tool-search/deferred schemas. | Practical file/shell tools. | Guardrails and graceful failure ideas. | Process gates. | Keeps practical tools, adds tool-search, result replay, tool-loop guards, read tracking, and evidence gates. | v5 has tools, but also learns not to bang the same hammer forever. |
| Subagents | Strong helper-agent architecture. | Basic or weaker helper story. | Some orchestration lessons. | Worker/reviewer process discipline. | Adds task/subagent dispatch, structured result envelopes, handoff context, telemetry, and reviewer-style checks. | v5 can ask helper robots, then make them bring back a receipt. |
| Skills | Rich skill discovery and activation. | Had simpler skill behavior. | Skill filtering ideas. | Procedural learning discipline. | Adds skill discovery, activation/reset behavior, filtering, and skill docs. | v5 can open the right instruction card for the job. |
| Memory/status | Runnable has memory patterns. | Had memory/status but not enough no-drift proof. | Not the core contribution. | Strong status/lesson/process style. | Adds durable `memory.md`, `AGENT_STATUS.md`, todos, checkpoints, resume and `/dream`. | v5 writes notes so tomorrow-v5 remembers what today-v5 promised. |
| Review/no drift | Not your exact worker-reviewer audit loop. | v4 did not enforce row-by-row proof strongly enough. | Failure discipline helps. | Main lesson: document, review, and gate work. | Adds row-level ledgers, scope audit, Claude review, final gates, and pushed evidence. | v5 cannot just say "I finished"; it must show its homework. |
| Cost/token/cache telemetry | Strong patterns in Runnable; v4 was thinner. | Some cost support, less complete. | Budget discipline. | Not runtime telemetry. | Tracks tokens, cache, model calls, subagent/tool behavior, local R-tier spend, and AWS budget checks. | v5 has a piggy-bank counter so it does not spend secretly. |
| Software-building proof | Reference implementation is strong. | v4 was useful but less proven on long software tasks. | Helpful constraints, not full SageMaker coding proof. | Process proof. | R13-R17 and R19 tests proved coding, debugging, refactor, long app build, recovery, and coherence. | v5 did real obstacle courses, not just a spelling test. |

## Why v5 Is The Best We Can Build For This Scope

| Reason | What It Means | Explain Like You Are 9 |
|---|---|---|
| It keeps v4's working SageMaker UI. | We did not throw away the part that already fits your company notebook workflow. | We kept the good bicycle frame. |
| It imports the best Runnable ideas that fit Bedrock. | Compaction, cache thinking, tool search, subagents, skills, and tool-loop controls were adapted instead of blindly copied. | We borrowed the best Lego pieces, but made them fit our house. |
| It adds Hermes-style budget/failure discipline. | Iteration limits, cost caps, failure recovery, and graceful stops are built into the process. | It knows when to stop before making a bigger mess. |
| It adds Learning Factory no-drift habits. | Prompts, reviews, ledgers, logs, status, and lessons are saved before closure. | It writes the answer sheet and the work steps. |
| It passed optimized real tests. | AWS tests were bundled to prove multiple abilities at once: coding quality, tool use, memory, compaction, subagents, recovery, cost, and telemetry. | One obstacle course tested running, jumping, balance, and listening together. |
| It failed usefully before passing. | R13, R14, R18-E7, R19-U3, R19-U5, and R17 found real bugs or process gaps that were fixed and retested. | The practice race found loose shoelaces before the real race. |

## What We Skipped Or Did Not Copy, Based On The Three Scans

Kid version: skipping does not mean "forgot." It means "we checked it, and it
did not fit this SageMaker/Bedrock job, or it would waste money, or it belongs
in future polish."

### Side-By-Side Skip / Disposition Matrix

| Item | v5 final decision | Runnable column | v4 column | Hermes column | Learning Factory column | Gap status after 3 scans | Explain like 9 |
|---|---|---|---|---|---|---|---|
| Exact Claude Code UI | Do not copy. Keep SageMaker notebook. | Runnable has CLI/app UI. | v4 notebook is the target. | Not relevant. | Not relevant. | Intentional adaptation. | Keep your desk, not someone else's cockpit. |
| Streaming-first engine | Do not ship in v5.0.1. | Runnable leans streaming. | v4 notebook is simpler. | Some streaming/concurrency ideas. | Not relevant. | Future/non-goal due notebook/Bedrock constraint. | Use walkie-talkie, not live TV. |
| Anthropic-direct request fields | Translate or drop for Bedrock. | Runnable can use Anthropic-direct fields. | v4 already Bedrock-shaped. | Multi-provider ideas only. | Not relevant. | Covered by R13 fix. | Square blocks do not fit round AWS holes. |
| True async/background subagents | Defer true async; strengthen sync supervision. | Runnable has more async helper machinery. | v4 does not require it. | Hermes has stronger concurrent patterns. | Process can support it later. | Explicitly reviewed in `SOFTWARE-ASYNC-DECISION`. | Helpers work one at a time for now, with receipts. |
| Full MCP/multi-source permission stack | Do not copy now. | Runnable has larger MCP/config permission system. | v4 notebook approval simpler. | Not central. | Not central. | Future/non-goal. | One room lock, not a hotel key system. |
| 94-command-style surface | Do not copy all commands. Consolidate/enhance existing commands. | Runnable has many commands. | v4 command shape is user-familiar. | Some command guidance. | Process commands not runtime commands. | Intentional simplification. | Do not add 90 buttons when 20 good buttons work. |
| Hermes business/domain logic | Do not copy. Borrow patterns only. | Not relevant. | Not relevant. | Hermes has domain-specific insurance/agent logic. | Not relevant. | Intentional non-goal. | Borrow the seatbelt, not the delivery route. |
| Learning Factory repo-specific scripts | Do not copy all scripts. Borrow no-drift process. | Not relevant. | Not relevant. | Not relevant. | LF has repo/process-specific automation. | Covered by audit/review/status docs. | Copy the study habit, not the exact timetable. |
| Literal 30-minute R4 idle wait | Use injectable threshold to test same path. | Runnable-style time behavior inspired it. | v4 cold-cache idea existed. | Cost/failure discipline says avoid waste. | Evidence discipline says document adaptation. | Covered; R4 READY. | Test alarm by setting it soon, not waiting all night. |
| 150 live Bedrock turns | Use approved prebuilt 150-logical-turn substitute. | Runnable can inspire long coherence. | v4 not enough. | Budget discipline argues against waste. | Evidence must say what was actually tested. | Covered; R19-U10 READY with caveat. | Use a saved long book, not pay to rewrite it. |
| Full OTel/export pipeline | Keep local JSONL/metrics for v5.0.1. | Runnable has richer telemetry patterns. | v4 thinner. | Observability ideas. | Process evidence. | Documented future; local telemetry sufficient. | Keep a good notebook now; fancy dashboard later. |
| Perfect direct clarification UX | Accept nonblocking polish. | Runnable has richer ask-user style. | v4 simpler. | Not central. | Process says track followup. | Future v5.0.2 polish. | It asks okay now; later ask prettier. |
| Separate live subagent notebook window | Do not add for v5.0.1. Keep the main notebook as supervisor. | Runnable has richer child process UI. | v4 stayed in one notebook. | Helpful attribution ideas. | Evidence trail covers current proof. | v5 shows subagent lifecycle, token/cache/cost, and envelopes in the main UI instead. | One dashboard shows the helper receipts. |
| Bulky optional skill examples in ship zip | Exclude from company runtime zip. | Reference assets useful for dev. | Some came from v4 docs. | Not needed. | Not needed. | Packaging decision; runtime import smoke passed. | Pack the toolbox, not the library shelf. |

| Skipped Or Not Copied | Source Repo | Why We Skipped It | Explain Like You Are 9 |
|---|---|---|---|
| Exact Claude Code/Runnable UI | Runnable | v5 must run as a SageMaker notebook, not a CLI clone. | We kept your classroom desk instead of copying someone else's cockpit. |
| Streaming-first behavior | Runnable / Hermes patterns | v5 is built around notebook/Bedrock constraints where non-streaming paths are safer and simpler. | We used a quiet walkie-talkie instead of a live TV broadcast. |
| Anthropic-direct API features that Bedrock does not support | Runnable | Bedrock has different request rules; R13 proved internal fields must be cleaned. | We cannot put square blocks into round AWS holes. |
| Literal 30-minute cold-cache wait in R4 | Runnable-style behavior | The same A-16 code path was validated with an injectable threshold to avoid wasting time and money. | We tested the alarm clock by setting it to ring soon, not by waiting all night. |
| 150 live Bedrock calls for R19-U10 | Long coherence test design | Approved prebuilt 150-logical-turn substitution proved the memory/coherence goal without waste. | We tested the long story with a saved long book, not by paying to rewrite the whole book live. |
| Full Runnable internal feature flags/GrowthBook/Kairos branches | Runnable | Those are Anthropic-internal product switches, not useful in this personal SageMaker agent. | We did not install switches for rooms this house does not have. |
| Full MCP/config multi-source permission stack | Runnable | v5 has a simpler notebook approval model and Bedrock/SageMaker runtime. | One door lock is enough for this room; we did not copy a whole hotel key system. |
| Exact async streaming subagent architecture | Runnable | v5 adapted subagents to sync notebook-compatible execution with structured envelopes. | Helpers still help, but they pass notes instead of shouting across a stadium. |
| Hermes insurance/domain-specific logic | Hermes | Hermes taught budget/failure patterns, but its business domain is not your coding-agent domain. | We borrowed the seatbelt, not the delivery truck route. |
| Learning Factory repo-specific automation | Learning Factory | We adopted the no-drift process, but not every repo-specific script/hook. | We copied the study habit, not the exact school timetable. |
| Full optional skill reference packs in company zip | v4/v5 docs assets | They are useful examples for development, but not needed for the main production runtime. | We packed the toolbox, not the big instruction-library shelf. |
| Perfect clarification UX | Final review follow-up | Current behavior is safe enough; direct `ask_user` polish is tracked for v5.0.2. | It asks okay now; later we can make it ask more neatly. |
| Separate live subagent window | Final UI review | v5 uses synchronous notebook subagents; adding separate child windows would add complexity and risk. The main UI now shows child lifecycle plus per-helper token/cache/cost attribution. | Helpers work inside the main room, but their receipts are visible. |
| Perfect `/dream` output shape | Final review follow-up | `/dream` passed memory-preservation tests; output formatting polish is future work. | The notebook remembers the facts; later we can make the handwriting nicer. |
| Mermaid-based final HTML diagrams | Docs packaging | Mermaid caused syntax/display problems, so the final HTML uses plain HTML flow boxes. | We used simple boxes instead of a fancy drawing tool that sometimes breaks. |

## What Failed, Why, And How It Was Fixed

| Test or Area | What Went Wrong | Fix Applied | Final Evidence |
|---|---|---|---|
| R1 coding accuracy | First diagnostic call found unsafe Unicode stdout behavior and uncovered config/geographic pricing accounting issues. | Unicode-safe output and pricing/config accounting were fixed, then R1 was rerun and gated. | `READY`, Phase C `GENUINE_PASS`, per-test gate passed. |
| R2 compaction recall | Needed real proof that important facts survive compaction. | Real compaction/recall evidence was preserved and gated. | `READY`, Phase C `GENUINE_PASS`, per-test gate passed. |
| R3 subagents | Early expectations around subagent markers were too brittle. | Assertions and evidence were corrected to match the implemented structured subagent behavior. | `READY`, reviewed evidence kept. |
| R4 cold-cache microcompact | Earlier process deferred A-16, but the user required it before production. | A-16 was implemented in runtime code and validated with an injectable threshold on real Bedrock, avoiding a wasteful 30-minute wait while hitting the same code path. | `READY`, Phase C `GENUINE_PASS`, per-test gate passed. |
| R5 exec-limit recovery | Needed proof that blocking exec does not break other recovery actions. | Evidence was refreshed and gated with the lowered-cap same-code-path fixture. | `READY`, Phase C `GENUINE_PASS`, per-test gate passed. |
| R6 and R19-U9 dream memory | Needed proof that `/dream` keeps good facts, drops stale duplicates, and releases its lock. | Ran a shared optimized real Haiku test covering both rows. | Both `READY`; low output-shape polish accepted nonblocking. |
| R7 model switch | Needed live proof that context survives model switch. | Ran same-session Haiku to Sonnet switch and verified recalled marker. | `READY`, Phase C `GENUINE_PASS`, per-test gate passed. |
| R8, R18-E2, R18-E5, R18-E9, R18-E12 | These were better as zero-cost deterministic mock tests than AWS calls. | Added local mock evidence and taught the gate to accept `local-call` evidence for mock rows only. | All `READY`, zero spend, per-test gates passed. |
| R9, R10, R12, R18-E1, R18-E3, R18-E4, R18-E6, R18-E8, R18-E10, R18-E11, R18-E13, R18-E14, R18-E15, R19-U8 | Some rows were covered by existing stronger evidence or needed local locks instead of new AWS spend. | Claude-approved disposition plan plus local locks where needed. Gate now supports reviewed `DISPOSITION_OK` rows. | All `DISPOSITION_OK`, per-test gates passed. |
| R11 Sonnet end-to-end | Needed a stronger model end-to-end artifact test. | Ran Sonnet dashboard/report workflow and verified generated artifacts. | `READY`, Phase C `GENUINE_PASS`, per-test gate passed. |
| R13 Bedrock API boundary | Real AWS rejected leaked internal metadata such as `is_meta`. | Sanitized metadata before Bedrock payloads and added halt-after-success protection. | `READY`, Phase C `GENUINE_PASS`, per-test gate passed. |
| R14 multi-file refactor | Artifact passed, but tool behavior was inefficient and looked like a repeated failed loop. This was critical. | Fixed read tracking and added guard-class breaker behavior. Later R19-U3, R16, R19-U10, R4, R7, and R11 did not reproduce the loop. | `READY`, Phase C `GENUINE_PASS`; recurrence watch remains nonblocking. |
| R15 debugging | Harness was too broad and counted unrelated runtime/cache files. | Tightened the debugging harness so it measured the intended planted-bug work. | `READY`, Phase C `GENUINE_PASS`, per-test gate passed. |
| R16 long app build | Needed real software-builder proof with tool quality and telemetry. | Fixed telemetry aggregation so multiple audit JSONL files in one directory are aggregated correctly. | `READY`, Haiku pass, no R14-style tool-loop recurrence. |
| R17 thinking visibility | First runner violated Bedrock invariant: `max_tokens` must exceed thinking budget. | Corrected the runner and captured thinking text in history plus audit/telemetry. | `READY`, Phase C `GENUINE_PASS`, per-test gate passed. |
| R18-E7 large result replay | First call exceeded the tiny row cap and exposed replay readiness issues. | Preserved diagnostic spend, fixed deterministic replay offset/readiness behavior, then reran under cap. | `READY`, Phase C `GENUINE_PASS`, per-test gate passed. |
| R19-U1 and R19-U2 ambiguity/contradiction | Workspace-root mismatch and UX expectations needed tightening. | Fixed root handling and accepted direct-clarification UX polish as nonblocking. | Both `READY`, per-test gates passed. |
| R19-U3, R19-U6, R19-U7 recovery bundle | R19-U3 reproduced the R14 repeated-tool-loop class. | Fixed the process blocker, reran the bundle, and verified repeated-call circuit breaker fired correctly. | All `READY`, Phase C `GENUINE_PASS`, per-test gates passed. |
| R19-U4 and R19-U5 subagent conflict/failure | One predicate was too narrow: artifact recorded missing child clearly, but test expected exact wording. | Fixed the predicate and added local lock tests before AWS retry. | Both `READY`, Phase C `GENUINE_PASS`, per-test gates passed. |
| R19-U10 long coherence | A full 150 live-turn AWS run would be wasteful. | Used the approved prebuilt 150-logical-turn transcript/churn substitution to prove anchor preservation and compaction/model-switch evidence. | `READY`; not claimed as 150 live Bedrock calls. |

## Why The Worker Failed But Still Got Safer

The worker failed in four useful ways:

- real product bugs, like the Bedrock `is_meta` payload leak;
- process bugs, like R14-style repeated failed tool loops;
- test harness bugs, like overly strict predicates or wrong Bedrock thinking budget;
- documentation and evidence drift, like rows that looked done but had not been individually gated.

Each class now has a stronger guard:

- API payload cleaning keeps internal fields out of Bedrock requests.
- Tool-loop quality checks and recurrence watch stop inefficient coding loops.
- Per-test gates make sure every R-tier row has its own evidence or reviewed disposition.
- Claude review plus saved logs make the work traceable instead of trusting terminal text.

## What Is Accepted But Not Perfect

These are not production blockers for v5.0.1, but should stay visible for v5.0.2 polish:

- direct clarification UX can be smoother than the current evidence path;
- subagent side metrics can show even richer token/cost/cache breakdowns;
- `/dream` output shape can be more polished;
- telemetry per-turn aggregation can become easier to read;
- R14/R19-U3 repeated-tool-loop recurrence watch should remain active in future software-builder tests;
- R4 used an injectable threshold for the A-16 time-based path instead of waiting 30 real minutes;
- R19-U10 used an approved prebuilt 150-logical-turn substitution, not 150 live Bedrock calls.

## Final Confidence Statement

If we explain it simply: v5 took the big test, fell down in some places, learned why, fixed those places, passed the gates, and got an independent final review.

That is the right kind of production evidence for this v5.0.1 personal SageMaker software-builder scope. It is not a promise that no future bug exists, but it is strong evidence that v5 is ready to use and that future problems will be traceable instead of mysterious.

## v4 Actual-Use Problem Scan Cross-Check

Date: 2026-05-06

This section records the extra v4 scan requested after production readiness:
two passes over v4 problem docs/source evidence, then v5 source/test evidence.

### Round 1: v4 Known Problems

Source checked: `compact_v4/docs/PS_actual_use_problems.md` and
`compact_v4/CHANGELOG.md`.

| v4 problem | v4 lesson | v5 evidence | Result |
|---|---|---|---|
| Startup warning noise | Advisory skill checks should not flood normal startup. | Block 0/skill smoke tests and final package smoke pass; normal UI import is quiet under mock mode. | Solved for v5 runtime. |
| Iteration budget too small | Long coding needs much more than 90 shared LLM turns. | `core/budget.py` default is 600; notebook Cell 2 exposes `iteration_budget_slider` 90-2000; `test_notebook_smoke.py` locks config threading. | Solved and UI-exposed. |
| Cold-cache behavior confusing but useful | Idle sessions need time-based microcompact, not surprise cost. | A-16 implemented; R4 real Bedrock gate validates cold-cache microcompact via injectable threshold. | Solved for v5.0.1 scope. |
| Thinking visible only sometimes | Thinking is model-controlled, but UI/config should be explicit. | Notebook Cell 2 exposes thinking checkbox and budget dropdown; R17 validates thinking visibility path. | Solved enough for production; behavior still model-dependent. |
| Session cost not persisted | Cost must live in token/cost tracker and survive save/resume. | `/save`, `/resume`, `/cost`, `runtime/tokens.py`, `runtime/session.py`, and `test_software_state.py` cover durable cost/status/memory paths. | Solved. |
| Exec limit made agent say "I cannot work" | Failure messages must tell the model what still works. | v5 keeps 200 exec-call default, `/context`/`/cost`, result replay, loop breakers, and R14/R19-U3 recurrence tests. | Solved and strengthened. |
| Tool matrix buried under prompt load | Capability guidance and no-drift gates must be explicit. | v5 adds command docs, software workflow contracts, `/verify`, `/done`, scope/audit gates, and final Claude review. | Solved through runtime + process gates. |

### Round 2: Source/Test Evidence

Source checked: `compact_v5/MAIN/agent`, notebook cells, package verifier,
R-tier matrix, and final production review.

| Evidence item | Command or file | Result |
|---|---|---|
| Notebook has v4-style model dropdown | `tests/integration/test_notebook_smoke.py` | `22 passed`; includes lock for `model_dropdown`, Sydney region, and Sonnet 4.5 default. |
| Default model and region match v4 intent | `entry.py`, `runtime/config.py`, `chat.ipynb` | First `BEDROCK_MODELS` entry is `Claude 4.5 Sonnet (AU) - default`; region is `ap-southeast-2`. |
| Minimum company zip excludes docs/tests/audit evidence | `verify_ship_zip.py` | Ship verifier passes; zip has no `docs/`, `_status/`, `tests/`, or design HTML. |
| R-tier matrix complete | `r_tier_test_matrix.json` | 42 rows total: 28 `READY`, 14 `DISPOSITION_OK`. |
| Final R-tier gate | `r_tier_gate.py --repo-root .` | Passed. |
| Final independent review | `final-claude-post-aws-production-readiness-review.md` | `APPROVE_PRODUCTION_READY`; nonblocking follow-ups accepted. |

Conclusion: v5 is better than v4 for the target use case because it keeps the
v4 SageMaker UI and Bedrock fit, restores v4 model-selection ergonomics, and
adds the software-builder features v4 did not prove: row-level review evidence,
subagent envelopes, result replay, checkpoint/resume, tool-loop quality gates,
and optimized real AWS coding tests.

## UI Parity Final Pass

Date: 2026-05-06

The post-production v4 comparison found that the v5 engine was strong, but the
notebook UI still had stale docs and a few controls that looked v4-like before
they were fully wired. The UI final pass keeps the v4 user experience without
rolling back v5 architecture.

| UI item | What changed | Why it matters |
|---|---|---|
| Dark v4-style chat | `V4WidgetChatUI` is the default ipywidgets surface. | The user sees the familiar v4 notebook shape, not a stripped-down demo. |
| Plan Mode | Checkbox now updates `Agent.plan_mode`, which reaches `QueryEngine.run(plan_mode=...)`. | Mutating tools are blocked when the operator is only planning. |
| Auto-Compact | Checkbox now updates `Agent.auto_compact_enabled`, which gates cold-cache microcompact and auto-compact. | The visible checkbox actually controls the expensive automatic compaction path. |
| Compact | Button now uses the v5 `Compactor` path directly instead of a nonexistent `/compact` command. | Manual compaction works from the notebook. |
| Clean | Button removes local non-session traces and keeps sessions, matching the v4 safety intent. | Users can clean scratch/audit traces without losing conversation continuity. |
| Sub-agent panel | Dropdowns now feed notebook sub-agent preferences into the dynamic prompt tail. | The model receives the operator's intended explorer/worker/reviewer preference without forcing unnecessary subagents. |
| Sub-agent visibility | The `task` tool now streams `[subagent:<type>] started/finished` messages into the notebook output path. | The main session remains the supervisor window, but users can see when helpers start, finish, stop, and how much they cost. |
| Cache and savings metrics | The bottom metrics panel now shows `Cache R/W`, `Without cache`, `Saved`, and parent/subagent token/cache/cost attribution inline. | The user can see whether prompt caching is working and how much money it saved without running `/cost`. |
| Todo/status visibility | The UI now renders a compact todo panel even before todos exist, nudging long tasks toward `todo_write` and `AGENT_STATUS.md`. | Long-running work has visible state instead of disappearing behind chat text. |
| Approval and ask-user boxes | Hidden duplicate placeholders were removed. | v5 already has real `PermissionDialog` and `ask_user` tool surfaces; duplicate dead UI would be misleading. |
| Docs | Stale "minimal MVP" UI claims were replaced with final v5.0.1 UI behavior. | Future workers will not accidentally downgrade v5 back to the old MVP description. |
