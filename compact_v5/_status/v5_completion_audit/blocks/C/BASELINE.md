# Block C Baseline

Date: 2026-05-04

## Baseline Scope

- Canonical source: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:89-113`.
- Expected rows: 19 (`C-1` through `C-19`).

## Baseline Commands

1. `python compact_v5/_status/scripts/scope_audit.py --block C`
   - Before ledger creation: 19 expected rows, 0 ledger rows, 19 ledger-missing blockers, `LEDGER_INCOMPLETE`.
   - Log: `compact_v5/_status/v5_completion_audit/logs/block-c-baseline-scope-audit.log`.

2. `python compact_v5/_status/scripts/scope_audit.py --block C`
   - After ledger initialization: 19 expected rows, 19 ledger rows, 19 missing/ship-blocking rows, `NEEDS_IMPLEMENTATION`.
   - Log: `compact_v5/_status/v5_completion_audit/logs/block-c-scope-audit-after-ledger-init.log`.

3. `python -m pytest tests/integration/test_block_c.py -q`
   - Baseline existing Block C suite before redo additions: 21 passed.
   - Log: `compact_v5/_status/v5_completion_audit/logs/block-c-pytest-existing.log`.

No AWS/R-tier tests were run or approved.
