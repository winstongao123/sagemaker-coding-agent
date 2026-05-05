# Block G Ledger

Canonical source: `compact_v5/_phase_2/wave_5_deep/SYNTHESIS_MASTER.md:234-247`

| row_id | capability | source | priority | fit | expected_target | code_evidence | test_evidence | port_log | adr | historical_review | git_evidence | disposition | action_needed | reviewer_verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G-1 | `loadAgentMemoryPrompt` per-agent-scoped memory | SYNTHESIS_MASTER.md:238; Runnable AgentTool/agentMemory.ts:138-177 | MED | CLEAN | Load scoped `MEMORY.md` into enabled subagent prompts. | `subagent/agent_memory.py:107`; `subagent/agent_types.py:158`; `subagent/spawn.py:333` | `tests/integration/test_block_g.py:705`; `tests/integration/test_block_g.py:755` | #195 | ADR-031 | `reviews/block-g-claude-review-iter1.md` APPROVE | pending close commit | SHIPPED | Close specific-file git checkpoint and update evidence SHA. | APPROVE |
| G-2 | `isAgentMemoryPath` path-traversal-safe | SYNTHESIS_MASTER.md:239; Runnable agentMemory.ts:68-104 | MED | CLEAN | Normalize and bound agent-memory path checks to allowed roots. | `subagent/agent_memory.py:83`; `subagent/agent_memory.py:29` | `tests/integration/test_block_g.py:733` | #195 | ADR-031 | `reviews/block-g-claude-review-iter1.md` APPROVE | pending close commit | SHIPPED | Close specific-file git checkpoint and update evidence SHA. | APPROVE |
| G-3 | `ONE_SHOT_BUILTIN_AGENT_TYPES` | SYNTHESIS_MASTER.md:240; Runnable AgentTool/constants.ts:9-12 | LOW | CLEAN | Explore/plan/verify/review are one-shot prompt-token-saving agent types. | `subagent/agent_types.py:174`; `subagent/agent_types.py:103` | `tests/integration/test_block_g.py:81` | #086 | ADR-031 | `reviews/block-g-claude-review-iter1.md` APPROVE | pending close commit | SHIPPED | Close specific-file git checkpoint and update evidence SHA. | APPROVE |
| G-4 | `getPrompt(isCoordinator)` slim-vs-full prompt | SYNTHESIS_MASTER.md:241; Runnable AgentTool/prompt.ts:202-213 | MED | CLEAN | Coordinator prompt omits subagent notes while normal agents include them. | `subagent/agent_types.py:188`; `subagent/agent_types.py:202` | `tests/integration/test_block_g.py:340` | #086 | ADR-031 | `reviews/block-g-claude-review-iter1.md` APPROVE | pending close commit | SHIPPED | Close specific-file git checkpoint and update evidence SHA. | APPROVE |
| G-5 | `IterationBudget` explicit PORT_LOG row | SYNTHESIS_MASTER.md:242; Hermes run_agent.py:213-254 | HIGH | CLEAN | Subagents share parent `IterationBudget` object. | `core/budget.py:27`; `subagent/spawn.py:68` | `tests/integration/test_block_g.py:267`; `tests/integration/test_subagent.py:62`; `tests/integration/test_subagent.py:400` | #016 | ADR-014; ADR-015; ADR-031 | `reviews/block-g-claude-review-iter1.md` APPROVE | pending close commit | SHIPPED | Close specific-file git checkpoint and update evidence SHA. | APPROVE |
| G-6 | DEFAULT_AGENT_PROMPT verbatim phrasing | SYNTHESIS_MASTER.md:243; Runnable constants/prompts.ts:758 | HIGH | CLEAN | Subagent base prompt includes concise no-gold-plating guidance. | `subagent/agent_types.py:38` | `tests/integration/test_block_g.py:351` | #086 | ADR-031 | `reviews/block-g-claude-review-iter1.md` APPROVE | pending close commit | SHIPPED | Close specific-file git checkpoint and update evidence SHA. | APPROVE |
| G-7 | "Notes" appendix to subagent system prompt | SYNTHESIS_MASTER.md:244; Runnable constants/prompts.ts:766-770 | HIGH | CLEAN | Subagent prompt includes notes for tool-call announcements, parallel research, and final reply visibility. | `subagent/agent_types.py:50`; `subagent/agent_types.py:91` | `tests/integration/test_block_g.py:340`; `tests/integration/test_block_g.py:81` | #086 | ADR-031 | `reviews/block-g-claude-review-iter1.md` APPROVE | pending close commit | SHIPPED | Close specific-file git checkpoint and update evidence SHA. | APPROVE |
| G-8 | `forkSubagent` cache-prefix replay | SYNTHESIS_MASTER.md:245; Runnable forkSubagent.ts:73-end | HIGH | already in plan | Cache-prefix fork message replay exists in the planned Block G2 helper surface. | `subagent/fork.py:126`; `subagent/fork.py:206`; `subagent/__init__.py:36` | `tests/integration/test_block_g2.py:67`; `tests/integration/test_block_g2.py:142` | #094 | ADR-033 | `reviews/block-g-claude-review-iter1.md` APPROVE | pending close commit | SHIPPED | Close specific-file git checkpoint and update evidence SHA. | APPROVE |

EXPECTED_ROWS: 8
LEDGER_ROWS: 8
SHIPPED: 8
PARTIAL: 0
MISSING: 0
DEFERRED_USER_APPROVED: 0
DROPPED_USER_APPROVED: 0
N/A_CONSTRAINT: 0
SHIP_BLOCKING_ROWS: 0 by local scope audit; pending Claude review
