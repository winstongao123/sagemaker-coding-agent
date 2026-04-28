# Production Readiness Status — compact_v4 V4.10.4

**Date:** 2026-04-28 (sub-agent handoff release)
**Runtime version:** `__version__ = "4.10.4"` ([sagemaker_agent.py](../MAIN/agent/sagemaker_agent.py))
**Scope:** personal / self-use SageMaker coding agent using AWS Bedrock
**Status:** **ship-ready for self-use SageMaker.** Not production-grade for shared / regulated / unattended operation (those would need a live Bedrock smoke test recorded, multi-user concurrency review, and a measured Runnable cost-benchmark — all out of scope for self-use).

## Test totals (deterministic offline suite)

- **160 passing** across `MAIN/agent/test_v4*.py` and `MAIN/tests/test_advanced.py` (excluding 1 known pre-existing fail in `test_v46_complex.py "Skill discovery works"` — V4.8.0 setting `auto_trigger:false` on security-review broke this older test, intentional behavior change).
- **74 passing** for the v4.10.x + v4.9.x auto-trigger regression subset (the targeted release verification).
- **Live tests** (`MAIN/tests/test_production.py` against real Bedrock) NOT run by default — manually invoked with AWS credentials; not a deterministic offline path.

## Known limitations (honest caveats Codex flagged)

1. **No ToolSearch deferred-schema** — all 23 tools are loaded up-front (~1.8K tokens). Acceptable for self-use; only matters at 60+ tools. Existing context-aware tool exclusion already trims doc/vision/web/semantic tools when not mentioned in recent text.
2. **Todo tool minimalism** — 2 tools (`todo_write` / `todo_read`) vs Runnable's 6-tool TaskCreate/Update/List/Get/Output/Stop suite. Intentional — self-use needs a step list, not a multi-tenant scheduler.
3. **Sub-agent handoff is prompt-dependent** — parent passes context via the `prompt` argument. v4.10.0 env-details block covers cwd/git state. No shared task state object — single-process SageMaker has no IPC layer to share state across processes.
4. **Token efficiency not benchmarked vs Runnable** — cache-boundary regression test (v4.10.3) proves the cache CAN activate; actual hit-rate on long sessions hasn't been measured. Sonnet 4.5 default is ~10x Haiku per token; cache earlier-activates (1024 vs 4096 token threshold) which partially offsets. **Recommend running one long-task trace on real Bedrock and comparing tokens-billed-vs-tokens-cached before declaring cost-equivalence with Runnable.**

## Ship gate (run before any release)

```
python compact_v4/verify_ship_zip.py
```

Asserts: required runtime files at root, required skill subfolders, no forbidden artefacts (test tempdirs, caches, `.proposed/`, `MAIN/agent/` wrapper), version sanity, flat-root layout. Exit 0 = ship-ready.



## Current Verdict

Not 100% production ready for shared, regulated, or unattended operation. Stronger self-use release candidate for SageMaker.

V4.10.0 includes the V4.9.6/V4.9.7 hardening fixes plus runnable-parity upgrades that fit SageMaker self-use:

- skill auto-loading is now default-off
- compaction now starts with a Bedrock-safe user message
- build sub-agent worktree isolation now actually runs
- build worktrees see dirty/untracked parent state
- parallel build sub-agents serialize to preserve worktree isolation
- `AGENT_STATUS.md` is loaded every top-level run for durable long-task state
- SageMaker git handling is local-tree-only; GitHub/`gh`/PR/remote git operations are not assumed
- the release zip has been rebuilt from the fixed runtime files
- `/context` identifies context/token bloat sources, duplicate full-file reads, and the next suggested action
- `notebook_edit` surgically edits existing `.ipynb` cells without overwriting whole notebooks
- skill listing is token-budgeted to avoid prompt bloat from many skills
- sub-agents receive a compact environment block: type, depth, cwd, git HEAD/status
- context window is derived from the Bedrock model map, with validated override support
- reactive compact retries once after Bedrock context-overflow rejection
- context collapse reduces runs of stale already-microcompacted tool round-trips

The current runnable comparison record is maintained in `docs/RUNNABLE_APPLICABILITY_REVIEW.md`. Runtime changes should come from that review path, not from copying broad runnable features directly into V4.

That is enough to continue serious personal/self-use coding in SageMaker with approval on and local git safety. It is not enough to call the system production-ready for multi-user use, regulated data, or unattended autonomous coding.

## Fixed in V4.9.6

| Area | Previous Risk | Status |
|---|---|---|
| Skills | Skills could auto-load from keyword/name matches and inject long instructions unexpectedly | Fixed: global `enable_skill_auto_trigger` defaults false; missing `auto_trigger` defaults false |
| Compaction | Compact could create assistant-first message history and risk Bedrock validation failure | Fixed: compact summary is a user message followed by assistant ack |
| Build sub-agents | Claimed worktree isolation branch was unreachable | Fixed: worktree creation now gated by `_worktree_ready` |
| Dirty workspace | Build worktree started from `HEAD` and missed current uncommitted edits | Fixed: dirty tracked and untracked files are overlaid into worktree |
| Parallel build agents | Parallel build agents could not safely use separate worktrees because `CONFIG.workspace` is global | Fixed: build agents serialize when worktree isolation is enabled |
| Long-running memory | Critical task state could rely too much on chat history and compaction quality | Fixed: `AGENT_STATUS.md` is a loaded durable handoff doc; `/status` can show or initialize it |
| Git/GitHub boundary | Agent could assume SageMaker can publish to GitHub or run remote git workflows | Fixed: runtime guidance and bash security now treat git as local-tree-only and block remote git operations |
| Release bundle | Ship bundle needed to reflect V4.9.6 runtime and docs without deep wrapper folders | Fixed: `compact_v4.zip` rebuilt, 22 files / 223.4 KB, flat root layout |

## Fixed in V4.9.7

| Area | Previous Risk | Status |
|---|---|---|
| Context visibility | Long tasks had a context percentage but no built-in explanation of what was consuming the window | Fixed: `/context` reports fixed overhead, tool request/result token sources, duplicate file reads, and a suggested next action |
| Release bundle | Ship bundle needed to include the V4.9.7 runtime and docs | Fixed: `compact_v4.zip` rebuilt with flat root layout |

## Fixed in V4.10.0

| Area | Previous Risk | Status |
|---|---|---|
| Notebook editing | Updating an existing notebook could require rewriting the full file | Fixed: `notebook_edit` supports insert/replace/delete of one cell with atomic write |
| Skill prompt bloat | Large skill lists could consume unnecessary tool-description tokens | Fixed: skill listing budget caps list at 1% of context window / 2,000 tokens |
| Sub-agent context | Fresh sub-agents could miss workspace/git state details | Fixed: per-sub-agent env-details block |
| Context window config | Thresholds assumed one static context size | Fixed: model-to-context-window map and validated `context_max_tokens` override |
| Context overflow recovery | Bedrock prompt-too-long errors could stop a long run | Fixed: reactive compact + one retry per run |
| Stale tool-call shape | Microcompact reduced output body size but left many stale tool round-trip messages | Fixed: `context_collapse()` collapses 3+ consecutive stale pairs into a synthetic Bedrock-safe pair |
| Release bundle | V4.10.0 zip must remain runtime-only and one-layer | Fixed: `compact_v4.zip` rebuilt, 22 files / 234.6 KB, flat root layout |

## Verification Status

Deterministic targeted tests currently pass:

- `test_v49_auto_trigger.py`
- `test_v491_unskill.py`
- `test_v494_hermes_patterns.py`
- `test_v495_self_patching.py`
- `test_v42_gap_closure.py`
- `test_v493_enhancements.py`
- `test_v471_enhancements.py`
- `test_v461_path_fix.py`
- `test_v410_skill_listing_budget.py`
- `test_v410_subagent_env.py`
- `test_v410_context_window.py`
- `test_v410_notebook_edit.py`
- `test_v410_reactive_compact.py`
- `test_v410_context_collapse.py`

Combined deterministic targeted suite after V4.10.0: **159/159 passing**.

## Remaining Production Gaps

### P0 Before Calling It Production

1. **Clean test harnesses**
   - `test_production.py` and `test_advanced.py` execute live Bedrock work at import time.
   - `test_v46_live.py` has pytest-collected tests requiring a missing `model_id` fixture.
   - Split offline unit tests from explicit live tests.

2. **Real SageMaker smoke test**
   - Launch `chat.ipynb` in SageMaker.
   - Confirm Bedrock model call, file read/write, compact, skill use, and build sub-agent worktree flow.

3. **Security pass**
   - Re-review bash/python execution boundaries.
   - Confirm allowed paths cannot be escaped through symlinks, relative paths, git worktree paths, or generated file paths.
   - Confirm `memory.md`, `AGENT_STATUS.md`, `CLAUDE.md`, and `SKILL.md` prompt-injection warnings are visible enough for the operator.

### P1 Strongly Recommended

1. **Sub-agent state isolation**
   - `CONFIG.workspace` is global. V4.9.6 serializes build agents, but a cleaner design would pass workspace through agent/tool context rather than global config.

2. **Live Bedrock regression profile**
   - Keep live tests behind an explicit flag such as `RUN_LIVE_BEDROCK=1`.
   - Record model, region, token/cost, and expected latency.

3. **Session and memory concurrency**
   - Audit session save/load, `_TODOS`, `_RECENT_DIFFS`, `_FILES_READ`, and memory extraction under interrupted or overlapping UI actions.

4. **Full runnable comparison checklist**
   - Context collapse parity beyond `/context` + reactive compact
   - Skill invocation parity
   - Sub-agent lifecycle parity
   - Permission persistence and auditability
   - Recovery after kernel restart

See `docs/RUNNABLE_APPLICABILITY_REVIEW.md` for the feature-by-feature applicability decision log.

## Self-Use Recommendation

Use it for personal SageMaker coding with these settings:

```python
CONFIG.require_tool_approval = True
CONFIG.enable_skill_auto_trigger = False
CONFIG.enable_worktree = True
CONFIG.enable_status_doc = True
CONFIG.enable_skill_patching = False
CONFIG.session_cost_limit = 5.0
```

Suggested operating rule:

- Use `/skill use <name>` explicitly.
- Keep `AGENT_STATUS.md` current on long-running or critical work.
- Use local git status/diff/log/worktree/commits only inside SageMaker; publish elsewhere manually if needed.
- Use `/done quick` before trusting non-trivial changes.
- Use `/verify` before applying generated code to valuable repos.
- Commit or checkpoint manually before long build-agent runs.

## Production Answer

No coding agent is "100%" production-ready in the absolute sense. For this one, the honest status after V4.10.0 is:

- **Personal self-use:** strong release candidate, ready for heavier SageMaker smoke testing.
- **Team shared use:** not yet.
- **Regulated / insurance production:** not yet.
- **Unattended autonomous coding:** not yet.
