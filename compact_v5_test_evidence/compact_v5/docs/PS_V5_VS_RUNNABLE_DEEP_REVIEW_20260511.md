# v5 vs Runnable Claude Code — deep review on six axes

Date: 2026-05-11
Author: Claude (analysis only, no code changes)
Scope: tool layer, subagent coordination, memory/plan/status, token/cache, UI/streaming
Repos compared:
- v5 (target): `d:/Github/sagemaker-coding-agent/compact_v5/compact_v5/`
- Runnable (gold): `d:/Github/gg_claude_code/gg-claude-code-runnable/src/`

Companion docs:
- `PS_PS_FINAL_TEST_v3_RESULT.md` (v5 acceptance PASS)
- `PS_PS_FINAL_TEST_v3_UI_ISSUES.md` (UI gaps from real-use test)
- `PS_TEST_REVIEW_FINAL.md`, `CRITICAL_UI_PER_TURN_METRICS_GAP.md`

## TL;DR — where v5 stands vs Runnable

| Theme | Where v5 leads | Where Runnable leads |
|---|---|---|
| **Tool descriptions** | Tighter WHEN-NOT discipline | Dynamic per-context injection |
| **Tool dispatch** | — | Streaming executor + sibling abort |
| **Cache invariants** | — | Per-tool schema hash + diff recording |
| **Streaming UI** | Per-turn inline metrics | True per-token React/Ink streaming |
| **Subagent receipts** | docs/reviews/ + envelope persist | — |
| **Subagent kinds** | 7 typed + tool allowlists | 4 builtin + dynamic file-based |
| **Memory** | — | Multi-file memdir + auto-consolidate |
| **Plan mode** | — | Dynamic permission state + entry/exit tools |
| **Recovery** | Atomic local per-turn JSON | — |
| **Cache control** | — | Multi-marker + 1h TTL gating |
| **Microcompact** | — | cache_edits path preserves cache prefix |
| **System prompt** | Smaller, sectioned, budgeted | Larger, runtime-computed |

Net read: **v5 is engine-correct and well-instrumented but architecturally
synchronous**, while Runnable is **architecturally streaming-async with
multiple cache levers**. Most of v5's user-visible "stuck" feeling traces back
to that sync-vs-async divide, not to missing features.

---

## Axis 1 — Tool layer

### 1.1 WHEN-not-WHAT tool descriptions — gap MINOR

| Tool | v5 | Runnable |
|---|---|---|
| read_file | `tools/read_file.py:41-63` — 23 lines, explicit WHEN + WHEN-NOT | `tools/FileReadTool/prompt.ts:12-49` — ~40 lines, no WHEN-NOT |
| bash | `tools/bash.py:46-71` — 26 lines, tight allow/deny + WHEN/WHEN-NOT | `tools/BashTool/prompt.ts:1-250+` — ~300 LOC, dynamic per USER_TYPE |
| task | `tools/task.py:39-68` — static enum + clear "do NOT use" | `tools/AgentTool/prompt.ts:66-250+` — dynamic agent injection |

**Read:** v5 actually wins on directive clarity (tighter negative guidance).
Runnable trades clarity for runtime adaptability (it knows the connected MCP
servers + USER_TYPE at prompt-build time). Worth keeping the v5 style; do
not regress to Runnable verbosity.

### 1.2 Parallel tool dispatch — gap MAJOR

- **v5:** `core/parallel_dispatch.py:26-54` — `ThreadPoolExecutor` (4 workers),
  static `PARALLEL_SAFE_TOOLS` allowlist + `NEVER_PARALLEL_TOOLS` denylist.
  Tools execute in batch; `task` is forbidden in parallel.
- **Runnable:** `services/tools/StreamingToolExecutor.ts:40-150` — tools
  start as their tool_use blocks arrive in the response stream, concurrency
  decision per-input, **sibling abort** kills sister subprocesses when a
  bash tool errors (line 45-48). Results emitted in receive order
  (line 36-38).

**Implication for v5:** Runnable's executor is "live" — it can dispatch
read_file + glob + grep concurrently as the model emits them, before the
assistant turn finishes. v5 must wait for the full assistant message,
parse all tool_use blocks, then dispatch. This is part of why v5 feels less
responsive on multi-tool turns.

**Effort to close gap:** large architectural change (sync → async dispatch).
Not a quick win.

### 1.3 Tool-result offloading — gap MINOR

- **v5:** `core/query_engine.py:230-274` — head-truncate with `[... truncated ...]`,
  delegates persist to `runtime.results.persist_large_tool_results()`,
  silent on storage failure.
- **Runnable:** `utils/toolResultStorage.ts:55-203` — `getPersistenceThreshold()`
  with **GrowthBook per-tool override** (`tengu_satin_quoll`),
  preview-with-filepath message (`buildLargeToolResultMessage()`), `Infinity`
  opt-out per tool.

**Read:** functional parity; Runnable adds polish (preview + per-tool config)
that v5 doesn't strictly need for the SageMaker scope. Low priority.

### 1.4 Cache invariants on tool list — gap MAJOR

- **v5:** `core/query_engine.py:1931-1968` — `_enforce_prompt_cache_invariants()`
  freezes `(model_id, system_prompt_hash, tool_names_tuple)` at session start.
  Binary: any toolset change defers + warning. No per-tool detail.
- **Runnable:** `services/api/promptCacheBreakDetection.ts:28-68` —
  `PreviousState` tracks `systemHash`, `toolsHash`, `perToolHashes`,
  `cacheControlHash`, model, betas. Detects **which tool's schema changed**
  (per-tool diff). Cache-break diffs saved to
  `cache-break-${suffix}.diff` for debugging.

**Implication for v5:** when v5 invalidates cache, you have no idea why. A
single tool description tweak silently kills the prefix. Runnable would tell
you exactly which tool changed and by how much.

**Effort to close gap:** medium. Adding per-tool hashing + a diff log on top
of the existing freeze is well-scoped. Worth doing.

### 1.5 Tool gen callback / streaming visibility — gap MAJOR

- **v5:** `core/query_engine.py:337-388, 1882-1925` — sync callback fires
  `"tool_generation"` (when tool_use blocks arrive in response) and
  `"tool_result"` (after execution). Two event types only.
  **Not currently wired from `agent.py:139-145` to the UI** — UI cannot
  subscribe today.
- **Runnable:** `query.ts:337+` — async generator yields `Message` objects
  incrementally; UI subscribes with `for await`. Tool progress streams
  through the same channel as assistant text.

**Implication for v5:** even after fixing the chat_ui live-stream gap
(see `PS_PS_FINAL_TEST_v3_UI_ISSUES.md` Problem 4), v5's "tool starting"
and "tool finished" visibility hinges on a manually plumbed callback.
Runnable gets it free from the architecture.

**Effort to close gap:** small if you only want the UI hook (just expose
`tool_gen_callback` through `Agent.__init__`); large if you want true
async-generator parity.

---

## Axis 2 — Subagent coordination

### 2.1 Agent kinds taxonomy — gap MAJOR (v5 leads)

- **v5:** `subagent/agent_types.py:88-178` — 7 typed agents
  (general/explore/plan/verify/build/review/fork) with dataclass config
  (system_suffix, max_turns, one_shot, allowed_tools, memory_scope,
  needs_worktree). `tools/task.py:84` enum-validates the subagent_type.
- **Runnable:** `tools/AgentTool/loadAgentsDir.ts` — file-based with
  YAML/frontmatter loading, 4 hardcoded built-ins
  (explore, plan, verification, generalPurpose), no allowlist enforcement
  at schema, fork synthesised in `forkSubagent.ts:60-71`.

**Read:** v5 is **stronger** here. Tool allowlists per agent type +
typed config is the right insurance for an enterprise SageMaker context.
Don't regress to Runnable's looser model.

### 2.2 Output streaming up to parent — gap MAJOR

- **v5:** `subagent/spawn.py:535` — `child.run(... output_fn=output_fn)`
  passes the parent's callback into the child engine synchronously.
  Parent UI receives string lines one by one. Today these lines are
  **buffered** in chat_ui (the `_run_message` list-append).
- **Runnable:** `runAgent.ts:560-583` — child returns
  `AsyncGenerator<Message, void>`; every `Message` yielded before
  child completes. Parent UI does `for await` on the generator,
  rendering tool calls and assistant chunks as they arrive.

**Implication for v5:** the architecture *is* capable of forwarding
child activity — the gap is in the chat_ui.py consumer (Problem 4 in
the UI issues doc). One UI fix unlocks live subagent visibility for
free.

### 2.3 Receipts / artifact persistence — gap MAJOR (v5 leads)

- **v5:** `tools/task.py:106-196` — every subagent run writes
  `_subagent_receipt_markdown()` to **three locations**:
  `.sageagent_state/subagents/{ts}-{kind}-{child}.md`,
  `docs/reviews/{same}.md`, `docs/logs/subagent_artifacts.log`.
  Receipt includes envelope (tokens, cost, duration) + prompt preview.
- **Runnable:** transcripts in `.claude/session-store/agents/`
  (via `writeAgentMetadata()` in runAgent.ts:66) but **no structured
  receipt markdown** for team-visible review evidence.

**Read:** v5 wins. The PS_PS acceptance test relied on these receipts;
Runnable's session cache wouldn't have satisfied that contract. Keep
v5's pattern.

### 2.4 Memory handoff parent ↔ child — gap MINOR

Both repos use the same scope model (user / project / local) and the
same `.claude/agent-memory/{scope}/{agent_type}/MEMORY.md` path
pattern (v5 `subagent/agent_memory.py:41-65, 107-161` ↔ Runnable
`tools/AgentTool/agentMemory.ts:52-65, 109-114, 138-150+`).

Difference: v5 child reads memory only; Runnable child can also write
(via file tools). Negligible practical gap.

### 2.5 Parallel subagent spawn — gap MINOR

- **v5:** task forbidden in parallel batch (`NEVER_PARALLEL_TOOLS`).
  Max 1 task per turn.
- **Runnable:** Fork tasks run async/background, so multiple forks
  *can* overlap; non-fork agents still serial per turn.

Both block true parallel sub-agent dispatch from a single turn for
non-fork kinds. Low priority.

### 2.6 Stop propagation parent → child — gap NONE

- **v5:** `subagent/spawn.py:222` shares `on_stop_check` (combined
  callback in `agent.py:132-137`).
- **Runnable:** parent's `AbortController` passed into child context
  (`runAgent.ts:706, 524-528, 613`).

Different idioms, same effect.

---

## Axis 3 — Memory + plan + status

### 3.1 Memory architecture — gap MAJOR

- **v5:** `runtime/state.py:127-128` reads single `memory.md` (12 KB cap).
  4 types (user/feedback/project/reference) inline. `runtime/dream.py:1-150`
  consolidation runs **only on manual `/dream`**. No daemon, no
  auto-trigger.
- **Runnable:** `memdir/memdir.ts:34-38` — multi-file `memdir/` with
  topic subdirs; entrypoint `MEMORY.md` + 25 KB cap; consolidation in
  `services/autoDream/autoDream.ts:122-156` runs **automatically** on
  time + session gates (minHours=24, minSessions=5, GrowthBook-tunable),
  forks a subagent.

**Implication for v5:** v5 memory grows linearly until a human types
`/dream`. On long projects this is a UX papercut. The auto-trigger logic
is small (~150 LOC) and worth porting if you want the long-task story
to scale.

### 3.2 AGENT_STATUS.md handoff — gap MINOR

- **v5:** `agent.py:32-57, 172-184` reads `AGENT_STATUS.md` from
  workspace root each top-level run; appended to system prompt tail
  after `CACHE_BOUNDARY` (lines 190-197). Local file, durable across
  process restart.
- **Runnable:** no equivalent on-disk handoff doc. Uses CCR (Anthropic's
  remote event log) via `assistant/sessionHistory.ts:1-87`.

**Read:** different bets. v5 is offline-resilient; Runnable assumes
service connectivity. v5's choice fits SageMaker (intermittent
network ok). Keep it.

### 3.3 Todo system — gap MINOR (v5 leads on durability)

- **v5:** `tools/todo.py:14-91` + `runtime/state.py:130-151` — atomic
  disk writes to `.sageagent_state/todos.json`. Survives kernel restart.
- **Runnable V1:** `tools/TodoWriteTool/TodoWriteTool.ts:31-115` —
  in-memory `appState.todos[todoKey]` only. Lost on exit.
- **Runnable V2:** `TaskCreateTool/TaskUpdateTool/TaskListTool` (gated by
  `isTodoV2Enabled()`) — disk-backed.

V2 closes the gap; on V1 v5 is plainly more robust.

### 3.4 Plan mode — gap MAJOR

- **v5:** `tools/registry.py:46-50` — `PLAN_MODE_ALLOWED_TOOLS` is a
  frozen set checked at dispatch in `core/query_engine.py:1286-1308`.
  Binary block. **No prompt guidance** to the model after entering plan
  mode.
- **Runnable:** `tools/EnterPlanModeTool/EnterPlanModeTool.ts:36-126`
  flips `appState.toolPermissionContext.mode = 'plan'` at runtime,
  injects mode-specific instructions (interview vs legacy), uses a
  classifier rather than a static set, has explicit Exit tool.

**Implication for v5:** the plan-mode model in v5 is "you tried a
write tool and got rejected" — no in-prompt nudge to plan first.
Runnable tells the model directly. Adding a small `PLAN_MODE_PROMPT`
suffix when plan_mode is set (matching v4's pattern) is a 5-line
improvement.

### 3.5 Recovery — gap MAJOR (v5 leads)

- **v5:** `agent.py:244-264` + `runtime/state.py:168-189` — atomic
  per-turn `last_turn.json` snapshot (messages, todos, tokens, status,
  result) + JSONL `turn_journal.jsonl` (append-only). Local crash
  recovery works without network.
- **Runnable:** no per-turn local checkpoint. Recovery means
  `sessionHistory.fetchLatestEvents()` against CCR.

**Read:** v5 wins. Keep it. This is the kind of differentiator that
matters for "long-running coding/research/review workflow" the
acceptance benchmark exercised.

### 3.6 Skills + self-improvement — gap MINOR

- **v5:** 10 shipped skills in `skills/`, opt-in self-patching surface
  (`skills/manager.py:13-14` `propose_patch()`, gated on
  `CONFIG.enable_skill_patching=True`).
- **Runnable:** ~14-19 bundled skills (batch, claudeApi, debug, dream,
  hunter, keybindings, loop, remember, schedule-remote-agents, simplify,
  skillify, stuck, updateConfig, verify), tool-invokable `skillify` for
  generating new skills, auto-dream consolidation.

**Read:** Runnable has more skills out of the box; v5 has the safer
self-patching gate. Different bets, both reasonable.

---

## Axis 4 — Token consumption + caching

### 4.1 Cache control breakpoints — gap MAJOR

- **v5:** `core/cache.py:44-88` — splits on `CACHE_BOUNDARY_MARKER`,
  attaches `cache_control: {"type": "ephemeral"}` to **system prompt
  only**. No tool-level marker. No conversation-prefix marker. No TTL.
- **Runnable:** `services/api/claude.ts:358-374, 393-421, 603, 615,
  648, 663` — `getCacheControl()` returns
  `{type:"ephemeral", ttl?:"1h", scope?:"global"}`; markers placed on
  **system prompt + tool schemas + conversation prefix** (3+ breakpoints
  per turn); 1h TTL gated by `should1hCacheTTL()` + GrowthBook per
  `querySource`.

**Implication for v5:** v5 is leaving cache savings on the table.
Adding cache_control to the tool schemas (one extra marker) and to the
conversation prefix (after stable tool_use/tool_result blocks) is a
small, high-ROI change. The PS_PS_FINAL_TEST_v3 numbers
(804k read / 217k write) suggest cache *is* working — but more
breakpoints means longer cache survival across compactions.

### 4.2 Microcompact — gap MAJOR

- **v5:** `core/compactor.py:503-630` — reactive at 70% threshold,
  prunes oversized tool results **in-place**. Mutates messages →
  invalidates cache prefix. No cache-aware path.
- **Runnable:** `services/compact/microCompact.ts:253-293` — two paths:
  - **Time-based** (lines 402-517): trims when assistant gap exceeds a
    GrowthBook threshold.
  - **Cached path** (lines 305-398): queues `cache_edits` instead of
    mutating messages — preserves the cache prefix.

**Implication for v5:** every microcompact in v5 also pays the full
re-cache cost on the next call. Runnable can prune without breaking
the prefix because Anthropic accepts `cache_edits` server-side. This
is the single largest cost-saving lever Runnable has that v5 lacks.

**Effort to close gap:** medium. Requires confirming Bedrock's
`cache_edits` support (Anthropic API has it; Bedrock parity needs
verification) and a new microcompact path that emits edits rather than
mutating arrays.

### 4.3 Pre-send compact — gap NONE

Both fire microcompact in the pre-call hook. v4's
`do_pre_send_compact()` is preserved in spirit by v5's compactor
trigger inside `query_engine.run`. No gap.

### 4.4 Tool-result pruning — gap MINOR

- **v5:** `core/compactor.py` `prune_tool_outputs()` truncates in place,
  preserves first + last, no cache awareness.
- **Runnable:** `services/compact/microCompact.ts:40-50, 313-330` —
  explicit `COMPACTABLE_TOOLS` allowlist, deletes content (not block,
  preserving tool_use_id), queues `cache_edits`.

Functional parity, Runnable cleaner. Couple to 4.2 above.

### 4.5 System prompt size — gap MINOR (v5 leads)

- **v5:** `prompt/sections.py:76-101` — 19 sections, each token-budgeted.
  `STATIC_TOKEN_BUDGET = 2900`, actual ~2740. Disciplined.
- **Runnable:** `constants/prompts.ts` — single 914-line monolithic file
  + runtime-computed sections (output style, MCP, USER_TYPE).
  Estimated ~3500-4500 tokens.

**Read:** v5 is leaner and more cache-friendly. Don't regress to
Runnable's monolithic style.

### 4.6 Live streaming — gap MAJOR

- **v5:** `ui/chat_ui.py:1239` `output_fn=lambda s: ...` — see
  `PS_PS_FINAL_TEST_v3_UI_ISSUES.md` Problem 4. The router exists but
  buffers + re-renders per chunk without per-token granularity.
- **Runnable:** `screens/REPL.tsx:838-864` — true per-token React/Ink
  streaming via `streamingToolUses`, `streamingThinking`, `streamMode`
  state. State changes trigger React re-render → Ink CLI updates live.

**Implication for v5:** Jupyter ipywidgets cannot literally do
"per-token" streaming the way Ink can — but v5 is doing **less than the
ipywidgets API allows**. Updating `widgets.HTML.value` per chunk is
already standard in v4 and works fine. The gap is implementation
laziness, not platform limit.

### 4.7 Per-turn metrics — gap MAJOR (v5 leads)

- **v5:** `ui/chat_ui.py:936-970` `_render_turn_meta()` — per-assistant
  turn shows input/output/cache R-W/cost/calls/reasoning state inline.
- **Runnable:** `costHook.ts:6-22` `useCostSummary()` — only logs at
  `process.exit`. **No per-turn inline metrics.**

**Read:** v5 is the gold standard here. Don't regress.

---

## Axis 5 — UI / streaming integration

(See `PS_PS_FINAL_TEST_v3_UI_ISSUES.md` for the full UI gap list.
Cross-references with this review:)

| UI issue | Architectural root |
|---|---|
| Looks "stuck" during run | Sync callback batching (axis 1.5 + 2.2) |
| Pure-md / no formatting | Missing tool/thinking roles in `_render_chat` |
| Metrics one column | CSS-only; not architectural |
| No subagent visibility | Sync child output_fn forwarding works; UI side fix only |
| Cooperative Stop unclear | Stop semantics correct; UI wording missing |

The UI work is **almost entirely UI-layer**, with one engine touch
(`tool_gen_callback` plumbing through `Agent.__init__`).

---

## Recommendations (ranked by ROI / effort)

### Tier 1 — high ROI, low effort (do this quarter)
1. **Wire `tool_gen_callback` through `Agent.__init__`** so the UI can
   render "Tool starting…" pills (axis 1.5).
2. **Add cache_control to tool schemas + conversation prefix** in
   `core/cache.py` (axis 4.1) — 30 LOC, immediate Bedrock cost win.
3. **Restore plan-mode prompt suffix** in `agent.py` when plan_mode is
   on (axis 3.4) — 5 LOC, raises model compliance.
4. **Per-tool cache-break diff log** in `_enforce_prompt_cache_invariants`
   (axis 1.4) — 50 LOC, dramatically improves cache debug story.
5. **Auto-dream gate** ported from Runnable's `autoDream.ts:122-156`
   (axis 3.1) — ~150 LOC, scales the long-task story.

### Tier 2 — medium ROI, medium effort
6. **`cache_edits` microcompact path** (axis 4.2) — needs Bedrock
   `cache_edits` support verification first; ~300 LOC if supported.
7. **UI live-stream router** as documented in
   `PS_PS_FINAL_TEST_v3_UI_ISSUES.md` (Problems 3 + 4) — ~60 LOC, fixes
   the "stuck" perception entirely.
8. **Streaming tool result preview** (axis 1.3) — Runnable's
   `buildLargeToolResultMessage` pattern with file path + preview.

### Tier 3 — large refactor, defer or skip
9. **Async-generator engine** (axes 1.2, 1.5, 2.2) — fundamental
   architectural change. The single highest impact item, but turns v5
   into a different codebase. Recommend deferring until there's a
   concrete user-visible motive beyond "matches Runnable."
10. **Streaming tool dispatcher with sibling abort** (axis 1.2) —
    blocked on item 9.

### Do NOT regress
- v5's tighter WHEN-NOT tool descriptions (axis 1.1).
- v5's typed subagent kinds + tool allowlists (axis 2.1).
- v5's `docs/reviews/` receipt persistence (axis 2.3).
- v5's atomic per-turn local recovery (axis 3.5).
- v5's smaller, sectioned, budgeted system prompt (axis 4.5).
- v5's per-turn inline metrics (axis 4.7) — Runnable is *worse* here.

---

## Net assessment

v5 already meets or exceeds Runnable on **6 of 28 sub-axes** measured
(receipts, recovery, todos durability, system prompt discipline,
per-turn metrics, sub-agent allowlists). It is at parity on **5
sub-axes** (stop propagation, tool offloading, pre-send compact, tool
descriptions, memory scope model). The remaining **17 sub-axes** are
either "Runnable better but small" (10 minor) or "Runnable better and
big" (7 major).

The seven MAJOR gaps cluster into three families:

1. **Streaming architecture** (axes 1.2, 1.5, 2.2, 4.6) — sync
   callback vs async generator. Largest impact, largest cost. Tier 3.
2. **Cache strategy** (axes 1.4, 4.1, 4.2) — multiple breakpoints,
   per-tool diff, cache-aware microcompact. High impact, medium cost.
   Tier 1-2.
3. **Memory + plan UX** (axes 3.1, 3.4) — auto-consolidation, plan-mode
   guidance. Medium impact, low cost. Tier 1.

Recommend doing **Tier 1 + the UI streaming router** before any
further engine work. That closes most of the *visible* gap with
~300 LOC of careful changes and zero engine refactor. The async-generator
question can wait until there's a real user demand the current
architecture cannot serve.
