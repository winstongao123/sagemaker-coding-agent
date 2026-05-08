# Wave 6 — User-Perspective Brainstorm: Multi-file coding tasks + refactoring + project workflows

**Date**: 2026-05-01
**Persona**: SageMaker user (data analyst / ML engineer in insurance company) — uses `compact_v5/_phase_2/v4_reference/chat.ipynb` to do real coding inside SageMaker Studio. No external internet (v4 Bedrock-only constraint applies).
**Method**: 25 distinct realistic scenarios. Each one cross-checked against:
- Plan: `compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md` (Block-level scoping)
- Synthesis: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` (per-row file:line + Graft)
- v4 baseline: `compact_v4/MAIN/agent/sagemaker_agent.py`

Verdict legend:
- **HANDLED** — plan covers it with specific Block + file:line + mechanism.
- **NEEDS-LOCK-TEST** — plan covers the mechanism but no acceptance test in Q4; must add lock test before ship.
- **POSSIBLE-GAP** — plan does not address the failure mode; needs new PORT_LOG row or v5-native enhancement.

---

## Scenario 1 — Build a Power BI dashboard from a CSV (analyst flagship workflow)

- **What user does**: opens `chat.ipynb` in SageMaker, pastes "build me a Power BI dashboard from `claims_2025.csv` — 4 charts (severity by region, monthly trend, top-10 carriers, age-band heatmap) + summary commentary. Output as one .pbix-equivalent flow: .xlsx data + .docx report + chart PNGs."
- **What could go wrong**: agent stops after first chart (iteration budget exhaustion mid-task with no auto-continue), or charts silently overwrite each other because `create_chart` lacks unique-path discipline, or .docx embeds broken image refs.
- **What v5.0.1 plan provides**:
  - Block T row T-1 / T-3 / T-5 / T-6: `create_excel` (v4 :5730), `create_chart` (v4 :6039), `create_word` (v4 :5642), `create_pdf` (v4 :6282) ported verbatim → `tools/create_excel.py`, `tools/create_chart.py`, `tools/create_word.py`.
  - Block F2 (NEW) F2-1: TokenBudget auto-continuation `query/tokenBudget.ts:1-93` — at <90% budget AND not diminishing-returns, agent injects "continue" and proceeds past 4-chart wall.
  - Block A row A-43: `generateTempFilePath` content-hash mode (`utils/tempfile.ts:1-32`) prevents chart-PNG name collisions.
- **Verdict**: **HANDLED** — but cross-tool round-trip (create_chart → create_excel embed → create_word embed) needs Block T Q4 lock test that exercises the chain end-to-end, not each tool in isolation.

---

## Scenario 2 — Refactor a 2,000-line `sagemaker_agent.py`-style monolith into 5 files

- **What user does**: "split `pipeline_monolith.py` into `loader.py`, `transform.py`, `model.py`, `predict.py`, `pipeline.py` — keep all existing imports working from outside callers."
- **What could go wrong**: agent rewrites file losing user's manual edits made in another window (mtime stale check missed), or curly-quote vs straight-quote breaks string-literal moves, or CRLF→LF flip on Windows breaks SageMaker Studio terminal `python -c "import pipeline_monolith"`.
- **What v5.0.1 plan provides**:
  - Block C row C-3 `findActualString` quote-normalized match (`FileEditTool/utils.ts:73-93`) — curly→straight normalization.
  - Block C row C-4 `preserveQuoteStyle` (`utils.ts:104-120`) — re-wraps if file uses curly.
  - Block C row C-7 `\r\n`→`\n` normalization preserving original on write.
  - Block C row C-8 staleness Windows content-fallback for OneDrive/AV mtime bumps (`FileEditTool.ts:289-311`).
  - Block C+ row C+2 file-history snapshot per-edit (`FileEditTool.ts:431-440`) → enables `/rollback` if user's manual edit gets overwritten.
- **Verdict**: **HANDLED** — five C-rows directly address the failure modes. Block C Q4 lock test includes the staleness check; need explicit "manual edit during agent edit" race test added to Block C+ Q4.

---

## Scenario 3 — Add unit tests for module X (multi-file: read source, generate `test_X.py`, run pytest)

- **What user does**: "add pytest unit tests for `claim_normalizer.py` covering all branches; run them and fix any failures."
- **What could go wrong**: agent loops forever on a flaky test (no test-call dedup), or runs pytest 40 times hitting v4's exec-call-limit hard-stop with misleading error, or never resets the per-turn discoveredToolNames so subsequent turns think pytest is the "only" tool.
- **What v5.0.1 plan provides**:
  - Block C row C-9 `interpretCommandResult` exit-code semantics (`BashTool/commandSemantics.ts:1-140`) — pytest exit 1 = test fail, exit 5 = no tests collected, agent reads correctly not as "blocked".
  - Block C row C-18 + C-19 multi-pass JSON repair (`run_agent.py:547-641`) — Bedrock Haiku malformed args don't crash pytest invocation.
  - Block M Fix 1: `core/query_engine.py:run()` resets `self._discovered_tool_names = set()` per-turn.
  - Block M Fix 2: `countToolCalls` from `QueryEngine.ts:1004-1048` + retry-limit check.
  - Block N row N-15 fuzzy tool-name matching (`run_agent.py:4689-4720`) — `pytest` typo → `bash` resolution.
- **Verdict**: **HANDLED** — Block M is exactly this scenario's root cause fix.

---

## Scenario 4 — Migrate SAS code to Python pandas (legacy insurance pipeline, 8 .sas files)

- **What user does**: "convert these 8 SAS programs in `legacy/` to one pandas pipeline, keep semantic equivalence, write a comparison report."
- **What could go wrong**: massive context bloat as 8 SAS files load, mid-task compaction strips the SAS source before agent finishes Python conversion, post-compact agent re-reads files from scratch wasting tokens.
- **What v5.0.1 plan provides**:
  - Block A row A-11 `createPostCompactFileAttachments` (`compact.ts:1415-1655`) re-injects recently-touched files post-compact.
  - Block A row A-14 POST_COMPACT exclusion list (`compact.ts:1674-1705`) excludes CLAUDE.md/MEMORY.md from re-inject — only the SAS files, not memory.
  - Block A row A-21 `runPostCompactCleanup` cache invalidation (`postCompactCleanup.ts:1-77`) clears _FILES_READ + skill-listing-cache.
  - Block A row A-25 stub-injection for missing tool_results post-compact (Hermes `run_agent.py:4585-4604`) — without it, Bedrock 400-errors after compact.
  - Block A row A-27 `flush_memories` pre-compression turn (Hermes `run_agent.py:7913-8157`) — extracts what agent has learned about SAS quirks BEFORE compact strips messages.
- **Verdict**: **HANDLED** — five A-rows cover compact survival. Block A Q4 lock test explicitly: "30-min idle + microcompact + freed ≥5K tokens"; need dedicated long-task lock test where 8-file content survives 1 reactive compact.

---

## Scenario 5 — Build a new feature spanning 8 files (cross-cutting: config, model, API, UI, tests, docs)

- **What user does**: "add `policy_renewal_reminder` feature: config flag, scheduler job, email template, REST endpoint, integration test, README update — touch 8 files."
- **What could go wrong**: parallel writes to 8 files but two of them have a path conflict (e.g., both edit `__init__.py`), corrupting the file; or agent forgets one file silently (Codex AXIS C "scope-narrowing" failure mode); or stops mid-feature when iteration budget hits.
- **What v5.0.1 plan provides**:
  - Block N row N-2 path-scoped parallelism helpers (Hermes `run_agent.py:355-380`).
  - Block N row N-3 `_NEVER_PARALLEL_TOOLS` / `_PATH_SCOPED_TOOLS` / `_MAX_TOOL_WORKERS=4` constants — Edit/Write to same path serialized.
  - Block N row N-4 worker tid race fix + checkpoint snapshots (`run_agent.py:8463-8725`).
  - Block F2 row F2-1 auto-continuation under iteration budget — feature finishes even at budget boundary.
  - Block K row K-7 A39 No-wire-dead-code without E2E (Hermes AGENTS.md) — prevents shipping a feature with one file silently dropped.
- **Verdict**: **HANDLED** — but the "cross-file scope-narrowing" risk needs a Block K-style end-of-task self-check (e.g., agent re-verifies all 8 files mentioned in spec are touched). Currently relies on user catching it. **Add lock test**: spec lists N files → agent confirms each touched.

---

## Scenario 6 — Find and fix all uses of deprecated `pd.append()` across 50+ files

- **What user does**: "replace every `pd.append()` and `df.append()` in the codebase with `pd.concat([...])`."
- **What could go wrong**: bash `grep -r` returns binary `.parquet` files mixed in (massive context waste), or agent loops re-reading same file with same offset/limit, or hits 200-call exec gate before finishing.
- **What v5.0.1 plan provides**:
  - Block C row C-15 `BINARY_EXTENSIONS` set + `isBinaryContent` 8KB null-byte sniff (`constants/files.ts:1-156`) — skips parquet/pickle/etc.
  - Block C v4 baseline: repetition detector (`:9156-9180`) — read_file dedup `f"{fp}@{offset}:{limit}"` blocks redundant reads.
  - Block C v4 baseline: exec-limit gate (`:9477-9489`) with explicit "Blocked: bash + python_exec call limit reached..." message + "OTHER TOOLS STILL WORK" listing.
  - Block T row T-7 `readFileInRange` fast/streaming with FileTooLargeError (`utils/readFileInRange.ts`) — reads 50-file logs without OOM.
- **Verdict**: **HANDLED** — three core-loop patterns cover the failure modes.

---

## Scenario 7 — Edit-test-edit workflow loop (TDD)

- **What user does**: edits `transform.py`, runs `python_exec("import transform; transform.test()")`, sees error, edits, re-tests — 15 iterations.
- **What could go wrong**: each test run re-invokes a stale Bedrock client connection (silent timeout on 16th iter), or agent forgets cwd between python_exec calls, or thinking-budget runs out without UI showing.
- **What v5.0.1 plan provides**:
  - Block C row C-17 `combinedAbortSignal` + `AsyncLocalStorage` cwd (Python `contextvars.ContextVar('cwd')`) — cwd preserved across calls.
  - Block L row L-6 stale-connection + keep-alive disable on retry (`withRetry.ts:112-118`) — Bedrock SDK client rebuilt on stale.
  - Block L row L-21 daemon-thread Bedrock call for Ctrl-C responsiveness (Hermes `run_agent.py:5637-5781`).
  - Block L row L-22 stale non-stream call detector (context-scaled deadline) (`run_agent.py:5704-5762`).
  - Block L row L-23 heartbeat callback every 30s during long calls.
  - Block E+F: ThinkingBudgetWidget already wired (Phase 11) — visible.
- **Verdict**: **HANDLED** — five L-rows directly target this loop's pain points.

---

## Scenario 8 — User has a `CLAUDE.md` in workspace; expects auto-load and rule respect

- **What user does**: drops `CLAUDE.md` at workspace root with "ALWAYS use ruff not flake8; NEVER touch `legacy_v1/`"; then types "lint and fix the project".
- **What could go wrong**: agent ignores CLAUDE.md (auto-load broken), or loads root only and misses `subdir/CLAUDE.md`, or applies tool rules during compact and the rules disappear.
- **What v5.0.1 plan provides**:
  - Block H row H-18 `getUserContext` CLAUDE.md aggregation (`context.ts:153-189`) — walks parent dirs; v5 auto-loads CLAUDE.md hierarchy.
  - Block A row A-14 POST_COMPACT exclusion list — CLAUDE.md/MEMORY.md NOT re-injected (it's already in system prompt).
  - Block A row A-33 A28 prompt-cache invariant policy — CLAUDE.md is in static prefix; mid-conv changes deferred.
  - Block A row A-40 `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` (`constants/systemPromptSections.ts:1-69`) — CLAUDE.md sits in static side, survives compact.
  - Block I row I-11 `skills/remember/` 4-step review CLAUDE.md/CLAUDE.local.md only.
- **Verdict**: **HANDLED** — but Q4 lock test for "agent reads `subdir/CLAUDE.md` when editing files in subdir" needed in Block H. Currently Block H Q4 only covers `getUserContext` walk; missing per-file-edit re-resolution.

---

## Scenario 9 — Compose .docx report with embedded charts (Block T multi-tool)

- **What user does**: "summarize Q1 claims data as a 10-page Word doc with 4 embedded charts and a TOC."
- **What could go wrong**: docx skill (Anthropic-bundled `docx`) collides with Block T's `create_word`; or chart PNGs get cleaned up before docx embeds them; or 200K-char tool-result-aggregate cap truncates the chart base64 mid-embed.
- **What v5.0.1 plan provides**:
  - Block T row T-1 `create_word` + Block T row T-5 `create_chart` (verbatim v4 ports).
  - Block T row T-11 tool result limits + per-message budget (`constants/toolLimits.ts`) — 200K char per-message tool result aggregate cap (knowing ahead of time, agent sequences charts → embeds → returns rather than batching).
  - Block T row T-10 API limits constants (5MB image / 20MB PDF / 100 pages) — fail-fast client-side.
- **Verdict**: **NEEDS-LOCK-TEST** — Block T Q4 currently lock-tests each tool in isolation; missing the chart→docx round-trip lock test. Add `tests/integration/test_word_chart_embed.py` round-trip.

---

## Scenario 10 — Long search across 50+ files (semantic_search)

- **What user does**: "find every place we compute claim severity to understand the formula spread."
- **What could go wrong**: semantic_search index goes stale during a long task (agent edits files, search hits old hashes), or first-time index build hits exec-limit gate, or user's `legacy_v1/` (CLAUDE.md "NEVER touch") gets indexed anyway.
- **What v5.0.1 plan provides**:
  - Block T row T-3 `SemanticSearch` class verbatim port (v4 `:6461-6610`) — full v4 logic preserved.
  - Block T schema row: `semantic_search` index/search/status actions.
  - Block I row I-1 conditional skills via `paths:` frontmatter — CLAUDE.md exclusion respected via skill-conditional gating.
  - Block C row C-15 BINARY_EXTENSIONS skip — index doesn't pollute on .parquet/.pkl.
- **Verdict**: **NEEDS-LOCK-TEST** — Block T Q4 covers `index→search returns hits`; missing "stale index after edits" reindex trigger test. Also missing CLAUDE.md exclude-glob test.

---

## Scenario 11 — Resume work after 30-min coffee break (cold-cache + microcompact)

- **What user does**: types something at minute 35 after stepping away.
- **What could go wrong**: cache TTL expired, full system prompt re-billed (cost spike PS#3 regression), or agent loses iteration budget context, or kernel was idle-killed by SageMaker.
- **What v5.0.1 plan provides**:
  - Block A row A-16 time-based microcompact (60-min idle clear) (`microCompact.ts:411-530`) — replaces v5's 30-min reactive trigger.
  - Block A row A-18 `sessionActivity` keep-alive during compact — SageMaker kernel idle-timeout protection.
  - Block A row A-37 `cache_ttl: "5m"|"1h"` config knob (Hermes `:1148-1157`) — long-session win.
  - Block A row A-31 `apply_anthropic_cache_control` Bedrock cache application — system prompt + last-3 messages cached.
  - v4 baseline: `COLD_CACHE_THRESHOLD_SECONDS = 30*60` (`:3826`) + cold-cache trigger (`:8923`).
- **Verdict**: **HANDLED** — Block A Q4 lock test "30-min idle → resume → microcompact fires + freed ≥5K tokens" is the canonical PS#3 lock test.

---

## Scenario 12 — Switch model mid-conversation (Sonnet → Haiku for cost)

- **What user does**: clicks model dropdown to switch from Sonnet to Haiku mid-conversation to save cost on bulk file reads.
- **What could go wrong**: thinking-block signature blocks invalidate (Sonnet thinking blocks rejected by Haiku), or cache invalidates but agent doesn't notice and bills full re-read, or per-tool cache-break detection emits false positives for Haiku.
- **What v5.0.1 plan provides**:
  - Block L row L-14 `isExcludedModel` Haiku exclusion (`promptCacheBreakDetection.ts:128-131`) — **MUST** — prevents constant false breaks for Haiku.
  - Block E+F row EF-3 FallbackTriggeredError model switch + `stripSignatureBlocks` (`query.ts:893-953`) — strips thinking sigs cross-model.
  - Block A row A-32 prefix-stable normalization (sorted JSON keys + content strip) (Hermes `:9870-9895`) — 5-15% cache-hit boost survives switch.
  - Block L row L-13 TTL-expiry classification (1h/5min/server-side) — actionable info on switch.
- **Verdict**: **HANDLED** — Q4 lock test in Block L covers "verify hash changes on tool description edit triggers `notifyCacheDeletion`"; need separate "model switch" lock test added.

---

## Scenario 13 — User pastes a 100KB log to debug a crash

- **What user does**: pastes a huge stack trace into chat: "what's wrong here?"
- **What could go wrong**: instant context bloat puts session at 70% trigger, reactive compact fires immediately stripping the log, agent answers about nothing.
- **What v5.0.1 plan provides**:
  - Block A row A-1 `getEffectiveContextWindowSize` + `MAX_OUTPUT_TOKENS_FOR_SUMMARY=20K` — knows budget pre-compact.
  - Block A row A-2 named token budgets (`AUTOCOMPACT_BUFFER=13K, MANUAL=3K`) — leaves headroom.
  - Block A row A-19 compact querySource recursion guards (`compact.ts:1125-1134`) — compact agent can't re-fire tools mid-paste.
  - Block A row A-35 block-on-context-limit pre-API guard (`query.ts:615-648`) — pre-emptive 413 prevention.
  - Block T row T-7 `readFileInRange` (if user pastes filepath instead of content).
- **Verdict**: **NEEDS-LOCK-TEST** — Block A "single huge paste triggers compact" not in Q4 list. Add: `tests/integration/test_large_paste_compact.py` — paste 100KB, assert reactive compact preserves the paste.

---

## Scenario 14 — Sub-agent task: spawn `verify` subagent during long build

- **What user does**: working on multi-file feature; subagent dispatched for `verify` to check no regressions.
- **What could go wrong**: parent's FileCache state leaks to verify subagent (subagent sees stale reads from parent), or verify subagent gets parent's full message history blowing context, or token attribution: subagent cost not split out.
- **What v5.0.1 plan provides**:
  - Block B+ FileCache thread-local context save/restore (v4 `:893-1017`, methods `save_and_clear_context`, `restore_context`, `enter_thread_local_context`, `exit_thread_local_context` at `:975-992+`).
  - Block B+ TokenTracker per-agent attribution (parent_*, subagent_*[type]) — same singleton, both update.
  - Block B+ acceptance test: spawn parent → call sub-agent type=build → assert TOKENS.parent_input_tokens > 0 + TOKENS.subagent_input_tokens["build"] > 0 + cost split.
  - Block G row G-1 `loadAgentMemoryPrompt` per-agent-scoped memory.
  - Block G row G-3 `ONE_SHOT_BUILTIN_AGENT_TYPES` — verify agent skips trailer (token saver).
  - Block G2 `forkSubagent` cache-prefix replay — byte-identical prefix for cache sharing.
- **Verdict**: **HANDLED** — Block B+ acceptance test is exactly this scenario.

---

## Scenario 15 — Approval flow: agent wants to delete 3 files, user approves once for all

- **What user does**: "clean up the old `*.bak` files" — agent finds 12 .bak files, wants to bash-delete them.
- **What could go wrong**: agent dispatches 12 separate approvals (UX nightmare), or rm pattern not in destructive-warning catalog, or always-allow doesn't persist for the next 11 calls.
- **What v5.0.1 plan provides**:
  - Block C+ Approval gate from v4 (`Config.require_tool_approval :1071`, gate at `:9444`, UI at `:9231 + :9448`, pending_approval at `:10306, :10491-10605`).
  - Block C row C-10 `getDestructiveCommandWarning` pattern catalog — `rm -rf`, git push --force, DROP TABLE, kubectl delete, terraform destroy.
  - Block C row C-11 cd+git compound bare-repo fsmonitor guard.
  - Block C+ Q3 note: "Runnable's PermissionDialog richer features (per-tool always-allow + reason-prompt) folded into Block L" — but Block L doesn't actually port PermissionDialog.
  - Block E+F row EF-1 permission-denial tracking surface (`QueryEngine.ts:244-271`) — "3 denials this turn" UI.
- **Verdict**: **POSSIBLE-GAP** — Plan v3 says "Runnable's PermissionDialog... folded into Block L" but SYNTHESIS_MASTER Block L rows L-1..L-28 are all error/retry/cache-break — NO PermissionDialog port. The "approve-once-for-batch / always-allow-this-pattern" UX is described but not in any PORT_LOG row. **Action**: add explicit row to Block C+ for batch-approval + always-allow pattern.

---

## Scenario 16 — Fix a bug across 3 services that share a util

- **What user does**: "fix the timezone bug — it's in `utils/datetime_helpers.py` but propagates to 3 services."
- **What could go wrong**: agent fixes `utils/datetime_helpers.py` then re-discovers each service tool description hash invalidates (Block L cache-break), causing 5x cost spike, or agent forgets which 3 services without checking imports.
- **What v5.0.1 plan provides**:
  - Block L row L-10 full PromptStateSnapshot 12 fields → 8 Bedrock-applicable.
  - Block L row L-15 `writeCacheBreakDiff` for debugging — surfaces the cache break to user.
  - Block L row L-16 `stripCacheControl` + `cacheControlHash` dual hash — detects TTL/scope flips.
  - Block A row A-32 prefix-stable normalization — minimizes invalidation surface.
  - Block T row T-3 SemanticSearch class — finds all 3 callers.
- **Verdict**: **HANDLED** — but Block L Q4 doesn't lock-test "edit-util-causes-cascade-cache-break" specifically. Add lock test: edit shared util, observe ≤1 cache break diagnostic emitted (not 3).

---

## Scenario 17 — Generate a 50-row Excel report from queried data

- **What user does**: "query our `claims_db` for top 50 high-value open claims and write to `report.xlsx` with conditional formatting."
- **What could go wrong**: openpyxl import fails in SageMaker kernel, or file write hits SageMaker EBS write throttle and partial-writes a corrupt xlsx, or 50 rows + 12 columns of formulas blow the per-message tool result aggregate.
- **What v5.0.1 plan provides**:
  - Block T row T-2 `create_excel` (v4 :5730 + schema :7250-7258) — verbatim port; uses openpyxl.
  - Block T row T-11 tool result limits + per-message budget (200K char cap).
  - Block C row C-9 `interpretCommandResult` exit-code semantics — pip install openpyxl exit 0 ≠ "import works".
  - Block J — Real-Bedrock smoke + zip verify ensures `import openpyxl` works in the shipped zip.
- **Verdict**: **HANDLED** — Block T Q4 lock test "create_excel writes expected file" + Block J zip-extract-import gate.

---

## Scenario 18 — Build a new ML pipeline notebook from scratch

- **What user does**: "create `train_pipeline.ipynb` with cells: data load, EDA charts, train/test split, XGBoost train, eval, save model."
- **What could go wrong**: `create_notebook` (T-3 in plan v3) is whole-file create; `notebook_edit` is surgical — agent picks wrong tool and corrupts JSON, or kernelspec/language mismatch.
- **What v5.0.1 plan provides**:
  - Block T row T-1 (synthesis): `notebook_edit` already in v5 (Phase 4) — surgical cell ops.
  - Plan v3 Block T row 4: `create_notebook` (v4 :5838 + schema :7263-7270) — full .ipynb create distinct from `notebook_edit`.
  - Block T Q4: each tool lock-tested for file write.
- **Verdict**: **NEEDS-LOCK-TEST** — Tool selection (whole vs surgical) is an LLM decision; no lock test asserts agent picks `create_notebook` for greenfield vs `notebook_edit` for incremental. Add behavior test in Block K K-6 (no-change-detector tests).

---

## Scenario 19 — Debug a Bedrock invoke that hangs at 90 seconds

- **What user does**: agent calls Bedrock for a long synthesis → 90+ sec, user wants to Ctrl-C.
- **What could go wrong**: Ctrl-C blocked because sync Bedrock call holds GIL, or stale call never times out, or kernel becomes unresponsive.
- **What v5.0.1 plan provides**:
  - Block L row L-21 daemon-thread Bedrock call for Ctrl-C responsiveness (Hermes `run_agent.py:5637-5781`).
  - Block L row L-22 stale non-stream call detector (context-scaled deadline) (`run_agent.py:5704-5762`) — kills hung Bedrock invoke.
  - Block L row L-23 heartbeat callback every 30s — keeps ipykernel alive.
  - Block L row L-24 `_rebuild_anthropic_client` Bedrock branch — defensive client rebuild.
  - Block L row L-25 `invalidate_runtime_client(region)` on stale.
  - Block C row C-17 `combinedAbortSignal` — Python `asyncio.Event`/`contextvars`.
- **Verdict**: **HANDLED** — six L-rows directly target this; Q4 needs explicit "Ctrl-C during 90s Bedrock invoke returns control in <2s" lock test.

---

## Scenario 20 — Review a PR-style diff before commit (`/diffs` + `/regression`)

- **What user does**: types `/diffs summary` to see what's changed in session, then `/regression` for git diff vs HEAD.
- **What could go wrong**: `/diffs` only shows last edit (truncates history), or `/regression` runs `git status` without `--no-optional-locks` triggering Windows fsmonitor lock contention.
- **What v5.0.1 plan provides**:
  - Block D verbatim port: `/diffs [summary|last|<file>]` (`:11200-11242`), `/regression` (`:11243-11275`).
  - Block H row H-19 `getSystemContext` git-status injection memoized + parallel + 2K truncate (`context.ts:36-189`) — uses `--no-optional-locks` Runnable bundled fix.
  - Block C row C-11 cd+git compound bare-repo fsmonitor guard.
- **Verdict**: **HANDLED** — Block D Q4 covers `/diffs` and `/regression` end-to-end.

---

## Scenario 21 — Save session, switch projects, resume next day with full context

- **What user does**: clicks Save → loads session next day → expects open files, agent context, cost-so-far, todos all preserved.
- **What could go wrong**: session reload crashes because tool_use without tool_result mid-pair (atomic save not honored), or cost counter resets, or AGENT_STATUS.md not re-loaded.
- **What v5.0.1 plan provides**:
  - Block B+ SessionManager (`:2578-...`) atomic save/load.
  - Block B+ session_cost_limit enforcement preserved (TokenTracker `:3638-3652`).
  - Block B+ AGENT_STATUS.md auto-load (`_load_persistent_memory + _load_project_status ~:8700-8722`).
  - Block A row A-25 stub-injection for missing tool_results post-compact (also applies post-load).
  - Block H row H-9 `hasToolCallsInLastAssistantTurn` predicate — don't save mid-pair.
  - Block A row A-41 `marble-origami-commit` persist-splice metadata — high-craft compaction-resume pattern.
- **Verdict**: **HANDLED** — Block B+ Q4 lock test "save→load→cost preserved + AGENT_STATUS injected".

---

## Scenario 22 — User wants to undo agent's last 3 file edits (`/revert`)

- **What user does**: agent made 3 edits to fix a bug, user realizes the original was actually correct, types `/revert all --yes`.
- **What could go wrong**: snapshot disk full (SageMaker EBS small), or revert applies in wrong order, or revert touches unrelated edits made manually outside agent.
- **What v5.0.1 plan provides**:
  - Block D verbatim port: `/revert <file>` and `/revert all --yes` (v4 `:10965-11029`).
  - Block B SnapshotManager (`:4418-4509`) + singleton (`:4510`).
  - Block C+ row C+2 file-history snapshot per-edit (`FileEditTool.ts:431-440`) — pre-edit content backup.
  - Block I row I-5 skill discovery on every edit (`FileEditTool.ts:404-423`) — pairs with snapshot.
  - SnapshotManager wires into `tools/edit_file.py`, `tools/write_file.py`, `skills/manager.py:apply_proposal`.
- **Verdict**: **HANDLED** — Block D `/revert` lock test in Q4 + Block B SnapshotManager test covers it; Q4 explicitly checks "diff preview + apply".

---

## Scenario 23 — Compose a PDF with charts using the Anthropic-bundled `pdf` skill collision with Block T `create_pdf`

- **What user does**: "make a 5-page PDF report from the analysis" — but Anthropic ships `pdf` skill AND Block T ships `create_pdf` tool.
- **What could go wrong**: skill activation order picks the wrong path, both fight over which writes the file, or `pdf` skill imports something not allowed in SageMaker (no internet, no pip-install mid-session).
- **What v5.0.1 plan provides**:
  - Block T row T-6 `create_pdf` (v4 :6282 + schema :7299-7305) — uses reportlab; structured sections; works offline.
  - Block I row I-1 conditional skills via `paths:` frontmatter — skill activation is gated.
  - Block I row I-2 `disable_model_invocation` flag — model can't trigger pdf-skill if user-only.
  - Block I row I-3 `enabled_when` skill predicate — CONFIG-flag gates.
  - Constraint #9 of plan: "Drop MCP entirely (single-user SageMaker)" — but Anthropic-bundled skills aren't MCP.
- **Verdict**: **POSSIBLE-GAP** — Plan does not explicitly specify whether `create_pdf` (Block T tool) or external `pdf` skill takes precedence when both available. SageMaker often has no network → reportlab via Block T is correct. **Action**: add Block I disposition note that bundled skills requiring network are auto-disabled in SageMaker; `create_pdf` is canonical PDF path.

---

## Scenario 24 — User asks for a multi-step workflow: clone-style "explore → plan → build → verify"

- **What user does**: types: "explore the codebase, propose a plan to add multi-tenancy, then build it, then verify."
- **What could go wrong**: agent collapses to single `general` agent type and skips the plan phase (PS#7 from memory), or coordinator doesn't know to spawn explore/plan/build/verify subagents in sequence.
- **What v5.0.1 plan provides**:
  - Block G AGENT_TYPES dict (v4 `:6914-7090`) — 7 types including `explore`, `plan`, `build`, `verify`, `simplify`, `general`, `feedback-codex`.
  - Block G row G-3 `ONE_SHOT_BUILTIN_AGENT_TYPES` — explore/plan/verify skip trailer (token saver).
  - Block G row G-4 `getPrompt(isCoordinator)` slim-vs-full prompt — coordinator gets shared block.
  - Block G3 (NEW BLOCK) Coordinator System Prompt (R7 N1 ~258 LOC) — encodes 4 phases (Research → Synthesis → Implementation → Verification), continue-vs-spawn matrix, never-delegate-understanding rule.
  - Block I row I-7 `skills/init/` (CLAUDE.md scaffolder) folds D-8.
- **Verdict**: **HANDLED** — Block G3 is exactly this user's #1 collaboration rule materialized. Q4 lock test for each agent type.

---

## Scenario 25 — Build a frontend prototype in HTML inside the notebook (visual verification needed)

- **What user does**: "make me an interactive HTML dashboard with 4 charts I can preview by opening the file."
- **What could go wrong**: agent writes the HTML but Mermaid syntax breaks (memory rule `feedback_mermaid_syntax`), special chars unescaped in chart labels, OR file written with curly quotes from prompt.
- **What v5.0.1 plan provides**:
  - Block C row C-3 `findActualString` quote normalization.
  - Block C row C-4 `preserveQuoteStyle`.
  - Block C row C-16 `escapeXml` / `escapeXmlAttr` (`utils/xml.ts:1-17`) — Memory/CLAUDE.md may contain `<` or `&`; same logic protects HTML output.
  - Block T row T-1 `create_word` for docx; for HTML there's `create_markdown` (T-7 in plan v3) but no dedicated `create_html` — agent uses `write_file`.
- **Verdict**: **POSSIBLE-GAP** — No dedicated `create_html` tool. v5 will use `write_file` which does string-replace not full-rewrite (Block C). For Mermaid, the user's global rule (`feedback_mermaid_syntax`: no `?$:+/` in node labels) lives in CLAUDE.md → loaded via H-18 → respected. **No new code needed**; flagging that visual verification (Playwright) per global rules is OUT-OF-SCOPE for SageMaker (no browser). Confirms the constraint.

---

## Summary

### Verdict distribution (25 scenarios)

| Verdict | Count | Scenarios |
|---|---:|---|
| **HANDLED** | 16 | 1, 2, 3, 4, 6, 7, 8 (with H Q4 add), 11, 12, 14, 17, 19, 20, 21, 22, 24 |
| **NEEDS-LOCK-TEST** | 6 | 5 (cross-file scope), 9 (chart→docx round-trip), 10 (semantic_search staleness), 13 (large-paste compact), 16 (cache-break cascade), 18 (notebook tool selection), plus implicit Q4 adds in 8/12/19 |
| **POSSIBLE-GAP** | 3 | 15 (batch approval / always-allow), 23 (Block T vs bundled skill precedence), 25 (no `create_html`; flagged as design choice) |

### Key gaps to close before Block 0

1. **Scenario 15 — Batch approval / always-allow**: Plan v3 Block C+ Q3 note references "Runnable's PermissionDialog folded into Block L" but Block L SYNTHESIS_MASTER rows are all error/retry/cache-break. Action: add explicit Block C+ row for batch-approval pattern OR a new Block L row referencing PermissionDialog.tsx specifically.
2. **Scenario 23 — Bundled skill vs Block T tool precedence**: SageMaker offline constraint means several Anthropic-bundled skills (`pdf`, `docx`, `xlsx`, `pptx`) shouldn't run if they require pip-install or network. Action: add Block I disposition note ("if bundled skill imports fail offline, fall through to Block T tool").
3. **Scenario 25 — `create_html` absence**: `write_file` fallback is fine, but explicit acknowledgement that SageMaker has no browser → "visual verification" rule from global CLAUDE.md is OUT-OF-SCOPE. Action: document constraint in Block T or Block J docs (not new code).

### Lock tests to add (6 scenarios → 6 new tests)

| # | Test name | Block | Triggered by |
|---|---|---|---|
| 5 | `test_multifile_scope_completeness.py` — agent confirms each file mentioned in spec is touched | K K-7 | scenario 5 |
| 9 | `test_word_chart_embed_round_trip.py` | T | scenario 9 |
| 10 | `test_semantic_search_stale_after_edit.py` + `test_semantic_search_claudemd_exclude.py` | T | scenario 10 |
| 13 | `test_large_paste_triggers_compact.py` | A | scenario 13 |
| 16 | `test_shared_util_edit_no_cascade_break.py` | L | scenario 16 |
| 18 | `test_notebook_tool_selection_behavior.py` (greenfield→create_notebook, incremental→notebook_edit) | K | scenario 18 |

### Cross-Block confirmation map

Most-relied-on Blocks across the 25 scenarios:
- **Block A** (compact + cache): scenarios 4, 8, 11, 12, 13, 14, 21 — 7 scenarios
- **Block C** (runtime safety + edit utils): 2, 3, 6, 7, 15, 16, 25 — 7 scenarios
- **Block T** (tool surface): 1, 9, 10, 17, 18, 23 — 6 scenarios
- **Block L** (error/retry/cache-break): 7, 12, 16, 19 — 4 scenarios
- **Block H** (memory + context): 4, 8, 20 — 3 scenarios
- **Block G/G3/G2** (subagent + coordinator): 14, 24 — 2 scenarios
- **Block N** (parallel exec): 5, 6 — 2 scenarios
- **Block F2** (auto-continuation): 1, 5 — 2 scenarios

### Bottom-line read

Plan v5.0.1 (post Wave-5-DEEP) covers **64% (16/25) HANDLED, 24% (6/25) needs-lock-test (mechanism present, test missing), 12% (3/25) possible-gap (one mechanism missing or design-decision needed)**. The 3 possible-gaps are all small (one row each); none require a new Block. The 6 needs-lock-test are pure Q4 additions (no LOC change).

For a SageMaker analyst doing realistic multi-file work, the v5.0.1 plan as written would handle the vast majority of workflows correctly; the gaps are edge cases (batch approval UX, skill-vs-tool precedence on offline SageMaker, no-browser visual verification) rather than fundamental architecture holes.
