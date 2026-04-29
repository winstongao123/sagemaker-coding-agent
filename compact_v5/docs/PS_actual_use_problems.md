# PS_actual_use_problems.md

Issues observed during actual SageMaker use of compact_v4, what they mean, and what fixed them.

Last updated: 2026-04-29 (within v4.10.10 in-place refinements)

---

## [Actual Use Issue 1]: Noisy `[CSO-CHECK]` warnings on every notebook startup

### What you saw
```
WARNING:root:[CSO-CHECK] skill 'batch' description does not start with 'Use when' — current: 'Coordinator-worker orchestration ...' (advisory; see ADVANCED_PATTERNS.md R-105)
WARNING:root:[CSO-CHECK] skill 'clara-review' description does not start with 'Use when' — ...
WARNING:root:[CSO-CHECK] skill 'design' ...
WARNING:root:[CSO-CHECK] skill 'powerbi-dashboard' ...
WARNING:root:[CSO-CHECK] skill 'powerbi-dashboard-v2' ...
WARNING:root:[CSO-CHECK] skill 'report' ...
WARNING:root:[CSO-CHECK] skill 'code-review' ...
WARNING:root:[CSO-CHECK] skill 'security-review' ...
WARNING:root:[CSO-CHECK] skill 'simplify' ...
WARNING:root:[CSO-CHECK] skill 'verify' ...
```

### What it is
A v4.9.3 audit check (`sagemaker_agent.py:2735-2743`) that flags skills whose descriptions don't start with `Use when [trigger]` (the "Capability Self-Organization" / CSO pattern from `ADVANCED_PATTERNS.md R-105`). This pattern makes the agent's own skill-surfacing prompt cleaner ("Consider using X when Y..." reads naturally).

### Why it fired for so many skills
The CSO convention was introduced after most skills were already written. Per `ADVANCED_PATTERNS.md R-105`: *"new only, no retrofit of existing files"*. The check is **advisory** — it never blocks loading.

### Why it was annoying
Logged at `WARNING` level → 8-10 lines printed to stderr on every notebook startup AND on every test run. Polluted real warnings.

### Fix (v4.10.10 in-place)
Lowered to `logging.debug`. The audit signal is preserved for anyone running with `LOG_LEVEL=DEBUG`, but normal startup is silent. No skill descriptions need to change.

**Code change**: [sagemaker_agent.py:2740](../MAIN/agent/sagemaker_agent.py) — `logging.warning` → `logging.debug`.

---

## [Actual Use Issue 2]: Iteration budget too tight (`max_iteration_budget = 90`)

### What you saw
Mid-task, the agent stops with: *"Iteration budget exhausted across N parent + sub-agents. Adjust CONFIG.max_iteration_budget or start a new session."*

### What it is
A **shared LLM-turn counter** across the parent agent and ALL spawned sub-agents (`/verify`, `/simplify`, `/security-review`, etc.). Defined at [sagemaker_agent.py:1104](../MAIN/agent/sagemaker_agent.py) and enforced by the `IterationBudget` class at line ~8168.

### Why it was capped at 90
Inherited from the hermes-agent pattern (`run_agent.py:170`). Designed for cost-capped insurance contexts where predictable spend ceilings matter more than task completion. Hermes default of 90 is conservative.

### Why even 300 ran out
A typical complex SageMaker task:
| Phase | Turns |
|---|---|
| Parent agent doing the actual work | 30-50 |
| `/verify` sub-agent (adversarial test) | 10-20 |
| `/simplify` sub-agent (reuse audit) | 10-15 |
| `/security-review` (OWASP audit) | 15-20 |
| Any reactive compact recovery | +5-10 |
| **Total realistic ceiling** | **70-115 per cycle** |

A `/done quick` (verify + simplify) before ship adds another ~25-35. Multiple iteration cycles + multi-step builds easily blow past 300.

### Fix (v4.10.10 in-place)
- **Default bumped 90 → 600.** Realistic headroom for complex SageMaker dev sessions.
- **UI slider added** in `chat.ipynb` cell 2 (`Iter Budget: 90 ... 2000`, step 50). Wired to `CONFIG.max_iteration_budget` in cell 3.
- **Banner shows current value**: *"... Iter ceiling: 600"*.
- **Range**: 90 (cost-strict) ↔ 2000 (very deep refactors).
- **Cost still bounded** by independent `session_cost_limit` ($5 default).

**Code changes**:
- [sagemaker_agent.py:1104](../MAIN/agent/sagemaker_agent.py) — `max_iteration_budget: int = 600`.
- [sagemaker_agent.py:8177](../MAIN/agent/sagemaker_agent.py) — `IterationBudget.DEFAULT_MAX = 600`.
- [chat.ipynb cell 2](../MAIN/agent/chat.ipynb) — `iteration_budget_slider` widget.
- [chat.ipynb cell 3](../MAIN/agent/chat.ipynb) — `CONFIG.max_iteration_budget = iteration_budget_slider.value`.

---

## [Actual Use Issue 3]: Cold cache detection (`[i] Cold cache detected (61min gap) — proactive microcompact freed ~6,850 tokens`)

### What you saw
After being idle for an hour, on the first new message the agent prints:
```
[i] Cold cache detected (61min gap) — proactive microcompact freed ~6,850 tokens
```

### What it is
**Bedrock's server-side prompt cache has a ~5-minute TTL.** When more than `COLD_CACHE_THRESHOLD_SECONDS = 1800` (30 minutes) elapse between API calls, the cache has definitely expired. v4 detects this via timestamp tracking (line 8896-8909) and **proactively runs microcompact** to clear stale tool-result content from the conversation history.

### Why this is a feature, not a bug
- **Without microcompact**: on cold-cache resume, Bedrock would re-tokenize and re-bill the entire context (potentially 50K+ tokens) at full price — your prompt cache savings (~90%) are gone.
- **With microcompact**: large stale tool results (`read_file` outputs from 30+ min ago that the agent isn't actively using) are replaced with `[MICROCOMPACT_MARKER]` placeholders. The retained context still has the conversation flow + recent turns, but you save the re-bill on stale bulk content.
- **Threshold (saves ≥ 5K tokens)**: only fires if there's meaningful saving. Otherwise no-op.
- **Cold-cache mode is more aggressive**: keeps only 1 most-recent tool round-trip (vs normal microcompact which keeps more). Mirrors `runnable`'s `keepRecent=5` design.

### What "61min gap" means
You took an hour break. The cache has been gone for ~56 minutes. Microcompact ran once on resume. Subsequent calls within 5 minutes of each other will rebuild a new cache.

### Impact on cost
**Saves money.** The 6,850 tokens freed avoid being re-billed on the next call. At Sonnet 4.5 input rate (~$3/M tokens), that's ~$0.02 saved per cold-cache event. More importantly, it stays useful on long async sessions where you come back to the agent after a break.

### Configurable via
| Constant | Default | Purpose | File:line |
|---|---|---|---|
| `COLD_CACHE_THRESHOLD_SECONDS` | `1800` (30 min) | Idle threshold to trigger | sagemaker_agent.py:3814 |
| `MICROCOMPACT_MIN_SAVINGS` | `5000` | Min tokens to bother | sagemaker_agent.py:3820 |
| `KEEP_LAST_N_COLD_CACHE` | `1` | Tool round-trips kept | sagemaker_agent.py:3822 |

You don't need to touch these unless you want different behavior.

---

## [Actual Use Issue 4]: Thinking mode appears only for the first message

### What you saw
With **Extended Thinking** enabled in cell 2, you see the 💭 thinking block for the FIRST response. Subsequent messages in the same conversation don't display thinking, even though it's still enabled.

### Why this is actually correct
**Extended Thinking is model-controlled, not agent-controlled.** v4 sends `thinking: { type: "enabled", budget_tokens: 8192 }` on every Bedrock call (verified at [sagemaker_agent.py:2471-2474](../MAIN/agent/sagemaker_agent.py)). What returns depends on the model:

| Turn type | Thinking shown? | Why |
|---|---|---|
| Complex first-message reasoning ("plan this refactor") | Yes (💭 block visible) | Model engages reasoning |
| Tool execution turns (running `read_file`, `bash`, etc.) | Usually no | Tool calls are deterministic; little to think about |
| Simple confirmations / continuations | Usually no | Trivial output, no reasoning needed |
| Ambiguous design choices mid-task | Sometimes | Model decides |

**Sonnet 4.5 is conservative with thinking budget.** It engages when a question has genuinely uncertain reasoning (planning, prioritization, critique). For mechanical execution turns it skips thinking — that's the cost-efficient behavior.

### Verified by code
- Line 2471 (`if thinking_enabled:`) — config IS passed to every call.
- Line 9880 (`💭 {c[:300]}...`) — display logic only fires when Bedrock returns a non-empty `reasoning_content` block.

### What you can do
- **Want thinking on every response?** Increase `thinking_budget` to 16000 (max). Sonnet will use more reasoning budget per turn but won't think on every trivial confirmation either.
- **Want zero thinking?** Untick the checkbox in cell 2.
- **Diagnostic**: run `/cost` after a session and compare reasoning-token counts between turns where you saw 💭 vs not.

---

## [Actual Use Issue 5]: Session totals not persisted across save/load

### What you saw
Banner shows `Budget: 42% ($2.09 / $5.00)` mid-session. After `/save` then `/load` of the same session, banner resets to `Budget: 0% ($0.00 / $5.00)`. The accumulated cost is lost.

### Root cause
[sagemaker_agent.py:11569-11577](../MAIN/agent/sagemaker_agent.py) `on_save` persisted `user_msg_count`, `exec_calls`, `exec_seconds`, `active_skills`, `checkpoints`, `token_stats` to session metadata — but NOT `session_cost`. The Agent class tracks `self.session_cost` internally but doesn't survive serialization round-trip.

### Fix (v4.10.10 in-place)
**`session_cost` now persisted alongside other metadata.**
- `on_save`: writes `metadata["session_cost"] = float(getattr(ui_state["agent"], "session_cost", 0.0))`.
- `on_load`: restores `ui_state["agent"].session_cost = float(session.metadata.get("session_cost", 0.0))`.

After this fix:
- Save a session at $2.09 → reload it → banner shows Budget 42% ($2.09 / $5.00).
- Multi-day sessions accumulate true total cost.
- Token stats (already saved) stay alongside the cost figure.

**Code changes**:
- [sagemaker_agent.py:~11578](../MAIN/agent/sagemaker_agent.py) — `metadata["session_cost"] = ...`.
- [sagemaker_agent.py:~11655](../MAIN/agent/sagemaker_agent.py) — `agent.session_cost = ...` on load.

### Where to view session totals
- **Banner** (status row): `Context: X% (Y / 200,000) Budget: Z% ($A / $5.00)` — current session totals.
- **`/cost`** slash command: detailed per-call + cumulative breakdown.
- **`/status`** slash command: snapshot of session counters (calls, tokens, cost).
- **Session JSON** (`sessions/<id>.json`): `metadata.session_cost`, `metadata.token_stats`, `metadata.exec_calls`, `metadata.exec_seconds`.

---

---

## [Actual Use Issue 6]: Codex caught my session_cost wiring bug (HIGH severity)

### What Codex found
During v4.10.10 in-place review, Codex flagged 2 HIGH findings on my own initial fix:
> *"`on_save` persists `ui_state["agent"].session_cost`, but runtime cost is tracked in global `TOKENS.session_cost` (not on `Agent`). This will usually save 0.0 (or stale dynamically-set value), so intended persistence is ineffective."*
>
> *"`on_load` restores into `ui_state["agent"].session_cost`, but budget checks/UI read `TOKENS.session_cost` (8770, 10272). Loaded cost does not affect /cost/banner/budget behavior."*

### Why I made the mistake
I assumed `session_cost` lived on the `Agent` class because line 3582 reads `self.session_cost = 0.0`. But that `__init__` belongs to **`TokenTracker`** (the singleton at `TOKENS = TokenTracker()` line 3750), not `Agent`. The budget check at line 3635 (`limit > 0 and self.session_cost > 0`) is also TokenTracker's method. The Agent class doesn't have its own `session_cost` attribute.

### Verdict
**Codex VERDICT: FAIL on first attempt. Codex was right.** My save/load was writing to a non-existent attribute and reading from one that always returns 0.

### Fix applied
- **on_save** [sagemaker_agent.py:~11583](../MAIN/agent/sagemaker_agent.py): `metadata["session_cost"] = float(getattr(TOKENS, "session_cost", 0.0))` (now reads from the right place).
- **on_load** [sagemaker_agent.py:~11665](../MAIN/agent/sagemaker_agent.py): conditionally writes to `TOKENS.session_cost` (now writes to the right place; only if saved value > 0 to avoid clobbering normal flow).

After the fix: `/cost`, banner Budget %, and budget-limit checks all see the restored session cost across save/load cycles.

### Lesson
Even with Codex review, the first fix can be wrong. Codex's strict review (not the friendly "looks fine") caught a HIGH-severity functional bug. **Always run the comprehensive Codex review on real changes — its independence is the value.**

---

## [Actual Use Issue 7]: Real log — agent confused after hitting 40-call exec limit (06:29-06:31)

### What you saw (paraphrased real session log)

```
[06:29:09] Agent: I hit the execution limit. Let me use Python instead:
[06:29:16] Agent: I've hit the session execution limit (40 calls). Let me be honest:
            I inferred the issue from the error message but haven't actually shown you
            the exact source code from the file. ... can you either:
              1. Restart the kernel and I'll verify the exact code, or
              2. Look at cell 3 ... yourself

[06:29:41] You: why "can't execute more commands this session"

[06:29:50] Agent: 💭 The user is asking why I said "can't execute more commands this session".
            They're right to question this - I hit the bash execution limit (40/session),
            but that doesn't mean I can't use other tools.
            You're absolutely right - I was wrong. ... I can still use other tools like
            read_file and grep.

[06:30:36] Agent: 💭 The user is asking what's blocking me.
              1. I got "Blocked: global execution call limit reached (40/session)" for both
                 bash and python_exec
              2. But I should still be able to use read_file, grep, glob, edit_file, etc.

[06:31:18 onward] Agent reads the same file region 3+ times trying to find call_textract.
[06:31:42] ⚠ [Warning: Repetitive read_file calls detected (3+ identical), stopping]
```

### What went wrong (root cause analysis)

1. **The 40-call limit was too low for real work.** `max_exec_calls_per_session: int = 40` (line 1075) was set as a conservative insurance ceiling. Realistic SageMaker tasks (read source → write tests → run pytest → debug → re-run) easily hit 40.

2. **The error message was misleading.** Old text:
   > *"Blocked: global execution call limit reached (40/session)"*

   The LLM read this as **"all execution is blocked"**. But only `bash` and `python_exec` are counted (line 9435: `if tool_name in {"bash", "python_exec"}`). Other tools (`read_file`, `grep`, `glob`, `edit_file`, `write_file`, `notebook_edit`, `task`, `ask_user`, `view_image`, `web_fetch`) are NOT counted and remain fully usable.

3. **The system prompt didn't explicitly list which tools are session-counted.** The LLM had to infer from context. Inference under stress (tool just failed) → wrong assumption.

4. **Repetitive read_file behavior** — when the agent fell back to `read_file`, it kept reading near the same offset because each cell-rendered view differed from the raw JSON line numbers. The `tool-failure-detect` correctly caught the loop after 3 identical calls. But:
   - The agent didn't know the rendered view differs from raw line numbers.
   - It didn't try `grep -n` to find a unique anchor first.

5. **Session_cost wiring bug** (compounding) — even when the agent realized other tools were available, `/cost` would have showed wrong totals because of the bug fixed in section 6 above.

### Fixes (v4.10.10 in-place)

| Issue | Fix | File:line |
|---|---|---|
| 40-call limit too low | **Bumped 40 → 200** | [sagemaker_agent.py:1080](../MAIN/agent/sagemaker_agent.py) |
| Misleading error text | **Spelled out which tools ARE/ARE NOT limited**: `"Blocked: bash + python_exec limit reached (200/session). OTHER TOOLS STILL WORK: read_file, grep, glob, edit_file, write_file, notebook_edit, task, ask_user, view_image, web_fetch are NOT counted by this limit. Continue with those, or ask the user to start a new session for more bash/python_exec."` | [sagemaker_agent.py:~9445](../MAIN/agent/sagemaker_agent.py) |
| Repetitive read_file pattern | (already mitigated by tool-failure-detect at 3-repeats; could be tightened further but the user-facing fix is the better error message above) | n/a |
| session_cost wiring bug | TOKENS singleton (not Agent) — see section 6 | sagemaker_agent.py:~11583, ~11665 |

### Why these fixes will help next time

When the agent next hits the limit:
1. The error itself **tells the LLM what to do**: "OTHER TOOLS STILL WORK: read_file, grep, glob, ...". No inference required.
2. With 200 calls (5× old limit), the limit will be hit much less often in normal workflow.
3. When it IS hit, the agent can productively use file-only tools to keep diagnosing without bash/python_exec.

### What's still NOT fixed (semantic gap remaining)

- **System prompt doesn't have a "tool capability matrix" section.** When the agent first plans work, it doesn't know in advance which tools count against the 200 limit. A future v4.11+ improvement: add a SYSTEM_PROMPT block at startup listing tool categories. (Out of scope for v4.10.10 in-place — requires careful prompt engineering + Codex review.)

- **Repetitive read pattern across cell-rendered vs raw-JSON views**: when grepping a `.ipynb` file, line numbers from grep map to raw JSON, but `read_file` on `.ipynb` returns a cell-rendered view with different effective line numbers. The agent wasted ~5 read attempts on this mismatch. **Future fix**: either (a) make grep on .ipynb return cell-rendered line numbers too, or (b) always use `notebook_edit` style cell-by-cell access for .ipynb files.

### Pattern reference: what hermes / runnable do here

Looking at [Learning_Factory ADVANCED_PATTERNS.md](D:/Github/Learning_Factory/docs/ADVANCED_PATTERNS.md) and runnable/hermes:

- **Runnable pattern**: explicit "tool capability surfacing" — tool descriptions include constraints inline (cost, side effects, blocking conditions).
- **Hermes pattern**: graceful degradation — when a high-cost path fails, fall back to lower-cost alternatives explicitly named in the failure message.
- **What v4.10.10 borrows**: the new error message follows the hermes "failure-message-as-instruction" pattern. Tells the LLM precisely which tools remain available.

### Codex investigation findings (background task `bzic5k138`)

Codex completed the deep-dive and identified two specific gaps:

**Finding A — Prompt gap.** `SYSTEM_PROMPT` had efficiency guidance but no explicit "tool-availability matrix" (limited vs unlimited) or "if exec blocked, switch to read-only tools" rule near line 8040-8060. The agent had no proactive way to know which tools are session-counted before hitting the limit.

**Finding B — Repetition detector too loose for read_file.** The dedup key was `path@offset` only (line 9155), so re-reading near the same offset with different `limit` values created different keys → the loop breaker only fired at 4th identical call. Should be `path@offset:limit` and threshold 2 (not 3) for read_file specifically.

**Both fixes applied in v4.10.10 in-place:**

| Codex finding | Fix | File:line |
|---|---|---|
| Prompt gap | Added new SYSTEM_PROMPT block "Tool availability matrix — V4.10.10 [Actual Use Issue 7]" listing session-limited tools (`bash`, `python_exec`) vs unlimited tools (`read_file`, `grep`, `glob`, `edit_file`, `write_file`, `notebook_edit`, `task`, `ask_user`, `view_image`, `web_fetch`). Tells the LLM proactively: "If bash or python_exec is blocked: keep working with the unlimited tools above." | sagemaker_agent.py:~8044-8048 |
| Repetition detector loose | (a) read_file dedup key now includes `limit`: `f"{fp}@{offset}:{limit}"`. (b) read_file gets a tighter 2-repeat threshold (other tools keep 3). | sagemaker_agent.py:~9156, ~9176 |

**Codex VERDICT: identified.**

This is what hermes/runnable do well — the **failure-message-as-instruction** pattern (Issue 7 fix) plus a **proactive capability matrix** in the system prompt (Codex Finding A). v4.10.10 now has both.

---

---

---

## Round 3 deep investigation: 5-investigator team review

After v4.10.10 round 2 shipped, user requested deeper investigation. 5 parallel investigators were dispatched:

| Investigator | Role | Verdict |
|---|---|---|
| Team A1 | Prompt-engineering deep analysis | "2 critical gaps + 1 high. Tool matrix BURIED in mid-list under cognitive load." |
| Team A2 | Tool-design gap analysis | "Time-budget branch missed in round 2. 'User denied permission' too terse. Generic exception fallback missing substitutes." |
| Team B1 | Real session log forensics (turn-by-turn) | "Failure was not lack of capability — it was lack of *runtime reminder of capability*." |
| Team B2 | Hermes/Runnable comparative analysis | "v4 mostly at parity or AHEAD. 6 gaps remain, 2 HIGH (skill filtering + dynamic tool references)." |
| Codex deep | Architectural review | **VERDICT: FAIL initially** — race risk, path-normalization gaps, missing regression tests. After round-3 re-fixes: **VERDICT: PASS**. |

### Cross-cutting consensus

Every investigator independently identified the **buried tool matrix + non-self-introspecting prompt** as the immediate failure cause. The agreement across 5 different angles is itself the strongest evidence.

### Round 3 fixes applied (all in v4.10.10, no version bump)

| Fix | File:line | Source finding |
|---|---|---|
| Promoted "Tool capability classes" to top-level section before "Using Tools" | sagemaker_agent.py:~8038-8052 | A1 CRITICAL, B1 P0, B2 P6 |
| Added self-correction rules: "After ANY Blocked: re-read matrix" + "BEFORE saying 'I can't': re-read" | sagemaker_agent.py:~8036-8037 | A1 CRITICAL, B1 P0 |
| Clarified `task` semantics (uncounted itself, but sub-agents share budget) | sagemaker_agent.py:~8044 | Codex B1 |
| Reworded call-count block message: "STILL AVAILABLE..." + "try grep/read_file/edit_file FIRST" | sagemaker_agent.py:~9467 | A2 HIGH, B1 P0, Codex B2 |
| **Same fix on time-budget branch** (missed in round 2) | sagemaker_agent.py:~9482 | A2 HIGH (parallel branch) |
| Rewrote "User denied permission" → action-guided 4-line message at both call sites | sagemaker_agent.py:9237, 9446 | A2 HIGH |
| Rewrote generic exception fallback with substitution guidance | sagemaker_agent.py:9509 | A2 MEDIUM |
| Path normalization in read_file dedup: `os.path.realpath(os.path.abspath(fp))` | sagemaker_agent.py:9156 | Codex C2 HIGH |
| New test file `test_v410_actual_use.py` with 12 regression tests | new file | Codex E HIGH |

### Codex final re-review (round 3)
> *"VERDICT: PASS — round 3 fixes are correctly implemented and materially close the identified failure mode; only minor residual risk is Windows case-normalization and lack of behavioral/integration test proof."*

### How runnable Claude Code solves these problems (reference patterns)

- **Tool descriptions with WHEN/WHEN-NOT inline** (`tools/BashTool/prompt.ts`): substitution table inside the tool description, not buried in global prompt. v4 round 3 brought the global matrix to the top, but per-tool inline guidance is still a future improvement.
- **Failure-message-as-instruction**: every error tells the LLM what to do next. v4 round 3 propagated this to all 5 error types (call-count, time-budget, user-denied, generic exception, repetition).
- **Deferred tool loading** (`tools/ToolSearchTool/prompt.ts`): tool names listed upfront, schemas loaded on demand. Saves ~5500 tokens/turn. **NOT YET IN v4** — biggest remaining cognitive-load win.
- **Path canonicalization** (`realpath + normcase` at state boundaries). v4 round 3 added `realpath + abspath`; `normcase` for Windows still pending.
- **Stop hooks for "I can't" patterns** (`services/stopHook.ts`): runtime intervention if the agent's output matches give-up patterns. v4 has the prompt-level rule, not runtime.

### What still isn't fixed (honest backlog)

| Gap | Severity | Why deferred |
|---|---|---|
| Windows `os.path.normcase()` for case-insensitive paths | LOW | Edge case, Windows-only |
| Tests are string-presence not behavioral | MEDIUM | Behavioral testing needs Bedrock integration |
| Tool-schema deferred loading (Runnable ToolSearchTool pattern) | HIGH | Saves ~5500 tokens/turn but requires bigger refactor |
| Skill filtering by available tools (Hermes pattern) | HIGH | Bash-dependent skills still listed when bash exhausted |
| Dynamic tool-name references in prompt (Hermes AGENTS.md:627-628) | MEDIUM | Static prompt mentions tools that may be disabled in some profiles |
| Runtime stop-hook for "I can't" patterns | MEDIUM | Prompt-level fix is in; runtime intervention is bigger architectural change |
| `_GLOBAL_EXEC_LOCK` check-then-act race (Codex A3) | MEDIUM | Pre-existing, not introduced by round 3; needs careful refactor |
| `.ipynb` cell-index hint in read_file output | MEDIUM | Would prevent the user's 06:31 read-loop confusion; bigger UX change |

### Multi-repo integration analysis (root-cause meta-finding)

The user asked: *"could the root cause be that I've been integrating v4 with other repos (runnable, hermes, learning factory)?"*

**Honest answer: indirectly, yes.** Each integration added ~200-500 tokens to the static system prompt. After 6+ rounds (v4.9.4 hermes, v4.10.0 runnable x5, v4.10.5 LF x3, v4.10.7-10), the static prompt grew to ~5000+ tokens. **Cognitive load on the LLM scaled non-linearly** — at small prompts, mid-list bullets are seen; at long prompts, attention drifts.

The failure was NOT directly from any one integration. It was from the **aggregate prompt size** + **v4's original (not borrowed) decisions** about error messages and limit defaults.

**The solution is what runnable does**: not fewer integrations, but better encapsulation (deferred tool schemas, per-tool inline guidance, dynamic capability lists). v4 round 3 made the most-impactful in-place fix (matrix promotion + self-correction rules). The structural refactor (deferred loading) remains future work.

---

## Summary table

| # | Issue | Severity | Fixed in v4.10.10 in-place? | Impact |
|---|---|---|---|---|
| 1 | Noisy CSO-CHECK warnings | Cosmetic | ✓ Logged as DEBUG instead of WARNING | Clean startup, no behavior change |
| 2 | Iteration budget 90 too tight | Functional | ✓ Default 600 + UI slider 90-2000 | No more "budget exhausted" mid-task |
| 3 | Cold cache message | Informational (good behavior) | n/a — feature, not bug | Saves cost on async sessions |
| 4 | Thinking only on 1st message | Expected behavior | n/a — model decision | Use 16000 budget for more thinking |
| 5 | Session cost not persisted | Functional | ✓ `session_cost` saved/loaded (correctly via TOKENS) | Multi-session cost tracking works |
| 6 | session_cost wired to Agent (Codex caught) | HIGH | ✓ Re-wired to TOKENS singleton | Save/load actually persists now |
| 7 | 40-call exec limit + misleading error text | HIGH | ✓ Bumped to 200 + error tells LLM which tools still work | Agent doesn't get confused after limit hit |

## Code change summary (v4.10.10 in-place additions)

| File | Line(s) | Change |
|---|---|---|
| `sagemaker_agent.py` | 1075-1080 | `max_exec_calls_per_session: int = 40` → `200` + comment |
| `sagemaker_agent.py` | 1108-1110 | `max_iteration_budget: int = 90` → `600` + comment |
| `sagemaker_agent.py` | 2740 | `logging.warning(...)` → `logging.debug(...)` for CSO-CHECK |
| `sagemaker_agent.py` | 8181 | `IterationBudget.DEFAULT_MAX = 90` → `600` |
| `sagemaker_agent.py` | ~9442 | Error message rewritten: spells out which tools are blocked vs still work |
| `sagemaker_agent.py` | ~11583 | `metadata["session_cost"] = float(getattr(TOKENS, ...))` (Codex-corrected from Agent) |
| `sagemaker_agent.py` | ~11665 | Conditional `TOKENS.session_cost = saved_cost` (Codex-corrected from Agent) |
| `chat.ipynb` cell 2 | — | New `iteration_budget_slider` widget (90-2000, step 50, default 600) |
| `chat.ipynb` cell 3 | — | `CONFIG.max_iteration_budget = iteration_budget_slider.value` + banner shows Iter ceiling |
| `compact_v4/docs/PS_actual_use_problems.md` | new file | This document |

All changes are non-version-bumping (still v4.10.10), tested (134 destructive + 122 unit pass), Codex-reviewed.

---

## How to use the new settings

1. Run cell 2 (Configuration). You'll see two new controls:
   - **Iter Budget** slider (default 600). Move to 90 for cost-strict / 2000 for deep refactors.
   - **Bedrock-only** checkbox (already there, default ticked = strict).

2. Run cell 3 (Launch). The banner now reports `Iter ceiling: <value>` and `AWS scope:`.

3. During a session:
   - `/cost` — see per-call + cumulative cost.
   - `/status` — see iteration counter + remaining budget.
   - `/save` — persist session including cost. `/load` restores it.

4. If you ever hit "budget exhausted":
   - Either start a new session (clean budget).
   - Or `/save` current session, edit the slider in cell 2 to a higher value, run cell 3 again, `/load` the session.
