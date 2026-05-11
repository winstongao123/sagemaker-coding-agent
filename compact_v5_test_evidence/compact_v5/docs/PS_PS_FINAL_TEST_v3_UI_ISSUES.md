# PS_PS_FINAL_TEST_v3 — UI/UX issues found in personal real-use test

Date: 2026-05-10
Author: Claude (analysis only, no code changes)
Companion: PS_PS_FINAL_TEST_v3_RESULT.md (acceptance PASS, but this is the human-facing UX gap)

## Why this doc exists

The v3 acceptance benchmark passed (Bedrock Haiku, 76 tests green, $0.71 cost,
end_turn). But when the user ran the same v5 build by hand in `chat.ipynb`, the
session **felt stuck** even though the engine was working fine. This doc lists
every concrete UI gap vs `compact_v4` that produced that "stuck" feeling, plus
how to fix each — so a worker can patch them without re-discovering the diff.

All v4 references are file paths in `compact_v4/MAIN/agent/sagemaker_agent.py`.
All v5 references are file paths in `compact_v5/compact_v5/ui/chat_ui.py` unless
noted.

---

## Problem 1 — Metrics stack in one column instead of two-per-row

### What the user sees
Bottom-of-chat metrics block renders as one tall column:

```
In 2,432 | Out 27,275 | Prompt Cache R/W ... | Saved ... | Calls ...
Cost: ... | Last: ... | Without cache: ... | Cache saved: ... | (pricing)
Reasoning: Thinking ON ...
Agents: parent $... (.../...; cache .../...)
AWS scope: ...
Context: 14% (...)
[bar]
Budget: 11% ($...)
[bar]
```

### What v4 did (the visual contract being broken)
v4 packed paired metrics on the same row using a flex container:

```html
<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px;">
  <span>In {n} | Out {n} | Calls {n}</span>
</div>
<div>{cost_line}</div>
<div>Context: {pct}% ...</div><div bar/>
{budget_block (Budget + bar)}
```
(`compact_v4/MAIN/agent/sagemaker_agent.py:10461-10476`)

v4 also placed the Context bar and Budget bar inline so they read as **paired
gauges**, not two unrelated rows.

### Where v5 broke it
`compact_v5/compact_v5/ui/chat_ui.py:829-841` — every metric is its own
`<div>` inside a single column container. No flex, no wrap.

### Fix (for worker)
- Wrap the In/Out/Calls line + the Cost/Last/Without-cache/Cache-saved line in
  a `display:flex; flex-wrap:wrap; gap:8px 16px;` container so they sit
  side-by-side on wide notebooks and stack only on narrow ones (matches v4
  behaviour).
- Keep the two progress bars (Context, Budget) directly under their label
  lines, but consider rendering them as a 2-column grid (left = Context bar,
  right = Budget bar) on wide notebooks.
- Reasoning / Agents / AWS-scope are operational status, not metrics — move
  them into the bottom `_mode_html` strip (line 842-855) where status flags
  already live, instead of cluttering the tokens panel.

---

## Problem 2 — Token usage looks higher than v4 for similar tasks

### What the user sees
For the notes_cli build (one task, partial run before user clicked Stop):

```
In 2,432 | Out 27,275 | Prompt Cache R/W 804,736/217,150 | Cost $0.5371
Without cache $1.2614 | Cache saved $0.7243 | Calls 48 | Thinking ON (budget 4096)
```

The user's read: 27k output tokens for one Stop'd turn feels high.

### Likely contributors (worker should measure each, not assume)
1. **Thinking ON, budget 4096.** Each LLM call can emit up to 4096 reasoning
   tokens *in addition* to the visible output. Across 48 calls that can add
   tens of thousands of output tokens. Test by running the same prompt with
   Thinking OFF and comparing `Out` total.

2. **System-prompt size.** v5 splits prompt across `prompt/` package
   (compact_v5/compact_v5/prompt/) — verify the assembled system prompt is
   not larger than v4's `SYSTEM_PROMPT` constant. Cache hit rate
   (804k read / 217k write) suggests cache is working, so this is probably
   not the dominant cost — but worth a one-off `len(system_prompt)`
   comparison.

3. **No pre-send / microcompact between turns.** v4
   (`sagemaker_agent.py:11407` `do_pre_send_compact()` and `:11514`
   post-send prune) trims tool outputs *before* re-sending the conversation.
   Worker: search compact_v5 for `prune_tool_outputs`, `microcompact`,
   `pre_send_compact`. If absent or not wired into the per-turn loop, every
   subsequent turn re-pays the full tool-result history.

4. **Per-turn meta in chat history.** Each assistant message in v5 carries
   a `meta` dict that the UI renders as a `<details>` thinking block. Confirm
   that `meta.thinking` is **not** appended to the conversation that goes
   back to Bedrock — the visible UI is fine, but if the engine round-trips
   thinking text into the next request, prompt size balloons.

### Fix shape (do not do all of these — measure first)
- Default Thinking OFF in cell 2 to match v4's default; let the user opt-in.
- If pre_send_compact / prune_tool_outputs are missing, port the v4 logic
  into the v5 engine's `agent.run` boundary (look for the equivalent of
  `_release_lock` in compact_v5/compact_v5/agent.py).
- Verify cache_control is set on system prompt, tools list, and the stable
  conversation prefix — the 804k/217k cache R/W ratio looks healthy, but
  worth `grep cache_control compact_v5/compact_v5/runtime/`.

---

## Problem 3 — AI response shown as raw markdown / mixed log instead of formatted

### What the user sees
The agent's final message ends up looking like a wall of plain text + the
"Reasoning / thinking captured for this turn" expansion shows lines like:

```
This is a comprehensive request to:
1. Create a folder structure for a Python CLI project
2. Build a notes_cli project ...
```

…rendered as raw, escaped text. Visually it reads like "v5 didn't render the
markdown."

### What v4 did
v4 kept four chat-row roles, each with its own card style:
- `user` — blue left bar
- `assistant` — green left bar, full markdown render
- `tool` — distinct card with tool name header + scrollable result body
- `thinking` — purple/italic, separate from the assistant message
- `system` — yellow/gray, for `[Warning]`, `[!]`, `[i]`, `[STOP]`, etc.

(`sagemaker_agent.py:10480-10484` `add_message(role, content, tool_name)` then
the `render_chat()` switch on role.)

v4's output_fn (`sagemaker_agent.py:11375-11403`) routed each chunk to the
right role:
- `[Calling ...]` → swallowed (don't display)
- `[<tool> result]:` → `tool` role with the matching tool name
- `[Warning|!|i|Reached ...]` → `system`
- bare prose → `assistant`

### Where v5 broke it
`compact_v5/compact_v5/ui/chat_ui.py:506-519` (`_render_chat`) only knows
three roles: `user`, `assistant`, `system`. There is no `tool` role and no
`thinking` role. So:
- Every tool call/result that v4 would have shown as its own neat card is
  either dropped (because `_run_message` only forwards `[`-prefixed strings
  as one merged system blob) or smushed into the assistant text fallback
  (`result.text or "\n".join(streamed)` at line 982-986).
- The thinking content gets rendered through `_render_turn_meta` (line 877-886)
  which **html-escapes the raw thinking string and joins lines with `<br>`** —
  intentionally not markdown-rendered, but the user sees numbered lines and
  paragraphs and reads it as "broken markdown".

### Fix (for worker)
1. Restore the `tool` chat role:
   - Extend the message tuple to `(role, text, ts, meta, tool_name)` (or
     keep tool_name inside `meta`).
   - In `_render_chat` add a branch for `role == "tool"` that renders a
     bordered card with the tool name as a small header and the result body
     in a scrollable monospace pre.
2. Restore the `thinking` chat role for live thinking that's emitted *during*
   the run (separate from the per-turn meta panel which is fine where it is).
3. In `_run_message` (line 959-995) replace
   `output_fn=lambda s: streamed.append(str(s))` with a router that calls
   `self._append_message` immediately, copying v4's logic at
   `sagemaker_agent.py:11375-11403`. Concretely:
   ```python
   def _live_output(text: str) -> None:
       if text.startswith("[Calling "):
           return
       m = re.match(r"^\[(\w+)\s+result\]:", text)
       if m:
           tool = m.group(1)
           body = text[m.end():].strip()
           self._append_message("tool", body, tool_name=tool)
           self._render_status()
           return
       if text.startswith(("[Warning", "[!]", "[i]", "[Reached", "[Stopped",
                           "[final-claim", "[subagent:")):
           self._append_message("system", text)
           return
       if text.strip():
           self._append_message("assistant", text)
           self._render_status()
   ```
4. Remove the `ops[-30:]` truncation at line 979-981 — the user wants every
   tool call visible, not the last 30 grouped into one system blob.

---

## Problem 4 — Looks "stuck" because nothing renders during the run (the big one)

### What the user sees
After clicking Send, the chat shows nothing for ~4 minutes. Then everything
appears at once when the agent finishes (or when the user clicks Stop). The
user reasonably concluded the agent was hung, even though it was making 48
API calls and 76 passing tests in the background.

### Root cause (single line)
`compact_v5/compact_v5/ui/chat_ui.py:976`:
```python
result = self.agent.run(msg, output_fn=lambda s: streamed.append(str(s)))
```

`output_fn` only appends to a Python list. The chat HTML widget is **not
touched** until after `agent.run` returns. So during the entire turn there is
zero UI feedback.

### What v4 did
`sagemaker_agent.py:11507`:
```python
ui_state["agent"].run(msg, output_fn, system_prompt=..., plan_mode=...)
```
where `output_fn` is the live router from Problem 3 above, calling
`add_message(...)` → `render_chat()` → `widgets.HTML.value = ...` immediately
on the daemon thread. ipywidgets pushes the new HTML to the front-end as
soon as `.value` is reassigned, so each tool call/result appears within
~milliseconds of being emitted.

### Fix (for worker)
This is the **same change as Problem 3 step 3** — wire `output_fn` to the
live router. Once that lands, every tool call, every system warning, every
streamed assistant chunk shows up in the chat as it happens.

Also call `self._render_status()` inside the live router so the metrics bar
updates per tool — matches v4's `update_tokens_display()` behaviour
(`sagemaker_agent.py:11394, 11403`).

Threading note: the v5 UI already runs `self._run_message` on a daemon
thread (line 953-957), and ipywidgets value updates from a non-kernel thread
are safe — v4 has been doing this for a year. No change needed there.

---

## Problem 5 — No subagent visibility (only start + finish lines)

### What the user sees
```
[subagent:review] started: Code review of notes_cli project
[final-claim guard: evidence is not ready; continuing]
[subagent:review] finished: stop=end_turn turns=17 cost=$0.1780 cache=254,291/76,711
```

That's all. The reviewer sub-agent ran 17 turns; the user saw 0 of those.

### Root cause
The parent's `_run_task_tool` (or v5 equivalent in `compact_v5/compact_v5/subagent/` or `agent.py`) calls the sub-agent like
this in v4:
```python
output_fn=lambda t: (sub_output.append(str(t)) if len(sub_output) < 200 else None)
```
(`sagemaker_agent.py:8562`)

That captures the sub-agent's chatter into a local list, never forwards it
back to the parent's UI `output_fn`. The parent only sees the final
`task_result` string and the bracketed status lines emitted at the boundary.

v4 had the same blind spot — the user's expectation has *grown* with v5
(because v5 is supposed to be "better than v4"), so the gap now feels
unacceptable.

### Fix (for worker)
- In the v5 task-tool boundary, accept a `parent_output_fn` and wire the
  sub-agent's `output_fn` to forward selected lines up:
  ```python
  def _sub_output(t: str) -> None:
      if len(sub_output) < 200:
          sub_output.append(str(t))
      # Forward to parent UI with a sub-prefix.
      if parent_output_fn is not None:
          parent_output_fn(f"[{subagent_kind}:sub] {t}")
  ```
- The UI router from Problem 3 already routes `[subagent:` to the system
  role; tweak the regex so `[<kind>:sub]` lines render as a slightly
  indented system message (or wrap them in a `<details>` block keyed by
  sub-agent id so the chat stays clean for power users).
- Optional: render an "active sub-agent" pill in the header (small badge)
  while a sub-agent is running, so the user knows *who* is talking even
  when the lines are sparse.

---

## Problem 6 — `[final-claim guard: evidence is not ready; continuing]` chatter
### What the user sees
The line repeats during long runs. With Problem 4 unfixed, it only appears
at the end and gives the impression "v5 was looping the verify gate".

### Root cause
v5's verify gate (search `compact_v5/compact_v5/runtime/` and `subagent/`
for `final_claim` or `evidence_ready`) is firing through `output_fn` —
which buffers it. Once Problem 4 is fixed and these lines stream live,
they will be informational rather than alarming. But the wording is also
ambiguous.

### Fix (for worker)
- Reword to something positive and progress-flavoured, e.g.
  `[verify gate: gathering evidence (turn 12)]` or
  `[verify gate: missing test report; agent will retry]`.
- Throttle: emit at most once every N turns or whenever the missing
  evidence set changes — repeating the identical line every turn adds
  noise without information.

---

## Problem 7 — `_render_status` rebuilds full HTML on every send

This is not what the user reported but worth flagging while a worker is in
the file. `_render_status` (line 737-855) reads `TOKENS.get_stats()`,
`get_cache_savings_usd()`, agent budget, the full subagent attribution map,
and assembles a 12-line HTML string on every call. With Problem 4 fixed
(per-tool refresh), this runs hundreds of times per turn. Profile before
optimising; if it shows up, cache the static parts (model, region,
pricing, mock flag, exec_mode) and only refresh the numeric bits.

---

## Suggested patch sequence for the worker

1. **First**: fix Problem 4 (live streaming) AND Problem 3 (tool/thinking
   roles + output_fn router). They're the same 60-line change in
   `_run_message` + `_render_chat` and they unlock 80% of the UX gap.
2. **Second**: fix Problem 1 (metrics layout) — pure CSS/HTML in
   `_render_status`. ~20 lines.
3. **Third**: fix Problem 5 (sub-agent forwarding) — ~30 lines in the
   v5 task-tool boundary plus a regex tweak in the UI router.
4. **Fourth**: investigate Problem 2 (token usage) — measure first, then
   port v4's pre_send_compact / prune_tool_outputs if missing.
5. **Last**: cosmetic — Problem 6 wording, Problem 7 if profiling says so.

After each step: run the `notes_cli` task by hand from `chat.ipynb` and
confirm the UI behaves like v4 plus the new live-subagent stream.

## What NOT to change

- The engine layer (agent.py, runtime/, prompt/, subagent/, tools/) — it
  passed v3 acceptance. The fixes above are all in
  `compact_v5/compact_v5/ui/chat_ui.py` and the small task-tool boundary
  in v5's subagent dispatcher (Problem 5).
- The chat.ipynb cells — Cell 2 / Cell 3 are fine. Defaulting Thinking
  OFF (Problem 2) is the only ipynb tweak.
- The acceptance test (`PS_PS_V3_COMPARE_REPORT.md` etc.) — it reflects
  the engine, not the UI, and remains valid.

---

## Implementation Status - v5.0.2 UI Live Supervisor

Date updated: 2026-05-11

| Problem | Status | Implementation |
|---|---|---|
| Problem 1: metrics stack in one column | Fixed | `_render_status()` now uses a wrapping flex row for token/cache/cost/call metrics and a responsive two-column grid for Context and Budget gauges. Operational mode text moved to the mode strip. |
| Problem 2: token usage looks higher than v4 | Measured, not optimized | UI now shows a display-only cost-driver line covering input/output dominance, calls, average output per call, Thinking ON/OFF, cache percentage, and subagent attribution. No model, prompt, cache, compaction, or thinking default was changed. |
| Problem 3: raw markdown / mixed logs | Fixed | Chat rows now include `tool`, `thinking`, and `subagent` roles. Assistant markdown still renders tables, lists, and code blocks; tool output renders as bounded cards. |
| Problem 4: nothing renders during run | Fixed | `agent.run(..., output_fn=...)` is now wired to a live UI router that appends messages and refreshes status while the run is active. The old list-only buffer path is no longer the UI path. |
| Problem 5: no subagent visibility | Fixed | `task` forwards child output through `[subagent:<type>:child]`; UI renders start, child updates, finish, selected child output, stop reason, cost/cache, and artifact paths from the existing envelope. |
| Problem 6: final-claim guard chatter | Improved by live context | Guard lines now stream live as system/status messages instead of appearing as a delayed blob. Wording/throttling in the engine was not changed to avoid non-UI drift. |
| Problem 7: status rebuild frequency | Measured / accepted | The UI refreshes status during live output. No caching optimization was added; profiling should precede any performance change. |

Claude CLI review note: each block saved a Claude prompt and output under
`compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/`. The CLI
returned `Credit balance is too low` for every review attempt, so no Claude
verdict was available. Local drift checks and zero-cost smoke checks were used
as the continuation gate.

## Final Follow-Up Status - 2026-05-11

Codex reviewed the worker output and found three remaining blockers:

1. assistant messages beginning with bracket headings such as `[SPEC vs SHIPPED]`
   were still routed as system cards;
2. parsed `task`/subagent result envelopes rendered twice: once as a subagent
   summary and again as a raw tool card;
3. `compact_v5.zip` was stale after the source fixes.

Fixes applied:

- `_live_output_router()` now uses a known-prefix status allowlist instead of
  treating every bracket-leading line as system output.
- `_on_tool_generation()` now returns after rendering a parsed `task` envelope
  as a subagent card, avoiding raw JSON duplication.
- `test_ui_live_supervisor_smoke.py` now covers bracket-leading assistant text,
  known bracket status routing, task-envelope deduplication, live rendering
  before `agent.run()` returns, and Stop status during a slow in-flight run.
- Fresh visual evidence was generated:
  `compact_v5_test_evidence/final_results/UI_LIVE_SUPERVISOR_FINAL_VISUAL_20260511.html`
  and `.png`.
- `compact_v5.zip` was rebuilt from `compact_v5/compact_v5/` and verified with
  `zipfile.testzip()`, required-member presence, forbidden-member absence, and
  required-member SHA-256 hash parity against the active source tree.

Claude review correction:

- The earlier worker used an API-token route and got `Credit balance is too
  low`.
- Codex reran Claude with the documented subscription-auth command:
  `C:\Users\winst\AppData\Roaming\npm\claude.cmd`, `ANTHROPIC_API_KEY` cleared
  for the child process, `CLAUDE_CODE_USE_BEDROCK` cleared, `--setting-sources
  user`, and `--permission-mode dontAsk`.
- The first usable Claude review requested changes because the zip was stale;
  after rebuilding and hash-verifying the zip, final review status is recorded
  under `compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/`.
- Post-zip Claude re-review returned `SHIP DECISION: APPROVE` with no findings:
  `compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/UI-LIVE-SUPERVISOR-FINAL-20260511-post-zip_claude_review.md`.

## Real-Use S3 Follow-Up - 2026-05-11

A later hand-run prompt, `list file and bucket structure of my s3`, exposed a
separate class of issues that are **not** closed by the UI live-supervisor
approval above. See `PS_PS_FINAL_TEST_v3_REAL_USE_ISSUES.md`.

Current distinction:

| Area | UI live-supervisor status | S3 real-use status |
|---|---|---|
| Live streaming | Fixed and reviewed. | Not the main failure in the S3 run. |
| Tool role existence | Fixed: `tool` role exists. | Still open: cards are expanded, not grouped/collapsed. |
| Thinking display | Role exists and default source constructor is OFF. | Still open: captured thinking renders after metrics and appeared expanded in the user's kernel. |
| Metrics | Fixed for layout/visibility. | Still open: metrics reveal high-cost behavior but do not prevent it. |
| Drift | Not covered by the UI approval. | Open: S3 request drifted into compact_v5 source-tree inventory. |
| AWS/S3 access | Not covered by the UI approval. | Open: `aws s3` is blocked and boto3 failed on Python sandbox import `linecache`. |

Do not treat the UI live-supervisor Claude approval as proof that the S3
workflow is production-ready. It only approved the earlier UI streaming/card
patch set.
