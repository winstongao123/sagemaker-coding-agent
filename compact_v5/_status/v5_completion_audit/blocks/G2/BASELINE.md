# Block G2 Baseline

Canonical source: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md`

Mechanical audit note: `scope_audit.py --block G2` currently parses one G2 row
from the synthesis summary table, while the detailed capability text is the
Block G row G-8: `forkSubagent` cache-prefix replay, already assigned to Block
G2 in the plan. The G ledger records G-8 as reviewed in Block G; this G2 close
flow records the separately planned implementation artifacts for the cache-prefix
helper module.

Existing implementation evidence:

- `compact_v5/MAIN/agent/subagent/fork.py`
- `compact_v5/MAIN/agent/subagent/__init__.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_g2.py`
- PORT_LOG #094
- ADR-033

No AWS/R-tier execution is approved or required for this block. The real Bedrock
cache-hit exercise remains behind R-tier R3 per ADR-033.
