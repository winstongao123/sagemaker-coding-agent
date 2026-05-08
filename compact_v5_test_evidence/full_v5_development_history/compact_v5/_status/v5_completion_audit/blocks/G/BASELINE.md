# Block G Baseline

Date: 2026-05-05

Canonical source:

- `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:234-247`

Initial scope audit:

```text
py -3.11 compact_v5/_status/scripts/scope_audit.py --block G
```

Initial result:

- Expected rows: 8
- Ledger rows: 0
- Ship-blocking rows: G-1 through G-8
- Verdict: `LEDGER_INCOMPLETE`

Existing evidence before this audit pass:

- `compact_v5/MAIN/agent/subagent/agent_types.py` already covered G-3, G-4, G-6, and G-7.
- `compact_v5/MAIN/agent/subagent/spawn.py`, `worktree.py`, and task schema evidence already covered major Block G subagent dispatch/worktree behavior.
- `compact_v5/MAIN/agent/subagent/fork.py` and `tests/integration/test_block_g2.py` already covered G-8, which the canonical row says is the planned Block G2 fork cache-prefix slice.
- G-1/G-2 were historically deferred in PORT_LOG #090; this audit pass superseded that deferral with shipped local code and tests.

Pre-review smoke state:

- Not run yet for Block G.
