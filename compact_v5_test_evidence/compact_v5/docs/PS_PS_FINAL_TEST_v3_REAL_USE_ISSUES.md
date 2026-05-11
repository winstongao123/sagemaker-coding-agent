# PS_PS_FINAL_TEST_v3 — Real-use issues from S3-listing session

Date: 2026-05-11
Author: Claude (diagnostic only, no code changes)
Trigger: user ran v5 by hand with prompt "list file and bucket structure of my s3"
Companions:
- `PS_PS_FINAL_TEST_v3_UI_ISSUES.md` — UI gaps from the notes_cli session (2026-05-10)
- `PS_PS_FINAL_TEST_v3_RESULT.md` — v3 acceptance PASS (engine correct)
- `PS_V5_VS_RUNNABLE_DEEP_REVIEW_20260511.md` — cross-codebase deep review
- `PS_TEST_REVIEW_FINAL.md` — major-issue history

## Why this doc exists

The v3 acceptance benchmark passes, the engine is correct, but a second
hand-run by the user surfaced a different *class* of problems than the
notes_cli session — not just UI rendering, but:
- **task drift** (agent forgets the original ask),
- **misdiagnosis of its own sandbox** (says "Bedrock-only" when config is OFF),
- **dead-end tool paths** (`aws` CLI blocked, boto3 broken by Python sandbox),
- **cost waste from retry chains and verbose framing**,
- **thinking-block ordering** inside the assistant bubble.

This doc lists each problem with the transcript line, the architectural
root cause, and the smallest fix-shape. Combined with the UI-issues doc,
this is the full real-use-test punch list as of 2026-05-11.

## Codex consolidation update - 2026-05-11

Codex cross-checked this Claude diagnosis against the current flattened active
tree. The current source path is `compact_v5/`; any older
`compact_v5/compact_v5/` references are historical/nested-layout references
from earlier workers.

### What Claude found that is confirmed

| Finding | Current evidence | Current status |
|---|---|---|
| Thinking block renders after metrics | `_render_turn_meta()` appends `thinking_html` after the metrics `summary` in `compact_v5/ui/chat_ui.py`. | **Open** |
| Tool cards are not collapsed | `role == "tool"` exists, but renders an expanded `<pre>` with max-height instead of a closed summary/body card. | **Open** |
| Drift happened in the S3 transcript | The response misdiagnosed Bedrock-only mode, then switched from S3 inventory to codebase inventory. | **Open** |
| S3 read path is contradictory | Docs/status say S3 read/list is allowed when Bedrock-only is OFF, but `aws s3` is blocked and boto3 import failed on `linecache`. | **Open** |
| Cost was inflated by retries and prose | 7 calls, 2,636 output tokens, Thinking ON, blocked retries, tool_search, and verbose local-tree summary. | **Open** |

### Corrections to avoid stale worker actions

| Claude statement | Correction from current source | Worker implication |
|---|---|---|
| "Tool role still missing." | A `tool` role now exists in `compact_v5/ui/chat_ui.py`; the remaining bug is collapse/grouping/default-closed rendering. | Do not re-add the role. Restyle/group the existing role. |
| "Default Thinking OFF should be changed in Cell 2." | The current UI constructor default is already `thinking_enabled=False`; the user's run still showed Thinking ON, likely from CONFIG/session/user toggle/deployed zip state. | Diagnose why SageMaker session had Thinking ON before changing defaults again. |
| "Use `compact_v5/compact_v5/...`." | Active repo tree is flattened `compact_v5/...`; zip should be rebuilt from that tree. | Do not recreate nested layout. |
| "Plan Mode would avoid failures." | Plan Mode is read-only, but the concrete S3 path still needs one working safe read mechanism. | Plan Mode is helpful guidance, not a substitute for fixing S3 access. |

### Consolidated open punch list

| Priority | Issue | Required proof before marking solved |
|---|---|---|
| P0 | S3 safe-read path: either dedicated S3 list/get/head tool, or working boto3 sandbox path. | Real SageMaker smoke: list buckets and first-level object prefixes without using blocked `aws s3` CLI. |
| P0 | Drift guard: response must stay anchored to "list my S3 buckets" after fallback choices. | Transcript test where user selects a fallback and final answer explicitly says whether S3 was answered, partially answered, or still blocked. |
| P0 | Wrong self-diagnosis: do not claim Bedrock-only when `CONFIG.aws_bedrock_only=False`. | Unit/smoke with blocked AWS path verifies message names bash allowlist or Python sandbox accurately. |
| P1 | Tool cards collapsed/grouped. | UI fixture/screenshot shows call/result cards closed by default and grouped for parallel dispatch. |
| P1 | Thinking placement/collapse. | UI fixture/screenshot shows reasoning outside the final-answer body and not expanded as plain text. |
| P1 | Cost control for simple inventory tasks. | Same S3 prompt runs with no repeated blocked-tool shape, no large follow-up menu, and materially fewer calls/output tokens. |
| P2 | Deferred-tool tax for common tools. | Measurement compares schema/call cost before and after changing deferral policy for `list_dir` or other common read tools. |

These are documentation findings only. No runtime/source patch is implied by
this consolidation entry.

## Transcript origin

User prompt: `list file and bucket structure of my s3`

What the agent did (abbreviated):
1. Tried `aws s3 ls` → blocked by bash allowlist
2. Tried `aws s3 ls --recursive` → same block
3. Tried `boto3.client('s3')` via python_exec → `ImportError: Security: import 'linecache' is not in the allowed modules list`
4. Posted a 3-option workaround menu
5. User chose Option 2 ("explore local directories")
6. Agent toured `compact_v5/` codebase, never returning to S3

Session totals at the end:
`In 70 | Out 2,636 | Calls 7 | Cost $0.0649`

Status bar at the same moment:
`Bedrock-only: OFF | Plan: OFF | Thinking ON (4096) | Auto-Compact: ON`

---

## Problem 1 — Thinking block at wrong place in the assistant bubble

### What the user sees
Inside one assistant turn:
```
Agent text…
In 40 | Out 1,356 | Cache R/W 36,025/17,193 | Cost $0.0351 | … | Thinking ON (budget 4096)
Reasoning / thinking captured for this turn
The user wants Option 2, which is to explore local directories…
```

Thinking is rendered *below* the metrics line, and the content appears
expanded (not collapsed) in the user's render.

### Root cause
`compact_v5/compact_v5/ui/chat_ui.py:870-891` — `_render_turn_meta` emits:
1. summary metrics line,
2. then `<details>` containing the thinking block.

So order within the bubble is `assistant text → metrics → thinking`.
Logically thinking happens *before* the answer; rendering it last is
chronologically backwards.

Second layer: `<details>` may not be auto-collapsing in this Jupyter
kernel. If the host strips/ignores `<details>`, the block displays
expanded, which compounds the ordering issue.

### Fix shape (for worker)
- Reorder `_render_turn_meta` to emit thinking `<details>` *between* the
  assistant text and the metrics line, OR
- Render thinking as its own chat row (v4's `thinking` role) so it sits
  above the assistant text and the metrics stay at the bubble bottom.
- Quick render-check: open the chat HTML in a real Jupyter kernel and
  confirm `<details>` collapses by default. If not, swap to a manual
  ToggleButton-driven `Output` widget.

---

## Problem 2 — Tool use not collapsed; output dumped raw

### What the user sees
```
[00:04:13] Tool: bash:
call requested
{ "command": "find . -type d -maxdepth 3 | head -50" }
[00:04:13] Tool: bash:
result
. (~50 raw lines)
```

Every `call requested` and every `result` is a fully-expanded chat row.
No preview, no `<details>`, no per-tool grouping. Three parallel bash
calls dump three giant rows.

### Root cause
Two:
- **`tool` role still not implemented in `_render_chat`** (already
  flagged as Problem 3 in `PS_PS_FINAL_TEST_v3_UI_ISSUES.md`). v5's
  chat only knows user/assistant/system. Tool blocks are coming through
  as system rows with no truncation.
- **No grouping of parallel calls**: `core/parallel_dispatch.py` runs
  3 reads side-by-side, but the UI receives them as 6 unrelated system
  messages (3 call requests + 3 results).

### Fix shape (for worker)
- Add `tool` role with header (`bash · find . …`) + `<details>` body
  showing full output in scrollable `<pre>`. First line of result as the
  summary preview.
- For parallel dispatch: emit one parent system message
  `[parallel: 3 bash calls]` and nest the three tool cards under it.
- Stretch goal: clicking the header `<details>` should keep the
  metrics-strip below visible (so users can see cost while inspecting
  tool output).

---

## Problem 3 — Drift (the most important issue here)

### Trace of intent
- t=0 user: "list file and bucket structure of my s3"
- agent tries `aws s3 ls`, fails
- agent tries `aws s3 ls --recursive`, same failure
- agent tries boto3, fails on Python sandbox
- agent offers Option 1 (CLI manually), Option 2 (explore local), Option 3 (ask admin)
- user picks Option 2
- **agent then describes the compact_v5/ source tree as if it were the answer**

### Two stacked drifts

**Drift A — sandbox misdiagnosis.** Agent's apology text claims
`The environment appears to be in Bedrock-only mode`. Status bar at the
same moment shows `Bedrock-only: OFF`. The real blockers were:
- `aws` CLI not in `tools/bash.py` allowlist (security, unrelated to
  Bedrock-only flag),
- `tools/python_exec.py` sandbox rejecting `linecache` (transitive stdlib
  import via `logging` → `traceback`), which kills boto3 before it loads.

The model named the wrong cause. It read the symptom ("S3 doesn't work")
and inferred the most familiar config flag, instead of inspecting
`CONFIG.aws_bedrock_only` directly.

**Drift B — original-intent loss.** "Option 2" was the *fallback* in
the agent's own apology menu — "if you'd like me to analyze data
*already in the workspace*". User picked it, but the agent then treated
it as a fresh task ("list workspace directories"). The compact_v5/
codebase contains no S3 data. Agent never re-anchored with something
like "the local directories don't contain S3 data, so we still haven't
answered your original question — would you like me to try X?"

### Root cause
v5 has no per-turn **intent anchor**. The original user message is in
conversation history but isn't re-checked against the proposed action.
The verify-gate (`[final-claim guard: evidence is not ready; continuing]`
from the earlier transcript) currently fires only on the "evidence
persisted" axis, not on the "answer addresses original intent" axis.

This is the same family as the v4 scope-drift incident captured in
`feedback_no_unilateral_scope_narrowing.md` (memory) and the
`LF_LESSON_AGENT_SCOPE_DRIFT.md` lesson — but v5 didn't carry over the
mechanical gate that would have caught it.

### Fix shape (for worker)
- **Smallest viable**: before the agent emits a "final answer" assistant
  message, inject a tiny synthetic guard prompt:
  *"The user's first request in this session was: {first user message}.
  Does this response address that request? If not, label it as a partial
  answer and propose the next step toward the original request."*
- Reuse the existing `final-claim guard` plumbing in
  `compact_v5/compact_v5/runtime/` (search `final_claim` / `evidence`).
  Add an axis: `original_intent_addressed`.
- Stretch: tie this to the verify subagent — but only if
  `CONFIG.enable_intent_guard = True`. Don't auto-add cost without an opt-in.

### Cross-reference with the deep review
`PS_V5_VS_RUNNABLE_DEEP_REVIEW_20260511.md` Axis 2.3 notes v5 has
**receipt persistence** (good) but neither v5 nor Runnable have a
formal intent-drift guard. This is a *new* axis worth adopting that
Runnable doesn't model either.

---

## Problem 4 — High cost driven by retry chain + verbose framing

### Cost numbers from the transcript
Cumulative: `In 70 | Out 2,636 | Calls 7 | Cost $0.0649`
For a single intent (`list my S3 buckets`) that should have completed
in 1-2 calls and a few hundred output tokens.

### Cost drivers ranked

| Driver | Contribution | Why it's wrong |
|---|---|---|
| **7 calls for one intent** | Largest | Retried blocked `aws s3 ls` twice; then boto3; then list_dir; then 3 parallel bash for the workspace tour. |
| **Verbose "Workspace Layout" report** | ~1,500 out tokens | Full tree + section bullets + four follow-up options when user wanted "list S3 buckets". |
| **Thinking ON, budget 4096** | 0–4096 hidden out per call × 7 calls | "List S3 buckets" needs no reasoning budget. Earlier doc Problem 2 already recommended Thinking OFF as default. |
| **`tool_search` for `list_dir`** | +1 call, +tokens | Every deferred-tool first-use pays a schema-fetch round trip. 18 tools are deferred per the prompt-metrics line. |

The status bar even self-narrates the issue:
`Cost drivers to measure first: output tokens dominate (70 in / 2,636 out)`.

Nothing in v5 acts on that telemetry.

### Order-of-magnitude estimate of correct behaviour
Same task done right: ~3 calls, ~600 out tokens, ~$0.015. **~4× cheaper.**

### Fix shape (for worker)
- **Default Thinking OFF** in `chat.ipynb` Cell 2 (already proposed in
  the UI-issues doc).
- **One-strike rule on blocked tools** — `tools/bash.py` and
  `tools/python_exec.py` already return clear "Blocked" strings.
  Add to system prompt: "If a tool returns 'Blocked' / 'not allowed',
  do NOT retry the same shape; pick a different tool or stop."
- **Cap suggestion-menu prose** — when answering a list question,
  return the list, not a four-option re-prompt. Add a single line to
  the assistant style guidance.
- **Promote frequently-used tools out of deferred** — `list_dir`,
  `read_file`, `write_file`, `bash`, `grep`, `glob` are paid-for on
  every first use; the schema-fetch tax is wasted. Move them to
  always-visible in `tools/registry.py`.

---

## Problem 5 — Sandbox configuration gaps (practical bugs)

### 5a. `python_exec` blocks `linecache`
Transcript:
```
ImportError: Security: import 'linecache' is not in the allowed modules list
```

`linecache` is imported transitively by `traceback`, which is imported
by `logging`, which is imported by `boto3`. So **any** boto3 usage
fails at import. boto3 is the standard way to talk to AWS from Python
— blocking it on a SageMaker agent removes the primary AWS access path.

**Root cause:** `tools/python_exec.py` sandbox allowlist is too narrow.
It needs the full transitive closure of stdlib modules pulled by
common imports, or a different sandbox model (whitelist by top-level
namespace, not exact import).

### 5b. `aws` CLI not in bash allowlist
Transcript:
```
Blocked: Command not allowed: 'aws'.
```

`aws` is the canonical CLI for AWS work on SageMaker. The block message
even suggests `python_exec` as a fallback — which is broken (5a). Dead
end loop.

### 5c. Agent's self-diagnosis disagrees with its own status bar
Agent says: `The environment appears to be in Bedrock-only mode`
Status bar says: `Bedrock-only: OFF`

The model isn't consulting `CONFIG.aws_bedrock_only`. The diagnosis
text is a guess based on the failure pattern, not a config read.

### Fix shape (for worker)
- **Allowlist policy decision needed from user**: either add `aws` to
  `tools/bash.py` allowlist (with the same per-arg validation as `git`),
  OR fix `tools/python_exec.py` to allow boto3 imports cleanly. One of
  the two must work for a SageMaker agent.
- **Sandbox-allowlist correctness**: the linecache block is a bug, not
  a feature. Allowlist should be transitive-closed against the modules
  it allows.
- **Surface CONFIG facts in self-diagnostic prompts**: when the agent
  apologises about restrictions, the system prompt should remind it
  to consult `CONFIG.aws_bedrock_only`, `CONFIG.require_tool_approval`,
  and the bash allowlist before naming a cause.

---

## Problem 6 — Other issues spotted in passing

| # | Issue | Evidence |
|---|---|---|
| 6a | **No in-flight "Calling…" pill** — tool rows show only after the call shape is parsed, not while running. | `Tool: bash: call requested` rendered post-fact |
| 6b | **Per-turn `Calls N` vs session `Calls N` not labeled** — two scales overlap in UI. | `Calls 4` in turn-meta vs `Calls 7` in session bar |
| 6c | **Recurring `tool_search` tax** — 18 deferred tools = up to 18 extra LLM round-trips per session for first-use. | `tool_search: query: "select:list_dir"` then `list_dir: call requested` |
| 6d | **Plan Mode not suggested for read-only intents** — listing S3 is read-only; Plan Mode would have routed to safe tools. | Plan: OFF the whole session |
| 6e | **Three parallel bash calls for one question** — could have been one `list_dir` + one targeted glob. | three back-to-back `bash: call requested` |
| 6f | **Final follow-up menu wastes tokens** — every assistant turn ends with "Would you like me to: …?" four options. | menu present even when user gave a complete instruction |
| 6g | **Output-token-dominance is auto-detected and ignored** — status bar tells the truth, nothing acts on it. | `Cost drivers to measure first: output tokens dominate (70 in / 2,636 out)` |

---

## Cross-reference matrix with earlier docs

| Problem here | Already documented? | Where |
|---|---|---|
| 1 Thinking block ordering | New | This doc |
| 2 Tool use not collapsed | Partly | `_v3_UI_ISSUES.md` Problem 3 (no `tool` role); collapse + grouping is new |
| 3 Drift | New | This doc — propose new axis "original_intent_addressed" |
| 4 Cost waste | Partly | `_v3_UI_ISSUES.md` Problem 2 (Thinking default); retry/menu drivers are new |
| 5a python_exec linecache | New | Real-use blocker |
| 5b `aws` not allowlisted | New | Real-use blocker |
| 5c Status-bar vs self-diagnosis | New | New axis |
| 6a-6g | New | Side-finds |

## Suggested patch sequence for the worker

Tier 1 — quick wins (combine with the UI-issues doc Tier 1):
1. **Reorder `_render_turn_meta` so thinking renders above metrics**
   (Problem 1, ~5 LOC in chat_ui.py).
2. **Verify `<details>` actually collapses in target Jupyter kernel**
   (Problem 1 second layer, render check only).
3. **Default Thinking OFF in `chat.ipynb` Cell 2** (Problem 4,
   1-line change).
4. **Add one-strike rule to system prompt**: do not retry blocked tools
   (Problem 4, ~3 lines in `prompt/sections.py`).
5. **Surface CONFIG flags in self-diagnostic guidance** (Problem 5c,
   ~5 lines in `prompt/sections.py`).

Tier 2 — sandbox correctness:
6. **Fix `python_exec` allowlist** to admit linecache + transitive
   stdlib closure (Problem 5a, requires careful review of allowed
   modules list).
7. **Decide `aws` CLI policy** — allowlist with per-arg validation OR
   document that boto3 (after 5a fix) is the canonical path (Problem 5b).

Tier 3 — intent-guard (biggest architectural ask):
8. **Add `original_intent_addressed` axis to the final-claim guard**
   (Problem 3, ~30 LOC in runtime/). Gate on `CONFIG.enable_intent_guard`
   so cost is opt-in.
9. **Promote frequently-used tools out of deferred** (Problem 6c, schema
   review in `tools/registry.py`).
10. **Suppress follow-up menu when user gave a complete instruction**
    (Problem 6f, system prompt nudge).

UI-collapse + parallel-grouping (Problem 2) should be done as part of
the larger live-stream router work in `_v3_UI_ISSUES.md` Tier 1 — same
function, same edit window.

## What NOT to change

- Engine layer (agent.py, runtime/, prompt/, core/, security/) except
  for the named additions above. The acceptance test passed; don't
  refactor.
- `chat.ipynb` cells except for the Thinking-default flip.
- Receipt-persistence in `tools/task.py` — that's a v5 win
  (documented in `PS_V5_VS_RUNNABLE_DEEP_REVIEW_20260511.md`).

## Open question for the user

The S3-access policy needs a call:
- **Option A**: allowlist `aws` CLI with per-arg validation (matches how
  `git` is handled today). Quick, but requires writing the per-arg rules.
- **Option B**: fix `python_exec` to admit boto3 cleanly. Slower, but
  unblocks the Python path more broadly (data science use cases too).
- **Option C**: keep both blocked, document that S3 work happens outside
  the agent. Honest, but kills a major SageMaker use case.

This is a config/policy decision, not a code question. Worker should
not pick one unilaterally.
