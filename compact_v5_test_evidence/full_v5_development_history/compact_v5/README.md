# SageAgent v5.0.1 (compact_v5.zip)

> **STATUS - 2026-05-06: production-ready candidate after the v5.0.1 completion audit.**
>
> v5.0.1 completed the block-by-block scope audit, independent Claude review loop,
> optimized R-tier AWS tests, final production-readiness review, and final ship-zip
> gate. Remaining items are documented nonblocking follow-ups, not hidden ship blockers.

SageMaker-native re-implementation of Runnable Claude Code. Ships as a flat zip
that runs without `pip install`-ing a v5 package.

## Quick Start

1. Extract `compact_v5.zip` into your SageMaker workspace.
2. Open `chat.ipynb` in Jupyter.
3. Run cells 1-3:
   - **Cell 1** installs runtime deps: Bedrock, widgets, image/docs/spreadsheet/chart/search helpers.
   - **Cell 2** sets CONFIG: model, region, workspace, mock mode, thinking, Bedrock-only, budgets.
   - **Cell 3** launches the v4-style dark notebook UI.
4. Send your first message via the Send button. In console fallback or programmatic notebook use, call `ui.send("...")`.

See `chat.md` for cell-by-cell explanation and troubleshooting.

## What Is In The Zip

```text
compact_v5/                         (extracts here)
|-- chat.ipynb                      # entry notebook
|-- chat.md                         # companion user guide
|-- entry.py                        # cell import target
|-- agent.py, commands.py           # Agent wrapper + slash commands
|-- sagemaker_agent.py              # v4-compatible import shim
|-- memory.md, AGENT_STATUS.md      # auto-loaded persistent files
|-- core/                           # budget, query engine, compactor, retry, cache
|-- tools/                          # production tools: read/write/edit/bash/python/grep/task/etc.
|-- skills/                         # 15 production skills
|-- runtime/                        # config, Bedrock client, audit, session, state, telemetry
|-- prompt/                         # sectioned system prompt files
|-- ui/                             # v4-style notebook UI + widgets
|-- subagent/                       # sub-agent spawn, handoff, worktree, memory
|-- coordinator/                    # software-work coordination helpers
|-- memory/                         # durable memory helpers
`-- security/                       # approval/security policy and dangerous patterns
```

## What v5 Brings Vs v4

- Visible shared IterationBudget across parent + sub-agents.
- v4-style model dropdowns and v4-style sub-agent model overrides via `CONFIG.agent_overrides`.
- Durable memory/status/checkpoint/resume workflow for long-running software work.
- Stronger `/verify` and `/done` gates that require fresh status, tests, review, results, telemetry, and sub-agent evidence.
- Tool-use quality controls: grep-first search, loop/repeated-call guards, command budgets, and R-tier process-quality evidence.
- Bedrock prompt/cache/token/cost telemetry, including per-agent cost buckets.
- Production skills for coding, review, debugging, reporting, memory, design/html, and verification.
- Optimized R-tier AWS evidence recorded in `_status/PS_TEST_REVIEW_FINAL.md` and `_status/v5_completion_audit/FINAL_POST_AWS_PRODUCTION_READY.md`.

## Deliberately Not Shipped In v5.0.1

These are documented future/polish items, not hidden claims:

- Durable async/background sub-agent task handles like Runnable.
- Live sub-agent activity pane with queued messages to running children.
- Worktree preservation UX for changed build sub-agent worktrees.
- Deeper Runnable-style context/cache-break drilldowns.
- Anthropic API-only `output_config.task_budget`; v5 uses Bedrock/local budget gates instead.

## Verify The Zip

```bash
cd compact_v5/
python verify_ship_zip.py
# Expected: RESULT: PASS -- zip is ship-ready
```

## Rebuild The Zip

```bash
cd compact_v5/
python _rebuild_zip.py
```

## Runtime Constraints

- Bedrock-only runtime path; no Anthropic API dependency.
- Default Bedrock-only mode blocks all AWS services except `bedrock-runtime`.
- If Bedrock-only is unticked for a task that needs S3, Python `boto3`
  S3 read calls such as `list_objects_v2`, `get_object`, and `head_object`
  are allowed through the approval gate, but S3 deletes remain blocked by
  regex guardrails: `delete_object`, `delete_objects`, and `delete_bucket`.
- No GitHub network at runtime.
- Python execution is sandboxed via allowlist and AST checks.
- Skill auto-trigger is OFF by default.
- Skill self-patching is OFF by default.
- The production zip excludes tests, `_status`, sessions, audit logs, caches, and `.sageagent_state`.

## Versions

- v5.0.1 - completion-audited production candidate.
- v5.0.0 - historical failed checkpoint; superseded.
