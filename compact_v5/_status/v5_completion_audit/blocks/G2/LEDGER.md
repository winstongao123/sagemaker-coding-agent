# Block G2 Ledger

Canonical source: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:419` plus detailed capability assignment at `SYNTHESIS_MASTER.md:245`.

| row_id | capability | source | priority | fit | expected_target | code_evidence | test_evidence | port_log | adr | historical_review | git_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G2 | `forkSubagent` cache-prefix replay helper | SYNTHESIS_MASTER.md:245,419; Runnable tools/AgentTool/forkSubagent.ts:73-end | HIGH | already in plan / ADAPT | Preserve byte-identical fork-child cache prefix through helper module and deterministic tests; real Bedrock cache-hit verification remains R-tier gated. | `subagent/fork.py:41`; `subagent/fork.py:51`; `subagent/fork.py:80`; `subagent/fork.py:126`; `subagent/fork.py:206`; `subagent/fork.py:220`; `subagent/__init__.py:36` | `tests/integration/test_block_g2.py:67`; `tests/integration/test_block_g2.py:142`; `tests/integration/test_block_g2.py:166`; `tests/integration/test_block_g2.py:283`; `logs/block-g2-tests.log` | #094 | ADR-033 | `reviews/block-g2-claude-review-iter1.md` APPROVE | f59376040c7c3f3238d6a3a9a0a8ca8c37575188 | SHIPPED | None; closed and pushed. | APPROVE |
