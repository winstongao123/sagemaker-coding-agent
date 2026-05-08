# Third Deep Scan - Software Builder Architecture Gaps

Date: 2026-05-05

Status: RED_TEAM_REVIEW_APPLIED_WORKER_BLOCKS_REQUIRED

User-facing requirement summary:
`compact_v5/_status/v5_completion_audit/PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md`

## Goal

Build v5 into a production-ready, single-person SageMaker software coding
agent that can run long software engineering tasks with:

- durable task/status/memory continuity across compaction, save/resume, and
  interrupted sessions;
- optimized tool use, token use, cache behavior, and model-call cost;
- clear token/cost/cache telemetry for parent agents, subagents, and reviewer
  subagents;
- reliable subagent coordination and reviewer handoff;
- evidence-preserving review, test, checkpoint, and resume workflows;
- enough optimized local and AWS validation to support at least 98 percent
  production confidence before real use.

Passing local tests alone is not sufficient. Production confidence requires the
full implementation scope, independent review, clean mechanical audits, and real
AWS software-building evidence.

## Source Repos And References

These sources are read-only references for the third deep scan:

- Current v5 target: `D:\Github\sagemaker-coding-agent\compact_v5`
- Primary Runnable reference:
  `D:\Github\gg_claude_code\gg-claude-code-runnable`
- Archived Runnable reference used for earlier comparison only:
  `D:\Github\sagemaker-coding-agent\_archive\compare_code\gg-claude-code-runnable`
- Additional Claude Code references:
  `D:\Github\gg_claude_code`,
  `D:\Github\how-claude-code-works`,
  `D:\Github\claude-code-best-practices`,
  `D:\Github\PS_everything_claude_code`
- Learning Factory: `D:\Github\Learning_Factory`
- Hermes agent: `D:\Github\hermes-agent`
- v4 reference:
  `D:\Github\sagemaker-coding-agent\compact_v4`,
  `D:\Github\sagemaker-coding-agent\compact_v5\_phase_2\v4_reference`
- Existing mapping and audit files are reference material only. They must not
  be treated as proof that a behavior exists in current v5 code.

## Relationship To Earlier Deep Scans

This is the third deep scan. It does not replace the earlier mapping and
synthesis work:

- Prior Runnable/v4 deep analysis examples:
  `PS_ClaudeCode_Insights/PS_Deep/gap_analysis_v4_vs_runnable.md`,
  `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md`,
  `compact_v5/_phase_2/wave_5_deep/00-SYNTHESIS.md`.
- Prior wave synthesis:
  `compact_v5/_phase_2/wave_5/WAVE_5_SYNTHESIS.md`,
  `compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md`.
- Current completion redo evidence:
  `compact_v5/_status/v5_completion_audit/blocks/`,
  `compact_v5/_status/v5_completion_audit/ledger/CLAUDE_REVIEW_MATRIX.md`.

The purpose of this third scan is narrower and stricter: after mapped blocks
are implemented, check whether v5 still lacks any architecture required for a
production long-running software builder.

## Scan Assignments

| Agent | Scope | Status |
|---|---|---|
| Runnable scan 1 | Runnable source vs current v5 for core long-running SWE agent capabilities | COMPLETE |
| Runnable scan 2 | Runnable plus Claude Code reference repos vs current v5 | COMPLETE |
| Learning Factory scan | Learning Factory governance, memory, status, lessons, checkpoint patterns vs v5 | COMPLETE |
| Hermes scan | Hermes coordination/tool/retry/error/telemetry patterns vs v5 | COMPLETE |
| v4 scan | v4 production workflows, skills, tests, status/memory/resume vs v5 | COMPLETE |

## Initial Known Gaps To Validate

These are not yet final decisions. They are known findings from prior checks
that the third scan must confirm, refine, or reject with file evidence.

| ID | Severity | Gap | Current Concern | Initial Decision |
|---|---|---|---|---|
| DS3-1 | HIGH | Task ledger persistence | `todo_write` state may be process-global and not fully persisted by `/save` or restored by `/resume`. Long-running work can lose task truth after restart. | Likely implement now if confirmed. |
| DS3-2 | HIGH | Runtime verify/review gate enforcement | `/verify`, `/done`, review/simplify/reflexion guidance may be advisory rather than an enforced close gate. | Likely implement now if confirmed. |
| DS3-3 | MEDIUM | Memory extraction integration | Memory extraction and `/dream` exist, but automatic extraction may depend on injected callbacks and may not run at session end or pre-compaction. | Consider implement or strengthen tests. |
| DS3-4 | MEDIUM | Compaction/recovery telemetry | Auto-compact and microcompact may not emit dedicated audit/telemetry events, weakening AWS evidence for recovery. | Likely implement telemetry/test hardening. |
| DS3-5 | MEDIUM | Subagent long-running coordination | Current subagents may be functionally sequential rather than true concurrent long-running worker/reviewer teams. | Decide whether current Bedrock-only design needs true concurrency now. |
| DS3-6 | MEDIUM | Rich structured ask-user UX | Runnable supports multi-question, multi-option, previewable user questions; v5 ask-user appears simpler. | Implement only if useful for SWE workflow decisions. |
| DS3-7 | LOW-MEDIUM | Sleep/wait/tick tool | Runnable has model-callable sleep/tick behavior for waiting without noisy loops; v5 may lack an equivalent. | Implement if needed for unattended long tasks. |
| DS3-8 | LOW | Model-callable config tool | Runnable exposes safe settings/config changes as a tool; v5 has config but may lack a model-callable adjustment surface. | Future unless needed for AWS tests. |

## Consolidated Scan Findings

The scans found repeated evidence for a small set of architectural themes. The
important result is not that v5 lacks every Claude Code/Runnable/Hermes feature;
the result is that a few durability and orchestration behaviors are still
important for the stated production goal.

| ID | Decision | Severity | Consolidated Gap | Evidence Summary | Required Action |
|---|---|---|---|---|---|
| DS3-S1 | `NEW_BLOCK_IMPLEMENT_NOW` | CRITICAL | Durable task/work ledger | Runnable has disk-backed locked tasks; Learning Factory relies on file-backed state; v5 `todo_write` is process-global and `Session.todos` is not fully saved/resumed. | Add durable todo/work-queue persistence and resume tests. |
| DS3-S2 | `NEW_BLOCK_IMPLEMENT_NOW` | CRITICAL | Full save/resume/checkpoint state | Runnable/v4 preserve conversation, task/checkpoint/file-history state; v5 `/save` primarily preserves messages/token stats and `/checkpoint` snapshots files only. | Extend save/resume/checkpoint to cover todos, status, named checkpoints, and recovery metadata. |
| DS3-S3 | `NEW_BLOCK_IMPLEMENT_NOW` | HIGH | Fresh status and memory context loading | Learning Factory requires fresh state before stop/commit; v4 loads `AGENT_STATUS.md` and `memory.md` into prompt repeatedly; v5 status appears one-time loaded and `memory.md` auto-load is not clearly wired. | Ensure top-level turns refresh durable status/memory context and tests prove it. |
| DS3-S4 | `NEW_BLOCK_IMPLEMENT_NOW` | HIGH | Enforced verify/done close gate | v5 has review/verify/reflexion skills, but `/verify` and `/done` are mostly prompt/advisory flows. | Add a local non-AWS close gate requiring fresh status, test evidence, review evidence, and explicit pass/fail before done claims. |
| DS3-S5 | `NEW_BLOCK_IMPLEMENT_NOW` | HIGH | Subagent supervision and structured result telemetry | Hermes/Runnable expose timeout, heartbeat, structured child traces, files touched, tokens, cost, duration; v5 `task` returns text/stop reason and synchronous child execution. | Add structured subagent result envelope, timeout/heartbeat metadata, files/tokens/cost/cache attribution, and parent recovery tests. |
| DS3-S6 | `NEW_BLOCK_DECISION_REQUIRED` | HIGH | True async/background subagents | Runnable/Hermes support pollable/background child work; v5 `task` is sync and `is_concurrency_safe=False`. This is large and may conflict with SageMaker notebook constraints. | Decide whether v5.0.1 must implement true background workers now or document as post-v5.0.1 while strengthening sync supervision. |
| DS3-S7 | `NEW_BLOCK_IMPLEMENT_NOW` | HIGH | Large tool-result persistence/replay | Runnable persists full outputs and replacement records; v5 truncates inline outputs and A-42 content-replacement coverage may not preserve full inspectability. | Add stable large-output artifact storage/replay, content-replacement metadata, and tests. |
| DS3-S8 | `NEW_BLOCK_IMPLEMENT_NOW` | HIGH | Safe revert/checkpoint UX | v4 single-file revert previews before mutation; v5 direct file revert is narrower. | Add preview/confirm behavior and lock tests for single-file revert/checkpoint restore. |
| DS3-S9 | `TEST_HARDENING_ONLY` | MEDIUM | Manual compact/clean controls | v4 exposed manual compact/clean controls; v5 has compaction internals but no clear `/compact` command/control. | Add command or explicit no-goal decision; at minimum add tests/docs for manual compaction trigger. |
| DS3-S10 | `NEW_BLOCK_IMPLEMENT_NOW` | HIGH | Compaction/recovery telemetry | Compaction works, but microcompact/auto-compact primarily emit UI text; telemetry builder detects compaction by audit-action strings, so real compaction can be invisible to evidence. | Add dedicated audit/telemetry events and R19-U10/R4 evidence checks. |
| DS3-S11 | `NEW_BLOCK_IMPLEMENT_NOW` | HIGH | Memory loading/extraction wiring | v5 memory APIs and `/dream` exist, but `memory.md` prompt loading and automatic extraction/session-end behavior are not sufficiently wired for the long-running goal. | Wire memory context loading and explicit local tests; then prioritize R6/R19-U8/R19-U9 AWS proof. |
| DS3-S12 | `DOCUMENT_FUTURE` | MEDIUM | Streaming tool state machine | Explicitly dropped by no-streaming constraint; non-streaming parallel dispatch is covered. | Keep as future unless product scope changes. |
| DS3-S13 | `DOCUMENT_FUTURE` | MEDIUM | Production OTel/export pipeline | v5 has local JSONL/metrics and test telemetry; real OTel export is beyond current personal SageMaker scope. | Document future; do not block v5.0.1. |
| DS3-S14 | `TEST_HARDENING_ONLY` | MEDIUM | Rich structured ask-user UX | Runnable has richer multi-question/preview UX; v5 ask-user is simpler. | Add only if AWS/user-alignment tests show need; otherwise document current scope. |
| DS3-S15 | `DOCUMENT_FUTURE` | LOW | Model-callable config/custom command surfaces | Useful for UX, not core to current production goal. | Future unless user explicitly needs it. |
| DS3-S16 | `NEW_BLOCK_IMPLEMENT_NOW` | CRITICAL | Foreground subprocess timeout/stop safety | v5 foreground shell/python tools can report timeout while child processes may continue; stop is a flag checked between turns. Hermes kills process groups on timeout/interrupt. | Add kill/terminate process-tree behavior, active-process cleanup, and tests for timeout/stop no-orphan behavior. |
| DS3-S17 | `NEW_BLOCK_IMPLEMENT_NOW` | HIGH | Managed background shell/job lifecycle | Runnable/Hermes support background shell tasks with output files, status/poll/wait/kill/recovery. v5 bash is foreground-only with timeout. | Add managed background shell lifecycle for dev servers, long tests, watchers, and migrations, or explicitly narrow product scope. |
| DS3-S18 | `NEW_BLOCK_IMPLEMENT_NOW` | HIGH | Broader tool-failure loop breaker | Current repeated-call guard is same `(tool,args)` within one run; Learning Factory blocks repeated same failure and total failed-call patterns. | Add failure-signature tracking across tool errors and turns, with status evidence and tests. |

## Decision Rules

Each confirmed gap must be classified into one of:

- `NEW_BLOCK_IMPLEMENT_NOW`: required before AWS production-readiness tests.
- `TEST_HARDENING_ONLY`: behavior exists, but tests/telemetry/review evidence are
  insufficient.
- `AWS_VALIDATION_ONLY`: local evidence is enough for now, but real Bedrock proof
  is required before production confidence.
- `DOCUMENT_FUTURE`: useful but not required for the current v5 production goal.
- `REJECTED_ALREADY_COVERED`: scan finding is stale or already covered in code,
  tests, docs, and review artifacts.

## Proposed Software-Builder Blocks

`SWE` means software-engineering / software-builder. To avoid ambiguity, the
worker-facing block names below use the explicit `SOFTWARE-*` prefix.

Final block names should be added to the worker queue after the current
canonical completion blocks close. Suggested new/revisit scopes:

- `SOFTWARE-ASYNC-DECISION`: explicit design decision for true background/async
  subagents in v5.0.1 vs post-v5.0.1. Current recommendation: defer true
  async subagents and validate strengthened synchronous supervision.
- `SOFTWARE-STATE`: durable todos, `/save`, `/resume`, `AGENT_STATUS.md`,
  `memory.md`, crash-safe per-turn journaling, and auto-restore continuity.
  This block must explicitly wire bounded per-turn `AGENT_STATUS.md` and
  `memory.md` prompt/context injection and either enable memory extraction by
  default for the accepted product path or expose an opt-in path that R16 and
  R19-U10 exercise.
- `SOFTWARE-CHECKPOINT`: durable named checkpoint index, safe single-file
  restore/revert preview, and restart-safe checkpoint listing.
- `SOFTWARE-SHELL`: foreground subprocess kill-on-timeout/stop, managed
  background shell jobs, output capture, poll/wait/kill, and no-orphan
  guarantees. This block must specify cross-platform process-tree semantics:
  Windows Job Object or `CREATE_NEW_PROCESS_GROUP` strategy, and POSIX
  `os.killpg` or equivalent.
- `SOFTWARE-RESULTS`: large tool-result persistence/replay and
  content-replacement metadata.
- `SOFTWARE-SUBAGENT`: structured synchronous subagent/reviewer result
  envelopes, timeout/heartbeat metadata, files changed, token/cost/cache
  telemetry, and parent recovery.
- `SOFTWARE-COMPACT-TELEMETRY`: manual compact/clean control if accepted,
  dedicated compaction/recovery telemetry, cache-hit evidence checks, and
  broader repeated-failure loop telemetry. This block must emit typed audit
  actions such as `compact_auto_start`, `compact_auto_end`,
  `compact_micro_start`, `compact_micro_end`, and `compact_failed`, so
  telemetry no longer relies on substring matching.
- `SOFTWARE-GATE`: enforced `/verify` and `/done` close discipline, status
  freshness, review/test evidence, and deterministic pass/fail. This must be
  last because it consumes the evidence surfaces created by the earlier blocks.

No worker should run AWS/R-tier spend until these accepted local
software-builder hardening blocks are implemented, tested, documented, and
independently reviewed, or explicitly classified as future/non-goal.

## Gap To Block Traceability

| Gap ID | Worker block | Notes |
|---|---|---|
| DS3-S1 | `SOFTWARE-STATE` | Durable task/work ledger and todo persistence. |
| DS3-S2 | `SOFTWARE-STATE`, `SOFTWARE-CHECKPOINT` | Session/todo/status/memory persistence in STATE; durable checkpoint index and restore in CHECKPOINT. |
| DS3-S3 | `SOFTWARE-STATE` | Fresh per-turn `AGENT_STATUS.md` and `memory.md` context loading. |
| DS3-S4 | `SOFTWARE-GATE` | Enforced `/verify` and `/done`; must run after state/results/subagent/telemetry blocks. |
| DS3-S5 | `SOFTWARE-SUBAGENT` | Structured synchronous child/reviewer result envelope. |
| DS3-S6 | `SOFTWARE-ASYNC-DECISION` | Current recommendation: defer true async subagents for v5.0.1 and validate sync supervision honestly. |
| DS3-S7 | `SOFTWARE-RESULTS` | Large tool-result persistence/replay and content-replacement references. |
| DS3-S8 | `SOFTWARE-CHECKPOINT` | Safe preview/confirm restore/revert and restart-safe checkpoint listing. |
| DS3-S9 | `SOFTWARE-COMPACT-TELEMETRY` | Manual compact/clean control or explicit no-goal decision. |
| DS3-S10 | `SOFTWARE-COMPACT-TELEMETRY` | Typed compaction/recovery audit events and cache evidence. |
| DS3-S11 | `SOFTWARE-STATE` | Memory loading/extraction wiring before AWS proof. |
| DS3-S12 | Future | Streaming state machine remains dropped by no-streaming constraint. |
| DS3-S13 | Future | Full OTel/export pipeline is out of v5.0.1 personal SageMaker scope. |
| DS3-S14 | Test/future | Rich ask-user UX only if AWS/user-alignment tests show need. |
| DS3-S15 | Future | Model-callable config/custom command surfaces are not pre-AWS blockers. |
| DS3-S16 | `SOFTWARE-SHELL` | Foreground subprocess kill-on-timeout/stop and no-orphan proof. |
| DS3-S17 | `SOFTWARE-SHELL` | Managed background shell/job lifecycle. |
| DS3-S18 | `SOFTWARE-COMPACT-TELEMETRY`, `SOFTWARE-GATE` | Failure-signature telemetry plus close-gate consumption. |

## Test Case Review Requirement

Every accepted third-scan gap must map to test evidence. The test decision must
be recorded before implementation work is considered complete:

| Decision | Required test update |
|---|---|
| `NEW_BLOCK_IMPLEMENT_NOW` | Add or extend local lock tests and add/adjust the optimized AWS scenario that proves the behavior in real Bedrock use. |
| `TEST_HARDENING_ONLY` | Add targeted local tests and update the evidence contract; no new AWS call unless real-model behavior matters. |
| `AWS_VALIDATION_ONLY` | Update `OPTIMIZED_AWS_VALIDATION_PLAN.md`, `TEST_CASE_PREP.md`, and R-tier evidence contracts so the behavior is measured in an existing high-signal AWS scenario. |
| `DOCUMENT_FUTURE` | Explain why it is not required for the current production goal and where it would belong later. |
| `REJECTED_ALREADY_COVERED` | Cite the existing code, test, review, and telemetry evidence. |

The preferred AWS strategy remains high-signal bundling, not many small
overlapping calls. One AWS test should reveal several properties whenever
possible: coding quality, tool use, token/cache behavior, compaction, memory and
status durability, reviewer/subagent coordination, and final artifact quality.

Relevant test planning files:

- `compact_v5/_status/v5_completion_audit/TEST_CASE_PREP.md`
- `compact_v5/_status/v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md`
- `compact_v5/_status/R_TIER_EVIDENCE_CONTRACT.md`
- `compact_v5/MAIN/agent/tests/r_tier/test_software_project_workflow_contracts.py`

## Test Updates Needed

Local zero-cost tests should be added before any AWS run:

- save/resume restores todos, status pointers, checkpoints, token stats, and
  memory context;
- per-turn crash-safe journal/auto-restore can recover messages, todos, token
  stats, status pointers, memory context, and checkpoint indexes after process
  restart;
- top-level turns refresh `AGENT_STATUS.md` and `memory.md`;
- `/done` refuses or clearly blocks close when required status/test/review
  evidence is stale or missing;
- single-file revert previews before mutation;
- foreground shell/python timeout and UI stop terminate or kill the active
  process tree and leave no orphan process mutating the workspace;
- background shell jobs can be started, polled, waited on, killed, and replay
  bounded output from durable logs;
- repeated same-failure and total-failure loops are blocked or escalated before
  unattended runs waste calls;
- large tool outputs are persisted and replayable by stable reference;
- subagent/reviewer result envelope includes role, stop reason, files changed,
  tokens, cost, cache read/write, duration, timeout/heartbeat metadata, and
  usefulness/result summary;
- compaction emits dedicated telemetry that `build_telemetry.py` can verify.
- `todo_write` state survives `/save` + `/resume` in a fresh process/session.
- `/done` refuses with an explicit reason when status is stale, required tests
  are missing, required review evidence is missing, or last verification failed.
- shell timeout kills a real sleeping child process tree; the test should use a
  sentinel file that would be written only if the child survived past timeout.
- an actual auto-compact or microcompact run emits typed audit actions that
  `build_telemetry.py` reads without substring guessing.

## Red-Team Corrections

A final read-only red-team review corrected four classifications:

1. Crash-safe per-turn journaling and auto-restore must be explicit in
   `SWE-STATE`; manual `/save` is not enough for the stated long-running
   software-builder goal.
2. Checkpoint indexes must be durable across process restart. Existing disk
   snapshots are insufficient if listing/revert depends on an in-memory index.
3. Compaction telemetry is implementation work, not only test hardening,
   because current telemetry may not see actual auto/microcompact events.
4. Memory loading/extraction is implementation work, not AWS-only validation,
   because `memory.md` prompt loading and automatic/session-end extraction need
   local wiring before real-AWS proof.

Optimized AWS matrix updates:

- R16 long app build must prove `/status`, `/save`, `/resume`, `/checkpoint`,
  `/verify`, `/done`, `/cost`, `/context`, durable todos, and status/memory
  continuity.
  It must report sub-checks separately: status round-trip, todo round-trip,
  named-checkpoint round-trip, verify/done stale-evidence block, compaction
  event emitted, shell background start/poll/kill if shell lifecycle ships, and
  final artifact quality.
- R19-U10 must prove post-compaction/resume coherence using file-backed status
  and memory, not only model memory.
- R3/R18-E11/R19-U4/R19-U5 must prove subagent/reviewer telemetry and parent
  recovery behavior. If true async is deferred, the test must say so honestly
  and validate the accepted synchronous-supervision contract.
- R18-E7 must prove large-output persistence/replay and stable replacement
  references.
- R19-U6/R19-U7 must prove background/foreground shell recovery and repeated
  failure loop handling without orphaned processes.
- R4/R2 cache evidence should include non-null cache-hit/read/write signals
  where Bedrock exposes them. If Bedrock/model output does not expose a field,
  the run must record an explicit model-side limitation row instead of silently
  leaving evidence blank.

## Final Output Required

Before AWS/R-tier spend resumes, this document must include:

1. Full scan-agent findings with exact file evidence.
2. A decision table for every confirmed gap.
3. A new-block/revisit-block plan for worker implementation.
4. Test updates needed to verify each accepted gap.
5. Claude reviewer handoff requirements for the new or revised blocks.
