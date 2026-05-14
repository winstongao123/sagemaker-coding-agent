# v5 Evolution Plan — Sequenced Phases

**Last updated:** 2026-05-14

**Purpose:** Sequenced execution plan for evolving v5 past the current ship
zip. Tells you *what to do in what order* and *what gate to clear before
moving on*. Companion to:
- `V5_NEXT_BACKLOG.md` — Block catalog (the *what* and *why*).
- `V5_KNOWLEDGE_INDEX.md` — doc pickup map.
- `AGENT_STATUS.md` — current live status.

**Source-of-truth rule:** every phase references Block IDs from
`V5_NEXT_BACKLOG.md`. A Block lands → its status flips to LANDED there.

## Binding goal

> v5 must be **better than the combined four references (Runnable + Hermes +
> Learning_Factory + v4)** on every axis that is **in-scope for single-user
> coding-agent / long-running task / SageMaker notebook**.
>
> Intentional gaps (terminal Ink UI, plugin marketplace, MCP, messaging
> gateways, async-generator engine, cross-platform backends) stay gaps —
> these are recorded as SKIP-N entries in V5_NEXT_BACKLOG.md.

## Current state (baseline)

- `compact_v5_ship.zip` SHA `79d04c5d7162da04f4b1a9a1c20f80b2cc901571b7ea90681c8c48009ad99a6c`
- 66 local tests pass; Playwright widget-render verified.
- **19 confirmed v5 wins** across 9 Runnable rounds + 3 Hermes rounds.
- **2 backlog blocks LANDED** (B-06 one-strike, B-07 intent-drift guard).
- **1 PARTIALLY LANDED** (B-09 tool-result pruning across turns).
- **14 PROPOSED Tier-1 blocks** queued.
- Last commit on `origin/v5-build`: `4b56a7f` (V5_NEXT_BACKLOG.md added).
- ~23 uncommitted source files in working tree (Codex's prior WIP — not
  in any commit yet).

## Phase EVO-0 — Ship gate (real SageMaker test)

**Goal:** validate the current zip works in production SageMaker before
spending Tier-1 budget. No new code.

| Step | Action |
|---|---|
| 1 | Decide what to do with Codex's 23 uncommitted source files: either commit + push (and rebuild zip), or stash. Don't ship a zip whose source isn't in github. |
| 2 | Upload `compact_v5_ship.zip` (or freshly-rebuilt zip) to a real SageMaker domain. |
| 3 | Kernel restart → run Cells 1-2 → verify widget renders with no `model not found`. |
| 4 | Rerun Cell 2 → confirm refresh-after-edit story works. |
| 5 | Run 3 user prompts: one S3 read, one notes_cli-style coding task, one `ask_user` ambiguity. |
| 6 | Capture cost/cache/duration deltas; save evidence under `compact_v5_test_evidence/final_results/20260514_real_sagemaker_test/`. |

**Pass gate:**
- All 3 prompts complete without model-not-found, drift, or hang.
- Cost per turn within ±30% of mock-mode predictions.
- Subagent receipts written to `<workspace>/compact_v5_wip/docs/reviews/`.

**Fail gate:** open a regression issue, fix, **do not start Phase EVO-1
until EVO-0 passes**.

---

## Phase EVO-1 — Durability cluster

**Goal:** survive a hung tool + a kernel crash. The single biggest user
pain on long unattended runs.

**Blocks:** B-01, B-02, B-03

| Block | What | LOC | Source ref |
|---|---|---|---|
| B-01 | Process supervisor + inactivity timeout | ~120 | Hermes `cron/scheduler.py:988-1055` |
| B-02 | Auto-resume compression chains after kernel crash | ~80 | Hermes `hermes_state.py:757, 1042` |
| B-03 | Heartbeat during long retries | ~30 | Runnable `services/api/withRetry.ts:170-517` |

**Order within phase:** B-03 first (smallest, lowest risk), then B-01,
then B-02 (depends on B-01's activity tracker).

**Per-block discipline:**
1. Worker prompt → Codex/Claude review prompt → diff → tests → status doc.
2. Each block is its own commit on `v5-build`.
3. After all three: rebuild zip, update `compact_v5_ship.zip` SHA in
   `chat.md` + `AGENT_STATUS.md`.

**Ship gate (phase complete):**
- Mock-mode test: a 700-second `time.sleep` inside a tool is killed at 600s
  with diagnostic message naming the tool.
- Mock-mode test: simulated kernel restart resumes from `last_turn.json`
  after user confirms "resume previous session? Y/N".
- Mock-mode test: a 90-second Bedrock backoff emits 3 heartbeats in the
  chat output.
- Real Bedrock smoke (1 call, ~$0.05): verify heartbeat copy isn't
  intrusive.

**Estimated effort:** 1-2 days focused.

---

## Phase EVO-2 — Cost / cache optimisation cluster

**Goal:** direct $ reduction on every long task. Cache is the biggest
lever; v5 leaves savings on the table today.

**Blocks:** B-05, B-08, B-10

| Block | What | LOC | Source ref |
|---|---|---|---|
| B-05 | cache_control on tools + conversation prefix | ~30 | Runnable `services/api/claude.ts:603-663` |
| B-08 | Cache-break per-source state machine + diff file | ~150 | Runnable `services/api/promptCacheBreakDetection.ts:28-99` |
| B-10 | cache_edits microcompact (Bedrock parity check first) | ~300 | Runnable `services/compact/microCompact.ts:305-398` |

**Order within phase:** B-05 first (smallest, biggest direct savings).
Then B-08 (builds on existing cache-break primitives). Then B-10 *only
if* Bedrock supports `cache_edits` (otherwise DEFER and document the
block as blocked on Bedrock).

**Pre-flight gate:** before starting B-10, verify Bedrock API supports
`cache_edits` via a single test call. If it doesn't, mark B-10 DEFERRED
in V5_NEXT_BACKLOG.md and ship without it.

**Ship gate (phase complete):**
- Benchmark on a known 5-turn task: cache_read / total prefix ratio
  improves measurably (target: ≥1.5× over pre-EVO-2 baseline).
- Cache-break diff file appears in `compact_v5_wip/cache_breaks/` after
  a deliberate tool-list change.
- No regression in 66-pass test suite.

**Estimated effort:** 2-3 days focused (B-10 is the big one).

---

## Phase EVO-3 — Observability + small fixes

**Goal:** make cost and behaviour diagnosable. Low effort, high
value-per-line.

**Blocks:** B-04, B-11, B-15, B-18

| Block | What | LOC | Source ref |
|---|---|---|---|
| B-04 | Per-turn telemetry summary event in audit JSONL | ~50 | Runnable `cost-tracker.ts` + `costHook.ts` |
| B-11 | Plan-mode prompt suffix (≤300 tokens) | ~5 + prompt | Runnable `tools/EnterPlanModeTool/EnterPlanModeTool.ts:104-125` |
| B-15 | Local-data fallback search paths in system prompt | ~15 | Codex S3-transcript review |
| B-18 | Turn-level cancel on `ask_user` | ~15 | Hermes turn-scoped abort pattern |

**Order within phase:** parallelisable. B-11 + B-15 are prompt-only;
B-04 + B-18 are runtime.

**Ship gate (phase complete):**
- `compact_v5/runtime/audit.py` JSONL contains one structured summary
  line per `agent.run` invocation.
- Plan-mode turn includes the suffix; non-plan turn doesn't.
- "Local data" prompts no longer tour the v5 install tree; instead they
  list standard SageMaker data dirs.
- Clicking Stop during an active `ask_user` reliably cancels the prompt
  within ~1s.

**Estimated effort:** 1 day.

---

## Phase EVO-4 — Learning loops (manual-approval only)

**Goal:** self-improving over time, with **hard user constraint** that
nothing auto-applies. Hermes' detection trigger + v5's existing
propose-not-apply gate.

**Blocks:** B-12, B-13, B-14

| Block | What | LOC | Source ref |
|---|---|---|---|
| B-12 | Background skill *proposal* every N turns (default OFF) | ~150 | Hermes `run_agent.py:1706-1717, 9425-9450` |
| B-13 | Background memory *proposal* every N turns (default OFF) | ~80 | Hermes `run_agent.py:1589` + SESSION_REVIEW_PROMPT |
| B-14 | FTS5 cross-session search index + tool | ~250 | Hermes `tools/session_search_tool.py` + `hermes_state.py:1229-1396` |

**Order within phase:** B-14 first (independent, enables the other two
to query history). Then B-12 + B-13 in parallel.

**Hard constraints enforced in code:**
- Default `CONFIG.enable_skill_nudges = False`.
- Default `CONFIG.enable_memory_nudges = False`.
- Proposal files land in `.proposed/` and
  `compact_v5_wip/memory_proposals/` only.
- Chat notification on every proposal: `[skill proposal: review at
  .proposed/...]` style.
- User must explicitly run `/skill apply <name>` or `/memory accept` to
  merge. No exception.
- Review call uses Haiku, max_tokens capped, runs in background thread.

**Ship gate (phase complete):**
- 20-turn mock session generates exactly one proposal in `.proposed/`
  and exactly one chat notification, with **no write** to the live
  skills/memory tree.
- FTS5 search returns correct snippet for a known phrase across 3 mock
  sessions.

**Estimated effort:** 2-3 days.

---

## Phase EVO-5 — Resilience polish

**Goal:** handle the long-tail failure modes Tier-1 hasn't covered.

**Blocks:** B-17, B-09 cache-aware completion

| Block | What | LOC | Source ref |
|---|---|---|---|
| B-17 | Model fallback after N consecutive 529s | ~40 | Runnable `services/api/withRetry.ts:267-314` |
| B-09 (completion) | Cache-aware tool-result pruning across turns | ~20 | Runnable `services/compact/microCompact.ts:40-50` |

**Ship gate:**
- Simulated 529 storm (5 consecutive) triggers fallback to Haiku with
  user notification.
- Long-task simulation: per-turn token count plateaus rather than
  growing linearly (Tier-1 already partial; this completes it).

**Estimated effort:** 0.5-1 day.

---

## Phase EVO-6 — Tier 2 enhancements (optional)

Only if there's a concrete user pain point. None of these are required
for "v5 > combined-4 on in-scope axes".

**Blocks:** B-16 (per-tool cache-break diff), B-19 (permission receipts),
B-20 (final-task quality gate for complex coding), B-21 (persistent
runtime health log).

**Gate to enter:** EVO-0 through EVO-5 all passed; user identifies a
specific Tier-2 item as needed.

---

## Phase EVO-DEFER — explicitly not in plan

These stay PROPOSED-but-DEFERRED in `V5_NEXT_BACKLOG.md` unless
circumstances change:

- **B-22 cron scheduler** — only matters if you go AFK during long tasks.
  Defer until concrete use case.
- **B-23 RPC tool bridge** — clear ROI but tail-end.
- **B-24 batch trajectory generation** — research use case only.
- **B-25 Honcho user modeling** — multi-project benefit; defer.
- **B-26 output styles** — cosmetic.
- **B-27 5-event hooks contract** — defer unless customer asks.
- **B-28 image/notebook cohesion** — defer.
- **B-29 async-generator engine** — full rewrite; **DEFER indefinitely**
  unless the sync architecture becomes a measured blocker.

---

## Phase EVO-SKIP — intentional gaps (do not regress)

These are SKIP-N entries in `V5_NEXT_BACKLOG.md`. They stay skipped:

- SKIP-1 cross-platform terminal backends.
- SKIP-2 ACP server.
- SKIP-3 messaging gateways.
- SKIP-4 plugin marketplace.
- SKIP-5 MCP support (enforced by entry.py banned-subsystem guard).
- SKIP-6 LLM permission classifier.

Any future "make v5 more like Runnable / Hermes" pressure that points at
these should be rejected. Justifications are in V5_NEXT_BACKLOG.md.

---

## Ship discipline per phase

Every phase must produce:

1. **Worker prompt** in `compact_v5_test_evidence/final_results/<phase>/`.
2. **Per-block diff** (git diff for each block).
3. **Per-block Claude review prompt + output** in same folder.
4. **Per-block Codex review prompt + output** in same folder.
5. **Tests log** showing all current tests + new tests pass.
6. **Status doc** (5-line drift check + intended scope).
7. **Updated V5_NEXT_BACKLOG.md** with status flipped to LANDED + commit
   SHA recorded.
8. **SESSION_STATE.md entry**.
9. **Rebuilt `compact_v5_ship.zip`** + verify-zip evidence.
10. **Pushed to `origin/v5-build`** (per latest doc — `sageagent` remote
    is 404).

**Codex + Claude review gate:** both must return APPROVE before the next
block in the same phase starts. Re-review until clean.

**Test discipline:** mock-mode first; real Bedrock only at the per-phase
ship gate (≤$0.10 per phase real spend, capped).

## Honest effort estimate

| Phase | Blocks | Effort | Cumulative |
|---|---|---|---|
| EVO-0 | (ship gate) | 0.5 day | 0.5 day |
| EVO-1 | B-01, B-02, B-03 | 1-2 days | 2 days |
| EVO-2 | B-05, B-08, (B-10 if Bedrock supports) | 2-3 days | 5 days |
| EVO-3 | B-04, B-11, B-15, B-18 | 1 day | 6 days |
| EVO-4 | B-12, B-13, B-14 | 2-3 days | 9 days |
| EVO-5 | B-17, B-09 completion | 0.5-1 day | 10 days |

**~10 focused days** to land all Tier-1 + Tier-1.5 work. Each phase is
a self-contained ship event with its own review gate, so you can stop
at any phase and have a coherent ship.

## After EVO-5 — claim check

At that point v5 will:
- Survive hung tools (B-01) and kernel crashes (B-02).
- Tell you what's happening during waits (B-03, B-04).
- Cost materially less per turn on long tasks (B-05, B-08, B-10).
- Tell you when cache breaks and why (B-08).
- Self-detect patterns worth saving (B-12, B-13) without ever applying
  them automatically.
- Let you ask "what did we figure out about X last week?" (B-14).
- Survive Bedrock capacity dips (B-17).
- Plus the 19 existing v5 wins.

That's the realistic interpretation of "v5 > Runnable + Hermes + LF + v4
on in-scope axes." The intentional gaps stay gaps — that's a feature, not
a defect.

## What this plan does NOT do

- Does not promise v5 will surpass Runnable on terminal UI streaming
  (intentional gap).
- Does not promise v5 will match Hermes on multi-platform messaging
  (out of scope).
- Does not promise v5 will adopt plugins, MCP, or LLM-driven permission
  classification (these are deliberate v5 design choices and would
  regress v5's safety story).

## Maintenance protocol

- A phase completes → its row in this doc is checked off; affected
  Blocks in V5_NEXT_BACKLOG.md flip to LANDED + commit SHA.
- New scan findings → either add a Block to V5_NEXT_BACKLOG.md AND
  place it into an existing or new EVO phase here, or mark as
  defer/skip with rationale.
- This doc is the **single forward-execution-plan source**. Anything
  claiming "v5 will do X by Y" must point at a phase here.
