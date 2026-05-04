# Block E+F Changelog

Date: 2026-05-04

- Added `core/formatting.py` with file size, duration, token, and cost helpers.
- Added `CONFIG.max_budget_usd` plus `maxBudgetUsd` config-file compatibility.
- Added QueryEngine status/warning callback support, denial counting, hard
  budget halt, fallback retry signature stripping, and tool-generation callback.
- Expanded `tests/integration/test_block_e_f.py` from old env-block remap tests
  to include canonical EF row locks.
- Added PORT_LOG #112 and ADR-044 for the Block E+F completion-audit redo.
- Addressed Claude iter1 LOW findings by stripping additional signature-key
  variants during fallback replay and emitting tool-generation events for every
  visible tool call before dispatch.

No AWS/R-tier tests, git tag, force push, Codex review, or nested `codex exec`
were run.
