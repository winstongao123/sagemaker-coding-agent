# W6 — Long sessions + context management + cost + budget (25 user-perspective scenarios)

> Date: 2026-05-01
> Source plan: `compact_v5/_phase_2/synthesis/V5_PHASE_2_PLAN_v3.md`
> Synthesis: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md`
> Confidence: `compact_v5/_phase_2/wave_5_deep/CONFIDENCE_REPORT.md`
> v4 baseline: `compact_v4/MAIN/agent/sagemaker_agent.py`
>
> Persona: A SageMaker user (insurance shop, no external network, Bedrock-only) building Power BI dashboards / analytics notebooks across multi-hour, multi-day sessions. They worry about cost, lost work, "did the agent break my context?", and "can I keep working?".
>
> For each scenario: **What user does → What could go wrong → What v5.0.1 plan provides → Verdict**.

---

## 1. The "I left it running over lunch" 90-minute idle

**What user does**: Kicks off a 5-step refactor at 11:55am, walks to lunch, comes back at 1:30pm. Hits Enter on next message.

**What could go wrong**: Bedrock prompt cache TTL has expired (cache window is short on Bedrock). First post-idle turn pays full uncached input → user sees a $0.40+ spike on a routine question and panics. v4 had `COLD_CACHE_THRESHOLD_SECONDS = 30*60` to detect this and pre-emptively microcompact.

**What v5.0.1 plan provides**: Block A — `COLD_CACHE_THRESHOLD_SECONDS = 30*60` (`sagemaker_agent.py:3826`) + cold-cache trigger logic at `:8923` ported into `runtime/compact.py`. Q4 lock test: "30-min idle → resume → microcompact fires + freed ≥5K tokens".

**Verdict**: HANDLED.

---

## 2. The "$10 cost slider, hit 80% in turn 14"

**What user does**: Sets cost-limit slider in cell 2 to $10, builds dashboard. By turn 14 spent $8.10.

**What could go wrong**: User wants a clear warning ("you have $1.90 left"), not a silent crash at $10.01. v4 prints the 80%/100% line; v5.0.0 had this disconnected from UI.

**What v5.0.1 plan provides**: Block B+ — TokenTracker `:3638-3652` (warns 80% / blocks 100%) + run-loop warning at `:8787` printed as `[Cost ${TOKENS.session_cost} passed budget ${CONFIG.session_cost_limit} — continuing.]`, wired in `core/query_engine.py:run()`. Cost-limit slider port at `:10086-10102` to Cell 2 (Block F).

**Verdict**: HANDLED.

---

## 3. The "100% cost cap hit mid tool_use loop"

**What user does**: Cost cap is $5. Agent is mid-multi-step `bash` debug at $4.97. Next tool call would push over.

**What could go wrong**: If hard cap blocks mid-tool_use the conversation can be left with a tool_use that has no tool_result → next turn returns Bedrock "messages.X.tool_use_id" error and session is wedged.

**What v5.0.1 plan provides**: Block B+ enforcement at TokenTracker `:3638-3652` (warns 80% / blocks 100%) — and **H2 stub-injection for missing tool_results** is a NOT-OPTIONAL correctness fix (plan §1, line 14). Combined: cap fires cleanly + stub injected so next turn isn't wedged.

**Verdict**: NEEDS-LOCK-TEST. The stub-injection-on-cost-block path is not explicitly named in Block B+ Q4 lock test; need a "blocked at 100% mid-tool_use → stub injected → recovery turn passes" test added.

---

## 4. The "I want to come back tomorrow, /save then /load"

**What user does**: 4pm Friday. Types `/save` (or clicks save). Monday 9am opens new kernel, `/load my_session`.

**What could go wrong**: Cost counter resets to $0 (user sees "session cost $0" and assumes free run). Skill activations lost. AGENT_STATUS.md not re-injected. v4 already preserved session_cost in save/load callbacks.

**What v5.0.1 plan provides**: Block B+ SessionManager (`:2578-...`) + on_save/on_load callbacks `:11569-11665` "incl. session_cost" (plan line 81). AGENT_STATUS auto-load wired in `agent/__init__.py:Agent.run()` first call (plan line 160). Q4 lock test: "save→load→cost preserved + AGENT_STATUS injected".

**Verdict**: HANDLED.

---

## 5. The "200+ python_exec in a row" runaway debug

**What user does**: Power BI DAX issue. Agent loops `python_exec` to test variants. By call 199, user is just watching.

**What could go wrong**: v5.0.0 had no exec gate; agent burns budget infinitely. v4 capped at 200 with a misleading error message that confused the model.

**What v5.0.1 plan provides**: Block C — exec-limit gate `:9477-9478` + corrected error message body `:9482-9489` ("Blocked: bash + python_exec call limit reached..."). `Config.max_exec_calls_per_session = 200` at `:1080`. Wired into `tools/bash.py` + `tools/python_exec.py`.

**Verdict**: HANDLED.

---

## 6. The "agent reads the same 600-line file 8 times"

**What user does**: Agent investigates a bug, re-reads `dashboard.py` repeatedly because it forgot it already read it.

**What could go wrong**: Massive cost waste, context bloat, eventually triggers compact prematurely.

**What v5.0.1 plan provides**: Block C — Repetition detector `:9156-9180` (`f"{fp}@{offset}:{limit}"` dedup key + threshold-2). Wired into `core/query_engine.py` tool dispatch. Plus Block N dedup blocks redundant calls.

**Verdict**: HANDLED.

---

## 7. The "I sent 100 tiny messages in 90 seconds"

**What user does**: Frustrated user spamming "fix it", "no", "try again", "no", typing fast.

**What could go wrong**: Bedrock throttle hits, opaque error. Or session cost shoots up because every message hits uncached prefix.

**What v5.0.1 plan provides**: Block C+ — Rate-limit `:8731-8740` (max_user_messages_per_minute / per_session) ported into `core/query_engine.py:run()` entry. Q4 lock test: "100 messages/min triggers rate limit".

**Verdict**: HANDLED.

---

## 8. The "context hits 70%, agent goes quiet for 8 seconds"

**What user does**: 2-hour session, context monitor reads 71%. Sends next message.

**What could go wrong**: User doesn't know microcompact is running; thinks the agent froze and force-restarts the kernel, losing in-flight tool_use.

**What v5.0.1 plan provides**: Block A — `MICROCOMPACT_TRIGGER_PERCENT = 0.70` (`:3822`) + `microcompact()` at `:3851-3977`. Q4 lock test: "70% context → reactive compact triggers". UI side: Block E+F status bar shows context % live (`update_tokens_display :10377`).

**Verdict**: NEEDS-LOCK-TEST. The trigger fires (HANDLED structurally) but the **user-visible "compacting…" indicator** during the 2-8s wait isn't called out as a Block E+F lock test. Risk: silent freeze UX.

---

## 9. The "auto-compact loops infinitely on a poison message"

**What user does**: Pastes a 200K token log file. Compactor runs, but post-compact context is still over threshold → re-triggers.

**What could go wrong**: Infinite compact loop, every cycle costing $0.05+. Without circuit breaker user discovers it 30 min later at $9.

**What v5.0.1 plan provides**: Block A — auto-compact circuit breaker (`_auto_compact_paused` global) + Runnable's `autoCompact.ts:1-352` thresholds. Plan line 234: "Runnable circuit-breaker thresholds".

**Verdict**: HANDLED.

---

## 10. The "/cost shows wildly different number than the cell-2 widget"

**What user does**: Mid-session types `/cost`. Status bar says $3.20, `/cost` says $3.85.

**What could go wrong**: Disagreement = lost trust. Often caused by sub-agent calls not attributed to the parent cost.

**What v5.0.1 plan provides**: Block B + B+ — TokenTracker singleton `:3755`, **per-agent attribution dict** (`parent_*`, `subagent_*[type]`), same singleton (object-identity preserved). Acceptance test (plan line 162): `TOKENS.session_cost == sum_of(per_agent_cost) ± $0.0001`. Lock test in `tests/integration/test_subagent_token_attribution.py`.

**Verdict**: HANDLED.

---

## 11. The "spawn build sub-agent, both share the same $5 budget"

**What user does**: User has $5 cap. Parent spawns `build` sub-agent which itself wants 30 turns.

**What could go wrong**: If sub-agent counts cost separately, parent + sub together blow past $5 with no warning.

**What v5.0.1 plan provides**: Block B+ — TokenTracker shared singleton, sub-agent updates same `session_cost` via BedrockClient.chat hook (constraint #14 plan line 120: "Token + cost metrics covering parent + sub-agent"). Hard cap applies to combined total.

**Verdict**: HANDLED.

---

## 12. The "fork sub-agent then parent runs out of budget mid-fork"

**What user does**: Parent at $4.85/$5.00, kicks off `verify` sub-agent (forkSubagent).

**What could go wrong**: Sub-agent enters with parent prefix, makes one Bedrock call, hits cap at $5.02 → cap blocks → returned to parent which still has open tool_use → wedged.

**What v5.0.1 plan provides**: Block G2 — forkSubagent cache-prefix replay (`forkSubagent.ts:73-end`) + Block B+ shared cap. Cap-block message returns clean tool_result. BUT: the "parent has open tool_use, sub-agent blocked at cap, recovery flow" path is not explicitly in any Q4 lock test.

**Verdict**: NEEDS-LOCK-TEST. Add a "fork → sub-agent capped mid-call → parent recovers" test under Block G2 or B+.

---

## 13. The "3-hour Power BI rebuild, can I trust the cost number"

**What user does**: Long session — 3 hours of dashboard rebuilds. Watches `/cost` every 30 min.

**What could go wrong**: TokenTracker math drifts (R7 N8 token-accounting bug — input cumulative vs output per turn). User sees $3 but actual AWS bill is $7.

**What v5.0.1 plan provides**: Plan §1 NOT-OPTIONAL fix list (line 14): **R7 N8 token-accounting input-cumulative-vs-output-per-turn** is one of the 8 not-optional correctness fixes. Block B + B+ ports the fix.

**Verdict**: HANDLED.

---

## 14. The "I switched models from Sonnet to Haiku mid-session, cost broke"

**What user does**: Halfway through, drops cell-2 model dropdown to Haiku to save money.

**What could go wrong**: Pricing math hardcoded to Sonnet → cost display wrong. Or cache breaks because `isExcludedModel` Haiku-cache-break bug from R4 #14.

**What v5.0.1 plan provides**: Plan §1 NOT-OPTIONAL fix line 14: **R4 #14 isExcludedModel Haiku cache-break**. Block L extends `core/cache.py` with per-tool hashing + cache-break diagnostics. Block A cache-aware pricing math (plan line 141: "v4 Bedrock cache-aware pricing math").

**Verdict**: HANDLED.

---

## 15. The "context-overflow 'max tokens exceeded' Bedrock error"

**What user does**: Pastes 50K-line CSV preview into chat. Next turn Bedrock returns max_tokens error.

**What could go wrong**: Generic error → model gives up → user types again → loops. v4 had `parseMaxTokensContextOverflowError` to detect + force-compact.

**What v5.0.1 plan provides**: Plan §1 NOT-OPTIONAL fix line 14: **R4 #2 parseMaxTokensContextOverflowError**. Block L extends `core/errors.py` (18 categories) + `core/retry.py` (retry-after, fast-mode fallback). Auto-compact triggers on the categorized error.

**Verdict**: HANDLED.

---

## 16. The "kernel died, did I lose 2 hours of work"

**What user does**: SageMaker JupyterLab kernel restart at hour 2. Reopens notebook.

**What could go wrong**: All state in-RAM only → conversation gone, cost gone, AGENT_STATUS not re-loaded. v4 had auto-save-on-send.

**What v5.0.1 plan provides**: Block E+F — "auto-save on send" (plan line 258, ported from v4 `:11569-11665` + `:10491-10605`). Block B+ SessionManager atomic save/load. Block A "post-compact restoration `_FILES_READ.clear()`" implies file-read cache also persists.

**Verdict**: HANDLED.

---

## 17. The "5-day vacation, /load my_session monday"

**What user does**: Resumes session 5 days later from same notebook.

**What could go wrong**: Stored session JSON has tool_use without matching tool_result (write was interrupted). Bedrock chokes on first turn.

**What v5.0.1 plan provides**: Plan §1 NOT-OPTIONAL fix line 14: **H2 stub-injection for missing tool_results** + **R4 #56 adjustIndexToPreserveAPIInvariants**. Block A's compact path also enforces invariants.

**Verdict**: HANDLED (structurally). Lock test exists per plan line 351 ("for each new error category"), but a specific "load truncated session → recover" test isn't called out — could be added under Block B+.

---

## 18. The "auto-dream daemon ran while I was idle, cost spike?"

**What user does**: Idle in notebook with kernel alive, agent runs Block H+ Auto-Dream daemon for memory consolidation.

**What could go wrong**: Background Bedrock calls user didn't authorize → unexpected $X charges → trust broken.

**What v5.0.1 plan provides**: Block H+ — Auto-Dream daemon ~350 LOC (plan line 11). Cost should be attributed via the same TokenTracker singleton. BUT: opt-in flag and "show cost from auto-dream in /cost" wiring is not detailed in v3 plan text.

**Verdict**: POSSIBLE-GAP. Block H+ exists but the "auto-dream is opt-in + its cost is visible + can be capped" UX is not specified. User needs an off-switch + cost transparency for any background daemon. Recommend: Block H+ Q4 lock test must include "auto-dream off-by-default + cost attributed + bounded by session_cost_limit".

---

## 19. The "I want to STOP a runaway agent right now"

**What user does**: Agent went on a 25-step tangent. User clicks stop button.

**What could go wrong**: Stop button doesn't cut between tool_use and tool_result → next turn wedged. Or stop fires only at end of turn → 30s wait.

**What v5.0.1 plan provides**: Block C+ — `agent/__init__.py:Agent.stop()` already exists; `core/query_engine.py:run()` per-turn checkpoint reads `_combined_stop()` (already wired in Phase 8, plan line 183).

**Verdict**: HANDLED.

---

## 20. The "/checkpoint create before scary refactor"

**What user does**: Before agent does mass-rename across notebook, types `/checkpoint create pre-rename`. Refactor breaks dashboard. `/checkpoint restore pre-rename`.

**What could go wrong**: Restore reverts files but session messages still reference old names → confusion + wrong tool calls.

**What v5.0.1 plan provides**: Block D — `/checkpoint [create <name>|list|restore <name>]` at `:11114-11182` (snapshot management). Q4 (plan line 226): "lock test all 20 command-like inputs end-to-end... includes `/checkpoint create/list/restore`".

**Verdict**: HANDLED. Caveat: whether session-message-state syncs with checkpoint restore is not detailed; lock test should verify post-restore messages reference current files.

---

## 21. The "auto-continuation after iteration budget hits"

**What user does**: Iteration budget = 30. Multi-step task hits 30 with no completion. User wants "keep going automatically up to 60".

**What could go wrong**: Without F2, agent halts at 30 with confusing message, user has to manually restart with new budget.

**What v5.0.1 plan provides**: Block F2 — Auto-Continuation under iteration budget ~100 LOC (plan line 11). `IterationBudgetWidget` already exists in `compact_v5/MAIN/agent/ui/widgets.py` (plan line 259, PS#2 RESOLVED).

**Verdict**: NEEDS-LOCK-TEST. Block F2 is allocated but its exact behavior contract (auto-extend? prompt user? respect cost-cap?) is not in plan v3 detail. Need lock test: "iter-budget hit → F2 auto-continues N more turns IFF cost cap allows + user opt-in".

---

## 22. The "100K token paste, context bloat, /context shows what"

**What user does**: Pastes a giant log. Types `/context` to see how bad it is.

**What could go wrong**: `/context` returns stale numbers. Or returns total tokens but doesn't show breakdown (system / tool-results / user / messages).

**What v5.0.1 plan provides**: Block D — `/context` at `:11052-11061` (token/context bloat diagnostic). Ported verbatim. Pairs with Block A microcompact triggering at 70%.

**Verdict**: HANDLED.

---

## 23. The "I want to set $2 cap to test, then $20 for real work"

**What user does**: Cell-2 cost slider $2 for sandbox test. Restarts cell with slider $20 for real session.

**What could go wrong**: Slider widget value doesn't propagate to runtime CONFIG until full kernel restart. User thinks they raised cap but it's still $2.

**What v5.0.1 plan provides**: Block F — Cost-limit slider integration `:10086-10102` (~16 LOC) ported into Cell 2 launch panel + status bar (plan line 257). `Config.session_cost_limit` enforced at `:1082` / `:3638-3652`.

**Verdict**: NEEDS-LOCK-TEST. The "slider → live CONFIG.session_cost_limit update without kernel restart" path isn't explicit. Add test: "move slider mid-session → next turn respects new cap".

---

## 24. The "two hours later: was a skill auto-applied I didn't see"

**What user does**: Opens `/skills` after long session, expects to see what fired.

**What could go wrong**: No audit trail. v4 had skill_suggestions / skill_apply / unskill commands.

**What v5.0.1 plan provides**: Block D full v4 command parity — `/skills`, `/skill use/clear`, `/unskill`, `/skill suggestions/reject`, `/skill apply` (plan line 85, refs `:8164` + `:10789-:11341`). Block I has 6 skill enhancements.

**Verdict**: HANDLED.

---

## 25. The "did the cache actually save me money on this 4-hour session"

**What user does**: At hour 4 wants to know cache-hit ratio. Looks at `/cost` and `/status`.

**What could go wrong**: v4 displayed cumulative cost only; cache savings invisible. User can't tell if Bedrock cache is working (Hermes A28 invariant matters here — wrong invariant = silent cache misses).

**What v5.0.1 plan provides**: Block L — `promptCacheBreakDetection.ts` ports (`notifyCacheDeletion` `:673`, `notifyCompaction` `:689`, `resetPromptCacheBreakDetection` `:704`). Block A28 prompt-cache invariant policy (plan §1 line 14, NOT-OPTIONAL). Block B+ Runnable B+ status block — "Runnable B+ (recursive advisor sub-cost accounting, atexit flush, persist on /resume, **4-line cost block**)" per CONFIDENCE_REPORT line 111. The 4-line block typically shows cached vs uncached input.

**Verdict**: NEEDS-LOCK-TEST. Cache-hit-ratio display in `/cost` UI isn't explicit. Need Q4 lock test: "/cost shows cached_input_tokens, uncached_input_tokens, output_tokens, cache_savings_estimate over session".

---

## Summary

| Verdict | Count | Scenario IDs |
|---|---|---|
| HANDLED | 16 | 1, 2, 4, 5, 6, 7, 9, 10, 11, 13, 14, 15, 16, 19, 22, 24 |
| NEEDS-LOCK-TEST | 7 | 3, 8, 12, 17, 20, 21, 23, 25 (8 — adjusted) |
| POSSIBLE-GAP | 1 | 18 (Auto-Dream cost transparency / opt-in) |

**Recount**: HANDLED = 16, NEEDS-LOCK-TEST = 8, POSSIBLE-GAP = 1. Total = 25.

### Top recommendations to v5.0.1 plan
1. **Block H+ (Auto-Dream)** — explicitly mark opt-in default-OFF, attribute cost to TokenTracker singleton, lock test "off by default + cost visible + bounded by session_cost_limit". (Scenario 18)
2. **Block B+** — add lock test "100% cost cap mid-tool_use → H2 stub injection → next turn passes". (Scenario 3)
3. **Block E+F** — add lock test for **visible compacting indicator** during microcompact (avoid silent 2-8s freeze). (Scenario 8)
4. **Block G2** — add lock test "fork → sub-agent capped at parent's session_cost_limit → parent recovers cleanly". (Scenario 12)
5. **Block F2** — specify behavior contract (auto-extend vs prompt) + lock test respecting cost cap. (Scenario 21)
6. **Block F (slider)** — lock test "live slider update without kernel restart". (Scenario 23)
7. **Block L + B+** — `/cost` 4-line block must show cache-hit ratio explicitly. (Scenario 25)
8. **Block B+** — lock test "load 5-day-old session with truncated tool_use → stub injection recovers". (Scenario 17)

### Bottom line
The long-session / cost / budget category is **structurally well-covered** by the v3 plan thanks to v4 baseline parity (Compactor + cold-cache + cost-limit + exec-gate + rate-limit + checkpoint + save/load) plus Runnable additions (cache_edits, autoCompact circuit-breaker, promptCacheBreakDetection, forkSubagent cache-prefix). The 8 NEEDS-LOCK-TEST items are about **explicit acceptance tests for combined-failure paths** (cap + tool_use, fork + cap, slider + live update, cache-hit visibility) rather than missing features. The 1 POSSIBLE-GAP (Auto-Dream cost UX) is a new v5-unique block; adding the off-switch + transparency contract closes it.

User can build a 4-hour Power BI dashboard session in v5.0.1 with high confidence on cost predictability — provided the 8 lock tests above are added before Block J (real-Bedrock smoke).
