# V5 Deep Scan vs Runnable Claude Code

Date: 2026-05-11

Scope: `compact_v5/` active flattened runtime compared against `D:/Github/gg_claude_code/gg-claude-code-runnable/src`.

This is a review-only pass. No source code was changed.

## Executive Verdict

v5 is materially healthier after the UI live-supervisor work. The original "stuck" feeling is mostly fixed in the active runtime: tool starts/results, subagent lifecycle, subagent artifact paths, assistant markdown, and per-turn metrics now render live through `ui/chat_ui.py`.

But v5 is not yet fully comparable to the Runnable Claude Code repo on coordination and request tracking. The biggest remaining gap is not a single UI bug. It is that Runnable treats tasks, agents, progress, and background work as first-class application state, while v5 still uses a lighter combination of `todo_write`, synchronous `task`, receipts, journals, and status files. That is workable, but it explains why long work can still feel harder to supervise than Runnable.

## Current Active Tree

| Area | Status | Evidence |
|---|---:|---|
| Active source tree | Flattened `compact_v5/` | `compact_v5/ui/chat_ui.py` exists; `compact_v5/compact_v5/ui/chat_ui.py` does not. |
| Zip shape | Flattened zip root | `compact_v5.zip` has `agent.py`, `ui/chat_ui.py`, `core/query_engine.py`, `tools/task.py`; no `compact_v5/agent.py` or `MAIN/agent/agent.py`. |
| Zip integrity | Pass | `zipfile.testzip()` returned `None`; 155 members; size 639054 bytes. |
| Git cleanliness | Dirty/noisy | Git sees old `compact_v5/MAIN/agent/...` files deleted and flattened files as untracked or modified. Treat this as a source-control/package risk, not a runtime failure. |
| Runnable reference | Present | `D:/Github/gg_claude_code/gg-claude-code-runnable/src`. |

## What Is Fixed Since Worker UI Pass

| User-facing problem | Before | Current status | Evidence | Remaining concern |
|---|---|---|---|---|
| Live output looked stuck | `output_fn` appended to a local list and UI rendered after `agent.run()` returned. | Fixed in UI path. `_live_output_router()` renders chunks during the run. | `compact_v5/ui/chat_ui.py:1051`, `agent.run(... output_fn=lambda s: self._live_output_router(...))` at `chat_ui.py:1239`. | Non-UI callers still need their own callback handling. |
| Tool use invisible | Tool start/result was not shown as structured UI. | Fixed in UI path. Tool generation/result events exist. | `QueryEngine.tool_gen_callback` at `core/query_engine.py:337,388,1889`; UI sets `engine.tool_gen_callback` at `chat_ui.py:1232`. | `Agent.__init__` does not expose a public `tool_gen_callback` parameter; UI mutates private `_engine`. |
| Subagent invisible | Child output was swallowed by list append. | Mostly fixed. `tools/task.py` forwards child output as `[subagent:<type>:child]`. UI parses subagent lifecycle and result envelopes. | `tools/task.py:257-300`; `chat_ui.py:1058-1079`, `1125-1168`. | Tool prompt text still says subagent results are not incrementally visible. |
| Metrics all one column | Metrics were visually hard to scan. | Fixed in UI styling. Footer and per-turn meta now use flex style. | `chat_ui.py:936`, `chat_ui.py:1001`, status rendering around `chat_ui.py:884-928`. | Needs notebook visual regression kept in future UI changes. |
| Assistant output pure markdown | Assistant and tool/thinking cards were not separated. | Fixed in UI path. Assistant markdown, tool cards, subagent cards, and status cards have separate roles. | `chat_ui.py:547`, `575`, `1051+`. | Long rendered history is still a single HTML widget, not virtualized. |
| Stop UX unclear | Stop looked like hard stop. | Fixed wording. UI says cooperative stop and current Bedrock/tool/subagent call will finish. | `chat_ui.py:373`, `888-894`, `1272-1277`. | True interrupt of in-flight Bedrock call is still not present. |
| Token/cost driver line absent | User had no quick clue what drove cost. | Improved. UI now renders cost-driver text and per-turn metrics. | `chat_ui.py:989-998`, `_turn_meta_from_stats()` at `chat_ui.py:1001`. | This is display, not optimization by itself. |

## Detailed Findings

| ID | Severity | Area | Finding | Why it matters | Fix direction |
|---|---|---|---|---|---|
| F1 | High | Source layout / release control | The active runtime is flattened, but Git still sees many old nested files deleted and many flattened files untracked. | A future worker can diff the wrong tree, rebuild zip from stale assumptions, or accidentally revert the active runtime. Non-technical: the product works, but the filing cabinet labels are out of sync with where the files actually live. | Choose one canonical layout. If flattened is final, `git add -A compact_v5 compact_v5.zip compact_v5_test_evidence/...` deliberately and update stale docs/scripts. If nested is final, restore nested source and rebuild zip from that. |
| F2 | High | Worker instructions / subagent prompt | `tools/task.py` and `subagent/agent_types.py` still contain stale guidance: "general only", "no worktree", "result must be incrementally visible" warning, and "parent cannot see intermediate tool calls". Runtime now supports multiple subagent types, worktree for build, and live child output. Claude confirmed the stale "parent cannot see" note is appended to all seven agent types through `SUBAGENT_NOTES`, so the blast radius is wider than one role. | The model reads tool descriptions. Wrong tool text can cause it to avoid subagents, under-report progress, or tell users "I cannot show that" when the UI can show it. | Update only prompt/doc text, then lock with a grep test that forbids stale phrases. |
| F3 | Medium-High | Public callback architecture | `QueryEngine` has `tool_gen_callback`, and UI wires it by mutating `agent._engine.tool_gen_callback`. `Agent` itself does not expose this callback in `__init__` or `run()`. | Notebook UI works, but public non-UI surfaces cannot subscribe cleanly to tool start/result events. This is an architecture leak compared with Runnable's first-class progress messages. | Add a public callback path on `Agent`, or a small event bus surface. Keep UI using public API. |
| F4 | Medium-High | Request/status tracking | v5 has `todo_write`, `todo_read`, `AGENT_STATUS.md`, turn journal, and subagent receipts. Runnable has richer `TaskCreate`, `TaskUpdate`, `TaskGet`, `TaskList`, `TaskOutput`, and `TaskStop` with owner, dependencies, status changes, and hooks. | This is the big "supervisor feeling" gap. v5 can track work, but not as a first-class request graph. Long user requests are harder to audit, resume, assign, and verify. | Add a minimal v5 task-state layer or extend todo state with IDs, owner, dependencies, evidence paths, and verification nudges. |
| F5 | Medium | Token consumption | Built system prompt is about 14,748 chars: 12,081 static plus 2,648 dynamic for current workspace. Visible tool schemas add about 18,123 chars; deferred schemas add 11,859 chars only when loaded. Status and memory can add up to about 16 KB dynamic text per turn. | The high numbers the user saw are plausible when Thinking ON uses 4096 budget across many calls. Also, uncached dynamic status/memory text can add recurring input load. | Measure per run: prompt static/dynamic chars, visible schema chars, status/memory chars, cache read/write, thinking budget, calls. Consider hash/delta status injection and smaller default memory/status caps. |
| F6 | Medium | Caching | Prompt boundary is correctly present once and Bedrock splits static vs dynamic. QueryEngine freezes cache invariants for model/system/tools. | Good foundation. The risk is dynamic tail growth and toolset changes, not missing cache boundary. | Keep boundary tests. Add a dashboard row showing static prompt, dynamic prompt, visible schema, deferred schema loaded, cache read/write percent. |
| F7 | Medium | Subagent coordination | v5 subagents are synchronous child runs sharing parent budget. Runnable supports background agents, progress lines, auto-background after long duration, SendMessage, TaskOutput/Stop, and agent foreground/background management. | v5 now shows child progress, but the parent cannot manage several long-lived background agents like Runnable. For notebook use this may be acceptable, but it is not parity. | Decide whether v5 needs "Runnable-like background agent management". If yes, design it as a separate block, not a small UI patch. |
| F8 | Medium-High | Read-only agent safety | `_READ_ONLY_TOOLS` includes `todo_write`. Explore/plan/review agents cannot edit files, but they can mutate the global todo list. Claude confirmed this persists to disk through `tools/todo.py`, so it can alter parent recovery state across processes. | This weakens the mental model of "read-only". A reviewer could alter parent task state and durable recovery state. | Remove `todo_write` from read-only subagents first. A later design can add child-local todo state if needed. |
| F9 | Medium | Tool dispatch performance | v5 can parallelize safe calls, but only takes the parallel fast path when there are multiple parallel calls and no sequential calls. Mixed batches are handled sequentially. Runnable can run tool calls concurrently while maintaining in-progress state. | Conservative and safe, but leaves performance on the table for common mixed batches like several reads plus one write. | Keep write serialization, but allow parallel-safe subset to run first or alongside sequential queue when context mutation rules allow. |
| F10 | Medium | UI scalability | The notebook UI uses one HTML chat display rebuilt from message rows. This is much better than the previous stuck state, but not equivalent to Runnable's terminal message/progress components. | Very long sessions can get heavy in the notebook. The user may again perceive lag after many messages, even though live streaming is fixed. | Add message pruning/virtualization or collapsible history buckets for old tool/subagent cards. |
| F11 | Low-Medium | Zip/docs drift | Evidence docs and `AGENT_STATUS.md` still mention `compact_v5/compact_v5/` in places. Zip itself is flattened and valid. | Workers may inspect the wrong file path. User may think fixes are missing because docs point to the old tree. | Sweep docs for active-path references and add a "Current active tree is flattened `compact_v5/`" note in the main status docs. |
| F12 | Low-Medium | Claude CLI reviewer workflow | The correct subscription-auth workflow is documented, but previous worker used an API-token path and hit credit errors. | The review process can falsely report "Claude unavailable" when the subscription CLI would work. | Use `C:/Users/winst/AppData/Roaming/npm/claude.cmd`, clear `ANTHROPIC_API_KEY` and `CLAUDE_CODE_USE_BEDROCK` only for child process, `--setting-sources user`, `--permission-mode dontAsk`, and reviewer settings from the preserved evidence path. |
| F13 | Medium | Parallel subagent fan-out | The `task` tool is not concurrency-safe, so v5 cannot parallel-dispatch multiple subagents through the normal tool planner. | Runnable can run multiple agents in background or parallel patterns. v5 can show one subagent live, but real multi-agent fan-out is still effectively sequential. | Treat as part of the later subagent orchestration block, not the small prompt-truth fix. |
| F14 | Low-Medium | Child structured progress channel | Child subagent output reaches the UI through `output_fn` text prefixes. Structured tool generation/result callbacks are installed on the parent UI engine, not exposed as a clean child event stream. | Current UI works, but progress is still parsed from text for children. This makes future UI/task dashboards more brittle. | Fold into PUBLIC-PROGRESS-EVENTS: public callback/event bus should cover parent and child events. |

## Runnable Comparison Matrix

| Capability | Runnable Claude Code | v5 current | Comparable? | Notes |
|---|---|---|---|---|
| Tool deferral/search | `ToolSearchTool`, `shouldDefer`, lazy schemas. | `tool_search`, `should_defer`, `always_load`, visible/deferred split. | Mostly yes | Current visible tools: 10. Deferred: 15. This is a strong port. |
| Tool ordering/cache stability | Stable built-in/MCP ordering. | `tools/registry.py` sorts and deduplicates, built-ins win. | Mostly yes | Good cache-stability discipline. |
| Tool execution progress | Streaming tool execution and in-progress IDs. | UI callback + live output router. | Partial | Notebook UI now sees starts/results, but architecture is less first-class. |
| Parallel tool execution | Concurrent runner with max concurrency and progress state. | ThreadPool for safe calls, max 4, dedup/path conflict rules. | Partial | Mixed safe + sequential batches are conservative. |
| Subagents | Sync/async/background, named agents, SendMessage, foreground/background, remote/worktree options. | Sync child run, shared budget, allowed tools, build worktree, live UI updates, receipts. | Partial | Strong enough for current notebook tasks, not Runnable-level orchestration. |
| Agent memory | Scoped user/project/local memory plus snapshots. | Scoped memory prompt exists; parent has `memory.md`; session/recovery state exists. | Partial | v5 lacks the full snapshot/sync sophistication. |
| Task/request tracking | Structured task tools with status, owner, dependencies, output, stop, hooks. | `todo_write/read`, status doc, journal, subagent receipts. | No | This is the biggest product gap. |
| Plan mode | Plan and verify tools/modes. | Plan mode allowlist and plan subagent. | Partial | Good safety gating, but less integrated with task/request state. |
| Prompt/cache | Cache-aware prompt sections and token/cost tracker. | Static/dynamic boundary, Bedrock cache blocks, cache invariant freeze, token tracker. | Mostly yes | Needs better dynamic-tail cost control. |
| UI | Ink/React terminal UI with progress components. | ipywidgets HTML UI. | Different by constraint | v5 can be good, but should not chase exact Runnable UI internals. |

## Token And Cache Notes

Measured from local import:

| Metric | Current value |
|---|---:|
| System prompt chars | 14,748 |
| Static prompt chars | 12,081 |
| Dynamic prompt chars | 2,648 |
| Cache boundary count | 1 |
| Visible tool count | 10 |
| Deferred tool count | 15 |
| Visible schema chars | 18,123 |
| Deferred schema chars if loaded | 11,859 |

Interpretation for non-technical readers: v5 starts each request with a fairly large instruction packet and a visible toolbox. Caching means the stable part should get cheaper after the first call. The expensive part is when the model makes many calls, uses a large thinking budget, emits a lot of output, or keeps adding dynamic status/memory text that cannot be cached as well.

## Recommended Fix Blocks

| Priority | Block | Purpose | Files likely touched | Tests/review |
|---:|---|---|---|---|
| 1 | PATH-DOC-DRIFT | Make active tree unambiguous and remove stale `compact_v5/compact_v5/` / old `MAIN/agent` instructions where misleading. | Docs/status/evidence only, possibly rebuild script docs. | `rg` drift check plus Claude CLI review. |
| 2 | SUBAGENT-PROMPT-TRUTH | Update `task` tool description and subagent notes to match live visibility, supported agent types, and worktree behavior. | `compact_v5/tools/task.py`, `compact_v5/subagent/agent_types.py`, tests. | Grep lock for stale phrases; subagent smoke. |
| 3 | PUBLIC-PROGRESS-EVENTS | Expose tool/subagent progress events on `Agent` public API instead of UI mutating `_engine`. | `agent.py`, `ui/chat_ui.py`, tests. | UI smoke and callback unit test. |
| 4 | SUBAGENT-READONLY-SCOPE | Remove `todo_write` from read-only agents. | `subagent/agent_types.py`, todo tests. | Verify explore/review cannot mutate parent todo state. |
| 5 | REQUEST-TRACKING-V2 | Add structured task/request tracking closer to Runnable. | New `tools/task_state.py` or extend `tools/todo.py`, runtime state, UI. | Unit tests for IDs/status/evidence; long-task smoke. |
| 6 | TOKEN-DYNAMIC-BUDGET | Measure and reduce dynamic tail/status/memory cost. | `agent.py`, `runtime/state.py`, UI status metrics. | Mock runs with same prompt, Thinking ON/OFF, cache R/W assertions. |
| 7 | MIXED-PARALLEL-DISPATCH | Improve mixed read/write tool batch scheduling. | `core/query_engine.py`, `core/parallel_dispatch.py`. | Parallel dispatch tests with read/read/write mixed batch. |
| 8 | UI-HISTORY-SCALING | Keep long notebook sessions responsive. | `ui/chat_ui.py`. | HTML fixture screenshot plus large-history smoke. |

## Bottom Line

v5 should be fixed further, but the next fixes should not be random UI patching. The correct next phase is a small set of architecture cleanup blocks: remove stale prompts/docs, remove the read-only `todo_write` hole, expose progress events cleanly, add structured request tracking, then measure dynamic prompt and thinking cost. After that, v5 will be much closer to Runnable's supervision quality while preserving the notebook and Bedrock constraints.

## Claude CLI Review Addendum

Claude CLI was run through the subscription-auth path on 2026-05-11:

- Smoke check: `CLAUDE_REVIEWER_READY stdin_smoke`
- Review output: `compact_v5_test_evidence/final_results/v5_deep_scan_claude_review/V5_DEEP_SCAN_RUNNABLE_COMPARE_20260511_claude_review.md`
- Stderr: `compact_v5_test_evidence/final_results/v5_deep_scan_claude_review/V5_DEEP_SCAN_RUNNABLE_COMPARE_20260511_claude_review.err.log`
- Verdict: `APPROVE_WITH_FIXES`

Claude confirmed the report's findings and added four refinements:

| Claude ID | Severity | Added point |
|---|---|---|
| C1 | Medium | The stale `SUBAGENT_NOTES` line affects all seven subagent types, not only one role. |
| C2 | Low-Medium | `todo_write` in read-only agents persists to disk, so the mutation survives beyond the current process. |
| C3 | Medium | `task` is not concurrency-safe, so parallel subagent fan-out is effectively unavailable today. |
| C4 | Low | Child subagent progress uses text-prefix routing, not a clean structured child callback stream. |

Claude recommended moving `SUBAGENT-READONLY-SCOPE` before the larger `REQUEST-TRACKING-V2` block. This report now reflects that order.
