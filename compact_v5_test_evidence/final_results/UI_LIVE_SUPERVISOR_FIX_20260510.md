# UI Live Supervisor Fix 20260510

Date completed: 2026-05-11
Active ship tree: `compact_v5/compact_v5/`

## Summary

This v5.0.2 UI observability pass fixes the SageMaker notebook "looks stuck"
problem without rewriting the v5 engine. The core Bedrock request shape,
thinking signature replay, tool dispatch semantics, compaction, security,
final-claim guard, subagent receipt persistence, and cost/cache accounting
remain owned by the existing runtime.

## Shipped Blocks

| Block | Shipped |
|---|---|
| UI-LIVE-STREAM | `output_fn` now renders messages/status during `agent.run()` instead of buffering until return. |
| UI-BRACKET-ASSISTANT | Assistant markdown/final answers that begin with bracket headings, such as `[SPEC vs SHIPPED]`, stay assistant messages unless they match a known engine/status prefix. |
| UI-TOOL-CARDS | Tool call/result events render as bounded cards. The existing `QueryEngine.tool_gen_callback` is wired to the UI and now receives result events for display. |
| UI-SUBAGENT-VIS | Subagent start, child output, finish, selected result, stop reason, cost/cache, and artifact paths are visible in the main supervisor chat. Parsed `task` envelopes are not duplicated as raw tool cards. |
| UI-METRICS-LAYOUT | Footer metrics use wrapping rows plus paired Context/Budget gauges instead of one tall column. |
| UI-STOP-STATUS | Stop wording now explains cooperative behavior: stop requested, finishing current Bedrock/tool/subagent call. |
| UI-COST-MEASURE | A display-only cost-driver line measures likely cost causes before any optimization. No model/prompt/cache/compaction defaults changed. |

## Review Status

Claude CLI review prompts and outputs were saved for every block in
`compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/`.

Actual Claude CLI output for each block:

```text
Credit balance is too low
```

This prevented an `APPROVE` / `REQUEST_CHANGES` verdict. The finding is
infrastructure-only and nonblocking for code continuation because no review
finding was produced to address. Each block still has a saved diff, prompt,
review output, and local drift check.

Final Codex follow-up used the documented subscription-auth Claude CLI path
from `AGENTS.md` / `CLAUDE_REVIEWER_AUTH.md`: clear `ANTHROPIC_API_KEY` and
`CLAUDE_CODE_USE_BEDROCK` for the child process, call
`C:\Users\winst\AppData\Roaming\npm\claude.cmd`, use `--setting-sources user`
and `--permission-mode dontAsk`. The first usable Claude review found one real
blocker: `compact_v5.zip` was stale even though the source tree was fixed.
The zip was rebuilt from `compact_v5/compact_v5/` and hash-verified against
the active tree before final status. The post-zip Claude re-review saved at
`compact_v5_test_evidence/final_results/ui_live_supervisor_reviews/UI-LIVE-SUPERVISOR-FINAL-20260511-post-zip_claude_review.md`
returned `SHIP DECISION: APPROVE` with no findings.

## Verification

Zero-cost local smoke checks passed:

- live output router renders during run
- bracket-leading assistant markdown stays assistant, not system
- known bracketed engine/status lines still route to system
- tool card HTML exists
- markdown table/list/code block renders
- subagent start/finish/artifact path is visible without duplicating raw task
  envelopes
- per-turn metrics include Cache R/W, Without cache, Saved, Calls
- Stop requested wording is visible
- live `_run_message` renders output before `agent.run()` returns
- Stop status updates while a slow run is still in flight

Fresh visual evidence:

- `compact_v5_test_evidence/final_results/UI_LIVE_SUPERVISOR_FINAL_VISUAL_20260511.html`
- `compact_v5_test_evidence/final_results/UI_LIVE_SUPERVISOR_FINAL_VISUAL_20260511.png`

Real AWS was not run.
