# Block D Baseline

Date: 2026-05-05

Pre-change repository baseline:

- `git rev-parse HEAD`: `43aa6c1be7e79019e8bcf93fbb5845a4b1d3bb6f`
- Recent `v5.0.1-block-*` tags: `v5.0.1-block-k`, `v5.0.1-block-j`,
  `v5.0.1-block-t`, `v5.0.1-block-n`, `v5.0.1-block-l`,
  `v5.0.1-block-h-plus`, `v5.0.1-block-h`, `v5.0.1-block-g2`,
  `v5.0.1-block-g3`, `v5.0.1-block-g`.
- `scope_audit.py --block D` before ledger creation: 13 expected rows, 0
  ledger rows, ship-blocking rows D-1 through D-13.

Dirty worktree at D start included pre-existing unrelated modified files such
as `AGENTS.md`, `compact_v5.zip`, `compact_v5/MAIN/agent/memory.md`, several
R-tier/status docs, and `blocks/A/STATUS.md`. These were not part of the D
implementation scope and must not be staged for the D checkpoint.

Zero-cost baseline tests were not meaningful before D implementation because
the block artifact folder did not exist and the D ledger was empty.
