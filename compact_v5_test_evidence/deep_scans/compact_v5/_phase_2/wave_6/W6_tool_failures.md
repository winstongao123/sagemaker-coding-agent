# W6 — User-Perspective Brainstorm: Tool Failures + Error Recovery + Safety Gates

**Author**: user-perspective sim agent
**Date**: 2026-05-01
**Scope**: 25 realistic scenarios a SageMaker user could hit while running v5 chat.ipynb. For each, I check whether the v5.0.1 plan (`V5_PHASE_2_PLAN_v3.md` + `SYNTHESIS_MASTER.md` + `CONFIDENCE_REPORT.md`) provides a concrete mechanism, and whether that mechanism actually closes the user-visible failure.
**Sources used**:
- Plan: `compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md`
- Synthesis: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md` (Blocks C, C+, L, A, N especially)
- v4 baseline: `compact_v4/MAIN/agent/sagemaker_agent.py`

Verdict legend:
- **HANDLED** = a specific plan row + file:line provides the user-visible recovery the scenario needs.
- **NEEDS-LOCK-TEST** = mechanism exists in plan but the user-visible behavior depends on a Q4 lock-test that has not yet been written / verified end-to-end.
- **POSSIBLE-GAP** = plan does not concretely cover this user-visible failure mode, OR the planned mechanism is too low-level to be reliably user-visible.

---

## Scenarios

### 1. Bash command runs past `max_exec_seconds_per_session` mid-session, then hits per-session limit
- **What user does**: long `pytest` or model fine-tune kicks `bash` past the 200-call / time-budget cap.
- **What could go wrong**: model gets a generic "Blocked" and re-emits the exact same `bash` call in a tight loop, burning Bedrock cost and hiding the real fix-path from the user.
- **What v5.0.1 plan provides**: Block C ports v4's exec-limit gate at `compact_v4/MAIN/agent/sagemaker_agent.py:9477-9489` (V4.10.10 round-3 misleading-error fix — explicit "STILL AVAILABLE" tool list pointed at read_file/grep/edit_file FIRST). Plan ref: `V5_PHASE_2_PLAN_v3.md` §"Block C", LOC 250.
- **Verdict**: HANDLED.

### 2. AWS credentials expire mid-session (SageMaker IAM token rotation)
- **What user does**: user kicks off a long compact + sub-agent fan-out around the 1-hour mark; the role token rotates.
- **What could go wrong**: every subsequent Bedrock `converse` raises `ExpiredTokenException` and the agent retries forever or surfaces a raw boto3 stack trace to the chat HTML.
- **What v5.0.1 plan provides**: Block L L-20 "Three-tier recovery ladder pattern (retry → IAM token refresh → user-error)" from Hermes `run_agent.py:5528-5610` (NEEDS-ADAPTATION). Plus L-24 `_rebuild_anthropic_client` Bedrock branch at Hermes `run_agent.py:5617-5635` and L-25 `invalidate_runtime_client(region)` at `:5685, 5938-5941`. SYNTHESIS_MASTER §"Block L".
- **Verdict**: NEEDS-LOCK-TEST. Plan adopts the ladder but L-20 is "0 LOC architectural" — the actual rebuild path (L-24/L-25) needs an integration test that simulates an `ExpiredToken` mid-call.

### 3. `write_file` refused because path is `/etc/passwd` (or `C:\Windows\System32`)
- **What user does**: model decides to "back up" config and writes to `/etc/passwd`.
- **What could go wrong**: silent crash, or worse, actual write attempt with a stack trace.
- **What v5.0.1 plan provides**: v4 SecurityManager class at `compact_v4/MAIN/agent/sagemaker_agent.py:1298-2106` already in v5 Phase 5 (SYNTHESIS_MASTER C-1 "FALSE-POSITIVE-DOC-GAP — needs explicit row"). Block C will add a PORT_LOG row but the gate already exists. C-6 also adds Windows UNC-path skip at Runnable `FileEditTool.ts:179-181` for NTLM credential leak class.
- **Verdict**: HANDLED (v4 SecurityManager covers this); needs the C-1 doc row so the test exists.

### 4. Model returns malformed JSON for tool args (Haiku-class glitch)
- **What user does**: routine `edit_file` call.
- **What could go wrong**: boto3 JSON decoder raises and the whole turn dies; user sees stack trace not a recovery message.
- **What v5.0.1 plan provides**: Block C C-18 multi-pass JSON repair `_repair_tool_call_arguments` from Hermes `run_agent.py:547-641` (95 LOC, **HIGH-MUST**). Plus C-19 `_escape_invalid_chars_in_json_strings` at Hermes `run_agent.py:505-544` (40 LOC). Synthesis explicitly notes "Bedrock Claude (esp. Haiku) emits malformed args; `{}` fallback better than crash."
- **Verdict**: HANDLED.

### 5. File user is editing changes on disk between `read_file` and `edit_file` (OneDrive sync, antivirus mtime bump)
- **What user does**: model reads `agent.py`, plans an edit, OneDrive syncs the file in the background, then `edit_file` runs.
- **What could go wrong**: stale-content overwrite that destroys the synced changes.
- **What v5.0.1 plan provides**: Block C C-8 "Staleness check Windows content-fallback for OneDrive/AV mtime bumps" from Runnable `FileEditTool.ts:289-311` (15 LOC, HIGH, "Real Windows fix"). Pairs with C-5 UTF-16 LE BOM detection at Runnable `FileEditTool.ts:208-214` for Notepad-saved files.
- **Verdict**: HANDLED.

### 6. Network blip mid-Bedrock call (Zscaler/corp-proxy reset)
- **What user does**: types a normal message during a corp-VPN reconnect.
- **What could go wrong**: `requests`/`botocore` SSL error surfaces as a raw `ConnectionResetError` and user gets no retry.
- **What v5.0.1 plan provides**: Block L L-8 `extractConnectionErrorDetails` SSL error walk + hint at Runnable `errorUtils.ts:42-100` (80 LOC, HIGH — explicitly "Corp Zscaler/proxy fixes"). L-6 stale-connection + keep-alive disable on retry at Runnable `withRetry.ts:112-118` (30 LOC). L-22 stale non-stream call detector with context-scaled deadline from Hermes `run_agent.py:5704-5762`.
- **Verdict**: HANDLED.

### 7. Tool the model wants doesn't exist (typo: `read_filee`)
- **What user does**: routine prompt — model hallucinates a tool name.
- **What could go wrong**: tool dispatcher returns "no such tool" and model loops trying variants.
- **What v5.0.1 plan provides**: Block N N-15 "Fuzzy tool-name matching" from Hermes `run_agent.py:4689-4720` (~30 LOC, already in plan). Reuses the same Levenshtein helper as Block I skill resolution.
- **Verdict**: HANDLED.

### 8. Skill name typo (`clara` vs `clara-review`)
- **What user does**: types `/skill use clara`.
- **What could go wrong**: dispatcher hard-fails; user gets "skill not found" and gives up.
- **What v5.0.1 plan provides**: Block I (50 LOC). Plan ref: `V5_PHASE_2_PLAN_v3.md` §"Block I" — alias-resolve directory + metadata `name:` + Hermes fuzzy match (`run_agent.py:4689-4720`). Q4 lock test: `/skill activate clara` resolves to `clara-review`; `/skill activate verfy` resolves to `verify`.
- **Verdict**: HANDLED.

### 9. `bash` command tries to `rm -rf /` (or `git push --force` to main)
- **What user does**: model overconfidently runs cleanup.
- **What could go wrong**: data loss before any approval gate fires.
- **What v5.0.1 plan provides**: Block C C-10 `getDestructiveCommandWarning` pattern catalog from Runnable `BashTool/destructiveCommandWarning.ts` (30 LOC, MED — "rm -rf, git push --force, DROP TABLE, kubectl delete, terraform destroy"). Plus existing v4 SecurityManager (C-1 doc row). Plus Block C+ approval gate at v4 `:9444 + :9448`. SYNTHESIS_MASTER §"Block C".
- **Verdict**: HANDLED.

### 10. Approval prompt for `write_file` appears, user clicks **Deny**
- **What user does**: clicks Deny on the diff dialog.
- **What could go wrong**: model interprets silence as success and continues; OR agent crashes on the cancelled future.
- **What v5.0.1 plan provides**: Block C+ approval gate wiring — v4 `pending_approval` dict + on_approve/on_deny at `:10306, :10491-10605` (~100 LOC). Plan §"Block C+" Q4 lock test: "write_file with diff approval Approve/Deny/Always".
- **Verdict**: NEEDS-LOCK-TEST. The Deny-then-recover path is in plan but the model-prompt that the agent feeds back ("user denied; do not retry without explicit instruction") needs an explicit lock test — it is implied not specified in v3 §"Block C+".

### 11. Repeated `read_file` of the same offset/limit (tight loop)
- **What user does**: vague prompt that makes the model re-read the same chunk.
- **What could go wrong**: cost spike, no progress, user has to ESC.
- **What v5.0.1 plan provides**: Block C repetition detector at v4 `:9156-9180` (read_file dedup key `f"{fp_norm}@{offset}:{limit}"` + threshold-2 — "V4.10.10 [Actual Use Issue 7]"). Plus Block N N-15 dedup at Hermes `run_agent.py:4639-4655`. Q4: "lock test 200 bash → 201st returns explicit message with OTHER TOOLS STILL WORK listing."
- **Verdict**: HANDLED.

### 12. Bedrock returns 5xx with a raw HTML error page (load balancer / WAF)
- **What user does**: any prompt during a Bedrock incident.
- **What could go wrong**: chat panel renders raw HTML; user can't tell if it's their bug or AWS.
- **What v5.0.1 plan provides**: Block L L-9 `sanitizeAPIError` + `extractNestedErrorMessage` from Runnable `errorUtils.ts:107-198` (50 LOC, **MUST**) — "Without it, Bedrock 5xx returns raw HTML to user." Plus L-17 "API error humanizer (Bedrock-only variant)" from Hermes `run_agent.py:3552-3590` (40 LOC).
- **Verdict**: HANDLED.

### 13. Bedrock returns 529 (capacity) repeatedly during peak hours
- **What user does**: business-hours prompt during ap-southeast-2 capacity event.
- **What could go wrong**: agent retries forever, multiplying load and burning the user's wallclock.
- **What v5.0.1 plan provides**: Block L L-4 `is529Error` + querySource-aware retry-vs-drop at Runnable `withRetry.ts:610-621, 84-89` (40 LOC, HIGH — "Prevents capacity-cascade amplification"). L-5 `FallbackTriggeredError` Opus→Sonnet on 3x 529 at Runnable `withRetry.ts:160-168` (NEEDS-ADAPTATION for Bedrock fallback inference profile).
- **Verdict**: NEEDS-LOCK-TEST. L-5 is NEEDS-ADAPTATION for Bedrock — adapter not yet specified at file:line; needs an integration test.

### 14. Context overflow 400 from Bedrock (`maxTokens` exceeded mid-compact)
- **What user does**: long session, finally triggers compact.
- **What could go wrong**: compact-itself-too-long PS-class bug — turn permanently fails, user can't recover.
- **What v5.0.1 plan provides**: Block L L-1 `getPromptTooLongTokenGap` parse + drop multiple groups at Runnable `errors.ts:104-118` (50 LOC, HIGH, "Closes compact-retry stalling PS-class bug"). L-2 `parseMaxTokensContextOverflowError` at Runnable `withRetry.ts:550-595` (30 LOC, **MUST**, "Without it, context-overflow 400s permanently fail the turn"). Plus Block A A-8 `MAX_PTL_RETRIES=3` + `truncateHeadForPTLRetry` at `compact.ts:227-491` (70 LOC).
- **Verdict**: HANDLED.

### 15. User hits ESC / interrupts a long-running bash mid-execution
- **What user does**: realizes the agent is doing the wrong thing, presses interrupt.
- **What could go wrong**: bash subprocess keeps running; agent state goes inconsistent; next prompt sees ghost output.
- **What v5.0.1 plan provides**: Block C C-17 `combinedAbortSignal` + `AsyncLocalStorage` cwd at Runnable `utils/combinedAbortSignal.ts + cwd.ts` (50 LOC, HIGH, NEEDS-ADAPTATION — Python `contextvars.ContextVar('cwd')` + `asyncio.Event`). Synthesis explicitly: "v4 can't cancel long bash." Plus L-21 daemon-thread Bedrock call for Ctrl-C responsiveness from Hermes `run_agent.py:5637-5781` (80 LOC).
- **Verdict**: NEEDS-LOCK-TEST. Adaptation from JS AsyncLocalStorage to Python contextvars is non-trivial; cancellation propagation to subprocess.Popen needs an explicit test.

### 16. Skill self-patch produces a syntactically broken `SKILL.md` (V4.9.5 self-patching path)
- **What user does**: types `/skill apply <name>`.
- **What could go wrong**: agent applies the patch but the broken SKILL.md prevents next-session load.
- **What v5.0.1 plan provides**: Block D ports v4 `/skill apply <name> [--yes|--edit]` handler at v4 `:10892-10954` verbatim (V4.9.5 8-rail safety: opt-in `CONFIG.enable_skill_patching`, propose-not-apply, diff preview, snapshot, audit log). Plan §"Block D" line "all 11 schema + impl line refs verified by grep against v4 source 2026-05-01."
- **Verdict**: HANDLED. Pre-apply snapshot via SnapshotManager (Block B `:4418-4509`) gives `/revert` recovery.

### 17. Cache-break detection emits constant false positives on Haiku 4.5 sub-agent
- **What user does**: dispatches a `build` sub-agent on Haiku.
- **What could go wrong**: constant cache-break warnings flood the chat; user can't tell real breaks from noise.
- **What v5.0.1 plan provides**: Block L L-14 `isExcludedModel` Haiku exclusion at Runnable `promptCacheBreakDetection.ts:128-131` (3 LOC, **MUST**, "Without it, Haiku 4.5 sub-agents emit constant false breaks"). One of the 8 NOT-OPTIONAL correctness fixes per SYNTHESIS_MASTER §1.
- **Verdict**: HANDLED.

### 18. Tool-call result aggregate exceeds 200K chars (huge log)
- **What user does**: greps a 10MB log file.
- **What could go wrong**: tool_result blows the per-message budget, model errors out.
- **What v5.0.1 plan provides**: Block T T-11 "Tool result limits + per-message budget" at Runnable `constants/toolLimits.ts` (30 LOC, HIGH — "200K char per-message tool result aggregate cap"). Plus Block N N-6 `enforce_turn_budget` over `messages[-num_tools:]` at Hermes `run_agent.py:8714-8725` (30 LOC).
- **Verdict**: HANDLED.

### 19. Bedrock call hangs forever (silent throttling-retry inside boto3)
- **What user does**: any prompt; just waits and the kernel stays "Busy".
- **What could go wrong**: no heartbeat; user can't tell if it's stuck or just slow; ipykernel may even time out.
- **What v5.0.1 plan provides**: Block L L-22 stale non-stream call detector with context-scaled deadline from Hermes `run_agent.py:5704-5762` (50 LOC, HIGH — "Bedrock can hang in throttling-retry"). L-23 heartbeat callback every 30s at Hermes `run_agent.py:5720-5724` (20 LOC, HIGH — "Keeps ipykernel alive"). Plus A-18 `sessionActivity` keep-alive during compact at Runnable `compact.ts:1167-1395` (20 LOC).
- **Verdict**: HANDLED.

### 20. Model output contains lone Unicode surrogate → boto3 JSON encoder crashes
- **What user does**: model emits emoji/CJK in a tool_result.
- **What could go wrong**: next Bedrock converse fails 400; user sees opaque encode error.
- **What v5.0.1 plan provides**: Block A A-26 surrogate sanitization recursive walker from Hermes `run_agent.py:384-502` (115 LOC, HIGH, "`_sanitize_messages_surrogates` before every Bedrock converse"). Plus N-17 surrogate sanitize at request-time folded into A-26.
- **Verdict**: HANDLED.

### 21. Stub-injection failure: model emits `tool_use` but no `tool_result` posted post-compact
- **What user does**: routine compact mid-conversation.
- **What could go wrong**: Bedrock 400-errors after compact ("missing tool_result") and turn dies.
- **What v5.0.1 plan provides**: Block A A-25 "Stub-injection for missing tool_results post-compact" from Hermes `run_agent.py:4585-4604` (25 LOC, **MUST** — "Without it, Bedrock 400-errors after compact"). One of 8 NOT-OPTIONAL fixes.
- **Verdict**: HANDLED.

### 22. User runs `/auth <wrong-token>` then keeps typing
- **What user does**: enables `CONFIG.require_auth=True` then mistypes the token.
- **What could go wrong**: subsequent commands silently no-op; user thinks the agent is broken.
- **What v5.0.1 plan provides**: Block D ports v4 `/auth <token>` auth-gate at v4 `:10789-:10802` verbatim (with explicit `not msg.startswith("/auth")` check at `:11314`). Q4 lock test: "`/auth` rejection on wrong token + `/auth` success on correct token."
- **Verdict**: HANDLED. v3 plan §"Block D" tracks `/auth` as a separate row beyond the 19 advertised commands.

### 23. Sub-agent dispatched with `type="build"` but worktree creation fails (disk full / git lock)
- **What user does**: triggers a build sub-agent.
- **What could go wrong**: parent agent silently uses the same workspace; concurrent edits collide; later compact corrupts session.
- **What v5.0.1 plan provides**: Block G ports v4 worktree spawn at `:8413-...` (~57 LOC). Plan §"Block G" Q4: "lock test for each agent type + worktree creation/cleanup for build." Block B+ FileCache thread-local context save/restore at v4 `:893-1017` provides isolation guarantee.
- **Verdict**: NEEDS-LOCK-TEST. Disk-full + git-lock failure paths are not explicitly in Q4; the lock test as written only verifies happy-path creation/cleanup.

### 24. Rate-limit gate fires (`max_user_messages_per_minute`) — user types fast during demo
- **What user does**: pastes 20 prompts in 30 seconds during a live demo.
- **What could go wrong**: rate-limit gate silently drops messages or gives a confusing "blocked" with no countdown.
- **What v5.0.1 plan provides**: Block C+ ports v4 rate-limit at `:8731-8740` verbatim. Plus Block L L-3 `getRateLimitResetDelayMs` Unix-sec parse at Runnable `withRetry.ts:814-822` (15 LOC — `anthropic-ratelimit-unified-reset` header). Q4 §"Block C+": "lock test 100 messages/min triggers rate limit."
- **Verdict**: NEEDS-LOCK-TEST. The Q4 lock test triggers the gate but does not assert the user-visible message includes a clear countdown / next-allowed-time. UX-grade behavior is not specified.

### 25. Approval gate UI never renders because user is in a non-`ipywidgets` shell (e.g. JupyterLab kernel via VS Code)
- **What user does**: opens chat.ipynb in VS Code's Jupyter extension instead of classic Notebook.
- **What could go wrong**: dialog never appears; agent waits forever on `pending_approval`; user has no way to approve and the kernel locks.
- **What v5.0.1 plan provides**: Block E renders approval dialog UI at v4 `:10491-10605` (~115 LOC) via `ipywidgets`. The plan does NOT detect rendering-layer absence; it assumes classic notebook host. Block J Real-Bedrock smoke test runs `import sagemaker_agent` but does not actually verify ipywidgets render in the user's host.
- **Verdict**: POSSIBLE-GAP. v5.0.1 has no fallback for "approval gate cannot render" — agent will hang. A timeout or text-mode fallback (`ask_user` tool from Block T) is not wired to the approval flow. Recommend adding a watchdog timer + text-mode fallback to Block C+.

---

## Summary

| Verdict | Count | Scenarios |
|---|---:|---|
| **HANDLED** | 16 | 1, 3, 4, 5, 6, 7, 8, 9, 11, 12, 14, 16, 17, 18, 19, 20, 21, 22 (= 18 actually — recount below) |
| **NEEDS-LOCK-TEST** | 6 | 2, 10, 13, 15, 23, 24 |
| **POSSIBLE-GAP** | 1 | 25 |

**Corrected totals (recount)**: HANDLED = 18, NEEDS-LOCK-TEST = 6, POSSIBLE-GAP = 1. Total = 25.

### Highest-leverage open items for builder

1. **Scenario 25 (POSSIBLE-GAP)** — approval gate has no non-ipywidgets fallback. Highest user-visible impact for VS Code users. Suggest: add a 60s watchdog in Block C+ that falls back to `ask_user` tool (Block T) text mode if the dialog future is not resolved.
2. **Scenario 15 (NEEDS-LOCK-TEST)** — Python contextvars + asyncio.Event adaptation of `combinedAbortSignal` is the single biggest "looks easy in plan, hard in code" item. Lock test must include a real subprocess.Popen kill.
3. **Scenario 13 (NEEDS-LOCK-TEST)** — Opus→Sonnet fallback inference profile on Bedrock has no concrete file:line in plan beyond "NEEDS-ADAPTATION." Should ship with at least the inference-profile ARN config plumbing.
4. **Scenario 2 (NEEDS-LOCK-TEST)** — IAM token expiry is a real SageMaker-class failure that is currently only "architectural" in L-20. Needs a real test that boto3 returns `ExpiredTokenException` and the rebuild fires.
5. **Scenario 10, 23, 24 (NEEDS-LOCK-TEST)** — UX-grade messages (Deny recovery, worktree-failure, rate-limit countdown) are speced as gates but not as user-visible messages.

### Coverage by Block

- **Block C** (runtime safety + JSON repair + bash hardening): 8 scenarios fully covered (1, 3, 4, 5, 9, 11, 15-mech, 25-partial).
- **Block C+** (approval + rate limit + abort): 4 scenarios — 2 fully, 2 need lock tests (10, 24).
- **Block L** (error/retry/cache-break): 7 scenarios — 5 fully, 2 need lock tests (2, 13).
- **Block A** (compact + sanitize + stub-inject): 3 scenarios fully covered (14, 20, 21).
- **Block N** (parallel + dedup + fuzzy): 2 scenarios fully covered (7, 11 partial).
- **Block I** (skill resolution): 1 scenario fully covered (8).
- **Block D** (slash commands incl. /auth, /skill apply): 2 scenarios fully covered (16, 22).
- **Block G** (sub-agent types + worktree): 1 scenario needs lock test (23).
- **Block T** (tool surface): 1 scenario fully covered (18).

### Confidence note

Plan v3 + Wave-5-DEEP cover the full surface area at the file:line level. The remaining risk is concentrated in **adaptation gaps** (JS→Python contextvars, Anthropic→Bedrock fallback profile) and **UX-grade lock tests** (does the user-visible message actually tell them what to do). All 6 NEEDS-LOCK-TEST scenarios have plan rows; the gap is between "code lands" and "user-visible behavior is right." The single POSSIBLE-GAP (scenario 25) is the one place the plan structurally assumes an environment that not all users have.
