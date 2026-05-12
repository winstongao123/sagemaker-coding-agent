# SageAgent v5 Notebook User Guide

This is the companion guide for `chat.ipynb`, the production SageMaker UI for SageAgent v5.

v5 keeps the v4-style notebook experience, but the engine underneath is the final v5 runtime: Bedrock Claude models, durable status and memory, subagents, checkpoints, compaction, result replay, telemetry, and review/verification gates for long-running software work.

## What To Run

Run the notebook cells in order:

1. Install dependencies.
2. Run the configuration cell. It displays the v4-style ipywidgets controls
   and refreshes the launcher/UI modules so a reused kernel does not run stale
   code from a previous zip.
3. Launch the v4-style chat UI.
4. Send messages from the chat box, or from a new cell with
   `ui.send("your message")`.
5. Read the quick reference section when you need commands or skills.

The usual production file to open is:

```text
chat.ipynb
```

The v4-compatible import path is still available:

```python
from sagemaker_agent import CONFIG, BEDROCK_MODELS, create_chat_ui
```

## Important Runtime Files

| File or folder | Why it matters |
|---|---|
| `chat.ipynb` | Main SageMaker UI. |
| `entry.py` | Notebook import helper. |
| `sagemaker_agent.py` | v4-compatible shim. |
| `agent.py` | Public `Agent` wrapper. |
| `commands.py` | Slash command dispatcher. |
| `AGENT_STATUS.md` | Durable project/task status loaded into context. |
| `memory.md` | Durable memory loaded into context and updated by memory flows. |
| `core/` | Query engine, compaction, cache, budget, retry, formatting. |
| `runtime/` | Bedrock client, config, session, tokens, telemetry, snapshots, gates. |
| `tools/` | Read, write, edit, shell, notebook, task, result replay, skills. |
| `skills/` | Production skill instructions. |
| `skills/html/references/` | Production HTML templates used by the `html` skill. |
| `docs/htmls/V5_DESIGN_OVERVIEW.html` | User-facing v5 architecture overview included in the company zip. |
| `subagent/` | Subagent spawning, handoff, envelopes, and context. |
| `ui/` | Notebook widgets and display components. |
| `security/` | Tool safety and prompt-injection protections. |

## Commands

Use slash commands in the chat box.

| Command | What it does |
|---|---|
| `/status` | Show current `AGENT_STATUS.md`; `/status init` creates it. |
| `/save [title]` | Save current session messages and cost snapshot. |
| `/resume <id>` | Resume a saved session. |
| `/checkpoint create <name>` | Create a file checkpoint. |
| `/checkpoint list` | List checkpoints. |
| `/checkpoint restore <name-or-file> [--yes]` | Preview or restore checkpoint content. |
| `/cost` | Show token, cache, model, parent/subagent, and cost summary. |
| `/context` | Show context-pressure diagnostics. |
| `/verify [full|quick|pre-commit]` | Run verification gates. |
| `/done [full|quick]` | Run the close gate before trusting completion. |
| `/dream` | Consolidate `memory.md`. |
| `/skills` | List available skills. |
| `/skill use <name>` | Activate a skill. |
| `/skill clear` | Clear active skills. |
| `/skill suggestions` | Ask for possible skill matches. |
| `/skill apply` | Apply a proposed skill patch when one exists. |
| `/skill reject` | Reject a proposed skill patch. |
| `/unskill` | Alias for clearing skills. |
| `/skillify` | Convert repeated process knowledge into a skill candidate. |
| `/promote-to-skill` | Promote useful knowledge into a skill flow. |
| `/simplify` | Run simplification/review support. |
| `/init` | Initialize workspace status/skill structure. |
| `/init-verifiers` | Initialize verifier support. |
| `/phase` | Phase/workflow helper. |
| `/diffs` | Show changed-file context. |
| `/regression` | Regression-test helper. |
| `/revert` | Revert helper with safety checks. |
| `/auth` | Authentication/status helper. |
| `/quit` or `/q` | Quit/stop chat loop. |

## Notebook Controls

| Control | What it does |
|---|---|
| Model dropdown | Changes `CONFIG.model_id` and the live Bedrock client model. |
| Plan Mode | Turns on the read-only planning gate in the v5 query engine. |
| Require Approval | Toggles approval prompts for mutating/high-risk tools. |
| Bedrock-only | When on, v5 blocks S3/Textract/Lambda/general AWS CLI and only allows Bedrock Runtime. Turn it off only when you intentionally want approved read-only S3/Textract access. S3 delete/admin stays blocked either way. |
| Extended Thinking / Think Budget | Changes the thinking config sent to Bedrock models that support it. |
| Budget $ | Updates the local session cost limit shown in the UI. |
| Auto-Compact | Enables or disables automatic compaction and cold-cache microcompact for future turns. |
| Compact | Manually compacts current conversation context with the v5 compactor. |
| Clean | Removes local non-session traces such as audit logs, snapshots, indexes, and temp output; saved sessions are kept. |
| Sub-Agent Models | Opens five v4-style child model dropdowns: `explore`, `review`, `general`, `build`, and `plan`. Each can use `Same as main` or any `BEDROCK_MODELS` entry. The choice writes to `CONFIG.agent_overrides`; it does not push prompt text into the model. |

## Skills

Production skills included in the company zip:

| Skill | Use it for |
|---|---|
| `batch` | Batch-style work. |
| `clara` | Structured codebase review methodology. |
| `debug` | Debugging workflows. |
| `design` | Design reasoning. |
| `html` | HTML/design/architecture deliverables. |
| `init` | Workspace initialization. |
| `init-verifiers` | Verifier setup. |
| `reflexion` | Self-review and reflection. |
| `remember` | Durable memory behavior. |
| `report` | Report writing. |
| `review` | Code/design review. |
| `security-review` | Security review. |
| `simplify` | Simplification passes. |
| `skillify` | Turning repeated workflows into skills. |
| `verify` | Verification gates. |

Use:

```text
/skills
/skill use verify
/skill clear
```

## Long-Running Software Work

For serious software tasks, use this rhythm:

1. State the goal clearly.
2. Let v5 maintain `AGENT_STATUS.md`, todos, and `memory.md`.
3. Use `/save` before long pauses.
4. Use `/checkpoint create <name>` before risky edits.
5. Use `/cost` and `/context` during long runs.
6. Use `/verify` before claiming a task is done.
7. Use `/done` before trusting final completion.
8. Use `/resume <id>` after restart or interruption.

This is the same anti-drift principle used to build v5 itself: long work must leave status, tests, logs, review evidence, and checkpoints.

## Cost And Safety

- The notebook default is real Bedrock mode (`CONFIG.mock_mode = False`), matching v4 production use.
- Tick Mock Mode only for a no-AWS smoke test.
- Bedrock-only is the safest mode: it allows `bedrock-runtime` and blocks
  S3/Lambda/Textract/etc. The main chat UI now shows this mode in the footer
  and exposes a live `Bedrock-only` checkbox.
- If you need S3 inventory, untick Bedrock-only before asking. v5 uses the
  dedicated read-only `aws_s3_list` tool for bucket/prefix/object listings and
  still blocks S3 destructive/admin behavior. General Python `boto3` may be
  constrained by the Python sandbox or local package availability; do not use
  it as the primary S3 inventory path.
- For simple AWS inventory questions, keep Extended Thinking off unless you
  specifically want deeper reasoning. Thinking tokens are visible in the
  footer, but they still count toward context/cost.
- The notebook default region is `ap-southeast-2` (Sydney), matching v4.
- The notebook default model is the first `BEDROCK_MODELS` entry: `Claude 4.5 Sonnet (AU) - default`.
- The model dropdown includes the v4-style choices: Sonnet 4.5 AU, Haiku 4.5 AU, Sonnet 4.6 AU, Opus 4.6 AU, Opus 4.5 Global, and Claude 3 fallback models.
- `/cost` shows session usage.
- `/context` shows context pressure.
- v5 tracks token/cache/model usage and local cost. AWS Budget checks are still external account-level guardrails.
- If a tool, model call, or verification gate fails, v5 should fix or stop instead of silently claiming success.

## Troubleshooting

| Problem | What to do |
|---|---|
| `ModuleNotFoundError: No module named 'entry'` | Use the rebuilt zip and re-run Cell 2. The thin notebook bootstrap locates the runtime from the shipped zip root, `compact_v5/`, or a repo root that contains `compact_v5/`. |
| `ModuleNotFoundError: No module named 'runtime'` | This usually means an old or partial zip was extracted. Re-extract the latest `compact_v5_ship.zip`; it must contain `runtime/__init__.py`, `core/__init__.py`, `tools/`, `subagent/`, and `ui/` beside `entry.py`. |
| Widgets do not render | Run the install cell, restart the kernel, clear old outputs, and rerun Cells 1-3 from the latest zip. Cell 2 intentionally drops cached `entry` and UI modules before importing so a reused kernel picks up the files on disk. |
| `Error displaying widget: model not found` or repeated `Loading widget...` | This means the SageMaker/Jupyter browser widget manager could not attach to a Python widget model. First restart the kernel and rerun Cells 1-3 from `compact_v5_ship.zip`. Then run `import ipywidgets as widgets; display(widgets.IntSlider(description="Widget test"))`. If the simple slider also fails, the target widget stack is broken or mismatched independent of v5. If the slider works but v5 fails, capture the screenshot and versions for a v5 UI fix. Avoid upgrading/downgrading `ipywidgets`, `jupyterlab_widgets`, or `widgetsnbextension` inside the notebook unless the SageMaker image specifically requires it. For emergency headless use only, call `launch_config_ui(use_widgets=False)` and `launch_chat_ui(config_ui, use_widgets=False)`, then send with `ui.send("your message")`. |
| Console fallback blocks a mutating tool | The fallback is only for headless/debug use. Use the v4-style widget UI for normal validation because it provides the intended approval and live-supervisor controls. |
| Bedrock access denied | Check IAM and region; use mock mode for local smoke. |
| Budget exhausted | Use `/cost`; raise configured budget only if you intend to spend. |
| Context feels too large | Use `/context`; compaction and result replay should help. |
| Long task got interrupted | Use `/resume <id>`, read `AGENT_STATUS.md`, and continue from saved status. |
| Need rollback | Use `/checkpoint list` and `/checkpoint restore ...` with preview first. |

## Production Evidence

The production zip intentionally excludes `_status`, tests, audit logs, and review artifacts. Those live in the repository, not the company runtime zip. It does include the production `html` skill templates and `docs/htmls/V5_DESIGN_OVERVIEW.html`.

Final evidence summary:

- Final Claude production-readiness review: `APPROVE_PRODUCTION_READY`.
- R-tier matrix: 42 rows, with 28 `READY` and 14 `DISPOSITION_OK`.
- Final R-tier gate: passed.
- Local recorded R-tier Bedrock spend: `$1.6757`.
- Final test review: `compact_v5/_status/PS_TEST_REVIEW_FINAL.md`.
- Current production-test readiness: 98% confidence for target SageMaker
  production testing, with the remaining risk explicitly limited to target
  environment widget/IAM/package variance.
- Current focused smoke suite: `31 passed`.
- Latest independent Claude CLI notebook/v4 comparison review: `APPROVE`, no
  HIGH/MEDIUM findings.
- Latest local visual evidence: Cell 2 rendered real ipywidgets controls,
  Cell 3 rendered the dark v4-style chat UI, and browser text contained
  `HAS_WIDGET_ERROR False`.

## What Is Not In The Runtime Zip

The company ship zip is intentionally small. It does not include:

- tests;
- `_status` audit evidence;
- historical scan reports;
- review logs;
- local sessions;
- audit logs;
- bulky optional skill reference examples.

Those files stay in the repository for traceability. The zip contains only the runtime package and the user-facing notebook guide.

## Live Supervisor UI

The notebook chat is now a live supervisor surface:

- Agent output appears during `agent.run()` as soon as the runtime emits it.
- Tool calls and results render as separate bounded cards instead of being
  merged into the final assistant answer.
- Markdown tables, lists, and code blocks render in assistant messages.
- Assistant messages that begin with bracketed headings, such as
  `[SPEC vs SHIPPED]`, remain assistant messages. Only known engine/status
  bracket prefixes are routed to system cards.
- Subagents show start, child updates, finish, selected child output, stop
  reason, token/cache/cost summary, and saved artifact paths. Parsed task
  envelopes are summarized as subagent cards instead of also showing raw JSON
  as a duplicate tool result.
- Footer metrics use wrapping rows and paired Context/Budget gauges. Each
  assistant turn still shows turn-level `Cache R/W`, `Without cache`, `Saved`,
  and `Calls` metadata when available.
- Stop is cooperative: clicking Stop requests a halt, then v5 finishes the
  current Bedrock, tool, or subagent call and stops at the next checkpoint.
- The footer includes display-only cost-driver measurement. Use it to compare
  output tokens, calls, Thinking ON/OFF, cache hit rate, and subagent
  attribution before changing model, prompt, cache, or compaction settings.

## S3 Read-Only Inventory

For S3 bucket/file structure questions, use read-only inventory behavior:

- Keep `Bedrock-only` off when you intentionally want S3 reads. When it is on,
  S3 is blocked and only Bedrock Runtime is allowed.
- v5 uses the dedicated `aws_s3_list` tool for S3 bucket/prefix inventory.
  Do not use `aws s3` or `aws s3api` through bash; those CLI paths are blocked
  by the bash allowlist and the UI/agent will direct the turn back to
  `aws_s3_list`.
- `aws_s3_list` is always visible, so simple S3 inventory should not spend an
  extra turn on `tool_search`.
- If Extended Thinking is on and the request is a simple read-only S3
  inventory, v5 disables thinking for that turn only and displays a
  `[cost control]` notice. Your persistent Thinking toggle is not changed.
- Tool calls/results render as one collapsed card per `tool_use_id`. Expand the
  card only when you need the full input/result body.
- If S3 cannot be listed, the answer should name the actual blocker: Bedrock-only
  mode, bash allowlist, Python sandbox import allowlist, approval, credentials,
  or AWS permissions.
