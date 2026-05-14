# 2026-05-14 — Hermes Agent Deep Scan

Source repos:
- v5 target: `d:/Github/sagemaker-coding-agent/compact_v5/`
- Hermes: `d:/Github/hermes-agent/` (NousResearch fork, v0.11.0, last commit 2026-04-25)

Purpose: previous deep scans focused on Runnable Claude Code. This scan
focuses on **Hermes specifically for long-running coding-task ability** —
the axis where Hermes is purpose-built and v5 has gaps to close.

## Hermes repo facts (myth-busting)

| Question | Answer |
|---|---|
| Latest? | v0.11.0, head commit `67892801` 2026-04-25. Active, actively maintained by NousResearch. |
| Mac-only? | **No.** Dockerfile = Debian Trixie. README claims Linux, macOS, WSL2, Termux/Android. Six terminal backends (local, Docker, SSH, Daytona, Singularity, Modal). |
| MIT license? | Yes. Fork-and-adapt is fine. |
| Cross-session memory? | Yes — SQLite + FTS5 + Honcho dialectic user model + autonomous nudges. |
| Built for long-running tasks? | Yes — that is the explicit product positioning. |

## Scope of this scan

Three non-overlapping parallel agents scanned:
- **Round H1**: session persistence + hibernate/wake + cron + cross-session continuity + process supervision.
- **Round H2**: subagent delegation + RPC tool calls + batch trajectory generation + concurrency model + ACP.
- **Round H3**: autonomous skill creation + cross-session FTS5 search + Honcho dialectic user modeling + nudge loop.

## Consolidated findings table

| Capability | Hermes (file:line) | v5 (file:line) | Gap | v5 should adopt? | Plain-English value |
|---|---|---|---|---|---|
| **Background skill nudges** (autonomous review every N turns) | `run_agent.py:1706-1717` + `:9425-9450` (SKILLS_REVIEW_PROMPT); default interval 10 turns; fire-and-forget thread post-response | `compact_v5/tools/skill_propose_patch.py:33-151` (manual only, `CONFIG.enable_skill_patching=False` default) | MAJOR | YES | Agent silently learns from its own work without you asking. Today v5 forgets useful patterns unless you type `/skill`. |
| **Background memory nudges** (auto-extract facts every N turns) | `run_agent.py:1589` (`memory_nudge_interval=10`) + `SESSION_REVIEW_PROMPT` template | `compact_v5/runtime/dream.py:1-150` — manual `/dream` only | MAJOR | YES | Agent saves "user is on Windows, prefers TypeScript" without you needing to tell it twice. v5 today re-asks the same things across sessions. |
| **FTS5 cross-session search** (search every past conversation) | `tools/session_search_tool.py` + `hermes_state.py:1229-1396` — SQLite FTS5 over all messages; CJK fallback; snippet+context; LLM summarises top 3 | (none) — `turn_journal.jsonl` exists but is not indexed | MAJOR | YES | "What did we figure out about the S3 path issue last Tuesday?" — works in Hermes, fails in v5. Critical for hours/days tasks. |
| **Cron scheduler** | `cron/scheduler.py:1-1284` + `cron/jobs.py:1-835` — one-shot + interval + 5-field cron; grace windows; workdir + skills per job; tick every 60s; inactivity timeout 600s default | (none) | MAJOR | OPTIONAL | "Run a code review every Monday 9am, send me the result" — Hermes ships this. v5 needs notebook open. |
| **Process supervision + inactivity timeout** | `cron/scheduler.py:988-1055` — polls `agent.get_activity_summary()` every 5s, kills if idle >600s, logs last activity for diagnostics | `compact_v5/core/retry.py:1-91` — Bedrock-level retry only; no agent-level supervisor | MAJOR | YES | If a tool hangs waiting on network, Hermes kills it after 10min. v5 can hang indefinitely. Bigger pain on long unattended runs. |
| **Session compression chains + auto-resume** | `hermes_state.py:757,1042` — `parent_session_id` links a compressed session to its successor; auto-resume on gateway restart | `compact_v5/runtime/state.py:168-189` (`last_turn.json` + `turn_journal.jsonl`) — written, not auto-loaded across kernel restarts | MAJOR | YES (partial) | After a kernel crash at hour 4, Hermes resumes from message 1000. v5 needs you to manually re-stage context. |
| **Subagent isolation + parallelism** | `tools/delegate_tool.py:1-17,1078-1083` — ThreadPoolExecutor, `max_concurrent_children=3`, `_set_subagent_approval_cb` for thread-safe approval | `compact_v5/subagent/spawn.py:1-77` — serial child run; shared IterationBudget | MINOR | YES (when an orchestrator role lands) | "Plan + Build + Review in parallel" — Hermes does it; v5 runs them one at a time. |
| **Delegate-block list (prevent recursive loops)** | `delegate_tool.py:40-49` — `DELEGATE_BLOCKED_TOOLS` includes `delegate_task`, `execute_code` | (n/a, no delegate tool yet) | n/a | YES (when orchestrator lands) | Prevents an agent spawning agents spawning agents until the budget is gone. |
| **RPC tool bridge** (scripts call tools via JSON-RPC) | `acp_adapter/server.py:500-622` + `acp_adapter/entry.py` — ACP JSON-RPC stdio; external Python scripts can invoke tools | (none) — v5 tools only callable inside one turn | MAJOR | OPTIONAL (post-final-test) | Collapse 20 tool calls into 1 python_exec running a script. Cuts cost dramatically on repetitive workflows. |
| **Batch trajectory generation** | `batch_runner.py:233-299` — multiprocessing.Pool, checkpoint resume, JSONL output with per-row docker_image + cwd | (none) — manual notebook runs only | MAJOR | OPTIONAL (research) | Run 1000 prompts overnight, get a JSONL of results. Useful for training/benchmarking; not core to a single SageMaker session. |
| **Honcho dialectic user modeling** | `plugins/memory/honcho/client.py:1-150` — per-user profile across sessions; recall modes (hybrid/context/tools) | `compact_v5/memory/` — per-project file-based, no cross-project user model | MAJOR | OPTIONAL | Per-user calibration (preferred style, verbosity, tool habits). High value if multi-user. |
| **agentskills.io standard** | README claim of compatibility; no enforced schema in code | v5 skill schema is proprietary (richer: `requires_tools`/`enabled_when`/`paths`) | MINOR | NO (yet) | Adopt if/when a real shared schema exists. Currently aspirational. |
| **Cross-platform terminal backends** | local + Docker + SSH + Daytona + Singularity + Modal | SageMaker notebook only | n/a | NO | v5 is SageMaker-only by design. Intentional gap. |
| **ACP server (external client API)** | `acp_adapter/server.py:1-80` — JSON-RPC server so external IDEs spawn sessions | n/a — v5 IS the IDE's runtime | n/a | NO | v5 doesn't expose itself; it lives inside Claude Code / SageMaker. Intentional. |
| **Messaging gateways** (Telegram/Discord/Slack/WhatsApp/Signal) | `gateway/` | (none) | n/a | NO | Not in scope. v5 is notebook-bound. |

## Ranked adoption recommendations

### Tier 1 — high value, modest effort, fits SageMaker
1. **Background skill nudges** — port Hermes' `_skill_nudge_interval` counter and `_spawn_background_review()` pattern into `compact_v5/agent.py`. ~150 LOC.
2. **Background memory nudges** — same pattern with `_memory_nudge_interval`; reuse `runtime/dream.py` engine. ~80 LOC.
3. **FTS5 session search** — index `.sageagent_state/turn_journal.jsonl` into SQLite FTS5, add `session_search` tool, top-3 results summarised by Bedrock (not Gemini). ~250 LOC.
4. **Process supervision + inactivity timeout** — port `cron/scheduler.py:988-1055` activity tracker into `compact_v5/runtime/`. Kill tool after configurable idle (default 600s). ~120 LOC.
5. **Auto-resume compression chains** — add `parent_session_id` to `last_turn.json`; auto-load on kernel restart if the same workspace. ~80 LOC.

### Tier 2 — high value, larger effort
6. **Cron scheduler** — port `cron/jobs.py` + `cron/scheduler.py` (~2100 LOC). Limit delivery to local-only initially. Useful for "review every Monday" automation in SageMaker. Requires notebook background-thread tick loop.
7. **Parallel sub-agent delegation** — when an orchestrator role lands, add ThreadPoolExecutor + delegate-block list. ~200 LOC.

### Tier 3 — optional / research
8. **RPC tool bridge** — JSON-RPC over stdio for Python scripts to call v5 tools. ~400 LOC. Cost-saving for repetitive pipelines.
9. **Batch runner** — multiprocessing trajectory generation. ~300 LOC. Research/benchmarking use case.
10. **Honcho dialectic user modeling** — pluggable cross-session user profile. ~250 LOC plus dependency.

### Skip (intentional gaps)
- Cross-platform terminal backends — SageMaker is fixed env.
- ACP server — v5 lives inside Claude Code, not exposed.
- Messaging gateways — out of scope.

## What v5 already does better than Hermes

| Axis | v5 win |
|---|---|
| Bedrock-native client | Hermes uses 200+-model abstraction; v5 is Bedrock-tuned with prompt-cache invariants + cache-break detection primitives. |
| Skill propose-not-apply gate | v5's 8-rail safety (`skill_propose_patch.py:33-51`) is safer than Hermes' direct-write review agent for unsupervised work. |
| Banned-subsystem import guard | v5's `entry.py:28-58` fails fast if MCP is re-introduced; Hermes has no equivalent. |
| Deterministic file-evidence verify/done gate | v5's `runtime/gate.py:1-60`; Hermes verifies through skill-based interactive review only. |
| Active rich skill conditionals | `requires_tools` + `enabled_when` + `paths` triggers. Hermes skill schema is simpler. |

## Cumulative scan tally

| Reference repo | Rounds done | v5 wins | Major gaps (after dedup) | Backlog adoption items |
|---|---|---|---|---|
| Runnable Claude Code | 9 (rounds 1-9) | 14 | 12 | 14 |
| Hermes Agent | 3 (rounds H1-H3, this doc) | 5 | 7 cross-cutting | 5 Tier-1 + 2 Tier-2 + 3 Tier-3 |

Combined post-final-test backlog **does not include any blockers** for the
current `compact_v5_ship.zip`. Five high-value Hermes Tier-1 items are
purely additive observability/learning loops that don't change the engine's
existing behaviour.

## Self-review notes

- All three agents used the live local Hermes repo at
  `D:/Github/hermes-agent/`, not an archive.
- Every gap row cites a Hermes file:line AND a v5 file:line (the "where we
  cleared / where we have the primitive" cross-link the user asked for).
- No runtime code touched.
- Intentional gaps explicitly marked (terminal backends, ACP, messaging).
- "Mac-only" question explicitly answered: NO — Hermes is cross-platform.
