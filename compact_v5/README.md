# SageAgent v5 (compact_v5.zip)

> **STATUS — 2026-04-30: v5.0.0 build candidate, SHIP BLOCKED.**
>
> The 14-phase build closed all internal gates but failed user
> verification. v5 ships as a structurally-smaller subset of v4 — several
> v4 features were silently deferred (Compactor, TokenTracker, exec-call
> enforcement, save/load slash commands, full chat-display HTML rendering).
> Original V5_PLAN.md success metric #1 ("functional parity with v4.10.10")
> is **not met**.
>
> See `_status/V5_SHIP_CRITIQUE.md` for the full failure analysis and the
> v5.0.1 patch agenda (Block 1-6) that must land before v5 is shippable.
>
> Do not treat the `v5.0.0` git tag as a release. It is a checkpoint.

SageMaker-native re-implementation of Runnable Claude Code. Ships as a flat
zip that runs without `pip install`-ing a v5 package.

## Quick start

1. Extract `compact_v5.zip` into your SageMaker workspace.
2. Open `chat.ipynb` in Jupyter.
3. Run cells 1-3:
   - **Cell 1** — installs deps (boto3, ipywidgets, Pillow).
   - **Cell 2** — sets CONFIG (model, mock mode, thinking, skill auto-trigger).
   - **Cell 3** — launches the chat UI.
4. Send your first message via the Send button (or `ui.send("...")` in
   ConsoleChatUI fallback).

See `chat.md` for cell-by-cell explanation + troubleshooting.

## What's in the zip

```
compact_v5/                          (extracts here)
├── chat.ipynb                       # entry notebook
├── chat.md                          # companion docs
├── entry.py                         # cell-0 import target
├── __init__.py                      # Agent class
├── memory.md, AGENT_STATUS.md       # auto-loaded persistent files
├── core/                            # budget, errors, retry, query_engine, cache
├── tools/                           # 14 tools (read/write/edit/bash/python/grep/...)
├── skills/                          # 10 production skills (batch, clara, design, html,
│                                    #                       reflexion, report, review,
│                                    #                       security-review, simplify, verify)
├── runtime/                         # config, bedrock_client, audit, snapshot, ...
├── prompt/                          # 19 sectioned .md files (≤ 2500 tokens static)
├── ui/                              # chat UI + budget/thinking widgets
├── subagent/                        # forkSubagent + handoff + env
├── security/                        # SecurityManager + dangerous patterns
└── mcp/                             # MCP stdio/http clients
```

## What v5 brings vs v4

- **PS Issue #1 fix** (Hermes filter): skills with `requires_tools` are
  filtered out when those tools aren't currently active.
- **PS Issue #2 fix** (visible IterationBudget): `ipywidgets.IntProgress`
  bar shows budget consumption across parent + sub-agents.
- **PS Issue #4 fix** (visible thinking): Checkbox + IntSlider toggle
  thinking-mode + budget mid-session.
- **PS Issue #7 fix** (tool_classes promotion): tool capability matrix at
  prompt slot 2 (right after identity), not buried mid-list.
- **Phase 7 deferred-loading**: low-frequency tools loaded on demand via
  `tool_search` instead of per-turn schema overhead. Saves ~770 tokens/turn.
- **Phase 9 forkSubagent**: shared IterationBudget across parent +
  sub-agents prevents collective cost-ceiling overruns.
- **Static system prompt ≤ 2500 tokens** (vs v4 ~5000) — 19 sectioned .md
  files with hard per-section caps.
- **Tests**: 437 pass + 4 skip across 13 phases (00 → 12). Each phase
  Codex-reviewed; every flagged issue fixed in same commit with lock tests.

## Verify the zip is ship-ready

```bash
cd compact_v5/
python verify_ship_zip.py
# Expected: RESULT: PASS -- zip is ship-ready
```

## Re-build the zip (after source edits)

```bash
cd compact_v5/
python _rebuild_zip.py
```

## Constraints

- Bedrock-only (no Anthropic API).
- No GitHub network at runtime.
- `python_exec` is sandboxed via closure-based allowlist + AST analysis.
- Skill auto-trigger is OFF by default (v4.9.6 contract).
- Skill self-patching is OFF by default (`CONFIG.enable_skill_patching=False`).

## Versions

- v5.0.0 — initial ship (this release).
- See `MAIN/changelogs/CHANGELOG_v5_phase_NN.md` for per-phase narrative.
