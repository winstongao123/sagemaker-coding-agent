REVIEWED FILES:

- `compact_v5/_status/v5_completion_audit/THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md`
- `compact_v5/_status/v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md`
- `compact_v5/_status/v5_completion_audit/TEST_CASE_PREP.md`
- `compact_v5/_status/v5_completion_audit/SOFTWARE_BUILDER_BLOCK_REVISIT_PLAN.md`
- `compact_v5/_status/v5_completion_audit/STATUS.md`
- `compact_v5/_status/v5_completion_audit/BLOCK_ORDER_AND_COVERAGE.md`
- `compact_v5/MAIN/agent/tools/todo.py`
- `compact_v5/MAIN/agent/tools/task.py`
- `compact_v5/MAIN/agent/tools/bash.py`
- `compact_v5/MAIN/agent/runtime/session.py`
- `compact_v5/MAIN/agent/runtime/snapshot.py`
- `compact_v5/MAIN/agent/runtime/dream.py` (head)
- `compact_v5/MAIN/agent/commands.py` (cmd_save / cmd_resume / cmd_checkpoint / cmd_verify / cmd_done / cmd_dream / cmd_status)
- `compact_v5/MAIN/agent/prompt/sections.py` + `prompt/status_doc.md`
- `compact_v5/MAIN/agent/subagent/spawn.py` (head + SubagentResult)
- `compact_v5/MAIN/agent/core/compactor.py` (audit/event grep)
- `compact_v5/MAIN/agent/runtime/feature_flags.py` (memory_extraction default)
- `compact_v5/_status/scripts/build_telemetry.py` (compaction extractor)
- `compact_v5/MAIN/agent/tests/r_tier/test_software_project_workflow_contracts.py` (head)

FINDINGS:

1. The third scan's headline gaps are reproducible against current code:
   - `tools/todo.py` keeps `_TODOS` as a process-global list; `commands.py:cmd_save` writes only `messages` and `metadata["tokens_stats"]` to `Session`, never `session.todos`. `cmd_resume` mirrors this. The `Session.todos` field is dead. **DS3-S1 confirmed.**
   - `cmd_save/cmd_resume` do not cover phase, status pointer, checkpoint index, skill state, or memory anchor. **DS3-S2 confirmed.**
   - `prompt/status_doc.md` and `prompt/memory_protocol.md` are static instructional sections; no code path loads `AGENT_STATUS.md` or `memory.md` content into the prompt per turn (`pre_turn` / `reload_status` / `load_memory` greps return zero matches). **DS3-S3 confirmed.**
   - `cmd_done` returns advisory "Pre-ship gate (mode: ...)" text with `side_effect="done_armed:..."`; `cmd_verify` only activates the verify skill. Neither blocks close on missing evidence. **DS3-S4 confirmed.**
   - `subagent/spawn.py:SubagentResult` carries only `text / stop_reason / turns_used / child_messages / error / agent_type / depth`. No tokens, cost, cache, files_changed, duration, or heartbeat. **DS3-S5 confirmed.**
   - `tools/bash.py` uses `subprocess.run` with timeout and an `abort_event` checked only before start; `_combined_abort_event` never fires kill on the running process tree on either Windows or POSIX. **DS3-S16 confirmed.**
   - No background-shell module/grep hits anywhere under `compact_v5/MAIN/agent`. **DS3-S17 confirmed.**
   - `core/compactor.py` does not call `AUDIT.log` for compact/microcompact actions; `build_telemetry.py` only filters audit entries where `"compact" in action.lower()`, so real compactions go invisible to evidence unless the dispatch wrapper happens to log a generic compact action. **DS3-S10 confirmed.**
   - `runtime/feature_flags.py` defaults `memory_extraction: False`, and `runtime/config.py` defaults `enable_memory_extraction = False`. **DS3-S11 confirmed.**
   - `runtime/snapshot.py:revert` overwrites the file in place with no diff/preview. **DS3-S8 confirmed.**

2. Things the plan was right to NOT include:
   - `/dream` IS wired beyond the advisory text — `ui/chat_ui.py` handles the `dream_invoked` side-effect and dispatches `runtime.dream.run_dream`. Block H+ is closed correctly.
   - 18 of 21 ledger blocks (A, B, B+, C, C+, D, E+F, F2, G, G2, G3, H, H+, I, K, L, N, T) are closed/pushed. Remaining: M (0 rows), J (0 rows), 0 (10 rows).

3. Plan structural notes:
   - The `SOFTWARE-*` worker prefix avoids overlap with the existing `/status`, `/save`, `/resume`, `/checkpoint`, `/verify`, `/done`, `/phase`, `/cost`, `/context`, `/dream` commands and complies with the consolidation rule in `TEST_CASE_PREP.md`. Good.
   - There is no explicit traceability column in the plan that maps each DS3-S* gap to a specific SOFTWARE-* block. Memory wiring (DS3-S11) and broader failure-loop telemetry (DS3-S18) are not explicitly attached to a block — they appear to fold into `SOFTWARE-STATE` and `SOFTWARE-COMPACT-TELEMETRY` respectively but it should be stated.
   - Memory-extraction default-off is a real risk for the long-task goal but is not called out as a config flip the SOFTWARE-STATE block must own.

MISSING HIGH/CRITICAL GAPS:

None new beyond the third-scan list. Two refinements the plan should pick up before workers start:

- M-1 (refinement, not new gap) — `SOFTWARE-STATE` must explicitly include: (a) flipping `enable_memory_extraction`/`memory_extraction` defaults or wiring an opt-in path that R16/R19-U10 actually exercise, and (b) per-turn injection of a bounded `AGENT_STATUS.md` + `memory.md` slice into the prompt or a top-of-turn read tool result. Otherwise local tests can pass while the AWS scenarios still see stale model context.
- M-2 (refinement) — `SOFTWARE-SHELL` must specify the cross-platform kill semantics (Windows `Job Object` / `CREATE_NEW_PROCESS_GROUP` vs POSIX `os.killpg`) so the worker doesn't ship a no-op `.terminate()` that fails the no-orphan test on Windows (the production target).
- M-3 (refinement) — `SOFTWARE-COMPACT-TELEMETRY` must require `core/compactor.py` (and the auto/microcompact paths in `core/query_engine.py`) to emit dedicated audit actions (`compact_auto_start`, `compact_auto_end`, `compact_micro_start`, `compact_micro_end`, `compact_failed`) so `build_telemetry.py` can stop relying on substring matching.

BLOCK PLAN VERDICT:

The eight `SOFTWARE-*` blocks are coherent and non-overlapping with current command surfaces. The proposed scope is the right size for v5.0.1 if (M-1, M-2, M-3) above are folded into the corresponding block scopes before workers start. `SOFTWARE-GATE` correctly sits last because it consumes evidence surfaces from the earlier blocks. No conflicting `/project-*` commands are introduced. The Revisit Plan is the right churn-control mechanism.

Two concrete plan-document fixes recommended:
- Add a `DS3-S* → SOFTWARE-* block` traceability table to `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` so no gap silently falls between blocks.
- In `SOFTWARE-STATE` make the auto-load of `AGENT_STATUS.md` and `memory.md` into the per-turn prompt budget an explicit row, not implicit.

TEST PLAN VERDICT:

The bundling principle in `OPTIMIZED_AWS_VALIDATION_PLAN.md` is correct (R13/R14/R15/R16/R19-U10 cover distinct production qualities). However:

- R16 carries too many properties to provide actionable signal on failure. Add a sub-check checklist (status-roundtrip ✓, todo-roundtrip ✓, named-checkpoint-roundtrip ✓, verify-blocked-on-stale-evidence ✓, compaction-event-emitted ✓) so a fail can be localized without re-running.
- Local zero-cost tests are missing for: (a) `_TODOS` survives `/save` + `/resume` round-trip, (b) `cmd_done` refuses with an explicit reason when status is stale or last verify failed, (c) bash timeout actually kills a sleeping child process tree (use a real subprocess that writes a sentinel file after expected timeout — assert no sentinel), (d) `compact_auto_start/end` audit events are emitted by an actual compaction run. Add these before AWS spend.
- No optimized AWS scenario explicitly proves background-shell lifecycle. R19-U6/U7 cover repeated-call/output-recovery, not background process control. If `SOFTWARE-SHELL` ships background lifecycle, add a single bundled sub-step to R16 (start dev server, poll, kill, verify no orphan) instead of a new R-tier row.
- Cache-hit/read/write evidence is required by the matrix but Bedrock exposure of those signals is inconsistent — the plan should pre-state the fallback assertion (e.g., "cache_read_count is non-null OR a documented model-side limitation row is recorded").

ASYNC DECISION:

DEFER true async/background subagents in v5.0.1; implement strengthened synchronous supervision now. Reasons:

1. Single-person SageMaker `.ipynb` runtime is single-kernel; true background workers add notebook-loop, signal, and IPC complexity that the product doesn't need yet.
2. The observability gap (no token/cost/cache/files-changed/heartbeat in `SubagentResult`) is the actual cause of "blind delegation" complaints. A structured synchronous envelope plus parent-side recovery captures ~85% of the production benefit at a fraction of the risk surface.
3. `task` is already `is_concurrency_safe=False`. Lifting that without process-tree management (which requires `SOFTWARE-SHELL` first) would create a foot-gun.
4. The deferral must be recorded honestly in the AWS test descriptions (R3 / R18-E11 / R19-U4 / R19-U5) so reviewers don't expect parallel subagent traces in evidence.

RECOMMENDED WORKER BLOCK ORDER:

1. **SOFTWARE-ASYNC-DECISION** — written deferral first, unblocks `SOFTWARE-SUBAGENT` design without risk of mid-block drift.
2. **SOFTWARE-STATE** — durable todos, per-turn `AGENT_STATUS.md` + `memory.md` injection, crash-safe per-turn journal, memory-extraction flip; prerequisite for any meaningful `/done` gate and for R16/R19-U10 evidence.
3. **SOFTWARE-CHECKPOINT** — durable named-checkpoint index + revert preview; independent of STATE but small.
4. **SOFTWARE-SHELL** — cross-platform process-tree kill (Windows `JobObject` / POSIX `killpg`), background lifecycle (`bash_bg start/poll/kill/wait`), no-orphan tests; required before SUBAGENT timeout/heartbeat enforcement.
5. **SOFTWARE-RESULTS** — large tool-result persistence/replay with stable references; required before SUBAGENT envelope can carry artifact pointers.
6. **SOFTWARE-SUBAGENT** — structured synchronous envelope (tokens/cost/cache/files/duration/heartbeat) + parent recovery; consumes RESULTS for output references and SHELL for kill semantics.
7. **SOFTWARE-COMPACT-TELEMETRY** — dedicated `compact_*` audit events + broader failure-signature loop breaker + `build_telemetry.py` switch from substring match to typed action match.
8. **SOFTWARE-GATE** — enforced `/verify` and `/done` gating that reads STATE freshness, RESULTS evidence, SUBAGENT envelopes, and COMPACT-TELEMETRY events; ship-blocks on missing evidence.

Run the optimized AWS matrix only after all eight blocks are closed, locally tested, scope-audited, and Claude-row-reviewed.

VERDICT: APPROVE_WITH_FIXES

The plan is architecturally fit and the gap classifications match what the code actually shows. APPROVE conditional on three documentation fixes before workers start: (a) add a DS3-S* → SOFTWARE-* traceability table, (b) fold the M-1/M-2/M-3 refinements (per-turn status+memory injection, cross-platform kill semantics, typed compaction audit events) into the relevant block scopes explicitly, and (c) add the four zero-cost local tests listed in TEST PLAN VERDICT before any AWS/R-tier spend resumes.

