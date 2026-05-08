# W6 — Sub-agent Coordination + Parallel Tool Execution + Delegation

**Date**: 2026-05-01
**Author**: User-perspective brainstorm (25 scenarios)
**Plan version**: V5_PHASE_2_PLAN_v3.md (post-no-deferrals 2026-05-01)
**Synthesis**: SYNTHESIS_MASTER.md (Wave 5-DEEP)
**v4 baseline cited**:
- AGENT_TYPES dict: `compact_v4/MAIN/agent/sagemaker_agent.py:6914-7090`
- Worktree spawn (`build`): `:8413` ff
- `_build_subagent_handoff_block`: `:7771-7841`
- `_build_subagent_env_details`: `:7695-7738`

**v5 Blocks referenced**:
- **G** = AGENT_TYPES + worktree (verbatim port from v4 + Runnable G-3/G-5/G-7)
- **G2** = forkSubagent cache-prefix replay (Runnable `forkSubagent.ts:73-end`)
- **G3** = Coordinator system prompt (Runnable `coordinatorMode.ts:111-369`, ~270 LOC, gated by `CONFIG.coordinator_mode_enabled`)
- **N** = Parallel tool execution + path-conflict + dedup + fuzzy match + dynamic tool ref (Hermes `run_agent.py:259-280, 311-372, 8274-9112, 4639-4655, 4689-4720, 850/1486-1488`)
- **B/B+** = TokenTracker per-agent attribution (parent + per sub-agent type)

---

## Legend

- **HANDLED** = Plan v3 Blocks G + G2 + G3 + N + B+ already specify the behavior + a Q4 lock test
- **NEEDS-LOCK-TEST** = Plan covers it conceptually but no specific lock test in Q4 yet — must add before Block G/G2/G3/N implementation
- **POSSIBLE-GAP** = Plan does not address it; needs explicit decision before Phase 3 implementation

---

## Scenario 1 — User invokes `task(subagent_type="build", prompt="implement /api/leads")`

**What user does**: types `task(subagent_type="build", prompt=..., max_turns=20)` in chat cell.

**What could go wrong**: dispatcher silently drops `subagent_type` and uses `build` default; or rejects unknown type with a useless error; or returns `general` agent without telling user.

**Plan provides**: Block G ports `AGENT_TYPES` dict (7 types) verbatim from v4 `:6914-7090`. `subagent/spawn.py` dispatches by `subagent_type`. Block G Q4 lock test = "lock test for each agent type". G3 Coordinator prompt teaches when to pick which type.

**Verdict**: HANDLED.

---

## Scenario 2 — User runs `task(subagent_type="explore")` on a 50K-file repo

**What user does**: explore agent does parallel `glob` + `grep` to map a foreign codebase.

**What could go wrong**: explore agent attempts file writes (it should be read-only per v4 prompt at `:6931-6936`); or `_PARALLEL_SAFE_TOOLS` filter is missing so glob+grep run sequentially.

**Plan provides**: Block G ports v4 explore prompt verbatim ("STRICTLY PROHIBITED from creating, modifying, or deleting files" — `:6931-6936`). Tool whitelist enforced via `tools={"read_file","glob","grep","list_dir","semantic_search"}`. Block N N-3 ports `_PARALLEL_SAFE_TOOLS` constant (Hermes `:259-280`). Block N Q4 lock test = "parallel-exec independent reads ≥40% wallclock gain".

**Verdict**: HANDLED.

---

## Scenario 3 — Parent spawns 3 sub-agents in parallel (research/plan/verify)

**What user does**: parent issues 3 `task(...)` calls in the same assistant message.

**What could go wrong**: Bedrock dispatch serializes them; ThreadPoolExecutor missing; or parent waits for first to finish before starting second.

**Plan provides**: Block N N-4 ports Hermes worker tid + ThreadPoolExecutor at `:8463-8725` (~200 LOC). `_MAX_TOOL_WORKERS=4` (Hermes `:259-280`). Block N Q4 lock test covers parallel exec wallclock win.

**Verdict**: NEEDS-LOCK-TEST. Plan covers parallel **tool calls** but does not explicitly assert that parallel **task() sub-agent dispatches** also share the same ThreadPoolExecutor. Add lock test: "3 task() calls in one assistant turn — assert wallclock < 1.2 × max(individual)."

---

## Scenario 4 — Sub-agent crashes (Bedrock 5xx after 3 retries)

**What user does**: parent dispatches build sub-agent; mid-task Bedrock returns ThrottlingException repeatedly.

**What could go wrong**: parent gets a stack trace as `tool_result` and aborts the parent turn; or parent never gets a result and stalls forever.

**Plan provides**: Block L L-17 (API error humanizer Bedrock-only) + L-19 (one-extra primary recovery after max retries) + L-20 (three-tier recovery ladder) + N-8 (retry classifier — pre-call/mid-call/post-call). Block N N-9 (mid-call stub recovery with user-visible warning, Hermes `:6644-6709`).

**Verdict**: NEEDS-LOCK-TEST. The "sub-agent crashed → parent receives a clean failure summary" path is not explicitly tested. Add lock test: "force Bedrock 5xx in sub-agent → parent receives `tool_result` with `is_error=true` + humanized message + parent turn continues."

---

## Scenario 5 — Sub-agent edits the same file the parent is mid-editing

**What user does**: parent runs `edit_file('a.py', ...)` then dispatches build sub-agent that also touches `a.py`.

**What could go wrong**: write-write race; or file content reverts because sub-agent read stale content; or git working tree corrupt.

**Plan provides**: Block N N-2 path-scoped parallelism helpers (`:355-380`) + N-3 `_PATH_SCOPED_TOOLS` constant. Block G worktree spawn (v4 `:8413`) isolates `build` agent in a separate worktree. Hermes path-conflict detection at `run_agent.py:311-355` (Block N row 1).

**Verdict**: NEEDS-LOCK-TEST. Worktree isolation handles the **build** type, but `general` / `verify` / `simplify` sub-agents run in the parent's CWD and could collide. Add lock test: "two non-build sub-agents writing same path — second one rejected with PathConflictError."

---

## Scenario 6 — `/done` command pipeline spawns simplify + verify sequentially

**What user does**: types `/done` after a feature implementation.

**What could go wrong**: simplify runs, edits files, then verify sees stale snapshot; or verify runs in parallel with simplify and reports false failures; or simplify token cost not attributed.

**Plan provides**: Block G3 Coordinator prompt (Runnable `coordinatorMode.ts:111-369`) codifies "parallel research, **serial write**" rule. G3-1 row marks this as **HIGH-MUST**. Block B+ token attribution per sub-agent type.

**Verdict**: NEEDS-LOCK-TEST. The G3 prompt is gated by `CONFIG.coordinator_mode_enabled=False` by default. Add lock test that `/done` (a built-in command) **forces** serial simplify→verify regardless of coordinator-mode flag.

---

## Scenario 7 — 8 parallel `read_file` tool calls in one assistant turn

**What user does**: parent issues 8 `read_file` calls in a single response (e.g., to map related modules).

**What could go wrong**: order in `tool_result` array doesn't match `tool_use` order so model sees mismatched results; per-call cost not attributed; ThreadPoolExecutor cap of 4 silently serializes the rest.

**Plan provides**: Block N N-3 `_MAX_TOOL_WORKERS=4` constant (Hermes `:259-280`). Block N N-4 worker tid race fix (Hermes `:8463-8482`) preserves order via tid mapping. Block B+ TokenTracker attributes per parent.

**Verdict**: HANDLED. Hermes pattern preserves order via tid; cap=4 is intentional (Bedrock burst limits).

---

## Scenario 8 — Hermes path-conflict detection blocks two sub-agents writing same file

**What user does**: parent dispatches sub-agent A (write `b.py`) and sub-agent B (write `b.py`) in parallel.

**What could go wrong**: detector lets both through; or detector blocks both with no fallback; or detector only checks paths and misses the case where one writes a directory and the other writes a file inside it.

**Plan provides**: Block N row 1 = path-conflict detection (`run_agent.py:311-355`) + dispatch logic (`:8274-8523`). N-2 path-scoped helpers (`:355-380`). N-5 sequential path bookkeeping (`:8727-9112`) as fallback when batch is unsafe.

**Verdict**: NEEDS-LOCK-TEST. Add explicit lock test for parent path + child path conflict (e.g., A writes `src/` directory rename; B writes `src/foo.py`).

---

## Scenario 9 — Cache-prefix replay (Block G2) saves tokens on sub-agent dispatch

**What user does**: parent dispatches sub-agent #1 then sub-agent #2 with same system prompt + handoff block.

**What could go wrong**: each dispatch rebuilds messages from scratch and breaks Bedrock cache hit; cache_control not propagated; or cache-prefix-share mode not actually byte-identical.

**Plan provides**: Block G2 ports Runnable `forkSubagent.ts:73-end` (~100 LOC). Q4 lock test = "parent + child API request bytes share identical prefix when cache_prefix_share=True". A-31 + A-32 (Hermes prefix-stable normalization) reinforce.

**Verdict**: HANDLED. Strongly tested in plan. (Q4 byte-identical assertion is the strongest lock there is.)

---

## Scenario 10 — AGENT_TYPES dict — user passes unknown `subagent_type="researcher"`

**What user does**: typo — meant "explore".

**What could go wrong**: silent fallback to `general` with no warning; or hard fail with stack trace; or fuzzy match picks something user didn't want.

**Plan provides**: Block I + Block N N-15 fuzzy tool-name matching (Hermes `:4689-4720`, ~30 LOC) — already extends to subagent_type lookup. Block G prompt suffix names + Coordinator prompt G3 lists 7 valid types.

**Verdict**: NEEDS-LOCK-TEST. Plan applies fuzzy match to **tool names**; not stated whether `subagent_type` benefits. Add lock test: `subagent_type="researcher"` → resolves to `explore` with INFO log; `subagent_type="zzz"` → user-visible error listing 7 valid types.

---

## Scenario 11 — Sub-agent depth limit (parent → child → grandchild)

**What user does**: build sub-agent recursively spawns another build sub-agent which spawns another.

**What could go wrong**: infinite recursion blows context window; or no depth tracking; or grandchild claims to be parent and double-counts tokens.

**Plan provides**: Block G ports v4 AGENT_TYPES; v4 baseline does **not** include explicit depth tracking. Runnable `forkSubagent.ts` (Block G2) tracks parent_session_id but no depth cap.

**Verdict**: POSSIBLE-GAP. Add `MAX_SUBAGENT_DEPTH=2` constant + lock test: grandchild `task()` call rejected with "max sub-agent depth exceeded". This is a v5-native enhancement, not in any of the 4 reference repos — but follows from "structurally fix PS_problems" rule.

---

## Scenario 12 — User invokes `task(subagent_type="build", use_worktree=True)` on non-git workspace

**What user does**: builds in `/home/sagemaker-user/scratch/` (not a git repo).

**What could go wrong**: `git worktree add` fails; sub-agent silently runs in main CWD; or dispatcher crashes.

**Plan provides**: SYNTHESIS_MASTER.md §7.5 (R1 worktree clarification): "SageMaker workspace usually `/home/sagemaker-user/`, not a git repo. Drop EnterWorktree/ExitWorktree formal tools." Block G keeps **implicit** worktree spawn for build only.

**Verdict**: NEEDS-LOCK-TEST. Add lock test: "non-git CWD + `subagent_type=build` → fall back to plain dispatch (no worktree) with INFO log; do NOT crash."

---

## Scenario 13 — `IterationBudget` of 25 turns is shared between parent and 3 sub-agents

**What user does**: parent has `max_turns=25`, dispatches 3 sub-agents each with their own `max_turns`.

**What could go wrong**: parent budget decremented by sub-agent turns (double-charge); or sub-agent budgets not tracked at all; or budget exhaustion in sub-agent silently aborts.

**Plan provides**: Block G G-5 ports Hermes `IterationBudget` from `:213-254` (~30 LOC) — explicitly "Subagent budget plumbing". Each `AGENT_TYPES` entry has its own `max_turns` (build=25, plan=15, explore=10, verify=15, etc.).

**Verdict**: NEEDS-LOCK-TEST. Add lock test: "parent budget=25, sub-agent budget=10 → parent counter unchanged by sub-agent turns; sub-agent independently exhausts at 10 with `MaxTurnsExceeded`."

---

## Scenario 14 — Sub-agent returns 30K-token result, blowing parent context

**What user does**: explore sub-agent reads 50 files and dumps a 30K-token summary.

**What could go wrong**: parent appends 30K to context, hits compaction immediately; or token cost mis-attributed to parent input rather than sub-agent output.

**Plan provides**: Block N N-6 `enforce_turn_budget` over `messages[-num_tools:]` (Hermes `:8714-8725`, ~30 LOC) — token cap on tool result aggregate. Block G G-3 `ONE_SHOT_BUILTIN_AGENT_TYPES` (Runnable `AgentTool/constants.ts:9-12`) skips trailer for explore/plan/verify (token saver). Block B+ separates parent input vs sub-agent output.

**Verdict**: HANDLED.

---

## Scenario 15 — Sub-agent's `_build_subagent_handoff_block` (parent-context summary) is malformed

**What user does**: parent dispatches sub-agent with very long task description.

**What could go wrong**: handoff block exceeds Bedrock prompt limit; or contains leaked PII the user wanted scrubbed; or has surrogate chars that crash Bedrock JSON encoder.

**Plan provides**: Block G ports `_build_subagent_handoff_block` from v4 `:7771-7841` verbatim. Block A A-26 surrogate sanitization recursive walker (Hermes `:384-502`, 115 LOC) runs before every Bedrock converse — covers handoff block too.

**Verdict**: HANDLED.

---

## Scenario 16 — Coordinator prompt (G3) makes parent over-decompose simple tasks

**What user does**: asks "rename one variable" — parent (with `coordinator_mode_enabled=True`) spawns plan + build + verify sub-agents.

**What could go wrong**: 4-phase rule fires for trivial work; tokens wasted; latency 5x worse.

**Plan provides**: Block G3 G3-1 — gated by `CONFIG.coordinator_mode_enabled` (default **False**). G3 prompt itself includes "continue-vs-spawn matrix" so coordinator decides when NOT to delegate.

**Verdict**: NEEDS-LOCK-TEST. Plan defaults the flag off, but does not lock test "trivial single-file edit with coordinator_mode=True still completes in 1 turn (no spurious sub-agent dispatch)."

---

## Scenario 17 — Parent forgets sub-agent's findings between turns

**What user does**: spawns explore sub-agent, gets findings, tries to use them 5 turns later after compaction.

**What could go wrong**: compaction drops sub-agent result; parent re-spawns explore; tokens wasted.

**Plan provides**: Block A A-28 post-compaction details (todo re-inject, file-dedup reset, token refresh) + A-27 `flush_memories` pre-compression turn (Hermes `:7913-8157`). Block H (memory) extracts sub-agent findings to scoped memory file.

**Verdict**: NEEDS-LOCK-TEST. Add explicit assertion: "sub-agent result mentioned in parent assistant message → preserved in compaction summary."

---

## Scenario 18 — TokenTracker shows wrong cost split for parent vs sub-agent

**What user does**: opens cost sidebar after running a `/done` pipeline.

**What could go wrong**: all tokens show as "parent"; or sub-agent type column missing; or session_cost ≠ sum(per_agent).

**Plan provides**: Block B+ TokenTracker singleton (`compact_v4/MAIN/agent/sagemaker_agent.py:3565-3753, :3755`) extended with per-agent attribution dict (`parent_*`, `subagent_*[type]`). Plan v3 line 162 — explicit acceptance test asserts `TOKENS.session_cost == sum_of(per_agent_cost) ± $0.0001`.

**Verdict**: HANDLED.

---

## Scenario 19 — User cancels (Ctrl-C) mid sub-agent execution

**What user does**: parent dispatched 3-min build sub-agent; user hits Ctrl-C at 90s.

**What could go wrong**: ipykernel hangs; sub-agent worktree left in dirty state; tokens billed but no result returned; parent stuck waiting.

**Plan provides**: Block L L-21 daemon-thread Bedrock call for Ctrl-C responsiveness (Hermes `:5637-5781`, 80 LOC). L-22 stale non-stream call detector. L-23 heartbeat callback every 30s. Block G worktree cleanup is part of v4 `:8413` ff.

**Verdict**: NEEDS-LOCK-TEST. Lock test: "KeyboardInterrupt during sub-agent → parent gets `is_error=true` `tool_result` within 2s; worktree cleaned; tokens flushed to TokenTracker."

---

## Scenario 20 — Sub-agent calls `task()` to spawn a peer (lateral fork)

**What user does**: build sub-agent decides to call explore mid-task instead of doing it itself.

**What could go wrong**: parent doesn't expect 2nd-level dispatch; cost attribution flattens to "build" subtype losing the "explore" sub-cost; cache prefix sharing breaks.

**Plan provides**: Block G allows nested task() calls (v4 baseline does this). Block G2 cache-prefix replay handles parent-of-parent prefix. Block B+ uses subagent_type as key — nested explore would correctly add to `subagent_*['explore']`.

**Verdict**: NEEDS-LOCK-TEST. Lock test: "build sub-agent calls task('explore') → TokenTracker shows both `subagent_*['build']` AND `subagent_*['explore']` non-zero; combined ≤ MAX_SUBAGENT_DEPTH (Scenario 11)."

---

## Scenario 21 — Tool dedup blocks legitimate retry of same tool call

**What user does**: sub-agent calls `bash('pytest')`, fails, decides to call `bash('pytest -v')` (different args).

**What could go wrong**: Hermes dedup (Block N N-16, `run_agent.py:4639-4655`) is too aggressive and blocks the second call as "duplicate".

**Plan provides**: Block N N-16 ports the dedup logic verbatim. Hermes implementation hashes (tool_name, args) — different args → different hash → not blocked.

**Verdict**: HANDLED. (Dedup is on tool_name+args, so `pytest` vs `pytest -v` are different.)

---

## Scenario 22 — `partial_tool_names` warning fires after sub-agent dies mid-write

**What user does**: build sub-agent issues `write_file` with 50K content; Bedrock disconnects mid-stream.

**What could go wrong**: parent sees `tool_use` with no matching `tool_result` → Bedrock 400 on next turn; or parent silently re-issues the write.

**Plan provides**: Block N N-7 `partial_tool_names` tracking + warning-on-death (Hermes `:6175, 6663-6687`, 40 LOC, **NEEDS-ADAPTATION** for non-streaming Bedrock invoke). Block A A-25 stub-injection for missing tool_results post-compact (Hermes `:4585-4604`, 25 LOC, **MUST**).

**Verdict**: HANDLED. (A-25 is **MUST**; lock-tested via Bedrock 400-on-missing-result regression test.)

---

## Scenario 23 — Sub-agent system prompt cache invariant (A28 policy) violated

**What user does**: dispatches sub-agent, then mid-conversation toggles a tool flag (e.g., enables web_fetch).

**What could go wrong**: system prompt rebuilt with new toolset → cache miss → 0% cache hit rate → 5-15% cost regression.

**Plan provides**: Block A A-33 A28 prompt-cache invariant policy (Hermes A28, **MUST**, NEEDS-ADAPTATION) — "NEVER rebuild system prompt mid-conv; toolset changes deferred to next session via `--now` opt-in. v4 violates this — v5.0.1 must enforce."

**Verdict**: NEEDS-LOCK-TEST. Critical Hermes-imported policy — add lock test: "mid-session tool toggle → system prompt unchanged for current session; new flag honored only on next session start."

---

## Scenario 24 — Verify sub-agent reads its own success criteria from a stale plan file

**What user does**: parent passes `plan_file_path` to verify sub-agent.

**What could go wrong**: plan file rewritten by simplify (or another sub-agent) before verify reads it; verify validates against wrong spec.

**Plan provides**: Block G3 Coordinator prompt enforces "parallel research, **serial write**" (G3-1, Runnable `coordinatorMode.ts:111-369`). Verify prompt itself (v4 `:6938-6973`) instructs reading the plan file.

**Verdict**: NEEDS-LOCK-TEST. Lock test: "verify sub-agent's read of plan_file is followed by SHA256 assertion that file matches the SHA captured at dispatch time; mismatch → verify reports 'spec drift, manual review needed'."

---

## Scenario 25 — Dynamic tool reference injection (Block N) confuses sub-agents

**What user does**: parent has access to MCP tool `playwright_screenshot`; explore sub-agent gets a system prompt that mentions playwright but its toolset whitelist excludes it.

**What could go wrong**: explore tries to call `playwright_screenshot`, gets "tool not available", model loops; or dynamic tool ref injection (Block N N-14, Hermes `AGENTS.md:627-628`) injects refs to tools the sub-agent can't use.

**Plan provides**: Block N N-14 dynamic tool-ref injection. Block G AGENT_TYPES dict has explicit `tools` whitelist per type. Plan v3 line 360: "implement in `core/query_engine.py` build-tools-payload phase. NO DEFERRAL."

**Verdict**: NEEDS-LOCK-TEST. Lock test: "tool-ref injection runs **after** sub-agent toolset whitelist filter — refs to filtered-out tools must be stripped from sub-agent system prompt."

---

# Summary

| Verdict | Count | Scenarios |
|---|---|---|
| **HANDLED** | **9** | 1, 2, 7, 9, 14, 15, 18, 21, 22 |
| **NEEDS-LOCK-TEST** | **15** | 3, 4, 5, 6, 8, 10, 12, 13, 16, 17, 19, 20, 23, 24, 25 |
| **POSSIBLE-GAP** | **1** | 11 (sub-agent depth limit — no source repo has it; v5-native add) |

## Top 3 risks for v5.0.1 ship

1. **Scenario 11 (depth limit) — only POSSIBLE-GAP**. Add `MAX_SUBAGENT_DEPTH=2` to Block G constants + lock test before Phase 3 implementation. Prevents runaway recursion (PS_problem-class issue).
2. **Scenario 23 (A28 cache invariant) — NEEDS-LOCK-TEST and MUST-policy**. Highest cost-impact item; missing lock test means we ship without enforcement signal. Add lock test in Block A Q4.
3. **Scenario 5 + Scenario 8 (path conflict, write-write race) — both NEEDS-LOCK-TEST**. Hermes patterns are MUST-import but the v5 specific lock tests aren't itemized. Add 2 lock tests in Block N Q4.

## Recommended Plan v3 deltas (before Block 0 starts)

| Block | Delta | Source |
|---|---|---|
| G | Add `MAX_SUBAGENT_DEPTH=2` constant + Q4 lock test (Scenarios 11, 20) | v5-native |
| G | Add Q4 lock test for non-git CWD fallback (Scenario 12) | v4 baseline behavior |
| G | Add Q4 lock test for unknown subagent_type fuzzy resolution (Scenario 10) | Block I fuzzy match |
| G2 | Already has byte-identical Q4 test — confirm covers Scenario 9 nested case | already in plan |
| G3 | Add Q4 lock test: trivial task w/ coordinator_mode=True does NOT spawn sub-agents (Scenario 16) | Runnable G3-1 |
| G3 | Add Q4 lock test: `/done` forces serial simplify→verify regardless of flag (Scenario 6) | v5-native |
| N | Add Q4 lock test: 3 parallel `task()` calls share ThreadPoolExecutor (Scenario 3) | Hermes N-4 extension |
| N | Add Q4 lock test: write-write path conflict between non-build sub-agents (Scenario 5, 8) | Hermes path-conflict |
| N | Add Q4 lock test: tool-ref injection respects sub-agent toolset filter (Scenario 25) | N-14 |
| L | Add Q4 lock test: Bedrock 5xx in sub-agent → clean parent recovery (Scenario 4) | L-17 + L-19 + N-8 |
| L | Add Q4 lock test: Ctrl-C during sub-agent → 2s recovery + worktree cleanup (Scenario 19) | L-21/22/23 |
| B+ | Acceptance test already covers parent + 1 sub-agent attribution; extend to nested (Scenario 20) | Plan v3 line 162 |
| A | Add Q4 lock test: A28 cache invariant on mid-session tool toggle (Scenario 23) | Hermes A-33 |
| A | Add Q4 lock test: sub-agent findings preserved across compaction (Scenario 17) | A-27 + A-28 |
| G | Add Q4 lock test: `IterationBudget` independence parent vs child (Scenario 13) | Hermes G-5 |
| G + N | Add Q4 lock test: verify sub-agent SHA256-checks its plan file (Scenario 24) | G3 + serial-write |

**Total new Q4 lock tests required: 15** (one per NEEDS-LOCK-TEST scenario).

**Total new constants required: 1** (`MAX_SUBAGENT_DEPTH=2` in `subagent/spawn.py`).

No new Blocks. All gaps close inside existing G / G2 / G3 / N / B+ / A / L block scope.

---

**End W6 — sub-agent + parallel + delegation brainstorm.**
