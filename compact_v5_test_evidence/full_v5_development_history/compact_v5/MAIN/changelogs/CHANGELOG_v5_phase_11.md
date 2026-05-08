# V5 Phase 11 Changelog — Notebook UX + entry + thinking/budget UI (PS Issue #4)

Date: 2026-04-30
Tag (target): v5-phase-11
ADR: ADR-017
PORT_LOG rows: #030, #031, #032, #033, #034

## Goal (V5_PLAN.md §Phase 11)

Port v4's chat.ipynb + chat_ui to v5; ship the IterationBudget UI (PS Issue #2 finish) + thinking-budget UI (PS Issue #4 fix). Acceptance: notebook executes hello-world turn against mock Bedrock.

## What landed

### Agent class — `agent/__init__.py` (PORT_LOG #031)
Thin public wrapper around Phase 8-10 modules. Composes BedrockClient +
IterationBudget + QueryEngine + optional SkillManager. Methods: run /
stop / clear / set_thinking. Lives in `agent/__init__.py` because the
package directory is named `agent`.

### entry.py — cell-0 import target (Phase 11)
Re-exports `Agent`, `create_chat_ui`, `CONFIG`, `BEDROCK_MODELS`,
`SkillManager`, `IterationBudget`. The notebook's first import line:
`from entry import Agent, create_chat_ui, CONFIG, BEDROCK_MODELS`.

### ui/chat_ui.py (PORT_LOG #030)
ADAPT port of v4's `create_chat_ui` (~2000 LOC → ~150 LOC). MVP: Send /
Stop / Clear buttons + budget bar + thinking widget + output area.
Falls back to `ConsoleChatUI` when ipywidgets is unavailable so CI +
SageMaker base images still exercise the factory.

### ui/widgets.py (PORT_LOG #033 + #034)
- **IterationBudgetWidget** (PS Issue #2): wraps `core.budget.IterationBudget`
  in `ipywidgets.IntProgress` with color cue (info → warning → danger
  at 70% / 90% consumption). HTML fallback when ipywidgets unavailable.
- **ThinkingBudgetWidget** (PS Issue #4): Checkbox + IntSlider routing
  changes into `Agent.set_thinking(...)`. HTML fallback.

### chat.ipynb + chat.md (PORT_LOG #032)
4-cell minimal notebook: install / configure / launch / quick-reference.
Companion `chat.md` documents cells + troubleshooting + OUT-OF-SCOPE list.

### Tests (20 new)
- `tests/integration/test_notebook_smoke.py` — 20 tests including the
  Phase 11 acceptance gate (`test_hello_world_turn_via_console_ui`),
  Agent surface, factory paths, both PS Issue widgets, chat.ipynb +
  chat.md presence/structure, and 5 Codex-fix lock tests.

## Test results

- Last full `pytest` run (post Codex fixes): 2026-04-30 — **412 passed +
  4 skipped** (was 392+4 in Phase 10; +20 net new tests).
- Aggregate audit: all 7 metrics PASS.

## Codex review

- First pass: APPROVE_WITH_FIXES. 5 findings (1 HIGH + 3 MEDIUM + 1 LOW).
  - **HIGH**: lazy `create_chat_ui` ignored CONFIG.max_turns + max_iteration_budget.
  - **MEDIUM**: ConsoleChatUI.render() returned raw HTML string.
  - **MEDIUM**: IterationBudgetWidget test didn't exercise sub-agent consumption.
  - **MEDIUM**: factory branch selection (ipywidgets / fallback) not exercised.
  - **LOW**: chat.ipynb assertions too loose.
- All 5 fixed in same commit; 5 new lock tests added.
- Post-fix: AXIS A PASS, AXIS B 5 ADAPTED / 0 DRIFTED.
- Saved at: `_status/codex_reviews/phase-11.md`.

## PS Issues resolved

- **PS Issue #2 (visible IterationBudget)**: Phase 8 shipped the data model;
  Phase 11 ships the visible UI (progress bar with color cue across parent +
  sub-agents). RESOLVED end-to-end.
- **PS Issue #4 (visible thinking budget)**: Phase 1 sent the thinking config;
  Phase 11 makes it visible (Checkbox + IntSlider). RESOLVED.

## Better than v4

- v4's create_chat_ui is ~2000 LOC of HTML rendering buried in the monolith;
  v5's is ~150 LOC of widget composition, testable in isolation.
- v4 has no in-UI surface for the IterationBudget — v4 only logs `[Budget
  exhausted...]` once the wall is hit. v5 shows a live progress bar.
- v4 has thinking-mode but no UI for the budget. v5 shows current budget +
  toggle, with observers routing live changes back to the agent.
- ConsoleChatUI fallback means tests + headless environments still exercise
  the factory. v4's UI requires Jupyter to even import.

## Next phase

Phase 12 — Parity tests vs v4. Run fixed scenarios against v4 and v5;
critical scenario suite 100%, non-critical ≥90%, differences logged.
