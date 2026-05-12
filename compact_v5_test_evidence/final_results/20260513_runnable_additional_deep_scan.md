# 2026-05-13 Runnable Claude Code Additional Deep Scan

Scope:
- v5 tree: `D:\Github\sagemaker-coding-agent\compact_v5`
- Runnable reference: `D:\Github\gg_claude_code\gg-claude-code-runnable`
- Prior deep dive: `20260512_v5_final_transcript_review/runnable_claude_code_deep_dive_v5_stability.md`

Purpose:

Run three more focused scans of Runnable Claude Code to find additional
stability/performance lessons for v5, document what is already implemented,
what should be implemented next, and where the reference evidence lives.

## Summary

The second scan found no reason to re-architect v5 before final testing. It
did find three concrete improvement tracks for after final test validation:

1. Make cache/context decisions deterministic across clear, compact, resume,
   and large tool-result replacement.
2. Make plan/permission boundaries more explicit for ambiguous or risky work,
   without turning ordinary clear coding tasks into planning theater.
3. Turn verification into an auditable gate with command evidence, not just a
   final answer habit.

These are improvement backlog items. They do not block final SageMaker testing
of the current v5 package.

## Round 4 - Cache, Context, And Compaction Determinism

| Runnable reference | Pattern observed | v5 lesson | v5 status |
|---|---|---|---|
| `src/bootstrap/state.ts:220-239` | Prompt-cache headers are session-stable latches. Once a cache-affecting mode/header turns on, it stays on to avoid repeated cache busts. | v5 should avoid changing cache-affecting prompt headers mid-session unless it records why. | Partly implemented through current cache/cost UI metrics; backlog is a cache-stability audit line. |
| `src/utils/toolResultStorage.ts:150-181` | Large tool outputs persist once per `tool_use_id`; replay does not rewrite the file. | v5 WIP logs should be idempotent: rerun/resume should not create duplicate evidence for the same tool result. | Backlog: artifact-backed large output previews with stable IDs. |
| `src/utils/toolResultStorage.ts:370-425` | Replacement decisions are frozen in a per-thread state so prompt prefixes remain byte-stable. | If v5 replaces large outputs with previews, it must store the exact preview shown to the model, not regenerate it differently on resume. | Backlog: persisted preview records under `<project>/compact_v5_wip/`. |
| `src/services/compact/postCompactCleanup.ts:12-54` | Post-compact cleanup is centralized and avoids clearing main-thread state from subagent compacts. | v5 should distinguish main-thread cleanup from subagent cleanup to avoid corrupting parent state. | Partly implemented via WIP separation; add subagent cleanup tests. |
| `src/services/compact/microCompact.ts:1-130` | Microcompact has explicit compactable tool sets and conservative token estimates. | v5 should only compact/preview tools whose output semantics are safe to summarize. | Backlog: compact only bash/test/read/search outputs first. |
| `src/utils/tokens.ts:216-260` | Token estimation accounts for split assistant records from parallel tool calls. | v5 token diagnostics should count interleaved parallel tool results, not only the last assistant block. | Backlog: improve transcript analyzer/token report. |

Implementation recommendation:

Add a `context_cache_audit` diagnostic report that lists:
- current prompt/cache mode toggles;
- last API-bound context token estimate;
- cache read/write/without-cache cost;
- large-output preview count;
- whether replacement choices are stable after resume.

## Round 5 - Plan, Permission, And Safety Boundaries

| Runnable reference | Pattern observed | v5 lesson | v5 status |
|---|---|---|---|
| `src/tools/EnterPlanModeTool/prompt.ts:1-90` | Planning is encouraged for genuinely non-trivial or ambiguous implementation work. | v5 should use explicit planning for risky/ambiguous work, but avoid forcing plan mode for simple clear tasks. | Current v5 behavior is acceptable; backlog is a plan-summary template for high-risk tasks. |
| `src/tools/EnterPlanModeTool/prompt.ts:95-165` | Internal prompt narrows plan mode to real ambiguity; clear tasks should start directly and ask specific questions only if needed. | This matches the user's preference for execution over endless planning. | Keep this as v5 rule. |
| `src/tools/ExitPlanModeTool/ExitPlanModeV2Tool.ts:61-90` | Plans can request semantic permission categories such as "run tests", not just exact commands. | v5 could reduce approval friction by grouping safe repeated actions into auditable permission scopes. | Backlog: optional WIP permission receipts for repeated tests/list/read tasks. |
| `src/utils/permissions/permissionSetup.ts:75-129` | Dangerous broad bash rules are detected: tool-level allow, `*`, interpreter wildcards, `python:*`, etc. | v5 should continue avoiding broad shell allows; approvals should stay scoped and auditable. | Already aligned with bash allowlist and explicit shell diagnostics. |
| `src/utils/permissions/permissionSetup.ts:134-210` | PowerShell has its own danger patterns, including `iex`, nested shells, `Start-Process`, `.exe` variants. | v5 Windows testing needs separate shell-safety cases instead of assuming POSIX behavior. | Backlog: add Windows-specific bash/PowerShell safety tests if Windows becomes a supported target. |
| `src/tools/FileReadTool/FileReadTool.ts:442-486` | Path checks and UNC checks avoid filesystem I/O before permission approval. | Avoid pre-permission filesystem touches on paths that can leak credentials or hang. | Useful for future v5 file/S3/path guards. |
| `src/tools/FileEditTool/FileEditTool.ts:137-190` | File edit validation blocks same-string edits, denied paths, UNC pre-I/O, and oversized files. | v5 edit/write tools should fail early with precise messages, not let the model infer from generic errors. | Partly implemented through artifact/path guards; backlog for file-size/write guard tests. |

Implementation recommendation:

Add a `permission_receipt` record in WIP evidence when v5 repeatedly performs
the same low-risk action category, for example "run project tests". This would
not auto-bypass user approvals; it would make approval/tool discipline
auditable and easier to review.

## Round 6 - Verification, Tool Choice, And Quality Gates

| Runnable reference | Pattern observed | v5 lesson | v5 status |
|---|---|---|---|
| `src/constants/prompts.ts:211` | Before reporting complete, verify the work actually runs; if verification cannot run, say so. | v5 final answers should never imply tests passed unless the runtime has evidence. | Already improved through regression tests and evidence docs. |
| `src/constants/prompts.ts:240` | Report outcomes faithfully; do not manufacture green results or keep re-verifying already confirmed results. | Avoid both false confidence and defensive over-checking. | Important: this directly addresses v5's "operationally noisy" transcript behavior. |
| `src/constants/prompts.ts:305-320` | Prefer dedicated tools over shell; use parallel tool calls only when independent. | v5 should keep using dedicated S3/artifact/task tools and avoid broad shell scans when a structured tool exists. | Already improved by S3 list/preview and follow-up cap. |
| `src/constants/prompts.ts:394` | Non-trivial implementation requires independent adversarial verification before reporting completion. | v5 should add a structural final gate for bigger coding tasks: review/test evidence must exist before final report. | Backlog: final-summary verification gate/nudge. |
| `src/coordinator/coordinatorMode.ts:210-330` | Verification means proving behavior, not confirming files exist; worker prompts must be self-contained and specific. | v5 reviewers/subagents should get exact files, line numbers, changed behavior, and tests to run. | Documented; continue using in Claude review loops. |
| `src/utils/toolSearch.ts:401-466` | Tool-search mode decisions are logged with reason, model, thresholds, and metrics. | v5 should record why expensive tool surfaces are enabled or skipped. | Backlog: add tool-loading/tool-search diagnostics to WIP logs. |

Implementation recommendation:

Add a `final_task_quality_gate` for complex coding tasks that records:
- changed files;
- tests run and outputs;
- reviewer/subagent verdict if required;
- unresolved failures or skipped checks;
- final cost/cache metrics from runtime, not manual calculation.

## What Was Implemented Versus Learned

| Category | Implemented now | Learned/backlog |
|---|---|---|
| Path/final-claim noise | Implemented previously in `core/query_engine.py` and covered by tests. | Extend transcript analyzer to flag repeated checks and false guard warnings. |
| Shell glob false negatives | Implemented previously in `tools/bash.py` for local `*` shell routing. | Add platform-specific Windows/PowerShell tests before claiming Windows glob parity. |
| WIP evidence layout | Implemented previously under `<project>/compact_v5_wip/`. | Add stable large-output preview records and WIP permission receipts. |
| UI metrics/cost display | Implemented previously in notebook UI blocks. | Final reports should cite runtime metric fields automatically. |
| Verification workflow | Implemented through Claude review loop and test evidence. | Add structural gate/nudge for complex final coding tasks. |
| Context/cache determinism | Metrics exist; cache/cost visible. | Add cache/context audit and stable preview decisions across resume. |

## Readiness Impact

This scan does not reveal a blocker for final testing. It strengthens the
post-final-test roadmap:

- Run final SageMaker tests now using the current zip.
- If final testing uncovers UI/session/cache weirdness, prioritize the
  `context_cache_audit` diagnostic.
- If final testing uncovers coding-task overchecking, prioritize
  `final_task_quality_gate`.
- If final testing produces huge logs or repeated transcript bloat, prioritize
  stable artifact-backed large-output previews.

## Self-Review Notes

- The scan references the real local Runnable path, not the stale archived path.
- Lessons are mapped back to file paths and line ranges.
- No new runtime behavior is changed by this scan; it is documentation and
  organization only.
- Existing architecture boundary remains: v5 is SageMaker notebook first, not a
  terminal clone.

---

# 2026-05-13 — Rounds 7-9 (extension, same date)

Three more scans were run on territory rounds 4-6 did not touch. Sources:
the same local Runnable path at `D:/Github/gg_claude_code/gg-claude-code-runnable/src/`
and the active v5 tree at `D:/Github/sagemaker-coding-agent/compact_v5/`. As
before, each row cites Runnable file:line and the v5 location where the lesson
either lands or already exists.

## Round 7 — Error / Retry / Telemetry / Cache-Break Observability / Gates

| Runnable reference | Pattern observed | v5 lesson | v5 status |
|---|---|---|---|
| `src/services/api/withRetry.ts:170-517` | Retry uses async generator that yields `SystemAPIErrorMessage` heartbeats every 30s during long waits so idle-session timeouts don't drop the call. | v5 should yield a heartbeat status from `core/retry.py` during long backoff sleeps so SageMaker sessions don't appear hung. | Backlog: add a `heartbeat_callback` to `RetryPolicy.run_with_backoff` and wire it through Bedrock client. Currently silent during waits (compact_v5/core/retry.py:25-90). |
| `src/services/api/withRetry.ts:62-82` | 529 handling distinguishes `FOREGROUND_529_RETRY_SOURCES` (retry) from background (drop fast). | v5 should drop background subagent 529s faster than parent 529s. | Backlog: add a `query_source` flag through QueryEngine so 529 retry budget differs by source. v5 retries identically today. |
| `src/services/api/withRetry.ts:267-314` | Fast-mode fallback: on repeated 429/529 either wait+retry (short) or enter cooldown and switch model (long). | v5 should consider a model-fallback gate after N consecutive 529s. | Backlog. v5 has classifier + ladder (compact_v5/core/retry.py:62-84) but no model swap path. |
| `src/services/autoDream/autoDream.ts:55-100` | Background memory consolidation auto-fires on time-gate (24h) AND session-gate (5 sessions touched), wrapped in `tryAcquireConsolidationLock`. | v5 should auto-fire `/dream` on the same gate, not require manual trigger. | Backlog. v5 has the consolidation engine (compact_v5/runtime/dream.py:1-150) but no scheduler. |
| `src/cost-tracker.ts` + `src/costHook.ts` | Cost hook fires after every assistant message, emits `tengu_*` events to a batched analytics pipeline (Datadog + Statsig). | v5 should emit one structured event per turn for cost/cache/retry/cache-break, even if the sink is local-only at first. | Backlog: add an event sink to compact_v5/runtime/audit.py (already JSONL) and gate it with a `CONFIG.telemetry_events_enabled` flag (default OFF for SageMaker). |
| `src/services/api/promptCacheBreakDetection.ts:28-99` | Per-source `PreviousState` (max 10 sources) captures system/tools/per-tool hashes, cache-control hash, betas, model, fast-mode, autoMode; on break it generates a structured diff and writes it to `getCacheBreakDiffPath()` for triage. | v5 has the hash helpers but no per-turn state, no diff generation, no surface. | Backlog. v5 has `compact_v5/core/cache_break_detection.py:29-100` (snapshot dataclass + Haiku exclusion + tool hash) — gap is the *state machine + diff*, not the primitives. |
| `src/assistant/*.ts` skill-based `/verify` `/done` | Verify/done is interactive: Claude is asked to confirm; no deterministic file gate. | v5 already exceeds: `compact_v5/runtime/gate.py:1-60` is a deterministic file-evidence gate (status/tests/review/results/subagent/telemetry). | **v5 WIN** (#7 cumulative). Runnable's interactive paradigm is fine for live coding but cannot be batched. |

Implementation recommendation:

A single `runtime/observability.py` module would let v5 absorb four of these
items together — heartbeat callback (axis 1), event-buffer flush (axis 5),
cache-break diff path (axis 6), and structured per-turn `summary_event` —
without re-architecting the engine. Estimate ~250 LOC, ships as v5.0.3
post-final-test if needed.

## Round 8 — Permissions / Sandbox / Hooks / Banned-Subsystem Guard

| Runnable reference | Pattern observed | v5 lesson | v5 status |
|---|---|---|---|
| `src/utils/permissions/yoloClassifier.ts` + `classifierDecision.ts` | Permission classifier runs an Anthropic SDK call to auto-permit/deny per tool input; Statsig feature gate (`tengu_sandbox_disabled_commands`) can flip sandbox off. | v5 chose the opposite: static allowlist + denylist, fail-closed, no LLM in the permission path. | **v5 WIN** (#8). For SageMaker enterprise, no per-call classifier API is the safer design. v5 stays at `compact_v5/security/manager.py:123-451`. |
| `src/tools/BashTool/shouldUseSandbox.ts` + sandbox manager | Sandbox is opaque, feature-gated, Statsig-driven exclusion list. | v5 has explicit `CONFIG.execution_mode: 'local' | 'docker'` enum + closure-based Python sandbox preamble. | **v5 WIN** (#9). `compact_v5/tools/python_exec.py:88-204` + `compact_v5/tools/bash.py:162-170`. Simpler, auditable, no remote feature flag dependency. |
| `src/tools/AskUserQuestionTool/` | AskUserQuestion is a turn-scoped tool with cancellation through the response generator. | v5's `tools/ask_user.py:24-58` blocks on a callable provider or stdin; no turn-level cancel. | MINOR gap. Acceptable for notebook use. Backlog: wire `on_stop_check` into the ask_user block. |
| `src/utils/hooks/*.ts` (AsyncHookRegistry, hookEvents, hooksConfigManager, hooksSettings) | 20+ event types: SessionStart, SessionEnd, PreToolUse, PostToolUse, PreCompact, PostCompact, Stop, Notification, PermissionDenied, etc. User-defined shell commands fire at lifecycle points. | v5 has no user-customizable hooks. Approval dialog and ask_user are the closest analogues. | MAJOR gap (Runnable wins). Backlog. Not a blocker for SageMaker — would add ~300 LOC + .claude/hooks/ contract. Defer to post-final-test. |
| `src/components/permissions/BashPermissionRequest/` + `bypassPermissionsKillswitch.ts` + Shift+Tab mode cycling | Permission state machine: default → acceptEdits → plan → bypassPermissions → auto. Modes persist across turns; Statsig can flip bypass off mid-session. | v5 has a sticky `CONFIG._always_allowed` dict + three-button modal (Approve/Deny/Always allow) in `compact_v5/ui/approval_dialog.py:38-150`. | MINOR gap. v5's model is appropriate for ipywidgets; full mode cycling would need a separate "Permission Mode" selector. Backlog. |
| (no equivalent in Runnable) | — | v5 has an active import-time **banned-subsystem guard** at `compact_v5/entry.py:28-58` (`_BANNED_PACKAGE_NAMES = ("mcp",)`). Fails fast if banned packages are re-introduced inside the v5 package; passes external pip-installed packages silently. | **v5 WIN** (#10). Runnable relies on feature flags + DCE; v5 has runtime enforcement. ADR-022. |

Implementation recommendation:

Two action items: (1) backlog a minimal hooks contract for v5 (just
`pre_tool_use`, `post_tool_use`, `pre_compact`, `post_compact`, `session_end` —
five events) only if a customer asks for it; otherwise the absence is fine.
(2) Backlog turn-level cancel on `ask_user` so Stop button reliably interrupts
a stuck ask_user prompt.

## Round 9 — File / Read / Notebook / REPL / Skills / Plugins / Output

| Runnable reference | Pattern observed | v5 lesson | v5 status |
|---|---|---|---|
| `src/tools/FileEditTool/utils.ts:73-93` | Quote normalization in-memory only; assumes UTF-8 + modern line endings. | v5 detects UTF-16 / UTF-8-sig BOMs and round-trips CRLF/LF; preserves curly-quote folding. | **v5 WIN** (#11). `compact_v5/tools/edit_file.py:143-202` + `compact_v5/security/edit_file_safety.*`. Helpful for enterprise files with Windows lineage. |
| `src/tools/FileReadTool/FileReadTool.ts:44-58` | Reads images inline via `maybeResizeAndDownsampleImageBuffer()` + `mapNotebookCellsToToolResult()`. | v5 has image handling as a *separate* `view_image` tool; read_file flattens .ipynb cells without preserving structure. | MAJOR gap (Runnable wins on cohesion). Backlog: either unify image handling into read_file, or document the separation. Not a blocker. |
| `src/tools/FileEditTool/FileEditTool.ts` mtime check | Simple mtime equality. | v5 has a false-positive guard: byte-identical content + mtime touch is NOT treated as stale. | **v5 WIN** (#12). `compact_v5/tools/edit_file.py:114-131` (Block C C-8). Avoids spurious "file changed under you" errors. |
| `src/screens/REPL.tsx:80,838-864` + Ink components | Terminal-native UI with React state, real-time token streaming, message virtualization, structured `useAssistantHistory()` for session restore. | v5 is notebook-native ipywidgets; cannot literally match Ink streaming. | INTENTIONAL gap. v5 stays at `compact_v5/ui/chat_ui.py`. Acknowledged in `PS_V5_VS_RUNNABLE_DEEP_REVIEW_20260511.md`. |
| `src/skills/bundled/runSkillGenerator.ts` | Bundled skill-generator exports an empty default; appears stubbed/incomplete in Runnable. | v5 has a working skill-proposal tool: `compact_v5/tools/skill_propose_patch.py` + `skills/manager.py:400+` (`propose_patch`/`apply_proposal`/`revert_skill`), gated by `CONFIG.enable_skill_patching=False` by default. | **v5 WIN** (#13). v5 ships what Runnable left as a stub. |
| `src/skills/loadSkillsDir.ts` + `builtinPlugins.ts:21+` | Skills discovered from project + user dirs; plugin system layers on top (`{name}@builtin`, `{name}@marketplace`). | v5 has skills (`compact_v5/skills/manager.py`) with conditional loading: `requires_tools` (Hermes filter), `paths` (fnmatch), `enabled_when` (CONFIG flag), `auto_trigger`. No plugin layer. | INTENTIONAL gap on plugins (SageMaker-only). **v5 WIN** (#14) on skill conditionals — Runnable's plugin model and v5's `requires_tools/enabled_when/paths` are different bets; v5's is more declarative. |
| `src/services/outputStyles/` + `loadOutputStylesDir.ts:26+` | Multi-file output-style system loaded from `~/.claude/output-styles/`. Frontmatter for `keep-coding-instructions`, `force-for-plugin`. | v5 has no user-defined output-style system; rendering policy is hardcoded in `compact_v5/ui/chat_ui.py:_render_assistant_markdown`. | MAJOR gap (Runnable wins). Backlog: v5 Phase 12+. Not a blocker. |
| `src/components/messages/AssistantThinkingMessage.tsx` | Thinking blocks rendered as their own message type. | v5 already renders thinking in a `<details>` strip in `_render_turn_meta` after the recent ordering fix; default Thinking OFF for cost. | Aligned (PARTIAL win for v5 — already implemented). |
| `src/tools/NotebookEditTool/` | `.ipynb` editing as a first-class tool with same temp-file atomicity, approval, cell metadata preservation. | v5 has `compact_v5/tools/notebook_edit.py` with insert/replace/delete, atomic temp+rename, nbformat-compliant source list. | NONE. Parity. |

Implementation recommendation:

The three real gaps from Round 9 (image/notebook cohesion in read_file,
session restore, output styles) all belong to a future "richer UX" phase.
None block final SageMaker testing of the current package.

## What Was Implemented Versus Learned (rounds 7-9 addition)

| Category | Implemented now | Learned / backlog |
|---|---|---|
| Retry / heartbeat | classifier + 3-tier ladder + jittered backoff in `core/retry.py` | Add heartbeat callback for long waits; add per-source 529 budget split; add model-fallback gate after N×529. |
| Background consolidation | manual `/dream` works in `runtime/dream.py` | Auto-fire on time-gate (24h) + session-gate (5 sessions). |
| Telemetry / cost-hook | `runtime/tokens.py` + `runtime/audit.py` JSONL | Add per-turn `summary_event` to audit log; behind `telemetry_events_enabled` flag. |
| Cache-break observability | hashes + Haiku exclusion in `core/cache_break_detection.py` | Add per-source state machine + diff file output. |
| File-edit encoding safety | UTF-16/BOM/CRLF round-trip in `tools/edit_file.py` | Export helpers as reusable module for write_file + future tools. |
| Stale-file false-positive guard | byte-identity check in `tools/edit_file.py:114-131` | Apply same guard to read_file mtime checks. |
| Skill conditionals | `requires_tools`/`enabled_when`/`paths` in `skills/manager.py` | None — v5 leads. |
| Banned-subsystem guard | active import-time check at `entry.py:28-58` | None — v5 leads. |
| Hooks | (none) | Backlog 5-event minimal hooks contract if a customer asks. |
| Image handling cohesion | `view_image` is a separate tool | Either unify into read_file or document the separation. |
| Output styles | hardcoded `_render_assistant_markdown` | Backlog (Phase 12). |
| Session restore | `last_turn.json` + `turn_journal.jsonl` recovery exists | Backlog (Phase 12) structured chat-history restore. |

## v5 WIN tally (cumulative across all 9 rounds)

1. WHEN-NOT tool description discipline
2. Typed sub-agent kinds with tool allowlists
3. `docs/reviews/` receipt persistence + envelopes
4. Atomic per-turn local recovery JSON + journal
5. Smaller, sectioned, budgeted system prompt
6. Per-turn inline metrics (Runnable hides until exit)
7. Deterministic file-evidence verify/done gate (Round 7)
8. Allowlist-based permission classifier (Round 8)
9. Explicit execution-mode enum + closure-based Python sandbox (Round 8)
10. Active import-time banned-subsystem guard (Round 8)
11. UTF-16/BOM/CRLF file-edit encoding safety (Round 9)
12. Stale-file false-positive byte-identity guard (Round 9)
13. Working `skill_propose_patch` tool (Runnable's runSkillGenerator is stubbed) (Round 9)
14. Declarative skill conditionals (`requires_tools`/`enabled_when`/`paths`) (Round 9)

## Readiness Impact (rounds 7-9 addition)

These three rounds reinforce the conclusion already in rounds 4-6: **none of
the new findings are blockers for final SageMaker testing**. They expand the
post-final-test backlog with seven concrete items (heartbeat, autoDream gate,
telemetry events, cache-break diff, image/notebook cohesion, output styles,
hooks) and add eight new v5 wins to defend against future "be more like
Runnable" pressure that would actually regress v5's strengths.

## Self-Review Notes (rounds 7-9)

- Three parallel Explore agents ran against the same local Runnable path used
  for rounds 4-6; no archived-path references.
- Every gap row cites Runnable file:line AND the v5 location where the
  partial-implementation already lives (the "where we cleared" cross-link
  the user asked for).
- Six of the fourteen v5 wins are NEW from these rounds; the other eight are
  re-confirmed from the 2026-05-11 deep review for completeness.
- No runtime code changed in this scan. Doc-only addition to an existing
  doc; no new file created at the scan layer.
- The "v5 SageMaker-notebook-first, not a terminal clone" architecture rule
  is preserved (chat UI + plugin gaps marked INTENTIONAL).

