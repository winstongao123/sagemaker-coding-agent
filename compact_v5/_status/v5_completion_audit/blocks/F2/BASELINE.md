# Block F2 Baseline

Canonical source: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:392-398`

Expected rows:

| row_id | capability | source | priority | fit | expected target |
|---|---|---|---|---|---|
| F2-1 | TokenBudget auto-continuation (R7 N4) | Runnable `query/tokenBudget.ts:1-93` and `query.ts:1308-1355` | HIGH | NEEDS-ADAPTATION | v5 should auto-continue when an explicit iteration budget is under 90 percent consumed and work is not showing diminishing returns. |

Existing evidence before this audit pass:

- `compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` row #072 records the earlier F2 implementation.
- `compact_v5/_status/V5_DESIGN_DECISIONS.md` ADR-028 records the adaptation from Runnable token-count budget to v5 iteration budget.
- `compact_v5/MAIN/agent/core/budget_continuation.py` implements the tracker and budget decision logic.
- `compact_v5/MAIN/agent/core/query_engine.py` wires F2 into the parent query loop.
- `compact_v5/MAIN/agent/runtime/config.py` keeps auto-continuation opt-in by default.
- `compact_v5/MAIN/agent/tests/integration/test_block_f2.py` contains pure-function, engine-wiring, cost-cap, subagent, diminishing-return, telemetry, exception, and tracker-reset lock tests.

Initial audit condition:

- `scope_audit.py --block F2` reported `LEDGER_INCOMPLETE` because the block artifact ledger did not exist.
- No new command surface is needed for F2. The long software-project workflow uses existing `/status`, `/phase`, `/save`, `/resume`, `/checkpoint`, `/verify`, `/done`, `/cost`, `/context`, and `/dream` commands.
