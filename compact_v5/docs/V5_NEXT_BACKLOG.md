# v5 Next Backlog — Block Catalogue

**Last updated:** 2026-05-14

**Purpose:** This is the **forward-looking** backlog doc for v5. Every adoption
item from the Runnable Claude Code (9 rounds) and Hermes Agent (3 rounds)
deep scans lives here as a numbered Block. Each Block cites where to learn
from (file:line in both repos) and where it lands in v5.

**Companion docs (historical only):**
- `compact_v5_test_evidence/full_v5_development_history/compact_v5/docs/V5_PLAN.md` — original v5 build phases (Phases 0-11).
- `compact_v5_test_evidence/deep_scans/compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` — append-only history of patterns already adopted.
- `compact_v5_test_evidence/final_results/20260513_runnable_additional_deep_scan.md` — Runnable rounds 4-9 findings.
- `compact_v5_test_evidence/final_results/20260514_hermes_deep_scan.md` — Hermes rounds H1-H3 findings.

## User profile that shapes priorities

This backlog is filtered for **single-user coding agent, long-running task
(hours-to-days), token + tool cost-sensitive, SageMaker notebook**. Items
that only matter for multi-user, multi-platform, or research/RL use cases
are explicitly marked LOWER priority or deferred.

## Hard user constraints (apply to every Block)

- **Never auto-create or auto-apply skills.** v5's existing propose-not-apply
  gate (`compact_v5/tools/skill_propose_patch.py:33-51`) is the correct
  architecture. The lesson from Hermes is the **detection trigger**, not
  the auto-execution. Every Hermes "background nudge" Block in this doc
  ends with a proposal file in `.proposed/<timestamp>.md` plus a chat
  notification — never a write to a live skill.
- **Never spend tokens without user-visible value.** Every nudge / heartbeat /
  diagnostic must have a clear cost-vs-savings story.
- **Manual user control surfaces** for anything that fires on a schedule.
  Default OFF unless explicitly enabled.
- **No new external dependencies** unless a Block explicitly notes one
  and the value justifies it.

## Block status legend

- `PROPOSED` — in this doc; not started.
- `IN PROGRESS` — under active work in a feature branch.
- `LANDED` — merged + tested + zip rebuilt.
- `DEFERRED` — kept in doc for future, not actively planned.
- `SKIP` — intentionally not adopted; rationale documented.

---

# Tier 1 — must-have for single-user long-running coding

These are the architectural baseline. Without them, hours-to-days tasks
break, hang, lose work, or burn budget invisibly.

## B-01 — Process supervision + inactivity timeout
- **Priority:** P0
- **Effort:** S (~120 LOC)
- **Status:** PROPOSED
- **Source — Hermes:** `cron/scheduler.py:988-1055` — polls
  `agent.get_activity_summary()` every 5s, kills if idle > 600s, logs last
  activity for diagnostics.
- **Source — Runnable:** N/A (different architecture).
- **v5 target:** new `compact_v5/runtime/supervisor.py` invoked by
  `compact_v5/agent.py:run`, configurable via
  `CONFIG.inactivity_timeout_seconds` (default 600).
- **Value (plain English):** If a tool hangs waiting on network, v5 today
  can sit silent for hours. This kills it after 10 min and logs which tool
  was last active. Big win for unattended overnight runs.
- **User constraint:** None. Always on; configurable timeout.
- **Acceptance:** mock-mode test that a `time.sleep(700)` inside a tool is
  killed at 600s with diagnostic message.

## B-02 — Auto-resume compression chains after kernel crash
- **Priority:** P0
- **Effort:** S (~80 LOC)
- **Status:** PROPOSED
- **Source — Hermes:** `hermes_state.py:757` (`get_compression_tip`) +
  `:1042` (`resolve_resume_session_id`). `parent_session_id` links
  compressed sessions to their successors; auto-resume on gateway restart.
- **Source — Runnable:** N/A (uses CCR remote event log).
- **v5 target:** extend `compact_v5/runtime/state.py:save_turn_recovery`
  with `parent_session_id`; add auto-load path in
  `compact_v5/agent.py:run` on first call.
- **Value:** After a kernel crash at hour 4 of an 8-hour task, v5 picks up
  from the last saved turn. Today v5 writes the data but doesn't auto-load
  it; user must manually re-stage context.
- **User constraint:** Auto-load asks user "resume previous session? Y/N"
  on first turn rather than silently re-injecting — gives the human
  control before tokens are spent.
- **Acceptance:** integration test that simulates kernel restart and
  verifies prompt + tokens diff is bounded.

## B-03 — Heartbeat during long retries
- **Priority:** P1
- **Effort:** S (~30 LOC)
- **Status:** PROPOSED
- **Source — Runnable:** `src/services/api/withRetry.ts:170-517` (async
  generator yields `SystemAPIErrorMessage` heartbeat every 30s during
  long waits).
- **Source — Hermes:** N/A.
- **v5 target:** add `heartbeat_callback` parameter to
  `compact_v5/core/retry.py:run_with_backoff`; wire through Bedrock client
  to emit `[retry: still waiting 30s]` style updates through the existing
  UI router.
- **Value:** When Bedrock 429/529 happens, v5 sits silent for 60s+ backoffs
  and the chat looks frozen. User kills it and wastes more budget. A
  visible heartbeat every 30s prevents premature aborts.
- **User constraint:** Heartbeat text should be terse — "waiting Ns for
  retry…" — not verbose explanations.
- **Acceptance:** mock-mode test that a 90s sleep emits 3 heartbeats.

## B-04 — Per-turn telemetry summary event
- **Priority:** P1
- **Effort:** S (~50 LOC)
- **Status:** PROPOSED
- **Source — Runnable:** `src/cost-tracker.ts` + `src/costHook.ts` — fires
  post-message, captures model/in-tokens/out-tokens/cost-deltas/stop-reason.
- **Source — Hermes:** N/A (uses SQLite state metadata).
- **v5 target:** append one JSONL line per turn into
  `compact_v5/runtime/audit.py` JSONL trail with `{turn, in, out, cache_r,
  cache_w, cost, retry_count, blocked_tool_attempts, stop_reason}`. Gated
  by `CONFIG.telemetry_events_enabled` (default ON locally; doesn't
  exfiltrate).
- **Value:** Today you can't easily ask "which turn wasted the most money?"
  without re-reading transcripts. One structured line per turn makes
  cost regressions diagnosable.
- **User constraint:** Local-only sink (audit.jsonl). No external
  telemetry pipeline. No Datadog/Statsig integration.
- **Acceptance:** test that audit.jsonl contains one summary line per
  `agent.run` invocation.

## B-05 — Cache_control on tools + conversation prefix
- **Priority:** P1
- **Effort:** S (~30 LOC)
- **Status:** PROPOSED
- **Source — Runnable:** `services/api/claude.ts:603,615,648,663` — places
  cache_control markers on system + tools + conversation prefix
  (3+ breakpoints per turn).
- **Source — Hermes:** N/A.
- **v5 target:** extend `compact_v5/core/cache.py:44-88` to mark tool list
  + the cache-stable conversation prefix in addition to the existing
  system-prompt marker. Verify Bedrock parity for multi-marker requests.
- **Value:** Direct cost reduction. v5 today marks only 1 breakpoint;
  Runnable marks 3+. More cache reuse = lower per-turn cost across long
  tasks.
- **User constraint:** Verify Bedrock accepts multi-marker requests on
  Haiku 4.5 and Sonnet 4.5 before shipping (Anthropic API supports it; need
  Bedrock confirmation).
- **Acceptance:** integration test that cache_read tokens / total prefix
  tokens ratio improves measurably on a 5-turn task.

## B-06 — One-strike rule on blocked tools
- **Priority:** P0
- **Effort:** XS (~5 LOC)
- **Status:** LANDED (S3 follow-up, 2026-05-12)
- **Source — Runnable:** N/A (Runnable uses dynamic classifier).
- **Source — Hermes:** N/A.
- **v5 target:** prompt-level rule in `compact_v5/prompt/security.md`
  already added: "If a tool returns 'Blocked' / 'not allowed', do NOT
  retry the same shape; pick a different tool or stop."
- **Value:** Prevents retry chains (e.g., `aws s3 ls` blocked → retry
  same → re-blocked) that waste 3-5 calls per blocked intent.
- **User constraint:** Already shipped.
- **Acceptance:** S3 follow-up regression tests cover this.

## B-07 — Intent-drift guard at final-claim
- **Priority:** P0
- **Effort:** S
- **Status:** LANDED (S3 follow-up, 2026-05-12)
- **Source — Runnable:** N/A.
- **Source — Hermes:** N/A.
- **v5 target:** `compact_v5/runtime/gate.py` already enforces
  evidence/intent alignment before final-claim.
- **Value:** Long tasks drift; the guard catches it.
- **Acceptance:** S3 intent-drift regression test.

## B-08 — Cache-break per-source state machine + diff file
- **Priority:** P1
- **Effort:** M (~150 LOC, primitives already exist)
- **Status:** PROPOSED
- **Source — Runnable:** `services/api/promptCacheBreakDetection.ts:28-99`
  — per-source `PreviousState` (max 10), captures system/tools/per-tool
  hashes + cache-control hash + betas + model + fast-mode + autoMode; on
  break generates structured diff and writes to `getCacheBreakDiffPath()`.
- **Source — Hermes:** N/A.
- **v5 target:** add per-source dict + `detect_cache_break(prev, curr)`
  on top of existing `compact_v5/core/cache_break_detection.py` snapshot
  primitives. Write diff to `<workspace>/compact_v5_wip/cache_breaks/`.
- **Value:** Silent cache breaks = budget cliff. Without this, you see the
  cost jump but don't know which prompt change caused it.
- **User constraint:** Diff path written under `compact_v5_wip/` (per
  CLAUDE.md evidence layout rule), never inside the v5 runtime tree.
- **Acceptance:** test that a deliberate tool-list change produces a diff
  file with the changed tool's hash.

## B-09 — Tool-result pruning across turns
- **Priority:** P1
- **Effort:** S
- **Status:** PARTIALLY LANDED
- **Source — Runnable:** `services/compact/microCompact.ts:40-50,313-330`
  — explicit `COMPACTABLE_TOOLS` allowlist, deletes content, queues
  `cache_edits`.
- **Source — Hermes:** N/A.
- **v5 target:** `compact_v5/core/compactor.py` already prunes; backlog
  is the cache-aware `cache_edits` path (see B-10).
- **Value:** Bounded per-turn cost on long tasks. Without this, every
  turn re-pays the full tool-result history.
- **Acceptance:** existing prune tests + new long-task test that asserts
  per-turn token count plateaus rather than growing linearly.

## B-10 — cache_edits microcompact path (cache-prefix preservation)
- **Priority:** P1
- **Effort:** M-L (~300 LOC)
- **Status:** PROPOSED (Bedrock support verification needed first)
- **Source — Runnable:** `services/compact/microCompact.ts:305-398`
  — cache-edits path queues server-side deletions instead of mutating
  messages.
- **Source — Hermes:** N/A.
- **v5 target:** new path in `compact_v5/core/compactor.py` that emits
  cache_edits when supported. Falls back to current in-place mutation
  otherwise.
- **Value:** When v5 trims old tool results to save context, it accidentally
  breaks the cache prefix → next call costs extra. Anthropic's `cache_edits`
  API trims without breaking. Big saving on long tasks.
- **User constraint:** Verify Bedrock supports cache_edits before shipping;
  if not, this becomes DEFERRED.
- **Acceptance:** real Bedrock test showing prune doesn't invalidate cache.

## B-11 — Plan-mode prompt suffix
- **Priority:** P1
- **Effort:** XS (~5 LOC)
- **Status:** PROPOSED
- **Source — Runnable:** `tools/EnterPlanModeTool/EnterPlanModeTool.ts:104-125`
  — interview-phase mode injection on plan-mode entry.
- **Source — Hermes:** N/A.
- **v5 target:** append a small `PLAN_MODE_PROMPT` suffix to system prompt
  in `compact_v5/agent.py:run` when `plan_mode=True`, replacing/augmenting
  the current pure-allowlist enforcement at
  `compact_v5/core/query_engine.py:1286-1308`.
- **Value:** v5 today only blocks write tools at dispatch — no in-prompt
  guidance to the model to plan-first. Better model compliance per turn.
- **User constraint:** Suffix must be ≤300 tokens to keep cache prefix
  stable for the common case.
- **Acceptance:** test that plan-mode turn includes the suffix; non-plan
  turn doesn't.

## B-12 — Background skill *proposal* every N turns (manual approval)
- **Priority:** P1
- **Effort:** M (~150 LOC)
- **Status:** PROPOSED
- **Source — Hermes:** `run_agent.py:1706-1717` + `:9425-9450`
  (SKILLS_REVIEW_PROMPT); default interval 10 turns; fire-and-forget
  thread post-response.
- **Source — Runnable:** N/A (Runnable's `runSkillGenerator.ts` is stubbed).
- **v5 target:** counter `_iters_since_skill_review` on `compact_v5/agent.py`;
  every N turns spawn a small review (cheapest model, Haiku) that asks
  *"is anything from the last N turns worth saving as a skill?"*; if yes,
  call v5's existing `compact_v5/tools/skill_propose_patch.py:propose`
  which writes to `.proposed/<timestamp>.md` and **emits a chat-visible
  notification** like `[skill proposal: review at .proposed/...]`. Default
  interval N=20. Disabled unless `CONFIG.enable_skill_nudges=True`.
- **Value:** Agent silently *detects* useful patterns over a long task.
- **User constraint (HARD):**
  - **Never auto-apply.** Proposal lands in `.proposed/` only.
  - **Always notify in chat + file.** User must explicitly run
    `/skill apply <name>` to merge.
  - **Default OFF** in CONFIG.
  - **Bounded cost:** review call uses Haiku, max_tokens capped, runs in
    a background thread that doesn't block the foreground.
- **Acceptance:** test that 20-turn mock session generates exactly one
  proposal in `.proposed/` and exactly one chat notification, with no
  write to the live skills tree.

## B-13 — Background memory *proposal* every N turns (manual approval)
- **Priority:** P1
- **Effort:** S (~80 LOC)
- **Status:** PROPOSED
- **Source — Hermes:** `run_agent.py:1589` (`memory_nudge_interval=10`)
  + `SESSION_REVIEW_PROMPT` template.
- **Source — Runnable:** N/A.
- **v5 target:** same counter pattern as B-12; review fact-extraction
  proposed-not-applied; lands in `<workspace>/compact_v5_wip/memory_proposals/`
  with chat notification. Uses existing
  `compact_v5/runtime/dream.py:1-150` consolidation engine but only on
  user accept.
- **Value:** Stops re-explaining the same thing every session. Captures
  "user is on Windows, prefers TypeScript, hates verbose responses" once.
- **User constraint (HARD):** Same as B-12. Manual `/memory accept` only.
  Default OFF.
- **Acceptance:** test that 20-turn mock session emits one proposal file
  + one chat notification, no edit to memory.md.

## B-14 — FTS5 cross-session search
- **Priority:** P1
- **Effort:** M (~250 LOC)
- **Status:** PROPOSED
- **Source — Hermes:** `tools/session_search_tool.py` + `hermes_state.py:1229-1396`
  — SQLite FTS5 over all messages; CJK fallback; snippet+context.
- **Source — Runnable:** N/A (uses CCR remote API).
- **v5 target:** index `compact_v5_wip/<workspace>/turn_journal.jsonl` into
  SQLite FTS5 lazily (on first `session_search` call). Add
  `compact_v5/tools/session_search.py` tool. Top-3 results summarised by
  Bedrock (not Gemini).
- **Value:** "What did we figure out about the S3 issue last Tuesday?"
  works. Long tasks span sessions; without this, you re-do analysis.
- **User constraint:** Index stays in `compact_v5_wip/`, never exfiltrated.
  Summarisation uses Bedrock Haiku, not external API.
- **Acceptance:** test that searching for a known phrase across 3 mock
  sessions returns the correct session id and snippet.

## B-15 — Local exploration concrete fallback paths
- **Priority:** P2
- **Effort:** S
- **Status:** PROPOSED
- **Source — Codex review of S3 transcript (internal finding).**
- **v5 target:** add to prompt or skill: when "local data" fallback is
  invoked, search `/home/sagemaker-user/`, `/home/sagemaker-user/SageMaker/`,
  mounted dirs — don't tour the v5 install tree.
- **Value:** Recovers gracefully when an AWS path is blocked.
- **Acceptance:** S3 follow-up regression test extension.

---

# Tier 2 — high value, modest effort, post-Tier-1

## B-16 — Per-tool cache-break diff logging
- **Priority:** P2
- **Effort:** M (~50 LOC additive on top of B-08)
- **Source — Runnable:** `promptCacheBreakDetection.ts:71-99` — per-tool
  hash diffing.
- **Source — Hermes:** N/A.
- **v5 target:** extend B-08 with which tool's schema changed.
- **Value:** Tells you *exactly* which tool description broke the cache.
- **Acceptance:** test that a 1-tool description tweak produces a diff
  identifying that tool.

## B-17 — Model fallback after N consecutive 529s
- **Priority:** P2
- **Effort:** S (~40 LOC)
- **Source — Runnable:** `services/api/withRetry.ts:267-314` — fast-mode
  fallback / model swap.
- **v5 target:** add a `consecutive_529_count` to bedrock client; after
  threshold, swap to Haiku as fallback for next N turns with user
  notification.
- **Value:** Sustains long tasks through Bedrock capacity dips without
  user intervention.
- **User constraint:** Notify user of model swap; allow `/no-fallback`
  to disable.

## B-18 — Turn-level cancel on `ask_user`
- **Priority:** P2
- **Effort:** XS (~15 LOC)
- **Source — Hermes:** turn-scoped cancellation pattern via
  `abortController`.
- **v5 target:** wire `on_stop_check` into
  `compact_v5/tools/ask_user.py:24-58` so Stop button reliably interrupts
  a stuck ask_user prompt.

## B-19 — `compact_v5_wip/` permission receipts
- **Priority:** P3
- **Effort:** S
- **Source — Runnable:** `tools/ExitPlanModeTool/ExitPlanModeV2Tool.ts:61-90`
  — semantic permission categories.
- **v5 target:** audit log of repeated auto-approved actions for enterprise
  review.

## B-20 — Final-task quality gate for complex coding tasks
- **Priority:** P2
- **Effort:** M
- **Source — Runnable:** `constants/prompts.ts:394` — independent
  adversarial verification before completion claims.
- **v5 target:** structural final gate that requires `changed_files +
  tests_run + reviewer_verdict + unresolved_failures` to be populated
  before claiming DONE on multi-file coding work.

## B-21 — Heartbeat-aware persistent retry mode
- **Priority:** P2
- **Effort:** S
- **Source — Runnable:** `withRetry.ts` heartbeat (already B-03) +
  Hermes `cron/scheduler.py` polling.
- **v5 target:** combine B-03 heartbeat + B-01 supervisor into a
  unified `persistent_runtime_health` log.

---

# Tier 3 — optional / research

## B-22 — Cron scheduler (port from Hermes)
- **Priority:** P3 (LOWER for single-user-present-during-work profile)
- **Effort:** L (~2100 LOC)
- **Source — Hermes:** `cron/scheduler.py:1-1284` + `cron/jobs.py:1-835`.
- **v5 target:** new `compact_v5/runtime/cron/` package.
- **Value:** "Review every Monday 9am" — only matters if user wants
  unattended scheduled runs while away.
- **Defer:** unless a real "user is away" use case lands.

## B-23 — RPC tool bridge (collapse N tool calls into 1 script)
- **Priority:** P3
- **Effort:** L (~400 LOC)
- **Source — Hermes:** `acp_adapter/server.py:500-622` + `acp_adapter/entry.py`.
- **v5 target:** stdio JSON-RPC server exposing the v5 tool surface so
  Python scripts can invoke tools in one turn.
- **Value:** Dramatic token savings on repetitive workflows.
- **Defer:** clear ROI but tail-end of priorities.

## B-24 — Batch trajectory generation
- **Priority:** P3 (research only)
- **Source — Hermes:** `batch_runner.py:233-299` — multiprocessing.Pool.
- **v5 target:** new `compact_v5/research/batch_runner.py`.
- **Defer:** only when training/benchmarking is on the agenda.

## B-25 — Honcho dialectic user modeling
- **Priority:** P3 (optional plugin)
- **Source — Hermes:** `plugins/memory/honcho/client.py:1-150`.
- **v5 target:** optional plugin in `compact_v5/memory/honcho/`.
- **Defer:** only valuable if multi-project user calibration is needed.

## B-26 — User-defined output styles
- **Priority:** P3
- **Source — Runnable:** `services/outputStyles/` + `loadOutputStylesDir.ts:26+`.
- **v5 target:** `compact_v5/ui/output_styles/` with frontmatter loader.
- **Defer:** cosmetic.

## B-27 — 5-event minimal hooks contract
- **Priority:** P3
- **Source — Runnable:** `utils/hooks/AsyncHookRegistry.ts` (20+ events).
- **v5 target:** five events only — `pre_tool_use`, `post_tool_use`,
  `pre_compact`, `post_compact`, `session_end` — fired into shell scripts
  under `~/.sageagent/hooks/`.
- **Defer:** unless a customer asks.

## B-28 — Image/notebook cohesion in `read_file`
- **Priority:** P3
- **Source — Runnable:** `tools/FileReadTool/FileReadTool.ts:44-58`.
- **v5 target:** either unify image handling into read_file or document
  the `view_image` separation.

## B-29 — Async-generator engine refactor (architectural rewrite)
- **Priority:** P3 (DEFER until concrete user-visible need)
- **Effort:** XL
- **Source — Runnable:** `query.ts` async generator pattern.
- **v5 target:** would require rewriting `compact_v5/core/query_engine.py`
  + `compact_v5/agent.py` + UI router.
- **Skip:** unless live per-token CLI streaming becomes a concrete
  product requirement. The current sync-callback architecture works for
  Jupyter widgets.

---

# Skip (intentional gaps)

## SKIP-1 — Cross-platform terminal backends
- **Source — Hermes:** local + Docker + SSH + Daytona + Singularity + Modal.
- **Rationale:** v5 is SageMaker notebook only. Intentional.

## SKIP-2 — ACP server / external client API
- **Source — Hermes:** `acp_adapter/server.py:1-80`.
- **Rationale:** v5 lives inside Claude Code / SageMaker, not exposed as a
  service. Intentional.

## SKIP-3 — Messaging gateways (Telegram/Discord/Slack/WhatsApp/Signal)
- **Source — Hermes:** `gateway/`.
- **Rationale:** v5 is notebook-bound. Intentional.

## SKIP-4 — Plugin marketplace
- **Source — Runnable:** `builtinPlugins.ts:21+` + plugin loader.
- **Rationale:** v5 is SageMaker-only enterprise. Plugins add surface
  area without benefit. Intentional.

## SKIP-5 — MCP support
- **Source — Runnable:** MCP infrastructure throughout.
- **Rationale:** v5.0.1 hard constraint #9 (no MCP). Enforced at
  `compact_v5/entry.py:28-58` banned-subsystem guard. Intentional.

## SKIP-6 — Permission-mode LLM classifier
- **Source — Runnable:** `utils/permissions/yoloClassifier.ts` + Statsig
  feature gates.
- **Rationale:** v5 chose static allowlist + fail-closed for enterprise
  safety. Avoiding LLM-in-the-permission-path is a deliberate v5 win.
  Intentional.

---

# Ranked roll-up for the user's profile

**Single-user / coding agent / hours-to-days task / cost-sensitive:**

| Order | Block | Why this position |
|---|---|---|
| 1 | B-01 supervisor + inactivity timeout | Hung tools are the #1 cause of dead overnight sessions |
| 2 | B-02 auto-resume after crash | Hour-7 crashes are devastating without this |
| 3 | B-03 retry heartbeat | Silence during retries triggers premature user abort |
| 4 | B-05 + B-10 + B-08 cache optimization | Direct cost reduction across every long task |
| 5 | B-04 per-turn telemetry | Can't optimize what you can't measure |
| 6 | B-11 plan-mode prompt suffix | Cheap improvement to model compliance |
| 7 | B-14 FTS5 session search | "What did we figure out yesterday?" |
| 8 | B-12 + B-13 nudges (manual approval) | Self-improving agent — but never auto-apply |
| 9 | B-17 model fallback on 529 storms | Sustains long runs through Bedrock dips |
| 10 | B-18 turn-level cancel on ask_user | Small but real bug |

Everything else is P2/P3 and can wait for a concrete pain point.

# Maintenance protocol

- New deep-scan findings → add a Block here.
- A Block lands → status changes to LANDED + commit SHA recorded.
- A Block is skipped → move to "Skip" section with rationale.
- This doc is the **single forward-looking source** for v5 evolution.
  Anything claimed as "v5 will do X" must point to a Block here.
