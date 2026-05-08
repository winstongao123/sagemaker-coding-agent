# Block G3 Baseline

Canonical source: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:249-258`

Expected rows:

- G3-1: Coordinator 258-LOC system prompt.
- G3-2: `getCoordinatorUserContext` worker-tools plus scratchpad context.

Existing implementation evidence:

- `compact_v5/MAIN/agent/coordinator/system_prompt.py`
- `compact_v5/MAIN/agent/coordinator/user_context.py`
- `compact_v5/MAIN/agent/coordinator/__init__.py`
- `compact_v5/MAIN/agent/core/query_engine.py`
- `compact_v5/MAIN/agent/runtime/config.py`
- `compact_v5/MAIN/agent/tests/integration/test_block_g3.py`
- PORT_LOG #092 and #093
- ADR-032

No AWS/R-tier execution is approved or required for this block. The real Haiku
orchestration test in `test_block_g3.py` remains skipped unless
`RUN_REAL_BEDROCK` is explicitly approved.
