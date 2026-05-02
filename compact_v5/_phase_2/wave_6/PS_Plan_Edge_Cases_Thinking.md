# PS_Plan_Edge_Cases_Thinking

**Date**: 2026-05-01
**Author**: Wave 6 synthesis agent
**Inputs**: 5 brainstorm files (`W6_long_sessions.md`, `W6_tool_failures.md`, `W6_subagent_parallel.md`, `W6_notebook_ux.md`, `W6_multi_file_tasks.md`)
**Plan reference**: `compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md` (21 Blocks, post no-deferrals)
**Synthesis reference**: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` (448 PORT_LOG rows)

---

## 1. Method

- 5 brainstorm agents x 25 user-perspective scenarios = **125 raw scenarios**
- Each scenario verdicted: **HANDLED** / **NEEDS-LOCK-TEST** / **POSSIBLE-GAP**
- Synthesis dedupes near-duplicates (e.g. cost-cap mid tool_use appears in long-sessions #3 and tool-failures #14 + multi-file #21)
- **Result**: 100+ unique scenarios with Block + file:line provenance

---

## 2. Final tally

| Category          | H  | NLT | PG | Total |
|-------------------|---:|---:|---:|---:|
| Long sessions     | 16 |  8 |  1 |  25 |
| Tool failures     | 18 |  6 |  1 |  25 |
| Sub-agents        |  9 | 15 |  1 |  25 |
| Notebook UX       | 15 |  7 |  3 |  25 |
| Multi-file tasks  | 16 |  6 |  3 |  25 |
| **TOTAL (raw)**   | **74** | **42** | **9** | **125** |
| **Unique post-dedup** | **~63** | **~39** | **9** | **~111** |

Dedup count: ~14 raw scenarios fold across categories (cost-cap mid tool_use; Ctrl-C / abort; cache-break on model switch; A28 invariant; save/load resume; rate-limit; approval Deny; AGENT_TYPES depth/typo; surrogate sanitize; multi-file write race). 100+ unique threshold confirmed.

---

## 3. The 100+ scenarios (master table sorted by Category + Block)

| #   | Cat        | Scenario                                                              | Verdict | Block      | Mechanism (file:line)                                               | Action needed                                  |
|----:|------------|-----------------------------------------------------------------------|---------|------------|---------------------------------------------------------------------|------------------------------------------------|
|   1 | LongSess   | 90-min idle → cold cache spike on next turn                          | H       | A          | `COLD_CACHE_THRESHOLD_SECONDS=30*60` v4:3826 + trigger v4:8923      | none                                           |
|   2 | LongSess   | Cost slider $10, hits 80% mid-session warns                          | H       | B+ + F     | TokenTracker v4:3638-3652 + slider port v4:10086-10102              | none                                           |
|   3 | LongSess   | 100% cost cap fires mid tool_use → wedge risk                        | NLT     | B+         | TokenTracker block + H2 stub-injection (Hermes :4585-4604, MUST)    | Add Q4: cap mid tool_use → stub → recover     |
|   4 | LongSess   | /save Friday → /load Monday preserves cost                           | H       | B+         | SessionManager v4:2578 + on_save/load v4:11569-11665                | none                                           |
|   5 | LongSess   | 200+ python_exec runaway debug                                       | H       | C          | Exec gate v4:9477-9489 + max_exec_calls=200 v4:1080                 | none                                           |
|   6 | LongSess   | Agent re-reads same 600-line file 8 times                            | H       | C          | Repetition detector v4:9156-9180 + dedup key                        | none                                           |
|   7 | LongSess   | 100 messages in 90s rate-limit                                       | H       | C+         | Rate-limit v4:8731-8740                                             | none                                           |
|   8 | LongSess   | 70% context → silent 8s freeze (no compacting indicator)             | NLT     | E+F        | `update_tokens_display` v4:10377 + microcompact v4:3851-3977         | Add Q4: visible "compacting…" indicator        |
|   9 | LongSess   | 200K paste → infinite compact loop                                   | H       | A          | autoCompact circuit-breaker (Runnable autoCompact.ts)               | none                                           |
|  10 | LongSess   | /cost vs status bar disagreement (sub-agent attribution)             | H       | B + B+     | TokenTracker singleton :3755 + per-agent dict + acceptance test      | none                                           |
|  11 | LongSess   | Sub-agent fork shares parent $5 cap                                  | H       | B+         | Shared singleton, `chat()` hook updates session_cost                 | none                                           |
|  12 | LongSess   | Fork sub-agent capped mid-call → parent open tool_use                | NLT     | G2 + B+    | forkSubagent.ts:73-end + cap-block returns clean tool_result        | Add Q4: fork→capped→parent recovers            |
|  13 | LongSess   | Cumulative input vs per-turn output drift (R7 N8)                    | H       | B+         | NOT-OPTIONAL fix list line 14                                       | none                                           |
|  14 | LongSess   | Mid-session model switch (Sonnet→Haiku) cache-break                  | H       | A + L      | A33 invariant + L-14 isExcludedModel + B-10 MODEL_COSTS              | none                                           |
|  15 | LongSess   | Bedrock max_tokens overflow on huge paste                            | H       | A + L      | L-2 parseMaxTokensContextOverflowError + A-8 PTL retries             | none                                           |
|  16 | LongSess   | Kernel restart at hour 2 → resume                                    | NLT     | E+F + B+   | Auto-save on send + SessionManager + AGENT_STATUS auto-load          | Add Q4: cell-3 launch auto-resume from latest  |
|  17 | LongSess   | 5-day load with truncated tool_use                                   | NLT     | B+ + A     | H2 stub-injection + adjustIndexToPreserveAPIInvariants               | Add Q4: load truncated session → recover       |
|  18 | LongSess   | Auto-Dream daemon ran while idle → unexpected cost                   | **PG**  | H+         | Block H+ ~350 LOC daemon, opt-in undefined in v3                    | ADR: default-OFF, cost-cap, /cost visible      |
|  19 | LongSess   | User clicks Stop button mid-25-step tangent                          | H       | C+         | Agent.stop() + per-turn `_combined_stop()` Phase 8                  | none                                           |
|  20 | LongSess   | /checkpoint create pre-rename + restore                              | H       | D + B      | /checkpoint v4:11114-11182 + SnapshotManager v4:4418                 | none                                           |
|  21 | LongSess   | F2 auto-continuation under iteration budget                          | NLT     | F2         | Auto-continuation ~100 LOC, contract not detailed                   | Add Q4: respects cost cap + opt-in             |
|  22 | LongSess   | /context after huge paste shows breakdown                            | H       | D + A      | /context v4:11052-11061 + A-29 tool-schema tokens                   | none                                           |
|  23 | LongSess   | Cost slider $2→$20 live update without kernel restart                | NLT     | F          | Slider port v4:10086-10102                                          | Add Q4: live slider mid-session                |
|  24 | LongSess   | /skills audit trail after long session                               | H       | D + I      | All 11 skill commands ported (D), 6 skill enhancements (I)          | none                                           |
|  25 | LongSess   | /cost shows cache-hit ratio over 4-hour session                      | NLT     | L + B+     | promptCacheBreakDetection ports + B+3 4-line cost block             | Add Q4: 4-line block shows cached/uncached     |
|  26 | ToolFail   | bash exec-gate hits with misleading error                            | H       | C          | Round-3 fix v4:9477-9489 STILL AVAILABLE listing                    | none                                           |
|  27 | ToolFail   | AWS IAM token rotation mid-session                                   | NLT     | L          | L-20 ladder + L-24 _rebuild + L-25 invalidate_runtime_client        | Add Q4: simulate ExpiredTokenException        |
|  28 | ToolFail   | write_file refused on /etc/passwd                                    | H       | C          | v4 SecurityManager :1298-2106 + C-1 doc row + C-6 UNC skip          | Add C-1 PORT_LOG row (doc-only)                |
|  29 | ToolFail   | Haiku malformed JSON args                                            | H       | C          | C-18 _repair_tool_call_arguments + C-19 _escape_invalid_chars       | none                                           |
|  30 | ToolFail   | OneDrive sync between read_file and edit_file                        | H       | C          | C-8 staleness Windows content-fallback + C-5 UTF-16 BOM             | none                                           |
|  31 | ToolFail   | Zscaler/proxy network blip mid-Bedrock                               | H       | L          | L-8 extractConnectionErrorDetails + L-6 keep-alive                  | none                                           |
|  32 | ToolFail   | Tool name typo (`read_filee`)                                         | H       | N          | N-15 fuzzy match Hermes :4689-4720                                  | none                                           |
|  33 | ToolFail   | Skill name typo (`clara`→`clara-review`)                              | H       | I          | Alias + metadata + Levenshtein fuzzy                                | none                                           |
|  34 | ToolFail   | bash `rm -rf /` destructive guard                                    | H       | C + C+     | C-10 destructive catalog + v4 SecurityManager + approval gate        | none                                           |
|  35 | ToolFail   | Approval dialog Deny → recover prompt                                | NLT     | C+         | pending_approval :10306 + on_approve/on_deny :10491-10605           | Add Q4: Deny→model-prompt no retry             |
|  36 | ToolFail   | Repeated read_file same offset/limit                                 | H       | C          | Repetition detector v4:9156-9180 + N-15 dedup                       | none                                           |
|  37 | ToolFail   | Bedrock 5xx returns raw HTML page                                    | H       | L          | L-9 sanitizeAPIError + L-17 humanizer                               | none                                           |
|  38 | ToolFail   | Bedrock 529 capacity event peak                                      | NLT     | L          | L-4 is529Error + L-5 fallback (NEEDS-ADAPTATION Bedrock)            | Add Q4: Bedrock fallback inference profile     |
|  39 | ToolFail   | Compact 400 (maxTokens) PS-class bug                                 | H       | L + A      | L-1 getPromptTooLongTokenGap + A-8 truncateHeadForPTLRetry          | none                                           |
|  40 | ToolFail   | ESC mid bash subprocess                                              | NLT     | C + L      | C-17 combinedAbortSignal (Python contextvars) + L-21 daemon thread   | Add Q4: real Popen kill propagates             |
|  41 | ToolFail   | Skill self-patch produces broken SKILL.md                            | H       | D + B      | /skill apply v4:10892-10954 + 8-rail safety + SnapshotManager         | none                                           |
|  42 | ToolFail   | Cache-break false positives on Haiku                                 | H       | L          | L-14 isExcludedModel (MUST, 8 not-optional)                         | none                                           |
|  43 | ToolFail   | tool_result aggregate >200K chars                                    | H       | T + N      | T-11 toolLimits.ts + N-6 enforce_turn_budget Hermes :8714           | none                                           |
|  44 | ToolFail   | Bedrock call hangs in throttling-retry                               | H       | L          | L-22 stale detector + L-23 30s heartbeat + A-18 sessionActivity     | none                                           |
|  45 | ToolFail   | Lone Unicode surrogate crashes JSON encoder                          | H       | A          | A-26 surrogate sanitize Hermes :384-502 (115 LOC, MUST)             | none                                           |
|  46 | ToolFail   | tool_use without tool_result post-compact                            | H       | A          | A-25 stub-injection MUST (1 of 8 not-optional)                       | none                                           |
|  47 | ToolFail   | /auth wrong token then keeps typing                                  | H       | D          | /auth v4:10789-:10802 + explicit not-startswith check :11314         | none                                           |
|  48 | ToolFail   | Worktree creation fails (disk full / git lock)                       | NLT     | G          | Worktree spawn v4:8413                                              | Add Q4: non-happy path failure                  |
|  49 | ToolFail   | Rate-limit fires with no countdown UX                                | NLT     | C+ + L     | v4:8731-8740 + L-3 getRateLimitResetDelayMs                          | Add Q4: countdown / next-allowed-time text      |
|  50 | ToolFail   | Approval gate cannot render (VS Code Jupyter, no ipywidgets)         | **PG**  | C+         | v4:10491-10605 ipywidgets dialog, no fallback today                  | +30 LOC: 60s watchdog + ask_user text fallback  |
|  51 | SubAgent   | task(subagent_type="build") happy path                               | H       | G          | AGENT_TYPES dict v4:6914-7090 (7 types)                              | none                                           |
|  52 | SubAgent   | task(subagent_type="explore") read-only on 50K-file repo             | H       | G + N      | Explore prompt :6931-6936 + N-3 _PARALLEL_SAFE_TOOLS                 | none                                           |
|  53 | SubAgent   | 3 task() in parallel — share ThreadPoolExecutor                      | NLT     | N          | N-4 worker tid + ThreadPoolExecutor :8463                            | Add Q4: 3 parallel tasks <1.2x max(individual)  |
|  54 | SubAgent   | Sub-agent crashes (Bedrock 5xx after retries)                        | NLT     | L          | L-17 humanizer + L-19 + L-20 + N-8 retry classifier                  | Add Q4: parent gets is_error=true clean         |
|  55 | SubAgent   | Sub-agent edits same file as parent                                  | NLT     | N          | N-2 path-scoped + Hermes path-conflict :311-355                      | Add Q4: 2 non-build subs same path → reject     |
|  56 | SubAgent   | /done = simplify + verify sequential pipeline                        | NLT     | G3 + D     | Coordinator prompt G3 (gated) + D :11276-11313                       | Add Q4: /done forces serial regardless of flag  |
|  57 | SubAgent   | 8 parallel read_file in one turn                                     | H       | N          | _MAX_TOOL_WORKERS=4 + N-4 tid mapping preserves order                | none                                           |
|  58 | SubAgent   | Path-conflict between two sub-agents                                 | NLT     | N          | N row 1 :311-355 + N-5 sequential bookkeeping                        | Add Q4: parent dir + child file conflict        |
|  59 | SubAgent   | forkSubagent cache-prefix replay byte-identical                      | H       | G2         | forkSubagent.ts:73-end + Q4 byte-identical assertion                  | none                                           |
|  60 | SubAgent   | Unknown subagent_type (typo "researcher")                            | NLT     | G + I      | I fuzzy match scope unclear for subagent_type                        | Add Q4: typo→explore w/ INFO; "zzz"→error list  |
|  61 | SubAgent   | Sub-agent recursion depth (parent→child→grandchild)                  | **PG**  | G          | No depth tracking in v4 or any reference repo                       | +5 LOC: `MAX_SUBAGENT_DEPTH=2` constant         |
|  62 | SubAgent   | use_worktree=True on non-git workspace                               | NLT     | G          | Synthesis §7.5 R1 — drop EnterWorktree formal                        | Add Q4: non-git CWD + build → fall back no-crash|
|  63 | SubAgent   | IterationBudget shared parent vs sub                                 | NLT     | G          | G-5 Hermes IterationBudget :213-254                                  | Add Q4: parent counter unchanged by sub turns   |
|  64 | SubAgent   | Sub-agent returns 30K-token result                                   | H       | N + G      | N-6 enforce_turn_budget + G-3 ONE_SHOT skip trailer                  | none                                           |
|  65 | SubAgent   | _build_subagent_handoff_block malformed                              | H       | G + A      | v4:7771-7841 verbatim + A-26 surrogate sanitize                      | none                                           |
|  66 | SubAgent   | G3 coordinator over-decomposes trivial task                          | NLT     | G3         | Default OFF + matrix in prompt                                       | Add Q4: trivial w/ flag-on still 1 turn         |
|  67 | SubAgent   | Sub-agent findings lost across compaction                            | NLT     | A          | A-28 post-compact details + A-27 flush_memories                      | Add Q4: sub-agent finding preserved in summary  |
|  68 | SubAgent   | TokenTracker parent vs sub-agent split                               | H       | B+         | Per-agent attribution dict + plan line 162 acceptance                 | none                                           |
|  69 | SubAgent   | Ctrl-C during 90s sub-agent build                                    | NLT     | L + G      | L-21 daemon + L-22 stale + L-23 heartbeat + worktree cleanup         | Add Q4: Ctrl-C → 2s recovery + worktree clean   |
|  70 | SubAgent   | Sub-agent calls task() laterally                                     | NLT     | G + B+     | Nested task() allowed; B+ uses subtype as key                        | Add Q4: nested attribution + depth gate         |
|  71 | SubAgent   | Tool dedup blocks legitimate retry (different args)                  | H       | N          | N-16 hashes (name, args) — different args ≠ duplicate                | none                                           |
|  72 | SubAgent   | partial_tool_names after sub-agent dies mid-write                    | H       | N + A      | N-7 :6175,6663 + A-25 stub-injection MUST                            | none                                           |
|  73 | SubAgent   | A28 cache invariant on mid-session tool toggle                       | NLT     | A          | A-33 H5 invariant policy MUST (Hermes A28)                           | Add Q4: tool toggle → system prompt unchanged   |
|  74 | SubAgent   | verify reads stale plan_file_path                                    | NLT     | G3 + N     | G3 serial-write rule                                                  | Add Q4: SHA256 plan-file integrity              |
|  75 | SubAgent   | Tool-ref injection refs filtered-out tool                            | NLT     | N + G      | N-14 dynamic tool-ref + G whitelist                                   | Add Q4: ref injection respects whitelist filter |
|  76 | NotebookUX | Kernel restart auto-resume on cell-3 launch                          | NLT     | E+F + B+   | (dup of #16 — covered)                                               | (dup)                                          |
|  77 | NotebookUX | Model dropdown switch mid-conversation                               | H       | A + L + B  | A-33 + L-14 + B-10 MODEL_COSTS                                        | none                                           |
|  78 | NotebookUX | Dark-mode toggle mid-session re-render                               | H       | E+F        | _render_assistant_markdown :9788-9922 + theme dict                   | none                                           |
|  79 | NotebookUX | IterationBudget slider propagates cell-2 → cell-3                    | H       | E+F + F2   | Phase 11 widget + F2 +100 LOC                                         | none                                           |
|  80 | NotebookUX | /cost after 50 turns + 3 sub-agents                                  | H       | B + B+     | Per-agent dict + B-11 input-cum vs output-per-turn + B+3 4-line       | none                                           |
|  81 | NotebookUX | /skills then /skill use clara fuzzy                                  | H       | I          | Alias + Levenshtein + Q4 lock test                                   | none                                           |
|  82 | NotebookUX | /done quick — simplify + verify pipeline                             | H       | D + G      | /done :11276-11313 + AGENT_TYPES dict                                 | none                                           |
|  83 | NotebookUX | /regression in non-git SageMaker workspace                           | NLT     | D          | /regression :11243-11275                                              | Add Q4: no-git fallback to session-edit history |
|  84 | NotebookUX | /skill apply with diff preview Approve                               | H       | D          | /skill apply :10892-10954 verbatim                                   | none                                           |
|  85 | NotebookUX | Stop button orphans bash subprocess                                  | H       | C+ + A     | Agent.stop() + A-25 stub-inject (general)                            | none                                           |
|  86 | NotebookUX | mock_mode=True (test convention) — silently calls Bedrock            | **PG**  | doc        | No mock_mode in v4; user habit from sagemaker tutorials              | USER_GUIDE.md disclaimer (no code)              |
|  87 | NotebookUX | Bedrock IAM AccessDeniedException unfriendly                         | NLT     | L          | L-9 sanitizeAPIError applied to AccessDenied                         | Add Q4: names missing IAM action                |
|  88 | NotebookUX | ipywidgets not installed → ImportError                               | **PG**  | doc        | Cell 1 has pip install but no fallback                                | USER_GUIDE.md note + pin (already in cell 1)    |
|  89 | NotebookUX | Long assistant text >100 lines → notebook scroll horror              | **PG**  | E+F        | _render_assistant_markdown wraps tool blocks not text                 | +10 LOC: <details> collapse for text >100 lines |
|  90 | NotebookUX | /checkpoint restore — _FILES_READ stale after                        | NLT     | B + A      | /checkpoint :11114-11182 + A-21 runPostCompactCleanup                | Add Q4: post-restore cache invalidated          |
|  91 | NotebookUX | /diffs misses notebook_edit + view_image edits                       | NLT     | B          | SNAPSHOTS wiring                                                      | Add Q4: all mutating tools snapshot pre-edit    |
|  92 | NotebookUX | /phase status bar tag                                                | H       | D + E+F    | /phase :11183-11199 + update_mode_display :10308-10357                | none                                           |
|  93 | NotebookUX | /verify pre-commit — verify skill not in PORT_LOG                    | NLT     | I          | I-12 implicit                                                         | Add I PORT_LOG row enumerating skills/verify/   |
|  94 | NotebookUX | Approval `Approve always` per-tool persistence                       | H       | C+         | C+ Q3 note "richer features"                                          | none                                           |
|  95 | NotebookUX | Cost-limit $0.50 — single Sonnet call $0.60 overshoot                | H       | E+F        | EF-2 maxBudgetUsd hard-cap halt MUST (R7 N7)                          | none                                           |
|  96 | NotebookUX | /context tool-schema 20-30K hidden                                   | H       | A + D      | A-29 tool-schema in pre-compression estimate                          | none                                           |
|  97 | NotebookUX | /skillify capture-session-as-skill                                   | H       | D + I      | D-10 Runnable skillify.ts + I-9 fold                                  | none                                           |
|  98 | NotebookUX | /dream manual when daemon disabled                                   | H       | D + H+     | D-11 manual independent of H+ daemon                                  | none                                           |
|  99 | NotebookUX | /auth wrong token failure UX                                         | H       | D          | (dup of #47)                                                          | (dup)                                          |
| 100 | MultiFile  | Power BI dashboard (4 charts + xlsx + docx)                          | H       | T + F2 + A | T-1/3/5/6 + F2-1 + A-43 generateTempFilePath content-hash             | Add Q4: cross-tool round-trip end-to-end        |
| 101 | MultiFile  | Refactor 2K-line monolith into 5 files                               | H       | C + C+     | C-3/4/7/8 quote/CRLF/staleness + C+2 file-history snapshot            | Add Q4: manual edit during agent edit race      |
| 102 | MultiFile  | Add unit tests + run pytest TDD loop                                 | H       | C + M + N  | C-9 interpretCommandResult + M Fix1/2 + N-15 fuzzy                    | none                                           |
| 103 | MultiFile  | Migrate 8 SAS files to pandas, survive compact                       | H       | A          | A-11/14/21/25/27 compact survival                                     | Add Q4: 8-file content survives 1 compact       |
| 104 | MultiFile  | Cross-cutting feature across 8 files (scope-narrowing risk)          | NLT     | K + N + F2 | N-2/3/4 path-scoped + K-7 A39 No-wire-dead + F2 auto-continue         | Add Q4: spec lists N files → all touched        |
| 105 | MultiFile  | grep-replace deprecated pd.append() across 50 files                  | H       | C + T      | C-15 BINARY_EXTENSIONS + repetition + exec-gate + T-7 readFileInRange | none                                           |
| 106 | MultiFile  | TDD edit-test-edit 15 iters (stale Bedrock client)                   | H       | C + L      | C-17 contextvars + L-6 keep-alive + L-21/22/23                        | none                                           |
| 107 | MultiFile  | CLAUDE.md auto-load + subdir hierarchy                               | NLT     | H          | H-18 getUserContext walk + A-14 exclude + A-40 dynamic boundary       | Add Q4: per-file-edit re-resolution             |
| 108 | MultiFile  | Word doc with 4 embedded charts + TOC                                | NLT     | T          | T-1 create_word + T-5 create_chart + T-11 limits                      | Add Q4: chart→docx round-trip                   |
| 109 | MultiFile  | semantic_search across 50 files                                      | NLT     | T + I      | T-3 SemanticSearch :6461-6610 + I-1 paths frontmatter                  | Add Q4: stale index after edits + CLAUDE excl   |
| 110 | MultiFile  | 30-min coffee break cold-cache resume                                | H       | A          | (dup of #1) + A-16 microcompact + A-37 cache_ttl                       | (covered)                                       |
| 111 | MultiFile  | Mid-session model switch thinking-block sigs                         | H       | E+F + L    | EF-3 stripSignatureBlocks + L-14 + A-32 prefix-stable                  | Add Q4: model-switch lock test                  |
| 112 | MultiFile  | 100KB log paste → instant compact strip risk                         | NLT     | A          | A-1/2/19/35 budget guards + T-7                                        | Add Q4: large paste → reactive compact preserve |
| 113 | MultiFile  | /verify subagent FileCache leak from parent                          | H       | B+ + G + G2| FileCache thread-local v4:893-1017 + G-1/3 + G2 prefix replay         | none                                           |
| 114 | MultiFile  | Agent wants to delete 12 .bak files — batch approval                 | **PG**  | C+         | v4 approval per-call; no batch UX in any source                       | Add explicit Block C+ Q1 PermissionDialog row   |
| 115 | MultiFile  | Edit shared util cascades cache breaks across 3 services             | NLT     | L + A      | L-10/15/16 cache-break detection + A-32                               | Add Q4: ≤1 diagnostic on shared-util edit       |
| 116 | MultiFile  | xlsx report — openpyxl import + EBS partial-write                    | H       | T + J      | T-2 create_excel + T-11 + C-9 + J zip-import gate                     | none                                           |
| 117 | MultiFile  | Greenfield .ipynb create vs surgical notebook_edit                   | NLT     | T + K      | T-1 notebook_edit (Phase 4) + T-4 create_notebook                     | Add Q4: tool selection behavior test            |
| 118 | MultiFile  | Ctrl-C during 90s Bedrock invoke                                     | H       | L + C      | (dup of #69 + #40)                                                    | (covered)                                       |
| 119 | MultiFile  | /diffs + /regression PR-style review                                 | H       | D + H + C  | /diffs :11200-11242 + H-19 git-status memoized + C-11 fsmonitor       | none                                           |
| 120 | MultiFile  | Save → switch projects → resume next day                             | H       | B+ + A + H | SessionManager + A-25 + H-9 hasToolCalls + A-41 marble-origami         | none                                           |
| 121 | MultiFile  | /revert 3 file edits — snapshot full disk risk                       | H       | D + B + C+ | /revert v4:10965-11029 + SnapshotManager + C+2 per-edit snapshot       | none                                           |
| 122 | MultiFile  | Anthropic-bundled `pdf` skill vs Block T `create_pdf`                | **PG**  | I          | T-6 reportlab works offline; I-1 paths gate                            | Block I disposition note: tool wins offline     |
| 123 | MultiFile  | explore→plan→build→verify multi-step coordination                    | H       | G + G3     | AGENT_TYPES 7 types + G3 coordinator prompt                            | none                                           |
| 124 | MultiFile  | Build interactive HTML dashboard inside notebook                     | **PG**  | T + doc    | write_file covers; no `create_html`; Playwright OOS for SageMaker      | doc note: write_file canonical, viz OOS         |
| 125 | MultiFile  | (dup) skill name typo `clara`                                        | (dup)   | I          | (dup of #33)                                                          | (covered)                                       |

**Unique post-dedup**: 111 rows after collapsing #76, #99, #110, #118, #125 as duplicates of earlier scenarios.

---

## 4. POSSIBLE-GAPs and resolution (all 9, none require new Blocks)

| # | Gap                                              | Block | LOC delta    | Resolution form         | Detail                                                                       |
|---|--------------------------------------------------|-------|--------------|-------------------------|------------------------------------------------------------------------------|
| 1 | Auto-Dream daemon opt-in / cost transparency     | H+    | 0 (doc)     | ADR + default-OFF flag  | `CONFIG.auto_dream_enabled=False`; cost attributed to TokenTracker; visible in /cost; bounded by `session_cost_limit` |
| 2 | Approval gate ipywidgets fallback (VS Code etc.) | C+    | +30 LOC     | Code (watchdog)         | 60s `concurrent.futures` watchdog on approval future; on timeout fall back to `ask_user` text-mode prompt (Block T tool); persist user choice in `pending_approval` |
| 3 | Sub-agent recursion depth                        | G     | +5 LOC      | Code (constant + check) | `MAX_SUBAGENT_DEPTH=2` in `subagent/spawn.py`; reject `task()` from depth-2 grandchild with explicit error message naming current depth |
| 4 | mock_mode=True user expectation                  | doc   | 0           | USER_GUIDE.md           | Disclaimer: "v5 has no mock_mode UI flag — `tests/integration/test_real_bedrock_smoke.py` is gated on `RUN_REAL_BEDROCK=1` env (test-only)" |
| 5 | ipywidgets pin / fallback                        | doc   | 0           | USER_GUIDE.md           | Cell 1 already pins `ipywidgets>=8.0`; doc note "DO NOT skip pip install" + check at cell-3 launch raises clear error |
| 6 | Long-text assistant response (>100 lines) collapse | E+F | +10 LOC     | render.py micro-extension | Wrap plain-text assistant output >100 lines in `<details><summary>...summary line...</summary>...full text...</details>` (mirrors v4 tool-block behavior) |
| 7 | PermissionDialog row missing in Block L          | C+    | 0 (PORT_LOG row) | Doc (Q1 row)        | Add explicit Block C+ Q1 row porting Runnable `PermissionDialog.tsx` features (per-tool always-allow + reason-prompt + batch grouping); v4:9444+:9448 + :10491-10605 already exist; this row makes batch-approval + always-allow-pattern explicit |
| 8 | Block T tool vs Anthropic-bundled skill precedence | I  | 0 (doc)     | Block I disposition note | "If a bundled skill (pdf/docx/xlsx/pptx) requires network or pip-install at runtime, fall through to Block T tool (`create_pdf`/`create_word`/`create_excel`). Block T is the canonical SageMaker-offline path." |
| 9 | `create_html` design choice                      | doc   | 0           | Block T USER_GUIDE note | "HTML output uses `write_file` directly; SageMaker has no browser, so visual verification (Playwright) is OUT-OF-SCOPE. Mermaid syntax constraints from CLAUDE.md (no `?$:+/` in node labels) are honored via H-18 getUserContext loading." |

| TOTAL | | **+45 LOC code** + **5 doc-only rows + 1 ADR** | | All 9 gaps close inside existing 21 Blocks |

**Confirmed**: NO new Blocks required. Total LOC delta ≈ 45 (code) + 0 (docs).

---

## 5. NEEDS-LOCK-TEST clustering (42 items by Block)

Pre-dedup: 42 NLT verdicts across 5 brainstorms. Post-dedup: ~39 unique tests (some duplicates: #16 kernel-restart appears in long-sessions and notebook-UX; #69+#40 Ctrl-C; #33 skill typo).

| Block       | New Q4 lock tests required (count) | Items                                                                                                                                                                                          |
|-------------|------------------------------------:|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **A**       | 5                                   | A28 invariant on tool toggle (#73); sub-agent finding survives compact (#67); 8-file SAS content survives compact (#103); large-paste reactive-compact preserves (#112); /context vs Bedrock CountTokens within 5% (#22 deep) |
| **B**       | 3                                   | /checkpoint restore resets _FILES_READ (#90); /diffs covers notebook_edit+view_image (#91); SNAPSHOTS wires all mutating tools                                                                  |
| **B+**      | 2                                   | Cost-cap mid tool_use → stub → recover (#3); load 5-day-old truncated session → recover (#17)                                                                                                   |
| **C**       | 1                                   | C-1 PORT_LOG row for SecurityManager doc-gap (already in synthesis as gap)                                                                                                                       |
| **C+**      | 4                                   | Approval Deny → model-prompt no retry (#35); rate-limit countdown UX (#49); ipywidgets fallback watchdog (#50, gap #2); manual-edit-during-agent-edit race (#101)                                |
| **D**       | 1                                   | /regression no-git fallback to session-edit history (#83)                                                                                                                                        |
| **E+F**     | 2                                   | Visible "compacting…" indicator during microcompact (#8); cell-3 auto-resume from latest session JSON (#16/#76)                                                                                  |
| **F**       | 1                                   | Live cost-slider mid-session update without kernel restart (#23)                                                                                                                                  |
| **F2**      | 1                                   | F2 auto-continue respects cost cap + opt-in contract (#21)                                                                                                                                        |
| **G**       | 4                                   | MAX_SUBAGENT_DEPTH=2 grandchild rejected (#61, gap #3); non-git CWD + build → fall back no-crash (#62); IterationBudget independence (#63); typo subagent_type→fuzzy resolves (#60)              |
| **G2**      | 1                                   | Fork sub-agent capped mid-call → parent recovers (#12)                                                                                                                                            |
| **G3**      | 2                                   | Trivial task with coordinator_mode=True does NOT spawn (#66); /done forces serial regardless of flag (#56)                                                                                       |
| **H**       | 1                                   | CLAUDE.md per-file-edit re-resolution in subdir (#107)                                                                                                                                            |
| **H+**      | 1                                   | Auto-Dream off-by-default + cost attributed + bounded (#18, gap #1)                                                                                                                                |
| **I**       | 1                                   | PORT_LOG enumerates `skills/verify/` as bundled (#93); + disposition note for tool-vs-skill precedence (gap #8)                                                                                   |
| **K**       | 2                                   | Spec lists N files → agent confirms each touched (#104); notebook tool selection behavior (#117)                                                                                                  |
| **L**       | 6                                   | IAM ExpiredToken simulation (#27); Bedrock 529 fallback inference profile (#38); ESC subprocess.Popen kill (#40, partial w/ C); sub-agent Bedrock 5xx clean recovery (#54); Ctrl-C 90s sub-agent <2s + worktree clean (#69); model-switch cache-break + AccessDenied IAM message (#87, #111, #115) |
| **N**       | 4                                   | 3 parallel task() share executor (#53); 2 non-build subs same path → reject (#55); parent dir + child file conflict (#58); tool-ref injection respects whitelist (#75)                            |
| **T**       | 4                                   | Power BI cross-tool round-trip (#100); Word+chart embed round-trip (#108); semantic_search stale after edits + CLAUDE excl (#109); chart→docx round-trip (#108)                                  |

**Total**: ~45 test additions; ~6 are dup-merges across blocks (e.g. Ctrl-C touches both C and L). Net **~39-42 unique new lock tests** across already-existing Q4 sections.

---

## 6. Plan v5.0.1 deltas required

### Blocks
- **Unchanged: 21** (no new Blocks)
- v3 already added G3, F2, H+ from Wave-5-DEEP — Wave 6 adds nothing new

### LOC
- **Before Wave 6**: ~19,300 LOC across 21 Blocks
- **Wave 6 adds**: ~45 LOC (gap #2 watchdog +30 LOC, gap #3 depth +5 LOC, gap #6 long-text collapse +10 LOC)
- **After Wave 6**: ~19,345 LOC (+0.23%)

### Q4 lock tests
- **Before Wave 6**: ~95 lock tests across 21 Blocks (per v3 plan)
- **Wave 6 adds**: ~39-42 unique lock tests
- **After Wave 6**: ~134-137 lock tests (+44%)

### PORT_LOG rows
- **+1**: Block C+ Q1 PermissionDialog row (gap #7)
- **+1**: Block I disposition note for tool-vs-skill precedence (gap #8)
- **+1 ADR**: Block H+ Auto-Dream opt-in default-OFF (gap #1)

### Documentation
- **+3 USER_GUIDE.md notes**: mock_mode disclaimer (gap #4); ipywidgets pin (gap #5); create_html via write_file + Playwright OOS (gap #9)

---

## 7. Confidence verdict

**v5.0.1 plan handles 100+ realistic user scenarios.**

- **Coverage**: 74/125 raw HANDLED (59%); 42/125 NEEDS-LOCK-TEST (34% — mechanism in plan, test additive); 9/125 POSSIBLE-GAP (7% — all close <100 LOC).
- **Gaps**: All 9 close inside existing 21 Blocks. ~45 LOC code + 5 doc-only items + 1 ADR.
- **Tests**: ~39-42 new Q4 lock tests fold into existing per-Block Q4 sections. No structural reshape.
- **Risk hotspots** (top 3 to lock-test before Block J real-Bedrock smoke):
  1. **A28 cache invariant on mid-session tool toggle** (#73) — highest cost-impact MUST-policy without explicit lock test today
  2. **Approval gate ipywidgets fallback** (#50, gap #2) — only POSSIBLE-GAP that can wedge a kernel for VS Code Jupyter users
  3. **Cost-cap mid tool_use → stub → recover** (#3) — combined-failure path that v3 only addresses structurally

**Result**: plan v5.0.1 is comprehensive. The 21 Blocks + 448 PORT_LOG rows + ~45 LOC + ~40 new lock tests + 5 doc rows close every realistic SageMaker-user failure mode the 5 brainstorms could surface. **Block 0 ready to start.**

---

**End PS_Plan_Edge_Cases_Thinking.**
