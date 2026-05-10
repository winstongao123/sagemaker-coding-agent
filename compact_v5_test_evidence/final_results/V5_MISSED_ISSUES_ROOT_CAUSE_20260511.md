# V5 Missed Issues Root-Cause Review

Date: 2026-05-11

Purpose: explain why the later v5 UI/source/coordination problems were not
caught by the earlier AWS/R-tier/PS-PS tests, and what gates should prevent the
same class from slipping again.

## Short Verdict

The AWS tests did catch real backend failures: invalid zips, stale final status,
Bedrock tool-result pairing, fatal/max-turn exits, subagent evidence, and
generated-project correctness.

They missed the later issues because those issues were mostly **operator
observability**, **source/package coherence**, and **architecture contract**
problems, not generated-project correctness problems.

In plain English: the test proved the robot could finish the homework, but it
did not fully prove that the dashboard showed each step live, that the filing
cabinet was organized afterward, or that every internal promise matched the
new architecture.

## What The Earlier Tests Actually Proved

| Test/evidence | What it proved | What it did not prove |
|---|---|---|
| AWS v1 Sonnet acceptance | Real Bedrock could build/test/review/fix a project; exposed bad zip and stale final status. | Clean unattended completion, notebook live rendering, source-tree hygiene. |
| PS/PS v2 protocol | Corrected the test instructions after v1: require real zip validation and final status. | It was a protocol update, not a single clean AWS pass. |
| PS/PS v3 Haiku run | 18/18 required files, 76 tests, valid result zip, `end_turn`, real cost/cache/subagent telemetry. | Live ipywidgets behavior during the run; CSS layout geometry; prompt truth drift; git/source-tree coherence. |
| Local final acceptance | Mock-mode UI strings existed: cache line, saved, agent attribution, todos, subagent lifecycle, `/verify`, `/done`. | Real notebook timing, live incremental DOM update during long Bedrock calls, rendered layout quality, and active-source-vs-zip-vs-git consistency. |
| R-tier matrix | Backend/runtime behaviors across budget, compaction, API boundary, recovery, long tasks, tool loops. | Human stuck feeling, visual card formatting, live subagent pane/streaming quality. |

## Missed-Issue Table

| Missed issue | Why it escaped earlier tests | Needed prevention gate |
|---|---|---|
| UI felt stuck while agent was running | AWS harness called `agent.run(..., output_fn=lambda s: out.append(str(s)))`, then judged final files/logs. It captured text, but did not assert that `WidgetChatUI._chat_display.value` changed before `agent.run()` returned. | A slow/mock agent test that starts a run, emits output chunks, and asserts the chat HTML updates within 1 second before final return. |
| Tool use not visible live | Backend logs had `[tool result]` / subagent text, and v3 only required final evidence. The UI router was not tested as a first-class live observer. | UI fixture test for tool-start and tool-result cards from both `output_fn` and `tool_gen_callback`. |
| Subagent visibility weak | v3 only checked that a subagent was used, costed, and saved artifacts. It did not require live child output to appear in the parent notebook while the child was running. | Parent/child callback smoke: child emits lifecycle/output/artifact envelope; parent UI must show start, child text, finish, cost/cache, artifact path. |
| Metrics all in one column | Tests checked strings like `Cache R/W`, `Saved`, `Agents`, and cost values. They did not inspect rendered layout or compare row/flex behavior against v4. | HTML fixture screenshot or DOM-style assertion for metric groups, row wrapping, and context/budget gauges. |
| Assistant response rendered like plain markdown/status text | Tests judged final answer text and files. They did not test bracket-leading assistant text such as `[SPEC vs SHIPPED]` against the UI router. | UI markdown routing test: bracket-heading assistant text remains assistant markdown unless it matches a known engine/status prefix. |
| Token usage looked high | Earlier tests recorded cost/cache numbers but did not decompose cost drivers: static prompt, dynamic prompt, visible schemas, deferred schemas, thinking budget, calls, output tokens. | Prompt-shape metrics on every turn plus test comparing Thinking ON/OFF and visible/deferred schema size. |
| Prompt/docs said stale subagent facts | Functional runs used the real task tool successfully, so stale text did not necessarily break the task. No grep lock checked for obsolete claims like "general only" or "parent cannot see output." | Prompt-truth drift test: grep forbidden stale phrases in `tools/task.py`, `subagent/agent_types.py`, and status docs. |
| `todo_write` allowed in read-only subagents | Tests verified subagents worked and produced evidence, but did not enforce that read-only/review agents cannot mutate durable parent task/todo state. | Read-only scope test: explore/plan/review/verify allowlists must exclude `todo_write`, write/edit tools, and mutating task-state tools. |
| UI used private `_engine.tool_gen_callback` mutation | It worked in the notebook and did not fail generated-project acceptance. No architecture test required UI to use only public `Agent` APIs. | Public API contract test: UI must call `Agent.run(..., tool_gen_callback=...)`; grep forbids `getattr(self.agent, "_engine")` in UI. |
| No structured request/task tracking | The generated project acceptance used `todo_write`/`AGENT_STATUS.md` and final artifacts, so lack of first-class `task_create/update/list` did not fail. Runnable comparison was deeper than the acceptance gate. | Architecture comparison gate for supervisor work: durable task IDs, owner/status/dependencies/evidence paths must exist for long-running requests. |
| Active source tree missing while zip was valid | Zip validation proved the package was internally valid. It did not assert that editable `compact_v5/` source existed and matched the zip, or that no temp extraction directory remained. | Source/zip parity gate: required source files exist under active tree, zip required files SHA-match source, no ` + $tmp + r`, no `.sageagent_state`, no tests/cache in zip. |
| Claude CLI review used wrong auth path | Earlier worker runs allowed a failed API-token route to count as "Claude unavailable." The reviewer-smoke itself was not a mandatory gate before block work. | Claude subscription-auth smoke before each review: `claude.cmd --print --setting-sources user --permission-mode dontAsk`, clear API-token/Bedrock env only for child process, require nonempty verdict. |
| Git not snapshotted | Runtime/zip tests do not imply source-control durability. The old flattened-tree transition left a noisy worktree that did not affect runtime but did affect reproducibility. | Release gate after final approval: commit scoped source/zip/evidence changes and push tracked branch; report unrelated dirty paths separately. |

## Root Causes

| Root cause | Explanation | Effect |
|---|---|---|
| Acceptance tested final state more than live process | The strongest AWS tests judged files, pytest, zip, stop reason, cost, and final logs. | Bugs in live notebook rendering and operator visibility survived. |
| UI tests were string-presence checks | Local acceptance checked that certain strings existed in HTML/output, not that the UI updated incrementally or laid out well. | Metrics layout and stuck feeling were not caught. |
| Human visual check was not converted into an automated gate | PS/PS v3 asked the user to visually confirm UI metrics before the long prompt. | If the visual check was skipped or not strict enough, no machine gate failed. |
| Backend success masked dashboard weakness | The agent could build a project correctly even when the UI did not show progress nicely. | A real AWS pass created confidence in runtime while UI still felt bad. |
| Zip validation was narrower than release validation | The zip was valid, but source tree placement, temp folders, and git staging were not part of the same gate. | Source/package drift survived until a later review. |
| Architecture contracts were implicit | Public callback API, read-only subagent boundaries, and task-state expectations were not encoded as tests. | Implementation could work but still be architecturally leaky. |
| Reviewer-gate auth was not hardened | Claude CLI review was required in principle, but the worker used the wrong auth path. | Some review steps looked blocked even though subscription CLI was available. |

## Why AWS Specifically Did Not Catch It

AWS/Bedrock only sees the model calls and tool-loop behavior. It does not see
ipywidgets layout, browser repaint timing, CSS row wrapping, or whether the
operator feels stuck in the notebook.

The v3 AWS summary proves this: the pass criteria were `acceptance_pass: true`,
`stop_reason: end_turn`, 18/18 required files, 76 tests, valid result zip, and
subagent cost/cache telemetry. Those are good gates, but none of them says:

- the chat widget updated before `agent.run()` returned;
- tool cards appeared live;
- metrics were arranged like v4;
- bracket-heading assistant markdown stayed formatted;
- active source tree matched the zip;
- git had the flattened tree committed.

So AWS did its job. The missing piece was a **notebook/release observability
gate** after the backend AWS pass.

## New Gates That Should Be Mandatory

| Gate | What it catches |
|---|---|
| `ui_live_supervisor_smoke` | live output, tool cards, subagent cards, markdown routing, stop wording, per-turn metrics. |
| HTML/screenshot fixture for metrics | one-column regressions, broken cards, unreadable footer layout. |
| Source/zip parity verifier | active tree missing, stale zip, runtime state leakage, forbidden members, wrong layout assumptions. |
| Prompt-truth grep lock | stale task/subagent docs that contradict runtime. |
| Public-API grep lock | UI reaching into `agent._engine` for progress. |
| Read-only subagent allowlist test | reviewers/explorers/planners mutating parent durable state. |
| Prompt-shape metrics test | high token usage without visibility into static/dynamic/schema/thinking drivers. |
| Claude subscription-auth smoke | false Claude unavailable from wrong API-token path. |
| Git snapshot gate | solved state not committed/pushed after final approval. |

## Final Answer

The misses were not because the AWS tests were useless. They were because the
AWS tests were aimed at backend completion and generated-project correctness,
while the user-visible failures were in the live supervisor surface and release
hygiene.

The correct fix is now in place: keep the AWS long-task test, but add a separate
UI/release-observability gate before saying solved.

